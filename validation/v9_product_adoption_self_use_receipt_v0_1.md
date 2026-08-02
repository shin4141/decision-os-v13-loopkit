# V9 Product Adoption Self-Use Receipt v0.1

Status: Creator-owned self-use evidence

As-of: 2026-08-02 JST

Repository: `shin4141/decision-os-v13-loopkit`

Observed case: PR #61 — `Show Contract as not used for manual runs`

This receipt records one bounded creator-owned self-use adoption event. It is
not external-user adoption, measured effectiveness, population evidence, or a
guarantee that future merge operations will succeed.

## 1. Proof Claim

In the PR #61 closure, GPT 13-28 completed the routine GitHub closure path from
accepted independent review through merge and post-merge verification without
returning the GitHub merge operation or a merge handoff to Shin or to a new
Codex execution thread.

The bounded value claim is:

> In this one creator-owned case, the final merge closure remained inside the
> GPT operating thread instead of returning routine merge execution and
> reconnection work to the human Decision Owner.

## 2. Operator-Reported Baseline

Shin reported that earlier GPT merge attempts had failed more than twenty
times and had repeatedly produced the following burden pattern:

1. GPT asks for merge approval.
2. Shin approves.
3. GPT merge fails.
4. The operation is handed to Codex.
5. State and completion must be reconnected across threads.

The count and historical sequence are operator-reported. This receipt does not
independently reconstruct or verify every prior merge attempt.

## 3. Current Self-Use Path

The observed PR #61 path was:

1. Codex 13-62 returned an independent read-only outcome of `APPROVE` at head
   `9c437237080649514c82836e9ecd722784955ff6`.
2. GPT 13-28 accepted the review closure and recorded V12 Completion Integrity
   as `PASS` for the bounded repair.
3. The GitHub Connector write path initially returned
   `403 Resource not accessible by integration` while reads still succeeded.
4. The GitHub Connector was reconnected. Write access then recovered.
5. GPT 13-28 corrected the PR body, recorded the closure acceptance, and kept
   release-related gates blocked.
6. Shin explicitly authorized merge of the fixed head.
7. GPT 13-28 moved the PR out of Draft, merged it, and read back the closed and
   merged state.

No manual PR-body edit or manual GitHub merge was left to Shin after the
Connector write path recovered. No new Codex merge-execution thread was
required.

## 4. Durable Evidence Anchors

- PR: `https://github.com/shin4141/decision-os-v13-loopkit/pull/61`
- Base commit:
  `c828297f7837f88f992fb0cffe34928c20b6d1dc`
- Accepted repair head:
  `9c437237080649514c82836e9ecd722784955ff6`
- Merge commit:
  `dc6438a65086f29a4621d6a0ee0c46c49cd1e0c9`
- GPT 13-28 closure-acceptance comment:
  `https://github.com/shin4141/decision-os-v13-loopkit/pull/61#issuecomment-5154873305`
- Final PR state observed after merge:
  `closed / merged`

## 5. Direct User Value Signal

Shin's direct assessment was:

> 「マージになると俺に聞いてきて承認、失敗、CODEXの流れがなくなったこと自体今は嬉しい」

This statement establishes a creator-owned subjective value signal for the
bounded workflow change. It does not quantify time saved, stress reduction, or
future reliability.

## 6. What This Establishes

This receipt establishes only that:

- one creator-owned PR closure reached merge and post-merge verification inside
  GPT 13-28;
- the routine GitHub merge operation was not returned to Shin;
- a separate Codex merge-execution handoff was not required;
- Shin identified the absence of the former approval-failure-Codex sequence as
  beneficial.

## 7. What This Does Not Establish

This receipt does not establish:

- that every future GPT merge will succeed;
- that the earlier reported merge-failure count has been independently audited;
- that LoopKit alone caused the improved result;
- that external users would experience the same benefit;
- any quantified reduction in time, tokens, cost, or stress;
- generalized product adoption;
- release readiness or publication suitability;
- the internal reason the pre-reconnection GitHub credential could read but not
  write.

The internal cause of the earlier Connector write failure remains `UNKNOWN`.

## 8. Forward-Only Delta

A separate forward-only operating rule was identified during the case:
GitHub browser, CLI, in-app browser, local Git, execution agent, and Connector
credentials must be treated as separate authentication boundaries. A
read-success/write-failure result must not be converted directly into human
manual cleanup before the acting write boundary and reconnect path are
checked.

This delta is not itself the adoption proof. The adoption proof is the completed
human-burden-free merge closure in this bounded case.

## 9. Gate State

- V9 Product Adoption — creator-owned self-use, bounded merge-closure claim:
  `PASS`
- External-user adoption: `NOT ESTABLISHED`
- Generalized merge reliability: `NOT ESTABLISHED`
- V13 next loop: `HOLD`
- Live Run / Claude Execution Bridge / Rail reopening / release / publication:
  `BLOCK`

## 10. Completion Line

One creator-owned self-use adoption event is fixed: PR #61 was independently
reviewed, explicitly authorized, merged, and verified without returning routine
merge execution or a Codex merge handoff to Shin, and Shin reported that this
change was beneficial.