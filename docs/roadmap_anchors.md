# Roadmap Anchors

## Purpose

Roadmap Anchors define the line that V13 uses to judge whether a 0.01 repair actually moves the user forward.

A 0.01 repair is not just a small task.

A 0.01 repair should improve the next loop’s starting condition along a declared direction.

In one line:

> No roadmap line, no meaningful 0.01.

## Why This Exists

V13 can judge whether a next loop should `GO`, `HOLD`, `CAP`, or `BLOCK`.

But it still needs a direction.

Without roadmap anchors, Codex may optimize locally:

- fix wording
- add docs
- add examples
- improve repo hygiene
- create more prompts
- suggest more features

These may be useful, but they do not necessarily compound toward the user’s Aspire.

Roadmap Anchors prevent local improvement from replacing directional progress.

## Minimum Requirement

At least two anchors are required.

One point is only a desire.

Two points create a line.

Three points begin to reveal a trajectory.

Minimal form:

```text
Anchor 1:
Current target or near-term objective

Anchor 2:
Next higher objective
```

Better form:

```text
Anchor 1:
Near-term adoption / proof target

Anchor 2:
Revenue / sustainability target

Anchor 3:
Life / Aspire target
```

## Prior As-of Roadmap

The previous user-defined line was:

```text
Stars / adoption
↓
Revenue
↓
Enjoy life
```

This roadmap was valid while V13's immediate problem was public understanding, first-use friction, and recognition. It remains preserved as historical As-of rather than being characterized as a mistake.

Meaning:

* stars are not the final goal
* adoption is a signal that the structure is useful
* revenue is the sustainability layer
* enjoying life is the higher Aspire

## Current Roadmap — Forward-Only Rebaseline 2026-07-22

```text
Primary Direction:
Human-Seat-Preserving Autonomous Compounding

Near-Term Operating Objective:
One bounded loop in which AI:
1. detects an exposed high-value gap;
2. closes AI-owned ambiguity from established context;
3. returns only an irreducible Human-Seat judgment;
4. calibrates question depth to person × domain × state × consequence;
5. maps dependencies after the answer;
6. applies only authorized Forward-only propagation;
7. validates authority, historical As-of, and Protected Object;
8. records whether correction, rereading, re-explanation, or Carrier burden
   decreased;
9. stops at the current Gate.

External Validation:
real reuse / successful fresh re-entry / reduced rereading / reduced
re-explanation / reduced correction / reduced Human supervision burden / stars /
comments / forks / adoption / external task evidence

Sustainability:
Revenue or paid operational value after sufficient evidence.

Higher Aspire:
A Decision-OS that can improve its own operating conditions while preserving
Human Seat, historical As-of, rollback, and challenge visibility, and that may
later support bounded self-evolution evaluation.
```

### Forward-Only Aspire-Anchored Independent Evolution Evaluation — 2026-07-22

The Decision Owner fixed the invariant comparison core for later bounded self-evolution evaluation:

> A self-update must expand reachable paths toward the Decision Owner's Aspire
> without breaking Guard, PIC, or stable self-recursion, and must remain
> independently comparable, falsifiable, rejectable, and reconnectable from
> outside the update's own newly proposed criteria.

Current forms of Human Seat, historical As-of, rollback, and challenge visibility may later be improved through separately authorized Forward-only change. Their functions must remain: Aspire-line comparison, non-circular justification, Decision Owner refusal, historical reconnection, visible material counterevidence, and return to a stable self-recursive point.

Capability, speed, autonomy, reuse, or burden reduction without expanded Aspire-directed reachability is capability expansion or adaptation, not sufficient evidence of self-evolution. Movement away from Aspire, self-ratification, hidden counterevidence, lost refusal, lost reconnection, or broken stable self-recursion is drift or self-distortion.

Changing Aspire itself is a separate Forward-only Human Seat judgment. It must preserve the old Aspire, reason for change, gains, losses, and re-evaluation condition. A self-update must not use its newly created Aspire to justify changing the prior Aspire inside the same update.

`PIC` remains a Decision Owner term without a local V13 definition. This roadmap records the term without inventing its semantics.

The causal order is now:

```text
stronger internal compounding
→ real operational value and evidence
→ reuse / adoption / stars
→ sustainability / revenue
→ higher Aspire
```

