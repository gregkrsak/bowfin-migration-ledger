# Sarah — Independent confirmation of PR #9’s synthetic validation

**NO BLOCKING FINDINGS IDENTIFIED. The evidence supports recommending the exact PR #9 revision for Greg’s separate acceptance and merge decision.**

I independently confirmed that the successful job executed the reviewed **PR #9 protocol files**, not the operational branch’s older protocol copy. I reconstructed the retained output, verified its **7,091-byte length and SHA-256**, and reconciled all **54 exact predecessor test methods**, with no omissions, duplicates, non-`ok` results, failures, errors, or skips.

The containment evidence is materially stronger than a bare successful-run summary: it includes the launcher, immutable execution image, Docker configuration, in-container limit readbacks, process outcome, and retained log. Its limits are stated below.

**PR #9 is the tooling candidate. PR #10 remains an operational/preservation surface and must not be merged into `main` as part of accepting PR #9.**

## 1. Exact identities and live state

| Surface | Verified identity |
|---|---|
| **Reviewed/tested PR #9 head** | **`62a19baf0f67474f0c25c609f9a4300aa11e74d4`** |
| **Reviewed/tested tree** | **`27a18b261d8f5325c2414ad9e18193e91b870a37`** |
| Reviewed protocol subtree | `cd514c89fda2d91318c7a63b8b737118141f7b2c` |
| Sole parent / base / current `main` | `edb0a11851cb1b51727c857d03c045ad1e7daa95` |
| Operational workflow head | `288b0f6c3a052ef32b9b61e2f41f83669ac46e75` |
| Operational workflow tree | `87af83dbe349098f6c78c1e05801f745b67aefb9` |
| Actions run / attempt | `40283940081` / **1** |
| Job | `121443126469` |
| Preservation commit | `851069fc4ec7514cb330125619f5ffa4703a60dc` |
| Preservation tree | `050ede8d60e0a1d244aeb8c957505817a61225a6` |
| Preservation blob | `030b06028f50c544b6311dbd08973bc79988e804` |

The commit object confirms the tested tree and required sole parent. Final PR #9 readback remains **open, draft, unmerged**, targeting `main`, at the exact reviewed head. `main` remains unchanged. No identity drift was found.   

GitHub reports the run completed successfully at the operational head, attempt 1. Its associated PR #10 now points to the later preservation commit; that does **not** change the recorded workflow head that actually ran.  

I refreshed and read the complete current Sarah charter, blob **`4df5839f388b50b5689c101f20fc845fb157700c`**, at governance commit `37d4446153cd761b70ad7fc599db1df994352585`, and the ledger’s complete `AGENTS.md`. The prior static review remains the baseline; this report addresses the execution-evidence delta.    

## 2. The executed subject was PR #9—not the runner branch

**Confirmed.** The workflow does not check out and run the operational branch’s protocol directory.

The workflow bootstrap retrieves only its orchestration helper from `GITHUB_SHA`, checks that helper against the fixed SHA-256 recorded in the authorization, and executes the helper. The helper then uses hard-coded **PR #9** head, tree, base, and protocol-subtree identities to acquire the test subject.  

Before starting the container, the inspected helper:

- verifies PR #9’s head, repository, target, draft/open/unmerged state, and unchanged `main`;
- verifies the subject commit’s tree and sole parent;
- requires exactly twelve manifest entries and reconstructs their protocol subtree;
- retrieves every file through the exact PR #9 commit;
- checks each file’s byte count, Git blob SHA-1, and SHA-256; and
- explicitly checks that the acquired `max_processing_steps` equals **100,000,000,000**. 

I compared the logged twelve-file inventory with the complete, non-truncated Git tree. Every path, mode, size, and blob identity agrees. Using independently written data-only code, I also reconstructed the manifest’s Git tree; it reproduces:

```text
cd514c89fda2d91318c7a63b8b737118141f7b2c
```

