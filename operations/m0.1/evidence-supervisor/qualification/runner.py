"""Proposed trusted-host qualification launcher. Inert until separately authorized.

Never import reviewed workload modules. Only the two benign qualification modes
are reachable. The GitHub API/TLS and runner OS are explicit trust dependencies.
This source has been prepared statically; preparation is not execution authority.
"""

import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import shlex
import signal
import stat
import subprocess
import sys
import threading
import time
import urllib.request


REPO = "gregkrsak/bowfin-migration-ledger"
COMMIT = "96e60a0a62d303f964fb4cefdc2687251f2f38b8"
TREE = "453d92123b914fb2c4aa082d9c42983ef69a83a5"
SUBTREE = "20e8b5bd1f9264f6eb00cba2db54c3e48407908b"
PREFIX = "operations/m0.1/evidence-supervisor"
PLAN_BLOB = "15b7b50060774bbb7f0fb7f3ebda7626caf7c81e"
PLAN_SHA = "1f64f9e3039841e623d4010a5312fdb69a2a5401798d9dd49c2574e430425eb4"
IMAGE = "docker.io/library/python@sha256:2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301"
CONFIG = "sha256:9cb180cb36bd45dc786105b834d3cb5f3b1d69a6a63c79ca10fc64f108aa649a"
ROOT = Path("/var/tmp/bowfin-pr18")
SOURCE = ROOT / "source"
CONTROL = ROOT / "control"
EXPORT = Path("/var/tmp/bowfin-pr18-export")
CGROUP = Path("/sys/fs/cgroup/bowfinpr18.slice")
UNITS = ("bowfinpr18.slice", "bowfinpr18-deadline.timer", "bowfinpr18-deadline.service")
CONTROL_JSON = frozenset(("intent", "loaded-units", "platform", "cgroup-owned", "create-argv",
    "container", "container-created", "timer-armed", "live-gate", "attach", "controller-cleanup",
    "result", "qualification-membership", "watchdog-test-ready", "deadline-fired", "deadline-cleanup",
    "terminal"))
COMMON = frozenset(("intent", "loaded-units", "platform", "cgroup-owned", "create-argv", "container",
    "container-created", "timer-armed", "live-gate", "qualification-membership", "terminal"))
HOST_CAPS = {"host/attestation.json": 262144, "host/launch-status.json": 65536,
             "host/final-state.json": 196608, "host/deadline-journal.txt": 262144,
             "host/controller.stdout": 65536, "host/controller.stderr": 65536,
             "inventory.json": 65536, "report.md": 65536}
ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
       "DOCKER_CONFIG": "/var/tmp/bowfin-pr18-acquisition"}
META = ("GITHUB_REPOSITORY", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_JOB", "GITHUB_SHA",
        "GITHUB_WORKFLOW", "GITHUB_REF", "GITHUB_EVENT_NAME", "GITHUB_WORKFLOW_REF",
        "GITHUB_WORKFLOW_SHA", "RUNNER_OS", "RUNNER_ARCH", "ImageOS", "ImageVersion")
PREP_END = None
POST_END = None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git_sha(kind, raw):
    return hashlib.sha1(kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, "duplicate JSON key")
        out[key] = value
    return out


def decode(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_float=finite_float,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def finite_float(token):
    require(len(token) <= 128, "JSON float token cap")
    value = float(token)
    require(math.isfinite(value), "nonfinite JSON float")
    return value


def read(path, cap):
    require(POST_END is None or time.monotonic() < POST_END, "capture deadline")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size <= cap, "invalid/big file: " + str(path))
        raw = stream.read(cap + 1)
    require(len(raw) <= cap, "read cap: " + str(path))
    require(POST_END is None or time.monotonic() < POST_END, "capture deadline")
    return raw


def write(path, raw, cap):
    require(POST_END is None or time.monotonic() < POST_END, "capture deadline")
    require(len(raw) <= cap, "write cap: " + str(path))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, "wb") as stream:
        require(stream.write(raw) == len(raw), "short evidence write")
        stream.flush()
        os.fsync(stream.fileno())
    require(read(path, cap) == raw, "evidence byte readback mismatch")


