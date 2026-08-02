# V9 Product Adoption Self-Use Receipt v0.1

Status: `INVALIDATED — PRODUCT ATTRIBUTION NOT ESTABLISHED`

As-of: 2026-08-02 JST

Repository: `shin4141/decision-os-v13-loopkit`

Observed case: PR #61 — `Show Contract as not used for manual runs`

## 1. Forward-Only Correction

The original version of this receipt classified the PR #61 merge closure as a
bounded V9 Product Adoption self-use `PASS`.

That classification was incorrect.

The merge closure was performed by GPT 13-28 through the ChatGPT GitHub
Connector after the Connector was reconnected. The Decision-OS Companion did
not run, and no LoopKit user-facing capability was used to produce the benefit
that Shin reported.

The fact that the merged PR belonged to the LoopKit repository does not make
the merge operation a use of the LoopKit product.

Therefore:

- the observed value belongs to the GPT / GitHub Connector operating path;
- it is not evidence that Companion or LoopKit was adopted or useful;
- the original V9 Product Adoption self-use `PASS` is withdrawn;
- V9 Product Adoption self-use remains `NOT ESTABLISHED`.

## 2. What Remains Valid

The underlying event remains real and useful as an operational observation:

1. Codex 13-62 returned an independent read-only `APPROVE` outcome for PR #61.
2. GPT 13-28 accepted the fixed-head closure.
3. The GitHub Connector initially permitted reads but returned
   `403 Resource not accessible by integration` for writes.
4. Reconnecting the GitHub Connector restored the write path.
5. GPT 13-28 then corrected the PR body, recorded closure, moved the PR out of
   Draft, merged the explicitly authorized head, and verified the merged state.
6. Shin reported that avoiding the former approval → merge failure → Codex
   handoff sequence was beneficial.

This establishes a bounded improvement in the GPT / Connector workflow only.
It does not establish product adoption.

## 3. Durable Evidence Anchors

- PR: `https://github.com/shin4141/decision-os-v13-loopkit/pull/61`
- Base commit:
  `c828297f7837f88f992fb0cffe34928c20b6d1dc`
- Accepted repair head:
  `9c437237080649514c82836e9ecd722784955ff6`
- Merge commit:
  `dc6438a65086f29a4621d6a0ee0c46c49cd1e0c9`
- GPT 13-28 closure-acceptance comment:
  `https://github.com/shin4141/decision-os-v13-loopkit/pull/61#issuecomment-5154873305`

## 4. Direct User Value Signal

Shin's direct assessment was:

> 「マージになると俺に聞いてきて承認、失敗、CODEXの流れがなくなったこと自体今は嬉しい」

This is valid evidence that the changed merge workflow felt beneficial to the
operator. It is not evidence that Companion or LoopKit produced that benefit.

## 5. Product Attribution Assessment

### Companion involvement

`NONE`

- No Companion Run was used for the merge closure.
- No Companion UI, Rail, bounded task, Approval flow, or receipt caused or
  completed the merge.

### LoopKit involvement

`CONTEXTUAL ONLY`

- The repository contained LoopKit code and governance terminology.
- V12 / V13 language was used to describe gates and closure.
- Those facts may have shaped the operating discipline, but they do not prove
  use of a LoopKit product capability.

### Actual execution path

`GPT 13-28 + ChatGPT GitHub Connector`

## 6. What This Does Not Establish

This event does not establish:

- creator-owned Companion adoption;
- creator-owned LoopKit product adoption;
- benefit from a LoopKit scan, intake, check, Guided Intake, Manual Bridge,
  Companion Run, Contract flow, Verified Save, or other product surface;
- external-user adoption;
- generalized merge reliability;
- measured reduction in time, tokens, cost, or stress;
- release or publication readiness.

The internal reason the pre-reconnection Connector credential could read but
not write remains `UNKNOWN`.

## 7. Required Re-Evaluation Condition

V9 Product Adoption self-use may be reconsidered only after Shin directly uses
one currently working Companion or LoopKit capability in a real task and can
identify a benefit that would not have occurred from ordinary GPT / GitHub
Connector operation alone.

A qualifying case must identify:

- the exact product surface used;
- the exact user-visible action;
- the output or evidence produced by that surface;
- the human burden or decision quality changed by that output;
- why ordinary GPT operation alone is not sufficient attribution;
- the claim boundary and remaining `UNKNOWN` items.

## 8. Gate State

- V9 Product Adoption — creator-owned self-use: `NOT ESTABLISHED`
- PR #61 merge closure — GPT / Connector workflow value: `OBSERVED`
- Companion involvement in the observed benefit: `NONE`
- LoopKit product attribution: `NOT ESTABLISHED`
- External-user adoption: `NOT ESTABLISHED`
- V13 next loop: `HOLD`
- Live Run / Claude Execution Bridge / Rail reopening / release / publication:
  `BLOCK`

## 9. Completion Line

The false product-attribution claim is withdrawn without erasing the historical
observation. PR #61 remains evidence of a beneficial GPT / GitHub Connector
merge-closure improvement, while V9 Product Adoption self-use remains open
until a real Companion or LoopKit product capability is directly used and
experienced as beneficial.