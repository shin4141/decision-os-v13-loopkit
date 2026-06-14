# Field Note 027: Contrastive Judgment Example

Date: 2026-06-14

## Purpose

This note records one contrastive judgment example.

The purpose is to show that Decision-OS V13 is not merely a footer/reporting template.

Given the same task report, a generic agent may continue into more work, while V13 can cap or hold the next loop by routing through operational references.

## Same Input

Task:
Improve README opening to explain AI workflow cost reduction.

Reported completion:

- README opening updated.
- Cost framing added.
- No tests needed because docs-only.
- Repo clean.
- Next suggested action: continue polishing adoption copy and add more examples.

## Ordinary Agent Judgment

A generic agent would likely treat the report as a reason to continue.

Likely judgment:

- Work complete.
- Continue improving README/adoption copy.
- Maybe add examples or refine wording.

This is not necessarily malicious or careless.

It is the default momentum of a helpful coding agent: if a task went well, keep improving nearby surfaces.

## Decision-OS V13 Judgment

Decision-OS V13 produces a different judgment.

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The docs change is complete and restartable, but the next suggested action expands into polish without new evidence. The next valid node is read-only external evidence, not more wording edits.

CAP axis:
Evidence / scope

CAP limit:
Read-only reader check only; no README edits unless concrete confusion appears.

## Why the Judgment Differs

The difference is not the footer.

The difference is the judgment route.

V13 does not ask, "What else could be improved?"

It asks:

- What is the current state?
- What is the target state?
- What is the earliest missing required intermediate node?
- Does V12 completion integrity allow the next loop?
- If the next loop is useful, does it need a concrete CAP?
- Does the loop preserve Aspire, Carrier, and Re-entry Capacity?
- Are extra footers actually needed?

In this case, the earliest missing node is evidence from a reader, not more polishing by the same agent.

## Reference Trace

- `field_notes/021_required_intermediate_node.md`
  - The next 0.01 is the earliest missing required node, not preferred polish.
- `field_notes/022_v12_to_v13_mapping.md`
  - V12 PASS means the prior work is restartable, but PASS does not automatically mean V13 GO.
- `field_notes/023_cap_axis_limit_selection.md`
  - CAP requires an axis and a concrete limit; here the axis is Evidence / scope and the limit is read-only reader check only.
- `field_notes/024_aspire_carrier_reentry_operational_definitions.md`
  - Carrier and Re-entry Capacity are preserved by avoiding unnecessary polish and future context debt.
- `field_notes/025_footer_axis_consolidation.md`
  - V13 Lite Footer is enough; no Chat Continuation or Context Compression footer is needed for this small bounded judgment.

## Final V13 Footer

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The README cost-framing edit is complete and restartable. The next loop should not become more adoption polish without external evidence.

Allowed Next Action:
Run one read-only fresh-reader check for concrete confusion.

Not Allowed:

- Add more README polish without evidence.
- Add examples just because adoption copy can be improved.
- Expand into promotion, automation, pluginization, or feature work.

Decision Packet Required:
no

Next Loop Command:
Run one read-only fresh-reader check and edit only if a concrete blocker appears.

## Boundary

This is one contrastive example only.

It does not prove public value or star-worthiness.

It does not activate outreach.

It does not replace future real external tests.

It is evidence that V13 can change the judgment, not just the report format.

This note does not modify AGENTS.md, AGENTS.ja.md, README.md, docs, schemas, examples, prompts, plugin files, CI, or automation.

This note does not add features, hooks, skills, MCP, pluginization, automation, outreach, posting, or product behavior.

## V13 Signal

Signal:
🟢 BLUE / CONTRASTIVE-JUDGMENT-EXAMPLE-CREATED
+
🟢 BLUE / ORDINARY-GO-VS-V13-CAP-SHOWN
+
🟢 BLUE / JUDGMENT-DIFFERENCE-NOT-JUST-FOOTER
+
🟡 YELLOW / PUBLIC-VALUE-STILL-NOT-PROVEN
+
🟡 YELLOW / REAL-EXTERNAL-CONTRAST-STILL-NEEDED

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The example shows a concrete judgment difference: an ordinary agent likely continues polishing, while V13 caps the next loop to evidence collection.

Next Loop Command:
Run one real external contrast later, or stop if the example is only for internal validation.
