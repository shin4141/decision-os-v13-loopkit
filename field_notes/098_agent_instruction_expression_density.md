# Agent Instruction Expression Density

## Observation

V13 has treated `AGENTS.md` / `CLAUDE.md` risk mainly as a length problem.

That is correct.

Long always-loaded instruction files create costs:

- more context-loading tax
- important rules become buried
- old assumptions remain active
- stale instructions can become context poison
- the AI carries instructions that may not apply to the current task

However, length is not the only factor.

The same number of tokens can produce different behavior depending on how the instruction is written.

## Core insight

```text
AGENTS.md / CLAUDE.md performance depends not only on token length, but on what human activity the AI understands the instruction to represent.
```

A weak instruction may list output requirements.

A stronger instruction tells the AI what human workflow it is performing.

## Example

Weak framing:

```text
After work, report changes, unverified items, and next actions.
```

This is valid, but the AI may treat it as a checklist of output fields.

Stronger framing:

```text
After work, leave a handoff note so the next AI can restart without guessing.
At minimum, include changes, unverified items, and next actions.
```

This gives the AI:

- who the output is for
- why the output exists
- what task it represents
- what success condition matters
- how the next agent will use it

The second version is not only more polite or longer.

It maps the instruction to a recognizable human workflow:

```text
handoff to the next worker
```

## Three performance axes

### 1. Length

Keep always-loaded instructions short.

Longer files increase reading cost and bury important constraints.

### 2. Structure

Do not put everything into `AGENTS.md` / `CLAUDE.md`.

Use them as thin entry points or routers.

Separate:

- always-read rules
- task-specific rules
- historical notes
- parked ideas
- public messaging rules
- dangerous actions requiring human confirmation

### 3. Expression density

Write instructions so the AI can convert them into behavior.

Prefer human-workflow framing over abstract instruction lists.

Examples:

```text
This is a pre-work checklist.
```

```text
This is a handoff note for the next AI.
```

```text
This is not a backpack carried every session.
It is a toolbox opened only when needed.
```

```text
This is not a completion report.
It is a restart note for the next worker.
```

```text
This is not a decision transfer to the AI.
It is a confirmation step that returns the Seat to the human.
```

## Why expression density matters

AI agents often comply with surface instructions.

But better instructions help the AI infer the operating role.

For example:

- checklist
- handoff
- verification
- inspection
- routing
- escalation
- seat return
- source-of-truth check
- restart note

When the role is clear, the AI is more likely to perform the intended action rather than merely fill fields.

## Review questions

When reviewing `AGENTS.md`, `CLAUDE.md`, `CODEX.md`, or `.cursor/rules`, ask:

1. Is this instruction always needed?
2. Does it belong in always-loaded context?
3. Is it duplicated elsewhere?
4. Does it use undefined terms?
5. Does it contain vector conflicts?
6. Does it describe what human workflow the AI should perform?
7. Does it tell the AI who the output is for?
8. Does it explain why the output matters?
9. Does it define when to return the Seat to the human?
10. Could this be clearer as a checklist, handoff, gate, router, or toolbox?

## Good pattern

```text
Short enough to load.
Structured enough to route.
Concrete enough to act.
```

Japanese framing:

```text
短く、分けて、行動に変換しやすい言葉で書く。
```

## Boundary

Do not rewrite `AGENTS.md` now.

Do not rewrite `CLAUDE.md` now.

Do not create new routing machinery now.

Do not create `CONTEXT_INDEX.md` now.

Use this note later when reviewing:

- agent instruction files
- Health Check skill
- AI Agent Workspace Health Check outputs
- paid audit criteria
- README onboarding
- copy-paste templates

## Status

Signal captured.

No AGENTS.md change.
No CLAUDE.md change.
No README change.
No feature expansion.
