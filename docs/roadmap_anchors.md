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

## Example Anchor Line

For this project, the current user-defined line is:

```text
Stars / adoption
↓
Revenue
↓
Enjoy life
```

Meaning:

* stars are not the final goal
* adoption is a signal that the structure is useful
* revenue is the sustainability layer
* enjoying life is the higher Aspire

Therefore, a 0.01 repair should be judged by whether it helps move along this line without damaging Carrier.

## How Codex Should Use Anchors

Before selecting a 0.01 repair, Codex should ask:

1. Which roadmap anchor does this repair support?
2. Does it move toward the next anchor or only improve local polish?
3. Does it preserve Carrier?
4. Does it violate any current CAP / HOLD / BLOCK?
5. Is this the highest-EV exposed gap relative to the anchor line?

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
Does this external opportunity help stars/adoption?
Does it help revenue?
Does it preserve the higher Aspire?
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
