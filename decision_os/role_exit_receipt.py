"""Pure structural validation for one Stage 4 Role Exit Receipt.

The validator binds a specialist's returned evidence to one supplied Role
Contract.  It does not read a repository, authenticate the producer, prove
that commands ran or were sufficient, grant authority, or choose the
receiver's review outcome.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from .role_contract import (
    ROLE_AUDITOR,
    ROLE_BUILDER,
    SUPPORTED_ROLES,
    _contract_semantic_issue,
    _contract_shape_issue,
)


SCHEMA_VERSION = "decision-os.role-exit-receipt.v0.1"
RESULT_VALID = "VALID"
RESULT_INVALID = "INVALID"

V12_STATES = frozenset(("PASS", "DELAY", "BLOCK", "UNKNOWN"))
COMPLETION_STATE_BY_V12 = {
    "PASS": "COMPLETE",
    "DELAY": "INCOMPLETE",
    "BLOCK": "BLOCKED",
    "UNKNOWN": "UNKNOWN",
}
CHANGE_TYPES = frozenset(("ADDED", "MODIFIED", "DELETED"))
RUNTIME_EVIDENCE_TYPES = frozenset(
    ("INSTALLED_MODULE", "APP_BUILD", "SMOKE_RUN", "OTHER")
)

IMPLEMENTATION_BOUNDARY = {
    "end_to_end_false_division_prevention": "NOT ESTABLISHED",
    "record_issuer_authentication_transport": "NOT IMPLEMENTED",
    "role_independence": "NOT ESTABLISHED",
    "role_separation_enforcement": "VALIDATOR-LEVEL ONLY",
    "verification_scope_sufficiency": "NOT ESTABLISHED",
}
CLAIMS_NOT_MADE = (
    "command_execution_authenticity",
    "verification_scope_sufficiency",
    "artifact_bytes_or_repository_state_beyond_supplied_hashes",
    "record_issuer_authentication_or_transport",
    "role_independence",
    "authority_approval_or_receiver_disposition",
)

TOP_LEVEL_FIELDS = frozenset(
    (
        "schema_version",
        "receipt_id",
        "recorded_at",
        "contract_identity",
        "assignment_identity",
        "repository_state",
        "changed_artifacts",
        "verification_commands",
        "runtime_evidence",
        "completion",
        "coverage_gap_recommendation",
        "implementation_boundary",
        "required_next_actor",
        "claims_not_made",
    )
)
SECTION_FIELDS = {
    "contract_identity": frozenset(("contract_id", "contract_hash")),
    "assignment_identity": frozenset(
        (
            "task_id",
            "role_id",
            "assignee_identity",
            "execution_context_identity",
        )
    ),
    "repository_state": frozenset(("repo", "base_head", "final_head")),
    "completion": frozenset(
        (
            "v12_state",
            "completion_state",
            "completion_line",
            "routine_cleanup_state",
            "remaining_unverified",
            "unknowns",
        )
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
    "implementation_boundary": frozenset(IMPLEMENTATION_BOUNDARY),
}
CHANGED_ARTIFACT_FIELDS = frozenset(("path", "change_type", "sha256"))
VERIFICATION_COMMAND_FIELDS = frozenset(
    (
        "argv",
        "exit_code",
        "stdout_sha256",
        "stderr_sha256",
        "environment_sha256",
        "required",
    )
)
RUNTIME_EVIDENCE_FIELDS = frozenset(("evidence_type", "identity_sha256"))

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
NON_PLACEHOLDER_STRING_PATTERN = (
    r"^(?!\s*(?:UNKNOWN|UNVERIFIABLE|NONE)\s*$)(?=[\s\S]*\S)[\s\S]+$"
)
BOUNDED_GIT_PATH_PATTERN = (
    r"^(?!/)(?!.*//)(?!.*(?:^|/)\.{1,2}(?:/|$))(?!.*/$)[^\\\u0000]+$"
)
RFC3339_PATTERN = (
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
_RFC3339_RE = re.compile(RFC3339_PATTERN)
_UNKNOWN_VALUES = frozenset(("", "UNKNOWN", "UNVERIFIABLE", "NONE"))


@dataclass(frozen=True)
class RoleExitReceiptAssessment:
    """Deterministic structural eligibility result for independent review."""

    result: str
    issue_codes: tuple[str, ...]

    @property
    def decision_line(self) -> str:
        if self.result == RESULT_VALID:
            return "VALID — STRUCTURALLY ELIGIBLE FOR INDEPENDENT REVIEW"
        issue = self.issue_codes[0] if self.issue_codes else "UNSPECIFIED"
        return f"INVALID — {issue.replace('_', ' ')}"


def _assessment(result: str, issue: str | None = None) -> RoleExitReceiptAssessment:
    return RoleExitReceiptAssessment(result, () if issue is None else (issue,))


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() not in _UNKNOWN_VALUES


def _string_list(
    value: Any,
    *,
    allow_empty: bool,
    unique: bool = True,
) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes, bytearray))
        and (allow_empty or bool(value))
        and all(_nonempty_string(item) for item in value)
        and (not unique or len(value) == len(set(value)))
    )


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or _RFC3339_RE.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _bounded_git_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return False
    return not value.startswith("/") and all(
        part not in ("", ".", "..") for part in value.split("/")
    )


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _git_head(value: Any) -> bool:
    return isinstance(value, str) and _GIT_HEAD_RE.fullmatch(value) is not None


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def compute_receipt_id(receipt: Mapping[str, Any]) -> str:
    """Return canonical SHA-256 with ``receipt_id`` blanked."""

    canonical = deepcopy(dict(receipt))
    if "receipt_id" not in canonical:
        raise ValueError("receipt_id is required")
    canonical["receipt_id"] = ""
    return hashlib.sha256(_canonical_json(canonical)).hexdigest()


def receipt_with_id(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-compatible copy with its canonical identity populated."""

    value = deepcopy(dict(receipt))
    value["receipt_id"] = compute_receipt_id(value)
    return value


