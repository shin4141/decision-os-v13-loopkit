# Current Codex Handoff - V13 LoopKit

## Repository

`decision-os-v13-loopkit`

Purpose:

V13 LoopKit is a lightweight operating layer for AI-agent work after completion. It helps decide whether the next loop should GO, HOLD, CAP, or BLOCK.

The repository now focuses on:

- V12 completion/restartability signal
- V13 next-loop signal
- Aspire-oriented Loop Map
- V13 Lite Footer
- Chat Continuation Footer
- MISTAKEN repair log
- bounded field notes as proof

## Current Public State

Recent completed and pushed updates include:

- Loop Map design note
- Aspire-Oriented Loop Map
- V13 Lite Footer in `AGENTS.md`
- Lite Footer proof 001 field note
- Lite Footer proof 002 README clarification
- Chat Continuation Footer in `AGENTS.md`
- README first-use clarity repairs from outside-reader checks:
  - pain-first hook
  - explicit first action
  - choose-one start paths
  - Input -> Decision -> Output
  - Before / After agent report
- `AGENTS.md` is the ongoing-project path.
- `prompts/v13_loop_review.md` is the one-off-review path.
- `MISTAKEN.md` is now available as a repair source for mistaken assumptions, failed invasion attempts, and loop decisions that later prove wrong.

Use `MISTAKEN.md` only when an actual mistaken assumption or failed invasion appears. Do not fill it speculatively.

## Current Signal

```text
🟢 BLUE / SELF-REPAIR-GREEN-CANDIDATE
+
🟢 BLUE / README-FIRST-USE-CLARITY-REPAIRED
+
🟢 BLUE / MISTAKEN-REPAIR-LOG-PUSHED
+
🟢 BLUE / V12-HANDOFF-INTENT-PRESERVED
+
🟡 YELLOW / PUBLIC-CAP
+
🟡 YELLOW / FEATURE-GROWTH-CAP
+
🟡 YELLOW / V1-HOLD
```

## V12 State

PASS

Reason:

The repository is clean, pushed, and restartable from the current public GitHub state.

## V13 Next Loop Gate

CAP

Reason:

The main exposed gaps have been addressed for now:

* V13 was too manual, so Lite Footer was added.
* Lite Footer worked in no-edit verification.
* Lite Footer worked in a small real README edit.
* Chat handoff durability was missing, so Chat Continuation Footer was added.
* README first-use clarity was repaired through outside-reader checks.
* `MISTAKEN.md` now preserves failed invasion and mistaken assumptions as repairable evidence.

Further repo growth should pause unless another exposed gap appears.

## Chat Continuation

PREPARE_HANDOFF

Reason:

The thread accumulated many commits, signals, and reporting rules. It can continue, but a handoff should be prepared before another large task.

Handoff Required:

No for small bounded verification.

Yes before the next large design, implementation, promotion, or v1.0 loop.

## Allowed Next Actions

Allowed:

* Use the next concrete ordinary Codex task to observe whether the V13 Lite Footer and Chat Continuation Footer appear naturally.
* Use V13 LoopKit as the working OS.
* Post only envy-inducing behavior/features when a real example appears.
* Record a field note only if a new observed result appears.
* Record a `MISTAKEN.md` entry only if an actual mistaken assumption or failed invasion appears.
* Make a small README or documentation correction only if an exposed gap appears.
* Prepare handoff notes before major continuation.

## Not Allowed

Do not add:

* automation
* CLI
* server
* Telegram bot
* package setup
* dependency manager
* CI
* schema changes
* broad promotion
* speculative `MISTAKEN.md` entries
* V13 v1.0 draft

## Decision Packet Required When

Set `Decision Packet Required: yes` if the next action is:

* irreversible
* public-facing
* monetary
* credential-related
* release-related
* ownership-sensitive
* authority-changing
* likely to broaden project scope

## Current Loop Map

```text
Proof Loop: GO / CAP
Friction Reduction Loop: CAP
Self-Repair Loop: GREEN-CANDIDATE
MISTAKEN Repair Loop: READY / USE ONLY ON REAL FAILURE
Public Loop: CAP
Star Acquisition Loop: HOLD direct promotion / CAP for envy-inducing behavior posts
Feature Growth Loop: HOLD unless exposed gap
V1 Paper Loop: HOLD
Revenue Loop: HOLD
Carrier Recovery Loop: standby
```

## Current Strategy

Do not try to sell the theory directly.

Do not over-explain V13 on X.

Show envy-inducing Codex behavior only, such as:

- Codex no longer only says “done”
- it reports V12 State
- it reports V13 Next Loop Gate
- it reports Chat Continuation
- it identifies the weakest point
- it makes bounded 0.01 repairs
- it records mistaken assumptions so the same failure is less likely to repeat

The goal is not to make a weak artifact look stronger.

The goal is to make the underlying artifact stronger until simplified presentation still feels desirable.

## Next Loop Command

Pause broad public promotion.

Continue development and use V13 LoopKit as the working OS.

Post only envy-inducing behavior/features when a real example appears.

Do not chase reactions.

If a public/invasion attempt fails or exposes a mistaken assumption, record it in `MISTAKEN.md`.
