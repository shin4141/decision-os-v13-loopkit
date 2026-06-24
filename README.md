# Decision-OS V13 LoopKit

![Release](https://img.shields.io/github/v/release/shin4141/decision-os-v13-loopkit?label=release)
![License](https://img.shields.io/github/license/shin4141/decision-os-v13-loopkit)
![Status](https://img.shields.io/badge/status-operating%20prototype-blue)
![No automation](https://img.shields.io/badge/automation-none-lightgrey)
![Human approval](https://img.shields.io/badge/human%20approval-required-orange)

> Good completion reduces future AI cost. Good loops reduce lifetime AI cost.

AI work gets expensive when every session has to rediscover the same context.

LoopKit helps Codex-style workflows reduce that hidden re-onboarding cost: what was done, why it stopped, what must not be touched, where residue belongs, and whether the next loop should run.

It keeps always-on rules small, moves manuals and examples to on-demand surfaces, and records restart points so the next agent does not have to reconstruct everything from scratch.

Before paying for a stronger model, fix the fuel efficiency of your AI workflow.

Decision-OS V13 is a no-install Lite Footer for AI coding sessions:

- V12 checks whether the work is actually complete and restartable.
- V13 checks whether the next loop should `GO`, `HOLD`, `CAP`, or `BLOCK`.
- `AGENTS.md` stays minimal while docs, examples, handoff, and field notes are read only when needed.
- `CAP` prevents small finished tasks from expanding into expensive scope creep.

If this feels abstract, ask your AI to read the [AI Reading Order](docs/ai_reading_order.md) and decide how V13 should fit your repo.

Ask your AI to generate a tutorial from this repo: see [AI_TUTORIAL_CAPSULE.md](AI_TUTORIAL_CAPSULE.md).

## What this is

V13 LoopKit is a copy-paste reporting kit for AI coding agents.

It is designed for workflows where an agent can follow project-level instructions, including Codex, Claude Code, Cursor, Cline, and similar tools.

After an agent says a task is done, LoopKit makes the agent report the completion state and the next-loop gate:

1. whether the task is actually complete and restartable
2. whether the next loop should `GO`, `HOLD`, `CAP`, or `BLOCK`

## Setup

No install is required.

Copy the instruction file that matches your workflow into your project, then ask your agent to follow it when reporting task completion.

Do not start by adding automation, integrations, or product features.

## First, try the Lite Footer

You do not need the full `AGENTS.md` rule set to feel the first benefit.

Ask your AI agent to append this small footer to its final report:

```text
V12 State: PASS / DELAY / BLOCK
V13 Next Loop Gate: GO / HOLD / CAP / BLOCK
Reason:
Next Loop:
```

The footer makes the agent state whether the current task is complete, whether the next loop should run, why, and the single next action.

If that feels useful, copy `AGENTS.md` later.

## Choose one

Use [`AGENTS.md`](AGENTS.md) for Codex or any AI coding agent that reads project-level instruction files.

Use [`CLAUDE.md`](CLAUDE.md) for Claude Code. It is a thin entry point that points back to `AGENTS.md` as the canonical rule set.

Use [Thin CLAUDE.md / AGENTS.md base](copy-paste/claude-md-thin-base.md) when you want a small copy-paste starter for keeping always-loaded agent instructions short.

Use [Next-Action Confidence Check](copy-paste/next-action-confidence-check.md) before letting an AI agent continue into the next task.

Use [Restartable Handoff](copy-paste/restartable-handoff.md) before ending a long AI-agent session.

For fork users using Codex, start here: [Fork + Codex Quickstart](docs/fork_codex_quickstart.md).

Use [`prompts/v13_loop_review.md`](prompts/v13_loop_review.md) when you want a one-off review without adding project-level instruction files.

Use [`templates/user_roadmap_anchors.md`](templates/user_roadmap_anchors.md) when you want V13 to align 0.01 repairs with your own direction line.

## What you get

Instead of only receiving:

```text
Done. I updated the README.
```

you receive a bounded next-loop decision:

```text
V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The README edit is complete, but the next action should stay bounded.

Allowed Next Action:
Push this commit.

Not Allowed:
- Add new features
- Start broad promotion
- Draft v1.0

Next Loop Command:
Push the commit, then pause until the next concrete task or external feedback appears.
```

### Active Signals vs Parked Horizons

V13 does not treat every yellow item as an unfinished task.

Some yellow items are active caps for the current loop.

Others are parked horizons: known future directions that are intentionally not active now.

Example:

```text
Signal:
🟢 BLUE / README-TRUST-BADGES-PUSHED
+
🟢 BLUE / TRUST-SURFACE-IMPROVED
+
🟡 YELLOW / FEATURE-GROWTH-CAP

Parked Horizons:
HOOKS / MCP / PLUGINIZATION / V1
```

This keeps the current loop readable while preserving future directions without letting them invade the present task.

## Observed Codex output from an AGENTS.md verification task

This is not a mock example. It was recorded from a Codex verification task after the repository instructions were read.

```text
V12 State:
PASS

V13 Next Loop Gate:
GO

Reason:
The V13 Lite Footer worked naturally for this ordinary verification report without requiring a full Loop Record. The repo remained unchanged and restartable.

Allowed Next Action:
Use the Lite Footer again on the next small concrete Codex task.

Not Allowed:
- Add automation
- Add CLI/server/package setup
- Draft V13 v1.0

Decision Packet Required:
no

Next Loop Command:
Run one more ordinary task later and confirm the Lite Footer remains useful without becoming too heavy.
```

## Input → Decision → Output

```text
Input:
An AI agent completed a task and proposes another follow-up.

Decision:
CAP

Reason:
The work is useful, but the next loop should run only within fixed limits.

Output:
The next loop may run only as a bounded action, with clear stop conditions.
```

## Before / After

Without LoopKit, an agent may finish a task like this:

```text
Done. I updated the README.
```

That sounds complete, but it does not tell you whether the next loop should run.

With LoopKit, the report adds the completion state, the next-loop gate, the allowed next action, the disallowed actions, and the next command.

The difference is simple:

> LoopKit turns “done” into a restartable decision about what should happen next.

## Gate outcomes

It asks whether the next loop should:

- `GO`: continue
- `HOLD`: wait for more evidence
- `CAP`: continue only within limits
- `BLOCK`: stop because the next loop is unsafe or not useful

## Quick Example

Your agent says a task is done.

Instead of immediately starting the next task, LoopKit asks whether the next loop should run.

### Input

```text
Task completed:
README first-use path clarified.

Evidence:
- README.md changed
- working tree clean
- no new features added

Proposed next action:
Add more examples and promote the repository.
```

### Output

```text
CAP

Reason:
The task is complete and restartable, but the proposed next action expands scope. Continue only with a bounded next step.

Cap:
Push the README clarification.

Not Allowed:
- Add automation
- Add CLI/server/package setup
- Start broad promotion

Next Loop Command:
Push the commit, then pause until the next concrete task or external feedback appears.
```

## When should I use it?

Use it after AI-assisted work such as:

- coding
- writing
- research
- posting
- automation planning

Especially when you are unsure whether to continue, verify, limit, or stop.

## One-off Review

1. Open [`prompts/v13_loop_review.md`](prompts/v13_loop_review.md)
2. Paste the completed work summary
3. Ask for a V13 Loop Record
4. Read the gate
5. Follow the `Next Loop Command`

## What does it prevent?

It prevents jumping from:

> “The task is done”

to:

> “Run the next loop”

without checking whether the work is restartable, bounded, and worth repeating.

## Quick Links

- [`prompts/v13_loop_review.md`](prompts/v13_loop_review.md): copy-paste prompt
- [`USE_CASES.md`](USE_CASES.md): practical use cases
- [`MISTAKEN.md`](MISTAKEN.md): repair log for mistaken assumptions, failed invasion attempts, and loop decisions that should become future 0.01 repairs
- [`docs/context_compression.md`](docs/context_compression.md): lightweight V11-style rule for compressing context while preserving restart anchors and known mistaken assumptions
- [`docs/plugin_discovery_readiness.md`](docs/plugin_discovery_readiness.md): design note for making V13 LoopKit easier for agents to discover, evaluate, and recommend safely
- [`docs/plugin_surface_spec.md`](docs/plugin_surface_spec.md): documentation-only map of possible future plugin skills, commands, non-goals, and Decision Packet requirements
- [`docs/roadmap_anchors.md`](docs/roadmap_anchors.md): rule for giving Codex at least two direction anchors so 0.01 repairs align with the user’s Aspire
- [`templates/user_roadmap_anchors.md`](templates/user_roadmap_anchors.md): fill-in template for defining your own roadmap anchors before asking V13 to choose 0.01 repairs
- [`docs/field_note_types.md`](docs/field_note_types.md): Self-Application, Real-Task Proof, and Public-Exposure Control
- [`docs/self_repair_diagnostic.md`](docs/self_repair_diagnostic.md): pre-invasion check for identifying the weakest point and highest-EV 0.01 repair

## Contributing and safety

See:

- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `.github/ISSUE_TEMPLATE/`

## Prototype Status

Current status: feature growth is paused; real-task proof continues.

See:

- [`docs/prototype_status.md`](docs/prototype_status.md)

## Current Signal

Current operating state:

- proof continues
- feature growth is paused
- public exposure is capped
- V13 v1.0 is on HOLD

See:

- [`docs/current_signal.md`](docs/current_signal.md)

## Loop Map

Loop Map tracks active loop gates across the prototype: proof, feature growth, public exposure, v1.0 readiness, Decision Packet, and ownership-sensitive work.

See:

- [`docs/loop_map.md`](docs/loop_map.md)

## Aspire-Oriented Loop Map

V13 is not only defensive. After basic gates are stable, it can also map whether each loop moves toward a declared Aspire such as adoption, stars, revenue, or operationalization without damaging the Carrier.

See:

- [`docs/aspire_oriented_loop_map.md`](docs/aspire_oriented_loop_map.md)

## Decision Packet

Future direction: V13 LoopKit should eventually produce human-actionable Decision Packets for high-impact or irreversible next-loop decisions.

See:

- [`docs/decision_packet.md`](docs/decision_packet.md)

Decision Packet examples:

- [`docs/decision_packet_examples.md`](docs/decision_packet_examples.md)

## V13 Lite Footer

For ordinary use, humans should not need to manually write full Loop Records. Agents can include a short V13 next-loop footer at the end of each task report.

V13 reports can also include a Chat Continuation signal: `CHAT_CONTINUE`, `PREPARE_HANDOFF`, or `HANDOFF_NOW`, so long-running work does not silently lose restartability.

Agents can also report `Context Compression: KEEP / COMPRESS / HANDOFF` so long-running work can reduce context cost without losing restartability.

See:

- [`AGENTS.md`](AGENTS.md)

## Field Notes

- `field_notes/001_self_application_v13_loopkit.md` — V13 LoopKit applied to itself.
- `field_notes/002_real_task_v13_announcement_post.md` — V13 LoopKit applied to a real public-posting decision.
- `field_notes/003_real_task_after_announcement.md` — V13 LoopKit applied after announcement to prevent reaction-chasing and return to real-task proof.
- `field_notes/004_real_task_v12_handoff_review.md` — V13 LoopKit applied to a concrete AI-assisted repository task: adding V12→V13 handoff discipline.
- `field_notes/005_v13_v1_readiness_review.md` — V13 LoopKit applied to the question of whether V13 should move from v0.2 to v1.0.
- `field_notes/006_external_real_task_review.md` — V13 LoopKit applied to one external concrete AI-assisted task.
- `field_notes/007_external_v13_readme_usability_review.md` — V13 LoopKit applied to an external V13 README usability review.
- `field_notes/008_reader_usability_check.md` — V13 LoopKit applied to a first-time reader usability check.
- `field_notes/009_v13_lite_footer_proof.md` — first proof that the V13 Lite Footer appeared naturally in an ordinary Codex report.
- `field_notes/010_self_repair_diagnostic_001.md` — first diagnostic run before the next Aspire-invasion move.
- `field_notes/011_context_compression_proof_001.md` — first proof that compressed handoff anchors restarted a later Codex chat successfully.
- `handoff/current_codex_handoff.md` — current restartable handoff for Codex-side V13 LoopKit state.

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

V13 LoopKit assumes V12-style completion integrity: first make the completed work restartable, then decide whether the next loop should GO / HOLD / CAP / BLOCK.

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
