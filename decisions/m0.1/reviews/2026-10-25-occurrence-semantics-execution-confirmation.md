# Sarah — Independent confirmation of PR #6’s second bounded synthetic run

## 1. Executive disposition

**The second execution is confirmed within the externally reported evidence boundary: the published output accounts for all 54 authored test methods, each reports `ok`, and the result is bound to the exact repaired revision. BML-OS05’s remaining synthetic execution-evidence concern is resolved.**

**One record-repair requirement remains before an unqualified owner-acceptance recommendation: BML-OS12.** The current PR body still says that no candidate test has executed against this head and that only the failed parent run occurred. The later comments establish the correct history, but the mutable, current-status summary should be reconciled before Greg’s acceptance decision.

This is **not a candidate-code failure or a failed execution confirmation**. No source change or additional run is required to correct that record. I found no new implementation regression in this review.

I did not execute or import candidate code, rerun tests, or change any repository or GitHub state.

## 2. Exact identities and repository state

| Item | Independently established value |
|---|---|
| Repository / PR | `gregkrsak/bowfin-migration-ledger` — PR #6 |
| Branch | `m01-v2-occurrence-semantics-repair` |
| Target | `main` |
| Accepted base | `d3832e24657b7ccd2c118b2aee6832f4d1289ca9` |
| **Executed and reviewed head** | **`23bed495c73b600d0a849b3c336d08a5c6cdd1b1`** |
| **Tree** | **`c642dca4c4b8ae4e08f1250e1862bbe821c43b04`** |
| **Protocol-v2 subtree** | **`d0e0c7419020415ddc7996631db616b2f73a25b3`** |
| Sole parent | `2d822f1228e230505578c0e482219e3b012cac01` |
| **Test-module blob** | **`8c6e8a241cbc93b947ca9ee29c1efd7d91e05551`** |

The Git commit and complete protocol-tree readbacks match all assigned identities. No intervening source revision separates the statically confirmed repair, second authorization, second execution report, and current PR head.  

Final PR #6 readback remains **open, draft, unmerged**, targeted to `main`, at that head. Ledger `main` remains at the accepted base. PR #5 remains **open, draft, unmerged** at `8fef7a12cf89d5cdad9d03db187d6060e450bc1d`; I inspected its metadata only.   

## 3. Authorization-to-execution correspondence

I read the complete static confirmation, second authorization, second execution report, and earlier failed-run report. Their publication sequence is coherent:

| Record | Publication time, UTC | Meaning |
|---|---|---|
| `6407766961` | October 26, 2026, 03:47:01 | Failed execution of the parent revision; BML-OS11 identified |
| `6407933361` | October 26, 2026, 04:02:10 | Static confirmation of the corrected revision; recommendation for a separate second-run decision |
| `6407936545` | October 26, 2026, 04:02:27 | Greg’s new, exact-revision, one-run authorization |
| `6407954265` | October 26, 2026, 04:04:04 | Second execution report: 54 tests passed |

These are comment publication times, not independently observed process start/end timestamps.    

The second authorization binds the exact repaired commit, tree, protocol subtree, and **54 authored methods**. It explicitly states that it neither reuses nor extends the exhausted parent authorization. It requires a fresh temporary materialization, complete twelve-file preflight, post-run identity and unexpected-file checks, exactly one invocation, and publication of a complete report. Its exact command is:

```text
python3 -B -I -m unittest discover -s tests -p 'test_protocol.py' -v
```

It prohibits retries, in-run repairs, production inputs, PR #5, compiler scanning, network access, dependency installation, workflows, compiler/Rust execution, acceptance, merge, and later migration work. It terminates upon completion, identity drift, or the first unexpected result. 

Miles’s report names the same identities and command, says the invocation occurred exactly once, records the requested results and custody checks, and denies the prohibited activity. **Its claimed behavior is within—not broader than—the authorization.** The completed run exhausts this second authorization; neither reviewed one-run authorization remains available for reuse. 

