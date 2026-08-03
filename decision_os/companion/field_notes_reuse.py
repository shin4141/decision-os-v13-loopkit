"""Typed, fail-closed Field Notes Lite A3 reuse evidence.

This module records reuse separately from saved Field Note bytes.  Injection,
successful completion, narrative claims, and human approval are intentionally
not inputs that can establish reuse.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
from pathlib import PurePosixPath
import re
from typing import Any, Iterable, Literal

from decision_os.companion.field_notes_model import canonical_json
from decision_os.companion.field_notes_reconnect import (
    FieldNoteReconnectReceipt,
)


ReuseState = Literal["CANDIDATE", "REUSED"]
UseEvidenceClass = Literal["RULE_TRACE", "OUTPUT_ARTIFACT"]
UseEvidenceOrigin = Literal["REUSING_RUN", "IMMEDIATE_COMPLETION_RECORD"]
ReuseOutcome = Literal["HELPFUL", "NOT_HELPFUL", "HARMFUL", "UNKNOWN"]
HumanIntervention = Literal["NONE", "NON_DECISIVE", "MATERIAL", "UNKNOWN"]
NextAction = Literal["KEEP", "REVISE", "HOLD", "STOP"]
ObserverRelation = Literal[
    "REUSING_RUN_SELF",
    "REUSING_RUN_PARTICIPANT",
    "INDEPENDENT",
]
OutcomeConfirmation = Literal[
    "SAME_RUN_CLAIM",
    "RUN_RELATED_CLAIM",
    "INDEPENDENT_CONFIRMATION",
]
ReuseFailureReason = Literal[
    "USE_EVIDENCE_MISSING",
    "NOTE_IDENTITY_MISMATCH",
    "ORIGIN_RUN_NOT_DIFFERENT",
    "STRUCTURE_BINDING_INVALID",
]
ServingPolicyDerivation = Literal["DELAY"]

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GENERIC_STRUCTURE_IDS = frozenset(
    {
        "entire field note",
        "entire note",
        "field note",
        "note",
        "the field note",
        "the note",
        "whole field note",
        "whole note",
    }
)
_DEFAULT_OUTCOME_RECHECK = (
    "Re-evaluate when bounded outcome evidence can determine the specific "
    "Note structure's contribution."
)
_DEFAULT_INTERVENTION_RECHECK = (
    "Re-evaluate when the specific Note structure's contribution can be "
    "separated from material or unknown human intervention."
)
_DEFAULT_CAUSAL_RECHECK = (
    "Re-evaluate when bounded causal evidence supports the declared outcome."
)
_DEFAULT_ATTRIBUTION_RECHECK = (
    "Re-evaluate when the specific Note structure's contribution can be "
    "separated from other Notes and causes."
)
_DEFAULT_STOP_SCOPE_RECHECK = (
    "Re-evaluate after an explicit bounded STOP scope is supplied."
)


def _bounded_text(value: Any, label: str, maximum: int = 2048) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text.")
    normalized = value.strip()
    if not normalized or len(normalized) > maximum or "\x00" in normalized:
        raise ValueError(f"{label} is outside its bounded schema.")
    return normalized


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest.")
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _relative_path(value: Any, label: str) -> str:
    normalized = _bounded_text(value, label, maximum=1024)
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


def _as_of(value: Any) -> str:
    normalized = _bounded_text(value, "As-of", maximum=64)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("As-of must be an RFC 3339 timestamp.") from exc
    if parsed.tzinfo is None:
        raise ValueError("As-of must be timezone-aware.")
    return normalized


@dataclass(frozen=True)
class FieldNoteIdentity:
    """Exact immutable identity of one saved Field Note."""

    note_path: str
    field_note_id: str
    note_sha256: str
    origin_run_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "note_path",
            _relative_path(self.note_path, "Field Note path"),
        )
        object.__setattr__(
            self,
            "field_note_id",
            _bounded_text(self.field_note_id, "Field Note ID", maximum=256),
        )
        object.__setattr__(
            self,
            "note_sha256",
            _sha256(self.note_sha256, "Field Note digest"),
        )
        object.__setattr__(
            self,
            "origin_run_id",
            _bounded_text(self.origin_run_id, "Origin Run ID", maximum=256),
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "note_path": self.note_path,
            "field_note_id": self.field_note_id,
            "note_sha256": self.note_sha256,
            "origin_run_id": self.origin_run_id,
        }


@dataclass(frozen=True)
class FieldNoteStructureBinding:
    """Deterministic byte-range anchor into one exact Field Note."""

    note: FieldNoteIdentity
    structure_id: str
    note_size: int
    start_byte: int
    end_byte: int
    structure_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "structure_id",
            _bounded_text(self.structure_id, "Structure ID", maximum=256),
        )
        object.__setattr__(
            self,
            "structure_sha256",
            _sha256(self.structure_sha256, "Structure digest"),
        )
        if (
            type(self.note_size) is not int
            or type(self.start_byte) is not int
            or type(self.end_byte) is not int
            or self.note_size <= 0
            or self.start_byte < 0
            or self.end_byte <= self.start_byte
            or self.end_byte > self.note_size
        ):
            raise ValueError("Structure byte range is outside its bounded schema.")

    @property
    def binding_sha256(self) -> str:
        payload = {
            "note": self.note.as_dict(),
            "structure_id": self.structure_id,
            "note_size": self.note_size,
            "start_byte": self.start_byte,
            "end_byte": self.end_byte,
            "structure_sha256": self.structure_sha256,
        }
        return _sha256_bytes(canonical_json(payload).encode("utf-8"))

    def verifies(self, note: FieldNoteIdentity, note_bytes: bytes) -> bool:
        if not isinstance(note_bytes, bytes):
            return False
        if (
            self.note != note
            or len(note_bytes) != self.note_size
            or _sha256_bytes(note_bytes) != note.note_sha256
            or self.structure_id.casefold() in _GENERIC_STRUCTURE_IDS
            or (self.start_byte == 0 and self.end_byte == len(note_bytes))
        ):
            return False
        structure_bytes = note_bytes[self.start_byte : self.end_byte]
        if (
            not structure_bytes.strip()
            or _sha256_bytes(structure_bytes) != self.structure_sha256
            or self.structure_sha256 == note.note_sha256
        ):
            return False
        try:
            note_bytes.decode("utf-8")
            structure_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return True

    def as_dict(self) -> dict[str, Any]:
        return {
            "note": self.note.as_dict(),
            "structure_id": self.structure_id,
            "note_size": self.note_size,
            "start_byte": self.start_byte,
            "end_byte": self.end_byte,
            "structure_sha256": self.structure_sha256,
            "binding_sha256": self.binding_sha256,
        }


def bind_field_note_structure(
    note: FieldNoteIdentity,
    note_bytes: bytes,
    *,
    structure_id: str,
    start_byte: int,
    end_byte: int,
) -> FieldNoteStructureBinding:
    """Create an anchor only after verifying the complete exact Note bytes."""

    if not isinstance(note_bytes, bytes) or _sha256_bytes(note_bytes) != (
        note.note_sha256
    ):
        raise ValueError("Structure source bytes do not match the exact Field Note.")
    binding = FieldNoteStructureBinding(
        note=note,
        structure_id=structure_id,
        note_size=len(note_bytes),
        start_byte=start_byte,
        end_byte=end_byte,
        structure_sha256=_sha256_bytes(note_bytes[start_byte:end_byte]),
    )
    if not binding.verifies(note, note_bytes):
        raise ValueError("Structure binding is not a specific exact-Note range.")
    return binding


@dataclass(frozen=True)
class FieldNoteUseEvidence:
    """Same-window typed evidence that one Note structure operated."""

    evidence_class: UseEvidenceClass
    evidence_origin: UseEvidenceOrigin
    reusing_run_id: str
    structure_binding: FieldNoteStructureBinding
    evidence_ref: str
    evidence_sha256: str
    observer_id: str
    observer_relation: ObserverRelation
    as_of: str

    def __post_init__(self) -> None:
        if self.evidence_class not in {"RULE_TRACE", "OUTPUT_ARTIFACT"}:
            raise ValueError("Use-evidence class is unsupported.")
        if self.evidence_origin not in {
            "REUSING_RUN",
            "IMMEDIATE_COMPLETION_RECORD",
        }:
            raise ValueError("Use evidence is outside the allowed Run window.")
        if self.observer_relation not in {
            "REUSING_RUN_SELF",
            "REUSING_RUN_PARTICIPANT",
            "INDEPENDENT",
        }:
            raise ValueError("Use-evidence observer relation is unsupported.")
        object.__setattr__(
            self,
            "reusing_run_id",
            _bounded_text(self.reusing_run_id, "Reusing Run ID", maximum=256),
        )
        if not isinstance(self.structure_binding, FieldNoteStructureBinding):
            raise ValueError("Use evidence lacks a typed structure binding.")
        object.__setattr__(
            self,
            "evidence_ref",
            _bounded_text(self.evidence_ref, "Use-evidence reference"),
        )
        object.__setattr__(
            self,
            "evidence_sha256",
            _sha256(self.evidence_sha256, "Use-evidence digest"),
        )
        object.__setattr__(
            self,
            "observer_id",
            _bounded_text(self.observer_id, "Use-evidence observer", maximum=256),
        )
        object.__setattr__(self, "as_of", _as_of(self.as_of))

    @property
    def structure_id(self) -> str:
        return self.structure_binding.structure_id

    @property
    def structure_sha256(self) -> str:
        return self.structure_binding.structure_sha256

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_class": self.evidence_class,
            "evidence_origin": self.evidence_origin,
            "reusing_run_id": self.reusing_run_id,
            "structure_binding": self.structure_binding.as_dict(),
            "evidence_ref": self.evidence_ref,
            "evidence_sha256": self.evidence_sha256,
            "observer_id": self.observer_id,
            "observer_relation": self.observer_relation,
            "as_of": self.as_of,
        }


@dataclass(frozen=True)
class FieldNoteOutcomeEvaluation:
    """Outcome claim kept separate from proof that reuse occurred."""

    outcome: ReuseOutcome
    scope: str
    observer_id: str
    observer_relation: ObserverRelation
    as_of: str
    causal_evidence_ref: str | None = None
    causal_evidence_sha256: str | None = None
    contribution_separated: bool = False

    def __post_init__(self) -> None:
        if self.outcome not in {
            "HELPFUL",
            "NOT_HELPFUL",
            "HARMFUL",
            "UNKNOWN",
        }:
            raise ValueError("Reuse outcome is unsupported.")
        if self.observer_relation not in {
            "REUSING_RUN_SELF",
            "REUSING_RUN_PARTICIPANT",
            "INDEPENDENT",
        }:
            raise ValueError("Outcome observer relation is unsupported.")
        object.__setattr__(
            self,
            "scope",
            _bounded_text(self.scope, "Outcome scope"),
        )
        object.__setattr__(
            self,
            "observer_id",
            _bounded_text(self.observer_id, "Outcome observer", maximum=256),
        )
        object.__setattr__(self, "as_of", _as_of(self.as_of))
        if type(self.contribution_separated) is not bool:
            raise ValueError("Contribution separation must be boolean.")
        causal = (self.causal_evidence_ref, self.causal_evidence_sha256)
        if (causal[0] is None) != (causal[1] is None):
            raise ValueError("Causal evidence identity is incomplete.")
        if causal[0] is not None:
            object.__setattr__(
                self,
                "causal_evidence_ref",
                _bounded_text(causal[0], "Causal-evidence reference"),
            )
            object.__setattr__(
                self,
                "causal_evidence_sha256",
                _sha256(causal[1], "Causal-evidence digest"),
            )

    @property
    def has_causal_evidence(self) -> bool:
        return self.causal_evidence_ref is not None

    @property
    def confirmation(self) -> OutcomeConfirmation:
        if self.observer_relation == "REUSING_RUN_SELF":
            return "SAME_RUN_CLAIM"
        if self.observer_relation == "INDEPENDENT":
            return "INDEPENDENT_CONFIRMATION"
        return "RUN_RELATED_CLAIM"

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "scope": self.scope,
            "observer_id": self.observer_id,
            "observer_relation": self.observer_relation,
            "as_of": self.as_of,
            "causal_evidence_ref": self.causal_evidence_ref,
            "causal_evidence_sha256": self.causal_evidence_sha256,
            "contribution_separated": self.contribution_separated,
        }


@dataclass(frozen=True)
class FieldNoteReuseDisposition:
    """Requested next action; invalid mappings are rejected or held."""

    action: NextAction
    reevaluation_condition: str | None = None
    stop_scope: str | None = None
    revision_candidate: FieldNoteIdentity | None = None

    def __post_init__(self) -> None:
        if self.action not in {"KEEP", "REVISE", "HOLD", "STOP"}:
            raise ValueError("Reuse next action is unsupported.")
        if self.reevaluation_condition is not None:
            object.__setattr__(
                self,
                "reevaluation_condition",
                _bounded_text(
                    self.reevaluation_condition,
                    "Re-evaluation condition",
                ),
            )
        if self.stop_scope is not None:
            object.__setattr__(
                self,
                "stop_scope",
                _bounded_text(self.stop_scope, "STOP scope"),
            )


@dataclass(frozen=True)
class FieldNoteReuseClaim:
    """One bounded claim evaluated against a canonical Note identity."""

    claimed_note: FieldNoteIdentity
    reusing_run_id: str
    use_evidence: FieldNoteUseEvidence | None
    outcome_evaluation: FieldNoteOutcomeEvaluation | None
    human_intervention: HumanIntervention
    disposition: FieldNoteReuseDisposition | None
    narrative_claim: str | None = None

    def __post_init__(self) -> None:
        if self.human_intervention not in {
            "NONE",
            "NON_DECISIVE",
            "MATERIAL",
            "UNKNOWN",
        }:
            raise ValueError("Human-intervention state is unsupported.")
        object.__setattr__(
            self,
            "reusing_run_id",
            _bounded_text(self.reusing_run_id, "Reusing Run ID", maximum=256),
        )
        if self.use_evidence is not None and (
            self.use_evidence.reusing_run_id != self.reusing_run_id
        ):
            raise ValueError("Use evidence is bound to a different reusing Run.")
        if self.narrative_claim is not None:
            object.__setattr__(
                self,
                "narrative_claim",
                _bounded_text(self.narrative_claim, "Narrative claim", maximum=4096),
            )


@dataclass(frozen=True)
class FieldNoteRevisionLink:
    """Forward-only link to a distinct revision candidate."""

    predecessor: FieldNoteIdentity
    successor: FieldNoteIdentity

    def __post_init__(self) -> None:
        if self.predecessor == self.successor:
            raise ValueError("A revision must be a new Field Note candidate.")

    def as_dict(self) -> dict[str, dict[str, str]]:
        return {
            "predecessor": self.predecessor.as_dict(),
            "successor": self.successor.as_dict(),
        }


@dataclass(frozen=True)
class PromotionPolicyBoundary:
    """Explicitly reserve PROMOTABLE while its policy is unset."""

    reserved_state: Literal["PROMOTABLE"] = "PROMOTABLE"
    policy_status: Literal["UNSET"] = "UNSET"
    threshold: None = None
    automatically_derivable: Literal[False] = False

    def __post_init__(self) -> None:
        if (
            self.reserved_state != "PROMOTABLE"
            or self.policy_status != "UNSET"
            or self.threshold is not None
            or self.automatically_derivable is not False
        ):
            raise ValueError("PROMOTABLE policy must remain unset.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "reserved_state": self.reserved_state,
            "policy_status": self.policy_status,
            "threshold": self.threshold,
            "automatically_derivable": self.automatically_derivable,
        }


@dataclass(frozen=True)
class FieldNoteReuseReceipt:
    """Immutable A3 receipt for one candidate or verified reuse event."""

    note: FieldNoteIdentity
    reusing_run_id: str
    state: ReuseState
    failure_reason: ReuseFailureReason | None
    use_evidence: FieldNoteUseEvidence | None
    claimed_outcome: ReuseOutcome | None
    outcome: ReuseOutcome | None
    outcome_confirmation: OutcomeConfirmation | None
    outcome_observer_id: str | None
    outcome_observer_relation: ObserverRelation | None
    outcome_as_of: str | None
    outcome_scope: str | None
    causal_evidence_ref: str | None
    causal_evidence_sha256: str | None
    contribution_separated: bool | None
    human_intervention: HumanIntervention | None
    next_action: NextAction | None
    reevaluation_condition: str | None
    stop_scope: str | None
    revision: FieldNoteRevisionLink | None
    reuse_event_id: str | None
    promotion: PromotionPolicyBoundary = PromotionPolicyBoundary()

    def __post_init__(self) -> None:
        if self.state not in {"CANDIDATE", "REUSED"}:
            raise ValueError("A3 can derive only CANDIDATE or REUSED.")
        if self.state == "CANDIDATE":
            if (
                self.failure_reason is None
                or self.use_evidence is not None
                or self.outcome is not None
                or self.outcome_scope is not None
                or self.causal_evidence_ref is not None
                or self.causal_evidence_sha256 is not None
                or self.contribution_separated is not None
                or self.next_action is not None
                or self.reuse_event_id is not None
            ):
                raise ValueError("Candidate receipt contains reuse-only fields.")
            return
        required = (
            self.use_evidence,
            self.claimed_outcome,
            self.outcome,
            self.outcome_confirmation,
            self.outcome_observer_id,
            self.outcome_observer_relation,
            self.outcome_as_of,
            self.outcome_scope,
            self.contribution_separated,
            self.human_intervention,
            self.next_action,
            self.reuse_event_id,
        )
        if self.failure_reason is not None or any(value is None for value in required):
            raise ValueError("Reused receipt lacks its typed evidence axes.")
        if type(self.contribution_separated) is not bool:
            raise ValueError("Reused receipt has an invalid attribution axis.")
        causal = (self.causal_evidence_ref, self.causal_evidence_sha256)
        if (causal[0] is None) != (causal[1] is None):
            raise ValueError("Reused receipt has incomplete causal evidence.")
        if causal[1] is not None:
            _sha256(causal[1], "Causal-evidence digest")
        if self.outcome in {"HELPFUL", "HARMFUL"} and causal[0] is None:
            raise ValueError("Causal outcome lacks causal evidence.")
        _sha256(self.reuse_event_id, "Reuse event ID")
        if self.outcome == "UNKNOWN" and self.next_action != "HOLD":
            raise ValueError("UNKNOWN outcome must HOLD.")
        if self.next_action == "HOLD" and self.reevaluation_condition is None:
            raise ValueError("HOLD requires a re-evaluation condition.")
        if self.next_action == "STOP" and self.stop_scope is None:
            raise ValueError("STOP requires an explicit bounded scope.")
        if self.next_action == "REVISE" and self.revision is None:
            raise ValueError("REVISE requires a forward revision link.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "note": self.note.as_dict(),
            "reusing_run_id": self.reusing_run_id,
            "state": self.state,
            "failure_reason": self.failure_reason,
            "use_evidence": (
                self.use_evidence.as_dict() if self.use_evidence else None
            ),
            "claimed_outcome": self.claimed_outcome,
            "outcome": self.outcome,
            "outcome_confirmation": self.outcome_confirmation,
            "outcome_observer_id": self.outcome_observer_id,
            "outcome_observer_relation": self.outcome_observer_relation,
            "outcome_as_of": self.outcome_as_of,
            "outcome_scope": self.outcome_scope,
            "causal_evidence_ref": self.causal_evidence_ref,
            "causal_evidence_sha256": self.causal_evidence_sha256,
            "contribution_separated": self.contribution_separated,
            "human_intervention": self.human_intervention,
            "next_action": self.next_action,
            "reevaluation_condition": self.reevaluation_condition,
            "stop_scope": self.stop_scope,
            "revision": self.revision.as_dict() if self.revision else None,
            "reuse_event_id": self.reuse_event_id,
            "promotion": self.promotion.as_dict(),
        }


@dataclass(frozen=True)
class FieldNoteMaturitySummary:
    """Deduplicated maturity capped at REUSED while policy is unset."""

    note: FieldNoteIdentity
    state: ReuseState
    reuse_event_ids: tuple[str, ...]
    duplicate_reuse_records_ignored: int
    reconnect_receipts_ignored: int
    promotion: PromotionPolicyBoundary = PromotionPolicyBoundary()

    def __post_init__(self) -> None:
        if self.state not in {"CANDIDATE", "REUSED"}:
            raise ValueError("A3 summary cannot derive PROMOTABLE.")
        if self.state == "CANDIDATE" and self.reuse_event_ids:
            raise ValueError("Candidate summary cannot contain reuse events.")
        if self.state == "REUSED" and not self.reuse_event_ids:
            raise ValueError("Reused summary requires a reuse event.")
        counters = (
            self.duplicate_reuse_records_ignored,
            self.reconnect_receipts_ignored,
        )
        if any(type(value) is not int or value < 0 for value in counters):
            raise ValueError("Maturity summary counters are invalid.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "note": self.note.as_dict(),
            "state": self.state,
            "reuse_event_ids": list(self.reuse_event_ids),
            "duplicate_reuse_records_ignored": (
                self.duplicate_reuse_records_ignored
            ),
            "reconnect_receipts_ignored": self.reconnect_receipts_ignored,
            "promotion": self.promotion.as_dict(),
        }


@dataclass(frozen=True)
class FieldNoteServingPolicyBoundary:
    """Fail-closed boundary for a future, separate Serving Policy.

    Evidence invalidation, serving reduction, supersession, staleness,
    contradiction, harm, and successor compression can only become later
    Forward-only records.  This boundary implements none of those events.
    """

    note: FieldNoteIdentity
    derivation: ServingPolicyDerivation = "DELAY"
    automatic_derivation_supported: Literal[False] = False
    automatic_injection: None = None
    complete_state_machine_implemented: Literal[False] = False
    forward_only_extension: Literal["LATER_RECORDS_ONLY"] = "LATER_RECORDS_ONLY"
    authority_precedence: tuple[
        Literal["TOPMOST_CANONICAL"],
        Literal["ADVISORY_FIELD_NOTE"],
    ] = ("TOPMOST_CANONICAL", "ADVISORY_FIELD_NOTE")
    delay_reason: str = "Current Serving Policy is unsupported."

    def __post_init__(self) -> None:
        if (
            not isinstance(self.note, FieldNoteIdentity)
            or self.derivation != "DELAY"
            or self.automatic_derivation_supported is not False
            or self.automatic_injection is not None
            or self.complete_state_machine_implemented is not False
            or self.forward_only_extension != "LATER_RECORDS_ONLY"
            or self.authority_precedence
            != ("TOPMOST_CANONICAL", "ADVISORY_FIELD_NOTE")
        ):
            raise ValueError("Serving Policy must remain separate and delayed.")
        object.__setattr__(
            self,
            "delay_reason",
            _bounded_text(self.delay_reason, "Serving Policy delay reason"),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "note": self.note.as_dict(),
            "derivation": self.derivation,
            "automatic_derivation_supported": (
                self.automatic_derivation_supported
            ),
            "automatic_injection": self.automatic_injection,
            "complete_state_machine_implemented": (
                self.complete_state_machine_implemented
            ),
            "forward_only_extension": self.forward_only_extension,
            "authority_precedence": list(self.authority_precedence),
            "delay_reason": self.delay_reason,
        }


@dataclass(frozen=True)
class FieldNoteA3Projection:
    """Read-only projection that keeps maturity and serving as separate axes."""

    evidence_maturity: FieldNoteMaturitySummary
    current_serving_policy: FieldNoteServingPolicyBoundary

    def __post_init__(self) -> None:
        if self.evidence_maturity.note != self.current_serving_policy.note:
            raise ValueError("A3 projection axes identify different Field Notes.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_maturity": self.evidence_maturity.as_dict(),
            "current_serving_policy": self.current_serving_policy.as_dict(),
        }


def project_field_note_a3_status(
    maturity: FieldNoteMaturitySummary,
    *,
    serving_delay_reason: str = "Current Serving Policy is unsupported.",
) -> FieldNoteA3Projection:
    """Project independent axes without deriving serving from maturity."""

    return FieldNoteA3Projection(
        evidence_maturity=maturity,
        current_serving_policy=FieldNoteServingPolicyBoundary(
            note=maturity.note,
            delay_reason=serving_delay_reason,
        ),
    )


def _candidate_receipt(
    note: FieldNoteIdentity,
    reusing_run_id: str,
    reason: ReuseFailureReason,
) -> FieldNoteReuseReceipt:
    return FieldNoteReuseReceipt(
        note=note,
        reusing_run_id=_bounded_text(
            reusing_run_id,
            "Reusing Run ID",
            maximum=256,
        ),
        state="CANDIDATE",
        failure_reason=reason,
        use_evidence=None,
        claimed_outcome=None,
        outcome=None,
        outcome_confirmation=None,
        outcome_observer_id=None,
        outcome_observer_relation=None,
        outcome_as_of=None,
        outcome_scope=None,
        causal_evidence_ref=None,
        causal_evidence_sha256=None,
        contribution_separated=None,
        human_intervention=None,
        next_action=None,
        reevaluation_condition=None,
        stop_scope=None,
        revision=None,
        reuse_event_id=None,
    )


def _effective_outcome(
    evaluation: FieldNoteOutcomeEvaluation,
    intervention: HumanIntervention,
) -> tuple[ReuseOutcome, str | None]:
    if intervention in {"MATERIAL", "UNKNOWN"} and not (
        evaluation.contribution_separated
    ):
        return "UNKNOWN", _DEFAULT_INTERVENTION_RECHECK
    if evaluation.outcome != "UNKNOWN" and not (
        evaluation.contribution_separated
    ):
        return "UNKNOWN", _DEFAULT_ATTRIBUTION_RECHECK
    if evaluation.outcome in {"HELPFUL", "HARMFUL"} and not (
        evaluation.has_causal_evidence
    ):
        return "UNKNOWN", _DEFAULT_CAUSAL_RECHECK
    return evaluation.outcome, None


def _normalized_disposition(
    *,
    note: FieldNoteIdentity,
    reusing_run_id: str,
    outcome: ReuseOutcome,
    disposition: FieldNoteReuseDisposition | None,
    forced_reevaluation: str | None,
) -> tuple[
    NextAction,
    str | None,
    str | None,
    FieldNoteRevisionLink | None,
]:
    if outcome == "UNKNOWN":
        condition = forced_reevaluation
        if condition is None and disposition is not None:
            condition = disposition.reevaluation_condition
        return "HOLD", condition or _DEFAULT_OUTCOME_RECHECK, None, None
    if disposition is None:
        raise ValueError("A known reuse outcome requires a next action.")
    allowed = {
        "HELPFUL": {"KEEP", "REVISE"},
        "NOT_HELPFUL": {"REVISE", "STOP"},
        "HARMFUL": {"REVISE", "STOP"},
    }
    if disposition.action not in allowed[outcome]:
        raise ValueError("Next action is invalid for the reuse outcome.")
    if disposition.action == "STOP":
        if disposition.stop_scope is None:
            return (
                "HOLD",
                disposition.reevaluation_condition or _DEFAULT_STOP_SCOPE_RECHECK,
                None,
                None,
            )
        return "STOP", None, disposition.stop_scope, None
    if disposition.action == "REVISE":
        successor = disposition.revision_candidate
        if successor is None:
            raise ValueError("REVISE requires a new candidate identity.")
        if successor.origin_run_id != reusing_run_id:
            raise ValueError("Revision candidate must originate in the reusing Run.")
        return "REVISE", None, None, FieldNoteRevisionLink(note, successor)
    return "KEEP", None, None, None


def assess_field_note_reuse(
    note: FieldNoteIdentity,
    claim: FieldNoteReuseClaim | None,
    *,
    note_bytes: bytes | None = None,
) -> FieldNoteReuseReceipt:
    """Assess one claim without mutating the Field Note or repository."""

    if claim is None:
        return _candidate_receipt(note, "UNBOUND_REUSE_RUN", "USE_EVIDENCE_MISSING")
    if claim.claimed_note != note:
        return _candidate_receipt(
            note,
            claim.reusing_run_id,
            "NOTE_IDENTITY_MISMATCH",
        )
    if claim.reusing_run_id == note.origin_run_id:
        return _candidate_receipt(
            note,
            claim.reusing_run_id,
            "ORIGIN_RUN_NOT_DIFFERENT",
        )
    evidence = claim.use_evidence
    if evidence is None:
        return _candidate_receipt(
            note,
            claim.reusing_run_id,
            "USE_EVIDENCE_MISSING",
        )
    if note_bytes is None or not evidence.structure_binding.verifies(
        note,
        note_bytes,
    ):
        return _candidate_receipt(
            note,
            claim.reusing_run_id,
            "STRUCTURE_BINDING_INVALID",
        )
    evaluation = claim.outcome_evaluation or FieldNoteOutcomeEvaluation(
        outcome="UNKNOWN",
        scope="The bounded reusing Run.",
        observer_id=evidence.observer_id,
        observer_relation=evidence.observer_relation,
        as_of=evidence.as_of,
    )
    outcome, forced_reevaluation = _effective_outcome(
        evaluation,
        claim.human_intervention,
    )
    action, condition, stop_scope, revision = _normalized_disposition(
        note=note,
        reusing_run_id=claim.reusing_run_id,
        outcome=outcome,
        disposition=claim.disposition,
        forced_reevaluation=forced_reevaluation,
    )
    event_payload = {
        "note": note.as_dict(),
        "reusing_run_id": claim.reusing_run_id,
        "use_evidence": evidence.as_dict(),
    }
    reuse_event_id = hashlib.sha256(
        canonical_json(event_payload).encode("utf-8")
    ).hexdigest()
    return FieldNoteReuseReceipt(
        note=note,
        reusing_run_id=claim.reusing_run_id,
        state="REUSED",
        failure_reason=None,
        use_evidence=evidence,
        claimed_outcome=evaluation.outcome,
        outcome=outcome,
        outcome_confirmation=evaluation.confirmation,
        outcome_observer_id=evaluation.observer_id,
        outcome_observer_relation=evaluation.observer_relation,
        outcome_as_of=evaluation.as_of,
        outcome_scope=evaluation.scope,
        causal_evidence_ref=evaluation.causal_evidence_ref,
        causal_evidence_sha256=evaluation.causal_evidence_sha256,
        contribution_separated=evaluation.contribution_separated,
        human_intervention=claim.human_intervention,
        next_action=action,
        reevaluation_condition=condition,
        stop_scope=stop_scope,
        revision=revision,
        reuse_event_id=reuse_event_id,
    )


def summarize_field_note_maturity(
    note: FieldNoteIdentity,
    reuse_receipts: Iterable[FieldNoteReuseReceipt],
    reconnect_receipts: Iterable[FieldNoteReconnectReceipt] = (),
) -> FieldNoteMaturitySummary:
    """Deduplicate reuse and explicitly ignore A2 injection as maturity."""

    event_ids: set[str] = set()
    duplicates = 0
    for receipt in reuse_receipts:
        if receipt.note != note:
            raise ValueError("Reuse receipt belongs to a different Field Note.")
        if receipt.state != "REUSED" or receipt.reuse_event_id is None:
            continue
        if receipt.reuse_event_id in event_ids:
            duplicates += 1
        else:
            event_ids.add(receipt.reuse_event_id)
    ignored_reconnects = 0
    for receipt in reconnect_receipts:
        if not isinstance(receipt, FieldNoteReconnectReceipt):
            raise ValueError("Reconnect receipt type is invalid.")
        ignored_reconnects += 1
    ordered = tuple(sorted(event_ids))
    return FieldNoteMaturitySummary(
        note=note,
        state="REUSED" if ordered else "CANDIDATE",
        reuse_event_ids=ordered,
        duplicate_reuse_records_ignored=duplicates,
        reconnect_receipts_ignored=ignored_reconnects,
    )
