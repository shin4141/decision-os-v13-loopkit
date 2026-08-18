# V13 Causal Trajectory

This is the thin, append-only causal spine for meaningful V13 frontier
movement. It is not an activity log, evidence authority, or a replacement for
PRs, Field Notes, validation evidence, handoffs, `docs/current_signal.md`, or
other canonical artifacts. Every claim must remain traceable to an evidence
anchor outside this trajectory.

After the bootstrap boundary below, append one causal delta only when the
frontier meaningfully moves or stops. Never silently revise an earlier entry
using later understanding. Append corrections, retractions, or improved
interpretations as later deltas and preserve the earlier As-of judgment.

## RETROSPECTIVE CAUSAL RECONSTRUCTION

These entries were reconstructed on 2026-08-12 from the evidence available at
this As-of. They were not recorded contemporaneously. Historical source
artifacts were not altered. Repository canonical main for this reconstruction
is `9566cc4fa442633a0885fa8d2f1180979b2078ee` in
`shin4141/decision-os-v13-loopkit`; the Decision Owner is Shin.

The reconstruction is deliberately incomplete. It preserves only the minimum
spine from the 13-36 blank-slate self-improvement frontier to the present F-01
Broker-bound contract frontier.

### 1. Blank-slate self-improvement moved to independent blind audit

**AS-OF**

Retrospective reconstruction at 2026-08-12 of the 13-36 frontier and its later
independent-audit transition.

**FRONTIER**

V13 was selecting endogenous improvements from a blank slate. Repeated
selection could improve the system while leaving uncertainty about what an
independent model seat would find without inheriting the same candidate frame.

**CAUSAL DELTA**

Previous state: endogenous blank-slate self-improvement. Question: would a
blind, independent model audit converge, expand coverage, or falsify the
system's own diagnosis? Observation: the audit could exclude prior candidate
lists, recent winners, self-improvement reasoning, current signals, handoffs,
Field Notes, and history from initial candidate generation. Why the frontier
moved: independent comparison became more valuable than another same-seat
candidate round, so the frontier moved to Cross-Model Blind Structural Audit
001.

**EVIDENCE ANCHOR**

- `docs/current_signal.md` and `handoff/current_codex_handoff.md`, historical
  13-121 and 13-124 blank-slate selection blocks at canonical main
  `9566cc4fa442633a0885fa8d2f1180979b2078ee`.
- `validation/cross_model_blind_structural_audit_001.md` at evidence commit
  `34ff1e2d2ce0cf4b883a561a8da7e9e79e846e1d`, especially the Identity and
  Blindness Boundary sections. This evidence commit is not an ancestor of the
  stated canonical main and is not represented here as canonical main.
- Decision Owner 13-143 bootstrap instruction for the 13-36 starting boundary.

**GATE**

`CAP` — one bounded blind structural audit; observation only and no repair
authority.

**COMPLETION LINE**

The endogenous frontier was exposed to one independently seated, blinded
structural audit without importing the excluded candidate frame.

**MISSING CLOSURE**

Audit findings still required evidence admission, retraction where falsified,
and separate repair authority.

**RE-ENTRY**

Re-enter from the frozen Audit 001 evidence and classify each finding without
turning audit output into automatic repair authority.

### 2. Audit 001 separated convergence, coverage expansion, and falsification

**AS-OF**

Audit evidence recorded 2026-08-11 at
`34ff1e2d2ce0cf4b883a561a8da7e9e79e846e1d`; reconstructed 2026-08-12.

**FRONTIER**

Cross-Model Blind Structural Audit 001 had candidate findings but had not yet
established which claims survived evidence admission.

**CAUSAL DELTA**

Question: which findings were current defects, and what did cross-seat
comparison actually show? Observation: F-01, an unrecoverable restart lock on
a persisted `ACTIVE` continuation chain, was admitted as independent
cross-seat convergence; F-04, acceptance of negative authority language as an
affirmative witness, was admitted as audit coverage expansion; F-02,
`Authority Match: NO` with an `ACTIVE` run, was fully retracted after the pinned
test and relevant semantics falsified the claim. Why the frontier moved: the
audit produced two admitted defects and one successful cross-seat
falsification, with no observed audit asymmetry established.

**EVIDENCE ANCHOR**

- `validation/cross_model_blind_structural_audit_001.md` at evidence commit
  `34ff1e2d2ce0cf4b883a561a8da7e9e79e846e1d`, sections F-01, F-04, F-02, and
  Audit 001 Result.
- F-02 falsifier:
  `tests/test_decision_os_checks.py::RepositoryChecksTest::test_active_authority_mismatch_can_stop_before_implementation`,
  as identified and executed in that audit record.

**GATE**

`HOLD` — evidence fixed; repair remained unauthorized.

**COMPLETION LINE**

Audit 001 closed as `PASS`: F-01 and F-04 were admitted, F-02 was fully
retracted, and the distinctions between convergence, coverage expansion, and
falsification were preserved.

**MISSING CLOSURE**

F-04 and F-01 remained admitted current defects; neither admission by itself
authorized implementation.

**RE-ENTRY**

Re-enter only under separate defect-specific repair authority, preserving the
F-02 retraction.

