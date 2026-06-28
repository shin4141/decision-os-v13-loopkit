# The AI-agent workspace health check

## Suggested category

Evaluation

## One-line summary

Don't install a framework first. Ask your own AI whether your workspace is restartable.

## What this loop does

This loop checks whether an AI-agent workspace is safe to continue from before asking an AI to do more work.

It can be used as a pre-flight check before entering a repo, or as a failure-trace review after a messy AI-agent session.

The goal is not to prove that a healthy chat was fine.

The goal is to identify whether the workspace has a living source of truth, fresh handoff, clear accepted state, labeled stale artifacts, and one safe next action.

It can also name past failure patterns and turn them into next-time prevention conditions.

## When to use

Use this when:

- an AI-agent repo has been worked on for a long time
- the next AI cannot easily restart
- the current source of truth is unclear
- a handoff may be stale, missing, or conflicting
- `AGENTS.md`, `CLAUDE.md`, or `CODEX.md` may be bloated or contradictory
- the AI said `done` but the user felt unsure
- a project contains old docs, snapshots, tmp files, stale tests, or unclear accepted state
- the user felt something was wrong but could not name it

Use this especially on failure traces:

- a past AI-agent accident
- a long session that became hard to continue
- a confusing handoff
- a repeated re-explanation loop
- an unclear `done` state
- a moment where the user sensed something was wrong but could not name it

## Ready-to-use prompt

```text
Read this repo, workspace, or AI-agent session trace as an AI-agent workspace.

Do not edit files.

Run an AI-agent workspace health check.

Focus on:
- restartability
- living source of truth
- accepted state / accepted SHA
- current branch safety
- handoff freshness
- stale artifacts
- preview / public / test mismatch
- always-loaded agent instruction quality
- unresolved or unclosed items
- unclear next safe action

Important:
Length is not the root cause.
Risk appears when complexity exceeds restartability structure.

Many records do not equal restartable state if source of truth, accepted state, handoff, and next safe action are unclear.

This is not a safety badge.
It is a way to turn failure traces into prevention structure.

Return:

## Overall Signal
🟢 GREEN / 🟡 YELLOW / 🔴 RED

## Short Verdict
One short paragraph.

## Evidence
Only list evidence found in the repo, workspace, or supplied trace.

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

This loop is the pre-flight and failure-trace loop.

- Workspace Health Check: before entering the workspace, or after messy history
- Next-Action Confidence Check: before continuing to the next task
- Restartable Handoff Loop: before exiting or handing off

Simple sequence:

```text
Health Check before work.
Confidence Check before continuation.
Restartable Handoff before exit.
```

## Reviewer-facing distinction

The AI-agent workspace health check is a pre-flight Evaluation loop: before asking an AI to continue work, it checks whether the repo is restartable, grounded in a living source of truth, and safe to enter without guessing.

It can also read messy failure traces and convert them into prevention conditions for the next loop.

## Public takeaway

Long AI-agent development does not become archaeology because it is long.

It becomes archaeology when complexity exceeds the workspace's living source of truth, handoff, verification, and restartability structure.