def record(name, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("ascii")
    write(EXPORT / name, raw, HOST_CAPS[name])


def tool(argv, seconds=10, cap=262144, prep=False, good=(0,)):
    if prep:
        seconds = min(seconds, PREP_END - time.monotonic())
    if POST_END is not None:
        seconds = min(seconds, POST_END - time.monotonic())
    require(seconds > 0, "prelaunch time budget exhausted")
    proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, close_fds=True, env=ENV,
                            cwd="/var/tmp", start_new_session=True)
    selector = selectors.DefaultSelector()
    buffers = [bytearray(), bytearray()]
    end = time.monotonic() + seconds
    try:
        for number, pipe in enumerate((proc.stdout, proc.stderr)):
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, number)
        while selector.get_map():
            require(time.monotonic() < end, "trusted tool timeout")
            for key, _ in selector.select(min(0.05, max(0, end - time.monotonic()))):
                raw = os.read(key.fd, min(65536, cap - len(buffers[key.data]) + 1))
                if not raw:
                    selector.unregister(key.fileobj)
                else:
                    require(len(buffers[key.data]) + len(raw) <= cap, "trusted tool output cap")
                    buffers[key.data].extend(raw)
        status = proc.wait(timeout=max(0.01, end - time.monotonic()))
        require(status in good, "trusted tool exit " + str(status) + ": " + argv[0])
        return status, bytes(buffers[0]), bytes(buffers[1])
    finally:
        selector.close()
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=2)
        proc.stdout.close()
        proc.stderr.close()


def api(path, cap=1048576):
    remaining = PREP_END - time.monotonic()
    require(remaining > 0, "acquisition time budget")
    url = "https://api.github.com/repos/" + REPO + path
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                  "User-Agent": "bowfin-pr18-static-pinned-qualification"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=min(10, remaining)) as response:
        require(response.geturl() == url and response.status == 200, "API redirect/status")
        raw = response.read(cap + 1)
    require(len(raw) <= cap and time.monotonic() < PREP_END, "API bound")
    return decode(raw)


def tree_entries(identity):
    value = api("/git/trees/" + identity)
    require(value["sha"] == identity and value.get("truncated") is False, "incomplete Git tree")
    entries = value["tree"]
    require(len(entries) <= 512, "Git tree entry bound")
    names = [e["path"] for e in entries]
    require(len(set(names)) == len(names) and all("/" not in n and n not in ("", ".", "..") for n in names), "Git tree paths")
    raw = bytearray()
    for entry in sorted(entries, key=lambda e: (e["path"] + ("/" if e["type"] == "tree" else "")).encode()):
        mode = entry["mode"].lstrip("0")
        require(mode in ("40000", "100644", "100755", "120000", "160000"), "Git tree mode")
        raw.extend(mode.encode() + b" " + entry["path"].encode() + b"\0" + bytes.fromhex(entry["sha"]))
    require(git_sha("tree", bytes(raw)) == identity, "Git tree object hash")
    return {e["path"]: e for e in entries}


def materialize(host):
    commit = api("/git/commits/" + COMMIT)
    require(commit["sha"] == COMMIT and commit["tree"]["sha"] == TREE, "commit/tree correspondence")
    entries = tree_entries(TREE)
    for part in PREFIX.split("/"):
        entry = entries[part]
        require(entry["type"] == "tree", "source ancestor is not tree")
        identity = entry["sha"]
        entries = tree_entries(identity)
    require(identity == SUBTREE, "operational subtree mismatch")
    nested = tree_entries(entries["containment"]["sha"])
    def obtain(path, expected_blob=None):
        item = nested[path.split("/")[1]] if "/" in path else entries[path]
        require(item["mode"] == "100644" and item["type"] == "blob", "deployment object mode/type")
        if expected_blob is not None:
            require(item["sha"] == expected_blob, "plan Git blob mismatch")
        value = api("/git/blobs/" + item["sha"], 1500000)
        require(value["encoding"] == "base64" and value["sha"] == item["sha"], "Git blob response")
        raw = base64.b64decode(value["content"].replace("\n", ""), validate=True)
        require(len(raw) == value["size"] <= 1048576 and git_sha("blob", raw) == item["sha"], "Git blob hash/size")
        return raw, item["sha"]
    plan_raw, _ = obtain("containment/invocation.json", PLAN_BLOB)
    require(len(plan_raw) == 1778 and sha(plan_raw) == PLAN_SHA, "plan independent digest")
    plan = decode(plan_raw)
    require(set(plan) == {"format", "image", "source_files"} and plan["image"] == IMAGE
            and plan["format"] == "bowfin-pr18-contained-run-v1", "plan shape")
    files = plan["source_files"]
    paths = {e["path"] for e in files}
    expected = {"supervisor.py", "test_supervisor.py", "runtime-pin.json", "containment/controller.py",
                "containment/probe.py", "containment/seccomp.json", "containment/LICENSE.moby"}
    expected.update("containment/" + name for name in UNITS)
    require(len(files) == 10 and paths == expected, "closed ten-object source set")
    SOURCE.mkdir(mode=0o755)
    (SOURCE / "containment").mkdir(mode=0o755)
    observed = []
    for item in files + [{"path": "containment/invocation.json", "bytes": 1778, "sha256": PLAN_SHA}]:
        path = item["path"]
        raw, blob = (plan_raw, PLAN_BLOB) if path == "containment/invocation.json" else obtain(path)
        require(type(item["bytes"]) is int and len(raw) == item["bytes"] and sha(raw) == item["sha256"], "deployment bytes/digest")
        write(SOURCE / path, raw, 1048576)
        os.chmod(SOURCE / path, 0o644)
        observed.append({"path": path, "blob": blob, "bytes": len(raw), "sha256": sha(raw)})
    host["source"] = {"repository": REPO, "commit": COMMIT, "tree": TREE, "subtree": SUBTREE,
                      "commit_binding": "trusted GitHub API/TLS; tree/blob object hashes independently reconstructed",
                      "objects": observed}


