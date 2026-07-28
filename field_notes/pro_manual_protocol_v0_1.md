# Stage 1 — Pro Manual Protocol v0.1

Status: `MANUAL DEFINITION FIXED / PRO MANUAL RUN 002 NOT AUTHORIZED`
Evidence basis: [V13-SDFP-001 final closure](../validation/v13_sdfp_001_final_closure.md)

## 1. Purpose

Use upper intelligence selectively for design and independent audit. SOL or coding agents observe the repository and implement within the fixed design.
Convert transferable findings into reusable, lower-cost structure instead of requiring permanent upper-model use.

## 2. Preconditions

Before a real Run starts, fix:

```text
Task ID
Objective
Target Repository / Artifact
As-of Commit or Version
Completion Line
Do Not Touch
Current Gate
Authority Boundary
Known UNKNOWNs
```

If any field is incomplete, do not infer it:

```text
HOLD — TASK BOUNDARY INCOMPLETE
```

Artifact identity is necessary evidence; it does not grant authority.

## 3. Fixed Manual Chain

```text
SOL Scout
→ Pro Design
→ SOL / coding-agent Build
→ Independent Pro Audit
→ Reusable Delta Fixation
```

| Step | Owner | Required input | Required output | Exit Gate | One prohibition |
| --- | --- | --- | --- | --- | --- |
| SOL Scout | SOL Scout | Fixed task boundary and exact as-of repository state | One frozen Evidence Packet | `READY FOR PRO DESIGN` or `HOLD — EVIDENCE INSUFFICIENT` | Do not add preferred architecture, design, or implementation. |
| Pro Design | Pro Designer | Frozen Evidence Packet only | One implementable Pro Design Packet | `DESIGN READY FOR BUILD` or `HOLD — DESIGN CANNOT BE FIXED` | Do not write to the repository or treat an UNKNOWN as known. |
| SOL / coding-agent Build | Fresh SOL or coding-agent Builder | Verified Evidence and Design Packets under explicit build authority | Bounded implementation and one Build Receipt | `BUILD READY FOR INDEPENDENT AUDIT` or `HOLD — DESIGN DEVIATION REQUIRED` | Do not silently replace the design or self-certify completion. |
| Independent Pro Audit | Pro Auditor independent of design and build | Packets, Build Receipt, and repository evidence at the recorded commit | One Pro Audit Receipt with `PASS`, `PARTIAL PASS`, or `FAIL` | `SATISFIED` or `HOLD_FOR_REPAIR`; one bounded repair only | Do not mutate the repository or add a new product design. |
| Reusable Delta Fixation | Assigned Reusable Delta Owner | Pro Audit Receipt and traceable source evidence | One Reusable Delta Record | `PASS — REUSABLE DELTA FIXED` or `HOLD — DELTA NOT TRACEABLE` | Do not rewrite frozen evidence or the original result. |

## 4. Required Outputs

```text
Evidence Packet
Pro Design Packet
Build Receipt
Pro Audit Receipt
Reusable Delta Record
```

Use repository-native prose and existing evidence conventions. Do not invent a proof language, ontology, or grammar.
Each receipt claims only its bounded work and evidence; it grants no merge, publication, transfer, or broader product authority.

## 5. Repair Rule

The Independent Pro Audit may return one bounded, forward-only repair to the Builder. It must name the failed condition, source evidence, exact delta,
permitted change surface, required re-test, and repair Completion Line; preserve frozen evidence and the original result in a separate version or
commit; and return once to Independent Pro Audit.

If another route-changing repair is required:

```text
HOLD — NEW GATE REQUIRED
```

Do not continue an unlimited correction loop or add a new feature.

## 6. Reusable Delta Rule

A finding qualifies only when it becomes at least one reusable form:

```text
Guard
test
rule
template
acceptance condition
failure detector
evidence requirement
handoff field
```

The delta must be `forward-only`, `condition-bound`, and traceable to source
evidence. It must preserve the original result rather than rewrite it.
Fixation does not authorize reuse; voluntary reuse remains Shin's value and
risk judgment.

## 7. Human / AI Boundary

```text
Shin:
direction, value judgment, risk tolerance, externalization, final Seat

AI / execution side:
evidence gathering, implementation, validation, receipts, routine cleanup
```

Routine repository work, Git handling, validation, evidence placement, and cleanup must not be returned to Shin.

## 8. Completion Standard

This protocol is complete when the next bounded real task can instantiate the
five-step chain without redesigning the protocol itself.

```text
This document defines Stage 1.
It does not authorize Pro Manual Run 002.
```
