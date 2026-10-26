# PR #9 budget profile: static review, authorization, and bounded synthetic result

Status: descriptive capture for independent execution-evidence confirmation.
It does not accept PR #9, authorize merge/readiness, accept M0.1, or authorize M1.
The single synthetic invocation is complete; its authorization is exhausted.

## Provenance and exact subjects

- Captured at (UTC): 2026-10-26T07:13:57Z.
- Capture method: read-only GitHub commit/tree/run/job/log inspection; exact raw
  test output reconstructed from the logged base64 chunks; trusted independent
  standard-library byte/hash/AST/set reconciliation. No repository code ran locally.
- Stated reviewer: Sarah; report supplied by Greg as an uploaded text file.
  Publisher/capture author: Miles. These are process attributions, not
  cryptographic proof of human identity.
- Reviewed/tested PR: https://github.com/gregkrsak/bowfin-migration-ledger/pull/9
- Reviewed/tested head: `62a19baf0f67474f0c25c609f9a4300aa11e74d4`.
- Reviewed/tested tree: `27a18b261d8f5325c2414ad9e18193e91b870a37`.
- Protocol subtree: `cd514c89fda2d91318c7a63b8b737118141f7b2c`.
- Unchanged ledger main/base: `edb0a11851cb1b51727c857d03c045ad1e7daa95`.
- Separate operational workflow head: `288b0f6c3a052ef32b9b61e2f41f83669ac46e75`.
- Operational workflow tree: `87af83dbe349098f6c78c1e05801f745b67aefb9`.
- Workflow URL: https://github.com/gregkrsak/bowfin-migration-ledger/actions/runs/40283940081
- Run: `40283940081`, attempt `1`; job `121443126469`, conclusion `success`.
- The workflow head is not PR #9's head. The job independently acquired and
  verified all twelve reviewed protocol files before executing their exact bytes.
- Original Sarah report UTF-8 SHA-256:
  `bf4e5c911aaa89b5a1d2cb5c23a9197d1abc848115923f8f427adf8c15885f24`.
- Sarah report publication copy:
  https://github.com/gregkrsak/bowfin-migration-ledger/pull/9#issuecomment-6409967889
- Fallback authorization publication:
  https://github.com/gregkrsak/bowfin-migration-ledger/pull/9#issuecomment-6410301583

The earlier local isolation probe failed before any candidate test invocation.
It was a setup failure, not a failing test run. There were zero local test runs.
The GitHub Actions invocation below is the sole test-module invocation.

## Reconciled result and limitations

GitHub reported one successful job. The retained bytes reconcile 54 exact
predecessor method names against AST inspection of the reviewed test module,
54 passing outcomes, no failures/errors/skips, process exit 0, and no timeout,
output-limit stop, or OOM kill. The unittest summary reports 0.277 seconds;
the external container/attachment interval was 1.328 seconds.

Runtime: 3.12.15 (main, Oct 21 2026, 01:08:07) [GCC 12.2.0]. CPython isolated mode was active and the process
ran as UID 65534. The acquired official Python image was locked to
`python@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70`; image ID `sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77`.

Reported and checked containment: no network, no credentials in the container,
read-only root/review mount, dropped capabilities, no-new-privileges, 1 GiB
cgroup memory, zero swap, one CPU, 64 PIDs, 128 MiB writable tmpfs, 300-second
test wall timeout, 240 CPU-seconds per process, 64 MiB per-file limit, 256 FDs,
4 MiB output limit, and 12-minute overall Actions job timeout. Runtime cgroup
values are in the full report retained in the raw job log below.

Raw test output: 7091 bytes, SHA-256
`52a4661fd0ee94bf0fa70ceb955ffb73385fa8f79d91f69fa5631ebaf4f5ce97`. The external job log below includes the exact JSON
report, per-file identities, complete method lists, base64 output chunk, and
completion marker. The decoded output is a convenience view of those same bytes,
not independently editable evidence.

This is externally reported synthetic execution, independently reconciled by the
preparer. It is not personally observed runner execution, an independent Sarah
execution confirmation, measured production feasibility, a production scan,
migration evidence generation, or M0.1 completion. It does not test PR #8's rewrite.
The operational PR/branch must not be merged into main as part of accepting PR #9.

## Complete chat-delivered Sarah static review

The following body is retained verbatim, including its original non-authority
and evidence-boundary statements:

# Sarah — Static review of PR #9’s budget-only alternative

**NO BLOCKING FINDINGS IDENTIFIED.** The exact candidate implements the stated three-file change: a 50-fold increase in the existing stage-local logical-work allowance, the matching limits-file digest pin, and documentation of the proposal and its trade-off.

This is **not** a scanner rewrite or a demonstrated production-scanning solution. The next gate is Greg’s separate decision about bounded synthetic validation of this exact revision, followed by independent review of that evidence before acceptance or integration.

## 1. Exact identities and state

| Item | Independently verified value |
|---|---|
| Repository / PR | `gregkrsak/bowfin-migration-ledger` — PR #9 |
| Target | `main` |
| Branch | `m01-v2-larger-work-budget` |
| Base commit | `edb0a11851cb1b51727c857d03c045ad1e7daa95` |
| Base tree | `633ab4de8c05f95a5d2672c15b40df2cd5689aff` |
| **Reviewed head** | **`62a19baf0f67474f0c25c609f9a4300aa11e74d4`** |
| **Reviewed tree** | **`27a18b261d8f5325c2414ad9e18193e91b870a37`** |
| Sole parent | `edb0a11851cb1b51727c857d03c045ad1e7daa95` |
| Commit message | `fix: increase migration tooling work budget` |

The commit objects confirm the declared trees and exactly the required sole parent. Ledger `main` remains at the base, so the candidate is **one commit ahead and zero behind**. Final PR readback remains **open, draft, and unmerged**, with the assigned head, branch, and target. No identity or scope mismatch was found.    

I refreshed and read the complete live Sarah charter at governance commit `37d4446153cd761b70ad7fc599db1df994352585`, blob **`4df5839f388b50b5689c101f20fc845fb157700c`**, and the ledger’s complete `AGENTS.md`. I also read the ledger boundary documents, relevant governing-contract requirements, complete candidate protocol document, full focused diff, and surrounding limit-loading and accounting implementation.    

## 2. Complete three-file scope

Complete root-tree and recursive protocol-tree comparisons agree with the commit diff: **three modified regular files, 37 additions, six deletions, and no mode changes**. All three retain mode `100644`.    

Paths below are relative to `protocol/m0.1/v2/`.

| File | Base blob | Candidate blob |
|---|---|---|
| `limits.json` | `46f8c03290682d275e30c27e3f353ebfd3f291b9` | `00859ebf3bf80203e3ade39af7b88e28c39ff604` |
| `protocol_lib.py` | `6fc10a6469f9944dfa57f3553661ab858a8a57a8` | `7c34cc34d6d70c6d1a08006ceb2a63ca1f501d0f` |
| `PROTOCOL.md` | `6a0a337400053c5b9bd9193f623b67d619c108ae` | `fcd376d22a01047e0923dffed948d8c66d47dfae` |

The generator, auditor, verifier, schema, complete test module, and all fixtures retain their base blob identities. The test module remains **`8c6e8a241cbc93b947ca9ee29c1efd7d91e05551`**; therefore all 54 predecessor test bodies are unchanged—not merely their names. The complete tests subtree remains `e9ea823dcb7ba67bb150cf512631657baa97b19d`.  

All root entries outside `protocol/` are identical, including the archive, decisions, evidence, and foundation-document subtrees. **No PR #8 scanner implementation is introduced by this delta.** No production inputs or generated evidence changed. I did not expand archived payloads or resume work on PR #5 or #8.  

## 3. Independent limits and digest verification

I decoded the exact base and candidate limits bytes and used reviewer-authored standard-library parsing and hashing. No repository helper was imported or called.

