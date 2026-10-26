# M0.1 v2 Rule-to-Occurrence Ledger Protocol

**Status:** Proposed discovery-efficiency repair of the accepted protocol/tooling
revision. The prior occurrence-semantics repair at reviewed head
`23bed495c73b600d0a849b3c336d08a5c6cdd1b1`, tree
`c642dca4c4b8ae4e08f1250e1862bbe821c43b04`, and protocol subtree
`d0e0c7419020415ddc7996631db616b2f73a25b3` were accepted by Greg and integrated
through ordinary merge commit `ef9574336edf2b16aae4308330d581f0bacb6e45`.
The present changed revision is unreviewed, unexecuted, and not yet eligible as a
tooling dependency. Production inputs and evidence generation remain separately
gated. M0.1 remains unaccepted and M1 remains unauthorized.

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

This accepted revision is subordinate to:

| Item | Identity |
| --- | --- |
| Source repository | `gregkrsak/klyxr` |
| Accepted integration commit | `609822762abd46c13ecd6187ccc8510695e52b2f` |
| Pre-merge test object, not integration | `9feb01fb68ebb72dfb7f0d6781e8e65b01b3c56d` |
| Accepted integration tree | `ebaf5e4b7b6a7a09acc693db52e3cdc5e0ec2239` |
| Contract path | `docs/migration/BOWFIN-NAME-MIGRATION-PLAN.md` |
| Contract blob | `03cd2c5b584a996ebfb873491f0d2888c984cfb9` |

If any of those identities changes, this acceptance no longer covers the changed
revision; renewed review and owner acceptance are required.

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
Steps 1 through 4 completed for the prior accepted revision identified above.
The changed discovery repair requires its own independent static review and
separate later execution/acceptance decisions. Replacement-input preparation was
separately authorized and is paused; neither that preparation nor the present
tooling-repair preparation permits production execution or evidence generation.

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

Filesystem snapshots are rooted at the repository root. Compiler-source evidence
must select the repository root itself: its view prefix is empty and its view tree
equals the commit's root tree. This makes every manifest path, selector, row path,
and occurrence key repository-relative and prevents distinct subtrees from sharing
the same coordinates. Tooling, compact inputs, observations, reviews, accepted
bases, and contracts may still use an explicitly selected eligible view. The
selected view must contain ordinary
directories and regular files only. Symlinks, special files, `.git`, and any
selected prefix or materialized path equal to or beneath `archive/unaccepted` are
rejected. Paths are relative POSIX UTF-8 strings; absolute paths, `.`/`..`,
backslashes, NUL, and non-NFC spellings reject.

Every source, accepted-base, contract, tooling, and compact-input snapshot is
accompanied by an `authenticated_git_export`. It carries the raw Git commit
object, repository-root tree, explicit `view_prefix` and `view_tree`, and a
complete root-to-view proof. Each proof node contains the complete ordered direct
entries of that Git tree, so the verifier reconstructs every tree on the path
from the commit root to the selected subtree. Siblings are authenticated only as
opaque mode/object identities; their bytes are neither supplied nor read.

The export then carries the selected view's complete ordered recursive
path/mode/blob-SHA-1/SHA-256/byte-count set. Verification reconstructs the view
tree, locally enumerates that filesystem subtree, and requires exact mode and byte
equality. Generator and auditor invoke this same reviewed authentication and
enumeration boundary; they do not independently enumerate the filesystem. The
expected prefix and view tree are independently supplied alongside the repository
commit and root tree. Selecting
`archive/unaccepted` is forbidden even when its opaque tree identity legitimately
appears in an ancestor proof. `synthetic_fixture` and
`current_accepted_dependency` eligibility classes are explicit and never
interchangeable.

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

Production compact inputs are not included in this protocol directory. A future
separately authorized input set contains:

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

Each external observation names a retained snapshot path plus its Git blob SHA-1
and SHA-256. The evidence record authenticates a closed observation export whose
path set exactly equals the registered surfaces. Observation metadata without the
corresponding retained bytes is not eligible evidence.

### 7.1 Mappings

