# V13-GI-001 — Guided Intake v0.1 Shared Evidence Packet

## 1. Packet Identity

```text
Task ID:
V13-GI-001

Protocol Run:
V13-PMR-003

Target:
Guided Intake v0.1

Layer:
V13 — Stage 3

Scout:
Codex 13-27

Scout role:
SOL Scout / repository observation and evidence fixation only

Packet status:
FROZEN SHARED EVIDENCE

Observation time:
2026-07-29T08:51:05+09:00

Repository:
shin4141/decision-os-v13-loopkit

Repository root observed:
/Users/sn/Documents/v13/decision-os-v13-loopkit

Exact As-of commit:
d785dbd9fe3ec3c41bbe0771080ad1d0a47f9d48

Observation branch:
codex/v13-guided-intake-evidence

Decision Owner:
Shin

Independent Pro Design:
NOT STARTED

Guided Intake implementation:
NOT STARTED

Product test changes:
NOT STARTED

Product PR:
NOT CREATED
```

This packet freezes current repository evidence for one later Independent Pro
Designer. It records implemented, partially implemented, documented-only,
absent, and unknown capabilities. It does not select a Guided Intake
architecture, final UI, command, schema, model, storage surface, or execution
route.

The packet's Git blob SHA and file SHA-256 are not embedded because either
literal would change the bytes being identified. The Scout completion receipt
externally fixes both identities after the one-file commit.

## 2. Task Boundary

```text
Objective:
Observe the canonical repository and create one frozen Shared Evidence Packet
that allows an Independent Pro Designer to design the smallest
repository-native Guided Intake v0.1 surface without re-observing current
intake, Companion, Manual Bridge, handoff, authority, test, and evidence
behavior.

Core Question:
What is the smallest repository-native product surface that can transform one
ambiguous request into Objective, Completion Line, Do Not Touch, and UNKNOWN
without inventing intent or granting execution authority?

Scout Authority:
Repository observation plus creation, validation, commit, and push of exactly
this one packet.

Scout Does Not Own:
Product design, implementation, product-test changes, PR creation, merge,
publication, posting, AGENTS.md changes, Framework Router experiments, or
Stage 4–5 work.

Completion Line:
The canonical repository state is verified; current and absent intake
capabilities are separated; the four primary outputs, Original Request
traceability, authority boundary, UNKNOWN boundary, before/after
demonstration, and later evaluation evidence are fixed; and exactly this one
new packet is committed and pushed without starting design or implementation.
```

The packet answers the Core Question with evidence and open questions only. An
existing surface named in this packet is an observed fact, not a selected
architecture.

## 3. Canonical Repository State

Before branch creation or file modification, these identities were observed:

```text
Required canonical main:
d785dbd9fe3ec3c41bbe0771080ad1d0a47f9d48

Starting HEAD:
d785dbd9fe3ec3c41bbe0771080ad1d0a47f9d48

Local main:
d785dbd9fe3ec3c41bbe0771080ad1d0a47f9d48

origin/main:
d785dbd9fe3ec3c41bbe0771080ad1d0a47f9d48

GitHub refs/heads/main:
d785dbd9fe3ec3c41bbe0771080ad1d0a47f9d48

Local main versus origin/main:
0 ahead / 0 behind

Starting branch:
main

Starting index and worktree:
CLEAN

Untracked files:
NONE

Unmerged entries:
NONE

In-progress merge or unresolved index state:
NONE
```

The repository remote is:

```text
https://github.com/shin4141/decision-os-v13-loopkit.git
```

The As-of commit is the merge of Stage 2 PR #43. The canonical worktree
therefore contains the implemented Companion Manual Bridge and the Stage 2
closure record. Stage 1 and Stage 2 are evidence inputs for Stage 3; this Scout
does not reopen either result.

```text
Stage 1:
Pro Manual Protocol — CLOSED

Stage 2:
Companion Manual Bridge — CLOSED / MERGED

Stage 3:
Guided Intake — SCOUT
```

The observation branch was created directly from the exact As-of commit. No
reset, rebase, overwrite, cleanup, or main update was performed.

## 4. Stage 3 Fixed Purpose

Guided Intake v0.1 begins with:

```text
one raw user request
```

It must make the original request traceable and produce exactly these four
primary fields:

```text
Objective
Completion Line
Do Not Touch
UNKNOWN
```

Its purpose is not to make a request sound polished. Its purpose is to prevent
an execution agent from silently inventing:

- the actual objective;
- the definition of completion;
- the permitted change surface;
- missing facts;
- authority.

The roadmap already documents Stage 3 as an ambiguous-request structuring
stage at
`field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md:118-133`. That
roadmap also lists `Evidence Needed`. The current V13-GI-001 transfer fixes
Objective, Completion Line, Do Not Touch, and UNKNOWN as the four primary
fields. `Evidence Needed` is not established by this Scout as a fifth primary
field.

Guided Intake v0.1 remains distinct from:

- the existing workflow-incident intake checker;
- the Companion's direct one-task Runner;
- the Stage 2 Manual Bridge;
- an Execution Handoff;
- handoff acceptance;
- Builder authority;
- independent completion or audit.

## 5. Existing Intake Surfaces

### Workflow Incident Intake Checker

`decision_os/intake.py` implements a deterministic checker for one local JSON
workflow-incident packet. Its required fields are workflow, bounded path,
incident time, trigger, expected and observed states, recovery work, restart or
fallback path, materials, and prohibited materials. Optional fields are next
actor, next safe action, and an `unknowns` list.

Observed behavior:

- the input is one local regular UTF-8 JSON file, capped at 256 KiB;
- duplicate keys, non-finite values, malformed JSON, non-object JSON, symlinks,
  non-regular files, unstable snapshots, and unsupported fields fail closed;
- output reports field presence and validity but deliberately does not echo
  packet contents;
- a nonempty input `unknowns` list becomes only
  `input_unknowns_present` in the result;
- unknown contents are not preserved in the output;
- a nonempty required string containing the literal `UNKNOWN` satisfies the
  current shape check;
- `FIT_CHECK_READY` means only that a bounded fit discussion may begin.

The accepted field allowlist does not contain `original_request`, `objective`,
`completion_line`, or `do_not_touch`. Adding those names to a current incident
packet would make them unsupported fields. This implemented incident checker
must not be described as Guided Intake.

`decision_os/cli.py` accepts only an intake packet path, with optional JSON or
text output. `decision_os/intake_text.py` renders field names and a structural
claim boundary, not the original content or a four-field interpretation.

### Existing incident-to-Audit chain

Three later validators consume the already-structured workflow-incident packet
and an already-written Audit delivery:

- `audit_delivery.py` requires structural Audit sections including
  `Unknowns`, `Exclusions`, and `Completion Line`;
- `audit_link.py` compares six enumerated incident fields from intake to Audit
  after bounded whitespace normalization;
- `audit_gate.py` runs intake, delivery, and continuity checks, then composes
  bounded component results.

This is useful adjacent evidence, not Guided Intake:

- the continuity checker covers only workflow, bounded path, trigger, expected
  state, observed state, and restart/fallback;
- the delivery validator checks visible, non-placeholder section shape but
  neither derives a Completion Line nor establishes that it is testable;
- an Audit Completion Line beginning with UNKNOWN is rejected, while Guided
  Intake must preserve unresolved completion as UNKNOWN and remain HOLD-capable;
- Audit `Exclusions` are not an exact Stage 3 Do Not Touch boundary;
- result receipts retain bounded markers and statuses, not the underlying
  unknown, exclusion, or request content;
- `HUMAN_REVIEW_READY` is structural eligibility for a later human review, not
  V13 execution authority or delivery acceptance.

The Audit gate therefore implements incident-specific identity continuity and
result aggregation. It does not preserve an Original Request, perform the
four-field transformation, or aggregate substantive Guided Intake evidence.

### Companion free-text task

