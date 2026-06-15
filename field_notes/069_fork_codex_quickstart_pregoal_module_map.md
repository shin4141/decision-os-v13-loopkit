# Field Note 069: Fork Codex Quickstart PreGOAL Module Map

Date: 2026-06-15

## Purpose

This note maps the selected goal-like case from Field Note 068 into PreGOAL modules before execution.

Selected case:

```text
Improve the fork-user Codex first-request path using existing docs/fork_codex_quickstart.md.
```

This is a module map only.

It does not execute the selected case.

It does not edit `docs/fork_codex_quickstart.md` or any other protected surface.

## Target GOAL-Like Case

Target:

```text
Improve the fork-user Codex first-request path without broad README/public/canonical edits.
```

The goal-like case should test whether the current quickstart helps a fork user ask Codex to use V13 safely without guessing:

- what to read first
- what V13 can help decide
- what Codex must not touch
- what output format to expect
- where the first example is
- when to stop before edits

## Why PreGOAL Mapping Is Needed

Directly editing the quickstart could hide which part improves comprehension.

For example, a quickstart edit might improve the file, but still fail to show whether the improvement came from:

- the read-first list
- the Codex request wording
- the must-not-touch boundary
- the output format
- the first example link
- the stop condition

PreGOAL modules create:

- diagnosis units
- reuse units
- reproducibility units
- repair units

They reduce whole-goal rework by exposing which unavoidable intermediate fixed point succeeded, failed, needed a cap, or should be reused.

## Candidate PreGOAL Modules

### P1: Identify Fork-User Pain

PreGOAL:

```text
Name the fork user's starting confusion.
```

Initial gate tendency:

```text
GO
```

Reason:

The current quickstart already states that it is for someone who forks the repo and wants to ask Codex to use V13 without guessing what to read first.

Expected residue:

```text
Reusable pain statement: fork user needs a safe first Codex request before editing.
```

### P2: Define What Codex Should Read First

PreGOAL:

```text
List the minimum read-first files.
```

Initial gate tendency:

```text
GO
```

Reason:

The current quickstart lists:

- `AGENTS.md`
- `docs/ai_reading_order.md`
- `examples/README.md`
- `examples/cap.v12_handoff_review.json`

Expected residue:

```text
Reusable read-first bundle for fork-user Codex onboarding.
```

### P3: Define What Codex Can Help With

PreGOAL:

```text
Explain what V13 helps decide after an AI-assisted task or loop.
```

Initial gate tendency:

```text
GO
```

Reason:

The current quickstart says V13 helps decide whether the next loop should run, be capped, be held, or be blocked because it may create debt, broaden scope, or damage the repo.

Expected residue:

```text
Reusable V13 capability summary for fork users.
```

### P4: Define What Codex Must Not Touch

PreGOAL:

```text
Name protected surfaces and authorization boundaries.
```

Initial gate tendency:

```text
CAP
```

Reason:

The current quickstart tells Codex not to edit files yet and not to edit README, AGENTS, examples, docs, schemas, prompts, or external repos unless explicitly authorized.

The boundary is useful, but it may be broad and should remain capped to the current quickstart wording until a real fork-user test shows whether more specificity is needed.

Expected residue:

```text
Reusable must-not-touch boundary for fork-user first requests.
```

### P5: Define Expected Output Format

PreGOAL:

```text
Tell the user what Codex should return after reading.
```

Initial gate tendency:

```text
GO
```

Reason:

The current quickstart asks Codex to return:

- What you understood
- What V13 can help with
- What files you would ask to inspect for my task
- What must not be touched
- V12 State
- V13 Next Loop Gate
- Signals
- Stop condition

Expected residue:

```text
Reusable first-response format for fork-user Codex onboarding.
```

### P6: Connect The Start Example To V12 PASS / V13 CAP

PreGOAL:

```text
Connect examples/cap.v12_handoff_review.json to the core V13 flow.
```

Initial gate tendency:

```text
GO
```

Reason:

The current quickstart says the example shows a completed AI-assisted handoff review where the work is V12 PASS, but the next loop is V13 CAP because further expansion needs bounds.

Expected residue:

```text
Reusable start-example explanation: completed AI-assisted work -> V12 PASS -> V13 CAP -> bounded next-loop decision.
```

### P7: Define Stop Condition Before Edits

PreGOAL:

```text
Make Codex stop after reading and explaining, before modifying files.
```

Initial gate tendency:

```text
GO
```

Reason:

The quickstart request explicitly says:

```text
Do not modify files yet.
```

The Boundary section also says the quickstart does not authorize Codex to edit files.

Expected residue:

```text
Reusable no-edit stop condition for first Codex contact.
```

### P8: Identify Reusable Residue For Future Fork Users

PreGOAL:

```text
Name what structure should remain reusable after the first Codex response.
```

Initial gate tendency:

```text
HOLD
```

Reason:

The current quickstart implies reusable residue, but it does not explicitly ask Codex to identify what part of the response should be reusable for future fork-user tasks.

This may not require an edit yet. It should be tested in a bounded review before changing the quickstart.

Expected residue:

```text
Reusable fork-user onboarding checklist or proof that the current first-response format already creates enough residue.
```

## Decimal Depth Handling

If a missing module is discovered between P2 and P3, record it as:

```text
P2.1
```

not as a late appended module.

Example:

If the read-first set is complete but the transition from reading files to explaining V13 is unclear, the missing structure belongs between P2 and P3:

```text
P2.1: explain why these files are the minimum set
```

Failure should expose structure position, not become a late generic reflection.

## Execution Boundary

This note does not authorize editing:

```text
docs/fork_codex_quickstart.md
```

Future execution requires a separate bounded edit or proof step.

Allowed next execution shape, if separately authorized:

```text
Review the current quickstart against P1-P8 and record which modules are GO / CAP / HOLD / BLOCK.
```

Not allowed in this note:

- implementation
- docs edit
- README edit
- public/canonical promotion
- automation/pluginization
- video production

## Current Gate

V12 State:

```text
PASS
```

Reason:

The selected goal-like case was decomposed into PreGOAL modules with initial gate tendencies, expected residue, decimal-depth handling, and execution boundaries.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The module map is clear enough for one bounded review, but it does not authorize editing the quickstart, docs, README, public surfaces, canonical surfaces, automation, pluginization, or implementation.

## Recommended Next 0.01

Recommended next 0.01:

```text
If separately authorized, run one bounded review of docs/fork_codex_quickstart.md against P1-P8.
```

Do not edit yet.

The next review should answer:

- which PreGOAL modules are already satisfied
- which modules are capped
- which modules are held
- whether P8 needs a future bounded edit
- whether the quickstart works as-is

## Boundaries

This is a module map only.

Do not:

- implement the selected case
- edit `docs/fork_codex_quickstart.md`
- edit README
- edit AGENTS.md
- edit AGENTS.ja.md
- edit CLAUDE.md
- edit docs, schema, examples, prompts, USE_CASES, or handoff files
- modify public or canonical surfaces
- add automation, hooks, MCP, pluginization, package/server/CLI surfaces, or tooling
- modify release state
- modify external repos
- create video assets
- produce a promotion video

## V13 Signal

Signal:
BLUE / FORK-CODEX-PREGOAL-MODULE-MAP-RECORDED
+
BLUE / P1-TO-P8-MODULES-DEFINED
+
BLUE / INITIAL-PREGOAL-GATES-ASSIGNED
+
YELLOW / QUICKSTART-REVIEW-NEXT-ONLY-IF-AUTHORIZED
+
YELLOW / NO-DOCS-EDIT
+
YELLOW / NO-IMPLEMENTATION
+
YELLOW / NO-PUBLIC-OR-CANONICAL-PROMOTION

V12 State:
PASS

V13 Next Loop Gate:
CAP

Next Loop Command:
Stop after recording the PreGOAL module map. Do not execute or edit the quickstart without separate approval.
