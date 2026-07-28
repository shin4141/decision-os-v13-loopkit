# Companion Manual Bridge v0.1 — Shared Evidence Packet

## 1. Packet Identity

```text
Task ID:
V13-CMB-001

Protocol Run:
V13-PMR-002

Stage:
Stage 2 — Companion Manual Bridge

Current role:
SOL Scout

Packet status:
FROZEN SHARED EVIDENCE

Observation time:
2026-07-28T20:39:13+09:00

Repository:
shin4141/decision-os-v13-loopkit

Repository root observed:
/Users/sn/Documents/v13/decision-os-v13-loopkit

Exact As-of commit:
63eb260a94595298e2b07b476f7f9d8572c9ef09

Observation branch:
codex/v13-cmb-001-shared-evidence-freeze

Decision Owner:
Shin

Pro Design status:
NOT STARTED

Bridge implementation status:
NOT STARTED

Product PR status:
NOT CREATED
```

This packet freezes repository evidence for one later independent Pro Designer.
It records present surfaces, absent surfaces, fixed requirements, and
`UNKNOWN`s. It does not choose a Bridge architecture, UI, schema, parser,
storage model, or execution method.

The packet's own Git blob SHA and file SHA-256 cannot be embedded as literal
values without changing the bytes being identified. Sections 18 and 19 preserve
the repository-native external-fixation rule. The authoritative values are
recorded in the Scout completion receipt after commit.

## 2. Task Boundary

```text
Objective:
Produce one frozen Shared Evidence Packet that allows an independent Pro
Designer to design Companion Manual Bridge v0.1 without re-observing the
repository or asking Shin to reconstruct the current operating state.

Target product surface:
Existing Decision OS Companion and its repository-native handoff, receipt,
identity, and execution-routing surfaces.

Current Gate:
GO UNDER CAP — SOL SCOUT / EVIDENCE PACKET ONLY

Authority Boundary:
Repository inspection plus creation, commit, and push of exactly one Shared
Evidence Packet file.

Completion Line:
The canonical As-of state and current Companion surfaces are evidenced; present,
partial, documented-only, absent, and UNKNOWN states are separated; Stage 2,
Golden Run, Replay, burden-observation, and authority boundaries are fixed; and
exactly this one packet is committed and pushed without design, implementation,
test changes, PR, merge, cleanup, or product modification.
```

This Run instantiates only the first step of the fixed manual chain:

```text
SOL Scout
→ Pro Design
→ SOL / coding-agent Build
→ Independent Pro Audit
→ Reusable Delta Fixation
```

The later actors receive evidence and authority only through their own gates.
This packet is an input artifact. Its existence and identity do not authorize
any later action.

## 3. Canonical Repository State

Before this packet was created, the following identities were observed:

```text
required As-of:
63eb260a94595298e2b07b476f7f9d8572c9ef09

starting HEAD:
63eb260a94595298e2b07b476f7f9d8572c9ef09

local main:
63eb260a94595298e2b07b476f7f9d8572c9ef09

origin/main:
63eb260a94595298e2b07b476f7f9d8572c9ef09

GitHub main from refs/heads/main:
63eb260a94595298e2b07b476f7f9d8572c9ef09

local main versus origin/main:
0 ahead / 0 behind

starting branch:
main

starting index and worktree:
CLEAN

untracked task artifacts:
NONE

unmerged state:
NONE
```

The observation branch was created directly from the exact As-of commit. `main`
was not moved or modified.

The As-of commit is the history-preserving merge of PR #42. Its first-parent
line contains the Stage 1 manual protocol and the provisional roadmap. Relevant
main history after the V13-SDFP-001 technical integration includes:

```text
0338edf  Merge PR #40 — V13-SDFP-001 final record fixation
8b98b66  Merge PR #41 — provisional LoopKit Orchestra roadmap
63eb260  Merge PR #42 — Pro Manual Protocol v0.1
```

At the As-of commit, the first operative blocks in
`handoff/current_codex_handoff.md` and `docs/current_signal.md` still name
V13-SDFP-001 post-merge discussion and canonical main
`c2f8870143cfed34bb6a8b8ee6ddcdcf6040a494`. The roadmap and Stage 1 protocol
were added by later main commits. This packet does not rewrite those state
surfaces. The explicit V13-CMB-001 handoff that authorized this Scout supplies
the new bounded Gate for this task.

Repository facts and the current authorization are therefore kept distinct:

- Git establishes the exact product and document bytes at the As-of commit.
- The current task handoff establishes Scout authority only.
- Older handoff and signal entries remain evidence at their recorded As-of and
  do not grant Bridge design or implementation authority.

## 4. Existing Companion Architecture

The repository contains a private local macOS Companion with this observed
runtime chain:

```text
Decision OS Companion.app
→ AppleScript launcher
→ python -m decision_os.companion
→ authenticated 127.0.0.1 browser surface
→ CompanionController
→ Codex app-server adapter
→ AccelerationEngine
→ append-only repository-local Verified Save state
```

### Launch and presentation

- `scripts/build_companion_app.sh` builds a private `.app`, copies the current
  `decision_os` package into a private runtime, preserves prior installed app
  and runtime directories as timestamped backups, and installs under the
  user's Applications and Application Support directories.
- `macos/DecisionOSCompanion.applescript` opens a fixed local repository picker
  and launches `python -m decision_os.companion`.
- `decision_os/companion/__main__.py` creates the controller and authenticated
  loopback server, opens a one-use bootstrap URL in the browser, and serves
  until shutdown.