The Companion contains one free-text `Bounded task` textarea. The browser posts
its value directly to `/api/run`; the controller requires a nonempty string,
applies `task.strip()`, and starts the Codex adapter in a fresh Run.

This is a raw task entry surface, but it is not a Guided Intake surface:

- it routes directly to execution;
- it does not produce the four fields;
- leading and trailing whitespace are removed before adapter dispatch;
- task text is not retained in the public Run state;
- the Companion state file persists only the repository path;
- it creates no Original Request identity or before/after artifact.

An unmatched exact repository × action × normalized path reaches a human
choice: Allow once, Use for this repository, or Deny. A verified saved exact
repository/action/path decision can later be reused without showing a new
approval card. The saved rule remains exact and revocable; terminal
verification remains separate. This execution gate does not convert direct
execution into non-authoritative intake.

## 6. Existing Companion and Bridge Surfaces

The canonical Companion has two separate paths.

### One-task Runner path

```text
Bounded task textarea
→ POST /api/run
→ CompanionController.start_run()
→ Codex adapter
→ read-only result or exact single-file create/modify approval
→ Verified Save/Reuse Receipt
```

The accepted Companion evidence establishes a private localhost, one-task
Runner, not a true multi-turn chat client and not native Codex Desktop
interception. The Runner Receipt records bounded execution/approval evidence;
it is not an intake-interpretation receipt.

### Execution and approval substrate

The acceleration layer is an implemented execution substrate:

- each Run starts a fresh ephemeral Codex thread with a read-only sandbox and
  fixed runtime identity;
- the prompt is sent to execution, but prompt or conversation content is not
  stored in the default or outward Receipt;
- only one typed file add or update maps to the bounded CREATE/MODIFY approval
  path; unsupported mutation shapes fail closed;
- the first unmatched exact repository/action/path invokes the human decision;
- choosing repository use creates a standing exact default;
- a later exact match skips the repeated approval interrupt and is promoted to
  `VERIFIED_SAVE` or `VERIFIED_REUSE` only after a normal checkpoint;
- revocation and supersession stop later matching while preserving verified
  history.

The default identity excludes prompt text, reason, diff, model, timestamp, and
Run ID. A different diff against the same exact repository/action/path can
therefore reuse the saved decision without a renewed human diff review, while
the adapter still binds completion to the typed change for that Run. A
different repository, action, or path does not match.

This is execution routing and authority handling after a task has been sent to
Codex. It provides no Original Request artifact and performs no Guided Intake
interpretation.

### Manual Bridge path

```text
manually authored structured boundary
→ Copy for Pro
→ exact artifact imports
→ instruction-only Execution Handoff
→ Bridge Receipt / Golden manifest / structural Replay
```

The Manual Bridge already exposes manually entered:

```text
Task ID
Protocol Run ID
Objective
Completion Line
Do Not Touch
Current Gate
Authority Boundary
As-of commit
Required next actor
Evidence Packet identity
```

Blank UI values are sent as `UNKNOWN`. The backend normalizes bounded scalar
values, treats an UNKNOWN required boundary value as incomplete, and records:

```text
HOLD — INCOMPLETE BOUNDARY
```

The Bridge does not call a model, start Codex, approve a change, mutate the
selected worktree, or grant authority. Its private state is stored under the
repository's Git common directory, separate from the Companion Runner's
acceleration state.

The Bridge is an implemented consumer and carrier of already-structured
fields. It does not:

- receive the Runner's raw task;
- derive Objective, Completion Line, Do Not Touch, or UNKNOWN from that task;
- preserve an Original Request role or identity;
- verify that an Objective did not expand the request;
- verify that a Completion Line is testable;
- verify that Do Not Touch is complete;
- automatically route its generated handoff to the Runner.

The generated Stage 2 Execution Handoff directly carries Completion Line. Its
required headings do not include exact Objective or exact Do Not Touch.
Objective is used only as a fallback inside receiving-ownership prose, and a
separate `Do Not Continue Boundary` may receive generic default prose. This is
an existing Stage 2 boundary, not evidence that Stage 3 fields are preserved
into a receiving Builder handoff.

### Existing receipt and comparison surfaces

The Bridge implements:

- exact-byte hashing before text parsing for imported artifacts;
- content-addressed artifact storage;
- hash-chained event evidence;
- role and authority validation;
- authority-inflation blocking;
- Bridge Receipt generation;
- six-role Golden manifest fixation;
- deterministic fifteen-field structural Replay.

Replay includes objective, completion line, do-not-touch, authority, and
unknown atoms and can report preserved, altered, missing, substituted,
authority-inflated, not-applicable, or unknown status. It compares
already-structured artifacts. It does not compare an Original Request with a
model-generated interpretation and cannot prove recovered intent or a testable
Completion Line.

## 7. Existing Handoff and Authority Structures

`docs/handoff_command.md` defines a repository-native responsibility-transfer
artifact with thirteen fields:

```text
Target Layer
Repo Root
Current State
Current Gate
Active Branch
Next Authorized Action
Completion Line
Missing Closure
Next Owner
What the Receiving AI Now Owns
First One Action
Do Not Continue Boundary
What must not be returned to the Decision Owner
```

The documented command transfers current state only. It does not start work,
make a new judgment, or choose a new target. Unknown fields remain explicit;
missing closure and routine execution work cannot be hidden or returned to
Shin.

The handoff contract contains Completion Line and a continuation boundary, but
it does not contain Original Request, Objective, or exact Stage 3 Do Not Touch.

The Manual Bridge implements deterministic generation of that handoff shape
after a complete structured boundary and a valid identity-bound Pro Design
import. The generated artifact fixes:

```text
Current Gate:
HOLD — SEPARATE BUILDER AUTHORITY REQUIRED

Authority state:
INSTRUCTION_ARTIFACT_ONLY
```

Its existence, identity, model, role, timestamp, or hash grants no execution,
merge, publication, or release authority.

`decision_os/handoff_acceptance.py` implements a separate read-only assessment
of one existing structured handoff. It:

- binds local repository, target layer, branch, owner, completion, and
  responsibility relations;
- rejects unresolved, ambiguous, conflicting, dirty, unmerged, or unstable
  states;
- routes every active responsibility transfer to semantic review;
- auto-accepts only a bounded clean canonical closed state;
- always reports approval not performed, authority not granted, and writes not
  performed;
- does not check remote freshness.

Handoff acceptance is not handoff generation and is not Guided Intake.

## 8. Implemented / Partial / Documented / Absent Matrix

The status labels mean:

```text
IMPLEMENTED:
current code plus tests or accepted repository evidence establish the bounded
behavior.

PARTIALLY IMPLEMENTED:
a narrower existing behavior carries some relevant structure but does not
satisfy Guided Intake v0.1.

DOCUMENTED ONLY:
repository prose fixes a requirement or convention with no matching Stage 3
execution path.

ABSENT:
bounded inspection of canonical product, documentation, validation, and
related tests found no matching implementation or dedicated Stage 3 surface.

UNKNOWN:
the canonical repository does not establish the fact.
```

