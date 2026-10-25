#!/usr/bin/env python3
"""Verify M0.1 v2 packages, bindings, records, and freshness."""

from __future__ import annotations

import argparse
import base64
import importlib.util
import sys
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

PRODUCTION_INPUT_PATHS = {
    "mappings.json",
    "classification-rules.json",
    "audit-policy.json",
    "surface-register.json",
    "external-surfaces.json",
    "applicability-decisions.json",
    "visual-inspection.json",
    "limitations.json",
}


def canonical_document(path: Path, limits: dict[str, int], maximum: int | None = None) -> Any:
    bound = limits["max_input_file_bytes"] if maximum is None else maximum
    data = lib.read_bounded_file(path, bound)
    return canonical_bytes(data, limits, str(path), bound)


def canonical_bytes(data: bytes, limits: dict[str, int], label: str, maximum: int) -> Any:
    value = lib.strict_json_bytes(data, limits, label, maximum)
    if data != lib.canonical_json_bytes(value, limits):
        lib.fail("E_CANONICAL_JSON", f"noncanonical JSON document: {label}")
    return value


def _nonempty_string(value: Any, label: str, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value:
        lib.fail("E_STRING", f"{label} must be a nonempty string")
    return value


def _canonical_input(files: dict[str, bytes], path: str, limits: dict[str, int]) -> Any:
    data = files.get(path)
    if data is None:
        lib.fail("E_INPUT_SET", f"missing compact input: {path}")
    value = lib.strict_json_bytes(data, limits, path, limits["max_input_file_bytes"])
    if data != lib.canonical_json_bytes(value, limits):
        lib.fail("E_CANONICAL_JSON", f"noncanonical compact input: {path}")
    return value


def _document_rows(document: Any, key: str, maximum: int, label: str) -> list[Any]:
    if not isinstance(document, dict):
        lib.fail("E_INPUT_SCHEMA", f"{label} must be an object")
    lib.require_keys(document, {"protocol_version", key}, set(), label)
    rows = document[key]
    if document["protocol_version"] != lib.PROTOCOL_VERSION or not isinstance(rows, list) or len(rows) > maximum:
        lib.fail("E_INPUT_SCHEMA", f"invalid {label}")
    return rows


def _string_array(value: Any, label: str, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        lib.fail("E_INPUT_SCHEMA", f"{label} must be a string array")
    if any(not isinstance(item, str) or not item for item in value):
        lib.fail("E_INPUT_SCHEMA", f"{label} contains an invalid string")
    return value


def _validate_mapping_document(document: Any, limits: dict[str, int]) -> set[str]:
    rows = _document_rows(document, "mappings", limits["max_mappings"], "mappings")
    ids: set[str] = set()
    sources: set[tuple[str, str]] = set()
    destinations: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        label = f"mappings[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_MAPPING_TYPE", f"{label} must be an object")
        lib.require_keys(row, {"mapping_id", "namespace", "original", "canonical", "policy"}, set(), label)
        mapping_id = lib.require_identifier(row["mapping_id"], f"{label}.mapping_id")
        namespace = lib.require_identifier(row["namespace"], f"{label}.namespace")
        original = _nonempty_string(row["original"], f"{label}.original")
        if mapping_id in ids or (namespace, original) in sources:
            lib.fail("E_MAPPING_SOURCE", f"duplicate mapping identity: {mapping_id}")
        ids.add(mapping_id)
        sources.add((namespace, original))
        policy = row["policy"]
        if policy not in {"replace", "retain", "compatibility"}:
            lib.fail("E_MAPPING_POLICY", f"unknown mapping policy: {policy}")
        if policy == "retain":
            if row["canonical"] is not None:
                lib.fail("E_MAPPING_CANONICAL", f"{label} retain requires null canonical")
            effective = original
        else:
            effective = _nonempty_string(row["canonical"], f"{label}.canonical")
        if (namespace, effective) in destinations:
            lib.fail("E_MAPPING_INJECTIVE", f"duplicate effective destination: {(namespace, effective)}")
        destinations.add((namespace, effective))
    return ids


def _validate_rules_document(document: Any, mapping_ids: set[str], limits: dict[str, int]) -> None:
    rows = _document_rows(document, "rules", limits["max_rules"], "classification-rules")
    rule_ids: set[str] = set()
    required = {
        "rule_id", "selector", "expected_count", "role", "phase", "rationale",
        "representative_context", "boundary_context", "producer", "consumer",
        "support_policy", "validation_test_id", "historical_relationship",
    }
    allowed_selector = {"mapping_id", "unit_kind", "path_exact", "path_prefix", "path_suffix", "json_pointer_prefix"}
    for index, row in enumerate(rows):
        label = f"rules[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_RULE_TYPE", f"{label} must be an object")
        lib.require_keys(row, required, set(), label)
        rule_id = lib.require_identifier(row["rule_id"], f"{label}.rule_id")
        if rule_id in rule_ids:
            lib.fail("E_RULE_ID", f"duplicate rule_id: {rule_id}")
        rule_ids.add(rule_id)
        selector = row["selector"]
        if not isinstance(selector, dict) or set(selector) - allowed_selector:
            lib.fail("E_SELECTOR_FIELD", f"invalid selector: {label}")
        if selector.get("mapping_id") not in mapping_ids or selector.get("unit_kind") not in lib.UNIT_KINDS:
            lib.fail("E_SELECTOR_UNIT", f"unknown mapping or unit kind: {label}")
        path_fields = [name for name in ("path_exact", "path_prefix", "path_suffix") if name in selector]
        if len(path_fields) != 1:
            lib.fail("E_SELECTOR_PATH", f"{label} requires exactly one path selector")
        selected = selector[path_fields[0]]
        if path_fields[0] == "path_suffix":
            if not isinstance(selected, str) or not selected or selected.startswith("/") or "\\" in selected or "\x00" in selected:
                lib.fail("E_SELECTOR_PATH", f"invalid path suffix: {label}")
        else:
            lib.validate_relpath(selected, limits)
        pointer = selector.get("json_pointer_prefix")
        if pointer is not None and not isinstance(pointer, str):
            lib.fail("E_SELECTOR_POINTER", f"invalid JSON Pointer prefix: {label}")
        if row["role"] not in lib.ROLES or (row["role"] == "historical" and path_fields[0] != "path_exact"):
            lib.fail("E_RULE_ROLE", f"invalid role or broad historical rule: {label}")
        count = row["expected_count"]
        if not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= limits["max_occurrences"]:
            lib.fail("E_RULE_COUNT", f"invalid expected count: {label}")
        lib.require_phase(row["phase"], f"{label}.phase")
        for field in ("rationale", "support_policy", "validation_test_id"):
            _nonempty_string(row[field], f"{label}.{field}")
        for field in ("representative_context", "boundary_context"):
            _string_array(row[field], f"{label}.{field}", True)
        for field in ("producer", "consumer", "historical_relationship"):
            _nonempty_string(row[field], f"{label}.{field}", True)


