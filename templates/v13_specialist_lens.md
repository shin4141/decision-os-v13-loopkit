# V13 Stage 4 Specialist Lens v0.1

## Lens Identity

```text
Lens ID:
Lens Version: 0.1
Lens SHA-256:
Assigned Role: BUILDER / AUDITOR
Role Contract ID:
Shin Gate Reference:
```

The Role Grant must explicitly select this Lens identity and exact hash.
An assignee cannot select, replace, or amend its own Lens. A missing or
mismatched identity or hash keeps the Role inactive.

## Purpose

State the narrow specialist judgment this Lens contributes to the assigned
Builder or Auditor responsibility. The Lens supplies a bounded review
perspective; it grants no authority and creates no additional Role.

## Primary Risks

- Identify risks inside the Role Contract's exact target.
- Keep Builder implementation risk separate from Auditor conformity risk.
- Treat unknown, stale, or unfixed evidence as a HOLD condition.
- Do not expand to Scout, Architect, Stage 5, or an ungranted specialist.

## Required Evidence

- Exact Role Contract identity and canonical hash.
- Exact Task Artifact Packet repository, head, paths, hashes, and as-of time.
- Exact Lens identity, version, and SHA-256.
- Assignee and execution context identities.
- A separately supplied Role Grant record and receiver Role Acceptance record
  bound to the Contract ID/hash, task, Role, assignee, execution context,
  shared snapshot, as-of time, and explicit revocation state.
- A supplied independence record bound to the declared prior-Role binding
  snapshot identity and hash.
- A supplied prior-Role binding snapshot with its identity, canonical hash,
  as-of time, completeness boundary, expected record-identity manifest,
  binding lifecycle times, and explicit revocation states.
- Before/after target identity when immutability is required.

Supplied records are validator inputs. Their names and internally consistent
fields do not authenticate an issuer, receiver, execution context, transport,
record store, provenance, completeness assertion, or revocation truth.

## Common Failure Patterns

- Treating a Role name or self-description as a Role Grant.
- Treating different artifact bytes as independent authorship or review.
- Omitting `producer_role` or `builder_generated` metadata to conceal a
  same-context Builder/Auditor collision.
- Omitting a true same-context binding and substituting a claimant-controlled
  different-context binding.
- Treating Contract-local `role_acceptance: ACCEPTED` as receiver proof.
- Reusing a stale or different-snapshot record.
- Mixing record as-of times across one validation snapshot.
- Accepting an Auditor before every supplied Builder binding has ended.
- Treating a different model as a different execution context.
- Treating a recommendation as an assignment or invocation.

## Escalation Conditions

Return HOLD or BLOCK when authority, Gate, identity, target, Lens, lifecycle,
snapshot freshness, completeness boundary, record manifest, revocation state,
Builder end time, or independence claim is missing, unknown, expired, stale,
revoked, inconsistent, or unverifiable. Any new Role, authority, target,
operation, or Lens requires a new Shin Gate.

## Output Contract

Produce only the contracted Role output and a Role Exit Receipt. The receipt
must state either a concrete Coverage Gap Recommendation or:

```text
Coverage Gap:
NONE DETECTED
```

Every recommendation remains inert:

```text
Recommendation: ALLOWED
Automatic Assignment: PROHIBITED
Automatic Invocation: PROHIBITED
```

Every Role Exit Receipt must also preserve this implementation boundary
exactly:

```text
Role Separation Enforcement: VALIDATOR-LEVEL ONLY
Record Issuer / Authentication / Transport: NOT IMPLEMENTED
Role Independence: NOT ESTABLISHED
End-to-End False-Division Prevention: NOT ESTABLISHED
```

An internally consistent supplied snapshot may satisfy validator conditions,
but it does not establish record authenticity, real-world completeness, Role
independence, or end-to-end false-division prevention. No automatic Role
assignment, specialist invocation, or Stage 5 decision follows.
