# Field Note 047: External Repo Transfer Packet

Date: 2026-06-15

## Purpose

This note records the External Repo Transfer Packet concept.

When V13 inspects or works with an external repo, medium-or-larger work should produce a reusable control packet: what must be sent to that repo or a future agent so the work becomes restartable, bounded, and reproducible.

This is a concept record only.

## Observation

V13 can inspect and reason about external repos.

However, medium-or-larger work should not rely on one-off Codex plans or implicit chat context.

If the repo will be touched repeatedly, handed off, forked, or revisited, V13 should produce a reusable control packet.

That packet should preserve the control delta, not the whole V13 theory.

## Problem

A normal Codex plan may:

- inspect the repo
- plan edits
- run checks
- report completion

For medium-or-larger work, this is often insufficient because:

- safety boundaries are not preserved
- allowed touch surface is not explicit
- validation commands may be unclear
- rollback may be missing
- repo-specific risks are forgotten
- future agents must rediscover the same structure
- mistakes become future debt instead of reusable delta

The problem is not that planning is useless.

The problem is that the plan often dies with the chat.

## Transfer Packet Concept

An External Repo Transfer Packet is a repo-specific control summary produced by the V13 control room.

It records what must be known or sent to a future agent or repo to make the work:

- reproducible
- bounded
- restartable

It is not the work itself.

It is the control capsule that lets future work start from the right boundaries instead of rediscovering them.

## When It Should Be Created

Create only when:

- the external task is medium-or-larger
- the repo may be revisited
- the task may need handoff
- the task touches more than one file/module
- validation or rollback matters
- the repo may benefit from a reusable control capsule
- repeated mistakes would be costly

Do not create for:

- tiny one-off checks
- single-read observations
- tasks with no expected reuse
- public/outreach claims

The packet should appear when reuse, safety, or restartability justifies the extra control surface.

## What It Should Contain

An External Repo Transfer Packet should contain:

- repo path / repo name
- task purpose
- current known state
- allowed touch surface
- do-not-touch areas
- validation commands
- rollback path
- known dangerous loops
- GO / CAP / HOLD / BLOCK conditions for that repo/task
- dependency/environment cautions
- handoff requirements
- what future agent must read first
- what evidence is required before continuing

The packet should be specific enough to prevent rediscovery.

It should be small enough to avoid becoming a second repo handbook.

## What It Must Not Do

An External Repo Transfer Packet must not:

- silently modify the external repo
- install V13 everywhere by default
- copy AGENTS.md blindly
- become repo invasion
- create control bloat
- claim the repo is ready or safe without evidence

The packet is a control delta.

It is not permission to spread V13 into every repo.

## Relation to V13 Control Room

V13 remains the control room.

External repos receive only the minimum reusable control delta needed for bounded work.

This allows V13 to influence other repos without turning into:

- a generic loop gallery
- uncontrolled AGENTS sprawl
- automatic repo governance
- implicit pluginization

Small repairs can still happen from the command room when bounded.

Medium-or-larger work needs a transferable control surface before repeated execution.

## Relation to V11 Memory

Transfer packets will eventually need lane-based, reconnectable compression.

The packet is not just a summary.

It must preserve:

- active context
- compressed residue
- provenance keys
- causal position of mistakes
- re-entry conditions

This connects to V11 memory because external work needs more than "what happened."

It needs the lane position that tells a future agent why the next move is safe, capped, held, or blocked.

## Fork / Adoption Value

This may make V13 more forkable because users do not need the whole theory first.

They can receive a repo-specific control packet:

- what to check
- what not to touch
- which loops are allowed
- when to stop
- how to resume

The packet can become a practical entry surface for external repos without forcing full AGENTS.md adoption.

This is potential adoption value, not proof of public readiness.

## Boundary

This is a concept record only.

Do not create actual transfer packet files yet.

Do not modify external repos.

Do not modify AGENTS.md.

Do not modify AGENTS.ja.md.

Do not modify README.md.

Do not modify previous field notes.

Do not rewrite README.

Do not claim public readiness.

Do not broaden into pluginization or automation.

Do not add implementation.

This note does not modify docs, schemas, examples, prompts, CI, automation, or plugin files.

This note does not add features, hooks, skills, MCP, pluginization, automation, outreach, posting, transfer packet files, or product behavior.

## V13 Signal

Signal:
🟢 BLUE / EXTERNAL-REPO-TRANSFER-PACKET-DEFINED
+
🟢 BLUE / CONTROL-ROOM-TO-REPO-DELTA-RECORDED
+
🟢 BLUE / RESTARTABLE-EXTERNAL-WORK-CONCEPT-RECORDED
+
🟢 BLUE / V11-MEMORY-CONNECTION-IDENTIFIED
+
🟡 YELLOW / CONCEPT-ONLY
+
🟡 YELLOW / NO-EXTERNAL-REPO-MODIFICATION
+
🟡 YELLOW / DO-NOT-COPY-AGENTS-BLINDLY
+
🟡 YELLOW / PUBLIC-VALUE-STILL-NOT-PROVEN

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The transfer packet concept is recorded as a bounded control-room observation, but no packet files, external repo changes, pluginization, automation, or public-readiness claims are authorized.

Next Loop Command:
After this, write the handoff. Do not start the V11 lane-memory note in this chat.