def _validate_audit_document(document: Any, limits: dict[str, int]) -> None:
    if not isinstance(document, dict):
        lib.fail("E_AUDIT_DOCUMENT", "audit policy must be an object")
    lib.require_keys(document, {"protocol_version", "independently_authored", "families"}, set(), "audit-policy")
    rows = document["families"]
    if (
        document["protocol_version"] != lib.PROTOCOL_VERSION
        or document["independently_authored"] is not True
        or not isinstance(rows, list)
        or len(rows) > limits["max_audit_families"]
    ):
        lib.fail("E_AUDIT_DOCUMENT", "audit policy must declare independent authorship")
    ids: set[str] = set()
    kinds = {"literal", "ascii_casefold_literal", "ascii_digit_suffix", "source_suffix", "path_component"}
    for index, row in enumerate(rows):
        label = f"families[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_AUDIT_FAMILY", f"{label} must be an object")
        lib.require_keys(row, {"family_id", "kind", "literal", "namespace", "unit_kinds"}, set(), label)
        family_id = lib.require_identifier(row["family_id"], f"{label}.family_id")
        if family_id in ids or row["kind"] not in kinds:
            lib.fail("E_AUDIT_FAMILY", f"duplicate or invalid family: {label}")
        ids.add(family_id)
        literal = _nonempty_string(row["literal"], f"{label}.literal")
        lib.require_identifier(row["namespace"], f"{label}.namespace")
        units = _string_array(row["unit_kinds"], f"{label}.unit_kinds", True)
        if len(units) != len(set(units)) or any(unit not in lib.UNIT_KINDS for unit in units):
            lib.fail("E_AUDIT_UNITS", f"invalid units: {label}")
        if row["kind"] in {"ascii_casefold_literal", "ascii_digit_suffix"} and any(ord(char) > 127 for char in literal):
            lib.fail("E_AUDIT_ASCII", f"non-ASCII literal: {label}")
        if row["kind"] in {"source_suffix", "path_component"} and units != ["path_component"]:
            lib.fail("E_AUDIT_UNITS", f"path family must be path-only: {label}")


def validate_compact_input_files(files: dict[str, bytes], limits: dict[str, int]) -> dict[str, Any]:
    if set(files) != PRODUCTION_INPUT_PATHS:
        lib.fail("E_INPUT_SET", f"compact input path set mismatch: {sorted(set(files) ^ PRODUCTION_INPUT_PATHS)}")
    documents = {path: _canonical_input(files, path, limits) for path in sorted(PRODUCTION_INPUT_PATHS)}
    mapping_ids = _validate_mapping_document(documents["mappings.json"], limits)
    _validate_rules_document(documents["classification-rules.json"], mapping_ids, limits)
    _validate_audit_document(documents["audit-policy.json"], limits)

    register_rows = _document_rows(documents["surface-register.json"], "required_surfaces", limits["max_source_files"], "surface-register")
    register: dict[str, str] = {}
    for index, value in enumerate(register_rows):
        if not isinstance(value, dict):
            lib.fail("E_SURFACE_REGISTER", f"required_surfaces[{index}] must be an object")
        lib.require_keys(value, {"surface_id", "class"}, set(), f"required_surfaces[{index}]")
        surface_id = lib.require_identifier(value["surface_id"], "required surface")
        surface_class = lib.require_identifier(value["class"], "required surface class")
        if surface_id in register:
            lib.fail("E_SURFACE_REGISTER", f"duplicate required surface: {surface_id}")
        register[surface_id] = surface_class
    if not register:
        lib.fail("E_SURFACE_REGISTER", "required surface register must be nonempty")

    surfaces = _document_rows(documents["external-surfaces.json"], "surfaces", limits["max_source_files"], "external-surfaces")
    surface_ids: set[str] = set()
    for index, row in enumerate(surfaces):
        label = f"surfaces[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_SURFACE", f"{label} must be an object")
        lib.require_keys(row, {"surface_id", "class", "status", "origin", "acquired_at", "coverage", "snapshot_sha256", "freshness_policy", "limitations"}, set(), label)
        surface_id = lib.require_identifier(row["surface_id"], f"{label}.surface_id")
        if surface_id in surface_ids:
            lib.fail("E_SURFACE", f"duplicate surface: {surface_id}")
        surface_ids.add(surface_id)
        surface_class = lib.require_identifier(row["class"], f"{label}.class")
        if row["status"] not in {"inspected", "not_applicable", "limited", "unavailable", "historical"}:
            lib.fail("E_SURFACE", f"invalid status: {label}")
        for field in ("origin", "coverage"):
            _nonempty_string(row[field], f"{label}.{field}")
        lib.parse_utc(row["acquired_at"], f"{label}.acquired_at")
        lib.require_sha256(row["snapshot_sha256"], f"{label}.snapshot_sha256")
        _string_array(row["limitations"], f"{label}.limitations")
        _validate_freshness_policy(row["freshness_policy"], f"{label}.freshness_policy")
        if register.get(surface_id) != surface_class:
            lib.fail("E_SURFACE_REGISTER", f"surface class mismatch: {surface_id}")
    if set(register) != surface_ids:
        lib.fail("E_SURFACE_REGISTER", "surface observations do not exactly match register")

    decisions = _document_rows(documents["applicability-decisions.json"], "decisions", limits["max_source_files"], "applicability-decisions")
    seen_decisions: set[str] = set()
    for index, row in enumerate(decisions):
        label = f"decisions[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_APPLICABILITY", f"{label} must be an object")
        decision_fields = {
            "surface_id", "disposition", "reviewer", "rationale", "subject_commit",
            "subject_tree", "record_repository", "record_commit", "record_tree",
            "record_path", "record_blob",
        }
        lib.require_keys(row, decision_fields, set(), label)
        surface_id = lib.require_identifier(row["surface_id"], f"{label}.surface_id")
        if surface_id in seen_decisions or surface_id not in surface_ids or row["disposition"] != "not_applicable":
            lib.fail("E_APPLICABILITY", f"invalid applicability decision: {label}")
        seen_decisions.add(surface_id)
        for field in ("subject_commit", "subject_tree", "record_commit", "record_tree", "record_blob"):
            lib.require_sha1(row[field], f"{label}.{field}")
        for field in ("reviewer", "rationale", "record_repository"):
            _nonempty_string(row[field], f"{label}.{field}")
        lib.validate_relpath(row["record_path"], limits)
    required_decisions = {
        row["surface_id"] for row in surfaces if row["status"] == "not_applicable"
    }
    if seen_decisions != required_decisions:
        lib.fail("E_APPLICABILITY", "reviewed applicability decisions do not exactly match not-applicable surfaces")

    visuals = _document_rows(documents["visual-inspection.json"], "visuals", limits["max_source_files"], "visual-inspection")
    visual_paths: set[str] = set()
    for index, row in enumerate(visuals):
        label = f"visuals[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_VISUAL", f"{label} must be an object")
        lib.require_keys(row, {"visual_id", "path", "blob_sha1", "sha256", "scope", "method", "reviewer", "whole_image_inspected", "regions", "limitations"}, set(), label)
        lib.require_identifier(row["visual_id"], f"{label}.visual_id")
        visual_path = lib.validate_relpath(row["path"], limits).as_posix()
        if visual_path in visual_paths:
            lib.fail("E_VISUAL", f"duplicate visual path: {visual_path}")
        visual_paths.add(visual_path)
        lib.require_sha1(row["blob_sha1"], f"{label}.blob_sha1")
        lib.require_sha256(row["sha256"], f"{label}.sha256")
        for field in ("scope", "method", "reviewer"):
            _nonempty_string(row[field], f"{label}.{field}")
        if row["whole_image_inspected"] is not True:
            lib.fail("E_VISUAL", f"{label} must record whole-image inspection")
        _string_array(row["regions"], f"{label}.regions")
        _string_array(row["limitations"], f"{label}.limitations")

    limitations = _document_rows(documents["limitations.json"], "limitations", limits["max_source_files"], "limitations")
    limitation_surfaces: set[str] = set()
    limitation_ids: set[str] = set()
    for index, row in enumerate(limitations):
        label = f"limitations[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_LIMITATION", f"{label} must be an object")
        lib.require_keys(row, {"limitation_id", "surface", "reason", "consequence", "disposition"}, set(), label)
        limitation_id = lib.require_identifier(row["limitation_id"], f"{label}.limitation_id")
        if limitation_id in limitation_ids:
            lib.fail("E_LIMITATION", f"duplicate limitation: {limitation_id}")
        limitation_ids.add(limitation_id)
        limitation_surfaces.add(_nonempty_string(row["surface"], f"{label}.surface"))
        for field in ("reason", "consequence", "disposition"):
            _nonempty_string(row[field], f"{label}.{field}")
    return {
        "documents": documents,
        "visuals": visuals,
        "visual_paths": visual_paths,
        "applicability_decisions": decisions,
        "limitation_surfaces": limitation_surfaces,
    }


