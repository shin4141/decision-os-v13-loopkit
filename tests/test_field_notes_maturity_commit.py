from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from decision_os.companion.field_notes_maturity_commit import (
    FieldNoteMaturityCommitConfirmationError,
    FieldNoteMaturityCommitRequest,
    FieldNoteMaturityCommitValidationError,
    commit_field_note_maturity,
)
from decision_os.companion.field_notes_maturity_ledger import (
    FieldNoteMaturityLedger,
    FieldNoteMaturityLedgerIntegrityError,
)
from decision_os.companion.field_notes_reconnect import (
    FieldNoteReconnectReceipt,
)
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteOutcomeEvaluation,
    FieldNoteReuseClaim,
    FieldNoteReuseDisposition,
    FieldNoteStructureBinding,
    FieldNoteUseEvidence,
    bind_field_note_structure,
)


AS_OF = "2026-08-04T09:00:00Z"
RECORDED_AT = "2026-08-04T09:01:00Z"
STRUCTURE_BYTES = b"Verify canonical state before restart."
NOTE_BYTES = (
    b"# A5 Operational Maturity Commit Bridge\n\n"
    b"## Decision / Pattern\n\n"
    + STRUCTURE_BYTES
    + b"\n\n## Limits\n\nCurrent canonical authority always wins.\n"
)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: str) -> str:
    return digest_bytes(value.encode("utf-8"))


def note_identity(
    *,
    field_note_id: str = "fn_a5_candidate",
    note_bytes: bytes = NOTE_BYTES,
    note_path: str = (
        ".decision-os/field-notes/"
        "2026-08-04-a5-commit-bridge-aaaaaaaaaa.md"
    ),
    origin_run_id: str = "run_origin",
) -> FieldNoteIdentity:
    return FieldNoteIdentity(
        note_path=note_path,
        field_note_id=field_note_id,
        note_sha256=digest_bytes(note_bytes),
        origin_run_id=origin_run_id,
    )


def structure_binding(
    note: FieldNoteIdentity,
    *,
    note_bytes: bytes = NOTE_BYTES,
) -> FieldNoteStructureBinding:
    start = note_bytes.index(STRUCTURE_BYTES)
    return bind_field_note_structure(
        note,
        note_bytes,
        structure_id="restart-state-identity-guard",
        start_byte=start,
        end_byte=start + len(STRUCTURE_BYTES),
    )


def use_evidence(
    note: FieldNoteIdentity,
    *,
    note_bytes: bytes = NOTE_BYTES,
    run_suffix: str = "1",
    evidence_class: str = "RULE_TRACE",
    binding: FieldNoteStructureBinding | None = None,
) -> FieldNoteUseEvidence:
    reusing_run_id = f"run_reuse_{run_suffix}"
    return FieldNoteUseEvidence(
        evidence_class=evidence_class,  # type: ignore[arg-type]
        evidence_origin="IMMEDIATE_COMPLETION_RECORD",
        reusing_run_id=reusing_run_id,
        structure_binding=binding or structure_binding(note, note_bytes=note_bytes),
        evidence_ref=f"run:{reusing_run_id}/evidence:guard",
        evidence_sha256=digest(f"use-evidence-{run_suffix}"),
        observer_id="observer_a5",
        observer_relation="INDEPENDENT",
        as_of=AS_OF,
    )


