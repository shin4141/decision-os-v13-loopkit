from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from decision_os.companion.field_notes_maturity_ledger import (
    GENESIS_EVENT_SHA256,
    FieldNoteMaturityLedger,
    FieldNoteMaturityLedgerIntegrityError,
)
from decision_os.companion.field_notes_maturity_review import (
    MATURITY_REVIEW_SCHEMA,
    FieldNoteMaturityReviewValidationError,
    review_field_note_maturity,
)
from decision_os.companion.field_notes_model import canonical_json
from decision_os.companion.field_notes_reconnect import (
    FieldNoteReconnectReceipt,
)
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteOutcomeEvaluation,
    FieldNoteReuseClaim,
    FieldNoteReuseDisposition,
    FieldNoteUseEvidence,
    assess_field_note_reuse,
    bind_field_note_structure,
)


REVIEW_AS_OF = "2026-08-04T12:00:00Z"
USE_AS_OF = "2026-08-04T10:00:00Z"
STRUCTURE_A = b"Verify canonical state before restart."
STRUCTURE_B = b"Preserve every bounded negative outcome."
PRIVATE_BODY = b"Private full Note paragraph that A6 must never expose."
NOTE_BYTES = (
    b"# A6 Maturity Evidence Review\n\n"
    b"## Decision / Pattern\n\n"
    + STRUCTURE_A
    + b"\n"
    + STRUCTURE_B
    + b"\n\n## Private Context\n\n"
    + PRIVATE_BODY
    + b"\n\n## Limits\n\nCurrent canonical authority always wins.\n"
)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: str) -> str:
    return digest_bytes(value.encode("utf-8"))


def note_identity(
    *,
    field_note_id: str = "fn_a6_review",
    note_bytes: bytes = NOTE_BYTES,
    note_path: str = (
        ".decision-os/field-notes/"
        "2026-08-04-a6-maturity-review-aaaaaaaaaa.md"
    ),
    origin_run_id: str = "run_origin",
) -> FieldNoteIdentity:
    return FieldNoteIdentity(
        note_path=note_path,
        field_note_id=field_note_id,
        note_sha256=digest_bytes(note_bytes),
        origin_run_id=origin_run_id,
    )


