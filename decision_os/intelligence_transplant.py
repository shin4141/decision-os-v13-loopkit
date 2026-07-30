"""Pure Stage 5 Intelligence Transplant validation and state reduction.

This module validates declared, self-hashed records and reduces their evidence
graph.  It performs no I/O, Git access, persistence, role assignment, model
invocation, or real-world identity authentication.  A structurally valid graph
can establish only the fixed manual-owner-attested governance boundary; it
never establishes cryptographic provenance or generalized transplant.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "decision-os.intelligence-transplant.v0.1"
RUN_TYPE = "intelligence_transplant"
AUTHORITY_MODE = "MANUAL_OWNER_ATTESTED"
DECISION_OWNER = "Shin"

STRUCTURAL_PASS = "PASS"
STRUCTURAL_FAIL = "FAIL"
AUTHORITY_PROVENANCE = "MANUAL OWNER ATTESTED"
CRYPTOGRAPHIC_PROVENANCE = "NOT ESTABLISHED"
GENERALIZED_TRANSPLANT = "NOT ESTABLISHED"

EXECUTION_NOT_ESTABLISHED = "NOT_ESTABLISHED"
EXECUTION_ACTIVE = "ACTIVE"
EXECUTION_CLOSED = "CLOSED"

DELTA_NONE = "NONE"
DELTA_CANDIDATE = "CANDIDATE"
DELTA_IMPLEMENTED = "IMPLEMENTED"
DELTA_REUSED = "REUSED"
DELTA_REJECTED = "REJECTED"
DELTA_REVOKED = "REVOKED"

GATE_GO = "GO"
GATE_HOLD = "HOLD"
GATE_CAP = "CAP"
GATE_BLOCK = "BLOCK"
GATES = frozenset((GATE_GO, GATE_HOLD, GATE_CAP, GATE_BLOCK))

RUN_CHARTER = "RUN_CHARTER"
SEAT_ASSIGNMENT_RECEIPT = "SEAT_ASSIGNMENT_RECEIPT"
AUDIT_INPUT_MANIFEST = "AUDIT_INPUT_MANIFEST"
E1_DISCOVERY = "E1_DISCOVERY"
E2_AUDIT = "E2_AUDIT"
AUDIT_COMPLETION_RECEIPT = "AUDIT_COMPLETION_RECEIPT"
E3_ACCEPTED_DISCOVERY = "E3_ACCEPTED_DISCOVERY"
E4_IMPLEMENTATION_BINDING = "E4_IMPLEMENTATION_BINDING"
LOWER_RUN_TRIAL_MANIFEST = "LOWER_RUN_TRIAL_MANIFEST"
LOWER_RUN_COMPLETION_RECEIPT = "LOWER_RUN_COMPLETION_RECEIPT"
E5_REUSE = "E5_REUSE"
MANUAL_CONTROL_RECEIPT = "MANUAL_CONTROL_RECEIPT"

OBJECT_TYPES = (
    RUN_CHARTER,
    SEAT_ASSIGNMENT_RECEIPT,
    AUDIT_INPUT_MANIFEST,
    E1_DISCOVERY,
    E2_AUDIT,
    AUDIT_COMPLETION_RECEIPT,
    E3_ACCEPTED_DISCOVERY,
    E4_IMPLEMENTATION_BINDING,
    LOWER_RUN_TRIAL_MANIFEST,
    LOWER_RUN_COMPLETION_RECEIPT,
    E5_REUSE,
    MANUAL_CONTROL_RECEIPT,
)

SEATS = frozenset(("DISCOVERY", "AUDIT", "IMPLEMENTATION", "LOWER_RUN"))
AUDIT_VERDICTS = frozenset(("SURVIVE", "REVISE", "REJECT"))
ASSET_TYPES = frozenset(("test", "guard", "rule", "schema", "validator"))
CAUSAL_PROOF_MODES = frozenset(("INTERCEPTION_TRACE", "CONTROLLED_CONTRAST"))
DETECTION_RESULTS = frozenset(("INTERCEPTED", "PREVENTED"))
HUMAN_RESCUE_VALUES = frozenset(("NONE", "PRESENT", "INTERRUPTED"))
CONTROL_ACTIONS = frozenset(("CAP", "CAP_RELEASE", "REVOKE", "ROLLBACK"))
DELTA_STATES = frozenset(
    (
        DELTA_NONE,
        DELTA_CANDIDATE,
        DELTA_IMPLEMENTED,
        DELTA_REUSED,
        DELTA_REJECTED,
        DELTA_REVOKED,
    )
)

REQUIRED_FORBIDDEN_INPUT_CLASSES = frozenset(
    (
        "UPPER_CONVERSATION",
        "UPPER_REASONING",
        "ACCEPTED_ANSWER",
        "SHIN_CORRECTION",
    )
)
ALLOWED_INPUT_CLASSES = frozenset(
    (
        "NEW_TASK",
        "REPOSITORY_STATE",
        "ACTIVE_ASSET",
        "MINIMUM_EXECUTION_BOUNDARY",
    )
)
BEHAVIORAL_VERIFICATION_MODES = frozenset(
    (
        "ADVERSARIAL_BEHAVIOR_TEST",
        "RUNTIME_INTERCEPTION_TRACE",
        "CONTROLLED_CONTRAST",
    )
)
ACTIVATION_EVIDENCE_MODES = frozenset(
    (
        "RUNTIME_TRACE",
        "ADVERSARIAL_TRIGGER_TRACE",
        "CONTROLLED_CONTRAST",
    )
)
LOWER_RUN_EVENT_SEQUENCE = (
    "RUN_STARTED",
    "ASSET_ACTIVATED",
    "FAILURE_OBSERVED",
    "EVALUATED",
)
CONTROLLED_CONTRAST_FIXED_VARIABLES = (
    "new_task_bytes",
    "repository_head",
    "runtime_context",
    "input_manifest",
)
CONTROLLED_CONTRAST_CHANGED_CONDITION = "ACTIVE_ASSET_ENABLED"
GENERALIZED_BOUNDARY = "GENERALIZED_TRANSPLANT_NOT_ESTABLISHED"
GENESIS_HASH = "0" * 64
MAX_JSON_BYTES = 4 * 1024 * 1024

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_GIT_BLOB_RE = re.compile(r"^[0-9a-f]{40}$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,200}$")
_FUTURE_SCHEMA_RE = re.compile(
    r"^(?:decision-os\.intelligence-transplant\.v[0-9]+(?:\.[0-9]+)*"
    r"|v13-intelligence-transplant-v[0-9]+(?:\.[0-9]+)*)$"
)
_UNKNOWN_VALUES = frozenset(("", "UNKNOWN", "UNVERIFIABLE", "NOT ESTABLISHED"))

BASE_FIELDS = frozenset(
    (
        "schema_version",
        "object_type",
        "object_id",
        "run_id",
        "as_of",
        "supersedes",
        "content_hash",
    )
)

OBJECT_FIELDS: dict[str, frozenset[str]] = {
    RUN_CHARTER: BASE_FIELDS
    | frozenset(
        (
            "charter_id",
            "charter_hash",
            "run_type",
            "authority_mode",
            "decision_owner",
            "decision_owner_attestation",
            "source_freeze_id",
            "source_freeze_sha256",
            "source_task_id",
            "source_task_hash",
            "completion_line",
            "repository_head",
            "failure_family_id",
            "failure_predicate",
            "charter_gate",
            "not_allowed_next",
        )
    ),
    SEAT_ASSIGNMENT_RECEIPT: BASE_FIELDS
    | frozenset(
        (
            "receipt_id",
            "receipt_hash",
            "charter_ref",
            "seat",
            "assignee_context_identity",
            "assignment_scope",
            "allowed_inputs",
            "not_allowed_inputs",
            "effective_as_of",
            "authority_mode",
            "decision_owner",
            "decision_owner_attestation",
            "cryptographic_identity",
        )
    ),
    AUDIT_INPUT_MANIFEST: BASE_FIELDS
    | frozenset(
        (
            "manifest_id",
            "manifest_hash",
            "charter_ref",
            "target_e1_ref",
            "audit_assignment_ref",
            "input_refs",
            "forbidden_input_classes",
            "frozen_as_of",
            "authority_mode",
            "decision_owner",
            "decision_owner_attestation",
        )
    ),
    E1_DISCOVERY: BASE_FIELDS
    | frozenset(
        (
            "e1_id",
            "charter_ref",
            "discovery_assignment_ref",
            "discovery_context_identity",
            "failure_family_id",
            "failure_predicate",
            "discovery_claim",
            "observed_failure",
            "mechanism",
            "strongest_falsifier",
            "evidence_anchors",
            "decision_owner_attestation",
        )
    ),
    E2_AUDIT: BASE_FIELDS
    | frozenset(
        (
            "e2_id",
            "charter_ref",
            "target_e1_ref",
            "audit_manifest_ref",
            "audit_assignment_ref",
            "auditor_context_identity",
            "verdict",
            "strongest_counterexample",
            "required_deltas",
            "decision_owner_attestation",
        )
    ),
    AUDIT_COMPLETION_RECEIPT: BASE_FIELDS
    | frozenset(
        (
            "receipt_id",
            "receipt_hash",
            "charter_ref",
            "target_e1_ref",
            "e2_ref",
            "audit_manifest_ref",
            "audit_assignment_ref",
            "verdict",
            "completed_as_of",
            "authority_mode",
            "decision_owner",
            "decision_owner_attestation",
            "cryptographic_identity",
        )
    ),
    E3_ACCEPTED_DISCOVERY: BASE_FIELDS
    | frozenset(
        (
            "e3_id",
            "charter_ref",
            "e1_ref",
            "e2_ref",
            "audit_completion_receipt_ref",
            "accepted_claims",
            "revision_applied",
            "excluded_claims",
            "implementation_requirements",
            "implementation_scope",
            "forbidden_overclaims",
            "claim_boundary",
            "decision_owner_attestation",
        )
    ),
    E4_IMPLEMENTATION_BINDING: BASE_FIELDS
    | frozenset(
        (
            "e4_id",
            "charter_ref",
            "e3_ref",
            "implementation_assignment_ref",
            "repository_base",
            "repository_head",
            "repository_opening_head",
            "repository_closing_head",
            "repository_base_is_ancestor",
            "changed_artifacts",
            "claim_bindings",
            "focused_suite_status",
            "regression_status",
            "regression_reason",
            "rollback_path",
            "decision_owner_attestation",
        )
    ),
    LOWER_RUN_TRIAL_MANIFEST: BASE_FIELDS
    | frozenset(
        (
            "manifest_id",
            "manifest_hash",
            "charter_ref",
            "e4_ref",
            "lower_run_assignment_ref",
            "trial_id",
            "new_task_id",
            "new_task_hash",
            "source_task_id",
            "source_task_hash",
            "failure_family_id",
            "failure_predicate",
            "allowed_input_manifest",
            "allowed_input_manifest_hash",
            "forbidden_input_classes",
            "input_separation_attestation",
            "active_asset_identity",
            "active_asset_version",
            "active_asset_hash",
            "repository_head",
            "lower_runtime_context_identity",
            "minimum_execution_boundary",
            "effective_as_of",
            "authority_mode",
            "decision_owner",
            "decision_owner_attestation",
        )
    ),
    LOWER_RUN_COMPLETION_RECEIPT: BASE_FIELDS
    | frozenset(
        (
            "receipt_id",
            "receipt_hash",
            "charter_ref",
            "trial_manifest_ref",
            "e4_ref",
            "trial_id",
            "actual_input_manifest_hash",
            "active_asset_identity",
            "active_asset_version",
            "active_asset_hash",
            "asset_activation_trace",
            "causal_proof_mode",
            "controlled_contrast",
            "detection_or_prevention_result",
            "human_rescue",
            "no_rescue_attestation",
            "event_sequence",
            "lower_runtime_context_identity",
            "evaluator_context_identity",
            "evaluator_receipt",
            "started_as_of",
            "asset_activated_as_of",
            "failure_observed_as_of",
            "completed_as_of",
            "authority_mode",
            "decision_owner",
            "decision_owner_attestation",
            "cryptographic_identity",
        )
    ),
    E5_REUSE: BASE_FIELDS
    | frozenset(
        (
            "e5_id",
            "charter_ref",
            "e4_ref",
            "trial_manifest_ref",
            "completion_receipt_ref",
            "source_task_id",
            "new_task_id",
            "failure_family_id",
            "failure_predicate",
            "causal_proof_mode",
            "detection_or_prevention_result",
            "decision_owner_attestation",
        )
    ),
    MANUAL_CONTROL_RECEIPT: BASE_FIELDS
    | frozenset(
        (
            "receipt_id",
            "receipt_hash",
            "charter_ref",
            "control_action",
            "target_object_id",
            "target_content_hash",
            "reason",
            "effective_as_of",
            "authority_mode",
            "decision_owner",
            "decision_owner_attestation",
            "cryptographic_identity",
            "capped_from",
            "cap_axis",
            "cap_limit",
            "cap_release_condition",
            "cap_expires_as_of",
            "release_evidence_refs",
            "post_rollback_repository_head",
            "rollback_changed_artifacts",
        )
    ),
}

SPECIAL_ID_FIELDS = {
    RUN_CHARTER: "charter_id",
    SEAT_ASSIGNMENT_RECEIPT: "receipt_id",
    AUDIT_INPUT_MANIFEST: "manifest_id",
    E1_DISCOVERY: "e1_id",
    E2_AUDIT: "e2_id",
    AUDIT_COMPLETION_RECEIPT: "receipt_id",
    E3_ACCEPTED_DISCOVERY: "e3_id",
    E4_IMPLEMENTATION_BINDING: "e4_id",
    LOWER_RUN_TRIAL_MANIFEST: "manifest_id",
    LOWER_RUN_COMPLETION_RECEIPT: "receipt_id",
    E5_REUSE: "e5_id",
    MANUAL_CONTROL_RECEIPT: "receipt_id",
}
SPECIAL_HASH_FIELDS = {
    RUN_CHARTER: "charter_hash",
    SEAT_ASSIGNMENT_RECEIPT: "receipt_hash",
    AUDIT_INPUT_MANIFEST: "manifest_hash",
    AUDIT_COMPLETION_RECEIPT: "receipt_hash",
    LOWER_RUN_TRIAL_MANIFEST: "manifest_hash",
    LOWER_RUN_COMPLETION_RECEIPT: "receipt_hash",
    MANUAL_CONTROL_RECEIPT: "receipt_hash",
}

REF_FIELD_TYPES: dict[str, dict[str, str | None]] = {
    SEAT_ASSIGNMENT_RECEIPT: {"charter_ref": RUN_CHARTER},
    AUDIT_INPUT_MANIFEST: {
        "charter_ref": RUN_CHARTER,
        "target_e1_ref": E1_DISCOVERY,
        "audit_assignment_ref": SEAT_ASSIGNMENT_RECEIPT,
    },
    E1_DISCOVERY: {
        "charter_ref": RUN_CHARTER,
        "discovery_assignment_ref": SEAT_ASSIGNMENT_RECEIPT,
    },
    E2_AUDIT: {
        "charter_ref": RUN_CHARTER,
        "target_e1_ref": E1_DISCOVERY,
        "audit_manifest_ref": AUDIT_INPUT_MANIFEST,
        "audit_assignment_ref": SEAT_ASSIGNMENT_RECEIPT,
    },
    AUDIT_COMPLETION_RECEIPT: {
        "charter_ref": RUN_CHARTER,
        "target_e1_ref": E1_DISCOVERY,
        "e2_ref": E2_AUDIT,
        "audit_manifest_ref": AUDIT_INPUT_MANIFEST,
        "audit_assignment_ref": SEAT_ASSIGNMENT_RECEIPT,
    },
    E3_ACCEPTED_DISCOVERY: {
        "charter_ref": RUN_CHARTER,
        "e1_ref": E1_DISCOVERY,
        "e2_ref": E2_AUDIT,
        "audit_completion_receipt_ref": AUDIT_COMPLETION_RECEIPT,
    },
    E4_IMPLEMENTATION_BINDING: {
        "charter_ref": RUN_CHARTER,
        "e3_ref": E3_ACCEPTED_DISCOVERY,
        "implementation_assignment_ref": SEAT_ASSIGNMENT_RECEIPT,
    },
    LOWER_RUN_TRIAL_MANIFEST: {
        "charter_ref": RUN_CHARTER,
        "e4_ref": E4_IMPLEMENTATION_BINDING,
        "lower_run_assignment_ref": SEAT_ASSIGNMENT_RECEIPT,
    },
    LOWER_RUN_COMPLETION_RECEIPT: {
        "charter_ref": RUN_CHARTER,
        "trial_manifest_ref": LOWER_RUN_TRIAL_MANIFEST,
        "e4_ref": E4_IMPLEMENTATION_BINDING,
    },
    E5_REUSE: {
        "charter_ref": RUN_CHARTER,
        "e4_ref": E4_IMPLEMENTATION_BINDING,
        "trial_manifest_ref": LOWER_RUN_TRIAL_MANIFEST,
        "completion_receipt_ref": LOWER_RUN_COMPLETION_RECEIPT,
    },
    MANUAL_CONTROL_RECEIPT: {
        "charter_ref": RUN_CHARTER,
        "target_ref": None,
    },
}

ISSUE_CODES = (
    "OBJECT_REQUIRED",
    "UNSUPPORTED_OBJECT_TYPE",
    "UNSUPPORTED_SCHEMA_VERSION",
    "INVALID_OBJECT_STRUCTURE",
    "INVALID_OBJECT_IDENTITY",
    "INVALID_RUN_IDENTITY",
    "INVALID_AS_OF",
    "INVALID_SUPERSEDES_REFERENCE",
    "INVALID_CONTENT_HASH",
    "CONTENT_HASH_MISMATCH",
    "SPECIALIZED_ID_MISMATCH",
    "SPECIALIZED_HASH_MISMATCH",
    "DECISION_OWNER_ATTESTATION_REQUIRED",
    "MANUAL_AUTHORITY_REQUIRED",
    "CRYPTOGRAPHIC_IDENTITY_OVERCLAIM",
    "INVALID_CHARTER",
    "INVALID_SEAT_ASSIGNMENT",
    "INVALID_AUDIT_MANIFEST",
    "INVALID_E1",
    "INVALID_E2",
    "INVALID_AUDIT_COMPLETION_RECEIPT",
    "INVALID_E3",
    "INVALID_E4",
    "INVALID_LOWER_RUN_MANIFEST",
    "INVALID_LOWER_RUN_COMPLETION_RECEIPT",
    "INVALID_E5",
    "INVALID_CONTROL_RECEIPT",
    "GRAPH_REQUIRED",
    "CHARTER_REQUIRED",
    "MULTIPLE_CHARTERS",
    "CROSS_RUN_SUBSTITUTION",
    "OBJECT_ID_REUSE",
    "REFERENCE_NOT_FOUND",
    "REFERENCE_HASH_MISMATCH",
    "REFERENCE_TYPE_MISMATCH",
    "DEPENDENCY_TIME_ORDER_INVALID",
    "DEPENDENCY_SEQUENCE_ORDER_INVALID",
    "GRAPH_CYCLE",
    "INVALID_SUPERSESSION",
    "SUPERSESSION_BRANCH",
    "FORWARD_REPLACEMENT_REQUIRED",
    "STALE_DEPENDENCY_REFERENCE",
    "CHARTER_BINDING_MISMATCH",
    "SEAT_BINDING_MISMATCH",
    "SAME_SEAT_SELF_AUDIT",
    "CONTEXT_INDEPENDENCE_VIOLATION",
    "IMMUTABLE_TARGET_MISMATCH",
    "AUDIT_MANIFEST_NOT_PREFROZEN",
    "AUDIT_COMPLETION_MISSING",
    "AUDIT_VERDICT_MISMATCH",
    "REJECTED_LINEAGE_CANNOT_PROGRESS",
    "REVISION_BINDING_INCOMPLETE",
    "ACCEPTED_CLAIM_MISMATCH",
    "GENERALIZED_TRANSPLANT_OVERCLAIM",
    "IMPLEMENTATION_AUTHORITY_MISSING",
    "REPOSITORY_BINDING_INVALID",
    "CLAIM_BINDING_INCOMPLETE",
    "BEHAVIORAL_ACTIVATION_MISSING",
    "LOWER_RUN_AUTHORITY_MISSING",
    "SAME_TASK_REUSE",
    "FAILURE_FAMILY_MISMATCH",
    "FAILURE_PREDICATE_MISMATCH",
    "LOWER_RUN_MANIFEST_NOT_PREFROZEN",
    "LOWER_RUN_INPUT_LEAKAGE",
    "ASSET_BINDING_MISMATCH",
    "ASSET_NOT_ACTIVATED",
    "CAUSAL_TRACE_MISMATCH",
    "UNCONTROLLED_CONTRAST",
    "HUMAN_RESCUE_PRESENT",
    "NO_RESCUE_SEQUENCE_MISMATCH",
    "CAP_RELEASE_AUTHORITY_MISSING",
    "CAP_MATURITY_MISMATCH",
    "CAP_TARGET_NOT_CURRENT",
    "REVOKE_AUTHORITY_MISSING",
    "ROLLBACK_TARGET_MISMATCH",
    "ROLLBACK_FORWARD_REPLACEMENT_REQUIRED",
    "E5_CHAIN_SPLICE",
    "CONTROL_CANNOT_RESCUE_INVALID_GRAPH",
)


class IntelligenceTransplantError(ValueError):
    """One Stage 5 record or graph failed its pure validation contract."""


@dataclass(frozen=True)
class ValidationAssessment:
    """Deterministic structural result with fixed provenance boundaries."""

    structural_validation: str
    issue_codes: tuple[str, ...]
    authority_provenance: str = AUTHORITY_PROVENANCE
    cryptographic_provenance: str = CRYPTOGRAPHIC_PROVENANCE

    @property
    def valid(self) -> bool:
        return self.structural_validation == STRUCTURAL_PASS

    @property
    def result(self) -> str:
        return self.structural_validation

    def as_dict(self) -> dict[str, Any]:
        return {
            "structural_validation": self.structural_validation,
            "issue_codes": list(self.issue_codes),
            "authority_provenance": self.authority_provenance,
            "cryptographic_provenance": self.cryptographic_provenance,
        }


@dataclass(frozen=True)
class IntelligenceTransplantProjection:
    """One read-only Stage 5 projection reduced from the supplied graph."""

    run_id: str
    execution_status: str
    delta_state: str
    current_gate: str
    missing_evidence: tuple[str, ...]
    next_one_action: str
    not_allowed_next: tuple[str, ...]
    evidence_objects: tuple[dict[str, str], ...]
    active_cap: dict[str, Any] | None
    structural_validation: str
    issue_codes: tuple[str, ...]
    authority_provenance: str = AUTHORITY_PROVENANCE
    cryptographic_provenance: str = CRYPTOGRAPHIC_PROVENANCE
    generalized_transplant: str = GENERALIZED_TRANSPLANT
    run_type: str = RUN_TYPE

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_type": self.run_type,
            "execution_status": self.execution_status,
            "delta_state": self.delta_state,
            "current_gate": self.current_gate,
            "missing_evidence": list(self.missing_evidence),
            "next_one_action": self.next_one_action,
            "not_allowed_next": list(self.not_allowed_next),
            "evidence_objects": [dict(item) for item in self.evidence_objects],
            "active_cap": deepcopy(self.active_cap),
            "structural_validation": self.structural_validation,
            "issue_codes": list(self.issue_codes),
            "authority_provenance": self.authority_provenance,
            "cryptographic_provenance": self.cryptographic_provenance,
            "generalized_transplant": self.generalized_transplant,
        }


TransplantProjection = IntelligenceTransplantProjection


def canonical_json(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes suitable for identity hashing."""

    try:
        rendered = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return rendered.encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise IntelligenceTransplantError(
            "Stage 5 structured data is not canonical JSON."
        ) from exc


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IntelligenceTransplantError("Duplicate JSON object key.")
        result[key] = value
    return result


