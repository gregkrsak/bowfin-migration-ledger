# Sarah — BML-EX01 corrective-supplement confirmation

**BML-EX01 is resolved. The corrective supplement supplies sufficient execution provenance and containment detail to remove the evidence blocker identified in my preceding report.**

**I recommend that this exact revision is ready for Greg’s separate protocol-acceptance and merge decision.** No remaining blocking finding was identified in this focused confirmation. The remaining limitations concern the strength of isolation and the scope of synthetic testing; they do not invalidate this run or justify claims of production or migration acceptance.

I did not rerun anything.

## 1. Exact identities and live state

| Item | Independently established value |
|---|---|
| Repository / PR | `gregkrsak/bowfin-migration-ledger` — PR #3 |
| Target branch | `main` |
| Candidate branch | `m01-v2-protocol-tooling` |
| **Reviewed head** | **`0b81e183df466890a779f1bbd777c6c864835a3b`** |
| **Reviewed tree** | **`c3b7438fbb20ee1debcc8e00490449975f9c2084`** |
| Sole parent | `7464c8358973ea99c9fbb2cdbee11e4094429abb` |
| Ledger `main` / accepted base | `4ccfb4d004773adacbbd36a8a8807fbc7583d54a` |
| Protocol-v2 subtree | `e0293933add0ac558e666da3aad02b77ac9ae969` |
| Original execution report | Comment `6402165361` |
| Corrective supplement and new run | Comment `6402498996` |

The live commit record confirms the head, tree, and sole parent. The final PR readback remains **open, draft, unmerged**, targeted to `main`, at the same reviewed head. Ledger `main` remains unchanged. There is no intervening source revision to invalidate the preceding static review.    

I refreshed and read the complete Sarah charter, blob **`4df5839f388b50b5689c101f20fc845fb157700c`**, repository guidance, relevant governing-contract requirements, and the protocol’s execution boundary. I read both execution reports, including the supplement’s complete retained transcript and failure disclosures.     

## 2. Twelve-file materialization manifest

**The supplement’s twelve paths and twelve Git blob identities exactly match the complete, non-truncated protocol tree returned by GitHub.** There are no missing, extra, or mismatched protocol files in that comparison.  

All paths below are relative to `protocol/m0.1/v2/`.

| File | Matching Git blob |
|---|---|
| `PROTOCOL.md` | `9f4f59f86e7dc7c598e7e91500a35cca589d9520` |
| `README.md` | `f31bc6115f0e703f7a816e85857e3009fe72796b` |
| `audit_scan.py` | `0b61f3543e13c00071e067cb31fd3223073ca574` |
| `generate.py` | `2199d25cf8c05e42e820150edc00a80c813039cc` |
| `limits.json` | `46f8c03290682d275e30c27e3f353ebfd3f291b9` |
| `protocol_lib.py` | `11c4e7f854c7bb86693e2df1edb88fb8a8cf55bf` |
| `schema.json` | `2eff3a0a0a5830fdfd542b62b92bf192a0563b5c` |
| `tests/fixtures/mutations.json` | `1f014c42dcea4ebdf143ef73cb0cbaeb2c625e1e` |
| `tests/fixtures/valid-case.json` | `a1cc67fbf970f745c5e2473d6dec9019bf7858b4` |
| `tests/fixtures/vectors.json` | `d7d024e2b6042d6b8d0a196bb0eda85542fb30e1` |
| `tests/test_protocol.py` | `7e348095fdc1c18e0de39ed0b80c0ef4a0bad66f` |
| `verify.py` | `4ef3b8a5a1ed1d1c303be35854830d3d56cf88c7` |

The supplement records zero local blob mismatches and identifies the materialized file ownership and permissions. My independent check establishes agreement between that manifest and the authoritative Git tree. I did **not** access the original temporary filesystem or personally repeat the executor’s local hashing. That remains externally recorded preflight evidence, now specific enough to audit. 

The root tree also remains unchanged, with no active workflow directory and the same preserved archive subtree. The archive was not part of the twelve-file materialization manifest. 

