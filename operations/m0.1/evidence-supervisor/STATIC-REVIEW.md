# M0.1 supervisor preparation — internal static review

**Disposition: prepared for Sarah's independent static review. Not executed,
accepted, ready for merge, or approved for an evidence invocation.**

## Scope and exact source

Miles prepared this five-file operational proposal from ledger commit
`1f6216b16bf6fe737d1aad8a5eac043ed240cf7c`, tree
`c8aadb0545cab81a85525a397a351cf36fc9bf04`. The governing contract and all preserved
Run 01 identities are recorded in `DESIGN.md`.

The entire change is confined to `operations/m0.1/evidence-supervisor/`:
`DESIGN.md`, `supervisor.py`, `test_supervisor.py`, `receipt.schema.json`, and this
record. The containing commit/tree must be read from the published PR; this file
does not embed its own future Git identity.

| Reviewed artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `DESIGN.md` | 16,975 | `c023743c797c7d5c760eefbe8ded735ae7bdb3f94f45401df6e8f90f3d551007` |
| `supervisor.py` | 22,348 | `ff828c196cc5e29c5c1aa89c5941428102b87fae4d361d8ed1aa38850b15b7b9` |
| `test_supervisor.py` | 20,395 | `3db09dd0efad225181a735ebca290376186f8d3c4f71872334a4f5a658ac3af8` |
| `receipt.schema.json` | 8,210 | `0cf7a7c47c98321a794385a3ab537c9d3efdf8b14d73bfce1e1b3963fc78f7ca` |

These identities describe a proposal, not accepted operational tooling.

## Checks actually performed

- Read the ledger instructions and governing contract; inspected exact current
  main and PR #17 identities. Main and PR #17 remained at the identities in
  `DESIGN.md` before publication. PR #17 remained open, draft, and unmerged.
- Read the entire proposed source, test source, schema, and design. Internal
  auxiliary reviews separately challenged failure handling and the replacement
  contract. These are Miles's internal QA, **not Sarah's independent review**.
- Parsed both Python files with trusted standard-library `ast.parse`, as inert
  source only. No candidate import, bytecode compilation, CLI invocation,
  `--help`, test, or production verifier operation was performed.
- Parsed the JSON schema as data and manually inspected its relationships with
  the source/receipt fields. This is not a claim that a JSON Schema validator or
  the synthetic suite was run.
- Counted one child-spawn call site in the supervisor and 19 test methods by
  source/AST inspection. Neither count establishes dynamic behavior.
- Hashed exact prepared file bytes and the original map bytes. The original map
  SHA-256 agrees with the preserved map identity in `DESIGN.md`.

The branch introduces no workflow. No workflow was dispatched, no Rust ran,
no evidence was regenerated, and no observation was refreshed.

## Concrete findings addressed before publication

### Missing child status must not become zero

The initial draft used `Popen.poll()`/`wait()` for observation. Static review
identified a second false-success path: CPython's POSIX implementation can
substitute zero after `ECHILD`/`ChildProcessError`. This behavior was confirmed
by reading the deployed runtime's `Lib/subprocess.py`; that file's SHA-256 was
`85d29b2bf0249f5436838298c9a60ee93508b1102e9ac43b001f8a7e7ae8f375`.

The final source instead uses exclusive direct `os.waitpid(pid, WNOHANG)`,
accepts only the exact child's genuine terminal status, retains raw status,
and derives receipt status from a separate observed value. Missing/malformed
status stays unknown; it never consults Popen's fallback returncode. The source
rejects nondefault inherited `SIGCHLD` and stops signaling after reaping or
detected loss of wait ownership. The focused internal reviewer re-read this
repair at the exact source hash above and closed this implementation finding
statically. **No runtime validation is claimed.**

Controls 18 and 19 were added for unavailable raw status and nondefault SIGCHLD.
Control 18's fixture consumes a real synthetic exit-2 wait status and withholds
it from the supervisor, requiring unknown status, one spawn, and no subsequent
process-group signal. The fixture is authored, not executed.

### Bounds and publication claims

Static self-review also removed duplicated cleanup-budget use, rejected
nonfinite exponent-overflow JSON, checked short stream writes, and tightened
close/signal restoration. The source has one shared cleanup deadline.

The design now distinguishes a retained child observation from proof that the
publisher's final sync/exit completed. A surviving receipt is read back as actual
bytes; known publication errors remain disclosed. This prevents either a lost
chat envelope or a visible filename from becoming a stronger claim than the
available evidence.

### Replacement contract conflicts

The design explicitly replaces the old process-replacement/direct-redirection
mechanics only in a later reviewed map. It does not silently reuse the old map,
three-file publication allowance, exhausted authority, or freshness clearance.
Changing an attempt label never overrides no-retry. No replacement map or
executable owner authorization has been instantiated here.

## Authored synthetic coverage — zero executions

| Controls | Intended boundary |
| --- | --- |
| 01–03 | Silent zero, empty-stream SIGKILL, and normal nonzero remain distinct |
| 04–06 | Timeout, exact output limit, and overflow with bounded retained prefix |
| 07–09 | Wrong map digest, Boolean timeout, duplicate JSON key reject before spawn |
| 10–12 | Reservation reuse, spawn failure, and reservation-sync failure |
| 13–15 | Receipt-link failure, SIGTERM cancellation, stream-write failure |
| 16–17 | Supervisor-source digest mismatch and nonfinite numeric input |
| 18–19 | Missing kernel wait status cannot become zero; nondefault SIGCHLD rejects |

The test harness pins the proposed runtime executable, uses only synthetic
children/IDs, limits each outer process to 20 seconds, and gives real fixtures an
eight-second alarm. It requires a separately approved whole-suite execution and
containment plan. Its fixtures do not read production packages or invoke the
accepted verifier.

The 19 controls do **not** simulate host power loss, every supervisor-SIGKILL
cutpoint, actual filesystem durability under disk failure, or every descendant
escape condition. They do not establish the outer runner's network/resource
isolation. Those limitations must remain explicit in the later validation plan;
they cannot be converted into tested claims because source review found no bug.

## Preparation-instruction provenance

- Stated author: Greg, the project owner in this conversation.
- Publisher/transcriber: Miles.
- Origin: current user message; no stable chat URL/message ID was available.
- Capture method: verbatim transcription from the message supplied to this turn.
- Capture time: `2026-10-31T02:01:16Z`.
- Applicability: this preparation proposal against the exact base above only.
- Encoding: UTF-8, no terminal LF within the quoted body; 303 bytes.
- Body SHA-256: `2fb61f01bc1ee6aaaabe875fe709027e1147496116dec0b764f538890b5d1bae`.

> I'm going to give you a temporary field promption to GPT-6 Astra Ultra for this unique assignment: Greg authorizes preparation and static review of the bounded M0.1 execution-supervisor repair and replacement-invocation design. This authorizes no execution, retry, acceptance, merge, or M0.1 completion.

This retained text and digest are descriptive process evidence, not cryptographic
identity verification, an executable approval, or permission for any later step.
The later PR's immutable head/tree binds this proposal; no future identity is
asserted inside this record.

## Handoff boundary

Sarah should independently inspect the exact published head and full five-file
delta, challenge status truth, physical bounds, fixture reachability, publication
semantics and authority/freshness separation, and report findings without running
the candidate. Internal QA is evidence to challenge, not a required verdict.

Run 01 remains indeterminate, and BML-E17R-01's historical missing-result limitation
is not retroactively closed. This proposal grants no execution, retry, acceptance,
ready-state transition, merge, refresh, production mutation, M0.1 completion, or
later phase. Greg remains the sole decision/merge authority.
