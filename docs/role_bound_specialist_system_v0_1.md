# Role-Bound Specialist System v0.1

## Boundary

This is the minimal V13 Stage 4 implementation. Stage 4 covers explicit Role
assignment, Role-bound work, a fixed Specialist Lens, and an inert Coverage
Gap Recommendation. Only `BUILDER` and `AUDITOR` exist in v0.1. Scout,
Architect, Companion integration, Runner integration, automatic specialist
invocation, and all Stage 5 decisions are outside this implementation.

```text
Stage 4:
Role assignment
Role-bound work
Specialist Lens
Coverage Gap Recommendation

Stage 5:
GO / HOLD / CAP / BLOCK the recommended specialist loop
```

```text
Recommendation: ALLOWED
Automatic Assignment: PROHIBITED
Automatic Invocation: PROHIBITED
```

## Authority and activation

A Role originates only from Shin's authority. An AI cannot assign itself a
Role. A Role name, artifact declaration, `producer_role`,
`builder_generated`, different artifact bytes, specialist recommendation, or
model self-description is never sufficient.

A Role is Active only when all of the following are established:

1. an `EXPLICIT_ROLE_GRANT` exists;
2. `assignment_authority` is `Shin`;
3. a non-placeholder Shin Gate reference exists;
4. the assignee identity is fixed;
5. the trusted execution context identity is fixed;
6. the Contract claims Role Acceptance and a receiver-side trusted Role
   Acceptance record establishes `ACCEPTED`;
7. the complete Role Contract and its canonical hash are fixed;
8. the Task Artifact Packet is fixed;
9. the Specialist Lens identity, version, and hash are fixed;
10. every required independence dimension is independently satisfied;
11. the grant has not expired; and
12. the grant has not been revoked.

Missing, unknown, or unverifiable state never becomes Active. A new Role,
authority, operation, target, or Lens requires a new Shin Gate.

The Role Contract's own authority fields are declarations, not proof of their
provenance. `validate_role_operation` therefore requires a
`trusted_role_grant` supplied independently of the Role Contract and operation
request. The trusted grant must bind the exact contract ID/hash, task, Role,
Grant type, Shin authority and Gate reference, assignee, and trusted execution
context. Contract self-declaration without this out-of-band evidence is HOLD.

The same separation applies to acceptance and independence.
`validate_role_operation` requires all four trusted inputs independently of
the claimant-controlled operation request:

```text
trusted_role_grant
trusted_role_acceptance
trusted_independence_evidence
trusted_prior_role_bindings
```

The request's `independence_evidence` and `prior_role_bindings` remain claims.
They must match the trusted records, but they are never the source of truth.
The trusted independence record binds its evidence identity to the exact task,
Role, assignee, execution context, and model. Every trusted prior-Role binding
does the same. Evidence identities must be unique, and the trusted binding
source must supply the complete same-task binding set. An adapter must not
construct a `trusted_*` input by copying claimant payload.

The receiver-side Role Acceptance record is also separate from the Contract
and request:

```json
{
  "contract_id": "contract-auditor-001",
  "contract_hash": "<canonical SHA-256>",
  "task_id": "task-stage4-001",
  "role_id": "AUDITOR",
  "assignee_identity": "auditor-assignee",
  "execution_context_identity": "trusted-auditor-context",
  "role_acceptance": "ACCEPTED",
  "accepted_at": "2026-07-29T00:01:00Z"
}
```

It must match the exact Contract ID/hash, task, Role, assignee, and execution
context. `accepted_at` must be timezone-aware, no earlier than issuance,
earlier than expiry, and no later than validation time. The Contract's own
`role_acceptance: ACCEPTED` is a hashed requirement claim, not receiver-side
proof.

## Contract identity

The schema is
[`schema/v13_role_contract.schema.json`](../schema/v13_role_contract.schema.json).
It separates contract identity, assignment, owned responsibility, operations,
Task Artifact Packet, Specialist Lens, independence profile, completion,
lifecycle, and Coverage Gap Recommendation.

`contract_hash` is the lowercase SHA-256 of canonical JSON with these rules:

1. replace `contract_identity.contract_hash` with the empty string;
2. encode JSON as UTF-8 with sorted keys, no insignificant whitespace, and
   non-ASCII characters preserved; and
3. hash the resulting bytes.

`decision_os.role_contract.compute_contract_hash` is the reference
implementation.

## Builder

Builder owns only implementation of the specified Design at the specified
paths and head under the specified Completion Line. It cannot self-audit,
change a Role Grant or Specialist Lens, change anything outside the exact
target, merge, post, invoke a specialist, or start Stage 5.

## Auditor

Auditor owns only read-only inspection of the fixed head, artifacts, evidence,
Role Contract conformity, and target immutability. It cannot change the
target, implement a repair, also act as Builder, merge, post, invoke a
specialist, or start Stage 5.

An Auditor must use a trusted execution context distinct from Builder's.
The same base model is allowed only when the Role Contract says
`SAME_MODEL_ALLOWED`. Model diversity never substitutes for context
independence.

## Independent dimensions

The four independence fields are separate and non-substitutable:

- `role_context_independence`
- `source_review_independence`
- `runtime_execution_independence`
- `model_diversity`

A different model is not a different context. A different context is not an
independent runtime execution. An independent runtime execution is not
independent evidence selection. `REQUIRED_NOT_ESTABLISHED`, missing evidence,
and unknown evidence remain HOLD. Independence decisions use only the trusted
out-of-band evidence and binding set. Claim/trusted mismatches are BLOCK.

## Specialist Lens

[`templates/v13_specialist_lens.md`](../templates/v13_specialist_lens.md)
defines the required Lens sections. The Role Grant selects the Lens; the
assignee cannot self-select it. Identity or hash absence or mismatch keeps the
Role inactive.

## Coverage Gap Recommendation

Every Role Exit Receipt includes the coverage result. No-gap receipts say
exactly `Coverage Gap: NONE DETECTED`. The recommendation records completed
coverage, the gap, recommended specialist, reason, exact target, required
evidence, urgency, and the two fixed controls:

```json
{
  "assignment_authority_required": true,
  "automatic_invocation": false
}
```

The recommendation is data only. Creating or validating it produces no Role
Assignment event, Runner/Codex/agent invocation, or Stage 5 decision.

## Semantic validation

`decision_os.role_contract.validate_role_operation` validates the complete
contract, one independently supplied trusted Role Grant, one receiver-side
trusted Role Acceptance record, trusted independence evidence, the complete
trusted prior-Role binding set, and one requested operation. It is
deterministic and read-only. It checks explicit authority and Gate binding,
assignee/context binding, receiver acceptance, exact packet and Lens
identities, scope and path identity, role-specific forbidden operations,
lifecycle, each independence dimension, and recommendation inertness.

The first closed attack is same-context false division: a trusted context
cannot create Builder artifact A, create different Audit artifact B, omit
producer metadata, and become Auditor. The trusted context binding produces:

```text
BLOCK — CONTEXT INDEPENDENCE VIOLATION
```

Omitting that true same-context Builder binding from the request and replacing
it with a forged different-context binding does not help: the complete trusted
binding set still exposes the collision, and the claim/trusted mismatch is
also recorded.

No automatic assignment or invocation function exists in this module.