| Capability | Status | Current evidence and Stage 3 boundary |
|---|---|---|
| Workflow-incident JSON intake | `IMPLEMENTED` | Strict local structural checker; not raw Guided Intake |
| Safe local intake-file read | `IMPLEMENTED` | Regular-file, size, UTF-8, JSON, duplicate-key, and snapshot guards |
| Incident UNKNOWN presence marker | `IMPLEMENTED` | Preserves only that input unknowns exist, not their content |
| Incident-to-Audit six-field continuity | `IMPLEMENTED` | Six enumerated fields compared after bounded whitespace normalization; no Original Request or Stage 3 fields |
| Audit delivery section validation | `IMPLEMENTED` | Requires structural Unknowns, Exclusions, and Completion Line; not semantic derivation or testability |
| Audit gate result aggregation | `IMPLEMENTED` | Composes bounded statuses without component content; not substantive Guided Intake evidence |
| One free-text Companion task input | `IMPLEMENTED` | Directly starts a Codex Run after trimming; not a structuring step |
| Original Request preservation in Companion | `ABSENT` | Task is not retained or hashed as an intake artifact |
| Exact file-change decision gate | `IMPLEMENTED` | Human decision for an unmatched exact repository/action/path |
| Verified saved exact-access reuse | `IMPLEMENTED` | Later exact matches can skip a repeated approval card after verified save |
| Prompt-to-Codex execution routing | `IMPLEMENTED` | Fresh bounded Run; execution path, not structuring or Original Request preservation |
| Manually authored Bridge boundary | `IMPLEMENTED` | Objective, Completion Line, Do Not Touch, gate, authority, actor, and evidence identity |
| HOLD on incomplete Bridge boundary | `IMPLEMENTED` | UNKNOWN in a required boundary field prevents Copy or handoff |
| Objective carrier | `PARTIALLY IMPLEMENTED` | Manual Bridge field and Replay atom exist; no raw-request recovery or expansion check |
| Completion Line carrier | `PARTIALLY IMPLEMENTED` | Manual Bridge and handoff fields exist; no general testability check |
| Do Not Touch carrier | `PARTIALLY IMPLEMENTED` | Manual Bridge and Replay field exist; exact value is not a required generated-handoff heading |
| UNKNOWN preservation | `PARTIALLY IMPLEMENTED` | Strong Stage 2 sentinel/atom behavior exists; no Stage 3 primary output from raw uncertainty |
| Structured field shape validation | `PARTIALLY IMPLEMENTED` | Existing validators check shape, identity, and bounded prose, not recovered intent |
| Exact artifact-byte identity | `IMPLEMENTED` | Manual Bridge hashes imported bytes before parsing; no Original Request role exists |
| Authority non-grant | `IMPLEMENTED` | Bridge, handoff, and acceptance explicitly separate identity from authority |
| Authority-inflation detection | `IMPLEMENTED` | Stage 2 import and Replay guards cover bounded authority states |
| Instruction-only handoff generation | `IMPLEMENTED` | Stage 2 only; separate Builder authority remains required |
| Generated-handoff-to-execution routing | `ABSENT` | Bridge generation and Runner execution remain separate |
| Read-only handoff acceptance | `IMPLEMENTED` | Existing structured handoff only; active transfers require semantic review |
| Receipt/evidence chain | `IMPLEMENTED` | Runner and Manual Bridge each have bounded but separate evidence records |
| Structural before/after Replay | `PARTIALLY IMPLEMENTED` | Compares structured artifact atoms, not raw request versus four fields |
| Stage 3 purpose and field family | `DOCUMENTED ONLY` | Roadmap names ambiguous request and Stage 3 fields |
| Raw request → four primary fields | `ABSENT` | No module, route, command, UI, schema, fixture, or test performs the transformation |
| Original Request trace field or identity | `ABSENT` | No canonical Stage 3 field, hash, role, or linkage exists |
| Objective-preservation evaluation | `ABSENT` | No comparison to an Original Request |
| Added-objective detection | `ABSENT` | No Stage 3 evaluator or fixture |
| Completion testability evaluation | `ABSENT` | Existing guards detect presence or bounded closure forms only |
| Protected-surface completeness evaluation | `ABSENT` | No raw-request-to-Do-Not-Touch evidence check |
| Stage 3 UNKNOWN provenance evaluation | `ABSENT` | No evidence links unresolved facts back to a raw request or clarification |
| Guided Intake authority-inflation evaluation | `ABSENT` | Adjacent authority guards exist, but no Stage 3 output evaluator exists |
| Visible Guided Intake before/after example | `ABSENT` | No canonical example, product display, or validation artifact |
| Final Guided Intake product placement | `UNKNOWN` | CLI, Companion, Bridge, or another repository-native surface is not selected |
| Final Guided Intake UI | `UNKNOWN` | This Scout has no design authority |
| Transformation method | `UNKNOWN` | Model, deterministic, hybrid, or human-interactive behavior is not fixed |
| Scoring implementation | `UNKNOWN` | Explicitly deferred; evaluation evidence is required, but scoring design is not part of this Scout |

The matrix does not rank current surfaces. Adjacent implemented behavior may
constrain or inform a later design without making any component the selected
Guided Intake architecture.

## 9. Guided Intake Fixed Inputs

The later product accepts:

```text
one raw user request
```

Fixed input boundaries:

- the request may be ambiguous or incomplete;
- the exact Original Request remains available for traceability;
- the request is evidence, not permission to infer missing facts;
- the request is not an execution grant;
- the request does not authorize file changes, merge, publication, release, or
  transfer;
- missing context stays visible instead of being replaced by a plausible
  interpretation;
- a later actor must be able to distinguish user text from model-generated
  interpretation.

The repository does not yet establish size, encoding, normalization, storage,
retention, redaction, or interaction-round rules for this input. Those remain
design-open.

## 10. Guided Intake Fixed Outputs

The later product produces one traceable intake containing:

```text
Original Request:
preserved verbatim or byte-traceable

Primary fields:
Objective
Completion Line
Do Not Touch
UNKNOWN
```

These names are fixed. Their representation, schema, display, persistence, and
transport are not fixed by this Scout.

The output is a bounded execution intake, not:

- evidence that user intent was detected correctly;
- a grant of execution or Builder authority;
- a handoff acceptance result;
- merge, publication, posting, release, or transfer approval;
- Product PASS;
- proof of generality or automatic correctness.

If the boundary is incomplete, the output remains HOLD-capable.

## 11. Original-Request Traceability

Protected rule:

```text
A model-generated interpretation is not the Original Request.
```

The later product must retain a visible and independently checkable relation
between the exact input and the four generated primary fields. A polished
restatement is not traceability.

Current evidence does not satisfy this rule:

- workflow incident intake intentionally emits no content and no input digest;
- Companion Runner input is trimmed and not retained in state;
- Manual Bridge exact-byte import roles do not include Original Request;
- handoff and handoff-acceptance fields omit Original Request;
- Stage 2 Replay begins from already-structured atoms.

Later independent evaluation therefore requires:

- the exact Original Request or an independently verifiable byte identity;
- the exact structured output being evaluated;
- evidence that the original was not overwritten by the interpretation;
- a visible distinction between user-provided text, generated text, and any
  later correction;
- a stable link allowing an evaluator to compare every claimed field against
  the original.

The mechanism for providing that evidence is design-open.

## 12. Objective Boundary

Objective must identify only the work supported by the Original Request.

Fixed rules:

- Objective must not silently expand;
- added goals, deliverables, users, repositories, surfaces, or outcomes are not
  clarification;
- inferred commercial, release, posting, implementation, or authority goals
  are prohibited;
- unresolved objective scope remains UNKNOWN or HOLD-capable;
- fluent prose is not proof that the actual objective was recovered.

Current Manual Bridge behavior proves only that a manually supplied Objective
is present and can be preserved as a structural atom. It does not establish
semantic fidelity to an Original Request. Existing handoff acceptance has no
Objective field.

Later evaluation needs direct evidence for both:

```text
preserved original objective
no added objective
```

## 13. Completion Line Boundary

Completion Line states what observable condition would make the bounded task
complete.

Fixed rules:

- it must be testable or remain UNKNOWN;
- it must not substitute a polished claim for observable completion;
- it must not import implementation details unsupported by the request;
- it must not imply merge, publication, release, or execution authority;
- if a testable condition cannot be recovered, the intake remains
  HOLD-capable.

Existing surfaces provide partial structure:

- Stage 1 requires Completion Line before a Run;
- Manual Bridge requires a non-UNKNOWN boundary scalar;
- generated Stage 2 handoff carries the scalar directly;
- handoff acceptance detects a bounded set of open/closed contradictions and
  otherwise requires semantic review.

