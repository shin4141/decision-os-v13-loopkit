# Fixture — Valid Build Receipt

This fixture records synthetic Builder execution evidence only.

```json
{
  "schema": "decision-os-companion-manual-bridge-record-v0.1",
  "task_id": "V13-CMB-001",
  "protocol_run_id": "V13-PMR-002",
  "artifact_role": "BUILD_RECEIPT",
  "selected_role": "BUILD_RECEIPT",
  "declared_role": "BUILD_RECEIPT",
  "source_path_or_label": "fixture/build_receipt_valid.md",
  "model_identity": {
    "value": "gpt-5.6-sol",
    "basis": "VERIFIED_BY_RUNTIME",
    "verification_state": "VERIFIED_BY_RUNTIME"
  },
  "role_identity": "Fresh SOL / coding-agent Builder",
  "artifact_authored_at": "2026-07-29T10:00:00+09:00",
  "imported_at": "TO_BE_FIXED_AT_IMPORT",
  "as_of_commit": "63eb260a94595298e2b07b476f7f9d8572c9ef09",
  "evidence_packet_identity": {
    "commit": "970ae5e24e59dada54e1b829229360d9945a0910",
    "path": "validation/companion_manual_bridge_v0_1_shared_evidence_packet.md",
    "blob_sha": "92f9f69f18db052b421fa5fa7f233ce77f5a42b8",
    "sha256": "847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab",
    "product_as_of_commit": "63eb260a94595298e2b07b476f7f9d8572c9ef09"
  },
  "artifact_content_hash": "TO_BE_FIXED_AT_IMPORT",
  "import_event_id": "TO_BE_FIXED_AT_IMPORT",
  "authority_state": "EXECUTION_EVIDENCE_ONLY",
  "objective": "Implement and validate Companion Manual Bridge v0.1 inside the bounded Builder surface.",
  "completion_line": "The bounded implementation and Builder validation are ready for independent audit.",
  "do_not_touch": "Independent Pro Audit, merge, publication, release, and later-owner Golden artifacts.",
  "current_gate": "BUILD READY FOR INDEPENDENT AUDIT",
  "authority_boundary": "Builder execution evidence only; no independent Product, Protocol, or Replay PASS.",
  "required_next_actor": "Independent Pro Auditor",
  "findings": [
    {
      "finding_id": "BUILD-FINDING-001",
      "type": "IMPLEMENTATION",
      "value": "The Bridge uses a separate Git-common-dir store."
    }
  ],
  "human_execution_cost": {
    "value_or_unknown": 42,
    "unit": "minutes",
    "method": "FIXTURE_ELAPSED_TIMER",
    "source_event_ids": [
      "fixture-build-start",
      "fixture-build-finish"
    ],
    "basis": "SYNTHETIC_FIXTURE",
    "confidence": "HIGH"
  },
  "reusable_delta": [
    {
      "delta_id": "BUILD-DELTA-001",
      "status": "CANDIDATE",
      "value": "Use typed atoms to prevent fluent-prose preservation shortcuts.",
      "authority_state": "FUTURE_USE_CANDIDATE_ONLY"
    }
  ],
  "unknowns": [
    "Independent Product Result",
    "Final Protocol Result",
    "Replay Result"
  ],
  "builder_identity": "Synthetic Builder Fixture",
  "builder_authority_source": "Explicit bounded execution handoff",
  "base_commit": "970ae5e24e59dada54e1b829229360d9945a0910",
  "branch": "codex/v13-cmb-001-build",
  "implementation_commit": "1111111111111111111111111111111111111111",
  "receipt_fixation_commit": "EXTERNAL AFTER COMMIT",
  "exact_changed_paths": [
    "decision_os/companion/manual_bridge.py",
    "docs/companion_manual_bridge_v0_1.md",
    "tests/test_companion_manual_bridge.py"
  ],
  "test_commands": [
    {
      "command": "python3 -B -m unittest -v tests.test_companion_manual_bridge",
      "result": "PASS"
    },
    {
      "command": "python3 -B -m unittest discover -s tests",
      "result": "PASS"
    },
    {
      "command": "git diff --check",
      "result": "PASS"
    }
  ],
  "deviations": [],
  "repair_count": 0,
  "routine_cleanup_state": "COMPLETE",
  "builder_completion_boundary": "Builder completion is execution evidence only. It is not independent Product PASS, Protocol PASS, Replay PASS, merge approval, publication approval, or reusable-delta acceptance.",
  "claim_boundary": "Synthetic Build Receipt fixture; execution evidence only."
}
```
