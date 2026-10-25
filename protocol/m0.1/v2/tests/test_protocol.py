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


lib = load_module("_m01v2_test_lib", "protocol_lib.py")
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

    def write_json(self, path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(lib.canonical_json_bytes(value, self.limits))

    def compact_documents(self) -> dict[str, Any]:
        surface = self.fixture["external_surfaces"]["surfaces"][0]
        return {
            "mappings.json": self.fixture["mappings"],
            "classification-rules.json": self.fixture["rules"],
            "audit-policy.json": self.fixture["audit_policy"],
            "surface-register.json": {
                "protocol_version": "m0.1-v2",
                "required_surfaces": [{"surface_id": surface["surface_id"], "class": surface["class"]}],
            },
            "external-surfaces.json": self.fixture["external_surfaces"],
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

    def commit_evidence(self, repository: str, branch: str, tree: str, parents: list[str], message: str) -> dict[str, Any]:
        headers = [f"tree {tree}", *(f"parent {parent}" for parent in parents)]
        raw = ("\n".join(headers) + "\nauthor Fixture <fixture@example.invalid> 0 +0000\ncommitter Fixture <fixture@example.invalid> 0 +0000\n\n" + message + "\n").encode("ascii")
        return {"repository": repository, "branch": branch, "commit": lib.git_object_sha1("commit", raw), "tree": tree, "parents": parents, "commit_object_base64": base64.b64encode(raw).decode("ascii")}

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
        rows = generate.discover([("KED-001-KED-002.json", b'{"KED-001":"KED-002"}\n')], mappings, "fixture/source", "1" * 40, self.limits)
        locators = [lib.canonical_json_bytes(row["locator"], self.limits, trailing_lf=False) for row in rows]
        self.assertEqual(len(locators), len(set(locators)))
        self.assertNotIn(b"match_index", b"".join(locators))

    def test_independent_auditor_reconciles_exact_keys(self) -> None:
        self.verify_valid(self.build_valid("independent"))

    def test_equal_count_different_key(self) -> None:
        built = self.build_valid("different-key")
        audit = verify.canonical_document(built["audit_path"], self.limits)
        audit["candidates"][0]["locator"][next(key for key in audit["candidates"][0]["locator"] if key.endswith("start"))] += 1
        candidate = audit["candidates"][0]
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
        limits = dict(self.limits)
        limits["max_processing_steps"] = 1
        self.assert_code("E_PROCESSING_STEPS", generate.discover, [("x.txt", b"Klyxr Klyxr")], generate.validate_mappings(self.fixture["mappings"], self.limits), "fixture/source", "1" * 40, limits)

    def test_direct_compact_input_field_validation(self) -> None:
        files = {name: lib.canonical_json_bytes(value, self.limits) for name, value in self.compact_documents().items()}
        verify.validate_compact_input_files(files, self.limits)
        changed = dict(files)
        bad = copy.deepcopy(self.fixture["external_surfaces"])
        bad["surfaces"][0]["unknown"] = True
        changed["external-surfaces.json"] = lib.canonical_json_bytes(bad, self.limits)
        self.assert_code("E_FIELD_UNKNOWN", verify.validate_compact_input_files, changed, self.limits)

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

    def test_manifest_binary_and_malformed_require_disposition(self) -> None:
        manifest = lib.scan_manifest([("binary.bin", b"\xff"), ("bad.json", b'{"x":')], self.limits)
        self.assertEqual("non_utf8", manifest[0]["text_status"])
        self.assertEqual("invalid_json", manifest[1]["structured_status"])

    def test_evidence_record_binds_actual_exports_and_generated_bytes(self) -> None:
        built = self.build_valid("evidence")
        source_export_path, source_export = self.make_export(built["source"], "fixture/source", False)
        input_export_path, input_export = self.make_export(built["inputs"], "fixture/inputs", False)
        roots: dict[str, tuple[Path, Path, dict[str, Any]]] = {}
        for name, repository, files in (
            ("base", "fixture/source", {"README.md": b"accepted base\n"}),
            ("contract", "fixture/source", {"contract.md": b"contract\n"}),
            ("tooling", "fixture/ledger", {"tool.py": b"# reviewed tool\n"}),
        ):
            root = built["case"] / name
            root.mkdir()
            for relative, data in files.items():
                (root / relative).write_bytes(data)
            export_path, export = self.make_export(root, repository, False)
            roots[name] = (root, export_path, export)
        index_data = (built["package"] / "index.json").read_bytes()
        summary_data = (built["package"] / "summary.json").read_bytes()
        manifest_data = (built["package"] / "scan-manifest.json").read_bytes()
        publication_data = (built["package"] / "publication.json").read_bytes()
        index = lib.strict_json_bytes(index_data, self.limits, "index")
        input_entries = {entry["path"]: entry for entry in input_export["entries"]}
        descriptor = [input_entries[path] for path in sorted(verify.PRODUCTION_INPUT_PATHS)]
        contract_entry = roots["contract"][2]["entries"][0]
        record = {
            "record_class": "migration_evidence", "protocol_version": "m0.1-v2", "phase": "M0.1",
            "source": {"repository": "fixture/source", "commit": source_export["commit"], "tree": source_export["tree"], "view_prefix": "", "view_tree": source_export["tree"], "export_sha256": lib.export_digest(source_export, self.limits)},
            "accepted_base": {"repository": "fixture/source", "commit": roots["base"][2]["commit"], "tree": roots["base"][2]["tree"], "view_prefix": "", "view_tree": roots["base"][2]["tree"], "export_sha256": lib.export_digest(roots["base"][2], self.limits)},
            "governing_contract": {"repository": "fixture/source", "commit": roots["contract"][2]["commit"], "tree": roots["contract"][2]["tree"], "view_prefix": "", "view_tree": roots["contract"][2]["tree"], "path": "contract.md", "blob": contract_entry["blob_sha1"], "export_sha256": lib.export_digest(roots["contract"][2], self.limits)},
            "tooling": {"repository": "fixture/ledger", "commit": roots["tooling"][2]["commit"], "tree": roots["tooling"][2]["tree"], "view_prefix": "", "view_tree": roots["tooling"][2]["tree"], "required_paths": ["tool.py"], "export_sha256": lib.export_digest(roots["tooling"][2], self.limits)},
            "inputs": {"repository": "fixture/inputs", "commit": input_export["commit"], "tree": input_export["tree"], "view_prefix": "", "view_tree": input_export["tree"], "required_paths": sorted(verify.PRODUCTION_INPUT_PATHS), "export_sha256": lib.export_digest(input_export, self.limits), "aggregate_sha256": lib.sha256_hex(lib.canonical_json_bytes(descriptor, self.limits, trailing_lf=False))},
            "generated": {"scan_manifest_sha256": lib.sha256_hex(manifest_data), "index_sha256": lib.sha256_hex(index_data), "summary_sha256": lib.sha256_hex(summary_data), "publication_sha256": lib.sha256_hex(publication_data), "aggregate_sha256": index["aggregate_sha256"]},
            "non_authority": {"execution": False, "approval": False, "custody": False, "replay_admission": False, "semantic_acceptance": False, "merge_permission": False, "release": False, "cutover": False, "next_phase": False},
        }
        record_path = built["case"] / "record.json"
        self.write_json(record_path, record)
        verify.verify_evidence_binding(record_path, built["package"], built["source"], source_export_path, roots["base"][0], roots["base"][1], roots["contract"][0], roots["contract"][1], roots["tooling"][0], roots["tooling"][1], built["inputs"], input_export_path, self.limits)
        (built["source"] / "notes.txt").write_text("stale", encoding="utf-8")
        self.assert_code("E_EXPORT_CONTENT", verify.verify_evidence_binding, record_path, built["package"], built["source"], source_export_path, roots["base"][0], roots["base"][1], roots["contract"][0], roots["contract"][1], roots["tooling"][0], roots["tooling"][1], built["inputs"], input_export_path, self.limits)

    def test_authenticated_cedp_ancestry_trees_targets_and_recovery(self) -> None:
        source_base = self.commit_evidence("fixture/source", "staging", "1" * 40, [], "source base")
        source_head = self.commit_evidence("fixture/source", "staging", "2" * 40, [source_base["commit"]], "source candidate")
        ledger_base = self.commit_evidence("fixture/ledger", "main", "3" * 40, [], "ledger base")
        evidence_head = self.commit_evidence("fixture/ledger", "main", "4" * 40, [ledger_base["commit"]], "evidence")
        review = self.commit_evidence("fixture/ledger", "main", "5" * 40, [evidence_head["commit"]], "review")
        owner = self.commit_evidence("fixture/ledger", "main", "6" * 40, [review["commit"]], "owner")
        source_merge = self.commit_evidence("fixture/source", "staging", source_head["tree"], [source_base["commit"], source_head["commit"]], "merge source")
        ledger_merge = self.commit_evidence("fixture/ledger", "main", owner["tree"], [ledger_base["commit"], owner["commit"]], "merge ledger")
        record = {
            "record_class": "integration_binding", "protocol_version": "m0.1-v2", "phase": "M0.1", "sequence": ["C", "E", "D", "P"],
            "C": {"base": source_base, "introduced_commits": [source_head], "reviewed": source_head},
            "E": {"base": ledger_base, "introduced_commits": [evidence_head], "reviewed": evidence_head, "source_candidate_commit": source_head["commit"], "source_candidate_tree": source_head["tree"], "index_sha256": "7" * 64},
            "D": {"review": review, "owner_decision": owner, "source_candidate_commit": source_head["commit"], "evidence_commit": evidence_head["commit"], "review_record_blob": "8" * 40, "owner_decision_blob": "9" * 40},
            "P": {"source_merge": source_merge, "ledger_merge": ledger_merge, "source_head": source_head["commit"], "ledger_head": owner["commit"]},
            "recovery": {"repository": "fixture/ledger", "backup_sha256": "a" * 64, "retained_refs": ["refs/heads/main"], "tested_at": "2026-10-24T12:00:00Z", "restored_commit": evidence_head["commit"], "restored_tree": evidence_head["tree"], "restored_commit_object_base64": evidence_head["commit_object_base64"], "recovery_evidence_blob": "b" * 40},
        }
        path = self.workspace / "binding.json"
        self.write_json(path, record)
        verify.verify_binding_record(path, self.limits)
        changed = copy.deepcopy(record)
        changed["P"]["source_merge"]["branch"] = "prod"
        self.write_json(path, changed)
        self.assert_code("E_BINDING_TARGET", verify.verify_binding_record, path, self.limits)

    def test_mutation_manifest_maps_to_real_tests(self) -> None:
        manifest = json.loads((FIXTURES / "mutations.json").read_text(encoding="utf-8"))
        ids = [item["mutation_id"] for item in manifest["mutations"]]
        self.assertEqual(len(ids), len(set(ids)))
        for item in manifest["mutations"]:
            self.assertTrue(item["expected_code"].startswith("E_"))
            self.assertTrue(callable(getattr(self, item["test_method"])))


if __name__ == "__main__":
    if not sys.flags.isolated:
        print("E_RUNTIME_ISOLATION: invoke with python3 -I", file=sys.stderr)
        raise SystemExit(2)
    unittest.main(verbosity=2)