- `decision_os/companion/server.py` binds only to `127.0.0.1` on an ephemeral
  port. It requires exact Host, same-origin, a private session cookie, and CSRF
  for state changes. Its POST allowlist is repository pick, run, approval, new
  run, and saved-default revocation.
- `decision_os/companion/static/index.html` presents one repository, one bounded
  task, progress, result, runtime identity, Verified Save Receipt, saved exact
  repository access, and a file-change approval card.

### Task and execution routing

- `CompanionController.start_run()` accepts one non-empty task string with a
  20,000-character limit, prevents overlapping Runs, and starts one background
  worker.
- The task string is passed to one fresh Codex app-server thread. The Companion
  state file persists only the last repository path; it rejects additional
  persisted fields. No task, Pro artifact, finding, or receipt artifact is
  persisted in that Companion state file.
- The Codex adapter fixes ChatGPT authentication, model `gpt-5.6-sol`,
  reasoning effort `ultra`, service tier `priority`, and Codex CLI version
  `0.146.0-alpha.3.1`.
- The adapter creates an ephemeral thread in a read-only, no-network sandbox.
  Apps, hooks, multi-agent, remote plugins, shell, MCP dependency installation,
  and other unsupported mutation item types are disabled or fail closed.
- The supported mutation boundary is one exact typed file create or modify.
  Delete, rename, multiple-file mutation, shell execution, MCP, subagents, and
  other unsupported item types do not enter the Verified Save protocol.
- Exact file mutation is routed to a human choice: allow once, save this exact
  repository/action/path default, or deny.

### Local state and Receipt routing

- `AccelerationStore` writes under the selected repository's Git common
  directory:
  `.git/decision-os/acceleration/v0.1/events.jsonl` and `config.json`.
- The event stream is append-only and hash-chained. Each event carries event,
  Run, repository, decision, adapter, status, timestamp, prior-hash, and
  current-hash fields.
- A saved exact access is not counted as verified when created. A later
  cross-Run match must reach a normal terminal checkpoint before it becomes
  `VERIFIED_SAVE`; subsequent verified uses become `VERIFIED_REUSE`.
- The current Receipt contains hard counts for verified saves and reuses,
  configured estimates for recovered minutes, money, and tokens, a
  chain-derived receipt identity, and a claim boundary.
- The Companion's public state intentionally omits the Receipt identity,
  decision key, rule hash, event hash, raw event stream, and raw repository
  identity. It exposes only allowlisted counters, estimates, file action
  summaries, runtime fields, and opaque saved-access handles.

The accepted product surface is explicitly a local one-task Runner, not a true
multi-turn chat client and not a native Codex Desktop interception layer.

## 5. Existing Relevant Files and Entry Points

All blob identities in this section are Git blobs at exact As-of
`63eb260a94595298e2b07b476f7f9d8572c9ef09`.

| Path | Blob SHA | Observed role |
|---|---|---|
| `field_notes/pro_manual_protocol_v0_1.md` | `77e180a4f27298fd066c418b6ea4ccdcb9f40b45` | Fixed Stage 1 manual chain, roles, outputs, repair rule, reusable-delta rule, and human/AI boundary |
| `field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md` | `c4373d0ec121aace1cc8213c907aeb45e85d40f3` | Fixed Stage 2 sequence and separation from Stages 3–5 |
| `validation/v13_sdfp_001_final_closure.md` | `aaa25bf54d4fc2e516de809aa30081622b7ad315` | Prior Golden-like manual evidence chain, method judgment, and exact artifact identities |
| `validation/decision_os_companion_acceptance_run_001.md` | `ffb7a1e09c08ff2bf03a4a284608e35e86a4b6bb` | Accepted current Companion surface, runtime, Receipt, claims, and recorded validation |
| `validation/handoff_acceptance_guard_v0_1_shared_evidence_packet.md` | `502ba73f643e8dabf19a2cbeaa06db3c910a32c5` | Repository-native frozen Shared Evidence Packet convention |
| `handoff/current_codex_handoff.md` | `0d153306c06f9d317a01f245eb9213849deaf61a` | Repository-designated current/historical handoff ledger |
| `docs/current_signal.md` | `cb36230bc49e39d78d6014d39b6ec389cda2fa6d` | Paired current/historical state surface |
| `docs/handoff_command.md` | `7ce12bf250cd486844c568777312064491340112` | Documented repository-native handoff output fields and transfer rules |
| `pyproject.toml` | `836b43f593003967bb7585b4d9ebe71c3cfd9b33` | Package identity and `decision-os` / `decision-os-accelerate` console entries |
| `scripts/build_companion_app.sh` | `98c108fd1f764e26d13dbc5b63a30a870a123141` | Private macOS app/runtime builder |
| `macos/DecisionOSCompanion.applescript` | `55efff60d399919e6b0148d104ed10ceca801f88` | App launcher and local repository picker |
| `decision_os/companion/__main__.py` | `9db18f733ea212a7d0f0988ec9a44b5edf0640a0` | Companion process entry |
| `decision_os/companion/controller.py` | `f6e00defff818a43d81f000e86b8fec83b67a5f4` | Repository choice, one active Run, approval bridge, runtime/result projection, Receipt delta, and revocation |
| `decision_os/companion/server.py` | `1365c673c75d8ebcdf6f0d3799374433c22a766f` | Authenticated localhost API and static allowlist |
| `decision_os/companion/static/index.html` | `5c441218b64f8dd0328e7a996758be3d525335a8` | Existing Companion fields and human controls |
| `decision_os/companion/static/app.js` | `78d072595ea74001b0b0d334b086584d661fecea` | API routing, state rendering, runtime fields, Receipt metrics, approval, and disconnection behavior |
| `decision_os/acceleration/codex_adapter.py` | `372241f30c410ec4edc15826130c679f763b2442` | Codex app-server transport, runtime identity fixation, isolated thread/turn, approval correlation, and terminal proof |
| `decision_os/acceleration/model.py` | `d0df6c7a19e8d330ec9ccd7f81b2a73a9b2c1fb9` | Repository, decision, rule, scope, and canonical hash identities |
| `decision_os/acceleration/store.py` | `05121ae1aeafa034cf6a820a3b83e71c08bc100f` | Hash-chained local events, UTC timestamps, settings, active defaults, counters, and chain head |
| `decision_os/acceleration/engine.py` | `286b681f5e9b2140adc0aced33984731651d2aa1` | Approval/default/checkpoint transitions and current Verified Save Receipt generation |
| `decision_os/acceleration/cli.py` | `51622b407d60d9e0a491a9bd04ffe09e476b456d` | Separate acceleration CLI, live run display, Receipt output, and sanitized receipt-file path |
| `decision_os/cli.py` | `983ddea52c7f22c694a40f44d27db2f4785dafc5` | Repository-local Runner commands including intake and handoff acceptance |
| `decision_os/intake.py` | `184c653b5c9c5c3c03b46e2d79e5722344e1d739` | Existing workflow-incident JSON structural intake; not Pro artifact intake |
| `decision_os/handoff_acceptance.py` | `132621dbe305588ddc5f5868a517814bb37a3891` | Read-only deterministic acceptance assessment of a repository-native handoff; not handoff generation |

