#!/usr/bin/env python3
"""Shared bounded primitives for the proposed M0.1 v2 protocol.

This module deliberately contains no classification-rule matching and no audit
discovery policy. Those algorithms remain separate in generate.py and
audit_scan.py. Do not execute this candidate before exact-revision review and
owner authorization.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, NoReturn


PROTOCOL_VERSION = "m0.1-v2"
UNIT_KINDS = frozenset(
    {
        "path_component",
        "raw_text",
        "structured_key",
        "structured_value",
        "embedded_identity",
        "machine_identifier",
    }
)
ROLES = frozenset({"live", "compatibility", "historical"})
ARCHIVE_PREFIX = PurePosixPath("archive/unaccepted")


class ProtocolError(Exception):
    """A stable, fail-closed protocol error."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def fail(code: str, message: str) -> NoReturn:
    raise ProtocolError(code, message)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("E_JSON_DUPLICATE_KEY", f"duplicate key {key!r}")
        result[key] = value
    return result


def _no_float(value: str) -> Any:
    fail("E_JSON_FLOAT", f"floating-point number is forbidden: {value}")


def _no_constant(value: str) -> Any:
    fail("E_JSON_CONSTANT", f"non-finite number is forbidden: {value}")


def strict_json_bytes(data: bytes, limits: dict[str, int], label: str) -> Any:
    if len(data) > limits["max_input_file_bytes"]:
        fail("E_INPUT_SIZE", f"{label} exceeds max_input_file_bytes")
    if data.startswith(b"\xef\xbb\xbf"):
        fail("E_JSON_BOM", f"{label} begins with a UTF-8 BOM")
    try:
        text = data.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        fail("E_JSON_UTF8", f"{label}: {exc}")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_float=_no_float,
            parse_constant=_no_constant,
        )
    except ProtocolError:
        raise
    except json.JSONDecodeError as exc:
        fail("E_JSON_SYNTAX", f"{label}: {exc}")
    validate_json_value(value, limits)
    return value


def strict_json_file(path: Path, limits: dict[str, int]) -> Any:
    return strict_json_bytes(read_bounded_file(path, limits["max_input_file_bytes"]), limits, str(path))


def source_json_strings(data: bytes, limits: dict[str, int], label: str) -> Any:
    """Parse source JSON for string discovery without importing numeric semantics.

    Protocol documents forbid floats and negative integers. Source files do not.
    Because occurrence discovery only traverses object keys and string values,
    every source number is replaced by zero while duplicate keys, constants,
    encoding, normalization, depth, and size remain fail-closed.
    """
    if len(data) > limits["max_source_file_bytes"]:
        fail("E_FILE_SIZE", f"{label} exceeds max_source_file_bytes")
    if data.startswith(b"\xef\xbb\xbf"):
        fail("E_SOURCE_JSON_BOM", f"{label} begins with a UTF-8 BOM")
    try:
        text = data.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        fail("E_SOURCE_JSON_UTF8", f"{label}: {exc}")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_int=lambda _value: 0,
            parse_float=lambda _value: 0,
            parse_constant=_no_constant,
        )
    except ProtocolError:
        raise
    except json.JSONDecodeError as exc:
        fail("E_SOURCE_JSON_SYNTAX", f"{label}: {exc}")
    validate_json_value(value, limits)
    return value


