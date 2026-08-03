from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from decision_os.acceleration.codex_adapter import CodexRuntimeIdentity
from decision_os.companion import field_notes_whole_flow as whole_flow
from decision_os.companion.field_notes_maturity_commit import (
    FieldNoteMaturityCommitRequest,
    commit_field_note_maturity,
)
from decision_os.companion.field_notes_maturity_ledger import (
    GENESIS_EVENT_SHA256,
    FieldNoteMaturityLedger,
)
from decision_os.companion.field_notes_maturity_review import (
    review_field_note_maturity,
)
from decision_os.companion.field_notes_model import canonical_json, compile_draft
from decision_os.companion.field_notes_reconnect import FieldNoteReconnectReceipt
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteOutcomeEvaluation,
    FieldNoteReuseClaim,
    FieldNoteReuseDisposition,
    FieldNoteUseEvidence,
    assess_field_note_reuse,
    bind_field_note_structure,
)
from decision_os.companion.field_notes_whole_flow import (
    FieldNoteSourceRepositoryIdentity,
    FieldNoteWholeFlowAttempt,
    FieldNoteWholeFlowEvidenceBundle,
    FieldNoteWholeFlowProofReceipt,
    FieldNoteWholeFlowRunIdentity,
    FieldNoteWholeFlowTraceEvent,
    FieldNoteWholeFlowValidationError,
    PortableCandidateWarehouseManifest,
    build_portable_candidate_warehouse_manifest,
    verify_field_note_whole_flow,
)


RUN_1_STARTED = "2026-08-05T10:00:00Z"
A1_CREATED = "2026-08-05T10:01:00Z"
RUN_2_STARTED = "2026-08-05T11:00:00Z"
USE_AS_OF = "2026-08-05T11:10:00Z"
OUTCOME_AS_OF = "2026-08-05T11:20:00Z"
RECORDED_AT = "2026-08-05T11:30:00Z"
REVIEW_AS_OF = "2026-08-05T11:40:00Z"
PROOF_AS_OF = "2026-08-05T12:00:00Z"
RUN_1_ID = "run_a7_capture"
RUN_2_ID = "run_a7_reuse"
ATTEMPT_ID = "proof_a7_fixture_001"
PRIVATE_NOTE_TEXT = "Private creator context must never enter the manifest."
ARTIFACT_SECRET = "private output artifact contents"
STRUCTURE_TEXT = "Verify exact state before any restart or irreversible action."


