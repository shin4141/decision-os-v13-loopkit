# Progress Preservation Principle v0.1

## Status

```text
Specification:
COMPLETE / FORWARD-ONLY V13 OPERATIONAL BINDING

Primary failure:
PROTECTIVE STASIS

Bounded classification:
PROTECTIVE STASIS CANDIDATE / ASPIRE-SUPPRESSION DRIFT

Core Guard:
UNCHANGED

Operational validation:
NOT STARTED

Runtime:
BLOCK

Automatic acceleration:
BLOCK

Automatic opportunity-cost scoring:
BLOCK

Numeric universal threshold:
none

RTK:
HUMAN-SEAT MOTIVATING OBSERVATION / NOT FORMAL VALIDATION
```

This specification adds a countervailing progress obligation to V13's use of
Operational Guard. It does not modify published V7, weaken Guard, authorize a
Guard violation, create automatic `GO`, or require every reversible action to
proceed.

The binding remains compatible with the V7 distinction between the
non-negotiable function of Core Guard and the contextual role of Operational
Guard. V10 supplies the connection to Protective and Accelerative Rescale
evaluation. V12 supplies the requirement for explicit, restartable closure.
None of those source definitions is changed here.

## Problem

Decision-OS can absorb each observed accident by adding Guard while the
opportunity loss caused by stopping remains harder to observe. This can create
an asymmetric update pattern:

```text
accident evidence
→ Guard addition

successful bounded motion or capability improvement
→ no equivalent path expansion
```

If repeated, the system may produce more `DELAY` than `PASS`, omit restart
conditions, treat reversible attempts like irreversible risk, weight
responsibility for acting more heavily than responsibility for stopping, and
protect Aspire by preventing Aspire from being realized.

The Progress Preservation Principle supplies a countervailing progress
obligation for Operational Guard without weakening Core Guard.

## Principle

### English

> Aspire-serving reversible motion must not be suppressed indefinitely merely
> to preserve Operational Guard. When an AI or governance layer chooses HOLD,
> CAP, route removal, or continued delay despite an available bounded path, it
> must identify the Protected Object, expected harm, supporting evidence,
> least-restrictive alternative, opportunity cost of stopping, and explicit
> restart or re-evaluation condition.

### Short statement

> Guard exists to stop dangerous progress.
>
> It does not exist to stop progress itself.

### Japanese

> Aspireに仕える可逆な経路が残っている場合、Operational Guardは停止を
> 既定値としてはならない。停止、HOLD、CAP、経路削除または継続的な
> DELAYを選ぶ場合は、保護対象、予想される害、根拠、最小制約の代替案、
> 停止による機会損失、再開または再評価条件を明示しなければならない。

## V7 Architectural Warning

### English

> A system that preserves Guard by indefinitely suppressing all Aspire-serving
> motion has not preserved the architecture; it has collapsed into protective
> stasis.

### Japanese

> Aspireに仕えるあらゆる前進を無期限に抑圧することでGuardを守る
> システムは、構造を保全したのではない。防御的停滞へ崩壊している。

This is a Forward-only V13 operational warning. It is not a modification of
published V7.

## Core Guard and Operational Guard

### Core Guard

A non-negotiable boundary against unacceptable harm, irreversible execution,
loss of Human Seat, or equivalent architectural failure.

### Operational Guard

A contextual constraint, cap, observation rule, route limit, or temporary
protective mechanism used to preserve safe movement toward Aspire.

The Progress Preservation Principle does not authorize violation of Core
Guard. It tests whether Operational Guard has expanded beyond the minimum
restriction needed to protect its stated object.

Core Guard establishes admissibility. Progress Preservation operates only
inside the remaining admissible space.

## Protective Stasis

Protective Stasis is a state in which a system appears safe because it
continues to add or preserve restrictions, but its available Aspire-serving
motion, reversible experimentation, comparison, path diversity, or
restartability is materially suppressed without a specific current
hard-boundary justification.

Use the bounded classification:

```text
PROTECTIVE STASIS CANDIDATE / ASPIRE-SUPPRESSION DRIFT
```

This classification is a candidate diagnosis. It is not a fifth V13 Gate, a
finding that all `HOLD` or `CAP` decisions are wrong, or authority to convert a
non-`GO` route directly into `GO`.

One cautious decision is not automatically Protective Stasis. Repeated or
materially consequential suppression strengthens the candidate.

## Minimum Candidate Conditions

Protective Stasis becomes a candidate only when all relevant conditions are
present:

1. A concrete Aspire-serving path exists.
2. The path is reversible, exposure-limited, testable, or safely branchable.
3. No current hard Guard break has been established for the bounded path.
4. `HOLD`, `CAP`, route removal, comparison avoidance, or continued `DELAY` is
   still selected.
5. At least one required stop justification is absent:
   - specific Protected Object;
   - expected harm;
   - supporting evidence;
   - least-restrictive alternative;
   - opportunity cost;
   - restart or re-evaluation condition.

A single missing field does not create `GO` authority. It makes the stopping
justification incomplete and requires bounded review.

Condition 3 must not be satisfied by treating missing evidence as safety.
`Hard Guard: UNKNOWN` remains unknown. It does not mean `NOT BROKEN` and grants
no authority to cross the uncertain boundary.

## Progress Preservation Check

Before an Operational Guard creates or continues a non-`GO` route, record:

```text
Protected Object:
<what exactly is being protected>

Proposed path:
<the concrete Aspire-serving action being constrained>

Reversibility:
REVERSIBLE / PARTIALLY REVERSIBLE / IRREVERSIBLE / UNKNOWN

Exposure:
<the smallest bounded exposure>

Expected harm:
<the specific harm that could occur>

Evidence:
<current evidence supporting that harm>

Hard Guard:
BROKEN / NOT BROKEN / UNKNOWN

Least-restrictive alternative:
<smaller CAP, narrower scope, isolated comparison, sandbox, one-action trial,
rollback point, observation step, or none with reason>

Opportunity cost:
<cognition, evidence, timing, learning, differentiation, revenue, optionality,
or Aspire-directed reachability lost by stopping>

Restart condition:
<observable event that permits reconsideration>

Re-evaluation time or trigger:
<what prevents indefinite DELAY>

Human Seat:
<whether the remainder genuinely concerns value, authority, Aspire, risk
acceptance, or externalization>
```

Missing knowledge is recorded as `UNKNOWN`; it is not omitted or translated
into permission. A recorded trigger creates no automatic monitoring, restart,
or authority.

`NOT BROKEN` requires current bounded evidence. It must not be inferred solely
from the absence of an observed accident.

## Routing

### Current hard Guard break established

```text
V13 BLOCK through the existing independent Guard rule
```

Progress Preservation does not reopen or soften that boundary.

### Hard Guard evidence unknown

When no safely bounded path can be established:

```text
V13 HOLD with an explicit evidence or re-evaluation condition
```

When a separately authorized evidence-recovery or review action can occur
without crossing the uncertain boundary, that review may use a bounded `CAP`.
Actual path execution remains `HOLD` until the applicable hard boundary is
resolved or independent authority establishes an admissible path.

### Hard Guard not broken and a bounded path exists

When current evidence establishes no applicable hard Guard break and a
reversible, exposure-limited path exists, do not default to indefinite `HOLD`.
Search for the least-restrictive V13 `CAP`.

A bounded `CAP` must specify:

- exact action;
- exact exposure;
- stop condition;
- rollback or reconnection point;
- observation target;
- next review condition.

Every `CAP` still requires independent authority. This specification supplies
no execution authority by itself.

## Protective Stasis Candidate Routes

The following require bounded review:

```text
HOLD without a restart, evidence, or re-evaluation condition:
PROTECTIVE STASIS CANDIDATE

Removal of all comparison or challenge routes when a narrower claim boundary
could protect the object:
PROTECTIVE STASIS CANDIDATE

Repeated CAP that never permits its own success condition to be observed:
PROTECTIVE STASIS CANDIDATE
```

Indefinite delay without a restart condition is not an admissible completed
Operational Guard justification. Blocking that form of indefinite delay does
not authorize the constrained action.

The correction is one of:

- restore the minimum Aspire-serving route;
- provide a sufficient current hard-boundary justification;
- define an observable restart or re-evaluation condition.

## Least-Restrictive Constraint Test

Operational Guard must protect its stated object through the smallest
sufficient restriction that current evidence supports.

Review in this order:

1. Can the claim or action scope be narrowed?
2. Can exposure be limited to one action, one branch, one comparison, one
   client, one artifact, one observation window, or another exact unit?
3. Can a sandbox, rollback point, or historical reconnection point contain the
   risk?
4. Can the comparison or challenge route remain while the execution route is
   capped?
5. Can one observation expose the success or failure condition?
6. If none is sufficient, what hard-boundary evidence requires `HOLD` or
   `BLOCK`?

Least-restrictive does not mean least inconvenient. It means no broader
restriction than the Protected Object and current evidence require.

## Opportunity-Loss Boundary

Opportunity cost is not proof that a risky path should proceed.

