# M0.1 v2 Rule-to-Occurrence Ledger Protocol

**Status:** Proposed protocol and tooling candidate. It is not accepted and must
not generate migration-acceptance evidence until independently reviewed, accepted
by Greg, and merged by ordinary merge commit.

## 1. Purpose and non-authority

This protocol turns compact, human-reviewed classification sources into one
canonical occurrence stream, independently discovers candidate occurrences, and
verifies the retained package byte-for-byte. It implements the evidence
architecture recognized by M0 Amendment 2 in `gregkrsak/klyxr`.

The protocol describes evidence. It cannot authorize source changes, execution,
approval, replay, custody, resources, merges, release, publication, repository
renaming, domain cutover, M0.1 acceptance, M1, or any later phase.

The first M0.1 attempt preserved beneath `archive/unaccepted/**` is permanently
ineligible as tooling, schema authority, compact input, fixture authority,
current evidence, or acceptance dependency.

## 2. Governing identity

This candidate is subordinate to:

| Item | Identity |
| --- | --- |
| Source repository | `gregkrsak/klyxr` |
| Accepted integration commit | `609822762abd46c13ecd6187ccc8510695e52b2f` |
| Pre-merge test object, not integration | `9feb01fb68ebb72dfb7f0d6781e8e65b01b3c56d` |
| Accepted integration tree | `ebaf5e4b7b6a7a09acc693db52e3cdc5e0ec2239` |
| Contract path | `docs/migration/BOWFIN-NAME-MIGRATION-PLAN.md` |
| Contract blob | `03cd2c5b584a996ebfb873491f0d2888c984cfb9` |

If any of those identities changes, this candidate requires renewed review.

## 3. Authorization sequence

1. The protocol specification, schemas, tooling, limits, fixtures, and tests are
   prepared in a draft ledger PR.
2. An independent reviewer statically examines the exact candidate. Candidate
   tooling is not executed during this step.
3. Greg may authorize isolated execution of the exact reviewed revision's
   synthetic self-tests. That authorization does not permit production inputs or
   evidence generation.
4. Test results and any repairs receive independent review. Greg alone may accept
   and merge the exact tooling revision by ordinary merge commit.
5. Compact production inputs and evidence generation require a later, separate
   authorization.

This sequence prevents candidate tooling from establishing its own trust.

## 4. Runtime and execution isolation

The normative runtime is CPython 3.12.x, invoked with isolated mode:

    python3 -I <tool> ...

The tools use only the Python standard library. Candidate source, governance
content, archived payloads, compact inputs, and scanned roots are never placed on
`sys.path` and are never imported or executed. The wrappers load only the exact
reviewed `protocol_lib.py` beside themselves by absolute path.

The tools do not invoke Git, hooks, filters, diff drivers, shells, compilers,
package managers, network clients, plugins, databases, services, templates,
regular expressions supplied by inputs, or general query languages. They require
read-only authenticated snapshots and write only to paths that do not yet exist
beneath a pre-existing, non-symlink output directory.

Source snapshots must be ordinary directories containing regular files and
directories only. Symlinks, special files, `.git`, and any path equal to or beneath
`archive/unaccepted` are rejected. Paths are relative POSIX UTF-8 strings; absolute
paths, `.`/`..`, backslashes, NUL, and non-NFC spellings reject.

Every source, accepted-base, contract, tooling, and compact-input snapshot is
accompanied by an `authenticated_git_export`. It carries the raw Git commit
object and complete ordered path/mode/blob-SHA-1/SHA-256/byte-count set.
Verification reconstructs the Git tree, authenticates the commit object,
enumerates the filesystem independently, and requires exact mode and byte
equality. `synthetic_fixture` and `current_accepted_dependency` eligibility
classes are explicit and never interchangeable.

## 5. Normative files

| Path | Purpose |
| --- | --- |
| `schema.json` | JSON Schema 2020-12 description of compact inputs and retained rows |
| `limits.json` | Normative serialized and processing limits |
| `protocol_lib.py` | Shared bounded byte, JSON, hash, path, and package primitives |
| `generate.py` | Classification expansion and deterministic package construction |
| `audit_scan.py` | Independently configured occurrence discovery |
| `verify.py` | Package, reconciliation, and freshness verification |
| `tests/` | Synthetic fixtures and independently stated expectations |

The schema is normative documentation. The standard-library verifier performs the
same required checks directly; no external JSON-Schema implementation is trusted.

## 6. Strict JSON and canonical bytes

All protocol JSON is UTF-8 without BOM. Parsing rejects duplicate object keys,
floating-point numbers, NaN/infinities, lone surrogates, non-NFC strings, excessive
depth, oversized strings, and integers outside `0..9007199254740991` unless a
field explicitly permits a signed value.

Canonical JSON uses:

- keys sorted by Unicode code-point order;
- UTF-8 characters emitted directly (`ensure_ascii = false`);
- separators `,` and `:` with no insignificant whitespace;
- JSON literals `true`, `false`, and `null` only;
- integers in ordinary decimal form; and
- exactly one trailing LF for a document or JSONL row.

