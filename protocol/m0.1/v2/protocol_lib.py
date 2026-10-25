#!/usr/bin/env python3
"""Bounded primitives shared by the proposed M0.1 v2 tools.

This module authenticates bytes and Git objects, but it contains no occurrence
matching, structured traversal, classification, audit-family, or reconciliation
logic. Do not execute this candidate before exact-revision review and owner
authorization.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, NoReturn


PROTOCOL_VERSION = "m0.1-v2"
EXPECTED_LIMITS_SHA256 = "2ae8756765340be8e25a5e3cc6688db1bbe382fea33084a435643af76210d8de"
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
FILE_MODES = frozenset({"100644", "100755"})
TREE_ENTRY_MODES = frozenset({"40000", "100644", "100755", "120000", "160000"})


class ProtocolError(Exception):
    """A stable, fail-closed protocol error."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def fail(code: str, message: str) -> NoReturn:
    raise ProtocolError(code, message)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_object_sha1(kind: str, data: bytes) -> str:
    header = kind.encode("ascii") + b" " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def require_sha1(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(char not in "0123456789abcdef" for char in value):
        fail("E_SHA1", f"invalid {label}")
    return value


def require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        fail("E_SHA256", f"invalid {label}")
    return value


def require_identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 200:
        fail("E_IDENTIFIER", f"invalid {label}")
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-"
    if value[0] not in allowed.replace(".", "").replace(":", "") or any(char not in allowed for char in value):
        fail("E_IDENTIFIER", f"invalid {label}")
    return value


def require_phase(value: Any, label: str) -> str:
    if not isinstance(value, str):
        fail("E_PHASE", f"invalid {label}")
    parts = value.split(".")
    if (
        len(parts) > 2
        or parts[0] not in {f"M{number}" for number in range(8)}
        or (len(parts) == 2 and (not parts[1] or not parts[1].isdigit()))
    ):
        fail("E_PHASE", f"invalid {label}")
    return value


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
        if unicodedata.normalize("NFC", value) != value:
            fail("E_JSON_NFC", "string is not NFC-normalized")
        if len(value.encode("utf-8")) > limits["max_string_bytes"]:
            fail("E_JSON_STRING", "string exceeds max_string_bytes")
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
    fail("E_JSON_TYPE", f"unsupported JSON type: {type(value).__name__}")


def strict_json_bytes(data: bytes, limits: dict[str, int], label: str, maximum: int | None = None) -> Any:
    bound = limits["max_input_file_bytes"] if maximum is None else maximum
    if len(data) > bound:
        fail("E_INPUT_SIZE", f"{label} exceeds its byte limit")
    if data.startswith(b"\xef\xbb\xbf"):
        fail("E_JSON_BOM", f"{label} begins with a UTF-8 BOM")
    try:
        text = data.decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        fail("E_JSON_UTF8", f"{label}: {error}")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_float=_no_float,
            parse_constant=_no_constant,
        )
    except ProtocolError:
        raise
    except json.JSONDecodeError as error:
        fail("E_JSON_SYNTAX", f"{label}: {error}")
    validate_json_value(value, limits)
    return value


def source_json_strings(data: bytes, limits: dict[str, int], label: str) -> Any:
    """Parse source JSON while replacing irrelevant numbers with zero."""
    if len(data) > limits["max_source_file_bytes"]:
        fail("E_FILE_SIZE", f"{label} exceeds max_source_file_bytes")
    try:
        text = data.decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        fail("E_SOURCE_JSON_UTF8", f"{label}: {error}")
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
    except json.JSONDecodeError as error:
        fail("E_SOURCE_JSON_SYNTAX", f"{label}: {error}")
    validate_json_value(value, limits)
    return value


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


def require_keys(obj: dict[str, Any], required: set[str], optional: set[str], label: str) -> None:
    missing = sorted(required - obj.keys())
    unknown = sorted(obj.keys() - required - optional)
    if missing:
        fail("E_FIELD_MISSING", f"{label} missing fields: {missing}")
    if unknown:
        fail("E_FIELD_UNKNOWN", f"{label} unknown fields: {unknown}")