### Recorded environment

| Field | Reported value |
|---|---|
| Interpreter | CPython 3.12.14 |
| Interpreter build string | Clang 22.1.3 |
| Executable | `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3` |
| Platform | Linux 6.18.55, x86_64, glibc 2.39 |
| Working directory | Fresh copy of the exact `protocol/m0.1/v2` subtree |

The report discloses no interpreter substitution, new dependency, alternate candidate source, or command deviation. The Clang entry is an interpreter build string, not a claim that a compiler was invoked during the run. These environment details remain executor observations; I did not inspect the temporary host or hash its interpreter binary. 

## 4. Complete 54-test identity and result reconciliation

I read the complete current test module and extracted its `ProtocolTests.test_*` definitions as text, without importing or compiling it. I separately extracted the result lines from the complete published unittest output and compared names, qualified identities, multiplicities, statuses, and sets using reviewer-authored data-only analysis. The source readback identifies the unchanged test-module blob.  

### Reconciliation result

| Check | Result |
|---|---:|
| Authored test-method definitions | **54** |
| Unique authored method names | **54** |
| Reported test-result lines | **54** |
| Unique reported method names | **54** |
| Duplicate result names | **0** |
| Authored methods omitted from output | **0** |
| Unexpected reported methods | **0** |
| Short-name versus qualified-name mismatches | **0** |
| Non-`ok` result lines | **0** |

Every reported identity has the class prefix `test_protocol.ProtocolTests.`. The complete reconciled method-name list below reports **`ok` for every entry**. 

```text
test_archive_and_dot_path_reject
test_auditor_high_work_no_match_stops_at_budget
test_authenticated_cedp_ancestry_trees_targets_and_recovery
test_authenticated_export_rejects_stale_bytes_mode_and_extra_path
test_authenticated_export_rejects_wrong_tree
test_authenticated_subtree_view_keeps_archive_opaque_and_ineligible
test_candidate_key_separates_physical_discovery_from_semantics
test_competing_package_creator_is_never_deleted
test_compiler_intermediate_content_and_decision_preservation
test_compiler_source_view_must_be_repository_root
test_cumulative_package_budget_rejects_before_next_read
test_direct_compact_input_field_validation
test_duplicate_json_key
test_equal_count_different_key
test_evidence_record_binds_actual_exports_and_generated_bytes
test_exact_candidate_keys_split_roles_within_one_file
test_exact_classification_population_and_collision_descriptor
test_export_eligibility_separates_fixture_and_production
test_fifo_is_rejected_before_blocking_open
test_forged_physical_keys
test_freshness_expiry_and_invalidation
test_generated_rows_are_bound_to_compact_meaning
test_incremental_processing_limit
test_independent_auditor_reconciles_exact_keys
test_independent_overlap_vectors
test_interrupted_document_write_removes_only_owned_partial
test_interrupted_package_never_publishes_completion_marker
test_intrinsic_locators_distinguish_multiple_identities
test_key_construction_exhaustion_and_group_budget_sites
test_literal_precomputed_vectors
test_manifest_binary_and_malformed_require_disposition
test_missing_extra_and_tampered_chunks
test_missing_publication_marker_rejects_partial_package
test_missing_surface_and_unsupported_not_applicable
test_mutation_manifest_maps_to_real_tests
test_new_work_accounting_boundaries
test_non_injective_mapping_including_retain
test_non_nfc_string
test_not_applicable_requires_current_semantic_review
test_opaque_symlink_inventory_not_bound_record
test_output_symlink_and_ancestor_symlink
test_physical_vectors_and_all_raw_kinds
test_protocol_error_identity_is_shared
test_recovery_wrong_kind_after_prior_visit
test_rehashed_noncanonical_chunk_repartition
test_retained_audit_policy_population
test_retained_cross_interpretation_rejection
test_retained_duplicate_audit_meanings
test_retained_path_component_claim_truth
test_selector_presence_and_malformed_key_lists
test_source_suffix_literal_is_one_component
test_stale_rule_count
test_unknown_unit_kind
test_valid_authenticated_generation_and_reconciliation
```

