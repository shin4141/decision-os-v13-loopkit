"""Claude Agent SDK adapter for the agent-agnostic Verified Save engine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import importlib
from pathlib import Path
import subprocess
from typing import Any, TextIO

from .engine import AccelerationEngine, CheckpointOutcome, DecisionOutcome
from .model import DecisionType, ScopeError, canonical_json, normalize_scope


CLAUDE_AGENT_SDK_VERSION = "0.2.123"
BUNDLED_CLAUDE_CODE_VERSION = "2.1.215"
ADAPTER_NAME = "claude-agent-sdk"


class ClaudeAdapterUnavailable(RuntimeError):
    """The optional Claude adapter dependency is unavailable."""


class ClaudeAdapterFailure(RuntimeError):
    """The SDK contract or bounded run failed before a normal checkpoint."""


@dataclass(frozen=True)
class ClaudeRunResult:
    """Sanitized result of one fresh Claude SDK query."""

    run_id: str
    normal_terminal: bool
    status: str
    error_type: str | None
    result_subtype: str | None
    api_error_status: int | None
    stop_reason: str | None
    checkpoint_outcomes: tuple[CheckpointOutcome, ...]


@dataclass(frozen=True)
class _MutationCallbackIdentity:
    """Exact SDK callback identity eligible for same-Run replay."""

    tool_use_id: str
    tool_name: str
    normalized_path: str
    canonical_input: str


class ClaudeAdapter:
    """Map exact Claude Edit/Write callbacks into fixed protocol decisions."""

    def __init__(
        self,
        engine: AccelerationEngine,
        *,
        input_func: Callable[[], str],
        stdout: TextIO,
        sdk_module: Any | None = None,
    ) -> None:
        self.engine = engine
        self.input_func = input_func
        self.stdout = stdout
        self._sdk_module = sdk_module
        self._run_id = ""
        self._iteration = 0
        self._pending: dict[str, DecisionOutcome] = {}
        self._seen: dict[str, DecisionOutcome] = {}
        self._mutation_allowed = False
        self._allowed_callback: _MutationCallbackIdentity | None = None
        self._permission_denied = False

    def _load_sdk(self) -> Any:
        if self._sdk_module is None:
            try:
                module = importlib.import_module("claude_agent_sdk")
            except ModuleNotFoundError as exc:
                raise ClaudeAdapterUnavailable(
                    "Claude adapter unavailable. Install with "
                    "'pip install decision-os-v13-loopkit[claude]'."
                ) from exc
        else:
            module = self._sdk_module
        version = getattr(module, "__version__", None)
        if version != CLAUDE_AGENT_SDK_VERSION:
            raise ClaudeAdapterFailure(
                "Claude Agent SDK version mismatch: "
                f"expected {CLAUDE_AGENT_SDK_VERSION}, observed {version!r}."
            )
        return module

    @staticmethod
    def bundled_cli_identity(sdk_module: Any) -> str:
        """Read the bundled CLI version without invoking a system Claude binary."""

        module_file = getattr(sdk_module, "__file__", None)
        if not module_file:
            raise ClaudeAdapterFailure("Claude SDK package path is unavailable.")
        executable = Path(module_file).resolve().parent / "_bundled" / "claude"
        if not executable.is_file():
            raise ClaudeAdapterFailure("Bundled Claude Code CLI is unavailable.")
        completed = subprocess.run(
            (str(executable), "--version"),
            capture_output=True,
            check=False,
            text=True,
        )
        if completed.returncode != 0:
            raise ClaudeAdapterFailure("Bundled Claude Code CLI version failed.")
        observed = completed.stdout.strip()
        if not observed.startswith(BUNDLED_CLAUDE_CODE_VERSION):
            raise ClaudeAdapterFailure(
                "Bundled Claude Code CLI version mismatch: "
                f"expected {BUNDLED_CLAUDE_CODE_VERSION}, observed {observed!r}."
            )
        return observed

    def _map_tool(
        self,
        tool_name: str,
        input_data: dict[str, Any],
    ) -> tuple[DecisionType, str]:
        if tool_name not in {"Edit", "Write"}:
            raise ClaudeAdapterFailure(f"Unsupported Claude tool: {tool_name}")
        raw_path = input_data.get("file_path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ClaudeAdapterFailure(
                f"{tool_name} input lacks the validated file_path string."
            )
        normalized = normalize_scope(self.engine.repository, raw_path)
        if tool_name == "Edit":
            return DecisionType.MODIFY_FILE, raw_path
        target = self.engine.store.repository / normalized
        decision_type = (
            DecisionType.MODIFY_FILE
            if target.exists()
            else DecisionType.CREATE_FILE
        )
        return decision_type, raw_path

    def _human_choice(self, identity: Any) -> str | None:
        action = (
            "create"
            if identity.decision_type is DecisionType.CREATE_FILE
            else "modify"
        )
        self.stdout.write(
            "\nYour coding agent needs one default.\n\n"
            f"May it {action} {identity.normalized_scope}?\n\n"
            "[1] Allow once\n"
            "[2] Use for this repository\n"
            "[3] Deny\n\n"
            "Selection: "
        )
        self.stdout.flush()
        try:
            return self.input_func()
        except (EOFError, KeyboardInterrupt, OSError):
            return None

    async def _permission_callback(
        self,
        sdk_module: Any,
        tool_name: str,
        input_data: dict[str, Any],
        context: Any,
    ) -> Any:
        try:
            decision_type, raw_path = self._map_tool(tool_name, input_data)
            normalized = normalize_scope(self.engine.repository, raw_path)
            canonical_input = canonical_json(input_data)
        except (ClaudeAdapterFailure, ScopeError) as exc:
            self._permission_denied = True
            return sdk_module.PermissionResultDeny(
                message=f"Verified Save denied: {type(exc).__name__}",
                interrupt=False,
            )
        except (TypeError, ValueError):
            self._permission_denied = True
            return sdk_module.PermissionResultDeny(
                message="Verified Save denied: invalid canonical tool input",
                interrupt=False,
            )

        raw_tool_use_id = getattr(context, "tool_use_id", None)
        callback_identity = (
            _MutationCallbackIdentity(
                tool_use_id=raw_tool_use_id,
                tool_name=tool_name,
                normalized_path=normalized,
                canonical_input=canonical_input,
            )
            if isinstance(raw_tool_use_id, str) and raw_tool_use_id
            else None
        )
        if self._mutation_allowed:
            if (
                callback_identity is not None
                and callback_identity == self._allowed_callback
            ):
                return sdk_module.PermissionResultAllow()
            self._permission_denied = True
            return sdk_module.PermissionResultDeny(
                message=(
                    "Verified Save denied: one distinct mutation is allowed "
                    "per Run."
                ),
                interrupt=False,
            )

        repository_identity = self.engine.store.repository_id
        key = (
            f"{repository_identity}|{decision_type.value}|{normalized}"
        )
        if key in self._seen:
            existing = self._seen[key]
            if existing.allowed:
                return sdk_module.PermissionResultAllow()
            return sdk_module.PermissionResultDeny(
                message="Verified Save denied for this decision.",
                interrupt=False,
            )

        self._iteration += 1
        outcome = self.engine.evaluate(
            run_id=self._run_id,
            iteration=self._iteration,
            decision_type=decision_type,
            requested_scope=raw_path,
            source_interrupt_id=(
                raw_tool_use_id if isinstance(raw_tool_use_id, str) else None
            ),
            choice_provider=self._human_choice,
        )
        self._seen[key] = outcome
        if outcome.pending_cross_run_checkpoint:
            self._pending[outcome.identity.decision_key] = outcome
        if outcome.allowed:
            self._mutation_allowed = True
            self._allowed_callback = callback_identity
            return sdk_module.PermissionResultAllow()
        self._permission_denied = True
        return sdk_module.PermissionResultDeny(
            message="Human denied or no explicit selection was available.",
            interrupt=False,
        )

    def _options(
        self,
        sdk_module: Any,
        *,
        demo: bool,
    ) -> Any:
        available_tools = ["Read", "Edit"] if demo else ["Read", "Edit", "Write"]

        async def callback(
            tool_name: str,
            input_data: dict[str, Any],
            context: Any,
        ) -> Any:
            return await self._permission_callback(
                sdk_module,
                tool_name,
                input_data,
                context,
            )

        return sdk_module.ClaudeAgentOptions(
            allowed_tools=["Read"],
            can_use_tool=callback,
            continue_conversation=False,
            cwd=self.engine.store.repository,
            disallowed_tools=[],
            permission_mode="default",
            setting_sources=[],
            skills=[],
            strict_mcp_config=True,
            system_prompt=(
                "Perform only the requested bounded file operation. "
                "Use Read when needed and exactly one Edit or Write operation. "
                "Do not use Bash, do not touch another path, and stop normally "
                "after the requested operation."
            ),
            tools=available_tools,
        )

    async def run(self, prompt: str, *, demo: bool = False) -> ClaudeRunResult:
        """Run one fresh query and promote pending matches only on normal result."""

        sdk = self._load_sdk()
        self._run_id = self.engine.new_run_id()
        self._iteration = 0
        self._pending = {}
        self._seen = {}
        self._mutation_allowed = False
        self._allowed_callback = None
        self._permission_denied = False
        options = self._options(sdk, demo=demo)
        result_message: Any | None = None
        error_type: str | None = None

        try:
            async with sdk.ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                async for message in client.receive_response():
                    if isinstance(message, sdk.ResultMessage):
                        result_message = message
        except Exception as exc:
            error_type = type(exc).__name__

        normal_terminal = bool(
            result_message is not None
            and getattr(result_message, "subtype", None) == "success"
            and not bool(getattr(result_message, "is_error", True))
            and error_type is None
        )
        checkpoints = tuple(
            self.engine.finish_checkpoint(
                outcome,
                normal_terminal=normal_terminal,
                checkpoint_id=(
                    f"claude-result:{self._run_id}:{index}"
                    if result_message is not None
                    else f"claude-missing-result:{self._run_id}:{index}"
                ),
            )
            for index, outcome in enumerate(self._pending.values(), start=1)
        )
        if checkpoints:
            status = checkpoints[-1].status
        elif self._permission_denied:
            status = "DENIED"
        elif normal_terminal:
            status = "NORMAL_TERMINAL"
        else:
            status = "ABNORMAL_TERMINAL"
        return ClaudeRunResult(
            run_id=self._run_id,
            normal_terminal=normal_terminal,
            status=status,
            error_type=error_type,
            result_subtype=(
                getattr(result_message, "subtype", None)
                if result_message is not None
                else None
            ),
            api_error_status=(
                getattr(result_message, "api_error_status", None)
                if result_message is not None
                else None
            ),
            stop_reason=(
                getattr(result_message, "stop_reason", None)
                if result_message is not None
                else None
            ),
            checkpoint_outcomes=checkpoints,
        )
