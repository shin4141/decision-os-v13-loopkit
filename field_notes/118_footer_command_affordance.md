# Field Note 118 - Footer Command Affordance

## Layer

V13 / Command Affordance / Handoff Visibility

Adjacent layers:
- V12 Completion Integrity / making restart actions visible
- V13 Loop Gate / choosing whether continuation should run, hold, cap, or block
- V14 Resource Justice / converting small repeated token cost into useful recovery actions

## Status

```text
Prior adopted / verification pending
```

This note records an adopted prior.

It is not verified Canon.

It must pass the Concept Promotion Gate before it can be required by `AGENTS.md`, README, templates, schemas, or Core Rules.

## Observation

A tiny command hint at the end of responses may raise expected value by reminding users of available recovery actions.

Candidate actions:

```text
Handoff
Snapshot
LoopMenu
Tutorial
```

Minimal candidate hint:

```text
Commands: Handoff / Snapshot / LoopMenu / Tutorial
```

The hypothesis is that a few repeated tokens can become "winning tokens" when they help a user avoid drift, recover state, ask for a snapshot, or create a restartable handoff instead of continuing from fragile context.

## Preferred Prior

Do not show the hint on every response by default.

Preferred prior:

```text
Show a tiny command hint only when context risk, session length, or handoff sensitivity rises.
```

Examples:

```text
Context Risk: YELLOW or RED
long-running task
handoff-sensitive repo work
fork-user onboarding
user appears unsure what recovery actions exist
```

## Why Not Always-On Yet

Repeated always-on hints may:

```text
become visible noise
increase copy burden
look like implemented UI commands
make users think automation exists when only Markdown command specs exist
```

This creates a risk of false affordance.

The hint should not imply that a UI menu, automation layer, or runtime command router has been implemented.

## Verification Questions

Before promotion, test:

```text
Does the hint reduce lost-context or handoff requests?
Does it increase useful Snapshot/Handoff usage?
Does it create user-visible noise?
Do fork users understand it as available workflow, not implemented UI?
```

## Promotion Boundary

This prior must pass the Concept Promotion Gate before canonical promotion.

Promotion requires:

```text
what is being promoted
why it is no longer only a hypothesis
verification or evidence used
falsifier or countercondition
rollback / downgrade condition
owner approval if public surface, outreach, authority, or irreversible action is affected
```

## Current Gate

```text
Field Note documentation: GO
AGENTS.md rule promotion: HOLD
Implementation: HOLD
Automation: HOLD
Public posting/outreach/release: HOLD
```

## Do Not Use This Note To Claim

Do not use this note to claim:

```text
footer command hints are verified
all responses should show a command menu
UI commands are implemented
automation exists
fork users will understand the hint without testing
AGENTS.md should require this immediately
```

## Completion Line

Footer Command Affordance is recorded as an adopted prior with verification pending.

It may guide future experiments or small surface tests, but it must not become Canon until the Concept Promotion Gate is passed.
