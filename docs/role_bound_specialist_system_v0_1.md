# Role-Bound Specialist System v0.1

## Implementation boundary

This is the minimal V13 Stage 4 validator implementation. It defines a Role
Contract, a fixed Specialist Lens, supplied-record validation, and an inert
Coverage Gap Recommendation for `BUILDER` and `AUDITOR`. It does not issue,
authenticate, transport, discover, or persist Role records. It does not assign
a Role, invoke a specialist, perform Role-bound work, or establish real-world
Role separation.

```text
Stage 4:
Role assignment contract
Role-bound operation validation
Specialist Lens
Coverage Gap Recommendation

Stage 5:
GO / HOLD / CAP / BLOCK the recommended specialist loop
```

Scout, Architect, Companion integration, Runner integration, automatic
specialist invocation, and every Stage 5 decision remain outside this
implementation.

```text
Recommendation: ALLOWED
Automatic Assignment: PROHIBITED
Automatic Invocation: PROHIBITED
```

The implementation boundary is fixed:

```text
Role Separation Enforcement: VALIDATOR-LEVEL ONLY
Record Issuer / Authentication / Transport: NOT IMPLEMENTED
Role Independence: NOT ESTABLISHED
End-to-End False-Division Prevention: NOT ESTABLISHED
```

## Authority declarations and validator-level ACTIVE

The governing rule is that a Role originates only from Shin's authority and an
AI cannot assign itself a Role. This validator does not authenticate Shin or
prove that an assignment event occurred. It checks that supplied fields carry
the required authority value and Gate binding.

A Role name, artifact declaration, `producer_role`, `builder_generated`,
different artifact bytes, specialist recommendation, or model
self-description is insufficient even at the validator boundary.

`ACTIVE` is only a validator result. It means that, at the supplied validation
time, the Contract, request, and separately supplied records satisfy the
implemented structural, binding, timestamp, declared revocation-state,
snapshot, and ordering checks. It does not establish that a Role was actually
granted or accepted, that any record is authentic, that a supplied snapshot is
complete in the real world, or that Role independence exists.

The validator can return `ACTIVE` only when:

1. the Contract declares `EXPLICIT_ROLE_GRANT`,
   `assignment_authority: Shin`, and a non-placeholder Shin Gate reference;
2. the Contract binds task, Role, assignee, execution context, exact target,
   Task Artifact Packet, Specialist Lens, operations, lifecycle, and
   completion;
3. the Contract's canonical hash is valid;
4. the operation request matches the Contract;
5. all required separately supplied records are present and internally valid;
6. all supplied records bind to the required Contract, task, Role, assignee,
   context, model, snapshot, and related record identities;
7. every supplied record is current for the same validation snapshot and has
   an admissible declared revocation state;
8. the supplied prior-Role snapshot carries a valid hash and a declared
   complete same-task boundary;
9. the supplied values satisfy each required validator-level independence
   condition; and
10. the requested operation remains inside the Stage 4 Role boundary.

Missing, unknown, malformed, incomplete, or stale input never becomes
`ACTIVE`. Mismatched, revoked, or observably conflicting input is rejected.
A new Role, authority, operation, target, or Lens requires a new Shin Gate,
but this validator does not create that Gate or the corresponding records.

## Separately supplied validator inputs

`validate_role_operation` accepts four separately supplied record inputs in
addition to the Role Contract and claimant-controlled operation request:

```text
supplied_role_grant
supplied_role_acceptance
supplied_independence_evidence
supplied_prior_role_bindings
```

The names describe how the values enter the validator API. They do not assert
that the values came from an independent party or channel. The implementation
cannot determine whether an adapter copied, fabricated, or coherently rewrote
them.

The request's `independence_evidence` and `prior_role_bindings` remain
claimant-controlled claims. The validator compares them with the separately
supplied inputs. Neither input is treated as authenticated truth, and a
successful comparison proves only internal consistency.

## Common record snapshot and lifecycle fields

The supplied Role Grant, Role Acceptance, and independence evidence records
carry these common fields:

```text
record_identity
snapshot_identity
as_of
revocation_state
revoked_at
revocation_reference
```

The prior-Role snapshot uses `snapshot_identity` as its own identity and
carries the same `as_of` and revocation fields.

