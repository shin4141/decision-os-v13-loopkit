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
- Assignee and trusted execution context identities.
- Independence evidence required by each independent profile field.
- Before/after target identity when immutability is required.

## Common Failure Patterns

- Treating a Role name or self-description as a Role Grant.
- Treating different artifact bytes as independent authorship or review.
- Omitting `producer_role` or `builder_generated` metadata to conceal a
  same-context Builder/Auditor collision.
- Treating a different model as a different trusted execution context.
- Treating a recommendation as an assignment or invocation.

## Escalation Conditions

Return HOLD or BLOCK when authority, Gate, identity, target, Lens, lifecycle,
or independence is missing, unknown, expired, revoked, inconsistent, or
unverifiable. Any new Role, authority, target, operation, or Lens requires a
new Shin Gate.

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
