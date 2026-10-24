# Evidence and Archive Layout

This repository distinguishes current migration evidence from unaccepted historical preservation. Storage location never determines acceptance or authority.

## Current migration evidence

After the governing compiler contract recognizes this ledger and the relevant phase is authorized, current evidence may use:

```text
evidence/<phase>/<source-commit>/
  record.json
  inputs/
  generated/
  reports/
```

The directory name is navigational, not authoritative. `record.json` must carry the complete exact-identity binding defined in `docs/LEDGER-BOUNDARY.md`.

- `inputs/`: compact typed mappings, classifications, and bounded configuration reviewed as sources of truth for the stated evidence claim.
- `generated/`: reproducible outputs retained because independent inspection or durable audit requires them.
- `reports/`: human-readable generation, validation, and independent-review reports with their limitations.
- Transient outputs remain workflow artifacts or are regenerated when durable retention is unnecessary.

Each retained generated file must identify, or be covered by a record identifying, its inputs, generator, digest algorithm and digest, coverage, and limitations. A large file is not evidence of completeness merely because it contains many rows.

## Unaccepted historical snapshots

A separately authorized preservation import uses a distinct path such as:

```text
archive/unaccepted/<snapshot-id>/
  ARCHIVE-RECORD.json
  NOTES.md
  payload/
    <original paths and bytes>
```

The required record class and status are `unaccepted_historical_snapshot` and `UNACCEPTED_HISTORICAL_SNAPSHOT`. The wrapper must record:

- origin repository and pull request or other origin reference;
- origin commit and tree;
- complete imported path set and original path spelling;
- per-file and total byte sizes;
- digest algorithm and per-file payload content identities;
- any source revision that the payload claimed to examine, separately from its origin;
- copy-integrity and import-completeness results;
- reproduction status: `unattempted`, `succeeded`, `failed`, or `limited`;
- semantic-validation status and bounded limitations; and
- the authorizing and reviewing records for preservation.

The payload remains byte-for-byte unchanged. New explanations, corrections, and supersession records are appended outside `payload/`. An archived workflow stays beneath the payload path and does not become an active repository workflow. Archived scripts, instructions, generators, and validators are retained as historical code and are not current tooling unless separately authorized and reviewed.

Copy integrity proves that the intended historical bytes were preserved. It does not prove that an archived generator is reproducible, that its results are correct or complete, that its architecture is adopted, that M0.1 is accepted, or that later migration work is authorized. Successful reproduction is not required for preservation.

This foundation intentionally contains no imported material from the closed first M0.1 attempt. A later import requires separate authorization and review.