| Check | Independent result |
|---|---|
| Base byte count | **683** |
| Candidate byte count | **685** |
| JSON field set | Identical: **22 fields** |
| Changed field | **Only `max_processing_steps`** |
| Old value | **2,000,000,000** |
| New value | **100,000,000,000** |
| Ratio | **Exactly 50** |
| Duplicate JSON keys | None |
| Candidate numeric limits | Positive integers; no Boolean or floating-point substitution |
| File ending | Exactly one trailing LF |
| Byte-level delta | Only the decimal literal for `max_processing_steps` |

The calculation used the retrieved file bytes, not a reserialized approximation.  

The independently computed candidate SHA-256 is:

```text
dd5785a0d34019bb37782caf2c5886cb987493eacfd24be1f6d2571adf0cb512
```

Its independently recomputed Git blob is:

```text
00859ebf3bf80203e3ade39af7b88e28c39ff604
```

Both match the candidate identities. The base bytes likewise reproduce the prior SHA-256 and Git blob.

The new value is below the unchanged JSON integer ceiling, **9,007,199,254,740,991**. `load_limits()` still rejects nonpositive values, Booleans, non-integers, unexpected fields, and the wrong protocol version; strict parsing still rejects duplicate keys and out-of-range integers. The relevant accounting uses integer addition, subtraction, and comparison without introducing a float conversion or fixed-width narrowing.  

### Digest pin and function-body preservation

The complete library diff contains only the replacement of `EXPECTED_LIMITS_SHA256`. **Every function body, import, charge site, identity check, and rejection branch is unchanged.** The candidate pin equals the independently calculated digest.  

`load_limits()` still checks the exact file hash **before** parsing or returning its limits. A mismatched file still reaches `E_LIMITS_IDENTITY`. Updating the pin therefore authenticates the new profile; it does not remove authentication or permit arbitrary caller-edited limits. 

## 4. Direct consequences and resource trade-off

### Stage-local allowance, not a process-wide ceiling

`WorkBudget` initializes its own counters for each instance. Its unchanged `charge()` rejects a negative charge or a charge that would exceed the configured limit before incrementing the counter. A cumulative charge exactly equal to the limit remains permitted; a further positive charge rejects. 

The generator’s discovery and classification functions, for example, each create their own budget. Thus **100 billion is the shared configuration value for individual accounting stages, not one 100-billion-unit pool for an entire process or command**. All generator, auditor, and verifier stages using that primitive receive the increased allowance—not just the discovery stage that motivated the proposal.  

### More permitted work; unchanged semantic checks

This deliberately weakens one resource-rejection threshold: work totals between the old and new ceilings are no longer rejected **solely** for exceeding two billion logical units. It does not weaken uniqueness, classification, population, identity, freshness, archive-exclusion, or integrity predicates. Those implementation bodies and their charge sites are unchanged. 

The trade-off is real. A costly or eventually invalid workload may consume more CPU time and hold intermediate data longer before failing. The increase does not improve asymptotic behavior, establish a measured runtime ratio, or prove a physical-memory ceiling. A 50-fold logical allowance is **not** a prediction of 50-fold runtime or memory use.

Every other numerical limit is unchanged, including source/file bytes, total source bytes, rows, occurrences, chunks, paths, strings, JSON depth, mappings, rules, and audit families. Those limits continue to constrain their respective dimensions; they are not interchangeable with operating-system resource containment.

### The earlier lower bound does not establish feasibility

The documentation cites a prior raw-text lower bound of **2,371,040,422** units. The arithmetic relationship is:

```text
2,000,000,000 < 2,371,040,422 < 100,000,000,000
```

That removes the particular argument that the cited lower bound already exceeds the configured allowance. **A lower bound below a ceiling is not an upper-bound proof.** Additional matching, encoding, grouping, classification, auditing, and verification work can still exhaust a stage or encounter another rejection. 

I verified this numerical consequence, not the original production-derived lower-bound calculation. I did not reconstruct its compiler/input population, scan production inputs, or infer that a production run will succeed.

## 5. Documentation and remaining evidence gate

The protocol’s opening status and new §18 clearly identify this as an **unreviewed/unexecuted proposed budget profile**, distinguish it from the accepted occurrence-semantics revision, describe the stage-local scope and increased resource exposure, and deny execution, production, acceptance, readiness, merge, and later-phase authority.  

Section 18 expressly limits the earlier acceptance and 54-test results to the **earlier accepted profile**. Its “removes that particular numerical impossibility” statement is qualified immediately: no measured runtime, complete upper bound, or production-success guarantee is claimed. I found no material documentation contradiction in the three-file proposal. Earlier historical acceptance statements must continue to be read with that explicit qualification.

The remaining gate is **changed-profile execution evidence**, not another static source repair identified here. The unchanged tests are useful predecessor controls, but their prior successful execution does not establish a result under the new pinned limits. The ledger’s sequence still calls for independent static review, Greg’s separate authorization of isolated synthetic testing, independent assessment of its results, and separate acceptance/integration decisions. 

Any later execution authorization should retain explicit external containment and timeout conditions; the larger logical counter is not a substitute for them. That is a prospective authorization consideration, not permission to run anything now.

## 6. Findings, limitations, and disposition

**Blocking static defects:** None identified within the exact three-file scope.

**Explicit resource trade-off:** A finite but substantially larger allowance at every applicable accounting stage. This is the chosen policy change, not evidence of improved scanner efficiency.

**Evidence gaps:** This profile has no reviewed execution result or measured runtime. Production feasibility remains unproved. I did not independently recalculate the cited production lower bound or conduct an unrelated architecture audit.

The review used read-only GitHub objects, full diff/tree comparison, relevant source inspection, and independent JSON/hash/arithmetic calculations. I did not repeat the preparer’s AST checks, and I did not treat them as execution evidence.

**No repository tooling, tests, compiler code, Rust, or workflow was executed. Nothing was posted to GitHub.** The only local computation was the expressly permitted reviewer-authored data analysis. No repository content, metadata, draft state, approval, or merge was changed.

**Independent disposition: NO BLOCKING FINDINGS IDENTIFIED — ready for Greg’s separate decision about bounded synthetic validation of this exact revision.**

This is not protocol acceptance, merge permission, production-scanning authorization, permission to resume PR #5 or #8, M0.1 acceptance, or M1/later-phase authority. **Greg retains sole acceptance and merge authority.**
## Complete fallback authorization publication

The following publication records Greg's bounded chat authorization and its
operational scope. It is descriptive only, not a reusable executable approval.
Its previously future execution state is resolved by the completed result above.

## Owner-authorized one-run GitHub Actions validation — descriptive record

Greg authorized the fallback in chat: “Alright. Let's try GitHub Actions. Authorized.”

This replaces the unavailable local isolation environment for this one synthetic validation only. The local sandbox preflight failed before any repository test code ran; **zero local test invocations occurred**.

- Subject: PR #9 at `62a19baf0f67474f0c25c609f9a4300aa11e74d4`, tree `27a18b261d8f5325c2414ad9e18193e91b870a37`.
- Protocol subtree: `cd514c89fda2d91318c7a63b8b737118141f7b2c`; all twelve files are pinned by Git blob, SHA-256, and byte count.
- Static review publication: https://github.com/gregkrsak/bowfin-migration-ledger/pull/9#issuecomment-6409967889
- Separate operational branch: `pr9-budget-validation-once`.
- Orchestration commit: `288b0f6c3a052ef32b9b61e2f41f83669ac46e75`, tree `87af83dbe349098f6c78c1e05801f745b67aefb9`; sole parent is unchanged ledger main `edb0a11851cb1b51727c857d03c045ad1e7daa95`.
- Orchestration helper SHA-256: `cf4f3080b27dd30add03b40c3f5681e95aa80cdec6bc29856595de2c05b11cad`.
- Scope: one invocation of the exact 54-test synthetic module. No retry or rerun is authorized by this record.

