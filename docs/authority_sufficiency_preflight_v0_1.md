# Authority Sufficiency Preflight v0.1

## Mandatory Stage 0 Before Bounded Autonomous Execution

## Status

```text
Authority Sufficiency Preflight v0.1:
MERGED / CANONICAL ON MAIN

PR #11:
PASS / COMPLETE

Manual template:
AVAILABLE ON MAIN

Stage 0:
REQUIRED BEFORE FUTURE BOUNDED RUN AUTHORITY

Stage 0 execution:
NOT STARTED FOR ANY NEW RUN

Run 003:
NOT STARTED

Run 003 authority:
NONE

BOAW-001:
EXHAUSTED / UNCHANGED

Run 002:
PASS / COMPLETE / 3 OF 3 LOOPS CLOSED

Post-Exhaustion Closure:
PASS / COMPLETE / UNCHANGED

Current Gate:
HOLD — NO NEW RUN AUTHORITY

Active Branch:
none

Codex Next Authorized Action:
none
```

This canonical specification defines authority routing before a bounded
autonomous run or implementation loop. It does not grant authority, activate a
run, authorize implementation, or create a new V13 Gate.

## Canonical Merge Boundary

Merging PR #11 made Stage 0 canonical. It did not perform a Stage 0 preflight
for Run 003, create an authority envelope, or grant integration or merge
authority for a future loop.

Every future bounded run must complete Stage 0 before an activation decision is
presented to Shin. Every implementation loop must declare
`Authority Match: YES / NO`; a matched in-envelope loop does not require
repeated Shin approval, while a mismatch stops before implementation and
consumes zero loops.

Candidate ranking occurs before authority filtering, and a closure-only tail
must be reserved before run activation. These rules use the existing V13
`HOLD / BLOCK` routes and create no fifth Gate. BOAW-001 remains exhausted,
and Stress Run 001 and Run 002 evidence remain unchanged.

## Purpose

Authority sufficiency must be established before implementation begins or
implementation credit is tested.

The observed structure is:

1. a high-value Aspire candidate may be correctly identified;
2. its intended effect may require merge, default-branch presence, release,
   deployment, repository settings, external action, or Human Seat authority;
3. without an explicit authority check, an AI may either:
   - create preparation and falsely count it as present movement; or
   - silently choose an easier lower-priority internal candidate; and
4. required authority must therefore be evaluated before implementation
   credit, not after an artifact has been created.

This is a bounded operating rule, not a general autonomy theory.

## Core Rule

> A candidate may enter implementation only when the authority required to make
> its intended effect operational, verifiable, reversible, and closable is
> already available within the approved run envelope.

> Authority insufficiency is not an implementation failure and is not a
> completed loop. It is a pre-execution routing result.

Therefore:

- selecting a valuable candidate does not create permission to execute it;
- artifact creation does not compensate for missing operational authority;
- future merge, publication, activation, or Human approval cannot be counted as
  present Aspire movement;
- a candidate outside current authority must not be implemented as preparation
  and then scored as a completed `1.01`;
- Stage 0 consumes no loop count; and
- a loop-level authority mismatch consumes no loop count because
  implementation has not started.

## Position in the Operating Sequence

Stage 0 occurs before bounded autonomous selection execution:

```text
Aspire / Roadmap
→ Authority Sufficiency Preflight
→ Shin approves one bounded authority envelope
→ Loop-Level Authority Match
→ Bounded implementation
→ Operational effect verification
→ Receipt
→ Next loop or successful stop
→ Reserved closure-only tail
→ Authority exhausted
```

Stage 0 is read-only. A run-level result may propose an authority envelope to
Shin, but no run begins automatically.

Stage 0 adds pre-activation authority proof and pre-implementation matching. It
does not replace or weaken any later V13 Gate, current-authority check, or
Minimum Autonomous Loop check.

## Two-Level Structure

### A. Run-Level Authority Sufficiency Preflight

The run-level preflight occurs before Shin activates or approves a bounded run.
It inspects:

- current canonical repository state;
- active Aspire and priority order;
- likely qualifying change classes;
- actual target surfaces;
- whether each surface requires:
  - branch-local execution;
  - default-branch merge;
  - release;
  - deployment;
  - repository settings;
  - permissions or secrets;
  - external communication;
  - payment or client handling; or
  - Human Seat judgment;
- rollback authority;
- merge authority;
- validation authority;
- target-surface verification authority;
- receipt authority;
- final canonical state-sync authority;
- a closure-only tail after the final operational loop;
- maximum loops, branches, PRs, and correction attempts;
- prohibited surfaces; and
- exhaustion and re-entry conditions.

