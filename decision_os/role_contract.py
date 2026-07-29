"""Validator-level fail-closed checks for Stage 4 Role Contracts.

This module is deliberately read-only.  It validates one fixed Role Contract
against one requested operation and supplied records, then returns a decision.
It does not issue or authenticate records, assign a role, invoke a specialist,
repair a target, persist replay state, or advance a stage.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


RESULT_ACTIVE = "ACTIVE"
RESULT_HOLD = "HOLD"
RESULT_BLOCK = "BLOCK"
RESULT_INVALID = "INVALID"

ROLE_BUILDER = "BUILDER"
ROLE_AUDITOR = "AUDITOR"
SUPPORTED_ROLES = frozenset((ROLE_BUILDER, ROLE_AUDITOR))

ROLE_CONTEXT_VALUES = frozenset(
    (
        "SAME_CONTEXT_ALLOWED",
        "FRESH_CONTEXT_REQUIRED",
        "DISTINCT_CONTEXT_REQUIRED",
    )
)
SOURCE_REVIEW_VALUES = frozenset(
    (
        "FULL_PRIOR_CONTEXT_ALLOWED",
        "FIXED_ARTIFACTS_ONLY",
        "INDEPENDENT_EVIDENCE_SELECTION_REQUIRED",
    )
)
RUNTIME_EXECUTION_VALUES = frozenset(
    (
        "NOT_REQUIRED",
        "REQUIRED_NOT_ESTABLISHED",
        "READ_ONLY_REEXECUTION_REQUIRED",
        "SEPARATE_ENV_REEXECUTION_REQUIRED",
        "EXECUTION_RECORD_SUPPLIED",
    )
)
MODEL_DIVERSITY_VALUES = frozenset(
    ("SAME_MODEL_ALLOWED", "DIFFERENT_MODEL_REQUIRED")
)

OPERATION_VALUES = frozenset(
    (
        "IMPLEMENT_DESIGN",
        "READ_TARGET",
        "AUDIT_TARGET",
        "VERIFY_TARGET_IMMUTABILITY",
        "RUN_TESTS",
        "RUN_READ_ONLY_TESTS",
        "PRODUCE_EXIT_RECEIPT",
        "GENERATE_COVERAGE_GAP_RECOMMENDATION",
        "SELF_AUDIT",
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
    )
)

BUILDER_ALLOWED = frozenset(
    (
        "IMPLEMENT_DESIGN",
        "READ_TARGET",
        "RUN_TESTS",
        "PRODUCE_EXIT_RECEIPT",
        "GENERATE_COVERAGE_GAP_RECOMMENDATION",
    )
)
AUDITOR_ALLOWED = frozenset(
    (
        "READ_TARGET",
        "AUDIT_TARGET",
        "VERIFY_TARGET_IMMUTABILITY",
        "RUN_READ_ONLY_TESTS",
        "PRODUCE_EXIT_RECEIPT",
        "GENERATE_COVERAGE_GAP_RECOMMENDATION",
    )
)
BUILDER_REQUIRED_FORBIDDEN = frozenset(
    (
        "AUDIT_TARGET",
        "SELF_AUDIT",
        "MODIFY_ROLE_GRANT",
        "MODIFY_SPECIALIST_LENS",
        "MODIFY_OUTSIDE_TARGET",
        "MERGE",
        "POST",
        "INVOKE_SPECIALIST",
        "START_STAGE_5",
    )
)
AUDITOR_REQUIRED_FORBIDDEN = frozenset(
    (
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
    )
)

TOP_LEVEL_FIELDS = frozenset(
    (
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
    )
)
SECTION_FIELDS = {
    "contract_identity": frozenset(("contract_id", "version", "contract_hash")),
    "assignment": frozenset(
        (
            "task_id",
            "role_id",
            "grant_type",
            "assignment_authority",
            "shin_gate_reference",
            "assignee_identity",
            "execution_context_identity",
            "role_acceptance",
        )
    ),
    "owned_responsibility": frozenset(
        ("responsibility", "exact_target", "next_owner")
    ),
    "operations": frozenset(("allowed_operations", "forbidden_operations")),
    "task_artifact_packet": frozenset(
        ("repo", "head", "paths", "artifact_hashes", "as_of")
    ),
    "specialist_lens": frozenset(("lens_id", "lens_version", "lens_hash")),
    "independence_profile": frozenset(
        (
            "role_context_independence",
            "source_review_independence",
            "runtime_execution_independence",
            "model_diversity",
        )
    ),
    "completion": frozenset(
        ("completion_line", "required_exit_receipt", "coverage_gap_required")
    ),
    "lifecycle": frozenset(
        ("issued_at", "expires_at", "revocation_reference", "status")
    ),
    "coverage_gap_recommendation": frozenset(
        (
            "coverage_completed",
            "coverage_gap",
            "recommended_specialist",
            "reason",
            "exact_target",
            "required_evidence",
            "urgency",
            "assignment_authority_required",
            "automatic_invocation",
        )
    ),
}

REQUEST_FIELDS = frozenset(
    (
        "operation",
        "task_id",
        "role_id",
        "assignee_identity",
        "execution_context_identity",
        "task_artifact_packet",
        "specialist_lens",
        "independence_evidence",
        "prior_role_bindings",
        "target_immutability",
        "coverage_gap_recommendation",
    )
)
INDEPENDENCE_EVIDENCE_FIELDS = frozenset(
    (
        "record_identity",
        "task_id",
        "role_id",
        "assignee_identity",
        "execution_context_identity",
        "role_context_independence",
        "source_review_independence",
        "runtime_execution_independence",
        "model_diversity",
        "model_identity",
        "source_review_evidence_reference",
        "runtime_execution_evidence_reference",
    )
)
PRIOR_BINDING_FIELDS = frozenset(
    (
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
)
TARGET_IMMUTABILITY_FIELDS = frozenset(
    (
        "before_head",
        "after_head",
        "before_artifact_hashes",
        "after_artifact_hashes",
    )
)
SUPPLIED_RECORD_STATE_FIELDS = frozenset(
    (
        "record_identity",
        "snapshot_identity",
        "as_of",
        "revocation_state",
        "revoked_at",
        "revocation_reference",
    )
)
SUPPLIED_ROLE_GRANT_FIELDS = frozenset(
    (
        "contract_id",
        "contract_hash",
        "task_id",
        "role_id",
        "grant_type",
        "assignment_authority",
        "shin_gate_reference",
        "assignee_identity",
        "execution_context_identity",
    )
) | SUPPLIED_RECORD_STATE_FIELDS
SUPPLIED_ROLE_ACCEPTANCE_FIELDS = frozenset(
    (
        "contract_id",
        "contract_hash",
        "task_id",
        "role_id",
        "assignee_identity",
        "execution_context_identity",
        "role_acceptance",
        "accepted_at",
        "grant_record_identity",
    )
) | SUPPLIED_RECORD_STATE_FIELDS
SUPPLIED_INDEPENDENCE_EVIDENCE_FIELDS = (
    INDEPENDENCE_EVIDENCE_FIELDS
    | SUPPLIED_RECORD_STATE_FIELDS
    | frozenset(
        (
            "contract_id",
            "contract_hash",
            "prior_role_bindings_snapshot_identity",
            "prior_role_bindings_snapshot_hash",
        )
    )
)
SUPPLIED_PRIOR_BINDING_FIELDS = (
    PRIOR_BINDING_FIELDS | SUPPLIED_RECORD_STATE_FIELDS
)
SUPPLIED_PRIOR_BINDING_SNAPSHOT_FIELDS = frozenset(
    (
        "snapshot_identity",
        "snapshot_hash",
        "contract_id",
        "contract_hash",
        "task_id",
        "as_of",
        "revocation_state",
        "revoked_at",
        "revocation_reference",
        "completeness_boundary",
        "bindings",
    )
)
COMPLETENESS_BOUNDARY_FIELDS = frozenset(
    (
        "scope",
        "task_id",
        "from",
        "through",
        "included_roles",
        "state",
        "expected_record_identities",
    )
)

REVOCATION_STATES = frozenset(("NOT_REVOKED", "REVOKED", "UNKNOWN"))

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
_UNKNOWN_VALUES = frozenset(("", "UNKNOWN", "UNVERIFIABLE", "NONE"))


@dataclass(frozen=True)
class RoleContractAssessment:
    """One deterministic Stage 4 role-operation assessment."""

    result: str
    issue_codes: tuple[str, ...]

    @property
    def decision_line(self) -> str:
        if self.result == RESULT_ACTIVE:
            return "ACTIVE — VALIDATOR CONDITIONS SATISFIED"
        issue = self.issue_codes[0] if self.issue_codes else "UNSPECIFIED"
        return f"{self.result} — {issue.replace('_', ' ')}"


def _assessment(result: str, *issue_codes: str) -> RoleContractAssessment:
    return RoleContractAssessment(result, tuple(dict.fromkeys(issue_codes)))


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() not in _UNKNOWN_VALUES


def _is_string_sequence(value: Any, *, nonempty: bool = True) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes, bytearray))
        and (bool(value) or not nonempty)
        and all(_is_nonempty_string(item) for item in value)
    )


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def compute_contract_hash(contract: Mapping[str, Any]) -> str:
    """Return the canonical SHA-256 with ``contract_hash`` blanked."""

    canonical = deepcopy(dict(contract))
    identity = canonical.get("contract_identity")
    if not isinstance(identity, Mapping):
        raise ValueError("contract_identity is required")
    canonical["contract_identity"] = dict(identity)
    canonical["contract_identity"]["contract_hash"] = ""
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def contract_with_hash(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-compatible copy with its canonical hash populated."""

    value = deepcopy(dict(contract))
    identity = value.get("contract_identity")
    if not isinstance(identity, Mapping):
        raise ValueError("contract_identity is required")
    value["contract_identity"] = dict(identity)
    value["contract_identity"]["contract_hash"] = compute_contract_hash(value)
    return value