The job has read-only contents/PR permissions. It acquires only the reviewed protocol files, checks the closed view and subject state, and locks the acquired official Python 3.12 image to its immutable Docker digest before execution. That actual image identity is recorded with the result; a mutable tag is not used for execution.

The test container has no network, no GitHub credentials, a read-only root and reviewed-file mount, UID 65534, dropped capabilities, and no-new-privileges. Bounds: 300-second test wall timeout, 240 CPU-seconds per process, 1 GiB memory with swap disabled, one CPU, 64 PIDs, 128 MiB writable tmpfs, 64 MiB per-file size, 256 file descriptors, and 4 MiB captured output. The overall Actions job timeout is 12 minutes. Unsupported containment or identity drift stops before the test module.

The job checks the complete executed method set and exit status; logs distinguish setup failure from test failure. No compiler/governance/archive code, production inputs, production scanner, or evidence-generation command is in scope. PR #9 remains unchanged and draft. This grants no acceptance, ready-state transition, merge, M0.1 completion, M1, or later authority. This text records Greg's bounded instruction; it is not a reusable executable approval.

Activation follows this publication. The actual run URL, outcome, and exhausted/unstarted invocation state will be recorded separately.

## Decoded exact container output

````text
PR9_RUNTIME_PROVENANCE={"python": "3.12.15 (main, Oct 21 2026, 01:08:07) [GCC 12.2.0]", "isolated": true, "uid": 65534, "cgroup_limits": {"memory.max": "1073741824", "memory.swap.max": "0", "pids.max": "64", "cpu.max": "100000 100000"}, "cpu_limit": [240, 240], "file_limit": [67108864, 67108864], "fd_limit": [256, 256]}
test_archive_and_dot_path_reject (__main__.ProtocolTests.test_archive_and_dot_path_reject) ... ok
test_auditor_high_work_no_match_stops_at_budget (__main__.ProtocolTests.test_auditor_high_work_no_match_stops_at_budget) ... ok
test_authenticated_cedp_ancestry_trees_targets_and_recovery (__main__.ProtocolTests.test_authenticated_cedp_ancestry_trees_targets_and_recovery) ... ok
test_authenticated_export_rejects_stale_bytes_mode_and_extra_path (__main__.ProtocolTests.test_authenticated_export_rejects_stale_bytes_mode_and_extra_path) ... ok
test_authenticated_export_rejects_wrong_tree (__main__.ProtocolTests.test_authenticated_export_rejects_wrong_tree) ... ok
test_authenticated_subtree_view_keeps_archive_opaque_and_ineligible (__main__.ProtocolTests.test_authenticated_subtree_view_keeps_archive_opaque_and_ineligible) ... ok
test_candidate_key_separates_physical_discovery_from_semantics (__main__.ProtocolTests.test_candidate_key_separates_physical_discovery_from_semantics) ... ok
test_competing_package_creator_is_never_deleted (__main__.ProtocolTests.test_competing_package_creator_is_never_deleted) ... ok
test_compiler_intermediate_content_and_decision_preservation (__main__.ProtocolTests.test_compiler_intermediate_content_and_decision_preservation) ... ok
test_compiler_source_view_must_be_repository_root (__main__.ProtocolTests.test_compiler_source_view_must_be_repository_root) ... ok
test_cumulative_package_budget_rejects_before_next_read (__main__.ProtocolTests.test_cumulative_package_budget_rejects_before_next_read) ... ok
test_direct_compact_input_field_validation (__main__.ProtocolTests.test_direct_compact_input_field_validation) ... ok
test_duplicate_json_key (__main__.ProtocolTests.test_duplicate_json_key) ... ok
test_equal_count_different_key (__main__.ProtocolTests.test_equal_count_different_key) ... ok
test_evidence_record_binds_actual_exports_and_generated_bytes (__main__.ProtocolTests.test_evidence_record_binds_actual_exports_and_generated_bytes) ... ok
test_exact_candidate_keys_split_roles_within_one_file (__main__.ProtocolTests.test_exact_candidate_keys_split_roles_within_one_file) ... ok
test_exact_classification_population_and_collision_descriptor (__main__.ProtocolTests.test_exact_classification_population_and_collision_descriptor) ... ok
test_export_eligibility_separates_fixture_and_production (__main__.ProtocolTests.test_export_eligibility_separates_fixture_and_production) ... ok
test_fifo_is_rejected_before_blocking_open (__main__.ProtocolTests.test_fifo_is_rejected_before_blocking_open) ... ok
test_forged_physical_keys (__main__.ProtocolTests.test_forged_physical_keys) ... ok
test_freshness_expiry_and_invalidation (__main__.ProtocolTests.test_freshness_expiry_and_invalidation) ... ok
test_generated_rows_are_bound_to_compact_meaning (__main__.ProtocolTests.test_generated_rows_are_bound_to_compact_meaning) ... ok
test_incremental_processing_limit (__main__.ProtocolTests.test_incremental_processing_limit) ... ok
test_independent_auditor_reconciles_exact_keys (__main__.ProtocolTests.test_independent_auditor_reconciles_exact_keys) ... ok
test_independent_overlap_vectors (__main__.ProtocolTests.test_independent_overlap_vectors) ... ok
test_interrupted_document_write_removes_only_owned_partial (__main__.ProtocolTests.test_interrupted_document_write_removes_only_owned_partial) ... ok
test_interrupted_package_never_publishes_completion_marker (__main__.ProtocolTests.test_interrupted_package_never_publishes_completion_marker) ... ok
test_intrinsic_locators_distinguish_multiple_identities (__main__.ProtocolTests.test_intrinsic_locators_distinguish_multiple_identities) ... ok
test_key_construction_exhaustion_and_group_budget_sites (__main__.ProtocolTests.test_key_construction_exhaustion_and_group_budget_sites) ... ok
test_literal_precomputed_vectors (__main__.ProtocolTests.test_literal_precomputed_vectors) ... ok
test_manifest_binary_and_malformed_require_disposition (__main__.ProtocolTests.test_manifest_binary_and_malformed_require_disposition) ... ok
test_missing_extra_and_tampered_chunks (__main__.ProtocolTests.test_missing_extra_and_tampered_chunks) ... ok
test_missing_publication_marker_rejects_partial_package (__main__.ProtocolTests.test_missing_publication_marker_rejects_partial_package) ... ok
test_missing_surface_and_unsupported_not_applicable (__main__.ProtocolTests.test_missing_surface_and_unsupported_not_applicable) ... ok
test_mutation_manifest_maps_to_real_tests (__main__.ProtocolTests.test_mutation_manifest_maps_to_real_tests) ... ok
test_new_work_accounting_boundaries (__main__.ProtocolTests.test_new_work_accounting_boundaries) ... ok
test_non_injective_mapping_including_retain (__main__.ProtocolTests.test_non_injective_mapping_including_retain) ... ok
test_non_nfc_string (__main__.ProtocolTests.test_non_nfc_string) ... ok
test_not_applicable_requires_current_semantic_review (__main__.ProtocolTests.test_not_applicable_requires_current_semantic_review) ... ok
test_opaque_symlink_inventory_not_bound_record (__main__.ProtocolTests.test_opaque_symlink_inventory_not_bound_record) ... ok
test_output_symlink_and_ancestor_symlink (__main__.ProtocolTests.test_output_symlink_and_ancestor_symlink) ... ok
test_physical_vectors_and_all_raw_kinds (__main__.ProtocolTests.test_physical_vectors_and_all_raw_kinds) ... ok
test_protocol_error_identity_is_shared (__main__.ProtocolTests.test_protocol_error_identity_is_shared) ... ok
test_recovery_wrong_kind_after_prior_visit (__main__.ProtocolTests.test_recovery_wrong_kind_after_prior_visit) ... ok
test_rehashed_noncanonical_chunk_repartition (__main__.ProtocolTests.test_rehashed_noncanonical_chunk_repartition) ... ok
test_retained_audit_policy_population (__main__.ProtocolTests.test_retained_audit_policy_population) ... ok
test_retained_cross_interpretation_rejection (__main__.ProtocolTests.test_retained_cross_interpretation_rejection) ... ok
test_retained_duplicate_audit_meanings (__main__.ProtocolTests.test_retained_duplicate_audit_meanings) ... ok
test_retained_path_component_claim_truth (__main__.ProtocolTests.test_retained_path_component_claim_truth) ... ok
test_selector_presence_and_malformed_key_lists (__main__.ProtocolTests.test_selector_presence_and_malformed_key_lists) ... ok
test_source_suffix_literal_is_one_component (__main__.ProtocolTests.test_source_suffix_literal_is_one_component) ... ok
test_stale_rule_count (__main__.ProtocolTests.test_stale_rule_count) ... ok
test_unknown_unit_kind (__main__.ProtocolTests.test_unknown_unit_kind) ... ok
test_valid_authenticated_generation_and_reconciliation (__main__.ProtocolTests.test_valid_authenticated_generation_and_reconciliation) ... ok

