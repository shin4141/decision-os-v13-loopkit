# Field Note 078: Precondition Delta Extraction Template

Date: 2026-06-15

## Purpose

This note defines a small reusable template for extracting a Precondition Delta from a failure or failure cluster.

The purpose is to:

- turn a failure or failure cluster into a short pre-run guard
- avoid reading all mistakes every time
- avoid bloating `AGENTS.md`
- place the extracted condition only before the relevant task type

This is a template note only.

It does not modify README, AGENTS, docs, schema, examples, prompts, USE_CASES, handoff files, public surfaces, canonical surfaces, automation, hooks, MCP, pluginization, package/server/CLI surfaces, release state, or external repos.

## Template

```md
## Precondition Delta Extraction

Task type:
- ...

Failure:
- ...

Failure cluster:
- ...
- ...
- ...

Missing precondition:
- ...

Precondition Delta:
- ...

Task-Scoped Wedge:
- ...

Gate triggers:
- CAP if ...
- HOLD if ...
- BLOCK if ...

Placement:
- Read before ...

Evaluation:
- useful / unclear / too heavy / wrong

Promotion:
- MISTAKEN.md only / Task-Scoped Wedge / AGENTS.md candidate / Park
```

## Field Definitions

Task type:

The kind of task where this wedge applies.

Examples:

- README pointer edit
- docs edit
- handoff refresh
- external repo change
- model upgrade test
- multi-agent run
- public copy
- schema edit

Failure:

The concrete incident or observed mistake.

Failure cluster:

Related failures that may share the same missing precondition.

Missing precondition:

The condition that should have been known before execution started.

Precondition Delta:

A short, preferably one-line, statement of the missing precondition.

Task-Scoped Wedge:

The small guard that should be read before the next similar task.

Gate triggers:

The concrete conditions that should force `CAP`, `HOLD`, or `BLOCK`.

Placement:

Where this wedge should be inserted before execution.

Evaluation:

Whether this extraction is:

- useful
- unclear
- too heavy
- wrong

Promotion:

Whether this remains only a field note, becomes a task-scoped wedge, is a future `AGENTS.md` candidate, or should be parked.

## Compression Rule

The Precondition Delta should be as short as possible.

One line is preferred.

It should prevent a class of failures, not merely restate one incident.

It should be placed before execution, not after failure.

It should not become:

- a long lesson
- an article
- a general warning
- a public positioning statement
- an always-on rule by default

The wedge can be slightly longer than the Precondition Delta, but should still stay small enough to read immediately before the relevant task.

## AGENTS.md Promotion Rule

Do not promote immediately.

Promotion to `AGENTS.md` is only considered if the failure is:

- repeated
- high-impact
- broadly relevant
- not task-specific enough for a wedge
- preventable with a small always-on rule

`AGENTS.md` promotion remains:

```text
HOLD
```

unless separately authorized.

## Example Reference

From Field Note 077:

Task type:

```text
README pointer edit
```

Precondition Delta:

```text
This is a pointer edit, not a framing rewrite.
```

Task-Scoped Wedge:

```text
Before a README pointer edit: This is a pointer edit, not a framing rewrite. Add at most one pointer, avoid public/canonical promotion, and stop after the bounded edit.
```

Evaluation:

```text
useful
```

Why this example works:

- one line compresses a broader failure cluster
- it applies only before a specific task type
- it avoids loading the whole mistake history
- it does not require `AGENTS.md` promotion
- it keeps README pointer work bounded

## Boundaries

This is a template note only.

Do not:

- create an actual template file outside `field_notes`
- edit `AGENTS.md`
- edit `README.md`
- edit docs
- edit handoff files
- implement routing
- add automation
- add hooks
- add MCP
- add pluginization
- publish this
- touch external repos

## Gate

V12 State:

```text
PASS
```

Reason:

The extraction template is recorded as field-note residue only, without modifying protected surfaces or creating implementation/routing behavior.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The template is useful enough to test later, but should remain bounded until applied to one non-README example.

## Recommended Next 0.01

If useful:

```text
later test the template on one non-README example
```

If unclear:

```text
revise the template in a separate field note
```

If too heavy:

```text
keep only the README example
```

If wrong:

```text
park Precondition Delta
```

Current recommendation:

```text
stop after recording this extraction template field note
```

No `AGENTS.md` edit is justified.

No README edit is justified.

No docs edit is justified.

No implementation is authorized.

## Stop Condition

Stop after this field note is committed and pushed.