def validate_locator(unit_kind: str, locator: Any) -> dict[str, Any]:
    if not isinstance(locator, dict):
        lib.fail("E_ROW_LOCATOR", "locator must be an object")
    if unit_kind == "path_component":
        expected = {"component_index", "component_byte_start", "component_byte_end"}
        start_name, end_name = "component_byte_start", "component_byte_end"
    elif unit_kind in {"raw_text", "embedded_identity", "machine_identifier"}:
        expected = {"byte_start", "byte_end"}
        start_name, end_name = "byte_start", "byte_end"
    elif unit_kind in {"structured_key", "structured_value"}:
        expected = {"json_pointer", "value_byte_start", "value_byte_end"}
        start_name, end_name = "value_byte_start", "value_byte_end"
        if not isinstance(locator.get("json_pointer"), str):
            lib.fail("E_ROW_LOCATOR", "structured locator requires JSON Pointer")
    else:
        lib.fail("E_ROW_ENUM", f"unknown unit kind: {unit_kind}")
    if set(locator) != expected:
        lib.fail("E_ROW_LOCATOR", f"wrong locator fields for {unit_kind}")
    for name in expected - {"json_pointer"}:
        value = locator[name]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            lib.fail("E_ROW_LOCATOR", f"invalid locator integer: {name}")
    if locator[end_name] <= locator[start_name]:
        lib.fail("E_ROW_LOCATOR", "locator end must exceed start")
    return locator


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
    unit_kind = row["unit_kind"]
    if unit_kind not in lib.UNIT_KINDS or row["role"] not in lib.ROLES:
        lib.fail("E_ROW_ENUM", "occurrence has unknown unit kind or role")
    lib.validate_relpath(row["path"], limits)
    validate_locator(unit_kind, row["locator"])
    lib.require_sha256(row["source_file_sha256"], "source_file_sha256")
    key = row["occurrence_key"]
    if not isinstance(key, str) or not key.startswith("sha256:"):
        lib.fail("E_OCCURRENCE_KEY", "invalid occurrence key")
    lib.require_sha256(key[7:], "occurrence key")
    _nonempty_string(row["original"], "original")
    if row["canonical"] is not None:
        _nonempty_string(row["canonical"], "canonical")
    lib.require_identifier(row["namespace"], "namespace")
    lib.require_identifier(row["mapping_id"], "mapping_id")
    lib.require_identifier(row["rule_id"], "rule_id")
    lib.require_phase(row["phase"], "phase")
    for field in ("support_policy", "validation_test_id", "context"):
        _nonempty_string(row[field], field)
    for field in ("producer", "consumer", "historical_relationship"):
        _nonempty_string(row[field], field, nullable=True)
    return row


def validate_scan_manifest(document: Any, limits: dict[str, int]) -> dict[str, dict[str, Any]]:
    if not isinstance(document, dict):
        lib.fail("E_SCAN_MANIFEST", "scan manifest must be an object")
    lib.require_keys(document, {"protocol_version", "files"}, set(), "scan-manifest")
    files = document["files"]
    if document["protocol_version"] != lib.PROTOCOL_VERSION or not isinstance(files, list):
        lib.fail("E_SCAN_MANIFEST", "invalid scan manifest")
    if len(files) > limits["max_source_files"]:
        lib.fail("E_SCAN_MANIFEST", "scan manifest exceeds max_source_files")
    previous: bytes | None = None
    total = 0
    result: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(files):
        label = f"scan-manifest.files[{index}]"
        if not isinstance(record, dict):
            lib.fail("E_SCAN_MANIFEST", f"{label} must be an object")
        lib.require_keys(
            record,
            {"path", "sha256", "byte_count", "text_status", "structured_status", "structured_error"},
            set(),
            label,
        )
        path = lib.validate_relpath(record["path"], limits).as_posix()
        key = path.encode("utf-8")
        if previous is not None and key <= previous:
            lib.fail("E_SCAN_MANIFEST_ORDER", "manifest paths are not strictly increasing")
        previous = key
        lib.require_sha256(record["sha256"], f"{path}.sha256")
        count = record["byte_count"]
        if not isinstance(count, int) or isinstance(count, bool) or count < 0 or count > limits["max_source_file_bytes"]:
            lib.fail("E_SCAN_MANIFEST", f"invalid byte count for {path}")
        total += count
        if total > limits["max_total_source_bytes"]:
            lib.fail("E_SCAN_MANIFEST", "manifest exceeds max_total_source_bytes")
        if record["text_status"] not in {"utf8", "non_utf8"}:
            lib.fail("E_SCAN_MANIFEST", f"invalid text status for {path}")
        if path.endswith(".json"):
            allowed = {"valid_json", "invalid_json"} if record["text_status"] == "utf8" else {"unavailable_non_utf8"}
        else:
            allowed = {"not_json"}
        if record["structured_status"] not in allowed:
            lib.fail("E_SCAN_MANIFEST", f"structured status conflicts for {path}")
        error = record["structured_error"]
        if record["structured_status"] == "invalid_json":
            _nonempty_string(error, f"{path}.structured_error")
        elif error is not None:
            lib.fail("E_SCAN_MANIFEST", f"unexpected structured error for {path}")
        result[path] = record
    return result


def _canonical_chunk_descriptors(rows: list[dict[str, Any]], limits: dict[str, int]) -> list[dict[str, Any]]:
    descriptors: list[dict[str, Any]] = []
    current: list[bytes] = []
    current_keys: list[str] = []
    current_size = 0
    for row in rows:
        encoded = lib.canonical_json_bytes(row, limits)
        if len(encoded) > limits["max_row_bytes"]:
            lib.fail("E_ROW_SIZE", "row exceeds max_row_bytes")
        if current and (
            len(current) >= limits["max_rows_per_chunk"]
            or current_size + len(encoded) > limits["max_chunk_bytes"]
        ):
            data = b"".join(current)
            descriptors.append({
                "sha256": lib.sha256_hex(data), "byte_count": len(data),
                "row_count": len(current_keys), "first_key": current_keys[0],
                "last_key": current_keys[-1],
            })
            current, current_keys, current_size = [], [], 0
        current.append(encoded)
        current_keys.append(row["occurrence_key"])
        current_size += len(encoded)
    if current:
        data = b"".join(current)
        descriptors.append({
            "sha256": lib.sha256_hex(data), "byte_count": len(data),
            "row_count": len(current_keys), "first_key": current_keys[0],
            "last_key": current_keys[-1],
        })
    return descriptors


