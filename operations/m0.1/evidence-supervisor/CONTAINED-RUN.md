# PR #18 portable synthetic run contract — static proposal

Status: prepared for independent static review, **not installed, qualified, or
authorized to execute**. This document replaces no historical record. Its
subject is the successor to reviewed head
`16110b5a399c678b64669cd7f2b806e59bc65750`, tree
`cf3a1537575d219f69307d6290cd5d6574a5e0ba`. The containing successor commit/tree
and the invocation-plan blob/SHA-256 are supplied externally in the PR report
and later review/owner instruction; they are not circularly embedded here.

## 1. Narrow repair and authority

Greg authorized the static C01-C03 repair after Sarah's review of the runtime-
portability/containment proposal. This successor changes only the controller,
probe, their deployment hashes, this contract, and new repair/control sources.
The earlier portability revision changed the synthetic harness's interpreter
path and executable SHA-256; that harness is unchanged in this repair.
The supervisor, receipt schema, all 22 test methods,
fixture logic, expected outputs, assertions, timeout tests, and negative cases
are preserved. There is no environment-variable override or fallback runtime.

The new controller is separate operational containment, not a second migration
verifier or an acceptance service. Its qualification probe is benign operational
code, not an extra supervisor test. Neither is executed during preparation.
No active workflow is added. The inert systemd units are not installed or enabled.

This plan is **synthetic only**. No compiler roots, accepted verifier, generated
package, audit, observation, archive, empty-review subtree, or production map is
mounted or invoked. Run 01 remains indeterminate. No existing invocation
authorization is reusable, and no replacement evidence invocation is instantiated.

## 2. Immutable workload runtime

| Binding | Selected value |
| --- | --- |
| Image platform | `linux/amd64` |
| Image | `docker.io/library/python@sha256:2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301` |
| Image config | `sha256:9cb180cb36bd45dc786105b834d3cb5f3b1d69a6a63c79ca10fc64f108aa649a` |
| Interpreter | `/usr/local/bin/python3.12` |
| Interpreter SHA-256 | `4dbf3143240288fb2170257ffaa7bd030cdda5d2703d1f5f30b627042267e2e3` |
| Interpreter bytes / mode | 14,480 / regular `0755` |
| Discovery tag, never used to launch | `3.12.12-slim-bookworm` |

`runtime-pin.json` retains manifest/config/layer descriptors, uncompressed
diff-IDs, origin and inspection limitations. Anonymous registry retrieval and
static archive reading verified all four compressed layer hashes and lengths,
all four uncompressed hashes, and the final interpreter member and directory
ancestors. No image code ran. The entire image root filesystem—not only its
small interpreter executable—is transitively bound by the platform manifest.
No layer payload is committed to the ledger.

This is content identity, not signature attestation, a vulnerability clearance,
a reproducible-build proof, or host-kernel identity. A security concern in this
fixed image requires a new reviewed pin, never a silent tag refresh. No apt,
pip, package installation, image build, extra runtime bind mount, or network
dependency is allowed inside the workload. Existing image defaults are bypassed
using `/usr/bin/env -i` and a literal interpreter command.

## 3. Concrete platform, trusted host, and materialization

The selected future platform is a fresh GitHub-hosted `ubuntu-24.04` x86-64 VM,
one VM per qualification or suite invocation. This label is not an immutable
VM-image identity. The workload userland and operational sources are pinned;
the GitHub platform, kernel, systemd, Docker/containerd/runc, and host Python are
trusted external enforcement components and must be recorded and qualified.
Do not describe this as complete host attestation.

Before candidate execution, a separately authorized operator must record the
job URL/run ID/attempt, runner image version, kernel, boot ID, host binary hashes
and versions, Docker server version/configuration, systemd version, cgroup/mount
topology, exact installed unit bytes, and effective container configuration.
Require cgroup v2, Docker's systemd cgroup driver, usable CPU/memory/PID
controllers and `cgroup.kill`. Reject rootless Docker, remote daemons, mixed
cgroup modes, unavailable controls, or unknown topology. Do not repair the
runner or install a new container engine inside this contract.