## 3. Corrections to the original report

### File count

The supplement explicitly corrects “17-file protocol subtree” to **twelve regular protocol files**. It explains seventeen as the count of the local ledger working representation, rather than the protocol-v2 subtree. The authoritative tree independently confirms twelve. This resolves the original ambiguity without silently rewriting the earlier claim.   

### Interpreter version

The supplement withdraws **Python 3.12.14** as reliable provenance for the first execution: that version came from the unrestricted preflight shell, while the stripped `PATH` would have selected the system interpreter. For the new run, the record identifies an explicit executable and captures its version:

```text
CHILD_INTERPRETER=/usr/bin/python3.12
Python 3.12.3
TEST_COMMAND=/usr/bin/python3.12 -I protocol/m0.1/v2/tests/test_protocol.py
```

This removes the earlier PATH-dependent interpreter ambiguity. Python 3.12.3 is within the protocol’s specified CPython 3.12.x runtime family.  

The explanation of the first run’s interpreter is a reported reconstruction, not a newly observed first-run measurement. **My favorable recommendation relies on the new explicit-interpreter transcript**, not on retroactively treating the original version claim as verified. The interpreter path and version are recorded; a cryptographic identity of the interpreter binary or entire host image is not.

The original functional result remains historical, while its deficient provenance summary is expressly superseded for acceptance-evidence purposes. That is an appropriate correction. 

## 4. Launcher and exit-status handling

The recorded execution structure is:

```text
timeout 120s
  → env -i with an explicit allowlist
    → prlimit with explicit soft:hard limits
      → /bin/sh for identity/environment/limit readback
        → exec /usr/bin/python3.12 -I .../tests/test_protocol.py
```

Setup used `set -euo pipefail`. The outer shell reportedly disabled immediate exit only around the launcher to capture `$?`, print `LAUNCH_EXIT`, and return that same status. The retained transcript shows the test result followed by `LAUNCH_EXIT=0`, rather than relying on the exit status of a later successful print command. 

