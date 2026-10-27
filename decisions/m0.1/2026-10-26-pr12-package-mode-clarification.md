# PR #12 package-mode clarification

**Record class:** Append-only execution-report clarification  
**Status:** Descriptive correction only; no acceptance or authority  
**Source URL:** https://github.com/gregkrsak/bowfin-migration-ledger/pull/12#issuecomment-6431452497  
**Stable comment ID:** `6431452497`  
**Published:** `2026-10-27T01:28:30Z`  
**Stated author and publisher:** Greg Krsak, published through the authenticated ChatGPT Codex GitHub connector  
**Capture method:** Complete GitHub issue-comment API readback  
**Captured body byte count:** `1650`  
**Captured body SHA-256:** `b454b898dbf39c3317b1ab7e8015cf9bbb811684cd2ab5f4a171bcd8ea6cae6d`  
**Corrected report:** https://github.com/gregkrsak/bowfin-migration-ledger/pull/12#issuecomment-6424692606  

## Exact subject

- Compiler candidate: `609822762abd46c13ecd6187ccc8510695e52b2f`
- Compiler tree: `ebaf5e4b7b6a7a09acc693db52e3cdc5e0ec2239`
- Ledger compact-input head: `90de48b66711ce48cdd5b3562536a12adc89734f`
- Ledger compact-input tree: `68d8dd84e9ba02dabf5b70e1143a02d1ff6196a1`
- Input-view tree: `e58803b562b8c5c5b1b9fe7b7beee14235520765`
- Accepted tooling integration: `4020cb64c1119ccfb4a4bc77b3f39e8b698ba2f5`
- Accepted tooling tree: `27a18b261d8f5325c2414ad9e18193e91b870a37`
- Accepted tooling subtree: `cd514c89fda2d91318c7a63b8b737118141f7b2c`

The copied body and digest preserve content; they do not independently authenticate human authority. Authority remains corroborated through the governed owner process. This record grants no execution, evidence acceptance, input acceptance, ready-state transition, merge, PR #5 disposition, M0.1 completion, M1, or later-phase permission.

## Complete published body

## BML-INP-09 — append-only package-mode clarification

Greg authorizes this clarification of the replacement bounded-execution report at comment 6424692606. The original report remains unchanged as the historical execution record.

The report's statement that the successful `verify.py package` invocation performed “semantic input binding” is broader than the accepted verifier source supports.

The precise result is:

- the generator, independent auditor, and package-mode verifier were reported to exit 0;
- package-mode verification checked the generated package's structural and key consistency, retained audit-policy constraints, authenticated source/input references, and exact generated-versus-audit occurrence-key reconciliation;
- the separate evidence-mode operation that calls `_validate_generated_meaning()` was **not** executed;
- therefore this run did **not** independently bind every generated row's semantic fields—such as mapping, rule, role, phase, support policy, and per-rule population—to the complete compact inputs; and
- no evidence-mode result may be inferred from the successful package-mode exit.

This corrects the description of the verification boundary. It does not alter the reported output bytes or hashes, erase the failed first attempt, invalidate the reported successful package-mode run, authorize another invocation, accept the compact inputs, establish M0.1 evidence, mark PR #12 ready, authorize merge, close PR #5, complete M0.1, or authorize M1 or later work.

Both prior execution authorizations remain exhausted. Preservation and any later semantic-evidence decision remain separately gated.
