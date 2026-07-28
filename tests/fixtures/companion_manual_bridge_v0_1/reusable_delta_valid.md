# Fixture — Valid Reusable Delta Record

This fixture records one future-use candidate without promoting it to Canon.

```json
{
  "schema": "decision-os-companion-manual-bridge-record-v0.1",
  "task_id": "V13-CMB-001",
  "protocol_run_id": "V13-PMR-002",
  "artifact_role": "REUSABLE_DELTA_RECORD",
  "selected_role": "REUSABLE_DELTA_RECORD",
  "declared_role": "REUSABLE_DELTA_RECORD",
  "source_path_or_label": "fixture/reusable_delta_valid.md",
  "model_identity": {
    "value": "UNKNOWN",
    "basis": "UNKNOWN",
    "verification_state": "UNKNOWN"
  },
  "role_identity": "Reusable Delta Recorder",
  "artifact_authored_at": "2026-07-29T13:00:00+09:00",
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
  "authority_state": "FUTURE_USE_CANDIDATE_ONLY",
  "objective": "Preserve one bounded reusable candidate from the synthetic Golden chain.",
  "completion_line": "Record the candidate with scope, conditions, exclusions, evidence, owner, and recheck.",
  "do_not_touch": "Canon, AGENTS.md, automatic routing, accepted rules, and Product Result.",
  "current_gate": "HOLD — OWNER ACCEPTANCE REQUIRED",
  "authority_boundary": "Candidate record only; no automatic Canon update or implementation authority.",
  "required_next_actor": "Shin / Decision Owner",
  "findings": [
    {
      "finding_id": "DELTA-SOURCE-FINDING-001",
      "type": "TRANSFER_INTEGRITY",
      "value": "Stable structural atom IDs make field loss mechanically visible."
    }
  ],
  "human_execution_cost": {
    "value_or_unknown": "UNKNOWN",
    "unit": "UNKNOWN",
    "method": "NOT_MEASURED",
    "source_event_ids": [],
    "basis": "SYNTHETIC_FIXTURE",
    "confidence": "UNKNOWN"
  },
  "reusable_delta": [
    {
      "delta_id": "REUSABLE-DELTA-001",
      "source_finding": "DELTA-SOURCE-FINDING-001",
      "source_artifact_identity": "sha256:4444444444444444444444444444444444444444444444444444444444444444",
      "reusable_form": "Require stable source-bound atoms for deterministic handoff comparison.",
      "scope": "Companion Manual Bridge structural Replay only",
      "conditions": [
        "typed source atoms exist",
        "source artifact identity is fixed"
      ],
      "exclusions": [
        "semantic truth",
        "automatic authority",
        "general Canon promotion"
      ],
      "evidence": [
        "synthetic preserved and field-loss Replay fixtures"
      ],
      "owner": "Shin",
      "status": "CANDIDATE",
      "authority_state": "FUTURE_USE_CANDIDATE_ONLY",
      "next_recheck": "Independent Pro Audit"
    }
  ],
  "unknowns": [
    "Owner acceptance",
    "Cross-context reuse value",
    "Measured burden effect"
  ],
  "claim_boundary": "Synthetic future-use candidate only; not an accepted operating rule."
}
```
