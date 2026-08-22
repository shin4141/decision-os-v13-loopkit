# Codex Tutorial Guide

Use this guide to onboard a fork user to LoopKit like a first-run tutorial.

This is not a theory document, README rewrite, or AGENTS rule. It is an instruction guide for Codex.

For a user who wants to build external intelligence for their own AI, start
with [`docs/external_intelligence_onboarding.md`](external_intelligence_onboarding.md).
This guide supplies an on-demand framework map; it is not a required sequence.

## Aspire-First Pre-Tutorial

For the current Aspire-First experience for an external Vibe coding beginner, share only:

[`docs/aspire_first_codex_pre_tutorial_participant.md`](aspire_first_codex_pre_tutorial_participant.md)

That file is the single participant-facing share surface for the Aspire-First Codex Pre-Tutorial. The internal canonical and governance surface remains [`docs/aspire_first_codex_pre_tutorial.md`](aspire_first_codex_pre_tutorial.md); do not send its full contents to participants. Do not reconstruct participant instructions from Trial 001 evidence, prior chat drafts, or the historical delta below.

This guide remains the current LoopKit onboarding guide. Its menu and first-response contract are not replaced by the Aspire-First Pre-Tutorial.

## Read First

Before explaining, read:

1. the public purpose, External Intelligence entry, claim boundary, and Fork
   boundary in `README.md`
2. `AGENTS.md`
3. `docs/external_intelligence_onboarding.md`
4. `docs/ai_reading_order.md`
5. `docs/field_note_lifecycle.md`

Briefly disclose which of those files were actually inspectable and which were
not. Give a short repository-grounded orientation before the Quest Board. Do
not turn this disclosure into a long audit or infer missing behavior.

Then read only the surface needed for the selected first structure:

- restart friction -> `docs/fork_codex_quickstart.md` and the current target
  repository's restart surface
- repeated failure -> one relevant failure record or Field Note, not the
  corpus
- instruction bloat -> the target repository's instruction files
- completion/continuation confusion -> the Lite Footer in `README.md`
- worked example requested -> `examples/README.md` and one matching example

For third-party fork onboarding, do not read the upstream
`docs/current_signal.md`, `handoff/current_codex_handoff.md`,
`docs/trajectory/V13_TRAJECTORY.md`, or `validation/` merely to establish the
fork user's current state. Read one of those only when the user asks about the
upstream repository itself or is resuming work whose authority depends on it.

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
- V12 State: PASS / DELAY / BLOCK / UNKNOWN
- V13 Next Loop Gate: GO / HOLD / CAP / BLOCK
- Reason
- Next Authorized Action
- Not Authorized
- Decision Packet Required: yes / no
- Decision Owner
- Completion Line

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
- `PASS / DELAY / BLOCK / UNKNOWN`
- `BLUE / YELLOW / RED`

If the user asks in Japanese, present the tutorial menu and explanations in Japanese, while preserving the original English file names and gate labels.

## First Response Contract

When the user asks for the LoopKit tutorial, onboarding, or first walkthrough,
respond in the user's language and establish these points briefly:

A natural Japanese request such as
`外部知能を使ってみたいんだけど、何から始めればいい？` is an External
Intelligence onboarding trigger in this repository. Unless the user explicitly
asks for model delegation, do not reinterpret it as a request to consult
ChatGPT or install a plugin.

1. Explain from the files actually inspected that external intelligence here
   means governed repository memory and selective reuse, not automatic
   model-weight training.
2. In a few lines, state what was and was not inspectable and the resulting
   evidence boundary. Do not infer missing implementation.
3. The user does not need to adopt the whole system.
4. Show the capability map before asking diagnostic questions, choosing a
   starting structure, or recommending one. Use the matching `English
   first-contact — External Intelligence Quest Board` or `日本語first-contact —
   External Intelligence Quest Board` in
   `docs/external_intelligence_onboarding.md`.
5. Do not require a Fork, clone, repository attachment, Codex project, setup,
   or file change to view the Quest Board. Environment attachment comes only
   after the user receives a repo-grounded Quest explanation or trial and says
   they want the Full Experience.
6. Wait for the user to choose, explore, ask to see everything, say what they
   already use, or request a recommendation. Viewing or choosing does not
   authorize setup or file changes.
7. After that choice, inspect the actual rules, docs, relevant Field Notes, and
   public implementation needed for that Quest before explaining it. Use the
   current conversation and repository to recognize existing instructions,
   memory, handoff, Git, Codex practice, interests, and current friction. Ask
   only for missing facts that would change the next step. Do not use a quiz or
   capability ranking.
8. Recommend at most one starting structure only after the map when the user
   asks what fits, or help use the one they selected. Leave a restart point and
   stop.
9. Treat the exchange as one bounded onboarding task. Do not attach the full
   completion report to every in-progress question; use the canonical report
   when the selected exercise closes or a real blocker ends the task.