None of these proves that a Completion Line generated from an ambiguous request
is testable. Later evaluation needs the Original Request, the generated
Completion Line, and independent evidence identifying the observable
completion condition or the unresolved gap.

## 14. Do Not Touch Boundary

Do Not Touch names protected surfaces and excluded actions for the receiving
Builder.

Fixed rules:

- it must remain explicit;
- it must not be inferred away;
- absence of a stated protection is not proof that all surfaces are permitted;
- an unsupported restriction must not be invented and attributed to the user;
- unresolved protection scope remains UNKNOWN or HOLD-capable;
- a receiving Builder must be able to distinguish owned work from protected
  work.

Current Manual Bridge has a manually supplied Do Not Touch field and a Replay
atom. The generated repository-native handoff instead requires a separate Do
Not Continue Boundary and does not directly emit the exact Do Not Touch
heading. Existing handoff acceptance checks the continuation boundary, not the
Stage 3 Do Not Touch field.

The relationship between these existing fields remains design-open. This packet
does not equate them.

## 15. UNKNOWN Boundary

UNKNOWN is an explicit unresolved state.

It is not:

```text
an empty string
null
false
zero
N/A
a plausible assumption
an omitted field
PASS
permission
```

Fixed rules:

- user-stated uncertainty remains visible;
- ambiguity discovered during structuring remains visible;
- missing facts are not replaced by likely values;
- UNKNOWN does not silently become Objective, Completion Line, Do Not Touch,
  or authority;
- resolution requires evidence or explicit user clarification;
- incomplete boundaries remain HOLD-capable.

The repository contains strong adjacent behavior:

- handoff prose requires UNKNOWN rather than inference;
- Manual Bridge normalizes missing bounded values to UNKNOWN;
- required UNKNOWN boundary fields produce HOLD;
- Stage 2 artifacts carry an `unknowns` collection;
- Replay preserves UNKNOWN atoms unless an explicit Forward-only Delta resolves
  them;
- historical Stage 2 UNKNOWNs were preserved rather than retroactively
  upgraded.

The workflow incident checker is narrower: it accepts an optional unknowns list
but reports only presence and may still return `FIT_CHECK_READY`. That behavior
is not Stage 3 UNKNOWN preservation.

## 16. Execution-Authority Boundary

The structured intake grants no execution authority.

It does not authorize:

- starting a Builder;
- changing a file;
- accepting an approval request;
- creating or switching an implementation branch;
- merge or ready-for-review transition;
- publication, posting, or release;
- ownership transfer;
- Product PASS.

Identity also grants no authority. Original-request bytes, a hash, a model
identity, a role, a timestamp, a repository commit, a field label, or a
well-formed output cannot become permission.

The existing Companion makes this separation operational in adjacent paths:

- the Runner starts Codex only through `/api/run` and routes an unmatched exact
  file change through Allow once, saved repository access, or Deny;
- a verified saved exact repository/action/path decision may be reused without
  a new approval card, but remains an execution-side default rather than intake
  authority;
- Manual Bridge endpoints never call the Codex adapter or approval route;
- generated handoff state is `INSTRUCTION_ARTIFACT_ONLY`;
- handoff acceptance always reports authority not granted.

A later Guided Intake design must preserve that separation. This packet does
not select how.

## 17. Before / After Demonstration Requirement

The later product must support one visible small demonstration:

```text
Before:
one exact ambiguous Original Request

After:
Objective
Completion Line
Do Not Touch
UNKNOWN
```

The demonstration must keep the Original Request visible or independently
traceable. It must make unresolved facts visible and must not silently continue
into execution.

The example may show only the bounded transformation. It must not claim:

- generality;
- intent detection;
- mind reading;
- automatic correctness;
- burden reduction;
- universal safety.

No example is selected by this Scout. No marketing language, post, publication,
or posting authority is created.

## 18. Independent Evaluation Requirements

A later independent evaluator must determine whether the structured output:

1. preserved the original objective;
2. avoided added objectives;
3. made completion testable;
4. made protected surfaces explicit;
5. preserved unresolved facts;
6. avoided authority inflation.

Required evaluation evidence:

- exact identity of the Original Request;
- exact identity of the evaluated output;
- the complete visible Objective, Completion Line, Do Not Touch, and UNKNOWN
  values;
- provenance distinguishing original, generated, clarified, and corrected
  material;
- the product version or repository identity at which the output was produced;
- the evaluation conditions and any materials visible to the product;
- one finding for each of the six requirements;
- explicit evaluator UNKNOWNs and evidence gaps;
- counterevidence when a field cannot be traced to the Original Request;
- a result boundary stating that evaluation is not execution, merge,
  publication, release, generality, or correctness authority;
- independent evaluator identity and separation from the Builder or product
  output under evaluation.

The evaluation must be able to expose:

- a fluent but added objective;
- a Completion Line that sounds complete but is not observable;
- a protected surface that disappeared;
- a plausible assumption substituted for UNKNOWN;
- an intake that implies permission not present in the Original Request.

Existing Stage 2 structural Replay may establish that fixed atoms were
preserved across already-structured artifacts. It does not, by itself,
establish any of the six Guided Intake judgments.

The scoring implementation, thresholds, aggregation rule, and final evaluation
architecture are explicitly not designed here.

## 19. Existing Tests and Guards

### Workflow incident intake

- `tests/test_decision_os_intake.py:48-68` verifies deterministic, read-only,
  non-echoing output.
- `tests/test_decision_os_intake.py:70-113` covers missing and invalid required
  fields.
- `tests/test_decision_os_intake.py:115-139` proves unknown contents are
  structural-only and collapse to an input-presence marker.
- `tests/test_decision_os_intake.py:140-265` covers unsupported fields,
  malformed JSON, UTF-8, size, FIFO, parser-depth, and symlink guards.
- `tests/test_decision_os_intake_cli.py:110-253` covers shipped example,
  callable/module/bin parity, stable JSON/text, safe usage failure, non-echo,
  and sanitized internal failure.

### Incident-to-Audit chain

- `tests/test_decision_os_audit_delivery.py:52-165,487-593` covers required
  Unknowns, Exclusions, and Completion Line structure, including placeholder
  and UNKNOWN rejection.
- `tests/test_decision_os_audit_link.py:88-235` covers exact six-field
  continuity, bounded normalization, mismatch, and invalid source structure.
- `tests/test_decision_os_audit_gate.py:152-205` shows content-level incident
  unknowns can coexist with a structurally ready gate result.
- `tests/test_decision_os_audit_gate.py:238-268,300-514` covers Completion Line
  propagation, component-result aggregation, precedence, and safe failures.
- `tests/test_decision_os_audit_gate.py:515-595` covers intra-run intake-file
  identity and instability guards.
- `tests/test_decision_os_audit_gate_cli.py:149-178` fixes the exact
  human-review-only claim boundary.

### Execution approval and routing

- `tests/test_acceleration_engine.py:33-62` covers a first saved decision,
  verified save, and later verified reuse.
- `tests/test_acceleration_engine.py:64-101` covers Allow once, Deny, and
  same-Run behavior.
- `tests/test_acceleration_engine.py:129-185,230-262` covers pre-checkpoint
  override, post-checkpoint revocation, and supersession.
- `tests/test_acceleration_codex_adapter.py:611-683` proves one human selection
  across two fresh threads and a reused second action.
- `tests/test_acceleration_codex_adapter.py:694-726` covers later verified
  reuse.
- `tests/test_acceleration_codex_adapter.py:1047-1091` keeps an abnormal
  matched Run `matched-not-verified`.

### Companion and Manual Bridge

- `tests/test_companion_controller.py:309-340` fixes state persistence to the
  repository path only and rejects persisted prompt state.
- `tests/test_companion_controller.py:342-499` covers Runner receipts, exact
  approval choices, saved access, one active Run, and reconnect.
- `tests/test_companion_controller.py:501-575` proves Manual Bridge lifecycle
  and corruption remain separate from Runner execution and Runner Receipt.
