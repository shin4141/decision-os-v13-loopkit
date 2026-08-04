"""Runtime-owned, append-only A7 creator-live proof trace acquisition."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any, Literal

from decision_os.acceleration.codex_adapter import CodexRuntimeIdentity
from decision_os.companion.field_notes_maturity_commit import (
    FieldNoteMaturityCommitResult,
)
from decision_os.companion.field_notes_maturity_ledger import (
    GENESIS_EVENT_SHA256,
    FieldNoteMaturityLedgerSnapshot,
)
from decision_os.companion.field_notes_maturity_review import (
    FieldNoteMaturityReviewPacket,
)
from decision_os.companion.field_notes_model import (
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
from decision_os.companion.field_notes_whole_flow import (
    TRACE_GENESIS_SHA256,
    WHOLE_FLOW_TRACE_SCHEMA,
    FieldNoteCreatorLiveRuntimeProvenance,
    FieldNoteSourceRepositoryIdentity,
    FieldNoteWholeFlowAttempt,
    FieldNoteWholeFlowRunIdentity,
    FieldNoteWholeFlowTraceEvent,
    FieldNoteWholeFlowValidationError,
    RepairAction,
    TraceStage,
    WholeFlowBoundary,
    _RUNTIME_PROVENANCE_AUTHORITY,
    _a1_evidence_sha256,
    _a2_receipt_sha256,
    _a3_receipt_sha256,
    _a5_confirmation_sha256,
    _a6_packet_sha256,
    _canonical_sha256,
    _event_receipt_sha256,
    _event_sha256,
    _expected_reuse_event_id,
    _parse_time,
    _runtime_as_dict,
    _sha256_bytes,
)


CREATOR_LIVE_JOURNAL_SCHEMA = (
    "decision-os.field-note-creator-live-proof-journal.v0.1"
)
CREATOR_LIVE_RECORD_SCHEMA = (
    "decision-os.field-note-creator-live-proof-record.v0.1"
)
CREATOR_LIVE_READBACK_SCHEMA = (
    "decision-os.field-note-creator-live-proof-readback.v0.1"
)
CREATOR_LIVE_ANCHOR_SCHEMA = (
    "decision-os.field-note-creator-live-proof-anchor.v0.1"
)
CREATOR_LIVE_JOURNAL_FILENAME = "creator-live-proof-v0.1.jsonl"
CREATOR_LIVE_ANCHOR_FILENAME = "creator-live-proof-v0.1.anchor.jsonl"
JOURNAL_GENESIS_SHA256 = "0" * 64
ANCHOR_GENESIS_SHA256 = "0" * 64

CreatorLiveAttemptState = Literal[
    "OPEN",
    "NOT_READY",
    "FAILED",
    "TRACE_COMPLETE",
]
JournalRecordKind = Literal[
    "ATTEMPT_OPENED",
    "RUN_2_OPENED",
    "CHECKPOINT",
    "ATTEMPT_FAILED",
    "TRACE_COMPLETED",
]

_STAGES: tuple[TraceStage, ...] = (
    "A1_CAPTURE",
    "A2_RECONNECT",
    "A3_REUSE",
    "A4_DURABILITY",
    "A5_CONFIRMATION",
    "A6_REVIEW",
)
_READBACK_AUTHORITY = object()


class FieldNoteCreatorLiveError(RuntimeError):
    """Base error for the bounded creator-live runtime path."""


class FieldNoteCreatorLiveValidationError(
    FieldNoteCreatorLiveError,
    ValueError,
):
    """The caller supplied an invalid identity or typed stage result."""


class FieldNoteCreatorLiveStageError(FieldNoteCreatorLiveError):
    """A stage failed and the one-attempt journal is terminal."""


class FieldNoteCreatorLiveDurabilityError(FieldNoteCreatorLiveError):
    """The durable journal cannot be trusted or extended."""


class FieldNoteCreatorLiveAttemptExistsError(FieldNoteCreatorLiveError):
    """The one-attempt journal already exists and cannot be replaced."""


class _JournalIntegrityError(ValueError):
    def __init__(
        self,
        reason: str,
        *,
        repair_action: RepairAction,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.repair_action = repair_action


def _utc_now_rfc3339() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _bounded_reason(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 256
        or "\x00" in value
    ):
        raise FieldNoteCreatorLiveValidationError(
            "Creator-live failure reason is outside its bounded schema."
        )
    return value.strip()


def _runtime_from_dict(value: Any) -> CodexRuntimeIdentity:
    if not isinstance(value, dict) or set(value) != {
        "model",
        "reasoning_effort",
        "service_tier",
        "codex_cli_version",
        "account_type",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUNTIME_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        return CodexRuntimeIdentity(**value)
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUNTIME_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc


def _repository_from_dict(value: Any) -> FieldNoteSourceRepositoryIdentity:
    if not isinstance(value, dict) or set(value) != {
        "repository_id",
        "source_commit",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_REPOSITORY_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        return FieldNoteSourceRepositoryIdentity(**value)
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_REPOSITORY_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc


def _run_from_dict(
    value: Any,
    *,
    repository: FieldNoteSourceRepositoryIdentity,
    runtime: CodexRuntimeIdentity,
) -> FieldNoteWholeFlowRunIdentity:
    if not isinstance(value, dict) or set(value) != {
        "proof_attempt_id",
        "run_id",
        "started_at",
        "repository",
        "runtime",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUN_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    if value["repository"] != repository.as_dict() or value["runtime"] != (
        _runtime_as_dict(runtime)
    ):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUN_IDENTITY_MISMATCH",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        return FieldNoteWholeFlowRunIdentity(
            proof_attempt_id=value["proof_attempt_id"],
            run_id=value["run_id"],
            started_at=value["started_at"],
            repository=repository,
            runtime=runtime,
        )
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUN_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc


def _attempt_from_dict(value: Any) -> FieldNoteWholeFlowAttempt:
    if not isinstance(value, dict) or set(value) != {
        "proof_attempt_id",
        "proof_mode",
        "creator_id",
        "proof_as_of",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        attempt = FieldNoteWholeFlowAttempt(**value)
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc
    if attempt.proof_mode != "CREATOR_LIVE":
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_MODE_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    return attempt


@dataclass(frozen=True)
class _JournalRecord:
    sequence: int
    kind: JournalRecordKind
    payload: dict[str, Any]
    previous_record_sha256: str
    record_sha256: str

    @classmethod
    def create(
        cls,
        *,
        sequence: int,
        kind: JournalRecordKind,
        payload: dict[str, Any],
        previous_record_sha256: str,
    ) -> _JournalRecord:
        body = {
            "schema": CREATOR_LIVE_RECORD_SCHEMA,
            "sequence": sequence,
            "kind": kind,
            "payload": payload,
            "previous_record_sha256": previous_record_sha256,
        }
        return cls(
            sequence=sequence,
            kind=kind,
            payload=payload,
            previous_record_sha256=previous_record_sha256,
            record_sha256=_canonical_sha256(body),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": CREATOR_LIVE_RECORD_SCHEMA,
            "sequence": self.sequence,
            "kind": self.kind,
            "payload": self.payload,
            "previous_record_sha256": self.previous_record_sha256,
            "record_sha256": self.record_sha256,
        }

    def serialize_line(self) -> bytes:
        return (canonical_json(self.as_dict()) + "\n").encode("utf-8")


@dataclass(frozen=True)
class _AnchorRecord:
    generation: int
    proof_attempt_id: str
    journal_record_count: int
    journal_byte_length: int
    journal_record_chain_head_sha256: str
    journal_sha256: str
    previous_anchor_sha256: str
    anchor_sha256: str

    @classmethod
    def create(
        cls,
        *,
        generation: int,
        proof_attempt_id: str,
        journal_raw: bytes,
        journal_records: tuple[_JournalRecord, ...],
        previous_anchor_sha256: str,
    ) -> _AnchorRecord:
        body = {
            "schema": CREATOR_LIVE_ANCHOR_SCHEMA,
            "generation": generation,
            "proof_attempt_id": proof_attempt_id,
            "journal_record_count": len(journal_records),
            "journal_byte_length": len(journal_raw),
            "journal_record_chain_head_sha256": (
                journal_records[-1].record_sha256
            ),
            "journal_sha256": hashlib.sha256(journal_raw).hexdigest(),
            "previous_anchor_sha256": previous_anchor_sha256,
        }
        return cls(
            generation=generation,
            proof_attempt_id=proof_attempt_id,
            journal_record_count=len(journal_records),
            journal_byte_length=len(journal_raw),
            journal_record_chain_head_sha256=(
                journal_records[-1].record_sha256
            ),
            journal_sha256=hashlib.sha256(journal_raw).hexdigest(),
            previous_anchor_sha256=previous_anchor_sha256,
            anchor_sha256=_canonical_sha256(body),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": CREATOR_LIVE_ANCHOR_SCHEMA,
            "generation": self.generation,
            "proof_attempt_id": self.proof_attempt_id,
            "journal_record_count": self.journal_record_count,
            "journal_byte_length": self.journal_byte_length,
            "journal_record_chain_head_sha256": (
                self.journal_record_chain_head_sha256
            ),
            "journal_sha256": self.journal_sha256,
            "previous_anchor_sha256": self.previous_anchor_sha256,
            "anchor_sha256": self.anchor_sha256,
        }

    def serialize_line(self) -> bytes:
        return (canonical_json(self.as_dict()) + "\n").encode("utf-8")


def _parse_records(raw: bytes) -> tuple[_JournalRecord, ...]:
    if not raw or not raw.endswith(b"\n"):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_DURABLE_TRACE_TRUNCATED",
            repair_action="EVIDENCE_DELETION",
        )
    records: list[_JournalRecord] = []
    previous = JOURNAL_GENESIS_SHA256
    for index, line in enumerate(raw.splitlines()):
        try:
            text = line.decode("utf-8")
            value = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_TRACE_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            ) from exc
        if not isinstance(value, dict) or canonical_json(value) != text:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_TRACE_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            )
        if set(value) != {
            "schema",
            "sequence",
            "kind",
            "payload",
            "previous_record_sha256",
            "record_sha256",
        }:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_TRACE_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            )
        kind = value["kind"]
        if kind not in {
            "ATTEMPT_OPENED",
            "RUN_2_OPENED",
            "CHECKPOINT",
            "ATTEMPT_FAILED",
            "TRACE_COMPLETED",
        }:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_TRACE_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            )
        body = {
            "schema": value["schema"],
            "sequence": value["sequence"],
            "kind": kind,
            "payload": value["payload"],
            "previous_record_sha256": value["previous_record_sha256"],
        }
        expected_sha = _canonical_sha256(body)
        if (
            value["schema"] != CREATOR_LIVE_RECORD_SCHEMA
            or value["sequence"] != index
            or value["previous_record_sha256"] != previous
            or value["record_sha256"] != expected_sha
            or not isinstance(value["payload"], dict)
        ):
            reason = (
                "CREATOR_LIVE_DURABLE_TRACE_DUPLICATED"
                if value["sequence"] != index
                else "CREATOR_LIVE_DURABLE_CHAIN_HEAD_MISMATCH"
            )
            action: RepairAction = (
                "RETRY_REPLACEMENT"
                if value["sequence"] != index
                else "EVENT_ID_CHANGE"
            )
            raise _JournalIntegrityError(reason, repair_action=action)
        record = _JournalRecord(
            sequence=index,
            kind=kind,
            payload=value["payload"],
            previous_record_sha256=previous,
            record_sha256=expected_sha,
        )
        records.append(record)
        previous = expected_sha
    return tuple(records)


def _parse_anchors(raw: bytes) -> tuple[_AnchorRecord, ...]:
    if not raw or not raw.endswith(b"\n"):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_DURABLE_ANCHOR_TRUNCATED",
            repair_action="EVIDENCE_DELETION",
        )
    anchors: list[_AnchorRecord] = []
    previous = ANCHOR_GENESIS_SHA256
    for generation, line in enumerate(raw.splitlines()):
        try:
            text = line.decode("utf-8")
            value = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_ANCHOR_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            ) from exc
        required = {
            "schema",
            "generation",
            "proof_attempt_id",
            "journal_record_count",
            "journal_byte_length",
            "journal_record_chain_head_sha256",
            "journal_sha256",
            "previous_anchor_sha256",
            "anchor_sha256",
        }
        if (
            not isinstance(value, dict)
            or set(value) != required
            or canonical_json(value) != text
        ):
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_ANCHOR_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            )
        body = {key: value[key] for key in required - {"anchor_sha256"}}
        expected_sha = _canonical_sha256(body)
        if (
            value["schema"] != CREATOR_LIVE_ANCHOR_SCHEMA
            or value["generation"] != generation
            or value["previous_anchor_sha256"] != previous
            or value["anchor_sha256"] != expected_sha
            or not isinstance(value["proof_attempt_id"], str)
            or not value["proof_attempt_id"]
            or type(value["journal_record_count"]) is not int
            or value["journal_record_count"] <= 0
            or type(value["journal_byte_length"]) is not int
            or value["journal_byte_length"] <= 0
        ):
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_ANCHOR_CHAIN_INVALID",
                repair_action="EVENT_ID_CHANGE",
            )
        for key in (
            "journal_record_chain_head_sha256",
            "journal_sha256",
            "previous_anchor_sha256",
            "anchor_sha256",
        ):
            digest = value[key]
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_DURABLE_ANCHOR_CHAIN_INVALID",
                    repair_action="EVENT_ID_CHANGE",
                )
        anchor = _AnchorRecord(
            generation=generation,
            proof_attempt_id=value["proof_attempt_id"],
            journal_record_count=value["journal_record_count"],
            journal_byte_length=value["journal_byte_length"],
            journal_record_chain_head_sha256=(
                value["journal_record_chain_head_sha256"]
            ),
            journal_sha256=value["journal_sha256"],
            previous_anchor_sha256=previous,
            anchor_sha256=expected_sha,
        )
        anchors.append(anchor)
        previous = expected_sha
    return tuple(anchors)


def _verify_journal_anchor(
    journal_raw: bytes,
    records: tuple[_JournalRecord, ...],
    anchors: tuple[_AnchorRecord, ...],
    *,
    proof_attempt_id: str,
) -> None:
    if not anchors or any(
        anchor.proof_attempt_id != proof_attempt_id for anchor in anchors
    ):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_DURABLE_ANCHOR_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    anchor = anchors[-1]
    if (
        anchor.journal_record_count != len(records)
        or anchor.journal_byte_length != len(journal_raw)
        or anchor.journal_record_chain_head_sha256
        != records[-1].record_sha256
        or anchor.journal_sha256 != hashlib.sha256(journal_raw).hexdigest()
    ):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_DURABLE_JOURNAL_ANCHOR_MISMATCH",
            repair_action="EVIDENCE_DELETION",
        )


def _note_from_dict(value: Any) -> FieldNoteIdentity:
    if not isinstance(value, dict) or set(value) != {
        "note_path",
        "field_note_id",
        "note_sha256",
        "origin_run_id",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CAPTURED_NOTE_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        return FieldNoteIdentity(**value)
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CAPTURED_NOTE_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc


def _provenance_from_dict(
    value: Any,
    *,
    attempt: FieldNoteWholeFlowAttempt,
    repository: FieldNoteSourceRepositoryIdentity,
    runtime: CodexRuntimeIdentity,
    run_1: FieldNoteWholeFlowRunIdentity,
) -> FieldNoteCreatorLiveRuntimeProvenance:
    provenance = FieldNoteCreatorLiveRuntimeProvenance._issue(
        authority=_RUNTIME_PROVENANCE_AUTHORITY,
        proof_attempt_id=attempt.proof_attempt_id,
        source_repository=repository,
        runtime=runtime,
        issued_for_run_1_id=run_1.run_id,
    )
    if value != provenance.as_dict():
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUNTIME_PROVENANCE_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    return provenance


def _event_from_dict(
    value: Any,
    *,
    attempt: FieldNoteWholeFlowAttempt,
    repository: FieldNoteSourceRepositoryIdentity,
    runtime: CodexRuntimeIdentity,
    provenance: FieldNoteCreatorLiveRuntimeProvenance,
) -> FieldNoteWholeFlowTraceEvent:
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "sequence",
        "stage",
        "run_id",
        "observed_at",
        "evidence_sha256",
        "previous_trace_sha256",
        "repair_action",
        "emitter",
        "proof_attempt_id",
        "runtime",
        "source_repository",
        "runtime_provenance",
        "trace_sha256",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CHECKPOINT_SHAPE_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    if (
        value["schema"] != WHOLE_FLOW_TRACE_SCHEMA
        or value["proof_attempt_id"] != attempt.proof_attempt_id
        or value["runtime"] != _runtime_as_dict(runtime)
        or value["source_repository"] != repository.as_dict()
        or value["runtime_provenance"] != provenance.as_dict()
    ):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CHECKPOINT_PROVENANCE_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        event = FieldNoteWholeFlowTraceEvent(
            sequence=value["sequence"],
            stage=value["stage"],
            run_id=value["run_id"],
            observed_at=value["observed_at"],
            evidence_sha256=value["evidence_sha256"],
            previous_trace_sha256=value["previous_trace_sha256"],
            repair_action=value["repair_action"],
            emitter=value["emitter"],
            proof_attempt_id=attempt.proof_attempt_id,
            runtime=runtime,
            source_repository=repository,
            runtime_provenance=provenance,
        )
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CHECKPOINT_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc
    if event.trace_sha256 != value["trace_sha256"]:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CHECKPOINT_IDENTITY_CHANGED",
            repair_action="EVENT_ID_CHANGE",
        )
    return event


@dataclass(frozen=True, init=False)
class FieldNoteCreatorLiveTraceReadback:
    """Sealed projection of exact durable journal bytes."""

    schema: Literal[
        "decision-os.field-note-creator-live-proof-readback.v0.1"
    ]
    attempt: FieldNoteWholeFlowAttempt
    source_repository: FieldNoteSourceRepositoryIdentity
    runtime: CodexRuntimeIdentity
    runtime_provenance: FieldNoteCreatorLiveRuntimeProvenance
    run_1: FieldNoteWholeFlowRunIdentity
    run_2: FieldNoteWholeFlowRunIdentity | None
    captured_note: FieldNoteIdentity | None
    captured_note_byte_count: int | None
    a3_reuse_event_id: str | None
    current_stage: TraceStage | None
    trace_event_count: int
    trace_chain_head_sha256: str
    events: tuple[FieldNoteWholeFlowTraceEvent, ...]
    state: CreatorLiveAttemptState
    failure_boundary: WholeFlowBoundary | None
    failure_reason: str | None
    repair_action: RepairAction
    one_attempt_no_retry: Literal[True]
    journal_record_count: int
    journal_byte_length: int
    journal_chain_head_sha256: str
    journal_sha256: str
    anchor_record_count: int
    anchor_chain_head_sha256: str
    anchor_sha256: str
    durable_readback_verified: bool

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise FieldNoteCreatorLiveValidationError(
            "Creator-live durable read-back cannot be caller-constructed."
        )

    @classmethod
    def _create(
        cls,
        *,
        authority: object,
        attempt: FieldNoteWholeFlowAttempt,
        source_repository: FieldNoteSourceRepositoryIdentity,
        runtime: CodexRuntimeIdentity,
        runtime_provenance: FieldNoteCreatorLiveRuntimeProvenance,
        run_1: FieldNoteWholeFlowRunIdentity,
        run_2: FieldNoteWholeFlowRunIdentity | None,
        captured_note: FieldNoteIdentity | None,
        captured_note_byte_count: int | None,
        a3_reuse_event_id: str | None,
        current_stage: TraceStage | None,
        events: tuple[FieldNoteWholeFlowTraceEvent, ...],
        state: CreatorLiveAttemptState,
        failure_boundary: WholeFlowBoundary | None,
        failure_reason: str | None,
        repair_action: RepairAction,
        journal_record_count: int,
        journal_byte_length: int,
        journal_chain_head_sha256: str,
        journal_sha256: str,
        anchor_record_count: int,
        anchor_chain_head_sha256: str,
        anchor_sha256: str,
        durable_readback_verified: bool,
    ) -> FieldNoteCreatorLiveTraceReadback:
        if authority is not _READBACK_AUTHORITY:
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live read-back authority is invalid."
            )
        value = object.__new__(cls)
        fields = {
            "schema": CREATOR_LIVE_READBACK_SCHEMA,
            "attempt": attempt,
            "source_repository": source_repository,
            "runtime": runtime,
            "runtime_provenance": runtime_provenance,
            "run_1": run_1,
            "run_2": run_2,
            "captured_note": captured_note,
            "captured_note_byte_count": captured_note_byte_count,
            "a3_reuse_event_id": a3_reuse_event_id,
            "current_stage": current_stage,
            "trace_event_count": len(events),
            "trace_chain_head_sha256": (
                events[-1].trace_sha256 if events else TRACE_GENESIS_SHA256
            ),
            "events": events,
            "state": state,
            "failure_boundary": failure_boundary,
            "failure_reason": failure_reason,
            "repair_action": repair_action,
            "one_attempt_no_retry": True,
            "journal_record_count": journal_record_count,
            "journal_byte_length": journal_byte_length,
            "journal_chain_head_sha256": journal_chain_head_sha256,
            "journal_sha256": journal_sha256,
            "anchor_record_count": anchor_record_count,
            "anchor_chain_head_sha256": anchor_chain_head_sha256,
            "anchor_sha256": anchor_sha256,
            "durable_readback_verified": durable_readback_verified,
        }
        for field, item in fields.items():
            object.__setattr__(value, field, item)
        return value

    @property
    def proof_attempt_id(self) -> str:
        return self.attempt.proof_attempt_id

    @property
    def creator_id(self) -> str:
        return self.attempt.creator_id

    def _body(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "attempt": self.attempt.as_dict(),
            "source_repository": self.source_repository.as_dict(),
            "runtime": _runtime_as_dict(self.runtime),
            "runtime_provenance": self.runtime_provenance.as_dict(),
            "run_1": self.run_1.as_dict(),
            "run_2": self.run_2.as_dict() if self.run_2 else None,
            "captured_note": (
                self.captured_note.as_dict() if self.captured_note else None
            ),
            "captured_note_byte_count": self.captured_note_byte_count,
            "a3_reuse_event_id": self.a3_reuse_event_id,
            "current_stage": self.current_stage,
            "trace_event_count": self.trace_event_count,
            "trace_chain_head_sha256": self.trace_chain_head_sha256,
            "events": [event.as_dict() for event in self.events],
            "state": self.state,
            "failure_boundary": self.failure_boundary,
            "failure_reason": self.failure_reason,
            "repair_action": self.repair_action,
            "one_attempt_no_retry": self.one_attempt_no_retry,
            "journal_record_count": self.journal_record_count,
            "journal_byte_length": self.journal_byte_length,
            "journal_chain_head_sha256": self.journal_chain_head_sha256,
            "journal_sha256": self.journal_sha256,
            "anchor_record_count": self.anchor_record_count,
            "anchor_chain_head_sha256": self.anchor_chain_head_sha256,
            "anchor_sha256": self.anchor_sha256,
            "durable_readback_verified": self.durable_readback_verified,
        }

    @property
    def readback_sha256(self) -> str:
        return _canonical_sha256(self._body())

    def as_dict(self) -> dict[str, Any]:
        return {**self._body(), "readback_sha256": self.readback_sha256}

    def matches_admission(
        self,
        *,
        attempt: FieldNoteWholeFlowAttempt,
        source_repository: FieldNoteSourceRepositoryIdentity,
        runtime: CodexRuntimeIdentity,
        run_1: FieldNoteWholeFlowRunIdentity,
        run_2: FieldNoteWholeFlowRunIdentity,
        proof_trace: tuple[FieldNoteWholeFlowTraceEvent, ...],
    ) -> bool:
        return (
            self.state == "TRACE_COMPLETE"
            and self.durable_readback_verified
            and self.failure_boundary is None
            and self.failure_reason is None
            and self.repair_action == "NONE"
            and self.attempt == attempt
            and self.source_repository == source_repository
            and self.runtime == runtime
            and self.run_1 == run_1
            and self.run_2 == run_2
            and self.a3_reuse_event_id is not None
            and self.events == proof_trace
            and self.trace_event_count == len(_STAGES)
            and self.trace_chain_head_sha256 == proof_trace[-1].trace_sha256
            and self.anchor_record_count == self.journal_record_count
            and self.journal_byte_length > 0
            and all(
                event.runtime_provenance == self.runtime_provenance
                for event in proof_trace
            )
        )


@dataclass(frozen=True)
class _StaticIdentity:
    attempt: FieldNoteWholeFlowAttempt
    repository: FieldNoteSourceRepositoryIdentity
    runtime: CodexRuntimeIdentity
    run_1: FieldNoteWholeFlowRunIdentity
    provenance: FieldNoteCreatorLiveRuntimeProvenance


def _static_identity(records: tuple[_JournalRecord, ...]) -> _StaticIdentity:
    if not records or records[0].kind != "ATTEMPT_OPENED":
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_RECORD_MISSING",
            repair_action="EVIDENCE_DELETION",
        )
    payload = records[0].payload
    if set(payload) != {
        "journal_schema",
        "attempt",
        "source_repository",
        "runtime",
        "run_1",
        "runtime_provenance",
        "one_attempt_no_retry",
    } or payload["journal_schema"] != CREATOR_LIVE_JOURNAL_SCHEMA:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_RECORD_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    if payload["one_attempt_no_retry"] is not True:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RETRY_BOUNDARY_INVALID",
            repair_action="RETRY_REPLACEMENT",
        )
    attempt = _attempt_from_dict(payload["attempt"])
    repository = _repository_from_dict(payload["source_repository"])
    runtime = _runtime_from_dict(payload["runtime"])
    run_1 = _run_from_dict(
        payload["run_1"],
        repository=repository,
        runtime=runtime,
    )
    if run_1.proof_attempt_id != attempt.proof_attempt_id:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUN_ATTEMPT_MISMATCH",
            repair_action="RECEIPT_REWRITE",
        )
    provenance = _provenance_from_dict(
        payload["runtime_provenance"],
        attempt=attempt,
        repository=repository,
        runtime=runtime,
        run_1=run_1,
    )
    return _StaticIdentity(
        attempt=attempt,
        repository=repository,
        runtime=runtime,
        run_1=run_1,
        provenance=provenance,
    )


def _project_records(
    journal_raw: bytes,
    records: tuple[_JournalRecord, ...],
    anchor_raw: bytes,
    anchors: tuple[_AnchorRecord, ...],
    static: _StaticIdentity,
) -> FieldNoteCreatorLiveTraceReadback:
    _verify_journal_anchor(
        journal_raw,
        records,
        anchors,
        proof_attempt_id=static.attempt.proof_attempt_id,
    )
    run_2: FieldNoteWholeFlowRunIdentity | None = None
    events: list[FieldNoteWholeFlowTraceEvent] = []
    captured_note: FieldNoteIdentity | None = None
    captured_note_byte_count: int | None = None
    a3_reuse_event_id: str | None = None
    state: CreatorLiveAttemptState = "OPEN"
    failure_boundary: WholeFlowBoundary | None = None
    failure_reason: str | None = None
    repair_action: RepairAction = "NONE"
    previous_trace = TRACE_GENESIS_SHA256

    for record in records[1:]:
        if state in {"FAILED", "TRACE_COMPLETE"}:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_TERMINAL_STATE_EXTENDED",
                repair_action="RETRY_REPLACEMENT",
            )
        payload = record.payload
        if record.kind == "RUN_2_OPENED":
            if run_2 is not None or len(events) != 1:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_2_ORDER_INVALID",
                    repair_action="RETRY_REPLACEMENT",
                )
            if set(payload) != {"run_2"}:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_2_RECORD_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            run_2 = _run_from_dict(
                payload["run_2"],
                repository=static.repository,
                runtime=static.runtime,
            )
            if (
                run_2.proof_attempt_id != static.attempt.proof_attempt_id
                or run_2.run_id == static.run_1.run_id
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_2_IDENTITY_INVALID",
                    repair_action="RETRY_REPLACEMENT",
                )
            _, run_1_time = _parse_time(
                static.run_1.started_at,
                "Run 1 start",
            )
            _, run_2_time = _parse_time(run_2.started_at, "Run 2 start")
            if run_2_time <= run_1_time:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_ORDER_INVALID",
                    repair_action="TIMESTAMP_CHANGE",
                )
            continue
        if record.kind == "CHECKPOINT":
            if set(payload) != {"event", "binding"}:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_CHECKPOINT_RECORD_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            event = _event_from_dict(
                payload["event"],
                attempt=static.attempt,
                repository=static.repository,
                runtime=static.runtime,
                provenance=static.provenance,
            )
            index = len(events)
            expected_run = (
                static.run_1.run_id
                if index == 0
                else run_2.run_id if run_2 else None
            )
            binding = payload["binding"]
            if (
                index >= len(_STAGES)
                or event.sequence != index
                or event.stage != _STAGES[index]
                or event.run_id != expected_run
                or event.previous_trace_sha256 != previous_trace
                or event.repair_action != "NONE"
                or not isinstance(binding, dict)
                or binding.get("evidence_sha256") != event.evidence_sha256
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_CHECKPOINT_ORDER_OR_IDENTITY_INVALID",
                    repair_action="EVENT_ID_CHANGE",
                )
            if index == 0:
                if set(binding) != {
                    "evidence_type",
                    "evidence_sha256",
                    "note",
                    "note_byte_count",
                } or binding["evidence_type"] != "FieldNoteDraft":
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A1_BINDING_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    )
                captured_note = _note_from_dict(binding["note"])
                count = binding["note_byte_count"]
                if type(count) is not int or count <= 0:
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A1_BYTE_COUNT_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    )
                captured_note_byte_count = count
            elif index == 2:
                if set(binding) != {
                    "evidence_type",
                    "evidence_sha256",
                    "reuse_event_id",
                } or binding["evidence_type"] != "FieldNoteReuseReceipt":
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A3_BINDING_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    )
                reuse_event_id = binding["reuse_event_id"]
                if (
                    not isinstance(reuse_event_id, str)
                    or len(reuse_event_id) != 64
                    or any(
                        character not in "0123456789abcdef"
                        for character in reuse_event_id
                    )
                ):
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A3_BINDING_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    )
                a3_reuse_event_id = reuse_event_id
            elif set(binding) != {"evidence_type", "evidence_sha256"}:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_STAGE_BINDING_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            events.append(event)
            previous_trace = event.trace_sha256
            continue
        if record.kind == "ATTEMPT_FAILED":
            if set(payload) != {
                "failure_boundary",
                "failure_reason",
                "repair_action",
            }:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_FAILURE_RECORD_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            boundary = payload["failure_boundary"]
            action = payload["repair_action"]
            if boundary not in {
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
            } or action not in {
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
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_FAILURE_RECORD_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            state = "FAILED"
            failure_boundary = boundary
            failure_reason = _bounded_reason(payload["failure_reason"])
            repair_action = action
            continue
        if record.kind == "TRACE_COMPLETED":
            if set(payload) != {
                "trace_event_count",
                "trace_chain_head_sha256",
                "runtime_provenance_id",
                "no_repair_verified",
            } or (
                len(events) != len(_STAGES)
                or run_2 is None
                or a3_reuse_event_id is None
                or payload["trace_event_count"] != len(_STAGES)
                or payload["trace_chain_head_sha256"] != previous_trace
                or payload["runtime_provenance_id"]
                != static.provenance.runtime_provenance_id
                or payload["no_repair_verified"] is not True
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_COMPLETION_RECORD_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            state = "TRACE_COMPLETE"
            continue
        raise _JournalIntegrityError(
            "CREATOR_LIVE_JOURNAL_ORDER_INVALID",
            repair_action="RECEIPT_REWRITE",
        )

    current_stage = (
        _STAGES[len(events)]
        if state == "OPEN" and len(events) < len(_STAGES)
        else None
    )
    return FieldNoteCreatorLiveTraceReadback._create(
        authority=_READBACK_AUTHORITY,
        attempt=static.attempt,
        source_repository=static.repository,
        runtime=static.runtime,
        runtime_provenance=static.provenance,
        run_1=static.run_1,
        run_2=run_2,
        captured_note=captured_note,
        captured_note_byte_count=captured_note_byte_count,
        a3_reuse_event_id=a3_reuse_event_id,
        current_stage=current_stage,
        events=tuple(events),
        state=state,
        failure_boundary=failure_boundary,
        failure_reason=failure_reason,
        repair_action=repair_action,
        journal_record_count=len(records),
        journal_byte_length=len(journal_raw),
        journal_chain_head_sha256=records[-1].record_sha256,
        journal_sha256=hashlib.sha256(journal_raw).hexdigest(),
        anchor_record_count=len(anchors),
        anchor_chain_head_sha256=anchors[-1].anchor_sha256,
        anchor_sha256=hashlib.sha256(anchor_raw).hexdigest(),
        durable_readback_verified=True,
    )


def _failed_readback(
    *,
    journal_raw: bytes,
    anchor_raw: bytes,
    static: _StaticIdentity,
    reason: str,
    repair_action: RepairAction,
) -> FieldNoteCreatorLiveTraceReadback:
    return FieldNoteCreatorLiveTraceReadback._create(
        authority=_READBACK_AUTHORITY,
        attempt=static.attempt,
        source_repository=static.repository,
        runtime=static.runtime,
        runtime_provenance=static.provenance,
        run_1=static.run_1,
        run_2=None,
        captured_note=None,
        captured_note_byte_count=None,
        a3_reuse_event_id=None,
        current_stage=None,
        events=(),
        state="FAILED",
        failure_boundary="RUNTIME_ENFORCEMENT",
        failure_reason=reason,
        repair_action=repair_action,
        journal_record_count=0,
        journal_byte_length=len(journal_raw),
        journal_chain_head_sha256=JOURNAL_GENESIS_SHA256,
        journal_sha256=hashlib.sha256(journal_raw).hexdigest(),
        anchor_record_count=0,
        anchor_chain_head_sha256=ANCHOR_GENESIS_SHA256,
        anchor_sha256=hashlib.sha256(anchor_raw).hexdigest(),
        durable_readback_verified=False,
    )


class FieldNoteCreatorLiveProofRuntime:
    """The only public path that can append creator-live checkpoints.

    Trust is bounded to this in-process implementation plus exact durable
    read-back. No signature, hardware root, separate observer, or adversarial
    local-process resistance is claimed.
    """

    def __init__(
        self,
        *,
        storage_root: Path,
        static: _StaticIdentity,
    ) -> None:
        self._storage_root = storage_root
        self._journal_path = storage_root / CREATOR_LIVE_JOURNAL_FILENAME
        self._anchor_path = storage_root / CREATOR_LIVE_ANCHOR_FILENAME
        self._static = static
        self._lock = threading.Lock()

    @property
    def journal_path(self) -> Path:
        return self._journal_path

    @property
    def anchor_path(self) -> Path:
        return self._anchor_path

    @classmethod
    def open_attempt(
        cls,
        storage_root: Path,
        *,
        attempt: FieldNoteWholeFlowAttempt,
        source_repository: FieldNoteSourceRepositoryIdentity,
        run_1: FieldNoteWholeFlowRunIdentity,
    ) -> FieldNoteCreatorLiveProofRuntime:
        if not isinstance(attempt, FieldNoteWholeFlowAttempt) or (
            attempt.proof_mode != "CREATOR_LIVE"
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live runtime requires a CREATOR_LIVE attempt."
            )
        if not isinstance(
            source_repository,
            FieldNoteSourceRepositoryIdentity,
        ) or not isinstance(run_1, FieldNoteWholeFlowRunIdentity):
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live runtime identity is not typed."
            )
        if (
            run_1.proof_attempt_id != attempt.proof_attempt_id
            or run_1.repository != source_repository
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Run 1 is cross-bound to the creator-live attempt."
            )
        root = Path(storage_root)
        if not root.is_absolute():
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live storage root must be absolute."
            )
        if root.exists() and root.is_symlink():
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live storage root cannot be a symlink."
            )
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        provenance = FieldNoteCreatorLiveRuntimeProvenance._issue(
            authority=_RUNTIME_PROVENANCE_AUTHORITY,
            proof_attempt_id=attempt.proof_attempt_id,
            source_repository=source_repository,
            runtime=run_1.runtime,
            issued_for_run_1_id=run_1.run_id,
        )
        static = _StaticIdentity(
            attempt=attempt,
            repository=source_repository,
            runtime=run_1.runtime,
            run_1=run_1,
            provenance=provenance,
        )
        payload = {
            "journal_schema": CREATOR_LIVE_JOURNAL_SCHEMA,
            "attempt": attempt.as_dict(),
            "source_repository": source_repository.as_dict(),
            "runtime": _runtime_as_dict(run_1.runtime),
            "run_1": run_1.as_dict(),
            "runtime_provenance": provenance.as_dict(),
            "one_attempt_no_retry": True,
        }
        record = _JournalRecord.create(
            sequence=0,
            kind="ATTEMPT_OPENED",
            payload=payload,
            previous_record_sha256=JOURNAL_GENESIS_SHA256,
        )
        path = root / CREATOR_LIVE_JOURNAL_FILENAME
        try:
            descriptor = os.open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError as exc:
            raise FieldNoteCreatorLiveAttemptExistsError(
                "Creator-live one-attempt journal already exists."
            ) from exc
        try:
            line = record.serialize_line()
            written = os.write(descriptor, line)
            if written != len(line):
                raise FieldNoteCreatorLiveDurabilityError(
                    "Creator-live attempt record write was incomplete."
                )
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        anchor = _AnchorRecord.create(
            generation=0,
            proof_attempt_id=attempt.proof_attempt_id,
            journal_raw=line,
            journal_records=(record,),
            previous_anchor_sha256=ANCHOR_GENESIS_SHA256,
        )
        anchor_path = root / CREATOR_LIVE_ANCHOR_FILENAME
        try:
            anchor_descriptor = os.open(
                anchor_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError as exc:
            raise FieldNoteCreatorLiveAttemptExistsError(
                "Creator-live one-attempt anchor already exists."
            ) from exc
        try:
            anchor_line = anchor.serialize_line()
            anchor_written = os.write(anchor_descriptor, anchor_line)
            if anchor_written != len(anchor_line):
                raise FieldNoteCreatorLiveDurabilityError(
                    "Creator-live attempt anchor write was incomplete."
                )
            os.fsync(anchor_descriptor)
        finally:
            os.close(anchor_descriptor)
        directory = os.open(root, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        runtime_path = cls(storage_root=root, static=static)
        if not runtime_path.read_back().durable_readback_verified:
            raise FieldNoteCreatorLiveDurabilityError(
                "Creator-live attempt did not survive exact durable read-back."
            )
        return runtime_path

    @classmethod
    def load_attempt(
        cls,
        storage_root: Path,
    ) -> FieldNoteCreatorLiveProofRuntime:
        root = Path(storage_root)
        path = root / CREATOR_LIVE_JOURNAL_FILENAME
        anchor_path = root / CREATOR_LIVE_ANCHOR_FILENAME
        journal_raw = path.read_bytes()
        anchor_raw = anchor_path.read_bytes()
        records = _parse_records(journal_raw)
        static = _static_identity(records)
        anchors = _parse_anchors(anchor_raw)
        _verify_journal_anchor(
            journal_raw,
            records,
            anchors,
            proof_attempt_id=static.attempt.proof_attempt_id,
        )
        return cls(storage_root=root, static=static)

    def _read_raw_locked(self, descriptor: int) -> bytes:
        os.lseek(descriptor, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)

    def read_back(self) -> FieldNoteCreatorLiveTraceReadback:
        with self._lock:
            journal_descriptor = os.open(self._journal_path, os.O_RDONLY)
            try:
                try:
                    anchor_descriptor = os.open(self._anchor_path, os.O_RDONLY)
                except OSError:
                    return _failed_readback(
                        journal_raw=self._read_raw_locked(journal_descriptor),
                        anchor_raw=b"",
                        static=self._static,
                        reason="CREATOR_LIVE_DURABLE_ANCHOR_MISSING",
                        repair_action="EVIDENCE_DELETION",
                    )
                try:
                    fcntl.flock(journal_descriptor, fcntl.LOCK_SH)
                    fcntl.flock(anchor_descriptor, fcntl.LOCK_SH)
                    journal_raw = self._read_raw_locked(journal_descriptor)
                    anchor_raw = self._read_raw_locked(anchor_descriptor)
                finally:
                    fcntl.flock(anchor_descriptor, fcntl.LOCK_UN)
                    os.close(anchor_descriptor)
            finally:
                fcntl.flock(journal_descriptor, fcntl.LOCK_UN)
                os.close(journal_descriptor)
        try:
            records = _parse_records(journal_raw)
            anchors = _parse_anchors(anchor_raw)
            static = _static_identity(records)
            if static != self._static:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_STATIC_IDENTITY_CHANGED",
                    repair_action="RECEIPT_REWRITE",
                )
            return _project_records(
                journal_raw,
                records,
                anchor_raw,
                anchors,
                static,
            )
        except _JournalIntegrityError as exc:
            return _failed_readback(
                journal_raw=journal_raw,
                anchor_raw=anchor_raw,
                static=self._static,
                reason=exc.reason,
                repair_action=exc.repair_action,
            )

    def _append(
        self,
        kind: JournalRecordKind,
        payload: dict[str, Any],
    ) -> FieldNoteCreatorLiveTraceReadback:
        with self._lock:
            journal_descriptor: int | None = None
            try:
                journal_descriptor = os.open(
                    self._journal_path,
                    os.O_RDWR | os.O_APPEND,
                )
                anchor_descriptor = os.open(
                    self._anchor_path,
                    os.O_RDWR | os.O_APPEND,
                )
            except OSError as exc:
                if journal_descriptor is not None:
                    os.close(journal_descriptor)
                raise FieldNoteCreatorLiveDurabilityError(
                    "Creator-live durable journal or anchor is missing."
                ) from exc
            try:
                fcntl.flock(journal_descriptor, fcntl.LOCK_EX)
                fcntl.flock(anchor_descriptor, fcntl.LOCK_EX)
                journal_raw = self._read_raw_locked(journal_descriptor)
                anchor_raw = self._read_raw_locked(anchor_descriptor)
                try:
                    records = _parse_records(journal_raw)
                    anchors = _parse_anchors(anchor_raw)
                    static = _static_identity(records)
                    readback = _project_records(
                        journal_raw,
                        records,
                        anchor_raw,
                        anchors,
                        static,
                    )
                except _JournalIntegrityError as exc:
                    raise FieldNoteCreatorLiveDurabilityError(
                        exc.reason
                    ) from exc
                if static != self._static or not readback.durable_readback_verified:
                    raise FieldNoteCreatorLiveDurabilityError(
                        "Creator-live durable identity changed before append."
                    )
                if readback.state in {"FAILED", "TRACE_COMPLETE"}:
                    raise FieldNoteCreatorLiveStageError(
                        "Creator-live attempt is terminal and cannot continue."
                    )
                record = _JournalRecord.create(
                    sequence=len(records),
                    kind=kind,
                    payload=payload,
                    previous_record_sha256=records[-1].record_sha256,
                )
                line = record.serialize_line()
                written = os.write(journal_descriptor, line)
                if written != len(line):
                    raise FieldNoteCreatorLiveDurabilityError(
                        "Creator-live journal append was incomplete."
                    )
                os.fsync(journal_descriptor)
                next_journal_raw = journal_raw + line
                next_records = records + (record,)
                anchor = _AnchorRecord.create(
                    generation=len(anchors),
                    proof_attempt_id=self._static.attempt.proof_attempt_id,
                    journal_raw=next_journal_raw,
                    journal_records=next_records,
                    previous_anchor_sha256=anchors[-1].anchor_sha256,
                )
                anchor_line = anchor.serialize_line()
                anchor_written = os.write(anchor_descriptor, anchor_line)
                if anchor_written != len(anchor_line):
                    raise FieldNoteCreatorLiveDurabilityError(
                        "Creator-live durable anchor append was incomplete."
                    )
                os.fsync(anchor_descriptor)
            finally:
                fcntl.flock(anchor_descriptor, fcntl.LOCK_UN)
                fcntl.flock(journal_descriptor, fcntl.LOCK_UN)
                os.close(anchor_descriptor)
                os.close(journal_descriptor)
        return self.read_back()

    def _terminal_failure(
        self,
        boundary: WholeFlowBoundary,
        reason: str,
        *,
        repair_action: RepairAction = "NONE",
    ) -> None:
        bounded = _bounded_reason(reason)
        readback = self.read_back()
        if readback.state in {"FAILED", "TRACE_COMPLETE"}:
            raise FieldNoteCreatorLiveStageError(
                "Creator-live attempt is terminal and cannot be reset."
            )
        self._append(
            "ATTEMPT_FAILED",
            {
                "failure_boundary": boundary,
                "failure_reason": bounded,
                "repair_action": repair_action,
            },
        )
        raise FieldNoteCreatorLiveStageError(bounded)

    def _require_stage(self, stage: TraceStage) -> FieldNoteCreatorLiveTraceReadback:
        readback = self.read_back()
        if not readback.durable_readback_verified:
            raise FieldNoteCreatorLiveDurabilityError(
                readback.failure_reason or "Creator-live read-back failed."
            )
        if readback.state in {"FAILED", "TRACE_COMPLETE"}:
            raise FieldNoteCreatorLiveStageError(
                "Creator-live attempt is terminal and cannot continue."
            )
        if readback.current_stage != stage:
            retry = stage in _STAGES[: readback.trace_event_count]
            self._terminal_failure(
                "RUNTIME_ENFORCEMENT",
                "CREATOR_LIVE_STAGE_ORDER_INVALID",
                repair_action=("RETRY_REPLACEMENT" if retry else "NONE"),
            )
        return readback

    def _emit(
        self,
        stage: TraceStage,
        *,
        evidence_sha256: str,
        binding: dict[str, Any],
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage(stage)
        index = readback.trace_event_count
        run = readback.run_1 if index == 0 else readback.run_2
        if run is None:
            self._terminal_failure(
                "RUN_SEPARATION",
                "CREATOR_LIVE_RUN_2_NOT_OPEN",
            )
        assert run is not None
        event = FieldNoteWholeFlowTraceEvent(
            sequence=index,
            stage=stage,
            run_id=run.run_id,
            observed_at=_utc_now_rfc3339(),
            evidence_sha256=evidence_sha256,
            previous_trace_sha256=readback.trace_chain_head_sha256,
            repair_action="NONE",
            proof_attempt_id=self._static.attempt.proof_attempt_id,
            runtime=self._static.runtime,
            source_repository=self._static.repository,
            runtime_provenance=self._static.provenance,
        )
        self._append(
            "CHECKPOINT",
            {"event": event.as_dict(), "binding": binding},
        )
        if stage == "A6_REVIEW":
            completed = self.read_back()
            self._append(
                "TRACE_COMPLETED",
                {
                    "trace_event_count": len(_STAGES),
                    "trace_chain_head_sha256": (
                        completed.trace_chain_head_sha256
                    ),
                    "runtime_provenance_id": (
                        self._static.provenance.runtime_provenance_id
                    ),
                    "no_repair_verified": True,
                },
            )
        return event

    def open_run_2(
        self,
        run_2: FieldNoteWholeFlowRunIdentity,
    ) -> FieldNoteCreatorLiveTraceReadback:
        readback = self.read_back()
        if readback.state != "OPEN":
            raise FieldNoteCreatorLiveStageError(
                "Creator-live attempt is terminal and cannot continue."
            )
        if readback.trace_event_count != 1 or readback.current_stage != (
            "A2_RECONNECT"
        ):
            self._terminal_failure(
                "RUN_SEPARATION",
                "CREATOR_LIVE_RUN_2_BEFORE_A1_CLOSURE",
            )
        if not isinstance(run_2, FieldNoteWholeFlowRunIdentity):
            self._terminal_failure(
                "RUN_SEPARATION",
                "CREATOR_LIVE_RUN_2_IDENTITY_INVALID",
            )
        if run_2.run_id == self._static.run_1.run_id:
            self._terminal_failure(
                "RUN_SEPARATION",
                "RUN_IDENTITIES_NOT_DISTINCT",
                repair_action="RETRY_REPLACEMENT",
            )
        if run_2.proof_attempt_id != self._static.attempt.proof_attempt_id:
            self._terminal_failure(
                "RUN_SEPARATION",
                "RUN_ATTEMPT_MISMATCH",
                repair_action="RETRY_REPLACEMENT",
            )
        if run_2.runtime != self._static.runtime:
            self._terminal_failure(
                "MODEL_IDENTITY",
                "MODEL_RUNTIME_MISMATCH",
                repair_action="RETRY_REPLACEMENT",
            )
        if run_2.repository != self._static.repository:
            self._terminal_failure(
                "REPOSITORY_IDENTITY",
                "SOURCE_REPOSITORY_MISMATCH",
                repair_action="RETRY_REPLACEMENT",
            )
        _, run_1_time = _parse_time(
            self._static.run_1.started_at,
            "Run 1 start",
        )
        _, run_2_time = _parse_time(run_2.started_at, "Run 2 start")
        if run_2_time <= run_1_time:
            self._terminal_failure(
                "RUN_SEPARATION",
                "RUN_ORDER_INVALID",
                repair_action="TIMESTAMP_CHANGE",
            )
        return self._append("RUN_2_OPENED", {"run_2": run_2.as_dict()})

    def record_a1_capture(self, draft: FieldNoteDraft) -> FieldNoteWholeFlowTraceEvent:
        self._require_stage("A1_CAPTURE")
        if not isinstance(draft, FieldNoteDraft):
            self._terminal_failure("A1_CAPTURE", "A1_CAPTURE_INVALID")
        try:
            validate_compiled_markdown(draft.markdown)
        except ValueError:
            self._terminal_failure("A1_CAPTURE", "A1_CAPTURE_INVALID")
        if (
            draft.source_run_id != self._static.run_1.run_id
            or _sha256_bytes(draft.markdown) != draft.sha256
        ):
            self._terminal_failure("A1_CAPTURE", "A1_NOTE_IDENTITY_MISMATCH")
        note = FieldNoteIdentity(
            note_path=draft.relative_path,
            field_note_id=draft.field_note_id,
            note_sha256=draft.sha256,
            origin_run_id=draft.source_run_id,
        )
        evidence_sha256 = _a1_evidence_sha256(draft)
        return self._emit(
            "A1_CAPTURE",
            evidence_sha256=evidence_sha256,
            binding={
                "evidence_type": "FieldNoteDraft",
                "evidence_sha256": evidence_sha256,
                "note": note.as_dict(),
                "note_byte_count": len(draft.markdown),
            },
        )

    def _require_exact_note(
        self,
        readback: FieldNoteCreatorLiveTraceReadback,
        note: FieldNoteIdentity,
        note_bytes: bytes,
        *,
        boundary: WholeFlowBoundary,
    ) -> None:
        if (
            not isinstance(note, FieldNoteIdentity)
            or not isinstance(note_bytes, bytes)
            or readback.captured_note != note
            or readback.captured_note_byte_count != len(note_bytes)
            or _sha256_bytes(note_bytes) != note.note_sha256
        ):
            self._terminal_failure(
                boundary,
                "CREATOR_LIVE_EXACT_NOTE_MISMATCH",
                repair_action="NOTE_EDIT",
            )

    def record_a2_reconnect(
        self,
        receipt: FieldNoteReconnectReceipt,
        *,
        note: FieldNoteIdentity,
        note_bytes: bytes,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage("A2_RECONNECT")
        self._require_exact_note(
            readback,
            note,
            note_bytes,
            boundary="A2_RECONNECT",
        )
        if not isinstance(receipt, FieldNoteReconnectReceipt):
            self._terminal_failure("A2_RECONNECT", "A2_EVIDENCE_INVALID")
        if readback.run_2 is None or receipt.run_id != readback.run_2.run_id:
            self._terminal_failure("A2_RECONNECT", "A2_RUN_MISMATCH")
        if (
            receipt.state not in {"INJECTED", "ACTIVATION_UNKNOWN"}
            or receipt.full_notes_injected != 1
            or receipt.failure_reason is not None
        ):
            self._terminal_failure("A2_RECONNECT", "A2_NOT_INJECTED")
        if (
            receipt.selected_field_note_path != note.note_path
            or receipt.selected_field_note_id != note.field_note_id
            or receipt.selected_full_note_sha256 != note.note_sha256
            or receipt.full_note_bytes_read != len(note_bytes)
        ):
            self._terminal_failure("A2_RECONNECT", "A2_EXACT_NOTE_MISMATCH")
        evidence_sha256 = _a2_receipt_sha256(receipt)
        return self._emit(
            "A2_RECONNECT",
            evidence_sha256=evidence_sha256,
            binding={
                "evidence_type": "FieldNoteReconnectReceipt",
                "evidence_sha256": evidence_sha256,
            },
        )

    def record_a3_reuse(
        self,
        receipt: FieldNoteReuseReceipt,
        *,
        note: FieldNoteIdentity,
        note_bytes: bytes,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage("A3_REUSE")
        self._require_exact_note(
            readback,
            note,
            note_bytes,
            boundary="A3_REUSE",
        )
        if not isinstance(receipt, FieldNoteReuseReceipt):
            self._terminal_failure("A3_REUSE", "A3_EVIDENCE_INVALID")
        if receipt.state != "REUSED" or receipt.use_evidence is None:
            self._terminal_failure("A3_REUSE", "A3_NOT_DEMONSTRABLY_REUSED")
        if receipt.note != note:
            self._terminal_failure("A3_REUSE", "A3_EXACT_NOTE_MISMATCH")
        if readback.run_2 is None or (
            receipt.reusing_run_id != readback.run_2.run_id
            or receipt.use_evidence.reusing_run_id != readback.run_2.run_id
        ):
            self._terminal_failure("A3_REUSE", "A3_RUN_MISMATCH")
        if not receipt.use_evidence.structure_binding.verifies(note, note_bytes):
            self._terminal_failure(
                "A3_REUSE",
                "A3_STRUCTURE_BINDING_INVALID",
            )
        if receipt.reuse_event_id != _expected_reuse_event_id(receipt):
            self._terminal_failure("A3_REUSE", "A3_REUSE_EVENT_ID_INVALID")
        if receipt.promotion != PromotionPolicyBoundary():
            self._terminal_failure("A3_REUSE", "A3_PROMOTABLE_POLICY_WIDENED")
        assert receipt.reuse_event_id is not None
        receipt_sha256 = _a3_receipt_sha256(receipt)
        return self._emit(
            "A3_REUSE",
            evidence_sha256=receipt_sha256,
            binding={
                "evidence_type": "FieldNoteReuseReceipt",
                "evidence_sha256": receipt_sha256,
                "reuse_event_id": receipt.reuse_event_id,
            },
        )

    def record_a4_durability(
        self,
        snapshot: FieldNoteMaturityLedgerSnapshot,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage("A4_DURABILITY")
        if not isinstance(snapshot, FieldNoteMaturityLedgerSnapshot):
            self._terminal_failure("A4_DURABILITY", "A4_EVIDENCE_INVALID")
        if len(snapshot.events) != 1 or readback.captured_note is None:
            self._terminal_failure(
                "A4_DURABILITY",
                "A4_EVENT_COUNT_NOT_EXACTLY_ONE",
            )
        event = snapshot.events[0]
        a3_receipt_identity = readback.events[2].evidence_sha256
        a3_reuse_event_id = readback.a3_reuse_event_id
        if (
            snapshot.note != readback.captured_note
            or a3_reuse_event_id is None
            or event.sequence != 0
            or event.previous_event_sha256 != GENESIS_EVENT_SHA256
            or event.event_id != event.receipt.reuse_event_id
            or event.receipt.reuse_event_id != a3_reuse_event_id
            or event.receipt.reuse_event_id
            != _expected_reuse_event_id(event.receipt)
            or event.receipt_sha256 != a3_receipt_identity
            or _event_receipt_sha256(event) != a3_receipt_identity
            or event.event_sha256 != _event_sha256(event)
            or snapshot.chain_head_sha256 != event.event_sha256
            or snapshot.evidence_maturity.state != "REUSED"
        ):
            self._terminal_failure(
                "A4_DURABILITY",
                "A4_EXACT_EVENT_INTEGRITY_INVALID",
                repair_action="LEDGER_REWRITE",
            )
        return self._emit(
            "A4_DURABILITY",
            evidence_sha256=event.event_sha256,
            binding={
                "evidence_type": "FieldNoteMaturityLedgerEvent",
                "evidence_sha256": event.event_sha256,
            },
        )

    def record_a5_confirmation(
        self,
        result: FieldNoteMaturityCommitResult,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage("A5_CONFIRMATION")
        if not isinstance(result, FieldNoteMaturityCommitResult):
            self._terminal_failure("A5_CONFIRMATION", "A5_EVIDENCE_INVALID")
        if (
            result.status not in {"RECORDED", "ALREADY_RECORDED"}
            or not result.durable_commit_confirmed
            or result.append_result is None
            or result.durable_snapshot is None
        ):
            self._terminal_failure(
                "A5_CONFIRMATION",
                "A5_APPEND_NOT_CONFIRMED",
            )
        a2_identity = readback.events[1].evidence_sha256
        a3_receipt_identity = readback.events[2].evidence_sha256
        a4_identity = readback.events[3].evidence_sha256
        if (
            readback.a3_reuse_event_id is None
            or result.assessment.reuse_event_id
            != readback.a3_reuse_event_id
            or _a3_receipt_sha256(result.assessment)
            != a3_receipt_identity
            or result.delivery_context is None
            or _a2_receipt_sha256(result.delivery_context) != a2_identity
            or result.append_result.event.event_sha256 != a4_identity
            or result.append_result.event.receipt_sha256
            != a3_receipt_identity
            or len(result.durable_snapshot.events) != 1
            or result.durable_snapshot.events[0].event_sha256 != a4_identity
        ):
            self._terminal_failure(
                "A5_CONFIRMATION",
                "A5_READ_BACK_LINEAGE_MISMATCH",
                repair_action="RECEIPT_REWRITE",
            )
        identity = _a5_confirmation_sha256(result)
        return self._emit(
            "A5_CONFIRMATION",
            evidence_sha256=identity,
            binding={
                "evidence_type": "FieldNoteMaturityCommitResult",
                "evidence_sha256": identity,
            },
        )

    def record_a6_review(
        self,
        packet: FieldNoteMaturityReviewPacket,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage("A6_REVIEW")
        if not isinstance(packet, FieldNoteMaturityReviewPacket):
            self._terminal_failure("A6_REVIEW", "A6_EVIDENCE_INVALID")
        a4_identity = readback.events[3].evidence_sha256
        if (
            packet.note_identity != readback.captured_note
            or readback.a3_reuse_event_id is None
            or len(packet.ordered_event_reviews) != 1
            or packet.ordered_event_reviews[0].event_id
            != readback.a3_reuse_event_id
            or packet.ordered_event_reviews[0].event_sha256 != a4_identity
            or packet.ledger_identity.chain_head_sha256 != a4_identity
            or packet.evidence_maturity.state != "REUSED"
            or packet.current_serving_policy.derivation != "DELAY"
            or packet.current_serving_policy.automatic_injection is not None
        ):
            self._terminal_failure(
                "A6_REVIEW",
                "A6_EXACT_PACKET_MISMATCH",
                repair_action="RECEIPT_REWRITE",
            )
        identity = _a6_packet_sha256(packet)
        return self._emit(
            "A6_REVIEW",
            evidence_sha256=identity,
            binding={
                "evidence_type": "FieldNoteMaturityReviewPacket",
                "evidence_sha256": identity,
            },
        )

    def record_stage_failure(
        self,
        boundary: WholeFlowBoundary,
        reason: str,
    ) -> None:
        self._terminal_failure(boundary, reason)

    def record_repair(
        self,
        boundary: WholeFlowBoundary,
        reason: str,
        *,
        repair_action: RepairAction,
    ) -> None:
        if repair_action == "NONE":
            raise FieldNoteCreatorLiveValidationError(
                "Repair recording requires a prohibited repair action."
            )
        self._terminal_failure(
            boundary,
            reason,
            repair_action=repair_action,
        )

    def record_retry_replacement(self, reason: str) -> None:
        self._terminal_failure(
            "RUNTIME_ENFORCEMENT",
            reason,
            repair_action="RETRY_REPLACEMENT",
        )
