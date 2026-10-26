# Ledger Boundary

**Status:** Accepted descriptive-ledger foundation, subordinate to the accepted
migration contract in `gregkrsak/klyxr`. This repository cannot amend or replace
that contract. The M0.1 v2 protocol/tooling revision, including the exact
occurrence-semantics repair merged by ledger PR #6 and budget-only profile merged
by ledger PR #9, is accepted; production inputs, migration evidence, M0.1, and M1
remain unaccepted.

## 1. Controlling question

> What new power does this create, where is that power bounded, and can we explain the answer plainly?

The ledger creates the power to record, reproduce, compare, and review migration
evidence. That power is bounded to description and verification. It creates no
power to execute Bowfin programs, approve operations, recover authority, assume
custody, consume resources, merge code, publish packages, change domains, rename
repositories, release software, accept M0.1, or begin M1.

## 2. Allowed responsibilities

The ledger may:

1. record exact source, contract, tooling, input, evidence, and merge identities;
2. store compact typed mapping and occurrence-classification inputs;
3. store deterministic schemas, generators, independent auditors, and validators;
4. preserve bounded canonical inventories and digests when retention is justified;
5. document scanner coverage, external-surface freshness, and limitations;
6. preserve append-only review, owner-decision, correction, revocation, and
   integration records;
7. preserve byte-truthful rejected or superseded material under the explicit class
   `UNACCEPTED_HISTORICAL_SNAPSHOT`; and
8. provide stable links used by source-repository acceptance records.

## 3. Prohibited responsibilities

The ledger must not:

- become a source of product semantics or runtime behavior;
- substitute for the compiler repository's migration contract;
- manufacture or carry executable approval, grants, replay identity, custody,
  schema validity, or resource authority;
- execute candidate compiler, governance, or archive code merely to inspect data;
- modify another repository or external service without separate authorization;
- make review equivalent to acceptance;
- make passing checks equivalent to owner authorization;
- derive authority from names, timestamps, ordering, comments, or matching hashes;
  or
- become necessary to build, install, run, or recover a released Bowfin toolchain.

## 4. Exact evidence identity

Every current M0.1 evidence record must identify at least:

| Field | Meaning |
| --- | --- |
| `record_class` | Exactly `migration_evidence` |
| `protocol_version` | Exact accepted protocol version |
| `phase` | Exactly `M0.1` for this gate |
| `source` | Exact repository/commit/tree plus authenticated export for C |
| `accepted_base` | Exact repository/commit/tree plus authenticated export |
| `governing_contract` | Repository, commit, tree, path, and blob |
| `tooling` | Ledger repository, accepted commit/tree, paths, and blobs |
| `inputs` | Exact eight-file set, aggregate digest, and authenticated export |
| `observations` | Closed retained-snapshot set with authenticated bytes |
| `reviews` | Closed applicability-review set with authenticated content |
| `generated` | Manifest, index, summary, publication-marker, chunk, and aggregate identities |
| `non_authority` | Explicit denials of executable or decision authority |

Required fields may not be inferred from directory names, branch names, issue
numbers, comments, timestamps, or conversational context. Unknown mapping kinds,
roles, or required status records fail closed.

The verifier receives the accepted tooling identity independently of the evidence
record and requires the fixed protocol artifact set. Generated rows are related
back to their exact mapping and uniquely matching rule; retained observation and
applicability-review bytes are authenticated and their semantic relationships are
checked. Coexistence of individually valid hashes is not evidence derivation.

Compiler-source evidence must use the repository-root view, so source paths and
occurrence identities remain repository-relative and unambiguous. Other dependency
classes may retain authenticated selected views. Independent-audit binding hashes,
parses, and reconciles one immutable read rather than reopening a pathname.

Generator and auditor intentionally share the authenticated Git-export boundary,
fatal filesystem enumeration, source-JSON parser, and manifest constructor. That
establishes a common byte universe but is not independent enumeration. Their
matching and structured traversal remain separate, and review must retain the
shared-boundary limitation and independently specified Git-object vectors.

Authenticated exports carry raw commit objects, repository-root trees, explicit
eligible-view prefixes and trees, and complete root-to-view Git tree proofs. Each
proof node supplies all direct entries required to reconstruct that tree. Opaque
siblings—including the preserved archive—remain authenticated object identities
without becoming readable or eligible dependencies. The selected view carries a
complete ordered path, mode, blob-SHA-1, SHA-256, and byte-count inventory; the
verifier reconstructs its subtree and compares every materialized path, mode, and
byte. A manifest that only names a commit, names a subtree, or hashes itself does
not prove correspondence.

