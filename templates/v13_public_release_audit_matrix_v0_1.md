# V13 Public-Release Audit Matrix v0.1

## Purpose

This is the stable layer-1 matrix for bounded public-release audits. A
build-specific layer-2 receipt records the audited identity, changed rows,
evidence, exceptions, unresolved items, authority, and final gate.

## Status rules

- `UNCHANGED`: a prior receipt covers the same matrix version and none of the
  row's re-evaluation triggers changed.
- `PASS`: affirmative evidence exists at the audited identity.
- `FAIL`: an established defect requires correction.
- `HOLD`: required evidence or a Decision Owner decision is missing.
- `NOT_APPLICABLE`: the row is inapplicable and the receipt records why.
- Every receipt separately assigns a required finding disposition and
  severity.
- Missing checks, reviews, tests, registry state, or security evidence never
  defaults to `PASS`.

## Stable canonical rows

| Row ID | Stable canonical row | Minimum evidence | FAIL / HOLD rule | Re-evaluation trigger |
|---|---|---|---|---|
| PRV | Identity and privacy | Current-tree identity scan; Owner-approved public identities | Real private or unapproved identity = `FAIL` | Identity, attribution, or new content |
| SEC | Secrets and credentials | Current tree plus reachable-history high-risk scan | Secret = `FAIL` and separate response; incomplete scan = `HOLD` | Any commit, archive, or credential alert |
| PATH | Local paths and environment leakage | Absolute-path, device, and account scan | Real private path in current public tree = `FAIL` | New validation or build record |
| CLM | Public claims and evidence maturity | Public surface compared with verified evidence boundary | Unsupported or stale claim = `FAIL`; evidence missing = `HOLD` | Claim, evidence, or maturity change |
| ENTRY | README and public entry flow | Primary commands and local links | Broken primary path = `FAIL` | README, pins, links, or commands |
| PKG | Install, package, and CLI integrity | Supported-version test and package or entry-point smoke | Broken declared support = `FAIL`; untested minimum = `HOLD` | Version, dependency, or build metadata |
| EX | Examples and templates | Parse or validation result and placeholder classification | User-facing invalid example = `FAIL` | Example, template, or schema change |
| BUG | Known bugs and failure modes | TODO, debug, and known-limit scan | Primary-path defect = `FAIL`; unresolved non-primary issue = `HOLD` | Bug report or behavior change |
| TEST | Tests and regression evidence | Fresh focused and full results with environment recorded | Product failure = `FAIL`; absent evidence = `HOLD` | Code, schema, or test change |
| HYG | Generated files and repository hygiene | Modes, tracked artifacts, and clean test run | Accidental output or private artifact = `FAIL` | New file, mode, or build output |
| BIN | Binary, archive, and database policy | Type, size, and source inventory | Unexplained binary, archive, or database = `FAIL` | New non-text file |
| LIC | License and third-party attribution | License, SPDX, dependencies, and vendored assets | Blocking legal omission = `FAIL` | Dependency, distribution, or license change |
| RPT | Security and reporting boundary | Accurate security model and safe reporting route | Unsafe or misleading instruction = `FAIL` | Security surface, setting, or channel change |
| VER | Version, tag, and release metadata | Package version, tags, releases, and registries | False current release or version claim = `FAIL` | Version, tag, release, or publication |
| GH | GitHub PR, review, and check state | Live PR metadata | Mismatch = `FAIL`; absent independent evidence = `HOLD` | Head, body, state, check, or review change |
| RBK | Rollback and re-evaluation conditions | Exact forward rollback and triggers | Missing or destructive rollback = `FAIL` | Cleanup or release-plan change |
| AUTH | Release and publication authority separation | Explicit merge, release, and publication boundary | Implied or unauthorized public action = `FAIL` | Owner decision or state mutation |

## Required layer-2 receipt fields

```text
build_or_run_id
audit_as_of
repository
audited_head
pr_or_release_candidate
canonical_matrix_version
row_status_vector
changed_rows
evidence_commands_and_results
exceptions
unresolved_items
owner_decisions
final_gate
exact_next_action
re_evaluation_triggers
no_mutation_attestation
```

Future receipts record only changed rows. An `UNCHANGED` row must cite the
previous receipt and affirm that none of its triggers changed.
