# Field Note 024: Aspire, Carrier, and Re-entry Operational Definitions

Date: 2026-06-14

## Observation

V13 needs more than V12 completion integrity and CAP limits.

It also needs minimum operational definitions for:

- Aspire
- Carrier
- Re-entry Capacity

Without those definitions, V13 can choose a next loop that is technically bounded but still wrong for the user, too costly for the operator, or hard to resume later.

## Problem

V13 has been using Aspire, Carrier, and Re-entry as important concepts.

But if those concepts are not operational, they can become vibes.

Weak use:

```text
This aligns with Aspire.
```

Better use:

```text
This moves one required node toward the declared target without damaging the operator's capacity or making the next session harder to restart.
```

The missing piece is a minimal set of proxies an agent can actually check.

## Aspire Definition

Aspire is the declared target direction that makes a next loop worth doing.

It answers:

```text
What future state is this loop supposed to move toward?
```

Aspire is not mood, ambition, or generic improvement.

Operational Aspire requires at least:

- a target state
- a current state
- a line between them
- the next required intermediate node

If the target is unclear, V13 should HOLD.

If the next action does not move along the line, V13 should not call it the next 0.01.

## Aspire Proxy Checks

Before allowing a next loop, ask:

1. What target state is this serving?
2. What current state are we starting from?
3. What required intermediate node does this action satisfy?
4. Does this action move along the line or distract from it?
5. Does this action preserve the user's stated priorities?

If the answer is vague, the Aspire proxy is not satisfied.

## Carrier Definition

Carrier is the capacity that carries the loop forward.

It includes the operator's time, attention, energy, money, trust, and future context budget.

Carrier is not only emotional load.

It is the practical ability to keep operating after this loop.

A loop that achieves a local win while damaging Carrier may still be a bad V13 decision.

## Carrier Proxy Checks

Before allowing a next loop, ask:

1. Does this consume disproportionate time, money, attention, or context?
2. Does this create cleanup burden for a stronger model later?
3. Does this increase owner anxiety, ambiguity, or review load?
4. Does this make the next human or AI session easier or harder?
5. Is the operator being asked to carry too many open loops?

If the loop is useful but Carrier risk is real, V13 should usually CAP.

If Carrier cannot support the loop, V13 should HOLD or BLOCK.

## Re-entry Capacity Definition

Re-entry Capacity is the ability for the next human or AI session to resume without reconstructing the whole context.

It answers:

```text
Can the next session restart from here without paying unnecessary recovery cost?
```

Re-entry is harmed when:

- changed files are unclear
- evidence is missing
- rollback or stop points are missing
- next action is vague
- touch surfaces are not named
- risks are hidden
- decisions are scattered across chat only

## Re-entry Proxy Checks

Before treating a loop as complete, ask:

1. Can the next session see what changed?
2. Can the next session see what was verified?
3. Can the next session see what remains risky or unverified?
4. Can the next session see what must not be touched?
5. Can the next session see the single safest next action?
6. Is the restart anchor durable enough?

If re-entry is weak, V12 should lean DELAY.

If a bounded recovery action exists, V13 may choose CAP.

If no recovery path is clear, V13 should HOLD.

## Interaction With 0.01

The next 0.01 must satisfy all three proxy families:

- Aspire: it moves toward the target.
- Carrier: it does not overload the operator or future context budget.
- Re-entry: it leaves the next session restartable.

Small is not enough.

Useful is not enough.

Fast is not enough.

The next 0.01 must be required, aligned, carryable, and restartable.

## Gate Implications

GO:

Use GO only when the next required node is clear, Aspire-aligned, Carrier-safe, and Re-entry-safe.

HOLD:

Use HOLD when Aspire, Carrier, or Re-entry cannot be assessed yet.

CAP:

Use CAP when the next required node is valid but Aspire, Carrier, or Re-entry risk requires a concrete limit.

BLOCK:

Use BLOCK when the loop damages Aspire, exceeds Carrier, or prevents safe Re-entry.

## Examples

### Example 1: Aspire unclear → HOLD

The agent proposes polishing documentation, but the target state is not declared.

V13 should HOLD until the user names what the polish is meant to improve.

### Example 2: Carrier risk → CAP

The next required node is useful, but it would open a broad refactor.

V13 should CAP the loop to one file, one test, or one proof step.

### Example 3: Re-entry weak → DELAY then CAP

The work is mostly done, but changed files and verification evidence are not clear.

V12 should lean DELAY.

V13 may CAP one bounded handoff reconstruction action.

## Boundary

This field note defines minimum operational proxies only.

It does not define the full Aspire system.

It does not define all Carrier psychology or economics.

It does not solve footer consolidation.

It does not modify canonical AGENTS.md yet.

It does not update AGENTS.ja.md, README.md, docs, schemas, examples, prompts, plugin files, CI, or automation.

It does not add features, hooks, skills, MCP, pluginization, automation, or product behavior.

This is the fourth repaired logic piece after:

1. `field_notes/021_required_intermediate_node.md`
2. `field_notes/022_v12_to_v13_mapping.md`
3. `field_notes/023_cap_axis_limit_selection.md`

## V13 Signal

Signal:
🟢 BLUE / ASPIRE-PROXY-DEFINED
+
🟢 BLUE / CARRIER-PROXY-DEFINED
+
🟢 BLUE / REENTRY-PROXY-DEFINED
+
🟡 YELLOW / FOOTER-CONSOLIDATION-STILL-INCOMPLETE
+
🟡 YELLOW / AGENTS-JUDGMENT-CORE-STILL-INCOMPLETE

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
Aspire, Carrier, and Re-entry now have minimum operational proxy checks. They can guide V13 gate selection without yet modifying canonical AGENTS.md or consolidating the footer.

Next Loop Command:
Proceed to footer consolidation as the next upstream logic repair.