def validate_relpath(raw: Any, limits: dict[str, int]) -> PurePosixPath:
    if not isinstance(raw, str) or not raw:
        fail("E_PATH", "path must be a nonempty string")
    if raw.startswith("/") or "\\" in raw or "\x00" in raw:
        fail("E_PATH", f"invalid path spelling: {raw!r}")
    components = raw.split("/")
    if any(component in {"", ".", ".."} for component in components):
        fail("E_PATH", f"empty or dot component is forbidden: {raw!r}")
    if len(components) > limits["max_json_depth"]:
        fail("E_PATH_DEPTH", f"path exceeds component-depth limit: {raw!r}")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in raw):
        fail("E_PATH_UTF8", f"path is not valid UTF-8: {raw!r}")
    if unicodedata.normalize("NFC", raw) != raw:
        fail("E_PATH_NFC", f"path is not NFC: {raw!r}")
    if len(raw.encode("utf-8")) > limits["max_path_bytes"]:
        fail("E_PATH_SIZE", f"path exceeds max_path_bytes: {raw!r}")
    if ".git" in components:
        fail("E_GIT_METADATA", f"Git metadata is forbidden: {raw}")
    if len(components) >= 2 and components[0:2] == ["archive", "unaccepted"]:
        fail("E_ARCHIVE_DEPENDENCY", f"unaccepted archive path is forbidden: {raw}")
    return PurePosixPath(*components)


def validate_view_prefix(raw: Any, limits: dict[str, int]) -> tuple[str, ...]:
    """Validate an eligible repository subtree prefix.

    The empty string names the repository root. Nonempty prefixes use the same
    fail-closed spelling and archive-exclusion rules as materialized paths.
    """
    if raw == "":
        return ()
    return validate_relpath(raw, limits).parts


def _validate_tree_component(raw: Any, limits: dict[str, int], label: str) -> str:
    """Validate an opaque Git-tree entry name without making it eligible."""
    if not isinstance(raw, str) or raw in {"", ".", ".."} or "/" in raw or "\x00" in raw:
        fail("E_EXPORT_PROOF", f"invalid {label}")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in raw):
        fail("E_EXPORT_PROOF", f"invalid UTF-8 in {label}")
    if unicodedata.normalize("NFC", raw) != raw:
        fail("E_EXPORT_PROOF", f"non-NFC {label}")
    if len(raw.encode("utf-8")) > limits["max_path_bytes"]:
        fail("E_EXPORT_PROOF", f"oversized {label}")
    return raw


def assert_no_symlink_ancestors(path: Path) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        if not current.exists() and not current.is_symlink():
            continue
        try:
            mode = current.lstat().st_mode
        except OSError as error:
            fail("E_PATH_STAT", f"cannot inspect {current}: {error}")
        if stat.S_ISLNK(mode):
            fail("E_SYMLINK", f"symlink ancestor is forbidden: {current}")


def read_bounded_file(path: Path, maximum: int) -> bytes:
    assert_no_symlink_ancestors(path)
    try:
        named = path.lstat()
    except OSError as error:
        fail("E_FILE_READ", f"cannot inspect {path}: {error}")
    if not stat.S_ISREG(named.st_mode):
        fail("E_SPECIAL_FILE", f"not a regular file: {path}")
    if named.st_size > maximum:
        fail("E_FILE_SIZE", f"{path} exceeds {maximum} bytes")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        fail("E_FILE_READ", f"cannot open {path}: {error}")
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            fail("E_SPECIAL_FILE", f"not a regular file: {path}")
        if (before.st_dev, before.st_ino) != (named.st_dev, named.st_ino):
            fail("E_FILE_CHANGED", f"file identity changed before reading: {path}")
        if before.st_size > maximum:
            fail("E_FILE_SIZE", f"{path} exceeds {maximum} bytes")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, maximum + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum:
                fail("E_FILE_SIZE", f"{path} exceeds {maximum} bytes")
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            fail("E_FILE_CHANGED", f"file changed while reading: {path}")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def strict_json_file(path: Path, limits: dict[str, int], maximum: int | None = None) -> Any:
    bound = limits["max_input_file_bytes"] if maximum is None else maximum
    return strict_json_bytes(read_bounded_file(path, bound), limits, str(path), bound)


