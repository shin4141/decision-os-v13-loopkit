from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from decision_os.companion.field_notes_maturity_ledger import (
    GENESIS_EVENT_SHA256,
    LEDGER_EVENT_SCHEMA,
    FieldNoteMaturityLedger,
    FieldNoteMaturityLedgerIntegrityError,
    FieldNoteMaturityLedgerValidationError,
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
    FieldNoteReuseReceipt,
    FieldNoteUseEvidence,
    assess_field_note_reuse,
    bind_field_note_structure,
)


AS_OF = "2026-08-03T12:00:00Z"
RECORDED_AT = "2026-08-03T12:01:00Z"
STRUCTURE_BYTES = b"Verify canonical state before restart."
NOTE_BYTES = (
    b"# A4 Durable Maturity Ledger\n\n"
    b"## Decision / Pattern\n\n"
    + STRUCTURE_BYTES
    + b"\n\n## Limits\n\nCurrent authority always wins.\n"
)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: str) -> str:
    return digest_bytes(value.encode("utf-8"))


def note_identity(
    *,
    field_note_id: str = "fn_a4_candidate",
    note_bytes: bytes = NOTE_BYTES,
    note_path: str = (
        ".decision-os/field-notes/"
        "2026-08-03-a4-ledger-aaaaaaaaaa.md"
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
    note_bytes: bytes = NOTE_BYTES,
    run_suffix: str = "1",
    outcome: str = "UNKNOWN",
    action: str | None = None,
    intervention: str = "NONE",
    evidence_class: str = "RULE_TRACE",
) -> FieldNoteReuseReceipt:
    reusing_run_id = f"run_reuse_{run_suffix}"
    start = note_bytes.index(STRUCTURE_BYTES)
    binding = bind_field_note_structure(
        note,
        note_bytes,
        structure_id="restart-state-identity-guard",
        start_byte=start,
        end_byte=start + len(STRUCTURE_BYTES),
    )
    evidence = FieldNoteUseEvidence(
        evidence_class=evidence_class,  # type: ignore[arg-type]
        evidence_origin="IMMEDIATE_COMPLETION_RECORD",
        reusing_run_id=reusing_run_id,
        structure_binding=binding,
        evidence_ref=f"run:{reusing_run_id}/evidence:guard",
        evidence_sha256=digest(f"evidence-{run_suffix}"),
        observer_id="observer_a4",
        observer_relation="INDEPENDENT",
        as_of=AS_OF,
    )
    evaluation = None
    if outcome != "UNKNOWN":
        causal = outcome in {"HELPFUL", "HARMFUL"}
        evaluation = FieldNoteOutcomeEvaluation(
            outcome=outcome,  # type: ignore[arg-type]
            scope="The bounded A4 test scope.",
            observer_id="outcome_observer_a4",
            observer_relation="INDEPENDENT",
            as_of=AS_OF,
            causal_evidence_ref=(
                f"run:{reusing_run_id}/causal" if causal else None
            ),
            causal_evidence_sha256=(
                digest(f"causal-{run_suffix}") if causal else None
            ),
            contribution_separated=True,
        )
    disposition = None
    if action == "KEEP":
        disposition = FieldNoteReuseDisposition(action="KEEP")
    elif action == "STOP":
        disposition = FieldNoteReuseDisposition(
            action="STOP",
            stop_scope=f"Bounded task family {run_suffix}.",
        )
    elif action == "REVISE":
        successor = note_identity(
            field_note_id=f"fn_a4_successor_{run_suffix}",
            note_bytes=(note_bytes + run_suffix.encode("ascii")),
            note_path=(
                ".decision-os/field-notes/"
                f"2026-08-03-a4-successor-{run_suffix.zfill(10)}.md"
            ),
            origin_run_id=reusing_run_id,
        )
        disposition = FieldNoteReuseDisposition(
            action="REVISE",
            revision_candidate=successor,
        )
    claim = FieldNoteReuseClaim(
        claimed_note=note,
        reusing_run_id=reusing_run_id,
        use_evidence=evidence,
        outcome_evaluation=evaluation,
        human_intervention=intervention,  # type: ignore[arg-type]
        disposition=disposition,
    )
    receipt = assess_field_note_reuse(note, claim, note_bytes=note_bytes)
    if receipt.state != "REUSED":
        raise AssertionError("test fixture failed to produce REUSED")
    return receipt


def candidate_receipt(note: FieldNoteIdentity) -> FieldNoteReuseReceipt:
    claim = FieldNoteReuseClaim(
        claimed_note=note,
        reusing_run_id="run_candidate",
        use_evidence=None,
        outcome_evaluation=None,
        human_intervention="NONE",
        disposition=None,
        narrative_claim="I used the Note.",
    )
    return assess_field_note_reuse(note, claim, note_bytes=NOTE_BYTES)


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


class LedgerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "maturity-ledger-v0.1"
        self.note = note_identity()
        self.ledger = FieldNoteMaturityLedger(self.root, self.note)

    def append(
        self,
        receipt: FieldNoteReuseReceipt,
        *,
        ledger: FieldNoteMaturityLedger | None = None,
        note_bytes: bytes = NOTE_BYTES,
    ):
        return (ledger or self.ledger).append_receipt(
            receipt,
            note_bytes=note_bytes,
            recorded_at=RECORDED_AT,
        )

    def parsed_lines(
        self,
        ledger: FieldNoteMaturityLedger | None = None,
    ) -> list[dict]:
        path = (ledger or self.ledger).events_path
        return [json.loads(line) for line in path.read_text().splitlines()]

    def rewrite_lines(
        self,
        events: list[dict],
        ledger: FieldNoteMaturityLedger | None = None,
    ) -> None:
        path = (ledger or self.ledger).events_path
        payload = "".join(f"{canonical_json(event)}\n" for event in events)
        path.write_text(payload)

    @staticmethod
    def rehash_event(event: dict) -> None:
        body = {key: value for key, value in event.items() if key != "event_sha256"}
        event["event_sha256"] = digest(canonical_json(body))


class FieldNotesMaturityLedgerAdmissionTests(LedgerTestCase):
    def test_valid_a3_reused_receipt_is_durably_recorded(self) -> None:
        receipt = reuse_receipt(self.note)
        result = self.append(receipt)
        self.assertTrue(result.appended)
        self.assertTrue(self.ledger.events_path.is_file())
        self.assertTrue(self.ledger.head_path.is_file())
        self.assertEqual(0, result.event.sequence)
        self.assertEqual(receipt, result.event.receipt)
        self.assertEqual(
            (result.event,),
            self.ledger.read_events(note_bytes=NOTE_BYTES),
        )

    def test_candidate_receipt_cannot_enter_ledger(self) -> None:
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerValidationError,
            "not valid|Only typed",
        ):
            self.append(candidate_receipt(self.note))
        self.assertFalse(self.root.exists())

    def test_a2_injection_alone_cannot_enter_ledger(self) -> None:
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerValidationError,
            "Only typed A3",
        ):
            self.append(reconnect_receipt(self.note))  # type: ignore[arg-type]
        self.assertFalse(self.root.exists())

    def test_free_form_narrative_cannot_enter_ledger(self) -> None:
        receipt = candidate_receipt(self.note)
        self.assertEqual("USE_EVIDENCE_MISSING", receipt.failure_reason)
        with self.assertRaises(FieldNoteMaturityLedgerValidationError):
            self.append(receipt)

    def test_exact_note_and_structure_identity_are_preserved(self) -> None:
        receipt = reuse_receipt(self.note)
        event = self.append(receipt).event
        stored = event.receipt.use_evidence.structure_binding
        self.assertEqual(self.note, event.receipt.note)
        self.assertEqual(self.note, stored.note)
        self.assertEqual(digest_bytes(STRUCTURE_BYTES), stored.structure_sha256)

    def test_receipt_for_another_note_is_rejected(self) -> None:
        other_bytes = NOTE_BYTES.replace(b"Current", b"Topmost")
        other = note_identity(
            field_note_id="fn_a4_other",
            note_bytes=other_bytes,
            note_path=(
                ".decision-os/field-notes/"
                "2026-08-03-a4-other-bbbbbbbbbb.md"
            ),
        )
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerValidationError,
            "exact Note partition",
        ):
            self.append(
                reuse_receipt(other, note_bytes=other_bytes),
                note_bytes=other_bytes,
            )

    def test_changed_note_identity_is_rejected(self) -> None:
        changed = replace(self.note, field_note_id="fn_a4_changed")
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerValidationError,
            "exact Note partition",
        ):
            self.append(reuse_receipt(changed))

    def test_duplicate_append_is_byte_idempotent(self) -> None:
        receipt = reuse_receipt(self.note)
        first = self.append(receipt)
        before = self.ledger.events_path.read_bytes()
        head_before = self.ledger.head_path.read_bytes()
        second = self.append(receipt)
        self.assertTrue(first.appended)
        self.assertFalse(second.appended)
        self.assertEqual(first.event, second.event)
        self.assertEqual(before, self.ledger.events_path.read_bytes())
        self.assertEqual(head_before, self.ledger.head_path.read_bytes())

    def test_duplicate_append_does_not_inflate_reconstruction(self) -> None:
        receipt = reuse_receipt(self.note)
        self.append(receipt)
        self.append(receipt)
        snapshot = self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        self.assertEqual(1, len(snapshot.events))
        self.assertEqual(1, len(snapshot.evidence_maturity.reuse_event_ids))

    def test_same_event_identity_with_different_payload_is_rejected(self) -> None:
        helpful = reuse_receipt(
            self.note,
            outcome="HELPFUL",
            action="KEEP",
        )
        harmful = reuse_receipt(
            self.note,
            outcome="HARMFUL",
            action="STOP",
        )
        self.assertEqual(helpful.reuse_event_id, harmful.reuse_event_id)
        self.append(helpful)
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerValidationError,
            "collides",
        ):
            self.append(harmful)


