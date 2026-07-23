This template performs authority routing only.
It does not grant authority, activate a run, or authorize implementation.

# V13 Authority Sufficiency Preflight Template

Use this manual template before a future bounded autonomous run and before each
implementation loop inside an approved run envelope.

Governing specification:
[Authority Sufficiency Preflight v0.1](../docs/authority_sufficiency_preflight_v0_1.md).

## 1. Run-Level Authority Sufficiency Preflight

Copy and complete:

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

Run-level rules:

- evaluate the highest-priority grounded run before authority filtering;
- name every required authority component and every missing component;
- reserve the closure-only tail before activation;
- reserve branch, PR, and correction capacity for closure transport inside the
  maxima or as a separate tail-only allowance;
- return the proposed envelope to Shin for one explicit activation decision;
- do not start the run from this template.

## 2. Loop-Level Authority Match Declaration

Copy and complete before implementation:

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

Loop-level rules:

- disclose the highest-priority grounded candidate before checking whether it
  fits the envelope;
- do not silently replace blocked high-priority work with easier internal work;
- allow a lower-priority candidate without escalation only when the
  higher-priority candidate's earliest missing node is an unarrived external
  event or separately reserved Human decision, the lower-priority action does
  not bypass, obscure, delay, or weaken that path, the envelope permits its
  class, and it independently satisfies the `1.01` conditions;
- `Authority Match: YES` permits continuation only inside the approved
  envelope and does not override another Gate or Human Seat boundary;
- require every authority component to be held, all operational-effect,
  validation, rollback, receipt, and closure-tail declarations to be `YES`,
  and `Human Seat Required` to be `NO` before declaring `Authority Match: YES`;
- in-envelope loops do not require repeated Shin approval; and
- a mismatch stops before branch, artifact, PR, or implementation creation and
  consumes no loop.

Loop count moves from `0` at the first candidate-specific implementation
mutation, including creation or modification of a candidate artifact. A later
mismatch cannot be reclassified as a zero-loop pre-execution result.

Envelope expansion requires new explicit Shin approval. A true Human Seat
decision returns to Shin before mutation.

If the authority match is `NO`, preserve:

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

The closure-only tail has no candidate-selection, criteria-change, extension,
renewal, or Loop N+1 authority.
