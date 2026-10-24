# Agent Instructions

This repository is the descriptive audit ledger for the staged Klyxr-to-Bowfin migration. It is not the compiler repository and it is not an authority service.

Before changing anything, read in order:

1. `README.md`
2. `docs/LEDGER-BOUNDARY.md`
3. `evidence/README.md`
4. The exact governing migration contract identified in `README.md`

## Mandatory rules

- Treat `gregkrsak/klyxr` and its accepted migration contract as authoritative for product behavior and migration acceptance.
- Do not claim that this repository authorizes source changes, merges, releases, execution, approval, replay, custody, resources, domain cutover, package publication, or repository renaming.
- Do not modify another repository or any external service without separate, explicit authorization.
- Greg is the sole merge authority. Reviewers recommend; they do not accept or merge.
- Work on a branch and open a pull request. Do not write directly to the default branch unless Greg explicitly directs it.
- Bind every evidence set to an exact source repository, commit, and tree. Record the governing contract blob when applicable.
- Preserve accepted evidence immutably. Corrections are new commits and records; never rewrite an accepted claim in place.
- Preserve an `UNACCEPTED_HISTORICAL_SNAPSHOT` payload byte-for-byte even when it was never cited by an accepted source record. Put classification, provenance, limitations, reproduction results, and corrections in a separate archival wrapper.
- Avoid circular identity claims. The source acceptance record may point to an already-created ledger commit and tree; a source candidate must not pretend to contain its own future evidence identity.
- Keep compact typed inputs, schemas, generators, and validators for current evidence independently reviewable. Current generated evidence must identify its generator and inputs and be reproducible without network access unless a bounded exception is recorded.
- Do not import a large current-evidence snapshot without a documented need, size accounting, reproducibility proof, and review.
- A separately authorized unaccepted historical snapshot instead requires verified copy integrity, origin and imported-path completeness, content identities, size accounting, an explicit non-acceptance status, and review. Successful reproduction is not required; record it honestly as `unattempted`, `succeeded`, `failed`, or `limited`.
- Treat archived scripts, instructions, validators, and workflow files as inert historical payloads. Do not execute, install, promote, or reuse them without separate authorization and review.
- Never store secrets, credentials, authority tokens, or executable approvals.
- Fail closed on unknown mapping kinds, ambiguous occurrence roles, duplicate or non-injective mappings, digest mismatch, source-identity mismatch, and missing required evidence.
- State scanner limitations plainly. Completeness claims must name their covered surface.
- This repository must never become a runtime, compiler-build, package-install, or released-tool dependency.
- Use Conventional Commit messages with a lowercase type prefix.

The repository—not conversational memory—is the durable ledger context.