def load_limits(path: Path) -> dict[str, int]:
    data = read_bounded_file(path, 1024 * 1024)
    if sha256_hex(data) != EXPECTED_LIMITS_SHA256:
        fail("E_LIMITS_IDENTITY", "limits.json does not match the reviewed identity")
    provisional = {
        "max_input_file_bytes": 1024 * 1024,
        "max_json_depth": 32,
        "max_json_integer": 9007199254740991,
        "max_string_bytes": 1024 * 1024,
    }
    obj = strict_json_bytes(data, provisional, str(path), 1024 * 1024)
    if not isinstance(obj, dict) or obj.get("protocol_version") != PROTOCOL_VERSION:
        fail("E_LIMITS", "invalid limits document")
    expected = {
        "max_audit_families", "max_audit_output_bytes", "max_chunk_bytes",
        "max_chunks", "max_context_bytes", "max_export_bytes",
        "max_generated_bytes", "max_input_file_bytes", "max_json_depth",
        "max_json_integer", "max_mappings", "max_occurrences",
        "max_path_bytes", "max_processing_steps", "max_row_bytes",
        "max_rows_per_chunk", "max_rules", "max_source_file_bytes",
        "max_source_files", "max_string_bytes", "max_total_source_bytes",
        "protocol_version",
    }
    if set(obj) != expected:
        fail("E_LIMITS", "limits fields do not match the normative set")
    result: dict[str, int] = {}
    for key, value in obj.items():
        if key == "protocol_version":
            continue
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            fail("E_LIMITS", f"{key} must be a positive integer")
        result[key] = value
    return result


def _git_tree_sha(entries: list[dict[str, Any]], limits: dict[str, int]) -> str:
    root: dict[str, Any] = {}
    for entry in entries:
        path = validate_relpath(entry["path"], limits)
        node = root
        for component in path.parts[:-1]:
            existing = node.setdefault(component, {})
            if not isinstance(existing, dict):
                fail("E_EXPORT_PATH", f"file/directory collision at {entry['path']}")
            node = existing
        leaf = path.parts[-1]
        if leaf in node:
            fail("E_EXPORT_PATH", f"duplicate or colliding path: {entry['path']}")
        node[leaf] = (entry["mode"], entry["blob_sha1"])

    def build(node: dict[str, Any]) -> str:
        records: list[tuple[bytes, bytes]] = []
        for name, value in node.items():
            name_bytes = name.encode("utf-8")
            if isinstance(value, dict):
                object_sha = build(value)
                sort_key = name_bytes + b"/"
                record = b"40000 " + name_bytes + b"\0" + bytes.fromhex(object_sha)
            else:
                mode, object_sha = value
                sort_key = name_bytes
                record = mode.encode("ascii") + b" " + name_bytes + b"\0" + bytes.fromhex(object_sha)
            records.append((sort_key, record))
        payload = b"".join(record for _key, record in sorted(records, key=lambda item: item[0]))
        return git_object_sha1("tree", payload)

    return build(root)


def _git_direct_tree_sha(entries: list[dict[str, Any]]) -> str:
    records: list[bytes] = []
    for entry in entries:
        records.append(
            entry["mode"].encode("ascii")
            + b" "
            + entry["name"].encode("utf-8")
            + b"\0"
            + bytes.fromhex(entry["object_sha1"])
        )
    return git_object_sha1("tree", b"".join(records))


