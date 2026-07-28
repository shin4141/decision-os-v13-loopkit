# Fixture — Valid Independent Pro Audit

This fixture is synthetic independent-audit evidence.

```json
{
  "schema": "decision-os-companion-manual-bridge-record-v0.1",
  "task_id": "V13-CMB-001",
  "protocol_run_id": "V13-PMR-002",
  "artifact_role": "PRO_AUDIT",
  "selected_role": "PRO_AUDIT",
  "declared_role": "PRO_AUDIT",
  "source_path_or_label": "fixture/pro_audit_valid.md",
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
    "sha256": "847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab",
    "product_as_of_commit": "63eb260a94595298e2b07b476f7f9d8572c9ef09"
  },
  "artifact_content_hash": "TO_BE_FIXED_AT_IMPORT",
  "import_event_id": "TO_BE_FIXED_AT_IMPORT",
  "authority_state": "INDEPENDENT_JUDGMENT_ONLY",
  "objective": "Independently assess whether the bounded implementation satisfies the accepted design.",
  "completion_line": "Record an evidence-based Product Result recommendation and preserve every remaining UNKNOWN.",
  "do_not_touch": "Implementation, merge state, publication state, frozen source artifacts, and Builder authority.",
  "current_gate": "HOLD — DECISION OWNER REVIEW REQUIRED",
  "authority_boundary": "Independent judgment only; no implementation, merge, publication, or release authority.",
  "required_next_actor": "Shin / Decision Owner",
  "findings": [
    {
      "finding_id": "AUDIT-FINDING-001",
      "type": "CONFORMANCE",
      "value": "The synthetic audited surface preserves identity without authority."
    }
  ],
  "human_execution_cost": {
    "value_or_unknown": 18,
    "unit": "minutes",
    "method": "FIXTURE_OBSERVED_INTERVAL",
    "source_event_ids": [
      "fixture-audit-start",
      "fixture-audit-end"
    ],
    "basis": "SYNTHETIC_FIXTURE",
    "confidence": "HIGH"
  },
  "reusable_delta": [],
  "unknowns": [
    "Decision Owner acceptance",
    "Merge decision",
    "Real-world burden change"
  ],
  "audit_evidence_basis": [
    "repository diff",
    "focused tests",
    "full suite",
    "independently recomputed hashes"
  ],
  "repository_diff_inspected": true,
  "artifact_identities_independently_checked": true,
  "tests_independently_checked": true,
  "product_result_recommendation": "PASS — SYNTHETIC FIXTURE ONLY",
  "repair_route": "No fixture repair required.",
  "claim_boundary": "Synthetic independent-audit fixture; no merge, publication, or release authority."
}
```
