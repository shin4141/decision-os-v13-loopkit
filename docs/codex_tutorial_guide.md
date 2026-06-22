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

## What do I get?

LoopKit is not just a checklist.

It helps reduce the hidden cost of AI work.

### 1. Lower restart cost

Each handoff leaves a short recap of what changed, what was verified, what was not touched, and what the next safe action is.

This means the next AI does not have to rediscover the whole context from scratch.

### 2. Less token waste

Without a recap, every new AI session spends tokens re-reading, guessing, and reconstructing prior decisions.

LoopKit keeps the reusable state small and explicit, so the model can spend more reasoning on progress instead of re-onboarding.

### 3. Less drift

LoopKit encourages the user or agent to record the actual reason for a decision, not just the most plausible explanation later.

This reduces the risk that a future AI continues from a false assumption.

### 4. Fewer accidental expansions

V13 separates "the current task is complete" from "the next loop should start."

A task can be V12 PASS while the next loop is still CAP or HOLD.

This prevents the AI from treating "done" as permission to start every visible next idea.

### 5. Smaller agent instructions

AGENTS.md should remain an operating manual, not a dumping ground.

Reusable lessons go to field notes.
Restart context goes to handoff.
Reusable examples go to examples.

The goal is not to add more documentation.

The goal is to make the next AI restart faster, cheaper, and safer.

## First 5-minute use

If you are not sure where to start, do not migrate the whole repo.

Start by asking Codex to attach a V12/V13 report after one small task:

```text
When this task is done, report:

- What changed
- What was verified
- What was not touched
- V12 State: PASS / DELAY / BLOCK
- V13 Next Loop Gate: GO / HOLD / CAP / BLOCK
- Reason
- Allowed Next Action
- Not Allowed

Do not start the next task automatically.
```

If the next gate is CAP or HOLD, keep the next action small.

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
- `BLUE / YELLOW / RED`

If the user asks in Japanese, present the tutorial menu and explanations in Japanese, while preserving the original English file names and gate labels.

## Exact First Response

When the user asks for the LoopKit tutorial, onboarding, or first walkthrough, start by printing this exact menu before explaining anything else:

```md
## LoopKit Tutorial

Basic Tutorial:

1. LoopKitとは？
2. 何の問題を解決するの？
3. V12とV13はどう動くの？
4. GO / HOLD / CAP / BLOCK とは？
5. notes・failures・handoff・examples はどこに記録するの？
6. 最初の小さなタスクはどう実行するの？
7. AGENTS.md を肥大化させないには？
8. 次のループを走らせるべきかどう判断するの？

Power Concepts:

- 🚦 Signals
- 🌱 Growth OS
- 💊 Setup Pill

番号か項目名で選んでください。
おすすめは 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 の順です。
最初に全体像だけ掴みたいなら 1 から始めましょう。
```

After the menu, wait for the user to choose a number or item. Do not explain the full tutorial all at once unless the user asks for the full walkthrough.

Keep this as an on-demand docs surface. Do not promote it to `AGENTS.md`.

## Start With This Menu

Show the user this menu:

Basic Tutorial:

1. What is LoopKit?
2. What problem does it solve?
3. How do V12 and V13 work?
4. What is GO / HOLD / CAP / BLOCK?
5. Where should notes, failures, handoffs, and examples be recorded?
6. How do I run my first small task?
7. How do I avoid bloating AGENTS.md?
8. How do I know whether the next loop should run?

Power Concepts / Advanced Concepts:

- `🚦 Signals`: read the current AI-work state using BLUE / YELLOW / RED.
- `🌱 Growth OS`: turn completions, failures, and residue into cheaper, safer, easier future runs.
- `💊 Setup Pill`: create a small read-only starter pack for using LoopKit in one specified repo.

Tell the user they can:

- ask for one topic
- follow the recommended order
- run a tiny guided task
- choose `🚦 Signals`, `🌱 Growth OS`, or `💊 Setup Pill` as optional but valuable follow-up modules

## Recommended First-Run Order

1. Explain the problem in plain language.
2. Explain the repo surfaces.
3. Explain V12 completion reporting.
4. Explain V13 next-loop gating.
5. Explain where to record residue.
6. Run one tiny task.
7. Produce a completion report.
8. Decide the next loop gate.

## Power Concepts / Advanced Concepts

### Presentation Rule for Power Concepts

When explaining `🚦 Signals`, always pair the canonical labels with visual markers:

- `🟢 BLUE`
- `🟡 YELLOW`
- `🔴 RED`

Do not replace the canonical labels. Use the emoji as a visual prefix.

When explaining `🌱 Growth OS`, keep the `🌱` marker visible in headings or summary lines, because the concept is about turning completions, failures, and residue into future improvement.

Prefer this compact summary when explaining Signals:

```text
🟢 BLUE = useful progress / safe continuation
🟡 YELLOW = risk / uncertainty / CAP or HOLD
🔴 RED = stop-level danger / boundary violation
```

LoopKit is not only a stop system. It is a growth OS for AI work.

`🚦 Signals` summarize the current AI-work state:

- BLUE: useful progress or safe continuation
- YELLOW: risk, uncertainty, scope pressure, or cap needed
- RED: stop-level danger or boundary violation

V12 checks whether the last work is restartable.
V13 decides whether the next loop should `GO / HOLD / CAP / BLOCK`.

`🌱 Growth OS` means LoopKit does not only prevent accidents. It helps each loop leave residue that makes the next run cheaper, safer, or easier to restart.

### 💊 Setup Pill

Use this when the Owner wants to know how to start using LoopKit in a specific repo.

It works like a repo fit check, but the output is only a small read-only starter pack.

Do not scan every repo. Do not edit files. Do not create files. Do not commit.

Read only the smallest useful surfaces and return a compact starter pack:

- repo purpose
- first files to read
- likely boundaries or "do not touch" areas
- suggested Lite Footer
- suggested memory surfaces
- first tiny guided task
- initial V13 recommendation: `GO / HOLD / CAP / BLOCK`

The goal is to reduce first-repo onboarding friction. It is not automation and it is not a replacement for Owner judgment.

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
