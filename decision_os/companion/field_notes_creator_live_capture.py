"""Bounded Run-1 bridge from the A1 proposal tool to durable A1 closure."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import os
from pathlib import Path
import stat
import time
from typing import Callable

from decision_os.acceleration.model import (
    RepositoryIdentityError,
    git_output,
    repository_id,
)
from decision_os.acceleration.codex_adapter import CodexRuntimeIdentity
from decision_os.companion.field_notes_adapter import (
    FieldNoteA1ProposalDiagnostic,
)
from decision_os.companion.field_notes_controller import (
    FieldNoteError,
    FieldNotesCompanionController,
)
from decision_os.companion.field_notes_creator_live import (
    FieldNoteCreatorLiveA1CaptureCommitReceipt,
    FieldNoteCreatorLiveProofRuntime,
    FieldNoteCreatorLiveStageError,
    FieldNoteCreatorLiveTraceReadbackV2,
    _A1_CAPTURE_COMMIT_AUTHORITY,
)
from decision_os.companion.field_notes_model import (
    FieldNoteDraft,
    validate_compiled_markdown,
)
from decision_os.companion.field_notes_reuse import FieldNoteIdentity
from decision_os.companion.field_notes_whole_flow import (
    FieldNoteSourceRepositoryIdentity,
    FieldNoteWholeFlowTraceEvent,
    _a1_evidence_sha256,
)


class FieldNoteCreatorLiveA1CaptureBridgeError(RuntimeError):
    """The bounded A1 bridge failed and left the attempt terminal."""


def _utc_now_rfc3339() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


class FieldNoteCreatorLiveA1CaptureBridge:
    """Consume one already-open attempt and exactly one controller Run 1."""

    def __init__(
        self,
        *,
        runtime: FieldNoteCreatorLiveProofRuntime,
        controller: FieldNotesCompanionController,
        repository: Path,
        source_repository: FieldNoteSourceRepositoryIdentity,
        timeout_seconds: float = 900.0,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        utc_now: Callable[[], str] = _utc_now_rfc3339,
    ) -> None:
        if (
            not isinstance(runtime, FieldNoteCreatorLiveProofRuntime)
            or not isinstance(controller, FieldNotesCompanionController)
            or not isinstance(
                source_repository,
                FieldNoteSourceRepositoryIdentity,
            )
            or not isinstance(timeout_seconds, (int, float))
            or isinstance(timeout_seconds, bool)
            or timeout_seconds <= 0
        ):
            raise FieldNoteCreatorLiveA1CaptureBridgeError(
                "Creator-live A1 bridge configuration is invalid."
            )
        self.runtime = runtime
        self.controller = controller
        self.repository = Path(repository)
        self.source_repository = source_repository
        self.timeout_seconds = float(timeout_seconds)
        self.monotonic = monotonic
        self.sleep = sleep
        self.utc_now = utc_now
        self._dispatched = False

    def _terminal(
        self,
        reason: str,
        proposal_diagnostic: FieldNoteA1ProposalDiagnostic | None = None,
    ) -> None:
        bounded = reason if len(reason) <= 256 else reason[:256]
        try:
            self.runtime.record_stage_failure(
                "A1_CAPTURE",
                bounded,
                proposal_diagnostic=proposal_diagnostic,
            )
        except FieldNoteCreatorLiveStageError as exc:
            raise FieldNoteCreatorLiveA1CaptureBridgeError(bounded) from exc
        raise FieldNoteCreatorLiveA1CaptureBridgeError(bounded)

    def _repository_identity_matches(self) -> bool:
        try:
            root = self.repository.resolve(strict=True)
            return (
                repository_id(root) == self.source_repository.repository_id
                and git_output(root, "rev-parse", "HEAD")
                == self.source_repository.source_commit
            )
        except (OSError, RepositoryIdentityError):
            return False

    def _preflight(self) -> tuple[str, Path, CodexRuntimeIdentity, str]:
        readback = self.runtime.read_back()
        if (
            not readback.durable_readback_verified
            or not isinstance(readback, FieldNoteCreatorLiveTraceReadbackV2)
            or readback.state != "OPEN"
            or readback.terminal_proof_as_of is not None
            or readback.current_stage != "A1_CAPTURE"
            or readback.trace_event_count != 0
            or readback.run_2 is not None
            or readback.source_repository != self.source_repository
            or readback.runtime != readback.run_1.runtime
        ):
            self._terminal("A1_ATTEMPT_NOT_OPEN")
        snapshot = self.controller.snapshot()
        selected = snapshot.get("repository")
        try:
            root = self.repository.resolve(strict=True)
            selected_root = Path(selected["path"]).resolve(strict=True)
        except (KeyError, OSError, TypeError):
            self._terminal("A1_REPOSITORY_IDENTITY_MISMATCH")
        if selected_root != root or not self._repository_identity_matches():
            self._terminal("A1_REPOSITORY_IDENTITY_MISMATCH")
        return (
            readback.run_1.run_id,
            root,
            readback.runtime,
            readback.proof_attempt_id,
        )

    def _wait_for_run(self) -> None:
        deadline = self.monotonic() + self.timeout_seconds
        while True:
            state = self.controller.snapshot()["run"]["state"]
            if state != "running":
                return
            if self.monotonic() >= deadline:
                self._terminal("A1_RUN_TIMEOUT")
            self.sleep(0.05)

    @staticmethod
    def _fixed_target(root: Path, draft: FieldNoteDraft) -> Path:
        parts = Path(draft.relative_path).parts
        if (
            len(parts) != 3
            or parts[:2] != (".decision-os", "field-notes")
        ):
            raise FieldNoteCreatorLiveA1CaptureBridgeError(
                "A1_TARGET_OUTSIDE_FIXED_ROOT"
            )
        return root.joinpath(*parts)

    @staticmethod
    def _require_unoccupied_target(target: Path) -> None:
        for parent in (target.parent.parent, target.parent):
            if parent.exists() or parent.is_symlink():
                linked = parent.lstat()
                if stat.S_ISLNK(linked.st_mode) or not stat.S_ISDIR(
                    linked.st_mode
                ):
                    raise FieldNoteCreatorLiveA1CaptureBridgeError(
                        "A1_TARGET_PARENT_UNSAFE"
                    )
        if target.exists() or target.is_symlink():
            raise FieldNoteCreatorLiveA1CaptureBridgeError(
                "A1_TARGET_PREEXISTING"
            )
        if target.parent.exists() and any(
            child.name.casefold() == target.name.casefold()
            for child in target.parent.iterdir()
        ):
            raise FieldNoteCreatorLiveA1CaptureBridgeError(
                "A1_TARGET_COLLISION"
            )

    @staticmethod
    def _exact_read_back(target: Path) -> bytes:
        descriptor: int | None = None
        try:
            linked = target.lstat()
            descriptor = os.open(
                target,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
            )
            opened = os.fstat(descriptor)
            if (
                stat.S_ISLNK(linked.st_mode)
                or not stat.S_ISREG(linked.st_mode)
                or not stat.S_ISREG(opened.st_mode)
                or (linked.st_dev, linked.st_ino)
                != (opened.st_dev, opened.st_ino)
            ):
                raise OSError("A1 target identity changed.")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 65_536)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def _capture_failure_reason(self, exc: Exception) -> str:
        value = str(exc).strip()
        if value.startswith("A1_"):
            return value
        return "A1_CAPTURE_FAILED"

    @staticmethod
    def _is_proposal_failure(reason: str | None) -> bool:
        return bool(
            isinstance(reason, str)
            and (
                reason.startswith("A1_PROPOSAL_")
                or reason == "A1_DIRECT_WRITE_REQUESTED"
            )
        )

    def capture(self, task: str) -> FieldNoteWholeFlowTraceEvent:
        """Dispatch one Run 1, save its exact proposal, then emit one A1."""

        if self._dispatched:
            self._terminal("A1_RUN_ALREADY_DISPATCHED")
        run_id, root, expected_runtime, proof_attempt_id = self._preflight()
        self._dispatched = True
        try:
            self.controller.start_creator_live_a1_capture(
                task,
                run_id=run_id,
                expected_runtime_identity=expected_runtime,
            )
            self._wait_for_run()
            try:
                failure_reason = (
                    self.controller.creator_live_a1_failure_reason(
                        expected_run_id=run_id
                    )
                )
            except FieldNoteError as exc:
                self._terminal(self._capture_failure_reason(exc))
            if (
                failure_reason is not None
                and not self._is_proposal_failure(failure_reason)
            ):
                self._terminal(failure_reason)
            try:
                proposal_diagnostic = (
                    self.controller.creator_live_a1_proposal_diagnostic(
                        expected_run_id=run_id
                    )
                )
            except FieldNoteError as exc:
                self._terminal(self._capture_failure_reason(exc))
            proposal_diagnostic = FieldNoteA1ProposalDiagnostic.from_dict(
                proposal_diagnostic.as_dict()
            )
            if proposal_diagnostic.final_subcause is not None:
                reason = proposal_diagnostic.final_subcause
                if (
                    reason == "A1_DIRECT_WRITE_REQUESTED"
                    and proposal_diagnostic.direct_write_identity is not None
                ):
                    reason = (
                        f"{reason}:"
                        f"{proposal_diagnostic.direct_write_identity}"
                    )
                self._terminal(reason, proposal_diagnostic)
            if failure_reason is not None:
                self._terminal(failure_reason)
            draft = self.controller.creator_live_a1_capture_candidate()
            completion = self.controller.creator_live_a1_run_completion()
            validate_compiled_markdown(draft.markdown)
            task_sha256 = hashlib.sha256(
                task.strip().encode("utf-8")
            ).hexdigest()
            if (
                draft.source_run_id != run_id
                or hashlib.sha256(draft.markdown).hexdigest() != draft.sha256
            ):
                self._terminal("A1_NOTE_IDENTITY_MISMATCH")
            if completion.run_id != run_id:
                self._terminal("A1_CAPTURE_IDENTITY_MISMATCH")
            if completion.task_sha256 != task_sha256:
                self._terminal("A1_TASK_IDENTITY_MISMATCH")
            if completion.actual_runtime_identity != expected_runtime:
                self._terminal("A1_ACTUAL_RUNTIME_IDENTITY_MISMATCH")
            target = self._fixed_target(root, draft)
            self._require_unoccupied_target(target)
            if not self._repository_identity_matches():
                self._terminal("A1_REPOSITORY_IDENTITY_MISMATCH")

            approval = self.controller.field_note_save()
            surface = approval["run"]["field_note"]
            request = surface["approval"]
            if (
                surface.get("state") != "approval"
                or request.get("action") != "CREATE"
                or request.get("path") != draft.relative_path
                or request.get("content_sha256") != draft.sha256
                or request.get("precondition") != "MUST_NOT_EXIST"
                or request.get("approval_scope") != "THIS ONE FILE ONLY"
            ):
                self._terminal("A1_SAVE_APPROVAL_IDENTITY_MISMATCH")

            saved = self.controller.field_note_approval("allow_once")
            if saved["run"]["field_note"] != {
                "state": "saved",
                "path": draft.relative_path,
            }:
                self._terminal("A1_CONTROLLER_SAVE_NOT_CONFIRMED")
            try:
                note_bytes = self._exact_read_back(target)
            except OSError:
                self._terminal("A1_NOTE_READ_BACK_FAILED")
            if (
                note_bytes != draft.markdown
                or len(note_bytes) != len(draft.markdown)
                or hashlib.sha256(note_bytes).hexdigest() != draft.sha256
            ):
                self._terminal("A1_NOTE_READ_BACK_MISMATCH")
            if not self._repository_identity_matches():
                self._terminal("A1_REPOSITORY_IDENTITY_MISMATCH")

            note = FieldNoteIdentity(
                note_path=draft.relative_path,
                field_note_id=draft.field_note_id,
                note_sha256=draft.sha256,
                origin_run_id=draft.source_run_id,
            )
            commit = FieldNoteCreatorLiveA1CaptureCommitReceipt._issue(
                authority=_A1_CAPTURE_COMMIT_AUTHORITY,
                proof_attempt_id=proof_attempt_id,
                run_id=run_id,
                task_sha256=task_sha256,
                actual_runtime_identity=(
                    completion.actual_runtime_identity
                ),
                source_repository=self.source_repository,
                note=note,
                note_byte_count=len(note_bytes),
                draft_evidence_sha256=_a1_evidence_sha256(draft),
                draft_created_at=draft.created_at,
                save_as_of=self.utc_now(),
            )
            event = self.runtime.record_a1_capture(
                draft,
                capture_commit=commit,
                expected_task_sha256=task_sha256,
                actual_runtime_identity=(
                    completion.actual_runtime_identity
                ),
                observed_at=self.utc_now(),
            )
            closed = self.runtime.read_back()
            if (
                not closed.durable_readback_verified
                or closed.state != "OPEN"
                or closed.current_stage != "A2_RECONNECT"
                or closed.trace_event_count != 1
                or closed.captured_note != note
                or closed.captured_note_byte_count != len(note_bytes)
                or closed.a1_capture_commit != commit
            ):
                self._terminal("A1_DURABLE_CLOSURE_MISMATCH")
            return event
        except FieldNoteCreatorLiveA1CaptureBridgeError as exc:
            if self.runtime.read_back().state == "OPEN":
                self._terminal(self._capture_failure_reason(exc))
            raise
        except FieldNoteCreatorLiveStageError:
            raise
        except Exception as exc:
            self._terminal(self._capture_failure_reason(exc))


__all__ = [
    "FieldNoteCreatorLiveA1CaptureBridge",
    "FieldNoteCreatorLiveA1CaptureBridgeError",
]
