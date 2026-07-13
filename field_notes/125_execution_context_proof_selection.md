# Field Note 125: Execution Context Proof Selection

Date: 2026-07-13

## Lifecycle Status

- Status: Candidate / verification pending
- Learning direction: Forward-only operational learning
- Canon promotion: HOLD
- Implementation / automation: HOLD
- Publication: HOLD

## Layer

V13 / continuation proof / destination and artifact authority

Adjacent layers:

- V12 Completion Integrity
- Human Seat / unpersisted judgment
- Handoff and restartability

## Evidence Basis

This Candidate is grounded in the verified `output-surface-integrity-report` workspace at local commit `7d54394e64c268b7a4035e4fa11140f0b1338071`.

Inspected evidence surfaces:

- `state/canonical_current_state.md`;
- `evidence/evidence_source_map.md`;
- `CLAIM_BOUNDARY.md`;
- `handoff/current_handoff.md`;
- `validation/bootstrap_validation.md`;
- `validation/post_bootstrap_evidence_delta_intake.md`.

The bootstrap records successful continuation from fixed artifacts, manifests, hashes, state, and handoff evidence. The post-bootstrap intake records a second boundary: claims not traceable from the receiving surface remained explicitly pending even when a successful result was asserted in a handoff.

This note does not reconstruct evidence from conversation memory and does not promote the report workspace's pending assertions.

## Observation

Continuation proof is not one universal identity check.

Some tasks depend only on fixed evidence that can be inspected and verified by any receiving AI. Other tasks depend on a judgment that existed only inside one specific prior execution context and was never persisted into a traceable artifact. Treating both cases alike either creates unnecessary chat-identity searches or overstates what files alone prove.

## Core Rule

Continuation should use the minimum sufficient proof required by the actual dependency of the task.

Use exactly one of three outcomes.

### 1. Artifact Provenance Guard

Use when fixed files, manifests, hashes, state records, and handoffs are sufficient to reconstruct authority and intent.

Artifact Provenance is the default when the authorized continuation can be proven from persisted evidence without relying on the identity of a prior chat or execution context.

### 2. Artifact Provenance + Destination Identity Guard

Add Destination Identity only when the authorized continuation depends on an unpersisted judgment from a specific prior execution context.

Destination Identity does not replace Artifact Provenance when fixed artifacts are also relevant. The combined guard must prove both the persisted evidence and the specific context-dependent judgment.

Destination Identity alone is not sufficient merely because a prior chat produced the work.

### 3. BLOCK — Sufficient Proof Unavailable

Stop before modification when the proof required by the task's actual dependency is missing, mismatched, or not canonically traceable.

The BLOCK must identify the exact missing or mismatched proof. It must not infer ownership, identity, validity, or authority from plausibility.

## Result Existence Versus Registrability

A successful result may exist while a canonically traceable and currently registrable result does not.

When the receiving surface cannot reconnect an assertion to sufficient proof, preserve the exact state:

```text
PENDING HANDOFF ASSERTION — NOT CANONICALLY VERIFIED
```

Do not convert result existence, handoff fluency, file presence, or remembered success into canonical verification.

## Overuse Risks

### Destination Identity Overuse

- makes chat continuity outrank fixed artifacts;
- creates unnecessary valid-context searches;
- returns chat reconstruction burden to the human;
- blocks legitimate continuation by another AI.

### Artifact Provenance Overuse

- treats file identity as proof of semantic completeness;
- treats a stale handoff as current authorization;
- substitutes hashes for unpersisted Human-Seat judgment;
- confuses artifact existence with valid execution authority.

## BLOCK Behavior

When sufficient proof is unavailable:

- identify the exact missing or mismatched proof;
- make no modification governed by that proof;
- do not infer ownership, identity, validity, or authorization;
- do not return chat search, terminal work, transport repair, cleanup, or routine recovery to the Decision Owner;
- preserve a restartable failure report with the last verified evidence and the unresolved dependency.

## Subordinate Transport Lesson

Transport failure is not evidence failure.

When folder or attachment access is unreliable, a self-contained single-file Bundle may be used as a bounded fallback. Preserve role-specific separation and verify SHA-256 where relevant.

The Bundle transports evidence; it does not expand authority, repair missing provenance, prove semantic completeness, or replace a required Destination Identity check.

This note does not create a transport framework or implementation.

## Validation Status

```text
Candidate / verification pending
```

Minimum future validation:

1. Artifact-sufficient continuation succeeds without chat identity.
2. Chat-specific unpersisted judgment correctly requires Destination Identity in addition to relevant artifact provenance.
3. Proof failure produces a precise, restartable BLOCK without human cleanup.

Until all three cases are observed under bounded conditions, this rule remains a Candidate and must not be treated as Canon.

## Non-Claims and Boundaries

- This note does not prove that Destination Identity is never needed.
- This note does not make file hashes proof of semantic completeness or authorization.
- This note does not promote pending Output Surface Integrity assertions.
- This note does not implement a validator, hook, automation, transport system, MCP surface, or plugin.
- This note does not authorize publication, report-body drafting, productization, or a new execution branch.

## Current Gate

```text
Field Note Candidate record: PASS
Future validation: HOLD / verification pending
Canon promotion: HOLD
Implementation / automation: HOLD
Publication: HOLD
```

## Completion Line

V13 preserves Execution Context Proof Selection as an evidence-backed but unvalidated Field Note Candidate. Artifact Provenance remains the default when fixed artifacts are sufficient; Destination Identity is added only for genuinely unpersisted context-specific judgment. No implementation, Canon promotion, or next branch is activated.
