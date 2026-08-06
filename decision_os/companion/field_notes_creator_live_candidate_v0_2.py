"""Additive non-live fixation for the isolated historical-AGENTS candidate.

The module owns no live launch, provider, proof-root, publication, or Cycle
authority.  It supplies the fixed content capability, content-free receipts,
candidate gates, and fixture-only public projections for
``CREATOR_LIVE_AGENTS_BEFORE_AFTER_V0_2``.  Candidate v0.1 remains untouched.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable, Mapping, Sequence

from decision_os.companion.field_notes_creator_live import (
    A3_COMPILER_BRANCH,
    A3_COMPILER_VERSION,
    FieldNoteCreatorLiveA3CompilerAudit,
)
from decision_os.companion.field_notes_creator_live_candidate import (
    BEHAVIOR_RESULT_SCHEMA,
    BEHAVIOR_RUBRIC_SHA256,
    BEHAVIOR_SUITE_SCHEMA,
    BEHAVIOR_SUITE_SHA256,
    PROJECTION_SCHEMA,
    SAFETY_SCHEMA,
    WITNESS_LOCATOR,
    BehaviorResult,
    BoundaryResult,
    PublicAfterProjection,
    RealBehaviorQualificationReceipt,
    SafetyReceipt,
    artifact_behavior_not_run,
    evaluate_behavior_fakes,
    load_behavior_suite,
    project_public_after,
    public_safety as inherited_public_safety,
)
from decision_os.companion.field_notes_model import (
    canonical_json,
    field_note_tool_spec_for_trust,
)
from decision_os.companion.field_notes_reuse import FieldNoteIdentity


CANDIDATE_ID = "CREATOR_LIVE_AGENTS_BEFORE_AFTER_V0_2"
AUTHORIZATION_OBSERVED_AT = "2026-08-05T23:39:00Z"

SOURCE_TOOL_NAME = "read_candidate_historical_before_v0_2"
SOURCE_VIRTUAL_PATH = "before/AGENTS.md"
SOURCE_REVISION = "21cd88d4efb378a60cd08a28712083d9d4a8bc19"
SOURCE_GIT_BLOB = "f85b0d9b17a8f90a7128ea96d9c8f63a88022128"
SOURCE_BYTE_COUNT = 20_705
SOURCE_LINE_COUNT = 517
SOURCE_SHA256 = "e856160413a9d47622779dede6a2eeca9fd027284d815b155ab6e323a74863db"
SOURCE_RESOURCE = (
    Path("candidate_inputs")
    / "creator_live_agents_before_after_v0_2"
    / "AGENTS.md"
)

RUN_1_PATH = "prompts/creator_live_agents_before_after_v0_2_run_1.txt"
RUN_1_BYTE_COUNT = 2_713
RUN_1_LINE_COUNT = 68
RUN_1_SHA256 = "2ed80098fb169313b13c36dddfd69a3ab487a4fe31d8474889cff7ba441b09e2"
RUN_2_PATH = "prompts/creator_live_agents_before_after_v0_2_run_2.txt"
RUN_2_BYTE_COUNT = 2_703
RUN_2_LINE_COUNT = 56
RUN_2_SHA256 = "1a67c3677ce8c73b4259317130e689dfefa1827fffe3abe377af861da8ec4bdb"

MANUAL_AFTER_REVISION = "e3d1b29f4bfb0215ebde66ea60376c01b7f87327"
MANUAL_AFTER_GIT_BLOB = "2deb6f610f8e3a4e67808a0182cb2439a7abc447"
MANUAL_AFTER_BYTE_COUNT = 11_147
MANUAL_AFTER_LINE_COUNT = 359
MANUAL_AFTER_SHA256 = "bb14c77c6b45c6bf365902b47729b455df566fa98688956824e072c352f2dae7"

SOURCE_ISOLATION_SCHEMA = "decision-os.creator-live-agents-source-isolation.v0.1"
INDEPENDENCE_SCHEMA = "decision-os.creator-live-agents-independence.v0.1"
COMPRESSION_SCHEMA = "decision-os.creator-live-agents-compression.v0.2"
DIFF_SCHEMA = "decision-os.creator-live-agents-diff.python-difflib-v0.1"
BOUNDARY_SCHEMA = "decision-os.creator-live-agents-boundary-checklist.v0.2"
WITNESS_SCHEMA = "decision-os.creator-live-agents-witness-binding.v0.2"
POST_A1_SCHEMA = "decision-os.creator-live-agents-post-a1-gate-readback.v0.2"
A3_WITNESS_SCHEMA = "decision-os.creator-live-agents-a3-witness-verification.v0.2"
COMPARISON_SCHEMA = "decision-os.creator-live-agents-common-before-comparison.v0.1"
REDUCTION_MAP_SCHEMA = "decision-os.reduction-boundary-map.v0.1"
PUBLIC_BUNDLE_SCHEMA = (
    "decision-os.creator-live-agents-before-after-public-bundle.v0.2"
)
PUBLIC_BUNDLE_ASSEMBLER = (
    "decision-os.creator-live-agents-before-after-public-bundle-assembler.v0.2"
)
SOURCE_ISOLATION_PUBLIC_PROJECTION_SCHEMA = PUBLIC_BUNDLE_SCHEMA + "#source-isolation"
INDEPENDENCE_PUBLIC_PROJECTION_SCHEMA = (
    PUBLIC_BUNDLE_SCHEMA + "#independence-qualification"
)

QUALIFICATION_RESULTS = frozenset({"PASS", "FAIL", "NOT_ESTABLISHED"})
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
POST_A1_READBACK_FILENAME = "candidate-v0.2-post-a1-gate.json"

SOURCE_TOOL_SPEC: dict[str, Any] = {
    "type": "function",
    "name": SOURCE_TOOL_NAME,
    "description": (
        "Disclose the one fixed Candidate v0.2 historical Before artifact. "
        "The tool accepts no arguments and exposes no repository path choice."
    ),
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "maxProperties": 0,
    },
}

ISOLATION_FEATURES: dict[str, bool] = {
    "arbitrary_file_read": False,
    "attachments": False,
    "apps": False,
    "browser_or_url": False,
    "dependency_installation": False,
    "file_mutation": False,
    "git_history_or_objects": False,
    "hooks": False,
    "mcp": False,
    "multi_agent": False,
    "native_or_implicit_file_reader": False,
    "plugins": False,
    "remote_plugins": False,
    "shell": False,
    "web": False,
}

CANDIDATE_DEVELOPER_INSTRUCTIONS = (
    "This is the isolated Candidate v0.2 A1 capture lane. Use only "
    "read_candidate_historical_before_v0_2 once and "
    "propose_field_note_candidate once. No native file reader, repository "
    "reader, shell, Git, web, MCP, plugin, app, hook, attachment, dependency "
    "installation, file change, retry, replacement, or publication is "
    "authorized. Hold the proposal until normal terminal completion and final "
    "independence PASS."
)
DEVELOPER_INSTRUCTIONS_SHA256 = hashlib.sha256(
    CANDIDATE_DEVELOPER_INSTRUCTIONS.encode("utf-8")
).hexdigest()

_PRIVATE_PROJECTION_FIELD_MARKERS = (
    b"proof_attempt_id",
    b"run_id",
    b"source_run_id",
    b"field_note_id",
    b"note_path",
    b"approval_id",
    b"provider_config",
    b"journal_sha256",
    b"anchor_sha256",
    b"readback_sha256",
    b"typed_readback",
    b"raw_journal",
    b"raw_anchor",
    b"raw_readback",
)
_PRIVATE_PROJECTION_LABEL_PATTERNS = (
    re.compile(
        rb"\b(?:journal|anchor)(?:[ _-]*file)?[ _-]*"
        rb"(?:sha(?:[ _-]?256)?|hash|identity)\b",
        re.I,
    ),
    re.compile(
        rb"\btyped[ _-]*readback(?:[ _-]*(?:sha(?:[ _-]?256)?|hash|identity))?\b",
        re.I,
    ),
    re.compile(
        rb"\breadback[ _-]*(?:sha(?:[ _-]?256)?|hash|identity)\b",
        re.I,
    ),
)


class CandidateV02Error(ValueError):
    """Fail-closed candidate error with one stable diagnostic code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def _line_count(value: bytes) -> int:
    if not value.endswith(b"\n"):
        raise CandidateV02Error("ARTIFACT_FINAL_LF_MISSING")
    return value.count(b"\n")


def _require_sha256(value: str, code: str) -> None:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise CandidateV02Error(code)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _HEX64.fullmatch(value) is not None


def public_safety(after: bytes) -> SafetyReceipt:
    """Extend the inherited checker with v0.2 private-proof field names."""

    inherited = inherited_public_safety(after)
    private_fields = tuple(
        marker.decode("ascii")
        for marker in _PRIVATE_PROJECTION_FIELD_MARKERS
        if marker.lower() in after.lower()
    )
    private_labels = tuple(
        f"LABEL_{index}"
        for index, pattern in enumerate(_PRIVATE_PROJECTION_LABEL_PATTERNS, start=1)
        if pattern.search(after)
    )
    if not private_fields and not private_labels:
        return inherited
    return SafetyReceipt(
        SAFETY_SCHEMA,
        "FAIL",
        tuple(inherited.finding_codes)
        + tuple(f"PRIVATE_PROOF_FIELD_{value.upper()}" for value in private_fields)
        + tuple(f"PRIVATE_PROOF_{value}" for value in private_labels),
    )


@dataclass(frozen=True)
class FixedSourceIdentity:
    virtual_path: str
    source_revision: str
    git_blob: str
    utf8_byte_count: int
    line_count: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "virtual_path": self.virtual_path,
            "source_revision": self.source_revision,
            "git_blob": self.git_blob,
            "utf8_byte_count": self.utf8_byte_count,
            "line_count": self.line_count,
            "sha256": self.sha256,
        }


FIXED_SOURCE_IDENTITY = FixedSourceIdentity(
    SOURCE_VIRTUAL_PATH,
    SOURCE_REVISION,
    SOURCE_GIT_BLOB,
    SOURCE_BYTE_COUNT,
    SOURCE_LINE_COUNT,
    SOURCE_SHA256,
)


def fixed_source_identity_sha256() -> str:
    return _sha256(canonical_json(FIXED_SOURCE_IDENTITY.as_dict()).encode("utf-8"))


@dataclass(frozen=True)
class FixedTaskIdentity:
    path: str
    byte_count: int
    line_count: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


FIXED_TASK_IDENTITIES = (
    FixedTaskIdentity(RUN_1_PATH, RUN_1_BYTE_COUNT, RUN_1_LINE_COUNT, RUN_1_SHA256),
    FixedTaskIdentity(RUN_2_PATH, RUN_2_BYTE_COUNT, RUN_2_LINE_COUNT, RUN_2_SHA256),
)


def _fixed_bytes(value: bytes, *, task: FixedTaskIdentity | None = None) -> bytes:
    try:
        value.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CandidateV02Error("FIXED_ARTIFACT_NOT_UTF8") from exc
    if task is None:
        expected = (SOURCE_BYTE_COUNT, SOURCE_LINE_COUNT, SOURCE_SHA256)
    else:
        expected = (task.byte_count, task.line_count, task.sha256)
    if (
        len(value) != expected[0]
        or _line_count(value) != expected[1]
        or _sha256(value) != expected[2]
    ):
        raise CandidateV02Error("FIXED_ARTIFACT_IDENTITY_DRIFT")
    return value


