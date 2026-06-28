# Session Size as Context Risk

## Classification

- Artifact type: V13 field note
- Observed in: agent workspace / Codex Desktop operation
- Root layer: V13 Context Risk Modifier / Loop Gate
- Related layers: V11 Active Context Layer, V12 Completion Integrity

## Core Claim

Session size is a Context Risk signal.

A loop can become unsafe not because the task failed, but because the working context can no longer be reliably resumed.

Japanese framing:

```text
セッションサイズはContext Riskである。
タスクが失敗していなくても、作業文脈が安全に再開できないなら、そのループはHOLD/CAP対象になる。
```

## Observation

In Codex Desktop and other agent workspaces, active sessions and rollout histories can grow very large.

Examples include:

- `rollout-*.jsonl` growth
- large session histories
- unreadable or slow active context
- resume failure
- startup failure
- session corruption
- runtime failures such as `RangeError: Invalid string length`

This is not only a UI problem.

It is loop continuation risk.

The task may have succeeded.

The code may be correct.

The artifact may be useful.

But if the working context cannot be loaded, resumed, inspected, or handed off reliably, the loop is no longer safely governable.

## Why This Matters

V13 loop safety depends on more than task correctness.

It also depends on whether the current state can be carried forward without losing the map.

Context Risk is not only cognitive confusion.

It also includes physical and operational context failures:

- oversized logs
- session corruption
- resume failure
- startup failure
- unreadable context
- tool or runtime limits caused by active history size

When the active workspace becomes fragile, continuing the same loop can increase risk even if the immediate task is still moving.

Long work may need to stop before visible failure.

In that case, safe stop, handoff, and compressed residue can matter more than pushing for completion inside the same active session.

## V13 Interpretation

Session size should modify Context Risk.

```text
BLUE:
session is readable and restartable

YELLOW:
session is long, slow, or fragile; handoff/compression recommended

RED:
session cannot be reliably loaded or resumed; continuation is blocked until recovery or handoff
```

If the task itself is successful but the working context is no longer safely restartable, the loop should not remain `GO`.

It should become `HOLD` or `CAP` depending on recoverability and scope.

## V11 Connection

The active session is a workbench, not a ledger.

Long-horizon memory should move from active context into reconnectable residue.

That residue may live in:

- field notes
- handoff files
- docs
- examples
- verification records
- commit history

V11 Active Context Layer should help decide what needs to remain active now and what should become durable, reconnectable memory.

## V12 Connection

Stopping before completion can preserve completion integrity when it protects restartability.

V12 is not only about finishing the visible task.

It also checks whether the next agent or human can restart from the accepted state without guessing.

If session size threatens restartability, pushing further inside the same context may damage the completion line.

In that situation, a safe handoff can be the more complete action.

## Operational Rule

If session size threatens restartability, do not keep pushing the same loop.

Create a handoff, preserve current state, record TODOs, evidence, verification status, and re-entry instructions, then restart from a smaller context.

Minimum closure packet:

- current accepted state
- changed files or artifacts
- unfinished TODOs
- verification results
- known risks
- explicit next safe action
- surfaces not to touch
- re-entry instructions

## Anti-patterns

- treating a successful task output as safe when the session cannot be resumed
- keeping all history inside active context
- waiting until the workspace crashes before writing handoff
- treating session corruption as unrelated to loop safety
- continuing a loop because the task is not yet complete, even when restartability is degrading

## Correct Closure Pattern

When session size becomes a risk:

1. Stop before corruption becomes unrecoverable
2. Record current state
3. Record unfinished TODOs
4. Record verification results
5. Record re-entry instructions
6. Move durable memory to repo/docs/handoff/evidence
7. Resume from a smaller active context

Correct interpretation:

```text
The task did not fail.
The active context became risky.
Therefore the next safe action is handoff/compression, not continued expansion.
```

## Status

This field note records a V13 Context Risk observation.

Do not implement AGENTS guidance, loop skill, automation, or external publication in this commit.

No README change.
No AGENTS.md change.
No CLAUDE.md change.
No docs change.
No loop_skills change.
No external post.
No exposure candidate search.
No Loop Library submission.
