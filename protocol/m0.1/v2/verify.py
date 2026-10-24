#!/usr/bin/env python3
"""Verify M0.1 v2 packages, audit reconciliation, records, and freshness."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _load_library() -> Any:
    path = Path(__file__).resolve().with_name("protocol_lib.py")
    spec = importlib.util.spec_from_file_location("_bowfin_m01v2_protocol_lib", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load reviewed protocol_lib.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


lib = _load_library()


def canonical_document(path: Path, limits: dict[str, int]) -> Any:
    data = lib.read_bounded_file(path, limits["max_input_file_bytes"])
    value = lib.strict_json_bytes(data, limits, str(path))
    if data != lib.canonical_json_bytes(value, limits):
        lib.fail("E_CANONICAL_JSON", f"noncanonical JSON document: {path}")
    return value


def validate_occurrence(row: Any, limits: dict[str, int]) -> dict[str, Any]:
    required = {
        "protocol_version", "occurrence_key", "path", "unit_kind", "locator",
        "source_file_sha256", "original", "canonical", "namespace", "role", "phase",
        "producer", "consumer", "support_policy", "validation_test_id",
        "historical_relationship", "mapping_id", "rule_id", "context",
    }
    if not isinstance(row, dict):
        lib.fail("E_ROW_TYPE", "occurrence row must be an object")
    lib.require_keys(row, required, set(), "occurrence")
    if row["protocol_version"] != lib.PROTOCOL_VERSION:
        lib.fail("E_PROTOCOL_VERSION", "occurrence has wrong protocol version")
    if row["unit_kind"] not in lib.UNIT_KINDS or row["role"] not in lib.ROLES:
        lib.fail("E_ROW_ENUM", "occurrence has unknown unit kind or role")
    lib.validate_relpath(row["path"], limits)
    if not isinstance(row["locator"], dict) or not row["locator"]:
        lib.fail("E_ROW_LOCATOR", "occurrence locator must be a nonempty object")
    for field in ("source_file_sha256",):
        value = row[field]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            lib.fail("E_ROW_DIGEST", f"invalid {field}")
    return row


def verify_package(
    package: Path,
    source_repository: str,
    source_tree: str,
    limits: dict[str, int],
) -> list[dict[str, Any]]:
    if package.is_symlink() or not package.is_dir():
        lib.fail("E_PACKAGE", "package must be a non-symlink directory")
    index = canonical_document(package / "index.json", limits)
    required_index = {
        "protocol_version", "aggregate_sha256", "scan_manifest_sha256",
        "total_rows", "total_bytes", "chunks",
    }
    if not isinstance(index, dict):
        lib.fail("E_INDEX", "index must be an object")
    lib.require_keys(index, required_index, set(), "index")
    if index["protocol_version"] != lib.PROTOCOL_VERSION or not isinstance(index["chunks"], list):
        lib.fail("E_INDEX", "invalid index version or chunks")
    if len(index["chunks"]) > limits["max_chunks"]:
        lib.fail("E_CHUNK_COUNT", "max_chunks exceeded")

    occurrence_dir = package / "occurrences"
    actual_names: list[str] = []
    if occurrence_dir.exists():
        if occurrence_dir.is_symlink() or not occurrence_dir.is_dir():
            lib.fail("E_CHUNK_DIR", "occurrences must be a non-symlink directory")
        actual_names = sorted(item.name for item in occurrence_dir.iterdir())
        for item in occurrence_dir.iterdir():
            if item.is_symlink() or not item.is_file():
                lib.fail("E_CHUNK_FILE", f"invalid chunk entry: {item}")

    expected_names = [f"{number:04d}.jsonl" for number in range(len(index["chunks"]))]
    if actual_names != expected_names:
        lib.fail("E_CHUNK_SET", f"chunk set mismatch: expected {expected_names}, found {actual_names}")

    descriptors: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    previous_key: str | None = None
    total_generated = 0
    for number, claimed in enumerate(index["chunks"]):
        if not isinstance(claimed, dict):
            lib.fail("E_CHUNK_DESCRIPTOR", "chunk descriptor must be an object")
        expected_path = f"occurrences/{number:04d}.jsonl"
        if claimed.get("path") != expected_path:
            lib.fail("E_CHUNK_NAME", f"expected {expected_path}")
        chunk_path = package / expected_path
        data = lib.read_bounded_file(chunk_path, limits["max_chunk_bytes"])
        total_generated += len(data)
        if not data or not data.endswith(b"\n"):
            lib.fail("E_CHUNK_NEWLINE", f"chunk is empty or lacks final LF: {expected_path}")
        chunk_rows: list[dict[str, Any]] = []
        for row_number, line in enumerate(data.splitlines(keepends=True)):
            if len(line) > limits["max_row_bytes"]:
                lib.fail("E_ROW_SIZE", f"oversized row {expected_path}:{row_number + 1}")
            row = validate_occurrence(lib.strict_json_bytes(line, limits, expected_path), limits)
            if line != lib.canonical_json_bytes(row, limits):
                lib.fail("E_ROW_CANONICAL", f"noncanonical row {expected_path}:{row_number + 1}")
            recomputed = lib.occurrence_key(
                source_repository,
                source_tree,
                row["path"],
                row["unit_kind"],
                row["locator"],
                row["namespace"],
                row["original"],
                limits,
            )
            if row["occurrence_key"] != recomputed:
                lib.fail("E_OCCURRENCE_KEY", f"key mismatch at {expected_path}:{row_number + 1}")
            key = row["occurrence_key"]
            if previous_key is not None and key <= previous_key:
                lib.fail("E_ROW_ORDER", f"non-increasing occurrence key at {expected_path}:{row_number + 1}")
            previous_key = key
            chunk_rows.append(row)
            rows.append(row)
        if not chunk_rows or len(chunk_rows) > limits["max_rows_per_chunk"]:
            lib.fail("E_CHUNK_ROWS", f"invalid row count in {expected_path}")
        descriptor = {
            "path": expected_path,
            "sha256": lib.sha256_hex(data),
            "byte_count": len(data),
            "row_count": len(chunk_rows),
            "first_key": chunk_rows[0]["occurrence_key"],
            "last_key": chunk_rows[-1]["occurrence_key"],
        }
        if claimed != descriptor:
            lib.fail("E_CHUNK_DESCRIPTOR", f"descriptor mismatch for {expected_path}")
        descriptors.append(descriptor)

    if len(rows) > limits["max_occurrences"]:
        lib.fail("E_OCCURRENCE_COUNT", "max_occurrences exceeded")
    manifest_document = canonical_document(package / "scan-manifest.json", limits)
    if not isinstance(manifest_document, dict):
        lib.fail("E_SCAN_MANIFEST", "scan manifest must be an object")
    lib.require_keys(manifest_document, {"protocol_version", "files"}, set(), "scan-manifest")
    if manifest_document["protocol_version"] != lib.PROTOCOL_VERSION or not isinstance(manifest_document["files"], list):
        lib.fail("E_SCAN_MANIFEST", "invalid scan manifest version or files")
    if len(manifest_document["files"]) > limits["max_source_files"]:
        lib.fail("E_SCAN_MANIFEST", "scan manifest exceeds max_source_files")
    previous_path: str | None = None
    manifest_by_path: dict[str, dict[str, Any]] = {}
    source_bytes = 0
    for record in manifest_document["files"]:
        required = {
            "path", "sha256", "byte_count", "text_status",
            "structured_status", "structured_error",
        }
        if not isinstance(record, dict):
            lib.fail("E_SCAN_MANIFEST", "scan manifest file record must be an object")
        lib.require_keys(record, required, set(), "scan-manifest-file")
        lib.validate_relpath(record["path"], limits)
        if previous_path is not None and record["path"].encode("utf-8") <= previous_path.encode("utf-8"):
            lib.fail("E_SCAN_MANIFEST_ORDER", "scan manifest paths are not strictly increasing")
        previous_path = record["path"]
        digest = record["sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            lib.fail("E_SCAN_MANIFEST", "invalid source file digest")
        if not isinstance(record["byte_count"], int) or isinstance(record["byte_count"], bool) or record["byte_count"] < 0:
            lib.fail("E_SCAN_MANIFEST", "invalid source file byte count")
        source_bytes += record["byte_count"]
        if source_bytes > limits["max_total_source_bytes"]:
            lib.fail("E_SCAN_MANIFEST", "scan manifest exceeds max_total_source_bytes")
        if record["text_status"] not in {"utf8", "non_utf8"}:
            lib.fail("E_SCAN_MANIFEST", "invalid text status")
        if record["structured_status"] not in {
            "not_json", "valid_json", "invalid_json", "unavailable_non_utf8",
        }:
            lib.fail("E_SCAN_MANIFEST", "invalid structured status")
        if record["path"].endswith(".json"):
            expected_statuses = (
                {"valid_json", "invalid_json"}
                if record["text_status"] == "utf8"
                else {"unavailable_non_utf8"}
            )
        else:
            expected_statuses = {"not_json"}
        if record["structured_status"] not in expected_statuses:
            lib.fail("E_SCAN_MANIFEST", "structured status conflicts with path or encoding")
        error = record["structured_error"]
        if record["structured_status"] == "invalid_json":
            if not isinstance(error, str) or not error:
                lib.fail("E_SCAN_MANIFEST", "invalid JSON status requires an error code")
        elif error is not None:
            lib.fail("E_SCAN_MANIFEST", "invalid structured error")
        manifest_by_path[record["path"]] = record
    for row in rows:
        source = manifest_by_path.get(row["path"])
        if source is None or row["source_file_sha256"] != source["sha256"]:
            lib.fail("E_SOURCE_BINDING", f"occurrence is not bound to manifest bytes: {row['occurrence_key']}")
    manifest_sha256 = lib.sha256_hex(
        lib.canonical_json_bytes(manifest_document, limits)
    )
    expected_index = {
        "protocol_version": lib.PROTOCOL_VERSION,
        "aggregate_sha256": lib.aggregate_digest(descriptors),
        "scan_manifest_sha256": manifest_sha256,
        "total_rows": len(rows),
        "total_bytes": sum(item["byte_count"] for item in descriptors),
        "chunks": descriptors,
    }
    if index != expected_index:
        lib.fail("E_INDEX", "index totals or aggregate digest mismatch")

    summary = canonical_document(package / "summary.json", limits)
    if summary != lib.summary_for(rows):
        lib.fail("E_SUMMARY", "summary does not match occurrence rows")
    total_generated += (
        (package / "index.json").stat().st_size
        + (package / "summary.json").stat().st_size
        + (package / "scan-manifest.json").stat().st_size
    )
    if total_generated > limits["max_generated_bytes"]:
        lib.fail("E_GENERATED_SIZE", "max_generated_bytes exceeded")
    expected_root_names = {"occurrences", "index.json", "summary.json", "scan-manifest.json"}
    actual_root_names = {item.name for item in package.iterdir()}
    if actual_root_names != expected_root_names:
        lib.fail("E_PACKAGE_FILES", f"unexpected package entries: {sorted(actual_root_names ^ expected_root_names)}")
    return rows


def reconcile(
    rows: list[dict[str, Any]],
    audit_path: Path,
    limits: dict[str, int],
    expected_scan_manifest_sha256: str | None = None,
    expected_source_repository: str | None = None,
    expected_source_tree: str | None = None,
) -> None:
    audit = canonical_document(audit_path, limits)
    required = {
        "protocol_version", "source_repository", "source_tree",
        "scan_manifest_sha256", "scan_manifest", "candidate_count", "candidates",
    }
    if not isinstance(audit, dict):
        lib.fail("E_AUDIT_DOCUMENT", "audit result must be an object")
    lib.require_keys(audit, required, set(), "audit-result")
    if audit["protocol_version"] != lib.PROTOCOL_VERSION or not isinstance(audit["candidates"], list):
        lib.fail("E_AUDIT_DOCUMENT", "invalid audit result")
    if expected_source_repository is not None and audit["source_repository"] != expected_source_repository:
        lib.fail("E_AUDIT_SOURCE", "audit source repository mismatch")
    if expected_source_tree is not None and audit["source_tree"] != expected_source_tree:
        lib.fail("E_AUDIT_SOURCE", "audit source tree mismatch")
    if not isinstance(audit["scan_manifest"], list):
        lib.fail("E_AUDIT_DOCUMENT", "audit scan manifest must be an array")
    recomputed_manifest_sha256 = lib.scan_manifest_digest(audit["scan_manifest"], limits)
    if audit["scan_manifest_sha256"] != recomputed_manifest_sha256:
        lib.fail("E_AUDIT_MANIFEST", "audit scan manifest digest mismatch")
    if expected_scan_manifest_sha256 is not None and audit["scan_manifest_sha256"] != expected_scan_manifest_sha256:
        lib.fail("E_AUDIT_MANIFEST", "generator and auditor scanned different source snapshots")
    generated_keys = {row["occurrence_key"] for row in rows}
    audit_keys: list[str] = []
    for candidate in audit["candidates"]:
        required_candidate = {
            "occurrence_key", "path", "unit_kind", "locator", "namespace",
            "original", "family_id",
        }
        if not isinstance(candidate, dict):
            lib.fail("E_AUDIT_CANDIDATE", "invalid audit candidate")
        lib.require_keys(candidate, required_candidate, set(), "audit-candidate")
        lib.validate_relpath(candidate["path"], limits)
        recomputed = lib.occurrence_key(
            audit["source_repository"], audit["source_tree"], candidate["path"],
            candidate["unit_kind"], candidate["locator"], candidate["namespace"],
            candidate["original"], limits,
        )
        if candidate["occurrence_key"] != recomputed:
            lib.fail("E_AUDIT_KEY", "audit candidate key does not match its identity")
        audit_keys.append(candidate["occurrence_key"])
    if len(audit_keys) != len(set(audit_keys)) or audit["candidate_count"] != len(audit_keys):
        lib.fail("E_AUDIT_DUPLICATE", "audit result contains duplicate or miscounted keys")
    audit_set = set(audit_keys)
    if generated_keys != audit_set:
        missing = sorted(audit_set - generated_keys)[:20]
        extra = sorted(generated_keys - audit_set)[:20]
        lib.fail("E_KEY_SET_MISMATCH", f"missing={missing} extra={extra}")


def verify_evidence_record(path: Path, limits: dict[str, int]) -> None:
    record = canonical_document(path, limits)
    required = {
        "record_class", "protocol_version", "phase", "source_repository", "source_commit",
        "source_tree", "accepted_base_commit", "accepted_base_tree", "governing_contract",
        "tooling", "inputs", "external_snapshots", "generated", "non_authority",
    }
    if not isinstance(record, dict):
        lib.fail("E_RECORD", "record must be an object")
    lib.require_keys(record, required, set(), "record")
    if record["record_class"] != "migration_evidence" or record["protocol_version"] != lib.PROTOCOL_VERSION or record["phase"] != "M0.1":
        lib.fail("E_RECORD_CLASS", "record class, phase, or version is invalid")
    if not isinstance(record["source_repository"], str) or not record["source_repository"]:
        lib.fail("E_RECORD_IDENTITY", "source_repository must be nonempty")
    for field in ("source_commit", "source_tree", "accepted_base_commit", "accepted_base_tree"):
        value = record[field]
        if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
            lib.fail("E_RECORD_IDENTITY", f"invalid {field}")
    contract_required = {"repository", "commit", "tree", "path", "blob"}
    tooling_required = {"repository", "commit", "tree", "paths", "blobs"}
    inputs_required = {"repository", "commit", "tree", "paths", "blobs", "aggregate_sha256"}
    generated_required = {
        "scan_manifest_sha256", "index_sha256", "summary_sha256", "aggregate_sha256",
    }
    for field, keys in (
        ("governing_contract", contract_required),
        ("tooling", tooling_required),
        ("inputs", inputs_required),
        ("generated", generated_required),
    ):
        value = record[field]
        if not isinstance(value, dict) or set(value) != keys:
            lib.fail("E_RECORD_FIELD", f"{field} must contain exactly {sorted(keys)}")
    contract = record["governing_contract"]
    tooling = record["tooling"]
    inputs = record["inputs"]
    for label, value in (
        ("governing_contract.commit", contract["commit"]),
        ("governing_contract.tree", contract["tree"]),
        ("governing_contract.blob", contract["blob"]),
        ("tooling.commit", tooling["commit"]),
        ("tooling.tree", tooling["tree"]),
        ("inputs.commit", inputs["commit"]),
        ("inputs.tree", inputs["tree"]),
    ):
        require_sha1(value, label)
    for label, section in (("tooling", tooling), ("inputs", inputs)):
        if not isinstance(section["repository"], str) or not section["repository"]:
            lib.fail("E_RECORD_IDENTITY", f"{label}.repository must be nonempty")
        if not isinstance(section["paths"], list) or not section["paths"]:
            lib.fail("E_RECORD_FIELD", f"{label}.paths must be nonempty")
        if not isinstance(section["blobs"], dict) or set(section["blobs"]) != set(section["paths"]):
            lib.fail("E_RECORD_FIELD", f"{label}.blobs must bind every path exactly")
        for item in section["paths"]:
            lib.validate_relpath(item, limits)
            require_sha1(section["blobs"][item], f"{label}.blobs[{item}]")
    if not isinstance(contract["repository"], str) or not contract["repository"]:
        lib.fail("E_RECORD_IDENTITY", "governing_contract.repository must be nonempty")
    lib.validate_relpath(contract["path"], limits)
    for label, digest in (
        ("inputs.aggregate_sha256", inputs["aggregate_sha256"]),
        *((f"generated.{name}", value) for name, value in record["generated"].items()),
    ):
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            lib.fail("E_RECORD_DIGEST", f"invalid {label}")
    if not isinstance(record["external_snapshots"], list):
        lib.fail("E_RECORD_FIELD", "external_snapshots must be an array")
    external_required = {"surface_id", "repository", "commit", "tree", "path", "blob", "sha256"}
    external_ids: set[str] = set()
    for snapshot in record["external_snapshots"]:
        if not isinstance(snapshot, dict):
            lib.fail("E_RECORD_FIELD", "external snapshot must be an object")
        lib.require_keys(snapshot, external_required, set(), "external-snapshot")
        if not isinstance(snapshot["surface_id"], str) or not snapshot["surface_id"] or snapshot["surface_id"] in external_ids:
            lib.fail("E_RECORD_FIELD", "external surface identifiers must be nonempty and unique")
        external_ids.add(snapshot["surface_id"])
        if not isinstance(snapshot["repository"], str) or not snapshot["repository"]:
            lib.fail("E_RECORD_IDENTITY", "external snapshot repository must be nonempty")
        for field in ("commit", "tree", "blob"):
            require_sha1(snapshot[field], f"external_snapshot.{field}")
        lib.validate_relpath(snapshot["path"], limits)
        digest = snapshot["sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            lib.fail("E_RECORD_DIGEST", "invalid external snapshot sha256")
    non_authority = record["non_authority"]
    required_denials = {
        "execution", "approval", "custody", "replay_admission", "semantic_acceptance",
        "merge_permission", "release", "cutover", "next_phase",
    }
    if not isinstance(non_authority, dict) or set(non_authority) != required_denials:
        lib.fail("E_RECORD_AUTHORITY", "non_authority has wrong fields")
    if any(value is not False for value in non_authority.values()):
        lib.fail("E_RECORD_AUTHORITY", "every non-authority field must be false")


def require_sha1(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        lib.fail("E_BINDING_IDENTITY", f"invalid {label}")
    return value


def verify_binding_record(path: Path, limits: dict[str, int]) -> None:
    """Verify finite C/E/D/P correspondence and recovery-record shape."""
    record = canonical_document(path, limits)
    required = {"record_class", "protocol_version", "phase", "sequence", "C", "E", "D", "P", "recovery"}
    if not isinstance(record, dict):
        lib.fail("E_BINDING", "binding record must be an object")
    lib.require_keys(record, required, set(), "binding-record")
    if (
        record["record_class"] != "integration_binding"
        or record["protocol_version"] != lib.PROTOCOL_VERSION
        or record["phase"] != "M0.1"
        or record["sequence"] != ["C", "E", "D", "P"]
    ):
        lib.fail("E_BINDING_SEQUENCE", "binding record must declare finite C/E/D/P order")

    shapes = {
        "C": {"repository", "commit", "tree"},
        "E": {
            "repository", "commit", "tree", "source_candidate_commit",
            "source_candidate_tree", "index_sha256",
        },
        "D": {
            "repository", "review_commit", "review_tree", "review_blob",
            "owner_decision_commit", "owner_decision_tree", "owner_decision_blob",
            "source_candidate_commit", "evidence_commit",
        },
        "P": {
            "source_merge_commit", "source_merge_tree", "ledger_merge_commit",
            "ledger_merge_tree", "source_candidate_commit", "evidence_commit",
            "review_commit", "owner_decision_commit", "correspondence",
        },
        "recovery": {
            "repository", "retained_refs", "tested_at", "restored_commit",
            "restored_tree", "result",
        },
    }
    for name, fields in shapes.items():
        value = record[name]
        if not isinstance(value, dict):
            lib.fail("E_BINDING_FIELD", f"{name} must be an object")
        lib.require_keys(value, fields, set(), name)

    sha1_fields = {
        "C": ("commit", "tree"),
        "E": ("commit", "tree", "source_candidate_commit", "source_candidate_tree"),
        "D": (
            "review_commit", "review_tree", "review_blob", "owner_decision_commit",
            "owner_decision_tree", "owner_decision_blob", "source_candidate_commit",
            "evidence_commit",
        ),
        "P": (
            "source_merge_commit", "source_merge_tree", "ledger_merge_commit",
            "ledger_merge_tree", "source_candidate_commit", "evidence_commit",
            "review_commit", "owner_decision_commit",
        ),
        "recovery": ("restored_commit", "restored_tree"),
    }
    for section, fields in sha1_fields.items():
        for field in fields:
            require_sha1(record[section][field], f"{section}.{field}")
    for section in ("C", "E", "D"):
        repository = record[section]["repository"]
        if not isinstance(repository, str) or not repository:
            lib.fail("E_BINDING_IDENTITY", f"{section}.repository must be nonempty")
    digest = record["E"]["index_sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        lib.fail("E_BINDING_IDENTITY", "invalid E.index_sha256")

    if record["E"]["source_candidate_commit"] != record["C"]["commit"] or record["E"]["source_candidate_tree"] != record["C"]["tree"]:
        lib.fail("E_BINDING_CORRESPONDENCE", "E does not bind C")
    if record["D"]["source_candidate_commit"] != record["C"]["commit"] or record["D"]["evidence_commit"] != record["E"]["commit"]:
        lib.fail("E_BINDING_CORRESPONDENCE", "D does not bind C and E")
    expected_p = {
        "source_candidate_commit": record["C"]["commit"],
        "evidence_commit": record["E"]["commit"],
        "review_commit": record["D"]["review_commit"],
        "owner_decision_commit": record["D"]["owner_decision_commit"],
    }
    if any(record["P"][field] != value for field, value in expected_p.items()) or record["P"]["correspondence"] is not True:
        lib.fail("E_BINDING_CORRESPONDENCE", "P does not bind C, E, and D")

    recovery = record["recovery"]
    if (
        recovery["repository"] != record["E"]["repository"]
        or not isinstance(recovery["retained_refs"], list)
        or not recovery["retained_refs"]
        or any(not isinstance(item, str) or not item for item in recovery["retained_refs"])
        or recovery["result"] != "succeeded"
    ):
        lib.fail("E_RECOVERY", "recovery record is incomplete or unsuccessful")
    lib.parse_utc(recovery["tested_at"], "recovery.tested_at")
    if recovery["restored_commit"] != record["E"]["commit"] or recovery["restored_tree"] != record["E"]["tree"]:
        lib.fail("E_RECOVERY", "recovery does not restore the bound evidence identity")


def verify_freshness(path: Path, evaluation_time: str, evaluation_point: str, events: list[str], limits: dict[str, int]) -> None:
    document = lib.strict_json_file(path, limits)
    surfaces = lib.require_protocol_document(document, "surfaces")
    instant = lib.parse_utc(evaluation_time, "evaluation_time")
    failures: list[str] = []
    surface_ids: set[str] = set()
    for surface in surfaces:
        required = {
            "surface_id", "class", "status", "origin", "acquired_at", "coverage",
            "snapshot_sha256", "freshness_policy", "limitations",
        }
        if not isinstance(surface, dict):
            lib.fail("E_FRESHNESS_SURFACE", "invalid external surface")
        lib.require_keys(surface, required, set(), "external-surface")
        surface_id = surface["surface_id"]
        if not isinstance(surface_id, str) or not surface_id or surface_id in surface_ids:
            lib.fail("E_FRESHNESS_SURFACE", "surface_id must be nonempty and unique")
        surface_ids.add(surface_id)
        if surface["status"] not in {"inspected", "not_applicable", "limited", "unavailable", "historical"}:
            lib.fail("E_FRESHNESS_SURFACE", f"unknown status for {surface_id}")
        for field in ("class", "origin", "coverage"):
            if not isinstance(surface[field], str) or not surface[field]:
                lib.fail("E_FRESHNESS_SURFACE", f"{surface_id}.{field} must be nonempty")
        digest = surface["snapshot_sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            lib.fail("E_FRESHNESS_SURFACE", f"invalid snapshot digest for {surface_id}")
        if not isinstance(surface["limitations"], list) or any(not isinstance(item, str) for item in surface["limitations"]):
            lib.fail("E_FRESHNESS_SURFACE", f"invalid limitations for {surface_id}")
        lib.parse_utc(surface["acquired_at"], f"{surface_id}.acquired_at")
        eligible, reason = lib.evaluate_freshness(surface, instant, evaluation_point, set(events))
        if not eligible and surface.get("status") != "not_applicable":
            failures.append(f"{surface_id}:{reason}")
    if failures:
        lib.fail("E_FRESHNESS", ",".join(sorted(failures)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limits", type=Path, default=Path(__file__).resolve().with_name("limits.json"))
    sub = parser.add_subparsers(dest="command", required=True)
    package = sub.add_parser("package")
    package.add_argument("--package", required=True, type=Path)
    package.add_argument("--source-repository", required=True)
    package.add_argument("--source-tree", required=True)
    package.add_argument("--audit", type=Path)
    record = sub.add_parser("record")
    record.add_argument("--record", required=True, type=Path)
    binding = sub.add_parser("binding")
    binding.add_argument("--record", required=True, type=Path)
    freshness = sub.add_parser("freshness")
    freshness.add_argument("--external-surfaces", required=True, type=Path)
    freshness.add_argument("--evaluation-time", required=True)
    freshness.add_argument("--evaluation-point", required=True, choices=["owner_acceptance", "pre_integration"])
    freshness.add_argument("--event", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    if not sys.flags.isolated:
        lib.fail("E_RUNTIME_ISOLATION", "invoke with python3 -I")
    args = parse_args()
    limits = lib.load_limits(args.limits)
    if args.command == "package":
        rows = verify_package(args.package, args.source_repository, args.source_tree, limits)
        if args.audit is not None:
            index = canonical_document(args.package / "index.json", limits)
            reconcile(
                rows, args.audit, limits, index["scan_manifest_sha256"],
                args.source_repository, args.source_tree,
            )
    elif args.command == "record":
        verify_evidence_record(args.record, limits)
    elif args.command == "binding":
        verify_binding_record(args.record, limits)
    elif args.command == "freshness":
        verify_freshness(args.external_surfaces, args.evaluation_time, args.evaluation_point, args.event, limits)
    else:
        lib.fail("E_COMMAND", "unknown command")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lib.ProtocolError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        raise SystemExit(2)
