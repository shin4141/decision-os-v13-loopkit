# Handoff Acceptance Guard v0.1 — Shared Evidence Packet

## 1. Packet Identity

```text
Experiment ID: V13-SDFP-001
Selected task: Handoff Acceptance Guard v0.1
Current layer: V13 — Design / Execution Separation
Packet status: FROZEN
As-of: 2026-07-28T10:23:12+09:00
Repository: shin4141/decision-os-v13-loopkit
Repository root observed: /Users/sn/Documents/v13/decision-os-v13-loopkit
Exact base commit: 8146ffa26fe7ff0f0c7981f1abb10a4349b23567
Observation agent: Codex 13-16
Observation branch: codex/v13-sdfp-001-shared-evidence-freeze
B planner status: NOT STARTED
C Shadow Design status: NOT STARTED
Implementation status: NOT STARTED
Evaluator status: NOT STARTED
```

This packet freezes the evidence shared with B and C. The Phase A receipt
records the packet commit, Git blob SHA, and SHA-256 after the bytes are
committed. Those self-identities are not embedded here because adding them to
this file would change the identities being recorded.

## 2. Human Objective

Add a local, read-only, deterministic, fail-closed Guard that determines
whether a repository handoff Artifact is structurally and semantically
sufficient for the receiving AI to know what it now owns and how it may safely
begin.

The Guard must not merely check that fields exist.

It must be capable of detecting material contradictions or ambiguity involving
at least:

- Target Layer;
- repository identity or root;
- Current State;
- Current Gate;
- Active Branch;
- Next Authorized Action;
- Completion Line;
- Missing Closure;
- Next Owner;
- what the receiving AI now owns;
- First One Action;
- Do Not Continue Boundary;
- work that must not be returned to the Decision Owner.

This objective is bounded to the selected task. It is not a product roadmap.

### Fixed future behavior boundary

The future Guard must remain:

- local;
- read-only against the target handoff;
- deterministic;
- fail-closed;
- non-permissive under `UNKNOWN`;
- safe against echoing untrusted handoff content;
- unable to rewrite the handoff;
- unable to approve the transfer automatically;
- unable to grant implementation, shell, branch, commit, merge, or authority
  permissions;
- able to distinguish an acceptable transfer, a non-acceptable transfer, and
  malformed or invalid input;
- unwilling to PASS solely because required field labels exist;
- able to detect material ownership, branch, next-action, Missing Closure, and
  Completion Line contradictions.

Names equivalent to `ACCEPTABLE / NOT_ACCEPTABLE / INVALID` are allowed, but
their exact labels are not frozen in Phase A.

## 3. Primary Proposition

The fixed primary proposition is:

> A frozen Design Artifact can preserve purpose, Completion Line,
> prohibitions, and rollback conditions while still allowing a fresh Codex
> executor to adapt implementation methods without fragmentation, rigidity, or
> silent scope drift.

The real task is evidence for this proposition. It is not the final product
direction.

The later experiment will also examine:

1. whether C Shadow Design uniquely predicts a material execution-stage
   problem missed by B;
2. whether design, execution, deviation, and review Artifacts leave a
   lower-cost restart path;
3. whether Shin avoids becoming the transfer layer for design comparison, file
   placement, Git operations, implementation supervision, or cleanup.

These questions are not answered or scored in Phase A.

## 4. Current Authority

```text
Phase A authority:
repository observation;
baseline validation;
one Shared Evidence Packet;
packet freeze and receipt.

No design authority.
No implementation authority.
No merge authority.
No public authority.
```

GPT 13-13 retains ownership of the experiment through the final Route
Judgment. Shin remains the Decision Owner.

The Phase A entry gate was:

```text
GO UNDER CAP — OBSERVATION AND SHARED PACKET FREEZE ONLY
```

This authority ends when this packet is frozen and the Phase A receipt is
returned. At freeze, the gate becomes:

```text
HOLD — SHARED PACKET FROZEN / AWAIT B AND C PLANNER CREATION
```

## 5. Base State

### Repository and Git identity

Observed before artifact creation:

```text
origin: https://github.com/shin4141/decision-os-v13-loopkit.git
required base: 8146ffa26fe7ff0f0c7981f1abb10a4349b23567
starting HEAD: 8146ffa26fe7ff0f0c7981f1abb10a4349b23567
local main: 8146ffa26fe7ff0f0c7981f1abb10a4349b23567
origin/main: 8146ffa26fe7ff0f0c7981f1abb10a4349b23567
remote main: 8146ffa26fe7ff0f0c7981f1abb10a4349b23567
starting worktree and index: CLEAN
local main versus origin/main: 0 ahead / 0 behind
```

