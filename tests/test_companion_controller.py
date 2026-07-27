from __future__ import annotations

from collections import deque
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time
import unittest
from typing import Any

from decision_os.acceleration.codex_adapter import (
    CODEX_CLI_VERSION,
    CODEX_MODEL,
    CODEX_REASONING_EFFORT,
    CODEX_SERVICE_TIER,
    CodexAdapterFailure,
    CodexApproval,
    CodexFileAction,
    CodexLifecycleEvent,
    CodexRunResult,
    CodexRuntimeIdentity,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import DecisionType
from decision_os.companion.controller import (
    ApprovalStateError,
    CompanionController,
    CompanionStateError,
    RepositorySelectionError,
    RunConflictError,
)


def create_repository(parent: Path, name: str = "repo") -> Path:
    repository = parent / name
    repository.mkdir()
    completed = subprocess.run(
        ("git", "init", "-q", str(repository)),
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    (repository / "target.txt").write_text("before\n", encoding="utf-8")
    return repository


def runtime_identity() -> CodexRuntimeIdentity:
    return CodexRuntimeIdentity(
        model=CODEX_MODEL,
        reasoning_effort=CODEX_REASONING_EFFORT,
        service_tier=CODEX_SERVICE_TIER,
        codex_cli_version=CODEX_CLI_VERSION,
        account_type="chatgpt",
    )


class ScriptedAdapter:
    def __init__(
        self,
        engine: AccelerationEngine,
        approval_provider: Any,
        lifecycle_sink: Any,
        mode: str,
    ) -> None:
        self.engine = engine
        self.approval_provider = approval_provider
        self.lifecycle_sink = lifecycle_sink
        self.mode = mode

    async def run(self, prompt: str) -> CodexRunResult:
        del prompt
        self.lifecycle_sink(
            CodexLifecycleEvent("runtime", "Starting the private Codex runtime.")
        )
        if self.mode == "malformed":
            self.lifecycle_sink({"kind": "raw", "message": "<script>"})
        if self.mode == "failure":
            raise CodexAdapterFailure("sensitive raw adapter failure")
        if self.mode == "read_only":
            return CodexRunResult(
                run_id=self.engine.new_run_id(),
                normal_terminal=True,
                status="NORMAL_TERMINAL",
                error_type=None,
                turn_status="completed",
                runtime_identity=runtime_identity(),
                checkpoint_outcomes=(),
                final_message="Read-only result.",
            )

        run_id = self.engine.new_run_id()
        outcome = self.engine.evaluate(
            run_id=run_id,
            iteration=1,
            decision_type=DecisionType.MODIFY_FILE,
            requested_scope="target.txt",
            source_interrupt_id="private-test-item",
            choice_provider=lambda identity: self.approval_provider(
                CodexApproval(
                    repository_name=self.engine.store.repository.name,
                    action="Modify",
                    normalized_scope=identity.normalized_scope,
                    diff=(
                        "--- a/target.txt\n"
                        "+++ b/target.txt\n"
                        "@@\n-before\n+after\n"
                    ),
                    reason="Apply the bounded update.",
                )
            ),
        )
        if not outcome.allowed:
            return CodexRunResult(
                run_id=run_id,
                normal_terminal=False,
                status="DENIED",
                error_type=None,
                turn_status="completed",
                runtime_identity=runtime_identity(),
                checkpoint_outcomes=(),
                final_message="The change was denied.",
                file_actions=(
                    CodexFileAction(
                        "Modify",
                        "target.txt",
                        "denied",
                        "denied",
                    ),
                ),
            )
        checkpoint = self.engine.finish_checkpoint(
            outcome,
            normal_terminal=True,
            checkpoint_id=f"companion-test:{run_id}",
        )
        access = {
            "ALLOW_ONCE": "one-time",
            "HUMAN_DEFAULT_CREATED": "newly-saved",
            "DEFAULT_MATCHED": "reused",
        }.get(outcome.status, "newly-saved")
        status = checkpoint.status if checkpoint.verified else "NORMAL_TERMINAL"
        return CodexRunResult(
            run_id=run_id,
            normal_terminal=True,
            status=status,
            error_type=None,
            turn_status="completed",
            runtime_identity=runtime_identity(),
            checkpoint_outcomes=(checkpoint,),
            final_message="Mutation result.",
            file_actions=(
                CodexFileAction(
                    "Modify",
                    "target.txt",
                    access,
                    "approved",
                ),
            ),
        )


class ScriptedFactory:
    def __init__(self, *modes: str) -> None:
        self.modes = deque(modes)

    def __call__(
        self,
        engine: AccelerationEngine,
        approval_provider: Any,
        lifecycle_sink: Any,
    ) -> ScriptedAdapter:
        return ScriptedAdapter(
            engine,
            approval_provider,
            lifecycle_sink,
            self.modes.popleft(),
        )


def wait_for(
    controller: CompanionController,
    predicate: Any,
    timeout: float = 4,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        snapshot = controller.snapshot()
        if predicate(snapshot):
            return snapshot
        time.sleep(0.01)
    raise AssertionError(f"Timed out waiting for companion state: {snapshot!r}")


class CompanionControllerTest(unittest.TestCase):
    def make_controller(
        self,
        directory: Path,
        factory: ScriptedFactory,
        *,
        picker_result: str | None = None,
    ) -> CompanionController:
        return CompanionController(
            state_path=directory / "application-state" / "state.json",
            picker_script=directory / "fixed-picker.applescript",
            picker_runner=lambda _script: picker_result,
            adapter_factory=factory,
        )

    def test_picker_validates_git_root_and_rejects_non_git(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory(),
                picker_result=str(repository),
            )

            snapshot = controller.pick_repository()

            self.assertEqual(
                str(repository.resolve()),
                snapshot["repository"]["path"],
            )
            non_git = root / "plain"
            non_git.mkdir()
            controller = self.make_controller(
                root / "other",
                ScriptedFactory(),
                picker_result=str(non_git),
            )
            with self.assertRaises(RepositorySelectionError):
                controller.pick_repository()

    def test_state_file_is_0600_and_contains_only_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(root, ScriptedFactory())

            controller.select_repository(repository)

            state_path = root / "application-state" / "state.json"
            self.assertEqual(
                {"repository": str(repository.resolve())},
                json.loads(state_path.read_text(encoding="utf-8")),
            )
            self.assertEqual(
                0o600,
                stat.S_IMODE(state_path.stat().st_mode),
            )
            invalid = root / "invalid-state.json"
            invalid.write_text(
                json.dumps(
                    {
                        "repository": str(repository),
                        "prompt": "must not persist",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(CompanionStateError):
                CompanionController(
                    state_path=invalid,
                    picker_runner=lambda _script: None,
                )

    def test_read_only_result_has_zero_verified_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            controller.select_repository(repository)

            controller.start_run("Read the target without changing it.")
            snapshot = wait_for(
                controller,
                lambda state: state["run"]["state"] == "completed",
            )

            self.assertEqual("Read-only result.", snapshot["run"]["result"])
            self.assertEqual(
                {
                    "estimated_minutes": 0.0,
                    "estimated_money_jpy": 0.0,
                    "estimated_tokens": None,
                    "verified_reuses": 0,
                    "verified_saves": 0,
                },
                snapshot["run"]["receipt_delta"],
            )
            self.assertEqual(0, snapshot["receipt"]["verified_saves"])

    def test_allow_once_deny_and_repository_default_choices(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)

            allow = self.make_controller(root / "allow", ScriptedFactory("mutation"))
            allow.select_repository(repository)
            allow.start_run("Modify target once.")
            wait_for(allow, lambda state: state["run"]["approval"] is not None)
            allow.submit_approval("allow_once")
            allowed = wait_for(
                allow,
                lambda state: state["run"]["state"] == "completed",
            )
            self.assertEqual("one-time", allowed["run"]["file_actions"][0]["access"])
            self.assertEqual([], allowed["defaults"])

            deny = self.make_controller(root / "deny", ScriptedFactory("mutation"))
            deny.select_repository(repository)
            deny.start_run("Attempt a denied modification.")
            wait_for(deny, lambda state: state["run"]["approval"] is not None)
            deny.submit_approval("deny")
            denied = wait_for(
                deny,
                lambda state: state["run"]["state"] == "denied",
            )
            self.assertEqual("denied", denied["run"]["file_actions"][0]["access"])

            saved = self.make_controller(root / "saved", ScriptedFactory("mutation"))
            saved.select_repository(repository)
            saved.start_run("Save exact access.")
            approval = wait_for(
                saved,
                lambda state: state["run"]["approval"] is not None,
            )["run"]["approval"]
            self.assertEqual(
                {
                    "action": "Modify",
                    "diff": (
                        "--- a/target.txt\n"
                        "+++ b/target.txt\n"
                        "@@\n-before\n+after\n"
                    ),
                    "path": "target.txt",
                    "reason": "Apply the bounded update.",
                    "repository": "repo",
                },
                approval,
            )
            saved.submit_approval("repository")
            persisted = wait_for(
                saved,
                lambda state: state["run"]["state"] == "completed",
            )
            self.assertEqual(
                "newly-saved",
                persisted["run"]["file_actions"][0]["access"],
            )
            self.assertEqual(1, len(persisted["defaults"]))

    def test_default_reuse_receipt_delta_enumeration_and_revoke(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("mutation", "mutation"),
            )
            controller.select_repository(repository)
            controller.start_run("Create exact saved access.")
            wait_for(controller, lambda state: state["run"]["approval"] is not None)
            controller.submit_approval("repository")
            first = wait_for(
                controller,
                lambda state: state["run"]["state"] == "completed",
            )
            self.assertEqual(0, first["receipt"]["verified_saves"])
            self.assertEqual(1, len(first["defaults"]))

            controller.new_run()
            controller.start_run("Reuse exact saved access.")
            second = wait_for(
                controller,
                lambda state: state["run"]["state"] == "completed",
            )

            self.assertEqual(1, second["run"]["receipt_delta"]["verified_saves"])
            self.assertEqual(1, second["run"]["receipt_delta"]["verified_reuses"])
            self.assertEqual(7.5, second["run"]["receipt_delta"]["estimated_minutes"])
            self.assertEqual(625.0, second["run"]["receipt_delta"]["estimated_money_jpy"])
            self.assertIsNone(second["run"]["receipt_delta"]["estimated_tokens"])
            self.assertEqual(1, second["receipt"]["verified_saves"])
            self.assertEqual(1, second["receipt"]["verified_reuses"])
            handle = second["defaults"][0]["handle"]

            revoked = controller.revoke_default(handle)

            self.assertEqual([], revoked["defaults"])
            self.assertEqual(1, revoked["receipt"]["verified_saves"])
            with self.assertRaises(ApprovalStateError):
                controller.submit_approval("allow_once")

    def test_one_active_run_and_browser_reconnect_to_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("mutation"),
            )
            controller.select_repository(repository)
            controller.start_run("Wait for approval.")
            first = wait_for(
                controller,
                lambda state: state["run"]["approval"] is not None,
            )

            second = controller.snapshot()

            self.assertEqual(first["run"]["approval"], second["run"]["approval"])
            with self.assertRaises(RunConflictError):
                controller.start_run("Overlapping Run.")
            with self.assertRaises(RunConflictError):
                controller.select_repository(repository)
            controller.submit_approval("deny")
            wait_for(
                controller,
                lambda state: state["run"]["state"] == "denied",
            )

    def test_malformed_lifecycle_and_app_server_failure_are_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root / "malformed",
                ScriptedFactory("malformed"),
            )
            controller.select_repository(repository)
            controller.start_run("Malformed lifecycle.")
            malformed = wait_for(
                controller,
                lambda state: state["run"]["state"] == "needs_attention",
            )
            self.assertEqual(
                "The companion received an invalid progress event.",
                malformed["run"]["error"],
            )
            self.assertNotIn("<script>", json.dumps(malformed))

            controller = self.make_controller(
                root / "failure",
                ScriptedFactory("failure"),
            )
            controller.select_repository(repository)
            controller.start_run("Adapter failure.")
            failed = wait_for(
                controller,
                lambda state: state["run"]["state"] == "needs_attention",
            )
            self.assertEqual(
                "The bounded Codex Run failed closed.",
                failed["run"]["error"],
            )
            self.assertNotIn("sensitive", json.dumps(failed))

    def test_corrupted_event_chain_blocks_repository_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            engine = AccelerationEngine(repository)
            outcome = engine.evaluate(
                run_id=engine.new_run_id(),
                iteration=1,
                decision_type=DecisionType.MODIFY_FILE,
                requested_scope="target.txt",
                source_interrupt_id="corruption-setup",
                choice_provider=lambda _identity: "2",
            )
            self.assertTrue(outcome.allowed)
            events_path = engine.store.events_path
            events_path.write_text("{}\n", encoding="utf-8")
            controller = self.make_controller(root, ScriptedFactory())

            with self.assertRaises(RepositorySelectionError):
                controller.select_repository(repository)
