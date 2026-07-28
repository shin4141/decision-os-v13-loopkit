# Companion Manual Bridge v0.1 — Independent Pro Design Packet

> Bounded design artifact for V13-CMB-001 / V13-PMR-002.
> This artifact is a design input. It grants no implementation, merge, publication, or release authority.

## 1. Design Identity

```text
Target layer:
V13 — Compound Loop / Stage 2 Companion Manual Bridge

Task ID:
V13-CMB-001

Protocol Run:
V13-PMR-002

Target:
Companion Manual Bridge v0.1

Current chat ownership:
Independent Pro Design only

Current Gate:
GO UNDER CAP — PRO DESIGN ONLY

Completion Line:
Produce one bounded, implementable, independently auditable Pro Design Packet;
seal it without repository writes, implementation, testing, PR, merge, or authority grant.

Decision Owner:
Shin

Design role:
Independent Pro Designer

Model identity:
GPT-5.6 Thinking — self-declared for this artifact; not independently verified

Role identity:
GPT 13-18 / Independent Pro Designer

Design time anchor:
2026-07-28T22:00:00+09:00

Product As-of commit:
63eb260a94595298e2b07b476f7f9d8572c9ef09

Frozen Evidence Packet commit:
970ae5e24e59dada54e1b829229360d9945a0910

Frozen Evidence Packet path:
validation/companion_manual_bridge_v0_1_shared_evidence_packet.md

Frozen Evidence Packet blob SHA:
92f9f69f18db052b421fa5fa7f233ce77f5a42b8

Frozen Evidence Packet SHA-256:
847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab

Implementation authority:
NONE

Required next actor after Shin accepts this design:
Fresh SOL / coding-agent Builder

Reserved Codex number:
13-25
```

The design artifact itself must not embed its own final content hash because that value is self-referential. The Bridge import event must fix the exact imported bytes, SHA-256, import event identity, source label, and import timestamp externally.

The following structured block is normative for importing this Pro Design artifact. `artifact_content_hash` is intentionally fixed only at import.

```json
{
  "schema": "decision-os-companion-manual-bridge-record-v0.1",
  "task_id": "V13-CMB-001",
  "protocol_run_id": "V13-PMR-002",
  "artifact_role": "PRO_DESIGN",
  "source_label": "GPT 13-18 Independent Pro Design Packet",
  "model_identity": {
    "value": "GPT-5.6 Thinking",
    "basis": "SELF_DECLARED",
    "verification_state": "UNVERIFIED"
  },
  "role_identity": "Independent Pro Designer",
  "artifact_authored_at": "2026-07-28T22:00:00+09:00",
  "as_of_commit": "63eb260a94595298e2b07b476f7f9d8572c9ef09",
  "evidence_packet_commit": "970ae5e24e59dada54e1b829229360d9945a0910",
  "evidence_packet_blob_sha": "92f9f69f18db052b421fa5fa7f233ce77f5a42b8",
  "evidence_packet_sha256": "847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab",
  "artifact_content_hash": "TO_BE_FIXED_AT_IMPORT",
  "authority_state": "DESIGN_ONLY_NO_EXECUTION_AUTHORITY",
  "required_next_actor": "Fresh SOL / coding-agent Builder",
  "result_claim": "DESIGN_READY_FOR_BUILD"
}
```

Missing Closure remains visible:

* the design has not been accepted by Shin;
* the Builder has not received separate execution authority;
* the Bridge has not been implemented;
* no Build Receipt exists;
* no independent Pro Audit exists;
* no Reusable Delta Record exists;
* the Golden Artifact Set is incomplete;
* Protocol, Product, and Replay results remain independent and unresolved.

## 2. Design Judgment

**Design judgment: DESIGN READY FOR BUILD.**

The smallest viable Bridge is one additional **Manual Bridge panel** inside the existing private local Companion, backed by a separate repository-local Bridge store and deterministic artifact contracts.

The v0.1 design consists of five bounded capabilities:

1. generate a deterministic `Copy for Pro` packet;
2. import exact artifact bytes under an explicitly selected artifact role;
3. fix artifact identity without granting authority;
4. generate a repository-native execution handoff and a separate Bridge Receipt;
5. freeze a Golden Artifact Set and perform field-by-field structural Replay.

The design deliberately does **not** add model invocation, automatic routing, orchestration, public hosting, general-purpose workflow management, or automatic execution. It extends the accepted local Companion surface rather than replacing it.

The key architectural judgment is to keep the Bridge state and Bridge Receipt **separate** from the existing Acceleration event store and Verified Save/Reuse Receipt. The current Receipt proves a different behavior: exact access reuse after a normal terminal checkpoint. Conflating it with Pro artifact identity, findings, actual burden observations, Golden fixation, or Replay would create false evidence and false completion.

## 3. Problem Definition

The existing Companion already has a bounded operational core:

* one local repository selection;
* one bounded task input;
* one fresh fixed Codex runtime;
* exact file create/modify approval;
* hash-chained local event state;
* Verified Save/Reuse Receipt;
* repository-native handoff acceptance.

Stage 2 lacks the bridge between the manual Pro workflow and that existing execution surface. Specifically, the current product does not provide:

* `Copy for Pro`;
* Pro Design or Pro Audit import;
* exact imported-artifact byte fixation;
* imported model, role, time, and As-of fixation;
* Pro-artifact-to-execution-handoff generation;
* finding/cost/Reusable Delta Receipt;
* Golden Artifact Set fixation;
* Golden Replay;
* separate Protocol/Product/Replay results.

The operational failure to prevent is not merely “missing convenience.” It is a joint failure in which fluent prose is treated as sufficient continuity while one or more of the following are lost:

* exact artifact identity;
* selected artifact role;
* model and role distinction;
* time and As-of distinction;
* authority boundary;
* Completion Line;
* UNKNOWNs;
* required next actor;
* cost and reusable-delta traceability.

The Bridge must therefore convert a manual prose-transfer chain into an auditable artifact chain **without converting the imported prose into operational authority**.

## 4. Protected Invariants

The following invariants are non-negotiable:

1. Shin remains Decision Owner.
2. Artifact identity does not grant authority.
3. Model identity does not grant authority.
4. Importing a Pro artifact does not authorize execution.
5. Pro Design and Pro Audit remain distinct roles and distinct import events.
6. Builder completion is not independent completion.
7. Routine execution and cleanup are not returned to Shin when the Builder or execution agent can close them.
8. As-of commit, artifact hash, model identity, role identity, and time anchor remain separately visible.
9. `UNKNOWN` is preserved and is never converted into PASS.
10. Golden Replay is not self-certification.
11. The existing exact file-change approval remains the only Companion-native permission for an actual supported file mutation.
12. The existing Verified Save/Reuse Receipt retains its current meaning and claim boundary.
13. Current and historical handoff records are not silently conflated.
14. A generated Execution Handoff is an instruction artifact, not an authority grant.
15. A Reusable Delta is a future-use candidate, not an automatic Canon update.
16. One stage’s completion cannot silently complete another stage.
17. No imported artifact can create merge, publication, release, transfer-approval, or unrelated-file authority.
18. Missing required fields remain visible as `MISSING` or `UNKNOWN`, not fluent substitutes.
19. Product PASS cannot be inferred from Protocol PASS or Replay PASS.
20. Design choices made in this packet are Forward-only design decisions, not claims that the current repository already implements them.