The isolated observation branch was created directly from that exact commit.
`main` was not modified.

Remote PR metadata observed during Phase A records PR #37 as `MERGED`, with
merge commit `8146ffa26fe7ff0f0c7981f1abb10a4349b23567`. PR #37 was not reopened
or altered.

### Package and entry points

Observed package metadata:

```text
distribution: decision-os-v13-loopkit
distribution version: 0.2.0
Python requirement: >=3.10
build backend: flit_core==3.12.0
core dependencies: none
```

Registered console scripts:

```text
decision-os = decision_os.cli:main
decision-os-accelerate = decision_os.acceleration.cli:main
```

`python3 -m decision_os` and repository-local `bin/decision-os` route to
`decision_os.cli:main`.

Observed `decision-os` commands:

```text
check
scan
intake
audit-check
audit-link
audit-gate
```

No dedicated Handoff Acceptance command, module, result schema, fixture family,
or test module was found in the base worktree after repository-wide filename,
content, and Python-symbol searches.

### Current repository-local validation behavior

At the exact base-derived, clean observation branch:

```text
Command: python3 -B -m decision_os scan --format json .
Exit: 0
Mode: V13_MANAGED_REPOSITORY
Route: RUN_V13_CHECK
Snapshot: stable
Remote freshness: NOT_CHECKED
Restart marker semantic quality proven: false
```

The scan observes bounded restart markers but explicitly does not establish
task completion, instruction quality, software correctness, remote freshness,
authority, or a V13 Gate.

```text
Command: python3 -B -m decision_os check .
Exit: 0
V12 State: DELAY
V13 Gate: HOLD
Authority Match: UNKNOWN
Human Seat Required: false
Missing Closure: []
Next Authorized Action:
none unless Shin explicitly approves review-state or merge work
```

The strict check reads the first fenced block from
`handoff/current_codex_handoff.md` and `docs/current_signal.md`. It does not
compare the recorded operational `Active Branch` with the Git checkout branch,
and it does not validate remote PR state.

### Current and historical state observation

At the base commit, the top blocks of both current state surfaces still record
the Companion feature branch as active and PR #37 as open/draft, while Git and
remote PR evidence establish that PR #37 is merged at the base commit. Both
files explicitly mark their lower material as a reverse-chronological
historical ledger that grants no present authority.

The current top handoff block does not instantiate most of the exact
`docs/handoff_command.md` fields. A full example of that exact field family
exists only inside the handoff's historical ledger.

These are observed current-versus-historical facts and a risk input. The known
surface inconsistency is not the selected task, is not repaired by this packet,
and grants no repair authority.

## 6. Relevant File Manifest

All identities below are Git blob SHAs at exact base
`8146ffa26fe7ff0f0c7981f1abb10a4349b23567`.

