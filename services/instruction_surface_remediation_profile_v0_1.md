# Instruction-Surface Remediation Profile v0.1

## Purpose and status

This is a bounded Operational Asset profile inside the existing
[AI Application Workflow Audit](ai_application_workflow_audit_delivery_v0_1.md).
It turns one accepted incident and one selected priority fix into a complete
rule block that can be pasted into an existing instruction surface.

The Audit profile remains:

```text
AI_APPLICATION_WORKFLOW
```

This profile is not a new product family, diagnostic engine, checker, remote
service, or authority to edit a customer's files. It formalizes one directly
usable paid Audit delivery form. A free public sample may demonstrate the
format, but a free fit check does not include bespoke diagnosis or an
instruction-surface asset.

## Supported target surfaces

One delivery may target exactly one bounded instruction surface:

- `AGENTS.md`;
- `CLAUDE.md`;
- a system prompt;
- an operational runbook;
- an equivalent project instruction file.

The target may be repository-wide or limited to one directory, agent,
workflow, or task. The delivery must state the boundary explicitly rather than
assuming that a filename establishes its effective scope.

## When to use this profile

Use this profile only when:

- one concrete incident is inside the accepted Audit scope;
- the incident exposes a bounded instruction, completion, evidence, stop, or
  handoff failure;
- one instruction-level fix is the selected priority repair;
- the authoritative target surface and intended placement can be named;
- the full insertion block can be delivered without credentials, secrets,
  customer data, or unauthorized private material.

Do not use it to disguise a software fix, vendor repair, security review,
workflow redesign, broad documentation rewrite, or ongoing implementation
project as an instruction-only remediation.

## Required delivery fields

Every delivered profile must include all of the following fields. A field may
state `UNKNOWN` only where this profile explicitly permits a recoverable
unknown; an unknown that affects safe placement or authority activates
`HOLD` or `BLOCK`.

### Target Surface

Name the instruction surface that will carry the rule, such as `AGENTS.md`,
`CLAUDE.md`, a system prompt, or an operational runbook.

### Target Path

Record the exact path or named configuration surface, for example
`/AGENTS.md`, `/CLAUDE.md`, or `Operations / Approval Runbook`. Do not infer a
canonical target from similar filenames.

### Intended Scope

State which directory, agent, workflow, or task the inserted rule is intended
to govern. State exclusions when the surface has wider visibility than the
accepted incident.

### Observed Incident

Describe what actually occurred within the accepted evidence boundary. Keep
unverified causes and effects explicit as `UNKNOWN`.

### Selected Fix

Name the first and only instruction-level repair being fixed by this profile.
Do not bundle unrelated policy, product, or workflow changes into the block.

### Exact Insertion Block

Provide the full text exactly as it should be pasted. The block must be usable
without reconstructing missing rules from the Audit narrative. Preserve any
syntax, heading, or delimiter required by the target surface.

### Required Completion Evidence

List what must be inspected and recorded before anyone may report the
remediation complete. Evidence must identify the canonical artifact or state,
the relevant verification, its observed result, and the as-of point.

### HOLD Conditions

List recoverable conditions that require work to stop before completion, such
as an unknown canonical path, unclear placement, missing evidence, or
disagreement among local, remote, and accepted states.

### BLOCK Conditions

List conditions that require refusal rather than inference or retry, including
missing edit authority, prohibited material, an unauthorized overwrite, or a
conflict that would weaken a higher-priority instruction or safety boundary.

### Handoff Requirements

State the minimum restart record for the next human or AI: target, scope,
selected fix, placement, canonical state, verification evidence, unresolved
or `UNKNOWN` items, next actor, next safe action, and rollback path.

### Placement Note

Identify where the block belongs in the existing surface and what nearby rule
or heading anchors that placement. Do not silently replace or reorder
unrelated instructions.

### Rollback