The twelve files total **400,136 bytes**, all with Git mode `100644`. 

Three identities particularly distinguish the tested profile from the operational branch’s inherited older copy:

| File | Verified tested blob |
|---|---|
| `PROTOCOL.md` | `fcd376d22a01047e0923dffed948d8c66d47dfae` |
| `limits.json` | `00859ebf3bf80203e3ade39af7b88e28c39ff604` |
| `protocol_lib.py` | `7c34cc34d6d70c6d1a08006ceb2a63ca1f501d0f` |

The operational tree retains the base’s older protocol subtree. The log instead records the three candidate identities above and the new limits digest. The read-only `/review` mount points to the freshly acquired candidate directory, and the container wrapper runs `/review/tests/test_protocol.py`. That establishes the relevant subject correspondence despite the different workflow SHA.   

I did not independently rehash all 400,136 source bytes locally in this review. The conclusion combines authoritative Git-object comparison, independent manifest-tree reconstruction, inspection of the acquisition checks, and the successful live job log showing those checks completed.

## 3. Output reconstruction and complete test reconciliation

I retrieved the actual GitHub job log independently of the execution-report comment. It contains one encoded output chunk, indexed **0**, followed by:

```text
PR9_LOG_END=7091:52a4661fd0ee94bf0fa70ceb955ffb73385fa8f79d91f69fa5631ebaf4f5ce97
```

The preserved record contains the same chunk and completion marker. 

My independent base64 decoding produced:

```text
Decoded bytes: 7,091
SHA-256:       52a4661fd0ee94bf0fa70ceb955ffb73385fa8f79d91f69fa5631ebaf4f5ce97
```

The chunk is valid base64, its decoded length matches both the report and completion marker, and the independently calculated digest matches exactly. The decoded text contains runtime provenance, the complete method-by-method output, and the final unittest summary—not merely selected successful lines.

I compared the result names with the declarations in the reviewed test-module blob, **`8c6e8a241cbc93b947ca9ee29c1efd7d91e05551`**, using source-text inspection and independent set/multiplicity analysis. I did not use the runner’s `expected_methods` field as the sole oracle.   

| Reconciliation check | Independent result |
|---|---:|
| Authored predecessor methods | **54** |
| Reported result lines | **54** |
| Unique reported names | **54** |
| Missing authored methods | **0** |
| Extra methods | **0** |
| Duplicate method results | **0** |
| Short-name/qualified-name mismatch | **0** |
| Non-`ok` result lines | **0** |
| Failures / errors / skips | **0 / 0 / 0** |

The reconstructed output ends with:

```text
Ran 54 tests in 0.277s

OK
```

The retained Docker state reports **`ExitCode: 0`**, the attach process reports **0**, and the helper records **`status: passed`**, **one attempted invocation**, **no containment stop**, and **`OOMKilled: false`**. Its external container/attachment duration is **1.328 seconds**, distinct from the unittest-reported 0.277 seconds.  

The helper’s success path requires the exact method set, successful container and attach outcomes, clean summary, runtime provenance, and a final subject-identity check. Its exception path records failure and ends nonzero. The success conclusion is therefore supported by more than the workflow’s green status. 

## 4. Containment and runtime assessment

### Immutable execution image

The host acquires the official `python:3.12-slim-bookworm` image, resolves it to a repository digest, and passes that **immutable digest—not the mutable tag—to container creation**. This acquisition-then-lock procedure is explicitly described in the authorization.  

The retained identities are:

```text
Execution image:
python@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70

Local image ID:
sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77
```

Runtime provenance reports **CPython 3.12.15**, GCC 12.2.0 build string, isolated mode active, and **UID 65534**. The wrapper checks the Python 3.12 family, isolated mode, effective capabilities, no-new-privileges, cgroup limits, and resource limits before entering the test module.  

