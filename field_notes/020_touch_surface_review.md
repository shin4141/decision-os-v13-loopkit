# Field Note 020: Touch Surface Review

Date: 2026-06-13

## Observation

V13 is not only a post-completion review layer.

It can also be used before touching someone else's repo, an existing product, or an inherited codebase.

The pre-edit use is different from ordinary task review:

```text
Before editing, classify what surfaces are safe to touch.
```

This is especially important when the user is asking an AI agent to work inside a repository that already has structure, history, deployment paths, process rules, or owner-visible behavior.

## Why This Matters

AI coding is not dangerous because the model cannot write code.

It is dangerous because it can confidently touch the wrong surface.

A repo may contain areas that look ordinary but are actually load-bearing:

- deployment gates
- approval policies
- public-facing behavior
- schemas
- env or DB paths
- generated artifacts
- release records
- inherited architecture
- owner-specific workflow constraints

The danger is not only bad code.

The danger is confident modification of a surface the agent did not understand.

## Before-Edit Gate

V13 can act as a before-edit gate.

The gate asks:

- What surfaces does the proposed task need to touch?
- Which surfaces are safe for the current loop?
- Which surfaces require owner approval?
- Which surfaces are too risky or too poorly understood to touch yet?
- What is the smallest safe first action?

This does not replace tests, code review, security review, deployment review, or human judgment.

It gives the agent a bounded way to stop before editing the wrong layer.

## Touch Surface Classes

V13 can classify touch surfaces before implementation:

1. Safe-to-touch surface

   A bounded surface that matches the task, has low blast radius, and does not affect approval-sensitive behavior.

2. Dangerous / code-bomb surface

   A surface that may be load-bearing, owner-visible, security-sensitive, deployment-sensitive, data-sensitive, or tied to hidden assumptions.

3. Do-not-touch-yet surface

   A surface that should remain unchanged until the owner provides a clearer mission, a Decision Packet, a local gate, or stronger evidence.

The useful output is not "edit or do not edit everything."

The useful output is:

```text
Touch this small surface.
Do not touch these surfaces yet.
Stop if the task requires them.
```

## Mature Repo Implication

Touch Surface Review is especially relevant when:

- a high-capability model created the original structure
- a lower-capability or cheaper model is asked to modify it
- the repo has existing process docs
- the repo has approval policies
- the repo has deployment gates
- the repo has schemas
- the repo has env, DB, or public surfaces
- the user is forking or modifying someone else's project

In these cases, V13 should not start by replacing the repo's instruction surface.

It can first operate as a review-only before-edit lane.

That supports mature repos where the safest adoption mode is not "merge V13 into local instructions," but:

```text
Use V13 to classify the touch surface before edits.
```

## User-Facing Framing

The strongest user-facing frame is not:

```text
AI review
```

The stronger frame is:

```text
Insurance before AI edits an existing repo.
```

This matters because ordinary users may not want to learn V13 terminology first.

They may understand the risk immediately if it is framed as:

```text
Before the AI edits this repo, ask it what surfaces it must not touch.
```

## Boundary

This field note does not activate a new feature.

It does not add a Touch Surface Review command, prompt, plugin, hook, skill, MCP integration, automation, CLI, server, schema, package setup, release file, V1 draft, or product behavior.

It does not modify README.md, AGENTS.md, docs/ai_reading_order.md, or plugin docs.

It does not authorize broad repo scans, external edits, deployment work, or changes to mature repositories.

This should remain CAP / field-note only for now.

## V13 Signal

Signal:
🟢 BLUE / TOUCH-SURFACE-REVIEW-IDENTIFIED
+
🟢 BLUE / BEFORE-EDIT-GATE-FRAMING-FOUND
+
🟡 YELLOW / DO-NOT-TURN-INTO-FEATURE-YET
+
🟡 YELLOW / README-NOT-YET

Parked Horizons:
CLAUDE-SKILLS / HOOKS / MCP / PLUGINIZATION / V1

Existing External Gates:
AUTO-SPEND-GATE = automation-spend-gate repo

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The touch-surface insight is recorded as a field-note-only framing. It can guide future review-only adoption and before-edit gates, but it does not yet authorize a new README promise, feature, prompt, plugin, hook, MCP integration, or automation surface.

Next Loop Command:
Use Touch Surface Review as a lens in the next external read-only evaluation before turning it into README or product surface.