def validate_json_value(value: Any, limits: dict[str, int], depth: int = 0) -> None:
    if depth > limits["max_json_depth"]:
        fail("E_JSON_DEPTH", "maximum JSON nesting depth exceeded")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < 0 or value > limits["max_json_integer"]:
            fail("E_JSON_INTEGER", f"integer outside accepted range: {value}")
        return
    if isinstance(value, float):
        fail("E_JSON_FLOAT", "floating-point values are forbidden")
    if isinstance(value, str):
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            fail("E_JSON_SURROGATE", "lone surrogate is forbidden")
        if len(value.encode("utf-8", "strict")) > limits["max_string_bytes"]:
            fail("E_JSON_STRING", "string exceeds max_string_bytes")
        if unicodedata.normalize("NFC", value) != value:
            fail("E_JSON_NFC", "string is not NFC-normalized")
        return
    if isinstance(value, list):
        for item in value:
            validate_json_value(item, limits, depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                fail("E_JSON_KEY", "object key is not a string")
            validate_json_value(key, limits, depth + 1)
            validate_json_value(item, limits, depth + 1)
        return
    fail("E_JSON_TYPE", f"unsupported JSON value type: {type(value).__name__}")


def canonical_json_bytes(value: Any, limits: dict[str, int], trailing_lf: bool = True) -> bytes:
    validate_json_value(value, limits)
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return encoded + (b"\n" if trailing_lf else b"")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bounded_file(path: Path, maximum: int) -> bytes:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        fail("E_FILE_READ", f"cannot stat {path}: {exc}")
    if stat.S_ISLNK(mode):
        fail("E_SYMLINK", f"symlink is forbidden: {path}")
    if not stat.S_ISREG(mode):
        fail("E_SPECIAL_FILE", f"not a regular file: {path}")
    size = path.stat().st_size
    if size > maximum:
        fail("E_FILE_SIZE", f"{path} exceeds {maximum} bytes")
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail("E_FILE_READ", f"cannot read {path}: {exc}")
    if len(data) != size:
        fail("E_FILE_CHANGED", f"size changed while reading {path}")
    return data


def require_keys(obj: dict[str, Any], required: set[str], optional: set[str], label: str) -> None:
    missing = sorted(required - obj.keys())
    unknown = sorted(obj.keys() - required - optional)
    if missing:
        fail("E_FIELD_MISSING", f"{label} missing fields: {missing}")
    if unknown:
        fail("E_FIELD_UNKNOWN", f"{label} unknown fields: {unknown}")


def require_protocol_document(obj: Any, payload_key: str) -> list[Any]:
    if not isinstance(obj, dict):
        fail("E_DOCUMENT_TYPE", "protocol document must be an object")
    require_keys(obj, {"protocol_version", payload_key}, set(), payload_key)
    if obj["protocol_version"] != PROTOCOL_VERSION:
        fail("E_PROTOCOL_VERSION", f"expected {PROTOCOL_VERSION}")
    payload = obj[payload_key]
    if not isinstance(payload, list):
        fail("E_DOCUMENT_TYPE", f"{payload_key} must be an array")
    return payload


def load_limits(path: Path) -> dict[str, int]:
    provisional = {
        "max_input_file_bytes": 1024 * 1024,
        "max_json_depth": 32,
        "max_json_integer": 9007199254740991,
        "max_string_bytes": 1024 * 1024,
    }
    obj = strict_json_file(path, provisional)
    if not isinstance(obj, dict) or obj.get("protocol_version") != PROTOCOL_VERSION:
        fail("E_LIMITS", "invalid limits document")
    required = {
        "max_audit_families",
        "max_chunk_bytes",
        "max_chunks",
        "max_context_codepoints",
        "max_generated_bytes",
        "max_input_file_bytes",
        "max_json_depth",
        "max_json_integer",
        "max_mappings",
        "max_occurrences",
        "max_path_bytes",
        "max_processing_steps",
        "max_row_bytes",
        "max_rows_per_chunk",
        "max_rules",
        "max_source_file_bytes",
        "max_source_files",
        "max_string_bytes",
        "max_total_source_bytes",
        "protocol_version",
    }
    if set(obj) != required:
        fail("E_LIMITS", "limits fields do not match the normative set")
    result: dict[str, int] = {}
    for key, value in obj.items():
        if key == "protocol_version":
            continue
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            fail("E_LIMITS", f"{key} must be a positive integer")
        result[key] = value
    return result


def validate_relpath(raw: str, limits: dict[str, int]) -> PurePosixPath:
    if not isinstance(raw, str) or not raw:
        fail("E_PATH", "path must be a nonempty string")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in raw):
        fail("E_PATH_UTF8", f"path is not valid UTF-8: {raw!r}")
    if unicodedata.normalize("NFC", raw) != raw:
        fail("E_PATH_NFC", f"path is not NFC: {raw!r}")
    if len(raw.encode("utf-8")) > limits["max_path_bytes"]:
        fail("E_PATH_SIZE", f"path exceeds max_path_bytes: {raw!r}")
    if "\\" in raw or "\x00" in raw or raw.startswith("/"):
        fail("E_PATH", f"invalid path spelling: {raw!r}")
    path = PurePosixPath(raw)
    if any(part in {"", ".", ".."} for part in path.parts):
        fail("E_PATH", f"dot or empty component is forbidden: {raw!r}")
    if path == PurePosixPath(".git") or ".git" in path.parts:
        fail("E_GIT_METADATA", f"Git metadata is forbidden: {raw}")
    if path == ARCHIVE_PREFIX or ARCHIVE_PREFIX in path.parents:
        fail("E_ARCHIVE_DEPENDENCY", f"unaccepted archive path is forbidden: {raw}")
    return path


