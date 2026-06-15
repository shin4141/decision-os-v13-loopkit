# Field Note 067: PreGOAL Gate Architecture Observation

Date: 2026-06-15

## Purpose

This note records the PreGOAL Gate Architecture observation for V13.

This is an observation note only.

It does not modify README, AGENTS, docs, schema, examples, prompts, USE_CASES, handoff files, public surfaces, canonical surfaces, automation, hooks, MCP, pluginization, package/server/CLI surfaces, release state, or external repos.

## Core Observation

GOAL-only execution is fast.

It can also become black-box execution.

A broad goal may complete or fail without exposing which intermediate structures were necessary.

If the GOAL fails, the whole process may require full review because the missing or broken intermediate structure was not isolated.

If the GOAL succeeds, reusable structure may still be lost unless the agent extracts it as residue.

In one line:

```text
GOAL-only execution can hide the reusable architecture between fixed points.
```

## PreGOAL Definition

A PreGOAL is not merely a small task.

A PreGOAL is an unavoidable intermediate fixed point required for the GOAL to become achievable.

It is close to the V13 next 0.01 definition:

```text
the earliest missing required intermediate node
```

Difference:

- next 0.01 names the immediate required node
- PreGOAL architecture names the chain of required fixed points that makes a broad GOAL executable, diagnosable, and reusable

## Why PreGOAL Modules Matter

PreGOAL modules matter because they:

- improve diagnosis
- improve reuse
- improve reproducibility
- improve repair ability
- reduce whole-goal rework
- expose hidden structure between known fixed points

Without PreGOALs, the agent may only report:

```text
GOAL succeeded
```

or:

```text
GOAL failed
```

With PreGOALs, the agent can report:

```text
which fixed point succeeded, failed, needs bounds, or should be reused
```

## Gate Placement

Each PreGOAL should have a V13 gate.

Gate meanings:

- `GO`: reusable and safe to continue
- `CAP`: usable under bounds
- `HOLD`: evidence or validation missing
- `BLOCK`: unsafe, misleading, or debt-producing

The point is not to slow every goal into bureaucracy.

The point is to prevent fast execution from hiding the exact module that created value, risk, or failure.

## Decimal Depth Rule

If a missing structure is discovered between `1.4` and `1.5`, it should be inserted as:

```text
1.41 / 1.42
```

not appended later as a purely chronological note.

This turns failure into structure exposure, not merely reflection.

The discovered structure should be placed where it belongs in the chain of required intermediate nodes.

## Goal-Mode Relation

Codex `/goal` can execute a broad goal.

V13 can ask what PreGOALs must exist before or during that goal.

The compound loop is:

```text
PreGOAL selection
-> PreGOAL execution
-> residue extraction
-> V13 gate
-> next PreGOAL
-> eventual GOAL
```

This does not replace goal-mode execution.

It gives goal-mode execution a diagnosable architecture.

## Example Shape

GOAL:

```text
create a strong product/repo promotion video
```

Possible PreGOALs:

- value extraction
- target reader/viewer selection
- 30-second structure
- narration rule
- visual template
- BGM / rights / cost check
- rendering / error repair
- evaluation
- next 0.01 residue

Example interpretation:

- value extraction may be `HOLD` if the product value is still unclear
- target viewer selection may be `CAP` if only one audience route should be tested
- narration rule may be `GO` if it is reusable across videos
- BGM / rights / cost check may be `BLOCK` if rights or cost are unsafe
- rendering / error repair may be `CAP` if the loop can run only under a fixed attempt limit
- evaluation may be `HOLD` if no success criteria exist
- next 0.01 residue should be extracted before treating the whole GOAL as complete

## Boundaries

This note is observation only.

Do not:

- implement PreGOAL tooling
- add automation
- add hooks
- add MCP
- add pluginization
- add package/server/CLI surfaces
- edit README or public copy
- edit AGENTS.md
- edit AGENTS.ja.md
- edit CLAUDE.md
- edit docs, schema, examples, prompts, USE_CASES, or handoff files
- modify release state
- modify external repos
- promote this to canonical instructions
- claim that this is proven

Promotion requirement:

```text
requires one real `/goal` or goal-like case before promotion
```

## Current Gate

V12 State:

```text
PASS
```

Reason:

The observation is recorded as a bounded field note with explicit boundaries and no public, canonical, implementation, or external surface changes.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The observation may be useful, but it is not proven. It should be tested on one real goal-like task before any promotion, implementation, README edit, AGENTS edit, automation, or public claim.

## Recommended Next 0.01

Recommended next 0.01:

```text
Do not implement.
```

Use one real goal-like task later to test whether PreGOAL gates reduce rework and improve residue quality.

Do not continue concept growth from this note alone.

## V13 Signal

Signal:
BLUE / PREGOAL-GATE-ARCHITECTURE-OBSERVATION-RECORDED
+
BLUE / GOAL-MODE-BLACK-BOX-RISK-NAMED
+
BLUE / PREGOAL-AS-REQUIRED-INTERMEDIATE-FIXED-POINT-DEFINED
+
YELLOW / OBSERVATION-ONLY
+
YELLOW / REAL-GOAL-LIKE-PROOF-REQUIRED
+
YELLOW / NO-IMPLEMENTATION
+
YELLOW / NO-CANONICAL-PROMOTION

V12 State:
PASS

V13 Next Loop Gate:
CAP

Next Loop Command:
Stop after recording this observation. Do not convert it into README edits, AGENTS promotion, automation, examples, or implementation without separate approval.
