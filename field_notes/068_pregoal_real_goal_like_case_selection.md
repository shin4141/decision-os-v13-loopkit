# Field Note 068: PreGOAL Real Goal-Like Case Selection

Date: 2026-06-15

## Purpose

This note selects one real goal-like case to test the PreGOAL Gate Architecture from Field Note 067.

This is a selection note only.

It does not implement the selected case.

It does not modify README, AGENTS, docs, schema, examples, prompts, USE_CASES, handoff files, public surfaces, canonical surfaces, automation, hooks, MCP, pluginization, package/server/CLI surfaces, release state, or external repos.

## Source Anchor

Source anchor:

```text
field_notes/067_pregoal_gate_architecture_observation.md
```

Field Note 067 observed that GOAL-only execution can become black-box execution unless unavoidable PreGOAL fixed points are identified, gated, and turned into reusable residue.

Promotion requirement from Field Note 067:

```text
requires one real `/goal` or goal-like case before promotion
```

## Candidate 1: Create A 30-Second Video Explaining V13 Fork + Codex Quickstart

GOAL:

```text
Create a 30-second video explaining V13 Fork + Codex Quickstart.
```

Likely PreGOAL modules:

- value extraction
- target viewer selection
- 30-second structure
- narration rule
- visual template
- BGM / rights / cost check
- rendering / error repair
- evaluation
- next 0.01 residue

Expected residue:

- reusable video structure
- narration constraints
- possible visual template
- rights/cost checklist
- evaluation criteria for future media

Risk of scope expansion:

```text
high
```

Reason:

The task can expand into creative production, public-positioning choices, asset selection, voice/narration polish, video rendering, rights checking, and promotion pressure.

Can it be tested inside the repo?

```text
partly
```

Reason:

The PreGOAL structure can be planned inside the repo, but actual video production would create non-repo artifacts and may require tools, assets, and rights decisions.

Risk of README/public/canonical edits:

```text
medium to high
```

Reason:

A promotion video can pressure public copy, README positioning, examples, and canonical claims.

V13 gate tendency:

```text
HOLD / CAP
```

Reason:

The case is real and useful later, but too broad for the first PreGOAL proof. It should stay parked until creative-production bounds, rights/cost constraints, and evaluation criteria are explicit.

Status:

```text
park video generation
```

## Candidate 2: Improve The Fork-User Codex First-Request Path Using Existing `docs/fork_codex_quickstart.md`

GOAL:

```text
Improve the fork-user Codex first-request path using existing docs/fork_codex_quickstart.md.
```

Likely PreGOAL modules:

- identify the current fork-user start state
- inspect `docs/fork_codex_quickstart.md`
- identify what Codex must read first
- identify what Codex can help decide
- identify protected surfaces
- identify expected output format
- identify first example path
- decide whether the current quickstart works as-is or has one bounded gap
- extract reusable PreGOAL residue
- V13 gate the next loop

Expected residue:

- tested PreGOAL chain for a real repo-local goal-like task
- clearer evidence about whether the quickstart is usable as-is
- reusable checklist for future fork-user onboarding reviews
- bounded decision about whether any future edit is needed
- PreGOAL gate proof without public/canonical promotion

Risk of scope expansion:

```text
low to medium
```

Reason:

The case can be reviewed inside the repo and capped to inspection or a later bounded docs-side edit. The main expansion risk is pressure to improve README or broaden onboarding copy, which can be explicitly blocked.

Can it be tested inside the repo?

```text
yes
```

Reason:

The case uses the existing repo-local quickstart file and can be tested without external repos, video tooling, public surfaces, automation, or implementation.

Risk of README/public/canonical edits:

```text
low if capped
```

Reason:

The quickstart already exists as a docs-side file. The proof can be bounded to read-only review or a separately authorized docs-side repair, while README, AGENTS, and public/canonical surfaces remain protected.

V13 gate tendency:

```text
CAP
```

Reason:

This is the safest first PreGOAL proof case because it is real, repo-local, bounded, and aligned with adoption readiness without requiring public copy, canonical promotion, or implementation.

Status:

```text
selected
```

## Candidate 3: Reproduce The V13 First-Use Path From A Fresh Codex/Fork-User Perspective

GOAL:

```text
Reproduce the V13 first-use path from a fresh Codex/fork-user perspective.
```

Likely PreGOAL modules:

- simulate fresh fork-user entry
- identify first file opened
- identify first Codex request
- identify expected Codex output
- inspect examples pointer
- inspect quickstart
- compare README, docs, examples, and AGENTS routes
- identify confusion
- gate whether any public or README edit is needed