CRLF, platform separators, locale collation, host paths, timestamps, runner names,
and job URLs never enter deterministic output.

## 7. Compact inputs

Production compact inputs are not included in this PR. A future separately
authorized input set contains:

- `mappings.json` — namespace-qualified original/canonical mappings;
- `classification-rules.json` — semantic rules and reviewed population claims;
- `audit-policy.json` — independently authored discovery families;
- `surface-register.json` — the complete required external-surface set;
- `external-surfaces.json` — retained observations and freshness policies;
- `applicability-decisions.json` — reviewed not-applicable decisions;
- `visual-inspection.json` — exact image identities and whole-image review;
- `limitations.json` — affected surface, reason, consequence, and disposition.

Every input document declares `protocol_version: "m0.1-v2"` and rejects unknown
top-level fields.

### 7.1 Mappings

Each mapping has a stable `mapping_id`, namespace, original identity, canonical
identity or explicit retention, and policy. `(namespace, original)` and
`(namespace, canonical)` are injective. Repeated occurrences do not violate
mapping injectivity.

### 7.2 Classification rules

Selectors are a conjunction of reviewed literal fields only:

- `mapping_id` (required);
- `unit_kind` (required);
- exactly one of `path_exact`, `path_prefix`, or `path_suffix` (required);
- optional exact `json_pointer_prefix`.

There are no regular expressions, globs, code expressions, plugins, or callbacks.
Historical rules require `path_exact`; broad historical exemptions reject.

Every rule records expected selected count, live/compatibility/historical role,
phase, rationale, representative and boundary context, producer, consumer,
support/removal policy, validation/test identity, and historical relationship.
One occurrence must match exactly one rule. Zero or multiple matches reject.

### 7.3 Independent audit policy

`audit-policy.json` is independently authored and reviewed. Neither generator nor
auditor may derive it from `mappings.json` or `classification-rules.json`.
Discovery families use only bounded literal forms:

- exact UTF-8 literal;
- ASCII-case-insensitive literal;
- literal prefix followed by one or more ASCII digits; or
- exact source suffix/path component.

Each family names its namespace and eligible unit kinds. The auditor receives no
classification rules, canonical identities, roles, phases, or historical
exclusions. It reports every discovered key, plus unknown and unclassified
candidates. Completeness is equality of exact occurrence-key sets, never counts.

## 8. Occurrence units and precedence

The scanner includes hidden files and case variants and defines these unit kinds:

1. `path_component` — a match in one filename or directory component;
2. `raw_text` — a match in strict UTF-8 file bytes;
3. `structured_key` — a match in a JSON object key at an exact JSON Pointer;
4. `structured_value` — a match in a JSON string value at an exact JSON Pointer;
5. `embedded_identity` — a raw-text match for decision, control, or test identity namespaces;
6. `machine_identifier` — a raw-text match for machine/provenance namespaces.

Structured matches are intentionally additional to raw-text/machine/embedded
matches. That overlap is explicit and receives distinct keys. Binary/non-UTF-8
files are retained in the authenticated scan manifest and produce no text
occurrences. JSON files that fail bounded source-JSON parsing remain raw text and
record an exact structured-scan error in that manifest; they are never silently
treated as valid JSON. Before evidence acceptance, each such status requires a
corresponding reviewed limitation or other explicit surface disposition.

## 9. Occurrence key and row

An occurrence key is:

    sha256:<lowercase SHA-256 of canonical JSON tuple>

The tuple is:

    [source_repository, source_tree, path, unit_kind, locator,
     namespace, original_identity]

It contains only discovered identity and location, never classification result,
mapping ID, rule ID, canonical identity, role, or rationale. Generator and auditor
can therefore reconcile the same keys without sharing classification logic.

Each generated row records the occurrence key plus exact location, source-file
SHA-256, original/canonical identity, namespace, role, phase, producer, consumer,
support/removal policy, validation/test identity, historical relationship,
mapping ID, rule ID, and bounded context. Rows sort by occurrence key bytewise.

Locators never use encounter order. Raw, embedded, and machine matches use exact
UTF-8 byte start/end coordinates. Path matches add component index and component
byte start/end. Structured matches use JSON Pointer plus value-local UTF-8 byte
start/end. The independently authored scanner can derive the same key without
sharing generator traversal state.

## 10. Chunking, index, and aggregate digest

Every row is canonical JSON plus LF. A row exceeding `max_row_bytes` rejects.
Sorted rows fill a chunk until adding the next row would exceed either
`max_rows_per_chunk` or `max_chunk_bytes`. The first chunk is
`occurrences/0000.jsonl`; names use four lowercase decimal digits and are
contiguous. An empty stream produces no chunks.

