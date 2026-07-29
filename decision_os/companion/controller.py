"""Thread-safe presentation controller over the existing Verified Save backend."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import contextmanager
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
    CodexLifecycleEvent,
    CodexRunResult,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import RepositoryIdentityError, git_root
from decision_os.acceleration.store import (
    AccelerationStore,
    ActiveDefaultRecord,
    StateIntegrityError,
)
from decision_os.companion.guided_intake import (
    AUTHORITY_CLAIM,
    AUTHORITY_EXPLANATION,
    GuidedIntakeBusyError,
    GuidedIntakeController,
    GuidedIntakeIntegrityError,
)
from decision_os.companion.manual_bridge import (
    BridgeSessionController,
    ManualBridgeBusyError,
    ManualBridgeIntegrityError,
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
        self._approval_choice: str | None = None
        self._default_handles: dict[str, str] = {}
        self._worker: threading.Thread | None = None
        self._bridge: BridgeSessionController | None = None
        self._guided_intake: GuidedIntakeController | None = None
        self._active_bridge_operations = 0
        self._active_guided_intake_operations = 0
        self._repository_selection_active = False
        self._load_last_repository()
        if self._repository is not None:
            self._bridge = BridgeSessionController(self._repository)
            self._guided_intake = GuidedIntakeController(self._repository)

    @staticmethod
    def _empty_run() -> dict[str, Any]:
        return {
            "state": "idle",
            "progress": [],
            "result": "",
            "file_actions": [],
            "runtime": None,
            "receipt_delta": None,
            "approval": None,
            "error": None,
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
                self._write_last_repository(repository)
                self._repository = repository
                self._bridge = BridgeSessionController(repository)
                self._guided_intake = GuidedIntakeController(repository)
                self._default_handles = {}
                self._run = self._empty_run()
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
        if self._run["state"] == "running":
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
            guided_intake = self._require_guided_intake()
            self._active_guided_intake_operations += 1
        try:
            yield guided_intake
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

    def start_run(self, task: str) -> dict[str, Any]:
        if not isinstance(task, str) or not task.strip():
            raise CompanionError("Enter one bounded task before running.")
        if len(task) > 20_000:
            raise CompanionError("The bounded task exceeds the local size limit.")
        with self._condition:
            repository = self._require_repository()
            self._require_no_active_run()
            before = self._safe_receipt(repository)
            self._run = self._empty_run()
            self._run["state"] = "running"
            self._run["progress"] = ["Preparing the bounded task."]
            self._run["receipt_before"] = before
            self._approval_choice = None
            self._worker = threading.Thread(
                target=self._run_worker,
                args=(repository, task.strip()),
                name="decision-os-companion-run",
                daemon=True,
            )
            self._worker.start()
            return self._snapshot_locked()

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
        engine = AccelerationEngine(
            repository,
            adapter=ADAPTER_NAME,
            adapter_version=CODEX_CLI_VERSION,
        )
        try:
            adapter = self.adapter_factory(
                engine,
                self._approval_provider,
                self._lifecycle_sink,
            )
            result = asyncio.run(adapter.run(task))
            self._complete_run(repository, result)
        except Exception as exc:
            self._fail_run(repository, exc)

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
        with self._condition:
            before = self._run.pop("receipt_before")
            self._run["state"] = self._display_state(result)
            self._run["result"] = result.final_message
            self._run["file_actions"] = self._public_actions(result)
            self._run["runtime"] = self._public_runtime(result)
            self._run["receipt_delta"] = self._receipt_delta(before, after)
            self._run["approval"] = None
            self._run["error"] = None
            self._condition.notify_all()

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        if isinstance(exc, StateIntegrityError):
            return "Repository verification state is corrupted."
        if isinstance(exc, CodexAdapterUnavailable):
            return "The private Codex runtime is unavailable."
        if isinstance(exc, CodexAdapterFailure):
            return "The bounded Codex Run failed closed."
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
        with self._condition:
            before = self._run.pop("receipt_before", None)
            self._run["state"] = "needs_attention"
            self._run["result"] = ""
            self._run["file_actions"] = []
            self._run["runtime"] = None
            self._run["receipt_delta"] = (
                self._receipt_delta(before, after)
                if before is not None and after is not None
                else None
            )
            self._run["approval"] = None
            self._run["error"] = self._safe_error(exc)
            self._approval_choice = "3"
            self._condition.notify_all()

    def new_run(self) -> dict[str, Any]:
        with self._condition:
            self._require_repository()
            self._require_no_active_run()
            self._run = self._empty_run()
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
                    "freeze": None,
                    "interpretation": None,
                    "original_request": None,
                    "request_history": [],
                    "request_identity": None,
                    "state": (
                        "BUSY"
                        if isinstance(exc, GuidedIntakeBusyError)
                        else "BLOCKED_CORRUPT"
                    ),
                    "transfer_receipt": None,
                }
        return {
            "repository": repository_view,
            "run": {
                key: value
                for key, value in self._run.items()
                if key != "receipt_before"
            },
            "receipt": receipt,
            "defaults": defaults,
            "manual_bridge": bridge,
            "guided_intake": guided_intake,
            "supported": (
                "Read-only work or one exact typed single-file create or modify."
            ),
        }
