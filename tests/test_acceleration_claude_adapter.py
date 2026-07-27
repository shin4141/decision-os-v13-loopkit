from __future__ import annotations

from dataclasses import dataclass
import io
from pathlib import Path
from types import SimpleNamespace
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from decision_os.acceleration.claude_adapter import (
    CLAUDE_AGENT_SDK_VERSION,
    ClaudeAdapter,
    ClaudeAdapterFailure,
    ClaudeAdapterUnavailable,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import DecisionType


@dataclass
class FakeAllow:
    behavior: str = "allow"


@dataclass
class FakeDeny:
    message: str = ""
    interrupt: bool = False
    behavior: str = "deny"


@dataclass
class FakeResult:
    subtype: str = "success"
    is_error: bool = False


@dataclass
class FakeContext:
    tool_use_id: str = "tool-use-1"


class FakeOptions:
    def __init__(self, **values: object) -> None:
        self.__dict__.update(values)


def create_repository(parent: Path) -> Path:
    repository = parent / "repo"
    repository.mkdir()
    subprocess.run(
        ("git", "init", "-q", str(repository)),
        check=True,
        capture_output=True,
    )
    (repository / "target.txt").write_text("one\n", encoding="utf-8")
    return repository


def fake_sdk(
    *,
    tool_name: str = "Edit",
    path: str = "target.txt",
    result: FakeResult | None = None,
    callback_results: list[object] | None = None,
    lifecycle_events: list[str] | None = None,
) -> SimpleNamespace:
    observed = callback_results if callback_results is not None else []
    events = lifecycle_events if lifecycle_events is not None else []

    class FakeClaudeSDKClient:
        def __init__(self, *, options: FakeOptions) -> None:
            self.options = options
            self.connected = False
            self.prompt: str | None = None

        async def __aenter__(self) -> FakeClaudeSDKClient:
            self.connected = True
            events.append("control_stream_opened")
            return self

        async def __aexit__(
            self,
            exc_type: object,
            exc: object,
            traceback: object,
        ) -> None:
            self.connected = False
            events.append("control_stream_closed")

        async def query(self, prompt: str) -> None:
            if not self.connected:
                raise AssertionError("query requires an open control stream")
            if not isinstance(prompt, str) or not prompt:
                raise AssertionError("missing prompt")
            self.prompt = prompt
            events.append("prompt_sent")

        async def receive_response(self):
            if not self.connected or self.prompt is None:
                raise AssertionError("response requires an open control stream")
            events.append("permission_requested")
            permission = await self.options.can_use_tool(
                tool_name,
                {"file_path": path},
                FakeContext(),
            )
            if not self.connected:
                raise AssertionError(
                    "control stream closed before permission completed"
                )
            observed.append(permission)
            events.append("permission_completed")
            events.append("terminal_result_received")
            yield result or FakeResult()

    return SimpleNamespace(
        __version__=CLAUDE_AGENT_SDK_VERSION,
        ClaudeAgentOptions=FakeOptions,
        ClaudeSDKClient=FakeClaudeSDKClient,
        PermissionResultAllow=FakeAllow,
        PermissionResultDeny=FakeDeny,
        ResultMessage=FakeResult,
    )


class ClaudeAdapterTest(unittest.IsolatedAsyncioTestCase):
    async def test_two_fresh_runs_create_default_then_verified_save(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = AccelerationEngine(
                repository,
                adapter="claude-agent-sdk",
                adapter_version=CLAUDE_AGENT_SDK_VERSION,
            )
            choices = iter(("2",))
            output = io.StringIO()
            permissions: list[object] = []
            adapter = ClaudeAdapter(
                engine,
                input_func=lambda: next(choices),
                stdout=output,
                sdk_module=fake_sdk(callback_results=permissions),
            )

            first = await adapter.run("first")
            second = await adapter.run("second")

            self.assertTrue(first.normal_terminal)
            self.assertEqual("NORMAL_TERMINAL", first.status)
            self.assertTrue(second.normal_terminal)
            self.assertEqual("VERIFIED_SAVE", second.status)
            self.assertEqual((1, 1), engine.store.counters())
            self.assertEqual(2, len(permissions))
            self.assertTrue(all(item.behavior == "allow" for item in permissions))
            self.assertEqual(1, output.getvalue().count("Selection:"))

    async def test_control_stream_stays_open_through_gated_edit_and_result(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            lifecycle: list[str] = []
            permissions: list[object] = []
            adapter = ClaudeAdapter(
                AccelerationEngine(repository),
                input_func=lambda: "1",
                stdout=io.StringIO(),
                sdk_module=fake_sdk(
                    callback_results=permissions,
                    lifecycle_events=lifecycle,
                ),
            )

            result = await adapter.run("modify target")

            self.assertTrue(result.normal_terminal)
            self.assertEqual(1, len(permissions))
            self.assertEqual(
                [
                    "control_stream_opened",
                    "prompt_sent",
                    "permission_requested",
                    "permission_completed",
                    "terminal_result_received",
                    "control_stream_closed",
                ],
                lifecycle,
            )

    async def test_error_result_leaves_cross_run_candidate_pending(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = AccelerationEngine(
                repository,
                adapter="claude-agent-sdk",
                adapter_version=CLAUDE_AGENT_SDK_VERSION,
            )
            first = ClaudeAdapter(
                engine,
                input_func=lambda: "2",
                stdout=io.StringIO(),
                sdk_module=fake_sdk(),
            )
            await first.run("first")
            second = ClaudeAdapter(
                engine,
                input_func=lambda: self.fail("human prompt must be skipped"),
                stdout=io.StringIO(),
                sdk_module=fake_sdk(
                    result=FakeResult(subtype="error", is_error=True)
                ),
            )

            result = await second.run("second")

            self.assertFalse(result.normal_terminal)
            self.assertEqual("PENDING", result.status)
            self.assertEqual("error", result.result_subtype)
            self.assertEqual((0, 0), engine.store.counters())

    async def test_options_isolate_settings_and_do_not_auto_allow_edits(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = AccelerationEngine(repository)
            adapter = ClaudeAdapter(
                engine,
                input_func=lambda: "3",
                stdout=io.StringIO(),
                sdk_module=fake_sdk(),
            )

            options = adapter._options(adapter._sdk_module, demo=False)

            self.assertEqual(["Read", "Edit", "Write"], options.tools)
            self.assertEqual(["Read"], options.allowed_tools)
            self.assertNotIn("Edit", options.allowed_tools)
            self.assertNotIn("Write", options.allowed_tools)
            self.assertEqual("default", options.permission_mode)
            self.assertEqual([], options.setting_sources)
            self.assertEqual([], options.skills)
            self.assertTrue(options.strict_mcp_config)
            self.assertFalse(options.continue_conversation)

    async def test_write_mapping_uses_pre_request_file_existence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = AccelerationEngine(repository)
            adapter = ClaudeAdapter(
                engine,
                input_func=lambda: "3",
                stdout=io.StringIO(),
                sdk_module=fake_sdk(),
            )

            existing, _ = adapter._map_tool(
                "Write", {"file_path": "target.txt"}
            )
            missing, _ = adapter._map_tool(
                "Write", {"file_path": "new.txt"}
            )

            self.assertIs(DecisionType.MODIFY_FILE, existing)
            self.assertIs(DecisionType.CREATE_FILE, missing)

    async def test_unsupported_tool_and_scope_escape_are_denied(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = AccelerationEngine(repository)
            denied: list[object] = []
            bash = ClaudeAdapter(
                engine,
                input_func=lambda: self.fail("must not prompt"),
                stdout=io.StringIO(),
                sdk_module=fake_sdk(
                    tool_name="Bash",
                    callback_results=denied,
                ),
            )
            escape = ClaudeAdapter(
                engine,
                input_func=lambda: self.fail("must not prompt"),
                stdout=io.StringIO(),
                sdk_module=fake_sdk(
                    path="../outside.txt",
                    callback_results=denied,
                ),
            )

            await bash.run("unsupported")
            await escape.run("escape")

            self.assertEqual(2, len(denied))
            self.assertTrue(all(item.behavior == "deny" for item in denied))
            self.assertEqual([], engine.store.read_events())

    async def test_missing_validated_file_path_schema_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            adapter = ClaudeAdapter(
                AccelerationEngine(repository),
                input_func=lambda: self.fail("must not prompt"),
                stdout=io.StringIO(),
                sdk_module=fake_sdk(),
            )

            with self.assertRaises(ClaudeAdapterFailure):
                adapter._map_tool("Edit", {})

    async def test_optional_sdk_is_loaded_lazily(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            adapter = ClaudeAdapter(
                AccelerationEngine(repository),
                input_func=lambda: "3",
                stdout=io.StringIO(),
            )
            with patch(
                "decision_os.acceleration.claude_adapter.importlib.import_module",
                side_effect=ModuleNotFoundError,
            ):
                with self.assertRaises(ClaudeAdapterUnavailable):
                    adapter._load_sdk()


if __name__ == "__main__":
    unittest.main()
