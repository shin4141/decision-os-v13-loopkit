from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from decision_os.acceleration.codex_adapter import CodexRuntimeIdentity
from decision_os.companion import field_notes_creator_live as creator_live
from decision_os.companion import field_notes_whole_flow as whole_flow
from decision_os.companion.field_notes_creator_live import (
    FieldNoteCreatorLiveA1CaptureCommitReceipt,
    FieldNoteCreatorLiveProofRuntime,
    FieldNoteCreatorLiveStageError,
)
from decision_os.companion.field_notes_maturity_commit import (
    FieldNoteMaturityCommitRequest,
    FieldNoteMaturityCommitResult,
    commit_field_note_maturity,
)
from decision_os.companion.field_notes_maturity_ledger import (
    FieldNoteMaturityLedger,
    FieldNoteMaturityLedgerSnapshot,
)
from decision_os.companion.field_notes_maturity_review import (
    FieldNoteMaturityReviewPacket,
    review_field_note_maturity,
)
from decision_os.companion.field_notes_model import compile_draft
from decision_os.companion.field_notes_reconnect import FieldNoteReconnectReceipt
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
from decision_os.companion.field_notes_whole_flow import (
    FieldNoteSourceRepositoryIdentity,
    FieldNoteWholeFlowAttempt,
    FieldNoteWholeFlowEvidenceBundle,
    FieldNoteWholeFlowRunIdentity,
    FieldNoteWholeFlowValidationError,
    build_portable_candidate_warehouse_manifest,
    verify_field_note_whole_flow,
)


RUN_1_STARTED = "2026-08-05T10:00:00Z"
A1_CREATED = "2026-08-05T10:01:00Z"
A1_CHECKPOINT = "2026-08-05T10:02:00Z"
RUN_2_STARTED = "2026-08-05T11:00:00Z"
A2_CHECKPOINT = "2026-08-05T11:05:00Z"
USE_AS_OF = "2026-08-05T11:10:00Z"
OUTCOME_AS_OF = "2026-08-05T11:20:00Z"
A3_CHECKPOINT = "2026-08-05T11:21:00Z"
RECORDED_AT = "2026-08-05T11:30:00Z"
A4_CHECKPOINT = "2026-08-05T11:31:00Z"
A5_CHECKPOINT = "2026-08-05T11:32:00Z"
REVIEW_AS_OF = "2026-08-05T11:40:00Z"
A6_CHECKPOINT = "2026-08-05T11:41:00Z"
PROOF_AS_OF = "2026-08-05T12:00:00Z"
RUN_1_ID = "run_a3_a7_production_order_capture"
RUN_2_ID = "run_a3_a7_production_order_reuse"
TASK = "Capture one exact bounded Note for A3-to-A7 qualification."
STRUCTURE_TEXT = "Preserve exact typed lineage before any durable continuation."


