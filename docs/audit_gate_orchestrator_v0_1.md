# Audit Gate Orchestrator v0.1

## Purpose

`decision-os audit-gate` runs the existing
[Workflow Incident Intake Checker](workflow_incident_intake_checker_v0_1.md),
[Audit Delivery Validator](audit_delivery_validator_v0_1.md), and
[Audit Case Link Checker](audit_case_link_checker_v0_1.md) through one local
command.

It returns `HUMAN_REVIEW_READY` only when all three accepted states are
present:

```text
FIT_CHECK_READY
+ DELIVERY_READY
+ LINKED
= HUMAN_REVIEW_READY
```

This is a structural eligibility result for bounded human review. It is not a
V13 authority gate, delivery acceptance, or evidence that the supplied claims
are true.

## Commands

JSON is the default output:

```bash
decision-os audit-gate accepted-intake.json audit.md
decision-os audit-gate --format json accepted-intake.json audit.md
```

Use the deterministic text receipt when preferred:

```bash
decision-os audit-gate --format text accepted-intake.json audit.md
```

The command accepts exactly one intake JSON file and one Audit Markdown file.
It performs no repository scan.

## Fixed check order

The command uses the existing public validators in this order:

1. intake structure;
2. delivery structure;
3. incident continuity.

Both structure checks run before the ordinary aggregate decision. If an input
identity changes after the intake check, the command fails closed immediately
and does not run later components. Incident continuity runs only when the
intake is `FIT_CHECK_READY` and the delivery is `DELIVERY_READY`.

If either structure is incomplete or invalid, incident continuity is
`NOT_RUN`. The orchestrator does not produce a partial link claim from a source
that is not ready under its own contract.

An accepted nonempty `unknowns` collection does not automatically fail the
aggregate. For example, a structurally complete Audit can remain
`DELIVERY_READY` while its `Unknowns` section is present. Human review still
owns the meaning and resolution of those unknowns.

## Aggregate decision and precedence

| Intake | Delivery | Continuity | Aggregate | Exit |
| --- | --- | --- | --- | ---: |
| `FIT_CHECK_READY` | `DELIVERY_READY` | `LINKED` | `HUMAN_REVIEW_READY` | `0` |
| `INCOMPLETE` | `DELIVERY_READY` or `INCOMPLETE` | `NOT_RUN` | `NOT_READY` | `4` |
| `FIT_CHECK_READY` | `INCOMPLETE` | `NOT_RUN` | `NOT_READY` | `4` |
| `FIT_CHECK_READY` | `DELIVERY_READY` | `MISMATCH` | `NOT_READY` | `4` |
| either source `INVALID` | any | `NOT_RUN` | `INVALID` | `4` |
| `FIT_CHECK_READY` | `DELIVERY_READY` | `INVALID` | `INVALID` | `4` |

`INVALID` has precedence over `NOT_READY` when the two structure checks expose
both conditions in one invocation.

CLI usage errors return `2`. Unexpected internal failures return `6` with a
fixed retry boundary and without exception details.

## Local read and identity boundary

The command:

- reads only the two supplied local files;
- performs no network access, telemetry, or writes;
- inherits each source validator's regular-file, symlink, UTF-8, and size
  boundary;
- reports safe basenames, fixed result markers, and structural field names;
- never reports compared values, file contents, or full paths.

The orchestrator captures regular-file identity before composition and checks
both inputs again after each completed component. A persistent change in
device, inode, mode, size, modification time, or change time fails closed as
`INVALID`.

This is a consistency guard, not an atomic filesystem snapshot. “One run”
means one CLI invocation. The existing validators may physically read the
intake or Audit more than once, and v0.1 does not claim one physical read per
file or exclude a replace-and-restore race between observations.

Do not place credentials, customer data, production secrets, or unauthorized
private material in either supplied file.

## JSON output

The result schema marker is:

```text
decision-os.audit-gate-result.v0.1
```

The stable JSON shape is:

```json
{
  "schema_version": "decision-os.audit-gate-result.v0.1",
  "command": "audit-gate",
  "result": "HUMAN_REVIEW_READY | NOT_READY | INVALID",
  "checks": {
    "intake_structure": {
      "result": "FIT_CHECK_READY | INCOMPLETE | INVALID | NOT_RUN",
      "missing_fields": [],
      "invalid_fields": [],
      "unknowns": []
    },
    "delivery_structure": {
      "result": "DELIVERY_READY | INCOMPLETE | INVALID | NOT_RUN",
      "missing_sections": [],
      "invalid_sections": [],
      "missing_fields": [],
      "invalid_fields": [],
      "unknowns": []
    },
    "incident_continuity": {
      "result": "LINKED | MISMATCH | INVALID | NOT_RUN",
      "matched_fields": [],
      "mismatched_fields": [],
      "missing_fields": [],
      "unknowns": []
    }
  },
  "unknowns": [],
  "claims_not_made": [],
  "minimum_next_step": "",
  "inputs": {
    "intake": {
      "name": "accepted-intake.json",
      "content_echoed": false
    },
    "audit": {
      "name": "audit.md",
      "content_echoed": false
    }
  }
}
```

All field-name lists retain their source contract's fixed order. Component
`unknowns` remain available in JSON. The compact text receipt lists the three
component states, fixed structural blockers, and top-level orchestration
unknowns; it does not reproduce component payloads or supplied content.

## Minimum next step

The aggregate selects one fixed minimum next step:

- intake structure first when the intake is incomplete;
- delivery structure when the intake is ready and the delivery is incomplete;
- exact six-field continuity repair when both structures are ready but differ;
- safe local input replacement for an invalid or identity-unstable input;
- bounded factual human review only after `HUMAN_REVIEW_READY`.

This ordering is deterministic. It is not a diagnosis or a claim that later
steps will succeed.

## Claims not made

`HUMAN_REVIEW_READY` does not establish:

- truth or completeness of either input;
- factual correctness of the diagnosis;
- efficacy or uniqueness of a repair;
- client acceptance;
- paid-delivery value or delivery authorization;
- prevention or recovery;
- software, workflow, security, or safety correctness;
- productivity, labor, cost, or revenue improvement;
- an atomic snapshot or one physical read of each input.

## Synthetic example

The shipped
[workflow incident intake](../examples/workflow_incident_intake_v0_1.json) and
[Audit delivery](../examples/ai_application_workflow_audit_delivery_v0_1.md)
form one synthetic, non-private pair:

```bash
python3 -B -m decision_os audit-gate \
  examples/workflow_incident_intake_v0_1.json \
  examples/ai_application_workflow_audit_delivery_v0_1.md
```

The command returns `HUMAN_REVIEW_READY` with exit `0`. That result is not
client evidence, a testimonial, a measured outcome, or paid-delivery proof.

## Rollback and re-evaluation

Rollback: revert the Audit Gate Orchestrator PR. This removes the two
orchestrator modules, tests, documentation, and CLI dispatch while leaving all
three source validators unchanged.

Re-evaluate after the first real bounded human review, a false-ready or
false-not-ready result, a detected input-identity race, or a change to any
accepted source contract.