Each mapping has a stable `mapping_id`, namespace, original identity, canonical
identity or explicit retention, and policy. `(namespace, original)` and
`(namespace, canonical)` are injective. Repeated occurrences do not violate
mapping injectivity.

### 7.2 Classification rules

Discovery and semantic classification are separate. Every interpretation carries
a physical `candidate_key` that excludes namespace, mapping, rule, role, and
canonical identity. Classifiers group interpretations by that key and must select
exactly one semantic interpretation for each physical candidate.

Selectors are a conjunction of reviewed literal fields only:

- `mapping_id` (required);
- `unit_kind` (required);
- exactly one path selector (`path_exact`, `path_prefix`, or `path_suffix`)
  or one nonempty, duplicate-free `candidate_keys` set (required);
- optional exact `json_pointer_prefix`, permitted only with a path selector.

Optional-field presence is significant: explicit null is not absence. Key lists
must contain only valid physical-key strings. A key selector cannot contain any
path selector or a JSON-pointer field, even if that other field is null. Both
runtime validators and the schema enforce this same language.

There are no regular expressions, globs, code expressions, plugins, or callbacks.
Historical rules require `path_exact` or exact `candidate_keys`; broad
historical exemptions reject.

Every rule records expected selected count, live/compatibility/historical role,
phase, rationale, representative and boundary context, producer, consumer,
support/removal policy, validation/test identity, and historical relationship.
One occurrence must match exactly one rule. Zero or multiple matches reject.
For classification as well as audit, `candidate_keys` denotes an **exact expected
population**, not merely permitted membership. Every listed key must resolve to
that rule's selected physical population; a nonexistent or otherwise unused key
rejects even when `expected_count` agrees. Counts remain a separate check.

### 7.3 Independent audit policy

`audit-policy.json` is independently authored and reviewed. Neither generator nor
auditor may derive it from `mappings.json` or `classification-rules.json`.
Discovery families use only bounded literal forms:

- exact UTF-8 literal;
- ASCII-case-insensitive literal;
- literal prefix followed by one or more ASCII digits; or
- exact source suffix/path component.

A `source_suffix` literal is a suffix of one path component. Forward or backward
slashes reject during policy validation; the scanner never interprets a suffix as
spanning directory boundaries. Non-ASCII component suffixes remain valid and use
UTF-8 byte coordinates.

Each family names its namespace and eligible unit kinds. A family may also name
an exact, nonempty, duplicate-free `candidate_keys` set. If present, every named
key must be rediscovered and only those physical candidates are emitted for that
family. This permits an independently reviewed audit policy to distinguish
identical spellings with different meanings without importing classification
rules.

The auditor receives no classification rules, canonical identities, roles,
phases, or historical exclusions. It reports both physical candidate keys and
semantic occurrence keys. Completeness is equality of exact occurrence-key sets,
never counts.
Discovery and retained-result validation reject competing semantic audit records
for one physical key. The retained validator resolves each record's family ID,
checks its namespace, unit kind and literal-family constraints, and requires exact
per-family key-population equality, including filtered families returning no rows.
The policy is taken from the authenticated compact-input export in evidence mode;
agreement with generated rows does not substitute for these policy checks.

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

## 9. Candidate key, occurrence key, and row

A candidate key is:

    sha256:<lowercase SHA-256 of canonical JSON tuple>

Its tuple is:

    [source_repository, source_tree, path, unit_kind, locator,
     original_identity]

It identifies discovered bytes and their intrinsic representation without
assigning a namespace or any classification meaning. The raw semantic unit kinds
`raw_text`, `embedded_identity`, and `machine_identifier` are normalized to
`raw_text` in this tuple because those distinctions are assigned only during
classification. All mapping interpretations of the same physical candidate
therefore share one candidate key.
The collision guard compares the complete normalized local descriptor (path,
physical kind, locator, original text), plus source-file hash and context. The
repository and source tree are fixed by the scan. Permitted differences in raw
semantic kind do not make a collision; differences in physical kind do. Package
verification also rejects a second emitted row for an already emitted physical
key, even when its semantic occurrence key is distinct.

An occurrence key is:

    sha256:<lowercase SHA-256 of canonical JSON tuple>