def reuse_claim(
    note: FieldNoteIdentity,
    *,
    note_bytes: bytes = NOTE_BYTES,
    run_suffix: str = "1",
    evidence_class: str = "RULE_TRACE",
    outcome: str = "UNKNOWN",
    action: str | None = None,
    intervention: str = "NONE",
    evidence: FieldNoteUseEvidence | None = None,
    include_evidence: bool = True,
    claimed_note: FieldNoteIdentity | None = None,
    narrative: str | None = None,
) -> FieldNoteReuseClaim:
    reusing_run_id = f"run_reuse_{run_suffix}"
    typed_evidence = evidence
    if typed_evidence is None and include_evidence:
        typed_evidence = use_evidence(
            note,
            note_bytes=note_bytes,
            run_suffix=run_suffix,
            evidence_class=evidence_class,
        )
    evaluation = None
    if outcome != "UNKNOWN":
        causal = outcome in {"HELPFUL", "HARMFUL"}
        evaluation = FieldNoteOutcomeEvaluation(
            outcome=outcome,  # type: ignore[arg-type]
            scope="The bounded A5 test scope.",
            observer_id="outcome_observer_a5",
            observer_relation="INDEPENDENT",
            as_of=AS_OF,
            causal_evidence_ref=(
                f"run:{reusing_run_id}/causal" if causal else None
            ),
            causal_evidence_sha256=(
                digest(f"causal-evidence-{run_suffix}") if causal else None
            ),
            contribution_separated=True,
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
            stop_scope=f"Bounded task family {run_suffix}.",
        )
    elif action == "REVISE":
        successor_bytes = note_bytes + run_suffix.encode("ascii")
        successor = note_identity(
            field_note_id=f"fn_a5_successor_{run_suffix}",
            note_bytes=successor_bytes,
            note_path=(
                ".decision-os/field-notes/"
                f"2026-08-04-a5-successor-{run_suffix.zfill(10)}.md"
            ),
            origin_run_id=reusing_run_id,
        )
        disposition = FieldNoteReuseDisposition(
            action="REVISE",
            revision_candidate=successor,
        )
    return FieldNoteReuseClaim(
        claimed_note=claimed_note or note,
        reusing_run_id=reusing_run_id,
        use_evidence=typed_evidence,
        outcome_evaluation=evaluation,
        human_intervention=intervention,  # type: ignore[arg-type]
        disposition=disposition,
        narrative_claim=narrative,
    )


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


class MaturityCommitTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "maturity-ledger-v0.1"
        self.note = note_identity()
        self.ledger = FieldNoteMaturityLedger(self.root, self.note)

    def request(
        self,
        *,
        claim: FieldNoteReuseClaim | None = None,
        note: FieldNoteIdentity | None = None,
        note_bytes: bytes = NOTE_BYTES,
        recorded_at: str = RECORDED_AT,
        delivery_context: FieldNoteReconnectReceipt | None = None,
    ) -> FieldNoteMaturityCommitRequest:
        return FieldNoteMaturityCommitRequest(
            note=note or self.note,
            note_bytes=note_bytes,
            reuse_claim=(reuse_claim(self.note) if claim is None else claim),
            recorded_at=recorded_at,
            delivery_context=delivery_context,
        )

    def commit(
        self,
        *,
        claim: FieldNoteReuseClaim | None = None,
        ledger: FieldNoteMaturityLedger | None = None,
        delivery_context: FieldNoteReconnectReceipt | None = None,
        recorded_at: str = RECORDED_AT,
    ):
        request = self.request(
            claim=claim,
            delivery_context=delivery_context,
            recorded_at=recorded_at,
        )
        return commit_field_note_maturity(ledger or self.ledger, request)


