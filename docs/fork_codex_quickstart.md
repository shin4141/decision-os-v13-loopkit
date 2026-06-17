# Fork + Codex Quickstart

This guide is for someone who forks this repo and wants to ask Codex to use V13 without guessing what to read first.

For an interactive first-run walkthrough, ask Codex to read [Codex Tutorial Guide](codex_tutorial_guide.md).

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

## Where to record things

Before or after a task, decide where the residue belongs:

* `field_notes/`: observations, failures, near-misses, and reusable lessons that are not yet canonical.
* `handoff/current_codex_handoff.md`: the current restart point for a future Codex or human session.
* `examples/`: reusable examples that teach a pattern.
* `AGENTS.md`: minimal always-on rules only. Treat promotion to AGENTS.md as HOLD unless separately authorized.
* `README.md`: public entrypoint only. Do not use it as a work log.
* No record: tiny, reversible work with no reusable lesson or restart need.

Before starting a non-trivial task, Codex should state the expected record target:
`none`, `field_note`, `handoff`, `example`, or `AGENTS_candidate_HOLD`.

## When to read each surface

Do not read every surface for every task. Use the smallest surface that matches the current need.

* `AGENTS.md`: read as the always-on rule surface before repo work.
* `README.md`: read when you need the public entrypoint or project positioning.
* `docs/fork_codex_quickstart.md`: read when onboarding a fork user or choosing where residue should go.
* `docs/codex_tutorial_guide.md`: read when the user wants an interactive first-run walkthrough.
* `handoff/current_codex_handoff.md`: read when resuming prior work or checking the current restart anchor.
* `examples/`: read only when a similar reusable pattern is needed.
* `field_notes/`: read only when investigating a related failure, observation, or non-canonical lesson.

If the current task is tiny, reversible, and has no reusable residue, no extra memory surface is required.

## When residue is detected

Do not ask the Owner a heavy open-ended question like "Should I add this?"

When reusable residue is detected, the coding agent should report it with a recommendation level, expected effect, suggested placement, and two choices.

Recommendation levels:

* `Low`: mention in the report only. No record may be needed.
* `Medium`: recording may reduce future re-onboarding cost or prevent a small repeat mistake.
* `High`: recording is likely to improve restartability, safety, or repeated task quality.
* `Owner Approval Required`: needed for `AGENTS.md` promotion, new files, automation, routing, or canonical rule changes.

Use this format:

```text
Detected reusable residue:
<one sentence>

Recommendation:
Low / Medium / High / Owner Approval Required

Expected effect:
<one sentence>

Suggested placement:
handoff / field_notes / examples / docs / AGENTS_candidate_HOLD / no record

Owner choices:
A. Record the minimal residue
B. Skip for now
```

Default placements:

* Current restart need -> `handoff/current_codex_handoff.md`
* Non-canonical lesson, failure, or observation -> `field_notes/`
* Reusable task pattern -> `examples/`
* Onboarding or manual guidance -> `docs/`
* Always-on safety rule -> `AGENTS_candidate_HOLD`
* Tiny reversible task with no reusable lesson -> `no record`

## Start example

Start with:

`examples/cap.v12_handoff_review.json`

It shows a completed AI-assisted handoff review where the work is V12 PASS, but the next loop is V13 CAP because further expansion needs bounds.

## Boundary

This quickstart does not authorize Codex to edit files.
It only helps a fork user start the conversation safely.
