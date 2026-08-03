"""Pure Field Notes Lite A5 bridge from A3 assessment to A4 durability."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from typing import Any, Literal

from decision_os.companion.field_notes_maturity_ledger import (
    FieldNoteMaturityAppendResult,
    FieldNoteMaturityLedger,
    FieldNoteMaturityLedgerSnapshot,
)
from decision_os.companion.field_notes_reconnect import (
    FieldNoteReconnectReceipt,
)
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteReuseClaim,
    FieldNoteReuseReceipt,
    assess_field_note_reuse,
)


MaturityCommitStatus = Literal[
    "NOT_REUSED",
    "RECORDED",
    "ALREADY_RECORDED",
]


class FieldNoteMaturityCommitError(RuntimeError):
    """Base error for an A5 commit that cannot be durably confirmed."""


class FieldNoteMaturityCommitValidationError(
    FieldNoteMaturityCommitError,
    ValueError,
):
    """The typed A5 request or A4 partition identity is invalid."""


class FieldNoteMaturityCommitConfirmationError(FieldNoteMaturityCommitError):
    """A4 read-back did not confirm the exact assessed reuse event."""


def _validate_recorded_at(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 64:
        raise FieldNoteMaturityCommitValidationError(
            "Maturity commit recorded_at is invalid."
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FieldNoteMaturityCommitValidationError(
            "Maturity commit recorded_at is invalid."
        ) from exc
    if parsed.tzinfo is None:
        raise FieldNoteMaturityCommitValidationError(
            "Maturity commit recorded_at is invalid."
        )
    return value


def _validate_delivery_context(
    context: FieldNoteReconnectReceipt | None,
    *,
    note: FieldNoteIdentity,
    note_byte_count: int,
    reusing_run_id: str | None,
) -> None:
    if context is None:
        return
    if not isinstance(context, FieldNoteReconnectReceipt):
        raise FieldNoteMaturityCommitValidationError(
            "Maturity commit delivery context is not a typed A2 receipt."
        )
    if (
        context.state not in {"INJECTED", "ACTIVATION_UNKNOWN"}
        or context.full_notes_injected != 1
    ):
        raise FieldNoteMaturityCommitValidationError(
            "Maturity commit A2 delivery context is not injected."
        )
    if (
        context.selected_field_note_path != note.note_path
        or context.selected_field_note_id != note.field_note_id
        or context.selected_full_note_sha256 != note.note_sha256
        or context.full_note_bytes_read != note_byte_count
    ):
        raise FieldNoteMaturityCommitValidationError(
            "Maturity commit A2 delivery context does not match the exact Field Note."
        )
    if reusing_run_id is not None and context.run_id != reusing_run_id:
        raise FieldNoteMaturityCommitValidationError(
            "Maturity commit A2 delivery context belongs to a different reusing Run."
        )


@dataclass(frozen=True)
class FieldNoteMaturityCommitRequest:
    """Exact Note, bounded A3 claim, and optional non-authoritative A2 context."""

    note: FieldNoteIdentity
    note_bytes: bytes = field(repr=False)
    reuse_claim: FieldNoteReuseClaim | None
    recorded_at: str
    delivery_context: FieldNoteReconnectReceipt | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.note, FieldNoteIdentity):
            raise FieldNoteMaturityCommitValidationError(
                "Maturity commit requires an exact Field Note identity."
            )
        if (
            not isinstance(self.note_bytes, bytes)
            or hashlib.sha256(self.note_bytes).hexdigest()
            != self.note.note_sha256
        ):
            raise FieldNoteMaturityCommitValidationError(
                "Maturity commit Note bytes do not match the exact identity."
            )
        if self.reuse_claim is not None and not isinstance(
            self.reuse_claim,
            FieldNoteReuseClaim,
        ):
            raise FieldNoteMaturityCommitValidationError(
                "Maturity commit reuse claim is not typed A3 evidence."
            )
        _validate_delivery_context(
            self.delivery_context,
            note=self.note,
            note_byte_count=len(self.note_bytes),
            reusing_run_id=(
                self.reuse_claim.reusing_run_id
                if self.reuse_claim is not None
                else None
            ),
        )
        object.__setattr__(
            self,
            "recorded_at",
            _validate_recorded_at(self.recorded_at),
        )


@dataclass(frozen=True)
class FieldNoteMaturityCommitResult:
    """Typed A5 result; committed states always contain verified A4 read-back."""

    status: MaturityCommitStatus
    assessment: FieldNoteReuseReceipt
    delivery_context: FieldNoteReconnectReceipt | None
    append_result: FieldNoteMaturityAppendResult | None
    durable_snapshot: FieldNoteMaturityLedgerSnapshot | None

    def __post_init__(self) -> None:
        if self.status not in {
            "NOT_REUSED",
            "RECORDED",
            "ALREADY_RECORDED",
        }:
            raise ValueError("Maturity commit result status is invalid.")
        if not isinstance(self.assessment, FieldNoteReuseReceipt):
            raise ValueError("Maturity commit result lacks its A3 assessment.")
        if self.delivery_context is not None and not isinstance(
            self.delivery_context,
            FieldNoteReconnectReceipt,
        ):
            raise ValueError("Maturity commit result has invalid A2 provenance.")
        if self.status == "NOT_REUSED":
            if (
                self.assessment.state != "CANDIDATE"
                or self.append_result is not None
                or self.durable_snapshot is not None
            ):
                raise ValueError(
                    "NOT_REUSED cannot contain a durable maturity commit."
                )
            return
        if (
            self.assessment.state != "REUSED"
            or self.assessment.use_evidence is None
            or self.append_result is None
            or self.durable_snapshot is None
            or self.append_result.appended != (self.status == "RECORDED")
        ):
            raise ValueError(
                "Committed maturity result lacks confirmed A4 evidence."
            )
        _validate_delivery_context(
            self.delivery_context,
            note=self.assessment.note,
            note_byte_count=(
                self.assessment.use_evidence.structure_binding.note_size
            ),
            reusing_run_id=self.assessment.reusing_run_id,
        )
        matching = tuple(
            event
            for event in self.durable_snapshot.events
            if event.event_id == self.assessment.reuse_event_id
        )
        if (
            self.durable_snapshot.note != self.assessment.note
            or self.durable_snapshot.evidence_maturity.state != "REUSED"
            or self.assessment.reuse_event_id
            not in self.durable_snapshot.evidence_maturity.reuse_event_ids
            or matching != (self.append_result.event,)
            or matching[0].receipt != self.assessment
        ):
            raise ValueError(
                "Committed maturity result is not confirmed by A4 read-back."
            )

    @property
    def durable_commit_confirmed(self) -> bool:
        return self.status in {"RECORDED", "ALREADY_RECORDED"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "durable_commit_confirmed": self.durable_commit_confirmed,
            "assessment": self.assessment.as_dict(),
            "delivery_context": (
                self.delivery_context.as_dict()
                if self.delivery_context is not None
                else None
            ),
            "append_result": (
                {
                    "appended": self.append_result.appended,
                    "event": self.append_result.event.as_dict(),
                }
                if self.append_result is not None
                else None
            ),
            "durable_snapshot": (
                self.durable_snapshot.as_dict()
                if self.durable_snapshot is not None
                else None
            ),
        }


def _confirm_read_back(
    receipt: FieldNoteReuseReceipt,
    append_result: FieldNoteMaturityAppendResult,
    snapshot: FieldNoteMaturityLedgerSnapshot,
) -> None:
    matching = tuple(
        event
        for event in snapshot.events
        if event.event_id == receipt.reuse_event_id
    )
    if (
        snapshot.note != receipt.note
        or snapshot.evidence_maturity.state != "REUSED"
        or receipt.reuse_event_id
        not in snapshot.evidence_maturity.reuse_event_ids
        or matching != (append_result.event,)
        or matching[0].receipt != receipt
    ):
        raise FieldNoteMaturityCommitConfirmationError(
            "A4 read-back did not confirm the exact A3 reuse event."
        )


def commit_field_note_maturity(
    ledger: FieldNoteMaturityLedger,
    request: FieldNoteMaturityCommitRequest,
) -> FieldNoteMaturityCommitResult:
    """Assess through A3 and report completion only after exact A4 read-back."""

    if not isinstance(ledger, FieldNoteMaturityLedger):
        raise FieldNoteMaturityCommitValidationError(
            "Maturity commit requires a typed A4 ledger."
        )
    if not isinstance(request, FieldNoteMaturityCommitRequest):
        raise FieldNoteMaturityCommitValidationError(
            "Maturity commit request is not typed."
        )
    if ledger.note != request.note:
        raise FieldNoteMaturityCommitValidationError(
            "Maturity commit request targets a different A4 Note partition."
        )
    assessment = assess_field_note_reuse(
        request.note,
        request.reuse_claim,
        note_bytes=request.note_bytes,
    )
    if assessment.state != "REUSED":
        return FieldNoteMaturityCommitResult(
            status="NOT_REUSED",
            assessment=assessment,
            delivery_context=request.delivery_context,
            append_result=None,
            durable_snapshot=None,
        )
    append_result = ledger.append_receipt(
        assessment,
        note_bytes=request.note_bytes,
        recorded_at=request.recorded_at,
    )
    snapshot = ledger.reconstruct(note_bytes=request.note_bytes)
    _confirm_read_back(assessment, append_result, snapshot)
    return FieldNoteMaturityCommitResult(
        status="RECORDED" if append_result.appended else "ALREADY_RECORDED",
        assessment=assessment,
        delivery_context=request.delivery_context,
        append_result=append_result,
        durable_snapshot=snapshot,
    )