def prepare(host):
    require(os.uname().machine == "x86_64" and Path("/proc/1/comm").read_text().strip() == "systemd", "host platform")
    require("ID=ubuntu" in Path("/etc/os-release").read_text() and 'VERSION_ID="24.04"' in Path("/etc/os-release").read_text(), "Ubuntu 24.04 required")
    require(Path("/sys/fs/cgroup/cgroup.controllers").is_file(), "cgroup v2 required")
    require({"cpu", "memory", "pids"} <= set(Path("/sys/fs/cgroup/cgroup.controllers").read_text().split()), "controllers unavailable")
    require(Path("/sys/fs/cgroup/system.slice/cgroup.kill").exists(), "non-root cgroup.kill unavailable")
    for unit in UNITS:
        require(all(not (Path(directory) / unit).exists() for directory in
                ("/run/systemd/system", "/etc/systemd/system", "/usr/lib/systemd/system", "/lib/systemd/system")),
                "unit already exists")
    require(not CGROUP.exists(), "workload cgroup already exists")
    binary_paths = ("/usr/bin/python3", "/usr/bin/docker", "/usr/bin/systemctl", "/usr/bin/busctl",
                    "/usr/bin/journalctl", "/usr/bin/containerd", "/usr/bin/runc")
    host["binaries"] = []
    for name in binary_paths:
        path = Path(name).resolve(strict=True)
        raw = read(path, 64 * 1024 * 1024)
        host["binaries"].append({"command": name, "resolved": str(path), "bytes": len(raw), "sha256": sha(raw)})
    host["versions"] = {}
    for key, argv in (("python", ["/usr/bin/python3", "--version"]), ("systemd", ["/usr/bin/systemctl", "--version"]),
                      ("docker", ["/usr/bin/docker", "version", "--format", "{{json .}}"]),
                      ("containerd", ["/usr/bin/containerd", "--version"]), ("runc", ["/usr/bin/runc", "--version"])):
        host["versions"][key] = tool(argv, prep=True)[1].decode("utf-8")
    host["mountinfo"] = Path("/proc/self/mountinfo").read_text()[:65536]
    require(len(Path("/proc/self/mountinfo").read_bytes()) <= 65536, "host mountinfo cap")
    daemon = decode(tool(["/usr/bin/docker", "info", "--format", "{{json .}}"], prep=True)[1])
    require(daemon.get("CgroupDriver") == "systemd" and daemon.get("CgroupVersion") == "2"
            and not any("rootless" in s for s in daemon.get("SecurityOptions", [])), "Docker topology")
    require(Path("/var/run/docker.sock").is_socket(), "local Docker socket unavailable")
    host["docker"] = {k: daemon.get(k) for k in ("ServerVersion", "CgroupDriver", "CgroupVersion", "SecurityOptions", "Driver", "Architecture", "OSType")}
    materialize(host)
    tool(["/usr/bin/docker", "pull", "--platform", "linux/amd64", IMAGE], seconds=60, prep=True)
    image = decode(tool(["/usr/bin/docker", "image", "inspect", IMAGE], prep=True)[1])
    require(len(image) == 1 and image[0]["Id"] == CONFIG and image[0]["Os"] == "linux"
            and image[0]["Architecture"] == "amd64", "image configuration")
    host["image"] = {k: image[0][k] for k in ("Id", "RepoDigests", "Os", "Architecture")}
    host["installed_units"] = {}
    for unit in UNITS:
        raw = read(SOURCE / "containment" / unit, 16384)
        path = Path("/run/systemd/system") / unit
        write(path, raw, 16384)
        os.chmod(path, 0o644)
        host["installed_units"][unit] = {"bytes": len(raw), "sha256": sha(raw), "text": raw.decode("ascii")}
    tool(["/usr/bin/systemctl", "daemon-reload"], prep=True)
    require(time.monotonic() < PREP_END, "prelaunch budget exhausted")