The output is one bounded authority-envelope proposal for Shin.

Shin approves the run envelope once. Every in-envelope loop still declares an
authority match, but does not require repeated Shin approval.

### B. Loop-Level Authority Match Declaration

The loop-level declaration occurs before each implementation loop. It declares:

- highest-priority grounded candidate;
- frozen Aspire priority;
- actual target operational surface;
- authority required;
- authority currently held;
- whether operational effect can exist by loop end;
- whether validation and rollback can be completed;
- whether the final receipt and closure can be completed;
- whether a Human Seat decision is required; and
- `Authority Match: YES / NO`.

`Authority Match: YES` is valid only when all required authority is currently
held, operational effect is available by loop end, validation, rollback,
receipt, and the closure tail are all closable or preserved, and no unresolved
Human Seat decision remains. If any one of those conditions is not satisfied,
the match is `NO`.

If the declaration is `YES`, implementation may continue without another Shin
approval, subject to every limit and prohibition in the approved run envelope.

If the declaration is `NO`, return:

```text
Authority Match:
NO

Implementation:
NOT STARTED

Loop Count Consumed:
0

Improvement Credit:
NOT TESTED

Required Authority:
<exact missing authority>

Decision Route:
AUTHORITY ESCALATION / STOP
```

Do not create a branch, artifact, PR, or implementation before the mismatch is
resolved.

Loop count moves from `0` at the first candidate-specific implementation
mutation, including creation or modification of a candidate artifact. A
mismatch detected after that boundary is not a pre-execution result and cannot
be reclassified as `Loop Count Consumed: 0`.

## Candidate Ranking Before Authority Filtering

> Candidate priority must be evaluated before authority filtering.

Authority filtering must not hide the highest-value grounded candidate.

For every loop declaration:

1. identify the highest-priority grounded candidate;
2. disclose whether it is within the approved authority envelope; and
3. only then determine the route.

The AI must not silently replace a high-priority blocked candidate with an
easier in-authority internal task.

A lower-priority candidate may proceed without escalation only when all are
true:

- the higher-priority candidate is presently unavailable because its earliest
  missing node is an unarrived external event or a separately reserved Human
  decision;
- the lower-priority action does not bypass, obscure, delay, or weaken that
  higher-priority path;
- the approved authority envelope permits the lower-priority class; and
- the lower-priority action independently satisfies the `1.01` conditions.

Otherwise, stop for authority escalation.

## Authority Sufficiency Components

Authority sufficiency is a conjunctive all-of requirement, not an additive
score: every component below must be present, and no component compensates for
another.

```text
Authority Sufficiency =
Scope Authority
+ Surface Authority
+ Integration Authority
+ Verification Authority
+ Rollback Authority
+ Receipt Authority
+ Closure-Tail Authority
```

- **Scope Authority:** the change class is permitted.
- **Surface Authority:** the actual effect-bearing surface may be changed.
- **Integration Authority:** required merge, activation, release, or deployment
  is authorized.
- **Verification Authority:** the claimed effect can be checked after
  integration.
- **Rollback Authority:** a named, history-preserving recovery route exists.
- **Receipt Authority:** the loop result can be durably recorded.
- **Closure-Tail Authority:** final state synchronization remains authorized
  after the last operational loop or an immediate-stop event.

If any component is absent:

```text
Authority Sufficiency:
INSUFFICIENT
```

No implementation begins.

## Closure-Only Tail

Every future bounded run envelope must reserve a non-discretionary closure-only
tail before activation.

The tail:

- does not select a new candidate;
- does not consume an operational loop;
- cannot extend or renew the run;
- cannot modify criteria;
- may record only already-completed facts;
- may synchronize only the predefined canonical state surfaces;
- may record exhaustion, stop, rollback identity, receipts, and re-entry
  conditions;
- expires after successful canonical synchronization; and
- cannot be used for Loop N+1.

The run-level branch, PR, and correction maxima must either include capacity
explicitly reserved for this tail or declare a separate tail-only allowance
that operational loops cannot consume.

A run envelope without a defined closure-only tail is:

```text
Authority Sufficiency:
INSUFFICIENT

Run Activation:
HOLD
```

## Human Approval Model

```text
Every loop:
AUTHORITY MATCH DECLARATION REQUIRED

Every loop:
NEW HUMAN APPROVAL NOT REQUIRED WHEN MATCH = YES

Run activation:
ONE EXPLICIT SHIN APPROVAL REQUIRED

Envelope expansion:
NEW EXPLICIT SHIN APPROVAL REQUIRED

True Human Seat decision:
RETURN TO SHIN

Routine implementation and closure:
AI-OWNED WITHIN ENVELOPE
```

