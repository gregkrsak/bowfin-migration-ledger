#!/usr/bin/env python3
"""DRAFT: retain one directly observed child result; never authorize an execution.

This Linux/CPython 3.12 operational wrapper is not the migration verifier. A
separately reviewed, explicitly authorized caller must authenticate every map
dependency, establish freshness, and provide read-only roots and external job
containment. Only ``supervisor_execution`` is interpreted here; the complete map
bytes are nevertheless hash-bound. There is no shell, retry, or recovery launch.

The trusted child and supervisor share a UID. This is NOT a sandbox against a
hostile child. Network denial, CPU/memory/process limits, a hard outer deadline,
and orphan cleanup belong to the enclosing runner. Kernel-blocked I/O, SIGKILL,
host loss, or disk failure may prevent a receipt. A reserved attempt with no
valid receipt remains consumed and indeterminate.
"""

import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time


MAP_LIMIT = 128 * 1024
RECORD_LIMIT = 256 * 1024
STREAM_LIMIT = 1024 * 1024
READ_LIMIT = 64 * 1024
TERM_GRACE = 2.0
CLEANUP_LIMIT = 5.0
EOF_GRACE = 2.0
ENVIRONMENT = {"LANG": "C", "LC_ALL": "C", "TZ": "UTC"}
EXECUTION_FIELDS = {
    "attempt_id", "subject_commit", "subject_tree", "argv", "cwd",
    "runtime_sha256", "supervisor_sha256", "timeout_seconds",
}


def _utc():
    """Report an observation time, never an invented kernel event time."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _hex(value, length):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{%d}" % length, value) is None:
        raise ValueError("invalid hexadecimal identity")
    return value


def _object(pairs):
    """Reject duplicate keys instead of letting later values silently win."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(_value):
    raise ValueError("nonfinite JSON number")


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite JSON number")
    return number


def _bounded_read(source, maximum):
    parts = []
    remaining = maximum + 1
    while remaining:
        chunk = source.read(min(READ_LIMIT, remaining))
        if not chunk:
            break
        parts.append(chunk)
        remaining -= len(chunk)
    raw = b"".join(parts)
    if len(raw) > maximum:
        raise ValueError("file exceeds its byte limit")
    return raw