The index records for each chunk: path, SHA-256, byte count, row count, first key,
and last key. It also records total rows and bytes and the SHA-256 of canonical
`scan-manifest.json`. The manifest records every source path, byte count,
source-file SHA-256, UTF-8 status, structured-scan status, and stable structured
error code. The index has no self-hash.

The aggregate digest is SHA-256 over the UTF-8 concatenation, in index order, of:

    path NUL sha256 NUL byte_count NUL row_count NUL first_key NUL last_key LF

The verifier recomputes every field and rejects missing, extra, duplicated,
renamed, noncontiguous, or reordered chunks. `summary.json` contains counts by
namespace, role, phase, and unit kind; it contains no occurrence rows.
The verifier independently reconstructs the unique greedy chunk partition and
rejects a byte-valid, fully rehashed alternative partition.

## 11. Freshness eligibility

Every required external-surface class uses one of:

- a justified `max_age_seconds` window;
- a nonempty set of named invalidating events;
- `point_in_time_only: true`; or
- a reviewed combination.

The evaluator accepts an explicit UTC evaluation instant and explicit observed
invalidating events. It never reads the clock or network. Eligibility is evaluated
before owner acceptance and immediately before integration. Missing evidence,
expired windows, limited or unavailable required surfaces, or applicable
invalidating events fail closed even when snapshot bytes are unchanged.
Reacquisition creates a new bound observation and requires renewed disposition.
A `not_applicable` record retains only that reviewed claim; the tooling does not
manufacture semantic applicability from the label. The required-surface register
and observation set must match exactly. Each not-applicable observation requires
one decision bound to the subject commit/tree and a content-addressed review
record; other observations must have none.

Offline regeneration consumes retained inputs only and never refreshes them.

## 12. Deterministic versus runtime provenance

Deterministic output contains exact repository/tree/blob identities, canonical
inputs, file hashes, rows, indexes, summaries, and limitations. Acquisition time,
evaluation time, runner identity, workflow URL, duration, and capture method live
in separate runtime provenance or decision records and are never inputs to
deterministic package bytes except where a retained external observation itself
is the explicit reviewed input.

## 13. Shared components and independent failure modes

Generator, auditor, and verifier share only strict JSON, canonical encoding,
SHA-256, path validation, occurrence-key construction, and bounded file I/O.
Generator rule matching is not imported by the auditor. Auditor discovery policy
is not imported by the generator. The verifier does not call either scanner when
checking package structure.

Shared primitive defects remain a common-mode risk and must be disclosed in review.
Synthetic expectations therefore include literal precomputed keys/digests and
mutation cases that do not ask the candidate generator to define its own oracle.

## 14. Rejection behavior

The tools return zero only for a satisfied command. Failures return nonzero and a
stable code on stderr. Required failures include duplicate JSON keys, unknown
fields/enums, non-injective mappings, empty/broad selectors, unmatched or multiply
matched occurrences, expected-count mismatch, key-set mismatch, digest mismatch,
bad ordering/chunking, stale freshness, path escape, symlink/special file, archive
dependency, excessive size/depth/count, and output overwrite.

The package destination must not exist. Individual documents use exclusive,
no-follow creation beneath an already-existing non-symlink parent. Row, chunk,
aggregate, and processing budgets are charged before or during work. An existing
destination rejects.

## 15. Retention, transfer, recovery, and R8

Accepted protocol, inputs, canonical uncompressed JSONL, index, summary, reports,
decisions, and receipts remain in reachable Git history. Compression is transport
only; workflow artifacts and external object URLs are never sole evidence.

The repository's documented backup must retain Git objects and refs sufficient to
recover accepted identities. Repository transfer records old and new repository
identities without rewriting historical records. After R8 the repository becomes
read-only unless a later accepted decision establishes another purpose. Retirement
never deletes or reclassifies accepted evidence or unaccepted archives.

Ledger unavailability blocks only migration gates that require it. It never blocks
normal compiler build, check, verify, run, failure recovery, or accepted production
operation.

The C/E/D/P receipt carries raw commit objects. C and E each include an ordered,
nonempty `introduced_commits` first-parent chain from accepted base to reviewed
head. P verifies merge parents, resulting trees, integrated heads, and target
branches rather than trusting asserted correspondence. Recovery authenticates the
restored E commit/tree and separately binds backup and recovery-evidence digests.

## 16. Synthetic test boundary

Fixtures beneath `tests/fixtures/` are synthetic protocol tests. They are not
compact production inputs, migration evidence, source classifications, owner
decisions, or authority. Mutation expectations are handwritten and versioned.

The required suite covers valid deterministic generation; repeated regeneration;
duplicate keys; non-NFC text; non-injective mappings; unknown kinds; hidden paths;
case variants; structured keys/values; overlapping identities; equal-count but
different-key substitution; stale rules; missing/extra/reordered/tampered chunks;
oversized rows; depth/count limits; symlinks/path escape; archive roots; unchanged
bytes with expired freshness; invalidating events; and C/E/D/P finite-sequence and
recovery-record shape.

No test execution is authorized by the existence of these files.