def compute_prior_role_bindings_snapshot_hash(
    snapshot: Mapping[str, Any],
) -> str:
    """Return the canonical SHA-256 with ``snapshot_hash`` blanked."""

    canonical = deepcopy(dict(snapshot))
    if "snapshot_hash" not in canonical:
        raise ValueError("snapshot_hash is required")
    canonical["snapshot_hash"] = ""
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _contract_shape_issue(contract: Any) -> str | None:
    if not isinstance(contract, Mapping):
        return "ROLE_CONTRACT_REQUIRED"
    if set(contract) != TOP_LEVEL_FIELDS:
        return "INVALID_CONTRACT_STRUCTURE"
    for section_name, fields in SECTION_FIELDS.items():
        section = contract.get(section_name)
        if not isinstance(section, Mapping) or set(section) != fields:
            return "INVALID_CONTRACT_STRUCTURE"
    return None


def _request_shape_issue(request: Any) -> str | None:
    if not isinstance(request, Mapping):
        return "OPERATION_REQUEST_REQUIRED"
    if not set(request).issubset(REQUEST_FIELDS):
        return "INVALID_OPERATION_REQUEST"
    required = REQUEST_FIELDS - {
        "coverage_gap_recommendation",
        "target_immutability",
    }
    if not required.issubset(request):
        return "OPERATION_REQUEST_INCOMPLETE"
    return None


