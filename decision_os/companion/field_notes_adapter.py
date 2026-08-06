"""Same-Run one-shot Field Notes proposal extension for the Codex adapter."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Mapping

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
from decision_os.companion.field_notes_creator_live_reconnect import (
    FieldNoteCreatorLiveA2ReconnectError,
    FieldNoteCreatorLiveA2ReconnectTarget,
    prepare_creator_live_a2_reconnect,
)

if TYPE_CHECKING:
    from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
        FixedSourceToolSession,
        IsolationEvidence,
        PostA1GateReadbackV02,
        SourceToolCallResult,
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

_CREATOR_LIVE_CANDIDATE_V02_A2_INSTRUCTIONS = (
    "This is the isolated Candidate v0.2 exact A2 reconnect lane. Use only "
    "the one supplied exact Field Note and the fixed user task. No dynamic "
    "tool, native file reader, repository scan, alternate-note selection, "
    "reconstruction, shell, Git, web, MCP, plugin, app, hook, attachment, "
    "dependency installation, file change, retry, replacement, or publication "
    "is authorized. Complete the bounded task normally or fail closed."
)

_CANDIDATE_PASSIVE_ITEM_TYPES = frozenset(
    {"agentMessage", "plan", "reasoning", "userMessage"}
)

_CANDIDATE_CORE_NOTIFICATION_METHODS = frozenset(
    {
        "error",
        "item/completed",
        "item/fileChange/patchUpdated",
        "item/started",
        "model/rerouted",
        "serverRequest/resolved",
        "thread/settings/updated",
        "turn/completed",
        "turn/started",
    }
)

_CANDIDATE_ITEM_DELTA_TYPES = {
    "item/agentMessage/delta": "agentMessage",
    "item/plan/delta": "plan",
    "item/reasoning/summaryPartAdded": "reasoning",
    "item/reasoning/summaryTextDelta": "reasoning",
    "item/reasoning/textDelta": "reasoning",
}

_CANDIDATE_PASSIVE_NOTIFICATION_METHODS = frozenset(
    {
        *_CANDIDATE_ITEM_DELTA_TYPES,
        "deprecationNotice",
        "model/safetyBuffering/updated",
        "thread/status/changed",
        "thread/tokenUsage/updated",
        "turn/moderationMetadata",
        "turn/plan/updated",
        "warning",
    }
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
class FieldNoteCreatorLiveCandidateV02A1Config:
    """Private selector and fixed contract binding for Cycle 006 Run 1."""

    run_id: str
    expected_runtime_identity: CodexRuntimeIdentity
    contract_identity_sha256: str
    turn_start_intent_observer: Callable[[str], None] | None = field(
        default=None,
        compare=False,
        repr=False,
    )
    turn_started_observer: Callable[[str], None] | None = field(
        default=None,
        compare=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.run_id, str)
            or not self.run_id.strip()
            or not isinstance(self.expected_runtime_identity, CodexRuntimeIdentity)
            or not isinstance(self.contract_identity_sha256, str)
            or len(self.contract_identity_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.contract_identity_sha256
            )
            or (
                self.turn_start_intent_observer is not None
                and not callable(self.turn_start_intent_observer)
            )
            or (
                self.turn_started_observer is not None
                and not callable(self.turn_started_observer)
            )
        ):
            raise ValueError("Candidate v0.2 Run-1 configuration is invalid.")


@dataclass(frozen=True)
class FieldNoteCreatorLiveCandidateV02A2Config:
    """Exact durable Candidate v0.2 Post-A1 prerequisite for Run 2."""

    readback_path: str
    readback_sha256: str
    turn_start_intent_observer: Callable[[str], None] | None = field(
        default=None,
        compare=False,
        repr=False,
    )
    turn_started_observer: Callable[[str], None] | None = field(
        default=None,
        compare=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if (
            not isinstance(self.readback_path, str)
            or not self.readback_path
            or not isinstance(self.readback_sha256, str)
            or len(self.readback_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.readback_sha256
            )
            or (
                self.turn_start_intent_observer is not None
                and not callable(self.turn_start_intent_observer)
            )
            or (
                self.turn_started_observer is not None
                and not callable(self.turn_started_observer)
            )
        ):
            raise ValueError("Candidate v0.2 Run-2 configuration is invalid.")


@dataclass(frozen=True)
class _ProposalResponse:
    call_id: str
    arguments_identity: str
    success: bool
    content_items: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class _FixedSourceResponse:
    call_id: str
    arguments_identity: str
    result: SourceToolCallResult
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
    candidate_v0_2_isolation_evidence: IsolationEvidence | None = None


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
        creator_live_a2_reconnect_provider: Callable[
            [], FieldNoteCreatorLiveA2ReconnectTarget | None
        ] | None = None,
        candidate_v0_2_a1_provider: Callable[
            [], FieldNoteCreatorLiveCandidateV02A1Config | None
        ] | None = None,
        candidate_v0_2_a2_provider: Callable[
            [], FieldNoteCreatorLiveCandidateV02A2Config | None
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
        self._creator_live_a2_reconnect_provider = (
            creator_live_a2_reconnect_provider or (lambda: None)
        )
        self._candidate_v0_2_a1_provider = (
            candidate_v0_2_a1_provider or (lambda: None)
        )
        self._candidate_v0_2_a2_provider = (
            candidate_v0_2_a2_provider or (lambda: None)
        )
        super().__init__(*args, **kwargs)

    def _reset_run(self) -> None:
        super()._reset_run()
        capture = self._creator_live_a1_capture_provider()
        reconnect_target = self._creator_live_a2_reconnect_provider()
        candidate_a1 = self._candidate_v0_2_a1_provider()
        candidate_a2 = self._candidate_v0_2_a2_provider()
        if capture is not None and not isinstance(
            capture,
            FieldNoteCreatorLiveA1CaptureConfig,
        ):
            raise codex.CodexAdapterFailure(
                "Creator-live A1 capture configuration is invalid."
            )
        if reconnect_target is not None and not isinstance(
            reconnect_target,
            FieldNoteCreatorLiveA2ReconnectTarget,
        ):
            raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
        if capture is not None and reconnect_target is not None:
            raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
        if candidate_a1 is not None and not isinstance(
            candidate_a1,
            FieldNoteCreatorLiveCandidateV02A1Config,
        ):
            raise codex.CodexAdapterFailure(
                "Candidate v0.2 Run-1 configuration is invalid."
            )
        if candidate_a2 is not None and not isinstance(
            candidate_a2,
            FieldNoteCreatorLiveCandidateV02A2Config,
        ):
            raise codex.CodexAdapterFailure(
                "Candidate v0.2 Run-2 configuration is invalid."
            )
        if (
            (candidate_a1 is not None)
            != (
                capture is not None
                and candidate_a1 is not None
                and capture.run_id == candidate_a1.run_id
                and capture.expected_runtime_identity
                == candidate_a1.expected_runtime_identity
            )
            or (candidate_a2 is not None and reconnect_target is None)
            or (candidate_a1 is not None and candidate_a2 is not None)
        ):
            raise codex.CodexAdapterFailure(
                "Candidate v0.2 lane configuration is inconsistent."
            )
        self._creator_live_a1_capture = capture
        self._creator_live_a2_reconnect_target = reconnect_target
        self._candidate_v0_2_a1 = candidate_a1
        self._candidate_v0_2_a2 = candidate_a2
        if capture is not None:
            self._run_id = capture.run_id
        elif reconnect_target is not None:
            expected_runtime = CodexRuntimeIdentity(
                model=self.expected_model,
                reasoning_effort=self.expected_reasoning_effort,
                service_tier=self.expected_service_tier,
                codex_cli_version=self.expected_cli_version,
                account_type="chatgpt",
            )
            if reconnect_target.expected_runtime_identity != expected_runtime:
                raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
            self._run_id = reconnect_target.run_2_id
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
        self._candidate_source_session = (
            self._new_candidate_source_session()
            if candidate_a1 is not None
            else None
        )
        self._candidate_source_responses: dict[str, _FixedSourceResponse] = {}
        self._candidate_source_requests: dict[str | int, str | None] = {}
        self._candidate_resolved_source_requests: set[str | int] = set()
        self._candidate_source_started_ids: set[str] = set()
        self._candidate_completed_source_items: set[str] = set()
        self._candidate_events: list[dict[str, Any]] = []
        self._candidate_event_reason_codes: set[str] = set()
        self._candidate_source_success_ordinal: int | None = None
        self._candidate_proposal_first_ordinal: int | None = None
        self._candidate_proposal_seen: set[str] = set()
        self._candidate_proposal_started_ids: set[str] = set()
        self._candidate_user_message: dict[str, Any] | None = None
        self._candidate_user_message_phases: set[str] = set()
        self._candidate_post_a1_readback: PostA1GateReadbackV02 | None = None
        prompt = self._reconnect_prompt
        if reconnect_target is not None:
            self._reconnect_plan = prepare_creator_live_a2_reconnect(
                self.engine.store.repository,
                reconnect_target,
            ).plan
            if candidate_a2 is not None:
                from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
                    read_post_a1_readback_v0_2,
                    require_post_a1_gate_for_a2,
                )

                self._candidate_post_a1_readback = read_post_a1_readback_v0_2(
                    Path(candidate_a2.readback_path),
                    candidate_a2.readback_sha256,
                )
                require_post_a1_gate_for_a2(self._candidate_post_a1_readback)
        elif isinstance(prompt, str) and self._creator_live_a1_capture is None:
            self._reconnect_plan = prepare_field_note_reconnect(
                self.engine.store.repository,
                prompt,
                self._run_id,
            )
        else:
            self._reconnect_plan = None

    def _start_turn(self, prompt: str) -> None:
        """Write ahead, then record accepted Cycle 006 turn activity."""

        candidate = self._candidate_v0_2_a1 or self._candidate_v0_2_a2
        intent_observer = (
            candidate.turn_start_intent_observer
            if candidate is not None
            else None
        )
        if intent_observer is not None:
            intent_observer(self._run_id)
        super()._start_turn(prompt)
        observer = (
            candidate.turn_started_observer if candidate is not None else None
        )
        if observer is not None:
            observer(self._run_id)

    def _developer_instructions(self) -> str:
        if self._candidate_v0_2_a1 is not None:
            from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
                CANDIDATE_DEVELOPER_INSTRUCTIONS,
            )

            existing = CANDIDATE_DEVELOPER_INSTRUCTIONS
        elif self._candidate_v0_2_a2 is not None:
            from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
                CANDIDATE_ID,
            )

            readback = self._candidate_post_a1_readback
            if readback is None:
                raise codex.CodexAdapterFailure(
                    "Candidate v0.2 Post-A1 gate is unavailable."
                )
            context = {
                "schema": "decision-os.creator-live-candidate-v0.2-a2-context.v0.1",
                "candidate_id": CANDIDATE_ID,
                "post_a1_result": readback.result,
                "post_a1_readback_sha256": readback.readback_sha256,
                "source_isolation_receipt_sha256": readback.source_isolation.get(
                    "receipt_sha256"
                ),
                "independence_receipt_sha256": readback.independence.get(
                    "receipt_sha256"
                ),
                "witness_sha256": readback.witness_binding.get("witness_sha256"),
            }
            existing = (
                "Candidate v0.2 durable Post-A1 gate context (content-free): "
                + canonical_json(context)
                + "\n"
                + _CREATOR_LIVE_CANDIDATE_V02_A2_INSTRUCTIONS
            )
        else:
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

    def _dynamic_tools(self) -> list[dict[str, Any]]:
        if self._candidate_v0_2_a1 is not None:
            from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
                candidate_dynamic_tools,
            )

            return candidate_dynamic_tools()
        if self._candidate_v0_2_a2 is not None:
            return []
        return [
            copy.deepcopy(codex._READ_TOOL_SPEC),
            field_note_tool_spec_for_trust(
                self.trusted_source_model_class,
                self.trusted_target_model_class,
            ),
        ]

    @staticmethod
    def _new_candidate_source_session() -> FixedSourceToolSession:
        from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
            FixedSourceToolSession,
        )

        return FixedSourceToolSession()

    def _start_thread(self) -> None:
        self._emit("run", "Starting one fresh bounded Run.")
        repository = self.engine.store.repository
        developer_instructions = self._developer_instructions()
        candidate = bool(
            self._candidate_v0_2_a1 is not None
            or self._candidate_v0_2_a2 is not None
        )
        isolated_features = {
            "apps": False,
            "hooks": False,
            "multi_agent": False,
            "remote_plugin": False,
            "shell_tool": False,
            "skill_mcp_dependency_install": False,
            **({"plugins": False} if candidate else {}),
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
                        **(
                            {
                                "project_doc_fallback_filenames": [],
                                "project_doc_max_bytes": 0,
                                "web_search": "disabled",
                            }
                            if candidate
                            else {}
                        ),
                    },
                    "cwd": str(repository),
                    "developerInstructions": developer_instructions,
                    "dynamicTools": self._dynamic_tools(),
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

    def _candidate_record_event(self, kind: str, **facts: Any) -> int:
        event = {
            "ordinal": len(self._candidate_events) + 1,
            "kind": kind,
            **facts,
        }
        self._candidate_events.append(event)
        return event["ordinal"]

    @staticmethod
    def _fixed_source_content(
        result: SourceToolCallResult,
    ) -> tuple[dict[str, str], ...]:
        payload = (
            dict(result.payload)
            if result.success
            else {"code": result.code, "status": "rejected"}
        )
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

    def _send_fixed_source_response(
        self,
        request_id: str | int,
        response: _FixedSourceResponse,
    ) -> None:
        self._send(
            {
                "id": request_id,
                "result": {
                    "contentItems": [dict(item) for item in response.content_items],
                    "success": response.result.success,
                },
            }
        )
        self._candidate_resolved_source_requests.add(request_id)

    def _reject_duplicate_candidate_tool_request(
        self,
        request_id: str | int,
        *,
        reason_code: str,
    ) -> None:
        """Reject a second lifecycle request without replaying protected bytes."""

        self._candidate_event_reason_codes.add(reason_code)
        self._mark_identity_failure()
        self._send(
            {
                "error": {
                    "code": -32600,
                    "message": "Duplicate candidate tool lifecycle.",
                },
                "id": request_id,
            }
        )

    def _respond_fixed_source_tool_call(self, message: dict[str, Any]) -> None:
        from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
            SOURCE_TOOL_NAME,
        )

        request_id = message.get("id")
        params = message.get("params")
        if (
            not isinstance(request_id, (str, int))
            or isinstance(request_id, bool)
            or not isinstance(params, dict)
        ):
            self._candidate_event_reason_codes.add("SOURCE_REQUEST_SHAPE_INVALID")
            self._mark_identity_failure()
            return
        call_id = params.get("callId")
        arguments = params.get("arguments")
        safe_call_id = call_id if isinstance(call_id, str) else "invalid-source"
        safe_arguments = arguments if isinstance(arguments, dict) else {}
        arguments_identity = self._arguments_identity(safe_arguments)
        if self._candidate_source_requests:
            self._reject_duplicate_candidate_tool_request(
                request_id,
                reason_code="SOURCE_REQUEST_COUNT_INVALID",
            )
            return
        self._candidate_source_requests[request_id] = (
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
            and not arguments
            and params.get("tool") == SOURCE_TOOL_NAME
            and params.get("namespace") is None
            and self._ids_match(params)
            and self._settings_verified
            and item is not None
            and item.get("type") == "dynamicToolCall"
            and item.get("tool") == SOURCE_TOOL_NAME
            and item.get("namespace") is None
            and item.get("arguments") == arguments
        )
        if not valid_shape or self._candidate_source_session is None:
            self._candidate_event_reason_codes.add("SOURCE_REQUEST_SHAPE_INVALID")
            self._mark_identity_failure()
            return
        assert isinstance(call_id, str)
        assert isinstance(arguments, dict)
        result = self._candidate_source_session.call(call_id, arguments)
        response = _FixedSourceResponse(
            call_id=call_id,
            arguments_identity=arguments_identity,
            result=result,
            content_items=self._fixed_source_content(result),
        )
        self._candidate_source_responses[call_id] = response
        ordinal = self._candidate_record_event(
            "source_response",
            call_identity_sha256=hashlib.sha256(
                call_id.encode("utf-8")
            ).hexdigest(),
            arguments_identity_sha256=arguments_identity,
            success=result.success,
            code=result.code,
            semantic_disclosure=result.semantic_disclosure,
        )
        if result.success and result.semantic_disclosure:
            self._candidate_source_success_ordinal = ordinal
        else:
            self._candidate_event_reason_codes.add(result.code)
        self._send_fixed_source_response(request_id, response)

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
        if (
            self._candidate_v0_2_a1 is not None
            and isinstance(call_id, str)
            and call_id
            and call_id not in self._candidate_proposal_seen
        ):
            self._candidate_proposal_seen.add(call_id)
            ordinal = self._candidate_record_event(
                "proposal_request",
                call_identity_sha256=hashlib.sha256(
                    call_id.encode("utf-8")
                ).hexdigest(),
                arguments_identity_sha256=self._arguments_identity(safe_arguments),
            )
            if self._candidate_proposal_first_ordinal is None:
                self._candidate_proposal_first_ordinal = ordinal
        if self._creator_live_a1_capture is not None:
            if isinstance(call_id, str) and call_id:
                self._capture_proposal_call_ids.add(call_id)
            else:
                self._capture_proposal_malformed = True
        if self._candidate_v0_2_a1 is not None and self._proposal_request_ids:
            self._reject_duplicate_candidate_tool_request(
                request_id,
                reason_code="PROPOSAL_REQUEST_COUNT_INVALID",
            )
            return
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

    def _candidate_fixed_task_matches(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
            FIXED_TASK_IDENTITIES,
        )

        task_index = 0 if self._candidate_v0_2_a1 is not None else 1
        identity = FIXED_TASK_IDENTITIES[task_index]
        encoded = value.encode("utf-8")
        return bool(
            len(encoded) == identity.byte_count
            and hashlib.sha256(encoded).hexdigest() == identity.sha256
        )

    def _candidate_passive_item_admission(
        self,
        params: dict[str, Any],
        *,
        phase: str,
    ) -> bool | None:
        """Admit only inert, schema-bounded item types in Candidate Runs."""

        if self._candidate_v0_2_a1 is None and self._candidate_v0_2_a2 is None:
            return None
        item = params.get("item")
        item_type = item.get("type") if isinstance(item, dict) else None
        if item_type in {"dynamicToolCall", "fileChange"}:
            return None
        if item_type not in _CANDIDATE_PASSIVE_ITEM_TYPES:
            self._candidate_event_reason_codes.add(
                "CANDIDATE_ITEM_TYPE_NOT_ALLOWED"
            )
            self._mark_unsupported("unsupported_dynamic_tool")
            if not self._ids_match(params):
                self._mark_identity_failure()
            return False
        if not self._ids_match(params):
            self._candidate_event_reason_codes.add(
                "CANDIDATE_PASSIVE_ITEM_IDENTITY_MISMATCH"
            )
            self._mark_identity_failure()
            return False
        assert isinstance(item, dict)
        item_id = item.get("id")
        shape_valid = isinstance(item_id, str) and bool(item_id)
        if item_type == "userMessage":
            content = item.get("content")
            text_input = (
                content[0]
                if isinstance(content, list) and len(content) == 1
                else None
            )
            shape_valid = bool(
                shape_valid
                and set(item).issubset({"clientId", "content", "id", "type"})
                and set(item) >= {"content", "id", "type"}
                and (
                    item.get("clientId") is None
                    or isinstance(item.get("clientId"), str)
                )
            )
            shape_valid = bool(
                shape_valid
                and isinstance(text_input, dict)
                and set(text_input).issubset(
                    {"text", "text_elements", "type"}
                )
                and set(text_input) >= {"text", "type"}
                and text_input.get("type") == "text"
                and text_input.get("text_elements", []) == []
                and isinstance(text_input.get("text"), str)
                and self._candidate_fixed_task_matches(text_input["text"])
                and self._reconnect_prompt == text_input["text"]
            )
            if not shape_valid:
                self._candidate_event_reason_codes.add(
                    "CANDIDATE_USER_MESSAGE_INVALID"
                )
                self._mark_identity_failure()
                return False
            if (
                self._candidate_user_message is not None
                and self._candidate_user_message != item
            ):
                self._candidate_event_reason_codes.add(
                    "CANDIDATE_USER_MESSAGE_COUNT_INVALID"
                )
                self._mark_identity_failure()
                return False
            if phase in self._candidate_user_message_phases:
                self._candidate_event_reason_codes.add(
                    "CANDIDATE_USER_MESSAGE_COUNT_INVALID"
                )
                self._mark_identity_failure()
                return False
            if self._candidate_user_message is None:
                self._candidate_user_message = copy.deepcopy(item)
            self._candidate_user_message_phases.add(phase)
            return True
        if item_type == "agentMessage":
            shape_valid = bool(
                shape_valid
                and set(item).issubset(
                    {"id", "memoryCitation", "phase", "text", "type"}
                )
                and set(item) >= {"id", "text", "type"}
                and isinstance(item.get("text"), str)
                and item.get("phase") in {None, "commentary", "final_answer"}
                and item.get("memoryCitation") is None
            )
        elif item_type == "reasoning":
            shape_valid = bool(
                shape_valid
                and set(item).issubset({"content", "id", "summary", "type"})
                and set(item) >= {"id", "type"}
                and isinstance(item.get("content", []), list)
                and all(
                    isinstance(value, str) for value in item.get("content", [])
                )
                and isinstance(item.get("summary", []), list)
                and all(
                    isinstance(value, str) for value in item.get("summary", [])
                )
            )
        elif item_type == "plan":
            shape_valid = bool(
                shape_valid
                and set(item) == {"id", "text", "type"}
                and isinstance(item.get("text"), str)
            )
        if not shape_valid:
            self._candidate_event_reason_codes.add(
                "CANDIDATE_PASSIVE_ITEM_SHAPE_INVALID"
            )
            self._mark_identity_failure()
            return False
        return True

    def _cache_item(self, params: dict[str, Any]) -> None:
        passive_admission = self._candidate_passive_item_admission(
            params,
            phase="started",
        )
        if passive_admission is not None:
            if passive_admission:
                item = params["item"]
                item_id = item["id"]
                existing = self._items.get(item_id)
                if existing is not None and existing != item:
                    self._candidate_event_reason_codes.add(
                        "CANDIDATE_PASSIVE_ITEM_LIFECYCLE_INVALID"
                    )
                    self._mark_identity_failure()
                else:
                    self._items[item_id] = copy.deepcopy(item)
            return
        item = params.get("item")
        if (
            (self._candidate_v0_2_a1 is not None or self._candidate_v0_2_a2 is not None)
            and isinstance(item, dict)
            and item.get("type") == "fileChange"
        ):
            self._candidate_event_reason_codes.add(
                "CANDIDATE_FILE_CHANGE_ITEM_STARTED"
            )
            self._mark_unsupported("unsupported_file_change_shape")
            if not self._ids_match(params):
                self._mark_identity_failure()
            return
        if (
            (self._candidate_v0_2_a1 is not None or self._candidate_v0_2_a2 is not None)
            and isinstance(item, dict)
            and item.get("type") == "dynamicToolCall"
        ):
            tool = item.get("tool")
            allowed = {FIELD_NOTE_TOOL_NAME}
            if self._candidate_v0_2_a1 is not None:
                from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
                    SOURCE_TOOL_NAME,
                )

                allowed.add(SOURCE_TOOL_NAME)
            if self._candidate_v0_2_a2 is not None or tool not in allowed:
                self._candidate_event_reason_codes.add(
                    "UNADVERTISED_DYNAMIC_TOOL_ITEM"
                )
                self._mark_unsupported("unsupported_dynamic_tool")
                return
        if self._candidate_v0_2_a1 is not None:
            from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
                SOURCE_TOOL_NAME,
            )

            if (
                isinstance(item, dict)
                and item.get("type") == "dynamicToolCall"
                and item.get("tool") == SOURCE_TOOL_NAME
            ):
                if not self._ids_match(params):
                    self._candidate_event_reason_codes.add(
                        "SOURCE_ITEM_IDENTITY_MISMATCH"
                    )
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
                    or arguments
                ):
                    self._candidate_event_reason_codes.add(
                        "SOURCE_ITEM_SHAPE_INVALID"
                    )
                    self._mark_identity_failure()
                    return
                if self._candidate_source_started_ids:
                    self._candidate_event_reason_codes.add(
                        "SOURCE_ITEM_COUNT_INVALID"
                    )
                    self._candidate_source_started_ids.add(item_id)
                    self._mark_identity_failure()
                    return
                if item_id in self._items and self._items[item_id] != item:
                    self._candidate_event_reason_codes.add(
                        "SOURCE_ITEM_REPLAY_INCONSISTENT"
                    )
                    self._mark_identity_failure()
                    return
                self._candidate_source_started_ids.add(item_id)
                self._items[item_id] = item
                self._candidate_record_event(
                    "source_item_started",
                    call_identity_sha256=hashlib.sha256(
                        item_id.encode("utf-8")
                    ).hexdigest(),
                    arguments_identity_sha256=self._arguments_identity(arguments),
                )
                return
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
            if (
                self._candidate_v0_2_a1 is not None
                and self._candidate_proposal_started_ids
            ):
                self._candidate_event_reason_codes.add(
                    "PROPOSAL_ITEM_COUNT_INVALID"
                )
                self._candidate_proposal_started_ids.add(item_id)
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
            if (
                self._candidate_v0_2_a1 is not None
                and item_id not in self._candidate_proposal_started_ids
            ):
                self._candidate_proposal_started_ids.add(item_id)
                if len(self._candidate_proposal_started_ids) != 1:
                    self._candidate_event_reason_codes.add(
                        "PROPOSAL_ITEM_COUNT_INVALID"
                    )
                    self._mark_identity_failure()
                self._candidate_proposal_seen.add(item_id)
                ordinal = self._candidate_record_event(
                    "proposal_item_started",
                    call_identity_sha256=hashlib.sha256(
                        item_id.encode("utf-8")
                    ).hexdigest(),
                    arguments_identity_sha256=self._arguments_identity(arguments),
                )
                if self._candidate_proposal_first_ordinal is None:
                    self._candidate_proposal_first_ordinal = ordinal
            return
        super()._cache_item(params)

    def _complete_item(self, params: dict[str, Any]) -> None:
        passive_admission = self._candidate_passive_item_admission(
            params,
            phase="completed",
        )
        if passive_admission is not None:
            if passive_admission:
                super()._complete_item(params)
            return
        item = params.get("item")
        if (
            (self._candidate_v0_2_a1 is not None or self._candidate_v0_2_a2 is not None)
            and isinstance(item, dict)
            and item.get("type") == "fileChange"
        ):
            self._candidate_event_reason_codes.add(
                "CANDIDATE_FILE_CHANGE_ITEM_COMPLETED"
            )
            self._mark_unsupported("unsupported_file_change_shape")
            if not self._ids_match(params):
                self._mark_identity_failure()
            return
        if (
            (self._candidate_v0_2_a1 is not None or self._candidate_v0_2_a2 is not None)
            and isinstance(item, dict)
            and item.get("type") == "dynamicToolCall"
        ):
            tool = item.get("tool")
            allowed = {FIELD_NOTE_TOOL_NAME}
            if self._candidate_v0_2_a1 is not None:
                from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
                    SOURCE_TOOL_NAME,
                )

                allowed.add(SOURCE_TOOL_NAME)
            if self._candidate_v0_2_a2 is not None or tool not in allowed:
                self._candidate_event_reason_codes.add(
                    "UNADVERTISED_DYNAMIC_TOOL_ITEM"
                )
                self._mark_unsupported("unsupported_dynamic_tool")
                return
        if self._candidate_v0_2_a1 is not None:
            from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
                SOURCE_TOOL_NAME,
            )

            if (
                isinstance(item, dict)
                and item.get("type") == "dynamicToolCall"
                and item.get("tool") == SOURCE_TOOL_NAME
            ):
                if not self._ids_match(params):
                    self._candidate_event_reason_codes.add(
                        "SOURCE_ITEM_IDENTITY_MISMATCH"
                    )
                    self._mark_identity_failure()
                    return
                item_id = item.get("id")
                response = (
                    self._candidate_source_responses.get(item_id)
                    if isinstance(item_id, str)
                    else None
                )
                started = (
                    self._items.get(item_id) if isinstance(item_id, str) else None
                )
                resolved = any(
                    request_id in self._candidate_resolved_source_requests
                    and request_item_id == item_id
                    for request_id, request_item_id
                    in self._candidate_source_requests.items()
                )
                expected_status = (
                    "completed"
                    if response is not None and response.result.success
                    else "failed"
                )
                if (
                    item_id in self._candidate_completed_source_items
                    or
                    response is None
                    or started is None
                    or item.get("namespace") is not None
                    or item.get("arguments") != started.get("arguments")
                    or self._arguments_identity(item.get("arguments", {}))
                    != response.arguments_identity
                    or item.get("status") != expected_status
                    or (
                        "success" in item
                        and item.get("success") is not response.result.success
                    )
                    or (
                        "contentItems" in item
                        and item.get("contentItems")
                        != [dict(value) for value in response.content_items]
                    )
                    or not resolved
                ):
                    self._candidate_event_reason_codes.add(
                        (
                            "SOURCE_ITEM_COMPLETION_DUPLICATE"
                            if item_id in self._candidate_completed_source_items
                            else "SOURCE_ITEM_COMPLETION_INVALID"
                        )
                    )
                    self._mark_identity_failure()
                    return
                assert isinstance(item_id, str)
                self._candidate_completed_source_items.add(item_id)
                self._candidate_record_event(
                    "source_item_completed",
                    call_identity_sha256=hashlib.sha256(
                        item_id.encode("utf-8")
                    ).hexdigest(),
                    status=expected_status,
                )
                return
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
                (
                    self._candidate_v0_2_a1 is not None
                    and item_id in self._completed_proposal_items
                )
                or
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
                if (
                    self._candidate_v0_2_a1 is not None
                    and item_id in self._completed_proposal_items
                ):
                    self._candidate_event_reason_codes.add(
                        "PROPOSAL_ITEM_COMPLETION_DUPLICATE"
                    )
                if self._creator_live_a1_capture is not None and (
                    item.get("status") == expected_status
                ):
                    self._capture_response_identity_mismatch = True
                self._mark_identity_failure()
                return
            self._completed_proposal_items.add(item_id)
            return
        super()._complete_item(params)

    @staticmethod
    def _candidate_nonnegative_integer(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    def _candidate_passive_notification_admission(
        self,
        message: dict[str, Any],
    ) -> bool | None:
        """Fail closed on every Candidate notification outside a strict set."""

        if self._candidate_v0_2_a1 is None and self._candidate_v0_2_a2 is None:
            return None
        if "id" in message:
            return None
        method = message.get("method")
        if method in _CANDIDATE_CORE_NOTIFICATION_METHODS:
            return None
        if method not in _CANDIDATE_PASSIVE_NOTIFICATION_METHODS:
            self._protocol_phase = "protocol_message"
            self._candidate_event_reason_codes.add(
                "CANDIDATE_NOTIFICATION_NOT_ALLOWED"
            )
            self._mark_unsupported("unsupported_request_method:other")
            return False
        params = message.get("params")
        if not isinstance(params, dict):
            self._candidate_event_reason_codes.add(
                "CANDIDATE_PASSIVE_NOTIFICATION_INVALID"
            )
            self._mark_identity_failure()
            return False

        valid = False
        item_type = _CANDIDATE_ITEM_DELTA_TYPES.get(method)
        if item_type is not None:
            required = {"itemId", "threadId", "turnId"}
            if method == "item/reasoning/summaryPartAdded":
                allowed = required | {"summaryIndex"}
                payload_valid = self._candidate_nonnegative_integer(
                    params.get("summaryIndex")
                )
            elif method == "item/reasoning/summaryTextDelta":
                allowed = required | {"delta", "summaryIndex"}
                payload_valid = bool(
                    isinstance(params.get("delta"), str)
                    and self._candidate_nonnegative_integer(
                        params.get("summaryIndex")
                    )
                )
            elif method == "item/reasoning/textDelta":
                allowed = required | {"contentIndex", "delta"}
                payload_valid = bool(
                    isinstance(params.get("delta"), str)
                    and self._candidate_nonnegative_integer(
                        params.get("contentIndex")
                    )
                )
            else:
                allowed = required | {"delta"}
                payload_valid = isinstance(params.get("delta"), str)
            item_id = params.get("itemId")
            item = self._items.get(item_id) if isinstance(item_id, str) else None
            valid = bool(
                set(params) == allowed
                and self._ids_match(params)
                and isinstance(item, dict)
                and item.get("type") == item_type
                and payload_valid
            )
        elif method == "turn/plan/updated":
            plan = params.get("plan")
            valid = bool(
                {"plan", "threadId", "turnId"} <= set(params)
                and set(params)
                <= {"explanation", "plan", "threadId", "turnId"}
                and self._ids_match(params)
                and (
                    params.get("explanation") is None
                    or isinstance(params.get("explanation"), str)
                )
            )
            valid = bool(
                valid
                and isinstance(plan, list)
                and all(
                    isinstance(step, dict)
                    and set(step) == {"status", "step"}
                    and step.get("status")
                    in {"pending", "inProgress", "completed"}
                    and isinstance(step.get("step"), str)
                    for step in plan
                )
            )
        elif method == "thread/tokenUsage/updated":
            usage = params.get("tokenUsage")

            def valid_breakdown(value: Any) -> bool:
                if not isinstance(value, dict):
                    return False
                required = {
                    "cachedInputTokens",
                    "inputTokens",
                    "outputTokens",
                    "reasoningOutputTokens",
                    "totalTokens",
                }
                return bool(
                    required <= set(value)
                    and set(value) <= required | {"cacheWriteInputTokens"}
                    and all(
                        self._candidate_nonnegative_integer(item)
                        for item in value.values()
                    )
                )

            valid = bool(
                set(params) == {"threadId", "tokenUsage", "turnId"}
                and self._ids_match(params)
                and isinstance(usage, dict)
                and {"last", "total"} <= set(usage)
                and set(usage) <= {"last", "modelContextWindow", "total"}
                and valid_breakdown(usage.get("last"))
                and valid_breakdown(usage.get("total"))
                and (
                    usage.get("modelContextWindow") is None
                    or self._candidate_nonnegative_integer(
                        usage.get("modelContextWindow")
                    )
                )
            )
        elif method == "thread/status/changed":
            status = params.get("status")
            valid = bool(
                set(params) == {"status", "threadId"}
                and params.get("threadId") == self._thread_id
                and isinstance(status, dict)
                and (
                    set(status) == {"type"}
                    and status.get("type") == "idle"
                    or set(status) == {"activeFlags", "type"}
                    and status.get("type") == "active"
                    and status.get("activeFlags") == []
                )
            )
        elif method == "turn/moderationMetadata":
            valid = bool(
                set(params) == {"metadata", "threadId", "turnId"}
                and self._ids_match(params)
            )
        elif method == "model/safetyBuffering/updated":
            valid = bool(
                {"model", "reasons", "showBufferingUi", "threadId", "turnId", "useCases"}
                <= set(params)
                and set(params)
                <= {
                    "fasterModel",
                    "model",
                    "reasons",
                    "showBufferingUi",
                    "threadId",
                    "turnId",
                    "useCases",
                }
                and self._ids_match(params)
                and params.get("model") == self.expected_model
                and params.get("fasterModel") is None
                and isinstance(params.get("showBufferingUi"), bool)
                and isinstance(params.get("reasons"), list)
                and all(isinstance(value, str) for value in params["reasons"])
                and isinstance(params.get("useCases"), list)
                and all(isinstance(value, str) for value in params["useCases"])
            )
        elif method == "warning":
            valid = bool(
                {"message"} <= set(params) <= {"message", "threadId"}
                and isinstance(params.get("message"), str)
                and params.get("threadId") in {None, self._thread_id}
            )
        elif method == "deprecationNotice":
            valid = bool(
                {"summary"} <= set(params) <= {"details", "summary"}
                and isinstance(params.get("summary"), str)
                and (
                    params.get("details") is None
                    or isinstance(params.get("details"), str)
                )
            )

        if not valid:
            self._candidate_event_reason_codes.add(
                "CANDIDATE_PASSIVE_NOTIFICATION_INVALID"
            )
            self._mark_identity_failure()
            return False
        self._protocol_phase = "protocol_message"
        return True

    def _dispatch(self, message: dict[str, Any]) -> None:
        passive_admission = self._candidate_passive_notification_admission(
            message
        )
        if passive_admission is not None:
            return
        if (
            message.get("method") == "item/fileChange/requestApproval"
            and "id" in message
            and (
                self._candidate_v0_2_a1 is not None
                or self._candidate_v0_2_a2 is not None
            )
        ):
            self._protocol_phase = "approval_bridge"
            params = message.get("params")
            request_id = message.get("id")
            item_id = params.get("itemId") if isinstance(params, dict) else None
            valid = bool(
                isinstance(params, dict)
                and self._ids_match(params)
                and isinstance(item_id, str)
                and item_id in self._items
                and self._items[item_id].get("type") == "fileChange"
                and self._register_approval_request(request_id, item_id)
            )
            self._mark_unsupported("unsupported_file_change_shape")
            self._candidate_event_reason_codes.add(
                "CANDIDATE_FILE_CHANGE_DECLINED"
            )
            if valid:
                self._declined_items.add(item_id)
            else:
                self._mark_identity_failure()
            self._send(
                {"id": request_id, "result": {"decision": "decline"}}
            )
            return
        if message.get("method") == "item/tool/call" and "id" in message:
            params = message.get("params")
            candidate_a1 = self._candidate_v0_2_a1 is not None
            candidate_a2 = self._candidate_v0_2_a2 is not None
            if candidate_a1:
                from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
                    SOURCE_TOOL_NAME,
                )

                if (
                    isinstance(params, dict)
                    and params.get("tool") == SOURCE_TOOL_NAME
                ):
                    self._protocol_phase = "dynamic_tool_call"
                    self._respond_fixed_source_tool_call(message)
                    return
            if (
                not candidate_a2
                and
                isinstance(params, dict)
                and params.get("tool") == FIELD_NOTE_TOOL_NAME
            ):
                self._protocol_phase = "dynamic_tool_call"
                self._respond_field_note_tool_call(message)
                return
            if candidate_a1 or candidate_a2:
                self._protocol_phase = "dynamic_tool_call"
                self._candidate_event_reason_codes.add(
                    "UNADVERTISED_DYNAMIC_TOOL_REQUEST"
                )
                self._respond_unsupported_request(message)
                return
        super()._dispatch(message)

    def _resolve_request(self, params: dict[str, Any]) -> None:
        request_id = params.get("requestId")
        if request_id in self._candidate_source_requests:
            if params.get("threadId") != self._thread_id:
                self._candidate_event_reason_codes.add(
                    "SOURCE_REQUEST_IDENTITY_MISMATCH"
                )
                self._mark_identity_failure()
                return
            self._candidate_resolved_source_requests.add(request_id)
            return
        super()._resolve_request(params)

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
        field_result = FieldNoteCodexRunResult(
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
        if self._candidate_v0_2_a1 is None:
            return field_result

        from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
            CANDIDATE_DEVELOPER_INSTRUCTIONS,
            CandidateV02A1AdmissionGate,
            IsolationEvidence,
            candidate_dynamic_tools,
            candidate_visible_input_set_sha256,
            dynamic_tool_manifest_sha256,
            fixed_source_identity_sha256,
            isolation_features_sha256,
            manual_after_contamination_codes,
            qualify_independence,
        )

        source_session = self._candidate_source_session
        assert source_session is not None
        successful_source_items = {
            call_id
            for call_id, response in self._candidate_source_responses.items()
            if response.result.success
        }
        all_sources_completed = successful_source_items.issubset(
            self._candidate_completed_source_items
        )
        proposal_lineage_complete = bool(
            len(self._candidate_proposal_started_ids) == 1
            and self._candidate_proposal_started_ids
            == set(self._proposal_responses)
            == self._completed_proposal_items
        )
        if not proposal_lineage_complete:
            self._candidate_event_reason_codes.add(
                "PROPOSAL_ITEM_LINEAGE_INCOMPLETE"
            )
        prequalification_terminal = bool(
            field_result.normal_terminal
            and all_sources_completed
            and proposal_lineage_complete
        )
        self._candidate_record_event(
            "run_terminal",
            normal_terminal=prequalification_terminal,
            turn_status=field_result.turn_status,
            runtime_status=field_result.status,
            source_items_completed=all_sources_completed,
            proposal_items_completed=all_proposals_completed,
        )
        task_bytes = prompt.encode("utf-8")
        dynamic_tools = candidate_dynamic_tools()
        runtime_identity_sha256 = (
            hashlib.sha256(
                canonical_json(
                    {
                        "model": field_result.runtime_identity.model,
                        "reasoning_effort": (
                            field_result.runtime_identity.reasoning_effort
                        ),
                        "service_tier": field_result.runtime_identity.service_tier,
                        "codex_cli_version": (
                            field_result.runtime_identity.codex_cli_version
                        ),
                        "account_type": field_result.runtime_identity.account_type,
                    }
                ).encode("utf-8")
            ).hexdigest()
            if field_result.runtime_identity is not None
            else None
        )
        prohibited = int(
            bool(
                field_result.file_actions
                or field_result.checkpoint_outcomes
                or field_result.read_evidence
                or field_result.unsupported_reason is not None
                or self._identity_failure
            )
        )
        event_reasons = set(self._candidate_event_reason_codes)
        event_reasons.update(source_session.reason_codes)
        evidence = IsolationEvidence(
            contract_identity_sha256=(
                self._candidate_v0_2_a1.contract_identity_sha256
            ),
            run_1_task_sha256=hashlib.sha256(task_bytes).hexdigest(),
            developer_instructions_sha256=hashlib.sha256(
                CANDIDATE_DEVELOPER_INSTRUCTIONS.encode("utf-8")
            ).hexdigest(),
            dynamic_tool_manifest_sha256=dynamic_tool_manifest_sha256(),
            runtime_identity_sha256=runtime_identity_sha256,
            isolation_features_sha256=isolation_features_sha256(),
            candidate_visible_input_set_sha256=(
                candidate_visible_input_set_sha256(
                    task_bytes,
                    CANDIDATE_DEVELOPER_INSTRUCTIONS.encode("utf-8"),
                    dynamic_tools,
                )
            ),
            event_log_sha256=hashlib.sha256(
                canonical_json(self._candidate_events).encode("utf-8")
            ).hexdigest(),
            source_identity_sha256=fixed_source_identity_sha256(),
            source_call_count=source_session.source_call_count,
            semantic_disclosure_count=source_session.semantic_disclosure_count,
            distinct_exposed_source_count=(
                source_session.distinct_exposed_source_count
            ),
            repository_read_count=len(field_result.read_evidence),
            current_after_access_count=0,
            git_access_count=0,
            prohibited_capability_event_count=prohibited,
            proposal_call_count=len(self._capture_proposal_call_ids),
            proposal_after_source=bool(
                self._candidate_source_success_ordinal is not None
                and self._candidate_proposal_first_ordinal is not None
                and self._candidate_proposal_first_ordinal
                > self._candidate_source_success_ordinal
            ),
            normal_terminal=prequalification_terminal,
            capability_surface_complete=(
                self._dynamic_tools() == dynamic_tools
            ),
            native_or_implicit_reader_absent=all(
                tool.get("name") != codex._READ_TOOL_NAME for tool in dynamic_tools
            ),
            manual_after_exposure_codes=manual_after_contamination_codes(
                (
                    task_bytes,
                    CANDIDATE_DEVELOPER_INSTRUCTIONS.encode("utf-8"),
                    canonical_json(dynamic_tools).encode("utf-8"),
                )
            ),
            event_reason_codes=tuple(sorted(event_reasons)),
        )
        isolation, independence = qualify_independence(evidence)
        admitted = CandidateV02A1AdmissionGate().admit(
            field_result.field_note_proposal,
            isolation=isolation,
            independence=independence,
        )
        candidate_pass = bool(
            admitted is not None
            and isolation.result == "PASS"
            and independence.result == "PASS"
            and proposal_lineage_complete
        )
        return replace(
            field_result,
            normal_terminal=(field_result.normal_terminal and candidate_pass),
            status=(
                field_result.status
                if candidate_pass or field_result.unsupported_reason is not None
                else "ABNORMAL_TERMINAL"
            ),
            error_type=(
                field_result.error_type
                if candidate_pass or field_result.unsupported_reason is not None
                else "CandidateV02IndependenceError"
            ),
            field_note_proposal=admitted,
            creator_live_a1_failure_reason=(
                field_result.creator_live_a1_failure_reason
                if field_result.creator_live_a1_failure_reason is not None
                else (
                    None
                    if candidate_pass
                    else "A1_CANDIDATE_INDEPENDENCE_NOT_PASS"
                )
            ),
            candidate_v0_2_isolation_evidence=evidence,
        )
