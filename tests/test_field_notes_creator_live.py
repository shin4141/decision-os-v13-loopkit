from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from decision_os.companion import field_notes_creator_live as creator_live
from decision_os.companion import field_notes_whole_flow as whole_flow
from decision_os.companion.field_notes_adapter import (
    FieldNoteA1ProposalDiagnostic,
)
from decision_os.companion.field_notes_creator_live import (
    FieldNoteCreatorLiveA1CaptureCommitReceipt,
    FieldNoteCreatorLiveAttemptExistsError,
    FieldNoteCreatorLiveDurabilityError,
    FieldNoteCreatorLiveProofRuntime,
    FieldNoteCreatorLiveStageError,
    FieldNoteCreatorLiveTraceReadback,
    FieldNoteCreatorLiveValidationError,
)
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    assess_field_note_reuse,
)
from decision_os.companion.field_notes_model import compile_draft
from decision_os.companion.field_notes_whole_flow import (
    FieldNoteCreatorLiveRuntimeProvenance,
    FieldNoteWholeFlowTraceEvent,
    FieldNoteWholeFlowValidationError,
    build_portable_candidate_warehouse_manifest,
    verify_field_note_whole_flow,
)
from tests.test_field_notes_whole_flow import (
    ARTIFACT_SECRET,
    PRIVATE_NOTE_TEXT,
    build_bundle,
    proposal,
    runtime,
    source_repository,
)


OBSERVED_AT = (
    "2026-08-05T10:02:00Z",
    "2026-08-05T11:05:00Z",
    "2026-08-05T11:21:00Z",
    "2026-08-05T11:31:00Z",
    "2026-08-05T11:32:00Z",
    "2026-08-05T11:41:00Z",
)
RUN_1_TASK = "Complete the bounded creator-live Run 1 task."
RUN_1_TASK_SHA256 = hashlib.sha256(RUN_1_TASK.encode("utf-8")).hexdigest()


def proposal_diagnostic(
    **changes,
) -> FieldNoteA1ProposalDiagnostic:
    values = {
        "proposal_call_count": 1,
        "call_identity_sha256": "1" * 64,
        "request_identity_sha256": "2" * 64,
        "arguments_identity_sha256": "3" * 64,
        "request_shape_valid": True,
        "malformed_observed": True,
        "gate_invoked": True,
        "gate_response_code": "proposal_schema_invalid",
        "gate_response_success": False,
        "accepted_proposal_present": False,
        "item_start_observed": True,
        "item_completion_observed": True,
        "item_observed_status": "failed",
        "item_expected_status": "failed",
        "all_proposals_completed": True,
        "request_identity_mismatch": False,
        "response_identity_mismatch": False,
        "inconsistent_replay": False,
        "protocol_identity_failure": False,
        "protocol_failure_phase": None,
        "direct_write_identity": None,
        "final_subcause": "A1_PROPOSAL_SCHEMA_REJECTED",
    }
    values.update(changes)
    return FieldNoteA1ProposalDiagnostic(**values)


class CreatorLiveTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bundle, self.ledger = build_bundle(self.root / "evidence")
        self.live_attempt = whole_flow.FieldNoteCreatorLiveAttempt(
            proof_attempt_id=self.bundle.attempt.proof_attempt_id,
            proof_mode="CREATOR_LIVE",
            creator_id=self.bundle.attempt.creator_id,
            authorization_observed_at="2026-08-05T09:58:00Z",
        )
        terminal_clock = patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value="2026-08-05T12:00:00Z",
        )
        terminal_clock.start()
        self.addCleanup(terminal_clock.stop)

    def open_runtime(
        self,
        label: str = "attempt",
        *,
        bundle=None,
    ) -> FieldNoteCreatorLiveProofRuntime:
        evidence = bundle or self.bundle
        attempt = whole_flow.FieldNoteCreatorLiveAttempt(
            proof_attempt_id=evidence.attempt.proof_attempt_id,
            proof_mode="CREATOR_LIVE",
            creator_id=evidence.attempt.creator_id,
            authorization_observed_at="2026-08-05T09:58:00Z",
        )
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            side_effect=("2026-08-05T09:59:00Z", evidence.run_1.started_at),
        ):
            return FieldNoteCreatorLiveProofRuntime.open_attempt(
                self.root / label,
                attempt=attempt,
                source_repository=evidence.source_repository,
                run_1_id=evidence.run_1.run_id,
                runtime=evidence.run_1.runtime,
            )

    def record_a1(
        self,
        runtime_path: FieldNoteCreatorLiveProofRuntime,
        *,
        observed_at: str = OBSERVED_AT[0],
        bundle=None,
    ) -> None:
        evidence = bundle or self.bundle
        assert evidence.a1_capture is not None
        readback = runtime_path.read_back()
        capture_commit = self.capture_commit(
            runtime_path,
            evidence.a1_capture,
        )
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value=observed_at,
        ):
            runtime_path.record_a1_capture(
                evidence.a1_capture,
                capture_commit=capture_commit,
                expected_task_sha256=RUN_1_TASK_SHA256,
                actual_runtime_identity=readback.runtime,
            )

    @staticmethod
    def capture_commit(
        runtime_path: FieldNoteCreatorLiveProofRuntime,
        draft,
    ) -> FieldNoteCreatorLiveA1CaptureCommitReceipt:
        readback = runtime_path.read_back()
        note = FieldNoteIdentity(
            note_path=draft.relative_path,
            field_note_id=draft.field_note_id,
            note_sha256=draft.sha256,
            origin_run_id=draft.source_run_id,
        )
        return FieldNoteCreatorLiveA1CaptureCommitReceipt._issue(
            authority=creator_live._A1_CAPTURE_COMMIT_AUTHORITY,
            proof_attempt_id=readback.proof_attempt_id,
            run_id=readback.run_1.run_id,
            task_sha256=RUN_1_TASK_SHA256,
            actual_runtime_identity=readback.runtime,
            source_repository=readback.source_repository,
            note=note,
            note_byte_count=len(draft.markdown),
            draft_evidence_sha256=whole_flow._a1_evidence_sha256(draft),
            draft_created_at=draft.created_at,
            save_as_of=draft.created_at,
        )

    @staticmethod
    def reissue_capture_commit(
        commit: FieldNoteCreatorLiveA1CaptureCommitReceipt,
        **changes,
    ) -> FieldNoteCreatorLiveA1CaptureCommitReceipt:
        values = {
            "proof_attempt_id": commit.proof_attempt_id,
            "run_id": commit.run_id,
            "task_sha256": commit.task_sha256,
            "actual_runtime_identity": commit.actual_runtime_identity,
            "source_repository": commit.source_repository,
            "note": commit.note,
            "note_byte_count": commit.note_byte_count,
            "draft_evidence_sha256": commit.draft_evidence_sha256,
            "draft_created_at": commit.draft_created_at,
            "save_as_of": commit.save_as_of,
        }
        values.update(changes)
        return FieldNoteCreatorLiveA1CaptureCommitReceipt._issue(
            authority=creator_live._A1_CAPTURE_COMMIT_AUTHORITY,
            **values,
        )

    def open_run_2(
        self,
        runtime_path: FieldNoteCreatorLiveProofRuntime,
        *,
        bundle=None,
    ) -> None:
        runtime_path.open_run_2((bundle or self.bundle).run_2)

    def ready_for_a2(
        self,
        label: str = "attempt",
        *,
        bundle=None,
    ) -> FieldNoteCreatorLiveProofRuntime:
        runtime_path = self.open_runtime(label, bundle=bundle)
        self.record_a1(runtime_path, bundle=bundle)
        self.open_run_2(runtime_path, bundle=bundle)
        return runtime_path

    def complete_runtime(
        self,
        label: str = "complete",
        *,
        bundle=None,
    ) -> tuple[FieldNoteCreatorLiveProofRuntime, object]:
        evidence = bundle or self.bundle
        runtime_path = self.open_runtime(label, bundle=evidence)
        assert evidence.a1_capture is not None
        assert evidence.a2_reconnect is not None
        assert evidence.a3_assessment is not None
        assert evidence.a4_snapshot is not None
        assert evidence.a5_commit is not None
        assert evidence.a6_review is not None
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            side_effect=(*OBSERVED_AT, "2026-08-05T12:00:00Z"),
        ):
            runtime_path.record_a1_capture(
                evidence.a1_capture,
                capture_commit=self.capture_commit(
                    runtime_path,
                    evidence.a1_capture,
                ),
                expected_task_sha256=RUN_1_TASK_SHA256,
                actual_runtime_identity=runtime_path.read_back().runtime,
            )
            runtime_path.open_run_2(evidence.run_2)
            runtime_path.record_a2_reconnect(
                evidence.a2_reconnect,
                note=evidence.note,
                note_bytes=evidence.note_bytes,
            )
            runtime_path.record_a3_reuse(
                evidence.a3_assessment,
                note=evidence.note,
                note_bytes=evidence.note_bytes,
            )
            runtime_path.record_a4_durability(evidence.a4_snapshot)
            runtime_path.record_a5_confirmation(evidence.a5_commit)
            runtime_path.record_a6_review(evidence.a6_review)
        return runtime_path, evidence

    def live_bundle(self, readback, *, bundle=None):
        evidence = bundle or self.bundle
        return replace(
            evidence,
            attempt=readback.attempt,
            run_1=readback.run_1,
            proof_trace=readback.events,
            creator_live_readback=readback,
        )


