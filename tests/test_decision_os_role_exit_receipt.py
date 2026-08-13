from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from decision_os.role_contract import (
    AUDITOR_ALLOWED,
    AUDITOR_REQUIRED_FORBIDDEN,
    contract_with_hash,
)
from decision_os.role_exit_receipt import (
    BOUNDED_GIT_PATH_PATTERN,
    CLAIMS_NOT_MADE,
    IMPLEMENTATION_BOUNDARY,
    NON_PLACEHOLDER_STRING_PATTERN,
    RFC3339_PATTERN,
    RESULT_INVALID,
    RESULT_VALID,
    SCHEMA_VERSION,
    TOP_LEVEL_FIELDS,
    RoleExitReceiptAssessment,
    receipt_with_id,
    validate_role_exit_receipt,
)
from tests.test_decision_os_checks import tree_digest


REPO_ROOT = Path(__file__).resolve().parents[1]
FINAL_HEAD = "b" * 40
ARTIFACT_SHA256 = "c" * 64
OUTPUT_SHA256 = "d" * 64
ERROR_SHA256 = "e" * 64
ENVIRONMENT_SHA256 = "f" * 64


class RoleExitReceiptValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(
            (REPO_ROOT / "examples" / "role_contract.v0_1.json").read_text(
                encoding="utf-8"
            )
        )

    def _receipt(
        self,
        contract: dict[str, object] | None = None,
    ) -> dict[str, object]:
        selected = contract or self.contract
        identity = selected["contract_identity"]
        assignment = selected["assignment"]
        packet = selected["task_artifact_packet"]
        completion = selected["completion"]
        ownership = selected["owned_responsibility"]
        self.assertIsInstance(identity, dict)
        self.assertIsInstance(assignment, dict)
        self.assertIsInstance(packet, dict)
        self.assertIsInstance(completion, dict)
        self.assertIsInstance(ownership, dict)
        role = assignment["role_id"]
        final_head = packet["head"] if role == "AUDITOR" else FINAL_HEAD
        changed = []
        if role == "BUILDER":
            changed = [
                {
                    "path": ownership["exact_target"][0],
                    "change_type": "MODIFIED",
                    "sha256": ARTIFACT_SHA256,
                }
            ]
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "receipt_id": "",
            "recorded_at": "2026-07-29T12:00:00Z",
            "contract_identity": {
                "contract_id": identity["contract_id"],
                "contract_hash": identity["contract_hash"],
            },
            "assignment_identity": {
                "task_id": assignment["task_id"],
                "role_id": role,
                "assignee_identity": assignment["assignee_identity"],
                "execution_context_identity": assignment[
                    "execution_context_identity"
                ],
            },
            "repository_state": {
                "repo": packet["repo"],
                "base_head": packet["head"],
                "final_head": final_head,
            },
            "changed_artifacts": changed,
            "verification_commands": [
                {
                    "argv": ["python3", "-B", "-m", "unittest"],
                    "exit_code": 0,
                    "stdout_sha256": OUTPUT_SHA256,
                    "stderr_sha256": ERROR_SHA256,
                    "environment_sha256": ENVIRONMENT_SHA256,
                    "required": True,
                }
            ],
            "runtime_evidence": [],
            "completion": {
                "v12_state": "PASS",
                "completion_state": "COMPLETE",
                "completion_line": completion["completion_line"],
                "routine_cleanup_state": "COMPLETE",
                "remaining_unverified": [],
                "unknowns": [],
            },
            "coverage_gap_recommendation": {
                "coverage_completed": True,
                "coverage_gap": "NONE DETECTED",
                "recommended_specialist": "NONE",
                "reason": "The contracted target and evidence are covered.",
                "exact_target": ownership["exact_target"],
                "required_evidence": ["Role Exit Receipt"],
                "urgency": "NONE",
                "assignment_authority_required": True,
                "automatic_invocation": False,
            },
            "implementation_boundary": dict(IMPLEMENTATION_BOUNDARY),
            "required_next_actor": ownership["next_owner"],
            "claims_not_made": list(CLAIMS_NOT_MADE),
        }
        return receipt_with_id(receipt)

    @staticmethod
    def _rehash(receipt: dict[str, object]) -> None:
        receipt["receipt_id"] = receipt_with_id(receipt)["receipt_id"]

    def _auditor_contract(self) -> dict[str, object]:
        contract = deepcopy(self.contract)
        assignment = contract["assignment"]
        operations = contract["operations"]
        profile = contract["independence_profile"]
        self.assertIsInstance(assignment, dict)
        self.assertIsInstance(operations, dict)
        self.assertIsInstance(profile, dict)
        assignment["role_id"] = "AUDITOR"
        assignment["assignee_identity"] = "example-auditor"
        assignment["execution_context_identity"] = "context-example-auditor-001"
        operations["allowed_operations"] = sorted(AUDITOR_ALLOWED)
        operations["forbidden_operations"] = sorted(AUDITOR_REQUIRED_FORBIDDEN)
        profile["role_context_independence"] = "DISTINCT_CONTEXT_REQUIRED"
        return contract_with_hash(contract)

    def test_valid_builder_receipt_is_deterministic_read_only_and_not_pass(
        self,
    ) -> None:
        receipt = self._receipt()
        before = tree_digest(REPO_ROOT)

        first = validate_role_exit_receipt(self.contract, receipt)
        second = validate_role_exit_receipt(self.contract, receipt)

        self.assertEqual(RoleExitReceiptAssessment(RESULT_VALID, ()), first)
        self.assertEqual(first, second)
        self.assertEqual(
            "VALID — STRUCTURALLY ELIGIBLE FOR INDEPENDENT REVIEW",
            first.decision_line,
        )
        self.assertNotIn("PASS", first.decision_line)
        self.assertEqual(before, tree_digest(REPO_ROOT))

    def test_schema_matches_validator_contract_and_claim_boundary(self) -> None:
        schema = json.loads(
            (
                REPO_ROOT / "schema" / "v13_role_exit_receipt.schema.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(TOP_LEVEL_FIELDS, set(schema["required"]))
        self.assertEqual(
            SCHEMA_VERSION,
            schema["properties"]["schema_version"]["const"],
        )
        self.assertEqual(
            list(CLAIMS_NOT_MADE),
            schema["properties"]["claims_not_made"]["const"],
        )
        self.assertEqual(
            NON_PLACEHOLDER_STRING_PATTERN,
            schema["$defs"]["nonEmptyString"]["pattern"],
        )
        self.assertEqual(
            BOUNDED_GIT_PATH_PATTERN,
            schema["$defs"]["boundedGitPath"]["pattern"],
        )
        self.assertEqual(
            RFC3339_PATTERN,
            schema["properties"]["recorded_at"]["pattern"],
        )
        self.assertEqual(
            "#/$defs/boundedGitPath",
            schema["$defs"]["changedArtifact"]["properties"]["path"][
                "$ref"
            ],
        )
        self.assertEqual(
            "#/$defs/nonEmptyString",
            schema["$defs"]["verificationCommand"]["properties"]["argv"][
                "items"
            ]["$ref"],
        )
        self.assertEqual(
            "#/$defs/boundedGitPath",
            schema["$defs"]["coverageGapRecommendation"]["properties"][
                "exact_target"
            ]["items"]["$ref"],
        )
        for field, value in IMPLEMENTATION_BOUNDARY.items():
            self.assertEqual(
                value,
                schema["properties"]["implementation_boundary"][
                    "properties"
                ][field]["const"],
            )

    def test_schema_path_pattern_matches_repository_boundary(self) -> None:
        for path, expected in (
            ("README.md", True),
            ("docs/receipt.md", True),
            ("/absolute", False),
            ("../outside", False),
            ("docs/../outside", False),
            ("docs//receipt.md", False),
            ("docs/", False),
            ("docs\\receipt.md", False),
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    expected,
                    re.fullmatch(BOUNDED_GIT_PATH_PATTERN, path) is not None,
                )

    def test_unknown_or_extra_result_family_is_rejected(self) -> None:
        receipt = self._receipt()
        receipt["schema_version"] = "decision-os.role-exit-receipt.v9"
        self._rehash(receipt)
        unsupported = validate_role_exit_receipt(self.contract, receipt)

        receipt = self._receipt()
        receipt["review_disposition"] = "GO"
        self._rehash(receipt)
        extra = validate_role_exit_receipt(self.contract, receipt)

        self.assertEqual(("UNSUPPORTED_SCHEMA_VERSION",), unsupported.issue_codes)
        self.assertEqual(("INVALID_RECEIPT_STRUCTURE",), extra.issue_codes)

    def test_receipt_hash_tampering_is_rejected(self) -> None:
        receipt = self._receipt()
        receipt["required_next_actor"] = "Different receiver"

        result = validate_role_exit_receipt(self.contract, receipt)

        self.assertEqual(RESULT_INVALID, result.result)
        self.assertEqual(("RECEIPT_HASH_MISMATCH",), result.issue_codes)

    def test_contract_and_assignment_bindings_are_exact(self) -> None:
        cases = (
            ("contract_identity", "contract_id", "other", "CONTRACT_BINDING_MISMATCH"),
            ("assignment_identity", "task_id", "other", "ASSIGNMENT_BINDING_MISMATCH"),
            (
                "assignment_identity",
                "role_id",
                "AUDITOR",
                "ASSIGNMENT_BINDING_MISMATCH",
            ),
            (
                "assignment_identity",
                "execution_context_identity",
                "other-context",
                "ASSIGNMENT_BINDING_MISMATCH",
            ),
        )
        for section, field, value, expected in cases:
            with self.subTest(section=section, field=field):
                receipt = self._receipt()
                receipt[section][field] = value
                self._rehash(receipt)

                result = validate_role_exit_receipt(self.contract, receipt)

                self.assertEqual((expected,), result.issue_codes)

    def test_repository_base_and_final_identity_are_checked(self) -> None:
        for field, value in (
            ("repo", "other/repository"),
            ("base_head", "a" * 40),
            ("final_head", "not-a-head"),
        ):
            with self.subTest(field=field):
                receipt = self._receipt()
                receipt["repository_state"][field] = value
                self._rehash(receipt)

                result = validate_role_exit_receipt(self.contract, receipt)

                self.assertEqual(("REPOSITORY_BINDING_MISMATCH",), result.issue_codes)

    def test_builder_change_evidence_and_head_advance_cannot_diverge(self) -> None:
        receipt = self._receipt()
        receipt["changed_artifacts"] = []
        self._rehash(receipt)
        advanced_without_changes = validate_role_exit_receipt(
            self.contract, receipt
        )

        receipt = self._receipt()
        receipt["repository_state"]["final_head"] = receipt[
            "repository_state"
        ]["base_head"]
        self._rehash(receipt)
        changes_without_advance = validate_role_exit_receipt(
            self.contract, receipt
        )

        expected = ("HEAD_CHANGE_EVIDENCE_MISMATCH",)
        self.assertEqual(expected, advanced_without_changes.issue_codes)
        self.assertEqual(expected, changes_without_advance.issue_codes)

    def test_changed_artifacts_are_hash_bound_and_scope_bound(self) -> None:
        receipt = self._receipt()
        receipt["changed_artifacts"][0]["path"] = "outside.py"
        self._rehash(receipt)
        outside = validate_role_exit_receipt(self.contract, receipt)

        receipt = self._receipt()
        receipt["changed_artifacts"][0]["sha256"] = "bad"
        self._rehash(receipt)
        malformed = validate_role_exit_receipt(self.contract, receipt)

        receipt = self._receipt()
        receipt["changed_artifacts"][0].update(
            {"change_type": "DELETED", "sha256": None}
        )
        self._rehash(receipt)
        deleted = validate_role_exit_receipt(self.contract, receipt)

        self.assertEqual(("TARGET_SCOPE_EXCEEDED",), outside.issue_codes)
        self.assertEqual(("INVALID_CHANGED_ARTIFACTS",), malformed.issue_codes)
        self.assertEqual(RESULT_VALID, deleted.result)

    def test_verification_evidence_requires_exact_hashes_and_argv(self) -> None:
        cases = (
            ("argv", [],),
            ("exit_code", True),
            ("stdout_sha256", "bad"),
            ("environment_sha256", "bad"),
        )
        for field, value in cases:
            with self.subTest(field=field):
                receipt = self._receipt()
                receipt["verification_commands"][0][field] = value
                self._rehash(receipt)

                result = validate_role_exit_receipt(self.contract, receipt)

                self.assertEqual(("INVALID_VERIFICATION_EVIDENCE",), result.issue_codes)

    def test_command_arguments_are_not_interpreted_as_repository_paths(
        self,
    ) -> None:
        receipt = self._receipt()
        receipt["verification_commands"][0]["argv"] = [
            "/usr/bin/python3",
            "../fixture",
            ".",
        ]
        self._rehash(receipt)

        result = validate_role_exit_receipt(self.contract, receipt)

        self.assertEqual(RESULT_VALID, result.result)

    def test_pass_fails_closed_without_successful_required_evidence(self) -> None:
        variants = []
        failed_command = self._receipt()
        failed_command["verification_commands"][0]["exit_code"] = 1
        variants.append(failed_command)
        no_commands = self._receipt()
        no_commands["verification_commands"] = []
        variants.append(no_commands)
        unverified = self._receipt()
        unverified["completion"]["remaining_unverified"] = ["Full suite"]
        variants.append(unverified)
        cleanup = self._receipt()
        cleanup["completion"]["routine_cleanup_state"] = "INCOMPLETE"
        variants.append(cleanup)
        unknown = self._receipt()
        unknown["completion"]["unknowns"] = ["Whether implementation works"]
        variants.append(unknown)
        no_op = self._receipt()
        no_op["repository_state"]["final_head"] = no_op[
            "repository_state"
        ]["base_head"]
        no_op["changed_artifacts"] = []
        variants.append(no_op)

        for receipt in variants:
            with self.subTest(receipt=receipt):
                self._rehash(receipt)
                result = validate_role_exit_receipt(self.contract, receipt)
                self.assertEqual(("FALSE_PASS_EVIDENCE",), result.issue_codes)

    def test_unknown_state_preserves_unresolved_evidence(self) -> None:
        receipt = self._receipt()
        receipt["completion"].update(
            {
                "v12_state": "UNKNOWN",
                "completion_state": "UNKNOWN",
                "routine_cleanup_state": "UNKNOWN",
                "remaining_unverified": ["Required runtime replay"],
                "unknowns": ["Whether the implementation works"],
            }
        )
        receipt["verification_commands"][0]["exit_code"] = 1
        self._rehash(receipt)

        result = validate_role_exit_receipt(self.contract, receipt)

        self.assertEqual(RESULT_VALID, result.result)

    def test_v12_state_and_completion_state_cannot_diverge(self) -> None:
        receipt = self._receipt()
        receipt["completion"]["v12_state"] = "DELAY"
        self._rehash(receipt)

        result = validate_role_exit_receipt(self.contract, receipt)

        self.assertEqual(("INVALID_COMPLETION_STATE",), result.issue_codes)

    def test_auditor_receipt_requires_immutable_target(self) -> None:
        contract = self._auditor_contract()
        receipt = self._receipt(contract)
        valid = validate_role_exit_receipt(contract, receipt)

        receipt["changed_artifacts"] = [
            {
                "path": "README.md",
                "change_type": "MODIFIED",
                "sha256": ARTIFACT_SHA256,
            }
        ]
        receipt["repository_state"]["final_head"] = FINAL_HEAD
        self._rehash(receipt)
        mutated = validate_role_exit_receipt(contract, receipt)

        self.assertEqual(RESULT_VALID, valid.result)
        self.assertEqual(("AUDITOR_MUTATION_EVIDENCE",), mutated.issue_codes)

    def test_coverage_gap_is_inert_and_target_bound(self) -> None:
        receipt = self._receipt()
        receipt["coverage_gap_recommendation"]["automatic_invocation"] = True
        self._rehash(receipt)
        automatic = validate_role_exit_receipt(self.contract, receipt)

        receipt = self._receipt()
        receipt["coverage_gap_recommendation"].update(
            {
                "coverage_completed": False,
                "coverage_gap": "Independent runtime replay missing",
                "recommended_specialist": "AUDITOR",
                "urgency": "MEDIUM",
            }
        )
        self._rehash(receipt)
        gap = validate_role_exit_receipt(self.contract, receipt)

        self.assertEqual(("INVALID_COVERAGE_GAP",), automatic.issue_codes)
        self.assertEqual(RESULT_VALID, gap.result)

    def test_malformed_nested_sequences_fail_closed(self) -> None:
        receipt = self._receipt()
        receipt["coverage_gap_recommendation"]["exact_target"] = None
        self._rehash(receipt)

        malformed_coverage = validate_role_exit_receipt(
            self.contract, receipt
        )

        contract = deepcopy(self.contract)
        contract["task_artifact_packet"]["paths"] = None
        contract = contract_with_hash(contract)
        malformed_contract = validate_role_exit_receipt(
            contract, self._receipt()
        )

        self.assertEqual(
            ("INVALID_COVERAGE_GAP",), malformed_coverage.issue_codes
        )
        self.assertEqual(
            ("TASK_ARTIFACT_PACKET_REQUIRED",),
            malformed_contract.issue_codes,
        )

    def test_malformed_enum_values_fail_closed(self) -> None:
        cases = (
            ("changed_artifacts", 0, "change_type"),
            ("runtime_evidence", 0, "evidence_type"),
            ("completion", None, "v12_state"),
            (
                "coverage_gap_recommendation",
                None,
                "recommended_specialist",
            ),
        )
        for section, index, field in cases:
            with self.subTest(section=section, field=field):
                receipt = self._receipt()
                if section == "runtime_evidence":
                    receipt[section] = [
                        {
                            "evidence_type": "OTHER",
                            "identity_sha256": ARTIFACT_SHA256,
                        }
                    ]
                target = receipt[section]
                if index is not None:
                    target = target[index]
                target[field] = []
                self._rehash(receipt)

                result = validate_role_exit_receipt(
                    self.contract, receipt
                )

                self.assertEqual(RESULT_INVALID, result.result)

    def test_contract_authority_and_lifecycle_are_enforced(self) -> None:
        contract = deepcopy(self.contract)
        contract["assignment"]["assignment_authority"] = "Mallory"
        contract = contract_with_hash(contract)
        wrong_authority = validate_role_exit_receipt(
            contract, self._receipt()
        )

        contract = deepcopy(self.contract)
        contract["lifecycle"]["status"] = "REVOKED"
        contract["lifecycle"]["revocation_reference"] = "revocation-001"
        contract = contract_with_hash(contract)
        revoked = validate_role_exit_receipt(contract, self._receipt())

        self.assertEqual(
            ("ASSIGNMENT_AUTHORITY_REQUIRED",),
            wrong_authority.issue_codes,
        )
        self.assertEqual(("ROLE_GRANT_REVOKED",), revoked.issue_codes)

    def test_contract_target_path_must_be_repository_bounded(self) -> None:
        contract = self._auditor_contract()
        contract["owned_responsibility"]["exact_target"] = ["../outside"]
        contract["task_artifact_packet"]["paths"] = ["../outside"]
        contract["task_artifact_packet"]["artifact_hashes"] = {
            "../outside": ARTIFACT_SHA256
        }
        contract["coverage_gap_recommendation"]["exact_target"] = [
            "../outside"
        ]
        contract = contract_with_hash(contract)

        result = validate_role_exit_receipt(contract, self._receipt(contract))

        self.assertEqual(("INVALID_TARGET_PATH",), result.issue_codes)

    def test_recorded_at_is_bound_to_contract_lifecycle(self) -> None:
        for recorded_at in (
            "2026-07-28T23:59:59Z",
            "2026-07-30T00:00:00Z",
            "2026-07-29 12:00:00+00:00",
        ):
            with self.subTest(recorded_at=recorded_at):
                receipt = self._receipt()
                receipt["recorded_at"] = recorded_at
                self._rehash(receipt)

                result = validate_role_exit_receipt(
                    self.contract, receipt
                )

                expected = (
                    "INVALID_RECORDED_AT"
                    if " " in recorded_at
                    else "RECEIPT_OUTSIDE_CONTRACT_LIFECYCLE"
                )
                self.assertEqual((expected,), result.issue_codes)

    def test_required_next_actor_is_contract_bound(self) -> None:
        receipt = self._receipt()
        receipt["required_next_actor"] = "Independent receiver"
        self._rehash(receipt)

        result = validate_role_exit_receipt(self.contract, receipt)

        self.assertEqual(
            ("NEXT_ACTOR_BINDING_MISMATCH",), result.issue_codes
        )

    def test_boundary_and_claim_inflation_are_rejected(self) -> None:
        receipt = self._receipt()
        receipt["implementation_boundary"]["role_independence"] = "ESTABLISHED"
        self._rehash(receipt)
        boundary = validate_role_exit_receipt(self.contract, receipt)

        receipt = self._receipt()
        receipt["claims_not_made"].remove("authority_approval_or_receiver_disposition")
        self._rehash(receipt)
        claims = validate_role_exit_receipt(self.contract, receipt)

        self.assertEqual(("IMPLEMENTATION_BOUNDARY_MISMATCH",), boundary.issue_codes)
        self.assertEqual(("CLAIM_BOUNDARY_MISMATCH",), claims.issue_codes)

    def test_contract_hash_mismatch_blocks_receipt_validation(self) -> None:
        contract = deepcopy(self.contract)
        contract["assignment"]["task_id"] = "tampered-task"

        result = validate_role_exit_receipt(contract, self._receipt())

        self.assertEqual(("CONTRACT_HASH_MISMATCH",), result.issue_codes)


if __name__ == "__main__":
    unittest.main()
