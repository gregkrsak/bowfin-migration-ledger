#!/usr/bin/env python3
"""Expand reviewed compact rules into a deterministic occurrence package."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path, PurePosixPath
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

EMBEDDED_NAMESPACES = frozenset(
    {"engineering_decision", "language_decision", "project_control", "test_identity"}
)
MACHINE_NAMESPACES = frozenset(
    {"machine_namespace", "compiler_identity", "environment_variable"}
)


def validate_mappings(document: Any, limits: dict[str, int]) -> list[dict[str, Any]]:
    rows = lib.require_protocol_document(document, "mappings")
    if len(rows) > limits["max_mappings"]:
        lib.fail("E_MAPPING_COUNT", "max_mappings exceeded")
    ids: set[str] = set()
    originals: set[tuple[str, str]] = set()
    canonicals: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    required = {"mapping_id", "namespace", "original", "policy"}
    optional = {"canonical"}
    for index, row in enumerate(rows):
        label = f"mappings[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_MAPPING_TYPE", f"{label} must be an object")
        lib.require_keys(row, required, optional, label)
        mapping_id = row["mapping_id"]
        namespace = row["namespace"]
        original = row["original"]
        policy = row["policy"]
        canonical = row.get("canonical")
        if not all(isinstance(value, str) and value for value in (mapping_id, namespace, original, policy)):
            lib.fail("E_MAPPING_FIELD", f"{label} has an empty or non-string field")
        if mapping_id in ids:
            lib.fail("E_MAPPING_ID", f"duplicate mapping_id: {mapping_id}")
        ids.add(mapping_id)
        source_key = (namespace, original)
        if source_key in originals:
            lib.fail("E_MAPPING_SOURCE", f"duplicate namespace/original: {source_key}")
        originals.add(source_key)
        if policy not in {"replace", "retain", "compatibility"}:
            lib.fail("E_MAPPING_POLICY", f"unknown policy: {policy}")
        if policy == "retain":
            if canonical is not None:
                lib.fail("E_MAPPING_CANONICAL", f"retained mapping {mapping_id} must use null canonical")
        else:
            if not isinstance(canonical, str) or not canonical:
                lib.fail("E_MAPPING_CANONICAL", f"mapping {mapping_id} requires canonical")
            target_key = (namespace, canonical)
            if target_key in canonicals:
                lib.fail("E_MAPPING_INJECTIVE", f"duplicate namespace/canonical: {target_key}")
            canonicals.add(target_key)
        result.append(dict(row))
    return result


def validate_rules(
    document: Any, mappings: list[dict[str, Any]], limits: dict[str, int]
) -> list[dict[str, Any]]:
    rows = lib.require_protocol_document(document, "rules")
    if len(rows) > limits["max_rules"]:
        lib.fail("E_RULE_COUNT", "max_rules exceeded")
    mapping_ids = {item["mapping_id"] for item in mappings}
    ids: set[str] = set()
    required = {
        "rule_id",
        "selector",
        "expected_count",
        "role",
        "phase",
        "rationale",
        "representative_context",
        "boundary_context",
        "producer",
        "consumer",
        "support_policy",
        "validation_test_id",
        "historical_relationship",
    }
    selector_allowed = {
        "mapping_id",
        "unit_kind",
        "path_exact",
        "path_prefix",
        "path_suffix",
        "json_pointer_prefix",
    }
    result: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        label = f"rules[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_RULE_TYPE", f"{label} must be an object")
        lib.require_keys(row, required, set(), label)
        rule_id = row["rule_id"]
        if not isinstance(rule_id, str) or not rule_id or rule_id in ids:
            lib.fail("E_RULE_ID", f"invalid or duplicate rule_id: {rule_id!r}")
        ids.add(rule_id)
        selector = row["selector"]
        if not isinstance(selector, dict):
            lib.fail("E_SELECTOR_TYPE", f"{label}.selector must be an object")
        unknown = set(selector) - selector_allowed
        if unknown:
            lib.fail("E_SELECTOR_FIELD", f"{label}.selector unknown fields: {sorted(unknown)}")
        if selector.get("mapping_id") not in mapping_ids:
            lib.fail("E_SELECTOR_MAPPING", f"{label} names unknown mapping")
        if selector.get("unit_kind") not in lib.UNIT_KINDS:
            lib.fail("E_SELECTOR_UNIT", f"{label} names unknown unit kind")
        path_fields = [name for name in ("path_exact", "path_prefix", "path_suffix") if name in selector]
        if len(path_fields) != 1:
            lib.fail("E_SELECTOR_PATH", f"{label} requires exactly one path selector")
        selected_path = selector[path_fields[0]]
        if not isinstance(selected_path, str) or not selected_path:
            lib.fail("E_SELECTOR_PATH", f"{label} has empty path selector")
        if path_fields[0] != "path_suffix":
            lib.validate_relpath(selected_path, limits)
        elif (
            selected_path.startswith("/") or "\\" in selected_path or "\x00" in selected_path
            or any(0xD800 <= ord(char) <= 0xDFFF for char in selected_path)
            or len(selected_path.encode("utf-8")) > limits["max_path_bytes"]
        ):
            lib.fail("E_SELECTOR_PATH", f"{label} has invalid path suffix")
        pointer_prefix = selector.get("json_pointer_prefix")
        if pointer_prefix is not None and not isinstance(pointer_prefix, str):
            lib.fail("E_SELECTOR_POINTER", f"{label}.json_pointer_prefix must be a string")
        if row["role"] not in lib.ROLES:
            lib.fail("E_RULE_ROLE", f"{label} has unknown role")
        if row["role"] == "historical" and path_fields[0] != "path_exact":
            lib.fail("E_HISTORICAL_BROAD", f"{label} historical rule requires path_exact")
        if not isinstance(row["expected_count"], int) or isinstance(row["expected_count"], bool) or row["expected_count"] < 0:
            lib.fail("E_RULE_COUNT", f"{label}.expected_count must be nonnegative integer")
        for name in ("rationale", "phase", "support_policy", "validation_test_id"):
            if not isinstance(row[name], str) or not row[name]:
                lib.fail("E_RULE_FIELD", f"{label}.{name} must be nonempty")
        phase = row["phase"]
        phase_parts = phase.split(".")
        if (
            len(phase_parts) > 2 or phase_parts[0] not in {f"M{number}" for number in range(8)}
            or (len(phase_parts) == 2 and (not phase_parts[1].isdigit() or not phase_parts[1]))
        ):
            lib.fail("E_RULE_PHASE", f"{label}.phase is invalid")
        for name in ("representative_context", "boundary_context"):
            if not isinstance(row[name], list) or not row[name] or any(not isinstance(x, str) or not x for x in row[name]):
                lib.fail("E_RULE_CONTEXT", f"{label}.{name} must be a nonempty string array")
        for name in ("producer", "consumer", "historical_relationship"):
            if row[name] is not None and not isinstance(row[name], str):
                lib.fail("E_RULE_FIELD", f"{label}.{name} must be string or null")
        result.append(dict(row))
    return result


def raw_unit_kind(namespace: str) -> str:
    if namespace in EMBEDDED_NAMESPACES:
        return "embedded_identity"
    if namespace in MACHINE_NAMESPACES:
        return "machine_identifier"
    return "raw_text"


def discover(
    files: list[tuple[str, bytes]],
    mappings: list[dict[str, Any]],
    source_repository: str,
    source_tree: str,
    limits: dict[str, int],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    steps = 0
    for path, data in files:
        file_sha = lib.sha256_hex(data)
        components = PurePosixPath(path).parts
        try:
            text = data.decode("utf-8", "strict")
        except UnicodeDecodeError:
            text = None
        for mapping in mappings:
            original = mapping["original"]
            namespace = mapping["namespace"]
            mapping_id = mapping["mapping_id"]
            for component_index, component in enumerate(components):
                steps += len(component)
                if steps > limits["max_processing_steps"]:
                    lib.fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")
                for match_index, position in enumerate(lib.overlapping_positions(component, original)):
                    locator = {"component_index": component_index, "match_index": match_index}
                    candidates.append(
                        candidate(
                            source_repository, source_tree, path, "path_component", locator,
                            namespace, original, mapping_id, file_sha, component, position,
                            position + len(original), limits,
                        )
                    )
                    steps += 1
            if text is not None:
                kind = raw_unit_kind(namespace)
                steps += len(text)
                if steps > limits["max_processing_steps"]:
                    lib.fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")
                for position in lib.overlapping_positions(text, original):
                    start = lib.utf8_byte_offset(text, position)
                    end = lib.utf8_byte_offset(text, position + len(original))
                    locator = {"byte_start": start, "byte_end": end}
                    candidates.append(
                        candidate(
                            source_repository, source_tree, path, kind, locator,
                            namespace, original, mapping_id, file_sha, text, position,
                            position + len(original), limits,
                        )
                    )
                    steps += 1
            if steps > limits["max_processing_steps"]:
                lib.fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")

        if text is not None and path.endswith(".json"):
            try:
                parsed = lib.source_json_strings(data, limits, path)
            except lib.ProtocolError as exc:
                if exc.code not in {
                    "E_SOURCE_JSON_BOM", "E_SOURCE_JSON_SYNTAX", "E_JSON_DUPLICATE_KEY",
                    "E_JSON_CONSTANT", "E_JSON_DEPTH", "E_JSON_NFC", "E_JSON_STRING",
                    "E_JSON_SURROGATE",
                }:
                    raise
                parsed = None
            if parsed is None:
                continue
            for unit_kind, pointer, value in lib.walk_json_strings(parsed):
                for mapping in mappings:
                    original = mapping["original"]
                    steps += len(value)
                    if steps > limits["max_processing_steps"]:
                        lib.fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")
                    for match_index, position in enumerate(lib.overlapping_positions(value, original)):
                        locator = {"json_pointer": pointer, "match_index": match_index}
                        candidates.append(
                            candidate(
                                source_repository, source_tree, path, unit_kind, locator,
                                mapping["namespace"], original, mapping["mapping_id"], file_sha,
                                value, position, position + len(original), limits,
                            )
                        )
                        steps += 1
                        if steps > limits["max_processing_steps"]:
                            lib.fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")
    if len(candidates) > limits["max_occurrences"]:
        lib.fail("E_OCCURRENCE_COUNT", "max_occurrences exceeded")
    return candidates


def candidate(
    source_repository: str,
    source_tree: str,
    path: str,
    unit_kind: str,
    locator: dict[str, Any],
    namespace: str,
    original: str,
    mapping_id: str,
    file_sha: str,
    context_text: str,
    context_start: int,
    context_end: int,
    limits: dict[str, int],
) -> dict[str, Any]:
    return {
        "occurrence_key": lib.occurrence_key(
            source_repository, source_tree, path, unit_kind, locator, namespace, original, limits
        ),
        "path": path,
        "unit_kind": unit_kind,
        "locator": locator,
        "source_file_sha256": file_sha,
        "namespace": namespace,
        "original": original,
        "mapping_id": mapping_id,
        "context": lib.bounded_context(
            context_text, context_start, context_end, limits["max_context_codepoints"]
        ),
    }


def selector_matches(selector: dict[str, Any], item: dict[str, Any]) -> bool:
    if selector["mapping_id"] != item["mapping_id"] or selector["unit_kind"] != item["unit_kind"]:
        return False
    path = item["path"]
    if "path_exact" in selector and path != selector["path_exact"]:
        return False
    if "path_prefix" in selector and not (path == selector["path_prefix"] or path.startswith(selector["path_prefix"] + "/")):
        return False
    if "path_suffix" in selector and not path.endswith(selector["path_suffix"]):
        return False
    pointer_prefix = selector.get("json_pointer_prefix")
    if pointer_prefix is not None:
        pointer = item["locator"].get("json_pointer")
        if not isinstance(pointer, str) or not pointer.startswith(pointer_prefix):
            return False
    return True


def classify(
    candidates: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
    rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    mappings_by_id = {item["mapping_id"]: item for item in mappings}
    selected_counts = {rule["rule_id"]: 0 for rule in rules}
    rows: list[dict[str, Any]] = []
    for item in candidates:
        matched = [rule for rule in rules if selector_matches(rule["selector"], item)]
        if not matched:
            lib.fail("E_UNCLASSIFIED", f"unclassified occurrence: {item['occurrence_key']}")
        if len(matched) != 1:
            ids = [rule["rule_id"] for rule in matched]
            lib.fail("E_MULTIPLE_CLASSIFICATION", f"{item['occurrence_key']} matched {ids}")
        rule = matched[0]
        selected_counts[rule["rule_id"]] += 1
        mapping = mappings_by_id[item["mapping_id"]]
        rows.append(
            {
                "protocol_version": lib.PROTOCOL_VERSION,
                **item,
                "canonical": mapping.get("canonical"),
                "role": rule["role"],
                "phase": rule["phase"],
                "producer": rule["producer"],
                "consumer": rule["consumer"],
                "support_policy": rule["support_policy"],
                "validation_test_id": rule["validation_test_id"],
                "historical_relationship": rule["historical_relationship"],
                "rule_id": rule["rule_id"],
            }
        )
    for rule in rules:
        actual = selected_counts[rule["rule_id"]]
        if actual != rule["expected_count"]:
            lib.fail(
                "E_EXPECTED_COUNT",
                f"{rule['rule_id']} expected {rule['expected_count']} but selected {actual}",
            )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--mappings", required=True, type=Path)
    parser.add_argument("--rules", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limits", type=Path, default=Path(__file__).resolve().with_name("limits.json"))
    return parser.parse_args()


def main() -> int:
    if not sys.flags.isolated:
        lib.fail("E_RUNTIME_ISOLATION", "invoke with python3 -I")
    args = parse_args()
    if len(args.source_tree) != 40 or any(char not in "0123456789abcdef" for char in args.source_tree):
        lib.fail("E_SOURCE_TREE", "source tree must be lowercase 40-hex SHA-1")
    limits = lib.load_limits(args.limits)
    mappings = validate_mappings(lib.strict_json_file(args.mappings, limits), limits)
    rules = validate_rules(lib.strict_json_file(args.rules, limits), mappings, limits)
    files = lib.snapshot_files(args.source_root, limits)
    rows = classify(
        discover(files, mappings, args.source_repository, args.source_tree, limits),
        mappings,
        rules,
    )
    lib.write_package(rows, lib.scan_manifest(files, limits), args.output, limits)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lib.ProtocolError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        raise SystemExit(2)
