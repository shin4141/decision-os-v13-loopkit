"""Thread-safe presentation controller over the existing Verified Save backend."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import threading
from typing import Any, Protocol

from decision_os.acceleration.codex_adapter import (
    ADAPTER_NAME,
    CODEX_CLI_VERSION,
    CodexAdapter,
    CodexAdapterFailure,
    CodexAdapterUnavailable,
    CodexApproval,
    CodexFailureDiagnostic,
    CodexLifecycleEvent,
    CodexRunResult,
    canonical_failure_diagnostic,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import (
    RepositoryIdentityError,
    git_root,
    normalize_scope,
)
from decision_os.acceleration.store import (
    AccelerationStore,
    ActiveDefaultRecord,
    StateIntegrityError,
)
from decision_os.intelligence_transplant import (
    IntelligenceTransplantError as CoreIntelligenceTransplantError,
    strict_json_object,
)
from decision_os.companion.guided_intake import (
    AUTHORITY_CLAIM,
    AUTHORITY_EXPLANATION,
    GuidedIntakeBusyError,
    GuidedIntakeController,
    GuidedIntakeIntegrityError,
)
from decision_os.companion.continuation import (
    ContinuationIntegrityError,
    StageBContinuationRequest,
    StageBContinuationStore,
    automatic_task_from_persisted_run,
    governed_stop,
    new_record,
    result_evidence,
    supervisor_context_from_persisted_run,
)
from decision_os.companion.intelligence_transplant import (
    IntelligenceTransplantBusyError,
    IntelligenceTransplantController,
    IntelligenceTransplantIntegrityError,
    IntelligenceTransplantValidationError,
)
from decision_os.companion.manual_bridge import (
    BridgeSessionController,
    ManualBridgeBusyError,
    ManualBridgeIntegrityError,
    build_intelligence_transplant_transport,
)
from decision_os.companion.ordinary_user_path import (
    EXECUTION_AUTHORITY_UNKNOWN,
    OrdinaryUserPathCoordinator,
    OrdinaryUserPathError,
    UNKNOWN_EXECUTION_AUTHORITY_REASON,
)
from decision_os.companion.supervisor import (
    SupervisorContext,
    judge_continuation,
)


class CompanionError(RuntimeError):
    """Base error for the private companion presentation surface."""


class CompanionStateError(CompanionError):
    """The companion's minimal local state is invalid."""


class RepositorySelectionError(CompanionError):
    """A selected path is not a usable local Git repository."""


class RunConflictError(CompanionError):
    """A state-changing action conflicts with the one active Run."""


class ApprovalStateError(CompanionError):
    """An approval response has no matching pending approval."""


class LifecycleEventError(CompanionError):
    """An adapter attempted to emit a malformed presentation event."""


class SupervisorStateError(CompanionError):
    """A Supervisor judgment has no exact completed Worker result."""


class ContinuationStateError(CompanionError):
    """A Stage B continuation request cannot be started safely."""


class AdapterFactory(Protocol):
    def __call__(
        self,
        engine: AccelerationEngine,
        approval_provider: Callable[[CodexApproval], str | None],
        lifecycle_sink: Callable[[CodexLifecycleEvent], None],
    ) -> CodexAdapter:
        """Create one adapter for one fresh Wrapper Run."""


PickerRunner = Callable[[Path], str | None]

_TERMINAL_STATES = frozenset(
    {"completed", "denied", "unsupported", "needs_attention"}
)
_INTELLIGENCE_TRANSPLANT_EVIDENCE_TYPES = frozenset(
    {
        "E1_DISCOVERY",
        "E2_AUDIT",
        "E3_ACCEPTED_DISCOVERY",
        "E4_IMPLEMENTATION_BINDING",
        "E5_REUSE",
    }
)
_INTELLIGENCE_TRANSPLANT_RECEIPT_TYPES = frozenset(
    {
        "AUDIT_COMPLETION_RECEIPT",
        "LOWER_RUN_COMPLETION_RECEIPT",
        "SEAT_ASSIGNMENT_RECEIPT",
    }
)
_LIFECYCLE_MESSAGES = {
    "starting": "Preparing the bounded task.",
    "runtime": "Starting the private Codex runtime.",
    "account": "Verifying ChatGPT authentication.",
    "model": "Verifying the required model and service tier.",
    "run": "Starting one fresh bounded Run.",
    "working": "Codex is working on the bounded task.",
    "approval": "Waiting for one exact file-change decision.",
    "reuse": "Matching saved repository access was reused.",
    "finalizing": "Finalizing the local Receipt.",
}


def _default_state_path() -> Path:
    return (
        Path.home()
        / "Library"
        / "Application Support"
        / "Decision OS Companion"
        / "state.json"
    )