def _validate_tree_proof(
    proof: Any,
    prefix_components: tuple[str, ...],
    root_tree: str,
    view_tree: str,
    limits: dict[str, int],
) -> None:
    if not isinstance(proof, list) or len(proof) != len(prefix_components):
        fail("E_EXPORT_PROOF", "tree proof length does not match view prefix")
    current_tree = root_tree
    for depth, node in enumerate(proof):
        label = f"tree_proof[{depth}]"
        if not isinstance(node, dict):
            fail("E_EXPORT_PROOF", f"{label} must be an object")
        require_keys(node, {"tree", "entries"}, set(), label)
        require_sha1(node["tree"], f"{label}.tree")
        if node["tree"] != current_tree:
            fail("E_EXPORT_PROOF", f"{label} does not continue the root-to-view chain")
        direct_entries = node["entries"]
        if not isinstance(direct_entries, list) or len(direct_entries) > limits["max_source_files"]:
            fail("E_EXPORT_PROOF", f"invalid {label}.entries")
        prior_sort_key: bytes | None = None
        names: set[str] = set()
        selected: dict[str, Any] | None = None
        for index, entry in enumerate(direct_entries):
            entry_label = f"{label}.entries[{index}]"
            if not isinstance(entry, dict):
                fail("E_EXPORT_PROOF", f"{entry_label} must be an object")
            require_keys(entry, {"name", "mode", "object_sha1"}, set(), entry_label)
            name = _validate_tree_component(entry["name"], limits, f"{entry_label}.name")
            if name in names:
                fail("E_EXPORT_PROOF", f"duplicate name in {label}: {name}")
            names.add(name)
            if entry["mode"] not in TREE_ENTRY_MODES:
                fail("E_EXPORT_PROOF", f"unsupported mode in {entry_label}")
            require_sha1(entry["object_sha1"], f"{entry_label}.object_sha1")
            sort_key = name.encode("utf-8") + (b"/" if entry["mode"] == "40000" else b"")
            if prior_sort_key is not None and sort_key <= prior_sort_key:
                fail("E_EXPORT_PROOF", f"entries are not in canonical Git order: {label}")
            prior_sort_key = sort_key
            if name == prefix_components[depth]:
                selected = entry
        if _git_direct_tree_sha(direct_entries) != current_tree:
            fail("E_EXPORT_PROOF", f"{label} does not reconstruct its nominated tree")
        if selected is None or selected["mode"] != "40000":
            fail("E_EXPORT_PROOF", f"view component is not a proved subtree: {prefix_components[depth]}")
        current_tree = selected["object_sha1"]
    if current_tree != view_tree:
        fail("E_EXPORT_PROOF", "tree proof does not terminate at the nominated view tree")


def validate_export_document(
    document: Any,
    limits: dict[str, int],
    expected_repository: str,
    expected_commit: str,
    expected_tree: str,
    expected_view_prefix: str,
    expected_view_tree: str,
    expected_fixture: bool,
) -> list[dict[str, Any]]:
    required = {
        "record_class", "protocol_version", "repository", "commit", "tree",
        "commit_object_base64", "fixture", "eligibility", "view_prefix",
        "view_tree", "tree_proof", "entries",
    }
    if not isinstance(document, dict):
        fail("E_EXPORT", "Git export must be an object")
    require_keys(document, required, set(), "git-export")
    if document["record_class"] != "authenticated_git_export" or document["protocol_version"] != PROTOCOL_VERSION:
        fail("E_EXPORT", "invalid Git export class or version")
    if (
        document["repository"] != expected_repository
        or document["commit"] != expected_commit
        or document["tree"] != expected_tree
        or document["view_prefix"] != expected_view_prefix
        or document["view_tree"] != expected_view_tree
        or document["fixture"] is not expected_fixture
    ):
        fail("E_EXPORT_IDENTITY", "Git export does not match independently expected identity")
    expected_eligibility = "synthetic_fixture" if expected_fixture else "current_accepted_dependency"
    if document["eligibility"] != expected_eligibility:
        fail("E_EXPORT_ELIGIBILITY", "Git export has the wrong eligibility class")
    require_sha1(document["commit"], "export commit")
    require_sha1(document["tree"], "export tree")
    require_sha1(document["view_tree"], "export view tree")
    prefix_components = validate_view_prefix(document["view_prefix"], limits)
    try:
        commit_bytes = base64.b64decode(document["commit_object_base64"], validate=True)
    except (ValueError, TypeError) as error:
        fail("E_EXPORT_COMMIT", f"invalid commit object base64: {error}")
    if git_object_sha1("commit", commit_bytes) != document["commit"]:
        fail("E_EXPORT_COMMIT", "commit object does not match commit identity")
    first_header = commit_bytes.split(b"\n", 1)[0]
    if first_header != b"tree " + document["tree"].encode("ascii"):
        fail("E_EXPORT_COMMIT", "commit object does not name the exported tree")
    _validate_tree_proof(
        document["tree_proof"], prefix_components, document["tree"],
        document["view_tree"], limits,
    )
    entries = document["entries"]
    if not isinstance(entries, list) or len(entries) > limits["max_source_files"]:
        fail("E_EXPORT_ENTRIES", "invalid export entry count")
    previous: bytes | None = None
    total = 0
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            fail("E_EXPORT_ENTRY", f"entries[{index}] must be an object")
        require_keys(entry, {"path", "mode", "blob_sha1", "sha256", "byte_count"}, set(), f"entries[{index}]")
        path = validate_relpath(entry["path"], limits).as_posix()
        key = path.encode("utf-8")
        if previous is not None and key <= previous:
            fail("E_EXPORT_ORDER", "export entries are not strictly path ordered")
        previous = key
        if entry["mode"] not in FILE_MODES:
            fail("E_EXPORT_MODE", f"unsupported mode for {path}")
        require_sha1(entry["blob_sha1"], f"{path}.blob_sha1")
        require_sha256(entry["sha256"], f"{path}.sha256")
        if not isinstance(entry["byte_count"], int) or isinstance(entry["byte_count"], bool) or entry["byte_count"] < 0:
            fail("E_EXPORT_SIZE", f"invalid byte count for {path}")
        if entry["byte_count"] > limits["max_source_file_bytes"]:
            fail("E_EXPORT_SIZE", f"source file exceeds limit: {path}")
        total += entry["byte_count"]
        if total > limits["max_total_source_bytes"]:
            fail("E_EXPORT_SIZE", "export exceeds max_total_source_bytes")
    if _git_tree_sha(entries, limits) != document["view_tree"]:
        fail("E_EXPORT_TREE", "materialized entries do not reconstruct the nominated view tree")
    return entries