Network-enabled image and source acquisition occurs **before** the workload,
by the trusted host. A future Actions workflow must be separately prepared and
reviewed; it may not run on push/PR events as a side effect of this preparation.
Its permissions are at most `contents: read`, without write, merge, release,
OIDC or secret access; it cannot publish acceptance or automatically retry.
Any actions it uses must be commit-pinned. A 20-minute job timeout is a final
platform ceiling, not evidence that a Docker cgroup was cleaned up.

Materialize only the closed file list in `containment/invocation.json` plus
that file itself under `/var/tmp/bowfin-pr18/source`. Confirm containing Git
commit/tree and each blob against the independent review and owner instruction;
then compare every deployed path, byte length, SHA-256 and file type. Reject
extra/missing files, symlinks, path traversal and mode mismatches. Paths must
have root-owned, non-group/world-writable directory ancestors. Source files
are root-owned, mode 0644; directories 0755. No repository hooks, Git filters,
checkout-time code or archived payload is used. Source remains immutable for
the invocation; no concurrent writers are permitted.

The dedicated timer and service are exclusively controlled by this attempt.
No privileged concurrent starts, reloads, timer resets/restarts, daemon reexec,
clock-namespace changes, or unit-file modifications are permitted. The same-host
Linux `CLOCK_MONOTONIC` domain binds the recorded expiry and controller checks.
Unknown or changed host-manager state blocks a favorable disposition.

Install only the three reviewed units under `/run/systemd/system/` (ephemeral
VM only), byte-for-byte, root-owned and not writable by the workload. The
controller checks those copies. The operator's independently supplied SHA-256
of `invocation.json` is mandatory. It binds all deployed code/policy/unit files;
the plan does not try to contain its own hash. This descriptive binding is not
an executable approval. Every invocation still requires Greg's separate order.

## 4. Fixed bounds and isolation

| Surface | Fixed requirement |
| --- | --- |
| Workload cgroup parent | `/sys/fs/cgroup/bowfinpr18.slice`, retained until cleanup readback |
| CPU | 2 cores maximum rate; parent and container limits |
| Memory | 512 MiB maximum, including charged tmpfs memory |
| Swap | 0; Docker memory-swap equals memory, parent swap max 0 |
| PIDs/threads | 64 maximum |
| Scratch `/tmp` | 64 MiB / 4,096 inodes; `nosuid,nodev,noexec` |
| `/dev/shm` | 1 MiB |
| Main workload deadline | 900 seconds, bounded by controller |
| Independent deadline | systemd timer 960 seconds after activation; 1-second accuracy |
| Deadline cleanup service | 45-second runtime, 5-second stop timeout, no restart |
| stdout and stderr | At most 4 MiB retained each, external to container |
| Candidate identity | UID/GID 65532, all capabilities dropped, no-new-privileges |
| Network | `none`; isolated IPv4 loopback is explicitly permitted, no external interface |
| Source/root | read-only source bind and container root; no host evidence/credentials/socket mounts |
| Process namespaces | private PID, mount, IPC, network and cgroup views; no host namespace modes |
| Docker logging/restart | log driver `none`; no restart; no automatic removal |

`containment/controller.py` fixes the Docker argv, limits, paths, result handling
and cleanup. `containment/invocation.json` does not allow arbitrary commands or
configurable limits. `containment/seccomp.json` is the retained Moby profile at
commit `4b8214fc4971e06172938a1f1554ccff6647ee80`, original blob
`6e5e47e242892aaa290f916ba1045f9213ef0b84`; its Apache-2.0 license is retained.
The local JSON representation adds one final LF to the 17,867-byte upstream
body; its 17,868 bytes have SHA-256
`514c38e72edc5363e87287ea87212211172c6c3251a974ca21ebfd05a56c7f5d`.
This is a recorded representation change, not an exact-byte upstream copy.
Actual profile interpretation is a runtime qualification obligation, not proved
by the presence of a flag. No unconfined seccomp fallback is permitted.

Do not claim `/tmp` is the only writable kernel interface: private procfs,
`/dev`, and bounded `/dev/shm` also exist. They must not expose host processes,
devices, credentials or management sockets. Procfs must expose the current
process's file/directory descriptor readlinks. `noexec` scratch prevents native
execution from that mount, not interpretation of Python data/code.