- `tests/test_companion_server.py:148-405` covers bootstrap/session security,
  same-origin/CSRF, route limits, exact-byte import, script-safe rendering, and
  Manual Bridge UI fields.
- `tests/test_companion_server.py:406-575` covers one active Run, public state,
  sanitized corruption, and disconnected UI clearing.
- `tests/test_companion_manual_bridge.py:247-360` covers exact-byte identity,
  declared-hash mismatch, separate identity fields, and UNKNOWN preservation.
- `tests/test_companion_manual_bridge.py:362-533` covers evidence mismatch,
  role separation, authority inflation, and deterministic freezable handoff.
- `tests/test_companion_manual_bridge.py:535-658` covers private store,
  unchanged worktree, six-role manifest, and result separation.
- `tests/test_companion_manual_bridge.py:1288-1315` proves a missing required
  Completion Line heading prevents handoff freeze.
- `tests/test_companion_manual_bridge.py:1396-1553` covers all Replay fields and
  statuses, altered Objective, missing Completion Line, authority inflation,
  UNKNOWN, and the prohibition on fluent-prose shortcuts.

### Handoff acceptance

- `tests/test_decision_os_handoff_acceptance.py:166-198` routes active native
  handoff variants to semantic review.
- `tests/test_decision_os_handoff_acceptance.py:311-404` covers repository,
  target, branch, owner, action, responsibility, and routine-work relations.
- `tests/test_decision_os_handoff_acceptance.py:406-477` covers clean canonical
  closure and dirty, untracked, unmerged, detached, and branch mismatch guards.
- `tests/test_decision_os_handoff_acceptance.py:513-579` covers UNKNOWN in every
  native field, owner work, Completion Line, and state/gate guards.
- `tests/test_decision_os_handoff_acceptance.py:580-698` proves active prose
  never auto-accepts and polished label presence is not completion evidence.
- `tests/test_decision_os_handoff_acceptance.py:819-1159` covers read-only Git
  safety, unresolved operations, deterministic output, and unstable snapshots.
- `tests/test_decision_os_handoff_acceptance_cli.py:120-429` covers
  callable/text/JSON/module/bin parity, safe failures, forged active acceptance,
  and read-only CLI behavior.

No current test covers:

```text
one raw Original Request
→ Objective
→ Completion Line
→ Do Not Touch
→ UNKNOWN
```

No current test evaluates the six Stage 3 requirements against an Original
Request.

This Scout changes no tests. Full tests are not required for the one-file
evidence freeze. The existing Stage 2 closure independently records its prior
focused and full-suite results; those records are not upgraded into Stage 3
test evidence.

## 20. Protected Invariants

The Independent Pro Designer and all later actors must preserve at minimum:

```text
Shin remains Decision Owner.

The Original Request remains traceable.

A model-generated interpretation is not the Original Request.

Objective must not silently expand.

Completion Line must be testable or remain UNKNOWN.

Do Not Touch must not be inferred away.

UNKNOWN must not become an assumption.

Structured intake does not grant execution authority.

A receiving actor must know what it owns.

Routine implementation work must not be returned to Shin.

Stage 3 does not reopen Stage 1 or Stage 2 results.

Stage 3 does not start Stage 4 or Stage 5.
```

Existing repository invariants also remain:

- artifact, model, role, time, hash, and commit identity do not grant
  authority;
- handoff transfers current state and does not start new work;
- design, build, audit, and reusable-delta roles remain separate;
- Builder completion is not independent completion;
- historical UNKNOWNs are not retroactively upgraded;
- Golden means frozen comparison source, not correct, approved, certified,
  authorized, or PASS;
- Product, Protocol, Replay, and Research results remain independent;
- active responsibility-transfer semantics do not auto-pass from label
  presence;
- current and historical handoff material remain distinct.

## 21. Do Not Touch

This Scout must not and did not:

```text
choose the Guided Intake architecture
choose the final UI
write production code
write product tests
modify existing files
modify Companion
modify Manual Bridge
modify current handoff
modify current signal
modify roadmap
modify Stage 1 or Stage 2 records
modify AGENTS.md
create a Product PR
merge anything
draft or publish a post
authorize posting
select marketing language
start Framework Router work
start Stage 4
start Stage 5
```

Explicit deferrals remain:

```text
AGENTS.md Framework Router
Codex repository-search policy
Decision-OS custom Pro versus temporary Pro comparison
automatic model routing
automatic Pro invocation
Multi-Agent Roles
LoopKit Orchestra
public SaaS
pricing
publication
release
```

These are:

```text
DEFERRED / NOT LOST
```

The only changed path is:

```text
validation/guided_intake_v0_1_shared_evidence_packet.md
```

## 22. Known UNKNOWNs

### Product and transformation

- Final repository-native product surface:
  `UNKNOWN / DESIGN-OPEN`.
- Final UI or command:
  `UNKNOWN / DESIGN-OPEN`.
- Transformation method:
  `UNKNOWN / DESIGN-OPEN`.
- Whether clarification is interactive, one-pass, or separately confirmed:
  `UNKNOWN / DESIGN-OPEN`.
- Request size, encoding, normalization, and multiline rules:
  `UNKNOWN / DESIGN-OPEN`.
- Original Request storage, retention, privacy, and display policy:
  `UNKNOWN / DESIGN-OPEN`.
- Exact byte-traceability evidence:
  `UNKNOWN / DESIGN-OPEN`.
- Output representation and repository path:
  `UNKNOWN / DESIGN-OPEN`.
- UNKNOWN granularity and provenance representation:
  `UNKNOWN / DESIGN-OPEN`.
- Exact conditions that make an incomplete Stage 3 boundary HOLD:
  `UNKNOWN / DESIGN-OPEN`.

### Field judgment

- Observable rule separating faithful objective clarification from expansion:
  `UNKNOWN / DESIGN-OPEN`.
- General rule establishing Completion Line testability:
  `UNKNOWN / DESIGN-OPEN`.
- Evidence establishing sufficient Do Not Touch coverage without inventing
  restrictions:
  `UNKNOWN / DESIGN-OPEN`.
- Resolution rule for user-stated uncertainty versus product-discovered gaps:
  `UNKNOWN / DESIGN-OPEN`.
- Relationship between exact Do Not Touch and the existing handoff's Do Not
  Continue Boundary:
  `UNKNOWN / DESIGN-OPEN`.
- Relationship between a structured intake and current Manual Bridge boundary:
  `UNKNOWN / DESIGN-OPEN`.
- Relationship between a structured intake and direct Companion execution:
  `UNKNOWN / DESIGN-OPEN`.

### Demonstration and evaluation

- Exact ambiguous demonstration request:
  `UNKNOWN / NOT SELECTED`.
- Independent evaluator identity:
  `UNKNOWN / NOT ASSIGNED`.
- Evaluation artifact format:
  `UNKNOWN / DESIGN-OPEN`.
- Scoring and threshold implementation:
  `UNKNOWN / EXPLICITLY DEFERRED`.
- Whether the product reduces burden:
  `UNKNOWN / NO CLAIM`.
- Generality, third-party reproduction, intent detection, mind reading,
  automatic correctness, and universal safety:
  `UNKNOWN / NOT CLAIMED`.

### Preserved prior-stage UNKNOWNs

The roadmap's research UNKNOWNs remain unresolved, including sustained Pro
design advantage, reliable-completion cost, token reduction, value for
delegation-first users, third-party retention, and external attention.

Stage 2's historical runtime and hash-recomputation UNKNOWNs remain preserved.
This Scout does not rewrite them.

## 23. Evidence Gaps

The canonical As-of repository contains no:

- Guided Intake module;
- Guided Intake command;
- Guided Intake API route;
- Guided Intake UI card or view;
- raw Original Request schema field;
- Original Request hash or byte identity;
- Original Request artifact role;
- linkage from one request to Objective, Completion Line, Do Not Touch, and
  UNKNOWN;