This does not remove stars or adoption. It moves them from the primary operating direction to external validation and downstream outcome. Internal coherence alone is also insufficient; external evidence remains necessary to prevent a closed self-confirming loop.

Current distinction:

```text
Primary internal direction:
Human-Seat-Preserving Autonomous Compounding

External falsification / validation:
reuse, task evidence, adoption, stars, comments, correction reduction,
re-explanation reduction

Downstream sustainability:
revenue

Higher Aspire:
self-improvement that may approach bounded self-evolution evaluation without
losing Human Seat
```

## How Codex Should Use Anchors

Before selecting a 0.01 repair, Codex should ask:

1. Does this repair improve the system's ability to detect, route, propagate, validate, and retain a beneficial `1.01` delta?
2. Does it keep routine work AI-owned without taking the Human Seat?
3. Does it move toward the next anchor or only improve local polish?
4. Does it preserve Carrier, historical As-of, rollback, challenge visibility, and Re-entry?
5. Does it violate any current `CAP / HOLD / BLOCK`?
6. Is this the highest-EV exposed gap relative to the current line?
7. Does the resulting improvement produce or strengthen external evidence, reuse, adoption, or sustainability?

Current operational questions:

> Does this loop improve the system's ability to detect, route, propagate, validate, and retain a beneficial 1.01 delta without returning routine burden or taking the Human Seat?

Then:

> Does the resulting improvement produce or strengthen external evidence, reuse, adoption, or sustainability?

For a future self-update claim, also ask:

> Can the claimed improvement be compared, falsified, rejected, and reconnected from a position independent of the update's own new criteria, and does it expand reachable paths toward the preserved Aspire?

## If Anchors Are Missing

If roadmap anchors are missing, Codex should not invent major strategy.

It may ask the user to provide at least two anchors.

Alternatively, Codex may propose draft anchors and ask the user to confirm.

Use this format:

```text
Roadmap Anchors Needed:
yes

Proposed Anchors:
1. <near-term objective>
2. <next higher objective>
3. <optional higher Aspire>

Question:
Do these anchors match your intended direction?
```

## Relationship to Self-Repair Diagnostic

Self-Repair Diagnostic asks:

> What is the weakest point and highest-EV 0.01 repair?

Roadmap Anchors add:

> Highest-EV relative to what line?

Together:

```text
Roadmap Anchors
↓
Self-Repair Diagnostic
↓
Highest-EV 0.01 repair
↓
V13 Next Loop Gate
```

## Relationship to External Discovery

External discovery tools, plugin search, Scout-like exploration, or market research should not be used before anchors exist.

Without anchors, external discovery increases options but not direction.

With anchors, external discovery can be filtered:

```text
Does this external signal test a claimed compounding improvement?
Does it show reuse, reduced correction, reduced re-explanation, or task value?
Does it strengthen adoption or stars without becoming star-chasing?
Does it create a credible path toward sustainability or revenue?
Does it preserve Human Seat and the higher Aspire?
Does it create Carrier load?
```

## Relationship to Model Routing

Model routing should also follow anchors.

Example:

* use stronger models for ambiguity, strategy, roadmap, and judgment
* use cheaper or faster models for execution, formatting, and bounded repetition
* use Codex for repository-grounded edits and verification

But model routing is secondary.

First define the line.

Then choose which model or agent should move which part of the line.

## Output Format

When relevant, Codex may include:

```text
Roadmap Anchors:
1. <anchor>
2. <anchor>
3. <optional anchor>

Anchor Alignment:
GREEN / YELLOW / RED

Reason:
<1-2 lines>

0.01 Candidate:
<smallest exposed repair that moves toward the anchor line>
```

## Gate Meanings

### GREEN

The next 0.01 clearly supports the roadmap line.

### YELLOW

The next 0.01 may help, but the anchor alignment is indirect or uncertain.

### RED

The next 0.01 is local polish, feature growth, public reaction-chasing, or unrelated expansion.

## Current Rule

Do not let Codex choose 0.01 repairs from isolated tasks alone.

Give it at least two roadmap anchors.

If the user has not provided anchors, ask or propose them.

One-line rule:

> A 0.01 is only compounding when it moves along a declared line.