This structure is consistent with fail-closed launch and status propagation. Upstream `prlimit` applies limits before executing the requested command and terminates on a limit-setting error. The supplied successful-run readback additionally shows that the requested values were present before the test invocation. [GitHub](https://raw.githubusercontent.com/util-linux/util-linux/master/sys-utils/prlimit.c) 

The inner shell body is summarized rather than preserved as a byte-for-byte launcher script. Nevertheless, the command structure, explicit executable, working directory, environment, effective-limit readback, complete test output, and recorded exit propagation now provide the equivalent execution transcript missing from the original report. I do not claim to have fault-injected the launcher or audited its installed utility binaries.

Python’s `-I` supplies the protocol-required import/environment isolation; it does not create filesystem or network confinement. [Python documentation](https://docs.python.org/3.12/using/cmdline.html)

## 5. Requested versus recorded effective limits

All six requested soft/hard resource settings match the retained `/proc/self/limits` readback. The separate wall-clock wrapper is also explicit. 

| Resource | Requested | Recorded effective setting |
|---|---:|---:|
| CPU time | `60:60` seconds | 60 seconds soft / 60 seconds hard |
| Address space | `805306368:805306368` bytes | 768 MiB soft / hard |
| File size | `67108864:67108864` bytes | 64 MiB soft / hard |
| Open descriptors | `128:128` | 128 soft / hard |
| Processes | `64:64` | 64 soft / hard |
| Core-file size | `0:0` bytes | 0 soft / hard |
| Wall-clock supervision | `timeout 120s` | Explicit launcher setting; the run completed before it expired |

These are now concrete settings, not merely a statement that “limits were applied.” They are not evidence that the suite exercised every external cap.

Two qualifications must remain attached:

**Process limit and privilege.** The recorded process limit is 64, but the child reports UID 0. Linux exempts real UID 0 and certain privileged processes from `RLIMIT_NPROC` enforcement. The transcript does not establish the namespace/capability facts needed to treat this as a proven 64-process containment ceiling. I credit it as a configured value, not a demonstrated fork barrier. File-size limits are also per-file bounds, not an aggregate workspace quota. [man7.org](https://www.man7.org/linux/man-pages/man2/getrlimit.2.html?utm_source=chatgpt.com)

**Timeout strength.** The displayed command uses the default termination signal and does not specify a later `--kill-after` escalation. It should not be described as an unconditional SIGKILL-enforced 120-second ceiling against code that ignores termination. The recorded run completed normally, so the timeout was not exercised. [GNU](https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html?utm_source=chatgpt.com)

These are **non-blocking qualifications for this exact, previously reviewed synthetic workload**, which has no identified subprocess or network-client path. They would need renewed consideration for a different or hostile workload; this report does not endorse the launcher as a general-purpose sandbox.

## 6. Environment and source protection

### Observed environment

The supplied allowlist contains six names:

```text
PATH=/usr/bin:/bin
LANG=C.UTF-8
LC_ALL=C.UTF-8
TZ=UTC
TMPDIR=/tmp/bowfin-m01v2-evidence.qwn3NP/tmp
RUN_REPO=/tmp/bowfin-m01v2-evidence.qwn3NP/repo
```

The recorded shell environment additionally contains:

```text
PWD=/tmp/bowfin-m01v2-evidence.qwn3NP/repo
OLDPWD=/workspace/scratch/2debe97770c0
```

The supplement explicitly acknowledges those additions. Thus “stripped environment” is accurate; “literally only the six supplied variables” would not be. No credential variable appears in the recorded environment. This does not establish the absence of credentials anywhere on the host filesystem or in every possible inherited resource. 

The recorded working directory and `TMPDIR` separate the copied protocol source from the writable synthetic workspace. That is consistent with the reviewed test harness’s use of `TemporaryDirectory`.  

### Permission-based protection

The materialized files are recorded as root-owned mode `0444`, with directories `0555`; the child is recorded as UID/GID 0. The supplement explicitly says this was **not a read-only mount** and does not claim an absolute barrier against a malicious root process. 

That is the necessary distinction. The permissions document the intended protection and reduce accidental writes, but they do not prove that source modification was impossible. The Git blob identities establish the declared source bytes; local permissions are a separate execution property.

No source-write regression was identified in this focused evidence review. I do not upgrade that conclusion into proof that every directory remained byte-for-byte untouched throughout execution.

## 7. Complete test output and repaired controls

The retained transcript contains **forty distinct named test-result lines**, each ending in `ok`, followed by:

```text
Ran 40 tests in 0.295s

OK
LAUNCH_EXIT=0
```

It records the run beginning at **October 25, 2026, 20:02:21 UTC** and ending at **20:02:22 UTC**. No failure, error, skip, or timeout is shown. These are the new run’s values; they should not be combined with the first report’s `0.313s` result or resource-timing line. 

The named successful methods include the controls examined in the preceding static reviews: compiler intermediate-content restrictions and decision preservation; authenticated C/E/D/P and index binding; six-occurrence identity; strict Boolean substitutions; missing recovery objects; opaque symlink treatment; and the wrong-kind-after-prior-visit graph. The exact test-suite blob remains unchanged.  

This moves the evidence beyond a bare “40 passed” summary: the individual method outcomes are now inspectable and correspond to the reviewed suite. It does not erase the earlier distinction between helper-level controls and full binding-entry-point controls.

My evidence classification is **externally executed, with a complete published transcript independently inspected and matched to the reviewed revision**. It is not personally executed testing, cryptographic attestation of the host, proof of exhaustive coverage, or a production-scale validation.

## 8. Pre-Python failures and evidence-controller failure

The supplement discloses four unsuccessful preparations, distinguished from candidate execution:

| Event | Disclosed evidence | Assessment |
|---|---|---|
| Original timing-wrapper attempt | Exit 127; `/usr/bin/time: No such file or directory` | Harness launch failure, not a protocol-test failure. |
| Original Bubblewrap attempt | Exit 1; `Creating new namespace failed: Operation not permitted` | Containment setup failure before the intended Python child. |
| New ownership-separation preflight | `chown` to UID 65534 failed with `Invalid argument`; the report attributes this to the managed UID/GID mapping | Failed setup for a stronger ownership boundary; the successful run does not claim that separation. |
| Evidence-controller manifest parsing | The controller rejected its own emitted line before launcher invocation; a fresh materialization was created and verified | Evidence-preparation failure, not candidate validation evidence. |

The first two now have explicit statuses and diagnostics. The latter two are described without a complete controller traceback or numeric exit status; I do not invent those missing details or independently certify the reported UID-mapping explanation. 

Their classification is consistent with the described ordering and fail-closed setup. None is counted as a passing candidate run. The supplement states **one candidate execution in this newly authorized rerun**, distinct from the earlier successful run and the failed preparations. The subsequent complete transcript and fresh manifest are sufficient to assess that new execution without treating the failed preparations as evidence of candidate correctness. 

## 9. Network namespace and remaining limitations

**The unavailable network namespace remains non-blocking for this exact reviewed workload.**

The supplement preserves the limitation rather than claiming successful network isolation. The relevant basis is the unchanged, reviewed local workload; synthetic inputs; stripped environment; and reported managed outbound restrictions. The protocol requires reviewed isolated execution but does not mandate Bubblewrap or a particular network-namespace mechanism.  

The resulting conclusion is deliberately narrower than “networking was impossible.” Managed-host restrictions were not independently probed during this review, and environment stripping does not itself disable networking. No syscall-level network-denial proof is supplied or required for this confirmation.

Other retained limits are likewise non-blocking here:

- This was one synthetic run on the recorded interpreter, not cross-platform or production-input validation.
- The transcript and local preflight are externally recorded evidence, not independently observed host execution.
- Permission modes, root execution, the configured process limit, and TERM-based timeout do not form a hostile-code sandbox.
- Passing controls do not authenticate human decisions, independently approve compiler-change paths, establish production occurrence completeness, or prove universal correctness.

The governing contract continues to separate tooling acceptance from production-input authorization, evidence acceptance, M0.1 completion, and M1 authorization. 

## 10. BML-EX01 disposition and recommendation

| BML-EX01 deficiency | Corrective disposition |
|---|---|
| Ambiguous seventeen-versus-twelve file claim | **Resolved:** explicit twelve-file manifest matches the authoritative tree. |
| Unreliable interpreter provenance | **Resolved for the new run:** absolute interpreter path and Python 3.12.3 readback; original claim expressly superseded. |
| Unspecified resource caps | **Resolved:** requested values and matching effective-limit readback are retained. |
| Insufficient launcher/status evidence | **Resolved:** launcher structure, explicit invocation, complete output, and status propagation are recorded. |
| Unclear environment and source protection | **Resolved:** actual environment, ownership, modes, UID, and permission-only limitations are disclosed. |
| Missing full test output | **Resolved:** forty named `ok` results, summary, and `LAUNCH_EXIT=0` are retained. |
| Inadequate failed-attempt disclosure | **Resolved sufficiently for this run:** all four preparation failures are separated from candidate execution, with the residual historical-detail limits stated above. |

**No remaining blocking finding or evidence regression was identified.** The original deficiency was real; the new authorized run and corrective record resolve it rather than making the original report retrospectively sufficient.

My recommendation applies only to:

```text
Head: 0b81e183df466890a779f1bbd777c6c864835a3b
Tree: c3b7438fbb20ee1debcc8e00490449975f9c2084
Corrective execution record: issuecomment-6402498996
```

**This exact revision is ready for Greg’s separate protocol-acceptance and merge decision**, subject to the ordinary exact-head, target, and integration checks at the time of that decision. This report does not itself accept the protocol, authorize merge or another execution, permit production inputs or evidence generation, accept M0.1, or authorize M1.

**I posted nothing to GitHub.** I did not modify either repository, rerun tooling or tests, start workflows, change PR state, approve, or merge. **Greg remains the sole merge authority.**

**NO BLOCKING FINDINGS IDENTIFIED — BML-EX01 RESOLVED.**