def digest(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def proposal() -> dict:
    return {
        "title": "A7 Whole Flow Proof Fixture",
        "value_level": 1,
        "source_model_class": "UNKNOWN",
        "target_model_class": "UNKNOWN",
        "trigger_terms": ["whole flow", "restart guard"],
        "scope": {
            "task_family": "bounded-whole-flow-proof",
            "path_prefixes": ["decision_os/companion"],
            "exclude_terms": ["live proof"],
        },
        "body": {
            "trigger": "A bounded proof needs exact cross-layer identity.",
            "reusable_structure": STRUCTURE_TEXT,
            "scope": "One creator, repository, model identity, Note, and reuse.",
            "do_not_apply_when": "Any proof evidence was manually repaired.",
            "procedure": "Bind each typed receipt to one immutable lineage.",
            "acceptance": "Every A1 through A6 boundary agrees exactly.",
            "evidence": "Typed receipts, durable read-back, and review identity.",
            "remaining_unknowns": PRIVATE_NOTE_TEXT,
        },
    }


def runtime(*, model: str = "gpt-5.6-codex") -> CodexRuntimeIdentity:
    return CodexRuntimeIdentity(
        model=model,
        reasoning_effort="high",
        service_tier="priority",
        codex_cli_version="0.120.0",
        account_type="chatgpt",
    )


def source_repository(*, suffix: str = "a") -> FieldNoteSourceRepositoryIdentity:
    return FieldNoteSourceRepositoryIdentity(
        repository_id=f"repo:v1:{suffix * 64}",
        source_commit="b" * 40,
    )


def trace_for(
    bundle: FieldNoteWholeFlowEvidenceBundle,
    *,
    repair_stage: str | None = None,
) -> tuple[FieldNoteWholeFlowTraceEvent, ...]:
    assert bundle.a1_capture is not None
    assert bundle.a2_reconnect is not None
    assert bundle.a3_assessment is not None
    assert bundle.a4_snapshot is not None
    assert bundle.a5_commit is not None
    assert bundle.a6_review is not None
    evidence = (
        whole_flow._a1_evidence_sha256(bundle.a1_capture),
        whole_flow._a2_receipt_sha256(bundle.a2_reconnect),
        bundle.a3_assessment.reuse_event_id,
        bundle.a4_snapshot.events[0].event_sha256,
        whole_flow._a5_confirmation_sha256(bundle.a5_commit),
        whole_flow._a6_packet_sha256(bundle.a6_review),
    )
    stages = (
        "A1_CAPTURE",
        "A2_RECONNECT",
        "A3_REUSE",
        "A4_DURABILITY",
        "A5_CONFIRMATION",
        "A6_REVIEW",
    )
    runs = (RUN_1_ID, RUN_2_ID, RUN_2_ID, RUN_2_ID, RUN_2_ID, RUN_2_ID)
    observed = (
        "2026-08-05T10:02:00Z",
        "2026-08-05T11:05:00Z",
        "2026-08-05T11:21:00Z",
        "2026-08-05T11:31:00Z",
        "2026-08-05T11:32:00Z",
        "2026-08-05T11:41:00Z",
    )
    result = []
    previous = whole_flow.TRACE_GENESIS_SHA256
    for index, stage in enumerate(stages):
        event = FieldNoteWholeFlowTraceEvent(
            sequence=index,
            stage=stage,  # type: ignore[arg-type]
            run_id=runs[index],
            observed_at=observed[index],
            evidence_sha256=evidence[index],
            previous_trace_sha256=previous,
            repair_action=(
                "NOTE_EDIT" if stage == repair_stage else "NONE"
            ),
        )
        result.append(event)
        previous = event.trace_sha256
    return tuple(result)


def build_bundle(
    root: Path,
    *,
    outcome: str = "HELPFUL",
    action: str | None = None,
    human_intervention: str = "NONE",
    evidence_class: str = "RULE_TRACE",
    already_recorded: bool = False,
) -> tuple[FieldNoteWholeFlowEvidenceBundle, FieldNoteMaturityLedger]:
    repository = source_repository()
    exact_runtime = runtime()
    attempt = FieldNoteWholeFlowAttempt(
        proof_attempt_id=ATTEMPT_ID,
        proof_mode="FIXTURE",
        creator_id="Shin",
        proof_as_of=PROOF_AS_OF,
    )
    run_1 = FieldNoteWholeFlowRunIdentity(
        proof_attempt_id=ATTEMPT_ID,
        run_id=RUN_1_ID,
        started_at=RUN_1_STARTED,
        repository=repository,
        runtime=exact_runtime,
    )
    run_2 = FieldNoteWholeFlowRunIdentity(
        proof_attempt_id=ATTEMPT_ID,
        run_id=RUN_2_ID,
        started_at=RUN_2_STARTED,
        repository=repository,
        runtime=exact_runtime,
    )
    draft = compile_draft(
        proposal(),
        source_run_id=RUN_1_ID,
        created_at=A1_CREATED,
        field_note_id="fn_a7_whole_flow_fixture",
    )
    note = FieldNoteIdentity(
        note_path=draft.relative_path,
        field_note_id=draft.field_note_id,
        note_sha256=draft.sha256,
        origin_run_id=draft.source_run_id,
    )
    reconnect = FieldNoteReconnectReceipt(
        run_id=RUN_2_ID,
        state="ACTIVATION_UNKNOWN",
        failure_reason=None,
        metadata_entries_seen=1,
        metadata_candidate_files_seen=1,
        metadata_files_valid=1,
        metadata_bytes_read=640,
        selected_field_note_path=note.note_path,
        selected_field_note_id=note.field_note_id,
        selected_metadata_sha256=digest("a7 metadata"),
        selected_full_note_sha256=note.note_sha256,
        full_note_bytes_read=len(draft.markdown),
        full_notes_injected=1,
        ordinary_distinct_paths_consumed=1,
    )
    structure_bytes = STRUCTURE_TEXT.encode("utf-8")
    start = draft.markdown.index(structure_bytes)
    binding = bind_field_note_structure(
        note,
        draft.markdown,
        structure_id="exact-state-before-irreversible-action",
        start_byte=start,
        end_byte=start + len(structure_bytes),
    )
    use_evidence = FieldNoteUseEvidence(
        evidence_class=evidence_class,  # type: ignore[arg-type]
        evidence_origin="IMMEDIATE_COMPLETION_RECORD",
        reusing_run_id=RUN_2_ID,
        structure_binding=binding,
        evidence_ref="run:run_a7_reuse/evidence:exact-state-rule",
        evidence_sha256=digest("bounded A7 use evidence"),
        observer_id="a7_fixture_observer",
        observer_relation="INDEPENDENT",
        as_of=USE_AS_OF,
    )
    causal = outcome in {"HELPFUL", "HARMFUL"}
    evaluation = FieldNoteOutcomeEvaluation(
        outcome=outcome,  # type: ignore[arg-type]
        scope="The exact bounded A7 fixture task.",
        observer_id="a7_outcome_observer",
        observer_relation="INDEPENDENT",
        as_of=OUTCOME_AS_OF,
        causal_evidence_ref=(
            "run:run_a7_reuse/causal:exact-state-rule" if causal else None
        ),
        causal_evidence_sha256=(
            digest("bounded A7 causal evidence") if causal else None
        ),
        contribution_separated=True,
    )
    if action is None:
        if outcome == "HELPFUL":
            action = "KEEP"
        elif outcome in {"NOT_HELPFUL", "HARMFUL"}:
            action = "STOP"
    disposition = None
    if action == "KEEP":
        disposition = FieldNoteReuseDisposition(action="KEEP")
    elif action == "STOP":
        disposition = FieldNoteReuseDisposition(
            action="STOP",
            stop_scope="Only the exact A7 fixture task family.",
        )
    elif action == "REVISE":
        successor_bytes = b"A7 successor candidate"
        disposition = FieldNoteReuseDisposition(
            action="REVISE",
            revision_candidate=FieldNoteIdentity(
                note_path=(
                    ".decision-os/field-notes/"
                    "2026-08-05-a7-successor-aaaaaaaaaa.md"
                ),
                field_note_id="fn_a7_successor",
                note_sha256=digest(successor_bytes),
                origin_run_id=RUN_2_ID,
            ),
        )
    claim = FieldNoteReuseClaim(
        claimed_note=note,
        reusing_run_id=RUN_2_ID,
        use_evidence=use_evidence,
        outcome_evaluation=evaluation,
        human_intervention=human_intervention,  # type: ignore[arg-type]
        disposition=disposition,
    )
    ledger = FieldNoteMaturityLedger(root / "maturity-ledger-v0.1", note)
    request = FieldNoteMaturityCommitRequest(
        note=note,
        note_bytes=draft.markdown,
        reuse_claim=claim,
        recorded_at=RECORDED_AT,
        delivery_context=reconnect,
    )
    commit = commit_field_note_maturity(ledger, request)
    if already_recorded:
        commit = commit_field_note_maturity(ledger, request)
    assert commit.durable_snapshot is not None
    assessment = commit.assessment
    review = review_field_note_maturity(
        ledger,
        note,
        note_bytes=draft.markdown,
        review_as_of=REVIEW_AS_OF,
    )
    bundle = FieldNoteWholeFlowEvidenceBundle(
        attempt=attempt,
        source_repository=repository,
        run_1=run_1,
        run_2=run_2,
        note=note,
        note_bytes=draft.markdown,
        a1_capture=draft,
        a2_reconnect=reconnect,
        a3_assessment=assessment,
        a4_snapshot=commit.durable_snapshot,
        a5_commit=commit,
        a6_review=review,
        proof_trace=(),
    )
    return replace(bundle, proof_trace=trace_for(bundle)), ledger


class WholeFlowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bundle, self.ledger = build_bundle(self.root)

    def verify(self, bundle=None) -> FieldNoteWholeFlowProofReceipt:
        return verify_field_note_whole_flow(bundle or self.bundle)


class FieldNoteWholeFlowPassTests(WholeFlowTestCase):
    def test_complete_valid_fixture_produces_typed_pass(self) -> None:
        receipt = self.verify()
        self.assertIsInstance(receipt, FieldNoteWholeFlowProofReceipt)
        self.assertEqual("PASS", receipt.state)
        self.assertIsNone(receipt.failed_boundary)
        self.assertEqual("TYPED_TRACE_VERIFIED", receipt.human_repair_result)

    def test_fixture_pass_is_not_a_creator_live_proof(self) -> None:
        receipt = self.verify()
        self.assertEqual("FIXTURE", receipt.proof_mode)
        self.assertFalse(
            receipt.claim_boundary.creator_live_proof_inferred_from_fixture
        )

    def test_helpful_outcome_can_pass_without_becoming_flow_identity(self) -> None:
        receipt = self.verify()
        self.assertEqual("PASS", receipt.state)
        self.assertEqual("HELPFUL", receipt.effective_outcome)
        self.assertEqual("KEEP", receipt.next_disposition)
        self.assertTrue(receipt.claim_boundary.usefulness_separate)

    def test_unknown_hold_can_pass(self) -> None:
        bundle, _ = build_bundle(self.root / "unknown", outcome="UNKNOWN")
        receipt = self.verify(bundle)
        self.assertEqual("PASS", receipt.state)
        self.assertEqual("UNKNOWN", receipt.effective_outcome)
        self.assertEqual("HOLD", receipt.next_disposition)

    def test_not_helpful_stop_or_revise_can_pass(self) -> None:
        for action in ("STOP", "REVISE"):
            with self.subTest(action=action):
                bundle, _ = build_bundle(
                    self.root / action.lower(),
                    outcome="NOT_HELPFUL",
                    action=action,
                )
                receipt = self.verify(bundle)
                self.assertEqual("PASS", receipt.state)
                self.assertEqual("NOT_HELPFUL", receipt.effective_outcome)
                self.assertEqual(action, receipt.next_disposition)

    def test_harmful_stop_or_revise_can_pass(self) -> None:
        for action in ("STOP", "REVISE"):
            with self.subTest(action=action):
                bundle, _ = build_bundle(
                    self.root / f"harmful-{action.lower()}",
                    outcome="HARMFUL",
                    action=action,
                )
                receipt = self.verify(bundle)
                self.assertEqual("PASS", receipt.state)
                self.assertEqual("HARMFUL", receipt.effective_outcome)
                self.assertEqual(action, receipt.next_disposition)

    def test_negative_outcome_remains_in_receipt_and_manifest(self) -> None:
        bundle, _ = build_bundle(self.root / "negative", outcome="HARMFUL")
        receipt = self.verify(bundle)
        manifest = build_portable_candidate_warehouse_manifest(bundle)
        self.assertEqual("HARMFUL", receipt.effective_outcome)
        self.assertEqual(1, manifest.as_dict()["outcome_summary"]["harmful"])
        self.assertEqual("HARMFUL", manifest.as_dict()["effective_outcome"])

    def test_human_intervention_remains_visible(self) -> None:
        bundle, _ = build_bundle(
            self.root / "intervention",
            human_intervention="MATERIAL",
        )
        receipt = self.verify(bundle)
        manifest = build_portable_candidate_warehouse_manifest(bundle)
        self.assertEqual("PASS", receipt.state)
        self.assertEqual("MATERIAL", receipt.human_intervention)
        self.assertEqual("MATERIAL", manifest.as_dict()["human_intervention"])

    def test_repeated_receipt_generation_is_deterministic(self) -> None:
        first = self.verify()
        second = self.verify()
        self.assertEqual(first, second)
        self.assertEqual(first.receipt_sha256, second.receipt_sha256)
        self.assertEqual(first.serialize(), second.serialize())
        self.assertEqual(first.render_text(), second.render_text())

    def test_receipt_projection_is_canonical_and_bounded(self) -> None:
        receipt = self.verify()
        self.assertEqual(canonical_json(receipt.as_dict()), receipt.serialize())
        self.assertTrue(receipt.render_text().endswith("\n"))
        self.assertNotIn(PRIVATE_NOTE_TEXT, receipt.serialize())
        self.assertNotIn(ARTIFACT_SECRET, receipt.serialize())

    def test_verification_is_read_only_over_a1_through_a6_artifacts(self) -> None:
        paths = (
            self.ledger.events_path,
            self.ledger.head_path,
            self.ledger.lock_path,
        )
        before = {
            path: (
                path.read_bytes(),
                path.stat().st_mode,
                path.stat().st_mtime_ns,
                path.stat().st_ino,
            )
            for path in paths
        }
        note_before = bytes(self.bundle.note_bytes)
        self.verify()
        build_portable_candidate_warehouse_manifest(self.bundle)
        after = {
            path: (
                path.read_bytes(),
                path.stat().st_mode,
                path.stat().st_mtime_ns,
                path.stat().st_ino,
            )
            for path in paths
        }
        self.assertEqual(before, after)
        self.assertEqual(note_before, self.bundle.note_bytes)


class FieldNoteWholeFlowProofSealingTests(WholeFlowTestCase):
    def test_pass_receipt_seals_exact_six_checkpoint_trace(self) -> None:
        receipt = self.verify()
        self.assertEqual(whole_flow.WHOLE_FLOW_TRACE_SCHEMA, receipt.proof_trace_schema)
        self.assertEqual(6, receipt.proof_trace_event_count)
        self.assertEqual(self.bundle.proof_trace, receipt.proof_trace)
        self.assertEqual(
            self.bundle.proof_trace[-1].trace_sha256,
            receipt.proof_trace_chain_head_sha256,
        )
        self.assertEqual(
            receipt.proof_trace_chain_head_sha256,
            receipt.as_dict()["proof_trace_chain_head_sha256"],
        )

    def test_valid_checkpoint_identity_change_changes_receipt_identity(self) -> None:
        original = self.verify()
        changed_trace = (
            *self.bundle.proof_trace[:-1],
            replace(
                self.bundle.proof_trace[-1],
                observed_at="2026-08-05T11:42:00Z",
            ),
        )
        changed = self.verify(replace(self.bundle, proof_trace=changed_trace))
        self.assertEqual("PASS", changed.state)
        self.assertNotEqual(
            original.proof_trace_chain_head_sha256,
            changed.proof_trace_chain_head_sha256,
        )
        self.assertNotEqual(original.receipt_sha256, changed.receipt_sha256)

    def test_direct_receipt_cannot_claim_verified_without_trace_identity(self) -> None:
        receipt = self.verify()
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            replace(
                receipt,
                proof_trace=(),
                proof_trace_event_count=0,
                proof_trace_chain_head_sha256=None,
            )

    def test_receipt_seals_complete_run_identities(self) -> None:
        receipt = self.verify()
        self.assertEqual(self.bundle.run_1, receipt.run_1)
        self.assertEqual(self.bundle.run_2, receipt.run_2)
        self.assertEqual(RUN_1_ID, receipt.run_1_id)
        self.assertEqual(RUN_2_ID, receipt.run_2_id)
        self.assertEqual(
            self.bundle.run_1.as_dict(),
            receipt.as_dict()["run_1"],
        )
        self.assertEqual(
            self.bundle.run_2.as_dict(),
            receipt.as_dict()["run_2"],
        )

    def test_direct_pass_receipt_rejects_inconsistent_run_identities(self) -> None:
        receipt = self.verify()
        cases = (
            ("same_run", replace(receipt.run_2, run_id=receipt.run_1_id)),
            (
                "not_later",
                replace(receipt.run_2, started_at=receipt.run_1.started_at),
            ),
            (
                "other_attempt",
                replace(receipt.run_2, proof_attempt_id="other_attempt"),
            ),
            (
                "other_repository",
                replace(receipt.run_2, repository=source_repository(suffix="c")),
            ),
            (
                "other_runtime",
                replace(receipt.run_2, runtime=runtime(model="other-model")),
            ),
        )
        for label, run_2 in cases:
            with self.subTest(label=label):
                with self.assertRaises(FieldNoteWholeFlowValidationError):
                    replace(receipt, run_2=run_2)

    def test_creator_live_mode_is_exactly_not_ready(self) -> None:
        live_attempt = replace(self.bundle.attempt, proof_mode="CREATOR_LIVE")
        receipt = self.verify(replace(self.bundle, attempt=live_attempt))
        self.assertEqual("NOT_READY", receipt.state)
        self.assertEqual("RUNTIME_ENFORCEMENT", receipt.failed_boundary)
        self.assertEqual(
            "CREATOR_LIVE_RUNTIME_ENFORCEMENT_NOT_IMPLEMENTED",
            receipt.failure_reason,
        )

    def test_hand_built_six_checkpoint_trace_cannot_enable_creator_live(self) -> None:
        self.assertEqual(6, len(self.bundle.proof_trace))
        self.assertTrue(
            all(
                event.emitter == "COMPANION_RUNTIME"
                for event in self.bundle.proof_trace
            )
        )
        live_attempt = replace(self.bundle.attempt, proof_mode="CREATOR_LIVE")
        live_bundle = replace(
            self.bundle,
            attempt=live_attempt,
            proof_trace=trace_for(self.bundle),
        )
        receipt = self.verify(live_bundle)
        self.assertEqual("NOT_READY", receipt.state)
        self.assertNotEqual("TYPED_TRACE_VERIFIED", receipt.human_repair_result)
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            build_portable_candidate_warehouse_manifest(live_bundle)


class FieldNoteWholeFlowReadinessTests(WholeFlowTestCase):
    def test_missing_a1_is_not_ready_at_exact_boundary(self) -> None:
        receipt = self.verify(replace(self.bundle, a1_capture=None))
        self.assertEqual("NOT_READY", receipt.state)
        self.assertEqual("A1_CAPTURE", receipt.failed_boundary)
        self.assertEqual("A1_EVIDENCE_MISSING", receipt.failure_reason)

    def test_missing_a2_is_not_ready_at_exact_boundary(self) -> None:
        receipt = self.verify(replace(self.bundle, a2_reconnect=None))
        self.assertEqual("NOT_READY", receipt.state)
        self.assertEqual("A2_RECONNECT", receipt.failed_boundary)
        self.assertEqual("A2_EVIDENCE_MISSING", receipt.failure_reason)

    def test_a2_injection_alone_cannot_satisfy_missing_a3(self) -> None:
        receipt = self.verify(replace(self.bundle, a3_assessment=None))
        self.assertEqual("NOT_READY", receipt.state)
        self.assertEqual("A3_REUSE", receipt.failed_boundary)
        self.assertEqual("A3_EVIDENCE_MISSING", receipt.failure_reason)

    def test_missing_a4_a5_or_a6_is_not_ready(self) -> None:
        cases = (
            ("a4_snapshot", "A4_DURABILITY"),
            ("a5_commit", "A5_CONFIRMATION"),
            ("a6_review", "A6_REVIEW"),
        )
        for field, boundary in cases:
            with self.subTest(field=field):
                receipt = self.verify(replace(self.bundle, **{field: None}))
                self.assertEqual("NOT_READY", receipt.state)
                self.assertEqual(boundary, receipt.failed_boundary)

    def test_candidate_a3_cannot_pass(self) -> None:
        candidate = assess_field_note_reuse(
            self.bundle.note,
            None,
            note_bytes=self.bundle.note_bytes,
        )
        receipt = self.verify(
            replace(self.bundle, a3_assessment=candidate)
        )
        self.assertEqual("FAIL", receipt.state)
        self.assertEqual("A3_REUSE", receipt.failed_boundary)
        self.assertEqual("A3_NOT_DEMONSTRABLY_REUSED", receipt.failure_reason)

    def test_narrative_use_claim_cannot_pass(self) -> None:
        claim = FieldNoteReuseClaim(
            claimed_note=self.bundle.note,
            reusing_run_id=RUN_2_ID,
            use_evidence=None,
            outcome_evaluation=None,
            human_intervention="NONE",
            disposition=None,
            narrative_claim="The Note was reused; trust this sentence.",
        )
        candidate = assess_field_note_reuse(
            self.bundle.note,
            claim,
            note_bytes=self.bundle.note_bytes,
        )
        receipt = self.verify(
            replace(self.bundle, a3_assessment=candidate)
        )
        self.assertEqual("FAIL", receipt.state)
        self.assertEqual("A3_NOT_DEMONSTRABLY_REUSED", receipt.failure_reason)

    def test_free_form_no_repair_attestation_is_not_an_input(self) -> None:
        with self.assertRaises(TypeError):
            FieldNoteWholeFlowEvidenceBundle(
                **self.bundle.__dict__,
                no_repair_attestation="no repair occurred",
            )
        receipt = self.verify(replace(self.bundle, proof_trace=()))
        self.assertEqual("NOT_READY", receipt.state)
        self.assertEqual("HUMAN_REPAIR", receipt.failed_boundary)


class FieldNoteWholeFlowBindingTests(WholeFlowTestCase):
    def test_run_1_and_run_2_must_be_distinct(self) -> None:
        run_2 = replace(self.bundle.run_2, run_id=RUN_1_ID)
        receipt = self.verify(replace(self.bundle, run_2=run_2))
        self.assertEqual("RUN_IDENTITIES_NOT_DISTINCT", receipt.failure_reason)

    def test_run_2_must_be_later(self) -> None:
        run_2 = replace(
            self.bundle.run_2,
            started_at="2026-08-05T09:59:00Z",
        )
        receipt = self.verify(replace(self.bundle, run_2=run_2))
        self.assertEqual("RUN_ORDER_INVALID", receipt.failure_reason)

    def test_both_runs_must_belong_to_the_same_attempt(self) -> None:
        run_2 = replace(self.bundle.run_2, proof_attempt_id="other_attempt")
        receipt = self.verify(replace(self.bundle, run_2=run_2))
        self.assertEqual("RUN_ATTEMPT_MISMATCH", receipt.failure_reason)

    def test_model_runtime_identities_must_match_exactly(self) -> None:
        run_2 = replace(self.bundle.run_2, runtime=runtime(model="other-model"))
        receipt = self.verify(replace(self.bundle, run_2=run_2))
        self.assertEqual("MODEL_IDENTITY", receipt.failed_boundary)
        self.assertEqual("MODEL_RUNTIME_MISMATCH", receipt.failure_reason)

    def test_cross_repository_evidence_cannot_pass(self) -> None:
        run_2 = replace(self.bundle.run_2, repository=source_repository(suffix="c"))
        receipt = self.verify(replace(self.bundle, run_2=run_2))
        self.assertEqual("REPOSITORY_IDENTITY", receipt.failed_boundary)
        self.assertEqual("SOURCE_REPOSITORY_MISMATCH", receipt.failure_reason)

    def test_a1_note_rewrite_cannot_pass(self) -> None:
        receipt = self.verify(
            replace(self.bundle, note_bytes=self.bundle.note_bytes + b"rewrite")
        )
        self.assertEqual("A1_CAPTURE", receipt.failed_boundary)
        self.assertEqual("A1_NOTE_IDENTITY_MISMATCH", receipt.failure_reason)

    def test_a1_must_originate_in_run_1(self) -> None:
        wrong_note = replace(self.bundle.note, origin_run_id="other_origin")
        receipt = self.verify(replace(self.bundle, note=wrong_note))
        self.assertEqual("A1_RUN_MISMATCH", receipt.failure_reason)

    def test_a2_exact_note_mismatch_cannot_pass(self) -> None:
        assert self.bundle.a2_reconnect is not None
        for field, value in (
            ("selected_field_note_path", ".decision-os/field-notes/other.md"),
            ("selected_field_note_id", "fn_other"),
            ("selected_full_note_sha256", "c" * 64),
            ("full_note_bytes_read", len(self.bundle.note_bytes) + 1),
        ):
            with self.subTest(field=field):
                a2 = replace(self.bundle.a2_reconnect, **{field: value})
                receipt = self.verify(replace(self.bundle, a2_reconnect=a2))
                self.assertEqual("A2_RECONNECT", receipt.failed_boundary)
                self.assertEqual("A2_EXACT_NOTE_MISMATCH", receipt.failure_reason)

    def test_a2_run_mismatch_cannot_pass(self) -> None:
        assert self.bundle.a2_reconnect is not None
        a2 = replace(self.bundle.a2_reconnect, run_id="other_run")
        receipt = self.verify(replace(self.bundle, a2_reconnect=a2))
        self.assertEqual("A2_RUN_MISMATCH", receipt.failure_reason)

    def test_a2_selected_but_not_injected_cannot_pass(self) -> None:
        assert self.bundle.a2_reconnect is not None
        a2 = replace(
            self.bundle.a2_reconnect,
            state="SELECTED",
            selected_full_note_sha256=None,
            full_note_bytes_read=0,
            full_notes_injected=0,
        )
        receipt = self.verify(replace(self.bundle, a2_reconnect=a2))
        self.assertEqual("A2_NOT_INJECTED", receipt.failure_reason)

    def test_a3_exact_note_mismatch_cannot_pass(self) -> None:
        assert self.bundle.a3_assessment is not None
        other = replace(self.bundle.note, field_note_id="fn_other")
        a3 = replace(self.bundle.a3_assessment, note=other)
        receipt = self.verify(replace(self.bundle, a3_assessment=a3))
        self.assertEqual("A3_EXACT_NOTE_MISMATCH", receipt.failure_reason)

    def test_a3_run_mismatch_cannot_pass(self) -> None:
        assert self.bundle.a3_assessment is not None
        a3 = replace(self.bundle.a3_assessment, reusing_run_id="other_run")
        receipt = self.verify(replace(self.bundle, a3_assessment=a3))
        self.assertEqual("A3_RUN_MISMATCH", receipt.failure_reason)

    def test_wrong_specific_structure_cannot_pass(self) -> None:
        assert self.bundle.a3_assessment is not None
        assert self.bundle.a3_assessment.use_evidence is not None
        evidence = self.bundle.a3_assessment.use_evidence
        bad_binding = replace(
            evidence.structure_binding,
            structure_sha256="d" * 64,
        )
        bad_evidence = replace(evidence, structure_binding=bad_binding)
        a3 = replace(self.bundle.a3_assessment, use_evidence=bad_evidence)
        receipt = self.verify(replace(self.bundle, a3_assessment=a3))
        self.assertEqual("A3_STRUCTURE_BINDING_INVALID", receipt.failure_reason)

    def test_a3_evidence_time_order_must_be_valid(self) -> None:
        assert self.bundle.a3_assessment is not None
        assert self.bundle.a3_assessment.use_evidence is not None
        evidence = replace(
            self.bundle.a3_assessment.use_evidence,
            as_of="2026-08-05T11:25:00Z",
        )
        a3 = replace(self.bundle.a3_assessment, use_evidence=evidence)
        a3 = replace(
            a3,
            reuse_event_id=whole_flow._expected_reuse_event_id(a3),
        )
        receipt = self.verify(replace(self.bundle, a3_assessment=a3))
        self.assertEqual("A3_EVIDENCE_TIME_ORDER_INVALID", receipt.failure_reason)

    def test_a4_missing_exact_event_cannot_pass(self) -> None:
        assert self.bundle.a4_snapshot is not None
        a4 = replace(
            self.bundle.a4_snapshot,
            events=(),
            chain_head_sha256=GENESIS_EVENT_SHA256,
        )
        receipt = self.verify(replace(self.bundle, a4_snapshot=a4))
        self.assertEqual("A4_EVENT_COUNT_NOT_EXACTLY_ONE", receipt.failure_reason)

    def test_a4_extra_history_is_not_silently_accepted(self) -> None:
        assert self.bundle.a4_snapshot is not None
        event = self.bundle.a4_snapshot.events[0]
        a4 = replace(self.bundle.a4_snapshot, events=(event, event))
        receipt = self.verify(replace(self.bundle, a4_snapshot=a4))
        self.assertEqual("A4_EVENT_COUNT_NOT_EXACTLY_ONE", receipt.failure_reason)

    def test_a4_tampering_cannot_pass(self) -> None:
        assert self.bundle.a4_snapshot is not None
        event = replace(
            self.bundle.a4_snapshot.events[0],
            event_sha256="e" * 64,
        )
        a4 = replace(
            self.bundle.a4_snapshot,
            events=(event,),
            chain_head_sha256="e" * 64,
        )
        receipt = self.verify(replace(self.bundle, a4_snapshot=a4))
        self.assertEqual("A4_EXACT_EVENT_INTEGRITY_INVALID", receipt.failure_reason)

    def test_a4_recorded_at_must_follow_reuse_evidence(self) -> None:
        assert self.bundle.a4_snapshot is not None
        event = replace(
            self.bundle.a4_snapshot.events[0],
            recorded_at="2026-08-05T11:15:00Z",
        )
        event = replace(
            event,
            event_sha256=whole_flow._event_sha256(event),
        )
        a4 = replace(
            self.bundle.a4_snapshot,
            events=(event,),
            chain_head_sha256=event.event_sha256,
        )
        receipt = self.verify(replace(self.bundle, a4_snapshot=a4))
        self.assertEqual("A4_EVENT_TIME_ORDER_INVALID", receipt.failure_reason)

    def test_a5_unconfirmed_append_cannot_pass(self) -> None:
        assert self.bundle.a5_commit is not None
        object.__setattr__(self.bundle.a5_commit, "durable_snapshot", None)
        receipt = self.verify()
        self.assertEqual("A5_APPEND_NOT_CONFIRMED", receipt.failure_reason)

    def test_a5_response_loss_reconciliation_can_pass_after_read_back(self) -> None:
        bundle, _ = build_bundle(self.root / "already", already_recorded=True)
        receipt = self.verify(bundle)
        self.assertEqual("PASS", receipt.state)
        self.assertEqual("ALREADY_RECORDED", receipt.a5_status)
        self.assertTrue(receipt.a5_durable_commit_confirmed)

    def test_a5_must_preserve_a2_delivery_lineage(self) -> None:
        assert self.bundle.a5_commit is not None
        object.__setattr__(self.bundle.a5_commit, "delivery_context", None)
        receipt = self.verify()
        self.assertEqual("A5_READ_BACK_LINEAGE_MISMATCH", receipt.failure_reason)

    def test_a6_exact_note_mismatch_cannot_pass(self) -> None:
        assert self.bundle.a6_review is not None
        other = replace(self.bundle.note, field_note_id="fn_other_a6")
        object.__setattr__(self.bundle.a6_review, "note_identity", other)
        receipt = self.verify()
        self.assertEqual("A6_EXACT_NOTE_MISMATCH", receipt.failure_reason)

    def test_a6_chain_head_mismatch_cannot_pass(self) -> None:
        assert self.bundle.a6_review is not None
        identity = replace(
            self.bundle.a6_review.ledger_identity,
            chain_head_sha256="f" * 64,
        )
        object.__setattr__(self.bundle.a6_review, "ledger_identity", identity)
        receipt = self.verify()
        self.assertEqual("A6_LEDGER_IDENTITY_MISMATCH", receipt.failure_reason)

    def test_a6_must_exactly_match_every_projected_a3_evidence_axis(self) -> None:
        assert self.bundle.a6_review is not None
        review = self.bundle.a6_review.ordered_event_reviews[0]
        cases = (
            ("evidence_origin", {"evidence_origin": "REUSING_RUN"}),
            (
                "use_observer_id",
                {"use_evidence_observer_id": "other_use_observer"},
            ),
            (
                "use_observer_relation",
                {"use_evidence_observer_relation": "REUSING_RUN_SELF"},
            ),
            ("outcome_scope", {"outcome_scope": "A different task scope."}),
            (
                "causal_evidence_ref",
                {"causal_evidence_ref": "run:other/causal:evidence"},
            ),
            (
                "causal_evidence_sha256",
                {"causal_evidence_sha256": "f" * 64},
            ),
            (
                "outcome_observer_id",
                {"outcome_observer_id": "other_outcome_observer"},
            ),
            (
                "outcome_observer_relation",
                {"outcome_observer_relation": "REUSING_RUN_PARTICIPANT"},
            ),
            (
                "outcome_confirmation",
                {"outcome_confirmation": "RUN_RELATED_CLAIM"},
            ),
            (
                "contribution_separated",
                {"contribution_separated": False},
            ),
        )
        for label, mutation in cases:
            with self.subTest(label=label):
                changed_review = replace(review, **mutation)
                changed_a6 = replace(self.bundle.a6_review)
                object.__setattr__(
                    changed_a6,
                    "ordered_event_reviews",
                    (changed_review,),
                )
                receipt = self.verify(
                    replace(self.bundle, a6_review=changed_a6)
                )
                self.assertEqual("FAIL", receipt.state)
                self.assertEqual("A6_REVIEW", receipt.failed_boundary)
                self.assertEqual(
                    "A6_EXACT_EVENT_MISMATCH",
                    receipt.failure_reason,
                )

    def test_a6_future_dated_evidence_cannot_pass(self) -> None:
        assert self.bundle.a6_review is not None
        object.__setattr__(
            self.bundle.a6_review,
            "review_as_of",
            "2026-08-05T11:29:59Z",
        )
        receipt = self.verify()
        self.assertEqual("A6_FUTURE_DATED_EVIDENCE", receipt.failure_reason)

    def test_proof_as_of_must_not_precede_a6(self) -> None:
        attempt = replace(
            self.bundle.attempt,
            proof_as_of="2026-08-05T11:39:59Z",
        )
        receipt = self.verify(replace(self.bundle, attempt=attempt))
        self.assertEqual("PROOF_AS_OF", receipt.failed_boundary)
        self.assertEqual("PROOF_AS_OF_PRECEDES_A6_REVIEW", receipt.failure_reason)

    def test_human_repair_evidence_causes_fail(self) -> None:
        trace = trace_for(self.bundle, repair_stage="A3_REUSE")
        receipt = self.verify(replace(self.bundle, proof_trace=trace))
        self.assertEqual("FAIL", receipt.state)
        self.assertEqual("HUMAN_REPAIR", receipt.failed_boundary)
        self.assertEqual("HUMAN_REPAIR_DETECTED", receipt.failure_reason)
        self.assertEqual("REPAIR_DETECTED", receipt.human_repair_result)

    def test_trace_must_bind_each_exact_layer_identity(self) -> None:
        trace = list(self.bundle.proof_trace)
        trace[3] = replace(trace[3], evidence_sha256="f" * 64)
        receipt = self.verify(replace(self.bundle, proof_trace=tuple(trace)))
        self.assertEqual("TYPED_PROOF_TRACE_INVALID", receipt.failure_reason)


class PortableCandidateWarehouseManifestTests(WholeFlowTestCase):
    def manifest(self) -> PortableCandidateWarehouseManifest:
        return build_portable_candidate_warehouse_manifest(self.bundle)

    def test_pass_produces_one_typed_manifest(self) -> None:
        manifest = self.manifest()
        self.assertIsInstance(manifest, PortableCandidateWarehouseManifest)
        self.assertEqual(
            "PORTABLE_CANDIDATE",
            manifest.claim_boundary.portability_state,
        )

    def test_arbitrary_pass_receipt_cannot_mint_a_manifest(self) -> None:
        arbitrary = replace(self.verify(), effective_outcome="HARMFUL")
        self.assertEqual("PASS", arbitrary.state)
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            PortableCandidateWarehouseManifest(arbitrary)
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            build_portable_candidate_warehouse_manifest(
                arbitrary  # type: ignore[arg-type]
            )

    def test_failed_or_not_ready_bundle_cannot_mint_a_manifest(self) -> None:
        cases = (
            replace(
                self.bundle,
                note_bytes=self.bundle.note_bytes + b"changed",
            ),
            replace(self.bundle, a1_capture=None),
        )
        for bundle in cases:
            with self.subTest(state=self.verify(bundle).state):
                with self.assertRaises(FieldNoteWholeFlowValidationError):
                    build_portable_candidate_warehouse_manifest(bundle)

    def test_bundle_mutation_cannot_reuse_an_old_receipt(self) -> None:
        old_receipt = self.verify()
        changed = replace(
            self.bundle,
            note_bytes=self.bundle.note_bytes + b"post-receipt mutation",
        )
        self.assertEqual("FAIL", self.verify(changed).state)
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            build_portable_candidate_warehouse_manifest(changed)
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            build_portable_candidate_warehouse_manifest(
                old_receipt  # type: ignore[arg-type]
            )

    def test_repeated_manifest_generation_is_deterministic(self) -> None:
        first = self.manifest()
        second = self.manifest()
        self.assertEqual(first, second)
        self.assertEqual(first.manifest_id, second.manifest_id)
        self.assertEqual(first.serialize(), second.serialize())
        self.assertEqual(first.render_text(), second.render_text())

    def test_manifest_identity_is_stable_for_identical_immutable_evidence(self) -> None:
        first = build_portable_candidate_warehouse_manifest(self.bundle)
        second = build_portable_candidate_warehouse_manifest(self.bundle)
        self.assertEqual(first.portable_asset_id, second.portable_asset_id)
        self.assertEqual(first.manifest_id, second.manifest_id)

    def test_changed_note_bytes_invalidate_portable_identity_generation(self) -> None:
        changed = replace(
            self.bundle,
            note_bytes=self.bundle.note_bytes + b"changed",
        )
        receipt = self.verify(changed)
        self.assertEqual("FAIL", receipt.state)
        with self.assertRaises(FieldNoteWholeFlowValidationError):
            build_portable_candidate_warehouse_manifest(changed)

    def test_manifest_coverage_is_exactly_one_one_one(self) -> None:
        manifest = self.manifest()
        body = manifest.as_dict()
        coverage = body["verified_coverage"]
        self.assertEqual(
            {
                "repositories": 1,
                "model_identities": 1,
                "verified_later_reuse_runs": 1,
            },
            coverage,
        )
        self.assertEqual("FIXTURE", body["coverage_evidence_mode"])
        self.assertFalse(body["creator_live_coverage_verified"])
        self.assertIn("Fixture-covered repositories: 1", manifest.render_text())
        self.assertNotIn("Verified repositories: 1", manifest.render_text())

    def test_fixture_receipt_and_manifest_emit_no_creator_live_claim(self) -> None:
        receipt = self.verify()
        manifest = self.manifest()
        self.assertEqual("FIXTURE", receipt.proof_mode)
        self.assertFalse(
            receipt.claim_boundary.creator_live_proof_inferred_from_fixture
        )
        self.assertEqual("FIXTURE", manifest.as_dict()["coverage_evidence_mode"])
        self.assertFalse(
            manifest.as_dict()["creator_live_coverage_verified"]
        )
        self.assertNotIn('"proof_mode":"CREATOR_LIVE"', receipt.serialize())
        self.assertNotIn('"proof_mode":"CREATOR_LIVE"', manifest.serialize())

    def test_manifest_is_bound_to_trace_sealed_receipt(self) -> None:
        receipt = self.verify()
        manifest = self.manifest()
        proof_trace = manifest.as_dict()["proof_trace"]
        self.assertEqual(receipt, manifest.proof_receipt)
        self.assertEqual(
            {
                "schema": receipt.proof_trace_schema,
                "event_count": receipt.proof_trace_event_count,
                "chain_head_sha256": receipt.proof_trace_chain_head_sha256,
            },
            proof_trace,
        )
        self.assertEqual(
            receipt.receipt_sha256,
            manifest.as_dict()["whole_flow_proof_receipt_sha256"],
        )

    def test_manifest_is_candidate_not_portability_proven(self) -> None:
        boundary = self.manifest().claim_boundary
        self.assertEqual("PORTABLE_CANDIDATE", boundary.portability_state)
        self.assertFalse(boundary.portability_proven)
        self.assertFalse(boundary.cross_repository_import_verified)
        self.assertFalse(boundary.cross_model_reuse_verified)

    def test_manifest_excludes_full_note_contents(self) -> None:
        manifest = self.manifest()
        self.assertNotIn(PRIVATE_NOTE_TEXT, manifest.serialize())
        self.assertNotIn(self.bundle.note_bytes.decode("utf-8"), manifest.serialize())

    def test_manifest_excludes_output_artifact_contents(self) -> None:
        bundle, _ = build_bundle(
            self.root / "artifact",
            evidence_class="OUTPUT_ARTIFACT",
        )
        manifest = build_portable_candidate_warehouse_manifest(bundle)
        self.assertNotIn(ARTIFACT_SECRET, manifest.serialize())

    def test_promotable_remains_unset(self) -> None:
        manifest = self.manifest().as_dict()
        self.assertEqual("UNSET", manifest["promotable_policy"])
        self.assertEqual("UNSET", self.verify().claim_boundary.promotable_policy)

    def test_serving_policy_remains_separate_and_delayed(self) -> None:
        manifest = self.manifest().as_dict()
        self.assertEqual("DELAY", manifest["serving_policy"])
        self.assertEqual("DELAY", self.verify().claim_boundary.serving_policy)

    def test_no_automatic_injection_is_derived(self) -> None:
        manifest = self.manifest().as_dict()
        self.assertIsNone(manifest["automatic_injection"])
        self.assertFalse(self.verify().claim_boundary.automatic_injection_derived)

    def test_canonical_authority_remains_above_advisory_note(self) -> None:
        manifest = self.manifest().as_dict()
        self.assertEqual(
            ["TOPMOST_CANONICAL", "ADVISORY_FIELD_NOTE"],
            manifest["authority_precedence"],
        )

    def test_future_evidence_is_target_local_not_a_shared_mutable_chain(self) -> None:
        manifest = self.manifest()
        boundary = manifest.claim_boundary
        self.assertTrue(boundary.source_evidence_immutable)
        self.assertEqual("TARGET_REPOSITORY_LOCAL", boundary.future_evidence_scope)
        self.assertTrue(boundary.explicit_import_receipt_required)
        self.assertFalse(boundary.shared_mutable_ledger)
        self.assertFalse(boundary.diverged_ledger_merge_supported)

    def test_manifest_serialization_is_canonical_and_bounded(self) -> None:
        manifest = self.manifest()
        self.assertEqual(canonical_json(manifest.as_dict()), manifest.serialize())
        self.assertTrue(manifest.render_text().endswith("\n"))
        self.assertNotIn("PORTABILITY_PROVEN", manifest.serialize())


if __name__ == "__main__":
    unittest.main()
