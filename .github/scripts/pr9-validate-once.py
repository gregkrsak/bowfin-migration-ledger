"""Owner-authorized orchestration only; repository test code runs in Docker."""
import ast
import base64
import hashlib
import json
import os
import pathlib
import re
import selectors
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timezone

REPO = "gregkrsak/bowfin-migration-ledger"
HEAD = "62a19baf0f67474f0c25c609f9a4300aa11e74d4"
TREE = "27a18b261d8f5325c2414ad9e18193e91b870a37"
BASE = "edb0a11851cb1b51727c857d03c045ad1e7daa95"
VIEW = "cd514c89fda2d91318c7a63b8b737118141f7b2c"
BRANCH = "pr9-budget-validation-once"
MANIFEST = json.loads(r'''{"PROTOCOL.md":{"blob_sha1":"fcd376d22a01047e0923dffed948d8c66d47dfae","bytes":36501,"mode":"100644","sha256":"facac8437e1fb41f517966eff413d2fdd2e37f8c249a594bb946e491fa16f055"},"README.md":{"blob_sha1":"e5d2356f377db7148b84b9953ae0ec5ee621a99e","bytes":9421,"mode":"100644","sha256":"e8a25ddb3ca2b0d32e2cffb172ba248ace99926a7bf7dd3967a9a9c7b9fdfe9c"},"audit_scan.py":{"blob_sha1":"d8ac2f74adaceedc638e78dafb488dfbbcb359a7","bytes":16388,"mode":"100644","sha256":"91cb6887583d48aa7f12ebc709ffbe8c6c59ce538246c6b38401d7c997d4bbaf"},"generate.py":{"blob_sha1":"7d103aa4d61c42d089e991e25b6c3763cae08ffe","bytes":24802,"mode":"100644","sha256":"d81bb830cb2753b139feb91ecf6658a22cf084e1766cd52ad2798ec68dec54f3"},"limits.json":{"blob_sha1":"00859ebf3bf80203e3ade39af7b88e28c39ff604","bytes":685,"mode":"100644","sha256":"dd5785a0d34019bb37782caf2c5886cb987493eacfd24be1f6d2571adf0cb512"},"protocol_lib.py":{"blob_sha1":"7c34cc34d6d70c6d1a08006ceb2a63ca1f501d0f","bytes":44701,"mode":"100644","sha256":"0d48a22571cde789a36bcb77dd65846d756de4a1af7dc4549ca8d402621a2568"},"schema.json":{"blob_sha1":"56f81ff76b38c1a870fdb49abc5e378f1c003370","bytes":27406,"mode":"100644","sha256":"257eb8d1427529d33fe1dcfe2b4867916d516af1fe6123109a1e4ba7900e344f"},"tests/fixtures/mutations.json":{"blob_sha1":"4aa64b28f9bcd472f4582f68e3b9c131fee0ac68","bytes":12940,"mode":"100644","sha256":"73918827468c654702cde5860557ade2f8dd2d4fa1580681ab9ef2b21da7d3d2"},"tests/fixtures/valid-case.json":{"blob_sha1":"a1cc67fbf970f745c5e2473d6dec9019bf7858b4","bytes":4974,"mode":"100644","sha256":"71038e6b0a49cfb3f6c5d903c0d38819683c1d88b2dcc7b4e7f3364b016a386e"},"tests/fixtures/vectors.json":{"blob_sha1":"b4113e7d35134f99507e685e72d0ab6478e5f751","bytes":4531,"mode":"100644","sha256":"4ed3ec81aa8e7130bfcc1686952eebd9b3151387bd3e4156f1c9a09c3dafb06d"},"tests/test_protocol.py":{"blob_sha1":"8c6e8a241cbc93b947ca9ee29c1efd7d91e05551","bytes":103835,"mode":"100644","sha256":"66809cd27594973cd68eb174d1851bd3c22b1b01499eb222eca6a42293f1f917"},"verify.py":{"blob_sha1":"e8492b02a262773c697f0c32f5fc22090ad84ec9","bytes":113952,"mode":"100644","sha256":"eb4936bfac9b30332919cd6293428c28cf1ff4cb0bddc72b4194f5aed3c9343f"}}''')
MAX_LOG = 4 * 1024 * 1024
report = {"record_class": "bounded_synthetic_execution_report", "repository": REPO,
          "subject_head": HEAD, "subject_tree": TREE, "protocol_subtree": VIEW,
          "workflow_head": os.environ.get("GITHUB_SHA"),
          "run_id": os.environ.get("GITHUB_RUN_ID"),
          "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
          "started_at": datetime.now(timezone.utc).isoformat(),
          "test_invocations_attempted": 0, "status": "preparation",
          "bounds": {"test_wall_seconds": 300, "cpu_seconds_per_process": 240,
                     "memory_bytes": 1073741824, "swap_disabled": True,
                     "cpus": 1, "pids": 64, "tmpfs_bytes": 134217728,
                     "file_bytes": 67108864, "open_files": 256,
                     "log_bytes": MAX_LOG, "network": "none", "root_read_only": True}}
