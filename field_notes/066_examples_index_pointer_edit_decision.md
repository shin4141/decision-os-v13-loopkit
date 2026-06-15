# Field Note 066: Examples Index Pointer Edit Decision

Date: 2026-06-15

## Decision Purpose

This note decides whether V13 should later add a bounded examples-side pointer that tells readers or agents where to start inside the examples set.

The decision is based on Field Notes 063-065.

This is a decision note only.

It does not edit examples, README, docs, prompts, USE_CASES, public surfaces, canonical surfaces, or feature surfaces.

## Current Evidence

Field Note 063 established:

```text
12 examples checked / 12 valid / 0 invalid
```

Field Note 064 established:

```text
all 12 examples are useful enough to support adoption readiness and restartability
```

Field Note 065 established:

```text
examples/cap.v12_handoff_review.json is the best general "start here" example
```

Current examples directory:

```text
examples/*.json only
```

No examples index or note currently exists.

## Possible Edit Surfaces

### README Pointer

Assessment:

```text
not preferred
```

Reason:

README/public-entry edits remain `HOLD`. The gap is local to navigating the examples set, not a proven public-entry failure.

Risk:

- creates public-entry churn
- may imply broader README/public positioning work
- may reopen public-copy decisions without real reader evidence

### Examples Index / Note

Assessment:

```text
preferred
```

Reason:

The ambiguity is local to the examples set. A small examples-side note can reduce navigation friction without changing README, docs, prompts, schema, AGENTS, or example contents.

Risk:

- low maintenance burden
- no canonical rule change
- no public-readiness claim
- low chance of concept expansion if kept to a pointer

### Filename / Order Hint

Assessment:

```text
not preferred as first edit
```

Reason:

The filenames already encode gate and scenario well enough. Renaming or ordering files creates churn and can make history noisier than a tiny local pointer.

Risk:

- unnecessary file churn
- possible broken links if examples are referenced elsewhere
- more invasive than needed

### No Edit

Assessment:

```text
acceptable fallback, but not best if a bounded examples-side edit is authorized
```

Reason:

The examples are valid and useful already. Nothing is broken. However, Field Notes 064-065 identified a real local navigation ambiguity that a tiny examples-side pointer would reduce.

Risk:

- leaves first-example ambiguity in place
- future readers or agents may choose a less representative first example

## Preferred Edit Surface

Preferred future edit surface:

```text
examples index / note only
```

Avoid:

- README as the first edit surface
- example renaming unless a later concrete need appears
- docs/prompts/USE_CASES edits
- schema edits
- example content edits

Reason:

The pointer gap is local, bounded, and navigation-oriented. It does not require public copy or canonical rule changes.

## Smallest Future Edit Candidate

Smallest possible future edit:

```text
Create or update an examples-side note that says:

Start here: examples/cap.v12_handoff_review.json

This is the best first example because it shows the core V13 flow:
completed AI-assisted work -> V12 PASS -> V13 CAP -> bounded next loop.
```

Constraints for that future edit:

- do not change schema
- do not change example contents
- do not edit README
- do not edit docs, prompts, or USE_CASES
- do not promote anything to canonical
- do not claim public readiness

Possible filename for a future edit:

```text
examples/README.md
```

This filename is a candidate only.

It is not created by this note.

## Risk / Weight Check

Does this reduce ambiguity?

```text
yes
```

Reason:

It gives readers and agents a first file to inspect before choosing among 12 valid examples.

Does it create README/public churn?

```text
no, if kept to examples index / note only
```

Reason:

The future edit can avoid README and public-entry surfaces entirely.

Does it imply canonical promotion?

```text
no
```

Reason:

A local examples pointer does not change V13 rules, AGENTS instructions, schema, prompts, gate definitions, or public claims.

Does it add maintenance burden?

```text
low
```

Reason:

The pointer would need updating only if the best first example changes or examples are reorganized.

Does it overfit to internal field notes?

```text
low risk
```

Reason:

The decision rests on existing example content and the explicit reader-value review in Field Notes 063-065. The future edit would not mention the field-note chain unless separately authorized.

Overall weight:

```text
low / bounded / local
```

## Gate

V12 State:

```text
PASS
```

Reason:

The decision reviewed the current evidence, confirmed no examples index/note exists, evaluated possible edit surfaces, selected the smallest future surface, and preserved all protected surfaces.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The future edit is justified only as a bounded local examples-side pointer. This note does not authorize README edits, docs edits, example content edits, canonical promotion, public claims, or feature growth.

## Recommended Next 0.01

Recommended next 0.01:

```text
If separately authorized, create one bounded examples-side pointer note that identifies `examples/cap.v12_handoff_review.json` as the start-here example and explains why in 1-2 lines.
```

If not authorized:

```text
park this line
```

If later evidence shows the pointer is confusing:

```text
HOLD before touching README or public surfaces
```

## Boundaries

This is a decision note only.

Do not:

- edit examples
- edit README
- edit `AGENTS.md`
- edit `AGENTS.ja.md`
- edit `CLAUDE.md`
- edit docs, prompts, or `USE_CASES`
- edit handoff files
- edit schema
- change release state
- modify public surfaces
- modify external repos
- add automation, hooks, MCP, pluginization, package/server/CLI surfaces, or tooling
- promote anything to canonical
- claim public readiness
- expand features

## V13 Signal

Signal:
BLUE / EXAMPLES-INDEX-POINTER-EDIT-DECISION-RECORDED
+
BLUE / EXAMPLES-INDEX-NOTE-PREFERRED
+
BLUE / START-HERE-EXAMPLE-SELECTED
+
YELLOW / FUTURE-BOUNDED-EXAMPLES-POINTER-CANDIDATE
+
YELLOW / NO-EXAMPLE-EDIT
+
YELLOW / NO-README-OR-PUBLIC-EDIT
+
YELLOW / NO-CANONICAL-PROMOTION

V12 State:
PASS

V13 Next Loop Gate:
CAP

Next Loop Command:
Stop after this edit decision. Do not edit examples, README, docs, prompts, USE_CASES, public/canonical surfaces, or expand features unless separately authorized.
