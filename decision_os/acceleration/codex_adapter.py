"""Codex app-server adapter for the agent-agnostic Verified Save engine."""

from __future__ import annotations

from collections.abc import Callable
import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import threading
from typing import Any, Protocol, TextIO

from .engine import AccelerationEngine, CheckpointOutcome, DecisionOutcome
from .model import DecisionType, ScopeError, normalize_scope


BUNDLED_CODEX_PATH = Path(
    "/Applications/ChatGPT.app/Contents/Resources/codex"
)
CODEX_CLI_VERSION = "0.146.0-alpha.3.1"
CODEX_MODEL = "gpt-5.6-sol"
CODEX_REASONING_EFFORT = "ultra"
CODEX_SERVICE_TIER = "priority"
ADAPTER_NAME = "codex-app-server"

_CLIENT_NAME = "decision_os_verified_save"
_CLIENT_VERSION = "0.1.0"
_DEVELOPER_INSTRUCTIONS = (
    "Perform only the requested bounded file operation. "
    "Do not use shell commands. "
    "Use the typed file-change tool for exactly one file mutation. "
    "Do not mutate files through shell commands, dynamic tools, or MCP tools. "
    "Do not touch another path, and stop normally after the requested operation."
)
_UNSUPPORTED_ITEM_TYPES = frozenset(
    {
        "collabAgentToolCall",
        "commandExecution",
        "dynamicToolCall",
        "hookPrompt",
        "imageGeneration",
        "mcpToolCall",
        "subAgentActivity",
    }
)
_UNSUPPORTED_REQUEST_METHOD_REASONS = {
    f"item/{item_type}/requestApproval": (
        f"unsupported_request_method:{item_type}"
    )
    for item_type in _UNSUPPORTED_ITEM_TYPES
}
_UNSUPPORTED_REASON_CODES = frozenset(
    {
        "approval_identity_mismatch",
        "additional_file_action_item",
        "duplicate_file_action_item_after_completion",
        "duplicate_approval_request",
        "unapproved_file_completion",
        "unsupported_file_change_shape",
        "unsupported_request_method:other",
    }
    | {
        f"unsupported_item_type:{item_type}"
        for item_type in _UNSUPPORTED_ITEM_TYPES
    }
    | set(_UNSUPPORTED_REQUEST_METHOD_REASONS.values())
)


class CodexAdapterUnavailable(RuntimeError):
    """The bundled Codex app-server executable is unavailable."""


class CodexAdapterFailure(RuntimeError):
    """The app-server contract or bounded run failed before a safe result."""


@dataclass(frozen=True)
class CodexRuntimeIdentity:
    """Machine-readable runtime identity observed from the app-server."""

    model: str
    reasoning_effort: str
    service_tier: str
    codex_cli_version: str
    account_type: str


@dataclass(frozen=True)
class CodexRunResult:
    """Sanitized result of one fresh Codex app-server thread."""

    run_id: str
    normal_terminal: bool
    status: str
    error_type: str | None
    turn_status: str | None
    runtime_identity: CodexRuntimeIdentity | None
    checkpoint_outcomes: tuple[CheckpointOutcome, ...]
    final_message: str = ""
    file_actions: tuple[CodexFileAction, ...] = ()
    unsupported_reason: str | None = None

    def __post_init__(self) -> None:
        if (
            self.unsupported_reason is not None
            and self.unsupported_reason not in _UNSUPPORTED_REASON_CODES
        ):
            raise ValueError(
                "Codex unsupported reason must be a bounded code."
            )
        if (
            self.status == "UNSUPPORTED_MUTATION"
        ) != (self.unsupported_reason is not None):
            raise ValueError(
                "Codex unsupported status and reason must agree."
            )


@dataclass(frozen=True)
class CodexApproval:
    """Presentation-safe description of one exact file-change approval."""

    repository_name: str
    action: str
    normalized_scope: str
    diff: str
    reason: str | None


@dataclass(frozen=True)
class CodexLifecycleEvent:
    """Small sanitized lifecycle event for non-CLI presentation surfaces."""

    kind: str
    message: str


@dataclass(frozen=True)
class CodexFileAction:
    """Presentation-safe outcome for one exact file action."""

    action: str
    normalized_scope: str
    access: str
    status: str


@dataclass(frozen=True)
class _CodexFileActionCandidate:
    """Internal action facts retained until terminal proof is available."""

    action: str
    item_id: str
    outcome: DecisionOutcome


@dataclass(frozen=True)
class _CodexApprovalBinding:
    """Exact one-Run human decision binding for one protocol item."""

    run_id: str
    item_id: str
    decision_type: DecisionType
    normalized_scope: str
    change_identity: str
    outcome: DecisionOutcome


class AppServerTransport(Protocol):
    """Small injectable JSONL transport used by the adapter and fake server."""

    @property
    def version(self) -> str:
        """Return the exact CLI version used by this transport."""

    def start(self) -> None:
        """Start one fresh app-server process."""

    def send(self, message: dict[str, Any]) -> None:
        """Send one JSON object as one JSONL message."""

    def receive(self) -> dict[str, Any]:
        """Receive one JSONL message."""

    def close(self) -> None:
        """Close the app-server process and control stream."""