| Path | Blob SHA | Role in the future task | Why relevant | Evidence class |
|---|---|---|---|---|
| `AGENTS.md` | `f85b0d9b17a8f90a7128ea96d9c8f63a88022128` | Repository operating and authority rules | Routes explicit Handoff, preserves V12/V13 separation, UNKNOWN, ownership, cleanup, and safety boundaries | authoritative |
| `docs/handoff_command.md` | `7ce12bf250cd486844c568777312064491340112` | Explicit Handoff contract | Defines the required fields and the semantic rules for ownership, closure, `none`, and AI-owned routine work | authoritative |
| `handoff/current_codex_handoff.md` | `5126df95cd7797a6239b2746ab70b972e0bf8749` | Repository-designated handoff surface | Supplies the current top block, historical boundary, and multiple historical handoff forms | authoritative, with observed freshness conflict |
| `docs/current_signal.md` | `5e7e5f48b5fee6b11c8b17db397eafcbc3c348b8` | Second canonical state surface used by `check` | Supplies cross-surface state values and the current/historical boundary | supporting |
| `docs/authority_sufficiency_preflight_v0_1.md` | `efd59f12f955003c61b0e284c45a3971c9e7a10e` | Authority sufficiency and closure-tail rules | Establishes that artifacts do not grant authority and that authority is conjunctive | authoritative |
| `docs/context_compression.md` | `5e1ca2d91c1dff0666fdaa7c6b07f6579cc09207` | Restart-equivalent state requirements | Preserves source, Gate, owner, one action, prohibitions, unresolved state, reopen path, and Completion Line | supporting |
| `docs/loop_library_restartable_handoff_loop.md` | `53a6f091aa39d0885dcbd565133aae70113c3edc` | Smaller restartable-handoff convention | Requires evidence, risks, off-limits scope, exactly one safe next action, and stop | supporting |
| `field_notes/099_handoff_responsibility_transfer.md` | `a67bc2a74e0eb3f94b721ba42a2ac1f9a7483ead` | Responsibility-transfer evidence origin | Records that information movement without responsibility movement is a false handoff | historical |
| `field_notes/125_execution_context_proof_selection.md` | `fa8f2b15d966f5550e259e156e71b2bb1b2e506b` | Artifact-provenance nuance | Separates byte identity from semantic completeness, current authority, and safe continuation | supporting origin evidence |
| `pyproject.toml` | `836b43f593003967bb7585b4d9ebe71c3cfd9b33` | Packaging and entry-point declaration | Establishes version, Python floor, dependencies, and registered scripts | authoritative |
| `bin/decision-os` | `07b5cd88453ec679afcc7c0b84cfc7fd50694c79` | Repository-local executable entry | Routes the fixed local executable to the module CLI | supporting |
| `decision_os/cli.py` | `0d106936f9ed3b9cd95955c4175b1a7903e2e098` | Current command dispatch and stable JSON output | Establishes existing commands, usage/internal exits, and serializer behavior | supporting |
| `decision_os/state.py` | `e072baf3bc0a21c507ae9c5def795c939ad68591` | Current state-field parsing | Reads only the first closed fence and parses two-line field/value forms | supporting |
| `decision_os/checks.py` | `4b7b1154d3af0a0847a0a1a588310e5877ea3f9e` | Current strict state and semantic checks | Establishes present required fields, contradiction handling, closure witnesses, and exit codes | supporting |
| `decision_os/scan.py` | `01b3f697ad0cfe862937cbcc9ae4f1b29ad11720` | Bounded restart-surface discovery | Observes handoff candidates and structural markers without claiming semantic quality | supporting |
| `decision_os/scan_text.py` | `ec473134f1c71ea8dee8a60de2231fe5083e9cb9` | Existing safe text rendering convention | Renders allowlisted computed facts and bounded next steps rather than raw content | supporting |
| `decision_os/audit_delivery.py` | `26945ead1628e9903d663059bc24288111f6537b` | Existing domain-specific Markdown validator | Demonstrates structural and selected semantic field checks, Completion Line handling, fail-closed input, and no-echo result behavior | supporting |
| `tests/test_decision_os_checks.py` | `c4249c22d47a2da69d54d24e3cf265f827272b5a` | Strict-check tests | Covers missing, conflicting, unresolved, historical, closure, authority, symlink, UTF-8, and read-only behavior | test evidence |
| `tests/test_decision_os_cli.py` | `80cc4b6d8b5075c29ba05c0da1b752cc198ba876` | Strict-check CLI tests | Covers module/bin parity, repeated byte identity, semantic exits, usage, internal failure, and no-write behavior | test evidence |
| `tests/test_decision_os_scan.py` | `21452330de03af58fd96d21d327bf2a4ce9e338d` | Bounded scan tests | Covers handoff discovery, marker insufficiency, symlink/UTF-8 bounds, snapshot stability, and no-write behavior | test evidence |
| `tests/test_decision_os_scan_cli.py` | `ef902f8730427b5c3586d9beb63eb42bca98da2f` | Scan CLI and protected-contract tests | Covers JSON/text parity, safe rendering, preserved exits, no-write behavior, and protected v0.1 identities | test evidence |
| `tests/test_decision_os_audit_delivery.py` | `016ad20d445b34e3c5fdb0ef5380ff126af568e9` | Existing Markdown-validator tests | Covers heading/field semantics, Completion Line, UNKNOWN rationale, malformed input, fences, and no echo | test evidence |
| `tests/test_decision_os_audit_delivery_cli.py` | `b29efe60068b931a3ba60ca577158ae0461425e2` | Existing validator CLI tests | Covers deterministic JSON/text and result/exit behavior | test evidence |
| `tests/test_decision_os_distribution.py` | `63bff6ba84e92003a11aad9c5494790478b9fa38` | Packaging tests | Fixes package metadata and entry-point behavior | test evidence |
| `tests/fixtures/v13_runner_v0_1/complete/docs/current_signal.md` | `50e127f53b4eda56cb6730f6a99f12badd03fd4b` | Paired complete state fixture | Existing synthetic complete case; not a Handoff Acceptance specification | fixture |
| `tests/fixtures/v13_runner_v0_1/complete/handoff/current_codex_handoff.md` | `070f5630efa57595f87e8007155435b9b5539d09` | Paired complete handoff fixture | Existing synthetic complete case; not authority | fixture |
| `tests/fixtures/v13_runner_v0_1/contradictory/docs/current_signal.md` | `73f3883372b7202249816bc70a5627de864948f2` | Paired contradictory state fixture | Existing cross-surface contradiction evidence | fixture |
| `tests/fixtures/v13_runner_v0_1/contradictory/handoff/current_codex_handoff.md` | `c034705317cbe5b20760571d3f08ab28ec7a6749` | Paired contradictory handoff fixture | Existing cross-surface contradiction evidence | fixture |
| `tests/fixtures/v13_runner_v0_1/missing_closure/docs/current_signal.md` | `1c585ebadc8ef48820ddb26f5f8ce1abcf253d75` | Paired missing-closure state fixture | Existing incomplete closure evidence | fixture |
| `tests/fixtures/v13_runner_v0_1/missing_closure/handoff/current_codex_handoff.md` | `0151506a999d19e5bdc2a535771ab9345d9d3872` | Paired missing-closure handoff fixture | Existing incomplete closure evidence | fixture |
| `tests/fixtures/v13_runner_v0_2/restart_markers/HANDOFF.md` | `76d2c14c33b67aac1612876695ef5f7f5de3bafd` | Structural restart-marker fixture | Contains identity, verification, rollback, missing closure, action, and boundary markers | fixture |
| `tests/fixtures/v13_runner_v0_2/restart_surface/HANDOFF.md` | `02f9259d7da57d0f177e4b58405a78e9249188e3` | Filename-only restart fixture | Preserves the fact that a handoff filename/title alone is insufficient | fixture |
| `validation/minimum_autonomous_loop_v0_1_run_001_preregistration.md` | `0d6255ce833a2b2514be807767ee58593f01d2db` | Prior preregistration convention | Freezes As-of, evidence boundary, scoring criteria, measurements, and no-score-before-run | historical |
| `validation/minimum_autonomous_loop_v0_1_run_001_packet.md` | `ec7ef7345b718bc72bcf700c5038b9ac3af92953` | Prior frozen-packet convention | Demonstrates identical evaluator evidence, role labels, isolation, and stop boundary | historical |
| `validation/minimum_autonomous_loop_v0_1_run_001_result.md` | `452b7bed590673999bcb91f20c3fb343130b77e3` | Prior post-run result convention | Records frozen identities, exact output, criteria, measurements, claim boundary, and closure | historical |

