from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from decision_os.companion.field_notes_reconnect import (
    FieldNoteReconnectReceipt,
)
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteMaturitySummary,
    FieldNoteOutcomeEvaluation,
    FieldNoteReuseClaim,
    FieldNoteReuseDisposition,
    FieldNoteReuseReceipt,
    FieldNoteUseEvidence,
    assess_field_note_reuse,
    summarize_field_note_maturity,
)


AS_OF = "2026-08-03T12:00:00Z"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def note_identity(
    *,
    field_note_id: str = "fn_a3_candidate",
    note_sha256: str | None = None,
    origin_run_id: str = "run_origin",
    note_path: str = (
        ".decision-os/field-notes/"
        "2026-08-03-a3-reuse-core-aaaaaaaaaa.md"
    ),
) -> FieldNoteIdentity:
    return FieldNoteIdentity(
        note_path=note_path,
        field_note_id=field_note_id,
        note_sha256=note_sha256 or digest("exact note bytes"),
        origin_run_id=origin_run_id,
    )


def use_evidence(
    *,
    evidence_class: str = "RULE_TRACE",
    reusing_run_id: str = "run_reuse",
    structure_id: str = "restart-state-identity-guard",
    structure_sha256: str | None = None,
    evidence_ref: str = "run:run_reuse/rule-trace:guard-1",
    evidence_sha256: str | None = None,
) -> FieldNoteUseEvidence:
    return FieldNoteUseEvidence(
        evidence_class=evidence_class,  # type: ignore[arg-type]
        evidence_origin="IMMEDIATE_COMPLETION_RECORD",
        reusing_run_id=reusing_run_id,
        structure_id=structure_id,
        structure_sha256=structure_sha256 or digest("specific structure"),
        evidence_ref=evidence_ref,
        evidence_sha256=evidence_sha256 or digest("typed use evidence"),
        observer_id="observer_a3",
        observer_relation="INDEPENDENT",
        as_of=AS_OF,
    )


def outcome_evaluation(
    outcome: str = "UNKNOWN",
    *,
    causal: bool = False,
    contribution_separated: bool | None = None,
    observer_relation: str = "INDEPENDENT",
) -> FieldNoteOutcomeEvaluation:
    return FieldNoteOutcomeEvaluation(
        outcome=outcome,  # type: ignore[arg-type]
        scope="The declared bounded test scope.",
        observer_id="outcome_observer",
        observer_relation=observer_relation,  # type: ignore[arg-type]
        as_of=AS_OF,
        causal_evidence_ref=(
            "run:run_reuse/outcome:causal-1" if causal else None
        ),
        causal_evidence_sha256=(digest("causal evidence") if causal else None),
        contribution_separated=(
            outcome != "UNKNOWN"
            if contribution_separated is None
            else contribution_separated
        ),
    )


def disposition(
    action: str,
    *,
    condition: str | None = None,
    stop_scope: str | None = None,
    revision_candidate: FieldNoteIdentity | None = None,
) -> FieldNoteReuseDisposition:
    return FieldNoteReuseDisposition(
        action=action,  # type: ignore[arg-type]
        reevaluation_condition=condition,
        stop_scope=stop_scope,
        revision_candidate=revision_candidate,
    )


def reuse_claim(
    canonical_note: FieldNoteIdentity,
    *,
    claimed_note: FieldNoteIdentity | None = None,
    reusing_run_id: str = "run_reuse",
    evidence: FieldNoteUseEvidence | None = None,
    outcome: FieldNoteOutcomeEvaluation | None = None,
    intervention: str = "NONE",
    next_disposition: FieldNoteReuseDisposition | None = None,
    narrative: str | None = None,
) -> FieldNoteReuseClaim:
    return FieldNoteReuseClaim(
        claimed_note=claimed_note or canonical_note,
        reusing_run_id=reusing_run_id,
        use_evidence=evidence,
        outcome_evaluation=outcome,
        human_intervention=intervention,  # type: ignore[arg-type]
        disposition=next_disposition,
        narrative_claim=narrative,
    )