The transcript ends with:

```text
Ran 54 tests in 0.337s

OK
```

The report separately records **0.359 seconds process wall time** and **exit status 0**. The transcript, method inventory, and summary agree on 54 discovered, 54 passed, zero failures, zero errors, and zero skipped. Wall time and process exit status are reported harness measurements, not values I independently measured. 

There are **29 further result lines after `test_independent_overlap_vectors`**, all `ok`, followed by the final successful summary. No later reported failure is hidden by attention to the previously failing method.

## 5. BML-OS11 and OS08–10 execution confirmation

| Finding/control | Reported second-run result | Consequence |
|---|---|---|
| BML-OS11 — `test_independent_overlap_vectors` | `ok` | The former exact-key filter error did not recur in the reported repaired run |
| BML-OS08 — `test_retained_path_component_claim_truth` | `ok` | The authored intrinsic-path positive and rejection controls completed |
| BML-OS09 — `test_source_suffix_literal_is_one_component` | `ok` | The authored separator negatives and multibyte positive completed |
| BML-OS10 — `test_incremental_processing_limit` | `ok` | The retargeted budget-boundary control completed |

All four results appear in the complete output, not only in Miles’s narrative summary. 

The unchanged overlap test iterates through `crate` and then `domain`, with no skip or exception-catching path that would convert the earlier error into success. Its reported `ok` therefore supports completion of both iterations and their assertions, consistent with the previously reviewed correction. It does not prove correctness of every possible overlap. 

**BML-OS11 is now resolved at both the static-repair level and the reported synthetic execution-evidence level.** The successful run does not retroactively validate the defective parent vector.

## 6. Failed-parent versus passing-repair evidence

The records keep the two runs distinct:

| Property | Failed parent run | Passing repaired run |
|---|---|---|
| Head | `2d822f1228e230505578c0e482219e3b012cac01` | `23bed495c73b600d0a849b3c336d08a5c6cdd1b1` |
| Tree | `93c16909b1cab865d1a82ba55590bcd918881241` | `c642dca4c4b8ae4e08f1250e1862bbe821c43b04` |
| Discovered / passed | 54 / 53 | 54 / 54 |
| Errors | 1 | 0 |
| Exit | 1 | 0 |
| Unittest time | 0.302 seconds | 0.337 seconds |
| Process wall time | 0.304 seconds | 0.359 seconds |
| Authorization | First one-run authorization, exhausted | Separate second one-run authorization, exhausted |

The earlier report still contains the original `E_AUDIT_CANDIDATE_FILTER` traceback, defective crate locator, and failure disposition. The corrected static report explicitly acknowledges the earlier review miss. Neither is replaced by the passing report.   

The second run’s passing result belongs only to the repaired identities. The successful parent controls remain historical parent results, not a substitute for this second run.

## 7. Source custody and `-B -I` harness assessment

### Canonical twelve-file set

The complete, non-truncated Git tree independently supplies the following exact authorized set. All entries are regular files with Git mode **`100644`**; paths are relative to `protocol/m0.1/v2/`. 