10. In a third-party fork, establish the fork's own Decision Owner. Do not
   inherit Shin merely because the upstream canonical repository names him.

For English first contact, preserve the same seven visible areas, the Little
OSI and Little Compactor entry names, evidence and availability boundaries,
free-choice examples, and no-automatic-install statement in the English Quest
Board. Do not replace it with the completion checker, Handoff, Compactor, or
Gate system as the repository's primary interpretation.

For Japanese first contact, do not replace the Quest Board with a preference
question, a handoff exercise, or another preselected structure. Preserve the
seven visible areas `MEMORY / GROW / LIGHTEN / CONTINUE / PROTECT / CONNECT /
GRADUATE`, the `Little OSI` and `Little Compactor` entry names, the multi-AI
`External Intelligence候補があります` idea, the free-choice examples, and the
statement that viewing or choosing does not automatically install anything.
Render the participant-facing Quest Board from
`docs/external_intelligence_onboarding.md`; do not replace it with an
abbreviated six-category summary. Then wait.

The order is:

```text
Read the repository first. Show the map. Deep-read after selection.
```

Do not call the user a beginner without evidence. Observe existing capability
from the conversation after the map. Personal memory such as money, time,
family, priorities, non-negotiables, and decision reasons is as eligible for
External Intelligence candidacy as reusable coding structure.

Before the user selects a Quest, do not modify files, create a handoff, save a
Note, promote a Rule, or begin setup.

If the user asks to graduate from the tutorial, present
`KEEP / MANUAL / REMOVE / NOT NOW`. Graduation is always the user's choice.
Before `MANUAL` or `REMOVE`, show the tutorial-only file changes and obtain
explicit approval. Never delete memory, notes, handoff, reusable intelligence,
rules, or V12/V13 operation as part of tutorial graduation.

Do not treat an unanswered preference question as a repository `HOLD` unless
the missing answer actually blocks a safe read-only next step.

Keep this as an on-demand docs surface. Do not promote it to `AGENTS.md`.

## On-Demand Topic Map

This framework-topic map is separate from the first-contact External
Intelligence Quest Board. Show it only after the Quest Board when the user asks
to see everything or requests the full LoopKit tutorial. Do not present it as
a required order.

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
- run a tiny guided task
- choose `🚦 Signals`, `🌱 Growth OS`, or `💊 Setup Pill` as optional but valuable follow-up modules

The initial Quest Board may also expose Little OSI and Little Compactor as
lightweight entry concepts. The public Little Compactor evidence is a
research-candidate document, not proof of a complete shipped implementation.
Do not turn those names into new products, runtime behavior, schemas, or
performance claims.

## First-Run Loop

1. Inspect the five first-contact repository surfaces and disclose the access
   boundary briefly.
2. Give a short repository-grounded orientation and show the full External
   Intelligence Quest Board.
3. Wait for the user's choice, exploration, or request for a recommendation.
4. Inspect only the additional repository evidence needed for that Quest.
5. Observe the user's current goal, friction, and existing system.
6. Explain only the minimum mental model needed for the choice.
7. Select at most one useful structure or follow the selected Quest.
8. Run one tiny, authorized use of that structure.
9. Leave the restart point and the condition for returning.
10. Offer `🔓 Full Experience — Forkして体感する` only if the user expresses
    interest after the explanation or trial.

Do not introduce another structure merely because it appears next in this
guide.

The tutorial remains in progress between these steps. Close it once, rather
than emitting a full V12/V13 report after each question.

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

This map is not a requirement to create a record. One observation remains an
observation. Promote it only after the evidence and approval conditions in
`docs/field_note_lifecycle.md` are met.

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
Follow the First Response Contract.
First show the External Intelligence Quest Board and wait for my choice.
After I choose, recognize what I already operate. If I ask what fits,
recommend at most one useful starting structure and help me use it once.
Do not edit files unless I explicitly approve.
```

## Forward-Only Delta: Aspire-First Codex Magic Trial 001

Status: historical evidence context / superseded for participant execution by `docs/aspire_first_codex_pre_tutorial_participant.md` and governed by `docs/aspire_first_codex_pre_tutorial.md`.

As-of 2026-07-12, one internal primary-user trial produced the following observed sequence:

```text
Casual answer -> Instant artifact -> One visible change -> Spontaneous idea expansion
```

The central observation was that initial-answer detail was not the useful success signal. Contact with a concrete artifact and one visible change was followed by the user's own next ideas.

This is internal primary evidence only. It is not an external beginner test, confirmed theory, causal proof, or general onboarding claim. It does not change the existing tutorial menu, first-response contract, or tutorial boundaries.

Evidence and preserved artifact:

- `examples/aspire_first_trial_001/trial_record.md`
- `examples/aspire_first_trial_001/index.html`

Do not rerun, generalize, publish, or expand the artifact from this delta alone.