The current console entry list has no dedicated Companion command. The `.app`
invokes the Companion module directly. The existing `decision-os intake`
contract is for a workflow incident packet and does not accept Pro Design or
Pro Audit artifacts.

## 6. Existing Handoff / Receipt / Identity Structures

### Repository-native handoff structure

`docs/handoff_command.md` requires:

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

The document requires `UNKNOWN` instead of inferred closure, distinguishes
receiving ownership from naming a next owner, and prevents unresolved routine
work from being returned to Shin.

`decision_os handoff-accept` implements a read-only assessment of one existing
handoff artifact. It binds repository, target layer, expected receiver, local
Git state, current record, branch, owner, completion, and authority-related
relations. Active-transfer prose routes to semantic review; only a bounded
closed-state conjunction can be mechanically accepted. It does not generate or
rewrite a handoff.

No code path was found that converts a Pro artifact into an execution handoff.

### Current Verified Save Receipt

The existing Receipt is not a Manual Protocol Build or Audit Receipt. It records:

```text
hard:
verified save count
verified reuse count

estimated:
recovered minutes
human-time value in JPY
tokens or UNKNOWN

identity:
SHA-256 derived from the verified event-chain head

claim boundary:
local proof-of-use, not third-party certification
```

The estimates come from configurable per-reuse inputs. They are not measured
human handling time, provider pricing, realized value, task correctness,
finding capture, audit result, or reusable-delta evidence.

### Existing identity families

| Identity family | Existing repository behavior | Boundary for Stage 2 |
|---|---|---|
| Repository identity | Credential-free origin or local root is hashed into `repo:v1:<sha256>` | Does not expose an As-of commit and does not grant authority |
| Decision identity | Repository, exact action type, and normalized exact path form a decision key and rule hash | Applies to file approval defaults, not artifact role or Manual Protocol stage |
| Event identity | UUID event ID, UTC timestamp, Run ID, previous event hash, and event hash | Does not identify a Pro artifact or Golden Artifact Set |
| Run identity | UUID Run ID; app-server thread and turn identities are correlated internally | Companion public result does not persist a Manual Protocol Run record |
| Runtime identity | Authentication, model, effort, tier, and CLI version are verified and displayed | Identifies the Codex execution runtime only; it does not identify a Pro model or grant authority |
| Receipt identity | Derived from the current event-chain head in the engine | Omitted from the Companion's public Receipt projection |
| Git artifact identity | Commits and blob/SHA-256 values are recorded manually in validation artifacts | No Companion path fixes imported artifact bytes to a commit/blob/SHA-256 |
| Role identity | Scout, Pro Designer, Builder, Pro Auditor, and Reusable Delta Owner exist in the manual protocol | No Companion field or runtime structure binds a role identity |
| Time identity | Event timestamps and saved-default `created_at` are implemented | No Manual Protocol artifact time anchor or imported-artifact time fixation exists |

### Existing approval and authority boundary

The current product has a concrete human approval boundary for exact file
changes:

```text
Allow once
Use for this repository
Deny
```

`Use for this repository` is limited to one repository, one action type, and one
exact path. Later reuse is not verified until a normal terminal checkpoint.
Revocation preserves historical proof.

This approval structure is evidence of an existing bounded authority surface.
It is not evidence that importing, hashing, displaying, or storing a Pro
artifact authorizes execution. The Manual Protocol separately states that
artifact identity is necessary evidence but does not grant authority.

## 7. Implemented vs Documented vs Absent Matrix

The status labels in this section mean:

```text
IMPLEMENTED:
current repository code and test or accepted execution evidence establish the
bounded behavior.

PARTIALLY IMPLEMENTED:
a narrower existing behavior supplies some of the named facts, but not the
Stage 2 behavior.

DOCUMENTED ONLY:
repository prose fixes a convention or requirement with no matching Companion
execution path found.

ABSENT:
bounded searches of current Companion, acceleration, Runner, and relevant tests
found no matching implementation or dedicated surface.

UNKNOWN:
the canonical repository does not establish the fact.
```