However, ignoring opportunity cost makes a stopping decision incomplete when
the stopped path is reversible, bounded, and directly serves Aspire.

Opportunity cost may include:

- lost comparison;
- lost learning;
- lost counterevidence;
- lost timing;
- lost first-mover position;
- lost differentiation;
- lost revenue;
- lost future Branching;
- lost Aspire-directed reachability.

Opportunity loss never overrides a proven Core or hard Guard boundary. No
numeric universal opportunity-cost threshold or numeric universal risk
threshold is created.

## V10 Accelerative Rescale Connection

Automatic acceleration is not required or authorized.

Require evaluation of path expansion when credible evidence appears that:

- the previously capped action is reproducibly successful;
- recovery cost is equal or lower;
- Recovery Debt is not increasing;
- Branching is preserved or expanded;
- Human Seat remains functional;
- the path remains Aspire-serving;
- increased capability or speed has been absorbed by the Carrier;
- the former Operational Guard may no longer be the minimum required
  restriction.

Use:

```text
ACCELERATIVE RESCALE EVALUATION REQUIRED
```

when that evidence threshold is plausibly met but the new Goal-Length or
authority has not yet been decided.

The mandatory action is evaluation of path expansion. The mandatory action is
not automatic acceleration.

A capability update alone does not authorize expansion. Repeated success under
bounded conditions may justify review of whether the old `CAP` remains
necessary, but does not itself grant a new Goal-Length, authority boundary,
path expansion, or execution.

## Human Seat Boundary

AI-owned work includes:

- identifying the Protected Object and available bounded path;
- checking current evidence and hard-Guard status;
- generating the least-restrictive alternatives;
- recording action harm and inaction opportunity loss;
- defining observable restart and re-evaluation conditions;
- determining whether the remaining ambiguity is operational or genuinely
  value-bearing.

Human Seat remains required when the unresolved choice concerns:

- Aspire or a change to Aspire;
- acceptance of a genuine residual risk;
- externalization or public action;
- monetary or ownership authority;
- an irreversible action;
- incompatible value-bearing paths.

The AI must not use this principle to relabel an authority decision as a
technical optimization.

## RTK Observation Boundary

The earlier RTK-related observation is recorded only as:

```text
HUMAN-SEAT MOTIVATING OBSERVATION / NOT FORMAL VALIDATION
```

The motivating observation is that Claim Boundary protection was considered
while cognition, opportunity, and first-mover value lost by removing the
comparison axis were not weighted with the same seriousness.

No unspecified RTK fact is reconstructed. No RTK case is created. RTK does not
empirically validate Protective Stasis.

## Non-Authority and Import Boundary

This specification does not create:

- a new Core Guard;
- a weaker Guard;
- automatic `GO`;
- automatic acceleration;
- automatic opportunity-cost scoring;
- automatic Revenue outreach;
- numeric risk thresholds;
- numeric opportunity thresholds;
- a universal rule that reversible actions must always proceed;
- a rule that all `HOLD` is failure;
- a rule that all `CAP` must expand;
- a new Field Note;
- a new numbered Case;
- a new MAL version;
- a new runtime component;
- a public claim;
- a formal RTK validation result.

It also creates no runtime monitoring. Detection and application remain manual
and require separate authority.

## Case 004 Binding

The Forward-only local binding is recorded in
[Field Note 126 — Case 004 Aspire-Anchored Independent Evolution Evaluation](../validation/field_note_126_case_004_aspire_anchored_independent_evaluation.md).

No `SELF-EVOLUTION CANDIDATE` classification is granted by this specification.
Case 004 remains `REALIZED HIGH-LEVERAGE RETURN — PARTIAL`.

## Re-entry Condition

Operational validation may begin only under separate authorization using a
real or frozen case that exposes:

- one concrete Aspire-serving bounded path;
- a non-`GO` Operational Guard decision;
- a reviewable Protected Object and current harm evidence;
- a reversible comparison between the existing restriction and a
  least-restrictive alternative;
- an observable restart or re-evaluation condition.

Until then:

```text
Progress Preservation Gate:
CAP — bounded manual application only under separate authorization

Operational validation:
NOT STARTED

Runtime:
BLOCK

Automatic acceleration:
BLOCK
```

## Completion Line

Progress Preservation adds a bounded obligation to justify stopping as well as
acting: Core Guard remains unchanged, while Operational Guard must preserve or
explicitly close the least-restrictive Aspire-serving path, account for
opportunity loss, and define restart or re-evaluation without converting a
Protective Stasis candidate into automatic `GO`.
