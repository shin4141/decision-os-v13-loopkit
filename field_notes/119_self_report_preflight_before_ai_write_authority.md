# Field Note 119 - Self-Report Preflight Before AI Write Authority

## Layer

V13 / Repo Re-entry / AI Write Authority Gate

Adjacent layers:
- V12 Completion Integrity / accepted state and restart path
- V13 Loop Gate / deciding whether write authority is safe
- V14 Resource Justice / preventing repair burden from returning to the human

## Status

```text
V13 intake candidate / implementation HOLD
```

This note records a candidate gate before AI write authority.

It is not Canon yet.

It does not authorize implementation, scanners, tooling, automation, or AGENTS.md promotion.

## Core

Before giving AI write authority over an old or ongoing repo, a state self-report is required before code audit or editing begins.

The preflight asks the repo/workspace to declare enough accepted state for safe AI re-entry.

## Problem

If AI enters a repo and starts editing before accepted state is declared, it may treat stale branches, stale tests, quarantined fixtures, outdated handoffs, or ambiguous source-of-truth files as current truth.

This creates false continuation and returns repair burden to the human operator.

The failure mode is not merely "AI made a bad edit."

The deeper issue is:

```text
AI was granted write authority before the repo declared what state was accepted.
```

## Preflight Fields

Before code audit or editing begins, collect:

- accepted branch
- accepted SHA / last good state
- source of truth
- stale / quarantined tests
- HOLD / BLOCK boundaries
- handoff quality
- do-not-touch areas
- rollback / next safe action

If these cannot be identified, write authority should remain HOLD.

## V13 Interpretation

This is a Loop Gate candidate before AI write authority.

The question is not:

```text
can the AI edit?
```

The question is:

```text
has the repo declared enough state for safe re-entry?
```

Without that declaration, `GO` for edits is premature even if the AI has tool access.

## B Interpretation

B is not primarily an automatic repo scanner.

B is a manual restartability preflight for AI repo re-entry / handoff audit.

It should help identify whether the workspace has enough visible state for a future AI or operator to restart without reconstructing hidden chat context.

## V12 Connection

A handoff is not valid unless the receiving AI can identify:

- accepted state
- missing closure
- restart path

If the receiving AI cannot tell what state is accepted, the handoff is not sufficiently restartable for write authority.

## V14 Connection

If state declaration is missing, repair load and re-explanation burden return to the human.

This is a Resource Justice failure at the repo/context joint.

The human should not have to repeatedly explain:

```text
which branch is real
which tests are stale
which fixtures are quarantined
which handoff is current
which files are source of truth
what must not be touched
```

## Implementation Path

```text
Phase 0: Field Note / intake candidate
Phase 1: convert into B audit card template
Phase 2: test on one owned repo/workspace read-only
Phase 3: only after examples, consider AGENTS.md promotion
Phase 4: only after proven repeated use, consider tooling or automation
```

## Do Not Promote Yet

```text
This is not Canon yet.
Do not update AGENTS.md.
Do not modify B repo.
Do not implement scanner/tooling.
Do not authorize write access.
```

## Current Gate

```text
Field Note documentation: GO
AGENTS.md Canon promotion: HOLD
B repo modification: HOLD
Implementation: HOLD
Scanner/tooling/automation: BLOCK
Public posting/outreach/release: HOLD
```

## Completion Line

Self-Report Preflight Before AI Write Authority is recorded as a V13 intake candidate.

It may guide future B audit-card work, but it does not authorize write access, implementation, tooling, automation, or Canon promotion.