def digest(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def note_proposal() -> dict[str, object]:
    return {
        "title": "A3 to A7 Production Order Vertical",
        "value_level": 1,
        "source_model_class": "UNKNOWN",
        "target_model_class": "UNKNOWN",
        "trigger_terms": ["production order", "typed lineage"],
        "scope": {
            "task_family": "a3-a7-production-order-qualification",
            "path_prefixes": ["decision_os/companion"],
            "exclude_terms": ["repair", "retry"],
        },
        "body": {
            "trigger": "A downstream qualification needs creation-order proof.",
            "reusable_structure": STRUCTURE_TEXT,
            "scope": "One exact Note and one later bounded reuse Run.",
            "do_not_apply_when": "Any checkpoint or receipt was replaced.",
            "procedure": "Create, checkpoint, commit, review, then verify.",
            "acceptance": "Every generated value binds one immutable lineage.",
            "evidence": "Production API results and durable read-back.",
            "remaining_unknowns": "Live/model execution remains out of scope.",
        },
    }


class ProductionOrderHarness:
    """Advance one creator-live attempt without prebuilding A3 through A6."""

    def __init__(self, root: Path, label: str) -> None:
        self.root = root / label
        self.attempt = FieldNoteWholeFlowAttempt(
            proof_attempt_id=f"proof_{label}",
            proof_mode="CREATOR_LIVE",
            creator_id="Shin",
            proof_as_of=PROOF_AS_OF,
        )
        self.repository = FieldNoteSourceRepositoryIdentity(
            repository_id=f"repo:v1:{'a' * 64}",
            source_commit="b" * 40,
        )
        self.runtime_identity = CodexRuntimeIdentity(
            model="gpt-5.6-codex",
            reasoning_effort="high",
            service_tier="priority",
            codex_cli_version="0.120.0",
            account_type="chatgpt",
        )
        self.run_1 = FieldNoteWholeFlowRunIdentity(
            proof_attempt_id=self.attempt.proof_attempt_id,
            run_id=RUN_1_ID,
            started_at=RUN_1_STARTED,
            repository=self.repository,
            runtime=self.runtime_identity,
        )
        self.run_2 = FieldNoteWholeFlowRunIdentity(
            proof_attempt_id=self.attempt.proof_attempt_id,
            run_id=RUN_2_ID,
            started_at=RUN_2_STARTED,
            repository=self.repository,
            runtime=self.runtime_identity,
        )
        self.draft = compile_draft(
            note_proposal(),
            source_run_id=RUN_1_ID,
            created_at=A1_CREATED,
            field_note_id="fn_a3_a7_production_order_vertical",
        )
        self.note = FieldNoteIdentity(
            note_path=self.draft.relative_path,
            field_note_id=self.draft.field_note_id,
            note_sha256=self.draft.sha256,
            origin_run_id=self.draft.source_run_id,
        )
        self.note_bytes = self.draft.markdown
        self.note_bytes_at_creation = bytes(self.note_bytes)
        self.a2_receipt = FieldNoteReconnectReceipt(
            run_id=RUN_2_ID,
            state="ACTIVATION_UNKNOWN",
            failure_reason=None,
            metadata_entries_seen=1,
            metadata_candidate_files_seen=1,
            metadata_files_valid=1,
            metadata_bytes_read=640,
            selected_field_note_path=self.note.note_path,
            selected_field_note_id=self.note.field_note_id,
            selected_metadata_sha256=digest("fixed typed A2 prerequisite"),
            selected_full_note_sha256=self.note.note_sha256,
            full_note_bytes_read=len(self.note_bytes),
            full_notes_injected=1,
            ordinary_distinct_paths_consumed=1,
        )
        self.runtime = FieldNoteCreatorLiveProofRuntime.open_attempt(
            self.root / "creator-live",
            attempt=self.attempt,
            source_repository=self.repository,
            run_1=self.run_1,
        )
        self._record_prerequisites()
        self.ledger_root = self.root / "maturity-ledger-v0.1"
        self.ledger: FieldNoteMaturityLedger | None = None
        self.reuse_claim: FieldNoteReuseClaim | None = None
        self.a3_receipt: FieldNoteReuseReceipt | None = None
        self.a4_snapshot: FieldNoteMaturityLedgerSnapshot | None = None
        self.a5_result: FieldNoteMaturityCommitResult | None = None
        self.a6_packet: FieldNoteMaturityReviewPacket | None = None

    def _record_prerequisites(self) -> None:
        opened = self.runtime.read_back()
        capture_commit = FieldNoteCreatorLiveA1CaptureCommitReceipt._issue(
            authority=creator_live._A1_CAPTURE_COMMIT_AUTHORITY,
            proof_attempt_id=self.attempt.proof_attempt_id,
            run_id=self.run_1.run_id,
            task_sha256=digest(TASK),
            actual_runtime_identity=self.runtime_identity,
            source_repository=self.repository,
            note=self.note,
            note_byte_count=len(self.note_bytes),
            draft_evidence_sha256=whole_flow._a1_evidence_sha256(self.draft),
            draft_created_at=self.draft.created_at,
            save_as_of=self.draft.created_at,
        )
        self.runtime.record_a1_capture(
            self.draft,
            capture_commit=capture_commit,
            expected_task_sha256=digest(TASK),
            actual_runtime_identity=opened.runtime,
            observed_at=A1_CHECKPOINT,
        )
        self.runtime.open_run_2(self.run_2)
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value=A2_CHECKPOINT,
        ):
            self.runtime.record_a2_reconnect(
                self.a2_receipt,
                note=self.note,
                note_bytes=self.note_bytes,
            )

    def build_claim(
        self,
        *,
        note: FieldNoteIdentity | None = None,
        note_bytes: bytes | None = None,
        outcome_as_of: str = OUTCOME_AS_OF,
        evidence_sha256: str | None = None,
    ) -> FieldNoteReuseClaim:
        exact_note = note or self.note
        exact_bytes = note_bytes or self.note_bytes
        structure = STRUCTURE_TEXT.encode("utf-8")
        start = exact_bytes.index(structure)
        binding = bind_field_note_structure(
            exact_note,
            exact_bytes,
            structure_id="preserve-exact-typed-lineage",
            start_byte=start,
            end_byte=start + len(structure),
        )
        use_evidence = FieldNoteUseEvidence(
            evidence_class="RULE_TRACE",
            evidence_origin="IMMEDIATE_COMPLETION_RECORD",
            reusing_run_id=RUN_2_ID,
            structure_binding=binding,
            evidence_ref="run:production-order/evidence:typed-lineage",
            evidence_sha256=(
                evidence_sha256 or digest("production-order use evidence")
            ),
            observer_id="production_order_use_observer",
            observer_relation="INDEPENDENT",
            as_of=USE_AS_OF,
        )
        evaluation = FieldNoteOutcomeEvaluation(
            outcome="HELPFUL",
            scope="The exact bounded A3-to-A7 production-order task.",
            observer_id="production_order_outcome_observer",
            observer_relation="INDEPENDENT",
            as_of=outcome_as_of,
            causal_evidence_ref="run:production-order/causal:typed-lineage",
            causal_evidence_sha256=digest("production-order causal evidence"),
            contribution_separated=True,
        )
        return FieldNoteReuseClaim(
            claimed_note=exact_note,
            reusing_run_id=RUN_2_ID,
            use_evidence=use_evidence,
            outcome_evaluation=evaluation,
            human_intervention="NONE",
            disposition=FieldNoteReuseDisposition(action="KEEP"),
        )

    def produce_a3(
        self,
        *,
        claim: FieldNoteReuseClaim | None = None,
        record_checkpoint: bool = True,
    ) -> FieldNoteReuseReceipt:
        self.reuse_claim = claim or self.build_claim()
        self.a3_receipt = assess_field_note_reuse(
            self.note,
            self.reuse_claim,
            note_bytes=self.note_bytes,
        )
        if record_checkpoint:
            with patch.object(
                creator_live,
                "_utc_now_rfc3339",
                return_value=A3_CHECKPOINT,
            ):
                self.runtime.record_a3_reuse(
                    self.a3_receipt,
                    note=self.note,
                    note_bytes=self.note_bytes,
                )
        return self.a3_receipt

    def commit_a4_a5(
        self,
        *,
        claim: FieldNoteReuseClaim | None = None,
        delivery_context: FieldNoteReconnectReceipt | None = None,
        recorded_at: str = RECORDED_AT,
    ) -> FieldNoteMaturityCommitResult:
        selected_claim = claim or self.reuse_claim or self.build_claim()
        self.ledger = FieldNoteMaturityLedger(self.ledger_root, self.note)
        request = FieldNoteMaturityCommitRequest(
            note=self.note,
            note_bytes=self.note_bytes,
            reuse_claim=selected_claim,
            recorded_at=recorded_at,
            delivery_context=delivery_context or self.a2_receipt,
        )
        self.a5_result = commit_field_note_maturity(self.ledger, request)
        self.a4_snapshot = self.a5_result.durable_snapshot
        return self.a5_result

    def record_a4(self) -> None:
        assert self.a4_snapshot is not None
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value=A4_CHECKPOINT,
        ):
            self.runtime.record_a4_durability(self.a4_snapshot)

    def record_a5(self, result: FieldNoteMaturityCommitResult | None = None) -> None:
        selected = result or self.a5_result
        assert selected is not None
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value=A5_CHECKPOINT,
        ):
            self.runtime.record_a5_confirmation(selected)

    def produce_a6(
        self,
        *,
        review_as_of: str = REVIEW_AS_OF,
    ) -> FieldNoteMaturityReviewPacket:
        assert self.ledger is not None
        self.a6_packet = review_field_note_maturity(
            self.ledger,
            self.note,
            note_bytes=self.note_bytes,
            review_as_of=review_as_of,
        )
        return self.a6_packet

    def record_a6(self, packet: FieldNoteMaturityReviewPacket | None = None) -> None:
        selected = packet or self.a6_packet
        assert selected is not None
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value=A6_CHECKPOINT,
        ):
            self.runtime.record_a6_review(selected)

    def advance_through_a4(self) -> None:
        self.produce_a3()
        self.commit_a4_a5()
        self.record_a4()

    def advance_through_a5(self) -> None:
        self.advance_through_a4()
        self.record_a5()

    def complete(self) -> None:
        self.advance_through_a5()
        self.produce_a6()
        self.record_a6()

    def bundle(self) -> FieldNoteWholeFlowEvidenceBundle:
        readback = self.runtime.read_back()
        return FieldNoteWholeFlowEvidenceBundle(
            attempt=self.attempt,
            source_repository=self.repository,
            run_1=self.run_1,
            run_2=self.run_2,
            note=self.note,
            note_bytes=self.note_bytes,
            a1_capture=self.draft,
            a2_reconnect=self.a2_receipt,
            a3_assessment=self.a3_receipt,
            a4_snapshot=self.a4_snapshot,
            a5_commit=self.a5_result,
            a6_review=self.a6_packet,
            proof_trace=readback.events,
            creator_live_readback=readback,
        )


