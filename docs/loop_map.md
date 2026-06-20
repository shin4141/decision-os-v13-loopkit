# Loop Map

## Purpose

A single V13 Loop Record answers:

> What should the next loop do?

A Loop Map answers:

> Which loops are currently active, capped, paused, blocked, or waiting for human decision?

Loop Map turns V13 from a one-off judgment into an operating surface.

It prevents the project from drifting into hidden loops such as:

- feature growth after feature growth was paused
- public posting after public exposure was capped
- v1.0 drafting while v1.0 is still on HOLD
- automation work before proof exists
- ownership-sensitive choices made without human participation

In one line:

> Loop Record judges the next move. Loop Map shows which games are currently allowed to run.

## Difference Between Loop Record and Loop Map

| Object | Scope | Question |
|---|---|---|
| Loop Record | One completed task or next loop | Should this next loop GO / HOLD / CAP / BLOCK? |
| Loop Map | Multiple active loop categories | Which loops are allowed, capped, paused, blocked, or human-required? |

A Loop Record is local.

A Loop Map is global.

## Minimal Loop Map Format

```text
Loop Map

Proof Loop:
Gate: GO / CAP
Meaning: continue bounded real-task proof

Feature Growth Loop:
Gate: HOLD / PAUSE
Meaning: do not add new features yet

Public Exposure Loop:
Gate: CAP
Meaning: no repeated promotion or reaction-chasing

V13 v1.0 Paper Loop:
Gate: HOLD
Meaning: wait for more operating-surface evidence

Decision Packet Loop:
Gate: DESIGN-ONLY / CAP
Meaning: document examples only; do not implement Telegram or automation

Ownership-Sensitive Loop:
Gate: HUMAN REQUIRED
Meaning: color, naming, brand, pricing, public promises, and other authorship decisions require human choice

Irreversible Action Loop:
Gate: HUMAN REQUIRED
Meaning: deletion, release, credential, money, account, or external authority changes require human confirmation
```

## Current Loop Map

As of the current prototype state:

| Loop                      |            Gate | Meaning                                     |
| ------------------------- | --------------: | ------------------------------------------- |
| Proof Loop                |     🟢 GO / CAP | Continue bounded real-task proof            |
| Feature Growth Loop       | 🟡 HOLD / PAUSE | Do not add new features yet                 |
| Public Exposure Loop      |          🟡 CAP | No repeated promotion or reaction-chasing   |
| V13 v1.0 Paper Loop       |         🟡 HOLD | Do not draft v1.0 yet                       |
| Decision Packet Loop      |  🟡 DESIGN-ONLY | Examples are allowed; implementation is not |
| External V13 README Reuse |           🟢 GO | Use as-is for next reader or task           |

## Deviation

A deviation occurs when the actual work starts moving a loop beyond its current gate.

Examples:

### Public Loop Deviation

Current gate:

```text
Public Exposure Loop: CAP
```

Deviation:

```text
The operator posts repeated follow-up explanations within 48 hours.
```

### Feature Growth Deviation

Current gate:

```text
Feature Growth Loop: HOLD / PAUSE
```

Deviation:

```text
The agent adds CLI, server, package setup, or automation.
```

### V1 Paper Deviation

Current gate:

```text
V13 v1.0 Paper Loop: HOLD
```

Deviation:

```text
The agent starts drafting V13 v1.0 before enough operating-surface evidence exists.
```

### Ownership Deviation

Current gate:

```text
Ownership-Sensitive Loop: HUMAN REQUIRED
```

Deviation:

```text
The agent chooses color, name, brand direction, pricing, customer-facing promise, or final delivery without human choice.
```

## Why Loop Map Matters

Without a Loop Map, each decision may look locally reasonable.

But the project can still drift.

Example:

* one README edit seems fine
* one field note seems fine
* one public clarification seems fine
* one extra feature seems fine

But across time, the project may violate its own signal:

```text
Feature growth was paused, but features kept growing.
Public exposure was capped, but posts kept appearing.
v1.0 was on HOLD, but drafting began.
```

Loop Map detects this kind of drift.

## Relationship to Decision Packet

Loop Map detects that a human decision may be needed.

Decision Packet compresses that decision into a human-actionable choice.

Sequence:

```text
Loop Map
↓
Deviation or human-required gate detected
↓
Decision Packet
↓
Human reply
↓
Next Loop Command
```