def _contract_context(
    contract: Any,
) -> tuple[dict[str, Any] | None, str | None]:
    shape_issue = _contract_shape_issue(contract)
    if shape_issue is not None:
        return None, shape_issue
    assert isinstance(contract, Mapping)
    try:
        semantic_issue = _contract_semantic_issue(contract)
    except (KeyError, TypeError, ValueError):
        return None, "INVALID_ROLE_CONTRACT"
    if semantic_issue is not None:
        return None, semantic_issue

    identity = contract["contract_identity"]
    assignment = contract["assignment"]
    ownership = contract["owned_responsibility"]
    packet = contract["task_artifact_packet"]
    completion = contract["completion"]
    lifecycle = contract["lifecycle"]
    if (
        lifecycle["status"] == "REVOKED"
        or lifecycle["revocation_reference"] is not None
    ):
        return None, "ROLE_GRANT_REVOKED"
    if lifecycle["status"] == "EXPIRED":
        return None, "ROLE_GRANT_EXPIRED"
    if lifecycle["status"] != "ACTIVE":
        return None, "ROLE_GRANT_NOT_ACTIVE"
    issued_at = _parse_timestamp(lifecycle["issued_at"])
    expires_at = _parse_timestamp(lifecycle["expires_at"])
    assert issued_at is not None and expires_at is not None
    if not all(_bounded_git_path(path) for path in ownership["exact_target"]):
        return None, "INVALID_TARGET_PATH"
    return {
        "contract_id": identity["contract_id"],
        "contract_hash": identity["contract_hash"],
        "task_id": assignment["task_id"],
        "role_id": assignment["role_id"],
        "assignee_identity": assignment["assignee_identity"],
        "execution_context_identity": assignment["execution_context_identity"],
        "repo": packet["repo"],
        "base_head": packet["head"],
        "exact_target": tuple(ownership["exact_target"]),
        "completion_line": completion["completion_line"],
        "next_owner": ownership["next_owner"],
        "issued_at": issued_at,
        "expires_at": expires_at,
    }, None


def _receipt_shape_valid(receipt: Any) -> bool:
    if not isinstance(receipt, Mapping) or set(receipt) != TOP_LEVEL_FIELDS:
        return False
    for section_name, fields in SECTION_FIELDS.items():
        section = receipt.get(section_name)
        if not isinstance(section, Mapping) or set(section) != fields:
            return False
    return all(
        isinstance(receipt.get(field), list)
        for field in (
            "changed_artifacts",
            "verification_commands",
            "runtime_evidence",
            "claims_not_made",
        )
    )


