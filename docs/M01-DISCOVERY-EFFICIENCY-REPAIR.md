# Proposed M0.1 generator discovery-efficiency repair

Status: prepared for independent static review only. This is not accepted
tooling, an execution result, production evidence, an input acceptance, or M0.1
completion. Greg authorized this bounded repair in chat after the source-scale
blocker was reported. That permits preparation and a draft PR only; it is not an
executable approval stored in the repository.

## Exact starting points

| Item | Identity |
| --- | --- |
| Ledger repository | `gregkrsak/bowfin-migration-ledger` |
| Repair base / target | `main` at `edb0a11851cb1b51727c857d03c045ad1e7daa95` |
| Base tree | `633ab4de8c05f95a5d2672c15b40df2cd5689aff` |
| Prior accepted tooling head | `23bed495c73b600d0a849b3c336d08a5c6cdd1b1` |
| Prior accepted tooling tree | `c642dca4c4b8ae4e08f1250e1862bbe821c43b04` |
| Prior accepted protocol subtree | `d0e0c7419020415ddc7996631db616b2f73a25b3` |
| Baseline generator blob | `7d103aa4d61c42d089e991e25b6c3763cae08ffe` |
| Unchanged limits blob | `46f8c03290682d275e30c27e3f353ebfd3f291b9` |
| Compiler candidate | `gregkrsak/klyxr` at `609822762abd46c13ecd6187ccc8510695e52b2f` |
| Compiler candidate tree | `ebaf5e4b7b6a7a09acc693db52e3cdc5e0ec2239` |
| Parked, unaccepted PR #5 head | `8fef7a12cf89d5cdad9d03db187d6060e450bc1d` |

The current ledger base adds accepted closeout documentation to the prior
tooling integration. It does not imply acceptance of this changed generator or
of PR #5. A future accepted repair receives a new exact tooling binding.

## Static blocker and its evidence boundary

GitHub returned the complete 277-file compiler tree with `truncated: false`.
The preparer retrieved all 275 text blobs at the exact compiler commit and
recomputed their Git blob identities: zero mismatches. They contain 6,066,277
UTF-8 bytes and 6,064,042 Unicode characters. The two raster files were excluded
from this text arithmetic, not from the required source view or path discovery.
The thirteen PR #5 input/observation blobs also matched their Git identities.

The old generator charges the text character count once per file, then once
per mapping, while its KMP loop charges at least once per character per mapping.
For N text characters and M nonempty mappings, its raw-text work alone is at
least `(1 + 2*M) * N`. With PR #5's original 195 mappings:

`(1 + 2*195) * 6,064,042 = 2,371,040,422 > 2,000,000,000`.

This excludes path matching, structured traversal, physical-key construction,
classification, and other charges. It proves that the old complete discovery
cannot finish this exact input within the unchanged stage limit; an earlier
rejection would not make the input usable. The unfinished successor's provisional
201 mappings would have raised that floor to 2,443,808,926.

This is source inspection plus trusted standard-library byte/hash/arithmetic
work, not an executed generator failure. No accepted or proposed protocol code,
compiler code, governance code, archived tooling, or tests were run to establish
it. No production occurrence package or independent-audit result was generated.

## Bounded change

Only `generate.py` changes executable behavior. It builds a first-character
literal index once per discovery stage. Every source representation gets one
position-dispatch traversal; suffix comparisons occur only for literals whose
first character matches. Equal spellings share comparison work but keep every
mapping interpretation. Short/long overlaps and Unicode byte-coordinate
conversion remain explicit. The index references existing bounded strings and
does not allocate a trie node per input character.

Construction, dispatch, remaining-length checks, character comparisons, and
yielded bindings consume the same stage-local WorkBudget. Source hashing/decode
and offset/encoding work are precharged as documented in PROTOCOL.md section 14.
Physical-key construction, occurrence limits, collision detection, semantic
classification, exact selector populations, and canonical output ordering remain
unchanged. Discovery encounter order can change; canonical package row order
cannot. No limits, row/key format, classification rule, or scope is relaxed.

The auditor still uses its separate, unchanged per-family KMP implementation.
It imports no generator index or matching function. The verifier, shared library,
schema, limits, source-root restriction, authenticated exports, filesystem safety,
archive exclusion, C/E/D/P checks, and evidence/authority boundaries are unchanged.

## Authored controls, not reported test results

All 54 predecessor test methods are retained without modification. Six new
methods bring the authored total to 60. Existing `valid-case.json` and
`vectors.json` bytes remain unchanged; the mutation manifest is extended without
removing or changing any predecessor mutation/control entry.

The new `discovery-dispatch.json` fixture states:

- a 6,064,042-character, 195-mapping synthetic source with four fixed expected
  semantic/physical-key records, including the short spelling inside the longer
  crate name; the test requires an unchanged normative limit and a smaller
  40,000,000-unit discovery ceiling;
- a hidden Unicode filename and JSON key/value with five literal expected
  coordinate/key records, including distinct structured kinds at the same pointer;
- overlapping short/long Unicode literals and duplicate-spelling bindings; and
- independently selected suffixes and byte coordinates. Standalone json/hashlib
  generated the fixed hashes without importing candidate code.

Other controls exercise one-character literals, partial prefixes at EOF, empty
text/index, mapping-order invariance, exact emission-budget neighbors, precharge
before index/lookup/comparison/emission, source hashing, and raw/path offset-map
construction work, and dense-prefix no-match exhaustion.
They retain rejection rather than skipping work when a bucket is expensive.

Static validation is limited to Python AST parsing, unchanged-predecessor/body
comparison, JSON/manifest consistency, independent fixed-vector recomputation,
scope/blob checks, and manual source review. It is not test discovery by execution,
a self-test pass, compilation, or a runtime/performance result.

## Review and remaining gates

Sarah must independently review the exact new head/tree, the unchanged base,
matcher completeness, overlap/multiplicity, Unicode/JSON/path coordinates, charge
placement, failure paths, oracle vectors, unchanged predecessor tests, and the
separation from auditor logic. No favorable conclusion is prescribed.

First-character dispatch is not a universal linear-time guarantee. Dense shared
prefixes can still exhaust the unchanged work budget. The large synthetic source
targets a changed cost schedule, not preservation of all prior budget outcomes:
some dense-prefix inputs may exhaust sooner than under per-literal KMP. Its
successful completion must preserve all discovered meanings and coordinates.
The large synthetic source
targets the proven repeated-scan defect; it is not the production source, complete
input semantics, a full-stage budget proof for real inputs, a physical-memory
benchmark, or a wall-clock promise. Other independent stages may still reject a
future production candidate for their own limits or semantics.

After static review, Greg may separately authorize one bounded synthetic run at
the exact reviewed identities. Preparation alone permits no run. Any repair
changes those identities and requires renewed review. Production execution and
evidence generation remain ungranted. PR #5 and the unfinished successor inputs
stay untouched; a later input successor must bind whichever exact tooling is then
accepted. Greg alone accepts, changes readiness, or merges. M0.1 and M1 remain
unaccepted/unauthorized respectively.