def verify_package(
    package: Path,
    source_repository: str,
    source_tree: str,
    limits: dict[str, int],
) -> list[dict[str, Any]]:
    lib.assert_no_symlink_ancestors(package)
    if package.is_symlink() or not package.is_dir():
        lib.fail("E_PACKAGE", "package must be a non-symlink directory")
    expected_root = {
        "occurrences", "index.json", "summary.json", "scan-manifest.json",
        "publication.json",
    }
    actual_root: set[str] = set()
    for child in package.iterdir():
        actual_root.add(child.name)
        if len(actual_root) > len(expected_root):
            lib.fail("E_PACKAGE_FILES", "package root contains too many entries")
    if actual_root != expected_root:
        lib.fail("E_PACKAGE_FILES", f"unexpected package entries: {sorted(actual_root ^ expected_root)}")

    total_generated = 0

    def read_part(relative: str, per_file_limit: int) -> bytes:
        nonlocal total_generated
        path = package / relative
        try:
            size = path.lstat().st_size
        except OSError as error:
            lib.fail("E_FILE_READ", f"cannot inspect package part {relative}: {error}")
        if size > per_file_limit:
            lib.fail("E_FILE_SIZE", f"package part exceeds its limit: {relative}")
        if total_generated > limits["max_generated_bytes"] - size:
            lib.fail("E_GENERATED_SIZE", f"package budget exceeded before reading {relative}")
        data = lib.read_bounded_file(path, min(per_file_limit, limits["max_generated_bytes"] - total_generated))
        total_generated += len(data)
        return data

    publication_data = read_part("publication.json", limits["max_input_file_bytes"])
    publication = canonical_bytes(
        publication_data, limits, "publication.json", limits["max_input_file_bytes"]
    )
    publication_fields = {
        "protocol_version", "status", "scan_manifest_sha256", "index_sha256",
        "summary_sha256",
    }
    if not isinstance(publication, dict):
        lib.fail("E_PUBLICATION", "publication marker must be an object")
    lib.require_keys(publication, publication_fields, set(), "publication")
    if publication["protocol_version"] != lib.PROTOCOL_VERSION or publication["status"] != "complete":
        lib.fail("E_PUBLICATION", "package is not completely published")
    for field in ("scan_manifest_sha256", "index_sha256", "summary_sha256"):
        lib.require_sha256(publication[field], f"publication.{field}")

    index_data = read_part("index.json", limits["max_input_file_bytes"])
    index = canonical_bytes(index_data, limits, "index.json", limits["max_input_file_bytes"])
    required_index = {
        "protocol_version", "aggregate_sha256", "scan_manifest_sha256",
        "total_rows", "total_bytes", "chunks",
    }
    if not isinstance(index, dict):
        lib.fail("E_INDEX", "index must be an object")
    lib.require_keys(index, required_index, set(), "index")
    if index["protocol_version"] != lib.PROTOCOL_VERSION or not isinstance(index["chunks"], list):
        lib.fail("E_INDEX", "invalid index")
    if len(index["chunks"]) > limits["max_chunks"]:
        lib.fail("E_CHUNK_COUNT", "max_chunks exceeded")

    manifest_data = read_part("scan-manifest.json", limits["max_export_bytes"])
    manifest_document = canonical_bytes(
        manifest_data, limits, "scan-manifest.json", limits["max_export_bytes"]
    )
    manifest = validate_scan_manifest(manifest_document, limits)
    manifest_bytes = manifest_data

    occurrence_directory = package / "occurrences"
    if occurrence_directory.is_symlink() or not occurrence_directory.is_dir():
        lib.fail("E_CHUNK_DIR", "occurrences must be a non-symlink directory")
    actual_names: list[str] = []
    for child in occurrence_directory.iterdir():
        if len(actual_names) >= limits["max_chunks"]:
            lib.fail("E_CHUNK_COUNT", "occurrence directory exceeds max_chunks")
        if child.is_symlink() or not child.is_file():
            lib.fail("E_CHUNK_FILE", f"invalid chunk entry: {child}")
        actual_names.append(child.name)
    actual_names.sort()
    expected_names = [f"{number:04d}.jsonl" for number in range(len(index["chunks"]))]
    if actual_names != expected_names:
        lib.fail("E_CHUNK_SET", "chunk set does not match index")

    rows: list[dict[str, Any]] = []
    descriptors: list[dict[str, Any]] = []
    previous_key: str | None = None
    for number, claimed in enumerate(index["chunks"]):
        if not isinstance(claimed, dict):
            lib.fail("E_CHUNK_DESCRIPTOR", "chunk descriptor must be an object")
        expected_path = f"occurrences/{number:04d}.jsonl"
        data = read_part(expected_path, limits["max_chunk_bytes"])
        if not data or not data.endswith(b"\n"):
            lib.fail("E_CHUNK_NEWLINE", f"invalid chunk newline: {expected_path}")
        chunk_rows: list[dict[str, Any]] = []
        for row_number, line in enumerate(data.splitlines(keepends=True), start=1):
            if len(line) > limits["max_row_bytes"]:
                lib.fail("E_ROW_SIZE", f"oversized row {expected_path}:{row_number}")
            row = validate_occurrence(lib.strict_json_bytes(line, limits, expected_path, limits["max_row_bytes"]), limits)
            if line != lib.canonical_json_bytes(row, limits):
                lib.fail("E_ROW_CANONICAL", f"noncanonical row {expected_path}:{row_number}")
            recomputed = lib.occurrence_key(
                source_repository, source_tree, row["path"], row["unit_kind"], row["locator"],
                row["namespace"], row["original"], limits,
            )
            if row["occurrence_key"] != recomputed:
                lib.fail("E_OCCURRENCE_KEY", f"key mismatch at {expected_path}:{row_number}")
            key = row["occurrence_key"]
            if previous_key is not None and key <= previous_key:
                lib.fail("E_ROW_ORDER", f"non-increasing key at {expected_path}:{row_number}")
            previous_key = key
            source = manifest.get(row["path"])
            if source is None or row["source_file_sha256"] != source["sha256"]:
                lib.fail("E_SOURCE_BINDING", f"row is not bound to manifest bytes: {key}")
            rows.append(row)
            chunk_rows.append(row)
            if len(rows) > limits["max_occurrences"]:
                lib.fail("E_OCCURRENCE_COUNT", "max_occurrences exceeded")
        if not chunk_rows or len(chunk_rows) > limits["max_rows_per_chunk"]:
            lib.fail("E_CHUNK_ROWS", f"invalid row count: {expected_path}")
        descriptor = {
            "path": expected_path,
            "sha256": lib.sha256_hex(data),
            "byte_count": len(data),
            "row_count": len(chunk_rows),
            "first_key": chunk_rows[0]["occurrence_key"],
            "last_key": chunk_rows[-1]["occurrence_key"],
        }
        if claimed != descriptor:
            lib.fail("E_CHUNK_DESCRIPTOR", f"descriptor mismatch: {expected_path}")
        descriptors.append(descriptor)

    expected_descriptors = _canonical_chunk_descriptors(rows, limits)
    actual_boundaries = [
        {key: descriptor[key] for key in ("sha256", "byte_count", "row_count", "first_key", "last_key")}
        for descriptor in descriptors
    ]
    if actual_boundaries != expected_descriptors:
        lib.fail("E_CHUNK_BOUNDARY", "chunks do not use canonical greedy boundaries")
    expected_index = {
        "protocol_version": lib.PROTOCOL_VERSION,
        "aggregate_sha256": lib.aggregate_digest(descriptors),
        "scan_manifest_sha256": lib.sha256_hex(manifest_bytes),
        "total_rows": len(rows),
        "total_bytes": sum(item["byte_count"] for item in descriptors),
        "chunks": descriptors,
    }
    if index != expected_index:
        lib.fail("E_INDEX", "index totals or digests do not match")
    summary_data = read_part("summary.json", limits["max_input_file_bytes"])
    summary = canonical_bytes(summary_data, limits, "summary.json", limits["max_input_file_bytes"])
    if summary != lib.summary_for(rows):
        lib.fail("E_SUMMARY", "summary does not match rows")
    expected_publication = {
        "protocol_version": lib.PROTOCOL_VERSION,
        "status": "complete",
        "scan_manifest_sha256": lib.sha256_hex(manifest_data),
        "index_sha256": lib.sha256_hex(index_data),
        "summary_sha256": lib.sha256_hex(summary_data),
    }
    if publication != expected_publication:
        lib.fail("E_PUBLICATION", "publication marker does not bind package documents")
    return rows


