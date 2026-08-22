# Field Note 130: Orchestration Boundary Layer

Date: 2026-08-08

Lifecycle status: Verification pending

Primary layer: V13

Supporting conceptual connection: V11 only as provenance of the discovery path

Canon promotion: HOLD

## Classification

- Artifact type: V13 Field Note
- Field Note type: Self-Application
- Status: Advisory discovery residue / verification pending
- Gate: GO for recording / HOLD for design, implementation, promotion, or
  Stage 4/5 integration

V11 is recorded only as provenance of the discovery path. This is not an
AGENTS.md Compactor feature.

This Field Note is advisory discovery residue only. It does not authorize new
Stage 4 implementation, new Stage 5 implementation, authority-schema changes,
Companion Manual Bridge changes, AGENTS.md changes, runtime changes,
current_signal changes, handoff changes, README changes, or publication claims.

## Problem

As the number of agents, delegated duration, and delegated scope increase,
individual AGENTS.md files may become insufficient for multi-agent
orchestration.

An individual AGENTS.md can state what that agent should do, but authority
boundaries are relational:

- what this agent owns;
- what it must not own;
- where authority transfers to a coordinator;
- where another agent's authority begins.

A boundary exists between actors and therefore cannot be validated merely by
one actor declaring its own boundary.

The coordinator has the reciprocal problem: reading multiple individual
AGENTS.md files does not by itself establish that their authority allocations
are mutually consistent.

## Existing V13 Connections

The following are conceptual connections only. They do not prove that a new
layer already exists and do not authorize changes to the referenced work.

### 1. Stage 4 Role Separation Validator

The concern is structurally related to the failure mode where one caller can
self-generate `trusted_*` authority in the same context.

Candidate principle:

```text
self-declared authority boundary != independently validated authority boundary
```

Do not modify Stage 4.

### 2. Stage 5 Seat Concepts

Existing Seats describe differentiated roles such as:

- Structure Discovery Seat
- Counter-Structure Audit Seat
- Implementation Compiler Seat
- Operational Runtime Seat

The unresolved question is not only which role exists, but how the authority
boundary between roles should be represented.

Do not modify Stage 5.

### 3. Companion Manual Bridge

Role Assignment is currently the nearest existing representational precedent.

This is only a possible future connection. Do not extend the Companion Manual
Bridge in this task.

## Two-Layer Distinction

### Layer 1: Information-volume control

Object: how much instruction material an individual agent keeps always active.

Existing product: AGENTS.md Compactor.

### Layer 2: Orchestration authority-boundary control

Object: who may do what, how far authority extends, and where authority
transfers between multiple agents / coordinator.

Status: unimplemented future V13 candidate.

These layers must not be collapsed.

## Candidate Hypothesis

A future orchestration system may require a coordinator-owned boundary map
separate from each individual agent's AGENTS.md. This map could describe
cross-agent authority relationships.

This is only a hypothesis. It does not specify a final schema, create
`asserted_*` or `trusted_*` fields, create runtime behavior, or decide whether
the candidate belongs in the Companion Manual Bridge or a separate component.

## Why It Is Intentionally Unresolved

- Stage 4 D-1 through D-3 remain relevant prerequisites: `asserted_*` naming,
  `UNKNOWN` handling, and As-of / revocation.
- Stage 5 proof remains immature.
- Adding a new active component before those tracks settle would create new
  unresolved operational debt.
- Therefore this note preserves the discovery without authorizing the next
  implementation loop.

## Re-evaluation Trigger

Re-open this Field Note only after BOTH are true:

1. Stage 4 authority-boundary prerequisites are settled sufficiently to know
   how asserted / trusted / UNKNOWN / revocation should behave.
2. Stage 5 has enough concrete evidence to judge whether Seat assignment alone
   is insufficient in actual multi-agent orchestration.

Until then:

```text
HOLD — DESIGN NOT AUTHORIZED
```

## Missing Closure

Unknown / intentionally deferred:

- representation format for cross-agent authority boundaries;
- coordinator read/validation behavior;
- consistency checking against individual AGENTS.md;
- whether Stage 4 vocabulary transfers;
- whether this extends Companion Manual Bridge or becomes a separate component.

## Explicit Non-Authority Statement

This Field Note is advisory discovery residue only.

It does not authorize:

- new Stage 4 implementation;
- new Stage 5 implementation;
- authority-schema changes;
- Companion Manual Bridge changes;
- AGENTS.md changes;
- runtime changes;
- current_signal changes;
- handoff changes;
- README changes;
- publication claims.
