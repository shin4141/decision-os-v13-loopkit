"""Field Notes Lite v0.1 Capture controller."""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import partial
import hashlib
import io
import os
from pathlib import Path
import stat
from typing import Any

from decision_os.acceleration.codex_adapter import (
    ADAPTER_NAME,
    CODEX_CLI_VERSION,
    CodexApproval,
    CodexLifecycleEvent,
    CodexReadEvidence,
    CodexRunResult,
    CodexRuntimeIdentity,
    _READ_MAX_BYTES,
    _READ_MAX_DISTINCT_PATHS,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.companion.controller import (
    CompanionController,
    CompanionError,
)
from decision_os.companion.field_notes_adapter import (
    FieldNoteA1ProposalDiagnostic,
    FieldNoteCreatorLiveA1CaptureConfig,
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
) -> FieldNotesCodexAdapter:
    return FieldNotesCodexAdapter(
        engine,
        input_func=lambda: None,
        stdout=io.StringIO(),
        approval_provider=approval_provider,
        lifecycle_sink=lifecycle_sink,
        trusted_source_model_class=trusted_source_model_class,
        trusted_target_model_class=trusted_target_model_class,
        creator_live_a1_capture_provider=creator_live_a1_capture_provider,
    )


@dataclass(frozen=True)
class _PendingSave:
    draft: FieldNoteDraft
    repository_identity: tuple[int, int]
    decision_directory_identity: tuple[int, int] | None
    field_notes_directory_identity: tuple[int, int] | None


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


class FieldNotesCompanionController(CompanionController):
    """Companion controller extended only with Field Notes Lite Capture."""

    def __init__(self, **kwargs: Any) -> None:
        self._field_note_draft: FieldNoteDraft | None = None
        self._field_note_pending: _PendingSave | None = None
        self._creator_live_a1_capture_config: (
            FieldNoteCreatorLiveA1CaptureConfig | None
        ) = None
        self._creator_live_a1_completed_run_id: str | None = None
        self._creator_live_a1_run_completion: (
            FieldNoteCreatorLiveA1RunCompletion | None
        ) = None
        self._creator_live_a1_failure_reason: str | None = None
        self._creator_live_a1_direct_write_identity: str | None = None
        self._creator_live_a1_proposal_diagnostic: (
            FieldNoteA1ProposalDiagnostic | None
        ) = None
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
            )
        super().__init__(**kwargs)

    def _active_creator_live_a1_capture(
        self,
    ) -> FieldNoteCreatorLiveA1CaptureConfig | None:
        with self._condition:
            return self._creator_live_a1_capture_config

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

    def start_run(self, task: str, *, task_mode: str = "manual") -> dict[str, Any]:
        with self._condition:
            self._require_no_active_run()
            self._clear_field_note_locked()
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
            self._creator_live_a1_capture_config = config
            self._creator_live_a1_completed_run_id = None
            self._creator_live_a1_run_completion = None
            self._creator_live_a1_failure_reason = None
            self._creator_live_a1_direct_write_identity = None
            self._creator_live_a1_proposal_diagnostic = None
        try:
            return super().start_run(task, task_mode="manual")
        except Exception:
            with self._condition:
                self._creator_live_a1_capture_config = None
            raise

    def new_run(self) -> dict[str, Any]:
        with self._condition:
            self._clear_field_note_locked()
            self._creator_live_a1_capture_config = None
            self._creator_live_a1_completed_run_id = None
            self._creator_live_a1_run_completion = None
            self._creator_live_a1_failure_reason = None
            self._creator_live_a1_direct_write_identity = None
            self._creator_live_a1_proposal_diagnostic = None
        return super().new_run()

    def select_repository(self, candidate: str | Path) -> dict[str, Any]:
        super().select_repository(candidate)
        with self._condition:
            self._clear_field_note_locked()
            self._creator_live_a1_capture_config = None
            self._creator_live_a1_completed_run_id = None
            self._creator_live_a1_run_completion = None
            self._creator_live_a1_failure_reason = None
            self._creator_live_a1_direct_write_identity = None
            self._creator_live_a1_proposal_diagnostic = None
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
        capture_failure = getattr(
            result,
            "creator_live_a1_failure_reason",
            None,
        )
        completion: FieldNoteCreatorLiveA1RunCompletion | None = None
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
                and (
                    capture_failure.startswith("A1_PROPOSAL_")
                    or capture_failure == "A1_DIRECT_WRITE_REQUESTED"
                )
            )
            if proposal_diagnostic is None:
                if capture_failure is None or proposal_failure:
                    capture_failure = "A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE"
            elif proposal_diagnostic.final_subcause is not None:
                if capture_failure is None or not proposal_failure:
                    capture_failure = proposal_diagnostic.final_subcause
                elif capture_failure != proposal_diagnostic.final_subcause:
                    capture_failure = "A1_PROPOSAL_DIAGNOSTIC_UNAVAILABLE"
            elif proposal_failure:
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
            self._creator_live_a1_run_completion = completion
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
            capture_active = self._creator_live_a1_capture_config is not None
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
                self._creator_live_a1_proposal_diagnostic = None
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

    def field_note_save(self) -> dict[str, Any]:
        with self._condition:
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

    def field_note_approval(self, choice: str) -> dict[str, Any]:
        with self._condition:
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
