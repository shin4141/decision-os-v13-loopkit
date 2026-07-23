# V7 Forward-only Architectural Delta v0.1 — Aspire-Serving Motion Obligation

## Status

```text
PRIVATE FORWARD-ONLY ARCHITECTURAL DELTA
NOT A REWRITE OF PUBLISHED V7
NOT YET PUBLISHED
NOT CANON PROMOTION
RUNTIME BLOCKED
```

Date:
`2026-07-23`

Repository As-of before this delta:
`344cdaf8cf87291c346518c5d31e9b8a93cc7f9b`

Primary layer:
`V7 — Aspire / Guard architecture`

Supporting layers:
`V10 — Protective and Accelerative Rescale`;
`V13 — Progress Preservation and Protective Stasis detection`;
`V12 — restartable non-GO closure`.

## Forward-only and Published-V7 Boundary

This delta does not silently alter the published V7 As-of.

It records a Forward-only candidate for a future V7 revision, addendum, or
series-level architectural statement. Published V7 remains historically valid
at its own As-of.

The delta exists because later operational evidence exposed a failure mode that
was not sufficiently explicit in the earlier public surface. Recording that
later evidence does not retroactively rewrite the earlier source or promote
this private delta into published V7 or Canon.

## Problem

Decision-OS learns strongly from observable accidents. Each accident can
produce a new Guard, `CAP`, `HOLD`, or restriction, while the opportunity loss
caused by stopping is less directly observable.

Without a countervailing architectural obligation, updates can become
asymmetric:

```text
accident
→ more protection

bounded success or capability improvement
→ no corresponding path expansion
```

This pattern can produce Protective Stasis: the architecture appears to avoid
failure by preventing Aspire from being realized.

## Architectural Invariant

Core Guard remains non-negotiable.

Inside the admissible space that remains after Core Guard, the architecture
must preserve at least one concrete Aspire-serving path whenever such a path
can be made reversible, exposure-limited, testable, or safely branchable.

Preserving a path does not mean that every reversible action must proceed. A
path may remain available as a bounded branch, comparison, test, or explicitly
restartable route without receiving execution authority.

### English principle

> A system that preserves Guard by indefinitely suppressing all Aspire-serving
> motion has not preserved the architecture; it has collapsed into protective
> stasis.

### Japanese principle

> Aspireに仕えるあらゆる前進を無期限に抑圧することでGuardを守る
> システムは、構造を保全したのではない。防御的停滞へ崩壊している。

### Short rule

> Guard must prevent inadmissible motion.
> It must not eliminate admissible motion.

### Japanese short rule

> Guardは許容不能な前進を止めなければならない。
> 許容可能な前進まで消してはならない。

## Required Guard Asymmetry

### Core Guard

Core Guard may override an Aspire-serving route when that route is
inadmissible. Aspire, opportunity cost, reversibility, bounded success, or
capability improvement does not override Core Guard.

### Operational Guard

Operational Guard remains subordinate to preserving safe movement toward
Aspire inside the admissible space. It must apply the least-restrictive
sufficient constraint supported by the current Protected Object and evidence.

This is not a statement that all Guard is subordinate to Aspire. Core Guard
determines admissibility; the motion obligation operates only after that
boundary has been preserved.

## Motion and Authority Axes

Aspire service, Core-Guard admissibility, and current execution authority are
separate:

- `ADMISSIBLE`: current bounded evidence establishes that the route remains
  inside the applicable Core Guard boundary;
- `INADMISSIBLE`: a proven applicable Core Guard or equivalent hard boundary
  excludes the route;
- `UNKNOWN`: neither state is established; execution remains `HOLD`, and the
  unknown state must receive an explicit evidence or re-evaluation condition.

Reversibility, limited exposure, testability, and safe Branching are containment
properties. They can make an admissible route safer to preserve or examine, but
they do not by themselves prove admissibility. An admissible route also does
not automatically receive execution authority.

A safer replacement retains comparable Aspire-directed reachability only when
it remains comparable against the Decision Owner's current Aspire and the
preserved historical comparison line, rather than criteria authored solely by
the replacement itself. No validated numeric reachability metric is introduced
by this delta.

## Forward-Motion Obligation

When at least one bounded Aspire-serving route remains admissible, the system
must do one of the following:

1. preserve that route;
2. replace it with a safer route that retains comparable Aspire-directed
   reachability;