The image digest makes this execution’s selected image identifiable. It is not a claim that the image was predetermined before acquisition or that its entire supply chain was independently audited here.

### Requested settings versus observed settings

| Boundary | Configuration and evidence | Qualification |
|---|---|---|
| Non-root execution | `65534:65534` configured; runtime reports UID 65534 | Direct runtime readback, not merely a desired user string |
| Network | Docker `NetworkMode: none`, checked before start | No separate network-attempt test or syscall trace |
| Credentials | Read-only host token used for acquisition; no token passed in container arguments; credential-variable and mount checks | Supports no forwarded Actions credentials; not a forensic audit of every image byte |
| Root and candidate files | Read-only root; sole host bind is `/review`, read-only | Docker configuration checked before start |
| Privilege | All capabilities dropped; no-new-privileges; nonprivileged container | Wrapper checks `CapEff == 0` and `NoNewPrivs == 1` before tests |
| Memory | 1 GiB configured; runtime `memory.max = 1073741824` | No memory-exhaustion benchmark |
| Swap | Runtime `memory.swap.max = 0` | Matches the requested disabled-swap state |
| CPU rate | One CPU configured; runtime `cpu.max = 100000 100000` | CPU-rate quota, not total CPU time |
| PIDs | 64 configured; runtime `pids.max = 64` | No PID-exhaustion test |
| CPU time | Soft/hard limits of 240 seconds per process | Runtime readback confirms both values |
| File size | Soft/hard limits of 64 MiB per file | Not a total filesystem quota |
| Descriptors | Soft/hard limits of 256 | Runtime readback confirms both values |
| Writable scratch | `/tmp` tmpfs, 128 MiB, `noexec,nosuid,nodev` | Applies to that mount; not a physical-memory measurement |
| Test wall time | Host supervisor checks a 300-second deadline and kills the container on expiry | Implemented safeguard; not exercised by this fast run |
| Captured output | 4 MiB bound, with kill/failed-result path on overflow | Captured-buffer bound, not a claim about every logging layer |
| Overall job | Twelve-minute Actions timeout | Workflow-level ceiling |

The requested flags, Docker inspection results, and in-container readbacks agree. The live log also shows read-only contents/metadata/PR permissions for the host acquisition token. The candidate container does not receive the host Docker socket or a repository checkout containing credentials.   

**Assessment:** this is an adequate bounded synthetic execution setup for the exact reviewed workload. It is not empirical proof that every boundary withstands exhaustion or hostile exploitation. The evidence is configuration inspection plus successful runtime assertions, not personally observed runner execution or a general sandbox certification.

The helper verifies source identities before execution and mounts them read-only. It rechecks the GitHub subject afterward, but does not publish a separate post-run source-file checksum table. I therefore rely on the inspected acquisition and read-only-mount design for that part of custody, rather than claiming an additional local post-run rehash.

## 5. Authorization, one invocation, and chronology

The authorization publication at **07:08:14 UTC on October 26, 2026** precedes the Actions run’s creation at **07:08:17 UTC**. It names the exact tested subject, separate operational commit, helper digest, one invocation, containment requirements, and prohibition on retries or reruns.  

The repository’s run listing for the operational head returns **one run**. That run has **attempt 1**, no previous-attempt URL, one successful validation job, and a helper report containing one attempted test invocation. The helper has one container-start path and no retry loop.   

The earlier local isolation probe is consistently disclosed as a setup failure **before candidate tests**, with zero local test invocations. I did not observe that local process or obtain a separate local transcript in this review. Its zero-test classification is therefore **reported and consistently preserved**, while the single Actions invocation is corroborated by GitHub metadata and logs. It is not misrepresented as a failed candidate test followed by an undisclosed retry.  

The authorization is exhausted. The workflow’s attempt guard and path filter do not themselves confer permission for any future run.

