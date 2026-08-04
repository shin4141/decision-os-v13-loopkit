from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from decision_os.acceleration.codex_adapter import (
    CodexApproval,
    CodexFileAction,
    CodexReadEvidence,
    CodexRuntimeIdentity,
)
from decision_os.acceleration.model import git_output, repository_id
from decision_os.companion.field_notes_adapter import FieldNoteCodexRunResult
from decision_os.companion.field_notes_controller import (
    FieldNotesCompanionController,
)
from decision_os.companion.field_notes_creator_live import (
    FieldNoteCreatorLiveA1CaptureCommitReceipt,
    FieldNoteCreatorLiveProofRuntime,
    FieldNoteCreatorLiveStageError,
    FieldNoteCreatorLiveValidationError,
)
from decision_os.companion.field_notes_creator_live_capture import (
    FieldNoteCreatorLiveA1CaptureBridge,
    FieldNoteCreatorLiveA1CaptureBridgeError,
)
from decision_os.companion.field_notes_model import FieldNoteDraft, compile_draft
from decision_os.companion.field_notes_whole_flow import (
    FieldNoteSourceRepositoryIdentity,
    FieldNoteWholeFlowAttempt,
    FieldNoteWholeFlowRunIdentity,
)


FAILED_LIVE_ATTEMPT = "proof_a7_creator_live_001_59a75977337edbec"


def proposal() -> dict[str, object]:
    return {
        "title": "Creator Live A1 Capture Bridge",
        "value_level": 1,
        "source_model_class": "UNKNOWN",
        "target_model_class": "UNKNOWN",
        "trigger_terms": ["creator live", "capture bridge"],
        "scope": {
            "task_family": "creator-live-a1-capture",
            "path_prefixes": ["decision_os/companion"],
            "exclude_terms": ["direct write"],
        },
        "body": {
            "trigger": "Use when Run 1 identifies a bounded reusable structure.",
            "reusable_structure": "Route capture through one typed proposal.",
            "scope": "One already-open creator-live attempt and one Run 1.",
            "do_not_apply_when": "Any direct repository write was requested.",
            "procedure": "Propose once, approve once, save, and read back.",
            "acceptance": "The exact Note bytes and identities agree.",
            "evidence": "A typed proposal and controller save confirmation.",
            "remaining_unknowns": "No creator-live proof is executed by tests.",
        },
    }


def create_repository(root: Path) -> Path:
    repository = root / "repo"
    repository.mkdir()
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
    (repository / "seed.txt").write_text("seed\n", encoding="utf-8")
    for command in commands:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr)
    return repository


class _CaptureAdapter:
    def __init__(
        self,
        owner: "CreatorLiveCaptureBridgeTests",
        approval_provider,
    ) -> None:
        self.owner = owner
        self.approval_provider = approval_provider

    async def run(self, task: str) -> FieldNoteCodexRunResult:
        config = self.owner.controller._active_creator_live_a1_capture()
        assert config is not None
        self.owner.observed_task = task
        draft = compile_draft(
            proposal(),
            source_run_id=(
                "different-origin"
                if self.owner.mode == "origin_mismatch"
                else config.run_id
            ),
            created_at="2026-08-06T01:01:00Z",
            field_note_id="fn_creator_live_capture_bridge_test",
        )
        if self.owner.mode == "outside_root":
            draft = replace(draft, relative_path="field_notes/direct.md")
        self.owner.last_draft = draft
        if self.owner.mode.startswith("direct_"):
            action = self.owner.mode.removeprefix("direct_")
            proposal_after_direct_request = None
            if action.startswith("valid_"):
                action = action.removeprefix("valid_")
                proposal_after_direct_request = draft
            decision = self.approval_provider(
                CodexApproval(
                    repository_name=self.owner.repository.name,
                    action=action,
                    normalized_scope="field_notes/direct.md",
                    diff="bounded direct-write request",
                    reason=None,
                )
            )
            self.owner.direct_decision = decision
            return self.owner.result(
                config.run_id,
                normal_terminal=False,
                status="DENIED",
                proposal=proposal_after_direct_request,
                failure="A1_DIRECT_WRITE_REQUESTED",
                actions=(
                    CodexFileAction(
                        action=action,
                        normalized_scope="field_notes/direct.md",
                        access="denied",
                        status="denied",
                    ),
                ),
            )
        if self.owner.mode in {"missing", "raw_markdown", "raw_json"}:
            return self.owner.result(
                config.run_id,
                normal_terminal=False,
                proposal=None,
                failure="A1_PROPOSAL_MISSING",
            )
        if self.owner.mode == "duplicate":
            return self.owner.result(
                config.run_id,
                normal_terminal=False,
                proposal=None,
                failure="A1_PROPOSAL_DUPLICATE",
                attempts=2,
            )
        if self.owner.mode == "malformed":
            return self.owner.result(
                config.run_id,
                normal_terminal=False,
                proposal=None,
                failure="A1_PROPOSAL_INVALID",
            )
        return self.owner.result(config.run_id, proposal=draft)


class CreatorLiveCaptureBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repository = create_repository(self.root)
        self.source_repository = FieldNoteSourceRepositoryIdentity(
            repository_id=repository_id(self.repository),
            source_commit=git_output(self.repository, "rev-parse", "HEAD"),
        )
        self.attempt = FieldNoteWholeFlowAttempt(
            proof_attempt_id="proof_a7_capture_bridge_fixture_001",
            proof_mode="CREATOR_LIVE",
            creator_id="fixture-creator",
            proof_as_of="2026-08-06T03:00:00Z",
        )
        self.run_1 = FieldNoteWholeFlowRunIdentity(
            proof_attempt_id=self.attempt.proof_attempt_id,
            run_id="run_creator_live_capture_fixture_001",
            started_at="2026-08-06T01:00:00Z",
            repository=self.source_repository,
            runtime=CodexRuntimeIdentity(
                model="gpt-5.6-sol",
                reasoning_effort="ultra",
                service_tier="priority",
                codex_cli_version="0.146.0-alpha.3.1",
                account_type="chatgpt",
            ),
        )
        self.runtime = FieldNoteCreatorLiveProofRuntime.open_attempt(
            self.root / "fixture-runtime",
            attempt=self.attempt,
            source_repository=self.source_repository,
            run_1=self.run_1,
        )
        self.mode = "valid"
        self.last_draft: FieldNoteDraft | None = None
        self.observed_task: str | None = None
        self.direct_decision: str | None = None
        self.actual_runtime_identity: CodexRuntimeIdentity | None = (
            self.run_1.runtime
        )
        self.read_evidence: tuple[CodexReadEvidence, ...] = ()
        self.task_sha256_override: str | None = None
        self.controller = FieldNotesCompanionController(
            state_path=self.root / "state.json",
            picker_script=self.root / "picker.scpt",
            adapter_factory=lambda _engine, approval, _lifecycle: (
                _CaptureAdapter(self, approval)
            ),
        )
        self.controller.select_repository(self.repository)

    def result(
        self,
        run_id: str,
        *,
        normal_terminal: bool = True,
        status: str = "NORMAL_TERMINAL",
        proposal: FieldNoteDraft | None,
        failure: str | None = None,
        attempts: int = 1,
        actions: tuple[CodexFileAction, ...] = (),
    ) -> FieldNoteCodexRunResult:
        return FieldNoteCodexRunResult(
            run_id=run_id,
            normal_terminal=normal_terminal,
            status=status,
            error_type=None,
            turn_status="completed",
            runtime_identity=self.actual_runtime_identity,
            checkpoint_outcomes=(),
            final_message="Completed.",
            file_actions=actions,
            read_evidence=self.read_evidence,
            field_note_proposal=proposal,
            creator_live_a1_capture=True,
            creator_live_a1_failure_reason=failure,
            creator_live_a1_proposal_attempts=attempts,
            creator_live_a1_task_sha256=hashlib.sha256(
                (self.observed_task or "").encode("utf-8")
            ).hexdigest()
            if self.task_sha256_override is None
            else self.task_sha256_override,
        )

    def bridge(self) -> FieldNoteCreatorLiveA1CaptureBridge:
        return FieldNoteCreatorLiveA1CaptureBridge(
            runtime=self.runtime,
            controller=self.controller,
            repository=self.repository,
            source_repository=self.source_repository,
            timeout_seconds=5,
            utc_now=lambda: "2026-08-06T01:02:00Z",
        )

    def test_exact_save_path_closes_one_durable_a1_checkpoint(self) -> None:
        original_save = self.controller.field_note_save
        original_approval = self.controller.field_note_approval
        original_read = FieldNoteCreatorLiveA1CaptureBridge._exact_read_back

        def checked_save():
            self.assertEqual(0, self.runtime.read_back().trace_event_count)
            return original_save()

        def checked_approval(choice: str):
            self.assertEqual("allow_once", choice)
            self.assertEqual(0, self.runtime.read_back().trace_event_count)
            return original_approval(choice)

        def checked_read(target: Path):
            self.assertEqual(0, self.runtime.read_back().trace_event_count)
            return original_read(target)

        with patch.object(
            self.controller,
            "field_note_save",
            side_effect=checked_save,
        ) as save, patch.object(
            self.controller,
            "field_note_approval",
            side_effect=checked_approval,
        ) as approval, patch.object(
            FieldNoteCreatorLiveA1CaptureBridge,
            "_exact_read_back",
            side_effect=checked_read,
        ):
            event = self.bridge().capture(
                "Perform the bounded reasoning task, propose once, and stop."
            )

        self.assertEqual("A1_CAPTURE", event.stage)
        self.assertEqual(1, save.call_count)
        self.assertEqual(1, approval.call_count)
        self.assertEqual(
            "Perform the bounded reasoning task, propose once, and stop.",
            self.observed_task,
        )
        assert self.last_draft is not None
        target = self.repository / self.last_draft.relative_path
        self.assertEqual(self.last_draft.markdown, target.read_bytes())
        self.assertEqual(
            (".decision-os", "field-notes"),
            Path(self.last_draft.relative_path).parts[:2],
        )
        readback = self.runtime.read_back()
        self.assertEqual("OPEN", readback.state)
        self.assertEqual("A2_RECONNECT", readback.current_stage)
        self.assertEqual(1, readback.trace_event_count)
        self.assertIsNotNone(readback.a1_capture_commit)
        completion = self.controller.creator_live_a1_run_completion()
        self.assertEqual(self.run_1.runtime, completion.actual_runtime_identity)
        self.assertEqual(0, completion.successful_read_count)
        assert readback.a1_capture_commit is not None
        self.assertEqual(
            readback.a1_capture_commit.receipt_sha256,
            event.evidence_sha256,
        )
        self.assertEqual(
            hashlib.sha256(
                self.observed_task.encode("utf-8")
            ).hexdigest(),
            readback.a1_capture_commit.task_sha256,
        )

    def test_one_exact_successful_read_is_optional_completion_evidence(self) -> None:
        self.read_evidence = (
            CodexReadEvidence(
                path="seed.txt",
                byte_count=5,
                sha256=hashlib.sha256(b"seed\n").hexdigest(),
                repository_identity=self.source_repository.repository_id,
                status="succeeded",
            ),
        )
        self.bridge().capture("Propose exactly once after one bounded read.")
        completion = self.controller.creator_live_a1_run_completion()
        self.assertEqual(1, completion.successful_read_count)

    def test_failed_read_is_terminal_and_creates_no_note(self) -> None:
        self.read_evidence = (
            CodexReadEvidence(
                path="missing.txt",
                byte_count=None,
                sha256=None,
                repository_identity=self.source_repository.repository_id,
                status="failed",
                reason="read_path_not_found",
            ),
        )
        with patch.object(self.controller, "field_note_save") as save:
            with self.assertRaises(FieldNoteCreatorLiveA1CaptureBridgeError):
                self.bridge().capture("Propose exactly once after a read.")
        self.assertEqual(0, save.call_count)
        readback = self.runtime.read_back()
        self.assertEqual("A1_READ_EVIDENCE_FAILED", readback.failure_reason)
        self.assertEqual(0, readback.trace_event_count)
        assert self.last_draft is not None
        self.assertFalse(
            (self.repository / self.last_draft.relative_path).exists()
        )

    def test_successful_read_cannot_replace_missing_or_malformed_proposal(self) -> None:
        for mode in ("missing", "malformed"):
            with self.subTest(mode=mode):
                self.setUp()
                self.mode = mode
                self.read_evidence = (
                    CodexReadEvidence(
                        path="seed.txt",
                        byte_count=5,
                        sha256=hashlib.sha256(b"seed\n").hexdigest(),
                        repository_identity=(
                            self.source_repository.repository_id
                        ),
                        status="succeeded",
                    ),
                )
                with self.assertRaises(
                    FieldNoteCreatorLiveA1CaptureBridgeError
                ):
                    self.bridge().capture("Propose exactly once and stop.")
                self.assertEqual(0, self.runtime.read_back().trace_event_count)

    def test_missing_and_each_changed_runtime_field_fail_before_save(self) -> None:
        cases = {
            "missing": None,
            "model": replace(self.run_1.runtime, model="other-model"),
            "reasoning_effort": replace(
                self.run_1.runtime,
                reasoning_effort="high",
            ),
            "service_tier": replace(
                self.run_1.runtime,
                service_tier="default",
            ),
            "codex_cli_version": replace(
                self.run_1.runtime,
                codex_cli_version="0.0.0",
            ),
            "account_type": replace(
                self.run_1.runtime,
                account_type="api",
            ),
        }
        for label, actual in cases.items():
            with self.subTest(field=label):
                self.setUp()
                self.actual_runtime_identity = actual
                with patch.object(self.controller, "field_note_save") as save:
                    with self.assertRaises(
                        FieldNoteCreatorLiveA1CaptureBridgeError
                    ):
                        self.bridge().capture("Propose exactly once and stop.")
                self.assertEqual(0, save.call_count)
                readback = self.runtime.read_back()
                self.assertEqual(
                    "A1_ACTUAL_RUNTIME_IDENTITY_MISSING"
                    if label == "missing"
                    else "A1_ACTUAL_RUNTIME_IDENTITY_MISMATCH",
                    readback.failure_reason,
                )
                self.assertEqual(0, readback.trace_event_count)
                assert self.last_draft is not None
                self.assertFalse(
                    (self.repository / self.last_draft.relative_path).exists()
                )

    def test_changed_task_identity_fails_before_save(self) -> None:
        self.task_sha256_override = "f" * 64
        with patch.object(self.controller, "field_note_save") as save:
            with self.assertRaises(FieldNoteCreatorLiveA1CaptureBridgeError):
                self.bridge().capture("Propose exactly once and stop.")
        self.assertEqual(0, save.call_count)
        self.assertEqual(
            "A1_TASK_IDENTITY_MISMATCH",
            self.runtime.read_back().failure_reason,
        )

    def test_full_note_body_is_absent_from_journal_and_anchor(self) -> None:
        self.bridge().capture("Propose exactly once and stop.")
        assert self.last_draft is not None
        for path in (self.runtime.journal_path, self.runtime.anchor_path):
            raw = path.read_bytes()
            self.assertNotIn(self.last_draft.markdown, raw)
            self.assertNotIn(
                b"Route capture through one typed proposal.",
                raw,
            )

    def test_missing_duplicate_malformed_and_raw_outputs_fail_closed(self) -> None:
        for mode in (
            "missing",
            "duplicate",
            "malformed",
            "raw_markdown",
            "raw_json",
        ):
            with self.subTest(mode=mode):
                self.setUp()
                self.mode = mode
                with self.assertRaises(
                    FieldNoteCreatorLiveA1CaptureBridgeError
                ):
                    self.bridge().capture("Propose exactly once and stop.")
                readback = self.runtime.read_back()
                self.assertEqual("FAILED", readback.state)
                self.assertEqual("A1_CAPTURE", readback.failure_boundary)
                self.assertEqual(0, readback.trace_event_count)

    def test_direct_create_update_delete_are_denied_and_terminal(self) -> None:
        for action in ("Create", "Update", "Delete"):
            with self.subTest(action=action):
                self.setUp()
                self.mode = f"direct_{action}"
                with self.assertRaises(
                    FieldNoteCreatorLiveA1CaptureBridgeError
                ):
                    self.bridge().capture("Propose; do not write.")
                self.assertEqual("3", self.direct_decision)
                readback = self.runtime.read_back()
                self.assertEqual("FAILED", readback.state)
                self.assertTrue(
                    readback.failure_reason.startswith(
                        "A1_DIRECT_WRITE_REQUESTED:"
                    )
                )
                self.assertFalse(
                    (self.repository / "field_notes" / "direct.md").exists()
                )
                with self.assertRaises(FieldNoteCreatorLiveStageError):
                    self.runtime.open_run_2(self.run_1)

    def test_direct_write_request_fails_even_with_valid_proposal(self) -> None:
        self.mode = "direct_valid_Create"
        with self.assertRaises(FieldNoteCreatorLiveA1CaptureBridgeError):
            self.bridge().capture("Propose once and do not write.")
        readback = self.runtime.read_back()
        self.assertTrue(
            readback.failure_reason.startswith("A1_DIRECT_WRITE_REQUESTED:")
        )
        self.assertEqual(0, readback.trace_event_count)

    def test_outside_root_origin_mismatch_and_existing_target_fail(self) -> None:
        for mode in ("outside_root", "origin_mismatch", "preexisting"):
            with self.subTest(mode=mode):
                self.setUp()
                self.mode = "valid" if mode == "preexisting" else mode
                if mode == "preexisting":
                    draft = compile_draft(
                        proposal(),
                        source_run_id=self.run_1.run_id,
                        created_at="2026-08-06T01:01:00Z",
                        field_note_id="fn_creator_live_capture_bridge_test",
                    )
                    target = self.repository / draft.relative_path
                    target.parent.mkdir(parents=True)
                    target.write_bytes(b"preexisting fixture\n")
                with self.assertRaises(
                    FieldNoteCreatorLiveA1CaptureBridgeError
                ):
                    self.bridge().capture("Propose exactly once and stop.")
                self.assertEqual("FAILED", self.runtime.read_back().state)
                self.assertEqual(0, self.runtime.read_back().trace_event_count)

    def test_parent_symlink_and_case_collision_fail_closed(self) -> None:
        for mode in ("symlink", "collision"):
            with self.subTest(mode=mode):
                self.setUp()
                draft = compile_draft(
                    proposal(),
                    source_run_id=self.run_1.run_id,
                    created_at="2026-08-06T01:01:00Z",
                    field_note_id="fn_creator_live_capture_bridge_test",
                )
                if mode == "symlink":
                    external = self.root / "external"
                    external.mkdir()
                    (self.repository / ".decision-os").symlink_to(
                        external,
                        target_is_directory=True,
                    )
                else:
                    target = self.repository / draft.relative_path
                    target.parent.mkdir(parents=True)
                    (target.parent / target.name.upper()).write_bytes(
                        b"collision fixture\n"
                    )
                with self.assertRaises(
                    FieldNoteCreatorLiveA1CaptureBridgeError
                ):
                    self.bridge().capture("Propose exactly once and stop.")
                self.assertEqual("FAILED", self.runtime.read_back().state)

    def test_changed_readback_and_repository_identity_fail_closed(self) -> None:
        for mode in ("bytes", "repository"):
            with self.subTest(mode=mode):
                self.setUp()
                bridge = self.bridge()
                if mode == "bytes":
                    context = patch.object(
                        bridge,
                        "_exact_read_back",
                        return_value=b"changed bytes",
                    )
                else:
                    context = patch.object(
                        bridge,
                        "_repository_identity_matches",
                        side_effect=(True, True, False),
                    )
                with context, self.assertRaises(
                    FieldNoteCreatorLiveA1CaptureBridgeError
                ):
                    bridge.capture("Propose exactly once and stop.")
                self.assertEqual("FAILED", self.runtime.read_back().state)
                self.assertEqual(0, self.runtime.read_back().trace_event_count)

    def test_capture_commit_cannot_be_caller_constructed(self) -> None:
        with self.assertRaises(FieldNoteCreatorLiveValidationError):
            FieldNoteCreatorLiveA1CaptureCommitReceipt()

    def test_fixture_never_uses_closed_live_attempt_or_real_repository(self) -> None:
        self.assertNotEqual(FAILED_LIVE_ATTEMPT, self.attempt.proof_attempt_id)
        self.assertTrue(self.repository.is_relative_to(self.root))
        self.assertTrue(self.runtime.journal_path.is_relative_to(self.root))


if __name__ == "__main__":
    unittest.main()