The primary packet path is new in Phase A and therefore has no blob at the base
commit. Its final blob and SHA-256 are recorded in the Phase A receipt.

## 7. Present Behavior

### Existing general repository-state checks

`decision-os scan` performs bounded, local, read-only Git and allowlisted
surface observation. It can detect whether handoff candidates contain accepted
marker classes, but it explicitly records that structural markers do not prove
semantic quality. It routes repositories with both V13 state surfaces to the
strict `check` path.

`decision-os check` reads exactly two fixed current-state surfaces, parses only
their first closed fenced blocks, and requires:

- V12 State;
- V13 Gate;
- Active Branch;
- Next Authorized Action.

It also detects duplicate and cross-surface conflicts for known aliases,
invalid V12/V13 tokens, unresolved alternatives, selected active-run
contradictions, authority-witness failures, closure-evidence gaps, and
authority-window exhaustion contradictions.

The check does not currently:

- require the full explicit-Handoff field set;
- compare textual repository/root identity with the inspected Git repository;
- compare operational Active Branch with the checkout branch;
- validate remote branch or PR state;
- establish the semantic sufficiency of Current State, Completion Line,
  Missing Closure, Next Owner, receiving ownership, Do Not Continue Boundary,
  or work retained by the receiving AI.

### Existing handoff-related documentation

`docs/handoff_command.md` defines a full explicit-Handoff contract with thirteen
required fields. Its semantic rules make ownership transfer, visible missing
closure, AI-owned routine cleanup, and the closed-state conditions for
`First One Action: none` material.

