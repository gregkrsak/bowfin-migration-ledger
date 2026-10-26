# M0.1 v2 protocol and tooling

Read [PROTOCOL.md](PROTOCOL.md) before reviewing any code.

## Proposed discovery-efficiency repair

This working revision proposes a generator-only literal-dispatch repair. It is
not yet independently reviewed, executed, accepted, or eligible as tooling.
The existing accepted revision and all prior results below remain historical
facts, not validation of this changed revision.

The generator builds a first-character index once per discovery stage and scans
each path component, raw text, and decoded JSON string once for dispatch. It
compares only literals in the relevant bucket and preserves all overlapping
spellings and all namespace interpretations. Every construction, dispatch,
comparison, and yielded binding is charged. Dense adversarial prefixes still
fail closed at the unchanged `max_processing_steps: 2000000000`.

The independent auditor, verifier, shared library, schema, limits, and existing
54 test methods are unchanged. Six new authored methods cover production-length
synthetic discovery, fixed Unicode/path/JSON keys, overlapping and duplicate
spellings, partial prefixes, and exact work-budget failure sites. They have not
been run. See [the repair note](../../../docs/M01-DISCOVERY-EFFICIENCY-REPAIR.md)
for the static lower-bound proof, review boundary, and remaining limitations.

Production inputs, production execution, evidence generation, acceptance,
readiness, merge, and later phases remain separately gated. PR #5 is unchanged.

## Prior accepted revision

The accepted M0.1 v2 revision recorded in PROTOCOL.md includes the
occurrence-semantics repair merged through PR #6. This directory contains only
protocol/tooling and synthetic fixtures; it contains no accepted production
classification inputs or migration evidence. Acceptance does not accept PR #5,
accept M0.1, or authorize M1.

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

The following commands describe the accepted revision's interface. Their presence is not an
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
  --audit <audit-result.json> \
  --audit-policy <audit-policy.json>

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

Package mode requires `--audit-policy` whenever `--audit` is supplied. It checks
the retained audit against that supplied policy, but does not authenticate the
policy's provenance. Evidence mode instead takes the policy from its authenticated
compact-input export. Package-mode success is not evidence acceptance.

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
original accepted baseline remains preserved in history. The current accepted
revision is head `23bed495c73b600d0a849b3c336d08a5c6cdd1b1`, tree
`c642dca4c4b8ae4e08f1250e1862bbe821c43b04`, and protocol subtree
`d0e0c7419020415ddc7996631db616b2f73a25b3`, integrated by ordinary merge commit
`ef9574336edf2b16aae4308330d581f0bacb6e45`. Production inputs, production
execution, migration evidence, M0.1 acceptance, and M1 remain separately gated.


## Accepted occurrence-semantics repair

This accepted repair introduces a namespace-free physical `candidate_key`, requires
one semantic classification per physical candidate, and permits exact
candidate-key selectors in both classification and independent audit policy.
It exists to distinguish identical legacy spellings used as CLI names, package
names, repository identities, domains, display brands, test identities, or
historical prose without treating one spelling as one meaning.

Sarah reviewed initial head `dd81974fcd7733a38ae00f67666df5208f059190` and required
repair. This follow-up addresses BML-OS01–07: verifier cross-interpretation
competition, authenticated audit-policy populations, strict selector presence,
new-work accounting, independent fixed-vector controls, normalized collision
descriptors, and exact population semantics for classification key lists.
Sarah's focused review of the first repair head
`a9fd31476de8a652919bf1825a4553ebba22daac` resolved OS01, OS03, OS04, OS06, and
OS07, but retained OS02 because of new blocker OS08; it also recorded OS09 and
OS10. The next appended repair binds retained filename claims to their actual path
component bytes, rejects cross-component source-suffix literals, and restores the
predecessor budget control's intended target. Sarah's static confirmation of head
`2d822f1228e230505578c0e482219e3b012cac01` resolved OS08–10 and recommended
bounded synthetic execution. The single authorized run discovered all 54 tests:
53 passed and `test_independent_overlap_vectors` errored because the `crate`
fixed vector described the 14-byte literal `klyxr_compiler` with a 13-byte end
offset and corresponding false candidate key. BML-OS11 records that failed run.
This appended repair corrected only that vector and preserved the historical
failure. The repaired revision then passed all 54 authored tests in one separately
authorized bounded run. Sarah independently reconciled that report against the
unchanged test module and exact source identities; a subsequent PR-body-only
record correction did not change the accepted candidate. Greg accepted the exact
repair, and PR #6 integrated it by ordinary merge commit
`ef9574336edf2b16aae4308330d581f0bacb6e45`.

Both one-run authorizations are exhausted. Do not generate production evidence,
accept M0.1, or begin M1 from this acceptance. PR #5 remains a separate unaccepted
draft whose inputs must be reconciled against this accepted tooling revision.