The budgets are selected finite ceilings, not measured adequacy claims. A budget
failure is adverse evidence; no automatic increase or rerun follows. A systemd
deadline is independent of the controller process, but not immune to host loss,
kernel stalls or scheduling failure. Those cases remain indeterminate.

## 5. Qualification before the suite

After independent static review, Greg may separately authorize a finite
qualification campaign. It must name exactly the reviewed controller, probe,
plan, units and image, and use fresh VMs/reservations for the following two
distinct cases. They are not supervisor-suite invocations:

1. **Ordinary containment:** invoke controller mode `qualify`. The benign probe
   checks interpreter identity, effective UID/capabilities/no-new-privileges,
   seccomp, loopback-only networking, read-only source/root and usable private
   `/proc/self/fd` file/directory links. It starts a separately-sessioned child.
   The host sends exactly `GO\n` followed by EOF through the same gate used by
   suite mode. The probe must acknowledge `BOWFIN_PR18_RELEASE_CONFIRMED` before
   its harmless child/session path; it never executes the suite in this mode.
   Created and live Docker configuration must explicitly set `AttachStdin`,
   `OpenStdin`, and `StdinOnce` true and `Tty` false. The host confirms containment
   and tests whole-job cleanup. Compare effective
   cgroup, namespaces, mount flags/quotas and Docker settings against this plan;
   a success message from the probe alone is insufficient.
2. **Independent deadline:** on another fresh VM, invoke controller mode
   `qualify-watchdog`. After retaining proof of the probe and separately-sessioned
   child's cgroup membership, this mode deliberately kills its own primary
   controller with SIGKILL. It leaves the already-armed systemd timer running. Require the
   independent service's termination/removal and retained-parent empty readback.
   Killing the controller is part of this separately authorized qualification,
   not permission to interrupt a production evidence job.

Both qualification modes use that exact release/EOF transport. A stalled EOF,
missing acknowledgment or wrong stdin configuration fails qualification before
any suite is authorized; no extra mode or implicit retry is introduced.

The intended probe remains alive until externally killed; it is not expected
to exit zero. Qualification success means the stated boundaries were observed,
not that candidate tests passed. If controller-loss cleanup, a usable procfs
view (BML-SUP-R01), any limit, or any evidence check cannot be established, stop
before the suite. Qualification output cannot automatically authorize a suite.

Immediately before a separately authorized suite invocation, recheck effective
configuration, source/image/plan identities and platform compatibility. A fresh
VM does not inherit another VM's configured state merely because its label
matches. Reconcile current host evidence against the qualification profile;
unexplained material differences require review, not an informal exemption.
The same-container benign bootstrap gate also repeats the applicable private
runtime/procfs/identity checks and waits while the external controller checks
the actual leaf cgroup limits and namespace separation. Only then may the host
send its literal release message. This closes the gap between configuring a
fresh VM and observing the actual container that will run the suite.

## 6. Exact invocation and no-retry meaning

The future owner instruction supplies the successor commit/tree, invocation-plan
blob and SHA-256, and the closed result-publication allowance. The host command
is `/usr/bin/python3 -I /var/tmp/bowfin-pr18/source/containment/controller.py`
followed by `suite --plan-sha256` and that independently supplied digest.
`qualify` and `qualify-watchdog` are distinct modes with distinct authority.
`deadline` is called only
by the installed independent cleanup service, not a suite-launch alias.

The container entrypoint is `/usr/bin/env`; it initially invokes the reviewed
benign probe in suite-gate mode, not the tests. After live checks and the exact
host release message, the probe closes/replaces stdin with `/dev/null` and
replaces itself with the following literal test invocation under the cleared
three-variable environment:

```
/usr/local/bin/python3.12 -I -B /reviewed/test_supervisor.py -v
```

The suite starts exactly once with stdin attached to `/dev/null` and cwd `/tmp`.
Container stdin is used only for the bounded startup handshake; it is not an
interactive shell, TTY, or input channel to the tests. The suite has 22
methods, including parameterized cases that legitimately start multiple
synthetic subprocesses. One suite invocation is not one fixture subprocess.
Existing test alarms and supervisor timeouts remain unchanged; neither is the
whole-job safety boundary. No test discovery outside this file, sharding,
filtering, failover, resumption or automatic retry is permitted.

