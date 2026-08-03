"""Durable, append-only Field Notes Lite A4 maturity evidence ledger."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import threading
from typing import Any, Iterator, Mapping

from decision_os.companion.field_notes_model import canonical_json
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteMaturitySummary,
    FieldNoteOutcomeEvaluation,
    FieldNoteReuseReceipt,
    FieldNoteRevisionLink,
    FieldNoteServingPolicyBoundary,
    FieldNoteStructureBinding,
    FieldNoteUseEvidence,
    PromotionPolicyBoundary,
    project_field_note_a3_status,
    summarize_field_note_maturity,
)


LEDGER_EVENT_SCHEMA = "decision-os.field-note-maturity-ledger-event.v0.1"
LEDGER_HEAD_SCHEMA = "decision-os.field-note-maturity-ledger-head.v0.1"
LEDGER_EVENT_KIND = "A3_REUSE"
GENESIS_EVENT_SHA256 = "0" * 64
MAX_LEDGER_BYTES = 8 * 1024 * 1024
MAX_EVENT_BYTES = 128 * 1024
MAX_HEAD_BYTES = 4 * 1024
MAX_EVENTS = 4096

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EVENT_KEYS = frozenset(
    {
        "event_id",
        "event_kind",
        "event_sha256",
        "note_partition_sha256",
        "previous_event_sha256",
        "receipt",
        "receipt_sha256",
        "recorded_at",
        "schema",
        "sequence",
    }
)
_HEAD_KEYS = frozenset(
    {
        "event_chain_head",
        "event_count",
        "head_sha256",
        "note_partition_sha256",
        "schema",
    }
)
_IDENTITY_KEYS = frozenset(
    {"note_path", "field_note_id", "note_sha256", "origin_run_id"}
)
_BINDING_KEYS = frozenset(
    {
        "binding_sha256",
        "end_byte",
        "note",
        "note_size",
        "start_byte",
        "structure_id",
        "structure_sha256",
    }
)
_USE_EVIDENCE_KEYS = frozenset(
    {
        "as_of",
        "evidence_class",
        "evidence_origin",
        "evidence_ref",
        "evidence_sha256",
        "observer_id",
        "observer_relation",
        "reusing_run_id",
        "structure_binding",
    }
)
_RECEIPT_KEYS = frozenset(
    {
        "causal_evidence_ref",
        "causal_evidence_sha256",
        "claimed_outcome",
        "contribution_separated",
        "failure_reason",
        "human_intervention",
        "next_action",
        "note",
        "outcome",
        "outcome_as_of",
        "outcome_confirmation",
        "outcome_observer_id",
        "outcome_observer_relation",
        "outcome_scope",
        "promotion",
        "reevaluation_condition",
        "reusing_run_id",
        "reuse_event_id",
        "revision",
        "state",
        "stop_scope",
        "use_evidence",
    }
)


class FieldNoteMaturityLedgerError(RuntimeError):
    """Base A4 ledger error."""


class FieldNoteMaturityLedgerValidationError(FieldNoteMaturityLedgerError):
    """Input is not a validated A3 reuse event for this Note partition."""


class FieldNoteMaturityLedgerIntegrityError(FieldNoteMaturityLedgerError):
    """Durable ledger bytes fail the bounded integrity contract."""


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json(value).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise FieldNoteMaturityLedgerIntegrityError(f"Invalid {label}.")
    return value


def _require_mapping(
    value: Any,
    keys: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise FieldNoteMaturityLedgerIntegrityError(f"Malformed {label}.")
    return value


def _integrity_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Duplicate JSON member in maturity ledger."
            )
        result[key] = value
    return result


def _validate_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 64:
        raise FieldNoteMaturityLedgerValidationError(
            "Ledger recorded_at is invalid."
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FieldNoteMaturityLedgerValidationError(
            "Ledger recorded_at is invalid."
        ) from exc
    if parsed.tzinfo is None:
        raise FieldNoteMaturityLedgerValidationError(
            "Ledger recorded_at is invalid."
        )
    return value


def _identity_from_dict(value: Any) -> FieldNoteIdentity:
    data = _require_mapping(value, _IDENTITY_KEYS, "Field Note identity")
    try:
        return FieldNoteIdentity(
            note_path=data["note_path"],
            field_note_id=data["field_note_id"],
            note_sha256=data["note_sha256"],
            origin_run_id=data["origin_run_id"],
        )
    except (TypeError, ValueError) as exc:
        raise FieldNoteMaturityLedgerIntegrityError(
            "Malformed Field Note identity."
        ) from exc


def _binding_from_dict(value: Any) -> FieldNoteStructureBinding:
    data = _require_mapping(value, _BINDING_KEYS, "structure binding")
    stored_binding_sha256 = _require_sha256(
        data["binding_sha256"],
        "structure binding digest",
    )
    try:
        binding = FieldNoteStructureBinding(
            note=_identity_from_dict(data["note"]),
            structure_id=data["structure_id"],
            note_size=data["note_size"],
            start_byte=data["start_byte"],
            end_byte=data["end_byte"],
            structure_sha256=data["structure_sha256"],
        )
    except (TypeError, ValueError) as exc:
        raise FieldNoteMaturityLedgerIntegrityError(
            "Malformed structure binding."
        ) from exc
    if binding.binding_sha256 != stored_binding_sha256:
        raise FieldNoteMaturityLedgerIntegrityError(
            "Structure binding identity mismatch."
        )
    return binding


def _use_evidence_from_dict(value: Any) -> FieldNoteUseEvidence:
    data = _require_mapping(value, _USE_EVIDENCE_KEYS, "use evidence")
    try:
        return FieldNoteUseEvidence(
            evidence_class=data["evidence_class"],
            evidence_origin=data["evidence_origin"],
            reusing_run_id=data["reusing_run_id"],
            structure_binding=_binding_from_dict(data["structure_binding"]),
            evidence_ref=data["evidence_ref"],
            evidence_sha256=data["evidence_sha256"],
            observer_id=data["observer_id"],
            observer_relation=data["observer_relation"],
            as_of=data["as_of"],
        )
    except (TypeError, ValueError) as exc:
        raise FieldNoteMaturityLedgerIntegrityError(
            "Malformed use evidence."
        ) from exc


def _revision_from_dict(value: Any) -> FieldNoteRevisionLink:
    data = _require_mapping(
        value,
        frozenset({"predecessor", "successor"}),
        "revision link",
    )
    try:
        return FieldNoteRevisionLink(
            predecessor=_identity_from_dict(data["predecessor"]),
            successor=_identity_from_dict(data["successor"]),
        )
    except (TypeError, ValueError) as exc:
        raise FieldNoteMaturityLedgerIntegrityError(
            "Malformed revision link."
        ) from exc


def _receipt_from_dict(value: Any) -> FieldNoteReuseReceipt:
    data = _require_mapping(value, _RECEIPT_KEYS, "A3 reuse receipt")
    if data["promotion"] != PromotionPolicyBoundary().as_dict():
        raise FieldNoteMaturityLedgerIntegrityError(
            "PROMOTABLE policy boundary is invalid."
        )
    use_evidence = (
        _use_evidence_from_dict(data["use_evidence"])
        if data["use_evidence"] is not None
        else None
    )
    revision = (
        _revision_from_dict(data["revision"])
        if data["revision"] is not None
        else None
    )
    try:
        return FieldNoteReuseReceipt(
            note=_identity_from_dict(data["note"]),
            reusing_run_id=data["reusing_run_id"],
            state=data["state"],
            failure_reason=data["failure_reason"],
            use_evidence=use_evidence,
            claimed_outcome=data["claimed_outcome"],
            outcome=data["outcome"],
            outcome_confirmation=data["outcome_confirmation"],
            outcome_observer_id=data["outcome_observer_id"],
            outcome_observer_relation=data["outcome_observer_relation"],
            outcome_as_of=data["outcome_as_of"],
            outcome_scope=data["outcome_scope"],
            causal_evidence_ref=data["causal_evidence_ref"],
            causal_evidence_sha256=data["causal_evidence_sha256"],
            contribution_separated=data["contribution_separated"],
            human_intervention=data["human_intervention"],
            next_action=data["next_action"],
            reevaluation_condition=data["reevaluation_condition"],
            stop_scope=data["stop_scope"],
            revision=revision,
            reuse_event_id=data["reuse_event_id"],
        )
    except (TypeError, ValueError) as exc:
        raise FieldNoteMaturityLedgerIntegrityError(
            "Malformed A3 reuse receipt."
        ) from exc


def _expected_reuse_event_id(receipt: FieldNoteReuseReceipt) -> str:
    if receipt.use_evidence is None:
        return ""
    payload = {
        "note": receipt.note.as_dict(),
        "reusing_run_id": receipt.reusing_run_id,
        "use_evidence": receipt.use_evidence.as_dict(),
    }
    return _sha256_bytes(_canonical_bytes(payload))


def _validate_reused_receipt(
    receipt: Any,
    note: FieldNoteIdentity,
    note_bytes: bytes,
) -> None:
    if not isinstance(receipt, FieldNoteReuseReceipt):
        raise FieldNoteMaturityLedgerValidationError(
            "Only typed A3 reuse receipts may enter the maturity ledger."
        )
    if (
        receipt.state != "REUSED"
        or receipt.failure_reason is not None
        or receipt.note != note
        or receipt.reusing_run_id == note.origin_run_id
        or receipt.use_evidence is None
        or receipt.use_evidence.reusing_run_id != receipt.reusing_run_id
        or receipt.reuse_event_id != _expected_reuse_event_id(receipt)
        or receipt.promotion != PromotionPolicyBoundary()
        or not receipt.use_evidence.structure_binding.verifies(note, note_bytes)
    ):
        raise FieldNoteMaturityLedgerValidationError(
            "A3 reuse receipt is not valid for this exact Note partition."
        )
    try:
        evaluation = FieldNoteOutcomeEvaluation(
            outcome=receipt.claimed_outcome,
            scope=receipt.outcome_scope,
            observer_id=receipt.outcome_observer_id,
            observer_relation=receipt.outcome_observer_relation,
            as_of=receipt.outcome_as_of,
            causal_evidence_ref=receipt.causal_evidence_ref,
            causal_evidence_sha256=receipt.causal_evidence_sha256,
            contribution_separated=receipt.contribution_separated,
        )
    except (TypeError, ValueError) as exc:
        raise FieldNoteMaturityLedgerValidationError(
            "A3 outcome evidence is malformed."
        ) from exc
    if receipt.outcome_confirmation != evaluation.confirmation:
        raise FieldNoteMaturityLedgerValidationError(
            "A3 outcome confirmation is inconsistent."
        )
    intervention = receipt.human_intervention
    if intervention not in {"NONE", "NON_DECISIVE", "MATERIAL", "UNKNOWN"}:
        raise FieldNoteMaturityLedgerValidationError(
            "A3 human-intervention evidence is malformed."
        )
    expected_outcome = evaluation.outcome
    if (
        intervention in {"MATERIAL", "UNKNOWN"}
        and not evaluation.contribution_separated
    ) or (
        evaluation.outcome != "UNKNOWN"
        and not evaluation.contribution_separated
    ) or (
        evaluation.outcome in {"HELPFUL", "HARMFUL"}
        and not evaluation.has_causal_evidence
    ):
        expected_outcome = "UNKNOWN"
    if receipt.outcome != expected_outcome:
        raise FieldNoteMaturityLedgerValidationError(
            "A3 claimed and effective outcomes are inconsistent."
        )
    action = receipt.next_action
    if receipt.outcome == "UNKNOWN":
        allowed_actions = {"HOLD"}
    elif receipt.outcome == "HELPFUL":
        allowed_actions = {"KEEP", "REVISE"}
    else:
        allowed_actions = {"REVISE", "STOP", "HOLD"}
    if action not in allowed_actions:
        raise FieldNoteMaturityLedgerValidationError(
            "A3 reuse disposition is inconsistent with its outcome."
        )
    if action == "HOLD":
        if (
            not isinstance(receipt.reevaluation_condition, str)
            or not receipt.reevaluation_condition.strip()
            or receipt.stop_scope is not None
            or receipt.revision is not None
        ):
            raise FieldNoteMaturityLedgerValidationError(
                "A3 HOLD disposition is malformed."
            )
    elif action == "STOP":
        if (
            not isinstance(receipt.stop_scope, str)
            or not receipt.stop_scope.strip()
            or receipt.reevaluation_condition is not None
            or receipt.revision is not None
        ):
            raise FieldNoteMaturityLedgerValidationError(
                "A3 STOP disposition is malformed."
            )
    elif action == "REVISE":
        revision = receipt.revision
        if (
            revision is None
            or revision.predecessor != note
            or revision.successor.origin_run_id != receipt.reusing_run_id
            or receipt.reevaluation_condition is not None
            or receipt.stop_scope is not None
        ):
            raise FieldNoteMaturityLedgerValidationError(
                "A3 REVISE disposition is malformed."
            )
    elif (
        receipt.reevaluation_condition is not None
        or receipt.stop_scope is not None
        or receipt.revision is not None
    ):
        raise FieldNoteMaturityLedgerValidationError(
            "A3 KEEP disposition is malformed."
        )


@dataclass(frozen=True)
class FieldNoteMaturityLedgerEvent:
    sequence: int
    recorded_at: str
    note_partition_sha256: str
    previous_event_sha256: str
    event_id: str
    receipt: FieldNoteReuseReceipt
    receipt_sha256: str
    event_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": LEDGER_EVENT_SCHEMA,
            "event_kind": LEDGER_EVENT_KIND,
            "sequence": self.sequence,
            "recorded_at": self.recorded_at,
            "note_partition_sha256": self.note_partition_sha256,
            "previous_event_sha256": self.previous_event_sha256,
            "event_id": self.event_id,
            "receipt": self.receipt.as_dict(),
            "receipt_sha256": self.receipt_sha256,
            "event_sha256": self.event_sha256,
        }


@dataclass(frozen=True)
class FieldNoteMaturityAppendResult:
    appended: bool
    event: FieldNoteMaturityLedgerEvent


@dataclass(frozen=True)
class FieldNoteMaturityLedgerSnapshot:
    note: FieldNoteIdentity
    events: tuple[FieldNoteMaturityLedgerEvent, ...]
    evidence_maturity: FieldNoteMaturitySummary
    current_serving_policy: FieldNoteServingPolicyBoundary
    chain_head_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "note": self.note.as_dict(),
            "events": [event.as_dict() for event in self.events],
            "evidence_maturity": self.evidence_maturity.as_dict(),
            "current_serving_policy": self.current_serving_policy.as_dict(),
            "chain_head_sha256": self.chain_head_sha256,
        }


class FieldNoteMaturityLedger:
    """One exact-Note append-only JSONL partition below a caller-owned root."""

    def __init__(self, root: Path, note: FieldNoteIdentity) -> None:
        if not isinstance(note, FieldNoteIdentity):
            raise FieldNoteMaturityLedgerValidationError(
                "Maturity ledger requires an exact Field Note identity."
            )
        self.root = Path(root)
        self.note = note
        self.note_partition_sha256 = _sha256_bytes(
            _canonical_bytes(note.as_dict())
        )
        self.events_path = self.root / f"{self.note_partition_sha256}.jsonl"
        self.head_path = self.root / f"{self.note_partition_sha256}.head.json"
        self.lock_path = self.root / ".maturity-ledger.lock"
        self._thread_lock = threading.RLock()

    def _assert_root(self) -> None:
        if self.root.is_symlink() or not self.root.is_dir():
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger root is unsafe."
            )

    def _ensure_root(self) -> None:
        if self.root.is_symlink():
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger root is unsafe."
            )
        try:
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(self.root, 0o700)
        except OSError as exc:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger root cannot be created safely."
            ) from exc
        self._assert_root()

    @staticmethod
    def _assert_private_file(path: Path) -> None:
        if path.is_symlink():
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger file is unsafe."
            )
        try:
            mode = path.stat().st_mode
        except OSError as exc:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger file cannot be inspected."
            ) from exc
        if not stat.S_ISREG(mode) or stat.S_IMODE(mode) & 0o077:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger file is unsafe."
            )

    @contextmanager
    def _locked(self, *, write: bool) -> Iterator[bool]:
        with self._thread_lock:
            if write:
                self._ensure_root()
            elif not os.path.lexists(self.root):
                yield False
                return
            else:
                self._assert_root()
            if not write and not self.lock_path.exists():
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger lock boundary is missing."
                )
            if self.lock_path.is_symlink():
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger lock boundary is unsafe."
                )
            flags = os.O_RDWR | os.O_CREAT if write else os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                descriptor = os.open(self.lock_path, flags, 0o600)
                if write:
                    os.fchmod(descriptor, 0o600)
                lock_mode = fcntl.LOCK_EX if write else fcntl.LOCK_SH
                fcntl.flock(descriptor, lock_mode)
                self._assert_private_file(self.lock_path)
            except (OSError, FieldNoteMaturityLedgerIntegrityError) as exc:
                if "descriptor" in locals():
                    os.close(descriptor)
                if isinstance(exc, FieldNoteMaturityLedgerIntegrityError):
                    raise
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger lock boundary failed."
                ) from exc
            try:
                yield True
            finally:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)

    def _event_from_dict(
        self,
        value: Any,
        *,
        expected_sequence: int,
        expected_previous: str,
        note_bytes: bytes,
    ) -> FieldNoteMaturityLedgerEvent:
        data = _require_mapping(value, _EVENT_KEYS, "maturity event")
        if data["schema"] != LEDGER_EVENT_SCHEMA:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Unsupported maturity ledger event version."
            )
        if data["event_kind"] != LEDGER_EVENT_KIND:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Unsupported maturity ledger event kind."
            )
        if (
            type(data["sequence"]) is not int
            or data["sequence"] != expected_sequence
        ):
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger sequence is invalid."
            )
        try:
            recorded_at = _validate_timestamp(data["recorded_at"])
        except FieldNoteMaturityLedgerValidationError as exc:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger recorded_at is invalid."
            ) from exc
        partition = _require_sha256(
            data["note_partition_sha256"],
            "Note partition digest",
        )
        previous = _require_sha256(
            data["previous_event_sha256"],
            "previous-event digest",
        )
        event_id = _require_sha256(data["event_id"], "reuse event identity")
        receipt_sha256 = _require_sha256(
            data["receipt_sha256"],
            "receipt digest",
        )
        event_sha256 = _require_sha256(
            data["event_sha256"],
            "event digest",
        )
        if partition != self.note_partition_sha256 or previous != expected_previous:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger identity chain is invalid."
            )
        receipt = _receipt_from_dict(data["receipt"])
        if receipt_sha256 != _sha256_bytes(_canonical_bytes(receipt.as_dict())):
            raise FieldNoteMaturityLedgerIntegrityError(
                "A3 receipt payload was mutated."
            )
        try:
            _validate_reused_receipt(receipt, self.note, note_bytes)
        except FieldNoteMaturityLedgerValidationError as exc:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Stored A3 receipt is invalid."
            ) from exc
        if event_id != receipt.reuse_event_id:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Reuse event identity mismatch."
            )
        body = {key: item for key, item in data.items() if key != "event_sha256"}
        if event_sha256 != _sha256_bytes(_canonical_bytes(body)):
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity event payload was mutated."
            )
        return FieldNoteMaturityLedgerEvent(
            sequence=expected_sequence,
            recorded_at=recorded_at,
            note_partition_sha256=partition,
            previous_event_sha256=previous,
            event_id=event_id,
            receipt=receipt,
            receipt_sha256=receipt_sha256,
            event_sha256=event_sha256,
        )

    def _read_head_unlocked(self) -> tuple[int, str]:
        if not os.path.lexists(self.head_path):
            if os.path.lexists(self.events_path):
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger head anchor is missing."
                )
            return 0, GENESIS_EVENT_SHA256
        self._assert_private_file(self.head_path)
        try:
            if self.head_path.stat().st_size > MAX_HEAD_BYTES:
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger head anchor is oversized."
                )
            raw = self.head_path.read_bytes()
            parsed = json.loads(raw, object_pairs_hook=_integrity_object)
        except FieldNoteMaturityLedgerIntegrityError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger head anchor is malformed."
            ) from exc
        data = _require_mapping(parsed, _HEAD_KEYS, "maturity ledger head")
        if _canonical_bytes(data) != raw or data["schema"] != LEDGER_HEAD_SCHEMA:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger head anchor is malformed."
            )
        event_count = data["event_count"]
        if (
            type(event_count) is not int
            or event_count < 0
            or event_count > MAX_EVENTS
        ):
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger head count is invalid."
            )
        partition = _require_sha256(
            data["note_partition_sha256"],
            "head Note partition digest",
        )
        event_chain_head = _require_sha256(
            data["event_chain_head"],
            "head event-chain digest",
        )
        head_sha256 = _require_sha256(data["head_sha256"], "head digest")
        body = {key: item for key, item in data.items() if key != "head_sha256"}
        if (
            partition != self.note_partition_sha256
            or head_sha256 != _sha256_bytes(_canonical_bytes(body))
            or (event_count == 0) != (event_chain_head == GENESIS_EVENT_SHA256)
        ):
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger head anchor is invalid."
            )
        return event_count, event_chain_head

    def _write_head_unlocked(self, event_count: int, event_chain_head: str) -> None:
        body = {
            "schema": LEDGER_HEAD_SCHEMA,
            "note_partition_sha256": self.note_partition_sha256,
            "event_count": event_count,
            "event_chain_head": event_chain_head,
        }
        payload = _canonical_bytes(
            {
                **body,
                "head_sha256": _sha256_bytes(_canonical_bytes(body)),
            }
        )
        if os.path.lexists(self.head_path):
            self._assert_private_file(self.head_path)
        temporary = self.root / (
            f".{self.note_partition_sha256}.{os.getpid()}."
            f"{threading.get_ident()}.tmp"
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor: int | None = None
        try:
            descriptor = os.open(temporary, flags, 0o600)
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("short maturity ledger head write")
                view = view[written:]
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = None
            os.replace(temporary, self.head_path)
            parent = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(parent)
            finally:
                os.close(parent)
        except OSError as exc:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger head anchor cannot be published."
            ) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass

    def _read_events_unlocked(
        self,
        note_bytes: bytes,
    ) -> tuple[FieldNoteMaturityLedgerEvent, ...]:
        anchored_count, anchored_head = self._read_head_unlocked()
        if not os.path.lexists(self.events_path):
            if anchored_count != 0:
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger event history is missing."
                )
            return ()
        self._assert_private_file(self.events_path)
        try:
            raw = self.events_path.read_bytes()
        except OSError as exc:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger cannot be read."
            ) from exc
        if (
            not raw
            or len(raw) > MAX_LEDGER_BYTES
            or not raw.endswith(b"\n")
        ):
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger is oversized or truncated."
            )
        lines = raw.splitlines()
        if len(lines) > MAX_EVENTS:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger event bound was exceeded."
            )
        events: list[FieldNoteMaturityLedgerEvent] = []
        previous = GENESIS_EVENT_SHA256
        seen_event_ids: set[str] = set()
        for sequence, line in enumerate(lines):
            if not line or len(line) > MAX_EVENT_BYTES:
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger event is malformed or oversized."
                )
            try:
                parsed = json.loads(
                    line,
                    object_pairs_hook=_integrity_object,
                )
            except FieldNoteMaturityLedgerIntegrityError:
                raise
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger event is malformed."
                ) from exc
            if not isinstance(parsed, dict) or _canonical_bytes(parsed) != line:
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger event is not canonical."
                )
            event = self._event_from_dict(
                parsed,
                expected_sequence=sequence,
                expected_previous=previous,
                note_bytes=note_bytes,
            )
            if event.event_id in seen_event_ids:
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Duplicate reuse event replay detected."
                )
            seen_event_ids.add(event.event_id)
            events.append(event)
            previous = event.event_sha256
        if anchored_count != len(events) or anchored_head != previous:
            raise FieldNoteMaturityLedgerIntegrityError(
                "Maturity ledger head does not match its event history."
            )
        return tuple(events)

    def read_events(
        self,
        *,
        note_bytes: bytes,
    ) -> tuple[FieldNoteMaturityLedgerEvent, ...]:
        if not isinstance(note_bytes, bytes) or _sha256_bytes(note_bytes) != (
            self.note.note_sha256
        ):
            raise FieldNoteMaturityLedgerValidationError(
                "Current Note bytes do not match the ledger partition identity."
            )
        with self._locked(write=False) as available:
            if not available:
                return ()
            return self._read_events_unlocked(note_bytes)

    def append_receipt(
        self,
        receipt: FieldNoteReuseReceipt,
        *,
        note_bytes: bytes,
        recorded_at: str,
    ) -> FieldNoteMaturityAppendResult:
        _validate_reused_receipt(receipt, self.note, note_bytes)
        recorded_at = _validate_timestamp(recorded_at)
        with self._locked(write=True):
            events = self._read_events_unlocked(note_bytes)
            if not os.path.lexists(self.head_path):
                self._write_head_unlocked(0, GENESIS_EVENT_SHA256)
            receipt_bytes = _canonical_bytes(receipt.as_dict())
            for event in events:
                if event.event_id != receipt.reuse_event_id:
                    continue
                if _canonical_bytes(event.receipt.as_dict()) != receipt_bytes:
                    raise FieldNoteMaturityLedgerValidationError(
                        "Reuse event identity collides with different evidence."
                    )
                return FieldNoteMaturityAppendResult(False, event)
            if len(events) >= MAX_EVENTS:
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger event bound was exceeded."
                )
            body = {
                "schema": LEDGER_EVENT_SCHEMA,
                "event_kind": LEDGER_EVENT_KIND,
                "sequence": len(events),
                "recorded_at": recorded_at,
                "note_partition_sha256": self.note_partition_sha256,
                "previous_event_sha256": (
                    events[-1].event_sha256
                    if events
                    else GENESIS_EVENT_SHA256
                ),
                "event_id": receipt.reuse_event_id,
                "receipt": receipt.as_dict(),
                "receipt_sha256": _sha256_bytes(receipt_bytes),
            }
            event_data = {
                **body,
                "event_sha256": _sha256_bytes(_canonical_bytes(body)),
            }
            payload = _canonical_bytes(event_data) + b"\n"
            if self.events_path.exists():
                self._assert_private_file(self.events_path)
                current_size = self.events_path.stat().st_size
            else:
                current_size = 0
            if len(payload) > MAX_EVENT_BYTES or (
                current_size + len(payload) > MAX_LEDGER_BYTES
            ):
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger size bound was exceeded."
                )
            created = not self.events_path.exists()
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                descriptor = os.open(self.events_path, flags, 0o600)
                os.fchmod(descriptor, 0o600)
                view = memoryview(payload)
                while view:
                    written = os.write(descriptor, view)
                    if written <= 0:
                        raise OSError("short maturity ledger append")
                    view = view[written:]
                os.fsync(descriptor)
            except OSError as exc:
                raise FieldNoteMaturityLedgerIntegrityError(
                    "Maturity ledger append failed."
                ) from exc
            finally:
                if "descriptor" in locals():
                    os.close(descriptor)
            if created:
                try:
                    parent = os.open(self.root, os.O_RDONLY)
                    try:
                        os.fsync(parent)
                    finally:
                        os.close(parent)
                except OSError as exc:
                    raise FieldNoteMaturityLedgerIntegrityError(
                        "Maturity ledger directory sync failed."
                    ) from exc
            event = self._event_from_dict(
                event_data,
                expected_sequence=len(events),
                expected_previous=body["previous_event_sha256"],
                note_bytes=note_bytes,
            )
            self._write_head_unlocked(len(events) + 1, event.event_sha256)
            return FieldNoteMaturityAppendResult(True, event)

    def reconstruct(
        self,
        *,
        note_bytes: bytes,
    ) -> FieldNoteMaturityLedgerSnapshot:
        events = self.read_events(note_bytes=note_bytes)
        maturity = summarize_field_note_maturity(
            self.note,
            tuple(event.receipt for event in events),
        )
        projection = project_field_note_a3_status(
            maturity,
            serving_delay_reason=(
                "A4 does not derive Current Serving Policy from maturity history."
            ),
        )
        return FieldNoteMaturityLedgerSnapshot(
            note=self.note,
            events=events,
            evidence_maturity=projection.evidence_maturity,
            current_serving_policy=projection.current_serving_policy,
            chain_head_sha256=(
                events[-1].event_sha256 if events else GENESIS_EVENT_SHA256
            ),
        )