class CreatorLiveProvenanceTests(CreatorLiveTestCase):
    def test_fixture_pass_remains_unchanged(self) -> None:
        receipt = verify_field_note_whole_flow(self.bundle)
        self.assertEqual("PASS", receipt.state)
        self.assertEqual("FIXTURE", receipt.proof_mode)
        self.assertIsNone(receipt.creator_live_readback)
        assert self.bundle.a1_capture is not None
        self.assertEqual(
            whole_flow._a1_evidence_sha256(self.bundle.a1_capture),
            receipt.a1_evidence_sha256,
        )
        self.assertIsNone(receipt.a1_draft_sha256)
        self.assertIsNone(receipt.a1_capture_commit_sha256)

    def test_hand_built_trace_cannot_satisfy_creator_live(self) -> None:
        live = replace(
            self.bundle,
            attempt=replace(self.bundle.attempt, proof_mode="CREATOR_LIVE"),
        )
        receipt = verify_field_note_whole_flow(live)
        self.assertEqual("NOT_READY", receipt.state)
        self.assertEqual(
            "CREATOR_LIVE_RUNTIME_EVIDENCE_MISSING",
            receipt.failure_reason,
        )

    def test_runtime_provenance_cannot_be_directly_constructed(self) -> None:
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            FieldNoteCreatorLiveRuntimeProvenance()

    def test_string_cannot_mint_runtime_provenance(self) -> None:
        fixture = self.bundle.proof_trace[0]
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            replace(
                fixture,
                proof_attempt_id=self.live_attempt.proof_attempt_id,
                runtime=self.bundle.run_1.runtime,
                source_repository=self.bundle.source_repository,
                runtime_provenance="COMPANION_RUNTIME",  # type: ignore[arg-type]
            )

    def test_readback_cannot_be_directly_constructed(self) -> None:
        with self.assertRaises(FieldNoteCreatorLiveValidationError):
            FieldNoteCreatorLiveTraceReadback()

    def test_runtime_provenance_states_exact_trust_boundary(self) -> None:
        runtime_path = self.open_runtime()
        provenance = runtime_path.read_back().runtime_provenance
        self.assertEqual(
            "IN_PROCESS_RUNTIME_CAPABILITY_WITH_DURABLE_READ_BACK",
            provenance.trust_boundary,
        )
        self.assertNotIn("signature", provenance.runtime_provenance_id)


