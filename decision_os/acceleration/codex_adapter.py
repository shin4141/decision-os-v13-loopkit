"""Codex app-server adapter for the agent-agnostic Verified Save engine."""

from __future__ import annotations

from collections.abc import Callable
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import threading
from typing import Any, Protocol, TextIO

from .engine import AccelerationEngine, CheckpointOutcome, DecisionOutcome
from .model import DecisionType, ScopeError, git_output, normalize_scope


BUNDLED_CODEX_PATH = Path(
    "/Applications/ChatGPT.app/Contents/Resources/codex"
)
CODEX_CLI_VERSION = "0.146.0-alpha.3.1"

# Cycle 006 is intentionally Forward-only.  Keep the historical/default
# bundled identity above unchanged and bind only the migrated Cycle 006 route
# to this preserved, content-addressed artifact.
CYCLE_006_CODEX_CLI_VERSION = "0.147.0-alpha.1.2"
CYCLE_006_CODEX_SHA256 = (
    "9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481"
)
CYCLE_006_CODEX_PATH = Path(
    "/Users/sn/Library/Application Support/Decision OS Companion/"
    "runtime-artifacts/codex/"
    f"{CYCLE_006_CODEX_SHA256}/codex"
)
CYCLE_006_CODEX_RECOVERY_RECEIPT = CYCLE_006_CODEX_PATH.with_name(
    "recovery-receipt.json"
)
_CYCLE_006_CODEX_MAX_BYTES = 275_653_216

# The current ordinary Companion route advances independently of the
# historical/default identity above. Reuse the already-qualified Forward-only
# artifact and its strict verifier without discovering or trusting a mutable
# executable at runtime.
ORDINARY_COMPANION_CODEX_CLI_VERSION = CYCLE_006_CODEX_CLI_VERSION
ORDINARY_COMPANION_CODEX_SHA256 = CYCLE_006_CODEX_SHA256
ORDINARY_COMPANION_CODEX_PATH = CYCLE_006_CODEX_PATH
CODEX_MODEL = "gpt-5.6-sol"
CODEX_REASONING_EFFORT = "ultra"
CODEX_SERVICE_TIER = "priority"
ADAPTER_NAME = "codex-app-server"

_CLIENT_NAME = "decision_os_verified_save"
_CLIENT_VERSION = "0.1.0"
_DEVELOPER_INSTRUCTIONS = (
    "Perform only the requested bounded file operation. "
    "Do not use shell commands. "
    "Before modifying an existing file, use read_repository_text_file once "
    "for that exact repository-relative path. "
    "Use the typed file-change tool for exactly one file mutation. "
    "The read tool is read-only and cannot authorize a mutation. "
    "Do not mutate files through shell commands, other dynamic tools, or MCP "
    "tools. "
    "Do not touch another path, and stop normally after the requested operation. "
    "Do not reproduce the complete repository source file in the final response. "
    "Report only what was changed, the path, and the bounded completion result."
)
_READ_TOOL_NAME = "read_repository_text_file"
_READ_MAX_BYTES = 131_072
_READ_MAX_DISTINCT_PATHS = 4
_WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[/\\]")
_SOURCE_ECHO_MARKER = "[Repository source content withheld.]"
_FENCE_OPENING = re.compile(
    r"(?m)^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})[^\r\n]*(?P<eol>\r?\n)"
)
_BLANK_LINE_BEFORE = re.compile(r"(?:\r?\n)[ \t]*(?:\r?\n)\Z")
_BLANK_LINE_AFTER = re.compile(r"\A(?:\r?\n)[ \t]*(?:\r?\n)")
_READ_TOOL_SPEC = {
    "type": "function",
    "name": _READ_TOOL_NAME,
    "description": (
        "Read one existing strict UTF-8 text file inside the selected "
        "repository. One bounded Run may read up to four distinct normalized "
        "repository paths; additional calls for an admitted path do not use "
        "another path slot. Modifying an existing file still requires reading "
        "that same path."
    ),
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["path"],
        "properties": {
            "path": {
                "type": "string",
                "minLength": 1,
            }
        },
    },
}


def _runtime_stat_identity(value: os.stat_result) -> tuple[int, ...]:
    """Return fields that must remain stable throughout artifact checking."""

    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _runtime_parent_chain_identity(path: Path) -> tuple[tuple[int, ...], ...]:
    """Reject symlink traversal and bind every directory in the fixed path."""

    identities: list[tuple[int, ...]] = []
    for parent in reversed(path.parents):
        try:
            observed = parent.lstat()
        except OSError as exc:
            raise ValueError("P0_CODEX_CLI_UNAVAILABLE") from exc
        if stat.S_ISLNK(observed.st_mode):
            raise ValueError("P0_CODEX_CLI_SYMLINK")
        if not stat.S_ISDIR(observed.st_mode):
            raise ValueError("P0_CODEX_CLI_UNAVAILABLE")
        identities.append(
            (observed.st_dev, observed.st_ino, observed.st_mode)
        )
    return tuple(identities)