Describe how to remove only the inserted block, restore the recorded prior
state, preserve unrelated later work, and re-run the relevant verification.

### Re-evaluation Trigger

Name the event that requires review of the delivered wording, such as a repeat
incident, a false completion, an instruction-precedence change, a canonical
path change, or evidence that the block conflicts with the actual workflow.

## Copy-and-complete asset template

Use this inside the full Audit's `Operational Asset` section:

~~~~markdown
Asset Type: Instruction-Surface Remediation Profile v0.1
Asset Content: Apply this complete profile only after bounded human review and
authority to edit the named target surface.

Target Surface: <one supported surface>

Target Path: <exact path or named configuration surface>

Intended Scope: <directory, agent, workflow, or task>

Observed Incident: <bounded observed event; keep unverified causes UNKNOWN>

Selected Fix: <one instruction-level repair>

Exact Insertion Block:

```markdown
<full paste-ready text>
```

Required Completion Evidence:

- <canonical artifact or accepted state inspected>
- <verification command or review and observed result>
- <as-of point recorded, plus an exact reference or digest when available>

HOLD Conditions:

- <recoverable condition requiring evidence or clarification>

BLOCK Conditions:

- <prohibited or unauthorized condition requiring refusal>

Handoff Requirements:

- <target and path, scope, selected fix, placement, canonical state,
  verification evidence, unresolved or UNKNOWN items, restart point, next
  actor, next safe action, and rollback path>

Placement Note: <exact insertion anchor without unrelated replacement>

Rollback: <remove this block, restore the recorded prior state, and verify>

Re-evaluation Trigger: <event requiring wording review>
~~~~

Angle-bracket text is a template marker and must be replaced in an actual
delivery. The `Exact Insertion Block` itself must be complete and paste-ready.

## Audit integration

The full delivery still uses the existing Audit headings, dimensions, claim
boundary, and exact accepted-incident identity. In the `Operational Asset`
section:

- `Asset Type` identifies this profile;
- `Asset Content` contains all required profile fields and the exact block;
- the Before / After Restart Check distinguishes the prior operational gap
  from the rule made explicit by the asset;
- unknowns and exclusions remain visible;
- the completion line states what was delivered without claiming adoption or
  efficacy.

The
[synthetic delivery sample](../examples/ai_instruction_surface_remediation_delivery_v0_1.md)
shows the complete form. The
[Validation Run 001](../validation/instruction_surface_remediation_run_001.md)
records its structural checks.

## Application and authority boundary

Delivery of a paste-ready block is not authorization to apply it. Before any
write, the implementing human or agent must separately establish:

- authority to edit the target surface;
- the canonical target and placement;
- the intended scope and precedence;
- the rollback source;
- the completion evidence to retain.

If those conditions are not established, preserve the delivered block without
applying it and use the stated `HOLD` or `BLOCK` condition.

## Claim boundary

This profile does not establish:

- factual correctness or completeness of the incident evidence;
- uniqueness or efficacy of the selected fix;
- that a model, agent, or human will follow the inserted instruction;
- prevention, recovery, security, safety, or software correctness;
- productivity, labor, cost, conversion, or revenue improvement;
- client acceptance or paid-delivery value;
- authority to publish, overwrite, merge, release, or edit another system.

## Rollback and re-evaluation

For one applied delivery, rollback means removing only the exact inserted
block, restoring the recorded prior state when needed, preserving unrelated
changes, and repeating the completion-evidence check.

Re-evaluate this profile after the first real bounded delivery, a false-ready
or false-complete result, a placement or precedence conflict, a repeat incident
despite the block, or a change to the parent Audit contract.

## Completion rule

The profile delivery is structurally complete when one accepted incident maps
to one named target, exact placement and scope, one complete insertion block,
completion evidence, `HOLD` and `BLOCK` conditions, restartable handoff,
rollback, and re-evaluation. Structural completeness is not proof that the
block was applied, followed, effective, or accepted.