class _SubprocessTransport:
    """Stable stdio JSONL transport for the bundled Codex app-server."""

    def __init__(self, executable: Path) -> None:
        self.executable = executable
        self._version = ""
        self._process: subprocess.Popen[str] | None = None
        self._stderr_thread: threading.Thread | None = None

    @property
    def version(self) -> str:
        return self._version

    def start(self) -> None:
        if not self.executable.is_file():
            raise CodexAdapterUnavailable(
                f"Bundled Codex executable is unavailable at {self.executable}."
            )
        try:
            completed = subprocess.run(
                (str(self.executable), "--version"),
                capture_output=True,
                check=False,
                text=True,
            )
        except OSError as exc:
            raise CodexAdapterUnavailable(
                "Bundled Codex version could not be read."
            ) from exc
        observed = completed.stdout.strip()
        prefix = "codex-cli "
        if completed.returncode != 0 or not observed.startswith(prefix):
            raise CodexAdapterFailure(
                "Bundled Codex CLI returned an invalid version identity."
            )
        self._version = observed[len(prefix) :].strip()
        try:
            self._process = subprocess.Popen(
                (
                    str(self.executable),
                    "-c",
                    "features.apps=false",
                    "-c",
                    "features.hooks=false",
                    "-c",
                    "features.multi_agent=false",
                    "-c",
                    "features.remote_plugin=false",
                    "-c",
                    "features.shell_tool=false",
                    "-c",
                    "features.skill_mcp_dependency_install=false",
                    "-c",
                    "mcp_servers={}",
                    "-c",
                    "plugins={}",
                    "app-server",
                ),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
        except OSError as exc:
            raise CodexAdapterUnavailable(
                "Bundled Codex app-server could not be started."
            ) from exc
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr,
            name="decision-os-codex-stderr",
            daemon=True,
        )
        self._stderr_thread.start()

    def _drain_stderr(self) -> None:
        process = self._process
        if process is None or process.stderr is None:
            return
        try:
            for _line in process.stderr:
                pass
        except (OSError, UnicodeError):
            return

    def send(self, message: dict[str, Any]) -> None:
        process = self._process
        if process is None or process.stdin is None or process.poll() is not None:
            raise CodexAdapterFailure("Codex app-server control stream is closed.")
        try:
            process.stdin.write(
                json.dumps(
                    message,
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            process.stdin.write("\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError, UnicodeError) as exc:
            raise CodexAdapterFailure(
                "Codex app-server control stream write failed."
            ) from exc

    def receive(self) -> dict[str, Any]:
        process = self._process
        if process is None or process.stdout is None:
            raise CodexAdapterFailure("Codex app-server is not running.")
        try:
            raw = process.stdout.readline()
        except (OSError, UnicodeError) as exc:
            raise CodexAdapterFailure(
                "Codex app-server control stream read failed."
            ) from exc
        if not raw:
            raise CodexAdapterFailure(
                "Codex app-server closed before the terminal checkpoint."
            )
        try:
            message = json.loads(raw)
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise CodexAdapterFailure(
                "Codex app-server emitted invalid JSONL."
            ) from exc
        if not isinstance(message, dict):
            raise CodexAdapterFailure(
                "Codex app-server emitted a non-object JSONL message."
            )
        return message

    def close(self) -> None:
        process = self._process
        if process is None:
            return
        if process.stdin is not None:
            try:
                process.stdin.close()
            except OSError:
                pass
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        if self._stderr_thread is not None:
            self._stderr_thread.join(timeout=1)


TransportFactory = Callable[[Path], AppServerTransport]
ApprovalProvider = Callable[[CodexApproval], str | None]
LifecycleSink = Callable[[CodexLifecycleEvent], None]


class CodexAdapter:
    """Map exact Codex file-change approvals into fixed protocol decisions."""

    def __init__(
        self,
        engine: AccelerationEngine,
        *,
        input_func: Callable[[], str],
        stdout: TextIO,
        executable: Path | None = None,
        transport_factory: TransportFactory | None = None,
        approval_provider: ApprovalProvider | None = None,
        lifecycle_sink: LifecycleSink | None = None,
        expected_model: str = CODEX_MODEL,
        expected_reasoning_effort: str = CODEX_REASONING_EFFORT,
        expected_service_tier: str = CODEX_SERVICE_TIER,
        expected_cli_version: str = CODEX_CLI_VERSION,
    ) -> None:
        self.engine = engine
        self.input_func = input_func
        self.stdout = stdout
        self.executable = executable or BUNDLED_CODEX_PATH
        self.transport_factory = transport_factory or _SubprocessTransport
        self.approval_provider = approval_provider
        self.lifecycle_sink = lifecycle_sink
        self.expected_model = expected_model
        self.expected_reasoning_effort = expected_reasoning_effort
        self.expected_service_tier = expected_service_tier
        self.expected_cli_version = expected_cli_version
        self._request_id = 0
        self._transport: AppServerTransport | None = None
        self._run_id = ""
        self._thread_id: str | None = None
        self._turn_id: str | None = None
        self._turn_status: str | None = None
        self._runtime_identity: CodexRuntimeIdentity | None = None
        self._account_type: str | None = None
        self._thread_cli_version: str | None = None
        self._settings_verified = False
        self._deferred_settings: list[dict[str, Any]] = []
        self._iteration = 0
        self._items: dict[str, dict[str, Any]] = {}
        self._approved_changes: dict[str, list[dict[str, Any]]] = {}
        self._approval_requests: dict[str | int, str | None] = {}
        self._resolved_approval_requests: set[str | int] = set()
        self._accepted_items: set[str] = set()
        self._declined_items: set[str] = set()
        self._resolved_items: set[str] = set()
        self._completed_items: set[str] = set()
        self._pending: dict[str, DecisionOutcome] = {}
        self._approval_binding: _CodexApprovalBinding | None = None
        self._permission_denied = False
        self._unsupported_mutation = False
        self._unsupported_reason: str | None = None
        self._identity_failure = False
        self._final_message = ""
        self._file_action_candidates: list[_CodexFileActionCandidate] = []

    def _reset_run(self) -> None:
        self._request_id = 0
        self._run_id = self.engine.new_run_id()
        self._thread_id = None
        self._turn_id = None
        self._turn_status = None
        self._runtime_identity = None
        self._account_type = None
        self._thread_cli_version = None
        self._settings_verified = False
        self._deferred_settings = []
        self._iteration = 0
        self._items = {}
        self._approved_changes = {}
        self._approval_requests = {}
        self._resolved_approval_requests = set()
        self._accepted_items = set()
        self._declined_items = set()
        self._resolved_items = set()
        self._completed_items = set()
        self._pending = {}
        self._approval_binding = None
        self._permission_denied = False
        self._unsupported_mutation = False
        self._unsupported_reason = None
        self._identity_failure = False
        self._final_message = ""
        self._file_action_candidates = []

    def _emit(self, kind: str, message: str) -> None:
        if self.lifecycle_sink is None:
            return
        self.lifecycle_sink(CodexLifecycleEvent(kind=kind, message=message))

    def _send(self, message: dict[str, Any]) -> None:
        if self._transport is None:
            raise CodexAdapterFailure("Codex app-server transport is unavailable.")
        self._transport.send(message)

    def _receive(self) -> dict[str, Any]:
        if self._transport is None:
            raise CodexAdapterFailure("Codex app-server transport is unavailable.")
        return self._transport.receive()

    def _request(self, method: str, params: dict[str, Any]) -> Any:
        self._request_id += 1
        request_id = self._request_id
        self._send({"id": request_id, "method": method, "params": params})
        while True:
            message = self._receive()
            if (
                message.get("id") == request_id
                and "method" not in message
            ):
                if "error" in message:
                    raise CodexAdapterFailure(
                        f"Codex app-server {method} request failed."
                    )
                if "result" not in message:
                    raise CodexAdapterFailure(
                        f"Codex app-server {method} response is incomplete."
                    )
                return message["result"]
            self._dispatch(message)

    @staticmethod
    def _require_object(value: Any, label: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise CodexAdapterFailure(f"{label} is not an object.")
        return value

    def _initialize(self) -> None:
        self._emit("runtime", "Starting the private Codex runtime.")
        result = self._require_object(
            self._request(
                "initialize",
                {
                    "capabilities": {"experimentalApi": False},
                    "clientInfo": {
                        "name": _CLIENT_NAME,
                        "title": "Decision OS Verified Save",
                        "version": _CLIENT_VERSION,
                    },
                },
            ),
            "initialize result",
        )
        for field in ("codexHome", "platformFamily", "platformOs", "userAgent"):
            if not isinstance(result.get(field), str) or not result[field]:
                raise CodexAdapterFailure(
                    f"initialize result lacks {field} identity."
                )
        self._send({"method": "initialized", "params": {}})

    def _verify_account(self) -> None:
        self._emit("account", "Verifying ChatGPT authentication.")
        result = self._require_object(
            self._request("account/read", {"refreshToken": False}),
            "account/read result",
        )
        account = self._require_object(
            result.get("account"),
            "account/read account",
        )
        if account.get("type") != "chatgpt":
            raise CodexAdapterFailure(
                "Codex app-server is not using ChatGPT subscription authentication."
            )
        self._account_type = "chatgpt"

    def _verify_model_catalog(self) -> None:
        self._emit("model", "Verifying the required model and service tier.")
        cursor: str | None = None
        seen_cursors: set[str] = set()
        while True:
            params: dict[str, Any] = {"includeHidden": False}
            if cursor is not None:
                params["cursor"] = cursor
            result = self._require_object(
                self._request("model/list", params),
                "model/list result",
            )
            data = result.get("data")
            if not isinstance(data, list):
                raise CodexAdapterFailure("Codex model catalog is unavailable.")
            selected = next(
                (
                    item
                    for item in data
                    if isinstance(item, dict)
                    and (
                        item.get("id") == self.expected_model
                        or item.get("model") == self.expected_model
                    )
                ),
                None,
            )
            if selected is not None:
                efforts = selected.get("supportedReasoningEfforts")
                tiers = selected.get("serviceTiers")
                if not isinstance(efforts, list) or not any(
                    isinstance(item, dict)
                    and item.get("reasoningEffort")
                    == self.expected_reasoning_effort
                    for item in efforts
                ):
                    raise CodexAdapterFailure(
                        "Required Codex reasoning effort is unsupported."
                    )
                if not isinstance(tiers, list) or not any(
                    isinstance(item, dict)
                    and item.get("id") == self.expected_service_tier
                    for item in tiers
                ):
                    raise CodexAdapterFailure(
                        "Required Codex service tier is unsupported."
                    )
                return
            next_cursor = result.get("nextCursor")
            if (
                not isinstance(next_cursor, str)
                or not next_cursor
                or next_cursor in seen_cursors
            ):
                raise CodexAdapterFailure(
                    "Required Codex model is absent from the local catalog."
                )
            seen_cursors.add(next_cursor)
            cursor = next_cursor

    def _start_thread(self) -> None:
        self._emit("run", "Starting one fresh bounded Run.")
        repository = self.engine.store.repository
        isolated_features = {
            "apps": False,
            "hooks": False,
            "multi_agent": False,
            "remote_plugin": False,
            "shell_tool": False,
            "skill_mcp_dependency_install": False,
        }
        result = self._require_object(
            self._request(
                "thread/start",
                {
                    "approvalPolicy": "on-request",
                    "approvalsReviewer": "user",
                    "config": {
                        "features": isolated_features,
                        "mcp_servers": {},
                        "model_reasoning_effort": (
                            self.expected_reasoning_effort
                        ),
                        "plugins": {},
                    },
                    "cwd": str(repository),
                    "developerInstructions": _DEVELOPER_INSTRUCTIONS,
                    "ephemeral": True,
                    "model": self.expected_model,
                    "modelProvider": "openai",
                    "sandbox": "read-only",
                    "serviceTier": self.expected_service_tier,
                },
            ),
            "thread/start result",
        )
        thread = self._require_object(result.get("thread"), "thread identity")
        thread_id = thread.get("id")
        cli_version = thread.get("cliVersion")
        if not isinstance(thread_id, str) or not thread_id:
            raise CodexAdapterFailure("thread/start lacks a fresh thread ID.")
        if cli_version != self.expected_cli_version:
            raise CodexAdapterFailure(
                "Codex app-server thread version identity mismatch."
            )
        if self._transport is None or self._transport.version != cli_version:
            raise CodexAdapterFailure(
                "Codex CLI and app-server version identities differ."
            )
        if result.get("model") != self.expected_model:
            raise CodexAdapterFailure("Codex model identity mismatch.")
        if result.get("modelProvider") != "openai":
            raise CodexAdapterFailure("Codex model provider identity mismatch.")
        if result.get("reasoningEffort") != self.expected_reasoning_effort:
            raise CodexAdapterFailure("Codex reasoning effort identity mismatch.")
        if result.get("serviceTier") != self.expected_service_tier:
            raise CodexAdapterFailure("Codex service tier identity mismatch.")
        if result.get("approvalPolicy") != "on-request":
            raise CodexAdapterFailure("Codex approval policy identity mismatch.")
        if result.get("approvalsReviewer") != "user":
            raise CodexAdapterFailure("Codex approval reviewer identity mismatch.")
        if not self._cwd_matches(result.get("cwd")):
            raise CodexAdapterFailure("Codex thread cwd identity mismatch.")
        if not self._read_only_sandbox(result.get("sandbox")):
            raise CodexAdapterFailure("Codex thread sandbox identity mismatch.")
        if thread.get("ephemeral") is not True:
            raise CodexAdapterFailure("Codex thread is not ephemeral.")
        if not self._cwd_matches(thread.get("cwd")):
            raise CodexAdapterFailure("Codex thread root identity mismatch.")
        account_type = self._account_type
        if account_type != "chatgpt":
            raise CodexAdapterFailure(
                "Codex account identity changed during thread start."
            )
        self._thread_id = thread_id
        self._thread_cli_version = cli_version
        self._settings_verified = True
        self._runtime_identity = CodexRuntimeIdentity(
            model=result["model"],
            reasoning_effort=result["reasoningEffort"],
            service_tier=result["serviceTier"],
            codex_cli_version=cli_version,
            account_type=account_type,
        )
        deferred = tuple(self._deferred_settings)
        self._deferred_settings = []
        for params in deferred:
            self._verify_settings(params)

    def _start_turn(self, prompt: str) -> None:
        if self._thread_id is None:
            raise CodexAdapterFailure("Codex thread identity is unavailable.")
        result = self._require_object(
            self._request(
                "turn/start",
                {
                    "approvalPolicy": "on-request",
                    "approvalsReviewer": "user",
                    "cwd": str(self.engine.store.repository),
                    "effort": self.expected_reasoning_effort,
                    "input": [{"text": prompt, "type": "text"}],
                    "model": self.expected_model,
                    "sandboxPolicy": {
                        "networkAccess": False,
                        "type": "readOnly",
                    },
                    "serviceTier": self.expected_service_tier,
                    "threadId": self._thread_id,
                },
            ),
            "turn/start result",
        )
        turn = self._require_object(result.get("turn"), "turn identity")
        turn_id = turn.get("id")
        if not isinstance(turn_id, str) or not turn_id:
            raise CodexAdapterFailure("turn/start lacks a fresh turn ID.")
        if self._turn_id is not None and self._turn_id != turn_id:
            raise CodexAdapterFailure("Codex turn identity changed during start.")
        self._turn_id = turn_id
        self._emit("working", "Codex is working on the bounded task.")

    def _cwd_matches(self, value: Any) -> bool:
        if not isinstance(value, str) or not value:
            return False
        try:
            return (
                Path(value).resolve()
                == self.engine.store.repository
            )
        except (OSError, RuntimeError, TypeError):
            return False

    @staticmethod
    def _read_only_sandbox(value: Any) -> bool:
        return bool(
            isinstance(value, dict)
            and value.get("type") == "readOnly"
            and value.get("networkAccess") is False
        )

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

    def _approval_choice(
        self,
        identity: Any,
        item: dict[str, Any],
        params: dict[str, Any],
    ) -> str | None:
        if self.approval_provider is None:
            return self._human_choice(identity)
        change = self._require_object(
            item["changes"][0],
            "Codex approval change",
        )
        diff = change.get("diff")
        if not isinstance(diff, str):
            raise CodexAdapterFailure(
                "Codex file change lacks a typed diff."
            )
        action = (
            "Create"
            if identity.decision_type is DecisionType.CREATE_FILE
            else "Modify"
        )
        reason = params.get("reason")
        if reason is not None and not isinstance(reason, str):
            reason = None
        self._emit("approval", "Waiting for one exact file-change decision.")
        return self.approval_provider(
            CodexApproval(
                repository_name=self.engine.store.repository.name,
                action=action,
                normalized_scope=identity.normalized_scope,
                diff=diff,
                reason=reason,
            )
        )

    def _mark_unsupported(self, reason: str) -> None:
        if reason not in _UNSUPPORTED_REASON_CODES:
            raise CodexAdapterFailure(
                "Codex unsupported reason is not a bounded code."
            )
        self._unsupported_mutation = True
        if self._unsupported_reason is None:
            self._unsupported_reason = reason

    def _final_file_actions(
        self,
        checkpoint_by_decision_key: dict[str, CheckpointOutcome],
        *,
        normal_terminal: bool,
    ) -> tuple[CodexFileAction, ...]:
        actions: list[CodexFileAction] = []
        for candidate in self._file_action_candidates:
            outcome = candidate.outcome
            if not outcome.allowed:
                if outcome.status != "DENIED":
                    continue
                access = "denied"
                status = "denied"
            elif outcome.status == "DEFAULT_MATCHED":
                checkpoint = checkpoint_by_decision_key.get(
                    outcome.identity.decision_key
                )
                verified = bool(
                    checkpoint is not None
                    and checkpoint.verified
                    and checkpoint.status
                    in {"VERIFIED_SAVE", "VERIFIED_REUSE"}
                )
                access = (
                    "reused" if verified else "matched-not-verified"
                )
                status = "approved"
            elif outcome.status == "ALLOW_ONCE":
                if candidate.item_id not in self._completed_items:
                    continue
                access = "one-time"
                status = "approved"
            elif outcome.status in {
                "HUMAN_DEFAULT_CREATED",
                "SAME_RUN_DEFAULT",
            }:
                if not normal_terminal:
                    continue
                access = "newly-saved"
                status = "approved"
            else:
                continue
            actions.append(
                CodexFileAction(
                    action=candidate.action,
                    normalized_scope=outcome.identity.normalized_scope,
                    access=access,
                    status=status,
                )
            )
        return tuple(actions)

    def _final_message_with_diagnostic(self, status: str) -> str:
        if (
            status != "UNSUPPORTED_MUTATION"
            or self._unsupported_reason is None
        ):
            return self._final_message
        diagnostic = (
            "Decision OS verification: not verified "
            f"({self._unsupported_reason})."
        )
        separator = "\n\n" if self._final_message else ""
        return f"{self._final_message}{separator}{diagnostic}"

    def _map_file_change(
        self,
        item: dict[str, Any],
    ) -> tuple[DecisionType, str]:
        changes = item.get("changes")
        if not isinstance(changes, list) or len(changes) != 1:
            raise CodexAdapterFailure(
                "Codex file approval is not one exact file change."
            )
        change = self._require_object(changes[0], "Codex file change")
        raw_path = change.get("path")
        diff = change.get("diff")
        kind = self._require_object(
            change.get("kind"),
            "Codex file change kind",
        )
        kind_type = kind.get("type")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise CodexAdapterFailure(
                "Codex file change lacks an exact path."
            )
        if not isinstance(diff, str):
            raise CodexAdapterFailure(
                "Codex file change lacks a typed diff."
            )
        normalized = normalize_scope(self.engine.repository, raw_path)
        target = self.engine.store.repository / normalized
        if kind_type == "add":
            if target.exists():
                raise CodexAdapterFailure(
                    "Codex add target already exists before approval."
                )
            return DecisionType.CREATE_FILE, raw_path
        if kind_type == "update":
            if kind.get("move_path") not in {None, ""}:
                raise CodexAdapterFailure(
                    "Codex move or rename is unsupported."
                )
            if not target.is_file():
                raise CodexAdapterFailure(
                    "Codex update target is not an existing file."
                )
            return DecisionType.MODIFY_FILE, raw_path
        raise CodexAdapterFailure(
            f"Unsupported Codex file change kind: {kind_type!r}."
        )

    def _ids_match(self, params: dict[str, Any]) -> bool:
        if params.get("threadId") != self._thread_id:
            return False
        observed_turn_id = params.get("turnId")
        if not isinstance(observed_turn_id, str) or not observed_turn_id:
            return False
        if self._turn_id is None:
            self._turn_id = observed_turn_id
        return observed_turn_id == self._turn_id

    def _register_approval_request(
        self,
        request_id: Any,
        item_id: Any,
    ) -> bool:
        if (
            not isinstance(request_id, (str, int))
            or isinstance(request_id, bool)
            or request_id in self._approval_requests
        ):
            return False
        self._approval_requests[request_id] = (
            item_id if isinstance(item_id, str) else None
        )
        return True

    def _respond_file_approval(self, message: dict[str, Any]) -> None:
        request_id = message.get("id")
        params = self._require_object(
            message.get("params"),
            "file approval parameters",
        )
        item_id = params.get("itemId")
        valid_request_id = (
            isinstance(request_id, (str, int))
            and not isinstance(request_id, bool)
        )
        request_replay = bool(
            valid_request_id and request_id in self._approval_requests
        )
        if request_replay:
            if self._approval_requests[request_id] != item_id:
                self._mark_unsupported("approval_identity_mismatch")
                if isinstance(item_id, str):
                    self._declined_items.add(item_id)
                self._send(
                    {"id": request_id, "result": {"decision": "decline"}}
                )
                return
        elif not self._register_approval_request(request_id, item_id):
            self._mark_unsupported("approval_identity_mismatch")
            if isinstance(item_id, str):
                self._declined_items.add(item_id)
            self._send(
                {"id": request_id, "result": {"decision": "decline"}}
            )
            return
        if (
            not isinstance(item_id, str)
            or not self._ids_match(params)
            or not self._settings_verified
            or item_id not in self._items
        ):
            self._mark_unsupported("approval_identity_mismatch")
            if isinstance(item_id, str):
                self._declined_items.add(item_id)
            self._send(
                {"id": request_id, "result": {"decision": "decline"}}
            )
            return
        try:
            decision_type, raw_path = self._map_file_change(
                self._items[item_id]
            )
            normalized = normalize_scope(self.engine.repository, raw_path)
        except (CodexAdapterFailure, ScopeError):
            self._mark_unsupported("unsupported_file_change_shape")
            self._declined_items.add(item_id)
            self._send(
                {"id": request_id, "result": {"decision": "decline"}}
            )
            return

        changes = self._items[item_id]["changes"]
        change_identity = hashlib.sha256(
            json.dumps(
                changes,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        binding = self._approval_binding
        if binding is not None:
            exact_item_replay = bool(
                binding.run_id == self._run_id
                and binding.item_id == item_id
                and binding.decision_type is decision_type
                and binding.normalized_scope == normalized
                and binding.change_identity == change_identity
            )
            if exact_item_replay:
                self._send(
                    {
                        "id": request_id,
                        "result": {
                            "decision": (
                                "accept" if binding.outcome.allowed else "decline"
                            )
                        },
                    }
                )
                return
            reason = (
                "duplicate_file_action_item_after_completion"
                if (
                    binding.decision_type is decision_type
                    and binding.normalized_scope == normalized
                )
                else "additional_file_action_item"
            )
            self._mark_unsupported(reason)
            self._declined_items.add(item_id)
            self._send(
                {"id": request_id, "result": {"decision": "decline"}}
            )
            return

        self._iteration += 1
        outcome = self.engine.evaluate(
            run_id=self._run_id,
            iteration=self._iteration,
            decision_type=decision_type,
            requested_scope=raw_path,
            source_interrupt_id=item_id,
            choice_provider=lambda identity: self._approval_choice(
                identity,
                self._items[item_id],
                params,
            ),
        )
        self._approval_binding = _CodexApprovalBinding(
            run_id=self._run_id,
            item_id=item_id,
            decision_type=decision_type,
            normalized_scope=normalized,
            change_identity=change_identity,
            outcome=outcome,
        )
        if outcome.pending_cross_run_checkpoint:
            self._pending[outcome.identity.decision_key] = outcome

        if outcome.allowed:
            decision_type, _ = self._map_file_change(self._items[item_id])
            self._file_action_candidates.append(
                _CodexFileActionCandidate(
                    action=(
                        "Create"
                        if decision_type is DecisionType.CREATE_FILE
                        else "Modify"
                    ),
                    item_id=item_id,
                    outcome=outcome,
                )
            )
            self._accepted_items.add(item_id)
            self._approved_changes[item_id] = copy.deepcopy(
                self._items[item_id]["changes"]
            )
            self._send(
                {"id": request_id, "result": {"decision": "accept"}}
            )
            return
        self._permission_denied = True
        self._file_action_candidates.append(
            _CodexFileActionCandidate(
                action=(
                    "Create"
                    if outcome.identity.decision_type is DecisionType.CREATE_FILE
                    else "Modify"
                ),
                item_id=item_id,
                outcome=outcome,
            )
        )
        self._declined_items.add(item_id)
        self._send(
            {"id": request_id, "result": {"decision": "decline"}}
        )

    def _resolve_request(self, params: dict[str, Any]) -> None:
        if params.get("threadId") != self._thread_id:
            self._identity_failure = True
            return
        request_id = params.get("requestId")
        if (
            not isinstance(request_id, (str, int))
            or isinstance(request_id, bool)
        ):
            self._identity_failure = True
            return
        if (
            request_id not in self._approval_requests
        ):
            self._identity_failure = True
            return
        if request_id in self._resolved_approval_requests:
            return
        self._resolved_approval_requests.add(request_id)
        item_id = self._approval_requests[request_id]
        if item_id is None:
            return
        if item_id in self._resolved_items:
            return
        self._resolved_items.add(item_id)

    def _respond_unsupported_request(self, message: dict[str, Any]) -> None:
        request_id = message.get("id")
        method = message.get("method")
        reason = _UNSUPPORTED_REQUEST_METHOD_REASONS.get(
            method,
            "unsupported_request_method:other",
        )
        self._mark_unsupported(reason)
        params = message.get("params")
        item_id = params.get("itemId") if isinstance(params, dict) else None
        self._register_approval_request(request_id, item_id)
        if method == "item/commandExecution/requestApproval":
            self._send(
                {"id": request_id, "result": {"decision": "decline"}}
            )
            return
        self._send(
            {
                "error": {
                    "code": -32601,
                    "message": "Unsupported approval request.",
                },
                "id": request_id,
            }
        )

    def _cache_item(self, params: dict[str, Any]) -> None:
        if not self._ids_match(params):
            self._identity_failure = True
            return
        item = self._require_object(params.get("item"), "started item")
        item_type = item.get("type")
        if item_type in _UNSUPPORTED_ITEM_TYPES:
            self._mark_unsupported(
                f"unsupported_item_type:{item_type}"
            )
            return
        if item_type != "fileChange":
            return
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            self._identity_failure = True
            return
        if item_id in self._items:
            if self._items[item_id] != item:
                self._identity_failure = True
            return
        self._items[item_id] = item

    def _update_patch(self, params: dict[str, Any]) -> None:
        if not self._ids_match(params):
            self._identity_failure = True
            return
        item_id = params.get("itemId")
        changes = params.get("changes")
        if (
            not isinstance(item_id, str)
            or item_id not in self._items
            or not isinstance(changes, list)
        ):
            self._identity_failure = True
            return
        if item_id in self._approved_changes:
            self._identity_failure = True
            return
        updated = dict(self._items[item_id])
        updated["changes"] = changes
        self._items[item_id] = updated

    def _complete_item(self, params: dict[str, Any]) -> None:
        if not self._ids_match(params):
            self._identity_failure = True
            return
        item = self._require_object(params.get("item"), "completed item")
        item_type = item.get("type")
        if item_type in _UNSUPPORTED_ITEM_TYPES:
            self._mark_unsupported(
                f"unsupported_item_type:{item_type}"
            )
            return
        if item_type == "agentMessage":
            text = item.get("text")
            phase = item.get("phase")
            if (
                not isinstance(text, str)
                or phase not in {None, "final_answer", "commentary"}
            ):
                self._identity_failure = True
                return
            if phase in {None, "final_answer"}:
                self._final_message = text
            return
        if item_type != "fileChange":
            return
        item_id = item.get("id")
        if item_id in self._declined_items:
            if (
                item.get("status") != "declined"
                or item_id not in self._resolved_items
            ):
                self._identity_failure = True
            return
        if item_id not in self._accepted_items:
            self._mark_unsupported("unapproved_file_completion")
            self._identity_failure = True
            return
        approved = self._approved_changes.get(item_id)
        if item_id in self._completed_items:
            if (
                item.get("status") != "completed"
                or approved is None
                or item.get("changes") != approved
                or item_id not in self._resolved_items
            ):
                self._identity_failure = True
            return
        if (
            item.get("status") != "completed"
            or approved is None
            or item.get("changes") != approved
            or item_id not in self._resolved_items
        ):
            self._identity_failure = True
            return
        self._completed_items.add(item_id)

    def _invalidate_runtime_identity(self) -> None:
        self._identity_failure = True
        self._settings_verified = False
        self._runtime_identity = None

    def _verify_settings(self, params: dict[str, Any]) -> None:
        if self._thread_id is None:
            self._deferred_settings.append(params)
            return
        if params.get("threadId") != self._thread_id:
            self._invalidate_runtime_identity()
            return
        settings = self._require_object(
            params.get("threadSettings"),
            "thread settings",
        )
        identity = self._runtime_identity
        if (
            self._identity_failure
            or not self._settings_verified
            or identity is None
            or identity.account_type != self._account_type
            or identity.codex_cli_version != self._thread_cli_version
            or settings.get("model") != identity.model
            or settings.get("modelProvider") != "openai"
            or settings.get("effort") != identity.reasoning_effort
            or settings.get("serviceTier") != identity.service_tier
            or settings.get("approvalPolicy") != "on-request"
            or settings.get("approvalsReviewer") != "user"
            or not self._cwd_matches(settings.get("cwd"))
            or not self._read_only_sandbox(
                settings.get("sandboxPolicy")
            )
        ):
            self._invalidate_runtime_identity()
            return

    def _complete_turn(self, params: dict[str, Any]) -> None:
        if params.get("threadId") != self._thread_id:
            self._identity_failure = True
            return
        turn = self._require_object(params.get("turn"), "completed turn")
        turn_id = turn.get("id")
        if not isinstance(turn_id, str) or not turn_id:
            self._identity_failure = True
            return
        if self._turn_id is None:
            self._turn_id = turn_id
        elif turn_id != self._turn_id:
            self._identity_failure = True
            return
        status = turn.get("status")
        if not isinstance(status, str):
            self._identity_failure = True
            return
        self._turn_status = status
        self._emit("finalizing", "Finalizing the local Receipt.")

    def _dispatch(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        if not isinstance(method, str):
            raise CodexAdapterFailure(
                "Codex app-server emitted an uncorrelated response."
            )
        if "id" in message:
            if method == "item/fileChange/requestApproval":
                self._respond_file_approval(message)
            else:
                self._respond_unsupported_request(message)
            return
        params = self._require_object(
            message.get("params", {}),
            f"{method} parameters",
        )
        if method == "item/started":
            self._cache_item(params)
        elif method == "item/fileChange/patchUpdated":
            self._update_patch(params)
        elif method == "item/completed":
            self._complete_item(params)
        elif method == "thread/settings/updated":
            self._verify_settings(params)
        elif method == "serverRequest/resolved":
            self._resolve_request(params)
        elif method == "turn/started":
            if params.get("threadId") != self._thread_id:
                self._identity_failure = True
            else:
                turn = self._require_object(
                    params.get("turn"),
                    "started turn",
                )
                turn_id = turn.get("id")
                if not isinstance(turn_id, str) or not turn_id:
                    self._identity_failure = True
                elif self._turn_id is None:
                    self._turn_id = turn_id
                elif self._turn_id != turn_id:
                    self._identity_failure = True
        elif method == "turn/completed":
            self._complete_turn(params)
        elif method in {"model/rerouted", "error"}:
            self._identity_failure = True
            self._runtime_identity = None

    async def run(self, prompt: str) -> CodexRunResult:
        """Run one fresh thread and promote matches only at a normal checkpoint."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise CodexAdapterFailure("Codex prompt must be a non-empty string.")
        self._reset_run()
        self._emit("starting", "Preparing the bounded task.")
        self._transport = self.transport_factory(self.executable)
        turn_started = False
        error_type: str | None = None
        try:
            self._transport.start()
            if self._transport.version != self.expected_cli_version:
                raise CodexAdapterFailure(
                    "Bundled Codex CLI version identity mismatch."
                )
            self._initialize()
            self._verify_account()
            self._verify_model_catalog()
            self._start_thread()
            self._start_turn(prompt)
            turn_started = True
            while self._turn_status is None:
                self._dispatch(self._receive())
        except (CodexAdapterUnavailable, CodexAdapterFailure) as exc:
            if not turn_started:
                raise
            error_type = type(exc).__name__
        except Exception as exc:
            if not turn_started:
                raise CodexAdapterFailure(
                    "Codex app-server failed before the turn started."
                ) from exc
            error_type = type(exc).__name__
        finally:
            try:
                self._transport.close()
            except Exception:
                if error_type is None and turn_started:
                    error_type = "CodexTransportCloseError"

        if self._identity_failure and error_type is None:
            error_type = "CodexRuntimeIdentityError"
        all_accepted_completed = self._accepted_items.issubset(
            self._completed_items
        )
        normal_terminal = bool(
            self._turn_status == "completed"
            and self._settings_verified
            and all_accepted_completed
            and not self._permission_denied
            and not self._unsupported_mutation
            and not self._identity_failure
            and error_type is None
        )
        checkpoint_by_decision_key: dict[str, CheckpointOutcome] = {}
        checkpoint_values: list[CheckpointOutcome] = []
        for index, (decision_key, outcome) in enumerate(
            self._pending.items(),
            start=1,
        ):
            checkpoint = self.engine.finish_checkpoint(
                outcome,
                normal_terminal=normal_terminal,
                checkpoint_id=(
                    f"codex-turn:{self._run_id}:{index}"
                    if self._turn_status is not None
                    else f"codex-missing-turn:{self._run_id}:{index}"
                ),
            )
            checkpoint_by_decision_key[decision_key] = checkpoint
            checkpoint_values.append(checkpoint)
        checkpoints = tuple(checkpoint_values)
        if self._unsupported_mutation:
            status = "UNSUPPORTED_MUTATION"
        elif checkpoints:
            status = checkpoints[-1].status
        elif self._permission_denied:
            status = "DENIED"
        elif normal_terminal:
            status = "NORMAL_TERMINAL"
        else:
            status = "ABNORMAL_TERMINAL"
        file_actions = self._final_file_actions(
            checkpoint_by_decision_key,
            normal_terminal=normal_terminal,
        )
        return CodexRunResult(
            run_id=self._run_id,
            normal_terminal=normal_terminal,
            status=status,
            error_type=error_type,
            turn_status=self._turn_status,
            runtime_identity=self._runtime_identity,
            checkpoint_outcomes=checkpoints,
            final_message=self._final_message_with_diagnostic(status),
            file_actions=file_actions,
            unsupported_reason=self._unsupported_reason,
        )