def _changed_artifacts_issue(
    value: list[Any], exact_target: tuple[str, ...]
) -> str | None:
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) != CHANGED_ARTIFACT_FIELDS:
            return "INVALID_CHANGED_ARTIFACTS"
        path = item.get("path")
        change_type = item.get("change_type")
        digest = item.get("sha256")
        if not _bounded_git_path(path) or path in seen:
            return "INVALID_CHANGED_ARTIFACTS"
        seen.add(path)
        if path not in exact_target:
            return "TARGET_SCOPE_EXCEEDED"
        if not isinstance(change_type, str) or change_type not in CHANGE_TYPES:
            return "INVALID_CHANGED_ARTIFACTS"
        if (change_type == "DELETED" and digest is not None) or (
            change_type != "DELETED" and not _sha256(digest)
        ):
            return "INVALID_CHANGED_ARTIFACTS"
    return None


def _verification_evidence_valid(
    commands: list[Any], runtime_evidence: list[Any]
) -> bool:
    for command in commands:
        if (
            not isinstance(command, Mapping)
            or set(command) != VERIFICATION_COMMAND_FIELDS
        ):
            return False
        exit_code = command.get("exit_code")
        if (
            not _string_list(
                command.get("argv"), allow_empty=False, unique=False
            )
            or not isinstance(exit_code, int)
            or isinstance(exit_code, bool)
            or not -255 <= exit_code <= 255
            or not all(
                _sha256(command.get(field))
                for field in (
                    "stdout_sha256",
                    "stderr_sha256",
                    "environment_sha256",
                )
            )
            or not isinstance(command.get("required"), bool)
        ):
            return False
    seen_runtime: set[tuple[str, str]] = set()
    for item in runtime_evidence:
        if not isinstance(item, Mapping) or set(item) != RUNTIME_EVIDENCE_FIELDS:
            return False
        identity = (item.get("evidence_type"), item.get("identity_sha256"))
        if (
            not isinstance(identity[0], str)
            or identity[0] not in RUNTIME_EVIDENCE_TYPES
            or not _sha256(identity[1])
            or identity in seen_runtime
        ):
            return False
        seen_runtime.add(identity)
    return True


def _completion_issue(
    completion: Mapping[str, Any],
    commands: list[Any],
    expected_line: str,
    role_id: str,
    changed_artifacts: list[Any],
) -> str | None:
    v12_state = completion.get("v12_state")
    if (
        not isinstance(v12_state, str)
        or v12_state not in V12_STATES
        or completion.get("completion_state")
        != COMPLETION_STATE_BY_V12.get(v12_state)
        or completion.get("completion_line") != expected_line
        or not isinstance(completion.get("routine_cleanup_state"), str)
        or completion.get("routine_cleanup_state")
        not in ("COMPLETE", "INCOMPLETE", "UNKNOWN")
        or not _string_list(
            completion.get("remaining_unverified"), allow_empty=True
        )
        or not _string_list(completion.get("unknowns"), allow_empty=True)
    ):
        return "INVALID_COMPLETION_STATE"
    if v12_state == "PASS" and (
        completion["routine_cleanup_state"] != "COMPLETE"
        or completion["remaining_unverified"]
        or completion["unknowns"]
        or not commands
        or not any(command["required"] for command in commands)
        or any(command["exit_code"] != 0 for command in commands)
        or (role_id == ROLE_BUILDER and not changed_artifacts)
    ):
        return "FALSE_PASS_EVIDENCE"
    return None


def _coverage_valid(
    coverage: Mapping[str, Any], exact_target: tuple[str, ...]
) -> bool:
    gap = coverage.get("coverage_gap")
    coverage_target = coverage.get("exact_target")
    if (
        not isinstance(coverage.get("coverage_completed"), bool)
        or not _nonempty_string(gap)
        or not isinstance(coverage.get("recommended_specialist"), str)
        or coverage.get("recommended_specialist")
        not in ("NONE", ROLE_BUILDER, ROLE_AUDITOR)
        or not _nonempty_string(coverage.get("reason"))
        or not _string_list(coverage_target, allow_empty=False)
        or tuple(coverage_target) != exact_target
        or not _string_list(coverage.get("required_evidence"), allow_empty=False)
        or not isinstance(coverage.get("urgency"), str)
        or coverage.get("urgency") not in ("LOW", "MEDIUM", "HIGH", "NONE")
        or coverage.get("assignment_authority_required") is not True
        or coverage.get("automatic_invocation") is not False
    ):
        return False
    if gap == "NONE DETECTED":
        return (
            coverage["coverage_completed"] is True
            and coverage["recommended_specialist"] == "NONE"
            and coverage["urgency"] == "NONE"
        )
    return (
        coverage["recommended_specialist"] in SUPPORTED_ROLES
        and coverage["urgency"] in ("LOW", "MEDIUM", "HIGH")
    )


