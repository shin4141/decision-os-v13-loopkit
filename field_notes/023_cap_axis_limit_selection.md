# Field Note 023: CAP Axis and Limit Selection

Date: 2026-06-14

## Observation

V13 uses CAP when the next loop is useful but must not run freely.

Until now, CAP has often meant:

```text
continue only within limits
```

That is true, but incomplete.

The missing piece is how to choose the limit.

## Problem

If CAP does not name the axis and limit, it can become vague permission.

Weak CAP:

```text
Proceed carefully.
```

Better CAP:

```text
Proceed only with one README wording edit. Do not touch AGENTS.md, docs, automation, or examples.
```

CAP must define the boundary that makes the next loop safe enough to run.

## CAP Principle

CAP means:

```text
The next required node is valid, but only under a concrete limit.
```

The limit should be selected from the risk that prevents GO.

Do not choose a limit by habit.

Do not list every possible forbidden action.

Choose the smallest limit that allows the required node while blocking the risk.

## CAP Axis

When V13 chooses CAP, it should name the primary axis being capped.

Common CAP axes:

1. Scope

   The work may proceed, but only inside a narrow task boundary.

2. Touch surface

   The work may proceed, but only on approved files, modules, repo areas, or surfaces.

3. Evidence

   The work may proceed, but only to gather or restore missing proof.

4. Time / effort

   The work may proceed, but only for a bounded attempt or small investigation.

5. Approval

   The work may proceed only up to the point before owner approval is required.

6. Cost / carrier load

   The work may proceed only if it does not consume disproportionate future context, money, attention, or operator energy.

7. Public / external exposure

   The work may proceed only without posting, publishing, deploying, promoting, or changing public state.

8. Implementation

   The work may proceed as documentation, analysis, or proof only, not product behavior.

## Limit Selection Rule

To choose the CAP limit:

1. Identify the Required Intermediate Node.
2. Ask why GO is not safe.
3. Name the risk axis.
4. Set the smallest concrete limit that allows the node.
5. State what remains outside the limit.
6. Stop when the limit is reached.

If no concrete limit can be stated, the gate is not CAP.

It is HOLD if clarification is needed.

It is BLOCK if the only path crosses a forbidden or approval-required boundary.

## CAP Output Shape

A useful CAP should include:

```text
CAP Axis:
<axis>

CAP Limit:
<concrete allowed boundary>

Not Allowed:
- <blocked expansion 1>
- <blocked expansion 2>

Stop Condition:
<when to stop this loop>
```

The limit must be observable.

If the agent cannot tell whether it stayed inside the cap, the cap is too vague.

## Examples

### Example 1: Scope CAP

Required node:

```text
clarify README opening sentence
```

Risk:

```text
README polish expands into broader adoption rewrite
```

CAP:

```text
CAP Axis:
Scope

CAP Limit:
Edit only one opening sentence in README.md.

Not Allowed:
- Rewrite setup
- Add examples
- Modify AGENTS.md

Stop Condition:
Stop after the one-sentence diff is reviewed.
```

### Example 2: Evidence CAP

Required node:

```text
recover missing verification evidence
```

Risk:

```text
agent starts fixing code instead of proving current state
```

CAP:

```text
CAP Axis:
Evidence

CAP Limit:
Run one read-only verification and report the result.

Not Allowed:
- Edit files
- Commit
- Push

Stop Condition:
Stop after the evidence is recorded.
```

### Example 3: Touch Surface CAP

Required node:

```text
repair docs wording
```

Risk:

```text
repo contains deployment, schema, and public surfaces
```

CAP:

```text
CAP Axis:
Touch surface

CAP Limit:
Change README.md only.

Not Allowed:
- Touch schemas
- Touch deployment files
- Touch env, DB, or public paths

Stop Condition:
Stop after README diff is committed or the README gap is not found.
```

## Gate Implications

GO:

Use GO only when the next required node is clear, safe, bounded by the task itself, and does not need an additional cap.

HOLD:

Use HOLD when the required node, risk axis, or owner intent is unclear.

CAP:

Use CAP when the required node is valid and the risk can be controlled by a concrete axis and limit.

BLOCK:

Use BLOCK when the required node crosses a forbidden boundary or cannot be made safe by a concrete cap.

## Boundary

This field note defines CAP axis and CAP limit selection only.

It does not define Aspire, Carrier, or Re-entry fully.

It does not consolidate footer axes.

It does not modify canonical AGENTS.md yet.

It does not update AGENTS.ja.md, README.md, docs, schemas, examples, prompts, plugin files, CI, or automation.

It does not add features, hooks, skills, MCP, pluginization, automation, or product behavior.

This is the third repaired logic piece after:

1. `field_notes/021_required_intermediate_node.md`
2. `field_notes/022_v12_to_v13_mapping.md`

## V13 Signal

Signal:
🟢 BLUE / CAP-AXIS-DEFINED
+
🟢 BLUE / CAP-LIMIT-SELECTION-DEFINED
+
🟡 YELLOW / ASPIRE-CARRIER-REENTRY-STILL-INCOMPLETE
+
🟡 YELLOW / AGENTS-JUDGMENT-CORE-STILL-INCOMPLETE

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
CAP axis and limit selection are now recorded as a bounded field-note-only repair. CAP should name the risk axis and the concrete limit that allows the required node without opening unsafe expansion.

Next Loop Command:
Proceed to Aspire / Carrier / Re-entry operational definitions as the next upstream logic repair.
