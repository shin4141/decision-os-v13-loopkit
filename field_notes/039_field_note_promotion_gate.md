# Field Note 039: Field Note Promotion Gate

Date: 2026-06-14

## Purpose

This note defines when a field note may be promoted into canonical AGENTS.md routing.

The purpose is to prevent every useful field note from becoming immediate canonical instruction.

## Problem

Field notes can capture useful observations.

But not every useful observation should become canonical AGENTS.md routing.

If every new insight is immediately routed into AGENTS.md, the system becomes:

- heavy
- confusing
- brittle
- hard to copy
- hard for future agents to apply

Canonical routing should be reserved for stable judgment anchors.

Field notes should remain the proving ground.

## Candidate Fixed Point

A candidate fixed point is a useful observation or rule that may help future judgment but has not yet been reused enough to become canonical.

It may be important.

It may be true.

But it is still under observation.

Candidate fixed points should be preserved without forcing every future agent to check them by default.

## Confirmed Fixed Point

A confirmed fixed point is a candidate that has changed at least one later judgment or prevented at least one later mistake.

Confirmation requires use.

The question is not:

```text
Does this note sound right?
```

The question is:

```text
Did this note change a later V13 decision?
```

## Canonical Judgment Anchor

A canonical judgment anchor is a confirmed fixed point that is stable, reusable, low-friction, and important enough that future agents should check it before making a gate decision.

Canonical anchors belong near the operational path.

They should be brief enough to use and clear enough to trigger.

If a rule needs a long story to apply, it may not be ready for canonical routing.

## Promotion Conditions

A field note may be promoted toward AGENTS.md routing only when:

1. It has been used in at least one later real task or real judgment.
2. It changed the outcome, not merely the wording.
3. It prevented a mistake, scope creep, false readiness claim, or debt transfer.
4. Its rule can be stated briefly.
5. Its trigger condition is clear.
6. Its failure mode is clear.
7. It does not duplicate an existing anchor.
8. It does not make the default AGENTS path too heavy.
9. It can be checked without reading the full conversation.
10. It preserves delta rather than sending debt forward.

Promotion should be earned by demonstrated judgment value.

## Non-Promotion Conditions

Do not promote when:

- the note is only a concept
- the note is only a reaction to excitement
- the note has not changed a later judgment
- the note requires too much context
- the note duplicates another rule
- the note is useful only for one situation
- the note would make AGENTS.md harder to use
- the note is being promoted to make the project look more complete

Not promoting a note is not a failure.

It may be the correct CAP.

## Required Evidence Types

Acceptable evidence for promotion includes:

- real external contrast
- later task where the rule changed GO/CAP/HOLD/BLOCK
- later task where the rule prevented premature outreach/plugin/star/readiness claim
- later Mistaken MD where the rule placed the missed structure earlier
- repeated use across two different task types

Evidence should show that the rule changed behavior.

It should not merely show that the rule was mentioned.

## Demotion / Delay Conditions

If a promoted rule becomes too heavy, confusing, duplicated, or unused, it should be delayed, moved back to docs, or kept as a field note rather than canonical AGENTS routing.

Canonical status is not permanent.

If a rule stops helping judgment, it should leave the default path.

The goal is not maximum canon.

The goal is useful judgment with low enough friction to survive real use.

## Application to Current Notes

Current recent notes:

### 029 Fixpoint Learning

Status:
candidate fixed point

Evidence:
used by 030

Decision:
not yet canonical

### 030 Mistaken Public Readiness

Status:
confirmed fixed point

Evidence:
used by 031, 032, and 034

Decision:
not yet canonical; needs concise trigger

### 031 Breakout Map

Status:
candidate / partially confirmed

Evidence:
useful for observation

Decision:
not canonical yet

### 032 Premature Claim Gate

Status:
confirmed for public-readiness prevention

Evidence:
used detection conditions to cap/block tempting claims

Decision:
not canonical yet; may become a public-readiness guard later

### 033 Decimal Depth Rule

Status:
candidate, then partially confirmed by 034

Evidence:
changed interpretation of the public-readiness map

Decision:
not canonical yet; needs future Mistaken MD use

### 034 Decimal Depth Application

Status:
confirmation evidence for 033

Evidence:
applied causal placement without renumbering history

Decision:
not canonical itself

### 035 Loop Gallery vs Decision-OS

Status:
positioning fixed point

Evidence:
confirmed by 036, 037, and 038

Decision:
not canonical yet

### 036 README Polish Audit

Status:
concrete evidence

Evidence:
showed Evidence / scope CAP for open-ended polish loop

Decision:
not canonical itself

### 037 Test Until Green Audit

Status:
concrete evidence

Evidence:
showed conditional GO for bounded verification loop

Decision:
not canonical itself

### 038 Execution Loop Gate Criteria

Status:
candidate fixed point

Evidence:
extracted criteria from 036 and 037

Decision:
not canonical yet; needs later use across a real task before AGENTS routing

## Boundary

This is a promotion-gate note only.

Do not promote anything yet.

Do not modify AGENTS.md.

Do not rewrite README.

Do not claim public readiness.

Do not broaden into outreach.

Do not add implementation.

Do not route field notes 029–038 into AGENTS.md yet.

This note does not modify AGENTS.md, AGENTS.ja.md, README.md, previous field notes, docs, schemas, examples, prompts, CI, automation, or plugin files.

This note does not add features, hooks, skills, MCP, pluginization, automation, outreach, posting, loop galleries, or product behavior.

## V13 Signal

Signal:
🟢 BLUE / PROMOTION-GATE-DEFINED
+
🟢 BLUE / FIELD-NOTE-VS-CANONICAL-ANCHOR-SEPARATED
+
🟢 BLUE / PREMATURE-CANONICALIZATION-CAPPED
+
🟢 BLUE / RECENT-NOTES-STATUS-CLASSIFIED
+
🟡 YELLOW / DO-NOT-ROUTE-INTO-AGENTS-YET
+
🟡 YELLOW / PUBLIC-READINESS-STILL-NOT-PROVEN
+
🟡 YELLOW / CANONICAL-BLOAT-RISK-CAPPED

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The promotion gate is defined, but no field note is promoted yet. Canonical routing remains capped until a note satisfies the promotion conditions.

Next Loop Command:
Use this promotion gate before any future AGENTS.md routing, README rewrite, pluginization, or public-readiness claim.