def _valid_coverage_gap(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    if set(value) != SECTION_FIELDS["coverage_gap_recommendation"]:
        return False
    if (
        not isinstance(value.get("coverage_completed"), bool)
        or not _is_nonempty_string(value.get("coverage_gap"))
        or value.get("recommended_specialist")
        not in ("NONE", ROLE_BUILDER, ROLE_AUDITOR)
        or not _is_nonempty_string(value.get("reason"))
        or not _is_string_sequence(value.get("exact_target"))
        or not _is_string_sequence(value.get("required_evidence"))
        or value.get("urgency") not in ("LOW", "MEDIUM", "HIGH", "NONE")
        or value.get("assignment_authority_required") is not True
        or value.get("automatic_invocation") is not False
    ):
        return False
    return True


def _packet_valid(packet: Any) -> bool:
    if not isinstance(packet, Mapping):
        return False
    if set(packet) != SECTION_FIELDS["task_artifact_packet"]:
        return False
    paths = packet.get("paths")
    hashes = packet.get("artifact_hashes")
    if (
        not _is_nonempty_string(packet.get("repo"))
        or not isinstance(packet.get("head"), str)
        or _GIT_HEAD_RE.fullmatch(packet["head"]) is None
        or not _is_string_sequence(paths)
        or len(paths) != len(set(paths))
        or not isinstance(hashes, Mapping)
        or set(hashes) != set(paths)
        or not all(
            isinstance(digest, str) and _SHA256_RE.fullmatch(digest)
            for digest in hashes.values()
        )
        or _parse_timestamp(packet.get("as_of")) is None
    ):
        return False
    return True


def _lens_valid(lens: Any) -> bool:
    return (
        isinstance(lens, Mapping)
        and set(lens) == SECTION_FIELDS["specialist_lens"]
        and _is_nonempty_string(lens.get("lens_id"))
        and _is_nonempty_string(lens.get("lens_version"))
        and isinstance(lens.get("lens_hash"), str)
        and _SHA256_RE.fullmatch(lens["lens_hash"]) is not None
    )


def _profile_valid(profile: Any) -> bool:
    return (
        isinstance(profile, Mapping)
        and set(profile) == SECTION_FIELDS["independence_profile"]
        and profile.get("role_context_independence") in ROLE_CONTEXT_VALUES
        and profile.get("source_review_independence") in SOURCE_REVIEW_VALUES
        and profile.get("runtime_execution_independence")
        in RUNTIME_EXECUTION_VALUES
        and profile.get("model_diversity") in MODEL_DIVERSITY_VALUES
    )


def _contract_semantic_issue(contract: Mapping[str, Any]) -> str | None:
    identity = contract["contract_identity"]
    assignment = contract["assignment"]
    ownership = contract["owned_responsibility"]
    operations = contract["operations"]
    packet = contract["task_artifact_packet"]
    lens = contract["specialist_lens"]
    profile = contract["independence_profile"]
    completion = contract["completion"]
    lifecycle = contract["lifecycle"]
    coverage = contract["coverage_gap_recommendation"]

    if (
        not _is_nonempty_string(identity["contract_id"])
        or identity["version"] != "0.1"
        or not isinstance(identity["contract_hash"], str)
        or _SHA256_RE.fullmatch(identity["contract_hash"]) is None
    ):
        return "INVALID_CONTRACT_IDENTITY"
    try:
        expected_hash = compute_contract_hash(contract)
    except (TypeError, ValueError):
        return "INVALID_CONTRACT_IDENTITY"
    if identity["contract_hash"] != expected_hash:
        return "CONTRACT_HASH_MISMATCH"

    role = assignment["role_id"]
    if role not in SUPPORTED_ROLES:
        return "UNSUPPORTED_ROLE"
    if assignment["grant_type"] != "EXPLICIT_ROLE_GRANT":
        return "EXPLICIT_ROLE_GRANT_REQUIRED"
    if assignment["assignment_authority"] != "Shin":
        return "ASSIGNMENT_AUTHORITY_REQUIRED"
    if not _is_nonempty_string(assignment["shin_gate_reference"]):
        return "SHIN_GATE_REFERENCE_REQUIRED"
    if (
        not _is_nonempty_string(assignment["task_id"])
        or not _is_nonempty_string(assignment["assignee_identity"])
        or not _is_nonempty_string(assignment["execution_context_identity"])
    ):
        return "ASSIGNMENT_BINDING_REQUIRED"
    if assignment["role_acceptance"] != "ACCEPTED":
        return "ROLE_ACCEPTANCE_REQUIRED"

    if (
        not _is_nonempty_string(ownership["responsibility"])
        or not _is_string_sequence(ownership["exact_target"])
        or not _is_nonempty_string(ownership["next_owner"])
    ):
        return "INVALID_OWNED_RESPONSIBILITY"
    if not _packet_valid(packet):
        return "TASK_ARTIFACT_PACKET_REQUIRED"
    if tuple(ownership["exact_target"]) != tuple(packet["paths"]):
        return "TARGET_SCOPE_MISMATCH"
    if not _lens_valid(lens):
        return "SPECIALIST_LENS_REQUIRED"
    if not _profile_valid(profile):
        return "INDEPENDENCE_PROFILE_INVALID"
    if role == ROLE_AUDITOR and (
        profile["role_context_independence"]
        != "DISTINCT_CONTEXT_REQUIRED"
    ):
        return "AUDITOR_DISTINCT_CONTEXT_REQUIRED"

    allowed = operations["allowed_operations"]
    forbidden = operations["forbidden_operations"]
    if (
        not _is_string_sequence(allowed)
        or not _is_string_sequence(forbidden)
        or len(allowed) != len(set(allowed))
        or len(forbidden) != len(set(forbidden))
        or not set((*allowed, *forbidden)).issubset(OPERATION_VALUES)
        or set(allowed) & set(forbidden)
    ):
        return "INVALID_OPERATION_BOUNDARY"
    role_allowed = BUILDER_ALLOWED if role == ROLE_BUILDER else AUDITOR_ALLOWED
    role_forbidden = (
        BUILDER_REQUIRED_FORBIDDEN
        if role == ROLE_BUILDER
        else AUDITOR_REQUIRED_FORBIDDEN
    )
    if not set(allowed).issubset(role_allowed) or not role_forbidden.issubset(
        forbidden
    ):
        return "ROLE_OPERATION_BOUNDARY_INCOMPLETE"

    if (
        not _is_nonempty_string(completion["completion_line"])
        or completion["required_exit_receipt"] is not True
        or completion["coverage_gap_required"] is not True
    ):
        return "COMPLETION_CONTRACT_INCOMPLETE"
    issued = _parse_timestamp(lifecycle["issued_at"])
    expires = _parse_timestamp(lifecycle["expires_at"])
    if issued is None or expires is None or issued >= expires:
        return "INVALID_LIFECYCLE"
    if lifecycle["status"] not in ("ACTIVE", "EXPIRED", "REVOKED"):
        return "INVALID_LIFECYCLE"
    revocation = lifecycle["revocation_reference"]
    if revocation is not None and not _is_nonempty_string(revocation):
        return "INVALID_LIFECYCLE"
    if not _valid_coverage_gap(coverage):
        return "COVERAGE_RECOMMENDATION_NOT_INERT"
    if tuple(coverage["exact_target"]) != tuple(packet["paths"]):
        return "COVERAGE_TARGET_MISMATCH"
    if coverage["coverage_gap"] == "NONE DETECTED" and (
        coverage["coverage_completed"] is not True
        or coverage["recommended_specialist"] != "NONE"
        or coverage["urgency"] != "NONE"
    ):
        return "COVERAGE_RECOMMENDATION_INCONSISTENT"
    if coverage["coverage_gap"] != "NONE DETECTED" and (
        coverage["recommended_specialist"] == "NONE"
        or coverage["urgency"] == "NONE"
    ):
        return "COVERAGE_RECOMMENDATION_INCONSISTENT"
    return None


def _claim_independence_evidence_valid(evidence: Any) -> bool:
    return (
        isinstance(evidence, Mapping)
        and set(evidence) == INDEPENDENCE_EVIDENCE_FIELDS
        and evidence.get("role_id") in SUPPORTED_ROLES
        and all(
            _is_nonempty_string(evidence.get(field))
            for field in (
                "record_identity",
                "task_id",
                "assignee_identity",
                "execution_context_identity",
                "model_identity",
                "source_review_evidence_reference",
                "runtime_execution_evidence_reference",
            )
        )
        and evidence.get("role_context_independence")
        in ROLE_CONTEXT_VALUES
        and evidence.get("source_review_independence")
        in SOURCE_REVIEW_VALUES
        and evidence.get("runtime_execution_independence")
        in RUNTIME_EXECUTION_VALUES
        and evidence.get("model_diversity") in MODEL_DIVERSITY_VALUES
    )


def _claim_prior_binding_map(
    bindings: Any,
) -> dict[str, Mapping[str, Any]] | None:
    if (
        not isinstance(bindings, Sequence)
        or isinstance(bindings, (str, bytes, bytearray))
    ):
        return None
    normalized: dict[str, Mapping[str, Any]] = {}
    for binding in bindings:
        if (
            not isinstance(binding, Mapping)
            or set(binding) != PRIOR_BINDING_FIELDS
            or binding.get("role_id") not in SUPPORTED_ROLES
            or binding.get("binding_state") not in ("ACTIVE", "ENDED")
            or not all(
                _is_nonempty_string(binding.get(field))
                for field in (
                    "record_identity",
                    "task_id",
                    "assignee_identity",
                    "execution_context_identity",
                    "model_identity",
                )
            )
        ):
            return None
        bound_at = _parse_timestamp(binding.get("bound_at"))
        ended_at = _parse_timestamp(binding.get("ended_at"))
        if (
            bound_at is None
            or (
                binding["binding_state"] == "ACTIVE"
                and binding.get("ended_at") is not None
            )
            or (
                binding["binding_state"] == "ENDED"
                and (ended_at is None or ended_at <= bound_at)
            )
        ):
            return None
        record_identity = binding["record_identity"]
        if record_identity in normalized:
            return None
        normalized[record_identity] = binding
    return normalized


def _supplied_record_state_assessment(
    record: Mapping[str, Any],
    prefix: str,
    current: datetime,
) -> RoleContractAssessment | None:
    if (
        not _is_nonempty_string(record.get("record_identity"))
        or not _is_nonempty_string(record.get("snapshot_identity"))
    ):
        return _assessment(RESULT_HOLD, f"{prefix}_REQUIRED")
    as_of = _parse_timestamp(record.get("as_of"))
    if as_of is None:
        return _assessment(RESULT_HOLD, f"{prefix}_AS_OF_UNVERIFIABLE")
    if as_of < current:
        return _assessment(RESULT_HOLD, f"{prefix}_STALE")
    if as_of > current:
        return _assessment(RESULT_BLOCK, f"{prefix}_TIME_INVALID")

    state = record.get("revocation_state")
    revoked_at = record.get("revoked_at")
    reference = record.get("revocation_reference")
    if state not in REVOCATION_STATES or state == "UNKNOWN":
        return _assessment(
            RESULT_HOLD,
            f"{prefix}_REVOCATION_UNVERIFIABLE",
        )
    if state == "REVOKED":
        revoked_at_value = _parse_timestamp(revoked_at)
        if (
            revoked_at_value is None
            or revoked_at_value > as_of
            or not _is_nonempty_string(reference)
        ):
            return _assessment(
                RESULT_HOLD,
                f"{prefix}_REVOCATION_UNVERIFIABLE",
            )
        return _assessment(RESULT_BLOCK, f"{prefix}_REVOKED")
    if revoked_at is not None or reference is not None:
        return _assessment(
            RESULT_HOLD,
            f"{prefix}_REVOCATION_UNVERIFIABLE",
        )
    return None


def _supplied_role_grant_assessment(
    contract: Mapping[str, Any],
    supplied_role_grant: Any,
    current: datetime,
) -> RoleContractAssessment | None:
    if (
        not isinstance(supplied_role_grant, Mapping)
        or set(supplied_role_grant) != SUPPLIED_ROLE_GRANT_FIELDS
    ):
        return _assessment(RESULT_HOLD, "SUPPLIED_ROLE_GRANT_REQUIRED")
    identity = contract["contract_identity"]
    assignment = contract["assignment"]
    expected = {
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
    if any(
        supplied_role_grant[field] != expected_value
        for field, expected_value in expected.items()
    ):
        return _assessment(RESULT_BLOCK, "SUPPLIED_ROLE_GRANT_MISMATCH")
    return _supplied_record_state_assessment(
        supplied_role_grant,
        "SUPPLIED_ROLE_GRANT",
        current,
    )


def _supplied_role_acceptance_assessment(
    contract: Mapping[str, Any],
    supplied_role_acceptance: Any,
    supplied_role_grant: Mapping[str, Any],
    current: datetime,
) -> RoleContractAssessment | None:
    if (
        not isinstance(supplied_role_acceptance, Mapping)
        or set(supplied_role_acceptance)
        != SUPPLIED_ROLE_ACCEPTANCE_FIELDS
    ):
        return _assessment(
            RESULT_HOLD,
            "SUPPLIED_ROLE_ACCEPTANCE_REQUIRED",
        )

    identity = contract["contract_identity"]
    assignment = contract["assignment"]
    expected_binding = {
        "contract_id": identity["contract_id"],
        "contract_hash": identity["contract_hash"],
        "task_id": assignment["task_id"],
        "role_id": assignment["role_id"],
        "assignee_identity": assignment["assignee_identity"],
        "execution_context_identity": assignment[
            "execution_context_identity"
        ],
        "grant_record_identity": supplied_role_grant["record_identity"],
    }
    if any(
        supplied_role_acceptance[field] != expected
        for field, expected in expected_binding.items()
    ):
        return _assessment(
            RESULT_BLOCK,
            "SUPPLIED_ROLE_ACCEPTANCE_MISMATCH",
        )
    if supplied_role_acceptance["role_acceptance"] != "ACCEPTED":
        return _assessment(
            RESULT_BLOCK,
            "SUPPLIED_ROLE_ACCEPTANCE_NOT_ACCEPTED",
        )
    state_assessment = _supplied_record_state_assessment(
        supplied_role_acceptance,
        "SUPPLIED_ROLE_ACCEPTANCE",
        current,
    )
    if state_assessment is not None:
        return state_assessment

    accepted_at = _parse_timestamp(supplied_role_acceptance["accepted_at"])
    if accepted_at is None:
        return _assessment(
            RESULT_HOLD,
            "SUPPLIED_ROLE_ACCEPTANCE_UNVERIFIABLE",
        )
    lifecycle = contract["lifecycle"]
    issued = _parse_timestamp(lifecycle["issued_at"])
    expires = _parse_timestamp(lifecycle["expires_at"])
    as_of = _parse_timestamp(supplied_role_acceptance["as_of"])
    assert issued is not None and expires is not None and as_of is not None
    if accepted_at < issued or accepted_at >= expires or accepted_at > as_of:
        return _assessment(
            RESULT_BLOCK,
            "SUPPLIED_ROLE_ACCEPTANCE_TIME_INVALID",
        )
    return None


def _supplied_prior_role_bindings_assessment(
    contract: Mapping[str, Any],
    supplied_prior_role_bindings: Any,
    current: datetime,
) -> tuple[
    RoleContractAssessment | None,
    dict[str, Mapping[str, Any]] | None,
]:
    if (
        not isinstance(supplied_prior_role_bindings, Mapping)
        or set(supplied_prior_role_bindings)
        != SUPPLIED_PRIOR_BINDING_SNAPSHOT_FIELDS
    ):
        return (
            _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_REQUIRED",
            ),
            None,
        )
    snapshot = supplied_prior_role_bindings
    identity = contract["contract_identity"]
    assignment = contract["assignment"]
    if (
        snapshot.get("contract_id") != identity["contract_id"]
        or snapshot.get("contract_hash") != identity["contract_hash"]
        or snapshot.get("task_id") != assignment["task_id"]
    ):
        return (
            _assessment(
                RESULT_BLOCK,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_SNAPSHOT_MISMATCH",
            ),
            None,
        )
    if (
        not _is_nonempty_string(snapshot.get("snapshot_identity"))
        or not isinstance(snapshot.get("snapshot_hash"), str)
        or _SHA256_RE.fullmatch(snapshot["snapshot_hash"]) is None
    ):
        return (
            _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_REQUIRED",
            ),
            None,
        )

    snapshot_as_of = _parse_timestamp(snapshot.get("as_of"))
    if snapshot_as_of is None:
        return (
            _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_AS_OF_UNVERIFIABLE",
            ),
            None,
        )
    if snapshot_as_of < current:
        return (
            _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_STALE",
            ),
            None,
        )
    if snapshot_as_of > current:
        return (
            _assessment(
                RESULT_BLOCK,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_TIME_INVALID",
            ),
            None,
        )
    state = snapshot.get("revocation_state")
    if state not in REVOCATION_STATES or state == "UNKNOWN":
        return (
            _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_REVOCATION_UNVERIFIABLE",
            ),
            None,
        )
    if state == "REVOKED":
        revoked_at_value = _parse_timestamp(snapshot.get("revoked_at"))
        if (
            revoked_at_value is None
            or revoked_at_value > snapshot_as_of
            or not _is_nonempty_string(
                snapshot.get("revocation_reference")
            )
        ):
            return (
                _assessment(
                    RESULT_HOLD,
                    "SUPPLIED_PRIOR_ROLE_BINDINGS_REVOCATION_UNVERIFIABLE",
                ),
                None,
            )
        return (
            _assessment(
                RESULT_BLOCK,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_REVOKED",
            ),
            None,
        )
    if (
        snapshot.get("revoked_at") is not None
        or snapshot.get("revocation_reference") is not None
    ):
        return (
            _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_REVOCATION_UNVERIFIABLE",
            ),
            None,
        )

    try:
        expected_hash = compute_prior_role_bindings_snapshot_hash(snapshot)
    except (TypeError, ValueError):
        return (
            _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_REQUIRED",
            ),
            None,
        )
    if snapshot["snapshot_hash"] != expected_hash:
        return (
            _assessment(
                RESULT_BLOCK,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_SNAPSHOT_HASH_MISMATCH",
            ),
            None,
        )

    boundary = snapshot.get("completeness_boundary")
    if (
        not isinstance(boundary, Mapping)
        or set(boundary) != COMPLETENESS_BOUNDARY_FIELDS
        or boundary.get("scope") != "ALL_PRIOR_ROLE_BINDINGS_FOR_TASK"
        or boundary.get("task_id") != assignment["task_id"]
        or boundary.get("from") != "TASK_INCEPTION"
        or boundary.get("through") != snapshot["as_of"]
        or not isinstance(boundary.get("included_roles"), list)
        or len(boundary["included_roles"]) != 2
        or set(boundary["included_roles"]) != SUPPORTED_ROLES
        or boundary.get("state") != "COMPLETE"
        or not _is_string_sequence(
            boundary.get("expected_record_identities"),
            nonempty=False,
        )
        or len(boundary["expected_record_identities"])
        != len(set(boundary["expected_record_identities"]))
    ):
        return (
            _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_INCOMPLETE",
            ),
            None,
        )

    bindings = snapshot.get("bindings")
    if (
        not isinstance(bindings, Sequence)
        or isinstance(bindings, (str, bytes, bytearray))
    ):
        return (
            _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_REQUIRED",
            ),
            None,
        )
    normalized: dict[str, Mapping[str, Any]] = {}
    for binding in bindings:
        if (
            not isinstance(binding, Mapping)
            or set(binding) != SUPPLIED_PRIOR_BINDING_FIELDS
            or binding.get("role_id") not in SUPPORTED_ROLES
            or binding.get("binding_state") not in ("ACTIVE", "ENDED")
            or not all(
                _is_nonempty_string(binding.get(field))
                for field in (
                    "record_identity",
                    "snapshot_identity",
                    "task_id",
                    "assignee_identity",
                    "execution_context_identity",
                    "model_identity",
                )
            )
        ):
            return (
                _assessment(
                    RESULT_HOLD,
                    "SUPPLIED_PRIOR_ROLE_BINDINGS_REQUIRED",
                ),
                None,
            )
        if (
            binding["snapshot_identity"] != snapshot["snapshot_identity"]
            or binding["task_id"] != assignment["task_id"]
        ):
            return (
                _assessment(
                    RESULT_BLOCK,
                    "SUPPLIED_PRIOR_ROLE_BINDINGS_SNAPSHOT_MISMATCH",
                ),
                None,
            )
        state_assessment = _supplied_record_state_assessment(
            binding,
            "SUPPLIED_PRIOR_ROLE_BINDING",
            current,
        )
        if state_assessment is not None:
            return state_assessment, None
        bound_at = _parse_timestamp(binding.get("bound_at"))
        ended_at = _parse_timestamp(binding.get("ended_at"))
        if (
            bound_at is None
            or bound_at > snapshot_as_of
            or (
                binding["binding_state"] == "ACTIVE"
                and binding.get("ended_at") is not None
            )
            or (
                binding["binding_state"] == "ENDED"
                and (
                    ended_at is None
                    or ended_at <= bound_at
                    or ended_at > snapshot_as_of
                )
            )
        ):
            return (
                _assessment(
                    RESULT_HOLD,
                    "SUPPLIED_PRIOR_ROLE_BINDING_TIME_UNVERIFIABLE",
                ),
                None,
            )
        record_identity = binding["record_identity"]
        if record_identity in normalized:
            return (
                _assessment(
                    RESULT_BLOCK,
                    "SUPPLIED_RECORD_IDENTITY_REPLAY",
                ),
                None,
            )
        normalized[record_identity] = binding

    expected_identities = set(boundary["expected_record_identities"])
    if expected_identities != set(normalized):
        return (
            _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_INCOMPLETE",
            ),
            None,
        )
    return None, normalized


