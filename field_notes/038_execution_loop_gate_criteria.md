# Field Note 038: Execution Loop Gate Criteria

Date: 2026-06-14

## Purpose

This note extracts reusable Decision-OS V13 criteria for judging execution loops.

The criteria come from comparing:

- `field_notes/036_execution_loop_audit_readme_polish.md`
- `field_notes/037_execution_loop_audit_test_until_green.md`

The purpose is to clarify that V13 is not anti-loop.

It is a loop-admissibility layer.

## Compared Loops

Compared loops:

1. README Polish Loop

   ```text
   Keep improving the README until it is clearer, more persuasive, and more adoption-ready.
   ```

2. Test Until Green Loop

   ```text
   Run tests, fix failures, and repeat until the test suite passes.
   ```

The two loops both look useful.

V13 gates them differently because their exit conditions, evidence sources, touch surfaces, and debt risks differ.

## README Polish Result

README Polish result:

- ordinary agent tends toward GO because nearby polish feels useful
- V13 returns CAP because "better README" has no concrete exit condition without reader evidence
- CAP axis: Evidence / scope
- debt risk: polishing can hide unproven public value

The problem is not that README polish is bad.

The problem is that "clearer, more persuasive, and more adoption-ready" can become subjective momentum without external evidence.

## Test Until Green Result

Test Until Green result:

- ordinary agent tends toward GO because test status is observable
- V13 can allow conditional GO only when boundaries are clear
- conditions: known test command, failing tests identified, allowed touch surface, rollback path, no weakening tests, no feature creep
- if ambiguity appears, gate shifts to HOLD/CAP/BLOCK

The loop is more GO-compatible because "tests pass" is a concrete exit condition.

But green status is still not permission to cross unrelated boundaries.

## Extracted Gate Criteria

V13 uses the following criteria to judge execution loops:

1. Exit condition clarity
2. Evidence source
3. Touch surface
4. Reversibility / rollback
5. Debt risk
6. Requirement ambiguity
7. Scope creep risk
8. Whether the loop creates delta or hides uncertainty
9. Whether the loop can weaken the measuring instrument
10. Whether the loop preserves future re-entry

These criteria ask whether a loop is admissible, not whether the loop is imaginable.

## GO-Compatible Loop Pattern

A loop may be GO when:

- exit condition is concrete
- evidence is direct
- touch surface is bounded
- rollback exists
- requirement ambiguity is low
- measurement cannot be weakened without approval
- loop output is verifiable
- future re-entry is preserved

GO means the loop can run without an extra cap because the task boundary itself is already safe enough.

## CAP-Compatible Loop Pattern

A loop should be CAP when:

- work may be useful but evidence is incomplete
- exit condition is partially subjective
- touch surface may expand
- public value or adoption readiness is unproven
- next action should be limited to observation, one check, one file, one iteration, or one evidence-gathering step

CAP means the loop is not rejected, but it cannot run freely.

The cap must name the axis and limit.

## HOLD-Compatible Loop Pattern

A loop should be HOLD when:

- the requirement itself is unclear
- the owner decision is missing
- evidence cannot identify the next required node
- proceeding would invent criteria

HOLD means the loop should wait for clarity before execution.

The agent should not invent the missing standard.

## BLOCK-Compatible Loop Pattern

A loop should be BLOCK when:

- it weakens tests or measurement to create success
- it rewrites unrelated behavior
- it converts uncertainty into public claims
- it hides debt as progress
- it violates owner constraints or safety boundaries

BLOCK means the loop is not admissible under current conditions.

The safest next action is not execution.

## What This Fixes

Decision-OS is not anti-loop.

It does not compete with loop galleries by offering more execution templates.

It evaluates loop admissibility.

The difference between README Polish and Test Until Green shows that V13 gates loops by:

- exit clarity
- evidence
- touch surface
- debt risk

This prevents two opposite mistakes:

- blocking all execution loops because they might expand
- allowing all execution loops because they look useful

V13 should do neither.

It should judge the loop.

## Boundary

This is a criteria extraction note only.

Do not modify AGENTS.md yet.

Do not create a loop gallery.

Do not claim public readiness.

Do not broaden into outreach.

Do not add implementation.

Do not route this into AGENTS.md yet.

This note does not modify AGENTS.md, AGENTS.ja.md, README.md, previous field notes, docs, schemas, examples, prompts, CI, automation, or plugin files.

This note does not add features, hooks, skills, MCP, pluginization, automation, outreach, posting, loop galleries, or product behavior.

## V13 Signal

Signal:
🟢 BLUE / EXECUTION-LOOP-GATE-CRITERIA-EXTRACTED
+
🟢 BLUE / README-POLISH-VS-TEST-GREEN-COMPARED
+
🟢 BLUE / V13-NOT-ANTI-LOOP-CLARIFIED
+
🟢 BLUE / LOOP-ADMISSIBILITY-LAYER-DEFINED
+
🟡 YELLOW / DO-NOT-ROUTE-INTO-AGENTS-YET
+
🟡 YELLOW / DO-NOT-BUILD-LOOP-GALLERY
+
🟡 YELLOW / PUBLIC-VALUE-STILL-NOT-PROVEN

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The execution-loop criteria are extracted as a candidate field-note-level judgment anchor, but they have not yet been tested enough to route into AGENTS.md.

Next Loop Command:
Observe whether these criteria should remain field-note level or later become canonical AGENTS routing.