### 3. F-04 repair closed canonically and returned the frontier to F-01

**AS-OF**

Canonical main `9566cc4fa442633a0885fa8d2f1180979b2078ee`, 2026-08-12.

**FRONTIER**

F-04 was the admitted authority-witness defect selected for bounded repair;
F-01 remained admitted but deferred.

**CAUSAL DELTA**

Question: could negative authority witnesses fail closed without widening the
accepted authority language or weakening protected validation? Observation:
after F-04 was admitted, initial repair `3f7fddf` received independent
`REVISE` because its open-ended negative denylist still allowed explicit
negative forms. Second repair `eb65fce` also received independent `REVISE`
because malformed or status-shaped `Required Authority` values could still
manufacture valid-looking `Authority Held`. Type-bound v3 `3698ac7` recovered
the pre-repair positive contract and type-bound the two witness roles; the
independent semantic review then returned `PASS WITH REQUIRED
PROTECTED-IDENTITY RE-ANCHOR`. The authorized re-anchor `b58e8c6` supplied that
protected-identity closure, followed by canonical closure in `9566cc4`. Why the
frontier moved: repeated falsification changed the repair strategy from
phrase-denial patching to type-bound positive authority semantics. With that
lineage canonically closed, the unresolved admitted-defect frontier returned
to F-01.

**EVIDENCE ANCHOR**

- Repair commits `3f7fddf5329725e05d8bf25bd8bc02f356da54af`,
  `eb65fceccfe20d149afb2e577373788e48b77e08`,
  `3698ac7b88e17901b52f547d176a717979685fa4`, and
  `b58e8c66035599da0b9d4afd0753ba0e8d88c761`.
- Canonical merge commit `9566cc4fa442633a0885fa8d2f1180979b2078ee`
  (`Canonicalize F-04 v3 authority witness validation`).
- `decision_os/checks.py`, `tests/test_decision_os_checks.py`, and
  `tests/test_decision_os_scan_cli.py` at that canonical commit.
- Decision Owner 13-145 causal-repair instruction for the independent review
  dispositions and the minimum rejection reasons preserved above.

**GATE**

F-04: `PASS`. F-01 re-entry: `HOLD` until separately bounded.

**COMPLETION LINE**

F-04 repair lineage and canonical closure completed without rewriting Audit
001 or its historical As-of judgment.

**MISSING CLOSURE**

F-01's persisted `ACTIVE` restart-lock defect remained unrepaired.

**RE-ENTRY**

Return to the admitted F-01 defect and establish the minimum safe recovery
contract before production implementation.

### 4. F-01 diagnosis moved from lock state to execution-owner recovery proof

**AS-OF**

Post-canonical F-01 analysis reconstructed 2026-08-12.

**FRONTIER**

F-01 was no longer only a stale-state question. A persisted `ACTIVE` chain
could be restart-locked because current execution ownership and extinction of
the prior mutation-capable execution were not observably established.

**CAUSAL DELTA**

Question: what evidence would make recovery safe rather than merely making the
state writable again? Observation: lock state alone could not prove that the
previous execution owner and every mutation-capable descendant had lost write
authority before a successor acquired it. Why the frontier moved/stopped: the
missing primitive was execution-owner observability, so F-01 recovery fixed a
contract requiring an Execution Fence, CAS/fencing for successor acquisition,
and recovery evidence that orders prior-owner extinction before new authority.

**EVIDENCE ANCHOR**

- F-01 diagnosis in
  `validation/cross_model_blind_structural_audit_001.md` at evidence commit
  `34ff1e2d2ce0cf4b883a561a8da7e9e79e846e1d`.
- `validation/f01_slice1_codex_execution_containment_qualification.json` at
  local qualification commit
  `f506734f6822bd3c63f8dd84b6e82f5a9c72285a`; its repository identity binds
  the work to canonical base `9566cc4fa442633a0885fa8d2f1180979b2078ee`.
- Decision Owner 13-143 bootstrap instruction for the fixed Execution Fence +
  CAS/Fencing + recovery-evidence contract. No canonical implementation
  artifact is claimed.

**GATE**

`HOLD` — contract fixation did not authorize production v0.2 or repository
migration.

**COMPLETION LINE**

F-01 was reframed from “clear `ACTIVE`” to “prove loss of prior mutation
authority before fenced successor acquisition.”

**MISSING CLOSURE**

Real Codex containment had not proved complete writer attribution, descendant
coverage, final fence release, or correctly ordered successor acquisition.

**RE-ENTRY**

Qualify the fixed contract against a real Codex execution in sacrificial
repositories, with no production recovery activation.

### 5. Real Codex qualification stopped at the privacy-compatible observability boundary

**AS-OF**

Local qualification evidence through
`4dec9d0611451a581e4cc0b1b1f2b0692092a9c1`, 2026-08-12; reconstructed the
same day.

**FRONTIER**

The Execution Fence could be exercised against a real Codex process, but the
direct-containment claim required sequence-complete proof across writers,
descendants, fence holders, extinction, and successor acquisition.

**CAUSAL DELTA**

