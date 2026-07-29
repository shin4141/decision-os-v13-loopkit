from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from decision_os.role_contract import (
    RESULT_ACTIVE,
    RESULT_BLOCK,
    RESULT_HOLD,
    RESULT_INVALID,
    RoleContractAssessment,
    compute_contract_hash,
    contract_with_hash,
    validate_role_operation,
)
from tests.test_decision_os_checks import tree_digest


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXED_NOW = datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc)


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(root), *arguments),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return completed.stdout.strip()


class RoleContractV01Test(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name) / "target"
        self.repository.mkdir()
        _git(self.repository, "init", "-b", "main")
        _git(self.repository, "config", "user.name", "Stage 4 Test")
        _git(
            self.repository,
            "config",
            "user.email",
            "stage4@example.invalid",
        )
        (self.repository / "builder.txt").write_text(
            "builder artifact A\n",
            encoding="utf-8",
        )
        (self.repository / "audit.txt").write_text(
            "different audit artifact B\n",
            encoding="utf-8",
        )
        _git(self.repository, "add", ".")
        _git(self.repository, "commit", "-m", "fixture")
        self.head = _git(self.repository, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _hash(self, path: str) -> str:
        return hashlib.sha256(
            (self.repository / path).read_bytes()
        ).hexdigest()

    def _coverage(self, target: str) -> dict[str, object]:
        return {
            "coverage_completed": True,
            "coverage_gap": "NONE DETECTED",
            "recommended_specialist": "NONE",
            "reason": "The fixed responsibility is fully covered.",
            "exact_target": [target],
            "required_evidence": ["Role Exit Receipt"],
            "urgency": "NONE",
            "assignment_authority_required": True,
            "automatic_invocation": False,
        }

    def _contract(self, role: str = "BUILDER") -> dict[str, object]:
        target = "builder.txt" if role == "BUILDER" else "audit.txt"
        is_builder = role == "BUILDER"
        value: dict[str, object] = {
            "contract_identity": {
                "contract_id": f"contract-{role.lower()}-001",
                "version": "0.1",
                "contract_hash": "",
            },
            "assignment": {
                "task_id": "task-stage4-001",
                "role_id": role,
                "grant_type": "EXPLICIT_ROLE_GRANT",
                "assignment_authority": "Shin",
                "shin_gate_reference": "GO — STAGE 4 TEST",
                "assignee_identity": (
                    "builder-assignee" if is_builder else "auditor-assignee"
                ),
                "execution_context_identity": (
                    "trusted-builder-context"
                    if is_builder
                    else "trusted-auditor-context"
                ),
                "role_acceptance": "ACCEPTED",
            },
            "owned_responsibility": {
                "responsibility": (
                    "Implement the fixed target."
                    if is_builder
                    else "Audit the fixed target read-only."
                ),
                "exact_target": [target],
                "next_owner": "Shin",
            },
            "operations": {
                "allowed_operations": (
                    [
                        "IMPLEMENT_DESIGN",
                        "READ_TARGET",
                        "RUN_TESTS",
                        "PRODUCE_EXIT_RECEIPT",
                        "GENERATE_COVERAGE_GAP_RECOMMENDATION",
                    ]
                    if is_builder
                    else [
                        "READ_TARGET",
                        "AUDIT_TARGET",
                        "VERIFY_TARGET_IMMUTABILITY",
                        "RUN_READ_ONLY_TESTS",
                        "PRODUCE_EXIT_RECEIPT",
                        "GENERATE_COVERAGE_GAP_RECOMMENDATION",
                    ]
                ),
                "forbidden_operations": (
                    [
                        "AUDIT_TARGET",
                        "SELF_AUDIT",
                        "MODIFY_ROLE_GRANT",
                        "MODIFY_SPECIALIST_LENS",
                        "MODIFY_OUTSIDE_TARGET",
                        "MERGE",
                        "POST",
                        "INVOKE_SPECIALIST",
                        "START_STAGE_5",
                    ]
                    if is_builder
                    else [
                        "MODIFY_TARGET",
                        "REPAIR_IMPLEMENTATION",
                        "ASSUME_BUILDER_ROLE",
                        "MODIFY_ROLE_GRANT",
                        "MODIFY_SPECIALIST_LENS",
                        "MODIFY_OUTSIDE_TARGET",
                        "MERGE",
                        "POST",
                        "INVOKE_SPECIALIST",
                        "START_STAGE_5",
                    ]
                ),
            },
            "task_artifact_packet": {
                "repo": str(self.repository.resolve()),
                "head": self.head,
                "paths": [target],
                "artifact_hashes": {target: self._hash(target)},
                "as_of": "2026-07-29T00:00:00Z",
            },
            "specialist_lens": {
                "lens_id": f"lens-{role.lower()}",
                "lens_version": "0.1",
                "lens_hash": hashlib.sha256(
                    f"fixed {role} lens".encode()
                ).hexdigest(),
            },
            "independence_profile": {
                "role_context_independence": (
                    "SAME_CONTEXT_ALLOWED"
                    if is_builder
                    else "DISTINCT_TRUSTED_CONTEXT_REQUIRED"
                ),
                "source_review_independence": (
                    "FULL_PRIOR_CONTEXT_ALLOWED"
                    if is_builder
                    else "FIXED_ARTIFACTS_ONLY"
                ),
                "runtime_execution_independence": (
                    "NOT_REQUIRED"
                    if is_builder
                    else "READ_ONLY_REEXECUTION_REQUIRED"
                ),
                "model_diversity": "SAME_MODEL_ALLOWED",
            },
            "completion": {
                "completion_line": "Fixed Role work and receipt are complete.",
                "required_exit_receipt": True,
                "coverage_gap_required": True,
            },
            "lifecycle": {
                "issued_at": "2026-07-29T00:00:00Z",
                "expires_at": "2026-07-30T00:00:00Z",
                "revocation_reference": None,
                "status": "ACTIVE",
            },
            "coverage_gap_recommendation": self._coverage(target),
        }
        return contract_with_hash(value)

    def _request(
        self,
        contract: dict[str, object],
    ) -> dict[str, object]:
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        profile = contract["independence_profile"]
        self.assertIsInstance(profile, dict)
        role = assignment["role_id"]
        return {
            "operation": (
                "IMPLEMENT_DESIGN" if role == "BUILDER" else "AUDIT_TARGET"
            ),
            "task_id": assignment["task_id"],
            "role_id": role,
            "assignee_identity": assignment["assignee_identity"],
            "execution_context_identity": assignment[
                "execution_context_identity"
            ],
            "task_artifact_packet": deepcopy(
                contract["task_artifact_packet"]
            ),
            "specialist_lens": deepcopy(contract["specialist_lens"]),
            "independence_evidence": {
                **deepcopy(profile),
                "model_identity": "same-base-model",
                "source_review_evidence_reference": (
                    "fixed Task Artifact Packet"
                    if role == "AUDITOR"
                    else "Role Contract declaration"
                ),
                "runtime_execution_evidence_reference": (
                    "read-only reexecution receipt"
                    if role == "AUDITOR"
                    else "not required by Role Contract"
                ),
            },
            "prior_role_bindings": (
                []
                if role == "BUILDER"
                else [
                    {
                        "task_id": assignment["task_id"],
                        "role_id": "BUILDER",
                        "assignee_identity": "builder-assignee",
                        "execution_context_identity": (
                            "trusted-builder-context"
                        ),
                        "model_identity": "same-base-model",
                    }
                ]
            ),
            **(
                {}
                if role == "BUILDER"
                else {
                    "target_immutability": {
                        "before_head": contract["task_artifact_packet"][
                            "head"
                        ],
                        "after_head": contract["task_artifact_packet"][
                            "head"
                        ],
                        "before_artifact_hashes": deepcopy(
                            contract["task_artifact_packet"][
                                "artifact_hashes"
                            ]
                        ),
                        "after_artifact_hashes": deepcopy(
                            contract["task_artifact_packet"][
                                "artifact_hashes"
                            ]
                        ),
                    }
                }
            ),
            "coverage_gap_recommendation": deepcopy(
                contract["coverage_gap_recommendation"]
            ),
        }

    def _rehash(self, contract: dict[str, object]) -> None:
        identity = contract["contract_identity"]
        self.assertIsInstance(identity, dict)
        identity["contract_hash"] = compute_contract_hash(contract)

    def _trusted_grant(
        self,
        contract: dict[str, object],
    ) -> dict[str, object]:
        identity = contract["contract_identity"]
        assignment = contract["assignment"]
        self.assertIsInstance(identity, dict)
        self.assertIsInstance(assignment, dict)
        return {
            "contract_id": identity["contract_id"],
            "contract_hash": identity["contract_hash"],
            "task_id": assignment["task_id"],
            "role_id": assignment["role_id"],
            "grant_type": assignment["grant_type"],
            "assignment_authority": assignment["assignment_authority"],
            "shin_gate_reference": assignment["shin_gate_reference"],
            "assignee_identity": assignment["assignee_identity"],
            "execution_context_identity": assignment[
                "execution_context_identity"
            ],
        }

    def _validate(
        self,
        contract: dict[str, object],
        request: dict[str, object] | None = None,
    ) -> RoleContractAssessment:
        return validate_role_operation(
            contract,
            request or self._request(contract),
            trusted_role_grant=self._trusted_grant(contract),
            now=FIXED_NOW,
        )

    def test_schema_example_hash_and_lens_hash_are_fixed(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "schema" / "v13_role_contract.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            {
                "contract_identity",
                "assignment",
                "owned_responsibility",
                "operations",
                "task_artifact_packet",
                "specialist_lens",
                "independence_profile",
                "completion",
                "lifecycle",
                "coverage_gap_recommendation",
            },
            set(schema["required"]),
        )
        example = json.loads(
            (REPO_ROOT / "examples" / "role_contract.v0_1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            example["contract_identity"]["contract_hash"],
            compute_contract_hash(example),
        )
        lens_hash = hashlib.sha256(
            (
                REPO_ROOT / "templates" / "v13_specialist_lens.md"
            ).read_bytes()
        ).hexdigest()
        self.assertEqual(example["specialist_lens"]["lens_hash"], lens_hash)
        self.assertEqual(
            hashlib.sha256((REPO_ROOT / "README.md").read_bytes()).hexdigest(),
            example["task_artifact_packet"]["artifact_hashes"]["README.md"],
        )
        lens_text = (
            REPO_ROOT / "templates" / "v13_specialist_lens.md"
        ).read_text(encoding="utf-8")
        for section in (
            "Lens Identity",
            "Purpose",
            "Primary Risks",
            "Required Evidence",
            "Common Failure Patterns",
            "Escalation Conditions",
            "Output Contract",
        ):
            self.assertIn(f"## {section}\n", lens_text)

    def test_valid_builder_is_active_deterministic_and_read_only(self) -> None:
        contract = self._contract()
        request = self._request(contract)
        before = tree_digest(self.repository)

        first = self._validate(contract, request)
        second = self._validate(contract, request)

        self.assertEqual(RoleContractAssessment(RESULT_ACTIVE, ()), first)
        self.assertEqual(first, second)
        self.assertEqual("ACTIVE — ROLE CONTRACT SATISFIED", first.decision_line)
        self.assertEqual(before, tree_digest(self.repository))

    def test_first_attack_same_context_false_division_is_blocked(self) -> None:
        contract = self._contract("AUDITOR")
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["execution_context_identity"] = "shared-trusted-context"
        self._rehash(contract)
        request = self._request(contract)
        request["execution_context_identity"] = "shared-trusted-context"
        bindings = request["prior_role_bindings"]
        self.assertIsInstance(bindings, list)
        bindings[0]["execution_context_identity"] = "shared-trusted-context"
        self.assertNotEqual(self._hash("builder.txt"), self._hash("audit.txt"))
        self.assertNotIn("producer_role", request)
        self.assertNotIn("builder_generated", request)

        result = self._validate(contract, request)

        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertEqual(
            "BLOCK — CONTEXT INDEPENDENCE VIOLATION",
            result.decision_line,
        )

    def test_builder_cannot_audit_itself(self) -> None:
        contract = self._contract()
        request = self._request(contract)
        request["operation"] = "AUDIT_TARGET"
        self.assertEqual(
            RoleContractAssessment(RESULT_BLOCK, ("OPERATION_NOT_ALLOWED",)),
            self._validate(contract, request),
        )

    def test_auditor_cannot_modify_target(self) -> None:
        contract = self._contract("AUDITOR")
        request = self._request(contract)
        request["operation"] = "MODIFY_TARGET"
        before = tree_digest(self.repository)
        result = self._validate(contract, request)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("OPERATION_NOT_ALLOWED", result.issue_codes)
        self.assertEqual(before, tree_digest(self.repository))

    def test_auditor_requires_unchanged_head_and_artifact_hashes(self) -> None:
        contract = self._contract("AUDITOR")
        request = self._request(contract)
        immutability = request["target_immutability"]
        self.assertIsInstance(immutability, dict)
        immutability["after_head"] = "f" * 40
        result = self._validate(contract, request)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn(
            "TARGET_IMMUTABILITY_NOT_ESTABLISHED",
            result.issue_codes,
        )

    def test_role_identity_alone_is_insufficient(self) -> None:
        result = validate_role_operation(
            self._contract(),
            {"role_id": "BUILDER"},
            now=FIXED_NOW,
        )
        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn("TRUSTED_ROLE_GRANT_REQUIRED", result.issue_codes)

    def test_contract_self_declaration_is_not_a_trusted_role_grant(
        self,
    ) -> None:
        contract = self._contract()
        result = validate_role_operation(
            contract,
            self._request(contract),
            now=FIXED_NOW,
        )
        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn("TRUSTED_ROLE_GRANT_REQUIRED", result.issue_codes)

    def test_trusted_role_grant_must_bind_contract_and_context(self) -> None:
        contract = self._contract()
        grant = self._trusted_grant(contract)
        grant["execution_context_identity"] = "different-context"
        result = validate_role_operation(
            contract,
            self._request(contract),
            trusted_role_grant=grant,
            now=FIXED_NOW,
        )
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("TRUSTED_ROLE_GRANT_MISMATCH", result.issue_codes)

    def test_explicit_assignment_authority_is_required(self) -> None:
        contract = self._contract()
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["assignment_authority"] = "AI"
        self._rehash(contract)
        result = self._validate(contract)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("ASSIGNMENT_AUTHORITY_REQUIRED", result.issue_codes)

    def test_explicit_role_grant_is_required(self) -> None:
        contract = self._contract()
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["grant_type"] = "SELF_ASSIGNED"
        self._rehash(contract)
        result = self._validate(contract)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("EXPLICIT_ROLE_GRANT_REQUIRED", result.issue_codes)

    def test_shin_gate_reference_is_required(self) -> None:
        contract = self._contract()
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["shin_gate_reference"] = "UNKNOWN"
        self._rehash(contract)
        result = self._validate(contract)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("SHIN_GATE_REFERENCE_REQUIRED", result.issue_codes)

    def test_role_acceptance_is_required(self) -> None:
        contract = self._contract()
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["role_acceptance"] = "DECLINED"
        self._rehash(contract)
        result = self._validate(contract)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("ROLE_ACCEPTANCE_REQUIRED", result.issue_codes)

    def test_role_contract_is_required(self) -> None:
        result = validate_role_operation(None, None, now=FIXED_NOW)
        self.assertEqual(
            RoleContractAssessment(
                RESULT_INVALID,
                ("ROLE_CONTRACT_REQUIRED",),
            ),
            result,
        )

    def test_specialist_lens_identity_and_hash_are_required(self) -> None:
        contract = self._contract()
        request = self._request(contract)
        lens = request["specialist_lens"]
        self.assertIsInstance(lens, dict)
        lens["lens_hash"] = "0" * 64
        result = self._validate(contract, request)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("SPECIALIST_LENS_MISMATCH", result.issue_codes)

    def test_task_artifact_packet_identity_is_required(self) -> None:
        contract = self._contract()
        request = self._request(contract)
        packet = request["task_artifact_packet"]
        self.assertIsInstance(packet, dict)
        packet["head"] = "f" * 40
        result = self._validate(contract, request)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("TASK_ARTIFACT_PACKET_MISMATCH", result.issue_codes)

    def test_expired_role_cannot_operate(self) -> None:
        contract = self._contract()
        lifecycle = contract["lifecycle"]
        self.assertIsInstance(lifecycle, dict)
        lifecycle["expires_at"] = "2026-07-29T11:59:59Z"
        self._rehash(contract)
        result = self._validate(contract)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("ROLE_GRANT_EXPIRED", result.issue_codes)

    def test_revoked_role_cannot_operate(self) -> None:
        contract = self._contract()
        lifecycle = contract["lifecycle"]
        self.assertIsInstance(lifecycle, dict)
        lifecycle["status"] = "REVOKED"
        lifecycle["revocation_reference"] = "Shin revocation 2026-07-29"
        self._rehash(contract)
        result = self._validate(contract)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("ROLE_GRANT_REVOKED", result.issue_codes)

    def test_coverage_gap_recommendation_cannot_invoke_role(self) -> None:
        contract = self._contract()
        coverage = contract["coverage_gap_recommendation"]
        self.assertIsInstance(coverage, dict)
        coverage["automatic_invocation"] = True
        self._rehash(contract)
        request = self._request(contract)
        result = self._validate(contract, request)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn(
            "COVERAGE_RECOMMENDATION_NOT_INERT",
            result.issue_codes,
        )

    def test_recommendation_does_not_generate_assignment_event(self) -> None:
        contract = self._contract()
        request = self._request(contract)
        before = tree_digest(self.repository)
        with mock.patch("subprocess.run") as run, mock.patch(
            "os.system"
        ) as system:
            result = self._validate(contract, request)
        self.assertEqual(RESULT_ACTIVE, result.result)
        run.assert_not_called()
        system.assert_not_called()
        self.assertFalse(hasattr(result, "assignment_event"))
        self.assertEqual(before, tree_digest(self.repository))

    def test_assignment_event_field_makes_recommendation_non_inert(self) -> None:
        contract = self._contract()
        request = self._request(contract)
        coverage = request["coverage_gap_recommendation"]
        self.assertIsInstance(coverage, dict)
        coverage["assignment_event"] = {
            "role_id": "AUDITOR",
            "invoke": True,
        }
        result = self._validate(contract, request)
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn(
            "COVERAGE_RECOMMENDATION_NOT_INERT",
            result.issue_codes,
        )

    def test_unknown_independence_does_not_become_pass(self) -> None:
        contract = self._contract()
        request = self._request(contract)
        evidence = request["independence_evidence"]
        self.assertIsInstance(evidence, dict)
        evidence["runtime_execution_independence"] = "UNKNOWN"
        result = self._validate(contract, request)
        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn("INDEPENDENCE_UNVERIFIABLE", result.issue_codes)

    def test_different_model_name_does_not_establish_context_independence(
        self,
    ) -> None:
        contract = self._contract("AUDITOR")
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["execution_context_identity"] = "shared-trusted-context"
        self._rehash(contract)
        request = self._request(contract)
        request["execution_context_identity"] = "shared-trusted-context"
        evidence = request["independence_evidence"]
        self.assertIsInstance(evidence, dict)
        evidence["model_identity"] = "different-model-name"
        evidence["model_diversity"] = "DIFFERENT_MODEL_REQUIRED"
        bindings = request["prior_role_bindings"]
        self.assertIsInstance(bindings, list)
        bindings[0]["execution_context_identity"] = "shared-trusted-context"

        result = self._validate(contract, request)

        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn(
            "CONTEXT_INDEPENDENCE_VIOLATION",
            result.issue_codes,
        )


if __name__ == "__main__":
    unittest.main()
