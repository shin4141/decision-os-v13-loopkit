# AI Application Workflow Audit — Instruction-Surface Remediation Sample 001

This full Audit delivery is synthetic, invented, and non-private. It uses the
same incident identity as the shipped
[workflow incident intake](workflow_incident_intake_v0_1.json) to demonstrate
the
[Instruction-Surface Remediation Profile v0.1](../services/instruction_surface_remediation_profile_v0_1.md).
It is not customer evidence, a testimonial, a measured outcome, a paid-client
result, or proof that an instruction prevents incidents.

## Scope

Audit Profile: AI_APPLICATION_WORKFLOW
Application or Workflow: Customer-support approval workflow
Bounded Workflow Path: draft response -> human approval -> send decision
Audit As-of: 2026-07-26

## Source Materials

Reviewed: Synthetic approval event sequence, sanitized handoff summary, and the invented project instruction layout described in this sample
Not Reviewed: Live application logs, vendor internals, production data, or an actual customer instruction file
Material Restrictions: No credentials, customer messages, production secrets, private code, or customer-identifying material

## Incident As-of State

Trigger: The workflow resumed after an interrupted approval step.
Expected State: The approved draft remained current and ready for the send decision.
Observed State: The resumed workflow could not establish which draft the approval covered.
Current Restart or Fallback Path: Keep the workflow stopped at approval until the draft identity is re-established.
Current Owner: Human publication operator
Next Safe Action: Submit one paste-ready completion-integrity and handoff rule for bounded human review before any write to the synthetic repository-root instruction surface

## Friction Map

| Point | Expected Carrier | Observed Gap | Returned Human Work |
| --- | --- | --- | --- |
| Approval-to-send handoff | Canonical draft identity, accepted state, and verification receipt | Command completion and resumed local state did not establish the accepted draft | The operator revalidated the draft and repeated the send decision |

## Restartability Diagnosis

Trigger Clarity: PASS — The interrupted approval and attempted resume are identified.
Accepted-State Clarity: PARTIAL — The intended approved state is named, but the accepted draft identity is not durably bound.
Evidence Continuity: FAIL — No retained verification connects command completion, canonical draft state, and the send decision.
Completion Integrity: FAIL — A completed command or resumed process can be reported without confirming the accepted state.
Restartability: PARTIAL — A stop-and-revalidate fallback exists, but its required evidence and handoff record are not explicit.
Ownership / Next Actor: PASS — The publication operator owns revalidation before another send decision.
Human Recovery Burden: PARTIAL — Revalidation and a repeated decision are known, but the workflow does not retain a restartable receipt.
Safe Next Action: PASS — The workflow remains stopped until identity and evidence are re-established.
Overall Diagnosis: The bounded workflow lacks an instruction-level completion and handoff rule that distinguishes command exit, canonical state, accepted state, and restartable evidence.

## Priority Fix

Selected Fix: Add one paste-ready completion-integrity and restartable-handoff rule block to the synthetic repository-root `/AGENTS.md`.
Why Priority: The block makes the existing stop, evidence, ownership, and restart obligations explicit without changing application code or claiming to repair the vendor workflow.

## Operational Asset

Asset Type: Instruction-Surface Remediation Profile v0.1 — paste-ready AGENTS.md rule block
Asset Content: Apply the complete profile below only after bounded human review and authority to edit the synthetic target surface.

Target Surface: AGENTS.md

Target Path: /AGENTS.md

Intended Scope: Repository-wide AI agents performing the bounded approval-to-send workflow; it does not govern unrelated repositories, vendor systems, or production authorization.

Observed Incident: The resumed approval workflow could not establish which draft the approval covered, so the human revalidated the draft and repeated the send decision.

Selected Fix: Require canonical-state inspection, retained verification evidence, explicit stop conditions, and a restartable handoff before any completion report.

Exact Insertion Block:

~~~~markdown
## Completion Integrity and Restartable Handoff

- Apply these rules only to AI agents executing the repository's
  approval-to-send workflow. They do not govern unrelated workflows or grant
  production authorization.
- Do not report completion solely because a command exited successfully.
- Before reporting completion, identify and inspect the canonical artifact or
  accepted state that the task was meant to change.
- Record the verification evidence used for closure, including the exact
  artifact, reference or state, relevant check, observed result, and as-of
  point.