All `as_of` values must be timezone-aware and coherent with the normalized
validator time and shared snapshot identity. The normalized `now` value is the
validation snapshot time, and every supplied `as_of` must equal it. An earlier
record is stale and results in HOLD; a future record is rejected as
time-invalid; skew between supplied records results in HOLD rather than
`ACTIVE`.

Revocation state is explicit:

- `NOT_REVOKED` requires both `revoked_at` and `revocation_reference` to be
  null.
- `REVOKED` is rejected; its supplied timestamp and reference do not
  authenticate the revocation source.
- `UNKNOWN`, missing, or internally inconsistent revocation state results in
  HOLD.

Record identities must be unique within one validation bundle. A duplicate
identity, a record bound to an old Contract hash, or another replay indicator
visible in the supplied bundle is rejected. This is not a cross-validation
replay ledger. An exact replay at an indistinguishable evaluation point cannot
be detected by this stateless implementation.

## Supplied Role Grant

`supplied_role_grant` binds:

- record and snapshot identities;
- Contract ID and canonical hash;
- task and Role;
- Grant type;
- declared assignment authority and Shin Gate reference;
- assignee and execution context; and
- `as_of` and explicit revocation state.

The Contract's assignment fields are declarations, not provenance evidence.
The supplied Role Grant is a separate validator input, not an authenticated
grant. Matching values establish only that the two supplied representations
are consistent.

## Supplied Role Acceptance

The Contract's `role_acceptance: ACCEPTED` remains a hashed requirement claim.
Validator-level `ACTIVE` also requires `supplied_role_acceptance`, containing:

```json
{
  "record_identity": "acceptance-record-001",
  "snapshot_identity": "validation-snapshot-001",
  "grant_record_identity": "grant-record-001",
  "contract_id": "contract-auditor-001",
  "contract_hash": "<canonical SHA-256>",
  "task_id": "task-stage4-001",
  "role_id": "AUDITOR",
  "assignee_identity": "auditor-assignee",
  "execution_context_identity": "auditor-context-001",
  "role_acceptance": "ACCEPTED",
  "accepted_at": "2026-07-29T00:03:00Z",
  "as_of": "2026-07-29T12:00:00Z",
  "revocation_state": "NOT_REVOKED",
  "revoked_at": null,
  "revocation_reference": null
}
```

The record must bind the exact Contract ID/hash, task, Role, assignee,
execution context, Grant record, and validation snapshot. `accepted_at` must
be timezone-aware, no earlier than Contract issuance, no later than the
record's `as_of`, and earlier than Contract expiry. These checks validate a
supplied acceptance claim; they do not authenticate the receiver or record
issuer.

For an Auditor, every supplied Builder binding for the same task must be
`ENDED` with a valid `ended_at`. An active Builder or a Builder without a
verifiable end keeps the result on HOLD. Auditor `accepted_at` must be strictly
later than the latest Builder `ended_at`; acceptance at or before that boundary
is rejected.

## Supplied prior-Role binding snapshot

`supplied_prior_role_bindings` is a snapshot envelope, not a bare list. Its
fields are:

```text
snapshot_identity
snapshot_hash
contract_id
contract_hash
task_id
as_of
revocation_state
revoked_at
revocation_reference
completeness_boundary
bindings
```

`completeness_boundary` contains:

```text
scope
task_id
from
through
included_roles
state
expected_record_identities
```

For validator-level `ACTIVE`, the boundary must declare
`scope: ALL_PRIOR_ROLE_BINDINGS_FOR_TASK`, bind the same task, cover the
required time range from `TASK_INCEPTION` through the snapshot `as_of`,
include the required Role set, use
`state: COMPLETE`, and list exactly the record identities present in
`bindings`. A missing boundary, `INCOMPLETE` or `UNKNOWN` state, manifest
mismatch, stale boundary, omitted required Builder history, or unverifiable
Builder end results in HOLD.

Each binding records:

```text
record_identity
snapshot_identity
task_id
role_id
assignee_identity
execution_context_identity
model_identity
bound_at
ended_at
binding_state
as_of
revocation_state
revoked_at
revocation_reference
```

`snapshot_hash` is the canonical SHA-256 of the supplied snapshot with its own
hash field blanked. The validator rejects supplied contents that no longer
match that hash, including changes to the envelope, completeness declaration,
identity manifest, or bindings. It does not authenticate the snapshot producer
or prove that the declared manifest contains every real-world binding.

