# Field Note 029: Fixpoint Learning and Breakout Loop

Date: 2026-06-14

## Purpose

This note records the distinction between GOAL planning and Fixpoint Learning.

GOAL-style reverse planning and Fixpoint Learning are related, but they are different skills.

Core distinction:

```text
GOAL is the skill of reverse-planning from a known objective.
Fixpoint Learning is the skill of moving toward an objective while discovering, recording, and reusing previously unseen fixed points.
```

## GOAL Planning

GOAL planning starts from a target.

It reverse-plans visible steps from that target back toward the current state.

It is useful when the map is already mostly known.

The strength of GOAL planning is direction.

It prevents random movement by asking:

```text
What must be true before the target can be reached?
```

Its weakness is that it does not automatically learn unseen intermediate fixed points.

If the original map is incomplete, GOAL planning may still move efficiently along the wrong or under-specified line.

## Fixpoint Learning

Fixpoint Learning starts from the premise that the map is incomplete.

At the beginning, only a few fixed points may be visible.

While working, new intermediate points appear.

Those points must be recorded, not lost.

A completed objective may start with three visible fixed points and end with one hundred learned fixed points.

The skill is not merely reaching the goal.

The skill is learning the missing map while moving.

Fixpoint Learning asks:

```text
What became visible only because we attempted the line?
```

and:

```text
How do we preserve that visibility for the next attempt?
```

## Why GOAL Alone Does Not Learn

Ordinary GOAL execution treats plan failure as deviation or delay.

It may re-plan around the obstacle.

It may continue toward the objective with a revised sequence.

But unless it records why the previous map was incomplete, the learning evaporates.

Without recording discovered fixed points, the next attempt repeats similar blind spots.

The system may become better at pushing through obstacles without becoming better at detecting them earlier.

That is not enough for V13.

V13 needs the failure difference to become a reusable detection condition.

## Breakout Loop

Breakout Loop is the operational pattern for Fixpoint Learning.

The loop is:

1. Start with a rough line such as `1 → 2 → 3`.
2. When evidence for `1` is sufficient, move to `2`.
3. If a weakness in `1` becomes visible while working on `2`, do not ignore it.
4. Record why that weakness was not visible during `1`.
5. Convert that reason into a future detection condition.
6. Retry with a stronger map.
7. Breakout may mean success, but even failed attempts can compound if the failure difference is preserved.

The important move is not simply returning to `1`.

The important move is returning with a sharper detector.

## Mistaken MD

Mistaken MD is the record of why a past fixed point was mistaken, incomplete, or prematurely treated as settled.

It should include:

- what was believed fixed
- what later showed the gap
- why it was not visible earlier
- what signal would have revealed it
- what future rule or detection condition should be added

Mistaken MD is not a shame log.

It is a fixed-point repair log.

Its job is to keep the system from paying the same blindness cost twice.

## Example Loop

The recent V13 repair line shows the pattern.

Initial belief:

```text
V13 was close to public-ready because internal utility and README/AGENTS surface were improving.
```

Later gap:

```text
AGENTS.md looked like footer/report discipline rather than judgment logic.
```

Why not visible earlier:

```text
Readability checks were mistaken for judgment-core checks.
```

Mistaken MD lesson:

```text
Do not treat "readable" as "operationally grounded."
```

New fixed point:

```text
Public readiness requires demonstrated judgment difference, not just clean entry text.
```

Breakout result:

```text
External contrast showed ordinary polish momentum vs V13 Evidence CAP.
```

The failure was not wasted because the difference became a sharper map.

## What Becomes Fixed

The following become fixed candidates:

- GOAL and Fixpoint Learning are separate skills.
- The map can grow during execution.
- Newly visible intermediate points are assets only if recorded.
- A past gap must become a future detection condition.
- Failure can compound when transformed into Mistaken MD.

These fixed points should be tested through later use before being promoted into canonical instructions.

## What Is Still Not Proven

This does not prove public adoption.

This does not prove star-worthiness.

This does not justify pluginization.

This does not automate the process.

This does not mean every failure is valuable.

A failure becomes valuable only when its difference is captured and converted into a future detection condition.

## Boundary

This is a concept record only.

Do not modify AGENTS.md yet.

Do not claim readiness.

Do not broaden into outreach.

Do not add implementation.

This note does not modify AGENTS.ja.md, README.md, docs, schemas, examples, prompts, plugin files, CI, or automation.

This note does not add features, hooks, skills, MCP, pluginization, automation, outreach, posting, or product behavior.

## V13 Signal

Signal:
🟢 BLUE / FIXPOINT-LEARNING-DEFINED
+
🟢 BLUE / GOAL-VS-FIXPOINT-LEARNING-SEPARATED
+
🟢 BLUE / MISTAKEN-MD-PURPOSE-DEFINED
+
🟢 BLUE / BREAKOUT-LOOP-CANDIDATE-RECORDED
+
🟡 YELLOW / PUBLIC-READINESS-NOT-PROVEN
+
🟡 YELLOW / DO-NOT-ROUTE-INTO-AGENTS-YET

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The concept distinction is recorded as a candidate fixed point, but it has not yet been reused enough to route into AGENTS.md or claim readiness.

Next Loop Command:
After this, observe whether this concept becomes a fixed point through later use, rather than routing it into AGENTS.md immediately.
