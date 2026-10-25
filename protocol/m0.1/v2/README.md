# M0.1 v2 protocol and tooling

Read [PROTOCOL.md](PROTOCOL.md) before reviewing any code.

This directory is the accepted M0.1 v2 protocol/tooling revision. It contains only
synthetic fixtures. It contains no production classification inputs and no
migration evidence. Acceptance of this directory does not accept M0.1 or authorize
M1.

## Review sequence

1. Review `PROTOCOL.md`, `schema.json`, and `limits.json`.
2. Review the shared primitives in `protocol_lib.py`.
3. Review `generate.py` and `audit_scan.py` separately; confirm that neither
   imports the other's selection logic or inputs.
4. Review `verify.py` and the handwritten fixture expectations.
5. Confirm archive exclusion, filesystem bounds, non-authority, and the absence
   of network/package/plugin behavior.
6. Only after exact-revision independent review may Greg authorize isolated
   synthetic test execution.

## Accepted interface

The following commands describe the accepted interface. Their presence is not an
authorization to execute the tooling against production inputs or generate
migration evidence:

```text
python3 -I generate.py \
  --source-root <read-only-snapshot> \
  --source-export <authenticated-source-export.json> \
  --source-repository <owner/repository> \
  --source-commit <40-hex-commit> \
  --source-tree <40-hex-tree> \
  --source-view-prefix "" \
  --source-view-tree <same-40-hex-source-root-tree> \
  --input-root <read-only-input-snapshot> \
  --input-export <authenticated-input-export.json> \
  --input-repository <owner/repository> \
  --input-commit <40-hex-commit> \
  --input-tree <40-hex-tree> \
  --input-view-prefix <repository-relative-prefix> \
  --input-view-tree <40-hex-tree> \
  --output <new-package-path>

python3 -I audit_scan.py \
  --source-root <read-only-snapshot> \
  --source-export <authenticated-source-export.json> \
  --source-repository <owner/repository> \
  --source-commit <40-hex-commit> \
  --source-tree <40-hex-tree> \
  --source-view-prefix "" \
  --source-view-tree <same-40-hex-source-root-tree> \
  --input-root <read-only-input-snapshot> \
  --input-export <authenticated-input-export.json> \
  --input-repository <owner/repository> \
  --input-commit <40-hex-commit> \
  --input-tree <40-hex-tree> \
  --input-view-prefix <repository-relative-prefix> \
  --input-view-tree <40-hex-tree> \
  --output <new-audit-result.json>

python3 -I verify.py package \
  --package <generated-directory> \
  --source-repository <owner/repository> \
  --source-commit <40-hex-commit> \
  --source-tree <40-hex-tree> \
  --source-export-sha256 <64-hex-digest> \
  --input-export-sha256 <64-hex-digest> \
  --audit <audit-result.json>

python3 -I verify.py evidence \
  --record <migration-evidence-record.json> \
  --package <generated-directory> \
  --source-root <read-only-source-snapshot> \
  --source-export <authenticated-source-export.json> \
  --base-root <read-only-accepted-base-snapshot> \
  --base-export <authenticated-base-export.json> \
  --contract-root <read-only-contract-snapshot> \
  --contract-export <authenticated-contract-export.json> \
  --tooling-root <read-only-tooling-snapshot> \
  --tooling-export <authenticated-tooling-export.json> \
  --observation-root <read-only-observation-snapshot> \
  --observation-export <authenticated-observation-export.json> \
  --review-root <read-only-review-snapshot> \
  --review-export <authenticated-review-export.json> \
  --input-root <read-only-input-snapshot> \
  --input-export <authenticated-input-export.json> \
  --audit <independent-audit-result.json> \
  --expected-tooling-repository <owner/repository> \
  --expected-tooling-commit <40-hex-commit> \
  --expected-tooling-tree <40-hex-root-tree> \
  --expected-tooling-view-prefix <repository-relative-prefix> \
  --expected-tooling-view-tree <40-hex-view-tree> \
  --expected-tooling-export-sha256 <64-hex-digest>

python3 -I verify.py freshness \
  --external-surfaces <external-surfaces.json> \
  --surface-register <surface-register.json> \
  --applicability-decisions <applicability-decisions.json> \
  --evaluation-time <UTC-time-ending-in-Z> \
  --evaluation-point <owner_acceptance-or-pre_integration> \
  --subject-commit <40-hex-commit> \
  --subject-tree <40-hex-tree> \
  --review-root <read-only-review-snapshot> \
  --review-export <authenticated-review-export.json> \
  --review-repository <owner/repository> \
  --review-commit <40-hex-commit> \
  --review-tree <40-hex-root-tree> \
  --review-view-prefix <repository-relative-prefix-or-empty-string> \
  --review-view-tree <40-hex-view-tree> \
  [--event <observed-invalidating-event>]...

python3 -I verify.py binding \
  --record <integration-binding-record.json> \
  --recovery-bundle <bounded-git-object-bundle-directory> \
  --expected-source-repository <owner/repository> \
  --expected-source-target-branch <branch> \
  --expected-source-merge-commit <40-hex-commit> \
  --expected-ledger-repository <owner/repository> \
  --expected-ledger-target-branch <branch> \
  --expected-ledger-merge-commit <40-hex-commit> \
  --expected-recovery-ref <refs/heads/name>

python3 -I tests/test_protocol.py
```

Production inputs, evidence generation, workflow activation, and phase acceptance
remain separately gated.

Compiler-source commands reject a nonempty source view prefix or a source view
tree different from the repository-root tree. Selected views remain supported for
tooling and other non-source dependency classes.

`<new-package-path>` must not exist. The generator creates it exclusively and
writes `publication.json` last; a pre-created empty directory is not accepted.

## Accepted focused repair boundary

P12/P15/P21–P24 repairs bind intermediate compiler content, actual E index bytes,
append-only decision successors, every recovery edge's object kind, and strict
Boolean types. Binding verification now requires independently reviewed source
change paths (`--expected-source-change-path`, repeated; empty means no changes).
See PROTOCOL.md §16 for the exact conservative policy and evidence limits. The
exact revision received independent static review, separately authorized bounded
synthetic execution, focused independent confirmation, Greg's acceptance, and an
ordinary merge. Production inputs, production execution, migration evidence,
M0.1 acceptance, and M1 remain separately gated.