def observe_mounts(stop, observations):
    """Read-only concurrent witness. A missed observation cannot qualify a run."""
    while not stop.wait(0.005):
        try:
            container = decode(read(CONTROL / "container.json", 4096))["id"]
            require(re.fullmatch(r"[0-9a-f]{64}", container) is not None, "container ID")
            leaf = CGROUP / ("docker-" + container + ".scope")
            pids = (leaf / "cgroup.procs").read_text().split()
            if not pids:
                continue
            pid = min(int(p) for p in pids)
            require(Path(f"/proc/{pid}/cgroup").read_text() == "0::/bowfinpr18.slice/docker-" + container + ".scope\n", "mount witness cgroup")
            raw = Path(f"/proc/{pid}/mountinfo").read_text()
            require(len(raw.encode()) <= 65536, "container mountinfo cap")
            mounts = {line.split()[4]: line.split() for line in raw.splitlines()}
            tmp, shm = mounts["/tmp"], mounts["/dev/shm"]
            for item in (tmp, shm):
                require(item[item.index("-") + 1] == "tmpfs", "tmpfs required")
            require({"rw", "nosuid", "nodev", "noexec"} <= set(tmp[5].split(",")), "scratch flags")
            tmp_stat = os.statvfs(f"/proc/{pid}/root/tmp")
            shm_stat = os.statvfs(f"/proc/{pid}/root/dev/shm")
            require(tmp_stat.f_blocks * tmp_stat.f_frsize == 67108864 and tmp_stat.f_files == 4096
                    and shm_stat.f_blocks * shm_stat.f_frsize == 1048576, "effective tmpfs quota")
            observations.update({"container": container, "host_pid": pid, "mountinfo": raw,
                "tmp_bytes": tmp_stat.f_blocks * tmp_stat.f_frsize, "tmp_inodes": tmp_stat.f_files,
                "shm_bytes": shm_stat.f_blocks * shm_stat.f_frsize, "observed_monotonic": time.monotonic()})
            return
        except (OSError, KeyError, ValueError, RuntimeError):
            continue


def bus_property(unit, interface, name):
    escaped = unit.replace("-", "_2d").replace(".", "_2e")
    raw = tool(["/usr/bin/busctl", "get-property", "org.freedesktop.systemd1",
        "/org/freedesktop/systemd1/unit/" + escaped, "org.freedesktop.systemd1." + interface, name])[1]
    return shlex.split(raw.decode("ascii"))


def service_state():
    raw = tool(["/usr/bin/systemctl", "show", "bowfinpr18-deadline.service", "--property=ActiveState",
        "--property=SubState", "--property=Result", "--property=ExecMainCode",
        "--property=ExecMainStatus", "--property=ExecMainStartTimestampMonotonic",
        "--property=ExecMainExitTimestampMonotonic"])[1]
    state = dict(line.split("=", 1) for line in raw.decode("ascii").splitlines())
    state["Job"] = bus_property("bowfinpr18-deadline.service", "Unit", "Job")
    return state


def final_units():
    timer = "bowfinpr18-deadline.timer"
    return {"service": service_state(), "timer": {
        "ActiveState": bus_property(timer, "Unit", "ActiveState"),
        "Job": bus_property(timer, "Unit", "Job"),
        "LastTriggerUSecMonotonic": bus_property(timer, "Timer", "LastTriggerUSecMonotonic"),
        "NextElapseUSecMonotonic": bus_property(timer, "Timer", "NextElapseUSecMonotonic")}}


