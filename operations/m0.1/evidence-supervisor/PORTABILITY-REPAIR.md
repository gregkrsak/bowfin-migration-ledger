# Runtime portability repair — preparation record

Prepared 2026-10-30 (America/Los_Angeles). Static preparation only.

## Authority and historical baseline

Greg asked for a concrete immutable containment/invocation plan for PR #18,
with no execution, dispatch, retry, acceptance, merge or M0.1 completion.
Investigation found that the reviewed harness bound an environment-specific
Codex Python path/hash without an identifiable matching OCI image. Miles stopped
before modifying that reviewed revision and recommended a narrow runtime-
portability repair. Greg then instructed: "Yes. Fix this. Begin. Thank you."
This records the bounded preparation context, not an executable approval.

The repaired parent is `e8889f9b310dd90888a329b3ab4acf8230c3e908`, tree
`7a53ab3e06f9f1e577570a657338eeb3a304f153`; its operational subtree is
`5d1ecdb90d1ea5f73c462152093b93b317ce240c`. Sarah's chat-delivered focused
review resolved T01/T02/T03 statically and retained X01 plus the R01 procfs
prerequisite. It did not report executed tests or a qualified environment.
This record does not pretend that review covers the successor.

## Actual repair

Two harness constants now bind a public official Linux/amd64 Python 3.12 image's
interpreter path and exact executable bytes. No configurable interpreter,
PATH-based fallback, environment override, or relaxed hash check was introduced.
The old Codex runtime is not copied, exported or repackaged.

`runtime-pin.json` content-addresses the complete image closure. The containment
directory adds a fixed-purpose external controller, benign qualification/startup
probe, explicit seccomp profile/license, three inert systemd units, and a closed
deployment manifest. `CONTAINED-RUN.md` specifies limits, qualification,
invocation, cleanup, host-trust boundaries and negative outcomes. No file under
`.github/workflows` is added and no systemd unit is installed.

The bootstrap gate starts no candidate test until actual same-container checks
pass. A separate systemd timer owns cleanup after loss of the primary controller;
the retained cgroup is checked for no live processes only after exact-container
removal fences delayed starts. Neither flags nor source review is represented
as observed containment enforcement.

## Static validation performed

- Compared the new harness with the exact GitHub parent blob
  `c97742413387b14c5fc7511dc37e9d977dabd178`. Its entire AST, after removing only
  the two runtime-constant assignments, is identical. All 22 test methods,
  fixture logic, expected results, imports and assertions are unchanged.
- The new harness is 29,296 bytes, Git blob
  `d5e58c4a71589478a4f1d3e2b7b5118e8872c9c2`, SHA-256
  `821af92e30133db5859c0be5b08004b7cf018d512b15f8514b96af60f24ab7e1`.
- The supervisor remains blob `96f220f4a0ef9bb47f2f4000cf7beca4371a214f`;
  the receipt schema remains blob `869526dee282462ce3dbdf3daf98f9a2722f4110`.
- Static registry/archive inspection verified the index/platform association,
  raw manifest/config hashes and sizes, all four compressed layer hashes/sizes,
  all four uncompressed diff-IDs, ordered path metadata and the final regular
  interpreter file. A second internal reviewer independently recomputed those
  bindings and the harness AST comparison. Image code was not executed.
- Internal source review pressured timer configuration, effective limits,
  startup races, source immutability, output caps and cleanup. This is Miles's
  internal QA, not Sarah's independent disposition or runtime evidence.
- Parsed all four Python sources as AST data only and all four JSON files with
  duplicate-key and non-finite-value rejection. Verified all ten deployment
  entries against their final byte lengths and SHA-256 digests. No candidate
  import, bytecode compilation, test, probe or controller invocation occurred.

The final publication report supplies the successor Git identities, complete
change set, syntax/data validation results and readback. Its identity is external
to these files to avoid self-reference. All original design/review records remain
unchanged and describe their historical revisions.

## Remaining gates

The controller, probe, image and changed harness require Sarah's exact-successor
static review. Runtime qualification remains unperformed: installed units,
actual resource enforcement, private procfs, startup release, ordinary cleanup,
and controller-loss deadline behavior require separately authorized observation.
Only afterward may Greg consider one exact bounded suite invocation. There is
no test-pass claim, host attestation or assurance of physical disk durability.

Run 01 remains indeterminate; PR #17 and all production evidence are untouched.
The accepted verifier, compiler, input/package/audit/export/observation/review
subtrees and current main are outside this repair. No production-map refresh or
replacement, acceptance, ready-state transition, merge, M0.1 completion or M1 is
authorized or performed. Greg remains the sole acceptance and merge authority.
