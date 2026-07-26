# AI Application Workflow Audit — Delivery v0.1

This is a delivery surface for the existing
[AI Agent Handoff Audit](ai_agent_handoff_audit_offer.md). It extends that
bounded offer to one accepted AI application or operational workflow; it does
not create a separate product family.

## What this covers

An accepted case may involve:

- an AI SaaS workflow;
- a multi-agent application;
- an AI content or production pipeline;
- a RAG or knowledge-assistant workflow;
- an AI customer-support workflow;
- a no-code or automation chain containing AI;
- one clearly bounded internal AI-assisted process.

This is not a general product audit, code review, security audit, model
evaluation, or vendor bug-fix service.

## Accepted incident boundary

The review accepts one concrete operational failure inside one clearly bounded
workflow path. Examples include:

- false or stale completion;
- a lost handoff or agent result;
- a failed restart or resume path;
- state disagreement between components;
- manual rollback, cleanup, revalidation, or context reconstruction;
- output that exists but leaves the next human unable to continue safely.

The incident must be specific enough to distinguish its trigger, expected
state, observed state, returned human work, and current restart or fallback
path.

## Prepare one incident packet

The local
[Workflow Incident Intake Checker](../docs/workflow_incident_intake_checker_v0_1.md)
can confirm whether a sanitized incident packet contains the minimum structure
for a free fit discussion. It does not diagnose the incident, and using it is
optional. A repository is not required. `FIT_CHECK_READY` does not imply
acceptance for a paid Audit.

## Minimum intake

Collect only:

- the application or workflow name;
- one bounded workflow path;
- the triggering incident;
- the expected state;
- the observed state;
- the human recovery work;
- the current restart or fallback path;
- the materials available for review;
- prohibited or confidential materials.

A repository is not required. Usable review materials may include public
screenshots, logs with secrets removed, workflow diagrams, high-level state
descriptions, runbooks, prompts, or selected configuration.

Do not provide credentials, secrets, customer data, private production data, or
materials that the requester is not authorized to share.

## Audit outputs

The paid delivery preserves the existing commercial structure:

1. **Friction Map** — show where the accepted incident returned work or
   uncertainty to the human.
2. **Restartability Diagnosis** — identify what the next human, agent, or
   operator cannot safely reconstruct.
3. **One Priority Fix** — select one bounded repair with the greatest practical
   value inside the accepted scope.
4. **One Copy-Paste or directly usable Operational Asset** — return one asset
   that can be applied without a broader implementation project.
5. **Before / After Restart Check** — make the changed restart condition
   visible.
6. **One bounded clarification round** — answer questions about the delivered
   audit and asset without expanding scope.

The operational asset may be:

- a fallback restart record;
- a completion gate;
- a state handoff block;
- an operator recovery checklist;
- a bounded incident intake;
- a next-safe-action record;
- an escalation or stop condition.

## Audit dimensions

Each dimension receives one result: `PASS`, `PARTIAL`, `FAIL`, or `UNKNOWN`.

- Trigger clarity
- Accepted-state clarity
- Evidence continuity
- Completion integrity
- Restartability
- Ownership / next actor
- Human recovery burden
- Safe next action

`UNKNOWN` remains explicit when the accepted materials do not establish a
dimension. It is not silently converted into failure, permission, or diagnosis.

## Delivery template

Copy and complete this Markdown template for one accepted incident:

```markdown
# AI Application Workflow Audit

## Scope

Audit Profile: AI_APPLICATION_WORKFLOW
Application or Workflow: <fill this>
Bounded Workflow Path: <fill this>
Audit As-of: <fill this>

## Source Materials

Reviewed: <fill this>
Not Reviewed: <fill this>
Material Restrictions: <fill this>

## Incident As-of State

Trigger: <fill this>
Expected State: <fill this>
Observed State: <fill this>
Current Restart or Fallback Path: <fill this>
Current Owner: <fill this>
Next Safe Action: <fill this>

## Friction Map

| Point | Expected Carrier | Observed Gap | Returned Human Work |
| --- | --- | --- | --- |
| <point> | <carrier> | <gap> | <work> |

## Restartability Diagnosis

Trigger Clarity: UNKNOWN — <rationale>
Accepted-State Clarity: UNKNOWN — <rationale>
Evidence Continuity: UNKNOWN — <rationale>
Completion Integrity: UNKNOWN — <rationale>
Restartability: UNKNOWN — <rationale>
Ownership / Next Actor: UNKNOWN — <rationale>
Human Recovery Burden: UNKNOWN — <rationale>
Safe Next Action: UNKNOWN — <rationale>
Overall Diagnosis: <fill this>

## Priority Fix

Selected Fix: <fill this>
Why Priority: <fill this>

## Operational Asset

Asset Type: <fill this>
Asset Content: <fill this; may continue over following lines>

## Before / After Restart Check

Before: <fill this>
After: <fill this>
Still UNKNOWN: <fill this>

## Unknowns

- <fill this>

## Exclusions

- <fill this>

## Claim Boundary

Vendor Bug Fix: NOT CLAIMED
Future Prevention: NOT CLAIMED
Lost-State Recovery: NOT CLAIMED
Security or Safety: NOT CLAIMED
Productivity / Labor / Cost / Revenue: NOT CLAIMED
Unreviewed Systems: NOT DIAGNOSED
Native Resume: NOT PROOF OF TRUSTWORTHY RESTART

## Completion Line

<fill this>
```

## Validate a completed delivery

The local
[Audit Delivery Validator](../docs/audit_delivery_validator_v0_1.md) is optional
but recommended before paid delivery. `DELIVERY_READY` means structural closure
only. It is not proof of diagnosis truth, Operational Asset efficacy, or client
acceptance.

## Fit-check boundary

The free fit check determines only:

- whether the incident fits;
- whether the workflow is sufficiently bounded;
- whether usable material exists;
- whether the review can be performed without unsafe or unauthorized access.

The free fit check does not include a diagnosis or implementation plan.

## Claim boundary

The delivery must not claim:

- that the underlying vendor bug will be fixed;
- that future incidents will be prevented;
- that lost data or sessions will be recovered;
- that security, safety, productivity, or revenue will improve;
- that native auto-resume is equivalent to trustworthy restart;
- that systems not reviewed have been diagnosed.

## Completion Line

The delivery is complete when:

- one bounded incident is diagnosed;
- one priority repair is selected;
- one usable operational asset is returned;
- the before / after restart distinction is visible;
- all unknowns and exclusions remain explicit.
