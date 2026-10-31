"""Inert, proposed Linux host controller; execution needs separate owner authority.

This trusted root controller is outside the candidate cgroup. Docker/platform
observations are externally reported evidence, not raw child waitpid evidence.
No mode retries the suite. A fresh host and exclusive control directory are
required for each separately authorized qualification or suite invocation.
"""

import argparse
from contextlib import contextmanager
import fcntl
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
import time


ROOT = Path("/var/tmp/bowfin-pr18")
SOURCE = ROOT / "source"
CONTROL = ROOT / "control"
CGROUP = Path("/sys/fs/cgroup/bowfinpr18.slice")
PLAN = SOURCE / "containment/invocation.json"
IMAGE = "docker.io/library/python@sha256:2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301"
IMAGE_CONFIG = "sha256:9cb180cb36bd45dc786105b834d3cb5f3b1d69a6a63c79ca10fc64f108aa649a"
RUNTIME = "/usr/local/bin/python3.12"
UNITS = ("bowfinpr18.slice", "bowfinpr18-deadline.timer", "bowfinpr18-deadline.service")
STREAM_CAP = 4 * 1024 * 1024
TOOL_CAP = 256 * 1024
PRIMARY_SECONDS = 900
CLEANUP_SECONDS = 30
ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
       "DOCKER_CONFIG": str(CONTROL / "docker-config")}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key] = value
    return out


def finite_float(token):
    if len(token) > 128:
        raise ValueError("JSON float token limit")
    value = float(token)
    if not math.isfinite(value):
        raise ValueError("nonfinite JSON float")
    return value


