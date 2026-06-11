# MISTAKEN.md

## Purpose

`MISTAKEN.md` records mistaken assumptions, failed invasion attempts, unclear reader reactions, overreach, and loop decisions that later prove wrong.

It is not a blame log.

It is a repair source.

V13 uses this file to turn failure into repairable evidence.

In one line:

> MISTAKEN.md turns failed invasion into repairable evidence.

## Why This Exists

Aspire-oriented loops will sometimes fail.

Examples:

- a public post does not land
- a README change does not improve first-time understanding
- a star-acquisition attempt gets no signal
- a loop expands too far
- a CAP was too loose
- a HOLD should have been used earlier
- the project over-optimizes and increases Carrier load
- a Decision Packet should have been triggered but was not

Without a repair log, these failures become discouragement or noise.

With `MISTAKEN.md`, they become inputs for the next 0.01 repair.

## When to Add an Entry

Add an entry when:

- an Aspire-invasion move fails or underperforms
- a public or adoption attempt produces weak or confusing feedback
- an assumption about users/readers proves wrong
- a GO / HOLD / CAP / BLOCK judgment later appears mistaken
- a loop caused avoidable Carrier load
- a handoff, footer, or report failed to preserve restartability
- a reader or user exposes a gap that was not expected

Do not add an entry for every minor imperfection.

Use this file when the mistaken assumption can improve the next loop.

## Entry Format

```md
## YYYY-MM-DD — Short title

### Mistaken assumption

What did we believe?

### Action taken

What did we do?

### Observed result

What happened?

### Why it was mistaken

Which assumption failed?

### Gate that should have applied

GO / HOLD / CAP / BLOCK

### Repair

What 0.01 repair should be made?

### Carrier impact

LOW / MEDIUM / HIGH

### Next rule

What should be done differently next time?
```

## Example Entry

```md
## 2026-06-12 — README clarity was overestimated

### Mistaken assumption

We believed the README was already clear enough after adding a worked example.

### Action taken

We ran a first-time-reader clarity check.

### Observed result

The reader still did not see the Before / After value difference and described the README as closer to an internal protocol note.

### Why it was mistaken

The concrete value was present, but not visible early enough above the abstract framework language.

### Gate that should have applied

CAP

### Repair

Move plain-language first action, Input → Decision → Output, and Before / After above abstract framework terms.

### Carrier impact

LOW

### Next rule

Do not assume README clarity from internal improvement. Recheck with a first-time reader before public invasion.
```

## Relationship to V13

`MISTAKEN.md` connects to:

* Self-Repair Diagnostic
* Aspire-Oriented Loop Map
* Public Exposure Loop
* Star Acquisition Loop
* Carrier Recovery Loop
* Decision Packet

Sequence:

```text
Aspire-invasion move
↓
Observed failure or weak signal
↓
MISTAKEN.md entry
↓
Self-Repair Diagnostic
↓
Highest-EV 0.01 repair
↓
Next bounded loop
```

## Rule

Do not hide failed invasion.

Do not overreact to failed invasion.

Record the mistaken assumption, repair the smallest exposed gap, and continue only within the next appropriate gate.
