#!/usr/bin/env python3
"""Synthetic tests for the proposed M0.1 v2 protocol.

Do not execute before exact-revision independent review and owner authorization.
The mutation manifest names every dedicated negative test method.
"""

from __future__ import annotations

import base64
import copy
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest import mock


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


lib = load_module("_bowfin_m01v2_protocol_lib", "protocol_lib.py")
generate = load_module("_m01v2_test_generate", "generate.py")
audit_scan = load_module("_m01v2_test_audit", "audit_scan.py")
verify = load_module("_m01v2_test_verify", "verify.py")


class ProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="m01v2-")
        self.workspace = Path(self.temporary.name)
        self.limits = lib.load_limits(ROOT / "limits.json")
        self.fixture = json.loads((FIXTURES / "valid-case.json").read_text(encoding="utf-8"))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_code(self, code: str, callable_: Any, *args: Any, **kwargs: Any) -> None:
        with self.assertRaises(lib.ProtocolError) as caught:
            callable_(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)

    def test_protocol_error_identity_is_shared(self) -> None:
        self.assertIs(lib, generate.lib)
        self.assertIs(lib, audit_scan.lib)
        self.assertIs(lib, verify.lib)
        self.assert_code("E_IDENTIFIER", generate.lib.require_identifier, "_bad", "fixture")
        with self.assertRaises(ValueError):
            self.assert_code("E_IDENTIFIER", lambda: (_ for _ in ()).throw(ValueError("unrelated")))

    def write_json(self, path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(lib.canonical_json_bytes(value, self.limits))

    def compact_documents(self) -> dict[str, Any]:
        fixture = copy.deepcopy(self.fixture)
        surface = fixture["external_surfaces"]["surfaces"][0]
        return {
            "mappings.json": fixture["mappings"],
            "classification-rules.json": fixture["rules"],
            "audit-policy.json": fixture["audit_policy"],
            "surface-register.json": {
                "protocol_version": "m0.1-v2",
                "required_surfaces": [{"surface_id": surface["surface_id"], "class": surface["class"]}],
            },
            "external-surfaces.json": fixture["external_surfaces"],
            "applicability-decisions.json": {"protocol_version": "m0.1-v2", "decisions": []},
            "visual-inspection.json": {"protocol_version": "m0.1-v2", "visuals": []},
            "limitations.json": {"protocol_version": "m0.1-v2", "limitations": []},
        }

    def make_export(self, root: Path, repository: str, fixture: bool = True) -> tuple[Path, dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            data = path.read_bytes()
            relative = path.relative_to(root).as_posix()
            mode = "100755" if path.stat().st_mode & 0o100 else "100644"
            entries.append({
                "path": relative, "mode": mode, "blob_sha1": lib.git_object_sha1("blob", data),
                "sha256": lib.sha256_hex(data), "byte_count": len(data),
            })
        tree = lib._git_tree_sha(entries, self.limits)
        raw_commit = (
            f"tree {tree}\nauthor Fixture <fixture@example.invalid> 0 +0000\n"
            f"committer Fixture <fixture@example.invalid> 0 +0000\n\nfixture\n"
        ).encode("ascii")
        commit = lib.git_object_sha1("commit", raw_commit)
        document = {
            "record_class": "authenticated_git_export", "protocol_version": "m0.1-v2",
            "repository": repository, "commit": commit, "tree": tree,
            "commit_object_base64": base64.b64encode(raw_commit).decode("ascii"),
            "fixture": fixture,
            "eligibility": "synthetic_fixture" if fixture else "current_accepted_dependency",
            "view_prefix": "", "view_tree": tree, "tree_proof": [],
            "entries": entries,
        }
        path = root.parent / f"{root.name}-export.json"
        self.write_json(path, document)
        return path, document

    def tree_entry(self, path: str, data: bytes, mode: str = "100644") -> dict[str, Any]:
        return {
            "path": path, "mode": mode,
            "blob_sha1": lib.git_object_sha1("blob", data),
        }

    def bound_record(self, path: str, data: bytes) -> dict[str, Any]:
        return {
            "path": path,
            "blob_sha1": lib.git_object_sha1("blob", data),
            "sha256": lib.sha256_hex(data),
            "content_base64": base64.b64encode(data).decode("ascii"),
        }

    def commit_evidence(
        self, repository: str, branch: str, tree_entries: list[dict[str, Any]],
        parents: list[str], message: str,
    ) -> dict[str, Any]:
        tree_entries = sorted(copy.deepcopy(tree_entries), key=lambda item: item["path"].encode("utf-8"))
        tree = lib.git_tree_objects(tree_entries, self.limits, allow_archive=True)[0]
        headers = [f"tree {tree}", *(f"parent {parent}" for parent in parents)]
        raw = ("\n".join(headers) + "\nauthor Fixture <fixture@example.invalid> 0 +0000\ncommitter Fixture <fixture@example.invalid> 0 +0000\n\n" + message + "\n").encode("ascii")
        return {
            "repository": repository, "branch": branch,
            "commit": lib.git_object_sha1("commit", raw), "tree": tree,
            "parents": parents,
            "commit_object_base64": base64.b64encode(raw).decode("ascii"),
            "tree_entries": tree_entries,
        }

    def build_valid(self, name: str = "valid") -> dict[str, Any]:
        case = self.workspace / name
        source = case / "source"
        inputs = case / "inputs"
        source.mkdir(parents=True)
        inputs.mkdir(parents=True)
        for relative, text in self.fixture["source_files"].items():
            path = source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="")
        for relative, document in self.compact_documents().items():
            self.write_json(inputs / relative, document)
        source_export_path, source_export = self.make_export(source, "fixture/source")
        input_export_path, input_export = self.make_export(inputs, "fixture/inputs")
        _, source_files = lib.verify_git_export(source, source_export_path, self.limits, "fixture/source", source_export["commit"], source_export["tree"], "", source_export["tree"], True)
        _, input_files = lib.verify_git_export(inputs, input_export_path, self.limits, "fixture/inputs", input_export["commit"], input_export["tree"], "", input_export["tree"], True)
        compact = dict(input_files)
        mappings = generate.validate_mappings(lib.strict_json_bytes(compact["mappings.json"], self.limits, "mappings"), self.limits)
        rules = generate.validate_rules(lib.strict_json_bytes(compact["classification-rules.json"], self.limits, "rules"), mappings, self.limits)
        rows = generate.classify(generate.discover(source_files, mappings, "fixture/source", source_export["tree"], self.limits), mappings, rules, self.limits)
        package = case / "package"
        lib.write_package(rows, lib.scan_manifest(source_files, self.limits), package, self.limits)
        families = audit_scan.validate_policy(lib.strict_json_bytes(compact["audit-policy.json"], self.limits, "audit"), self.limits)
        candidates = audit_scan.discover(source_files, families, "fixture/source", source_export["tree"], self.limits)
        manifest = lib.scan_manifest(source_files, self.limits)
        audit = {
            "protocol_version": "m0.1-v2", "source_repository": "fixture/source",
            "source_commit": source_export["commit"], "source_tree": source_export["tree"],
            "source_export_sha256": lib.export_digest(source_export, self.limits),
            "input_export_sha256": lib.export_digest(input_export, self.limits),
            "scan_manifest_sha256": lib.scan_manifest_digest(manifest, self.limits),
            "scan_manifest": manifest, "candidate_count": len(candidates), "candidates": candidates,
        }
        audit_path = case / "audit.json"
        self.write_json(audit_path, audit)
        return {"case": case, "source": source, "inputs": inputs, "source_export_path": source_export_path, "input_export_path": input_export_path, "source_export": source_export, "input_export": input_export, "package": package, "audit_path": audit_path, "mappings": mappings, "rules": rules, "rows": rows}

    def verify_valid(self, built: dict[str, Any]) -> None:
        rows = verify.verify_package(built["package"], "fixture/source", built["source_export"]["tree"], self.limits)
        index = verify.canonical_document(built["package"] / "index.json", self.limits)
        verify.reconcile(rows, built["audit_path"], self.limits, "fixture/source", built["source_export"]["commit"], built["source_export"]["tree"], lib.export_digest(built["source_export"], self.limits), lib.export_digest(built["input_export"], self.limits), index["scan_manifest_sha256"])

    def test_valid_authenticated_generation_and_reconciliation(self) -> None:
        self.verify_valid(self.build_valid())

    def test_literal_precomputed_vectors(self) -> None:
        vectors = json.loads((FIXTURES / "vectors.json").read_text(encoding="utf-8"))
        self.assertEqual(vectors["canonical_json"]["expected_utf8_hex"], lib.canonical_json_bytes(vectors["canonical_json"]["value"], self.limits).hex())
        self.assertEqual(vectors["aggregate"]["expected_sha256"], lib.aggregate_digest(vectors["aggregate"]["descriptors"]))
        occurrence = vectors["occurrence_key"]
        self.assertEqual(occurrence["expected"], lib.occurrence_key(occurrence["repository"], occurrence["tree"], occurrence["path"], occurrence["unit_kind"], occurrence["locator"], occurrence["namespace"], occurrence["original"], self.limits))

    def test_duplicate_json_key(self) -> None:
        self.assert_code("E_JSON_DUPLICATE_KEY", lib.strict_json_bytes, b'{"a":1,"a":2}\n', self.limits, "duplicate")

    def test_non_nfc_string(self) -> None:
        self.assert_code("E_JSON_NFC", lib.strict_json_bytes, json.dumps({"x": "e\u0301"}, ensure_ascii=False).encode(), self.limits, "nfc")

    def test_non_injective_mapping_including_retain(self) -> None:
        document = copy.deepcopy(self.fixture["mappings"])
        document["mappings"].append({"mapping_id": "retain-brand", "namespace": "display_brand", "original": "Bowfin", "canonical": None, "policy": "retain"})
        self.assert_code("E_MAPPING_INJECTIVE", generate.validate_mappings, document, self.limits)

    def test_unknown_unit_kind(self) -> None:
        mappings = generate.validate_mappings(self.fixture["mappings"], self.limits)
        document = copy.deepcopy(self.fixture["rules"])
        document["rules"][0]["selector"]["unit_kind"] = "mystery"
        self.assert_code("E_SELECTOR_UNIT", generate.validate_rules, document, mappings, self.limits)

    def test_authenticated_export_rejects_wrong_tree(self) -> None:
        built = self.build_valid("wrong-tree")
        document = copy.deepcopy(built["source_export"])
        document["tree"] = "0" * 40
        self.write_json(built["source_export_path"], document)
        self.assert_code("E_EXPORT_IDENTITY", lib.verify_git_export, built["source"], built["source_export_path"], self.limits, "fixture/source", document["commit"], built["source_export"]["tree"], "", built["source_export"]["tree"], True)

    def test_authenticated_export_rejects_stale_bytes_mode_and_extra_path(self) -> None:
        built = self.build_valid("stale")
        (built["source"] / "notes.txt").write_text("changed", encoding="utf-8")
        self.assert_code("E_EXPORT_CONTENT", lib.verify_git_export, built["source"], built["source_export_path"], self.limits, "fixture/source", built["source_export"]["commit"], built["source_export"]["tree"], "", built["source_export"]["tree"], True)
        built = self.build_valid("extra")
        (built["source"] / "extra.txt").write_text("extra", encoding="utf-8")
        self.assert_code("E_EXPORT_PATH_SET", lib.verify_git_export, built["source"], built["source_export_path"], self.limits, "fixture/source", built["source_export"]["commit"], built["source_export"]["tree"], "", built["source_export"]["tree"], True)

    def test_export_eligibility_separates_fixture_and_production(self) -> None:
        built = self.build_valid("eligibility")
        self.assert_code("E_EXPORT_IDENTITY", lib.verify_git_export, built["source"], built["source_export_path"], self.limits, "fixture/source", built["source_export"]["commit"], built["source_export"]["tree"], "", built["source_export"]["tree"], False)

    def test_authenticated_subtree_view_keeps_archive_opaque_and_ineligible(self) -> None:
        repository_root = self.workspace / "view-repository"
        (repository_root / "protocol" / "current").mkdir(parents=True)
        (repository_root / "archive" / "unaccepted").mkdir(parents=True)
        (repository_root / "protocol" / "current" / "current.txt").write_bytes(b"current\n")
        (repository_root / "archive" / "unaccepted" / "history.txt").write_bytes(b"history\n")
        raw_commit = (
            b"tree 8f3fbf9033050d4197f49028cfb71f6011e6e2fa\n"
            b"author Fixture <fixture@example.invalid> 0 +0000\n"
            b"committer Fixture <fixture@example.invalid> 0 +0000\n\nfixture\n"
        )
        root_entries = [
            {"name": "archive", "mode": "40000", "object_sha1": "3674c867dc467b680453fc818c722be2ba29bb7b"},
            {"name": "protocol", "mode": "40000", "object_sha1": "902a1f92d2e1dfdddc0cfc2f53233c5350998838"},
        ]
        document = {
            "record_class": "authenticated_git_export", "protocol_version": "m0.1-v2",
            "repository": "fixture/ledger", "commit": "22a9ff4c7ecaa9f0d5f6c330784870154739a066",
            "tree": "8f3fbf9033050d4197f49028cfb71f6011e6e2fa",
            "commit_object_base64": base64.b64encode(raw_commit).decode("ascii"),
            "fixture": True, "eligibility": "synthetic_fixture",
            "view_prefix": "protocol/current",
            "view_tree": "1601c399f9105099ffe3731c4481be60af8be50f",
            "tree_proof": [
                {"tree": "8f3fbf9033050d4197f49028cfb71f6011e6e2fa", "entries": root_entries},
                {"tree": "902a1f92d2e1dfdddc0cfc2f53233c5350998838", "entries": [
                    {"name": "current", "mode": "40000", "object_sha1": "1601c399f9105099ffe3731c4481be60af8be50f"},
                ]},
            ],
            "entries": [{
                "path": "current.txt", "mode": "100644",
                "blob_sha1": "5b9023a315ae79fd8cbe9e8c3a6f8053f0ed3ddb",
                "sha256": "48aa6cae8c70abdb28631d22b316e6d9f9d0768ec2911de7090e248b2afe6ca1",
                "byte_count": 8,
            }],
        }
        export_path = self.workspace / "eligible-view-export.json"
        self.write_json(export_path, document)
        _export, files = lib.verify_git_export(
            repository_root, export_path, self.limits, "fixture/ledger",
            document["commit"], document["tree"], document["view_prefix"],
            document["view_tree"], True,
        )
        self.assertEqual([("current.txt", b"current\n")], files)

        tampered = copy.deepcopy(document)
        tampered["tree_proof"][0]["entries"][0]["object_sha1"] = "0" * 40
        self.write_json(export_path, tampered)
        self.assert_code(
            "E_EXPORT_PROOF", lib.verify_git_export, repository_root, export_path,
            self.limits, "fixture/ledger", document["commit"], document["tree"],
            document["view_prefix"], document["view_tree"], True,
        )

        archive = copy.deepcopy(document)
        archive["view_prefix"] = "archive/unaccepted"
        archive["view_tree"] = "7e5de99c9e33b5f58940b9dfabe98337bc43aa1e"
        archive["tree_proof"] = [
            {"tree": document["tree"], "entries": root_entries},
            {"tree": "3674c867dc467b680453fc818c722be2ba29bb7b", "entries": [
                {"name": "unaccepted", "mode": "40000", "object_sha1": archive["view_tree"]},
            ]},
        ]
        archive["entries"] = [{
            "path": "history.txt", "mode": "100644",
            "blob_sha1": "c375d5ba0db809e5bb4953d9665c341b38208914",
            "sha256": "834e1cc36168f216747fbf3b8de6cc700e64700276b25a3563233b2df000fdfb",
            "byte_count": 8,
        }]
        self.write_json(export_path, archive)
        self.assert_code(
            "E_ARCHIVE_DEPENDENCY", lib.verify_git_export, repository_root,
            export_path, self.limits, "fixture/ledger", document["commit"],
            document["tree"], archive["view_prefix"], archive["view_tree"], True,
        )

    def test_intrinsic_locators_distinguish_multiple_identities(self) -> None:
        mapping_document = {"protocol_version": "m0.1-v2", "mappings": [
            {"mapping_id": "ked1", "namespace": "engineering_decision", "original": "KED-001", "canonical": "BED-001", "policy": "replace"},
            {"mapping_id": "ked2", "namespace": "engineering_decision", "original": "KED-002", "canonical": "BED-002", "policy": "replace"},
        ]}
        mappings = generate.validate_mappings(mapping_document, self.limits)
        files = [("KED-001-KED-002.json", b'{"KED-001":"KED-002"}\n')]
        rows = generate.discover(files, mappings, "fixture/source", "1" * 40, self.limits)
        keys = [row["occurrence_key"] for row in rows]
        self.assertEqual(len(keys), len(set(keys)))
        structured = {
            (row["unit_kind"], row["original"]): row
            for row in rows
            if row["unit_kind"] in {"structured_key", "structured_value"}
        }
        expected_locator = {
            "json_pointer": "/KED-001", "value_byte_start": 0, "value_byte_end": 7,
        }
        self.assertEqual(expected_locator, structured[("structured_key", "KED-001")]["locator"])
        self.assertEqual(expected_locator, structured[("structured_value", "KED-002")]["locator"])
        self.assertNotEqual(
            structured[("structured_key", "KED-001")]["occurrence_key"],
            structured[("structured_value", "KED-002")]["occurrence_key"],
        )
        family = [{
            "family_id": "ked-family", "kind": "ascii_digit_suffix", "literal": "KED-",
            "namespace": "engineering_decision",
            "unit_kinds": ["path_component", "embedded_identity", "structured_key", "structured_value"],
        }]
        audited = audit_scan.discover(files, family, "fixture/source", "1" * 40, self.limits)
        self.assertEqual(set(keys), {row["occurrence_key"] for row in audited})
        self.assertEqual(6, len(rows))
        self.assertEqual({
            ("path_component", "KED-001"), ("path_component", "KED-002"),
            ("embedded_identity", "KED-001"), ("embedded_identity", "KED-002"),
            ("structured_key", "KED-001"), ("structured_value", "KED-002"),
        }, {(row["unit_kind"], row["original"]) for row in rows})
        self.assertNotIn(
            b"match_index",
            b"".join(lib.canonical_json_bytes(row["locator"], self.limits, trailing_lf=False) for row in rows),
        )

    def test_candidate_key_separates_physical_discovery_from_semantics(self) -> None:
        mapping_document = {"protocol_version": "m0.1-v2", "mappings": [
            {"mapping_id": "cli", "namespace": "cli_invocation", "original": "klyxr", "canonical": "bowfin", "policy": "compatibility"},
            {"mapping_id": "brand", "namespace": "display_brand", "original": "klyxr", "canonical": "Bowfin", "policy": "replace"},
        ]}
        mappings = generate.validate_mappings(mapping_document, self.limits)
        candidates = generate.discover(
            [("mixed.txt", b"klyxr then klyxr")], mappings,
            "fixture/source", "1" * 40, self.limits,
        )
        grouped: dict[str, list[dict[str, Any]]] = {}
        for candidate in candidates:
            grouped.setdefault(candidate["candidate_key"], []).append(candidate)
        self.assertEqual(2, len(grouped))
        self.assertEqual([2, 2], sorted(len(group) for group in grouped.values()))
        keys = list(grouped)
        rules_document = {"protocol_version": "m0.1-v2", "rules": [
            {
                "rule_id": "cli-first", "selector": {
                    "mapping_id": "cli", "unit_kind": "raw_text",
                    "candidate_keys": [keys[0]],
                },
                "expected_count": 1, "role": "compatibility", "phase": "M4",
                "rationale": "The first physical occurrence is the legacy command.",
                "representative_context": ["klyxr"], "boundary_context": ["command"],
                "producer": "CLI parser", "consumer": "operator",
                "support_policy": "retain until a later accepted BED removes it",
                "validation_test_id": "synthetic:cli-first",
                "historical_relationship": None,
            },
            {
                "rule_id": "brand-second", "selector": {
                    "mapping_id": "brand", "unit_kind": "raw_text",
                    "candidate_keys": [keys[1]],
                },
                "expected_count": 1, "role": "live", "phase": "M1",
                "rationale": "The second physical occurrence is display identity.",
                "representative_context": ["klyxr"], "boundary_context": ["brand"],
                "producer": "documentation", "consumer": "reader",
                "support_policy": "replace in M1",
                "validation_test_id": "synthetic:brand-second",
                "historical_relationship": None,
            },
        ]}
        rules = generate.validate_rules(rules_document, mappings, self.limits)
        rows = generate.classify(candidates, mappings, rules, self.limits)
        self.assertEqual({"cli", "brand"}, {row["mapping_id"] for row in rows})
        self.assertEqual(2, len({row["candidate_key"] for row in rows}))

        broad = copy.deepcopy(rules_document)
        for rule in broad["rules"]:
            rule["selector"].pop("candidate_keys")
            rule["selector"]["path_exact"] = "mixed.txt"
        broad_rules = generate.validate_rules(broad, mappings, self.limits)
        self.assert_code(
            "E_MULTIPLE_CLASSIFICATION", generate.classify,
            candidates, mappings, broad_rules, self.limits,
        )

    def test_exact_candidate_keys_split_roles_within_one_file(self) -> None:
        mapping_document = {"protocol_version": "m0.1-v2", "mappings": [
            {"mapping_id": "brand", "namespace": "display_brand", "original": "Klyxr", "canonical": "Bowfin", "policy": "replace"},
        ]}
        mappings = generate.validate_mappings(mapping_document, self.limits)
        candidates = generate.discover(
            [("history.md", b"Klyxr then Klyxr")], mappings,
            "fixture/source", "2" * 40, self.limits,
        )
        keys = [candidate["candidate_key"] for candidate in candidates]
        rules_document = {"protocol_version": "m0.1-v2", "rules": [
            {
                "rule_id": "live", "selector": {"mapping_id": "brand", "unit_kind": "raw_text", "candidate_keys": [keys[0]]},
                "expected_count": 1, "role": "live", "phase": "M1",
                "rationale": "Live prose.", "representative_context": ["Klyxr"],
                "boundary_context": ["live"], "producer": "docs", "consumer": "reader",
                "support_policy": "replace", "validation_test_id": "synthetic:live",
                "historical_relationship": None,
            },
            {
                "rule_id": "historical", "selector": {"mapping_id": "brand", "unit_kind": "raw_text", "candidate_keys": [keys[1]]},
                "expected_count": 1, "role": "historical", "phase": "M7",
                "rationale": "Quoted history.", "representative_context": ["Klyxr"],
                "boundary_context": ["history"], "producer": None, "consumer": None,
                "support_policy": "retain as history", "validation_test_id": "synthetic:history",
                "historical_relationship": "records the predecessor identity",
            },
        ]}
        rules = generate.validate_rules(rules_document, mappings, self.limits)
        rows = generate.classify(candidates, mappings, rules, self.limits)
        self.assertEqual({"live", "historical"}, {row["role"] for row in rows})

        families = audit_scan.validate_policy({
            "protocol_version": "m0.1-v2", "independently_authored": True,
            "families": [
                {"family_id": "live", "kind": "literal", "literal": "Klyxr",
                 "namespace": "display_brand", "unit_kinds": ["raw_text"],
                 "candidate_keys": [keys[0]]},
                {"family_id": "historical", "kind": "literal", "literal": "Klyxr",
                 "namespace": "display_brand", "unit_kinds": ["raw_text"],
                 "candidate_keys": [keys[1]]},
            ],
        }, self.limits)
        audited = audit_scan.discover(
            [("history.md", b"Klyxr then Klyxr")], families,
            "fixture/source", "2" * 40, self.limits,
        )
        self.assertEqual(set(keys), {row["candidate_key"] for row in audited})
        self.assertEqual(
            {row["occurrence_key"] for row in rows},
            {row["occurrence_key"] for row in audited},
        )

    def test_independent_auditor_reconciles_exact_keys(self) -> None:
        self.verify_valid(self.build_valid("independent"))

    def test_equal_count_different_key(self) -> None:
        built = self.build_valid("different-key")
        audit = verify.canonical_document(built["audit_path"], self.limits)
        audit["candidates"][0]["locator"][next(key for key in audit["candidates"][0]["locator"] if key.endswith("start"))] += 1
        candidate = audit["candidates"][0]
        candidate["candidate_key"] = lib.candidate_key(
            "fixture/source", audit["source_tree"], candidate["path"],
            candidate["unit_kind"], candidate["locator"], candidate["original"], self.limits,
        )
        candidate["occurrence_key"] = lib.occurrence_key("fixture/source", audit["source_tree"], candidate["path"], candidate["unit_kind"], candidate["locator"], candidate["namespace"], candidate["original"], self.limits)
        self.write_json(built["audit_path"], audit)
        rows = verify.verify_package(built["package"], "fixture/source", built["source_export"]["tree"], self.limits)
        index = verify.canonical_document(built["package"] / "index.json", self.limits)
        self.assert_code("E_KEY_SET_MISMATCH", verify.reconcile, rows, built["audit_path"], self.limits, "fixture/source", built["source_export"]["commit"], built["source_export"]["tree"], lib.export_digest(built["source_export"], self.limits), lib.export_digest(built["input_export"], self.limits), index["scan_manifest_sha256"])

    def test_stale_rule_count(self) -> None:
        built = self.build_valid("stale-count")
        rules = copy.deepcopy(built["rules"])
        rules[0]["expected_count"] += 1
        files = lib.verify_git_export(built["source"], built["source_export_path"], self.limits, "fixture/source", built["source_export"]["commit"], built["source_export"]["tree"], "", built["source_export"]["tree"], True)[1]
        candidates = generate.discover(files, built["mappings"], "fixture/source", built["source_export"]["tree"], self.limits)
        self.assert_code("E_EXPECTED_COUNT", generate.classify, candidates, built["mappings"], rules, self.limits)

    def test_missing_extra_and_tampered_chunks(self) -> None:
        for name, mutation, code in (("missing", "missing", "E_CHUNK_SET"), ("extra", "extra", "E_CHUNK_SET"), ("tamper", "tamper", "E_CHUNK_DESCRIPTOR")):
            built = self.build_valid(name)
            chunk = next((built["package"] / "occurrences").iterdir())
            if mutation == "missing": chunk.unlink()
            elif mutation == "extra": (built["package"] / "occurrences" / "9999.jsonl").write_bytes(b"{}\n")
            else: chunk.write_bytes(chunk.read_bytes().replace(b"Klyxr", b"KLYXR", 1))
            self.assert_code(code, verify.verify_package, built["package"], "fixture/source", built["source_export"]["tree"], self.limits)

    def test_rehashed_noncanonical_chunk_repartition(self) -> None:
        built = self.build_valid("repartition")
        index_path = built["package"] / "index.json"
        index = verify.canonical_document(index_path, self.limits)
        if len(index["chunks"]) == 1:
            rows = (built["package"] / "occurrences" / "0000.jsonl").read_bytes().splitlines(keepends=True)
            self.assertGreater(len(rows), 1)
            first, second = b"".join(rows[:1]), b"".join(rows[1:])
            (built["package"] / "occurrences" / "0000.jsonl").write_bytes(first)
            (built["package"] / "occurrences" / "0001.jsonl").write_bytes(second)
            descriptors = []
            for number, data in enumerate((first, second)):
                parsed = [json.loads(line) for line in data.splitlines()]
                descriptors.append({"path": f"occurrences/{number:04d}.jsonl", "sha256": lib.sha256_hex(data), "byte_count": len(data), "row_count": len(parsed), "first_key": parsed[0]["occurrence_key"], "last_key": parsed[-1]["occurrence_key"]})
            index["chunks"] = descriptors
            index["aggregate_sha256"] = lib.aggregate_digest(descriptors)
            index["total_bytes"] = sum(item["byte_count"] for item in descriptors)
            self.write_json(index_path, index)
        self.assert_code("E_CHUNK_BOUNDARY", verify.verify_package, built["package"], "fixture/source", built["source_export"]["tree"], self.limits)

    def test_output_symlink_and_ancestor_symlink(self) -> None:
        if not hasattr(Path, "symlink_to"):
            self.skipTest("symlinks unavailable")
        parent = self.workspace / "outputs"
        parent.mkdir()
        target = self.workspace / "target"
        target.mkdir()
        (parent / "link").symlink_to(target, target_is_directory=True)
        self.assert_code("E_SYMLINK", lib.write_exclusive_document, parent / "link" / "out.json", {"x": 1}, self.limits, 1000)

    def test_competing_package_creator_is_never_deleted(self) -> None:
        output = self.workspace / "contended-package"
        original_mkdir = Path.mkdir

        def competing_mkdir(path: Path, *args: Any, **kwargs: Any) -> None:
            original_mkdir(path, *args, **kwargs)
            (path / "competitor-owned.txt").write_text("preserve me", encoding="utf-8")
            raise FileExistsError("simulated competing creator")

        with mock.patch.object(Path, "mkdir", new=competing_mkdir):
            self.assert_code("E_OUTPUT_CREATE", lib.write_package, [], [], output, self.limits)
        self.assertEqual("preserve me", (output / "competitor-owned.txt").read_text(encoding="utf-8"))

    def test_interrupted_document_write_removes_only_owned_partial(self) -> None:
        output = self.workspace / "partial.json"
        with mock.patch.object(os, "write", side_effect=OSError("simulated interruption")):
            self.assert_code("E_OUTPUT_WRITE", lib._write_exclusive, output, b"partial")
        self.assertFalse(output.exists())

    def test_interrupted_package_never_publishes_completion_marker(self) -> None:
        output = self.workspace / "interrupted-package"
        original_write = lib._write_exclusive

        def interrupt_before_index(path: Path, data: bytes) -> None:
            if path.name == "index.json":
                lib.fail("E_OUTPUT_WRITE", "simulated package interruption")
            original_write(path, data)

        with mock.patch.object(lib, "_write_exclusive", side_effect=interrupt_before_index):
            self.assert_code("E_OUTPUT_WRITE", lib.write_package, [], [], output, self.limits)
        self.assertTrue(output.is_dir())
        self.assertFalse((output / "publication.json").exists())

    def test_fifo_is_rejected_before_blocking_open(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation unavailable")
        fifo = self.workspace / "input.fifo"
        os.mkfifo(fifo)
        self.assert_code("E_SPECIAL_FILE", lib.read_bounded_file, fifo, 1024)

    def test_missing_publication_marker_rejects_partial_package(self) -> None:
        built = self.build_valid("missing-publication")
        (built["package"] / "publication.json").unlink()
        self.assert_code(
            "E_PACKAGE_FILES", verify.verify_package, built["package"],
            "fixture/source", built["source_export"]["tree"], self.limits,
        )

    def test_cumulative_package_budget_rejects_before_next_read(self) -> None:
        built = self.build_valid("package-budget")
        publication_size = (built["package"] / "publication.json").stat().st_size
        index_size = (built["package"] / "index.json").stat().st_size
        limits = dict(self.limits)
        limits["max_generated_bytes"] = publication_size + index_size - 1
        self.assert_code(
            "E_GENERATED_SIZE", verify.verify_package, built["package"],
            "fixture/source", built["source_export"]["tree"], limits,
        )

    def test_auditor_high_work_no_match_stops_at_budget(self) -> None:
        limits = dict(self.limits)
        limits["max_processing_steps"] = 16
        budget = audit_scan.lib.WorkBudget(limits)
        family = {
            "kind": "ascii_casefold_literal", "literal": "A" * 64 + "B",
        }
        with self.assertRaises(audit_scan.lib.ProtocolError) as caught:
            list(audit_scan._matches("A" * 4096, family, budget))
        self.assertEqual("E_PROCESSING_STEPS", caught.exception.code)

    def test_archive_and_dot_path_reject(self) -> None:
        self.assert_code("E_ARCHIVE_DEPENDENCY", lib.validate_relpath, "archive/unaccepted/data", self.limits)
        self.assert_code("E_PATH", lib.validate_relpath, "a/../b", self.limits)

    def test_incremental_processing_limit(self) -> None:
        mappings = generate.validate_mappings(self.fixture["mappings"], self.limits)
        rules = generate.validate_rules(self.fixture["rules"], mappings, self.limits)
        candidates = generate.discover(
            [("src/Klyxr.txt", b"Klyxr Klyxr")], mappings,
            "fixture/source", "1" * 40, self.limits,
        )
        self.assertTrue(candidates)
        exact_index_cost = (
            sum(1 + len(item["mapping_id"]) for item in mappings)
            + sum(
                1 + len(rule["selector"]["mapping_id"])
                + len(rule["selector"]["unit_kind"])
                for rule in rules
            )
            + sum(1 + len(rule["rule_id"]) for rule in rules)
        )
        limits = {**self.limits, "max_processing_steps": exact_index_cost}
        self.assert_code(
            "E_PROCESSING_STEPS", generate.classify,
            candidates, mappings, rules, limits,
        )

    def test_direct_compact_input_field_validation(self) -> None:
        files = {name: lib.canonical_json_bytes(value, self.limits) for name, value in self.compact_documents().items()}
        verify.validate_compact_input_files(files, self.limits)
        changed = dict(files)
        bad = copy.deepcopy(self.fixture["external_surfaces"])
        bad["surfaces"][0]["unknown"] = True
        changed["external-surfaces.json"] = lib.canonical_json_bytes(bad, self.limits)
        self.assert_code("E_FIELD_UNKNOWN", verify.validate_compact_input_files, changed, self.limits)

        bad_identifier = self.compact_documents()
        bad_identifier["mappings.json"]["mappings"][0]["mapping_id"] = "_invalid"
        changed = {
            name: lib.canonical_json_bytes(value, self.limits)
            for name, value in bad_identifier.items()
        }
        self.assert_code("E_IDENTIFIER", verify.validate_compact_input_files, changed, self.limits)

        bad_suffix = self.compact_documents()
        selector = bad_suffix["classification-rules.json"]["rules"][0]["selector"]
        selector.pop("path_exact", None)
        selector["path_suffix"] = "x" * (self.limits["max_path_bytes"] + 1)
        changed = {
            name: lib.canonical_json_bytes(value, self.limits)
            for name, value in bad_suffix.items()
        }
        self.assert_code("E_SELECTOR_PATH", verify.validate_compact_input_files, changed, self.limits)

    def test_missing_surface_and_unsupported_not_applicable(self) -> None:
        documents = self.compact_documents()
        documents["external-surfaces.json"]["surfaces"] = []
        files = {name: lib.canonical_json_bytes(value, self.limits) for name, value in documents.items()}
        self.assert_code("E_SURFACE_REGISTER", verify.validate_compact_input_files, files, self.limits)
        documents = self.compact_documents()
        documents["external-surfaces.json"]["surfaces"][0]["status"] = "not_applicable"
        files = {name: lib.canonical_json_bytes(value, self.limits) for name, value in documents.items()}
        self.assert_code("E_APPLICABILITY", verify.validate_compact_input_files, files, self.limits)

    def test_freshness_expiry_and_invalidation(self) -> None:
        surface = self.fixture["external_surfaces"]["surfaces"][0]
        self.assertEqual((False, "expired"), lib.evaluate_freshness(surface, datetime(2026, 10, 26, tzinfo=timezone.utc), "owner_acceptance", set()))
        self.assertEqual((False, "invalidating_event"), lib.evaluate_freshness(surface, datetime(2026, 10, 24, 12, tzinfo=timezone.utc), "pre_integration", {"repository_settings_changed"}))

    def test_not_applicable_requires_current_semantic_review(self) -> None:
        subject_commit, subject_tree = "1" * 40, "2" * 40
        surface = copy.deepcopy(self.fixture["external_surfaces"]["surfaces"][0])
        surface["status"] = "not_applicable"
        observation_sha256 = lib.sha256_hex(
            lib.canonical_json_bytes(surface, self.limits, trailing_lf=False)
        )
        review = {
            "record_class": "applicability_review", "protocol_version": "m0.1-v2",
            "surface_id": surface["surface_id"], "disposition": "not_applicable",
            "subject_commit": subject_commit, "subject_tree": subject_tree,
            "observation_sha256": observation_sha256, "reviewer": "Sarah",
            "rationale": "The synthetic facility was absent at observation time.",
            "eligibility_policy": surface["freshness_policy"],
            "limitations": surface["limitations"],
            "non_authority": {"owner_acceptance": False, "merge_permission": False},
        }
        reviews = self.workspace / "freshness-reviews"
        reviews.mkdir()
        self.write_json(reviews / "fixture-review.json", review)
        review_export_path, review_export = self.make_export(reviews, "fixture/reviews", False)
        review_entry = review_export["entries"][0]
        decision = {
            "surface_id": surface["surface_id"], "disposition": "not_applicable",
            "reviewer": review["reviewer"], "rationale": review["rationale"],
            "subject_commit": subject_commit, "subject_tree": subject_tree,
            "record_repository": "fixture/reviews", "record_commit": review_export["commit"],
            "record_tree": review_export["tree"], "record_path": "fixture-review.json",
            "record_blob": review_entry["blob_sha1"], "record_sha256": review_entry["sha256"],
            "observation_sha256": observation_sha256,
            "eligibility_policy": surface["freshness_policy"],
        }
        register_path = self.workspace / "surface-register.json"
        surface_path = self.workspace / "external-surfaces.json"
        decision_path = self.workspace / "applicability-decisions.json"
        self.write_json(register_path, {"protocol_version": "m0.1-v2", "required_surfaces": [{"surface_id": surface["surface_id"], "class": surface["class"]}]})
        self.write_json(surface_path, {"protocol_version": "m0.1-v2", "surfaces": [surface]})
        self.write_json(decision_path, {"protocol_version": "m0.1-v2", "decisions": [decision]})
        arguments = (
            surface_path, register_path, decision_path, "2026-10-24T12:00:00Z",
            "owner_acceptance", [], subject_commit, subject_tree, reviews,
            review_export_path, "fixture/reviews", review_export["commit"],
            review_export["tree"], "", review_export["tree"], self.limits,
        )
        verify.verify_freshness(*arguments)
        invalidated = list(arguments)
        invalidated[5] = ["repository_settings_changed"]
        with self.assertRaises(verify.lib.ProtocolError) as caught:
            verify.verify_freshness(*invalidated)
        self.assertEqual("E_FRESHNESS", caught.exception.code)

        review["reviewer"] = "Unrelated reviewer"
        wrong_reviews = self.workspace / "wrong-freshness-reviews"
        wrong_reviews.mkdir()
        self.write_json(wrong_reviews / "fixture-review.json", review)
        wrong_export_path, wrong_export = self.make_export(wrong_reviews, "fixture/reviews", False)
        wrong_entry = wrong_export["entries"][0]
        decision["record_commit"] = wrong_export["commit"]
        decision["record_tree"] = wrong_export["tree"]
        decision["record_blob"] = wrong_entry["blob_sha1"]
        decision["record_sha256"] = wrong_entry["sha256"]
        self.write_json(decision_path, {"protocol_version": "m0.1-v2", "decisions": [decision]})
        semantic_arguments = list(arguments)
        semantic_arguments[8:15] = [
            wrong_reviews, wrong_export_path, "fixture/reviews", wrong_export["commit"],
            wrong_export["tree"], "", wrong_export["tree"],
        ]
        with self.assertRaises(verify.lib.ProtocolError) as caught:
            verify.verify_freshness(*semantic_arguments)
        self.assertEqual("E_APPLICABILITY_REVIEW", caught.exception.code)

        review["reviewer"] = "Sarah"
        review["non_authority"] = {"owner_acceptance": 0, "merge_permission": 0}
        numeric_reviews = self.workspace / "numeric-freshness-reviews"
        numeric_reviews.mkdir()
        self.write_json(numeric_reviews / "fixture-review.json", review)
        numeric_export_path, numeric_export = self.make_export(
            numeric_reviews, "fixture/reviews", False
        )
        numeric_entry = numeric_export["entries"][0]
        decision["record_commit"] = numeric_export["commit"]
        decision["record_tree"] = numeric_export["tree"]
        decision["record_blob"] = numeric_entry["blob_sha1"]
        decision["record_sha256"] = numeric_entry["sha256"]
        self.write_json(decision_path, {"protocol_version": "m0.1-v2", "decisions": [decision]})
        numeric_arguments = list(arguments)
        numeric_arguments[8:15] = [
            numeric_reviews, numeric_export_path, "fixture/reviews", numeric_export["commit"],
            numeric_export["tree"], "", numeric_export["tree"],
        ]
        with self.assertRaises(verify.lib.ProtocolError) as caught:
            verify.verify_freshness(*numeric_arguments)
        self.assertEqual("E_APPLICABILITY_REVIEW", caught.exception.code)

        review["non_authority"] = {"owner_acceptance": False, "merge_permission": False}
        review["eligibility_policy"] = copy.deepcopy(surface["freshness_policy"])
        review["eligibility_policy"]["point_in_time_only"] = 0
        policy_reviews = self.workspace / "numeric-policy-reviews"
        policy_reviews.mkdir()
        self.write_json(policy_reviews / "fixture-review.json", review)
        policy_export_path, policy_export = self.make_export(
            policy_reviews, "fixture/reviews", False
        )
        policy_entry = policy_export["entries"][0]
        decision["record_commit"] = policy_export["commit"]
        decision["record_tree"] = policy_export["tree"]
        decision["record_blob"] = policy_entry["blob_sha1"]
        decision["record_sha256"] = policy_entry["sha256"]
        self.write_json(decision_path, {"protocol_version": "m0.1-v2", "decisions": [decision]})
        policy_arguments = list(arguments)
        policy_arguments[8:15] = [
            policy_reviews, policy_export_path, "fixture/reviews", policy_export["commit"],
            policy_export["tree"], "", policy_export["tree"],
        ]
        with self.assertRaises(verify.lib.ProtocolError) as caught:
            verify.verify_freshness(*policy_arguments)
        self.assertEqual("E_FRESHNESS_POLICY", caught.exception.code)

    def test_generated_rows_are_bound_to_compact_meaning(self) -> None:
        built = self.build_valid("meaning-binding")
        rows = copy.deepcopy(built["rows"])
        rows[0]["canonical"] = "UnreviewedIdentity"
        package = built["case"] / "meaning-tamper"
        source_files = lib.verify_git_export(
            built["source"], built["source_export_path"], self.limits,
            "fixture/source", built["source_export"]["commit"],
            built["source_export"]["tree"], "", built["source_export"]["tree"], True,
        )[1]
        lib.write_package(rows, lib.scan_manifest(source_files, self.limits), package, self.limits)
        verified_rows = verify.verify_package(
            package, "fixture/source", built["source_export"]["tree"], self.limits
        )
        compact = verify.validate_compact_input_files(
            {path: (built["inputs"] / path).read_bytes() for path in verify.PRODUCTION_INPUT_PATHS},
            self.limits,
        )
        with self.assertRaises(verify.lib.ProtocolError) as caught:
            verify._validate_generated_meaning(verified_rows, compact, self.limits)
        self.assertEqual("E_CLASSIFICATION_BINDING", caught.exception.code)

        constrained = dict(self.limits)
        constrained["max_processing_steps"] = 1
        self.assert_code(
            "E_PROCESSING_STEPS",
            verify._validate_generated_meaning,
            built["rows"], compact, constrained,
        )

    def test_compiler_source_view_must_be_repository_root(self) -> None:
        self.assert_code(
            "E_SOURCE_VIEW", lib.require_root_source_view,
            "nested", "1" * 40, "1" * 40,
        )
        self.assert_code(
            "E_SOURCE_VIEW", lib.require_root_source_view,
            "nested", "1" * 40, "2" * 40,
        )
        self.assert_code(
            "E_SOURCE_VIEW", lib.require_root_source_view,
            "", "1" * 40, "2" * 40,
        )
        lib.require_root_source_view("", "1" * 40, "1" * 40)

    def test_manifest_binary_and_malformed_require_disposition(self) -> None:
        manifest = lib.scan_manifest([("binary.bin", b"\xff"), ("bad.json", b'{"x":')], self.limits)
        self.assertEqual("non_utf8", manifest[0]["text_status"])
        self.assertEqual("invalid_json", manifest[1]["structured_status"])

    def test_evidence_record_binds_actual_exports_and_generated_bytes(self) -> None:
        built = self.build_valid("evidence")
        source_export_path, source_export = self.make_export(built["source"], "fixture/source", False)
        roots: dict[str, tuple[Path, Path, dict[str, Any]]] = {}
        for name, repository, files in (
            ("base", "fixture/source", {"README.md": b"accepted base\n"}),
            ("contract", "fixture/source", {"contract.md": b"contract\n"}),
            ("tooling", "fixture/ledger", {path: (path + "\n").encode() for path in verify.REQUIRED_TOOLING_PATHS}),
        ):
            root = built["case"] / name
            root.mkdir()
            for relative, data in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            export_path, export = self.make_export(root, repository, False)
            roots[name] = (root, export_path, export)

        observations = built["case"] / "observations"
        observations.mkdir()
        (observations / "repository-settings.json").write_bytes(
            b'{"repository":"fixture/source","settings":"observed"}\n'
        )
        observation_export_path, observation_export = self.make_export(
            observations, "fixture/observations", False
        )
        observation_entry = observation_export["entries"][0]
        documents = self.compact_documents()
        surface = documents["external-surfaces.json"]["surfaces"][0]
        surface["snapshot_blob_sha1"] = observation_entry["blob_sha1"]
        surface["snapshot_sha256"] = observation_entry["sha256"]
        for relative, document in documents.items():
            self.write_json(built["inputs"] / relative, document)
        input_export_path, input_export = self.make_export(built["inputs"], "fixture/inputs", False)

        reviews = built["case"] / "reviews"
        reviews.mkdir()
        review_export_path, review_export = self.make_export(reviews, "fixture/reviews", False)
        audit = verify.canonical_document(built["audit_path"], self.limits)
        audit["source_export_sha256"] = lib.export_digest(source_export, self.limits)
        audit["input_export_sha256"] = lib.export_digest(input_export, self.limits)
        self.write_json(built["audit_path"], audit)

        index_data = (built["package"] / "index.json").read_bytes()
        summary_data = (built["package"] / "summary.json").read_bytes()
        manifest_data = (built["package"] / "scan-manifest.json").read_bytes()
        publication_data = (built["package"] / "publication.json").read_bytes()
        audit_data = built["audit_path"].read_bytes()
        index = lib.strict_json_bytes(index_data, self.limits, "index")
        input_entries = {entry["path"]: entry for entry in input_export["entries"]}
        descriptor = [input_entries[path] for path in sorted(verify.PRODUCTION_INPUT_PATHS)]
        contract_entry = roots["contract"][2]["entries"][0]
        expected_tooling = {
            "repository": "fixture/ledger", "commit": roots["tooling"][2]["commit"],
            "tree": roots["tooling"][2]["tree"], "view_prefix": "",
            "view_tree": roots["tooling"][2]["tree"],
            "export_sha256": lib.export_digest(roots["tooling"][2], self.limits),
        }
        record = {
            "record_class": "migration_evidence", "protocol_version": "m0.1-v2", "phase": "M0.1",
            "source": {"repository": "fixture/source", "commit": source_export["commit"], "tree": source_export["tree"], "view_prefix": "", "view_tree": source_export["tree"], "export_sha256": lib.export_digest(source_export, self.limits)},
            "accepted_base": {"repository": "fixture/source", "commit": roots["base"][2]["commit"], "tree": roots["base"][2]["tree"], "view_prefix": "", "view_tree": roots["base"][2]["tree"], "export_sha256": lib.export_digest(roots["base"][2], self.limits)},
            "governing_contract": {"repository": "fixture/source", "commit": roots["contract"][2]["commit"], "tree": roots["contract"][2]["tree"], "view_prefix": "", "view_tree": roots["contract"][2]["tree"], "path": "contract.md", "blob": contract_entry["blob_sha1"], "export_sha256": lib.export_digest(roots["contract"][2], self.limits)},
            "tooling": {**expected_tooling, "required_paths": sorted(verify.REQUIRED_TOOLING_PATHS)},
            "inputs": {"repository": "fixture/inputs", "commit": input_export["commit"], "tree": input_export["tree"], "view_prefix": "", "view_tree": input_export["tree"], "required_paths": sorted(verify.PRODUCTION_INPUT_PATHS), "export_sha256": lib.export_digest(input_export, self.limits), "aggregate_sha256": lib.sha256_hex(lib.canonical_json_bytes(descriptor, self.limits, trailing_lf=False))},
            "observations": {"repository": "fixture/observations", "commit": observation_export["commit"], "tree": observation_export["tree"], "view_prefix": "", "view_tree": observation_export["tree"], "required_paths": ["repository-settings.json"], "export_sha256": lib.export_digest(observation_export, self.limits)},
            "reviews": {"repository": "fixture/reviews", "commit": review_export["commit"], "tree": review_export["tree"], "view_prefix": "", "view_tree": review_export["tree"], "required_paths": [], "export_sha256": lib.export_digest(review_export, self.limits)},
            "generated": {"scan_manifest_sha256": lib.sha256_hex(manifest_data), "index_sha256": lib.sha256_hex(index_data), "summary_sha256": lib.sha256_hex(summary_data), "publication_sha256": lib.sha256_hex(publication_data), "independent_audit_sha256": lib.sha256_hex(audit_data), "aggregate_sha256": index["aggregate_sha256"]},
            "non_authority": {"execution": False, "approval": False, "custody": False, "replay_admission": False, "semantic_acceptance": False, "merge_permission": False, "release": False, "cutover": False, "next_phase": False},
        }
        record_path = built["case"] / "record.json"
        self.write_json(record_path, record)
        arguments = (
            record_path, built["package"], built["source"], source_export_path,
            roots["base"][0], roots["base"][1], roots["contract"][0], roots["contract"][1],
            roots["tooling"][0], roots["tooling"][1], observations, observation_export_path,
            reviews, review_export_path, built["inputs"], input_export_path,
            built["audit_path"], expected_tooling, self.limits,
        )
        original_read = verify.lib.read_bounded_file
        audit_reads = 0

        def one_audit_read(path: Path, maximum: int) -> bytes:
            nonlocal audit_reads
            if path == built["audit_path"]:
                audit_reads += 1
                if audit_reads > 1:
                    raise AssertionError("evidence binding reopened the audit path")
            return original_read(path, maximum)

        with mock.patch.object(verify.lib, "read_bounded_file", side_effect=one_audit_read):
            verify.verify_evidence_binding(*arguments)
        self.assertEqual(1, audit_reads)
        wrong_tooling = list(arguments)
        wrong_tooling[17] = {**expected_tooling, "commit": "f" * 40}
        with self.assertRaises(verify.lib.ProtocolError) as caught:
            verify.verify_evidence_binding(*wrong_tooling)
        self.assertEqual("E_EXPECTED_TOOLING", caught.exception.code)
        (built["source"] / "notes.txt").write_text("stale", encoding="utf-8")
        self.assert_code("E_EXPORT_CONTENT", verify.verify_evidence_binding, *arguments)

    def test_authenticated_cedp_ancestry_trees_targets_and_recovery(self) -> None:
        source_base_data = b"source base\n"
        source_head_data = b"source candidate\n"
        source_base_entries = [self.tree_entry("README.md", source_base_data)]
        source_head_entries = [
            *source_base_entries, self.tree_entry("src/candidate.bow", source_head_data),
        ]
        source_base = self.commit_evidence(
            "fixture/source", "staging", source_base_entries, [], "source base"
        )
        source_head = self.commit_evidence(
            "fixture/source", "candidate", source_head_entries,
            [source_base["commit"]], "source candidate",
        )

        ledger_base_data = b"ledger base\n"
        evidence_data = b'{"index":"bound"}\n'
        package_prefix = f"evidence/m0.1/{source_head['commit']}"
        index_reference = self.bound_record(package_prefix + "/generated/index.json", evidence_data)
        ledger_base_entries = [self.tree_entry("README.md", ledger_base_data)]
        evidence_entries = [
            *ledger_base_entries,
            self.tree_entry(index_reference["path"], evidence_data),
        ]
        ledger_base = self.commit_evidence(
            "fixture/ledger", "main", ledger_base_entries, [], "ledger base"
        )
        evidence_head = self.commit_evidence(
            "fixture/ledger", "evidence", evidence_entries,
            [ledger_base["commit"]], "evidence",
        )

        review_body = {
            "record_class": "independent_review", "protocol_version": "m0.1-v2",
            "phase": "M0.1", "reviewer": "Sarah",
            "source_candidate_commit": source_head["commit"],
            "source_candidate_tree": source_head["tree"],
            "evidence_commit": evidence_head["commit"],
            "evidence_tree": evidence_head["tree"],
            "disposition": "ready_for_owner_decision",
            "non_authority": {"owner_acceptance": False, "merge_permission": False},
        }
        review_data = lib.canonical_json_bytes(review_body, self.limits)
        review_reference = self.bound_record("decisions/review.json", review_data)
        review_entries = [
            *evidence_entries,
            self.tree_entry(review_reference["path"], review_data),
        ]
        review = self.commit_evidence(
            "fixture/ledger", "decisions", review_entries,
            [evidence_head["commit"]], "review",
        )

        owner_body = {
            "record_class": "owner_decision", "protocol_version": "m0.1-v2",
            "phase": "M0.1", "owner": "Greg Krsak",
            "source_candidate_commit": source_head["commit"],
            "source_candidate_tree": source_head["tree"],
            "evidence_commit": evidence_head["commit"],
            "evidence_tree": evidence_head["tree"],
            "review_commit": review["commit"],
            "review_record_blob": review_reference["blob_sha1"],
            "disposition": "accepted_for_integration", "merge_authorized": True,
        }
        owner_data = lib.canonical_json_bytes(owner_body, self.limits)
        owner_reference = self.bound_record("decisions/owner.json", owner_data)
        owner_entries = [
            *review_entries, self.tree_entry(owner_reference["path"], owner_data),
        ]
        owner = self.commit_evidence(
            "fixture/ledger", "decisions", owner_entries,
            [review["commit"]], "owner",
        )
        source_merge = self.commit_evidence(
            "fixture/source", "staging", source_head_entries,
            [source_base["commit"], source_head["commit"]], "merge source",
        )
        ledger_merge = self.commit_evidence(
            "fixture/ledger", "main", owner_entries,
            [ledger_base["commit"], owner["commit"]], "merge ledger",
        )

        bundle = self.workspace / "recovery-bundle"
        (bundle / "objects").mkdir(parents=True)
        object_map: dict[str, tuple[str, bytes]] = {}
        for data in (ledger_base_data, evidence_data):
            object_map[lib.git_object_sha1("blob", data)] = ("blob", data)
        for commit in (ledger_base, evidence_head):
            raw = base64.b64decode(commit["commit_object_base64"], validate=True)
            object_map[commit["commit"]] = ("commit", raw)
            _tree, trees = lib.git_tree_objects(
                commit["tree_entries"], self.limits, allow_archive=True
            )
            object_map.update({identity: ("tree", data) for identity, data in trees.items()})
        descriptors = []
        for identity, (kind, data) in sorted(object_map.items()):
            relative = f"objects/{identity}"
            (bundle / relative).write_bytes(data)
            descriptors.append({
                "sha1": identity, "kind": kind, "path": relative,
                "sha256": lib.sha256_hex(data), "byte_count": len(data),
            })
        recovery_manifest = {
            "record_class": "git_recovery_bundle", "protocol_version": "m0.1-v2",
            "repository": "fixture/ledger",
            "refs": [{"name": "refs/heads/main", "commit": evidence_head["commit"]}],
            "objects": descriptors,
        }
        manifest_data = lib.canonical_json_bytes(recovery_manifest, self.limits)
        (bundle / "manifest.json").write_bytes(manifest_data)
        backup_sha256 = lib.sha256_hex(manifest_data)

        recovery_body = {
            "record_class": "recovery_evidence", "protocol_version": "m0.1-v2",
            "repository": "fixture/ledger", "backup_sha256": backup_sha256,
            "retained_refs": ["refs/heads/main"],
            "tested_at": "2026-10-24T12:00:00Z",
            "restored_commit": evidence_head["commit"],
            "restored_tree": evidence_head["tree"], "disposition": "succeeded",
            "non_authority": {
                "acceptance": False, "merge_permission": False, "next_phase": False,
            },
        }
        recovery_data = lib.canonical_json_bytes(recovery_body, self.limits)
        recovery_reference = self.bound_record("decisions/recovery.json", recovery_data)
        recovery_entries = [
            *owner_entries,
            self.tree_entry(recovery_reference["path"], recovery_data),
        ]
        recovery_commit = self.commit_evidence(
            "fixture/ledger", "main", recovery_entries,
            [ledger_merge["commit"]], "recovery evidence",
        )
        record = {
            "record_class": "integration_binding", "protocol_version": "m0.1-v2", "phase": "M0.1", "sequence": ["C", "E", "D", "P"],
            "C": {"base": source_base, "introduced_commits": [source_head], "reviewed": source_head},
            "E": {"base": ledger_base, "introduced_commits": [evidence_head], "reviewed": evidence_head, "source_candidate_commit": source_head["commit"], "source_candidate_tree": source_head["tree"], "index_sha256": lib.sha256_hex(evidence_data), "index_record": index_reference},
            "D": {"review": review, "owner_decision": owner, "source_candidate_commit": source_head["commit"], "evidence_commit": evidence_head["commit"], "review_record": review_reference, "owner_decision_record": owner_reference},
            "P": {"source_merge": source_merge, "ledger_merge": ledger_merge, "source_head": source_head["commit"], "ledger_head": owner["commit"]},
            "recovery": {"repository": "fixture/ledger", "backup_sha256": backup_sha256, "retained_refs": ["refs/heads/main"], "tested_at": "2026-10-24T12:00:00Z", "restored_commit": evidence_head["commit"], "restored_tree": evidence_head["tree"], "recovery_commit": recovery_commit, "recovery_record": recovery_reference},
        }
        expected = {
            "source_repository": "fixture/source", "source_target_branch": "staging",
            "source_merge_commit": source_merge["commit"],
            "ledger_repository": "fixture/ledger", "ledger_target_branch": "main",
            "ledger_merge_commit": ledger_merge["commit"],
            "recovery_ref": "refs/heads/main",
            "source_change_paths": ["src/candidate.bow"],
        }
        path = self.workspace / "binding.json"
        self.write_json(path, record)
        verify.verify_binding_record(path, bundle, expected, self.limits)

        wrong_index = copy.deepcopy(record)
        wrong_index["E"]["index_sha256"] = "7" * 64
        self.write_json(path, wrong_index)
        self.assert_code("E_BINDING_CONTENT", verify.verify_binding_record,
                         path, bundle, expected, self.limits)

        # Rehash each numeric-Boolean body and its containing commit so rejection
        # tests semantic type checking, not a stale digest or tree.
        for section, body, reference, parent, field, code in (
            ("review", review_body, review_reference, evidence_head, "owner_acceptance", "E_REVIEW_DECISION"),
            ("owner_decision", owner_body, owner_reference, review, "merge_authorized", "E_OWNER_DECISION"),
            ("recovery", recovery_body, recovery_reference, ledger_merge, "acceptance", "E_RECOVERY_RECORD"),
        ):
            with self.subTest(numeric_boolean=section):
                bad_body = copy.deepcopy(body)
                if field == "merge_authorized":
                    bad_body[field] = 1
                else:
                    bad_body["non_authority"][field] = 0
                data = lib.canonical_json_bytes(bad_body, self.limits)
                ref = self.bound_record(reference["path"], data)
                commit = self.commit_evidence("fixture/ledger", "main",
                    [*parent["tree_entries"], self.tree_entry(ref["path"], data)],
                    [parent["commit"]], "numeric Boolean")
                bad = copy.deepcopy(record)
                if section == "recovery":
                    bad["recovery"]["recovery_commit"] = commit
                    bad["recovery"]["recovery_record"] = ref
                else:
                    bad["D"][section] = commit
                    bad["D"][section + "_record"] = ref
                    if section == "review":
                        bad["D"]["owner_decision"] = self.commit_evidence(
                            "fixture/ledger", "decisions", owner_entries,
                            [commit["commit"]], "owner follows numeric review")
                self.write_json(path, bad)
                self.assert_code(code, verify.verify_binding_record,
                                 path, bundle, expected, self.limits)

        changed = copy.deepcopy(record)
        changed["C"]["base"]["branch"] = "prod"
        changed["C"]["reviewed"]["branch"] = "prod"
        changed["C"]["introduced_commits"][0]["branch"] = "prod"
        changed["P"]["source_merge"]["branch"] = "prod"
        self.write_json(path, changed)
        self.assert_code(
            "E_BINDING_TARGET", verify.verify_binding_record,
            path, bundle, expected, self.limits,
        )

        hidden_parent = self.commit_evidence(
            "fixture/source", "candidate", source_head_entries,
            [source_base["commit"], "f" * 40], "hidden merge parent",
        )
        self.assert_code(
            "E_BINDING_ANCESTRY", verify._introduced_chain,
            source_base, hidden_parent, [hidden_parent], "hidden", self.limits,
        )

        missing_object = bundle / descriptors[0]["path"]
        missing_bytes = missing_object.read_bytes()
        missing_object.unlink()
        self.write_json(path, record)
        self.assert_code(
            "E_RECOVERY_BUNDLE", verify.verify_binding_record,
            path, bundle, expected, self.limits,
        )
        missing_object.write_bytes(missing_bytes)

        altered = copy.deepcopy(record)
        altered_owner_body = {**owner_body, "merge_authorized": False}
        altered_owner_data = lib.canonical_json_bytes(altered_owner_body, self.limits)
        altered_owner_reference = self.bound_record(
            "decisions/owner.json", altered_owner_data
        )
        altered_owner_entries = [
            *review_entries,
            self.tree_entry(altered_owner_reference["path"], altered_owner_data),
        ]
        altered_owner = self.commit_evidence(
            "fixture/ledger", "decisions", altered_owner_entries,
            [review["commit"]], "altered owner",
        )
        altered_ledger_merge = self.commit_evidence(
            "fixture/ledger", "main", altered_owner_entries,
            [ledger_base["commit"], altered_owner["commit"]], "altered merge ledger",
        )
        altered_recovery_commit = self.commit_evidence(
            "fixture/ledger", "main", recovery_entries,
            [altered_ledger_merge["commit"]], "altered recovery evidence",
        )
        altered["D"]["owner_decision"] = altered_owner
        altered["D"]["owner_decision_record"] = altered_owner_reference
        altered["P"]["ledger_merge"] = altered_ledger_merge
        altered["P"]["ledger_head"] = altered_owner["commit"]
        altered["recovery"]["recovery_commit"] = altered_recovery_commit
        altered_expected = {
            **expected, "ledger_merge_commit": altered_ledger_merge["commit"],
        }
        self.write_json(path, altered)
        self.assert_code(
            "E_OWNER_DECISION", verify.verify_binding_record,
            path, bundle, altered_expected, self.limits,
        )

    def test_compiler_intermediate_content_and_decision_preservation(self) -> None:
        base = self.commit_evidence("fixture/source", "staging", [], [], "base")
        final_entries = [self.tree_entry("anchor.json", b"approved\n")]
        intermediate = self.commit_evidence("fixture/source", "candidate",
            [self.tree_entry("bulk.jsonl", b"prohibited\n")], [base["commit"]], "bulk")
        final = self.commit_evidence("fixture/source", "candidate", final_entries,
            [intermediate["commit"]], "remove bulk")
        chain = verify._introduced_chain(base, final, [intermediate, final], "C", self.limits)
        self.assert_code("E_BINDING_CONTENT", verify._compiler_content_chain,
                         base, final, chain, ["anchor.json"], self.limits)
        # The allowed path cannot hide a third, transient object either.
        transient = self.commit_evidence("fixture/source", "candidate",
            [self.tree_entry("anchor.json", b"unapproved\n")], [base["commit"]], "third state")
        self.assert_code("E_BINDING_CONTENT", verify._compiler_content_chain,
                         base, final, [transient], ["anchor.json"], self.limits)
        verify._compiler_content_chain(base, final, [final], ["anchor.json"], self.limits)
        self.assert_code("E_BINDING_CONTENT", verify._compiler_content_chain,
                         base, final, [final], [], self.limits)

        prefix = "evidence/m0.1/" + "a" * 40
        protected = self.tree_entry(prefix + "/generated/index.json", b"{}\n")
        parent = {"tree_entries": [protected]}
        data = b'{"review":"synthetic"}\n'
        ref = self.bound_record("decisions/review.json", data)
        addition = self.tree_entry(ref["path"], data)
        verify._record_addition(parent, {"tree_entries": [protected, addition]}, ref, prefix)
        for entries in ([addition], [dict(protected, blob_sha1="f" * 40), addition],
                        [protected, addition, self.tree_entry("extra.txt", b"extra")]):
            self.assert_code("E_BINDING_CONTENT", verify._record_addition,
                             parent, {"tree_entries": entries}, ref, prefix)
        overwritten = self.bound_record(protected["path"], data)
        self.assert_code("E_BINDING_CONTENT", verify._record_addition, parent,
                         {"tree_entries": [self.tree_entry(protected["path"], data)]},
                         overwritten, prefix)

    def test_opaque_symlink_inventory_not_bound_record(self) -> None:
        data = b"{}\n"
        entry = dict(self.tree_entry("record.json", data), mode="120000")
        self.assertEqual([entry], verify._tree_inventory([entry], "opaque", self.limits))
        raw_tree = b"120000 record.json\0" + bytes.fromhex(entry["blob_sha1"])
        self.assertEqual([("blob", entry["blob_sha1"])],
                         verify._git_tree_references(raw_tree, "fixture", self.limits))
        self.assert_code("E_DECISION_RECORD", verify._bound_json_record,
                         self.bound_record("record.json", data),
                         {"tree_entries": [entry]}, "record", self.limits)
        self.assertNotIn("120000", lib.FILE_MODES)

    def test_recovery_wrong_kind_after_prior_visit(self) -> None:
        # B is a real commit object, referenced first as a parent and then as a
        # regular-file blob. No hash collision or broken object digest is used.
        base = self.commit_evidence("fixture/ledger", "main", [], [], "B")
        entries = [{"path": "wrong-kind", "mode": "100644", "blob_sha1": base["commit"]}]
        head = self.commit_evidence("fixture/ledger", "main", entries, [base["commit"]], "E")
        objects = {}
        for commit in (base, head):
            objects[commit["commit"]] = ("commit", base64.b64decode(commit["commit_object_base64"]))
            _, trees = lib.git_tree_objects(commit["tree_entries"], self.limits)
            objects.update({identity: ("tree", data) for identity, data in trees.items()})
        root = self.workspace / "wrong-kind-bundle"
        (root / "objects").mkdir(parents=True)
        descriptors = []
        for identity, (kind, data) in sorted(objects.items()):
            relative = f"objects/{identity}"
            (root / relative).write_bytes(data)
            descriptors.append({"sha1": identity, "kind": kind, "path": relative,
                                "sha256": lib.sha256_hex(data), "byte_count": len(data)})
        manifest = {"record_class": "git_recovery_bundle", "protocol_version": "m0.1-v2",
                    "repository": "fixture/ledger", "refs": [{"name": "refs/heads/main", "commit": head["commit"]}],
                    "objects": descriptors}
        raw = lib.canonical_json_bytes(manifest, self.limits)
        (root / "manifest.json").write_bytes(raw)
        recovery = {"backup_sha256": lib.sha256_hex(raw), "retained_refs": ["refs/heads/main"]}
        self.assert_code("E_RECOVERY_BUNDLE", verify._verify_recovery_bundle,
                         root, recovery, "fixture/ledger", "refs/heads/main", head,
                         [base, head], self.limits)

    def test_mutation_manifest_maps_to_real_tests(self) -> None:
        manifest = json.loads((FIXTURES / "mutations.json").read_text(encoding="utf-8"))
        ids = [item["mutation_id"] for item in manifest["mutations"]]
        self.assertEqual(len(ids), len(set(ids)))
        for item in manifest["mutations"]:
            self.assertTrue(item["expected_code"].startswith("E_"))
            self.assertTrue(callable(getattr(self, item["test_method"])))
        control_ids = [item["control_id"] for item in manifest["controls"]]
        self.assertEqual(len(control_ids), len(set(control_ids)))
        for item in manifest["controls"]:
            self.assertEqual({"control_id", "test_method"}, set(item))
            self.assertTrue(callable(getattr(self, item["test_method"])))


if __name__ == "__main__":
    if not sys.flags.isolated:
        print("E_RUNTIME_ISOLATION: invoke with python3 -I", file=sys.stderr)
        raise SystemExit(2)
    unittest.main(verbosity=2)
