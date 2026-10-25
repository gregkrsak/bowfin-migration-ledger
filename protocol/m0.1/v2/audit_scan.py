#!/usr/bin/env python3
"""Independently discover legacy occurrences from a reviewed audit policy.

This scanner shares authenticated bytes and occurrence-key encoding with the
generator, but owns its traversal and match enumeration. It receives no mappings,
classification rules, canonical identities, roles, phases, or exemptions.
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


def validate_policy(document: Any, limits: dict[str, int]) -> list[dict[str, Any]]:
    if not isinstance(document, dict):
        lib.fail("E_AUDIT_DOCUMENT", "audit policy must be an object")
    lib.require_keys(document, {"protocol_version", "independently_authored", "families"}, set(), "audit-policy")
    if document["protocol_version"] != lib.PROTOCOL_VERSION or document["independently_authored"] is not True:
        lib.fail("E_AUDIT_DOCUMENT", "audit policy must declare version and independent authorship")
    families = document["families"]
    if not isinstance(families, list) or len(families) > limits["max_audit_families"]:
        lib.fail("E_AUDIT_FAMILIES", "invalid audit family count")
    allowed = {"literal", "ascii_casefold_literal", "ascii_digit_suffix", "source_suffix", "path_component"}
    identifiers: set[str] = set()
    result: list[dict[str, Any]] = []
    for index, family in enumerate(families):
        label = f"families[{index}]"
        if not isinstance(family, dict):
            lib.fail("E_AUDIT_FAMILY", f"{label} must be an object")
        lib.require_keys(family, {"family_id", "kind", "literal", "namespace", "unit_kinds"}, set(), label)
        family_id = lib.require_identifier(family["family_id"], f"{label}.family_id")
        if family_id in identifiers:
            lib.fail("E_AUDIT_ID", f"duplicate family_id: {family_id}")
        identifiers.add(family_id)
        if family["kind"] not in allowed:
            lib.fail("E_AUDIT_KIND", f"{label} has unknown kind")
        literal = family["literal"]
        if not isinstance(literal, str) or not literal:
            lib.fail("E_AUDIT_LITERAL", f"{label}.literal must be nonempty")
        if family["kind"] in {"ascii_casefold_literal", "ascii_digit_suffix"} and any(ord(char) > 127 for char in literal):
            lib.fail("E_AUDIT_ASCII", f"{label} requires an ASCII literal")
        lib.require_identifier(family["namespace"], f"{label}.namespace")
        units = family["unit_kinds"]
        if not isinstance(units, list) or not units or len(units) != len(set(units)):
            lib.fail("E_AUDIT_UNITS", f"{label}.unit_kinds must be nonempty and unique")
        if any(unit not in lib.UNIT_KINDS for unit in units):
            lib.fail("E_AUDIT_UNITS", f"{label} has unknown unit kind")
        if family["kind"] in {"source_suffix", "path_component"} and units != ["path_component"]:
            lib.fail("E_AUDIT_UNITS", f"{label} path family must use path_component only")
        result.append(dict(family))
    return result


def _ascii_lower(character: str) -> str:
    return chr(ord(character) + 32) if "A" <= character <= "Z" else character


def _kmp_positions(value: str, literal: str, fold_ascii: bool, budget: Any) -> Iterator[int]:
    """Yield overlapping matches with linear, comparison-level accounting."""
    def equal(left: str, right: str) -> bool:
        if fold_ascii:
            return _ascii_lower(left) == _ascii_lower(right)
        return left == right

    table = [0] * len(literal)
    budget.charge(len(literal))
    prefix = 0
    cursor = 1
    while cursor < len(literal):
        budget.charge(1)
        if equal(literal[cursor], literal[prefix]):
            prefix += 1
            table[cursor] = prefix
            cursor += 1
        elif prefix:
            prefix = table[prefix - 1]
        else:
            cursor += 1
    matched = 0
    for index, character in enumerate(value):
        while matched:
            budget.charge(1)
            if equal(character, literal[matched]):
                break
            matched = table[matched - 1]
        if not matched:
            budget.charge(1)
            if not equal(character, literal[0]):
                continue
        matched += 1
        if matched == len(literal):
            yield index - len(literal) + 1
            matched = table[matched - 1]


def _matches(value: str, family: dict[str, Any], budget: Any) -> Iterator[tuple[int, int, str]]:
    literal = family["literal"]
    kind = family["kind"]
    width = len(literal)
    positions = _kmp_positions(value, literal, kind == "ascii_casefold_literal", budget)
    if kind == "ascii_digit_suffix":
        for start in positions:
            cursor = start + width
            while cursor < len(value) and "0" <= value[cursor] <= "9":
                budget.charge(1)
                cursor += 1
            if cursor > start + width:
                budget.charge(cursor - start)
                yield (start, cursor, value[start:cursor])
        return
    for start in positions:
        budget.charge(width)
        yield (start, start + width, value[start : start + width])


def _offsets(value: str) -> list[int]:
    result = [0]
    total = 0
    for character in value:
        total += len(character.encode("utf-8"))
        result.append(total)
    return result


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _structured_units(value: Any) -> Iterator[tuple[str, str, str]]:
    stack: list[tuple[Any, str]] = [(value, "")]
    while stack:
        current, pointer = stack.pop()
        if isinstance(current, dict):
            keys = sorted(current, reverse=True)
            for key in keys:
                child = pointer + "/" + _pointer_escape(key)
                stack.append((current[key], child))
                stack.append((("__audit_key__", key), child))
        elif isinstance(current, tuple) and len(current) == 2 and current[0] == "__audit_key__":
            yield ("structured_key", pointer, current[1])
        elif isinstance(current, list):
            for index in range(len(current) - 1, -1, -1):
                stack.append((current[index], pointer + "/" + str(index)))
        elif isinstance(current, str):
            yield ("structured_value", pointer, current)


def discover(
    files: list[tuple[str, bytes]],
    families: list[dict[str, Any]],
    source_repository: str,
    source_tree: str,
    limits: dict[str, int],
) -> list[dict[str, Any]]:
    budget = lib.WorkBudget(limits)
    found: dict[str, dict[str, Any]] = {}

    def add(path: str, unit_kind: str, locator: dict[str, Any], namespace: str, original: str, family_id: str) -> None:
        budget.add_occurrence()
        key = lib.occurrence_key(
            source_repository, source_tree, path, unit_kind, locator, namespace, original, limits
        )
        record = {
            "occurrence_key": key,
            "path": path,
            "unit_kind": unit_kind,
            "locator": locator,
            "namespace": namespace,
            "original": original,
            "family_id": family_id,
        }
        prior = found.get(key)
        if prior is not None and prior != record:
            lib.fail("E_AUDIT_COLLISION", f"inconsistent duplicate discovery for {key}")
        found[key] = record

    for path, data in files:
        components = PurePosixPath(path).parts
        try:
            text = data.decode("utf-8", "strict")
        except UnicodeDecodeError:
            text = None
        if text is not None:
            budget.charge(len(text))
        text_offsets = _offsets(text) if text is not None else None
        for family in families:
            if "path_component" not in family["unit_kinds"]:
                continue
            if family["kind"] == "source_suffix":
                budget.charge(len(path))
                if path.endswith(family["literal"]):
                    component_index = len(components) - 1
                    component = components[-1]
                    start = len(component) - len(family["literal"])
                    offsets = _offsets(component)
                    locator = {
                        "component_index": component_index,
                        "component_byte_start": offsets[start],
                        "component_byte_end": offsets[len(component)],
                    }
                    add(path, "path_component", locator, family["namespace"], component[start:], family["family_id"])
            else:
                for component_index, component in enumerate(components):
                    budget.charge(len(component))
                    offsets = _offsets(component)
                    for start, end, original in _matches(component, family, budget):
                        locator = {
                            "component_index": component_index,
                            "component_byte_start": offsets[start],
                            "component_byte_end": offsets[end],
                        }
                        add(path, "path_component", locator, family["namespace"], original, family["family_id"])

        if text is not None and text_offsets is not None:
            for family in families:
                for unit_kind in family["unit_kinds"]:
                    if unit_kind not in {"raw_text", "embedded_identity", "machine_identifier"}:
                        continue
                    for start, end, original in _matches(text, family, budget):
                        locator = {"byte_start": text_offsets[start], "byte_end": text_offsets[end]}
                        add(path, unit_kind, locator, family["namespace"], original, family["family_id"])

        if text is not None and path.endswith(".json"):
            try:
                parsed = lib.source_json_strings(data, limits, path)
            except lib.ProtocolError:
                parsed = None
            if parsed is not None:
                for unit_kind, pointer, value in _structured_units(parsed):
                    budget.charge(1 + len(pointer) + len(value))
                    offsets = _offsets(value)
                    for family in families:
                        if unit_kind not in family["unit_kinds"]:
                            continue
                        for start, end, original in _matches(value, family, budget):
                            locator = {
                                "json_pointer": pointer,
                                "value_byte_start": offsets[start],
                                "value_byte_end": offsets[end],
                            }
                            add(path, unit_kind, locator, family["namespace"], original, family["family_id"])
    return [found[key] for key in sorted(found)]


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
    source_export, files = lib.verify_git_export(
        args.source_root, args.source_export, limits, args.source_repository,
        args.source_commit, args.source_tree, args.source_view_prefix,
        args.source_view_tree, args.source_fixture,
    )
    input_export, input_files = lib.verify_git_export(
        args.input_root, args.input_export, limits, args.input_repository,
        args.input_commit, args.input_tree, args.input_view_prefix,
        args.input_view_tree, args.input_fixture,
    )
    inputs = dict(input_files)
    if "audit-policy.json" not in inputs:
        lib.fail("E_INPUT_SET", "missing compact input: audit-policy.json")
    families = validate_policy(lib.strict_json_bytes(inputs["audit-policy.json"], limits, "audit-policy.json"), limits)
    manifest = lib.scan_manifest(files, limits)
    candidates = discover(files, families, args.source_repository, args.source_tree, limits)
    output = {
        "protocol_version": lib.PROTOCOL_VERSION,
        "source_repository": args.source_repository,
        "source_commit": args.source_commit,
        "source_tree": args.source_tree,
        "source_export_sha256": lib.export_digest(source_export, limits),
        "input_export_sha256": lib.export_digest(input_export, limits),
        "scan_manifest_sha256": lib.scan_manifest_digest(manifest, limits),
        "scan_manifest": manifest,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    lib.write_exclusive_document(args.output, output, limits, limits["max_audit_output_bytes"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lib.ProtocolError as error:
        print(f"{error.code}: {error.message}", file=sys.stderr)
        raise SystemExit(2)
