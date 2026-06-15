# Fork + Codex Quickstart

This guide is for someone who forks this repo and wants to ask Codex to use V13 without guessing what to read first.

## Ask Codex to read these first

1. `AGENTS.md`
2. `docs/ai_reading_order.md`
3. `examples/README.md`
4. `examples/cap.v12_handoff_review.json`

## Copy-paste request for Codex

```text
Read the following files first:

- AGENTS.md
- docs/ai_reading_order.md
- examples/README.md
- examples/cap.v12_handoff_review.json

Then explain, in simple terms:

1. What V13 can help me decide
2. When to use GO / HOLD / CAP / BLOCK
3. What you must not edit without authorization
4. What output format I should expect after a task
5. How the start example shows completed AI-assisted work -> V12 PASS -> V13 CAP -> bounded next-loop decision

Do not modify files yet.
Do not edit README.md, AGENTS.md, examples, docs, schemas, prompts, or external repos unless I explicitly authorize it.

After reading, return:

- What you understood
- What V13 can help with
- What files you would ask to inspect for my task
- What must not be touched
- V12 State
- V13 Next Loop Gate
- Signals
- Stop condition
```

## What V13 can help with

V13 helps after an AI-assisted task or loop, when the question is not only "is it done?" but:

* should the next loop run?
* should it be capped?
* should it be held until more evidence exists?
* should it be blocked because it may create debt, broaden scope, or damage the repo?

## After a task, ask for reusable residue

After Codex finishes a task, ask it to leave a small reusable residue, not only a completion summary.

Useful residue may include:

* what was changed
* what was not touched
* validation or checks performed
* V12 State
* V13 Next Loop Gate
* why the next loop is GO / HOLD / CAP / BLOCK
* what a future Codex session should read first
* stop condition

This helps the next session restart without rereading the full history.

## Start example

Start with:

`examples/cap.v12_handoff_review.json`

It shows a completed AI-assisted handoff review where the work is V12 PASS, but the next loop is V13 CAP because further expansion needs bounds.

## Boundary

This quickstart does not authorize Codex to edit files.
It only helps a fork user start the conversation safely.
