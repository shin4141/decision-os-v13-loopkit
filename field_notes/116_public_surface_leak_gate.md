# Field Note 116 — Public Surface Leak Gate

## Status

Canon-promoted

Promoted location:

`templates/v13_build_capsule_minimum_contract.md`

`## Public Surface Rule`

Promotion evidence:

- The rule changed a later real remediation task.
- Confirmed operator-specific paths and private operational references were removed.
- Rendered GitHub surface verification found no remaining leak or redaction-induced breakage.

Concise trigger:

Before public-surface PASS, inspect source and rendered surfaces for private-context leakage.

Rollback / demotion condition:

If the rule creates repeated false positives, is applied to non-public work by default, duplicates another canonical rule without independent value, or adds excessive capsule friction, demote it to on-demand documentation.

## Layer

V13 / Public Release Gate / Public Surface Integrity

Adjacent layers:
- V9 As-of / Release integrity
- V12 Completion Integrity
- V13 Loop Gate / GO-HOLD-CAP-BLOCK
- V14 Resource Justice

## Background

Pain Timing Map cleanup revealed a public-surface leak failure mode.

The issue was not that the internal example structure was weak.

The structure of the internal dogfood/example record was useful.

The failure was that private operator context could be exposed through public-facing examples, README surfaces, issue examples, field notes, offer packets, or repository documents.

This means the problem is not only a writing issue.

It is a V13 public release gate issue.

## Core Lesson

```text
A good internal dogfood example is not automatically a safe public example.
```

Japanese:

```text
内部dogfoodとして良い記録でも、そのまま公開例にしてよいとは限らない。
```

## Observed Failure Mode

Public-facing repository surfaces can accidentally expose:

```text
personal names
private operator context
financial runway
health / fatigue / collapse wording
Named-owner / owner-approved / owner-only style references
private recovery capacity
sensitive motivation or survival framing
private handoff notes exposed as public examples
```

If these appear in a public-facing repo, even inside a structurally good example, the public release state should be BLOCK.

## Why V12 Alone Is Not Enough

V12 helps close work correctly.

It asks whether completion, handoff, and restartability are valid.

However, V12 alone does not guarantee that a public surface is safe to publish.

A file can be complete, internally useful, and restartable, while still unsafe as a public example.

V13 must therefore gate public release separately.

## V13 Rule Candidate

Before any repository, README, issue template, example, field note, offer packet, or public-facing document is published or made public, run a leak audit.

Required audit:

```text
Personal Name / Private Context Leak Audit
```

The audit must check for:

```text
personal names
private operator context
financial runway
health / fatigue / collapse wording
internal owner references
private recovery capacity
sensitive motivation or survival framing
private handoff notes accidentally exposed as public examples
```

Default action:

```text
Public release = BLOCK until the audit is clean.
```

## Allowed Replacements

```text
Named person → Decision Owner / operator / maintainer
Named-owner request → Ask the Decision Owner
Named-owner-approved → Decision Owner-approved
Named-owner-only → operator-only / single-user
Named owner's time / recovery capacity → operator capacity
survival / runway crisis → resource-constrained prioritization
```

## Public Surface Leak Gate

Minimum gate:

```text
Before public release, inspect the rendered and source-visible surface for personal-name and private-context leaks.
```

If the surface includes public examples, also inspect whether internal dogfood examples were generalized.

A public example must not require the reader to know the operator’s private life, financial condition, health state, fatigue state, survival pressure, or recovery capacity.

## What This Prevents

This gate prevents:

```text
publishing useful internal notes as unsafe public examples
exposing Decision Owner-specific private context
turning repo examples into personal diary fragments
making external users interpret the work through the author’s private constraints
leaking sensitive motivation or survival framing
requiring later public cleanup after release
```

## Relation to Previous V13 Incidents

This connects to earlier V13 public-surface incidents:

```text
Field Note 114 — Screenshot-dependent Gate Signal Miss
```

Both show that public-facing surfaces require separate V13 checks.

A repo can be internally coherent but externally unsafe or misleading.

## Gate Interpretation

```text
Internal dogfood example: may be useful
Public example: requires leak audit
Public release: BLOCK until clean
Generalized public example: GO only after audit
```

## Do Not Use This Note To Claim

Do not use this note to claim:

```text
internal examples are bad
dogfooding should stop
all private context is forbidden in private notes
Pain Timing Map structure was invalid
V12 is unnecessary
public release is permanently blocked
```

The lesson is narrower:

```text
Internal usefulness does not imply public safety.
```

## Future Rule Candidate

Possible future rule:

```text
Public Surface Leak Gate:
Before public release, run Personal Name / Private Context Leak Audit across README, examples, issue templates, offer packets, field notes, and rendered first-screen surfaces. Public release remains BLOCK until clean.
```

This may later be promoted into:

* a public release checklist
* a V13 template rule
* a MISTAKEN.md entry if repeated
* a repo-specific public surface audit requirement

For now, keep it as a Field Note.

## Completion Line

This Field Note records Public Surface Leak Gate as a V13 public-release failure mode.

The core rule is:

```text
A good internal dogfood example is not automatically a safe public example.
```

Before any public release, repository or document surfaces must be checked for personal names, private operator context, financial runway, health/fatigue/collapse wording, internal owner references, private recovery capacity, sensitive motivation/survival framing, and private handoff notes used as public examples.

Current status:

```text
Field Note: PASS
Public release rule: CANON-PROMOTED
Public reopen: HOLD
Minimum Contract promotion: COMPLETE
Pain repo cleanup: completed outside this note
```
