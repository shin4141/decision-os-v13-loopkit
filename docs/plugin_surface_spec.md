# Plugin Surface Spec

## Purpose

This document defines a possible future plugin surface for V13 LoopKit.

It is documentation-only.

It does not implement a plugin.

Current gate:

```text
Pluginization:
DESIGN-CAP
```

Meaning:

> The shape can be designed, but plugin implementation remains on HOLD.

## Why This Exists

V13 LoopKit currently works as a repository-level instruction and documentation kit.

A future plugin could reduce adoption friction by packaging the same behaviors into discoverable surfaces.

But pluginization must not remove human control or bypass V13 gates.

Therefore, this spec defines:

* possible plugin surfaces
* which parts should become skills
* which parts should become commands
* what must remain manual
* what must never be automated
* when a Decision Packet is required

## Non-Goals

This spec does not add:

* `.codex-plugin/`
* plugin manifest
* install script
* hooks
* automation
* CLI
* server
* package setup
* MCP integration
* credential access
* deployment integration
* release automation
* public posting automation

## Proposed Surface Map

### Project-level rules

Surface:

```text
AGENTS.md
```

Purpose:

Core reporting behavior for agent work inside a repository.

Includes:

* V12 State
* V13 Next Loop Gate
* Chat Continuation
* Context Compression
* Decision Packet requirement checks
* allowed / not allowed next actions

Plugin role:

> Remains the core instruction surface.

A plugin may reference or install guidance derived from `AGENTS.md`, but must not overwrite an existing `AGENTS.md` without human approval.

---

### Skill: `v13-reporting`

Purpose:

Generate the ordinary task-end report.

Outputs:

```text
V12 State:
PASS / DELAY / BLOCK

V13 Next Loop Gate:
GO / HOLD / CAP / BLOCK

Reason:
<1-2 lines>

Allowed Next Action:
<one line>

Not Allowed:
<up to 3 bullets>

Decision Packet Required:
yes / no

Next Loop Command:
<one line>
```

Boundaries:

* does not execute next actions
* does not install files
* does not make release decisions
* does not bypass human approval

---

### Skill: `context-compression`

Purpose:

Decide whether accumulated context should be kept, compressed, or handed off.

Outputs:

```text
Context Compression:
KEEP / COMPRESS / HANDOFF

Reason:
<1-2 lines>

Preserve:
- current signal
- latest pushed state
- allowed next action
- not allowed action
- next loop command
- known mistaken assumption pointer if any

Restart From:
<file / commit / handoff / section>
```

Boundaries:

* does not delete history
* does not solve recursive omission detection
* does not replace full review for high-impact work

---

### Skill: `self-repair`

Purpose:

Identify the current weakest point and the highest-EV 0.01 repair.

Inputs:

* Roadmap Anchors
* current repo state
* current signal
* MISTAKEN.md if relevant
* handoff state
* recent field notes

Outputs:

```text
Self-Repair Diagnostic:
GREEN / YELLOW / RED

Weakest Point:
<one line>

Highest-EV 0.01 Repair:
<one line>

Roadmap Anchors:
<anchors>

Anchor Alignment:
GREEN / YELLOW / RED

Next Loop Command:
<one line>
```

Boundaries:

* does not make multiple repairs at once
* does not add features without exposed gaps
* does not override public / feature / pluginization caps

---

### Skill: `roadmap-anchors`

Purpose:

Help a user define at least two anchors before asking V13 to choose 0.01 repairs.

Inputs:

* user-stated goals
* near-term proof/adoption target
* sustainability target
* higher Aspire target

Outputs:

```text
Roadmap Anchors:
1. <anchor>
2. <anchor>
3. <optional anchor>

Anchor Alignment:
GREEN / YELLOW / RED

0.01 Candidate:
<smallest exposed repair aligned with the anchor line>
```

Boundaries:

* does not decide the user’s Aspire
* may propose draft anchors but must ask the user to confirm
* should not proceed to external discovery without anchors

---

### Command: `v13-review`

Purpose:

Run a one-off review after a completed task.

Equivalent manual path:

```text
prompts/v13_loop_review.md
```

Use when:

* the user does not want to modify project files
* the user wants one-time V13 judgment
* a completed task needs GO / HOLD / CAP / BLOCK review