def invoke(mode, publisher, host):
    require(time.monotonic() < PREP_END, "no launch after preflight expiry")
    argv = ["/usr/bin/python3", "-I", str(SOURCE / "containment/controller.py"), mode, "--plan-sha256", PLAN_SHA]
    publisher.update({"argv": argv, "invocation_attempted": True, "started_monotonic": time.monotonic()})
    stop = threading.Event()
    observed = {}
    witness = threading.Thread(target=observe_mounts, args=(stop, observed), daemon=True)
    witness.start()
    handles = []
    selector = selectors.DefaultSelector()
    proc = None
    counts = [0, 0]
    capture_completed = False
    try:
        for name in ("host/controller.stdout", "host/controller.stderr"):
            fd = os.open(EXPORT / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
            handles.append(os.fdopen(fd, "wb", buffering=0))
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=ENV, close_fds=True, start_new_session=True)
        publisher["controller_pid"] = proc.pid
        for number, pipe in enumerate((proc.stdout, proc.stderr)):
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, number)
        end = time.monotonic() + 1030
        exited_at = None
        while proc.poll() is None or selector.get_map():
            require(time.monotonic() < end, "controller/witness deadline exceeded")
            if proc.returncode is not None:
                if exited_at is None:
                    exited_at = time.monotonic()
                require(time.monotonic() < exited_at + 1, "publisher pipe EOF unavailable after direct-child exit")
            for key, _ in selector.select(0.02):
                data = os.read(key.fd, min(65536, 65536 - counts[key.data] + 1))
                if not data:
                    selector.unregister(key.fileobj)
                else:
                    room = 65536 - counts[key.data]
                    handles[key.data].write(data[:room])
                    counts[key.data] += min(room, len(data))
                    require(len(data) <= room, "publisher stream cap")
        capture_completed = True
        publisher["controller_returncode"] = proc.returncode
        publisher["controller_completed_monotonic"] = time.monotonic()
        if mode == "qualify-watchdog":
            require(proc.returncode == -signal.SIGKILL, "not the expected direct controller SIGKILL")
            ready = decode(read(CONTROL / "watchdog-test-ready.json", 262144))
            require(ready["controller_pid"] == proc.pid and ready["boot_id"] == host["boot_id"]
                    and ready["fault"] == "intentional_controller_SIGKILL", "fault identity")
            expiry = decode(read(CONTROL / "timer-armed.json", 262144))["next_elapse_usec"] / 1000000
            require(type(expiry) in (int, float) and time.monotonic() < expiry, "late/unknown watchdog observation")
            while time.monotonic() < expiry + 50:
                if (CONTROL / "deadline-cleanup.json").exists():
                    state = service_state()
                    if state.get("ActiveState") in ("inactive", "failed") and state.get("Job") == ["(uo)", "0", "/"]:
                        break
                time.sleep(0.2)
            else:
                raise RuntimeError("independent service did not complete in deadline budget")
            publisher["deadline_service"] = service_state()
        else:
            require(proc.returncode == 0, "ordinary controller did not exit zero")
    finally:
        publisher["controller_capture_complete"] = capture_completed
        publisher["controller_pipe_eof"] = not bool(selector.get_map()) if proc is not None else False
        publisher["controller_retained_bytes"] = {"stdout": counts[0], "stderr": counts[1]}
        selector.close()
        if proc is not None:
            status = proc.poll()
            if status is not None:
                publisher["controller_returncode"] = status
                publisher.setdefault("controller_completed_monotonic", time.monotonic())
            else:
                # An outer-wrapper failure is adverse; only terminate its exact
                # primary child. The independent deadline is not disarmed.
                proc.kill()
                publisher["wrapper_intervention"] = "controller_SIGKILL_after_wrapper_error"
                try:
                    publisher["controller_returncode"] = proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    publisher["controller_wait_unavailable"] = True
            proc.stdout.close()
            proc.stderr.close()
        stop.set()
        witness.join(timeout=1)
        host["live_mount_witness"] = observed
        for handle in handles:
            os.fsync(handle.fileno())
            handle.close()