def _enumerate_root(root: Path, limits: dict[str, int]) -> dict[str, str]:
    assert_no_symlink_ancestors(root)
    try:
        root_mode = root.lstat().st_mode
    except OSError as error:
        fail("E_SOURCE_ROOT", f"cannot inspect source root: {error}")
    if not stat.S_ISDIR(root_mode) or stat.S_ISLNK(root_mode):
        fail("E_SOURCE_ROOT", "source root must be a non-symlink directory")
    result: dict[str, str] = {}
    directories = 0

    def visit(directory: Path, prefix: tuple[str, ...]) -> None:
        nonlocal directories
        directories += 1
        if directories > limits["max_source_files"]:
            fail("E_SOURCE_DIRECTORIES", "directory count exceeds max_source_files")
        try:
            with os.scandir(directory) as iterator:
                children = []
                for child in iterator:
                    if len(children) >= limits["max_source_files"]:
                        fail("E_SOURCE_FILES", f"directory entry count exceeds max_source_files: {directory}")
                    children.append(child)
                children.sort(key=lambda item: item.name.encode("utf-8", "surrogateescape"))
        except OSError as error:
            fail("E_SOURCE_TRAVERSAL", f"cannot enumerate {directory}: {error}")
        for child in children:
            raw = "/".join(prefix + (child.name,))
            path = validate_relpath(raw, limits).as_posix()
            try:
                if child.is_symlink():
                    fail("E_SYMLINK", f"symlink is forbidden: {path}")
                if child.is_dir(follow_symlinks=False):
                    visit(Path(child.path), prefix + (child.name,))
                elif child.is_file(follow_symlinks=False):
                    mode = child.stat(follow_symlinks=False).st_mode
                    result[path] = "100755" if mode & stat.S_IXUSR else "100644"
                    if len(result) > limits["max_source_files"]:
                        fail("E_SOURCE_FILES", "source file count exceeds max_source_files")
                else:
                    fail("E_SPECIAL_FILE", f"special file is forbidden: {path}")
            except OSError as error:
                fail("E_SOURCE_TRAVERSAL", f"cannot inspect {path}: {error}")

    visit(root, ())
    return result


