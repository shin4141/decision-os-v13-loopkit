# AGENTS.md / CLAUDE.md Expression Density

## Observation

V13 has often treated `AGENTS.md` / `CLAUDE.md` problems as a length problem.

That is correct.

Long always-loaded instruction files can create:

- higher context-loading cost
- buried important rules
- stale assumptions
- repeated or conflicting instructions
- context poison
- unnecessary instructions loaded into every task

However, length is not the only performance axis.

The same instruction can produce different AI behavior depending on how it is written.

## Core claim

`AGENTS.md` / `CLAUDE.md` performance depends on at least three axes:

1. length
2. structure
3. expression density

## 1. Length

Shorter always-loaded files are usually better.

The goal is not to remove all instruction.

The goal is to avoid making the AI carry rarely used rules, stale project history, one-off procedures, or task-specific instructions into every session.

## 2. Structure

Always-loaded files should behave more like routers than storage dumps.

They should separate:

- always-read rules
- task-specific instructions
- stale or historical notes
- files that require recheck
- files the AI should not trust without confirmation
- actions that require human seat return

This keeps `AGENTS.md` / `CLAUDE.md` thin while still making deeper context reachable.

## 3. Expression density

Instruction quality also depends on whether the AI can convert the instruction into a recognizable work pattern.

Weak form:

```text
After the task, report changes, unverified items, and next actions.
```

This is valid, but the AI may treat it as a generic output checklist.

Stronger form:

```text
After the task, leave a handoff note so the next AI or human can restart without guessing. At minimum, include changes made, unverified items, and the next safe action.
```

This gives the AI:

- who the output is for
- why it exists
- what human work pattern it represents
- what success means
- what failure would cost

The instruction is not just shorter or longer.

It is more behaviorally legible.

## Human-work framing

Agent instructions become stronger when they map abstract commands to concrete human work.

Examples:

```text
This is a pre-work checklist.
```

```text
This is a handoff note for the next AI or human.
```

```text
This is not a completion report. It is a restart memo.
```

```text
This file is a router, not a warehouse.
```

```text
This is not permission for the AI to decide alone. It is a seat-return checkpoint.
```

```text
This is a toolbox to open when needed, not a backpack to carry every session.
```

These forms help the AI understand how to act, not only what to output.

## Why this matters

A short instruction can still be weak if it is abstract, undefined, or detached from the work situation.

A longer instruction can sometimes perform better if it makes the role, recipient, boundary, and success condition clear.

The target is not only brevity.

The target is:

```text
short enough to stay light,
structured enough to route context,
and concrete enough to become action.
```

## Connection to Workspace Health Check

The AI Agent Workspace Health Check should eventually inspect agent instruction quality across these axes:

- is the file too long?
- is it acting as a router or a storage dump?
- are task-specific rules leaking into always-loaded context?
- are terms undefined?
- are instructions duplicated?
- are vectors in conflict?
- do instructions map to concrete human work?
- do they specify when to return the seat to the human?
- do they help the next AI restart?

## Useful distinction

Bad question:

```text
Is AGENTS.md too long?
```

Better question:

```text
Is AGENTS.md short, routed, and behaviorally legible?
```

## One-sentence summary

The performance of `AGENTS.md` / `CLAUDE.md` is not determined only by token count.

It also depends on whether the AI can understand each instruction as a concrete work pattern.

Shorten it, route it, and write it in language that converts into action.

## Boundary

Do not rewrite `AGENTS.md` now.

Do not rewrite `CLAUDE.md` now.

Do not add a new router file now.

Do not create a new skill now.

This note only records the design principle for future V13 agent-instruction audits.

## Status

Signal captured.

No AGENTS.md change.
No CLAUDE.md change.
No README change.
No new skill.