| Path | Bytes | Git blob |
|---|---:|---|
| `PROTOCOL.md` | 34,427 | `f714973fe696ac6fb351d05ce700e47aa795bd10` |
| `README.md` | 9,119 | `054fc685cb33ebe0edf85f392d3bc5424b1d40ed` |
| `audit_scan.py` | 16,388 | `d8ac2f74adaceedc638e78dafb488dfbbcb359a7` |
| `generate.py` | 24,802 | `7d103aa4d61c42d089e991e25b6c3763cae08ffe` |
| `limits.json` | 683 | `46f8c03290682d275e30c27e3f353ebfd3f291b9` |
| `protocol_lib.py` | 44,701 | `6fc10a6469f9944dfa57f3553661ab858a8a57a8` |
| `schema.json` | 27,406 | `56f81ff76b38c1a870fdb49abc5e378f1c003370` |
| `tests/fixtures/mutations.json` | 12,940 | `4aa64b28f9bcd472f4582f68e3b9c131fee0ac68` |
| `tests/fixtures/valid-case.json` | 4,974 | `a1cc67fbf970f745c5e2473d6dec9019bf7858b4` |
| `tests/fixtures/vectors.json` | 4,531 | `b4113e7d35134f99507e685e72d0ab6478e5f751` |
| `tests/test_protocol.py` | 103,835 | `8c6e8a241cbc93b947ca9ee29c1efd7d91e05551` |
| `verify.py` | 113,952 | `e8492b02a262773c697f0c32f5fc22090ad84ec9` |

The execution report binds its pre/post checks to this exact subtree and states that a fresh temporary workspace contained these twelve authorized files before execution; afterward the same twelve remained with matching blobs, modes, and sizes, none missing, no unexpected files, and no `__pycache__` or `.pyc` artifacts. 

**Direct verification stops at the repository manifest and the published custody statement.** The report does not reproduce a separate per-file local pre/post comparison transcript, and I did not access the temporary workspace. I therefore confirm that the reported custody claim is specific, consistent with the authoritative set, and within the authorization—not that I personally observed those local checks.

Likewise, current unchanged GitHub state corroborates repository continuity, but does not independently prove every event in the temporary environment.

### Harness semantics