## 5. Minimal User Workflow

The v0.1 workflow uses one selected repository and one Manual Bridge session.

### Step 1 — Open a bounded Bridge session

The user selects the repository through the existing repository picker and starts a Manual Bridge session with:

* Task ID;
* Protocol Run ID;
* objective;
* Completion Line;
* Do Not Touch;
* Current Gate;
* Authority Boundary;
* As-of commit;
* required next actor;
* frozen Evidence Packet identity.

The Bridge does not infer missing values. Missing required values keep the session at `HOLD — INCOMPLETE BOUNDARY`.

### Step 2 — Copy for Pro

The user presses `Copy for Pro`.

The Bridge generates deterministic Markdown containing:

* the fixed task boundary;
* Evidence Packet identity;
* required artifact role;
* required output fields;
* authority prohibitions;
* UNKNOWN rule;
* final seal requirements.

Copying creates a local event. It does not call a model.

### Step 3 — Import Pro Design

The user explicitly selects `PRO_DESIGN`, then imports either:

* a file as exact bytes; or
* pasted UTF-8 text as exact captured payload bytes.

The Bridge computes the payload SHA-256 before parsing, fixes the import event ID and time, records the selected role, and stores the immutable bytes.

The artifact’s own declared role cannot override the user-selected role. A mismatch produces `HOLD — ROLE MISMATCH`.

### Step 4 — Generate Execution Handoff

After a valid Pro Design import, the user presses `Generate Execution Handoff`.

The Bridge generates repository-native Markdown from:

* frozen session fields;
* the structured Pro Design record;
* preserved UNKNOWNs.

It does not infer required fields from free prose. The generated handoff is instruction-only and defaults to:

`Current Gate: HOLD — SEPARATE BUILDER AUTHORITY REQUIRED`

The handoff may state a **requested** bounded build gate, but the Bridge does not activate it.

### Step 5 — Fresh Builder execution under separate authority

Shin transmits the handoff and separately authorizes the fresh Builder. The Builder performs only the authorized implementation surface and produces a Build Receipt.

The Bridge is not the execution engine for this step.

### Step 6 — Import Build Receipt

The user selects `BUILD_RECEIPT` and imports the exact Build Receipt bytes. The Bridge fixes identity and preserves:

* implementation commit and branch;
* exact changed paths;
* tests;
* deviations;
* repairs;
* cost observations;
* remaining UNKNOWNs;
* builder authority boundary.

### Step 7 — Import independent Pro Audit

The user selects `PRO_AUDIT` and imports the independent audit artifact as a distinct event. The Bridge rejects any attempt to derive audit completion from the Build Receipt.

### Step 8 — Import Reusable Delta Record

The user selects `REUSABLE_DELTA_RECORD` and imports the exact record. A delta remains a candidate until its own acceptance boundary is met.

### Step 9 — Generate Bridge Receipt and Golden manifest

The Bridge generates:

* Finding / Cost / Reusable Delta Receipt;
* Golden Artifact Set manifest.

Missing artifacts remain explicit manifest entries.

### Step 10 — Replay

Once the Golden manifest is eligible, the same fixed materials can be processed through the implemented Bridge in Replay mode. The Bridge compares canonical structural fields field by field, not free-prose wording.

## 6. Proposed Architecture

The architecture adds one bounded subsystem to the current Companion.

```text
Existing authenticated local Companion
└── Manual Bridge panel
    ├── BridgeSessionController
    ├── Artifact Import + Identity Fixation
    ├── Deterministic Output Generators
    ├── Separate ManualBridgeStore
    └── Structural Replay Evaluator
```

### A. Manual Bridge panel

The panel is an additional section in the existing local browser UI. It contains:

* session identity;
* frozen task-boundary fields;
* `Copy for Pro`;
* artifact-role selector;
* file import and paste import;
* imported-artifact identity list;
* generation controls;
* Golden manifest status;
* Replay result;
* burden observation status.

The panel does not replace the existing task runner, result, runtime identity, approval card, or Verified Save Receipt.

### B. BridgeSessionController

A bounded controller object owns one Manual Bridge session for the currently selected repository. It enforces lifecycle order, required fields, and explicit user actions.

It does not start Codex, route models, grant authority, or mutate repository files.

### C. ManualBridgeStore

The Bridge uses a separate store rooted at:

```text
.git/decision-os/manual-bridge/v0.1/
```

Proposed local layout:

```text
events.jsonl
artifacts/sha256/<artifact_sha256>.bin
imports/<import_event_id>.json
sessions/<session_id>/session.json
outputs/<session_id>/copy_for_pro.md
outputs/<session_id>/execution_handoff.md
outputs/<session_id>/bridge_receipt.md
outputs/<session_id>/golden_manifest.json
outputs/<session_id>/replay_result.json
```

The store is:

* repository-local through the Git common directory;
* private to the local Companion;
* append-only for events;
* content-addressed for artifact bytes;
* separate from AccelerationStore;
* fail-closed on corruption;
* non-authoritative for execution.

### D. Deterministic artifact contracts

Each imported artifact consists of two separate objects:

1. **raw payload bytes** — immutable identity source;
2. **Bridge Artifact Envelope** — typed structural fields.

The envelope may be supplied by:

* a normative fenced JSON block inside the artifact; or
* explicit UI metadata entered at import.

The Bridge never upgrades free prose into required structured fields.

### E. Structural Replay Evaluator

Replay operates on typed field atoms and stable field IDs. It does not use an LLM, embedding similarity, or fluent paraphrase scoring.

The prose body remains available for independent human audit, but preservation status is determined only from the structured record and its source map.

## 7. Existing Components Reused

### Reused as-is

1. **Repository picker and local Git-root validation**
   Reused to bind a Bridge session to one repository.

2. **Authenticated localhost server boundary**
   Existing Host, Origin, session-cookie, CSRF, loopback, and static-allowlist protections remain the security boundary for new Bridge endpoints.

3. **Existing Companion presentation shell**
   The new panel is added to the current private local UI rather than creating another app.

4. **Existing one-repository operating context**
   The Bridge uses the repository already selected by the Companion.

5. **Repository-native handoff field contract**
   The required fields from `docs/handoff_command.md` are reused as the generated handoff schema.

6. **Existing exact file-change approval**
   It remains the only Companion-native authorization surface for supported file creation or modification. The Bridge does not bypass or reinterpret it.

7. **Current runtime identity display**
   It remains the identity of the Codex execution runtime only. It is not reused as imported Pro model identity.

8. **Existing handoff acceptance command**
   It remains a separate, read-only assessment tool. v0.1 generates compatible handoff Markdown but does not modify, embed, or automatically invoke the acceptance implementation.

9. **Existing application build path**
   The current private app builder already copies the `decision_os` package. Actual inclusion of the new module must be verified by the Builder, but no build-script change is authorized unless the permitted implementation proves insufficient and a new Gate is obtained.

### Reused conceptually but kept separate

The Bridge adopts the existing repository’s useful identity discipline:

* immutable content hashing;
* append-only events;
* event identity;
* UTC import time;
* local corruption stop.

It does not reuse the existing Acceleration event identity as a Bridge artifact identity.

### Left untouched

The following are deliberately not extended in v0.1:

* `decision_os/acceleration/store.py`;
* `decision_os/acceleration/engine.py`;
* the existing Verified Save Receipt identity;
* the current approval decision key and rule hash;
* `decision_os/acceleration/codex_adapter.py`;
* `decision_os/handoff_acceptance.py`;
* `decision_os/intake.py`;
* `handoff/current_codex_handoff.md`;
* `docs/current_signal.md`;
* Stage 1 protocol;
* provisional roadmap;
* AGENTS.md;
* Runner behavior.

## 8. New Components Required

### A. Bridge artifact roles

The v0.1 role enum is fixed to:

```text
EVIDENCE_PACKET
PRO_DESIGN
EXECUTION_HANDOFF
BUILD_RECEIPT
PRO_AUDIT
REUSABLE_DELTA_RECORD
GOLDEN_MANIFEST
REPLAY_RESULT
BRIDGE_RECEIPT
FORWARD_ONLY_DELTA
```

The user may import only the first, second, fourth, fifth, and sixth roles. The Bridge generates the other roles.

### B. Bridge Artifact Envelope

The envelope is a typed record with independently visible identity and authority fields.

Minimum envelope fields:

```text
schema
task_id
protocol_run_id
artifact_role
source_path_or_label
selected_role
declared_role
model_identity.value
model_identity.basis
model_identity.verification_state
role_identity
artifact_authored_at
imported_at
as_of_commit
artifact_content_hash
import_event_id
authority_state
objective
completion_line
do_not_touch
current_gate
authority_boundary
required_next_actor
findings
human_execution_cost
reusable_delta
unknowns
```

### C. Bridge session state machine

The session state machine must include:

```text
BOUNDARY_INCOMPLETE
COPY_READY
DESIGN_IMPORTED
HANDOFF_GENERATED
HANDOFF_FROZEN
BUILD_RECEIPT_IMPORTED
AUDIT_IMPORTED
DELTA_IMPORTED
GOLDEN_INCOMPLETE
GOLDEN_ELIGIBLE
GOLDEN_FROZEN
REPLAY_ELIGIBLE
REPLAY_RECORDED
BLOCKED_CORRUPT
BLOCKED_AUTHORITY_INFLATION
```

### D. Deterministic generators

The new module must generate:

* Copy for Pro;
* imported-artifact identity record;
* Execution Handoff;
* Bridge Receipt;
* Golden manifest;
* Replay result.

### E. Separate burden observation record

The Bridge session includes a burden sheet with values, methods, units, evidence event IDs, and UNKNOWN state.

### F. Explicit correction events

No artifact is overwritten. A correction creates:

* new artifact bytes;
* new hash;
* new import event;
* `supersedes_import_event_id`;
* correction reason;
* Forward-only Delta linkage.

## 9. Artifact Lifecycle

### Lifecycle order

The normative Golden order is:

1. Evidence Packet
2. Pro Design Packet
3. Execution Handoff
4. Build Receipt
5. Pro Audit Receipt
6. Reusable Delta Record

### Freeze rules

An imported artifact becomes locally frozen when all of the following exist:

* exact captured payload bytes;
* SHA-256 of those bytes;
* selected artifact role;
* source path or source label;
* import event UUID;
* import timestamp;
* task and protocol IDs;
* authority state;
* immutable content-addressed storage entry.

A generated artifact becomes frozen only after:

* deterministic generation succeeds;
* all required fields are present or explicitly UNKNOWN;
* the user presses `Freeze`;
* output bytes and hash are recorded;
* the event is appended.

### No mutation after freeze

A frozen artifact is never edited in place. Later correction uses a new artifact and a Forward-only Delta.

### Missing artifacts

Every Golden role exists in the manifest from session creation. Before fixation, its entry is:

```json
{
  "state": "MISSING",
  "artifact_hash": "UNKNOWN",
  "import_event_id": "UNKNOWN",
  "reason": "NOT_YET_PRODUCED"
}
```

A missing artifact never disappears from the manifest.

### Golden eligibility

The set becomes eligible for Replay only when:

* all six required roles are present;
* every role has exactly one currently effective frozen artifact;
* all identities are fixed;
* role conflicts are absent;
* no unresolved authority inflation exists;
* the manifest itself is frozen.

Golden eligibility does not mean correctness, Product PASS, Protocol PASS, merge approval, or release approval.

## 10. Input Contracts

### A. Frozen Evidence Packet

Required identity:

```text
Task ID: V13-CMB-001
Protocol Run: V13-PMR-002
Packet commit: 970ae5e24e59dada54e1b829229360d9945a0910
Packet path: validation/companion_manual_bridge_v0_1_shared_evidence_packet.md
Packet blob SHA: 92f9f69f18db052b421fa5fa7f233ce77f5a42b8
Packet SHA-256: 847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab
Product As-of commit: 63eb260a94595298e2b07b476f7f9d8572c9ef09
```

Any mismatch produces `HOLD — EVIDENCE IDENTITY MISMATCH`.

### B. Pro Design artifact

Required:

* explicit selected role `PRO_DESIGN`;
* Task ID and Protocol Run ID;
* model identity value or `UNKNOWN`;
* model identity basis;
* role identity `Independent Pro Designer`;
* authored time or `UNKNOWN`;
* Product As-of commit;
* authority state `DESIGN_ONLY_NO_EXECUTION_AUTHORITY`;
* design judgment;
* exact implementation surface;
* required tests;
* Builder instructions;
* acceptance conditions;
* claim boundary;
* known UNKNOWNs;
* final seal.

Free prose may supplement but cannot replace these fields.

### C. Build Receipt

Required:

* Builder identity and authority source;
* task and protocol IDs;
* base commit;
* branch;
* implementation commit;
* exact changed paths;
* test commands and results;
* Build findings;
* deviations;
* repair count;
* execution cost fields;
* routine cleanup state;
* remaining UNKNOWNs;
* statement that Builder completion is not independent completion.

### D. Pro Audit artifact

Required:

* role `Independent Pro Auditor`;
* distinct import event;
* audit evidence basis;
* repository diff inspected;
* artifact identities independently checked;
* tests independently checked;
* Product Result recommendation;
* claim-boundary review;
* repair route;
* remaining UNKNOWNs.

### E. Reusable Delta Record

Required:

* source finding;
* source artifact identity;
* qualifying delta form;
* reuse scope;
* conditions;
* exclusions;
* evidence;
* owner;
* status `CANDIDATE`, `ACCEPTED`, or `REJECTED`;
* authority state `FUTURE_USE_CANDIDATE_ONLY` unless Shin explicitly accepts it elsewhere.

### F. Explicit artifact-role selection

Role selection is mandatory and must occur before bytes are accepted. The imported document’s own label is evidence only. It cannot silently choose its operational role.

## 11. Output Contracts

### A. Copy for Pro

Deterministic Markdown containing:

* fixed evidence identity;
* bounded role;
* required output;
* authority boundary;
* Do Not Touch;
* Completion Line;
* final seal.