| Capability | Status | Repository evidence and boundary |
|---|---|---|
| Local repository selection | `IMPLEMENTED` | Companion picker validates a local Git root and intact acceleration state |
| One bounded task intake | `IMPLEMENTED` | One 20,000-character task enters one fresh Run |
| Fresh Codex thread and turn | `IMPLEMENTED` | Adapter creates an ephemeral read-only, no-network thread and correlated turn |
| Codex runtime identity | `IMPLEMENTED` | ChatGPT, model, effort, tier, CLI, cwd, sandbox, approval policy, and reviewer are checked |
| Exact file-change approval | `IMPLEMENTED` | Allow once / repository default / deny for one typed create or modify |
| Saved exact access verification | `IMPLEMENTED` | Cross-Run match plus normal terminal checkpoint produces Verified Save/Reuse |
| Hash-chained local event state | `IMPLEMENTED` | Canonical JSON event chain with timestamp, prior hash, and event hash |
| Existing Verified Save Receipt | `IMPLEMENTED` | Hard verified counts, estimates, chain-derived receipt identity, claim boundary |
| Existing workflow incident intake | `IMPLEMENTED` | Separate JSON packet validator; it is not a Stage 2 or Pro artifact intake |
| Existing handoff acceptance | `IMPLEMENTED` | Read-only assessment of an existing repository-native handoff |
| Repository-native handoff format | `DOCUMENTED ONLY` for generation | Required fields and rules exist; no generator code was found |
| `Copy for Pro` | `ABSENT` | Exact Stage 2 phrase occurs in the roadmap, not current product/test code |
| Pro Design import | `ABSENT` | No dedicated upload, paste, file-import, or Pro Design endpoint/state was found |
| Pro Audit import | `ABSENT` | No dedicated upload, paste, file-import, or Pro Audit endpoint/state was found |
| Artifact-byte hash fixation | `PARTIALLY IMPLEMENTED` | Generic event and repository hashing exist; no imported Pro artifact hash fixation exists |
| As-of commit fixation | `DOCUMENTED ONLY` | Manual validation artifacts record commits; Companion state and Receipt do not |
| Model fixation for imported Pro artifact | `ABSENT` | Codex execution model is fixed; imported Pro model identity has no product field |
| Role fixation | `DOCUMENTED ONLY` | Manual roles exist in Stage 1 prose; no Companion role field exists |
| Manual artifact time fixation | `PARTIALLY IMPLEMENTED` | Events have UTC timestamps; manual artifacts/imports have no Companion time anchor |
| Execution handoff generation | `DOCUMENTED ONLY` | Handoff contract exists; no Pro-artifact-to-handoff product path was found |
| Finding capture | `DOCUMENTED ONLY` | Manual Protocol and roadmap name findings; current Receipt has no finding field |
| Human/execution cost capture | `PARTIALLY IMPLEMENTED` | Per-reuse estimates exist; Golden Run burden and actual cost observations do not |
| Reusable Delta capture | `DOCUMENTED ONLY` | Manual Protocol defines qualifying reusable forms; current product has no delta record |
| Golden Artifact Set fixation | `ABSENT` | No Bridge-specific artifact set, manifest, fixture, or product state exists |
| Golden Replay execution | `ABSENT` | No Replay path or comparison result exists |
| Protocol / Product / Replay result separation | `DOCUMENTED ONLY` in this task boundary | No current product result structure carries all three |
| UNKNOWN preservation | `PARTIALLY IMPLEMENTED` | Token estimate and repository governance preserve UNKNOWN; no Bridge-wide field contract exists |
| Imported-artifact execution authority guard | `ABSENT` | No import exists; manual authority rules prohibit treating identity as permission |

Bounded repository-wide searches found the exact Stage 2 phrases `Copy for Pro`,
`Paste Pro Design`, and `Paste Pro Audit` only in the provisional roadmap.
Searches of current product and relevant tests found no Bridge, Golden Run,
Golden Replay, Pro-role, artifact-import, or Pro-to-handoff implementation.

## 8. Stage 2 Fixed Requirements

The future bounded Bridge must support this sequence:

```text
Copy for Pro
→ Pro Design / Pro Audit import
→ hash / model / role / time fixation
→ execution handoff generation
→ finding / cost / reusable delta Receipt
```

The independent Pro Designer must preserve the difference between:

- an observed repository fact;
- an imported artifact's byte identity;
- a model identity;
- a role identity;
- a time anchor;
- an As-of commit or artifact hash;
- an authority grant;
- a result claim.

The Stage 2 target is bounded to the existing Companion and its repository-native
handoff, receipt, identity, and execution-routing surfaces.

The Stage 2 target does not include:

```text
Guided Intake
Multi-Agent Roles
LoopKit Orchestra
automatic model routing
automatic Pro invocation
public SaaS
external-user adoption
pricing
market claims
```

Existing candidate surfaces may be observed in sections 4–7. This packet does
not rank them, select among them, or require that the later design reuse any
particular internal component.

## 9. Manual Golden Run Artifact Set

V13-PMR-002 will create the first Golden Run for the Bridge through the fixed
manual process.

The frozen Golden Artifact Set is:

```text
1. Evidence Packet
2. Pro Design Packet
3. Execution Handoff
4. Build Receipt
5. Pro Audit Receipt
6. Reusable Delta Record
```

This file is artifact 1. Artifacts 2–6 have not started and do not exist at this
packet freeze.

Each later artifact must retain its own role, authority boundary, source
identity, time anchor, result boundary, `UNKNOWN`s, and next actor. One
artifact's completion must not silently complete another stage.