def reconcile(
    rows: list[dict[str, Any]],
    audit_path: Path,
    limits: dict[str, int],
    source_repository: str,
    source_commit: str,
    source_tree: str,
    source_export_sha256: str,
    input_export_sha256: str,
    scan_manifest_sha256: str,
) -> None:
    audit = canonical_document(audit_path, limits, limits["max_audit_output_bytes"])
    required = {
        "protocol_version", "source_repository", "source_commit", "source_tree",
        "source_export_sha256", "input_export_sha256", "scan_manifest_sha256",
        "scan_manifest", "candidate_count", "candidates",
    }
    if not isinstance(audit, dict):
        lib.fail("E_AUDIT_DOCUMENT", "audit result must be an object")
    lib.require_keys(audit, required, set(), "audit-result")
    expected_identity = {
        "source_repository": source_repository,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "source_export_sha256": source_export_sha256,
        "input_export_sha256": input_export_sha256,
        "scan_manifest_sha256": scan_manifest_sha256,
    }
    if audit["protocol_version"] != lib.PROTOCOL_VERSION:
        lib.fail("E_AUDIT_DOCUMENT", "wrong audit protocol version")
    for field, value in expected_identity.items():
        if audit[field] != value:
            lib.fail("E_AUDIT_SOURCE", f"audit {field} mismatch")
    validate_scan_manifest({"protocol_version": lib.PROTOCOL_VERSION, "files": audit["scan_manifest"]}, limits)
    if lib.scan_manifest_digest(audit["scan_manifest"], limits) != audit["scan_manifest_sha256"]:
        lib.fail("E_AUDIT_MANIFEST", "audit manifest digest mismatch")
    candidates = audit["candidates"]
    if not isinstance(candidates, list) or len(candidates) > limits["max_occurrences"]:
        lib.fail("E_AUDIT_CANDIDATE", "invalid candidate array")
    audit_keys: list[str] = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            lib.fail("E_AUDIT_CANDIDATE", f"candidate {index} must be an object")
        lib.require_keys(
            candidate,
            {"occurrence_key", "path", "unit_kind", "locator", "namespace", "original", "family_id"},
            set(),
            f"candidate[{index}]",
        )
        path = lib.validate_relpath(candidate["path"], limits).as_posix()
        if candidate["unit_kind"] not in lib.UNIT_KINDS:
            lib.fail("E_AUDIT_CANDIDATE", "unknown audit unit kind")
        validate_locator(candidate["unit_kind"], candidate["locator"])
        lib.require_identifier(candidate["namespace"], "audit namespace")
        lib.require_identifier(candidate["family_id"], "audit family_id")
        _nonempty_string(candidate["original"], "audit original")
        recomputed = lib.occurrence_key(
            source_repository, source_tree, path, candidate["unit_kind"], candidate["locator"],
            candidate["namespace"], candidate["original"], limits,
        )
        if candidate["occurrence_key"] != recomputed:
            lib.fail("E_AUDIT_KEY", "audit candidate key mismatch")
        audit_keys.append(recomputed)
    if audit["candidate_count"] != len(audit_keys) or len(audit_keys) != len(set(audit_keys)):
        lib.fail("E_AUDIT_DUPLICATE", "audit candidate count or uniqueness mismatch")
    generated_keys = {row["occurrence_key"] for row in rows}
    audit_set = set(audit_keys)
    if generated_keys != audit_set:
        lib.fail(
            "E_KEY_SET_MISMATCH",
            f"missing={sorted(audit_set - generated_keys)[:20]} extra={sorted(generated_keys - audit_set)[:20]}",
        )


def _validate_freshness_policy(policy: Any, label: str) -> None:
    if not isinstance(policy, dict):
        lib.fail("E_FRESHNESS_POLICY", f"{label} must be an object")
    lib.require_keys(
        policy,
        {"evaluation_points", "point_in_time_only", "invalidating_events", "max_age_seconds"},
        set(),
        label,
    )
    points = policy["evaluation_points"]
    if not isinstance(points, list) or set(points) != {"owner_acceptance", "pre_integration"} or len(points) != 2:
        lib.fail("E_FRESHNESS_POLICY", f"{label} must contain both evaluation points exactly")
    if not isinstance(policy["point_in_time_only"], bool):
        lib.fail("E_FRESHNESS_POLICY", f"{label}.point_in_time_only must be Boolean")
    events = policy["invalidating_events"]
    if not isinstance(events, list) or len(events) != len(set(events)):
        lib.fail("E_FRESHNESS_POLICY", f"{label}.invalidating_events must be unique")
    for event in events:
        lib.require_identifier(event, f"{label}.invalidating_event")
    maximum = policy["max_age_seconds"]
    if maximum is not None and (not isinstance(maximum, int) or isinstance(maximum, bool) or maximum <= 0):
        lib.fail("E_FRESHNESS_POLICY", f"{label}.max_age_seconds is invalid")
    if maximum is None and not events and policy["point_in_time_only"] is False:
        lib.fail("E_FRESHNESS_POLICY", f"{label} has no eligibility rule")