An unaccepted historical snapshot instead uses its archival wrapper and records
origin repository/reference, origin commit/tree, imported path set, sizes, and
payload identities. Origin identity and a payload's claimed-source identity remain
separate and establish no semantic correctness.

## 5. Acyclic C/E/D/P chain

The controlling sequence is:

1. **C:** one compiler candidate is fixed at an exact commit and tree, including
   any accepted minimal compiler-side anchor.
2. **E:** one ledger evidence package identifies C, the accepted base, governing
   contract, accepted protocol/tooling, compact inputs, required snapshots, and
   generated outputs.
3. **D:** later preserved review and owner-decision records identify the exact C
   and E dispositions.
4. **P:** a later receipt identifies actual source and ledger merge commits, trees,
   parents, targets, and correspondence to C, E, and D.

E cannot identify its own future commit. C cannot be modified after E is generated
to embed E. P proves post-merge correspondence; it does not replace C or E.
Publication of P is itself represented without requiring P to contain its own
future storage identity.

Every change to C, the accepted base, governing contract, protocol/tooling,
compact inputs, or a required external/visual snapshot invalidates the applicable
binding and requires a new package and renewed disposition. Equal generated bytes
or counts do not create a drift exception.

Source and evidence integrations use ordinary merge commits. Pre-merge test-merge
SHAs are not post-merge proof. Introduced ancestry must reject prohibited bulk
compiler evidence even if later deleted from the final tree.

C and E record their complete introduced first-parent commit chains, not only
endpoints. D records authenticated review and owner-decision commits. P records
raw source and ledger merge objects and verifies exact parents, resulting trees,
integrated heads, and target branches.

## 6. Decision records

GitHub comments and chat messages are publication venues, not immutable storage.
Every decisive review, owner decision, correction, revocation, and integration
record is preserved append-only outside the immutable evidence package it
describes.

Each record retains the complete body, source URL/identifier when available,
stated author and publisher context, capture time/method, body digest, applicable
C/E/D/P identities, and verification limitations. A copy plus digest does not
authenticate authority by itself; process corroboration remains required.

Structural validity, independent-review disposition, Greg's acceptance/rejection,
integration status, and next-phase authorization are separate states. Missing,
conflicting, superseded, or unverifiable records fail closed. Latest comment wins,
newest timestamp wins, and author-name string matching are prohibited.

Integration correspondence is not established by labels carried only inside a
candidate record. The verifier receives expected source and ledger repositories,
target branches, merge commits, and recovery ref independently. It reconstructs
every named commit tree from a complete inventory, requires each introduced C/E
commit to be the sole-parent descendant of the prior commit, and authenticates the
canonical review and owner-decision bodies through their exact blobs and containing
trees. These checks establish byte and ancestry correspondence; governed human
process remains the source of review and owner authority.

## 7. Authority and failure behavior

Evidence may block acceptance when missing, stale, inconsistent, ambiguous, or
outside coverage. Evidence cannot cause acceptance.

Ledger unavailability during migration blocks only gates requiring ledger
evidence. It must not prevent normal compiler build, check, verify, run, failure
recovery, or accepted production operation.

Greg remains the sole merger. If that assumption changes or automated merging is
introduced, migration work stops until the governing contract establishes an
independently reviewed control.

## 8. Immutability and correction

Once evidence is cited by an accepted record, or an unaccepted snapshot is merged:

- commit and tree identities remain historical facts;
- canonical evidence and archived payload bytes remain unchanged;
- corrections and revocations are new append-only records;
- history is not rewritten to make an old claim appear correct; and
- original bytes and digests remain inspectable regardless of disposition.

## 9. Unaccepted historical snapshots

`UNACCEPTED_HISTORICAL_SNAPSHOT` is a preservation class, never a status capable of
satisfying a migration gate. Its payload remains byte-for-byte under
`archive/unaccepted/**`; all new provenance, limitations, reproduction results,
and corrections remain outside the payload.

Archived scripts, validators, instructions, schemas, fixtures, and workflows are
inert and permanently ineligible as current tooling or dependencies. A new path,
copy, import, or matching digest cannot promote them. Successful copy or
reproduction establishes neither semantic correctness nor acceptance.

The closed first M0.1 attempt may remain preserved, but it cannot supply current
classifications, schemas, fixtures, tools, completeness claims, or acceptance
evidence.

## 10. M0.1 v2 preparation and execution gate

