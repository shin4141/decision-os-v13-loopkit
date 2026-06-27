# GitHub Conversion and AI-readable Repo Framing

## Observation

A GitHub repo is not used just because it looks useful.

People often see a repo and think:

- useful
- maybe later
- interesting
- seems powerful

But they still do not fork, copy, or apply it.

The missing step is conversion.

Before a user acts, they need to understand:

- what pain this removes
- why they should fork it
- what changes after they fork
- what their own AI should read first
- what first action becomes easier

## Weak framing

V13 can look weak if it is described only as:

- an AI operations OS
- a LoopKit
- a handoff system
- AGENTS.md / Field Notes / Handoff / Loop Gate
- a useful template collection

This can sound impressive but still fail to answer:

```text
What does this do for me today?
```

## Stronger framing

V13 should be framed around the user's cost:

- reduce repeated explanation to AI
- reduce restart friction
- keep AGENTS.md / CLAUDE.md thin
- prevent AI from saying `done` and drifting into the next task
- preserve failures as future decision material
- let the next AI restart faster, lighter, and with less drift

Possible one-line framing:

```text
V13 LoopKit is for people who keep re-explaining context to AI agents.
It leaves behind the state, limits, and next-action gate so the next AI can restart without guessing.
```

Alternative framing:

```text
V13 LoopKit is a performance layer for AI-agent work:
faster restarts, lighter context, less drift, and clearer next-loop decisions.
```

## What the repo should answer

A GitHub repo aimed at AI-agent users should answer near the top:

1. Why use this now?
2. Why fork this?
3. What happens after I fork?
4. What should I ask my AI first?

## AI-readable repo principle

V13 should not only be a repo humans read.

It should be a repo users can fork and ask their own AI to interpret, adapt, and apply.

The intended first action can be:

```text
Read this repo and onboard me.
Explain what I gain from it.
Then tell me the safest first action for my own AI workflow.
```

## Structural lesson from grasp-like repos

Some repos are easier to understand because they show:

- a one-sentence hypothesis
- a clear map of parts
- what the repo is not claiming
- how AI is expected to read and use the repo

V13 can learn from this presentation style without copying the underlying implementation.

For V13, the map can be:

- `AGENTS.md` / `CLAUDE.md`: thin entry / routing layer
- Field Notes: observations, mistakes, and candidate signals
- `MISTAKEN.md`: failures converted into future repair material
- Handoff: restartable state for the next AI/human
- Loop Gate: `GO / HOLD / CAP / BLOCK` decision
- Human Seat: final decision remains with the human
- `copy-paste/`: immediate portable prompts

## Misunderstandings to prevent

V13 is not:

- an autonomous execution engine
- a replacement for human judgment
- a claim that AGENTS.md is bad
- a model-improvement method
- a guarantee that AI work will be correct
- a system for adding endless process

V13 is:

- an exit and restart layer for AI-agent work
- a way to preserve useful context without loading everything
- a way to separate task completion from permission to continue
- a way to make AI work easier to restart, audit, and hand off

## Boundary

Do not rewrite README now.

Do not add new templates now.

Do not create a post now.

Use this note later when README, GitHub conversion, or fork onboarding is explicitly reopened.

## Status

Signal captured.

No README rewrite.
No tutorial change.
No feature expansion.
