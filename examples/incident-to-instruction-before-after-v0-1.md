# Incident-to-Instruction Before / After v0.1

**Synthetic / invented / non-private**

**Not customer evidence**

**Not measured effectiveness**

**Not proof of incident prevention**

This example shows what the
[Incident-to-Instruction prompt](../copy-paste/incident-to-instruction-rule.md)
can return from one sanitized invented incident. No file was edited and no
rule was applied.

## Before

- The agent reported completion after a command exited successfully.
- The remote state had not changed.
- The next session resumed from stale state.
- The human inspected logs and repeated the decision.

The synthetic repository uses `/AGENTS.md` for repository-wide agent rules. It
contains an existing `## Repository Authority` section followed later by
`## Task Execution`.

## After — one returned draft rule

### 1. Incident As-of

Synthetic scenario as of 2026-07-26.

### 2. First Operational Gap

Completion was reported from command exit without inspecting the canonical
artifact, remote state, or accepted state and without retaining verification
evidence for the next session.

### 3. Target Surface

`AGENTS.md`

### 4. Target Path or Placement

Repository-root `/AGENTS.md`, immediately after `## Repository Authority` and
before `## Task Execution`.

### 5. Intended Scope

AI agents performing Git-backed repository changes whose accepted completion
depends on local, remote, or reviewed state. The rule does not grant authority
for unrelated workflows, publication, merge, release, or overwrite.

### 6. Exact Paste-Ready Insertion Block

~~~~markdown
## Canonical Completion and Restart Rule

- Apply this rule only to Git-backed repository changes whose accepted result
  depends on local, remote, or reviewed state.
- Do not report completion solely because a command exited successfully.
- Before reporting completion, inspect the canonical artifact or accepted
  state that the task was meant to change.
- Record the verification evidence used for closure: the exact artifact,
  reference or state, relevant check, observed result, and as-of point.
- Compare local, remote, and accepted state whenever they participate in the
  workflow. If they disagree, or a required identity is unresolved, set
  `HOLD` and stop before closure.
- Do not silently retry, guess which copy is canonical, or overwrite an
  artifact or state without explicit authority.
- Preserve unresolved items as `UNKNOWN`.
- Next actor: the repository operator. Next safe action: inspect and reconcile
  the canonical local, remote, and accepted state before another completion
  decision.
- Do not mark handoff complete until the next human or AI can identify the
  exact restart point, current gate, verification evidence, unresolved items,
  next actor, next safe action, and rollback path.
~~~~

### 7. Required Completion Evidence

- The canonical target path and intended scope are recorded.
- The insertion block appears once between the two named headings without
  replacing unrelated instructions.
- The canonical post-write artifact is inspected with its exact reference or
  digest and accepted as-of point.
- The relevant instruction-surface check and its observed result are recorded.
- Local, remote, and accepted states agree when all three apply.

### 8. HOLD Conditions

- The canonical artifact, target path, placement anchor, or intended scope is
  unresolved.
- Local, remote, and accepted states disagree or cannot be compared with the
  available evidence.
- Required verification evidence or the exact restart point is missing.

### 9. BLOCK Conditions

- The actor lacks authority to edit the instruction surface.
- Applying the rule would expose private material, weaken a higher-priority
  instruction, or overwrite unrelated content.
- The requested action requires guessed canonical state, evidence suppression,
  or an unauthorized merge, release, publication, or overwrite.

### 10. Handoff Requirements

Record the target path, placement, intended scope, selected fix, canonical
post-write state, verification evidence, current gate, all unresolved or
`UNKNOWN` items, exact restart point, next actor, next safe action, and
rollback path.

### 11. Rollback

Remove only the exact `Canonical Completion and Restart Rule` block, restore
the recorded prior `/AGENTS.md` state when necessary, preserve unrelated later
changes, and repeat the canonical-state and instruction-surface verification.

### 12. Re-evaluation Trigger

Review the wording after another false-completion or stale-resume incident, a
change to the canonical path or instruction precedence, a state disagreement
not handled by the rule, or evidence that the rule conflicts with the actual
workflow.

### 13. Still UNKNOWN

- Whether the synthetic target layout matches any real repository.
- Whether an authorized operator would accept or apply the rule.
- Whether an AI agent would follow it.
- Whether it would reduce recovery work or prevent any future incident.
- The underlying cause of the stale remote state.

### After checklist

- One exact `AGENTS.md` block.
- Canonical-state inspection.
- Verification evidence.
- `HOLD` on local/remote/accepted-state disagreement.
- `UNKNOWN` preservation.
- Next actor and restart point.
- Rollback and re-evaluation trigger.

## Free draft and paid Audit boundary

This After is a structured draft, not an applied improvement, customer
diagnosis, verified implementation, or measured result. The paid AI
Application Workflow Audit separately reviews whether the selected gap,
surface, scope, placement, evidence, conflicts, rollback, and handoff are
appropriate for one accepted workflow.