3. temporarily constrain it with an explicit restart condition;
4. provide sufficient current hard-boundary evidence explaining why no
   admissible route remains.

Operational Guard must not silently erase all Aspire-serving motion. A
completed stopping justification must identify:

- a specific Protected Object;
- a concrete expected harm;
- current evidence;
- a least-restrictive alternative analysis;
- the opportunity cost of stopping;
- a restart or re-evaluation condition.

`Hard Guard: UNKNOWN` is not evidence that a route is admissible and grants no
permission to cross the uncertain boundary. It also must not become an
unrecorded permanent stop: the non-`GO` closure must preserve an explicit
evidence, restart, or re-evaluation condition.

The following are not architectural success:

- indefinite `HOLD` without a restart or evidence condition;
- repeated `CAP` that never permits its own success condition to become
  observable;
- removal of comparison, challenge, or learning routes more broadly than the
  Protected Object requires.

An incomplete stopping justification creates no automatic `GO`. The required
correction is to preserve or replace the minimum admissible route, define a
restartable temporary constraint, or supply sufficient current hard-boundary
evidence.

## Success and Capability Update Obligation

Bounded success does not automatically authorize acceleration.

When credible current evidence of repeated or reproducible bounded success,
equal or lower recovery cost, non-increasing Recovery Debt, preserved
functional Human Seat, stable or expanded Branching, continued Aspire service,
and Carrier absorption indicates that an Operational Guard may no longer be
the minimum necessary restriction, the system must re-evaluate path expansion.

Use:

```text
ACCELERATIVE RESCALE EVALUATION REQUIRED
```

The required action is evaluation. Automatic acceleration, Goal-Length change,
authority expansion, and execution remain blocked unless separately decided
through their applicable authority and Gate.

## Layer Separation

### V7

Defines the architectural obligation to preserve admissible Aspire-serving
motion.

### V10

Determines whether Goal-Length should remain, contract, or expand through
Protective or Accelerative Rescale. V10 evaluates survivability and Rescale; it
does not replace Guard or grant V13 execution authority.

### V13

Detects Protective Stasis, requires least-restrictive constraints, and routes
`GO / HOLD / CAP / BLOCK`. Protective Stasis remains a bounded candidate
diagnosis and never creates automatic `GO`.

### V12

Requires a non-`GO` decision to leave an explicit restartable closure. A
restart condition records how reconsideration becomes possible; it creates no
automatic monitoring or restart.

These roles must not be collapsed.

## V13 Progress Preservation Connection

The
[Progress Preservation Principle v0.1](progress_preservation_principle_v0_1.md)
remains the V13 operational specification.

This V7 delta supplies its Forward-only architectural parent obligation. V13
Protective Stasis detection, least-restrictive constraint analysis, and
restartable non-`GO` routing are the bounded manual enforcement mapping of that
obligation.

Core Guard remains unchanged. This connection authorizes no validation,
runtime, automatic monitoring, automatic opportunity-cost scoring, automatic
acceleration, or path execution.

## Non-Authority Boundary

This delta does not:

- modify the published V7 manuscripts or their historical As-of;
- weaken Core Guard or permit Aspire to override it;
- subordinate all Guard to Aspire;
- require every reversible or bounded action to proceed;
- infer admissibility from the absence of an observed accident;
- convert missing stop evidence into permission;
- create automatic `GO`, acceleration, Rescale, Goal-Length change, path
  expansion, or execution;
- create a numeric risk, success, or opportunity-cost threshold;
- modify V10, V12, V13, PIC, Guard, MAL, Case 004, or Field Note source
  definitions;
- create runtime, automation, monitoring, publication, or Canon authority;
- define a new Aspire or bypass a value-bearing Human Seat decision.

## Publication and Re-entry Condition

Publication, incorporation into a future V7 revision or addendum, or
series-level architectural promotion requires a later explicit Human Seat
decision.

Operational validation, runtime design, and automatic acceleration remain
outside this delta. A later evaluation may compare this candidate against real
or frozen evidence, but this task supplies no authority to begin that work.

## Completion Line

This private Forward-only V7 delta closes the architectural gap in which Guard
could appear preserved by eliminating all admissible Aspire-serving motion:
Core Guard remains non-negotiable, Operational Guard must preserve or
explicitly close at least one least-restrictive admissible path, and credible
absorbed repeated success may require Accelerative Rescale evaluation without
authorizing automatic acceleration, publication, runtime, or execution.
