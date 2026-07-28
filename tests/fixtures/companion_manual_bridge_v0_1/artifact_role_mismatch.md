# Fixture — Selected and Declared Role Mismatch

The operational selection in this synthetic envelope is `PRO_DESIGN`, while
the artifact declares `PRO_AUDIT`. Import must hold with `ROLE MISMATCH`.

```json
{
  "schema": "decision-os-companion-manual-bridge-record-v0.1",
  "task_id": "V13-CMB-001",
  "protocol_run_id": "V13-PMR-002",
  "artifact_role": "PRO_AUDIT",
  "selected_role": "PRO_DESIGN",
  "declared_role": "PRO_AUDIT",
  "source_path_or_label": "fixture/artifact_role_mismatch.md",
  "model_identity": {
    "value": "Independent Pro Model",
    "basis": "SELF_DECLARED",
    "verification_state": "UNVERIFIED"
  },
  "role_identity": "Independent Pro Auditor",
  "artifact_authored_at": "2026-07-29T12:00:00+09:00",
  "imported_at": "TO_BE_FIXED_AT_IMPORT",
  "as_of_commit": "63eb260a94595298e2b07b476f7f9d8572c9ef09",
  "evidence_packet_identity": {
    "commit": "970ae5e24e59dada54e1b829229360d9945a0910",
    "path": "validation/companion_manual_bridge_v0_1_shared_evidence_packet.md",
    "blob_sha": "92f9f69f18db052b421fa5fa7f233ce77f5a42b8",
    "sha256": "847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab"
  },
  "artifact_content_hash": "TO_BE_FIXED_AT_IMPORT",
  "import_event_id": "TO_BE_FIXED_AT_IMPORT",
  "authority_state": "INDEPENDENT_JUDGMENT_ONLY_NO_IMPLEMENTATION_AUTHORITY",
  "objective": "Exercise explicit selected-role versus declared-role validation.",
  "completion_line": "Reject operational role substitution.",
  "do_not_touch": "Role-selection authority.",
  "current_gate": "HOLD — ROLE MISMATCH",
  "authority_boundary": "The document label cannot select its operational role.",
  "required_next_actor": "Artifact importer",
  "findings": [],
  "human_execution_cost": {
    "value_or_unknown": "UNKNOWN",
    "unit": "UNKNOWN",
    "method": "NOT_MEASURED",
    "source_event_ids": [],
    "basis": "FIXTURE",
    "confidence": "UNKNOWN"
  },
  "reusable_delta": [],
  "unknowns": []
}
```
