# Field Note 142 — Evidence-State-Bearing External Intelligence

Status: Verification pending

As-of: 2026-08-30 JST

## Observation

External Intelligence becomes more useful when it preserves not only **what was learned**, but also **how strongly that knowledge is established and how safely it may affect the next decision**.

A memory item can be true enough to preserve while still being too weak to drive a later action. Likewise, a useful observation can be internally reproduced without having survived a different context, and a cross-context result can still lack independent third-party review.

This suggests that mature External Intelligence may need to carry an explicit evidence state alongside the knowledge itself.

The candidate structure is:

```text
knowledge item
+ As-of
+ provenance
+ evidence state
+ verification level
+ promotion state
+ re-evaluation trigger
-> bounded downstream influence
```

The important change is not merely "store more evidence." It is to make the **credibility and maturity of the stored intelligence visible to the future decision process**.

## Discovery gradient and verification gradient

In an early research or operating system, discovery can move faster than verification.

```text
Discovery Gradient > Verification Gradient
```

That difference is not automatically a failure. New failure boundaries, candidate rules, and operating structures may appear faster than independent validation can be accumulated.

The failure begins when the gap becomes invisible authority—for example, when an observation is later read as an established rule, an internal reproduction is treated as external validation, or a creator-owned result is reused as if a third party had confirmed it.

A healthier system may therefore permit temporary verification debt while keeping the debt explicit and reconnectable.

The objective is not necessarily to force verification to catch discovery immediately. The objective is to prevent **unverified intelligence from silently promoting itself**.

## Candidate evidence states

The following vocabulary is only a candidate schema. It is not Canon and does not require every future intelligence item to use these exact labels.

```text
OBSERVATION / HYPOTHESIS
    useful enough to preserve; not established

INTERNAL REPRODUCTION
    reproduced within the creator-owned or current operating environment

CROSS-CONTEXT REPRODUCTION
    reproduced in a materially different repository, workflow, model, or task context

THIRD-PARTY REVIEW / ACCEPTANCE
    an independent external party reviewed, accepted, merged, adopted, or otherwise validated the bounded claim actually at issue

REVALIDATION REQUIRED
    previously useful intelligence whose current applicability is uncertain because the relevant state, environment, or As-of has changed

SUPERSEDED
    preserved for lineage, but replaced by stronger or more current evidence
```

These labels should not be interpreted as a universal scalar score. Different evidence types establish different things. A third-party merge can validate a bounded repair without validating the entire Decision-OS theory; an internal A/B test can establish a local effect without proving population-level generality.

## Structural distinction

This extends the distinction in Field Note 140, which separates memory presence from legitimate judgment reuse.

A further separation is:

```text
knowledge is stored
  != knowledge is current
  != knowledge is verified
  != knowledge is promoted
  != knowledge has authority to drive this action
```

A future AI should therefore be able to recover both the content and the evidence boundary around the content.

The reusable object is closer to:

```text
claim
-> source / provenance
-> As-of
-> verification state
-> current applicability check
-> allowed influence on this decision
```

## Why this matters for External Intelligence

External Intelligence is not model self-training. The model weights do not become more correct because a repository contains more notes.

The value comes from changing a later judgment using selected external structure. If that structure does not expose whether it is tentative, reproduced, externally accepted, stale, or superseded, then the external memory can preserve knowledge while losing the conditions under which that knowledge deserves trust.

Evidence-state-bearing intelligence would make those conditions part of the reconnectable object itself.

That creates a possible progression from:

```text
external memory
-> selective retrieval
-> changed judgment
```

into:

```text
external memory
-> selective retrieval
-> evidence-state read
-> current applicability check
-> bounded influence
-> changed judgment
```

The added step is not intended to make every decision heavier. It is intended to stop weak or stale intelligence from becoming invisible permission merely because it was successfully retrieved.

## Decision-OS lineage connections

### V9 — As-of / Seat / Release

Evidence state should remain attached to an As-of and provenance boundary. Later capability or later evidence must not rewrite what was known at the original decision point.

### V11 — Reconnectable Forgetting

Compression and forgetting should preserve the path back not only to the claim, but also to the evidence needed to re-establish its credibility when current applicability matters.

### V12 — Completion Integrity

A future agent benefits from knowing whether a completion claim is creator-asserted, locally verified, cross-context reproduced, or externally accepted. Completion evidence can therefore be part of the restartable state rather than a prose afterthought.

### V13 — Compound Loop / Loop Gate

A later loop should not treat all retrieved intelligence as equally authoritative. Evidence state can become one input to whether reuse is allowed, requires revalidation, is advisory only, or must be blocked from driving the next action.

This does **not** mean that evidence state should automatically determine `GO / HOLD / CAP / BLOCK`. Human Seat, current evidence, scope, and risk still matter.

## Current project observation

Decision-OS development has produced candidate structures faster than every structure could receive independent validation at the moment of discovery. Over time, additional verification surfaces have begun to accumulate through bounded internal tests, cross-context ports, public OSS maintainer review, upstream acceptance, and other externally observable settlement events.

This note does not claim that those surfaces validate Decision-OS as a whole. They illustrate why a single binary label such as "verified / unverified" may be too coarse for the intelligence that accumulates across the system.

The stronger direction is for External Intelligence to preserve **which part has reached which evidence boundary**.

## Candidate implications

These are candidates, not promoted rules.

1. **Evidence maturity should travel with reusable intelligence.** A future reader should not need to infer the verification state from tone or file location alone.

2. **Verification debt should be visible.** Discovery may outrun verification, but the gap should remain inspectable and reconnectable.

3. **Promotion and verification are separate transitions.** A note can be useful enough to retain without being strong enough to become Canon or execution authority.

4. **Evidence state should be claim-scoped.** External acceptance of one bounded repair must not silently validate adjacent claims.

5. **Revalidation is a first-class state.** Previously verified intelligence may need to step down when the environment, source, version, or As-of materially changes.

6. **Downstream influence should be bounded by current applicability, not by storage success.** Retrieval is not permission.

## Non-claims

This note does not establish:

- a universal evidence taxonomy;
- that the candidate labels above are the right final schema;
- that evidence maturity can be reduced to one numeric confidence score;
- that third-party acceptance is always stronger than every form of internal evidence;
- that every memory item requires expensive verification before reuse;
- that verification must completely catch up with discovery;
- that public OSS merges validate Decision-OS as a whole;
- that evidence-state metadata alone improves downstream decisions;
- or that this note creates any new execution authority.

## Re-evaluation trigger

Re-evaluate this note when at least one of the following becomes available:

- a bounded sample of External Intelligence items is annotated with evidence state and a later AI demonstrably changes or withholds a downstream judgment because of that state;
- the same task is compared with and without evidence-state-bearing retrieval;
- a later AI avoids stale or under-verified reuse because `REVALIDATION REQUIRED`, provenance, or As-of is visible;
- an independent user workflow demonstrates useful evidence-state routing;
- or contrary evidence shows that the additional evidence-state layer adds more decision cost than decision quality within the tested scope.

## Promotion boundary

```text
Current status: Verification pending
Canon promotion: HOLD
Execution authority created: NO
Current V13 Gate changed: NO
```

Preserve this note as a research direction and origin record. Any schema, lifecycle change, automatic weighting rule, or Canon promotion requires a separate bounded task and evidence review.