- Compare local, remote, and accepted state whenever all three participate in
  the workflow. If they disagree, or any required identity is unresolved, set
  the task to `HOLD` and stop before closure.
- Do not silently retry, guess which copy is canonical, or overwrite an
  artifact or state without explicit authority.
- Preserve every unresolved item as `UNKNOWN`. Name the next actor and the next
  safe action.
- Treat a handoff as incomplete until the next human or AI can identify the
  exact restart point, current gate, verification evidence, unresolved items,
  next actor, next safe action, and rollback path.
~~~~

Required Completion Evidence:

- Record `/AGENTS.md` as the canonical target and the repository-wide intended scope.
- Confirm the exact insertion block appears once at the stated placement without replacing unrelated instructions.
- Inspect the canonical post-write artifact and record its exact reference or digest and the accepted as-of point.
- Record the relevant syntax or instruction-surface review and its observed result.
- Confirm local, remote, and accepted states agree when all three exist; otherwise retain `HOLD`.

HOLD Conditions:

- The canonical instruction path, insertion anchor, intended scope, or accepted state is unresolved.
- Local, remote, and accepted states disagree or cannot be compared with the available evidence.
- The completion evidence or restart record is missing or incomplete.
- Instruction precedence or an overlapping rule requires bounded clarification.

BLOCK Conditions:

- The implementer lacks authority to edit the target surface.
- Application would expose prohibited material, weaken a higher-priority instruction, or require an unauthorized public action.
- Applying the block would overwrite unrelated instructions or require guessing which artifact is canonical.
- A requester asks for silent retry, evidence suppression, or bypass of a required stop condition.

Handoff Requirements:

- Preserve the exact target and path, intended scope, selected fix, placement anchor, canonical post-write state, verification evidence, all unresolved or `UNKNOWN` items, current gate, next actor, next safe action, and rollback path.
- Do not mark the handoff complete until the next human or AI can locate the exact restart point without reconstructing it from chat history.

Placement Note: Insert the block in the repository-root `/AGENTS.md` immediately after the existing `## Approval Workflow Authority` section and before the existing `## Task-Specific Procedures` section. Preserve both anchor sections, all unrelated text, and any higher-priority rule.

Rollback: Remove only the exact `Completion Integrity and Restartable Handoff` block, restore the recorded prior `/AGENTS.md` state if necessary, preserve unrelated later changes, and repeat the same canonical-state and syntax verification.

Re-evaluation Trigger: Review the wording after a repeated false-completion or handoff incident, a change in canonical path or instruction precedence, a local/remote/accepted-state mismatch not handled by the block, or evidence that the rule conflicts with the actual workflow.

## Before / After Restart Check

Before: The resumed workflow can treat command completion or available local state as closure without binding the accepted draft, retained evidence, next actor, or restart point.
After: The delivered instruction block explicitly requires canonical-state inspection, evidence recording, `HOLD` on disagreement, bounded refusal conditions, and a restartable handoff before completion may be reported.
Still UNKNOWN: Whether the block will be applied, followed, accepted by a customer, or reduce future incidents or human recovery work.

## Unknowns

- Actual customer instruction precedence, adoption, agent compliance, and operational effect remain unknown because this sample is synthetic.
- Whether the underlying vendor session can be recovered or the approval state reconstructed natively remains unknown.

## Exclusions

- Customer-file modification, vendor repair, application-code changes, production recovery, security review, publication, and effectiveness measurement are outside this sample.
- The sample does not authorize an implementation agent to edit, merge, release, or overwrite any target surface.

## Claim Boundary

Vendor Bug Fix: NOT CLAIMED
Future Prevention: NOT CLAIMED
Lost-State Recovery: NOT CLAIMED
Security or Safety: NOT CLAIMED
Productivity / Labor / Cost / Revenue: NOT CLAIMED
Unreviewed Systems: NOT DIAGNOSED
Native Resume: NOT PROOF OF TRUSTWORTHY RESTART

## Completion Line

This synthetic delivery identifies the target instruction surface, exact path
and placement, one paste-ready rule block, completion evidence, `HOLD` and
`BLOCK` conditions, restartable handoff, rollback, and re-evaluation while
preserving the existing Audit's claim boundary.