def validate_role_exit_receipt(
    contract: Any, receipt: Any
) -> RoleExitReceiptAssessment:
    """Validate one supplied receipt without reading or mutating external state."""

    context, contract_issue = _contract_context(contract)
    if contract_issue is not None:
        return _assessment(RESULT_INVALID, contract_issue)
    assert context is not None
    if not _receipt_shape_valid(receipt):
        return _assessment(RESULT_INVALID, "INVALID_RECEIPT_STRUCTURE")
    if receipt["schema_version"] != SCHEMA_VERSION:
        return _assessment(RESULT_INVALID, "UNSUPPORTED_SCHEMA_VERSION")
    if not _sha256(receipt["receipt_id"]):
        return _assessment(RESULT_INVALID, "INVALID_RECEIPT_ID")
    try:
        expected_receipt_id = compute_receipt_id(receipt)
    except (TypeError, ValueError):
        return _assessment(RESULT_INVALID, "INVALID_RECEIPT_STRUCTURE")
    if receipt["receipt_id"] != expected_receipt_id:
        return _assessment(RESULT_INVALID, "RECEIPT_HASH_MISMATCH")
    recorded_at = _parse_timestamp(receipt["recorded_at"])
    if recorded_at is None:
        return _assessment(RESULT_INVALID, "INVALID_RECORDED_AT")
    if not context["issued_at"] <= recorded_at < context["expires_at"]:
        return _assessment(
            RESULT_INVALID, "RECEIPT_OUTSIDE_CONTRACT_LIFECYCLE"
        )

    if receipt["contract_identity"] != {
        "contract_id": context["contract_id"],
        "contract_hash": context["contract_hash"],
    }:
        return _assessment(RESULT_INVALID, "CONTRACT_BINDING_MISMATCH")
    if receipt["assignment_identity"] != {
        "task_id": context["task_id"],
        "role_id": context["role_id"],
        "assignee_identity": context["assignee_identity"],
        "execution_context_identity": context["execution_context_identity"],
    }:
        return _assessment(RESULT_INVALID, "ASSIGNMENT_BINDING_MISMATCH")

    repository = receipt["repository_state"]
    if (
        repository["repo"] != context["repo"]
        or repository["base_head"] != context["base_head"]
        or not _git_head(repository["final_head"])
    ):
        return _assessment(RESULT_INVALID, "REPOSITORY_BINDING_MISMATCH")
    changed_issue = _changed_artifacts_issue(
        receipt["changed_artifacts"], context["exact_target"]
    )
    if changed_issue is not None:
        return _assessment(RESULT_INVALID, changed_issue)
    if context["role_id"] == ROLE_AUDITOR and (
        receipt["changed_artifacts"]
        or repository["base_head"] != repository["final_head"]
    ):
        return _assessment(RESULT_INVALID, "AUDITOR_MUTATION_EVIDENCE")
    if context["role_id"] == ROLE_BUILDER and bool(
        receipt["changed_artifacts"]
    ) != (repository["base_head"] != repository["final_head"]):
        return _assessment(RESULT_INVALID, "HEAD_CHANGE_EVIDENCE_MISMATCH")

    commands = receipt["verification_commands"]
    if not _verification_evidence_valid(commands, receipt["runtime_evidence"]):
        return _assessment(RESULT_INVALID, "INVALID_VERIFICATION_EVIDENCE")
    completion_issue = _completion_issue(
        receipt["completion"],
        commands,
        context["completion_line"],
        context["role_id"],
        receipt["changed_artifacts"],
    )
    if completion_issue is not None:
        return _assessment(RESULT_INVALID, completion_issue)
    if not _coverage_valid(
        receipt["coverage_gap_recommendation"], context["exact_target"]
    ):
        return _assessment(RESULT_INVALID, "INVALID_COVERAGE_GAP")
    if receipt["implementation_boundary"] != IMPLEMENTATION_BOUNDARY:
        return _assessment(RESULT_INVALID, "IMPLEMENTATION_BOUNDARY_MISMATCH")
    if receipt["required_next_actor"] != context["next_owner"]:
        return _assessment(RESULT_INVALID, "NEXT_ACTOR_BINDING_MISMATCH")
    if tuple(receipt["claims_not_made"]) != CLAIMS_NOT_MADE:
        return _assessment(RESULT_INVALID, "CLAIM_BOUNDARY_MISMATCH")
    return _assessment(RESULT_VALID)