def _verify_cycle_006_codex_runtime_identity(
    executable: Path,
) -> tuple[str, tuple[int, ...]]:
    """Return the version and stable file identity of the fixed artifact.

    The caller supplies a configured path only so a substituted configuration
    can be rejected.  The expected path, full binary digest, and version are
    fixed constants rather than runtime-discovered or PATH-resolved values.
    """

    configured = Path(executable)
    if configured != CYCLE_006_CODEX_PATH:
        raise ValueError("P0_CODEX_CLI_PATH_MISMATCH")
    parent_chain = _runtime_parent_chain_identity(configured)
    try:
        before = configured.lstat()
    except OSError as exc:
        raise ValueError("P0_CODEX_CLI_UNAVAILABLE") from exc
    if stat.S_ISLNK(before.st_mode):
        raise ValueError("P0_CODEX_CLI_SYMLINK")
    if (
        not stat.S_ISREG(before.st_mode)
        or stat.S_IMODE(before.st_mode) != 0o755
    ):
        raise ValueError("P0_CODEX_CLI_NOT_REGULAR_EXECUTABLE")
    if before.st_size > _CYCLE_006_CODEX_MAX_BYTES:
        raise ValueError("P0_CODEX_CLI_SHA256_MISMATCH")

    digest = hashlib.sha256()
    try:
        with configured.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if _runtime_stat_identity(opened) != _runtime_stat_identity(before):
                raise ValueError("P0_CODEX_CLI_IDENTITY_CHANGED")
            while block := stream.read(1024 * 1024):
                digest.update(block)
            after_read = os.fstat(stream.fileno())
    except ValueError:
        raise
    except OSError as exc:
        raise ValueError("P0_CODEX_CLI_UNAVAILABLE") from exc
    if _runtime_stat_identity(after_read) != _runtime_stat_identity(before):
        raise ValueError("P0_CODEX_CLI_IDENTITY_CHANGED")
    if digest.hexdigest() != CYCLE_006_CODEX_SHA256:
        raise ValueError("P0_CODEX_CLI_SHA256_MISMATCH")

    try:
        completed = subprocess.run(
            (str(configured), "--version"),
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("P0_CODEX_CLI_VERSION_PROBE_FAILED") from exc
    if completed.returncode != 0:
        raise ValueError("P0_CODEX_CLI_VERSION_PROBE_FAILED")
    expected_stdout = (
        f"codex-cli {CYCLE_006_CODEX_CLI_VERSION}\n".encode("ascii")
    )
    if completed.stdout != expected_stdout:
        raise ValueError("P0_CODEX_CLI_VERSION_MISMATCH")
    try:
        after_probe = configured.lstat()
    except OSError as exc:
        raise ValueError("P0_CODEX_CLI_IDENTITY_CHANGED") from exc
    if _runtime_stat_identity(after_probe) != _runtime_stat_identity(before):
        raise ValueError("P0_CODEX_CLI_IDENTITY_CHANGED")
    try:
        ending_parent_chain = _runtime_parent_chain_identity(configured)
    except ValueError as exc:
        raise ValueError("P0_CODEX_CLI_IDENTITY_CHANGED") from exc
    if ending_parent_chain != parent_chain:
        raise ValueError("P0_CODEX_CLI_IDENTITY_CHANGED")
    return (
        CYCLE_006_CODEX_CLI_VERSION,
        _runtime_stat_identity(after_probe),
    )


def verify_cycle_006_codex_runtime_artifact(executable: Path) -> str:
    """Verify the sole Forward-only Cycle 006 Codex executable."""

    version, _identity = _verify_cycle_006_codex_runtime_identity(executable)
    return version


def _trailing_line_ending(value: str) -> str:
    if value.endswith("\r\n"):
        return "\r\n"
    if value.endswith("\n"):
        return "\n"
    return ""


def _replace_exact_spans(
    value: str,
    spans: list[tuple[int, int, str]],
) -> str:
    for start, end, replacement in reversed(spans):
        value = f"{value[:start]}{replacement}{value[end:]}"
    return value


def _redact_fenced_source_echo(message: str, source_content: str) -> str:
    spans: list[tuple[int, int, str]] = []
    search_at = 0
    while opening := _FENCE_OPENING.search(message, search_at):
        fence = opening.group("fence")
        closing_pattern = re.compile(
            rf"(?m)^ {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}"
            r"[ \t]*(?:\r?\n|\Z)"
        )
        closing = closing_pattern.search(message, opening.end())
        if closing is None:
            search_at = opening.end()
            continue
        body = message[opening.end() : closing.start()]
        matched = body == source_content
        if not matched:
            matched = any(
                body == f"{source_content}{line_ending}"
                for line_ending in ("\r\n", "\n")
            )
        if matched:
            boundary = _trailing_line_ending(body)
            spans.append(
                (
                    opening.end(),
                    closing.start(),
                    f"{_SOURCE_ECHO_MARKER}{boundary}",
                )
            )
        search_at = closing.end()
    return _replace_exact_spans(message, spans)


def _has_explicit_block_end(source_content: str, suffix: str) -> bool:
    if not suffix:
        return True
    if _BLANK_LINE_AFTER.match(suffix) is not None:
        return True
    return bool(_trailing_line_ending(source_content)) and suffix.startswith(
        ("\r\n", "\n")
    )


def _redact_separate_source_blocks(
    message: str,
    source_content: str,
) -> str:
    if not source_content.strip():
        return message
    spans: list[tuple[int, int, str]] = []
    search_at = 0
    while True:
        start = message.find(source_content, search_at)
        if start < 0:
            break
        end = start + len(source_content)
        prefix = message[:start]
        suffix = message[end:]
        has_start = not prefix or _BLANK_LINE_BEFORE.search(prefix) is not None
        if has_start and _has_explicit_block_end(source_content, suffix):
            spans.append(
                (
                    start,
                    end,
                    f"{_SOURCE_ECHO_MARKER}"
                    f"{_trailing_line_ending(source_content)}",
                )
            )
        search_at = end
    return _replace_exact_spans(message, spans)


def _redact_complete_source_echo(message: str, source_content: str) -> str:
    """Suppress only exact complete-source echoes with explicit structure."""

    if not source_content:
        return message
    search_at = 0
    while True:
        start = message.find(source_content, search_at)
        if start < 0:
            break
        end = start + len(source_content)
        if not message[:start].strip() and not message[end:].strip():
            return _SOURCE_ECHO_MARKER
        search_at = end
    guarded = _redact_fenced_source_echo(message, source_content)
    return _redact_separate_source_blocks(guarded, source_content)


_UNSUPPORTED_ITEM_TYPES = frozenset(
    {
        "collabAgentToolCall",
        "commandExecution",
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
        "modify_requires_repository_read",
        "read_file_not_utf8",
        "read_file_too_large",
        "read_identity_changed",
        "read_path_not_found",
        "read_path_not_regular_file",
        "read_path_outside_repository",
        "read_preimage_changed_before_approval",
        "read_request_identity_mismatch",
        "read_write_path_mismatch",
        "additional_read_target",
        "unsupported_dynamic_tool",
        "unsupported_read_request_shape",
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

_FAILURE_DIAGNOSTIC_SPECS = {
    "input_validation": (
        "codex_input_validation_failed",
        "The bounded Codex task input was rejected safely.",
        "review_bounded_task",
    ),
    "transport_start": (
        "codex_transport_start_failed",
        "The private Codex runtime is unavailable.",
        "recheck_runtime",
    ),
    "version_verification": (
        "codex_version_verification_failed",
        "The bounded Codex Run failed closed while verifying the runtime version.",
        "recheck_runtime",
    ),
    "initialize_handshake": (
        "codex_initialize_handshake_failed",
        "The bounded Codex Run failed closed during runtime initialization.",
        "recheck_runtime",
    ),
    "account_verification": (
        "codex_account_verification_failed",
        "The bounded Codex Run failed closed while verifying authentication.",
        "recheck_runtime",
    ),
    "model_verification": (
        "codex_model_verification_failed",
        "The bounded Codex Run failed closed while verifying the model configuration.",
        "recheck_runtime",
    ),
    "thread_start": (
        "codex_thread_start_failed",
        "The bounded Codex Run failed closed while starting its isolated thread.",
        "recheck_protocol",
    ),
    "thread_identity_verification": (
        "codex_thread_identity_verification_failed",
        "The bounded Codex Run failed closed while verifying the isolated thread.",
        "recheck_protocol",
    ),
    "settings_verification": (
        "codex_settings_verification_failed",
        "The bounded Codex Run failed closed while verifying runtime settings.",
        "recheck_runtime",
    ),
    "turn_start": (
        "codex_turn_start_failed",
        "The bounded Codex Run failed closed while starting the model turn.",
        "recheck_protocol",
    ),
    "turn_started": (
        "codex_turn_identity_failed",
        "The bounded Codex Run failed closed while verifying the started turn.",
        "recheck_protocol",
    ),
    "dynamic_tool_call": (
        "codex_dynamic_tool_call_failed",
        "The bounded Codex Run failed closed while handling the bounded repository read.",
        "review_bounded_read",
    ),
    "file_change_item": (
        "codex_file_change_item_failed",
        "The bounded Codex Run failed closed while verifying a typed file-change item.",
        "review_file_change",
    ),
    "agent_message": (
        "codex_agent_message_failed",
        "The bounded Codex Run failed closed while validating a model response item.",
        "review_terminal_state",
    ),
    "unsupported_item": (
        "codex_unsupported_item_failed",
        "The bounded Codex Run failed closed while validating an unsupported item.",
        "recheck_protocol",
    ),
    "approval_bridge": (
        "codex_approval_bridge_failed",
        "The bounded Codex Run failed closed at the exact Approval boundary.",
        "review_approval_bridge",
    ),
    "terminal_wait": (
        "codex_terminal_wait_failed",
        "The bounded Codex Run failed closed while waiting for terminal completion.",
        "review_terminal_state",
    ),
    "terminal_completion": (
        "codex_terminal_completion_failed",
        "The bounded Codex Run failed closed while verifying terminal completion.",
        "review_terminal_state",
    ),
    "runtime_identity_verification": (
        "codex_runtime_identity_failed",
        "The bounded Codex Run failed closed because runtime identity could not be verified.",
        "recheck_runtime",
    ),
    "protocol_message": (
        "codex_protocol_message_failed",
        "The bounded Codex Run failed closed while validating an app-server message.",
        "recheck_protocol",
    ),
    "finalization": (
        "codex_finalization_failed",
        "The bounded Codex Run failed closed during finalization.",
        "review_terminal_state",
    ),
    "unknown": (
        "codex_unknown_failure",
        "The bounded Codex Run failed closed.",
        None,
    ),
}

_FAILURE_CATEGORIES = frozenset(
    {
        "jsonrpc_method_rejected",
        "jsonrpc_invalid_params",
        "state_or_filesystem",
        "transport_or_process",
        "unknown",
    }
)
_PROTOCOL_METHODS = frozenset(
    {
        "account/read",
        "initialize",
        "model/list",
        "thread/start",
        "turn/start",
    }
)
_PROTOCOL_METHOD_BY_PHASE = {
    "account_verification": "account/read",
    "initialize_handshake": "initialize",
    "model_verification": "model/list",
    "thread_start": "thread/start",
    "turn_start": "turn/start",
}
_STATE_OR_FILESYSTEM_MARKERS = (
    "codex home",
    "database",
    "failed to create",
    "file system",
    "filesystem",
    "no such file",
    "permission denied",
    "read-only file system",
    "sqlite",
    "state directory",
    "unable to create",
)
_INVALID_PARAMS_MARKERS = (
    "deserialize",
    "invalid parameter",
    "invalid params",
    "invalid request",
    "missing field",
    "requires experimentalapi capability",
    "schema",
    "unknown field",
)


def _coherent_failure_evidence(
    protocol_phase: str,
    category: str,
    jsonrpc_code: int | None,
    protocol_method: str | None,
) -> bool:
    if category not in _FAILURE_CATEGORIES:
        return False
    if protocol_method is not None:
        if _PROTOCOL_METHOD_BY_PHASE.get(protocol_phase) != protocol_method:
            return False
    elif jsonrpc_code is not None or category != "unknown":
        return False

    if category == "jsonrpc_method_rejected":
        return jsonrpc_code == -32601
    if category == "jsonrpc_invalid_params":
        return jsonrpc_code in {-32600, -32602}
    if category == "transport_or_process":
        return jsonrpc_code is None and protocol_method is not None
    if category == "state_or_filesystem":
        return bool(
            protocol_method is not None
            and jsonrpc_code not in {-32600, -32601, -32602}
        )
    return jsonrpc_code not in {-32601, -32602}


@dataclass(frozen=True)
class CodexFailureDiagnostic:
    """Bounded public diagnostic for one failed app-server boundary."""

    code: str
    protocol_phase: str
    reason: str
    action: str | None = None
    category: str = "unknown"
    jsonrpc_code: int | None = None
    protocol_method: str | None = None

    def __post_init__(self) -> None:
        spec = _FAILURE_DIAGNOSTIC_SPECS.get(self.protocol_phase)
        bounded_code = bool(
            self.jsonrpc_code is None
            or (
                type(self.jsonrpc_code) is int
                and -(2**63) <= self.jsonrpc_code < 2**63
            )
        )
        bounded_method = bool(
            self.protocol_method is None
            or self.protocol_method in _PROTOCOL_METHODS
        )
        coherent_evidence = _coherent_failure_evidence(
            self.protocol_phase,
            self.category,
            self.jsonrpc_code,
            self.protocol_method,
        )
        if (
            spec != (self.code, self.reason, self.action)
            or not bounded_code
            or not bounded_method
            or not coherent_evidence
        ):
            raise ValueError("Codex failure diagnostic must be bounded.")

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "code": self.code,
            "protocol_phase": self.protocol_phase,
            "reason": self.reason,
            "action": self.action,
            "category": self.category,
            "jsonrpc_code": self.jsonrpc_code,
            "protocol_method": self.protocol_method,
        }

    @classmethod
    def for_phase(cls, protocol_phase: str) -> CodexFailureDiagnostic:
        return _failure_diagnostic(protocol_phase)


def _failure_diagnostic(
    protocol_phase: str,
    *,
    category: str = "unknown",
    jsonrpc_code: int | None = None,
    protocol_method: str | None = None,
) -> CodexFailureDiagnostic:
    phase = (
        protocol_phase
        if protocol_phase in _FAILURE_DIAGNOSTIC_SPECS
        else "unknown"
    )
    code, reason, action = _FAILURE_DIAGNOSTIC_SPECS[phase]
    return CodexFailureDiagnostic(
        code=code,
        protocol_phase=phase,
        reason=reason,
        action=action,
        category=category,
        jsonrpc_code=jsonrpc_code,
        protocol_method=protocol_method,
    )


def _bounded_failure_text_category(value: object) -> str:
    if type(value) is not str:
        return "unknown"
    lowered = value.casefold()
    if "path aliases" in lowered:
        return "unknown"
    if any(marker in lowered for marker in _STATE_OR_FILESYSTEM_MARKERS):
        return "state_or_filesystem"
    if any(marker in lowered for marker in _INVALID_PARAMS_MARKERS):
        return "jsonrpc_invalid_params"
    return "unknown"


def _jsonrpc_failure_diagnostic(
    protocol_phase: str,
    protocol_method: str,
    error: object,
) -> CodexFailureDiagnostic:
    category = "unknown"
    jsonrpc_code: int | None = None
    message: object = None
    if isinstance(error, dict):
        raw_code = error.get("code")
        if type(raw_code) is int and -(2**63) <= raw_code < 2**63:
            jsonrpc_code = raw_code
        message = error.get("message")
    if jsonrpc_code == -32601:
        category = "jsonrpc_method_rejected"
    elif jsonrpc_code == -32602:
        category = "jsonrpc_invalid_params"
    elif jsonrpc_code == -32600:
        classified = _bounded_failure_text_category(message)
        category = (
            classified
            if classified == "jsonrpc_invalid_params"
            else "unknown"
        )
    else:
        category = _bounded_failure_text_category(message)
    if category == "jsonrpc_invalid_params" and jsonrpc_code not in {
        -32600,
        -32602,
    }:
        category = "unknown"
    return _failure_diagnostic(
        protocol_phase,
        category=category,
        jsonrpc_code=jsonrpc_code,
        protocol_method=(
            protocol_method if protocol_method in _PROTOCOL_METHODS else None
        ),
    )


def canonical_failure_diagnostic(value: object) -> CodexFailureDiagnostic:
    """Rebuild one untrusted diagnostic from canonical identifiers only."""

    unknown = _failure_diagnostic("unknown")
    if type(value) is not CodexFailureDiagnostic:
        return unknown
    try:
        code = object.__getattribute__(value, "code")
        protocol_phase = object.__getattribute__(value, "protocol_phase")
        reason = object.__getattribute__(value, "reason")
        action = object.__getattribute__(value, "action")
        category = object.__getattribute__(value, "category")
        jsonrpc_code = object.__getattribute__(value, "jsonrpc_code")
        protocol_method = object.__getattribute__(value, "protocol_method")
    except Exception:
        return unknown
    if (
        type(code) is not str
        or type(protocol_phase) is not str
        or type(reason) is not str
        or (action is not None and type(action) is not str)
        or type(category) is not str
        or (jsonrpc_code is not None and type(jsonrpc_code) is not int)
        or (protocol_method is not None and type(protocol_method) is not str)
    ):
        return unknown
    spec = _FAILURE_DIAGNOSTIC_SPECS.get(protocol_phase)
    if spec != (code, reason, action):
        return unknown
    try:
        return _failure_diagnostic(
            protocol_phase,
            category=category,
            jsonrpc_code=jsonrpc_code,
            protocol_method=protocol_method,
        )
    except ValueError:
        return unknown


class CodexAdapterUnavailable(RuntimeError):
    """The bundled Codex app-server executable is unavailable."""

    def __init__(
        self,
        message: str,
        *,
        diagnostic: CodexFailureDiagnostic | None = None,
    ) -> None:
        super().__init__(message)
        self.diagnostic = (
            None
            if diagnostic is None
            else canonical_failure_diagnostic(diagnostic)
        )


class CodexAdapterFailure(RuntimeError):
    """The app-server contract or bounded run failed before a safe result."""

    def __init__(
        self,
        message: str,
        *,
        diagnostic: CodexFailureDiagnostic | None = None,
    ) -> None:
        super().__init__(message)
        self.diagnostic = (
            None
            if diagnostic is None
            else canonical_failure_diagnostic(diagnostic)
        )


class _ReadValidationError(RuntimeError):
    """One typed repository read was rejected before content disclosure."""

    def __init__(
        self,
        reason: str,
        *,
        path: str | None,
        repository_identity: str | None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.path = path
        self.repository_identity = repository_identity


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
    read_evidence: tuple[CodexReadEvidence, ...] = ()
    unsupported_reason: str | None = None
    failure_diagnostic: CodexFailureDiagnostic | None = None

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
class CodexReadEvidence:
    """Content-free evidence for one bounded repository read attempt."""

    path: str | None
    byte_count: int | None
    sha256: str | None
    repository_identity: str | None
    status: str
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"succeeded", "failed"}:
            raise ValueError("Codex read evidence status is unsupported.")
        if (self.status == "succeeded") != (self.reason is None):
            raise ValueError(
                "Codex read evidence status and reason must agree."
            )
        if self.reason is not None and self.reason not in _UNSUPPORTED_REASON_CODES:
            raise ValueError("Codex read evidence reason must be bounded.")


@dataclass(frozen=True)
class _CodexReadBinding:
    """Exact one-Run binding for one successful dynamic read item."""

    run_id: str
    call_id: str
    normalized_scope: str
    byte_count: int
    sha256: str
    repository_identity: str
    content: str
    arguments_identity: str


@dataclass(frozen=True)
class _CodexReadResponse:
    """One exact app-server response retained for replay verification."""

    call_id: str
    arguments_identity: str
    success: bool
    content_items: tuple[dict[str, str], ...]


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

    @property
    def failure_category(self) -> str:
        """Return one bounded category inferred from private stderr."""

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
        self._failure_category = "unknown"
        self._failure_category_lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._stderr_thread: threading.Thread | None = None

    @property
    def version(self) -> str:
        return self._version

    @property
    def failure_category(self) -> str:
        with self._failure_category_lock:
            return self._failure_category

    def start(self) -> None:
        self._probe_version()
        self._launch()
        self._start_stderr_drain()

    def _probe_version(self) -> None:
        """Read the historical/default transport's CLI identity."""

        if not self.executable.is_file():
            raise CodexAdapterUnavailable(
                f"Bundled Codex executable is unavailable at {self.executable}.",
                diagnostic=_failure_diagnostic("transport_start"),
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
                "Bundled Codex version could not be read.",
                diagnostic=_failure_diagnostic("version_verification"),
            ) from exc
        observed = completed.stdout.strip()
        prefix = "codex-cli "
        if completed.returncode != 0 or not observed.startswith(prefix):
            raise CodexAdapterFailure(
                "Bundled Codex CLI returned an invalid version identity.",
                diagnostic=_failure_diagnostic("version_verification"),
            )
        self._version = observed[len(prefix) :].strip()

    def _launch(self) -> None:
        """Spawn the configured executable without resolving through PATH."""

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
                "Bundled Codex app-server could not be started.",
                diagnostic=_failure_diagnostic("transport_start"),
            ) from exc

    def _start_stderr_drain(self) -> None:
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
            for line in process.stderr:
                category = _bounded_failure_text_category(line)
                if category != "state_or_filesystem":
                    continue
                with self._failure_category_lock:
                    self._failure_category = category
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


class _Cycle006SubprocessTransport(_SubprocessTransport):
    """Strictly bind the fixed Cycle 006 artifact around one exact launch."""

    def _strict_identity(self) -> tuple[str, tuple[int, ...]]:
        try:
            return _verify_cycle_006_codex_runtime_identity(self.executable)
        except ValueError as exc:
            raise CodexAdapterFailure(
                "The fixed Cycle 006 Codex runtime failed artifact verification.",
                diagnostic=_failure_diagnostic("version_verification"),
            ) from exc

    def _current_identity(self) -> tuple[int, ...]:
        try:
            current = self.executable.lstat()
        except OSError as exc:
            raise CodexAdapterFailure(
                "The fixed Cycle 006 Codex runtime changed before launch.",
                diagnostic=_failure_diagnostic("version_verification"),
            ) from exc
        return _runtime_stat_identity(current)

    def start(self) -> None:
        version, verified_identity = self._strict_identity()
        if self._current_identity() != verified_identity:
            raise CodexAdapterFailure(
                "The fixed Cycle 006 Codex runtime changed before launch.",
                diagnostic=_failure_diagnostic("version_verification"),
            )
        self._version = version
        self._launch()
        try:
            post_version, post_identity = self._strict_identity()
            if (
                post_version != version
                or post_identity != verified_identity
                or self._current_identity() != verified_identity
            ):
                raise CodexAdapterFailure(
                    "The fixed Cycle 006 Codex runtime changed during launch.",
                    diagnostic=_failure_diagnostic("version_verification"),
                )
        except Exception:
            self.close()
            raise
        self._start_stderr_drain()


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
        self._read_requests: dict[str | int, str | None] = {}
        self._resolved_read_requests: set[str | int] = set()
        self._read_responses: dict[str, _CodexReadResponse] = {}
        self._read_replay_failures: dict[str, _CodexReadResponse] = {}
        self._read_evidence: list[CodexReadEvidence] = []
        self._read_evidence_keys: set[tuple[str, str, str | None]] = set()
        self._read_bindings: dict[str, _CodexReadBinding] = {}
        self._admitted_read_paths: set[str] = set()
        self._completed_read_items: set[str] = set()
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
        self._protocol_phase = "unknown"
        self._failure_phase: str | None = None

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
        self._read_requests = {}
        self._resolved_read_requests = set()
        self._read_responses = {}
        self._read_replay_failures = {}
        self._read_evidence = []
        self._read_evidence_keys = set()
        self._read_bindings = {}
        self._admitted_read_paths = set()
        self._completed_read_items = set()
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
        self._protocol_phase = "unknown"
        self._failure_phase = None

    def _emit(self, kind: str, message: str) -> None:
        if self.lifecycle_sink is None:
            return
        self.lifecycle_sink(CodexLifecycleEvent(kind=kind, message=message))

    def _latch_failure_phase(self, protocol_phase: str | None = None) -> None:
        if self._failure_phase is not None:
            return
        phase = self._protocol_phase if protocol_phase is None else protocol_phase
        self._failure_phase = (
            phase if phase in _FAILURE_DIAGNOSTIC_SPECS else "unknown"
        )

    def _mark_identity_failure(self) -> None:
        self._latch_failure_phase()
        self._identity_failure = True

    def _latched_failure_diagnostic(self) -> CodexFailureDiagnostic:
        return _failure_diagnostic(self._failure_phase or "unknown")

    def _diagnostic_for_typed_exception(
        self,
        exc: CodexAdapterUnavailable | CodexAdapterFailure,
    ) -> CodexFailureDiagnostic:
        attached = (
            None
            if exc.diagnostic is None
            else canonical_failure_diagnostic(exc.diagnostic)
        )
        if self._failure_phase is None:
            if attached is None:
                self._latch_failure_phase()
            else:
                self._latch_failure_phase(attached.protocol_phase)
        latched = self._latched_failure_diagnostic()
        if (
            attached is not None
            and attached.protocol_phase == latched.protocol_phase
        ):
            return attached
        return latched

    def _transport_failure_category(self) -> str:
        transport = self._transport
        if transport is None:
            return "transport_or_process"
        try:
            category = transport.failure_category
        except (AttributeError, RuntimeError):
            category = "unknown"
        return (
            category
            if category == "state_or_filesystem"
            else "transport_or_process"
        )

    def _send(self, message: dict[str, Any]) -> None:
        if self._transport is None:
            raise CodexAdapterFailure("Codex app-server transport is unavailable.")
        self._transport.send(message)

    def _receive(self) -> dict[str, Any]:
        if self._transport is None:
            raise CodexAdapterFailure("Codex app-server transport is unavailable.")
        return self._transport.receive()

    def _request(self, method: str, params: dict[str, Any]) -> Any:
        request_phase = self._protocol_phase
        self._request_id += 1
        request_id = self._request_id
        try:
            self._send({"id": request_id, "method": method, "params": params})
        except (CodexAdapterUnavailable, CodexAdapterFailure) as exc:
            raise CodexAdapterFailure(
                f"Codex app-server {method} transport failed.",
                diagnostic=_failure_diagnostic(
                    request_phase,
                    category=self._transport_failure_category(),
                    protocol_method=(
                        method if method in _PROTOCOL_METHODS else None
                    ),
                ),
            ) from exc
        while True:
            try:
                message = self._receive()
            except (CodexAdapterUnavailable, CodexAdapterFailure) as exc:
                raise CodexAdapterFailure(
                    f"Codex app-server {method} transport failed.",
                    diagnostic=_failure_diagnostic(
                        request_phase,
                        category=self._transport_failure_category(),
                        protocol_method=(
                            method if method in _PROTOCOL_METHODS else None
                        ),
                    ),
                ) from exc
            if (
                message.get("id") == request_id
                and "method" not in message
            ):
                if "error" in message:
                    raise CodexAdapterFailure(
                        f"Codex app-server {method} request failed.",
                        diagnostic=_jsonrpc_failure_diagnostic(
                            request_phase,
                            method,
                            message.get("error"),
                        ),
                    )
                if "result" not in message:
                    raise CodexAdapterFailure(
                        f"Codex app-server {method} response is incomplete.",
                        diagnostic=_failure_diagnostic(
                            request_phase,
                            protocol_method=(
                                method if method in _PROTOCOL_METHODS else None
                            ),
                        ),
                    )
                return message["result"]
            self._dispatch(message)
            self._protocol_phase = request_phase

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
                    "capabilities": {"experimentalApi": True},
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
                    "dynamicTools": [copy.deepcopy(_READ_TOOL_SPEC)],
                    "ephemeral": True,
                    "model": self.expected_model,
                    "modelProvider": "openai",
                    "sandbox": "read-only",
                    "serviceTier": self.expected_service_tier,
                },
            ),
            "thread/start result",
        )
        self._protocol_phase = "thread_identity_verification"
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
        self._protocol_phase = "settings_verification"
        for params in deferred:
            self._verify_settings(params)
        self._protocol_phase = "thread_identity_verification"

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
        self._latch_failure_phase()
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
        message = self._final_message
        for read_binding in sorted(
            self._read_bindings.values(),
            key=lambda value: len(value.content),
            reverse=True,
        ):
            message = _redact_complete_source_echo(
                message,
                read_binding.content,
            )
        if (
            status != "UNSUPPORTED_MUTATION"
            or self._unsupported_reason is None
        ):
            return message
        diagnostic = (
            "Decision OS verification: not verified "
            f"({self._unsupported_reason})."
        )
        separator = "\n\n" if message else ""
        return f"{message}{separator}{diagnostic}"

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

    @staticmethod
    def _arguments_identity(arguments: dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(
                arguments,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _read_content_item(payload: dict[str, Any]) -> tuple[dict[str, str], ...]:
        return (
            {
                "type": "inputText",
                "text": json.dumps(
                    payload,
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            },
        )

    def _record_read_evidence(
        self,
        evidence: CodexReadEvidence,
        *,
        call_id: str | None = None,
    ) -> None:
        if call_id is None:
            if evidence not in self._read_evidence:
                self._read_evidence.append(evidence)
            return
        key = (call_id, evidence.status, evidence.reason)
        if key not in self._read_evidence_keys:
            self._read_evidence_keys.add(key)
            self._read_evidence.append(evidence)

    def _read_failure_response(
        self,
        *,
        call_id: str,
        arguments_identity: str,
        reason: str,
        path: str | None,
        repository_identity: str | None,
    ) -> _CodexReadResponse:
        self._mark_unsupported(reason)
        evidence = CodexReadEvidence(
            path=path,
            byte_count=None,
            sha256=None,
            repository_identity=repository_identity,
            status="failed",
            reason=reason,
        )
        self._record_read_evidence(evidence, call_id=call_id)
        return _CodexReadResponse(
            call_id=call_id,
            arguments_identity=arguments_identity,
            success=False,
            content_items=self._read_content_item(
                {
                    "bytes": None,
                    "path": path,
                    "reason": reason,
                    "repository_identity": repository_identity,
                    "sha256": None,
                    "status": "failed",
                }
            ),
        )

    def _normalized_read_path(self, raw_path: str) -> str:
        candidate = raw_path.strip()
        if (
            not candidate
            or "\x00" in candidate
            or "\\" in candidate
            or Path(candidate).is_absolute()
            or _WINDOWS_ABSOLUTE_PATH.match(candidate) is not None
        ):
            raise _ReadValidationError(
                "read_path_outside_repository",
                path=None,
                repository_identity=None,
            )
        parts: list[str] = []
        for part in candidate.split("/"):
            if part in {"", "."}:
                continue
            if part == ".." or part.casefold() == ".git":
                raise _ReadValidationError(
                    "read_path_outside_repository",
                    path=None,
                    repository_identity=None,
                )
            parts.append(part)
        if not parts:
            raise _ReadValidationError(
                "read_path_outside_repository",
                path=None,
                repository_identity=None,
            )
        return "/".join(parts)

    def _read_repository_file(
        self,
        raw_path: str,
    ) -> tuple[str, bytes, str, str]:
        normalized = self._normalized_read_path(raw_path)
        repository = self.engine.store.repository.resolve(strict=True)
        try:
            repository_identity = git_output(
                repository,
                "rev-parse",
                "HEAD^{commit}",
            )
        except Exception as exc:
            raise CodexAdapterFailure(
                "Selected repository identity is unavailable."
            ) from exc
        target = repository.joinpath(*normalized.split("/"))
        try:
            resolved = target.resolve(strict=True)
        except FileNotFoundError as exc:
            raise _ReadValidationError(
                "read_path_not_found",
                path=normalized,
                repository_identity=repository_identity,
            ) from exc
        except (OSError, RuntimeError) as exc:
            raise _ReadValidationError(
                "read_path_not_regular_file",
                path=normalized,
                repository_identity=repository_identity,
            ) from exc
        try:
            relative_resolved = resolved.relative_to(repository)
        except ValueError as exc:
            raise _ReadValidationError(
                "read_path_outside_repository",
                path=None,
                repository_identity=repository_identity,
            ) from exc
        if any(part.casefold() == ".git" for part in relative_resolved.parts):
            raise _ReadValidationError(
                "read_path_outside_repository",
                path=None,
                repository_identity=repository_identity,
            )
        try:
            with resolved.open("rb") as handle:
                before = os.fstat(handle.fileno())
                if not stat.S_ISREG(before.st_mode):
                    raise _ReadValidationError(
                        "read_path_not_regular_file",
                        path=normalized,
                        repository_identity=repository_identity,
                    )
                if before.st_size > _READ_MAX_BYTES:
                    raise _ReadValidationError(
                        "read_file_too_large",
                        path=normalized,
                        repository_identity=repository_identity,
                    )
                data = handle.read(_READ_MAX_BYTES + 1)
                after = os.fstat(handle.fileno())
        except _ReadValidationError:
            raise
        except (OSError, ValueError) as exc:
            raise _ReadValidationError(
                "read_path_not_regular_file",
                path=normalized,
                repository_identity=repository_identity,
            ) from exc
        if len(data) > _READ_MAX_BYTES:
            raise _ReadValidationError(
                "read_file_too_large",
                path=normalized,
                repository_identity=repository_identity,
            )
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        if before_identity != after_identity:
            raise _ReadValidationError(
                "read_identity_changed",
                path=normalized,
                repository_identity=repository_identity,
            )
        try:
            content = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise _ReadValidationError(
                "read_file_not_utf8",
                path=normalized,
                repository_identity=repository_identity,
            ) from exc
        if (
            git_output(repository, "rev-parse", "HEAD^{commit}")
            != repository_identity
        ):
            raise _ReadValidationError(
                "read_identity_changed",
                path=normalized,
                repository_identity=repository_identity,
            )
        return normalized, data, content, repository_identity

    def _send_read_response(
        self,
        request_id: str | int,
        response: _CodexReadResponse,
    ) -> None:
        self._send(
            {
                "id": request_id,
                "result": {
                    "contentItems": [dict(item) for item in response.content_items],
                    "success": response.success,
                },
            }
        )
        # Dynamic tool calls resolve with the client response itself; app-server
        # proceeds directly to item/completed without a resolved notification.
        if (
            isinstance(request_id, (str, int))
            and not isinstance(request_id, bool)
        ):
            self._resolved_read_requests.add(request_id)

    def _respond_read_tool_call(self, message: dict[str, Any]) -> None:
        request_id = message.get("id")
        params = self._require_object(
            message.get("params"),
            "dynamic read parameters",
        )
        call_id = params.get("callId")
        arguments = params.get("arguments")
        valid_request_id = (
            isinstance(request_id, (str, int))
            and not isinstance(request_id, bool)
        )
        safe_call_id = call_id if isinstance(call_id, str) else "invalid-read"
        safe_arguments = arguments if isinstance(arguments, dict) else {}
        arguments_identity = self._arguments_identity(safe_arguments)
        if valid_request_id and request_id in self._read_requests:
            if self._read_requests[request_id] != call_id:
                response = self._read_failure_response(
                    call_id=safe_call_id,
                    arguments_identity=arguments_identity,
                    reason="read_request_identity_mismatch",
                    path=None,
                    repository_identity=None,
                )
                self._send_read_response(request_id, response)
                return
        elif valid_request_id:
            self._read_requests[request_id] = (
                call_id if isinstance(call_id, str) else None
            )
        else:
            response = self._read_failure_response(
                call_id=safe_call_id,
                arguments_identity=arguments_identity,
                reason="read_request_identity_mismatch",
                path=None,
                repository_identity=None,
            )
            self._send_read_response(request_id, response)
            return

        item = self._items.get(safe_call_id)
        valid_shape = bool(
            set(params).issubset(
                {"arguments", "callId", "namespace", "threadId", "tool", "turnId"}
            )
            and set(params) >= {"arguments", "callId", "threadId", "tool", "turnId"}
            and isinstance(call_id, str)
            and bool(call_id)
            and isinstance(arguments, dict)
            and set(arguments) == {"path"}
            and isinstance(arguments.get("path"), str)
            and params.get("tool") == _READ_TOOL_NAME
            and params.get("namespace") is None
            and self._ids_match(params)
            and self._settings_verified
            and item is not None
            and item.get("type") == "dynamicToolCall"
            and item.get("tool") == _READ_TOOL_NAME
            and item.get("namespace") is None
            and item.get("arguments") == arguments
        )
        if not valid_shape:
            reason = (
                "unsupported_dynamic_tool"
                if params.get("tool") != _READ_TOOL_NAME
                else "unsupported_read_request_shape"
            )
            response = self._read_failure_response(
                call_id=safe_call_id,
                arguments_identity=arguments_identity,
                reason=reason,
                path=None,
                repository_identity=None,
            )
            if safe_call_id in self._read_responses:
                self._read_replay_failures[safe_call_id] = response
            else:
                self._read_responses[safe_call_id] = response
            self._send_read_response(request_id, response)
            return

        assert isinstance(call_id, str)
        assert isinstance(arguments, dict)
        existing = self._read_responses.get(call_id)
        if existing is not None:
            if existing.arguments_identity != arguments_identity:
                response = self._read_failure_response(
                    call_id=call_id,
                    arguments_identity=arguments_identity,
                    reason="read_request_identity_mismatch",
                    path=None,
                    repository_identity=None,
                )
                self._send_read_response(request_id, response)
                return
            replay_failure = self._read_replay_failures.get(call_id)
            if replay_failure is not None:
                self._send_read_response(request_id, replay_failure)
                return
            if existing.success:
                binding = self._read_bindings.get(call_id)
                try:
                    current = self._read_repository_file(arguments["path"])
                except (CodexAdapterFailure, _ReadValidationError):
                    current = None
                if (
                    binding is None
                    or binding.call_id != call_id
                    or current is None
                    or current[0] != binding.normalized_scope
                    or current[1] != binding.content.encode("utf-8")
                    or hashlib.sha256(current[1]).hexdigest() != binding.sha256
                    or current[3] != binding.repository_identity
                ):
                    response = self._read_failure_response(
                        call_id=call_id,
                        arguments_identity=arguments_identity,
                        reason="read_identity_changed",
                        path=(binding.normalized_scope if binding else None),
                        repository_identity=(
                            binding.repository_identity if binding else None
                        ),
                    )
                    self._read_replay_failures[call_id] = response
                    self._send_read_response(request_id, response)
                    return
            self._send_read_response(request_id, existing)
            return

        try:
            requested_path = self._normalized_read_path(arguments["path"])
        except _ReadValidationError as exc:
            response = self._read_failure_response(
                call_id=call_id,
                arguments_identity=arguments_identity,
                reason=exc.reason,
                path=exc.path,
                repository_identity=exc.repository_identity,
            )
            self._read_responses[call_id] = response
            self._send_read_response(request_id, response)
            return

        is_new_path = requested_path not in self._admitted_read_paths
        if (
            is_new_path
            and len(self._admitted_read_paths) >= _READ_MAX_DISTINCT_PATHS
        ):
            response = self._read_failure_response(
                call_id=call_id,
                arguments_identity=arguments_identity,
                reason="additional_read_target",
                path=requested_path,
                repository_identity=None,
            )
            self._read_responses[call_id] = response
            self._send_read_response(request_id, response)
            return

        if is_new_path:
            self._admitted_read_paths.add(requested_path)

        try:
            normalized, data, content, repository_identity = (
                self._read_repository_file(requested_path)
            )
        except _ReadValidationError as exc:
            response = self._read_failure_response(
                call_id=call_id,
                arguments_identity=arguments_identity,
                reason=exc.reason,
                path=exc.path,
                repository_identity=exc.repository_identity,
            )
            self._read_responses[call_id] = response
            self._send_read_response(request_id, response)
            return
        except CodexAdapterFailure:
            response = self._read_failure_response(
                call_id=call_id,
                arguments_identity=arguments_identity,
                reason="read_request_identity_mismatch",
                path=None,
                repository_identity=None,
            )
            self._read_responses[call_id] = response
            self._send_read_response(request_id, response)
            return
        digest = hashlib.sha256(data).hexdigest()
        prior_binding = next(
            (
                binding
                for binding in self._read_bindings.values()
                if binding.normalized_scope == normalized
            ),
            None,
        )
        if prior_binding is not None and (
            data != prior_binding.content.encode("utf-8")
            or digest != prior_binding.sha256
            or repository_identity != prior_binding.repository_identity
        ):
            response = self._read_failure_response(
                call_id=call_id,
                arguments_identity=arguments_identity,
                reason="read_identity_changed",
                path=normalized,
                repository_identity=prior_binding.repository_identity,
            )
            self._read_responses[call_id] = response
            self._send_read_response(request_id, response)
            return
        binding = _CodexReadBinding(
            run_id=self._run_id,
            call_id=call_id,
            normalized_scope=normalized,
            byte_count=len(data),
            sha256=digest,
            repository_identity=repository_identity,
            content=content,
            arguments_identity=arguments_identity,
        )
        response = _CodexReadResponse(
            call_id=call_id,
            arguments_identity=arguments_identity,
            success=True,
            content_items=self._read_content_item(
                {
                    "bytes": len(data),
                    "content": content,
                    "path": normalized,
                    "repository_identity": repository_identity,
                    "sha256": digest,
                }
            ),
        )
        self._read_bindings[call_id] = binding
        self._read_responses[call_id] = response
        self._record_read_evidence(
            CodexReadEvidence(
                path=normalized,
                byte_count=len(data),
                sha256=digest,
                repository_identity=repository_identity,
                status="succeeded",
            ),
            call_id=call_id,
        )
        self._send_read_response(request_id, response)

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

        if decision_type is DecisionType.MODIFY_FILE:
            matching_bindings = tuple(
                binding
                for binding in self._read_bindings.values()
                if binding.normalized_scope == normalized
            )
            read_binding = next(
                (
                    binding
                    for binding in reversed(matching_bindings)
                    if binding.run_id == self._run_id
                    and binding.call_id in self._completed_read_items
                ),
                None,
            )
            if not self._read_bindings or (
                matching_bindings and read_binding is None
            ):
                reason = "modify_requires_repository_read"
            elif not matching_bindings:
                reason = "read_write_path_mismatch"
            else:
                assert read_binding is not None
                try:
                    current = self._read_repository_file(normalized)
                except (CodexAdapterFailure, _ReadValidationError):
                    current = None
                if (
                    current is None
                    or current[0] != read_binding.normalized_scope
                    or hashlib.sha256(current[1]).hexdigest()
                    != read_binding.sha256
                    or current[3] != read_binding.repository_identity
                ):
                    reason = "read_preimage_changed_before_approval"
                else:
                    reason = None
            if reason is not None:
                self._mark_unsupported(reason)
                self._declined_items.add(item_id)
                self._record_read_evidence(
                    CodexReadEvidence(
                        path=(
                            read_binding.normalized_scope
                            if read_binding is not None
                            else normalized
                        ),
                        byte_count=None,
                        sha256=None,
                        repository_identity=(
                            read_binding.repository_identity
                            if read_binding is not None
                            else None
                        ),
                        status="failed",
                        reason=reason,
                    )
                )
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
            self._mark_identity_failure()
            return
        request_id = params.get("requestId")
        if (
            not isinstance(request_id, (str, int))
            or isinstance(request_id, bool)
        ):
            self._mark_identity_failure()
            return
        is_approval = request_id in self._approval_requests
        is_read = request_id in self._read_requests
        if is_approval == is_read:
            self._mark_identity_failure()
            return
        if is_read:
            if request_id in self._resolved_read_requests:
                return
            self._resolved_read_requests.add(request_id)
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
            self._mark_identity_failure()
            return
        item = self._require_object(params.get("item"), "started item")
        item_type = item.get("type")
        if item_type in _UNSUPPORTED_ITEM_TYPES:
            self._mark_unsupported(
                f"unsupported_item_type:{item_type}"
            )
            return
        if item_type not in {"dynamicToolCall", "fileChange"}:
            return
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            self._mark_identity_failure()
            return
        if item_type == "dynamicToolCall":
            arguments = item.get("arguments")
            if (
                item.get("tool") != _READ_TOOL_NAME
                or item.get("namespace") is not None
                or item.get("status") != "inProgress"
                or not isinstance(arguments, dict)
                or set(arguments) != {"path"}
                or not isinstance(arguments.get("path"), str)
            ):
                self._mark_unsupported("unsupported_dynamic_tool")
                return
        if item_id in self._items:
            if self._items[item_id] != item:
                self._mark_identity_failure()
            return
        self._items[item_id] = item

    def _update_patch(self, params: dict[str, Any]) -> None:
        if not self._ids_match(params):
            self._mark_identity_failure()
            return
        item_id = params.get("itemId")
        changes = params.get("changes")
        if (
            not isinstance(item_id, str)
            or item_id not in self._items
            or not isinstance(changes, list)
        ):
            self._mark_identity_failure()
            return
        if item_id in self._approved_changes:
            self._mark_identity_failure()
            return
        updated = dict(self._items[item_id])
        updated["changes"] = changes
        self._items[item_id] = updated

    def _complete_item(self, params: dict[str, Any]) -> None:
        if not self._ids_match(params):
            self._mark_identity_failure()
            return
        item = self._require_object(params.get("item"), "completed item")
        item_type = item.get("type")
        if item_type in _UNSUPPORTED_ITEM_TYPES:
            self._mark_unsupported(
                f"unsupported_item_type:{item_type}"
            )
            return
        if item_type == "dynamicToolCall":
            item_id = item.get("id")
            response = None
            if isinstance(item_id, str):
                response = (
                    self._read_replay_failures.get(item_id)
                    or self._read_responses.get(item_id)
                )
            started = (
                self._items.get(item_id)
                if isinstance(item_id, str)
                else None
            )
            resolved = any(
                request_id in self._resolved_read_requests
                and request_item_id == item_id
                for request_id, request_item_id in self._read_requests.items()
            )
            expected_status = (
                "completed" if response is not None and response.success else "failed"
            )
            if (
                response is None
                or started is None
                or item.get("tool") != _READ_TOOL_NAME
                or item.get("namespace") is not None
                or item.get("arguments") != started.get("arguments")
                or self._arguments_identity(item.get("arguments", {}))
                != response.arguments_identity
                or item.get("status") != expected_status
                or (
                    "success" in item
                    and item.get("success") is not response.success
                )
                or (
                    "contentItems" in item
                    and item.get("contentItems")
                    != [dict(value) for value in response.content_items]
                )
                or not resolved
            ):
                self._mark_identity_failure()
                return
            self._completed_read_items.add(item_id)
            return
        if item_type == "agentMessage":
            text = item.get("text")
            phase = item.get("phase")
            if (
                not isinstance(text, str)
                or phase not in {None, "final_answer", "commentary"}
            ):
                self._mark_identity_failure()
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
                self._mark_identity_failure()
            return
        if item_id not in self._accepted_items:
            self._mark_unsupported("unapproved_file_completion")
            self._mark_identity_failure()
            return
        approved = self._approved_changes.get(item_id)
        if item_id in self._completed_items:
            if (
                item.get("status") != "completed"
                or approved is None
                or item.get("changes") != approved
                or item_id not in self._resolved_items
            ):
                self._mark_identity_failure()
            return
        if (
            item.get("status") != "completed"
            or approved is None
            or item.get("changes") != approved
            or item_id not in self._resolved_items
        ):
            self._mark_identity_failure()
            return
        self._completed_items.add(item_id)

    def _invalidate_runtime_identity(self) -> None:
        self._mark_identity_failure()
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
            self._mark_identity_failure()
            return
        turn = self._require_object(params.get("turn"), "completed turn")
        turn_id = turn.get("id")
        if not isinstance(turn_id, str) or not turn_id:
            self._mark_identity_failure()
            return
        if self._turn_id is None:
            self._turn_id = turn_id
        elif turn_id != self._turn_id:
            self._mark_identity_failure()
            return
        status = turn.get("status")
        if not isinstance(status, str):
            self._mark_identity_failure()
            return
        self._turn_status = status
        self._emit("finalizing", "Finalizing the local Receipt.")

    def _notification_protocol_phase(
        self,
        method: str,
        message: dict[str, Any],
    ) -> str:
        if method == "item/fileChange/patchUpdated":
            return "file_change_item"
        if method in {"item/started", "item/completed"}:
            params = message.get("params")
            item = params.get("item") if isinstance(params, dict) else None
            item_type = item.get("type") if isinstance(item, dict) else None
            if item_type == "dynamicToolCall":
                return "dynamic_tool_call"
            if item_type == "agentMessage":
                return "agent_message"
            if item_type == "fileChange":
                return "file_change_item"
            if item_type in _UNSUPPORTED_ITEM_TYPES:
                return "unsupported_item"
            return "protocol_message"
        if method == "serverRequest/resolved":
            params = message.get("params")
            request_id = (
                params.get("requestId") if isinstance(params, dict) else None
            )
            if request_id in self._read_requests:
                return "dynamic_tool_call"
            if request_id in self._approval_requests:
                return "approval_bridge"
            return "protocol_message"
        return {
            "thread/settings/updated": "settings_verification",
            "turn/started": "turn_started",
            "turn/completed": "terminal_completion",
            "model/rerouted": "runtime_identity_verification",
            "error": "protocol_message",
        }.get(method, "protocol_message")

    def _dispatch(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        if not isinstance(method, str):
            self._protocol_phase = "protocol_message"
            raise CodexAdapterFailure(
                "Codex app-server emitted an uncorrelated response."
            )
        if "id" in message:
            if method == "item/fileChange/requestApproval":
                self._protocol_phase = "approval_bridge"
                self._respond_file_approval(message)
            elif method == "item/tool/call":
                self._protocol_phase = "dynamic_tool_call"
                self._respond_read_tool_call(message)
            else:
                self._protocol_phase = "protocol_message"
                self._respond_unsupported_request(message)
            return
        self._protocol_phase = self._notification_protocol_phase(
            method,
            message,
        )
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
                self._mark_identity_failure()
            else:
                turn = self._require_object(
                    params.get("turn"),
                    "started turn",
                )
                turn_id = turn.get("id")
                if not isinstance(turn_id, str) or not turn_id:
                    self._mark_identity_failure()
                elif self._turn_id is None:
                    self._turn_id = turn_id
                elif self._turn_id != turn_id:
                    self._mark_identity_failure()
        elif method == "turn/completed":
            self._complete_turn(params)
        elif method in {"model/rerouted", "error"}:
            self._mark_identity_failure()
            self._runtime_identity = None

    async def run(self, prompt: str) -> CodexRunResult:
        """Run one fresh thread and promote matches only at a normal checkpoint."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise CodexAdapterFailure(
                "Codex prompt must be a non-empty string.",
                diagnostic=_failure_diagnostic("input_validation"),
            )
        self._reset_run()
        self._emit("starting", "Preparing the bounded task.")
        self._transport = self.transport_factory(self.executable)
        turn_started = False
        error_type: str | None = None
        failure_diagnostic: CodexFailureDiagnostic | None = None
        try:
            self._protocol_phase = "transport_start"
            self._transport.start()
            self._protocol_phase = "version_verification"
            if self._transport.version != self.expected_cli_version:
                raise CodexAdapterFailure(
                    "Bundled Codex CLI version identity mismatch."
                )
            self._protocol_phase = "initialize_handshake"
            self._initialize()
            self._protocol_phase = "account_verification"
            self._verify_account()
            self._protocol_phase = "model_verification"
            self._verify_model_catalog()
            self._protocol_phase = "thread_start"
            self._start_thread()
            self._protocol_phase = "turn_start"
            self._start_turn(prompt)
            turn_started = True
            while self._turn_status is None:
                self._protocol_phase = "terminal_wait"
                self._dispatch(self._receive())
        except (CodexAdapterUnavailable, CodexAdapterFailure) as exc:
            failure_diagnostic = self._diagnostic_for_typed_exception(exc)
            exc.diagnostic = failure_diagnostic
            if not turn_started:
                raise
            error_type = type(exc).__name__
        except Exception as exc:
            self._latch_failure_phase("unknown")
            failure_diagnostic = self._latched_failure_diagnostic()
            if not turn_started:
                raise CodexAdapterFailure(
                    "Codex app-server failed before the turn started.",
                    diagnostic=failure_diagnostic,
                ) from exc
            error_type = type(exc).__name__
        finally:
            try:
                self._protocol_phase = "finalization"
                self._transport.close()
            except Exception:
                if error_type is None and turn_started:
                    error_type = "CodexTransportCloseError"
                    self._latch_failure_phase("finalization")
                    failure_diagnostic = self._latched_failure_diagnostic()

        if self._identity_failure and error_type is None:
            error_type = "CodexRuntimeIdentityError"
            if self._failure_phase is None:
                self._latch_failure_phase(
                    "settings_verification"
                    if not self._settings_verified
                    else "runtime_identity_verification"
                )
            failure_diagnostic = self._latched_failure_diagnostic()
        all_accepted_completed = self._accepted_items.issubset(
            self._completed_items
        )
        successful_read_items = {
            call_id
            for call_id, response in self._read_responses.items()
            if response.success
        }
        all_reads_completed = successful_read_items.issubset(
            self._completed_read_items
        )
        normal_terminal = bool(
            self._turn_status == "completed"
            and self._settings_verified
            and all_accepted_completed
            and all_reads_completed
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
            read_evidence=tuple(self._read_evidence),
            unsupported_reason=self._unsupported_reason,
            failure_diagnostic=failure_diagnostic,
        )