def _default_picker_runner(script: Path) -> str | None:
    if not script.is_file():
        raise RepositorySelectionError(
            "The fixed macOS repository picker is unavailable."
        )
    try:
        completed = subprocess.run(
            ("/usr/bin/osascript", str(script), "pick"),
            capture_output=True,
            check=False,
            text=True,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RepositorySelectionError(
            "The macOS repository picker could not be opened."
        ) from exc
    if completed.returncode != 0:
        raise RepositorySelectionError(
            "The macOS repository picker did not complete."
        )
    selected = completed.stdout.strip()
    return selected or None


def _default_adapter_factory(
    engine: AccelerationEngine,
    approval_provider: Callable[[CodexApproval], str | None],
    lifecycle_sink: Callable[[CodexLifecycleEvent], None],
) -> CodexAdapter:
    return CodexAdapter(
        engine,
        input_func=lambda: None,
        stdout=io.StringIO(),
        approval_provider=approval_provider,
        lifecycle_sink=lifecycle_sink,
    )


class CompanionController:
    """Own repository selection, one active Run, approvals, and safe receipts."""

    def __init__(
        self,
        *,
        state_path: Path | None = None,
        picker_script: Path | None = None,
        picker_runner: PickerRunner | None = None,
        adapter_factory: AdapterFactory | None = None,
    ) -> None:
        self.state_path = state_path or _default_state_path()
        self.picker_script = picker_script or Path(
            "/Applications/Decision OS Companion.app/Contents/Resources/"
            "DecisionOSCompanion.applescript"
        )
        self.picker_runner = picker_runner or _default_picker_runner
        self.adapter_factory = adapter_factory or _default_adapter_factory
        self._condition = threading.Condition(threading.RLock())
        self._repository: Path | None = None
        self._run: dict[str, Any] = self._empty_run()
        self._last_run_result: CodexRunResult | None = None
        self._last_supervisor_context: SupervisorContext | None = None
        self._continuation_store = StageBContinuationStore(
            self.state_path.with_name("stage-b-continuation.json")
        )
        self._compound_loop: dict[str, Any] | None = None
        self._compound_active = False
        self._compound_recovery_required = False
        self._compound_allowed_mutation_paths: tuple[str, ...] = ()
        self._approval_choice: str | None = None
        self._default_handles: dict[str, str] = {}
        self._worker: threading.Thread | None = None
        self._bridge: BridgeSessionController | None = None
        self._guided_intake: GuidedIntakeController | None = None
        self._ordinary_user_path: OrdinaryUserPathCoordinator | None = None
        self._intelligence_transplant: (
            IntelligenceTransplantController | None
        ) = None
        self._active_bridge_operations = 0
        self._active_guided_intake_operations = 0
        self._active_intelligence_transplant_operations = 0
        self._repository_selection_active = False
        self._load_last_repository()
        self._load_compound_loop()
        if self._repository is not None:
            self._bridge = BridgeSessionController(self._repository)
            self._guided_intake = GuidedIntakeController(self._repository)
            self._ordinary_user_path = OrdinaryUserPathCoordinator(
                self._repository,
                self._guided_intake,
            )
            try:
                self._ordinary_user_path.recover_incomplete()
            except OrdinaryUserPathError:
                pass
            self._intelligence_transplant = IntelligenceTransplantController(
                self._repository
            )

    @staticmethod
    def _empty_run() -> dict[str, Any]:
        return {
            "run_type": "bounded_task",
            "task_mode": None,
            "state": "idle",
            "progress": [],
            "result": "",
            "file_actions": [],
            "read_evidence": [],
            "outcomes": {
                "execution": {
                    "state": "not_started",
                    "label": "Not started",
                },
                "file_change": {
                    "state": "none",
                    "label": "No file was modified",
                },
                "verification": {
                    "state": "not_started",
                    "label": "Not started",
                    "reason": None,
                },
            },
            "runtime": None,
            "receipt_delta": None,
            "supervisor": None,
            "continuation": None,
            "approval": None,
            "error": None,
            "failure": None,
        }

    def _load_last_repository(self) -> None:
        if not self.state_path.exists():
            return
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CompanionStateError(
                "Decision OS Companion state is invalid."
            ) from exc
        if (
            not isinstance(value, dict)
            or set(value) != {"repository"}
            or not isinstance(value["repository"], str)
            or not value["repository"]
        ):
            raise CompanionStateError(
                "Decision OS Companion state exceeds its allowed field boundary."
            )
        try:
            self._repository = self._validated_repository(
                Path(value["repository"])
            )
        except RepositorySelectionError:
            self._repository = None

    def _write_last_repository(self, repository: Path) -> None:
        directory = self.state_path.parent
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(directory, 0o700)
        temporary = directory / f".state-{secrets.token_hex(8)}.tmp"
        payload = json.dumps(
            {"repository": str(repository)},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.write("\n")
            os.replace(temporary, self.state_path)
            os.chmod(self.state_path, 0o600)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def _load_compound_loop(self) -> None:
        try:
            value = self._continuation_store.load()
            if value is not None and self._repository is not None:
                expected = AccelerationStore(self._repository).repository_id
                if value["repository_id"] != expected:
                    if value.get("state") in {
                        "RUN_1_ACTIVE",
                        "RUN_1_COMPLETE",
                        "RUN_2_ACTIVE",
                    }:
                        raise ContinuationIntegrityError(
                            "Persisted Stage B repository identity mismatches."
                        )
                    value = None
            self._compound_loop = value
            self._compound_recovery_required = bool(
                value is not None
                and value.get("state")
                in {"RUN_1_ACTIVE", "RUN_1_COMPLETE", "RUN_2_ACTIVE"}
            )
        except (ContinuationIntegrityError, OSError):
            self._compound_recovery_required = True
            self._compound_loop = {
                "schema": "decision-os-stage-b-continuation-view-v0.1",
                "state": "BLOCKED_CORRUPT",
                "gate": "BLOCK",
                "decision_route": "EVIDENCE-RECOVERY",
                "automatic_continuations_started": 0,
                "automatic_continuation_limit": 1,
                "error": (
                    "Stage B continuation state is not reconnectable from "
                    "verified persisted evidence."
                ),
                "next_bounded_action": (
                    "Recover the exact persisted Stage B record under current "
                    "repository authority."
                ),
            }

    @staticmethod
    def _validated_repository(candidate: Path) -> Path:
        try:
            root = git_root(candidate)
            store = AccelerationStore(root)
            store.read_events()
            store.read_settings()
        except (
            OSError,
            RepositoryIdentityError,
            StateIntegrityError,
        ) as exc:
            raise RepositorySelectionError(
                "Select a valid local Git repository with intact Decision OS state."
            ) from exc
        return root

    def select_repository(self, candidate: str | Path) -> dict[str, Any]:
        with self._condition:
            self._require_no_active_run()
            if self._active_bridge_operations:
                raise RepositorySelectionError(
                    "A Manual Bridge action is already active."
                )
            if self._active_guided_intake_operations:
                raise RepositorySelectionError(
                    "A Guided Intake action is already active."
                )
            if self._active_intelligence_transplant_operations:
                raise RepositorySelectionError(
                    "An Intelligence Transplant action is already active."
                )
            if self._repository_selection_active:
                raise RepositorySelectionError(
                    "Repository selection is already active."
                )
            self._repository_selection_active = True
        try:
            if not isinstance(candidate, (str, Path)):
                raise RepositorySelectionError("Repository path is invalid.")
            repository = self._validated_repository(Path(candidate))
            with self._condition:
                self._require_no_active_run()
                if self._active_bridge_operations:
                    raise RepositorySelectionError(
                        "A Manual Bridge action is already active."
                    )
                if self._active_guided_intake_operations:
                    raise RepositorySelectionError(
                        "A Guided Intake action is already active."
                    )
                if self._active_intelligence_transplant_operations:
                    raise RepositorySelectionError(
                        "An Intelligence Transplant action is already active."
                    )
                self._write_last_repository(repository)
                self._repository = repository
                self._load_compound_loop()
                self._bridge = BridgeSessionController(repository)
                self._guided_intake = GuidedIntakeController(repository)
                self._ordinary_user_path = OrdinaryUserPathCoordinator(
                    repository,
                    self._guided_intake,
                )
                try:
                    self._ordinary_user_path.recover_incomplete()
                except OrdinaryUserPathError:
                    pass
                self._intelligence_transplant = (
                    IntelligenceTransplantController(repository)
                )
                self._default_handles = {}
                self._run = self._empty_run()
                self._last_run_result = None
                self._last_supervisor_context = None
                self._compound_active = False
                self._compound_allowed_mutation_paths = ()
                return self._snapshot_locked()
        finally:
            with self._condition:
                self._repository_selection_active = False
                self._condition.notify_all()

    def pick_repository(self) -> dict[str, Any]:
        selected = self.picker_runner(self.picker_script)
        if selected is None:
            raise RepositorySelectionError("Repository selection was cancelled.")
        return self.select_repository(selected)

    def _require_repository(self) -> Path:
        if self._repository is None:
            raise RepositorySelectionError("Choose a local Git repository first.")
        return self._repository

    def _require_no_active_run(self) -> None:
        if (
            self._run["state"] == "running"
            or self._compound_active
            or self._compound_recovery_required
        ):
            raise RunConflictError("One bounded Run is already active.")

    def _require_bridge(self) -> BridgeSessionController:
        self._require_repository()
        if self._bridge is None:
            raise RepositorySelectionError("Choose a local Git repository first.")
        return self._bridge

    def _require_guided_intake(self) -> GuidedIntakeController:
        self._require_repository()
        if self._guided_intake is None:
            raise RepositorySelectionError("Choose a local Git repository first.")
        return self._guided_intake

    def _require_ordinary_user_path(self) -> OrdinaryUserPathCoordinator:
        self._require_repository()
        if self._ordinary_user_path is None:
            raise RepositorySelectionError("Choose a local Git repository first.")
        return self._ordinary_user_path

    def _require_intelligence_transplant(
        self,
    ) -> IntelligenceTransplantController:
        self._require_repository()
        if self._intelligence_transplant is None:
            raise RepositorySelectionError("Choose a local Git repository first.")
        return self._intelligence_transplant

    @contextmanager
    def _bridge_operation(self) -> Any:
        with self._condition:
            if self._repository_selection_active:
                raise RepositorySelectionError(
                    "Repository selection is already active."
                )
            bridge = self._require_bridge()
            self._active_bridge_operations += 1
        try:
            yield bridge
        finally:
            with self._condition:
                self._active_bridge_operations -= 1
                self._condition.notify_all()

    def _snapshot_after_bridge(
        self,
        bridge: BridgeSessionController,
    ) -> dict[str, Any]:
        with self._condition:
            if bridge is not self._bridge:
                raise RepositorySelectionError(
                    "The selected repository changed during the Bridge action."
                )
            return self._snapshot_locked()

    @contextmanager
    def _guided_intake_operation(self) -> Any:
        with self._condition:
            if self._repository_selection_active:
                raise RepositorySelectionError(
                    "Repository selection is already active."
                )
            if self._active_intelligence_transplant_operations:
                raise GuidedIntakeBusyError(
                    "An Intelligence Transplant action is already active."
                )
            guided_intake = self._require_guided_intake()
            ordinary = self._require_ordinary_user_path()
            if ordinary.mutation_active:
                raise GuidedIntakeBusyError(
                    "An ordinary Contract action is still active."
                )
            self._active_guided_intake_operations += 1
        try:
            yield guided_intake
        finally:
            with self._condition:
                self._active_guided_intake_operations -= 1
                self._condition.notify_all()

    @contextmanager
    def _ordinary_user_path_operation(self) -> Any:
        with self._condition:
            if self._repository_selection_active:
                raise RepositorySelectionError(
                    "Repository selection is already active."
                )
            if self._active_guided_intake_operations:
                raise GuidedIntakeBusyError(
                    "A Guided Intake action is already active."
                )
            ordinary = self._require_ordinary_user_path()
            self._active_guided_intake_operations += 1
        try:
            yield ordinary
        finally:
            with self._condition:
                self._active_guided_intake_operations -= 1
                self._condition.notify_all()

    @contextmanager
    def _guided_intake_bridge_operation(self) -> Any:
        with self._condition:
            if self._repository_selection_active:
                raise RepositorySelectionError(
                    "Repository selection is already active."
                )
            if self._active_intelligence_transplant_operations:
                raise GuidedIntakeBusyError(
                    "An Intelligence Transplant action is already active."
                )
            guided_intake = self._require_guided_intake()
            bridge = self._require_bridge()
            self._active_guided_intake_operations += 1
            self._active_bridge_operations += 1
        try:
            yield guided_intake, bridge
        finally:
            with self._condition:
                self._active_bridge_operations -= 1
                self._active_guided_intake_operations -= 1
                self._condition.notify_all()

    def _snapshot_after_guided_intake(
        self,
        guided_intake: GuidedIntakeController,
        bridge: BridgeSessionController | None = None,
    ) -> dict[str, Any]:
        with self._condition:
            if guided_intake is not self._guided_intake:
                raise RepositorySelectionError(
                    "The selected repository changed during the Guided Intake action."
                )
            if bridge is not None and bridge is not self._bridge:
                raise RepositorySelectionError(
                    "The selected repository changed during the Guided Intake transfer."
                )
            return self._snapshot_locked()

    @contextmanager
    def _intelligence_transplant_operation(self) -> Any:
        with self._condition:
            if self._repository_selection_active:
                raise RepositorySelectionError(
                    "Repository selection is already active."
                )
            self._require_no_active_run()
            if self._active_guided_intake_operations:
                raise IntelligenceTransplantBusyError(
                    "A Guided Intake action is already active."
                )
            intelligence_transplant = (
                self._require_intelligence_transplant()
            )
            self._active_intelligence_transplant_operations += 1
        try:
            yield intelligence_transplant
        finally:
            with self._condition:
                self._active_intelligence_transplant_operations -= 1
                self._condition.notify_all()

    @contextmanager
    def _guided_intake_transplant_operation(self) -> Any:
        with self._condition:
            if self._repository_selection_active:
                raise RepositorySelectionError(
                    "Repository selection is already active."
                )
            self._require_no_active_run()
            if self._active_guided_intake_operations:
                raise GuidedIntakeBusyError(
                    "A Guided Intake action is already active."
                )
            if self._active_intelligence_transplant_operations:
                raise IntelligenceTransplantBusyError(
                    "An Intelligence Transplant action is already active."
                )
            guided_intake = self._require_guided_intake()
            intelligence_transplant = (
                self._require_intelligence_transplant()
            )
            self._active_guided_intake_operations += 1
            self._active_intelligence_transplant_operations += 1
        try:
            with guided_intake.store.transaction(
                write=False,
                timeout_seconds=0.05,
            ):
                yield guided_intake, intelligence_transplant
        finally:
            with self._condition:
                self._active_intelligence_transplant_operations -= 1
                self._active_guided_intake_operations -= 1
                self._condition.notify_all()

    @staticmethod
    def _intelligence_transplant_run(
        projection: Mapping[str, Any],
    ) -> dict[str, Any]:
        run = deepcopy(dict(projection))
        run.update(
            {
                "run_type": "intelligence_transplant",
                "state": "active",
                "progress": [],
                "result": "",
                "file_actions": [],
                "read_evidence": [],
                "runtime": None,
                "receipt_delta": None,
                "approval": None,
                "error": projection.get("error"),
            }
        )
        return run

    def _snapshot_after_intelligence_transplant(
        self,
        intelligence_transplant: IntelligenceTransplantController,
        projection: Mapping[str, Any],
        guided_intake: GuidedIntakeController | None = None,
    ) -> dict[str, Any]:
        with self._condition:
            if intelligence_transplant is not self._intelligence_transplant:
                raise RepositorySelectionError(
                    "The selected repository changed during the "
                    "Intelligence Transplant action."
                )
            if (
                guided_intake is not None
                and guided_intake is not self._guided_intake
            ):
                raise RepositorySelectionError(
                    "The selected repository changed during the "
                    "Intelligence Transplant Charter action."
                )
            self._run = self._intelligence_transplant_run(projection)
            return self._snapshot_locked()

    @staticmethod
    def _transport_json_object(payload: bytes) -> dict[str, Any]:
        try:
            return strict_json_object(payload)
        except CoreIntelligenceTransplantError as exc:
            raise IntelligenceTransplantValidationError(
                "Intelligence Transplant payload must be one strict JSON object."
            ) from exc

    @staticmethod
    def _intelligence_transplant_transport(
        *,
        payload: bytes,
        mode: str,
        source_path_or_label: str,
        declared_sha256: str,
        context_evidence_ref: Mapping[str, Any] | None,
        as_of: str,
    ) -> dict[str, Any]:
        return build_intelligence_transplant_transport(
            payload=payload,
            source_path_or_label=source_path_or_label,
            mode=mode,
            declared_sha256=declared_sha256,
            context_evidence_ref=context_evidence_ref,
            as_of=as_of,
        )

    def start_bridge_session(
        self,
        boundary: dict[str, Any],
    ) -> dict[str, Any]:
        with self._bridge_operation() as bridge:
            bridge.create_session(boundary)
            return self._snapshot_after_bridge(bridge)

    def bridge_copy_for_pro(self) -> dict[str, Any]:
        with self._bridge_operation() as bridge:
            bridge.copy_for_pro()
            return self._snapshot_after_bridge(bridge)

    def bridge_import_artifact(
        self,
        *,
        selected_role: str,
        payload: bytes,
        source_path_or_label: str,
        import_mode: str,
        metadata: dict[str, Any] | None = None,
        declared_sha256: str | None = None,
        supersedes_import_event_id: str | None = None,
        correction_reason: str | None = None,
    ) -> dict[str, Any]:
        with self._bridge_operation() as bridge:
            bridge.import_artifact(
                selected_role=selected_role,
                payload=payload,
                source_path_or_label=source_path_or_label,
                import_mode=import_mode,
                metadata=metadata,
                declared_sha256=declared_sha256,
                supersedes_import_event_id=supersedes_import_event_id,
                correction_reason=correction_reason,
            )
            return self._snapshot_after_bridge(bridge)

    def bridge_generate_handoff(self) -> dict[str, Any]:
        with self._bridge_operation() as bridge:
            bridge.generate_execution_handoff()
            return self._snapshot_after_bridge(bridge)

    def bridge_freeze_output(self, role: str) -> dict[str, Any]:
        with self._bridge_operation() as bridge:
            bridge.freeze_output(role)
            return self._snapshot_after_bridge(bridge)

    def bridge_generate_receipt(self) -> dict[str, Any]:
        with self._bridge_operation() as bridge:
            bridge.generate_bridge_receipt()
            return self._snapshot_after_bridge(bridge)

    def bridge_generate_manifest(self) -> dict[str, Any]:
        with self._bridge_operation() as bridge:
            bridge.generate_golden_manifest()
            return self._snapshot_after_bridge(bridge)

    def bridge_replay(
        self,
        baseline: dict[str, Any],
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        with self._bridge_operation() as bridge:
            bridge.evaluate_replay(baseline, candidate)
            return self._snapshot_after_bridge(bridge)

    def bridge_record_observation(
        self,
        *,
        field: str,
        value: int | float | str,
        unit: str,
        method: str,
        notes: str = "",
    ) -> dict[str, Any]:
        with self._bridge_operation() as bridge:
            bridge.record_observation(
                field=field,
                value=value,
                unit=unit,
                method=method,
                notes=notes,
            )
            return self._snapshot_after_bridge(bridge)

    def guided_intake_capture(
        self,
        original_request: str,
        *,
        supersedes_request_id: str | None = None,
    ) -> dict[str, Any]:
        with self._guided_intake_operation() as guided_intake:
            guided_intake.capture(
                original_request,
                supersedes_request_id=supersedes_request_id,
            )
            return self._snapshot_after_guided_intake(guided_intake)

    def guided_intake_copy_for_pro(self) -> dict[str, Any]:
        with self._guided_intake_operation() as guided_intake:
            guided_intake.copy_for_pro()
            return self._snapshot_after_guided_intake(guided_intake)

    def guided_intake_import_draft(
        self,
        draft_json: str,
        producer_label: str,
    ) -> dict[str, Any]:
        with self._guided_intake_operation() as guided_intake:
            guided_intake.import_draft(draft_json, producer_label)
            return self._snapshot_after_guided_intake(guided_intake)

    def guided_intake_confirm(
        self,
        question: str,
        answer: str,
        resulting_delta: dict[str, Any],
    ) -> dict[str, Any]:
        with self._guided_intake_operation() as guided_intake:
            guided_intake.confirm(question, answer, resulting_delta)
            return self._snapshot_after_guided_intake(guided_intake)

    def guided_intake_freeze(self) -> dict[str, Any]:
        with self._guided_intake_operation() as guided_intake:
            guided_intake.freeze()
            return self._snapshot_after_guided_intake(guided_intake)

    def guided_intake_purge(
        self,
        request_id: str,
        request_sha256: str,
        confirmed: bool,
    ) -> dict[str, Any]:
        with self._guided_intake_operation() as guided_intake:
            guided_intake.purge(
                request_id,
                request_sha256,
                confirmed,
            )
            return self._snapshot_after_guided_intake(guided_intake)

    def guided_intake_transfer_to_bridge(self) -> dict[str, Any]:
        with self._guided_intake_bridge_operation() as (
            guided_intake,
            bridge,
        ):
            guided_intake.transfer_to_bridge(bridge)
            return self._snapshot_after_guided_intake(
                guided_intake,
                bridge,
            )

    def ordinary_contract_prepare(
        self,
        *,
        filename: str,
        source_bytes: bytes,
        source_byte_size: int,
        source_sha256: str,
        expected_repository_identity: str,
        expected_active_request_id: str | None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        with self._ordinary_user_path_operation() as ordinary:
            ordinary.prepare(
                filename=filename,
                source_bytes=source_bytes,
                source_byte_size=source_byte_size,
                source_sha256=source_sha256,
                expected_repository_identity=expected_repository_identity,
                expected_active_request_id=expected_active_request_id,
                idempotency_key=idempotency_key,
            )
            with self._condition:
                if ordinary is not self._ordinary_user_path:
                    raise RepositorySelectionError(
                        "The selected repository changed during Contract preparation."
                    )
                return self._snapshot_locked()

    def ordinary_contract_confirm(
        self,
        *,
        preparation_id: str,
        clarification_id: str,
        answer: str,
        expected_interpretation_sha256: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        with self._ordinary_user_path_operation() as ordinary:
            ordinary.confirm(
                preparation_id=preparation_id,
                clarification_id=clarification_id,
                answer=answer,
                expected_interpretation_sha256=expected_interpretation_sha256,
                idempotency_key=idempotency_key,
            )
            with self._condition:
                if ordinary is not self._ordinary_user_path:
                    raise RepositorySelectionError(
                        "The selected repository changed during Contract confirmation."
                    )
                return self._snapshot_locked()

    def ordinary_contract_fix(
        self,
        *,
        preparation_id: str,
        expected_repository_identity: str,
        expected_source_sha256: str,
        expected_request_id: str,
        expected_draft_id: str,
        expected_interpretation_sha256: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        with self._ordinary_user_path_operation() as ordinary:
            ordinary.fix(
                preparation_id=preparation_id,
                expected_repository_identity=expected_repository_identity,
                expected_source_sha256=expected_source_sha256,
                expected_request_id=expected_request_id,
                expected_draft_id=expected_draft_id,
                expected_interpretation_sha256=expected_interpretation_sha256,
                idempotency_key=idempotency_key,
            )
            with self._condition:
                if ordinary is not self._ordinary_user_path:
                    raise RepositorySelectionError(
                        "The selected repository changed during Contract fixation."
                    )
                return self._snapshot_locked()

    def ordinary_contract_dismiss_error(
        self,
        *,
        error_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        with self._ordinary_user_path_operation() as ordinary:
            ordinary.dismiss_error(
                error_id=error_id,
                idempotency_key=idempotency_key,
            )
            with self._condition:
                if ordinary is not self._ordinary_user_path:
                    raise RepositorySelectionError(
                        "The selected repository changed during error dismissal."
                    )
                return self._snapshot_locked()

    def ordinary_contract_record_error(self, code: str, message: str) -> str:
        with self._ordinary_user_path_operation() as ordinary:
            return ordinary.record_external_error(code=code, message=message)

    def intelligence_transplant_freeze_charter(
        self,
        record: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(record, Mapping):
            raise IntelligenceTransplantValidationError(
                "Run Charter must be an object."
            )
        with self._guided_intake_transplant_operation() as (
            guided_intake,
            intelligence_transplant,
        ):
            charter_source = guided_intake.charter_source()
            expected_source = {
                "completion_line": charter_source["completion_line"],
                "repository_head": charter_source["repository_head"],
                "source_freeze_id": charter_source["freeze_id"],
                "source_freeze_sha256": (
                    charter_source["frozen_intake_sha256"]
                ),
            }
            if any(
                record.get(key) != expected
                for key, expected in expected_source.items()
            ):
                raise IntelligenceTransplantValidationError(
                    "Run Charter does not match the current Guided Intake freeze."
                )
            projection = intelligence_transplant.freeze_charter(
                dict(record),
                charter_source=charter_source,
                repository_head=charter_source["repository_head"],
            )
            return self._snapshot_after_intelligence_transplant(
                intelligence_transplant,
                projection,
                guided_intake,
            )

    def _intelligence_transplant_attach(
        self,
        *,
        payload: bytes,
        mode: str,
        source_path_or_label: str,
        declared_sha256: str,
        context_evidence_ref: Mapping[str, Any] | None,
        as_of: str,
        operation: str,
    ) -> dict[str, Any]:
        record = self._transport_json_object(payload)
        object_type = record.get("object_type")
        if operation == "evidence":
            allowed_types = _INTELLIGENCE_TRANSPLANT_EVIDENCE_TYPES
        elif operation == "receipt":
            allowed_types = _INTELLIGENCE_TRANSPLANT_RECEIPT_TYPES
        elif operation == "manifest":
            allowed_types = frozenset(
                {"AUDIT_INPUT_MANIFEST", "LOWER_RUN_TRIAL_MANIFEST"}
            )
        elif operation == "control":
            allowed_types = frozenset({"MANUAL_CONTROL_RECEIPT"})
        else:
            raise IntelligenceTransplantValidationError(
                "Intelligence Transplant operation is invalid."
            )
        if object_type not in allowed_types:
            raise IntelligenceTransplantValidationError(
                "Intelligence Transplant object type does not match the route."
            )
        transport = self._intelligence_transplant_transport(
            payload=payload,
            mode=mode,
            source_path_or_label=source_path_or_label,
            declared_sha256=declared_sha256,
            context_evidence_ref=context_evidence_ref,
            as_of=as_of,
        )
        with self._intelligence_transplant_operation() as (
            intelligence_transplant
        ):
            if operation == "manifest":
                projection = intelligence_transplant.freeze_manifest(
                    record,
                    transport=transport,
                )
            elif operation == "control":
                projection = intelligence_transplant.record_control(
                    record,
                    transport=transport,
                )
            else:
                projection = intelligence_transplant.attach_object(
                    record,
                    transport=transport,
                )
            return self._snapshot_after_intelligence_transplant(
                intelligence_transplant,
                projection,
            )

    def intelligence_transplant_freeze_manifest(
        self,
        *,
        payload: bytes,
        mode: str,
        source_path_or_label: str,
        declared_sha256: str,
        context_evidence_ref: Mapping[str, Any] | None,
        as_of: str,
    ) -> dict[str, Any]:
        return self._intelligence_transplant_attach(
            payload=payload,
            mode=mode,
            source_path_or_label=source_path_or_label,
            declared_sha256=declared_sha256,
            context_evidence_ref=context_evidence_ref,
            as_of=as_of,
            operation="manifest",
        )

    def intelligence_transplant_attach_evidence(
        self,
        *,
        payload: bytes,
        mode: str,
        source_path_or_label: str,
        declared_sha256: str,
        context_evidence_ref: Mapping[str, Any] | None,
        as_of: str,
    ) -> dict[str, Any]:
        return self._intelligence_transplant_attach(
            payload=payload,
            mode=mode,
            source_path_or_label=source_path_or_label,
            declared_sha256=declared_sha256,
            context_evidence_ref=context_evidence_ref,
            as_of=as_of,
            operation="evidence",
        )

    def intelligence_transplant_attach_receipt(
        self,
        *,
        payload: bytes,
        mode: str,
        source_path_or_label: str,
        declared_sha256: str,
        context_evidence_ref: Mapping[str, Any] | None,
        as_of: str,
    ) -> dict[str, Any]:
        return self._intelligence_transplant_attach(
            payload=payload,
            mode=mode,
            source_path_or_label=source_path_or_label,
            declared_sha256=declared_sha256,
            context_evidence_ref=context_evidence_ref,
            as_of=as_of,
            operation="receipt",
        )

    def intelligence_transplant_record_control(
        self,
        *,
        payload: bytes,
        mode: str,
        source_path_or_label: str,
        declared_sha256: str,
        context_evidence_ref: Mapping[str, Any] | None,
        as_of: str,
    ) -> dict[str, Any]:
        return self._intelligence_transplant_attach(
            payload=payload,
            mode=mode,
            source_path_or_label=source_path_or_label,
            declared_sha256=declared_sha256,
            context_evidence_ref=context_evidence_ref,
            as_of=as_of,
            operation="control",
        )

    def start_run(
        self,
        task: str,
        *,
        task_mode: str = "manual",
    ) -> dict[str, Any]:
        if not isinstance(task, str) or not task.strip():
            raise CompanionError("Enter one bounded task before running.")
        if len(task) > 20_000:
            raise CompanionError("The bounded task exceeds the local size limit.")
        if not isinstance(task_mode, str) or task_mode not in {
            "manual",
            "contract",
        }:
            raise CompanionError("Run task mode is invalid.")
        with self._condition:
            repository = self._require_repository()
            if (
                self._run.get("run_type") == "intelligence_transplant"
                and self._run.get("state") == "active"
            ):
                raise RunConflictError(
                    "One Intelligence Transplant Run is already active."
                )
            self._require_no_active_run()
            if self._active_intelligence_transplant_operations:
                raise RunConflictError(
                    "An Intelligence Transplant action is already active."
                )
            self._prepare_bounded_run_locked(
                repository,
                task.strip(),
                task_mode=task_mode,
            )
            self._worker = threading.Thread(
                target=self._run_worker,
                args=(repository, task.strip()),
                name="decision-os-companion-run",
                daemon=True,
            )
            self._worker.start()
            return self._snapshot_locked()

    def _prepare_bounded_run_locked(
        self,
        repository: Path,
        task: str,
        *,
        task_mode: str,
        continuation: Mapping[str, Any] | None = None,
    ) -> None:
        before = self._safe_receipt(repository)
        self._run = self._empty_run()
        self._run["task_mode"] = task_mode
        self._run["state"] = "running"
        self._run["progress"] = ["Preparing the bounded task."]
        self._run["outcomes"]["execution"] = {
            "state": "running",
            "label": "Codex is working",
        }
        self._run["outcomes"]["verification"] = {
            "state": "pending",
            "label": "Pending",
            "reason": None,
        }
        self._run["receipt_before"] = before
        self._run["continuation"] = (
            None if continuation is None else deepcopy(dict(continuation))
        )
        self._last_run_result = None
        self._last_supervisor_context = None
        self._approval_choice = None

    def _lifecycle_sink(self, event: CodexLifecycleEvent) -> None:
        if (
            not isinstance(event, CodexLifecycleEvent)
            or event.kind not in _LIFECYCLE_MESSAGES
            or event.message != _LIFECYCLE_MESSAGES[event.kind]
        ):
            raise LifecycleEventError("Malformed companion lifecycle event.")
        with self._condition:
            if self._run["state"] != "running":
                raise LifecycleEventError(
                    "Lifecycle event arrived outside the active Run."
                )
            if event.message not in self._run["progress"]:
                self._run["progress"].append(event.message)
            self._condition.notify_all()

    def _approval_provider(self, approval: CodexApproval) -> str | None:
        if (
            not isinstance(approval, CodexApproval)
            or approval.action not in {"Create", "Modify"}
            or not approval.repository_name
            or not approval.normalized_scope
            or not isinstance(approval.diff, str)
        ):
            raise ApprovalStateError("Malformed file approval request.")
        with self._condition:
            if self._run["state"] != "running":
                return "3"
            if (
                self._compound_active
                and approval.normalized_scope
                not in self._compound_allowed_mutation_paths
            ):
                return "3"
            self._run["approval"] = {
                "repository": approval.repository_name,
                "action": approval.action,
                "path": approval.normalized_scope,
                "diff": approval.diff,
                "reason": approval.reason,
            }
            self._approval_choice = None
            self._condition.notify_all()
            while (
                self._run["state"] == "running"
                and self._approval_choice is None
            ):
                self._condition.wait(timeout=1)
            choice = self._approval_choice or "3"
            self._run["approval"] = None
            self._approval_choice = None
            self._condition.notify_all()
            return choice

    def submit_approval(self, choice: str) -> dict[str, Any]:
        choices = {
            "allow_once": "1",
            "repository": "2",
            "deny": "3",
        }
        if choice not in choices:
            raise ApprovalStateError("Approval choice is unsupported.")
        with self._condition:
            if (
                self._run["state"] != "running"
                or self._run["approval"] is None
                or self._approval_choice is not None
            ):
                raise ApprovalStateError("No file approval is waiting.")
            self._approval_choice = choices[choice]
            self._condition.notify_all()
            return self._snapshot_locked()

    def _run_worker(self, repository: Path, task: str) -> None:
        try:
            result = self._execute_worker_run(repository, task)
            self._complete_run(repository, result)
        except Exception as exc:
            self._fail_run(repository, exc)

    def _execute_worker_run(
        self,
        repository: Path,
        task: str,
    ) -> CodexRunResult:
        engine = AccelerationEngine(
            repository,
            adapter=ADAPTER_NAME,
            adapter_version=CODEX_CLI_VERSION,
        )
        adapter = self.adapter_factory(
            engine,
            self._approval_provider,
            self._lifecycle_sink,
        )
        return asyncio.run(adapter.run(task))

    @staticmethod
    def _public_runtime(result: CodexRunResult) -> dict[str, str] | None:
        identity = result.runtime_identity
        if identity is None:
            return None
        return {
            "authentication": identity.account_type,
            "model": identity.model,
            "reasoning_effort": identity.reasoning_effort,
            "service_tier": identity.service_tier,
            "codex_version": identity.codex_cli_version,
        }

    @staticmethod
    def _public_actions(result: CodexRunResult) -> list[dict[str, str]]:
        return [
            {
                "action": action.action,
                "path": action.normalized_scope,
                "access": action.access,
                "status": action.status,
            }
            for action in result.file_actions
        ]

    @staticmethod
    def _public_read_evidence(
        result: CodexRunResult,
    ) -> list[dict[str, Any]]:
        return [
            {
                "path": evidence.path,
                "bytes": evidence.byte_count,
                "sha256": evidence.sha256,
                "repository_identity": evidence.repository_identity,
                "status": evidence.status,
                "reason": evidence.reason,
            }
            for evidence in result.read_evidence
        ]

    @staticmethod
    def _public_outcomes(result: CodexRunResult) -> dict[str, Any]:
        execution_completed = result.turn_status == "completed"
        execution = {
            "state": "completed" if execution_completed else "not_completed",
            "label": (
                "Codex turn completed"
                if execution_completed
                else "Codex turn did not complete"
            ),
        }

        completed_actions = [
            action
            for action in result.file_actions
            if action.status == "approved"
        ]
        if completed_actions:
            action = completed_actions[-1]
            verb = "Created" if action.action == "Create" else "Modified"
            file_change = {
                "state": verb.lower(),
                "label": f"{verb} successfully",
            }
        elif any(
            action.status == "denied" for action in result.file_actions
        ):
            file_change = {
                "state": "denied",
                "label": "No file was modified — change denied",
            }
        elif result.status in {
            "NORMAL_TERMINAL",
            "VERIFIED_SAVE",
            "VERIFIED_REUSE",
        }:
            file_change = {
                "state": "none",
                "label": "No file was modified",
            }
        else:
            file_change = {
                "state": "unknown",
                "label": (
                    "Not established — file-change outcome requires review"
                ),
            }

        if result.status in {
            "NORMAL_TERMINAL",
            "VERIFIED_SAVE",
            "VERIFIED_REUSE",
        }:
            verification_state = "completed"
            verification_label = (
                "Verified"
                if result.status in {"VERIFIED_SAVE", "VERIFIED_REUSE"}
                else "Completed"
            )
        elif result.status == "UNSUPPORTED_MUTATION":
            verification_state = "unsupported"
            verification_label = "Unsupported — review required"
        elif result.status == "DENIED":
            verification_state = "not_completed"
            verification_label = "Not completed — change denied"
        else:
            verification_state = "needs_attention"
            verification_label = "Needs attention"
        return {
            "execution": execution,
            "file_change": file_change,
            "verification": {
                "state": verification_state,
                "label": verification_label,
                "reason": result.unsupported_reason,
            },
        }

    @staticmethod
    def _display_state(result: CodexRunResult) -> str:
        if result.status in {
            "NORMAL_TERMINAL",
            "VERIFIED_SAVE",
            "VERIFIED_REUSE",
        }:
            return "completed"
        if result.status == "DENIED":
            return "denied"
        if result.status == "UNSUPPORTED_MUTATION":
            return "unsupported"
        return "needs_attention"

    def _complete_run(
        self,
        repository: Path,
        result: CodexRunResult,
    ) -> None:
        after = self._safe_receipt(repository)
        diagnostic = (
            None
            if result.failure_diagnostic is None
            else canonical_failure_diagnostic(result.failure_diagnostic)
        )
        with self._condition:
            before = self._run.pop("receipt_before")
            self._run["state"] = (
                "needs_attention"
                if diagnostic is not None
                else self._display_state(result)
            )
            self._run["result"] = (
                "" if diagnostic is not None else result.final_message
            )
            self._run["file_actions"] = self._public_actions(result)
            self._run["read_evidence"] = self._public_read_evidence(result)
            outcomes = self._public_outcomes(result)
            if diagnostic is not None:
                outcomes["verification"] = {
                    "state": "needs_attention",
                    "label": "Needs attention",
                    "reason": diagnostic.reason,
                }
            self._run["outcomes"] = outcomes
            self._run["runtime"] = self._public_runtime(result)
            self._run["receipt_delta"] = self._receipt_delta(before, after)
            self._run["supervisor"] = None
            self._last_run_result = result
            self._last_supervisor_context = None
            self._run["approval"] = None
            self._run["error"] = (
                diagnostic.reason if diagnostic is not None else None
            )
            self._run["failure"] = (
                diagnostic.as_dict() if diagnostic is not None else None
            )
            self._condition.notify_all()

    @staticmethod
    def _safe_failure(
        exc: Exception,
    ) -> CodexFailureDiagnostic | None:
        try:
            attached = exc.diagnostic
        except Exception:
            attached = object()
        if isinstance(exc, CodexAdapterUnavailable):
            if attached is None:
                return CodexFailureDiagnostic.for_phase("transport_start")
            return canonical_failure_diagnostic(attached)
        if isinstance(exc, CodexAdapterFailure):
            if attached is None:
                return CodexFailureDiagnostic.for_phase("unknown")
            return canonical_failure_diagnostic(attached)
        return None

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        diagnostic = CompanionController._safe_failure(exc)
        if diagnostic is not None:
            return diagnostic.reason
        if isinstance(exc, StateIntegrityError):
            return "Repository verification state is corrupted."
        if isinstance(exc, LifecycleEventError):
            return "The companion received an invalid progress event."
        if isinstance(exc, ApprovalStateError):
            return "The companion approval bridge failed closed."
        return "The bounded Run could not complete safely."

    def _fail_run(self, repository: Path, exc: Exception) -> None:
        try:
            after = self._safe_receipt(repository)
        except StateIntegrityError:
            after = None
        diagnostic = self._safe_failure(exc)
        with self._condition:
            before = self._run.pop("receipt_before", None)
            self._run["state"] = "needs_attention"
            self._run["result"] = ""
            self._run["file_actions"] = []
            self._run["read_evidence"] = []
            self._run["outcomes"] = {
                "execution": {
                    "state": "not_completed",
                    "label": "Codex turn did not complete",
                },
                "file_change": {
                    "state": "unknown",
                    "label": (
                        "Not established — file-change outcome requires review"
                    ),
                },
                "verification": {
                    "state": "needs_attention",
                    "label": "Needs attention",
                    "reason": (
                        diagnostic.reason
                        if diagnostic is not None
                        else None
                    ),
                },
            }
            self._run["runtime"] = None
            self._run["receipt_delta"] = (
                self._receipt_delta(before, after)
                if before is not None and after is not None
                else None
            )
            self._run["supervisor"] = None
            self._last_run_result = None
            self._last_supervisor_context = None
            self._run["approval"] = None
            self._run["error"] = self._safe_error(exc)
            self._run["failure"] = (
                diagnostic.as_dict() if diagnostic is not None else None
            )
            self._approval_choice = "3"
            self._condition.notify_all()

    def supervise_last_run(
        self,
        context: SupervisorContext,
    ) -> dict[str, Any]:
        if not isinstance(context, SupervisorContext):
            raise SupervisorStateError("Supervisor context is invalid.")
        with self._condition:
            self._require_repository()
            self._require_no_active_run()
            if (
                self._run.get("run_type") != "bounded_task"
                or self._run.get("state") not in _TERMINAL_STATES
                or self._last_run_result is None
            ):
                raise SupervisorStateError(
                    "No exact completed bounded Worker Run is available."
                )
            if self._run.get("supervisor") is not None:
                if context != self._last_supervisor_context:
                    raise SupervisorStateError(
                        "The completed Worker Run already has a different "
                        "Supervisor context."
                    )
                return self._snapshot_locked()
            judgment = judge_continuation(self._last_run_result, context)
            self._run["supervisor"] = judgment.as_dict()
            self._last_supervisor_context = context
            return self._snapshot_locked()

    def start_one_automatic_continuation(
        self,
        request: StageBContinuationRequest,
    ) -> dict[str, Any]:
        """Start Run 1 and permit exactly one persisted GO continuation."""

        if not isinstance(request, StageBContinuationRequest):
            raise ContinuationStateError(
                "Stage B requires one explicit continuation authority envelope."
            )
        with self._condition:
            repository = self._require_repository()
            self._require_no_active_run()
            if self._active_intelligence_transplant_operations:
                raise RunConflictError(
                    "An Intelligence Transplant action is already active."
                )
            persisted: dict[str, Any] | None = None
            try:
                normalized_paths = tuple(
                    normalize_scope(repository, path)
                    for path in request.allowed_mutation_paths
                )
                normalized_request = replace(
                    request,
                    allowed_mutation_paths=normalized_paths,
                )
                repository_identity = AccelerationStore(
                    repository
                ).repository_id
                chain_id = secrets.token_hex(16)
                persisted = self._continuation_store.save(
                    new_record(
                        normalized_request,
                        chain_id=chain_id,
                        repository_id=repository_identity,
                    )
                )
                self._prepare_bounded_run_locked(
                    repository,
                    normalized_request.run_1_task.strip(),
                    task_mode="contract",
                    continuation={
                        "schema": (
                            "decision-os-bounded-run-continuation-v0.1"
                        ),
                        "chain_id": chain_id,
                        "run_number": 1,
                        "automatic": False,
                        "source_run_id": None,
                        "source_evidence_sha256": None,
                        "task_sha256": hashlib.sha256(
                            normalized_request.run_1_task.strip().encode(
                                "utf-8"
                            )
                        ).hexdigest(),
                    },
                )
            except (
                ContinuationIntegrityError,
                OSError,
                RepositoryIdentityError,
                StateIntegrityError,
                ValueError,
            ) as exc:
                try:
                    if persisted is not None:
                        persisted["state"] = "BLOCKED"
                        persisted["governed_stop"] = governed_stop(
                            gate="BLOCK",
                            route="EVIDENCE-RECOVERY",
                            reason=(
                                "Stage B Run 1 could not start from verified "
                                "persisted authority and Receipt state."
                            ),
                            next_action=(
                                "Recover the exact persisted Stage B authority "
                                "and pre-Run Receipt under the unchanged Goal."
                            ),
                        )
                        self._compound_loop = self._continuation_store.save(
                            persisted
                        )
                except (ContinuationIntegrityError, OSError, ValueError):
                    self._set_stage_b_blocked_view()
                raise ContinuationStateError(
                    "Stage B authority or persistence could not be established."
                ) from exc
            assert persisted is not None
            self._compound_loop = persisted
            self._compound_active = True
            self._compound_recovery_required = False
            self._compound_allowed_mutation_paths = normalized_paths
            self._worker = threading.Thread(
                target=self._stage_b_worker,
                args=(repository, normalized_request),
                name="decision-os-companion-stage-b",
                daemon=True,
            )
            self._worker.start()
            return self._snapshot_locked()

    def _stage_b_worker(
        self,
        repository: Path,
        request: StageBContinuationRequest,
    ) -> None:
        try:
            run_1 = self._execute_worker_run(
                repository,
                request.run_1_task.strip(),
            )
            self._complete_run(repository, run_1)
        except Exception as exc:
            self._fail_run(repository, exc)
            self._stage_b_execution_stop(run_number=1)
            return
        try:
            task_2 = self._stage_b_prepare_run_2(repository, run_1)
        except (
            ContinuationIntegrityError,
            OSError,
            RepositoryIdentityError,
            StateIntegrityError,
            ValueError,
        ):
            self._stage_b_integrity_stop()
            return
        if task_2 is None:
            return

        try:
            run_2 = self._execute_worker_run(repository, task_2)
            self._complete_run(repository, run_2)
        except Exception as exc:
            self._fail_run(repository, exc)
            self._stage_b_execution_stop(run_number=2)
            return
        try:
            self._stage_b_finish_run_2(run_2)
        except (ContinuationIntegrityError, OSError, ValueError):
            self._stage_b_integrity_stop()

    def _stage_b_prepare_run_2(
        self,
        repository: Path,
        run_1: CodexRunResult,
    ) -> str | None:
        with self._condition:
            record = self._continuation_store.load_required()
            if (
                record.get("state") != "RUN_1_ACTIVE"
                or record.get("repository_id")
                != AccelerationStore(repository).repository_id
                or record.get("runs")
                or record.get("automatic_continuations_started") != 0
                or self._run.get("continuation", {}).get("chain_id")
                != record.get("chain_id")
            ):
                raise ContinuationIntegrityError(
                    "Run 1 does not match the persisted Stage B chain."
                )
            receipt_delta = self._run.get("receipt_delta")
            if not isinstance(receipt_delta, dict):
                raise ContinuationIntegrityError(
                    "Run 1 Receipt delta is not established."
                )
            record["runs"] = [
                result_evidence(
                    run_1,
                    run_number=1,
                    receipt_delta=receipt_delta,
                )
            ]
            record["state"] = "RUN_1_COMPLETE"
            record = self._continuation_store.save(record)
            context = supervisor_context_from_persisted_run(record)
            judgment = judge_continuation(run_1, context)
            self._run["supervisor"] = judgment.as_dict()
            self._last_supervisor_context = context
            record["supervisor"] = judgment.as_dict()

            if (
                judgment.gate.value != "GO"
                or judgment.decision_route.value != "AI-OWNED"
            ):
                next_action = (
                    judgment.next_bounded_action
                    if judgment.next_bounded_action is not None
                    else judgment.human_seat_return
                )
                assert next_action is not None
                record["state"] = "STOPPED"
                record["governed_stop"] = governed_stop(
                    gate=judgment.gate.value,
                    route=judgment.decision_route.value,
                    reason=judgment.reason,
                    next_action=next_action,
                )
                self._compound_loop = self._continuation_store.save(record)
                self._compound_active = False
                self._compound_allowed_mutation_paths = ()
                self._condition.notify_all()
                return None

            record = self._continuation_store.save(record)
            automatic_task = automatic_task_from_persisted_run(record)
            record["automatic_task"] = automatic_task
            record["automatic_continuations_started"] = 1
            record["state"] = "RUN_2_ACTIVE"
            persisted = self._continuation_store.save(record)
            persisted_task = persisted.get("automatic_task")
            if (
                not isinstance(persisted_task, dict)
                or persisted_task != automatic_task
            ):
                raise ContinuationIntegrityError(
                    "Persisted automatic Task 2 read-back mismatches."
                )
            self._compound_loop = persisted
            self._prepare_bounded_run_locked(
                repository,
                automatic_task["task"],
                task_mode="contract",
                continuation={
                    "schema": "decision-os-bounded-run-continuation-v0.1",
                    "chain_id": record["chain_id"],
                    "run_number": 2,
                    "automatic": True,
                    "source_run_id": automatic_task["source_run_id"],
                    "source_evidence_sha256": automatic_task[
                        "source_evidence_sha256"
                    ],
                    "task_sha256": automatic_task["task_sha256"],
                },
            )
            self._condition.notify_all()
            return automatic_task["task"]

    def _stage_b_finish_run_2(self, run_2: CodexRunResult) -> None:
        with self._condition:
            record = self._continuation_store.load_required()
            if (
                record.get("state") != "RUN_2_ACTIVE"
                or record.get("automatic_continuations_started") != 1
                or len(record.get("runs", [])) != 1
                or self._run.get("continuation", {}).get("run_number") != 2
                or self._run.get("continuation", {}).get("source_run_id")
                != record["runs"][0]["run_id"]
            ):
                raise ContinuationIntegrityError(
                    "Run 2 does not match the persisted Stage B causal chain."
                )
            receipt_delta = self._run.get("receipt_delta")
            if not isinstance(receipt_delta, dict):
                raise ContinuationIntegrityError(
                    "Run 2 Receipt delta is not established."
                )
            record["runs"].append(
                result_evidence(
                    run_2,
                    run_number=2,
                    receipt_delta=receipt_delta,
                )
            )
            record["state"] = "COMPLETE"
            if (
                not run_2.normal_terminal
                or run_2.turn_status != "completed"
                or run_2.status
                not in {"NORMAL_TERMINAL", "VERIFIED_SAVE", "VERIFIED_REUSE"}
            ):
                record["governed_stop"] = governed_stop(
                    gate="HOLD",
                    route="STOP",
                    reason=(
                        "Automatic Worker Run 2 did not establish a clean "
                        "normal-terminal result."
                    ),
                    next_action=(
                        "Preserve both Run records and recover bounded Run 2 "
                        "evidence under the unchanged Goal."
                    ),
                )
            self._compound_loop = self._continuation_store.save(record)
            self._compound_active = False
            self._compound_allowed_mutation_paths = ()
            self._condition.notify_all()

    def _stage_b_execution_stop(self, *, run_number: int) -> None:
        with self._condition:
            try:
                record = self._continuation_store.load_required()
                record["state"] = "STOPPED"
                record["governed_stop"] = governed_stop(
                    gate="HOLD",
                    route="EVIDENCE-RECOVERY",
                    reason=(
                        f"Automatic compound Worker Run {run_number} could not "
                        "complete safely."
                    ),
                    next_action=(
                        f"Recover bounded Worker Run {run_number} execution "
                        "evidence under the unchanged persisted authority."
                    ),
                )
                self._compound_loop = self._continuation_store.save(record)
                self._compound_recovery_required = False
            except (ContinuationIntegrityError, OSError, ValueError):
                self._set_stage_b_blocked_view()
            self._compound_active = False
            self._compound_allowed_mutation_paths = ()
            self._condition.notify_all()

    def _stage_b_integrity_stop(self) -> None:
        with self._condition:
            try:
                record = self._continuation_store.load_required()
                record["state"] = "BLOCKED"
                record["governed_stop"] = governed_stop(
                    gate="BLOCK",
                    route="EVIDENCE-RECOVERY",
                    reason=(
                        "The causal Stage B continuation proof is not intact."
                    ),
                    next_action=(
                        "Recover the exact persisted Goal, authority, Run 1 "
                        "evidence, Supervisor judgment, and Task 2 binding."
                    ),
                )
                self._compound_loop = self._continuation_store.save(record)
                self._compound_recovery_required = False
            except (ContinuationIntegrityError, OSError, ValueError):
                self._set_stage_b_blocked_view()
            self._compound_active = False
            self._compound_allowed_mutation_paths = ()
            self._condition.notify_all()

    def _set_stage_b_blocked_view(self) -> None:
        self._compound_loop = {
            "schema": "decision-os-stage-b-continuation-view-v0.1",
            "state": "BLOCKED_CORRUPT",
            "gate": "BLOCK",
            "decision_route": "EVIDENCE-RECOVERY",
            "automatic_continuations_started": 0,
            "automatic_continuation_limit": 1,
            "error": "The causal Stage B continuation proof is not intact.",
            "next_bounded_action": (
                "Recover the exact persisted Goal, authority, Run evidence, "
                "Supervisor judgment, and Task 2 binding."
            ),
        }
        self._compound_recovery_required = True

    def new_run(self) -> dict[str, Any]:
        with self._condition:
            self._require_repository()
            self._require_no_active_run()
            if self._active_intelligence_transplant_operations:
                raise RunConflictError(
                    "An Intelligence Transplant action is already active."
                )
            self._run = self._empty_run()
            self._last_run_result = None
            self._last_supervisor_context = None
            self._approval_choice = None
            return self._snapshot_locked()

    @staticmethod
    def _safe_receipt(repository: Path) -> dict[str, Any]:
        return AccelerationEngine(repository).receipt()

    @staticmethod
    def _public_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
        hard = receipt["hard_metrics"]
        estimated = receipt["estimated"]
        return {
            "status": receipt["status"],
            "verified_saves": hard["verified_saves"],
            "verified_reuses": hard["verified_reuses"],
            "estimated_minutes": estimated["minutes"],
            "estimated_money_jpy": estimated["money_jpy"],
            "estimated_tokens": estimated["tokens"],
            "claim_boundary": receipt["claim_boundary"],
        }

    @staticmethod
    def _receipt_delta(
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> dict[str, Any]:
        before_public = CompanionController._public_receipt(before)
        after_public = CompanionController._public_receipt(after)
        before_tokens = before_public["estimated_tokens"]
        after_tokens = after_public["estimated_tokens"]
        return {
            "verified_saves": (
                after_public["verified_saves"]
                - before_public["verified_saves"]
            ),
            "verified_reuses": (
                after_public["verified_reuses"]
                - before_public["verified_reuses"]
            ),
            "estimated_minutes": (
                after_public["estimated_minutes"]
                - before_public["estimated_minutes"]
            ),
            "estimated_money_jpy": (
                after_public["estimated_money_jpy"]
                - before_public["estimated_money_jpy"]
            ),
            "estimated_tokens": (
                None
                if before_tokens is None or after_tokens is None
                else after_tokens - before_tokens
            ),
        }

    def _default_view(
        self,
        records: tuple[ActiveDefaultRecord, ...],
    ) -> list[dict[str, str]]:
        active_keys = {record.decision_key for record in records}
        self._default_handles = {
            handle: key
            for handle, key in self._default_handles.items()
            if key in active_keys
        }
        key_to_handle = {
            key: handle for handle, key in self._default_handles.items()
        }
        result: list[dict[str, str]] = []
        for record in records:
            handle = key_to_handle.get(record.decision_key)
            if handle is None:
                handle = secrets.token_urlsafe(18)
                self._default_handles[handle] = record.decision_key
            result.append(
                {
                    "handle": handle,
                    "action": (
                        "Create"
                        if record.decision_type == "CREATE_FILE"
                        else "Modify"
                    ),
                    "path": record.normalized_scope,
                    "created_at": record.created_at,
                }
            )
        return result

    def revoke_default(self, handle: str) -> dict[str, Any]:
        if not isinstance(handle, str) or not handle:
            raise CompanionError("Saved access handle is invalid.")
        with self._condition:
            repository = self._require_repository()
            self._require_no_active_run()
            decision_key = self._default_handles.get(handle)
            if decision_key is None:
                raise CompanionError("Saved access is no longer active.")
            engine = AccelerationEngine(repository)
            engine.revoke(
                run_id=engine.new_run_id(),
                decision_key=decision_key,
            )
            self._default_handles.pop(handle, None)
            return self._snapshot_locked()

    def snapshot(self) -> dict[str, Any]:
        with self._condition:
            return self._snapshot_locked()

    def _snapshot_locked(self) -> dict[str, Any]:
        if self._repository is None:
            repository_view = None
            receipt = None
            defaults: list[dict[str, str]] = []
            bridge = None
            guided_intake = None
            ordinary_contract = {
                "schema": "decision-os-ordinary-user-path-view-v0.1",
                "state": "NO_CONTRACT",
                "status_label": "Select a Contract",
                "progress_text": "Choose a local Git repository first.",
                "operation_revision": 0,
                "preparation_id": None,
                "repository_identity": None,
                "source_identity": None,
                "review": None,
                "clarification": None,
                "contract_summary": "",
                "execution_authority": EXECUTION_AUTHORITY_UNKNOWN,
                "execution_authority_reason": UNKNOWN_EXECUTION_AUTHORITY_REASON,
                "allowed_actions": [],
                "technical_details": {"active_request_id": None},
                "action_error": None,
            }
            intelligence_transplant = None
        else:
            store = AccelerationStore(self._repository)
            receipt = self._public_receipt(
                AccelerationEngine(
                    self._repository,
                    store=store,
                ).receipt()
            )
            defaults = self._default_view(store.active_defaults())
            repository_view = {
                "name": self._repository.name,
                "path": str(self._repository),
            }
            try:
                bridge = self._require_bridge().snapshot()
            except (ManualBridgeIntegrityError, ManualBridgeBusyError) as exc:
                bridge = {
                    "state": (
                        "BOUNDARY_INCOMPLETE"
                        if isinstance(exc, ManualBridgeBusyError)
                        else "BLOCKED_CORRUPT"
                    ),
                    "error": (
                        "Manual Bridge is temporarily busy."
                        if isinstance(exc, ManualBridgeBusyError)
                        else (
                            "Manual Bridge state is corrupted. "
                            "Bridge reads and writes are blocked."
                        )
                    ),
                    "session": None,
                    "imports": [],
                    "outputs": {},
                    "golden_manifest": None,
                    "results": {
                        "protocol": "IN PROGRESS / NOT FINAL",
                        "product": (
                            "BUILDER EVIDENCE ONLY / "
                            "INDEPENDENT AUDIT REQUIRED"
                        ),
                        "replay": "NOT YET PERFORMED",
                    },
                    "burden": {},
                }
            try:
                guided_intake = self._require_guided_intake().snapshot()
            except (
                GuidedIntakeIntegrityError,
                GuidedIntakeBusyError,
            ) as exc:
                guided_intake = {
                    "active_question": None,
                    "authority_claim": AUTHORITY_CLAIM,
                    "authority_explanation": AUTHORITY_EXPLANATION,
                    "copy_for_pro_prompt": None,
                    "error": (
                        "Guided Intake is temporarily busy."
                        if isinstance(exc, GuidedIntakeBusyError)
                        else (
                            "Guided Intake state is corrupted. "
                            "Guided Intake reads and writes are blocked."
                        )
                    ),
                    "fidelity_evaluation": "BLOCKED",
                    "freeze": None,
                    "interpretation": None,
                    "judgment_reuse": "BLOCKED",
                    "original_request": None,
                    "purge": None,
                    "raw_source_availability": "UNKNOWN",
                    "request_history": [],
                    "request_identity": None,
                    "state": (
                        "BUSY"
                        if isinstance(exc, GuidedIntakeBusyError)
                        else "BLOCKED_CORRUPT"
                    ),
                    "transfer_receipt": None,
                }
            try:
                ordinary_contract = self._require_ordinary_user_path().snapshot()
            except OrdinaryUserPathError as exc:
                ordinary_contract = {
                    "schema": "decision-os-ordinary-user-path-view-v0.1",
                    "state": "CANNOT_FIX_SAFELY",
                    "status_label": "Cannot be fixed safely",
                    "progress_text": "The ordinary Contract path is unavailable.",
                    "operation_revision": 0,
                    "preparation_id": None,
                    "repository_identity": None,
                    "source_identity": None,
                    "review": None,
                    "clarification": None,
                    "contract_summary": "",
                    "execution_authority": EXECUTION_AUTHORITY_UNKNOWN,
                    "execution_authority_reason": UNKNOWN_EXECUTION_AUTHORITY_REASON,
                    "allowed_actions": [],
                    "technical_details": {"active_request_id": None},
                    "action_error": {
                        "schema": "decision-os-ordinary-action-error-v0.1",
                        "error_id": exc.error_id,
                        "scope": "SELECTION_PREPARATION",
                        "code": exc.code,
                        "what_failed": exc.message,
                        "current_state": "CANNOT_FIX_SAFELY",
                        "anything_fixed": "UNKNOWN_READ_BACK_REQUIRED",
                        "user_action_required": "Use Advanced / Audit Mode only after integrity review.",
                        "retryable": False,
                        "operation_id": None,
                        "recorded_at": None,
                        "dismissed_at": None,
                    },
                }
            try:
                intelligence_transplant = (
                    self._require_intelligence_transplant().snapshot()
                )
            except (
                IntelligenceTransplantIntegrityError,
                IntelligenceTransplantBusyError,
            ) as exc:
                busy = isinstance(exc, IntelligenceTransplantBusyError)
                intelligence_transplant = {
                    "run_id": None,
                    "run_type": "intelligence_transplant",
                    "execution_status": "NOT_ESTABLISHED",
                    "delta_state": "NONE",
                    "current_gate": "HOLD" if busy else "BLOCK",
                    "missing_evidence": [
                        (
                            "STAGE5_STORE_BUSY"
                            if busy
                            else "STAGE5_STORE_INTEGRITY"
                        )
                    ],
                    "next_one_action": (
                        "Retry the read after the bounded store operation."
                        if busy
                        else (
                            "Repair the Stage 5 store from verified event "
                            "and blob identities."
                        )
                    ),
                    "not_allowed_next": [
                        "STATE_PROMOTION",
                        "MODEL_INVOCATION",
                        "ROLE_ASSIGNMENT",
                    ],
                    "evidence_objects": [],
                    "lineage": [],
                    "active_cap": None,
                    "generalized_transplant": "NOT ESTABLISHED",
                    "structural_validation": "UNKNOWN" if busy else "FAIL",
                    "authority_provenance": "MANUAL OWNER ATTESTED",
                    "cryptographic_provenance": "NOT ESTABLISHED",
                    "store_state": "BUSY" if busy else "BLOCKED_CORRUPT",
                    "error": (
                        "Intelligence Transplant is temporarily busy."
                        if busy
                        else (
                            "Intelligence Transplant state is corrupted. "
                            "Stage 5 reads and writes are blocked."
                        )
                    ),
                }
        if (
            self._run.get("run_type") == "intelligence_transplant"
            and intelligence_transplant is not None
        ):
            run = self._intelligence_transplant_run(
                intelligence_transplant
            )
            # Stage 5 maturity is always derived from the freshly verified
            # projection above.  Keep the private cache synchronized so a
            # later operation or projection cannot reuse stale maturity.
            self._run = deepcopy(run)
        else:
            run = {
                key: value
                for key, value in self._run.items()
                if key != "receipt_before"
            }
        return {
            "repository": repository_view,
            "run": run,
            "compound_loop": deepcopy(self._compound_loop),
            "receipt": receipt,
            "defaults": defaults,
            "manual_bridge": bridge,
            "guided_intake": guided_intake,
            "ordinary_contract": ordinary_contract,
            "intelligence_transplant": intelligence_transplant,
            "supported": (
                "Read-only work or one exact typed single-file create or modify."
            ),
        }
