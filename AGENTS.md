# Agent Operating Rule

Before generating or changing files, preserve the purpose of this repository:

> This repository exists to convert completed work into governed next-loop decisions.

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