The Golden Artifact Set is a frozen comparison source for later Replay. It is
not an implementation specification, certification, merge approval, or product
PASS.

## 10. Future Replay Comparison Fields

After Companion Manual Bridge v0.1 is implemented under later authority, the
same fixed materials will be passed through the Bridge.

The Replay compares structural preservation, not exact prose identity.

Required comparison fields:

```text
Task ID
Objective
Completion Line
Do Not Touch
Current Gate
Authority Boundary
As-of commit / artifact hash
Model identity
Role identity
Time anchor
Required next actor
Findings
Human / execution cost
Reusable Delta
UNKNOWNs
```

The future comparison must expose loss, alteration, substitution, or authority
inflation for each field. Absence or fluent reformulation must not be converted
into a preserved field without evidence.

Three results remain independent:

```text
Protocol Result:
Did Pro Manual Protocol Run 002 execute correctly?

Product Result:
Did Companion Manual Bridge v0.1 satisfy its bounded design?

Replay Result:
Did the Bridge preserve the Golden Run structure without authority inflation,
field loss, or false completion?
```

No one result implies either of the other two. Do not collapse them into one
`PASS`.

## 11. Baseline Human-Burden Observation Fields

The manual Golden Run must use this minimal observation sheet:

| Observation | Packet-freeze value |
|---|---|
| Shin manual transfer count | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |
| Shin copy/paste count | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |
| Shin re-explanation count | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |
| Shin boundary-correction count | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |
| Shin operational intervention count | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |
| Human handling time | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |
| Total elapsed time | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |
| Number of Pro calls | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |
| Number of Builder repairs | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |
| Number of reusable deltas | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |
| Fields lost or altered during transfer | `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN` |

The current Verified Save Receipt's estimated recovered minutes, money, and
tokens are not values for this sheet. They measure a different local
proof-of-use protocol and do not establish actual Golden Run handling cost.

This packet makes no improvement promise and invents no baseline.

## 12. Existing Tests and Guards Relevant to the Future Design

### Accepted current product evidence

`validation/decision_os_companion_acceptance_run_001.md` records:

```text
Focused Companion tests:
16 / 16 PASS

Focused Codex adapter tests:
31 / 31 PASS

Full repository suite:
244 / 244 PASS

Protected v0.1 blob/mode guard:
PASS

git diff --check:
PASS
```

These are preserved acceptance-run results. This Scout does not reclassify them
as proof of any Bridge behavior.

### Current relevant test files

| Path | Blob SHA | Existing guard surface |
|---|---|---|
| `tests/test_companion_controller.py` | `ded30817e6f248f3ede241c59ee0d7eab94e1f51` | repository validation, minimal state, one task, approval choices, reuse Receipt delta, revocation, one active Run, sanitized failures |
| `tests/test_companion_server.py` | `88473b688cafa92491642bb81238e58376e2f3b6` | bootstrap/session, Host/Origin/CSRF, static allowlist, script-safe rendering, reconnect, opaque handles, sanitized corruption |
| `tests/test_acceleration_codex_adapter.py` | `1d31ed46a1628046723048ee0a141204ba29d3cd` | runtime identity, fresh threads, terminal checkpoints, exact file actions, unsupported mutations, request correlation, model reroute fail-closed |
| `tests/test_acceleration_engine.py` | `42764f7322553a4c9d4d4beb5cdc944606ad8330` | cross-Run verification, abnormal terminal pending, revocation, estimates/privacy, UNKNOWN tokens |
| `tests/test_acceleration_store.py` | `ef59140035a0aa9e2791c78fa58ad76ac86f7a02` | Git-common-dir state, reproducible hash chain, corruption stop, scope safety, credential-free repository identity |
| `tests/test_decision_os_handoff_acceptance.py` | `5d676c53856504e22e57fb304b003a5ebc2a1af8` | current/historical separation, repository/branch/owner relations, UNKNOWN, semantic review, local Git closed-state compatibility, deterministic read-only/non-echo behavior |
| `tests/test_decision_os_scan_cli.py` | `cbe3dbae31a8103064caa5ac9b2c7a313ab5b164` | protected v0.1 blob/mode identities for the earlier Runner contract |

Existing guards establish important negative boundaries:

- runtime or model identity mismatch fails closed;
- a model reroute prevents pending verification promotion;
- an abnormal terminal remains pending;
- a completed file change without correlated approval is unsupported;
- a post-approval patch change cannot promote;
- command execution, MCP, subagents, and other unsupported items fail closed;
- local event-chain corruption blocks reads and future appends;
- only exact repository/action/path saved access is reused;
- active-transfer handoff prose is never automatically accepted;
- `UNKNOWN`, dirty state, detached state, branch mismatch, untracked state, and
  unmerged state do not become a closed-state PASS.

No current test names or fixtures mention Companion Manual Bridge, Copy for Pro,
Pro Design import, Pro Audit import, Golden Run, Golden Replay, Bridge finding
Receipt, or Reusable Delta Receipt.

## 13. Protected Invariants

The independent Pro Designer and every later actor must preserve at minimum:

```text
Shin remains Decision Owner.

Artifact identity does not grant authority.

Model identity does not grant authority.

Importing a Pro artifact does not authorize execution.

Design and Audit remain distinct roles.

Builder completion is not independent completion.

Routine execution and cleanup are not returned to Shin.

As-of, hash, role, model, and time remain separately visible.

UNKNOWN is not converted into PASS.

Golden Replay does not become self-certification.
```

