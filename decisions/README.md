# Decision records

This directory preserves append-only records that explain why an exact ledger or
compiler identity was prepared, reviewed, accepted, rejected, corrected,
revoked, merged, transferred, or retired.

A decision record is descriptive evidence, not an executable credential. It must
bind the exact subject identities and quote or hash the authorizing statement it
preserves. It must distinguish preparation, execution, review, acceptance, merge,
integration, and later-phase authority; none implies another.

Records never rewrite the immutable evidence package they describe. Corrections
and revocations are new records that identify their predecessors. Ordering by
filename, commit time, comment time, or author-name string does not establish
precedence. Greg remains the sole human merge authority.

The first record under `decisions/m0.1/` preserves only the bounded authorization
to prepare the M0.1 v2 protocol/tooling candidate. It does not authorize running
that candidate, producing evidence, accepting M0.1, beginning M1, or merging.

The protocol/tooling acceptance closeout preserves the final independent review,
Greg's exact-revision acceptance, and the ordinary PR #3 merge. It accepts only
the recorded protocol/tooling revision. Production compact inputs, migration
evidence, M0.1 acceptance, M1, and later work remain separately gated.

The occurrence-semantics repair closeout preserves the independent execution
confirmation, BML-OS12 record-correction readback, exact prescribed correction,
Greg's acceptance, and the ordinary PR #6 merge. It makes the repaired revision
the then-current accepted protocol/tooling dependency. PR #5 and its compact inputs
remain unaccepted and require reconciliation; production execution, migration
evidence, M0.1, M1, and later work remain separately gated.

The later work-budget closeout preserves the complete static and independent
execution-evidence reviews, an unchanged copy of the retained PR #9 synthetic
validation capture, owner authorization and merge context, and actual PR #9 merge
correspondence. The current accepted tooling is the exact budget-only revision
integrated at `4020cb64c1119ccfb4a4bc77b3f39e8b698ba2f5`, not the operational
PR #10 branch or a later records-only head. PR #10's workflow and helper are not
imported. The historical validation capture retains its original prospective and
draft-state wording; the later acceptance record resolves chronology without
rewriting those bytes.

The work-budget acceptance is limited to tooling. Its single synthetic-execution
authorization is exhausted. PR #5, PR #8, production scanning/evidence, M0.1, M1,
and later work are not accepted or authorized by this record. Reviewing or
merging a records-only closeout grants no new execution or later-phase authority.