class FieldNotesMaturityLedgerRetentionTests(LedgerTestCase):
    def test_all_outcomes_are_retained_not_only_positive_results(self) -> None:
        cases = (
            ("HELPFUL", "KEEP"),
            ("NOT_HELPFUL", "STOP"),
            ("HARMFUL", "STOP"),
            ("UNKNOWN", None),
        )
        for index, (outcome, action) in enumerate(cases, start=1):
            self.append(
                reuse_receipt(
                    self.note,
                    run_suffix=str(index),
                    outcome=outcome,
                    action=action,
                )
            )
        snapshot = self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        self.assertEqual(
            ["HELPFUL", "NOT_HELPFUL", "HARMFUL", "UNKNOWN"],
            [event.receipt.outcome for event in snapshot.events],
        )

    def test_causal_evidence_is_retained_for_causal_outcomes(self) -> None:
        for index, outcome in enumerate(("HELPFUL", "HARMFUL"), start=1):
            action = "KEEP" if outcome == "HELPFUL" else "STOP"
            self.append(
                reuse_receipt(
                    self.note,
                    run_suffix=str(index),
                    outcome=outcome,
                    action=action,
                )
            )
        receipts = [
            event.receipt
            for event in self.ledger.read_events(note_bytes=NOTE_BYTES)
        ]
        self.assertTrue(all(item.causal_evidence_ref for item in receipts))
        self.assertTrue(all(item.causal_evidence_sha256 for item in receipts))
        self.assertTrue(all(item.outcome_scope for item in receipts))

    def test_material_and_unknown_human_intervention_are_retained(self) -> None:
        for index, intervention in enumerate(("MATERIAL", "UNKNOWN"), start=1):
            self.append(
                reuse_receipt(
                    self.note,
                    run_suffix=str(index),
                    outcome="UNKNOWN",
                    intervention=intervention,
                )
            )
        snapshot = self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        self.assertEqual(
            ["MATERIAL", "UNKNOWN"],
            [event.receipt.human_intervention for event in snapshot.events],
        )

    def test_hold_and_bounded_stop_are_retained(self) -> None:
        self.append(reuse_receipt(self.note, run_suffix="1"))
        self.append(
            reuse_receipt(
                self.note,
                run_suffix="2",
                outcome="HARMFUL",
                action="STOP",
            )
        )
        events = self.ledger.read_events(note_bytes=NOTE_BYTES)
        self.assertEqual("HOLD", events[0].receipt.next_action)
        self.assertTrue(events[0].receipt.reevaluation_condition)
        self.assertEqual("STOP", events[1].receipt.next_action)
        self.assertEqual("Bounded task family 2.", events[1].receipt.stop_scope)

    def test_revise_preserves_forward_predecessor_and_successor(self) -> None:
        receipt = reuse_receipt(
            self.note,
            outcome="NOT_HELPFUL",
            action="REVISE",
        )
        self.append(receipt)
        stored = self.ledger.read_events(note_bytes=NOTE_BYTES)[0].receipt
        self.assertEqual(self.note, stored.revision.predecessor)
        self.assertNotEqual(self.note, stored.revision.successor)
        self.assertEqual(stored.reusing_run_id, stored.revision.successor.origin_run_id)

    def test_rule_trace_and_output_artifact_evidence_are_retained(self) -> None:
        for index, evidence_class in enumerate(
            ("RULE_TRACE", "OUTPUT_ARTIFACT"),
            start=1,
        ):
            self.append(
                reuse_receipt(
                    self.note,
                    run_suffix=str(index),
                    evidence_class=evidence_class,
                )
            )
        events = self.ledger.read_events(note_bytes=NOTE_BYTES)
        self.assertEqual(
            ["RULE_TRACE", "OUTPUT_ARTIFACT"],
            [event.receipt.use_evidence.evidence_class for event in events],
        )

    def test_existing_note_bytes_are_not_modified(self) -> None:
        before = bytes(NOTE_BYTES)
        self.append(reuse_receipt(self.note))
        self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        self.assertEqual(before, NOTE_BYTES)
        self.assertEqual(self.note.note_sha256, digest_bytes(NOTE_BYTES))


