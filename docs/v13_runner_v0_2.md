# V13 Runner v0.2 — Unmanaged Repository Scan

## Canonical Integration Receipt

V13 Runner v0.2 was implemented in exactly two operational loops on
`codex/v13-runner-v0-2` and merged through PR #13.

```text
Starting canonical main:
57dc2d1f557aabf40b18c09313fabcb5b6dc96f8

Loop 01:
2e1eb1c93b51b926d976497ac3cd4304872fb4aa / UNMANAGED SCAN ENGINE

Loop 02:
605ca44b6e0b7a86a12002cfec0c687f893cba88 / CLI, TEXT, DOCS, AND VALIDATION

Approved implementation head:
605ca44b6e0b7a86a12002cfec0c687f893cba88

History-preserving merge:
4cbc45acfd39305d771dcac4c50ad126c7ce9cfd

PR:
#13 / PASS / MERGED / COMPLETE

Validation:
69 OF 69 TESTS PASS / 12 OF 12 REQUIRED SCAN SCENARIOS COVERED

Determinism:
JSON AND TEXT REPEATED-BYTE IDENTITY / MODULE-BIN PARITY PASS

No-write proof:
TARGET WORKTREE + GIT DIR + RUNNER SOURCE DIGESTS PASS

Operational loops:
2 OF 2 CONSUMED

Implementation branches:
1 OF 1 USED

Implementation PRs:
1 OF 1 USED

Pre-merge corrections:
2 OF 2 USED

Loop 03:
NOT AUTHORIZED

Rollback Identity:
STARTING MAIN 57dc2d1f557aabf40b18c09313fabcb5b6dc96f8 / IMPLEMENTATION MERGE 4cbc45acfd39305d771dcac4c50ad126c7ce9cfd

Rollback:
NOT EXECUTED

Authority Envelope:
CONSUMED / CLOSED

Closure-Only Tail:
THIS FILE + docs/current_signal.md + handoff/current_codex_handoff.md / CONSUMED BY ENCLOSING COMMIT
```

The enclosing closure commit supplies its own transport identity because a
commit cannot embed its own SHA. The reserved tail grants no implementation,
correction, branch, PR, merge, rollback, release, external action, or v0.3
authority.

V13 Runner v0.2 adds a repository-local, read-only discovery command for an
ordinary Git repository that has not adopted V13:

```text
decision-os scan <repository>
```

The scan collects bounded local evidence. It does not diagnose a workflow,
grant authority, rank values, write to the inspected repository, contact a
remote, or replace the paid AI Agent Handoff Audit.

The strict V13 validator remains:

```text
decision-os check <repository>
```

`scan` does not weaken, replace, or automatically execute `check`.

## Five-Minute Local Path

From this source repository:

```sh
PATH="$PWD/bin:$PATH"
decision-os scan .
decision-os scan --format text .
```

The equivalent module forms are:

```sh
python3 -B -m decision_os scan .
python3 -B -m decision_os scan --format text .
```

No package installation, publication, release, LLM, network access, or global
command registration is required.

## Command and Format Contract

The accepted forms are exactly:

```text
decision-os scan <repository>
decision-os scan --format json <repository>
decision-os scan --format text <repository>
```

JSON is the default. JSON output is one UTF-8 object followed by one line feed,
with sorted keys, stable evidence order, and no timestamp. Text is an explicit,
deterministic rendering of the already-built payload; it performs no second
inspection, terminal detection, wrapping, or additional inference.

The JSON schema is separate from the v0.1 `check` schema:

```text
schema_version:
decision-os.scan.v0.2

scan_completion:
COMPLETE / PARTIAL / FAILED

mode:
UNMANAGED_REPOSITORY / V13_MANAGED_REPOSITORY / UNDETERMINED

evidence.status:
OBSERVED / ABSENT / NOT_APPLICABLE / UNKNOWN / CONTRADICTORY

route.code:
NONE / RUN_V13_CHECK
```

Top-level fields are:

- `schema_version`
- `command`
- `scan_completion`
- `mode`
- `repository`
- `evidence`
- `unknowns`
- `recommendation`
- `route`
- `claims_not_made`

The report omits absolute repository paths, dirty filenames, file bodies,
marker values, credentials, URL query/fragment data, timestamps, and opaque
scores. A configured origin is sanitized. Remote freshness is always
`NOT_CHECKED`.

## Bounded Evidence

Local Git reads report:

- inspectable worktree and `HEAD`;
- branch or detached state;
- clean or dirty state and change count;
- locally recorded default-ref relationship;
- sanitized origin presence and identity;
- opening/closing snapshot stability.

The implementation disables optional Git locks, filesystem monitoring,
terminal prompts, and lazy object fetching. Ambient `GIT_*` variables are
removed so they cannot redirect inspection, change object/index identity, or
write trace output. No `fetch`, `pull`, `ls-remote`, hook, network, or mutating
Git command is run.

Instruction presence is checked only at:

```text
AGENTS.md
CLAUDE.md
.github/copilot-instructions.md
```

Instruction content and quality are not evaluated.

Restart candidates are limited to:

```text
HANDOFF.md
CURRENT_STATE.md
docs/current_state.md
handoff/*.md
```

`handoff/*.md` means direct children only: no recursion, at most 64 Markdown
candidates, and at most 4,096 directory entries inspected. Each candidate is
limited to 256 KiB and all restart content together to 1 MiB.

