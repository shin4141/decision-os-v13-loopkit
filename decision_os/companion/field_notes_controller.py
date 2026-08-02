"""Field Notes Lite v0.1 Capture controller."""

from __future__ import annotations

from dataclasses import dataclass
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
    CodexRunResult,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.companion.controller import CompanionController, CompanionError
from decision_os.companion.field_notes_adapter import (
    FieldNoteCodexRunResult,
    FieldNotesCodexAdapter,
)
from decision_os.companion.field_notes_model import FieldNoteDraft, compile_draft


class FieldNoteError(CompanionError):
    """A bounded Field Notes operation failed closed."""


def _field_notes_adapter_factory(
    engine: AccelerationEngine,
    approval_provider: Any,
    lifecycle_sink: Any,
) -> FieldNotesCodexAdapter:
    return FieldNotesCodexAdapter(
        engine,
        input_func=lambda: None,
        stdout=io.StringIO(),
        approval_provider=approval_provider,
        lifecycle_sink=lifecycle_sink,
    )


@dataclass(frozen=True)
class _PendingSave:
    draft: FieldNoteDraft


class FieldNotesCompanionController(CompanionController):
    """Companion controller extended only with Field Notes Lite Capture."""

    def __init__(self, **kwargs: Any) -> None:
        self._field_note_draft: FieldNoteDraft | None = None
        self._field_note_pending: _PendingSave | None = None
        kwargs.setdefault("adapter_factory", _field_notes_adapter_factory)
        super().__init__(**kwargs)

    @staticmethod
    def _empty_run() -> dict[str, Any]:
        run = CompanionController._empty_run()
        run["field_note"] = {"state": "none"}
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

    def new_run(self) -> dict[str, Any]:
        with self._condition:
            self._clear_field_note_locked()
        return super().new_run()

    def select_repository(self, candidate: str | Path) -> dict[str, Any]:
        super().select_repository(candidate)
        with self._condition:
            self._clear_field_note_locked()
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
        if (
            draft.source_run_id != result.run_id
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

    def _complete_run(
        self,
        repository: Path,
        result: CodexRunResult,
    ) -> None:
        super()._complete_run(repository, result)
        draft = self._eligible_draft(result)
        with self._condition:
            if draft is None:
                self._clear_field_note_locked()
            else:
                self._field_note_draft = draft
                self._field_note_pending = None
                self._run["field_note"] = draft.public_candidate()
            self._condition.notify_all()

    def _fail_run(self, repository: Path, exc: Exception) -> None:
        super()._fail_run(repository, exc)
        with self._condition:
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
            target = repository.joinpath(*current.relative_path.split("/"))
            try:
                target.parent.relative_to(repository)
            except ValueError as exc:
                raise FieldNoteError(
                    "Field Note path escapes the repository."
                ) from exc
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
            self._field_note_draft = draft
            self._field_note_pending = _PendingSave(draft)
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
    def _ensure_safe_directory(repository: Path, directory: Path) -> None:
        try:
            parts = directory.relative_to(repository).parts
        except ValueError as exc:
            raise FieldNoteError(
                "Field Note directory escapes the repository."
            ) from exc
        current = repository
        for part in parts:
            current = current / part
            if current.exists():
                try:
                    info = current.lstat()
                except OSError as exc:
                    raise FieldNoteError(
                        "Field Note parent path cannot be inspected safely."
                    ) from exc
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                    raise FieldNoteError(
                        "Field Note parent path is not a safe directory."
                    )
                continue
            try:
                os.mkdir(current, 0o700)
            except OSError as exc:
                raise FieldNoteError(
                    "Field Note directory could not be materialized safely."
                ) from exc

    def _write_pending(self, pending: _PendingSave) -> None:
        repository = self._require_repository().resolve(strict=True)
        target = repository.joinpath(*pending.draft.relative_path.split("/"))
        try:
            target.relative_to(repository)
        except ValueError as exc:
            raise FieldNoteError("Field Note path escapes the repository.") from exc
        self._ensure_safe_directory(repository, target.parent)
        if (
            target.exists()
            or target.is_symlink()
            or self._case_collision(target.parent, target.name)
        ):
            raise FieldNoteError(
                "Field Note create-new precondition failed."
            )
        opened_identity: tuple[int, int] | None = None
        try:
            descriptor = os.open(
                target,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
        except OSError as exc:
            raise FieldNoteError(
                "Field Note create-new precondition failed."
            ) from exc
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise FieldNoteError(
                    "Field Note target is not a safe regular file."
                )
            opened_identity = (opened.st_dev, opened.st_ino)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(pending.draft.markdown)
                stream.flush()
                os.fsync(stream.fileno())
            observed_info = target.lstat()
            if (
                stat.S_ISLNK(observed_info.st_mode)
                or not stat.S_ISREG(observed_info.st_mode)
                or (observed_info.st_dev, observed_info.st_ino)
                != opened_identity
            ):
                raise FieldNoteError(
                    "Field Note post-write path identity did not match."
                )
            observed = target.read_bytes()
            readback_info = target.lstat()
            if (
                stat.S_ISLNK(readback_info.st_mode)
                or not stat.S_ISREG(readback_info.st_mode)
                or (readback_info.st_dev, readback_info.st_ino)
                != opened_identity
                or observed != pending.draft.markdown
                or hashlib.sha256(observed).hexdigest()
                != pending.draft.sha256
            ):
                raise FieldNoteError(
                    "Field Note readback identity did not match."
                )
        except Exception as exc:
            try:
                current = target.lstat()
                if (
                    opened_identity is not None
                    and stat.S_ISREG(current.st_mode)
                    and (current.st_dev, current.st_ino) == opened_identity
                ):
                    target.unlink()
            except OSError:
                pass
            if isinstance(exc, FieldNoteError):
                raise
            raise FieldNoteError(
                "Field Note write or readback failed safely."
            ) from exc

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