class CreatorLiveAttemptStateTests(CreatorLiveTestCase):
    def test_runtime_issued_terminal_cutoff_allows_delayed_run_1(self) -> None:
        authorization_observed_at = "2026-08-05T08:00:00Z"
        attempt_opened_at = "2026-08-05T09:59:00Z"
        run_1_started_at = "2026-08-05T10:00:00Z"
        terminal_proof_as_of = "2026-08-05T10:03:00Z"
        attempt = whole_flow.FieldNoteCreatorLiveAttempt(
            proof_attempt_id=self.bundle.attempt.proof_attempt_id,
            proof_mode="CREATOR_LIVE",
            creator_id=self.bundle.attempt.creator_id,
            authorization_observed_at=authorization_observed_at,
        )
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            side_effect=(attempt_opened_at, run_1_started_at),
        ):
            runtime_path = FieldNoteCreatorLiveProofRuntime.open_attempt(
                self.root / "delayed-run-1",
                attempt=attempt,
                source_repository=self.bundle.source_repository,
                run_1_id=self.bundle.run_1.run_id,
                runtime=self.bundle.run_1.runtime,
            )

        assert self.bundle.a1_capture is not None
        runtime_path.record_a1_capture(
            self.bundle.a1_capture,
            capture_commit=self.capture_commit(
                runtime_path,
                self.bundle.a1_capture,
            ),
            expected_task_sha256=RUN_1_TASK_SHA256,
            actual_runtime_identity=self.bundle.run_1.runtime,
            observed_at=OBSERVED_AT[0],
        )
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value=terminal_proof_as_of,
        ):
            with self.assertRaises(FieldNoteCreatorLiveStageError):
                runtime_path.record_stage_failure(
                    "A2_RECONNECT",
                    "DELAYED_RUN_1_TEST_TERMINAL",
                )

        readback = runtime_path.read_back()
        self.assertEqual(authorization_observed_at, readback.authorization_observed_at)
        self.assertEqual(attempt_opened_at, readback.attempt_opened_at)
        self.assertEqual(run_1_started_at, readback.run_1.started_at)
        self.assertEqual(OBSERVED_AT[0], readback.last_admitted_observation)
        self.assertEqual(terminal_proof_as_of, readback.terminal_proof_as_of)
        self.assertEqual("FAILED", readback.state)
        self.assertLess(
            readback.authorization_observed_at,
            readback.attempt_opened_at,
        )
        self.assertLess(readback.attempt_opened_at, readback.run_1.started_at)
        self.assertLess(readback.run_1.started_at, self.bundle.a1_capture.created_at)
        self.assertLessEqual(
            self.bundle.a1_capture.created_at,
            readback.a1_capture_commit.save_as_of,
        )
        self.assertLessEqual(
            readback.a1_capture_commit.save_as_of,
            readback.last_admitted_observation,
        )
        self.assertLessEqual(
            readback.last_admitted_observation,
            readback.terminal_proof_as_of,
        )

    def test_open_readback_has_no_guessed_terminal_cutoff(self) -> None:
        runtime_path = self.open_runtime("open-time-authorities")
        readback = runtime_path.read_back()
        self.assertEqual(creator_live.CREATOR_LIVE_READBACK_SCHEMA_V2, readback.schema)
        self.assertEqual(
            readback.attempt.authorization_observed_at,
            readback.authorization_observed_at,
        )
        self.assertLessEqual(
            readback.authorization_observed_at,
            readback.attempt_opened_at,
        )
        self.assertLess(readback.attempt_opened_at, readback.run_1.started_at)
        self.assertIsNone(readback.terminal_proof_as_of)
        self.assertIsNone(readback.last_admitted_observation)
        self.assertEqual(
            creator_live.CREATOR_LIVE_JOURNAL_FILENAME_V2,
            runtime_path.journal_path.name,
        )
        self.assertNotIn(
            b'"proof_as_of"',
            runtime_path.journal_path.read_bytes(),
        )

    def test_authorization_after_attempt_opening_is_rejected(self) -> None:
        attempt = whole_flow.FieldNoteCreatorLiveAttempt(
            proof_attempt_id=self.bundle.attempt.proof_attempt_id,
            proof_mode="CREATOR_LIVE",
            creator_id=self.bundle.attempt.creator_id,
            authorization_observed_at="2026-08-05T10:00:00Z",
        )
        root = self.root / "authorization-after-opening"
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            side_effect=("2026-08-05T09:59:00Z", "2026-08-05T10:01:00Z"),
        ):
            with self.assertRaises(FieldNoteCreatorLiveValidationError):
                FieldNoteCreatorLiveProofRuntime.open_attempt(
                    root,
                    attempt=attempt,
                    source_repository=self.bundle.source_repository,
                    run_1_id=self.bundle.run_1.run_id,
                    runtime=self.bundle.run_1.runtime,
                )
        self.assertFalse((root / creator_live.CREATOR_LIVE_JOURNAL_FILENAME_V2).exists())

    def test_attempt_opening_not_before_run_1_is_rejected(self) -> None:
        root = self.root / "opening-after-run"
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            side_effect=("2026-08-05T10:00:00Z", "2026-08-05T10:00:00Z"),
        ):
            with self.assertRaises(FieldNoteCreatorLiveValidationError):
                FieldNoteCreatorLiveProofRuntime.open_attempt(
                    root,
                    attempt=self.live_attempt,
                    source_repository=self.bundle.source_repository,
                    run_1_id=self.bundle.run_1.run_id,
                    runtime=self.bundle.run_1.runtime,
                )
        self.assertFalse((root / creator_live.CREATOR_LIVE_JOURNAL_FILENAME_V2).exists())

    def test_failure_before_first_checkpoint_gets_terminal_cutoff(self) -> None:
        runtime_path = self.open_runtime("failure-before-checkpoint")
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value="2026-08-05T10:00:00Z",
        ):
            with self.assertRaises(FieldNoteCreatorLiveStageError):
                runtime_path.record_stage_failure("A1_CAPTURE", "A1_FAILED")
        readback = runtime_path.read_back()
        self.assertEqual("2026-08-05T10:00:00Z", readback.terminal_proof_as_of)
        self.assertIsNone(readback.last_admitted_observation)
        self.assertLessEqual(
            readback.attempt_opened_at,
            readback.terminal_proof_as_of,
        )

    def test_terminal_cutoff_is_immutable_across_load_and_append(self) -> None:
        runtime_path = self.open_runtime("immutable-terminal")
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure("A1_CAPTURE", "A1_FAILED")
        before = runtime_path.journal_path.read_bytes()
        first = runtime_path.read_back()
        loaded = FieldNoteCreatorLiveProofRuntime.load_attempt(
            runtime_path.journal_path.parent
        )
        second = loaded.read_back()
        self.assertEqual(first.terminal_proof_as_of, second.terminal_proof_as_of)
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            loaded.record_stage_failure("A1_CAPTURE", "OTHER_FAILURE")
        self.assertEqual(before, runtime_path.journal_path.read_bytes())

    def test_terminal_cutoff_byte_change_fails_durable_readback(self) -> None:
        runtime_path = self.open_runtime("changed-terminal-cutoff")
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure("A1_CAPTURE", "A1_FAILED")
        raw = runtime_path.journal_path.read_bytes()
        original = b'"proof_as_of":"2026-08-05T12:00:00Z"'
        changed = b'"proof_as_of":"2026-08-05T12:00:01Z"'
        self.assertIn(original, raw)
        runtime_path.journal_path.write_bytes(raw.replace(original, changed, 1))
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertFalse(readback.durable_readback_verified)
        self.assertIsNone(readback.terminal_proof_as_of)

    def test_draft_alone_cannot_emit_a1_checkpoint(self) -> None:
        runtime_path = self.open_runtime()
        assert self.bundle.a1_capture is not None
        with self.assertRaises(TypeError):
            runtime_path.record_a1_capture(  # type: ignore[call-arg]
                self.bundle.a1_capture
            )
        readback = runtime_path.read_back()
        self.assertEqual("OPEN", readback.state)
        self.assertEqual(0, readback.trace_event_count)

    def test_changed_capture_sha_or_byte_count_fails_terminal(self) -> None:
        assert self.bundle.a1_capture is not None
        for label, note_sha256, byte_delta in (
            ("wrong-sha", "0" * 64, 0),
            ("wrong-count", self.bundle.a1_capture.sha256, 1),
        ):
            with self.subTest(label=label):
                runtime_path = self.open_runtime(label)
                draft = self.bundle.a1_capture
                commit = self.capture_commit(runtime_path, draft)
                changed_note = replace(
                    commit.note,
                    note_sha256=note_sha256,
                )
                changed = FieldNoteCreatorLiveA1CaptureCommitReceipt._issue(
                    authority=creator_live._A1_CAPTURE_COMMIT_AUTHORITY,
                    proof_attempt_id=commit.proof_attempt_id,
                    run_id=commit.run_id,
                    task_sha256=commit.task_sha256,
                    actual_runtime_identity=(
                        commit.actual_runtime_identity
                    ),
                    source_repository=commit.source_repository,
                    note=changed_note,
                    note_byte_count=commit.note_byte_count + byte_delta,
                    draft_evidence_sha256=(
                        commit.draft_evidence_sha256
                    ),
                    draft_created_at=commit.draft_created_at,
                    save_as_of=commit.save_as_of,
                )
                with self.assertRaises(FieldNoteCreatorLiveStageError):
                    runtime_path.record_a1_capture(
                        draft,
                        capture_commit=changed,
                        expected_task_sha256=RUN_1_TASK_SHA256,
                        actual_runtime_identity=(
                            runtime_path.read_back().runtime
                        ),
                    )
                self.assertEqual(
                    "A1_CAPTURE_COMMIT_MISMATCH",
                    runtime_path.read_back().failure_reason,
                )

    def test_changed_task_or_actual_runtime_in_commit_fails_terminal(self) -> None:
        assert self.bundle.a1_capture is not None
        for label, changes in (
            ("task", {"task_sha256": "f" * 64}),
            (
                "runtime",
                {
                    "actual_runtime_identity": replace(
                        self.bundle.run_1.runtime,
                        model="other-model",
                    )
                },
            ),
        ):
            with self.subTest(identity=label):
                runtime_path = self.open_runtime(f"changed-{label}")
                commit = self.capture_commit(
                    runtime_path,
                    self.bundle.a1_capture,
                )
                changed = self.reissue_capture_commit(commit, **changes)
                with self.assertRaises(FieldNoteCreatorLiveStageError):
                    runtime_path.record_a1_capture(
                        self.bundle.a1_capture,
                        capture_commit=changed,
                        expected_task_sha256=RUN_1_TASK_SHA256,
                        actual_runtime_identity=(
                            runtime_path.read_back().runtime
                        ),
                        observed_at=OBSERVED_AT[0],
                    )
                self.assertEqual(
                    "A1_CAPTURE_COMMIT_MISMATCH",
                    runtime_path.read_back().failure_reason,
                )

    def test_draft_before_run_1_is_temporally_rejected(self) -> None:
        runtime_path = self.open_runtime("draft-before-run")
        draft = compile_draft(
            proposal(),
            source_run_id=self.bundle.run_1.run_id,
            created_at="2026-08-05T09:59:00Z",
            field_note_id="fn_a7_whole_flow_fixture_before_run",
        )
        commit = self.capture_commit(runtime_path, draft)
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a1_capture(
                draft,
                capture_commit=commit,
                expected_task_sha256=RUN_1_TASK_SHA256,
                actual_runtime_identity=runtime_path.read_back().runtime,
                observed_at=OBSERVED_AT[0],
            )
        readback = runtime_path.read_back()
        self.assertEqual("A1_CAPTURE_CHRONOLOGY_INVALID", readback.failure_reason)
        self.assertEqual("TIMESTAMP_CHANGE", readback.repair_action)

    def test_save_before_draft_creation_is_rejected_by_typed_receipt(self) -> None:
        assert self.bundle.a1_capture is not None
        runtime_path = self.open_runtime("save-before-draft")
        commit = self.capture_commit(runtime_path, self.bundle.a1_capture)
        with self.assertRaises(FieldNoteCreatorLiveValidationError):
            self.reissue_capture_commit(
                commit,
                save_as_of="2026-08-05T10:00:00Z",
            )
        self.assertEqual(0, runtime_path.read_back().trace_event_count)

    def test_terminal_cutoff_before_a1_observation_is_rejected(self) -> None:
        assert self.bundle.a1_capture is not None
        runtime_path = self.open_runtime("save-after-proof")
        commit = self.reissue_capture_commit(
            self.capture_commit(runtime_path, self.bundle.a1_capture),
            save_as_of="2026-08-05T12:01:00Z",
        )
        runtime_path.record_a1_capture(
            self.bundle.a1_capture,
            capture_commit=commit,
            expected_task_sha256=RUN_1_TASK_SHA256,
            actual_runtime_identity=runtime_path.read_back().runtime,
            observed_at="2026-08-05T12:01:00Z",
        )
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value="2026-08-05T12:00:00Z",
        ):
            with self.assertRaises(FieldNoteCreatorLiveValidationError):
                runtime_path.record_stage_failure(
                    "A2_RECONNECT",
                    "TERMINAL_CUTOFF_TEST",
                )
        self.assertEqual("OPEN", runtime_path.read_back().state)

    def test_checkpoint_observation_before_save_is_temporally_rejected(self) -> None:
        assert self.bundle.a1_capture is not None
        runtime_path = self.open_runtime("observe-before-save")
        commit = self.reissue_capture_commit(
            self.capture_commit(runtime_path, self.bundle.a1_capture),
            save_as_of="2026-08-05T10:03:00Z",
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a1_capture(
                self.bundle.a1_capture,
                capture_commit=commit,
                expected_task_sha256=RUN_1_TASK_SHA256,
                actual_runtime_identity=runtime_path.read_back().runtime,
                observed_at=OBSERVED_AT[0],
            )
        self.assertEqual(
            "A1_CAPTURE_CHRONOLOGY_INVALID",
            runtime_path.read_back().failure_reason,
        )

    def test_capture_commit_identity_is_the_creator_live_trace_identity(self) -> None:
        assert self.bundle.a1_capture is not None
        events = []
        commits = []
        for label, save_as_of in (
            ("first-commit", self.bundle.a1_capture.created_at),
            ("second-commit", "2026-08-05T10:01:30Z"),
        ):
            runtime_path = self.open_runtime(label)
            commit = self.reissue_capture_commit(
                self.capture_commit(runtime_path, self.bundle.a1_capture),
                save_as_of=save_as_of,
            )
            event = runtime_path.record_a1_capture(
                self.bundle.a1_capture,
                capture_commit=commit,
                expected_task_sha256=RUN_1_TASK_SHA256,
                actual_runtime_identity=runtime_path.read_back().runtime,
                observed_at=OBSERVED_AT[0],
            )
            events.append(event)
            commits.append(commit)
            self.assertEqual(commit.receipt_sha256, event.evidence_sha256)
        self.assertNotEqual(commits[0].receipt_sha256, commits[1].receipt_sha256)
        self.assertNotEqual(events[0].trace_sha256, events[1].trace_sha256)

    def test_attempt_opens_with_exact_repository_and_runtime(self) -> None:
        readback = self.open_runtime().read_back()
        self.assertEqual("OPEN", readback.state)
        self.assertEqual(self.live_attempt.proof_attempt_id, readback.proof_attempt_id)
        self.assertEqual(self.bundle.source_repository, readback.source_repository)
        self.assertEqual(self.bundle.run_1.runtime, readback.runtime)
        self.assertEqual(self.bundle.run_1, readback.run_1)
        self.assertIsNone(readback.run_2)
        self.assertEqual("A1_CAPTURE", readback.current_stage)
        self.assertTrue(readback.one_attempt_no_retry)

    def test_run_1_and_run_2_must_be_distinct(self) -> None:
        runtime_path = self.open_runtime()
        self.record_a1(runtime_path)
        same_run = replace(
            self.bundle.run_2,
            run_id=self.bundle.run_1.run_id,
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.open_run_2(same_run)
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertEqual("RETRY_REPLACEMENT", readback.repair_action)

    def test_run_2_cannot_open_before_a1_closure(self) -> None:
        runtime_path = self.open_runtime()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.open_run_2(self.bundle.run_2)
        self.assertEqual("FAILED", runtime_path.read_back().state)

    def test_runtime_identity_cannot_change_between_runs(self) -> None:
        runtime_path = self.open_runtime()
        self.record_a1(runtime_path)
        changed = replace(
            self.bundle.run_2,
            runtime=runtime(model="other-model"),
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.open_run_2(changed)
        self.assertEqual(
            "MODEL_RUNTIME_MISMATCH",
            runtime_path.read_back().failure_reason,
        )

    def test_repository_identity_cannot_change_between_runs(self) -> None:
        runtime_path = self.open_runtime()
        self.record_a1(runtime_path)
        changed = replace(
            self.bundle.run_2,
            repository=source_repository(suffix="c"),
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.open_run_2(changed)
        self.assertEqual(
            "SOURCE_REPOSITORY_MISMATCH",
            runtime_path.read_back().failure_reason,
        )

    def test_cross_attempt_run_2_is_rejected(self) -> None:
        runtime_path = self.open_runtime()
        self.record_a1(runtime_path)
        changed = replace(
            self.bundle.run_2,
            proof_attempt_id="other_attempt",
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.open_run_2(changed)
        self.assertEqual(
            "RUN_ATTEMPT_MISMATCH",
            runtime_path.read_back().failure_reason,
        )

    def test_stage_cannot_be_skipped(self) -> None:
        runtime_path = self.open_runtime()
        assert self.bundle.a3_assessment is not None
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a3_reuse(
                self.bundle.a3_assessment,
                note=self.bundle.note,
                note_bytes=self.bundle.note_bytes,
            )
        self.assertEqual("FAILED", runtime_path.read_back().state)

    def test_stage_cannot_be_reordered(self) -> None:
        runtime_path = self.ready_for_a2()
        assert self.bundle.a3_assessment is not None
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a3_reuse(
                self.bundle.a3_assessment,
                note=self.bundle.note,
                note_bytes=self.bundle.note_bytes,
            )
        self.assertEqual(
            "CREATOR_LIVE_STAGE_ORDER_INVALID",
            runtime_path.read_back().failure_reason,
        )

    def test_stage_cannot_be_emitted_twice(self) -> None:
        runtime_path = self.open_runtime()
        self.record_a1(runtime_path)
        assert self.bundle.a1_capture is not None
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a1_capture(
                self.bundle.a1_capture,
                capture_commit=self.capture_commit(
                    runtime_path,
                    self.bundle.a1_capture,
                ),
                expected_task_sha256=RUN_1_TASK_SHA256,
                actual_runtime_identity=runtime_path.read_back().runtime,
            )
        self.assertEqual("RETRY_REPLACEMENT", runtime_path.read_back().repair_action)

    def test_failed_stage_cannot_later_emit_success(self) -> None:
        runtime_path = self.ready_for_a2()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure(
                "A2_RECONNECT",
                "A2_OPERATION_FAILED",
            )
        assert self.bundle.a2_reconnect is not None
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a2_reconnect(
                self.bundle.a2_reconnect,
                note=self.bundle.note,
                note_bytes=self.bundle.note_bytes,
            )
        self.assertEqual(1, runtime_path.read_back().trace_event_count)

    def test_failed_attempt_cannot_be_reset_to_open(self) -> None:
        runtime_path = self.open_runtime()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure("A1_CAPTURE", "A1_FAILED")
        loaded = FieldNoteCreatorLiveProofRuntime.load_attempt(
            runtime_path.journal_path.parent
        )
        self.assertEqual("FAILED", loaded.read_back().state)
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            self.record_a1(loaded)

    def test_legacy_terminal_record_projects_diagnostic_unavailable(self) -> None:
        runtime_path = self.open_runtime("legacy-failure")
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure(
                "A1_CAPTURE",
                "A1_PROPOSAL_INVALID",
            )
        loaded = FieldNoteCreatorLiveProofRuntime.load_attempt(
            runtime_path.journal_path.parent
        )
        readback = loaded.read_back()
        self.assertTrue(readback.durable_readback_verified)
        self.assertEqual("A1_PROPOSAL_INVALID", readback.failure_reason)
        self.assertIsNone(readback.a1_proposal_diagnostic)

    def test_typed_proposal_failure_cannot_open_run_2(self) -> None:
        runtime_path = self.open_runtime("diagnostic-terminal")
        diagnostic = proposal_diagnostic()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure(
                "A1_CAPTURE",
                diagnostic.final_subcause,
                proposal_diagnostic=diagnostic,
            )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.open_run_2(self.bundle.run_2)
        self.assertEqual(0, runtime_path.read_back().trace_event_count)

    def test_second_attempt_is_not_started_automatically(self) -> None:
        runtime_path = self.open_runtime()
        with self.assertRaises(FieldNoteCreatorLiveAttemptExistsError):
            FieldNoteCreatorLiveProofRuntime.open_attempt(
                runtime_path.journal_path.parent,
                attempt=self.live_attempt,
                source_repository=self.bundle.source_repository,
                run_1_id=self.bundle.run_1.run_id,
                runtime=self.bundle.run_1.runtime,
            )
        self.assertEqual("OPEN", runtime_path.read_back().state)


class CreatorLiveStageAcquisitionTests(CreatorLiveTestCase):
    def test_each_checkpoint_binds_exact_typed_stage_evidence(self) -> None:
        runtime_path, evidence = self.complete_runtime()
        readback = runtime_path.read_back()
        assert evidence.a1_capture is not None
        assert evidence.a2_reconnect is not None
        assert evidence.a3_assessment is not None
        assert evidence.a4_snapshot is not None
        assert evidence.a5_commit is not None
        assert evidence.a6_review is not None
        self.assertEqual(
            (
                readback.a1_capture_commit.receipt_sha256,
                whole_flow._a2_receipt_sha256(evidence.a2_reconnect),
                whole_flow._a3_receipt_sha256(evidence.a3_assessment),
                evidence.a4_snapshot.events[0].event_sha256,
                whole_flow._a5_confirmation_sha256(evidence.a5_commit),
                whole_flow._a6_packet_sha256(evidence.a6_review),
            ),
            tuple(event.evidence_sha256 for event in readback.events),
        )

    def test_cross_run_a2_evidence_is_rejected(self) -> None:
        runtime_path = self.ready_for_a2()
        assert self.bundle.a2_reconnect is not None
        changed = replace(self.bundle.a2_reconnect, run_id="other_run")
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a2_reconnect(
                changed,
                note=self.bundle.note,
                note_bytes=self.bundle.note_bytes,
            )
        self.assertEqual("A2_RUN_MISMATCH", runtime_path.read_back().failure_reason)

    def test_changed_note_bytes_are_rejected(self) -> None:
        runtime_path = self.ready_for_a2()
        assert self.bundle.a2_reconnect is not None
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a2_reconnect(
                self.bundle.a2_reconnect,
                note=self.bundle.note,
                note_bytes=self.bundle.note_bytes + b"changed",
            )
        self.assertEqual("NOTE_EDIT", runtime_path.read_back().repair_action)

    def test_a2_exact_note_mismatch_is_rejected(self) -> None:
        runtime_path = self.ready_for_a2()
        assert self.bundle.a2_reconnect is not None
        changed = replace(
            self.bundle.a2_reconnect,
            selected_field_note_id="other_note",
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a2_reconnect(
                changed,
                note=self.bundle.note,
                note_bytes=self.bundle.note_bytes,
            )
        self.assertEqual(
            "A2_EXACT_NOTE_MISMATCH",
            runtime_path.read_back().failure_reason,
        )

    def test_a3_non_reused_evidence_is_rejected(self) -> None:
        runtime_path = self.ready_for_a2()
        assert self.bundle.a2_reconnect is not None
        assert self.bundle.a3_assessment is not None
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value=OBSERVED_AT[1],
        ):
            runtime_path.record_a2_reconnect(
                self.bundle.a2_reconnect,
                note=self.bundle.note,
                note_bytes=self.bundle.note_bytes,
            )
        candidate = assess_field_note_reuse(
            self.bundle.note,
            None,
            note_bytes=self.bundle.note_bytes,
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a3_reuse(
                candidate,
                note=self.bundle.note,
                note_bytes=self.bundle.note_bytes,
            )
        self.assertEqual(
            "A3_NOT_DEMONSTRABLY_REUSED",
            runtime_path.read_back().failure_reason,
        )

    def runtime_through_a3(self, label: str, *, bundle=None):
        evidence = bundle or self.bundle
        runtime_path = self.ready_for_a2(label, bundle=evidence)
        assert evidence.a2_reconnect is not None
        assert evidence.a3_assessment is not None
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            side_effect=OBSERVED_AT[1:3],
        ):
            runtime_path.record_a2_reconnect(
                evidence.a2_reconnect,
                note=evidence.note,
                note_bytes=evidence.note_bytes,
            )
            runtime_path.record_a3_reuse(
                evidence.a3_assessment,
                note=evidence.note,
                note_bytes=evidence.note_bytes,
            )
        return runtime_path

    def mutated_a4_snapshot(self, bundle, **changes):
        assert bundle.a3_assessment is not None
        assert bundle.a4_snapshot is not None
        receipt = replace(bundle.a3_assessment)
        for field, value in changes.items():
            object.__setattr__(receipt, field, value)
        event = replace(bundle.a4_snapshot.events[0])
        object.__setattr__(event, "receipt", receipt)
        object.__setattr__(
            event,
            "receipt_sha256",
            whole_flow._event_receipt_sha256(event),
        )
        object.__setattr__(event, "event_sha256", whole_flow._event_sha256(event))
        snapshot = replace(bundle.a4_snapshot)
        object.__setattr__(snapshot, "events", (event,))
        object.__setattr__(snapshot, "chain_head_sha256", event.event_sha256)
        return snapshot

    def assert_a3_mutation_stops_at_a4(
        self,
        label: str,
        bundle,
        **changes,
    ) -> None:
        runtime_path = self.runtime_through_a3(label, bundle=bundle)
        changed = self.mutated_a4_snapshot(bundle, **changes)
        assert bundle.a3_assessment is not None
        self.assertEqual(
            bundle.a3_assessment.reuse_event_id,
            changed.events[0].receipt.reuse_event_id,
        )
        self.assertNotEqual(
            whole_flow._a3_receipt_sha256(bundle.a3_assessment),
            changed.events[0].receipt_sha256,
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a4_durability(changed)
        self.assertEqual("FAILED", runtime_path.read_back().state)
        assert bundle.a5_commit is not None
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a5_confirmation(bundle.a5_commit)
        assert bundle.a6_review is not None
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a6_review(bundle.a6_review)

    def test_complete_a3_receipt_axes_cannot_be_substituted(self) -> None:
        mutations = {
            "claimed-outcome": {"claimed_outcome": "HARMFUL"},
            "effective-outcome": {"outcome": "HARMFUL"},
            "outcome-scope": {"outcome_scope": "A changed bounded scope."},
            "causal-evidence": {"causal_evidence_sha256": "f" * 64},
            "outcome-observer": {"outcome_observer_id": "other_observer"},
            "outcome-confirmation": {
                "outcome_confirmation": "SAME_RUN_CLAIM"
            },
            "contribution": {"contribution_separated": False},
            "intervention": {"human_intervention": "MATERIAL"},
            "disposition": {"next_action": "STOP"},
        }
        for label, changes in mutations.items():
            with self.subTest(axis=label):
                self.assert_a3_mutation_stops_at_a4(
                    f"a3-mutation-{label}",
                    self.bundle,
                    **changes,
                )

    def test_stop_scope_substitution_cannot_continue(self) -> None:
        bundle, _ = build_bundle(self.root / "stop-source", outcome="HARMFUL")
        self.assert_a3_mutation_stops_at_a4(
            "stop-scope-mutation",
            bundle,
            stop_scope="A substituted STOP scope.",
        )

    def test_revise_lineage_substitution_cannot_continue(self) -> None:
        bundle, _ = build_bundle(
            self.root / "revise-source",
            outcome="NOT_HELPFUL",
            action="REVISE",
        )
        assert bundle.a3_assessment is not None
        assert bundle.a3_assessment.revision is not None
        successor = replace(
            bundle.a3_assessment.revision.successor,
            field_note_id="fn_a7_substituted_successor",
        )
        revision = replace(
            bundle.a3_assessment.revision,
            successor=successor,
        )
        self.assert_a3_mutation_stops_at_a4(
            "revision-lineage-mutation",
            bundle,
            revision=revision,
        )

    def test_a4_tampered_durability_is_rejected(self) -> None:
        runtime_path = self.runtime_through_a3("a4")
        assert self.bundle.a4_snapshot is not None
        event = replace(
            self.bundle.a4_snapshot.events[0],
            event_sha256="f" * 64,
        )
        changed = replace(
            self.bundle.a4_snapshot,
            events=(event,),
            chain_head_sha256="f" * 64,
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a4_durability(changed)
        self.assertEqual("LEDGER_REWRITE", runtime_path.read_back().repair_action)

    def runtime_through_a4(self, label: str):
        runtime_path = self.runtime_through_a3(label)
        assert self.bundle.a4_snapshot is not None
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value=OBSERVED_AT[3],
        ):
            runtime_path.record_a4_durability(self.bundle.a4_snapshot)
        return runtime_path

    def test_a5_unconfirmed_readback_is_rejected(self) -> None:
        runtime_path = self.runtime_through_a4("a5")
        assert self.bundle.a5_commit is not None
        changed = type(self.bundle.a5_commit)(
            status="NOT_REUSED",
            assessment=assess_field_note_reuse(
                self.bundle.a5_commit.assessment.note,
                None,
            ),
            delivery_context=None,
            append_result=None,
            durable_snapshot=None,
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a5_confirmation(changed)
        self.assertEqual(
            "A5_APPEND_NOT_CONFIRMED",
            runtime_path.read_back().failure_reason,
        )

    def runtime_through_a5(self, label: str):
        runtime_path = self.runtime_through_a4(label)
        assert self.bundle.a5_commit is not None
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value=OBSERVED_AT[4],
        ):
            runtime_path.record_a5_confirmation(self.bundle.a5_commit)
        return runtime_path

    def test_a6_mismatched_packet_is_rejected(self) -> None:
        runtime_path = self.runtime_through_a5("a6")
        assert self.bundle.a6_review is not None
        other = replace(self.bundle.note, field_note_id="other_note")
        changed = replace(self.bundle.a6_review)
        object.__setattr__(changed, "note_identity", other)
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_a6_review(changed)
        self.assertEqual(
            "A6_EXACT_PACKET_MISMATCH",
            runtime_path.read_back().failure_reason,
        )


class CreatorLiveDurabilityTests(CreatorLiveTestCase):
    def test_historical_v0_1_artifacts_remain_byte_exact_and_read_only(self) -> None:
        root = self.root / "historical-v0-1"
        root.mkdir()
        attempt = whole_flow.FieldNoteWholeFlowAttempt(
            proof_attempt_id=self.bundle.attempt.proof_attempt_id,
            proof_mode="CREATOR_LIVE",
            creator_id=self.bundle.attempt.creator_id,
            proof_as_of="2026-08-05T12:00:00Z",
        )
        provenance = whole_flow.FieldNoteCreatorLiveRuntimeProvenance._issue(
            authority=whole_flow._RUNTIME_PROVENANCE_AUTHORITY,
            proof_attempt_id=attempt.proof_attempt_id,
            source_repository=self.bundle.source_repository,
            runtime=self.bundle.run_1.runtime,
            issued_for_run_1_id=self.bundle.run_1.run_id,
        )
        record = creator_live._JournalRecord.create(
            sequence=0,
            kind="ATTEMPT_OPENED",
            payload={
                "journal_schema": creator_live.CREATOR_LIVE_JOURNAL_SCHEMA,
                "attempt": attempt.as_dict(),
                "source_repository": self.bundle.source_repository.as_dict(),
                "runtime": whole_flow._runtime_as_dict(self.bundle.run_1.runtime),
                "run_1": self.bundle.run_1.as_dict(),
                "runtime_provenance": provenance.as_dict(),
                "one_attempt_no_retry": True,
            },
            previous_record_sha256=creator_live.JOURNAL_GENESIS_SHA256,
        )
        journal_raw = record.serialize_line()
        anchor = creator_live._AnchorRecord.create(
            generation=0,
            proof_attempt_id=attempt.proof_attempt_id,
            journal_raw=journal_raw,
            journal_records=(record,),
            previous_anchor_sha256=creator_live.ANCHOR_GENESIS_SHA256,
        )
        anchor_raw = anchor.serialize_line()
        journal_path = root / creator_live.CREATOR_LIVE_JOURNAL_FILENAME
        anchor_path = root / creator_live.CREATOR_LIVE_ANCHOR_FILENAME
        journal_path.write_bytes(journal_raw)
        anchor_path.write_bytes(anchor_raw)

        self.assertEqual(
            "6c154a8df21c4eb25245919e9b672b66d75c893f32b9937191f51881c73d0451",
            hashlib.sha256(journal_raw).hexdigest(),
        )
        self.assertEqual(
            "d4033bee02d008dd269395663c3e13f04e24cb98c5c62413048aec384db82695",
            hashlib.sha256(anchor_raw).hexdigest(),
        )
        runtime_path = FieldNoteCreatorLiveProofRuntime.load_attempt(root)
        readback = runtime_path.read_back()
        self.assertEqual(creator_live.CREATOR_LIVE_READBACK_SCHEMA, readback.schema)
        self.assertEqual(
            "e04be488d568651afb7d89f7cc19ec0f5cc558a13460fc1d1e84d2fe9dc5450a",
            readback.readback_sha256,
        )
        self.assertEqual(attempt, readback.attempt)
        self.assertFalse(hasattr(readback, "terminal_proof_as_of"))
        receipt = verify_field_note_whole_flow(
            replace(
                self.bundle,
                attempt=attempt,
                creator_live_readback=readback,
                proof_trace=(),
            )
        )
        self.assertEqual("NOT_READY", receipt.state)
        self.assertEqual(whole_flow.WHOLE_FLOW_SCHEMA, receipt.schema)
        self.assertEqual(attempt.proof_as_of, receipt.proof_as_of)
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure("A1_CAPTURE", "A1_FAILED")
        self.assertEqual(journal_raw, journal_path.read_bytes())
        self.assertEqual(anchor_raw, anchor_path.read_bytes())

    def runtime_through_a2(
        self,
        label: str,
    ) -> FieldNoteCreatorLiveProofRuntime:
        runtime_path = self.ready_for_a2(label)
        assert self.bundle.a2_reconnect is not None
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value=OBSERVED_AT[1],
        ):
            runtime_path.record_a2_reconnect(
                self.bundle.a2_reconnect,
                note=self.bundle.note,
                note_bytes=self.bundle.note_bytes,
            )
        return runtime_path

    def remove_journal_tail(
        self,
        runtime_path: FieldNoteCreatorLiveProofRuntime,
        count: int = 1,
    ) -> None:
        lines = runtime_path.journal_path.read_bytes().splitlines(keepends=True)
        runtime_path.journal_path.write_bytes(b"".join(lines[:-count]))

    def remove_anchor_tail(
        self,
        runtime_path: FieldNoteCreatorLiveProofRuntime,
        count: int = 1,
    ) -> None:
        lines = runtime_path.anchor_path.read_bytes().splitlines(keepends=True)
        runtime_path.anchor_path.write_bytes(b"".join(lines[:-count]))

    def test_trace_persistence_is_append_only(self) -> None:
        runtime_path = self.open_runtime()
        initial = runtime_path.journal_path.read_bytes()
        initial_anchor = runtime_path.anchor_path.read_bytes()
        self.record_a1(runtime_path)
        after_a1 = runtime_path.journal_path.read_bytes()
        after_a1_anchor = runtime_path.anchor_path.read_bytes()
        self.open_run_2(runtime_path)
        after_run_2 = runtime_path.journal_path.read_bytes()
        after_run_2_anchor = runtime_path.anchor_path.read_bytes()
        self.assertTrue(after_a1.startswith(initial))
        self.assertTrue(after_run_2.startswith(after_a1))
        self.assertTrue(after_a1_anchor.startswith(initial_anchor))
        self.assertTrue(after_run_2_anchor.startswith(after_a1_anchor))

    def test_deleting_last_complete_checkpoint_fails_closed(self) -> None:
        runtime_path = self.runtime_through_a2("drop-checkpoint")
        self.remove_journal_tail(runtime_path)
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertEqual(
            "CREATOR_LIVE_DURABLE_JOURNAL_ANCHOR_MISMATCH",
            readback.failure_reason,
        )

    def test_deleting_complete_failure_record_fails_closed(self) -> None:
        runtime_path = self.open_runtime("drop-failure")
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure("A1_CAPTURE", "A1_FAILED")
        self.remove_journal_tail(runtime_path)
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertFalse(readback.durable_readback_verified)

    def test_proposal_diagnostic_is_journaled_anchor_sealed_and_read_back(self) -> None:
        runtime_path = self.open_runtime("diagnostic-sealed")
        diagnostic = proposal_diagnostic()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure(
                "A1_CAPTURE",
                diagnostic.final_subcause,
                proposal_diagnostic=diagnostic,
            )
        readback = runtime_path.read_back()
        self.assertTrue(readback.durable_readback_verified)
        self.assertEqual(diagnostic, readback.a1_proposal_diagnostic)
        self.assertEqual(
            readback.anchor_record_count,
            readback.journal_record_count - 1,
        )
        journal = runtime_path.journal_path.read_text(encoding="utf-8")
        anchor = runtime_path.anchor_path.read_text(encoding="utf-8")
        self.assertIn(diagnostic.diagnostic_sha256, journal)
        self.assertIn(readback.journal_sha256, anchor)
        self.assertNotIn("reusable_structure", journal)
        self.assertNotIn("proposal Markdown", journal)
        self.assertNotIn("raw model output", journal)

    def test_proposal_diagnostic_record_mutation_fails_closed(self) -> None:
        runtime_path = self.open_runtime("diagnostic-mutation")
        diagnostic = proposal_diagnostic()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure(
                "A1_CAPTURE",
                diagnostic.final_subcause,
                proposal_diagnostic=diagnostic,
            )
        raw = runtime_path.journal_path.read_bytes()
        marker = diagnostic.diagnostic_sha256.encode("ascii")
        offset = raw.index(marker)
        replacement = b"f" if marker[:1] != b"f" else b"e"
        runtime_path.journal_path.write_bytes(
            raw[:offset] + replacement + raw[offset + 1 :]
        )
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertFalse(readback.durable_readback_verified)

    def test_proposal_diagnostic_tail_deletion_fails_closed(self) -> None:
        runtime_path = self.open_runtime("diagnostic-tail")
        diagnostic = proposal_diagnostic()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure(
                "A1_CAPTURE",
                diagnostic.final_subcause,
                proposal_diagnostic=diagnostic,
            )
        self.remove_journal_tail(runtime_path)
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertFalse(readback.durable_readback_verified)

    def test_deleting_complete_trace_completion_fails_closed(self) -> None:
        runtime_path, _ = self.complete_runtime("drop-completion")
        self.remove_journal_tail(runtime_path)
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertEqual("EVIDENCE_DELETION", readback.repair_action)

    def test_deleting_multiple_complete_tail_records_fails_closed(self) -> None:
        runtime_path, _ = self.complete_runtime("drop-multiple")
        self.remove_journal_tail(runtime_path, 3)
        self.assertEqual("FAILED", runtime_path.read_back().state)

    def test_journal_ahead_of_anchor_fails_closed(self) -> None:
        runtime_path = self.runtime_through_a2("journal-ahead")
        self.remove_anchor_tail(runtime_path)
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertEqual(
            "CREATOR_LIVE_DURABLE_JOURNAL_ANCHOR_MISMATCH",
            readback.failure_reason,
        )

    def test_anchor_ahead_of_journal_fails_closed(self) -> None:
        runtime_path = self.runtime_through_a2("anchor-ahead")
        self.remove_journal_tail(runtime_path)
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertFalse(readback.durable_readback_verified)

    def test_anchor_tampering_fails_closed(self) -> None:
        runtime_path = self.runtime_through_a2("anchor-tamper")
        raw = runtime_path.anchor_path.read_bytes()
        marker = b'"journal_sha256":"'
        start = raw.rindex(marker) + len(marker)
        replacement = b"f" if raw[start : start + 1] != b"f" else b"e"
        runtime_path.anchor_path.write_bytes(
            raw[:start] + replacement + raw[start + 1 :]
        )
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertEqual("EVENT_ID_CHANGE", readback.repair_action)

    def test_anchor_truncation_fails_closed(self) -> None:
        runtime_path = self.runtime_through_a2("anchor-truncate")
        raw = runtime_path.anchor_path.read_bytes()
        runtime_path.anchor_path.write_bytes(raw[:-1])
        readback = runtime_path.read_back()
        self.assertEqual(
            "CREATOR_LIVE_DURABLE_ANCHOR_TRUNCATED",
            readback.failure_reason,
        )

    def test_truncated_prefix_cannot_be_appended_to(self) -> None:
        runtime_path = self.runtime_through_a2("blocked-prefix")
        self.remove_journal_tail(runtime_path)
        journal_before = runtime_path.journal_path.read_bytes()
        anchor_before = runtime_path.anchor_path.read_bytes()
        assert self.bundle.a2_reconnect is not None
        with self.assertRaises(FieldNoteCreatorLiveDurabilityError):
            runtime_path.record_a2_reconnect(
                self.bundle.a2_reconnect,
                note=self.bundle.note,
                note_bytes=self.bundle.note_bytes,
            )
        self.assertEqual(journal_before, runtime_path.journal_path.read_bytes())
        self.assertEqual(anchor_before, runtime_path.anchor_path.read_bytes())

    def test_removed_failure_cannot_reopen_attempt(self) -> None:
        runtime_path = self.open_runtime("failure-reopen")
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure("A1_CAPTURE", "A1_FAILED")
        self.remove_journal_tail(runtime_path)
        with self.assertRaises(FieldNoteCreatorLiveDurabilityError):
            self.record_a1(runtime_path)
        self.assertEqual("FAILED", runtime_path.read_back().state)

    def test_removed_completion_cannot_resume_attempt(self) -> None:
        runtime_path, _ = self.complete_runtime("completion-resume")
        self.remove_journal_tail(runtime_path)
        assert self.bundle.a6_review is not None
        with self.assertRaises(FieldNoteCreatorLiveDurabilityError):
            runtime_path.record_a6_review(self.bundle.a6_review)
        self.assertEqual("FAILED", runtime_path.read_back().state)

    def test_durable_exact_readback_reaches_trace_complete(self) -> None:
        runtime_path, _ = self.complete_runtime()
        readback = runtime_path.read_back()
        self.assertEqual("TRACE_COMPLETE", readback.state)
        self.assertTrue(readback.durable_readback_verified)
        self.assertEqual(6, readback.trace_event_count)
        self.assertEqual(
            readback.journal_record_count - 1,
            readback.anchor_record_count,
        )
        self.assertEqual(
            len(runtime_path.journal_path.read_bytes()),
            readback.journal_byte_length,
        )
        self.assertEqual(
            hashlib.sha256(runtime_path.journal_path.read_bytes()).hexdigest(),
            readback.journal_sha256,
        )
        self.assertEqual(
            hashlib.sha256(runtime_path.anchor_path.read_bytes()).hexdigest(),
            readback.anchor_sha256,
        )
        self.assertEqual(
            readback.events[-1].trace_sha256,
            readback.trace_chain_head_sha256,
        )

    def test_trace_completion_cannot_be_extended(self) -> None:
        runtime_path, _ = self.complete_runtime("completion-terminal")
        readback = runtime_path.read_back()
        before = runtime_path.journal_path.read_bytes()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure("A6_REVIEW", "LATE_FAILURE")
        self.assertEqual(before, runtime_path.journal_path.read_bytes())
        loaded = FieldNoteCreatorLiveProofRuntime.load_attempt(
            runtime_path.journal_path.parent
        )
        self.assertEqual(readback, loaded.read_back())

    def test_trace_tampering_fails_closed(self) -> None:
        runtime_path = self.ready_for_a2()
        raw = runtime_path.journal_path.read_bytes()
        marker = b'"evidence_sha256":"'
        start = raw.index(marker) + len(marker)
        replacement = b"f" if raw[start : start + 1] != b"f" else b"e"
        changed = raw[:start] + replacement + raw[start + 1 :]
        runtime_path.journal_path.write_bytes(changed)
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertFalse(readback.durable_readback_verified)

    def test_trace_truncation_fails_closed(self) -> None:
        runtime_path = self.ready_for_a2()
        raw = runtime_path.journal_path.read_bytes()
        runtime_path.journal_path.write_bytes(raw[:-1])
        readback = runtime_path.read_back()
        self.assertEqual(
            "CREATOR_LIVE_DURABLE_TRACE_TRUNCATED",
            readback.failure_reason,
        )
        self.assertEqual("EVIDENCE_DELETION", readback.repair_action)

    def test_trace_duplication_fails_closed(self) -> None:
        runtime_path = self.ready_for_a2()
        raw = runtime_path.journal_path.read_bytes()
        last = raw.splitlines(keepends=True)[-1]
        runtime_path.journal_path.write_bytes(raw + last)
        readback = runtime_path.read_back()
        self.assertEqual(
            "CREATOR_LIVE_DURABLE_TRACE_DUPLICATED",
            readback.failure_reason,
        )
        self.assertEqual("RETRY_REPLACEMENT", readback.repair_action)

    def test_chain_head_mismatch_fails_closed(self) -> None:
        runtime_path = self.ready_for_a2()
        raw = runtime_path.journal_path.read_bytes()
        marker = b'"previous_record_sha256":"'
        first = raw.index(marker) + len(marker)
        second = raw.index(marker, first) + len(marker)
        changed = raw[:second] + b"f" + raw[second + 1:]
        runtime_path.journal_path.write_bytes(changed)
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertFalse(readback.durable_readback_verified)

    def test_in_memory_six_events_without_readback_cannot_pass(self) -> None:
        runtime_path, _ = self.complete_runtime()
        readback = runtime_path.read_back()
        live = replace(
            self.bundle,
            attempt=self.live_attempt,
            proof_trace=readback.events,
            creator_live_readback=None,
        )
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            verify_field_note_whole_flow(live)

    def test_repair_marker_causes_fail(self) -> None:
        runtime_path = self.open_runtime()
        self.record_a1(runtime_path)
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_repair(
                "HUMAN_REPAIR",
                "NOTE_EDIT_AFTER_CAPTURE",
                repair_action="NOTE_EDIT",
            )
        readback = runtime_path.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertEqual("NOTE_EDIT", readback.repair_action)

    def test_retry_replacement_causes_fail(self) -> None:
        runtime_path = self.open_runtime()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_retry_replacement("RUN_REPLACEMENT_ATTEMPTED")
        self.assertEqual("RETRY_REPLACEMENT", runtime_path.read_back().repair_action)

    def test_proof_artifacts_are_deterministic_and_bounded(self) -> None:
        first, _ = self.complete_runtime("first")
        second, _ = self.complete_runtime("second")
        first_bytes = first.journal_path.read_bytes()
        second_bytes = second.journal_path.read_bytes()
        first_anchor_bytes = first.anchor_path.read_bytes()
        second_anchor_bytes = second.anchor_path.read_bytes()
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(first_anchor_bytes, second_anchor_bytes)
        self.assertLess(len(first_bytes), 100_000)
        self.assertLess(len(first_anchor_bytes), 100_000)
        self.assertEqual(first.read_back(), second.read_back())

    def test_trace_storage_excludes_full_note_contents(self) -> None:
        runtime_path, _ = self.complete_runtime()
        text = runtime_path.journal_path.read_text(encoding="utf-8")
        self.assertNotIn(PRIVATE_NOTE_TEXT, text)
        self.assertNotIn(self.bundle.note_bytes.decode("utf-8"), text)

    def test_trace_storage_excludes_output_artifact_contents(self) -> None:
        bundle, _ = build_bundle(
            self.root / "output-evidence",
            evidence_class="OUTPUT_ARTIFACT",
        )
        runtime_path, _ = self.complete_runtime("output", bundle=bundle)
        text = runtime_path.journal_path.read_text(encoding="utf-8")
        self.assertNotIn(ARTIFACT_SECRET, text)


class CreatorLiveA7AdmissionTests(CreatorLiveTestCase):
    def test_open_attempt_cannot_produce_a_receipt(self) -> None:
        runtime_path = self.open_runtime()
        live = self.live_bundle(runtime_path.read_back())
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            verify_field_note_whole_flow(live)
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            build_portable_candidate_warehouse_manifest(live)

    def test_failed_attempt_enters_a7_as_fail(self) -> None:
        runtime_path = self.open_runtime()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            runtime_path.record_stage_failure("A1_CAPTURE", "A1_FAILED")
        live = self.live_bundle(runtime_path.read_back())
        receipt = verify_field_note_whole_flow(live)
        self.assertEqual("FAIL", receipt.state)
        self.assertEqual("A1_FAILED", receipt.failure_reason)
        self.assertEqual(
            runtime_path.read_back().terminal_proof_as_of,
            receipt.proof_as_of,
        )

    def test_trace_complete_creator_live_evidence_can_enter_a7(self) -> None:
        runtime_path, _ = self.complete_runtime()
        live = self.live_bundle(runtime_path.read_back())
        receipt = verify_field_note_whole_flow(live)
        self.assertEqual("PASS", receipt.state)
        self.assertEqual(whole_flow.WHOLE_FLOW_SCHEMA_V2, receipt.schema)
        self.assertEqual(
            runtime_path.read_back().terminal_proof_as_of,
            receipt.proof_as_of,
        )
        self.assertEqual("CREATOR_LIVE", receipt.proof_mode)
        self.assertEqual(live.attempt, runtime_path.read_back().attempt)
        self.assertEqual(live.attempt, receipt.attempt)
        self.assertEqual("TYPED_TRACE_VERIFIED", receipt.human_repair_result)
        commit = runtime_path.read_back().a1_capture_commit
        assert commit is not None
        self.assertEqual(commit.receipt_sha256, receipt.a1_evidence_sha256)
        self.assertEqual(
            commit.receipt_sha256,
            receipt.a1_capture_commit_sha256,
        )
        self.assertEqual(
            commit.draft_evidence_sha256,
            receipt.a1_draft_sha256,
        )

    def test_direct_a7_receipt_cannot_cross_bind_a1_commit_identity(self) -> None:
        runtime_path, _ = self.complete_runtime("direct-a7-commit")
        live = self.live_bundle(runtime_path.read_back())
        receipt = verify_field_note_whole_flow(live)
        self.assertEqual("PASS", receipt.state)
        for field in ("a1_capture_commit_sha256", "a1_draft_sha256"):
            with self.subTest(field=field):
                with self.assertRaises(FieldNoteWholeFlowValidationError):
                    replace(receipt, **{field: "f" * 64})
        self.assertIsNotNone(receipt.creator_live_readback)

    def assert_attempt_substitution_fails(self, **changes) -> None:
        runtime_path, _ = self.complete_runtime(
            "attempt-" + "-".join(sorted(changes))
        )
        readback = runtime_path.read_back()
        live = self.live_bundle(readback)
        changed = replace(live, attempt=replace(live.attempt, **changes))
        receipt = verify_field_note_whole_flow(changed)
        self.assertEqual("FAIL", receipt.state)
        self.assertEqual(
            "CREATOR_LIVE_RUNTIME_IDENTITY_MISMATCH",
            receipt.failure_reason,
        )

    def test_changed_creator_identity_cannot_enter_a7(self) -> None:
        self.assert_attempt_substitution_fails(creator_id="Other Creator")

    def test_caller_cannot_supply_terminal_proof_as_of(self) -> None:
        with self.assertRaises(TypeError):
            replace(
                self.live_attempt,
                proof_as_of="2026-08-05T12:01:00Z",
            )

    def test_changed_attempt_id_cannot_enter_a7(self) -> None:
        self.assert_attempt_substitution_fails(proof_attempt_id="other_attempt")

    def test_changed_proof_mode_cannot_attach_live_readback(self) -> None:
        runtime_path, _ = self.complete_runtime("attempt-mode")
        live = self.live_bundle(runtime_path.read_back())
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            replace(
                live,
                attempt=replace(live.attempt, proof_mode="FIXTURE"),
            )

    def test_creator_live_manifest_is_readback_and_trace_bound(self) -> None:
        runtime_path, _ = self.complete_runtime()
        live = self.live_bundle(runtime_path.read_back())
        manifest = build_portable_candidate_warehouse_manifest(live)
        body = manifest.as_dict()
        self.assertEqual("CREATOR_LIVE", body["coverage_evidence_mode"])
        self.assertTrue(body["creator_live_coverage_verified"])
        self.assertEqual(
            runtime_path.read_back().trace_chain_head_sha256,
            body["proof_trace"]["chain_head_sha256"],
        )

    def test_cross_bound_readback_cannot_admit_other_attempt(self) -> None:
        runtime_path, _ = self.complete_runtime()
        readback = runtime_path.read_back()
        other_attempt = replace(
            self.live_attempt,
            proof_attempt_id="other_attempt",
        )
        other_run_1 = replace(
            self.bundle.run_1,
            proof_attempt_id="other_attempt",
        )
        other_run_2 = replace(
            self.bundle.run_2,
            proof_attempt_id="other_attempt",
        )
        live = replace(
            self.bundle,
            attempt=other_attempt,
            run_1=other_run_1,
            run_2=other_run_2,
            proof_trace=readback.events,
            creator_live_readback=readback,
        )
        receipt = verify_field_note_whole_flow(live)
        self.assertEqual("FAIL", receipt.state)
        self.assertEqual(
            "CREATOR_LIVE_RUNTIME_IDENTITY_MISMATCH",
            receipt.failure_reason,
        )

    def test_unknown_outcome_remains_supported(self) -> None:
        bundle, _ = build_bundle(self.root / "unknown", outcome="UNKNOWN")
        runtime_path, _ = self.complete_runtime("unknown-live", bundle=bundle)
        live = self.live_bundle(runtime_path.read_back(), bundle=bundle)
        receipt = verify_field_note_whole_flow(live)
        self.assertEqual("PASS", receipt.state)
        self.assertEqual("UNKNOWN", receipt.effective_outcome)
        self.assertEqual("HOLD", receipt.next_disposition)

    def test_negative_outcome_remains_supported(self) -> None:
        bundle, _ = build_bundle(self.root / "harmful", outcome="HARMFUL")
        runtime_path, _ = self.complete_runtime("harmful-live", bundle=bundle)
        live = self.live_bundle(runtime_path.read_back(), bundle=bundle)
        receipt = verify_field_note_whole_flow(live)
        self.assertEqual("PASS", receipt.state)
        self.assertEqual("HARMFUL", receipt.effective_outcome)
        self.assertEqual("STOP", receipt.next_disposition)

    def test_promotable_remains_unset(self) -> None:
        runtime_path, _ = self.complete_runtime()
        receipt = verify_field_note_whole_flow(
            self.live_bundle(runtime_path.read_back())
        )
        self.assertEqual("UNSET", receipt.claim_boundary.promotable_policy)

    def test_serving_policy_remains_delayed_and_separate(self) -> None:
        runtime_path, _ = self.complete_runtime()
        live = self.live_bundle(runtime_path.read_back())
        receipt = verify_field_note_whole_flow(live)
        manifest = build_portable_candidate_warehouse_manifest(live)
        self.assertEqual("DELAY", receipt.claim_boundary.serving_policy)
        self.assertEqual("DELAY", manifest.as_dict()["serving_policy"])
        self.assertIsNone(manifest.as_dict()["automatic_injection"])


if __name__ == "__main__":
    unittest.main()