def reconcile(mode, publisher, host):
    require(host.get("live_mount_witness"), "no complete effective-mount witness")
    names = set(p.name for p in CONTROL.iterdir())
    allowed = {n + ".json" for n in CONTROL_JSON} | {"stdout", "stderr", "terminal.lock", "docker-config"}
    require(names <= allowed and (CONTROL / "docker-config").is_dir()
            and not list((CONTROL / "docker-config").iterdir()), "unexpected output inventory")
    expected = set(COMMON)
    expected.update(("attach", "controller-cleanup", "result") if mode == "qualify" else
                    ("watchdog-test-ready", "deadline-fired", "deadline-cleanup"))
    require(names == {n + ".json" for n in expected} | {"stdout", "stderr", "terminal.lock", "docker-config"}, "incomplete/extra case output")
    values = {n: decode(read(CONTROL / (n + ".json"), 262144)) for n in expected}
    require(values["intent"]["mode"] == mode and values["intent"]["plan_sha256"] == PLAN_SHA, "intent binding")
    require(values["cgroup-owned"]["boot_id"] == host["boot_id"] and
            values["cgroup-owned"]["path"] == str(CGROUP), "retained cgroup ownership")
    retained_stdout = read(CONTROL / "stdout", 4194304)
    require(all(marker in retained_stdout for marker in (b"BOWFIN_PR18_GATE_READY\n",
            b"BOWFIN_PR18_RELEASE_CONFIRMED\n", b"BOWFIN_PR18_PROBE_READY\n")), "incomplete retained handshake")
    for item in host["source"]["objects"]:
        raw = read(SOURCE / item["path"], 1048576)
        require(len(raw) == item["bytes"] and sha(raw) == item["sha256"], "source changed after launch")
    terminal = values["terminal"]
    units = final_units()
    publisher["final_units"] = units
    require(units["timer"]["Job"] == ["(uo)", "0", "/"]
            and units["service"]["Job"] == ["(uo)", "0", "/"], "final unit pending job")
    require(terminal["plan_sha256"] == PLAN_SHA and terminal["accepted"] is False
            and terminal["retry_authorized"] is False and terminal["merge_authorized"] is False, "terminal scope")
    if mode == "qualify":
        require(units["timer"]["ActiveState"] == ["s", "inactive"]
                and units["timer"]["LastTriggerUSecMonotonic"] == ["t", "0"]
                and units["service"]["ActiveState"] == "inactive"
                and units["service"]["SubState"] == "dead", "ordinary independent unit quiescence")
        require(terminal["origin"] == "controller" and terminal["classification"] == "watchdog_quiescent_pending_independent_review"
                and terminal["result_sha256"] == sha(read(CONTROL / "result.json", 262144)), "ordinary terminal seal")
        require(values["result"]["candidate_classification"] == "qualification_probe_and_cleanup_observed_pending_review"
                and values["result"]["error"] is None and values["attach"]["release_confirmed"] is True,
                "ordinary qualification result")
        cleanup = values["controller-cleanup"]
    else:
        require(terminal["origin"] == "deadline" and terminal["classification"] == "indeterminate", "watchdog terminal remains indeterminate")
        state = units["service"]
        require(state["Result"] == "exit-code" and state["ExecMainCode"] == "1"
                and state["ExecMainStatus"] == "1" and state["ActiveState"] in ("inactive", "failed")
                and state["Job"] == ["(uo)", "0", "/"], "deadline publisher status")
        expiry = values["timer-armed"]["next_elapse_usec"]
        trigger = units["timer"]["LastTriggerUSecMonotonic"]
        require(len(trigger) == 2 and trigger[0] == "t" and trigger[1].isdigit()
                and int(trigger[1]) >= expiry, "independent timer activation chronology")
        require(type(expiry) is int and int(state["ExecMainStartTimestampMonotonic"]) >= expiry
                and int(state["ExecMainExitTimestampMonotonic"]) >= int(state["ExecMainStartTimestampMonotonic"]),
                "deadline publisher chronology")
        cleanup = values["deadline-cleanup"]
        require(cleanup["terminal_arbitration_error"] is None, "deadline publication/arbitration error")
    require(cleanup["complete"] is True and cleanup["container_removed"] is True
            and cleanup["live_tasks_absent"] is True and cleanup["errors"] == [], "cleanup incomplete")
    raw = (CGROUP / "cgroup.events").read_text()
    require(dict(line.split() for line in raw.splitlines()).get("populated") == "0", "retained parent not empty")
    cid = values["container"]["id"]
    require(host["live_mount_witness"]["container"] == cid, "effective mount witness container mismatch")
    all_ids = tool(["/usr/bin/docker", "container", "ls", "--all", "--no-trunc", "--format", "{{.ID}}"])[1].decode("ascii").splitlines()
    require(cid not in all_ids, "exact container still present")
    publisher["final_cgroup_events"] = raw
    publisher["exact_container_absent"] = cid
    require(read(EXPORT / "host/controller.stderr", 65536) == b""
            and read(EXPORT / "host/controller.stdout", 65536) == b"", "unexpected primary publication diagnostic")
    return {"mode": mode, "classification": "qualification_observed_pending_independent_review",
            "suite_executed": False, "accepted": False, "retry_authorized": False, "merge_authorized": False}


