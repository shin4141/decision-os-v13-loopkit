from __future__ import annotations

import hashlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from decision_os.acceleration import codex_adapter as codex
from decision_os.acceleration.codex_adapter import (
    ADAPTER_NAME,
    CODEX_CLI_VERSION,
    CodexRuntimeIdentity,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import git_output, repository_id
from decision_os.companion import field_notes_creator_live as creator_live
from decision_os.companion import field_notes_creator_live_reconnect as exact_a2
from decision_os.companion import field_notes_reconnect as reconnect
from decision_os.companion import field_notes_whole_flow as whole_flow
from decision_os.companion.field_notes_adapter import (
    FieldNoteCodexRunResult,
    FieldNoteCreatorLiveA1CaptureConfig,
    FieldNotesCodexAdapter,
)
from decision_os.companion.field_notes_controller import (
    FieldNotesCompanionController,
)
from decision_os.companion.field_notes_creator_live import (
    FieldNoteCreatorLiveA1CaptureCommitReceipt,
    FieldNoteCreatorLiveProofRuntime,
)
from decision_os.companion.field_notes_creator_live_reconnect import (
    FieldNoteCreatorLiveA2ReconnectBridge,
    FieldNoteCreatorLiveA2ReconnectError,
    FieldNoteCreatorLiveA2ReconnectTarget,
    creator_live_a2_target_from_readback,
    prepare_creator_live_a2_reconnect,
)
from decision_os.companion.field_notes_model import compile_draft
from decision_os.companion.field_notes_reuse import FieldNoteIdentity
from decision_os.companion.field_notes_whole_flow import (
    FieldNoteCreatorLiveAttempt,
    FieldNoteSourceRepositoryIdentity,
    FieldNoteWholeFlowRunIdentity,
)
from tests.test_acceleration_codex_adapter import (
    FakeTransportFactory,
    completed_agent_message,
    completed_turn,
    handshake_messages,
)


RUN_1_TASK = "Create one bounded fixture candidate."
RUN_1_TASK_SHA256 = hashlib.sha256(RUN_1_TASK.encode("utf-8")).hexdigest()


def _proposal(*, title: str = "Exact lineage reconnect") -> dict[str, object]:
    return {
        "title": title,
        "value_level": 1,
        "source_model_class": "UNKNOWN",
        "target_model_class": "UNKNOWN",
        "trigger_terms": ["never matching", "fixture only"],
        "scope": {
            "task_family": "creator-live-a2-exact-reconnect",
            "path_prefixes": ["decision_os/companion"],
            "exclude_terms": [],
        },
        "body": {
            "trigger": "Use only for the exact durable lineage.",
            "reusable_structure": "Keep the captured Note identity exact.",
            "scope": "One proof attempt and its distinct Run 2.",
            "do_not_apply_when": "Any target field differs.",
            "procedure": "Validate and inject exactly one Note envelope.",
            "acceptance": "The existing A2 admission accepts the receipt.",
            "evidence": "Deterministic model-free fixture evidence.",
            "remaining_unknowns": "No live proof claim is made.",
        },
    }


def _create_repository(root: Path) -> Path:
    repository = root / "repo"
    repository.mkdir()
    (repository / "seed.txt").write_text("seed\n", encoding="utf-8")
    commands = (
        ("git", "init", "-q", str(repository)),
        ("git", "-C", str(repository), "add", "seed.txt"),
        (
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=Field Notes Test",
            "-c",
            "user.email=field-notes@example.invalid",
            "commit",
            "-qm",
            "seed",
        ),
    )
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise AssertionError(result.stderr)
    return repository


def _runtime_identity() -> CodexRuntimeIdentity:
    return CodexRuntimeIdentity(
        model=codex.CODEX_MODEL,
        reasoning_effort=codex.CODEX_REASONING_EFFORT,
        service_tier=codex.CODEX_SERVICE_TIER,
        codex_cli_version=codex.CODEX_CLI_VERSION,
        account_type="chatgpt",
    )


def _reissue(
    target: FieldNoteCreatorLiveA2ReconnectTarget,
    **changes: object,
) -> FieldNoteCreatorLiveA2ReconnectTarget:
    values = {
        "proof_attempt_id": target.proof_attempt_id,
        "run_1_id": target.run_1_id,
        "run_2_id": target.run_2_id,
        "field_note_id": target.field_note_id,
        "note_relative_path": target.note_relative_path,
        "note_sha256": target.note_sha256,
        "note_byte_count": target.note_byte_count,
        "source_repository_id": target.source_repository_id,
        "source_commit": target.source_commit,
        "expected_runtime_identity": target.expected_runtime_identity,
    }
    values.update(changes)
    return FieldNoteCreatorLiveA2ReconnectTarget._issue(
        authority=exact_a2._A2_TARGET_AUTHORITY,
        **values,
    )


class _BridgeAdapter:
    def __init__(self, owner: "CreatorLiveExactReconnectTests") -> None:
        self.owner = owner

    async def run(self, task: str) -> FieldNoteCodexRunResult:
        self.owner.adapter_invocations += 1
        target = self.owner.controller._active_creator_live_a2_reconnect()
        assert target is not None
        prepared = prepare_creator_live_a2_reconnect(
            self.owner.repository,
            target,
        )
        plan = prepared.plan.injected().finalized(
            normal_terminal=True,
            ordinary_paths=0,
        )
        return FieldNoteCodexRunResult(
            run_id=target.run_2_id,
            normal_terminal=True,
            status="NORMAL_TERMINAL",
            error_type=None,
            turn_status="completed",
            runtime_identity=target.expected_runtime_identity,
            checkpoint_outcomes=(),
            final_message="bounded model-free fixture",
            reconnect_receipt=plan.receipt,
        )


class CreatorLiveExactReconnectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repository = _create_repository(self.root)
        self.source_repository = FieldNoteSourceRepositoryIdentity(
            repository_id=repository_id(self.repository),
            source_commit=git_output(self.repository, "rev-parse", "HEAD"),
        )
        self.attempt = FieldNoteCreatorLiveAttempt(
            proof_attempt_id="proof_a7_exact_reconnect_fixture_001",
            proof_mode="CREATOR_LIVE",
            creator_id="fixture-creator",
            authorization_observed_at="2026-08-06T09:58:00Z",
        )
        exact_runtime = _runtime_identity()
        terminal_clock = patch.object(
            creator_live,
            "_utc_now_rfc3339",
            return_value="2026-08-06T12:00:00Z",
        )
        terminal_clock.start()
        self.addCleanup(terminal_clock.stop)
        with patch.object(
            creator_live,
            "_utc_now_rfc3339",
            side_effect=(
                "2026-08-06T09:59:00Z",
                "2026-08-06T10:00:00Z",
            ),
        ):
            self.runtime = FieldNoteCreatorLiveProofRuntime.open_attempt(
                self.root / "runtime",
                attempt=self.attempt,
                source_repository=self.source_repository,
                run_1_id="run_exact_reconnect_fixture_1",
                runtime=exact_runtime,
            )
        self.run_1 = self.runtime.read_back().run_1
        self.run_2 = FieldNoteWholeFlowRunIdentity(
            proof_attempt_id=self.attempt.proof_attempt_id,
            run_id="run_exact_reconnect_fixture_2",
            started_at="2026-08-06T11:00:00Z",
            repository=self.source_repository,
            runtime=self.run_1.runtime,
        )
        self.draft = compile_draft(
            _proposal(),
            source_run_id=self.run_1.run_id,
            created_at="2026-08-06T10:01:00Z",
            field_note_id="fn_exact_reconnect_fixture_001",
        )
        self.note_path = self.repository / self.draft.relative_path
        self.note_path.parent.mkdir(parents=True)
        self.note_path.write_bytes(self.draft.markdown)
        note = FieldNoteIdentity(
            note_path=self.draft.relative_path,
            field_note_id=self.draft.field_note_id,
            note_sha256=self.draft.sha256,
            origin_run_id=self.draft.source_run_id,
        )
        commit = FieldNoteCreatorLiveA1CaptureCommitReceipt._issue(
            authority=creator_live._A1_CAPTURE_COMMIT_AUTHORITY,
            proof_attempt_id=self.attempt.proof_attempt_id,
            run_id=self.run_1.run_id,
            task_sha256=RUN_1_TASK_SHA256,
            actual_runtime_identity=self.run_1.runtime,
            source_repository=self.source_repository,
            note=note,
            note_byte_count=len(self.draft.markdown),
            draft_evidence_sha256=whole_flow._a1_evidence_sha256(self.draft),
            draft_created_at=self.draft.created_at,
            save_as_of="2026-08-06T10:02:00Z",
        )
        self.runtime.record_a1_capture(
            self.draft,
            capture_commit=commit,
            expected_task_sha256=RUN_1_TASK_SHA256,
            actual_runtime_identity=self.run_1.runtime,
            observed_at="2026-08-06T10:03:00Z",
        )
        self.runtime.open_run_2(self.run_2)
        self.target = creator_live_a2_target_from_readback(
            self.runtime.read_back()
        )
        self.adapter_invocations = 0
        self.controller = FieldNotesCompanionController(
            state_path=self.root / "state.json",
            picker_script=self.root / "picker.scpt",
            adapter_factory=lambda _engine, _approval, _lifecycle: (
                _BridgeAdapter(self)
            ),
        )
        self.controller.select_repository(self.repository)

    def _bridge(self) -> FieldNoteCreatorLiveA2ReconnectBridge:
        return FieldNoteCreatorLiveA2ReconnectBridge(
            runtime=self.runtime,
            controller=self.controller,
            repository=self.repository,
            source_repository=self.source_repository,
            timeout_seconds=5,
        )

    @staticmethod
    def _terminal_messages(repository: Path) -> list[dict[str, object]]:
        messages = handshake_messages(
            repository,
            thread_id="thread-exact-a2",
            turn_id="turn-exact-a2",
        )
        messages.extend(
            [
                completed_agent_message(
                    thread_id="thread-exact-a2",
                    turn_id="turn-exact-a2",
                    text="Completed.",
                ),
                completed_turn(
                    thread_id="thread-exact-a2",
                    turn_id="turn-exact-a2",
                ),
            ]
        )
        return messages

    def _adapter(
        self,
        target: FieldNoteCreatorLiveA2ReconnectTarget,
        factory: object,
        *,
        a1: bool = False,
    ) -> FieldNotesCodexAdapter:
        engine = AccelerationEngine(
            self.repository,
            adapter=ADAPTER_NAME,
            adapter_version=CODEX_CLI_VERSION,
        )
        return FieldNotesCodexAdapter(
            engine,
            input_func=lambda: None,
            stdout=io.StringIO(),
            transport_factory=factory,
            creator_live_a1_capture_provider=(
                lambda: FieldNoteCreatorLiveA1CaptureConfig(
                    run_id=self.run_1.run_id,
                    expected_runtime_identity=self.run_1.runtime,
                )
                if a1
                else None
            ),
            creator_live_a2_reconnect_provider=lambda: target,
        )

    def test_target_is_issued_only_from_verified_post_run_2_readback(self) -> None:
        with self.assertRaisesRegex(
            FieldNoteCreatorLiveA2ReconnectError,
            "A2_TARGET_INVALID",
        ):
            FieldNoteCreatorLiveA2ReconnectTarget()
        self.assertEqual(self.attempt.proof_attempt_id, self.target.proof_attempt_id)
        self.assertEqual(self.run_1.run_id, self.target.run_1_id)
        self.assertEqual(self.run_2.run_id, self.target.run_2_id)
        self.assertEqual(self.draft.relative_path, self.target.note_relative_path)

    def test_exact_preparation_is_score_free_and_never_selects_alternate(self) -> None:
        alternate = compile_draft(
            _proposal(title="Higher scoring alternate"),
            source_run_id=self.run_1.run_id,
            created_at="2026-08-06T10:01:30Z",
            field_note_id="fn_exact_reconnect_alternate_001",
        )
        (self.repository / alternate.relative_path).write_bytes(alternate.markdown)
        ordinary = reconnect.prepare_field_note_reconnect(
            self.repository,
            "completely unrelated score zero task",
            self.run_2.run_id,
        )
        self.assertEqual("NO_MATCH", ordinary.receipt.state)
        with patch.object(reconnect, "_score", side_effect=AssertionError("score")):
            prepared = prepare_creator_live_a2_reconnect(
                self.repository,
                self.target,
            )
        self.assertEqual("SELECTED", prepared.plan.receipt.state)
        self.assertEqual(
            self.draft.field_note_id,
            prepared.plan.receipt.selected_field_note_id,
        )
        self.assertNotEqual(
            alternate.field_note_id,
            prepared.plan.receipt.selected_field_note_id,
        )

    def test_exact_selected_receipt_contains_all_existing_identity_fields(self) -> None:
        prepared = prepare_creator_live_a2_reconnect(
            self.repository,
            self.target,
        )
        receipt = prepared.plan.receipt
        self.assertEqual("SELECTED", receipt.state)
        self.assertEqual(self.run_2.run_id, receipt.run_id)
        self.assertEqual(self.draft.relative_path, receipt.selected_field_note_path)
        self.assertEqual(self.draft.field_note_id, receipt.selected_field_note_id)
        self.assertEqual(self.draft.sha256, receipt.selected_full_note_sha256)
        self.assertEqual(len(self.draft.markdown), receipt.full_note_bytes_read)
        self.assertEqual(0, receipt.full_notes_injected)
        self.assertEqual(self.draft.markdown, prepared.note_bytes)

    def test_exact_identity_mismatch_matrix_fails_closed(self) -> None:
        cases = {
            "note_id": (
                {"field_note_id": "fn_different"},
                "A2_TARGET_NOTE_ID_MISMATCH",
            ),
            "traversal": (
                {"note_relative_path": "../alternate.md"},
                "A2_TARGET_PATH_INVALID",
            ),
            "source_run": (
                {"run_1_id": "run_different"},
                "A2_TARGET_SOURCE_RUN_MISMATCH",
            ),
            "repository": (
                {"source_repository_id": "repo:v1:" + "0" * 64},
                "A2_TARGET_REPOSITORY_MISMATCH",
            ),
            "commit": (
                {"source_commit": "0" * 40},
                "A2_TARGET_COMMIT_MISMATCH",
            ),
            "sha": (
                {"note_sha256": "0" * 64},
                "A2_TARGET_SHA256_MISMATCH",
            ),
            "bytes": (
                {"note_byte_count": self.target.note_byte_count + 1},
                "A2_TARGET_BYTE_COUNT_MISMATCH",
            ),
        }
        for label, (changes, code) in cases.items():
            with self.subTest(label=label):
                target = _reissue(self.target, **changes)
                with self.assertRaisesRegex(
                    FieldNoteCreatorLiveA2ReconnectError,
                    code,
                ):
                    prepare_creator_live_a2_reconnect(self.repository, target)

    def test_missing_symlink_changed_and_invalid_notes_fail_closed(self) -> None:
        original = self.note_path.read_bytes()
        cases = (
            "missing",
            "symlink",
            "replaced",
            "changed",
            "invalid_metadata",
            "invalid_full",
        )
        for case in cases:
            with self.subTest(case=case):
                if self.note_path.exists() or self.note_path.is_symlink():
                    self.note_path.unlink()
                self.note_path.write_bytes(original)
                if case == "missing":
                    self.note_path.unlink()
                elif case == "symlink":
                    alternate = self.root / "outside.md"
                    alternate.write_bytes(original)
                    self.note_path.unlink()
                    self.note_path.symlink_to(alternate)
                elif case == "replaced":
                    replacement = compile_draft(
                        _proposal(title="Replacement note"),
                        source_run_id=self.run_1.run_id,
                        created_at="2026-08-06T10:01:30Z",
                        field_note_id="fn_replacement_note_001",
                    )
                    self.note_path.write_bytes(replacement.markdown)
                elif case == "invalid_metadata":
                    self.note_path.write_bytes(
                        original.replace(
                            b'"status":"CANDIDATE"',
                            b'"status":"BROKEN"',
                        )
                    )
                elif case == "invalid_full":
                    self.note_path.write_bytes(original + b"\x00")
                if case == "changed":
                    with patch.object(
                        reconnect,
                        "_read_full_note",
                        return_value=(
                            None,
                            10,
                            "selected_identity_changed",
                        ),
                    ):
                        with self.assertRaisesRegex(
                            FieldNoteCreatorLiveA2ReconnectError,
                            "A2_TARGET_CHANGED_DURING_READ",
                        ):
                            prepare_creator_live_a2_reconnect(
                                self.repository,
                                self.target,
                            )
                else:
                    with self.assertRaises(FieldNoteCreatorLiveA2ReconnectError):
                        prepare_creator_live_a2_reconnect(
                            self.repository,
                            self.target,
                        )

    async def _run_exact_adapter(self) -> tuple[object, FakeTransportFactory]:
        factory = FakeTransportFactory(
            [self._terminal_messages(self.repository)]
        )
        adapter = self._adapter(self.target, factory)
        result = await adapter.run("completely unrelated score zero task")
        return result, factory

    def test_successful_bridge_admits_existing_receipt_and_opens_a3(self) -> None:
        event = self._bridge().reconnect("fixed Run 2 task")
        readback = self.runtime.read_back()
        self.assertEqual("A2_RECONNECT", event.stage)
        self.assertEqual("OPEN", readback.state)
        self.assertEqual("A3_REUSE", readback.current_stage)
        self.assertEqual(2, readback.trace_event_count)
        self.assertEqual(1, self.adapter_invocations)
        completion = self.controller.creator_live_a2_run_completion(
            expected_run_id=self.run_2.run_id
        )
        self.assertIn(
            completion.reconnect_receipt.state,
            {"INJECTED", "ACTIVATION_UNKNOWN"},
        )
        self.assertEqual(1, completion.reconnect_receipt.full_notes_injected)

    def _assert_cross_bound_terminal(
        self,
        target: FieldNoteCreatorLiveA2ReconnectTarget,
        code: str,
    ) -> None:
        with patch.object(
            exact_a2,
            "creator_live_a2_target_from_readback",
            return_value=target,
        ):
            with self.assertRaisesRegex(
                FieldNoteCreatorLiveA2ReconnectError,
                code,
            ):
                self._bridge().reconnect("fixed Run 2 task")
        readback = self.runtime.read_back()
        self.assertEqual("FAILED", readback.state)
        self.assertEqual("A2_RECONNECT", readback.failure_boundary)
        self.assertEqual(code, readback.failure_reason)
        self.assertEqual(1, readback.trace_event_count)
        self.assertEqual(0, self.adapter_invocations)

    def test_cross_bound_proof_fails_before_adapter_and_terminalizes(self) -> None:
        self._assert_cross_bound_terminal(
            _reissue(self.target, proof_attempt_id="proof_different"),
            "A2_TARGET_PROOF_MISMATCH",
        )

    def test_cross_bound_run_2_fails_before_adapter_and_terminalizes(self) -> None:
        self._assert_cross_bound_terminal(
            _reissue(self.target, run_2_id="run_different"),
            "A2_TARGET_RUN_2_MISMATCH",
        )

    def test_pre_thread_failure_constructs_no_transport(self) -> None:
        calls = 0

        def factory(_executable: Path):
            nonlocal calls
            calls += 1
            raise AssertionError("transport must not be constructed")

        adapter = self._adapter(
            _reissue(self.target, note_sha256="0" * 64),
            factory,
        )

        async def invoke() -> None:
            await adapter.run("fixed Run 2 task")

        with self.assertRaisesRegex(
            FieldNoteCreatorLiveA2ReconnectError,
            "A2_TARGET_SHA256_MISMATCH",
        ):
            import asyncio

            asyncio.run(invoke())
        self.assertEqual(0, calls)

    def test_bridge_file_failure_is_durable_with_zero_transport(
        self,
    ) -> None:
        calls = 0
        holder: dict[str, FieldNotesCompanionController] = {}

        def transport_factory(_executable: Path):
            nonlocal calls
            calls += 1
            raise AssertionError("transport must not be constructed")

        def adapter_factory(engine, approval, lifecycle):
            return FieldNotesCodexAdapter(
                engine,
                input_func=lambda: None,
                stdout=io.StringIO(),
                approval_provider=approval,
                lifecycle_sink=lifecycle,
                transport_factory=transport_factory,
                creator_live_a2_reconnect_provider=(
                    holder["controller"]._active_creator_live_a2_reconnect
                ),
            )

        controller = FieldNotesCompanionController(
            state_path=self.root / "failure-state.json",
            picker_script=self.root / "failure-picker.scpt",
            adapter_factory=adapter_factory,
        )
        holder["controller"] = controller
        controller.select_repository(self.repository)
        self.note_path.unlink()
        bridge = FieldNoteCreatorLiveA2ReconnectBridge(
            runtime=self.runtime,
            controller=controller,
            repository=self.repository,
            source_repository=self.source_repository,
            timeout_seconds=5,
        )
        with self.assertRaisesRegex(
            FieldNoteCreatorLiveA2ReconnectError,
            "A2_TARGET_NOTE_MISSING",
        ):
            bridge.reconnect("fixed Run 2 task")
        readback = self.runtime.read_back()
        self.assertEqual(0, calls)
        self.assertEqual("FAILED", readback.state)
        self.assertEqual("A2_RECONNECT", readback.failure_boundary)
        self.assertEqual("A2_TARGET_NOTE_MISSING", readback.failure_reason)
        self.assertEqual(1, readback.trace_event_count)

    def test_a1_and_a2_modes_are_mutually_exclusive_before_transport(self) -> None:
        calls = 0

        def factory(_executable: Path):
            nonlocal calls
            calls += 1
            raise AssertionError("transport must not be constructed")

        adapter = self._adapter(self.target, factory, a1=True)

        async def invoke() -> None:
            await adapter.run("fixed Run task")

        with self.assertRaisesRegex(
            FieldNoteCreatorLiveA2ReconnectError,
            "A2_TARGET_INVALID",
        ):
            import asyncio

            asyncio.run(invoke())
        self.assertEqual(0, calls)


class CreatorLiveExactReconnectAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_thread_injects_exact_envelope_once(self) -> None:
        case = CreatorLiveExactReconnectTests("runTest")
        case.setUp()
        self.addCleanup(case.doCleanups)
        result, factory = await case._run_exact_adapter()
        self.assertEqual("ACTIVATION_UNKNOWN", result.reconnect_receipt.state)
        self.assertEqual(1, result.reconnect_receipt.full_notes_injected)
        request = next(
            item
            for item in factory.transports[0].sent
            if item.get("method") == "thread/start"
        )
        instructions = request["params"]["developerInstructions"]
        self.assertEqual(1, instructions.count(case.draft.markdown.decode("utf-8")))
        self.assertEqual(
            1,
            instructions.count(
                "=== DECISION OS FIELD NOTE / ADVISORY MEMORY / BEGIN ==="
            ),
        )


if __name__ == "__main__":
    unittest.main()