It is clipboard output only. It triggers no model call.

### B. Imported-artifact identity record

Machine-readable JSON containing:

* exact payload SHA-256;
* payload size;
* content-addressed path;
* selected and declared roles;
* source label/path;
* model, role, time, As-of;
* import event;
* authority state;
* validation state;
* supersession link if any.

### C. Execution Handoff

Repository-native Markdown with exactly these required transfer fields:

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

Additional identity block:

```text
Task ID
Protocol Run ID
Evidence Packet identity
Pro Design artifact hash
Pro Design model identity
Pro Design role identity
Pro Design time anchor
Handoff hash
Authority state
```

The generated default Gate is `HOLD — SEPARATE BUILDER AUTHORITY REQUIRED`.

### D. Bridge Receipt

Title:

`Companion Manual Bridge v0.1 — Finding / Cost / Reusable Delta Receipt`

It must contain:

* artifact identities;
* findings;
* actual/observed cost fields with methods;
* Reusable Delta records;
* Protocol/Product/Replay result references;
* UNKNOWNs;
* claim boundary.

It must not display the current Verified Save estimates as Golden burden values.

### E. Golden manifest

JSON with six ordered artifact entries, status, hashes, time anchors, role identities, authority states, and source paths/labels.

### F. Replay result

JSON plus readable Markdown table with one row per fixed comparison field and one of the seven required statuses.

## 12. Identity and Hash Fixation

### Exact byte rule

The Bridge hashes the exact payload received before any:

* Unicode normalization;
* line-ending conversion;
* whitespace trimming;
* Markdown parsing;
* field extraction;
* display escaping.

A CRLF file and an LF file are different artifacts. A trailing newline difference changes identity.

### Import modes

**File import**

* hashes exact uploaded bytes;
* may be labeled `BYTE_EXACT_FILE_IMPORT`;
* eligible for Golden fixation.

**Paste import**

* encodes the exact captured browser string as UTF-8;
* hashes those captured bytes;
* must be labeled `PASTE_CAPTURE`;
* makes no claim that the captured bytes equal an external source file.

### Independently visible identities

The identity record keeps separate:

* Task ID;
* Protocol Run ID;
* selected artifact role;
* declared artifact role;
* model identity;
* model identity basis;
* model identity verification state;
* role identity;
* claimed authored time;
* system import time;
* Product As-of commit;
* Evidence Packet commit;
* artifact content hash;
* source path or source label;
* import event identity;
* authority state.

### Model identity rule

Imported Pro model identity is not treated as verified merely because the artifact states a model name. Allowed verification states are:

```text
VERIFIED_BY_RUNTIME
USER_ATTESTED
ARTIFACT_DECLARED
SELF_DECLARED
UNKNOWN
```

Only the existing Codex runtime can use `VERIFIED_BY_RUNTIME` under the current evidence.

### Time rule

The artifact-authored time and import-event time remain separate. Missing authored time remains `UNKNOWN`; the Bridge must not substitute import time for authored time.

### Duplicate and collision rule

* same bytes + same role + same session: record a duplicate event but reuse the content-addressed blob;
* same bytes + different selected role: `HOLD — ROLE COLLISION`;
* declared SHA-256 mismatch: reject import;
* content-addressed blob mismatch or store corruption: `BLOCKED_CORRUPT`.

### Identity is not authority

No hash, model name, role name, time, commit, source label, or manifest status is consumed by an execution route as permission.

## 13. Authority and Role Separation

| Artifact / actor  | Permitted meaning                               | Forbidden implication           |
| ----------------- | ----------------------------------------------- | ------------------------------- |
| Evidence Packet   | frozen evidence input                           | design or execution authority   |
| Pro Design        | design authority only                           | build, merge, publication, PASS |
| Execution Handoff | instruction artifact                            | authority grant                 |
| Builder           | bounded implementation under separate authority | independent completion          |
| Build Receipt     | execution evidence                              | audit PASS                      |
| Pro Audit         | independent judgment                            | implementation authority        |
| Reusable Delta    | future-use candidate                            | automatic Canon update          |
| Golden manifest   | comparison source                               | correctness or certification    |
| Replay result     | structural preservation result                  | Protocol or Product PASS        |
| Shin              | final Decision Seat                             | routine cleanup executor        |

### Role separation checks

* Pro Design and Pro Audit must have different artifact roles and different import event IDs.
* A Build Receipt cannot satisfy the Pro Audit input.
* A generated Bridge Receipt cannot declare independent audit completion without a valid `PRO_AUDIT` import.
* Model identity equality does not automatically violate independence; role/event separation and declared independent execution remain required.
* Role identity is evidence, not authority.

### Execution boundary

The Bridge never:

* starts a Builder;
* writes a repository file;
* approves a file change;
* grants merge or publication rights;
* changes the existing exact approval default;
* converts the handoff into an active execution turn.

## 14. Execution Handoff Generation

### Generation prerequisites

Generation is enabled only when:

1. the Evidence Packet identity matches;
2. a frozen Pro Design import exists;
3. Task ID and Protocol Run ID match;
4. Product As-of commit is present;
5. selected and declared roles do not conflict;
6. the Pro Design authority state is design-only;
7. required handoff fields exist in the structured record;
8. UNKNOWNs remain explicit;
9. no store corruption or authority inflation is active.

### Source precedence

Handoff fields are populated in this order:

1. frozen session boundary;
2. fixed Evidence Packet identity;
3. typed Pro Design fields;
4. explicit `UNKNOWN`.

Free prose is never used to fill a missing required field.

### Default authority state

The generated handoff states:

```text
Current Gate:
HOLD — SEPARATE BUILDER AUTHORITY REQUIRED

Next Authorized Action:
Shin may grant a fresh Builder the bounded implementation task defined by this
handoff. Until that separate grant exists, no implementation action is authorized.

Authority state:
INSTRUCTION_ARTIFACT_ONLY
```

This is intentionally conservative. Shin’s later transmission and explicit authorization are human Seat actions outside artifact identity.

### Repository-native form

The output follows the existing thirteen-field handoff contract and adds identity references without changing the meaning of current handoff acceptance.

### Freeze behavior

Once frozen, a handoff is immutable. Any change requires a Forward-only Delta and a new handoff hash.

## 15. Finding / Cost / Reusable Delta Receipt

The Bridge Receipt is a new record and must not extend or rename the existing Verified Save Receipt.

### Receipt identity

```text
receipt_type:
COMPANION_MANUAL_BRIDGE_V0_1

receipt_id:
SHA-256 over canonical receipt JSON plus referenced import event IDs

claim_boundary:
Local artifact-chain and observation record; not third-party certification,
task correctness proof, model verification, merge approval, or burden-reduction proof.
```

### Finding record

Each finding includes:

* finding ID;
* source artifact role;
* source artifact hash;
* source excerpt or structured atom IDs;
* finding type;
* materiality state;
* audit state;
* UNKNOWNs.

### Cost record

Each cost includes:

* field name;
* numeric value or UNKNOWN;
* unit;
* measurement method;
* evidence event IDs;
* confidence/basis;
* whether user-entered or system-derived.

