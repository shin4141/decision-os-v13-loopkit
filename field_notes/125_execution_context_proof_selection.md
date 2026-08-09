# Field Note 125: Execution Context Proof Selection

Date: 2026-07-13

## Lifecycle Status

- Current status: Canon-promoted
- Original status: Candidate / verification pending
- Learning direction: Forward-only operational learning
- Operational validation: complete — [validation record](../validation/field_note_125_operational_validation.md)
- Canon location: [`AGENTS.md` — Continuation Proof Selection](../AGENTS.md#continuation-proof-selection)
- Runtime implementation: not implemented
- Automation: HOLD
- Publication: HOLD

## Layer

V13 / continuation proof / destination and artifact authority

Adjacent layers:

- V12 Completion Integrity
- Human Seat / unpersisted judgment
- Handoff and restartability

## Evidence Basis

The original Candidate was grounded in the verified `output-surface-integrity-report` workspace at local commit `7d54394e64c268b7a4035e4fa11140f0b1338071`.

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

## Candidate Validation Status — Historical

At Candidate creation, the validation status was:

```text
Candidate / verification pending
```

Minimum future validation:

1. Artifact-sufficient continuation succeeds without chat identity.
2. Chat-specific unpersisted judgment correctly requires Destination Identity in addition to relevant artifact provenance.
3. Proof failure produces a precise, restartable BLOCK without human cleanup.

At Candidate creation, this rule was required to remain a Candidate until all three categories were observed under bounded conditions. Case 3 later separated into transport failure and historical path reconciliation.

The required categories and both Case 3 paths are now complete in the [operational validation record](../validation/field_note_125_operational_validation.md). This closes the Candidate validation condition without rewriting the earlier state.

## Forward-Only Canon Adoption

Date: 2026-07-13

Decision Owner approval: explicit and bounded to the validated core and Path Reconciliation Rule.

Promotion evidence:

- Case 1 — Artifact-sufficient continuation: `PASS`;
- Case 2 — Unpersisted context-specific judgment: `PASS`;
- Case 3A — Transport proof failure: `PASS`;
- Case 3B — Historical path reconciliation: `PASS / RECONCILIATION SUFFICIENT`;
- evidence record: [`validation/field_note_125_operational_validation.md`](../validation/field_note_125_operational_validation.md).

The rule is no longer only a hypothesis because the three required validation categories changed later operational handling: persisted evidence enabled continuation without chat identity, unpersisted judgment required Destination Identity, missing proof produced a restartable stop, and uniquely proven one-level relocation supported bounded reconciliation.

### Canon Core Adopted

Use the minimum sufficient proof required by the continuation dependency. Fixed artifacts are the default source of authority. Destination Identity is added only when authorized continuation depends on genuinely unpersisted, context-specific judgment.

If sufficient proof cannot be established, `BLOCK` before modification, identify the exact missing or mismatched proof, and do not return routine recovery to the Decision Owner.

The three outcomes remain:

1. `Artifact Provenance Guard`;
2. `Artifact Provenance + Destination Identity Guard`;
3. `BLOCK — sufficient proof unavailable`.

Destination Identity does not replace relevant Artifact Provenance. A result that may exist but cannot be traced and registered from the receiving surface remains:

```text
PENDING HANDOFF ASSERTION — NOT CANONICALLY VERIFIED
```

### Bounded Path Reconciliation Rule Adopted

When an authorized task names a missing artifact path, the execution AI may reconcile it without returning routine path work to the Decision Owner when:

- one current canonical root is registered;
- exactly one role-matching artifact exists within a directly explainable child directory;
- current canonical records bind its role and identity;
- freshness and uniqueness are established;
- the requested operation is independently authorized.

Record the expected and resolved paths and continue only inside the authorized scope.

`BLOCK` when identity, uniqueness, freshness, authority, or relocation remains ambiguous.

Artifact existence alone never grants execution authority.

This rule does not authorize broad path guessing, fuzzy matching as authority, cross-repository substitution, or version substitution.

### Exact Artifact Identity and Mutable Paths

When exact artifact identity matters, do not treat a mutable path or an
observed version as durable identity. Establish evidence proportional to the
claim, such as a preserved or currently qualified artifact, content identity
or SHA-256 where applicable, an exact version probe, and a recoverable or
reinstallable source when rerun identity is required.

If historical artifact equality cannot be established, do not silently
substitute the current occupant of a path or another version. Use a new
Forward-only As-of qualification and preserve the historical identity as
`UNKNOWN` where its bytes or custody cannot be recovered.

A path can contribute to identity when an authoritative custody system makes
it immutable or separately binds it to exact content. This rule is therefore
not a universal hashing requirement for ordinary files or executable use where
exact artifact identity is not part of the claim.

Origin and promotion evidence:
[`Field Note 129`](129_mutable_path_is_not_artifact_identity.md) and
[`Stage D dogfood 001`](../validation/stage_d_leave_the_desk_dogfood_001.md).

### Transport Clarification

Transport failure is not evidence failure.

When transport prevents proof access, promote no claim, preserve the exact missing proof and re-entry condition, resume only after artifact identity becomes verifiable, and do not return routine transport repair to the Decision Owner.

This remains subordinate to proof selection and does not create a transport framework.

### Falsifier, Countercondition, and Downgrade

Downgrade or narrow this Canon routing if later evidence shows that it:

- permits an incorrect artifact or context to control authority;
- hides ambiguity in identity, freshness, uniqueness, ownership, or authorization;
- causes bounded path reconciliation to substitute across repositories or versions;
- adds default-path burden without changing operational decisions.

Rollback is a Forward-only lifecycle downgrade from `Canon-promoted` to the appropriate verification-pending, superseded, or archived status, with the triggering evidence and replacement authority recorded. Do not erase the Candidate, validation, or adoption history.

## Non-Claims and Boundaries

- This note does not prove that Destination Identity is never needed.
- This note does not make file hashes proof of semantic completeness or authorization.
- This note does not promote pending Output Surface Integrity assertions.
- This note does not implement a validator, hook, automation, transport system, MCP surface, or plugin.
- This note does not authorize publication, report-body drafting, productization, or a new execution branch.

## Historical Candidate Gate

At Candidate creation, the Gate was:

```text
Field Note Candidate record: PASS
Future validation: HOLD / verification pending
Canon promotion: HOLD
Implementation / automation: HOLD
Publication: HOLD
```

## Current Canon Gate

```text
Canon adoption: PASS
Operational validation: COMPLETE
Runtime implementation: NOT IMPLEMENTED
Automation: HOLD
Publication: HOLD
```

## Historical Candidate Completion Line

V13 preserves Execution Context Proof Selection as an evidence-backed but unvalidated Field Note Candidate. Artifact Provenance remains the default when fixed artifacts are sufficient; Destination Identity is added only for genuinely unpersisted context-specific judgment. No implementation, Canon promotion, or next branch is activated.

## Current Completion Line

Field Note 125 is adopted as V13 Canon through a bounded Forward-only delta. V13 defaults to persisted Artifact Provenance, adds Destination Identity only when continuation depends on unpersisted context-specific judgment, and permits bounded AI-owned path reconciliation only when identity, uniqueness, freshness, and independent authorization are all established.
