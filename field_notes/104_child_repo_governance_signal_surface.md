# Field Note 104: Child Repo Governance Signal Surface

## Layer

V13 / Derived Repo Governance / Signal Surface

Adjacent layers:

- V9 As-of / stale-state auditability
- V10 Goal-Length / bounded continuation
- V12 Completion Integrity / reconciliation before continuation
- V14 Resource Justice / avoiding hidden operational burden

## Summary

Entry Window Radar showed that V13 governance can transfer into a derived repo through Launch Capsule, AGENTS.md, STATUS.md, phase gates, and HOLD/BLOCK boundaries.

However, this also exposed an important visibility problem:

```text
V13 governance can be working,
but if the child repo does not emit visible signals,
users and future AIs may not understand what the governance prevented.
```

The value of V13 is often an absence:

```text
scope did not expand
stale state did not continue
Phase 5 was not falsely marked PASS
Delivery Scope Radar did not merge into the MVP
V14 deep scoring did not leak into the free core
external posting did not begin prematurely
```

But absence is hard to perceive.

Therefore, a child repo that inherits V13 governance needs a visible Signal Surface.

## Source Observation

Observed in the Entry Window Radar derived repo during Phase 5.1 governance reconciliation.

Child repo path:

```text
/Users/sn/Documents/Entry Window Radar
```

Relevant commit:

```text
c9f8312 Reconcile governance state after README phase
```

Files changed in the child repo:

```text
STATUS.md
AGENTS.md
```

The reconciliation corrected stale governance fields:

```text
Phase 4 changed from HOLD to PASS.
Phase 4 commit was recorded.
Phase 4 was removed from Missing Closure.
Phase 5 was represented as FAIL / Reconciliation in progress, not PASS.
Phase 5.1 was marked PASS.
Next owner now points to rerunning Phase 5 Acceptance Audit v0.2.
Phase 6 remains HOLD.
External API and posting remain HOLD.
Delivery Scope Radar and V14 deep scoring remain BLOCK.
```

## What V13 Successfully Prevented

The important success was not just that files were updated.

The success was that the repo did not continue from stale governance state.

Without reconciliation, the child repo could have treated Phase 5 as complete while its recorded state still contained unresolved Phase 4 closure.

This would have created a false-continuation risk:

```text
old state
-> treated as current state
-> next phase continues
-> governance appears present but is actually stale
```

V13 prevented this by forcing reconciliation before continuation.

## Signal Surface Problem

From the inside, this is clearly valuable.

From the outside, it may look like:

```text
STATUS.md was edited
AGENTS.md was edited
some gates were updated
```

A third-party user may not immediately see that V13 prevented a false PASS or stale-state continuation.

This matters because V13 often works by preventing invisible failures.

If those prevented failures are not surfaced, the user may feel that the governance adds overhead without visible benefit.

## Required Signal Surface

When V13 governance is transferred to a child repo, the child repo should make the following visible somewhere appropriate, usually STATUS.md, AGENTS.md, or a short audit result:

```text
Current Gate
Last PASS
Current HOLD
Current BLOCK
Missing Closure
Next allowed action
Next blocked action
Last prevented failure or stale-state correction
Recheck condition
```

The signal does not need to be long.

It needs to let the next human or AI answer:

```text
What just got prevented?
Why are we stopped here?
What is safe to do next?
What is still blocked?
```

## V13 Learning

The learning is:

```text
V13 governance must not only transfer.
It must emit visible signals in the child repo.
```

A Launch Capsule can carry the boundary.
AGENTS.md can carry rules.
STATUS.md can carry current state.
Acceptance Audit can detect drift.
Reconciliation can repair stale state.

But the child repo still needs a visible signal that explains why the governance mattered.

## Not a MISTAKEN.md Entry Yet

This is not yet a MISTAKEN.md rule.

Reason:

```text
This is an observed design learning, not a repeated failure pattern.
```

Promote to MISTAKEN.md only if future derived repos repeatedly inherit V13 governance but fail to show visible current-state or prevented-failure signals.

Possible future MISTAKEN rule:

```text
Do not transfer governance without a visible child-repo signal surface.
```

For now, keep it as a Field Note.

## Future Reuse

This pattern should be checked when V13 produces future derived repos:

```text
Field Note
-> Launch Capsule
-> scaffold
-> acceptance audit
-> governance reconciliation if stale
-> visible signal surface in child repo
```

A child repo should not merely inherit V13 constraints.

It should show the user and the next AI how those constraints are currently shaping safe continuation.

## Completion Line

Entry Window Radar revealed a reusable V13 learning:

```text
A child repo can inherit V13 governance successfully,
but the value remains hard to perceive unless the repo exposes visible signals of current gate, blocked scope, stale-state correction, and next allowed action.
```

This field note records that learning for future derived repo launches.
