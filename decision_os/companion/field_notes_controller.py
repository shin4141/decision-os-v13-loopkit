"""Field Notes Lite v0.1 Capture controller."""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, replace
from functools import partial
import hashlib
import io
import os
from pathlib import Path
import stat
from typing import Any, Callable

from decision_os.acceleration.codex_adapter import (
    ADAPTER_NAME,
    CODEX_CLI_VERSION,
    CYCLE_006_CODEX_CLI_VERSION,
    CYCLE_006_CODEX_PATH,
    ORDINARY_COMPANION_CODEX_CLI_VERSION,
    ORDINARY_COMPANION_CODEX_PATH,
    CodexApproval,
    CodexLifecycleEvent,
    CodexReadEvidence,
    CodexRunResult,
    CodexRuntimeIdentity,
    _READ_MAX_BYTES,
    _READ_MAX_DISTINCT_PATHS,
    _Cycle006SubprocessTransport,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.companion.controller import (
    CompanionController,
    CompanionError,
)
from decision_os.companion.field_notes_adapter import (
    FieldNoteA1ProposalDiagnostic,
    FieldNoteCreatorLiveA1CaptureConfig,
    FieldNoteCreatorLiveCandidateV02A1Config,
    FieldNoteCreatorLiveCandidateV02A2Config,
    FieldNoteCodexRunResult,
    FieldNotesCodexAdapter,
)
from decision_os.companion.field_notes_model import (
    FieldNoteDraft,
    canonical_json,
    compile_draft,
    configured_model_class,
    validate_compiled_markdown,
)
from decision_os.companion.field_notes_reconnect import (
    FieldNoteReconnectReceipt,
)
from decision_os.companion.field_notes_creator_live_reconnect import (
    FieldNoteCreatorLiveA2ReconnectError,
    FieldNoteCreatorLiveA2ReconnectTarget,
)


class FieldNoteError(CompanionError):
    """A bounded Field Notes operation failed closed."""


def _field_notes_adapter_factory(
    engine: AccelerationEngine,
    approval_provider: Any,
    lifecycle_sink: Any,
    *,
    trusted_source_model_class: str = "UNKNOWN",
    trusted_target_model_class: str = "UNKNOWN",
    creator_live_a1_capture_provider: Any = None,
    creator_live_a2_reconnect_provider: Any = None,
    candidate_v0_2_a1_provider: Any = None,
    candidate_v0_2_a2_provider: Any = None,
) -> FieldNotesCodexAdapter:
    # The controller creates a fresh adapter for one worker.  Snapshot the
    # four paired values once so route selection and the adapter's run reset
    # cannot observe different Candidate/capture state.
    provider_values = {
        "creator_live_a1_capture": (
            creator_live_a1_capture_provider()
            if creator_live_a1_capture_provider is not None
            else None
        ),
        "creator_live_a2_reconnect": (
            creator_live_a2_reconnect_provider()
            if creator_live_a2_reconnect_provider is not None
            else None
        ),
        "candidate_v0_2_a1": (
            candidate_v0_2_a1_provider()
            if candidate_v0_2_a1_provider is not None
            else None
        ),
        "candidate_v0_2_a2": (
            candidate_v0_2_a2_provider()
            if candidate_v0_2_a2_provider is not None
            else None
        ),
    }

    def fixed_provider(name: str, original: Any) -> Any:
        if original is None:
            return None
        return lambda value=provider_values[name]: value

    creator_live_cycle_005_selected = bool(
        provider_values["creator_live_a1_capture"] is not None
        or provider_values["creator_live_a2_reconnect"] is not None
    )
    cycle_006_selected = bool(
        provider_values["candidate_v0_2_a1"] is not None
        or provider_values["candidate_v0_2_a2"] is not None
    )
    runtime_options: dict[str, Any] = {}
    if cycle_006_selected:
        engine.adapter_version = CYCLE_006_CODEX_CLI_VERSION
        runtime_options = {
            "executable": CYCLE_006_CODEX_PATH,
            "expected_cli_version": CYCLE_006_CODEX_CLI_VERSION,
            "transport_factory": _Cycle006SubprocessTransport,
        }
    elif not creator_live_cycle_005_selected:
        # Forward-only: the current ordinary route uses the already-preserved
        # verified artifact. Historical Cycle 005 runs retain CODEX_CLI_VERSION.
        engine.adapter_version = ORDINARY_COMPANION_CODEX_CLI_VERSION
        runtime_options = {
            "executable": ORDINARY_COMPANION_CODEX_PATH,
            "expected_cli_version": ORDINARY_COMPANION_CODEX_CLI_VERSION,
            "transport_factory": _Cycle006SubprocessTransport,
        }
    return FieldNotesCodexAdapter(
        engine,
        input_func=lambda: None,
        stdout=io.StringIO(),
        approval_provider=approval_provider,
        lifecycle_sink=lifecycle_sink,
        trusted_source_model_class=trusted_source_model_class,
        trusted_target_model_class=trusted_target_model_class,
        creator_live_a1_capture_provider=fixed_provider(
            "creator_live_a1_capture",
            creator_live_a1_capture_provider,
        ),
        creator_live_a2_reconnect_provider=(
            fixed_provider(
                "creator_live_a2_reconnect",
                creator_live_a2_reconnect_provider,
            )
        ),
        candidate_v0_2_a1_provider=fixed_provider(
            "candidate_v0_2_a1",
            candidate_v0_2_a1_provider,
        ),
        candidate_v0_2_a2_provider=fixed_provider(
            "candidate_v0_2_a2",
            candidate_v0_2_a2_provider,
        ),
        **runtime_options,
    )


@dataclass(frozen=True)
class _PendingSave:
    draft: FieldNoteDraft
    repository_identity: tuple[int, int]
    decision_directory_identity: tuple[int, int] | None
    field_notes_directory_identity: tuple[int, int] | None


class _ExactCreatorLiveTask(str):
    """Preserve fixed task bytes through the ordinary controller worker seam."""

    def strip(self, chars: str | None = None) -> str:
        if chars is not None:
            return str(self).strip(chars)
        return str(self)


@dataclass(frozen=True)
class FieldNoteCreatorLiveA1RunCompletion:
    """Typed facts observed from one completed creator-live Run 1."""

    run_id: str
    task_sha256: str
    actual_runtime_identity: CodexRuntimeIdentity
    proposal_attempts: int
    successful_read_count: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.run_id, str)
            or not self.run_id.strip()
            or len(self.task_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.task_sha256
            )
            or not isinstance(
                self.actual_runtime_identity,
                CodexRuntimeIdentity,
            )
            or self.proposal_attempts != 1
            or type(self.successful_read_count) is not int
            or self.successful_read_count < 0
            or self.successful_read_count > _READ_MAX_DISTINCT_PATHS
        ):
            raise ValueError("Creator-live A1 Run completion is invalid.")


@dataclass(frozen=True)
class FieldNoteCreatorLiveA2RunCompletion:
    """Typed exact reconnect evidence observed from one completed Run 2."""

    run_id: str
    task_byte_count: int
    task_sha256: str
    transmission_ordinal: int
    normal_terminal: bool
    turn_status: str
    runtime_status: str
    failure_diagnostic_absent: bool
    actual_runtime_identity: CodexRuntimeIdentity
    reconnect_receipt: FieldNoteReconnectReceipt
    final_output_bytes: bytes
    final_output_sha256: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.run_id, str)
            or not self.run_id.strip()
            or type(self.task_byte_count) is not int
            or self.task_byte_count <= 0
            or not isinstance(self.task_sha256, str)
            or len(self.task_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.task_sha256
            )
            or self.transmission_ordinal != 2
            or self.normal_terminal is not True
            or self.turn_status != "completed"
            or self.runtime_status != "NORMAL_TERMINAL"
            or self.failure_diagnostic_absent is not True
            or not isinstance(
                self.actual_runtime_identity,
                CodexRuntimeIdentity,
            )
            or not isinstance(
                self.reconnect_receipt,
                FieldNoteReconnectReceipt,
            )
            or self.reconnect_receipt.run_id != self.run_id
            or self.reconnect_receipt.state
            not in {"INJECTED", "ACTIVATION_UNKNOWN"}
            or self.reconnect_receipt.failure_reason is not None
            or self.reconnect_receipt.full_notes_injected != 1
            or not isinstance(self.final_output_bytes, bytes)
            or not self.final_output_bytes
            or len(self.final_output_bytes) > 65_536
            or hashlib.sha256(self.final_output_bytes).hexdigest()
            != self.final_output_sha256
        ):
            raise ValueError("Creator-live A2 Run completion is invalid.")