def decode(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_float=finite_float,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def trusted(path, maximum=1024 * 1024):
    """The enclosing root materialization is immutable against the workload UID."""
    if not path.is_absolute():
        raise ValueError("absolute path required")
    for parent in [path, *path.parents]:
        info = parent.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise ValueError("symlink in trusted materialization")
        if info.st_uid != 0 or (parent != Path("/var/tmp") and info.st_mode & 0o022):
            raise ValueError("untrusted materialization ownership or permissions")
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("regular file required before open")
    with path.open("rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("regular file required")
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("trusted file limit exceeded")
    return raw


def record(name, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("ascii")
    if len(raw) > TOOL_CAP:
        raise ValueError("record limit")
    fd = os.open(CONTROL / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def terminal_lock():
    """Root-owned precreated inode; never unlink/replace it during this attempt."""
    fd = os.open(CONTROL / "terminal.lock", os.O_RDWR | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o077 or info.st_size != 0:
            raise ValueError("invalid terminal lock")
        expires = time.monotonic() + 5
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= expires:
                    raise RuntimeError("terminal lock timeout")
                time.sleep(0.01)
        yield
    finally:
        os.close(fd)  # SIGKILL/process exit also releases this kernel lock.


def bounded(argv, timeout=10, cap=TOOL_CAP):
    """Bound trusted tool time and both streams; never execute a shell."""
    proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=ENV, cwd=ROOT,
                            close_fds=True, start_new_session=True)
    sel = selectors.DefaultSelector()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    adverse = None
    expires = time.monotonic() + timeout
    try:
        for name in buffers:
            pipe = getattr(proc, name)
            os.set_blocking(pipe.fileno(), False)
            sel.register(pipe, selectors.EVENT_READ, name)
        while sel.get_map():
            if time.monotonic() >= expires:
                adverse = "tool_timeout"
                break
            for key, _ in sel.select(min(0.1, max(0, expires - time.monotonic()))):
                data = os.read(key.fd, min(65536, cap - len(buffers[key.data]) + 1))
                if not data:
                    sel.unregister(key.fileobj)
                    continue
                room = cap - len(buffers[key.data])
                buffers[key.data].extend(data[:room])
                if len(data) > room:
                    adverse = "tool_output_limit"
                    break
            if adverse:
                break
        if adverse:
            os.killpg(proc.pid, signal.SIGKILL)
        try:
            status = proc.wait(timeout=max(0.1, min(2, expires - time.monotonic())))
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            status = proc.wait(timeout=2)
            adverse = adverse or "tool_timeout"
        if adverse:
            raise RuntimeError(adverse)
        return status, bytes(buffers["stdout"]), bytes(buffers["stderr"])
    finally:
        sel.close()
        for name in buffers:
            getattr(proc, name).close()
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=2)


def checked(argv, timeout=10):
    status, out, err = bounded(argv, timeout)
    if status != 0:
        raise RuntimeError("trusted tool failed: " + argv[0] + ": " + err[:512].decode("utf-8", "replace"))
    return out


def inspect_container(identity):
    data = decode(checked(["/usr/bin/docker", "container", "inspect", identity]))
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError("invalid Docker inspection")
    return data[0]


def verify_plan(expected):
    if re.fullmatch(r"[0-9a-f]{64}", expected or "") is None:
        raise ValueError("explicit plan SHA-256 required")
    raw = trusted(PLAN, 65536)
    if sha(raw) != expected:
        raise ValueError("plan digest mismatch")
    plan = decode(raw)
    if set(plan) != {"format", "image", "source_files"} or plan["format"] != "bowfin-pr18-contained-run-v1" or plan["image"] != IMAGE:
        raise ValueError("unsupported plan")
    entries = plan["source_files"]
    if not isinstance(entries, list) or not 8 <= len(entries) <= 32:
        raise ValueError("invalid closed source manifest")
    seen = set()
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
            raise ValueError("invalid source descriptor")
        path = item["path"]
        if not isinstance(path, str) or path.startswith("/") or any(x in ("", ".", "..") for x in path.split("/")) or path in seen or path == "containment/invocation.json":
            raise ValueError("invalid source path")
        if type(item["bytes"]) is not int or not 0 <= item["bytes"] <= 1024 * 1024 or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None:
            raise ValueError("invalid source identity")
        seen.add(path)
        data = trusted(SOURCE / path)
        if len(data) != item["bytes"] or sha(data) != item["sha256"]:
            raise ValueError("source identity mismatch")
    actual = set()
    directory_count = 0
    expected_dirs = {str(Path(path).parent) for path in seen | {"containment/invocation.json"}}
    expected_dirs |= {str(parent) for path in list(expected_dirs) for parent in Path(path).parents}
    for directory, dirs, files in os.walk(SOURCE, followlinks=False):
        directory_count += 1
        if directory_count > 16 or len(dirs) + len(files) > 64:
            raise ValueError("materialization enumeration bound exceeded")
        for name in dirs:
            p = Path(directory) / name
            info = p.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
                raise ValueError("invalid source directory")
            if p.relative_to(SOURCE).as_posix() not in expected_dirs:
                raise ValueError("unexpected source directory")
        for name in files:
            actual.add((Path(directory) / name).relative_to(SOURCE).as_posix())
        if len(actual) > 33:
            raise ValueError("unexpected materialized files")
    if actual != seen | {"containment/invocation.json"}:
        raise ValueError("source path set mismatch")
    required = {"supervisor.py", "test_supervisor.py", "runtime-pin.json", "containment/controller.py", "containment/probe.py", "containment/seccomp.json"}
    required.update("containment/" + name for name in UNITS)
    if not required <= seen:
        raise ValueError("missing required source")
    for name in UNITS:
        if trusted(Path("/run/systemd/system") / name, 16384) != trusted(SOURCE / "containment" / name, 16384):
            raise ValueError("installed unit differs from reviewed source")
    return plan


def bus_property(unit, interface, name):
    escaped = unit.replace("-", "_2d").replace(".", "_2e")
    return shlex.split(checked(["/usr/bin/busctl", "get-property", "org.freedesktop.systemd1",
                       "/org/freedesktop/systemd1/unit/" + escaped,
                       "org.freedesktop.systemd1." + interface, name]).decode("ascii"))


def verify_loaded_units():
    """Reject stale/drop-in modified units; setup must have daemon-reloaded them."""
    retained = {}
    for name in UNITS:
        raw = checked(["/usr/bin/systemctl", "show", name, "--property=FragmentPath",
                       "--property=DropInPaths", "--property=LoadState"])
        properties = dict(line.split("=", 1) for line in raw.decode("utf-8").splitlines())
        if properties != {"FragmentPath": "/run/systemd/system/" + name,
                          "DropInPaths": "", "LoadState": "loaded"}:
            raise RuntimeError("unexpected loaded unit or drop-ins")
        retained[name] = properties
    for name in UNITS[1:]:
        if bus_property(name, "Unit", "ActiveState") != ["s", "inactive"]:
            raise RuntimeError("deadline unit already active or failed")
    expected = {("Service", "Type"): ["s", "exec"], ("Service", "Restart"): ["s", "no"],
                ("Service", "RuntimeMaxUSec"): ["t", "45000000"],
                ("Service", "TimeoutStopUSec"): ["t", "5000000"],
                ("Service", "KillMode"): ["s", "control-group"],
                ("Service", "Slice"): ["s", "system.slice"]}
    for (interface, key), value in expected.items():
        if bus_property("bowfinpr18-deadline.service", interface, key) != value:
            raise RuntimeError("unexpected effective deadline service property")
    command = checked(["/usr/bin/systemctl", "show", "bowfinpr18-deadline.service", "--property=ExecStart", "--value"]).decode("ascii")
    exact = "{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 -I /var/tmp/bowfin-pr18/source/containment/controller.py deadline ; ignore_errors=no ;"
    if not command.startswith(exact) or command.count("path=") != 1:
        raise RuntimeError("unexpected effective deadline command")
    timers = bus_property("bowfinpr18-deadline.timer", "Timer", "TimersMonotonic")
    if len(timers) != 5 or timers[:4] != ["a(stt)", "1", "OnActiveUSec", "960000000"]:
        raise RuntimeError("unexpected timer interval")
    if bus_property("bowfinpr18-deadline.timer", "Timer", "AccuracyUSec") != ["t", "1000000"] or bus_property("bowfinpr18-deadline.timer", "Timer", "RandomizedDelayUSec") != ["t", "0"]:
        raise RuntimeError("unexpected timer accuracy or randomization")
    if bus_property("bowfinpr18-deadline.timer", "Timer", "WakeSystem") != ["b", "false"]:
        raise RuntimeError("timer must use CLOCK_MONOTONIC, not boottime")
    record("loaded-units.json", retained)


def quiesce_watchdog(earliest_deadline):
    """Called with terminal lock held, after confirmed workload cleanup.

    Stopping a timer alone cannot drain an activated service. Positive sealing
    needs pre-expiry timer disarm, a separate synchronous service stop, and
    manager readback. Absolute monotonic time is essential: zeroed history after
    unit garbage collection must never rehabilitate a post-deadline completion.
    """
    if type(earliest_deadline) is not int or earliest_deadline <= 0:
        raise ValueError("missing armed monotonic deadline")
    def before_deadline():
        now = time.monotonic_ns() // 1000
        if now >= earliest_deadline:
            raise RuntimeError("not strictly before independent deadline")
        return now
    before = before_deadline()
    timer = "bowfinpr18-deadline.timer"
    service = "bowfinpr18-deadline.service"
    pre_disarm = {"active_state": bus_property(timer, "Unit", "ActiveState"),
                  "last_trigger": bus_property(timer, "Timer", "LastTriggerUSecMonotonic"),
                  "next_elapse": bus_property(timer, "Timer", "NextElapseUSecMonotonic")}
    if pre_disarm != {"active_state": ["s", "active"], "last_trigger": ["t", "0"],
                      "next_elapse": ["t", str(earliest_deadline)]}:
        raise RuntimeError("timer is not the untriggered armed deadline")
    checked(["/usr/bin/systemctl", "stop", timer])
    stopped_before = before_deadline()
    # This drains/cancels already queued or active deadline-service work; it is
    # safe to disarm cleanup only because workload cleanup is already proven.
    checked(["/usr/bin/systemctl", "stop", service])
    observations = {}
    for unit in (timer, service):
        active = bus_property(unit, "Unit", "ActiveState")
        job = bus_property(unit, "Unit", "Job")
        if active != ["s", "inactive"] or job != ["(uo)", "0", "/"]:
            raise RuntimeError("watchdog unit not quiescent")
        observations[unit] = {"active_state": active, "job": job}
    history = {"service_substate": bus_property(service, "Unit", "SubState"),
               "service_inactive_exit_usec": bus_property(service, "Unit", "InactiveExitTimestampMonotonic"),
               "service_exec_start_usec": bus_property(service, "Service", "ExecMainStartTimestampMonotonic"),
               "timer_last_trigger_usec": bus_property(timer, "Timer", "LastTriggerUSecMonotonic")}
    if history != {"service_substate": ["s", "dead"], "service_inactive_exit_usec": ["t", "0"],
                   "service_exec_start_usec": ["t", "0"], "timer_last_trigger_usec": ["t", "0"]}:
        raise RuntimeError("deadline activation history is not empty")
    if (CONTROL / "deadline-fired.json").exists():
        raise RuntimeError("deadline event recorded")
    return {"earliest_deadline_usec": earliest_deadline,
            "before_disarm_usec": before, "timer_stopped_usec": stopped_before,
            "reconciled_usec": before_deadline(), "units": observations,
            "pre_disarm": pre_disarm, "history": history}


def finish(output, armed, earliest_deadline, intent):
    """A provisional result is never favorable terminal evidence on its own."""
    provisional = dict(output, classification="provisional",
                       candidate_classification=output["classification"], provisional=True)
    record("result.json", provisional)
    with terminal_lock():
        if (CONTROL / "terminal.json").exists():
            return False  # An adverse deadline disposition already won.
        terminal = {"origin": "controller", "classification": "indeterminate",
                    "plan_sha256": intent["plan_sha256"],
                    "result_sha256": sha(trusted(CONTROL / "result.json", TOOL_CAP)),
                    "accepted": False, "retry_authorized": False, "merge_authorized": False}
        if armed and output.get("cleanup_complete"):
            try:
                terminal["watchdog"] = quiesce_watchdog(earliest_deadline)
                if output["classification"] != "indeterminate":
                    terminal["classification"] = "watchdog_quiescent_pending_independent_review"
            except Exception as error:
                terminal["error"] = type(error).__name__ + ": " + str(error)[:2048]
        record("terminal.json", terminal)
        return terminal["classification"] == "watchdog_quiescent_pending_independent_review"


def cgroup_kill():
    with (CGROUP / "cgroup.kill").open("w", encoding="ascii") as out:
        out.write("1\n")


def population():
    raw = (CGROUP / "cgroup.events").read_text(encoding="ascii")
    if len(raw) > 4096:
        raise ValueError("unexpected cgroup event size")
    values = dict(line.split() for line in raw.splitlines())
    if values.get("populated") not in ("0", "1"):
        raise ValueError("missing recursive population observation")
    return raw, values["populated"]


def cleanup(intent, prefix, arbitration_error=None):
    """Fence delayed starts by exact container removal, then prove group empty."""
    result = {"complete": False, "live_tasks_absent": False, "all_zombies_reaped": False,
              "container_removed": False, "terminal_container_state": None, "errors": []}
    if prefix == "deadline":
        result["terminal_arbitration_error"] = arbitration_error
    deadline = time.monotonic() + CLEANUP_SECONDS
    try:
        ownership = decode(trusted(CONTROL / "cgroup-owned.json", 4096))
        if ownership != {"path": str(CGROUP), "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip(), "plan_sha256": intent["plan_sha256"]}:
            raise ValueError("no exact cgroup ownership proof; refuse kill")
        descriptor = decode(trusted(CONTROL / "container.json", 4096))
        cid = descriptor["id"]
        if re.fullmatch(r"[0-9a-f]{64}", cid) is None:
            raise ValueError("invalid exact container ID")
        # Independent kernel kill remains available if the Docker daemon fails.
        cgroup_kill()
        info = inspect_container(cid)
        if info["Id"] != cid or info["Name"] != "/" + intent["name"] or info["Config"]["Labels"].get("org.bowfin.pr18.plan") != intent["plan_sha256"]:
            raise ValueError("container identity mismatch; refuse removal")
        while info["State"]["Running"] and time.monotonic() < deadline - 15:
            time.sleep(0.05)
            info = inspect_container(cid)
        if not info["State"]["Running"]:
            result["terminal_container_state"] = info["State"]
        checked(["/usr/bin/docker", "container", "rm", "--force", cid], timeout=10)
        result["container_removed"] = True
        cgroup_kill()
        while time.monotonic() < deadline:
            raw, populated = population()
            if populated == "0":
                result["cgroup_events"] = raw
                result["live_tasks_absent"] = True
                result["complete"] = True
                break
            time.sleep(0.05)
        if not result["complete"]:
            raise RuntimeError("cleanup deadline without empty-group proof")
    except Exception as error:
        result["errors"].append(type(error).__name__ + ": " + str(error)[:1024])
    record(prefix + "-cleanup.json", result)
    return result


def deadline_mode():
    intent = decode(trusted(CONTROL / "intent.json", 4096))
    arbitration_error = None
    try:
        # Record activation before waiting for arbitration. Cleanup must remain
        # available even if a stalled controller retains the terminal lock.
        record("deadline-fired.json", {"reason": "independent_systemd_deadline", "monotonic": time.monotonic()})
        with terminal_lock():
            if not (CONTROL / "terminal.json").exists():
                record("terminal.json", {"origin": "deadline", "classification": "indeterminate",
                       "plan_sha256": intent["plan_sha256"], "accepted": False,
                       "retry_authorized": False, "merge_authorized": False})
    except Exception as error:
        arbitration_error = type(error).__name__ + ": " + str(error)[:2048]
    # No lock is held over cleanup; marker/lock failure cannot suppress it.
    result = cleanup(intent, "deadline", arbitration_error)
    return 1 if result["complete"] else 2


def create_argv(mode, plan_sha):
    command = ["/usr/bin/docker", "container", "create", "--pull", "never", "--interactive", "--name", "bowfinpr18-" + mode,
               "--label", "org.bowfin.pr18.plan=" + plan_sha,
               "--platform", "linux/amd64", "--cgroup-parent", "bowfinpr18.slice", "--cgroupns", "private",
               "--network", "none", "--ipc", "private", "--user", "65532:65532", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges", "--security-opt", "seccomp=" + str(SOURCE / "containment/seccomp.json"),
               "--read-only", "--cpu-period", "100000", "--cpu-quota", "200000", "--memory", "512m", "--memory-swap", "512m", "--pids-limit", "64",
               "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=67108864,nr_inodes=4096,mode=1777",
               "--shm-size", "1m", "--log-driver", "none", "--restart", "no",
               "--mount", "type=bind,src=" + str(SOURCE) + ",dst=/reviewed,readonly,bind-propagation=rprivate",
               "--workdir", "/tmp", "--entrypoint", "/usr/bin/env", IMAGE,
               "-i", "LANG=C", "LC_ALL=C", "TZ=UTC", RUNTIME, "-I", "-B",
               "/reviewed/containment/probe.py"]
    if mode == "suite":
        command.append("--suite-gate")
    return command


def check_container(info, mode):
    cfg, host = info["Config"], info["HostConfig"]
    command = create_argv(mode, "0" * 64)
    expected_cmd = command[command.index(IMAGE) + 1:]
    if info["Image"] != IMAGE_CONFIG or cfg["Image"] != IMAGE or cfg["User"] != "65532:65532" or cfg["Entrypoint"] != ["/usr/bin/env"] or cfg["Cmd"] != expected_cmd or cfg["Tty"] is not False or cfg["OpenStdin"] is not True or cfg.get("AttachStdin") is not True or cfg.get("StdinOnce") is not True:
        raise ValueError("created image or process configuration mismatch")
    checks = {"ReadonlyRootfs": True, "Privileged": False, "NetworkMode": "none", "IpcMode": "private", "PidMode": "", "UTSMode": "", "CgroupnsMode": "private", "CgroupParent": "bowfinpr18.slice", "CpuPeriod": 100000, "CpuQuota": 200000, "Memory": 536870912, "MemorySwap": 536870912, "PidsLimit": 64, "ShmSize": 1048576}
    if any(host.get(key) != value for key, value in checks.items()) or host["CapDrop"] != ["ALL"] or host.get("CapAdd") not in (None, []) or host["RestartPolicy"] != {"Name": "no", "MaximumRetryCount": 0} or host["LogConfig"] != {"Type": "none", "Config": {}}:
        raise ValueError("created containment or resource configuration mismatch")
    if host.get("Devices") not in (None, []) or host.get("DeviceRequests") not in (None, []) or host.get("Binds") not in (None, []) or host.get("PortBindings") not in (None, {}):
        raise ValueError("unexpected device, bind, or port grant")
    if host["Tmpfs"] != {"/tmp": "rw,nosuid,nodev,noexec,size=67108864,nr_inodes=4096,mode=1777"}:
        raise ValueError("tmpfs mismatch")
    mounts = host["Mounts"]
    if len(mounts) != 1 or mounts[0].get("Type") != "bind" or mounts[0].get("Source") != str(SOURCE) or mounts[0].get("Target") != "/reviewed" or mounts[0].get("ReadOnly") is not True or mounts[0].get("BindOptions", {}).get("Propagation") != "rprivate":
        raise ValueError("source mount mismatch")
    security = host["SecurityOpt"]
    if not isinstance(security, list) or len(security) != 2 or security[0] != "no-new-privileges" or not security[1].startswith("seccomp=") or decode(security[1][8:].encode("utf-8")) != decode(trusted(SOURCE / "containment/seccomp.json")):
        raise ValueError("effective security policy mismatch")


def live_gate(cid):
    info = inspect_container(cid)
    pid = info["State"]["Pid"]
    if type(pid) is not int or pid <= 1 or info["State"]["Running"] is not True:
        raise ValueError("invalid live container PID")
    expected = "/bowfinpr18.slice/docker-" + cid + ".scope"
    with Path(f"/proc/{pid}/cgroup").open() as stream:
        membership = stream.read(4097)
    if membership != "0::" + expected + "\n":
        raise ValueError("container outside exact dedicated cgroup")
    observations = {"host_pid": pid, "membership": membership, "limits": {}, "namespaces": {}}
    limits = {"cpu.max": "200000 100000", "memory.max": "536870912", "memory.swap.max": "0", "pids.max": "64"}
    for name, required in limits.items():
        with (Path("/sys/fs/cgroup") / expected.lstrip("/") / name).open() as stream:
            value = stream.read(129).strip()
        if value != required:
            raise ValueError("live cgroup resource limit mismatch")
        observations["limits"][name] = value
    for namespace in ("mnt", "pid", "net", "cgroup", "ipc", "uts"):
        candidate = os.readlink(f"/proc/{pid}/ns/{namespace}")
        if candidate == os.readlink(f"/proc/self/ns/{namespace}"):
            raise ValueError("shared host namespace")
        observations["namespaces"][namespace] = candidate
    return info, observations


def attach(cid, mode, expires):
    proc = subprocess.Popen(["/usr/bin/docker", "container", "start", "--attach", "--interactive", cid],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=ENV, cwd=ROOT, close_fds=True, start_new_session=True)
    selector = selectors.DefaultSelector()
    counts = {"stdout": 0, "stderr": 0}
    hashes = {name: hashlib.sha256() for name in counts}
    files = {}
    marker = bytearray()
    released = False
    result = {"docker_attach_status": None, "reason": None, "streams_complete": False,
              "release_confirmed": False}
    try:
        for name in counts:
            fd = os.open(CONTROL / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            files[name] = os.fdopen(fd, "wb")
            pipe = getattr(proc, name)
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, name)
        while selector.get_map():
            if time.monotonic() >= expires or (CONTROL / "deadline-fired.json").exists():
                result["reason"] = "deadline"
                break
            for key, _ in selector.select(0.1):
                data = os.read(key.fd, min(65536, STREAM_CAP - counts[key.data] + 1))
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                room = STREAM_CAP - counts[key.data]
                retained = data[:room]
                files[key.data].write(retained)
                hashes[key.data].update(retained)
                counts[key.data] += len(retained)
                if key.data == "stdout" and len(marker) < 65536:
                    marker.extend(retained[:65536 - len(marker)])
                if len(data) > room:
                    result["reason"] = "output_limit"
                    break
            if result["reason"]:
                break
            if not released and b"BOWFIN_PR18_GATE_READY\n" in marker:
                info, observations = live_gate(cid)
                check_container(info, mode)
                record("live-gate.json", observations)
                if time.monotonic() >= expires or (CONTROL / "deadline-fired.json").exists():
                    raise RuntimeError("deadline before release")
                proc.stdin.write(b"GO\n")
                proc.stdin.flush()
                proc.stdin.close()
                released = True
            if released and b"BOWFIN_PR18_RELEASE_CONFIRMED\n" in marker:
                result["release_confirmed"] = True
            if mode in ("qualify", "qualify-watchdog") and result["release_confirmed"] and b"BOWFIN_PR18_PROBE_READY\n" in marker:
                info, observations = live_gate(cid)
                pid = info["State"]["Pid"]
                if type(pid) is not int or pid <= 1:
                    raise ValueError("invalid host container PID")
                membership = Path(f"/proc/{pid}/cgroup").read_text(encoding="ascii")
                if not membership.startswith("0::/bowfinpr18.slice/"):
                    raise ValueError("container outside dedicated slice")
                with Path(f"/proc/{pid}/task/{pid}/children").open(encoding="ascii") as stream:
                    children = stream.read(4097).split()
                if len(children) != 1 or not children[0].isdigit():
                    raise ValueError("qualification child not uniquely observed")
                child = int(children[0])
                child_membership = Path(f"/proc/{child}/cgroup").read_text(encoding="ascii")
                if child_membership != membership or os.getsid(child) != child:
                    raise ValueError("new-session child containment not demonstrated")
                record("qualification-membership.json", {"init_pid": pid, "child_pid": child,
                       "init_cgroup": membership, "child_cgroup": child_membership,
                       "child_session": os.getsid(child)})
                if mode == "qualify-watchdog":
                    for stream in files.values():
                        stream.flush()
                        os.fsync(stream.fileno())
                    record("watchdog-test-ready.json", {"controller_pid": os.getpid(),
                           "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip(),
                           "fault": "intentional_controller_SIGKILL", "expected_main_result": "absent"})
                    os.kill(os.getpid(), signal.SIGKILL)
                    raise RuntimeError("intentional SIGKILL unexpectedly returned")
                result["reason"] = "qualification_cleanup_probe"
                break
        if result["reason"] is None:
            result["streams_complete"] = True
            result["docker_attach_status"] = proc.wait(timeout=2)
            if not released or not result["release_confirmed"]:
                result["reason"] = "release_not_confirmed"
        else:
            os.killpg(proc.pid, signal.SIGKILL)
            result["docker_attach_status"] = proc.wait(timeout=2)
    finally:
        selector.close()
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=2)
        for name, stream in files.items():
            stream.flush()
            os.fsync(stream.fileno())
            stream.close()
            with (CONTROL / name).open("rb") as retained:
                actual = retained.read(STREAM_CAP + 1)
            if len(actual) != counts[name] or hashlib.sha256(actual).digest() != hashes[name].digest():
                raise RuntimeError("retained stream readback mismatch")
        if proc.stdin is not None and not proc.stdin.closed:
            proc.stdin.close()
        for name in counts:
            getattr(proc, name).close()
        result["streams"] = {name: {"bytes": counts[name], "sha256": hashes[name].hexdigest()} for name in counts}
        record("attach.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("qualify", "qualify-watchdog", "suite", "deadline"))
    parser.add_argument("--plan-sha256")
    args = parser.parse_args()
    if os.getuid() != 0:
        raise RuntimeError("trusted host controller requires root")
    if "/bowfinpr18.slice" in Path("/proc/self/cgroup").read_text(encoding="ascii"):
        raise RuntimeError("controller must remain outside workload slice")
    if args.mode == "deadline":
        return deadline_mode()
    verify_plan(args.plan_sha256)
    CONTROL.mkdir(mode=0o700)  # Exclusive attempt reservation; never resume/reuse.
    (CONTROL / "docker-config").mkdir(mode=0o700)
    lock_fd = os.open(CONTROL / "terminal.lock", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.close(lock_fd)
    intent = {"mode": args.mode, "name": "bowfinpr18-" + args.mode,
              "plan_sha256": args.plan_sha256, "image": IMAGE, "attempt_reusable": False}
    record("intent.json", intent)
    output = {"classification": "indeterminate", "accepted": False, "merge_authorized": False,
              "retry_authorized": False, "error": None}
    armed = False
    earliest_deadline = None
    try:
        verify_loaded_units()
        daemon = decode(checked(["/usr/bin/docker", "info", "--format", "{{json .}}"] ))
        if daemon.get("CgroupDriver") != "systemd" or daemon.get("CgroupVersion") != "2":
            raise RuntimeError("requires Docker systemd cgroup-v2 driver")
        image = decode(checked(["/usr/bin/docker", "image", "inspect", IMAGE]))
        accepted_repo = "python@sha256:2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301"
        if not isinstance(image, list) or len(image) != 1 or image[0].get("Id") != IMAGE_CONFIG or image[0].get("Os") != "linux" or image[0].get("Architecture") != "amd64" or not ({IMAGE, accepted_repo} & set(image[0].get("RepoDigests", []))):
            raise RuntimeError("materialized image identity mismatch")
        record("platform.json", {"docker": {key: daemon.get(key) for key in ("ServerVersion", "CgroupDriver", "CgroupVersion", "KernelVersion", "OperatingSystem", "OSType", "Architecture")}, "image": {"Id": image[0]["Id"], "RepoDigests": image[0]["RepoDigests"]}, "kernel": os.uname().release,
               "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip(),
               "systemd_version": checked(["/usr/bin/systemctl", "--version"]).decode("utf-8")})
        checked(["/usr/bin/systemctl", "start", "bowfinpr18.slice"])
        actual = checked(["/usr/bin/systemctl", "show", "bowfinpr18.slice", "--property=ControlGroup", "--value"]).decode("ascii").strip()
        if actual != "/bowfinpr18.slice" or population()[1] != "0":
            raise RuntimeError("unexpected or occupied workload slice")
        if (CGROUP / "cgroup.type").read_text(encoding="ascii").strip() != "domain":
            raise RuntimeError("non-threaded domain cgroup required")
        record("cgroup-owned.json", {"path": str(CGROUP), "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip(), "plan_sha256": args.plan_sha256})
        create = create_argv(args.mode, args.plan_sha256)
        record("create-argv.json", create)
        cid = checked(create, timeout=30).decode("ascii").strip()
        if re.fullmatch(r"[0-9a-f]{64}", cid) is None:
            raise ValueError("Docker did not return one full container ID")
        record("container.json", {"id": cid})
        created = inspect_container(cid)
        check_container(created, args.mode)
        record("container-created.json", created)
        started = time.monotonic()
        checked(["/usr/bin/systemctl", "start", "bowfinpr18-deadline.timer"])
        armed = True
        timer = checked(["/usr/bin/systemctl", "show", "bowfinpr18-deadline.timer",
                         "--property=ActiveState", "--property=NextElapseUSecMonotonic", "--property=Unit"]).decode("ascii")
        if "ActiveState=active\n" not in timer or "Unit=bowfinpr18-deadline.service\n" not in timer:
            raise RuntimeError("independent deadline is not armed")
        next_elapse = bus_property("bowfinpr18-deadline.timer", "Timer", "NextElapseUSecMonotonic")
        if len(next_elapse) != 2 or next_elapse[0] != "t" or not next_elapse[1].isdigit() or not started + 959 <= int(next_elapse[1]) / 1000000 <= started + 962 or time.monotonic() >= int(next_elapse[1]) / 1000000:
            raise RuntimeError("deadline expiry is not finite and within reviewed bound")
        earliest_deadline = int(next_elapse[1])
        record("timer-armed.json", {"properties": timer, "next_elapse_usec": int(next_elapse[1]), "controller_monotonic": started})
        if (CONTROL / "deadline-fired.json").exists():
            raise RuntimeError("deadline already fired; no launch")
        captured = attach(cid, args.mode, started + PRIMARY_SECONDS)
        cleaned = cleanup(intent, "controller")
        output["cleanup_complete"] = cleaned["complete"]
        state = cleaned["terminal_container_state"]
        if args.mode == "suite" and captured["reason"] is None and captured["streams_complete"] and captured["release_confirmed"] and captured["docker_attach_status"] == 0 and cleaned["complete"] and isinstance(state, dict) and state.get("Running") is False and state.get("ExitCode") == 0 and state.get("OOMKilled") is False and state.get("Error") == "" and state.get("StartedAt", "").startswith("20") and state.get("FinishedAt", "").startswith("20") and not (CONTROL / "deadline-fired.json").exists():
            output["classification"] = "docker_reported_suite_exit_zero_pending_independent_review"
        elif args.mode == "qualify" and captured["reason"] == "qualification_cleanup_probe" and captured["release_confirmed"] and cleaned["complete"] and not (CONTROL / "deadline-fired.json").exists():
            output["classification"] = "qualification_probe_and_cleanup_observed_pending_review"
    except Exception as error:
        output["error"] = type(error).__name__ + ": " + str(error)[:2048]
        if not (CONTROL / "controller-cleanup.json").exists():
            cleaned = cleanup(intent, "controller")
            output["cleanup_complete"] = cleaned["complete"]
    finally:
        favorable_terminal = finish(output, armed, earliest_deadline, intent)
    return 0 if favorable_terminal else 2


if __name__ == "__main__":
    raise SystemExit(main())
