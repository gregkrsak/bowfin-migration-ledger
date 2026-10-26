# Bowfin Migration Ledger

**Status:** Accepted descriptive-ledger foundation and accepted M0.1 v2
protocol/tooling revision. Production compact inputs, migration evidence, M0.1,
and M1 remain separately gated and unaccepted. This repository grants no product,
execution, release, approval, replay, custody, resource, or merge authority.

## Purpose

This repository may hold:

- compact, typed migration mappings and classifications;
- deterministic generators and validators;
- reproducible generated inventories, digests, and bounded scanner limitations;
- phase reports and independently preserved review and owner-decision records;
- byte-truthful, explicitly unaccepted historical snapshots; and
- exact links between source candidates and the evidence used to evaluate them.

It must not become a runtime, build, packaging, or release dependency of Bowfin.

## Governing source

The governing migration contract remains in `gregkrsak/klyxr`:

| Item | Exact identity |
| --- | --- |
| Integration branch | `bowfin-migration-staging` |
| Accepted staging merge commit | `609822762abd46c13ecd6187ccc8510695e52b2f` |
| Pre-merge test object, not integration | `9feb01fb68ebb72dfb7f0d6781e8e65b01b3c56d` |
| Accepted staging tree | `ebaf5e4b7b6a7a09acc693db52e3cdc5e0ec2239` |
| Accepted Amendment 2 candidate | `0ca819ab9f627f586df453c7a97a55c9a9694bf3` |
| Contract path | `docs/migration/BOWFIN-NAME-MIGRATION-PLAN.md` |
| Contract blob | `03cd2c5b584a996ebfb873491f0d2888c984cfb9` |
| Production commit, unchanged | `3c0a540df7d5ad75510db4ecad80e27fb4d0903a` |
| Production tree, unchanged | `928accaa6c71068a6bce273f73f8c152b4c4d348` |

M0 Amendment 2 recognizes this repository as the separate evidence surface for
the replacement Rule-to-Occurrence Ledger. The compiler repository and its
accepted migration contract remain authoritative for product behavior and
migration acceptance. This ledger cannot amend that contract.

## Binding model

The controlling chain is acyclic:

- **C** — one fixed compiler candidate commit and tree;
- **E** — one immutable ledger evidence package identifying C and every exact
  dependency;
- **D** — later preserved review and owner-decision records identifying C and E;
  and
- **P** — a later integration receipt identifying the actual source and ledger
  merges and proving correspondence.

E cannot contain its own future commit. C cannot be changed after E is generated
to embed E. A passing ledger check is evidence; it is never authorization.

Any change to the source candidate, accepted base, governing contract, accepted
tooling, compact inputs, or required external/visual snapshot invalidates the
corresponding evidence binding. There is no informal relevant-drift exception.

## Accepted M0.1 v2 protocol/tooling boundary

The original M0.1 v2 protocol/tooling revision was accepted through PR #3. The
current accepted content includes the independently reviewed occurrence-semantics
repair at head `23bed495c73b600d0a849b3c336d08a5c6cdd1b1`, tree
`c642dca4c4b8ae4e08f1250e1862bbe821c43b04`, and protocol subtree
`d0e0c7419020415ddc7996631db616b2f73a25b3`, integrated by ordinary merge
commit `ef9574336edf2b16aae4308330d581f0bacb6e45` through PR #6. The original
acceptance and adverse repair history remain preserved.

This acceptance makes that exact protocol/tooling revision eligible as a current
M0.1 dependency. It does not authorize production classification inputs, scanner
execution against the compiler repository, migration evidence generation, M0.1
acceptance, M1, or later work. See the preparation authorization and protocol-
tooling acceptance records under `decisions/m0.1/`.

## Content policy

For current migration evidence, commit compact sources of truth, schemas,
generators, validators, reports, and evidence that must remain independently
inspectable. Canonical generated occurrence evidence is bounded, uncompressed
JSONL with an authenticated index. Generated inventories must be reproducible and
justified. A large materialized snapshot does not become accepted evidence merely
because it can be generated or stored here.

Decisive reviews, owner decisions, corrections, revocations, and integration
receipts are preserved as append-only, content-addressed records outside the
immutable evidence package they describe. GitHub comments and chat are publication
venues, not immutable authority storage. Latest-comment, newest-timestamp, and
author-name-string rules are forbidden.

### Unaccepted historical snapshots

A separately authorized import may preserve rejected or superseded material under
the explicit class `UNACCEPTED_HISTORICAL_SNAPSHOT`. Its payload is retained
byte-for-byte as an object of history. New classification, provenance,
limitations, reproduction results, and corrections live outside the payload in an
archival wrapper.

Archival copy integrity and payload completeness are distinct from reproduction
or semantic correctness. Reproduction may be `unattempted`, `succeeded`, `failed`,
or `limited`; success is not required for truthful preservation. Archived scripts,
instructions, schemas, fixtures, generators, validators, and workflows are inert
and permanently ineligible as current protocol dependencies.

Merging an archival snapshot permits retention only. It does not validate claims,
adopt architecture or tooling, accept M0.1, satisfy a compiler gate, or authorize
later work.

Do not commit secrets, credentials, authority tokens, caches, build outputs, or
executable approvals. Do not rewrite evidence cited by an accepted record or the
payload of an unaccepted historical snapshot.

## Lifecycle

Greg remains the sole human merge authority. Migration work proceeds through
reviewed pull requests using ordinary merge commits where the accepted contract
requires them. After release state R8, this repository should be archived read-only
unless a later accepted decision establishes a continuing purpose. Preservation
does not convert accepted evidence or unaccepted snapshots into another status.

See [docs/LEDGER-BOUNDARY.md](docs/LEDGER-BOUNDARY.md),
[evidence/README.md](evidence/README.md), and
[protocol/m0.1/v2/PROTOCOL.md](protocol/m0.1/v2/PROTOCOL.md).
