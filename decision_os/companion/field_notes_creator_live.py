"""Runtime-owned, append-only A7 creator-live proof trace acquisition."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any, Literal

from decision_os.acceleration.codex_adapter import CodexRuntimeIdentity
from decision_os.companion.field_notes_adapter import (
    FieldNoteA1ProposalDiagnostic,
)
from decision_os.companion.field_notes_maturity_commit import (
    FieldNoteMaturityCommitResult,
)
from decision_os.companion.field_notes_maturity_ledger import (
    GENESIS_EVENT_SHA256,
    FieldNoteMaturityLedgerSnapshot,
)
from decision_os.companion.field_notes_maturity_review import (
    FieldNoteMaturityReviewPacket,
)
from decision_os.companion.field_notes_model import (
    FieldNoteDraft,
    canonical_json,
    validate_compiled_markdown,
)
from decision_os.companion.field_notes_reconnect import (
    FieldNoteReconnectReceipt,
)
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteReuseReceipt,
    PromotionPolicyBoundary,
)
from decision_os.companion.field_notes_whole_flow import (
    TRACE_GENESIS_SHA256,
    WHOLE_FLOW_TRACE_SCHEMA,
    FieldNoteCreatorLiveRuntimeProvenance,
    FieldNoteCreatorLiveAttempt,
    FieldNoteSourceRepositoryIdentity,
    FieldNoteWholeFlowAttempt,
    FieldNoteWholeFlowRunIdentity,
    FieldNoteWholeFlowTraceEvent,
    FieldNoteWholeFlowValidationError,
    RepairAction,
    TraceStage,
    WholeFlowBoundary,
    _RUNTIME_PROVENANCE_AUTHORITY,
    _a1_evidence_sha256,
    _a2_receipt_sha256,
    _a3_receipt_sha256,
    _a5_confirmation_sha256,
    _a6_packet_sha256,
    _canonical_sha256,
    _event_receipt_sha256,
    _event_sha256,
    _expected_reuse_event_id,
    _parse_time,
    _runtime_as_dict,
    _sha256_bytes,
)


CREATOR_LIVE_JOURNAL_SCHEMA = (
    "decision-os.field-note-creator-live-proof-journal.v0.1"
)
CREATOR_LIVE_RECORD_SCHEMA = (
    "decision-os.field-note-creator-live-proof-record.v0.1"
)
CREATOR_LIVE_READBACK_SCHEMA = (
    "decision-os.field-note-creator-live-proof-readback.v0.1"
)
CREATOR_LIVE_ANCHOR_SCHEMA = (
    "decision-os.field-note-creator-live-proof-anchor.v0.1"
)
CREATOR_LIVE_JOURNAL_FILENAME = "creator-live-proof-v0.1.jsonl"
CREATOR_LIVE_ANCHOR_FILENAME = "creator-live-proof-v0.1.anchor.jsonl"
CREATOR_LIVE_JOURNAL_SCHEMA_V2 = (
    "decision-os.field-note-creator-live-proof-journal.v0.2"
)
CREATOR_LIVE_RECORD_SCHEMA_V2 = (
    "decision-os.field-note-creator-live-proof-record.v0.2"
)
CREATOR_LIVE_READBACK_SCHEMA_V2 = (
    "decision-os.field-note-creator-live-proof-readback.v0.2"
)
CREATOR_LIVE_ANCHOR_SCHEMA_V2 = (
    "decision-os.field-note-creator-live-proof-anchor.v0.2"
)
CREATOR_LIVE_JOURNAL_FILENAME_V2 = "creator-live-proof-v0.2.jsonl"
CREATOR_LIVE_ANCHOR_FILENAME_V2 = "creator-live-proof-v0.2.anchor.jsonl"
CREATOR_LIVE_JOURNAL_SCHEMA_V3 = (
    "decision-os.field-note-creator-live-proof-journal.v0.3"
)
CREATOR_LIVE_RECORD_SCHEMA_V3 = (
    "decision-os.field-note-creator-live-proof-record.v0.3"
)
CREATOR_LIVE_READBACK_SCHEMA_V3 = (
    "decision-os.field-note-creator-live-proof-readback.v0.3"
)
CREATOR_LIVE_ANCHOR_SCHEMA_V3 = (
    "decision-os.field-note-creator-live-proof-anchor.v0.3"
)
CREATOR_LIVE_JOURNAL_FILENAME_V3 = "creator-live-proof-v0.3.jsonl"
CREATOR_LIVE_ANCHOR_FILENAME_V3 = "creator-live-proof-v0.3.anchor.jsonl"
TERMINAL_PROJECTION_BINDING_SCHEMA = (
    "decision-os.field-note-creator-live-terminal-projection-binding.v0.1"
)
RUN_2_OUTPUT_IDENTITY_SCHEMA = (
    "decision-os.field-note-creator-live-run-2-output-identity.v0.1"
)
OUTPUT_ARTIFACT_IDENTITY_SCHEMA = (
    "decision-os.field-note-creator-live-output-artifact-identity.v0.1"
)
A3_COMPILER_AUDIT_SCHEMA = (
    "decision-os.field-note-creator-live-a3-compiler-audit.v0.1"
)
A3_COMPILER_VERSION = (
    "decision-os.creator-live-a3-exact-output-artifact-compiler.v0.1"
)
A3_COMPILER_BRANCH = "EXACT_UTF8_NON_WHOLE_UNIQUE_SOURCE_UNIQUE_OUTPUT"
A1_CAPTURE_COMMIT_SCHEMA = (
    "decision-os.field-note-creator-live-a1-capture-commit.v0.1"
)
JOURNAL_GENESIS_SHA256 = "0" * 64
ANCHOR_GENESIS_SHA256 = "0" * 64

CreatorLiveAttemptState = Literal[
    "OPEN",
    "NOT_READY",
    "FAILED",
    "TRACE_COMPLETE",
]
JournalRecordKind = Literal[
    "ATTEMPT_OPENED",
    "RUN_1_OPENED",
    "RUN_2_OPENED",
    "RUN_2_OUTPUT_IDENTITY_RECORDED",
    "A3_COMPILER_AUDIT_RECORDED",
    "CHECKPOINT",
    "ATTEMPT_FAILED",
    "TRACE_COMPLETED",
]

_STAGES: tuple[TraceStage, ...] = (
    "A1_CAPTURE",
    "A2_RECONNECT",
    "A3_REUSE",
    "A4_DURABILITY",
    "A5_CONFIRMATION",
    "A6_REVIEW",
)
_READBACK_AUTHORITY = object()
_A1_CAPTURE_COMMIT_AUTHORITY = object()


def _identity_text(value: Any, label: str, *, maximum: int = 512) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
        or "\x00" in value
        or "\n" in value
        or "\r" in value
    ):
        raise FieldNoteCreatorLiveValidationError(f"{label} is invalid.")
    return value


def _identity_sha256(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise FieldNoteCreatorLiveValidationError(f"{label} is invalid.")
    return value


def _identity_count(value: Any, label: str, *, positive: bool = False) -> int:
    if (
        type(value) is not int
        or value < (1 if positive else 0)
    ):
        raise FieldNoteCreatorLiveValidationError(f"{label} is invalid.")
    return value


@dataclass(frozen=True)
class FieldNoteCreatorLiveContractIdentity:
    profile: str
    title: str
    source_byte_count: int
    source_sha256: str
    wrapper_sha256: str
    interpretation_sha256: str

    def __post_init__(self) -> None:
        _identity_text(self.profile, "Contract profile", maximum=128)
        _identity_text(self.title, "Contract title", maximum=256)
        _identity_count(
            self.source_byte_count,
            "Contract source byte count",
            positive=True,
        )
        _identity_sha256(self.source_sha256, "Contract source SHA-256")
        _identity_sha256(self.wrapper_sha256, "Contract wrapper SHA-256")
        _identity_sha256(
            self.interpretation_sha256,
            "Contract interpretation SHA-256",
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "title": self.title,
            "source_byte_count": self.source_byte_count,
            "source_sha256": self.source_sha256,
            "wrapper_sha256": self.wrapper_sha256,
            "interpretation_sha256": self.interpretation_sha256,
        }

    @classmethod
    def from_dict(cls, value: Any) -> FieldNoteCreatorLiveContractIdentity:
        fields = {
            "profile",
            "title",
            "source_byte_count",
            "source_sha256",
            "wrapper_sha256",
            "interpretation_sha256",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise FieldNoteCreatorLiveValidationError(
                "Contract terminal projection identity is invalid."
            )
        return cls(**value)


@dataclass(frozen=True)
class FieldNoteCreatorLiveTaskIdentity:
    byte_count: int
    sha256: str

    def __post_init__(self) -> None:
        _identity_count(self.byte_count, "Task byte count", positive=True)
        _identity_sha256(self.sha256, "Task SHA-256")

    def as_dict(self) -> dict[str, Any]:
        return {"byte_count": self.byte_count, "sha256": self.sha256}

    @classmethod
    def from_dict(cls, value: Any) -> FieldNoteCreatorLiveTaskIdentity:
        if not isinstance(value, dict) or set(value) != {"byte_count", "sha256"}:
            raise FieldNoteCreatorLiveValidationError(
                "Task terminal projection identity is invalid."
            )
        return cls(**value)


@dataclass(frozen=True)
class FieldNoteCreatorLiveHistoricalBoundary:
    cycle_key: str
    state: str
    failure_boundary: str
    failure_code: str

    def __post_init__(self) -> None:
        _identity_text(self.cycle_key, "Historical Cycle key", maximum=128)
        _identity_text(self.state, "Historical state", maximum=64)
        _identity_text(
            self.failure_boundary,
            "Historical failure boundary",
            maximum=128,
        )
        _identity_text(self.failure_code, "Historical failure code", maximum=256)

    def as_dict(self) -> dict[str, Any]:
        return {
            "cycle_key": self.cycle_key,
            "state": self.state,
            "failure_boundary": self.failure_boundary,
            "failure_code": self.failure_code,
        }

    @classmethod
    def from_dict(cls, value: Any) -> FieldNoteCreatorLiveHistoricalBoundary:
        fields = {"cycle_key", "state", "failure_boundary", "failure_code"}
        if not isinstance(value, dict) or set(value) != fields:
            raise FieldNoteCreatorLiveValidationError(
                "Historical terminal projection boundary is invalid."
            )
        return cls(**value)


@dataclass(frozen=True)
class FieldNoteCreatorLiveTerminalProjectionBinding:
    schema: str
    launch_binding_sha256: str
    contract_identity: FieldNoteCreatorLiveContractIdentity
    ordinary_contract_execution_authority: str
    guided_intake_freeze_authority: str
    implementation_authorization_observed_at: str
    run_1_task: FieldNoteCreatorLiveTaskIdentity
    run_2_task: FieldNoteCreatorLiveTaskIdentity
    historical_boundary: FieldNoteCreatorLiveHistoricalBoundary
    retry_count: int
    replacement_count: int

    def __post_init__(self) -> None:
        if self.schema != TERMINAL_PROJECTION_BINDING_SCHEMA:
            raise FieldNoteCreatorLiveValidationError(
                "Terminal projection binding schema is invalid."
            )
        _identity_sha256(self.launch_binding_sha256, "Launch binding SHA-256")
        if not isinstance(
            self.contract_identity,
            FieldNoteCreatorLiveContractIdentity,
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Contract terminal projection identity is invalid."
            )
        if self.ordinary_contract_execution_authority != "INTERPRETATION_ONLY":
            raise FieldNoteCreatorLiveValidationError(
                "Ordinary Contract authority changed."
            )
        if self.guided_intake_freeze_authority != (
            "IMMUTABLE_INTERPRETATION_ONLY"
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Guided Intake freeze authority changed."
            )
        _parse_time(
            self.implementation_authorization_observed_at,
            "Implementation authorization observation",
        )
        if not isinstance(self.run_1_task, FieldNoteCreatorLiveTaskIdentity) or (
            not isinstance(self.run_2_task, FieldNoteCreatorLiveTaskIdentity)
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Terminal projection task identity is invalid."
            )
        if not isinstance(
            self.historical_boundary,
            FieldNoteCreatorLiveHistoricalBoundary,
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Historical terminal projection boundary is invalid."
            )
        if self.retry_count != 0 or self.replacement_count != 0:
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live retry or replacement count widened."
            )

    @classmethod
    def create(
        cls,
        *,
        launch_binding_sha256: str,
        contract_identity: FieldNoteCreatorLiveContractIdentity,
        ordinary_contract_execution_authority: str,
        guided_intake_freeze_authority: str,
        implementation_authorization_observed_at: str,
        run_1_task: FieldNoteCreatorLiveTaskIdentity,
        run_2_task: FieldNoteCreatorLiveTaskIdentity,
        historical_boundary: FieldNoteCreatorLiveHistoricalBoundary,
        retry_count: int = 0,
        replacement_count: int = 0,
    ) -> FieldNoteCreatorLiveTerminalProjectionBinding:
        return cls(
            schema=TERMINAL_PROJECTION_BINDING_SCHEMA,
            launch_binding_sha256=launch_binding_sha256,
            contract_identity=contract_identity,
            ordinary_contract_execution_authority=(
                ordinary_contract_execution_authority
            ),
            guided_intake_freeze_authority=guided_intake_freeze_authority,
            implementation_authorization_observed_at=(
                implementation_authorization_observed_at
            ),
            run_1_task=run_1_task,
            run_2_task=run_2_task,
            historical_boundary=historical_boundary,
            retry_count=retry_count,
            replacement_count=replacement_count,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "launch_binding_sha256": self.launch_binding_sha256,
            "contract_identity": self.contract_identity.as_dict(),
            "ordinary_contract_execution_authority": (
                self.ordinary_contract_execution_authority
            ),
            "guided_intake_freeze_authority": (
                self.guided_intake_freeze_authority
            ),
            "implementation_authorization_observed_at": (
                self.implementation_authorization_observed_at
            ),
            "run_1_task": self.run_1_task.as_dict(),
            "run_2_task": self.run_2_task.as_dict(),
            "historical_boundary": self.historical_boundary.as_dict(),
            "retry_count": self.retry_count,
            "replacement_count": self.replacement_count,
        }

    @classmethod
    def from_dict(
        cls,
        value: Any,
    ) -> FieldNoteCreatorLiveTerminalProjectionBinding:
        fields = {
            "schema",
            "launch_binding_sha256",
            "contract_identity",
            "ordinary_contract_execution_authority",
            "guided_intake_freeze_authority",
            "implementation_authorization_observed_at",
            "run_1_task",
            "run_2_task",
            "historical_boundary",
            "retry_count",
            "replacement_count",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise FieldNoteCreatorLiveValidationError(
                "Terminal projection binding is invalid."
            )
        return cls(
            schema=value["schema"],
            launch_binding_sha256=value["launch_binding_sha256"],
            contract_identity=FieldNoteCreatorLiveContractIdentity.from_dict(
                value["contract_identity"]
            ),
            ordinary_contract_execution_authority=(
                value["ordinary_contract_execution_authority"]
            ),
            guided_intake_freeze_authority=(
                value["guided_intake_freeze_authority"]
            ),
            implementation_authorization_observed_at=(
                value["implementation_authorization_observed_at"]
            ),
            run_1_task=FieldNoteCreatorLiveTaskIdentity.from_dict(
                value["run_1_task"]
            ),
            run_2_task=FieldNoteCreatorLiveTaskIdentity.from_dict(
                value["run_2_task"]
            ),
            historical_boundary=FieldNoteCreatorLiveHistoricalBoundary.from_dict(
                value["historical_boundary"]
            ),
            retry_count=value["retry_count"],
            replacement_count=value["replacement_count"],
        )


class FieldNoteCreatorLiveError(RuntimeError):
    """Base error for the bounded creator-live runtime path."""


class FieldNoteCreatorLiveValidationError(
    FieldNoteCreatorLiveError,
    ValueError,
):
    """The caller supplied an invalid identity or typed stage result."""


class FieldNoteCreatorLiveStageError(FieldNoteCreatorLiveError):
    """A stage failed and the one-attempt journal is terminal."""


class FieldNoteCreatorLiveDurabilityError(FieldNoteCreatorLiveError):
    """The durable journal cannot be trusted or extended."""


class FieldNoteCreatorLiveAttemptExistsError(FieldNoteCreatorLiveError):
    """The one-attempt journal already exists and cannot be replaced."""


@dataclass(frozen=True)
class FieldNoteCreatorLiveOutputArtifactIdentity:
    schema: str
    artifact_id: str
    proof_attempt_id: str
    run_id: str
    transmission_ordinal: int
    media_type: str
    byte_count: int
    sha256: str

    @staticmethod
    def _body(
        *,
        proof_attempt_id: str,
        run_id: str,
        transmission_ordinal: int,
        media_type: str,
        byte_count: int,
        sha256: str,
    ) -> dict[str, Any]:
        return {
            "schema": OUTPUT_ARTIFACT_IDENTITY_SCHEMA,
            "proof_attempt_id": proof_attempt_id,
            "run_id": run_id,
            "transmission_ordinal": transmission_ordinal,
            "media_type": media_type,
            "byte_count": byte_count,
            "sha256": sha256,
        }

    @classmethod
    def create(
        cls,
        *,
        proof_attempt_id: str,
        run_id: str,
        byte_count: int,
        sha256: str,
    ) -> FieldNoteCreatorLiveOutputArtifactIdentity:
        _identity_text(proof_attempt_id, "Output proof-attempt ID", maximum=256)
        _identity_text(run_id, "Output Run ID", maximum=256)
        _identity_count(byte_count, "Output byte count", positive=True)
        _identity_sha256(sha256, "Output SHA-256")
        body = cls._body(
            proof_attempt_id=proof_attempt_id,
            run_id=run_id,
            transmission_ordinal=2,
            media_type="text/plain; charset=utf-8",
            byte_count=byte_count,
            sha256=sha256,
        )
        return cls(
            **body,
            artifact_id=_canonical_sha256(body),
        )

    def __post_init__(self) -> None:
        body = self._body(
            proof_attempt_id=_identity_text(
                self.proof_attempt_id,
                "Output proof-attempt ID",
                maximum=256,
            ),
            run_id=_identity_text(self.run_id, "Output Run ID", maximum=256),
            transmission_ordinal=self.transmission_ordinal,
            media_type=self.media_type,
            byte_count=self.byte_count,
            sha256=self.sha256,
        )
        if (
            self.schema != OUTPUT_ARTIFACT_IDENTITY_SCHEMA
            or self.transmission_ordinal != 2
            or self.media_type != "text/plain; charset=utf-8"
            or self.byte_count > 65_536
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Output artifact fixed identity is invalid."
            )
        _identity_count(self.byte_count, "Output byte count", positive=True)
        _identity_sha256(self.sha256, "Output SHA-256")
        if self.artifact_id != _canonical_sha256(body):
            raise FieldNoteCreatorLiveValidationError(
                "Output artifact canonical identity is invalid."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "artifact_id": self.artifact_id,
            "proof_attempt_id": self.proof_attempt_id,
            "run_id": self.run_id,
            "transmission_ordinal": self.transmission_ordinal,
            "media_type": self.media_type,
            "byte_count": self.byte_count,
            "sha256": self.sha256,
        }

    @classmethod
    def from_dict(
        cls,
        value: Any,
    ) -> FieldNoteCreatorLiveOutputArtifactIdentity:
        fields = {
            "schema",
            "artifact_id",
            "proof_attempt_id",
            "run_id",
            "transmission_ordinal",
            "media_type",
            "byte_count",
            "sha256",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise FieldNoteCreatorLiveValidationError(
                "Output artifact identity is invalid."
            )
        return cls(**value)


@dataclass(frozen=True)
class FieldNoteCreatorLiveRun2OutputIdentity:
    schema: str
    proof_attempt_id: str
    run_id: str
    task_byte_count: int
    task_sha256: str
    transmission_ordinal: int
    normal_terminal: bool
    turn_status: str
    runtime_status: str
    failure_diagnostic_absent: bool
    final_output_byte_count: int
    final_output_sha256: str
    output_artifact: FieldNoteCreatorLiveOutputArtifactIdentity
    a3_compiler_branch: str

    @classmethod
    def create(
        cls,
        *,
        proof_attempt_id: str,
        run_id: str,
        task_byte_count: int,
        task_sha256: str,
        final_output_byte_count: int,
        final_output_sha256: str,
    ) -> FieldNoteCreatorLiveRun2OutputIdentity:
        artifact = FieldNoteCreatorLiveOutputArtifactIdentity.create(
            proof_attempt_id=proof_attempt_id,
            run_id=run_id,
            byte_count=final_output_byte_count,
            sha256=final_output_sha256,
        )
        return cls(
            schema=RUN_2_OUTPUT_IDENTITY_SCHEMA,
            proof_attempt_id=proof_attempt_id,
            run_id=run_id,
            task_byte_count=task_byte_count,
            task_sha256=task_sha256,
            transmission_ordinal=2,
            normal_terminal=True,
            turn_status="completed",
            runtime_status="NORMAL_TERMINAL",
            failure_diagnostic_absent=True,
            final_output_byte_count=final_output_byte_count,
            final_output_sha256=final_output_sha256,
            output_artifact=artifact,
            a3_compiler_branch=A3_COMPILER_BRANCH,
        )

    def __post_init__(self) -> None:
        _identity_text(self.proof_attempt_id, "Run 2 proof-attempt ID", maximum=256)
        _identity_text(self.run_id, "Run 2 output Run ID", maximum=256)
        _identity_count(self.task_byte_count, "Run 2 task byte count", positive=True)
        _identity_sha256(self.task_sha256, "Run 2 task SHA-256")
        _identity_count(
            self.final_output_byte_count,
            "Run 2 final-output byte count",
            positive=True,
        )
        _identity_sha256(self.final_output_sha256, "Run 2 final-output SHA-256")
        if (
            self.schema != RUN_2_OUTPUT_IDENTITY_SCHEMA
            or self.transmission_ordinal != 2
            or self.normal_terminal is not True
            or self.turn_status != "completed"
            or self.runtime_status != "NORMAL_TERMINAL"
            or self.failure_diagnostic_absent is not True
            or self.a3_compiler_branch != A3_COMPILER_BRANCH
            or self.final_output_byte_count > 65_536
            or not isinstance(
                self.output_artifact,
                FieldNoteCreatorLiveOutputArtifactIdentity,
            )
            or self.output_artifact.proof_attempt_id != self.proof_attempt_id
            or self.output_artifact.run_id != self.run_id
            or self.output_artifact.transmission_ordinal != 2
            or self.output_artifact.byte_count != self.final_output_byte_count
            or self.output_artifact.sha256 != self.final_output_sha256
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Run 2 output identity is cross-bound or invalid."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "proof_attempt_id": self.proof_attempt_id,
            "run_id": self.run_id,
            "task_byte_count": self.task_byte_count,
            "task_sha256": self.task_sha256,
            "transmission_ordinal": self.transmission_ordinal,
            "normal_terminal": self.normal_terminal,
            "turn_status": self.turn_status,
            "runtime_status": self.runtime_status,
            "failure_diagnostic_absent": self.failure_diagnostic_absent,
            "final_output_byte_count": self.final_output_byte_count,
            "final_output_sha256": self.final_output_sha256,
            "output_artifact": self.output_artifact.as_dict(),
            "a3_compiler_branch": self.a3_compiler_branch,
        }

    @classmethod
    def from_dict(
        cls,
        value: Any,
    ) -> FieldNoteCreatorLiveRun2OutputIdentity:
        fields = {
            "schema",
            "proof_attempt_id",
            "run_id",
            "task_byte_count",
            "task_sha256",
            "transmission_ordinal",
            "normal_terminal",
            "turn_status",
            "runtime_status",
            "failure_diagnostic_absent",
            "final_output_byte_count",
            "final_output_sha256",
            "output_artifact",
            "a3_compiler_branch",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise FieldNoteCreatorLiveValidationError(
                "Run 2 output identity record is invalid."
            )
        return cls(
            **{key: value[key] for key in fields - {"output_artifact"}},
            output_artifact=FieldNoteCreatorLiveOutputArtifactIdentity.from_dict(
                value["output_artifact"]
            ),
        )


@dataclass(frozen=True)
class FieldNoteCreatorLiveA3RejectionCounts:
    below_minimum_byte_length: int
    whole_note_range: int
    non_unique_source_occurrence: int
    absent_output_occurrence: int
    multiple_output_occurrences: int

    def __post_init__(self) -> None:
        for label, value in self.as_dict().items():
            _identity_count(value, f"A3 rejection count {label}")

    def as_dict(self) -> dict[str, int]:
        return {
            "below_minimum_byte_length": self.below_minimum_byte_length,
            "whole_note_range": self.whole_note_range,
            "non_unique_source_occurrence": self.non_unique_source_occurrence,
            "absent_output_occurrence": self.absent_output_occurrence,
            "multiple_output_occurrences": self.multiple_output_occurrences,
        }

    @classmethod
    def from_dict(cls, value: Any) -> FieldNoteCreatorLiveA3RejectionCounts:
        fields = {
            "below_minimum_byte_length",
            "whole_note_range",
            "non_unique_source_occurrence",
            "absent_output_occurrence",
            "multiple_output_occurrences",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise FieldNoteCreatorLiveValidationError(
                "A3 rejection counts are invalid."
            )
        return cls(**value)


@dataclass(frozen=True, init=False)
class FieldNoteCreatorLiveA3CompilerAudit:
    schema: str
    proof_attempt_id: str
    run_id: str
    output_artifact_id: str
    compiler_version: str
    compiler_branch: str
    source_note_byte_count: int
    source_note_sha256: str
    output_byte_count: int
    output_sha256: str
    eligible_candidate_count: int
    rejection_counts: FieldNoteCreatorLiveA3RejectionCounts
    longest_candidate_byte_count: int
    winning_candidate_count: int
    selected_source_start_byte: int | None
    selected_source_end_byte: int | None
    selected_output_start_byte: int | None
    selected_output_end_byte: int | None
    terminal_a3_code: str | None
    audit_sha256: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise FieldNoteCreatorLiveValidationError(
            "A3 compiler audits are issued only from exact compiler facts."
        )

    @classmethod
    def issue(
        cls,
        *,
        proof_attempt_id: str,
        run_id: str,
        output_artifact_id: str,
        source_note_byte_count: int,
        source_note_sha256: str,
        output_byte_count: int,
        output_sha256: str,
        eligible_candidate_count: int,
        rejection_counts: FieldNoteCreatorLiveA3RejectionCounts,
        longest_candidate_byte_count: int,
        winning_candidate_count: int,
        selected_source_start_byte: int | None,
        selected_source_end_byte: int | None,
        selected_output_start_byte: int | None,
        selected_output_end_byte: int | None,
        terminal_a3_code: str | None,
    ) -> FieldNoteCreatorLiveA3CompilerAudit:
        _identity_text(proof_attempt_id, "A3 proof-attempt ID", maximum=256)
        _identity_text(run_id, "A3 Run ID", maximum=256)
        _identity_sha256(output_artifact_id, "A3 output artifact ID")
        _identity_count(
            source_note_byte_count,
            "A3 source Note byte count",
            positive=True,
        )
        _identity_sha256(source_note_sha256, "A3 source Note SHA-256")
        _identity_count(output_byte_count, "A3 output byte count", positive=True)
        _identity_sha256(output_sha256, "A3 output SHA-256")
        _identity_count(eligible_candidate_count, "A3 eligible candidate count")
        _identity_count(
            longest_candidate_byte_count,
            "A3 longest candidate byte count",
        )
        _identity_count(winning_candidate_count, "A3 winning candidate count")
        if not isinstance(rejection_counts, FieldNoteCreatorLiveA3RejectionCounts):
            raise FieldNoteCreatorLiveValidationError(
                "A3 rejection counts are invalid."
            )
        offsets = (
            selected_source_start_byte,
            selected_source_end_byte,
            selected_output_start_byte,
            selected_output_end_byte,
        )
        if winning_candidate_count == 1:
            if (
                eligible_candidate_count < 1
                or terminal_a3_code is not None
                or any(type(value) is not int for value in offsets)
            ):
                raise FieldNoteCreatorLiveValidationError(
                    "A3 winning offsets are invalid."
                )
            source_start = selected_source_start_byte
            source_end = selected_source_end_byte
            output_start = selected_output_start_byte
            output_end = selected_output_end_byte
            assert isinstance(source_start, int)
            assert isinstance(source_end, int)
            assert isinstance(output_start, int)
            assert isinstance(output_end, int)
            if (
                not 0 <= source_start < source_end <= source_note_byte_count
                or not 0 <= output_start < output_end <= output_byte_count
                or source_end - source_start != output_end - output_start
                or longest_candidate_byte_count != source_end - source_start
            ):
                raise FieldNoteCreatorLiveValidationError(
                    "A3 winning offsets are out of bounds."
                )
        else:
            if any(value is not None for value in offsets):
                raise FieldNoteCreatorLiveValidationError(
                    "A3 non-winning offsets must be null."
                )
            expected_code = (
                "A3_EXACT_STRUCTURE_MISSING"
                if eligible_candidate_count == 0
                else "A3_EXACT_STRUCTURE_AMBIGUOUS"
            )
            if (
                winning_candidate_count < 0
                or terminal_a3_code != expected_code
                or (
                    eligible_candidate_count == 0
                    and (
                        winning_candidate_count != 0
                        or longest_candidate_byte_count != 0
                    )
                )
                or (
                    eligible_candidate_count > 0
                    and winning_candidate_count < 2
                )
            ):
                raise FieldNoteCreatorLiveValidationError(
                    "A3 terminal compiler result is invalid."
                )
        body = {
            "schema": A3_COMPILER_AUDIT_SCHEMA,
            "proof_attempt_id": proof_attempt_id,
            "run_id": run_id,
            "output_artifact_id": output_artifact_id,
            "compiler_version": A3_COMPILER_VERSION,
            "compiler_branch": A3_COMPILER_BRANCH,
            "source_note_byte_count": source_note_byte_count,
            "source_note_sha256": source_note_sha256,
            "output_byte_count": output_byte_count,
            "output_sha256": output_sha256,
            "eligible_candidate_count": eligible_candidate_count,
            "rejection_counts": rejection_counts.as_dict(),
            "longest_candidate_byte_count": longest_candidate_byte_count,
            "winning_candidate_count": winning_candidate_count,
            "selected_source_start_byte": selected_source_start_byte,
            "selected_source_end_byte": selected_source_end_byte,
            "selected_output_start_byte": selected_output_start_byte,
            "selected_output_end_byte": selected_output_end_byte,
            "terminal_a3_code": terminal_a3_code,
        }
        value = object.__new__(cls)
        for field, item in {
            **body,
            "rejection_counts": rejection_counts,
            "audit_sha256": _canonical_sha256(body),
        }.items():
            object.__setattr__(value, field, item)
        return value

    def _body(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "proof_attempt_id": self.proof_attempt_id,
            "run_id": self.run_id,
            "output_artifact_id": self.output_artifact_id,
            "compiler_version": self.compiler_version,
            "compiler_branch": self.compiler_branch,
            "source_note_byte_count": self.source_note_byte_count,
            "source_note_sha256": self.source_note_sha256,
            "output_byte_count": self.output_byte_count,
            "output_sha256": self.output_sha256,
            "eligible_candidate_count": self.eligible_candidate_count,
            "rejection_counts": self.rejection_counts.as_dict(),
            "longest_candidate_byte_count": self.longest_candidate_byte_count,
            "winning_candidate_count": self.winning_candidate_count,
            "selected_source_start_byte": self.selected_source_start_byte,
            "selected_source_end_byte": self.selected_source_end_byte,
            "selected_output_start_byte": self.selected_output_start_byte,
            "selected_output_end_byte": self.selected_output_end_byte,
            "terminal_a3_code": self.terminal_a3_code,
        }

    def as_dict(self) -> dict[str, Any]:
        return {**self._body(), "audit_sha256": self.audit_sha256}

    @classmethod
    def from_dict(cls, value: Any) -> FieldNoteCreatorLiveA3CompilerAudit:
        fields = {
            "schema",
            "proof_attempt_id",
            "run_id",
            "output_artifact_id",
            "compiler_version",
            "compiler_branch",
            "source_note_byte_count",
            "source_note_sha256",
            "output_byte_count",
            "output_sha256",
            "eligible_candidate_count",
            "rejection_counts",
            "longest_candidate_byte_count",
            "winning_candidate_count",
            "selected_source_start_byte",
            "selected_source_end_byte",
            "selected_output_start_byte",
            "selected_output_end_byte",
            "terminal_a3_code",
            "audit_sha256",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise FieldNoteCreatorLiveValidationError(
                "A3 compiler audit record is invalid."
            )
        if (
            value["schema"] != A3_COMPILER_AUDIT_SCHEMA
            or value["compiler_version"] != A3_COMPILER_VERSION
            or value["compiler_branch"] != A3_COMPILER_BRANCH
        ):
            raise FieldNoteCreatorLiveValidationError(
                "A3 compiler audit fixed identity is invalid."
            )
        issued = cls.issue(
            proof_attempt_id=value["proof_attempt_id"],
            run_id=value["run_id"],
            output_artifact_id=value["output_artifact_id"],
            source_note_byte_count=value["source_note_byte_count"],
            source_note_sha256=value["source_note_sha256"],
            output_byte_count=value["output_byte_count"],
            output_sha256=value["output_sha256"],
            eligible_candidate_count=value["eligible_candidate_count"],
            rejection_counts=FieldNoteCreatorLiveA3RejectionCounts.from_dict(
                value["rejection_counts"]
            ),
            longest_candidate_byte_count=value["longest_candidate_byte_count"],
            winning_candidate_count=value["winning_candidate_count"],
            selected_source_start_byte=value["selected_source_start_byte"],
            selected_source_end_byte=value["selected_source_end_byte"],
            selected_output_start_byte=value["selected_output_start_byte"],
            selected_output_end_byte=value["selected_output_end_byte"],
            terminal_a3_code=value["terminal_a3_code"],
        )
        if issued.audit_sha256 != value["audit_sha256"]:
            raise FieldNoteCreatorLiveValidationError(
                "A3 compiler audit canonical identity is invalid."
            )
        return issued


def _proposal_diagnostic_reason_matches(
    diagnostic: FieldNoteA1ProposalDiagnostic,
    reason: str,
) -> bool:
    subcause = diagnostic.final_subcause
    if subcause is None:
        return False
    if subcause == "A1_DIRECT_WRITE_REQUESTED":
        suffix = (
            f":{diagnostic.direct_write_identity}"
            if diagnostic.direct_write_identity is not None
            else ""
        )
        return reason == f"{subcause}{suffix}"
    return reason == subcause


@dataclass(frozen=True, init=False)
class FieldNoteCreatorLiveA1CaptureCommitReceipt:
    """Identity-only proof that the controller saved and read back one Note."""

    schema: Literal[
        "decision-os.field-note-creator-live-a1-capture-commit.v0.1"
    ]
    proof_attempt_id: str
    run_id: str
    task_sha256: str
    actual_runtime_identity: CodexRuntimeIdentity
    source_repository: FieldNoteSourceRepositoryIdentity
    note: FieldNoteIdentity
    note_byte_count: int
    draft_evidence_sha256: str
    draft_created_at: str
    save_as_of: str
    controller_state: Literal["saved"]
    read_back_verified: Literal[True]
    receipt_sha256: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise FieldNoteCreatorLiveValidationError(
            "A1 capture commit receipts are issued only after exact read-back."
        )

    @classmethod
    def _issue(
        cls,
        *,
        authority: object,
        proof_attempt_id: str,
        run_id: str,
        task_sha256: str,
        actual_runtime_identity: CodexRuntimeIdentity,
        source_repository: FieldNoteSourceRepositoryIdentity,
        note: FieldNoteIdentity,
        note_byte_count: int,
        draft_evidence_sha256: str,
        draft_created_at: str,
        save_as_of: str,
    ) -> FieldNoteCreatorLiveA1CaptureCommitReceipt:
        if authority is not _A1_CAPTURE_COMMIT_AUTHORITY:
            raise FieldNoteCreatorLiveValidationError(
                "A1 capture commit authority is invalid."
            )
        if (
            not isinstance(proof_attempt_id, str)
            or not proof_attempt_id.strip()
            or not isinstance(run_id, str)
            or not run_id.strip()
            or not isinstance(task_sha256, str)
            or len(task_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in task_sha256
            )
            or not isinstance(
                actual_runtime_identity,
                CodexRuntimeIdentity,
            )
            or not isinstance(
                source_repository,
                FieldNoteSourceRepositoryIdentity,
            )
            or not isinstance(note, FieldNoteIdentity)
            or type(note_byte_count) is not int
            or note_byte_count <= 0
            or not isinstance(draft_evidence_sha256, str)
            or len(draft_evidence_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in draft_evidence_sha256
            )
        ):
            raise FieldNoteCreatorLiveValidationError(
                "A1 capture commit identity is invalid."
            )
        normalized_draft_created_at, draft_time = _parse_time(
            draft_created_at,
            "A1 draft creation time",
        )
        normalized_save_as_of, save_time = _parse_time(
            save_as_of,
            "A1 capture save As-of",
        )
        if save_time < draft_time:
            raise FieldNoteCreatorLiveValidationError(
                "A1 capture save precedes draft creation."
            )
        body = {
            "schema": A1_CAPTURE_COMMIT_SCHEMA,
            "proof_attempt_id": proof_attempt_id.strip(),
            "run_id": run_id.strip(),
            "task_sha256": task_sha256,
            "actual_runtime_identity": _runtime_as_dict(
                actual_runtime_identity
            ),
            "source_repository": source_repository.as_dict(),
            "note": note.as_dict(),
            "note_byte_count": note_byte_count,
            "draft_evidence_sha256": draft_evidence_sha256,
            "draft_created_at": normalized_draft_created_at,
            "save_as_of": normalized_save_as_of,
            "controller_state": "saved",
            "read_back_verified": True,
        }
        value = object.__new__(cls)
        for field, item in {
            **body,
            "actual_runtime_identity": actual_runtime_identity,
            "source_repository": source_repository,
            "note": note,
            "receipt_sha256": _canonical_sha256(body),
        }.items():
            object.__setattr__(value, field, item)
        return value

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "proof_attempt_id": self.proof_attempt_id,
            "run_id": self.run_id,
            "task_sha256": self.task_sha256,
            "actual_runtime_identity": _runtime_as_dict(
                self.actual_runtime_identity
            ),
            "source_repository": self.source_repository.as_dict(),
            "note": self.note.as_dict(),
            "note_byte_count": self.note_byte_count,
            "draft_evidence_sha256": self.draft_evidence_sha256,
            "draft_created_at": self.draft_created_at,
            "save_as_of": self.save_as_of,
            "controller_state": self.controller_state,
            "read_back_verified": self.read_back_verified,
            "receipt_sha256": self.receipt_sha256,
        }


class _JournalIntegrityError(ValueError):
    def __init__(
        self,
        reason: str,
        *,
        repair_action: RepairAction,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.repair_action = repair_action


def _utc_now_rfc3339() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _bounded_reason(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 256
        or "\x00" in value
    ):
        raise FieldNoteCreatorLiveValidationError(
            "Creator-live failure reason is outside its bounded schema."
        )
    return value.strip()


def _a1_capture_chronology_is_valid(
    *,
    run_1_started_at: str,
    draft_created_at: str,
    save_as_of: str,
    observed_at: str,
    proof_as_of: str | None = None,
) -> bool:
    """Compare the five creator-live A1 instants in their required order."""

    _, run_time = _parse_time(run_1_started_at, "Run 1 start")
    _, draft_time = _parse_time(draft_created_at, "A1 draft creation time")
    _, save_time = _parse_time(save_as_of, "A1 capture save As-of")
    _, observed_time = _parse_time(observed_at, "A1 checkpoint observation")
    chronology_valid = run_time <= draft_time <= save_time <= observed_time
    if proof_as_of is None:
        return chronology_valid
    _, proof_time = _parse_time(proof_as_of, "Proof As-of")
    return chronology_valid and observed_time <= proof_time


def _runtime_from_dict(value: Any) -> CodexRuntimeIdentity:
    if not isinstance(value, dict) or set(value) != {
        "model",
        "reasoning_effort",
        "service_tier",
        "codex_cli_version",
        "account_type",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUNTIME_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        return CodexRuntimeIdentity(**value)
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUNTIME_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc


def _repository_from_dict(value: Any) -> FieldNoteSourceRepositoryIdentity:
    if not isinstance(value, dict) or set(value) != {
        "repository_id",
        "source_commit",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_REPOSITORY_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        return FieldNoteSourceRepositoryIdentity(**value)
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_REPOSITORY_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc


def _run_from_dict(
    value: Any,
    *,
    repository: FieldNoteSourceRepositoryIdentity,
    runtime: CodexRuntimeIdentity,
) -> FieldNoteWholeFlowRunIdentity:
    if not isinstance(value, dict) or set(value) != {
        "proof_attempt_id",
        "run_id",
        "started_at",
        "repository",
        "runtime",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUN_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    if value["repository"] != repository.as_dict() or value["runtime"] != (
        _runtime_as_dict(runtime)
    ):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUN_IDENTITY_MISMATCH",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        return FieldNoteWholeFlowRunIdentity(
            proof_attempt_id=value["proof_attempt_id"],
            run_id=value["run_id"],
            started_at=value["started_at"],
            repository=repository,
            runtime=runtime,
        )
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUN_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc


def _attempt_from_dict(value: Any) -> FieldNoteWholeFlowAttempt:
    if not isinstance(value, dict) or set(value) != {
        "proof_attempt_id",
        "proof_mode",
        "creator_id",
        "proof_as_of",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        attempt = FieldNoteWholeFlowAttempt(**value)
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc
    if attempt.proof_mode != "CREATOR_LIVE":
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_MODE_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    return attempt


def _attempt_v2_from_dict(value: Any) -> FieldNoteCreatorLiveAttempt:
    if not isinstance(value, dict) or set(value) != {
        "proof_attempt_id",
        "proof_mode",
        "creator_id",
        "authorization_observed_at",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        return FieldNoteCreatorLiveAttempt(**value)
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc


@dataclass(frozen=True)
class _JournalRecord:
    schema: str
    sequence: int
    kind: JournalRecordKind
    payload: dict[str, Any]
    previous_record_sha256: str
    record_sha256: str

    @classmethod
    def create(
        cls,
        *,
        sequence: int,
        kind: JournalRecordKind,
        payload: dict[str, Any],
        previous_record_sha256: str,
        schema: str = CREATOR_LIVE_RECORD_SCHEMA,
    ) -> _JournalRecord:
        body = {
            "schema": schema,
            "sequence": sequence,
            "kind": kind,
            "payload": payload,
            "previous_record_sha256": previous_record_sha256,
        }
        return cls(
            schema=schema,
            sequence=sequence,
            kind=kind,
            payload=payload,
            previous_record_sha256=previous_record_sha256,
            record_sha256=_canonical_sha256(body),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "sequence": self.sequence,
            "kind": self.kind,
            "payload": self.payload,
            "previous_record_sha256": self.previous_record_sha256,
            "record_sha256": self.record_sha256,
        }

    def serialize_line(self) -> bytes:
        return (canonical_json(self.as_dict()) + "\n").encode("utf-8")


@dataclass(frozen=True)
class _AnchorRecord:
    schema: str
    generation: int
    proof_attempt_id: str
    journal_record_count: int
    journal_byte_length: int
    journal_record_chain_head_sha256: str
    journal_sha256: str
    previous_anchor_sha256: str
    anchor_sha256: str

    @classmethod
    def create(
        cls,
        *,
        generation: int,
        proof_attempt_id: str,
        journal_raw: bytes,
        journal_records: tuple[_JournalRecord, ...],
        previous_anchor_sha256: str,
        schema: str = CREATOR_LIVE_ANCHOR_SCHEMA,
    ) -> _AnchorRecord:
        body = {
            "schema": schema,
            "generation": generation,
            "proof_attempt_id": proof_attempt_id,
            "journal_record_count": len(journal_records),
            "journal_byte_length": len(journal_raw),
            "journal_record_chain_head_sha256": (
                journal_records[-1].record_sha256
            ),
            "journal_sha256": hashlib.sha256(journal_raw).hexdigest(),
            "previous_anchor_sha256": previous_anchor_sha256,
        }
        return cls(
            schema=schema,
            generation=generation,
            proof_attempt_id=proof_attempt_id,
            journal_record_count=len(journal_records),
            journal_byte_length=len(journal_raw),
            journal_record_chain_head_sha256=(
                journal_records[-1].record_sha256
            ),
            journal_sha256=hashlib.sha256(journal_raw).hexdigest(),
            previous_anchor_sha256=previous_anchor_sha256,
            anchor_sha256=_canonical_sha256(body),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generation": self.generation,
            "proof_attempt_id": self.proof_attempt_id,
            "journal_record_count": self.journal_record_count,
            "journal_byte_length": self.journal_byte_length,
            "journal_record_chain_head_sha256": (
                self.journal_record_chain_head_sha256
            ),
            "journal_sha256": self.journal_sha256,
            "previous_anchor_sha256": self.previous_anchor_sha256,
            "anchor_sha256": self.anchor_sha256,
        }

    def serialize_line(self) -> bytes:
        return (canonical_json(self.as_dict()) + "\n").encode("utf-8")


def _parse_records(raw: bytes) -> tuple[_JournalRecord, ...]:
    if not raw or not raw.endswith(b"\n"):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_DURABLE_TRACE_TRUNCATED",
            repair_action="EVIDENCE_DELETION",
        )
    records: list[_JournalRecord] = []
    previous = JOURNAL_GENESIS_SHA256
    record_schema: str | None = None
    for index, line in enumerate(raw.splitlines()):
        try:
            text = line.decode("utf-8")
            value = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_TRACE_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            ) from exc
        if not isinstance(value, dict) or canonical_json(value) != text:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_TRACE_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            )
        if set(value) != {
            "schema",
            "sequence",
            "kind",
            "payload",
            "previous_record_sha256",
            "record_sha256",
        }:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_TRACE_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            )
        kind = value["kind"]
        base_kinds = {
            "ATTEMPT_OPENED",
            "RUN_1_OPENED",
            "RUN_2_OPENED",
            "CHECKPOINT",
            "ATTEMPT_FAILED",
            "TRACE_COMPLETED",
        }
        v3_kinds = {
            "RUN_2_OUTPUT_IDENTITY_RECORDED",
            "A3_COMPILER_AUDIT_RECORDED",
        }
        if kind not in base_kinds | v3_kinds or (
            kind in v3_kinds and value["schema"] != CREATOR_LIVE_RECORD_SCHEMA_V3
        ):
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_TRACE_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            )
        body = {
            "schema": value["schema"],
            "sequence": value["sequence"],
            "kind": kind,
            "payload": value["payload"],
            "previous_record_sha256": value["previous_record_sha256"],
        }
        expected_sha = _canonical_sha256(body)
        if record_schema is None:
            record_schema = value["schema"]
        if (
            value["schema"] not in {
                CREATOR_LIVE_RECORD_SCHEMA,
                CREATOR_LIVE_RECORD_SCHEMA_V2,
                CREATOR_LIVE_RECORD_SCHEMA_V3,
            }
            or value["schema"] != record_schema
            or value["sequence"] != index
            or value["previous_record_sha256"] != previous
            or value["record_sha256"] != expected_sha
            or not isinstance(value["payload"], dict)
        ):
            reason = (
                "CREATOR_LIVE_DURABLE_TRACE_DUPLICATED"
                if value["sequence"] != index
                else "CREATOR_LIVE_DURABLE_CHAIN_HEAD_MISMATCH"
            )
            action: RepairAction = (
                "RETRY_REPLACEMENT"
                if value["sequence"] != index
                else "EVENT_ID_CHANGE"
            )
            raise _JournalIntegrityError(reason, repair_action=action)
        record = _JournalRecord(
            schema=value["schema"],
            sequence=index,
            kind=kind,
            payload=value["payload"],
            previous_record_sha256=previous,
            record_sha256=expected_sha,
        )
        records.append(record)
        previous = expected_sha
    return tuple(records)


def _parse_anchors(raw: bytes) -> tuple[_AnchorRecord, ...]:
    if not raw or not raw.endswith(b"\n"):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_DURABLE_ANCHOR_TRUNCATED",
            repair_action="EVIDENCE_DELETION",
        )
    anchors: list[_AnchorRecord] = []
    previous = ANCHOR_GENESIS_SHA256
    anchor_schema: str | None = None
    for generation, line in enumerate(raw.splitlines()):
        try:
            text = line.decode("utf-8")
            value = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_ANCHOR_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            ) from exc
        required = {
            "schema",
            "generation",
            "proof_attempt_id",
            "journal_record_count",
            "journal_byte_length",
            "journal_record_chain_head_sha256",
            "journal_sha256",
            "previous_anchor_sha256",
            "anchor_sha256",
        }
        if (
            not isinstance(value, dict)
            or set(value) != required
            or canonical_json(value) != text
        ):
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_ANCHOR_TAMPERED",
                repair_action="RECEIPT_REWRITE",
            )
        body = {key: value[key] for key in required - {"anchor_sha256"}}
        expected_sha = _canonical_sha256(body)
        if anchor_schema is None:
            anchor_schema = value["schema"]
        if (
            value["schema"] not in {
                CREATOR_LIVE_ANCHOR_SCHEMA,
                CREATOR_LIVE_ANCHOR_SCHEMA_V2,
                CREATOR_LIVE_ANCHOR_SCHEMA_V3,
            }
            or value["schema"] != anchor_schema
            or value["generation"] != generation
            or value["previous_anchor_sha256"] != previous
            or value["anchor_sha256"] != expected_sha
            or not isinstance(value["proof_attempt_id"], str)
            or not value["proof_attempt_id"]
            or type(value["journal_record_count"]) is not int
            or value["journal_record_count"] <= 0
            or type(value["journal_byte_length"]) is not int
            or value["journal_byte_length"] <= 0
        ):
            raise _JournalIntegrityError(
                "CREATOR_LIVE_DURABLE_ANCHOR_CHAIN_INVALID",
                repair_action="EVENT_ID_CHANGE",
            )
        for key in (
            "journal_record_chain_head_sha256",
            "journal_sha256",
            "previous_anchor_sha256",
            "anchor_sha256",
        ):
            digest = value[key]
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_DURABLE_ANCHOR_CHAIN_INVALID",
                    repair_action="EVENT_ID_CHANGE",
                )
        anchor = _AnchorRecord(
            schema=value["schema"],
            generation=generation,
            proof_attempt_id=value["proof_attempt_id"],
            journal_record_count=value["journal_record_count"],
            journal_byte_length=value["journal_byte_length"],
            journal_record_chain_head_sha256=(
                value["journal_record_chain_head_sha256"]
            ),
            journal_sha256=value["journal_sha256"],
            previous_anchor_sha256=previous,
            anchor_sha256=expected_sha,
        )
        anchors.append(anchor)
        previous = expected_sha
    return tuple(anchors)


def _verify_journal_anchor(
    journal_raw: bytes,
    records: tuple[_JournalRecord, ...],
    anchors: tuple[_AnchorRecord, ...],
    *,
    proof_attempt_id: str,
) -> None:
    if not anchors or any(
        anchor.proof_attempt_id != proof_attempt_id for anchor in anchors
    ):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_DURABLE_ANCHOR_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    anchor = anchors[-1]
    if (
        anchor.journal_record_count != len(records)
        or anchor.journal_byte_length != len(journal_raw)
        or anchor.journal_record_chain_head_sha256
        != records[-1].record_sha256
        or anchor.journal_sha256 != hashlib.sha256(journal_raw).hexdigest()
    ):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_DURABLE_JOURNAL_ANCHOR_MISMATCH",
            repair_action="EVIDENCE_DELETION",
        )


def _note_from_dict(value: Any) -> FieldNoteIdentity:
    if not isinstance(value, dict) or set(value) != {
        "note_path",
        "field_note_id",
        "note_sha256",
        "origin_run_id",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CAPTURED_NOTE_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        return FieldNoteIdentity(**value)
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CAPTURED_NOTE_IDENTITY_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc


def _a1_capture_commit_from_dict(
    value: Any,
) -> FieldNoteCreatorLiveA1CaptureCommitReceipt:
    required = {
        "schema",
        "proof_attempt_id",
        "run_id",
        "task_sha256",
        "actual_runtime_identity",
        "source_repository",
        "note",
        "note_byte_count",
        "draft_evidence_sha256",
        "draft_created_at",
        "save_as_of",
        "controller_state",
        "read_back_verified",
        "receipt_sha256",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_A1_CAPTURE_COMMIT_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        receipt = FieldNoteCreatorLiveA1CaptureCommitReceipt._issue(
            authority=_A1_CAPTURE_COMMIT_AUTHORITY,
            proof_attempt_id=value["proof_attempt_id"],
            run_id=value["run_id"],
            task_sha256=value["task_sha256"],
            actual_runtime_identity=_runtime_from_dict(
                value["actual_runtime_identity"]
            ),
            source_repository=_repository_from_dict(
                value["source_repository"]
            ),
            note=_note_from_dict(value["note"]),
            note_byte_count=value["note_byte_count"],
            draft_evidence_sha256=value["draft_evidence_sha256"],
            draft_created_at=value["draft_created_at"],
            save_as_of=value["save_as_of"],
        )
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_A1_CAPTURE_COMMIT_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc
    if receipt.as_dict() != value:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_A1_CAPTURE_COMMIT_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    return receipt


def _provenance_from_dict(
    value: Any,
    *,
    attempt: FieldNoteWholeFlowAttempt | FieldNoteCreatorLiveAttempt,
    repository: FieldNoteSourceRepositoryIdentity,
    runtime: CodexRuntimeIdentity,
    run_1: FieldNoteWholeFlowRunIdentity,
) -> FieldNoteCreatorLiveRuntimeProvenance:
    provenance = FieldNoteCreatorLiveRuntimeProvenance._issue(
        authority=_RUNTIME_PROVENANCE_AUTHORITY,
        proof_attempt_id=attempt.proof_attempt_id,
        source_repository=repository,
        runtime=runtime,
        issued_for_run_1_id=run_1.run_id,
    )
    if value != provenance.as_dict():
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUNTIME_PROVENANCE_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    return provenance


def _event_from_dict(
    value: Any,
    *,
    attempt: FieldNoteWholeFlowAttempt | FieldNoteCreatorLiveAttempt,
    repository: FieldNoteSourceRepositoryIdentity,
    runtime: CodexRuntimeIdentity,
    provenance: FieldNoteCreatorLiveRuntimeProvenance,
) -> FieldNoteWholeFlowTraceEvent:
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "sequence",
        "stage",
        "run_id",
        "observed_at",
        "evidence_sha256",
        "previous_trace_sha256",
        "repair_action",
        "emitter",
        "proof_attempt_id",
        "runtime",
        "source_repository",
        "runtime_provenance",
        "trace_sha256",
    }:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CHECKPOINT_SHAPE_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    if (
        value["schema"] != WHOLE_FLOW_TRACE_SCHEMA
        or value["proof_attempt_id"] != attempt.proof_attempt_id
        or value["runtime"] != _runtime_as_dict(runtime)
        or value["source_repository"] != repository.as_dict()
        or value["runtime_provenance"] != provenance.as_dict()
    ):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CHECKPOINT_PROVENANCE_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    try:
        event = FieldNoteWholeFlowTraceEvent(
            sequence=value["sequence"],
            stage=value["stage"],
            run_id=value["run_id"],
            observed_at=value["observed_at"],
            evidence_sha256=value["evidence_sha256"],
            previous_trace_sha256=value["previous_trace_sha256"],
            repair_action=value["repair_action"],
            emitter=value["emitter"],
            proof_attempt_id=attempt.proof_attempt_id,
            runtime=runtime,
            source_repository=repository,
            runtime_provenance=provenance,
        )
    except (TypeError, ValueError) as exc:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CHECKPOINT_INVALID",
            repair_action="RECEIPT_REWRITE",
        ) from exc
    if event.trace_sha256 != value["trace_sha256"]:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_CHECKPOINT_IDENTITY_CHANGED",
            repair_action="EVENT_ID_CHANGE",
        )
    return event


@dataclass(frozen=True, init=False)
class FieldNoteCreatorLiveTraceReadback:
    """Sealed projection of exact durable journal bytes."""

    schema: Literal[
        "decision-os.field-note-creator-live-proof-readback.v0.1"
    ]
    attempt: FieldNoteWholeFlowAttempt
    source_repository: FieldNoteSourceRepositoryIdentity
    runtime: CodexRuntimeIdentity
    runtime_provenance: FieldNoteCreatorLiveRuntimeProvenance
    run_1: FieldNoteWholeFlowRunIdentity
    run_2: FieldNoteWholeFlowRunIdentity | None
    captured_note: FieldNoteIdentity | None
    captured_note_byte_count: int | None
    a1_capture_commit: FieldNoteCreatorLiveA1CaptureCommitReceipt | None
    a1_proposal_diagnostic: FieldNoteA1ProposalDiagnostic | None
    a3_reuse_event_id: str | None
    current_stage: TraceStage | None
    trace_event_count: int
    trace_chain_head_sha256: str
    events: tuple[FieldNoteWholeFlowTraceEvent, ...]
    state: CreatorLiveAttemptState
    failure_boundary: WholeFlowBoundary | None
    failure_reason: str | None
    repair_action: RepairAction
    one_attempt_no_retry: Literal[True]
    journal_record_count: int
    journal_byte_length: int
    journal_chain_head_sha256: str
    journal_sha256: str
    anchor_record_count: int
    anchor_chain_head_sha256: str
    anchor_sha256: str
    durable_readback_verified: bool

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise FieldNoteCreatorLiveValidationError(
            "Creator-live durable read-back cannot be caller-constructed."
        )

    @classmethod
    def _create(
        cls,
        *,
        authority: object,
        attempt: FieldNoteWholeFlowAttempt,
        source_repository: FieldNoteSourceRepositoryIdentity,
        runtime: CodexRuntimeIdentity,
        runtime_provenance: FieldNoteCreatorLiveRuntimeProvenance,
        run_1: FieldNoteWholeFlowRunIdentity,
        run_2: FieldNoteWholeFlowRunIdentity | None,
        captured_note: FieldNoteIdentity | None,
        captured_note_byte_count: int | None,
        a1_capture_commit: (
            FieldNoteCreatorLiveA1CaptureCommitReceipt | None
        ),
        a1_proposal_diagnostic: FieldNoteA1ProposalDiagnostic | None,
        a3_reuse_event_id: str | None,
        current_stage: TraceStage | None,
        events: tuple[FieldNoteWholeFlowTraceEvent, ...],
        state: CreatorLiveAttemptState,
        failure_boundary: WholeFlowBoundary | None,
        failure_reason: str | None,
        repair_action: RepairAction,
        journal_record_count: int,
        journal_byte_length: int,
        journal_chain_head_sha256: str,
        journal_sha256: str,
        anchor_record_count: int,
        anchor_chain_head_sha256: str,
        anchor_sha256: str,
        durable_readback_verified: bool,
    ) -> FieldNoteCreatorLiveTraceReadback:
        if authority is not _READBACK_AUTHORITY:
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live read-back authority is invalid."
            )
        value = object.__new__(cls)
        fields = {
            "schema": CREATOR_LIVE_READBACK_SCHEMA,
            "attempt": attempt,
            "source_repository": source_repository,
            "runtime": runtime,
            "runtime_provenance": runtime_provenance,
            "run_1": run_1,
            "run_2": run_2,
            "captured_note": captured_note,
            "captured_note_byte_count": captured_note_byte_count,
            "a1_capture_commit": a1_capture_commit,
            "a1_proposal_diagnostic": a1_proposal_diagnostic,
            "a3_reuse_event_id": a3_reuse_event_id,
            "current_stage": current_stage,
            "trace_event_count": len(events),
            "trace_chain_head_sha256": (
                events[-1].trace_sha256 if events else TRACE_GENESIS_SHA256
            ),
            "events": events,
            "state": state,
            "failure_boundary": failure_boundary,
            "failure_reason": failure_reason,
            "repair_action": repair_action,
            "one_attempt_no_retry": True,
            "journal_record_count": journal_record_count,
            "journal_byte_length": journal_byte_length,
            "journal_chain_head_sha256": journal_chain_head_sha256,
            "journal_sha256": journal_sha256,
            "anchor_record_count": anchor_record_count,
            "anchor_chain_head_sha256": anchor_chain_head_sha256,
            "anchor_sha256": anchor_sha256,
            "durable_readback_verified": durable_readback_verified,
        }
        for field, item in fields.items():
            object.__setattr__(value, field, item)
        return value

    @property
    def proof_attempt_id(self) -> str:
        return self.attempt.proof_attempt_id

    @property
    def creator_id(self) -> str:
        return self.attempt.creator_id

    def _body(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "attempt": self.attempt.as_dict(),
            "source_repository": self.source_repository.as_dict(),
            "runtime": _runtime_as_dict(self.runtime),
            "runtime_provenance": self.runtime_provenance.as_dict(),
            "run_1": self.run_1.as_dict(),
            "run_2": self.run_2.as_dict() if self.run_2 else None,
            "captured_note": (
                self.captured_note.as_dict() if self.captured_note else None
            ),
            "captured_note_byte_count": self.captured_note_byte_count,
            "a1_capture_commit": (
                self.a1_capture_commit.as_dict()
                if self.a1_capture_commit
                else None
            ),
            "a1_proposal_diagnostic": (
                self.a1_proposal_diagnostic.as_dict()
                if self.a1_proposal_diagnostic
                else None
            ),
            "a3_reuse_event_id": self.a3_reuse_event_id,
            "current_stage": self.current_stage,
            "trace_event_count": self.trace_event_count,
            "trace_chain_head_sha256": self.trace_chain_head_sha256,
            "events": [event.as_dict() for event in self.events],
            "state": self.state,
            "failure_boundary": self.failure_boundary,
            "failure_reason": self.failure_reason,
            "repair_action": self.repair_action,
            "one_attempt_no_retry": self.one_attempt_no_retry,
            "journal_record_count": self.journal_record_count,
            "journal_byte_length": self.journal_byte_length,
            "journal_chain_head_sha256": self.journal_chain_head_sha256,
            "journal_sha256": self.journal_sha256,
            "anchor_record_count": self.anchor_record_count,
            "anchor_chain_head_sha256": self.anchor_chain_head_sha256,
            "anchor_sha256": self.anchor_sha256,
            "durable_readback_verified": self.durable_readback_verified,
        }

    @property
    def readback_sha256(self) -> str:
        return _canonical_sha256(self._body())

    def as_dict(self) -> dict[str, Any]:
        return {**self._body(), "readback_sha256": self.readback_sha256}

    def matches_admission(
        self,
        *,
        attempt: FieldNoteWholeFlowAttempt | FieldNoteCreatorLiveAttempt,
        source_repository: FieldNoteSourceRepositoryIdentity,
        runtime: CodexRuntimeIdentity,
        run_1: FieldNoteWholeFlowRunIdentity,
        run_2: FieldNoteWholeFlowRunIdentity,
        proof_trace: tuple[FieldNoteWholeFlowTraceEvent, ...],
    ) -> bool:
        return (
            self.state == "TRACE_COMPLETE"
            and self.durable_readback_verified
            and self.failure_boundary is None
            and self.failure_reason is None
            and self.repair_action == "NONE"
            and self.attempt == attempt
            and self.source_repository == source_repository
            and self.runtime == runtime
            and self.run_1 == run_1
            and self.run_2 == run_2
            and self.a3_reuse_event_id is not None
            and self.events == proof_trace
            and self.trace_event_count == len(_STAGES)
            and self.trace_chain_head_sha256 == proof_trace[-1].trace_sha256
            and self.anchor_record_count
            == self.journal_record_count
            - (
                1
                if self.schema
                in {
                    CREATOR_LIVE_READBACK_SCHEMA_V2,
                    CREATOR_LIVE_READBACK_SCHEMA_V3,
                }
                else 0
            )
            and self.journal_byte_length > 0
            and all(
                event.runtime_provenance == self.runtime_provenance
                for event in proof_trace
            )
        )


@dataclass(frozen=True, init=False)
class FieldNoteCreatorLiveTraceReadbackV2(FieldNoteCreatorLiveTraceReadback):
    """Forward-only readback with runtime-owned opening and terminal time."""

    attempt: FieldNoteCreatorLiveAttempt
    authorization_observed_at: str
    attempt_opened_at: str
    terminal_proof_as_of: str | None
    last_admitted_observation: str | None

    @classmethod
    def _create_v2(
        cls,
        *,
        authorization_observed_at: str,
        attempt_opened_at: str,
        terminal_proof_as_of: str | None,
        **kwargs: Any,
    ) -> FieldNoteCreatorLiveTraceReadbackV2:
        attempt = kwargs.get("attempt")
        if not isinstance(attempt, FieldNoteCreatorLiveAttempt):
            raise FieldNoteCreatorLiveValidationError(
                "v0.2 read-back attempt identity is invalid."
            )
        value = super()._create(**kwargs)
        assert isinstance(value, cls)
        events = value.events
        object.__setattr__(value, "schema", CREATOR_LIVE_READBACK_SCHEMA_V2)
        object.__setattr__(
            value,
            "authorization_observed_at",
            authorization_observed_at,
        )
        object.__setattr__(value, "attempt_opened_at", attempt_opened_at)
        object.__setattr__(value, "terminal_proof_as_of", terminal_proof_as_of)
        object.__setattr__(
            value,
            "last_admitted_observation",
            events[-1].observed_at if events else None,
        )
        return value

    def _body(self) -> dict[str, Any]:
        return {
            **super()._body(),
            "authorization_observed_at": self.authorization_observed_at,
            "attempt_opened_at": self.attempt_opened_at,
            "terminal_proof_as_of": self.terminal_proof_as_of,
            "last_admitted_observation": self.last_admitted_observation,
        }

    def matches_admission(
        self,
        *,
        attempt: FieldNoteWholeFlowAttempt | FieldNoteCreatorLiveAttempt,
        source_repository: FieldNoteSourceRepositoryIdentity,
        runtime: CodexRuntimeIdentity,
        run_1: FieldNoteWholeFlowRunIdentity,
        run_2: FieldNoteWholeFlowRunIdentity,
        proof_trace: tuple[FieldNoteWholeFlowTraceEvent, ...],
    ) -> bool:
        if self.terminal_proof_as_of is None or not proof_trace:
            return False
        _, terminal_time = _parse_time(
            self.terminal_proof_as_of,
            "Terminal Proof As-of",
        )
        _, last_time = _parse_time(
            proof_trace[-1].observed_at,
            "Last admitted observation",
        )
        return (
            super().matches_admission(
                attempt=attempt,
                source_repository=source_repository,
                runtime=runtime,
                run_1=run_1,
                run_2=run_2,
                proof_trace=proof_trace,
            )
            and self.authorization_observed_at
            == self.attempt.authorization_observed_at
            and self.last_admitted_observation == proof_trace[-1].observed_at
            and last_time <= terminal_time
        )


@dataclass(frozen=True, init=False)
class FieldNoteCreatorLiveTraceReadbackV3(FieldNoteCreatorLiveTraceReadbackV2):
    """Forward-only content-free output and compiler audit projection."""

    terminal_projection_binding: FieldNoteCreatorLiveTerminalProjectionBinding
    run_2_output_identity: FieldNoteCreatorLiveRun2OutputIdentity | None
    a3_compiler_audit: FieldNoteCreatorLiveA3CompilerAudit | None

    @classmethod
    def _create_v3(
        cls,
        *,
        terminal_projection_binding: FieldNoteCreatorLiveTerminalProjectionBinding,
        run_2_output_identity: FieldNoteCreatorLiveRun2OutputIdentity | None,
        a3_compiler_audit: FieldNoteCreatorLiveA3CompilerAudit | None,
        **kwargs: Any,
    ) -> FieldNoteCreatorLiveTraceReadbackV3:
        if not isinstance(
            terminal_projection_binding,
            FieldNoteCreatorLiveTerminalProjectionBinding,
        ):
            raise FieldNoteCreatorLiveValidationError(
                "v0.3 terminal projection binding is invalid."
            )
        value = super()._create_v2(**kwargs)
        assert isinstance(value, cls)
        object.__setattr__(value, "schema", CREATOR_LIVE_READBACK_SCHEMA_V3)
        object.__setattr__(
            value,
            "terminal_projection_binding",
            terminal_projection_binding,
        )
        object.__setattr__(value, "run_2_output_identity", run_2_output_identity)
        object.__setattr__(value, "a3_compiler_audit", a3_compiler_audit)
        return value

    def _body(self) -> dict[str, Any]:
        return {
            **super()._body(),
            "terminal_projection_binding": (
                self.terminal_projection_binding.as_dict()
            ),
            "run_2_output_identity": (
                self.run_2_output_identity.as_dict()
                if self.run_2_output_identity is not None
                else None
            ),
            "a3_compiler_audit": (
                self.a3_compiler_audit.as_dict()
                if self.a3_compiler_audit is not None
                else None
            ),
        }


@dataclass(frozen=True)
class _StaticIdentity:
    attempt: FieldNoteWholeFlowAttempt | FieldNoteCreatorLiveAttempt
    repository: FieldNoteSourceRepositoryIdentity
    runtime: CodexRuntimeIdentity
    run_1: FieldNoteWholeFlowRunIdentity
    provenance: FieldNoteCreatorLiveRuntimeProvenance
    journal_schema: str
    record_schema: str
    anchor_schema: str
    attempt_opened_at: str | None
    terminal_projection_binding: (
        FieldNoteCreatorLiveTerminalProjectionBinding | None
    )


def _static_identity(records: tuple[_JournalRecord, ...]) -> _StaticIdentity:
    if not records or records[0].kind != "ATTEMPT_OPENED":
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_RECORD_MISSING",
            repair_action="EVIDENCE_DELETION",
        )
    payload = records[0].payload
    if records[0].schema in {
        CREATOR_LIVE_RECORD_SCHEMA_V2,
        CREATOR_LIVE_RECORD_SCHEMA_V3,
    }:
        is_v3 = records[0].schema == CREATOR_LIVE_RECORD_SCHEMA_V3
        required_fields = {
            "journal_schema",
            "attempt",
            "attempt_opened_at",
            "source_repository",
            "runtime",
            "run_1_id",
            "one_attempt_no_retry",
        }
        if is_v3:
            required_fields.add("terminal_projection_binding")
        expected_journal_schema = (
            CREATOR_LIVE_JOURNAL_SCHEMA_V3
            if is_v3
            else CREATOR_LIVE_JOURNAL_SCHEMA_V2
        )
        if set(payload) != required_fields or payload["journal_schema"] != (
            expected_journal_schema
        ):
            raise _JournalIntegrityError(
                "CREATOR_LIVE_ATTEMPT_RECORD_INVALID",
                repair_action="RECEIPT_REWRITE",
            )
        if payload["one_attempt_no_retry"] is not True:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_RETRY_BOUNDARY_INVALID",
                repair_action="RETRY_REPLACEMENT",
            )
        if len(records) < 2 or records[1].kind != "RUN_1_OPENED":
            raise _JournalIntegrityError(
                "CREATOR_LIVE_RUN_1_RECORD_MISSING",
                repair_action="EVIDENCE_DELETION",
            )
        run_payload = records[1].payload
        if set(run_payload) != {"run_1", "runtime_provenance"}:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_RUN_1_RECORD_INVALID",
                repair_action="RECEIPT_REWRITE",
            )
        attempt = _attempt_v2_from_dict(payload["attempt"])
        repository = _repository_from_dict(payload["source_repository"])
        runtime = _runtime_from_dict(payload["runtime"])
        run_1 = _run_from_dict(
            run_payload["run_1"],
            repository=repository,
            runtime=runtime,
        )
        if (
            run_1.proof_attempt_id != attempt.proof_attempt_id
            or run_1.run_id != payload["run_1_id"]
        ):
            raise _JournalIntegrityError(
                "CREATOR_LIVE_RUN_ATTEMPT_MISMATCH",
                repair_action="RECEIPT_REWRITE",
            )
        opened_at, opened_time = _parse_time(
            payload["attempt_opened_at"],
            "Attempt opening time",
        )
        _, authorization_time = _parse_time(
            attempt.authorization_observed_at,
            "Authorization observation",
        )
        _, run_time = _parse_time(run_1.started_at, "Run 1 start")
        if authorization_time > opened_time or opened_time >= run_time:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_OPENING_CHRONOLOGY_INVALID",
                repair_action="TIMESTAMP_CHANGE",
            )
        provenance = _provenance_from_dict(
            run_payload["runtime_provenance"],
            attempt=attempt,
            repository=repository,
            runtime=runtime,
            run_1=run_1,
        )
        terminal_projection_binding = None
        if is_v3:
            try:
                terminal_projection_binding = (
                    FieldNoteCreatorLiveTerminalProjectionBinding.from_dict(
                        payload["terminal_projection_binding"]
                    )
                )
            except FieldNoteCreatorLiveValidationError as exc:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_TERMINAL_PROJECTION_BINDING_INVALID",
                    repair_action="RECEIPT_REWRITE",
                ) from exc
            _, implementation_authorization_time = _parse_time(
                terminal_projection_binding.implementation_authorization_observed_at,
                "Implementation authorization observation",
            )
            if (
                implementation_authorization_time > opened_time
                or not attempt.proof_attempt_id.endswith(
                    "_" + terminal_projection_binding.launch_binding_sha256
                )
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_TERMINAL_PROJECTION_BINDING_MISMATCH",
                    repair_action="RECEIPT_REWRITE",
                )
        return _StaticIdentity(
            attempt=attempt,
            repository=repository,
            runtime=runtime,
            run_1=run_1,
            provenance=provenance,
            journal_schema=expected_journal_schema,
            record_schema=(
                CREATOR_LIVE_RECORD_SCHEMA_V3
                if is_v3
                else CREATOR_LIVE_RECORD_SCHEMA_V2
            ),
            anchor_schema=(
                CREATOR_LIVE_ANCHOR_SCHEMA_V3
                if is_v3
                else CREATOR_LIVE_ANCHOR_SCHEMA_V2
            ),
            attempt_opened_at=opened_at,
            terminal_projection_binding=terminal_projection_binding,
        )
    if set(payload) != {
        "journal_schema",
        "attempt",
        "source_repository",
        "runtime",
        "run_1",
        "runtime_provenance",
        "one_attempt_no_retry",
    } or payload["journal_schema"] != CREATOR_LIVE_JOURNAL_SCHEMA:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_ATTEMPT_RECORD_INVALID",
            repair_action="RECEIPT_REWRITE",
        )
    if payload["one_attempt_no_retry"] is not True:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RETRY_BOUNDARY_INVALID",
            repair_action="RETRY_REPLACEMENT",
        )
    attempt = _attempt_from_dict(payload["attempt"])
    repository = _repository_from_dict(payload["source_repository"])
    runtime = _runtime_from_dict(payload["runtime"])
    run_1 = _run_from_dict(
        payload["run_1"],
        repository=repository,
        runtime=runtime,
    )
    if run_1.proof_attempt_id != attempt.proof_attempt_id:
        raise _JournalIntegrityError(
            "CREATOR_LIVE_RUN_ATTEMPT_MISMATCH",
            repair_action="RECEIPT_REWRITE",
        )
    provenance = _provenance_from_dict(
        payload["runtime_provenance"],
        attempt=attempt,
        repository=repository,
        runtime=runtime,
        run_1=run_1,
    )
    return _StaticIdentity(
        attempt=attempt,
        repository=repository,
        runtime=runtime,
        run_1=run_1,
        provenance=provenance,
        journal_schema=CREATOR_LIVE_JOURNAL_SCHEMA,
        record_schema=CREATOR_LIVE_RECORD_SCHEMA,
        anchor_schema=CREATOR_LIVE_ANCHOR_SCHEMA,
        attempt_opened_at=None,
        terminal_projection_binding=None,
    )


def _project_records(
    journal_raw: bytes,
    records: tuple[_JournalRecord, ...],
    anchor_raw: bytes,
    anchors: tuple[_AnchorRecord, ...],
    static: _StaticIdentity,
) -> FieldNoteCreatorLiveTraceReadback:
    _verify_journal_anchor(
        journal_raw,
        records,
        anchors,
        proof_attempt_id=static.attempt.proof_attempt_id,
    )
    if any(anchor.schema != static.anchor_schema for anchor in anchors):
        raise _JournalIntegrityError(
            "CREATOR_LIVE_DURABLE_SCHEMA_MISMATCH",
            repair_action="RECEIPT_REWRITE",
        )
    run_2: FieldNoteWholeFlowRunIdentity | None = None
    events: list[FieldNoteWholeFlowTraceEvent] = []
    captured_note: FieldNoteIdentity | None = None
    captured_note_byte_count: int | None = None
    a1_capture_commit: FieldNoteCreatorLiveA1CaptureCommitReceipt | None = None
    a1_proposal_diagnostic: FieldNoteA1ProposalDiagnostic | None = None
    run_2_output_identity: FieldNoteCreatorLiveRun2OutputIdentity | None = None
    a3_compiler_audit: FieldNoteCreatorLiveA3CompilerAudit | None = None
    a3_reuse_event_id: str | None = None
    state: CreatorLiveAttemptState = "OPEN"
    failure_boundary: WholeFlowBoundary | None = None
    failure_reason: str | None = None
    repair_action: RepairAction = "NONE"
    terminal_proof_as_of: str | None = None
    previous_trace = TRACE_GENESIS_SHA256

    start_index = (
        2
        if static.journal_schema
        in {CREATOR_LIVE_JOURNAL_SCHEMA_V2, CREATOR_LIVE_JOURNAL_SCHEMA_V3}
        else 1
    )
    for record in records[start_index:]:
        if state in {"FAILED", "TRACE_COMPLETE"}:
            raise _JournalIntegrityError(
                "CREATOR_LIVE_TERMINAL_STATE_EXTENDED",
                repair_action="RETRY_REPLACEMENT",
            )
        payload = record.payload
        if record.kind == "RUN_2_OPENED":
            if run_2 is not None or len(events) != 1:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_2_ORDER_INVALID",
                    repair_action="RETRY_REPLACEMENT",
                )
            if set(payload) != {"run_2"}:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_2_RECORD_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            run_2 = _run_from_dict(
                payload["run_2"],
                repository=static.repository,
                runtime=static.runtime,
            )
            if (
                run_2.proof_attempt_id != static.attempt.proof_attempt_id
                or run_2.run_id == static.run_1.run_id
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_2_IDENTITY_INVALID",
                    repair_action="RETRY_REPLACEMENT",
                )
            _, run_1_time = _parse_time(
                static.run_1.started_at,
                "Run 1 start",
            )
            _, run_2_time = _parse_time(run_2.started_at, "Run 2 start")
            if run_2_time <= run_1_time:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_ORDER_INVALID",
                    repair_action="TIMESTAMP_CHANGE",
                )
            continue
        if record.kind == "RUN_2_OUTPUT_IDENTITY_RECORDED":
            if (
                static.journal_schema != CREATOR_LIVE_JOURNAL_SCHEMA_V3
                or run_2 is None
                or len(events) != 2
                or run_2_output_identity is not None
                or a3_compiler_audit is not None
                or static.terminal_projection_binding is None
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_2_OUTPUT_ORDER_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            try:
                candidate_output_identity = (
                    FieldNoteCreatorLiveRun2OutputIdentity.from_dict(payload)
                )
            except FieldNoteCreatorLiveValidationError as exc:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_2_OUTPUT_IDENTITY_INVALID",
                    repair_action="RECEIPT_REWRITE",
                ) from exc
            expected_task = static.terminal_projection_binding.run_2_task
            if (
                candidate_output_identity.proof_attempt_id
                != static.attempt.proof_attempt_id
                or candidate_output_identity.run_id != run_2.run_id
                or candidate_output_identity.task_byte_count
                != expected_task.byte_count
                or candidate_output_identity.task_sha256 != expected_task.sha256
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_RUN_2_OUTPUT_IDENTITY_MISMATCH",
                    repair_action="RECEIPT_REWRITE",
                )
            run_2_output_identity = candidate_output_identity
            continue
        if record.kind == "A3_COMPILER_AUDIT_RECORDED":
            if (
                static.journal_schema != CREATOR_LIVE_JOURNAL_SCHEMA_V3
                or run_2 is None
                or len(events) != 2
                or run_2_output_identity is None
                or a3_compiler_audit is not None
                or captured_note is None
                or captured_note_byte_count is None
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_A3_COMPILER_AUDIT_ORDER_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            try:
                candidate_audit = FieldNoteCreatorLiveA3CompilerAudit.from_dict(
                    payload
                )
            except FieldNoteCreatorLiveValidationError as exc:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_A3_COMPILER_AUDIT_INVALID",
                    repair_action="RECEIPT_REWRITE",
                ) from exc
            if (
                candidate_audit.proof_attempt_id
                != static.attempt.proof_attempt_id
                or candidate_audit.run_id != run_2.run_id
                or candidate_audit.output_artifact_id
                != run_2_output_identity.output_artifact.artifact_id
                or candidate_audit.output_byte_count
                != run_2_output_identity.final_output_byte_count
                or candidate_audit.output_sha256
                != run_2_output_identity.final_output_sha256
                or candidate_audit.source_note_byte_count
                != captured_note_byte_count
                or candidate_audit.source_note_sha256 != captured_note.note_sha256
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_A3_COMPILER_AUDIT_MISMATCH",
                    repair_action="RECEIPT_REWRITE",
                )
            a3_compiler_audit = candidate_audit
            continue
        if record.kind == "CHECKPOINT":
            if set(payload) != {"event", "binding"}:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_CHECKPOINT_RECORD_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            event = _event_from_dict(
                payload["event"],
                attempt=static.attempt,
                repository=static.repository,
                runtime=static.runtime,
                provenance=static.provenance,
            )
            index = len(events)
            expected_run = (
                static.run_1.run_id
                if index == 0
                else run_2.run_id if run_2 else None
            )
            binding = payload["binding"]
            if (
                index >= len(_STAGES)
                or event.sequence != index
                or event.stage != _STAGES[index]
                or event.run_id != expected_run
                or event.previous_trace_sha256 != previous_trace
                or event.repair_action != "NONE"
                or not isinstance(binding, dict)
                or binding.get("evidence_sha256") != event.evidence_sha256
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_CHECKPOINT_ORDER_OR_IDENTITY_INVALID",
                    repair_action="EVENT_ID_CHANGE",
                )
            if index == 0:
                if set(binding) != {
                    "evidence_type",
                    "evidence_sha256",
                    "a1_draft_sha256",
                    "note",
                    "note_byte_count",
                    "capture_commit",
                    "capture_commit_sha256",
                } or binding["evidence_type"] != (
                    "FieldNoteCreatorLiveA1CaptureCommitReceipt"
                ):
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A1_BINDING_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    )
                captured_note = _note_from_dict(binding["note"])
                count = binding["note_byte_count"]
                if type(count) is not int or count <= 0:
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A1_BYTE_COUNT_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    )
                captured_note_byte_count = count
                a1_capture_commit = _a1_capture_commit_from_dict(
                    binding["capture_commit"]
                )
                if (
                    binding["capture_commit_sha256"]
                    != a1_capture_commit.receipt_sha256
                    or binding["evidence_sha256"]
                    != a1_capture_commit.receipt_sha256
                    or binding["a1_draft_sha256"]
                    != a1_capture_commit.draft_evidence_sha256
                    or a1_capture_commit.note != captured_note
                    or a1_capture_commit.note_byte_count != count
                    or a1_capture_commit.proof_attempt_id
                    != static.attempt.proof_attempt_id
                    or a1_capture_commit.run_id != static.run_1.run_id
                    or a1_capture_commit.source_repository
                    != static.repository
                    or a1_capture_commit.actual_runtime_identity
                    != static.runtime
                    or not _a1_capture_chronology_is_valid(
                        run_1_started_at=static.run_1.started_at,
                        draft_created_at=(
                            a1_capture_commit.draft_created_at
                        ),
                        save_as_of=a1_capture_commit.save_as_of,
                        observed_at=event.observed_at,
                        proof_as_of=(
                            static.attempt.proof_as_of
                            if isinstance(
                                static.attempt,
                                FieldNoteWholeFlowAttempt,
                            )
                            else None
                        ),
                    )
                ):
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A1_CAPTURE_COMMIT_MISMATCH",
                        repair_action="RECEIPT_REWRITE",
                    )
            elif index == 2:
                if static.journal_schema == CREATOR_LIVE_JOURNAL_SCHEMA_V3 and (
                    run_2_output_identity is None
                    or a3_compiler_audit is None
                    or a3_compiler_audit.winning_candidate_count != 1
                    or a3_compiler_audit.terminal_a3_code is not None
                ):
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A3_DURABLE_AUDIT_MISSING",
                        repair_action="EVIDENCE_DELETION",
                    )
                if set(binding) != {
                    "evidence_type",
                    "evidence_sha256",
                    "reuse_event_id",
                } or binding["evidence_type"] != "FieldNoteReuseReceipt":
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A3_BINDING_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    )
                reuse_event_id = binding["reuse_event_id"]
                if (
                    not isinstance(reuse_event_id, str)
                    or len(reuse_event_id) != 64
                    or any(
                        character not in "0123456789abcdef"
                        for character in reuse_event_id
                    )
                ):
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A3_BINDING_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    )
                a3_reuse_event_id = reuse_event_id
            elif set(binding) != {"evidence_type", "evidence_sha256"}:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_STAGE_BINDING_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            events.append(event)
            previous_trace = event.trace_sha256
            continue
        if record.kind == "ATTEMPT_FAILED":
            legacy_fields = {
                "failure_boundary",
                "failure_reason",
                "repair_action",
            }
            diagnostic_fields = legacy_fields | {
                "proof_attempt_id",
                "run_id",
                "proposal_diagnostic",
                "proposal_diagnostic_sha256",
            }
            if static.journal_schema in {
                CREATOR_LIVE_JOURNAL_SCHEMA_V2,
                CREATOR_LIVE_JOURNAL_SCHEMA_V3,
            }:
                legacy_fields = legacy_fields | {"proof_as_of"}
                diagnostic_fields = diagnostic_fields | {"proof_as_of"}
            if set(payload) not in {
                frozenset(legacy_fields),
                frozenset(diagnostic_fields),
            }:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_FAILURE_RECORD_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            boundary = payload["failure_boundary"]
            action = payload["repair_action"]
            if boundary not in {
                "RUNTIME_ENFORCEMENT",
                "A1_CAPTURE",
                "RUN_SEPARATION",
                "MODEL_IDENTITY",
                "REPOSITORY_IDENTITY",
                "A2_RECONNECT",
                "A3_REUSE",
                "A4_DURABILITY",
                "A5_CONFIRMATION",
                "A6_REVIEW",
                "HUMAN_REPAIR",
                "PROOF_AS_OF",
            } or action not in {
                "NONE",
                "NOTE_EDIT",
                "EVIDENCE_MANUFACTURE",
                "RECEIPT_REWRITE",
                "LEDGER_REWRITE",
                "EVENT_ID_CHANGE",
                "TIMESTAMP_CHANGE",
                "EVIDENCE_DELETION",
                "RETRY_REPLACEMENT",
            }:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_FAILURE_RECORD_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            state = "FAILED"
            failure_boundary = boundary
            failure_reason = _bounded_reason(payload["failure_reason"])
            repair_action = action
            if static.journal_schema in {
                CREATOR_LIVE_JOURNAL_SCHEMA_V2,
                CREATOR_LIVE_JOURNAL_SCHEMA_V3,
            }:
                terminal_proof_as_of, terminal_time = _parse_time(
                    payload["proof_as_of"],
                    "Terminal Proof As-of",
                )
                lower_bound = (
                    events[-1].observed_at
                    if events
                    else static.attempt_opened_at
                )
                assert lower_bound is not None
                _, lower_time = _parse_time(
                    lower_bound,
                    "Last admitted observation",
                )
                if terminal_time < lower_time:
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_TERMINAL_CUTOFF_INVALID",
                        repair_action="TIMESTAMP_CHANGE",
                    )
            if (
                static.journal_schema == CREATOR_LIVE_JOURNAL_SCHEMA_V3
                and boundary == "A3_REUSE"
                and failure_reason
                in {
                    "A3_EXACT_STRUCTURE_MISSING",
                    "A3_EXACT_STRUCTURE_AMBIGUOUS",
                }
                and (
                    a3_compiler_audit is None
                    or a3_compiler_audit.terminal_a3_code != failure_reason
                )
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_A3_TERMINAL_AUDIT_MISMATCH",
                    repair_action="RECEIPT_REWRITE",
                )
            if set(payload) == diagnostic_fields:
                if (
                    boundary != "A1_CAPTURE"
                    or payload["proof_attempt_id"]
                    != static.attempt.proof_attempt_id
                    or payload["run_id"] != static.run_1.run_id
                ):
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A1_DIAGNOSTIC_BINDING_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    )
                try:
                    diagnostic = FieldNoteA1ProposalDiagnostic.from_dict(
                        payload["proposal_diagnostic"]
                    )
                except ValueError as exc:
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A1_DIAGNOSTIC_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    ) from exc
                if (
                    payload["proposal_diagnostic_sha256"]
                    != diagnostic.diagnostic_sha256
                    or not _proposal_diagnostic_reason_matches(
                        diagnostic,
                        failure_reason,
                    )
                ):
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_A1_DIAGNOSTIC_IDENTITY_INVALID",
                        repair_action="RECEIPT_REWRITE",
                    )
                a1_proposal_diagnostic = diagnostic
            continue
        if record.kind == "TRACE_COMPLETED":
            completion_fields = {
                "trace_event_count",
                "trace_chain_head_sha256",
                "runtime_provenance_id",
                "no_repair_verified",
            }
            if static.journal_schema in {
                CREATOR_LIVE_JOURNAL_SCHEMA_V2,
                CREATOR_LIVE_JOURNAL_SCHEMA_V3,
            }:
                completion_fields.add("proof_as_of")
            if set(payload) != completion_fields or (
                len(events) != len(_STAGES)
                or run_2 is None
                or a3_reuse_event_id is None
                or (
                    static.journal_schema == CREATOR_LIVE_JOURNAL_SCHEMA_V3
                    and (
                        run_2_output_identity is None
                        or a3_compiler_audit is None
                        or a3_compiler_audit.winning_candidate_count != 1
                        or a3_compiler_audit.terminal_a3_code is not None
                    )
                )
                or payload["trace_event_count"] != len(_STAGES)
                or payload["trace_chain_head_sha256"] != previous_trace
                or payload["runtime_provenance_id"]
                != static.provenance.runtime_provenance_id
                or payload["no_repair_verified"] is not True
            ):
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_COMPLETION_RECORD_INVALID",
                    repair_action="RECEIPT_REWRITE",
                )
            if static.journal_schema in {
                CREATOR_LIVE_JOURNAL_SCHEMA_V2,
                CREATOR_LIVE_JOURNAL_SCHEMA_V3,
            }:
                terminal_proof_as_of, terminal_time = _parse_time(
                    payload["proof_as_of"],
                    "Terminal Proof As-of",
                )
                _, last_time = _parse_time(
                    events[-1].observed_at,
                    "Last admitted observation",
                )
                if terminal_time < last_time:
                    raise _JournalIntegrityError(
                        "CREATOR_LIVE_TERMINAL_CUTOFF_INVALID",
                        repair_action="TIMESTAMP_CHANGE",
                    )
            state = "TRACE_COMPLETE"
            continue
        raise _JournalIntegrityError(
            "CREATOR_LIVE_JOURNAL_ORDER_INVALID",
            repair_action="RECEIPT_REWRITE",
        )

    current_stage = (
        _STAGES[len(events)]
        if state == "OPEN" and len(events) < len(_STAGES)
        else None
    )
    readback_fields = dict(
        authority=_READBACK_AUTHORITY,
        attempt=static.attempt,
        source_repository=static.repository,
        runtime=static.runtime,
        runtime_provenance=static.provenance,
        run_1=static.run_1,
        run_2=run_2,
        captured_note=captured_note,
        captured_note_byte_count=captured_note_byte_count,
        a1_capture_commit=a1_capture_commit,
        a1_proposal_diagnostic=a1_proposal_diagnostic,
        a3_reuse_event_id=a3_reuse_event_id,
        current_stage=current_stage,
        events=tuple(events),
        state=state,
        failure_boundary=failure_boundary,
        failure_reason=failure_reason,
        repair_action=repair_action,
        journal_record_count=len(records),
        journal_byte_length=len(journal_raw),
        journal_chain_head_sha256=records[-1].record_sha256,
        journal_sha256=hashlib.sha256(journal_raw).hexdigest(),
        anchor_record_count=len(anchors),
        anchor_chain_head_sha256=anchors[-1].anchor_sha256,
        anchor_sha256=hashlib.sha256(anchor_raw).hexdigest(),
        durable_readback_verified=True,
    )
    if static.journal_schema == CREATOR_LIVE_JOURNAL_SCHEMA_V3:
        assert isinstance(static.attempt, FieldNoteCreatorLiveAttempt)
        assert static.attempt_opened_at is not None
        assert static.terminal_projection_binding is not None
        return FieldNoteCreatorLiveTraceReadbackV3._create_v3(
            terminal_projection_binding=static.terminal_projection_binding,
            run_2_output_identity=run_2_output_identity,
            a3_compiler_audit=a3_compiler_audit,
            authorization_observed_at=(
                static.attempt.authorization_observed_at
            ),
            attempt_opened_at=static.attempt_opened_at,
            terminal_proof_as_of=terminal_proof_as_of,
            **readback_fields,
        )
    if static.journal_schema == CREATOR_LIVE_JOURNAL_SCHEMA_V2:
        assert isinstance(static.attempt, FieldNoteCreatorLiveAttempt)
        assert static.attempt_opened_at is not None
        return FieldNoteCreatorLiveTraceReadbackV2._create_v2(
            authorization_observed_at=(
                static.attempt.authorization_observed_at
            ),
            attempt_opened_at=static.attempt_opened_at,
            terminal_proof_as_of=terminal_proof_as_of,
            **readback_fields,
        )
    return FieldNoteCreatorLiveTraceReadback._create(**readback_fields)


def _failed_readback(
    *,
    journal_raw: bytes,
    anchor_raw: bytes,
    static: _StaticIdentity,
    reason: str,
    repair_action: RepairAction,
) -> FieldNoteCreatorLiveTraceReadback:
    fields = dict(
        authority=_READBACK_AUTHORITY,
        attempt=static.attempt,
        source_repository=static.repository,
        runtime=static.runtime,
        runtime_provenance=static.provenance,
        run_1=static.run_1,
        run_2=None,
        captured_note=None,
        captured_note_byte_count=None,
        a1_capture_commit=None,
        a1_proposal_diagnostic=None,
        a3_reuse_event_id=None,
        current_stage=None,
        events=(),
        state="FAILED",
        failure_boundary="RUNTIME_ENFORCEMENT",
        failure_reason=reason,
        repair_action=repair_action,
        journal_record_count=0,
        journal_byte_length=len(journal_raw),
        journal_chain_head_sha256=JOURNAL_GENESIS_SHA256,
        journal_sha256=hashlib.sha256(journal_raw).hexdigest(),
        anchor_record_count=0,
        anchor_chain_head_sha256=ANCHOR_GENESIS_SHA256,
        anchor_sha256=hashlib.sha256(anchor_raw).hexdigest(),
        durable_readback_verified=False,
    )
    if static.journal_schema == CREATOR_LIVE_JOURNAL_SCHEMA_V3:
        assert isinstance(static.attempt, FieldNoteCreatorLiveAttempt)
        assert static.attempt_opened_at is not None
        assert static.terminal_projection_binding is not None
        return FieldNoteCreatorLiveTraceReadbackV3._create_v3(
            terminal_projection_binding=static.terminal_projection_binding,
            run_2_output_identity=None,
            a3_compiler_audit=None,
            authorization_observed_at=(
                static.attempt.authorization_observed_at
            ),
            attempt_opened_at=static.attempt_opened_at,
            terminal_proof_as_of=None,
            **fields,
        )
    if static.journal_schema == CREATOR_LIVE_JOURNAL_SCHEMA_V2:
        assert isinstance(static.attempt, FieldNoteCreatorLiveAttempt)
        assert static.attempt_opened_at is not None
        return FieldNoteCreatorLiveTraceReadbackV2._create_v2(
            authorization_observed_at=(
                static.attempt.authorization_observed_at
            ),
            attempt_opened_at=static.attempt_opened_at,
            terminal_proof_as_of=None,
            **fields,
        )
    return FieldNoteCreatorLiveTraceReadback._create(**fields)


class FieldNoteCreatorLiveProofRuntime:
    """The only public path that can append creator-live checkpoints.

    Trust is bounded to this in-process implementation plus exact durable
    read-back. No signature, hardware root, separate observer, or adversarial
    local-process resistance is claimed.
    """

    def __init__(
        self,
        *,
        storage_root: Path,
        static: _StaticIdentity,
    ) -> None:
        self._storage_root = storage_root
        is_v2 = static.journal_schema == CREATOR_LIVE_JOURNAL_SCHEMA_V2
        is_v3 = static.journal_schema == CREATOR_LIVE_JOURNAL_SCHEMA_V3
        self._journal_path = storage_root / (
            CREATOR_LIVE_JOURNAL_FILENAME_V3
            if is_v3
            else (
                CREATOR_LIVE_JOURNAL_FILENAME_V2
                if is_v2
                else CREATOR_LIVE_JOURNAL_FILENAME
            )
        )
        self._anchor_path = storage_root / (
            CREATOR_LIVE_ANCHOR_FILENAME_V3
            if is_v3
            else (
                CREATOR_LIVE_ANCHOR_FILENAME_V2
                if is_v2
                else CREATOR_LIVE_ANCHOR_FILENAME
            )
        )
        self._static = static
        self._lock = threading.Lock()

    @property
    def journal_path(self) -> Path:
        return self._journal_path

    @property
    def anchor_path(self) -> Path:
        return self._anchor_path

    @classmethod
    def open_attempt(
        cls,
        storage_root: Path,
        *,
        attempt: FieldNoteCreatorLiveAttempt,
        source_repository: FieldNoteSourceRepositoryIdentity,
        run_1_id: str,
        runtime: CodexRuntimeIdentity,
        terminal_projection_binding: (
            FieldNoteCreatorLiveTerminalProjectionBinding | None
        ) = None,
    ) -> FieldNoteCreatorLiveProofRuntime:
        if not isinstance(attempt, FieldNoteCreatorLiveAttempt):
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live runtime requires a forward-only attempt."
            )
        if not isinstance(
            source_repository,
            FieldNoteSourceRepositoryIdentity,
        ) or not isinstance(runtime, CodexRuntimeIdentity):
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live runtime identity is not typed."
            )
        is_v3 = terminal_projection_binding is not None
        if is_v3 and not isinstance(
            terminal_projection_binding,
            FieldNoteCreatorLiveTerminalProjectionBinding,
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live terminal projection binding is not typed."
            )
        if is_v3 and not attempt.proof_attempt_id.endswith(
            "_" + terminal_projection_binding.launch_binding_sha256
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live launch binding does not match the attempt."
            )
        if (
            not isinstance(run_1_id, str)
            or not run_1_id.strip()
            or len(run_1_id) > 256
            or "\x00" in run_1_id
        ):
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live Run 1 ID is invalid."
            )
        run_1_id = run_1_id.strip()
        root = Path(storage_root)
        if not root.is_absolute():
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live storage root must be absolute."
            )
        if root.exists() and root.is_symlink():
            raise FieldNoteCreatorLiveValidationError(
                "Creator-live storage root cannot be a symlink."
            )
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if any(
            (root / filename).exists()
            for filename in (
                CREATOR_LIVE_JOURNAL_FILENAME,
                CREATOR_LIVE_ANCHOR_FILENAME,
                CREATOR_LIVE_JOURNAL_FILENAME_V2,
                CREATOR_LIVE_ANCHOR_FILENAME_V2,
                CREATOR_LIVE_JOURNAL_FILENAME_V3,
                CREATOR_LIVE_ANCHOR_FILENAME_V3,
            )
        ):
            raise FieldNoteCreatorLiveAttemptExistsError(
                "Creator-live one-attempt storage already exists."
            )
        attempt_opened_at, opened_time = _parse_time(
            _utc_now_rfc3339(),
            "Attempt opening time",
        )
        _, authorization_time = _parse_time(
            attempt.authorization_observed_at,
            "Authorization observation",
        )
        if authorization_time > opened_time:
            raise FieldNoteCreatorLiveValidationError(
                "Authorization observation follows attempt opening."
            )
        run_1_started_at, run_time = _parse_time(
            _utc_now_rfc3339(),
            "Run 1 start",
        )
        if opened_time >= run_time:
            raise FieldNoteCreatorLiveValidationError(
                "Attempt opening must precede Run 1."
            )
        run_1 = FieldNoteWholeFlowRunIdentity(
            proof_attempt_id=attempt.proof_attempt_id,
            run_id=run_1_id,
            started_at=run_1_started_at,
            repository=source_repository,
            runtime=runtime,
        )
        provenance = FieldNoteCreatorLiveRuntimeProvenance._issue(
            authority=_RUNTIME_PROVENANCE_AUTHORITY,
            proof_attempt_id=attempt.proof_attempt_id,
            source_repository=source_repository,
            runtime=runtime,
            issued_for_run_1_id=run_1.run_id,
        )
        static = _StaticIdentity(
            attempt=attempt,
            repository=source_repository,
            runtime=runtime,
            run_1=run_1,
            provenance=provenance,
            journal_schema=(
                CREATOR_LIVE_JOURNAL_SCHEMA_V3
                if is_v3
                else CREATOR_LIVE_JOURNAL_SCHEMA_V2
            ),
            record_schema=(
                CREATOR_LIVE_RECORD_SCHEMA_V3
                if is_v3
                else CREATOR_LIVE_RECORD_SCHEMA_V2
            ),
            anchor_schema=(
                CREATOR_LIVE_ANCHOR_SCHEMA_V3
                if is_v3
                else CREATOR_LIVE_ANCHOR_SCHEMA_V2
            ),
            attempt_opened_at=attempt_opened_at,
            terminal_projection_binding=terminal_projection_binding,
        )
        payload = {
            "journal_schema": static.journal_schema,
            "attempt": attempt.as_dict(),
            "attempt_opened_at": attempt_opened_at,
            "source_repository": source_repository.as_dict(),
            "runtime": _runtime_as_dict(runtime),
            "run_1_id": run_1_id,
            "one_attempt_no_retry": True,
        }
        if terminal_projection_binding is not None:
            payload["terminal_projection_binding"] = (
                terminal_projection_binding.as_dict()
            )
        record = _JournalRecord.create(
            sequence=0,
            kind="ATTEMPT_OPENED",
            payload=payload,
            previous_record_sha256=JOURNAL_GENESIS_SHA256,
            schema=static.record_schema,
        )
        run_record = _JournalRecord.create(
            sequence=1,
            kind="RUN_1_OPENED",
            payload={
                "run_1": run_1.as_dict(),
                "runtime_provenance": provenance.as_dict(),
            },
            previous_record_sha256=record.record_sha256,
            schema=static.record_schema,
        )
        path = root / (
            CREATOR_LIVE_JOURNAL_FILENAME_V3
            if is_v3
            else CREATOR_LIVE_JOURNAL_FILENAME_V2
        )
        try:
            descriptor = os.open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError as exc:
            raise FieldNoteCreatorLiveAttemptExistsError(
                "Creator-live one-attempt journal already exists."
            ) from exc
        try:
            journal_raw = record.serialize_line() + run_record.serialize_line()
            written = os.write(descriptor, journal_raw)
            if written != len(journal_raw):
                raise FieldNoteCreatorLiveDurabilityError(
                    "Creator-live attempt record write was incomplete."
                )
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        anchor = _AnchorRecord.create(
            generation=0,
            proof_attempt_id=attempt.proof_attempt_id,
            journal_raw=journal_raw,
            journal_records=(record, run_record),
            previous_anchor_sha256=ANCHOR_GENESIS_SHA256,
            schema=static.anchor_schema,
        )
        anchor_path = root / (
            CREATOR_LIVE_ANCHOR_FILENAME_V3
            if is_v3
            else CREATOR_LIVE_ANCHOR_FILENAME_V2
        )
        try:
            anchor_descriptor = os.open(
                anchor_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError as exc:
            raise FieldNoteCreatorLiveAttemptExistsError(
                "Creator-live one-attempt anchor already exists."
            ) from exc
        try:
            anchor_line = anchor.serialize_line()
            anchor_written = os.write(anchor_descriptor, anchor_line)
            if anchor_written != len(anchor_line):
                raise FieldNoteCreatorLiveDurabilityError(
                    "Creator-live attempt anchor write was incomplete."
                )
            os.fsync(anchor_descriptor)
        finally:
            os.close(anchor_descriptor)
        directory = os.open(root, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        runtime_path = cls(storage_root=root, static=static)
        if not runtime_path.read_back().durable_readback_verified:
            raise FieldNoteCreatorLiveDurabilityError(
                "Creator-live attempt did not survive exact durable read-back."
            )
        return runtime_path

    @classmethod
    def load_attempt(
        cls,
        storage_root: Path,
    ) -> FieldNoteCreatorLiveProofRuntime:
        root = Path(storage_root)
        v3_path = root / CREATOR_LIVE_JOURNAL_FILENAME_V3
        v3_anchor = root / CREATOR_LIVE_ANCHOR_FILENAME_V3
        v2_path = root / CREATOR_LIVE_JOURNAL_FILENAME_V2
        v2_anchor = root / CREATOR_LIVE_ANCHOR_FILENAME_V2
        v1_path = root / CREATOR_LIVE_JOURNAL_FILENAME
        v1_anchor = root / CREATOR_LIVE_ANCHOR_FILENAME
        if v3_path.exists() or v3_anchor.exists():
            path, anchor_path = v3_path, v3_anchor
        elif v2_path.exists() or v2_anchor.exists():
            path, anchor_path = v2_path, v2_anchor
        else:
            path, anchor_path = v1_path, v1_anchor
        journal_raw = path.read_bytes()
        anchor_raw = anchor_path.read_bytes()
        records = _parse_records(journal_raw)
        static = _static_identity(records)
        anchors = _parse_anchors(anchor_raw)
        _verify_journal_anchor(
            journal_raw,
            records,
            anchors,
            proof_attempt_id=static.attempt.proof_attempt_id,
        )
        return cls(storage_root=root, static=static)

    def _read_raw_locked(self, descriptor: int) -> bytes:
        os.lseek(descriptor, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)

    def read_back(self) -> FieldNoteCreatorLiveTraceReadback:
        with self._lock:
            journal_descriptor = os.open(self._journal_path, os.O_RDONLY)
            try:
                try:
                    anchor_descriptor = os.open(self._anchor_path, os.O_RDONLY)
                except OSError:
                    return _failed_readback(
                        journal_raw=self._read_raw_locked(journal_descriptor),
                        anchor_raw=b"",
                        static=self._static,
                        reason="CREATOR_LIVE_DURABLE_ANCHOR_MISSING",
                        repair_action="EVIDENCE_DELETION",
                    )
                try:
                    fcntl.flock(journal_descriptor, fcntl.LOCK_SH)
                    fcntl.flock(anchor_descriptor, fcntl.LOCK_SH)
                    journal_raw = self._read_raw_locked(journal_descriptor)
                    anchor_raw = self._read_raw_locked(anchor_descriptor)
                finally:
                    fcntl.flock(anchor_descriptor, fcntl.LOCK_UN)
                    os.close(anchor_descriptor)
            finally:
                fcntl.flock(journal_descriptor, fcntl.LOCK_UN)
                os.close(journal_descriptor)
        try:
            records = _parse_records(journal_raw)
            anchors = _parse_anchors(anchor_raw)
            static = _static_identity(records)
            if static != self._static:
                raise _JournalIntegrityError(
                    "CREATOR_LIVE_STATIC_IDENTITY_CHANGED",
                    repair_action="RECEIPT_REWRITE",
                )
            return _project_records(
                journal_raw,
                records,
                anchor_raw,
                anchors,
                static,
            )
        except _JournalIntegrityError as exc:
            return _failed_readback(
                journal_raw=journal_raw,
                anchor_raw=anchor_raw,
                static=self._static,
                reason=exc.reason,
                repair_action=exc.repair_action,
            )

    def _append(
        self,
        kind: JournalRecordKind,
        payload: dict[str, Any],
    ) -> FieldNoteCreatorLiveTraceReadback:
        if self._static.journal_schema not in {
            CREATOR_LIVE_JOURNAL_SCHEMA_V2,
            CREATOR_LIVE_JOURNAL_SCHEMA_V3,
        }:
            raise FieldNoteCreatorLiveStageError(
                "Historical v0.1 creator-live attempts are read-only."
            )
        with self._lock:
            journal_descriptor: int | None = None
            try:
                journal_descriptor = os.open(
                    self._journal_path,
                    os.O_RDWR | os.O_APPEND,
                )
                anchor_descriptor = os.open(
                    self._anchor_path,
                    os.O_RDWR | os.O_APPEND,
                )
            except OSError as exc:
                if journal_descriptor is not None:
                    os.close(journal_descriptor)
                raise FieldNoteCreatorLiveDurabilityError(
                    "Creator-live durable journal or anchor is missing."
                ) from exc
            try:
                fcntl.flock(journal_descriptor, fcntl.LOCK_EX)
                fcntl.flock(anchor_descriptor, fcntl.LOCK_EX)
                journal_raw = self._read_raw_locked(journal_descriptor)
                anchor_raw = self._read_raw_locked(anchor_descriptor)
                try:
                    records = _parse_records(journal_raw)
                    anchors = _parse_anchors(anchor_raw)
                    static = _static_identity(records)
                    readback = _project_records(
                        journal_raw,
                        records,
                        anchor_raw,
                        anchors,
                        static,
                    )
                except _JournalIntegrityError as exc:
                    raise FieldNoteCreatorLiveDurabilityError(
                        exc.reason
                    ) from exc
                if static != self._static or not readback.durable_readback_verified:
                    raise FieldNoteCreatorLiveDurabilityError(
                        "Creator-live durable identity changed before append."
                    )
                if readback.state in {"FAILED", "TRACE_COMPLETE"}:
                    raise FieldNoteCreatorLiveStageError(
                        "Creator-live attempt is terminal and cannot continue."
                    )
                record = _JournalRecord.create(
                    sequence=len(records),
                    kind=kind,
                    payload=payload,
                    previous_record_sha256=records[-1].record_sha256,
                    schema=self._static.record_schema,
                )
                line = record.serialize_line()
                written = os.write(journal_descriptor, line)
                if written != len(line):
                    raise FieldNoteCreatorLiveDurabilityError(
                        "Creator-live journal append was incomplete."
                    )
                os.fsync(journal_descriptor)
                next_journal_raw = journal_raw + line
                next_records = records + (record,)
                anchor = _AnchorRecord.create(
                    generation=len(anchors),
                    proof_attempt_id=self._static.attempt.proof_attempt_id,
                    journal_raw=next_journal_raw,
                    journal_records=next_records,
                    previous_anchor_sha256=anchors[-1].anchor_sha256,
                    schema=self._static.anchor_schema,
                )
                anchor_line = anchor.serialize_line()
                anchor_written = os.write(anchor_descriptor, anchor_line)
                if anchor_written != len(anchor_line):
                    raise FieldNoteCreatorLiveDurabilityError(
                        "Creator-live durable anchor append was incomplete."
                    )
                os.fsync(anchor_descriptor)
            finally:
                fcntl.flock(anchor_descriptor, fcntl.LOCK_UN)
                fcntl.flock(journal_descriptor, fcntl.LOCK_UN)
                os.close(anchor_descriptor)
                os.close(journal_descriptor)
        if self._static.journal_schema == CREATOR_LIVE_JOURNAL_SCHEMA_V3:
            directory = os.open(self._storage_root, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        return self.read_back()

    def _terminal_failure(
        self,
        boundary: WholeFlowBoundary,
        reason: str,
        *,
        repair_action: RepairAction = "NONE",
        proposal_diagnostic: FieldNoteA1ProposalDiagnostic | None = None,
    ) -> None:
        bounded = _bounded_reason(reason)
        if proposal_diagnostic is not None:
            try:
                proposal_diagnostic = FieldNoteA1ProposalDiagnostic.from_dict(
                    proposal_diagnostic.as_dict()
                )
            except ValueError as exc:
                raise FieldNoteCreatorLiveValidationError(
                    "Creator-live A1 proposal diagnostic is invalid."
                ) from exc
            if (
                boundary != "A1_CAPTURE"
                or not _proposal_diagnostic_reason_matches(
                    proposal_diagnostic,
                    bounded,
                )
            ):
                raise FieldNoteCreatorLiveValidationError(
                    "Creator-live A1 proposal diagnostic is cross-bound."
                )
        readback = self.read_back()
        if readback.state in {"FAILED", "TRACE_COMPLETE"}:
            raise FieldNoteCreatorLiveStageError(
                "Creator-live attempt is terminal and cannot be reset."
            )
        payload: dict[str, Any] = {
            "failure_boundary": boundary,
            "failure_reason": bounded,
            "repair_action": repair_action,
        }
        if self._static.journal_schema in {
            CREATOR_LIVE_JOURNAL_SCHEMA_V2,
            CREATOR_LIVE_JOURNAL_SCHEMA_V3,
        }:
            payload["proof_as_of"] = self._runtime_terminal_proof_as_of(
                readback
            )
        if proposal_diagnostic is not None:
            payload.update(
                {
                    "proof_attempt_id": (
                        self._static.attempt.proof_attempt_id
                    ),
                    "run_id": self._static.run_1.run_id,
                    "proposal_diagnostic": proposal_diagnostic.as_dict(),
                    "proposal_diagnostic_sha256": (
                        proposal_diagnostic.diagnostic_sha256
                    ),
                }
            )
        self._append("ATTEMPT_FAILED", payload)
        raise FieldNoteCreatorLiveStageError(bounded)

    def _runtime_terminal_proof_as_of(
        self,
        readback: FieldNoteCreatorLiveTraceReadback,
    ) -> str:
        proof_as_of, proof_time = _parse_time(
            _utc_now_rfc3339(),
            "Terminal Proof As-of",
        )
        lower_bound = (
            readback.events[-1].observed_at
            if readback.events
            else self._static.attempt_opened_at
        )
        if lower_bound is None:
            raise FieldNoteCreatorLiveValidationError(
                "Terminal Proof As-of lacks an opening lower bound."
            )
        _, lower_time = _parse_time(
            lower_bound,
            "Last admitted observation",
        )
        if proof_time < lower_time:
            raise FieldNoteCreatorLiveValidationError(
                "Terminal Proof As-of precedes admitted evidence."
            )
        return proof_as_of

    def _require_stage(self, stage: TraceStage) -> FieldNoteCreatorLiveTraceReadback:
        readback = self.read_back()
        if not readback.durable_readback_verified:
            raise FieldNoteCreatorLiveDurabilityError(
                readback.failure_reason or "Creator-live read-back failed."
            )
        if readback.state in {"FAILED", "TRACE_COMPLETE"}:
            raise FieldNoteCreatorLiveStageError(
                "Creator-live attempt is terminal and cannot continue."
            )
        if readback.current_stage != stage:
            retry = stage in _STAGES[: readback.trace_event_count]
            self._terminal_failure(
                "RUNTIME_ENFORCEMENT",
                "CREATOR_LIVE_STAGE_ORDER_INVALID",
                repair_action=("RETRY_REPLACEMENT" if retry else "NONE"),
            )
        return readback

    def _emit(
        self,
        stage: TraceStage,
        *,
        evidence_sha256: str,
        binding: dict[str, Any],
        observed_at: str | None = None,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage(stage)
        index = readback.trace_event_count
        run = readback.run_1 if index == 0 else readback.run_2
        if run is None:
            self._terminal_failure(
                "RUN_SEPARATION",
                "CREATOR_LIVE_RUN_2_NOT_OPEN",
            )
        assert run is not None
        event = FieldNoteWholeFlowTraceEvent(
            sequence=index,
            stage=stage,
            run_id=run.run_id,
            observed_at=(
                _utc_now_rfc3339() if observed_at is None else observed_at
            ),
            evidence_sha256=evidence_sha256,
            previous_trace_sha256=readback.trace_chain_head_sha256,
            repair_action="NONE",
            proof_attempt_id=self._static.attempt.proof_attempt_id,
            runtime=self._static.runtime,
            source_repository=self._static.repository,
            runtime_provenance=self._static.provenance,
        )
        self._append(
            "CHECKPOINT",
            {"event": event.as_dict(), "binding": binding},
        )
        if stage == "A6_REVIEW":
            completed = self.read_back()
            completion_payload = {
                "trace_event_count": len(_STAGES),
                "trace_chain_head_sha256": (
                    completed.trace_chain_head_sha256
                ),
                "runtime_provenance_id": (
                    self._static.provenance.runtime_provenance_id
                ),
                "no_repair_verified": True,
            }
            if self._static.journal_schema in {
                CREATOR_LIVE_JOURNAL_SCHEMA_V2,
                CREATOR_LIVE_JOURNAL_SCHEMA_V3,
            }:
                completion_payload["proof_as_of"] = (
                    self._runtime_terminal_proof_as_of(completed)
                )
            self._append(
                "TRACE_COMPLETED",
                completion_payload,
            )
        return event

    def record_run_2_output_identity(
        self,
        identity: FieldNoteCreatorLiveRun2OutputIdentity,
    ) -> FieldNoteCreatorLiveTraceReadbackV3:
        readback = self._require_stage("A3_REUSE")
        if self._static.journal_schema != CREATOR_LIVE_JOURNAL_SCHEMA_V3 or (
            not isinstance(readback, FieldNoteCreatorLiveTraceReadbackV3)
        ):
            raise FieldNoteCreatorLiveStageError(
                "Run 2 output identity requires a v0.3 attempt."
            )
        if (
            not isinstance(identity, FieldNoteCreatorLiveRun2OutputIdentity)
            or readback.run_2 is None
            or readback.run_2_output_identity is not None
            or readback.a3_compiler_audit is not None
            or identity.proof_attempt_id != readback.proof_attempt_id
            or identity.run_id != readback.run_2.run_id
            or identity.task_byte_count
            != readback.terminal_projection_binding.run_2_task.byte_count
            or identity.task_sha256
            != readback.terminal_projection_binding.run_2_task.sha256
        ):
            self._terminal_failure(
                "A3_REUSE",
                "A3_RUN_2_OUTPUT_IDENTITY_INVALID",
            )
        recorded = self._append(
            "RUN_2_OUTPUT_IDENTITY_RECORDED",
            identity.as_dict(),
        )
        if not isinstance(recorded, FieldNoteCreatorLiveTraceReadbackV3) or (
            recorded.run_2_output_identity != identity
        ):
            raise FieldNoteCreatorLiveDurabilityError(
                "Run 2 output identity did not survive exact read-back."
            )
        return recorded

    def record_a3_compiler_audit(
        self,
        audit: FieldNoteCreatorLiveA3CompilerAudit,
    ) -> FieldNoteCreatorLiveTraceReadbackV3:
        readback = self._require_stage("A3_REUSE")
        if self._static.journal_schema != CREATOR_LIVE_JOURNAL_SCHEMA_V3 or (
            not isinstance(readback, FieldNoteCreatorLiveTraceReadbackV3)
        ):
            raise FieldNoteCreatorLiveStageError(
                "A3 compiler audit requires a v0.3 attempt."
            )
        output_identity = readback.run_2_output_identity
        note = readback.captured_note
        if (
            not isinstance(audit, FieldNoteCreatorLiveA3CompilerAudit)
            or output_identity is None
            or readback.a3_compiler_audit is not None
            or readback.run_2 is None
            or note is None
            or readback.captured_note_byte_count is None
            or audit.proof_attempt_id != readback.proof_attempt_id
            or audit.run_id != readback.run_2.run_id
            or audit.output_artifact_id
            != output_identity.output_artifact.artifact_id
            or audit.output_byte_count != output_identity.final_output_byte_count
            or audit.output_sha256 != output_identity.final_output_sha256
            or audit.source_note_byte_count != readback.captured_note_byte_count
            or audit.source_note_sha256 != note.note_sha256
        ):
            self._terminal_failure(
                "A3_REUSE",
                "A3_COMPILER_AUDIT_IDENTITY_INVALID",
            )
        recorded = self._append("A3_COMPILER_AUDIT_RECORDED", audit.as_dict())
        if not isinstance(recorded, FieldNoteCreatorLiveTraceReadbackV3) or (
            recorded.a3_compiler_audit != audit
        ):
            raise FieldNoteCreatorLiveDurabilityError(
                "A3 compiler audit did not survive exact read-back."
            )
        return recorded

    def open_run_2(
        self,
        run_2: FieldNoteWholeFlowRunIdentity,
    ) -> FieldNoteCreatorLiveTraceReadback:
        readback = self.read_back()
        if readback.state != "OPEN":
            raise FieldNoteCreatorLiveStageError(
                "Creator-live attempt is terminal and cannot continue."
            )
        if readback.trace_event_count != 1 or readback.current_stage != (
            "A2_RECONNECT"
        ):
            self._terminal_failure(
                "RUN_SEPARATION",
                "CREATOR_LIVE_RUN_2_BEFORE_A1_CLOSURE",
            )
        if not isinstance(run_2, FieldNoteWholeFlowRunIdentity):
            self._terminal_failure(
                "RUN_SEPARATION",
                "CREATOR_LIVE_RUN_2_IDENTITY_INVALID",
            )
        if run_2.run_id == self._static.run_1.run_id:
            self._terminal_failure(
                "RUN_SEPARATION",
                "RUN_IDENTITIES_NOT_DISTINCT",
                repair_action="RETRY_REPLACEMENT",
            )
        if run_2.proof_attempt_id != self._static.attempt.proof_attempt_id:
            self._terminal_failure(
                "RUN_SEPARATION",
                "RUN_ATTEMPT_MISMATCH",
                repair_action="RETRY_REPLACEMENT",
            )
        if run_2.runtime != self._static.runtime:
            self._terminal_failure(
                "MODEL_IDENTITY",
                "MODEL_RUNTIME_MISMATCH",
                repair_action="RETRY_REPLACEMENT",
            )
        if run_2.repository != self._static.repository:
            self._terminal_failure(
                "REPOSITORY_IDENTITY",
                "SOURCE_REPOSITORY_MISMATCH",
                repair_action="RETRY_REPLACEMENT",
            )
        _, run_1_time = _parse_time(
            self._static.run_1.started_at,
            "Run 1 start",
        )
        _, run_2_time = _parse_time(run_2.started_at, "Run 2 start")
        if run_2_time <= run_1_time:
            self._terminal_failure(
                "RUN_SEPARATION",
                "RUN_ORDER_INVALID",
                repair_action="TIMESTAMP_CHANGE",
            )
        return self._append("RUN_2_OPENED", {"run_2": run_2.as_dict()})

    def record_a1_capture(
        self,
        draft: FieldNoteDraft,
        *,
        capture_commit: FieldNoteCreatorLiveA1CaptureCommitReceipt,
        expected_task_sha256: str,
        actual_runtime_identity: CodexRuntimeIdentity,
        observed_at: str | None = None,
    ) -> FieldNoteWholeFlowTraceEvent:
        self._require_stage("A1_CAPTURE")
        if not isinstance(draft, FieldNoteDraft):
            self._terminal_failure("A1_CAPTURE", "A1_CAPTURE_INVALID")
        try:
            validate_compiled_markdown(draft.markdown)
        except ValueError:
            self._terminal_failure("A1_CAPTURE", "A1_CAPTURE_INVALID")
        if (
            draft.source_run_id != self._static.run_1.run_id
            or _sha256_bytes(draft.markdown) != draft.sha256
        ):
            self._terminal_failure("A1_CAPTURE", "A1_NOTE_IDENTITY_MISMATCH")
        note = FieldNoteIdentity(
            note_path=draft.relative_path,
            field_note_id=draft.field_note_id,
            note_sha256=draft.sha256,
            origin_run_id=draft.source_run_id,
        )
        draft_evidence_sha256 = _a1_evidence_sha256(draft)
        checkpoint_observed_at = (
            _utc_now_rfc3339() if observed_at is None else observed_at
        )
        if (
            not isinstance(
                capture_commit,
                FieldNoteCreatorLiveA1CaptureCommitReceipt,
            )
            or capture_commit.proof_attempt_id
            != self._static.attempt.proof_attempt_id
            or capture_commit.run_id != self._static.run_1.run_id
            or capture_commit.task_sha256 != expected_task_sha256
            or capture_commit.actual_runtime_identity
            != actual_runtime_identity
            or actual_runtime_identity != self._static.runtime
            or capture_commit.source_repository != self._static.repository
            or capture_commit.note != note
            or capture_commit.note_byte_count != len(draft.markdown)
            or capture_commit.draft_evidence_sha256
            != draft_evidence_sha256
            or capture_commit.draft_created_at != draft.created_at
            or capture_commit.controller_state != "saved"
            or capture_commit.read_back_verified is not True
        ):
            self._terminal_failure(
                "A1_CAPTURE",
                "A1_CAPTURE_COMMIT_MISMATCH",
            )
        if not _a1_capture_chronology_is_valid(
            run_1_started_at=self._static.run_1.started_at,
            draft_created_at=draft.created_at,
            save_as_of=capture_commit.save_as_of,
            observed_at=checkpoint_observed_at,
            proof_as_of=(
                self._static.attempt.proof_as_of
                if isinstance(
                    self._static.attempt,
                    FieldNoteWholeFlowAttempt,
                )
                else None
            ),
        ):
            self._terminal_failure(
                "A1_CAPTURE",
                "A1_CAPTURE_CHRONOLOGY_INVALID",
                repair_action="TIMESTAMP_CHANGE",
            )
        evidence_sha256 = capture_commit.receipt_sha256
        return self._emit(
            "A1_CAPTURE",
            evidence_sha256=evidence_sha256,
            observed_at=checkpoint_observed_at,
            binding={
                "evidence_type": (
                    "FieldNoteCreatorLiveA1CaptureCommitReceipt"
                ),
                "evidence_sha256": evidence_sha256,
                "a1_draft_sha256": draft_evidence_sha256,
                "note": note.as_dict(),
                "note_byte_count": len(draft.markdown),
                "capture_commit": capture_commit.as_dict(),
                "capture_commit_sha256": capture_commit.receipt_sha256,
            },
        )

    def _require_exact_note(
        self,
        readback: FieldNoteCreatorLiveTraceReadback,
        note: FieldNoteIdentity,
        note_bytes: bytes,
        *,
        boundary: WholeFlowBoundary,
    ) -> None:
        if (
            not isinstance(note, FieldNoteIdentity)
            or not isinstance(note_bytes, bytes)
            or readback.captured_note != note
            or readback.captured_note_byte_count != len(note_bytes)
            or _sha256_bytes(note_bytes) != note.note_sha256
        ):
            self._terminal_failure(
                boundary,
                "CREATOR_LIVE_EXACT_NOTE_MISMATCH",
                repair_action="NOTE_EDIT",
            )

    def record_a2_reconnect(
        self,
        receipt: FieldNoteReconnectReceipt,
        *,
        note: FieldNoteIdentity,
        note_bytes: bytes,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage("A2_RECONNECT")
        self._require_exact_note(
            readback,
            note,
            note_bytes,
            boundary="A2_RECONNECT",
        )
        if not isinstance(receipt, FieldNoteReconnectReceipt):
            self._terminal_failure("A2_RECONNECT", "A2_EVIDENCE_INVALID")
        if readback.run_2 is None or receipt.run_id != readback.run_2.run_id:
            self._terminal_failure("A2_RECONNECT", "A2_RUN_MISMATCH")
        if (
            receipt.state not in {"INJECTED", "ACTIVATION_UNKNOWN"}
            or receipt.full_notes_injected != 1
            or receipt.failure_reason is not None
        ):
            self._terminal_failure("A2_RECONNECT", "A2_NOT_INJECTED")
        if (
            receipt.selected_field_note_path != note.note_path
            or receipt.selected_field_note_id != note.field_note_id
            or receipt.selected_full_note_sha256 != note.note_sha256
            or receipt.full_note_bytes_read != len(note_bytes)
        ):
            self._terminal_failure("A2_RECONNECT", "A2_EXACT_NOTE_MISMATCH")
        evidence_sha256 = _a2_receipt_sha256(receipt)
        return self._emit(
            "A2_RECONNECT",
            evidence_sha256=evidence_sha256,
            binding={
                "evidence_type": "FieldNoteReconnectReceipt",
                "evidence_sha256": evidence_sha256,
            },
        )

    def record_a3_reuse(
        self,
        receipt: FieldNoteReuseReceipt,
        *,
        note: FieldNoteIdentity,
        note_bytes: bytes,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage("A3_REUSE")
        self._require_exact_note(
            readback,
            note,
            note_bytes,
            boundary="A3_REUSE",
        )
        if not isinstance(receipt, FieldNoteReuseReceipt):
            self._terminal_failure("A3_REUSE", "A3_EVIDENCE_INVALID")
        if receipt.state != "REUSED" or receipt.use_evidence is None:
            self._terminal_failure("A3_REUSE", "A3_NOT_DEMONSTRABLY_REUSED")
        if receipt.note != note:
            self._terminal_failure("A3_REUSE", "A3_EXACT_NOTE_MISMATCH")
        if readback.run_2 is None or (
            receipt.reusing_run_id != readback.run_2.run_id
            or receipt.use_evidence.reusing_run_id != readback.run_2.run_id
        ):
            self._terminal_failure("A3_REUSE", "A3_RUN_MISMATCH")
        if not receipt.use_evidence.structure_binding.verifies(note, note_bytes):
            self._terminal_failure(
                "A3_REUSE",
                "A3_STRUCTURE_BINDING_INVALID",
            )
        if isinstance(readback, FieldNoteCreatorLiveTraceReadbackV3):
            audit = readback.a3_compiler_audit
            output_identity = readback.run_2_output_identity
            structure = receipt.use_evidence.structure_binding
            if (
                audit is None
                or output_identity is None
                or audit.winning_candidate_count != 1
                or audit.terminal_a3_code is not None
                or structure.start_byte != audit.selected_source_start_byte
                or structure.end_byte != audit.selected_source_end_byte
                or receipt.use_evidence.evidence_class != "OUTPUT_ARTIFACT"
                or receipt.use_evidence.evidence_origin
                != "IMMEDIATE_COMPLETION_RECORD"
                or receipt.use_evidence.evidence_sha256
                != output_identity.final_output_sha256
                or receipt.use_evidence.evidence_ref
                != (
                    f"run:{readback.run_2.run_id}:final-output:bytes:"
                    f"{audit.selected_output_start_byte}:"
                    f"{audit.selected_output_end_byte}"
                )
            ):
                self._terminal_failure(
                    "A3_REUSE",
                    "A3_COMPILER_AUDIT_CLAIM_MISMATCH",
                )
        if receipt.reuse_event_id != _expected_reuse_event_id(receipt):
            self._terminal_failure("A3_REUSE", "A3_REUSE_EVENT_ID_INVALID")
        if receipt.promotion != PromotionPolicyBoundary():
            self._terminal_failure("A3_REUSE", "A3_PROMOTABLE_POLICY_WIDENED")
        assert receipt.reuse_event_id is not None
        receipt_sha256 = _a3_receipt_sha256(receipt)
        return self._emit(
            "A3_REUSE",
            evidence_sha256=receipt_sha256,
            binding={
                "evidence_type": "FieldNoteReuseReceipt",
                "evidence_sha256": receipt_sha256,
                "reuse_event_id": receipt.reuse_event_id,
            },
        )

    def record_a4_durability(
        self,
        snapshot: FieldNoteMaturityLedgerSnapshot,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage("A4_DURABILITY")
        if not isinstance(snapshot, FieldNoteMaturityLedgerSnapshot):
            self._terminal_failure("A4_DURABILITY", "A4_EVIDENCE_INVALID")
        if len(snapshot.events) != 1 or readback.captured_note is None:
            self._terminal_failure(
                "A4_DURABILITY",
                "A4_EVENT_COUNT_NOT_EXACTLY_ONE",
            )
        event = snapshot.events[0]
        a3_receipt_identity = readback.events[2].evidence_sha256
        a3_reuse_event_id = readback.a3_reuse_event_id
        if (
            snapshot.note != readback.captured_note
            or a3_reuse_event_id is None
            or event.sequence != 0
            or event.previous_event_sha256 != GENESIS_EVENT_SHA256
            or event.event_id != event.receipt.reuse_event_id
            or event.receipt.reuse_event_id != a3_reuse_event_id
            or event.receipt.reuse_event_id
            != _expected_reuse_event_id(event.receipt)
            or event.receipt_sha256 != a3_receipt_identity
            or _event_receipt_sha256(event) != a3_receipt_identity
            or event.event_sha256 != _event_sha256(event)
            or snapshot.chain_head_sha256 != event.event_sha256
            or snapshot.evidence_maturity.state != "REUSED"
        ):
            self._terminal_failure(
                "A4_DURABILITY",
                "A4_EXACT_EVENT_INTEGRITY_INVALID",
                repair_action="LEDGER_REWRITE",
            )
        return self._emit(
            "A4_DURABILITY",
            evidence_sha256=event.event_sha256,
            binding={
                "evidence_type": "FieldNoteMaturityLedgerEvent",
                "evidence_sha256": event.event_sha256,
            },
        )

    def record_a5_confirmation(
        self,
        result: FieldNoteMaturityCommitResult,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage("A5_CONFIRMATION")
        if not isinstance(result, FieldNoteMaturityCommitResult):
            self._terminal_failure("A5_CONFIRMATION", "A5_EVIDENCE_INVALID")
        if (
            result.status not in {"RECORDED", "ALREADY_RECORDED"}
            or not result.durable_commit_confirmed
            or result.append_result is None
            or result.durable_snapshot is None
        ):
            self._terminal_failure(
                "A5_CONFIRMATION",
                "A5_APPEND_NOT_CONFIRMED",
            )
        a2_identity = readback.events[1].evidence_sha256
        a3_receipt_identity = readback.events[2].evidence_sha256
        a4_identity = readback.events[3].evidence_sha256
        if (
            readback.a3_reuse_event_id is None
            or result.assessment.reuse_event_id
            != readback.a3_reuse_event_id
            or _a3_receipt_sha256(result.assessment)
            != a3_receipt_identity
            or result.delivery_context is None
            or _a2_receipt_sha256(result.delivery_context) != a2_identity
            or result.append_result.event.event_sha256 != a4_identity
            or result.append_result.event.receipt_sha256
            != a3_receipt_identity
            or len(result.durable_snapshot.events) != 1
            or result.durable_snapshot.events[0].event_sha256 != a4_identity
        ):
            self._terminal_failure(
                "A5_CONFIRMATION",
                "A5_READ_BACK_LINEAGE_MISMATCH",
                repair_action="RECEIPT_REWRITE",
            )
        identity = _a5_confirmation_sha256(result)
        return self._emit(
            "A5_CONFIRMATION",
            evidence_sha256=identity,
            binding={
                "evidence_type": "FieldNoteMaturityCommitResult",
                "evidence_sha256": identity,
            },
        )

    def record_a6_review(
        self,
        packet: FieldNoteMaturityReviewPacket,
    ) -> FieldNoteWholeFlowTraceEvent:
        readback = self._require_stage("A6_REVIEW")
        if not isinstance(packet, FieldNoteMaturityReviewPacket):
            self._terminal_failure("A6_REVIEW", "A6_EVIDENCE_INVALID")
        a4_identity = readback.events[3].evidence_sha256
        if (
            packet.note_identity != readback.captured_note
            or readback.a3_reuse_event_id is None
            or len(packet.ordered_event_reviews) != 1
            or packet.ordered_event_reviews[0].event_id
            != readback.a3_reuse_event_id
            or packet.ordered_event_reviews[0].event_sha256 != a4_identity
            or packet.ledger_identity.chain_head_sha256 != a4_identity
            or packet.evidence_maturity.state != "REUSED"
            or packet.current_serving_policy.derivation != "DELAY"
            or packet.current_serving_policy.automatic_injection is not None
        ):
            self._terminal_failure(
                "A6_REVIEW",
                "A6_EXACT_PACKET_MISMATCH",
                repair_action="RECEIPT_REWRITE",
            )
        identity = _a6_packet_sha256(packet)
        return self._emit(
            "A6_REVIEW",
            evidence_sha256=identity,
            binding={
                "evidence_type": "FieldNoteMaturityReviewPacket",
                "evidence_sha256": identity,
            },
        )

    def record_stage_failure(
        self,
        boundary: WholeFlowBoundary,
        reason: str,
        *,
        proposal_diagnostic: FieldNoteA1ProposalDiagnostic | None = None,
    ) -> None:
        self._terminal_failure(
            boundary,
            reason,
            proposal_diagnostic=proposal_diagnostic,
        )

    def record_repair(
        self,
        boundary: WholeFlowBoundary,
        reason: str,
        *,
        repair_action: RepairAction,
    ) -> None:
        if repair_action == "NONE":
            raise FieldNoteCreatorLiveValidationError(
                "Repair recording requires a prohibited repair action."
            )
        self._terminal_failure(
            boundary,
            reason,
            repair_action=repair_action,
        )

    def record_retry_replacement(self, reason: str) -> None:
        self._terminal_failure(
            "RUNTIME_ENFORCEMENT",
            reason,
            repair_action="RETRY_REPLACEMENT",
        )
