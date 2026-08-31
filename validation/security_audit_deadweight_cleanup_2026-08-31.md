# V13 Security / Audit Deadweight Cleanup — 2026-08-31

## Scope and baseline

```text
Repository: shin4141/decision-os-v13-loopkit
Baseline: 94a24a06d492f6f86482de389b350862b0b83df3
Gate: GO / CAP — READ / CLASSIFY / SAFE CLEANUP ONLY
External runtime effects: 0
Security boundary changed: NO
```

The inventory covered all 577 tracked baseline paths. Candidate selection used
the path roles named in the cleanup request: audit, security, forensic,
qualification, verification, proof, evidence, bridge, re-entry, incident,
trajectory, handoff, authority, collision, restart, temporary/legacy/obsolete,
plus the two active current-state surfaces and the old roadmap/demo pair.
This produced 190 candidate paths.

## Classification

Candidate unit is one tracked baseline path.

| Class | Count | Disposition |
| --- | ---: | --- |
| KEEP | 184 | Runtime boundary, production regression, current handoff/lineage dependency, public supported surface, or a referenced fixed-As-of record |
| COMPRESS | 2 | `docs/current_signal.md` and `handoff/current_codex_handoff.md`; repeated historical blocks are compressible, but exact byte-preservation is currently a protected regression, so cleanup is HOLD |
| ARCHIVE | 2 | `docs/companion_product_roadmap_v0_2.md` moved outside active docs; `services/ai_agent_handoff_audit_automation.md` is explicitly inactive but remains in place because the protected handoff history still references it |
| DELETE-CANDIDATE | 2 | Unreferenced fixed-As-of Stage 5 audit ledger and one-shot pre-merge scrub receipt; both removed |

The deterministic 186-path keyword inventory is the baseline tree filtered by:

```text
audit|security|forensic|qualif|verification|verify|proof|evidence|
temporary|temp|one-shot|bridge|reentry|re-entry|obsolete|deprecated|
legacy|old|workaround|probe|harness|receipt|incident|trajectory|
handoff|collision|authority|restart
```

All paths in that set not named in COMPRESS, ARCHIVE, or DELETE-CANDIDATE are
KEEP. The four manually admitted candidates are `docs/current_signal.md`,
`docs/companion_product_roadmap_v0_2.md`, `docs/demo_storyboard.md`, and
`scripts/demo_loopkit_terminal.sh`; the demo pair remains KEEP because the
storyboard is its direct caller/usage contract and the protected handoff records
the pair.

## Dependency graph

```text
AGENTS.md / SECURITY.md
  -> current signal + current handoff
  -> decision_os.checks / decision_os.scan
  -> current-state, handoff, authority and collision regressions

CLI
  -> audit_gate
     -> audit_delivery + audit_link + intake
  -> public_claim_guard
  -> handoff_acceptance

Companion / acceleration runtime
  -> authority, one-mutation, durable-store and protected-path checks
  -> production tests and exact fixtures

Stage 5 public-claim protection
  -> decision_os/public_claim_guard.py
  -> templates/v13_public_release_audit_matrix_v0_1.md
  -> tests/test_decision_os_public_claim_guard.py
  -> validation/v13_sdfp_001_final_closure.md
```

## Safe cleanup and non-dilution proof

Removed:

- `docs/audit/v13_stage5_audit_coverage_ledger_v0_1.md`
- `validation/v13_s5_fr_001_pre_merge_public_release_scrub_receipt_001.md`

Both were fixed-As-of, had zero repository callers by exact-path search, and
did not participate in imports, CLI dispatch, workflows, current handoff, or
tests. Their conclusions and protections are superseded by the production
public-claim guard, its live regression suite, the still-active audit matrix,
and the final Stage 5 closure named above. Exact historical bytes remain in Git
history at the baseline commit. Therefore the same protection is already
enforced elsewhere by concrete code and tests; no check, Gate, hash, approval,
or fail-closed branch was removed.

Archived from the ordinary docs route:

- `archive/roadmaps/companion_product_roadmap_v0_2.md`

The active v0.2 path is now a short archive pointer. Its exact 373-line body is
preserved byte-for-byte in the archive, while the forward successor
`docs/companion_product_roadmap_v0_3.md` remains byte-identical to baseline.
No runtime or authority consumer used the v0.2 body.

## HOLD

The two active current-state surfaces contain large superseded histories, but
`tests/test_current_state_admission.py` currently fixes those histories by
SHA-256. Removing or relocating them would change a protected restart
invariant. They remain unmodified until a separate design proves equivalent
reconstruction without weakening restartability.

## Verification contract

Required before closure:

- exact reference/import/workflow caller re-scan;
- public-claim, current-state, handoff, audit, Companion authority, collision,
  and compact-output regressions;
- repository scan and current first-block equality;
- `git diff --check`;
- pushed branch read-back from the remote.

## Closure

```text
V12 State:
PASS when the required verification and remote branch read-back pass

V13 Gate:
HOLD after this bounded cleanup; no automatic next loop

Missing Closure:
tests, commit, push, and remote branch read-back until completed
```
