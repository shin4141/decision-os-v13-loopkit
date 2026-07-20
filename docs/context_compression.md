# Context Compression

## Purpose

Context Compression is a lightweight V11-style rule for reducing repeated context loading while preserving restartability.

The goal is not to remember everything.

The goal is to preserve the minimum reconnection anchors needed for the next loop to continue safely.

In one line:

> Compress the context, not the ability to restart.

## Why This Exists

As V13 LoopKit grows, the full working context can become expensive to reread:

- repeated decisions
- old branches
- resolved README repairs
- pushed commits
- earlier public strategy debates
- repeated warnings
- already-closed loops

Reading all of that every time wastes tokens and increases noise.

But compressing too aggressively can remove the anchors needed to restart safely.

Context Compression defines what to preserve and what to deprioritize.

## Relationship to V11, V12, and V13

V11 asks:

> What should be forgotten, compressed, or preserved so future work can reconnect?

V12 asks:

> Is the work complete and restartable?

V13 asks:

> Should the next loop GO, HOLD, CAP, or BLOCK?

Context Compression connects them:

```text
V11: compress context while preserving reconnection
V12: check restartability
V13: decide the next loop
```

## When to Compress

Compress when:

* the handoff becomes long
* the chat/thread becomes difficult to continue
* repeated context is being reread without adding value
* a future agent would need too much reconstruction
* the same decisions are being restated
* the next task does not need the full historical path

Do not compress when:

* the current decision is unresolved
* the next action depends on detailed reasoning not yet captured
* the current failure mode is still unclear
* the operator still needs the full thread for judgment

## Preserve Anchors

A compressed context should preserve:

1. Current goal
2. Current public repository state
3. Latest commit or pushed state
4. Current signal
5. V12 State
6. V13 Next Loop Gate
7. Chat Continuation
8. Self-Repair Diagnostic state
9. Allowed next actions
10. Not allowed actions
11. Current weakest point
12. Highest-EV 0.01 repair
13. Next Loop Command
14. Known mistaken assumptions
15. Open uncertainties

## Known Mistaken Assumptions

Do not compress away important mistakes.

If a mistaken assumption or failed invasion has already been recorded in `MISTAKEN.md`, preserve a short pointer to it in compressed handoffs.

Why:

> A forgotten mistake can become a repeated mistake.

The compressed context does not need to repeat the full failure story.

It should preserve enough to prevent the same failure from silently returning.

## Deprioritize

A compressed context may deprioritize:

* old draft variants
* resolved wording debates
* repeated explanations
* emotional noise not needed for restart
* prior branches that were explicitly closed
* stale implementation ideas
* old public-promotion ideas that are currently capped

Deprioritize does not mean delete.

It means the next agent should not need to reload it unless a related issue reappears.

## Compression Output Format

Use this format:

```text
Context Compression:
KEEP / COMPRESS / HANDOFF

Reason:
<1-2 lines>

Preserve:
- <current goal>
- <current signal>
- <latest pushed state>
- <allowed next action>
- <not allowed action>
- <next loop command>
- <known mistaken assumption pointer if any>

Deprioritize:
- <resolved branch>
- <old draft variants>
- <stale discussion>

Restart From:
<file, commit, handoff, or section>
```

## Compact Restart Surface Mode

Compact Restart Surface Mode replaces unnecessary full-history reload with the minimum decision-relevant state required for the next human or AI to continue safely.

It is a conditional output mode inside the existing Context Compression / Handoff workflow. It is not a new Skill and does not replace the ordinary compression signal or ownership transfer.

### Use This Mode When

* a long or high-context history is becoming expensive to reload
* the next loop needs current operating state rather than full chronology
* a handoff or capsule can preserve restart-equivalent judgment state
* deeper source pointers remain available
* omitted history contains no unresolved rationale that can change the Protected Object, ownership, Gate, authority, or next action

Do not use it when:

* the current decision remains unresolved
* the original rationale is not yet captured
* ownership or authority is unclear
* a high-impact unknown would be compressed away
* the next action depends on detailed evidence missing from the compact surface
* omission would upgrade uncertainty into permission

### Required Operating State

The compact surface must preserve:

* current direction or goal
* Protected Object when it differs from the surface task
* current source of truth
* latest accepted or pushed state
* current Gate
* active ownership
* one Next Authorized Action
* prohibited actions
* unresolved branches that can still change the next action
* exact restart point and required source pointers
* recheck or reopening conditions
* Completion Line
* known mistaken-assumption pointer when relevant

It must also state what was safely omitted or deprioritized, why that material is not required for the current restart, and when full history must be reopened.

Use `UNKNOWN` when a required value cannot be established. A smaller output with missing decision-critical state is not a successful Compact Restart Surface.

### Compact Restart Surface Output

```text
Compact Restart Surface:

Current Direction:
Protected Object:
Current Source of Truth:
Latest Accepted / Pushed State:

Current Gate:
Current Owner:
Next Authorized Action:
Not Authorized:

Unresolved Branches That Can Change the Next Action:
Required Source Pointers:
Restart From:
Reopen Full History If:

Safely Omitted / Deprioritized:
Completion Line:
```

### Compression Accounting — Conditional

Include Compression Accounting only when measurement or required-item retention accounting is materially relevant. It is not a universal footer and is not required for ordinary handoffs.

```text
Compression Accounting:

Source Surface:
Restart-Item Register / Checklist Source:

Full Character Count:
Capsule Character Count:
Character Reduction:

Required Restart Items:
Required Items Retained:

Safely Omitted Material:
Restart From:

Evaluation Scope:
Measurement Status: MEASURED / NOT MEASURED / UNKNOWN
Claim Boundary:
```

Accounting rules:

1. Never invent a reduction percentage.
2. `NOT MEASURED` is a valid ordinary state.
3. Use `MEASURED` only when both Full and Compact character counts were actually measured.
4. Character reduction must not be renamed token reduction.
5. Character reduction must not be presented as time saving or external performance equivalence without separate evidence.
6. `Required Restart Items` must cite a register, checklist, schema, or declared source that fixes the denominator.
7. Required-item retention must not be inferred from fluent similarity.
8. A smaller capsule fails if any decision-critical required restart item is lost.
9. `Safely Omitted Material` must state why the omitted material is unnecessary for the current restart.
10. Reopen full history when the compact surface cannot establish direction, Protected Object, ownership, Gate, authority, binding rationale, or the next safe action.
11. Compression success means less material with restart-equivalent operating state, not merely fewer characters.

### Relationship to Existing V13 Surfaces

* Context Compression decides whether to `KEEP / COMPRESS / HANDOFF`.
* Compact Restart Surface is one output mode used after `COMPRESS` or `HANDOFF` is selected.
* Handoff transfers ownership and next-loop authority.
* Compact Restart Surface reduces the material that must be read for that transfer to remain valid.
* 0.01 Update Check may record reduced restart burden as a future-loop improvement, but does not validate compression by itself.
* V11 owns the underlying reconnectable-forgetting theory.
* V12 owns restartable completion and handoff validity.
* V13 owns activation timing, next-loop connection, Gate, owner, next action, and the decision to reopen full history.

Omission does not itself prove restartability. The mode succeeds only when the compact surface preserves restart-equivalent operating state.

## Gate Meanings

### KEEP

Continue using the current context.

Use when the context is still small, active, and not causing restart risk.

### COMPRESS

Create or update a compressed handoff.

Use when repeated context loading is wasteful but the work can still continue.

### HANDOFF

Stop before the next major loop and create a handoff.

Use when the current context has become too large or too branchy to safely continue without losing restartability.

## Relationship to Chat Continuation

Chat Continuation reports whether the current chat should continue.

Context Compression reports whether the accumulated context should be compressed.

They are related but not identical.

Example:

```text
Chat Continuation:
PREPARE_HANDOFF

Context Compression:
COMPRESS
```

Meaning:

> The current chat can continue for small tasks, but the state should be compressed before the next large loop.

## Current Minimal Rule

For now, V13 LoopKit does not try to detect recursive compression omissions.

Future versions may track information that was repeatedly compressed away but later returned as important.

For now, the rule is simpler:

> Preserve restart anchors and known mistaken assumptions. Compress everything else only after the current loop is safely closed.

## One-Line Rule

Do not keep all context.

Do not forget the ability to restart.

Compress toward reconnection.