def verify_freshness(
    surface_path: Path,
    register_path: Path,
    applicability_path: Path,
    evaluation_time: str,
    evaluation_point: str,
    events: list[str],
    subject_commit: str,
    subject_tree: str,
    limits: dict[str, int],
) -> None:
    register = canonical_document(register_path, limits)
    surfaces_document = canonical_document(surface_path, limits)
    decisions_document = canonical_document(applicability_path, limits)
    if not isinstance(register, dict) or not isinstance(surfaces_document, dict) or not isinstance(decisions_document, dict):
        lib.fail("E_FRESHNESS_DOCUMENT", "freshness inputs must be objects")
    lib.require_keys(register, {"protocol_version", "required_surfaces"}, set(), "surface-register")
    lib.require_keys(surfaces_document, {"protocol_version", "surfaces"}, set(), "external-surfaces")
    lib.require_keys(decisions_document, {"protocol_version", "decisions"}, set(), "applicability-decisions")
    if any(document["protocol_version"] != lib.PROTOCOL_VERSION for document in (register, surfaces_document, decisions_document)):
        lib.fail("E_PROTOCOL_VERSION", "freshness document version mismatch")
    required_rows = register["required_surfaces"]
    surfaces = surfaces_document["surfaces"]
    decisions = decisions_document["decisions"]
    if not isinstance(required_rows, list) or not required_rows:
        lib.fail("E_SURFACE_REGISTER", "required surface register must be nonempty")
    if not isinstance(surfaces, list) or not isinstance(decisions, list):
        lib.fail("E_FRESHNESS_DOCUMENT", "surfaces and decisions must be arrays")
    required: dict[str, str] = {}
    for index, row in enumerate(required_rows):
        if not isinstance(row, dict):
            lib.fail("E_SURFACE_REGISTER", "surface register row must be an object")
        lib.require_keys(row, {"surface_id", "class"}, set(), f"required_surfaces[{index}]")
        surface_id = lib.require_identifier(row["surface_id"], "surface_id")
        surface_class = lib.require_identifier(row["class"], "surface class")
        if surface_id in required:
            lib.fail("E_SURFACE_REGISTER", f"duplicate required surface: {surface_id}")
        required[surface_id] = surface_class
    observed: dict[str, dict[str, Any]] = {}
    for index, surface in enumerate(surfaces):
        if not isinstance(surface, dict):
            lib.fail("E_FRESHNESS_SURFACE", "surface must be an object")
        fields = {
            "surface_id", "class", "status", "origin", "acquired_at", "coverage",
            "snapshot_sha256", "freshness_policy", "limitations",
        }
        lib.require_keys(surface, fields, set(), f"surfaces[{index}]")
        surface_id = lib.require_identifier(surface["surface_id"], "surface_id")
        if surface_id in observed:
            lib.fail("E_FRESHNESS_SURFACE", f"duplicate surface: {surface_id}")
        if surface_id not in required or surface["class"] != required[surface_id]:
            lib.fail("E_FRESHNESS_SURFACE", f"unregistered or misclassified surface: {surface_id}")
        if surface["status"] not in {"inspected", "not_applicable", "limited", "unavailable", "historical"}:
            lib.fail("E_FRESHNESS_SURFACE", f"unknown status: {surface_id}")
        for field in ("origin", "coverage"):
            _nonempty_string(surface[field], f"{surface_id}.{field}")
        lib.parse_utc(surface["acquired_at"], f"{surface_id}.acquired_at")
        lib.require_sha256(surface["snapshot_sha256"], f"{surface_id}.snapshot_sha256")
        if not isinstance(surface["limitations"], list) or any(not isinstance(item, str) or not item for item in surface["limitations"]):
            lib.fail("E_FRESHNESS_SURFACE", f"invalid limitations: {surface_id}")
        _validate_freshness_policy(surface["freshness_policy"], f"{surface_id}.freshness_policy")
        observed[surface_id] = surface
    if set(observed) != set(required):
        lib.fail("E_REQUIRED_SURFACE", f"missing={sorted(set(required) - set(observed))}")

    applicability: dict[str, dict[str, Any]] = {}
    decision_fields = {
        "surface_id", "disposition", "reviewer", "rationale", "subject_commit",
        "subject_tree", "record_repository", "record_commit", "record_tree",
        "record_path", "record_blob",
    }
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            lib.fail("E_APPLICABILITY", "applicability decision must be an object")
        lib.require_keys(decision, decision_fields, set(), f"decisions[{index}]")
        surface_id = lib.require_identifier(decision["surface_id"], "decision surface_id")
        if decision["disposition"] != "not_applicable" or surface_id in applicability:
            lib.fail("E_APPLICABILITY", f"invalid applicability decision: {surface_id}")
        for field in ("reviewer", "rationale", "record_repository"):
            _nonempty_string(decision[field], f"decision.{field}")
        for field in ("subject_commit", "subject_tree", "record_commit", "record_tree", "record_blob"):
            lib.require_sha1(decision[field], f"decision.{field}")
        lib.validate_relpath(decision["record_path"], limits)
        if decision["subject_commit"] != subject_commit or decision["subject_tree"] != subject_tree:
            lib.fail("E_APPLICABILITY", f"decision does not bind current subject: {surface_id}")
        applicability[surface_id] = decision

    instant = lib.parse_utc(evaluation_time, "evaluation_time")
    failures: list[str] = []
    for surface_id, surface in observed.items():
        if surface["status"] == "not_applicable":
            if surface_id not in applicability:
                failures.append(f"{surface_id}:missing_reviewed_applicability")
            continue
        if surface_id in applicability:
            failures.append(f"{surface_id}:unexpected_applicability_decision")
            continue
        eligible, reason = lib.evaluate_freshness(surface, instant, evaluation_point, set(events))
        if not eligible:
            failures.append(f"{surface_id}:{reason}")
    if failures:
        lib.fail("E_FRESHNESS", ",".join(sorted(failures)))