No configured estimate is relabeled as measured cost.

### Reusable Delta record

Each delta includes:

* delta ID;
* source finding;
* exact source artifact identities;
* reusable form;
* scope;
* conditions;
* exclusions;
* evidence;
* owner;
* status;
* next recheck.

A delta is not counted as accepted merely because it is present. The Receipt shows candidate and accepted counts separately.

### Receipt completion rule

Receipt generation is permitted with missing fields, but missing values remain `UNKNOWN`. Receipt generation does not create Product PASS.

## 16. Golden Artifact Set

### Repository naming

The first Golden Run uses this reserved repository directory:

```text
validation/companion_manual_bridge_v0_1_golden/
```

The six artifacts are:

```text
1. validation/companion_manual_bridge_v0_1_shared_evidence_packet.md
2. validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_02_pro_design_packet.md
3. validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_03_execution_handoff.md
4. validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_04_build_receipt.md
5. validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_05_pro_audit_receipt.md
6. validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_06_reusable_delta_record.md
```

Manifest:

```text
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_manifest.json
```

First bounded repair record, if required:

```text
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_forward_only_delta_001.md
```

Replay result:

```text
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_replay_result.json
```

### Minimum manifest fields

```text
schema
task_id
protocol_run_id
golden_status
golden_status_claim_boundary
artifact_order
artifact_role
repository_path_or_source_label
artifact_sha256
git_blob_sha_or_unknown
fixation_commit_or_unknown
import_event_id
model_identity
model_identity_basis
role_identity
artifact_authored_at
imported_at
as_of_commit
authority_state
result_boundary
unknowns
supersedes
```

### When an artifact becomes frozen

Local freeze occurs when exact bytes and identity are fixed in the Bridge store. Repository freeze occurs when the exact bytes are committed and the commit/blob identity is added to the manifest through a Forward-only manifest update.

### Forward-only correction

A correction does not rewrite the original artifact. It creates `v13_pmr_002_forward_only_delta_001.md`, identifies the affected artifact and hash, states the reason, records the replacement artifact identity, and preserves the original manifest entry as historical.

### Missing artifact visibility

The manifest is created with all six entries. Missing roles remain `MISSING` until separately fixed.

### Replay eligibility

The set is Replay-eligible only when all six artifacts are frozen and the manifest has no unresolved role collision, hash mismatch, or authority inflation.

**Golden means frozen comparison source. It does not mean correct.**

## 17. Replay Evaluation

### Comparison object

Replay compares a baseline Golden manifest and candidate Replay outputs.

The fixed fields are:

1. Task ID
2. Objective
3. Completion Line
4. Do Not Touch
5. Current Gate
6. Authority Boundary
7. As-of commit / artifact hash
8. Model identity
9. Role identity
10. Time anchor
11. Required next actor
12. Findings
13. Human / execution cost
14. Reusable Delta
15. UNKNOWNs

### Structural atom format

Each field is represented as typed atoms:

```json
{
  "field": "completion_line",
  "atoms": [
    {
      "atom_id": "CL-001",
      "value": "bounded statement",
      "source_artifact_hash": "sha256",
      "source_location": "structured envelope path"
    }
  ]
}
```

Downstream generated artifacts propagate the stable `atom_id` and source identity. Human prose may be rewritten, but the structural atoms must remain visible.

### Status vocabulary

Every field receives exactly one primary status:

* `PRESERVED`
* `ALTERED`
* `MISSING`
* `SUBSTITUTED`
* `AUTHORITY-INFLATED`
* `NOT APPLICABLE`
* `UNKNOWN`

Definitions:

**PRESERVED**
All required baseline atoms and relations remain present with valid source identity.

**ALTERED**
The field exists, but one or more baseline atoms or relations changed.

**MISSING**
A required baseline field or atom is absent.

**SUBSTITUTED**
A different field, artifact role, actor, time, or source is presented in place of the baseline field.

**AUTHORITY-INFLATED**
The candidate gives an artifact or actor more authority than the baseline permits.

**NOT APPLICABLE**
The baseline explicitly declares the field not applicable and preserves the reason.

**UNKNOWN**
The baseline or candidate explicitly preserves unresolved state; it is not treated as PASS.

### Overall Replay rule

Replay PASS requires:

* every required field is `PRESERVED` or evidence-backed `NOT APPLICABLE`;
* baseline UNKNOWNs remain UNKNOWN or become resolved only through an explicit Forward-only Delta;
* no `ALTERED`, `MISSING`, `SUBSTITUTED`, or `AUTHORITY-INFLATED` field exists.

### No fluent-prose escape

A paragraph that appears semantically similar but lacks the required field atom is `MISSING`, not `PRESERVED`.

### Additions

New findings or deltas are recorded as Forward-only additions. They do not rewrite baseline preservation status.

## 18. Protocol / Product / Replay Result Separation

The Bridge stores three separate result objects.

### Protocol Result

Question:

`Did Pro Manual Protocol Run 002 execute correctly?`

Fields:

* protocol steps completed;
* role sequence;
* artifact identities;
* repair count;
* protocol deviations;
* human-burden observations;
* result;
* UNKNOWNs.

### Product Result

Question:

`Did Companion Manual Bridge v0.1 satisfy this bounded design?`

Fields:

* acceptance-condition results;
* test evidence;
* regression evidence;
* implementation diff;
* security boundary;
* result;
* UNKNOWNs.

### Replay Result

Question:

`Did the Bridge preserve the Golden Run structure?`

Fields:

* baseline manifest;
* candidate manifest;
* fifteen field results;
* authority-inflation findings;
* overall Replay result;
* UNKNOWNs.

### Non-implication rule

The record schema includes:

```text
protocol_result_does_not_imply_product_result: true
protocol_result_does_not_imply_replay_result: true
product_result_does_not_imply_protocol_result: true
product_result_does_not_imply_replay_result: true
replay_result_does_not_imply_protocol_result: true
replay_result_does_not_imply_product_result: true
```

No UI badge may collapse these into one PASS.

## 19. Human-Burden Observation

The Bridge preserves all Scout-defined fields.

| Observation                            | v0.1 recording method                                                                            |
| -------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Shin manual transfer count             | system-derived from explicit copy-out/import-in transfer events; method shown                    |
| Shin copy/paste count                  | clipboard button and paste-import events; file import is not counted as paste                    |
| Shin re-explanation count              | explicit one-click `Record re-explanation`; otherwise UNKNOWN                                    |
| Shin boundary-correction count         | superseding import or correction event tagged `BOUNDARY_CORRECTION`                              |
| Shin operational intervention count    | explicit reject, HOLD, supersede, manual correction, or recovery event                           |
| Human handling time                    | local active-interaction intervals with idle exclusion and method label; if unavailable, UNKNOWN |
| Total elapsed time                     | first session event to final selected event                                                      |
| Number of Pro calls                    | unique Pro call IDs if entered; otherwise derived lower bound plus UNKNOWN qualifier             |
| Number of Builder repairs              | Build Receipt field; not inferred from commits                                                   |
| Number of reusable deltas              | count by status: candidate / accepted / rejected                                                 |
| Fields lost or altered during transfer | Replay counts by status                                                                          |