def snapshot_files(root: Path, limits: dict[str, int]) -> list[tuple[str, bytes]]:
    try:
        root_mode = root.lstat().st_mode
    except OSError as exc:
        fail("E_SOURCE_ROOT", f"cannot stat source root: {exc}")
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        fail("E_SOURCE_ROOT", "source root must be a non-symlink directory")

    records: list[tuple[str, bytes]] = []
    total = 0
    for directory, names, filenames in os.walk(root, topdown=True, followlinks=False):
        names.sort()
        filenames.sort()
        directory_path = Path(directory)
        for name in list(names):
            child = directory_path / name
            mode = child.lstat().st_mode
            if stat.S_ISLNK(mode):
                fail("E_SYMLINK", f"symlink directory is forbidden: {child}")
            if not stat.S_ISDIR(mode):
                fail("E_SPECIAL_FILE", f"special directory entry: {child}")
            rel = child.relative_to(root).as_posix()
            validate_relpath(rel, limits)
        for name in filenames:
            child = directory_path / name
            rel = child.relative_to(root).as_posix()
            validate_relpath(rel, limits)
            data = read_bounded_file(child, limits["max_source_file_bytes"])
            total += len(data)
            if total > limits["max_total_source_bytes"]:
                fail("E_SOURCE_TOTAL", "source snapshot exceeds max_total_source_bytes")
            records.append((rel, data))
            if len(records) > limits["max_source_files"]:
                fail("E_SOURCE_FILES", "source snapshot exceeds max_source_files")
    return records


def scan_manifest(files: list[tuple[str, bytes]], limits: dict[str, int]) -> list[dict[str, Any]]:
    """Describe every source file, including files that cannot yield text units."""
    manifest: list[dict[str, Any]] = []
    for path, data in sorted(files, key=lambda item: item[0].encode("utf-8")):
        try:
            data.decode("utf-8", "strict")
            encoding = "utf8"
        except UnicodeDecodeError:
            encoding = "non_utf8"
        structured = "not_json"
        structured_error = None
        if path.endswith(".json"):
            if encoding == "non_utf8":
                structured = "unavailable_non_utf8"
            else:
                try:
                    source_json_strings(data, limits, path)
                    structured = "valid_json"
                except ProtocolError as exc:
                    structured = "invalid_json"
                    structured_error = exc.code
        manifest.append(
            {
                "path": path,
                "sha256": sha256_hex(data),
                "byte_count": len(data),
                "text_status": encoding,
                "structured_status": structured,
                "structured_error": structured_error,
            }
        )
    return manifest


def scan_manifest_digest(manifest: list[dict[str, Any]], limits: dict[str, int]) -> str:
    document = {"protocol_version": PROTOCOL_VERSION, "files": manifest}
    return sha256_hex(canonical_json_bytes(document, limits))


def json_pointer_escape(text: str) -> str:
    return text.replace("~", "~0").replace("/", "~1")


