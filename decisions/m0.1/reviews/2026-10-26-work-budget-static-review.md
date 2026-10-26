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