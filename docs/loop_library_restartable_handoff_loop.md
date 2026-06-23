# The Restartable Handoff Loop

## Use when

Use this when an AI-agent session is ending, context is getting long, or another human/AI may need to continue the work.

## Verify

The next human or AI can restart the work without guessing what happened, what was verified, what is off limits, or what the safest next action is.

## Stop when

The handoff includes current state, evidence, open risks, off-limits scope, and exactly one safe next action, without starting that action.

## Goal

Close the current AI-agent session in a way that makes the next session restartable.

The handoff should preserve enough context to continue, but not so much that it becomes a full transcript dump.

## Run this loop

1. State the current goal.
2. State what changed in this session.
3. State what was verified.
4. State what was not touched.
5. State what remains uncertain or risky.
6. State any off-limits scope.
7. State the last known decision or gate.
8. Name exactly one safe next action.
9. Stop and wait for the user or next agent.

## Copy-paste prompt

```text
Before ending this session, create a Restartable Handoff.

Report:

- Current goal
- What changed
- What was verified
- What was not touched
- What remains uncertain
- Open risks
- Off-limits scope
- Last known decision or gate
- Exactly one safe next action
- What the next AI/human should not assume

Do not start the next action.
Stop after the handoff.
```

## Example

```text
Current goal:
Improve first-time onboarding for a V13 LoopKit repo.

What changed:
Added benefit-first tutorial framing and a first-contact onboarding rule.

What was verified:
The files were updated, committed, pushed, and the working tree was clean.

What was not touched:
README, examples, automation, hooks, MCP, pluginization, execution engine.

What remains uncertain:
Whether a fresh external user will follow the onboarding path without summary drift.

Open risks:
Over-expanding into README rewrites or new examples before retesting.

Off-limits scope:
Do not add automation, hooks, MCP, pluginization, or broad product positioning.

Last known decision or gate:
V12 State: PASS.
V13 Next Loop Gate: CAP.

Exactly one safe next action:
Run one no-edit fresh onboarding retest.

Do not assume:
Do not assume the tutorial works for all Codex sessions until tested in a fresh session.
```

## Why this helps

AI work often fails after the task appears complete.

The next AI or human may not know what changed, what was verified, what remains risky, or what should not be touched.

This loop turns the end of a session into a restartable handoff instead of a context cliff.
