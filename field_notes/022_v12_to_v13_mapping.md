# Field Note 022: V12→V13 Mapping

Date: 2026-06-14

## Observation

V12 and V13 use different state spaces.

V12 reports completion integrity:

```text
PASS / DELAY / BLOCK
```

V13 reports the next-loop gate:

```text
GO / HOLD / CAP / BLOCK
```

Those states are related, but they are not the same decision.

## Problem

Without an explicit mapping, V13 can look like arbitrary label selection.

The common failure is assuming:

```text
V12 PASS = V13 GO
```

That is wrong.

A completed task can still lead to a capped, held, or blocked next loop.

Likewise, incomplete V12 state must prevent V13 from pretending the next loop is ready to run.

## Mapping Principle

V12 does not decide whether the next loop should run.

V12 decides whether the prior completion is restartable enough to become input for V13.

V13 then decides whether the next loop should:

```text
GO / HOLD / CAP / BLOCK
```

The V13 decision must still check:

- touch surface
- owner approval
- scope creep risk
- future AI cost
- the next 0.01
- re-entry capacity
- risky or hidden assumptions

## Mapping Table

### V12 PASS

Prior work is complete, evidenced, and restartable.

V13 may choose:

- GO
- CAP
- HOLD

PASS does not automatically mean GO.

V13 must still check touch surface, owner approval, scope creep risk, future AI cost, and the next 0.01.

### V12 DELAY

Prior work has progress, but evidence, verification, handoff, rollback, or restartability is incomplete.

V13 must not output GO.

V13 should choose HOLD if clarification, verification, or owner intent is needed.

V13 may choose CAP only if one bounded next action can produce the missing evidence or restart handle.

### V12 BLOCK

Prior work cannot be safely treated as complete.

V13 must not output GO.

V13 should choose BLOCK unless there is a safe bounded repair action.

If a repair action exists, V13 may choose CAP with a concrete repair limit.

### V12 UNKNOWN

Completion integrity has not been checked or cannot be reconstructed.

V13 must not output GO.

The next action should be a V12 completion check, handoff reconstruction, or evidence recovery.

Use HOLD if the recovery path is unclear.

Use CAP if one bounded recovery action is clear.

## Gate Implications

GO requires:

- V12 PASS
- safe touch surface
- clear next 0.01
- no approval boundary
- preserved re-entry capacity
- no harmful scope expansion

HOLD is for:

- missing clarity
- missing verification
- missing owner intent
- unresolved mapping input

CAP is for:

- a valid next loop that is useful only under a concrete limit
- a bounded repair action after DELAY, BLOCK, or UNKNOWN
- a completed prior task whose proposed next loop risks scope expansion

BLOCK is for:

- unsafe loops
- non-restartable loops
- approval-required loops
- hidden-assumption-dependent loops
- forbidden touch surfaces

## Examples

### Example 1: V12 PASS but V13 CAP

A UI fix is complete and tested.

V12:

```text
PASS
```

The next suggested action expands into auth/database work.

V13:

```text
CAP
```

The completed task passes, but the next loop must be capped to prevent scope expansion.

### Example 2: V12 DELAY and V13 HOLD

A task summary says done, but verification evidence and rollback path are missing.

V12:

```text
DELAY
```

V13:

```text
HOLD
```

The next loop should not GO. It should wait for verification, or CAP one bounded evidence-recovery action if that action is clear.

## Boundary

This field note does not solve CAP limit selection yet.

It does not define Aspire, Carrier, or Re-entry fully.

It does not consolidate footer axes yet.

It does not modify canonical AGENTS.md yet.

It does not update AGENTS.ja.md, README.md, docs, schemas, examples, prompts, plugin files, CI, or automation.

It does not add features, hooks, skills, MCP, pluginization, automation, or product behavior.

This is the second repaired logic piece after `field_notes/021_required_intermediate_node.md`.

## V13 Signal

Signal:
🟢 BLUE / V12-V13-MAPPING-DEFINED
+
🟢 BLUE / PASS-DOES-NOT-AUTO-GO
+
🟡 YELLOW / CAP-LIMIT-SELECTION-STILL-INCOMPLETE
+
🟡 YELLOW / AGENTS-JUDGMENT-CORE-STILL-INCOMPLETE

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The V12→V13 mapping is now recorded as a bounded field-note-only repair. PASS no longer implies GO, and DELAY/BLOCK/UNKNOWN cannot produce GO.

Next Loop Command:
Proceed to CAP axis and CAP limit selection as the next upstream logic repair.