class FieldNotesCompanionController(CompanionController):
    """Companion controller extended only with Field Notes Lite Capture."""

    def __init__(self, **kwargs: Any) -> None:
        creator_live_entrypoint_factory: Callable[[Any], Any] | None = kwargs.pop(
            "creator_live_entrypoint_factory",
            None,
        )
        creator_live_cycle_006_entrypoint_factory: (
            Callable[[Any], Any] | None
        ) = kwargs.pop(
            "creator_live_cycle_006_entrypoint_factory",
            None,
        )
        self._field_note_draft: FieldNoteDraft | None = None
        self._field_note_pending: _PendingSave | None = None
        self._creator_live_a1_capture_config: (
            FieldNoteCreatorLiveA1CaptureConfig | None
        ) = None
        self._creator_live_a1_completed_run_id: str | None = None
        self._creator_live_a1_run_completion: (
            FieldNoteCreatorLiveA1RunCompletion | None
        ) = None
        self._creator_live_a1_completed_draft: FieldNoteDraft | None = None
        self._creator_live_a1_failure_reason: str | None = None
        self._creator_live_a1_direct_write_identity: str | None = None
        self._creator_live_a1_proposal_diagnostic: (
            FieldNoteA1ProposalDiagnostic | None
        ) = None
        self._creator_live_a2_reconnect_target: (
            FieldNoteCreatorLiveA2ReconnectTarget | None
        ) = None
        self._creator_live_a2_task_byte_count: int | None = None
        self._creator_live_a2_task_sha256: str | None = None
        self._creator_live_a2_completed_run_id: str | None = None
        self._creator_live_a2_run_completion: (
            FieldNoteCreatorLiveA2RunCompletion | None
        ) = None
        self._creator_live_a2_failure_reason: str | None = None
        self._candidate_v0_2_a1_config: (
            FieldNoteCreatorLiveCandidateV02A1Config | None
        ) = None
        self._candidate_v0_2_a2_config: (
            FieldNoteCreatorLiveCandidateV02A2Config | None
        ) = None
        self._candidate_v0_2_isolation_evidence: Any = None
        trusted_source_model_class = configured_model_class(
            kwargs.pop("trusted_source_model_class", "UNKNOWN")
        )
        trusted_target_model_class = configured_model_class(
            kwargs.pop("trusted_target_model_class", "UNKNOWN")
        )
        if kwargs.get("adapter_factory") is None:
            kwargs["adapter_factory"] = partial(
                _field_notes_adapter_factory,
                trusted_source_model_class=trusted_source_model_class,
                trusted_target_model_class=trusted_target_model_class,
                creator_live_a1_capture_provider=(
                    self._active_creator_live_a1_capture
                ),
                creator_live_a2_reconnect_provider=(
                    self._active_creator_live_a2_reconnect
                ),
                candidate_v0_2_a1_provider=(
                    self._active_candidate_v0_2_a1
                ),
                candidate_v0_2_a2_provider=(
                    self._active_candidate_v0_2_a2
                ),
            )
        super().__init__(**kwargs)
        if creator_live_entrypoint_factory is None:
            from decision_os.companion.field_notes_creator_live_entrypoint import (
                CreatorLiveCycle005Entrypoint,
            )

            creator_live_entrypoint_factory = CreatorLiveCycle005Entrypoint
        self._creator_live_cycle_005 = creator_live_entrypoint_factory(self)
        if creator_live_cycle_006_entrypoint_factory is None:
            from decision_os.companion.field_notes_creator_live_cycle_006 import (
                CreatorLiveCycle006Entrypoint,
            )

            creator_live_cycle_006_entrypoint_factory = (
                CreatorLiveCycle006Entrypoint
            )
        self._creator_live_cycle_006 = (
            creator_live_cycle_006_entrypoint_factory(self)
        )

    def _active_creator_live_a1_capture(
        self,
    ) -> FieldNoteCreatorLiveA1CaptureConfig | None:
        with self._condition:
            return self._creator_live_a1_capture_config

    def _active_creator_live_a2_reconnect(
        self,
    ) -> FieldNoteCreatorLiveA2ReconnectTarget | None:
        with self._condition:
            return self._creator_live_a2_reconnect_target

    def _active_candidate_v0_2_a1(
        self,
    ) -> FieldNoteCreatorLiveCandidateV02A1Config | None:
        with self._condition:
            return self._candidate_v0_2_a1_config

    def _active_candidate_v0_2_a2(
        self,
    ) -> FieldNoteCreatorLiveCandidateV02A2Config | None:
        with self._condition:
            return self._candidate_v0_2_a2_config

    @staticmethod
    def _empty_run() -> dict[str, Any]:
        run = CompanionController._empty_run()
        run["field_note"] = {"state": "none"}
        run["field_note_reconnect"] = None
        return run

    def _clear_field_note_locked(self) -> None:
        self._field_note_draft = None
        self._field_note_pending = None
        self._run["field_note"] = {"state": "none"}

    def _clear_creator_live_a2_locked(self) -> None:
        self._creator_live_a2_reconnect_target = None
        self._creator_live_a2_task_byte_count = None
        self._creator_live_a2_task_sha256 = None
        self._creator_live_a2_completed_run_id = None
        self._creator_live_a2_run_completion = None
        self._creator_live_a2_failure_reason = None
        self._candidate_v0_2_a2_config = None

    def _clear_candidate_v0_2_a1_locked(self) -> None:
        self._candidate_v0_2_a1_config = None
        self._candidate_v0_2_isolation_evidence = None

    def _require_cycle_006_mutation_allowed_locked(self) -> None:
        if self.creator_live_cycle_006_mutation_blocked():
            raise FieldNoteError("CREATOR_LIVE_CYCLE_006_ACTIVE")

    def _require_cycle_006_field_note_authority_locked(
        self,
        authority: object | None,
    ) -> None:
        if authority is None:
            self._require_cycle_006_mutation_allowed_locked()
            return
        if (
            authority is not self._creator_live_cycle_006
            or not self.creator_live_cycle_006_mutation_blocked()
        ):
            raise FieldNoteError(
                "CREATOR_LIVE_CYCLE_006_INTERNAL_AUTHORITY_INVALID"
            )

    @contextmanager
    def _cycle_006_guarded_operation(self, operation: Any) -> Any:
        stack = ExitStack()
        with self._condition:
            self._require_cycle_006_mutation_allowed_locked()
            value = stack.enter_context(operation)
        with stack:
            yield value

    @contextmanager
    def _bridge_operation(self) -> Any:
        with self._cycle_006_guarded_operation(
            super()._bridge_operation()
        ) as value:
            yield value

    @contextmanager
    def _guided_intake_operation(self) -> Any:
        with self._cycle_006_guarded_operation(
            super()._guided_intake_operation()
        ) as value:
            yield value

    @contextmanager
    def _ordinary_user_path_operation(self) -> Any:
        with self._cycle_006_guarded_operation(
            super()._ordinary_user_path_operation()
        ) as value:
            yield value

    @contextmanager
    def _guided_intake_bridge_operation(self) -> Any:
        with self._cycle_006_guarded_operation(
            super()._guided_intake_bridge_operation()
        ) as value:
            yield value

    @contextmanager
    def _intelligence_transplant_operation(self) -> Any:
        with self._cycle_006_guarded_operation(
            super()._intelligence_transplant_operation()
        ) as value:
            yield value

    @contextmanager
    def _guided_intake_transplant_operation(self) -> Any:
        with self._cycle_006_guarded_operation(
            super()._guided_intake_transplant_operation()
        ) as value:
            yield value

    def start_run(self, task: str, *, task_mode: str = "manual") -> dict[str, Any]:
        with self._condition:
            if self.creator_live_cycle_005_mutation_blocked():
                raise FieldNoteError("CREATOR_LIVE_CYCLE_005_ACTIVE")
            if self.creator_live_cycle_006_mutation_blocked():
                raise FieldNoteError("CREATOR_LIVE_CYCLE_006_ACTIVE")
            self._require_no_active_run()
            self._clear_field_note_locked()
            self._clear_candidate_v0_2_a1_locked()
            self._clear_creator_live_a2_locked()
            return super().start_run(task, task_mode=task_mode)

    def start_creator_live_a1_capture(
        self,
        task: str,
        *,
        run_id: str,
        expected_runtime_identity: CodexRuntimeIdentity,
    ) -> dict[str, Any]:
        """Start one read-only Run whose only capture path is the A1 tool."""

        config = FieldNoteCreatorLiveA1CaptureConfig(
            run_id=run_id,
            expected_runtime_identity=expected_runtime_identity,
        )
        with self._condition:
            self._require_no_active_run()
            self._clear_field_note_locked()
            self._clear_candidate_v0_2_a1_locked()
            if self._creator_live_a2_reconnect_target is not None:
                raise FieldNoteError("Creator-live A2 reconnect is active.")
            self._clear_creator_live_a2_locked()
            self._creator_live_a1_capture_config = config
            self._creator_live_a1_completed_run_id = None
            self._creator_live_a1_run_completion = None
            self._creator_live_a1_completed_draft = None
            self._creator_live_a1_failure_reason = None
            self._creator_live_a1_direct_write_identity = None
            self._creator_live_a1_proposal_diagnostic = None
        try:
            return super().start_run(task, task_mode="manual")
        except Exception:
            with self._condition:
                self._creator_live_a1_capture_config = None
            raise

    def start_creator_live_candidate_v0_2_a1(
        self,
        task: str,
        *,
        run_id: str,
        expected_runtime_identity: CodexRuntimeIdentity,
        contract_identity_sha256: str,
        turn_start_intent_observer: Callable[[str], None] | None = None,
        turn_started_observer: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Start the fixed Candidate v0.2 Run 1 without normalizing bytes."""

        from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
            RUN_1_BYTE_COUNT,
            RUN_1_SHA256,
        )

        if not isinstance(task, str):
            raise FieldNoteError("A1_TASK_IDENTITY_MISMATCH")
        try:
            task_bytes = task.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise FieldNoteError("A1_TASK_IDENTITY_MISMATCH") from exc
        if (
            len(task_bytes) != RUN_1_BYTE_COUNT
            or hashlib.sha256(task_bytes).hexdigest() != RUN_1_SHA256
        ):
            raise FieldNoteError("A1_TASK_IDENTITY_MISMATCH")
        capture = FieldNoteCreatorLiveA1CaptureConfig(
            run_id=run_id,
            expected_runtime_identity=expected_runtime_identity,
        )
        candidate = FieldNoteCreatorLiveCandidateV02A1Config(
            run_id=run_id,
            expected_runtime_identity=expected_runtime_identity,
            contract_identity_sha256=contract_identity_sha256,
            turn_start_intent_observer=turn_start_intent_observer,
            turn_started_observer=turn_started_observer,
        )
        with self._condition:
            self._require_no_active_run()
            self._clear_field_note_locked()
            self._clear_creator_live_a2_locked()
            self._creator_live_a1_capture_config = capture
            self._candidate_v0_2_a1_config = candidate
            self._candidate_v0_2_isolation_evidence = None
            self._creator_live_a1_completed_run_id = None
            self._creator_live_a1_run_completion = None
            self._creator_live_a1_completed_draft = None
            self._creator_live_a1_failure_reason = None
            self._creator_live_a1_direct_write_identity = None
            self._creator_live_a1_proposal_diagnostic = None
        try:
            return super().start_run(
                _ExactCreatorLiveTask(task),
                task_mode="manual",
            )
        except Exception:
            with self._condition:
                self._creator_live_a1_capture_config = None
                self._clear_candidate_v0_2_a1_locked()
            raise

    def start_creator_live_a2_reconnect(
        self,
        task: str,
        *,
        target: FieldNoteCreatorLiveA2ReconnectTarget,
    ) -> dict[str, Any]:
        """Start one Run 2 whose reconnect input is one durable exact target."""

        if not isinstance(target, FieldNoteCreatorLiveA2ReconnectTarget):
            raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
        try:
            task_bytes = task.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise FieldNoteCreatorLiveA2ReconnectError(
                "A2_TARGET_INVALID"
            ) from exc
        if not task_bytes:
            raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
        with self._condition:
            self._require_no_active_run()
            if self._creator_live_a1_capture_config is not None:
                raise FieldNoteCreatorLiveA2ReconnectError(
                    "A2_TARGET_INVALID"
                )
            self._clear_field_note_locked()
            self._clear_creator_live_a2_locked()
            self._creator_live_a2_reconnect_target = target
            self._creator_live_a2_task_byte_count = len(task_bytes)
            self._creator_live_a2_task_sha256 = hashlib.sha256(
                task_bytes
            ).hexdigest()
        try:
            return super().start_run(task, task_mode="manual")
        except Exception:
            with self._condition:
                self._clear_creator_live_a2_locked()
            raise

    def start_creator_live_candidate_v0_2_a2(
        self,
        task: str,
        *,
        target: FieldNoteCreatorLiveA2ReconnectTarget,
        post_a1_readback_path: Path,
        post_a1_readback_sha256: str,
        turn_start_intent_observer: Callable[[str], None] | None = None,
        turn_started_observer: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Start fixed exact A2 with no dynamic tools or task normalization."""

        from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
            RUN_2_BYTE_COUNT,
            RUN_2_SHA256,
        )

        if not isinstance(target, FieldNoteCreatorLiveA2ReconnectTarget):
            raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
        if not isinstance(task, str):
            raise FieldNoteError("A2_TASK_IDENTITY_MISMATCH")
        try:
            task_bytes = task.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise FieldNoteError("A2_TASK_IDENTITY_MISMATCH") from exc
        if (
            len(task_bytes) != RUN_2_BYTE_COUNT
            or hashlib.sha256(task_bytes).hexdigest() != RUN_2_SHA256
        ):
            raise FieldNoteError("A2_TASK_IDENTITY_MISMATCH")
        candidate = FieldNoteCreatorLiveCandidateV02A2Config(
            readback_path=str(Path(post_a1_readback_path)),
            readback_sha256=post_a1_readback_sha256,
            turn_start_intent_observer=turn_start_intent_observer,
            turn_started_observer=turn_started_observer,
        )
        with self._condition:
            self._require_no_active_run()
            if self._creator_live_a1_capture_config is not None:
                raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
            self._clear_field_note_locked()
            self._clear_creator_live_a2_locked()
            self._creator_live_a2_reconnect_target = target
            self._candidate_v0_2_a2_config = candidate
            self._creator_live_a2_task_byte_count = len(task_bytes)
            self._creator_live_a2_task_sha256 = hashlib.sha256(
                task_bytes
            ).hexdigest()
        try:
            return super().start_run(
                _ExactCreatorLiveTask(task),
                task_mode="manual",
            )
        except Exception:
            with self._condition:
                self._clear_creator_live_a2_locked()
            raise

    def new_run(self) -> dict[str, Any]:
        with self._condition:
            self._require_cycle_006_mutation_allowed_locked()
            self._clear_field_note_locked()
            self._clear_candidate_v0_2_a1_locked()
            self._creator_live_a1_capture_config = None
            self._creator_live_a1_completed_run_id = None
            self._creator_live_a1_run_completion = None
            self._creator_live_a1_completed_draft = None
            self._creator_live_a1_failure_reason = None
            self._creator_live_a1_direct_write_identity = None
            self._creator_live_a1_proposal_diagnostic = None
            self._clear_creator_live_a2_locked()
            return super().new_run()

    def select_repository(self, candidate: str | Path) -> dict[str, Any]:
        with self._condition:
            self._require_cycle_006_mutation_allowed_locked()
            super().select_repository(candidate)
            self._clear_field_note_locked()
            self._clear_candidate_v0_2_a1_locked()
            self._creator_live_a1_capture_config = None
            self._creator_live_a1_completed_run_id = None
            self._creator_live_a1_run_completion = None
            self._creator_live_a1_completed_draft = None
            self._creator_live_a1_failure_reason = None
            self._creator_live_a1_direct_write_identity = None
            self._creator_live_a1_proposal_diagnostic = None
            self._clear_creator_live_a2_locked()
            return self._snapshot_locked()

    @staticmethod
    def _has_completion_evidence(result: CodexRunResult) -> bool:
        return bool(
            result.file_actions
            or result.read_evidence
            or result.checkpoint_outcomes
        )

    @classmethod
    def _eligible_draft(
        cls,
        result: CodexRunResult,
    ) -> FieldNoteDraft | None:
        draft = getattr(result, "field_note_proposal", None)
        if not isinstance(draft, FieldNoteDraft):
            return None
        try:
            validate_compiled_markdown(draft.markdown)
        except ValueError:
            return None
        if (
            draft.source_run_id != result.run_id
            or hashlib.sha256(draft.markdown).hexdigest() != draft.sha256
            or not result.normal_terminal
            or result.turn_status != "completed"
            or result.status
            not in {"NORMAL_TERMINAL", "VERIFIED_SAVE", "VERIFIED_REUSE"}
            or result.failure_diagnostic is not None
            or not cls._has_completion_evidence(result)
            or not draft.body_value("evidence").strip()
            or not draft.body_value("remaining_unknowns").strip()
        ):
            return None
        return draft

    @staticmethod
    def _creator_live_successful_read(
        evidence: CodexReadEvidence,
    ) -> bool:
        return bool(
            isinstance(evidence, CodexReadEvidence)
            and evidence.status == "succeeded"
            and isinstance(evidence.path, str)
            and evidence.path
            and type(evidence.byte_count) is int
            and evidence.byte_count >= 0
            and evidence.byte_count <= _READ_MAX_BYTES
            and isinstance(evidence.sha256, str)
            and len(evidence.sha256) == 64
            and all(
                character in "0123456789abcdef"
                for character in evidence.sha256
            )
            and isinstance(evidence.repository_identity, str)
            and bool(evidence.repository_identity)
            and evidence.reason is None
        )

    @classmethod
    def _eligible_creator_live_draft(
        cls,
        result: CodexRunResult,
        *,
        expected_runtime_identity: CodexRuntimeIdentity,
    ) -> FieldNoteDraft | None:
        draft = getattr(result, "field_note_proposal", None)
        task_sha256 = getattr(
            result,
            "creator_live_a1_task_sha256",
            None,
        )
        if not isinstance(draft, FieldNoteDraft):
            return None
        try:
            validate_compiled_markdown(draft.markdown)
        except ValueError:
            return None
        if (
            getattr(result, "creator_live_a1_capture", False) is not True
            or getattr(result, "creator_live_a1_failure_reason", None)
            is not None
            or getattr(result, "creator_live_a1_proposal_attempts", 0) != 1
            or not isinstance(task_sha256, str)
            or len(task_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in task_sha256
            )
            or result.runtime_identity != expected_runtime_identity
            or draft.source_run_id != result.run_id
            or hashlib.sha256(draft.markdown).hexdigest() != draft.sha256
            or not result.normal_terminal
            or result.turn_status != "completed"
            or result.status
            not in {"NORMAL_TERMINAL", "VERIFIED_SAVE", "VERIFIED_REUSE"}
            or result.failure_diagnostic is not None
            or result.file_actions
            or result.checkpoint_outcomes
            or len(result.read_evidence) > _READ_MAX_DISTINCT_PATHS
            or len(
                {
                    evidence.path
                    for evidence in result.read_evidence
                }
            ) != len(result.read_evidence)
            or any(
                not cls._creator_live_successful_read(evidence)
                for evidence in result.read_evidence
            )
            or not draft.body_value("evidence").strip()
            or not draft.body_value("remaining_unknowns").strip()
        ):
            return None
        return draft

    def _complete_run(
        self,
        repository: Path,
        result: CodexRunResult,
    ) -> None:
        capture = self._creator_live_a1_capture_config
        reconnect_target = self._creator_live_a2_reconnect_target
        candidate_a1 = self._candidate_v0_2_a1_config
        candidate_a2 = self._candidate_v0_2_a2_config
        capture_failure = getattr(
            result,
            "creator_live_a1_failure_reason",
            None,
        )
        completion: FieldNoteCreatorLiveA1RunCompletion | None = None
        reconnect_completion: FieldNoteCreatorLiveA2RunCompletion | None = None
        reconnect_failure: str | None = None
        proposal_diagnostic: FieldNoteA1ProposalDiagnostic | None = None
        if capture is not None:
            if (
                getattr(result, "creator_live_a1_capture", False) is not True
                or result.run_id != capture.run_id
            ):
                capture_failure = "A1_CAPTURE_IDENTITY_MISMATCH"
            elif capture_failure is None and result.runtime_identity is None:
                capture_failure = "A1_ACTUAL_RUNTIME_IDENTITY_MISSING"
            elif capture_failure is None and (
                result.runtime_identity
                != capture.expected_runtime_identity
            ):
                capture_failure = "A1_ACTUAL_RUNTIME_IDENTITY_MISMATCH"
            elif capture_failure is None and any(
                evidence.status != "succeeded"
                for evidence in result.read_evidence
            ):
                capture_failure = "A1_READ_EVIDENCE_FAILED"
            raw_diagnostic = getattr(
                result,
                "creator_live_a1_proposal_diagnostic",
                None,
            )
            if isinstance(raw_diagnostic, FieldNoteA1ProposalDiagnostic):
                try:
                    proposal_diagnostic = (
                        FieldNoteA1ProposalDiagnostic.from_dict(
                            raw_diagnostic.as_dict()
                        )
                    )
                except ValueError:
                    proposal_diagnostic = None
            proposal_failure = bool(
                isinstance(capture_failure, str)
                and capture_failure.startswith("A1_PROPOSAL_")
            )
            direct_write_failure = (
                capture_failure == "A1_DIRECT_WRITE_REQUESTED"
            )
            if proposal_diagnostic is None:
                if (
                    capture_failure is None
                    or proposal_failure
                    or direct_write_failure
                ):
                    capture_failure = "A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE"
            elif proposal_diagnostic.final_subcause is not None:
                if capture_failure is None or proposal_failure:
                    capture_failure = proposal_diagnostic.final_subcause
                elif (
                    direct_write_failure
                    and proposal_diagnostic.final_subcause
                    != "A1_DIRECT_WRITE_REQUESTED"
                ):
                    capture_failure = "A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE"
            elif proposal_failure or direct_write_failure:
                capture_failure = "A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE"
            if (
                proposal_diagnostic is not None
                and proposal_diagnostic.final_subcause
                == "A1_DIRECT_WRITE_REQUESTED"
                and self._creator_live_a1_direct_write_identity is not None
            ):
                proposal_diagnostic = (
                    proposal_diagnostic.with_direct_write_identity(
                        self._creator_live_a1_direct_write_identity
                    )
                )
                if isinstance(result, FieldNoteCodexRunResult):
                    result = replace(
                        result,
                        creator_live_a1_proposal_diagnostic=(
                            proposal_diagnostic
                        ),
                    )
            draft = (
                self._eligible_creator_live_draft(
                    result,
                    expected_runtime_identity=(
                        capture.expected_runtime_identity
                    ),
                )
                if capture_failure is None
                else None
            )
            if draft is not None:
                assert result.runtime_identity is not None
                completion = FieldNoteCreatorLiveA1RunCompletion(
                    run_id=result.run_id,
                    task_sha256=getattr(
                        result,
                        "creator_live_a1_task_sha256",
                    ),
                    actual_runtime_identity=result.runtime_identity,
                    proposal_attempts=getattr(
                        result,
                        "creator_live_a1_proposal_attempts",
                    ),
                    successful_read_count=len(result.read_evidence),
                )
            if candidate_a1 is not None:
                from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
                    IsolationEvidence,
                    qualify_independence,
                )

                candidate_evidence = getattr(
                    result,
                    "candidate_v0_2_isolation_evidence",
                    None,
                )
                if not isinstance(candidate_evidence, IsolationEvidence):
                    capture_failure = "A1_CANDIDATE_EVIDENCE_MISSING"
                    completion = None
                    draft = None
                else:
                    isolation, independence = qualify_independence(
                        candidate_evidence
                    )
                    if isolation.result != "PASS" or independence.result != "PASS":
                        capture_failure = "A1_CANDIDATE_INDEPENDENCE_NOT_PASS"
                        completion = None
                        draft = None
        elif reconnect_target is not None:
            draft = None
            reconnect_receipt = getattr(result, "reconnect_receipt", None)
            if result.run_id != reconnect_target.run_2_id:
                reconnect_failure = "A2_TARGET_RUN_2_MISMATCH"
            elif result.runtime_identity != (
                reconnect_target.expected_runtime_identity
            ):
                reconnect_failure = "A2_TARGET_INVALID"
            elif not isinstance(
                reconnect_receipt,
                FieldNoteReconnectReceipt,
            ):
                reconnect_failure = "A2_TARGET_INVALID"
            elif reconnect_receipt.run_id != reconnect_target.run_2_id:
                reconnect_failure = "A2_TARGET_RUN_2_MISMATCH"
            elif reconnect_receipt.selected_field_note_path != (
                reconnect_target.note_relative_path
            ):
                reconnect_failure = "A2_TARGET_PATH_INVALID"
            elif reconnect_receipt.selected_field_note_id != (
                reconnect_target.field_note_id
            ):
                reconnect_failure = "A2_TARGET_NOTE_ID_MISMATCH"
            elif reconnect_receipt.selected_full_note_sha256 != (
                reconnect_target.note_sha256
            ):
                reconnect_failure = "A2_TARGET_SHA256_MISMATCH"
            elif reconnect_receipt.full_note_bytes_read != (
                reconnect_target.note_byte_count
            ):
                reconnect_failure = "A2_TARGET_BYTE_COUNT_MISMATCH"
            elif (
                reconnect_receipt.state
                not in {"INJECTED", "ACTIVATION_UNKNOWN"}
                or reconnect_receipt.full_notes_injected != 1
                or reconnect_receipt.ordinary_distinct_paths_consumed != 0
                or reconnect_receipt.failure_reason is not None
            ):
                reconnect_failure = "A2_TARGET_INVALID"
            else:
                assert result.runtime_identity is not None
                try:
                    final_output_bytes = result.final_message.encode("utf-8")
                except UnicodeEncodeError:
                    reconnect_failure = "A2_OUTPUT_INVALID"
                    final_output_bytes = b""
                if (
                    reconnect_failure is None
                    and (
                        not result.normal_terminal
                        or result.turn_status != "completed"
                        or result.status != "NORMAL_TERMINAL"
                        or result.failure_diagnostic is not None
                        or getattr(result, "field_note_proposal", None)
                        is not None
                        or result.file_actions
                        or result.checkpoint_outcomes
                        or result.read_evidence
                        or not final_output_bytes
                        or len(final_output_bytes) > 65_536
                    )
                ):
                    reconnect_failure = "A2_OUTPUT_INVALID"
                if reconnect_failure is not None:
                    final_output_bytes = b""
            if reconnect_failure is None:
                assert result.runtime_identity is not None
                if (
                    self._creator_live_a2_task_byte_count is None
                    or self._creator_live_a2_task_sha256 is None
                ):
                    reconnect_failure = "A2_TARGET_INVALID"
            if reconnect_failure is None:
                assert result.runtime_identity is not None
                assert self._creator_live_a2_task_byte_count is not None
                assert self._creator_live_a2_task_sha256 is not None
                reconnect_completion = FieldNoteCreatorLiveA2RunCompletion(
                    run_id=result.run_id,
                    task_byte_count=self._creator_live_a2_task_byte_count,
                    task_sha256=self._creator_live_a2_task_sha256,
                    transmission_ordinal=2,
                    normal_terminal=result.normal_terminal,
                    turn_status=result.turn_status,
                    runtime_status=result.status,
                    failure_diagnostic_absent=(
                        result.failure_diagnostic is None
                    ),
                    actual_runtime_identity=result.runtime_identity,
                    reconnect_receipt=reconnect_receipt,
                    final_output_bytes=final_output_bytes,
                    final_output_sha256=hashlib.sha256(
                        final_output_bytes
                    ).hexdigest(),
                )
        else:
            draft = self._eligible_draft(result)
        reconnect_receipt = getattr(result, "reconnect_receipt", None)
        reconnect_projection = (
            reconnect_receipt.as_dict()
            if isinstance(reconnect_receipt, FieldNoteReconnectReceipt)
            and reconnect_receipt.run_id == result.run_id
            else None
        )
        with self._condition:
            super()._complete_run(repository, result)
            if capture is not None:
                self._creator_live_a1_completed_run_id = capture.run_id
                self._creator_live_a1_capture_config = None
                self._candidate_v0_2_a1_config = None
                self._candidate_v0_2_isolation_evidence = (
                    candidate_evidence if candidate_a1 is not None else None
                )
            if reconnect_target is not None:
                self._creator_live_a2_completed_run_id = (
                    reconnect_target.run_2_id
                )
                self._creator_live_a2_reconnect_target = None
                self._candidate_v0_2_a2_config = None
                self._creator_live_a2_run_completion = reconnect_completion
                self._creator_live_a2_failure_reason = reconnect_failure
                self._run["result"] = ""
            self._creator_live_a1_run_completion = completion
            if capture is not None:
                self._creator_live_a1_completed_draft = draft
            self._creator_live_a1_failure_reason = capture_failure
            self._creator_live_a1_proposal_diagnostic = proposal_diagnostic
            self._run["field_note_reconnect"] = reconnect_projection
            if draft is None:
                self._clear_field_note_locked()
            else:
                self._field_note_draft = draft
                self._field_note_pending = None
                self._run["field_note"] = draft.public_candidate()
            self._condition.notify_all()

    def _approval_provider(self, approval: CodexApproval) -> str | None:
        with self._condition:
            capture_active = bool(
                self._creator_live_a1_capture_config is not None
                or self._candidate_v0_2_a1_config is not None
                or self._candidate_v0_2_a2_config is not None
            )
        if not capture_active:
            return super()._approval_provider(approval)
        if not isinstance(approval, CodexApproval):
            raise FieldNoteError("Malformed creator-live file request.")
        diagnostic = {
            "action": str(approval.action),
            "path": str(approval.normalized_scope),
            "repository": str(approval.repository_name),
        }
        identity = hashlib.sha256(
            canonical_json(diagnostic).encode("utf-8")
        ).hexdigest()
        with self._condition:
            self._creator_live_a1_direct_write_identity = identity
        return "3"

    def creator_live_a1_capture_candidate(self) -> FieldNoteDraft:
        """Return the exact eligible capture candidate without exposing a body."""

        with self._condition:
            run_id = self._creator_live_a1_completed_run_id
            if run_id is None:
                raise FieldNoteError("No creator-live A1 capture is active.")
            if self._run.get("state") == "running":
                raise FieldNoteError("Creator-live A1 capture is still running.")
            if self._creator_live_a1_failure_reason is not None:
                suffix = (
                    f":{self._creator_live_a1_direct_write_identity}"
                    if self._creator_live_a1_failure_reason
                    == "A1_DIRECT_WRITE_REQUESTED"
                    and self._creator_live_a1_direct_write_identity is not None
                    else ""
                )
                raise FieldNoteError(
                    f"{self._creator_live_a1_failure_reason}{suffix}"
                )
            if self._field_note_draft is None:
                raise FieldNoteError("A1_PROPOSAL_INVALID")
            if self._field_note_draft.source_run_id != run_id:
                raise FieldNoteError("A1_CAPTURE_IDENTITY_MISMATCH")
            return self._field_note_draft

    def creator_live_a1_run_completion(
        self,
    ) -> FieldNoteCreatorLiveA1RunCompletion:
        """Return the exact typed Run-1 completion consumed by the bridge."""

        with self._condition:
            completion = self._creator_live_a1_run_completion
            if completion is None:
                reason = self._creator_live_a1_failure_reason
                if reason is not None:
                    raise FieldNoteError(reason)
                raise FieldNoteError(
                    "Creator-live A1 Run completion is unavailable."
                )
            return completion

    def creator_live_a1_completed_draft(
        self,
        *,
        expected_run_id: str,
    ) -> FieldNoteDraft:
        """Return the private typed A1 draft retained for A7 construction."""

        with self._condition:
            draft = self._creator_live_a1_completed_draft
            if (
                not isinstance(expected_run_id, str)
                or not expected_run_id
                or draft is None
                or draft.source_run_id != expected_run_id
            ):
                raise FieldNoteError("A1_CAPTURE_IDENTITY_MISMATCH")
            return draft

    def creator_live_a1_proposal_diagnostic(
        self,
        *,
        expected_run_id: str,
    ) -> FieldNoteA1ProposalDiagnostic:
        """Return the digest-verified diagnostic for the exact completed Run."""

        with self._condition:
            if (
                not isinstance(expected_run_id, str)
                or not expected_run_id
                or self._creator_live_a1_completed_run_id != expected_run_id
            ):
                raise FieldNoteError("A1_CAPTURE_IDENTITY_MISMATCH")
            diagnostic = self._creator_live_a1_proposal_diagnostic
            if diagnostic is None:
                raise FieldNoteError("A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE")
            try:
                return FieldNoteA1ProposalDiagnostic.from_dict(
                    diagnostic.as_dict()
                )
            except ValueError as exc:
                raise FieldNoteError(
                    "A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE"
                ) from exc

    def creator_live_a1_failure_reason(
        self,
        *,
        expected_run_id: str,
    ) -> str | None:
        """Return the exact established failure family for one completed Run."""

        with self._condition:
            if (
                not isinstance(expected_run_id, str)
                or not expected_run_id
                or self._creator_live_a1_completed_run_id != expected_run_id
            ):
                raise FieldNoteError("A1_CAPTURE_IDENTITY_MISMATCH")
            if self._run.get("state") == "running":
                raise FieldNoteError("Creator-live A1 capture is still running.")
            return self._creator_live_a1_failure_reason

    def creator_live_candidate_v0_2_isolation_evidence(
        self,
        *,
        expected_run_id: str,
    ) -> Any:
        """Return the private fixed-source evidence for the completed Run 1."""

        from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
            IsolationEvidence,
        )

        with self._condition:
            if (
                self._creator_live_a1_completed_run_id != expected_run_id
                or not isinstance(
                    self._candidate_v0_2_isolation_evidence,
                    IsolationEvidence,
                )
            ):
                raise FieldNoteError("A1_CANDIDATE_EVIDENCE_MISSING")
            return self._candidate_v0_2_isolation_evidence

    def creator_live_a2_run_completion(
        self,
        *,
        expected_run_id: str,
    ) -> FieldNoteCreatorLiveA2RunCompletion:
        """Return exact injected reconnect evidence for one completed Run 2."""

        with self._condition:
            if (
                not isinstance(expected_run_id, str)
                or not expected_run_id
                or self._creator_live_a2_completed_run_id != expected_run_id
            ):
                raise FieldNoteError("A2_TARGET_RUN_2_MISMATCH")
            if self._run.get("state") == "running":
                raise FieldNoteError("Creator-live A2 reconnect is still running.")
            completion = self._creator_live_a2_run_completion
            if completion is None:
                raise FieldNoteError(
                    self._creator_live_a2_failure_reason
                    or "A2_TARGET_INVALID"
                )
            return completion

    def release_creator_live_a2_run_completion(
        self,
        *,
        expected_run_id: str,
    ) -> None:
        """Discard the controller-owned transient Run 2 output bytes."""

        with self._condition:
            if (
                not isinstance(expected_run_id, str)
                or not expected_run_id
                or self._creator_live_a2_completed_run_id != expected_run_id
            ):
                raise FieldNoteError("A2_TARGET_RUN_2_MISMATCH")
            self._creator_live_a2_run_completion = None
            self._run["result"] = ""

    def creator_live_a2_failure_reason(
        self,
        *,
        expected_run_id: str,
    ) -> str | None:
        """Return the exact fail-closed preparation reason for one Run 2."""

        with self._condition:
            if (
                not isinstance(expected_run_id, str)
                or not expected_run_id
                or self._creator_live_a2_completed_run_id != expected_run_id
            ):
                raise FieldNoteError("A2_TARGET_RUN_2_MISMATCH")
            if self._run.get("state") == "running":
                raise FieldNoteError("Creator-live A2 reconnect is still running.")
            return self._creator_live_a2_failure_reason

    def _fail_run(self, repository: Path, exc: Exception) -> None:
        with self._condition:
            super()._fail_run(repository, exc)
            if self._creator_live_a1_capture_config is not None:
                self._creator_live_a1_completed_run_id = (
                    self._creator_live_a1_capture_config.run_id
                )
                self._creator_live_a1_capture_config = None
                self._creator_live_a1_failure_reason = "A1_RUN_FAILED"
                self._creator_live_a1_run_completion = None
                self._creator_live_a1_completed_draft = None
                self._creator_live_a1_proposal_diagnostic = None
                self._candidate_v0_2_a1_config = None
                self._candidate_v0_2_isolation_evidence = None
            if self._creator_live_a2_reconnect_target is not None:
                self._creator_live_a2_completed_run_id = (
                    self._creator_live_a2_reconnect_target.run_2_id
                )
                self._creator_live_a2_reconnect_target = None
                self._creator_live_a2_failure_reason = (
                    exc.code
                    if isinstance(
                        exc,
                        FieldNoteCreatorLiveA2ReconnectError,
                    )
                    else "A2_TARGET_INVALID"
                )
                self._creator_live_a2_run_completion = None
                self._candidate_v0_2_a2_config = None
            self._clear_field_note_locked()
            self._condition.notify_all()

    @staticmethod
    def _case_collision(parent: Path, filename: str) -> bool:
        if not parent.exists():
            return False
        try:
            return any(
                child.name.casefold() == filename.casefold()
                for child in parent.iterdir()
            )
        except OSError as exc:
            raise FieldNoteError(
                "Field Note directory cannot be inspected safely."
            ) from exc

    @staticmethod
    def _proposal_arguments(draft: FieldNoteDraft) -> dict[str, Any]:
        return {
            "title": draft.title,
            "value_level": draft.value_level,
            "source_model_class": draft.source_model_class,
            "target_model_class": draft.target_model_class,
            "trigger_terms": list(draft.trigger_terms),
            "scope": {
                "task_family": draft.task_family,
                "path_prefixes": list(draft.path_prefixes),
                "exclude_terms": list(draft.exclude_terms),
            },
            "body": dict(draft.body),
        }

    def _safe_candidate_path(self, draft: FieldNoteDraft) -> FieldNoteDraft:
        repository = self._require_repository().resolve(strict=True)
        current = draft
        for _ in range(8):
            filename = self._field_note_filename(current)
            target = repository / ".decision-os" / "field-notes" / filename
            if (
                not target.exists()
                and not target.is_symlink()
                and not self._case_collision(target.parent, target.name)
            ):
                return current
            current = compile_draft(
                self._proposal_arguments(current),
                source_run_id=current.source_run_id,
                created_at=current.created_at,
            )
        raise FieldNoteError(
            "A collision-free Field Note path could not be prepared."
        )

    def field_note_save(
        self,
        *,
        _cycle_006_authority: object | None = None,
    ) -> dict[str, Any]:
        with self._condition:
            self._require_cycle_006_field_note_authority_locked(
                _cycle_006_authority
            )
            if (
                self._run.get("state") != "completed"
                or self._field_note_draft is None
            ):
                raise FieldNoteError(
                    "No eligible Field Note candidate is available."
                )
            if self._field_note_pending is not None:
                raise FieldNoteError("A Field Note Approval is already pending.")
            draft = self._safe_candidate_path(self._field_note_draft)
            try:
                validate_compiled_markdown(draft.markdown)
            except ValueError as exc:
                raise FieldNoteError(
                    "Field Note compiled structure is invalid."
                ) from exc
            if hashlib.sha256(draft.markdown).hexdigest() != draft.sha256:
                raise FieldNoteError(
                    "Field Note compiled digest is invalid."
                )
            (
                repository_identity,
                decision_directory_identity,
                field_notes_directory_identity,
            ) = self._capture_parent_identities()
            self._field_note_draft = draft
            self._field_note_pending = _PendingSave(
                draft,
                repository_identity,
                decision_directory_identity,
                field_notes_directory_identity,
            )
            self._run["field_note"] = {
                "state": "approval",
                "title": draft.title,
                "approval": {
                    "action": "CREATE",
                    "path": draft.relative_path,
                    "content": draft.markdown.decode("utf-8"),
                    "content_sha256": draft.sha256,
                    "precondition": "MUST_NOT_EXIST",
                    "approval_scope": "THIS ONE FILE ONLY",
                },
            }
            return self._snapshot_locked()

    def field_note_skip(self) -> dict[str, Any]:
        with self._condition:
            self._require_cycle_006_mutation_allowed_locked()
            if self._field_note_draft is None:
                raise FieldNoteError("No Field Note candidate is available.")
            self._field_note_draft = None
            self._field_note_pending = None
            self._run["field_note"] = {"state": "skipped"}
            return self._snapshot_locked()

    @staticmethod
    def _descriptor_containment_supported() -> None:
        if (
            not getattr(os, "O_DIRECTORY", 0)
            or not getattr(os, "O_NOFOLLOW", 0)
            or os.open not in os.supports_dir_fd
            or os.mkdir not in os.supports_dir_fd
            or os.stat not in os.supports_dir_fd
            or os.stat not in os.supports_follow_symlinks
            or os.unlink not in os.supports_dir_fd
            or os.listdir not in os.supports_fd
        ):
            raise FieldNoteError(
                "Descriptor-bound Field Note containment is unavailable."
            )

    @staticmethod
    def _identity(info: os.stat_result) -> tuple[int, int]:
        return (info.st_dev, info.st_ino)

    @classmethod
    def _open_repository_descriptor(
        cls,
        repository: Path,
        expected_identity: tuple[int, int] | None = None,
    ) -> tuple[int, tuple[int, int]]:
        descriptor: int | None = None
        flags = (
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            linked = repository.lstat()
            descriptor = os.open(repository, flags)
            opened = os.fstat(descriptor)
        except OSError as exc:
            if descriptor is not None:
                os.close(descriptor)
            raise FieldNoteError(
                "Field Note repository cannot be anchored safely."
            ) from exc
        identity = cls._identity(opened)
        if (
            stat.S_ISLNK(linked.st_mode)
            or not stat.S_ISDIR(linked.st_mode)
            or not stat.S_ISDIR(opened.st_mode)
            or cls._identity(linked) != identity
            or (
                expected_identity is not None
                and identity != expected_identity
            )
        ):
            os.close(descriptor)
            raise FieldNoteError(
                "Field Note repository identity changed."
            )
        return descriptor, identity

    @classmethod
    def _verify_directory_link(
        cls,
        parent_descriptor: int,
        name: str,
        descriptor: int,
    ) -> tuple[int, int]:
        try:
            opened = os.fstat(descriptor)
            linked = os.stat(
                name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise FieldNoteError(
                "Field Note parent directory identity changed."
            ) from exc
        identity = cls._identity(opened)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or not stat.S_ISDIR(linked.st_mode)
            or cls._identity(linked) != identity
        ):
            raise FieldNoteError(
                "Field Note parent directory identity changed."
            )
        return identity

    @classmethod
    def _open_existing_directory(
        cls,
        parent_descriptor: int,
        name: str,
    ) -> tuple[int, tuple[int, int]] | None:
        flags = (
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            descriptor = os.open(name, flags, dir_fd=parent_descriptor)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise FieldNoteError(
                "Field Note parent path is not a safe directory."
            ) from exc
        try:
            identity = cls._verify_directory_link(
                parent_descriptor,
                name,
                descriptor,
            )
        except Exception:
            os.close(descriptor)
            raise
        return descriptor, identity

    @classmethod
    def _open_or_create_directory(
        cls,
        parent_descriptor: int,
        name: str,
        expected_identity: tuple[int, int] | None,
    ) -> tuple[int, tuple[int, int]]:
        opened = cls._open_existing_directory(parent_descriptor, name)
        created = False
        if opened is None:
            try:
                os.mkdir(name, 0o700, dir_fd=parent_descriptor)
                created = True
            except FileExistsError:
                created = False
            except OSError as exc:
                raise FieldNoteError(
                    "Field Note directory could not be created safely."
                ) from exc
            opened = cls._open_existing_directory(parent_descriptor, name)
            if opened is None:
                raise FieldNoteError(
                    "Field Note directory could not be anchored safely."
                )
        descriptor, identity = opened
        if (
            (expected_identity is None and not created)
            or (expected_identity is not None and created)
            or (
                expected_identity is not None
                and identity != expected_identity
            )
        ):
            os.close(descriptor)
            raise FieldNoteError(
                "Field Note parent directory changed after Approval."
            )
        return descriptor, identity

    @classmethod
    def _verify_file_link(
        cls,
        directory_descriptor: int,
        filename: str,
        descriptor: int,
        expected_identity: tuple[int, int],
    ) -> None:
        try:
            opened = os.fstat(descriptor)
            linked = os.stat(
                filename,
                dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise FieldNoteError(
                "Field Note file identity changed."
            ) from exc
        if (
            not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(linked.st_mode)
            or cls._identity(opened) != expected_identity
            or cls._identity(linked) != expected_identity
        ):
            raise FieldNoteError(
                "Field Note file identity changed."
            )

    @staticmethod
    def _field_note_filename(draft: FieldNoteDraft) -> str:
        parts = draft.relative_path.split("/")
        if (
            len(parts) != 3
            or parts[:2] != [".decision-os", "field-notes"]
            or not parts[2]
            or parts[2] in {".", ".."}
            or Path(parts[2]).name != parts[2]
        ):
            raise FieldNoteError("Field Note path is outside its fixed root.")
        return parts[2]

    def _capture_parent_identities(
        self,
    ) -> tuple[
        tuple[int, int],
        tuple[int, int] | None,
        tuple[int, int] | None,
    ]:
        self._descriptor_containment_supported()
        repository_descriptor: int | None = None
        decision_descriptor: int | None = None
        field_notes_descriptor: int | None = None
        try:
            repository_descriptor, repository_identity = (
                self._open_repository_descriptor(self._require_repository())
            )
            decision = self._open_existing_directory(
                repository_descriptor,
                ".decision-os",
            )
            if decision is None:
                return repository_identity, None, None
            decision_descriptor, decision_identity = decision
            field_notes = self._open_existing_directory(
                decision_descriptor,
                "field-notes",
            )
            if field_notes is None:
                return repository_identity, decision_identity, None
            field_notes_descriptor, field_notes_identity = field_notes
            self._verify_directory_link(
                repository_descriptor,
                ".decision-os",
                decision_descriptor,
            )
            return (
                repository_identity,
                decision_identity,
                field_notes_identity,
            )
        finally:
            for descriptor in (
                field_notes_descriptor,
                decision_descriptor,
                repository_descriptor,
            ):
                if descriptor is not None:
                    os.close(descriptor)

    @staticmethod
    def _descriptor_case_collision(
        directory_descriptor: int,
        filename: str,
    ) -> bool:
        try:
            return any(
                name.casefold() == filename.casefold()
                for name in os.listdir(directory_descriptor)
            )
        except OSError as exc:
            raise FieldNoteError(
                "Field Note directory cannot be inspected safely."
            ) from exc

    @classmethod
    def _verify_casefold_file_link(
        cls,
        directory_descriptor: int,
        filename: str,
        descriptor: int,
        expected_identity: tuple[int, int],
    ) -> None:
        try:
            matches = [
                name
                for name in os.listdir(directory_descriptor)
                if name.casefold() == filename.casefold()
            ]
        except OSError as exc:
            raise FieldNoteError(
                "Field Note directory cannot be inspected safely."
            ) from exc
        if matches != [filename]:
            raise FieldNoteError(
                "Field Note case-normalized identity changed."
            )
        cls._verify_file_link(
            directory_descriptor,
            filename,
            descriptor,
            expected_identity,
        )

    @classmethod
    def _unlink_exact_created_file(
        cls,
        directory_descriptor: int,
        filename: str,
        expected_identity: tuple[int, int],
    ) -> None:
        try:
            linked = os.stat(
                filename,
                dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
            if (
                stat.S_ISREG(linked.st_mode)
                and cls._identity(linked) == expected_identity
            ):
                os.unlink(filename, dir_fd=directory_descriptor)
                os.fsync(directory_descriptor)
        except OSError:
            pass

    def _write_pending(self, pending: _PendingSave) -> None:
        self._descriptor_containment_supported()
        filename = self._field_note_filename(pending.draft)
        repository_descriptor: int | None = None
        decision_descriptor: int | None = None
        field_notes_descriptor: int | None = None
        file_descriptor: int | None = None
        created_identity: tuple[int, int] | None = None
        try:
            repository_descriptor, _ = self._open_repository_descriptor(
                self._require_repository(),
                pending.repository_identity,
            )
            decision_descriptor, _ = self._open_or_create_directory(
                repository_descriptor,
                ".decision-os",
                pending.decision_directory_identity,
            )
            field_notes_descriptor, _ = self._open_or_create_directory(
                decision_descriptor,
                "field-notes",
                pending.field_notes_directory_identity,
            )
            self._verify_directory_link(
                repository_descriptor,
                ".decision-os",
                decision_descriptor,
            )
            self._verify_directory_link(
                decision_descriptor,
                "field-notes",
                field_notes_descriptor,
            )
            if self._descriptor_case_collision(
                field_notes_descriptor,
                filename,
            ):
                raise FieldNoteError(
                    "Field Note create-new precondition failed."
                )
            try:
                file_descriptor = os.open(
                    filename,
                    os.O_RDWR
                    | os.O_CREAT
                    | os.O_EXCL
                    | os.O_NOFOLLOW
                    | getattr(os, "O_CLOEXEC", 0),
                    0o600,
                    dir_fd=field_notes_descriptor,
                )
            except OSError as exc:
                raise FieldNoteError(
                    "Field Note create-new precondition failed."
                ) from exc
            created = os.fstat(file_descriptor)
            if not stat.S_ISREG(created.st_mode):
                raise FieldNoteError(
                    "Field Note target is not a safe regular file."
                )
            created_identity = self._identity(created)
            self._verify_casefold_file_link(
                field_notes_descriptor,
                filename,
                file_descriptor,
                created_identity,
            )
            remaining = memoryview(pending.draft.markdown)
            while remaining:
                written = os.write(file_descriptor, remaining)
                if written <= 0:
                    raise FieldNoteError(
                        "Field Note write did not make progress."
                    )
                remaining = remaining[written:]
            os.fsync(file_descriptor)
            self._verify_directory_link(
                repository_descriptor,
                ".decision-os",
                decision_descriptor,
            )
            self._verify_directory_link(
                decision_descriptor,
                "field-notes",
                field_notes_descriptor,
            )
            self._verify_casefold_file_link(
                field_notes_descriptor,
                filename,
                file_descriptor,
                created_identity,
            )
            os.lseek(file_descriptor, 0, os.SEEK_SET)
            chunks: list[bytes] = []
            while True:
                chunk = os.read(file_descriptor, 64 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            observed = b"".join(chunks)
            self._verify_directory_link(
                repository_descriptor,
                ".decision-os",
                decision_descriptor,
            )
            self._verify_directory_link(
                decision_descriptor,
                "field-notes",
                field_notes_descriptor,
            )
            if observed != pending.draft.markdown:
                raise FieldNoteError(
                    "Field Note readback identity did not match."
                )
            self._verify_casefold_file_link(
                field_notes_descriptor,
                filename,
                file_descriptor,
                created_identity,
            )
            if hashlib.sha256(observed).hexdigest() != pending.draft.sha256:
                raise FieldNoteError(
                    "Field Note readback identity did not match."
                )
            self._verify_casefold_file_link(
                field_notes_descriptor,
                filename,
                file_descriptor,
                created_identity,
            )
            os.fsync(field_notes_descriptor)
            self._verify_directory_link(
                repository_descriptor,
                ".decision-os",
                decision_descriptor,
            )
            self._verify_directory_link(
                decision_descriptor,
                "field-notes",
                field_notes_descriptor,
            )
            self._verify_casefold_file_link(
                field_notes_descriptor,
                filename,
                file_descriptor,
                created_identity,
            )
        except Exception as exc:
            if (
                field_notes_descriptor is not None
                and created_identity is not None
            ):
                self._unlink_exact_created_file(
                    field_notes_descriptor,
                    filename,
                    created_identity,
                )
            if isinstance(exc, FieldNoteError):
                raise
            raise FieldNoteError(
                "Field Note write or readback failed safely."
            ) from exc
        finally:
            for descriptor in (
                file_descriptor,
                field_notes_descriptor,
                decision_descriptor,
                repository_descriptor,
            ):
                if descriptor is not None:
                    os.close(descriptor)

    def field_note_approval(
        self,
        choice: str,
        *,
        _cycle_006_authority: object | None = None,
    ) -> dict[str, Any]:
        with self._condition:
            self._require_cycle_006_field_note_authority_locked(
                _cycle_006_authority
            )
            pending = self._field_note_pending
            if (
                pending is None
                or self._run.get("field_note", {}).get("state") != "approval"
            ):
                raise FieldNoteError("No Field Note Approval is pending.")
            if choice == "deny":
                self._field_note_pending = None
                self._run["field_note"] = {
                    **pending.draft.public_candidate(),
                    "error": "Save was not approved.",
                }
                return self._snapshot_locked()
            if choice != "allow_once":
                raise FieldNoteError(
                    "Field Note save allows exact one-time Approval only."
                )
            self._field_note_pending = None
            try:
                self._write_pending(pending)
            except FieldNoteError:
                self._field_note_draft = pending.draft
                self._run["field_note"] = {
                    **pending.draft.public_candidate(),
                    "error": (
                        "Save failed; prepare a new exact Approval before "
                        "retrying."
                    ),
                }
                raise
            path = pending.draft.relative_path
            self._field_note_draft = None
            self._run["field_note"] = {"state": "saved", "path": path}
            return self._snapshot_locked()

    def creator_live_cycle_005_start(
        self,
        launch_binding_sha256: str,
    ) -> dict[str, Any]:
        """Start only the dedicated Cycle 005 production entrypoint."""

        self._creator_live_cycle_005.start(launch_binding_sha256)
        return self.snapshot()

    def creator_live_cycle_006_start(
        self,
        launch_binding_sha256: str,
    ) -> dict[str, Any]:
        """Enter only the dedicated, currently non-live Cycle 006 boundary."""

        from decision_os.companion.field_notes_creator_live_cycle_006 import (
            CreatorLiveCycle006Error,
        )

        with self._condition:
            ordinary_active = bool(
                self._ordinary_user_path is not None
                and self._ordinary_user_path.mutation_active
            )
            if (
                self._run.get("state") in {"running", "active"}
                or self._repository_selection_active
                or self._active_bridge_operations
                or self._active_guided_intake_operations
                or self._active_intelligence_transplant_operations
                or ordinary_active
            ):
                raise CreatorLiveCycle006Error(
                    "CYCLE_006_CONTROLLER_BUSY"
                )
            self._creator_live_cycle_006.start(launch_binding_sha256)
            return self._snapshot_locked()

    def creator_live_cycle_005_mutation_blocked(self) -> bool:
        entrypoint = getattr(self, "_creator_live_cycle_005", None)
        return bool(entrypoint is not None and entrypoint.mutation_blocked)

    def creator_live_cycle_006_mutation_blocked(self) -> bool:
        entrypoint = getattr(self, "_creator_live_cycle_006", None)
        return bool(
            entrypoint is not None
            and getattr(entrypoint, "mutation_blocked", False)
        )

    @staticmethod
    def creator_live_cycle_005_public_projection(
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """Redact private coordinator Runs from every HTTP projection."""

        cycle = snapshot.get("creator_live_cycle_005")
        if not isinstance(cycle, dict) or cycle.get("state") in {
            "READY",
            "NOT_READY",
            "UNAVAILABLE",
        }:
            return snapshot
        state = cycle.get("state")
        if state in {
            "FAILED",
            "TRACE_COMPLETE",
            "PASS",
            "OPEN_UNRESUMABLE",
            "INTEGRITY_FAILURE",
        }:
            run = snapshot.get("run")
            if isinstance(run, dict) and run.get("run_type") == "bounded_task":
                return snapshot
            snapshot["run"] = CompanionController._empty_run()
            return snapshot
        public_state = (
            "running"
            if state == "RUNNING"
            else "completed"
            if state in {"PASS", "TRACE_COMPLETE"}
            else "needs_attention"
        )
        snapshot["run"] = {
            "run_type": "creator_live_cycle_005",
            "task_mode": None,
            "state": public_state,
            "progress": [cycle.get("stage") or "P0"],
            "result": "",
            "file_actions": [],
            "read_evidence": [],
            "outcomes": None,
            "runtime": None,
            "receipt_delta": None,
            "approval": None,
            "error": cycle.get("failure_code"),
            "failure": None,
        }
        return snapshot

    def _snapshot_locked(self) -> dict[str, Any]:
        snapshot = super()._snapshot_locked()
        entrypoint = getattr(self, "_creator_live_cycle_005", None)
        snapshot["creator_live_cycle_005"] = (
            entrypoint.snapshot(snapshot)
            if entrypoint is not None
            else {
                "cycle_key": "cycle-005",
                "state": "UNAVAILABLE",
                "p0": {"ready": False, "failure_code": "ENTRYPOINT_UNAVAILABLE"},
                "launch_binding_sha256": None,
            }
        )
        cycle_006 = getattr(self, "_creator_live_cycle_006", None)
        snapshot["creator_live_cycle_006"] = (
            cycle_006.snapshot(snapshot)
            if cycle_006 is not None
            else {
                "cycle_key": "cycle-006",
                "cycle_number": "006",
                "state": "UNAVAILABLE",
                "stage": "P0",
                "p0": {
                    "ready": False,
                    "failure_code": "ENTRYPOINT_UNAVAILABLE",
                },
                "launch_binding_sha256": None,
                "live_start_authorization": "ABSENT",
                "start_allowed": False,
                "proof_identity": None,
                "model_invocation_count": 0,
                "task_transmission_count": 0,
                "artifact_behavior": "NOT_RUN",
                "comparison_result": "NOT_ESTABLISHED",
            }
        )
        return snapshot