def verify_git_export(
    root: Path,
    export_path: Path,
    limits: dict[str, int],
    expected_repository: str,
    expected_commit: str,
    expected_tree: str,
    expected_view_prefix: str,
    expected_view_tree: str,
    expected_fixture: bool,
) -> tuple[dict[str, Any], list[tuple[str, bytes]]]:
    document = strict_json_file(export_path, limits, limits["max_export_bytes"])
    entries = validate_export_document(
        document,
        limits,
        expected_repository,
        expected_commit,
        expected_tree,
        expected_view_prefix,
        expected_view_tree,
        expected_fixture,
    )
    prefix_components = validate_view_prefix(document["view_prefix"], limits)
    view_root = root.joinpath(*prefix_components) if prefix_components else root
    actual_paths = _enumerate_root(view_root, limits)
    expected_paths = {entry["path"]: entry["mode"] for entry in entries}
    if actual_paths != expected_paths:
        missing = sorted(set(expected_paths) - set(actual_paths))[:20]
        extra = sorted(set(actual_paths) - set(expected_paths))[:20]
        fail("E_EXPORT_PATH_SET", f"missing={missing} extra={extra}")
    files: list[tuple[str, bytes]] = []
    for entry in entries:
        path = view_root.joinpath(*entry["path"].split("/"))
        data = read_bounded_file(path, limits["max_source_file_bytes"])
        if (
            len(data) != entry["byte_count"]
            or sha256_hex(data) != entry["sha256"]
            or git_object_sha1("blob", data) != entry["blob_sha1"]
        ):
            fail("E_EXPORT_CONTENT", f"content does not match export: {entry['path']}")
        files.append((entry["path"], data))
    return document, files


def export_digest(document: dict[str, Any], limits: dict[str, int]) -> str:
    return sha256_hex(canonical_json_bytes(document, limits))


def scan_manifest(files: list[tuple[str, bytes]], limits: dict[str, int]) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for path, data in files:
        try:
            data.decode("utf-8", "strict")
            text_status = "utf8"
        except UnicodeDecodeError:
            text_status = "non_utf8"
        structured_status = "not_json"
        structured_error = None
        if path.endswith(".json"):
            if text_status == "non_utf8":
                structured_status = "unavailable_non_utf8"
            else:
                try:
                    source_json_strings(data, limits, path)
                    structured_status = "valid_json"
                except ProtocolError as error:
                    structured_status = "invalid_json"
                    structured_error = error.code
        manifest.append(
            {
                "path": path,
                "sha256": sha256_hex(data),
                "byte_count": len(data),
                "text_status": text_status,
                "structured_status": structured_status,
                "structured_error": structured_error,
            }
        )
    return manifest


def scan_manifest_document(manifest: list[dict[str, Any]]) -> dict[str, Any]:
    return {"protocol_version": PROTOCOL_VERSION, "files": manifest}


def scan_manifest_digest(manifest: list[dict[str, Any]], limits: dict[str, int]) -> str:
    return sha256_hex(canonical_json_bytes(scan_manifest_document(manifest), limits))


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
    return "sha256:" + sha256_hex(canonical_json_bytes(identity, limits, trailing_lf=False))