log = bytearray()
container = None

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def command(args, timeout=30):
    return subprocess.run(args, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=timeout).stdout

def acquire(url, maximum, authenticated=False):
    headers = {"User-Agent": "pr9-owner-authorized-synthetic-validation"}
    if authenticated:
        require(url.startswith("https://api.github.com/repos/" + REPO + "/"), "API scope")
        headers["Authorization"] = "Bearer " + os.environ["GH_READ_TOKEN"]
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read(maximum + 1)
    require(len(data) <= maximum, "acquisition size")
    return data

def api(path):
    return json.loads(acquire("https://api.github.com/repos/" + REPO + "/" + path,
                              1024 * 1024, True))

def verify_subject():
    pr = api("pulls/9")
    require(pr["state"] == "open" and pr["draft"] and not pr.get("merged", False), "PR state")
    require(pr["head"]["sha"] == HEAD and pr["head"]["repo"]["full_name"] == REPO, "PR head")
    require(pr["base"]["ref"] == "main" and pr["base"]["sha"] == BASE, "PR base")
    require(api("branches/main")["commit"]["sha"] == BASE, "main drift")

def git_hash(kind, data):
    return hashlib.sha1(kind.encode() + b" " + str(len(data)).encode() + b"\0" + data).hexdigest()

def reconstruct_view():
    root = {}
    for path, item in MANIFEST.items():
        node = root
        parts = path.split("/")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = item["blob_sha1"]
    def tree(node):
        entries = []
        for name, value in node.items():
            directory = isinstance(value, dict)
            entries.append((name + ("/" if directory else ""),
                            (b"40000" if directory else b"100644") + b" " + name.encode()
                            + b"\0" + bytes.fromhex(tree(value) if directory else value)))
        return git_hash("tree", b"".join(value for _, value in sorted(entries)))
    return tree(root)