The repository also contains smaller restart and reconnection forms. Their
labels and shapes are not identical to the explicit-Handoff form. The current
global precedence among every supported documentary form is not established by
the inspected evidence.

### Existing semantic and validator behavior

The repository already has domain-specific validators that distinguish
structural readiness, invalid input, incomplete input, and relational
mismatch. Existing validators bound file type and size, reject unsafe or
unstable inputs, preserve stable output shapes, and avoid echoing supplied
content in their public results.

`audit-check` validates one specific Audit profile. It is evidence of an
existing validation convention, not a Handoff Acceptance path.

### Missing dedicated path

No dedicated Handoff Acceptance executable path was found at this As-of.
Absence is bounded to the exact base worktree and the performed repository-wide
searches. Installed packages, unobserved branches, and future commits were not
used as evidence.

## 8. Existing Test and Fixture Surface

### Relevant existing tests

- `tests/test_decision_os_checks.py`: 28 strict state/check tests.
- `tests/test_decision_os_cli.py`: 6 strict CLI tests.
- `tests/test_decision_os_scan.py`: 24 bounded scan tests.
- `tests/test_decision_os_scan_cli.py`: 11 scan CLI/protected-contract tests.
- `tests/test_decision_os_audit_delivery.py`: 26 domain-specific Markdown
  validator tests.
- `tests/test_decision_os_audit_delivery_cli.py`: 7 validator CLI tests.
- `tests/test_decision_os_distribution.py`: 4 package/entry-point tests.

The full suite also covers Intake, Audit Link, Audit Gate, acceleration,
Companion, and their CLIs. Those surfaces are not treated as Handoff Acceptance
tests.

### Fixture conventions

The v0.1 strict-check fixtures pair
`docs/current_signal.md` and `handoff/current_codex_handoff.md` in temporary Git
repositories. Existing tests mutate only temporary copies and compare
worktree-plus-Git digests to establish read-only behavior.

The v0.2 scan fixtures are composable overlays. One contains structural
handoff markers; one intentionally contains only a title/filename. Existing
tests preserve that a marker-bearing file is not semantic proof.

The existing fixtures do not cover the complete Human Objective field family.
They are observed evidence, not a frozen design for new tests.

### Existing result and exit conventions

| Path | Successful result | Non-success result / exit |
|---|---|---|
| `decision-os check` | internally consistent / `0` | usage `2`; non-Git `3`; incomplete `4`; contradiction `5`; internal `6` |
| `decision-os scan` | completed or partial bounded observation / `0` | usage `2`; non-Git `3`; internal `6`; unstable snapshot `7` |
| `decision-os audit-check` | `DELIVERY_READY` / `0` | `INCOMPLETE` or `INVALID` / `4`; usage `2`; internal `6` |

Exit `0` from the current strict check is not handoff approval, transfer
acceptance, implementation authority, or remote freshness.

### Baseline commands and results

Environment:

```text
Python: 3.14.3
macOS: 26.2 arm64
Base: 8146ffa26fe7ff0f0c7981f1abb10a4349b23567
```

Focused state parsing and CLI baseline:

```text
Command:
python3 -B -m unittest -v tests.test_decision_os_checks tests.test_decision_os_cli

Result:
34 / 34 PASS
Exit: 0
Test-runner duration: 17.376 seconds
```

The focused selection is the combination of the existing strict state/check
and strict CLI modules. It is not a new test architecture.

Established full deterministic suite:

```text
Command:
python3 -B -m unittest discover -s tests

Result:
244 / 244 PASS
Exit: 0
Test-runner duration: 68.409 seconds
```

The full-suite command is recorded in existing validation records. The initial
workspace-sandbox attempt ran all 244 tests but produced seven
`CompanionServerTest` setup errors because the sandbox denied an ephemeral
`127.0.0.1` bind. An authorized rerun with localhost binding available passed
244 / 244. No baseline failure was repaired or excluded.

Existing protected v0.1 blob/mode guard:

```text
Result: 1 / 1 PASS
```

The guard currently protects fourteen v0.1 paths, including `checks.py`,
`state.py`, both strict-check test modules, all six paired v0.1 fixtures,
`bin/decision-os`, `decision_os/__main__.py`, and
`docs/v13_runner_v0_1.md`.

## 9. Fixed Completion Line

The experiment is complete only when all of the following later conditions are
established:

1. B and C receive this exact packet;
2. C remains hidden from the B executor;
3. B Design is executed by a fresh Codex executor;
4. required handoff structure and semantic contradictions are testable;
5. false-ready, false-incomplete, malformed, `UNKNOWN`, and ownership
   ambiguity are covered;
