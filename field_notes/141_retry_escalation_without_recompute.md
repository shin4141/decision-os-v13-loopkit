# Field Note 141 — Retry Escalation Without Recompute

Status: Field Note Candidate / Canon promotion HOLD

As-of: 2026-08-26 JST

Primary layer: V13 — Compound Loop / Loop Governance

Secondary residue: V14 — Resource Justice

## Observation

A bounded repository-maintenance task produced a failure on an external write-capable execution route.

Instead of first classifying the failure and updating the method, the next attempts increased execution pressure while leaving the method semantics materially unchanged.

The observed pattern was:

```text
attempt
-> failure cause remains unknown
-> same method retriggered
-> same method recreated
-> external side effects expand
-> method finally changes
-> objective succeeds
```

Repository-bound review later verified that the incident was not merely a conversational recollection. The execution history contained two divergent Git chains from a common base, three failed GitHub Actions runs with zero jobs created, a retrigger-only delta that did not change method semantics, an exact recreation of the same temporary-workflow blob, and a later successful direct-write route that abandoned the failed Actions method.

The exact private repository, commit, workflow-run, and notification identities were verified during review. They are intentionally not copied into this public Field Note because the reusable V13 lesson does not require exposing the private execution surface.

## Structural mechanism

The distinct failure family is:

```text
causal learning remains flat
+
execution pressure increases
+
side effects expand
```

The problem is not retry itself.

The problem is treating failure only as `objective still unmet` instead of also treating it as evidence about method validity, causal understanding, and stopping conditions.

A failed loop can therefore look active while failing to compound:

```text
failure
-> no causal delta
-> no method delta
-> stronger execution
```

This is not a useful Compound Loop. It can become a 0.99 loop because cost and external effects increase while learning remains flat.

## Candidate Core Line

> **A failed loop must change the next loop. If it changes only the execution pressure, it is not compounding.**

## Evidence-classified retry Gate

This is a candidate Gate, not Canon.

After a failed attempt, preserve the failure evidence and classify it as one of:

```text
TRANSIENT
METHOD-RELEVANT
UNKNOWN
```

### TRANSIENT

One bounded retry may proceed only when:

- the transient cause is evidenced;
- the method remains valid;
- side effects are bounded; and
- a retry CAP is fixed.

### METHOD-RELEVANT

HOLD the current method.

Update at least one of:

- the causal hypothesis;
- the changed variable;
- the method itself.

Increasing execution pressure is not a valid delta.

### UNKNOWN

HOLD.

Perform bounded read-only diagnosis before another attempt.

Do not retrigger, recreate, or strengthen the same write-capable method while the failure cause remains unknown.

### Same failure family with no causal or method delta

BLOCK the current method under the current Gate.

A later attempt is not permanently forbidden. It requires a new admissible basis:

```text
documented evidence delta
+
method validity
+
bounded side effects
+
explicit Gate
```

Attempt count alone neither authorizes retry nor permanently forbids it.

### New external side effects

If a failed route starts producing new external effects — notifications, cost, state mutation, account risk, user-visible noise, or other burden — BLOCK escalation until the effects, owner, and rollback are understood.

## Relation to existing V13 notes

This note does not replace Field Note 029, `Fixpoint Learning and Breakout Loop`.

Field Note 029 already establishes that failure becomes useful only when its difference is preserved and converted into a sharper future detector. This note adds a narrower negative pattern: the system may continue acting after failure while preserving almost no causal learning and increasing execution pressure instead.

This note also does not replace Field Note 087, `Rechallenge Gate`.

Rechallenge Gate allows a previously failed route to become eligible again when conditions, evidence, cost, learning, bounded downside, or total EV have changed. Therefore, this note must not become a simplistic numeric rule such as `two failures -> permanent BLOCK`.

The relevant distinction is not retry count. It is whether the next attempt has a legitimate causal or method delta and bounded downside.

## V14 residue

The primary failure is V13: the loop degraded because failure evidence did not change the next loop soon enough.

A secondary V14 question appears when that degradation transfers burden outward:

```text
V13:
Why did the loop fail to compound?

V14:
Who paid for the extra attempts and side effects?
```

In the source incident, external notification burden was directly reported by the Decision Owner. The exact notification count was not established, so this note does not quantify Human Carrier cost.

## Non-claims

This note does not establish that:

- every failed attempt requires a different method;
- two failures always require BLOCK;
- transient retries are generally unsafe;
- the observed GitHub Actions failure cause is known;
- the mechanism is already validated across domains;
- this Gate should be enforced in runtime, API, CI, or product code now.

## Promotion evidence still missing

Canon promotion remains HOLD until later evidence can test at least the following:

- the same mechanism appears in another task or domain;
- this Gate actually stops a harmful same-method retry;
- a safe transient retry is not unnecessarily blocked;
- retry CAP and method BLOCK do not create unacceptable false positives;
- UNKNOWN failures can be held safely long enough for bounded diagnosis.

## Capsule 201 relationship

Current applicability remains CONDITIONAL.

No Capsule 201 modification is required by this Field Note Candidate. Reconnect only when a future runtime or API path proposes external retry, workflow/job retriggering, write-capable automation, repeated failed external action, or material retry side effects.

## Boundary

This is a Field Note Candidate only.

Do not promote it into Canon from this single incident.
Do not modify Capsule 201 from this note alone.
Do not add runtime retry enforcement.
Do not convert the Gate into a universal attempt-count rule.

## V13 Signal

Signal:

```text
GREEN  — DISTINCT FAILURE FAMILY CAPTURED
GREEN  — REPOSITORY-BOUND INCIDENT EVIDENCE VERIFIED
GREEN  — EVIDENCE-CLASSIFIED RETRY GATE RECORDED
YELLOW — CROSS-DOMAIN VALIDATION NOT YET ESTABLISHED
YELLOW — CANON PROMOTION HOLD
YELLOW — CAPSULE 201 APPLICABILITY CONDITIONAL
```

V12 State:
PASS

V13 Next Loop Gate:
HOLD — promotion only

Reason:
The reusable mechanism and bounded Gate are now preserved as an evidence-backed Field Note Candidate, but one incident is not enough to justify Canon, Capsule activation, or runtime enforcement.

Re-evaluation trigger:
Observe a later failed external action where this Gate either prevents a same-method escalation or incorrectly blocks a demonstrably safe transient retry.