def retain_control():
    if not CONTROL.exists():
        return
    target = EXPORT / "control"
    target.mkdir(mode=0o755)
    for path in sorted(CONTROL.iterdir()):
        if path.name == "docker-config":
            require(path.is_dir() and not path.is_symlink() and not list(path.iterdir()), "nonempty Docker configuration")
            continue
        cap = 4194304 if path.name in ("stdout", "stderr") else (0 if path.name == "terminal.lock" else 262144)
        require(path.name in {n + ".json" for n in CONTROL_JSON} | {"stdout", "stderr", "terminal.lock"}, "unapproved control path")
        write(target / path.name, read(path, cap), cap)


def main():
    global PREP_END, POST_END
    require(os.getuid() == 0 and sys.argv[1:] in (["qualify"], ["qualify-watchdog"]), "root and one qualification mode required")
    mode = sys.argv[1]
    require(signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL, "unexpected SIGCHLD disposition")
    metadata = {key: os.environ.get(key, "") for key in META}
    require(all(metadata.values()) and metadata["GITHUB_JOB"] ==
            ("ordinary" if mode == "qualify" else "watchdog")
            and metadata["GITHUB_REF"] == "refs/heads/main"
            and re.fullmatch(r"[0-9a-f]{40}", metadata["GITHUB_SHA"]) is not None
            and metadata["GITHUB_WORKFLOW_SHA"] == metadata["GITHUB_SHA"], "closed workflow metadata")
    require(metadata["GITHUB_REPOSITORY"] == REPO and metadata["GITHUB_RUN_ATTEMPT"] == "1"
            and metadata["RUNNER_OS"] == "Linux" and metadata["RUNNER_ARCH"] == "X64"
            and metadata["GITHUB_EVENT_NAME"] == "workflow_dispatch"
            and metadata["ImageVersion"] and all(len(v) <= 512 for v in metadata.values()), "runner metadata/attempt")
    started = float(os.environ["JOB_STARTED_MONOTONIC"])
    age = time.monotonic() - started
    require(0 <= age < 100, "bootstrap age outside preparation budget")
    PREP_END = time.monotonic() + 100 - age
    POST_END = started + 1130
    launcher = read(Path(__file__), 65536)
    launcher_commit = os.environ["BOWFIN_LAUNCHER_COMMIT"]
    require(re.fullmatch(r"[0-9a-f]{40}", launcher_commit) is not None
            and sha(launcher) == os.environ["BOWFIN_LAUNCHER_SHA256"]
            and git_sha("blob", launcher) == os.environ["BOWFIN_LAUNCHER_BLOB"], "externally pinned launcher identity")
    require(not ROOT.exists() and not EXPORT.exists(), "attempt path already reserved")
    ROOT.mkdir(mode=0o755)
    EXPORT.mkdir(mode=0o755)
    (EXPORT / "host").mkdir(mode=0o755)
    Path(ENV["DOCKER_CONFIG"]).mkdir(mode=0o700)
    host = {"metadata": metadata, "kernel": os.uname().release,
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(), "mode": mode,
            "launcher": {"commit": launcher_commit, "bytes": len(launcher), "sha256": sha(launcher),
                         "blob": git_sha("blob", launcher)}, "capture_deadline_monotonic": POST_END}
    publisher = {"invocation_attempted": False, "retry_authorized": False}
    outcome = {"mode": mode, "classification": "indeterminate", "suite_executed": False,
               "accepted": False, "retry_authorized": False, "merge_authorized": False}
    journal = b""
    journal_attempted = False
    try:
        prepare(host)
        invoke(mode, publisher, host)
        journal_attempted = True
        status, journal, journal_err = tool(["/usr/bin/journalctl", "--unit=bowfinpr18-deadline.service", "--boot",
            "--output=json", "--no-pager", "--all", "-n", "128"], cap=262144)
        require(status == 0 and not journal_err, "deadline journal collection incomplete")
        entries = [decode(line) for line in journal.splitlines() if line]
        require(mode != "qualify-watchdog" or entries, "missing deadline journal")
        require(all(e.get("_BOOT_ID") == host["boot_id"].replace("-", "") for e in entries), "journal boot identity")
        # Python prints no normal output in deadline mode. Any process-origin
        # diagnostic could be a post-visible-JSON publication/fsync failure.
        require(not any(e.get("_TRANSPORT") == "stdout" for e in entries), "deadline publication diagnostic")
        require(mode != "qualify-watchdog" or any(e.get("_PID") == "1"
                and "Main process exited, code=exited, status=1/FAILURE" in e.get("MESSAGE", "")
                for e in entries), "deadline publisher exit journal coverage missing")
        require(len(entries) < 128, "deadline journal coverage potentially truncated")
        outcome = reconcile(mode, publisher, host)
    except Exception as error:
        outcome["error"] = type(error).__name__ + ": " + str(error)[:2048]
    finally:
        # Do not fake missing results or disarm/kill the watchdog on failure.
        # Platform loss or incomplete cleanup remains indeterminate.
        try:
            if publisher["invocation_attempted"] and "final_units" not in publisher:
                try:
                    publisher["final_units"] = final_units()
                except Exception as error:
                    publisher["final_units_unavailable"] = type(error).__name__
            if not journal_attempted:
                journal_attempted = True
                try:
                    _, journal, journal_err = tool(["/usr/bin/journalctl", "--unit=bowfinpr18-deadline.service",
                        "--boot", "--output=json", "--no-pager", "--all", "-n", "128"], cap=262144)
                    publisher["failure_journal_capture"] = "retained" if not journal_err else "diagnostic_present"
                except Exception as error:
                    publisher["failure_journal_capture"] = "unavailable: " + type(error).__name__
            retain_control()
            write(EXPORT / "host/deadline-journal.txt", journal, HOST_CAPS["host/deadline-journal.txt"])
            record("host/attestation.json", host)
            record("host/launch-status.json", publisher)
            record("host/final-state.json", outcome)
            report = ("# PR #18 qualification capture\n\nCase: `" + mode + "`\n\n"
                "Classification: `" + outcome["classification"] + "`\n\n"
                "This is unaccepted operational evidence pending independent review, not suite execution, "
                "acceptance, retry, merge, production evidence, or M0.1 completion.\n\n"
                "Reviewed workload: `" + COMMIT + "`, tree `" + TREE + "`.\n\n"
                "Host/source trust and all retained results are described in the exact closed inventory.\n")
            write(EXPORT / "report.md", report.encode("ascii"), HOST_CAPS["report.md"])
            inventory = []
            allowed_export = set(HOST_CAPS) | {"control/" + n + ".json" for n in CONTROL_JSON}
            allowed_export.update(("control/stdout", "control/stderr", "control/terminal.lock"))
            for path in sorted(EXPORT.rglob("*")):
                if path.is_dir():
                    require(not path.is_symlink() and path.relative_to(EXPORT).as_posix() in ("host", "control"),
                            "unapproved export directory")
                    continue
                name = path.relative_to(EXPORT).as_posix()
                require(name in allowed_export, "unapproved export path")
                cap = HOST_CAPS.get(name, 4194304 if name in ("control/stdout", "control/stderr") else
                    (0 if name == "control/terminal.lock" else 262144))
                raw = read(path, cap)
                inventory.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
            require(len(inventory) <= 27 and sum(e["bytes"] for e in inventory) <= 13828096, "export aggregate cap before inventory")
            record("inventory.json", {"record_class": "unaccepted_qualification_capture", "files": inventory,
                "mode": mode, "self_hash": "none", "accepted": False, "retry_authorized": False})
        except Exception as error:
            print("Retention failed; no favorable qualification claim: " + type(error).__name__, file=sys.stderr)
            return 2
    return 0 if outcome["classification"] == "qualification_observed_pending_independent_review" else 2


if __name__ == "__main__":
    raise SystemExit(main())
