# Workflow Incident Intake Checker v0.1

## Purpose

`decision-os intake` checks whether one local, non-repository AI workflow
incident packet contains enough bounded structure to begin a free fit
discussion.

It does not perform an Audit, diagnose a workflow or vendor, recover state,
establish correctness or safety, or accept work for a paid Audit.

## Exact-commit first use

Download the example from the exact source commit, then run the checker from
that same commit:

```sh
curl -fsSLo workflow_incident_intake_v0_1.json \
  https://raw.githubusercontent.com/shin4141/decision-os-v13-loopkit/d3ba864c66367e5c676ec14fbaa550801e4f1889/examples/workflow_incident_intake_v0_1.json

uvx --isolated --no-config --no-env-file --no-python-downloads \
  --from "git+https://github.com/shin4141/decision-os-v13-loopkit@d3ba864c66367e5c676ec14fbaa550801e4f1889" \
  decision-os intake --format text workflow_incident_intake_v0_1.json
```

Tool transport:

- `curl` contacts `raw.githubusercontent.com` for the exact example blob;
- `uvx` may contact GitHub for the exact source commit;
- a cold run may contact the Python package index for the pinned build backend;
- a local cache may be used;
- transport messages may appear on stderr.

Intake execution:

- reads only the supplied local JSON file;
- uploads no target workflow data through the checker;
- uses no telemetry;
- performs no input-file writes;
- does not echo packet contents.

## Who this is for

This path is for:

- released AI applications with one concrete incident;
- staging, beta, or pilot workflows with one concrete incident;
- internal AI-assisted operational workflows with one concrete incident.

It is not for:

- a pre-release application with no incident;
- general safety approval;
- a security audit;
- a product-wide code review;
- vendor bug repair.

## Commands

The three Decision-OS commands remain separate:

```text
decision-os check <repository>
decision-os scan <repository>
decision-os intake <packet.json>
```

Workflow Intake Checker accepts exactly:

```text
decision-os intake <packet.json>
decision-os intake --format json <packet.json>
decision-os intake --format text <packet.json>
```

JSON is the default. JSON reports all accepted field presence. Text provides a
fixed summary of the nine fit-boundary fields shown in the example output.
Both formats are deterministic and do not echo field contents. The schema
version and `incident_as_of` remain validated even though the text summary does
not list them.

## Local read boundary

After tool transport, the `decision-os intake` checker:

- reads one local file only;
- performs no network access, telemetry, or writes;
- rejects an input whose final path component is a symlink, plus directories
  and other non-regular files;
- rejects invalid UTF-8 and malformed or non-standard JSON;
- rejects inputs larger than 256 KiB;
- reports only a safe basename, never the supplied path or packet contents.

Do not place credentials, customer data, production secrets, or other private
material in an intake packet. `prohibited_materials` records excluded material
classes; it does not authorize their collection.

## Input schema

The schema version is:

```text
decision-os.workflow-intake.v0.1
```

Required non-empty string fields:

- `workflow`
- `bounded_path`
- `incident_as_of`
- `trigger`
- `expected_state`
- `observed_state`
- `restart_or_fallback_path`

Required non-empty string-list fields:

- `human_recovery_work`
- `materials_available`

`prohibited_materials` must exist and must be a string list. An explicit empty
list is accepted when no prohibited material class is known.

Optional fields are:

- `next_actor`: non-empty string when present
- `next_safe_action`: non-empty string when present
- `unknowns`: string list; an empty list is accepted

Other top-level fields are unsupported in v0.1. String contents are not
diagnosed or fact-checked.

See the bounded
[workflow incident intake example](../examples/workflow_incident_intake_v0_1.json).

## Result contract

JSON uses:

```text
decision-os.workflow-intake-result.v0.1
```

Results and exits are:

| Result | Exit | Meaning |
| --- | ---: | --- |
| `FIT_CHECK_READY` | 0 | Required structure and material-class presence are available. |
| `INCOMPLETE` | 4 | JSON parsed, but a required or accepted field is missing or malformed. |
| `INVALID` | 4 | The file could not be safely read or parsed as the accepted schema. |
| CLI usage error | 2 | The command form is unsupported. |
| Unexpected internal failure | 6 | The bounded checker did not complete. |

`FIT_CHECK_READY` means only that a bounded fit discussion can begin. It is not
a PASS/FAIL Audit judgment and does not imply paid Audit acceptance.

The result never claims:

- workflow or vendor-bug diagnosis;
- task or product correctness;
- security or safety;
- recovery or prevention;
- productivity, labor, cost, or revenue improvement;
- paid Audit acceptance;
- native resume as proof of trustworthy restart.

## Example

```sh
python3 -B -m decision_os intake \
  examples/workflow_incident_intake_v0_1.json

python3 -B -m decision_os intake --format text \
  examples/workflow_incident_intake_v0_1.json
```

The example contains invented, non-private structure only. Replace it with a
sanitized packet that names one bounded workflow path and excludes private
material.

## Rollback and re-evaluation

Rollback: revert the Workflow Intake Checker PR. Existing `check`, `scan`,
offer, pricing, and delivery surfaces remain unchanged.

Re-evaluate after the first external use, a malformed real-world packet, a
fit-check request, or evidence that preparing this JSON creates excessive
human burden.
