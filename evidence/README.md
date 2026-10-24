# Evidence Layout

This directory will hold accepted migration-evidence sets after the governing compiler contract recognizes the separate ledger and the relevant phase is authorized.

Proposed path form:

```text
evidence/<phase>/<source-commit>/
  record.json
  inputs/
  generated/
  reports/
```

The directory name is navigational, not authoritative. `record.json` must carry the complete exact-identity binding defined in `docs/LEDGER-BOUNDARY.md`.

## Storage classes

- `inputs/`: compact typed mappings, classifications, and bounded configuration reviewed as sources of truth.
- `generated/`: reproducible outputs retained because independent inspection or durable audit requires them.
- `reports/`: human-readable generation, validation, and independent-review reports.
- Transient outputs should remain workflow artifacts or be regenerated locally when durable retention is unnecessary.

Each retained generated file must identify or be covered by a record identifying its inputs, generator, digest, coverage, and limitations. A large file is not evidence of completeness merely because it contains many rows.

This foundation intentionally contains no migrated evidence from the closed first M0.1 attempt.