### Observation record schema

Every observation stores:

```text
value_or_unknown
unit
method
source_event_ids
recorded_at
basis
confidence
notes
```

### Minimizing work returned to Shin

The default is automatic local event counting. Shin is asked only for facts the system cannot observe, using bounded one-click actions or one numeric field. No free-form retrospective burden report is required.

### No improvement promise

The product records burden. It does not promise that counts, time, cost, or corrections will improve.

### No estimate substitution

Existing Verified Save estimates remain separate and are never copied into the Golden burden sheet.

## 20. Framework Lens Handling

The provisional hypothesis is preserved without becoming a v0.1 implementation claim:

```text
Material Finding
=
Model Tier
× Independent Role
× Framework Lens
```

The Bridge includes four optional metadata fields:

```text
framework_lens_used
relevant_decision_os_layer
reinterpretation_question
framework_derived_finding
```

Rules:

* all four are optional;
* absence is `UNKNOWN` or `NOT APPLICABLE`, not failure;
* they do not affect artifact authority;
* they do not affect Product PASS;
* they do not select a model;
* they do not route AGENTS.md;
* they do not remove independent Pro Audit;
* they do not load V9–V13 theory automatically;
* they are displayed as provisional observation metadata only.

Including these fields in v0.1 is justified as low-cost trace preservation. Any claim that they improve findings is a Forward-only research candidate and requires later evidence.

## 21. Failure Modes and Fail-Closed Rules

| Failure mode                                        | Required behavior                                      |
| --------------------------------------------------- | ------------------------------------------------------ |
| no explicit role selection                          | reject import                                          |
| selected role differs from declared role            | HOLD — ROLE MISMATCH                                   |
| exact bytes differ from declared hash               | reject import; preserve failure event                  |
| missing Task ID or Protocol Run ID                  | identity may be stored, stage remains HOLD             |
| As-of commit missing or malformed                   | preserve UNKNOWN; no handoff freeze                    |
| Evidence Packet identity mismatch                   | HOLD — EVIDENCE IDENTITY MISMATCH                      |
| model identity missing                              | store UNKNOWN; never substitute Codex runtime identity |
| authored time missing                               | store UNKNOWN; keep import time separate               |
| same artifact used as Design and Audit              | HOLD — ROLE COLLISION                                  |
| Build Receipt offered as Pro Audit                  | reject stage substitution                              |
| imported prose claims execution authority           | prose remains non-operative; flag authority review     |
| structured authority exceeds role                   | BLOCKED_AUTHORITY_INFLATION                            |
| UNKNOWN omitted or converted to PASS                | Product test failure and Replay failure                |
| required handoff field missing                      | no freeze; mark MISSING                                |
| Golden role absent                                  | manifest remains GOLDEN_INCOMPLETE                     |
| fluent paraphrase without structural atom           | MISSING                                                |
| wrong source atom used                              | SUBSTITUTED                                            |
| store event-chain or blob corruption                | block Bridge reads/appends for affected repository     |
| generated output hash changes after freeze          | corruption/block                                       |
| Protocol/Product/Replay result collapsed            | Product test failure                                   |
| Builder generates its own independent audit         | reject audit eligibility                               |
| existing approval or Verified Save behavior changes | Product FAIL                                           |
| Bridge route starts Codex or writes files           | forbidden deviation / BLOCK                            |
| routine Builder cleanup returned to Shin            | audit finding; Product cannot PASS until closed        |
| second route-changing repair needed                 | HOLD — NEW GATE REQUIRED                               |

Corruption in the separate Bridge store must not silently modify or reinterpret the existing Acceleration store. The Bridge panel may fail closed while the accepted existing Runner remains available, provided no shared security boundary is compromised.

## 22. Exact Implementation Change Surface

The fresh Builder may modify only these existing paths:

```text
decision_os/companion/controller.py
decision_os/companion/server.py
decision_os/companion/static/index.html
decision_os/companion/static/app.js
tests/test_companion_controller.py
tests/test_companion_server.py
```

The fresh Builder may create only these implementation paths:

```text
decision_os/companion/manual_bridge.py
docs/companion_manual_bridge_v0_1.md
tests/test_companion_manual_bridge.py
tests/fixtures/companion_manual_bridge_v0_1/pro_design_valid.md
tests/fixtures/companion_manual_bridge_v0_1/pro_audit_valid.md
tests/fixtures/companion_manual_bridge_v0_1/build_receipt_valid.md
tests/fixtures/companion_manual_bridge_v0_1/reusable_delta_valid.md
tests/fixtures/companion_manual_bridge_v0_1/artifact_role_mismatch.md
tests/fixtures/companion_manual_bridge_v0_1/artifact_authority_inflated.md
tests/fixtures/companion_manual_bridge_v0_1/golden_manifest_complete.json
tests/fixtures/companion_manual_bridge_v0_1/golden_manifest_missing.json
tests/fixtures/companion_manual_bridge_v0_1/replay_candidate_preserved.json
tests/fixtures/companion_manual_bridge_v0_1/replay_candidate_field_loss.json
tests/fixtures/companion_manual_bridge_v0_1/replay_candidate_authority_inflated.json
```

The Builder may create these Golden Run files only when the exact source bytes exist and only within its stage authority:

```text
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_02_pro_design_packet.md
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_03_execution_handoff.md
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_04_build_receipt.md
```

The following paths are reserved for later owners and are **not** Builder-authorized:

```text
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_05_pro_audit_receipt.md
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_06_reusable_delta_record.md
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_manifest.json
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_forward_only_delta_001.md
validation/companion_manual_bridge_v0_1_golden/v13_pmr_002_replay_result.json
```

The Builder may run, but not modify, all existing tests.

### Explicitly forbidden modification paths

```text
decision_os/acceleration/model.py
decision_os/acceleration/store.py
decision_os/acceleration/engine.py
decision_os/acceleration/codex_adapter.py
decision_os/handoff_acceptance.py
decision_os/intake.py
decision_os/cli.py
pyproject.toml
scripts/build_companion_app.sh
macos/DecisionOSCompanion.applescript
handoff/current_codex_handoff.md
docs/current_signal.md
docs/handoff_command.md
field_notes/pro_manual_protocol_v0_1.md
field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md
AGENTS.md
```

### DESIGN REQUIRES BUILDER DISCOVERY

No additional repository path discovery is authorized.

The only narrow discovery allowed is locating insertion points inside the six permitted existing files and confirming that the current app builder automatically includes the newly created `decision_os/companion/manual_bridge.py`.

If implementation requires any other path, dependency, command entry, build-script change, schema migration, or acceleration-store change:

`HOLD — DESIGN DEVIATION REQUIRED`.

## 23. Required Tests and Guards

The Builder must implement tests for at least the following.

### Artifact-byte hashing

* exact bytes produce expected SHA-256;
* LF and CRLF differ;
* trailing newline difference changes hash;
* paste capture identifies captured UTF-8 bytes honestly;
* declared hash mismatch rejects import.

### Identity fixation

* Task ID, Protocol Run, selected role, model, role, authored time, import time, As-of, source, hash, import event, and authority remain separately visible;
* missing model/time remains UNKNOWN;
* current Codex runtime identity is not substituted for Pro identity.

