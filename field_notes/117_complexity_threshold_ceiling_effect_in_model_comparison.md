# Field Note 117 — Complexity Threshold and Ceiling Effect in Model Comparison

## Layer

V13 / Model Selection / Loop Capability Boundary

Adjacent layers:
- V10 Goal-Length / selecting the minimum sufficient model
- V12 Completion Integrity / avoiding false confidence in “PASS”
- V13 Loop Gate / deciding when stronger review is needed
- V14 Resource Justice / model cost versus decision risk

## Background

A recent comparison claimed little or no difference between two models across repeated runs.

However, the task design appeared to remain below the capability ceiling of the lower model.

If the lower model can already complete the task reliably, the additional capability of the higher model may never become visible.

This creates a measurement problem.

## Core Observation

```text
If the task stays below the lower model’s complexity threshold,
the higher model’s advantage may be structurally unobservable.
```

This is similar to a ceiling effect.

When both models can solve the task, the experiment may show no difference even if a difference would appear under higher complexity, longer context, unstable assumptions, or mid-task premise shifts.

## What the Experiment Did Not Measure

The experiment did not appear to stress the zone where higher-level reasoning may matter most:

```text
long-running real work
premise changes midstream
conflicting context
handoff instability
scope drift
silent false completion
multi-repo dependency
unclear Decision Owner boundary
resource tradeoff under pressure
```

If those failure conditions are absent, the comparison mainly tests whether both models can handle a bounded self-contained task.

It does not test whether the higher model can detect failure modes that only appear past the lower model’s complexity threshold.

## V13 Interpretation

V13 should not select models only by average performance on simple tasks.

The key question is:

```text
At what complexity level does the current model stop seeing the real failure mode?
```

A stronger model may matter less when the task is:

```text
short
self-contained
single-step
low-stakes
well-specified
below the lower model’s ceiling
```

A stronger model may matter more when the task includes:

```text
long context
multi-day continuity
hidden contradictions
unclear gates
public-surface risk
handoff responsibility transfer
mid-loop premise changes
Resource Justice tradeoffs
```

## V13 Rule Candidate

```text
Do not infer “no model difference” from tasks that never cross the lower model’s complexity threshold.
```

Japanese:

```text
下位モデルの複雑性閾値を超えないタスクだけで、「モデル差がない」と結論づけない。
```

## Relation to Fable / Opus

This note does not assert a universal performance ranking.

It records a structural limitation:

```text
If Opus-level capability is sufficient for the task,
Fable-level additional capability may not have a place to appear.
```

Therefore, a “no difference” result under threshold-level tasks does not prove that the higher model has no operational value.

It only shows that the tested task did not require the higher capability.

## Better Test Design

To test the threshold hypothesis, use tasks where failure modes emerge over time:

```text
premises change midway
instructions conflict
handoff state becomes stale
public-facing surface must be checked
one AI claims completion too early
new context invalidates an earlier plan
resource constraints change the correct action
multiple repos or documents interact
```

The comparison should observe:

```text
Which model detects the hidden shift?
Which model asks for re-entry clarification?
Which model marks UNKNOWN rather than hallucinating closure?
Which model refuses false PASS?
Which model preserves the human Seat?
Which model reduces rather than increases review burden?
```

## V12 Connection

A model comparison should not count completion as PASS unless it includes:

```text
what was inspected
what was not inspected
what was inferred
what remains UNKNOWN
whether rendered or external surfaces were actually checked
whether completion is YES / NO / CONDITIONAL
```

Otherwise, the experiment may confuse fluent completion with verified completion.

## V14 Connection

Higher models are not automatically justified.

Resource Justice asks:

```text
Does the stronger model reduce downstream correction, review burden, false completion, or rework enough to justify its cost?
```

Below the complexity threshold, maybe not.

Above the threshold, possibly yes.

The boundary matters.

## Do Not Use This Note To Claim

Do not use this note to claim:

```text
Fable is always better
Opus is insufficient
simple benchmarks are useless
all comparisons are invalid
higher-cost models should always be used
```

The narrower lesson is:

```text
A comparison must include tasks where the alleged advantage has a chance to appear.
```

## One-line Lesson

```text
A model’s advantage is invisible below the complexity threshold where the weaker model already succeeds.
```

Japanese:

```text
弱いモデルでも成功できる複雑性閾値以下では、上位モデルの優位性は見えない。
```

## Current Gate

```text
Field Note: PASS
External claim: HOLD
Benchmark implementation: BLOCK
Model superiority claim: BLOCK
Future experiment design: CAP
```

## Completion Line

This Field Note records the complexity-threshold limitation in model comparison.

A “no difference” result on tasks below the lower model’s capability ceiling does not prove the higher model has no value. It only shows that the tested task did not cross the threshold where the higher model’s additional capability could become observable.