Question: did direct fence inheritance contain every mutation-capable real
Codex execution long enough to make successor recovery safe? Observation: the
typed mutation succeeded and useful containment facts were observed, but a
descendant escaped the original process group, writer attribution remained
incomplete, and short-lived descendant gaps prevented sequence-complete proof.
A privileged Endpoint Security retry was considered, then stopped before
streaming because the installed observer could not pre-delivery restrict both
qualification-owned lineage and qualification-owned file targets. Why the
frontier stopped: direct containment was neither proven nor falsified, and
privacy could not be traded away to close the observability gap.

**EVIDENCE ANCHOR**

- `validation/f01_slice1_codex_execution_containment_qualification.json` at
  local qualification commit
  `f506734f6822bd3c63f8dd84b6e82f5a9c72285a`, disposition
  `QUALIFICATION INCONCLUSIVE`.
- `validation/f01_slice1_sequence_complete_privileged_containment_qualification.json`
  at local qualification commit
  `4dec9d0611451a581e4cc0b1b1f2b0692092a9c1`, disposition
  `QUALIFICATION STILL INCONCLUSIVE` and stop code
  `ESLOGGER_PRIVACY_SCOPE_UNEXPRESSIBLE`.
- Both local evidence branches descend from and explicitly bind canonical main
  `9566cc4fa442633a0885fa8d2f1180979b2078ee`; neither is represented here as
  merged canonical main.

**GATE**

`HOLD` — privacy-preserving, sequence-complete observability was missing.

**COMPLETION LINE**

The real Codex qualification preserved an inconclusive result and stopped
before unauthorized observation; it did not upgrade partial evidence into a
direct-containment proof.

**MISSING CLOSURE**

An observer or architecture was needed that could establish the recovery
ordering while preventing unrelated process or file events from entering the
observation boundary.

**RE-ENTRY**

Re-enter only with privacy-compatible observability or an architecture that
does not depend on proving complete containment from inside the untrusted
execution domain.

### 6. Guardian-only recovery was rejected; the contract became Broker-bound

**AS-OF**

Decision Owner contract frontier reconstructed at the 2026-08-12 13-143
bootstrap As-of.

**FRONTIER**

Direct containment was inconclusive. A Guardian could observe or terminate,
but recovery still required one authority that could prevent repository writes
after ownership transfer and make fencing decisive.

**CAUSAL DELTA**

Question: could a Guardian alone close F-01? Observation: Guardian could make
controller death harmless, but old Codex descendants still retained direct
protected-repository mutation capability independently of Guardian lifecycle.
Accepted privacy boundaries also prevented host-wide, sequence-complete
process-extinction observation from serving as the safety proof. Guardian was
not rejected because its implementation failed, and process-group escape alone
was not decisive: process lifetime could not be the authority boundary. Safe
same-boot recovery instead required structural removal of direct Codex mutation
capability, so Broker became required as the sole protected-repository writer.
Old Codex processes may remain alive only if they are structurally unable to
write. Why the frontier moved: mutation capability, not process liveness or a
generic design preference, became the decisive boundary. Guardian evidence may
inform the Broker but cannot substitute for Broker-owned mutation authority.

**EVIDENCE ANCHOR**

- The two local F-01 qualification records at commits
  `f506734f6822bd3c63f8dd84b6e82f5a9c72285a` and
  `4dec9d0611451a581e4cc0b1b1f2b0692092a9c1` establish the inconclusive
  direct-containment and privacy-observability boundary that forced
  architectural re-entry. They are local/noncanonical qualification evidence,
  not canonical architecture or contract authority.
- Decision Owner 13-143 bootstrap instruction fixes the subsequent
  Guardian-only rejection, Broker requirement, and Broker-bound F-01 contract.
  This trajectory is not the evidence authority for those decisions.
- Decision Owner 13-145 causal-repair instruction preserves the
  architecture-review conclusion that mutation capability, rather than
  process liveness, is the decisive boundary; it does not promote the local
  qualification evidence to canonical authority.

**GATE**

Contract: `PASS`. Implementation: `HOLD` — no Broker, Guardian, production
v0.2, migration, or canonical implementation change is authorized.

**COMPLETION LINE**

The F-01 recovery architecture and contract are fixed as Broker-bound rather
than as direct Codex containment or Guardian-only recovery; F-01 itself remains
open.

**MISSING CLOSURE**

The deployment and security boundary for the privileged Broker remains a Human
Seat decision.

**RE-ENTRY**

Return only for the minimum deployment-boundary decision; do not begin
implementation from contract fixation alone.

### 7. Current frontier: deployment-boundary Human Seat decision

**AS-OF**

2026-08-12; canonical main
`9566cc4fa442633a0885fa8d2f1180979b2078ee`.

**FRONTIER**

**F-01 remains OPEN.** F-04 is canonical / closed. The Guardian-only route is
rejected; the Broker requirement is established; and the Broker-bound contract
is fixed. `Contract: PASS` / `Broker-bound contract fixed` means only that the
recovery architecture and contract are fixed. It does **not** mean F-01 is
repaired, implemented, canonical, or closed. The deployment/security boundary
awaits Human Seat decision. Broker/Guardian implementation, production v0.2,
repository migration, and canonical implementation changes remain
unauthorized.

**CAUSAL DELTA**

