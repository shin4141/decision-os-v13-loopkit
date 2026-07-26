# Audit Delivery Validator v0.1

The Audit Delivery Validator checks whether one local Markdown delivery packet
contains the required structure for the AI Application Workflow Audit. It is
deterministic, dependency-free, read-only, and limited to structural closure.

It does not establish that a diagnosis is true, a selected fix is unique, an
operational asset will work, or a client should accept the delivery.

## Commands

JSON is the default output:

```bash
decision-os audit-check audit.md
decision-os audit-check --format json audit.md
```

Use the deterministic text view when a human-readable receipt is preferred:

```bash
decision-os audit-check --format text audit.md
```

The executable synthetic example is
[`examples/ai_application_workflow_audit_delivery_v0_1.md`](../examples/ai_application_workflow_audit_delivery_v0_1.md).

## Supported profile

v0.1 supports only:

```text
AI_APPLICATION_WORKFLOW
```

The required Scope declaration is:

```text
Audit Profile: AI_APPLICATION_WORKFLOW
```

The coding-repository Audit profile is not supported in v0.1.

## Result and exit contract

| Result | Exit | Meaning |
| --- | ---: | --- |
| `DELIVERY_READY` | `0` | All required structural surfaces are present. |
| `INCOMPLETE` | `4` | Readable Markdown is missing or malformed required structure. |
| `INVALID` | `4` | The local input or accepted Markdown contract is invalid. |
| CLI usage error | `2` | The command shape is unsupported. |
| Unexpected internal failure | `6` | The bounded validator failed unexpectedly. |

`DELIVERY_READY` means structural closure only. It is not proof of diagnosis
truth, repair efficacy, operational value, or client acceptance.

## Local read boundary

The command:

- reads one local regular file only;
- rejects symlinks, directories, and other non-regular inputs;
- rejects invalid UTF-8 and files larger than 512 KiB;
- performs no network access, telemetry, or writes;
- reports only a safe basename and predefined structural markers;
- does not echo delivery content;
- ignores headings, field-like text, and tables inside fenced blocks;
- rejects an unclosed fenced block.

## Required heading order

One non-empty level-one title is required. The following level-two headings must
each appear exactly once, outside fenced blocks, in this relative order:

1. `Scope`
2. `Source Materials`
3. `Incident As-of State`
4. `Friction Map`
5. `Restartability Diagnosis`
6. `Priority Fix`
7. `Operational Asset`
8. `Before / After Restart Check`
9. `Unknowns`
10. `Exclusions`
11. `Claim Boundary`
12. `Completion Line`

Additional headings may exist, but they cannot replace or reorder the required
headings.

## Required fields

`Scope` binds the supported profile, application or workflow, bounded path, and
Audit as-of state. `Source Materials` states what was and was not reviewed and
the material restrictions. `Incident As-of State` records the trigger,
expected and observed states, restart or fallback path, current owner, and next
safe action.

The eight diagnosis dimensions must begin with exactly one of `PASS`,
`PARTIAL`, `FAIL`, or `UNKNOWN`, followed by a short rationale. `Overall
Diagnosis` is also required. `UNKNOWN` is an explicit judgment, not a
placeholder.

`Priority Fix` requires `Selected Fix` and `Why Priority`. `Operational Asset`
requires `Asset Type` and `Asset Content`; the content may continue across
multiple lines or contain a closed fenced block. The Before / After section
requires `Before`, `After`, and `Still UNKNOWN`.

## Friction Map contract

The Friction Map requires this four-column Markdown table:

```markdown
| Point | Expected Carrier | Observed Gap | Returned Human Work |
| --- | --- | --- | --- |
| one bounded point | expected evidence | observed gap | returned work |
```

Column comparison is case-insensitive. At least one non-placeholder data row is
required. `UNKNOWN` is allowed inside a row.

## Unknowns, exclusions, and placeholders

`Unknowns` and `Exclusions` each require at least one non-placeholder bullet.
When the accepted scope records none, use:

```markdown
- none recorded within the accepted scope
```

An empty value, an angle-bracket placeholder, `TBD`, `TODO`, `FIXME`, or
`PLACEHOLDER` makes a required surface incomplete. `UNKNOWN` remains valid
except where a known Priority Fix, Operational Asset, or Completion Line is
required.

## Exact claim declarations

The Claim Boundary section requires:

```text
Vendor Bug Fix: NOT CLAIMED
Future Prevention: NOT CLAIMED
Lost-State Recovery: NOT CLAIMED
Security or Safety: NOT CLAIMED
Productivity / Labor / Cost / Revenue: NOT CLAIMED
Unreviewed Systems: NOT DIAGNOSED
Native Resume: NOT PROOF OF TRUSTWORTHY RESTART
```

The validator checks those declarations but does not search the rest of the
document for contradictory prose.

## Output boundary

The result uses
`decision-os.audit-delivery-result.v0.1` and exposes only section names, field
names, bounded unknown markers, fixed claim limitations, a safe input basename,
and a bounded next step. `input.content_echoed` is always `false`.

The result explicitly does not establish:

- truth or completeness of source materials;
- factual correctness of the diagnosis;
- uniqueness of the selected Priority Fix;
- efficacy of the Operational Asset;
- absence of contradictory prose elsewhere in the document;
- software, workflow, security, or product correctness;
- prevention or recovery;
- productivity, labor, cost, or revenue improvement;
- client acceptance;
- paid-delivery value;
- testimonial or external delivery evidence.

## Service relationship

The validator is an optional pre-delivery check for the existing
[AI Application Workflow Audit delivery surface](../services/ai_application_workflow_audit_delivery_v0_1.md).
It does not add a product family, diagnose a workflow, perform a repair, or
accept a delivery on the client's behalf.

## Rollback and re-evaluation

Rollback is to remove the validator modules, tests, example, and documentation,
remove the `audit-check` dispatch, and restore the prior service template.
Existing `check`, `scan`, and `intake` behavior remains independent.

Re-evaluate after the first real paid delivery, external validator use, a
false-ready or false-incomplete result, or evidence that the canonical Markdown
format creates excessive delivery burden.