Descriptor-relative, no-follow traversal rejects intermediate and final
symlinks. Exact path case is required. Unsafe, unreadable, invalid-UTF-8,
oversized, case-mismatched, or over-limit evidence becomes `UNKNOWN`; it is
never silently treated as absent.

## Restart Markers

Readable restart candidates are checked only for exact normalized field-label
classes:

| Class | Accepted labels |
| --- | --- |
| Current identity | `Current Task`, `Active Branch` |
| Verification | `Verification`, `Validation`, `Test Receipt`, `Tests` |
| Rollback | `Rollback`, `Rollback Identity`, `Known-Good Commit` |
| Unfinished work | `Known Gaps`, `Unfinished Work`, `Missing Closure` |
| Next action | `Next Action`, `Next Authorized Action` |
| Boundary | `Not Authorized`, `Do Not Repeat`, `Boundary` |

A file is bounded structural restart evidence only when at least one current
identity marker and one next-action marker are present. Marker values are not
reported or semantically judged. Marker presence does not establish truth,
freshness, completeness, quality, successful verification, or task completion.

## V13 Routing

The canonical V13 paths are:

```text
docs/current_signal.md
handoff/current_codex_handoff.md
```

If both are safely present, mode is `V13_MANAGED_REPOSITORY`. If only one is
present or either cannot be safely established, mode is `UNDETERMINED`. Both
modes return the literal route `decision-os check <repository>` and make no
generic adoption recommendation. Only `check` evaluates canonical V13 state.

The absence of both files selects `UNMANAGED_REPOSITORY`; their absence is not
a failure or a claim that the repository is unsafe.

## Recommendation Contract

The scan returns exactly one of:

```text
NO ADOPTION RECOMMENDATION
LITE RESTART NOTE RECOMMENDED
HANDOFF SURFACE RECOMMENDED
FULLER V13 FIT CHECK MAY BE USEFUL
INSUFFICIENT EVIDENCE
```

The first matching rule applies:

1. V13-managed or undetermined V13 route: no adoption recommendation; use the
   strict `check` route.
2. Unsafe or unreadable bounded evidence in an unmanaged repository:
   insufficient evidence.
3. Multiple instruction surfaces, no bounded restart evidence, and dirty or
   locally-ahead non-default work: a fuller fit check may be useful.
4. Multiple instruction surfaces or locally-ahead non-default work, with no
   bounded restart evidence: a handoff surface is recommended.
5. Dirty work, detached `HEAD`, or exactly one instruction surface, with no
   bounded restart evidence: a lite restart note is recommended.
6. Otherwise: no adoption recommendation.

These are static generic recommendations, not V13 Gates, permissions, safety
ratings, workflow diagnoses, or proof that adoption is required.

## Exit Codes

`scan` uses:

| Code | Meaning |
| ---: | --- |
| `0` | Scan transport completed, including ordinary gaps and optional unknowns |
| `2` | Invalid scan invocation or format |
| `3` | Non-Git/unborn target or required local Git read failure |
| `6` | Unexpected bounded internal failure |
| `7` | Opening and closing evidence cannot belong to one stable snapshot |

`scan` never emits the strict `check` meanings `4` or `5`. An optional missing,
unreadable, malformed, oversized, or rejected surface returns exit `0` with a
visible `PARTIAL` result. Missing evidence is not permission to continue.

The existing `check` exit codes, fields, first-current-block rule, historical
separation, and contradiction precedence remain unchanged.

## Explicit Non-Claims

The scan does not establish:

- repository safety;
- task completion;
- instruction quality;
- software correctness;
- remote freshness;
- workflow-specific causation or repeated failure;
- Aspire, Gate, authority, or a Human value decision.

A clean worktree is not task completion. A filename is not a valid handoff.
An instruction file is not proof of instruction quality. A test marker is not
proof that software is correct. Multiple instruction surfaces are not, by
themselves, a contradiction.

## Optional Repository-Specific Interpretation

`decision-os scan` reports bounded, generic repository evidence; it does not
provide workflow-specific diagnosis, select a custom priority fix, or give
implementation advice. If repository-specific interpretation may be useful,
you may
[open the AI Agent Handoff Audit fit-check form](https://github.com/shin4141/decision-os-v13-loopkit/issues/new?template=ai_agent_handoff_audit_fit_check.md).
The free fit check confirms only fit, bounded scope, and material availability;
bespoke diagnosis begins only after scope confirmation and payment. Because
the form is public, do not post credentials, secrets, private repository
content, customer data, or confidential material.

The link is documentation-only. JSON and terminal output contain no URL,
automatic lead submission, tracking, payment flow, price, personalized sales
pressure, or free bespoke diagnosis.

## Implementation and Closure Boundary

Runner v0.2 is standard-library-only and repository-local. Its bounded
implementation surfaces are `decision_os/scan.py`,
`decision_os/scan_text.py`, the explicit `scan` dispatch in
`decision_os/cli.py`, v0.2-only tests/fixtures, and this document.

The integration receipt is reserved for the predefined Forward-only
closure-only tail after exact-head review and history-preserving merge. That
tail may update only this document, `docs/current_signal.md`, and
`handoff/current_codex_handoff.md`. Until that receipt is written, this section
does not claim merge completion or grant additional authority.