Previous state: Broker requirement established. Question: should V13 adopt the
deployment/security boundary needed to make the Broker's authority materially
separate from Codex/UID 501? Observation: the proposed boundary is a root-owned
signed LaunchDaemon, a dedicated non-login Broker UID/group, a root-controlled
protected repository ancestor, read-only protected access for Codex/UID 501, a
separate writable scratch surface, and a root/admin break-glass trust boundary.
Why the frontier stopped: adopting that host trust and deployment boundary is
an authority- and security-bearing Human Seat choice, not an AI-owned
implementation detail.

**EVIDENCE ANCHOR**

- Decision Owner 13-143 task statement, which fixes this exact current frontier
  and its authorization exclusions.
- Canonical repository identity commit
  `9566cc4fa442633a0885fa8d2f1180979b2078ee`.
- Prior causal basis: the two local qualification records at commits
  `f506734f6822bd3c63f8dd84b6e82f5a9c72285a` and
  `4dec9d0611451a581e4cc0b1b1f2b0692092a9c1`.

**GATE**

`HOLD — HUMAN SEAT`. Broker/Guardian implementation, production v0.2,
repository migration, and canonical implementation changes remain
unauthorized.

**COMPLETION LINE**

V13 has one fixed Broker-bound F-01 recovery contract and one exposed Human
Seat decision about the proposed deployment/security boundary; no
implementation authority is implied.

**MISSING CLOSURE**

Shin's decision whether to adopt the stated root/Broker/Codex/repository/
scratch/break-glass boundary.

**RE-ENTRY**

Re-enter from an explicit Human Seat decision. If adopted, require separately
bounded implementation authority. If rejected or revised, append the new
causal delta; do not rewrite this As-of entry.

## APPEND-ONLY BOUNDARY

Everything above this boundary is the retrospective bootstrap. Future entries
are contemporaneous only if their own `AS-OF` says so. Append them below this
line using exactly:

```text
AS-OF
FRONTIER
CAUSAL DELTA
EVIDENCE ANCHOR
GATE
COMPLETION LINE
MISSING CLOSURE
RE-ENTRY
```

An appended entry may correct or supersede an interpretation, but it must name
the prior entry and preserve that prior record unchanged.

### 8. F-01 Host Attempt 1 preserved state but did not qualify Slice 4A

**AS-OF**

2026-08-14 JST, after the single-input sudo authentication-failure re-anchor.

**FRONTIER**

F-01 Slice 4A had attempted to establish distinct host principals. Host
Attempt 1 instead stopped with only the partial `_decisionos_codex` user and
private group remaining at UID/GID 510; principal-separation deployment had
not completed.

**CAUSAL DELTA**

Question: could the partial host identity be safely removed without widening
rollback authority or exceeding the Human Seat interaction boundary?
Observation: multiple bounded recovery routes were attempted, but no deletion
ever completed. No Guardian or Broker principal was provisioned, and no ACL,
protected-repository permission, or sole-writer transition occurred. The
recovery established that Directory Service presentation can vary by observer
context and that privilege escalation does not itself prove mutation
authority. Why the frontier stopped: the stale Codex principal remained while
Human Seat recovery cost reached the fixed CAP boundary, so Host Attempt 1
could not qualify as a Slice 4A deployment.

**EVIDENCE ANCHOR**

- Decision Owner `TIME TUBE — F-01 SLICE 4A / HOST ATTEMPT 1`, As-of
  2026-08-14 JST after the single-input sudo authentication-failure re-anchor;
  this is the authoritative terminal-state and recovery-history record.
- Recovery branch `codex/13-153-rollback-review` through
  `11bc417c2104840676003d2cc3d5f12517e9d13f`, especially
  `validation/f01_slice4a_partial_host_recovery_preparation.md`,
  `validation/f01_slice4a_opendirectory_mutation_artifact.md`,
  `validation/f01_slice4a_observer_password_marker_contract_repair.md`, and
  `validation/f01_slice4a_single_interaction_sudo_transport.md`. These
  preparation artifacts do not supersede the Time Tube or claim completed
  deletion.

**GATE**

`HOLD — HOST ATTEMPT 1 IS NOT A QUALIFIED SLICE 4A DEPLOYMENT`. No next action
is authorized until re-entry path A or B is explicitly selected.

**COMPLETION LINE**

`PASS — POST-FAILURE STATE PRESERVED`: the accepted pre-rollback host state
remains bounded and restartable without representing recovery or Slice 4A as
successful.

**MISSING CLOSURE**

The stale `_decisionos_codex` user/group still occupies UID/GID 510. It must
not be reused or promoted as fresh Slice 4A authority; F-01 remains open and
principal separation remains incomplete.

**RE-ENTRY**

Re-enter only after explicit selection of either A, separately qualified
cleanup of the stale host principal, or B, fresh Slice 4A deployment on a
clean host or clean macOS environment. Do not infer a selection from this
trajectory entry and do not invent another privileged rollback transport.

## 9. F-01 Slice 4A isolated the deployment mechanism before selecting a zero-cost clean execution boundary