class FieldNotesMaturityLedgerIntegrityTests(LedgerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.append(reuse_receipt(self.note))

    def test_event_payload_tampering_is_detected(self) -> None:
        events = self.parsed_lines()
        events[0]["receipt"]["outcome"] = "HARMFUL"
        self.rewrite_lines(events)
        with self.assertRaises(FieldNoteMaturityLedgerIntegrityError):
            self.ledger.reconstruct(note_bytes=NOTE_BYTES)

    def test_exact_note_identity_tampering_is_detected(self) -> None:
        events = self.parsed_lines()
        events[0]["receipt"]["note"]["field_note_id"] = "fn_tampered"
        self.rewrite_lines(events)
        with self.assertRaises(FieldNoteMaturityLedgerIntegrityError):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_event_identity_tampering_is_detected_even_if_rehashed(self) -> None:
        events = self.parsed_lines()
        events[0]["event_id"] = digest("forged-event-id")
        self.rehash_event(events[0])
        self.rewrite_lines(events)
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "identity mismatch",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_truncated_record_fails_closed(self) -> None:
        raw = self.ledger.events_path.read_bytes()
        self.ledger.events_path.write_bytes(raw[:-1])
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "truncated",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_whole_trailing_record_removal_fails_closed(self) -> None:
        self.append(reuse_receipt(self.note, run_suffix="2"))
        events = self.parsed_lines()
        self.rewrite_lines(events[:1])
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "head",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_missing_head_anchor_fails_closed(self) -> None:
        self.ledger.head_path.unlink()
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "anchor is missing",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_head_anchor_tampering_fails_closed(self) -> None:
        head = json.loads(self.ledger.head_path.read_text())
        head["event_count"] = 2
        self.ledger.head_path.write_text(canonical_json(head))
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "anchor is invalid",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_empty_existing_partition_fails_closed(self) -> None:
        self.ledger.events_path.write_bytes(b"")
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "truncated",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_boolean_sequence_fails_closed_even_if_rehashed(self) -> None:
        events = self.parsed_lines()
        events[0]["sequence"] = False
        self.rehash_event(events[0])
        self.rewrite_lines(events)
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "sequence",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_invalid_recorded_at_fails_closed_even_if_rehashed(self) -> None:
        events = self.parsed_lines()
        events[0]["recorded_at"] = "not-a-timestamp"
        self.rehash_event(events[0])
        self.rewrite_lines(events)
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "recorded_at",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_malformed_record_fails_closed(self) -> None:
        self.ledger.events_path.write_bytes(b"{not-json}\n")
        with self.assertRaises(FieldNoteMaturityLedgerIntegrityError):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_unsupported_event_version_fails_closed(self) -> None:
        events = self.parsed_lines()
        events[0]["schema"] = "decision-os.unsupported.v9"
        self.rehash_event(events[0])
        self.rewrite_lines(events)
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "Unsupported",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_cross_note_contamination_fails_closed(self) -> None:
        other_bytes = NOTE_BYTES.replace(b"Current", b"Topmost")
        other_note = note_identity(
            field_note_id="fn_a4_other",
            note_bytes=other_bytes,
            note_path=(
                ".decision-os/field-notes/"
                "2026-08-03-a4-other-bbbbbbbbbb.md"
            ),
        )
        other_ledger = FieldNoteMaturityLedger(self.root, other_note)
        self.append(
            reuse_receipt(other_note, note_bytes=other_bytes),
            ledger=other_ledger,
            note_bytes=other_bytes,
        )
        self.ledger.events_path.write_bytes(other_ledger.events_path.read_bytes())
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerIntegrityError,
            "identity chain",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_reordered_records_fail_closed(self) -> None:
        self.append(reuse_receipt(self.note, run_suffix="2"))
        events = self.parsed_lines()
        self.rewrite_lines(list(reversed(events)))
        with self.assertRaises(FieldNoteMaturityLedgerIntegrityError):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_duplicate_event_replay_fails_closed(self) -> None:
        events = self.parsed_lines()
        self.rewrite_lines([events[0], events[0]])
        with self.assertRaises(FieldNoteMaturityLedgerIntegrityError):
            self.ledger.read_events(note_bytes=NOTE_BYTES)

    def test_changed_current_note_bytes_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            FieldNoteMaturityLedgerValidationError,
            "Current Note bytes",
        ):
            self.ledger.read_events(note_bytes=NOTE_BYTES + b"changed")