The tuple is:

    [source_repository, source_tree, path, unit_kind, locator,
     namespace, original_identity]

It contains only discovered identity and location, never classification result,
mapping ID, rule ID, canonical identity, role, or rationale. Generator and auditor
can therefore reconcile the same keys without sharing classification logic.

Each generated row records both keys plus exact location, source-file SHA-256,
original/canonical identity, namespace, role, phase, producer, consumer,
support/removal policy, validation/test identity, historical relationship,
mapping ID, rule ID, and bounded context. Rows sort by occurrence key bytewise.

Locators never use encounter order. Raw, embedded, and machine matches use exact
UTF-8 byte start/end coordinates. Path matches add component index and component
byte start/end. Structured matches use JSON Pointer plus value-local UTF-8 byte
start/end. The independently authored scanner can derive the same key without
sharing generator traversal state.

Retained verification treats path coordinates as an intrinsic claim, before
classification or audit-family meaning. For every `path_component` row, the
component index must resolve within the retained relative path, the byte range
must lie within that component, and the selected UTF-8 bytes must equal
`original` exactly. Recomputed keys and matching population sets cannot substitute
for this check: they can bind a self-consistent false tuple. The check consumes
the current verification-stage work budget before splitting or encoding the path.

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

`publication.json` is the package's completion marker. It binds the exact
`scan-manifest.json`, `index.json`, and `summary.json` digests and is created only
after every other package file has been written and synchronized. A package
without that exact marker is incomplete and rejects; the presence of a directory
alone is never publication.

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
manufacture semantic applicability from the label. It remains subject to the
observation's explicit age, event, evaluation-point, and point-in-time boundaries.
The required-surface register and observation set must match exactly. Each
not-applicable observation requires one decision bound to the exact canonical
observation, subject commit/tree, and eligibility policy. That decision resolves
to a retained canonical review body whose meaning—surface, disposition, subject,
reviewer, rationale, policy, limitations, and non-authority—is validated rather
than inferred from its pathname or blob identity. Other observations must have no
applicability review. Human process corroboration remains separate.

Offline regeneration consumes retained inputs only and never refreshes them.

## 12. Evidence derivation binding

An evidence record does not choose its own trusted tooling. The verifier receives
the accepted tooling repository, commit, root tree, selected view, view tree, and
export digest independently from the record. The selected tooling view must
contain the exact required set: `PROTOCOL.md`, `README.md`, `audit_scan.py`,
`generate.py`, `limits.json`, `protocol_lib.py`, `schema.json`, and `verify.py`.

After structural package verification, the verifier independently relates every
row back to the compact inputs. Its mapping ID must resolve to the exact retained
namespace, original, and canonical identities. The verifier indexes all rules by
original spelling and normalized physical kind, rather than by the row's chosen
mapping. It independently accounts for the raw semantic kind discoverable in each
namespace and examines competing mappings and raw semantic kinds. Exactly one
applicable reviewed rule must match the physical candidate's path/pointer or key;
that rule must name the emitted mapping and semantic unit. A hidden competing
rule rejects even if its declared expected count is zero. An undiscoverable
zero-count path rule is not a competing interpretation.
The row's role, phase, producer, consumer, support policy, validation identity,
historical relationship, rule ID, and per-rule population must agree with that
rule. A self-consistent rehash after altering classification meaning rejects.

The evidence record also binds the exact independent-audit bytes. Reconciliation
parses the same single byte buffer whose SHA-256 is recorded; it never reopens the
audit pathname for semantic validation. It checks source, input-export, and
scan-manifest identities and requires exact occurrence-key equality with the
semantically bound package rows. It receives the authenticated `audit-policy.json`
from the same compact-input view and enforces the family/population requirements
of §7.3 before set reconciliation. A freshly rehashed audit result that omits a
declared key or invents a family remains invalid.

## 13. Deterministic versus runtime provenance

Deterministic output contains exact repository/tree/blob identities, canonical
inputs, file hashes, rows, indexes, summaries, and limitations. Acquisition time,
evaluation time, runner identity, workflow URL, duration, and capture method live
in separate runtime provenance or decision records and are never inputs to
deterministic package bytes except where a retained external observation itself
is the explicit reviewed input.