try:
    require(os.environ.get("GITHUB_ACTIONS") == "true", "GitHub Actions required")
    require(os.environ.get("GITHUB_REPOSITORY") == REPO, "repository scope")
    require(os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH, "branch scope")
    require(os.environ.get("GITHUB_EVENT_NAME") == "push", "push only")
    require(os.environ.get("GITHUB_RUN_ATTEMPT") == "1", "no rerun authorized")
    require(len(MANIFEST) == 12 and reconstruct_view() == VIEW, "closed reviewed protocol view")
    verify_subject()
    commit = api("git/commits/" + HEAD)
    require(commit["tree"]["sha"] == TREE and [p["sha"] for p in commit["parents"]] == [BASE], "commit identity")
    root = pathlib.Path(tempfile.mkdtemp(prefix="pr9-reviewed-", dir=os.environ["RUNNER_TEMP"]))
    for path, item in sorted(MANIFEST.items()):
        require(not path.startswith("/") and ".." not in path.split("/") and item["mode"] == "100644", "path/mode")
        data = acquire("https://raw.githubusercontent.com/" + REPO + "/" + HEAD
                       + "/protocol/m0.1/v2/" + path, item["bytes"])
        require(len(data) == item["bytes"] and git_hash("blob", data) == item["blob_sha1"]
                and hashlib.sha256(data).hexdigest() == item["sha256"], "source bytes: " + path)
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write(data)
        target.chmod(0o444)
    for directory in sorted((p for p in root.rglob("*") if p.is_dir()), reverse=True):
        directory.chmod(0o555)
    root.chmod(0o555)
    require(json.loads((root / "limits.json").read_text())["max_processing_steps"] == 100000000000, "budget profile")
    parsed = ast.parse((root / "tests/test_protocol.py").read_text())
    case = next(n for n in parsed.body if isinstance(n, ast.ClassDef) and n.name == "ProtocolTests")
    expected = sorted(n.name for n in case.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_"))
    require(len(expected) == len(set(expected)) == 54, "54 authored predecessor methods required")
    report["expected_methods"] = expected
    report["reviewed_files"] = MANIFEST
    # The tag is acquisition only. Execute the resulting immutable digest, never
    # the mutable tag; preserve the acquired image identity for reproduction.
    command(["docker", "pull", "docker.io/library/python:3.12-slim-bookworm"], 120)
    image = json.loads(command(["docker", "image", "inspect", "docker.io/library/python:3.12-slim-bookworm"]))[0]
    require(bool(image["RepoDigests"]), "immutable image digest required")
    immutable_image = image["RepoDigests"][0]
    require(immutable_image.startswith("python@sha256:") or immutable_image.startswith("docker.io/library/python@sha256:"), "official Python image")
    report["image"] = {"reference": immutable_image, "image_id": image["Id"],
                       "architecture": image["Architecture"], "os": image["Os"]}
    report["docker_version"] = json.loads(command(["docker", "version", "--format", "{{json .}} "]))
    container = "pr9-synthetic-" + os.environ["GITHUB_RUN_ID"] + "-1"
    wrapper = (
        "import json,os,pathlib,resource,runpy,sys; "
        "assert sys.version_info[:2]==(3,12); assert sys.flags.isolated; "
        "cg=pathlib.Path('/sys/fs/cgroup'); "
        "caps={n:(cg/n).read_text().strip() for n in ('memory.max','memory.swap.max','pids.max','cpu.max')}; "
        "assert caps['memory.max']=='1073741824' and caps['memory.swap.max']=='0' and caps['pids.max']=='64'; "
        "quota,period=map(int,caps['cpu.max'].split()); assert quota==period and quota>0; "
        "assert resource.getrlimit(resource.RLIMIT_CPU)==(240,240); "
        "assert resource.getrlimit(resource.RLIMIT_FSIZE)==(67108864,67108864); "
        "assert resource.getrlimit(resource.RLIMIT_NOFILE)==(256,256); "
        "status=pathlib.Path('/proc/self/status').read_text().splitlines(); "
        "assert any(s.startswith('NoNewPrivs:') and s.split()[-1]=='1' for s in status); "
        "assert any(s.startswith('CapEff:') and int(s.split()[-1],16)==0 for s in status); "
        "print('PR9_RUNTIME_PROVENANCE='+json.dumps({'python':sys.version,'isolated':bool(sys.flags.isolated),"
        "'uid':os.getuid(),'cgroup_limits':caps,'cpu_limit':resource.getrlimit(resource.RLIMIT_CPU),"
        "'file_limit':resource.getrlimit(resource.RLIMIT_FSIZE),'fd_limit':resource.getrlimit(resource.RLIMIT_NOFILE)}),flush=True); "
        "sys.argv=['/review/tests/test_protocol.py']; runpy.run_path(sys.argv[0],run_name='__main__')"
    )
    args = ["docker", "create", "--name", container, "--restart=no", "--network=none",
            "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges=true",
            "--user=65534:65534", "--memory=1073741824", "--memory-swap=1073741824",
            "--cpus=1", "--pids-limit=64", "--ulimit=cpu=240:240",
            "--ulimit=fsize=67108864:67108864", "--ulimit=nofile=256:256",
            "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=134217728,mode=1777",
            "--mount=type=bind,src=" + str(root) + ",dst=/review,readonly",
            "--workdir=/tmp", "--env=TZ=UTC", "--env=LANG=C.UTF-8",
            immutable_image, "python3", "-I", "-B", "-u", "-c", wrapper]
    command(args)
    config = json.loads(command(["docker", "inspect", container]))[0]
    host = config["HostConfig"]
    require(host["NetworkMode"] == "none" and host["ReadonlyRootfs"], "network/root containment")
    require(host["Memory"] == host["MemorySwap"] == 1073741824 and host["NanoCpus"] == 1000000000
            and host["PidsLimit"] == 64, "resource containment")
    require(host["CapDrop"] == ["ALL"] and any(s in {"no-new-privileges", "no-new-privileges=true", "no-new-privileges:true"}
                                              for s in host["SecurityOpt"]), "privilege containment")
    require(config["Config"]["User"] == "65534:65534" and host["RestartPolicy"]["Name"] == "no", "user/restart containment")
    binds = [m for m in config["Mounts"] if m["Type"] == "bind"]
    require(len(binds) == 1 and binds[0]["Destination"] == "/review" and not binds[0]["RW"], "review-only bind mount")
    require(all(m["Type"] == "bind" or (m["Type"] == "tmpfs" and m["Destination"] == "/tmp")
                for m in config["Mounts"]), "no other mounted data")
    require(set(host["Tmpfs"]) == {"/tmp"} and "size=134217728" in host["Tmpfs"]["/tmp"], "bounded writable tmpfs")
    require(not any(e.startswith(("GH_READ_TOKEN=", "GITHUB_TOKEN=", "ACTIONS_RUNTIME_TOKEN="))
                    for e in config["Config"]["Env"]), "no credential in container")
    report["container_host_config"] = host
    verify_subject()
    report["test_invocations_attempted"] = 1
    report["status"] = "running"
    started = time.monotonic()
    proc = subprocess.Popen(["docker", "start", "--attach", container], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ)
    reason = None
    while selector.get_map():
        if time.monotonic() - started >= 300:
            reason = "wall_timeout"
            break
        for key, _ in selector.select(timeout=1):
            data = os.read(key.fileobj.fileno(), 65536)
            if not data:
                selector.unregister(key.fileobj)
                continue
            if len(log) + len(data) > MAX_LOG:
                reason = "output_limit"
                break
            log.extend(data)
        if reason:
            break
    if reason:
        subprocess.run(["docker", "kill", container], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        proc.kill()
    proc.wait(timeout=10)
    state = json.loads(command(["docker", "inspect", container]))[0]["State"]
    report.update({"container_state": state, "docker_attach_exit": proc.returncode,
                   "duration_seconds": round(time.monotonic() - started, 3), "containment_stop": reason})
    text = log.decode("utf-8", "replace")
    methods = re.findall(r"(?m)^(test_\w+) \(__main__\.ProtocolTests(?:\.\w+)?\)", text)
    runtime = next((json.loads(line.split("=", 1)[1]) for line in text.splitlines()
                    if line.startswith("PR9_RUNTIME_PROVENANCE=")), None)
    report.update({"observed_methods": methods, "runtime": runtime})
    require(reason is None and state["Status"] == "exited" and state["ExitCode"] == 0
            and not state["OOMKilled"] and proc.returncode == 0, "test process outcome")
    require(sorted(methods) == expected and len(methods) == 54, "exact executed method set")
    require(re.search(r"(?m)^Ran 54 tests in [0-9.]+s\s*$", text) and re.search(r"(?m)^OK\s*$", text), "clean unittest summary")
    require(runtime and runtime["isolated"] and runtime["uid"] == 65534, "runtime provenance")
    verify_subject()
    report["status"] = "passed"
except Exception as error:
    report["status"] = "failed_or_blocked"
    report["error"] = type(error).__name__ + ": " + str(error)
    if container:
        subprocess.run(["docker", "kill", container], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
finally:
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["output_bytes"] = len(log)
    report["output_sha256"] = hashlib.sha256(log).hexdigest()
    print("PR9_REPORT_JSON=" + json.dumps(report, sort_keys=True, separators=(",", ":")), flush=True)
    for offset in range(0, len(log), 12288):
        print("PR9_LOG_CHUNK=" + str(offset // 12288) + ":" + base64.b64encode(log[offset:offset + 12288]).decode(), flush=True)
    print("PR9_LOG_END=" + str(len(log)) + ":" + report["output_sha256"], flush=True)
if report["status"] != "passed":
    raise SystemExit(1)