Host Attempt 1 closed with only a stale `_decisionos_codex` user/group and no
Guardian, Broker, DecisionOS state tree, ACL promotion, or sole-writer
transition. Its exact accepted Time Tube was later fixed as durable supporting
evidence, while the trajectory/evidence lineage and implementation/recovery
lineage remained deliberately separate.

Path B — clean-host deployment — was selected because cleanup of Host Attempt
1 was not required for forward F-01 progress. The stale host was explicitly
excluded from the new deployment authority and evidence boundary.

A single GitHub-hosted clean macOS capsule then proved that host contamination
was not the only relevant variable. Clean-host qualification passed with all
DecisionOS principal names absent, UID/GID 510–512 free, no prior state tree,
and no ACL authority. Provisioning nevertheless failed closed during the first
Codex principal creation when a post-creation `GeneratedUID` write through the
serial `dscl` mechanism was denied by Directory Services. No Guardian,
Broker, state tree, ACL, or sole-writer authority was reached.

This result did not reproduce Host Attempt 1's recovery failure. Host Attempt 1
had already persisted a Codex GUID and later encountered a separate sandbox
denial during recovery. The two attempts therefore exposed different authority
boundaries rather than one repeated host-contamination failure.

After repeated environment-side hypotheses, an independent Opus audit was
introduced before another costly or privileged attempt. That audit challenged
the existing frame: three-principal separation was being conflated with
implementation choices such as serial `dscl` mutation and post-creation
`GeneratedUID` replacement. Subsequent primary-source audit classified the
strongest supported root cause as deployment mechanism, not architecture.

The falsified implementation assumption was narrowed to:

`EUID 0 alone is a sufficient and portable authority qualification for the
selected Directory Services mutation path.`

The accepted F-01 security contract remained intact. The candidate
forward-only delta replaced bare-record-plus-serial-mutation provisioning with
explicitly authenticated `/Local/Default` OpenDirectory complete-record
creation, preserving fixed identity semantics while moving GUID assignment
into the initial record dictionary.

Design review then separated two different failure properties:

* authority fail-closed;
* state fail-closed.

Because the complete Slice 4A principal set spans multiple user/group records,
the proposed operation is not a true atomic transaction. It is a compensating
transaction whose partial-state behavior, reverse compensation, evidence, and
future re-entry conditions must be explicit.

A scratch-only OpenDirectory mechanism capsule was therefore designed before
any new F-01 production attempt. It tests explicit node authentication,
complete-record creation, fixed GUID assignment, `IsHidden`, disabled-login
semantics, failed-create zero-residue behavior, one-shot deletion, independent
observation, and root-only environment behavior using non-production
identities.

Its control semantics were repaired before execution:

* ambient EUID 0 may or may not possess Directory Services mutation authority
  on a particular host;
* F-01 must never use EUID 0 alone as proof of qualified authority;
* failed complete-record creation is judged primarily by zero persistent state,
  not by one universal numeric error code.

No scratch mechanism execution has yet occurred.

Environment selection was then performed against the frozen capsule contract,
not by provider name. A second internal macOS installation and a local
Virtualization.framework macOS VM were both found technically capable without
new monetary spending. The local VM was selected because it preserves a
separate macOS `/Local/Default` while giving lower ordinary-host risk, stronger
isolation, easier reset, and equivalent zero-new-spend cost.

GitHub-hosted macOS was rejected for the frozen new mechanism because it does
not supply the usable local-administrator credential required for explicit
OpenDirectory node authentication.

External SSD spending is therefore not currently necessary.

Current frontier:

Prepare exactly one fresh owner-controlled local Virtualization.framework
macOS VM and perform non-mutating qualification only. The qualification must
establish the fresh guest `/Local/Default`, VM-local administrator,
explicit-node credential establishment, future EUID-0 path, non-sandboxed
execution, independent observer, and evidence export.

No scratch user/group creation is authorized during this preparation.

If the VM qualification passes, a later separately authorized loop may execute
the already frozen scratch mechanism capsule exactly once.

Current Gate:

`GO — PREPARE SELECTED ZERO-COST ENVIRONMENT`

F-01 remains OPEN.

Slice 4A remains INCOMPLETE.

Host Attempt 1 remains excluded and untouched.

## 10. F-01 VM execution stopped at its resource gate and left the active frontier

**AS-OF**

2026-08-18 JST, trajectory fixation before the GPT 13-40 → 13-41 Handoff.

**FRONTIER**

Entry 9 had selected one owner-controlled local macOS VM preparation path for
F-01 Slice 4A. The preparation surface was built and checked, but the later
fixed host-safety gate observed only 195.84 GiB available against the 214 GiB
pre-start minimum. No VM bundle was created and no Directory Services mutation
or scratch mechanism execution occurred.

**CAUSAL DELTA**

Question: should the prepared VM path proceed into execution? Observation: the
fixed pre-creation resource boundary did not pass, so the VM execution path
failed closed before creation. The Decision Owner now records F-01 / VM as no
longer the active frontier. Why the frontier stopped: preparation did not
create execution authority, and the unmet resource boundary made continuation
inadmissible at that As-of. Parking this line does not rewrite Entry 9 or close
F-01.

**EVIDENCE ANCHOR**