### Identity without authority

* imported hash never starts a run;
* imported role never creates file approval;
* generated handoff never writes a file;
* artifact identity never creates PASS.

### Design/Audit separation

* separate roles and import events required;
* Build Receipt cannot fill Audit;
* Builder-generated audit is ineligible;
* same model identity is allowed only with separate role/event evidence and no self-certification.

### UNKNOWN preservation

* UNKNOWN survives generation;
* UNKNOWN cannot become empty string, false, zero, N/A, or PASS;
* baseline UNKNOWN is recognized in Replay.

### Handoff required fields

* all thirteen repository-native fields required;
* missing field blocks freeze;
* routine work is not assigned to Shin;
* receiving ownership is separate from Next Owner.

### Imported artifact cannot authorize execution

* authority claims in prose are non-operative;
* structured authority inflation is blocked;
* no Bridge endpoint calls the Codex adapter.

### Golden manifest completeness

* six ordered roles always visible;
* missing roles remain MISSING;
* Golden eligibility requires all six;
* Golden status does not alter Product Result.

### Replay comparison

* each of fifteen fields receives one valid status;
* preserved atom passes;
* missing atom is MISSING;
* wrong source is SUBSTITUTED;
* changed field is ALTERED;
* authority escalation is AUTHORITY-INFLATED;
* fluent prose without atom cannot pass.

### Result separation

* Protocol, Product, and Replay records have separate identities;
* one PASS never updates another result;
* UI presents three independent statuses.

### Corrupted or altered artifact rejection

* corrupted content-addressed blob blocks Bridge use;
* event-chain mismatch blocks appends;
* frozen output byte change is detected;
* duplicate bytes with role collision hold.

### Existing Companion regression

* existing repository picker behavior remains;
* one active Codex Run behavior remains;
* existing security controls remain;
* existing approval choices remain;
* existing revocation remains;
* existing Verified Save/Reuse Receipt values and claim boundary remain;
* existing runtime identity checks remain;
* existing handoff acceptance remains read-only and unchanged.

### Security and presentation

* new endpoints require session and CSRF;
* file names and artifact prose are escaped;
* raw imported prose is never echoed into executable HTML;
* content size limits are enforced;
* only selected repository-local Bridge state is accessed.

### Full suite

* all new focused tests pass;
* all existing focused tests pass;
* full repository suite passes;
* `git diff --check` passes;
* no protected existing blob is changed outside the permitted surface.

## 24. Builder Instructions

### Implementation order

1. Verify the exact base commit supplied by the execution handoff.
2. Confirm the permitted change surface and clean worktree.
3. Create `decision_os/companion/manual_bridge.py`.
4. Implement immutable byte storage, identity records, separate event chain, lifecycle, deterministic generators, and Replay evaluator.
5. Integrate one Bridge session into `CompanionController` without changing existing Run semantics.
6. Add authenticated Bridge GET/POST routes in `server.py`.
7. Add the bounded Manual Bridge panel to `index.html` and `app.js`.
8. Add fixtures and focused tests.
9. Add the bounded documentation file.
10. Run focused and full regression suites.
11. Build the private app using the existing builder and verify the new module is included without modifying the builder.
12. Run a local smoke test.
13. Import the exact Pro Design artifact, generate and freeze the Execution Handoff, and preserve their exact hashes.
14. Produce the Build Receipt.
15. Stop. Do not perform the independent Pro Audit.

### Exact boundaries

The Builder must not:

* modify any path outside Section 22;
* start Guided Intake, Multi-Agent Roles, or Orchestra work;
* add automatic Pro invocation;
* add network access;
* add model routing;
* use an LLM for Replay;
* extend the existing Verified Save Receipt;
* change exact file approval;
* change handoff acceptance;
* create Pro Audit or Reusable Delta results;
* merge or publish without separate authority.

### Migration behavior

* no migration of existing Companion state;
* no migration of AccelerationStore;
* no change to saved exact access;
* the new Bridge root is created lazily under the Git common directory;
* absence of Bridge state means an empty Bridge session, not corruption;
* corrupt Bridge state blocks Bridge use for that repository and preserves evidence;
* existing Runner remains unchanged unless the shared local security boundary itself fails.

### Failure behavior

All validation failures are visible and typed. The Builder must not catch and smooth a failure into a generic success message.

### Evidence to preserve

The Build Receipt must preserve:

* base commit;
* branch;
* implementation commit;
* exact changed paths;
* local/remote head state;
* test commands and outputs;
* app build/smoke evidence;
* generated artifact hashes;
* event-chain head;
* deviations;
* repairs;
* UNKNOWNs;
* routine cleanup status.

### Required Build Receipt

The receipt must state:

```text
Builder completion is execution evidence only.
It is not independent Product PASS, Protocol PASS, Replay PASS, merge approval,
publication approval, or reusable-delta acceptance.
```

### HOLD — DESIGN DEVIATION REQUIRED

The Builder must stop and request a new Gate if any of the following is required:

* another repository path;
* a new dependency;
* an existing store or Receipt modification;
* Codex adapter integration;
* automatic handoff acceptance;
* semantic/LLM Replay;
* automatic authority grant;
* more than one generated repository file mutation in a current Companion Run;
* a route-changing repair;
* modification of current signal or current handoff;
* modification of AGENTS.md;
* scope beyond Stage 2.

## 25. Acceptance Conditions

Companion Manual Bridge v0.1 receives **Product PASS** only when every condition below is independently evidenced.

1. The existing Companion opens with its current repository selection, task runner, result, runtime, approval, and Verified Save surfaces intact.
2. One bounded Manual Bridge panel is available only on the authenticated local surface.
3. `Copy for Pro` is deterministic for the same frozen session input.
4. Artifact import requires explicit user-selected role.
5. File import hashes exact bytes before parsing.
6. Paste import is labeled as captured payload, not external-file identity.
7. An identity record displays all required identities separately.
8. Missing model or authored time remains UNKNOWN.
9. Importing any artifact triggers no execution or file mutation.
10. Pro Design and Pro Audit require separate roles and import events.
11. Execution Handoff generation requires all fixed prerequisites.
12. The generated handoff contains all thirteen repository-native fields.
13. The generated handoff states instruction-only authority and separate Builder authority requirement.
14. The existing exact file approval remains unchanged.
15. The Bridge Receipt is separate from the Verified Save Receipt.
16. The Bridge Receipt does not use configured Verified Save estimates as measured Golden burden.
17. The Golden manifest always displays all six roles.
18. Missing Golden artifacts remain visible.
19. Golden eligibility does not set Product, Protocol, or Replay PASS.
20. Replay emits one of the seven fixed statuses for every required field.
21. Replay does not use free-prose similarity as preservation evidence.
22. Authority inflation is detected and blocks Replay PASS.
23. UNKNOWN cannot be upgraded by generation or Replay.
24. Protocol, Product, and Replay result records remain separate in storage and UI.
25. Store corruption blocks Bridge use and preserves the failure.
26. Current Companion approval, revocation, runtime identity, event chain, and Verified Save behavior pass regression tests.
27. Existing handoff acceptance remains unchanged.
28. All focused and full tests pass.
29. Private app build and local smoke test pass.
30. No out-of-scope path changed.
31. The Build Receipt exists with the required claim boundary.
32. Independent Pro Audit is still required before Product Result is finalized.
33. No claim of burden reduction is made without measured evidence.
34. Routine implementation and cleanup are closed by the Builder rather than returned to Shin.

