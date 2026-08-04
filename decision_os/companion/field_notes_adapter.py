"""Same-Run one-shot Field Notes proposal extension for the Codex adapter."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace
import hashlib
import json
from typing import Any, Callable, Mapping

from decision_os.acceleration import codex_adapter as codex
from decision_os.acceleration.codex_adapter import (
    CodexAdapter,
    CodexRunResult,
    CodexRuntimeIdentity,
)
from decision_os.companion.field_notes_model import (
    FIELD_NOTE_TOOL_NAME,
    FieldNoteDraft,
    FieldNoteProposalGate,
    canonical_json,
    configured_model_class,
    field_note_tool_spec_for_trust,
)
from decision_os.companion.field_notes_reconnect import (
    FieldNoteReconnectPlan,
    FieldNoteReconnectReceipt,
    prepare_field_note_reconnect,
)


_FIELD_NOTE_PROPOSAL_INSTRUCTIONS = (
    " You may optionally call propose_field_note_candidate "
    "once inside this same Run after identifying one bounded "
    "reusable insight. The proposal tool is side-effect-free. "
    "Do not emit raw Field Note JSON or Markdown and do not "
    "call it twice."
)

_CREATOR_LIVE_A1_CAPTURE_INSTRUCTIONS = (
    "This is a bounded creator-live A1 capture Run. Perform only the "
    "requested bounded reasoning task in read-only mode. Do not use shell "
    "commands. Use read_repository_text_file only for bounded repository "
    "evidence needed by the task. You must call "
    "propose_field_note_candidate exactly once with the reusable insight. "
    "The proposal tool is the only capture path. Do not create, update, "
    "modify, delete, patch, or otherwise write any repository file. Do not emit "
    "the candidate as raw Markdown or JSON. Stop normally after the one "
    "proposal call and the bounded read-only task."
)

_DIRECT_MUTATION_REASONS = frozenset(
    {
        "additional_file_action_item",
        "duplicate_file_action_item_after_completion",
        "modify_requires_repository_read",
        "read_preimage_changed_before_approval",
        "read_write_path_mismatch",
        "unapproved_file_completion",
        "unsupported_dynamic_tool",
        "unsupported_file_change_shape",
        "unsupported_request_method:other",
        "unsupported_request_method:commandExecution",
        "unsupported_item_type:commandExecution",
        "unsupported_item_type:mcpToolCall",
    }
)

_A1_PROPOSAL_DIAGNOSTIC_SCHEMA = (
    "decision-os.field-note-a1-proposal-diagnostic.v0.1"
)
_A1_PROPOSAL_SUBCAUSES = frozenset(
    {
        "A1_PROPOSAL_REQUEST_SHAPE_INVALID",
        "A1_PROPOSAL_SCHEMA_REJECTED",
        "A1_PROPOSAL_GATE_REJECTED",
        "A1_PROPOSAL_ITEM_NOT_COMPLETED",
        "A1_PROPOSAL_ITEM_STATUS_MISMATCH",
        "A1_PROPOSAL_RESPONSE_IDENTITY_MISMATCH",
        "A1_PROPOSAL_INCONSISTENT_REPLAY",
        "A1_PROPOSAL_PROTOCOL_IDENTITY_FAILURE",
        "A1_PROPOSAL_ACCEPTED_STATE_MISSING",
        "A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE",
        "A1_PROPOSAL_MISSING",
        "A1_PROPOSAL_DUPLICATE",
        "A1_DIRECT_WRITE_REQUESTED",
    }
)


def _optional_sha256(value: str | None, label: str) -> None:
    if value is not None and (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} is invalid.")


@dataclass(frozen=True)
class FieldNoteA1ProposalDiagnostic:
    """Payload-free lifecycle facts for one future creator-live A1 proposal."""

    proposal_call_count: int
    call_identity_sha256: str | None
    request_identity_sha256: str | None
    arguments_identity_sha256: str | None
    request_shape_valid: bool | None
    malformed_observed: bool
    gate_invoked: bool
    gate_response_code: str | None
    gate_response_success: bool | None
    accepted_proposal_present: bool
    item_start_observed: bool
    item_completion_observed: bool
    item_observed_status: str | None
    item_expected_status: str | None
    all_proposals_completed: bool
    request_identity_mismatch: bool
    response_identity_mismatch: bool
    inconsistent_replay: bool
    protocol_identity_failure: bool
    protocol_failure_phase: str | None
    direct_write_identity: str | None
    final_subcause: str | None
    schema: str = field(
        default=_A1_PROPOSAL_DIAGNOSTIC_SCHEMA,
        init=False,
    )
    diagnostic_sha256: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if (
            type(self.proposal_call_count) is not int
            or self.proposal_call_count < 0
            or self.schema != _A1_PROPOSAL_DIAGNOSTIC_SCHEMA
            or (
                self.request_shape_valid is not None
                and type(self.request_shape_valid) is not bool
            )
            or (
                self.gate_response_success is not None
                and type(self.gate_response_success) is not bool
            )
            or any(
                type(value) is not bool
                for value in (
                    self.malformed_observed,
                    self.gate_invoked,
                    self.accepted_proposal_present,
                    self.item_start_observed,
                    self.item_completion_observed,
                    self.all_proposals_completed,
                    self.request_identity_mismatch,
                    self.response_identity_mismatch,
                    self.inconsistent_replay,
                    self.protocol_identity_failure,
                )
            )
            or any(
                value is not None
                and (
                    not isinstance(value, str)
                    or not value
                    or len(value) > 128
                )
                for value in (
                    self.gate_response_code,
                    self.item_observed_status,
                    self.item_expected_status,
                    self.protocol_failure_phase,
                )
            )
            or self.final_subcause not in _A1_PROPOSAL_SUBCAUSES | {None}
            or (
                self.protocol_identity_failure
                != (self.protocol_failure_phase is not None)
            )
            or (not self.gate_invoked and self.gate_response_code is not None)
            or (not self.gate_invoked and self.gate_response_success is not None)
        ):
            raise ValueError("A1 proposal diagnostic is invalid.")
        _optional_sha256(self.call_identity_sha256, "Proposal call identity")
        _optional_sha256(
            self.request_identity_sha256,
            "Proposal request identity",
        )
        _optional_sha256(
            self.arguments_identity_sha256,
            "Proposal arguments identity",
        )
        _optional_sha256(
            self.direct_write_identity,
            "Direct-write identity",
        )
        object.__setattr__(
            self,
            "diagnostic_sha256",
            hashlib.sha256(
                canonical_json(self._body()).encode("utf-8")
            ).hexdigest(),
        )

    def _body(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "proposal_call_count": self.proposal_call_count,
            "call_identity_sha256": self.call_identity_sha256,
            "request_identity_sha256": self.request_identity_sha256,
            "arguments_identity_sha256": self.arguments_identity_sha256,
            "request_shape_valid": self.request_shape_valid,
            "malformed_observed": self.malformed_observed,
            "gate_invoked": self.gate_invoked,
            "gate_response_code": self.gate_response_code,
            "gate_response_success": self.gate_response_success,
            "accepted_proposal_present": self.accepted_proposal_present,
            "item_start_observed": self.item_start_observed,
            "item_completion_observed": self.item_completion_observed,
            "item_observed_status": self.item_observed_status,
            "item_expected_status": self.item_expected_status,
            "all_proposals_completed": self.all_proposals_completed,
            "request_identity_mismatch": self.request_identity_mismatch,
            "response_identity_mismatch": self.response_identity_mismatch,
            "inconsistent_replay": self.inconsistent_replay,
            "protocol_identity_failure": self.protocol_identity_failure,
            "protocol_failure_phase": self.protocol_failure_phase,
            "direct_write_identity": self.direct_write_identity,
            "final_subcause": self.final_subcause,
        }

    def as_dict(self) -> dict[str, Any]:
        return {**self._body(), "diagnostic_sha256": self.diagnostic_sha256}

    @classmethod
    def from_dict(cls, value: Any) -> FieldNoteA1ProposalDiagnostic:
        if not isinstance(value, dict):
            raise ValueError("A1 proposal diagnostic must be an object.")
        expected = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        if set(value) != expected:
            raise ValueError("A1 proposal diagnostic fields are invalid.")
        digest = value.get("diagnostic_sha256")
        try:
            diagnostic = cls(
                **{
                    key: item
                    for key, item in value.items()
                    if key not in {"schema", "diagnostic_sha256"}
                }
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("A1 proposal diagnostic is invalid.") from exc
        if value.get("schema") != diagnostic.schema or (
            digest != diagnostic.diagnostic_sha256
        ):
            raise ValueError("A1 proposal diagnostic digest is invalid.")
        return diagnostic

    def with_direct_write_identity(
        self,
        identity: str,
    ) -> FieldNoteA1ProposalDiagnostic:
        return replace(self, direct_write_identity=identity)


@dataclass(frozen=True)
class FieldNoteCreatorLiveA1CaptureConfig:
    """One predeclared Run identity for the bounded creator-live A1 lane."""

    run_id: str
    expected_runtime_identity: CodexRuntimeIdentity

    def __post_init__(self) -> None:
        if (
            not isinstance(self.run_id, str)
            or not self.run_id.strip()
            or not isinstance(
                self.expected_runtime_identity,
                CodexRuntimeIdentity,
            )
        ):
            raise ValueError("Creator-live A1 capture Run ID is invalid.")


@dataclass(frozen=True)
class _ProposalResponse:
    call_id: str
    arguments_identity: str
    success: bool
    content_items: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class FieldNoteCodexRunResult(CodexRunResult):
    field_note_proposal: FieldNoteDraft | None = None
    reconnect_receipt: FieldNoteReconnectReceipt | None = None
    creator_live_a1_capture: bool = False
    creator_live_a1_failure_reason: str | None = None
    creator_live_a1_proposal_attempts: int = 0
    creator_live_a1_task_sha256: str | None = None
    creator_live_a1_proposal_diagnostic: (
        FieldNoteA1ProposalDiagnostic | None
    ) = None


class FieldNotesCodexAdapter(CodexAdapter):
    """Codex adapter with one side-effect-free same-Run proposal tool."""

    def __init__(
        self,
        *args: Any,
        trusted_source_model_class: str = "UNKNOWN",
        trusted_target_model_class: str = "UNKNOWN",
        creator_live_a1_capture_provider: Callable[
            [], FieldNoteCreatorLiveA1CaptureConfig | None
        ] | None = None,
        **kwargs: Any,
    ) -> None:
        self._reconnect_prompt: str | None = None
        self._reconnect_plan: FieldNoteReconnectPlan | None = None
        self.trusted_source_model_class = configured_model_class(
            trusted_source_model_class
        )
        self.trusted_target_model_class = configured_model_class(
            trusted_target_model_class
        )
        self._creator_live_a1_capture_provider = (
            creator_live_a1_capture_provider or (lambda: None)
        )
        super().__init__(*args, **kwargs)

    def _reset_run(self) -> None:
        super()._reset_run()
        capture = self._creator_live_a1_capture_provider()
        if capture is not None and not isinstance(
            capture,
            FieldNoteCreatorLiveA1CaptureConfig,
        ):
            raise codex.CodexAdapterFailure(
                "Creator-live A1 capture configuration is invalid."
            )
        self._creator_live_a1_capture = capture
        if capture is not None:
            self._run_id = capture.run_id
        self._field_note_gate = FieldNoteProposalGate(
            self._run_id,
            trusted_source_model_class=self.trusted_source_model_class,
            trusted_target_model_class=self.trusted_target_model_class,
        )
        self._proposal_responses: dict[str, _ProposalResponse] = {}
        self._proposal_request_ids: dict[str | int, str | None] = {}
        self._resolved_proposal_requests: set[str | int] = set()
        self._completed_proposal_items: set[str] = set()
        self._capture_proposal_call_ids: set[str] = set()
        self._capture_request_identities: set[str] = set()
        self._capture_argument_identities: set[str] = set()
        self._capture_proposal_malformed = False
        self._capture_request_shape_valid: bool | None = None
        self._capture_gate_invoked = False
        self._capture_gate_response_code: str | None = None
        self._capture_gate_response_success: bool | None = None
        self._capture_item_start_observed = False
        self._capture_item_completion_observed = False
        self._capture_item_observed_status: str | None = None
        self._capture_item_expected_status: str | None = None
        self._capture_request_identity_mismatch = False
        self._capture_response_identity_mismatch = False
        self._capture_inconsistent_replay = False
        prompt = self._reconnect_prompt
        if (
            isinstance(prompt, str)
            and self._creator_live_a1_capture is None
        ):
            self._reconnect_plan = prepare_field_note_reconnect(
                self.engine.store.repository,
                prompt,
                self._run_id,
            )
        else:
            self._reconnect_plan = None

    def _developer_instructions(self) -> str:
        existing = (
            _CREATOR_LIVE_A1_CAPTURE_INSTRUCTIONS
            if self._creator_live_a1_capture is not None
            else (
                codex._DEVELOPER_INSTRUCTIONS
                + _FIELD_NOTE_PROPOSAL_INSTRUCTIONS
            )
        )
        plan = self._reconnect_plan
        if plan is None or plan.envelope is None:
            return existing
        return plan.envelope + existing

    def _start_thread(self) -> None:
        self._emit("run", "Starting one fresh bounded Run.")
        repository = self.engine.store.repository
        developer_instructions = self._developer_instructions()
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
                        "model_reasoning_effort": self.expected_reasoning_effort,
                        "plugins": {},
                    },
                    "cwd": str(repository),
                    "developerInstructions": developer_instructions,
                    "dynamicTools": [
                        copy.deepcopy(codex._READ_TOOL_SPEC),
                        field_note_tool_spec_for_trust(
                            self.trusted_source_model_class,
                            self.trusted_target_model_class,
                        ),
                    ],
                    "ephemeral": True,
                    "model": self.expected_model,
                    "modelProvider": "openai",
                    "sandbox": "read-only",
                    "serviceTier": self.expected_service_tier,
                },
            ),
            "thread/start result",
        )
        if (
            self._reconnect_plan is not None
            and self._reconnect_plan.envelope is not None
        ):
            self._reconnect_plan = self._reconnect_plan.injected()
        self._protocol_phase = "thread_identity_verification"
        thread = self._require_object(result.get("thread"), "thread identity")
        thread_id = thread.get("id")
        cli_version = thread.get("cliVersion")
        if not isinstance(thread_id, str) or not thread_id:
            raise codex.CodexAdapterFailure("thread/start lacks a fresh thread ID.")
        if cli_version != self.expected_cli_version:
            raise codex.CodexAdapterFailure(
                "Codex app-server thread version identity mismatch."
            )
        if self._transport is None or self._transport.version != cli_version:
            raise codex.CodexAdapterFailure(
                "Codex CLI and app-server version identities differ."
            )
        if result.get("model") != self.expected_model:
            raise codex.CodexAdapterFailure("Codex model identity mismatch.")
        if result.get("modelProvider") != "openai":
            raise codex.CodexAdapterFailure("Codex model provider identity mismatch.")
        if result.get("reasoningEffort") != self.expected_reasoning_effort:
            raise codex.CodexAdapterFailure("Codex reasoning effort identity mismatch.")
        if result.get("serviceTier") != self.expected_service_tier:
            raise codex.CodexAdapterFailure("Codex service tier identity mismatch.")
        if result.get("approvalPolicy") != "on-request":
            raise codex.CodexAdapterFailure("Codex approval policy identity mismatch.")
        if result.get("approvalsReviewer") != "user":
            raise codex.CodexAdapterFailure("Codex approval reviewer identity mismatch.")
        if not self._cwd_matches(result.get("cwd")):
            raise codex.CodexAdapterFailure("Codex thread cwd identity mismatch.")
        if not self._read_only_sandbox(result.get("sandbox")):
            raise codex.CodexAdapterFailure("Codex thread sandbox identity mismatch.")
        if thread.get("ephemeral") is not True:
            raise codex.CodexAdapterFailure("Codex thread is not ephemeral.")
        if not self._cwd_matches(thread.get("cwd")):
            raise codex.CodexAdapterFailure("Codex thread root identity mismatch.")
        if self._account_type != "chatgpt":
            raise codex.CodexAdapterFailure(
                "Codex account identity changed during thread start."
            )
        self._thread_id = thread_id
        self._thread_cli_version = cli_version
        self._settings_verified = True
        self._runtime_identity = codex.CodexRuntimeIdentity(
            model=result["model"],
            reasoning_effort=result["reasoningEffort"],
            service_tier=result["serviceTier"],
            codex_cli_version=cli_version,
            account_type="chatgpt",
        )
        deferred = tuple(self._deferred_settings)
        self._deferred_settings = []
        self._protocol_phase = "settings_verification"
        for params in deferred:
            self._verify_settings(params)
        self._protocol_phase = "thread_identity_verification"

    @staticmethod
    def _proposal_content(payload: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
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

    def _send_proposal_response(
        self,
        request_id: str | int,
        response: _ProposalResponse,
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
        self._resolved_proposal_requests.add(request_id)

    def _failed_proposal_response(
        self,
        *,
        request_id: str | int,
        call_id: str,
        arguments: Mapping[str, Any],
        code: str,
    ) -> None:
        response = _ProposalResponse(
            call_id=call_id,
            arguments_identity=self._arguments_identity(dict(arguments)),
            success=False,
            content_items=self._proposal_content(
                {"code": code, "status": "rejected"}
            ),
        )
        # A malformed replay must never replace the first response record.
        self._proposal_responses.setdefault(call_id, response)
        self._send_proposal_response(request_id, response)

    def _respond_field_note_tool_call(self, message: dict[str, Any]) -> None:
        request_id = message.get("id")
        if (
            self._creator_live_a1_capture is not None
            and not isinstance(message.get("params"), dict)
        ):
            self._capture_proposal_malformed = True
            self._capture_request_shape_valid = False
        params = self._require_object(
            message.get("params"),
            "Field Note proposal parameters",
        )
        call_id = params.get("callId")
        arguments = params.get("arguments")
        if (
            not isinstance(request_id, (str, int))
            or isinstance(request_id, bool)
        ):
            if self._creator_live_a1_capture is not None:
                self._capture_proposal_malformed = True
                self._capture_request_shape_valid = False
            self._mark_identity_failure()
            return
        if self._creator_live_a1_capture is not None:
            self._capture_request_identities.add(
                hashlib.sha256(
                    canonical_json(
                        {
                            "type": type(request_id).__name__,
                            "value": request_id,
                        }
                    ).encode("utf-8")
                ).hexdigest()
            )
        safe_call_id = call_id if isinstance(call_id, str) else "invalid-proposal"
        safe_arguments = arguments if isinstance(arguments, dict) else {}
        if self._creator_live_a1_capture is not None:
            if isinstance(call_id, str) and call_id:
                self._capture_proposal_call_ids.add(call_id)
            else:
                self._capture_proposal_malformed = True
        if request_id in self._proposal_request_ids:
            if self._proposal_request_ids[request_id] != call_id:
                if self._creator_live_a1_capture is not None:
                    self._capture_request_identity_mismatch = True
                self._failed_proposal_response(
                    request_id=request_id,
                    call_id=safe_call_id,
                    arguments=safe_arguments,
                    code="proposal_request_identity_mismatch",
                )
                self._mark_identity_failure()
                return
        else:
            self._proposal_request_ids[request_id] = (
                call_id if isinstance(call_id, str) else None
            )
        item = self._items.get(safe_call_id)
        valid_shape = bool(
            set(params).issubset(
                {"arguments", "callId", "namespace", "threadId", "tool", "turnId"}
            )
            and set(params) >= {"arguments", "callId", "threadId", "tool", "turnId"}
            and isinstance(call_id, str)
            and bool(call_id)
            and isinstance(arguments, dict)
            and params.get("tool") == FIELD_NOTE_TOOL_NAME
            and params.get("namespace") is None
            and self._ids_match(params)
            and self._settings_verified
            and item is not None
            and item.get("type") == "dynamicToolCall"
            and item.get("tool") == FIELD_NOTE_TOOL_NAME
            and item.get("namespace") is None
            and item.get("arguments") == arguments
        )
        if not valid_shape:
            if self._creator_live_a1_capture is not None:
                self._capture_proposal_malformed = True
                self._capture_request_shape_valid = False
            self._failed_proposal_response(
                request_id=request_id,
                call_id=safe_call_id,
                arguments=safe_arguments,
                code="proposal_request_shape_invalid",
            )
            self._mark_identity_failure()
            return
        assert isinstance(call_id, str)
        assert isinstance(arguments, dict)
        arguments_identity = self._arguments_identity(arguments)
        if self._creator_live_a1_capture is not None:
            if self._capture_request_shape_valid is None:
                self._capture_request_shape_valid = True
            self._capture_argument_identities.add(arguments_identity)
        existing = self._proposal_responses.get(call_id)
        if existing is not None:
            if existing.arguments_identity != arguments_identity:
                if self._creator_live_a1_capture is not None:
                    self._capture_inconsistent_replay = True
                self._failed_proposal_response(
                    request_id=request_id,
                    call_id=call_id,
                    arguments=arguments,
                    code="proposal_request_identity_mismatch",
                )
                self._mark_identity_failure()
                return
            self._send_proposal_response(request_id, existing)
            return
        if self._creator_live_a1_capture is not None:
            self._capture_gate_invoked = True
        accepted, code = self._field_note_gate.propose(arguments)
        if self._creator_live_a1_capture is not None:
            self._capture_gate_response_code = code
            self._capture_gate_response_success = accepted
        response = _ProposalResponse(
            call_id=safe_call_id,
            arguments_identity=arguments_identity,
            success=accepted,
            content_items=self._proposal_content(
                {
                    "code": code,
                    "status": "accepted" if accepted else "rejected",
                }
            ),
        )
        self._proposal_responses[safe_call_id] = response
        self._send_proposal_response(request_id, response)

    @staticmethod
    def _identity_set_sha256(values: set[str]) -> str | None:
        if not values:
            return None
        return hashlib.sha256(
            canonical_json(sorted(values)).encode("utf-8")
        ).hexdigest()

    def _proposal_final_subcause(
        self,
        result: CodexRunResult,
        *,
        all_proposals_completed: bool,
    ) -> str | None:
        if result.file_actions or result.unsupported_reason in _DIRECT_MUTATION_REASONS:
            return "A1_DIRECT_WRITE_REQUESTED"
        attempts = len(self._capture_proposal_call_ids)
        if attempts == 0:
            if self._capture_request_shape_valid is False:
                return "A1_PROPOSAL_REQUEST_SHAPE_INVALID"
            return "A1_PROPOSAL_MISSING"
        if attempts != 1:
            return "A1_PROPOSAL_DUPLICATE"
        if self._capture_inconsistent_replay:
            return "A1_PROPOSAL_INCONSISTENT_REPLAY"
        if self._capture_request_shape_valid is False:
            return "A1_PROPOSAL_REQUEST_SHAPE_INVALID"
        if (
            self._capture_item_completion_observed
            and self._capture_item_observed_status is not None
            and self._capture_item_expected_status is not None
            and (
                self._capture_item_observed_status
                != self._capture_item_expected_status
            )
        ):
            return "A1_PROPOSAL_ITEM_STATUS_MISMATCH"
        if (
            self._capture_request_identity_mismatch
            or self._capture_response_identity_mismatch
        ):
            return "A1_PROPOSAL_RESPONSE_IDENTITY_MISMATCH"
        if (
            self._capture_gate_invoked
            and self._capture_gate_response_code == "proposal_schema_invalid"
        ):
            return "A1_PROPOSAL_SCHEMA_REJECTED"
        if (
            self._capture_gate_invoked
            and self._capture_gate_response_success is False
        ):
            return "A1_PROPOSAL_GATE_REJECTED"
        if (
            self._capture_gate_response_success is True
            and self._field_note_gate.accepted is None
        ):
            return "A1_PROPOSAL_ACCEPTED_STATE_MISSING"
        if not all_proposals_completed:
            if not self._capture_item_completion_observed:
                return "A1_PROPOSAL_ITEM_NOT_COMPLETED"
            if (
                self._identity_failure
                and self._failure_phase == "dynamic_tool_call"
            ):
                return "A1_PROPOSAL_PROTOCOL_IDENTITY_FAILURE"
            return "A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE"
        if (
            self._identity_failure
            and self._failure_phase == "dynamic_tool_call"
        ):
            return "A1_PROPOSAL_PROTOCOL_IDENTITY_FAILURE"
        if self._capture_proposal_malformed:
            return "A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE"
        if self._field_note_gate.accepted is None:
            return "A1_PROPOSAL_ACCEPTED_STATE_MISSING"
        return None

    def _creator_live_a1_proposal_diagnostic(
        self,
        result: CodexRunResult,
        *,
        all_proposals_completed: bool,
    ) -> FieldNoteA1ProposalDiagnostic | None:
        if self._creator_live_a1_capture is None:
            return None
        subcause = self._proposal_final_subcause(
            result,
            all_proposals_completed=all_proposals_completed,
        )
        return FieldNoteA1ProposalDiagnostic(
            proposal_call_count=len(self._capture_proposal_call_ids),
            call_identity_sha256=self._identity_set_sha256(
                {
                    hashlib.sha256(value.encode("utf-8")).hexdigest()
                    for value in self._capture_proposal_call_ids
                }
            ),
            request_identity_sha256=self._identity_set_sha256(
                self._capture_request_identities
            ),
            arguments_identity_sha256=self._identity_set_sha256(
                self._capture_argument_identities
            ),
            request_shape_valid=self._capture_request_shape_valid,
            malformed_observed=self._capture_proposal_malformed,
            gate_invoked=self._capture_gate_invoked,
            gate_response_code=self._capture_gate_response_code,
            gate_response_success=self._capture_gate_response_success,
            accepted_proposal_present=self._field_note_gate.accepted is not None,
            item_start_observed=self._capture_item_start_observed,
            item_completion_observed=(
                self._capture_item_completion_observed
            ),
            item_observed_status=self._capture_item_observed_status,
            item_expected_status=self._capture_item_expected_status,
            all_proposals_completed=all_proposals_completed,
            request_identity_mismatch=(
                self._capture_request_identity_mismatch
            ),
            response_identity_mismatch=(
                self._capture_response_identity_mismatch
            ),
            inconsistent_replay=self._capture_inconsistent_replay,
            protocol_identity_failure=self._identity_failure,
            protocol_failure_phase=(
                self._failure_phase if self._identity_failure else None
            ),
            direct_write_identity=None,
            final_subcause=subcause,
        )

    def _creator_live_a1_failure(
        self,
        result: CodexRunResult,
        *,
        all_proposals_completed: bool,
    ) -> str | None:
        if self._creator_live_a1_capture is None:
            return None
        proposal_failure = self._proposal_final_subcause(
            result,
            all_proposals_completed=all_proposals_completed,
        )
        if proposal_failure is not None:
            return proposal_failure
        if any(
            evidence.status != "succeeded"
            for evidence in result.read_evidence
        ):
            return "A1_READ_EVIDENCE_FAILED"
        if result.runtime_identity is None:
            return "A1_ACTUAL_RUNTIME_IDENTITY_MISSING"
        if (
            result.runtime_identity
            != self._creator_live_a1_capture.expected_runtime_identity
        ):
            return "A1_ACTUAL_RUNTIME_IDENTITY_MISMATCH"
        if not result.normal_terminal or result.turn_status != "completed":
            return "A1_RUN_INCOMPLETE"
        return None

    def _cache_item(self, params: dict[str, Any]) -> None:
        item = params.get("item")
        if (
            isinstance(item, dict)
            and item.get("type") == "dynamicToolCall"
            and item.get("tool") == FIELD_NOTE_TOOL_NAME
        ):
            if self._creator_live_a1_capture is not None:
                self._capture_item_start_observed = True
            if not self._ids_match(params):
                self._mark_identity_failure()
                return
            item_id = item.get("id")
            arguments = item.get("arguments")
            if (
                not isinstance(item_id, str)
                or not item_id
                or item.get("namespace") is not None
                or item.get("status") != "inProgress"
                or not isinstance(arguments, dict)
            ):
                if self._creator_live_a1_capture is not None:
                    self._capture_proposal_malformed = True
                self._mark_identity_failure()
                return
            if item_id in self._items and self._items[item_id] != item:
                if self._creator_live_a1_capture is not None:
                    existing = self._items[item_id]
                    if existing.get("arguments") != arguments:
                        self._capture_inconsistent_replay = True
                    else:
                        self._capture_response_identity_mismatch = True
                self._mark_identity_failure()
                return
            if self._creator_live_a1_capture is not None:
                self._capture_argument_identities.add(
                    self._arguments_identity(arguments)
                )
            self._items[item_id] = item
            return
        super()._cache_item(params)

    def _complete_item(self, params: dict[str, Any]) -> None:
        item = params.get("item")
        if (
            isinstance(item, dict)
            and item.get("type") == "dynamicToolCall"
            and item.get("tool") == FIELD_NOTE_TOOL_NAME
        ):
            if self._creator_live_a1_capture is not None:
                self._capture_item_completion_observed = True
                status = item.get("status")
                self._capture_item_observed_status = (
                    status if isinstance(status, str) and status else None
                )
            if not self._ids_match(params):
                self._mark_identity_failure()
                return
            item_id = item.get("id")
            response = (
                self._proposal_responses.get(item_id)
                if isinstance(item_id, str)
                else None
            )
            started = (
                self._items.get(item_id) if isinstance(item_id, str) else None
            )
            resolved = any(
                request_id in self._resolved_proposal_requests
                and request_item_id == item_id
                for request_id, request_item_id in self._proposal_request_ids.items()
            )
            expected_status = (
                "completed" if response is not None and response.success else "failed"
            )
            if self._creator_live_a1_capture is not None:
                self._capture_item_expected_status = expected_status
            if (
                response is None
                or started is None
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
                if self._creator_live_a1_capture is not None and (
                    item.get("status") == expected_status
                ):
                    self._capture_response_identity_mismatch = True
                self._mark_identity_failure()
                return
            self._completed_proposal_items.add(item_id)
            return
        super()._complete_item(params)

    def _dispatch(self, message: dict[str, Any]) -> None:
        if message.get("method") == "item/tool/call" and "id" in message:
            params = message.get("params")
            if (
                isinstance(params, dict)
                and params.get("tool") == FIELD_NOTE_TOOL_NAME
            ):
                self._protocol_phase = "dynamic_tool_call"
                self._respond_field_note_tool_call(message)
                return
        super()._dispatch(message)

    async def run(self, prompt: str) -> FieldNoteCodexRunResult:
        self._reconnect_prompt = prompt
        try:
            result = await super().run(prompt)
        finally:
            self._reconnect_prompt = None
        all_proposals_completed = set(self._proposal_responses).issubset(
            self._completed_proposal_items
        )
        proposal_diagnostic = self._creator_live_a1_proposal_diagnostic(
            result,
            all_proposals_completed=all_proposals_completed,
        )
        capture_failure = self._creator_live_a1_failure(
            result,
            all_proposals_completed=all_proposals_completed,
        )
        proposal = (
            self._field_note_gate.accepted
            if (
                result.normal_terminal
                and all_proposals_completed
                and capture_failure is None
            )
            else None
        )
        normal_terminal = (
            result.normal_terminal
            and all_proposals_completed
            and capture_failure is None
        )
        if self._reconnect_plan is not None:
            self._reconnect_plan = self._reconnect_plan.finalized(
                normal_terminal=normal_terminal,
                ordinary_paths=len(self._admitted_read_paths),
            )
        reconnect_receipt = (
            None
            if self._reconnect_plan is None
            else self._reconnect_plan.receipt
        )
        return FieldNoteCodexRunResult(
            run_id=result.run_id,
            normal_terminal=normal_terminal,
            status=(
                result.status
                if (
                    all_proposals_completed
                    and capture_failure is None
                )
                or result.unsupported_reason is not None
                else "ABNORMAL_TERMINAL"
            ),
            error_type=(
                result.error_type
                if all_proposals_completed and capture_failure is None
                else "FieldNoteProposalCompletionError"
            ),
            turn_status=result.turn_status,
            runtime_identity=result.runtime_identity,
            checkpoint_outcomes=result.checkpoint_outcomes,
            final_message=result.final_message,
            file_actions=result.file_actions,
            read_evidence=result.read_evidence,
            unsupported_reason=result.unsupported_reason,
            failure_diagnostic=result.failure_diagnostic,
            field_note_proposal=proposal,
            reconnect_receipt=reconnect_receipt,
            creator_live_a1_capture=(
                self._creator_live_a1_capture is not None
            ),
            creator_live_a1_failure_reason=capture_failure,
            creator_live_a1_proposal_attempts=len(
                self._capture_proposal_call_ids
            ),
            creator_live_a1_task_sha256=(
                hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                if self._creator_live_a1_capture is not None
                else None
            ),
            creator_live_a1_proposal_diagnostic=proposal_diagnostic,
        )