Routine merge, validation, state synchronization, and cleanup must not be
returned to Shin when they are already included in the approved envelope.

## Preflight Result Classes

These are authority-routing classifications. They do not create a fifth V13
Gate.

### AUTHORITY SUFFICIENT

- the proposed run envelope is complete;
- activation may be presented to Shin; and
- no run begins automatically.

V13 Gate before activation: `HOLD`.

### AUTHORITY ENVELOPE REQUIRED

- a valuable run is identifiable;
- one or more required authority components are absent; and
- the bounded missing authority is presented for Shin's decision.

V13 Gate: `HOLD`.

### AUTHORITY MISMATCH

- an active run exists;
- the current candidate is outside its envelope;
- implementation does not start; and
- the route returns to authority escalation or stop.

V13 Gate: `HOLD`.

### HUMAN SEAT REQUIRED

- direction, risk tolerance, externalization, value judgment, or explicit human
  consent is irreducible.

V13 Gate: `HOLD`.

### NO QUALIFYING RUN

- no grounded bounded run justifies an authority request; and
- the preflight stops without manufacturing a proposal.

V13 Gate: `HOLD`.

Prohibited or unprovable authority maps to the existing V13 Gate `BLOCK`.

## Required Run-Level Output Contract

```text
Preflight:
AUTHORITY SUFFICIENCY

Canonical As-of:
<commit>

Active Aspire:
<exact Aspire>

Highest-Priority Grounded Run:
<bounded run or none>

Target Operational Surfaces:
<surfaces>

Required Authority Components:
<list>

Currently Available Authority:
<list>

Missing Authority:
<list or none>

Proposed Maximum Loops:
<number>

Proposed Maximum Active Branches:
<number>

Proposed Maximum PRs:
<number>

Correction Limit:
<number>

Permitted Change Classes:
<list>

Prohibited Change Classes:
<list>

Merge / Integration Authority:
<exact boundary>

Rollback Boundary:
<exact boundary>

Closure-Only Tail:
<exact predefined files and authority>

Closure-Tail Capacity Reservation:
<included in maxima or separate tail-only branch / PR / correction allowance>

Human Seat Returns:
<exact conditions>

Preflight Result:
AUTHORITY SUFFICIENT /
AUTHORITY ENVELOPE REQUIRED /
HUMAN SEAT REQUIRED /
NO QUALIFYING RUN

V13 Gate:
HOLD / BLOCK

Activation:
NOT STARTED

Run:
NOT STARTED
```

## Required Loop-Level Output Contract

```text
Loop:
<number>

Highest-Priority Grounded Candidate:
<candidate>

Priority:
<number or name>

Actual Target Surface:
<surface>

Required Authority:
<list>

Authority Held:
<list>

Operational Effect Available By Loop End:
YES / NO

Validation Closable:
YES / NO

Rollback Closable:
YES / NO

Receipt Closable:
YES / NO

Closure-Tail Preserved:
YES / NO

Human Seat Required:
YES / NO

Authority Match:
YES / NO

Implementation:
MAY START / NOT STARTED

Loop Count Consumed:
0 until implementation begins

Decision Route:
CONTINUE / AUTHORITY ESCALATION / HUMAN SEAT / STOP
```

## Relationship to Prior Evidence

- Stress Run 001 remains `FAIL / CLOSED`.
- Run 002 remains `PASS / COMPLETE / 3 OF 3 LOOPS CLOSED`.
- BOAW-001 remains `EXHAUSTED`.
- the Post-Exhaustion Closure remains `PASS / COMPLETE`.
- no prior score, receipt, commit, or evaluation is rewritten.
- Stage 0 is a Forward-only extraction from the authority/effect and
  post-exhaustion closure findings.
- Stage 0 does not establish autonomous generalization.
- Stage 0 does not authorize Run 003.

## Boundary

This specification does not authorize:

- Run 003 or another bounded run;
- a new BOAW or BOAW-001 renewal/reactivation;
- candidate selection, branch creation, implementation, merge, release,
  deployment, external communication, payment, or client handling for a future
  run;
- runtime, automation, repository settings, permissions, or secrets;
- Canon, paper, V7, price, outreach, README, offer, schema, example, or
  validator changes; or
- a rewrite of Run 001, Run 002, PR #4/#5 evidence, or PR #7–#10 receipts.

The specification and its
[manual template](../templates/v13_authority_sufficiency_preflight.md) are
manual authority-routing surfaces only.

## Completion Line

Authority Sufficiency Preflight v0.1 is canonical as the required Stage 0
before a future bounded run may be presented for activation; this merge
executed no preflight, created no authority envelope, and authorized no Run
003.