## Context Risk Modifier

Context Risk is an external context-health signal that affects the next-loop gate.

It is not automatic detection in the MVP. The operator may observe it manually.

Signals include:

- Codex limit warning
- context pressure warning
- repeated clarification failure
- repeated re-checks caused by context uncertainty
- mild boundary confusion
- instruction confusion
- anchor weakening or anchor loss
- goal mixing
- Seat loss
- contradiction with the handoff

Core proceed rule:

```text
Loop Map Confidence >= Required Confidence
AND
Context Risk is not RED
```

GOAL-style execution moves the loop.

LoopKit watches the health of the map around the loop.

When the map weakens, LoopKit injects only the missing context, confidence threshold, Seat check, or recovery path needed for the next 0.01 action.

## Context Risk Levels

### BLUE

Context remains usable.

Normal Required Confidence applies.

GOAL-style execution may continue if task risk allows it.

### YELLOW

YELLOW means limit warning, context pressure, mild boundary confusion, repeated re-checks, or early anchor weakening.

Effects:

- Add +10 to Required Confidence.
- Next Action Card must surface Consult / Handoff / Split as available choices.
- Continue is allowed only under cap and only if adjusted confidence remains sufficient.

### RED

RED means key anchors are missing or contradicted.

Examples:

- the model is mixing goals
- the model is losing Seat
- instructions are confused
- context failure is near
- the current state contradicts the handoff

Effects:

- GOAL-style auto-continuation is blocked.
- Allowed choices narrow to Handoff / Split / Consult / Stop.

## Loop Map Confidence

Loop Map Confidence is not progress percentage.

It is the confidence that the AI can choose the next 0.01 action without breaking:

- Goal
- Forward Anchor
- Current State
- Context Boundary
- Re-entry
- Seat
- Risk

Codex limit warnings either reduce Loop Map Confidence or raise the Required Confidence threshold through Context Risk.

## Required Confidence Defaults

MVP default ranges:

| Task type | Required Confidence |
| --- | ---: |
| Low-risk search / notes / drafts | 40-55 |
| Small docs / repo edits | 60-75 |
| Commit / push / public-facing docs | 75-85 |
| External post / release / deletion / payment / irreversible actions | 90+ |

YELLOW Context Risk adds +10 to the Required Confidence threshold.

RED Context Risk blocks GOAL-style continuation regardless of confidence.

## Next Action Card Behavior

When Context Risk is BLUE:

- Next Action Card may recommend normal continuation if Loop Map Confidence is sufficient.

When Context Risk is YELLOW:

- Next Action Card must show the adjusted Required Confidence.
- Next Action Card must include Consult / Handoff / Split as available choices.
- Continue must be framed as "continue under cap," not unrestricted execution.

When Context Risk is RED:

- Next Action Card must not recommend normal continuation.
- It may recommend only:
  1. Handoff
  2. Split context
  3. Consult and restore missing anchors
  4. Stop and resume later

## V12 Carry-Forward Rule

If a concept changes the gate, threshold, stop condition, or recovery path, it must be carried forward in the next handoff.

Context Risk Modifier changes gate and threshold behavior.

It must not be left only in chat memory.

## When to Trigger a Decision Packet

A Decision Packet should be triggered when:

* a loop attempts to move beyond its current gate
* a HUMAN REQUIRED loop is touched
* a CAP would be exceeded
* a HOLD loop is about to restart
* a BLOCK loop is being reconsidered
* public exposure, deletion, credential, money, release, authority, or ownership-sensitive decisions are involved

## When No Decision Packet Is Needed

No Decision Packet is needed when:

* the action remains inside the current loop gate
* the task is reversible and low-impact
* the work is already covered by an approved CAP
* the action does not change public state, ownership, money, credentials, release, or authority
* the final report can simply include the normal V12/V13 signal

## Aspire-Oriented Extension

The base Loop Map shows which loops are active, capped, paused, blocked, or human-required.

For Aspire-oriented operation, see:

- `docs/aspire_oriented_loop_map.md`

The Aspire-oriented map asks whether each loop is moving the operator closer to a declared Aspire, such as adoption, stars, revenue, or operationalization, without damaging the Carrier.

## One-Line Summary

Loop Map is the operating map of V13.

It shows which loops are allowed to run, which are capped, which are paused, which are blocked, and which require human authorship.