## Contract identity

The schema is
[`schema/v13_role_contract.schema.json`](../schema/v13_role_contract.schema.json).
It separates Contract identity, assignment, owned responsibility, operations,
Task Artifact Packet, Specialist Lens, independence profile, completion,
lifecycle, and Coverage Gap Recommendation. Its `$defs` also describe the
separately supplied validator records.

`contract_hash` is the lowercase SHA-256 of canonical JSON with these rules:

1. replace `contract_identity.contract_hash` with the empty string;
2. encode JSON as UTF-8 with sorted keys, no insignificant whitespace, and
   non-ASCII characters preserved; and
3. hash the resulting bytes.

`decision_os.role_contract.compute_contract_hash` is the reference
implementation.

## Builder boundary

A Builder Contract can permit only implementation of the specified Design at
the specified paths and head under the specified Completion Line. The
validator rejects Builder requests to self-audit, change a Role Grant or
Specialist Lens, change anything outside the exact target, merge, post, invoke
a specialist, or start Stage 5.

## Auditor boundary

An Auditor Contract can permit only read-only inspection of the fixed head,
artifacts, supplied evidence, Contract conformity, and target immutability.
The validator rejects Auditor requests to change the target, implement a
repair, also act as Builder, merge, post, invoke a specialist, or start
Stage 5.

An Auditor Contract requires `DISTINCT_CONTEXT_REQUIRED`. The validator
compares its execution-context identity with the Builder bindings present in
the supplied current snapshot. The same base model is allowed only when the
Contract says `SAME_MODEL_ALLOWED`. Model diversity never substitutes for a
distinct context.

## Independence dimensions

The four independence fields are separate and non-substitutable:

- `role_context_independence`
- `source_review_independence`
- `runtime_execution_independence`
- `model_diversity`

A different model is not a different context. A different context is not a
separate runtime execution. A supplied runtime execution record is not
independent evidence selection. `REQUIRED_NOT_ESTABLISHED`, missing evidence,
and unknown evidence remain HOLD. `EXECUTION_RECORD_SUPPLIED` means only that
the required record value was supplied and passed validator checks; it does
not establish real-world runtime independence.

The independence record also binds the Contract ID/hash and the prior-Role
snapshot identity/hash. The validator checks those bindings and declared
values. Role independence remains NOT ESTABLISHED outside this validator-level
assessment.

## Specialist Lens

[`templates/v13_specialist_lens.md`](../templates/v13_specialist_lens.md)
defines the required Lens sections. The Contract selects the Lens identity and
hash. The validator rejects a missing or mismatched Lens; it does not assign
the Lens or invoke a specialist.

## Coverage Gap Recommendation

Every Role Exit Receipt includes the coverage result. A no-gap receipt says
exactly `Coverage Gap: NONE DETECTED`. The recommendation records completed
coverage, the gap, recommended specialist, reason, exact target, required
evidence, urgency, and the two fixed controls:

```json
{
  "assignment_authority_required": true,
  "automatic_invocation": false
}
```

The recommendation is inert data. Creating or validating it produces no Role
Assignment event, Runner/Codex/agent invocation, or Stage 5 decision.

## Observable adversarial behavior

When the supplied current snapshot contains a same-context Builder binding for
an Auditor request, the validator returns:

```text
BLOCK — CONTEXT INDEPENDENCE VIOLATION
```

Replacing the request's binding claim does not override a conflicting binding
that remains present in the supplied snapshot. Missing, incomplete, stale, or
internally incoherent snapshot state returns HOLD rather than `ACTIVE`.

The validator also rejects observable revoked records, duplicate identities,
snapshot-hash or identity-manifest mismatches, and Auditor acceptance at or
before Builder completion. It holds on timestamp skew, stale records, unknown
revocation state, an active or unended Builder, and other unverifiable input.

These are validator responses to supplied data, not end-to-end attack
prevention. A caller that fabricates a coherent snapshot, falsely declares it
complete, and recomputes its hash may evade these checks. Likewise, a
stateless validator cannot detect an exact cross-call replay, and independently
loaded records are not an atomic snapshot merely because their `as_of` values
match. Record authentication, authoritative history lookup, atomic transport,
and replay consumption state are not implemented.

No automatic assignment or invocation function exists in this module.