## 14. Shared components and independent failure modes

Generator, auditor, and verifier deliberately share the authenticated Git-export
boundary, fatal filesystem enumeration, source JSON parsing, manifest
construction, strict JSON, canonical encoding, SHA-256, path validation,
physical- and semantic-key construction, and bounded file I/O. That shared
boundary proves which bytes both scanners received; it is a disclosed common-mode surface, not an
independent enumeration claim. Generator rule matching and structured traversal
are not imported by the auditor. Auditor matching, traversal, and discovery policy
are not imported by the generator. The verifier does not call either scanner when
checking package structure.

Shared authentication, parsing, manifest, and primitive defects remain a
common-mode risk and must be disclosed in review. Synthetic expectations therefore
include literal precomputed keys/digests, independently specified Git-object
vectors, and mutation cases that do not ask the candidate generator or shared
export constructor to define its own oracle.

Literal discovery uses separate implementations. The auditor retains its own
per-family KMP matcher. The proposed generator uses one first-character literal
index per discovery stage, with a single position-dispatch traversal of each path
component, raw text, and decoded JSON key/value. Equal spellings share comparison
work but retain every original mapping/namespace binding. Every shorter/longer
overlap is emitted; dispatch does not select a semantic interpretation.

Generator index construction charges `8 + 2 * len(original)` per mapping before
string hashing/equality, bucket insertion, and binding append. Each scanned position costs
two units before its first-character lookup; each relevant distinct literal costs
two before its remaining-length check; each suffix-character comparison costs
three before the character accesses; each emitted binding costs one before yield.
The stage also precharges twice the source-byte count for hashing/UTF-8 decoding,
the raw character count before its single offset map, twice each path-component
character count before offsets/encoding, and `1 + len(pointer) + 2 * len(value)`
before structured offsets/encoding. Existing physical-key, materialization,
occurrence-count, classification, and verification charges remain in force.

The generator stores references to bounded literal strings, not a trie with a
node per character. With dense shared first-character/prefix populations, suffix
comparison work can still grow with the relevant bucket and literal lengths.
There is no universal linear-time, wall-clock, or production-feasibility claim;
the unchanged stage-local processing limit must reject excess work. Auditor
prefix construction, character comparisons, match materialization, digit-suffix
traversal, offset construction, and structured traversal retain their existing
charges. No matching logic is shared between generator and auditor.

The generator's cost schedule changes, not the normative limit. Budget-dependent
accept/reject outcomes can therefore differ in either direction, including dense
prefix inputs that the older per-literal KMP traversal handled more efficiently.
When discovery completes, its full candidate interpretations and intrinsic
coordinates must agree; encounter order is not canonical package row order.

Package verification charges the
cumulative serialized-byte budget before each document or chunk read; it never
first materializes an over-budget package and rejects afterward. Classification-
meaning verification indexes rules by spelling and normalized physical kind,
then charges index construction, lookups, selector checks, string comparisons, semantic comparisons,
and population accounting before or during that work.

The occurrence-semantics repair additionally precharges key-list validation and
set construction, complete descriptor comparisons, physical-key encoding/hashing,
and exact-set exhaustion. `charge_value` incrementally charges 64 units per value
and per string character; container slots cost 64 each, object ordering adds a
quadratic member-count envelope, and object keys additionally cost 64 times their
length times the member count. This deliberately covers UTF-8/JSON expansion,
ordering, hashing and repeated comparisons without encoding or copying first.
Exact-key set construction validates each bounded, fixed-width key before adding
it. Exhaustion charges `128 * 72 * (1 + actual_count + declared_count)` before
comparison, on success and failure alike. Linear selector searches charge each
comparison, including unsuccessful first/last/missing cases. Processing loops pass
their existing stage-local `WorkBudget` into physical-key creation; they do not
reset it for each key. Limits are unchanged. These are conservative logical-work
accounting rules, not measured CPU or wall-clock guarantees or a new global budget
across independent stages.