Additional existing repository boundaries remain in force:

- V12 completion and V13 next-loop permission are separate judgments.
- A saved approval default is exact and revocable; historical proof remains.
- A normal terminal checkpoint is required before matched access is called
  verified.
- Current/historical handoff material must not be conflated.
- Handoff information is not a substitute for explicit receiving ownership.
- A Pro Designer may design from this packet but may not write to the repository
  or treat an `UNKNOWN` as known.
- Later Builder and Auditor roles require separate authority and separate
  receipts.

## 14. Do Not Touch

This Scout must not and did not:

```text
choose the Bridge architecture
recommend the final UI
write production code
write tests
modify Companion
modify Runner
modify current handoff
modify current signal
modify roadmap
modify Stage 1 protocol
create a Product PR
merge anything
start Pro Design
start implementation
perform historical cleanup
```

The change boundary is exactly:

```text
validation/companion_manual_bridge_v0_1_shared_evidence_packet.md
```

Observed candidate surfaces in this packet are facts, not recommendations. No
candidate is ranked or selected.

## 15. Known UNKNOWNs

### Golden Run facts not yet observed

- Pro Designer model identity:
  `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN`.
- Pro Auditor model identity:
  `UNKNOWN — TO BE OBSERVED DURING GOLDEN RUN`.
- Exact Pro Design Packet bytes, hash, role time, and findings: `UNKNOWN`.
- Exact Execution Handoff bytes, hash, and receiving actor: `UNKNOWN`.
- Exact Build Receipt bytes, findings, execution cost, and repair count:
  `UNKNOWN`.
- Exact Pro Audit Receipt bytes, result, findings, and repair route: `UNKNOWN`.
- Exact Reusable Delta Record bytes and number of qualifying deltas: `UNKNOWN`.
- All human-burden values in section 11: `UNKNOWN`.

### Current repository facts not established

- Whether the currently installed private `.app` runtime bytes equal the As-of
  repository bytes: `UNKNOWN`. The acceptance record proves its recorded Run,
  not current installed-runtime parity at this packet freeze.
- Whether any unobserved local, installed, or external artifact already uses the
  Stage 2 phrases or structure: `UNKNOWN`. This packet claims absence only for
  the bounded canonical worktree searches described here.
- Whether the Companion's existing event store, controller, server, or UI should
  be reused by the Bridge: `UNKNOWN / DESIGN-OPEN`.
- Whether the existing Verified Save Receipt identity should be exposed,
  extended, or kept separate: `UNKNOWN / DESIGN-OPEN`.
- The authoritative repository path for later artifacts 2–6:
  `UNKNOWN / NOT FIXED BY THIS SCOUT`.
- Exact import transport, storage lifetime, display form, normalization,
  validation, and comparison method: `UNKNOWN / DESIGN-OPEN`.
- Exact structural-preservation evaluation method beyond the fixed fields in
  section 10: `UNKNOWN / DESIGN-OPEN`.
- Exact handling of equivalent prose variants: `UNKNOWN / DESIGN-OPEN`.
- Exact relationship between a generated execution handoff and
  `decision-os handoff-accept`: `UNKNOWN / DESIGN-OPEN`.

### Result UNKNOWNs

- Protocol Result: `UNKNOWN — RUN 002 HAS NOT COMPLETED`.
- Product Result: `UNKNOWN — BRIDGE HAS NOT BEEN DESIGNED OR BUILT`.
- Replay Result: `UNKNOWN — REPLAY HAS NOT OCCURRED`.
- Whether the Bridge will reduce manual transfers, time, corrections, tokens,
  or other burden: `UNKNOWN`.

These `UNKNOWN`s must not be converted into design facts or PASS conditions.

## 16. Evidence Gaps

The following evidence does not exist in the canonical As-of worktree:

- a Bridge-specific product module, endpoint, command, UI control, schema,
  fixture family, or test suite;
- a Copy for Pro output;
- an imported Pro Design sample;
- an imported Pro Audit sample;
- a Bridge artifact manifest;
- a Bridge execution handoff;
- a Bridge finding/cost/reusable-delta Receipt;
- a Golden Artifact Set manifest;
- a Golden Replay output;
- measured Manual Golden Run burden data;
- a three-result Protocol/Product/Replay record.

The first operative blocks of the current handoff and current signal also lag
the As-of Git main identity. This is exposed repository evidence, not authority
for the Scout to repair either surface.

These are evidence gaps, not permission to invent architecture. The later Pro
Designer must either design explicit handling within the fixed boundary or
preserve the relevant fact as `UNKNOWN`.

The following excluded roadmap stages and claims are not evidence gaps for
Stage 2:

```text
Guided Intake
Multi-Agent Roles
LoopKit Orchestra
automatic model routing
automatic Pro invocation
public SaaS
external-user adoption
pricing
market claims
```

## 17. Exact Evidence Anchors

All line anchors refer to blobs listed in section 5 at the exact As-of commit.

### Stage and authority anchors

- `field_notes/pro_manual_protocol_v0_1.md:13-33` — required task-boundary
  fields, HOLD on incomplete boundary, and artifact identity without authority.
- `field_notes/pro_manual_protocol_v0_1.md:35-51` — fixed roles, inputs,
  outputs, exit gates, and prohibitions.
- `field_notes/pro_manual_protocol_v0_1.md:53-64` — required artifact family,
  repository-native prose, and receipt authority boundary.
- `field_notes/pro_manual_protocol_v0_1.md:66-78` — one bounded forward-only
  repair and new-Gate stop.
