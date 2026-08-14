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
