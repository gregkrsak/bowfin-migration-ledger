# M0.1 v2 protocol candidate

Read [PROTOCOL.md](PROTOCOL.md) before reviewing any code.

This directory is a proposed, unaccepted protocol/tooling revision. It contains
only synthetic fixtures. It contains no production classification inputs and no
migration evidence.

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

## Future commands

The following commands describe the intended accepted interface. They are not an
authorization to execute this candidate:

```text
python3 -I generate.py \
  --source-root <read-only-snapshot> \
  --source-repository <owner/repository> \
  --source-tree <40-hex-tree> \
  --mappings <mappings.json> \
  --rules <classification-rules.json> \
  --output <empty-directory>

python3 -I audit_scan.py \
  --source-root <read-only-snapshot> \
  --source-repository <owner/repository> \
  --source-tree <40-hex-tree> \
  --policy <audit-policy.json> \
  --output <new-audit-result.json>

python3 -I verify.py package \
  --package <generated-directory> \
  --source-repository <owner/repository> \
  --source-tree <40-hex-tree> \
  --audit <audit-result.json>

python3 -I verify.py binding \
  --record <integration-binding-record.json>

python3 -I tests/test_protocol.py
```

Production inputs, evidence generation, workflow activation, and phase acceptance
remain separately gated.
