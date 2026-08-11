"""One persisted, exact, addressability-only Field Note reconnect edge.

This module deliberately does not integrate with Field Note selection,
injection, serving, promotion, authority, or Worker dispatch.  It reads one
fixed edge record, verifies one exact Note and byte-range binding, performs a
separate current-applicability comparison, and returns the bound bytes or a
fail-closed HOLD result.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
from typing import Any, Literal, Mapping

from decision_os.acceleration.model import (
    RepositoryIdentityError,
    git_output,
    git_root,
    repository_id,
)
from decision_os.companion.field_notes_model import canonical_json
from decision_os.companion.field_notes_reconnect import (
    FieldNoteExactRead,
    FieldNoteExactReadError,
    read_exact_field_note,
)
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteServingPolicyBoundary,
    FieldNoteStructureBinding,
)


SELECTIVE_RECONNECT_SCHEMA = "decision-os.selective-reconnect-edge.v1.01"
SELECTIVE_RECONNECT_RECEIPT_SCHEMA = (
    "decision-os.selective-reconnect-receipt.v1.01"
)
SELECTIVE_RECONNECT_SOURCE_EVIDENCE_SCHEMA = (
    "decision-os.selective-reconnect-source-evidence.v1.01"
)
SELECTIVE_RECONNECT_EDGE_PATH = (
    ".decision-os/selective-reconnect/edge-v1.jsonl"
)
MAX_EDGE_FILE_BYTES = 128 * 1024
MAX_SOURCE_EVIDENCE_BYTES = 8 * 1024 * 1024

V13Gate = Literal["GO", "HOLD", "CAP", "BLOCK"]
SelectiveReconnectState = Literal["RECALLED", "DELAY_HOLD"]
SelectiveReconnectFailure = Literal[
    "ZERO_TARGETS",
    "MULTIPLE_TARGETS",
    "CORRUPTED_EDGE",
    "GOAL_IDENTITY_MISMATCH",
    "GAP_IDENTITY_MISMATCH",
    "CURRENT_GATE_MISMATCH",
    "PROTECTED_OBJECT_MISMATCH",
    "AUTHORITY_BOUNDARY_MISMATCH",
    "AS_OF_MISMATCH",
    "TARGET_IDENTITY_MISMATCH",
    "STALE_TARGET",
    "SOURCE_IDENTITY_MISMATCH",
    "SOURCE_EVIDENCE_FAILURE",
    "SCOPE_MISMATCH",
    "STALE_EVIDENCE",
    "CURRENT_REPOSITORY_MISMATCH",
    "UNSUPPORTED_APPLICABILITY_ROUTE",
    "UNSTABLE_RECOVERY_WINDOW",
]

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_RFC3339_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?"
    r"(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
_CURRENT_KEYS = frozenset(
    {
        "as_of",
        "authority_boundary",
        "binding_sha256",
        "current_gate",
        "goal",
        "protected_object",
        "repository_id",
        "remaining_gap",
        "as_of_commit",
    }
)
_IDENTITY_KEYS = frozenset({"identity", "sha256"})
_SOURCE_KEYS = frozenset(
    {
        "as_of",
        "evidence_path",
        "evidence_sha256",
        "repository_id",
        "source_blob",
        "source_commit",
        "source_path",
        "source_sha256",
    }
)
_NOTE_KEYS = frozenset(
    {"field_note_id", "note_path", "note_sha256", "origin_run_id"}
)
_STRUCTURE_KEYS = frozenset(
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
_TARGET_KEYS = frozenset(
    {
        "binding_sha256",
        "recheck_conditions",
        "reentry_path",
        "scope",
        "source",
        "stop_conditions",
        "structure",
        "unresolved_delta",
    }
)
_SERVING_POLICY_KEYS = frozenset(
    {
        "authority_precedence",
        "automatic_derivation_supported",
        "automatic_injection",
        "complete_state_machine_implemented",
        "delay_reason",
        "derivation",
        "forward_only_extension",
        "note",
    }
)
_APPLICABILITY_KEYS = frozenset(
    {
        "binding_sha256",
        "current",
        "evidence_stale",
        "scope",
        "serving_policy",
        "source",
        "target_binding_sha256",
        "target_current_gate",
        "target_status_as_of",
    }
)
_EDGE_KEYS = frozenset(
    {"applicability", "current", "edge_sha256", "schema", "target"}
)


class _DuplicateKey(ValueError):
    pass


class _ExactFileError(RuntimeError):
    pass


@dataclass(frozen=True)
class _ExactRepositoryFileRead:
    data: bytes
    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey("Duplicate JSON key.")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ValueError("Non-finite JSON constants are unsupported.")


def _bounded_text(value: Any, label: str, *, maximum: int = 2048) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text.")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > maximum
        or "\x00" in normalized
        or "\r" in normalized
    ):
        raise ValueError(f"{label} is outside its bounded schema.")
    try:
        normalized.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{label} is not valid UTF-8 text.") from exc
    return normalized


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest.")
    return value


def _as_of(value: Any) -> str:
    normalized = _bounded_text(value, "As-of", maximum=64)
    if _RFC3339_RE.fullmatch(normalized) is None:
        raise ValueError("As-of must be strict RFC 3339.")
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("As-of must be RFC 3339.") from exc
    if parsed.tzinfo is None:
        raise ValueError("As-of must be timezone-aware.")
    return normalized


def _relative_path(value: Any, label: str, *, maximum: int = 1024) -> str:
    normalized = _bounded_text(value, label, maximum=maximum)
    path = PurePosixPath(normalized)
    if (
        path.is_absolute()
        or normalized.startswith("./")
        or normalized.endswith("/")
        or "\\" in normalized
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != normalized
    ):
        raise ValueError(f"{label} must be a canonical relative path.")
    return normalized


def _conditions(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)) or not 1 <= len(value) <= 8:
        raise ValueError(f"{label} must contain one to eight items.")
    result = tuple(
        _bounded_text(item, label, maximum=1024) for item in value
    )
    if len(set(result)) != len(result):
        raise ValueError(f"{label} contains duplicates.")
    return result


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def selective_reconnect_source_evidence_bytes(
    *,
    repository_id: str,
    source_commit: str,
    source_path: str,
    source_blob: str,
    source_sha256: str,
    evidence_path: str,
    as_of: str,
) -> bytes:
    """Build the narrow canonical evidence record bound to one source tuple."""

    checked_repository = _bounded_text(
        repository_id,
        "Source repository",
        maximum=512,
    )
    if not isinstance(source_commit, str) or _COMMIT_RE.fullmatch(source_commit) is None:
        raise ValueError("Source commit must be a lowercase 40-character ID.")
    if not isinstance(source_blob, str) or _COMMIT_RE.fullmatch(source_blob) is None:
        raise ValueError("Source blob must be a lowercase 40-character ID.")
    payload = {
        "schema": SELECTIVE_RECONNECT_SOURCE_EVIDENCE_SCHEMA,
        "repository_id": checked_repository,
        "source_commit": source_commit,
        "source_path": _relative_path(source_path, "Source artifact path"),
        "source_blob": source_blob,
        "source_sha256": _sha256(source_sha256, "Source artifact digest"),
        "evidence_path": _relative_path(evidence_path, "Source-evidence path"),
        "as_of": _as_of(as_of),
    }
    return canonical_json(payload).encode("utf-8") + b"\n"


def _mapping(value: Any, keys: frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} has an invalid shape.")
    return value


@dataclass(frozen=True)
class SelectiveReconnectIdentity:
    """An exact named current or applicability identity."""

    identity: str
    sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "identity",
            _bounded_text(self.identity, "Identity", maximum=512),
        )
        object.__setattr__(self, "sha256", _sha256(self.sha256, "Identity digest"))

    def as_dict(self) -> dict[str, str]:
        return {"identity": self.identity, "sha256": self.sha256}


@dataclass(frozen=True)
class SelectiveReconnectCurrentBinding:
    """The one exact current Goal/gap condition that may address the edge."""

    goal: SelectiveReconnectIdentity
    remaining_gap: SelectiveReconnectIdentity
    current_gate: V13Gate
    protected_object: SelectiveReconnectIdentity
    authority_boundary: SelectiveReconnectIdentity
    repository_id: str
    as_of_commit: str
    as_of: str

    def __post_init__(self) -> None:
        identities = (
            self.goal,
            self.remaining_gap,
            self.protected_object,
            self.authority_boundary,
        )
        if any(not isinstance(item, SelectiveReconnectIdentity) for item in identities):
            raise ValueError("Current-side edge identities are invalid.")
        if self.current_gate not in {"GO", "HOLD", "CAP", "BLOCK"}:
            raise ValueError("Current Gate is invalid.")
        object.__setattr__(
            self,
            "repository_id",
            _bounded_text(self.repository_id, "Current repository", maximum=512),
        )
        if not isinstance(self.as_of_commit, str) or _COMMIT_RE.fullmatch(
            self.as_of_commit
        ) is None:
            raise ValueError("Current As-of commit must be a lowercase commit ID.")
        object.__setattr__(self, "as_of", _as_of(self.as_of))

    def _payload(self) -> dict[str, Any]:
        return {
            "goal": self.goal.as_dict(),
            "remaining_gap": self.remaining_gap.as_dict(),
            "current_gate": self.current_gate,
            "protected_object": self.protected_object.as_dict(),
            "authority_boundary": self.authority_boundary.as_dict(),
            "repository_id": self.repository_id,
            "as_of_commit": self.as_of_commit,
            "as_of": self.as_of,
        }

    @property
    def binding_sha256(self) -> str:
        return _digest(self._payload())

    def as_dict(self) -> dict[str, Any]:
        return {**self._payload(), "binding_sha256": self.binding_sha256}


@dataclass(frozen=True)
class SelectiveReconnectSourceAnchor:
    """Exact source identity plus one locally verifiable evidence artifact."""

    repository_id: str
    source_commit: str
    source_path: str
    source_blob: str
    source_sha256: str
    evidence_path: str
    evidence_sha256: str
    as_of: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "repository_id",
            _bounded_text(self.repository_id, "Source repository", maximum=512),
        )
        if not isinstance(self.source_commit, str) or _COMMIT_RE.fullmatch(
            self.source_commit
        ) is None:
            raise ValueError("Source commit must be a lowercase 40-character ID.")
        object.__setattr__(
            self,
            "source_path",
            _relative_path(self.source_path, "Source artifact path"),
        )
        if not isinstance(self.source_blob, str) or _COMMIT_RE.fullmatch(
            self.source_blob
        ) is None:
            raise ValueError("Source blob must be a lowercase 40-character ID.")
        object.__setattr__(
            self,
            "source_sha256",
            _sha256(self.source_sha256, "Source artifact digest"),
        )
        object.__setattr__(
            self,
            "evidence_path",
            _relative_path(self.evidence_path, "Source-evidence path"),
        )
        object.__setattr__(
            self,
            "evidence_sha256",
            _sha256(self.evidence_sha256, "Source-evidence digest"),
        )
        object.__setattr__(self, "as_of", _as_of(self.as_of))

    def as_dict(self) -> dict[str, str]:
        return {
            "repository_id": self.repository_id,
            "source_commit": self.source_commit,
            "source_path": self.source_path,
            "source_blob": self.source_blob,
            "source_sha256": self.source_sha256,
            "evidence_path": self.evidence_path,
            "evidence_sha256": self.evidence_sha256,
            "as_of": self.as_of,
        }


@dataclass(frozen=True)
class SelectiveReconnectTargetBinding:
    """One exact structure and the V11-critical facts needed for re-entry."""

    structure: FieldNoteStructureBinding
    source: SelectiveReconnectSourceAnchor
    scope: SelectiveReconnectIdentity
    stop_conditions: tuple[str, ...]
    recheck_conditions: tuple[str, ...]
    unresolved_delta: str
    reentry_path: str

    def __post_init__(self) -> None:
        if not isinstance(self.structure, FieldNoteStructureBinding):
            raise ValueError("Reconnect target lacks an exact structure binding.")
        if not isinstance(self.source, SelectiveReconnectSourceAnchor):
            raise ValueError("Reconnect target lacks an exact source anchor.")
        if not isinstance(self.scope, SelectiveReconnectIdentity):
            raise ValueError("Reconnect target scope is invalid.")
        object.__setattr__(
            self,
            "stop_conditions",
            _conditions(self.stop_conditions, "Stop conditions"),
        )
        object.__setattr__(
            self,
            "recheck_conditions",
            _conditions(self.recheck_conditions, "Recheck conditions"),
        )
        object.__setattr__(
            self,
            "unresolved_delta",
            _bounded_text(self.unresolved_delta, "Unresolved delta"),
        )
        object.__setattr__(
            self,
            "reentry_path",
            _relative_path(self.reentry_path, "Re-entry path"),
        )
        if self.reentry_path != self.structure.note.note_path:
            raise ValueError("Re-entry path does not identify the bound Field Note.")

    def _payload(self) -> dict[str, Any]:
        return {
            "structure": self.structure.as_dict(),
            "source": self.source.as_dict(),
            "scope": self.scope.as_dict(),
            "stop_conditions": list(self.stop_conditions),
            "recheck_conditions": list(self.recheck_conditions),
            "unresolved_delta": self.unresolved_delta,
            "reentry_path": self.reentry_path,
        }

    @property
    def binding_sha256(self) -> str:
        return _digest(self._payload())

    def as_dict(self) -> dict[str, Any]:
        return {**self._payload(), "binding_sha256": self.binding_sha256}


@dataclass(frozen=True)
class SelectiveReconnectEdge:
    """The only record admitted by Selective Reconnect Edge 1.01."""

    current: SelectiveReconnectCurrentBinding
    target: SelectiveReconnectTargetBinding
    applicability: SelectiveReconnectApplicability

    def __post_init__(self) -> None:
        if (
            not isinstance(self.current, SelectiveReconnectCurrentBinding)
            or not isinstance(self.target, SelectiveReconnectTargetBinding)
            or not isinstance(
                self.applicability,
                SelectiveReconnectApplicability,
            )
        ):
            raise ValueError("Selective reconnect edge is invalid.")

    def _payload(self) -> dict[str, Any]:
        return {
            "schema": SELECTIVE_RECONNECT_SCHEMA,
            "current": self.current.as_dict(),
            "target": self.target.as_dict(),
            "applicability": self.applicability.as_dict(),
        }

    @property
    def edge_sha256(self) -> str:
        return _digest(self._payload())

    def as_dict(self) -> dict[str, Any]:
        return {**self._payload(), "edge_sha256": self.edge_sha256}


@dataclass(frozen=True)
class SelectiveReconnectApplicability:
    """Persisted current-use evidence checked only after target recovery."""

    current: SelectiveReconnectCurrentBinding
    target_binding_sha256: str
    source: SelectiveReconnectSourceAnchor
    scope: SelectiveReconnectIdentity
    target_current_gate: V13Gate
    target_status_as_of: str
    evidence_stale: bool
    serving_policy: FieldNoteServingPolicyBoundary

    def __post_init__(self) -> None:
        if not isinstance(self.current, SelectiveReconnectCurrentBinding):
            raise ValueError("Applicability current binding is invalid.")
        object.__setattr__(
            self,
            "target_binding_sha256",
            _sha256(self.target_binding_sha256, "Applicability target digest"),
        )
        if not isinstance(self.source, SelectiveReconnectSourceAnchor):
            raise ValueError("Applicability source is invalid.")
        if not isinstance(self.scope, SelectiveReconnectIdentity):
            raise ValueError("Applicability scope is invalid.")
        if self.target_current_gate not in {"GO", "HOLD", "CAP", "BLOCK"}:
            raise ValueError("Target current-use Gate is invalid.")
        object.__setattr__(self, "target_status_as_of", _as_of(self.target_status_as_of))
        if type(self.evidence_stale) is not bool:
            raise ValueError("Applicability staleness must be Boolean.")
        if not isinstance(self.serving_policy, FieldNoteServingPolicyBoundary):
            raise ValueError("Applicability Serving Policy is invalid.")

    def _payload(self) -> dict[str, Any]:
        return {
            "current": self.current.as_dict(),
            "target_binding_sha256": self.target_binding_sha256,
            "source": self.source.as_dict(),
            "scope": self.scope.as_dict(),
            "target_current_gate": self.target_current_gate,
            "target_status_as_of": self.target_status_as_of,
            "evidence_stale": self.evidence_stale,
            "serving_policy": self.serving_policy.as_dict(),
        }

    @property
    def binding_sha256(self) -> str:
        return _digest(self._payload())

    def as_dict(self) -> dict[str, Any]:
        return {**self._payload(), "binding_sha256": self.binding_sha256}


@dataclass(frozen=True)
class SelectiveReconnectReceipt:
    """Replayable evidence for addressability without activation semantics."""

    state: SelectiveReconnectState
    failure_reason: SelectiveReconnectFailure | None
    current_binding_sha256: str
    applicability_gate: V13Gate
    edge_records_seen: int = 0
    edge_sha256: str | None = None
    target_binding_sha256: str | None = None
    structure_binding_sha256: str | None = None
    target_note_path: str | None = None
    target_field_note_id: str | None = None
    target_note_sha256: str | None = None
    edge_read_attempts: int = 0
    source_evidence_read_attempts: int = 0
    target_note_read_attempts: int = 0
    target_note_bytes_validated: int = 0
    structure_bytes_reopened: int = 0
    field_note_directory_entries_seen: int = 0
    unrelated_field_note_files_opened: int = 0
    broad_scan_performed: Literal[False] = False
    serving_policy_derivation: Literal["DELAY"] = "DELAY"
    automatic_injection: None = None
    serving_created: Literal[False] = False
    selection_created: Literal[False] = False
    promotion_created: Literal[False] = False
    canon_created: Literal[False] = False
    authority_granted: Literal[False] = False
    worker_runs_dispatched: Literal[0] = 0
    promotion_policy_status: Literal["UNSET"] = "UNSET"
    authority_precedence: tuple[str, str] = (
        "TOPMOST_CANONICAL",
        "ADVISORY_FIELD_NOTE",
    )

    def __post_init__(self) -> None:
        if self.state not in {"RECALLED", "DELAY_HOLD"}:
            raise ValueError("Selective reconnect state is invalid.")
        if self.applicability_gate not in {"GO", "HOLD", "CAP", "BLOCK"}:
            raise ValueError("Applicability Gate is invalid.")
        _sha256(self.current_binding_sha256, "Current binding digest")
        counters = (
            self.edge_records_seen,
            self.edge_read_attempts,
            self.source_evidence_read_attempts,
            self.target_note_read_attempts,
            self.target_note_bytes_validated,
            self.structure_bytes_reopened,
            self.field_note_directory_entries_seen,
            self.unrelated_field_note_files_opened,
        )
        if any(type(item) is not int or item < 0 for item in counters):
            raise ValueError("Selective reconnect counters are invalid.")
        for value, label in (
            (self.edge_sha256, "Edge digest"),
            (self.target_binding_sha256, "Target binding digest"),
            (self.structure_binding_sha256, "Structure binding digest"),
            (self.target_note_sha256, "Target Note digest"),
        ):
            if value is not None:
                _sha256(value, label)
        fixed = (
            self.broad_scan_performed is False
            and self.field_note_directory_entries_seen == 0
            and self.unrelated_field_note_files_opened == 0
            and self.serving_policy_derivation == "DELAY"
            and self.automatic_injection is None
            and self.serving_created is False
            and self.selection_created is False
            and self.promotion_created is False
            and self.canon_created is False
            and self.authority_granted is False
            and self.worker_runs_dispatched == 0
            and self.promotion_policy_status == "UNSET"
            and self.authority_precedence
            == ("TOPMOST_CANONICAL", "ADVISORY_FIELD_NOTE")
        )
        if not fixed:
            raise ValueError("Selective reconnect crossed an activation boundary.")
        if self.state == "RECALLED":
            required = (
                self.edge_sha256,
                self.target_binding_sha256,
                self.structure_binding_sha256,
                self.target_note_path,
                self.target_field_note_id,
                self.target_note_sha256,
            )
            if (
                self.failure_reason is not None
                or any(item is None for item in required)
                or self.edge_records_seen != 1
                or self.edge_read_attempts != 2
                or self.source_evidence_read_attempts != 2
                or self.target_note_read_attempts != 2
                or self.target_note_bytes_validated <= 0
                or self.structure_bytes_reopened <= 0
            ):
                raise ValueError("Recalled receipt lacks exact recovery evidence.")
        elif self.failure_reason is None or self.applicability_gate != "HOLD":
            raise ValueError("Failed reconnect must produce DELAY/HOLD.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SELECTIVE_RECONNECT_RECEIPT_SCHEMA,
            "state": self.state,
            "failure_reason": self.failure_reason,
            "current_binding_sha256": self.current_binding_sha256,
            "applicability_gate": self.applicability_gate,
            "edge_records_seen": self.edge_records_seen,
            "edge_sha256": self.edge_sha256,
            "target_binding_sha256": self.target_binding_sha256,
            "structure_binding_sha256": self.structure_binding_sha256,
            "target_note_path": self.target_note_path,
            "target_field_note_id": self.target_field_note_id,
            "target_note_sha256": self.target_note_sha256,
            "edge_read_attempts": self.edge_read_attempts,
            "source_evidence_read_attempts": self.source_evidence_read_attempts,
            "target_note_read_attempts": self.target_note_read_attempts,
            "target_note_bytes_validated": self.target_note_bytes_validated,
            "structure_bytes_reopened": self.structure_bytes_reopened,
            "field_note_directory_entries_seen": self.field_note_directory_entries_seen,
            "unrelated_field_note_files_opened": self.unrelated_field_note_files_opened,
            "broad_scan_performed": self.broad_scan_performed,
            "serving_policy_derivation": self.serving_policy_derivation,
            "automatic_injection": self.automatic_injection,
            "serving_created": self.serving_created,
            "selection_created": self.selection_created,
            "promotion_created": self.promotion_created,
            "canon_created": self.canon_created,
            "authority_granted": self.authority_granted,
            "worker_runs_dispatched": self.worker_runs_dispatched,
            "promotion_policy_status": self.promotion_policy_status,
            "authority_precedence": list(self.authority_precedence),
        }


@dataclass(frozen=True)
class SelectiveReconnectResult:
    receipt: SelectiveReconnectReceipt
    target: SelectiveReconnectTargetBinding | None = None
    structure_bytes: bytes | None = None
    envelope: str | None = None

    def __post_init__(self) -> None:
        recalled = self.receipt.state == "RECALLED"
        payload_present = (
            self.target is not None,
            self.structure_bytes is not None,
            self.envelope is not None,
        )
        if (recalled and not all(payload_present)) or (
            not recalled and any(payload_present)
        ):
            raise ValueError("Selective reconnect payload disagrees with its receipt.")
        if self.structure_bytes is not None and not self.structure_bytes:
            raise ValueError("Selective reconnect structure bytes are empty.")


def _identity_from_dict(value: Any) -> SelectiveReconnectIdentity:
    data = _mapping(value, _IDENTITY_KEYS, "Selective reconnect identity")
    return SelectiveReconnectIdentity(
        identity=data["identity"],
        sha256=data["sha256"],
    )


def _current_from_dict(value: Any) -> SelectiveReconnectCurrentBinding:
    data = _mapping(value, _CURRENT_KEYS, "Current-side binding")
    current = SelectiveReconnectCurrentBinding(
        goal=_identity_from_dict(data["goal"]),
        remaining_gap=_identity_from_dict(data["remaining_gap"]),
        current_gate=data["current_gate"],
        protected_object=_identity_from_dict(data["protected_object"]),
        authority_boundary=_identity_from_dict(data["authority_boundary"]),
        repository_id=data["repository_id"],
        as_of_commit=data["as_of_commit"],
        as_of=data["as_of"],
    )
    if current.binding_sha256 != _sha256(
        data["binding_sha256"], "Stored current binding digest"
    ):
        raise ValueError("Current-side binding digest mismatch.")
    return current


def _source_from_dict(value: Any) -> SelectiveReconnectSourceAnchor:
    data = _mapping(value, _SOURCE_KEYS, "Source anchor")
    return SelectiveReconnectSourceAnchor(
        repository_id=data["repository_id"],
        source_commit=data["source_commit"],
        source_path=data["source_path"],
        source_blob=data["source_blob"],
        source_sha256=data["source_sha256"],
        evidence_path=data["evidence_path"],
        evidence_sha256=data["evidence_sha256"],
        as_of=data["as_of"],
    )


def _note_from_dict(value: Any) -> FieldNoteIdentity:
    data = _mapping(value, _NOTE_KEYS, "Field Note identity")
    return FieldNoteIdentity(
        note_path=data["note_path"],
        field_note_id=data["field_note_id"],
        note_sha256=data["note_sha256"],
        origin_run_id=data["origin_run_id"],
    )


def _structure_from_dict(value: Any) -> FieldNoteStructureBinding:
    data = _mapping(value, _STRUCTURE_KEYS, "Field Note structure binding")
    binding = FieldNoteStructureBinding(
        note=_note_from_dict(data["note"]),
        structure_id=data["structure_id"],
        note_size=data["note_size"],
        start_byte=data["start_byte"],
        end_byte=data["end_byte"],
        structure_sha256=data["structure_sha256"],
    )
    if binding.binding_sha256 != _sha256(
        data["binding_sha256"], "Stored structure binding digest"
    ):
        raise ValueError("Structure binding digest mismatch.")
    return binding


def _target_from_dict(value: Any) -> SelectiveReconnectTargetBinding:
    data = _mapping(value, _TARGET_KEYS, "Selective reconnect target")
    target = SelectiveReconnectTargetBinding(
        structure=_structure_from_dict(data["structure"]),
        source=_source_from_dict(data["source"]),
        scope=_identity_from_dict(data["scope"]),
        stop_conditions=data["stop_conditions"],
        recheck_conditions=data["recheck_conditions"],
        unresolved_delta=data["unresolved_delta"],
        reentry_path=data["reentry_path"],
    )
    if target.binding_sha256 != _sha256(
        data["binding_sha256"], "Stored target binding digest"
    ):
        raise ValueError("Target binding digest mismatch.")
    return target


def _serving_policy_from_dict(value: Any) -> FieldNoteServingPolicyBoundary:
    data = _mapping(value, _SERVING_POLICY_KEYS, "Serving Policy boundary")
    precedence = data["authority_precedence"]
    if not isinstance(precedence, list):
        raise ValueError("Serving Policy authority precedence is invalid.")
    return FieldNoteServingPolicyBoundary(
        note=_note_from_dict(data["note"]),
        derivation=data["derivation"],
        automatic_derivation_supported=data["automatic_derivation_supported"],
        automatic_injection=data["automatic_injection"],
        complete_state_machine_implemented=data["complete_state_machine_implemented"],
        forward_only_extension=data["forward_only_extension"],
        authority_precedence=tuple(precedence),
        delay_reason=data["delay_reason"],
    )


def _applicability_from_dict(value: Any) -> SelectiveReconnectApplicability:
    data = _mapping(value, _APPLICABILITY_KEYS, "Current applicability evidence")
    applicability = SelectiveReconnectApplicability(
        current=_current_from_dict(data["current"]),
        target_binding_sha256=data["target_binding_sha256"],
        source=_source_from_dict(data["source"]),
        scope=_identity_from_dict(data["scope"]),
        target_current_gate=data["target_current_gate"],
        target_status_as_of=data["target_status_as_of"],
        evidence_stale=data["evidence_stale"],
        serving_policy=_serving_policy_from_dict(data["serving_policy"]),
    )
    if applicability.binding_sha256 != _sha256(
        data["binding_sha256"],
        "Stored applicability binding digest",
    ):
        raise ValueError("Current applicability binding digest mismatch.")
    return applicability


def _edge_from_dict(value: Any) -> SelectiveReconnectEdge:
    data = _mapping(value, _EDGE_KEYS, "Selective reconnect edge")
    if data["schema"] != SELECTIVE_RECONNECT_SCHEMA:
        raise ValueError("Selective reconnect schema is unsupported.")
    edge = SelectiveReconnectEdge(
        current=_current_from_dict(data["current"]),
        target=_target_from_dict(data["target"]),
        applicability=_applicability_from_dict(data["applicability"]),
    )
    if edge.edge_sha256 != _sha256(data["edge_sha256"], "Stored edge digest"):
        raise ValueError("Selective reconnect edge digest mismatch.")
    return edge


def _file_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _directory_flags() -> int:
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise _ExactFileError("Safe directory flags unavailable.")
    return os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY


def _file_flags() -> int:
    if not hasattr(os, "O_NOFOLLOW"):
        raise _ExactFileError("Safe file flags unavailable.")
    return os.O_RDONLY | os.O_NOFOLLOW


def _read_exact_repository_file(
    repository: Path,
    relative_path: str,
    *,
    maximum_bytes: int,
    missing_ok: bool,
) -> _ExactRepositoryFileRead | None:
    """Read one exact relative file through no-follow descriptors; never scan."""

    canonical = _relative_path(relative_path, "Exact repository file path")
    segments = canonical.split("/")
    descriptors: list[int] = []
    directory_chain: list[
        tuple[str | Path, int | None, int, tuple[int, int, int, int, int]]
    ] = []
    try:
        try:
            root_before = os.stat(repository, follow_symlinks=False)
        except (OSError, TypeError, ValueError) as exc:
            raise _ExactFileError("Repository root is unsafe.") from exc
        if not stat.S_ISDIR(root_before.st_mode):
            raise _ExactFileError("Repository root is unsafe.")
        root_fd = os.open(repository, _directory_flags())
        descriptors.append(root_fd)
        root_identity = _file_identity(root_before)
        if _file_identity(os.fstat(root_fd)) != root_identity:
            raise _ExactFileError("Repository root changed during read.")
        directory_chain.append((repository, None, root_fd, root_identity))
        parent_fd = root_fd
        for segment in segments[:-1]:
            try:
                before = os.stat(segment, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                if missing_ok:
                    return None
                raise _ExactFileError("Exact parent directory is missing.") from None
            except OSError as exc:
                raise _ExactFileError("Exact parent directory is unsafe.") from exc
            if not stat.S_ISDIR(before.st_mode):
                raise _ExactFileError("Exact parent directory is unsafe.")
            child_fd = os.open(segment, _directory_flags(), dir_fd=parent_fd)
            descriptors.append(child_fd)
            identity = _file_identity(before)
            if _file_identity(os.fstat(child_fd)) != identity:
                raise _ExactFileError("Exact parent directory changed.")
            directory_chain.append((segment, parent_fd, child_fd, identity))
            parent_fd = child_fd
        filename = segments[-1]
        try:
            before_file = os.stat(filename, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            if missing_ok:
                return None
            raise _ExactFileError("Exact file is missing.") from None
        except OSError as exc:
            raise _ExactFileError("Exact file is unsafe.") from exc
        if not stat.S_ISREG(before_file.st_mode):
            raise _ExactFileError("Exact file is unsafe.")
        file_identity = _file_identity(before_file)
        file_fd = os.open(filename, _file_flags(), dir_fd=parent_fd)
        descriptors.append(file_fd)
        if _file_identity(os.fstat(file_fd)) != file_identity:
            raise _ExactFileError("Exact file changed during read.")
        data = bytearray()
        while True:
            chunk = os.read(file_fd, min(65536, maximum_bytes + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > maximum_bytes:
                raise _ExactFileError("Exact file exceeds its bounded size.")
        after_file = os.fstat(file_fd)
        entry_after = os.stat(filename, dir_fd=parent_fd, follow_symlinks=False)
        if (
            _file_identity(after_file) != file_identity
            or _file_identity(entry_after) != file_identity
            or len(data) != file_identity[2]
        ):
            raise _ExactFileError("Exact file changed during read.")
        for name, parent, descriptor, expected in reversed(directory_chain):
            entry = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if (
                not stat.S_ISDIR(entry.st_mode)
                or _file_identity(entry) != expected
                or _file_identity(os.fstat(descriptor)) != expected
            ):
                raise _ExactFileError("Exact directory changed during read.")
        return _ExactRepositoryFileRead(
            data=bytes(data),
            device=file_identity[0],
            inode=file_identity[1],
            size=file_identity[2],
            mtime_ns=file_identity[3],
            ctime_ns=file_identity[4],
        )
    except _ExactFileError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise _ExactFileError("Exact file read failed safely.") from exc
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _ensure_edge_directory(repository: Path) -> int:
    root_before = os.stat(repository, follow_symlinks=False)
    if not stat.S_ISDIR(root_before.st_mode):
        raise ValueError("Repository root is unsafe.")
    root_fd = os.open(repository, _directory_flags())
    current_fd = root_fd
    try:
        for segment in (".decision-os", "selective-reconnect"):
            try:
                os.mkdir(segment, mode=0o700, dir_fd=current_fd)
            except FileExistsError:
                pass
            before = os.stat(segment, dir_fd=current_fd, follow_symlinks=False)
            if not stat.S_ISDIR(before.st_mode):
                raise ValueError("Selective reconnect directory is unsafe.")
            opened = os.open(segment, _directory_flags(), dir_fd=current_fd)
            if _file_identity(os.fstat(opened)) != _file_identity(before):
                os.close(opened)
                raise ValueError("Selective reconnect directory changed.")
            if current_fd != root_fd:
                os.close(current_fd)
            current_fd = opened
        return current_fd
    except Exception:
        if current_fd != root_fd:
            os.close(current_fd)
        raise
    finally:
        os.close(root_fd)


def _repository_identity(root: Path) -> tuple[str, str]:
    try:
        if git_root(root) != root.resolve(strict=True):
            raise RepositoryIdentityError(
                "Selective reconnect requires the exact Git worktree root."
            )
        return repository_id(root), git_output(root, "rev-parse", "HEAD")
    except (OSError, RepositoryIdentityError) as exc:
        raise _ExactFileError("Current repository identity is unavailable.") from exc


def persist_selective_reconnect_edge(
    repository: Path,
    edge: SelectiveReconnectEdge,
) -> Path:
    """Persist exactly one canonical edge; never replace a different record."""

    if not isinstance(edge, SelectiveReconnectEdge):
        raise ValueError("Only a typed selective reconnect edge can be persisted.")
    root = Path(repository)
    try:
        observed_repository, observed_commit = _repository_identity(root)
    except _ExactFileError as exc:
        raise ValueError("Current repository identity is unavailable.") from exc
    if (
        observed_repository != edge.current.repository_id
        or observed_commit != edge.current.as_of_commit
    ):
        raise ValueError("Selective reconnect current repository identity mismatches.")
    applicability_failure = _applicability_failure(
        edge.current,
        edge.target,
        edge.applicability,
    )
    if applicability_failure is not None:
        raise ValueError(
            "Selective reconnect edge inputs are internally inconsistent."
        )
    try:
        exact = read_exact_field_note(root, edge.target.reentry_path)
    except FieldNoteExactReadError as exc:
        raise ValueError("Selective reconnect target is not exact and current.") from exc
    if _exact_target_failure(edge.target, exact) is not None:
        raise ValueError("Selective reconnect target is not exact and current.")
    expected_evidence = selective_reconnect_source_evidence_bytes(
        repository_id=edge.target.source.repository_id,
        source_commit=edge.target.source.source_commit,
        source_path=edge.target.source.source_path,
        source_blob=edge.target.source.source_blob,
        source_sha256=edge.target.source.source_sha256,
        evidence_path=edge.target.source.evidence_path,
        as_of=edge.target.source.as_of,
    )
    try:
        evidence = _read_exact_repository_file(
            root,
            edge.target.source.evidence_path,
            maximum_bytes=MAX_SOURCE_EVIDENCE_BYTES,
            missing_ok=False,
        )
    except _ExactFileError as exc:
        raise ValueError("Selective reconnect source evidence is unavailable.") from exc
    if (
        evidence is None
        or evidence.data != expected_evidence
        or hashlib.sha256(evidence.data).hexdigest()
        != edge.target.source.evidence_sha256
    ):
        raise ValueError("Selective reconnect source evidence is inconsistent.")
    data = canonical_json(edge.as_dict()).encode("utf-8") + b"\n"
    if len(data) > MAX_EDGE_FILE_BYTES:
        raise ValueError("Selective reconnect edge exceeds its bounded size.")
    target = root / SELECTIVE_RECONNECT_EDGE_PATH
    directory_fd = _ensure_edge_directory(root)
    temporary_name: str | None = None
    descriptor: int | None = None
    try:
        for _attempt in range(16):
            candidate = f".edge-v1-{secrets.token_hex(16)}.tmp"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory_fd,
                )
            except FileExistsError:
                continue
            temporary_name = candidate
            break
        if descriptor is None or temporary_name is None:
            raise ValueError("Selective reconnect temporary slot is unavailable.")
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise ValueError("Selective reconnect edge write failed.")
            view = view[written:]
        os.fsync(descriptor)
        try:
            os.link(
                temporary_name,
                "edge-v1.jsonl",
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            existing = _read_exact_repository_file(
                root,
                SELECTIVE_RECONNECT_EDGE_PATH,
                maximum_bytes=MAX_EDGE_FILE_BYTES,
                missing_ok=False,
            )
            if existing is None or existing.data != data:
                raise ValueError(
                    "The one Selective Reconnect Edge slot already differs."
                )
        os.fsync(directory_fd)
        return target
    except (OSError, _ExactFileError) as exc:
        raise ValueError("Selective reconnect edge could not be persisted safely.") from exc
    finally:
        if temporary_name is not None and descriptor is not None:
            try:
                expected = _file_identity(os.fstat(descriptor))
                observed = os.stat(
                    temporary_name,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                if _file_identity(observed) == expected:
                    os.unlink(temporary_name, dir_fd=directory_fd)
                    os.fsync(directory_fd)
            except (FileNotFoundError, OSError):
                pass
        if descriptor is not None:
            os.close(descriptor)
        os.close(directory_fd)


def _parse_edges(data: bytes) -> tuple[SelectiveReconnectEdge, ...]:
    if not data:
        return ()
    if len(data) > MAX_EDGE_FILE_BYTES or not data.endswith(b"\n") or b"\r" in data:
        raise ValueError("Selective reconnect edge file is not canonical JSONL.")
    lines = data[:-1].split(b"\n")
    if not lines or any(not line for line in lines):
        raise ValueError("Selective reconnect edge file contains an empty record.")
    result: list[SelectiveReconnectEdge] = []
    for line in lines:
        try:
            text = line.decode("utf-8")
            value = json.loads(
                text,
                object_pairs_hook=_strict_pairs,
                parse_constant=_reject_constant,
            )
            if not isinstance(value, dict) or canonical_json(value) != text:
                raise ValueError("Selective reconnect edge JSON is noncanonical.")
            result.append(_edge_from_dict(value))
        except (
            UnicodeDecodeError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
            RecursionError,
        ) as exc:
            raise ValueError("Selective reconnect edge JSON is invalid.") from exc
    return tuple(result)


def _current_mismatch(
    expected: SelectiveReconnectCurrentBinding,
    observed: SelectiveReconnectCurrentBinding,
) -> SelectiveReconnectFailure | None:
    if expected.goal != observed.goal:
        return "GOAL_IDENTITY_MISMATCH"
    if expected.remaining_gap != observed.remaining_gap:
        return "GAP_IDENTITY_MISMATCH"
    if expected.current_gate != observed.current_gate:
        return "CURRENT_GATE_MISMATCH"
    if expected.protected_object != observed.protected_object:
        return "PROTECTED_OBJECT_MISMATCH"
    if expected.authority_boundary != observed.authority_boundary:
        return "AUTHORITY_BOUNDARY_MISMATCH"
    if expected.repository_id != observed.repository_id:
        return "CURRENT_REPOSITORY_MISMATCH"
    if expected.as_of_commit != observed.as_of_commit:
        return "AS_OF_MISMATCH"
    if expected.as_of != observed.as_of:
        return "AS_OF_MISMATCH"
    return None


def _hold(
    current: SelectiveReconnectCurrentBinding,
    reason: SelectiveReconnectFailure,
    *,
    edge_records_seen: int = 0,
    edge_read_attempts: int = 0,
    edge: SelectiveReconnectEdge | None = None,
    target_note_read_attempts: int = 0,
    target_note_bytes_validated: int = 0,
    source_evidence_read_attempts: int = 0,
) -> SelectiveReconnectResult:
    target = edge.target if edge is not None else None
    structure = target.structure if target is not None else None
    note = structure.note if structure is not None else None
    return SelectiveReconnectResult(
        receipt=SelectiveReconnectReceipt(
            state="DELAY_HOLD",
            failure_reason=reason,
            current_binding_sha256=current.binding_sha256,
            applicability_gate="HOLD",
            edge_records_seen=edge_records_seen,
            edge_sha256=edge.edge_sha256 if edge is not None else None,
            target_binding_sha256=(target.binding_sha256 if target else None),
            structure_binding_sha256=(
                structure.binding_sha256 if structure else None
            ),
            target_note_path=note.note_path if note else None,
            target_field_note_id=note.field_note_id if note else None,
            target_note_sha256=note.note_sha256 if note else None,
            edge_read_attempts=edge_read_attempts,
            source_evidence_read_attempts=source_evidence_read_attempts,
            target_note_read_attempts=target_note_read_attempts,
            target_note_bytes_validated=target_note_bytes_validated,
        )
    )


def _applicability_failure(
    current: SelectiveReconnectCurrentBinding,
    target: SelectiveReconnectTargetBinding,
    applicability: SelectiveReconnectApplicability,
) -> SelectiveReconnectFailure | None:
    current_failure = _current_mismatch(current, applicability.current)
    if current_failure is not None:
        return current_failure
    if target.source.as_of != current.as_of:
        return "AS_OF_MISMATCH"
    if applicability.target_binding_sha256 != target.binding_sha256:
        return "TARGET_IDENTITY_MISMATCH"
    if (
        applicability.source.repository_id != target.source.repository_id
        or applicability.source.source_commit != target.source.source_commit
        or applicability.source.source_path != target.source.source_path
        or applicability.source.source_blob != target.source.source_blob
        or applicability.source.source_sha256 != target.source.source_sha256
    ):
        return "SOURCE_IDENTITY_MISMATCH"
    if applicability.source.as_of != target.source.as_of:
        return "AS_OF_MISMATCH"
    if (
        applicability.source.evidence_path != target.source.evidence_path
        or applicability.source.evidence_sha256 != target.source.evidence_sha256
    ):
        return "SOURCE_EVIDENCE_FAILURE"
    if applicability.scope != target.scope:
        return "SCOPE_MISMATCH"
    if applicability.target_status_as_of != current.as_of:
        return "AS_OF_MISMATCH"
    if applicability.evidence_stale:
        return "STALE_EVIDENCE"
    if applicability.target_current_gate != "HOLD":
        return "UNSUPPORTED_APPLICABILITY_ROUTE"
    if applicability.serving_policy.note != target.structure.note:
        return "TARGET_IDENTITY_MISMATCH"
    return None


def _selective_envelope(
    current: SelectiveReconnectCurrentBinding,
    edge: SelectiveReconnectEdge,
    structure_bytes: bytes,
) -> str:
    structure = edge.target.structure
    applicability = edge.applicability
    separator = "" if structure_bytes.endswith(b"\n") else "\n"
    return (
        "=== DECISION OS SELECTIVE RECONNECT / ADDRESSABILITY ONLY / BEGIN ===\n"
        f"Edge SHA-256: {edge.edge_sha256}\n"
        f"Current binding SHA-256: {current.binding_sha256}\n"
        f"Target binding SHA-256: {edge.target.binding_sha256}\n"
        f"Structure binding SHA-256: {structure.binding_sha256}\n"
        f"Field Note path: {structure.note.note_path}\n"
        f"Current Goal Gate: {current.current_gate}\n"
        f"Target current-use Gate: {applicability.target_current_gate}\n\n"
        "Boundary:\n"
        "This block proves exact addressability only. Recall does not establish\n"
        "current validity, serving, selection, promotion, Canon, authority, or\n"
        "permission to continue. Existing topmost authority and HOLD conditions\n"
        "remain controlling.\n\n"
        "--- EXACT FIELD NOTE STRUCTURE UTF-8 BYTES BEGIN ---\n"
        + structure_bytes.decode("utf-8")
        + separator
        + "--- EXACT FIELD NOTE STRUCTURE UTF-8 BYTES END ---\n"
        "=== DECISION OS SELECTIVE RECONNECT / ADDRESSABILITY ONLY / END ===\n"
    )


def _exact_target_failure(
    target: SelectiveReconnectTargetBinding,
    exact: FieldNoteExactRead,
) -> SelectiveReconnectFailure | None:
    expected_note = target.structure.note
    if (
        exact.relative_path != expected_note.note_path
        or exact.field_note_id != expected_note.field_note_id
        or exact.source_run_id != expected_note.origin_run_id
    ):
        return "TARGET_IDENTITY_MISMATCH"
    if (
        exact.note_sha256 != expected_note.note_sha256
        or len(exact.note_bytes) != target.structure.note_size
        or not target.structure.verifies(expected_note, exact.note_bytes)
    ):
        return "STALE_TARGET"
    if (
        exact.task_family != target.scope.identity
        or exact.scope_sha256 != target.scope.sha256
    ):
        return "SCOPE_MISMATCH"
    return None


def resolve_selective_reconnect(
    repository: Path,
    *,
    current: SelectiveReconnectCurrentBinding,
) -> SelectiveReconnectResult:
    """Recover only one persisted exact target, or fail safely to HOLD."""

    if not isinstance(current, SelectiveReconnectCurrentBinding):
        raise ValueError("Selective reconnect input is not a typed current binding.")
    root = Path(repository)
    edge_read_attempts = 0
    target_note_read_attempts = 0
    source_evidence_read_attempts = 0
    target_note_bytes_validated = 0
    edge: SelectiveReconnectEdge | None = None

    def hold(reason: SelectiveReconnectFailure, *, records: int = 0) -> SelectiveReconnectResult:
        return _hold(
            current,
            reason,
            edge_records_seen=records,
            edge_read_attempts=edge_read_attempts,
            edge=edge,
            target_note_read_attempts=target_note_read_attempts,
            target_note_bytes_validated=target_note_bytes_validated,
            source_evidence_read_attempts=source_evidence_read_attempts,
        )

    try:
        observed_repository, observed_commit = _repository_identity(root)
    except _ExactFileError:
        return hold("CURRENT_REPOSITORY_MISMATCH")
    if observed_repository != current.repository_id:
        return hold("CURRENT_REPOSITORY_MISMATCH")
    if observed_commit != current.as_of_commit:
        return hold("AS_OF_MISMATCH")

    edge_read_attempts += 1
    try:
        edge_read = _read_exact_repository_file(
            root,
            SELECTIVE_RECONNECT_EDGE_PATH,
            maximum_bytes=MAX_EDGE_FILE_BYTES,
            missing_ok=True,
        )
    except _ExactFileError:
        return hold("CORRUPTED_EDGE")
    if edge_read is None or edge_read.data == b"":
        return hold("ZERO_TARGETS")
    try:
        edges = _parse_edges(edge_read.data)
    except (TypeError, ValueError):
        return hold("CORRUPTED_EDGE")
    if not edges:
        return hold("ZERO_TARGETS")
    if len(edges) != 1:
        return hold("MULTIPLE_TARGETS", records=len(edges))
    edge = edges[0]

    mismatch = _current_mismatch(current, edge.current)
    if mismatch is not None:
        return hold(mismatch, records=1)

    target = edge.target
    applicability = edge.applicability
    target_note_read_attempts += 1
    try:
        exact = read_exact_field_note(root, target.reentry_path)
    except FieldNoteExactReadError:
        return hold("STALE_TARGET", records=1)
    target_failure = _exact_target_failure(target, exact)
    if target_failure is not None:
        return hold(target_failure, records=1)
    target_note_bytes_validated += len(exact.note_bytes)

    applicability_failure = _applicability_failure(
        current,
        target,
        applicability,
    )
    if applicability_failure is not None:
        return hold(applicability_failure, records=1)

    expected_evidence = selective_reconnect_source_evidence_bytes(
        repository_id=target.source.repository_id,
        source_commit=target.source.source_commit,
        source_path=target.source.source_path,
        source_blob=target.source.source_blob,
        source_sha256=target.source.source_sha256,
        evidence_path=target.source.evidence_path,
        as_of=target.source.as_of,
    )
    source_evidence_read_attempts += 1
    try:
        evidence_read = _read_exact_repository_file(
            root,
            target.source.evidence_path,
            maximum_bytes=MAX_SOURCE_EVIDENCE_BYTES,
            missing_ok=False,
        )
    except _ExactFileError:
        evidence_read = None
    evidence = evidence_read.data if evidence_read is not None else None
    if (
        evidence is None
        or evidence != expected_evidence
        or hashlib.sha256(evidence).hexdigest()
        != target.source.evidence_sha256
    ):
        return hold("SOURCE_EVIDENCE_FAILURE", records=1)

    # Re-read every persisted input before returning RECALLED.  This creates a
    # bounded stable validation window and fails closed if a path is swapped
    # between the independent exact reads.
    edge_read_attempts += 1
    try:
        edge_read_after = _read_exact_repository_file(
            root,
            SELECTIVE_RECONNECT_EDGE_PATH,
            maximum_bytes=MAX_EDGE_FILE_BYTES,
            missing_ok=False,
        )
    except _ExactFileError:
        edge_read_after = None
    if edge_read_after != edge_read:
        return hold("UNSTABLE_RECOVERY_WINDOW", records=1)

    target_note_read_attempts += 1
    try:
        exact_after = read_exact_field_note(root, target.reentry_path)
    except FieldNoteExactReadError:
        return hold("UNSTABLE_RECOVERY_WINDOW", records=1)
    if exact_after != exact or _exact_target_failure(target, exact_after) is not None:
        return hold("UNSTABLE_RECOVERY_WINDOW", records=1)
    target_note_bytes_validated += len(exact_after.note_bytes)

    source_evidence_read_attempts += 1
    try:
        evidence_read_after = _read_exact_repository_file(
            root,
            target.source.evidence_path,
            maximum_bytes=MAX_SOURCE_EVIDENCE_BYTES,
            missing_ok=False,
        )
    except _ExactFileError:
        evidence_read_after = None
    if evidence_read_after != evidence_read:
        return hold("UNSTABLE_RECOVERY_WINDOW", records=1)

    try:
        repository_after, commit_after = _repository_identity(root)
    except _ExactFileError:
        repository_after, commit_after = "", ""
    if repository_after != current.repository_id:
        return hold("CURRENT_REPOSITORY_MISMATCH", records=1)
    if commit_after != current.as_of_commit:
        return hold("AS_OF_MISMATCH", records=1)

    expected_note = target.structure.note
    structure_bytes = exact_after.note_bytes[
        target.structure.start_byte : target.structure.end_byte
    ]
    return SelectiveReconnectResult(
        receipt=SelectiveReconnectReceipt(
            state="RECALLED",
            failure_reason=None,
            current_binding_sha256=current.binding_sha256,
            applicability_gate=applicability.target_current_gate,
            edge_records_seen=1,
            edge_sha256=edge.edge_sha256,
            target_binding_sha256=target.binding_sha256,
            structure_binding_sha256=target.structure.binding_sha256,
            target_note_path=expected_note.note_path,
            target_field_note_id=expected_note.field_note_id,
            target_note_sha256=expected_note.note_sha256,
            edge_read_attempts=edge_read_attempts,
            source_evidence_read_attempts=source_evidence_read_attempts,
            target_note_read_attempts=target_note_read_attempts,
            target_note_bytes_validated=target_note_bytes_validated,
            structure_bytes_reopened=len(structure_bytes),
        ),
        target=target,
        structure_bytes=structure_bytes,
        envelope=_selective_envelope(current, edge, structure_bytes),
    )