Current PR #9 prose correctly separates **construction-time static checks** from the later successful execution and confines earlier accepted-profile results to their earlier identities. It identifies independent confirmation and Greg’s decision as subsequent gates. I found no stale current-status claim requiring the kind of record correction encountered in the earlier PR #6 review. 

## 6. Faithful preservation and operational scope

The preservation commit has exactly the workflow head as its sole parent. Comparing complete root entries and the complete changed `decisions/` subtree confirms that it retains every parent leaf and adds only:

```text
decisions/m0.1/validations/pr9-budget-profile-synthetic-validation.md
```

The addition is a regular `100644` file, **50,762 bytes**, blob:

```text
030b06028f50c544b6311dbd08973bc79988e804
```

No workflow, helper, protocol, existing decision, evidence, or archive content changes in that preservation commit. Its added path cannot match the workflow’s two operational-file trigger paths.     

The capture preserves the complete static-review prose, including its unfavorable resource trade-off and non-authority statements; the complete fallback authorization; decoded output; and retrieved job log. It distinguishes **Sarah as the stated reviewer, Greg’s supplied source text, and Miles as publisher/capture author**. It expressly declines to turn those attributions or hashes into cryptographic proof of human authority.  

The authorization copy retains its original prospective wording, while the enclosing record explains that the completed result resolves that former future state. That preserves chronology rather than rewriting authorization as retrospective approval.

PR #10 remains open, draft, and unmerged, explicitly labeled **“do not merge into main.”** Its retained operational tree is not the tested tooling candidate. Its preservation role must remain separate from accepting and integrating PR #9. 

## 7. Findings, limitations, and recommendation

### Findings

**No blocking defect or material record inconsistency was identified in the reviewed execution-evidence chain.** The remaining qualifications are evidence limits, not repair requirements:

- The test result is **externally executed and independently reconciled**, not personally executed by Sarah.
- The container settings and runtime readbacks establish this run’s configured conditions; they do not prove universal host containment.
- The mutable image tag was used only for acquisition, then resolved to and executed by recorded digest, as authorized.
- The local zero-test probe and original chat authorization remain attributed process records rather than independently observed local events.
- The successful synthetic suite does not exercise a real production inventory or establish that a stage approaching 100 billion logical units completes acceptably.

The prior static resource conclusion remains unchanged: this profile permits more work before numerical exhaustion, without improving the scanner algorithm or proving production feasibility. **The 0.277-second synthetic result must not be presented as a production runtime estimate.**

### Evidence boundary

I used read-only GitHub inspection, complete log retrieval, source-text examination, and reviewer-authored base64, hash, Git-tree, and set/count calculations. A supplemental raw-download attempt failed at DNS resolution; connector reads supplied the needed material, and no required evidence remained unavailable.

I did **not** import or execute repository modules, discover or run tests, invoke scanners/verifiers, run Rust, dispatch or rerun Actions, scan production inputs, or generate migration evidence. I did not resume PR #5 or PR #8.

### Final disposition

The synthetic-validation gate identified by the preceding static review is sufficiently evidenced for this exact subject:

```text
PR #9 head: 62a19baf0f67474f0c25c609f9a4300aa11e74d4
Tree:       27a18b261d8f5325c2414ad9e18193e91b870a37
Run:        40283940081, attempt 1
Job:        121443126469
```

**I recommend PR #9 for Greg’s separate acceptance and merge decision**, subject to the ordinary exact-head, target, and integration checks at that time. This does not recommend merging PR #10.

**Nothing was posted to GitHub.** No repository content, metadata, workflow, readiness state, approval, or merge was changed. This report grants no new execution, production scanning, evidence generation, PR #5/#8 work, M0.1 acceptance/completion, or M1/later-phase authority.

**Greg remains the sole acceptance and merge authority.**

**NO BLOCKING FINDINGS IDENTIFIED — EXECUTION EVIDENCE CONFIRMED; READY FOR GREG’S PR #9 ACCEPTANCE/MERGE DECISION.**