class FieldNotesMaturityLedgerReconstructionTests(LedgerTestCase):
    def test_empty_ledger_reconstructs_candidate_deterministically(self) -> None:
        first = self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        second = self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        self.assertEqual(first, second)
        self.assertEqual("CANDIDATE", first.evidence_maturity.state)
        self.assertEqual(GENESIS_EVENT_SHA256, first.chain_head_sha256)

    def test_same_ledger_reconstructs_identically(self) -> None:
        self.append(reuse_receipt(self.note, run_suffix="1"))
        self.append(reuse_receipt(self.note, run_suffix="2"))
        first = self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        second = self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        self.assertEqual(first.as_dict(), second.as_dict())

    def test_automatic_maturity_is_capped_at_reused(self) -> None:
        for index in range(1, 6):
            self.append(reuse_receipt(self.note, run_suffix=str(index)))
        snapshot = self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        self.assertEqual("REUSED", snapshot.evidence_maturity.state)
        self.assertEqual(5, len(snapshot.evidence_maturity.reuse_event_ids))
        self.assertEqual("UNSET", snapshot.evidence_maturity.promotion.policy_status)
        self.assertIsNone(snapshot.evidence_maturity.promotion.threshold)

    def test_reused_does_not_derive_serving_or_injection(self) -> None:
        self.append(reuse_receipt(self.note))
        snapshot = self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        policy = snapshot.current_serving_policy
        self.assertEqual("REUSED", snapshot.evidence_maturity.state)
        self.assertEqual("DELAY", policy.derivation)
        self.assertFalse(policy.automatic_derivation_supported)
        self.assertIsNone(policy.automatic_injection)
        self.assertFalse(policy.complete_state_machine_implemented)

    def test_canonical_authority_remains_above_advisory_note(self) -> None:
        snapshot = self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        self.assertEqual(
            ("TOPMOST_CANONICAL", "ADVISORY_FIELD_NOTE"),
            snapshot.current_serving_policy.authority_precedence,
        )

    def test_reconstruction_is_read_only(self) -> None:
        self.append(reuse_receipt(self.note))
        before = self.ledger.events_path.read_bytes()
        self.ledger.reconstruct(note_bytes=NOTE_BYTES)
        self.assertEqual(before, self.ledger.events_path.read_bytes())


class FieldNotesMaturityLedgerProtectedArtifactTests(unittest.TestCase):
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
                self.assertEqual(sha256, digest_bytes(data))


if __name__ == "__main__":
    unittest.main()