def reconnect_receipt(
    canonical_note: FieldNoteIdentity,
    *,
    run_id: str = "run_reuse",
) -> FieldNoteReconnectReceipt:
    return FieldNoteReconnectReceipt(
        run_id=run_id,
        state="ACTIVATION_UNKNOWN",
        failure_reason=None,
        metadata_entries_seen=1,
        metadata_candidate_files_seen=1,
        metadata_files_valid=1,
        metadata_bytes_read=700,
        selected_field_note_path=canonical_note.note_path,
        selected_field_note_id=canonical_note.field_note_id,
        selected_metadata_sha256=digest("metadata"),
        selected_full_note_sha256=canonical_note.note_sha256,
        full_note_bytes_read=2743,
        full_notes_injected=1,
        ordinary_distinct_paths_consumed=1,
    )


class FieldNotesReuseAdmissionTests(unittest.TestCase):
    def test_injection_alone_cannot_produce_reused(self) -> None:
        note = note_identity()
        summary = summarize_field_note_maturity(
            note,
            (),
            (reconnect_receipt(note),),
        )
        self.assertEqual("CANDIDATE", summary.state)
        self.assertEqual(1, summary.reconnect_receipts_ignored)

    def test_free_form_i_used_the_note_cannot_produce_reused(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                narrative="I used the Note and it helped.",
                evidence=None,
            ),
        )
        self.assertEqual("CANDIDATE", receipt.state)
        self.assertEqual("USE_EVIDENCE_MISSING", receipt.failure_reason)

    def test_same_run_as_note_origin_cannot_satisfy_reuse(self) -> None:
        note = note_identity(origin_run_id="run_same")
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                reusing_run_id="run_same",
                evidence=use_evidence(reusing_run_id="run_same"),
            ),
        )
        self.assertEqual("CANDIDATE", receipt.state)
        self.assertEqual("ORIGIN_RUN_NOT_DIFFERENT", receipt.failure_reason)

    def test_exact_note_identity_is_required(self) -> None:
        note = note_identity()
        wrong = note_identity(note_sha256=digest("different exact bytes"))
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                claimed_note=wrong,
                evidence=use_evidence(),
            ),
        )
        self.assertEqual("CANDIDATE", receipt.state)
        self.assertEqual("NOTE_IDENTITY_MISMATCH", receipt.failure_reason)

    def test_whole_note_without_specific_structure_is_insufficient(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(
                    structure_id="whole Note",
                    structure_sha256=note.note_sha256,
                ),
            ),
        )
        self.assertEqual("CANDIDATE", receipt.state)
        self.assertEqual("STRUCTURE_NOT_SPECIFIC", receipt.failure_reason)

    def test_rule_trace_can_establish_reuse(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(note, evidence=use_evidence()),
        )
        self.assertEqual("REUSED", receipt.state)
        self.assertEqual("RULE_TRACE", receipt.use_evidence.evidence_class)

    def test_output_artifact_can_establish_reuse(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(
                    evidence_class="OUTPUT_ARTIFACT",
                    evidence_ref="artifact:decision-1/path:result.md",
                    evidence_sha256=digest("verified output artifact"),
                ),
            ),
        )
        self.assertEqual("REUSED", receipt.state)
        self.assertEqual("OUTPUT_ARTIFACT", receipt.use_evidence.evidence_class)

    def test_later_hindsight_resemblance_cannot_establish_reuse(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=None,
                narrative="A later report resembles the Note in hindsight.",
            ),
        )
        self.assertEqual("CANDIDATE", receipt.state)
        self.assertIsNone(receipt.use_evidence)

    def test_use_evidence_rejects_later_narrative_origin(self) -> None:
        with self.assertRaisesRegex(ValueError, "allowed Run window"):
            FieldNoteUseEvidence(
                evidence_class="RULE_TRACE",
                evidence_origin="LATER_NARRATIVE",  # type: ignore[arg-type]
                reusing_run_id="run_reuse",
                structure_id="restart-state-identity-guard",
                structure_sha256=digest("specific structure"),
                evidence_ref="later:narrative",
                evidence_sha256=digest("later narrative"),
                observer_id="observer",
                observer_relation="INDEPENDENT",
                as_of=AS_OF,
            )


