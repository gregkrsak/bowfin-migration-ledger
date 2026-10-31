# Campaign 01 — qualification acquisition failure

Status: **indeterminate; ordinary acquisition failed; watchdog skipped**.
Preservation only, pending independent review. This record grants no retry,
qualification acceptance, suite execution, merge, M0.1 completion or later phase.

## Exact subject

| Item | Observed identity |
| --- | --- |
| Repository | `gregkrsak/bowfin-migration-ledger` |
| Run | [41209928358](https://github.com/gregkrsak/bowfin-migration-ledger/actions/runs/41209928358) |
| Event / branch / attempt | `workflow_dispatch` / `main` / `1` |
| Reported actor / triggering actor | `gregkrsak` / `gregkrsak` |
| Installed workflow commit | `14ad3bba0ec0dbd416262d41b6529c211fda0a64` |
| Installed tree | `77523facd951eb411d6188e29db64ca5ee3f9221` |
| Workflow blob | `6a774792d4eb75d6d00851d659e321ef82a74509` |
| Workflow SHA-256 | `4736f550f4fc6ed13b040b05e5a639f104d13ccb108d32c1f7de194e6545ddf1` |
| Helper commit | `1fd58aa6a46b646418a8eb258c9102e5f8045672` |
| Helper blob | `233c6ef63514b4b5fe15fb7e099086c19350c3ba` |
| Helper SHA-256 | `8792a1abde9d35b355445bfb436db6c5db5f01fac22d2bab0be11da782ef1606` |
| Reviewed workload commit | `96e60a0a62d303f964fb4cefdc2687251f2f38b8` |
| Workload tree | `453d92123b914fb2c4aa082d9c42983ef69a83a5` |
| Manifest blob | `15b7b50060774bbb7f0fb7f3ebda7626caf7c81e` |
| Retention-plan commit / blob | `71e19cbf7264ed77c4e2d3ddd7d0a4ed9b69864a` / `98e417426d1a68472fbc0c4853d81ffd639df1bc` |

The run was created at 2026-10-31T14:23:43Z and last updated at
2026-10-31T14:24:00Z. Captured metadata independently records the same
GITHUB_SHA, GITHUB_WORKFLOW_SHA, repository, branch, job and first attempt.
Reported account names corroborate the owner-operated process; their presence
alone is not authentication or executable authority.

## Observed result

| Job | ID | Result |
| --- | --- | --- |
| Ordinary | `124562591349` | Failed, outer step exit 2; upload succeeded |
| Watchdog | `124562646443` | Skipped; no case artifact |

The retained ordinary `host/final-state.json` records:

```text
HTTPError: HTTP Error 403: rate limit exceeded
```

Its classification remains `indeterminate`, `accepted` is false, and
`suite_executed` is false. `host/launch-status.json` records
`invocation_attempted: false` and `retry_authorized: false`.

Static tracing of the exact helper places `materialize()` and its unauthenticated
GitHub API reads inside `prepare()`, before image acquisition, unit installation
and the subsequent `invoke()` call. The error and incomplete host/source record
support an acquisition-stage stop before controller invocation. The specific
API request, rate-limit headers, quota reset time and shared-egress explanation
were not retained and are not claimed here.

This is not a failed containment exercise or a compiler defect. Neither ordinary
controller behavior nor watchdog behavior was exercised. The helper and trusted
host inspection commands did execute; saying that no executable ran would be false.
No synthetic suite or production verifier ran.

## Exact preserved partial capture

Artifact ID `13044984141`, name
`pr18-qualification-41209928358-1-qualify`, was created at
2026-10-31T14:23:57Z and was not expired at capture. Transport expiry is
2026-11-30T14:23:56Z.

The downloaded ZIP was exactly **9,729 bytes**, SHA-256:

`7caaacd9382a2ebd29d521b63d53c351d9c0ac911a327a39dd7bdbe26e2b2667`

That digest matches both artifact metadata and the upload log. ZIP members were
read as bounded data, not executed. Duplicate names, traversal paths, symlinks and
oversized payloads were rejected before preservation. No ZIP is added to the
canonical ledger path.

The six retained files below are copied byte-for-byte beneath `qualify/`:

| Path relative to qualify/ | Bytes | SHA-256 |
| --- | ---: | --- |
| `host/attestation.json` | 7219 | `36f297eb060516ff16232646bdfc0b2dde53d052f2b88adc3c0f8a7f0a0667d0` |
| `host/deadline-journal.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `host/final-state.json` | 228 | `0dbeaa6c2498fe20601f8e18b05c37fc6f8d3409b6fa2df14505b96fff26472e` |
| `host/launch-status.json` | 106 | `8197cbf0fd32514a8a831f95d2cc1d592d757747b1839d5052ece09729c8e495` |
| `inventory.json` | 936 | `29c37ec2a13a60a306f7789cfd1b93b30419be97c17efee0b803c9783771afa6` |
| `report.md` | 440 | `fde9a28a5524fe36862dcf58fb5d95f2e004e62454aed1fe738d0bf149509adb` |

Total partial-capture payload: **8,929 bytes**. The five entries in the original
inventory exactly match the other five retained files by path, byte count and
SHA-256. Its external inventory digest is:

`29c37ec2a13a60a306f7789cfd1b93b30419be97c17efee0b803c9783771afa6`

The inventory deliberately excludes itself. This report binds it externally and
does not contain its own future storage commit. Outward PR metadata records the
resulting preservation commit and tree.

No missing controller record is fabricated. No watchdog directory, stub result,
success marker, fabricated second capture or additional host dump is added. This
six-file partial case is not the seventeen-control-file complete-case inventory.
This report is the sole additional permitted campaign file and remains below its
65,536-byte ceiling; all additions remain inside the reviewed 57-file,
27,852,800-byte maximum. Existing files and records are not modified.

## Method and limitations

Miles retrieved run metadata, both jobs, artifact metadata and the complete
ordinary job log through the GitHub connector, downloaded the artifact and
independently verified its ZIP digest, members and internal inventory. The helper
source was read at its exact reviewed identity; it was not executed locally.
The full job log is not added as an eighth file outside the closed retention set.

Two platform discrepancies remain disclosed, without a qualification claim:
the setup log names runner image `20261025.353.1`, while retained ImageVersion
is `20261026.354.1`; the upload log states that the pinned Node-20 action was
forced by GitHub to run on Node 24. These are unreconciled provenance observations,
not established causes of the API error.

Independent containment/mount/quota/cleanup observations are absent because no
controller invocation was attempted. An empty deadline journal is not evidence
that watchdog cleanup succeeded. Successful artifact upload proves transport,
not qualification or physical persistence.

## Disposition and next boundary

Campaign 01 is spent under the reviewed no-retry rule despite the pre-invocation
stop. The watchdog was skipped rather than silently retried elsewhere. Neither a
new run ID nor waiting for quota reset restores authority.

The narrow engineering target is source acquisition's anonymous GitHub API
dependency. Any acquisition repair, revised immutable pins and successor attempt
require their own review and explicit owner decision; none is implemented or
authorized by this preservation record. No budget or containment limit is changed.

PR #18 remains draft and its reviewed code unchanged. Run 01's earlier
indeterminate status is untouched. Greg remains sole acceptance and merge
authority. This record is unaccepted operational history, not M0.1 evidence or
an executable approval.