“Works correctly,” “preserves context,” or “supports workflow” is not an acceptance condition unless evidenced through the criteria above.

## 26. Independent Audit Hooks

The later Pro Auditor must independently inspect:

1. repository base and implementation commits;
2. complete repository diff;
3. exact changed-path list against Section 22;
4. no hidden changes to AccelerationStore, Receipt, approval, Codex adapter, handoff acceptance, or AGENTS.md;
5. artifact fixtures and their exact hashes;
6. at least three independently recomputed artifact SHA-256 values;
7. selected role versus declared role behavior;
8. model/role/time/As-of separation;
9. authority state and non-operative imported prose;
10. generated Execution Handoff, including all thirteen fields;
11. the statement that separate Builder authority is required;
12. Bridge Receipt identity and claim boundary;
13. separation from Verified Save Receipt;
14. Golden manifest completeness and missing-state visibility;
15. Forward-only correction behavior;
16. Replay output for preserved, missing, substituted, altered, UNKNOWN, N/A, and authority-inflated cases;
17. separate Protocol/Product/Replay records;
18. focused and full test results;
19. private app build and smoke evidence;
20. local store corruption behavior;
21. UI security and raw-prose escaping;
22. human-burden values, methods, event IDs, and UNKNOWNs;
23. no improvement promise;
24. Framework Lens optional fields and non-gating behavior;
25. routine cleanup completion;
26. claim boundary;
27. all remaining UNKNOWNs.

The Pro Auditor must not accept the Builder’s hashes or test summary as sufficient. Independent recomputation and fixture inspection are required.

## 27. Allowed Deviations

The Builder may vary only the following without a new design Gate:

* internal class and function names inside `manual_bridge.py`;
* private JSON key ordering;
* visual arrangement of the Manual Bridge panel;
* neutral wording of buttons;
* whether file and paste import appear as tabs or separate controls;
* UUID generation implementation;
* internal helper decomposition within the single new module;
* test fixture prose, provided each required structural case remains covered;
* idle threshold used for active handling time, provided the exact method is shown and the value is not presented as universal truth.

Any allowed variation must preserve all contracts, statuses, paths, authority boundaries, tests, and claim boundaries.

## 28. Forbidden Deviations

The following are forbidden:

* redesigning the Companion from scratch;
* new public service or network listener;
* public SaaS or external onboarding;
* automatic Pro model call;
* automatic model selection or routing;
* Multi-Agent Roles or Orchestra;
* Guided Intake;
* general workflow orchestration;
* AGENTS.md modification;
* semantic LLM Replay;
* embedding similarity used as structural preservation proof;
* imported prose used as execution permission;
* Bridge-generated PASS used as merge or publication authority;
* modification or extension of Verified Save Receipt semantics;
* migration of AccelerationStore;
* modification of exact file approval semantics;
* automatic invocation or rewriting of handoff acceptance;
* audit generated by the Builder;
* deletion or hiding of missing Golden roles;
* rewriting frozen artifacts in place;
* changing historical As-of facts through a correction;
* converting UNKNOWN into N/A or PASS;
* returning routine Git, test, fixture, hashing, build, or cleanup work to Shin;
* any Stage 3–5 behavior;
* pricing, market claims, or publication work;
* unrelated cleanup or refactoring.

## 29. Repair Boundary

One bounded Forward-only repair is allowed after independent audit.

The repair must:

* remain inside the exact implementation paths in Section 22;
* address one audit finding;
* create no new architecture route;
* preserve all frozen Golden artifacts;
* create `v13_pmr_002_forward_only_delta_001.md`;
* state reason, impact, changed paths, tests, rollback, and re-evaluation condition;
* produce a new Build Receipt;
* return to independent audit.

The repair must not rewrite the original design, original Build Receipt, or original audit.

If the repair requires a second route-changing correction, a new dependency, a new path, store conflation, authority change, or architecture redesign:

**HOLD — NEW GATE REQUIRED.**

## 30. Claim Boundary

This packet claims only that the frozen evidence supports a bounded, implementable design for Companion Manual Bridge v0.1.

It does not claim:

* the Bridge exists;
* the Bridge is secure against all threats;
* the Bridge reduces burden;
* imported model identity is independently verified;
* structural Replay proves semantic truth;
* a Golden artifact is correct;
* a hash grants authority;
* a manifest is certification;
* the manual protocol has passed;
* the product has passed;
* Replay has passed;
* the private installed app matches current repository bytes;
* a Reusable Delta is accepted;
* implementation should merge or publish;
* the optional Framework Lens hypothesis is proven.

Replay proves only the bounded structural comparison encoded by its field contracts.

The Bridge Receipt proves only the local artifact and observation chain it records.

## 31. Known UNKNOWNs

The following remain UNKNOWN after this design:

* Shin’s acceptance of the design;
* exact content hash of this Pro Design artifact until import;
* independently verified model identity for this Pro Design artifact;
* exact Builder identity;
* exact Builder authority grant;
* implementation branch and commit;
* actual implementation findings;
* actual Build Receipt bytes and hash;
* exact Pro Auditor identity and model;
* Pro Audit result;
* Reusable Delta count and acceptance;
* all measured Golden Run burden values;
* actual reduction or increase in manual transfer burden;
* installed private app parity at build time;
* final Protocol Result;
* final Product Result;
* final Replay Result;
* whether optional Framework Lens metadata produces material value;
* whether the first bounded repair will be needed;
* whether exact UI-active-time measurement is sufficiently reliable;
* whether external prose outside the structured envelope contains contradictions requiring independent semantic audit.

These UNKNOWNs are not defects to smooth over. They are required future observations.

## 32. Exit Gate

The Pro Design stage is complete when:

* this exact artifact is sealed;
* its bytes are fixed by the next import event;
* Shin accepts or rejects it;
* no implementation has been performed by GPT 13-18;
* no authority has been granted by the artifact itself;
* the next owner is unambiguous.

Design output:

**DESIGN READY FOR BUILD**

Current transition state:

```text
HOLD — AWAITING SHIN ACCEPTANCE AND SEPARATE FRESH BUILDER AUTHORITY
```

No routine implementation preparation remains assigned to Shin. After acceptance, the receiving Builder owns implementation planning, code, tests, app build, receipts, and routine cleanup within the authorized surface.

Task ID:
V13-CMB-001

Protocol Run:
V13-PMR-002

Role:
Independent Pro Designer

Design Gate:
DESIGN READY FOR BUILD

Evidence Packet Commit:
970ae5e24e59dada54e1b829229360d9945a0910

Evidence Packet Blob SHA:
92f9f69f18db052b421fa5fa7f233ce77f5a42b8

Evidence Packet SHA-256:
847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab

Design Status:
SEALED — AWAITING SHIN ACCEPTANCE

Implementation Authority:
NONE

Next Owner:
Fresh SOL / coding-agent Builder
