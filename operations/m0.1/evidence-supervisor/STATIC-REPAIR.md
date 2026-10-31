# Focused supervisor test repair — static preparation only

This is a successor to the original preparation and static review, not a rewrite
of them. Sarah's chat-delivered independent review examined PR #18 head
`a1f8066ef65db4980ac0189282912207f6b83041`, tree
`f2b9ebde7e461862bbbf6dd8e150ba37cbba8f18`. It found BML-SUP-T01 and T02
major test-oracle gaps, T03 a minor wait-result coverage gap, and X01 an
unresolved containment prerequisite. It found no confirmed supervisor
incorrect-success defect at that head. Her report has not been published here;
this summary does not substitute for the complete independent report.

The successor changes the synthetic tests and adds a proposed containment plan.
The supervisor, design, schema, and original static report are unchanged. The
original report's references to its 19 controls and hashes describe that earlier
revision; the successor has 22 test methods, including parameterized cases.

- T01: require exact saved bytes at the stream limit and for the overflow prefix;
  independently check known, distinct data on both streams.
- T02: classify synchronization attempts by open object and publication state;
  assert the expected normal sequence and inject failures at reservation,
  intent, both streams, temporary receipt, and the three receipt-directory
  publication stages. A visible final receipt after failed publication does not
  prove the supervisor's final synchronization or exit completed.
- T03: inject wrong-PID, nonterminal, incorrect-type and malformed-shape wait
  results after reaping a synthetic exit-2 child, guard against signaling after
  loss of ownership, and check that no receipt asserts a fabricated zero.
- X01: `SYNTHETIC-CONTAINMENT.md` proposes an independently controlled
  container and cgroup boundary. It is not an installed, verified, pinned, or
  authorized runtime; a future exact plan must establish all those details.

Only static preparation is authorized. Syntax parsing does not import or execute
the candidate. The controls are authored and unrun: they do not establish actual
behavior, physical durability, safe containment, or a test pass. In particular,
fault injection cannot prove persistence during power loss. Independent review
must examine this new revision and the proposed containment before Greg decides
whether to authorize any bounded synthetic execution. Run 01 remains
indeterminate. This work grants no retry, production invocation, acceptance,
ready-state, merge, M0.1 completion, or later-phase authority.