- `/Users/sn/Documents/v13/13-160-f01-slice4a-vm-preparation/README.md`.
- `/Users/sn/Documents/v13/13-160-f01-slice4a-vm-preparation/evidence/host_safety_gate_repair.json`, classification
  `HOLD_CURRENT_FREE_SPACE_BELOW_FIXED_PRE_START_MINIMUM` and
  `vm_created: false`.
- Decision Owner 13-40 trajectory-fixation instruction for the current parked
  status. It does not alter the historical Entry 9 As-of.

**GATE**

`HOLD / PARKED — F-01 AND VM EXECUTION ARE NOT THE ACTIVE FRONTIER`.

**COMPLETION LINE**

The VM path's fail-closed stop and subsequent parking are preserved without
representing preparation, F-01, or Slice 4A as complete.

**MISSING CLOSURE**

F-01 remains open. VM qualification, explicit node authority, scratch
mechanism execution, and every later deployment step remain unperformed.

**RE-ENTRY**

Re-enter only through a fresh Decision Owner selection using current resource,
host-safety, and F-01 authority evidence. Do not infer reactivation from the
existing preparation artifacts.

## 11. Task Envelope and Repo Improver made bounded execution reconstructable

**AS-OF**

2026-08-18 JST, after the Task Envelope qualifications and Repo Improver v0.1
field executions.

**FRONTIER**

With the privileged F-01 path parked, the next useful question was whether an
AI improvement loop could be frozen, bounded, independently reconstructed, and
stopped without acquiring authority from its own success.

**CAUSAL DELTA**

Question: could one autonomous loop operate inside an evidence-bearing fixed
envelope rather than relying on fluent self-report? Observation: Task Envelope
fixed eight authority/scope fields before execution and bound later records in
an append-only hash chain; its independent harness derived completion, gate,
and EV stops while keeping `authority_granted: false`. Repo Improver then
narrowed the execution shape to one repository, one explicit invocation, at
most one selected variable, frozen paths, Before/After proof, and independent
live reconstruction. Why the frontier moved: later field trials now had a
bounded execution substrate that could distinguish a verified local change
from permission for another cycle.

**EVIDENCE ANCHOR**

- `/Users/sn/Documents/v13/13-145-bridge-readiness/docs/task_envelope_v0_1.md`.
- `/Users/sn/Documents/v13/13-145-bridge-readiness/validation/task_envelope_v0_1_codex_native_dogfood_002.jsonl`.
- `/Users/sn/Documents/v13/13-145-bridge-readiness/docs/repo_improver_v0_1.md`.
- `/Users/sn/Documents/v13/13-145-bridge-readiness/validation/v13_governance_receipt_13_174_v0_1.md`.

**GATE**

`PASS — BOUNDED EXECUTION SUBSTRATE OBSERVED`; automatic continuation and
authority inheritance remain prohibited.

**COMPLETION LINE**

One-variable repository work can be frozen, executed, reconstructed, and
terminated without treating harness PASS or local improvement as a new
authority source.

**MISSING CLOSURE**

The substrate does not authenticate actors or commands, prove semantic EV
calibration, establish general completeness, or demonstrate superior raw
repair ability.

**RE-ENTRY**

Use it only inside a separately authorized bounded task. A completed envelope
or Repo Improver run never activates another invocation.

## 12. Same-snapshot controls moved the frontier from raw repair to loop legitimacy

**AS-OF**

2026-08-17–18 JST, after completed 13-173 and 13-174 Normal / Bare Sol control
interpretation was fixed.

**FRONTIER**

Task Envelope and Repo Improver could generate a qualified repair path, but it
remained unknown whether V13 produced better raw repair loops than a capable
GPT-5.6 Sol on the same repository snapshot.

**CAUSAL DELTA**

Question: did the V13 substrate demonstrate raw-repair differentiation, or was
useful loop construction already available to capable Sol? Observation: the
control paths constructed useful inspect → select → implement → verify → stop
loops, while V13's observed difference lay in bounded continuation authority,
independent reconstruction, and durable governance evidence. The fixed result
was `RAW REPAIR DIFFERENTIATION — NOT DEMONSTRATED` and
`PROMPT-STRUCTURE DEPENDENCE — NOT DEMONSTRATED IN THIS SNAPSHOT`. Why the
frontier moved: another repair contest had lower information value than asking
what remains scarce when loop generation is already cheap. The question moved
from repair production toward entry, continuation legitimacy, and stopping.

**EVIDENCE ANCHOR**

- `/Users/sn/Documents/v13/13-173-control-pyscrappy/evidence/measurements.md` and
  `/Users/sn/Documents/v13/13-173-v13-pyscrappy/evidence/04_terminal_summary.md`.
- `/Users/sn/Documents/v13/13-174-control-gren-core/evidence/experiment-notes.md`
  and `/Users/sn/Documents/v13/13-174-v13-gren-core/evidence/trial_record.md`.
- `/Users/sn/Documents/v13/13-145-bridge-readiness/field_notes/135_when_improvement_loops_become_cheap_legitimacy_becomes_scarce.md`,
  which fixes the cross-control interpretation and its non-claims.

**GATE**

`CAP — CONTROL DIFFERENTIATION SUFFICIENT`; zero additional Normal, Bare, or
V13 control invocations are authorized by this result.

