#!/usr/bin/env python3
"""Independently discover candidate legacy occurrences from an audit policy."""

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


def validate_policy(document: Any, limits: dict[str, int]) -> list[dict[str, Any]]:
    if not isinstance(document, dict):
        lib.fail("E_AUDIT_DOCUMENT", "audit policy must be an object")
    lib.require_keys(document, {"protocol_version", "independently_authored", "families"}, set(), "audit-policy")
    if document["protocol_version"] != lib.PROTOCOL_VERSION or document["independently_authored"] is not True:
        lib.fail("E_AUDIT_DOCUMENT", "audit policy must declare version and independent authorship")
    families = document["families"]
    if not isinstance(families, list) or len(families) > limits["max_audit_families"]:
        lib.fail("E_AUDIT_FAMILIES", "invalid audit family count")
    required = {"family_id", "kind", "literal", "namespace", "unit_kinds"}
    allowed_kinds = {"literal", "ascii_casefold_literal", "ascii_digit_suffix", "source_suffix", "path_component"}
    ids: set[str] = set()
    result: list[dict[str, Any]] = []
    for index, family in enumerate(families):
        label = f"families[{index}]"
        if not isinstance(family, dict):
            lib.fail("E_AUDIT_FAMILY", f"{label} must be an object")
        lib.require_keys(family, required, set(), label)
        family_id = family["family_id"]
        if not isinstance(family_id, str) or not family_id or family_id in ids:
            lib.fail("E_AUDIT_ID", f"invalid or duplicate family_id: {family_id!r}")
        ids.add(family_id)
        if family["kind"] not in allowed_kinds:
            lib.fail("E_AUDIT_KIND", f"{label} has unknown kind")
        if not isinstance(family["literal"], str) or not family["literal"]:
            lib.fail("E_AUDIT_LITERAL", f"{label} literal must be nonempty")
        if family["kind"] in {"ascii_casefold_literal", "ascii_digit_suffix"} and any(
            ord(char) > 127 for char in family["literal"]
        ):
            lib.fail("E_AUDIT_ASCII", f"{label} requires an ASCII literal")
        if not isinstance(family["namespace"], str) or not family["namespace"]:
            lib.fail("E_AUDIT_NAMESPACE", f"{label} namespace must be nonempty")
        units = family["unit_kinds"]
        if not isinstance(units, list) or not units or len(units) != len(set(units)):
            lib.fail("E_AUDIT_UNITS", f"{label} unit_kinds must be nonempty and unique")
        if any(unit not in lib.UNIT_KINDS for unit in units):
            lib.fail("E_AUDIT_UNITS", f"{label} has unknown unit kind")
        if family["kind"] in {"source_suffix", "path_component"} and units != ["path_component"]:
            lib.fail("E_AUDIT_UNITS", f"{label} path family must use only path_component")
        result.append(dict(family))
    return result


def ascii_casefold(value: str) -> str:
    return "".join(chr(ord(char) + 32) if "A" <= char <= "Z" else char for char in value)


def find_matches(value: str, family: dict[str, Any]) -> Iterator[tuple[int, int, str]]:
    literal = family["literal"]
    kind = family["kind"]
    if kind in {"literal", "source_suffix", "path_component"}:
        for start in lib.overlapping_positions(value, literal):
            yield (start, start + len(literal), value[start : start + len(literal)])
        return
    if kind == "ascii_casefold_literal":
        lowered = ascii_casefold(value)
        needle = ascii_casefold(literal)
        for start in lib.overlapping_positions(lowered, needle):
            yield (start, start + len(needle), value[start : start + len(needle)])
        return
    if kind == "ascii_digit_suffix":
        for start in lib.overlapping_positions(value, literal):
            end = start + len(literal)
            cursor = end
            while cursor < len(value) and "0" <= value[cursor] <= "9":
                cursor += 1
            if cursor > end:
                yield (start, cursor, value[start:cursor])
        return
    lib.fail("E_AUDIT_KIND", f"unsupported family kind: {kind}")


