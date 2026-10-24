#!/usr/bin/env python3
"""Synthetic, non-production tests for the proposed M0.1 v2 protocol.

Do not execute before exact-revision independent review and owner authorization.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_module(name: str, filename: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lib = load_module("_test_protocol_lib", "protocol_lib.py")
generate = load_module("_test_generate", "generate.py")
audit_scan = load_module("_test_audit", "audit_scan.py")
verify = load_module("_test_verify", "verify.py")


class ProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="m01v2-test-")
        self.workspace = Path(self.temporary.name)
        self.limits = lib.load_limits(ROOT / "limits.json")
        self.fixture = json.loads((FIXTURES / "valid-case.json").read_text(encoding="utf-8"))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_code(self, expected: str, callable_: Any, *args: Any, **kwargs: Any) -> None:
        with self.assertRaises(Exception) as caught:
            callable_(*args, **kwargs)
        self.assertEqual(expected, getattr(caught.exception, "code", None), str(caught.exception))

    def write_json(self, path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(lib.canonical_json_bytes(value, self.limits))

    def build_valid(self, name: str = "case") -> dict[str, Any]:
        root = self.workspace / name
        source = root / "source"
        source.mkdir(parents=True)
        for relative, text in self.fixture["source_files"].items():
            destination = source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(text, encoding="utf-8", newline="")
        mappings_path = root / "mappings.json"
        rules_path = root / "rules.json"
        audit_policy_path = root / "audit-policy.json"
        external_path = root / "external-surfaces.json"
        self.write_json(mappings_path, self.fixture["mappings"])
        self.write_json(rules_path, self.fixture["rules"])
        self.write_json(audit_policy_path, self.fixture["audit_policy"])
        self.write_json(external_path, self.fixture["external_surfaces"])

        mappings = generate.validate_mappings(lib.strict_json_file(mappings_path, self.limits), self.limits)
        rules = generate.validate_rules(lib.strict_json_file(rules_path, self.limits), mappings, self.limits)
        files = lib.snapshot_files(source, self.limits)
        manifest = lib.scan_manifest(files, self.limits)
        candidates = generate.discover(
            files,
            mappings,
            self.fixture["source_repository"],
            self.fixture["source_tree"],
            self.limits,
        )
        rows = generate.classify(candidates, mappings, rules)
        package = root / "generated"
        lib.write_package(rows, manifest, package, self.limits)

        families = audit_scan.validate_policy(lib.strict_json_file(audit_policy_path, self.limits), self.limits)
        audit_rows = audit_scan.discover(
            files,
            families,
            self.fixture["source_repository"],
            self.fixture["source_tree"],
            self.limits,
        )
        audit_path = root / "audit.json"
        audit_result = {
            "protocol_version": lib.PROTOCOL_VERSION,
            "source_repository": self.fixture["source_repository"],
            "source_tree": self.fixture["source_tree"],
            "scan_manifest_sha256": lib.scan_manifest_digest(manifest, self.limits),
            "scan_manifest": manifest,
            "candidate_count": len(audit_rows),
            "candidates": audit_rows,
        }
        self.write_json(audit_path, audit_result)
        return {
            "root": root,
            "source": source,
            "package": package,
            "audit": audit_path,
            "external": external_path,
            "rows": rows,
            "mappings": mappings,
            "rules": rules,
        }

    def verify_valid(self, built: dict[str, Any]) -> list[dict[str, Any]]:
        rows = verify.verify_package(
            built["package"],
            self.fixture["source_repository"],
            self.fixture["source_tree"],
            self.limits,
        )
        index = verify.canonical_document(built["package"] / "index.json", self.limits)
        verify.reconcile(
            rows, built["audit"], self.limits, index["scan_manifest_sha256"],
            self.fixture["source_repository"], self.fixture["source_tree"],
        )
        return rows

    def test_precomputed_canonical_and_aggregate_vectors(self) -> None:
        vectors = json.loads((FIXTURES / "vectors.json").read_text(encoding="utf-8"))
        canonical = lib.canonical_json_bytes(vectors["canonical_json"]["value"], self.limits)
        self.assertEqual(vectors["canonical_json"]["expected_utf8_hex"], canonical.hex())
        self.assertEqual(
            vectors["aggregate"]["expected_sha256"],
            lib.aggregate_digest(vectors["aggregate"]["descriptors"]),
        )

    def test_valid_generation_audit_and_verification(self) -> None:
        built = self.build_valid()
        rows = self.verify_valid(built)
        self.assertEqual(
            self.fixture["expected_occurrence_keys"],
            sorted(row["occurrence_key"] for row in rows),
        )

    def test_repeated_generation_is_byte_identical(self) -> None:
        first = self.build_valid("first")
        second = self.build_valid("second")
        first_files = {
            item.relative_to(first["package"]).as_posix(): item.read_bytes()
            for item in first["package"].rglob("*") if item.is_file()
        }
        second_files = {
            item.relative_to(second["package"]).as_posix(): item.read_bytes()
            for item in second["package"].rglob("*") if item.is_file()
        }
        self.assertEqual(first_files, second_files)

    def test_duplicate_key_and_non_nfc_reject(self) -> None:
        self.assert_code(
            "E_JSON_DUPLICATE_KEY",
            lib.strict_json_bytes,
            b'{"a":1,"a":2}\n',
            self.limits,
            "duplicate",
        )
        data = json.dumps({"value": "e\u0301"}, ensure_ascii=False).encode("utf-8")
        self.assert_code("E_JSON_NFC", lib.strict_json_bytes, data, self.limits, "non-nfc")

    def test_mapping_and_rule_mutations_reject(self) -> None:
        mappings_doc = copy.deepcopy(self.fixture["mappings"])
        mappings_doc["mappings"].append(
            {
                "canonical": "Bowfin",
                "mapping_id": "map-brand-two",
                "namespace": "display_brand",
                "original": "KLYXR",
                "policy": "replace",
            }
        )
        self.assert_code("E_MAPPING_INJECTIVE", generate.validate_mappings, mappings_doc, self.limits)

        valid_mappings = generate.validate_mappings(self.fixture["mappings"], self.limits)
        rules_doc = copy.deepcopy(self.fixture["rules"])
        rules_doc["rules"][0]["selector"]["unit_kind"] = "unknown"
        self.assert_code("E_SELECTOR_UNIT", generate.validate_rules, rules_doc, valid_mappings, self.limits)

    def test_stale_rule_count_rejects(self) -> None:
        built = self.build_valid()
        rules = copy.deepcopy(built["rules"])
        rules[0]["expected_count"] += 1
        candidates = generate.discover(
            lib.snapshot_files(built["source"], self.limits),
            built["mappings"],
            self.fixture["source_repository"],
            self.fixture["source_tree"],
            self.limits,
        )
        self.assert_code("E_EXPECTED_COUNT", generate.classify, candidates, built["mappings"], rules)

    def test_equal_count_different_key_rejects(self) -> None:
        built = self.build_valid()
        audit = lib.strict_json_file(built["audit"], self.limits)
        audit["candidates"][0]["locator"]["match_index"] += 1
        candidate = audit["candidates"][0]
        candidate["occurrence_key"] = lib.occurrence_key(
            audit["source_repository"], audit["source_tree"], candidate["path"],
            candidate["unit_kind"], candidate["locator"], candidate["namespace"],
            candidate["original"], self.limits,
        )
        self.write_json(built["audit"], audit)
        rows = verify.verify_package(
            built["package"], self.fixture["source_repository"], self.fixture["source_tree"], self.limits
        )
        self.assert_code("E_KEY_SET_MISMATCH", verify.reconcile, rows, built["audit"], self.limits)

    def test_generator_and_auditor_must_scan_same_manifest(self) -> None:
        built = self.build_valid("manifest-mismatch")
        audit = lib.strict_json_file(built["audit"], self.limits)
        audit["scan_manifest"][0]["byte_count"] += 1
        audit["scan_manifest_sha256"] = lib.scan_manifest_digest(audit["scan_manifest"], self.limits)
        self.write_json(built["audit"], audit)
        rows = verify.verify_package(
            built["package"], self.fixture["source_repository"], self.fixture["source_tree"], self.limits
        )
        index = verify.canonical_document(built["package"] / "index.json", self.limits)
        self.assert_code(
            "E_AUDIT_MANIFEST", verify.reconcile, rows, built["audit"], self.limits,
            index["scan_manifest_sha256"],
        )

    def test_missing_and_extra_chunk_reject(self) -> None:
        missing = self.build_valid("missing")
        next((missing["package"] / "occurrences").iterdir()).unlink()
        self.assert_code(
            "E_CHUNK_SET", verify.verify_package, missing["package"],
            self.fixture["source_repository"], self.fixture["source_tree"], self.limits,
        )
        extra = self.build_valid("extra")
        (extra["package"] / "occurrences" / "9999.jsonl").write_bytes(b"{}\n")
        self.assert_code(
            "E_CHUNK_SET", verify.verify_package, extra["package"],
            self.fixture["source_repository"], self.fixture["source_tree"], self.limits,
        )

    def test_tampered_and_reordered_chunk_reject(self) -> None:
        tampered = self.build_valid("tampered")
        chunk = next((tampered["package"] / "occurrences").iterdir())
        rows = [json.loads(line) for line in chunk.read_text(encoding="utf-8").splitlines()]
        rows[0]["context"] += " altered"
        chunk.write_bytes(b"".join(lib.canonical_json_bytes(row, self.limits) for row in rows))
        self.assert_code(
            "E_CHUNK_DESCRIPTOR", verify.verify_package, tampered["package"],
            self.fixture["source_repository"], self.fixture["source_tree"], self.limits,
        )

        reordered = self.build_valid("reordered")
        chunk = next((reordered["package"] / "occurrences").iterdir())
        lines = chunk.read_bytes().splitlines(keepends=True)
        chunk.write_bytes(b"".join(reversed(lines)))
        self.assert_code(
            "E_ROW_ORDER", verify.verify_package, reordered["package"],
            self.fixture["source_repository"], self.fixture["source_tree"], self.limits,
        )

    def test_oversized_row_rejects(self) -> None:
        built = self.build_valid("oversized")
        chunk = next((built["package"] / "occurrences").iterdir())
        chunk.write_bytes(b"{" + b" " * self.limits["max_row_bytes"] + b"}\n")
        self.assert_code(
            "E_ROW_SIZE", verify.verify_package, built["package"],
            self.fixture["source_repository"], self.fixture["source_tree"], self.limits,
        )

    @unittest.skipUnless(hasattr(Path, "symlink_to"), "symlinks unavailable")
    def test_symlink_and_archive_paths_reject(self) -> None:
        root = self.workspace / "symlink-root"
        root.mkdir()
        target = self.workspace / "target.txt"
        target.write_text("Klyxr\n", encoding="utf-8")
        (root / "link.txt").symlink_to(target)
        self.assert_code("E_SYMLINK", lib.snapshot_files, root, self.limits)

        archive = self.workspace / "archive-root"
        (archive / "archive" / "unaccepted").mkdir(parents=True)
        (archive / "archive" / "unaccepted" / "payload.txt").write_text("inert", encoding="utf-8")
        self.assert_code("E_ARCHIVE_DEPENDENCY", lib.snapshot_files, archive, self.limits)

    def test_structured_key_and_overlap_are_explicit(self) -> None:
        walked = list(lib.walk_json_strings({"KlyxrKey": "Klyxr"}))
        self.assertIn(("structured_key", "/KlyxrKey", "KlyxrKey"), walked)
        self.assertIn(("structured_value", "/KlyxrKey", "Klyxr"), walked)
        self.assertEqual([0, 2], list(lib.overlapping_positions("ababa", "aba")))

    def test_scan_manifest_retains_non_text_and_malformed_json(self) -> None:
        files = [
            ("binary.bin", b"\xff\x00"),
            ("malformed.json", b'{"Klyxr":'),
        ]
        manifest = lib.scan_manifest(files, self.limits)
        self.assertEqual("non_utf8", manifest[0]["text_status"])
        self.assertEqual("invalid_json", manifest[1]["structured_status"])
        self.assertEqual("E_SOURCE_JSON_SYNTAX", manifest[1]["structured_error"])

    def test_freshness_constant_bytes_time_and_event(self) -> None:
        surface = self.fixture["external_surfaces"]["surfaces"][0]
        eligible = lib.evaluate_freshness(
            surface, datetime(2026, 10, 24, 12, tzinfo=timezone.utc), "owner_acceptance", set()
        )
        self.assertEqual((True, "eligible"), eligible)
        expired = lib.evaluate_freshness(
            surface, datetime(2026, 10, 26, tzinfo=timezone.utc), "owner_acceptance", set()
        )
        self.assertEqual((False, "expired"), expired)
        invalidated = lib.evaluate_freshness(
            surface,
            datetime(2026, 10, 24, 12, tzinfo=timezone.utc),
            "pre_integration",
            {"repository_settings_changed"},
        )
        self.assertEqual((False, "invalidating_event"), invalidated)

        limited = copy.deepcopy(self.fixture["external_surfaces"])
        limited["surfaces"][0]["status"] = "limited"
        path = self.workspace / "limited-external.json"
        self.write_json(path, limited)
        self.assert_code(
            "E_FRESHNESS", verify.verify_freshness, path,
            "2026-10-24T12:00:00Z", "owner_acceptance", [], self.limits,
        )

    def test_evidence_record_and_non_authority_shape(self) -> None:
        record = {
            "record_class": "migration_evidence",
            "protocol_version": "m0.1-v2",
            "phase": "M0.1",
            "source_repository": "fixture/source",
            "source_commit": "1" * 40,
            "source_tree": "2" * 40,
            "accepted_base_commit": "3" * 40,
            "accepted_base_tree": "4" * 40,
            "governing_contract": {"repository": "fixture/source", "commit": "5" * 40, "tree": "6" * 40, "path": "contract.md", "blob": "7" * 40},
            "tooling": {"repository": "fixture/ledger", "commit": "8" * 40, "tree": "9" * 40, "paths": ["protocol"], "blobs": {"protocol": "a" * 40}},
            "inputs": {"repository": "fixture/ledger", "commit": "b" * 40, "tree": "c" * 40, "paths": ["inputs"], "blobs": {"inputs": "d" * 40}, "aggregate_sha256": "e" * 64},
            "external_snapshots": [],
            "generated": {
                "scan_manifest_sha256": "2" * 64,
                "index_sha256": "f" * 64,
                "summary_sha256": "0" * 64,
                "aggregate_sha256": "1" * 64,
            },
            "non_authority": {
                "execution": False, "approval": False, "custody": False,
                "replay_admission": False, "semantic_acceptance": False,
                "merge_permission": False, "release": False, "cutover": False,
                "next_phase": False,
            },
        }
        path = self.workspace / "record.json"
        self.write_json(path, record)
        verify.verify_evidence_record(path, self.limits)
        changed = copy.deepcopy(record)
        changed["non_authority"]["next_phase"] = True
        self.write_json(path, changed)
        self.assert_code("E_RECORD_AUTHORITY", verify.verify_evidence_record, path, self.limits)

    def test_finite_binding_sequence_and_recovery_shape(self) -> None:
        record = {
            "record_class": "integration_binding",
            "protocol_version": "m0.1-v2",
            "phase": "M0.1",
            "sequence": ["C", "E", "D", "P"],
            "C": {"repository": "fixture/source", "commit": "1" * 40, "tree": "2" * 40},
            "E": {
                "repository": "fixture/ledger", "commit": "3" * 40, "tree": "4" * 40,
                "source_candidate_commit": "1" * 40, "source_candidate_tree": "2" * 40,
                "index_sha256": "5" * 64,
            },
            "D": {
                "repository": "fixture/ledger", "review_commit": "6" * 40,
                "review_tree": "7" * 40, "review_blob": "8" * 40,
                "owner_decision_commit": "9" * 40, "owner_decision_tree": "a" * 40,
                "owner_decision_blob": "b" * 40, "source_candidate_commit": "1" * 40,
                "evidence_commit": "3" * 40,
            },
            "P": {
                "source_merge_commit": "c" * 40, "source_merge_tree": "d" * 40,
                "ledger_merge_commit": "e" * 40, "ledger_merge_tree": "f" * 40,
                "source_candidate_commit": "1" * 40, "evidence_commit": "3" * 40,
                "review_commit": "6" * 40, "owner_decision_commit": "9" * 40,
                "correspondence": True,
            },
            "recovery": {
                "repository": "fixture/ledger", "retained_refs": ["refs/heads/main"],
                "tested_at": "2026-10-24T12:00:00Z", "restored_commit": "3" * 40,
                "restored_tree": "4" * 40, "result": "succeeded",
            },
        }
        path = self.workspace / "binding.json"
        self.write_json(path, record)
        verify.verify_binding_record(path, self.limits)
        changed = copy.deepcopy(record)
        changed["P"]["evidence_commit"] = "0" * 40
        self.write_json(path, changed)
        self.assert_code("E_BINDING_CORRESPONDENCE", verify.verify_binding_record, path, self.limits)

    def test_mutation_manifest_is_complete_and_unique(self) -> None:
        manifest = json.loads((FIXTURES / "mutations.json").read_text(encoding="utf-8"))
        ids = [item["mutation_id"] for item in manifest["mutations"]]
        self.assertEqual(len(ids), len(set(ids)))
        required = {
            "duplicate-json-key", "non-nfc-string", "non-injective-mapping",
            "unknown-unit-kind", "equal-count-different-key", "different-scan-manifest",
            "stale-rule-count",
            "missing-chunk", "extra-chunk", "tampered-chunk", "reordered-rows",
            "oversized-row", "symlink-source", "archive-root", "limited-required-surface",
            "expired-unchanged-snapshot", "invalidating-event",
        }
        self.assertEqual(required, set(ids))


if __name__ == "__main__":
    if not sys.flags.isolated:
        print("E_RUNTIME_ISOLATION: invoke with python3 -I", file=sys.stderr)
        raise SystemExit(2)
    unittest.main(verbosity=2)
