# Field Note 077: Precondition Delta Example / README Pointer

Date: 2026-06-15

## Purpose

This note applies the Precondition Delta / Task-Scoped Wedge concept from Field Note 076 to one concrete past pattern:

```text
README edits expanding into framing rewrites or public/canonical promotion
```

This is an example extraction only.

It does not modify README, AGENTS, docs, schema, examples, prompts, USE_CASES, handoff files, public surfaces, canonical surfaces, automation, hooks, MCP, pluginization, package/server/CLI surfaces, release state, or external repos.

## Example Target

Task type:

```text
README pointer edit
```

Observed risk:

```text
a small README edit can expand into framing rewrite, public copy, canonical promotion, or explanation bloat
```

The target is not to forbid README pointer edits.

The target is to prevent a bounded pointer task from becoming a broader positioning task.

## Failure Cluster

Failure cluster:

- README edit becomes larger than needed.
- A pointer turns into explanation.
- Discoverability improvement turns into public positioning.
- Canonical/promotion implications appear without authorization.
- Handoff implications may be forgotten after visible entrypoint edits.

Cluster shape:

```text
small visible-entry edit
-> explanatory framing
-> public/canonical pressure
-> wider touch surface
-> missing restart residue
```

## Missing Precondition

Missing precondition that would prevent the cluster:

```text
This task is an entrypoint pointer edit, not a framing rewrite.
```

Why this matters:

- it fixes the edit identity before execution starts
- it separates discoverability from positioning
- it prevents a pointer from becoming public copy
- it reminds the agent to stop after the bounded edit
- it keeps canonical promotion outside the task unless separately authorized

## Precondition Delta

Compressed one-line Precondition Delta:

```text
This is a pointer edit, not a framing rewrite.
```

This line is short enough to be read before a task without loading the full failure history.

## Task-Scoped Wedge

Wedge to read before similar README pointer edits:

```text
Before a README pointer edit: This is a pointer edit, not a framing rewrite. Add at most one pointer, avoid public/canonical promotion, and stop after the bounded edit.
```

This wedge is task-scoped.

It is not a universal AGENTS rule.

It should be used when the task type is specifically a README or visible-entry pointer edit.

## Gate Triggers

Gate triggers for similar work:

- If the edit adds explanatory framing: `CAP`.
- If it touches AGENTS/canonical/public surfaces: `HOLD` or `BLOCK` unless separately authorized.
- If it changes more than the intended pointer surface: `CAP`.
- If the visible entrypoint changed, consider a separate handoff refresh.

Interpretation:

- `CAP` means the task may still be useful, but only under tighter bounds.
- `HOLD` means authorization or evidence is missing.
- `BLOCK` means the edit is unsafe relative to the current task boundary.

## Result Of This Example

Evaluation:

```text
useful
```

Reason:

One line compresses the cluster without requiring the agent to read the whole history of README/public-entry friction.

The wedge is short enough to place before a task, and specific enough to change behavior before execution.

It also preserves the separation between:

- pointer edit
- framing rewrite
- public positioning
- canonical promotion
- handoff refresh

## Boundary

This is only an example extraction.

Do not:

- promote this to `AGENTS.md`
- edit README
- edit AGENTS
- edit docs
- edit handoff files
- create a template yet
- implement routing
- publish this as public copy
- claim this is a proven governance pattern

## Gate

V12 State:

```text
PASS
```

Reason:

The example extraction is recorded as bounded residue, and no protected surface was modified.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The example is useful, but it should remain bounded until tested against another concrete failure cluster or converted into a separately authorized tiny extraction template.

## Recommended Next 0.01

If useful:

```text
later create a tiny extraction template
```

If unclear:

```text
test one more example
```

If too heavy:

```text
keep as field-note-only
```

If wrong:

```text
park the concept
```

Current recommendation:

```text
stop after recording this one example
```

No README edit is justified by this note.

No AGENTS promotion is justified by this note.

No template or implementation is authorized by this note.

## Stop Condition

Stop after this field note is committed and pushed.