`-I` selects Python isolated mode, excludes the normal current/script-directory and user-site additions, and ignores `PYTHON*` environment variables. `-B` suppresses import-time `.pyc` writes through a command-line option, so it does not depend on the ignored `PYTHONDONTWRITEBYTECODE` variable. The authorized combination is consistent with the reported absence of bytecode artifacts. [Python documentation](https://docs.python.org/3.12/using/cmdline.html)

Neither option is an operating-system sandbox. The report explicitly disclaims empirical host-containment guarantees. It supplies no syscall-level network audit, interpreter-binary attestation, or measured external resource-containment proof, and I infer none. Its “no network,” “no installation,” and related scope statements remain externally reported observations. 

The harness change addresses the earlier cache observation without altering candidate code. The first run’s cache creation remains disclosed historical evidence; the second report does not erase it.

## 8. BML-OS05 disposition

**BML-OS05’s remaining synthetic execution-evidence concern is resolved for this exact revision.**

The supporting chain now includes the exact-revision static reviews, independently checked corrected vectors, unchanged 54-method test module, separate owner authorization, complete method-by-method passing output, and explicit pre/post custody statement. The prior failure remains available and correctly attributed.   

The evidence classification is **externally executed, with the published output independently inspected and reconciled against the pinned source**. It is not personally executed verification or cryptographic attestation of the process.

Closure applies to the authored synthetic controls and this recorded environment. It does not establish production completeness, production-input correctness, valid migration evidence, cross-platform behavior, independent human authorship of every expectation, or universal protocol correctness.

## 9. PR-body truthfulness determination

**The later comments preserve truthful chronological history and are sufficient to confirm the execution result. They do not make the PR’s contradictory current-status summary accurate. I require a PR-body record correction before an unqualified owner-acceptance recommendation.**

At final readback, the body still presents these claims under current candidate/validation headings:

> “No candidate module or test has executed against the current head.”

It also says the only bounded execution was the failed parent run and that focused static confirmation remains pending. Those statements were true before the later records, but are now false as an unqualified description of the same current head. 

### BML-OS12 — Current PR summary contradicts the preserved execution record

**Classification:** Confirmed record-correctness defect  
**Severity:** Minor; **required correction at the owner-acceptance record gate**  
**Affected surface:** PR #6 body, especially “Current exact candidate,” “Review, execution, and repair history,” “Validation status,” and the description of the next task  
**Candidate-code impact:** None identified

**Consequence.** A reader using the PR’s current summary receives a different execution state from a reader following the later authorization and report comments. The durable history is recoverable, but the owner-facing acceptance record is unnecessarily contradictory.

**Smallest sufficient repair.** An authorized maintainer should update the current-status summary to link the completed BML-OS11 static confirmation, separate second authorization, and second execution report; record **54/54, exit 0 at the exact repaired identities**; preserve the **53/54, exit 1 parent failure**; state that both one-run authorizations are exhausted; and leave owner acceptance, readiness transition, merge, production work, and later phases separately ungranted.

The original wording may be retained if explicitly labeled as a dated historical snapshot and followed by the current status. The failed report and adverse reviews should not be rewritten.

**No candidate commit or rerun is needed for this correction.** I have not changed the body. The pinned README’s pre-execution description is an immutable statement of its construction-time state; this finding does not require editing that source file and thereby changing the executed tree.

## 10. Evidence boundaries and review method

I refreshed the complete Sarah charter at governance commit `37d4446153cd761b70ad7fc599db1df994352585`, blob **`4df5839f388b50b5689c101f20fc845fb157700c`**, and read current ledger `AGENTS.md`. I read all four required records, the complete current test module, relevant pinned source context, current PR metadata, and the complete protocol manifest.    

The distinction is:

| Evidence level | Established here |
|---|---|
| Directly inspected | GitHub identities/state, authoritative file set, authorization/report contents, source method definitions |
| Independently calculated | Test-name sets, duplicates, omissions, status counts, qualified-name agreement, and subsequent-result count |
| Externally reported and checked for consistency | One invocation, temporary environment, runtime identity, pre/post local custody, wall time, process exit, and absence of prohibited activity |
| Not established | Independent host observation, interpreter binary identity, actual resource-cap enforcement, exhaustive filesystem/network audit, production validity, or cross-platform correctness |

No material retrieval gap prevents this focused conclusion. The absence of raw local custody artifacts limits its forensic strength but is not treated as a failed test or concealed identity discrepancy.

I executed only reviewer-authored **text and count analysis**. No candidate module, extracted function, fixture, test, generator, auditor, verifier, accepted predecessor tool, or archived tool was executed or imported. No workflow, production scan, or evidence-generation operation occurred.

## 11. Remaining findings and readiness

| Item | Disposition |
|---|---|
| BML-OS11 fixture repair | Confirmed statically and supported by the repaired-run control result |
| BML-OS08–10 controls | Reported passing in the exact second run; no recurrence shown |
| BML-OS05 synthetic execution evidence | **Resolved within the stated evidence boundary** |
| New candidate-code finding | None identified |
| **BML-OS12 current PR summary** | **Record correction required before favorable owner-acceptance readiness** |
| Further execution authorization | None remains active in the reviewed chain |
| PR #5 | Separate, unchanged draft; no authority to repair or accept it |

The source and synthetic-result evidence support progression to an owner decision once the current PR summary is corrected. The outstanding requirement is **record consistency, not another code repair or another test run**.

## 12. Final recommendation and authority

This report applies only to:

```text
Head:             23bed495c73b600d0a849b3c336d08a5c6cdd1b1
Tree:             c642dca4c4b8ae4e08f1250e1862bbe821c43b04
Protocol subtree: d0e0c7419020415ddc7996631db616b2f73a25b3
Execution record: issuecomment-6407954265
```

**I posted nothing to GitHub.** No repository content, metadata, workflow, draft state, approval, or merge was changed.

This confirmation does not accept the protocol, mark PR #6 ready, authorize merge or another execution, permit production work or PR #5 repair, complete M0.1, or authorize M1. **Greg remains the sole acceptance and merge authority.**

**RECORD REPAIR REQUIRED — NOT READY FOR OWNER ACCEPTANCE DECISION**