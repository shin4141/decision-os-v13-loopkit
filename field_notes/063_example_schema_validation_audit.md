# Field Note 063: Example Schema Validation Audit

Date: 2026-06-15

## Purpose

This note audits whether the existing example JSON files conform to the repository's own V13 Loop Record schema.

The purpose is to distinguish:

```text
examples exist
```

from:

```text
examples validate against the repo's own schema
```

This is an evidence-quality check only.

It does not modify schema, examples, docs, public surfaces, canonical instructions, tooling, or release state.

## Scope

Schema inspected:

```text
schema/v13_loop_record.schema.json
```

Example files inspected:

```text
examples/block.carrier_damage.json
examples/cap.after_announcement_real_task.json
examples/cap.bounded_public_test.json
examples/cap.external_real_task_review.json
examples/cap.external_v13_readme_usability_review.json
examples/cap.self_application_v13_loopkit.json
examples/cap.v12_handoff_review.json
examples/cap.v13_announcement_post.json
examples/go.loop_positive.json
examples/go.reader_usability_check.json
examples/hold.unclear_cost.json
examples/hold.v13_v1_readiness_review.json
```

Validation method:

- Checked whether Python `jsonschema` was available.
- It was not installed in the local environment.
- Used a minimal read-only Python validation command tailored to `schema/v13_loop_record.schema.json`.

The validation checked:

- JSON parseability
- root object type
- required top-level fields
- disallowed additional top-level fields
- string fields and non-empty string constraints
- `v12_status` enum when present
- `residue` array shape
- `carrier_impact` required keys and impact-level enums
- `re_entry_capacity` required keys and status enum
- `gate` enum
- `cap_or_recheck` string type when present

This did not add a validation tool.

This did not create a validation script file.

## Results

| Example file | Result | Reason |
| --- | --- | --- |
| `examples/block.carrier_damage.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/cap.after_announcement_real_task.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/cap.bounded_public_test.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/cap.external_real_task_review.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/cap.external_v13_readme_usability_review.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/cap.self_application_v13_loopkit.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/cap.v12_handoff_review.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/cap.v13_announcement_post.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/go.loop_positive.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/go.reader_usability_check.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/hold.unclear_cost.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |
| `examples/hold.v13_v1_readiness_review.json` | valid | Parsed as JSON and matched required schema shape, enums, nested impact fields, and re-entry fields. |

Summary:

```text
12 checked / 12 valid / 0 invalid / 0 not checked
```

## Findings

The existing examples currently support adoption and restartability evidence at the schema-structure level.

They are not merely present as illustrative files.

They conform to the repo's own loop-record schema under the local read-only validation method used in this audit.

No schema/example mismatch was found.

No future fix note is required from this audit.

Evidence quality improved because a future reader or agent can treat the example set as structurally consistent with the schema, not only as hand-written examples.

## Validation Limit

This audit used a minimal local validation command because `jsonschema` was not installed.

The result is sufficient for the current schema shape because the schema is simple and the command checked the relevant required fields, enums, nested objects, and additional-property constraints.

This does not prove compatibility with every possible JSON Schema implementation.

It does not justify adding validation tooling.

## Boundaries

Do not:

- edit `schema/v13_loop_record.schema.json`
- edit `examples/*.json`
- add validation tooling
- add a validation script
- edit README or public-entry surfaces
- edit `AGENTS.md`
- edit `AGENTS.ja.md`
- edit `CLAUDE.md`
- edit docs, prompts, or `USE_CASES`
- edit handoff files
- change release state
- modify external repos
- implement automation, hooks, MCP, pluginization, package/server/CLI surfaces, or canonical surfaces
- promote this audit to canonical instructions

## Gate

V12 State:

```text
PASS
```

Reason:

The audit completed, all example JSON files were checked against the repo's schema shape, and no schema/example mismatch was found.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The evidence-quality gap is closed for now, but this does not authorize schema edits, example edits, tooling, public copy, canonical promotion, or feature growth.

## Recommended Next 0.01

Recommended next 0.01:

```text
Stop or park this line.
```

Reason:

All examples validated. There is no immediate schema/example fix to make.

Future validation work should reopen only if:

- examples change
- schema changes
- a real reader or agent reports an example/schema mismatch
- Shin separately authorizes validation tooling or CI

## V13 Signal

Signal:
BLUE / EXAMPLE-SCHEMA-VALIDATION-AUDIT-RECORDED
+
BLUE / 12-EXAMPLES-CHECKED
+
BLUE / 12-EXAMPLES-VALID
+
BLUE / NO-SCHEMA-EXAMPLE-MISMATCH-FOUND
+
YELLOW / VALIDATION-TOOLING-NOT-ADDED
+
YELLOW / NO-SCHEMA-OR-EXAMPLE-EDIT
+
YELLOW / NO-CANONICAL-PROMOTION

V12 State:
PASS

V13 Next Loop Gate:
CAP

Next Loop Command:
Stop after this evidence note. Do not fix schema/examples, add tooling, edit public or canonical surfaces, or expand features unless separately authorized.