6. focused and full suites pass;
7. Plan Gaps, deviations, drift, and rework are recorded;
8. B and C predictions are independently compared;
9. human friction is measured;
10. Shin's voluntary-reuse judgment is recorded;
11. Draft PR and all routine experiment cleanup are closed without returning
    them to Shin;
12. GPT 13-13 issues the next `GO / HOLD / CAP / BLOCK`.

Phase A does not claim that any of these later experiment conditions has
already been met, except creation and freeze of the shared packet needed for
condition 1.

## 10. Fixed Prohibitions

The following prohibitions are frozen for all later actors unless Shin supplies
separate explicit authority:

### Phase and role prohibitions

- Do not perform B Design during Phase A.
- Do not perform C Shadow Design during Phase A.
- Do not begin implementation during Phase A.
- Do not evaluate B, C, the implementation, or the primary proposition during
  Phase A.
- Do not answer the supporting questions during Phase A.
- Do not create public claims or expand the selected task into a product
  roadmap.
- Do not merge.
- Do not continue into B Design after the Phase A receipt.
- Do not treat an artifact, hash, clean tree, passing test, or label set as
  automatic authority.

### Product and repository prohibitions

- Do not redesign or modify Companion.
- Do not expand the narrow Runner.
- Do not reopen or alter PR #37.
- Do not touch PR #4, #5, #24, or #33.
- Do not modify README.
- Do not alter pricing, release, tag, signing, notarization, packaging, sales,
  or public-posting surfaces.
- Do not create public claims.
- Do not implement Design / Execution Separation machinery.
- Do not create a general-purpose Markdown linter.
- Do not create a handoff generator.
- Do not create an orchestration engine.
- Do not create automatic authority granting.
- Do not create automatic branch or Git operations.
- Do not rewrite existing handoffs in bulk.
- Do not use the known `current_signal` / canonical handoff closure
  inconsistency as the selected task.
- Do not repair `docs/current_signal.md`.
- Do not repair `handoff/current_codex_handoff.md`.

### Future Guard behavior prohibitions

- The future Guard must not write or rewrite the target handoff.
- It must not approve a transfer automatically.
- It must not grant implementation, shell, branch, commit, merge, or other
  authority permissions.
- It must not treat `UNKNOWN` as permissive.
- It must not echo untrusted handoff content.
- It must not PASS solely because required labels exist.
- It must not collapse acceptable, non-acceptable, malformed, or invalid input
  into one permissive state.

### Planner-contamination prohibitions

- Do not expose a preferred B or C architecture inside this packet.
- Do not create a gold design that biases either planner.
- Do not recommend a production module layout.
- Do not recommend a particular parser or schema representation.
- Do not prescribe production module file names.
- Do not fix a preferred CLI command name.
- Do not embed a preferred test architecture.
- Do not rank likely designs.
- Do not tell either planner which design should win.
- Do not hide solution language inside evidence.
- Do not include observations available only after implementation.
- Do not write unverified assumptions as facts.
- Do not add hidden hints intended for B or C.
- Do not replace unresolved evidence with inference.
- Do not label an open design choice as missing evidence; use `DESIGN-OPEN`.

### Evidence and validation prohibitions

- Do not treat historical records as current executable authority.
- Do not silently substitute a newer base for
  `8146ffa26fe7ff0f0c7981f1abb10a4349b23567`.
- Do not claim repository-wide absence without bounded inspection.
- Do not treat the minimum observation list as permission to load or summarize
  the whole repository.
- Add an observed file only when its role is directly relevant to the fixed
  task; do not include unrelated files to make the packet appear
  comprehensive.
- Do not silently exclude failing tests.
- Do not repair unrelated baseline failures.
- Do not design new tests in the existing-test observation section.
- Do not inflate Known Risks with unsupported speculation.
- Do not estimate tokens, money, recovered time, or human effort.
- Do not silently replace or alter this packet after freeze.
- Corrections require a new version and an explicit Forward-only Delta.

### Git and operational prohibitions

- Do not mutate `main`.
- Keep experiment changes isolated from the fixed base.
- Create no Phase A product, test, documentation, or state-surface change other
  than this Shared Evidence Packet.
- Do not open a PR during Phase A.
- Do not delete the frozen packet branch needed by later phases.
- Do not ask Shin to run commands, create branches, place the packet, hash
  files, clean the worktree, align the remote branch, or perform other routine
  Git work.