----------------------------------------------------------------------
Ran 54 tests in 0.277s

OK
````

## Complete retrieved GitHub job log

````text
﻿2026-10-26T07:08:21.1105180Z Current runner version: '2.338.0'
2026-10-26T07:08:21.1131841Z ##[group]Runner Image Provisioner
2026-10-26T07:08:21.1132871Z Hosted Compute Agent
2026-10-26T07:08:21.1133628Z Version: 20261021.618
2026-10-26T07:08:21.1134372Z Commit: 21505ad2541d5be6135ed84fc33697146cf75b8e
2026-10-26T07:08:21.1135342Z Build Date: 2026-10-21T00:45:21Z
2026-10-26T07:08:21.1136187Z Worker ID: {9e299bd9-b784-4101-8530-0c19fc53598e}
2026-10-26T07:08:21.1137049Z Region: centralus
2026-10-26T07:08:21.1137819Z Cloud: Azure
2026-10-26T07:08:21.1138491Z ##[endgroup]
2026-10-26T07:08:21.1140198Z ##[group]Operating System
2026-10-26T07:08:21.1141177Z Ubuntu
2026-10-26T07:08:21.1141785Z 24.04.5
2026-10-26T07:08:21.1142479Z LTS
2026-10-26T07:08:21.1143072Z ##[endgroup]
2026-10-26T07:08:21.1143682Z ##[group]Runner Image
2026-10-26T07:08:21.1144458Z Image: ubuntu-24.04
2026-10-26T07:08:21.1145111Z Version: 20261012.334.1
2026-10-26T07:08:21.1146640Z Included Software: https://github.com/actions/runner-images/blob/ubuntu24/20261012.334/images/ubuntu/Ubuntu2404-Readme.md
2026-10-26T07:08:21.1148523Z Image Release: https://github.com/actions/runner-images/releases/tag/ubuntu24%2F20261012.334
2026-10-26T07:08:21.1149920Z ##[endgroup]
2026-10-26T07:08:21.1151321Z ##[group]GITHUB_TOKEN Permissions
2026-10-26T07:08:21.1153589Z Contents: read
2026-10-26T07:08:21.1154347Z Metadata: read
2026-10-26T07:08:21.1155052Z PullRequests: read
2026-10-26T07:08:21.1155782Z ##[endgroup]
2026-10-26T07:08:21.1158399Z Secret source: Actions
2026-10-26T07:08:21.1159833Z Cache mode: write
2026-10-26T07:08:21.1160965Z Prepare workflow directory
2026-10-26T07:08:21.1856866Z Prepare all required actions
2026-10-26T07:08:21.1969535Z Complete job name: validate
2026-10-26T07:08:21.3820738Z ##[group]Run python3 -I -B - <<'PY'
2026-10-26T07:08:21.3821395Z [36;1mpython3 -I -B - <<'PY'[0m
2026-10-26T07:08:21.3822166Z [36;1mimport hashlib, os, pathlib, re, sys, urllib.request[0m
2026-10-26T07:08:21.3822880Z [36;1msha = os.environ['GITHUB_SHA'][0m
2026-10-26T07:08:21.3823572Z [36;1massert re.fullmatch('[0-9a-f]{40}', sha)[0m
2026-10-26T07:08:21.3824606Z [36;1murl = 'https://raw.githubusercontent.com/gregkrsak/bowfin-migration-ledger/' + sha + '/.github/scripts/pr9-validate-once.py'[0m
2026-10-26T07:08:21.3825668Z [36;1mwith urllib.request.urlopen(url, timeout=20) as response:[0m
2026-10-26T07:08:21.3826397Z [36;1m    data = response.read(65537)[0m
2026-10-26T07:08:21.3826947Z [36;1massert len(data) <= 65536[0m
2026-10-26T07:08:21.3827888Z [36;1massert hashlib.sha256(data).hexdigest() == 'cf4f3080b27dd30add03b40c3f5681e95aa80cdec6bc29856595de2c05b11cad'[0m
2026-10-26T07:08:21.3829378Z [36;1mtarget = pathlib.Path(os.environ['RUNNER_TEMP']) / 'pr9-validate-once.py'[0m
2026-10-26T07:08:21.3830217Z [36;1mwith target.open('xb') as output:[0m
2026-10-26T07:08:21.3830805Z [36;1m    output.write(data)[0m
2026-10-26T07:08:21.3831503Z [36;1mos.execv(sys.executable, [sys.executable, '-I', '-B', str(target)])[0m
2026-10-26T07:08:21.3832244Z [36;1mPY[0m
2026-10-26T07:08:21.4932404Z shell: /usr/bin/bash --noprofile --norc -e -o pipefail {0}
2026-10-26T07:08:21.4933345Z env:
2026-10-26T07:08:21.4936730Z   GH_READ_TOKEN: ***
2026-10-26T07:08:21.4937238Z ##[endgroup]
2026-10-26T07:08:35.5414001Z PR9_REPORT_JSON={"bounds":{"cpu_seconds_per_process":240,"cpus":1,"file_bytes":67108864,"log_bytes":4194304,"memory_bytes":1073741824,"network":"none","open_files":256,"pids":64,"root_read_only":true,"swap_disabled":true,"test_wall_seconds":300,"tmpfs_bytes":134217728},"container_host_config":{"AutoRemove":false,"Binds":null,"BlkioDeviceReadBps":[],"BlkioDeviceReadIOps":[],"BlkioDeviceWriteBps":[],"BlkioDeviceWriteIOps":[],"BlkioWeight":0,"BlkioWeightDevice":[],"CapAdd":null,"CapDrop":["ALL"],"Cgroup":"","CgroupParent":"","CgroupnsMode":"private","ConsoleSize":[0,0],"ContainerIDFile":"","CpuCount":0,"CpuPercent":0,"CpuPeriod":0,"CpuQuota":0,"CpuRealtimePeriod":0,"CpuRealtimeRuntime":0,"CpuShares":0,"CpusetCpus":"","CpusetMems":"","DeviceCgroupRules":null,"DeviceRequests":null,"Devices":[],"Dns":[],"DnsOptions":[],"DnsSearch":[],"ExtraHosts":null,"GroupAdd":null,"IOMaximumBandwidth":0,"IOMaximumIOps":0,"IpcMode":"private","Isolation":"","Links":null,"LogConfig":{"Config":{},"Type":"json-file"},"MaskedPaths":["/proc/asound","/proc/acpi","/proc/interrupts","/proc/kcore","/proc/keys","/proc/latency_stats","/proc/timer_list","/proc/timer_stats","/proc/sched_debug","/proc/scsi","/sys/firmware","/sys/devices/virtual/powercap"],"Memory":1073741824,"MemoryReservation":0,"MemorySwap":1073741824,"MemorySwappiness":null,"Mounts":[{"ReadOnly":true,"Source":"/home/runner/work/_temp/pr9-reviewed-nya6yesu","Target":"/review","Type":"bind"}],"NanoCpus":1000000000,"NetworkMode":"none","OomKillDisable":false,"OomScoreAdj":0,"PidMode":"","PidsLimit":64,"PortBindings":{},"Privileged":false,"PublishAllPorts":false,"ReadonlyPaths":["/proc/bus","/proc/fs","/proc/irq","/proc/sys","/proc/sysrq-trigger"],"ReadonlyRootfs":true,"RestartPolicy":{"MaximumRetryCount":0,"Name":"no"},"Runtime":"runc","SecurityOpt":["no-new-privileges=true"],"ShmSize":67108864,"Tmpfs":{"/tmp":"rw,noexec,nosuid,nodev,size=134217728,mode=1777"},"UTSMode":"","Ulimits":[{"Hard":240,"Name":"cpu","Soft":240},{"Hard":67108864,"Name":"fsize","Soft":67108864},{"Hard":256,"Name":"nofile","Soft":256}],"UsernsMode":"","VolumeDriver":"","VolumesFrom":null},"container_state":{"Dead":false,"Error":"","ExitCode":0,"FinishedAt":"2026-10-26T07:08:34.731934355Z","OOMKilled":false,"Paused":false,"Pid":0,"Restarting":false,"Running":false,"StartedAt":"2026-10-26T07:08:33.790016806Z","Status":"exited"},"containment_stop":null,"docker_attach_exit":0,"docker_version":{"Client":{"ApiVersion":"1.48","Arch":"amd64","BuildTime":"Tue Mar 25 15:07:16 2025","Context":"default","DefaultAPIVersion":"1.48","GitCommit":"b8034c0","GoVersion":"go1.23.7","Os":"linux","Platform":{"Name":"Docker Engine - Community"},"Version":"28.0.4"},"Server":{"ApiVersion":"1.48","Arch":"amd64","BuildTime":"2025-03-25T15:07:16.000000000+00:00","Components":[{"Details":{"ApiVersion":"1.48","Arch":"amd64","BuildTime":"Tue Mar 25 15:07:16 2025","Experimental":"false","GitCommit":"6430e49","GoVersion":"go1.23.7","KernelVersion":"6.17.0-1022-azure","MinAPIVersion":"1.24","Os":"linux"},"Name":"Engine","Version":"28.0.4"},{"Details":{"GitCommit":"f2551031d7276a770f65f98c9b52e57e7dad07e8"},"Name":"containerd","Version":"v2.4.1"},{"Details":{"GitCommit":"v1.5.2-0-g29dd3dc2"},"Name":"runc","Version":"1.5.2"},{"Details":{"GitCommit":"de40ad0"},"Name":"docker-init","Version":"0.19.0"}],"GitCommit":"6430e49","GoVersion":"go1.23.7","KernelVersion":"6.17.0-1022-azure","MinAPIVersion":"1.24","Os":"linux","Platform":{"Name":"Docker Engine - Community"},"Version":"28.0.4"}},"duration_seconds":1.328,"expected_methods":["test_archive_and_dot_path_reject","test_auditor_high_work_no_match_stops_at_budget","test_authenticated_cedp_ancestry_trees_targets_and_recovery","test_authenticated_export_rejects_stale_bytes_mode_and_extra_path","test_authenticated_export_rejects_wrong_tree","test_authenticated_subtree_view_keeps_archive_opaque_and_ineligible","test_candidate_key_separates_physical_discovery_from_semantics","test_competing_package_creator_is_never_deleted","test_compiler_intermediate_content_and_decision_preservation","test_compiler_source_view_must_be_repository_root","test_cumulative_package_budget_rejects_before_next_read","test_direct_compact_input_field_validation","test_duplicate_json_key","test_equal_count_different_key","test_evidence_record_binds_actual_exports_and_generated_bytes","test_exact_candidate_keys_split_roles_within_one_file","test_exact_classification_population_and_collision_descriptor","test_export_eligibility_separates_fixture_and_production","test_fifo_is_rejected_before_blocking_open","test_forged_physical_keys","test_freshness_expiry_and_invalidation","test_generated_rows_are_bound_to_compact_meaning","test_incremental_processing_limit","test_independent_auditor_reconciles_exact_keys","test_independent_overlap_vectors","test_interrupted_document_write_removes_only_owned_partial","test_interrupted_package_never_publishes_completion_marker","test_intrinsic_locators_distinguish_multiple_identities","test_key_construction_exhaustion_and_group_budget_sites","test_literal_precomputed_vectors","test_manifest_binary_and_malformed_require_disposition","test_missing_extra_and_tampered_chunks","test_missing_publication_marker_rejects_partial_package","test_missing_surface_and_unsupported_not_applicable","test_mutation_manifest_maps_to_real_tests","test_new_work_accounting_boundaries","test_non_injective_mapping_including_retain","test_non_nfc_string","test_not_applicable_requires_current_semantic_review","test_opaque_symlink_inventory_not_bound_record","test_output_symlink_and_ancestor_symlink","test_physical_vectors_and_all_raw_kinds","test_protocol_error_identity_is_shared","test_recovery_wrong_kind_after_prior_visit","test_rehashed_noncanonical_chunk_repartition","test_retained_audit_policy_population","test_retained_cross_interpretation_rejection","test_retained_duplicate_audit_meanings","test_retained_path_component_claim_truth","test_selector_presence_and_malformed_key_lists","test_source_suffix_literal_is_one_component","test_stale_rule_count","test_unknown_unit_kind","test_valid_authenticated_generation_and_reconciliation"],"finished_at":"2026-10-26T07:08:35.535846+00:00","image":{"architecture":"amd64","image_id":"sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77","os":"linux","reference":"python@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70"},"observed_methods":["test_archive_and_dot_path_reject","test_auditor_high_work_no_match_stops_at_budget","test_authenticated_cedp_ancestry_trees_targets_and_recovery","test_authenticated_export_rejects_stale_bytes_mode_and_extra_path","test_authenticated_export_rejects_wrong_tree","test_authenticated_subtree_view_keeps_archive_opaque_and_ineligible","test_candidate_key_separates_physical_discovery_from_semantics","test_competing_package_creator_is_never_deleted","test_compiler_intermediate_content_and_decision_preservation","test_compiler_source_view_must_be_repository_root","test_cumulative_package_budget_rejects_before_next_read","test_direct_compact_input_field_validation","test_duplicate_json_key","test_equal_count_different_key","test_evidence_record_binds_actual_exports_and_generated_bytes","test_exact_candidate_keys_split_roles_within_one_file","test_exact_classification_population_and_collision_descriptor","test_export_eligibility_separates_fixture_and_production","test_fifo_is_rejected_before_blocking_open","test_forged_physical_keys","test_freshness_expiry_and_invalidation","test_generated_rows_are_bound_to_compact_meaning","test_incremental_processing_limit","test_independent_auditor_reconciles_exact_keys","test_independent_overlap_vectors","test_interrupted_document_write_removes_only_owned_partial","test_interrupted_package_never_publishes_completion_marker","test_intrinsic_locators_distinguish_multiple_identities","test_key_construction_exhaustion_and_group_budget_sites","test_literal_precomputed_vectors","test_manifest_binary_and_malformed_require_disposition","test_missing_extra_and_tampered_chunks","test_missing_publication_marker_rejects_partial_package","test_missing_surface_and_unsupported_not_applicable","test_mutation_manifest_maps_to_real_tests","test_new_work_accounting_boundaries","test_non_injective_mapping_including_retain","test_non_nfc_string","test_not_applicable_requires_current_semantic_review","test_opaque_symlink_inventory_not_bound_record","test_output_symlink_and_ancestor_symlink","test_physical_vectors_and_all_raw_kinds","test_protocol_error_identity_is_shared","test_recovery_wrong_kind_after_prior_visit","test_rehashed_noncanonical_chunk_repartition","test_retained_audit_policy_population","test_retained_cross_interpretation_rejection","test_retained_duplicate_audit_meanings","test_retained_path_component_claim_truth","test_selector_presence_and_malformed_key_lists","test_source_suffix_literal_is_one_component","test_stale_rule_count","test_unknown_unit_kind","test_valid_authenticated_generation_and_reconciliation"],"output_bytes":7091,"output_sha256":"52a4661fd0ee94bf0fa70ceb955ffb73385fa8f79d91f69fa5631ebaf4f5ce97","protocol_subtree":"cd514c89fda2d91318c7a63b8b737118141f7b2c","record_class":"bounded_synthetic_execution_report","repository":"gregkrsak/bowfin-migration-ledger","reviewed_files":{"PROTOCOL.md":{"blob_sha1":"fcd376d22a01047e0923dffed948d8c66d47dfae","bytes":36501,"mode":"100644","sha256":"facac8437e1fb41f517966eff413d2fdd2e37f8c249a594bb946e491fa16f055"},"README.md":{"blob_sha1":"e5d2356f377db7148b84b9953ae0ec5ee621a99e","bytes":9421,"mode":"100644","sha256":"e8a25ddb3ca2b0d32e2cffb172ba248ace99926a7bf7dd3967a9a9c7b9fdfe9c"},"audit_scan.py":{"blob_sha1":"d8ac2f74adaceedc638e78dafb488dfbbcb359a7","bytes":16388,"mode":"100644","sha256":"91cb6887583d48aa7f12ebc709ffbe8c6c59ce538246c6b38401d7c997d4bbaf"},"generate.py":{"blob_sha1":"7d103aa4d61c42d089e991e25b6c3763cae08ffe","bytes":24802,"mode":"100644","sha256":"d81bb830cb2753b139feb91ecf6658a22cf084e1766cd52ad2798ec68dec54f3"},"limits.json":{"blob_sha1":"00859ebf3bf80203e3ade39af7b88e28c39ff604","bytes":685,"mode":"100644","sha256":"dd5785a0d34019bb37782caf2c5886cb987493eacfd24be1f6d2571adf0cb512"},"protocol_lib.py":{"blob_sha1":"7c34cc34d6d70c6d1a08006ceb2a63ca1f501d0f","bytes":44701,"mode":"100644","sha256":"0d48a22571cde789a36bcb77dd65846d756de4a1af7dc4549ca8d402621a2568"},"schema.json":{"blob_sha1":"56f81ff76b38c1a870fdb49abc5e378f1c003370","bytes":27406,"mode":"100644","sha256":"257eb8d1427529d33fe1dcfe2b4867916d516af1fe6123109a1e4ba7900e344f"},"tests/fixtures/mutations.json":{"blob_sha1":"4aa64b28f9bcd472f4582f68e3b9c131fee0ac68","bytes":12940,"mode":"100644","sha256":"73918827468c654702cde5860557ade2f8dd2d4fa1580681ab9ef2b21da7d3d2"},"tests/fixtures/valid-case.json":{"blob_sha1":"a1cc67fbf970f745c5e2473d6dec9019bf7858b4","bytes":4974,"mode":"100644","sha256":"71038e6b0a49cfb3f6c5d903c0d38819683c1d88b2dcc7b4e7f3364b016a386e"},"tests/fixtures/vectors.json":{"blob_sha1":"b4113e7d35134f99507e685e72d0ab6478e5f751","bytes":4531,"mode":"100644","sha256":"4ed3ec81aa8e7130bfcc1686952eebd9b3151387bd3e4156f1c9a09c3dafb06d"},"tests/test_protocol.py":{"blob_sha1":"8c6e8a241cbc93b947ca9ee29c1efd7d91e05551","bytes":103835,"mode":"100644","sha256":"66809cd27594973cd68eb174d1851bd3c22b1b01499eb222eca6a42293f1f917"},"verify.py":{"blob_sha1":"e8492b02a262773c697f0c32f5fc22090ad84ec9","bytes":113952,"mode":"100644","sha256":"eb4936bfac9b30332919cd6293428c28cf1ff4cb0bddc72b4194f5aed3c9343f"}},"run_attempt":"1","run_id":"40283940081","runtime":{"cgroup_limits":{"cpu.max":"100000 100000","memory.max":"1073741824","memory.swap.max":"0","pids.max":"64"},"cpu_limit":[240,240],"fd_limit":[256,256],"file_limit":[67108864,67108864],"isolated":true,"python":"3.12.15 (main, Oct 21 2026, 01:08:07) [GCC 12.2.0]","uid":65534},"started_at":"2026-10-26T07:08:21.747755+00:00","status":"passed","subject_head":"62a19baf0f67474f0c25c609f9a4300aa11e74d4","subject_tree":"27a18b261d8f5325c2414ad9e18193e91b870a37","test_invocations_attempted":1,"workflow_head":"288b0f6c3a052ef32b9b61e2f41f83669ac46e75"}
2026-10-26T07:08:35.5979257Z PR9_LOG_CHUNK=0:UFI5X1JVTlRJTUVfUFJPVkVOQU5DRT17InB5dGhvbiI6ICIzLjEyLjE1IChtYWluLCBPY3QgMjEgMjAyNiwgMDE6MDg6MDcpIFtHQ0MgMTIuMi4wXSIsICJpc29sYXRlZCI6IHRydWUsICJ1aWQiOiA2NTUzNCwgImNncm91cF9saW1pdHMiOiB7Im1lbW9yeS5tYXgiOiAiMTA3Mzc0MTgyNCIsICJtZW1vcnkuc3dhcC5tYXgiOiAiMCIsICJwaWRzLm1heCI6ICI2NCIsICJjcHUubWF4IjogIjEwMDAwMCAxMDAwMDAifSwgImNwdV9saW1pdCI6IFsyNDAsIDI0MF0sICJmaWxlX2xpbWl0IjogWzY3MTA4ODY0LCA2NzEwODg2NF0sICJmZF9saW1pdCI6IFsyNTYsIDI1Nl19CnRlc3RfYXJjaGl2ZV9hbmRfZG90X3BhdGhfcmVqZWN0IChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfYXJjaGl2ZV9hbmRfZG90X3BhdGhfcmVqZWN0KSAuLi4gb2sKdGVzdF9hdWRpdG9yX2hpZ2hfd29ya19ub19tYXRjaF9zdG9wc19hdF9idWRnZXQgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9hdWRpdG9yX2hpZ2hfd29ya19ub19tYXRjaF9zdG9wc19hdF9idWRnZXQpIC4uLiBvawp0ZXN0X2F1dGhlbnRpY2F0ZWRfY2VkcF9hbmNlc3RyeV90cmVlc190YXJnZXRzX2FuZF9yZWNvdmVyeSAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X2F1dGhlbnRpY2F0ZWRfY2VkcF9hbmNlc3RyeV90cmVlc190YXJnZXRzX2FuZF9yZWNvdmVyeSkgLi4uIG9rCnRlc3RfYXV0aGVudGljYXRlZF9leHBvcnRfcmVqZWN0c19zdGFsZV9ieXRlc19tb2RlX2FuZF9leHRyYV9wYXRoIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfYXV0aGVudGljYXRlZF9leHBvcnRfcmVqZWN0c19zdGFsZV9ieXRlc19tb2RlX2FuZF9leHRyYV9wYXRoKSAuLi4gb2sKdGVzdF9hdXRoZW50aWNhdGVkX2V4cG9ydF9yZWplY3RzX3dyb25nX3RyZWUgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9hdXRoZW50aWNhdGVkX2V4cG9ydF9yZWplY3RzX3dyb25nX3RyZWUpIC4uLiBvawp0ZXN0X2F1dGhlbnRpY2F0ZWRfc3VidHJlZV92aWV3X2tlZXBzX2FyY2hpdmVfb3BhcXVlX2FuZF9pbmVsaWdpYmxlIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfYXV0aGVudGljYXRlZF9zdWJ0cmVlX3ZpZXdfa2VlcHNfYXJjaGl2ZV9vcGFxdWVfYW5kX2luZWxpZ2libGUpIC4uLiBvawp0ZXN0X2NhbmRpZGF0ZV9rZXlfc2VwYXJhdGVzX3BoeXNpY2FsX2Rpc2NvdmVyeV9mcm9tX3NlbWFudGljcyAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X2NhbmRpZGF0ZV9rZXlfc2VwYXJhdGVzX3BoeXNpY2FsX2Rpc2NvdmVyeV9mcm9tX3NlbWFudGljcykgLi4uIG9rCnRlc3RfY29tcGV0aW5nX3BhY2thZ2VfY3JlYXRvcl9pc19uZXZlcl9kZWxldGVkIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfY29tcGV0aW5nX3BhY2thZ2VfY3JlYXRvcl9pc19uZXZlcl9kZWxldGVkKSAuLi4gb2sKdGVzdF9jb21waWxlcl9pbnRlcm1lZGlhdGVfY29udGVudF9hbmRfZGVjaXNpb25fcHJlc2VydmF0aW9uIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfY29tcGlsZXJfaW50ZXJtZWRpYXRlX2NvbnRlbnRfYW5kX2RlY2lzaW9uX3ByZXNlcnZhdGlvbikgLi4uIG9rCnRlc3RfY29tcGlsZXJfc291cmNlX3ZpZXdfbXVzdF9iZV9yZXBvc2l0b3J5X3Jvb3QgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9jb21waWxlcl9zb3VyY2Vfdmlld19tdXN0X2JlX3JlcG9zaXRvcnlfcm9vdCkgLi4uIG9rCnRlc3RfY3VtdWxhdGl2ZV9wYWNrYWdlX2J1ZGdldF9yZWplY3RzX2JlZm9yZV9uZXh0X3JlYWQgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9jdW11bGF0aXZlX3BhY2thZ2VfYnVkZ2V0X3JlamVjdHNfYmVmb3JlX25leHRfcmVhZCkgLi4uIG9rCnRlc3RfZGlyZWN0X2NvbXBhY3RfaW5wdXRfZmllbGRfdmFsaWRhdGlvbiAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X2RpcmVjdF9jb21wYWN0X2lucHV0X2ZpZWxkX3ZhbGlkYXRpb24pIC4uLiBvawp0ZXN0X2R1cGxpY2F0ZV9qc29uX2tleSAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X2R1cGxpY2F0ZV9qc29uX2tleSkgLi4uIG9rCnRlc3RfZXF1YWxfY291bnRfZGlmZmVyZW50X2tleSAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X2VxdWFsX2NvdW50X2RpZmZlcmVudF9rZXkpIC4uLiBvawp0ZXN0X2V2aWRlbmNlX3JlY29yZF9iaW5kc19hY3R1YWxfZXhwb3J0c19hbmRfZ2VuZXJhdGVkX2J5dGVzIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfZXZpZGVuY2VfcmVjb3JkX2JpbmRzX2FjdHVhbF9leHBvcnRzX2FuZF9nZW5lcmF0ZWRfYnl0ZXMpIC4uLiBvawp0ZXN0X2V4YWN0X2NhbmRpZGF0ZV9rZXlzX3NwbGl0X3JvbGVzX3dpdGhpbl9vbmVfZmlsZSAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X2V4YWN0X2NhbmRpZGF0ZV9rZXlzX3NwbGl0X3JvbGVzX3dpdGhpbl9vbmVfZmlsZSkgLi4uIG9rCnRlc3RfZXhhY3RfY2xhc3NpZmljYXRpb25fcG9wdWxhdGlvbl9hbmRfY29sbGlzaW9uX2Rlc2NyaXB0b3IgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9leGFjdF9jbGFzc2lmaWNhdGlvbl9wb3B1bGF0aW9uX2FuZF9jb2xsaXNpb25fZGVzY3JpcHRvcikgLi4uIG9rCnRlc3RfZXhwb3J0X2VsaWdpYmlsaXR5X3NlcGFyYXRlc19maXh0dXJlX2FuZF9wcm9kdWN0aW9uIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfZXhwb3J0X2VsaWdpYmlsaXR5X3NlcGFyYXRlc19maXh0dXJlX2FuZF9wcm9kdWN0aW9uKSAuLi4gb2sKdGVzdF9maWZvX2lzX3JlamVjdGVkX2JlZm9yZV9ibG9ja2luZ19vcGVuIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfZmlmb19pc19yZWplY3RlZF9iZWZvcmVfYmxvY2tpbmdfb3BlbikgLi4uIG9rCnRlc3RfZm9yZ2VkX3BoeXNpY2FsX2tleXMgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9mb3JnZWRfcGh5c2ljYWxfa2V5cykgLi4uIG9rCnRlc3RfZnJlc2huZXNzX2V4cGlyeV9hbmRfaW52YWxpZGF0aW9uIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfZnJlc2huZXNzX2V4cGlyeV9hbmRfaW52YWxpZGF0aW9uKSAuLi4gb2sKdGVzdF9nZW5lcmF0ZWRfcm93c19hcmVfYm91bmRfdG9fY29tcGFjdF9tZWFuaW5nIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfZ2VuZXJhdGVkX3Jvd3NfYXJlX2JvdW5kX3RvX2NvbXBhY3RfbWVhbmluZykgLi4uIG9rCnRlc3RfaW5jcmVtZW50YWxfcHJvY2Vzc2luZ19saW1pdCAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X2luY3JlbWVudGFsX3Byb2Nlc3NpbmdfbGltaXQpIC4uLiBvawp0ZXN0X2luZGVwZW5kZW50X2F1ZGl0b3JfcmVjb25jaWxlc19leGFjdF9rZXlzIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfaW5kZXBlbmRlbnRfYXVkaXRvcl9yZWNvbmNpbGVzX2V4YWN0X2tleXMpIC4uLiBvawp0ZXN0X2luZGVwZW5kZW50X292ZXJsYXBfdmVjdG9ycyAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X2luZGVwZW5kZW50X292ZXJsYXBfdmVjdG9ycykgLi4uIG9rCnRlc3RfaW50ZXJydXB0ZWRfZG9jdW1lbnRfd3JpdGVfcmVtb3Zlc19vbmx5X293bmVkX3BhcnRpYWwgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9pbnRlcnJ1cHRlZF9kb2N1bWVudF93cml0ZV9yZW1vdmVzX29ubHlfb3duZWRfcGFydGlhbCkgLi4uIG9rCnRlc3RfaW50ZXJydXB0ZWRfcGFja2FnZV9uZXZlcl9wdWJsaXNoZXNfY29tcGxldGlvbl9tYXJrZXIgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9pbnRlcnJ1cHRlZF9wYWNrYWdlX25ldmVyX3B1Ymxpc2hlc19jb21wbGV0aW9uX21hcmtlcikgLi4uIG9rCnRlc3RfaW50cmluc2ljX2xvY2F0b3JzX2Rpc3Rpbmd1aXNoX211bHRpcGxlX2lkZW50aXRpZXMgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9pbnRyaW5zaWNfbG9jYXRvcnNfZGlzdGluZ3Vpc2hfbXVsdGlwbGVfaWRlbnRpdGllcykgLi4uIG9rCnRlc3Rfa2V5X2NvbnN0cnVjdGlvbl9leGhhdXN0aW9uX2FuZF9ncm91cF9idWRnZXRfc2l0ZXMgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9rZXlfY29uc3RydWN0aW9uX2V4aGF1c3Rpb25fYW5kX2dyb3VwX2J1ZGdldF9zaXRlcykgLi4uIG9rCnRlc3RfbGl0ZXJhbF9wcmVjb21wdXRlZF92ZWN0b3JzIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfbGl0ZXJhbF9wcmVjb21wdXRlZF92ZWN0b3JzKSAuLi4gb2sKdGVzdF9tYW5pZmVzdF9iaW5hcnlfYW5kX21hbGZvcm1lZF9yZXF1aXJlX2Rpc3Bvc2l0aW9uIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfbWFuaWZlc3RfYmluYXJ5X2FuZF9tYWxmb3JtZWRfcmVxdWlyZV9kaXNwb3NpdGlvbikgLi4uIG9rCnRlc3RfbWlzc2luZ19leHRyYV9hbmRfdGFtcGVyZWRfY2h1bmtzIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfbWlzc2luZ19leHRyYV9hbmRfdGFtcGVyZWRfY2h1bmtzKSAuLi4gb2sKdGVzdF9taXNzaW5nX3B1YmxpY2F0aW9uX21hcmtlcl9yZWplY3RzX3BhcnRpYWxfcGFja2FnZSAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X21pc3NpbmdfcHVibGljYXRpb25fbWFya2VyX3JlamVjdHNfcGFydGlhbF9wYWNrYWdlKSAuLi4gb2sKdGVzdF9taXNzaW5nX3N1cmZhY2VfYW5kX3Vuc3VwcG9ydGVkX25vdF9hcHBsaWNhYmxlIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfbWlzc2luZ19zdXJmYWNlX2FuZF91bnN1cHBvcnRlZF9ub3RfYXBwbGljYWJsZSkgLi4uIG9rCnRlc3RfbXV0YXRpb25fbWFuaWZlc3RfbWFwc190b19yZWFsX3Rlc3RzIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfbXV0YXRpb25fbWFuaWZlc3RfbWFwc190b19yZWFsX3Rlc3RzKSAuLi4gb2sKdGVzdF9uZXdfd29ya19hY2NvdW50aW5nX2JvdW5kYXJpZXMgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9uZXdfd29ya19hY2NvdW50aW5nX2JvdW5kYXJpZXMpIC4uLiBvawp0ZXN0X25vbl9pbmplY3RpdmVfbWFwcGluZ19pbmNsdWRpbmdfcmV0YWluIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3Rfbm9uX2luamVjdGl2ZV9tYXBwaW5nX2luY2x1ZGluZ19yZXRhaW4pIC4uLiBvawp0ZXN0X25vbl9uZmNfc3RyaW5nIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3Rfbm9uX25mY19zdHJpbmcpIC4uLiBvawp0ZXN0X25vdF9hcHBsaWNhYmxlX3JlcXVpcmVzX2N1cnJlbnRfc2VtYW50aWNfcmV2aWV3IChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3Rfbm90X2FwcGxpY2FibGVfcmVxdWlyZXNfY3VycmVudF9zZW1hbnRpY19yZXZpZXcpIC4uLiBvawp0ZXN0X29wYXF1ZV9zeW1saW5rX2ludmVudG9yeV9ub3RfYm91bmRfcmVjb3JkIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3Rfb3BhcXVlX3N5bWxpbmtfaW52ZW50b3J5X25vdF9ib3VuZF9yZWNvcmQpIC4uLiBvawp0ZXN0X291dHB1dF9zeW1saW5rX2FuZF9hbmNlc3Rvcl9zeW1saW5rIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3Rfb3V0cHV0X3N5bWxpbmtfYW5kX2FuY2VzdG9yX3N5bWxpbmspIC4uLiBvawp0ZXN0X3BoeXNpY2FsX3ZlY3RvcnNfYW5kX2FsbF9yYXdfa2luZHMgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9waHlzaWNhbF92ZWN0b3JzX2FuZF9hbGxfcmF3X2tpbmRzKSAuLi4gb2sKdGVzdF9wcm90b2NvbF9lcnJvcl9pZGVudGl0eV9pc19zaGFyZWQgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9wcm90b2NvbF9lcnJvcl9pZGVudGl0eV9pc19zaGFyZWQpIC4uLiBvawp0ZXN0X3JlY292ZXJ5X3dyb25nX2tpbmRfYWZ0ZXJfcHJpb3JfdmlzaXQgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9yZWNvdmVyeV93cm9uZ19raW5kX2FmdGVyX3ByaW9yX3Zpc2l0KSAuLi4gb2sKdGVzdF9yZWhhc2hlZF9ub25jYW5vbmljYWxfY2h1bmtfcmVwYXJ0aXRpb24gKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF9yZWhhc2hlZF9ub25jYW5vbmljYWxfY2h1bmtfcmVwYXJ0aXRpb24pIC4uLiBvawp0ZXN0X3JldGFpbmVkX2F1ZGl0X3BvbGljeV9wb3B1bGF0aW9uIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfcmV0YWluZWRfYXVkaXRfcG9saWN5X3BvcHVsYXRpb24pIC4uLiBvawp0ZXN0X3JldGFpbmVkX2Nyb3NzX2ludGVycHJldGF0aW9uX3JlamVjdGlvbiAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X3JldGFpbmVkX2Nyb3NzX2ludGVycHJldGF0aW9uX3JlamVjdGlvbikgLi4uIG9rCnRlc3RfcmV0YWluZWRfZHVwbGljYXRlX2F1ZGl0X21lYW5pbmdzIChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3RfcmV0YWluZWRfZHVwbGljYXRlX2F1ZGl0X21lYW5pbmdzKSAuLi4gb2sKdGVzdF9yZXRhaW5lZF9wYXRoX2NvbXBvbmVudF9jbGFpbV90cnV0aCAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X3JldGFpbmVkX3BhdGhfY29tcG9uZW50X2NsYWltX3RydXRoKSAuLi4gb2sKdGVzdF9zZWxlY3Rvcl9wcmVzZW5jZV9hbmRfbWFsZm9ybWVkX2tleV9saXN0cyAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X3NlbGVjdG9yX3ByZXNlbmNlX2FuZF9tYWxmb3JtZWRfa2V5X2xpc3RzKSAuLi4gb2sKdGVzdF9zb3VyY2Vfc3VmZml4X2xpdGVyYWxfaXNfb25lX2NvbXBvbmVudCAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X3NvdXJjZV9zdWZmaXhfbGl0ZXJhbF9pc19vbmVfY29tcG9uZW50KSAuLi4gb2sKdGVzdF9zdGFsZV9ydWxlX2NvdW50IChfX21haW5fXy5Qcm90b2NvbFRlc3RzLnRlc3Rfc3RhbGVfcnVsZV9jb3VudCkgLi4uIG9rCnRlc3RfdW5rbm93bl91bml0X2tpbmQgKF9fbWFpbl9fLlByb3RvY29sVGVzdHMudGVzdF91bmtub3duX3VuaXRfa2luZCkgLi4uIG9rCnRlc3RfdmFsaWRfYXV0aGVudGljYXRlZF9nZW5lcmF0aW9uX2FuZF9yZWNvbmNpbGlhdGlvbiAoX19tYWluX18uUHJvdG9jb2xUZXN0cy50ZXN0X3ZhbGlkX2F1dGhlbnRpY2F0ZWRfZ2VuZXJhdGlvbl9hbmRfcmVjb25jaWxpYXRpb24pIC4uLiBvawoKLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLQpSYW4gNTQgdGVzdHMgaW4gMC4yNzdzCgpPSwo=
2026-10-26T07:08:35.6508945Z PR9_LOG_END=7091:52a4661fd0ee94bf0fa70ceb955ffb73385fa8f79d91f69fa5631ebaf4f5ce97
2026-10-26T07:08:35.6628072Z Cleaning up orphan processes
````
