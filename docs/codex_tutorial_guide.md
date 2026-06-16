# Codex Tutorial Guide

Use this guide to onboard a fork user to LoopKit like a first-run tutorial.

This is not a theory document, README rewrite, or AGENTS rule. It is an instruction guide for Codex.

## Read First

Before explaining, read:

1. `README.md`
2. `AGENTS.md`
3. `docs/fork_codex_quickstart.md`
4. `examples/README.md`
5. `examples/cap.v12_handoff_review.json`

## Language Behavior

Use the user's language for explanations and menu guidance.

Keep file paths, command-like labels, and gate names unchanged:

- `README.md`
- `AGENTS.md`
- `field_notes/`
- `handoff/current_codex_handoff.md`
- `examples/`
- `GO / HOLD / CAP / BLOCK`
- `PASS / DELAY / BLOCK`

If the user asks in Japanese, present the tutorial menu and explanations in Japanese, while preserving the original English file names and gate labels.

## Start With This Menu

Show the user this menu:

1. What is LoopKit?
2. What problem does it solve?
3. How do V12 and V13 work?
4. What is GO / HOLD / CAP / BLOCK?
5. Where should notes, failures, handoffs, and examples be recorded?
6. How do I run my first small task?
7. How do I avoid bloating AGENTS.md?
8. How do I know whether the next loop should run?

Tell the user they can:

- ask for one topic
- follow the recommended order
- run a tiny guided task

## Recommended First-Run Order

1. Explain the problem in plain language.
2. Explain the repo surfaces.
3. Explain V12 completion reporting.
4. Explain V13 next-loop gating.
5. Explain where to record residue.
6. Run one tiny task.
7. Produce a completion report.
8. Decide the next loop gate.

## Signals and Growth Loop

LoopKit is not only a stop system. It is a growth OS for AI work.

Signals summarize the current loop state:

- BLUE: useful progress or safe continuation
- YELLOW: risk, uncertainty, scope pressure, or cap needed
- RED: stop-level danger or boundary violation

V12 checks whether the last work is restartable.
V13 decides whether the next loop should `GO / HOLD / CAP / BLOCK`.

When used well, LoopKit does not only prevent accidents. It helps each loop leave residue that makes the next run cheaper, safer, or easier to restart.

## Recording Map

Use this map before or after a task:

- `field_notes/`: observations, failures, near-misses, and reusable lessons that are not canonical.
- `handoff/current_codex_handoff.md`: the current restart point for a future Codex or human session.
- `examples/`: reusable examples that teach a pattern.
- `AGENTS.md`: minimal always-on rules only. Treat promotion to AGENTS.md as HOLD unless separately authorized.
- `README.md`: public entrypoint only. Do not use it as a work log.
- No record: tiny, reversible work with no reusable lesson or restart need.

Before starting a non-trivial task, state the expected record target:

```text
none / field_note / handoff / example / AGENTS_candidate_HOLD
```

## Tutorial Boundaries

Do not edit files during the tutorial unless the user explicitly asks.

Do not:

- promote anything to `AGENTS.md`
- rewrite `README.md`
- create new field notes unless the user explicitly asks
- invent new gate outcomes
- use anything other than `GO / HOLD / CAP / BLOCK` for V13

If PreGOAL is mentioned, explain it as an intermediate checkpoint, not a gate outcome.

## Sample User Prompt

```text
Read `docs/codex_tutorial_guide.md` and onboard me to this LoopKit repo.
Start by showing me the menu.
Then recommend the best first path for a fork user.
Do not edit files unless I explicitly approve.
```