Expected residue:

- fresh-perspective usability findings
- possible first-use friction map
- possible evidence for future README or docs repairs
- restartable onboarding review notes

Risk of scope expansion:

```text
medium
```

Reason:

The task is useful, but it may create pressure to edit README, public-entry copy, examples, docs, or AGENTS because first-use path reviews tend to expose surface-level wording gaps.

Can it be tested inside the repo?

```text
yes
```

Reason:

The review can be performed against current repo files.

Risk of README/public/canonical edits:

```text
medium
```

Reason:

Fresh first-use replay is likely to generate README/public-entry edit candidates, and those surfaces currently remain HOLD unless separately authorized.

V13 gate tendency:

```text
CAP
```

Reason:

The case is valid later, but as the first PreGOAL proof it is more likely to reopen README/public-entry pressure than candidate 2.

Status:

```text
keep first-use path replay capped
```

## Selected Case

Selected case:

```text
Candidate 2: Improve the fork-user Codex first-request path using existing docs/fork_codex_quickstart.md.
```

## Why This Is The Earliest Safe Proof Case

Candidate 2 is the earliest safe proof case because it is:

- real
- goal-like
- repo-local
- already bounded by an existing docs-side artifact
- directly connected to adoption readiness
- testable without implementation
- testable without video production
- testable without README/public/canonical edits
- able to produce reusable PreGOAL residue

It tests the PreGOAL architecture against a concrete goal-like workflow while preserving current parked boundaries.

## What Would Be Tested Next

If separately authorized, the next test should ask:

```text
Can the fork-user Codex first-request path be decomposed into PreGOAL modules, gated module by module, and used to decide whether docs/fork_codex_quickstart.md works as-is or has one bounded gap?
```

Potential PreGOAL gates to observe:

- read-first file set: `GO` if complete, `HOLD` if missing
- Codex capability explanation: `GO` if clear, `CAP` if too broad
- must-not-touch boundary: `GO` if explicit, `BLOCK` if unsafe
- output format expectation: `GO` if complete, `HOLD` if unclear
- first example path: `GO` if discoverable
- edit pressure: `CAP` if any improvement is useful but bounded

Expected residue:

- proof of whether PreGOAL gates reduce rework
- proof of whether the quickstart produces reusable structure
- one bounded next-loop decision

## What Must Not Happen Yet

Do not:

- execute candidate 2 yet
- edit `docs/fork_codex_quickstart.md`
- edit README
- edit AGENTS.md
- edit AGENTS.ja.md
- edit CLAUDE.md
- edit docs, schema, examples, prompts, USE_CASES, or handoff files
- modify public or canonical surfaces
- create video assets
- produce a promotion video
- add automation, hooks, MCP, pluginization, package/server/CLI surfaces, or tooling
- modify release state
- modify external repos
- claim PreGOAL architecture is proven
- promote PreGOAL architecture to canonical instructions

## Current Gate

V12 State:

```text
PASS
```

Reason:

The selection is recorded as a bounded field note, compares three candidate goal-like cases, selects one safest proof case, and makes no implementation or protected-surface changes.

V13 Next Loop Gate:

```text
CAP
```

Reason:

Candidate 2 is valid only as a separately authorized bounded proof test. The current note does not authorize implementation, docs edits, README edits, public/canonical changes, automation, pluginization, video production, or external repo changes.

## Recommended Next 0.01

Recommended next 0.01:

```text
Do not execute yet.
```

If separately authorized, run a bounded PreGOAL proof review on candidate 2:

```text
Improve the fork-user Codex first-request path using existing docs/fork_codex_quickstart.md.
```

The test should decompose the case into PreGOAL modules, gate each module, extract residue, and stop before editing unless a separate edit is authorized.

## V13 Signal

Signal:
BLUE / PREGOAL-REAL-GOAL-LIKE-CASE-SELECTION-RECORDED
+
BLUE / THREE-CANDIDATE-GOAL-LIKE-CASES-COMPARED
+
BLUE / CANDIDATE-2-SELECTED-AS-SAFEST-FIRST-PROOF
+
YELLOW / VIDEO-GENERATION-PARKED
+
YELLOW / FIRST-USE-REPLAY-CAPPED
+
YELLOW / NO-IMPLEMENTATION
+
YELLOW / NO-PUBLIC-OR-CANONICAL-PROMOTION

V12 State:
PASS

V13 Next Loop Gate:
CAP

Next Loop Command:
Stop after recording this case selection. Do not execute the selected GOAL-like case without separate approval.