class FieldNotesReuseOutcomeTests(unittest.TestCase):
    def test_reused_can_coexist_with_helpful(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation("HELPFUL", causal=True),
                next_disposition=disposition("KEEP"),
            ),
        )
        self.assertEqual(("REUSED", "HELPFUL", "KEEP"), (
            receipt.state,
            receipt.outcome,
            receipt.next_action,
        ))

    def test_reused_can_coexist_with_not_helpful(self) -> None:
        note = note_identity()
        revision = note_identity(
            field_note_id="fn_a3_revision",
            note_sha256=digest("new candidate bytes"),
            origin_run_id="run_reuse",
            note_path=(
                ".decision-os/field-notes/"
                "2026-08-03-a3-revision-bbbbbbbbbb.md"
            ),
        )
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation("NOT_HELPFUL"),
                next_disposition=disposition(
                    "REVISE",
                    revision_candidate=revision,
                ),
            ),
        )
        self.assertEqual("NOT_HELPFUL", receipt.outcome)
        self.assertEqual("REVISE", receipt.next_action)

    def test_reused_can_coexist_with_harmful(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation("HARMFUL", causal=True),
                next_disposition=disposition(
                    "STOP",
                    stop_scope="This exact task family in this repository.",
                ),
            ),
        )
        self.assertEqual("HARMFUL", receipt.outcome)
        self.assertEqual("STOP", receipt.next_action)

    def test_reused_can_coexist_with_unknown(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(note, evidence=use_evidence()),
        )
        self.assertEqual("UNKNOWN", receipt.outcome)
        self.assertEqual("HOLD", receipt.next_action)

    def test_helpful_without_causal_evidence_fails_closed(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation("HELPFUL", causal=False),
                next_disposition=disposition("KEEP"),
            ),
        )
        self.assertEqual("HELPFUL", receipt.claimed_outcome)
        self.assertEqual("UNKNOWN", receipt.outcome)
        self.assertEqual("HOLD", receipt.next_action)

    def test_harmful_without_causal_evidence_becomes_unknown(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation("HARMFUL", causal=False),
                next_disposition=disposition(
                    "STOP",
                    stop_scope="This exact task family.",
                ),
            ),
        )
        self.assertEqual("HARMFUL", receipt.claimed_outcome)
        self.assertEqual("UNKNOWN", receipt.outcome)
        self.assertEqual("HOLD", receipt.next_action)

    def test_material_and_unknown_human_intervention_are_retained(self) -> None:
        note = note_identity()
        for intervention in ("MATERIAL", "UNKNOWN"):
            with self.subTest(intervention=intervention):
                receipt = assess_field_note_reuse(
                    note,
                    reuse_claim(
                        note,
                        evidence=use_evidence(),
                        outcome=outcome_evaluation("UNKNOWN"),
                        intervention=intervention,
                    ),
                )
                self.assertEqual(intervention, receipt.human_intervention)

    def test_unseparated_material_intervention_forces_unknown(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation(
                    "HELPFUL",
                    causal=True,
                    contribution_separated=False,
                ),
                intervention="MATERIAL",
                next_disposition=disposition("KEEP"),
            ),
        )
        self.assertEqual("UNKNOWN", receipt.outcome)
        self.assertEqual("HOLD", receipt.next_action)
        self.assertIn("human intervention", receipt.reevaluation_condition)

    def test_separated_material_intervention_can_preserve_causal_outcome(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation(
                    "HELPFUL",
                    causal=True,
                    contribution_separated=True,
                ),
                intervention="MATERIAL",
                next_disposition=disposition("KEEP"),
            ),
        )
        self.assertEqual("HELPFUL", receipt.outcome)
        self.assertEqual("MATERIAL", receipt.human_intervention)

    def test_unseparated_other_causes_force_unknown(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation(
                    "NOT_HELPFUL",
                    contribution_separated=False,
                ),
                next_disposition=disposition("STOP", stop_scope="Task alpha."),
            ),
        )
        self.assertEqual("UNKNOWN", receipt.outcome)
        self.assertEqual("HOLD", receipt.next_action)
        self.assertIn("other Notes and causes", receipt.reevaluation_condition)

    def test_same_run_outcome_observer_is_not_independent_confirmation(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation(
                    "HELPFUL",
                    causal=True,
                    observer_relation="REUSING_RUN_SELF",
                ),
                next_disposition=disposition("KEEP"),
            ),
        )
        self.assertEqual("SAME_RUN_CLAIM", receipt.outcome_confirmation)


