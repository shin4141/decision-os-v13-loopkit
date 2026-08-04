"""Exact-lineage creator-live A2 reconnect preparation and bridge."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Callable

from decision_os.acceleration.codex_adapter import CodexRuntimeIdentity
from decision_os.acceleration.model import (
    RepositoryIdentityError,
    git_output,
    repository_id,
)
from decision_os.companion.field_notes_reconnect import (
    FieldNoteExactReadError,
    FieldNoteReconnectPlan,
    FieldNoteReconnectReceipt,
    read_exact_field_note,
)
from decision_os.companion.field_notes_reuse import FieldNoteIdentity
from decision_os.companion.field_notes_whole_flow import (
    FieldNoteSourceRepositoryIdentity,
    FieldNoteWholeFlowTraceEvent,
)


A2_TARGET_FAILURE_CODES = frozenset(
    {
        "A2_TARGET_MISSING",
        "A2_TARGET_INVALID",
        "A2_TARGET_PROOF_MISMATCH",
        "A2_TARGET_RUN_1_MISMATCH",
        "A2_TARGET_RUN_2_MISMATCH",
        "A2_TARGET_NOTE_ID_MISMATCH",
        "A2_TARGET_SOURCE_RUN_MISMATCH",
        "A2_TARGET_PATH_INVALID",
        "A2_TARGET_NOTE_MISSING",
        "A2_TARGET_NOTE_INVALID",
        "A2_TARGET_SHA256_MISMATCH",
        "A2_TARGET_BYTE_COUNT_MISMATCH",
        "A2_TARGET_REPOSITORY_MISMATCH",
        "A2_TARGET_COMMIT_MISMATCH",
        "A2_TARGET_CHANGED_DURING_READ",
    }
)
_A2_TARGET_AUTHORITY = object()


class FieldNoteCreatorLiveA2ReconnectError(RuntimeError):
    """An exact A2 target failed closed with a bounded diagnostic code."""

    def __init__(self, code: str) -> None:
        if code not in A2_TARGET_FAILURE_CODES:
            raise ValueError("Creator-live A2 failure code is invalid.")
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, init=False)
class FieldNoteCreatorLiveA2ReconnectTarget:
    """Immutable exact target issued only from verified durable read-back."""

    proof_attempt_id: str
    run_1_id: str
    run_2_id: str
    field_note_id: str
    note_relative_path: str
    note_sha256: str
    note_byte_count: int
    source_repository_id: str
    source_commit: str
    expected_runtime_identity: CodexRuntimeIdentity

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")

    @classmethod
    def _issue(
        cls,
        *,
        authority: object,
        proof_attempt_id: str,
        run_1_id: str,
        run_2_id: str,
        field_note_id: str,
        note_relative_path: str,
        note_sha256: str,
        note_byte_count: int,
        source_repository_id: str,
        source_commit: str,
        expected_runtime_identity: CodexRuntimeIdentity,
    ) -> FieldNoteCreatorLiveA2ReconnectTarget:
        if authority is not _A2_TARGET_AUTHORITY:
            raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
        bounded = (
            proof_attempt_id,
            run_1_id,
            run_2_id,
            field_note_id,
            note_relative_path,
            source_repository_id,
            source_commit,
        )
        if (
            any(
                not isinstance(value, str)
                or not value.strip()
                or len(value) > 1024
                or "\x00" in value
                for value in bounded
            )
            or not isinstance(note_sha256, str)
            or len(note_sha256) != 64
            or any(character not in "0123456789abcdef" for character in note_sha256)
            or type(note_byte_count) is not int
            or note_byte_count <= 0
            or not isinstance(expected_runtime_identity, CodexRuntimeIdentity)
        ):
            raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
        value = object.__new__(cls)
        fields = {
            "proof_attempt_id": proof_attempt_id,
            "run_1_id": run_1_id,
            "run_2_id": run_2_id,
            "field_note_id": field_note_id,
            "note_relative_path": note_relative_path,
            "note_sha256": note_sha256,
            "note_byte_count": note_byte_count,
            "source_repository_id": source_repository_id,
            "source_commit": source_commit,
            "expected_runtime_identity": expected_runtime_identity,
        }
        for name, item in fields.items():
            object.__setattr__(value, name, item)
        return value


@dataclass(frozen=True)
class FieldNoteCreatorLiveA2Preparation:
    """Exact safe-read bytes and the existing reconnect plan projection."""

    target: FieldNoteCreatorLiveA2ReconnectTarget
    plan: FieldNoteReconnectPlan
    note_bytes: bytes


def creator_live_a2_target_from_readback(
    readback: Any,
) -> FieldNoteCreatorLiveA2ReconnectTarget:
    """Issue one target from the exact verified post-open_run_2 read-back."""

    from decision_os.companion.field_notes_creator_live import (
        FieldNoteCreatorLiveA1CaptureCommitReceipt,
        FieldNoteCreatorLiveTraceReadback,
    )

    if not isinstance(readback, FieldNoteCreatorLiveTraceReadback):
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
    if (
        readback.durable_readback_verified is not True
        or readback.state != "OPEN"
        or readback.current_stage != "A2_RECONNECT"
        or readback.trace_event_count != 1
    ):
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
    note = readback.captured_note
    commit = readback.a1_capture_commit
    run_2 = readback.run_2
    if note is None or commit is None or run_2 is None:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_MISSING")
    if not isinstance(note, FieldNoteIdentity) or not isinstance(
        commit,
        FieldNoteCreatorLiveA1CaptureCommitReceipt,
    ):
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
    if (
        readback.proof_attempt_id != readback.run_1.proof_attempt_id
        or readback.proof_attempt_id != run_2.proof_attempt_id
        or commit.proof_attempt_id != readback.proof_attempt_id
    ):
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_PROOF_MISMATCH")
    if commit.run_id != readback.run_1.run_id:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_RUN_1_MISMATCH")
    if run_2.run_id == readback.run_1.run_id:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_RUN_2_MISMATCH")
    if commit.note.field_note_id != note.field_note_id:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_NOTE_ID_MISMATCH")
    if (
        note.origin_run_id != readback.run_1.run_id
        or commit.note.origin_run_id != readback.run_1.run_id
    ):
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_SOURCE_RUN_MISMATCH")
    if commit.note != note:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
    if (
        readback.captured_note_byte_count != commit.note_byte_count
        or type(readback.captured_note_byte_count) is not int
        or readback.captured_note_byte_count <= 0
    ):
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
    if (
        commit.source_repository != readback.source_repository
        or readback.run_1.repository != readback.source_repository
        or run_2.repository != readback.source_repository
    ):
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_REPOSITORY_MISMATCH"
        )
    if (
        commit.actual_runtime_identity != readback.runtime
        or readback.run_1.runtime != readback.runtime
        or run_2.runtime != readback.runtime
    ):
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
    return FieldNoteCreatorLiveA2ReconnectTarget._issue(
        authority=_A2_TARGET_AUTHORITY,
        proof_attempt_id=readback.proof_attempt_id,
        run_1_id=readback.run_1.run_id,
        run_2_id=run_2.run_id,
        field_note_id=note.field_note_id,
        note_relative_path=note.note_path,
        note_sha256=note.note_sha256,
        note_byte_count=readback.captured_note_byte_count,
        source_repository_id=readback.source_repository.repository_id,
        source_commit=readback.source_repository.source_commit,
        expected_runtime_identity=readback.runtime,
    )


def _require_target_readback_binding(target: Any, readback: Any) -> None:
    note = readback.captured_note
    run_2 = readback.run_2
    if not isinstance(target, FieldNoteCreatorLiveA2ReconnectTarget):
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
    if note is None or run_2 is None:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_MISSING")
    if target.proof_attempt_id != readback.proof_attempt_id:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_PROOF_MISMATCH")
    if target.run_1_id != readback.run_1.run_id:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_RUN_1_MISMATCH")
    if target.run_2_id != run_2.run_id:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_RUN_2_MISMATCH")
    if target.field_note_id != note.field_note_id:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_NOTE_ID_MISMATCH")
    if target.note_relative_path != note.note_path:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_PATH_INVALID")
    if target.run_1_id != note.origin_run_id:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_SOURCE_RUN_MISMATCH"
        )
    if target.note_sha256 != note.note_sha256:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_SHA256_MISMATCH"
        )
    if target.note_byte_count != readback.captured_note_byte_count:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_BYTE_COUNT_MISMATCH"
        )
    if target.source_repository_id != readback.source_repository.repository_id:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_REPOSITORY_MISMATCH"
        )
    if target.source_commit != readback.source_repository.source_commit:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_COMMIT_MISMATCH")
    if target.expected_runtime_identity != readback.runtime:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")


def _repository_identity(root: Path) -> tuple[str, str]:
    try:
        return repository_id(root), git_output(root, "rev-parse", "HEAD")
    except (OSError, RepositoryIdentityError) as exc:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_REPOSITORY_MISMATCH"
        ) from exc


def _map_exact_read_failure(reason: str) -> str:
    if reason == "exact_note_missing":
        return "A2_TARGET_NOTE_MISSING"
    if reason == "exact_changed_during_read":
        return "A2_TARGET_CHANGED_DURING_READ"
    if reason in {
        "exact_path_invalid",
        "exact_entry_unsafe",
        "repository_root_unsafe",
        "decision_directory_unsafe",
        "field_notes_directory_unsafe",
    }:
        return "A2_TARGET_PATH_INVALID"
    return "A2_TARGET_NOTE_INVALID"


def prepare_creator_live_a2_reconnect(
    repository: Path,
    target: FieldNoteCreatorLiveA2ReconnectTarget | None,
) -> FieldNoteCreatorLiveA2Preparation:
    """Prepare only the durable target path; never scan, score, or fall back."""

    if target is None:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_MISSING")
    if not isinstance(target, FieldNoteCreatorLiveA2ReconnectTarget):
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
    root = Path(repository)
    observed_repository, observed_commit = _repository_identity(root)
    if observed_repository != target.source_repository_id:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_REPOSITORY_MISMATCH"
        )
    if observed_commit != target.source_commit:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_COMMIT_MISMATCH")
    try:
        exact = read_exact_field_note(root, target.note_relative_path)
    except FieldNoteExactReadError as exc:
        raise FieldNoteCreatorLiveA2ReconnectError(
            _map_exact_read_failure(exc.reason)
        ) from exc
    repository_after, commit_after = _repository_identity(root)
    if repository_after != target.source_repository_id:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_REPOSITORY_MISMATCH"
        )
    if commit_after != target.source_commit:
        raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_COMMIT_MISMATCH")
    if exact.field_note_id != target.field_note_id:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_NOTE_ID_MISMATCH"
        )
    if exact.source_run_id != target.run_1_id:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_SOURCE_RUN_MISMATCH"
        )
    if exact.note_sha256 != target.note_sha256:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_SHA256_MISMATCH"
        )
    if len(exact.note_bytes) != target.note_byte_count:
        raise FieldNoteCreatorLiveA2ReconnectError(
            "A2_TARGET_BYTE_COUNT_MISMATCH"
        )
    receipt = FieldNoteReconnectReceipt(
        run_id=target.run_2_id,
        state="SELECTED",
        failure_reason=None,
        metadata_entries_seen=1,
        metadata_candidate_files_seen=1,
        metadata_files_valid=1,
        metadata_bytes_read=exact.metadata_byte_count,
        selected_field_note_path=exact.relative_path,
        selected_field_note_id=exact.field_note_id,
        selected_metadata_sha256=exact.metadata_sha256,
        selected_full_note_sha256=exact.note_sha256,
        full_note_bytes_read=len(exact.note_bytes),
        full_notes_injected=0,
        ordinary_distinct_paths_consumed=0,
    )
    return FieldNoteCreatorLiveA2Preparation(
        target=target,
        plan=FieldNoteReconnectPlan(receipt=receipt, envelope=exact.envelope),
        note_bytes=exact.note_bytes,
    )


class FieldNoteCreatorLiveA2ReconnectBridge:
    """Dispatch Run 2 through exact preparation and emit the existing A2."""

    def __init__(
        self,
        *,
        runtime: Any,
        controller: Any,
        repository: Path,
        source_repository: FieldNoteSourceRepositoryIdentity,
        timeout_seconds: float = 900.0,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        from decision_os.companion.field_notes_controller import (
            FieldNotesCompanionController,
        )
        from decision_os.companion.field_notes_creator_live import (
            FieldNoteCreatorLiveProofRuntime,
        )

        if (
            not isinstance(runtime, FieldNoteCreatorLiveProofRuntime)
            or not isinstance(controller, FieldNotesCompanionController)
            or not isinstance(source_repository, FieldNoteSourceRepositoryIdentity)
            or not isinstance(timeout_seconds, (int, float))
            or isinstance(timeout_seconds, bool)
            or timeout_seconds <= 0
        ):
            raise FieldNoteCreatorLiveA2ReconnectError("A2_TARGET_INVALID")
        self.runtime = runtime
        self.controller = controller
        self.repository = Path(repository)
        self.source_repository = source_repository
        self.timeout_seconds = float(timeout_seconds)
        self.monotonic = monotonic
        self.sleep = sleep
        self._dispatched = False

    def _terminal(self, code: str) -> None:
        from decision_os.companion.field_notes_creator_live import (
            FieldNoteCreatorLiveStageError,
        )

        if code not in A2_TARGET_FAILURE_CODES:
            code = "A2_TARGET_INVALID"
        try:
            self.runtime.record_stage_failure("A2_RECONNECT", code)
        except FieldNoteCreatorLiveStageError as exc:
            raise FieldNoteCreatorLiveA2ReconnectError(code) from exc
        raise FieldNoteCreatorLiveA2ReconnectError(code)

    def _wait_for_run(self) -> None:
        deadline = self.monotonic() + self.timeout_seconds
        while self.controller.snapshot()["run"]["state"] == "running":
            if self.monotonic() >= deadline:
                self._terminal("A2_TARGET_INVALID")
            self.sleep(0.05)

    def reconnect(self, task: str) -> FieldNoteWholeFlowTraceEvent:
        """Execute exactly one already-open Run 2 and durably close A2."""

        if self._dispatched:
            self._terminal("A2_TARGET_INVALID")
        try:
            readback = self.runtime.read_back()
            target = creator_live_a2_target_from_readback(readback)
            _require_target_readback_binding(target, readback)
            if readback.source_repository != self.source_repository:
                self._terminal("A2_TARGET_REPOSITORY_MISMATCH")
            snapshot = self.controller.snapshot()
            selected = snapshot.get("repository")
            try:
                root = self.repository.resolve(strict=True)
                selected_root = Path(selected["path"]).resolve(strict=True)
            except (KeyError, OSError, TypeError):
                self._terminal("A2_TARGET_REPOSITORY_MISMATCH")
            if selected_root != root:
                self._terminal("A2_TARGET_REPOSITORY_MISMATCH")
            self._dispatched = True
            self.controller.start_creator_live_a2_reconnect(task, target=target)
            self._wait_for_run()
            failure = self.controller.creator_live_a2_failure_reason(
                expected_run_id=target.run_2_id
            )
            if failure is not None:
                self._terminal(failure)
            completion = self.controller.creator_live_a2_run_completion(
                expected_run_id=target.run_2_id
            )
            if completion.actual_runtime_identity != target.expected_runtime_identity:
                self._terminal("A2_TARGET_INVALID")
            prepared = prepare_creator_live_a2_reconnect(root, target)
            note = FieldNoteIdentity(
                note_path=target.note_relative_path,
                field_note_id=target.field_note_id,
                note_sha256=target.note_sha256,
                origin_run_id=target.run_1_id,
            )
            event = self.runtime.record_a2_reconnect(
                completion.reconnect_receipt,
                note=note,
                note_bytes=prepared.note_bytes,
            )
            closed = self.runtime.read_back()
            if (
                not closed.durable_readback_verified
                or closed.state != "OPEN"
                or closed.current_stage != "A3_REUSE"
                or closed.trace_event_count != 2
                or closed.events[-1] != event
            ):
                self._terminal("A2_TARGET_INVALID")
            return event
        except FieldNoteCreatorLiveA2ReconnectError as exc:
            if self.runtime.read_back().state == "OPEN":
                self._terminal(exc.code)
            raise
        except Exception:
            if self.runtime.read_back().state == "OPEN":
                self._terminal("A2_TARGET_INVALID")
            raise


__all__ = [
    "A2_TARGET_FAILURE_CODES",
    "FieldNoteCreatorLiveA2Preparation",
    "FieldNoteCreatorLiveA2ReconnectBridge",
    "FieldNoteCreatorLiveA2ReconnectError",
    "FieldNoteCreatorLiveA2ReconnectTarget",
    "creator_live_a2_target_from_readback",
    "prepare_creator_live_a2_reconnect",
]
