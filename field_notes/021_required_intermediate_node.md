# Field Note 021: Required Intermediate Node

Date: 2026-06-14

## Observation

V13 often says "next 0.01" when selecting the next action.

That phrase is useful only if it has an operational definition.

The next 0.01 must not mean any small task.

It must mean the next required step on the path from the current state to the target state.

## Problem

Without a stronger definition, "next 0.01" can drift into:

- whatever task is easiest
- whatever task is most interesting
- whatever the model notices first
- whatever feels like progress
- whatever keeps the loop moving

That is not enough.

A small task can still be wrong if it is not on the required trajectory.

V13 needs a rule that prevents tiny but irrelevant movement.

## Operational Definition

The next 0.01 is:

```text
The earliest missing required intermediate node on the line from the current state to the target state.
```

This definition requires:

1. current state
2. target state
3. a line between them
4. required intermediate nodes that must exist for the line to work
5. the earliest missing node on that line

The next action is not chosen by preference, momentum, or model creativity.

It is chosen by necessity on the path.

## Simple Example

Current state:

```text
woke up
```

Target state:

```text
bought the desired item
```

Known line:

```text
wake up → go shopping → obtain item
```

Required intermediate nodes emerge between them:

- get ready
- take wallet/phone/keys
- travel to store
- check payment method
- withdraw money if payment is missing
- buy item

The next 0.01 is not "research more stores" if the person has not taken wallet/phone/keys.

It is not "buy item" if there is no payment method.

The next 0.01 is the earliest missing required node.

## Line Before Tree

Start with a line, not a full tree.

First identify:

- current state
- target state
- the simplest known line between them

Then fill only the required intermediate nodes that must exist for the line to work.

Branch into a tree only when ambiguity or alternatives appear.

This prevents V13 from expanding into unnecessary planning too early.

## How This Changes V13

V13 should not ask:

```text
What small thing could we do next?
```

V13 should ask:

```text
What is the earliest missing required intermediate node between here and the target?
```

This changes next-loop selection:

- Do not choose an action because it is small.
- Do not choose an action because it is available.
- Do not jump to later nodes when earlier required nodes are missing.
- Do not treat polishing as progress if an entry node is missing.
- Do not treat implementation as progress if the touch surface is not classified.
- Do not treat promotion as progress if the entry path is unclear.

The next 0.01 must be small and required.

## Gate Implications

GO:

The earliest missing required node is clear, safe, and bounded.

HOLD:

The line, target, or required node is unclear.

CAP:

The required node is valid only under a concrete limit.

BLOCK:

The required node crosses a forbidden or approval-required boundary.

If the required node touches a risky surface, approval boundary, or uncertain assumption, V13 should HOLD or CAP, not GO.

## Boundary

This field note does not solve all V13 judgment logic.

It does not define Aspire, Carrier, or the full V12→V13 mapping yet.

It does not update AGENTS.md, AGENTS.ja.md, README.md, docs, prompts, examples, schemas, plugin files, CI, or automation.

It does not add feature implementation, pluginization, hooks, skills, MCP, product behavior, or automation.

This should be used as the first repaired piece before broader AGENTS.md changes.

Do not broaden this loop into pluginization, README changes, or full automation.

## V13 Signal

Signal:
🟢 BLUE / REQUIRED-INTERMEDIATE-NODE-DEFINED
+
🟢 BLUE / NEXT-0.01-OPERATIONALIZED
+
🟡 YELLOW / AGENTS-JUDGMENT-CORE-STILL-INCOMPLETE
+
🟡 YELLOW / DO-NOT-BROADEN-YET

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The Required Intermediate Node rule defines next 0.01 selection as the earliest missing required node on the line from current state to target state, while leaving broader V13 judgment logic for a later bounded repair.

Next Loop Command:
Stop after recording this field note. Next repair should address the next upstream logic gap, not broaden this loop.
