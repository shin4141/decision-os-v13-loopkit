"""Field Notes Lite A7 bounded A1-A6 Whole-Flow proof contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import re
from typing import TYPE_CHECKING, Any, Literal

from decision_os.acceleration.codex_adapter import CodexRuntimeIdentity
from decision_os.companion.field_notes_maturity_commit import (
    FieldNoteMaturityCommitResult,
)
from decision_os.companion.field_notes_maturity_ledger import (
    GENESIS_EVENT_SHA256,
    LEDGER_EVENT_KIND,
    LEDGER_EVENT_SCHEMA,
    FieldNoteMaturityLedgerEvent,
    FieldNoteMaturityLedgerSnapshot,
)
from decision_os.companion.field_notes_maturity_review import (
    FieldNoteMaturityReviewPacket,
)
from decision_os.companion.field_notes_model import (
    FIELD_NOTE_SCHEMA_VERSION,
    FieldNoteDraft,
    canonical_json,
    validate_compiled_markdown,
)
from decision_os.companion.field_notes_reconnect import (
    FieldNoteReconnectReceipt,
)
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteReuseReceipt,
    PromotionPolicyBoundary,
)

if TYPE_CHECKING:
    from decision_os.companion.field_notes_creator_live import (
        FieldNoteCreatorLiveTraceReadback,
    )


WHOLE_FLOW_SCHEMA = "decision-os.field-note-whole-flow-proof.v0.1"
WHOLE_FLOW_SCHEMA_V2 = "decision-os.field-note-whole-flow-proof.v0.2"
WHOLE_FLOW_TRACE_SCHEMA = "decision-os.field-note-whole-flow-trace-event.v0.1"
WAREHOUSE_MANIFEST_SCHEMA = (
    "decision-os.portable-candidate-warehouse-manifest.v0.1"
)
PORTABLE_ASSET_SCHEMA = "decision-os.portable-field-note-asset.v0.1"
CREATOR_LIVE_PROVENANCE_SCHEMA = (
    "decision-os.field-note-creator-live-runtime-provenance.v0.1"
)
TRACE_GENESIS_SHA256 = "0" * 64

WholeFlowState = Literal["NOT_READY", "PASS", "FAIL"]
WholeFlowMode = Literal["FIXTURE", "CREATOR_LIVE"]
WholeFlowBoundary = Literal[
    "RUNTIME_ENFORCEMENT",
    "A1_CAPTURE",
    "RUN_SEPARATION",
    "MODEL_IDENTITY",
    "REPOSITORY_IDENTITY",
    "A2_RECONNECT",
    "A3_REUSE",
    "A4_DURABILITY",
    "A5_CONFIRMATION",
    "A6_REVIEW",
    "HUMAN_REPAIR",
    "PROOF_AS_OF",
]
HumanRepairResult = Literal[
    "NOT_EVALUATED",
    "INCOMPLETE",
    "TYPED_TRACE_VERIFIED",
    "REPAIR_DETECTED",
]
TraceStage = Literal[
    "A1_CAPTURE",
    "A2_RECONNECT",
    "A3_REUSE",
    "A4_DURABILITY",
    "A5_CONFIRMATION",
    "A6_REVIEW",
]
RepairAction = Literal[
    "NONE",
    "NOTE_EDIT",
    "EVIDENCE_MANUFACTURE",
    "RECEIPT_REWRITE",
    "LEDGER_REWRITE",
    "EVENT_ID_CHANGE",
    "TIMESTAMP_CHANGE",
    "EVIDENCE_DELETION",
    "RETRY_REPLACEMENT",
]

_TRACE_STAGES: tuple[TraceStage, ...] = (
    "A1_CAPTURE",
    "A2_RECONNECT",
    "A3_REUSE",
    "A4_DURABILITY",
    "A5_CONFIRMATION",
    "A6_REVIEW",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_REPOSITORY_RE = re.compile(r"^repo:v1:[0-9a-f]{64}$")


class FieldNoteWholeFlowError(RuntimeError):
    """Base error for an invalid A7 contract operation."""


class FieldNoteWholeFlowValidationError(FieldNoteWholeFlowError, ValueError):
    """A top-level A7 value is malformed rather than incomplete evidence."""


def _bounded_text(value: Any, label: str, *, maximum: int = 256) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or "\x00" in value
    ):
        raise FieldNoteWholeFlowValidationError(
            f"{label} is outside its bounded schema."
        )
    return value.strip()


def _parse_time(value: Any, label: str) -> tuple[str, datetime]:
    normalized = _bounded_text(value, label, maximum=64)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FieldNoteWholeFlowValidationError(
            f"{label} must be an RFC 3339 timestamp."
        ) from exc
    if parsed.tzinfo is None:
        raise FieldNoteWholeFlowValidationError(
            f"{label} must be timezone-aware."
        )
    return normalized, parsed


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: dict[str, Any]) -> str:
    return _sha256_bytes(canonical_json(value).encode("utf-8"))


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise FieldNoteWholeFlowValidationError(
            f"{label} must be a lowercase SHA-256 digest."
        )
    return value


def _runtime_as_dict(value: CodexRuntimeIdentity) -> dict[str, str]:
    return {
        "model": value.model,
        "reasoning_effort": value.reasoning_effort,
        "service_tier": value.service_tier,
        "codex_cli_version": value.codex_cli_version,
        "account_type": value.account_type,
    }


def _validate_runtime(value: Any) -> CodexRuntimeIdentity:
    if not isinstance(value, CodexRuntimeIdentity):
        raise FieldNoteWholeFlowValidationError(
            "Whole-Flow Run lacks a typed runtime identity."
        )
    for field, item in _runtime_as_dict(value).items():
        _bounded_text(item, f"Runtime {field}", maximum=128)
    return value


@dataclass(frozen=True)
class FieldNoteSourceRepositoryIdentity:
    """Credential-free repository identity plus one immutable source commit."""

    repository_id: str
    source_commit: str

    def __post_init__(self) -> None:
        if _REPOSITORY_RE.fullmatch(self.repository_id) is None:
            raise FieldNoteWholeFlowValidationError(
                "Source repository identity is invalid."
            )
        if _COMMIT_RE.fullmatch(self.source_commit) is None:
            raise FieldNoteWholeFlowValidationError(
                "Source repository commit is invalid."
            )

    def as_dict(self) -> dict[str, str]:
        return {
            "repository_id": self.repository_id,
            "source_commit": self.source_commit,
        }


@dataclass(frozen=True)
class FieldNoteWholeFlowAttempt:
    """Historical v0.1 or fixture identity with an explicit proof cutoff."""

    proof_attempt_id: str
    proof_mode: WholeFlowMode
    creator_id: str
    proof_as_of: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "proof_attempt_id",
            _bounded_text(self.proof_attempt_id, "Proof attempt ID"),
        )
        object.__setattr__(
            self,
            "creator_id",
            _bounded_text(self.creator_id, "Creator identity"),
        )
        if self.proof_mode not in {"FIXTURE", "CREATOR_LIVE"}:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow proof mode is invalid."
            )
        normalized, _ = _parse_time(self.proof_as_of, "Proof As-of")
        object.__setattr__(self, "proof_as_of", normalized)

    def as_dict(self) -> dict[str, str]:
        return {
            "proof_attempt_id": self.proof_attempt_id,
            "proof_mode": self.proof_mode,
            "creator_id": self.creator_id,
            "proof_as_of": self.proof_as_of,
        }


@dataclass(frozen=True)
class FieldNoteCreatorLiveAttempt:
    """Forward-only creator-live identity carrying authorization evidence."""

    proof_attempt_id: str
    proof_mode: Literal["CREATOR_LIVE"]
    creator_id: str
    authorization_observed_at: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "proof_attempt_id",
            _bounded_text(self.proof_attempt_id, "Proof attempt ID"),
        )
        object.__setattr__(
            self,
            "creator_id",
            _bounded_text(self.creator_id, "Creator identity"),
        )
        if self.proof_mode != "CREATOR_LIVE":
            raise FieldNoteWholeFlowValidationError(
                "Creator-live attempt mode is invalid."
            )
        normalized, _ = _parse_time(
            self.authorization_observed_at,
            "Authorization observation",
        )
        object.__setattr__(
            self,
            "authorization_observed_at",
            normalized,
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "proof_attempt_id": self.proof_attempt_id,
            "proof_mode": self.proof_mode,
            "creator_id": self.creator_id,
            "authorization_observed_at": self.authorization_observed_at,
        }


@dataclass(frozen=True)
class FieldNoteWholeFlowRunIdentity:
    """One fresh Run bound to the proof, repository, and exact runtime."""

    proof_attempt_id: str
    run_id: str
    started_at: str
    repository: FieldNoteSourceRepositoryIdentity
    runtime: CodexRuntimeIdentity

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "proof_attempt_id",
            _bounded_text(self.proof_attempt_id, "Proof attempt ID"),
        )
        object.__setattr__(
            self,
            "run_id",
            _bounded_text(self.run_id, "Run ID"),
        )
        normalized, _ = _parse_time(self.started_at, "Run start time")
        object.__setattr__(self, "started_at", normalized)
        if not isinstance(self.repository, FieldNoteSourceRepositoryIdentity):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow Run lacks a typed repository identity."
            )
        _validate_runtime(self.runtime)

    def as_dict(self) -> dict[str, Any]:
        return {
            "proof_attempt_id": self.proof_attempt_id,
            "run_id": self.run_id,
            "started_at": self.started_at,
            "repository": self.repository.as_dict(),
            "runtime": _runtime_as_dict(self.runtime),
        }


_RUNTIME_PROVENANCE_AUTHORITY = object()


@dataclass(frozen=True, init=False)
class FieldNoteCreatorLiveRuntimeProvenance:
    """In-process runtime capability identity, not external attestation.

    Normal construction is deliberately unavailable. The creator-live runtime
    issues this value while opening its append-only journal. Its identity proves
    only that this repository's runtime path produced the typed projection and
    later verified the same durable bytes; it is neither a signature nor an
    independent cryptographic attestation against a hostile local process.
    """

    schema: Literal[
        "decision-os.field-note-creator-live-runtime-provenance.v0.1"
    ]
    proof_attempt_id: str
    source_repository: FieldNoteSourceRepositoryIdentity
    runtime: CodexRuntimeIdentity
    issued_for_run_1_id: str
    trust_boundary: Literal[
        "IN_PROCESS_RUNTIME_CAPABILITY_WITH_DURABLE_READ_BACK"
    ]
    runtime_provenance_id: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise FieldNoteWholeFlowValidationError(
            "Creator-live runtime provenance cannot be caller-constructed."
        )

    @classmethod
    def _issue(
        cls,
        *,
        authority: object,
        proof_attempt_id: str,
        source_repository: FieldNoteSourceRepositoryIdentity,
        runtime: CodexRuntimeIdentity,
        issued_for_run_1_id: str,
    ) -> FieldNoteCreatorLiveRuntimeProvenance:
        if authority is not _RUNTIME_PROVENANCE_AUTHORITY:
            raise FieldNoteWholeFlowValidationError(
                "Creator-live runtime provenance authority is invalid."
            )
        attempt_id = _bounded_text(proof_attempt_id, "Proof attempt ID")
        run_id = _bounded_text(issued_for_run_1_id, "Run 1 ID")
        if not isinstance(source_repository, FieldNoteSourceRepositoryIdentity):
            raise FieldNoteWholeFlowValidationError(
                "Runtime provenance repository identity is invalid."
            )
        _validate_runtime(runtime)
        trust_boundary = (
            "IN_PROCESS_RUNTIME_CAPABILITY_WITH_DURABLE_READ_BACK"
        )
        body = {
            "schema": CREATOR_LIVE_PROVENANCE_SCHEMA,
            "proof_attempt_id": attempt_id,
            "source_repository": source_repository.as_dict(),
            "runtime": _runtime_as_dict(runtime),
            "issued_for_run_1_id": run_id,
            "trust_boundary": trust_boundary,
        }
        value = object.__new__(cls)
        object.__setattr__(value, "schema", CREATOR_LIVE_PROVENANCE_SCHEMA)
        object.__setattr__(value, "proof_attempt_id", attempt_id)
        object.__setattr__(value, "source_repository", source_repository)
        object.__setattr__(value, "runtime", runtime)
        object.__setattr__(value, "issued_for_run_1_id", run_id)
        object.__setattr__(value, "trust_boundary", trust_boundary)
        object.__setattr__(
            value,
            "runtime_provenance_id",
            _canonical_sha256(body),
        )
        return value

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "proof_attempt_id": self.proof_attempt_id,
            "source_repository": self.source_repository.as_dict(),
            "runtime": _runtime_as_dict(self.runtime),
            "issued_for_run_1_id": self.issued_for_run_1_id,
            "trust_boundary": self.trust_boundary,
            "runtime_provenance_id": self.runtime_provenance_id,
        }


@dataclass(frozen=True)
class FieldNoteWholeFlowTraceEvent:
    """One runtime checkpoint in the bounded, exact-evidence proof chain."""

    sequence: int
    stage: TraceStage
    run_id: str
    observed_at: str
    evidence_sha256: str
    previous_trace_sha256: str
    repair_action: RepairAction = "NONE"
    emitter: Literal["COMPANION_RUNTIME"] = "COMPANION_RUNTIME"
    proof_attempt_id: str | None = None
    runtime: CodexRuntimeIdentity | None = None
    source_repository: FieldNoteSourceRepositoryIdentity | None = None
    runtime_provenance: FieldNoteCreatorLiveRuntimeProvenance | None = None

    def __post_init__(self) -> None:
        if type(self.sequence) is not int or self.sequence < 0:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow trace sequence is invalid."
            )
        if self.stage not in _TRACE_STAGES:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow trace stage is invalid."
            )
        object.__setattr__(self, "run_id", _bounded_text(self.run_id, "Run ID"))
        normalized, _ = _parse_time(self.observed_at, "Trace observation time")
        object.__setattr__(self, "observed_at", normalized)
        _require_sha256(self.evidence_sha256, "Trace evidence identity")
        _require_sha256(self.previous_trace_sha256, "Previous trace identity")
        if self.repair_action not in {
            "NONE",
            "NOTE_EDIT",
            "EVIDENCE_MANUFACTURE",
            "RECEIPT_REWRITE",
            "LEDGER_REWRITE",
            "EVENT_ID_CHANGE",
            "TIMESTAMP_CHANGE",
            "EVIDENCE_DELETION",
            "RETRY_REPLACEMENT",
        }:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow repair action is invalid."
            )
        if self.emitter != "COMPANION_RUNTIME":
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow trace emitter is invalid."
            )
        live_values = (
            self.proof_attempt_id,
            self.runtime,
            self.source_repository,
            self.runtime_provenance,
        )
        if self.runtime_provenance is None:
            if any(value is not None for value in live_values[:-1]):
                raise FieldNoteWholeFlowValidationError(
                    "Fixture trace contains incomplete runtime provenance."
                )
            return
        if (
            not isinstance(
                self.runtime_provenance,
                FieldNoteCreatorLiveRuntimeProvenance,
            )
            or self.proof_attempt_id is None
            or self.runtime is None
            or self.source_repository is None
        ):
            raise FieldNoteWholeFlowValidationError(
                "Creator-live trace lacks typed runtime provenance."
            )
        _bounded_text(self.proof_attempt_id, "Proof attempt ID")
        _validate_runtime(self.runtime)
        if not isinstance(
            self.source_repository,
            FieldNoteSourceRepositoryIdentity,
        ):
            raise FieldNoteWholeFlowValidationError(
                "Creator-live trace repository identity is invalid."
            )
        provenance = self.runtime_provenance
        if (
            provenance.proof_attempt_id != self.proof_attempt_id
            or provenance.source_repository != self.source_repository
            or provenance.runtime != self.runtime
        ):
            raise FieldNoteWholeFlowValidationError(
                "Creator-live trace provenance is cross-bound."
            )

    @property
    def trace_sha256(self) -> str:
        return _canonical_sha256(self._body())

    def _body(self) -> dict[str, Any]:
        body = {
            "schema": WHOLE_FLOW_TRACE_SCHEMA,
            "sequence": self.sequence,
            "stage": self.stage,
            "run_id": self.run_id,
            "observed_at": self.observed_at,
            "evidence_sha256": self.evidence_sha256,
            "previous_trace_sha256": self.previous_trace_sha256,
            "repair_action": self.repair_action,
            "emitter": self.emitter,
        }
        if self.runtime_provenance is not None:
            assert self.proof_attempt_id is not None
            assert self.runtime is not None
            assert self.source_repository is not None
            body.update(
                {
                    "proof_attempt_id": self.proof_attempt_id,
                    "runtime": _runtime_as_dict(self.runtime),
                    "source_repository": self.source_repository.as_dict(),
                    "runtime_provenance": self.runtime_provenance.as_dict(),
                }
            )
        return body

    def as_dict(self) -> dict[str, Any]:
        return {**self._body(), "trace_sha256": self.trace_sha256}


@dataclass(frozen=True)
class FieldNoteWholeFlowEvidenceBundle:
    """Existing A1-A6 values plus the smallest typed no-repair trace."""

    attempt: FieldNoteWholeFlowAttempt | FieldNoteCreatorLiveAttempt
    source_repository: FieldNoteSourceRepositoryIdentity
    run_1: FieldNoteWholeFlowRunIdentity
    run_2: FieldNoteWholeFlowRunIdentity
    note: FieldNoteIdentity
    note_bytes: bytes
    a1_capture: FieldNoteDraft | None
    a2_reconnect: FieldNoteReconnectReceipt | None
    a3_assessment: FieldNoteReuseReceipt | None
    a4_snapshot: FieldNoteMaturityLedgerSnapshot | None
    a5_commit: FieldNoteMaturityCommitResult | None
    a6_review: FieldNoteMaturityReviewPacket | None
    proof_trace: tuple[FieldNoteWholeFlowTraceEvent, ...]
    creator_live_readback: FieldNoteCreatorLiveTraceReadback | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.attempt,
            (FieldNoteWholeFlowAttempt, FieldNoteCreatorLiveAttempt),
        ):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow bundle lacks a typed proof attempt."
            )
        required = (
            (
                self.source_repository,
                FieldNoteSourceRepositoryIdentity,
                "source repository",
            ),
            (self.run_1, FieldNoteWholeFlowRunIdentity, "Run 1"),
            (self.run_2, FieldNoteWholeFlowRunIdentity, "Run 2"),
            (self.note, FieldNoteIdentity, "Field Note identity"),
        )
        for value, expected, label in required:
            if not isinstance(value, expected):
                raise FieldNoteWholeFlowValidationError(
                    f"Whole-Flow bundle lacks a typed {label}."
                )
        if not isinstance(self.note_bytes, bytes):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow Note bytes must be bytes."
            )
        optional = (
            (self.a1_capture, FieldNoteDraft, "A1 capture"),
            (self.a2_reconnect, FieldNoteReconnectReceipt, "A2 receipt"),
            (self.a3_assessment, FieldNoteReuseReceipt, "A3 assessment"),
            (self.a4_snapshot, FieldNoteMaturityLedgerSnapshot, "A4 snapshot"),
            (self.a5_commit, FieldNoteMaturityCommitResult, "A5 result"),
            (self.a6_review, FieldNoteMaturityReviewPacket, "A6 packet"),
        )
        for value, expected, label in optional:
            if value is not None and not isinstance(value, expected):
                raise FieldNoteWholeFlowValidationError(
                    f"Whole-Flow bundle has an untyped {label}."
                )
        if not isinstance(self.proof_trace, tuple) or any(
            not isinstance(item, FieldNoteWholeFlowTraceEvent)
            for item in self.proof_trace
        ):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow proof trace is not typed."
            )
        if self.creator_live_readback is not None:
            from decision_os.companion.field_notes_creator_live import (
                FieldNoteCreatorLiveTraceReadback,
            )

            if not isinstance(
                self.creator_live_readback,
                FieldNoteCreatorLiveTraceReadback,
            ):
                raise FieldNoteWholeFlowValidationError(
                    "Creator-live durable read-back is not typed."
                )
        if (
            self.attempt.proof_mode == "FIXTURE"
            and self.creator_live_readback is not None
        ):
            raise FieldNoteWholeFlowValidationError(
                "FIXTURE evidence cannot attach creator-live read-back."
            )


@dataclass(frozen=True)
class FieldNoteOutcomeSummary:
    helpful: int
    not_helpful: int
    harmful: int
    unknown: int

    def __post_init__(self) -> None:
        values = (self.helpful, self.not_helpful, self.harmful, self.unknown)
        if any(type(value) is not int or value < 0 for value in values):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow outcome summary is invalid."
            )

    def as_dict(self) -> dict[str, int]:
        return {
            "helpful": self.helpful,
            "not_helpful": self.not_helpful,
            "harmful": self.harmful,
            "unknown": self.unknown,
        }


@dataclass(frozen=True)
class FieldNoteWholeFlowClaimBoundary:
    scope: Literal["ONE_CREATOR_ONE_REPOSITORY_ONE_MODEL_TWO_RUNS"] = (
        "ONE_CREATOR_ONE_REPOSITORY_ONE_MODEL_TWO_RUNS"
    )
    usefulness_separate: Literal[True] = True
    a2_authoritative_for_maturity: Literal[False] = False
    promotable_policy: Literal["UNSET"] = "UNSET"
    serving_policy: Literal["DELAY"] = "DELAY"
    automatic_injection_derived: Literal[False] = False
    portability_state: Literal["PORTABLE_CANDIDATE"] = "PORTABLE_CANDIDATE"
    portability_proven: Literal[False] = False
    creator_live_proof_inferred_from_fixture: Literal[False] = False

    def __post_init__(self) -> None:
        if self.as_dict() != {
            "scope": "ONE_CREATOR_ONE_REPOSITORY_ONE_MODEL_TWO_RUNS",
            "usefulness_separate": True,
            "a2_authoritative_for_maturity": False,
            "promotable_policy": "UNSET",
            "serving_policy": "DELAY",
            "automatic_injection_derived": False,
            "portability_state": "PORTABLE_CANDIDATE",
            "portability_proven": False,
            "creator_live_proof_inferred_from_fixture": False,
        }:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow claim boundary is invalid."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "usefulness_separate": self.usefulness_separate,
            "a2_authoritative_for_maturity": self.a2_authoritative_for_maturity,
            "promotable_policy": self.promotable_policy,
            "serving_policy": self.serving_policy,
            "automatic_injection_derived": self.automatic_injection_derived,
            "portability_state": self.portability_state,
            "portability_proven": self.portability_proven,
            "creator_live_proof_inferred_from_fixture": (
                self.creator_live_proof_inferred_from_fixture
            ),
        }


@dataclass(frozen=True)
class FieldNoteWholeFlowProofReceipt:
    """Deterministic bounded result of verifying one exact A1-A6 lineage."""

    schema: Literal[
        "decision-os.field-note-whole-flow-proof.v0.1",
        "decision-os.field-note-whole-flow-proof.v0.2",
    ]
    proof_attempt_id: str
    proof_mode: WholeFlowMode
    proof_as_of: str
    creator_id: str
    source_repository: FieldNoteSourceRepositoryIdentity
    source_runtime: CodexRuntimeIdentity
    run_1: FieldNoteWholeFlowRunIdentity
    run_2: FieldNoteWholeFlowRunIdentity
    note: FieldNoteIdentity
    note_byte_count: int
    reused_structure_id: str | None
    reused_structure_sha256: str | None
    reused_structure_binding_sha256: str | None
    a1_evidence_sha256: str | None
    a1_draft_sha256: str | None
    a1_capture_commit_sha256: str | None
    a2_receipt_sha256: str | None
    a3_reuse_event_id: str | None
    a3_receipt_sha256: str | None
    a4_partition_sha256: str | None
    a4_event_sha256: str | None
    a4_event_count: int | None
    a4_chain_head_sha256: str | None
    a4_snapshot_sha256: str | None
    a5_status: str | None
    a5_durable_commit_confirmed: bool | None
    a5_confirmation_sha256: str | None
    a6_packet_sha256: str | None
    a6_review_as_of: str | None
    maturity_state: str | None
    effective_outcome: str | None
    outcome_summary: FieldNoteOutcomeSummary | None
    human_intervention: str | None
    next_disposition: str | None
    proof_trace_schema: Literal[
        "decision-os.field-note-whole-flow-trace-event.v0.1"
    ]
    proof_trace_event_count: int
    proof_trace_chain_head_sha256: str | None
    proof_trace: tuple[FieldNoteWholeFlowTraceEvent, ...]
    creator_live_readback: FieldNoteCreatorLiveTraceReadback | None
    human_repair_result: HumanRepairResult
    state: WholeFlowState
    failed_boundary: WholeFlowBoundary | None
    failure_reason: str | None
    claim_boundary: FieldNoteWholeFlowClaimBoundary

    def __post_init__(self) -> None:
        if self.schema not in {WHOLE_FLOW_SCHEMA, WHOLE_FLOW_SCHEMA_V2}:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow receipt schema is unsupported."
            )
        _bounded_text(self.proof_attempt_id, "Proof attempt ID")
        _bounded_text(self.creator_id, "Creator identity")
        _parse_time(self.proof_as_of, "Proof As-of")
        if self.proof_mode not in {"FIXTURE", "CREATOR_LIVE"}:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow proof mode is invalid."
            )
        if not isinstance(self.source_repository, FieldNoteSourceRepositoryIdentity):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow receipt repository identity is invalid."
            )
        _validate_runtime(self.source_runtime)
        if not isinstance(
            self.run_1,
            FieldNoteWholeFlowRunIdentity,
        ) or not isinstance(
            self.run_2,
            FieldNoteWholeFlowRunIdentity,
        ):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow receipt Run identity is invalid."
            )
        if not isinstance(self.note, FieldNoteIdentity):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow receipt Note identity is invalid."
            )
        if type(self.note_byte_count) is not int or self.note_byte_count <= 0:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow receipt Note byte count is invalid."
            )
        for value, label in (
            (self.reused_structure_sha256, "Reused structure identity"),
            (
                self.reused_structure_binding_sha256,
                "Reused structure binding identity",
            ),
            (self.a1_evidence_sha256, "A1 evidence identity"),
            (self.a1_draft_sha256, "A1 draft identity"),
            (
                self.a1_capture_commit_sha256,
                "A1 capture-commit identity",
            ),
            (self.a2_receipt_sha256, "A2 receipt identity"),
            (self.a3_reuse_event_id, "A3 reuse event identity"),
            (self.a3_receipt_sha256, "A3 complete receipt identity"),
            (self.a4_partition_sha256, "A4 partition identity"),
            (self.a4_event_sha256, "A4 event identity"),
            (self.a4_chain_head_sha256, "A4 chain-head identity"),
            (self.a4_snapshot_sha256, "A4 snapshot identity"),
            (self.a5_confirmation_sha256, "A5 confirmation identity"),
            (self.a6_packet_sha256, "A6 packet identity"),
            (
                self.proof_trace_chain_head_sha256,
                "Proof trace chain-head identity",
            ),
        ):
            if value is not None:
                _require_sha256(value, label)
        if self.a4_event_count is not None and (
            type(self.a4_event_count) is not int or self.a4_event_count < 0
        ):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow A4 event count is invalid."
            )
        if self.a5_durable_commit_confirmed is not None and type(
            self.a5_durable_commit_confirmed
        ) is not bool:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow A5 confirmation state is invalid."
            )
        if self.outcome_summary is not None and not isinstance(
            self.outcome_summary,
            FieldNoteOutcomeSummary,
        ):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow outcome summary is not typed."
            )
        if self.reused_structure_id is not None:
            _bounded_text(
                self.reused_structure_id,
                "Reused structure ID",
            )
        if self.a5_status is not None and self.a5_status not in {
            "NOT_REUSED",
            "RECORDED",
            "ALREADY_RECORDED",
        }:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow A5 status is invalid."
            )
        if self.failure_reason is not None:
            _bounded_text(
                self.failure_reason,
                "Whole-Flow failure reason",
            )
        if self.human_repair_result not in {
            "NOT_EVALUATED",
            "INCOMPLETE",
            "TYPED_TRACE_VERIFIED",
            "REPAIR_DETECTED",
        }:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow human-repair result is invalid."
            )
        self._validate_proof_trace_identity()
        if self.creator_live_readback is not None:
            from decision_os.companion.field_notes_creator_live import (
                FieldNoteCreatorLiveTraceReadback,
                FieldNoteCreatorLiveTraceReadbackV2,
            )

            if not isinstance(
                self.creator_live_readback,
                FieldNoteCreatorLiveTraceReadback,
            ):
                raise FieldNoteWholeFlowValidationError(
                    "Receipt creator-live durable read-back is not typed."
                )
            if self.schema == WHOLE_FLOW_SCHEMA_V2:
                if (
                    not isinstance(
                        self.creator_live_readback,
                        FieldNoteCreatorLiveTraceReadbackV2,
                    )
                    or self.creator_live_readback.state
                    not in {"FAILED", "TRACE_COMPLETE"}
                    or self.creator_live_readback.terminal_proof_as_of
                    != self.proof_as_of
                ):
                    raise FieldNoteWholeFlowValidationError(
                        "v0.2 receipt terminal cutoff is not runtime-bound."
                    )
            elif isinstance(
                self.creator_live_readback,
                FieldNoteCreatorLiveTraceReadbackV2,
            ):
                raise FieldNoteWholeFlowValidationError(
                    "v0.1 receipt cannot reinterpret v0.2 read-back."
                )
        if (
            self.proof_mode == "FIXTURE"
            and self.creator_live_readback is not None
        ):
            raise FieldNoteWholeFlowValidationError(
                "FIXTURE receipt cannot attach creator-live read-back."
            )
        if self.state not in {"NOT_READY", "PASS", "FAIL"}:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow proof state is invalid."
            )
        if self.failed_boundary is not None and self.failed_boundary not in {
            "RUNTIME_ENFORCEMENT",
            "A1_CAPTURE",
            "RUN_SEPARATION",
            "MODEL_IDENTITY",
            "REPOSITORY_IDENTITY",
            "A2_RECONNECT",
            "A3_REUSE",
            "A4_DURABILITY",
            "A5_CONFIRMATION",
            "A6_REVIEW",
            "HUMAN_REPAIR",
            "PROOF_AS_OF",
        }:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow failed boundary is invalid."
            )
        if (
            self.state == "PASS"
            and (self.failed_boundary is not None or self.failure_reason is not None)
        ) or (
            self.state != "PASS"
            and (self.failed_boundary is None or self.failure_reason is None)
        ):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow state and failed boundary disagree."
            )
        if self.state == "PASS":
            required = (
                self.reused_structure_id,
                self.reused_structure_sha256,
                self.reused_structure_binding_sha256,
                self.a1_evidence_sha256,
                self.a2_receipt_sha256,
                self.a3_reuse_event_id,
                self.a4_partition_sha256,
                self.a4_event_sha256,
                self.a4_event_count,
                self.a4_chain_head_sha256,
                self.a4_snapshot_sha256,
                self.a5_status,
                self.a5_durable_commit_confirmed,
                self.a5_confirmation_sha256,
                self.a6_packet_sha256,
                self.a6_review_as_of,
                self.maturity_state,
                self.effective_outcome,
                self.outcome_summary,
                self.human_intervention,
                self.next_disposition,
            )
            if (
                any(value is None for value in required)
                or (
                    self.proof_mode == "CREATOR_LIVE"
                    and (
                        self.a3_receipt_sha256 is None
                        or self.a1_draft_sha256 is None
                        or self.a1_capture_commit_sha256 is None
                    )
                )
                or self.a4_event_count != 1
                or self.a4_chain_head_sha256 != self.a4_event_sha256
                or self.a5_status not in {"RECORDED", "ALREADY_RECORDED"}
                or self.a5_durable_commit_confirmed is not True
                or self.maturity_state != "REUSED"
                or self.human_repair_result != "TYPED_TRACE_VERIFIED"
            ):
                raise FieldNoteWholeFlowValidationError(
                    "PASS receipt lacks complete fixed-scope evidence."
                )
            self._validate_complete_run_binding()
            self._validate_creator_live_admission()
        if (
            self.human_repair_result == "TYPED_TRACE_VERIFIED"
            and self.state != "PASS"
        ):
            raise FieldNoteWholeFlowValidationError(
                "Typed proof trace verification requires a PASS receipt."
            )
        if not isinstance(self.claim_boundary, FieldNoteWholeFlowClaimBoundary):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow receipt claim boundary is invalid."
            )

    @property
    def run_1_id(self) -> str:
        return self.run_1.run_id

    @property
    def run_2_id(self) -> str:
        return self.run_2.run_id

    def _validate_complete_run_binding(self) -> None:
        _, run_1_time = _parse_time(self.run_1.started_at, "Run 1 start time")
        _, run_2_time = _parse_time(self.run_2.started_at, "Run 2 start time")
        if (
            self.run_1.run_id == self.run_2.run_id
            or run_2_time <= run_1_time
            or self.run_1.proof_attempt_id != self.proof_attempt_id
            or self.run_2.proof_attempt_id != self.proof_attempt_id
            or self.run_1.repository != self.source_repository
            or self.run_2.repository != self.source_repository
            or self.run_1.runtime != self.source_runtime
            or self.run_2.runtime != self.source_runtime
        ):
            raise FieldNoteWholeFlowValidationError(
                "PASS receipt Run identities are not exactly cross-bound."
            )

    def _validate_creator_live_admission(self) -> None:
        if self.proof_mode == "FIXTURE":
            if any(
                event.runtime_provenance is not None
                for event in self.proof_trace
            ):
                raise FieldNoteWholeFlowValidationError(
                    "FIXTURE receipt contains creator-live provenance."
                )
            return
        readback = self.creator_live_readback
        if readback is None:
            raise FieldNoteWholeFlowValidationError(
                "CREATOR_LIVE PASS lacks durable runtime read-back."
            )
        if not readback.matches_admission(
            attempt=self.attempt,
            source_repository=self.source_repository,
            runtime=self.source_runtime,
            run_1=self.run_1,
            run_2=self.run_2,
            proof_trace=self.proof_trace,
        ):
            raise FieldNoteWholeFlowValidationError(
                "CREATOR_LIVE PASS durable runtime identity is invalid."
            )
        commit = readback.a1_capture_commit
        if (
            commit is None
            or not self.proof_trace
            or self.a1_evidence_sha256 != commit.receipt_sha256
            or self.a1_capture_commit_sha256 != commit.receipt_sha256
            or self.a1_draft_sha256 != commit.draft_evidence_sha256
            or commit.proof_attempt_id != self.proof_attempt_id
            or commit.run_id != self.run_1.run_id
            or commit.actual_runtime_identity != self.source_runtime
            or commit.source_repository != self.source_repository
            or commit.note != self.note
            or commit.note_byte_count != self.note_byte_count
            or self.proof_trace[0].evidence_sha256
            != commit.receipt_sha256
        ):
            raise FieldNoteWholeFlowValidationError(
                "CREATOR_LIVE PASS A1 capture commit is invalid."
            )
        _, run_time = _parse_time(self.run_1.started_at, "Run 1 start")
        _, draft_time = _parse_time(
            commit.draft_created_at,
            "A1 draft creation time",
        )
        _, save_time = _parse_time(commit.save_as_of, "A1 save As-of")
        _, observed_time = _parse_time(
            self.proof_trace[0].observed_at,
            "A1 checkpoint observation",
        )
        _, proof_time = _parse_time(self.proof_as_of, "Proof As-of")
        if not (
            run_time <= draft_time <= save_time <= observed_time <= proof_time
        ):
            raise FieldNoteWholeFlowValidationError(
                "CREATOR_LIVE PASS A1 chronology is invalid."
            )

    def _validate_proof_trace_identity(self) -> None:
        if self.proof_trace_schema != WHOLE_FLOW_TRACE_SCHEMA:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow receipt proof trace schema is unsupported."
            )
        if (
            not isinstance(self.proof_trace, tuple)
            or any(
                not isinstance(item, FieldNoteWholeFlowTraceEvent)
                for item in self.proof_trace
            )
            or type(self.proof_trace_event_count) is not int
            or self.proof_trace_event_count != len(self.proof_trace)
        ):
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow receipt proof trace count is invalid."
            )
        expected_head = (
            self.proof_trace[-1].trace_sha256 if self.proof_trace else None
        )
        if self.proof_trace_chain_head_sha256 != expected_head:
            raise FieldNoteWholeFlowValidationError(
                "Whole-Flow receipt proof trace head is invalid."
            )
        if self.human_repair_result != "TYPED_TRACE_VERIFIED":
            return
        expected_evidence = (
            self.a1_evidence_sha256,
            self.a2_receipt_sha256,
            (
                self.a3_receipt_sha256
                if self.proof_mode == "CREATOR_LIVE"
                else self.a3_reuse_event_id
            ),
            self.a4_event_sha256,
            self.a5_confirmation_sha256,
            self.a6_packet_sha256,
        )
        expected_runs = (
            self.run_1.run_id,
            self.run_2.run_id,
            self.run_2.run_id,
            self.run_2.run_id,
            self.run_2.run_id,
            self.run_2.run_id,
        )
        previous = TRACE_GENESIS_SHA256
        _, proof_time = _parse_time(self.proof_as_of, "Proof As-of")
        _, run_1_time = _parse_time(self.run_1.started_at, "Run 1 start time")
        _, run_2_time = _parse_time(self.run_2.started_at, "Run 2 start time")
        previous_time: datetime | None = None
        if self.proof_trace_event_count != len(_TRACE_STAGES) or any(
            evidence is None for evidence in expected_evidence
        ):
            raise FieldNoteWholeFlowValidationError(
                "Typed proof trace lacks its exact six-checkpoint identity."
            )
        for index, event in enumerate(self.proof_trace):
            _, event_time = _parse_time(
                event.observed_at,
                "Trace observation time",
            )
            minimum_time = run_1_time if index == 0 else run_2_time
            if (
                event.sequence != index
                or event.stage != _TRACE_STAGES[index]
                or event.run_id != expected_runs[index]
                or event.evidence_sha256 != expected_evidence[index]
                or event.previous_trace_sha256 != previous
                or event.repair_action != "NONE"
                or event_time < minimum_time
                or event_time > proof_time
                or (
                    previous_time is not None
                    and event_time < previous_time
                )
            ):
                raise FieldNoteWholeFlowValidationError(
                    "Typed proof trace identity is invalid."
                )
            previous = event.trace_sha256
            previous_time = event_time

    @property
    def attempt(self) -> FieldNoteWholeFlowAttempt | FieldNoteCreatorLiveAttempt:
        """Return the exact typed attempt identity preserved by this receipt."""

        if self.schema == WHOLE_FLOW_SCHEMA_V2:
            readback = self.creator_live_readback
            if readback is None or not isinstance(
                readback.attempt,
                FieldNoteCreatorLiveAttempt,
            ):
                raise FieldNoteWholeFlowValidationError(
                    "v0.2 receipt lacks its creator-live attempt identity."
                )
            return readback.attempt
        return FieldNoteWholeFlowAttempt(
            proof_attempt_id=self.proof_attempt_id,
            proof_mode=self.proof_mode,
            creator_id=self.creator_id,
            proof_as_of=self.proof_as_of,
        )

    def _body(self) -> dict[str, Any]:
        body = {
            "schema": self.schema,
            "proof_attempt_id": self.proof_attempt_id,
            "proof_mode": self.proof_mode,
            "proof_as_of": self.proof_as_of,
            "creator_id": self.creator_id,
            "source_repository": self.source_repository.as_dict(),
            "source_runtime": _runtime_as_dict(self.source_runtime),
            "run_1": self.run_1.as_dict(),
            "run_2": self.run_2.as_dict(),
            "note": self.note.as_dict(),
            "note_byte_count": self.note_byte_count,
            "reused_structure": {
                "structure_id": self.reused_structure_id,
                "structure_sha256": self.reused_structure_sha256,
                "binding_sha256": self.reused_structure_binding_sha256,
            },
            "a1_evidence_sha256": self.a1_evidence_sha256,
            "a2_receipt_sha256": self.a2_receipt_sha256,
            "a3_reuse_event_id": self.a3_reuse_event_id,
            "a4": {
                "partition_sha256": self.a4_partition_sha256,
                "event_sha256": self.a4_event_sha256,
                "event_count": self.a4_event_count,
                "chain_head_sha256": self.a4_chain_head_sha256,
                "snapshot_sha256": self.a4_snapshot_sha256,
            },
            "a5": {
                "status": self.a5_status,
                "durable_commit_confirmed": self.a5_durable_commit_confirmed,
                "confirmation_sha256": self.a5_confirmation_sha256,
            },
            "a6": {
                "packet_sha256": self.a6_packet_sha256,
                "review_as_of": self.a6_review_as_of,
            },
            "maturity_state": self.maturity_state,
            "effective_outcome": self.effective_outcome,
            "outcome_summary": (
                self.outcome_summary.as_dict()
                if self.outcome_summary is not None
                else None
            ),
            "human_intervention": self.human_intervention,
            "next_disposition": self.next_disposition,
            "proof_trace_schema": self.proof_trace_schema,
            "proof_trace_event_count": self.proof_trace_event_count,
            "proof_trace_chain_head_sha256": (
                self.proof_trace_chain_head_sha256
            ),
            "proof_trace": [event.as_dict() for event in self.proof_trace],
            "human_repair_result": self.human_repair_result,
            "state": self.state,
            "failed_boundary": self.failed_boundary,
            "failure_reason": self.failure_reason,
            "claim_boundary": self.claim_boundary.as_dict(),
        }
        if self.proof_mode == "CREATOR_LIVE":
            body["a1_draft_sha256"] = self.a1_draft_sha256
            body["a1_capture_commit_sha256"] = (
                self.a1_capture_commit_sha256
            )
            body["a3_receipt_sha256"] = self.a3_receipt_sha256
            body["creator_live_readback"] = (
                self.creator_live_readback.as_dict()
                if self.creator_live_readback is not None
                else None
            )
        return body

    @property
    def receipt_sha256(self) -> str:
        return _canonical_sha256(self._body())

    def as_dict(self) -> dict[str, Any]:
        return {**self._body(), "receipt_sha256": self.receipt_sha256}

    def serialize(self) -> str:
        return canonical_json(self.as_dict())

    def render_text(self) -> str:
        return "\n".join(
            (
                (
                    "Field Note Whole-Flow Proof Receipt v0.2"
                    if self.schema == WHOLE_FLOW_SCHEMA_V2
                    else "Field Note Whole-Flow Proof Receipt v0.1"
                ),
                f"State: {self.state}",
                f"Proof mode: {self.proof_mode}",
                f"Proof As-of: {self.proof_as_of}",
                f"Proof attempt: {self.proof_attempt_id}",
                f"Creator: {self.creator_id}",
                f"Run 1: {self.run_1_id}",
                f"Run 2: {self.run_2_id}",
                f"Proof trace events: {self.proof_trace_event_count}",
                (
                    "Proof trace head: "
                    f"{self.proof_trace_chain_head_sha256 or 'NONE'}"
                ),
                f"Field Note: {self.note.note_path}",
                f"Outcome: {self.effective_outcome or 'NOT_ESTABLISHED'}",
                f"Disposition: {self.next_disposition or 'NOT_ESTABLISHED'}",
                f"Failed boundary: {self.failed_boundary or 'NONE'}",
                "PROMOTABLE: UNSET",
                "Serving Policy: DELAY",
                "Authority: TOPMOST_CANONICAL > ADVISORY_FIELD_NOTE",
                f"Receipt SHA-256: {self.receipt_sha256}",
                "",
            )
        )


@dataclass(frozen=True)
class PortableCandidateClaimBoundary:
    portability_state: Literal["PORTABLE_CANDIDATE"] = "PORTABLE_CANDIDATE"
    portability_proven: Literal[False] = False
    cross_repository_import_verified: Literal[False] = False
    cross_model_reuse_verified: Literal[False] = False
    external_user_reuse_verified: Literal[False] = False
    source_evidence_immutable: Literal[True] = True
    future_evidence_scope: Literal["TARGET_REPOSITORY_LOCAL"] = (
        "TARGET_REPOSITORY_LOCAL"
    )
    explicit_import_receipt_required: Literal[True] = True
    shared_mutable_ledger: Literal[False] = False
    diverged_ledger_merge_supported: Literal[False] = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "portability_state": self.portability_state,
            "portability_proven": self.portability_proven,
            "cross_repository_import_verified": (
                self.cross_repository_import_verified
            ),
            "cross_model_reuse_verified": self.cross_model_reuse_verified,
            "external_user_reuse_verified": self.external_user_reuse_verified,
            "source_evidence_immutable": self.source_evidence_immutable,
            "future_evidence_scope": self.future_evidence_scope,
            "explicit_import_receipt_required": (
                self.explicit_import_receipt_required
            ),
            "shared_mutable_ledger": self.shared_mutable_ledger,
            "diverged_ledger_merge_supported": (
                self.diverged_ledger_merge_supported
            ),
        }


@dataclass(frozen=True, init=False)
class PortableCandidateWarehouseManifest:
    """Portable immutable label; future evidence remains repository-local."""

    proof_receipt: FieldNoteWholeFlowProofReceipt
    claim_boundary: PortableCandidateClaimBoundary = (
        PortableCandidateClaimBoundary()
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise FieldNoteWholeFlowValidationError(
            "Warehouse manifests must be built from a verified evidence bundle."
        )

    @classmethod
    def _from_verified_receipt(
        cls,
        receipt: FieldNoteWholeFlowProofReceipt,
    ) -> PortableCandidateWarehouseManifest:
        manifest = object.__new__(cls)
        object.__setattr__(manifest, "proof_receipt", receipt)
        object.__setattr__(
            manifest,
            "claim_boundary",
            PortableCandidateClaimBoundary(),
        )
        manifest._validate()
        return manifest

    def _validate(self) -> None:
        if (
            not isinstance(self.proof_receipt, FieldNoteWholeFlowProofReceipt)
            or self.proof_receipt.state != "PASS"
        ):
            raise FieldNoteWholeFlowValidationError(
                "Warehouse manifest requires one verified PASS receipt."
            )
        if not isinstance(self.claim_boundary, PortableCandidateClaimBoundary):
            raise FieldNoteWholeFlowValidationError(
                "Warehouse portability claim boundary is invalid."
            )
        if self.claim_boundary.as_dict() != PortableCandidateClaimBoundary().as_dict():
            raise FieldNoteWholeFlowValidationError(
                "Warehouse portability claim boundary was widened."
            )

    @property
    def portable_asset_id(self) -> str:
        receipt = self.proof_receipt
        return _canonical_sha256(
            {
                "schema": PORTABLE_ASSET_SCHEMA,
                "note": receipt.note.as_dict(),
                "note_byte_count": receipt.note_byte_count,
                "origin_run_id": receipt.note.origin_run_id,
                "source_repository": receipt.source_repository.as_dict(),
                "source_runtime": _runtime_as_dict(receipt.source_runtime),
            }
        )

    def _body(self) -> dict[str, Any]:
        receipt = self.proof_receipt
        if receipt.outcome_summary is None:
            raise FieldNoteWholeFlowValidationError(
                "Warehouse manifest lacks a bounded outcome summary."
            )
        return {
            "schema": WAREHOUSE_MANIFEST_SCHEMA,
            "portable_asset_id": self.portable_asset_id,
            "source_note": receipt.note.as_dict(),
            "note_sha256": receipt.note.note_sha256,
            "note_byte_count": receipt.note_byte_count,
            "origin_run_id": receipt.note.origin_run_id,
            "source_repository": receipt.source_repository.as_dict(),
            "source_runtime": _runtime_as_dict(receipt.source_runtime),
            "whole_flow_proof_receipt_sha256": receipt.receipt_sha256,
            "proof_mode": receipt.proof_mode,
            "proof_trace": {
                "schema": receipt.proof_trace_schema,
                "event_count": receipt.proof_trace_event_count,
                "chain_head_sha256": receipt.proof_trace_chain_head_sha256,
            },
            "a4_evidence_snapshot_sha256": receipt.a4_snapshot_sha256,
            "a6_review_packet_sha256": receipt.a6_packet_sha256,
            "coverage_evidence_mode": receipt.proof_mode,
            "creator_live_coverage_verified": (
                receipt.proof_mode == "CREATOR_LIVE"
            ),
            "verified_coverage": {
                "repositories": 1,
                "model_identities": 1,
                "verified_later_reuse_runs": 1,
            },
            "maturity_state": receipt.maturity_state,
            "outcome_summary": receipt.outcome_summary.as_dict(),
            "effective_outcome": receipt.effective_outcome,
            "human_intervention": receipt.human_intervention,
            "next_disposition": receipt.next_disposition,
            "promotable_policy": "UNSET",
            "serving_policy": "DELAY",
            "automatic_injection": None,
            "authority_precedence": [
                "TOPMOST_CANONICAL",
                "ADVISORY_FIELD_NOTE",
            ],
            "claim_boundary": self.claim_boundary.as_dict(),
            "future_evidence_extension": (
                "TARGET_LOCAL_LEDGER_WITH_EXPLICIT_IMPORT_REQUIRED"
            ),
        }

    @property
    def manifest_id(self) -> str:
        return _canonical_sha256(self._body())

    def as_dict(self) -> dict[str, Any]:
        return {**self._body(), "manifest_id": self.manifest_id}

    def serialize(self) -> str:
        return canonical_json(self.as_dict())

    def render_text(self) -> str:
        mode = self.proof_receipt.proof_mode
        coverage_label = (
            "Fixture-covered" if mode == "FIXTURE" else "Creator-live-covered"
        )
        return "\n".join(
            (
                "Portable Candidate Warehouse Manifest v0.1",
                "State: PORTABLE_CANDIDATE",
                f"Asset: {self.portable_asset_id}",
                f"Field Note: {self.proof_receipt.note.note_path}",
                f"Coverage evidence mode: {mode}",
                (
                    "Creator-live coverage verified: "
                    f"{'true' if mode == 'CREATOR_LIVE' else 'false'}"
                ),
                f"{coverage_label} repositories: 1",
                f"{coverage_label} model identities: 1",
                f"{coverage_label} later reuse Runs: 1",
                (
                    "Proof trace head: "
                    f"{self.proof_receipt.proof_trace_chain_head_sha256}"
                ),
                "PROMOTABLE: UNSET",
                "Serving Policy: DELAY",
                "Portability proven: false",
                "Future evidence: target-repository-local with explicit import",
                f"Manifest SHA-256: {self.manifest_id}",
                "",
            )
        )


def _a1_evidence_sha256(draft: FieldNoteDraft) -> str:
    return _canonical_sha256(
        {
            "schema": FIELD_NOTE_SCHEMA_VERSION,
            "title": draft.title,
            "value_level": draft.value_level,
            "source_model_class": draft.source_model_class,
            "target_model_class": draft.target_model_class,
            "source_run_id": draft.source_run_id,
            "created_at": draft.created_at,
            "field_note_id": draft.field_note_id,
            "relative_path": draft.relative_path,
            "note_sha256": draft.sha256,
            "note_byte_count": len(draft.markdown),
        }
    )


def _a2_receipt_sha256(receipt: FieldNoteReconnectReceipt) -> str:
    return _canonical_sha256(receipt.as_dict())


def _a3_receipt_sha256(receipt: FieldNoteReuseReceipt) -> str:
    return _canonical_sha256(receipt.as_dict())


def _a5_confirmation_sha256(result: FieldNoteMaturityCommitResult) -> str:
    return _canonical_sha256(result.as_dict())


def _a6_packet_sha256(packet: FieldNoteMaturityReviewPacket) -> str:
    return _sha256_bytes(packet.serialize().encode("utf-8"))


def _event_receipt_sha256(event: FieldNoteMaturityLedgerEvent) -> str:
    return _canonical_sha256(event.receipt.as_dict())


def _event_sha256(event: FieldNoteMaturityLedgerEvent) -> str:
    body = {
        "schema": LEDGER_EVENT_SCHEMA,
        "event_kind": LEDGER_EVENT_KIND,
        "sequence": event.sequence,
        "recorded_at": event.recorded_at,
        "note_partition_sha256": event.note_partition_sha256,
        "previous_event_sha256": event.previous_event_sha256,
        "event_id": event.event_id,
        "receipt": event.receipt.as_dict(),
        "receipt_sha256": event.receipt_sha256,
    }
    return _canonical_sha256(body)


def _expected_reuse_event_id(receipt: FieldNoteReuseReceipt) -> str:
    if receipt.use_evidence is None:
        return ""
    return _canonical_sha256(
        {
            "note": receipt.note.as_dict(),
            "reusing_run_id": receipt.reusing_run_id,
            "use_evidence": receipt.use_evidence.as_dict(),
        }
    )


def _outcome_summary(packet: FieldNoteMaturityReviewPacket) -> FieldNoteOutcomeSummary:
    signals = packet.aggregate_evidence_signals
    return FieldNoteOutcomeSummary(
        helpful=signals.helpful_outcomes,
        not_helpful=signals.not_helpful_outcomes,
        harmful=signals.harmful_outcomes,
        unknown=signals.unknown_outcomes,
    )


def _bundle_proof_as_of(bundle: FieldNoteWholeFlowEvidenceBundle) -> str:
    if isinstance(bundle.attempt, FieldNoteCreatorLiveAttempt):
        readback = bundle.creator_live_readback
        terminal = (
            getattr(readback, "terminal_proof_as_of", None)
            if readback is not None
            else None
        )
        if terminal is None:
            raise FieldNoteWholeFlowValidationError(
                "Forward-only creator-live proof is not terminal."
            )
        return _parse_time(terminal, "Terminal Proof As-of")[0]
    return bundle.attempt.proof_as_of


def _receipt(
    bundle: FieldNoteWholeFlowEvidenceBundle,
    *,
    state: WholeFlowState,
    failed_boundary: WholeFlowBoundary | None,
    failure_reason: str | None,
    human_repair_result: HumanRepairResult = "NOT_EVALUATED",
) -> FieldNoteWholeFlowProofReceipt:
    a1 = bundle.a1_capture
    a2 = bundle.a2_reconnect
    a3 = bundle.a3_assessment
    a4 = bundle.a4_snapshot
    a5 = bundle.a5_commit
    a6 = bundle.a6_review
    binding = a3.use_evidence.structure_binding if (
        a3 is not None and a3.use_evidence is not None
    ) else None
    first_event = a4.events[0] if a4 is not None and a4.events else None
    a1_capture_commit = (
        bundle.creator_live_readback.a1_capture_commit
        if bundle.attempt.proof_mode == "CREATOR_LIVE"
        and bundle.creator_live_readback is not None
        else None
    )
    a1_draft_sha256 = _a1_evidence_sha256(a1) if a1 else None
    return FieldNoteWholeFlowProofReceipt(
        schema=(
            WHOLE_FLOW_SCHEMA_V2
            if isinstance(bundle.attempt, FieldNoteCreatorLiveAttempt)
            else WHOLE_FLOW_SCHEMA
        ),
        proof_attempt_id=bundle.attempt.proof_attempt_id,
        proof_mode=bundle.attempt.proof_mode,
        proof_as_of=_bundle_proof_as_of(bundle),
        creator_id=bundle.attempt.creator_id,
        source_repository=bundle.source_repository,
        source_runtime=bundle.run_1.runtime,
        run_1=bundle.run_1,
        run_2=bundle.run_2,
        note=bundle.note,
        note_byte_count=len(bundle.note_bytes),
        reused_structure_id=binding.structure_id if binding else None,
        reused_structure_sha256=binding.structure_sha256 if binding else None,
        reused_structure_binding_sha256=(
            binding.binding_sha256 if binding else None
        ),
        a1_evidence_sha256=(
            a1_capture_commit.receipt_sha256
            if a1_capture_commit is not None
            else (
                a1_draft_sha256
                if bundle.attempt.proof_mode == "FIXTURE"
                else None
            )
        ),
        a1_draft_sha256=(
            a1_draft_sha256
            if bundle.attempt.proof_mode == "CREATOR_LIVE"
            else None
        ),
        a1_capture_commit_sha256=(
            a1_capture_commit.receipt_sha256
            if a1_capture_commit is not None
            else None
        ),
        a2_receipt_sha256=_a2_receipt_sha256(a2) if a2 else None,
        a3_reuse_event_id=a3.reuse_event_id if a3 else None,
        a3_receipt_sha256=(
            _a3_receipt_sha256(a3)
            if a3 is not None and bundle.attempt.proof_mode == "CREATOR_LIVE"
            else None
        ),
        a4_partition_sha256=(
            first_event.note_partition_sha256 if first_event else None
        ),
        a4_event_sha256=first_event.event_sha256 if first_event else None,
        a4_event_count=len(a4.events) if a4 else None,
        a4_chain_head_sha256=a4.chain_head_sha256 if a4 else None,
        a4_snapshot_sha256=(
            _canonical_sha256(a4.as_dict()) if a4 else None
        ),
        a5_status=a5.status if a5 else None,
        a5_durable_commit_confirmed=(
            a5.durable_commit_confirmed if a5 else None
        ),
        a5_confirmation_sha256=(
            _a5_confirmation_sha256(a5) if a5 else None
        ),
        a6_packet_sha256=_a6_packet_sha256(a6) if a6 else None,
        a6_review_as_of=a6.review_as_of if a6 else None,
        maturity_state=a6.evidence_maturity.state if a6 else None,
        effective_outcome=a3.outcome if a3 else None,
        outcome_summary=_outcome_summary(a6) if a6 else None,
        human_intervention=a3.human_intervention if a3 else None,
        next_disposition=a3.next_action if a3 else None,
        proof_trace_schema=WHOLE_FLOW_TRACE_SCHEMA,
        proof_trace_event_count=len(bundle.proof_trace),
        proof_trace_chain_head_sha256=(
            bundle.proof_trace[-1].trace_sha256
            if bundle.proof_trace
            else None
        ),
        proof_trace=bundle.proof_trace,
        creator_live_readback=bundle.creator_live_readback,
        human_repair_result=human_repair_result,
        state=state,
        failed_boundary=failed_boundary,
        failure_reason=failure_reason,
        claim_boundary=FieldNoteWholeFlowClaimBoundary(),
    )


def _not_ready(
    bundle: FieldNoteWholeFlowEvidenceBundle,
    boundary: WholeFlowBoundary,
    reason: str,
) -> FieldNoteWholeFlowProofReceipt:
    return _receipt(
        bundle,
        state="NOT_READY",
        failed_boundary=boundary,
        failure_reason=reason,
        human_repair_result=(
            "INCOMPLETE" if boundary == "HUMAN_REPAIR" else "NOT_EVALUATED"
        ),
    )


def _fail(
    bundle: FieldNoteWholeFlowEvidenceBundle,
    boundary: WholeFlowBoundary,
    reason: str,
    *,
    human_repair_result: HumanRepairResult = "NOT_EVALUATED",
) -> FieldNoteWholeFlowProofReceipt:
    return _receipt(
        bundle,
        state="FAIL",
        failed_boundary=boundary,
        failure_reason=reason,
        human_repair_result=human_repair_result,
    )


def verify_field_note_whole_flow(
    bundle: FieldNoteWholeFlowEvidenceBundle,
) -> FieldNoteWholeFlowProofReceipt:
    """Verify one fixed A1-A6 lineage without writing, retrying, or repairing."""

    if not isinstance(bundle, FieldNoteWholeFlowEvidenceBundle):
        raise FieldNoteWholeFlowValidationError(
            "Whole-Flow verifier requires a typed evidence bundle."
        )
    if bundle.attempt.proof_mode == "CREATOR_LIVE":
        readback = bundle.creator_live_readback
        if readback is None:
            return _not_ready(
                bundle,
                "RUNTIME_ENFORCEMENT",
                "CREATOR_LIVE_RUNTIME_EVIDENCE_MISSING",
            )
        if readback.state == "FAILED" or not readback.durable_readback_verified:
            return _fail(
                bundle,
                readback.failure_boundary or "RUNTIME_ENFORCEMENT",
                readback.failure_reason or "CREATOR_LIVE_DURABLE_READ_BACK_FAILED",
                human_repair_result=(
                    "REPAIR_DETECTED"
                    if readback.repair_action != "NONE"
                    else "NOT_EVALUATED"
                ),
            )
        if readback.state != "TRACE_COMPLETE":
            return _not_ready(
                bundle,
                "RUNTIME_ENFORCEMENT",
                "CREATOR_LIVE_TRACE_INCOMPLETE",
            )
        if not readback.matches_admission(
            attempt=bundle.attempt,
            source_repository=bundle.source_repository,
            runtime=bundle.run_1.runtime,
            run_1=bundle.run_1,
            run_2=bundle.run_2,
            proof_trace=bundle.proof_trace,
        ):
            return _fail(
                bundle,
                "RUNTIME_ENFORCEMENT",
                "CREATOR_LIVE_RUNTIME_IDENTITY_MISMATCH",
            )
    for value, boundary, reason in (
        (bundle.a1_capture, "A1_CAPTURE", "A1_EVIDENCE_MISSING"),
        (bundle.a2_reconnect, "A2_RECONNECT", "A2_EVIDENCE_MISSING"),
        (bundle.a3_assessment, "A3_REUSE", "A3_EVIDENCE_MISSING"),
        (bundle.a4_snapshot, "A4_DURABILITY", "A4_EVIDENCE_MISSING"),
        (bundle.a5_commit, "A5_CONFIRMATION", "A5_EVIDENCE_MISSING"),
        (bundle.a6_review, "A6_REVIEW", "A6_EVIDENCE_MISSING"),
    ):
        if value is None:
            return _not_ready(bundle, boundary, reason)  # type: ignore[arg-type]
    if len(bundle.proof_trace) < len(_TRACE_STAGES):
        return _not_ready(
            bundle,
            "HUMAN_REPAIR",
            "TYPED_PROOF_TRACE_INCOMPLETE",
        )

    assert bundle.a1_capture is not None
    assert bundle.a2_reconnect is not None
    assert bundle.a3_assessment is not None
    assert bundle.a4_snapshot is not None
    assert bundle.a5_commit is not None
    assert bundle.a6_review is not None
    a1 = bundle.a1_capture
    a2 = bundle.a2_reconnect
    a3 = bundle.a3_assessment
    a4 = bundle.a4_snapshot
    a5 = bundle.a5_commit
    a6 = bundle.a6_review

    if (
        bundle.run_1.proof_attempt_id != bundle.attempt.proof_attempt_id
        or bundle.run_2.proof_attempt_id != bundle.attempt.proof_attempt_id
    ):
        return _fail(bundle, "RUN_SEPARATION", "RUN_ATTEMPT_MISMATCH")
    if bundle.run_1.run_id == bundle.run_2.run_id:
        return _fail(bundle, "RUN_SEPARATION", "RUN_IDENTITIES_NOT_DISTINCT")
    _, run_1_time = _parse_time(bundle.run_1.started_at, "Run 1 start")
    _, run_2_time = _parse_time(bundle.run_2.started_at, "Run 2 start")
    if run_2_time <= run_1_time:
        return _fail(bundle, "RUN_SEPARATION", "RUN_ORDER_INVALID")
    if bundle.run_1.runtime != bundle.run_2.runtime:
        return _fail(bundle, "MODEL_IDENTITY", "MODEL_RUNTIME_MISMATCH")
    if (
        bundle.run_1.repository != bundle.source_repository
        or bundle.run_2.repository != bundle.source_repository
    ):
        return _fail(
            bundle,
            "REPOSITORY_IDENTITY",
            "SOURCE_REPOSITORY_MISMATCH",
        )

    try:
        validate_compiled_markdown(a1.markdown)
    except ValueError:
        return _fail(bundle, "A1_CAPTURE", "A1_CAPTURE_INVALID")
    _, a1_time = _parse_time(a1.created_at, "A1 capture time")
    expected_note = FieldNoteIdentity(
        note_path=a1.relative_path,
        field_note_id=a1.field_note_id,
        note_sha256=a1.sha256,
        origin_run_id=a1.source_run_id,
    )
    if (
        a1.source_run_id != bundle.run_1.run_id
        or bundle.note.origin_run_id != bundle.run_1.run_id
    ):
        return _fail(bundle, "A1_CAPTURE", "A1_RUN_MISMATCH")
    if (
        bundle.note != expected_note
        or bundle.note_bytes != a1.markdown
        or len(bundle.note_bytes) != len(a1.markdown)
        or _sha256_bytes(bundle.note_bytes) != bundle.note.note_sha256
        or _sha256_bytes(a1.markdown) != a1.sha256
    ):
        return _fail(bundle, "A1_CAPTURE", "A1_NOTE_IDENTITY_MISMATCH")
    if bundle.attempt.proof_mode == "CREATOR_LIVE":
        assert bundle.creator_live_readback is not None
        commit = bundle.creator_live_readback.a1_capture_commit
        if (
            commit is None
            or commit.proof_attempt_id != bundle.attempt.proof_attempt_id
            or commit.run_id != bundle.run_1.run_id
            or commit.actual_runtime_identity != bundle.run_1.runtime
            or commit.source_repository != bundle.source_repository
            or commit.note != bundle.note
            or commit.note_byte_count != len(bundle.note_bytes)
            or commit.draft_evidence_sha256 != _a1_evidence_sha256(a1)
            or commit.draft_created_at != a1.created_at
            or not bundle.proof_trace
            or bundle.proof_trace[0].evidence_sha256
            != commit.receipt_sha256
        ):
            return _fail(
                bundle,
                "A1_CAPTURE",
                "A1_CAPTURE_COMMIT_MISMATCH",
            )
        _, save_time = _parse_time(commit.save_as_of, "A1 save As-of")
        _, observed_time = _parse_time(
            bundle.proof_trace[0].observed_at,
            "A1 checkpoint observation",
        )
        _, proof_time = _parse_time(
            _bundle_proof_as_of(bundle),
            "Proof As-of",
        )
        if not (
            run_1_time <= a1_time <= save_time <= observed_time <= proof_time
        ):
            return _fail(
                bundle,
                "A1_CAPTURE",
                "A1_CAPTURE_CHRONOLOGY_INVALID",
            )
    if a1_time < run_1_time or a1_time >= run_2_time:
        return _fail(bundle, "A1_CAPTURE", "A1_NOT_NEW_FOR_PROOF_ATTEMPT")

    if a2.run_id != bundle.run_2.run_id:
        return _fail(bundle, "A2_RECONNECT", "A2_RUN_MISMATCH")
    if (
        a2.state not in {"INJECTED", "ACTIVATION_UNKNOWN"}
        or a2.full_notes_injected != 1
        or a2.failure_reason is not None
    ):
        return _fail(bundle, "A2_RECONNECT", "A2_NOT_INJECTED")
    if (
        a2.selected_field_note_path != bundle.note.note_path
        or a2.selected_field_note_id != bundle.note.field_note_id
        or a2.selected_full_note_sha256 != bundle.note.note_sha256
        or a2.full_note_bytes_read != len(bundle.note_bytes)
    ):
        return _fail(bundle, "A2_RECONNECT", "A2_EXACT_NOTE_MISMATCH")

    if a3.state != "REUSED" or a3.use_evidence is None:
        return _fail(bundle, "A3_REUSE", "A3_NOT_DEMONSTRABLY_REUSED")
    if a3.note != bundle.note:
        return _fail(bundle, "A3_REUSE", "A3_EXACT_NOTE_MISMATCH")
    if (
        a3.reusing_run_id != bundle.run_2.run_id
        or a3.use_evidence.reusing_run_id != bundle.run_2.run_id
    ):
        return _fail(bundle, "A3_REUSE", "A3_RUN_MISMATCH")
    if not a3.use_evidence.structure_binding.verifies(
        bundle.note,
        bundle.note_bytes,
    ):
        return _fail(bundle, "A3_REUSE", "A3_STRUCTURE_BINDING_INVALID")
    if a3.reuse_event_id != _expected_reuse_event_id(a3):
        return _fail(bundle, "A3_REUSE", "A3_REUSE_EVENT_ID_INVALID")
    if a3.promotion != PromotionPolicyBoundary():
        return _fail(bundle, "A3_REUSE", "A3_PROMOTABLE_POLICY_WIDENED")
    _, use_time = _parse_time(a3.use_evidence.as_of, "A3 use evidence As-of")
    _, outcome_time = _parse_time(a3.outcome_as_of, "A3 outcome As-of")
    if use_time < run_2_time or outcome_time < use_time:
        return _fail(bundle, "A3_REUSE", "A3_EVIDENCE_TIME_ORDER_INVALID")

    expected_partition = _canonical_sha256(bundle.note.as_dict())
    if len(a4.events) != 1:
        return _fail(bundle, "A4_DURABILITY", "A4_EVENT_COUNT_NOT_EXACTLY_ONE")
    event = a4.events[0]
    if (
        a4.note != bundle.note
        or event.sequence != 0
        or event.previous_event_sha256 != GENESIS_EVENT_SHA256
        or event.note_partition_sha256 != expected_partition
        or event.event_id != a3.reuse_event_id
        or event.receipt != a3
        or event.receipt_sha256 != _event_receipt_sha256(event)
        or event.event_sha256 != _event_sha256(event)
        or a4.chain_head_sha256 != event.event_sha256
        or a4.evidence_maturity.note != bundle.note
        or a4.evidence_maturity.state != "REUSED"
        or a4.evidence_maturity.reuse_event_ids != (a3.reuse_event_id,)
    ):
        return _fail(bundle, "A4_DURABILITY", "A4_EXACT_EVENT_INTEGRITY_INVALID")
    _, recorded_time = _parse_time(event.recorded_at, "A4 recorded-at")
    if recorded_time < outcome_time or recorded_time < use_time:
        return _fail(bundle, "A4_DURABILITY", "A4_EVENT_TIME_ORDER_INVALID")

    if (
        a5.status not in {"RECORDED", "ALREADY_RECORDED"}
        or not a5.durable_commit_confirmed
        or a5.append_result is None
        or a5.durable_snapshot is None
    ):
        return _fail(bundle, "A5_CONFIRMATION", "A5_APPEND_NOT_CONFIRMED")
    if (
        a5.assessment != a3
        or a5.delivery_context != a2
        or a5.append_result.event != event
        or a5.append_result.appended != (a5.status == "RECORDED")
        or a5.durable_snapshot != a4
    ):
        return _fail(bundle, "A5_CONFIRMATION", "A5_READ_BACK_LINEAGE_MISMATCH")

    if a6.note_identity != bundle.note:
        return _fail(bundle, "A6_REVIEW", "A6_EXACT_NOTE_MISMATCH")
    if (
        a6.ledger_identity.note_partition_sha256 != expected_partition
        or a6.ledger_identity.durable_event_count != 1
        or a6.ledger_identity.chain_head_sha256 != event.event_sha256
        or len(a6.ordered_event_reviews) != 1
    ):
        return _fail(bundle, "A6_REVIEW", "A6_LEDGER_IDENTITY_MISMATCH")
    review = a6.ordered_event_reviews[0]
    if (
        review.sequence != event.sequence
        or review.recorded_at != event.recorded_at
        or review.event_id != event.event_id
        or review.previous_event_sha256 != event.previous_event_sha256
        or review.event_sha256 != event.event_sha256
        or review.reusing_run_id != a3.reusing_run_id
        or review.structure_id != a3.use_evidence.structure_id
        or review.structure_sha256 != a3.use_evidence.structure_sha256
        or review.structure_binding_sha256
        != a3.use_evidence.structure_binding.binding_sha256
        or review.evidence_class != a3.use_evidence.evidence_class
        or review.evidence_origin != a3.use_evidence.evidence_origin
        or review.evidence_ref != a3.use_evidence.evidence_ref
        or review.evidence_sha256 != a3.use_evidence.evidence_sha256
        or review.use_evidence_observer_id != a3.use_evidence.observer_id
        or review.use_evidence_observer_relation
        != a3.use_evidence.observer_relation
        or review.use_evidence_as_of != a3.use_evidence.as_of
        or review.claimed_outcome != a3.claimed_outcome
        or review.effective_outcome != a3.outcome
        or review.outcome_scope != a3.outcome_scope
        or review.causal_evidence_ref != a3.causal_evidence_ref
        or review.causal_evidence_sha256 != a3.causal_evidence_sha256
        or review.outcome_observer_id != a3.outcome_observer_id
        or review.outcome_observer_relation != a3.outcome_observer_relation
        or review.outcome_confirmation != a3.outcome_confirmation
        or review.outcome_as_of != a3.outcome_as_of
        or review.contribution_separated != a3.contribution_separated
        or review.human_intervention != a3.human_intervention
        or review.next_action != a3.next_action
        or review.reevaluation_condition != a3.reevaluation_condition
        or review.stop_scope != a3.stop_scope
        or review.revision != a3.revision
    ):
        return _fail(bundle, "A6_REVIEW", "A6_EXACT_EVENT_MISMATCH")
    if (
        a6.evidence_maturity.state != "REUSED"
        or a6.evidence_maturity.reuse_event_ids != (a3.reuse_event_id,)
        or a6.evidence_maturity.promotion != PromotionPolicyBoundary()
        or a6.current_serving_policy.derivation != "DELAY"
        or a6.current_serving_policy.automatic_injection is not None
        or a6.current_serving_policy.authority_precedence
        != ("TOPMOST_CANONICAL", "ADVISORY_FIELD_NOTE")
    ):
        return _fail(bundle, "A6_REVIEW", "A6_POLICY_BOUNDARY_WIDENED")
    _, review_time = _parse_time(a6.review_as_of, "A6 Review As-of")
    if review_time < max(recorded_time, use_time, outcome_time):
        return _fail(bundle, "A6_REVIEW", "A6_FUTURE_DATED_EVIDENCE")
    _, proof_time = _parse_time(_bundle_proof_as_of(bundle), "Proof As-of")
    if proof_time < review_time:
        return _fail(bundle, "PROOF_AS_OF", "PROOF_AS_OF_PRECEDES_A6_REVIEW")

    creator_a1_commit = (
        bundle.creator_live_readback.a1_capture_commit
        if bundle.attempt.proof_mode == "CREATOR_LIVE"
        and bundle.creator_live_readback is not None
        else None
    )
    expected_evidence = (
        (
            creator_a1_commit.receipt_sha256
            if creator_a1_commit is not None
            else _a1_evidence_sha256(a1)
        ),
        _a2_receipt_sha256(a2),
        (
            _a3_receipt_sha256(a3)
            if bundle.attempt.proof_mode == "CREATOR_LIVE"
            else a3.reuse_event_id
        ),
        event.event_sha256,
        _a5_confirmation_sha256(a5),
        _a6_packet_sha256(a6),
    )
    expected_runs = (
        bundle.run_1.run_id,
        bundle.run_2.run_id,
        bundle.run_2.run_id,
        bundle.run_2.run_id,
        bundle.run_2.run_id,
        bundle.run_2.run_id,
    )
    minimum_times = (
        a1_time,
        run_2_time,
        max(use_time, outcome_time),
        recorded_time,
        recorded_time,
        review_time,
    )
    if len(bundle.proof_trace) != len(_TRACE_STAGES):
        return _fail(bundle, "HUMAN_REPAIR", "TYPED_PROOF_TRACE_INVALID")
    previous = TRACE_GENESIS_SHA256
    previous_time: datetime | None = None
    for index, trace in enumerate(bundle.proof_trace):
        _, trace_time = _parse_time(trace.observed_at, "Trace observation time")
        if (
            trace.sequence != index
            or trace.stage != _TRACE_STAGES[index]
            or trace.run_id != expected_runs[index]
            or trace.evidence_sha256 != expected_evidence[index]
            or trace.previous_trace_sha256 != previous
            or trace_time < minimum_times[index]
            or trace_time > proof_time
            or (previous_time is not None and trace_time < previous_time)
        ):
            return _fail(
                bundle,
                "HUMAN_REPAIR",
                "TYPED_PROOF_TRACE_INVALID",
            )
        if trace.repair_action != "NONE":
            return _fail(
                bundle,
                "HUMAN_REPAIR",
                "HUMAN_REPAIR_DETECTED",
                human_repair_result="REPAIR_DETECTED",
            )
        previous = trace.trace_sha256
        previous_time = trace_time

    return _receipt(
        bundle,
        state="PASS",
        failed_boundary=None,
        failure_reason=None,
        human_repair_result="TYPED_TRACE_VERIFIED",
    )


def build_portable_candidate_warehouse_manifest(
    bundle: FieldNoteWholeFlowEvidenceBundle,
) -> PortableCandidateWarehouseManifest:
    """Reverify one bundle before creating its evidence-labelled candidate."""

    receipt = verify_field_note_whole_flow(bundle)
    if receipt.state != "PASS":
        raise FieldNoteWholeFlowValidationError(
            "Warehouse manifest requires a bundle that verifies to PASS."
        )
    return PortableCandidateWarehouseManifest._from_verified_receipt(receipt)