An exclusive external reservation precedes Docker create/start. Any ambiguous
failure after reservation consumes that invocation. Neither changing a folder,
container name, VM, mode label nor Actions run attempt renews authority. Image
pull failure before candidate launch does not authorize changing the image pin.

## 7. Capture, cleanup and truthful results

The controller captures suite stdout/stderr through bounded nonblocking pipes,
with daemon logging disabled. Overflow retains only the bounded prefix, marks
the result adverse, and triggers cleanup. It separately records the Docker
client status and the container engine's termination state/exit code, OOM/error
fields and intervention history. Client exit zero is not substituted for the
container result. This envelope trusts Docker; it is not a claim that the host
controller personally performed the container process's kernel wait.

On every outcome, cleanup targets the dedicated cgroup and exact created
container. A single `cgroup.kill` followed by an empty observation is insufficient
while an in-flight Docker start might later populate it: require confirmed
container removal, another whole-subtree kill, and `cgroup.events` readback
showing `populated 0` on the still-retained parent. Missing paths, failed removal,
inaccessible Docker or vanished client PIDs are not cleanup success. A terminal
marker prevents ordinary subsequent start paths; it is not itself a kernel
fence. Uncertain races remain indeterminate.

The independent systemd deadline service runs in `system.slice`, not the
candidate slice, and performs cleanup even if the primary controller dies.
Do not disarm it until cleanup is confirmed. Keep the parent active until its
readback is retained. `populated 0` proves no live processes recursively; it
does not independently prove every zombie was reaped or physical persistence.

### Terminal arbitration (C01 repair)

`result.json` is always provisional, even if its `candidate_classification`
describes a successful bounded observation. It is never sufficient terminal
evidence. A separate `terminal.json` binds its exact SHA-256 and plan identity.

The controller and deadline service arbitrate that terminal record using the
same root-owned, precreated, never-replaced zero-byte `terminal.lock` inode.
Lock acquisition waits at most five seconds. Process death releases the lock.
The deadline service records activation before waiting for the lock and still
attempts cleanup after a lock/marker/arbitration error; such an error is retained
in `deadline-cleanup.json`. Cleanup is never conditional on winning the lock.

After confirmed workload cleanup, the controller may seal a favorable bounded
observation only after all of the following while holding the lock:

1. Compare the still-active, untriggered timer with the exact initially armed
   `NextElapseUSecMonotonic`; do not derive a new later deadline.
2. Synchronously stop the timer **strictly before** that original earliest
   expiry, measured in the same host monotonic microsecond clock. `WakeSystem`
   must be false and timer accuracy adds delay, not an earlier firing point.
3. Separately synchronously stop/drain the deadline service. A timer stop alone
   does not cancel an already-activated service.
4. Read back both units inactive with no scheduled/running job, service substate
   dead, no observed service-start/activation or timer-trigger history, and no
   adverse marker. Retain all those observations and monotonic checkpoints.
5. Require reconciliation strictly before the original earliest expiry, then
   create the one terminal record exclusively. No prior terminal is replaced.

The absolute pre-expiry check is essential: zero history after systemd unit
garbage collection/reload cannot turn a post-deadline completion into success.
Under exclusive trusted-host control, a stopped timer plus a drained service
has no remaining activation source after sealing. Missing/partial seal, elapsed
deadline, lock failure, tool failure, pending job, observed activation, or
ambiguous state is indeterminate. Stopping a service waiting for the lock cannot
erase the original monotonic deadline. An adverse deadline disposition cannot
be overwritten by the controller. An unexpected later adverse record conflicts
with any favorable evidence and rejects; readers must inspect the whole set.

Only `watchdog_quiescent_pending_independent_review` in a complete controller
terminal record can support further review, and only together with the bound
provisional result, full streams, engine state and cleanup evidence. It grants
no acceptance or execution authority. Death before sealing leaves no favorable
terminal evidence; death after sealing cannot restart the drained watchdog under
the stated assumptions. This is a source-level argument, not observed behavior.

