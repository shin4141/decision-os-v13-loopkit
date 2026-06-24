# Subthreshold Signal Integration

## Observation

Field notes often capture candidates that are not yet strong enough to act on.

A single note may be only `0.3`, `0.5`, or `0.7`.

The previous interpretation was:

- preserve the candidate
- wait until it becomes strong enough by itself
- reconsider when it reaches `1.0`

But this misses another path.

A candidate does not always need to reach `1.0` alone.

If two or more subthreshold signals point in a similar direction, they may integrate into an actionable `1.0`.

## Core idea

Subthreshold signals should not only be stored independently.

They should also be checked for integration.

```text
0.5 + 0.8 does not automatically equal 1.3.

But if both signals point toward the same pain, route, missing piece, or next action,
their integration may reach the actionable threshold.
```

The key is not arithmetic addition.

The key is directional compatibility.

## Directional compatibility

Two subthreshold signals may be integrated when they share:

- the same underlying pain
- the same failure mode
- the same missing condition
- the same route pressure
- the same next 0.01 action
- complementary evidence
- compatible Aspire direction

They should not be integrated when they are merely adjacent, exciting, recent, or emotionally salient.

## Examples

### Field note level

One field note says:

- users understand the pain but do not know what to copy

Another field note says:

- copyable prompts reduce first-use friction

Individually, each may be below action threshold.

Together, they may justify a `copy-paste/` template.

### Mistake level

One mistake shows that Codex summarized a repo instead of starting a tutorial.

Another signal shows that users need a first-contact menu.

Together, they may justify an Exact First Response entry rule.

### Aspire anchor level

One Aspire anchor points toward research continuity.

Another points toward practical adoption.

Individually, each may be incomplete.

Together, they may support a service path or public-facing copyable loop.

### Existing line x future line

An existing repo line may be stable but not growing.

A future market line may be visible but not actionable alone.

If they align, integration may create a valid next 0.01.

If they do not align, forcing them together creates noise.

## V13 interpretation

V13 should not only ask:

- Should this loop run?
- Should this candidate remain parked?
- Has this note matured enough by itself?

It should also ask:

- Are there nearby subthreshold signals?
- Do they point in the same direction?
- Does their integration create a safer or shorter 0.01 path?
- Does integration reduce route distance?
- Does integration preserve Returnability?
- Does integration avoid overfitting to recency or frustration?

## Minimal-radius path

This is part of minimal-radius thinking.

The shortest valid next action may not come from the strongest single signal.

It may come from integrating weaker nearby signals that share a direction.

```text
Single strong signal:
one candidate reaches 1.0 alone.

Integrated signal:
multiple compatible candidates form the shortest path to 1.0.
```

## Risk

Integration can also create false confidence.

Bad integration occurs when:

- unrelated notes are combined because they are recent
- emotional pressure makes weak signals look aligned
- different Aspire lines are forced together
- a future line is used to justify an unrelated current action
- integration removes necessary uncertainty

Therefore, integration must preserve uncertainty and require a concrete next 0.01 action.

## Integration test

Before integrating subthreshold signals, ask:

1. What is each signal saying?
2. What threshold value does each signal appear to have?
3. What direction does each signal point toward?
4. What is shared between them?
5. What does one signal supply that the other lacks?
6. What new action becomes possible only after integration?
7. Is the integrated action still small, reversible, and bounded?
8. Does the integration produce a valid next 0.01?
9. Should the result be GO, HOLD, CAP, or BLOCK?

## Status

Signal captured.

No README rewrite.
No tutorial change.
No copy-paste file.
No feature expansion.
No automation.
