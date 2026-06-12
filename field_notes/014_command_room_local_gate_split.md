# Command Room / Local Gate Split

Date: 2026-06-13

## Context

V13 LoopKit successfully governed a fresh external normal-repo proof.

External repo:

```text
/Users/sn/Projects/decisiongate-triage
```

External proof commit:

```text
0fb42aa Test V13 external docs proof
```

Related V13 field notes:

- `field_notes/012_invalid_target_guard_observation.md`
- `field_notes/013_fresh_external_entrypoint_proof.md`

## Observation

V13 is beginning to function as a manual command-room layer for bounded cross-repo governance.

It is not an automated orchestrator.

It can inspect a target repository, apply a small bounded repair, commit and push, and return with V12/V13 reporting.

When `AGENTS.md` is placed in the external repository, that repository becomes a local worksite with its own repo-level gate.

## Command Room / Local Gate Split

Small repairs can be executed from the V13 command room.

Medium or larger changes must be localized behind a repo-level gate before execution.

小工事はV13から出張修理。

中工事以上は現地にゲートを置いてから施工。

## Small Repair Rule

Small repairs may be handled centrally when they are bounded.

Examples include:

- README wording
- documentation clarification
- small trust-surface wording
- no-behavior-change repository hygiene

The command room may inspect the target repo, make the bounded documentation repair, commit and push, then report back with V12/V13 state.

## Medium-or-Larger Rule

Medium or larger work should not be performed directly from the command room.

First localize governance inside the target repository.

Put the minimal repo-level gate or instruction surface in the target repo.

Then execute within that local boundary and report back to V13.

This keeps expanding work from being carried only by distant command-room context.

## Spend / Irreversible Boundary

Large, spend-sensitive, irreversible, automation-expanding, authority-changing, or public-scope-expanding work requires a Decision Packet or equivalent owner-visible gate.

It should not proceed as an ordinary bounded repair.

Auto-Spend Gate remains a parked future horizon.

Do not implement Auto-Spend Gate in this loop.

Do not create an Auto-Spend Gate file, plugin, MCP server, hook, automation scaffold, or CLI.

## Why This Matters

The external proof showed that V13 can coordinate a bounded cross-repo repair without losing completion discipline.

It also revealed the boundary where central governance should stop and local governance should begin.

This split preserves the usefulness of a command room while preventing it from becoming uncontrolled cross-repo automation.

## V12/V13 Interpretation

This is an operational observation derived from the external proof.

V13 is functioning as a manual command-room layer.

The external repo acts as a local worksite when `AGENTS.md` is placed there.

Small repairs can be handled centrally when bounded.

Medium or larger work should first receive local governance.

Auto-Spend Gate is only a parked future horizon at this point.

## Boundary

This does not claim autonomous orchestration.

This does not claim production readiness.

This does not authorize automation, hooks, skills, MCP, plugins, CLI, server behavior, package setup, CI, schema changes, or Auto-Spend Gate implementation.

It records a manual governance pattern observed after one successful external entrypoint proof.

## Result

Signal:
🟢 BLUE / COMMAND-ROOM-LOCAL-GATE-SPLIT-IDENTIFIED
+
🟢 BLUE / CROSS-REPO-GOVERNANCE-PATTERN-OBSERVED
+
🟡 YELLOW / DO-NOT-IMPLEMENT-SPEND-GATE-YET

Parked Horizons:
CLAUDE-SKILLS / HOOKS / MCP / PLUGINIZATION / V1 / AUTO-SPEND-GATE

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The external proof showed that V13 can govern a bounded cross-repo repair from the command room, but medium or larger changes should be localized behind a repo-level gate before execution. Auto-Spend Gate remains parked and must not be implemented in this loop.

## Next Loop

Preserve CAP; continue only with concrete exposed gaps or bounded adoption-readability repairs.
