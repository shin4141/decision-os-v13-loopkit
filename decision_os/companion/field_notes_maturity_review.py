"""Read-only Field Notes Lite A6 maturity evidence review projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import re
from typing import Any, Literal

from decision_os.companion.field_notes_maturity_ledger import (
    GENESIS_EVENT_SHA256,
    FieldNoteMaturityLedger,
    FieldNoteMaturityLedgerEvent,
)
from decision_os.companion.field_notes_model import canonical_json
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteMaturitySummary,
    FieldNoteRevisionLink,
    FieldNoteServingPolicyBoundary,
    HumanIntervention,
    NextAction,
    ObserverRelation,
    OutcomeConfirmation,
    ReuseOutcome,
    UseEvidenceClass,
    UseEvidenceOrigin,
)


MATURITY_REVIEW_SCHEMA = "decision-os.field-note-maturity-review.v0.1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class FieldNoteMaturityReviewError(RuntimeError):
    """Base error for an A6 review packet that cannot be produced safely."""


class FieldNoteMaturityReviewValidationError(
    FieldNoteMaturityReviewError,
    ValueError,
):
    """The requested exact Note, A4 partition, or review As-of is invalid."""


def _validate_review_as_of(value: Any) -> str:
    if not isinstance(value, str):
        raise FieldNoteMaturityReviewValidationError(
            "Maturity review As-of must be text."
        )
    normalized = value.strip()
    if not normalized or len(normalized) > 64 or "\x00" in normalized:
        raise FieldNoteMaturityReviewValidationError(
            "Maturity review As-of is outside its bounded schema."
        )
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FieldNoteMaturityReviewValidationError(
            "Maturity review As-of must be an RFC 3339 timestamp."
        ) from exc
    if parsed.tzinfo is None:
        raise FieldNoteMaturityReviewValidationError(
            "Maturity review As-of must be timezone-aware."
        )
    return normalized


def _require_sha256(value: Any, label: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest.")


@dataclass(frozen=True)
class FieldNoteMaturityReviewLedgerIdentity:
    """Exact A4 partition and verified event-chain identity."""

    note_partition_sha256: str
    chain_head_sha256: str
    durable_event_count: int

    def __post_init__(self) -> None:
        _require_sha256(self.note_partition_sha256, "Note partition identity")
        _require_sha256(self.chain_head_sha256, "A4 chain head")
        if type(self.durable_event_count) is not int or self.durable_event_count < 0:
            raise ValueError("Durable event count is invalid.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "note_partition_sha256": self.note_partition_sha256,
            "chain_head_sha256": self.chain_head_sha256,
            "durable_event_count": self.durable_event_count,
        }


@dataclass(frozen=True)
class FieldNoteMaturityReviewSignals:
    """Deterministic evidence descriptions, never scores or policy decisions."""

    helpful_outcomes: int
    not_helpful_outcomes: int
    harmful_outcomes: int
    unknown_outcomes: int
    material_or_unknown_interventions: int
    same_run_outcome_claims: int
    run_related_outcome_claims: int
    independent_outcome_confirmations: int
    keep_dispositions: int
    hold_dispositions: int
    stop_dispositions: int
    revise_links: int
    unique_reusing_runs: int
    unique_specific_structures: int
    rule_trace_events: int
    output_artifact_events: int
    evidence_classes: tuple[UseEvidenceClass, ...]

    def __post_init__(self) -> None:
        counts = (
            self.helpful_outcomes,
            self.not_helpful_outcomes,
            self.harmful_outcomes,
            self.unknown_outcomes,
            self.material_or_unknown_interventions,
            self.same_run_outcome_claims,
            self.run_related_outcome_claims,
            self.independent_outcome_confirmations,
            self.keep_dispositions,
            self.hold_dispositions,
            self.stop_dispositions,
            self.revise_links,
            self.unique_reusing_runs,
            self.unique_specific_structures,
            self.rule_trace_events,
            self.output_artifact_events,
        )
        if any(type(value) is not int or value < 0 for value in counts):
            raise ValueError("Maturity review signal counts are invalid.")
        if (
            tuple(sorted(set(self.evidence_classes))) != self.evidence_classes
            or any(
                value not in {"RULE_TRACE", "OUTPUT_ARTIFACT"}
                for value in self.evidence_classes
            )
        ):
            raise ValueError("Maturity review evidence classes are invalid.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "helpful_outcomes": self.helpful_outcomes,
            "not_helpful_outcomes": self.not_helpful_outcomes,
            "harmful_outcomes": self.harmful_outcomes,
            "unknown_outcomes": self.unknown_outcomes,
            "material_or_unknown_interventions": (
                self.material_or_unknown_interventions
            ),
            "same_run_outcome_claims": self.same_run_outcome_claims,
            "run_related_outcome_claims": self.run_related_outcome_claims,
            "independent_outcome_confirmations": (
                self.independent_outcome_confirmations
            ),
            "keep_dispositions": self.keep_dispositions,
            "hold_dispositions": self.hold_dispositions,
            "stop_dispositions": self.stop_dispositions,
            "revise_links": self.revise_links,
            "unique_reusing_runs": self.unique_reusing_runs,
            "unique_specific_structures": self.unique_specific_structures,
            "rule_trace_events": self.rule_trace_events,
            "output_artifact_events": self.output_artifact_events,
            "evidence_classes": list(self.evidence_classes),
        }


@dataclass(frozen=True)
class FieldNoteMaturityEventReview:
    """Bounded projection of one sequence-ordered, A4-verified reuse event."""

    sequence: int
    recorded_at: str
    event_id: str
    previous_event_sha256: str
    event_sha256: str
    reusing_run_id: str
    structure_id: str
    structure_sha256: str
    structure_binding_sha256: str
    evidence_class: UseEvidenceClass
    evidence_origin: UseEvidenceOrigin
    evidence_ref: str
    evidence_sha256: str
    use_evidence_observer_id: str
    use_evidence_observer_relation: ObserverRelation
    use_evidence_as_of: str
    claimed_outcome: ReuseOutcome
    effective_outcome: ReuseOutcome
    outcome_scope: str
    causal_evidence_ref: str | None
    causal_evidence_sha256: str | None
    outcome_observer_id: str
    outcome_observer_relation: ObserverRelation
    outcome_confirmation: OutcomeConfirmation
    outcome_as_of: str
    contribution_separated: bool
    human_intervention: HumanIntervention
    next_action: NextAction
    reevaluation_condition: str | None
    stop_scope: str | None
    revision: FieldNoteRevisionLink | None

    def __post_init__(self) -> None:
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("Maturity event review sequence is invalid.")
        for value, label in (
            (self.event_id, "Reuse event identity"),
            (self.previous_event_sha256, "Previous event identity"),
            (self.event_sha256, "Event identity"),
            (self.structure_sha256, "Structure identity"),
            (self.structure_binding_sha256, "Structure binding identity"),
            (self.evidence_sha256, "Use-evidence identity"),
        ):
            _require_sha256(value, label)
        if self.causal_evidence_sha256 is not None:
            _require_sha256(
                self.causal_evidence_sha256,
                "Causal-evidence identity",
            )
        if (self.causal_evidence_ref is None) != (
            self.causal_evidence_sha256 is None
        ):
            raise ValueError("Causal-evidence identity is incomplete.")
        if type(self.contribution_separated) is not bool:
            raise ValueError("Contribution separation is invalid.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "recorded_at": self.recorded_at,
            "event_id": self.event_id,
            "previous_event_sha256": self.previous_event_sha256,
            "event_sha256": self.event_sha256,
            "reusing_run_id": self.reusing_run_id,
            "structure": {
                "structure_id": self.structure_id,
                "structure_sha256": self.structure_sha256,
                "structure_binding_sha256": self.structure_binding_sha256,
            },
            "use_evidence": {
                "evidence_class": self.evidence_class,
                "evidence_origin": self.evidence_origin,
                "evidence_ref": self.evidence_ref,
                "evidence_sha256": self.evidence_sha256,
                "observer_id": self.use_evidence_observer_id,
                "observer_relation": self.use_evidence_observer_relation,
                "as_of": self.use_evidence_as_of,
            },
            "outcome_evidence": {
                "claimed_outcome": self.claimed_outcome,
                "effective_outcome": self.effective_outcome,
                "scope": self.outcome_scope,
                "causal_evidence_ref": self.causal_evidence_ref,
                "causal_evidence_sha256": self.causal_evidence_sha256,
                "observer_id": self.outcome_observer_id,
                "observer_relation": self.outcome_observer_relation,
                "confirmation": self.outcome_confirmation,
                "as_of": self.outcome_as_of,
                "contribution_separated": self.contribution_separated,
                "human_intervention": self.human_intervention,
            },
            "disposition": {
                "next_action": self.next_action,
                "reevaluation_condition": self.reevaluation_condition,
                "stop_scope": self.stop_scope,
                "revision": (
                    self.revision.as_dict() if self.revision is not None else None
                ),
            },
        }


@dataclass(frozen=True)
class FieldNoteMaturityReviewClaimBoundary:
    """Fixed limit: durable history is neither current truth nor policy."""

    evidence_scope: Literal["HISTORICAL_AS_OF_RECORDS"] = (
        "HISTORICAL_AS_OF_RECORDS"
    )
    current_usefulness: Literal["NOT_ESTABLISHED"] = "NOT_ESTABLISHED"
    promotion_decision: Literal["NOT_PERFORMED"] = "NOT_PERFORMED"
    serving_policy_derived: Literal[False] = False
    full_note_contents_included: Literal[False] = False

    def __post_init__(self) -> None:
        if (
            self.evidence_scope != "HISTORICAL_AS_OF_RECORDS"
            or self.current_usefulness != "NOT_ESTABLISHED"
            or self.promotion_decision != "NOT_PERFORMED"
            or self.serving_policy_derived is not False
            or self.full_note_contents_included is not False
        ):
            raise ValueError("Maturity review claim boundary is invalid.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_scope": self.evidence_scope,
            "current_usefulness": self.current_usefulness,
            "promotion_decision": self.promotion_decision,
            "serving_policy_derived": self.serving_policy_derived,
            "full_note_contents_included": self.full_note_contents_included,
        }


@dataclass(frozen=True)
class FieldNoteMaturityReviewPacket:
    """Canonical A6 packet projected only from verified A4 reconstruction."""

    schema: Literal["decision-os.field-note-maturity-review.v0.1"]
    review_as_of: str
    note_identity: FieldNoteIdentity
    ledger_identity: FieldNoteMaturityReviewLedgerIdentity
    evidence_maturity: FieldNoteMaturitySummary
    current_serving_policy: FieldNoteServingPolicyBoundary
    aggregate_evidence_signals: FieldNoteMaturityReviewSignals
    ordered_event_reviews: tuple[FieldNoteMaturityEventReview, ...]
    claim_boundary: FieldNoteMaturityReviewClaimBoundary

    def __post_init__(self) -> None:
        if self.schema != MATURITY_REVIEW_SCHEMA:
            raise ValueError("Maturity review schema is unsupported.")
        object.__setattr__(
            self,
            "review_as_of",
            _validate_review_as_of(self.review_as_of),
        )
        if not isinstance(self.note_identity, FieldNoteIdentity):
            raise ValueError("Maturity review lacks an exact Note identity.")
        expected_partition = hashlib.sha256(
            canonical_json(self.note_identity.as_dict()).encode("utf-8")
        ).hexdigest()
        reviews = self.ordered_event_reviews
        event_ids = tuple(sorted(item.event_id for item in reviews))
        sequence = tuple(item.sequence for item in reviews)
        chain_is_valid = all(
            item.previous_event_sha256
            == (
                GENESIS_EVENT_SHA256
                if index == 0
                else reviews[index - 1].event_sha256
            )
            for index, item in enumerate(reviews)
        )
        expected_head = (
            reviews[-1].event_sha256 if reviews else GENESIS_EVENT_SHA256
        )
        if (
            not isinstance(
                self.ledger_identity,
                FieldNoteMaturityReviewLedgerIdentity,
            )
            or self.ledger_identity.note_partition_sha256 != expected_partition
            or self.ledger_identity.durable_event_count != len(reviews)
            or self.ledger_identity.chain_head_sha256 != expected_head
            or sequence != tuple(range(len(reviews)))
            or not chain_is_valid
        ):
            raise ValueError("Maturity review ledger identity is inconsistent.")
        if (
            not isinstance(self.evidence_maturity, FieldNoteMaturitySummary)
            or self.evidence_maturity.note != self.note_identity
            or self.evidence_maturity.reuse_event_ids != event_ids
            or (self.evidence_maturity.state == "CANDIDATE") != (not reviews)
        ):
            raise ValueError("Maturity review evidence summary is inconsistent.")
        if (
            not isinstance(
                self.current_serving_policy,
                FieldNoteServingPolicyBoundary,
            )
            or self.current_serving_policy.note != self.note_identity
        ):
            raise ValueError("Maturity review Serving Policy boundary is invalid.")
        if self.aggregate_evidence_signals != _review_signals(reviews):
            raise ValueError("Maturity review aggregate signals are inconsistent.")
        if not isinstance(
            self.claim_boundary,
            FieldNoteMaturityReviewClaimBoundary,
        ):
            raise ValueError("Maturity review claim boundary is invalid.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "review_as_of": self.review_as_of,
            "note_identity": self.note_identity.as_dict(),
            "ledger_identity": self.ledger_identity.as_dict(),
            "evidence_maturity": self.evidence_maturity.as_dict(),
            "current_serving_policy": self.current_serving_policy.as_dict(),
            "aggregate_evidence_signals": (
                self.aggregate_evidence_signals.as_dict()
            ),
            "ordered_event_reviews": [
                event.as_dict() for event in self.ordered_event_reviews
            ],
            "claim_boundary": self.claim_boundary.as_dict(),
        }

    def serialize(self) -> str:
        """Return one deterministic canonical JSON representation."""

        return canonical_json(self.as_dict())

    def render_text(self) -> str:
        """Render a concise review without Note or artifact contents."""

        promotion = self.evidence_maturity.promotion
        policy = self.current_serving_policy
        signals = self.aggregate_evidence_signals
        classes = ",".join(signals.evidence_classes) or "NONE"
        lines = [
            "Field Note Maturity Evidence Review v0.1",
            f"Review As-of: {self.review_as_of}",
            f"Note: {self.note_identity.note_path}",
            f"Field Note ID: {self.note_identity.field_note_id}",
            f"Note SHA-256: {self.note_identity.note_sha256}",
            f"Origin Run: {self.note_identity.origin_run_id}",
            f"A4 partition: {self.ledger_identity.note_partition_sha256}",
            f"A4 chain head: {self.ledger_identity.chain_head_sha256}",
            f"Durable events: {self.ledger_identity.durable_event_count}",
            (
                "Evidence Maturity: "
                f"{self.evidence_maturity.state} (historical evidence)"
            ),
            (
                "PROMOTABLE policy: "
                f"{promotion.policy_status}; automatic promotion unavailable"
            ),
            (
                "Current Serving Policy: "
                f"{policy.derivation}; separate and not derived from maturity"
            ),
            "Authority: TOPMOST_CANONICAL > ADVISORY_FIELD_NOTE",
            (
                "Signals: "
                f"helpful={signals.helpful_outcomes}, "
                f"not_helpful={signals.not_helpful_outcomes}, "
                f"harmful={signals.harmful_outcomes}, "
                f"unknown={signals.unknown_outcomes}, "
                f"intervention_affected="
                f"{signals.material_or_unknown_interventions}, "
                f"hold={signals.hold_dispositions}, "
                f"stop={signals.stop_dispositions}, "
                f"revise={signals.revise_links}, "
                f"runs={signals.unique_reusing_runs}, "
                f"structures={signals.unique_specific_structures}, "
                f"evidence_classes={classes}"
            ),
        ]
        for event in self.ordered_event_reviews:
            lines.append(
                f"Event {event.sequence}: recorded={event.recorded_at}; "
                f"run={event.reusing_run_id}; "
                f"structure={event.structure_id}; "
                f"evidence={event.evidence_class}; "
                f"claimed_outcome={event.claimed_outcome}; "
                f"effective_outcome={event.effective_outcome}; "
                f"confirmation={event.outcome_confirmation}; "
                f"intervention={event.human_intervention}; "
                f"disposition={event.next_action}"
            )
        lines.append(
            "Claim boundary: historical evidence only; current usefulness is "
            "not established; promotion is not decided; serving is not derived."
        )
        return "\n".join(lines) + "\n"


def _event_review(event: FieldNoteMaturityLedgerEvent) -> FieldNoteMaturityEventReview:
    receipt = event.receipt
    evidence = receipt.use_evidence
    if evidence is None:
        raise ValueError("Verified A4 reuse event lacks use evidence.")
    binding = evidence.structure_binding
    if (
        receipt.claimed_outcome is None
        or receipt.outcome is None
        or receipt.outcome_scope is None
        or receipt.outcome_observer_id is None
        or receipt.outcome_observer_relation is None
        or receipt.outcome_confirmation is None
        or receipt.outcome_as_of is None
        or receipt.contribution_separated is None
        or receipt.human_intervention is None
        or receipt.next_action is None
    ):
        raise ValueError("Verified A4 reuse event lacks review evidence axes.")
    return FieldNoteMaturityEventReview(
        sequence=event.sequence,
        recorded_at=event.recorded_at,
        event_id=event.event_id,
        previous_event_sha256=event.previous_event_sha256,
        event_sha256=event.event_sha256,
        reusing_run_id=receipt.reusing_run_id,
        structure_id=binding.structure_id,
        structure_sha256=binding.structure_sha256,
        structure_binding_sha256=binding.binding_sha256,
        evidence_class=evidence.evidence_class,
        evidence_origin=evidence.evidence_origin,
        evidence_ref=evidence.evidence_ref,
        evidence_sha256=evidence.evidence_sha256,
        use_evidence_observer_id=evidence.observer_id,
        use_evidence_observer_relation=evidence.observer_relation,
        use_evidence_as_of=evidence.as_of,
        claimed_outcome=receipt.claimed_outcome,
        effective_outcome=receipt.outcome,
        outcome_scope=receipt.outcome_scope,
        causal_evidence_ref=receipt.causal_evidence_ref,
        causal_evidence_sha256=receipt.causal_evidence_sha256,
        outcome_observer_id=receipt.outcome_observer_id,
        outcome_observer_relation=receipt.outcome_observer_relation,
        outcome_confirmation=receipt.outcome_confirmation,
        outcome_as_of=receipt.outcome_as_of,
        contribution_separated=receipt.contribution_separated,
        human_intervention=receipt.human_intervention,
        next_action=receipt.next_action,
        reevaluation_condition=receipt.reevaluation_condition,
        stop_scope=receipt.stop_scope,
        revision=receipt.revision,
    )


def _review_signals(
    events: tuple[FieldNoteMaturityEventReview, ...],
) -> FieldNoteMaturityReviewSignals:
    outcomes = tuple(event.effective_outcome for event in events)
    confirmations = tuple(event.outcome_confirmation for event in events)
    actions = tuple(event.next_action for event in events)
    classes = tuple(sorted({event.evidence_class for event in events}))
    return FieldNoteMaturityReviewSignals(
        helpful_outcomes=outcomes.count("HELPFUL"),
        not_helpful_outcomes=outcomes.count("NOT_HELPFUL"),
        harmful_outcomes=outcomes.count("HARMFUL"),
        unknown_outcomes=outcomes.count("UNKNOWN"),
        material_or_unknown_interventions=sum(
            event.human_intervention in {"MATERIAL", "UNKNOWN"}
            for event in events
        ),
        same_run_outcome_claims=confirmations.count("SAME_RUN_CLAIM"),
        run_related_outcome_claims=confirmations.count("RUN_RELATED_CLAIM"),
        independent_outcome_confirmations=confirmations.count(
            "INDEPENDENT_CONFIRMATION"
        ),
        keep_dispositions=actions.count("KEEP"),
        hold_dispositions=actions.count("HOLD"),
        stop_dispositions=actions.count("STOP"),
        revise_links=sum(event.revision is not None for event in events),
        unique_reusing_runs=len({event.reusing_run_id for event in events}),
        unique_specific_structures=len(
            {event.structure_binding_sha256 for event in events}
        ),
        rule_trace_events=sum(
            event.evidence_class == "RULE_TRACE" for event in events
        ),
        output_artifact_events=sum(
            event.evidence_class == "OUTPUT_ARTIFACT" for event in events
        ),
        evidence_classes=classes,
    )


def review_field_note_maturity(
    ledger: FieldNoteMaturityLedger,
    note: FieldNoteIdentity,
    *,
    note_bytes: bytes,
    review_as_of: str,
) -> FieldNoteMaturityReviewPacket:
    """Project verified A4 history without modifying evidence or deriving policy."""

    if not isinstance(ledger, FieldNoteMaturityLedger):
        raise FieldNoteMaturityReviewValidationError(
            "Maturity review requires a typed A4 ledger."
        )
    if not isinstance(note, FieldNoteIdentity):
        raise FieldNoteMaturityReviewValidationError(
            "Maturity review requires an exact Field Note identity."
        )
    if ledger.note != note:
        raise FieldNoteMaturityReviewValidationError(
            "Maturity review targets a different A4 Note partition."
        )
    if (
        not isinstance(note_bytes, bytes)
        or hashlib.sha256(note_bytes).hexdigest() != note.note_sha256
    ):
        raise FieldNoteMaturityReviewValidationError(
            "Maturity review Note bytes do not match the exact identity."
        )
    review_as_of = _validate_review_as_of(review_as_of)
    snapshot = ledger.reconstruct(note_bytes=note_bytes)
    if snapshot.note != note:
        raise FieldNoteMaturityReviewValidationError(
            "A4 reconstruction returned a cross-bound Note identity."
        )
    event_reviews = tuple(_event_review(event) for event in snapshot.events)
    return FieldNoteMaturityReviewPacket(
        schema=MATURITY_REVIEW_SCHEMA,
        review_as_of=review_as_of,
        note_identity=note,
        ledger_identity=FieldNoteMaturityReviewLedgerIdentity(
            note_partition_sha256=ledger.note_partition_sha256,
            chain_head_sha256=snapshot.chain_head_sha256,
            durable_event_count=len(snapshot.events),
        ),
        evidence_maturity=snapshot.evidence_maturity,
        current_serving_policy=snapshot.current_serving_policy,
        aggregate_evidence_signals=_review_signals(event_reviews),
        ordered_event_reviews=event_reviews,
        claim_boundary=FieldNoteMaturityReviewClaimBoundary(),
    )
