# Proposed synthetic test containment — not authorized or verified

This is a proposed prerequisite for a later independently reviewed and separately
authorized synthetic run. It is not a runner configuration, evidence of an
existing sandbox, permission to execute, or a replacement invocation map.
Run 01 remains indeterminate.

## Proposed enforcement boundary

Use an independently controlled Linux container with a dedicated cgroup v2
subtree, created and monitored by a trusted controller outside the candidate's
process tree. The cgroup must contain the entire test job and all descendants,
including processes that create new sessions. The candidate cannot administer or
escape the cgroup. If the actual platform cannot demonstrate these properties,
stop before launching the suite.

- Fix and review the OCI image by digest and its complete runtime closure,
  including interpreter, standard library, native libraries, and loader. Verify
  the test's exact interpreter path and digest against the materialized image;
  pin and independently read back the exact candidate source and tests.
- Start without external networking, credentials, tokens, host sockets, or
  ambient repository write access. `network=none` may retain loopback; the plan
  must either disable loopback or explicitly document and review its residual
  availability. Mount reviewed code read-only and isolate a dedicated scratch
  filesystem with a hard size limit; keep scratch outside all evidence roots.
- Run as an unprivileged identity, drop capabilities, set no-new-privileges, use
  a read-only container root, and prevent access to container-management sockets.
  Verify actual enforcement rather than treating flags as proof.
- Before authorization, specify finite CPU, memory, process-count, scratch
  storage, and wall-clock limits, including their enforcement mechanisms and
  sufficient headroom for the exact suite. Inability to establish any required
  limit is a stop condition, not a reason to run without it.
- An external watchdog owns the whole-job deadline and, on normal completion,
  test failure, cancellation, or timeout, destroys the container and kills the
  entire cgroup. Independently verify that the cgroup has no remaining tasks
  before reporting cleanup complete. A separately enforced platform deadline
  must cover watchdog loss. Host loss or inaccessible cleanup status remains
  indeterminate; no receipt or process disappearance proves whole-job cleanup.

Before a run, a reviewed plan must name the actual platform, pinned image and
runtime identities, exact source, commands, fixed limits, watchdog and cleanup
owner, no-network and no-credential checks, result capture, and what happens if
any check or cleanup verification fails. It must account for a synthetic child
that starts a new session and for supervisor, test harness, or watchdog failure.
These requirements are proposals until independently verified on that platform.
No tests, live verifier, workflow, or production material may be run under this
document alone. A later result cannot repair Run 01's missing observed status.