The accepted compiler contract now recognizes this ledger's Rule-to-Occurrence
architecture. Greg separately authorized preparation of the protocol specification
and tooling. Preparation permits a draft PR containing schemas, limits, source,
synthetic fixtures, and tests.

Unreviewed candidate tooling is not executed. An independent reviewer first
examines the exact revision statically. Greg may then authorize isolated synthetic
self-test execution of that same revision. Production compact inputs and evidence
generation require another later authorization after tooling acceptance.

That protocol/tooling sequence first completed through PR #3. The current
accepted revision includes the occurrence-semantics repair at reviewed head
`23bed495c73b600d0a849b3c336d08a5c6cdd1b1`, tree
`c642dca4c4b8ae4e08f1250e1862bbe821c43b04`, and protocol subtree
`d0e0c7419020415ddc7996631db616b2f73a25b3`, integrated by ordinary merge
commit `ef9574336edf2b16aae4308330d581f0bacb6e45`. Durable review, owner-decision,
and merge records for those acceptance steps remain preserved under `decisions/m0.1/`.

The later budget-only profile was reviewed/tested at
`62a19baf0f67474f0c25c609f9a4300aa11e74d4`, tree
`27a18b261d8f5325c2414ad9e18193e91b870a37`, protocol subtree
`cd514c89fda2d91318c7a63b8b737118141f7b2c`, and integrated through PR #9 by
ordinary merge `4020cb64c1119ccfb4a4bc77b3f39e8b698ba2f5`. That merge retains
the exact reviewed tree and has the prior-main and reviewed-head parents in that
order. The immutable merge identifies the accepted tooling dependency, not the
head of a later documentation closeout.

Only the stage-local `max_processing_steps` ceiling, its mandatory digest pin,
and profile documentation changed. The new finite ceiling is 100,000,000,000
logical steps per WorkBudget, not a process-wide CPU/time/memory allowance.
Algorithms, charge sites, and all other limits remain unchanged. One contained
Actions invocation passed the unchanged 54-test synthetic suite; Sarah confirmed
the external execution evidence independently. No production feasibility follows
from that result, and the invocation authorization is exhausted.

The work-budget closeout preserves both full reviews, the validation capture,
owner-process context, and verified merge correspondence under `decisions/m0.1/`.
The capture is copied byte-for-byte from PR #10's preservation commit; no workflow
or helper is imported. PR #10 is a separate operational/preservation surface,
not an accepted tooling dependency. This closeout is not a C/E/D/P production-
evidence integration receipt and does not repair or accept PR #5 or adopt
PR #8's scanner rewrite.

No protocol review, test result, tooling merge, or ledger record accepts M0.1 or
authorizes M1.

## 11. External and visual surfaces

Every relevant surface is inspected, demonstrably not applicable, explicitly
limited, or unavailable. Failure or inaccessibility is not not-applicable.

Every external observation names retained snapshot bytes. Not-applicable status
also names a retained canonical review body and explicit eligibility policy bound
to that exact observation and subject. Expiry, point-in-time limits, or a named
invalidating event rejects the decision even when the subject tree is unchanged.

External acquisition is separate from deterministic generation. Each required
surface class has a reviewed freshness policy with a justified observation window,
named invalidating events, bounded point-in-time treatment, or a reviewed
combination. Eligibility is evaluated before owner acceptance and immediately
before integration and fails closed even when snapshot bytes are unchanged.

Visual evidence binds exact blobs and records scope, method, reviewer, regions,
whole-image inspection, and limitations. Listed regions never substitute for
complete inspection.

## 12. Retention, recovery, transfer, and retirement

Canonical generated occurrences are bounded, uncompressed JSONL with an
authenticated index and a last-written completion marker. Missing markers and
packages that exceed their cumulative read budget fail closed. Compression is
transport only; expiring workflow artifacts, caches, attachments, and object-store
URLs are never sole evidence.

Accepted protocol, inputs, evidence, decisions, and receipts remain reachable in
Git plus a documented backup/recovery path. Repository transfer records old and
new identities without rewriting history. After R8, archive this repository
read-only unless a later accepted decision defines a continuing role. Retirement
does not erase or reclassify evidence or archives.

Recovery evidence includes the bounded on-disk object bundle, not merely a digest
claim. A canonical manifest binds its refs and every object descriptor; verification
checks byte counts, SHA-256, Git object identities and kinds, exact bundle paths,
and the complete commit/tree/blob graph reachable from the independently expected
ref. The canonical recovery result is itself bound into a separate post-integration
ledger commit. Missing objects, unexpected paths, or unbound recovery prose fail
closed.
