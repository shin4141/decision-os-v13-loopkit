# Agent Operating Rule

Before generating or changing files, preserve the purpose of this repository:

> This repository exists to convert completed work into governed next-loop decisions.

## V12 → V13 Handoff Discipline

V13 LoopKit starts only after a V12-style completion check.

V12 asks:

> Is the previous work actually complete in a way that the future self or next agent can restart?

V13 asks:

> Given that completion state, should the next loop be run, held, capped, or blocked?

Agents must not jump directly from “task done” to “next loop.”

Before producing a V13 Loop Record, check whether the previous loop has enough completion integrity:

- what changed
- what files or artifacts were created or modified
- what was verified
- what remains unverified
- what assumptions remain open
- how the next agent or future self can restart
- what rollback, pause, or recheck path exists

If completion integrity is missing, do not output GO.

Use one of:

- HOLD if completion is unclear but recoverable through verification
- CAP if one bounded next action can produce the missing evidence
- BLOCK if the prior completion is unsafe, non-restartable, or dependent on hidden assumptions

The V12 output becomes the input condition for V13.

Minimal handoff:

```text
V12 Completion State:
PASS / DELAY / BLOCK / UNKNOWN

Completion Evidence:
<what proves the work is restartable>

Restart Path:
<how the future self or next agent resumes>

Known Gaps:
<what remains unverified or incomplete>

Then produce the V13 Loop Record.
```

## Agent Rule

A V13 gate without a V12 completion state is incomplete.

Do not treat a polished summary as completion.

Do not treat local success as restartability.

Do not treat “done” as evidence.

The agent must preserve the difference between:

- finishing an output
- making the work restartable
- deciding whether the next loop should run

# Do Not Overbuild

Do not build a web app, database, UI, dashboard, or complex CLI unless explicitly requested.

Start with:

- schemas
- examples
- templates
- validation-ready structure

# Output Discipline

Every loop record must preserve:

- previous loop
- residue
- next variable
- Carrier impact
- re-entry capacity
- gate
- cap or recheck condition
- next loop command

# Gate Discipline

Use only:

```text
GO / HOLD / CAP / BLOCK
```

Do not invent additional gate outcomes.

# Safety Rule

If a loop damages Aspire, Carrier, or re-entry capacity, it must not be marked GO.

If uncertainty is high, prefer HOLD or CAP over GO.

# CAP Rule

Many loops are not wrong.
They are only valid under a cap.

CAP must specify a concrete limit:

- money
- time
- exposure
- iteration count
- automation authority
- model cost
- human review burden
- publishing scope

# BLOCK Rule

BLOCK does not mean permanently dead.
It means the current loop form is not admissible.

A BLOCK record should state what must change before reconsideration.
