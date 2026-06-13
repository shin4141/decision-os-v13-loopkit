# Aspire-Fit Adoption Modes

Date: 2026-06-13

## Context

`field_notes/017_second_external_proof_copy_friction.md` recorded the second external normal-repo proof.

That proof succeeded, but it also showed medium `AGENTS.md` copy friction.

The target repository had developed its own local instruction surface during the proof window. During rebase, that created an add/add conflict with the copied V13 `AGENTS.md`.

The correct repair was to preserve the target repo's existing instruction surface instead of overwriting it.

## Observation

Mature users may already have working local instructions.

For those users, asking them to replace their instruction surface first is the wrong entry posture.

Core point:

```text
Do not ask mature users to replace their instruction surface first.
Ask their AI to compare V13 against their Aspire and choose the adoption mode.
```

## Why Mature Users Create Instruction-Surface Conflict

A mature repository is more likely to have:

- local conventions
- project-specific safety rules
- existing agent instructions
- workflow-specific boundaries
- ownership-sensitive operating norms

Those surfaces may already be useful.

V13 should not treat them as obstacles to overwrite.

The better question is whether V13 improves the user's Aspire path without damaging local fit.

## Adoption Modes

When a target repository already has an instruction surface, V13 should support three adoption modes:

1. Keep current instructions

   Use this when local instructions already serve the user's Aspire well, or when V13 would add more ceremony than value.

2. Add V13 as review-only completion lane

   Use this when the repo should keep its local instructions, but V13 can help judge completed work with V12 State, V13 Next Loop Gate, Parked Horizons, and next-loop discipline.

3. Merge V13 into local instructions

   Use this only when the target repo benefits from making V13 behavior part of the local instruction surface and the owner explicitly approves the merge.

## Aspire-Fit Comparison Criteria

The comparison should ask:

- What is the target repo's current Aspire?
- What does the existing instruction surface already protect?
- What failure mode would V13 reduce?
- Would V13 improve completion judgment, restartability, scope control, or next-loop selection?
- Would V13 create double-update cost or local rule conflict?
- Is review-only enough, or does the repo actually need merged instructions?
- Has the owner explicitly approved any instruction-surface change?

## Review-Only Lane as Primary Entry

For mature repositories, review-only should be the primary low-friction entry.

That means V13 can be used to review a completed task or proposed next loop without replacing the repository's canonical local instructions.

This preserves local ownership while still testing whether V13 adds value.

If the review-only lane repeatedly proves useful, later loops can consider whether merge or pluginization would reduce friction.

## Why This Matters for Plugin Readiness

This is Plugin Readiness evidence.

Manual `AGENTS.md` copy worked in the first external proof and partially worked in the second, but the second proof showed that existing instruction surfaces create real adoption friction.

A future plugin may need a review-only lane selected through Aspire-fit comparison.

That does not justify building the plugin now.

It clarifies what a plugin would eventually need to support:

- inspect local instruction surfaces
- compare V13 against the user's Aspire
- recommend keep, review-only, or merge
- avoid overwriting local instructions
- preserve `AGENTS.md` as canonical until an owner decision changes it

## Boundary

This note does not implement pluginization.

This note does not create plugin scaffolding, comparison tooling, MCP, hooks, skills, automation, CLI, server, package setup, schema changes, release files, V1 draft, Auto-Spend Gate implementation, marketing automation, or new features.

This note does not authorize replacing mature users' instruction surfaces.

This note does not claim broad adoption or plugin readiness completion.

External repositories were not modified by this field note.

## V12/V13 Interpretation

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The second external proof showed that V13 can operate around an existing instruction surface, but mature-user adoption should be guided by Aspire-fit comparison instead of replacement-first copying.

Plugin implementation remains parked.

## Result

Signal:
🟢 BLUE / ASPIRE-FIT-ADOPTION-MODES-RECORDED
+
🟢 BLUE / REVIEW-ONLY-LANE-IDENTIFIED
+
🟢 BLUE / MATURE-INSTRUCTION-SURFACE-PRESERVED
+
🟡 YELLOW / DO-NOT-BUILD-PLUGIN-YET

Parked Horizons:
CLAUDE-SKILLS / HOOKS / MCP / PLUGINIZATION / V1

Existing External Gates:
AUTO-SPEND-GATE = automation-spend-gate repo

## Next Loop

Use Aspire-fit comparison before asking a mature repo to adopt V13, and prefer review-only entry before merge or plugin implementation.