class A3ToA7ProductionOrderVerticalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_production_order_reaches_pass_receipt_and_manifest(self) -> None:
        harness = ProductionOrderHarness(self.root, "pass")
        self.assertEqual(harness.note_bytes_at_creation, harness.note_bytes)
        self.assertEqual(digest(harness.note_bytes), harness.note.note_sha256)
        self.assertFalse(harness.ledger_root.exists())
        self.assertEqual("A3_REUSE", harness.runtime.read_back().current_stage)

        a3 = harness.produce_a3()
        self.assertEqual("REUSED", a3.state)
        self.assertEqual(3, harness.runtime.read_back().trace_event_count)
        self.assertEqual("A4_DURABILITY", harness.runtime.read_back().current_stage)
        self.assertFalse(harness.ledger_root.exists())

        a5 = harness.commit_a4_a5()
        self.assertEqual(a3, a5.assessment)
        self.assertEqual("RECORDED", a5.status)
        self.assertTrue(a5.durable_commit_confirmed)
        self.assertIsNotNone(a5.durable_snapshot)
        assert a5.durable_snapshot is not None
        self.assertEqual(
            (a3,),
            tuple(event.receipt for event in a5.durable_snapshot.events),
        )
        self.assertTrue(harness.ledger_root.exists())

        harness.record_a4()
        self.assertEqual("A5_CONFIRMATION", harness.runtime.read_back().current_stage)
        harness.record_a5()
        self.assertEqual("A6_REVIEW", harness.runtime.read_back().current_stage)

        a6 = harness.produce_a6()
        self.assertEqual(
            a5.durable_snapshot.chain_head_sha256,
            a6.ledger_identity.chain_head_sha256,
        )
        harness.record_a6()
        readback = harness.runtime.read_back()
        self.assertEqual("TRACE_COMPLETE", readback.state)
        self.assertTrue(readback.durable_readback_verified)
        self.assertEqual(
            (
                "A1_CAPTURE",
                "A2_RECONNECT",
                "A3_REUSE",
                "A4_DURABILITY",
                "A5_CONFIRMATION",
                "A6_REVIEW",
            ),
            tuple(event.stage for event in readback.events),
        )

        bundle = harness.bundle()
        receipt = verify_field_note_whole_flow(bundle)
        self.assertEqual("PASS", receipt.state)
        self.assertEqual("CREATOR_LIVE", receipt.proof_mode)
        manifest = build_portable_candidate_warehouse_manifest(bundle)
        self.assertEqual(receipt, manifest.proof_receipt)
        self.assertEqual(
            receipt.receipt_sha256,
            manifest.as_dict()["whole_flow_proof_receipt_sha256"],
        )
        self.assertEqual(a3.reuse_event_id, receipt.a3_reuse_event_id)
        self.assertEqual(
            a5.durable_snapshot.events[0].event_sha256,
            receipt.a4_event_sha256,
        )
        self.assertEqual(
            whole_flow._a6_packet_sha256(a6),
            manifest.as_dict()["a6_review_packet_sha256"],
        )
        self.assertEqual(
            readback.trace_chain_head_sha256,
            manifest.as_dict()["proof_trace"]["chain_head_sha256"],
        )
        self.assertEqual(harness.note_bytes_at_creation, bundle.note_bytes)

    def _commit_external_lineage(
        self,
        harness: ProductionOrderHarness,
        *,
        label: str,
        note: FieldNoteIdentity,
        claim: FieldNoteReuseClaim,
    ) -> tuple[FieldNoteMaturityLedger, FieldNoteMaturityCommitResult]:
        ledger = FieldNoteMaturityLedger(
            harness.root / f"{label}-ledger",
            note,
        )
        result = commit_field_note_maturity(
            ledger,
            FieldNoteMaturityCommitRequest(
                note=note,
                note_bytes=harness.note_bytes,
                reuse_claim=claim,
                recorded_at=RECORDED_AT,
                delivery_context=None,
            ),
        )
        return ledger, result

    def test_a3_substitution_or_missing_checkpoint_cannot_reach_a4(self) -> None:
        receipt_substitution = ProductionOrderHarness(
            self.root,
            "a3-receipt-substitution",
        )
        original = receipt_substitution.produce_a3()
        substituted_claim = receipt_substitution.build_claim(
            evidence_sha256="f" * 64,
        )
        substituted = receipt_substitution.commit_a4_a5(
            claim=substituted_claim,
        )
        self.assertNotEqual(original, substituted.assessment)
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            receipt_substitution.record_a4()
        readback = receipt_substitution.runtime.read_back()
        self.assertEqual("A4_DURABILITY", readback.failure_boundary)
        self.assertEqual(
            "A4_EXACT_EVENT_INTEGRITY_INVALID",
            readback.failure_reason,
        )

        identity_substitution = ProductionOrderHarness(
            self.root,
            "a3-identity-substitution",
        )
        identity_substitution.produce_a3()
        other_note = replace(
            identity_substitution.note,
            field_note_id="fn_substituted_before_a4",
        )
        other_claim = identity_substitution.build_claim(note=other_note)
        _, other_result = self._commit_external_lineage(
            identity_substitution,
            label="other-note",
            note=other_note,
            claim=other_claim,
        )
        assert other_result.durable_snapshot is not None
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            identity_substitution.runtime.record_a4_durability(
                other_result.durable_snapshot
            )
        self.assertEqual(
            "A4_EXACT_EVENT_INTEGRITY_INVALID",
            identity_substitution.runtime.read_back().failure_reason,
        )

        missing = ProductionOrderHarness(self.root, "a3-checkpoint-missing")
        missing.commit_a4_a5()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            missing.record_a4()
        missing_readback = missing.runtime.read_back()
        self.assertEqual(
            "CREATOR_LIVE_STAGE_ORDER_INVALID",
            missing_readback.failure_reason,
        )
        self.assertEqual("NONE", missing_readback.repair_action)

    def test_a4_substitution_or_missing_checkpoint_cannot_reach_a5(self) -> None:
        for substitution in ("event", "receipt"):
            with self.subTest(substitution=substitution):
                harness = ProductionOrderHarness(
                    self.root,
                    f"a4-{substitution}-substitution",
                )
                harness.produce_a3()
                harness.commit_a4_a5()
                assert harness.a4_snapshot is not None
                event = harness.a4_snapshot.events[0]
                if substitution == "event":
                    changed_event = replace(
                        event,
                        event_sha256="e" * 64,
                    )
                    changed_head = changed_event.event_sha256
                else:
                    changed_receipt = assess_field_note_reuse(
                        harness.note,
                        harness.build_claim(evidence_sha256="d" * 64),
                        note_bytes=harness.note_bytes,
                    )
                    changed_event = replace(event, receipt=changed_receipt)
                    changed_head = event.event_sha256
                harness.a4_snapshot = replace(
                    harness.a4_snapshot,
                    events=(changed_event,),
                    chain_head_sha256=changed_head,
                )
                with self.assertRaises(FieldNoteCreatorLiveStageError):
                    harness.record_a4()
                self.assertEqual(
                    "A4_EXACT_EVENT_INTEGRITY_INVALID",
                    harness.runtime.read_back().failure_reason,
                )

        missing = ProductionOrderHarness(self.root, "a4-checkpoint-missing")
        missing.produce_a3()
        missing.commit_a4_a5()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            missing.record_a5()
        self.assertEqual(
            "CREATOR_LIVE_STAGE_ORDER_INVALID",
            missing.runtime.read_back().failure_reason,
        )

    def test_a5_lineage_unconfirmed_or_missing_cannot_reach_a6(self) -> None:
        unconfirmed = ProductionOrderHarness(self.root, "a5-unconfirmed")
        unconfirmed.advance_through_a4()
        candidate = assess_field_note_reuse(
            unconfirmed.note,
            None,
            note_bytes=unconfirmed.note_bytes,
        )
        unconfirmed_result = FieldNoteMaturityCommitResult(
            status="NOT_REUSED",
            assessment=candidate,
            delivery_context=None,
            append_result=None,
            durable_snapshot=None,
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            unconfirmed.record_a5(unconfirmed_result)
        self.assertEqual(
            "A5_APPEND_NOT_CONFIRMED",
            unconfirmed.runtime.read_back().failure_reason,
        )

        substituted = ProductionOrderHarness(self.root, "a5-a2-substitution")
        substituted.advance_through_a4()
        alternate_a2 = replace(
            substituted.a2_receipt,
            selected_metadata_sha256="c" * 64,
        )
        alternate_result = substituted.commit_a4_a5(
            delivery_context=alternate_a2,
        )
        self.assertEqual("ALREADY_RECORDED", alternate_result.status)
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            substituted.record_a5(alternate_result)
        self.assertEqual(
            "A5_READ_BACK_LINEAGE_MISMATCH",
            substituted.runtime.read_back().failure_reason,
        )

        missing = ProductionOrderHarness(self.root, "a5-checkpoint-missing")
        missing.advance_through_a4()
        packet = missing.produce_a6()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            missing.record_a6(packet)
        self.assertEqual(
            "CREATOR_LIVE_STAGE_ORDER_INVALID",
            missing.runtime.read_back().failure_reason,
        )

    def test_a6_packet_or_ledger_substitution_is_terminal(self) -> None:
        packet_substitution = ProductionOrderHarness(
            self.root,
            "a6-packet-substitution",
        )
        packet_substitution.advance_through_a5()
        other_note = replace(
            packet_substitution.note,
            field_note_id="fn_substituted_a6_packet",
        )
        other_claim = packet_substitution.build_claim(note=other_note)
        other_ledger, _ = self._commit_external_lineage(
            packet_substitution,
            label="other-packet",
            note=other_note,
            claim=other_claim,
        )
        other_packet = review_field_note_maturity(
            other_ledger,
            other_note,
            note_bytes=packet_substitution.note_bytes,
            review_as_of=REVIEW_AS_OF,
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            packet_substitution.record_a6(other_packet)
        self.assertEqual(
            "A6_EXACT_PACKET_MISMATCH",
            packet_substitution.runtime.read_back().failure_reason,
        )

        ledger_substitution = ProductionOrderHarness(
            self.root,
            "a6-ledger-substitution",
        )
        ledger_substitution.advance_through_a5()
        different_claim = ledger_substitution.build_claim(
            evidence_sha256="b" * 64,
        )
        different_ledger, _ = self._commit_external_lineage(
            ledger_substitution,
            label="different-ledger",
            note=ledger_substitution.note,
            claim=different_claim,
        )
        different_packet = review_field_note_maturity(
            different_ledger,
            ledger_substitution.note,
            note_bytes=ledger_substitution.note_bytes,
            review_as_of=REVIEW_AS_OF,
        )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            ledger_substitution.record_a6(different_packet)
        self.assertEqual(
            "A6_EXACT_PACKET_MISMATCH",
            ledger_substitution.runtime.read_back().failure_reason,
        )

    def test_retry_replacement_and_non_none_repair_are_terminal(self) -> None:
        completed = ProductionOrderHarness(self.root, "completed-stage-retry")
        receipt = completed.produce_a3()
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            completed.runtime.record_a3_reuse(
                receipt,
                note=completed.note,
                note_bytes=completed.note_bytes,
            )
        self.assertEqual(
            "RETRY_REPLACEMENT",
            completed.runtime.read_back().repair_action,
        )

        failed = ProductionOrderHarness(self.root, "failed-stage-replacement")
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            failed.runtime.record_stage_failure(
                "A3_REUSE",
                "A3_OPERATION_FAILED",
            )
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            failed.produce_a3()
        failed_readback = failed.runtime.read_back()
        self.assertEqual("FAILED", failed_readback.state)
        self.assertEqual("A3_OPERATION_FAILED", failed_readback.failure_reason)
        self.assertEqual(2, failed_readback.trace_event_count)

        repair_actions = (
            "NOTE_EDIT",
            "EVIDENCE_MANUFACTURE",
            "RECEIPT_REWRITE",
            "LEDGER_REWRITE",
            "EVENT_ID_CHANGE",
            "TIMESTAMP_CHANGE",
            "EVIDENCE_DELETION",
            "RETRY_REPLACEMENT",
        )
        for repair_action in repair_actions:
            with self.subTest(repair_action=repair_action):
                repaired = ProductionOrderHarness(
                    self.root,
                    f"non-none-repair-{repair_action.lower()}",
                )
                with self.assertRaises(FieldNoteCreatorLiveStageError):
                    repaired.runtime.record_repair(
                        "A3_REUSE",
                        "A3_REPAIR_ATTEMPTED",
                        repair_action=repair_action,  # type: ignore[arg-type]
                    )
                repair_readback = repaired.runtime.read_back()
                self.assertEqual("FAILED", repair_readback.state)
                self.assertEqual(repair_action, repair_readback.repair_action)
                receipt = verify_field_note_whole_flow(repaired.bundle())
                self.assertEqual("FAIL", receipt.state)
                self.assertEqual(
                    "REPAIR_DETECTED",
                    receipt.human_repair_result,
                )

    def test_invalid_as_of_ordering_cannot_produce_pass_or_manifest(self) -> None:
        cases = (
            ("outcome-before-use", "2026-08-05T11:09:00Z", RECORDED_AT),
            ("recorded-before-outcome", OUTCOME_AS_OF, "2026-08-05T11:15:00Z"),
        )
        for label, outcome_as_of, recorded_at in cases:
            with self.subTest(label=label):
                harness = ProductionOrderHarness(self.root, label)
                claim = harness.build_claim(outcome_as_of=outcome_as_of)
                harness.produce_a3(claim=claim)
                harness.commit_a4_a5(recorded_at=recorded_at)
                harness.record_a4()
                harness.record_a5()
                harness.produce_a6()
                harness.record_a6()
                bundle = harness.bundle()
                receipt = verify_field_note_whole_flow(bundle)
                self.assertEqual("FAIL", receipt.state)
                self.assertIn(
                    receipt.failure_reason,
                    {
                        "A3_EVIDENCE_TIME_ORDER_INVALID",
                        "A4_EVENT_TIME_ORDER_INVALID",
                    },
                )
                with self.assertRaises(FieldNoteWholeFlowValidationError):
                    build_portable_candidate_warehouse_manifest(bundle)

    def test_failed_incomplete_substituted_or_mutated_bundle_is_not_portable(
        self,
    ) -> None:
        failed = ProductionOrderHarness(self.root, "failed-bundle")
        with self.assertRaises(FieldNoteCreatorLiveStageError):
            failed.runtime.record_repair(
                "A3_REUSE",
                "A3_REPAIR_REJECTED",
                repair_action="RECEIPT_REWRITE",
            )

        incomplete = ProductionOrderHarness(self.root, "incomplete-bundle")
        incomplete.advance_through_a5()
        incomplete.produce_a6()
        incomplete_receipt = verify_field_note_whole_flow(incomplete.bundle())
        self.assertEqual("NOT_READY", incomplete_receipt.state)
        self.assertEqual(
            "CREATOR_LIVE_TRACE_INCOMPLETE",
            incomplete_receipt.failure_reason,
        )

        completed = ProductionOrderHarness(self.root, "mutated-bundle-source")
        completed.complete()
        valid = completed.bundle()
        substituted_a3 = assess_field_note_reuse(
            completed.note,
            completed.build_claim(evidence_sha256="a" * 64),
            note_bytes=completed.note_bytes,
        )
        bundles = {
            "failed": failed.bundle(),
            "incomplete": incomplete.bundle(),
            "substituted": replace(valid, a3_assessment=substituted_a3),
            "mutated": replace(valid, note_bytes=valid.note_bytes + b"mutated"),
        }
        for label, bundle in bundles.items():
            with self.subTest(label=label):
                receipt = verify_field_note_whole_flow(bundle)
                self.assertNotEqual("PASS", receipt.state)
                with self.assertRaises(FieldNoteWholeFlowValidationError):
                    build_portable_candidate_warehouse_manifest(bundle)


if __name__ == "__main__":
    unittest.main()
