# Prototype Status

## Current Signal

- 🟢 BLUE / MANUAL-PROTOTYPE-MAINTAINED
- 🟡 YELLOW / FEATURE-GROWTH-HOLD
- 🟡 YELLOW / PUBLIC-EXPOSURE-HOLD
- 🔴 RED / RUNTIME-AUTOMATION-BLOCK

## Current State

V13 LoopKit remains prototype-bound and manually governed.

However, it is no longer only a prompt collection.

It now includes reusable manual governance surfaces for AI-agent
restartability, handoff, mistake memory, launch boundaries, and current-state
transfer, plus the local read-only V13 Runner v0.2.

The exact-ref `uvx` distribution surface lets a user launch that unchanged
Runner against a local Git repository. Tool transport may contact GitHub and
package infrastructure; after launch, the Runner scan remains local and
read-only.

It is currently usable for:

- V12 to V13 handoff review
- post-completion GO / HOLD / CAP / BLOCK judgment
- next-action confidence checks
- restartability checks
- handoff responsibility transfer
- manual reconnection packet creation
- bounded field-note proof-of-use
- local read-only repository scanning with Runner v0.2
- exact-ref `uvx` distribution of the unchanged Runner

## Current Manual Surfaces

Current reusable surfaces include:

- README first-use path
- copy-paste prompts
- `AGENTS.md` / `CLAUDE.md`
- `MISTAKEN.md`
- `handoff/current_codex_handoff.md`
- `templates/v13_reconnection_packet_template.md`
- field notes
- launch capsules
- acceptance audit records
- V13 Runner v0.2 CLI
- exact-ref `uvx` distribution surface

## Boundary

Still not a runtime.

Still not an execution engine.

Still no hooks / MCP / pluginization.

Still no runtime service, server, telemetry, remote scan, or automatic
execution.

Human keeps the Seat.

## Feature Growth Status

Feature growth is currently paused.

This does not mean the project is stopped.

It means the next improvement should come from concrete observed need, restartability repair, or current-surface reconciliation, not from adding more product surface.

The existing Runner CLI and package setup are historical completed work. Their
existence is not prohibited by this status, and it does not grant authority for
a new Runner version or another CLI or package change.

Do not add without a separate explicit gate:

- server
- runtime service
- runtime automation
- hooks
- MCP
- pluginization
- execution engine
- telemetry
- remote scan
- automatic execution
- broader promotion

Unapproved feature growth remains on HOLD.

## Public Exposure Status

Public exposure remains on HOLD / CAP.

Do not treat weak public reaction as invalidation.

Do not broaden promotion from this status file.

## Next Loop Command

Use V13 LoopKit on one bounded AI-assisted task completion or handoff-sensitive closure.

If restartability matters, use:

```text
templates/v13_reconnection_packet_template.md
```

In one line:

> Keep the prototype manual, preserve restartability, and use the reconnection packet before handing off state.