def discover(
    files: list[tuple[str, bytes]],
    families: list[dict[str, Any]],
    source_repository: str,
    source_tree: str,
    limits: dict[str, int],
) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    steps = 0

    def add(path: str, unit: str, locator: dict[str, Any], namespace: str, original: str, family_id: str) -> None:
        nonlocal steps
        key = lib.occurrence_key(source_repository, source_tree, path, unit, locator, namespace, original, limits)
        record = {
            "occurrence_key": key,
            "path": path,
            "unit_kind": unit,
            "locator": locator,
            "namespace": namespace,
            "original": original,
            "family_id": family_id,
        }
        prior = found.get(key)
        if prior is not None and prior != record:
            lib.fail("E_AUDIT_COLLISION", f"inconsistent duplicate discovery for {key}")
        found[key] = record
        steps += 1
        if steps > limits["max_processing_steps"]:
            lib.fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")

    for path, data in files:
        components = PurePosixPath(path).parts
        try:
            text = data.decode("utf-8", "strict")
        except UnicodeDecodeError:
            text = None

        for family in families:
            if "path_component" not in family["unit_kinds"]:
                continue
            if family["kind"] == "source_suffix":
                steps += len(path)
                if steps > limits["max_processing_steps"]:
                    lib.fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")
                if path.endswith(family["literal"]):
                    component_index = len(components) - 1
                    component = components[-1]
                    start = max(0, len(component) - len(family["literal"]))
                    locator = {"component_index": component_index, "match_index": 0}
                    add(path, "path_component", locator, family["namespace"], component[start:], family["family_id"])
            else:
                for component_index, component in enumerate(components):
                    steps += len(component)
                    if steps > limits["max_processing_steps"]:
                        lib.fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")
                    for match_index, (_start, _end, original) in enumerate(find_matches(component, family)):
                        locator = {"component_index": component_index, "match_index": match_index}
                        add(path, "path_component", locator, family["namespace"], original, family["family_id"])

        if text is not None:
            for family in families:
                for unit in family["unit_kinds"]:
                    if unit not in {"raw_text", "embedded_identity", "machine_identifier"}:
                        continue
                    steps += len(text)
                    if steps > limits["max_processing_steps"]:
                        lib.fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")
                    for start, end, original in find_matches(text, family):
                        locator = {
                            "byte_start": lib.utf8_byte_offset(text, start),
                            "byte_end": lib.utf8_byte_offset(text, end),
                        }
                        add(path, unit, locator, family["namespace"], original, family["family_id"])

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
            for unit, pointer, value in lib.walk_json_strings(parsed):
                for family in families:
                    if unit not in family["unit_kinds"]:
                        continue
                    steps += len(value)
                    if steps > limits["max_processing_steps"]:
                        lib.fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")
                    for match_index, (_start, _end, original) in enumerate(find_matches(value, family)):
                        locator = {"json_pointer": pointer, "match_index": match_index}
                        add(path, unit, locator, family["namespace"], original, family["family_id"])
    if len(found) > limits["max_occurrences"]:
        lib.fail("E_OCCURRENCE_COUNT", "max_occurrences exceeded")
    return [found[key] for key in sorted(found)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--policy", required=True, type=Path)
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
    families = validate_policy(lib.strict_json_file(args.policy, limits), limits)
    files = lib.snapshot_files(args.source_root, limits)
    manifest = lib.scan_manifest(files, limits)
    rows = discover(files, families, args.source_repository, args.source_tree, limits)
    if args.output.exists():
        lib.fail("E_OUTPUT_EXISTS", f"refusing to overwrite {args.output}")
    output = {
        "protocol_version": lib.PROTOCOL_VERSION,
        "source_repository": args.source_repository,
        "source_tree": args.source_tree,
        "scan_manifest_sha256": lib.scan_manifest_digest(manifest, limits),
        "scan_manifest": manifest,
        "candidate_count": len(rows),
        "candidates": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(lib.canonical_json_bytes(output, limits))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lib.ProtocolError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        raise SystemExit(2)