def verify_evidence_binding(
    record_path: Path,
    package: Path,
    source_root: Path,
    source_export_path: Path,
    base_root: Path,
    base_export_path: Path,
    contract_root: Path,
    contract_export_path: Path,
    tooling_root: Path,
    tooling_export_path: Path,
    input_root: Path,
    input_export_path: Path,
    limits: dict[str, int],
) -> None:
    record = canonical_document(record_path, limits)
    required = {
        "record_class", "protocol_version", "phase", "source", "accepted_base",
        "governing_contract", "tooling", "inputs", "generated", "non_authority",
    }
    if not isinstance(record, dict):
        lib.fail("E_RECORD", "record must be an object")
    lib.require_keys(record, required, set(), "evidence-record")
    if record["record_class"] != "migration_evidence" or record["protocol_version"] != lib.PROTOCOL_VERSION or record["phase"] != "M0.1":
        lib.fail("E_RECORD_CLASS", "invalid evidence record class, version, or phase")
    source_fields = {
        "repository", "commit", "tree", "view_prefix", "view_tree", "export_sha256",
    }
    contract_fields = {
        "repository", "commit", "tree", "view_prefix", "view_tree",
        "path", "blob", "export_sha256",
    }
    tooling_fields = {
        "repository", "commit", "tree", "view_prefix", "view_tree",
        "required_paths", "export_sha256",
    }
    input_fields = {
        "repository", "commit", "tree", "view_prefix", "view_tree",
        "required_paths", "export_sha256", "aggregate_sha256",
    }
    generated_fields = {
        "scan_manifest_sha256", "index_sha256", "summary_sha256",
        "publication_sha256", "aggregate_sha256",
    }
    for field, fields in (
        ("source", source_fields), ("accepted_base", source_fields),
        ("governing_contract", contract_fields), ("tooling", tooling_fields),
        ("inputs", input_fields), ("generated", generated_fields),
    ):
        value = record[field]
        if not isinstance(value, dict):
            lib.fail("E_RECORD_FIELD", f"{field} must be an object")
        lib.require_keys(value, fields, set(), field)

    export_specs = {
        "source": (source_root, source_export_path),
        "accepted_base": (base_root, base_export_path),
        "governing_contract": (contract_root, contract_export_path),
        "tooling": (tooling_root, tooling_export_path),
        "inputs": (input_root, input_export_path),
    }
    exported_files: dict[str, dict[str, bytes]] = {}
    entries: dict[str, list[dict[str, Any]]] = {}
    for field, (root, export_path) in export_specs.items():
        section = record[field]
        document, files = lib.verify_git_export(
            root, export_path, limits, section["repository"], section["commit"],
            section["tree"], section["view_prefix"], section["view_tree"], False,
        )
        exported_files[field] = dict(files)
        entries[field] = document["entries"]
        digest = lib.export_digest(document, limits)
        if section["export_sha256"] != digest:
            lib.fail("E_RECORD_EXPORT", f"{field} export digest mismatch")

    contract = record["governing_contract"]
    lib.validate_relpath(contract["path"], limits)
    lib.require_sha1(contract["blob"], "governing contract blob")
    contract_entries = {entry["path"]: entry for entry in entries["governing_contract"]}
    if contract["path"] not in contract_entries or contract_entries[contract["path"]]["blob_sha1"] != contract["blob"]:
        lib.fail("E_RECORD_CONTRACT", "governing contract blob is not present in its authenticated export")

    for field in ("tooling", "inputs"):
        paths = record[field]["required_paths"]
        if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
            lib.fail("E_RECORD_PATHS", f"{field}.required_paths must be nonempty and unique")
        for path in paths:
            lib.validate_relpath(path, limits)
        available = {entry["path"] for entry in entries[field]}
        if not set(paths).issubset(available):
            lib.fail("E_RECORD_PATHS", f"{field} export is missing required paths")
    if set(record["inputs"]["required_paths"]) != PRODUCTION_INPUT_PATHS:
        lib.fail("E_RECORD_INPUTS", "production compact input set is incomplete")
    input_entries = {entry["path"]: entry for entry in entries["inputs"]}
    input_descriptor = [input_entries[path] for path in sorted(PRODUCTION_INPUT_PATHS)]
    expected_input_digest = lib.sha256_hex(lib.canonical_json_bytes(input_descriptor, limits, trailing_lf=False))
    if record["inputs"]["aggregate_sha256"] != expected_input_digest:
        lib.fail("E_RECORD_INPUTS", "compact input aggregate mismatch")
    compact = validate_compact_input_files(exported_files["inputs"], limits)

    rows = verify_package(package, record["source"]["repository"], record["source"]["tree"], limits)
    del rows
    index_data = lib.read_bounded_file(package / "index.json", limits["max_input_file_bytes"])
    summary_data = lib.read_bounded_file(package / "summary.json", limits["max_input_file_bytes"])
    manifest_data = lib.read_bounded_file(package / "scan-manifest.json", limits["max_export_bytes"])
    publication_data = lib.read_bounded_file(package / "publication.json", limits["max_input_file_bytes"])
    index = lib.strict_json_bytes(index_data, limits, "index.json")
    expected_generated = {
        "scan_manifest_sha256": lib.sha256_hex(manifest_data),
        "index_sha256": lib.sha256_hex(index_data),
        "summary_sha256": lib.sha256_hex(summary_data),
        "publication_sha256": lib.sha256_hex(publication_data),
        "aggregate_sha256": index["aggregate_sha256"],
    }
    if record["generated"] != expected_generated:
        lib.fail("E_RECORD_GENERATED", "generated package binding mismatch")

    manifest_document = lib.strict_json_bytes(
        manifest_data, limits, "scan-manifest.json", limits["max_export_bytes"]
    )
    manifest = validate_scan_manifest(manifest_document, limits)
    authenticated_manifest = lib.scan_manifest(
        sorted(exported_files["source"].items(), key=lambda item: item[0].encode("utf-8")),
        limits,
    )
    if manifest_document != lib.scan_manifest_document(authenticated_manifest):
        lib.fail("E_SOURCE_BINDING", "package scan manifest does not exactly cover authenticated source bytes")
    source_entries = {entry["path"]: entry for entry in entries["source"]}
    for visual in compact["visuals"]:
        entry = source_entries.get(visual["path"])
        if entry is None or entry["blob_sha1"] != visual["blob_sha1"] or entry["sha256"] != visual["sha256"]:
            lib.fail("E_VISUAL_BINDING", f"visual record does not bind authenticated source bytes: {visual['path']}")
    tooling_entries = {entry["path"]: entry for entry in entries["tooling"]}
    tooling = record["tooling"]
    for decision in compact["applicability_decisions"]:
        entry = tooling_entries.get(decision["record_path"])
        if (
            decision["subject_commit"] != record["source"]["commit"]
            or decision["subject_tree"] != record["source"]["tree"]
            or decision["record_repository"] != tooling["repository"]
            or decision["record_commit"] != tooling["commit"]
            or decision["record_tree"] != tooling["tree"]
            or entry is None
            or entry["blob_sha1"] != decision["record_blob"]
        ):
            lib.fail("E_APPLICABILITY_BINDING", f"applicability decision record is not authenticated: {decision['surface_id']}")
    for path, item in manifest.items():
        if item["text_status"] == "non_utf8" or item["structured_status"] == "invalid_json":
            if f"file:{path}" not in compact["limitation_surfaces"] and path not in compact["visual_paths"]:
                lib.fail("E_SOURCE_DISPOSITION", f"source scan limitation lacks explicit disposition: {path}")

    denials = {
        "execution", "approval", "custody", "replay_admission", "semantic_acceptance",
        "merge_permission", "release", "cutover", "next_phase",
    }
    non_authority = record["non_authority"]
    if not isinstance(non_authority, dict) or set(non_authority) != denials or any(value is not False for value in non_authority.values()):
        lib.fail("E_RECORD_AUTHORITY", "non-authority flags are incomplete or elevated")


def _commit_evidence(value: Any, label: str) -> dict[str, Any]:
    fields = {"repository", "branch", "commit", "tree", "parents", "commit_object_base64"}
    if not isinstance(value, dict):
        lib.fail("E_COMMIT_EVIDENCE", f"{label} must be an object")
    lib.require_keys(value, fields, set(), label)
    _nonempty_string(value["repository"], f"{label}.repository")
    _nonempty_string(value["branch"], f"{label}.branch")
    lib.require_sha1(value["commit"], f"{label}.commit")
    lib.require_sha1(value["tree"], f"{label}.tree")
    parents = value["parents"]
    if not isinstance(parents, list):
        lib.fail("E_COMMIT_EVIDENCE", f"{label}.parents must be an array")
    for parent in parents:
        lib.require_sha1(parent, f"{label}.parent")
    try:
        raw = base64.b64decode(value["commit_object_base64"], validate=True)
    except (ValueError, TypeError) as error:
        lib.fail("E_COMMIT_EVIDENCE", f"{label} has invalid commit object: {error}")
    if lib.git_object_sha1("commit", raw) != value["commit"]:
        lib.fail("E_COMMIT_EVIDENCE", f"{label} commit object identity mismatch")
    headers = raw.split(b"\n\n", 1)[0].splitlines()
    trees = [line[5:].decode("ascii") for line in headers if line.startswith(b"tree ")]
    actual_parents = [line[7:].decode("ascii") for line in headers if line.startswith(b"parent ")]
    if trees != [value["tree"]] or actual_parents != parents:
        lib.fail("E_COMMIT_EVIDENCE", f"{label} tree or parents mismatch")
    return value


