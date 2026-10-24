# Ledger Boundary

**Status:** Proposed foundation. This document governs work inside this repository only. It is subordinate to the accepted migration contract in `gregkrsak/klyxr` and cannot amend or replace that contract.

## 1. Controlling question

> What new power does this create, where is that power bounded, and can we explain the answer plainly?

Creating this ledger creates the power to record, reproduce, compare, and review migration evidence. That power is bounded to description and verification. It creates no power to execute Bowfin programs, approve operations, recover authority, assume custody, consume resources, merge code, publish packages, change domains, rename repositories, or release software.

## 2. Allowed responsibilities

The ledger may:

1. record exact source commit and tree identities;
2. store typed mapping and occurrence-classification inputs;
3. store deterministic schemas, generators, and validators;
4. preserve generated inventories and digests when their retention is justified;
5. document bounded scanner coverage and limitations;
6. preserve phase reports and independent review records; and
7. provide stable links used by source-repository acceptance records.

## 3. Prohibited responsibilities

The ledger must not:

- become a source of product semantics or runtime behavior;
- substitute for the compiler repository's migration contract;
- manufacture or carry executable approval, grants, replay identity, custody, schema validity, or resource authority;
- execute candidate compiler code merely to inspect migration metadata;
- modify the compiler repository, governance repository, domains, registries, releases, or repository settings without separate authorization;
- make review equivalent to acceptance;
- make a passing workflow equivalent to owner authorization; or
- become necessary to build, install, run, or recover a released Bowfin toolchain.

## 4. Exact identity binding

Every phase evidence set must identify at least:

| Field | Meaning |
| --- | --- |
| `source_repository` | Exact owner/repository name examined |
| `source_commit` | Exact candidate commit examined |
| `source_tree` | Exact candidate tree examined |
| `governing_contract_blob` | Exact contract content governing the examination |
| `phase` | Migration phase or precondition |
| `generator_identity` | Exact generator path and content identity or released version |
| `input_digests` | Digests of compact source inputs |
| `output_digests` | Digests of generated evidence |
| `limitations` | Bounded surfaces not examined or not provable |
| `review_status` | Proposed, reviewed, accepted, superseded, or historical |

Unknown fields may be retained, but required fields may not be inferred from filenames or conversational context.

## 5. Two-sided acceptance anchor

The binding sequence is intentionally asymmetric:

1. A source candidate is fixed at an exact commit and tree.
2. The ledger generates and commits evidence for that exact source identity.
3. An independent reviewer verifies the source identity, ledger identity, digests, coverage, and limitations.
4. Greg decides whether to accept the source candidate.
5. The source PR's acceptance record links the exact ledger commit and tree.

This avoids a circular self-hash: the source candidate need not contain the identity of evidence that could not exist until after the source candidate was fixed. GitHub comments are part of the acceptance record but not part of the source tree.

A later source change invalidates evidence bound to the earlier tree unless the evidence explicitly proves that the changed surface is outside its bounded claim.

## 6. Authority and failure behavior

Evidence can block acceptance when it is missing, stale, inconsistent, ambiguous, or outside its claimed coverage. Evidence cannot cause acceptance.

Ledger unavailability during migration blocks any gate that requires its evidence. Ledger unavailability after release must not prevent building, installing, running, inspecting, or recovering Bowfin.

Greg remains the sole merger. If that assumption changes or automated merging is introduced, migration work stops until the governing contract establishes an independently reviewed control.

## 7. Immutability and correction

Once an evidence identity is cited in an accepted source record:

- its commit and tree are immutable historical facts;
- corrections use new commits and explicitly superseding records;
- history is not force-rewritten to make an old claim appear correct; and
- original bytes and digests remain inspectable.

## 8. Relationship to M0.1

The closed first M0.1 attempt in `gregkrsak/klyxr` demonstrated that a complete materialized snapshot can be internally consistent while still being unsuitable for the product repository. Its large tables are not accepted merely by relocation.

A replacement M0.1 design must separate:

- compact, reviewed sources of truth;
- deterministic generation and validation logic;
- generated evidence worth retaining;
- transient output that can be reproduced on demand; and
- the minimal source-repository acceptance anchor.

No replacement M0.1 work is authorized by this foundation document alone.

## 9. Recognition and retirement

Before this ledger can satisfy a compiler-repository migration gate, the governing migration contract must be amended through its own reviewed and frozen process to define this repository's role, exact binding, authority limit, and lifecycle.

After migration state R8, archive this repository read-only unless a later accepted decision defines a continuing role. Archival preserves evidence; it grants no continuing authority.