Physical-key agreement between scanners cannot validate their shared primitive.
The new fixed vectors state hand-selected physical tuples, literal canonical bytes
and independently computed digests. Audit filters in the mixed-role and overlap
controls use these fixed expectations, not generator discoveries.

## 15. Rejection behavior

The tools return zero only for a satisfied command. Failures return nonzero and a
stable code on stderr. Required failures include duplicate JSON keys, unknown
fields/enums, non-injective mappings, empty/broad selectors, unmatched or multiply
matched occurrences, expected-count mismatch, key-set mismatch, digest mismatch,
bad ordering/chunking, stale freshness, path escape, symlink/special file, archive
dependency, excessive size/depth/count, and output overwrite.

The package destination must not exist. Creation ownership begins only after the
exclusive directory creation succeeds. A losing concurrent invocation never
removes or modifies the winner's destination. A failed package write deliberately
does not recursively clean its directory, because pathname-based cleanup could
race with replacement by another process. Individual failed documents remove only
the exact regular-file identity they created. `publication.json` is written last,
so abandoned or externally interrupted directories cannot validate as complete
packages and must be inspected before human removal.

Individual documents use exclusive, no-follow creation beneath an
already-existing non-symlink parent. Bounded reads inspect the named path before
opening it, reject non-regular files, use no-follow and nonblocking flags where
available, and verify that the opened descriptor is the inspected file. A FIFO
therefore rejects before an operation that could wait for a writer. Row, chunk,
aggregate, generated-byte, and processing budgets are charged before or during
work. An existing destination rejects.

## 16. Retention, transfer, recovery, and R8

### Integration content constraints (P12/P21–P24 repair)

The binding command takes repeated `--expected-source-change-path` arguments.
Their exact set must be independently reviewed against the compiler content
policy for the exact C base and final head; copying a candidate-supplied list is
not independent review. Omission means an empty change set, not unrestricted
permission. The set must equal the actual base-to-final changed paths. In every
introduced C tree, other paths retain their base objects and modes. An approved
path may contain only its base or reviewed-final object/mode (including absence).
Transient third states reject, even when later deleted. This conservative policy
may require a newly prepared clean candidate; it never authorizes history rewrite.
It does not mechanically determine whether approved final content is appropriate.

E carries an `index_record` with canonical bytes, Git blob identity, and SHA-256.
Its path is `evidence/m0.1/<C-commit>/generated/index.json`; its authenticated
SHA-256 must equal `E.index_sha256`. This binds index bytes, not package semantic
validity, which remains the separate evidence-verification obligation.

Each review, owner-decision, and later recovery commit must preserve its entire
parent tree and add exactly its bound regular-file record under `decisions/`.
The path must be new and outside the protected evidence package. No deletion,
replacement, mode change, or unrelated addition is allowed. Boolean declarations
are checked by exact type before body equality; JSON zero/one cannot substitute.

Opaque full-history inventories and recovery graphs allow Git symlink mode
`120000` as a blob reference only. Active materialized views still prohibit it;
bound JSON records must be regular files. Every recovery edge checks presence and
expected kind before the visited-object shortcut. An unreadable listed object
(`E_FILE_READ`) is normalized to `E_RECOVERY_BUNDLE`; other filesystem safety and
resource diagnostics retain their original codes.

These additions received independent static review and passed the separately
authorized bounded synthetic run. That result supports acceptance of this exact
protocol/tooling revision only; it is not production or migration evidence.

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

The C/E/D/P receipt carries raw commit objects and complete flat tree inventories;
the verifier reconstructs every named Git tree rather than accepting a tree hash
as an assertion. C and E each include an ordered, nonempty introduced-commit chain
from accepted base to reviewed head. Every introduced commit must have exactly the
prior commit as its sole parent, so no unlisted merge parent or side ancestry can
enter the reviewed range.

P verifies merge parents, resulting trees, and integrated heads. Repository names,
target branches, merge commits, and the recovery ref are supplied independently on
the verifier command line and must match the receipt; consistently changing every
candidate-controlled label therefore cannot retarget integration. Review, owner,
and recovery records carry their canonical JSON bytes, blob identities, digests,
paths, and containing commit trees. The verifier checks their complete semantic
bodies as well as their ancestry. Human identity and authority still require the
governed process; strings inside those records do not create authority.