- Destructive, authority-bearing, public, or externally contacting behavior
  requires `BLOCK`.

## 11. Rollback Conditions

- `main` remains unchanged at
  `8146ffa26fe7ff0f0c7981f1abb10a4349b23567` during Phase A.
- Phase A changes remain isolated on
  `codex/v13-sdfp-001-shared-evidence-freeze`.
- The Phase A change boundary is exactly this packet.
- Before any later implementation, the exact base and packet-freeze commit
  remain named restart identities.
- Any later implementation must remain revertible to the exact base or the
  packet-freeze commit through a history-preserving route.
- No merge is allowed without a separate Shin decision.
- If identity, authority, isolation, or the exact change boundary cannot be
  established, stop with `HOLD` before freeze or `BLOCK` before destructive,
  authority-bearing, public, or externally contacting behavior.
- A packet correction is a new version with an explicit Forward-only Delta,
  never an in-place silent replacement.

## 12. Known Risks

These risks are grounded in the observed repository:

- **Label-only false-ready:** required labels can exist in historical ledger
  sections or coexist with material contradictions.
- **Over-rigid false-incomplete:** repository-supported handoff and restart
  forms use different labels and shapes.
- **Parser ambiguity across formats:** the strict state parser reads only the
  first closed fenced block and a narrow two-line field/value form, while other
  repository handoff forms use ordinary Markdown fields and prose.
- **Untrusted-content echo:** handoff content is agent-supplied text; existing
  validators intentionally avoid content echo, and repository safety rules
  require untrusted file content to remain data rather than instructions.
- **Current versus historical confusion:** repeated historical headings and
  fields include inner statements describing themselves as current, while the
  top boundary demotes them to historical evidence.
- **Freshness without semantic validity:** Git blob and SHA-256 identities can
  freeze bytes but cannot prove current correctness, semantic sufficiency, or
  authority.
- **Ownership continuity reduced to memory continuity:** a transfer can carry
  information while omitting executable receiving ownership.
- **Owner substitution:** `Decision Owner` or `Next Owner` alone does not state
  what the receiving AI now owns.
- **Branch and next-action contradiction:** documentary branch/action state can
  diverge from Git or from another surface without the current strict check
  comparing every required relation.
- **Conditional `none` ambiguity:** `none unless ...` is not the explicit
  branch/action/First-One-Action closed triad defined by the Handoff contract.
- **Unresolved closure with `First One Action: none`:** an incomplete transfer
  can appear closed if executable investigation, validation, Git work, or
  cleanup is omitted.
- **Scope expansion:** a narrow acceptance task can drift into general Markdown
  validation, handoff generation, orchestration, or authority automation.
- **Design rigidity:** a frozen design can overfit one documentary format and
  reject meaning-preserving variants.
- **Silent executor redesign:** the executor can replace rather than implement
  the frozen B Design without recording a deviation.

## 13. Known Unknowns

### Repository evidence not established

- `UNKNOWN`: universal present-day precedence between
  `handoff/current_codex_handoff.md` and `docs/current_signal.md`. One
  historical MAL packet gave the handoff precedence at one As-of; that is not a
  universal current rule.
- `UNKNOWN`: whether every update to `handoff/current_codex_handoff.md` must
  satisfy `docs/handoff_command.md`, or whether that exact contract applies
  only when the user explicitly selects Handoff.
- `UNKNOWN`: the currently accepted repository/root identity as represented
  inside the current top handoff block; it contains no exact `Repo Root` field.
- `UNKNOWN`: whether conditional `none unless ...` is intended to count as
  closed `none`; the observed contract defines only explicit closed-state
  conditions.
- `UNKNOWN`: behavior on untested Python versions, operating systems, and
  architectures.
- `UNKNOWN`: whether an equivalent path exists only in an unobserved branch,
  installed artifact, or future commit. The base worktree contains no dedicated
  path.

### Later empirical data not yet available

- B Design quality: `UNKNOWN`.
- C Shadow Design quality: `UNKNOWN`.
- Execution-stage issues: `UNKNOWN`.
- Independent final review findings: `UNKNOWN`.
- Human friction and voluntary reuse: `UNKNOWN`.
- False-ready and false-incomplete rates outside future test cases: `UNKNOWN`.
- Restart cost after the future implementation: `UNKNOWN`.

### Open implementation choices

The following are `DESIGN-OPEN`, not missing repository evidence:

- exact command name;
- parser architecture;
- schema representation;
- production module split and file placement;
- output wording and result labels;
- internal implementation method;
- input-surface selection and normalization policy;
- relation between documentary variants;
- fixture organization;
- focused test composition;
- renderer organization.

## 14. Measurement Preregistration

The experiment measurements are frozen before B, C, implementation, or
evaluation begins.

| Measurement | Packet-freeze value |
|---|---|
| active human operation time | `NOT MEASURED` |
| elapsed waiting time | `NOT MEASURED` |
| manual transfers | `NOT MEASURED` |
| human intervention count | `NOT MEASURED` |
| clarification requests | `NOT MEASURED` |
| pre-execution holes detected | `NOT MEASURED` |
| implementation rework loops | `NOT MEASURED` |
| discarded or rewritten work | `NOT MEASURED` |
| test failures and causes | `NOT MEASURED` |
| scope drift | `NOT MEASURED` |
| Completion Line drift | `NOT MEASURED` |
| silent drift | `NOT MEASURED` |
| valid forward-only deltas | `NOT MEASURED` |
| false complexity | `NOT MEASURED` |
| request omissions | `NOT MEASURED` |
| unresolved debt | `NOT MEASURED` |
| next-Run restart cost | `NOT MEASURED` |
| whether Shin would voluntarily use the flow again | `NOT MEASURED` |

The machine-test durations in section 8 are baseline command observations, not
human-burden measurements. Tokens, money, recovered time, and human effort are
not estimated.

## 15. Required Classification Vocabulary

Later design, execution, and evaluation records must use these frozen
classifications:

- `PLAN_GAP`
- `EXECUTION_DEVIATION`
- `CHANGED_CONDITION`
- `HUMAN_DIRECTION_CHANGE`
- `VALID_FORWARD_ONLY_DELTA`
- `FALSE_COMPLEXITY`
- `REQUEST_OMISSION`
- `REVIEW_ATTRIBUTION_CONFLICT`
- `UNKNOWN`

This vocabulary does not pre-classify any future event.

## 16. B/C Evaluation Rule

For each actual execution-stage issue, later classify whether it was:

- predicted by B only;
- predicted by C only;
- predicted by both;
- predicted by neither;
- falsely predicted by B;
- falsely predicted by C.

Do not reward length, strictness, recommendation count, model prestige, or
vocabulary.

C's central positive signal is:

> a material issue uniquely predicted by C that later appears during B
> execution or independent final review.

C's costs include:

- false complexity;
- unsupported constraints;
- rigidity;
- suggestions unsupported by the frozen packet.

The same evidence threshold applies to B and C.

## 17. Contamination Boundary

- B must not see C.
- C must not see B.
- The executor must see only this frozen packet and the frozen B Design.
- The evaluator may open B and C only after B execution closes.
- C may not be rewritten after B execution.
- This packet may not be altered after freeze.
- Corrections require a new version and an explicit Forward-only Delta, not
  silent replacement.
- B and C must receive byte-identical copies of this packet.
- No recommendation, ranking, hidden hint, or outcome evidence may be added to
  one planner's copy.

Contamination observed at freeze:

```text
NONE OBSERVED
```

## 18. Packet Neutrality Test

The frozen packet was checked against the following neutrality failures:

| Neutrality condition | Result |
|---|---|
| recommends a production module layout | PASS — absent |
| recommends a particular parser | PASS — absent |
| fixes a command name unnecessarily | PASS — absent |
| embeds a preferred test architecture | PASS — absent |
| tells either planner which design should win | PASS — absent |
| contains solution language disguised as evidence | PASS — absent |
| contains observations available only after implementation | PASS — absent |
| writes unverified assumptions as facts | PASS — absent; unresolved facts use `UNKNOWN` |
| converts open design choices into evidence gaps | PASS — choices use `DESIGN-OPEN` |

Overall neutrality:

```text
PASS
```

## 19. Phase A Freeze Boundary

```text
Changed file:
validation/handoff_acceptance_guard_v0_1_shared_evidence_packet.md

B Design: NOT STARTED
C Shadow Design: NOT STARTED
Implementation: NOT STARTED
Evaluator: NOT STARTED
Public claim: NONE
Merge authority: NONE
```

Phase A Completion Line:

> V13-SDFP-001 now has one neutral, base-bound Shared Evidence Packet with
> preregistered boundaries and measurements; no design, implementation,
> evaluation, merge, or public work has begun.
