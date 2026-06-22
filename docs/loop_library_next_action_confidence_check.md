# Next-Action Confidence Check

## Use when

Use this loop when an AI agent finishes a task and wants to continue to the next one.

The goal is to prevent the agent from treating "task complete" as permission to start every visible next idea.

## Goal

Decide whether the next AI loop should run.

The output must be one of:

- `GO`: continue
- `HOLD`: wait because information is missing
- `CAP`: continue only within a narrow limit
- `BLOCK`: do not continue in this form

## Input

Ask the agent to report:

- what changed
- what was verified
- what was not touched
- what remains uncertain
- what the next visible action is
- what could go wrong if the next loop starts now

## Loop

1. State what changed.
2. State what was verified.
3. State what was not touched.
4. Identify missing evidence or uncertainty.
5. Decide `V12 State`: `PASS` / `DELAY` / `BLOCK`.
6. Decide `V13 Next Loop Gate`: `GO` / `HOLD` / `CAP` / `BLOCK`.
7. If the gate is `CAP`, define the exact limit.
8. If the gate is `HOLD` or `BLOCK`, do not start the next task.
9. Output one allowed next action.
10. Stop and wait for the user.

## Copy-paste prompt

```text
Before starting the next task, run a Next-Action Confidence Check.

Report:

- What changed
- What was verified
- What was not touched
- What remains uncertain
- V12 State: PASS / DELAY / BLOCK
- V13 Next Loop Gate: GO / HOLD / CAP / BLOCK
- Reason
- Allowed Next Action
- Not Allowed
- CAP limit, if any

Do not start the next task automatically.
```

## Verifier

The loop passes only if:

- the current task completion is separated from the next-loop decision
- the next action is one concrete action, not a broad direction
- `CAP`, `HOLD`, and `BLOCK` stop uncontrolled expansion
- the agent does not start the next task automatically
- the user keeps final Seat

## Stop condition

Stop after the check is produced.

Do not continue into implementation, refactoring, posting, cleanup, or another loop unless the user explicitly approves.

## Example

```text
What changed:
Updated the tutorial with a first-use prompt.

What was verified:
The file was edited and the handoff was updated.

What was not touched:
README, examples, automation, hooks, MCP, pluginization.

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The current task is complete, but the next visible actions could expand into README rewrite, examples, or posting.

Allowed Next Action:
Run one no-edit onboarding retest.

Not Allowed:
Do not rewrite README.
Do not add examples.
Do not submit externally yet.
Do not start another implementation loop.
```

## Why this helps

AI agents often finish one task and immediately continue into the next visible idea.

This loop adds a small exit gate.

It keeps AI work restartable, limits drift, reduces re-onboarding cost, and prevents "done" from becoming uncontrolled continuation.