Recovery uses a bounded directory containing a canonical manifest and raw Git
objects. The manifest digest binds every retained ref and object descriptor. Each
object's byte count, SHA-256, Git object identity, type, and canonical path are
checked. Traversal from the independently expected restored ref must find the
complete reachable commit/tree/blob graph, including the exact E base and
introduced commits. A separate post-integration ledger commit binds the canonical
recovery-evidence body. Backup or recovery hashes without the corresponding
authenticated objects are insufficient.

## 17. Synthetic test boundary

Fixtures beneath `tests/fixtures/` are synthetic protocol tests. They are not
compact production inputs, migration evidence, source classifications, owner
decisions, or authority. Mutation expectations are handwritten and versioned.

The required suite covers valid deterministic generation; repeated regeneration;
duplicate keys; non-NFC text; non-injective mappings; unknown kinds; hidden paths;
case variants; structured keys/values; overlapping identities; equal-count but
different-key substitution; stale rules; missing/extra/reordered/tampered chunks;
oversized rows; depth/count limits; symlinks/path escape; archive roots; unchanged
bytes with expired freshness; invalidating events; and C/E/D/P finite-sequence and
recovery-record shape. It also covers competing package creation, interrupted
single-document writes, FIFO inputs, missing completion markers, cumulative
package-byte exhaustion before the next read, and adversarial no-match discovery
that exhausts the comparison budget. Positive controls are listed separately from
mutation cases. They cover a single immutable audit read, one shared protocol-
exception identity, complete occurrence-key identity where different structured
units legitimately share a locator, fresh fixture state for each mutation,
classification-meaning budget exhaustion, numeric substitution for Boolean review
fields, and rejection of non-root compiler-source views.

The accepted occurrence-semantics controls add all three normalized raw kinds;
independent physical-key vectors and overlapping short/long spellings; two-row
physical duplicates and a one-row hidden competing path rule with zero expected
count; retained-audit phantom/missing keys and unknown/wrong families; forged
physical keys with valid semantic keys; malformed/null selector properties;
normalized collision descriptors; exact classification populations; and targeted
key-list, construction, exhaustion, grouping and linear-search budget failures.
Malformed retained packages are rebuilt with current descriptors; retained audit
mutations are re-encoded before reconciliation.

The BML-OS08–10 follow-up adds an impossible retained filename claim, wrong
component and wrong span, a valid Unicode-path claim, malformed cross-component
source suffixes, and a multibyte source-suffix positive. It also retargets the
predecessor incremental-budget control: an independently stated pre-candidate
cost permits all rule precharging and index construction, then observes rejection
on the first candidate descriptor. BML-OS11 corrected the fixed crate-overlap
vector without weakening population enforcement.

The prior accepted occurrence-semantics repair received independent static review and one separately
authorized bounded run in which all 54 authored tests passed. Both one-run
authorizations are exhausted. The existence or acceptance of these files grants
no production execution, evidence generation, M0.1 acceptance, or later authority.

The proposed discovery-efficiency repair adds six authored methods and the
independently specified `discovery-dispatch.json` fixture. A 6,064,042-character,
195-mapping synthetic control reproduces the old algorithm's unavoidable
2,371,040,422-step floor arithmetically. It requires the new discovery to return
four exact fixed-key records, including the short spelling inside a longer one,
under a 40,000,000-unit control ceiling without changing normative limits. Other
controls cover Unicode offsets across hidden paths/raw text/JSON keys and values;
all short/long overlaps and duplicate-spelling bindings under reordered mappings;
single-character and incomplete-tail literals; precharge at index construction,
position, comparison, emission, source hashing, and raw/path offset-map boundaries;
and dense-prefix no-match
exhaustion. All 54 predecessor method bodies and the existing fixture vectors
remain intact; the mutation manifest is extended without changing prior entries.
The new fixture is synthetic and is not a production input or evidence package.
These 60 authored methods have not been executed at this changed revision.
