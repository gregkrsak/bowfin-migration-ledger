# M0.1 execution-supervisor repair — proposed, static only

## Purpose and present authority

Retain the actual termination result of one reviewed child invocation before a
chat/tool response can be lost. This is operational capture tooling, not a new
migration verifier, evidence architecture, acceptance service, or retry system.

Greg's preparation order on 2026-10-31 authorizes preparation and static review
of the bounded execution-supervisor repair and replacement-invocation design.
It authorizes **no execution, retry, acceptance, merge, or M0.1 completion**.
In particular, the synthetic tests in this directory have not been run under
this order. This document is a proposal, not an executable approval.

## Exact starting points

| Item | Identity |
| --- | --- |
| Ledger preparation base | `1f6216b16bf6fe737d1aad8a5eac043ed240cf7c` |
| Base tree | `c8aadb0545cab81a85525a397a351cf36fc9bf04` |
| Governing compiler contract commit | `609822762abd46c13ecd6187ccc8510695e52b2f` |
| Governing contract tree | `ebaf5e4b7b6a7a09acc693db52e3cdc5e0ec2239` |
| Contract path | `docs/migration/BOWFIN-NAME-MIGRATION-PLAN.md` |
| Contract blob | `03cd2c5b584a996ebfb873491f0d2888c984cfb9` |
| Accepted verifier tooling commit | `4020cb64c1119ccfb4a4bc77b3f39e8b698ba2f5` |
| Tooling root tree | `27a18b261d8f5325c2414ad9e18193e91b870a37` |
| `protocol/m0.1/v2` subtree | `cd514c89fda2d91318c7a63b8b737118141f7b2c` |
| Original subject H | `568047f573a8896462bacacb57af9ed7353b55ef` |
| Original subject tree | `0c564a9db13574442551170f241a64c3e5238c38` |
| Original invocation map commit M | `c882318def0c17a9bd11a96d28dbb68ff9067c54` |
| Original map tree | `a4351c6d685841209e54f50724076ee67f085d64` |
| Original map blob | `a2cdcf43d704442e6b27dd601ad2f8f628cfd1d9` |
| Original map SHA-256 | `301ed1b498b0d5cf1abd8ed8be15665f4c2e8f61f18aed0ee38f2d5af41b6a3d` |
| PR #17 preserved clarified head | `8c1f05932ee05ced58f1b9e7493bea6665a26d41` |
| PR #17 preserved clarified tree | `81a51e39eb21bfdfb42bef6996408fc91484944a` |

The source repository is `gregkrsak/klyxr`; the ledger is
`gregkrsak/bowfin-migration-ledger`. The map is under
`evidence/m0.1/d7aaf0ca79139b8ab3899aa5f5f6bf2092bdd598/reports/` as
`evidence-invocation-map.json`.

