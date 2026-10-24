# Bowfin Migration Ledger

**Status:** Foundation proposed for review. This repository is an audit surface for the staged Klyxr-to-Bowfin migration. It grants no product, execution, release, approval, replay, custody, resource, or merge authority.

## Purpose

This repository may hold:

- compact, typed migration mappings and classifications;
- deterministic generators and validators;
- reproducible generated inventories, digests, and bounded scanner limitations;
- phase reports and independent review records;
- byte-truthful, explicitly unaccepted historical snapshots; and
- exact links between source candidates and the evidence used to evaluate them.

It must not become a runtime, build, packaging, or release dependency of Bowfin.

## Governing source

The current governing migration contract remains in `gregkrsak/klyxr`:

| Item | Exact identity |
| --- | --- |
| Integration branch | `bowfin-migration-staging` |
| Accepted staging commit | `37cb00d5cc01804e46446809fd325322c0c3f05f` |
| Accepted staging tree | `d817671d87760f62a603d2de2f696fe49f0a24ac` |
| Contract path | `docs/migration/BOWFIN-NAME-MIGRATION-PLAN.md` |
| Contract blob | `2d03f764b3fb516bc8d18c4e32a26c5c06a4d3fa` |
| Production commit, unchanged | `3c0a540df7d5ad75510db4ecad80e27fb4d0903a` |
| Production tree, unchanged | `928accaa6c71068a6bce273f73f8c152b4c4d348` |

The compiler repository and its accepted migration contract remain authoritative for product behavior and migration acceptance. This ledger cannot amend that contract. Recognition of this repository as a migration-evidence surface requires a separately reviewed amendment in the compiler repository.

## Binding model

A ledger record binds to an exact source repository, commit, and tree. After the ledger commit exists, the corresponding source PR acceptance record may link the exact ledger commit, tree, and relevant digests. The product candidate does not embed a self-referential ledger hash.

Independent review must verify both sides of that relationship. A green ledger check is evidence; it is never authorization.

## Content policy

For current migration evidence, commit compact sources of truth, schemas, generators, validators, reports, and evidence that must remain independently inspectable. Generated inventories used as current evidence must be reproducible and justified. A large materialized snapshot does not become accepted evidence merely because it can be generated or stored here.

### Unaccepted historical snapshots

A separately authorized import may preserve rejected or superseded material under the explicit class `UNACCEPTED_HISTORICAL_SNAPSHOT`. Its payload is retained byte-for-byte as an object of history. New classification, provenance, limitations, reproduction results, and corrections live outside the payload in an archival wrapper.

Archival copy integrity and payload completeness are distinct from reproduction or semantic correctness. Reproduction may be recorded as `unattempted`, `succeeded`, `failed`, or `limited`; successful reproduction is not a prerequisite for truthful preservation. Archived scripts, instructions, and workflows are inert payloads, not current tooling or governing instructions.

Merging an archival snapshot permits retention only. It does not validate the snapshot's claims, adopt its architecture or tooling, accept a migration phase, satisfy a compiler gate, or authorize later work.

Do not commit secrets, credentials, authority tokens, caches, build outputs, or executable approvals. Do not rewrite evidence used to accept a source candidate or the payload of an unaccepted historical snapshot.

## Lifecycle

Greg remains the sole human merge authority. Migration work proceeds through reviewed pull requests. After release state R8, this repository should be archived read-only unless a later accepted decision establishes a continuing purpose. That preservation includes accepted evidence and unaccepted historical snapshots without converting either one's recorded status.

See [docs/LEDGER-BOUNDARY.md](docs/LEDGER-BOUNDARY.md) for the detailed boundary and [evidence/README.md](evidence/README.md) for the proposed evidence layout.