def _supplied_independence_evidence_shape_valid(evidence: Any) -> bool:
    return (
        isinstance(evidence, Mapping)
        and set(evidence) == SUPPLIED_INDEPENDENCE_EVIDENCE_FIELDS
        and evidence.get("role_id") in SUPPORTED_ROLES
        and all(
            _is_nonempty_string(evidence.get(field))
            for field in (
                "record_identity",
                "snapshot_identity",
                "contract_id",
                "contract_hash",
                "task_id",
                "assignee_identity",
                "execution_context_identity",
                "model_identity",
                "source_review_evidence_reference",
                "runtime_execution_evidence_reference",
                "prior_role_bindings_snapshot_identity",
                "prior_role_bindings_snapshot_hash",
            )
        )
        and evidence.get("role_context_independence")
        in ROLE_CONTEXT_VALUES
        and evidence.get("source_review_independence")
        in SOURCE_REVIEW_VALUES
        and evidence.get("runtime_execution_independence")
        in RUNTIME_EXECUTION_VALUES
        and evidence.get("model_diversity") in MODEL_DIVERSITY_VALUES
    )


def _independence_assessment(
    contract: Mapping[str, Any],
    request: Mapping[str, Any],
    supplied_role_acceptance: Mapping[str, Any],
    supplied_independence_evidence: Any,
    supplied_prior_role_bindings: Mapping[str, Any],
    supplied_binding_map: Mapping[str, Mapping[str, Any]],
    current: datetime,
) -> RoleContractAssessment | None:
    assignment = contract["assignment"]
    required = contract["independence_profile"]
    claimed_evidence = request["independence_evidence"]
    claimed_bindings = request["prior_role_bindings"]

    if not _supplied_independence_evidence_shape_valid(
        supplied_independence_evidence
    ):
        return _assessment(
            RESULT_HOLD,
            "SUPPLIED_INDEPENDENCE_EVIDENCE_REQUIRED",
        )
    evidence = supplied_independence_evidence
    identity = contract["contract_identity"]
    evidence_binding = {
        "contract_id": identity["contract_id"],
        "contract_hash": identity["contract_hash"],
        "task_id": assignment["task_id"],
        "role_id": assignment["role_id"],
        "assignee_identity": assignment["assignee_identity"],
        "execution_context_identity": assignment[
            "execution_context_identity"
        ],
    }
    if any(
        evidence[field] != expected
        for field, expected in evidence_binding.items()
    ):
        return _assessment(
            RESULT_BLOCK,
            "SUPPLIED_INDEPENDENCE_EVIDENCE_MISMATCH",
        )
    state_assessment = _supplied_record_state_assessment(
        evidence,
        "SUPPLIED_INDEPENDENCE_EVIDENCE",
        current,
    )
    if state_assessment is not None:
        return state_assessment

    snapshot_identity = supplied_prior_role_bindings["snapshot_identity"]
    snapshot_hash = supplied_prior_role_bindings["snapshot_hash"]
    if (
        evidence["prior_role_bindings_snapshot_identity"]
        != snapshot_identity
        or evidence["prior_role_bindings_snapshot_hash"] != snapshot_hash
    ):
        return _assessment(
            RESULT_BLOCK,
            "SUPPLIED_PRIOR_ROLE_BINDINGS_SNAPSHOT_MISMATCH",
        )

    supplied_projection = {
        field: evidence[field] for field in INDEPENDENCE_EVIDENCE_FIELDS
    }
    evidence_claim_mismatch = (
        not _claim_independence_evidence_valid(claimed_evidence)
        or dict(claimed_evidence) != supplied_projection
    )
    claimed_binding_map = _claim_prior_binding_map(claimed_bindings)
    supplied_binding_projection = {
        record_identity: {
            field: binding[field] for field in PRIOR_BINDING_FIELDS
        }
        for record_identity, binding in supplied_binding_map.items()
    }
    binding_claim_mismatch = claimed_binding_map is None or (
        {
            record_identity: dict(binding)
            for record_identity, binding in claimed_binding_map.items()
        }
        != supplied_binding_projection
    )
    claim_mismatch_codes = (
        *(
            ("SUPPLIED_INDEPENDENCE_EVIDENCE_CLAIM_MISMATCH",)
            if evidence_claim_mismatch
            else ()
        ),
        *(
            ("SUPPLIED_PRIOR_ROLE_BINDINGS_CLAIM_MISMATCH",)
            if binding_claim_mismatch
            else ()
        ),
    )

    same_task = [
        binding
        for binding in supplied_binding_map.values()
        if binding["task_id"] == assignment["task_id"]
    ]
    builder_bindings = [
        binding
        for binding in same_task
        if binding["role_id"] == ROLE_BUILDER
    ]
    if assignment["role_id"] == ROLE_AUDITOR:
        if not builder_bindings:
            return _assessment(
                RESULT_HOLD,
                "SUPPLIED_PRIOR_ROLE_BINDINGS_INCOMPLETE",
            )
        if any(
            binding["binding_state"] != "ENDED"
            or binding["ended_at"] is None
            for binding in builder_bindings
        ):
            return _assessment(
                RESULT_HOLD,
                "BUILDER_ROLE_END_NOT_ESTABLISHED",
            )
        accepted_at = _parse_timestamp(supplied_role_acceptance["accepted_at"])
        builder_ends = [
            _parse_timestamp(binding["ended_at"])
            for binding in builder_bindings
        ]
        assert accepted_at is not None and all(
            ended_at is not None for ended_at in builder_ends
        )
        if accepted_at <= max(
            ended_at for ended_at in builder_ends if ended_at is not None
        ):
            return _assessment(
                RESULT_BLOCK,
                "AUDITOR_ACCEPTANCE_BEFORE_BUILDER_END",
            )

    current_context = assignment["execution_context_identity"]
    current_assignee = assignment["assignee_identity"]
    role_requirement = required["role_context_independence"]

    if (
        role_requirement != "SAME_CONTEXT_ALLOWED"
        and evidence["role_context_independence"] != role_requirement
    ):
        return _assessment(
            RESULT_HOLD,
            "CONTEXT_INDEPENDENCE_NOT_ESTABLISHED",
        )
    if role_requirement in (
        "FRESH_CONTEXT_REQUIRED",
        "DISTINCT_CONTEXT_REQUIRED",
    ) and any(
        binding["execution_context_identity"] == current_context
        for binding in same_task
    ):
        return _assessment(
            RESULT_BLOCK,
            "CONTEXT_INDEPENDENCE_VIOLATION",
            *claim_mismatch_codes,
        )
    if assignment["role_id"] == ROLE_AUDITOR and any(
        binding["assignee_identity"] == current_assignee
        for binding in builder_bindings
    ):
        return _assessment(
            RESULT_BLOCK,
            "BUILDER_AUDITOR_ROLE_COLLISION",
            *claim_mismatch_codes,
        )
    if evidence_claim_mismatch:
        return _assessment(
            RESULT_BLOCK,
            "SUPPLIED_INDEPENDENCE_EVIDENCE_CLAIM_MISMATCH",
            *claim_mismatch_codes,
        )
    if binding_claim_mismatch:
        return _assessment(
            RESULT_BLOCK,
            "SUPPLIED_PRIOR_ROLE_BINDINGS_CLAIM_MISMATCH",
        )

    source_required = required["source_review_independence"]
    source_observed = evidence["source_review_independence"]
    source_satisfies = {
        "FULL_PRIOR_CONTEXT_ALLOWED": SOURCE_REVIEW_VALUES,
        "FIXED_ARTIFACTS_ONLY": frozenset(
            (
                "FIXED_ARTIFACTS_ONLY",
                "INDEPENDENT_EVIDENCE_SELECTION_REQUIRED",
            )
        ),
        "INDEPENDENT_EVIDENCE_SELECTION_REQUIRED": frozenset(
            ("INDEPENDENT_EVIDENCE_SELECTION_REQUIRED",)
        ),
    }
    if source_observed not in source_satisfies[source_required]:
        return _assessment(
            RESULT_HOLD,
            "SOURCE_REVIEW_INDEPENDENCE_NOT_ESTABLISHED",
        )

    runtime_required = required["runtime_execution_independence"]
    runtime_observed = evidence["runtime_execution_independence"]
    if runtime_required == "REQUIRED_NOT_ESTABLISHED":
        return _assessment(
            RESULT_HOLD,
            "RUNTIME_EXECUTION_INDEPENDENCE_NOT_ESTABLISHED",
        )
    if (
        runtime_required != "NOT_REQUIRED"
        and runtime_observed != runtime_required
    ):
        return _assessment(
            RESULT_HOLD,
            "RUNTIME_EXECUTION_INDEPENDENCE_NOT_ESTABLISHED",
        )

    model_required = required["model_diversity"]
    if model_required == "DIFFERENT_MODEL_REQUIRED":
        if not builder_bindings or any(
            binding["model_identity"] == evidence["model_identity"]
            for binding in builder_bindings
        ):
            return _assessment(
                RESULT_HOLD,
                "MODEL_DIVERSITY_NOT_ESTABLISHED",
            )
    return None


