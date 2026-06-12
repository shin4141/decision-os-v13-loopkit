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
- Context Compression Footer
- Roadmap Anchors for meaningful 0.01 selection
- User Roadmap Anchors template for user-defined direction lines
- Plugin Discovery Readiness as a design-only adoption path
- MISTAKEN repair log
- bounded field notes as proof
- OSS community standards

## Compressed Restart Anchors

Current goal:

Use V13 LoopKit as the working OS for AI-agent completion, next-loop gating, handoff durability, context compression, self-repair, failed-assumption repair, and roadmap-anchored 0.01 selection.

Latest public state:

Repository is pushed and restartable from `origin/main` at `464120e Add user roadmap anchors template`.

Release state:

`v0.1.0 — First Operating Prototype` exists and points to `42a1b79 Add community standards`. Current `main` is newer by the plugin discovery readiness note, roadmap anchors note, Self-Repair Diagnostic 002 handoff refresh, and user roadmap anchors template. Do not edit release state unless explicitly instructed.

Current signal:

```text
🟢 BLUE / USER-ROADMAP-TEMPLATE-PUSHED
+
🟢 BLUE / USER-DEFINED-ASPIRE-LINE-ENABLED
+
🟢 BLUE / 0.01-ALIGNMENT-IMPROVED
+
🟢 BLUE / PLUGIN-DISCOVERY-READINESS-PUSHED
+
🟡 YELLOW / PUBLIC-CAP
+
🟡 YELLOW / FEATURE-GROWTH-CAP
+
🟡 YELLOW / PLUGINIZATION-HOLD
+
🟡 YELLOW / V1-HOLD
```

V12 State:

PASS

V13 Next Loop Gate:

CAP

Chat Continuation:

PREPARE_HANDOFF

Context Compression:

COMPRESS

Self-Repair Diagnostic:

GREEN-CANDIDATE

Allowed next actions:

* continue only through concrete exposed gaps
* use real behavior examples
* use user-defined Roadmap Anchors before choosing future 0.01 repairs, model routing, external discovery, or pluginization
* update handoff/compression only when needed
* use `MISTAKEN.md` only when an actual mistaken assumption or failed invasion appears
* bounded public/Star Acquisition planning only if anchored to stars/adoption -> revenue -> enjoy life and based on real behavior, not theory explanation

Not allowed:

* add automation
* add CLI/server/package setup
* add Telegram bot
* add schema changes
* add plugin implementation, `.codex-plugin/`, hooks, or MCP integration
* draft V13 v1.0
* broaden public promotion
* edit GitHub release state without explicit instruction
* fill `MISTAKEN.md` speculatively
* continue large work from full chat history when compressed anchors are available

Known mistaken assumptions:

See `MISTAKEN.md`.

Current relevant lesson:

Do not assume internal clarity equals outside-reader clarity. First-time-reader checks exposed README weaknesses, and the highest-EV repairs were above-the-fold clarity, start-path clarity, Before/After value difference, and pain-first hook.

Restart source:

Start from this file, `AGENTS.md`, `docs/context_compression.md`, `docs/roadmap_anchors.md`, `templates/user_roadmap_anchors.md`, `docs/plugin_discovery_readiness.md`, and `MISTAKEN.md`. Use the full chat only if a missing detail is required for the next concrete task.

Next Loop Command:

Use user-defined Roadmap Anchors before choosing future 0.01 repairs, model routing, external discovery, or pluginization.

## Current Public State

Recent completed and pushed updates include:

- Loop Map design note
- Aspire-Oriented Loop Map
- V13 Lite Footer in `AGENTS.md`
- Lite Footer proof 001 field note
- Lite Footer proof 002 README clarification
- Chat Continuation Footer in `AGENTS.md`
- Context Compression note in `docs/context_compression.md`
- Context Compression Footer in `AGENTS.md`
- Context Compression Proof 001 in `field_notes/011_context_compression_proof_001.md`
- Community standards: `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, and issue templates
- `v0.1.0 — First Operating Prototype` GitHub release at `42a1b79 Add community standards`
- Plugin Discovery Readiness in `docs/plugin_discovery_readiness.md`
- Roadmap Anchors in `docs/roadmap_anchors.md`
- User Roadmap Anchors template in `templates/user_roadmap_anchors.md`
- Self-Repair Diagnostic 002 refreshed this handoff after roadmap/plugin/release/community updates
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
🟢 BLUE / USER-ROADMAP-TEMPLATE-PUSHED
+
🟢 BLUE / USER-DEFINED-ASPIRE-LINE-ENABLED
+
🟢 BLUE / 0.01-ALIGNMENT-IMPROVED
+
🟢 BLUE / PLUGIN-DISCOVERY-READINESS-PUSHED
+
🟡 YELLOW / PUBLIC-CAP
+
🟡 YELLOW / FEATURE-GROWTH-CAP
+
🟡 YELLOW / PLUGINIZATION-HOLD
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
* Context Compression was added as a note and operationalized as a footer.
* README first-use clarity was repaired through outside-reader checks.
* `MISTAKEN.md` now preserves failed invasion and mistaken assumptions as repairable evidence.
* Community standards were added for OSS trust.
* Plugin Discovery Readiness was documented without plugin implementation.
* Roadmap Anchors now define the line for meaningful 0.01 repairs: stars/adoption -> revenue -> enjoy life.
* `templates/user_roadmap_anchors.md` now gives other users a fill-in path for defining their own direction anchors.

Further repo growth should pause unless another exposed gap appears.

## Chat Continuation

PREPARE_HANDOFF

Reason:

The thread accumulated many commits, signals, and reporting rules. It can continue, but a handoff should be prepared before another large task.

## Context Compression

COMPRESS

Reason:

Future large work should restart from compressed anchors instead of rereading full chat history.

Handoff Required:

No for small bounded verification.

Yes before the next large design, implementation, promotion, or v1.0 loop.

## Allowed Next Actions

Allowed:

* Use the next concrete ordinary Codex task to observe whether the V13 Lite Footer and Chat Continuation Footer appear naturally.
* Use V13 LoopKit as the working OS.
* Use user-defined Roadmap Anchors before selecting future 0.01 repairs.
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
* MCP integration
* plugin implementation
* `.codex-plugin/`
* broad promotion
* speculative `MISTAKEN.md` entries
* continuing large work from full chat history when compressed anchors are available
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
Context Compression Loop: COMPRESS / USE ANCHORS BEFORE LARGE WORK
Roadmap Anchors Loop: GREEN / USER_DEFINED / USE BEFORE 0.01 SELECTION
Pluginization Loop: HOLD / DESIGN-CAP ONLY
External Discovery Loop: HOLD UNTIL ANCHORED
Model Routing Loop: DESIGN-CAP
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

Use user-defined Roadmap Anchors before choosing future 0.01 repairs, model routing, external discovery, or pluginization.

Pause broad public promotion and plugin implementation.

Continue only through concrete exposed gaps, real behavior examples, or bounded public/Star Acquisition planning.