def reuse_receipt(
    note: FieldNoteIdentity,
    *,
    evidence_tag: str = "1",
    reusing_run_id: str | None = None,
    structure: str = "A",
    evidence_class: str = "RULE_TRACE",
    outcome: str = "UNKNOWN",
    outcome_scope: str = "The bounded A6 review test scope.",
    outcome_observer_id: str = "outcome_observer_a6",
    outcome_observer_relation: str = "INDEPENDENT",
    use_observer_id: str = "use_observer_a6",
    use_observer_relation: str = "INDEPENDENT",
    contribution_separated: bool = True,
    intervention: str = "NONE",
    action: str | None = None,
) -> object:
    run_id = reusing_run_id or f"run_reuse_{evidence_tag}"
    structure_bytes = STRUCTURE_A if structure == "A" else STRUCTURE_B
    structure_id = (
        "canonical-restart-state-guard"
        if structure == "A"
        else "negative-outcome-retention"
    )
    start = NOTE_BYTES.index(structure_bytes)
    binding = bind_field_note_structure(
        note,
        NOTE_BYTES,
        structure_id=structure_id,
        start_byte=start,
        end_byte=start + len(structure_bytes),
    )
    evidence = FieldNoteUseEvidence(
        evidence_class=evidence_class,  # type: ignore[arg-type]
        evidence_origin="IMMEDIATE_COMPLETION_RECORD",
        reusing_run_id=run_id,
        structure_binding=binding,
        evidence_ref=f"run:{run_id}/evidence:{evidence_tag}",
        evidence_sha256=digest(f"use evidence {evidence_tag}"),
        observer_id=use_observer_id,
        observer_relation=use_observer_relation,  # type: ignore[arg-type]
        as_of=USE_AS_OF,
    )
    causal = outcome in {"HELPFUL", "HARMFUL"}
    evaluation = FieldNoteOutcomeEvaluation(
        outcome=outcome,  # type: ignore[arg-type]
        scope=outcome_scope,
        observer_id=outcome_observer_id,
        observer_relation=outcome_observer_relation,  # type: ignore[arg-type]
        as_of=USE_AS_OF,
        causal_evidence_ref=(
            f"run:{run_id}/causal:{evidence_tag}" if causal else None
        ),
        causal_evidence_sha256=(
            digest(f"causal evidence {evidence_tag}") if causal else None
        ),
        contribution_separated=contribution_separated,
    )
    if action is None and outcome == "HELPFUL":
        action = "KEEP"
    if action is None and outcome in {"NOT_HELPFUL", "HARMFUL"}:
        action = "STOP"
    disposition = None
    if action == "KEEP":
        disposition = FieldNoteReuseDisposition(action="KEEP")
    elif action == "STOP":
        disposition = FieldNoteReuseDisposition(
            action="STOP",
            stop_scope=f"Bounded A6 task family {evidence_tag}.",
        )
    elif action == "REVISE":
        successor_bytes = NOTE_BYTES + evidence_tag.encode("ascii")
        successor = note_identity(
            field_note_id=f"fn_a6_successor_{evidence_tag}",
            note_bytes=successor_bytes,
            note_path=(
                ".decision-os/field-notes/"
                f"2026-08-04-a6-successor-{evidence_tag.zfill(10)}.md"
            ),
            origin_run_id=run_id,
        )
        disposition = FieldNoteReuseDisposition(
            action="REVISE",
            revision_candidate=successor,
        )
    claim = FieldNoteReuseClaim(
        claimed_note=note,
        reusing_run_id=run_id,
        use_evidence=evidence,
        outcome_evaluation=evaluation,
        human_intervention=intervention,  # type: ignore[arg-type]
        disposition=disposition,
    )
    receipt = assess_field_note_reuse(note, claim, note_bytes=NOTE_BYTES)
    if receipt.state != "REUSED":
        raise AssertionError("A6 test fixture failed to produce REUSED")
    return receipt


def reconnect_receipt(note: FieldNoteIdentity) -> FieldNoteReconnectReceipt:
    return FieldNoteReconnectReceipt(
        run_id="run_reuse_1",
        state="ACTIVATION_UNKNOWN",
        failure_reason=None,
        metadata_entries_seen=1,
        metadata_candidate_files_seen=1,
        metadata_files_valid=1,
        metadata_bytes_read=700,
        selected_field_note_path=note.note_path,
        selected_field_note_id=note.field_note_id,
        selected_metadata_sha256=digest("metadata"),
        selected_full_note_sha256=note.note_sha256,
        full_note_bytes_read=len(NOTE_BYTES),
        full_notes_injected=1,
        ordinary_distinct_paths_consumed=1,
    )


class MaturityReviewTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "maturity-ledger-v0.1"
        self.note = note_identity()
        self.ledger = FieldNoteMaturityLedger(self.root, self.note)
        self.append_count = 0

    def append(self, **kwargs):
        receipt = reuse_receipt(self.note, **kwargs)
        recorded_at = f"2026-08-04T11:{self.append_count:02d}:00Z"
        self.append_count += 1
        return self.ledger.append_receipt(
            receipt,
            note_bytes=NOTE_BYTES,
            recorded_at=recorded_at,
        )

    def review(self, *, review_as_of: str = REVIEW_AS_OF):
        return review_field_note_maturity(
            self.ledger,
            self.note,
            note_bytes=NOTE_BYTES,
            review_as_of=review_as_of,
        )

    def parsed_events(self) -> list[dict]:
        return [
            json.loads(line)
            for line in self.ledger.events_path.read_text().splitlines()
        ]

    def rewrite_events(self, events: list[dict]) -> None:
        self.ledger.events_path.write_text(
            "".join(f"{canonical_json(event)}\n" for event in events)
        )


