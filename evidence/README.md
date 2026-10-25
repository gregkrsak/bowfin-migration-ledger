# Current migration evidence

This directory is reserved for accepted, current migration evidence. Material in
`archive/unaccepted/**` is historical preservation and is permanently ineligible
for use here.

No M0.1 v2 production evidence exists yet. The protocol/tooling preparation PR
does not authorize production inputs, scanner execution against the compiler
repository, evidence generation, or phase acceptance.

## Required layout

A future separately authorized M0.1 package uses:

```text
evidence/m0.1/<source-commit>/
  record.json
  inputs/
    mappings.json
    classification-rules.json
    audit-policy.json
    surface-register.json
    external-surfaces.json
    applicability-decisions.json
    visual-inspection.json
    limitations.json
  observations/
    <retained-external-snapshot>
  reviews/
    <canonical-applicability-review>
  generated/
    scan-manifest.json
    index.json
    summary.json
    publication.json
    occurrences/
      0000.jsonl
      ...
  reports/
    generation.json
    independent-audit.json
    verification.json
```

The source-commit directory name and `record.json` identities must agree.
`record.json` binds the source candidate and accepted base, governing contract,
accepted tooling revision, compact inputs, external/visual observations, and
generated package. The accepted tooling identity is also supplied independently
to the verifier and cannot be selected by `record.json`. It also denies execution, approval, custody, replay,
semantic-acceptance, merge, release, cutover, and next-phase authority.

Each dependency is supplied as an authenticated Git export containing its raw
commit object, repository-root tree, explicit eligible-view prefix and tree, and
a complete root-to-view Git tree proof. The proof authenticates opaque sibling
objects without reading or making them eligible. The selected view then carries
its complete path/mode/blob/content inventory, which is reconstructed and compared
against that exact subtree of a separately supplied filesystem snapshot. A
self-hash, named path list, or unproved subtree label is not correspondence proof.
`archive/unaccepted/**` may appear only as opaque proof metadata and may never be
selected or materialized as a current dependency.

## Package rules

- Occurrence chunks are canonical, uncompressed JSONL and remain reachable in
  Git. Compression may be used only as a transport copy.
- `scan-manifest.json` authenticates every scanned source path, byte count,
  SHA-256, UTF-8 status, and structured-scan status.
- `index.json` authenticates the scan manifest and every occurrence chunk.
- `publication.json` is written last and binds the manifest, index, and summary;
  its absence makes the package incomplete.
- The independent audit records its own complete scan manifest and must agree
  with the generator's exact manifest digest before occurrence keys reconcile.
- A binary/non-UTF-8 file or malformed JSON file does not silently disappear.
  Its manifest status requires a corresponding reviewed limitation or other
  explicit surface disposition before evidence can be accepted.
- Missing, expired, limited, unavailable, or invalidated required external
  evidence fails current eligibility. `not_applicable` requires independent
  semantic review, retained review bytes, and an unexpired eligibility boundary;
  the tool cannot establish it merely from a label or blob reference.
- The required-surface register is closed-world, and applicability decisions
  exactly match the not-applicable subset.
- Every registered observation resolves to one exact retained snapshot path,
  Git blob SHA-1, and SHA-256. Every applicability decision resolves to a canonical
  review body whose semantic fields are checked against the decision and subject.
- Every generated row is checked against its exact mapping and unique matching
  rule, including retained classification meaning and expected per-rule count.
- The evidence record binds the exact independent-audit bytes; source, input,
  manifest, and occurrence-key reconciliation is repeated during evidence binding.
- The verifier reconstructs canonical greedy chunk boundaries; a fully rehashed
  alternative partition is not equivalent evidence.
- Aggregate package bytes are charged before each read, and a package that would
  cross the generated-byte limit rejects before the next file is opened.

## Decisions and authority

Review findings, owner decisions, corrections, revocations, and integration
receipts live under `decisions/`, outside the immutable package they describe.
They identify exact commits, trees, blobs, and package digests. A comment, author
name, timestamp, passing check, or newest record is never authority by itself.

Only Greg may accept a candidate or merge a pull request. Acceptance of E does
not accept C, authorize integration, or begin M1. The later integration receipt P
must prove the finite C/E/D/P correspondence required by the governing contract.

## Availability and retirement

Accepted protocol, inputs, evidence, decisions, and receipts must remain
recoverable from reachable Git history plus the documented backup path. An
expiring workflow artifact, cache, attachment, or object-store URL cannot be the
sole retained copy. Ledger unavailability blocks only gates that require ledger
evidence; it never blocks ordinary compiler build, verification, failure
recovery, or accepted production operation.

After R8, archive this repository read-only unless a later accepted decision
defines another role. Retirement does not erase or reclassify evidence.