def source_resource_path() -> Path:
    return Path(__file__).resolve().parent / SOURCE_RESOURCE


def load_fixed_source() -> bytes:
    """Load only the installed content-addressed resource; never consult Git."""

    path = source_resource_path()
    if not path.is_file() or path.is_symlink():
        raise CandidateV02Error("SOURCE_RESOURCE_UNAVAILABLE")
    try:
        return _fixed_bytes(path.read_bytes())
    except OSError as exc:
        raise CandidateV02Error("SOURCE_RESOURCE_UNAVAILABLE") from exc


def verify_packaged_source_against_git(repository: Path) -> FixedSourceIdentity:
    """Non-live qualification only: bind packaged bytes to the historical blob."""

    packaged = load_fixed_source()
    try:
        historical = subprocess.run(
            ["git", "show", f"{SOURCE_REVISION}:AGENTS.md"],
            cwd=Path(repository),
            check=True,
            capture_output=True,
        ).stdout
        blob = subprocess.run(
            ["git", "rev-parse", f"{SOURCE_REVISION}:AGENTS.md"],
            cwd=Path(repository),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CandidateV02Error("HISTORICAL_SOURCE_UNAVAILABLE") from exc
    if historical != packaged or blob != SOURCE_GIT_BLOB:
        raise CandidateV02Error("HISTORICAL_SOURCE_IDENTITY_DRIFT")
    return FIXED_SOURCE_IDENTITY


def verify_fixed_tasks(repository: Path) -> tuple[FixedTaskIdentity, FixedTaskIdentity]:
    for task in FIXED_TASK_IDENTITIES:
        try:
            value = (Path(repository) / task.path).read_bytes()
        except OSError as exc:
            raise CandidateV02Error("FIXED_TASK_UNAVAILABLE") from exc
        _fixed_bytes(value, task=task)
    return FIXED_TASK_IDENTITIES


def candidate_dynamic_tools(
    source_model_class: str = "stronger",
    target_model_class: str = "lower-cost",
) -> list[dict[str, Any]]:
    return [
        copy.deepcopy(SOURCE_TOOL_SPEC),
        field_note_tool_spec_for_trust(source_model_class, target_model_class),
    ]


def dynamic_tool_manifest_sha256() -> str:
    return _sha256(canonical_json(candidate_dynamic_tools()).encode("utf-8"))


@dataclass(frozen=True)
class SourceToolCallResult:
    success: bool
    code: str
    payload: Mapping[str, Any]
    semantic_disclosure: bool


class FixedSourceToolSession:
    """One-run, content-addressed source capability with replay identity."""

    def __init__(self) -> None:
        self._source = load_fixed_source()
        self._responses: dict[str, tuple[str, SourceToolCallResult]] = {}
        self._successful_call_id: str | None = None
        self.source_call_count = 0
        self.semantic_disclosure_count = 0
        self.distinct_exposed_source_count = 0
        self.reason_codes: list[str] = []

    @staticmethod
    def _arguments_sha256(arguments: Mapping[str, Any]) -> str:
        return _sha256(canonical_json(dict(arguments)).encode("utf-8"))

    def call(self, call_id: str, arguments: Mapping[str, Any]) -> SourceToolCallResult:
        if not isinstance(call_id, str) or not call_id:
            self.reason_codes.append("SOURCE_CALL_ID_INVALID")
            return SourceToolCallResult(False, "SOURCE_CALL_ID_INVALID", {}, False)
        if not isinstance(arguments, Mapping):
            self.reason_codes.append("SOURCE_ARGUMENTS_INVALID")
            return SourceToolCallResult(False, "SOURCE_ARGUMENTS_INVALID", {}, False)
        argument_hash = self._arguments_sha256(arguments)
        if call_id in self._responses:
            prior_hash, prior = self._responses[call_id]
            if prior_hash != argument_hash:
                self.reason_codes.append("SOURCE_REPLAY_INCONSISTENT")
                return SourceToolCallResult(False, "SOURCE_REPLAY_INCONSISTENT", {}, False)
            return prior

        self.source_call_count += 1
        if dict(arguments):
            result = SourceToolCallResult(False, "SOURCE_ARGUMENTS_INVALID", {}, False)
            self.reason_codes.append(result.code)
            self._responses[call_id] = (argument_hash, result)
            return result
        if self._successful_call_id is not None:
            result = SourceToolCallResult(False, "SOURCE_ALREADY_CONSUMED", {}, False)
            self.reason_codes.append(result.code)
            self._responses[call_id] = (argument_hash, result)
            return result

        payload = {
            **FIXED_SOURCE_IDENTITY.as_dict(),
            "content": self._source.decode("utf-8"),
        }
        result = SourceToolCallResult(True, "SOURCE_DISCLOSED", payload, True)
        self._successful_call_id = call_id
        self.semantic_disclosure_count = 1
        self.distinct_exposed_source_count = 1
        self._responses[call_id] = (argument_hash, result)
        return result


_MANUAL_AFTER_IDENTITIES = (
    MANUAL_AFTER_REVISION.encode("ascii"),
    MANUAL_AFTER_GIT_BLOB.encode("ascii"),
    MANUAL_AFTER_SHA256.encode("ascii"),
)


def manual_after_contamination_codes(
    control_material: Sequence[bytes],
    *,
    after_only_line_sha256: Iterable[str] = (),
) -> tuple[str, ...]:
    """Check control material only; the common Before is deliberately excluded."""

    line_hashes = frozenset(after_only_line_sha256)
    codes: set[str] = set()
    for value in control_material:
        if not isinstance(value, bytes):
            codes.add("CONTROL_MATERIAL_INVALID")
            continue
        if any(identity in value for identity in _MANUAL_AFTER_IDENTITIES):
            codes.add("MANUAL_AFTER_IDENTITY_EXPOSED")
        text = value.decode("utf-8", errors="replace")
        if (
            re.search(r"(?:UTF-?8[ _-]*bytes?|byte[ _-]*count)\s*[\"']?\s*[:=]\s*11[,_]?147", text, re.I)
            or re.search(r"(?:line[ _-]*count|lines?)\s*[\"']?\s*[:=]\s*359\b", text, re.I)
        ):
            codes.add("MANUAL_AFTER_METRICS_EXPOSED")
        if (
            "--- before/AGENTS.md" in text
            or "+++ after/AGENTS.md" in text
            or re.search(r"(?m)^@@ -\d", text)
        ):
            codes.add("MANUAL_AFTER_DIFF_EXPOSED")
        if any(_sha256(line) in line_hashes for line in value.splitlines()):
            codes.add("MANUAL_AFTER_ONLY_TEXT_EXPOSED")
    return tuple(sorted(codes))


@dataclass(frozen=True)
class IsolationEvidence:
    contract_identity_sha256: str | None
    run_1_task_sha256: str | None
    developer_instructions_sha256: str | None
    dynamic_tool_manifest_sha256: str | None
    runtime_identity_sha256: str | None
    isolation_features_sha256: str | None
    candidate_visible_input_set_sha256: str | None
    event_log_sha256: str | None
    source_identity_sha256: str | None
    source_call_count: int
    semantic_disclosure_count: int
    distinct_exposed_source_count: int
    repository_read_count: int
    current_after_access_count: int
    git_access_count: int
    prohibited_capability_event_count: int
    proposal_call_count: int
    proposal_after_source: bool
    normal_terminal: bool
    capability_surface_complete: bool
    native_or_implicit_reader_absent: bool
    manual_after_exposure_codes: tuple[str, ...] = ()
    event_reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceIsolationReceipt:
    result: str
    reason_codes: tuple[str, ...]
    source_identity: Mapping[str, Any]
    source_identity_sha256: str | None
    source_call_count: int
    successful_semantic_disclosure_count: int
    distinct_exposed_source_count: int
    repository_read_count: int
    current_after_access_count: int
    git_access_count: int
    prohibited_capability_event_count: int
    dynamic_tool_manifest_sha256: str | None
    isolation_features_sha256: str | None
    event_log_sha256: str | None
    normal_terminal: bool
    schema: str = SOURCE_ISOLATION_SCHEMA
    candidate_id: str = CANDIDATE_ID

    def __post_init__(self) -> None:
        if self.result not in QUALIFICATION_RESULTS:
            raise CandidateV02Error("SOURCE_ISOLATION_RESULT_INVALID")

    def body(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "candidate_id": self.candidate_id,
            "result": self.result,
            "reason_codes": list(self.reason_codes),
            "source_identity": dict(self.source_identity),
            "source_identity_sha256": self.source_identity_sha256,
            "source_call_count": self.source_call_count,
            "successful_semantic_disclosure_count": self.successful_semantic_disclosure_count,
            "distinct_exposed_source_count": self.distinct_exposed_source_count,
            "repository_read_count": self.repository_read_count,
            "current_after_access_count": self.current_after_access_count,
            "git_access_count": self.git_access_count,
            "prohibited_capability_event_count": self.prohibited_capability_event_count,
            "dynamic_tool_manifest_sha256": self.dynamic_tool_manifest_sha256,
            "isolation_features_sha256": self.isolation_features_sha256,
            "event_log_sha256": self.event_log_sha256,
            "normal_terminal": self.normal_terminal,
        }

    @property
    def receipt_sha256(self) -> str:
        return _sha256(_canonical_bytes(self.body()))

    def as_dict(self) -> dict[str, Any]:
        return {**self.body(), "receipt_sha256": self.receipt_sha256}

    @classmethod
    def from_dict(cls, value: Any) -> "SourceIsolationReceipt":
        body_fields = {
            "schema", "candidate_id", "result", "reason_codes",
            "source_identity", "source_identity_sha256", "source_call_count",
            "successful_semantic_disclosure_count", "distinct_exposed_source_count",
            "repository_read_count", "current_after_access_count", "git_access_count",
            "prohibited_capability_event_count", "dynamic_tool_manifest_sha256",
            "isolation_features_sha256", "event_log_sha256", "normal_terminal",
        }
        if not isinstance(value, dict) or set(value) != body_fields | {"receipt_sha256"}:
            raise CandidateV02Error("SOURCE_ISOLATION_RECEIPT_INVALID")
        if not isinstance(value["reason_codes"], list) or not isinstance(
            value["source_identity"], dict
        ):
            raise CandidateV02Error("SOURCE_ISOLATION_RECEIPT_INVALID")
        try:
            result = cls(
                result=value["result"],
                reason_codes=tuple(value["reason_codes"]),
                source_identity=value["source_identity"],
                source_identity_sha256=value["source_identity_sha256"],
                source_call_count=value["source_call_count"],
                successful_semantic_disclosure_count=value[
                    "successful_semantic_disclosure_count"
                ],
                distinct_exposed_source_count=value["distinct_exposed_source_count"],
                repository_read_count=value["repository_read_count"],
                current_after_access_count=value["current_after_access_count"],
                git_access_count=value["git_access_count"],
                prohibited_capability_event_count=value[
                    "prohibited_capability_event_count"
                ],
                dynamic_tool_manifest_sha256=value["dynamic_tool_manifest_sha256"],
                isolation_features_sha256=value["isolation_features_sha256"],
                event_log_sha256=value["event_log_sha256"],
                normal_terminal=value["normal_terminal"],
                schema=value["schema"],
                candidate_id=value["candidate_id"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CandidateV02Error("SOURCE_ISOLATION_RECEIPT_INVALID") from exc
        if value["receipt_sha256"] != result.receipt_sha256:
            raise CandidateV02Error("SOURCE_ISOLATION_RECEIPT_SHA_INVALID")
        return result


@dataclass(frozen=True)
class IndependenceReceipt:
    result: str
    reason_codes: tuple[str, ...]
    source_isolation_receipt_sha256: str
    contract_identity_sha256: str | None
    run_1_task_sha256: str | None
    developer_instructions_sha256: str | None
    runtime_identity_sha256: str | None
    candidate_visible_input_set_sha256: str | None
    manual_after_exposure_codes: tuple[str, ...]
    proposal_call_count: int
    proposal_after_source: bool
    normal_terminal: bool
    latent_model_memory_excluded: bool = False
    schema: str = INDEPENDENCE_SCHEMA
    candidate_id: str = CANDIDATE_ID

    def __post_init__(self) -> None:
        if self.result not in QUALIFICATION_RESULTS:
            raise CandidateV02Error("INDEPENDENCE_RESULT_INVALID")
        _require_sha256(
            self.source_isolation_receipt_sha256,
            "SOURCE_ISOLATION_RECEIPT_SHA_INVALID",
        )
        if self.latent_model_memory_excluded:
            raise CandidateV02Error("LATENT_MODEL_MEMORY_NONCLAIM_VIOLATED")

    def body(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "candidate_id": self.candidate_id,
            "result": self.result,
            "reason_codes": list(self.reason_codes),
            "source_isolation_receipt_sha256": self.source_isolation_receipt_sha256,
            "contract_identity_sha256": self.contract_identity_sha256,
            "run_1_task_sha256": self.run_1_task_sha256,
            "developer_instructions_sha256": self.developer_instructions_sha256,
            "runtime_identity_sha256": self.runtime_identity_sha256,
            "candidate_visible_input_set_sha256": self.candidate_visible_input_set_sha256,
            "manual_after_exposure_codes": list(self.manual_after_exposure_codes),
            "proposal_call_count": self.proposal_call_count,
            "proposal_after_source": self.proposal_after_source,
            "normal_terminal": self.normal_terminal,
            "latent_model_memory_excluded": False,
        }

    @property
    def receipt_sha256(self) -> str:
        return _sha256(_canonical_bytes(self.body()))

    def as_dict(self) -> dict[str, Any]:
        return {**self.body(), "receipt_sha256": self.receipt_sha256}

    @classmethod
    def from_dict(cls, value: Any) -> "IndependenceReceipt":
        body_fields = {
            "schema", "candidate_id", "result", "reason_codes",
            "source_isolation_receipt_sha256", "contract_identity_sha256",
            "run_1_task_sha256", "developer_instructions_sha256",
            "runtime_identity_sha256", "candidate_visible_input_set_sha256",
            "manual_after_exposure_codes", "proposal_call_count",
            "proposal_after_source", "normal_terminal", "latent_model_memory_excluded",
        }
        if not isinstance(value, dict) or set(value) != body_fields | {"receipt_sha256"}:
            raise CandidateV02Error("INDEPENDENCE_RECEIPT_INVALID")
        if not isinstance(value["reason_codes"], list) or not isinstance(
            value["manual_after_exposure_codes"], list
        ):
            raise CandidateV02Error("INDEPENDENCE_RECEIPT_INVALID")
        try:
            result = cls(
                result=value["result"],
                reason_codes=tuple(value["reason_codes"]),
                source_isolation_receipt_sha256=value[
                    "source_isolation_receipt_sha256"
                ],
                contract_identity_sha256=value["contract_identity_sha256"],
                run_1_task_sha256=value["run_1_task_sha256"],
                developer_instructions_sha256=value["developer_instructions_sha256"],
                runtime_identity_sha256=value["runtime_identity_sha256"],
                candidate_visible_input_set_sha256=value[
                    "candidate_visible_input_set_sha256"
                ],
                manual_after_exposure_codes=tuple(
                    value["manual_after_exposure_codes"]
                ),
                proposal_call_count=value["proposal_call_count"],
                proposal_after_source=value["proposal_after_source"],
                normal_terminal=value["normal_terminal"],
                latent_model_memory_excluded=value["latent_model_memory_excluded"],
                schema=value["schema"],
                candidate_id=value["candidate_id"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CandidateV02Error("INDEPENDENCE_RECEIPT_INVALID") from exc
        if value["receipt_sha256"] != result.receipt_sha256:
            raise CandidateV02Error("INDEPENDENCE_RECEIPT_SHA_INVALID")
        return result


def isolation_features_sha256() -> str:
    return _sha256(canonical_json(ISOLATION_FEATURES).encode("utf-8"))


def candidate_visible_input_set_sha256(
    task_bytes: bytes,
    developer_instructions: bytes,
    dynamic_tools: Sequence[Mapping[str, Any]],
    *,
    attachments: Sequence[bytes] = (),
) -> str:
    manifest = {
        "task_sha256": _sha256(task_bytes),
        "developer_instructions_sha256": _sha256(developer_instructions),
        "dynamic_tool_manifest_sha256": _sha256(
            canonical_json(list(dynamic_tools)).encode("utf-8")
        ),
        "attachment_count": len(attachments),
        "attachment_sha256": [_sha256(value) for value in attachments],
    }
    return _sha256(canonical_json(manifest).encode("utf-8"))


def fixed_candidate_visible_input_set_sha256() -> str:
    manifest = {
        "task_sha256": RUN_1_SHA256,
        "developer_instructions_sha256": DEVELOPER_INSTRUCTIONS_SHA256,
        "dynamic_tool_manifest_sha256": dynamic_tool_manifest_sha256(),
        "attachment_count": 0,
        "attachment_sha256": [],
    }
    return _sha256(canonical_json(manifest).encode("utf-8"))


def qualify_independence(
    evidence: IsolationEvidence,
) -> tuple[SourceIsolationReceipt, IndependenceReceipt]:
    sha_fields = (
        evidence.contract_identity_sha256,
        evidence.run_1_task_sha256,
        evidence.developer_instructions_sha256,
        evidence.dynamic_tool_manifest_sha256,
        evidence.runtime_identity_sha256,
        evidence.isolation_features_sha256,
        evidence.candidate_visible_input_set_sha256,
        evidence.event_log_sha256,
        evidence.source_identity_sha256,
    )
    count_fields = (
        evidence.source_call_count,
        evidence.semantic_disclosure_count,
        evidence.distinct_exposed_source_count,
        evidence.repository_read_count,
        evidence.current_after_access_count,
        evidence.git_access_count,
        evidence.prohibited_capability_event_count,
        evidence.proposal_call_count,
    )
    boolean_fields = (
        evidence.proposal_after_source,
        evidence.normal_terminal,
        evidence.capability_surface_complete,
        evidence.native_or_implicit_reader_absent,
    )
    malformed = (
        any(value is not None and not _is_sha256(value) for value in sha_fields)
        or any(type(value) is not int or value < 0 for value in count_fields)
        or any(type(value) is not bool for value in boolean_fields)
        or not isinstance(evidence.manual_after_exposure_codes, tuple)
        or not isinstance(evidence.event_reason_codes, tuple)
        or any(
            not isinstance(value, str) or not value
            for value in (
                *evidence.manual_after_exposure_codes,
                *evidence.event_reason_codes,
            )
        )
    )
    missing = (
        malformed
        or any(value is None for value in sha_fields)
        or evidence.capability_surface_complete is not True
        or evidence.native_or_implicit_reader_absent is not True
    )

    valid_event_codes = isinstance(evidence.event_reason_codes, tuple) and all(
        isinstance(value, str) and bool(value) for value in evidence.event_reason_codes
    )
    valid_manual_codes = isinstance(
        evidence.manual_after_exposure_codes, tuple
    ) and all(
        isinstance(value, str) and bool(value)
        for value in evidence.manual_after_exposure_codes
    )
    positive_codes: set[str] = (
        set(evidence.event_reason_codes) if valid_event_codes else set()
    )
    if type(evidence.source_call_count) is int and evidence.source_call_count >= 0:
        if evidence.source_call_count != 1:
            positive_codes.add("SOURCE_CALL_COUNT_INVALID")
    if (
        type(evidence.semantic_disclosure_count) is int
        and evidence.semantic_disclosure_count >= 0
    ):
        if evidence.semantic_disclosure_count != 1:
            positive_codes.add("SOURCE_DISCLOSURE_COUNT_INVALID")
    if (
        type(evidence.distinct_exposed_source_count) is int
        and evidence.distinct_exposed_source_count >= 0
    ):
        if evidence.distinct_exposed_source_count != 1:
            positive_codes.add("DISTINCT_SOURCE_COUNT_INVALID")
    for observed, code in (
        (evidence.repository_read_count, "REPOSITORY_READ_OBSERVED"),
        (evidence.current_after_access_count, "CURRENT_AFTER_ACCESS_OBSERVED"),
        (evidence.git_access_count, "GIT_ACCESS_OBSERVED"),
        (evidence.prohibited_capability_event_count, "PROHIBITED_CAPABILITY_EVENT"),
    ):
        if type(observed) is int and observed > 0:
            positive_codes.add(code)
    expected_identities = (
        (evidence.source_identity_sha256, fixed_source_identity_sha256(), "SOURCE_IDENTITY_INVALID"),
        (evidence.dynamic_tool_manifest_sha256, dynamic_tool_manifest_sha256(), "DYNAMIC_TOOL_MANIFEST_INVALID"),
        (evidence.isolation_features_sha256, isolation_features_sha256(), "ISOLATION_FEATURES_INVALID"),
        (evidence.run_1_task_sha256, RUN_1_SHA256, "RUN_1_TASK_IDENTITY_INVALID"),
        (evidence.developer_instructions_sha256, DEVELOPER_INSTRUCTIONS_SHA256, "DEVELOPER_INSTRUCTIONS_IDENTITY_INVALID"),
        (evidence.candidate_visible_input_set_sha256, fixed_candidate_visible_input_set_sha256(), "CANDIDATE_VISIBLE_INPUT_SET_INVALID"),
    )
    for observed, expected, code in expected_identities:
        if _is_sha256(observed) and observed != expected:
            positive_codes.add(code)
    if valid_manual_codes and evidence.manual_after_exposure_codes:
        positive_codes.update(evidence.manual_after_exposure_codes)
    if type(evidence.proposal_call_count) is int and evidence.proposal_call_count >= 0:
        if evidence.proposal_call_count != 1:
            positive_codes.add("PROPOSAL_CALL_COUNT_INVALID")
    if type(evidence.proposal_after_source) is bool and not evidence.proposal_after_source:
        positive_codes.add("PROPOSAL_BEFORE_SOURCE")
    if type(evidence.normal_terminal) is bool and not evidence.normal_terminal:
        positive_codes.add("RUN_NOT_NORMAL_TERMINAL")

    if positive_codes:
        result = "FAIL"
        reasons = tuple(sorted(positive_codes))
    elif missing:
        result = "NOT_ESTABLISHED"
        reasons = (
            "EVIDENCE_MALFORMED"
            if malformed
            else "REQUIRED_EVIDENCE_NOT_ESTABLISHED",
        )
    else:
        result = "PASS"
        reasons = ()

    isolation = SourceIsolationReceipt(
        result=result,
        reason_codes=reasons,
        source_identity=FIXED_SOURCE_IDENTITY.as_dict(),
        source_identity_sha256=evidence.source_identity_sha256,
        source_call_count=evidence.source_call_count,
        successful_semantic_disclosure_count=evidence.semantic_disclosure_count,
        distinct_exposed_source_count=evidence.distinct_exposed_source_count,
        repository_read_count=evidence.repository_read_count,
        current_after_access_count=evidence.current_after_access_count,
        git_access_count=evidence.git_access_count,
        prohibited_capability_event_count=evidence.prohibited_capability_event_count,
        dynamic_tool_manifest_sha256=evidence.dynamic_tool_manifest_sha256,
        isolation_features_sha256=evidence.isolation_features_sha256,
        event_log_sha256=evidence.event_log_sha256,
        normal_terminal=evidence.normal_terminal,
    )
    independence = IndependenceReceipt(
        result=result,
        reason_codes=reasons,
        source_isolation_receipt_sha256=isolation.receipt_sha256,
        contract_identity_sha256=evidence.contract_identity_sha256,
        run_1_task_sha256=evidence.run_1_task_sha256,
        developer_instructions_sha256=evidence.developer_instructions_sha256,
        runtime_identity_sha256=evidence.runtime_identity_sha256,
        candidate_visible_input_set_sha256=evidence.candidate_visible_input_set_sha256,
        manual_after_exposure_codes=evidence.manual_after_exposure_codes,
        proposal_call_count=evidence.proposal_call_count,
        proposal_after_source=evidence.proposal_after_source,
        normal_terminal=evidence.normal_terminal,
    )
    return isolation, independence


def require_source_isolation_pass(receipt: SourceIsolationReceipt) -> None:
    if (
        not isinstance(receipt, SourceIsolationReceipt)
        or receipt.schema != SOURCE_ISOLATION_SCHEMA
        or receipt.candidate_id != CANDIDATE_ID
        or receipt.result != "PASS"
        or receipt.reason_codes
        or dict(receipt.source_identity) != FIXED_SOURCE_IDENTITY.as_dict()
        or receipt.source_identity_sha256 != fixed_source_identity_sha256()
        or receipt.source_call_count != 1
        or receipt.successful_semantic_disclosure_count != 1
        or receipt.distinct_exposed_source_count != 1
        or receipt.repository_read_count != 0
        or receipt.current_after_access_count != 0
        or receipt.git_access_count != 0
        or receipt.prohibited_capability_event_count != 0
        or receipt.dynamic_tool_manifest_sha256 != dynamic_tool_manifest_sha256()
        or receipt.isolation_features_sha256 != isolation_features_sha256()
        or not _is_sha256(receipt.event_log_sha256)
        or receipt.normal_terminal is not True
    ):
        raise CandidateV02Error("SOURCE_ISOLATION_NOT_PASS")


def require_independence_pass(
    receipt: IndependenceReceipt,
    isolation: SourceIsolationReceipt,
) -> None:
    require_source_isolation_pass(isolation)
    if (
        not isinstance(receipt, IndependenceReceipt)
        or receipt.schema != INDEPENDENCE_SCHEMA
        or receipt.candidate_id != CANDIDATE_ID
        or receipt.result != "PASS"
        or receipt.reason_codes
        or receipt.source_isolation_receipt_sha256 != isolation.receipt_sha256
        or not _is_sha256(receipt.contract_identity_sha256)
        or receipt.run_1_task_sha256 != RUN_1_SHA256
        or receipt.developer_instructions_sha256 != DEVELOPER_INSTRUCTIONS_SHA256
        or not _is_sha256(receipt.runtime_identity_sha256)
        or receipt.candidate_visible_input_set_sha256
        != fixed_candidate_visible_input_set_sha256()
        or receipt.manual_after_exposure_codes
        or receipt.proposal_call_count != 1
        or receipt.proposal_after_source is not True
        or receipt.normal_terminal is not True
        or receipt.latent_model_memory_excluded is not False
    ):
        raise CandidateV02Error("INDEPENDENCE_NOT_PASS")


class CandidateV02A1AdmissionGate:
    """Hold a side-effect-free proposal until terminal independence PASS."""

    def admit(
        self,
        proposal: Any,
        *,
        isolation: SourceIsolationReceipt,
        independence: IndependenceReceipt,
    ) -> Any | None:
        try:
            require_independence_pass(independence, isolation)
        except CandidateV02Error:
            del proposal
            return None
        return proposal


@dataclass(frozen=True)
class CompressionReceipt:
    schema: str
    diff_schema: str
    result: str
    before_byte_count: int
    after_byte_count: int
    reduction_byte_count: int
    reduction_fraction: str
    before_line_count: int
    after_line_count: int
    addition_count: int
    deletion_count: int
    changed_line_count: int
    diff_sha256: str
    diff_bytes: bytes

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "diff_schema": self.diff_schema,
            "result": self.result,
            "before_byte_count": self.before_byte_count,
            "after_byte_count": self.after_byte_count,
            "reduction_byte_count": self.reduction_byte_count,
            "reduction_fraction": self.reduction_fraction,
            "before_line_count": self.before_line_count,
            "after_line_count": self.after_line_count,
            "addition_count": self.addition_count,
            "deletion_count": self.deletion_count,
            "changed_line_count": self.changed_line_count,
            "diff_sha256": self.diff_sha256,
        }


def compression_receipt(before: bytes, after: bytes) -> CompressionReceipt:
    _fixed_bytes(before)
    try:
        before_text = before.decode("utf-8", errors="strict")
        after_text = after.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CandidateV02Error("COMPRESSION_UTF8_INVALID") from exc
    before_lines = before_text.splitlines(keepends=True)
    after_lines = after_text.splitlines(keepends=True)
    if not after.endswith(b"\n"):
        raise CandidateV02Error("COMPRESSION_AFTER_FINAL_LF_MISSING")
    matcher = difflib.SequenceMatcher(None, before_lines, after_lines, autojunk=False)
    additions = deletions = 0
    for tag, a0, a1, b0, b1 in matcher.get_opcodes():
        if tag in {"replace", "delete"}:
            deletions += a1 - a0
        if tag in {"replace", "insert"}:
            additions += b1 - b0
    diff = "".join(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile="before/AGENTS.md",
            tofile="after/AGENTS.md",
            n=3,
            lineterm="\n",
        )
    ).encode("utf-8")
    reduction = len(before) - len(after)
    fraction = (Decimal(reduction) / Decimal(SOURCE_BYTE_COUNT)).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_UP
    )
    return CompressionReceipt(
        schema=COMPRESSION_SCHEMA,
        diff_schema=DIFF_SCHEMA,
        result="PASS" if len(after) < SOURCE_BYTE_COUNT else "FAIL",
        before_byte_count=len(before),
        after_byte_count=len(after),
        reduction_byte_count=reduction,
        reduction_fraction=format(fraction, ".6f"),
        before_line_count=_line_count(before),
        after_line_count=_line_count(after),
        addition_count=additions,
        deletion_count=deletions,
        changed_line_count=additions + deletions,
        diff_sha256=_sha256(diff),
        diff_bytes=diff,
    )


@dataclass(frozen=True)
class BoundarySpec:
    boundary_id: str
    matcher_id: str
    locator: str
    rationale: str
    patterns: tuple[str, ...]


BOUNDARY_SPECS: tuple[BoundarySpec, ...] = (
    BoundarySpec(
        "B01_HUMAN_SEAT",
        "boundary.b01.v0.1",
        "B01 Human Seat:",
        "Historical Before lines 240–275 preserve the operator's final Seat while agents provide bounded continuation signals.",
        (r"\b(?:human|shin|decision owner)\b", r"\b(?:final seat|final decision|final approval)\b", r"\b(?:retain|retains|hold|holds|own|owns)\b"),
    ),
    BoundarySpec(
        "B02_AUTHORITY",
        "boundary.b02.v0.1",
        "B02 Authority Boundary:",
        "Historical Before lines 95–120 require exact identity, ownership, validity, freshness, and authority without path, repository, or version substitution.",
        (r"\b(?:authori[sz](?:e|ed|ation)|authority)\b", r"\b(?:scope|repository|branch|commit|operation|gate|completion line)\b", r"\b(?:do not infer|must not infer|no inference|does not create authority|no expansion|must not expand)\b"),
    ),
    BoundarySpec(
        "B03_GUARD_SAFETY",
        "boundary.b03.v0.1",
        "B03 Guard and Safety:",
        "Historical Before lines 349–374 and 488–494 preserve evidence-based promotion, rollback conditions, and prompt-injection safety stops; the candidate contract additionally protects fixed artifacts and tests.",
        (r"\b(?:protected artifacts?|tests?|hash(?:es)?)\b", r"\b(?:safety|guard)\b", r"\b(?:preserve|preserves|do not weaken|must not weaken)\b"),
    ),
    BoundarySpec(
        "B04_RESPONSIBILITY_TRANSFER",
        "boundary.b04.v0.1",
        "B04 Responsibility Transfer:",
        "Historical Before lines 21–63 and 127–175 require restartable handoff evidence, owned next action, and closing-agent responsibility.",
        (r"\b(?:handoff|receiv(?:e|er|ing))\b", r"\b(?:responsibility|ownership|owns?|owned)\b", r"\b(?:closure|next action|completion line)\b"),
    ),
    BoundarySpec(
        "B05_STOP_CONDITIONS",
        "boundary.b05.v0.1",
        "B05 Stop Conditions:",
        "Historical Before lines 31–37, 89–91, and 101–120 require HOLD, CAP, or BLOCK when prerequisites or sufficient proof are missing.",
        (r"\bstop\b", r"\b(?:hold|block)\b", r"\b(?:mismatch|missing|prerequisite|unresolved|unsafe)\b"),
    ),
    BoundarySpec(
        "B06_EVIDENCE_PROVENANCE",
        "boundary.b06.v0.1",
        "B06 Evidence and Provenance:",
        "Historical Before lines 21–29 and 95–125 require completion evidence, exact provenance, verified identity, and bounded recovery before continuation.",
        (r"\b(?:identity|provenance)\b", r"\b(?:evidence|readback|read-back|verification|verified)\b", r"\b(?:before|require|required|must)\b"),
    ),
    BoundarySpec(
        "B07_HANDOFF_COMPLETION",
        "boundary.b07.v0.1",
        "B07 Handoff and Completion:",
        "Historical Before lines 21–63 and 127–177 require handoff restart state, a Completion Line, and the next safe action.",
        (r"\b(?:handoff|restart)\b", r"\bcompletion line\b", r"\b(?:next safe action|next authorized action|next action)\b"),
    ),
    BoundarySpec(
        "B08_AGENT_HUMAN_ROLES",
        "boundary.b08.v0.1",
        "B08 Agent and Human Roles:",
        "Historical Before lines 129–175 and 240–275 separate bounded agent reporting from the human operator's final decision.",
        (r"\bagents?\b", r"\b(?:bounded work|bounded execution|execute|executes)\b", r"\b(?:human|decision owner)\b", r"\b(?:risk|value|approval|externalization)\b"),
    ),
    BoundarySpec(
        "B09_ROUTINE_CLEANUP",
        "boundary.b09.v0.1",
        "B09 Routine Cleanup:",
        "Historical Before lines 101–120 require the executing agent to perform bounded routine recovery rather than return it to the Owner.",
        (r"\broutine cleanup\b", r"\b(?:agent|executing agent|ai)\b", r"\b(?:not returned|do not return|must not return)\b", r"\b(?:shin|decision owner)\b"),
    ),
    BoundarySpec(
        "B10_FORWARD_ROLLBACK",
        "boundary.b10.v0.1",
        "B10 Forward Change and Rollback:",
        "Historical Before lines 21–29 and 367–374 require rollback, recheck, and downgrade paths; the candidate contract separately fixes Forward-only repair and protected-history preservation.",
        (r"\b(?:forward-only|forward change|normal revert)\b", r"\b(?:rollback|source recovery|revert)\b", r"\b(?:preserve|preserves|protected history|protected artifacts?)\b"),
    ),
)


def check_boundaries_v0_2(
    after: bytes,
    safety: SafetyReceipt,
) -> tuple[BoundaryResult, ...]:
    try:
        after.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CandidateV02Error("BOUNDARY_AFTER_NOT_UTF8") from exc
    if not after.endswith(b"\n"):
        raise CandidateV02Error("BOUNDARY_FINAL_LF_MISSING")
    lines = after[:-1].split(b"\n")
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for line in lines:
        offsets.append((cursor, cursor + len(line)))
        cursor += len(line) + 1
    results: list[BoundaryResult] = []
    for spec in BOUNDARY_SPECS:
        locator = spec.locator.encode("ascii")
        matches = [index for index, line in enumerate(lines) if line.startswith(locator)]
        if len(matches) > 1:
            status, index = "AMBIGUOUS", matches[0]
        elif not matches:
            status, index = "MISSING", None
        else:
            index = matches[0]
            text = lines[index].decode("utf-8")
            status = (
                "PRESENT"
                if all(re.search(pattern, text, re.I | re.ASCII) for pattern in spec.patterns)
                else "MISSING"
            )
        line_hash = _sha256(lines[index]) if index is not None else None
        expose = index is not None and status == "PRESENT" and safety.result == "PASS"
        start, end = offsets[index] if expose and index is not None else (None, None)
        results.append(
            BoundaryResult(
                spec.boundary_id,
                spec.matcher_id,
                spec.locator,
                spec.rationale,
                status,
                "MANDATORY",
                line_hash,
                start,
                end,
            )
        )
    return tuple(results)


@dataclass(frozen=True)
class WitnessBindingV02:
    schema: str
    candidate_id: str
    note_identity_sha256: str
    note_content_sha256: str
    projection_sha256: str
    locator: str
    witness_utf8_byte_count: int
    witness_sha256: str
    source_start_byte: int
    source_end_byte: int
    projection_start_byte: int
    projection_end_byte: int
    source_occurrence_count: int
    projection_occurrence_count: int
    policy_result: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def bind_generated_witness_v0_2(
    note_identity: FieldNoteIdentity,
    note_bytes: bytes,
    projection: PublicAfterProjection,
    run_1_task: bytes,
    run_2_task: bytes,
    safety: SafetyReceipt,
) -> WitnessBindingV02:
    if not isinstance(note_identity, FieldNoteIdentity):
        raise CandidateV02Error("WITNESS_NOTE_IDENTITY_INVALID")
    if _sha256(note_bytes) != note_identity.note_sha256:
        raise CandidateV02Error("WITNESS_NOTE_CONTENT_MISMATCH")
    source_lines = tuple(
        line for line in note_bytes.split(b"\n") if line.startswith(WITNESS_LOCATOR)
    )
    projection_lines = tuple(
        line for line in projection.body.split(b"\n") if line.startswith(WITNESS_LOCATOR)
    )
    if len(source_lines) != 1 or len(projection_lines) != 1:
        raise CandidateV02Error("WITNESS_OCCURRENCE_COUNT_INVALID")
    witness = source_lines[0]
    if (
        witness != projection_lines[0]
        or note_bytes.count(witness) != 1
        or projection.body.count(witness) != 1
        or witness in {note_bytes, projection.body}
    ):
        raise CandidateV02Error("WITNESS_EXACT_BINDING_INVALID")
    suffix = witness[len(WITNESS_LOCATOR) :]
    try:
        suffix_text = suffix.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CandidateV02Error("WITNESS_NOT_UTF8") from exc
    nonspace_bytes = sum(
        len(character.encode("utf-8"))
        for character in suffix_text
        if not character.isspace()
    )
    words = re.findall(r"[A-Za-z]+", suffix_text, re.ASCII)
    word_counts = Counter(word.casefold() for word in words)
    complete_invariant = any(
        all(re.search(pattern, suffix_text, re.I | re.ASCII) for pattern in spec.patterns)
        for spec in BOUNDARY_SPECS
    )
    if (
        nonspace_bytes < 32
        or len(words) < 6
        or not complete_invariant
        or len({word.casefold() for word in words}) * 2 < len(words)
        or any(count > 2 for count in word_counts.values())
    ):
        raise CandidateV02Error("WITNESS_MEANING_POLICY_FAILED")
    if re.fullmatch(r"(?:0x)?[0-9a-fA-F_-]+", re.sub(r"\s+", "", suffix_text)):
        raise CandidateV02Error("WITNESS_NONCE_ONLY")
    if witness in run_1_task or witness in run_2_task:
        raise CandidateV02Error("WITNESS_PRESENT_IN_TASK")
    if safety.result != "PASS":
        raise CandidateV02Error("WITNESS_SAFETY_NOT_PASS")
    source_start = note_bytes.index(witness)
    projection_start = projection.body.index(witness)
    note_identity_sha = _sha256(canonical_json(note_identity.as_dict()).encode("utf-8"))
    return WitnessBindingV02(
        WITNESS_SCHEMA,
        CANDIDATE_ID,
        note_identity_sha,
        note_identity.note_sha256,
        projection.sha256,
        WITNESS_LOCATOR.decode("ascii"),
        len(witness),
        _sha256(witness),
        source_start,
        source_start + len(witness),
        projection_start,
        projection_start + len(witness),
        1,
        1,
        "PASS",
    )


def _receipt_digest(value: Mapping[str, Any]) -> str:
    return _sha256(_canonical_bytes(value))


@dataclass(frozen=True)
class PostA1GateReadbackV02:
    schema: str
    candidate_id: str
    result: str
    source_identity: Mapping[str, Any]
    task_identities: tuple[Mapping[str, Any], Mapping[str, Any]]
    source_isolation: Mapping[str, Any]
    independence: Mapping[str, Any]
    projection: Mapping[str, Any]
    compression: Mapping[str, Any]
    safety: Mapping[str, Any]
    boundaries: tuple[Mapping[str, Any], ...]
    witness_binding: Mapping[str, Any]
    unauthorized_projection_metadata_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "candidate_id": self.candidate_id,
            "result": self.result,
            "source_identity": dict(self.source_identity),
            "task_identities": [dict(value) for value in self.task_identities],
            "source_isolation": dict(self.source_isolation),
            "independence": dict(self.independence),
            "projection": dict(self.projection),
            "compression": dict(self.compression),
            "safety": dict(self.safety),
            "boundaries": [dict(value) for value in self.boundaries],
            "witness_binding": dict(self.witness_binding),
            "unauthorized_projection_metadata_count": self.unauthorized_projection_metadata_count,
        }

    @property
    def readback_sha256(self) -> str:
        return _sha256(_canonical_bytes(self.as_dict()))

    @classmethod
    def from_dict(cls, value: Any) -> "PostA1GateReadbackV02":
        fields = {
            "schema",
            "candidate_id",
            "result",
            "source_identity",
            "task_identities",
            "source_isolation",
            "independence",
            "projection",
            "compression",
            "safety",
            "boundaries",
            "witness_binding",
            "unauthorized_projection_metadata_count",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise CandidateV02Error("POST_A1_READBACK_INVALID")
        if not isinstance(value["task_identities"], list) or not isinstance(
            value["boundaries"], list
        ):
            raise CandidateV02Error("POST_A1_READBACK_INVALID")
        result = cls(
            schema=value["schema"],
            candidate_id=value["candidate_id"],
            result=value["result"],
            source_identity=value["source_identity"],
            task_identities=tuple(value["task_identities"]),
            source_isolation=value["source_isolation"],
            independence=value["independence"],
            projection=value["projection"],
            compression=value["compression"],
            safety=value["safety"],
            boundaries=tuple(value["boundaries"]),
            witness_binding=value["witness_binding"],
            unauthorized_projection_metadata_count=value[
                "unauthorized_projection_metadata_count"
            ],
        )
        require_post_a1_gate_for_a2(result)
        return result


def issue_post_a1_gate_v0_2(
    *,
    before: bytes,
    task_bytes: tuple[bytes, bytes],
    note_identity: FieldNoteIdentity,
    note_bytes: bytes,
    source_isolation: SourceIsolationReceipt,
    independence: IndependenceReceipt,
    projection: PublicAfterProjection,
    compression: CompressionReceipt,
    safety: SafetyReceipt,
    boundaries: Sequence[BoundaryResult],
    witness_binding: WitnessBindingV02,
) -> PostA1GateReadbackV02:
    _fixed_bytes(before)
    require_independence_pass(independence, source_isolation)
    for data, identity in zip(task_bytes, FIXED_TASK_IDENTITIES, strict=True):
        _fixed_bytes(data, task=identity)
    expected_projection = project_public_after(note_bytes)
    expected_compression = compression_receipt(before, expected_projection.body)
    expected_safety = public_safety(expected_projection.body)
    expected_boundaries = check_boundaries_v0_2(expected_projection.body, expected_safety)
    expected_witness = bind_generated_witness_v0_2(
        note_identity,
        note_bytes,
        expected_projection,
        task_bytes[0],
        task_bytes[1],
        expected_safety,
    )
    unauthorized_count = sum(
        expected_projection.body.lower().count(marker)
        for marker in _PRIVATE_PROJECTION_FIELD_MARKERS
    ) + sum(
        1
        for pattern in _PRIVATE_PROJECTION_LABEL_PATTERNS
        if pattern.search(expected_projection.body)
    )
    if (
        projection != expected_projection
        or compression != expected_compression
        or safety != expected_safety
        or tuple(boundaries) != expected_boundaries
        or witness_binding != expected_witness
        or compression.result != "PASS"
        or safety.result != "PASS"
        or any(value.status != "PRESENT" for value in boundaries)
        or unauthorized_count
    ):
        raise CandidateV02Error("POST_A1_CANDIDATE_GATE_NOT_PASS")
    return PostA1GateReadbackV02(
        schema=POST_A1_SCHEMA,
        candidate_id=CANDIDATE_ID,
        result="PASS",
        source_identity=FIXED_SOURCE_IDENTITY.as_dict(),
        task_identities=tuple(value.as_dict() for value in FIXED_TASK_IDENTITIES),
        source_isolation=source_isolation.as_dict(),
        independence=independence.as_dict(),
        projection=projection.identity_dict(),
        compression=compression.as_dict(),
        safety=safety.as_dict(),
        boundaries=tuple(value.as_dict() for value in boundaries),
        witness_binding=witness_binding.as_dict(),
        unauthorized_projection_metadata_count=0,
    )


def require_post_a1_gate_for_a2(readback: PostA1GateReadbackV02) -> None:
    try:
        if not isinstance(readback, PostA1GateReadbackV02):
            raise CandidateV02Error("A2_POST_A1_GATE_NOT_PASS")
        isolation = SourceIsolationReceipt.from_dict(dict(readback.source_isolation))
        independence = IndependenceReceipt.from_dict(dict(readback.independence))
        require_independence_pass(independence, isolation)

        projection = dict(readback.projection)
        compression = dict(readback.compression)
        safety = dict(readback.safety)
        witness = dict(readback.witness_binding)
        if (
            readback.schema != POST_A1_SCHEMA
            or readback.candidate_id != CANDIDATE_ID
            or readback.result != "PASS"
            or dict(readback.source_identity) != FIXED_SOURCE_IDENTITY.as_dict()
            or tuple(readback.task_identities)
            != tuple(value.as_dict() for value in FIXED_TASK_IDENTITIES)
            or set(projection)
            != {"schema", "utf8_byte_count", "line_count", "sha256"}
            or projection.get("schema") != PROJECTION_SCHEMA
            or type(projection.get("utf8_byte_count")) is not int
            or not 0 < projection["utf8_byte_count"] < SOURCE_BYTE_COUNT
            or type(projection.get("line_count")) is not int
            or projection["line_count"] <= 0
            or not _is_sha256(projection.get("sha256"))
            or set(compression)
            != {
                "schema", "diff_schema", "result", "before_byte_count",
                "after_byte_count", "reduction_byte_count", "reduction_fraction",
                "before_line_count", "after_line_count", "addition_count",
                "deletion_count", "changed_line_count", "diff_sha256",
            }
            or compression.get("schema") != COMPRESSION_SCHEMA
            or compression.get("diff_schema") != DIFF_SCHEMA
            or compression.get("result") != "PASS"
            or compression.get("before_byte_count") != SOURCE_BYTE_COUNT
            or compression.get("after_byte_count") != projection["utf8_byte_count"]
            or compression.get("reduction_byte_count")
            != SOURCE_BYTE_COUNT - projection["utf8_byte_count"]
            or compression.get("before_line_count") != SOURCE_LINE_COUNT
            or compression.get("after_line_count") != projection["line_count"]
            or any(
                type(compression.get(name)) is not int or compression[name] < 0
                for name in ("addition_count", "deletion_count", "changed_line_count")
            )
            or compression["changed_line_count"]
            != compression["addition_count"] + compression["deletion_count"]
            or compression.get("reduction_fraction")
            != format(
                (
                    Decimal(compression["reduction_byte_count"])
                    / Decimal(SOURCE_BYTE_COUNT)
                ).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
                ".6f",
            )
            or not _is_sha256(compression.get("diff_sha256"))
            or safety
            != {"schema": SAFETY_SCHEMA, "result": "PASS", "finding_codes": []}
            or readback.unauthorized_projection_metadata_count != 0
        ):
            raise CandidateV02Error("A2_POST_A1_GATE_NOT_PASS")

        if len(readback.boundaries) != len(BOUNDARY_SPECS):
            raise CandidateV02Error("A2_POST_A1_GATE_NOT_PASS")
        boundary_fields = {
            "boundary_id", "matcher_id", "locator", "rationale", "status",
            "severity", "line_sha256", "start_byte", "end_byte",
        }
        for value, spec in zip(readback.boundaries, BOUNDARY_SPECS, strict=True):
            if (
                not isinstance(value, Mapping)
                or set(value) != boundary_fields
                or value.get("boundary_id") != spec.boundary_id
                or value.get("matcher_id") != spec.matcher_id
                or value.get("locator") != spec.locator
                or value.get("rationale") != spec.rationale
                or value.get("status") != "PRESENT"
                or value.get("severity") != "MANDATORY"
                or not _is_sha256(value.get("line_sha256"))
                or type(value.get("start_byte")) is not int
                or type(value.get("end_byte")) is not int
                or not 0 <= value["start_byte"] < value["end_byte"]
                <= projection["utf8_byte_count"]
            ):
                raise CandidateV02Error("A2_POST_A1_GATE_NOT_PASS")

        witness_fields = {
            "schema", "candidate_id", "note_identity_sha256",
            "note_content_sha256", "projection_sha256", "locator",
            "witness_utf8_byte_count", "witness_sha256", "source_start_byte",
            "source_end_byte", "projection_start_byte", "projection_end_byte",
            "source_occurrence_count", "projection_occurrence_count", "policy_result",
        }
        integer_fields = (
            "source_start_byte", "source_end_byte", "projection_start_byte",
            "projection_end_byte", "witness_utf8_byte_count",
        )
        if (
            set(witness) != witness_fields
            or witness.get("schema") != WITNESS_SCHEMA
            or witness.get("candidate_id") != CANDIDATE_ID
            or witness.get("projection_sha256") != projection["sha256"]
            or witness.get("locator") != WITNESS_LOCATOR.decode("ascii")
            or witness.get("source_occurrence_count") != 1
            or witness.get("projection_occurrence_count") != 1
            or witness.get("policy_result") != "PASS"
            or any(not _is_sha256(witness.get(name)) for name in (
                "note_identity_sha256", "note_content_sha256", "witness_sha256"
            ))
            or any(type(witness.get(name)) is not int for name in integer_fields)
            or witness["witness_utf8_byte_count"] < len(WITNESS_LOCATOR) + 32
            or witness["source_end_byte"] - witness["source_start_byte"]
            != witness["witness_utf8_byte_count"]
            or witness["projection_end_byte"] - witness["projection_start_byte"]
            != witness["witness_utf8_byte_count"]
            or not 0 <= witness["projection_start_byte"]
            < witness["projection_end_byte"] <= projection["utf8_byte_count"]
        ):
            raise CandidateV02Error("A2_POST_A1_GATE_NOT_PASS")
    except (KeyError, TypeError, ValueError, CandidateV02Error) as exc:
        if isinstance(exc, CandidateV02Error) and exc.code == "A2_POST_A1_GATE_NOT_PASS":
            raise
        raise CandidateV02Error("A2_POST_A1_GATE_NOT_PASS") from exc


def persist_post_a1_readback_v0_2(
    path: Path,
    readback: PostA1GateReadbackV02,
) -> str:
    require_post_a1_gate_for_a2(readback)
    raw = _canonical_bytes(readback.as_dict())
    target = Path(path)
    if (
        target.name != POST_A1_READBACK_FILENAME
        or not target.parent.is_dir()
        or target.parent.is_symlink()
        or target.is_symlink()
    ):
        raise CandidateV02Error("POST_A1_READBACK_PATH_INVALID")
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise CandidateV02Error("POST_A1_READBACK_ALREADY_EXISTS") from exc
    try:
        if os.write(descriptor, raw) != len(raw):
            raise CandidateV02Error("POST_A1_READBACK_WRITE_INCOMPLETE")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        parent_descriptor = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    except OSError as exc:
        raise CandidateV02Error("POST_A1_READBACK_DIRECTORY_SYNC_FAILED") from exc
    digest = _sha256(raw)
    read_post_a1_readback_v0_2(target, digest)
    return digest


def read_post_a1_readback_v0_2(
    path: Path,
    expected_sha256: str,
) -> PostA1GateReadbackV02:
    _require_sha256(expected_sha256, "POST_A1_EXPECTED_SHA_INVALID")
    target = Path(path)
    if target.name != POST_A1_READBACK_FILENAME or target.is_symlink():
        raise CandidateV02Error("POST_A1_READBACK_PATH_INVALID")
    try:
        raw = target.read_bytes()
    except OSError as exc:
        raise CandidateV02Error("POST_A1_READBACK_UNAVAILABLE") from exc
    if _sha256(raw) != expected_sha256:
        raise CandidateV02Error("POST_A1_READBACK_SHA_MISMATCH")
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateV02Error("POST_A1_READBACK_INVALID") from exc
    readback = PostA1GateReadbackV02.from_dict(value)
    if _canonical_bytes(readback.as_dict()) != raw:
        raise CandidateV02Error("POST_A1_READBACK_NONCANONICAL")
    return readback


@dataclass(frozen=True)
class A3WitnessVerificationV02:
    schema: str
    candidate_id: str
    result: str
    witness_sha256: str
    source_start_byte: int
    source_end_byte: int
    output_start_byte: int
    output_end_byte: int
    a3_audit_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def verify_a3_winner_witness_v0_2(
    audit: FieldNoteCreatorLiveA3CompilerAudit,
    binding: WitnessBindingV02,
    source_note_bytes: bytes,
    output_bytes: bytes,
) -> A3WitnessVerificationV02:
    if not isinstance(audit, FieldNoteCreatorLiveA3CompilerAudit):
        raise CandidateV02Error("A3_AUDIT_INVALID")
    if (
        not isinstance(binding, WitnessBindingV02)
        or binding.schema != WITNESS_SCHEMA
        or binding.candidate_id != CANDIDATE_ID
        or binding.policy_result != "PASS"
        or binding.source_occurrence_count != 1
        or binding.projection_occurrence_count != 1
        or audit.eligible_candidate_count != 1
        or audit.winning_candidate_count != 1
        or audit.terminal_a3_code is not None
    ):
        raise CandidateV02Error("A3_WINNER_COUNT_INVALID")
    source_range = (audit.selected_source_start_byte, audit.selected_source_end_byte)
    output_range = (audit.selected_output_start_byte, audit.selected_output_end_byte)
    if source_range != (binding.source_start_byte, binding.source_end_byte):
        raise CandidateV02Error("A3_SOURCE_OFFSETS_MISMATCH")
    if (
        audit.source_note_sha256 != binding.note_content_sha256
        or _sha256(source_note_bytes) != binding.note_content_sha256
        or audit.output_sha256 != _sha256(output_bytes)
    ):
        raise CandidateV02Error("A3_ARTIFACT_IDENTITY_MISMATCH")
    if any(type(value) is not int for value in (*source_range, *output_range)):
        raise CandidateV02Error("A3_OFFSETS_INVALID")
    ss, se = source_range
    os_, oe = output_range
    source_span = source_note_bytes[ss:se]
    output_span = output_bytes[os_:oe]
    if (
        source_span != output_span
        or _sha256(source_span) != binding.witness_sha256
        or output_bytes.count(source_span) != 1
    ):
        raise CandidateV02Error("A3_WITNESS_BYTES_MISMATCH")
    return A3WitnessVerificationV02(
        A3_WITNESS_SCHEMA,
        CANDIDATE_ID,
        "PASS",
        binding.witness_sha256,
        ss,
        se,
        os_,
        oe,
        audit.audit_sha256,
    )


COMMON_BEFORE_PUBLIC = {
    "logical_artifact": "AGENTS.md",
    **FIXED_SOURCE_IDENTITY.as_dict(),
}

PUBLIC_CLAIMS = (
    "Compression percentage requires exact artifact identities and the fixed byte-count algorithm.",
    "B01-B10 establishes specified textual and structural presence only.",
    "Behavior preservation requires separately authorized real 10/10 qualification.",
    "A3 establishes only exact reuse of the designated Witness bytes.",
    "Source isolation establishes supplied-input and capability isolation only.",
    "Loop-governance evidence does not establish output quality.",
    "Public usefulness requires separate user or human evidence.",
)

PUBLIC_NON_CLAIMS = (
    "Independence does not establish absence of latent model memory.",
    "Shorter does not mean better.",
    "A higher reduction rate does not establish a superior system across layers.",
    "Structural presence does not establish behavior preservation.",
    "A3 does not establish usefulness, safety, or generality.",
    "A common Before does not establish identical objectives across lanes.",
    "V13 is not only a compressor.",
    "Public usefulness and cross-tool superiority are not established.",
)

SOURCE_RECOVERY = (
    "Use a normal Forward revert, preserve Candidate v0.1, Cycle 005, and "
    "historical proof bytes, then rebuild, refix, and requalify."
)


def _common_before_comparison_template() -> dict[str, Any]:
    unknown = {"result": "NOT_ESTABLISHED", "value": None}
    lane_a = {
        "lane_id": "A_COMPACTOR",
        "tool_identity": dict(unknown),
        "version_identity": dict(unknown),
        "common_before_binding": dict(unknown),
        "after_identity": dict(unknown),
        "reduction": dict(unknown),
        "qualification": dict(unknown),
    }
    lane_b = {
        "lane_id": "B_HISTORICAL_HUMAN_AI_MANUAL",
        "common_before_binding": {
            "result": "PASS",
            "sha256": SOURCE_SHA256,
        },
        "after_identity": {
            "result": "PASS",
            "utf8_byte_count": MANUAL_AFTER_BYTE_COUNT,
            "line_count": MANUAL_AFTER_LINE_COUNT,
            "sha256": MANUAL_AFTER_SHA256,
        },
        "reduction": {
            "result": "PASS",
            "byte_count": 9_558,
            "fraction": "0.461628",
            "approximate_percentage": "46.16%",
            "line_count": 158,
        },
        "qualification": {
            "class": "CANONICAL_MANUAL_TEXTUAL_RESTRUCTURING_ONLY",
            "b01_b10_receipt": "NOT_ESTABLISHED",
            "behavior": "NOT_ESTABLISHED",
        },
    }
    default_lane_c = {
        "lane_id": "C_V13_CREATOR_LIVE",
        "common_before_binding": {
            "result": "PASS",
            "sha256": SOURCE_SHA256,
        },
        "after_identity": dict(unknown),
        "reduction": dict(unknown),
        "b01_b10": dict(unknown),
        "independence": dict(unknown),
        "public_safety": dict(unknown),
        "behavior": dict(unknown),
        "a1": dict(unknown),
        "a2": dict(unknown),
        "a3_exact_reuse": dict(unknown),
        "retry_replacement": "NOT_AUTHORIZED",
        "explicit_non_claims": list(PUBLIC_NON_CLAIMS),
    }
    manifest = {
        "schema": COMPARISON_SCHEMA,
        "comparison_result": "NOT_ESTABLISHED",
        "shared_before": copy.deepcopy(COMMON_BEFORE_PUBLIC),
        "lanes": [lane_a, lane_b, default_lane_c],
        "claim_boundary": {
            "common_source_is_not_common_objective": True,
            "higher_reduction_is_not_cross_layer_superiority": True,
            "structural_is_not_behavioral": True,
        },
        "cross_lane_isolation": {
            "run_1_input_lanes": ["SHARED_BEFORE_ONLY"],
            "run_2_input_lanes": ["C_EXACT_NOTE_AND_RECEIPTS_ONLY"],
            "assembled_after_lane_c_qualification": True,
            "public_content_free_receipts_only": True,
            "missing_values_explicit": "NOT_ESTABLISHED",
        },
    }
    return manifest


def build_common_before_comparison() -> dict[str, Any]:
    manifest = _common_before_comparison_template()
    validate_common_before_comparison(manifest)
    return manifest


def validate_common_before_comparison(value: Mapping[str, Any]) -> None:
    if list(value) != [
        "schema",
        "comparison_result",
        "shared_before",
        "lanes",
        "claim_boundary",
        "cross_lane_isolation",
    ]:
        raise CandidateV02Error("COMPARISON_ROOT_ORDER_INVALID")
    if dict(value) != _common_before_comparison_template():
        raise CandidateV02Error("COMPARISON_MANIFEST_INVALID")
    raw = canonical_json(value)
    if "11147" not in raw or MANUAL_AFTER_SHA256 not in raw:
        raise CandidateV02Error("COMPARISON_LANE_B_MISSING")
    if "NOT_ESTABLISHED" not in raw:
        raise CandidateV02Error("COMPARISON_UNKNOWN_ERASED")
    forbidden = ("before/AGENTS.md\n", "--- before/AGENTS.md", "+++ after/AGENTS.md")
    if any(item in raw for item in forbidden):
        raise CandidateV02Error("COMPARISON_RAW_LANE_OUTPUT_EXPOSED")


REDUCTION_CORE_STATEMENT = (
    "These systems are not competitors on one compression axis. They remove "
    "waste from different operational surfaces."
)
REDUCTION_RULES = (
    "Higher percentage does not imply cross-layer superiority.",
    "Combinations are allowed only when preserved boundaries remain compatible.",
    "No external performance number is included.",
    "Cross-layer ranking and superiority claims are prohibited.",
)


def _reduction_boundary_map_template() -> dict[str, Any]:
    entries = [
        {
            "system": "RTK",
            "surface": "tool-output surface",
            "proposed_removal_boundary": "unnecessary payload after tool execution",
            "preserved_boundary": "necessary tool result and evidence",
            "combination_position": "may precede output/handoff and V13 governance",
            "verification_status": "LATER_WEB_VERIFICATION_REQUIRED",
        },
        {
            "system": "Ponytail",
            "surface": "implementation surface",
            "proposed_removal_boundary": "unnecessary implementation bulk or repetition",
            "preserved_boundary": "specified contracts and behavior",
            "combination_position": "may coexist with instruction and output reduction",
            "verification_status": "LATER_WEB_VERIFICATION_REQUIRED",
        },
        {
            "system": "Compactor",
            "surface": "persistent-instruction surface",
            "proposed_removal_boundary": "always-loaded instruction burden or duplication",
            "preserved_boundary": "mandatory instructions and recallability",
            "combination_position": "may feed output/handoff and V13 governance",
            "verification_status": "LATER_WEB_VERIFICATION_REQUIRED",
        },
        {
            "system": "OSI",
            "surface": "output / handoff surface",
            "proposed_removal_boundary": "repetitive or non-actionable output and handoff material",
            "preserved_boundary": "restart state and actionable evidence",
            "combination_position": "may sit downstream of other reductions",
            "verification_status": "LATER_WEB_VERIFICATION_REQUIRED",
        },
        {
            "system": "V13",
            "surface": "iteration / authority surface",
            "proposed_removal_boundary": "unnecessary or unauthorized repeated loops and ambiguous authority transitions",
            "preserved_boundary": "human Seat, evidence, rollback, and re-entry capacity",
            "combination_position": "may govern compatible combinations across surfaces",
            "verification_status": "INTERNAL_POSITIONING_STATEMENT",
        },
    ]
    return {
        "schema": REDUCTION_MAP_SCHEMA,
        "core_statement": REDUCTION_CORE_STATEMENT,
        "entries": entries,
        "rules": list(REDUCTION_RULES),
    }


def build_reduction_boundary_map() -> dict[str, Any]:
    result = _reduction_boundary_map_template()
    validate_reduction_boundary_map(result)
    return result


def validate_reduction_boundary_map(value: Mapping[str, Any]) -> None:
    if set(value) != {"schema", "core_statement", "entries", "rules"}:
        raise CandidateV02Error("REDUCTION_MAP_SHAPE_INVALID")
    entries = value.get("entries")
    entry_fields = {
        "system", "surface", "proposed_removal_boundary", "preserved_boundary",
        "combination_position", "verification_status",
    }
    if (
        dict(value) != _reduction_boundary_map_template()
        or
        value.get("schema") != REDUCTION_MAP_SCHEMA
        or value.get("core_statement") != REDUCTION_CORE_STATEMENT
        or not isinstance(entries, list)
        or len(entries) != 5
        or any(not isinstance(entry, Mapping) or set(entry) != entry_fields for entry in entries)
        or [entry.get("system") for entry in entries]
        != ["RTK", "Ponytail", "Compactor", "OSI", "V13"]
        or [entry.get("surface") for entry in entries]
        != [
            "tool-output surface",
            "implementation surface",
            "persistent-instruction surface",
            "output / handoff surface",
            "iteration / authority surface",
        ]
        or any(
            entry.get("verification_status") != "LATER_WEB_VERIFICATION_REQUIRED"
            for entry in entries[:4]
        )
        or entries[4].get("verification_status") != "INTERNAL_POSITIONING_STATEMENT"
        or any(
            not isinstance(entry.get(field), str) or not entry[field].strip()
            for entry in entries
            for field in (
                "proposed_removal_boundary", "preserved_boundary", "combination_position"
            )
        )
        or value.get("rules") != list(REDUCTION_RULES)
    ):
        raise CandidateV02Error("REDUCTION_MAP_INVALID")
    entry_text = canonical_json({"entries": entries}).casefold()
    if re.search(
        r"\b(?:outperform(?:s|ed|ing)?|best|better\s+than|superior(?:\s+to)?|"
        r"beats?|leading|more\s+effective|less\s+effective|rank(?:s|ed|ing)?)\b",
        entry_text,
    ):
        raise CandidateV02Error("REDUCTION_MAP_SUPERIORITY_CLAIM")
    if re.search(
        r"\b\d+(?:\.\d+)?\s*(?:%|percent\b|x\b|times\b|ms\b|seconds?\b)",
        entry_text,
    ):
        raise CandidateV02Error("REDUCTION_MAP_EXTERNAL_PERFORMANCE_CLAIM")


PUBLIC_BUNDLE_PATHS = (
    "before/AGENTS.md",
    "after/AGENTS.md",
    "manifest.json",
    "diff.patch",
    "boundary-checklist.json",
    "source-isolation.json",
    "independence-qualification.json",
    "behavior-qualification.json",
    "comparison-manifest.json",
    "reduction-boundary-map.json",
    "proof-summary.json",
    "README.md",
)

_PUBLIC_PRIVATE_KEYS = frozenset(
    {
        "proof_attempt_id",
        "run_id",
        "source_run_id",
        "field_note_id",
        "note_path",
        "created_at",
        "approval_id",
        "provider_config",
        "journal_sha256",
        "anchor_sha256",
        "readback_sha256",
        "typed_readback",
        "raw_journal",
        "raw_anchor",
        "raw_readback",
        "witness_text",
        "task_body",
        "raw_output",
    }
)


def _reject_private_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        if _PUBLIC_PRIVATE_KEYS.intersection(
            key.casefold() for key in value if isinstance(key, str)
        ):
            raise CandidateV02Error("PUBLIC_BUNDLE_PRIVATE_KEY")
        for item in value.values():
            _reject_private_keys(item)
    elif isinstance(value, list):
        for item in value:
            _reject_private_keys(item)


def _public_source_isolation_projection(
    receipt: SourceIsolationReceipt,
) -> dict[str, Any]:
    return {
        "schema": SOURCE_ISOLATION_PUBLIC_PROJECTION_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "result": receipt.result,
        "source_identity": FIXED_SOURCE_IDENTITY.as_dict(),
        "receipt_sha256": receipt.receipt_sha256,
    }


def _public_independence_projection(
    receipt: IndependenceReceipt,
) -> dict[str, Any]:
    return {
        "schema": INDEPENDENCE_PUBLIC_PROJECTION_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "result": receipt.result,
        "source_isolation_receipt_sha256": receipt.source_isolation_receipt_sha256,
        "latent_model_memory_excluded": False,
        "receipt_sha256": receipt.receipt_sha256,
    }


def build_public_manifest_v0_2(
    *,
    projection: PublicAfterProjection,
    compression: CompressionReceipt,
    safety: SafetyReceipt,
    boundaries: Sequence[BoundaryResult],
    source_isolation: SourceIsolationReceipt,
    independence: IndependenceReceipt,
    harness_behavior: BehaviorResult,
    artifact_behavior: BehaviorResult,
    comparison: Mapping[str, Any],
    reduction_map: Mapping[str, Any],
    receipt_hashes: Mapping[str, str],
    output_artifact: Mapping[str, Any],
    a3: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": PUBLIC_BUNDLE_SCHEMA,
        "assembler": PUBLIC_BUNDLE_ASSEMBLER,
        "candidate_id": CANDIDATE_ID,
        "before": copy.deepcopy(COMMON_BEFORE_PUBLIC),
        "after": projection.identity_dict(),
        "compression": compression.as_dict(),
        "safety": safety.as_dict(),
        "source_isolation": {
            "result": source_isolation.result,
            "receipt_sha256": source_isolation.receipt_sha256,
        },
        "independence": {
            "result": independence.result,
            "receipt_sha256": independence.receipt_sha256,
            "latent_model_memory_excluded": False,
        },
        "behavior": {
            "suite_schema": BEHAVIOR_SUITE_SCHEMA,
            "suite_sha256": artifact_behavior.suite_sha256,
            "harness_qualification": harness_behavior.result,
            "artifact_behavior_qualification": artifact_behavior.result,
        },
        "boundary_ids": [value.boundary_id for value in boundaries],
        "receipt_hashes": dict(receipt_hashes),
        "output_artifact": dict(output_artifact),
        "a3": dict(a3),
        "comparison_schema": comparison.get("schema"),
        "reduction_map_schema": reduction_map.get("schema"),
        "claims": list(PUBLIC_CLAIMS),
        "non_claims": list(PUBLIC_NON_CLAIMS),
        "source_recovery": SOURCE_RECOVERY,
        "files": list(PUBLIC_BUNDLE_PATHS),
    }


def assemble_public_bundle_v0_2(
    *,
    before: bytes,
    projection: PublicAfterProjection,
    compression: CompressionReceipt,
    safety: SafetyReceipt,
    boundaries: Sequence[BoundaryResult],
    source_isolation: SourceIsolationReceipt,
    independence: IndependenceReceipt,
    harness_behavior: BehaviorResult,
    artifact_behavior: BehaviorResult,
    comparison: Mapping[str, Any],
    reduction_map: Mapping[str, Any],
    public_manifest: Mapping[str, Any],
    witness: bytes | None,
    fixture_witness_publication_approved: bool,
) -> dict[str, bytes]:
    _fixed_bytes(before)
    require_independence_pass(independence, source_isolation)
    expected_projection = PublicAfterProjection(
        projection.schema,
        len(projection.body),
        _line_count(projection.body),
        _sha256(projection.body),
        projection.body,
    )
    if projection != expected_projection or projection.schema != PROJECTION_SCHEMA:
        raise CandidateV02Error("PUBLIC_BUNDLE_AFTER_IDENTITY_INVALID")
    expected_compression = compression_receipt(before, projection.body)
    expected_safety = public_safety(projection.body)
    expected_boundaries = check_boundaries_v0_2(projection.body, expected_safety)
    witness_lines = tuple(
        line for line in projection.body.split(b"\n") if line.startswith(WITNESS_LOCATOR)
    )
    if (
        len(witness_lines) != 1
        or witness != witness_lines[0]
        or not fixture_witness_publication_approved
    ):
        raise CandidateV02Error("PUBLIC_BUNDLE_WITNESS_NOT_APPROVED")
    if (
        compression != expected_compression
        or compression.result != "PASS"
        or safety != expected_safety
        or safety.result != "PASS"
        or tuple(boundaries) != expected_boundaries
        or any(value.status != "PRESENT" for value in boundaries)
        or harness_behavior.result != "PASS"
        or harness_behavior.passed != 10
        or artifact_behavior.result != "NOT_RUN"
        or artifact_behavior.passed != 0
        or harness_behavior.suite_sha256 != artifact_behavior.suite_sha256
    ):
        raise CandidateV02Error("PUBLIC_BUNDLE_CANDIDATE_NOT_PASS")
    validate_common_before_comparison(comparison)
    validate_reduction_boundary_map(reduction_map)
    _reject_private_keys(public_manifest)
    _reject_private_keys(comparison)
    _reject_private_keys(reduction_map)
    expected_manifest = build_public_manifest_v0_2(
        projection=projection,
        compression=compression,
        safety=safety,
        boundaries=boundaries,
        source_isolation=source_isolation,
        independence=independence,
        harness_behavior=harness_behavior,
        artifact_behavior=artifact_behavior,
        comparison=comparison,
        reduction_map=reduction_map,
        receipt_hashes=public_manifest.get("receipt_hashes", {}),
        output_artifact=public_manifest.get("output_artifact", {}),
        a3=public_manifest.get("a3", {}),
    )
    if dict(public_manifest) != expected_manifest:
        raise CandidateV02Error("PUBLIC_BUNDLE_MANIFEST_BINDING_INVALID")
    receipt_hashes = public_manifest["receipt_hashes"]
    if (
        not isinstance(receipt_hashes, Mapping)
        or set(receipt_hashes) != {"a1_capture_sha256", "a2_reconnect_sha256"}
        or any(_HEX64.fullmatch(value) is None for value in receipt_hashes.values())
    ):
        raise CandidateV02Error("PUBLIC_BUNDLE_RECEIPT_HASH_INVALID")
    output = public_manifest["output_artifact"]
    if (
        not isinstance(output, Mapping)
        or set(output) != {"artifact_id", "media_type", "byte_count", "sha256"}
        or _HEX64.fullmatch(output.get("artifact_id", "")) is None
        or output.get("media_type") != "text/plain; charset=utf-8"
        or type(output.get("byte_count")) is not int
        or output["byte_count"] <= 0
        or _HEX64.fullmatch(output.get("sha256", "")) is None
    ):
        raise CandidateV02Error("PUBLIC_BUNDLE_OUTPUT_IDENTITY_INVALID")
    a3 = public_manifest["a3"]
    if (
        not isinstance(a3, Mapping)
        or set(a3) != {"compiler_version", "compiler_branch", "audit_sha256", "exact_reuse"}
        or a3.get("compiler_version") != A3_COMPILER_VERSION
        or a3.get("compiler_branch") != A3_COMPILER_BRANCH
        or _HEX64.fullmatch(a3.get("audit_sha256", "")) is None
        or a3.get("exact_reuse") != "PASS"
    ):
        raise CandidateV02Error("PUBLIC_BUNDLE_A3_INVALID")

    checklist = {
        "schema": BOUNDARY_SCHEMA,
        "results": [value.as_dict() for value in boundaries],
    }
    behavior = {
        "schema": BEHAVIOR_RESULT_SCHEMA,
        "suite_sha256": artifact_behavior.suite_sha256,
        "harness": harness_behavior.as_dict(),
        "artifact": artifact_behavior.as_dict(),
    }
    summary = {
        "schema": PUBLIC_BUNDLE_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "before": public_manifest["before"],
        "after": public_manifest["after"],
        "compression": public_manifest["compression"],
        "source_isolation": public_manifest["source_isolation"],
        "independence": public_manifest["independence"],
        "behavior": public_manifest["behavior"],
        "a3": public_manifest["a3"],
        "claims": list(PUBLIC_CLAIMS),
        "non_claims": list(PUBLIC_NON_CLAIMS),
    }
    readme = (
        "# Candidate v0.2 fixture-only bundle\n\n"
        + "\n".join(PUBLIC_CLAIMS)
        + "\n\n"
        + "\n".join(PUBLIC_NON_CLAIMS)
        + "\n"
    ).encode("utf-8")
    bundle = {
        "before/AGENTS.md": before,
        "after/AGENTS.md": projection.body,
        "manifest.json": _canonical_bytes(public_manifest),
        "diff.patch": compression.diff_bytes,
        "boundary-checklist.json": _canonical_bytes(checklist),
        "source-isolation.json": _canonical_bytes(
            _public_source_isolation_projection(source_isolation)
        ),
        "independence-qualification.json": _canonical_bytes(
            _public_independence_projection(independence)
        ),
        "behavior-qualification.json": _canonical_bytes(behavior),
        "comparison-manifest.json": _canonical_bytes(comparison),
        "reduction-boundary-map.json": _canonical_bytes(reduction_map),
        "proof-summary.json": _canonical_bytes(summary),
        "README.md": readme,
    }
    if tuple(bundle) != PUBLIC_BUNDLE_PATHS:
        raise CandidateV02Error("PUBLIC_BUNDLE_PATH_SET_INVALID")
    for path in (
        "after/AGENTS.md", "manifest.json", "boundary-checklist.json",
        "source-isolation.json", "independence-qualification.json",
        "behavior-qualification.json", "comparison-manifest.json",
        "reduction-boundary-map.json", "proof-summary.json", "README.md",
    ):
        lowered = bundle[path].lower()
        if (
            any(marker in lowered for marker in _PRIVATE_PROJECTION_FIELD_MARKERS)
            or any(
                pattern.search(bundle[path])
                for pattern in _PRIVATE_PROJECTION_LABEL_PATTERNS
            )
            or public_safety(bundle[path]).result != "PASS"
        ):
            raise CandidateV02Error("PUBLIC_BUNDLE_PRIVATE_CONTENT")
    return bundle


def behavior_suite_directory(repository: Path) -> Path:
    return (
        Path(repository)
        / "validation/fixtures/creator_live_agents_before_after_v0_1/behavior"
    )


def qualify_behavior_harness(
    repository: Path,
) -> tuple[BehaviorResult, BehaviorResult]:
    suite = behavior_suite_directory(repository)
    _, scenarios, suite_sha = load_behavior_suite(suite)
    if suite_sha != BEHAVIOR_SUITE_SHA256:
        raise CandidateV02Error("BEHAVIOR_SUITE_IDENTITY_DRIFT")
    observations = {
        scenario["scenario_id"]: scenario["required_tags"] for scenario in scenarios
    }
    harness = evaluate_behavior_fakes(suite, observations)
    artifact = artifact_behavior_not_run(suite)
    if harness.result != "PASS" or artifact.result != "NOT_RUN":
        raise CandidateV02Error("BEHAVIOR_QUALIFICATION_BOUNDARY_INVALID")
    return harness, artifact
