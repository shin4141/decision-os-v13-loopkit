# Rechallenge Gate

## Observation

A failed route can become psychologically frozen.

When a person tries something seriously and is disappointed, rejected, ignored, or defeated, the route may become emotionally marked as unsafe or humiliating.

Later, even if the external conditions change, the person may avoid that route.

This can cause a decision error:

```text
Previously failed but now higher-EV route:
avoided because it carries old pain

New lower-EV route:
chosen because it has no emotional scar yet
```

## Core idea

A failed route should not be permanently closed by default.

It should remain eligible for re-evaluation when conditions change.

This does not mean retrying because the probability is high.

It means retrying only when the total expected value is positive.

## Rechallenge Gate

A previously failed route can be reconsidered when:

- the external conditions have changed
- the user's assets, evidence, or credibility have changed
- the cost of retry is lower
- the downside is bounded
- the learning value is meaningful
- the old failure produced knowledge that improves the next attempt
- the route now aligns with the current Aspire anchor
- the retry can be done as a bounded 0.01 action

## Not enough

Do not retry only because:

- time has passed
- the user feels revenge
- the probability seems high
- the route is emotionally unfinished
- the AI wants forward motion
- the previous failure feels unfair
- the opportunity looks new but the structure is unchanged

## V10 interpretation

Rechallenge can protect Aspire when it reopens a route that fear has frozen.

But it can also harm Aspire if it reopens an old wound without changed conditions.

Therefore, rechallenge requires both:

```text
changed conditions
+
positive total EV
```

## V13 interpretation

A previously `BLOCK` or `HOLD` route is not necessarily permanently closed.

V13 may later ask:

- Has the context changed?
- Has the evidence changed?
- Has the cost changed?
- Has the user's capability or credibility changed?
- Is the downside bounded?
- Is there a small reversible retry?
- Is the retry driven by EV, not emotional repair?
- Should this route now be GO / HOLD / CAP / BLOCK?

## Minimal template

```text
Rechallenge Gate:

Past route:
Why it failed:
What was learned:
What changed:
Current expected upside:
Current cost:
Current downside:
Learning value if failed again:
Smallest retry:
Gate: GO / HOLD / CAP / BLOCK
```

## Boundary

Do not implement this as a feature now.

Do not add automation.

Do not create a new loop submission.

Do not apply it to any specific past route yet.

Capture the principle only.

## Status

Signal captured.

No README rewrite.
No tutorial change.
No copy-paste file.
No feature expansion.
