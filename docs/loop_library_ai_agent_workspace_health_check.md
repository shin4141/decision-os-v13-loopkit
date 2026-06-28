# The AI-agent workspace health check

## One-line summary

Don't install a framework first. Ask your own AI whether your workspace is restartable.

## What this loop does

This loop checks whether an AI-agent workspace is safe to continue from.

It looks at the repo, recent work, handoff state, source of truth, agent instructions, stale artifacts, and next safe action before asking the AI to continue work.

## Diagnostic principle

Length is not the root cause.

Risk appears when complexity exceeds restartability structure.

A long AI-agent workspace can remain healthy if it has a living source of truth, fresh handoff, accepted state clarity, labeled stale artifacts, and one safe next action.

A short or fragmented workflow can still become unsafe if unresolved state accumulates across many small sessions.

Many records do not equal restartable state if source of truth, accepted state, handoff, and next safe action are unclear.

## When to use

Use this when:

- an AI-agent repo has been worked on for a long time
- the next AI cannot easily restart
- the current source of truth is unclear
- a handoff may be stale or missing
- `AGENTS.md` / `CLAUDE.md` / `CODEX.md` may be bloated or conflicting
- the AI said `done` but the user is not sure
- a project contains old docs, snapshots, tmp files, stale tests, or unclear accepted state
- the user felt something was wrong but could not name it

## Ready-to-use prompt

```text
Read this repo or workspace as an AI-agent workspace.

Do not edit files.

Run an AI-agent workspace health check.

Focus on:
- restartability
- living source of truth
- accepted state / accepted SHA
- current branch safety
- handoff freshness
- stale artifacts
- preview/public/test mismatch
- always-loaded agent instruction quality
- unclear next safe action

Return:

## Overall Signal
🟢 GREEN / 🟡 YELLOW / 🔴 RED

## Short Verdict
One short paragraph.

## Evidence
Only list evidence found in the repo or supplied trace.

## Source of Truth
What appears to be the current living source of truth?
What is unclear or conflicting?

## Handoff Freshness
Fresh / stale / missing / conflicting.

## Agent Instruction Health
Check for:
- always-loaded bloat
- duplicate instructions
- undefined terms
- vector conflicts
- scope leakage
- missing seat-return rules

## Open / Unclosed Items
List unresolved or unclosed items that may make continuation unsafe.

Examples:
- unclear accepted state
- unresolved verdicts
- stale tests
- old artifacts
- branch/public mismatch
- incomplete handoff
- undefined next safe action
- conflicting or unprioritized instructions

## Growth-Path Notes
If GREEN, clarify whether this is disciplined GREEN or low-complexity GREEN.

If this project is expected to grow into long-running AI-agent development, list early choices that can create compounding advantage later.

## Likely Failure Modes
Only list failure modes supported by evidence.

## Safest Next Action Today
One action only.

Do not repair before diagnosis.
Do not continue if source of truth is unclear.
Return the decision to the human when continuation is unsafe or ambiguous.
```

## Output meaning

### 🟢 GREEN

Safe to continue with bounded action under current complexity.

GREEN does not mean future-safe.

If the repo is simple, mark it as low-complexity GREEN and give Growth-Path Notes instead of a repair plan.

### 🟡 YELLOW

Records exist, but the current state needs clarification or reconstruction before blind continuation.

### 🔴 RED

Source of truth, branch state, handoff, accepted state, or next safe action is broken enough that continuation is unsafe.

## Stop condition

This loop stops before repair.

It does not rewrite docs, delete files, change branches, or continue implementation.

The first goal is visibility.

## Relationship to other loops

This loop is the pre-flight check.

- Workspace Health Check: before entering the workspace
- Next-Action Confidence Check: before continuing to the next task
- Restartable Handoff Loop: before exiting or handing off

Simple sequence:

```text
Health Check before work.
Confidence Check before continuation.
Restartable Handoff before exit.
```

## Public takeaway

Long AI-agent development does not become archaeology because it is long.

It becomes archaeology when complexity exceeds the workspace's living source of truth, handoff, verification, and restartability structure.