Sarah's [execution review](https://github.com/gregkrsak/bowfin-migration-ledger/pull/17#issuecomment-6535544448)
identified BML-E17R-01: the direct runner envelope was not retained. Empty
stdout/stderr and disappearance of a process cannot establish exit zero.
Her [clarification review](https://github.com/gregkrsak/bowfin-migration-ledger/pull/17#issuecomment-6536243362)
confirmed the append-only correction without resolving that missing result.
**Run 01 stays indeterminate.** A later successful run cannot retrospectively
repair its missing termination observation.

## Deliberately small change boundary

Only this new operational directory changes. The accepted protocol subtree,
compiler, compact inputs, packages, audits, exports, observations, reviews,
empty-review subtree, existing maps, Run 01 files, and clarification remain
unchanged. There is no workflow, service, dependency, plugin, or network client.
No archived code is imported or reused. Normal compiler operations never depend
on this supervisor.

The proposed source is Linux/POSIX CPython 3.12 standard-library code. The
future production map must pin the exact accepted supervisor and runtime,
including the runtime deployment's trusted standard-library environment.
A hash of the executable alone is not a complete runtime attestation.
Windows support and hostile-child sandboxing are out of scope.

The production supervisor must run as a standalone process with exclusive
ownership of its child reaping and default `SIGCHLD` disposition. It is not a
library to embed inside another event loop, child-reaping service, or traced
process. Nondefault `SIGCHLD` rejects before reservation; direct wait errors still
fail closed rather than relying on that precondition alone.

## Capture state machine

1. **Static preflight:** the operator checks complete identities, applicable
   review and owner authority, freshness, materialization, isolation, and limits.
   The supervisor additionally checks bounded map bytes, expected digest,
   duplicate-free JSON, its consumed field types, runtime/source digests, and
   physical paths. It does not replace the operator's complete preflight.
2. **Reserve:** create an exclusive new attempt directory and sync the parent;
   write and sync `intent.json` before the single spawn call. Existing attempt
   paths are never resumed, emptied, or reused. Reservation is conservative:
   even an ambiguous crash before spawn consumes the reserved attempt.
3. **Observe:** call `Popen` once with the literal argv, no shell, closed input,
   a cleared environment containing only `LANG=C`, `LC_ALL=C`, `TZ=UTC`, closed
   inherited descriptors, and a new process session. Capture both streams with
   bounded nonblocking reads. Obtain the child's raw status directly from
   `os.waitpid(pid, WNOHANG)` and decode only a returned status for that exact
   child. `ECHILD`/unavailable status is indeterminate. CPython's higher-level
   `Popen.poll()`/`wait()` fallback can substitute zero when status is unavailable;
   it is not used as execution evidence. Negative decoded values remain signals.
4. **Finish capture:** preserve intervention flags even if the child subsequently
   exits zero. Close and sync the saved streams and hash their exact retained
   bytes. A bounded prefix is never described as complete output.
5. **Publish locally:** write and sync a temporary receipt, link it to the final
   receipt without replacement, and sync the directory before removing the
   temporary name. A final receipt retains the reported child observation; it
   does not prove that the publisher's last `fsync` or own exit succeeded.
   Publication errors and leftover temporary state must be reported and examined;
   they never permit a restart.
6. **Retain remotely later:** read back and validate the actual capture set,
   then publish only files separately authorized by the later owner order.
   Git publication failure permits preservation/reconciliation of the same bytes,
   never another invocation. No such result publication is authorized now.

An attempt ID is a label, not a global distributed lock. The filesystem
reservation prevents reuse only in its exact capture parent. Operator control
must also prevent relaunch in a different directory, machine, or session.
Synthetic attempts use `M0.1-SYNTHETIC-NNN`; they are explicitly not evidence
invocations. The proposed production ID is `M0.1-EVIDENCE-02`.

## What a receipt establishes

It records direct child status, exact launch bytes/bindings, stream hashes,
interventions, and observation times. A pre-spawn timestamp is not the exact
kernel process-start time; status-observation time is not the exact death time.

`observed_exit_zero` means only that this supervisor observed its direct child
exit zero without an adverse capture condition. It is not, by itself, a verdict
that the correct evidence was verified. That stronger bounded statement also
requires the independently checked exact map, runtime, argv, materialized roots,
complete receipt/streams, and applicable preflight. A synthetic child's exit zero
can never establish production evidence validity.

Missing or malformed receipt, unknown termination status, mismatched retained
bytes, incomplete output, cancellation, timeout, output limit, failed cleanup,
or publication failure fails closed. Empty streams have no independent success
meaning. The supervisor's exit code and the child's exit code are distinct.

A receipt and digest retain content; they do not cryptographically attest that
the supervisor was honest. This proposal trusts the exact reviewed supervisor,
non-hostile accepted child, runtime, local filesystem, and enclosing execution
service. Same-UID file permissions are not a security boundary against a
malicious child or concurrent privileged actor.

### Required receipt readback

Read all four files as actual bytes, not prior chat output or claimed digests.
Reject unexpected files, symlinks, leftover `receipt.tmp`, malformed/duplicate
keys, nonfinite numbers, over-limit records or streams, and unknown schema fields.
Validate the receipt schema with format assertions, then independently compare:

- map digest/blob and externally corroborated containing commit/tree;
- exact attempt kind, subject, literal launch, runtime/supervisor and limit pins;
- intent SHA-256, its reserved-before-spawn state, non-reusability, and exact
  agreement of all shared fields with the receipt and the reviewed map;
- both saved stream lengths and SHA-256 values, EOF flags and intervention/error
  state; the receipt is not permitted to substitute counters for actual bytes;
- raw terminal `wait_status` decoded for POSIX: nonnegative returncode requires
  equal `exit_code` and null `signal`; negative returncode requires null
  `exit_code` and `signal == -returncode`; unavailable status requires raw status,
  returncode, exit code and signal all null;
- `observed_exit_zero` requires directly observed zero, complete captures, no
  intervention/error/cancellation, and genuine spawn/status-observation records.

Report any known publication error separately. A missing publisher-completion
envelope leaves its final sync/transport outcome unproven; it neither erases a
surviving directly recorded child status nor proves end-to-end publication
success. This distinction is the repair: lost chat output no longer necessarily
loses the child status, but absent child evidence is never reconstructed.
No readback outcome permits a retry or grants acceptance.

## Physical bounds and unavoidable limits

The implementation caps map bytes, argv count/length, child elapsed-time budget,
stream bytes and read chunks. Child timeout is at most 3,600 seconds; each saved
stream is at most 1 MiB, with at most 2 MiB saved across both. Cleanup has a
separate finite grace and reap budget. Exact constants and error behavior are
reviewed in source; changing them requires renewed review and identity binding.

These Python limits do not bound a kernel-stalled spawn, filesystem write,
`fsync`, or an uncatchable supervisor death. The future launch environment must
provide an outer whole-job deadline, memory/CPU/storage limits, no network or
credentials, read-only authenticated roots, protected runtime, and ownership of
all descendant cleanup. This source does not install that containment.
The final map must name the concrete mechanism and supported limits; an assertion
that containment exists is insufficient. Unknown platform capability blocks run.

Catchable cancellation triggers bounded cleanup. SIGKILL, host loss, or storage
loss can prevent a terminal receipt. In those cases reservation remains consumed
and the result is indeterminate. Process-group signaling is not used after the
direct child is reaped; inherited pipes without EOF remain an adverse capture
condition. Enclosing containment, not PID absence, establishes whole-job cleanup.

## Replacement invocation: a new, explicitly reviewed contract

The old map is not executable through this supervisor unchanged. Its
`process_replacement_required: true` and direct-redirection-only rules conflict
with a waiting parent and bounded pipe capture. A future replacement map must
explicitly supersede those launch mechanics for that single new attempt, while
preserving the accepted verifier's exact argv and all unchanged dependencies.

The replacement map is intentionally **not instantiated in this preparation**.
It will contain complete dependency/materialization bindings and the exact
`supervisor_execution` launch object described in the source. It will pin the
supervisor and schema to an already-created reviewed commit. A later owner order
will name the map's containing commit/tree/blob/SHA-256; these external labels
are passed to the supervisor and corroborated in preflight, not self-embedded.
This keeps supervisor -> map -> invocation result -> review/decision acyclic.

The map must explicitly fix:

- the exact subject and every C/B/T/I/S/H dependency, raw bytes, tree view and
  relevant blob; no mutable branch names or inferred equivalence;
- the complete unchanged verifier argv, except for a separately reviewed
  materialization relocation if required; no alternate mode or hidden command;
- supervisor/runtime closure and the exact launcher argv/environment/cwd;
- one fixed capture parent outside all authenticated roots, initially empty,
  with no symlink traversal or concurrent writers;
- genuine empty-review-directory materialization (Git checkout alone does not
  materialize the authenticated empty tree);
- concrete external isolation, resource limits, cleanup owner and deadline;
- complete static preflight comparisons, named invalidating events and freshness;
- exactly one reservation/spawn attempt and an explicit no-retry rule under
  every outcome, including infrastructure, capture, or publication failure;
- readback requirements and the complete new output/publication allowlist.

The proposed successful capture allowlist is **four files**: `intent.json`,
`stdout`, `stderr`, `receipt.json`, under one fresh attempt-specific path. The
final map must bind these literal paths. This is a deliberate change from Run 01's three-file publication
allowance, which grants no authority to publish new files. If no final receipt
exists, a later order must specify preservation of existing partial captures and
any `receipt.tmp` separately, without synthesizing a successful receipt.

### Freshness is a real gate, not a renamed run

The original map's source/governance eligibility deadline is
`2026-10-31T03:39:14Z`. Preparation does not extend that deadline or establish
absence of invalidating events. Evidence mode does not itself assess freshness.
The final replacement map cannot simply inherit a once-valid clearance.

If the existing observations no longer qualify, stop. Refresh/rebinding needs
separate authority and must follow contract sections 13.6 and 13.8. A reviewed
historical-structural-only scope would be a different explicit proposal, not a
silent relaxation here. This order grants neither refresh nor evidence mutation.

### No-retry cannot be bypassed by changing a label

The original one-run authority is exhausted. A future owner order must expressly
authorize one replacement attempt notwithstanding the prior prospective
no-further-invocation restriction, bind the reviewed new supervisor/map, and
leave Run 01 indeterminate. Merely saying "Run 02" supplies no such authority.
Neither this design nor favorable review authorizes that exception.

## Review and validation sequence

1. Independent static review of the whole proposed supervisor, receipt schema,
   synthetic test source and this replacement design. Internal Miles QA is not
   Sarah's independent review and is not acceptance.
2. If Greg separately authorizes it, execute one bounded synthetic test plan at
   exact reviewed identities, with distinct synthetic IDs and no production
   verifier, roots, observations, or evidence generation. Capture the harness's
   own actual status and finite limits; do not repeat the original evidence gap.
3. Resolve any findings before accepting/pinning operational tooling. Prepare
   and review the final replacement map only after its prerequisites and scope
   are settled. Existing freshness must be rechecked at the required checkpoints.
4. Greg may then separately decide whether to authorize a replacement production
   attempt and its publication. No step here grants the next one automatically.

The mandatory regression is a child killed by SIGKILL with two empty streams:
the only honest classification is signaled/adverse, never exit zero. Additional
tests cover nonzero exit, output bounds, timeout, cancellation, reservation,
spawn failure, malformed input, and capture/publication I/O errors. Static review
must distinguish implemented synthetic tests from host-failure scenarios that
need separately planned integration tests. None has been executed in this PR.

## API references and evidence limits

Python's [`subprocess` documentation](https://docs.python.org/3.12/library/subprocess.html)
defines direct return codes, POSIX signal representation, replacement
environments, pipe buffering, and the limit on interrupting initial creation.
[`os`](https://docs.python.org/3.12/library/os.html) documents file sync/link
primitives; [`signal`](https://docs.python.org/3.12/library/signal.html) documents
catchable handlers and their limits. These API references support implementation
choices; they do not certify the eventual host or storage durability.

**Current disposition: prepared for static review only. Run 01 indeterminate;
no replacement execution, test run, acceptance, readiness, merge, or M0.1 completion.**