- transformation fixture family;
- before/after Guided Intake example;
- Objective-expansion detector or evaluation;
- Completion Line testability evaluation;
- Do Not Touch completeness evaluation;
- Stage 3 unresolved-fact provenance evaluation;
- Stage 3 authority-inflation evaluation;
- Guided Intake Receipt;
- Guided Intake acceptance run;
- independent Guided Intake evaluation record.

Adjacent gaps relevant to later design:

- Companion Runner text is trimmed and not persisted;
- workflow incident intake non-echo is privacy behavior, not Original Request
  traceability;
- workflow incident unknown contents are collapsed to a presence marker;
- Audit-link exact continuity covers only six incident fields and contains no
  Original Request or four-field Stage 3 identity;
- Audit result aggregation suppresses component content and is not a Guided
  Intake evidence bundle;
- Audit Completion Line shape validation is not a testability evaluation, and
  its UNKNOWN rejection cannot substitute for Stage 3 UNKNOWN/HOLD behavior;
- a verified execution default may authorize another diff at the same exact
  repository/action/path without a renewed approval card, so it cannot be
  treated as approval of intake meaning;
- Manual Bridge accepts already-structured fields rather than deriving them;
- Manual Bridge required-boundary checks establish presence, not semantic
  correctness;
- exact Do Not Touch is not a required generated-handoff heading;
- existing handoff and handoff acceptance omit Original Request and Objective;
- Stage 2 Replay compares structured atoms rather than request meaning;
- direct Runner execution is independent of Manual Bridge completeness;
- handoff acceptance checks a stable local snapshot and explicitly does not
  establish remote freshness.

These are evidence gaps, not permission to select architecture or invent
missing behavior.

## 24. Design-Open Questions

The Independent Pro Designer must resolve or preserve as UNKNOWN:

1. Which repository-native surface receives the one raw request?
2. What evidence makes Original Request preservation verbatim or
   byte-traceable?
3. How is generated interpretation visibly distinguished from original text?
4. What observable rule separates faithful Objective recovery from silent
   expansion?
5. What makes a Completion Line testable rather than merely nonempty or
   polished?
6. How is Do Not Touch made explicit without inventing restrictions or
   inferring protections away?
7. How are user-stated unknowns distinguished from gaps discovered during
   structuring?
8. What evidence is required before an UNKNOWN can be resolved?
9. What exact incomplete-boundary conditions remain HOLD?
10. How does the fixed fourth primary field UNKNOWN relate to per-field
    uncertainty without adding a new primary ontology?
11. How does the roadmap's `Evidence Needed` remain subordinate to the fixed
    four-primary-field contract?
12. How, if at all, does Guided Intake relate to the current workflow incident
    checker?
13. How, if at all, does Guided Intake relate to the Companion Runner without
    triggering execution?
14. How, if at all, does Guided Intake relate to Manual Bridge, generated
    handoff, and handoff acceptance?
15. How does exact Objective and Do Not Touch reach a receiving Builder when
    current handoff headings do not require them?
16. What is authoritative if a structured intake, Manual Bridge boundary, and
    imported design disagree?
17. What request-size, encoding, normalization, and privacy boundaries preserve
    traceability?
18. What exact evidence bundle supports independent evaluation of all six
    required judgments?
19. What one small example can be shown without making generality, intent,
    correctness, burden, or safety claims?
20. What output claim boundary makes non-authority visible to the user and the
    receiving actor?

These questions do not prefer CLI, Companion, Manual Bridge, a new module, a
model, a parser, a schema, or any other architecture.

## 25. Exact Evidence Anchors

All blob identities below are Git blobs at exact As-of commit
`d785dbd9fe3ec3c41bbe0771080ad1d0a47f9d48`.

### Canonical blob identities

| Path | Git blob |
|---|---|
| `decision_os/intake.py` | `184c653b5c9c5c3c03b46e2d79e5722344e1d739` |
| `decision_os/intake_text.py` | `d87145fb4f1e439670015e86334ba8c605e5a74c` |
| `decision_os/cli.py` | `983ddea52c7f22c694a40f44d27db2f4785dafc5` |
| `decision_os/audit_delivery.py` | `26945ead1628e9903d663059bc24288111f6537b` |
| `decision_os/audit_link.py` | `cd1b4387820e8e4a795ffdf49f7e01431a5854b5` |
| `decision_os/audit_gate.py` | `23b5d2ec65d02c39ffeb77ae527395e7234cf643` |
| `decision_os/acceleration/model.py` | `d0df6c7a19e8d330ec9ccd7f81b2a73a9b2c1fb9` |
| `decision_os/acceleration/store.py` | `05121ae1aeafa034cf6a820a3b83e71c08bc100f` |
| `decision_os/acceleration/engine.py` | `286b681f5e9b2140adc0aced33984731651d2aa1` |
| `decision_os/acceleration/codex_adapter.py` | `372241f30c410ec4edc15826130c679f763b2442` |
| `decision_os/handoff_acceptance.py` | `132621dbe305588ddc5f5868a517814bb37a3891` |
| `decision_os/companion/controller.py` | `3793dba9226848dab04635c7997beca8a84ffdd7` |
| `decision_os/companion/server.py` | `ac274065a93a2de003d605c9e44b25ef2b2aff1f` |
| `decision_os/companion/static/index.html` | `151a473ce3df8e316a9b236f661c094b4479e611` |
| `decision_os/companion/static/app.js` | `24e179f3b33a7a3f3aa70db0902e06bc989ab926` |
| `decision_os/companion/manual_bridge.py` | `001484a350e5355a32b8ffb864c6b056b69704d4` |
| `docs/handoff_command.md` | `7ce12bf250cd486844c568777312064491340112` |
| `docs/companion_manual_bridge_v0_1.md` | `16fd352e9e37e94c8d30698245f81e16ebf533d3` |
| `docs/workflow_incident_intake_checker_v0_1.md` | `6fb26bb9eb02723a052b0b352442b5f3a4c7ee18` |
| `docs/audit_delivery_validator_v0_1.md` | `b3aff56f34324e495c3b9eb162d81f417876ecd8` |
| `docs/audit_case_link_checker_v0_1.md` | `929bb2fb4a390a391fe58fb0aea3f67931017840` |
| `docs/audit_gate_orchestrator_v0_1.md` | `1e98c579a466c8bf80d9c26b392e4b1ed18f13eb` |
| `docs/verified_save_claude_mvp_v0_1.md` | `c7775fbe4cb6abe01b6d7d92a889fc4fc201e6c1` |
| `field_notes/pro_manual_protocol_v0_1.md` | `77e180a4f27298fd066c418b6ea4ccdcb9f40b45` |
| `field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md` | `c4373d0ec121aace1cc8213c907aeb45e85d40f3` |
| `validation/companion_manual_bridge_v0_1_stage_2_closure.md` | `fe4bcbe30b65008aa7f2f98f81ff0d51f2de1100` |
| `validation/decision_os_companion_acceptance_run_001.md` | `ffb7a1e09c08ff2bf03a4a284608e35e86a4b6bb` |
| `tests/test_decision_os_intake.py` | `3d1b4ec40c0e0ef6891c764f192079307b86521f` |
| `tests/test_decision_os_intake_cli.py` | `6bad644bf309c6ad6e37462d6b0a8a782babb856` |
| `tests/test_decision_os_audit_delivery.py` | `016ad20d445b34e3c5fdb0ef5380ff126af568e9` |
| `tests/test_decision_os_audit_link.py` | `35de943a68da2dcc9ddf858eabbc1d84d54cc499` |
| `tests/test_decision_os_audit_gate.py` | `d3c2b7721ea9f40cb8c0e6c9d01a5e4d40e56662` |
| `tests/test_decision_os_audit_gate_cli.py` | `fbbebe2bfb5d8fe6223f656da72f9096ef156dd7` |
| `tests/test_acceleration_engine.py` | `42764f7322553a4c9d4d4beb5cdc944606ad8330` |
| `tests/test_acceleration_codex_adapter.py` | `1d31ed46a1628046723048ee0a141204ba29d3cd` |
| `tests/test_companion_controller.py` | `5c4e045c31a8c86f58105416a1dabfc969b5c5c5` |
| `tests/test_companion_server.py` | `457575512cf7e954ec1e3e9bd4e14f490fb16eca` |
| `tests/test_companion_manual_bridge.py` | `2702141abe0f1e0712ae5d634c8f7927aa568ace` |
| `tests/test_decision_os_handoff_acceptance.py` | `5d676c53856504e22e57fb304b003a5ebc2a1af8` |
| `tests/test_decision_os_handoff_acceptance_cli.py` | `29ea504a9bc26f3ebb4d7eb46bb6cc2ae46ba852` |

