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
    compute_prior_role_bindings_snapshot_hash,
    contract_with_hash,
    validate_role_operation,
)
from tests.test_decision_os_checks import tree_digest


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXED_NOW = datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc)
FIXED_AS_OF = "2026-07-29T12:00:00Z"


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
                    "builder-context"
                    if is_builder
                    else "auditor-context"
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
                    else "DISTINCT_CONTEXT_REQUIRED"
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

    def _independence_evidence(
        self,
        contract: dict[str, object],
    ) -> dict[str, object]:
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        profile = contract["independence_profile"]
        self.assertIsInstance(profile, dict)
        role = assignment["role_id"]
        return {
            "record_identity": (
                f"supplied-{role.lower()}-independence-001"
            ),
            "task_id": assignment["task_id"],
            "role_id": role,
            "assignee_identity": assignment["assignee_identity"],
            "execution_context_identity": assignment[
                "execution_context_identity"
            ],
            **deepcopy(profile),
            "model_identity": "same-base-model",
            "source_review_evidence_reference": (
                "supplied fixed-artifact review receipt"
                if role == "AUDITOR"
                else "supplied full-context allowance record"
            ),
            "runtime_execution_evidence_reference": (
                "supplied read-only reexecution receipt"
                if role == "AUDITOR"
                else "supplied not-required record"
            ),
        }

    def _prior_role_bindings(
        self,
        contract: dict[str, object],
    ) -> list[dict[str, object]]:
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        if assignment["role_id"] == "BUILDER":
            return []
        return [
            {
                "record_identity": "supplied-builder-binding-001",
                "task_id": assignment["task_id"],
                "role_id": "BUILDER",
                "assignee_identity": "builder-assignee",
                "execution_context_identity": "builder-context",
                "model_identity": "same-base-model",
                "bound_at": "2026-07-29T00:00:00Z",
                "ended_at": "2026-07-29T00:02:00Z",
                "binding_state": "ENDED",
            }
        ]

    def _request(
        self,
        contract: dict[str, object],
    ) -> dict[str, object]:
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
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
            "independence_evidence": self._independence_evidence(contract),
            "prior_role_bindings": self._prior_role_bindings(contract),
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

    def _snapshot_identity(
        self,
        contract: dict[str, object],
    ) -> str:
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        return (
            f"snapshot-{str(assignment['role_id']).lower()}-"
            "20260729T120000Z"
        )

    def _supplied_grant(
        self,
        contract: dict[str, object],
    ) -> dict[str, object]:
        identity = contract["contract_identity"]
        assignment = contract["assignment"]
        self.assertIsInstance(identity, dict)
        self.assertIsInstance(assignment, dict)
        return {
            "record_identity": (
                f"supplied-{str(assignment['role_id']).lower()}-grant-001"
            ),
            "snapshot_identity": self._snapshot_identity(contract),
            "as_of": FIXED_AS_OF,
            "revocation_state": "NOT_REVOKED",
            "revoked_at": None,
            "revocation_reference": None,
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

    def _supplied_acceptance(
        self,
        contract: dict[str, object],
        grant: dict[str, object] | None = None,
    ) -> dict[str, object]:
        identity = contract["contract_identity"]
        assignment = contract["assignment"]
        self.assertIsInstance(identity, dict)
        self.assertIsInstance(assignment, dict)
        supplied_grant = grant or self._supplied_grant(contract)
        return {
            "record_identity": (
                "supplied-"
                f"{str(assignment['role_id']).lower()}-acceptance-001"
            ),
            "snapshot_identity": self._snapshot_identity(contract),
            "as_of": FIXED_AS_OF,
            "revocation_state": "NOT_REVOKED",
            "revoked_at": None,
            "revocation_reference": None,
            "contract_id": identity["contract_id"],
            "contract_hash": identity["contract_hash"],
            "task_id": assignment["task_id"],
            "role_id": assignment["role_id"],
            "assignee_identity": assignment["assignee_identity"],
            "execution_context_identity": assignment[
                "execution_context_identity"
            ],
            "role_acceptance": "ACCEPTED",
            "accepted_at": (
                "2026-07-29T00:01:00Z"
                if assignment["role_id"] == "BUILDER"
                else "2026-07-29T00:03:00Z"
            ),
            "grant_record_identity": supplied_grant["record_identity"],
        }

    def _supplied_prior_role_bindings(
        self,
        contract: dict[str, object],
    ) -> dict[str, object]:
        identity = contract["contract_identity"]
        assignment = contract["assignment"]
        self.assertIsInstance(identity, dict)
        self.assertIsInstance(assignment, dict)
        snapshot_identity = self._snapshot_identity(contract)
        bindings = [
            {
                **deepcopy(binding),
                "snapshot_identity": snapshot_identity,
                "as_of": FIXED_AS_OF,
                "revocation_state": "NOT_REVOKED",
                "revoked_at": None,
                "revocation_reference": None,
            }
            for binding in self._prior_role_bindings(contract)
        ]
        snapshot: dict[str, object] = {
            "snapshot_identity": snapshot_identity,
            "snapshot_hash": "",
            "contract_id": identity["contract_id"],
            "contract_hash": identity["contract_hash"],
            "task_id": assignment["task_id"],
            "as_of": FIXED_AS_OF,
            "revocation_state": "NOT_REVOKED",
            "revoked_at": None,
            "revocation_reference": None,
            "completeness_boundary": {
                "scope": "ALL_PRIOR_ROLE_BINDINGS_FOR_TASK",
                "task_id": assignment["task_id"],
                "from": "TASK_INCEPTION",
                "through": FIXED_AS_OF,
                "included_roles": ["BUILDER", "AUDITOR"],
                "state": "COMPLETE",
                "expected_record_identities": [
                    binding["record_identity"] for binding in bindings
                ],
            },
            "bindings": bindings,
        }
        snapshot["snapshot_hash"] = (
            compute_prior_role_bindings_snapshot_hash(snapshot)
        )
        return snapshot

    def _supplied_independence_evidence(
        self,
        contract: dict[str, object],
        snapshot: dict[str, object],
    ) -> dict[str, object]:
        identity = contract["contract_identity"]
        self.assertIsInstance(identity, dict)
        return {
            **self._independence_evidence(contract),
            "snapshot_identity": snapshot["snapshot_identity"],
            "as_of": FIXED_AS_OF,
            "revocation_state": "NOT_REVOKED",
            "revoked_at": None,
            "revocation_reference": None,
            "contract_id": identity["contract_id"],
            "contract_hash": identity["contract_hash"],
            "prior_role_bindings_snapshot_identity": snapshot[
                "snapshot_identity"
            ],
            "prior_role_bindings_snapshot_hash": snapshot["snapshot_hash"],
        }

    def _supplied_inputs(
        self,
        contract: dict[str, object],
    ) -> dict[str, object]:
        grant = self._supplied_grant(contract)
        snapshot = self._supplied_prior_role_bindings(contract)
        return {
            "supplied_role_grant": grant,
            "supplied_role_acceptance": self._supplied_acceptance(
                contract,
                grant,
            ),
            "supplied_independence_evidence": (
                self._supplied_independence_evidence(contract, snapshot)
            ),
            "supplied_prior_role_bindings": snapshot,
        }

    def _rehash_supplied_snapshot(
        self,
        supplied_inputs: dict[str, object],
    ) -> None:
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        evidence = supplied_inputs["supplied_independence_evidence"]
        self.assertIsInstance(snapshot, dict)
        self.assertIsInstance(evidence, dict)
        snapshot["snapshot_hash"] = (
            compute_prior_role_bindings_snapshot_hash(snapshot)
        )
        evidence["prior_role_bindings_snapshot_hash"] = snapshot[
            "snapshot_hash"
        ]

    def _set_supplied_as_of(
        self,
        supplied_inputs: dict[str, object],
        as_of: str,
    ) -> None:
        for record_name in (
            "supplied_role_grant",
            "supplied_role_acceptance",
            "supplied_independence_evidence",
        ):
            record = supplied_inputs[record_name]
            self.assertIsInstance(record, dict)
            record["as_of"] = as_of
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        self.assertIsInstance(snapshot, dict)
        snapshot["as_of"] = as_of
        boundary = snapshot["completeness_boundary"]
        bindings = snapshot["bindings"]
        self.assertIsInstance(boundary, dict)
        self.assertIsInstance(bindings, list)
        boundary["through"] = as_of
        for binding in bindings:
            binding["as_of"] = as_of
        self._rehash_supplied_snapshot(supplied_inputs)

    def _validate(
        self,
        contract: dict[str, object],
        request: dict[str, object] | None = None,
    ) -> RoleContractAssessment:
        return validate_role_operation(
            contract,
            request or self._request(contract),
            **self._supplied_inputs(contract),
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
        self.assertEqual(
            {
                "record_identity",
                "snapshot_identity",
                "contract_id",
                "contract_hash",
                "grant_record_identity",
                "task_id",
                "role_id",
                "assignee_identity",
                "execution_context_identity",
                "role_acceptance",
                "accepted_at",
                "as_of",
                "revocation_state",
                "revoked_at",
                "revocation_reference",
            },
            set(
                schema["$defs"]["suppliedRoleAcceptanceRecord"]["required"]
            ),
        )
        supplied_identity_fields = {
            "record_identity",
            "snapshot_identity",
            "task_id",
            "role_id",
            "assignee_identity",
            "execution_context_identity",
            "model_identity",
        }
        self.assertTrue(
            supplied_identity_fields.issubset(
                schema["$defs"]["suppliedPriorRoleBinding"]["required"]
            )
        )
        self.assertTrue(
            supplied_identity_fields.issubset(
                schema["$defs"]["suppliedIndependenceEvidenceRecord"][
                    "required"
                ]
            )
        )
        boundary = schema["$defs"]["suppliedPriorRoleBindingSnapshot"][
            "properties"
        ]["completeness_boundary"]
        self.assertEqual(
            "ALL_PRIOR_ROLE_BINDINGS_FOR_TASK",
            boundary["properties"]["scope"]["const"],
        )
        self.assertEqual(
            "TASK_INCEPTION",
            boundary["properties"]["from"]["const"],
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
        packet = example["task_artifact_packet"]
        self.assertEqual(
            "3a14dc65ea15f2d81cf3b3cd33362b3c001c0a41",
            packet["head"],
        )
        self.assertEqual("2026-07-29T00:00:00Z", packet["as_of"])
        self.assertEqual(
            "decc254e317b693604084ecdc1e9bfe034b8d6b69b32a70404fc63d64055ad39",
            packet["artifact_hashes"]["README.md"],
        )
        historical_readme = subprocess.run(
            (
                "git",
                "-C",
                str(REPO_ROOT),
                "show",
                f"{packet['head']}:README.md",
            ),
            check=False,
            capture_output=True,
        )
        if historical_readme.returncode == 0:
            self.assertEqual(
                hashlib.sha256(historical_readme.stdout).hexdigest(),
                packet["artifact_hashes"]["README.md"],
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
        implementation_boundary = "\n".join(
            (
                "Role Separation Enforcement: VALIDATOR-LEVEL ONLY",
                "Record Issuer / Authentication / Transport: "
                "NOT IMPLEMENTED",
                "Role Independence: NOT ESTABLISHED",
                "End-to-End False-Division Prevention: NOT ESTABLISHED",
            )
        )
        docs_text = (
            REPO_ROOT / "docs" / "role_bound_specialist_system_v0_1.md"
        ).read_text(encoding="utf-8")
        self.assertIn(implementation_boundary, lens_text)
        self.assertIn(implementation_boundary, docs_text)

    def test_matching_supplied_records_return_active_validator_result(
        self,
    ) -> None:
        contract = self._contract()
        request = self._request(contract)
        before = tree_digest(self.repository)

        first = self._validate(contract, request)
        second = self._validate(contract, request)

        self.assertEqual(RoleContractAssessment(RESULT_ACTIVE, ()), first)
        self.assertEqual(first, second)
        self.assertEqual(
            "ACTIVE — VALIDATOR CONDITIONS SATISFIED",
            first.decision_line,
        )
        self.assertEqual(before, tree_digest(self.repository))

    def test_subsecond_validation_snapshot_is_not_truncated(self) -> None:
        contract = self._contract()
        supplied_inputs = self._supplied_inputs(contract)
        self._set_supplied_as_of(
            supplied_inputs,
            "2026-07-29T12:00:00.500000Z",
        )

        result = validate_role_operation(
            contract,
            self._request(contract),
            **supplied_inputs,
            now=datetime(
                2026,
                7,
                29,
                12,
                0,
                0,
                500000,
                tzinfo=timezone.utc,
            ),
        )

        self.assertEqual(RESULT_ACTIVE, result.result)

    def test_equivalent_timezone_as_of_values_are_coherent(self) -> None:
        contract = self._contract()
        supplied_inputs = self._supplied_inputs(contract)
        grant = supplied_inputs["supplied_role_grant"]
        self.assertIsInstance(grant, dict)
        grant["as_of"] = "2026-07-29T21:00:00+09:00"

        result = validate_role_operation(
            contract,
            self._request(contract),
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_ACTIVE, result.result)

    def test_supplied_snapshot_same_context_collision_returns_block(
        self,
    ) -> None:
        contract = self._contract("AUDITOR")
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["execution_context_identity"] = "shared-supplied-context"
        self._rehash(contract)
        request = self._request(contract)
        request["execution_context_identity"] = "shared-supplied-context"
        bindings = request["prior_role_bindings"]
        self.assertIsInstance(bindings, list)
        bindings[0]["execution_context_identity"] = "shared-supplied-context"
        supplied_inputs = self._supplied_inputs(contract)
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        self.assertIsInstance(snapshot, dict)
        supplied_bindings = snapshot["bindings"]
        self.assertIsInstance(supplied_bindings, list)
        supplied_bindings[0]["execution_context_identity"] = (
            "shared-supplied-context"
        )
        self._rehash_supplied_snapshot(supplied_inputs)
        self.assertNotEqual(self._hash("builder.txt"), self._hash("audit.txt"))
        self.assertNotIn("producer_role", request)
        self.assertNotIn("builder_generated", request)

        result = validate_role_operation(
            contract,
            request,
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertEqual(
            "BLOCK — CONTEXT INDEPENDENCE VIOLATION",
            result.decision_line,
        )

    def test_claim_replacement_does_not_override_supplied_collision(
        self,
    ) -> None:
        contract = self._contract("AUDITOR")
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["execution_context_identity"] = "shared-supplied-context"
        self._rehash(contract)

        request = self._request(contract)
        request["execution_context_identity"] = "shared-supplied-context"
        claimed_bindings = request["prior_role_bindings"]
        self.assertIsInstance(claimed_bindings, list)
        claimed_bindings[0]["record_identity"] = (
            "forged-builder-binding-002"
        )
        claimed_bindings[0]["execution_context_identity"] = (
            "fake-distinct-context"
        )

        supplied_inputs = self._supplied_inputs(contract)
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        self.assertIsInstance(snapshot, dict)
        supplied_bindings = snapshot["bindings"]
        self.assertIsInstance(supplied_bindings, list)
        supplied_bindings[0]["execution_context_identity"] = (
            "shared-supplied-context"
        )
        self._rehash_supplied_snapshot(supplied_inputs)
        result = validate_role_operation(
            contract,
            request,
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertEqual(
            (
                "CONTEXT_INDEPENDENCE_VIOLATION",
                "SUPPLIED_PRIOR_ROLE_BINDINGS_CLAIM_MISMATCH",
            ),
            result.issue_codes,
        )

    def test_malformed_claims_do_not_downgrade_supplied_context_block(
        self,
    ) -> None:
        contract = self._contract("AUDITOR")
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["execution_context_identity"] = "shared-supplied-context"
        self._rehash(contract)
        supplied_inputs = self._supplied_inputs(contract)
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        self.assertIsInstance(snapshot, dict)
        supplied_bindings = snapshot["bindings"]
        self.assertIsInstance(supplied_bindings, list)
        supplied_bindings[0]["execution_context_identity"] = (
            "shared-supplied-context"
        )
        self._rehash_supplied_snapshot(supplied_inputs)

        malformed_requests = []
        malformed_evidence = self._request(contract)
        malformed_evidence["independence_evidence"] = {}
        malformed_requests.append(
            (
                "malformed evidence",
                malformed_evidence,
                "SUPPLIED_INDEPENDENCE_EVIDENCE_CLAIM_MISMATCH",
            )
        )
        duplicate_bindings = self._request(contract)
        binding_claims = duplicate_bindings["prior_role_bindings"]
        self.assertIsInstance(binding_claims, list)
        binding_claims.append(deepcopy(binding_claims[0]))
        malformed_requests.append(
            (
                "duplicate binding identity",
                duplicate_bindings,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_CLAIM_MISMATCH",
            )
        )

        for label, request, mismatch_issue in malformed_requests:
            with self.subTest(label=label):
                result = validate_role_operation(
                    contract,
                    request,
                    **supplied_inputs,
                    now=FIXED_NOW,
                )
                self.assertEqual(RESULT_BLOCK, result.result)
                self.assertEqual(
                    "CONTEXT_INDEPENDENCE_VIOLATION",
                    result.issue_codes[0],
                )
                self.assertIn(mismatch_issue, result.issue_codes)

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
        self.assertIn("SUPPLIED_ROLE_GRANT_REQUIRED", result.issue_codes)

    def test_contract_self_declaration_is_not_a_supplied_role_grant(
        self,
    ) -> None:
        contract = self._contract()
        result = validate_role_operation(
            contract,
            self._request(contract),
            now=FIXED_NOW,
        )
        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn("SUPPLIED_ROLE_GRANT_REQUIRED", result.issue_codes)

    def test_supplied_role_grant_must_bind_contract_and_context(self) -> None:
        contract = self._contract()
        grant = self._supplied_grant(contract)
        grant["execution_context_identity"] = "different-context"
        result = validate_role_operation(
            contract,
            self._request(contract),
            supplied_role_grant=grant,
            now=FIXED_NOW,
        )
        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn("SUPPLIED_ROLE_GRANT_MISMATCH", result.issue_codes)

    def test_request_only_independence_claims_do_not_replace_supplied_record(
        self,
    ) -> None:
        contract = self._contract()
        supplied_inputs = self._supplied_inputs(contract)
        supplied_inputs.pop("supplied_independence_evidence")
        result = validate_role_operation(
            contract,
            self._request(contract),
            **supplied_inputs,
            now=FIXED_NOW,
        )
        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn(
            "SUPPLIED_INDEPENDENCE_EVIDENCE_REQUIRED",
            result.issue_codes,
        )

    def test_supplied_independence_evidence_binds_all_identities(self) -> None:
        replacements = {
            "task_id": "different-task",
            "role_id": "AUDITOR",
            "assignee_identity": "different-assignee",
            "execution_context_identity": "different-context",
            "model_identity": "different-model",
            "record_identity": "different-record",
        }
        for field, replacement in replacements.items():
            with self.subTest(field=field):
                contract = self._contract()
                supplied_inputs = self._supplied_inputs(contract)
                supplied_evidence = supplied_inputs[
                    "supplied_independence_evidence"
                ]
                self.assertIsInstance(supplied_evidence, dict)
                supplied_evidence[field] = replacement
                result = validate_role_operation(
                    contract,
                    self._request(contract),
                    **supplied_inputs,
                    now=FIXED_NOW,
                )
                self.assertEqual(RESULT_BLOCK, result.result)
                self.assertIn(
                    (
                        "SUPPLIED_INDEPENDENCE_EVIDENCE_CLAIM_MISMATCH"
                        if field in ("model_identity", "record_identity")
                        else "SUPPLIED_INDEPENDENCE_EVIDENCE_MISMATCH"
                    ),
                    result.issue_codes,
                )

    def test_supplied_prior_role_bindings_require_snapshot_wrapper(
        self,
    ) -> None:
        contract = self._contract("AUDITOR")
        common = self._supplied_inputs(contract)
        common.pop("supplied_prior_role_bindings")
        missing = validate_role_operation(
            contract,
            self._request(contract),
            **common,
            now=FIXED_NOW,
        )
        self.assertEqual(RESULT_HOLD, missing.result)
        self.assertIn(
            "SUPPLIED_PRIOR_ROLE_BINDINGS_REQUIRED",
            missing.issue_codes,
        )

        binding = self._prior_role_bindings(contract)[0]
        bare_sequence = validate_role_operation(
            contract,
            self._request(contract),
            supplied_prior_role_bindings=[
                deepcopy(binding),
                deepcopy(binding),
            ],
            **common,
            now=FIXED_NOW,
        )
        self.assertEqual(RESULT_HOLD, bare_sequence.result)
        self.assertIn(
            "SUPPLIED_PRIOR_ROLE_BINDINGS_REQUIRED",
            bare_sequence.issue_codes,
        )

    def test_duplicate_record_identity_in_validation_bundle_is_blocked(
        self,
    ) -> None:
        contract = self._contract("AUDITOR")
        supplied_inputs = self._supplied_inputs(contract)
        supplied_evidence = supplied_inputs[
            "supplied_independence_evidence"
        ]
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        self.assertIsInstance(supplied_evidence, dict)
        self.assertIsInstance(snapshot, dict)
        supplied_bindings = snapshot["bindings"]
        self.assertIsInstance(supplied_bindings, list)
        supplied_evidence["record_identity"] = supplied_bindings[0][
            "record_identity"
        ]
        request = self._request(contract)
        request["independence_evidence"] = deepcopy(supplied_evidence)
        request_evidence = request["independence_evidence"]
        self.assertIsInstance(request_evidence, dict)
        for field in (
            "snapshot_identity",
            "as_of",
            "revocation_state",
            "revoked_at",
            "revocation_reference",
            "contract_id",
            "contract_hash",
            "prior_role_bindings_snapshot_identity",
            "prior_role_bindings_snapshot_hash",
        ):
            request_evidence.pop(field)

        result = validate_role_operation(
            contract,
            request,
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn(
            "SUPPLIED_RECORD_IDENTITY_REPLAY",
            result.issue_codes,
        )

    def test_incomplete_prior_binding_snapshot_is_hold(self) -> None:
        contract = self._contract("AUDITOR")
        cases = ("declared incomplete", "manifest omission")
        for case in cases:
            with self.subTest(case=case):
                supplied_inputs = self._supplied_inputs(contract)
                snapshot = supplied_inputs["supplied_prior_role_bindings"]
                self.assertIsInstance(snapshot, dict)
                boundary = snapshot["completeness_boundary"]
                bindings = snapshot["bindings"]
                self.assertIsInstance(boundary, dict)
                self.assertIsInstance(bindings, list)
                if case == "declared incomplete":
                    boundary["state"] = "INCOMPLETE"
                else:
                    bindings.clear()
                self._rehash_supplied_snapshot(supplied_inputs)

                result = validate_role_operation(
                    contract,
                    self._request(contract),
                    **supplied_inputs,
                    now=FIXED_NOW,
                )

                self.assertEqual(RESULT_HOLD, result.result)
                self.assertIn(
                    "SUPPLIED_PRIOR_ROLE_BINDINGS_INCOMPLETE",
                    result.issue_codes,
                )

    def test_omission_substitution_with_stale_manifest_is_hold(
        self,
    ) -> None:
        contract = self._contract("AUDITOR")
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["execution_context_identity"] = "shared-context"
        self._rehash(contract)
        supplied_inputs = self._supplied_inputs(contract)
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        self.assertIsInstance(snapshot, dict)
        bindings = snapshot["bindings"]
        self.assertIsInstance(bindings, list)
        true_binding = bindings[0]
        true_binding["execution_context_identity"] = "shared-context"
        fake_binding = deepcopy(true_binding)
        fake_binding["record_identity"] = "fake-distinct-binding-002"
        fake_binding["execution_context_identity"] = "fake-distinct-context"
        bindings[0] = fake_binding
        self._rehash_supplied_snapshot(supplied_inputs)

        result = validate_role_operation(
            contract,
            self._request(contract),
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn(
            "SUPPLIED_PRIOR_ROLE_BINDINGS_INCOMPLETE",
            result.issue_codes,
        )

    def test_coherent_snapshot_fabrication_is_not_detectable(self) -> None:
        contract = self._contract("AUDITOR")
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["execution_context_identity"] = "shared-context"
        self._rehash(contract)
        request = self._request(contract)
        supplied_inputs = self._supplied_inputs(contract)
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        self.assertIsInstance(snapshot, dict)
        boundary = snapshot["completeness_boundary"]
        supplied_bindings = snapshot["bindings"]
        claimed_bindings = request["prior_role_bindings"]
        self.assertIsInstance(boundary, dict)
        self.assertIsInstance(supplied_bindings, list)
        self.assertIsInstance(claimed_bindings, list)

        supplied_bindings[0]["record_identity"] = (
            "fabricated-distinct-binding-002"
        )
        supplied_bindings[0]["execution_context_identity"] = (
            "fabricated-distinct-context"
        )
        boundary["expected_record_identities"] = [
            supplied_bindings[0]["record_identity"]
        ]
        claimed_bindings[0] = {
            field: supplied_bindings[0][field]
            for field in (
                "record_identity",
                "task_id",
                "role_id",
                "assignee_identity",
                "execution_context_identity",
                "model_identity",
                "bound_at",
                "ended_at",
                "binding_state",
            )
        }
        self._rehash_supplied_snapshot(supplied_inputs)

        result = validate_role_operation(
            contract,
            request,
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_ACTIVE, result.result)

    def test_stale_acceptance_record_is_hold(self) -> None:
        contract = self._contract()
        supplied_inputs = self._supplied_inputs(contract)
        acceptance = supplied_inputs["supplied_role_acceptance"]
        self.assertIsInstance(acceptance, dict)
        acceptance["as_of"] = "2026-07-29T11:59:59Z"

        result = validate_role_operation(
            contract,
            self._request(contract),
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn("SUPPLIED_ROLE_ACCEPTANCE_STALE", result.issue_codes)

    def test_stale_prior_binding_snapshot_is_hold(self) -> None:
        contract = self._contract("AUDITOR")
        supplied_inputs = self._supplied_inputs(contract)
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        evidence = supplied_inputs["supplied_independence_evidence"]
        self.assertIsInstance(snapshot, dict)
        self.assertIsInstance(evidence, dict)
        snapshot["as_of"] = "2026-07-29T11:59:59Z"
        boundary = snapshot["completeness_boundary"]
        bindings = snapshot["bindings"]
        self.assertIsInstance(boundary, dict)
        self.assertIsInstance(bindings, list)
        boundary["through"] = snapshot["as_of"]
        for binding in bindings:
            binding["as_of"] = snapshot["as_of"]
        self._rehash_supplied_snapshot(supplied_inputs)

        result = validate_role_operation(
            contract,
            self._request(contract),
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn(
            "SUPPLIED_PRIOR_ROLE_BINDINGS_STALE",
            result.issue_codes,
        )

    def test_cross_snapshot_acceptance_replay_indicator_is_blocked(
        self,
    ) -> None:
        contract = self._contract()
        supplied_inputs = self._supplied_inputs(contract)
        acceptance = supplied_inputs["supplied_role_acceptance"]
        self.assertIsInstance(acceptance, dict)
        acceptance["snapshot_identity"] = "previous-snapshot-identity"

        result = validate_role_operation(
            contract,
            self._request(contract),
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn(
            "SUPPLIED_RECORD_SNAPSHOT_MISMATCH",
            result.issue_codes,
        )

    def test_revoked_supplied_records_never_return_active(self) -> None:
        contract = self._contract("AUDITOR")
        cases = {
            "grant": (
                "supplied_role_grant",
                "SUPPLIED_ROLE_GRANT_REVOKED",
            ),
            "acceptance": (
                "supplied_role_acceptance",
                "SUPPLIED_ROLE_ACCEPTANCE_REVOKED",
            ),
            "independence": (
                "supplied_independence_evidence",
                "SUPPLIED_INDEPENDENCE_EVIDENCE_REVOKED",
            ),
            "snapshot": (
                "supplied_prior_role_bindings",
                "SUPPLIED_PRIOR_ROLE_BINDINGS_REVOKED",
            ),
            "binding": (
                "binding",
                "SUPPLIED_PRIOR_ROLE_BINDING_REVOKED",
            ),
        }
        for case, (target_name, expected_issue) in cases.items():
            with self.subTest(case=case):
                supplied_inputs = self._supplied_inputs(contract)
                if target_name == "binding":
                    snapshot = supplied_inputs[
                        "supplied_prior_role_bindings"
                    ]
                    self.assertIsInstance(snapshot, dict)
                    bindings = snapshot["bindings"]
                    self.assertIsInstance(bindings, list)
                    target = bindings[0]
                else:
                    target = supplied_inputs[target_name]
                self.assertIsInstance(target, dict)
                target["revocation_state"] = "REVOKED"
                target["revoked_at"] = "2026-07-29T11:59:00Z"
                target["revocation_reference"] = "revocation-record-001"
                if target_name in (
                    "binding",
                    "supplied_prior_role_bindings",
                ):
                    self._rehash_supplied_snapshot(supplied_inputs)

                result = validate_role_operation(
                    contract,
                    self._request(contract),
                    **supplied_inputs,
                    now=FIXED_NOW,
                )

                self.assertEqual(RESULT_BLOCK, result.result)
                self.assertIn(expected_issue, result.issue_codes)

    def test_malformed_revoked_metadata_is_hold(self) -> None:
        cases = (
            (
                "grant",
                "SUPPLIED_ROLE_GRANT_REVOCATION_UNVERIFIABLE",
            ),
            (
                "snapshot",
                "SUPPLIED_PRIOR_ROLE_BINDINGS_REVOCATION_UNVERIFIABLE",
            ),
        )
        for case, expected_issue in cases:
            with self.subTest(case=case):
                contract = self._contract()
                supplied_inputs = self._supplied_inputs(contract)
                target = (
                    supplied_inputs["supplied_role_grant"]
                    if case == "grant"
                    else supplied_inputs["supplied_prior_role_bindings"]
                )
                self.assertIsInstance(target, dict)
                target["revocation_state"] = "REVOKED"
                target["revoked_at"] = None
                target["revocation_reference"] = None

                result = validate_role_operation(
                    contract,
                    self._request(contract),
                    **supplied_inputs,
                    now=FIXED_NOW,
                )

                self.assertEqual(RESULT_HOLD, result.result)
                self.assertIn(expected_issue, result.issue_codes)

    def test_toctou_snapshot_mutation_after_hash_binding_is_blocked(
        self,
    ) -> None:
        contract = self._contract("AUDITOR")
        supplied_inputs = self._supplied_inputs(contract)
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        self.assertIsInstance(snapshot, dict)
        bindings = snapshot["bindings"]
        self.assertIsInstance(bindings, list)
        bindings[0]["execution_context_identity"] = "changed-after-hash"

        result = validate_role_operation(
            contract,
            self._request(contract),
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn(
            "SUPPLIED_PRIOR_ROLE_BINDINGS_SNAPSHOT_HASH_MISMATCH",
            result.issue_codes,
        )

    def test_auditor_acceptance_before_builder_end_is_blocked(self) -> None:
        contract = self._contract("AUDITOR")
        supplied_inputs = self._supplied_inputs(contract)
        acceptance = supplied_inputs["supplied_role_acceptance"]
        self.assertIsInstance(acceptance, dict)
        acceptance["accepted_at"] = "2026-07-29T00:01:00Z"

        result = validate_role_operation(
            contract,
            self._request(contract),
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn(
            "AUDITOR_ACCEPTANCE_BEFORE_BUILDER_END",
            result.issue_codes,
        )

    def test_active_builder_keeps_auditor_on_hold(self) -> None:
        contract = self._contract("AUDITOR")
        supplied_inputs = self._supplied_inputs(contract)
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        self.assertIsInstance(snapshot, dict)
        bindings = snapshot["bindings"]
        self.assertIsInstance(bindings, list)
        bindings[0]["binding_state"] = "ACTIVE"
        bindings[0]["ended_at"] = None
        self._rehash_supplied_snapshot(supplied_inputs)

        result = validate_role_operation(
            contract,
            self._request(contract),
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn("BUILDER_ROLE_END_NOT_ESTABLISHED", result.issue_codes)

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

    def test_contract_acceptance_claim_needs_supplied_receiver_record(
        self,
    ) -> None:
        contract = self._contract()
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        self.assertEqual("ACCEPTED", assignment["role_acceptance"])

        result = validate_role_operation(
            contract,
            self._request(contract),
            supplied_role_grant=self._supplied_grant(contract),
            supplied_independence_evidence=self._independence_evidence(
                contract
            ),
            supplied_prior_role_bindings=[],
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn("SUPPLIED_ROLE_ACCEPTANCE_REQUIRED", result.issue_codes)

    def test_supplied_role_acceptance_binds_receiver_and_contract(
        self,
    ) -> None:
        replacements = {
            "contract_id": "different-contract",
            "contract_hash": "f" * 64,
            "task_id": "different-task",
            "role_id": "AUDITOR",
            "assignee_identity": "different-assignee",
            "execution_context_identity": "different-context",
        }
        for field, replacement in replacements.items():
            with self.subTest(field=field):
                contract = self._contract()
                acceptance = self._supplied_acceptance(contract)
                acceptance[field] = replacement
                result = validate_role_operation(
                    contract,
                    self._request(contract),
                    supplied_role_grant=self._supplied_grant(contract),
                    supplied_role_acceptance=acceptance,
                    supplied_independence_evidence=(
                        self._independence_evidence(contract)
                    ),
                    supplied_prior_role_bindings=[],
                    now=FIXED_NOW,
                )
                self.assertEqual(RESULT_BLOCK, result.result)
                self.assertIn(
                    "SUPPLIED_ROLE_ACCEPTANCE_MISMATCH",
                    result.issue_codes,
                )

    def test_supplied_role_acceptance_status_and_time_fail_closed(
        self,
    ) -> None:
        cases = (
            (
                "role_acceptance",
                "DECLINED",
                RESULT_BLOCK,
                "SUPPLIED_ROLE_ACCEPTANCE_NOT_ACCEPTED",
            ),
            (
                "accepted_at",
                "UNKNOWN",
                RESULT_HOLD,
                "SUPPLIED_ROLE_ACCEPTANCE_UNVERIFIABLE",
            ),
            (
                "accepted_at",
                "2026-07-28T23:59:59Z",
                RESULT_BLOCK,
                "SUPPLIED_ROLE_ACCEPTANCE_TIME_INVALID",
            ),
            (
                "accepted_at",
                "2026-07-30T00:00:00Z",
                RESULT_BLOCK,
                "SUPPLIED_ROLE_ACCEPTANCE_TIME_INVALID",
            ),
            (
                "accepted_at",
                "2026-07-29T13:00:00Z",
                RESULT_BLOCK,
                "SUPPLIED_ROLE_ACCEPTANCE_TIME_INVALID",
            ),
        )
        for field, replacement, expected_result, expected_issue in cases:
            with self.subTest(field=field, replacement=replacement):
                contract = self._contract()
                acceptance = self._supplied_acceptance(contract)
                acceptance[field] = replacement
                result = validate_role_operation(
                    contract,
                    self._request(contract),
                    supplied_role_grant=self._supplied_grant(contract),
                    supplied_role_acceptance=acceptance,
                    supplied_independence_evidence=(
                        self._independence_evidence(contract)
                    ),
                    supplied_prior_role_bindings=[],
                    now=FIXED_NOW,
                )
                self.assertEqual(expected_result, result.result)
                self.assertIn(expected_issue, result.issue_codes)

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
        supplied_inputs = self._supplied_inputs(contract)
        supplied_evidence = supplied_inputs[
            "supplied_independence_evidence"
        ]
        self.assertIsInstance(supplied_evidence, dict)
        supplied_evidence["runtime_execution_independence"] = "UNKNOWN"
        result = validate_role_operation(
            contract,
            request,
            **supplied_inputs,
            now=FIXED_NOW,
        )
        self.assertEqual(RESULT_HOLD, result.result)
        self.assertIn(
            "SUPPLIED_INDEPENDENCE_EVIDENCE_REQUIRED",
            result.issue_codes,
        )

    def test_different_model_name_does_not_establish_context_independence(
        self,
    ) -> None:
        contract = self._contract("AUDITOR")
        assignment = contract["assignment"]
        self.assertIsInstance(assignment, dict)
        assignment["execution_context_identity"] = "shared-supplied-context"
        self._rehash(contract)
        request = self._request(contract)
        request["execution_context_identity"] = "shared-supplied-context"
        evidence = request["independence_evidence"]
        self.assertIsInstance(evidence, dict)
        evidence["model_identity"] = "different-model-name"
        evidence["model_diversity"] = "DIFFERENT_MODEL_REQUIRED"
        bindings = request["prior_role_bindings"]
        self.assertIsInstance(bindings, list)
        bindings[0]["execution_context_identity"] = "shared-supplied-context"
        supplied_inputs = self._supplied_inputs(contract)
        supplied_evidence = supplied_inputs[
            "supplied_independence_evidence"
        ]
        snapshot = supplied_inputs["supplied_prior_role_bindings"]
        self.assertIsInstance(supplied_evidence, dict)
        self.assertIsInstance(snapshot, dict)
        supplied_evidence["model_identity"] = "different-model-name"
        supplied_evidence["model_diversity"] = "DIFFERENT_MODEL_REQUIRED"
        supplied_bindings = snapshot["bindings"]
        self.assertIsInstance(supplied_bindings, list)
        supplied_bindings[0]["execution_context_identity"] = (
            "shared-supplied-context"
        )
        self._rehash_supplied_snapshot(supplied_inputs)

        result = validate_role_operation(
            contract,
            request,
            **supplied_inputs,
            now=FIXED_NOW,
        )

        self.assertEqual(RESULT_BLOCK, result.result)
        self.assertIn(
            "CONTEXT_INDEPENDENCE_VIOLATION",
            result.issue_codes,
        )


if __name__ == "__main__":
    unittest.main()