def walk_json_strings(value: Any, pointer: str = "") -> Iterator[tuple[str, str, str]]:
    if isinstance(value, dict):
        for key in sorted(value):
            child_pointer = pointer + "/" + json_pointer_escape(key)
            yield ("structured_key", child_pointer, key)
            yield from walk_json_strings(value[key], child_pointer)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_json_strings(item, pointer + "/" + str(index))
    elif isinstance(value, str):
        yield ("structured_value", pointer, value)


def overlapping_positions(haystack: str, needle: str) -> Iterator[int]:
    position = 0
    while True:
        found = haystack.find(needle, position)
        if found < 0:
            return
        yield found
        position = found + 1


def utf8_byte_offset(text: str, codepoint_offset: int) -> int:
    return len(text[:codepoint_offset].encode("utf-8"))


def occurrence_key(
    source_repository: str,
    source_tree: str,
    path: str,
    unit_kind: str,
    locator: dict[str, Any],
    namespace: str,
    original: str,
    limits: dict[str, int],
) -> str:
    if unit_kind not in UNIT_KINDS:
        fail("E_UNIT_KIND", f"unknown unit kind: {unit_kind}")
    identity = [source_repository, source_tree, path, unit_kind, locator, namespace, original]
    digest = sha256_hex(canonical_json_bytes(identity, limits, trailing_lf=False))
    return "sha256:" + digest


def bounded_context(text: str, start: int, end: int, maximum: int) -> str:
    half = maximum // 2
    left = max(0, start - half)
    right = min(len(text), end + half)
    value = text[left:right]
    if left:
        value = "…" + value
    if right < len(text):
        value += "…"
    return value[:maximum]


def aggregate_digest(descriptors: list[dict[str, Any]]) -> str:
    payload = bytearray()
    for descriptor in descriptors:
        fields = (
            descriptor["path"],
            descriptor["sha256"],
            str(descriptor["byte_count"]),
            str(descriptor["row_count"]),
            descriptor["first_key"],
            descriptor["last_key"],
        )
        payload.extend("\x00".join(fields).encode("utf-8") + b"\n")
    return sha256_hex(bytes(payload))