### Intake and CLI anchors

- `decision_os/intake.py:16-65` — incident schema, required and optional fields,
  field order, and accepted-field allowlist.
- `decision_os/intake.py:67-89` — claim and minimum-next-step boundaries.
- `decision_os/intake.py:122-164` — stable result, non-echo, and UNKNOWN output.
- `decision_os/intake.py:167-276` — safe regular-file snapshot and strict JSON
  parsing.
- `decision_os/intake.py:279-363` — string/list shape checks, unsupported
  fields, and unknown-presence collapse.
- `decision_os/intake.py:366-399` — INCOMPLETE, INVALID, and FIT_CHECK_READY
  routing.
- `decision_os/intake_text.py:14-35` — current incident text field family.
- `decision_os/intake_text.py:91-123` — structural-only text rendering.
- `decision_os/cli.py:52-55` — packet-path intake usage.
- `decision_os/cli.py:214-258` — intake argument parsing and validation call.
- `decision_os/cli.py:631-650` — handoff and intake command dispatch.
- `docs/workflow_incident_intake_checker_v0_1.md:3-9` — bounded incident purpose
  and non-goals.
- `docs/workflow_incident_intake_checker_v0_1.md:98-140` — current schema and
  optional unknowns.
- `docs/workflow_incident_intake_checker_v0_1.md:143-188` — result and claim
  boundary.

### Incident-to-Audit anchors

- `decision_os/audit_delivery.py:25-38` — required Audit sections including
  Unknowns, Exclusions, and Completion Line.
- `decision_os/audit_delivery.py:84-134` — bounded result fields and claims
  excluded.
- `decision_os/audit_delivery.py:747-781` — structural bullets and visible
  non-placeholder, non-UNKNOWN Completion Line.
- `decision_os/audit_link.py:24-74` — six incident continuity fields and
  continuity-only claim boundary.
- `decision_os/audit_link.py:170-225` — bounded normalization and full-source
  validation.
- `decision_os/audit_link.py:269-334` — field comparison after bounded
  normalization and result.
- `decision_os/audit_gate.py:32-63` — human-review-only result boundary.
- `decision_os/audit_gate.py:432-494` — file identity guard and bounded
  component summaries without content.
- `decision_os/audit_gate.py:526-779` — aggregate contract, precedence, and
  result classification.
- `decision_os/audit_gate.py:814-935` — intake, delivery, and continuity
  orchestration with stable source identity.
- `docs/audit_delivery_validator_v0_1.md:70-134` — delivery fields, Unknowns,
  Exclusions, Completion Line, and structural claim boundary.
- `docs/audit_case_link_checker_v0_1.md:32-108` — exact six-field mapping,
  normalization, and continuity-only result.
- `docs/audit_gate_orchestrator_v0_1.md:11-23` — not a V13 authority gate or
  delivery acceptance.
- `docs/audit_gate_orchestrator_v0_1.md:43-101` — sequence, component
  unknowns, aggregate result, and file identity.
- `docs/audit_gate_orchestrator_v0_1.md:160-206` — non-reproduction of content,
  human-review boundary, and synthetic evidence exclusions.

### Acceleration and execution anchors

- `decision_os/acceleration/model.py:207-301` — exact bounded scope and
  repository/action/path decision identity.
- `decision_os/acceleration/store.py:103-227` — canonical append-only,
  hash-chained local events.
- `decision_os/acceleration/store.py:311-379` — active-default reconstruction
  and deactivation.
- `decision_os/acceleration/engine.py:88-146` — exact default matching,
  same-Run separation, and skipped repeated interrupt.
- `decision_os/acceleration/engine.py:148-193` — Allow once, repository
  default, and Deny decisions.
- `decision_os/acceleration/engine.py:195-264` — terminal-checkpoint promotion
  to verified save or reuse.
- `decision_os/acceleration/engine.py:266-397` — revocation, supersession, and
  bounded Receipt facts.
- `decision_os/acceleration/codex_adapter.py:563-646` — fresh bounded thread
  and verified runtime identity.
- `decision_os/acceleration/codex_adapter.py:652-757` — prompt-to-execution
  routing and exact human decision presentation.
- `decision_os/acceleration/codex_adapter.py:834-879` — single-file
  CREATE/MODIFY mapping and unsupported mutation guards.
- `decision_os/acceleration/codex_adapter.py:1124-1171` — completion binding to
  the typed adapter-approved change.
- `decision_os/acceleration/codex_adapter.py:1278-1376` — full fresh-Run
  lifecycle and terminal classification.
- `docs/verified_save_claude_mvp_v0_1.md:72-90` — exact saved rule contents.
- `docs/verified_save_claude_mvp_v0_1.md:180-195` — prompt and conversation
  content excluded from local state and outward Receipt.
- `docs/verified_save_claude_mvp_v0_1.md:268-305` — Receipt and productivity
  claim boundaries.

### Companion and Manual Bridge anchors

- `decision_os/companion/controller.py:174-232` — Run state and repository-only
  persistent state.
- `decision_os/companion/controller.py:335-420` — Manual Bridge controller
  operations.
- `decision_os/companion/controller.py:421-524` — direct task validation,
  trimming, thread start, adapter execution, and exact approval route.
- `decision_os/companion/controller.py:628-676` — Runner Receipt projection.
- `decision_os/companion/controller.py:728-795` — separate Runner and Manual
  Bridge public snapshot.
- `decision_os/companion/server.py:35-70` — request limits, static allowlist,
  private tokens, and loopback bind.
- `decision_os/companion/server.py:255-305` — bounded JSON input and direct Run
  endpoint.
- `decision_os/companion/server.py:318-453` — Manual Bridge session, import,
  handoff, Receipt, manifest, Replay, and observation routes.
- `decision_os/companion/static/index.html:39-58` — direct bounded-task input and
  Run button.
- `decision_os/companion/static/index.html:124-166` — Manual Bridge authority
  notice and manually authored boundary fields.
- `decision_os/companion/static/index.html:283-308` — independent results,
  UNKNOWN burden, and Golden claim boundary.
- `decision_os/companion/static/app.js:606-618` — direct task POST to `/api/run`.
- `decision_os/companion/static/app.js:676-701` — blank-to-UNKNOWN structured
  boundary POST.
- `decision_os/companion/static/app.js:769-783` — handoff and Receipt generation
  and freeze controls.
- `decision_os/companion/manual_bridge.py:1-6` — Bridge never starts Codex or
  grants authority.
- `decision_os/companion/manual_bridge.py:90-150` — Replay and handoff field
  families.
- `decision_os/companion/manual_bridge.py:163-198` — role authorities and
  required structured boundary.
- `decision_os/companion/manual_bridge.py:1130-1249` — evidence matching,
  UNKNOWN completeness, HOLD, and session fixation.
- `decision_os/companion/manual_bridge.py:1318-1352` — complete-boundary Copy for
  Pro with Objective, Completion Line, Do Not Touch, and non-authority.
- `decision_os/companion/manual_bridge.py:1939-2101` — identity-bound,
  instruction-only Execution Handoff generation.
- `decision_os/companion/manual_bridge.py:2180-2232` — Bridge Receipt identity,
  claim boundary, and unknowns.