- `field_notes/pro_manual_protocol_v0_1.md:80-98` — qualifying Reusable Delta
  forms and traceability.
- `field_notes/pro_manual_protocol_v0_1.md:100-110` — Shin/AI boundary and
  routine execution ownership.
- `field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md:86-117` — Stage 1
  then fixed Stage 2 sequence and objective.
- `field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md:118-157` — separate
  Stages 3–5.
- `field_notes/loopkit_orchestra_provisional_roadmap_v0_1.md:175-200` —
  preserved UNKNOWNs and roadmap HOLD.

### Accepted Companion anchors

- `validation/decision_os_companion_acceptance_run_001.md:57-86` — accepted
  `.app`, localhost UI, fixed runtime, and one-task Runner.
- `validation/decision_os_companion_acceptance_run_001.md:91-118` — fresh
  process, exact access match, normal completion, and reused label boundary.
- `validation/decision_os_companion_acceptance_run_001.md:120-150` — event
  chain, checkpoint, Verified Save, and Verified Reuse.
- `validation/decision_os_companion_acceptance_run_001.md:171-186` — existing
  Receipt and estimate claim boundary.
- `validation/decision_os_companion_acceptance_run_001.md:188-208` — local
  acceptance claims and explicit non-claims.
- `validation/decision_os_companion_acceptance_run_001.md:217-246` — recorded
  validation receipt.

### Companion entry and task anchors

- `scripts/build_companion_app.sh:4-13` — private app/runtime target identity.
- `scripts/build_companion_app.sh:42-79` — compiled app, copied runtime, backups,
  and installation.
- `macos/DecisionOSCompanion.applescript:1-22` — repository picker and module
  launch.
- `decision_os/companion/__main__.py:23-49` — controller/server/bootstrap
  process.
- `decision_os/companion/controller.py:87-94` — persisted Companion state path.
- `decision_os/companion/controller.py:175-224` — last-repository-only persisted
  state and restrictive file permissions.
- `decision_os/companion/controller.py:226-260` — repository validation and
  picker.
- `decision_os/companion/controller.py:267-292` — one active Run and bounded
  task intake.
- `decision_os/companion/controller.py:310-359` — exact approval bridge and
  human choices.
- `decision_os/companion/controller.py:361-432` — adapter execution, runtime
  projection, file actions, result, and Receipt delta.
- `decision_os/companion/controller.py:477-526` — public Receipt projection and
  current-Run delta.
- `decision_os/companion/controller.py:582-612` — public Companion snapshot and
  supported boundary.

### Server and UI anchors

- `decision_os/companion/server.py:27-61` — static allowlist, security policy,
  private tokens, and loopback bind.
- `decision_os/companion/server.py:127-176` — Host, Origin, session, and CSRF
  checks.
- `decision_os/companion/server.py:211-244` — authenticated state and static
  reads.
- `decision_os/companion/server.py:272-319` — complete POST endpoint allowlist.
- `decision_os/companion/static/index.html:10-20` — private local Runner and
  locked runtime display.
- `decision_os/companion/static/index.html:23-58` — repository and one bounded
  task controls plus unsupported surface statement.
- `decision_os/companion/static/index.html:72-122` — result, runtime, Receipt,
  and saved exact access surfaces.
- `decision_os/companion/static/index.html:127-155` — approval card and three
  human choices.
- `decision_os/companion/static/app.js:47-76` — Receipt metrics and UNKNOWN
  tokens.
- `decision_os/companion/static/app.js:93-171` — file action, runtime, result,
  and approval rendering.
- `decision_os/companion/static/app.js:206-242` — public state routing to current
  UI surfaces.
- `decision_os/companion/static/app.js:323-408` — current GET/POST routing and
  polling; no artifact import or handoff-generation route.

### Identity, event, and Receipt anchors

- `decision_os/acceleration/model.py:16-58` — protocol event types and exact
  event fields.
- `decision_os/acceleration/model.py:91-123` — decision identity and canonical
  SHA-256 helpers.
- `decision_os/acceleration/model.py:188-205` — hashed credential-free
  repository identity.
- `decision_os/acceleration/model.py:207-245` — exact normalized file scope.
- `decision_os/acceleration/model.py:248-301` — decision key, rule hash, and
  derived identity.
- `decision_os/acceleration/store.py:32-71` — saved-default identity, created
  time, estimate settings, and UTC clock.
- `decision_os/acceleration/store.py:78-101` — Git-common-dir state location.
- `decision_os/acceleration/store.py:103-168` — full event-chain verification.
- `decision_os/acceleration/store.py:170-227` — append fields, timestamp, and
  event hash.
- `decision_os/acceleration/store.py:229-309` — separate configurable estimate
  inputs.
- `decision_os/acceleration/store.py:311-379` — active exact access and
  `created_at`.
- `decision_os/acceleration/store.py:381-411` — verified keys, counters, and
  chain head.
- `decision_os/acceleration/engine.py:61-193` — exact decision check, saved
  default match, and human approval outcomes.
- `decision_os/acceleration/engine.py:195-264` — normal checkpoint requirement
  and Verified Save/Reuse promotion.
- `decision_os/acceleration/engine.py:364-443` — current Receipt fields,
  chain-derived identity, estimates, and UNKNOWN tokens.

### Codex runtime and authority anchors

- `decision_os/acceleration/codex_adapter.py:18-35` — bundled runtime identity
  constants and bounded developer instruction.
- `decision_os/acceleration/codex_adapter.py:36-66` — unsupported item and
  request surface.
- `decision_os/acceleration/codex_adapter.py:77-145` — runtime, Run, approval,
  lifecycle, and file-action structures.