class FieldNotesMaturityReviewProjectionTests(MaturityReviewTestCase):
    def test_empty_valid_ledger_produces_candidate_review(self) -> None:
        packet = self.review()
        self.assertEqual(MATURITY_REVIEW_SCHEMA, packet.schema)
        self.assertEqual("CANDIDATE", packet.evidence_maturity.state)
        self.assertEqual(0, packet.ledger_identity.durable_event_count)
        self.assertEqual((), packet.ordered_event_reviews)
        self.assertFalse(self.root.exists())

    def test_one_durable_event_produces_reused_review(self) -> None:
        self.append()
        packet = self.review()
        self.assertEqual("REUSED", packet.evidence_maturity.state)
        self.assertEqual(1, len(packet.ordered_event_reviews))

    def test_multiple_events_remain_in_durable_sequence_order(self) -> None:
        for tag in ("1", "2", "3"):
            self.append(evidence_tag=tag)
        packet = self.review()
        self.assertEqual(
            [0, 1, 2],
            [event.sequence for event in packet.ordered_event_reviews],
        )
        self.assertEqual(
            ["run_reuse_1", "run_reuse_2", "run_reuse_3"],
            [event.reusing_run_id for event in packet.ordered_event_reviews],
        )

    def test_repeated_generation_is_deterministic(self) -> None:
        self.append(outcome="HARMFUL")
        first = self.review()
        second = self.review()
        self.assertEqual(first, second)
        self.assertEqual(first.serialize(), second.serialize())
        self.assertEqual(first.render_text(), second.render_text())

    def test_review_as_of_is_the_only_caller_supplied_projection_variation(self) -> None:
        self.append()
        first = self.review(review_as_of="2026-08-04T12:00:00Z")
        second = self.review(review_as_of="2026-08-04T13:00:00Z")
        first_data = first.as_dict()
        second_data = second.as_dict()
        self.assertNotEqual(first_data.pop("review_as_of"), second_data.pop("review_as_of"))
        self.assertEqual(first_data, second_data)

    def test_exact_note_identity_is_preserved(self) -> None:
        packet = self.review()
        self.assertEqual(self.note, packet.note_identity)
        self.assertEqual(self.note.as_dict(), packet.as_dict()["note_identity"])

    def test_a4_chain_head_and_event_count_are_preserved(self) -> None:
        first = self.append(evidence_tag="1")
        second = self.append(evidence_tag="2")
        packet = self.review()
        self.assertEqual(2, packet.ledger_identity.durable_event_count)
        self.assertEqual(
            second.event.event_sha256,
            packet.ledger_identity.chain_head_sha256,
        )
        self.assertEqual(
            first.event.event_sha256,
            packet.ordered_event_reviews[1].previous_event_sha256,
        )

    def test_review_generation_is_read_only(self) -> None:
        self.append()
        paths = (
            self.ledger.events_path,
            self.ledger.head_path,
            self.ledger.lock_path,
        )
        before = {
            path: (
                path.read_bytes(),
                path.stat().st_size,
                path.stat().st_mode,
                path.stat().st_mtime_ns,
                path.stat().st_ino,
            )
            for path in paths
        }
        note_before = bytes(NOTE_BYTES)
        self.review()
        self.review()
        after = {
            path: (
                path.read_bytes(),
                path.stat().st_size,
                path.stat().st_mode,
                path.stat().st_mtime_ns,
                path.stat().st_ino,
            )
            for path in paths
        }
        self.assertEqual(before, after)
        self.assertEqual(note_before, NOTE_BYTES)

    def test_serialization_and_text_projection_are_canonical(self) -> None:
        self.append(outcome="NOT_HELPFUL")
        packet = self.review()
        self.assertEqual(canonical_json(packet.as_dict()), packet.serialize())
        self.assertTrue(packet.render_text().endswith("\n"))
        self.assertIn("historical evidence", packet.render_text())