- `decision_os/companion/manual_bridge.py:2324-2473` — fifteen-field structural
  Replay baseline including Objective, Completion Line, Do Not Touch, and
  UNKNOWNs.
- `decision_os/companion/manual_bridge.py:2755-2820` — UNKNOWN and
  authority-inflation comparison guards.
- `decision_os/companion/manual_bridge.py:2842-3030` — structural Replay result
  statuses and result independence.
- `docs/companion_manual_bridge_v0_1.md:5-25` — Bridge purpose, chain, and
  non-authority.
- `docs/companion_manual_bridge_v0_1.md:27-63` — private state and worktree
  no-write boundary.
- `docs/companion_manual_bridge_v0_1.md:195-246` — role/authority separation.
- `docs/companion_manual_bridge_v0_1.md:296-345` — complete structured boundary,
  lifecycle, and routes that do not call Codex.
- `docs/companion_manual_bridge_v0_1.md:347-379` — instruction-only handoff and
  separate Builder-authority HOLD.
- `docs/companion_manual_bridge_v0_1.md:430-519` — Replay fields, statuses,
  UNKNOWN, and trace-only Framework fields.
- `docs/companion_manual_bridge_v0_1.md:540-554` — explicit Guided Intake,
  automatic Builder, Stage 3–5, and public-surface non-goals.

### Handoff and authority anchors

- `docs/handoff_command.md:3-8` — state transfer only; no new work or judgment.
- `docs/handoff_command.md:10-24` — thirteen required handoff fields.
- `docs/handoff_command.md:26-39` — UNKNOWN, ownership, routine work,
  no-authority, and Completion Line rules.
- `decision_os/handoff_acceptance.py:23-103` — result, issue, and canonical
  field registries.
- `decision_os/handoff_acceptance.py:338-385` — approval, authority, writes, and
  remote freshness fixed false/not checked.
- `decision_os/handoff_acceptance.py:1611-1642` — unresolved and ambiguous field
  detection.
- `decision_os/handoff_acceptance.py:1748-1775` — required-field and UNKNOWN
  checks.
- `decision_os/handoff_acceptance.py:1880-1991` — active semantic review and
  bounded closed-state acceptance.
- `decision_os/handoff_acceptance.py:2001-2087` — stable local snapshot
  assessment and reread.
- `field_notes/pro_manual_protocol_v0_1.md:11-34` — fixed task boundary,
  incomplete-boundary HOLD, and identity non-authority.
- `field_notes/pro_manual_protocol_v0_1.md:35-64` — five-stage role chain and
  bounded receipts.
- `field_notes/pro_manual_protocol_v0_1.md:100-120` — Shin's Seat, execution-side
  routine work, and Stage 1 boundary.
- `field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md:33-42` —
  Acceleration Surface sequence.
- `field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md:86-157` — separate
  Stages 1–5 and documented Guided Intake field family.
- `field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md:175-212` —
  preserved research UNKNOWNs and roadmap HOLD.

### Prior acceptance and closure anchors

- `validation/companion_manual_bridge_v0_1_stage_2_closure.md:35-60` —
  independent Product, Protocol, Replay, and Research results.
- `validation/companion_manual_bridge_v0_1_stage_2_closure.md:85-88` —
  historical UNKNOWNs remain historical.
- `validation/companion_manual_bridge_v0_1_stage_2_closure.md:120-161` —
  six-role Golden and manifest identity trace.
- `validation/companion_manual_bridge_v0_1_stage_2_closure.md:187-215` —
  Objective, Completion Line, Do Not Touch, authority, and UNKNOWN structural
  preservation.
- `validation/companion_manual_bridge_v0_1_stage_2_closure.md:217-242` — prior
  Stage 2 validation evidence.
- `validation/companion_manual_bridge_v0_1_stage_2_closure.md:244-284` — one-run
  claim boundary and no merge, posting, release, or Stage 3–5 authority.
- `validation/decision_os_companion_acceptance_run_001.md:57-90` — accepted
  private one-task Runner surface.
- `validation/decision_os_companion_acceptance_run_001.md:91-150` — exact local
  Run and event-chain evidence.
- `validation/decision_os_companion_acceptance_run_001.md:171-208` — Receipt,
  estimates, UNKNOWN tokens, and product claim boundary.
- `validation/decision_os_companion_acceptance_run_001.md:217-249` — prior
  Companion validation and unchanged product surface.

### Test anchors

- `tests/test_decision_os_intake.py:48-265` — incident structure, UNKNOWN
  presence, privacy, safety, and read-only behavior.
- `tests/test_decision_os_intake_cli.py:92-253` — incident CLI separation,
  parity, deterministic output, and safe failures.
- `tests/test_decision_os_audit_delivery.py:52-165,487-593` — Audit Unknowns,
  Exclusions, and Completion Line structural guards.
- `tests/test_decision_os_audit_link.py:88-235` — six-field intake-to-Audit
  continuity and safe failures.
- `tests/test_decision_os_audit_gate.py:152-268,300-477,515-595` — content
  unknowns, Completion Line propagation, aggregate result, precedence, and
  file-identity guards.
- `tests/test_decision_os_audit_gate_cli.py:149-178` — exact aggregate Receipt
  and human-review claim boundary.
- `tests/test_acceleration_engine.py:33-185,230-262` — exact decisions, saved
  reuse, checkpoints, revocation, and supersession.
- `tests/test_acceleration_codex_adapter.py:611-726,1047-1091` — one human
  choice across fresh threads, later reuse, and abnormal-terminal non-
  verification.
- `tests/test_companion_controller.py:283-575` — repository state, Runner,
  approval, Receipt, Bridge separation, and corruption isolation.
- `tests/test_companion_server.py:148-575` — localhost security, exact routes,
  DOM, one Run, and disconnect behavior.
- `tests/test_companion_manual_bridge.py:247-533` — byte identity, UNKNOWN,
  role, authority, and handoff.
- `tests/test_companion_manual_bridge.py:535-658` — no worktree mutation,
  manifest, and independent results.
- `tests/test_companion_manual_bridge.py:1288-1315` — missing Completion Line
  freeze guard.
- `tests/test_companion_manual_bridge.py:1396-1553` — complete structural Replay
  status coverage and no prose shortcut.
- `tests/test_decision_os_handoff_acceptance.py:166-698` — active/closed,
  repository, owner, action, UNKNOWN, completion, and semantic-review guards.
- `tests/test_decision_os_handoff_acceptance.py:819-1159` — read-only Git and
  snapshot stability guards.
- `tests/test_decision_os_handoff_acceptance_cli.py:120-429` — CLI parity,
  trusted inputs, forged acceptance rejection, and read-only behavior.

Bounded repository-wide search found the exact phrase `Guided Intake` only in
the provisional roadmap, Stage 2 exclusion records, and an earlier Stage 2
design prohibition. It found no `Original Request` field in canonical product,
documentation, validation, or related tests before this packet.

## 26. Exit Gate

Successful Scout exit:

```text
READY FOR INDEPENDENT PRO DESIGN
```

This exit applies only when:

- canonical local main, origin/main, and GitHub main remain the exact required
  As-of commit;
- this packet is the only changed file;
- no existing file, code, or test is modified;
- `git diff --check` passes;
- the packet is committed once with
  `validation: freeze Guided Intake evidence`;
- the branch `codex/v13-guided-intake-evidence` is pushed;
- local and remote branch heads match;
- main remains unchanged;
- the final worktree is clean;
- no PR, design, implementation, merge, publication, posting, or Stage 4–5
  action occurs.

If repository evidence is insufficient:

```text
HOLD — GUIDED INTAKE EVIDENCE INSUFFICIENT
```

If repository identity differs:

```text
HOLD — AS-OF REPOSITORY IDENTITY MISMATCH
```

After successful external fixation, the sole next owner is:

```text
Independent Pro Designer
```