- `decision_os/acceleration/codex_adapter.py:487-561` — ChatGPT account and
  required model catalog checks.
- `decision_os/acceleration/codex_adapter.py:563-650` — fresh ephemeral thread,
  disabled features, identity checks, and read-only sandbox.
- `decision_os/acceleration/codex_adapter.py:652-701` — turn input, exact model,
  effort, service tier, no network, and cwd.
- `decision_os/acceleration/codex_adapter.py:723-819` — presentation-safe
  approval and terminal-aware access labels.
- `decision_os/acceleration/codex_adapter.py:834-879` — exactly one create or
  modify; delete, rename, and other shapes unsupported.
- `decision_os/acceleration/codex_adapter.py:907-1028` — correlated approval,
  exact decision evaluation, and accept/decline.
- `decision_os/acceleration/codex_adapter.py:1173-1208` — runtime identity
  invalidation on settings mismatch.
- `decision_os/acceleration/codex_adapter.py:1278-1376` — full Run, terminal
  conditions, checkpoint promotion, and final result.

### Handoff anchors

- `docs/handoff_command.md:3-8` — handoff transfers current state and starts no
  new work.
- `docs/handoff_command.md:10-24` — required repository-native fields.
- `docs/handoff_command.md:26-39` — UNKNOWN, ownership, routine-work,
  no-authority, and Completion Line rules.
- `decision_os/handoff_acceptance.py:23-103` — result/mode/issue registries and
  thirteen canonical handoff fields.
- `decision_os/handoff_acceptance.py:225-250` — local Git and input snapshot
  identities used by the acceptance guard.
- `decision_os/cli.py:68-88` — handoff-accept option and process boundaries.
- `decision_os/cli.py:594-628` — handoff assessment execution and safe result
  routing.
- `decision_os/cli.py:631-691` — current Runner command dispatch.

### Test anchors

- `tests/test_companion_controller.py:214-271` — repository picker and minimal
  state persistence.
- `tests/test_companion_controller.py:273-360` — read-only zero Receipt and
  three approval choices.
- `tests/test_companion_controller.py:362-430` — cross-Run Receipt delta,
  revocation, reconnect, and one active Run.
- `tests/test_companion_controller.py:432-487` — sanitized failures and corrupt
  chain stop.
- `tests/test_companion_server.py:110-210` — session/security/static/no-script
  guards.
- `tests/test_companion_server.py:212-313` — one active Run, reconnect, and
  opaque public default handle.
- `tests/test_acceleration_engine.py:33-183` — verification, pending, override,
  and history preservation.
- `tests/test_acceleration_engine.py:184-228` — Receipt estimates/privacy and
  UNKNOWN token guard.
- `tests/test_acceleration_store.py:32-118` — reproducible chain and corruption
  stop.
- `tests/test_acceleration_store.py:119-179` — exact scope and credential-free
  repository identity.
- `tests/test_acceleration_codex_adapter.py:1132-1323` — machine identity and
  mismatch fail-closed tests.
- `tests/test_acceleration_codex_adapter.py:1385-1576` — unsupported mutation,
  command, MCP, and subagent boundaries.
- `tests/test_acceleration_codex_adapter.py:1815-1969` — unapproved completion,
  patch change, and unresolved request cannot promote.
- `tests/test_acceleration_codex_adapter.py:2165-2211` — model reroute prevents
  promotion.
- `tests/test_decision_os_handoff_acceptance.py:166-198` — active native handoff
  routes to semantic review.
- `tests/test_decision_os_handoff_acceptance.py:406-477` — closed-state local
  Git identity and dirty/detached/branch guards.
- `tests/test_decision_os_handoff_acceptance.py:513-579` — UNKNOWN, owner work,
  completion, and state/gate guards.
- `tests/test_decision_os_handoff_acceptance.py:819-963` — read-only local Git
  safety and unresolved operation guards.
- `tests/test_decision_os_handoff_acceptance.py:1054-1159` — deterministic,
  unstable-snapshot, and trusted-scalar guards.

## 18. Packet Blob SHA

```text
Value:
NOT EMBEDDED — SELF-REFERENTIAL IDENTITY

Authoritative fixation:
Git blob SHA of
validation/companion_manual_bridge_v0_1_shared_evidence_packet.md
at the Scout packet-freeze commit.

Reporting surface:
Scout completion receipt.
```

Adding the literal blob SHA to this file would change the Git blob. The external
commit receipt is the repository-native authoritative location for the value.

## 19. Packet SHA-256

```text
Value:
NOT EMBEDDED — SELF-REFERENTIAL IDENTITY

Authoritative fixation:
SHA-256 of the exact committed packet bytes.

Reporting surface:
Scout completion receipt.
```

Adding the literal file SHA-256 to this file would change the file bytes. The
external completion receipt records the value computed from the committed
packet.

## 20. Exit Gate

Successful Scout exit:

```text
READY FOR INDEPENDENT PRO DESIGN
```

This exit applies only when:

- the exact As-of state remains verified;
- this packet is the only changed file;
- the packet is committed and pushed on
  `codex/v13-cmb-001-shared-evidence-freeze`;
- local and remote branch heads match;
- `main` remains unchanged;
- the worktree is clean;
- no PR, design, implementation, test change, merge, or cleanup occurred.

If those conditions are not met:

```text
HOLD — EVIDENCE INSUFFICIENT
```

Repository identity mismatch remains:

```text
HOLD — AS-OF REPOSITORY IDENTITY MISMATCH
```

After successful freeze, the sole next owner is:

```text
Independent Pro Designer
```