def bounded_context_bytes(data: bytes, start: int, end: int, maximum: int) -> str:
    left = max(0, start - maximum // 2)
    right = min(len(data), end + maximum // 2)
    excerpt = data[left:right].decode("utf-8", "replace")
    if left:
        excerpt = "…" + excerpt
    if right < len(data):
        excerpt += "…"
    return excerpt


class WorkBudget:
    """Incremental resource accounting shared only as a numeric primitive."""

    def __init__(self, limits: dict[str, int]):
        self.limits = limits
        self.steps = 0
        self.occurrences = 0

    def charge(self, amount: int) -> None:
        if amount < 0 or self.steps > self.limits["max_processing_steps"] - amount:
            fail("E_PROCESSING_STEPS", "max_processing_steps exceeded")
        self.steps += amount

    def add_occurrence(self) -> None:
        if self.occurrences >= self.limits["max_occurrences"]:
            fail("E_OCCURRENCE_COUNT", "max_occurrences exceeded")
        self.occurrences += 1


def aggregate_digest(descriptors: list[dict[str, Any]]) -> str:
    payload = bytearray()
    for descriptor in descriptors:
        fields = (
            descriptor["path"], descriptor["sha256"], str(descriptor["byte_count"]),
            str(descriptor["row_count"]), descriptor["first_key"], descriptor["last_key"],
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


def _write_exclusive(path: Path, data: bytes) -> None:
    assert_no_symlink_ancestors(path.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o644)
    except OSError as error:
        fail("E_OUTPUT_CREATE", f"cannot exclusively create {path}: {error}")
    try:
        identity = os.fstat(descriptor)
    except OSError as error:
        os.close(descriptor)
        fail("E_OUTPUT_WRITE", f"cannot inspect created output {path}: {error}")
    succeeded = False
    try:
        view = memoryview(data)
        while view:
            try:
                written = os.write(descriptor, view)
            except OSError as error:
                fail("E_OUTPUT_WRITE", f"cannot write {path}: {error}")
            if written <= 0:
                fail("E_OUTPUT_WRITE", f"short write to {path}")
            view = view[written:]
        try:
            os.fsync(descriptor)
        except OSError as error:
            fail("E_OUTPUT_WRITE", f"cannot synchronize {path}: {error}")
        succeeded = True
    finally:
        try:
            os.close(descriptor)
        finally:
            if not succeeded:
                try:
                    current = path.lstat()
                    if (
                        stat.S_ISREG(current.st_mode)
                        and not stat.S_ISLNK(current.st_mode)
                        and (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino)
                    ):
                        path.unlink()
                except OSError:
                    pass


def write_exclusive_document(path: Path, value: Any, limits: dict[str, int], maximum: int) -> None:
    data = canonical_json_bytes(value, limits)
    if len(data) > maximum:
        fail("E_OUTPUT_SIZE", f"serialized output exceeds limit: {path}")
    if path.exists() or path.is_symlink():
        fail("E_OUTPUT_EXISTS", f"output already exists: {path}")
    assert_no_symlink_ancestors(path.parent)
    try:
        parent_mode = path.parent.lstat().st_mode
    except OSError as error:
        fail("E_OUTPUT_PARENT", f"output parent must already exist: {error}")
    if not stat.S_ISDIR(parent_mode) or stat.S_ISLNK(parent_mode):
        fail("E_OUTPUT_PARENT", "output parent must be a non-symlink directory")
    _write_exclusive(path, data)


def write_package(
    rows: list[dict[str, Any]],
    manifest: list[dict[str, Any]],
    output: Path,
    limits: dict[str, int],
) -> None:
    if output.exists() or output.is_symlink():
        fail("E_OUTPUT_EXISTS", "package output must not exist")
    assert_no_symlink_ancestors(output.parent)
    try:
        parent_mode = output.parent.lstat().st_mode
    except OSError as error:
        fail("E_OUTPUT_PARENT", f"package parent must already exist: {error}")
    if not stat.S_ISDIR(parent_mode) or stat.S_ISLNK(parent_mode):
        fail("E_OUTPUT_PARENT", "package parent must be a non-symlink directory")
    sorted_rows = sorted(rows, key=lambda row: row["occurrence_key"].encode("utf-8"))
    keys = [row["occurrence_key"] for row in sorted_rows]
    if len(keys) != len(set(keys)):
        fail("E_OCCURRENCE_DUPLICATE", "duplicate occurrence key")
    encoded_rows: list[bytes] = []
    total_encoded = 0
    for row in sorted_rows:
        encoded = canonical_json_bytes(row, limits)
        if len(encoded) > limits["max_row_bytes"]:
            fail("E_ROW_SIZE", f"row exceeds max_row_bytes: {row.get('occurrence_key')}")
        if total_encoded > limits["max_generated_bytes"] - len(encoded):
            fail("E_GENERATED_SIZE", "max_generated_bytes exceeded before write")
        total_encoded += len(encoded)
        encoded_rows.append(encoded)

    manifest_bytes = canonical_json_bytes(scan_manifest_document(manifest), limits)
    if total_encoded > limits["max_generated_bytes"] - len(manifest_bytes):
        fail("E_GENERATED_SIZE", "manifest exceeds generated-output budget")

    chunks: list[tuple[bytes, list[str]]] = []
    current_rows: list[bytes] = []
    current_keys: list[str] = []
    current_size = 0
    for row, encoded in zip(sorted_rows, encoded_rows):
        if current_rows and (
            len(current_rows) >= limits["max_rows_per_chunk"]
            or current_size + len(encoded) > limits["max_chunk_bytes"]
        ):
            chunks.append((b"".join(current_rows), list(current_keys)))
            current_rows, current_keys, current_size = [], [], 0
        current_rows.append(encoded)
        current_keys.append(row["occurrence_key"])
        current_size += len(encoded)
    if current_rows:
        chunks.append((b"".join(current_rows), list(current_keys)))
    if len(chunks) > limits["max_chunks"]:
        fail("E_CHUNK_COUNT", "max_chunks exceeded")

    descriptors: list[dict[str, Any]] = []
    for number, (data, chunk_keys) in enumerate(chunks):
        descriptors.append(
            {
                "path": f"occurrences/{number:04d}.jsonl",
                "sha256": sha256_hex(data),
                "byte_count": len(data),
                "row_count": len(chunk_keys),
                "first_key": chunk_keys[0],
                "last_key": chunk_keys[-1],
            }
        )
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
    publication_bytes = canonical_json_bytes(
        {
            "protocol_version": PROTOCOL_VERSION,
            "status": "complete",
            "scan_manifest_sha256": sha256_hex(manifest_bytes),
            "index_sha256": sha256_hex(index_bytes),
            "summary_sha256": sha256_hex(summary_bytes),
        },
        limits,
    )
    total = (
        total_encoded + len(manifest_bytes) + len(index_bytes)
        + len(summary_bytes) + len(publication_bytes)
    )
    if total > limits["max_generated_bytes"]:
        fail("E_GENERATED_SIZE", "max_generated_bytes exceeded before publication")

    try:
        output.mkdir(mode=0o755)
    except OSError as error:
        fail("E_OUTPUT_CREATE", f"cannot exclusively create package directory {output}: {error}")
    try:
        created = output.lstat()
    except OSError as error:
        fail("E_OUTPUT_CREATE", f"cannot inspect created package directory {output}: {error}")
    if not stat.S_ISDIR(created.st_mode) or stat.S_ISLNK(created.st_mode):
        fail("E_OUTPUT_CREATE", "created package output is not a directory")
    try:
        (output / "occurrences").mkdir(mode=0o755)
    except OSError as error:
        fail("E_OUTPUT_CREATE", f"cannot create occurrence directory: {error}")
    for descriptor, (data, _keys) in zip(descriptors, chunks):
        _write_exclusive(output / descriptor["path"], data)
    _write_exclusive(output / "scan-manifest.json", manifest_bytes)
    _write_exclusive(output / "index.json", index_bytes)
    _write_exclusive(output / "summary.json", summary_bytes)
    _write_exclusive(output / "publication.json", publication_bytes)


def parse_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        fail("E_TIME", f"{label} must be UTC with trailing Z")
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        fail("E_TIME", f"{label}: {error}")
    return result.astimezone(timezone.utc)


def evaluate_freshness(
    surface: dict[str, Any],
    evaluation_time: datetime,
    evaluation_point: str,
    observed_events: set[str],
) -> tuple[bool, str]:
    policy = surface["freshness_policy"]
    points = policy["evaluation_points"]
    if set(points) != {"owner_acceptance", "pre_integration"} or evaluation_point not in points:
        return (False, "missing_evaluation_point")
    if surface["status"] != "inspected":
        return (False, "not_currently_inspected")
    events = set(policy["invalidating_events"])
    if observed_events.intersection(events):
        return (False, "invalidating_event")
    if policy["point_in_time_only"] is True:
        return (False, "point_in_time_only")
    maximum = policy["max_age_seconds"]
    if maximum is None:
        if not events:
            return (False, "no_current_eligibility_rule")
    else:
        acquired = parse_utc(surface["acquired_at"], "acquired_at")
        age = (evaluation_time - acquired).total_seconds()
        if age < 0:
            return (False, "acquisition_in_future")
        if age > maximum:
            return (False, "expired")
    return (True, "eligible")


def digest_documents(paths: Iterable[Path], limits: dict[str, int]) -> str:
    descriptors: list[dict[str, Any]] = []
    for path in sorted(paths, key=lambda item: item.as_posix().encode("utf-8")):
        data = read_bounded_file(path, limits["max_input_file_bytes"])
        descriptors.append({"path": path.as_posix(), "sha256": sha256_hex(data), "byte_count": len(data)})
    return sha256_hex(canonical_json_bytes(descriptors, limits, trailing_lf=False))
