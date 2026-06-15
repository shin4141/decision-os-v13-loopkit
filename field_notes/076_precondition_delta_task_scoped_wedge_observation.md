# Field Note 076: Precondition Delta / Task-Scoped Wedge Observation

Date: 2026-06-15

## Purpose

This note records the concept of extracting missing preconditions from failure clusters and placing them as short task-scoped wedges before the next similar task.

This is an observation note only.

It does not modify README, AGENTS, docs, schema, examples, prompts, USE_CASES, handoff files, public surfaces, canonical surfaces, automation, hooks, MCP, pluginization, package/server/CLI surfaces, release state, or external repos.

## Trigger

The user observed that AI can often identify risks in overview mode.

During execution, however, the model can become absorbed by the goal and repeat known mistakes.

The user proposed placing known pitfalls before the task begins.

The idea evolved through:

- Risk Guard First
- Pre-Run Wedge
- Precondition Delta
- Task-Scoped Wedge

The underlying pressure:

```text
known failures should shape the next run before execution begins
```

## Core Concept

A failure should not only be recorded as a mistake.

A failure should expose the missing precondition that would have prevented it.

That missing precondition is the Precondition Delta.

The Precondition Delta should be compressed into a short, preferably one-line, task-scoped wedge.

The wedge should be read before the next similar task, not after the failure.

In one line:

```text
convert repeated failure residue into a small pre-run condition that changes the next execution
```

## Definitions

`MISTAKEN.md`:

```text
incident memory / mistake history
```

Model Failure Profile:

```text
model-specific and task-specific failure tendencies
```

Precondition Delta:

```text
the missing precondition revealed by a failure or failure cluster
```

Task-Scoped Wedge:

```text
the short pre-run guard placed before a specific task type
```

`AGENTS.md`:

```text
minimal always-on constitution; promotion target only for repeated, high-impact, broadly relevant failures
```

## Structure

Pipeline:

```text
Failure Cluster
-> Missing Precondition
-> Precondition Delta
-> One-line Task-Scoped Wedge
-> Pre-run placement
-> Safer next loop
```

The wedge is not the whole incident record.

It is the smallest usable precondition extracted from the incident record.

## Why This Matters

Reading all past mistakes every time is too heavy.

Putting everything in `AGENTS.md` bloats the always-on context.

A one-line wedge can prevent a whole cluster of related failures.

This has high cost-effectiveness because it changes the model's behavior before execution starts.

Placement matters.

The wedge must appear before the task, when the model is still in overview/control mode.

If the wedge appears only after execution begins, it may be treated as commentary rather than as a task-shaping precondition.

## Example Wedges

Possible task-scoped wedges:

- "This is a pointer edit, not a framing rewrite."
- "This task may improve discoverability, but must not promote canonical status."
- "Do not optimize for completion speed if verification evidence is missing."
- "If the model version changed, treat the run as CAP until stability is verified."
- "Use agents only for independent packets; keep integration in the parent session."

These are not universal rules.

They are examples of short pre-run conditions that can be attached to the next similar task.

## Promotion Rule

Do not immediately promote every failure to `AGENTS.md`.

First:

```text
record the incident
```

Then:

```text
identify the Precondition Delta
```

Then:

```text
use it as a Task-Scoped Wedge
```

Only if the same failure repeatedly breaks through, or the risk is high-impact and broadly relevant, consider `AGENTS.md` promotion.

`AGENTS.md` promotion remains:

```text
HOLD
```

unless separately authorized.

## Boundaries

This is not:

- an implementation
- an `AGENTS.md` edit
- a README edit
- a docs edit
- a public promotion
- a canonical promotion
- a replacement for verification
- a requirement that every small task read extra context

Use the pattern for tasks that are:

- repeated
- high-impact
- public-facing
- repo-facing
- model-upgrade-sensitive
- multi-agent-sensitive
- handoff-sensitive

## Gate

V12 State:

```text
PASS
```

Reason:

The observation is recorded as bounded field-note residue without modifying always-on, public, canonical, or implementation surfaces.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The concept is useful, but it should stay bounded until tested against one concrete failure cluster or task class.

## Recommended Next 0.01

Stop after recording.

Possible later review:

```text
define a small template for extracting Precondition Delta from one failure
```

No `AGENTS.md` edit is justified yet.

No implementation is justified yet.

Do not convert this into:

- `AGENTS.md` promotion
- README edits
- docs expansion
- public copy
- automation
- hooks
- MCP
- pluginization
- package/server/CLI surfaces

## Stop Condition

Stop after this field note is committed and pushed.