def _target_immutability_satisfied(
    contract: Mapping[str, Any],
    request: Mapping[str, Any],
) -> bool:
    evidence = request.get("target_immutability")
    packet = contract["task_artifact_packet"]
    return (
        isinstance(evidence, Mapping)
        and set(evidence) == TARGET_IMMUTABILITY_FIELDS
        and evidence.get("before_head") == packet["head"]
        and evidence.get("after_head") == packet["head"]
        and evidence.get("before_artifact_hashes")
        == packet["artifact_hashes"]
        and evidence.get("after_artifact_hashes")
        == packet["artifact_hashes"]
    )


def validate_role_operation(
    contract: Mapping[str, Any] | None,
    request: Mapping[str, Any] | None,
    *,
    supplied_role_grant: Mapping[str, Any] | None = None,
    supplied_role_acceptance: Mapping[str, Any] | None = None,
    supplied_independence_evidence: Mapping[str, Any] | None = None,
    supplied_prior_role_bindings: Mapping[str, Any] | None = None,
    now: datetime | None = None,
) -> RoleContractAssessment:
    """Validate one operation against unauthenticated supplied records."""

    shape_issue = _contract_shape_issue(contract)
    if shape_issue is not None:
        return _assessment(RESULT_INVALID, shape_issue)
    assert contract is not None
    semantic_issue = _contract_semantic_issue(contract)
    if semantic_issue is not None:
        result = (
            RESULT_BLOCK
            if semantic_issue
            in (
                "EXPLICIT_ROLE_GRANT_REQUIRED",
                "ASSIGNMENT_AUTHORITY_REQUIRED",
                "SHIN_GATE_REFERENCE_REQUIRED",
                "ROLE_ACCEPTANCE_REQUIRED",
                "COVERAGE_RECOMMENDATION_NOT_INERT",
            )
            else RESULT_INVALID
        )
        return _assessment(result, semantic_issue)

    current = now or datetime.now(timezone.utc)
    if not isinstance(current, datetime) or current.tzinfo is None:
        return _assessment(RESULT_INVALID, "CURRENT_TIME_UNVERIFIABLE")
    current = current.astimezone(timezone.utc)

    lifecycle = contract["lifecycle"]
    expires = _parse_timestamp(lifecycle["expires_at"])
    issued = _parse_timestamp(lifecycle["issued_at"])
    assert expires is not None and issued is not None
    if (
        lifecycle["status"] == "REVOKED"
        or lifecycle["revocation_reference"] is not None
    ):
        return _assessment(RESULT_BLOCK, "ROLE_GRANT_REVOKED")
    if lifecycle["status"] == "EXPIRED" or current >= expires:
        return _assessment(RESULT_BLOCK, "ROLE_GRANT_EXPIRED")
    if lifecycle["status"] != "ACTIVE" or current < issued:
        return _assessment(RESULT_HOLD, "ROLE_GRANT_NOT_ACTIVE")

    grant_assessment = _supplied_role_grant_assessment(
        contract,
        supplied_role_grant,
        current,
    )
    if grant_assessment is not None:
        return grant_assessment
    assert supplied_role_grant is not None

    request_issue = _request_shape_issue(request)
    if request_issue is not None:
        return _assessment(RESULT_INVALID, request_issue)
    assert request is not None

    assignment = contract["assignment"]
    if (
        request["task_id"] != assignment["task_id"]
        or request["role_id"] != assignment["role_id"]
        or request["assignee_identity"] != assignment["assignee_identity"]
        or request["execution_context_identity"]
        != assignment["execution_context_identity"]
    ):
        return _assessment(RESULT_BLOCK, "ASSIGNMENT_BINDING_MISMATCH")
    if request["task_artifact_packet"] != contract["task_artifact_packet"]:
        return _assessment(RESULT_BLOCK, "TASK_ARTIFACT_PACKET_MISMATCH")
    if request["specialist_lens"] != contract["specialist_lens"]:
        return _assessment(RESULT_BLOCK, "SPECIALIST_LENS_MISMATCH")

    operation = request["operation"]
    if (
        operation not in OPERATION_VALUES
        or operation not in contract["operations"]["allowed_operations"]
        or operation in contract["operations"]["forbidden_operations"]
    ):
        return _assessment(RESULT_BLOCK, "OPERATION_NOT_ALLOWED")
    if (
        assignment["role_id"] == ROLE_AUDITOR
        and not _target_immutability_satisfied(contract, request)
    ):
        return _assessment(
            RESULT_BLOCK,
            "TARGET_IMMUTABILITY_NOT_ESTABLISHED",
        )

    acceptance = _supplied_role_acceptance_assessment(
        contract,
        supplied_role_acceptance,
        supplied_role_grant,
        current,
    )
    if acceptance is not None:
        return acceptance
    assert supplied_role_acceptance is not None

    snapshot_assessment, supplied_binding_map = (
        _supplied_prior_role_bindings_assessment(
            contract,
            supplied_prior_role_bindings,
            current,
        )
    )
    if snapshot_assessment is not None:
        return snapshot_assessment
    assert supplied_prior_role_bindings is not None
    assert supplied_binding_map is not None

    if not _supplied_independence_evidence_shape_valid(
        supplied_independence_evidence
    ):
        return _assessment(
            RESULT_HOLD,
            "SUPPLIED_INDEPENDENCE_EVIDENCE_REQUIRED",
        )
    assert supplied_independence_evidence is not None

    supplied_records = (
        supplied_role_grant,
        supplied_role_acceptance,
        supplied_independence_evidence,
    )
    snapshot_identity = supplied_prior_role_bindings["snapshot_identity"]
    snapshot_as_of = _parse_timestamp(
        supplied_prior_role_bindings["as_of"]
    )
    assert snapshot_as_of is not None
    if any(
        record["snapshot_identity"] != snapshot_identity
        for record in supplied_records
    ):
        return _assessment(
            RESULT_BLOCK,
            "SUPPLIED_RECORD_SNAPSHOT_MISMATCH",
        )
    if any(
        _parse_timestamp(record["as_of"]) != snapshot_as_of
        for record in supplied_records
    ):
        return _assessment(RESULT_HOLD, "SUPPLIED_RECORDS_AS_OF_MISMATCH")

    record_identities = [
        supplied_role_grant["record_identity"],
        supplied_role_acceptance["record_identity"],
        supplied_independence_evidence["record_identity"],
        *supplied_binding_map,
    ]
    if len(record_identities) != len(set(record_identities)):
        return _assessment(
            RESULT_BLOCK,
            "SUPPLIED_RECORD_IDENTITY_REPLAY",
        )

    independence = _independence_assessment(
        contract,
        request,
        supplied_role_acceptance,
        supplied_independence_evidence,
        supplied_prior_role_bindings,
        supplied_binding_map,
        current,
    )
    if independence is not None:
        return independence

    if contract["completion"]["coverage_gap_required"]:
        recommendation = request.get("coverage_gap_recommendation")
        if not _valid_coverage_gap(recommendation):
            return _assessment(
                RESULT_BLOCK,
                "COVERAGE_RECOMMENDATION_NOT_INERT",
            )
        if recommendation != contract["coverage_gap_recommendation"]:
            return _assessment(
                RESULT_BLOCK,
                "COVERAGE_RECOMMENDATION_MISMATCH",
            )

    return _assessment(RESULT_ACTIVE)
