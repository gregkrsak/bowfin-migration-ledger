# C01-C03 terminal-disposition repair — static preparation

Prepared 2026-10-31 (America/Los_Angeles). Proposed source only; not executed.

## Authority and exact baseline

Greg authorized a focused repair after Sarah's chat-delivered independent review
of PR #18, head `16110b5a399c678b64669cd7f2b806e59bc65750`, tree
`cf3a1537575d219f69307d6290cd5d6574a5e0ba`, operational subtree
`577e4073968ca6b6eb57bc04e5d2c0c9f09345b6`. The review's disposition was
STATIC REPAIR REQUIRED, with C01 blocking, C02 minor, and C03 a transport
observation. This record summarizes repair construction; it is not a verbatim
copy of Sarah's report, a claim of her successor review, or an executable grant.

The report's malformed protocol-tree token in Section 1 is not adopted. Its
Section 2 and the source tree agree on the correct unchanged accepted identity:
`cd514c89fda2d91318c7a63b8b737118141f7b2c`.

## C01: explicit provisional/result and terminal separation

The old `finally` path stopped only the timer, checked for a marker, and could
publish a favorable classification before a queued deadline service wrote its
marker. This was a real source-level race, not a failed runtime test.

The repaired controller always publishes `result.json` with classification
`provisional`. Its candidate observation is data, not terminal disposition.
The sole controller favorable terminal class is
`watchdog_quiescent_pending_independent_review` in a separate `terminal.json`,
which binds the provisional result SHA-256 and deployment-plan identity.

The primary controller and deadline service share a root-owned, precreated,
zero-byte `terminal.lock`, with five-second nonblocking acquisition bounds and
kernel release on process death. No path unlinks or replaces it. The deadline
service records activation before lock acquisition, claims only an adverse
terminal record, and attempts cleanup even after lock or marker failure.

The favorable-controller sequence is:

1. Establish complete workload cleanup and retain the provisional result.
2. Hold the shared terminal lock; reject any prior terminal disposition.
3. Check the original armed deadline against the active, untriggered timer.
4. Synchronously stop the timer before the original monotonic earliest expiry.
5. Separately stop/drain the deadline service.
6. Require both units inactive, no queued/running jobs, service dead, empty
   observed trigger/activation history and no adverse deadline marker.
7. Recheck original absolute expiry, retain exact readbacks/checkpoint times,
   and create the terminal record exclusively with the bound result digest.

Stopping the timer alone is not the fence. The service drain and original
absolute pre-expiry bound are indispensable. Unit garbage collection may reset
history; a zero after reload cannot rehabilitate an elapsed deadline. Both
systemd and the controller use the same host `CLOCK_MONOTONIC`, with
`WakeSystem=false` verified. No privileged concurrent starts, reloads, timer
resets/restarts, or host/clock replacement are permitted in this dedicated job.

### Adversarial schedules and expected source-level outcomes

| Schedule | Required outcome |
| --- | --- |
| Timer has fired, service queued, marker not yet written | Trigger history or elapsed original deadline rejects; no favorable seal |
| History is later zeroed by unit unloading | Original monotonic deadline still rejects late completion |
| Timer stop or service drain/readback fails | Indeterminate terminal; no favorable evidence |
| Deadline service owns terminal first | Controller cannot replace the adverse disposition |
| Controller owns lock and stalls past expiry | Absolute-time check rejects; service lock timeout does not suppress cleanup |
| Controller dies before sealing | Missing/partial terminal is not favorable evidence; watchdog remains responsible unless already safely drained |
| Controller dies after complete favorable seal | Timer already stopped before expiry and service drained; no remaining automatic activation source under exclusive host control |
| Unexpected adverse record appears beside a favorable record | Whole-set reconciliation rejects; never latest-record-wins |

The existing cleanup helper retains its thirty-second loop deadline plus bounded
trusted-tool calls; it is not represented as an exact thirty-second wall-clock
ceiling. The independent service's reviewed 45-second runtime/five-second stop
timeout and the final platform ceiling remain separately qualified limits.

## C02: finite JSON floats, including exponent overflow

`decode()` now supplies a dedicated `parse_float`: at most 128 token characters,
ordinary float conversion, and explicit `math.isfinite` rejection. Duplicate
keys and nonfinite literals remain rejected. Overflow such as `1e999` and
`-1e999` can no longer become nonfinite data. Finite underflow to zero is allowed;
the manifest's independent exact-type/range checks remain unchanged.

## C03: explicit stdin binding and harmless transport qualification

Created and live configuration now requires `AttachStdin` and `StdinOnce` true,
in addition to `OpenStdin=true` and `Tty=false`. Both benign qualification modes
use exactly the suite's ready/`GO\n`/EOF transport. The probe replaces stdin
with `/dev/null`, emits a fixed release acknowledgment, and only then enters
either its harmless qualification child/session path or its suite-only exec.

The controller retains `release_confirmed` and requires it for the ordinary
qualification or suite candidate-success classification. Bounded startup-marker
capture continues after release so acknowledgment and probe-ready markers remain
observable. The qualification gate does not execute the suite, add a mode, or
authorize a later suite invocation.

## Controls, preservation, and remaining gates

`test_containment.py` contains 30 separately authored, unexecuted regression methods
for finite-number parsing, stop/drain ordering, adverse manager states/timing,
provisional-result binding, terminal precedence, deadline arbitration failures,
stdin configuration and qualification-versus-suite separation. Every external
systemd/Docker boundary in those controls is mocked. These are test source, not
executed evidence, and are not deployed in the ten-file workload materialization.
Any later execution requires its own exact review/authority and bounded plan.

The original supervisor, receipt schema, 22-method harness, runtime closure,
seccomp profile/license, three units, accepted protocol and all production
evidence remain unchanged. Only controller/probe behavior, their manifest
entries, the current run contract and new repair/control sources change.

Preparation validation is AST/data parsing, exact scope/hash correspondence and
internal source-level adversarial analysis only. Final hashes, containing commit,
tree and publication readback are supplied externally in the PR report to avoid
self-reference. No candidate code was imported, executed or compiled; no test,
container, workflow or unit was run, installed or dispatched. No production
refresh, retry, acceptance, ready-state transition, merge or M0.1 completion
occurred. Run 01 remains indeterminate. PR #17 remains separate and untouched.

Five Python sources were parsed as AST data and four JSON files as strict data;
all ten deployment-manifest byte counts/digests matched. The unchanged supervisor
harness still has exactly 22 methods. Those counts describe source, not passes.
Internal review independently examined the actual terminal protocol, absolute
deadline fence, garbage-collection limitation, lock-failure cleanup path and
universal release transport; no concrete new blocker was identified in that
internal source review. Sarah's successor disposition remains pending.

This successor still requires Sarah's independent static review. A favorable
review would permit Greg to consider a separate two-case qualification order,
not execution now or automatic promotion. No static analysis can promise all
future defects are impossible. Greg remains the sole acceptance/merge authority.