class FieldNotesMaturityReviewEvidenceTests(MaturityReviewTestCase):
    def test_unique_reusing_run_count_is_correct(self) -> None:
        self.append(evidence_tag="1", reusing_run_id="run_shared", structure="A")
        self.append(evidence_tag="2", reusing_run_id="run_shared", structure="B")
        self.append(evidence_tag="3", reusing_run_id="run_other", structure="A")
        self.assertEqual(2, self.review().aggregate_evidence_signals.unique_reusing_runs)

    def test_unique_specific_structure_count_is_correct(self) -> None:
        self.append(evidence_tag="1", structure="A")
        self.append(evidence_tag="2", structure="A")
        self.append(evidence_tag="3", structure="B")
        packet = self.review()
        self.assertEqual(
            2,
            packet.aggregate_evidence_signals.unique_specific_structures,
        )

    def test_rule_trace_is_represented(self) -> None:
        self.append(evidence_class="RULE_TRACE")
        packet = self.review()
        self.assertEqual("RULE_TRACE", packet.ordered_event_reviews[0].evidence_class)
        self.assertEqual(1, packet.aggregate_evidence_signals.rule_trace_events)

    def test_output_artifact_is_represented_by_identity_only(self) -> None:
        self.append(evidence_class="OUTPUT_ARTIFACT")
        packet = self.review()
        event = packet.ordered_event_reviews[0]
        self.assertEqual("OUTPUT_ARTIFACT", event.evidence_class)
        self.assertEqual(1, packet.aggregate_evidence_signals.output_artifact_events)
        self.assertTrue(event.evidence_ref)
        self.assertRegex(event.evidence_sha256, r"^[0-9a-f]{64}$")

    def test_helpful_is_represented(self) -> None:
        self.append(outcome="HELPFUL")
        packet = self.review()
        self.assertEqual("HELPFUL", packet.ordered_event_reviews[0].effective_outcome)
        self.assertEqual(1, packet.aggregate_evidence_signals.helpful_outcomes)

    def test_not_helpful_is_represented(self) -> None:
        self.append(outcome="NOT_HELPFUL")
        packet = self.review()
        self.assertEqual(
            "NOT_HELPFUL",
            packet.ordered_event_reviews[0].effective_outcome,
        )
        self.assertEqual(1, packet.aggregate_evidence_signals.not_helpful_outcomes)

    def test_harmful_is_represented(self) -> None:
        self.append(outcome="HARMFUL")
        packet = self.review()
        self.assertEqual("HARMFUL", packet.ordered_event_reviews[0].effective_outcome)
        self.assertEqual(1, packet.aggregate_evidence_signals.harmful_outcomes)

    def test_unknown_is_represented(self) -> None:
        self.append(outcome="UNKNOWN")
        packet = self.review()
        self.assertEqual("UNKNOWN", packet.ordered_event_reviews[0].effective_outcome)
        self.assertEqual(1, packet.aggregate_evidence_signals.unknown_outcomes)

    def test_mixed_positive_and_negative_evidence_remains_mixed(self) -> None:
        cases = (
            ("1", "HELPFUL"),
            ("2", "NOT_HELPFUL"),
            ("3", "HARMFUL"),
            ("4", "UNKNOWN"),
        )
        for tag, outcome in cases:
            self.append(evidence_tag=tag, outcome=outcome)
        packet = self.review()
        self.assertEqual(
            ["HELPFUL", "NOT_HELPFUL", "HARMFUL", "UNKNOWN"],
            [event.effective_outcome for event in packet.ordered_event_reviews],
        )
        rendered = packet.render_text()
        for _, outcome in cases:
            self.assertIn(f"effective_outcome={outcome}", rendered)

    def test_outcome_scope_is_preserved(self) -> None:
        scope = "One exact bounded A6 task family."
        self.append(outcome_scope=scope)
        self.assertEqual(scope, self.review().ordered_event_reviews[0].outcome_scope)

    def test_causal_evidence_identity_is_preserved(self) -> None:
        result = self.append(outcome="HARMFUL")
        receipt = result.event.receipt
        event = self.review().ordered_event_reviews[0]
        self.assertEqual(receipt.causal_evidence_ref, event.causal_evidence_ref)
        self.assertEqual(
            receipt.causal_evidence_sha256,
            event.causal_evidence_sha256,
        )

    def test_use_and_outcome_observer_identity_and_relation_are_preserved(self) -> None:
        self.append(
            use_observer_id="use_observer_exact",
            use_observer_relation="REUSING_RUN_PARTICIPANT",
            outcome_observer_id="outcome_observer_exact",
            outcome_observer_relation="INDEPENDENT",
        )
        event = self.review().ordered_event_reviews[0]
        self.assertEqual("use_observer_exact", event.use_evidence_observer_id)
        self.assertEqual(
            "REUSING_RUN_PARTICIPANT",
            event.use_evidence_observer_relation,
        )
        self.assertEqual("outcome_observer_exact", event.outcome_observer_id)
        self.assertEqual("INDEPENDENT", event.outcome_observer_relation)

    def test_confirmation_class_is_preserved(self) -> None:
        self.append(outcome_observer_relation="INDEPENDENT")
        event = self.review().ordered_event_reviews[0]
        self.assertEqual("INDEPENDENT_CONFIRMATION", event.outcome_confirmation)

    def test_contribution_separation_is_preserved(self) -> None:
        self.append(contribution_separated=False, outcome="UNKNOWN")
        event = self.review().ordered_event_reviews[0]
        self.assertFalse(event.contribution_separated)

    def test_material_and_unknown_human_intervention_are_preserved(self) -> None:
        self.append(evidence_tag="1", intervention="MATERIAL")
        self.append(evidence_tag="2", intervention="UNKNOWN")
        packet = self.review()
        self.assertEqual(
            ["MATERIAL", "UNKNOWN"],
            [event.human_intervention for event in packet.ordered_event_reviews],
        )
        self.assertEqual(
            2,
            packet.aggregate_evidence_signals.material_or_unknown_interventions,
        )

    def test_hold_and_reevaluation_condition_are_preserved(self) -> None:
        self.append(outcome="UNKNOWN")
        event = self.review().ordered_event_reviews[0]
        self.assertEqual("HOLD", event.next_action)
        self.assertTrue(event.reevaluation_condition)
        self.assertEqual(1, self.review().aggregate_evidence_signals.hold_dispositions)

    def test_bounded_stop_and_scope_are_preserved(self) -> None:
        self.append(outcome="HARMFUL", action="STOP")
        event = self.review().ordered_event_reviews[0]
        self.assertEqual("STOP", event.next_action)
        self.assertEqual("Bounded A6 task family 1.", event.stop_scope)
        self.assertEqual(1, self.review().aggregate_evidence_signals.stop_dispositions)

    def test_revise_predecessor_and_successor_lineage_are_preserved(self) -> None:
        self.append(outcome="NOT_HELPFUL", action="REVISE")
        event = self.review().ordered_event_reviews[0]
        self.assertEqual(self.note, event.revision.predecessor)
        self.assertNotEqual(self.note, event.revision.successor)
        self.assertEqual(event.reusing_run_id, event.revision.successor.origin_run_id)
        self.assertEqual(1, self.review().aggregate_evidence_signals.revise_links)

    def test_same_run_and_run_related_claims_remain_distinguishable(self) -> None:
        self.append(
            evidence_tag="1",
            outcome_observer_relation="REUSING_RUN_SELF",
        )
        self.append(
            evidence_tag="2",
            outcome_observer_relation="REUSING_RUN_PARTICIPANT",
        )
        self.append(
            evidence_tag="3",
            outcome_observer_relation="INDEPENDENT",
        )
        packet = self.review()
        self.assertEqual(
            [
                "SAME_RUN_CLAIM",
                "RUN_RELATED_CLAIM",
                "INDEPENDENT_CONFIRMATION",
            ],
            [event.outcome_confirmation for event in packet.ordered_event_reviews],
        )
        signals = packet.aggregate_evidence_signals
        self.assertEqual(1, signals.same_run_outcome_claims)
        self.assertEqual(1, signals.run_related_outcome_claims)
        self.assertEqual(1, signals.independent_outcome_confirmations)

    def test_recorded_run_structure_and_use_evidence_identities_are_preserved(self) -> None:
        appended = self.append(evidence_tag="7", structure="B")
        event = self.review().ordered_event_reviews[0]
        binding = appended.event.receipt.use_evidence.structure_binding
        self.assertEqual(appended.event.recorded_at, event.recorded_at)
        self.assertEqual("run_reuse_7", event.reusing_run_id)
        self.assertEqual(binding.structure_id, event.structure_id)
        self.assertEqual(binding.structure_sha256, event.structure_sha256)
        self.assertEqual(binding.binding_sha256, event.structure_binding_sha256)


