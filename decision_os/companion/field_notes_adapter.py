"""Same-Run one-shot Field Notes proposal extension for the Codex adapter."""

from __future__ import annotations

import copy
from dataclasses import dataclass
import json
from typing import Any, Mapping

from decision_os.acceleration import codex_adapter as codex
from decision_os.acceleration.codex_adapter import CodexAdapter, CodexRunResult
from decision_os.companion.field_notes_model import (
    FIELD_NOTE_TOOL_NAME,
    FIELD_NOTE_TOOL_SPEC,
    FieldNoteDraft,
    FieldNoteProposalGate,
)


@dataclass(frozen=True)
class _ProposalResponse:
    call_id: str
    arguments_identity: str
    success: bool
    content_items: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class FieldNoteCodexRunResult(CodexRunResult):
    field_note_proposal: FieldNoteDraft | None = None


class FieldNotesCodexAdapter(CodexAdapter):
    """Codex adapter with one side-effect-free same-Run proposal tool."""

    def _reset_run(self) -> None:
        super()._reset_run()
        self._field_note_gate = FieldNoteProposalGate(self._run_id)
        self._proposal_responses: dict[str, _ProposalResponse] = {}
        self._proposal_request_ids: dict[str | int, str | None] = {}
        self._resolved_proposal_requests: set[str | int] = set()
        self._completed_proposal_items: set[str] = set()

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
                        "model_reasoning_effort": self.expected_reasoning_effort,
                        "plugins": {},
                    },
                    "cwd": str(repository),
                    "developerInstructions": codex._DEVELOPER_INSTRUCTIONS + (
                        " You may optionally call propose_field_note_candidate "
                        "once inside this same Run after identifying one bounded "
                        "reusable insight. The proposal tool is side-effect-free. "
                        "Do not emit raw Field Note JSON or Markdown and do not "
                        "call it twice."
                    ),
                    "dynamicTools": [
                        copy.deepcopy(codex._READ_TOOL_SPEC),
                        copy.deepcopy(FIELD_NOTE_TOOL_SPEC),
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
        self._proposal_responses[call_id] = response
        self._send_proposal_response(request_id, response)

    def _respond_field_note_tool_call(self, message: dict[str, Any]) -> None:
        request_id = message.get("id")
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
            self._mark_identity_failure()
            return
        safe_call_id = call_id if isinstance(call_id, str) else "invalid-proposal"
        safe_arguments = arguments if isinstance(arguments, dict) else {}
        if request_id in self._proposal_request_ids:
            if self._proposal_request_ids[request_id] != call_id:
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
            self._failed_proposal_response(
                request_id=request_id,
                call_id=safe_call_id,
                arguments=safe_arguments,
                code="proposal_request_shape_invalid",
            )
            self._mark_identity_failure()
            return
        accepted, code = self._field_note_gate.propose(arguments)
        response = _ProposalResponse(
            call_id=safe_call_id,
            arguments_identity=self._arguments_identity(arguments),
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

    def _cache_item(self, params: dict[str, Any]) -> None:
        item = params.get("item")
        if (
            isinstance(item, dict)
            and item.get("type") == "dynamicToolCall"
            and item.get("tool") == FIELD_NOTE_TOOL_NAME
        ):
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
                self._mark_identity_failure()
                return
            if item_id in self._items and self._items[item_id] != item:
                self._mark_identity_failure()
                return
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
        result = await super().run(prompt)
        all_proposals_completed = set(self._proposal_responses).issubset(
            self._completed_proposal_items
        )
        proposal = (
            self._field_note_gate.accepted
            if result.normal_terminal and all_proposals_completed
            else None
        )
        return FieldNoteCodexRunResult(
            run_id=result.run_id,
            normal_terminal=result.normal_terminal and all_proposals_completed,
            status=(
                result.status
                if all_proposals_completed
                else "ABNORMAL_TERMINAL"
            ),
            error_type=(
                result.error_type
                if all_proposals_completed
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
        )
