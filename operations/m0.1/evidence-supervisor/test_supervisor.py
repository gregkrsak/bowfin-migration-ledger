"""Proposed synthetic controls; not executed during source preparation.

Executing this file imports the draft supervisor and starts synthetic Python
children. It therefore requires its own explicit bounded-execution authority.
It never reads a production evidence package or invokes the accepted verifier.
Every real fixture installs an eight-second alarm, and the outer harness limits
each supervisor process to twenty seconds. Host-loss and durable-storage
failure still require an enclosing runner; these are not sandbox tests.
"""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "supervisor.py"
# Public linux/amd64 image and complete layer closure: runtime-pin.json.
# No PATH lookup, environment override, or fallback interpreter is permitted.
RUNTIME = Path("/usr/local/bin/python3.12")
RUNTIME_SHA256 = "4dbf3143240288fb2170257ffaa7bd030cdda5d2703d1f5f30b627042267e2e3"
STREAM_LIMIT = 1_048_576
OUTER_TIMEOUT = 20
ENV = {"LANG": "C", "LC_ALL": "C", "TZ": "UTC"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blob_identity(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def load_supervisor():
    """Import only when the separately authorized synthetic suite executes."""
    spec = importlib.util.spec_from_file_location("reviewed_supervisor", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fault_worker(kind, counter_path, arguments):
    """Isolate post-spawn fault injection behind the outer harness deadline."""
    module = load_supervisor()
    real_popen = module.subprocess.Popen
    with mock.patch.object(module.subprocess, "Popen", wraps=real_popen) as spawn:
        if kind == "publication":
            with mock.patch.object(module.os, "link", side_effect=OSError("injected link failure")):
                status = module.main(arguments)
        elif kind == "stream-write":
            original = module._exclusive_file

            class BrokenWrite:
                def __init__(self, wrapped):
                    self.wrapped = wrapped

                def write(self, _data):
                    raise OSError("injected stream write failure")

                def __getattr__(self, name):
                    return getattr(self.wrapped, name)

            def open_with_fault(directory_fd, name):
                opened = original(directory_fd, name)
                return BrokenWrite(opened) if name == "stdout" else opened

            with mock.patch.object(module, "_exclusive_file", side_effect=open_with_fault):
                status = module.main(arguments)
        elif kind == "lost-wait":
            real_waitpid = module.os.waitpid
            real_killpg = module.os.killpg
            stolen_statuses = []
            post_loss_signals = []

            def competing_reaper(pid, flags):
                # Consume a real terminal result, then hide it from the supervisor.
                # The child is already reaped; this does not create a live orphan.
                waited_pid, raw_status = real_waitpid(pid, flags)
                if waited_pid == pid:
                    stolen_statuses.append(raw_status)
                    raise ChildProcessError("synthetic competing reaper consumed status")
                return waited_pid, raw_status

            def guarded_killpg(pid, number):
                if stolen_statuses:
                    # Do not let a defective candidate signal a possibly reused PID.
                    post_loss_signals.append(number)
                    return
                return real_killpg(pid, number)

            with mock.patch.object(module.os, "waitpid", side_effect=competing_reaper):
                with mock.patch.object(module.os, "killpg", side_effect=guarded_killpg):
                    status = module.main(arguments)
            observation = {
                "stolen_status_count": len(stolen_statuses),
                "stolen_statuses": stolen_statuses,
                "post_loss_signal_count": len(post_loss_signals),
            }
            Path(counter_path).with_name("wait-loss.json").write_text(
                json.dumps(observation, sort_keys=True), encoding="ascii",
            )
        elif kind.startswith("sync:"):
            # Classify syncs by the open object and publication state, not by
            # call number. Record attempts even if the injected sync fails.
            requested = kind.removeprefix("sync:")
            real_fsync = module.os.fsync
            stages = []

            def checked_sync(fd):
                path = Path(os.readlink(f"/proc/self/fd/{fd}"))
                if path.name == "capture":
                    stage = "parent"
                elif path.name in ("intent.json", "stdout", "stderr", "receipt.tmp"):
                    stage = path.name
                elif path.is_dir() and path.name.startswith("M0.1-SYNTHETIC-"):
                    temporary = (path / "receipt.tmp").exists()
                    final = (path / "receipt.json").exists()
                    stage = ("postlink" if temporary and final else
                             "prelink" if temporary else
                             "final" if final else "intent-directory")
                else:
                    raise AssertionError(f"unexpected sync target: {path}")
                stages.append(stage)
                if stage == requested:
                    raise OSError("injected stage-specific sync failure")
                return real_fsync(fd)

            with mock.patch.object(module.os, "fsync", side_effect=checked_sync):
                status = module.main(arguments)
            Path(counter_path).with_name("sync-stages.json").write_text(
                json.dumps(stages), encoding="ascii",
            )
        elif kind.startswith("wait:"):
            # Reap the real child before returning a synthetic malformed value;
            # never signal a PID after that ownership has been lost.
            case = kind.removeprefix("wait:")
            real_waitpid = module.os.waitpid
            real_killpg = module.os.killpg
            lost = []
            unsafe_signals = []

            def malformed_wait(pid, flags):
                if not lost:
                    result = real_waitpid(pid, flags)
                    if result[0] == 0:
                        return result
                    lost.append(result[1])
                if case == "wrong-pid":
                    return (pid + 1, 0)
                if case == "nonterminal":
                    return (pid, 0x7f)
                if case == "wrong-type":
                    return (True, 0)
                if case == "shape":
                    return None
                raise AssertionError("unknown wait fixture")

            def guard_signal(pid, number):
                if lost:
                    unsafe_signals.append(number)
                    return
                return real_killpg(pid, number)

            with mock.patch.object(module.os, "waitpid", side_effect=malformed_wait):
                with mock.patch.object(module.os, "killpg", side_effect=guard_signal):
                    status = module.main(arguments)
            Path(counter_path).with_name("wait-fault.json").write_text(
                json.dumps({"reaped": lost, "unsafe_signals": unsafe_signals}),
                encoding="ascii",
            )
        else:
            raise ValueError("unknown synthetic fault")
        Path(counter_path).write_text(str(spawn.call_count), encoding="ascii")
    return status


class SupervisorControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # A different interpreter is a setup failure, never an automatic fallback.
        if Path(sys.executable).resolve() != RUNTIME.resolve():
            raise RuntimeError("synthetic suite requires the reviewed runtime path")
        if digest(RUNTIME.read_bytes()) != RUNTIME_SHA256:
            raise RuntimeError("synthetic suite runtime digest mismatch")
        cls.supervisor = load_supervisor()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="m01-supervisor-synthetic-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.parent = self.root / "capture"
        self.parent.mkdir()
        self.map_path = self.root / "map.json"
        # Fixed identities are synthetic labels, not claims about Git objects.
        self.plan = {
            "record_class": "synthetic_supervisor_control",
            "supervisor_execution": {
                "attempt_id": "M0.1-SYNTHETIC-001",
                "subject_commit": "1" * 40,
                "subject_tree": "2" * 40,
                "argv": [],
                "cwd": str(self.root),
                "runtime_sha256": RUNTIME_SHA256,
                "supervisor_sha256": digest(SOURCE.read_bytes()),
                "timeout_seconds": 4,
            },
        }

    def prepare(self, number, child="pass", timeout=4):
        """Build inert map bytes. The child has a self-contained lifetime limit."""
        execution = self.plan["supervisor_execution"]
        execution["attempt_id"] = f"M0.1-SYNTHETIC-{number:03d}"
        execution["argv"] = [
            str(RUNTIME.resolve()), "-I", "-c",
            "import signal; signal.alarm(8); " + child,
        ]
        execution["timeout_seconds"] = timeout
        return self.write_map()

    def write_map(self, raw=None):
        raw = raw if raw is not None else json.dumps(self.plan, sort_keys=True).encode("utf-8")
        self.map_path.write_bytes(raw)
        return [
            "--map", str(self.map_path),
            "--map-sha256", digest(raw),
            "--map-commit", "3" * 40,
            "--map-tree", "4" * 40,
            "--map-blob", blob_identity(raw),
            "--capture-parent", str(self.parent),
        ]

    @property
    def attempt(self):
        return self.parent / self.plan["supervisor_execution"]["attempt_id"]

    def receipt(self):
        return json.loads((self.attempt / "receipt.json").read_bytes())

    def spawn_outer(self, arguments, fault=None):
        if fault is None:
            command = [str(RUNTIME), "-I", str(SOURCE), *arguments]
        else:
            command = [
                str(RUNTIME), "-I", str(Path(__file__).resolve()),
                "--fault-worker", fault, str(self.root / "spawn-count"), *arguments,
            ]
        process = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, cwd=self.root, env=ENV,
            close_fds=True, shell=False, start_new_session=True,
        )
        self.addCleanup(self.stop_outer, process)
        return process

    @staticmethod
    def stop_outer(process):
        """Do not leave a live harness process after an assertion or timeout."""
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
        # A separately-sessioned synthetic child has its own eight-second alarm.
        # The authorized enclosing runner must additionally own orphan cleanup.

    def run_outer(self, arguments, fault=None):
        return self.spawn_outer(arguments, fault).wait(timeout=OUTER_TIMEOUT)

    def assert_capture_identity(self, record):
        raw_map = self.map_path.read_bytes()
        self.assertEqual(record["map"]["sha256"], digest(raw_map))
        self.assertEqual(record["map"]["blob"], blob_identity(raw_map))
        self.assertEqual(record["launch"]["argv"], self.plan["supervisor_execution"]["argv"])
        self.assertEqual(record["reservation"]["sha256"], digest((self.attempt / "intent.json").read_bytes()))
        for field in ("attempt_reusable", "acceptance", "ready_state", "merge", "m01_completion", "later_execution"):
            self.assertIs(record["authority"][field], False)
        for name in ("stdout", "stderr"):
            actual = (self.attempt / name).read_bytes()
            observed = record["capture"][name]
            self.assertEqual(observed["byte_count"], len(actual))
            self.assertEqual(observed["sha256"], digest(actual))
            self.assertLessEqual(len(actual), STREAM_LIMIT)

    def assert_zero_spawn(self, arguments):
        with mock.patch.object(self.supervisor.subprocess, "Popen") as spawn:
            status = self.supervisor.main(arguments)
        self.assertEqual(status, 2)
        spawn.assert_not_called()

    def test_01_silent_zero_is_directly_observed(self):
        arguments = self.prepare(1)
        self.assertEqual(self.run_outer(arguments), 0)
        record = self.receipt()
        self.assertEqual(record["attempt_kind"], "synthetic")
        self.assertEqual(record["outcome"], "observed_exit_zero")
        self.assertEqual(record["process"]["wait_status"], 0)
        self.assertEqual(record["process"]["returncode"], 0)
        self.assertTrue(record["capture"]["complete"])
        self.assertEqual(record["interventions"], [])
        self.assertEqual((self.attempt / "stdout").read_bytes(), b"")
        self.assertEqual((self.attempt / "stderr").read_bytes(), b"")
        self.assertFalse((self.attempt / "receipt.tmp").exists())
        self.assert_capture_identity(record)

    def test_02_empty_streams_do_not_hide_sigkill(self):
        arguments = self.prepare(2, "import os; os.kill(os.getpid(), signal.SIGKILL)")
        self.assertEqual(self.run_outer(arguments), 1)
        record = self.receipt()
        self.assertEqual(record["process"]["returncode"], -signal.SIGKILL)
        self.assertEqual(record["process"]["signal"], signal.SIGKILL)
        self.assertIsNone(record["process"]["exit_code"])
        self.assertTrue(os.WIFSIGNALED(record["process"]["wait_status"]))
        self.assertEqual(os.WTERMSIG(record["process"]["wait_status"]), signal.SIGKILL)
        self.assertNotEqual(record["outcome"], "observed_exit_zero")
        self.assertEqual((self.attempt / "stdout").read_bytes(), b"")
        self.assertEqual((self.attempt / "stderr").read_bytes(), b"")
        self.assert_capture_identity(record)

    def test_03_nonzero_exit_is_retained(self):
        arguments = self.prepare(3, "raise SystemExit(2)")
        self.assertEqual(self.run_outer(arguments), 1)
        record = self.receipt()
        self.assertEqual(record["outcome"], "observed_nonzero")
        self.assertEqual(record["process"]["returncode"], 2)
        self.assertEqual(record["process"]["exit_code"], 2)
        self.assertIsNone(record["process"]["signal"])
        self.assertTrue(os.WIFEXITED(record["process"]["wait_status"]))
        self.assertEqual(os.WEXITSTATUS(record["process"]["wait_status"]), 2)
        self.assert_capture_identity(record)

    def test_04_timeout_cannot_be_success(self):
        arguments = self.prepare(4, "import time; time.sleep(3)", timeout=1)
        self.assertEqual(self.run_outer(arguments), 1)
        record = self.receipt()
        self.assertEqual(record["outcome"], "indeterminate")
        self.assertIn("timeout", record["interventions"])
        self.assertIsNotNone(record["process"]["returncode"])
        self.assert_capture_identity(record)

    def test_05_exact_stream_boundary_is_not_overflow(self):
        arguments = self.prepare(5, f"import sys; sys.stdout.buffer.write(b'x' * {STREAM_LIMIT}); sys.stdout.buffer.flush()")
        self.assertEqual(self.run_outer(arguments), 0)
        record = self.receipt()
        self.assertEqual(record["outcome"], "observed_exit_zero")
        self.assertEqual(record["capture"]["stdout"]["byte_count"], STREAM_LIMIT)
        self.assertEqual((self.attempt / "stdout").read_bytes(), b"x" * STREAM_LIMIT)
        self.assertTrue(record["capture"]["complete"])
        self.assert_capture_identity(record)

    def test_06_overflow_retains_only_bounded_prefix(self):
        arguments = self.prepare(6, f"import sys; sys.stdout.buffer.write(b'x' * {STREAM_LIMIT + 1}); sys.stdout.buffer.flush()")
        self.assertEqual(self.run_outer(arguments), 1)
        record = self.receipt()
        self.assertEqual(record["outcome"], "indeterminate")
        self.assertIn("output_limit", record["interventions"])
        self.assertEqual(record["capture"]["stdout"]["byte_count"], STREAM_LIMIT)
        self.assertEqual((self.attempt / "stdout").read_bytes(), b"x" * STREAM_LIMIT)
        self.assertNotEqual(record["outcome"], "observed_exit_zero")
        self.assertFalse(record["capture"]["complete"])
        self.assert_capture_identity(record)

    def test_07_map_digest_mismatch_stops_before_spawn(self):
        arguments = self.prepare(7)
        arguments[arguments.index("--map-sha256") + 1] = "0" * 64
        self.assert_zero_spawn(arguments)
        self.assertFalse(self.attempt.exists())

    def test_08_boolean_timeout_is_not_an_integer_budget(self):
        arguments = self.prepare(8, timeout=True)
        self.assert_zero_spawn(arguments)
        self.assertFalse(self.attempt.exists())

    def test_09_duplicate_json_key_is_rejected(self):
        self.prepare(9)
        encoded = json.dumps(self.plan, sort_keys=True)
        duplicated = encoded.replace('"timeout_seconds": 4', '"timeout_seconds": 4, "timeout_seconds": 4')
        self.assertNotEqual(duplicated, encoded)
        self.assert_zero_spawn(self.write_map(duplicated.encode("utf-8")))
        self.assertFalse(self.attempt.exists())

    def test_10_existing_reservation_is_never_reused(self):
        arguments = self.prepare(10)
        self.assertEqual(self.run_outer(arguments), 0)
        before = {path.name: path.read_bytes() for path in self.attempt.iterdir()}
        self.assert_zero_spawn(arguments)
        after = {path.name: path.read_bytes() for path in self.attempt.iterdir()}
        self.assertEqual(after, before)

    def test_11_spawn_failure_consumes_the_reservation(self):
        arguments = self.prepare(11)
        with mock.patch.object(self.supervisor.subprocess, "Popen", side_effect=OSError("injected spawn failure")) as spawn:
            status = self.supervisor.main(arguments)
        self.assertEqual(status, 1)
        self.assertEqual(spawn.call_count, 1)
        record = self.receipt()
        self.assertEqual(record["outcome"], "indeterminate")
        self.assertIs(record["process"]["spawn_attempted"], True)
        self.assertIsNone(record["process"]["returncode"])
        self.assertTrue((self.attempt / "intent.json").is_file())
        self.assert_zero_spawn(arguments)

    def test_12_reservation_sync_failure_does_not_launch(self):
        arguments = self.prepare(12)
        with mock.patch.object(self.supervisor.os, "fsync", side_effect=OSError("injected sync failure")):
            self.assert_zero_spawn(arguments)
        self.assertTrue(self.attempt.exists())
        self.assertFalse((self.attempt / "receipt.json").exists())
        self.assert_zero_spawn(arguments)

    def test_13_publication_failure_is_not_success(self):
        arguments = self.prepare(13)
        self.assertEqual(self.run_outer(arguments, fault="publication"), 2)
        self.assertEqual((self.root / "spawn-count").read_text(encoding="ascii"), "1")
        self.assertFalse((self.attempt / "receipt.json").exists())
        self.assertTrue((self.attempt / "receipt.tmp").exists())
        self.assert_zero_spawn(arguments)

    def test_14_cancellation_remains_distinct_from_child_status(self):
        marker = self.root / "child-started"
        child = f"from pathlib import Path; Path({str(marker)!r}).write_text('started'); import time; time.sleep(3)"
        arguments = self.prepare(14, child)
        process = self.spawn_outer(arguments)
        deadline = time.monotonic() + 5
        while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(marker.exists(), "synthetic child never reached its start marker")
        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(timeout=OUTER_TIMEOUT), 1)
        record = self.receipt()
        self.assertEqual(record["outcome"], "indeterminate")
        self.assertIn("cancelled", record["interventions"])
        self.assertEqual(record["cancellation_signal"], signal.SIGTERM)
        self.assertIs(record["process"]["spawn_attempted"], True)
        self.assertIsNotNone(record["process"]["returncode"])
        self.assert_capture_identity(record)


    def test_15_stream_write_error_cannot_publish_success(self):
        arguments = self.prepare(15, "print('synthetic output')")
        self.assertEqual(self.run_outer(arguments, fault="stream-write"), 1)
        self.assertEqual((self.root / "spawn-count").read_text(encoding="ascii"), "1")
        record = self.receipt()
        self.assertEqual(record["outcome"], "indeterminate")
        self.assertIn("capture:OSError", record["supervisor_errors"])
        self.assertFalse(record["capture"]["complete"])
        self.assert_capture_identity(record)

    def test_16_supervisor_digest_mismatch_stops_before_spawn(self):
        self.prepare(16)
        self.plan["supervisor_execution"]["supervisor_sha256"] = "0" * 64
        self.assert_zero_spawn(self.write_map())
        self.assertFalse(self.attempt.exists())

    def test_17_nonfinite_number_is_rejected(self):
        self.prepare(17)
        encoded = json.dumps(self.plan, sort_keys=True)
        corrupted = encoded.replace('"timeout_seconds": 4', '"timeout_seconds": 1e999')
        self.assertNotEqual(corrupted, encoded)
        self.assert_zero_spawn(self.write_map(corrupted.encode("utf-8")))
        self.assertFalse(self.attempt.exists())


    def test_18_unavailable_raw_wait_status_cannot_become_zero(self):
        arguments = self.prepare(18, "raise SystemExit(2)")
        self.assertEqual(self.run_outer(arguments, fault="lost-wait"), 1)
        self.assertEqual((self.root / "spawn-count").read_text(encoding="ascii"), "1")
        observation = json.loads((self.root / "wait-loss.json").read_bytes())
        self.assertEqual(observation["stolen_status_count"], 1)
        self.assertTrue(os.WIFEXITED(observation["stolen_statuses"][0]))
        self.assertEqual(os.WEXITSTATUS(observation["stolen_statuses"][0]), 2)
        self.assertEqual(observation["post_loss_signal_count"], 0)
        record = self.receipt()
        self.assertEqual(record["outcome"], "indeterminate")
        self.assertIn("wait_status_unavailable", record["interventions"])
        self.assertIn("waitpid:ChildProcessError", record["supervisor_errors"])
        self.assertIs(record["process"]["spawn_attempted"], True)
        for field in ("wait_status", "returncode", "exit_code", "signal"):
            self.assertIsNone(record["process"][field])
        self.assertFalse(record["capture"]["complete"])
        self.assert_capture_identity(record)

    def test_19_nondefault_sigchld_stops_before_reservation(self):
        arguments = self.prepare(19)
        prior = signal.getsignal(signal.SIGCHLD)
        self.assertEqual(prior, signal.SIG_DFL)
        try:
            signal.signal(signal.SIGCHLD, signal.SIG_IGN)
            self.assert_zero_spawn(arguments)
        finally:
            signal.signal(signal.SIGCHLD, prior)
        self.assertFalse(self.attempt.exists())

    def test_20_both_streams_retain_exact_distinct_bytes(self):
        child = ("import os; "
                 "[(os.write(1, b'out-' * 1024), os.write(2, b'ERR!' * 1024)) "
                 "for _ in range(32)]")
        arguments = self.prepare(20, child)
        self.assertEqual(self.run_outer(arguments), 0)
        record = self.receipt()
        self.assertEqual((self.attempt / "stdout").read_bytes(), b"out-" * 32768)
        self.assertEqual((self.attempt / "stderr").read_bytes(), b"ERR!" * 32768)
        self.assertTrue(record["capture"]["complete"])
        self.assert_capture_identity(record)

    def test_21_sync_sequence_normal_and_selective_failures(self):
        # Each case uses a distinct reservation. These assertions examine
        # control flow, not physical persistence across power or host loss.
        stages = ["parent", "intent.json", "intent-directory", "stdout", "stderr",
                  "receipt.tmp", "prelink", "postlink", "final"]
        for number, failed in enumerate(["none", *stages], start=21):
            with self.subTest(failed=failed):
                arguments = self.prepare(number, "print('known output')")
                status = self.run_outer(arguments, fault="sync:" + failed)
                events = json.loads((self.root / "sync-stages.json").read_text(encoding="ascii"))
                spawns = int((self.root / "spawn-count").read_text(encoding="ascii"))
                self.assertEqual(events.count(failed), 0 if failed == "none" else 1)
                self.assertTrue(self.attempt.is_dir())
                if failed == "none":
                    self.assertEqual(status, 0)
                    self.assertEqual(spawns, 1)
                    self.assertEqual(events, stages)
                    self.assertEqual((self.attempt / "stdout").read_bytes(), b"known output\n")
                    self.assertEqual(self.receipt()["outcome"], "observed_exit_zero")
                elif failed in stages[:3]:
                    self.assertEqual(status, 2)
                    self.assertEqual(spawns, 0)
                    self.assertEqual((self.attempt / "intent.json").exists(), failed != "parent")
                    self.assertFalse((self.attempt / "stdout").exists())
                    self.assertFalse((self.attempt / "receipt.json").exists())
                elif failed in ("stdout", "stderr"):
                    self.assertEqual(status, 1)
                    self.assertEqual(spawns, 1)
                    self.assertEqual(self.receipt()["outcome"], "indeterminate")
                    self.assertIn("stream_sync_" + failed + ":OSError", self.receipt()["supervisor_errors"])
                    self.assertFalse(self.receipt()["capture"]["complete"])
                else:
                    self.assertEqual(status, 2)
                    self.assertEqual(spawns, 1)
                    self.assertEqual((self.attempt / "receipt.json").exists(), failed in ("postlink", "final"))
                    self.assertEqual((self.attempt / "receipt.tmp").exists(), failed != "final")
                    # A visible receipt on publication failure cannot prove
                    # the enclosing publication or final synchronization.
                if failed != "parent":
                    self.assertTrue((self.attempt / "intent.json").is_file())
                if spawns:
                    self.assertTrue((self.attempt / "stdout").is_file())
                    self.assertTrue((self.attempt / "stderr").is_file())
                self.assert_zero_spawn(arguments)

    def test_22_malformed_wait_results_never_become_success(self):
        for number, case in enumerate(("wrong-pid", "nonterminal", "wrong-type", "shape"), start=31):
            with self.subTest(case=case):
                arguments = self.prepare(number, "raise SystemExit(2)")
                status = self.run_outer(arguments, fault="wait:" + case)
                self.assertEqual((self.root / "spawn-count").read_text(encoding="ascii"), "1")
                observation = json.loads((self.root / "wait-fault.json").read_text(encoding="ascii"))
                self.assertEqual(len(observation["reaped"]), 1)
                self.assertTrue(os.WIFEXITED(observation["reaped"][0]))
                self.assertEqual(os.WEXITSTATUS(observation["reaped"][0]), 2)
                self.assertEqual(observation["unsafe_signals"], [])
                receipt_path = self.attempt / "receipt.json"
                if case == "shape":
                    # The current implementation can propagate TypeError from
                    # cleanup; that is an adverse wrapper result, not a receipt.
                    self.assertEqual(status, 2)
                    self.assertFalse(receipt_path.exists())
                else:
                    self.assertEqual(status, 1)
                    self.assertTrue(receipt_path.is_file())
                    record = self.receipt()
                    self.assertEqual(record["outcome"], "indeterminate")
                    self.assertIn("wait_status_unavailable", record["interventions"])
                    self.assertIn("waitpid:ValueError", record["supervisor_errors"])
                    self.assertFalse(record["capture"]["complete"])
                    for field in ("wait_status", "returncode", "exit_code", "signal"):
                        self.assertIsNone(record["process"][field])
                self.assert_zero_spawn(arguments)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fault-worker":
        raise SystemExit(fault_worker(sys.argv[2], sys.argv[3], sys.argv[4:]))
    unittest.main()
