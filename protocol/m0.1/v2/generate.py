#!/usr/bin/env python3
"""Expand reviewed compact rules into a deterministic occurrence package.

The generator authenticates source and input exports before discovery. Its
matching and structured traversal are implemented here and are not imported by
the independent auditor.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


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


def require_document(document: Any, payload_key: str) -> list[Any]:
    if not isinstance(document, dict):
        lib.fail("E_DOCUMENT_TYPE", f"{payload_key} document must be an object")
    lib.require_keys(document, {"protocol_version", payload_key}, set(), payload_key)
    if document["protocol_version"] != lib.PROTOCOL_VERSION or not isinstance(document[payload_key], list):
        lib.fail("E_DOCUMENT_TYPE", f"invalid {payload_key} document")
    return document[payload_key]


def validate_mappings(document: Any, limits: dict[str, int]) -> list[dict[str, Any]]:
    rows = require_document(document, "mappings")
    if len(rows) > limits["max_mappings"]:
        lib.fail("E_MAPPING_COUNT", "max_mappings exceeded")
    identifiers: set[str] = set()
    originals: set[tuple[str, str]] = set()
    destinations: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        label = f"mappings[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_MAPPING_TYPE", f"{label} must be an object")
        lib.require_keys(row, {"mapping_id", "namespace", "original", "canonical", "policy"}, set(), label)
        mapping_id = lib.require_identifier(row["mapping_id"], f"{label}.mapping_id")
        namespace = lib.require_identifier(row["namespace"], f"{label}.namespace")
        original = row["original"]
        policy = row["policy"]
        canonical = row["canonical"]
        if not isinstance(original, str) or not original:
            lib.fail("E_MAPPING_FIELD", f"{label}.original must be nonempty")
        if mapping_id in identifiers:
            lib.fail("E_MAPPING_ID", f"duplicate mapping_id: {mapping_id}")
        identifiers.add(mapping_id)
        source = (namespace, original)
        if source in originals:
            lib.fail("E_MAPPING_SOURCE", f"duplicate namespace/original: {source}")
        originals.add(source)
        if policy not in {"replace", "retain", "compatibility"}:
            lib.fail("E_MAPPING_POLICY", f"unknown policy: {policy}")
        if policy == "retain":
            if canonical is not None:
                lib.fail("E_MAPPING_CANONICAL", f"retained mapping {mapping_id} requires null canonical")
            effective = original
        else:
            if not isinstance(canonical, str) or not canonical:
                lib.fail("E_MAPPING_CANONICAL", f"mapping {mapping_id} requires canonical")
            effective = canonical
        destination = (namespace, effective)
        if destination in destinations:
            lib.fail("E_MAPPING_INJECTIVE", f"duplicate effective destination: {destination}")
        destinations.add(destination)
        result.append(dict(row))
    return result


def _validate_path_suffix(value: Any, limits: dict[str, int], label: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value or "\x00" in value:
        lib.fail("E_SELECTOR_PATH", f"invalid {label}")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value) or len(value.encode("utf-8")) > limits["max_path_bytes"]:
        lib.fail("E_SELECTOR_PATH", f"invalid {label}")
    return value


def validate_rules(
    document: Any,
    mappings: list[dict[str, Any]],
    limits: dict[str, int],
) -> list[dict[str, Any]]:
    rows = require_document(document, "rules")
    if len(rows) > limits["max_rules"]:
        lib.fail("E_RULE_COUNT", "max_rules exceeded")
    mapping_ids = {item["mapping_id"] for item in mappings}
    identifiers: set[str] = set()
    result: list[dict[str, Any]] = []
    required = {
        "rule_id", "selector", "expected_count", "role", "phase", "rationale",
        "representative_context", "boundary_context", "producer", "consumer",
        "support_policy", "validation_test_id", "historical_relationship",
    }
    selector_allowed = {
        "mapping_id", "unit_kind", "path_exact", "path_prefix", "path_suffix",
        "json_pointer_prefix",
    }
    for index, row in enumerate(rows):
        label = f"rules[{index}]"
        if not isinstance(row, dict):
            lib.fail("E_RULE_TYPE", f"{label} must be an object")
        lib.require_keys(row, required, set(), label)
        rule_id = lib.require_identifier(row["rule_id"], f"{label}.rule_id")
        if rule_id in identifiers:
            lib.fail("E_RULE_ID", f"duplicate rule_id: {rule_id}")
        identifiers.add(rule_id)
        selector = row["selector"]
        if not isinstance(selector, dict):
            lib.fail("E_SELECTOR_TYPE", f"{label}.selector must be an object")
        if set(selector) - selector_allowed:
            lib.fail("E_SELECTOR_FIELD", f"{label}.selector has unknown fields")
        if selector.get("mapping_id") not in mapping_ids:
            lib.fail("E_SELECTOR_MAPPING", f"{label} names unknown mapping")
        if selector.get("unit_kind") not in lib.UNIT_KINDS:
            lib.fail("E_SELECTOR_UNIT", f"{label} names unknown unit kind")
        path_fields = [name for name in ("path_exact", "path_prefix", "path_suffix") if name in selector]
        if len(path_fields) != 1:
            lib.fail("E_SELECTOR_PATH", f"{label} requires exactly one path selector")
        selected = selector[path_fields[0]]
        if path_fields[0] == "path_suffix":
            _validate_path_suffix(selected, limits, f"{label}.path_suffix")
        else:
            lib.validate_relpath(selected, limits)
        pointer = selector.get("json_pointer_prefix")
        if pointer is not None and not isinstance(pointer, str):
            lib.fail("E_SELECTOR_POINTER", f"{label}.json_pointer_prefix must be a string")
        if row["role"] not in lib.ROLES:
            lib.fail("E_RULE_ROLE", f"{label} has unknown role")
        if row["role"] == "historical" and path_fields[0] != "path_exact":
            lib.fail("E_HISTORICAL_BROAD", f"{label} historical rule requires path_exact")
        count = row["expected_count"]
        if not isinstance(count, int) or isinstance(count, bool) or count < 0 or count > limits["max_occurrences"]:
            lib.fail("E_RULE_COUNT", f"{label}.expected_count is invalid")
        lib.require_phase(row["phase"], f"{label}.phase")
        for name in ("rationale", "support_policy", "validation_test_id"):
            if not isinstance(row[name], str) or not row[name]:
                lib.fail("E_RULE_FIELD", f"{label}.{name} must be nonempty")
        for name in ("representative_context", "boundary_context"):
            if not isinstance(row[name], list) or not row[name] or any(not isinstance(item, str) or not item for item in row[name]):
                lib.fail("E_RULE_CONTEXT", f"{label}.{name} must be a nonempty string array")
        for name in ("producer", "consumer", "historical_relationship"):
            if row[name] is not None and (not isinstance(row[name], str) or not row[name]):
                lib.fail("E_RULE_FIELD", f"{label}.{name} must be nonempty string or null")
        result.append(dict(row))
    return result


def _literal_positions(text: str, needle: str, budget: Any) -> Iterator[int]:
    """Yield overlapping literal matches with every comparison charged."""
    if not needle:
        return
    table = [0] * len(needle)
    prefix = 0
    cursor = 1
    while cursor < len(needle):
        budget.charge(1)
        if needle[cursor] == needle[prefix]:
            prefix += 1
            table[cursor] = prefix
            cursor += 1
        elif prefix:
            prefix = table[prefix - 1]
        else:
            cursor += 1
    matched = 0
    for index, character in enumerate(text):
        while matched:
            budget.charge(1)
            if character == needle[matched]:
                break
            matched = table[matched - 1]
        if not matched:
            budget.charge(1)
            if character != needle[0]:
                continue
        matched += 1
        if matched == len(needle):
            yield index - len(needle) + 1
            matched = table[matched - 1]


def _byte_offsets(text: str) -> list[int]:
    offsets = [0]
    total = 0
    for character in text:
        total += len(character.encode("utf-8"))
        offsets.append(total)
    return offsets


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _walk_structured(value: Any, pointer: str = "") -> Iterator[tuple[str, str, str]]:
    if isinstance(value, dict):
        for key in sorted(value):
            child = pointer + "/" + _escape_pointer(key)
            yield ("structured_key", child, key)
            yield from _walk_structured(value[key], child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_structured(item, pointer + "/" + str(index))
    elif isinstance(value, str):
        yield ("structured_value", pointer, value)


def _raw_unit_kind(namespace: str) -> str:
    if namespace in EMBEDDED_NAMESPACES:
        return "embedded_identity"
    if namespace in MACHINE_NAMESPACES:
        return "machine_identifier"
    return "raw_text"


def _candidate(
    source_repository: str,
    source_tree: str,
    path: str,
    unit_kind: str,
    locator: dict[str, Any],
    namespace: str,
    original: str,
    mapping_id: str,
    file_sha: str,
    context_data: bytes,
    start: int,
    end: int,
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
        "context": lib.bounded_context_bytes(context_data, start, end, limits["max_context_bytes"]),
    }


def discover(
    files: list[tuple[str, bytes]],
    mappings: list[dict[str, Any]],
    source_repository: str,
    source_tree: str,
    limits: dict[str, int],
) -> list[dict[str, Any]]:
    budget = lib.WorkBudget(limits)
    candidates: list[dict[str, Any]] = []

    def append(item: dict[str, Any]) -> None:
        budget.add_occurrence()
        candidates.append(item)

    for path, data in files:
        file_sha = lib.sha256_hex(data)
        components = PurePosixPath(path).parts
        try:
            text = data.decode("utf-8", "strict")
        except UnicodeDecodeError:
            text = None
        text_offsets = _byte_offsets(text) if text is not None else None
        if text is not None:
            budget.charge(len(text))
        for mapping in mappings:
            original = mapping["original"]
            namespace = mapping["namespace"]
            mapping_id = mapping["mapping_id"]
            for component_index, component in enumerate(components):
                budget.charge(len(component))
                offsets = _byte_offsets(component)
                component_bytes = component.encode("utf-8")
                for position in _literal_positions(component, original, budget):
                    start, end = offsets[position], offsets[position + len(original)]
                    locator = {
                        "component_index": component_index,
                        "component_byte_start": start,
                        "component_byte_end": end,
                    }
                    append(
                        _candidate(
                            source_repository, source_tree, path, "path_component", locator,
                            namespace, original, mapping_id, file_sha, component_bytes, start, end, limits,
                        )
                    )
            if text is not None and text_offsets is not None:
                budget.charge(len(text))
                for position in _literal_positions(text, original, budget):
                    start, end = text_offsets[position], text_offsets[position + len(original)]
                    locator = {"byte_start": start, "byte_end": end}
                    append(
                        _candidate(
                            source_repository, source_tree, path, _raw_unit_kind(namespace), locator,
                            namespace, original, mapping_id, file_sha, data, start, end, limits,
                        )
                    )

        if text is not None and path.endswith(".json"):
            try:
                parsed = lib.source_json_strings(data, limits, path)
            except lib.ProtocolError:
                parsed = None
            if parsed is not None:
                for unit_kind, pointer, value in _walk_structured(parsed):
                    offsets = _byte_offsets(value)
                    value_bytes = value.encode("utf-8")
                    for mapping in mappings:
                        original = mapping["original"]
                        budget.charge(len(value))
                        for position in _literal_positions(value, original, budget):
                            start, end = offsets[position], offsets[position + len(original)]
                            locator = {
                                "json_pointer": pointer,
                                "value_byte_start": start,
                                "value_byte_end": end,
                            }
                            append(
                                _candidate(
                                    source_repository, source_tree, path, unit_kind, locator,
                                    mapping["namespace"], original, mapping["mapping_id"], file_sha,
                                    value_bytes, start, end, limits,
                                )
                            )
    return candidates


def _selector_matches(selector: dict[str, Any], item: dict[str, Any]) -> bool:
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
    limits: dict[str, int],
) -> list[dict[str, Any]]:
    budget = lib.WorkBudget(limits)
    mappings_by_id = {item["mapping_id"]: item for item in mappings}
    rules_by_unit: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for rule in rules:
        selector = rule["selector"]
        rules_by_unit.setdefault((selector["mapping_id"], selector["unit_kind"]), []).append(rule)
    selected_counts = {rule["rule_id"]: 0 for rule in rules}
    rows: list[dict[str, Any]] = []
    for item in candidates:
        possible = rules_by_unit.get((item["mapping_id"], item["unit_kind"]), [])
        budget.charge(len(possible))
        matched = [rule for rule in possible if _selector_matches(rule["selector"], item)]
        if not matched:
            lib.fail("E_UNCLASSIFIED", f"unclassified occurrence: {item['occurrence_key']}")
        if len(matched) != 1:
            lib.fail("E_MULTIPLE_CLASSIFICATION", f"multiple classifications: {item['occurrence_key']}")
        rule = matched[0]
        selected_counts[rule["rule_id"]] += 1
        mapping = mappings_by_id[item["mapping_id"]]
        budget.add_occurrence()
        rows.append(
            {
                "protocol_version": lib.PROTOCOL_VERSION,
                **item,
                "canonical": mapping["canonical"],
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
            lib.fail("E_EXPECTED_COUNT", f"{rule['rule_id']} expected {rule['expected_count']} but selected {actual}")
    return rows


def _identity_arguments(parser: argparse.ArgumentParser, prefix: str) -> None:
    parser.add_argument(f"--{prefix}-root", required=True, type=Path)
    parser.add_argument(f"--{prefix}-export", required=True, type=Path)
    parser.add_argument(f"--{prefix}-repository", required=True)
    parser.add_argument(f"--{prefix}-commit", required=True)
    parser.add_argument(f"--{prefix}-tree", required=True)
    parser.add_argument(f"--{prefix}-view-prefix", required=True)
    parser.add_argument(f"--{prefix}-view-tree", required=True)
    parser.add_argument(f"--{prefix}-fixture", action="store_true")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    _identity_arguments(parser, "source")
    _identity_arguments(parser, "input")
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    if not sys.flags.isolated:
        lib.fail("E_RUNTIME_ISOLATION", "invoke with python3 -I")
    args = parse_args()
    limits = lib.load_limits(Path(__file__).resolve().with_name("limits.json"))
    lib.require_root_source_view(
        args.source_view_prefix, args.source_tree, args.source_view_tree
    )
    _source_export, files = lib.verify_git_export(
        args.source_root, args.source_export, limits, args.source_repository,
        args.source_commit, args.source_tree, args.source_view_prefix,
        args.source_view_tree, args.source_fixture,
    )
    _input_export, input_files = lib.verify_git_export(
        args.input_root, args.input_export, limits, args.input_repository,
        args.input_commit, args.input_tree, args.input_view_prefix,
        args.input_view_tree, args.input_fixture,
    )
    inputs = dict(input_files)
    required_inputs = {"mappings.json", "classification-rules.json"}
    if not required_inputs.issubset(inputs):
        lib.fail("E_INPUT_SET", f"missing compact inputs: {sorted(required_inputs - set(inputs))}")
    mappings = validate_mappings(lib.strict_json_bytes(inputs["mappings.json"], limits, "mappings.json"), limits)
    rules = validate_rules(
        lib.strict_json_bytes(inputs["classification-rules.json"], limits, "classification-rules.json"),
        mappings,
        limits,
    )
    rows = classify(discover(files, mappings, args.source_repository, args.source_tree, limits), mappings, rules, limits)
    lib.write_package(rows, lib.scan_manifest(files, limits), args.output, limits)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lib.ProtocolError as error:
        print(f"{error.code}: {error.message}", file=sys.stderr)
        raise SystemExit(2)