def _reject_json_constant(_: str) -> None:
    raise IntelligenceTransplantError("Non-finite JSON value.")


def strict_json_object(raw: str | bytes) -> dict[str, Any]:
    """Parse exactly one UTF-8 JSON object while rejecting duplicate keys."""

    if isinstance(raw, bytes):
        if len(raw) > MAX_JSON_BYTES:
            raise IntelligenceTransplantError("Stage 5 JSON exceeds the size limit.")
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise IntelligenceTransplantError("Stage 5 JSON is not UTF-8.") from exc
    elif isinstance(raw, str):
        try:
            encoded = raw.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise IntelligenceTransplantError("Stage 5 JSON is not UTF-8.") from exc
        if len(encoded) > MAX_JSON_BYTES:
            raise IntelligenceTransplantError("Stage 5 JSON exceeds the size limit.")
        text = raw
    else:
        raise IntelligenceTransplantError("Stage 5 JSON text is required.")

    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except IntelligenceTransplantError:
        raise
    except (json.JSONDecodeError, RecursionError, UnicodeError, ValueError) as exc:
        raise IntelligenceTransplantError("Stage 5 JSON is malformed.") from exc
    if not isinstance(value, dict):
        raise IntelligenceTransplantError("Stage 5 JSON object is required.")
    return value


def compute_content_hash(record: Mapping[str, Any]) -> str:
    """Hash a record with all of its self-hash fields blanked."""

    if not isinstance(record, Mapping):
        raise IntelligenceTransplantError("Stage 5 record object is required.")
    canonical = deepcopy(dict(record))
    if "content_hash" not in canonical:
        raise IntelligenceTransplantError("content_hash is required.")
    canonical["content_hash"] = ""
    object_type = canonical.get("object_type")
    specialized = SPECIAL_HASH_FIELDS.get(object_type)
    if specialized is not None:
        if specialized not in canonical:
            raise IntelligenceTransplantError(f"{specialized} is required.")
        canonical[specialized] = ""
    return hashlib.sha256(canonical_json(canonical)).hexdigest()