class FieldNotesMaturityCommitFlowTests(MaturityCommitTestCase):
    def test_valid_typed_evidence_is_recorded_only_after_a4_read_back(self) -> None:
        class ReadbackSpyLedger(FieldNoteMaturityLedger):
            reconstruct_calls = 0

            def reconstruct(self, *, note_bytes: bytes):
                self.reconstruct_calls += 1
                return super().reconstruct(note_bytes=note_bytes)

        ledger = ReadbackSpyLedger(self.root, self.note)
        result = self.commit(ledger=ledger)
        self.assertEqual("RECORDED", result.status)
        self.assertTrue(result.durable_commit_confirmed)
        self.assertEqual(1, ledger.reconstruct_calls)
        self.assertEqual(result.assessment, result.append_result.event.receipt)
        self.assertEqual(RECORDED_AT, result.append_result.event.recorded_at)
        self.assertIn(
            result.assessment.reuse_event_id,
            result.durable_snapshot.evidence_maturity.reuse_event_ids,
        )

    def test_duplicate_retry_returns_already_recorded(self) -> None:
        first = self.commit()
        second = self.commit(recorded_at="2026-08-04T09:02:00Z")
        self.assertEqual("RECORDED", first.status)
        self.assertEqual("ALREADY_RECORDED", second.status)
        self.assertTrue(second.durable_commit_confirmed)
        self.assertEqual(first.durable_snapshot, second.durable_snapshot)

    def test_duplicate_retry_does_not_change_ledger_bytes(self) -> None:
        self.commit()
        events_before = self.ledger.events_path.read_bytes()
        head_before = self.ledger.head_path.read_bytes()
        self.commit(recorded_at="2026-08-04T09:02:00Z")
        self.assertEqual(events_before, self.ledger.events_path.read_bytes())
        self.assertEqual(head_before, self.ledger.head_path.read_bytes())

    def test_duplicate_retry_does_not_increase_event_count(self) -> None:
        self.commit()
        second = self.commit()
        self.assertEqual(1, len(second.durable_snapshot.events))
        self.assertEqual(
            1,
            len(second.durable_snapshot.evidence_maturity.reuse_event_ids),
        )

    def test_candidate_does_not_enter_a4(self) -> None:
        claim = reuse_claim(
            self.note,
            include_evidence=False,
            narrative="I used the Note.",
        )
        result = self.commit(claim=claim)
        self.assertEqual("NOT_REUSED", result.status)
        self.assertFalse(result.durable_commit_confirmed)
        self.assertEqual("CANDIDATE", result.assessment.state)
        self.assertIsNone(result.append_result)
        self.assertIsNone(result.durable_snapshot)
        self.assertFalse(self.root.exists())

    def test_a2_injection_alone_does_not_enter_a4(self) -> None:
        request = FieldNoteMaturityCommitRequest(
            note=self.note,
            note_bytes=NOTE_BYTES,
            reuse_claim=None,
            recorded_at=RECORDED_AT,
            delivery_context=reconnect_receipt(self.note),
        )
        result = commit_field_note_maturity(self.ledger, request)
        self.assertEqual("NOT_REUSED", result.status)
        self.assertEqual("USE_EVIDENCE_MISSING", result.assessment.failure_reason)
        self.assertEqual(request.delivery_context, result.delivery_context)
        self.assertFalse(self.root.exists())

    def test_narrative_reuse_claim_does_not_enter_a4(self) -> None:
        result = self.commit(
            claim=reuse_claim(
                self.note,
                include_evidence=False,
                narrative="I used the Note and it helped.",
            )
        )
        self.assertEqual("NOT_REUSED", result.status)
        self.assertFalse(self.root.exists())

    def test_task_success_alone_does_not_enter_a4(self) -> None:
        result = self.commit(
            claim=reuse_claim(
                self.note,
                include_evidence=False,
                narrative="The task completed successfully.",
            )
        )
        self.assertEqual("NOT_REUSED", result.status)
        self.assertFalse(self.root.exists())

    def test_human_approval_alone_does_not_enter_a4(self) -> None:
        result = self.commit(
            claim=reuse_claim(
                self.note,
                include_evidence=False,
                intervention="NON_DECISIVE",
                narrative="The human approved the result.",
            )
        )
        self.assertEqual("NOT_REUSED", result.status)
        self.assertFalse(self.root.exists())

    def test_exact_claimed_note_mismatch_fails_closed_to_candidate(self) -> None:
        other = replace(self.note, field_note_id="fn_a5_other")
        result = self.commit(
            claim=reuse_claim(self.note, claimed_note=other)
        )
        self.assertEqual("NOT_REUSED", result.status)
        self.assertEqual("NOTE_IDENTITY_MISMATCH", result.assessment.failure_reason)
        self.assertFalse(self.root.exists())

    def test_different_a4_note_partition_is_rejected(self) -> None:
        other = replace(self.note, field_note_id="fn_a5_other")
        other_ledger = FieldNoteMaturityLedger(self.root, other)
        with self.assertRaisesRegex(
            FieldNoteMaturityCommitValidationError,
            "different A4 Note partition",
        ):
            commit_field_note_maturity(other_ledger, self.request())

    def test_changed_note_bytes_are_rejected_before_assessment(self) -> None:
        with self.assertRaisesRegex(
            FieldNoteMaturityCommitValidationError,
            "do not match",
        ):
            self.request(note_bytes=NOTE_BYTES + b"changed")
        self.assertFalse(self.root.exists())

    def test_invalid_recorded_at_is_rejected_before_assessment(self) -> None:
        with self.assertRaisesRegex(
            FieldNoteMaturityCommitValidationError,
            "recorded_at",
        ):
            self.request(recorded_at="not-a-timestamp")
        self.assertFalse(self.root.exists())

    def test_invalid_structure_binding_fails_closed_to_candidate(self) -> None:
        binding = replace(
            structure_binding(self.note),
            structure_sha256=digest("wrong structure"),
        )
        evidence = use_evidence(self.note, binding=binding)
        result = self.commit(
            claim=reuse_claim(self.note, evidence=evidence)
        )
        self.assertEqual("NOT_REUSED", result.status)
        self.assertEqual(
            "STRUCTURE_BINDING_INVALID",
            result.assessment.failure_reason,
        )
        self.assertFalse(self.root.exists())

    def test_origin_and_reusing_runs_must_differ(self) -> None:
        evidence = use_evidence(self.note, run_suffix="origin")
        evidence = replace(evidence, reusing_run_id=self.note.origin_run_id)
        claim = FieldNoteReuseClaim(
            claimed_note=self.note,
            reusing_run_id=self.note.origin_run_id,
            use_evidence=evidence,
            outcome_evaluation=None,
            human_intervention="NONE",
            disposition=None,
        )
        result = self.commit(claim=claim)
        self.assertEqual("NOT_REUSED", result.status)
        self.assertEqual(
            "ORIGIN_RUN_NOT_DIFFERENT",
            result.assessment.failure_reason,
        )
        self.assertFalse(self.root.exists())


