# PR #18 qualification launcher and closed retention proposal

Status: **static preparation only; not installed, dispatched, or qualified**.
Greg authorized preparation of this launcher and retention proposal for Sarah's
independent static review. No source in this directory is executed during that
preparation. No installation, dispatch, retry, suite, acceptance, readiness, merge,
production invocation, M0.1 completion, or later-phase authority follows.

## 1. Subject and separation

The workload remains the exact C01-C03 revision reviewed by Sarah:

| Identity | Fixed value |
| --- | --- |
| Repository | `gregkrsak/bowfin-migration-ledger` |
| Workload commit | `96e60a0a62d303f964fb4cefdc2687251f2f38b8` |
| Workload tree | `453d92123b914fb2c4aa082d9c42983ef69a83a5` |
| Operational subtree | `20e8b5bd1f9264f6eb00cba2db54c3e48407908b` |
| Invocation manifest blob | `15b7b50060774bbb7f0fb7f3ebda7626caf7c81e` |
| Manifest bytes | 1,778 |
| Manifest SHA-256 | `1f64f9e3039841e623d4010a5312fdb69a2a5401798d9dd49c2574e430425eb4` |
| Independent review | [Sarah's verbatim report](https://github.com/gregkrsak/bowfin-migration-ledger/pull/18#issuecomment-6543650389) |

The controller, probe, original 22-method harness, new 30-method controls,
supervisor, schema, runtime pin, seccomp policy/license, all three systemd units,
and deployment manifest are unchanged. The launcher is a separate trusted host
component. It never imports the controller or calls its functions. Its only
controller launch arguments select `qualify` or `qualify-watchdog`, never `suite`.
The original harness is materialized solely because the reviewed manifest is
closed; neither qualification branch executes it. The 30 mocked controls are not
part of deployment and are not invoked by this campaign.

This proposal supplements, and does not silently edit, `CONTAINED-RUN.md` at the
workload commit. Original review and adverse history remain historical facts.
Run 01 remains indeterminate; PR #17 and all production evidence are untouched.

## 2. Preparation is not activation

`qualification.workflow.yml` is deliberately stored here, **outside**
`.github/workflows/`. Publishing it on PR #18 cannot register or trigger it.
There is no push, PR, schedule, reusable-workflow, or repository-dispatch trigger.
The proposed installed workflow has only `workflow_dispatch`.

GitHub requires a manually dispatched workflow to exist on the default branch.
Putting it only on PR #18 would therefore create a qualification-before-merge
cycle. The future activation sequence is explicit:

1. Sarah statically reviews the exact launcher commit/tree, helper blob/digest,
   template blob/digest, retention contract, bootstrap code and pinned action.
2. If Greg agrees, a **separately authorized workflow-only bootstrap PR** targets
   ledger `main`. It copies the reviewed template byte-for-byte to
   `.github/workflows/pr18-containment-qualification.yml`, with no helper,
   controller, protocol, production-evidence, or other default-branch changes.
   Greg alone decides whether to merge that bootstrap PR. PR #18 stays draft.
3. Verify the bootstrap's actual merge, installed workflow blob and bytes,
   helper pin and workload pin. A pre-merge test SHA is not the installed ref.
4. Greg separately authorizes one two-case campaign at those exact identities,
   with this complete publication allowance and exact installed workflow SHA.
   The operator dispatches the exact ref once. Installation is not dispatch
   authority; the earlier unattempted qualification go-ahead is not a standing
   permission to execute a newly authored launcher.
5. Preserve and independently review both captures before any suite decision.
   Qualification does not authorize merging PR #18 or running the suite.

No bootstrap PR, active workflow installation, settings change, dispatch or
qualification is part of the present preparation. This proposal does not assume
that the current connector can dispatch Actions: the separately authorized
operator must use a supported interface; permission/authentication blockers stop
the operation rather than justify credential extraction or an alternate runner.

The workflow pins the helper to an already-created ancestor commit and its
SHA-256. It does not claim to contain its own future commit hash. The installed
workflow SHA is an independent assertion supplied in the future dispatch order
and compared with GitHub's workflow/source context, not an approval token.

| Launcher acquisition binding | Exact value |
| --- | --- |
| Helper commit | `1fd58aa6a46b646418a8eb258c9102e5f8045672` |
| Helper commit tree | `d166d12f9b6712553eea7d778a85efcb527751e9` |
| Helper path | `operations/m0.1/evidence-supervisor/qualification/runner.py` |
| Helper blob | `233c6ef63514b4b5fe15fb7e099086c19350c3ba` |
| Helper bytes | 36,268 |
| Helper SHA-256 | `8792a1abde9d35b355445bfb436db6c5db5f01fac22d2bab0be11da782ef1606` |
| Upload action | `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` |
| Action descriptor blob | `2a0ecf19e8d0087dd2e5d1785dcf764811e79fae` |

The Git-pinned action runs its bundled Node 20 entrypoint without a package-install
step. GitHub's host-supplied Node runtime remains a trusted platform component.
The pin establishes content identity, not security certification.

## 3. Two cases, two fresh VMs, no suite

The template has two explicit jobs, not a matrix or a selectable command input:

| Job | Exact controller mode | Dependency |
| --- | --- | --- |
| `ordinary` | `qualify` | First |
| `watchdog` | `qualify-watchdog` | Ordinary job, including capture upload, succeeds |

Each job requests a new GitHub-hosted `ubuntu-24.04` x86-64 VM, never a job
container or self-hosted runner. The workflow refuses an event/repository/ref
mismatch or `run_attempt != 1`. No job uses automatic retry, rerun, failover,
resumption, sharding, `continue-on-error`, package installation, engine repair,
runtime replacement, mutable checkout, repository hooks, or candidate imports.
Only an exact pinned upload-artifact action runs after capture; no checkout
action or repository token is passed to the helper or workload.

Every job has a 20-minute platform ceiling. Acquisition/preflight has a 100-second
deadline from the first bootstrap monotonic timestamp. The unchanged independent
timer has a 960-second interval, 1-second accuracy, 45-second service runtime and
5-second stop timeout. The wrapper reserves additional time for bounded readback
and upload; it does not shorten, restart, or reset the reviewed timer to fit the
job. Platform timeout, cancellation, host loss, acquisition failure or missing
capture is adverse/indeterminate, not cleanup success or retry permission.

An exclusive case reservation and the controller's exclusive control-directory
reservation prevent in-VM resumption. They do not globally authenticate or prevent
an unauthorized new GitHub run. Greg's finite campaign order and operator checks
remain necessary; a new run ID, run attempt, VM or directory renews no authority.
If ordinary fails, watchdog is not launched. Any launched/reserved case is spent
under the no-retry rule; repairing infrastructure or raising budgets needs a new
reviewed proposal and owner decision, not another click.

## 4. Host acquisition and preflight

The trusted launcher acquires only the fixed workload commit/tree and the eleven
closed deployment files (ten manifest entries plus the manifest). It authenticates
the Git-object correspondence, blob identities, byte counts and SHA-256 values
before installing source or launching candidate code. It does not fetch or read
archive payloads, compiler roots, accepted verifier code, inputs, observations,
production packages, or empty-review subtrees. Tree siblings may be inspected as
opaque identity metadata only.

The public registry image is the exact pinned Linux/amd64 image in the existing
contract; no tag-based launch, image build, package installation or override is
permitted. Network acquisition finishes before container launch. No proxy,
credential environment, Docker socket or host management path is mounted into
the workload. The runner's host network remains a trusted acquisition/artifact
surface; workload networking is independently constrained by the reviewed
controller and benign probe.

Before candidate launch, retain whitelisted run/job/attempt/workflow metadata,
runner image version, kernel, boot ID, host binary hashes/versions, systemd and
Docker identities/configuration and cgroup/mount topology. Reject remote or
rootless Docker, wrong cgroup version/driver, unusable controllers or `cgroup.kill`,
unexpected existing paths/units/containers, symlinks, wrong ownership/modes,
source drift, missing metadata or unsupported topology. The VM label is not an
immutable host identity or complete attestation.

Install only the exact three reviewed units under `/run/systemd/system/`,
root-owned, mode 0644, exclusively for this VM. Do not enable them for boot or
change any other unit. The controller independently checks their loaded/effective
properties. There are no concurrent privileged starts, resets, reloads, daemon
reexecs, source/unit rewrites or clock-namespace changes during the attempt.
All host tools and candidate processes receive a cleared, explicitly bounded
environment. Host Python, kernel, Docker, systemd, GitHub's runner/runtime and
artifact action are disclosed trusted components, not untrusted workload code.

## 5. Observation requirements, not an acceptance oracle

The runner records its direct child's terminal status separately from controller
files. A complete-looking JSON file cannot erase a nonzero publisher status or
known write/fsync failure. The helper does not certify physical persistence.

Ordinary observation requires the expected release/membership evidence, controller
exit zero, provisional qualification result with no error, confirmed exact-container
removal and retained-parent `populated 0`, plus a controller-origin terminal seal
binding the actual retained `result.json` digest and exact plan. That seal must
state `watchdog_quiescent_pending_independent_review`. Deadline-origin records
or conflicting later evidence reject the ordinary observation.

Watchdog observation requires direct controller termination by SIGKILL, its ready
record binding PID/boot ID, the same release/membership transport, and actual
activation/completion of the independent deadline service. The wrapper never
calls `deadline` itself or substitutes its own early cleanup. It waits for the
reviewed timer/service and retains actual final unit/job/status observations.
The service intentionally returns **1** after complete cleanup; therefore its
`Result=exit-code` and `ExecMainStatus=1` are expected. The terminal record remains
deadline-origin **indeterminate**, not favorable suite evidence. Require complete
deadline cleanup, no arbitration error, exact container absent and the retained
parent empty. No fabricated primary result is permitted.

Because a publication exception could also exit 1, watchdog reconciliation also
retains bounded diagnostics for this exact unit/boot and checks for publication
errors and incomplete diagnostic coverage. Exit 1 and JSON presence alone are
insufficient. The required manager exit record and a tail shorter than 128
entries establish available-record corroboration, not proof that journald never
lost or rate-limited a message. The host manager, journal and filesystem remain
trusted external components; an unobserved logging/storage failure is not ruled
out. No logging reconfiguration is performed to hide this limitation.
Filesystem or host failure, known missed/overflowed diagnostics, partial
publication, vanished cgroup or unverifiable final state remains indeterminate.

The helper's positive wording is only **observations captured, pending independent
review**. A successful Actions conclusion is not independent qualification,
acceptance, suite success, merge permission, or authority for another invocation.
Independent review must reconcile the entire capture, publisher states, source
and workflow identities, transport, mounts/quotas, cgroups and all limitations.

## 6. Exact proposed retention allowance

For each case, the future capture root is `/var/tmp/bowfin-pr18-export`.
Only the following paths may be uploaded or later retained. No arbitrary glob
over the runner filesystem, environment dump, credential/config export, image
layer, cache, Git checkout or journal outside the named unit is permitted.

Under `control/`, the closed twenty-name union is:

| Group | Exact relative filenames |
| --- | --- |
| Common eleven | `intent.json`, `loaded-units.json`, `platform.json`, `cgroup-owned.json`, `create-argv.json`, `container.json`, `container-created.json`, `timer-armed.json`, `live-gate.json`, `stdout`, `stderr` |
| Both cases | `qualification-membership.json`, `terminal.json`, `terminal.lock` |
| Ordinary only | `attach.json`, `controller-cleanup.json`, `result.json` |
| Watchdog only | `watchdog-test-ready.json`, `deadline-fired.json`, `deadline-cleanup.json` |

A completely reached case has exactly seventeen controller files. Ordinary
forbids the three watchdog-only records; watchdog forbids the three ordinary-only
records. Partial or conflicting inventories may be preserved as adverse evidence,
never passed as a complete case. Each controller JSON is at most 256 KiB; each
workload stream at most 4 MiB; the lock is exactly zero bytes. The otherwise empty
`docker-config` directory is checked but not exported. No nested extra directory,
symlink, special file, extra name or overflow can support a positive disposition.

The exact additional wrapper files are:

| Relative path | Maximum bytes |
| --- | ---: |
| `host/attestation.json` | 262,144 |
| `host/launch-status.json` | 65,536 |
| `host/final-state.json` | 196,608 |
| `host/deadline-journal.txt` | 262,144 |
| `host/controller.stdout` | 65,536 |
| `host/controller.stderr` | 65,536 |
| `inventory.json` | 65,536 |
| `report.md` | 65,536 |

Wrapper maximum: exactly 1 MiB. Including the entire controller union, the
per-case absolute payload ceiling is **28 files / 13,893,632 bytes** (13 MiB plus
256 KiB), and the two-case ceiling is **56 files / 27,787,264 bytes**. A normal
seventeen-file case is below this union ceiling. Transport ZIP overhead is not
canonical file payload. Retained files are plain regular files, not an archive
that requires executing extraction hooks.

`inventory.json` authenticates each retained payload's exact path, byte count
and SHA-256, excluding itself. Its digest is recorded externally in the later
publication report, not as a self-hash. Missing or changing files during capture
fail the positive disposition. Capture finalization is exclusive/no-replace and
read back; known publication errors are retained, not hidden behind success text.

Artifact names are `pr18-qualification-<run-id>-1-qualify` and
`pr18-qualification-<run-id>-1-qualify-watchdog`, with 30-day transport retention,
no overwrite and no workflow, job, or candidate-invocation retry. The pinned
artifact library may retransmit transport requests within its one-minute step
ceiling; that is disclosed transport behavior, not another qualification or
renewed authority. Expiring artifacts are transport, never sole durable
evidence. Before relying on them, an authorized external operator downloads and
verifies the bounded exact files and preserves them append-only under:

`operations/m0.1/evidence-supervisor/qualification-results/campaign-01/<case>/`

where `<case>` is exactly `qualify` or `qualify-watchdog`. The later human report
may add only `operations/m0.1/evidence-supervisor/qualification-results/campaign-01/REPORT.md`,
at most 65,536 bytes, for an aggregate durable allowance of **57 files /
27,852,800 bytes**. It must record run/job URLs and IDs, attempt, installed
workflow/helper/workload identities, inventory digests, dispositions and limits.
It may not rewrite any existing file. No such result exists or is published now.
Missing durable retention blocks use of the qualification evidence.

## 7. Static preparation checks and review limits

Preparation checks parse Python/YAML/JSON as data and compare immutable bytes,
Git objects, exact paths, branch state, action pins and the proposed inventory.
They do not import or execute the helper, controller, probe, harness, supervisor,
tests, Docker, systemd units, workflow or accepted migration tools.

Sarah should challenge the new launcher/transport/capture and this allowance,
including partial failures and the expected watchdog exit-1 ambiguity. The prior
C01-C03 finding disposition applies to the unchanged workload, not automatically
to the new host launcher. The launcher adds trusted operational power and must be
reviewed as such. Neither internal static QA nor Sarah's review grants execution.

Primary platform references:

- <https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow>
- <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax>
- <https://github.com/actions/upload-artifact/tree/ea165f8d65b6e75b540449e92b4886f43607fa02>

Greg retains every acceptance and merge decision.