def summary_for(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def counts(field: str) -> dict[str, int]:
        return dict(sorted(Counter(str(row[field]) for row in rows).items()))

    return {
        "protocol_version": PROTOCOL_VERSION,
        "total_occurrences": len(rows),
        "by_namespace": counts("namespace"),
        "by_role": counts("role"),
        "by_phase": counts("phase"),
        "by_unit_kind": counts("unit_kind"),
    }


def ensure_empty_destination(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            fail("E_OUTPUT", "output destination must be a directory")
        if any(path.iterdir()):
            fail("E_OUTPUT_NOT_EMPTY", f"output destination is not empty: {path}")
    else:
        path.mkdir(parents=True, mode=0o755)


def write_package(
    rows: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    output: Path,
    limits: dict[str, int],
) -> None:
    if len(rows) > limits["max_occurrences"]:
        fail("E_OCCURRENCE_COUNT", "max_occurrences exceeded")
    sorted_rows = sorted(rows, key=lambda row: row["occurrence_key"].encode("utf-8"))
    keys = [row["occurrence_key"] for row in sorted_rows]
    if len(keys) != len(set(keys)):
        fail("E_OCCURRENCE_DUPLICATE", "duplicate occurrence key")

    ensure_empty_destination(output)
    temporary = output.parent / (output.name + ".tmp-m01v2")
    if temporary.exists():
        fail("E_OUTPUT_TEMP", f"temporary output already exists: {temporary}")
    temporary.mkdir(mode=0o700)
    occurrence_dir = temporary / "occurrences"
    occurrence_dir.mkdir()
    descriptors: list[dict[str, Any]] = []
    total_generated = 0
    try:
        chunk_rows: list[bytes] = []
        chunk_keys: list[str] = []
        chunk_bytes = 0

        def flush() -> None:
            nonlocal chunk_rows, chunk_keys, chunk_bytes, total_generated
            if not chunk_rows:
                return
            number = len(descriptors)
            if number >= limits["max_chunks"]:
                fail("E_CHUNK_COUNT", "max_chunks exceeded")
            relative = f"occurrences/{number:04d}.jsonl"
            data = b"".join(chunk_rows)
            (temporary / relative).write_bytes(data)
            descriptors.append(
                {
                    "path": relative,
                    "sha256": sha256_hex(data),
                    "byte_count": len(data),
                    "row_count": len(chunk_rows),
                    "first_key": chunk_keys[0],
                    "last_key": chunk_keys[-1],
                }
            )
            total_generated += len(data)
            chunk_rows = []
            chunk_keys = []
            chunk_bytes = 0

        for row in sorted_rows:
            encoded = canonical_json_bytes(row, limits)
            if len(encoded) > limits["max_row_bytes"]:
                fail("E_ROW_SIZE", f"row exceeds max_row_bytes: {row.get('occurrence_key')}")
            if chunk_rows and (
                len(chunk_rows) >= limits["max_rows_per_chunk"]
                or chunk_bytes + len(encoded) > limits["max_chunk_bytes"]
            ):
                flush()
            chunk_rows.append(encoded)
            chunk_keys.append(row["occurrence_key"])
            chunk_bytes += len(encoded)
        flush()

        manifest_document = {
            "protocol_version": PROTOCOL_VERSION,
            "files": manifest,
        }
        manifest_bytes = canonical_json_bytes(manifest_document, limits)
        index = {
            "protocol_version": PROTOCOL_VERSION,
            "aggregate_sha256": aggregate_digest(descriptors),
            "scan_manifest_sha256": sha256_hex(manifest_bytes),
            "total_rows": len(sorted_rows),
            "total_bytes": sum(item["byte_count"] for item in descriptors),
            "chunks": descriptors,
        }
        index_bytes = canonical_json_bytes(index, limits)
        summary_bytes = canonical_json_bytes(summary_for(sorted_rows), limits)
        total_generated += len(index_bytes) + len(summary_bytes) + len(manifest_bytes)
        if total_generated > limits["max_generated_bytes"]:
            fail("E_GENERATED_SIZE", "max_generated_bytes exceeded")
        (temporary / "index.json").write_bytes(index_bytes)
        (temporary / "summary.json").write_bytes(summary_bytes)
        (temporary / "scan-manifest.json").write_bytes(manifest_bytes)
        output.rmdir()
        temporary.rename(output)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def parse_utc(value: str, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        fail("E_TIME", f"{label} must be UTC with trailing Z")
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        fail("E_TIME", f"{label}: {exc}")
    return result.astimezone(timezone.utc)


def evaluate_freshness(
    surface: dict[str, Any],
    evaluation_time: datetime,
    evaluation_point: str,
    observed_events: set[str],
) -> tuple[bool, str]:
    policy = surface.get("freshness_policy")
    if not isinstance(policy, dict):
        return (False, "missing_policy")
    points = policy.get("evaluation_points")
    required_points = {"owner_acceptance", "pre_integration"}
    if (
        not isinstance(points, list)
        or len(points) != len(set(points))
        or set(points) != required_points
        or evaluation_point not in points
    ):
        return (False, "missing_evaluation_point")
    status = surface.get("status")
    if status != "inspected":
        return (False, "not_currently_inspected")
    events = policy.get("invalidating_events")
    if not isinstance(events, list) or any(not isinstance(item, str) for item in events):
        return (False, "invalid_event_policy")
    if observed_events.intersection(events):
        return (False, "invalidating_event")
    if policy.get("point_in_time_only") is True:
        return (False, "point_in_time_only")
    maximum = policy.get("max_age_seconds")
    if maximum is None:
        if not events:
            return (False, "no_current_eligibility_rule")
    elif not isinstance(maximum, int) or isinstance(maximum, bool) or maximum <= 0:
        return (False, "invalid_max_age")
    else:
        acquired = parse_utc(surface.get("acquired_at"), "acquired_at")
        age = (evaluation_time - acquired).total_seconds()
        if age < 0:
            return (False, "acquisition_in_future")
        if age > maximum:
            return (False, "expired")
    return (True, "eligible")