**COMPLETION LINE**

`RAW REPAIR DIFFERENTIATION — NOT DEMONSTRATED` is preserved, and the frontier
is redirected to the legitimacy of beginning or continuing a loop.

**MISSING CLOSURE**

No general raw-capability parity, V13 superiority, frequency of illegitimate
continuation, or prevention advantage has been established.

**RE-ENTRY**

Re-enter through independently arising legitimacy or continuation evidence;
do not manufacture it by starting another same-snapshot control.

## 13. Proven-fork repeat merges shifted value toward starting position and continuation legitimacy

**AS-OF**

2026-08-18 JST, after upstream `pooza/makoto2` PR #94 merged and the
precommitted proven-fork phase Completion Line was reached.

**FRONTIER**

Raw repair differentiation was not demonstrated. The next question was
whether earned repository and maintainer residue still improved the starting
position of later real work without silently authorizing that work.

**CAUSAL DELTA**

Question: what remained useful in a proven fork if capable Sol could already
construct a repair loop? Observation: residue accelerated repository search,
toolchain/test routing, maintainer-route recovery, and bounded candidate
selection, while current As-of checks still had to correct the contribution
branch, suite size, dependencies, and affected URL surface. Upstream merge
evidence reached two independent repeat pairs:
`ritsth/job-autofill-extension` #215 → #221 and `pooza/makoto2` #56 → #94.
Why the frontier moved: inherited state improved re-entry, while direction and
continuation still required current validation and external acceptance. The
phase stopped at `SECOND INDEPENDENT REPEAT MERGE`; its unused final trial was
not consumed. No claim is made that the loop caused either merge.

**EVIDENCE ANCHOR**

- `/Users/sn/Documents/v13/13-175-proven-fork-field-trial-3/FIELD_TRIAL_RECORD.md`.
- `/Users/sn/Documents/v13/13-175-proven-fork-field-trial-3/evidence/EXTERNALIZATION_RECEIPT.md`.
- `/Users/sn/Documents/v13/13-175-proven-fork-field-trial-3/SELECTION_FREEZE.md`.

**GATE**

`CAP — SECOND INDEPENDENT REPEAT MERGE ACHIEVED / ADDITIONAL TRIAL AUTHORITY TERMINATED`.

**COMPLETION LINE**

The two repeat-merge pairs and precommitted phase stop are fixed as bounded
starting-position and acceptance evidence; the unused trial remains
unconsumed and unauthorized.

**MISSING CLOSURE**

Causal trust, relationship improvement, general acceptance advantage, and the
effect size of residue on starting position remain unestablished.

**RE-ENTRY**

Preserve future independent evidence without reopening this completed phase.
Any new trial or external action requires a fresh Entry decision and authority.

## 14. Entry Gate and Compound Gate became a working architecture hypothesis

**AS-OF**

2026-08-18 JST, after the proven-fork phase terminated at its precommitted CAP.

**FRONTIER**

The field evidence showed both that residue could improve a successor starting
position and that unused loop budget must not become a continuation target.
One undifferentiated infinite improvement loop could not preserve both facts.

**CAUSAL DELTA**

Question: how should V13 preserve compounding without inheriting direction
from prior success? Observation: two distinct decisions emerged. The Entry Gate
asks, “What deserves a loop now?” The Compound Gate asks whether residue earned
inside a completed loop justifies another loop on the same meaning-line. When
the compound chain terminates, direction returns to Entry selection. Why the
frontier moved: the working cycle preserves the useful residue while requiring
a fresh directional judgment:

```text
State is inherited.
Direction is re-evaluated.
```

Earned residue improves the starting position; it does not determine the
destination.

**EVIDENCE ANCHOR**

- `/Users/sn/Documents/v13/13-145-bridge-readiness/field_notes/137_entry_gate_compound_gate_cycle.md`.
- Bounded supporting phase evidence in
  `/Users/sn/Documents/v13/13-175-proven-fork-field-trial-3/FIELD_TRIAL_RECORD.md`.

**GATE**

`HOLD — WORKING ARCHITECTURE HYPOTHESIS / NOT CANON`.

**COMPLETION LINE**

Entry selection, same-line Compound continuation, CAP termination, and return
to Entry are preserved as a working hypothesis without changing Canon or
implementing a runtime gate.

**MISSING CLOSURE**

The distinction has not been validated across multiple independent workflows,
under pressure, or against path-dependency and zero-reset failures.

**RE-ENTRY**

Re-evaluate only from independently arising multi-workflow evidence. Do not
start an experiment, implementation, or remaining field-trial budget from the
hypothesis itself.

## 15. External criticism separated property verification from direction

**AS-OF**

2026-08-18 JST, after an external practitioner challenged the control framing
of “better.”

**FRONTIER**

The legitimacy frontier still risked compressing heterogeneous outcomes into
one universal quality judgment and then treating that judgment as a reason to
continue.

**CAUSAL DELTA**