class FieldNotesMaturityCommitEvidenceTests(MaturityCommitTestCase):
    def test_rule_trace_evidence_is_preserved(self) -> None:
        result = self.commit(
            claim=reuse_claim(self.note, evidence_class="RULE_TRACE")
        )
        self.assertEqual("RULE_TRACE", result.assessment.use_evidence.evidence_class)
        self.assertEqual(result.assessment, result.append_result.event.receipt)

    def test_output_artifact_evidence_is_preserved(self) -> None:
        result = self.commit(
            claim=reuse_claim(self.note, evidence_class="OUTPUT_ARTIFACT")
        )
        self.assertEqual(
            "OUTPUT_ARTIFACT",
            result.assessment.use_evidence.evidence_class,
        )
        self.assertEqual(result.assessment, result.append_result.event.receipt)

    def test_helpful_is_preserved(self) -> None:
        result = self.commit(
            claim=reuse_claim(self.note, outcome="HELPFUL")
        )
        self.assertEqual("HELPFUL", result.assessment.outcome)
        self.assertEqual("KEEP", result.assessment.next_action)

    def test_not_helpful_is_preserved(self) -> None:
        result = self.commit(
            claim=reuse_claim(self.note, outcome="NOT_HELPFUL")
        )
        self.assertEqual("NOT_HELPFUL", result.assessment.outcome)
        self.assertEqual("STOP", result.assessment.next_action)

    def test_harmful_is_preserved(self) -> None:
        result = self.commit(
            claim=reuse_claim(self.note, outcome="HARMFUL")
        )
        self.assertEqual("HARMFUL", result.assessment.outcome)
        self.assertEqual("STOP", result.assessment.next_action)

    def test_unknown_defaults_to_reused_and_hold(self) -> None:
        result = self.commit(claim=reuse_claim(self.note))
        self.assertEqual("REUSED", result.assessment.state)
        self.assertEqual("UNKNOWN", result.assessment.outcome)
        self.assertEqual("HOLD", result.assessment.next_action)
        self.assertTrue(result.assessment.reevaluation_condition)

    def test_causal_evidence_and_outcome_scope_are_preserved(self) -> None:
        result = self.commit(
            claim=reuse_claim(self.note, outcome="HELPFUL")
        )
        self.assertEqual("The bounded A5 test scope.", result.assessment.outcome_scope)
        self.assertTrue(result.assessment.causal_evidence_ref)
        self.assertTrue(result.assessment.causal_evidence_sha256)
        self.assertTrue(result.assessment.contribution_separated)
        self.assertEqual(
            "outcome_observer_a5",
            result.assessment.outcome_observer_id,
        )
        self.assertEqual(
            "INDEPENDENT",
            result.assessment.outcome_observer_relation,
        )
        self.assertEqual(
            "INDEPENDENT_CONFIRMATION",
            result.assessment.outcome_confirmation,
        )

    def test_human_intervention_is_preserved(self) -> None:
        result = self.commit(
            claim=reuse_claim(
                self.note,
                outcome="HELPFUL",
                intervention="MATERIAL",
            )
        )
        self.assertEqual("MATERIAL", result.assessment.human_intervention)
        self.assertEqual("HELPFUL", result.assessment.outcome)

    def test_bounded_stop_is_preserved(self) -> None:
        result = self.commit(
            claim=reuse_claim(self.note, outcome="HARMFUL")
        )
        self.assertEqual("STOP", result.assessment.next_action)
        self.assertEqual("Bounded task family 1.", result.assessment.stop_scope)

    def test_revise_preserves_forward_predecessor_and_successor(self) -> None:
        result = self.commit(
            claim=reuse_claim(
                self.note,
                outcome="NOT_HELPFUL",
                action="REVISE",
            )
        )
        revision = result.assessment.revision
        self.assertEqual(self.note, revision.predecessor)
        self.assertNotEqual(self.note, revision.successor)
        self.assertEqual(
            result.assessment.reusing_run_id,
            revision.successor.origin_run_id,
        )


