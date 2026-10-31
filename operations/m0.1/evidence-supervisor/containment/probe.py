"""Benign containment qualification only; not authority to execute the suite."""

import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import sys
import time


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    require(sys.argv[1:] in ([], ["--suite-gate"]), "unexpected qualification arguments")
    runtime = Path("/usr/local/bin/python3.12")
    require(Path(sys.executable).resolve() == runtime, "wrong interpreter path")
    with runtime.open("rb") as stream:
        runtime_bytes = stream.read(14481)
    require(len(runtime_bytes) == 14480 and hashlib.sha256(runtime_bytes).hexdigest() == "4dbf3143240288fb2170257ffaa7bd030cdda5d2703d1f5f30b627042267e2e3", "interpreter digest mismatch")
    require(os.getuid() == 65532 and os.getgid() == 65532, "wrong unprivileged identity")
    require(dict(os.environ) == {"LANG": "C", "LC_ALL": "C", "TZ": "UTC"}, "unexpected environment")
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    for name in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"):
        require(int(status[name].strip(), 16) == 0, "capabilities remain")
    require(status["NoNewPrivs"].strip() == "1", "no-new-privileges absent")
    require(status["Seccomp"].strip() == "2", "seccomp filtering absent")
    require(sorted(p.name for p in Path("/sys/class/net").iterdir()) == ["lo"], "non-loopback interface")
    for path in (Path("/"), Path("/reviewed")):
        require(os.statvfs(path).f_flag & os.ST_RDONLY, "writable root or source mount")
    require(os.statvfs("/sys/fs/cgroup").f_flag & os.ST_RDONLY, "writable cgroup filesystem")
    require(Path("/proc/self/cgroup").read_text() == "0::/\n", "nonprivate cgroup view")
    for path in ("/var/run/docker.sock", "/run/containerd/containerd.sock"):
        require(not Path(path).exists(), "host runtime socket exposed")
    scratch = Path("/tmp/bowfin-proc-probe")
    scratch.mkdir(mode=0o700)
    (scratch / "file").write_bytes(b"qualification only\n")
    for path, flags in ((scratch, os.O_RDONLY | os.O_DIRECTORY), (scratch / "file", os.O_RDONLY)):
        fd = os.open(path, flags)
        try:
            require(os.readlink(f"/proc/self/fd/{fd}") == str(path), "procfs fd classifier unavailable")
        finally:
            os.close(fd)
    signal.alarm(60)
    print("BOWFIN_PR18_GATE_READY", flush=True)
    received = bytearray()
    while len(received) < 4:
        part = os.read(0, 4 - len(received))
        if not part:
            break
        received.extend(part)
    require(bytes(received) == b"GO\n", "no exact bounded release")
    signal.alarm(0)
    null = os.open("/dev/null", os.O_RDONLY)
    os.dup2(null, 0)
    if null != 0:
        os.close(null)
    print("BOWFIN_PR18_RELEASE_CONFIRMED", flush=True)
    if sys.argv[1:] == ["--suite-gate"]:
        runtime = "/usr/local/bin/python3.12"
        os.execve(runtime, [runtime, "-I", "-B", "/reviewed/test_supervisor.py", "-v"],
                  {"LANG": "C", "LC_ALL": "C", "TZ": "UTC"})
    # The probe and child remain alive for external membership and cgroup-kill
    # observation. Alarm is last-resort bounded lifetime, not cleanup evidence.
    signal.alarm(1000)
    reader, writer = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(reader)
        os.setsid()
        signal.alarm(1000)
        os.write(writer, b"ready")
        os.close(writer)
        while True:
            signal.pause()
    os.close(writer)
    require(os.read(reader, 5) == b"ready", "new-session child not ready")
    os.close(reader)
    print(json.dumps({"uid": os.getuid(), "gid": os.getgid(), "pid": os.getpid(),
                      "child_pid": child, "child_session": os.getsid(child),
                      "cgroup": Path("/proc/self/cgroup").read_text(),
                      "proc_fd_usable": True, "loopback_permitted": True}, sort_keys=True), flush=True)
    print("BOWFIN_PR18_PROBE_READY", flush=True)
    while True:
        signal.pause()


if __name__ == "__main__":
    main()
