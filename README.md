# Start Here

If an AI agent just finished work and you are not sure what to do next, use V13 LoopKit.

1. Open `prompts/v13_loop_review.md`
2. Paste the completed work summary
3. Ask for a V13 Loop Record
4. Read the gate:
   - GO: continue
   - HOLD: observe before scaling
   - CAP: run only under a fixed limit
   - BLOCK: do not continue in the current form
5. Follow the `Next Loop Command`

## Short Example

Input:
"Codex created README, schema, examples, templates, and use cases."

Output:
CAP

Reason:
The scaffold is useful, but no real user has tried it yet.

Cap:
Ask one user to run the prompt on one real completed AI task. Do not automate outreach.

Next Loop Command:
Run one real V13 review on an AI coding completion and record whether CAP felt useful.

## Field Notes

- `field_notes/001_self_application_v13_loopkit.md` — V13 LoopKit applied to itself.
- `field_notes/002_real_task_v13_announcement_post.md` — V13 LoopKit applied to a real public-posting decision.

# Decision-OS V13 LoopKit

Turns completion records into governed next-loop decisions using GO / HOLD / CAP / BLOCK.

## Conceptual Flow

```text
V12 Completion Record
        ↓
V13 Loop Record
        ↓
GO / HOLD / CAP / BLOCK
        ↓
Next Loop Command
```

## Core Distinction

```text
V12 asks:
Is this work actually complete and restartable?

V13 asks:
Given that completion state, should the next loop be run, held, capped, or blocked?
```

## V13 Canon

```text
Capability without controllability is not intelligence.
```

## Core Principle

```text
A Compound Loop improves the condition from which the next loop begins.
```

## Gate Outcomes

- GO: positive-EV, controllable, residue-producing, Carrier-preserving
- HOLD: sign, cost, residue, or Carrier impact is unclear
- CAP: valid only under fixed exposure limits
- BLOCK: damages Aspire, Carrier, or re-entry capacity

## Practical Use

- Start with [`USE_CASES.md`](USE_CASES.md) for common loop-governance scenarios.
- Copy and paste [`prompts/v13_loop_review.md`](prompts/v13_loop_review.md) after a completed work report to produce a V13 Loop Record.

## Current Status

```text
Status: Prototype scaffold / file-based loop governance kit.
This repository is not a full application yet.
```