def _introduced_chain(
    base: dict[str, Any],
    reviewed: dict[str, Any],
    values: Any,
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(values, list) or not values:
        lib.fail("E_BINDING_ANCESTRY", f"{label} must be a nonempty introduced-commit array")
    chain = [_commit_evidence(value, f"{label}[{index}]") for index, value in enumerate(values)]
    prior = base["commit"]
    repository = base["repository"]
    branch = base["branch"]
    for index, commit in enumerate(chain):
        if commit["repository"] != repository or commit["branch"] != branch:
            lib.fail("E_BINDING_ANCESTRY", f"{label}[{index}] repository or branch drift")
        if not commit["parents"] or commit["parents"][0] != prior:
            lib.fail("E_BINDING_ANCESTRY", f"{label}[{index}] does not first-parent descend from prior commit")
        prior = commit["commit"]
    if chain[-1] != reviewed:
        lib.fail("E_BINDING_ANCESTRY", f"{label} does not terminate at reviewed head")
    return chain


def verify_binding_record(path: Path, limits: dict[str, int]) -> None:
    record = canonical_document(path, limits, limits["max_export_bytes"])
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

    for section, fields in (
        ("C", {"base", "introduced_commits", "reviewed"}),
        ("E", {"base", "introduced_commits", "reviewed", "source_candidate_commit", "source_candidate_tree", "index_sha256"}),
        ("D", {"review", "owner_decision", "source_candidate_commit", "evidence_commit", "review_record_blob", "owner_decision_blob"}),
        ("P", {"source_merge", "ledger_merge", "source_head", "ledger_head"}),
    ):
        value = record[section]
        if not isinstance(value, dict):
            lib.fail("E_BINDING_FIELD", f"{section} must be an object")
        lib.require_keys(value, fields, set(), section)
    C_base = _commit_evidence(record["C"]["base"], "C.base")
    C_reviewed = _commit_evidence(record["C"]["reviewed"], "C.reviewed")
    E_base = _commit_evidence(record["E"]["base"], "E.base")
    E_reviewed = _commit_evidence(record["E"]["reviewed"], "E.reviewed")
    D_review = _commit_evidence(record["D"]["review"], "D.review")
    D_owner = _commit_evidence(record["D"]["owner_decision"], "D.owner_decision")
    source_merge = _commit_evidence(record["P"]["source_merge"], "P.source_merge")
    ledger_merge = _commit_evidence(record["P"]["ledger_merge"], "P.ledger_merge")

    lib.require_sha256(record["E"]["index_sha256"], "E.index_sha256")
    for field in ("source_candidate_commit", "source_candidate_tree"):
        lib.require_sha1(record["E"][field], f"E.{field}")
    for field in ("source_candidate_commit", "evidence_commit", "review_record_blob", "owner_decision_blob"):
        lib.require_sha1(record["D"][field], f"D.{field}")
    _introduced_chain(C_base, C_reviewed, record["C"]["introduced_commits"], "C.introduced_commits")
    _introduced_chain(E_base, E_reviewed, record["E"]["introduced_commits"], "E.introduced_commits")
    if record["E"]["source_candidate_commit"] != C_reviewed["commit"] or record["E"]["source_candidate_tree"] != C_reviewed["tree"]:
        lib.fail("E_BINDING_CORRESPONDENCE", "E does not bind reviewed C")
    if (
        record["D"]["source_candidate_commit"] != C_reviewed["commit"]
        or record["D"]["evidence_commit"] != E_reviewed["commit"]
        or D_review["parents"] != [E_reviewed["commit"]]
        or D_owner["parents"] != [D_review["commit"]]
    ):
        lib.fail("E_BINDING_CORRESPONDENCE", "D does not descend from and bind C/E")
    if source_merge["parents"] != [C_base["commit"], C_reviewed["commit"]] or source_merge["tree"] != C_reviewed["tree"]:
        lib.fail("E_BINDING_INTEGRATION", "source merge does not integrate reviewed C over its base")
    if ledger_merge["parents"] != [E_base["commit"], D_owner["commit"]] or ledger_merge["tree"] != D_owner["tree"]:
        lib.fail("E_BINDING_INTEGRATION", "ledger merge does not integrate E/D over its base")
    if record["P"]["source_head"] != C_reviewed["commit"] or record["P"]["ledger_head"] != D_owner["commit"]:
        lib.fail("E_BINDING_INTEGRATION", "P names incorrect integrated heads")
    if source_merge["branch"] != C_base["branch"] or ledger_merge["branch"] != E_base["branch"]:
        lib.fail("E_BINDING_TARGET", "merge target branch does not match accepted base branch")

    recovery = record["recovery"]
    recovery_fields = {
        "repository", "backup_sha256", "retained_refs", "tested_at",
        "restored_commit", "restored_tree", "restored_commit_object_base64",
        "recovery_evidence_blob",
    }
    if not isinstance(recovery, dict):
        lib.fail("E_RECOVERY", "recovery must be an object")
    lib.require_keys(recovery, recovery_fields, set(), "recovery")
    if recovery["repository"] != E_reviewed["repository"]:
        lib.fail("E_RECOVERY", "recovery repository mismatch")
    lib.require_sha256(recovery["backup_sha256"], "recovery backup_sha256")
    lib.require_sha1(recovery["restored_commit"], "recovery restored_commit")
    lib.require_sha1(recovery["restored_tree"], "recovery restored_tree")
    lib.require_sha1(recovery["recovery_evidence_blob"], "recovery evidence blob")
    if not isinstance(recovery["retained_refs"], list) or not recovery["retained_refs"] or any(not isinstance(item, str) or not item for item in recovery["retained_refs"]):
        lib.fail("E_RECOVERY", "retained_refs must be nonempty")
    lib.parse_utc(recovery["tested_at"], "recovery.tested_at")
    restored = _commit_evidence(
        {
            "repository": recovery["repository"],
            "branch": E_reviewed["branch"],
            "commit": recovery["restored_commit"],
            "tree": recovery["restored_tree"],
            "parents": E_reviewed["parents"],
            "commit_object_base64": recovery["restored_commit_object_base64"],
        },
        "recovery.restored",
    )
    if restored["commit"] != E_reviewed["commit"] or restored["tree"] != E_reviewed["tree"]:
        lib.fail("E_RECOVERY", "recovery did not restore reviewed E")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="command", required=True)
    package = subcommands.add_parser("package")
    package.add_argument("--package", required=True, type=Path)
    package.add_argument("--source-repository", required=True)
    package.add_argument("--source-commit", required=True)
    package.add_argument("--source-tree", required=True)
    package.add_argument("--source-export-sha256", required=True)
    package.add_argument("--input-export-sha256", required=True)
    package.add_argument("--audit", type=Path)
    evidence = subcommands.add_parser("evidence")
    evidence.add_argument("--record", required=True, type=Path)
    evidence.add_argument("--package", required=True, type=Path)
    evidence.add_argument("--source-root", required=True, type=Path)
    evidence.add_argument("--source-export", required=True, type=Path)
    evidence.add_argument("--base-root", required=True, type=Path)
    evidence.add_argument("--base-export", required=True, type=Path)
    evidence.add_argument("--contract-root", required=True, type=Path)
    evidence.add_argument("--contract-export", required=True, type=Path)
    evidence.add_argument("--tooling-root", required=True, type=Path)
    evidence.add_argument("--tooling-export", required=True, type=Path)
    evidence.add_argument("--input-root", required=True, type=Path)
    evidence.add_argument("--input-export", required=True, type=Path)
    binding = subcommands.add_parser("binding")
    binding.add_argument("--record", required=True, type=Path)
    freshness = subcommands.add_parser("freshness")
    freshness.add_argument("--external-surfaces", required=True, type=Path)
    freshness.add_argument("--surface-register", required=True, type=Path)
    freshness.add_argument("--applicability-decisions", required=True, type=Path)
    freshness.add_argument("--evaluation-time", required=True)
    freshness.add_argument("--evaluation-point", required=True, choices=["owner_acceptance", "pre_integration"])
    freshness.add_argument("--subject-commit", required=True)
    freshness.add_argument("--subject-tree", required=True)
    freshness.add_argument("--event", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    if not sys.flags.isolated:
        lib.fail("E_RUNTIME_ISOLATION", "invoke with python3 -I")
    args = parse_args()
    limits = lib.load_limits(Path(__file__).resolve().with_name("limits.json"))
    if args.command == "package":
        rows = verify_package(args.package, args.source_repository, args.source_tree, limits)
        if args.audit is not None:
            index = canonical_document(args.package / "index.json", limits)
            reconcile(
                rows, args.audit, limits, args.source_repository, args.source_commit,
                args.source_tree, args.source_export_sha256, args.input_export_sha256,
                index["scan_manifest_sha256"],
            )
    elif args.command == "evidence":
        verify_evidence_binding(
            args.record, args.package, args.source_root, args.source_export,
            args.base_root, args.base_export, args.contract_root, args.contract_export,
            args.tooling_root, args.tooling_export, args.input_root, args.input_export,
            limits,
        )
    elif args.command == "binding":
        verify_binding_record(args.record, limits)
    elif args.command == "freshness":
        verify_freshness(
            args.external_surfaces, args.surface_register, args.applicability_decisions,
            args.evaluation_time, args.evaluation_point, args.event,
            args.subject_commit, args.subject_tree, limits,
        )
    else:
        lib.fail("E_COMMAND", "unknown command")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lib.ProtocolError as error:
        print(f"{error.code}: {error.message}", file=sys.stderr)
        raise SystemExit(2)