class FieldNotesMaturityReviewBoundaryTests(MaturityReviewTestCase):
    def test_a2_injection_is_not_an_a6_input_or_reuse_evidence(self) -> None:
        delivery = reconnect_receipt(self.note)
        packet = self.review()
        self.assertEqual(0, packet.ledger_identity.durable_event_count)
        self.assertEqual("CANDIDATE", packet.evidence_maturity.state)
        self.assertEqual(0, packet.evidence_maturity.reconnect_receipts_ignored)
        self.assertIsNone(packet.current_serving_policy.automatic_injection)
        with self.assertRaises(TypeError):
            review_field_note_maturity(
                self.ledger,
                self.note,
                note_bytes=NOTE_BYTES,
                review_as_of=REVIEW_AS_OF,
                delivery_context=delivery,  # type: ignore[call-arg]
            )

    def test_promotable_remains_reserved_and_unset(self) -> None:
        for tag in ("1", "2", "3"):
            self.append(evidence_tag=tag, outcome="HELPFUL")
        promotion = self.review().evidence_maturity.promotion
        self.assertEqual("PROMOTABLE", promotion.reserved_state)
        self.assertEqual("UNSET", promotion.policy_status)
        self.assertIsNone(promotion.threshold)
        self.assertFalse(promotion.automatically_derivable)

    def test_no_promotion_recommendation_or_score_exists(self) -> None:
        self.append(outcome="HELPFUL")
        packet = self.review()

        def keys(value):
            if isinstance(value, dict):
                result = set(value)
                for nested in value.values():
                    result.update(keys(nested))
                return result
            if isinstance(value, list):
                result = set()
                for nested in value:
                    result.update(keys(nested))
                return result
            return set()

        serialized_keys = keys(packet.as_dict())
        self.assertFalse(any("score" in key for key in serialized_keys))
        self.assertFalse(any("recommend" in key for key in serialized_keys))
        self.assertNotIn("promotion-ready", packet.serialize().casefold())

    def test_serving_policy_remains_separate_and_delayed(self) -> None:
        self.append(outcome="HELPFUL")
        policy = self.review().current_serving_policy
        self.assertEqual("DELAY", policy.derivation)
        self.assertFalse(policy.automatic_derivation_supported)
        self.assertFalse(policy.complete_state_machine_implemented)

    def test_reused_does_not_imply_injection(self) -> None:
        self.append(outcome="HELPFUL")
        packet = self.review()
        self.assertEqual("REUSED", packet.evidence_maturity.state)
        self.assertIsNone(packet.current_serving_policy.automatic_injection)

    def test_canonical_authority_remains_above_advisory_field_notes(self) -> None:
        packet = self.review()
        self.assertEqual(
            ("TOPMOST_CANONICAL", "ADVISORY_FIELD_NOTE"),
            packet.current_serving_policy.authority_precedence,
        )
        self.assertIn(
            "TOPMOST_CANONICAL > ADVISORY_FIELD_NOTE",
            packet.render_text(),
        )

    def test_full_note_body_is_absent_from_serialized_and_text_review(self) -> None:
        self.append()
        packet = self.review()
        private_text = PRIVATE_BODY.decode("utf-8")
        full_note = NOTE_BYTES.decode("utf-8")
        self.assertNotIn(private_text, packet.serialize())
        self.assertNotIn(private_text, packet.render_text())
        self.assertNotIn(full_note, packet.serialize())
        self.assertFalse(packet.claim_boundary.full_note_contents_included)

    def test_historical_evidence_is_not_current_truth(self) -> None:
        self.append(outcome="HELPFUL")
        boundary = self.review().claim_boundary
        self.assertEqual("HISTORICAL_AS_OF_RECORDS", boundary.evidence_scope)
        self.assertEqual("NOT_ESTABLISHED", boundary.current_usefulness)
        self.assertEqual("NOT_PERFORMED", boundary.promotion_decision)
        self.assertFalse(boundary.serving_policy_derived)