Must not:

* install files
* alter repo state
* create commits
* trigger automation

---

### Command: `v13-handoff`

Purpose:

Review whether the current state is restartable and whether handoff is needed.

Uses:

* V12 State
* Chat Continuation
* Context Compression
* current handoff file

Must not:

* replace human judgment for major transitions
* claim restartability without evidence
* skip current repo state verification

---

### Command: `v13-roadmap`

Purpose:

Check whether Roadmap Anchors are present and whether the next 0.01 aligns with them.

Uses:

```text
templates/user_roadmap_anchors.md
docs/roadmap_anchors.md
```

Must not:

* invent major user goals without confirmation
* optimize local polish without anchor alignment
* start external discovery before anchors exist

---

### Command: `v13-self-repair`

Purpose:

Run a bounded Self-Repair Diagnostic.

Use when:

* the user asks “what is the weakest point?”
* an external reader exposes a gap
* a public/invasion attempt fails
* the repo may have stale handoff or stale documentation
* a 0.01 repair needs to be selected

Must not:

* make multiple unrelated repairs
* add features speculatively
* update releases unless explicitly authorized
* implement plugins unless pluginization gate changes

## Manual Surfaces That Should Remain Files

These should remain durable files even if a plugin exists:

* `MISTAKEN.md`
* `handoff/current_codex_handoff.md`
* `templates/user_roadmap_anchors.md`
* `field_notes/`
* `docs/context_compression.md`
* `docs/roadmap_anchors.md`

Reason:

> The plugin may assist behavior, but durable project memory should remain visible in the repository.

## Must Not Automate

A future plugin must not automatically:

* install or overwrite `AGENTS.md`
* merge with existing project instructions
* make public posts
* create releases
* change deployment settings
* touch credentials
* perform monetary actions
* add hooks
* add MCP integrations
* broaden public exposure
* draft V13 v1.0
* bypass Decision Packet requirements

## Decision Packet Required When

A Decision Packet is required if plugin adoption would:

* overwrite or merge an existing `AGENTS.md`
* change project-wide agent behavior
* affect release, deployment, money, credentials, or external integrations
* introduce hooks, automation, CLI/server setup, or MCP
* alter ownership-sensitive workflows
* broaden public exposure
* create or modify durable project memory in a way the user may not expect

No Decision Packet is required for:

* reading this repository
* summarizing whether it may help
* comparing current workflow gaps
* proposing a non-destructive manual next step
* generating a one-off review without modifying files

## Safe Adoption Flow

A future plugin should follow:

```text
1. Inspect current repository instructions
2. Detect whether AGENTS.md or equivalent instructions already exist
3. Explain what V13 LoopKit would change
4. Identify possible conflicts
5. Produce a Decision Packet if project-wide behavior would change
6. Ask human approval
7. Apply the smallest approved change
8. Report V12 State, V13 Next Loop Gate, Chat Continuation, and Context Compression
```

## Readiness Gate

Current pluginization gate:

```text
Pluginization:
DESIGN-CAP
```

Ready to move toward implementation only when:

* this surface spec is understandable to a first-time user
* skill and command names are understandable
* safe adoption flow is validated
* existing AGENTS.md merge behavior is designed
* Decision Packet conditions are clear
* there is a concrete external signal that plugin form is needed

Activation timing:

Pluginization should remain parked until most of these are true:

* `AGENTS.md` copy friction is observed from at least one real user or external agent workflow
* at least two external normal-repo proofs have succeeded with `AGENTS.md`
* README entry-path testing passes
* V12/V13 reporting format remains stable across several loops
* pluginization would reduce setup friction without changing the canonical rule set
* expected plugin update cost is lower than continued manual-copy friction
* there is an explicit owner decision to activate pluginization

Boundaries:

* Do not build the plugin before the rule set stabilizes.
* Do not wait for perfect demand before defining the plugin shelf.
* Pluginization is a cross-repo / packaging decision, not a reason to split the canonical rule set.
* `AGENTS.md` remains canonical unless explicitly changed by owner decision.

## One-Line Rule

Design the plugin surface before implementing the plugin.

Do not let lower-friction adoption remove human control.