def object_with_content_hash(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deep JSON-compatible copy with matching self-hash fields."""

    value = deepcopy(dict(record))
    digest = compute_content_hash(value)
    value["content_hash"] = digest
    specialized = SPECIAL_HASH_FIELDS.get(value.get("object_type"))
    if specialized is not None:
        value[specialized] = digest
    return value


def exact_ref(record: Mapping[str, Any]) -> dict[str, str]:
    """Return the exact object-id/content-hash reference for one record."""

    if not isinstance(record, Mapping):
        raise IntelligenceTransplantError("Stage 5 record object is required.")
    object_id = record.get("object_id")
    content_hash = record.get("content_hash")
    if (
        not isinstance(object_id, str)
        or _SAFE_ID_RE.fullmatch(object_id) is None
        or not isinstance(content_hash, str)
        or _SHA256_RE.fullmatch(content_hash) is None
    ):
        raise IntelligenceTransplantError("Stage 5 exact reference is unavailable.")
    return {"object_id": object_id, "content_hash": content_hash}


def _ordered_issues(issues: Iterable[str]) -> tuple[str, ...]:
    selected = set(issues)
    ordered = [code for code in ISSUE_CODES if code in selected]
    ordered.extend(sorted(selected - set(ISSUE_CODES)))
    return tuple(ordered)


def _assessment(issues: Iterable[str] = ()) -> ValidationAssessment:
    ordered = _ordered_issues(issues)
    return ValidationAssessment(
        STRUCTURAL_FAIL if ordered else STRUCTURAL_PASS,
        ordered,
    )


def _is_nonempty_string(value: Any) -> bool:
    return (
        isinstance(value, str)
        and value.strip() not in _UNKNOWN_VALUES
        and "\x00" not in value
    )


def _is_string_list(
    value: Any,
    *,
    allow_empty: bool = False,
    unique: bool = True,
) -> bool:
    if not isinstance(value, list) or (not allow_empty and not value):
        return False
    if not all(_is_nonempty_string(item) for item in value):
        return False
    return not unique or len(value) == len(set(value))


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


def _same_time(left: Any, right: Any) -> bool:
    left_time = _parse_timestamp(left)
    right_time = _parse_timestamp(right)
    return left_time is not None and left_time == right_time


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _is_commit(value: Any) -> bool:
    return isinstance(value, str) and _GIT_COMMIT_RE.fullmatch(value) is not None


def _is_ref(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == {"object_id", "content_hash"}
        and isinstance(value.get("object_id"), str)
        and _SAFE_ID_RE.fullmatch(value["object_id"]) is not None
        and _is_sha256(value.get("content_hash"))
    )


def _declared_ref(record: Mapping[str, Any], field: str) -> Any:
    if (
        record.get("object_type") == MANUAL_CONTROL_RECEIPT
        and field == "target_ref"
    ):
        return {
            "object_id": record.get("target_object_id"),
            "content_hash": record.get("target_content_hash"),
        }
    return record.get(field)


def _is_ref_list(value: Any, *, allow_empty: bool = False) -> bool:
    if not isinstance(value, list) or (not allow_empty and not value):
        return False
    if not all(_is_ref(item) for item in value):
        return False
    identities = [
        (item["object_id"], item["content_hash"])
        for item in value
        if isinstance(item, Mapping)
    ]
    return len(identities) == len(set(identities))


def _is_owner_attestation(value: Any) -> bool:
    return _is_nonempty_string(value)


def _authority_fields_valid(record: Mapping[str, Any]) -> bool:
    return (
        record.get("authority_mode") == AUTHORITY_MODE
        and record.get("decision_owner") == DECISION_OWNER
        and _is_owner_attestation(record.get("decision_owner_attestation"))
    )


def _cryptographic_boundary_valid(record: Mapping[str, Any]) -> bool:
    return record.get("cryptographic_identity") == "NOT_ESTABLISHED"


def _artifact_valid(value: Any) -> bool:
    required = {
        "path",
        "git_blob",
        "sha256",
        "asset_identity",
        "asset_version",
        "asset_type",
    }
    return (
        isinstance(value, Mapping)
        and set(value) == required
        and all(
            _is_nonempty_string(value.get(field))
            for field in ("path", "asset_identity", "asset_version")
        )
        and isinstance(value.get("git_blob"), str)
        and _GIT_BLOB_RE.fullmatch(value["git_blob"]) is not None
        and _is_sha256(value.get("sha256"))
        and value.get("asset_type") in ASSET_TYPES
    )


def _behavioral_verification_valid(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == {"mode", "evidence_ref", "observed_behavior"}
        and value.get("mode") in BEHAVIORAL_VERIFICATION_MODES
        and _is_nonempty_string(value.get("evidence_ref"))
        and _is_nonempty_string(value.get("observed_behavior"))
    )


def _activation_evidence_valid(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == {"mode", "trace_ref", "activation_point"}
        and value.get("mode") in ACTIVATION_EVIDENCE_MODES
        and _is_nonempty_string(value.get("trace_ref"))
        and _is_nonempty_string(value.get("activation_point"))
    )


def _claim_binding_valid(value: Any) -> bool:
    required = {
        "accepted_claim",
        "required_control_behavior",
        "asset_identity",
        "asset_version",
        "asset_hash",
        "behavioral_verification",
        "activation_evidence",
    }
    return (
        isinstance(value, Mapping)
        and set(value) == required
        and all(
            _is_nonempty_string(value.get(field))
            for field in (
                "accepted_claim",
                "required_control_behavior",
                "asset_identity",
                "asset_version",
            )
        )
        and _is_sha256(value.get("asset_hash"))
        and _behavioral_verification_valid(value.get("behavioral_verification"))
        and _activation_evidence_valid(value.get("activation_evidence"))
    )


def _revision_valid(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == {"required_delta", "revision_applied"}
        and _is_nonempty_string(value.get("required_delta"))
        and _is_nonempty_string(value.get("revision_applied"))
    )


def _activation_trace_valid(value: Any) -> bool:
    required = {
        "asset_identity",
        "asset_version",
        "asset_hash",
        "e4_ref",
        "failure_predicate",
        "interception_point",
    }
    return (
        isinstance(value, Mapping)
        and set(value) == required
        and all(
            _is_nonempty_string(value.get(field))
            for field in (
                "asset_identity",
                "asset_version",
                "failure_predicate",
            )
        )
        and _is_sha256(value.get("asset_hash"))
        and _is_ref(value.get("e4_ref"))
        and isinstance(value.get("interception_point"), Mapping)
        and set(value["interception_point"])
        == {"mode", "event_ref", "observed_effect"}
        and value["interception_point"].get("mode")
        in (
            "PRE_ACTION_CONTROL_INTERCEPTION",
            "FAILURE_PREDICATE_PREVENTION",
        )
        and _is_nonempty_string(
            value["interception_point"].get("event_ref")
        )
        and value["interception_point"].get("observed_effect")
        in DETECTION_RESULTS
    )


def _contrast_valid(value: Any) -> bool:
    required = {
        "fixed_variables",
        "only_changed_condition",
        "off_result",
        "on_result",
    }
    return (
        isinstance(value, Mapping)
        and set(value) == required
        and value.get("fixed_variables")
        == list(CONTROLLED_CONTRAST_FIXED_VARIABLES)
        and value.get("only_changed_condition")
        == CONTROLLED_CONTRAST_CHANGED_CONDITION
        and value.get("off_result") == "FAILURE_OBSERVED"
        and value.get("on_result") in DETECTION_RESULTS
    )


def _allowed_input_manifest_valid(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != len(ALLOWED_INPUT_CLASSES):
        return False
    classes: list[str] = []
    for item in value:
        if not isinstance(item, Mapping):
            return False
        input_class = item.get("input_class")
        classes.append(input_class)
        if input_class == "NEW_TASK":
            if not (
                set(item) == {"input_class", "task_id", "sha256"}
                and _is_nonempty_string(item.get("task_id"))
                and _is_sha256(item.get("sha256"))
            ):
                return False
        elif input_class == "REPOSITORY_STATE":
            if not (
                set(item) == {"input_class", "repository_head"}
                and _is_commit(item.get("repository_head"))
            ):
                return False
        elif input_class == "ACTIVE_ASSET":
            if not (
                set(item)
                == {
                    "input_class",
                    "asset_identity",
                    "asset_version",
                    "asset_hash",
                }
                and _is_nonempty_string(item.get("asset_identity"))
                and _is_nonempty_string(item.get("asset_version"))
                and _is_sha256(item.get("asset_hash"))
            ):
                return False
        elif input_class == "MINIMUM_EXECUTION_BOUNDARY":
            if not (
                set(item) == {"input_class", "boundary"}
                and _is_nonempty_string(item.get("boundary"))
            ):
                return False
        else:
            return False
    return len(classes) == len(set(classes)) and set(classes) == ALLOWED_INPUT_CLASSES


def _rollback_artifact_valid(value: Any) -> bool:
    if not (
        isinstance(value, Mapping)
        and set(value)
        == {"path", "post_rollback_state", "git_blob", "sha256"}
        and _is_nonempty_string(value.get("path"))
        and value.get("post_rollback_state") in ("PRESENT", "DELETED")
    ):
        return False
    if value["post_rollback_state"] == "PRESENT":
        return (
            isinstance(value.get("git_blob"), str)
            and _GIT_BLOB_RE.fullmatch(value["git_blob"]) is not None
            and _is_sha256(value.get("sha256"))
        )
    return value.get("git_blob") is None and value.get("sha256") is None


def _future_version_issues(record: Mapping[str, Any]) -> set[str]:
    """Validate only the immutable envelope of an unknown Stage 5 version."""

    issues = {"UNSUPPORTED_SCHEMA_VERSION"}
    if not BASE_FIELDS.issubset(record):
        issues.add("INVALID_OBJECT_STRUCTURE")
        return issues
    object_type = record.get("object_type")
    if not _is_nonempty_string(object_type):
        issues.add("UNSUPPORTED_OBJECT_TYPE")
    object_id = record.get("object_id")
    if not isinstance(object_id, str) or _SAFE_ID_RE.fullmatch(object_id) is None:
        issues.add("INVALID_OBJECT_IDENTITY")
    run_id = record.get("run_id")
    if not isinstance(run_id, str) or _SAFE_ID_RE.fullmatch(run_id) is None:
        issues.add("INVALID_RUN_IDENTITY")
    if _parse_timestamp(record.get("as_of")) is None:
        issues.add("INVALID_AS_OF")
    supersedes = record.get("supersedes")
    if supersedes is not None and not _is_ref(supersedes):
        issues.add("INVALID_SUPERSEDES_REFERENCE")
    content_hash = record.get("content_hash")
    if not _is_sha256(content_hash):
        issues.add("INVALID_CONTENT_HASH")
    else:
        try:
            expected_hash = compute_content_hash(record)
        except IntelligenceTransplantError:
            issues.add("INVALID_CONTENT_HASH")
        else:
            if content_hash != expected_hash:
                issues.add("CONTENT_HASH_MISMATCH")
    special_id = SPECIAL_ID_FIELDS.get(str(object_type))
    if special_id is not None:
        if record.get(special_id) != object_id:
            issues.add("SPECIALIZED_ID_MISMATCH")
        special_hash = SPECIAL_HASH_FIELDS.get(str(object_type))
        if (
            special_hash is not None
            and record.get(special_hash) != content_hash
        ):
            issues.add("SPECIALIZED_HASH_MISMATCH")
    return issues


def _local_object_issues(record: Any) -> set[str]:
    issues: set[str] = set()
    if not isinstance(record, Mapping):
        return {"OBJECT_REQUIRED"}
    schema_version = record.get("schema_version")
    if (
        isinstance(schema_version, str)
        and _FUTURE_SCHEMA_RE.fullmatch(schema_version) is not None
        and schema_version != SCHEMA_VERSION
    ):
        return _future_version_issues(record)
    object_type = record.get("object_type")
    if object_type not in OBJECT_FIELDS:
        return {"UNSUPPORTED_OBJECT_TYPE"}
    if record.get("schema_version") != SCHEMA_VERSION:
        issues.add("UNSUPPORTED_SCHEMA_VERSION")
        issues.add("INVALID_OBJECT_STRUCTURE")
    if set(record) != OBJECT_FIELDS[object_type]:
        issues.add("INVALID_OBJECT_STRUCTURE")
        if not _is_owner_attestation(record.get("decision_owner_attestation")):
            issues.add("DECISION_OWNER_ATTESTATION_REQUIRED")
        return issues

    object_id = record.get("object_id")
    if (
        not isinstance(object_id, str)
        or _SAFE_ID_RE.fullmatch(object_id) is None
    ):
        issues.add("INVALID_OBJECT_IDENTITY")
    run_id = record.get("run_id")
    if not isinstance(run_id, str) or _SAFE_ID_RE.fullmatch(run_id) is None:
        issues.add("INVALID_RUN_IDENTITY")
    if _parse_timestamp(record.get("as_of")) is None:
        issues.add("INVALID_AS_OF")
    supersedes = record.get("supersedes")
    if supersedes is not None and not _is_ref(supersedes):
        issues.add("INVALID_SUPERSEDES_REFERENCE")

    content_hash = record.get("content_hash")
    if not _is_sha256(content_hash):
        issues.add("INVALID_CONTENT_HASH")
    else:
        try:
            expected_hash = compute_content_hash(record)
        except IntelligenceTransplantError:
            issues.add("INVALID_CONTENT_HASH")
        else:
            if content_hash != expected_hash:
                issues.add("CONTENT_HASH_MISMATCH")

    special_id = SPECIAL_ID_FIELDS[object_type]
    if record.get(special_id) != object_id:
        issues.add("SPECIALIZED_ID_MISMATCH")
    special_hash = SPECIAL_HASH_FIELDS.get(object_type)
    if special_hash is not None and record.get(special_hash) != content_hash:
        issues.add("SPECIALIZED_HASH_MISMATCH")
    if not _is_owner_attestation(record.get("decision_owner_attestation")):
        issues.add("DECISION_OWNER_ATTESTATION_REQUIRED")

    if object_type == RUN_CHARTER:
        if not (
            record.get("run_type") == RUN_TYPE
            and record.get("authority_mode") == AUTHORITY_MODE
            and record.get("decision_owner") == DECISION_OWNER
            and _is_nonempty_string(record.get("source_freeze_id"))
            and _is_sha256(record.get("source_freeze_sha256"))
            and _is_nonempty_string(record.get("source_task_id"))
            and _is_sha256(record.get("source_task_hash"))
            and _is_nonempty_string(record.get("completion_line"))
            and _is_commit(record.get("repository_head"))
            and _is_nonempty_string(record.get("failure_family_id"))
            and _is_nonempty_string(record.get("failure_predicate"))
            and record.get("charter_gate") in GATES
            and _is_string_list(record.get("not_allowed_next"), allow_empty=True)
            and record.get("supersedes") is None
        ):
            issues.add("INVALID_CHARTER")
        if not _authority_fields_valid(record):
            issues.add("MANUAL_AUTHORITY_REQUIRED")

    elif object_type == SEAT_ASSIGNMENT_RECEIPT:
        if not (
            _is_ref(record.get("charter_ref"))
            and record.get("seat") in SEATS
            and _is_nonempty_string(record.get("assignee_context_identity"))
            and _is_nonempty_string(record.get("assignment_scope"))
            and _is_string_list(record.get("allowed_inputs"))
            and _is_string_list(record.get("not_allowed_inputs"))
            and _same_time(record.get("effective_as_of"), record.get("as_of"))
        ):
            issues.add("INVALID_SEAT_ASSIGNMENT")
        if not _authority_fields_valid(record):
            issues.add("MANUAL_AUTHORITY_REQUIRED")
        if not _cryptographic_boundary_valid(record):
            issues.add("CRYPTOGRAPHIC_IDENTITY_OVERCLAIM")

    elif object_type == AUDIT_INPUT_MANIFEST:
        if not (
            _is_ref(record.get("charter_ref"))
            and _is_ref(record.get("target_e1_ref"))
            and _is_ref(record.get("audit_assignment_ref"))
            and _is_ref_list(record.get("input_refs"))
            and _is_string_list(record.get("forbidden_input_classes"))
            and _same_time(record.get("frozen_as_of"), record.get("as_of"))
        ):
            issues.add("INVALID_AUDIT_MANIFEST")
        if not _authority_fields_valid(record):
            issues.add("MANUAL_AUTHORITY_REQUIRED")

    elif object_type == E1_DISCOVERY:
        if not (
            _is_ref(record.get("charter_ref"))
            and _is_ref(record.get("discovery_assignment_ref"))
            and all(
                _is_nonempty_string(record.get(field))
                for field in (
                    "discovery_context_identity",
                    "failure_family_id",
                    "failure_predicate",
                    "discovery_claim",
                    "observed_failure",
                    "mechanism",
                    "strongest_falsifier",
                )
            )
            and _is_string_list(record.get("evidence_anchors"))
        ):
            issues.add("INVALID_E1")

    elif object_type == E2_AUDIT:
        if not (
            _is_ref(record.get("charter_ref"))
            and _is_ref(record.get("target_e1_ref"))
            and _is_ref(record.get("audit_manifest_ref"))
            and _is_ref(record.get("audit_assignment_ref"))
            and _is_nonempty_string(record.get("auditor_context_identity"))
            and record.get("verdict") in AUDIT_VERDICTS
            and _is_nonempty_string(record.get("strongest_counterexample"))
            and _is_string_list(record.get("required_deltas"), allow_empty=True)
            and (
                (record.get("verdict") == "REVISE" and bool(record["required_deltas"]))
                or (
                    record.get("verdict") in ("SURVIVE", "REJECT")
                    and not record["required_deltas"]
                )
            )
        ):
            issues.add("INVALID_E2")

    elif object_type == AUDIT_COMPLETION_RECEIPT:
        if not (
            all(
                _is_ref(record.get(field))
                for field in (
                    "charter_ref",
                    "target_e1_ref",
                    "e2_ref",
                    "audit_manifest_ref",
                    "audit_assignment_ref",
                )
            )
            and record.get("verdict") in AUDIT_VERDICTS
            and _same_time(record.get("completed_as_of"), record.get("as_of"))
        ):
            issues.add("INVALID_AUDIT_COMPLETION_RECEIPT")
        if not _authority_fields_valid(record):
            issues.add("MANUAL_AUTHORITY_REQUIRED")
        if not _cryptographic_boundary_valid(record):
            issues.add("CRYPTOGRAPHIC_IDENTITY_OVERCLAIM")

    elif object_type == E3_ACCEPTED_DISCOVERY:
        revisions = record.get("revision_applied")
        if not (
            all(
                _is_ref(record.get(field))
                for field in (
                    "charter_ref",
                    "e1_ref",
                    "e2_ref",
                    "audit_completion_receipt_ref",
                )
            )
            and _is_string_list(record.get("accepted_claims"))
            and isinstance(revisions, list)
            and all(_revision_valid(item) for item in revisions)
            and _is_string_list(record.get("excluded_claims"), allow_empty=True)
            and _is_string_list(record.get("implementation_requirements"))
            and _is_string_list(record.get("implementation_scope"))
            and _is_string_list(record.get("forbidden_overclaims"))
            and record.get("claim_boundary") == GENERALIZED_BOUNDARY
            and GENERALIZED_BOUNDARY in record.get("forbidden_overclaims", ())
        ):
            issues.add("INVALID_E3")
        if record.get("claim_boundary") != GENERALIZED_BOUNDARY:
            issues.add("GENERALIZED_TRANSPLANT_OVERCLAIM")

    elif object_type == E4_IMPLEMENTATION_BINDING:
        artifacts = record.get("changed_artifacts")
        bindings = record.get("claim_bindings")
        if not (
            _is_ref(record.get("charter_ref"))
            and _is_ref(record.get("e3_ref"))
            and _is_ref(record.get("implementation_assignment_ref"))
            and _is_commit(record.get("repository_base"))
            and _is_commit(record.get("repository_head"))
            and _is_commit(record.get("repository_opening_head"))
            and _is_commit(record.get("repository_closing_head"))
            and isinstance(record.get("repository_base_is_ancestor"), bool)
            and isinstance(artifacts, list)
            and bool(artifacts)
            and all(_artifact_valid(item) for item in artifacts)
            and isinstance(bindings, list)
            and bool(bindings)
            and all(_claim_binding_valid(item) for item in bindings)
            and record.get("focused_suite_status") == "PASS"
            and record.get("regression_status") in ("PASS", "NA")
            and (
                (record.get("regression_status") == "PASS"
                 and record.get("regression_reason") is None)
                or (
                    record.get("regression_status") == "NA"
                    and _is_nonempty_string(record.get("regression_reason"))
                )
            )
            and _is_nonempty_string(record.get("rollback_path"))
        ):
            issues.add("INVALID_E4")
        if not isinstance(bindings, list) or not bindings:
            issues.add("CLAIM_BINDING_INCOMPLETE")
        elif any(
            not isinstance(item, Mapping)
            or not _behavioral_verification_valid(
                item.get("behavioral_verification")
            )
            or not _activation_evidence_valid(item.get("activation_evidence"))
            for item in bindings
        ):
            issues.add("BEHAVIORAL_ACTIVATION_MISSING")

    elif object_type == LOWER_RUN_TRIAL_MANIFEST:
        if not (
            all(
                _is_ref(record.get(field))
                for field in ("charter_ref", "e4_ref", "lower_run_assignment_ref")
            )
            and all(
                _is_nonempty_string(record.get(field))
                for field in (
                    "trial_id",
                    "new_task_id",
                    "source_task_id",
                    "failure_family_id",
                    "failure_predicate",
                    "active_asset_identity",
                    "active_asset_version",
                    "lower_runtime_context_identity",
                    "minimum_execution_boundary",
                )
            )
            and _is_sha256(record.get("new_task_hash"))
            and _is_sha256(record.get("source_task_hash"))
            and _allowed_input_manifest_valid(record.get("allowed_input_manifest"))
            and _is_sha256(record.get("allowed_input_manifest_hash"))
            and _is_string_list(record.get("forbidden_input_classes"))
            and record.get("input_separation_attestation")
            == "UPPER_INPUT_EXCLUDED"
            and _is_sha256(record.get("active_asset_hash"))
            and _is_commit(record.get("repository_head"))
            and _same_time(record.get("effective_as_of"), record.get("as_of"))
        ):
            issues.add("INVALID_LOWER_RUN_MANIFEST")
        if not _allowed_input_manifest_valid(
            record.get("allowed_input_manifest")
        ):
            issues.add("LOWER_RUN_INPUT_LEAKAGE")
        if not _authority_fields_valid(record):
            issues.add("MANUAL_AUTHORITY_REQUIRED")

    elif object_type == LOWER_RUN_COMPLETION_RECEIPT:
        sequence = record.get("event_sequence")
        timestamps = tuple(
            _parse_timestamp(record.get(field))
            for field in (
                "started_as_of",
                "asset_activated_as_of",
                "failure_observed_as_of",
                "completed_as_of",
            )
        )
        if not (
            all(
                _is_ref(record.get(field))
                for field in ("charter_ref", "trial_manifest_ref", "e4_ref")
            )
            and _is_nonempty_string(record.get("trial_id"))
            and _is_sha256(record.get("actual_input_manifest_hash"))
            and _is_nonempty_string(record.get("active_asset_identity"))
            and _is_nonempty_string(record.get("active_asset_version"))
            and _is_sha256(record.get("active_asset_hash"))
            and _activation_trace_valid(record.get("asset_activation_trace"))
            and record.get("causal_proof_mode") in CAUSAL_PROOF_MODES
            and record.get("detection_or_prevention_result") in DETECTION_RESULTS
            and record.get("human_rescue") in HUMAN_RESCUE_VALUES
            and _is_nonempty_string(record.get("no_rescue_attestation"))
            and sequence == list(LOWER_RUN_EVENT_SEQUENCE)
            and _is_nonempty_string(record.get("lower_runtime_context_identity"))
            and _is_nonempty_string(record.get("evaluator_context_identity"))
            and _is_nonempty_string(record.get("evaluator_receipt"))
            and all(timestamp is not None for timestamp in timestamps)
            and _same_time(record.get("completed_as_of"), record.get("as_of"))
        ):
            issues.add("INVALID_LOWER_RUN_COMPLETION_RECEIPT")
        if not _activation_trace_valid(record.get("asset_activation_trace")):
            issues.add("CAUSAL_TRACE_MISMATCH")
        if sequence != list(LOWER_RUN_EVENT_SEQUENCE):
            issues.add("NO_RESCUE_SEQUENCE_MISMATCH")
        if not _authority_fields_valid(record):
            issues.add("MANUAL_AUTHORITY_REQUIRED")
        if not _cryptographic_boundary_valid(record):
            issues.add("CRYPTOGRAPHIC_IDENTITY_OVERCLAIM")

    elif object_type == E5_REUSE:
        if not (
            all(
                _is_ref(record.get(field))
                for field in (
                    "charter_ref",
                    "e4_ref",
                    "trial_manifest_ref",
                    "completion_receipt_ref",
                )
            )
            and all(
                _is_nonempty_string(record.get(field))
                for field in (
                    "source_task_id",
                    "new_task_id",
                    "failure_family_id",
                    "failure_predicate",
                )
            )
            and record.get("causal_proof_mode") in CAUSAL_PROOF_MODES
            and record.get("detection_or_prevention_result") in DETECTION_RESULTS
        ):
            issues.add("INVALID_E5")

    elif object_type == MANUAL_CONTROL_RECEIPT:
        if not (
            _is_ref(record.get("charter_ref"))
            and isinstance(record.get("target_object_id"), str)
            and _SAFE_ID_RE.fullmatch(record["target_object_id"]) is not None
            and _is_sha256(record.get("target_content_hash"))
            and record.get("control_action") in CONTROL_ACTIONS
            and _is_nonempty_string(record.get("reason"))
            and _same_time(record.get("effective_as_of"), record.get("as_of"))
            and record.get("capped_from") in DELTA_STATES | {None}
            and (
                record.get("cap_expires_as_of") is None
                or _parse_timestamp(record.get("cap_expires_as_of")) is not None
            )
            and _is_ref_list(
                record.get("release_evidence_refs"),
                allow_empty=True,
            )
            and (
                record.get("post_rollback_repository_head") is None
                or _is_commit(record.get("post_rollback_repository_head"))
            )
            and isinstance(record.get("rollback_changed_artifacts"), list)
            and all(
                _rollback_artifact_valid(item)
                for item in record["rollback_changed_artifacts"]
            )
        ):
            issues.add("INVALID_CONTROL_RECEIPT")
        if not _authority_fields_valid(record):
            issues.add("MANUAL_AUTHORITY_REQUIRED")
        if not _cryptographic_boundary_valid(record):
            issues.add("CRYPTOGRAPHIC_IDENTITY_OVERCLAIM")
        action = record.get("control_action")
        if action == "CAP" and not (
            record.get("capped_from") in DELTA_STATES
            and _is_nonempty_string(record.get("cap_axis"))
            and _is_nonempty_string(record.get("cap_limit"))
            and _is_nonempty_string(record.get("cap_release_condition"))
            and not record.get("release_evidence_refs")
            and record.get("post_rollback_repository_head") is None
            and not record.get("rollback_changed_artifacts")
        ):
            issues.add("INVALID_CONTROL_RECEIPT")
        elif action == "CAP_RELEASE" and not (
            record.get("capped_from") is None
            and record.get("cap_axis") is None
            and record.get("cap_limit") is None
            and _is_nonempty_string(record.get("cap_release_condition"))
            and bool(record.get("release_evidence_refs"))
            and record.get("cap_expires_as_of") is None
            and record.get("post_rollback_repository_head") is None
            and not record.get("rollback_changed_artifacts")
        ):
            issues.add("CAP_RELEASE_AUTHORITY_MISSING")
        elif action == "REVOKE" and not (
            record.get("capped_from") is None
            and record.get("cap_axis") is None
            and record.get("cap_limit") is None
            and record.get("cap_release_condition") is None
            and record.get("cap_expires_as_of") is None
            and not record.get("release_evidence_refs")
            and record.get("post_rollback_repository_head") is None
            and not record.get("rollback_changed_artifacts")
        ):
            issues.add("REVOKE_AUTHORITY_MISSING")
        elif action == "ROLLBACK" and not (
            record.get("capped_from") is None
            and record.get("cap_axis") is None
            and record.get("cap_limit") is None
            and record.get("cap_release_condition") is None
            and record.get("cap_expires_as_of") is None
            and not record.get("release_evidence_refs")
            and _is_commit(record.get("post_rollback_repository_head"))
            and bool(record.get("rollback_changed_artifacts"))
        ):
            issues.add("ROLLBACK_TARGET_MISMATCH")
    return issues


def validate_object(
    record: Mapping[str, Any] | None,
    *,
    objects: Sequence[Mapping[str, Any]] = (),
    now: datetime | str | None = None,
) -> ValidationAssessment:
    """Validate one record, optionally inside its complete dependency graph."""

    local = _local_object_issues(record)
    if local or not objects:
        return _assessment(local)
    assert record is not None
    combined = list(objects)
    if not any(item is record for item in combined):
        combined.append(record)
    return validate_graph(combined, now=now)


def _all_refs(record: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    refs: list[Mapping[str, Any]] = []
    if _is_ref(record.get("supersedes")):
        refs.append(record["supersedes"])
    for field in REF_FIELD_TYPES.get(record.get("object_type"), {}):
        value = _declared_ref(record, field)
        if _is_ref(value):
            refs.append(value)
    for field in ("input_refs", "release_evidence_refs"):
        value = record.get(field)
        if isinstance(value, list):
            refs.extend(item for item in value if _is_ref(item))
    trace = record.get("asset_activation_trace")
    if isinstance(trace, Mapping) and _is_ref(trace.get("e4_ref")):
        refs.append(trace["e4_ref"])
    return tuple(refs)


def _resolve_ref(
    owner: Mapping[str, Any],
    field: str,
    expected_type: str | None,
    registry: Mapping[str, Mapping[str, Any]],
    issues: set[str],
) -> Mapping[str, Any] | None:
    reference = _declared_ref(owner, field)
    if not _is_ref(reference):
        return None
    target = registry.get(reference["object_id"])
    if target is None:
        issues.add("REFERENCE_NOT_FOUND")
        return None
    if target.get("content_hash") != reference["content_hash"]:
        issues.add("REFERENCE_HASH_MISMATCH")
    if expected_type is not None and target.get("object_type") != expected_type:
        issues.add("REFERENCE_TYPE_MISMATCH")
    if target.get("run_id") != owner.get("run_id"):
        issues.add("CROSS_RUN_SUBSTITUTION")
    target_time = _parse_timestamp(target.get("as_of"))
    owner_time = _parse_timestamp(owner.get("as_of"))
    if target_time is not None and owner_time is not None and target_time > owner_time:
        issues.add("DEPENDENCY_TIME_ORDER_INVALID")
    return target


def _reference_matches(record: Mapping[str, Any], field: str, target: Mapping[str, Any]) -> bool:
    return record.get(field) == exact_ref(target)


def _valid_now(now: datetime | str | None) -> datetime | None:
    if now is None:
        return None
    if isinstance(now, str):
        return _parse_timestamp(now)
    if isinstance(now, datetime) and now.tzinfo is not None:
        return now.astimezone(timezone.utc)
    return None


def _current_e4_at(
    objects: Sequence[Mapping[str, Any]],
    before_position: int,
) -> Mapping[str, Any] | None:
    """Return the current E4 on the active lineage at one control instant."""

    prefix = objects[:before_position]
    records = _current_records(prefix)
    chain = _select_chain(records)
    e4 = chain["e4"]
    if e4 is None:
        return None
    registry = _record_registry(records)
    closure = _dependency_closure(_chain_records(chain), registry)
    if _chain_revocation(prefix, closure) is not None:
        return None
    return e4


def validate_graph(
    objects: Sequence[Mapping[str, Any]],
    *,
    now: datetime | str | None = None,
) -> ValidationAssessment:
    """Validate one complete Stage 5 record graph without reading external state."""

    if (
        not isinstance(objects, Sequence)
        or isinstance(objects, (str, bytes, bytearray))
        or not objects
    ):
        return _assessment(("GRAPH_REQUIRED",))
    issues: set[str] = set()
    if now is not None and _valid_now(now) is None:
        issues.add("INVALID_AS_OF")
    current_time = _valid_now(now)

    for record in objects:
        issues.update(_local_object_issues(record))
        record_time = (
            _parse_timestamp(record.get("as_of"))
            if isinstance(record, Mapping)
            else None
        )
        if (
            current_time is not None
            and record_time is not None
            and record_time > current_time
        ):
            issues.add("INVALID_AS_OF")
    if any(not isinstance(record, Mapping) for record in objects):
        return _assessment(issues)
    if issues:
        return _assessment(issues)

    registry: dict[str, Mapping[str, Any]] = {}
    position_by_id: dict[str, int] = {}
    duplicate_ids: set[str] = set()
    for position, record in enumerate(objects):
        object_id = record.get("object_id")
        if not isinstance(object_id, str):
            continue
        if object_id in registry:
            duplicate_ids.add(object_id)
        else:
            registry[object_id] = record
            position_by_id[object_id] = position
    if duplicate_ids:
        issues.add("OBJECT_ID_REUSE")

    charters = [record for record in objects if record.get("object_type") == RUN_CHARTER]
    if not charters:
        issues.add("CHARTER_REQUIRED")
        return _assessment(issues)
    if len(charters) != 1:
        issues.add("MULTIPLE_CHARTERS")
        return _assessment(issues)
    charter = charters[0]
    run_id = charter.get("run_id")
    if any(record.get("run_id") != run_id for record in objects):
        issues.add("CROSS_RUN_SUBSTITUTION")

    resolved: dict[tuple[str, str], Mapping[str, Any] | None] = {}
    for record_position, record in enumerate(objects):
        object_id = str(record.get("object_id", ""))
        for field, expected_type in REF_FIELD_TYPES.get(
            record.get("object_type"), {}
        ).items():
            resolved[(object_id, field)] = _resolve_ref(
                record, field, expected_type, registry, issues
            )
        supersedes = record.get("supersedes")
        if _is_ref(supersedes):
            target = registry.get(supersedes["object_id"])
            if target is None:
                issues.add("REFERENCE_NOT_FOUND")
            else:
                if target.get("content_hash") != supersedes["content_hash"]:
                    issues.add("REFERENCE_HASH_MISMATCH")
                if (
                    target.get("object_type") != record.get("object_type")
                    or target.get("run_id") != record.get("run_id")
                    or target.get("object_id") == record.get("object_id")
                ):
                    issues.add("INVALID_SUPERSESSION")
                target_time = _parse_timestamp(target.get("as_of"))
                record_time = _parse_timestamp(record.get("as_of"))
                if (
                    target_time is not None
                    and record_time is not None
                    and target_time > record_time
                ):
                    issues.add("INVALID_SUPERSESSION")
        for field in ("input_refs", "release_evidence_refs"):
            values = record.get(field)
            if not isinstance(values, list):
                continue
            for reference in values:
                if not _is_ref(reference):
                    continue
                target = registry.get(reference["object_id"])
                if target is None:
                    issues.add("REFERENCE_NOT_FOUND")
                elif target.get("content_hash") != reference["content_hash"]:
                    issues.add("REFERENCE_HASH_MISMATCH")
                elif target.get("run_id") != record.get("run_id"):
                    issues.add("CROSS_RUN_SUBSTITUTION")
                else:
                    target_time = _parse_timestamp(target.get("as_of"))
                    record_time = _parse_timestamp(record.get("as_of"))
                    if (
                        target_time is not None
                        and record_time is not None
                        and target_time > record_time
                    ):
                        issues.add("DEPENDENCY_TIME_ORDER_INVALID")
        for reference in _all_refs(record):
            target_position = position_by_id.get(reference["object_id"])
            if target_position is not None and target_position >= record_position:
                issues.add("DEPENDENCY_SEQUENCE_ORDER_INVALID")

    successors: dict[str, list[Mapping[str, Any]]] = {}
    for record in objects:
        supersedes = record.get("supersedes")
        if _is_ref(supersedes):
            successors.setdefault(supersedes["object_id"], []).append(record)
    if any(len(values) > 1 for values in successors.values()):
        issues.add("SUPERSESSION_BRANCH")

    lineage_fields = {
        E2_AUDIT: ("target_e1_ref",),
        AUDIT_COMPLETION_RECEIPT: ("e2_ref",),
        E3_ACCEPTED_DISCOVERY: (
            "e1_ref",
            "e2_ref",
            "audit_completion_receipt_ref",
        ),
        E4_IMPLEMENTATION_BINDING: ("e3_ref",),
    }
    for object_type, fields in lineage_fields.items():
        current_by_lineage: dict[bytes, Mapping[str, Any]] = {}
        for record in objects:
            if record.get("object_type") != object_type:
                continue
            lineage = canonical_json(
                [_declared_ref(record, field) for field in fields]
            )
            predecessor = current_by_lineage.get(lineage)
            if (
                predecessor is not None
                and record.get("supersedes") != exact_ref(predecessor)
            ):
                issues.add("FORWARD_REPLACEMENT_REQUIRED")
            current_by_lineage[lineage] = record

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(object_id: str) -> None:
        if object_id in visiting:
            issues.add("GRAPH_CYCLE")
            return
        if object_id in visited:
            return
        visiting.add(object_id)
        record = registry.get(object_id)
        if record is not None:
            for reference in _all_refs(record):
                visit(reference["object_id"])
        visiting.remove(object_id)
        visited.add(object_id)

    for object_id in registry:
        visit(object_id)

    for record in objects:
        if record.get("object_type") != RUN_CHARTER:
            bound_charter = resolved.get((str(record.get("object_id")), "charter_ref"))
            if bound_charter is not None and bound_charter is not charter:
                issues.add("CHARTER_BINDING_MISMATCH")

    # A dependency that had already been superseded before a later object was
    # created is a stale replay. Historical downstream objects created before
    # replacement remain admissible history but are no longer effective.
    successor_positions: dict[str, int] = {}
    for target_id, values in successors.items():
        if values:
            successor_positions[target_id] = min(
                position_by_id[str(value.get("object_id"))] for value in values
            )
    for record_position, record in enumerate(objects):
        for reference in _all_refs(record):
            if reference == record.get("supersedes"):
                continue
            replaced_at = successor_positions.get(reference["object_id"])
            if replaced_at is not None and replaced_at <= record_position:
                issues.add("STALE_DEPENDENCY_REFERENCE")

    revoked_positions: dict[str, int] = {}
    for record_position, record in enumerate(objects):
        if (
            record.get("object_type") == MANUAL_CONTROL_RECEIPT
            and record.get("control_action") in ("REVOKE", "ROLLBACK")
        ):
            target_id = record.get("target_object_id")
            if isinstance(target_id, str):
                current_value = revoked_positions.get(target_id)
                if current_value is None or record_position < current_value:
                    revoked_positions[target_id] = record_position
    for record_position, record in enumerate(objects):
        if record.get("object_type") == MANUAL_CONTROL_RECEIPT:
            continue
        for reference in _all_refs(record):
            if reference == record.get("supersedes"):
                continue
            revoked_at = revoked_positions.get(reference["object_id"])
            if revoked_at is not None and revoked_at <= record_position:
                issues.add("STALE_DEPENDENCY_REFERENCE")

    def dep(record: Mapping[str, Any], field: str) -> Mapping[str, Any] | None:
        return resolved.get((str(record.get("object_id")), field))

    for record_position, record in enumerate(objects):
        object_type = record.get("object_type")
        if object_type == E1_DISCOVERY:
            assignment = dep(record, "discovery_assignment_ref")
            if assignment is not None and (
                assignment.get("seat") != "DISCOVERY"
                or assignment.get("assignee_context_identity")
                != record.get("discovery_context_identity")
            ):
                issues.add("SEAT_BINDING_MISMATCH")
            if (
                record.get("failure_family_id") != charter.get("failure_family_id")
            ):
                issues.add("FAILURE_FAMILY_MISMATCH")
            if record.get("failure_predicate") != charter.get("failure_predicate"):
                issues.add("FAILURE_PREDICATE_MISMATCH")

        elif object_type == AUDIT_INPUT_MANIFEST:
            e1 = dep(record, "target_e1_ref")
            assignment = dep(record, "audit_assignment_ref")
            if assignment is not None and assignment.get("seat") != "AUDIT":
                issues.add("SEAT_BINDING_MISMATCH")
            if e1 is not None and record.get("input_refs") != [exact_ref(e1)]:
                issues.add("IMMUTABLE_TARGET_MISMATCH")
            e1_time = _parse_timestamp(e1.get("as_of")) if e1 is not None else None
            manifest_time = _parse_timestamp(record.get("as_of"))
            if (
                e1_time is not None
                and manifest_time is not None
                and manifest_time < e1_time
            ):
                issues.add("AUDIT_MANIFEST_NOT_PREFROZEN")

        elif object_type == E2_AUDIT:
            e1 = dep(record, "target_e1_ref")
            manifest = dep(record, "audit_manifest_ref")
            assignment = dep(record, "audit_assignment_ref")
            discovery_assignment = (
                dep(e1, "discovery_assignment_ref") if e1 is not None else None
            )
            if manifest is not None and e1 is not None and (
                not _reference_matches(manifest, "target_e1_ref", e1)
                or not _reference_matches(record, "target_e1_ref", e1)
            ):
                issues.add("IMMUTABLE_TARGET_MISMATCH")
            if (
                manifest is not None
                and assignment is not None
                and not _reference_matches(
                    manifest, "audit_assignment_ref", assignment
                )
            ):
                issues.add("IMMUTABLE_TARGET_MISMATCH")
            if assignment is not None and (
                assignment.get("seat") != "AUDIT"
                or assignment.get("assignee_context_identity")
                != record.get("auditor_context_identity")
            ):
                issues.add("SEAT_BINDING_MISMATCH")
            if (
                assignment is not None
                and discovery_assignment is not None
                and assignment.get("object_id")
                == discovery_assignment.get("object_id")
            ):
                issues.add("SAME_SEAT_SELF_AUDIT")
            if (
                e1 is not None
                and record.get("auditor_context_identity")
                == e1.get("discovery_context_identity")
            ):
                issues.add("CONTEXT_INDEPENDENCE_VIOLATION")
            if manifest is not None:
                manifest_time = _parse_timestamp(manifest.get("as_of"))
                audit_time = _parse_timestamp(record.get("as_of"))
                if (
                    manifest_time is not None
                    and audit_time is not None
                    and manifest_time >= audit_time
                ):
                    issues.add("AUDIT_MANIFEST_NOT_PREFROZEN")
        elif object_type == AUDIT_COMPLETION_RECEIPT:
            e1 = dep(record, "target_e1_ref")
            e2 = dep(record, "e2_ref")
            manifest = dep(record, "audit_manifest_ref")
            assignment = dep(record, "audit_assignment_ref")
            if e2 is not None and (
                record.get("verdict") != e2.get("verdict")
                or (e1 is not None and not _reference_matches(e2, "target_e1_ref", e1))
                or (
                    manifest is not None
                    and not _reference_matches(e2, "audit_manifest_ref", manifest)
                )
                or (
                    assignment is not None
                    and not _reference_matches(e2, "audit_assignment_ref", assignment)
                )
                or (
                    manifest is not None
                    and assignment is not None
                    and not _reference_matches(
                        manifest, "audit_assignment_ref", assignment
                    )
                )
            ):
                issues.add("AUDIT_VERDICT_MISMATCH")

        elif object_type == E3_ACCEPTED_DISCOVERY:
            e1 = dep(record, "e1_ref")
            e2 = dep(record, "e2_ref")
            receipt = dep(record, "audit_completion_receipt_ref")
            if e2 is not None and e2.get("verdict") == "REJECT":
                issues.add("REJECTED_LINEAGE_CANNOT_PROGRESS")
            if e1 is not None and e2 is not None and not _reference_matches(
                e2, "target_e1_ref", e1
            ):
                issues.add("IMMUTABLE_TARGET_MISMATCH")
            if e2 is not None and receipt is not None and not _reference_matches(
                receipt, "e2_ref", e2
            ):
                issues.add("AUDIT_VERDICT_MISMATCH")
            if e1 is not None and e1.get("discovery_claim") not in record.get(
                "accepted_claims", ()
            ):
                issues.add("ACCEPTED_CLAIM_MISMATCH")
            if e1 is not None and record.get("accepted_claims") != [
                e1.get("discovery_claim")
            ]:
                issues.add("ACCEPTED_CLAIM_MISMATCH")
            if set(record.get("accepted_claims", ())) & set(
                record.get("excluded_claims", ())
            ):
                issues.add("ACCEPTED_CLAIM_MISMATCH")
            if e2 is not None:
                required = list(e2.get("required_deltas", ()))
                revisions = record.get("revision_applied", ())
                applied = [
                    item.get("required_delta")
                    for item in revisions
                    if isinstance(item, Mapping)
                ]
                if e2.get("verdict") == "REVISE" and (
                    len(applied) != len(set(applied))
                    or set(applied) != set(required)
                ):
                    issues.add("REVISION_BINDING_INCOMPLETE")
                if e2.get("verdict") == "SURVIVE" and applied:
                    issues.add("REVISION_BINDING_INCOMPLETE")

        elif object_type == E4_IMPLEMENTATION_BINDING:
            e3 = dep(record, "e3_ref")
            assignment = dep(record, "implementation_assignment_ref")
            if assignment is not None and assignment.get("seat") != "IMPLEMENTATION":
                issues.add("IMPLEMENTATION_AUTHORITY_MISSING")
            if not (
                record.get("repository_base_is_ancestor") is True
                and record.get("repository_base") != record.get("repository_head")
                and record.get("repository_opening_head")
                == record.get("repository_head")
                == record.get("repository_closing_head")
            ):
                issues.add("REPOSITORY_BINDING_INVALID")
            artifacts = record.get("changed_artifacts", ())
            bindings = record.get("claim_bindings", ())
            artifact_keys = {
                (
                    item.get("asset_identity"),
                    item.get("asset_version"),
                    item.get("sha256"),
                )
                for item in artifacts
                if isinstance(item, Mapping)
            }
            binding_claims = [
                item.get("accepted_claim")
                for item in bindings
                if isinstance(item, Mapping)
            ]
            accepted_claims = (
                list(e3.get("accepted_claims", ())) if e3 is not None else []
            )
            if (
                len(binding_claims) != len(set(binding_claims))
                or set(binding_claims) != set(accepted_claims)
                or any(
                    (
                        item.get("asset_identity"),
                        item.get("asset_version"),
                        item.get("asset_hash"),
                    )
                    not in artifact_keys
                    for item in bindings
                    if isinstance(item, Mapping)
                )
            ):
                issues.add("CLAIM_BINDING_INCOMPLETE")
            if any(
                not _behavioral_verification_valid(
                    item.get("behavioral_verification")
                )
                or not _activation_evidence_valid(item.get("activation_evidence"))
                for item in bindings
                if isinstance(item, Mapping)
            ):
                issues.add("BEHAVIORAL_ACTIVATION_MISSING")

        elif object_type == LOWER_RUN_TRIAL_MANIFEST:
            e4 = dep(record, "e4_ref")
            assignment = dep(record, "lower_run_assignment_ref")
            if assignment is not None and (
                assignment.get("seat") != "LOWER_RUN"
                or assignment.get("assignee_context_identity")
                != record.get("lower_runtime_context_identity")
            ):
                issues.add("LOWER_RUN_AUTHORITY_MISSING")
            if (
                record.get("source_task_id") != charter.get("source_task_id")
                or record.get("source_task_hash") != charter.get("source_task_hash")
            ):
                issues.add("CHARTER_BINDING_MISMATCH")
            if (
                record.get("new_task_id") == record.get("source_task_id")
                or record.get("new_task_hash") == record.get("source_task_hash")
            ):
                issues.add("SAME_TASK_REUSE")
            if record.get("failure_family_id") != charter.get("failure_family_id"):
                issues.add("FAILURE_FAMILY_MISMATCH")
            if record.get("failure_predicate") != charter.get("failure_predicate"):
                issues.add("FAILURE_PREDICATE_MISMATCH")
            if not REQUIRED_FORBIDDEN_INPUT_CLASSES.issubset(
                set(record.get("forbidden_input_classes", ()))
            ):
                issues.add("LOWER_RUN_INPUT_LEAKAGE")
            expected_allowed_inputs = [
                {
                    "input_class": "NEW_TASK",
                    "task_id": record.get("new_task_id"),
                    "sha256": record.get("new_task_hash"),
                },
                {
                    "input_class": "REPOSITORY_STATE",
                    "repository_head": record.get("repository_head"),
                },
                {
                    "input_class": "ACTIVE_ASSET",
                    "asset_identity": record.get("active_asset_identity"),
                    "asset_version": record.get("active_asset_version"),
                    "asset_hash": record.get("active_asset_hash"),
                },
                {
                    "input_class": "MINIMUM_EXECUTION_BOUNDARY",
                    "boundary": record.get("minimum_execution_boundary"),
                },
            ]
            if record.get("allowed_input_manifest") != expected_allowed_inputs:
                issues.add("LOWER_RUN_INPUT_LEAKAGE")
            if record.get("allowed_input_manifest_hash") != hashlib.sha256(
                canonical_json(record.get("allowed_input_manifest"))
            ).hexdigest():
                issues.add("LOWER_RUN_INPUT_LEAKAGE")
            if e4 is not None:
                artifact_keys = {
                    (
                        item.get("asset_identity"),
                        item.get("asset_version"),
                        item.get("sha256"),
                    )
                    for item in e4.get("changed_artifacts", ())
                    if isinstance(item, Mapping)
                }
                active_key = (
                    record.get("active_asset_identity"),
                    record.get("active_asset_version"),
                    record.get("active_asset_hash"),
                )
                if (
                    active_key not in artifact_keys
                    or record.get("repository_head") != e4.get("repository_head")
                ):
                    issues.add("ASSET_BINDING_MISMATCH")
            context_id = record.get("lower_runtime_context_identity")
            for candidate in objects:
                if (
                    candidate.get("object_type") == SEAT_ASSIGNMENT_RECEIPT
                    and candidate.get("seat") in ("DISCOVERY", "AUDIT")
                    and candidate.get("assignee_context_identity") == context_id
                ):
                    issues.add("CONTEXT_INDEPENDENCE_VIOLATION")

        elif object_type == LOWER_RUN_COMPLETION_RECEIPT:
            manifest = dep(record, "trial_manifest_ref")
            e4 = dep(record, "e4_ref")
            if manifest is not None:
                if (
                    record.get("trial_id") != manifest.get("trial_id")
                    or record.get("actual_input_manifest_hash")
                    != manifest.get("allowed_input_manifest_hash")
                    or record.get("lower_runtime_context_identity")
                    != manifest.get("lower_runtime_context_identity")
                ):
                    issues.add("LOWER_RUN_INPUT_LEAKAGE")
                manifest_time = _parse_timestamp(manifest.get("as_of"))
                start_time = _parse_timestamp(record.get("started_as_of"))
                if (
                    manifest_time is not None
                    and start_time is not None
                    and manifest_time >= start_time
                ):
                    issues.add("LOWER_RUN_MANIFEST_NOT_PREFROZEN")
                active = (
                    record.get("active_asset_identity"),
                    record.get("active_asset_version"),
                    record.get("active_asset_hash"),
                )
                manifest_active = (
                    manifest.get("active_asset_identity"),
                    manifest.get("active_asset_version"),
                    manifest.get("active_asset_hash"),
                )
                if active != manifest_active:
                    issues.add("ASSET_BINDING_MISMATCH")
                if (
                    e4 is not None
                    and not _reference_matches(manifest, "e4_ref", e4)
                ):
                    issues.add("E5_CHAIN_SPLICE")
            trace = record.get("asset_activation_trace")
            if isinstance(trace, Mapping):
                trace_active = (
                    trace.get("asset_identity"),
                    trace.get("asset_version"),
                    trace.get("asset_hash"),
                )
                record_active = (
                    record.get("active_asset_identity"),
                    record.get("active_asset_version"),
                    record.get("active_asset_hash"),
                )
                if (
                    trace_active != record_active
                    or (e4 is not None and trace.get("e4_ref") != exact_ref(e4))
                    or trace.get("failure_predicate")
                    != charter.get("failure_predicate")
                    or trace.get("interception_point", {}).get(
                        "observed_effect"
                    )
                    != record.get("detection_or_prevention_result")
                ):
                    issues.add("CAUSAL_TRACE_MISMATCH")
            started = _parse_timestamp(record.get("started_as_of"))
            activated = _parse_timestamp(record.get("asset_activated_as_of"))
            failed = _parse_timestamp(record.get("failure_observed_as_of"))
            completed = _parse_timestamp(record.get("completed_as_of"))
            if not (
                started is not None
                and activated is not None
                and failed is not None
                and completed is not None
                and started <= activated < failed <= completed
            ):
                issues.add("ASSET_NOT_ACTIVATED")
            sequence = record.get("event_sequence", ())
            if sequence != list(LOWER_RUN_EVENT_SEQUENCE):
                issues.add("ASSET_NOT_ACTIVATED")
            if record.get("human_rescue") != "NONE":
                issues.add("HUMAN_RESCUE_PRESENT")
            if (
                record.get("no_rescue_attestation") != "NO_HUMAN_RESCUE"
                or "HUMAN_RESCUE" in sequence
            ):
                issues.add("NO_RESCUE_SEQUENCE_MISMATCH")
            if record.get("causal_proof_mode") == "INTERCEPTION_TRACE":
                if record.get("controlled_contrast") is not None:
                    issues.add("CAUSAL_TRACE_MISMATCH")
            elif record.get("causal_proof_mode") == "CONTROLLED_CONTRAST":
                if not _contrast_valid(record.get("controlled_contrast")):
                    issues.add("UNCONTROLLED_CONTRAST")
                elif (
                    record["controlled_contrast"].get("on_result")
                    != record.get("detection_or_prevention_result")
                ):
                    issues.add("CAUSAL_TRACE_MISMATCH")

        elif object_type == E5_REUSE:
            e4 = dep(record, "e4_ref")
            manifest = dep(record, "trial_manifest_ref")
            completion = dep(record, "completion_receipt_ref")
            if manifest is not None and (
                record.get("source_task_id") != manifest.get("source_task_id")
                or record.get("new_task_id") != manifest.get("new_task_id")
            ):
                issues.add("SAME_TASK_REUSE")
            if record.get("source_task_id") == record.get("new_task_id"):
                issues.add("SAME_TASK_REUSE")
            if record.get("failure_family_id") != charter.get("failure_family_id"):
                issues.add("FAILURE_FAMILY_MISMATCH")
            if record.get("failure_predicate") != charter.get("failure_predicate"):
                issues.add("FAILURE_PREDICATE_MISMATCH")
            if manifest is not None and (
                record.get("failure_family_id") != manifest.get("failure_family_id")
                or record.get("failure_predicate") != manifest.get("failure_predicate")
            ):
                issues.add("FAILURE_FAMILY_MISMATCH")
            if completion is not None and (
                record.get("causal_proof_mode")
                != completion.get("causal_proof_mode")
                or record.get("detection_or_prevention_result")
                != completion.get("detection_or_prevention_result")
                or completion.get("human_rescue") != "NONE"
            ):
                issues.add("CAUSAL_TRACE_MISMATCH")
            if (
                e4 is not None
                and manifest is not None
                and not _reference_matches(manifest, "e4_ref", e4)
            ):
                issues.add("ASSET_BINDING_MISMATCH")
                issues.add("E5_CHAIN_SPLICE")
            if (
                manifest is not None
                and completion is not None
                and (
                    not _reference_matches(
                        completion, "trial_manifest_ref", manifest
                    )
                    or (
                        e4 is not None
                        and not _reference_matches(completion, "e4_ref", e4)
                    )
                )
            ):
                issues.add("E5_CHAIN_SPLICE")

        elif object_type == MANUAL_CONTROL_RECEIPT:
            target = dep(record, "target_ref")
            action = record.get("control_action")
            if action == "CAP":
                prefix = objects[:record_position]
                prior_cap, _ = _cap_state(
                    prefix, _parse_timestamp(record.get("as_of"))
                )
                if prior_cap is not None:
                    issues.add("CONTROL_CANNOT_RESCUE_INVALID_GRAPH")
                prefix_records = _current_records(prefix)
                prefix_registry = _record_registry(prefix_records)
                prefix_chain = _select_chain(prefix_records)
                actual_maturity = _chain_maturity(
                    prefix_chain, prefix, prefix_registry
                )
                if record.get("capped_from") != actual_maturity:
                    issues.add("CAP_MATURITY_MISMATCH")
                roots = _chain_records(prefix_chain)
                if not roots:
                    roots = (charter,)
                current_closure = _dependency_closure(roots, prefix_registry)
                if target is None or not any(
                    target is candidate for candidate in current_closure
                ):
                    issues.add("CAP_TARGET_NOT_CURRENT")
                if actual_maturity in (DELTA_REJECTED, DELTA_REVOKED):
                    issues.add("CONTROL_CANNOT_RESCUE_INVALID_GRAPH")
            elif action == "CAP_RELEASE":
                release_prefix = objects[:record_position]
                release_current_records = _current_records(release_prefix)
                release_registry = _record_registry(release_current_records)
                if (
                    target is None
                    or target.get("object_type") != MANUAL_CONTROL_RECEIPT
                    or target.get("control_action") != "CAP"
                    or record.get("cap_release_condition")
                    != target.get("cap_release_condition")
                ):
                    issues.add("CAP_RELEASE_AUTHORITY_MISSING")
                for reference in record.get("release_evidence_refs", ()):
                    evidence = registry.get(reference.get("object_id"))
                    current_evidence = release_registry.get(
                        str(reference.get("object_id"))
                    )
                    evidence_position = position_by_id.get(
                        str(reference.get("object_id"))
                    )
                    target_position = (
                        position_by_id.get(str(target.get("object_id")))
                        if target is not None
                        else None
                    )
                    if (
                        evidence is None
                        or evidence.get("content_hash") != reference.get("content_hash")
                        or evidence_position is None
                        or target_position is None
                        or evidence_position <= target_position
                        or current_evidence is not evidence
                        or evidence.get("object_type")
                        == MANUAL_CONTROL_RECEIPT
                        or not _dependencies_are_current(
                            evidence, release_registry
                        )
                        or _chain_revocation(
                            release_prefix,
                            _dependency_closure(
                                (evidence,), release_registry
                            ),
                        )
                        is not None
                    ):
                        issues.add("CAP_RELEASE_AUTHORITY_MISSING")
            elif action == "ROLLBACK":
                current_e4 = _current_e4_at(objects, record_position)
                if (
                    target is None
                    or target.get("object_type") != E4_IMPLEMENTATION_BINDING
                    or current_e4 is None
                    or target is not current_e4
                ):
                    issues.add("ROLLBACK_TARGET_MISMATCH")
            elif action == "REVOKE" and target is not None and target.get(
                "object_type"
            ) in (RUN_CHARTER, MANUAL_CONTROL_RECEIPT):
                issues.add("REVOKE_AUTHORITY_MISSING")

    controlled_e4_positions: list[
        tuple[int, Mapping[str, Any], str]
    ] = []
    for position, record in enumerate(objects):
        if (
            record.get("object_type") == MANUAL_CONTROL_RECEIPT
            and record.get("control_action") in ("REVOKE", "ROLLBACK")
        ):
            target = registry.get(str(record.get("target_object_id")))
            if (
                target is not None
                and target.get("content_hash")
                == record.get("target_content_hash")
                and target.get("object_type") == E4_IMPLEMENTATION_BINDING
            ):
                controlled_e4_positions.append(
                    (
                        position,
                        target,
                        (
                            "ROLLBACK_FORWARD_REPLACEMENT_REQUIRED"
                            if record.get("control_action") == "ROLLBACK"
                            else "FORWARD_REPLACEMENT_REQUIRED"
                        ),
                    )
                )
    for control_position, controlled_e4, issue_code in controlled_e4_positions:
        predecessor = controlled_e4
        for candidate in objects[control_position + 1 :]:
            if candidate.get("object_type") != E4_IMPLEMENTATION_BINDING:
                continue
            if candidate.get("supersedes") != exact_ref(predecessor):
                issues.add(issue_code)
            else:
                predecessor = candidate

    rejected_e1: list[
        tuple[int, Mapping[str, Any], Mapping[str, Any]]
    ] = []
    for candidate_position, candidate in enumerate(objects):
        if (
            candidate.get("object_type") == E2_AUDIT
            and candidate.get("verdict") == "REJECT"
        ):
            target_ref = candidate.get("target_e1_ref")
            target = (
                registry.get(target_ref.get("object_id"))
                if isinstance(target_ref, Mapping)
                else None
            )
            if target is not None:
                rejected_e1.append(
                    (candidate_position, target, candidate)
                )
    material_fields = (
        "discovery_claim",
        "observed_failure",
        "mechanism",
        "strongest_falsifier",
        "evidence_anchors",
    )
    blocked_after_reject = {
        AUDIT_INPUT_MANIFEST,
        E2_AUDIT,
        AUDIT_COMPLETION_RECEIPT,
        E3_ACCEPTED_DISCOVERY,
        E4_IMPLEMENTATION_BINDING,
        LOWER_RUN_TRIAL_MANIFEST,
        LOWER_RUN_COMPLETION_RECEIPT,
        E5_REUSE,
    }
    for candidate_position, candidate in enumerate(objects):
        if candidate.get("object_type") != E1_DISCOVERY:
            for rejected_position, rejected, rejecting_e2 in rejected_e1:
                if (
                    candidate_position <= rejected_position
                    or candidate.get("object_type")
                    not in blocked_after_reject
                    or (
                        candidate.get("object_type")
                        == AUDIT_COMPLETION_RECEIPT
                        and candidate.get("e2_ref") == exact_ref(rejecting_e2)
                        and candidate.get("verdict") == "REJECT"
                    )
                ):
                    continue
                closure = _dependency_closure((candidate,), registry)
                if any(item is rejected for item in closure):
                    issues.add("REJECTED_LINEAGE_CANNOT_PROGRESS")
            continue
        for rejected_position, rejected, _ in rejected_e1:
            if candidate_position <= rejected_position or candidate is rejected:
                continue
            if all(
                candidate.get(field) == rejected.get(field)
                for field in material_fields
            ):
                issues.add("REJECTED_LINEAGE_CANNOT_PROGRESS")

    return _assessment(issues)


def _record_time(record: Mapping[str, Any]) -> datetime:
    parsed = _parse_timestamp(record.get("as_of"))
    return parsed if parsed is not None else datetime.min.replace(tzinfo=timezone.utc)


def _current_records(
    objects: Sequence[Mapping[str, Any]],
    *,
    cutoff: datetime | None = None,
) -> list[Mapping[str, Any]]:
    selected = [
        record
        for record in objects
        if cutoff is None or _record_time(record) <= cutoff
    ]
    replaced = {
        record["supersedes"]["object_id"]
        for record in selected
        if _is_ref(record.get("supersedes"))
    }
    return [record for record in selected if record.get("object_id") not in replaced]


def _latest(
    records: Iterable[Mapping[str, Any]],
    object_type: str,
    *,
    predicate: Any = None,
) -> Mapping[str, Any] | None:
    candidates = [
        (position, record)
        for position, record in enumerate(records)
        if record.get("object_type") == object_type
        and (predicate is None or predicate(record))
    ]
    return (
        max(candidates, key=lambda item: (_record_time(item[1]), item[0]))[1]
        if candidates
        else None
    )


def _semantic_refs(
    record: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    supersedes = record.get("supersedes")
    return tuple(
        reference
        for reference in _all_refs(record)
        if reference != supersedes
    )


def _record_registry(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    return {
        str(record.get("object_id")): record
        for record in records
        if isinstance(record.get("object_id"), str)
    }


def _dependency_closure(
    roots: Iterable[Mapping[str, Any]],
    registry: Mapping[str, Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    selected: dict[str, Mapping[str, Any]] = {}

    def include(record: Mapping[str, Any]) -> None:
        object_id = str(record.get("object_id"))
        if object_id in selected:
            return
        selected[object_id] = record
        for reference in _semantic_refs(record):
            target = registry.get(reference["object_id"])
            if (
                target is not None
                and target.get("content_hash") == reference["content_hash"]
            ):
                include(target)

    for root in roots:
        include(root)
    return tuple(selected.values())


def _dependencies_are_current(
    record: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, Any]],
) -> bool:
    pending = [record]
    visited: set[str] = set()
    while pending:
        candidate = pending.pop()
        object_id = str(candidate.get("object_id"))
        if object_id in visited:
            continue
        visited.add(object_id)
        for reference in _semantic_refs(candidate):
            target = registry.get(reference["object_id"])
            if (
                target is None
                or target.get("content_hash") != reference["content_hash"]
            ):
                return False
            pending.append(target)
    return True


def _select_chain(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any] | None]:
    """Select only a chain whose complete semantic dependency closure is current."""

    registry = _record_registry(records)
    current = lambda item: _dependencies_are_current(item, registry)
    e1 = _latest(records, E1_DISCOVERY, predicate=current)
    e2 = (
        _latest(
            records,
            E2_AUDIT,
            predicate=lambda item: current(item)
            and item.get("target_e1_ref") == exact_ref(e1),
        )
        if e1 is not None
        else None
    )
    audit_receipt = (
        _latest(
            records,
            AUDIT_COMPLETION_RECEIPT,
            predicate=lambda item: current(item)
            and item.get("e2_ref") == exact_ref(e2),
        )
        if e2 is not None
        else None
    )
    e3 = (
        _latest(
            records,
            E3_ACCEPTED_DISCOVERY,
            predicate=lambda item: current(item)
            and item.get("e2_ref") == exact_ref(e2)
            and item.get("audit_completion_receipt_ref")
            == exact_ref(audit_receipt),
        )
        if e2 is not None and audit_receipt is not None
        else None
    )
    e4 = (
        _latest(
            records,
            E4_IMPLEMENTATION_BINDING,
            predicate=lambda item: current(item)
            and item.get("e3_ref") == exact_ref(e3),
        )
        if e3 is not None
        else None
    )
    def linked(
        owner: Mapping[str, Any],
        field: str,
        expected_type: str,
    ) -> Mapping[str, Any] | None:
        reference = owner.get(field)
        if not _is_ref(reference):
            return None
        target = registry.get(reference["object_id"])
        if (
            target is None
            or target.get("content_hash") != reference["content_hash"]
            or target.get("object_type") != expected_type
            or not current(target)
        ):
            return None
        return target

    def complete_reuse(item: Mapping[str, Any]) -> bool:
        if (
            e4 is None
            or not current(item)
            or item.get("e4_ref") != exact_ref(e4)
        ):
            return False
        candidate_manifest = linked(
            item, "trial_manifest_ref", LOWER_RUN_TRIAL_MANIFEST
        )
        candidate_completion = linked(
            item,
            "completion_receipt_ref",
            LOWER_RUN_COMPLETION_RECEIPT,
        )
        return (
            candidate_manifest is not None
            and candidate_completion is not None
            and candidate_manifest.get("e4_ref") == exact_ref(e4)
            and candidate_completion.get("e4_ref") == exact_ref(e4)
            and candidate_completion.get("trial_manifest_ref")
            == exact_ref(candidate_manifest)
        )

    e5 = (
        _latest(records, E5_REUSE, predicate=complete_reuse)
        if e4 is not None
        else None
    )
    manifest = (
        linked(e5, "trial_manifest_ref", LOWER_RUN_TRIAL_MANIFEST)
        if e5 is not None
        else None
    )
    completion = (
        linked(
            e5,
            "completion_receipt_ref",
            LOWER_RUN_COMPLETION_RECEIPT,
        )
        if e5 is not None
        else None
    )

    def complete_trial(item: Mapping[str, Any]) -> bool:
        if (
            e4 is None
            or not current(item)
            or item.get("e4_ref") != exact_ref(e4)
        ):
            return False
        candidate_manifest = linked(
            item, "trial_manifest_ref", LOWER_RUN_TRIAL_MANIFEST
        )
        return (
            candidate_manifest is not None
            and candidate_manifest.get("e4_ref") == exact_ref(e4)
        )

    if completion is None and e4 is not None:
        completion = _latest(
            records,
            LOWER_RUN_COMPLETION_RECEIPT,
            predicate=complete_trial,
        )
        if completion is not None:
            manifest = linked(
                completion,
                "trial_manifest_ref",
                LOWER_RUN_TRIAL_MANIFEST,
            )
    if manifest is None and e4 is not None:
        manifest = _latest(
            records,
            LOWER_RUN_TRIAL_MANIFEST,
            predicate=lambda item: current(item)
            and item.get("e4_ref") == exact_ref(e4),
        )
    return {
        "e1": e1,
        "e2": e2,
        "audit_receipt": audit_receipt,
        "e3": e3,
        "e4": e4,
        "manifest": manifest,
        "completion": completion,
        "e5": e5,
    }


def _chain_records(
    chain: Mapping[str, Mapping[str, Any] | None],
) -> tuple[Mapping[str, Any], ...]:
    return tuple(item for item in chain.values() if item is not None)


def _chain_revocation(
    controls: Sequence[Mapping[str, Any]],
    closure: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    closure_ids = {record.get("object_id") for record in closure}
    return _latest(
        controls,
        MANUAL_CONTROL_RECEIPT,
        predicate=lambda item: item.get("control_action")
        in ("REVOKE", "ROLLBACK")
        and item.get("target_object_id") in closure_ids,
    )


def _chain_maturity(
    chain: Mapping[str, Mapping[str, Any] | None],
    controls: Sequence[Mapping[str, Any]],
    registry: Mapping[str, Mapping[str, Any]],
) -> str:
    e1 = chain["e1"]
    e2 = chain["e2"]
    receipt = chain["audit_receipt"]
    e3 = chain["e3"]
    e4 = chain["e4"]
    e5 = chain["e5"]
    closure = _dependency_closure(_chain_records(chain), registry)
    if _chain_revocation(controls, closure) is not None:
        return DELTA_REVOKED
    if e1 is None:
        return DELTA_NONE
    if e2 is not None and receipt is not None and e2.get("verdict") == "REJECT":
        return DELTA_REJECTED
    if e3 is None:
        return DELTA_NONE
    if e4 is None:
        return DELTA_CANDIDATE
    if e5 is None:
        return DELTA_IMPLEMENTED
    return DELTA_REUSED


def _cap_state(
    objects: Sequence[Mapping[str, Any]],
    current: datetime | None,
) -> tuple[Mapping[str, Any] | None, bool]:
    controls = [
        (position, record)
        for position, record in enumerate(objects)
        if record.get("object_type") == MANUAL_CONTROL_RECEIPT
    ]
    caps = [
        (position, record)
        for position, record in controls
        if record.get("control_action") == "CAP"
    ]
    for cap_position, cap in reversed(caps):
        released = any(
            record.get("control_action") == "CAP_RELEASE"
            and _declared_ref(record, "target_ref") == exact_ref(cap)
            and position > cap_position
            for position, record in controls
        )
        if released:
            continue
        expires = _parse_timestamp(cap.get("cap_expires_as_of"))
        if expires is not None and current is not None and current >= expires:
            return cap, True
        return cap, False
    return None, False


def _evidence_summary(
    objects: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "object_id": str(record.get("object_id")),
            "object_type": str(record.get("object_type")),
            "content_hash": str(record.get("content_hash")),
            "lifecycle": (
                "FORWARD_ONLY_REPLACED"
                if any(
                    candidate.get("supersedes") == exact_ref(record)
                    for candidate in objects
                )
                else "CURRENT"
            ),
        }
        for record in sorted(objects, key=_record_time)
        if record.get("object_type") not in (RUN_CHARTER, MANUAL_CONTROL_RECEIPT)
    )


def _invalid_projection(
    objects: Sequence[Mapping[str, Any]],
    assessment: ValidationAssessment,
) -> IntelligenceTransplantProjection:
    charter = next(
        (
            record
            for record in objects
            if isinstance(record, Mapping)
            and record.get("object_type") == RUN_CHARTER
        ),
        None,
    )
    run_id = str(charter.get("run_id")) if charter is not None else "UNKNOWN"
    version_only = set(assessment.issue_codes).issubset(
        {"UNSUPPORTED_SCHEMA_VERSION"}
    )
    gate = GATE_HOLD if version_only else GATE_BLOCK
    return IntelligenceTransplantProjection(
        run_id=run_id,
        execution_status=EXECUTION_NOT_ESTABLISHED,
        delta_state=DELTA_NONE,
        current_gate=gate,
        missing_evidence=assessment.issue_codes,
        next_one_action=(
            "Open the unsupported Stage 5 version read-only."
            if version_only
            else "Correct the invalid Stage 5 record graph without promoting state."
        ),
        not_allowed_next=(
            "Do not promote CANDIDATE, IMPLEMENTED, or REUSED.",
            "Do not use CAP to rescue invalid evidence.",
            "Do not claim cryptographic or generalized provenance.",
        ),
        evidence_objects=(),
        active_cap=None,
        structural_validation=STRUCTURAL_FAIL,
        issue_codes=assessment.issue_codes,
    )


def reduce_evidence_graph(
    objects: Sequence[Mapping[str, Any]],
    *,
    now: datetime | str | None = None,
) -> IntelligenceTransplantProjection:
    """Reduce one valid graph into the canonical read-only Stage 5 projection."""

    assessment = validate_graph(objects, now=now)
    if not assessment.valid:
        return _invalid_projection(objects, assessment)
    current_time = _valid_now(now)
    cap, cap_expired = _cap_state(objects, current_time)
    cap_position = (
        next(
            position
            for position, record in enumerate(objects)
            if cap is record
        )
        if cap is not None
        else len(objects)
    )
    effective_source = objects[:cap_position] if cap is not None else objects
    current_records = _current_records(effective_source)
    charter = next(
        record for record in current_records if record.get("object_type") == RUN_CHARTER
    )
    chain = _select_chain(current_records)
    e1 = chain["e1"]
    e2 = chain["e2"]
    audit_receipt = chain["audit_receipt"]
    e3 = chain["e3"]
    e4 = chain["e4"]
    manifest = chain["manifest"]
    completion = chain["completion"]
    e5 = chain["e5"]
    registry = _record_registry(current_records)
    selected_chain = _chain_records(chain)
    closure = _dependency_closure(selected_chain, registry)
    revocation = _chain_revocation(objects, closure)
    full_chain = _select_chain(_current_records(objects))
    full_e2 = full_chain["e2"]
    full_rejected = (
        full_e2 is not None
        and full_e2.get("verdict") == "REJECT"
        and full_chain["audit_receipt"] is not None
    )

    if full_rejected:
        execution = EXECUTION_ACTIVE
        delta = DELTA_REJECTED
        gate = GATE_BLOCK
        missing = ("MATERIALLY_NEW_E1_LINEAGE",)
        next_action = "Begin a materially new E1 lineage before reconsideration."
    elif e1 is None:
        execution = EXECUTION_NOT_ESTABLISHED
        delta = DELTA_NONE
        gate = charter["charter_gate"]
        missing = ("E1_DISCOVERY",)
        next_action = "Attach a manually authorized E1 discovery record."
    elif revocation is not None:
        execution = EXECUTION_ACTIVE
        delta = DELTA_REVOKED
        gate = GATE_HOLD
        missing = ("FORWARD_ONLY_REPLACEMENT",)
        next_action = "Start a new forward-only evidence branch from current authority."
    elif e2 is None or audit_receipt is None:
        execution = EXECUTION_ACTIVE
        delta = DELTA_NONE
        gate = GATE_HOLD
        missing = (
            "AUDIT_INPUT_MANIFEST",
            "E2_AUDIT",
            "AUDIT_COMPLETION_RECEIPT",
        )
        next_action = "Complete a pre-frozen independent E2 audit."
    elif e2.get("verdict") == "REJECT":
        execution = EXECUTION_ACTIVE
        delta = DELTA_REJECTED
        gate = GATE_BLOCK
        missing = ("MATERIALLY_NEW_E1_LINEAGE",)
        next_action = "Begin a materially new E1 lineage before reconsideration."
    elif e3 is None:
        execution = EXECUTION_ACTIVE
        delta = DELTA_NONE
        gate = GATE_HOLD
        missing = ("E3_ACCEPTED_DISCOVERY",)
        next_action = "Attach the accepted or fully revised E3 discovery."
    elif e4 is None:
        execution = EXECUTION_ACTIVE
        delta = DELTA_CANDIDATE
        implementation_authority = _latest(
            current_records,
            SEAT_ASSIGNMENT_RECEIPT,
            predicate=lambda item: item.get("seat") == "IMPLEMENTATION",
        )
        gate = GATE_GO if implementation_authority is not None else GATE_HOLD
        missing = (
            ("E4_IMPLEMENTATION_BINDING",)
            if implementation_authority is not None
            else ("IMPLEMENTATION_SEAT_ASSIGNMENT", "E4_IMPLEMENTATION_BINDING")
        )
        next_action = (
            "Implement and bind every accepted claim under the fixed authority."
            if implementation_authority is not None
            else "Freeze a separate implementation Seat Assignment Receipt."
        )
    elif e5 is None:
        execution = EXECUTION_ACTIVE
        delta = DELTA_IMPLEMENTED
        gate = GATE_GO if manifest is not None else GATE_HOLD
        missing = (
            ("LOWER_RUN_COMPLETION_RECEIPT", "E5_REUSE")
            if manifest is not None
            else ("LOWER_RUN_TRIAL_MANIFEST",)
        )
        next_action = (
            "Run only the pre-frozen lower-run trial and record causal proof."
            if manifest is not None
            else "Freeze the blind lower-run trial manifest before execution."
        )
    else:
        execution = EXECUTION_ACTIVE
        delta = DELTA_REUSED
        gate = GATE_HOLD
        missing = ("GENERALIZED_TRANSPLANT_NOT_ESTABLISHED",)
        next_action = "Hold generalized claims; preserve this case-bounded reuse."

    active_cap: dict[str, Any] | None = None
    if cap is not None:
        active_cap = {
            "receipt_id": cap["receipt_id"],
            "receipt_hash": cap["receipt_hash"],
            "target_ref": {
                "object_id": cap["target_object_id"],
                "content_hash": cap["target_content_hash"],
            },
            "capped_from": cap["capped_from"],
            "cap_axis": cap["cap_axis"],
            "cap_limit": cap["cap_limit"],
            "cap_release_condition": cap["cap_release_condition"],
            "cap_expires_as_of": cap["cap_expires_as_of"],
            "status": "EXPIRED_HOLD" if cap_expired else "ACTIVE",
        }
        if delta not in (DELTA_REJECTED, DELTA_REVOKED):
            gate = GATE_HOLD if cap_expired else GATE_CAP
            missing = tuple(dict.fromkeys((*missing, "CAP_RELEASE_CONDITION")))
            next_action = (
                "Record an explicit CAP release; expiry does not release authority."
                if cap_expired
                else "Satisfy the exact CAP release condition under manual authority."
            )

    not_allowed = tuple(
        dict.fromkeys(
            (
                *charter["not_allowed_next"],
                "Do not claim cryptographic provenance.",
                "Do not claim generalized transplant.",
                "Do not start an automatic model or Role invocation.",
            )
        )
    )
    return IntelligenceTransplantProjection(
        run_id=charter["run_id"],
        execution_status=execution,
        delta_state=delta,
        current_gate=gate,
        missing_evidence=tuple(missing),
        next_one_action=next_action,
        not_allowed_next=not_allowed,
        evidence_objects=_evidence_summary(objects),
        active_cap=active_cap,
        structural_validation=STRUCTURAL_PASS,
        issue_codes=(),
    )