class FieldNotesMaturityReviewIntegrityTests(MaturityReviewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.append(outcome="HARMFUL")

    def test_malformed_a4_history_fails_closed(self) -> None:
        raw = self.ledger.events_path.read_bytes()
        self.ledger.events_path.write_bytes(raw[:-1])
        with self.assertRaises(FieldNoteMaturityLedgerIntegrityError):
            self.review()

    def test_tampered_event_fails_closed(self) -> None:
        events = self.parsed_events()
        events[0]["receipt"]["outcome"] = "HELPFUL"
        self.rewrite_events(events)
        with self.assertRaises(FieldNoteMaturityLedgerIntegrityError):
            self.review()

    def test_cross_note_partition_fails_closed(self) -> None:
        other = note_identity(
            field_note_id="fn_a6_other",
            note_path=(
                ".decision-os/field-notes/"
                "2026-08-04-a6-other-bbbbbbbbbb.md"
            ),
        )
        other_ledger = FieldNoteMaturityLedger(self.root, other)
        with self.assertRaisesRegex(
            FieldNoteMaturityReviewValidationError,
            "different A4 Note partition",
        ):
            review_field_note_maturity(
                other_ledger,
                self.note,
                note_bytes=NOTE_BYTES,
                review_as_of=REVIEW_AS_OF,
            )

    def test_changed_note_bytes_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            FieldNoteMaturityReviewValidationError,
            "do not match",
        ):
            review_field_note_maturity(
                self.ledger,
                self.note,
                note_bytes=NOTE_BYTES + b"changed",
                review_as_of=REVIEW_AS_OF,
            )

    def test_unsupported_ledger_schema_fails_closed(self) -> None:
        events = self.parsed_events()
        events[0]["schema"] = "decision-os.unsupported.v9"
        self.rewrite_events(events)
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "Unsupported",
        ):
            self.review()

    def test_invalid_review_as_of_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            FieldNoteMaturityReviewValidationError,
            "RFC 3339",
        ):
            self.review(review_as_of="not-a-timestamp")

    def test_untyped_ledger_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            FieldNoteMaturityReviewValidationError,
            "typed A4 ledger",
        ):
            review_field_note_maturity(
                object(),  # type: ignore[arg-type]
                self.note,
                note_bytes=NOTE_BYTES,
                review_as_of=REVIEW_AS_OF,
            )


if __name__ == "__main__":
    unittest.main()