Question: can bounded facts be established without allowing a verifier to
invent the direction or trade-off weights? Observation: specific declared
properties can be recorded as `PASS / FAIL / UNKNOWN`, while direction and
continuation remain a separate `GO / HOLD / CAP / BLOCK` judgment. Different
properties may conflict or require a Decision Seat value judgment. Why the
frontier moved: the useful distinction became `Verification Is Not Direction`.
A property PASS does not imply GO, a FAIL does not automatically authorize
repair, and an UNKNOWN does not automatically authorize another loop.

**EVIDENCE ANCHOR**

- `/Users/sn/Documents/v13/13-145-bridge-readiness/field_notes/138_verification_is_not_direction.md`.
- The bounded 13-175 merge illustration referenced by that note; the merge is
  external acceptance of one contribution, not a universal “better” proof.

**GATE**

`HOLD — STRUCTURE RECORDED / GENERALIZATION NOT YET VALIDATED`.

**COMPLETION LINE**

Property verification and directional authority are durably separated without
creating a universal scalar, Canon change, implementation, or successor loop.

**MISSING CLOSURE**

No repeated workflow evidence yet shows that this separation handles
conflicting properties or prevents false “better” claims and unnecessary
continuation.

**RE-ENTRY**

Preserve independently arising property-versus-direction evidence for a later
bounded judgment; do not generate it through an unauthorized experiment.

## 16. Selective retrieval moved Field Notes toward a bounded case-law library

**AS-OF**

2026-08-18 JST, after 13-176 completed.

**FRONTIER**

Field Notes contained extensive advisory memory, but it had not been directly
qualified whether a fresh reader could select only materially relevant cases,
reject near-matches, return `NONE`, preserve authority boundaries, and transfer
the residue into a new rule.

**CAUSAL DELTA**

Question: can the existing corpus be used selectively rather than loaded or
copied wholesale? Observation: five positive scenarios passed all five
independent properties; the negative control returned `NONE` and passed
precision, negative-control discipline, boundary preservation, and transfer
quality. No authority-boundary violation was observed. Independent relevance
for the `NONE` case remained `UNKNOWN` because its evaluator received no
selected note bodies, and corpus-wide recall remained unknown because
retrieval was selectively title-routed. Why the frontier moved: selective
case-law reuse was demonstrated in a bounded qualification, exposing routing
recall—not wholesale note reading—as the next candidate question.

**EVIDENCE ANCHOR**

- `/Users/sn/Documents/v13/13-176-selective-field-note-retrieval/FINAL_REPORT.md`.
- `/Users/sn/Documents/v13/13-176-selective-field-note-retrieval/PASS_FAIL_UNKNOWN_MATRIX.md`.
- `/Users/sn/Documents/v13/13-176-selective-field-note-retrieval/PROTECTED_SURFACE_VERIFICATION.md`.

**GATE**

`HOLD — MINIMAL FIELD NOTE ROUTER / ROUTING-RECALL QUALIFICATION NOT STARTED`.

**COMPLETION LINE**

`PASS — SELECTIVE REUSE DEMONSTRATED IN BOUNDED QUALIFICATION`.

**MISSING CLOSURE**

Corpus-wide false-negative rate, weak-title recall, model/run generalization,
ranking stability, and repeat negative-control performance remain unknown.

**RE-ENTRY**

Only a fresh Decision Owner action may start a Minimal Field Note Router or
routing-recall qualification. Do not repair indexing, metadata, filenames,
README, or Field Notes from 13-176.

## 17. Long-context value triggered causal fixation before handoff

**AS-OF**

2026-08-18 JST, GPT 13-40 immediately before responsibility-bearing handoff to
GPT 13-41.

**FRONTIER**

The post-Entry-9 causal movement existed across durable artifacts, but the
current long context had become valuable enough that fear of terminating it
was beginning to influence the judgment to continue. The causal spine needed
fixation before the receiver-facing Handoff was written.

**CAUSAL DELTA**

Question: could the session stop without losing why the current frontier
exists? Observation: durable evidence could reconstruct the trajectory through
the parked F-01 path, bounded execution substrate, control pivot, proven-fork
reuse, working gate hypotheses, Verification-versus-Direction distinction, and
selective Field Note qualification. Why the frontier moved: continuation
pressure from context value became the reason to preserve causal joints and
hand off, rather than a reason to keep the same session alive. This is one
operator observation, not a general long-context law. The current passive
calibration `model_context_window = 500000` is recorded only as session state,
not as an optimal-setting claim.

**EVIDENCE ANCHOR**

- The durable evidence anchors named in Entries 10–16.
- Decision Owner 13-40 trajectory-fixation instruction for the current
  operational observation, handoff decision, and passive calibration state.

**GATE**

`CAP — TRAJECTORY FIXATION ONLY`; the 13-40 → 13-41 Handoff remains outside
this task.

**COMPLETION LINE**

The minimum post-Entry-9 causal spine is append-only fixed on the established
trajectory lineage before GPT 13-40 creates the responsibility-bearing
13-40 → 13-41 Handoff.

**MISSING CLOSURE**

The receiver-facing 13-40 → 13-41 Handoff has not yet been written. No general
long-context law or optimal context-window setting has been established.

**RE-ENTRY**

After this trajectory append is committed and pushed, return to GPT 13-40 to
create the responsibility-bearing Handoff referencing the fixed trajectory.
Do not create that Handoff inside this fixation task.