def _regular_bytes(path, maximum):
    """Read one bounded regular file without following its final symlink."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError("not a regular file")
        return _bounded_read(source, maximum)


def _directory(path):
    """Reject relative, non-normalized, symlinked, or non-directory roots.

    This precheck is not protection against concurrent same-UID replacement;
    stable materialization is an explicit enclosing-runner requirement.
    """
    if not isinstance(path, str) or len(path) > 4096 or "\0" in path:
        raise ValueError("invalid directory path")
    if not os.path.isabs(path) or path.startswith("//") or os.path.normpath(path) != path:
        raise ValueError("directory must be an absolute normalized path")
    current = Path(path).anchor
    for component in Path(path).parts[1:]:
        current = os.path.join(current, component)
        if not stat.S_ISDIR(os.lstat(current).st_mode):
            raise ValueError("directory path contains a symlink or non-directory")
    return path


def _serialized(value):
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      indent=2) + "\n").encode("ascii")
    if len(raw) > RECORD_LIMIT:
        raise ValueError("record exceeds its byte limit")
    return raw


def _exclusive_file(directory_fd, name):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=directory_fd)
    return os.fdopen(fd, "wb")


def _write_record(directory_fd, name, raw):
    with _exclusive_file(directory_fd, name) as target:
        target.write(raw)
        target.flush()
        os.fsync(target.fileno())
    os.fsync(directory_fd)


def _publish_receipt(directory_fd, receipt):
    """Publish complete bytes without replacing an existing receipt.

    receipt.tmp survives until the final link and directory sync succeed.
    Readers reject any leftover temp. A failure at any step is a publication
    failure, even if a final filename is visible. No recovery launch is allowed.
    """
    _write_record(directory_fd, "receipt.tmp", _serialized(receipt))
    os.link("receipt.tmp", "receipt.json", src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd, follow_symlinks=False)
    os.fsync(directory_fd)
    os.unlink("receipt.tmp", dir_fd=directory_fd)
    os.fsync(directory_fd)


def _configuration(args):
    if sys.platform != "linux" or sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
        raise ValueError("requires reviewed Linux CPython 3.12 environment")
    if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
        raise ValueError("requires default SIGCHLD disposition and exclusive child reaping")
    expected = _hex(args.map_sha256, 64)
    raw = _regular_bytes(args.map, MAP_LIMIT)
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("map digest mismatch")
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if blob != _hex(args.map_blob, 40):
        raise ValueError("map Git blob mismatch")
    parsed = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                        parse_constant=_nonfinite, parse_float=_finite_float)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("supervisor_execution"), dict):
        raise ValueError("missing supervisor_execution object")
    execution = parsed["supervisor_execution"]
    if set(execution) != EXECUTION_FIELDS:
        raise ValueError("unexpected execution fields")
    attempt = execution["attempt_id"]
    if attempt == "M0.1-EVIDENCE-02":
        kind = "evidence"
    elif isinstance(attempt, str) and re.fullmatch(r"M0\.1-SYNTHETIC-[0-9]{3}", attempt):
        kind = "synthetic"
    else:
        raise ValueError("unsupported attempt identity")
    argv = execution["argv"]
    if not isinstance(argv, list) or not 3 <= len(argv) <= 256:
        raise ValueError("invalid argv length")
    if any(not isinstance(token, str) or not token or len(token.encode("utf-8")) > 4096 or "\0" in token for token in argv):
        raise ValueError("invalid argv token")
    if sum(len(token.encode("utf-8")) for token in argv) > 65536:
        raise ValueError("argv exceeds byte limit")
    runtime_path = os.path.realpath(sys.executable)
    if argv[0] != runtime_path or argv[1] != "-I":
        raise ValueError("child must use the exact isolated supervisor runtime")
    runtime_hash = hashlib.sha256(_regular_bytes(runtime_path, 64 * 1024 * 1024)).hexdigest()
    source_hash = hashlib.sha256(_regular_bytes(os.path.abspath(__file__), 1024 * 1024)).hexdigest()
    if runtime_hash != _hex(execution["runtime_sha256"], 64):
        raise ValueError("runtime digest mismatch")
    if source_hash != _hex(execution["supervisor_sha256"], 64):
        raise ValueError("supervisor digest mismatch")
    timeout = execution["timeout_seconds"]
    if type(timeout) is not int or not 1 <= timeout <= 3600:
        raise ValueError("invalid timeout")
    return {
        "attempt_id": attempt, "attempt_kind": kind,
        "map": {"commit": _hex(args.map_commit, 40), "tree": _hex(args.map_tree, 40),
                "blob": blob, "sha256": expected},
        "subject": {"commit": _hex(execution["subject_commit"], 40),
                    "tree": _hex(execution["subject_tree"], 40)},
        "launch": {"argv": argv, "cwd": _directory(execution["cwd"]),
                   "environment": ENVIRONMENT.copy(), "runtime_sha256": runtime_hash,
                   "supervisor_sha256": source_hash},
        "capture_parent": _directory(args.capture_parent),
        "limits": {"timeout_seconds": timeout, "per_stream_bytes": STREAM_LIMIT,
                   "aggregate_stream_bytes": 2 * STREAM_LIMIT, "read_bytes": READ_LIMIT,
                   "term_grace_seconds": TERM_GRACE, "cleanup_seconds": CLEANUP_LIMIT,
                   "eof_grace_seconds": EOF_GRACE},
    }


def _execute(config):
    """Consume one exclusive reservation and attempt at most one child spawn."""
    parent_fd = os.open(config["capture_parent"], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    directory_fd = None
    try:
        os.mkdir(config["attempt_id"], 0o700, dir_fd=parent_fd)
        os.fsync(parent_fd)
        directory_fd = os.open(config["attempt_id"], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                               dir_fd=parent_fd)
        reserved_at = _utc()
        intent = {"format": "m01-supervisor-intent-v1", "attempt_id": config["attempt_id"],
                  "attempt_kind": config["attempt_kind"], "map": config["map"],
                  "subject": config["subject"], "launch": config["launch"],
                  "limits": config["limits"], "reserved_at": reserved_at,
                  "state": "reserved_before_spawn_attempt", "attempt_reusable": False}
        intent_raw = _serialized(intent)
        _write_record(directory_fd, "intent.json", intent_raw)
        return _capture(config, directory_fd, reserved_at, hashlib.sha256(intent_raw).hexdigest())
    finally:
        if directory_fd is not None:
            os.close(directory_fd)
        os.close(parent_fd)


def _capture(config, directory_fd, reserved_at, intent_sha256):
    process = None
    files = {}
    eof = {"stdout": False, "stderr": False}
    counts = {"stdout": 0, "stderr": 0}
    errors = []
    interventions = []
    cancelled = []
    old_handlers = {}
    selector = selectors.DefaultSelector()
    started = time.monotonic()
    pre_spawn_at = None
    status_observed_at = None
    observed_status = None
    raw_wait_status = None
    wait_ownership_lost = False
    spawn_attempted = False
    cleanup_deadline = None

    def add_error(stage, error):
        if len(errors) < 16:
            errors.append(stage + ":" + type(error).__name__)

    def intervene(reason):
        if reason not in interventions:
            interventions.append(reason)

    def cancellation(number, _frame):
        if not cancelled:
            cancelled.append(number)

    def observe():
        """Accept only this child's actual terminal kernel wait status.

        Popen.poll()/wait() may synthesize zero after ECHILD. They are therefore
        deliberately excluded from the evidence path. A missing status remains
        missing even if streams are empty or the child is no longer present.
        """
        nonlocal status_observed_at, observed_status, raw_wait_status, wait_ownership_lost
        if process is None or observed_status is not None or wait_ownership_lost:
            return observed_status
        try:
            waited_pid, status = os.waitpid(process.pid, os.WNOHANG)
            if type(waited_pid) is not int or type(status) is not int or not 0 <= status <= 65535:
                raise ValueError("invalid wait result types")
            if waited_pid == 0 and status == 0:
                return None
            if waited_pid != process.pid or not (os.WIFEXITED(status) or os.WIFSIGNALED(status)):
                raise ValueError("wait did not return this child's terminal status")
            decoded = os.waitstatus_to_exitcode(status)
        except InterruptedError:
            return None
        except (OSError, ValueError) as error:
            wait_ownership_lost = True
            add_error("waitpid", error)
            intervene("wait_status_unavailable")
            return None
        raw_wait_status = status
        observed_status = decoded
        status_observed_at = _utc()
        # Suppress Popen's later destructor reap only after a real observation.
        # Its returncode is never read back or used as execution evidence here.
        process.returncode = decoded
        return observed_status

    def send(number):
        # Do not signal a possibly recycled PGID after reaping the direct child.
        if process is not None and observed_status is None and not wait_ownership_lost:
            try:
                os.killpg(process.pid, number)
            except ProcessLookupError:
                pass
            except OSError as error:
                add_error("signal", error)

    def stop():
        """Bound cleanup; only direct wait results may establish termination."""
        nonlocal cleanup_deadline
        if process is None or observe() is not None or wait_ownership_lost:
            return
        intervene("cleanup_required")
        if cleanup_deadline is None:
            cleanup_deadline = time.monotonic() + CLEANUP_LIMIT
        send(signal.SIGTERM)
        escalation_at = min(cleanup_deadline, time.monotonic() + TERM_GRACE)
        escalated = False
        while observe() is None and not wait_ownership_lost:
            now = time.monotonic()
            if now >= escalation_at and not escalated:
                send(signal.SIGKILL)
                escalated = True
            if now >= cleanup_deadline:
                observe()
                if observed_status is None and not wait_ownership_lost:
                    intervene("termination_unobserved")
                return
            time.sleep(min(0.05, cleanup_deadline - now))

    try:
        for number in (signal.SIGINT, signal.SIGTERM):
            old_handlers[number] = signal.signal(number, cancellation)
        for name in ("stdout", "stderr"):
            files[name] = _exclusive_file(directory_fd, name)
        if cancelled:
            intervene("cancelled_before_spawn")
        else:
            pre_spawn_at = _utc()
            started = time.monotonic()
            spawn_attempted = True
            # This is the sole spawn site. Any exception consumes the reservation.
            process = subprocess.Popen(config["launch"]["argv"], cwd=config["launch"]["cwd"],
                                       env=ENVIRONMENT.copy(), stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       shell=False, close_fds=True, start_new_session=True)
            for name in ("stdout", "stderr"):
                pipe = getattr(process, name)
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            deadline = started + config["limits"]["timeout_seconds"]
            escalation_at = None
            eof_deadline = None
            while True:
                status = observe()
                if wait_ownership_lost:
                    break
                now = time.monotonic()
                if status is not None and eof_deadline is None:
                    eof_deadline = now + EOF_GRACE
                if cancelled:
                    intervene("cancelled")
                if now >= deadline:
                    intervene("timeout")
                if eof_deadline is not None and now >= eof_deadline and selector.get_map():
                    intervene("stream_eof_timeout")
                    break
                if interventions and cleanup_deadline is None:
                    cleanup_deadline = now + CLEANUP_LIMIT
                    escalation_at = now + TERM_GRACE
                    send(signal.SIGTERM)
                if escalation_at is not None and now >= escalation_at:
                    send(signal.SIGKILL)
                    escalation_at = None
                if status is not None and not selector.get_map():
                    break
                if cleanup_deadline is not None and now >= cleanup_deadline:
                    intervene("cleanup_deadline")
                    break
                for key, _events in selector.select(0.1):
                    name = key.data
                    remaining = STREAM_LIMIT - counts[name]
                    try:
                        chunk = os.read(key.fd, min(READ_LIMIT, remaining + 1))
                    except BlockingIOError:
                        continue
                    if not chunk:
                        eof[name] = True
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        continue
                    kept = chunk[:remaining]
                    if kept:
                        if files[name].write(kept) != len(kept):
                            raise OSError("short capture write")
                        counts[name] += len(kept)
                    if len(chunk) > remaining:
                        intervene("output_limit")
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
    except Exception as error:
        add_error("capture", error)
        intervene("capture_error")
    finally:
        try:
            stop()
        except OSError as error:
            add_error("cleanup", error)
        finally:
            try:
                selector.close()
            except OSError as error:
                add_error("selector_close", error)
            # Popen may have returned before pipe registration itself failed.
            if process is not None:
                for name in ("stdout", "stderr"):
                    pipe = getattr(process, name)
                    if pipe is not None:
                        try:
                            pipe.close()
                        except OSError as error:
                            add_error("pipe_close_" + name, error)
            for name, target in files.items():
                try:
                    target.flush()
                    os.fsync(target.fileno())
                except OSError as error:
                    add_error("stream_sync_" + name, error)
                finally:
                    try:
                        target.close()
                    except OSError as error:
                        add_error("stream_close_" + name, error)
            for number, handler in old_handlers.items():
                try:
                    signal.signal(number, handler)
                except (OSError, ValueError) as error:
                    add_error("signal_restore", error)

    # Hash the retained bytes, not optimistic counters or buffered write inputs.
    streams = {}
    for name in ("stdout", "stderr"):
        raw = None
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
            with os.fdopen(fd, "rb") as source:
                if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                    raise ValueError("capture is not a regular file")
                raw = _bounded_read(source, STREAM_LIMIT)
        except (OSError, ValueError) as error:
            raw = None
            add_error("stream_hash_" + name, error)
        streams[name] = {"file": name, "byte_count": None if raw is None else len(raw),
                         "sha256": None if raw is None else hashlib.sha256(raw).hexdigest(),
                         "eof": eof[name]}
    if cancelled:
        intervene("cancelled")
    status = observed_status
    complete = all(eof.values()) and not errors and not interventions and status is not None
    outcome = "indeterminate"
    if complete:
        outcome = "observed_exit_zero" if status == 0 else "observed_nonzero"
    receipt = {
        "format": "m01-supervisor-receipt-v1", "attempt_id": config["attempt_id"],
        "attempt_kind": config["attempt_kind"], "map": config["map"],
        "subject": config["subject"], "launch": config["launch"], "limits": config["limits"],
        "reservation": {"file": "intent.json", "sha256": intent_sha256},
        "timing": {"reserved_at": reserved_at, "pre_spawn_at": pre_spawn_at,
                   "status_observed_at": status_observed_at, "finished_at": _utc(),
                   "elapsed_monotonic_seconds": time.monotonic() - started},
        "process": {"spawn_attempted": spawn_attempted, "pid": None if process is None else process.pid,
                    "wait_status": raw_wait_status, "returncode": status,
                    "exit_code": status if status is not None and status >= 0 else None,
                    "signal": -status if status is not None and status < 0 else None},
        "interventions": interventions, "cancellation_signal": cancelled[0] if cancelled else None,
        "capture": {**streams, "complete": complete}, "outcome": outcome,
        "supervisor_errors": errors,
        "authority": {"attempt_reusable": False, "acceptance": False, "ready_state": False,
                      "merge": False, "m01_completion": False, "later_execution": False},
    }
    _publish_receipt(directory_fd, receipt)
    return 0 if outcome == "observed_exit_zero" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", required=True)
    parser.add_argument("--map-sha256", required=True)
    parser.add_argument("--map-commit", required=True)
    parser.add_argument("--map-tree", required=True)
    parser.add_argument("--map-blob", required=True)
    parser.add_argument("--capture-parent", required=True)
    args = parser.parse_args(argv)
    try:
        return _execute(_configuration(args))
    except Exception as error:
        # Never infer an execution result from this wrapper's own exit status.
        print("Supervisor stopped: " + type(error).__name__ +
              "; inspect retained files; no retry is authorized.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
