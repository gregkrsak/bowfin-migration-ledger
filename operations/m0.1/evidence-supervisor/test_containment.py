"""Authored operational regression controls; NOT executed during preparation.

Future execution imports the exact sibling controller and requires separate
owner authority. All systemd/Docker boundaries are mocked; these controls do
not qualify a host or replace the unchanged 22 supervisor controls.
"""

import ast
from contextlib import ExitStack, nullcontext
import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
TIMER = "bowfinpr18-deadline.timer"
SERVICE = "bowfinpr18-deadline.service"
DEADLINE = 5_000_000


def load_controller():
    spec = importlib.util.spec_from_file_location(
        "reviewed_containment_controller", HERE / "containment/controller.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContainmentControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = load_controller()

    def test_finite_json_numbers(self):
        for token, expected in ((b"1.25", 1.25), (b"-1e2", -100.0),
                                (b"0.0", 0.0), (b"1e-999", 0.0)):
            with self.subTest(token=token):
                self.assertEqual(self.controller.decode(token), expected)

    def test_exponent_overflow_rejected(self):
        for token in (b"1e999", b"-1e999", b'{"nested":[1e999]}'):
            with self.subTest(token=token):
                with self.assertRaises(ValueError):
                    self.controller.decode(token)

    def test_nonfinite_literals_rejected(self):
        for token in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(token=token):
                with self.assertRaises(ValueError):
                    self.controller.decode(token)

    def test_float_token_bound(self):
        limit = b"1." + b"0" * 126
        self.assertEqual(len(limit), 128)
        self.assertEqual(self.controller.decode(limit), 1.0)
        with self.assertRaises(ValueError):
            self.controller.decode(limit + b"0")

    def test_duplicate_keys_rejected(self):
        with self.assertRaises(ValueError):
            self.controller.decode(b'{"same":1,"same":2}')

    def watchdog_fixture(self, *, overrides=None, fail_stop=None,
                         retain_active=None, marker=False, clocks=None):
        """Model only manager properties; no subprocess or real unit access."""
        module = self.controller
        properties = {
            (TIMER, "Unit", "ActiveState"): ["s", "active"],
            (SERVICE, "Unit", "ActiveState"): ["s", "inactive"],
            (TIMER, "Unit", "Job"): ["(uo)", "0", "/"],
            (SERVICE, "Unit", "Job"): ["(uo)", "0", "/"],
            (SERVICE, "Unit", "SubState"): ["s", "dead"],
            (SERVICE, "Unit", "InactiveExitTimestampMonotonic"): ["t", "0"],
            (SERVICE, "Service", "ExecMainStartTimestampMonotonic"): ["t", "0"],
            (TIMER, "Timer", "LastTriggerUSecMonotonic"): ["t", "0"],
            (TIMER, "Timer", "NextElapseUSecMonotonic"): ["t", str(DEADLINE)],
        }
        properties.update(overrides or {})
        calls = []

        def checked(argv, timeout=10):
            self.assertEqual(argv[:2], ["/usr/bin/systemctl", "stop"])
            calls.append(argv[2])
            if argv[2] == fail_stop:
                raise RuntimeError("injected stop failure")
            if argv[2] != retain_active:
                properties[(argv[2], "Unit", "ActiveState")] = ["s", "inactive"]
            return b""

        stack = ExitStack()
        stack.enter_context(mock.patch.object(module, "checked", side_effect=checked))
        stack.enter_context(mock.patch.object(module, "bus_property",
                                             side_effect=lambda *key: properties[key]))
        stack.enter_context(mock.patch.object(Path, "exists", return_value=marker))
        if clocks is None:
            stack.enter_context(mock.patch.object(module.time, "monotonic_ns",
                                                 return_value=1_000_000_000))
        else:
            stack.enter_context(mock.patch.object(module.time, "monotonic_ns",
                                                 side_effect=clocks))
        self.addCleanup(stack.close)
        return calls

    def test_successful_stop_order_and_quiescent_readback(self):
        calls = self.watchdog_fixture()
        observed = self.controller.quiesce_watchdog(DEADLINE)
        self.assertEqual(calls, [TIMER, SERVICE])
        self.assertEqual(observed["earliest_deadline_usec"], DEADLINE)
        self.assertLess(observed["before_disarm_usec"], DEADLINE)
        self.assertLess(observed["timer_stopped_usec"], DEADLINE)
        self.assertLess(observed["reconciled_usec"], DEADLINE)
        for unit in (TIMER, SERVICE):
            self.assertEqual(observed["units"][unit]["active_state"], ["s", "inactive"])
            self.assertEqual(observed["units"][unit]["job"], ["(uo)", "0", "/"])

    def test_missing_or_boolean_deadline_rejected(self):
        for deadline in (None, True, 0, -1):
            with self.subTest(deadline=deadline):
                with self.assertRaises(ValueError):
                    self.controller.quiesce_watchdog(deadline)

    def test_queued_trigger_without_marker_is_adverse(self):
        calls = self.watchdog_fixture(overrides={
            (TIMER, "Timer", "LastTriggerUSecMonotonic"): ["t", "100"]})
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)
        self.assertEqual(calls, [])

    def test_elapsed_deadline_rejected_even_when_history_zero(self):
        calls = self.watchdog_fixture(clocks=[DEADLINE * 1000])
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)
        self.assertEqual(calls, [])

    def test_timer_stop_failure_does_not_stop_service(self):
        calls = self.watchdog_fixture(fail_stop=TIMER)
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)
        self.assertEqual(calls, [TIMER])

    def test_service_stop_failure_rejects(self):
        calls = self.watchdog_fixture(fail_stop=SERVICE)
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)
        self.assertEqual(calls, [TIMER, SERVICE])

    def test_timer_still_active_rejects(self):
        self.watchdog_fixture(retain_active=TIMER)
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)

    def test_service_still_active_rejects(self):
        self.watchdog_fixture(overrides={
            (SERVICE, "Unit", "ActiveState"): ["s", "active"]},
            retain_active=SERVICE)
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)

    def test_pending_manager_job_rejects(self):
        for unit in (TIMER, SERVICE):
            with self.subTest(unit=unit):
                # Each fixture is immediately restored before the next subcase.
                self.watchdog_fixture(overrides={
                    (unit, "Unit", "Job"): ["(uo)", "7", "/job/7"]})
                try:
                    with self.assertRaises(RuntimeError):
                        self.controller.quiesce_watchdog(DEADLINE)
                finally:
                    self.doCleanups()

    def test_started_service_history_rejects(self):
        self.watchdog_fixture(overrides={
            (SERVICE, "Service", "ExecMainStartTimestampMonotonic"): ["t", "10"]})
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)

    def test_inactive_exit_history_rejects(self):
        self.watchdog_fixture(overrides={
            (SERVICE, "Unit", "InactiveExitTimestampMonotonic"): ["t", "10"]})
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)

    def test_changed_armed_expiry_rejects(self):
        self.watchdog_fixture(overrides={
            (TIMER, "Timer", "NextElapseUSecMonotonic"): ["t", str(DEADLINE + 1)]})
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)

    def test_adverse_marker_rejects(self):
        self.watchdog_fixture(marker=True)
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)

    def test_clock_crosses_deadline_during_disarm(self):
        calls = self.watchdog_fixture(clocks=[1_000_000_000, DEADLINE * 1000])
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)
        self.assertEqual(calls, [TIMER])

    def test_clock_crosses_deadline_after_manager_readbacks(self):
        calls = self.watchdog_fixture(clocks=[1_000_000_000, 1_000_000_000,
                                              DEADLINE * 1000])
        with self.assertRaises(RuntimeError):
            self.controller.quiesce_watchdog(DEADLINE)
        self.assertEqual(calls, [TIMER, SERVICE])

    def deadline_fixture(self, *, fail_lock=False, fail_marker=False):
        module = self.controller
        intent = {"plan_sha256": "a" * 64}
        records = {}
        stack = ExitStack()

        def record(name, value):
            if fail_marker and name == "deadline-fired.json":
                raise OSError("injected marker write failure")
            self.assertNotIn(name, records)
            records[name] = value

        stack.enter_context(mock.patch.object(module, "trusted",
            return_value=json.dumps(intent).encode("ascii")))
        stack.enter_context(mock.patch.object(module, "record", side_effect=record))
        stack.enter_context(mock.patch.object(module, "terminal_lock",
            side_effect=RuntimeError("injected terminal lock failure") if fail_lock else nullcontext))
        stack.enter_context(mock.patch.object(Path, "exists", return_value=False))
        cleanup = stack.enter_context(mock.patch.object(module, "cleanup",
                                                      return_value={"complete": True}))
        self.addCleanup(stack.close)
        return intent, records, cleanup

    def test_deadline_cleanup_survives_terminal_lock_failure(self):
        intent, records, cleanup = self.deadline_fixture(fail_lock=True)
        self.assertEqual(self.controller.deadline_mode(), 1)
        self.assertIn("deadline-fired.json", records)
        self.assertNotIn("terminal.json", records)
        cleanup.assert_called_once()
        self.assertEqual(cleanup.call_args.args[:2], (intent, "deadline"))
        self.assertIn("injected terminal lock failure", cleanup.call_args.args[2])

    def test_deadline_cleanup_survives_marker_write_failure(self):
        intent, records, cleanup = self.deadline_fixture(fail_marker=True)
        self.assertEqual(self.controller.deadline_mode(), 1)
        self.assertEqual(records, {})
        cleanup.assert_called_once()
        self.assertEqual(cleanup.call_args.args[:2], (intent, "deadline"))
        self.assertIn("injected marker write failure", cleanup.call_args.args[2])

    def test_deadline_records_adverse_terminal_and_attempts_cleanup(self):
        intent, records, cleanup = self.deadline_fixture()
        self.assertEqual(self.controller.deadline_mode(), 1)
        self.assertEqual(list(records), ["deadline-fired.json", "terminal.json"])
        self.assertEqual(records["deadline-fired.json"]["reason"], "independent_systemd_deadline")
        terminal = records["terminal.json"]
        self.assertEqual(terminal["origin"], "deadline")
        self.assertEqual(terminal["classification"], "indeterminate")
        self.assertEqual(terminal["plan_sha256"], intent["plan_sha256"])
        self.assertFalse(terminal["accepted"])
        self.assertFalse(terminal["retry_authorized"])
        self.assertFalse(terminal["merge_authorized"])
        cleanup.assert_called_once_with(intent, "deadline", None)

    def finish_fixture(self, *, terminal_exists=False, fail_quiesce=False):
        module = self.controller
        records = {"terminal.json": {"origin": "deadline"}} if terminal_exists else {}
        stack = ExitStack()

        def record(name, value):
            self.assertNotIn(name, records, "terminal records must be no-replace")
            records[name] = value

        def trusted(path, maximum):
            return (json.dumps(records[path.name], sort_keys=True) + "\n").encode("ascii")

        stack.enter_context(mock.patch.object(module, "record", side_effect=record))
        stack.enter_context(mock.patch.object(module, "trusted", side_effect=trusted))
        stack.enter_context(mock.patch.object(module, "terminal_lock", side_effect=nullcontext))
        stack.enter_context(mock.patch.object(Path, "exists",
                                             side_effect=lambda: terminal_exists))
        quiesce = stack.enter_context(mock.patch.object(module, "quiesce_watchdog",
            side_effect=RuntimeError("injected reconciliation failure") if fail_quiesce else None,
            return_value={"reconciled_usec": 1_000_000}))
        self.addCleanup(stack.close)
        return records, quiesce

    def test_result_remains_provisional_with_separate_bound_terminal(self):
        records, quiesce = self.finish_fixture()
        output = {"classification": "docker_reported_suite_exit_zero_pending_independent_review",
                  "cleanup_complete": True}
        self.assertTrue(self.controller.finish(output, True, DEADLINE,
                                              {"plan_sha256": "a" * 64}))
        self.assertTrue(records["result.json"]["provisional"])
        self.assertEqual(records["result.json"]["classification"], "provisional")
        self.assertEqual(records["result.json"]["candidate_classification"], output["classification"])
        terminal = records["terminal.json"]
        self.assertEqual(terminal["classification"], "watchdog_quiescent_pending_independent_review")
        self.assertEqual(terminal["plan_sha256"], "a" * 64)
        raw = (json.dumps(records["result.json"], sort_keys=True) + "\n").encode("ascii")
        self.assertEqual(terminal["result_sha256"], self.controller.sha(raw))
        self.assertFalse(terminal["accepted"])
        self.assertFalse(terminal["retry_authorized"])
        self.assertFalse(terminal["merge_authorized"])
        quiesce.assert_called_once_with(DEADLINE)

    def test_existing_deadline_terminal_wins(self):
        records, quiesce = self.finish_fixture(terminal_exists=True)
        self.assertFalse(self.controller.finish({"classification": "favorable", "cleanup_complete": True},
                                               True, DEADLINE, {"plan_sha256": "a" * 64}))
        self.assertEqual(records["terminal.json"], {"origin": "deadline"})
        self.assertEqual(records["result.json"]["classification"], "provisional")
        quiesce.assert_not_called()

    def test_quiescence_failure_cannot_seal_positive(self):
        records, _ = self.finish_fixture(fail_quiesce=True)
        self.assertFalse(self.controller.finish({"classification": "favorable", "cleanup_complete": True},
                                               True, DEADLINE, {"plan_sha256": "a" * 64}))
        self.assertEqual(records["terminal.json"]["classification"], "indeterminate")
        self.assertIn("error", records["terminal.json"])

    def test_unarmed_or_unproven_cleanup_never_seals_positive(self):
        for armed, cleaned in ((False, True), (True, False)):
            with self.subTest(armed=armed, cleaned=cleaned):
                records, quiesce = self.finish_fixture()
                try:
                    self.assertFalse(self.controller.finish({"classification": "favorable", "cleanup_complete": cleaned},
                                                           armed, DEADLINE, {"plan_sha256": "a" * 64}))
                    self.assertEqual(records["terminal.json"]["classification"], "indeterminate")
                    quiesce.assert_not_called()
                finally:
                    self.doCleanups()

    def test_indeterminate_candidate_does_not_become_positive(self):
        records, _ = self.finish_fixture()
        self.assertFalse(self.controller.finish({"classification": "indeterminate", "cleanup_complete": True},
                                               True, DEADLINE, {"plan_sha256": "a" * 64}))
        self.assertEqual(records["terminal.json"]["classification"], "indeterminate")

    def test_docker_stdin_flags_are_strictly_required(self):
        module = self.controller
        for name in ("AttachStdin", "StdinOnce"):
            for value in (False, None, 1):
                with self.subTest(name=name, value=value):
                    command = module.create_argv("qualify", "a" * 64)
                    config = {"Image": module.IMAGE, "User": "65532:65532",
                              "Entrypoint": ["/usr/bin/env"],
                              "Cmd": command[command.index(module.IMAGE) + 1:],
                              "Tty": False, "OpenStdin": True,
                              "AttachStdin": True, "StdinOnce": True}
                    config[name] = value
                    with self.assertRaises(ValueError):
                        module.check_container({"Image": module.IMAGE_CONFIG,
                                                "Config": config, "HostConfig": {}}, "qualify")

    def test_harmless_qualification_uses_gate_without_suite_argument(self):
        for mode in ("qualify", "qualify-watchdog"):
            with self.subTest(mode=mode):
                argv = self.controller.create_argv(mode, "a" * 64)
                self.assertEqual(argv[-1], "/reviewed/containment/probe.py")
                self.assertNotIn("--suite-gate", argv)
                self.assertNotIn("/reviewed/test_supervisor.py", argv)
        tree = ast.parse((HERE / "containment/probe.py").read_text(encoding="utf-8"))
        executable_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Attribute) and node.func.attr == "execve"]
        self.assertEqual(len(executable_calls), 1)
        branches = [node for node in ast.walk(tree) if isinstance(node, ast.If)
                    and executable_calls[0] in list(ast.walk(node))]
        self.assertTrue(any("--suite-gate" in ast.unparse(node.test) for node in branches))


if __name__ == "__main__":
    unittest.main()
