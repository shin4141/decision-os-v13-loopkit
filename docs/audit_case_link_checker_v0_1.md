# Audit Case Link Checker v0.1

## Purpose

`decision-os audit-link` checks whether one local AI workflow Audit delivery
preserves the same six accepted incident-identity values as one local
[Workflow Incident Intake Checker](workflow_incident_intake_checker_v0_1.md)
packet.

The check is deterministic, dependency-free, local, and read-only. It checks
bounded field continuity only. It does not diagnose the incident, evaluate a
repair, or establish that either supplied file is factually correct.

## Commands

JSON is the default output:

```bash
decision-os audit-link accepted-intake.json audit.md
decision-os audit-link --format json accepted-intake.json audit.md
```

Use the deterministic text receipt when preferred:

```bash
decision-os audit-link --format text accepted-intake.json audit.md
```

The command accepts exactly one intake JSON file and one Audit Markdown file.
It performs no repository scan.

## Compared identity fields

The accepted intake values map to the Audit fields as follows:

| Intake JSON | Audit section | Audit field |
| --- | --- | --- |
| `workflow` | `Scope` | `Application or Workflow` |
| `bounded_path` | `Scope` | `Bounded Workflow Path` |
| `trigger` | `Incident As-of State` | `Trigger` |
| `expected_state` | `Incident As-of State` | `Expected State` |
| `observed_state` | `Incident As-of State` | `Observed State` |
| `restart_or_fallback_path` | `Incident As-of State` | `Current Restart or Fallback Path` |

Carry these six values into the Audit without paraphrasing.

`incident_as_of` and `Audit As-of` are independently required by their source
contracts but are not compared by v0.1. A `LINKED` result must not be used to
claim that unlisted fields or prose are identical.

## Comparison normalization

Before exact comparison, each of the six values is normalized only by:

1. converting CRLF and CR line endings to LF;
2. removing leading and trailing whitespace;
3. collapsing internal runs of spaces, tabs, and line breaks to one ASCII
   space.

All other text must be exactly equal. Comparison is case-sensitive and
punctuation-sensitive. The checker does not use fuzzy matching, embeddings, AI
inference, synonyms, case-folding, or Unicode semantic normalization.

## Accepted source contracts

The intake must satisfy the complete
`decision-os.workflow-intake.v0.1` contract. The Audit must be
`DELIVERY_READY` under the
[Audit Delivery Validator](audit_delivery_validator_v0_1.md) and use the
`AI_APPLICATION_WORKFLOW` profile.

An incomplete source contract is `INVALID` for `audit-link`, even when some of
the six values can be found. The checker does not weaken either source
validator or produce a partial continuity claim from an invalid source.

Audit headings and field-like text inside fenced blocks remain ignored. The
six mapped Audit fields are read using the same visible-heading and
visible-field rules used by `audit-check`.

## Local read boundary

The command:

- reads the two supplied local files only;
- performs no network access, telemetry, or writes;
- rejects symlinks, directories, and non-regular files;
- rejects invalid UTF-8;
- rejects intake files larger than 256 KiB;
- rejects Audit files larger than 512 KiB;
- reports only safe basenames, fixed result markers, and field names;
- never echoes compared values or full paths.

Do not place credentials, customer data, production secrets, or unauthorized
private material in either supplied file.

## Result and exit contract

| Result | Exit | Meaning |
| --- | ---: | --- |
| `LINKED` | `0` | All six accepted identity fields match after bounded whitespace normalization. |
| `MISMATCH` | `4` | Both complete source contracts are usable, but at least one identity field differs. |
| `INVALID` | `4` | Either file cannot be safely read, parsed, or mapped to its accepted v0.1 contract. |
| CLI usage error | `2` | The command form is unsupported. |
| Unexpected internal failure | `6` | The bounded checker did not complete. |

`LINKED` proves only field continuity between the two supplied files. It does
not establish source truth, diagnosis quality, repair efficacy, or client
acceptance.

## JSON output

The result schema is:

```text
decision-os.audit-link-result.v0.1
```

The JSON shape is:

```json
{
  "schema_version": "decision-os.audit-link-result.v0.1",
  "command": "audit-link",
  "result": "LINKED | MISMATCH | INVALID",
  "matched_fields": [],
  "mismatched_fields": [],
  "missing_fields": [],
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

Field-name lists always follow the fixed six-field order shown above. Compared
contents never appear in JSON or text output.

## Claims not made

The checker does not establish:

- truth of the intake packet;
- correctness of the Audit diagnosis;
- completeness of source materials;
- efficacy or uniqueness of the Priority Fix;
- client acceptance;
- prevention, recovery, security, safety, productivity, cost, or revenue;
- identity of systems not represented by the supplied files;
- absence of contradictory prose elsewhere.

## Synthetic example

The shipped
[workflow incident intake](../examples/workflow_incident_intake_v0_1.json) and
[Audit delivery](../examples/ai_application_workflow_audit_delivery_v0_1.md)
form one synthetic, non-private pair:

```bash
python3 -B -m decision_os audit-link \
  examples/workflow_incident_intake_v0_1.json \
  examples/ai_application_workflow_audit_delivery_v0_1.md

python3 -B -m decision_os audit-check \
  examples/ai_application_workflow_audit_delivery_v0_1.md
```

The first command returns `LINKED`. The second returns `DELIVERY_READY`.
Neither result is client evidence, a testimonial, a measured result, or proof
that the invented incident and diagnosis are true.

## Service relationship

The checker is an optional but recommended pre-delivery continuity check for
the existing
[AI Application Workflow Audit delivery surface](../services/ai_application_workflow_audit_delivery_v0_1.md).
It creates no new product family, diagnosis, repair, acceptance decision, or
remote service.

## Rollback and re-evaluation

Rollback: revert the Audit Case Link Checker PR. This removes the two checker
modules, tests, documentation, CLI dispatch, and service reference, and
restores the prior synthetic example and Audit validator test fixtures.

Re-evaluate after the first real paid delivery, a false link or false mismatch,
an accepted source-contract change, or evidence that preserving the six exact
values creates excessive delivery burden.