The suite deletes its fixture TemporaryDirectories. Container tmpfs also
disappears on stop. Consequently **individual synthetic receipts are not promised
as retained output**. Retain the external reservation, preflight and launch
metadata, bounded streams, controller/engine status and cleanup evidence. The
future publication order must explicitly allow the exact result file set named
by the controller; unexpected or missing output blocks a positive disposition.
No expiring Actions artifact is the sole durable copy after authorized retention.

The closed controller-output inventory under `/var/tmp/bowfin-pr18/control` is:

| When present | Exact relative filenames |
| --- | --- |
| Common to every fully reached qualification/suite gate | `intent.json`, `loaded-units.json`, `platform.json`, `cgroup-owned.json`, `create-argv.json`, `container.json`, `container-created.json`, `timer-armed.json`, `live-gate.json`, `stdout`, `stderr` |
| Normal controller completion | `attach.json`, `controller-cleanup.json`, `result.json` |
| Both qualification modes | `qualification-membership.json` |
| Deliberate controller-loss qualification | `watchdog-test-ready.json` |
| Independent deadline actually fires | `deadline-fired.json`, `deadline-cleanup.json` |
| Shared terminal protocol | `terminal.json`, zero-byte `terminal.lock` |

This is at most 20 files: two streams capped at 4 MiB each, seventeen JSON
records capped at 256 KiB each, and a zero-byte lock; at most 12 MiB plus 256 KiB
total file payload. The sole
additional directory, `docker-config`, must remain empty and contains no
credentials. Early failures may produce only an adverse partial inventory;
they are not successful runs with optional evidence omitted. A normal successful
suite has the common files, three normal-completion files and terminal-protocol
files. The deliberate
SIGKILL case instead expects no `attach.json`, `controller-cleanup.json` or
`result.json`; its independently retained deadline evidence supplies cleanup
observations, not a fabricated primary-controller result. Its flushed stream
bytes require separate bounded capture/hash readback before publication.
Its terminal record has deadline origin and indeterminate classification, not
a positive suite disposition. Early failures need not have a complete seal.

Host provisioning/job attestation and the later human-readable report are
separate records whose exact paths and bounds must be approved in the future
publication instruction. The inventory above permits neither arbitrary runner
filesystem collection nor publication now.

Passing synthetic evidence requires all 22 methods reported without failures,
errors or skips, a corroborating successful container result, complete bounded
capture, no adverse intervention, confirmed cleanup, and the complete favorable
terminal seal with matching provisional-result digest. External review checks
these jointly. It proves neither storage durability under power loss nor
production evidence validity. No emitted JSON or successful status grants
acceptance, ready-state, merge, retry, M0.1 completion or later-phase authority.

## 8. What is established now and what is not

Static preparation establishes the runtime content pin, narrow harness change,
source-level launch/cleanup implementation and fixed proposed limits. It does
not establish installed unit behavior, actual namespaces/cgroup limits, deadline
enforcement, usable procfs, or passing qualification/tests. Those observations
cannot honestly be manufactured by static analysis.

The next gate is Sarah's independent review of the **entire exact successor**,
including new controller/probe source and third-party seccomp policy. A favorable
review permits Greg to consider a bounded qualification order; it is not an
execution authorization. PR #18 stays draft. Production freshness, replacement
invocation and acceptance remain separate work, not hidden prerequisites or
permissions of this synthetic plan.

## 9. Primary API references

- [Docker run](https://docs.docker.com/reference/cli/docker/container/run/)
- [Docker cgroup driver/parent](https://docs.docker.com/reference/cli/dockerd/)
- [Docker force removal](https://docs.docker.com/reference/cli/docker/container/rm/)
- [Docker isolated loopback](https://docs.docker.com/engine/network/drivers/none/)
- [Kernel cgroup v2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)
- [systemd timers](https://www.freedesktop.org/software/systemd/man/255/systemd.timer.html)
- [systemd manager/unit API](https://www.freedesktop.org/software/systemd/man/255/org.freedesktop.systemd1.html)

These document mechanisms, not an attestation of the future runner.