class FieldNotesReuseDispositionTests(unittest.TestCase):
    def test_unknown_requires_hold(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation("UNKNOWN"),
                next_disposition=disposition("KEEP"),
            ),
        )
        self.assertEqual("HOLD", receipt.next_action)

    def test_hold_requires_a_reevaluation_condition(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(note, evidence=use_evidence()),
        )
        self.assertTrue(receipt.reevaluation_condition)
        with self.assertRaisesRegex(ValueError, "re-evaluation condition"):
            replace(receipt, reevaluation_condition=None)

    def test_stop_requires_explicit_bounded_scope(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation("HARMFUL", causal=True),
                next_disposition=disposition(
                    "STOP",
                    stop_scope="Only task family alpha in repository current.",
                ),
            ),
        )
        self.assertEqual("STOP", receipt.next_action)
        self.assertEqual(
            "Only task family alpha in repository current.",
            receipt.stop_scope,
        )

    def test_stop_without_scope_fails_closed_to_hold(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation("HARMFUL", causal=True),
                next_disposition=disposition("STOP"),
            ),
        )
        self.assertEqual("HOLD", receipt.next_action)
        self.assertIsNone(receipt.stop_scope)
        self.assertIn("STOP scope", receipt.reevaluation_condition)

    def test_revise_links_forward_without_mutating_predecessor(self) -> None:
        note = note_identity()
        before = note.as_dict()
        successor = note_identity(
            field_note_id="fn_a3_successor",
            note_sha256=digest("successor bytes"),
            origin_run_id="run_reuse",
            note_path=(
                ".decision-os/field-notes/"
                "2026-08-03-a3-successor-cccccccccc.md"
            ),
        )
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(
                note,
                evidence=use_evidence(),
                outcome=outcome_evaluation("NOT_HELPFUL"),
                next_disposition=disposition(
                    "REVISE",
                    revision_candidate=successor,
                ),
            ),
        )
        self.assertEqual(before, note.as_dict())
        self.assertEqual(note, receipt.revision.predecessor)
        self.assertEqual(successor, receipt.revision.successor)

    def test_global_stop_is_not_an_ordinary_action(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            FieldNoteReuseDisposition(
                action="GLOBAL_STOP",  # type: ignore[arg-type]
            )

    def test_invalid_outcome_action_mapping_is_rejected(self) -> None:
        note = note_identity()
        with self.assertRaisesRegex(ValueError, "invalid for the reuse outcome"):
            assess_field_note_reuse(
                note,
                reuse_claim(
                    note,
                    evidence=use_evidence(),
                    outcome=outcome_evaluation("HELPFUL", causal=True),
                    next_disposition=disposition(
                        "STOP",
                        stop_scope="A bounded scope.",
                    ),
                ),
            )


class FieldNotesReusePromotionBoundaryTests(unittest.TestCase):
    def test_no_automatic_promotable_transition_exists(self) -> None:
        note = note_identity()
        receipts = []
        for index in range(5):
            run_id = f"run_reuse_{index}"
            receipt = assess_field_note_reuse(
                note,
                reuse_claim(
                    note,
                    reusing_run_id=run_id,
                    evidence=use_evidence(
                        reusing_run_id=run_id,
                        evidence_ref=f"run:{run_id}/rule-trace:guard",
                        evidence_sha256=digest(f"evidence {index}"),
                    ),
                ),
            )
            receipts.append(receipt)
        summary = summarize_field_note_maturity(note, receipts)
        self.assertEqual("REUSED", summary.state)
        self.assertEqual("UNSET", summary.promotion.policy_status)
        self.assertIsNone(summary.promotion.threshold)
        self.assertFalse(summary.promotion.automatically_derivable)

    def test_duplicate_evidence_and_repeated_injection_do_not_raise_maturity(
        self,
    ) -> None:
        note = note_identity()
        claim = reuse_claim(note, evidence=use_evidence())
        first = assess_field_note_reuse(note, claim)
        duplicate = assess_field_note_reuse(note, claim)
        summary = summarize_field_note_maturity(
            note,
            (first, duplicate),
            (reconnect_receipt(note), reconnect_receipt(note, run_id="run_2")),
        )
        self.assertEqual("REUSED", summary.state)
        self.assertEqual(1, len(summary.reuse_event_ids))
        self.assertEqual(1, summary.duplicate_reuse_records_ignored)
        self.assertEqual(2, summary.reconnect_receipts_ignored)
        self.assertEqual("UNSET", summary.promotion.policy_status)

    def test_receipt_serialization_preserves_promotion_boundary(self) -> None:
        note = note_identity()
        receipt = assess_field_note_reuse(
            note,
            reuse_claim(note, evidence=use_evidence()),
        )
        projection = receipt.as_dict()
        self.assertEqual(
            {
                "reserved_state": "PROMOTABLE",
                "policy_status": "UNSET",
                "threshold": None,
                "automatically_derivable": False,
            },
            projection["promotion"],
        )

    def test_summary_rejects_cross_note_receipts(self) -> None:
        note = note_identity()
        other = note_identity(
            field_note_id="fn_other",
            note_sha256=digest("other note"),
        )
        receipt = assess_field_note_reuse(
            other,
            reuse_claim(other, evidence=use_evidence()),
        )
        with self.assertRaisesRegex(ValueError, "different Field Note"):
            summarize_field_note_maturity(note, (receipt,))


class FieldNotesReuseProtectedArtifactTests(unittest.TestCase):
    def test_local_protected_artifacts_match_fixed_identities(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        expected = {
            Path(
                ".decision-os/field-notes/"
                "2026-08-03-topmost-canonical-state-restart-guard-"
                "lcmwhjvkpf.md"
            ): (
                2743,
                "3c2e45460f21a2346a8d100ebfefc6ed079994e687a70911e5f4a8954cf2d05d",
            ),
            Path("validation/companion_live_task_001.md"): (
                779,
                "e28815932e0a3baf34bc0c6b0e2f9a03130e10260765367458a53116502845cf",
            ),
            Path("validation/companion_manual_live_run_probe_v0_1.md"): (
                539,
                "f68b3a1f47136782cbb5ade4c4686724c2b877eaaffe52bdb81aa72ae19c6344",
            ),
            Path("validation/companion_medium_live_task_001.md"): (
                4632,
                "a096b2455d7d57d24f3dd0a2b1e5b7c26a782e6870f2e076cdebdf7348a5a411",
            ),
            Path("validation/companion_medium_live_task_002.md"): (
                4139,
                "0f2203beddb5469dfe00deeae392277cd0634aa5b0713296efb2a754a59b8bba",
            ),
        }
        missing = [path for path in expected if not (repository / path).exists()]
        if missing:
            self.skipTest("Protected creator artifacts are local-only.")
        for relative, (size, sha256) in expected.items():
            with self.subTest(path=relative.as_posix()):
                data = (repository / relative).read_bytes()
                self.assertEqual(size, len(data))
                self.assertEqual(sha256, hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    unittest.main()
