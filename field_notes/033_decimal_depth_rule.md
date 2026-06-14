# Field Note 033: Decimal Depth Rule

Date: 2026-06-14

## Purpose

This note records the Decimal Depth Rule for Breakout Maps and Mistaken MD.

The rule preserves where a later-discovered fixed point originally belonged in the line, instead of merely appending it at the end of the record.

## Problem

When a new fixed point is discovered after progress has already been made, ordinary documentation tends to append it as the next item:

```text
1.4
1.5
1.6
1.7 new insight
```

That preserves chronology.

But it may destroy causal position.

If the insight actually belonged between `1.4` and `1.5`, appending it as `1.7` loses the structure of the mistake.

The record then looks coherent while hiding where the real blind spot was.

## Decimal Depth Rule

Later-discovered fixed points should be inserted where they originally belonged in the line, not where they were chronologically discovered.

If a point was missing between `1.4` and `1.5`, record it as:

```text
1.41
```

not:

```text
1.7
```

If a deeper missing structure is later found inside `1.41`, record it as:

```text
1.441
```

or a similar decimal-depth marker.

Decimal depth records both:

- where the missed structure belonged
- how deeply it was hidden

## Why Appending Is Wrong

Appending preserves chronology but destroys causal position.

It makes the record look cleaner than the learning process was.

It can imply:

```text
We learned A, then B, then C, then D.
```

when the real structure was:

```text
We learned A, skipped a hidden part of A, built B and C on top of the gap, then later discovered the missing part.
```

High-capability models can often smooth this over with retrospective narrative consistency.

But retrospective coherence is not self-evolution.

Self-evolution requires showing where the earlier map was structurally incomplete.

## Decimal Depth as Signal

A deeper decimal is not necessarily a smaller or less important item.

In Fixpoint Learning, deeper decimal depth may indicate a structure that was more deeply hidden and should have been detected earlier.

The deeper the late insertion, the more important it is to ask:

- why was this not visible at the earlier point?
- which later judgments were affected by missing it?
- what signal would have revealed it sooner?
- what future detection condition should be added?

Decimal depth is therefore a signal, not just numbering.

It marks hidden topology.

## Relation to Mistaken MD

Mistaken MD records why a past fixed point was mistaken or incomplete.

Decimal Depth records where that mistaken or missing structure originally belonged.

Together:

- Mistaken MD = why it was missed
- Decimal Depth = where it belonged
- Detection condition = how to catch it earlier next time

Mistaken MD without Decimal Depth can explain the mistake while losing its location in the map.

Decimal Depth without Mistaken MD can place the missing node without explaining why it was missed.

Both are needed for stronger Fixpoint Learning.

## Relation to Breakout Loop

Breakout Loop does not merely add lessons at the end.

It reinserts discovered structure into the map so the next attempt starts with a stronger topology.

Failure becomes useful only when its missing structure is placed back into the line.

The breakout is not:

```text
We failed, then learned a lesson.
```

The breakout is:

```text
We found where the map was missing a required node, inserted it, and made the next traversal less blind.
```

## Relation to V7 Self-Evolution

This is a V7-style self-evolution requirement.

Self-evolution is not high-model retrospective coherence.

Self-evolution requires converting missed structures into earlier detectable fixed points.

Without decimal-depth placement, the future receives a lesson but not the structure of the failure.

The model may sound wiser while the map remains wrongly shaped.

V7-style self-evolution requires the shape to change.

## Example

V13 public-readiness repair produced this original line:

```text
1.4 Next 0.01 must be the earliest missing required node.
1.5 V12 PASS does not imply V13 GO.
```

If a later-discovered missing structure actually explains why `1.5` was misapplied, it should not be appended as:

```text
1.16
```

or:

```text
1.7
```

It should be inserted near where it belonged, such as:

```text
1.41
```

The public-readiness mistake was not merely "another lesson."

It exposed a missing structure between internal utility and public value:

```text
internal utility ≠ public readiness
```

That belongs before any public-readiness or outreach claim, not after it.

The decimal-depth marker preserves that causal position.

## Boundary

This is a mapping rule only.

Do not renumber existing files.

Do not rewrite previous notes.

Do not modify AGENTS.md.

Do not claim public readiness.

Do not broaden into outreach.

Do not add implementation.

Do not route this into AGENTS.md yet.

This note does not modify AGENTS.md, AGENTS.ja.md, README.md, previous field notes, docs, schemas, examples, prompts, CI, automation, or plugin files.

This note does not add features, hooks, skills, MCP, pluginization, automation, outreach, posting, or product behavior.

## V13 Signal

Signal:
🟢 BLUE / DECIMAL-DEPTH-RULE-RECORDED
+
🟢 BLUE / CAUSAL-POSITION-PRESERVED
+
🟢 BLUE / MISTAKEN-MD-STRUCTURE-STRENGTHENED
+
🟢 BLUE / V7-STYLE-SELF-EVOLUTION-CONNECTION-RECORDED
+
🟡 YELLOW / DO-NOT-RENORMALIZE-HISTORY
+
🟡 YELLOW / DO-NOT-ROUTE-INTO-AGENTS-YET

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The Decimal Depth Rule is recorded as a mapping rule, but it has not yet been tested through later Mistaken MD placement or promoted into AGENTS.md.

Next Loop Command:
Observe later whether Decimal Depth changes how future Mistaken MD records are placed, before routing it into AGENTS.md.