class FieldNotesMaturityCommitIntegrityTests(MaturityCommitTestCase):
    def test_optional_a2_provenance_does_not_change_maturity(self) -> None:
        without_root = Path(self.temporary.name) / "without-a2"
        with_root = Path(self.temporary.name) / "with-a2"
        without = commit_field_note_maturity(
            FieldNoteMaturityLedger(without_root, self.note),
            self.request(),
        )
        context = reconnect_receipt(self.note)
        with_context = commit_field_note_maturity(
            FieldNoteMaturityLedger(with_root, self.note),
            self.request(delivery_context=context),
        )
        self.assertEqual(without.assessment, with_context.assessment)
        self.assertEqual(
            without.durable_snapshot.evidence_maturity,
            with_context.durable_snapshot.evidence_maturity,
        )
        self.assertEqual(
            0,
            with_context.durable_snapshot.evidence_maturity.reconnect_receipts_ignored,
        )
        self.assertEqual(context, with_context.delivery_context)

    def test_append_failure_cannot_return_committed_success(self) -> None:
        class AppendFailureLedger(FieldNoteMaturityLedger):
            def append_receipt(self, *args, **kwargs):
                raise FieldNoteMaturityLedgerIntegrityError(
                    "simulated A4 append failure"
                )

        ledger = AppendFailureLedger(self.root, self.note)
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "simulated A4 append failure",
        ):
            self.commit(ledger=ledger)
        self.assertFalse(self.root.exists())

    def test_read_back_integrity_failure_cannot_return_committed_success(self) -> None:
        class ReadbackFailureLedger(FieldNoteMaturityLedger):
            def reconstruct(self, *, note_bytes: bytes):
                raise FieldNoteMaturityLedgerIntegrityError(
                    "simulated A4 read-back failure"
                )

        ledger = ReadbackFailureLedger(self.root, self.note)
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "simulated A4 read-back failure",
        ):
            self.commit(ledger=ledger)
        events = FieldNoteMaturityLedger(self.root, self.note).read_events(
            note_bytes=NOTE_BYTES
        )
        self.assertEqual(1, len(events))
        recovered = self.commit(
            ledger=FieldNoteMaturityLedger(self.root, self.note)
        )
        self.assertEqual("ALREADY_RECORDED", recovered.status)
        self.assertEqual(1, len(recovered.durable_snapshot.events))

    def test_unconfirmed_read_back_cannot_return_committed_success(self) -> None:
        class MissingEventLedger(FieldNoteMaturityLedger):
            def reconstruct(self, *, note_bytes: bytes):
                snapshot = super().reconstruct(note_bytes=note_bytes)
                return replace(snapshot, events=())

        ledger = MissingEventLedger(self.root, self.note)
        with self.assertRaisesRegex(
            FieldNoteMaturityCommitConfirmationError,
            "did not confirm",
        ):
            self.commit(ledger=ledger)

    def test_retry_after_simulated_response_loss_reconciles_idempotently(self) -> None:
        class ResponseLossLedger(FieldNoteMaturityLedger):
            failed = False

            def append_receipt(self, *args, **kwargs):
                result = super().append_receipt(*args, **kwargs)
                if not self.failed:
                    self.failed = True
                    raise FieldNoteMaturityLedgerIntegrityError(
                        "simulated response loss after append"
                    )
                return result

        lossy = ResponseLossLedger(self.root, self.note)
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "response loss",
        ):
            self.commit(ledger=lossy)
        events_before = lossy.events_path.read_bytes()
        recovered = self.commit(
            ledger=FieldNoteMaturityLedger(self.root, self.note)
        )
        self.assertEqual("ALREADY_RECORDED", recovered.status)
        self.assertEqual(1, len(recovered.durable_snapshot.events))
        self.assertEqual(events_before, lossy.events_path.read_bytes())

    def test_serving_policy_remains_separate_and_delayed(self) -> None:
        result = self.commit()
        policy = result.durable_snapshot.current_serving_policy
        self.assertEqual("REUSED", result.durable_snapshot.evidence_maturity.state)
        self.assertEqual("DELAY", policy.derivation)
        self.assertFalse(policy.automatic_derivation_supported)
        self.assertFalse(policy.complete_state_machine_implemented)

    def test_promotable_remains_unset(self) -> None:
        result = self.commit()
        promotion = result.durable_snapshot.evidence_maturity.promotion
        self.assertEqual("PROMOTABLE", promotion.reserved_state)
        self.assertEqual("UNSET", promotion.policy_status)
        self.assertIsNone(promotion.threshold)
        self.assertFalse(promotion.automatically_derivable)

    def test_reused_does_not_imply_injection(self) -> None:
        result = self.commit()
        policy = result.durable_snapshot.current_serving_policy
        self.assertIsNone(result.delivery_context)
        self.assertIsNone(policy.automatic_injection)

    def test_canonical_authority_remains_above_field_notes(self) -> None:
        result = self.commit()
        self.assertEqual(
            ("TOPMOST_CANONICAL", "ADVISORY_FIELD_NOTE"),
            result.durable_snapshot.current_serving_policy.authority_precedence,
        )

    def test_existing_note_bytes_remain_unchanged(self) -> None:
        before = bytes(NOTE_BYTES)
        self.commit()
        self.assertEqual(before, NOTE_BYTES)
        self.assertEqual(self.note.note_sha256, digest_bytes(NOTE_BYTES))

    def test_result_serialization_is_deterministic(self) -> None:
        first = self.commit()
        second = self.commit()
        self.assertEqual(first.durable_snapshot, second.durable_snapshot)
        self.assertEqual(
            first.as_dict()["durable_snapshot"],
            second.as_dict()["durable_snapshot"],
        )


if __name__ == "__main__":
    unittest.main()
