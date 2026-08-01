"""Bounded three-action Contract fixation for ordinary Companion users."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import threading
import time
from typing import Any
import uuid

from .guided_intake import (
    DRAFT_SCHEMA,
    MAX_ORIGINAL_REQUEST_BYTES,
    GuidedIntakeBusyError,
    GuidedIntakeConflictError,
    GuidedIntakeController,
    GuidedIntakeError,
    GuidedIntakeIntegrityError,
    GuidedIntakeValidationError,
    _git_common_directory,
    _quoted_payload_boundary,
    _repository_head,
    canonical_json,
    sha256_bytes,
    structured_sha256,
)


COMPILER_VERSION = "decision-os-contract-fixation-compiler-v0.1"
PRODUCER_IDENTITY = "DECISION_OS_CONTRACT_FIXATION_COMPILER_V0_1"
VIEW_SCHEMA = "decision-os-ordinary-user-path-view-v0.1"
STORE_SCHEMA = "decision-os-ordinary-user-path-store-v0.1"
STATE_SCHEMA = "decision-os-ordinary-user-path-state-v0.1"
ERROR_SCHEMA = "decision-os-ordinary-action-error-v0.1"
PREPARATION_RECEIPT_SCHEMA = "decision-os-contract-preparation-receipt-v0.1"
FRICTION_SCHEMA = "decision-os-ordinary-path-friction-v0.1"
MAX_SOURCE_BYTES = 61_440

PRODUCT_PROFILE = "PRODUCT_CONTRACT_APPROVED_CANDIDATE_V0_1"
ORDINARY_PROFILE = "ORDINARY_USER_PATH_CONTRACT_APPROVED_CANDIDATE_V0_1"
PRODUCT_TITLE = "Initial Product Contract v0.1 — APPROVED CANDIDATE"
ORDINARY_TITLE = "Ordinary User Path Contract v0.1 — APPROVED CANDIDATE"
_DOES_NOT_AUTHORIZE = (
    "This operation does not implement, run, transfer, merge, release, "
    "publish, or send this Contract anywhere."
)
_FIXED_MESSAGE = (
    "Contract fixed. This Contract can now be used to resume the same "
    "decision in this repository without reconstructing its meaning from "
    "scratch."
)
_PRODUCT_REVIEW_COMPLETION = (
    "Complete when one current interpretation preserves the exact embedded "
    "Contract, records its V9/V13 role and authority boundary, records its "
    "evidence boundary, and keeps all downstream execution blocked."
)
_ORDINARY_REVIEW_COMPLETION = (
    "Complete when one current interpretation preserves the exact embedded "
    "Contract, records V9 as primary and V13 as supporting, records that this "
    "operation grants no implementation authority, and keeps implementation "
    "blocked."
)
_ORDINARY_VISIBLE_DENYLIST = (
    "PRESERVED",
    "TESTABLE",
    "authority_claim",
    "schema_version",
    "Request ID",
    "Draft ID",
    "Freeze ID",
    "SHA-256",
    "CLEAR ENOUGH TO FREEZE",
    "NEEDS USER CONFIRMATION",
    "HOLD —",
    "UNKNOWN_",
    "MODEL_DETECTED_MISSING_FACT",
    "Producer label",
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,200}$")


class OrdinaryUserPathError(RuntimeError):
    """Structured ordinary-path failure suitable for the local API."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        http_status: int = 400,
        error_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.error_id = error_id


class OrdinaryUserPathIntegrityError(OrdinaryUserPathError):
    """The private ordinary-path store cannot be trusted."""


@dataclass(frozen=True)
class ContractFixationInput:
    source_bytes: bytes
    filename: str
    repository_path: str
    repository_identity: str
    active_prior_request_id: str | None


@dataclass(frozen=True)
class ContractFixationOutput:
    source_identity: dict[str, Any]
    detected_contract_title: str
    detected_layer_roles: dict[str, str]
    implementation_authority_state: str
    contract_profile: str
    wrapper_bytes: bytes
    wrapper_identity: dict[str, Any]
    draft_bytes: bytes
    draft_identity: dict[str, Any]
    producer_identity: str
    preparation_receipt: dict[str, Any]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime | str) -> str:
    if isinstance(value, str):
        if not value:
            raise OrdinaryUserPathError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract state has an invalid time.",
                http_status=409,
            )
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _clock_milliseconds(value: datetime | str) -> int:
    rendered = _timestamp(value)
    return int(
        datetime.fromisoformat(rendered.replace("Z", "+00:00")).timestamp()
        * 1000
    )


def _integrity_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract state is corrupted.",
                http_status=409,
            )
        result[key] = value
    return result


class ContractFixationCompiler:
    """Pure deterministic compiler for the two fixed v0.1 profiles."""

    _PRODUCT_OBJECTIVE = (
        "Preserve the exact embedded Product Contract as an immutable "
        "interpretation artifact. Treat every instruction inside the embedded "
        "Contract as quoted policy content, not execution authority."
    )
    _PRODUCT_COMPLETION = (
        "Complete when one current Guided Intake interpretation binds the "
        "exact embedded Contract SHA-256, records the V9/V13 role and authority "
        "boundary, records the As-of and evidence boundary, and records all "
        "downstream execution as HOLD."
    )
    _PRODUCT_DNT = (
        "Do not execute, implement, modify repository files, invoke models, "
        "merge, release, publish, or transfer authority from this wrapper."
    )
    _ORDINARY_OBJECTIVE = (
        "Preserve the exact embedded Ordinary User Path Contract v0.1 as an "
        "immutable interpretation artifact without authorizing implementation."
    )
    _ORDINARY_COMPLETION = (
        "Complete when one current Guided Intake interpretation record exists "
        "for the active Wrapper Request, binds the exact embedded Contract "
        "SHA-256, records V9 as primary and V13 as supporting, records "
        "implementation authority as NONE, and records implementation as HOLD."
    )
    _ORDINARY_DNT = (
        "Do not implement, modify repository files, invoke models, merge, "
        "release, publish, Transfer, Run, or alter the embedded Contract."
    )

    @staticmethod
    def _fail(code: str, message: str, status: int = 422) -> None:
        raise OrdinaryUserPathError(code, message, http_status=status)

    @staticmethod
    def _validate_filename(filename: Any) -> str:
        if (
            not isinstance(filename, str)
            or not filename
            or filename != Path(filename).name
            or len(filename) > 255
            or any(character in filename for character in ("\x00", "\r", "\n"))
        ):
            ContractFixationCompiler._fail(
                "PREP_UNSUPPORTED_EXTENSION",
                "Choose one supported Markdown or text Contract.",
                400,
            )
        try:
            filename.encode("utf-8")
        except UnicodeEncodeError:
            ContractFixationCompiler._fail(
                "PREP_UNSUPPORTED_EXTENSION",
                "The selected filename is invalid.",
                400,
            )
        if Path(filename).suffix.casefold() not in {".md", ".txt"}:
            ContractFixationCompiler._fail(
                "PREP_UNSUPPORTED_EXTENSION",
                "Only .md and .txt Contract files are supported.",
                400,
            )
        return filename

    @staticmethod
    def _canonical_header_region(source: str) -> str:
        """Return only structural, unquoted evidence from the fixed header."""

        visible: list[str] = []
        fence: tuple[str, int] | None = None
        for raw_line in source.splitlines(keepends=True):
            line = raw_line.rstrip("\r\n")
            placeholder = "\n" if raw_line.endswith(("\r", "\n")) else ""
            content = line.lstrip(" ")
            indent = len(line) - len(content)
            fence_match = (
                re.match(r"(`{3,}|~{3,})(.*)$", content)
                if indent <= 3
                else None
            )
            if fence is not None:
                if fence_match is not None:
                    marker = fence_match.group(1)
                    remainder = fence_match.group(2)
                    if (
                        marker[0] == fence[0]
                        and len(marker) >= fence[1]
                        and not remainder.strip()
                    ):
                        fence = None
                visible.append(placeholder)
                continue
            if fence_match is not None:
                marker = fence_match.group(1)
                fence = (marker[0], len(marker))
                visible.append(placeholder)
                continue
            if re.match(r"^ {0,3}>", line) or line.startswith(("    ", "\t")):
                visible.append(placeholder)
                continue
            if re.match(
                r"^ {0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$",
                line,
            ):
                break
            section = re.match(r"^ {0,3}(#{2,6})[ \t]+(.+?)\s*$", line)
            if section is not None and (
                len(section.group(1)) != 2
                or section.group(2).strip().casefold() != "status"
            ):
                break
            visible.append(raw_line)
        return "".join(visible)

    @staticmethod
    def _profile(header: str) -> tuple[str, str]:
        supported = {
            PRODUCT_TITLE: (PRODUCT_PROFILE, PRODUCT_TITLE),
            ORDINARY_TITLE: (ORDINARY_PROFILE, ORDINARY_TITLE),
        }
        lines = header.splitlines()
        contract_headings: list[str] = []
        for index, line in enumerate(lines):
            atx = re.match(r"^ {0,3}#(?!#)[ \t]+(.+?)[ \t]*$", line)
            if atx is not None:
                title = re.sub(r"[ \t]+#+[ \t]*$", "", atx.group(1)).strip()
            elif (
                line.strip()
                and index + 1 < len(lines)
                and re.match(r"^ {0,3}=+[ \t]*$", lines[index + 1])
            ):
                title = line.strip()
            else:
                continue
            if re.search(r"\bContract\b", title, re.IGNORECASE):
                contract_headings.append(title)
        if not contract_headings:
            ContractFixationCompiler._fail(
                "PREP_TITLE_INVALID",
                "A supported Contract title could not be identified.",
            )
        first = contract_headings[0]
        if first not in supported:
            ContractFixationCompiler._fail(
                "PREP_UNSUPPORTED_CONTRACT_ROLE",
                "This Contract family is not supported.",
            )
        if len(contract_headings) != 1:
            ContractFixationCompiler._fail(
                "PREP_TITLE_INVALID",
                "The Contract title is ambiguous.",
            )
        return supported[first]

    @staticmethod
    def _validate_metadata(source: str, profile: str) -> None:
        if profile == PRODUCT_PROFILE:
            required = (
                r"(?m)^\*\*Primary Layer:\*\* V9\b.*$",
                r"(?m)^\*\*Supporting Layer:\*\* V13\b.*$",
                r"(?m)^- Repository implementation: \*\*HOLD\*\*$",
            )
            authorization_pattern = re.escape(
                "It does not authorize implementation, repository modification, "
                "release, or publication."
            )
        else:
            required = (
                r"(?m)^Primary Layer:\r?\nV9\b.*$",
                r"(?m)^Supporting Layer:\r?\nV13\b.*$",
                r"(?m)^Implementation Authority:\r?\nNONE\r?$",
            )
            authorization_pattern = (
                r"This Contract does not authorize repository changes, "
                r"implementation, merge,\r?\nrelease, publication, model "
                r"invocation, or rollout\."
            )
        if any(len(re.findall(pattern, source)) != 1 for pattern in required):
            ContractFixationCompiler._fail(
                "PREP_METADATA_MALFORMED",
                "The Contract's fixed layer or authority metadata is malformed.",
            )
        label_counts = {
            "primary": len(re.findall(r"(?mi)^\*\*Primary Layer:\*\*|^Primary Layer:\r?$", source)),
            "supporting": len(re.findall(r"(?mi)^\*\*Supporting Layer:\*\*|^Supporting Layer:\r?$", source)),
        }
        if (
            any(count != 1 for count in label_counts.values())
            or re.search(authorization_pattern, source) is None
        ):
            ContractFixationCompiler._fail(
                "PREP_METADATA_MALFORMED",
                "The Contract's fixed layer or authority metadata is malformed.",
            )

    @classmethod
    def _template(cls, profile: str) -> dict[str, str]:
        if profile == PRODUCT_PROFILE:
            return {
                "wrapper_title": "Product Contract Fixation Wrapper v0.1",
                "objective": cls._PRODUCT_OBJECTIVE,
                "completion": cls._PRODUCT_COMPLETION,
                "dnt": cls._PRODUCT_DNT,
                "observable": (
                    "One current Guided Intake interpretation record for the "
                    "active wrapper request contains the exact embedded Contract "
                    "SHA-256, the V9/V13 role and authority boundary, the As-of "
                    "and evidence boundary, and downstream execution state."
                ),
                "pass_condition": (
                    "The interpretation record exists; every named field is "
                    "present and non-empty; the embedded Contract SHA-256 equals "
                    "the verified source SHA-256; downstream execution state "
                    "equals HOLD."
                ),
                "evidence": (
                    "Active Original Request identity, current Guided Intake "
                    "interpretation record, and current Guided Intake state."
                ),
            }
        return {
            "wrapper_title": "Ordinary User Path Contract Fixation Wrapper v0.1",
            "objective": cls._ORDINARY_OBJECTIVE,
            "completion": cls._ORDINARY_COMPLETION,
            "dnt": cls._ORDINARY_DNT,
            "observable": (
                "One current Guided Intake interpretation record for the active "
                "Wrapper Request contains the embedded Contract SHA-256, layer "
                "roles, implementation authority, and implementation Gate."
            ),
            "pass_condition": (
                "The interpretation record exists; the embedded Contract SHA-256 "
                "equals the verified source SHA-256; V9 is recorded as primary; "
                "V13 is recorded as supporting; implementation authority equals "
                "NONE; implementation state equals HOLD."
            ),
            "evidence": (
                "Active Original Request identity, current Guided Intake "
                "interpretation record, current Guided Intake state, and native "
                "Freeze receipt."
            ),
        }

    @staticmethod
    def _draft_failure_code(message: str) -> str:
        normalized = message.upper()
        if "AUTHORITY INFLATION" in normalized:
            return "PREP_AUTHORITY_INFLATION"
        if "QUOTED PAYLOAD" in normalized or "PROVENANCE" in normalized:
            return "PREP_PROVENANCE_OVERLAP"
        if "OBJECTIVE" in normalized and (
            "FIDELITY" in normalized or "UNKNOWN" in normalized
        ):
            return "PREP_OBJECTIVE_FIDELITY_FAILED"
        if "COMPLETION" in normalized:
            return "PREP_COMPLETION_UNTESTABLE"
        if "MATERIAL UNKNOWN" in normalized:
            return "PREP_MATERIAL_UNKNOWN"
        if "DO NOT TOUCH" in normalized:
            return "PREP_DNT_CONFLICT"
        return "PREP_DRAFT_SCHEMA_INVALID"

    @staticmethod
    def _gate_failure_code(gate: Any) -> str:
        normalized = str(gate).upper()
        if "AUTHORITY INFLATION" in normalized:
            return "PREP_AUTHORITY_INFLATION"
        if "OBJECTIVE" in normalized:
            return "PREP_OBJECTIVE_FIDELITY_FAILED"
        if "COMPLETION" in normalized:
            return "PREP_COMPLETION_UNTESTABLE"
        if "DO NOT TOUCH" in normalized:
            return "PREP_DNT_CONFLICT"
        if "UNKNOWN" in normalized or "CONFIRMATION" in normalized:
            return "PREP_MATERIAL_UNKNOWN"
        return "PREP_DRAFT_SCHEMA_INVALID"

    def compile(self, value: ContractFixationInput) -> ContractFixationOutput:
        if not isinstance(value, ContractFixationInput):
            self._fail(
                "PREP_DRAFT_SCHEMA_INVALID",
                "The Contract compiler input is invalid.",
            )
        filename = self._validate_filename(value.filename)
        source_bytes = value.source_bytes
        if not isinstance(source_bytes, bytes):
            self._fail(
                "PREP_INVALID_UTF8",
                "The Contract is not valid UTF-8.",
                400,
            )
        if len(source_bytes) > MAX_SOURCE_BYTES:
            self._fail(
                "PREP_SOURCE_TOO_LARGE",
                "The Contract is too large for this bounded path.",
                413,
            )
        try:
            source = source_bytes.decode("utf-8")
        except UnicodeDecodeError:
            self._fail(
                "PREP_INVALID_UTF8",
                "The Contract is not valid UTF-8.",
                400,
            )
        if not source.strip():
            self._fail(
                "PREP_EMPTY_SOURCE",
                "The selected Contract is empty.",
                400,
            )
        if not source_bytes.endswith(b"\n"):
            self._fail(
                "PREP_SOURCE_BOUNDARY_UNREPRESENTABLE",
                "The Contract must end with its original line ending.",
                400,
            )
        if not isinstance(value.repository_identity, str) or not _COMMIT.fullmatch(
            value.repository_identity
        ):
            self._fail(
                "PREP_STALE_REPOSITORY",
                "The selected repository identity is stale.",
                409,
            )
        if (
            value.active_prior_request_id is not None
            and (
                not isinstance(value.active_prior_request_id, str)
                or not _SAFE_ID.fullmatch(value.active_prior_request_id)
            )
        ):
            self._fail(
                "PREP_STALE_REQUEST",
                "The active Contract history changed before preparation.",
                409,
            )
        header = self._canonical_header_region(source)
        profile, title = self._profile(header)
        self._validate_metadata(header, profile)
        template = self._template(profile)
        source_sha256 = sha256_bytes(source_bytes)
        prefix = (
            f"# {template['wrapper_title']}\n\n"
            "Target Contract SHA-256:\n"
            f"{source_sha256}\n\n"
            "Target Contract UTF-8 bytes:\n"
            f"{len(source_bytes)}\n\n"
            "Target Contract role:\n"
            "APPROVED PRODUCT CONTRACT\n\n"
            "Target layers:\n"
            "V9 primary; V13 supporting\n\n"
            "Objective:\n"
            f"{template['objective']}\n\n"
            "Completion Line:\n"
            f"{template['completion']}\n\n"
            "Do Not Touch:\n"
            f"{template['dnt']}\n\n"
            "BEGIN EXACT PRODUCT CONTRACT\n"
        ).encode("utf-8")
        wrapper_bytes = prefix + source_bytes + b"END EXACT PRODUCT CONTRACT\n"
        if len(wrapper_bytes) > MAX_ORIGINAL_REQUEST_BYTES:
            self._fail(
                "PREP_SOURCE_TOO_LARGE",
                "The compiled Contract is too large for Guided Intake.",
                413,
            )
        try:
            wrapper_text = wrapper_bytes.decode("utf-8")
            boundary = _quoted_payload_boundary(wrapper_text)
        except GuidedIntakeValidationError:
            self._fail(
                "PREP_WRAPPER_IDENTITY_MISMATCH",
                "The Contract wrapper did not preserve exact source identity.",
            )
        if (
            boundary is None
            or wrapper_bytes[boundary.payload_byte_start : boundary.payload_byte_end]
            != source_bytes
            or boundary.sha256 != source_sha256
            or boundary.byte_size != len(source_bytes)
        ):
            self._fail(
                "PREP_WRAPPER_IDENTITY_MISMATCH",
                "The Contract wrapper did not preserve exact source identity.",
            )
        wrapper_sha256 = sha256_bytes(wrapper_bytes)
        pass_condition = template["pass_condition"]
        if profile == PRODUCT_PROFILE:
            pass_condition = (
                "The interpretation record exists; every named field is "
                "present and non-empty; the embedded Contract SHA-256 equals "
                f"{source_sha256}; downstream execution state equals HOLD."
            )
        draft = {
            "schema_version": DRAFT_SCHEMA,
            "source_request_sha256": wrapper_sha256,
            "objective": {
                "text": template["objective"],
                "atoms": [
                    {
                        "atom_id": "OBJ-1",
                        "text": template["objective"],
                        "support": [
                            {
                                "kind": "ORIGINAL_REQUEST_QUOTE",
                                "quote": template["objective"],
                                "occurrence": 1,
                            }
                        ],
                    }
                ],
            },
            "completion_line": {
                "text": template["completion"],
                "testability_status": "TESTABLE",
                "checks": [
                    {
                        "observable": template["observable"],
                        "pass_condition": pass_condition,
                        "evidence_source": template["evidence"],
                    }
                ],
            },
            "do_not_touch": [
                {
                    "item_id": "DNT-1",
                    "text": template["dnt"],
                    "basis_kind": "USER_EXPLICIT",
                    "support": {
                        "kind": "ORIGINAL_REQUEST_QUOTE",
                        "quote": template["dnt"],
                        "occurrence": 1,
                    },
                }
            ],
            "unknown": [],
            "authority_claim": "NONE",
            "clarification_candidate": None,
        }
        draft_bytes = canonical_json(draft)
        try:
            interpretation, question = GuidedIntakeController._validate_draft(
                draft,
                original=wrapper_text,
                request_sha256=wrapper_sha256,
                confirmations=[],
            )
        except GuidedIntakeValidationError as exc:
            self._fail(
                self._draft_failure_code(str(exc)),
                "The deterministic interpretation failed strict validation.",
            )
        gate = interpretation.get("gate")
        if gate != "CLEAR ENOUGH TO FREEZE" or question is not None:
            self._fail(
                self._gate_failure_code(gate),
                "The Contract cannot be fixed safely without changing meaning.",
            )
        source_identity = {
            "byte_size": len(source_bytes),
            "encoding": "UTF-8",
            "filename": filename,
            "sha256": source_sha256,
        }
        wrapper_identity = {
            "byte_size": len(wrapper_bytes),
            "sha256": wrapper_sha256,
        }
        draft_identity = {
            "byte_size": len(draft_bytes),
            "schema": DRAFT_SCHEMA,
            "sha256": sha256_bytes(draft_bytes),
        }
        receipt = {
            "active_prior_request_id": value.active_prior_request_id,
            "compiler_version": COMPILER_VERSION,
            "contract_profile": profile,
            "detected_contract_title": title,
            "detected_layer_roles": {"primary": "V9", "supporting": "V13"},
            "draft_identity": draft_identity,
            "implementation_authority_state": "NONE",
            "producer_identity": PRODUCER_IDENTITY,
            "repository_identity": value.repository_identity,
            "source_identity": source_identity,
            "wrapper_identity": wrapper_identity,
        }
        return ContractFixationOutput(
            source_identity=source_identity,
            detected_contract_title=title,
            detected_layer_roles={"primary": "V9", "supporting": "V13"},
            implementation_authority_state="NONE",
            contract_profile=profile,
            wrapper_bytes=wrapper_bytes,
            wrapper_identity=wrapper_identity,
            draft_bytes=draft_bytes,
            draft_identity=draft_identity,
            producer_identity=PRODUCER_IDENTITY,
            preparation_receipt=receipt,
        )


def _empty_state() -> dict[str, Any]:
    return {
        "action_error": None,
        "errors": {},
        "fix": None,
        "friction": {
            "clarification_count": 0,
            "failed_automatic_recovery_count": 0,
            "repeated_click_count": 0,
            "selection_started_ms": None,
            "user_intervention_count": 0,
        },
        "idempotency": {},
        "operation_revision": 0,
        "preparation": None,
        "schema": STATE_SCHEMA,
        "state": "NO_CONTRACT",
    }


class OrdinaryUserPathStore:
    """Private integrity-wrapped sidecar for orchestration and friction state."""

    _locks_guard = threading.Lock()
    _locks: dict[str, threading.RLock] = {}

    def __init__(self, repository: Path) -> None:
        self.repository = Path(repository).resolve()
        self.git_common_dir = _git_common_directory(self.repository)
        self.root = self.git_common_dir / "decision-os" / "ordinary-user-path-v0.1"
        self.state_path = self.root / "state.json"
        self.lock_path = self.root / ".transaction.lock"
        with self._locks_guard:
            self._lock = self._locks.setdefault(
                str(self.git_common_dir), threading.RLock()
            )

    def _ensure_directories(self) -> None:
        cursor = self.git_common_dir
        for part in ("decision-os", "ordinary-user-path-v0.1"):
            cursor = cursor / part
            if cursor.is_symlink():
                raise OrdinaryUserPathIntegrityError(
                    "ORDINARY_STORE_CORRUPT",
                    "Ordinary Contract state is corrupted.",
                    http_status=409,
                )
            cursor.mkdir(mode=0o700, exist_ok=True)
            os.chmod(cursor, 0o700)
        for part in ("preparation-receipts", "friction"):
            directory = self.root / part
            if directory.is_symlink():
                raise OrdinaryUserPathIntegrityError(
                    "ORDINARY_STORE_CORRUPT",
                    "Ordinary Contract state is corrupted.",
                    http_status=409,
                )
            directory.mkdir(mode=0o700, exist_ok=True)
            os.chmod(directory, 0o700)

    @staticmethod
    def _assert_private_file(path: Path) -> None:
        metadata = path.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract state is corrupted.",
                http_status=409,
            )

    @contextmanager
    def transaction(self, *, write: bool = True, timeout_seconds: float = 5.0) -> Any:
        descriptor: int | None = None
        with self._lock:
            if write:
                self._ensure_directories()
            elif not self.root.exists():
                yield
                return
            flags = os.O_RDWR | os.O_CREAT if write else os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                descriptor = os.open(self.lock_path, flags, 0o600)
                if write:
                    os.chmod(self.lock_path, 0o600)
                self._assert_private_file(self.lock_path)
            except OSError as exc:
                raise OrdinaryUserPathIntegrityError(
                    "ORDINARY_STORE_CORRUPT",
                    "Ordinary Contract state is corrupted.",
                    http_status=409,
                ) from exc
            deadline = time.monotonic() + timeout_seconds
            try:
                while True:
                    try:
                        fcntl.flock(
                            descriptor,
                            (fcntl.LOCK_EX if write else fcntl.LOCK_SH)
                            | fcntl.LOCK_NB,
                        )
                        break
                    except BlockingIOError as exc:
                        if time.monotonic() >= deadline:
                            raise OrdinaryUserPathError(
                                "ORDINARY_BUSY",
                                "The ordinary Contract path is temporarily busy.",
                                http_status=409,
                            ) from exc
                        time.sleep(0.01)
                with self._lock:
                    yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)

    def _atomic_write(self, target: Path, payload: bytes) -> None:
        self._ensure_directories()
        if target.is_symlink() or target.parent.resolve() not in {
            self.root.resolve(),
            (self.root / "preparation-receipts").resolve(),
            (self.root / "friction").resolve(),
        }:
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract state is corrupted.",
                http_status=409,
            )
        temporary = target.parent / f".{target.name}.{uuid.uuid4().hex}.tmp"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            os.chmod(target, 0o600)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return _empty_state()
        if self.state_path.is_symlink():
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract state is corrupted.",
                http_status=409,
            )
        self._assert_private_file(self.state_path)
        try:
            wrapped = json.loads(
                self.state_path.read_bytes(),
                object_pairs_hook=_integrity_object,
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract state is corrupted.",
                http_status=409,
            ) from exc
        if (
            not isinstance(wrapped, dict)
            or set(wrapped) != {"record", "record_sha256", "schema"}
            or wrapped.get("schema") != STORE_SCHEMA
            or not isinstance(wrapped.get("record"), dict)
            or wrapped.get("record_sha256")
            != sha256_bytes(canonical_json(wrapped["record"]))
        ):
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract state is corrupted.",
                http_status=409,
            )
        state = wrapped["record"]
        allowed_states = {
            "NO_CONTRACT",
            "PREPARING",
            "REVIEW_READY",
            "NEEDS_CONFIRMATION",
            "CANNOT_FIX_SAFELY",
            "FIXING",
            "FIXED",
            "FIX_FAILED",
        }
        if (
            set(state) != set(_empty_state())
            or state.get("schema") != STATE_SCHEMA
            or state.get("state") not in allowed_states
            or not isinstance(state.get("operation_revision"), int)
            or isinstance(state.get("operation_revision"), bool)
            or state["operation_revision"] < 0
            or not isinstance(state.get("errors"), dict)
            or not isinstance(state.get("idempotency"), dict)
            or not isinstance(state.get("friction"), dict)
            or set(state["friction"])
            != set(_empty_state()["friction"])
            or (
                state.get("preparation") is not None
                and not isinstance(state.get("preparation"), dict)
            )
            or (
                state.get("fix") is not None
                and not isinstance(state.get("fix"), dict)
            )
            or (
                state.get("action_error") is not None
                and state.get("action_error") not in state["errors"]
            )
        ):
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract state is corrupted.",
                http_status=409,
            )
        return state

    def save_state(self, state: Mapping[str, Any]) -> None:
        record = deepcopy(dict(state))
        payload = canonical_json(
            {
                "record": record,
                "record_sha256": sha256_bytes(canonical_json(record)),
                "schema": STORE_SCHEMA,
            }
        )
        self._atomic_write(self.state_path, payload)

    def store_preparation_receipt(self, receipt: Mapping[str, Any]) -> str:
        payload = canonical_json(receipt)
        digest = sha256_bytes(payload)
        target = self.root / "preparation-receipts" / f"{digest}.json"
        if target.exists():
            self._assert_private_file(target)
            if target.read_bytes() != payload:
                raise OrdinaryUserPathIntegrityError(
                    "ORDINARY_STORE_CORRUPT",
                    "Ordinary Contract receipt identity is corrupted.",
                    http_status=409,
                )
        else:
            self._atomic_write(target, payload)
        return digest

    def read_preparation_receipt(self, digest: str) -> dict[str, Any]:
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract receipt identity is corrupted.",
                http_status=409,
            )
        target = self.root / "preparation-receipts" / f"{digest}.json"
        if not target.exists() or target.is_symlink():
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract receipt identity is corrupted.",
                http_status=409,
            )
        self._assert_private_file(target)
        try:
            payload = target.read_bytes()
            receipt = json.loads(payload, object_pairs_hook=_integrity_object)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract receipt identity is corrupted.",
                http_status=409,
            ) from exc
        if (
            sha256_bytes(payload) != digest
            or canonical_json(receipt) != payload
            or not isinstance(receipt, dict)
            or receipt.get("schema") != PREPARATION_RECEIPT_SCHEMA
        ):
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary Contract receipt identity is corrupted.",
                http_status=409,
            )
        return receipt

    def store_friction_receipt(self, receipt: Mapping[str, Any]) -> None:
        target = self.root / "friction" / "first-implementation-run.json"
        if target.is_symlink():
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary friction evidence is corrupted.",
                http_status=409,
            )
        if target.exists():
            self._assert_private_file(target)
            try:
                payload = target.read_bytes()
            except OSError as exc:
                raise OrdinaryUserPathIntegrityError(
                    "ORDINARY_STORE_CORRUPT",
                    "Ordinary friction evidence is corrupted.",
                    http_status=409,
                ) from exc
            self._validate_friction_receipt(payload)
            return
        payload = canonical_json(receipt)
        self._validate_friction_receipt(payload)
        self._atomic_write(target, payload)

    @staticmethod
    def _validate_friction_receipt(payload: bytes) -> dict[str, Any]:
        try:
            receipt = json.loads(payload, object_pairs_hook=_integrity_object)
        except OrdinaryUserPathIntegrityError:
            raise
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary friction evidence is corrupted.",
                http_status=409,
            ) from exc
        expected_keys = {
            "schema",
            "run_ordinal",
            "visible_user_actions",
            "visible_user_action_count",
            "repeated_click_count",
            "waiting_intervals_ms",
            "clarification_count",
            "failed_automatic_recovery_count",
            "user_intervention_count",
            "internal_terms_exposed",
        }
        counts = (
            (
                receipt.get("visible_user_action_count"),
                receipt.get("repeated_click_count"),
                receipt.get("clarification_count"),
                receipt.get("failed_automatic_recovery_count"),
                receipt.get("user_intervention_count"),
            )
            if isinstance(receipt, dict)
            else ()
        )
        waiting = (
            receipt.get("waiting_intervals_ms")
            if isinstance(receipt, dict)
            else None
        )
        if (
            not isinstance(receipt, dict)
            or set(receipt) != expected_keys
            or receipt.get("schema") != FRICTION_SCHEMA
            or not isinstance(receipt.get("run_ordinal"), int)
            or isinstance(receipt.get("run_ordinal"), bool)
            or receipt.get("run_ordinal") != 1
            or receipt.get("visible_user_actions")
            != ["SELECT_CONTRACT", "REVIEW_INTERPRETATION", "FIX_CONTRACT"]
            or receipt.get("visible_user_action_count") != 3
            or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 0
                for value in counts
            )
            or not isinstance(waiting, dict)
            or set(waiting) != {"selection_to_review_ready", "fix_to_receipt"}
            or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 0
                for value in waiting.values()
            )
            or receipt.get("internal_terms_exposed") != []
            or canonical_json(receipt) != payload
        ):
            raise OrdinaryUserPathIntegrityError(
                "ORDINARY_STORE_CORRUPT",
                "Ordinary friction evidence is corrupted.",
                http_status=409,
            )
        return receipt


class ConfirmationDeltaBuilder:
    """Map one bound ordinary answer to one precompiled native delta."""

    @staticmethod
    def build(clarification: Mapping[str, Any], answer: str) -> dict[str, Any]:
        if answer not in {"CONFIRM", "REJECT"}:
            raise OrdinaryUserPathError(
                "CONFIRM_ANSWER_INVALID",
                "Choose Yes or No for the current question.",
                http_status=400,
            )
        answers = clarification.get("answer_deltas")
        delta = answers.get(answer) if isinstance(answers, dict) else None
        if not isinstance(delta, dict):
            raise OrdinaryUserPathError(
                "CONFIRM_DELTA_INVALID",
                "That answer cannot be mapped safely.",
                http_status=422,
            )
        return deepcopy(delta)


class OrdinaryUserPathCoordinator:
    """Server-side ordinary-path orchestration over native Guided Intake."""

    def __init__(
        self,
        repository: Path,
        guided_intake: GuidedIntakeController,
        *,
        compiler: ContractFixationCompiler | None = None,
        clock: Callable[[], datetime | str] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.repository = Path(repository).resolve()
        self.guided_intake = guided_intake
        self.compiler = compiler or ContractFixationCompiler()
        self.store = OrdinaryUserPathStore(self.repository)
        self._clock = clock or _utc_now
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))

    def _now(self) -> str:
        return _timestamp(self._clock())

    def _now_ms(self) -> int:
        return _clock_milliseconds(self._clock())

    def _new_id(self, prefix: str) -> str:
        value = f"{prefix}-{self._id_factory()}"
        if not _SAFE_ID.fullmatch(value):
            raise OrdinaryUserPathError(
                "ORDINARY_STORE_CORRUPT",
                "An ordinary-path identity could not be generated.",
                http_status=500,
            )
        return value

    @staticmethod
    def _uuid(value: Any) -> str:
        if not isinstance(value, str):
            raise OrdinaryUserPathError(
                "ORDINARY_IDEMPOTENCY_CONFLICT",
                "A valid action identity is required.",
                http_status=400,
            )
        try:
            parsed = uuid.UUID(value)
        except (ValueError, AttributeError) as exc:
            raise OrdinaryUserPathError(
                "ORDINARY_IDEMPOTENCY_CONFLICT",
                "A valid action identity is required.",
                http_status=400,
            ) from exc
        if str(parsed) != value:
            raise OrdinaryUserPathError(
                "ORDINARY_IDEMPOTENCY_CONFLICT",
                "A canonical action identity is required.",
                http_status=400,
            )
        return value

    @staticmethod
    def _payload_digest(value: Mapping[str, Any]) -> str:
        return sha256_bytes(canonical_json(value))

    def _idempotency(
        self,
        state: dict[str, Any],
        *,
        operation: str,
        key: str,
        payload_digest: str,
    ) -> dict[str, Any] | None:
        digest = sha256_bytes(key.encode("utf-8"))
        existing = state["idempotency"].get(digest)
        if existing is None:
            state["idempotency"][digest] = {
                "error_id": None,
                "operation": operation,
                "payload_digest": payload_digest,
                "result_state": None,
                "status": "PENDING",
            }
            return None
        if (
            existing.get("operation") != operation
            or existing.get("payload_digest") != payload_digest
        ):
            state["friction"]["repeated_click_count"] += 1
            raise OrdinaryUserPathError(
                "ORDINARY_IDEMPOTENCY_CONFLICT",
                "This action identity was already used for different input.",
                http_status=409,
            )
        state["friction"]["repeated_click_count"] += 1
        if existing.get("status") == "ERROR":
            error = state["errors"].get(existing.get("error_id"), {})
            raise OrdinaryUserPathError(
                str(error.get("code", "ORDINARY_STORE_CORRUPT")),
                str(error.get("what_failed", "The ordinary action failed.")),
                http_status=self._status_for_code(str(error.get("code", ""))),
                error_id=existing.get("error_id"),
            )
        return existing

    @staticmethod
    def _status_for_code(code: str) -> int:
        if code == "PREP_SOURCE_TOO_LARGE":
            return 413
        if code.startswith("PREP_") and code not in {
            "PREP_STALE_REPOSITORY",
            "PREP_STALE_REQUEST",
            "PREP_INTERRUPTED",
        }:
            return 422 if code not in {
                "PREP_UNSUPPORTED_EXTENSION",
                "PREP_SOURCE_TRANSPORT_MISMATCH",
                "PREP_INVALID_UTF8",
                "PREP_EMPTY_SOURCE",
                "PREP_SOURCE_BOUNDARY_UNREPRESENTABLE",
            } else 400
        if code.startswith("CONFIRM_"):
            return 400 if code.endswith("INVALID") else 409
        if code.startswith("FIX_") or code.startswith("RECEIPT_"):
            return 409
        return 409

    def _record_error(
        self,
        state: dict[str, Any],
        *,
        scope: str,
        code: str,
        message: str,
        current_state: str,
        anything_fixed: str,
        user_action: str,
        retryable: bool,
        operation_id: str | None,
        idempotency_key: str | None = None,
    ) -> OrdinaryUserPathError:
        error_id = self._new_id("OUP-ERR")
        record = {
            "schema": ERROR_SCHEMA,
            "error_id": error_id,
            "scope": scope,
            "code": code,
            "what_failed": message,
            "current_state": current_state,
            "anything_fixed": anything_fixed,
            "user_action_required": user_action,
            "retryable": retryable,
            "operation_id": operation_id,
            "recorded_at": self._now(),
            "dismissed_at": None,
        }
        state["errors"][error_id] = record
        state["action_error"] = error_id
        state["state"] = current_state
        state["operation_revision"] += 1
        if idempotency_key is not None:
            key_digest = sha256_bytes(idempotency_key.encode("utf-8"))
            entry = state["idempotency"].get(key_digest)
            if isinstance(entry, dict):
                entry["error_id"] = error_id
                entry["result_state"] = current_state
                entry["status"] = "ERROR"
        self.store.save_state(state)
        return OrdinaryUserPathError(
            code,
            message,
            http_status=self._status_for_code(code),
            error_id=error_id,
        )

    @staticmethod
    def _fix_outcome_blocks_selection(state: Mapping[str, Any]) -> bool:
        if state.get("state") != "FIX_FAILED":
            return False
        fix = state.get("fix")
        operation_id = fix.get("operation_id") if isinstance(fix, dict) else None
        for record in reversed(list(state.get("errors", {}).values())):
            if (
                isinstance(record, dict)
                and record.get("operation_id") == operation_id
                and record.get("scope") in {"FIXATION", "RECEIPT_PERSISTENCE"}
            ):
                return record.get("anything_fixed") in {
                    "YES",
                    "UNKNOWN_READ_BACK_REQUIRED",
                }
        return False

    @staticmethod
    def _review(
        guided: Mapping[str, Any],
        profile: Any,
    ) -> dict[str, Any] | None:
        interpretation = guided.get("interpretation")
        if not isinstance(interpretation, dict):
            return None
        objective = interpretation.get("objective")
        completion = interpretation.get("completion_line")
        if not isinstance(objective, dict) or not isinstance(completion, dict):
            return None
        dnt = [
            item.get("text")
            for item in interpretation.get("do_not_touch", [])
            if isinstance(item, dict)
            and item.get("basis_kind") in {"USER_EXPLICIT", "USER_CONFIRMED_CANDIDATE"}
            and isinstance(item.get("text"), str)
        ]
        unresolved = [
            item.get("statement")
            for item in interpretation.get("unknown", [])
            if isinstance(item, dict)
            and item.get("current_state") == "OPEN"
            and isinstance(item.get("statement"), str)
        ]
        return {
            "preserves": objective.get("text", ""),
            "completion": (
                _PRODUCT_REVIEW_COMPLETION
                if profile == PRODUCT_PROFILE
                else (
                    _ORDINARY_REVIEW_COMPLETION
                    if profile == ORDINARY_PROFILE
                    else completion.get("text", "")
                )
            ),
            "must_not_change": dnt,
            "unresolved": unresolved,
            "does_not_authorize": _DOES_NOT_AUTHORIZE,
        }

    @staticmethod
    def _preparation_binds_current_native_state(
        preparation: Mapping[str, Any],
        guided_state: Mapping[str, Any],
        current_repository_identity: str | None,
    ) -> bool:
        interpretation = guided_state.get("current_interpretation")
        profile = preparation.get("profile")
        return (
            profile in (ORDINARY_PROFILE, PRODUCT_PROFILE)
            and preparation.get("request_id")
            == guided_state.get("active_request_id")
            and preparation.get("draft_id")
            == guided_state.get("active_draft_id")
            and isinstance(interpretation, dict)
            and preparation.get("interpretation_sha256")
            == structured_sha256(interpretation)
            and preparation.get("repository_identity")
            == current_repository_identity
        )

    def _projection(self, state: Mapping[str, Any]) -> dict[str, Any]:
        with self.guided_intake.store.transaction(
            write=False,
            timeout_seconds=0.05,
        ):
            guided_state = self.guided_intake.store.load_state()
            guided = self.guided_intake._snapshot_from_state(guided_state)
        preparation = state.get("preparation")
        local_state = str(state.get("state", "NO_CONTRACT"))
        status = {
            "NO_CONTRACT": "Select a Contract",
            "PREPARING": "Preparing…",
            "REVIEW_READY": "Ready to fix",
            "NEEDS_CONFIRMATION": "Needs your confirmation",
            "CANNOT_FIX_SAFELY": "Cannot be fixed safely",
            "FIXING": "Fixing…",
            "FIXED": "Contract fixed",
            "FIX_FAILED": "Contract could not be fixed",
        }.get(local_state, "Cannot be fixed safely")
        progress = {
            "NO_CONTRACT": "Choose one local Markdown or text Contract.",
            "PREPARING": "Reading exact bytes and checking the Contract safely.",
            "REVIEW_READY": "Review the interpretation before fixing this Contract.",
            "NEEDS_CONFIRMATION": "Answer the one question before fixation.",
            "CANNOT_FIX_SAFELY": "Choose another supported Contract.",
            "FIXING": "Rechecking the reviewed Contract and preserving its receipt.",
            "FIXED": _FIXED_MESSAGE,
            "FIX_FAILED": "Review the error before retrying safely.",
        }.get(local_state, "The Contract cannot be fixed safely.")
        allowed: list[str] = []
        if (
            local_state not in {"PREPARING", "FIXING"}
            and not self._fix_outcome_blocks_selection(state)
        ):
            allowed.append("SELECT_CONTRACT")
        if local_state == "REVIEW_READY":
            allowed.append("FIX_CONTRACT")
        if local_state == "NEEDS_CONFIRMATION":
            allowed.append("CONFIRM_ANSWER")
        error_id = state.get("action_error")
        error = state.get("errors", {}).get(error_id)
        if isinstance(error, dict) and error.get("dismissed_at") is None:
            allowed.append("DISMISS_ERROR")
        source_identity = None
        technical: dict[str, Any] = {
            "active_request_id": (
                guided.get("request_identity", {}).get("request_id")
                if isinstance(guided.get("request_identity"), dict)
                else None
            )
        }
        review = None
        clarification = None
        preparation_id = None
        try:
            current_repository_identity = _repository_head(self.repository)
        except GuidedIntakeIntegrityError:
            current_repository_identity = None
            allowed = [action for action in allowed if action != "SELECT_CONTRACT"]
            if local_state == "NO_CONTRACT":
                progress = "The selected repository needs a committed identity first."
        repository_identity = current_repository_identity
        if isinstance(preparation, dict):
            preparation_id = preparation.get("preparation_id")
            repository_identity = preparation.get("repository_identity")
            source_identity = deepcopy(preparation.get("source_identity"))
            if isinstance(source_identity, dict):
                source_identity["title"] = preparation.get("title")
                source_identity["profile"] = preparation.get("profile")
            technical.update(
                {
                    "wrapper_sha256": preparation.get("wrapper_sha256"),
                    "request_id": preparation.get("request_id"),
                    "draft_id": preparation.get("draft_id"),
                    "interpretation_sha256": preparation.get("interpretation_sha256"),
                    "gate": preparation.get("gate"),
                    "producer_identity": PRODUCER_IDENTITY,
                    "preparation_receipt_sha256": preparation.get(
                        "preparation_receipt_sha256"
                    ),
                    "freeze": deepcopy(state.get("fix", {}).get("freeze"))
                    if isinstance(state.get("fix"), dict)
                    else None,
                }
            )
            preparation_is_current = (
                self._preparation_binds_current_native_state(
                    preparation,
                    guided_state,
                    current_repository_identity,
                )
            )
            if not preparation_is_current:
                allowed = [
                    action
                    for action in allowed
                    if action not in {"FIX_CONTRACT", "CONFIRM_ANSWER"}
                ]
            if preparation_is_current and local_state in {
                "REVIEW_READY",
                "NEEDS_CONFIRMATION",
                "CANNOT_FIX_SAFELY",
                "FIXING",
                "FIXED",
                "FIX_FAILED",
            }:
                review = self._review(guided, preparation.get("profile"))
            if preparation_is_current and local_state == "NEEDS_CONFIRMATION":
                plan = preparation.get("clarification")
                if isinstance(plan, dict):
                    clarification = {
                        "clarification_id": plan.get("clarification_id"),
                        "question": plan.get("question"),
                    }
        return {
            "schema": VIEW_SCHEMA,
            "state": local_state,
            "status_label": status,
            "progress_text": progress,
            "operation_revision": state.get("operation_revision", 0),
            "preparation_id": preparation_id,
            "repository_identity": repository_identity,
            "source_identity": source_identity,
            "review": review,
            "clarification": clarification,
            "allowed_actions": allowed,
            "technical_details": technical,
            "action_error": deepcopy(error) if isinstance(error, dict) else None,
        }

    def snapshot(self) -> dict[str, Any]:
        with self.store.transaction(write=False, timeout_seconds=0.05):
            return self._projection(self.store.load_state())

    @property
    def mutation_active(self) -> bool:
        with self.store.transaction(write=False, timeout_seconds=0.05):
            return self.store.load_state().get("state") in {"PREPARING", "FIXING"}

    def recover_incomplete(self) -> None:
        """Roll forward one persisted preparation/fixation journal on startup."""

        with self.store.transaction(write=False, timeout_seconds=0.05):
            observed = self.store.load_state()
        if observed.get("state") not in {"PREPARING", "FIXING"}:
            return
        with self.store.transaction():
            state = self.store.load_state()
            if state.get("state") == "PREPARING":
                preparation = state.get("preparation")
                if not isinstance(preparation, dict):
                    self._record_error(
                        state,
                        scope="SELECTION_PREPARATION",
                        code="PREP_INTERRUPTED",
                        message="Contract preparation was interrupted before exact bytes were staged.",
                        current_state="CANNOT_FIX_SAFELY",
                        anything_fixed="NO",
                        user_action="Select the same Contract again.",
                        retryable=True,
                        operation_id=None,
                    )
                    return
                wrapper_sha256 = preparation.get("wrapper_sha256")
                draft_sha256 = preparation.get("draft_sha256")
                try:
                    with self.guided_intake.store.transaction(write=False):
                        if not (
                            isinstance(wrapper_sha256, str)
                            and isinstance(draft_sha256, str)
                            and self.guided_intake.store.blob_exists(
                                "original-requests",
                                wrapper_sha256,
                                suffix=".utf8",
                            )
                            and self.guided_intake.store.blob_exists(
                                "drafts", draft_sha256, suffix=".json"
                            )
                        ):
                            raise FileNotFoundError
                        wrapper_bytes = self.guided_intake.store.read_blob(
                            "original-requests", wrapper_sha256, suffix=".utf8"
                        )
                        draft_bytes = self.guided_intake.store.read_blob(
                            "drafts", draft_sha256, suffix=".json"
                        )
                except (FileNotFoundError, GuidedIntakeError):
                    self._record_error(
                        state,
                        scope="SELECTION_PREPARATION",
                        code="PREP_INTERRUPTED",
                        message="Contract preparation was interrupted before exact bytes were staged.",
                        current_state="CANNOT_FIX_SAFELY",
                        anything_fixed="NO",
                        user_action="Select the same Contract again.",
                        retryable=True,
                        operation_id=preparation.get("preparation_id"),
                    )
                    return
                try:
                    guided = self.guided_intake.prepare_compiled_contract(
                        wrapper_bytes=wrapper_bytes,
                        draft_bytes=draft_bytes,
                        producer_label=PRODUCER_IDENTITY,
                        expected_prior_request_id=preparation[
                            "expected_prior_request_id"
                        ],
                        request_id=preparation["request_id"],
                        draft_id=preparation["draft_id"],
                        capture_event_id=preparation["capture_event_id"],
                        import_event_id=preparation["import_event_id"],
                        captured_at=preparation["captured_at"],
                        imported_at=preparation["imported_at"],
                    )
                except (GuidedIntakeError, KeyError) as exc:
                    state["friction"]["failed_automatic_recovery_count"] += 1
                    self._record_error(
                        state,
                        scope="SELECTION_PREPARATION",
                        code="PREP_INTERRUPTED",
                        message=str(exc),
                        current_state="CANNOT_FIX_SAFELY",
                        anything_fixed="NO",
                        user_action="Select the same Contract again.",
                        retryable=True,
                        operation_id=preparation.get("preparation_id"),
                    )
                    return
                interpretation = guided.get("interpretation")
                if not isinstance(interpretation, dict):
                    self._record_error(
                        state,
                        scope="SELECTION_PREPARATION",
                        code="PREP_INTERRUPTED",
                        message="Recovered preparation did not produce a verified interpretation.",
                        current_state="CANNOT_FIX_SAFELY",
                        anything_fixed="NO",
                        user_action="Select the same Contract again.",
                        retryable=True,
                        operation_id=preparation.get("preparation_id"),
                    )
                    return
                preparation["interpretation_sha256"] = structured_sha256(
                    interpretation
                )
                preparation["gate"] = interpretation.get("gate")
                preparation["review_ready_ms"] = self._now_ms()
                with self.guided_intake.store.transaction(write=False):
                    event_chain_head = self.guided_intake.store.read_events()[
                        -1
                    ]["event_hash"]
                receipt = {
                    "active_prior_request_id": preparation[
                        "expected_prior_request_id"
                    ],
                    "compiler_version": COMPILER_VERSION,
                    "contract_profile": preparation["profile"],
                    "detected_contract_title": preparation["title"],
                    "detected_layer_roles": {
                        "primary": "V9",
                        "supporting": "V13",
                    },
                    "draft_identity": {
                        "byte_size": len(draft_bytes),
                        "schema": DRAFT_SCHEMA,
                        "sha256": draft_sha256,
                    },
                    "implementation_authority_state": "NONE",
                    "producer_identity": PRODUCER_IDENTITY,
                    "repository_identity": preparation[
                        "repository_identity"
                    ],
                    "source_identity": preparation["source_identity"],
                    "wrapper_identity": {
                        "byte_size": len(wrapper_bytes),
                        "sha256": wrapper_sha256,
                    },
                    "draft_id": preparation["draft_id"],
                    "event_chain_head": event_chain_head,
                    "gate": preparation["gate"],
                    "interpretation_sha256": preparation[
                        "interpretation_sha256"
                    ],
                    "preparation_id": preparation["preparation_id"],
                    "recorded_at": self._now(),
                    "request_id": preparation["request_id"],
                    "schema": PREPARATION_RECEIPT_SCHEMA,
                }
                preparation["preparation_receipt_sha256"] = (
                    self.store.store_preparation_receipt(receipt)
                )
                state["state"] = (
                    "REVIEW_READY"
                    if preparation["gate"] == "CLEAR ENOUGH TO FREEZE"
                    and guided.get("active_question") is None
                    else "CANNOT_FIX_SAFELY"
                )
                state["action_error"] = None
                state["operation_revision"] += 1
                for entry in state["idempotency"].values():
                    if entry.get("operation") == "PREPARE" and entry.get(
                        "status"
                    ) == "PENDING":
                        entry["result_state"] = state["state"]
                        entry["status"] = "COMPLETE"
                self.store.save_state(state)
                return

            if state.get("state") != "FIXING":
                return
            preparation = state.get("preparation")
            fix = state.get("fix")
            verified = self.guided_intake.verified_current_freeze()
            if (
                isinstance(preparation, dict)
                and isinstance(fix, dict)
                and self._matching_freeze(verified, preparation)
            ):
                fix["freeze"] = deepcopy(verified)
                fix["phase"] = "RECEIPT_VERIFIED"
                self.store.store_friction_receipt(
                    self._friction_receipt(state, self._now_ms())
                )
                state["state"] = "FIXED"
                state["action_error"] = None
                state["operation_revision"] += 1
                for entry in state["idempotency"].values():
                    if entry.get("operation") == "FIX" and entry.get(
                        "status"
                    ) == "PENDING":
                        entry["result_state"] = "FIXED"
                        entry["status"] = "COMPLETE"
                self.store.save_state(state)
                return
            state["friction"]["failed_automatic_recovery_count"] += 1
            self._record_error(
                state,
                scope="FIXATION",
                code="FIX_CALL_OUTCOME_UNKNOWN",
                message="The interrupted fixation could not be read back safely.",
                current_state="FIX_FAILED",
                anything_fixed="UNKNOWN_READ_BACK_REQUIRED",
                user_action="Do not click Fix again until receipt read-back succeeds.",
                retryable=False,
                operation_id=fix.get("operation_id") if isinstance(fix, dict) else None,
            )

    def prepare(
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
        key = self._uuid(idempotency_key)
        if (
            not isinstance(source_byte_size, int)
            or isinstance(source_byte_size, bool)
            or source_byte_size < 0
            or not isinstance(source_sha256, str)
            or not _SHA256.fullmatch(source_sha256)
            or source_byte_size != len(source_bytes)
            or source_sha256 != sha256_bytes(source_bytes)
        ):
            raise OrdinaryUserPathError(
                "PREP_SOURCE_TRANSPORT_MISMATCH",
                "The selected file changed while it was being read.",
                http_status=400,
            )
        payload_digest = self._payload_digest(
            {
                "expected_active_request_id": expected_active_request_id,
                "expected_repository_identity": expected_repository_identity,
                "filename": filename,
                "source_byte_size": source_byte_size,
                "source_sha256": source_sha256,
            }
        )
        key_digest = sha256_bytes(key.encode("utf-8"))
        with self.store.transaction():
            prior_state = self.store.load_state()
            if key_digest in prior_state["idempotency"]:
                replay = self._idempotency(
                    prior_state,
                    operation="PREPARE",
                    key=key,
                    payload_digest=payload_digest,
                )
                if replay is not None and replay.get("status") == "COMPLETE":
                    self.store.save_state(prior_state)
                    return self._projection(prior_state)
        repository_identity = _repository_head(self.repository)
        if expected_repository_identity != repository_identity:
            raise OrdinaryUserPathError(
                "PREP_STALE_REPOSITORY",
                "The selected repository changed before preparation.",
                http_status=409,
            )
        guided_before = self.guided_intake.snapshot()
        native_request = guided_before.get("request_identity")
        active_request_id = (
            native_request.get("request_id")
            if isinstance(native_request, dict)
            else None
        )
        if expected_active_request_id != active_request_id:
            raise OrdinaryUserPathError(
                "PREP_STALE_REQUEST",
                "The active Contract history changed before preparation.",
                http_status=409,
            )
        with self.store.transaction():
            state = self.store.load_state()
            replay = self._idempotency(
                state,
                operation="PREPARE",
                key=key,
                payload_digest=payload_digest,
            )
            if replay is not None and replay.get("status") == "COMPLETE":
                self.store.save_state(state)
                return self._projection(state)
            if self._fix_outcome_blocks_selection(state):
                error = state.get("errors", {}).get(state.get("action_error"))
                raise OrdinaryUserPathError(
                    str(
                        error.get("code", "FIX_CALL_OUTCOME_UNKNOWN")
                        if isinstance(error, dict)
                        else "FIX_CALL_OUTCOME_UNKNOWN"
                    ),
                    "Resolve the prior fixation receipt before selecting another Contract.",
                    http_status=409,
                    error_id=(
                        error.get("error_id") if isinstance(error, dict) else None
                    ),
                )
            existing = state.get("preparation")
            if state.get("state") in {"PREPARING", "FIXING"} and not (
                state.get("state") == "PREPARING"
                and isinstance(existing, dict)
                and existing.get("source_identity", {}).get("sha256")
                == source_sha256
                and existing.get("repository_identity") == repository_identity
                and existing.get("expected_prior_request_id") == active_request_id
            ):
                raise OrdinaryUserPathError(
                    "ORDINARY_BUSY",
                    "Another ordinary Contract action is still active.",
                    http_status=409,
                )
            if isinstance(existing, dict) and state.get("state") == "PREPARING":
                preparation = existing
            else:
                now = self._now()
                preparation = {
                    "capture_event_id": self._new_id("GI-EVT"),
                    "captured_at": now,
                    "clarification": None,
                    "draft_id": self._new_id("GI-DRAFT"),
                    "draft_sha256": None,
                    "expected_prior_request_id": active_request_id,
                    "filename": filename,
                    "gate": None,
                    "import_event_id": self._new_id("GI-EVT"),
                    "imported_at": now,
                    "interpretation_sha256": None,
                    "preparation_id": self._new_id("OUP-PREP"),
                    "preparation_receipt_sha256": None,
                    "profile": None,
                    "repository_identity": repository_identity,
                    "request_id": self._new_id("GI-REQ"),
                    "review_ready_ms": None,
                    "source_identity": {
                        "byte_size": source_byte_size,
                        "encoding": "UTF-8",
                        "filename": filename,
                        "sha256": source_sha256,
                    },
                    "started_ms": self._now_ms(),
                    "title": None,
                    "wrapper_sha256": None,
                }
            state["preparation"] = preparation
            state["state"] = "PREPARING"
            state["operation_revision"] += 1
            state["friction"]["selection_started_ms"] = preparation["started_ms"]
            self.store.save_state(state)

            try:
                compiled = self.compiler.compile(
                    ContractFixationInput(
                        source_bytes=source_bytes,
                        filename=filename,
                        repository_path=str(self.repository),
                        repository_identity=repository_identity,
                        active_prior_request_id=active_request_id,
                    )
                )
                preparation.update(
                    {
                        "draft_sha256": compiled.draft_identity["sha256"],
                        "profile": compiled.contract_profile,
                        "title": compiled.detected_contract_title,
                        "wrapper_sha256": compiled.wrapper_identity["sha256"],
                    }
                )
                self.store.save_state(state)
                guided = self.guided_intake.prepare_compiled_contract(
                    wrapper_bytes=compiled.wrapper_bytes,
                    draft_bytes=compiled.draft_bytes,
                    producer_label=compiled.producer_identity,
                    expected_prior_request_id=active_request_id,
                    request_id=preparation["request_id"],
                    draft_id=preparation["draft_id"],
                    capture_event_id=preparation["capture_event_id"],
                    import_event_id=preparation["import_event_id"],
                    captured_at=preparation["captured_at"],
                    imported_at=preparation["imported_at"],
                )
            except OrdinaryUserPathError as exc:
                raise self._record_error(
                    state,
                    scope="SELECTION_PREPARATION",
                    code=exc.code,
                    message=exc.message,
                    current_state="CANNOT_FIX_SAFELY",
                    anything_fixed="NO",
                    user_action="Select another supported Contract.",
                    retryable=False,
                    operation_id=preparation["preparation_id"],
                    idempotency_key=key,
                )
            except (GuidedIntakeConflictError, GuidedIntakeBusyError) as exc:
                code = (
                    "ORDINARY_BUSY"
                    if isinstance(exc, GuidedIntakeBusyError)
                    else "PREP_STALE_REQUEST"
                )
                raise self._record_error(
                    state,
                    scope="SELECTION_PREPARATION",
                    code=code,
                    message=str(exc),
                    current_state="CANNOT_FIX_SAFELY",
                    anything_fixed="NO",
                    user_action="Select the Contract again.",
                    retryable=True,
                    operation_id=preparation["preparation_id"],
                    idempotency_key=key,
                )
            except (GuidedIntakeValidationError, GuidedIntakeIntegrityError) as exc:
                raise self._record_error(
                    state,
                    scope="SELECTION_PREPARATION",
                    code="PREP_DRAFT_SCHEMA_INVALID",
                    message=str(exc),
                    current_state="CANNOT_FIX_SAFELY",
                    anything_fixed="NO",
                    user_action="Select another supported Contract.",
                    retryable=False,
                    operation_id=preparation["preparation_id"],
                    idempotency_key=key,
                )

            interpretation = guided.get("interpretation")
            request = guided.get("request_identity")
            if not isinstance(interpretation, dict) or not isinstance(request, dict):
                raise self._record_error(
                    state,
                    scope="SELECTION_PREPARATION",
                    code="PREP_DRAFT_SCHEMA_INVALID",
                    message="The prepared interpretation could not be verified.",
                    current_state="CANNOT_FIX_SAFELY",
                    anything_fixed="NO",
                    user_action="Select the Contract again.",
                    retryable=True,
                    operation_id=preparation["preparation_id"],
                    idempotency_key=key,
                )
            preparation["interpretation_sha256"] = structured_sha256(interpretation)
            preparation["gate"] = interpretation.get("gate")
            with self.guided_intake.store.transaction(write=False):
                event_chain_head = self.guided_intake.store.load_state()[
                    "event_chain_head"
                ]
            runtime_receipt = {
                **compiled.preparation_receipt,
                "draft_id": preparation["draft_id"],
                "event_chain_head": event_chain_head,
                "gate": preparation["gate"],
                "interpretation_sha256": preparation["interpretation_sha256"],
                "preparation_id": preparation["preparation_id"],
                "recorded_at": self._now(),
                "request_id": preparation["request_id"],
                "schema": PREPARATION_RECEIPT_SCHEMA,
            }
            preparation["preparation_receipt_sha256"] = (
                self.store.store_preparation_receipt(runtime_receipt)
            )
            active_question = guided.get("active_question")
            if preparation["gate"] == "CLEAR ENOUGH TO FREEZE" and active_question is None:
                state["state"] = "REVIEW_READY"
            elif preparation["gate"] == "NEEDS USER CONFIRMATION" and isinstance(
                active_question, dict
            ):
                state["state"] = "NEEDS_CONFIRMATION"
            else:
                state["state"] = "CANNOT_FIX_SAFELY"
            if state["state"] in {"REVIEW_READY", "NEEDS_CONFIRMATION"}:
                preparation["review_ready_ms"] = self._now_ms()
            state["action_error"] = None
            state["operation_revision"] += 1
            entry = state["idempotency"][sha256_bytes(key.encode("utf-8"))]
            entry["result_state"] = state["state"]
            entry["status"] = "COMPLETE"
            self.store.save_state(state)
            return self._projection(state)

    def confirm(
        self,
        *,
        preparation_id: str,
        clarification_id: str,
        answer: str,
        expected_interpretation_sha256: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        key = self._uuid(idempotency_key)
        payload_digest = self._payload_digest(
            {
                "answer": answer,
                "clarification_id": clarification_id,
                "expected_interpretation_sha256": expected_interpretation_sha256,
                "preparation_id": preparation_id,
            }
        )
        with self.store.transaction():
            state = self.store.load_state()
            replay = self._idempotency(
                state,
                operation="CONFIRM",
                key=key,
                payload_digest=payload_digest,
            )
            if replay is not None and replay.get("status") == "COMPLETE":
                self.store.save_state(state)
                return self._projection(state)
            preparation = state.get("preparation")
            clarification = (
                preparation.get("clarification")
                if isinstance(preparation, dict)
                else None
            )
            if state.get("state") != "NEEDS_CONFIRMATION" or not isinstance(
                clarification, dict
            ):
                raise self._record_error(
                    state,
                    scope="CLARIFICATION",
                    code="CONFIRM_NONE_ACTIVE",
                    message="There is no current question to answer.",
                    current_state="CANNOT_FIX_SAFELY",
                    anything_fixed="NO",
                    user_action="Select the Contract again.",
                    retryable=False,
                    operation_id=preparation_id,
                    idempotency_key=key,
                )
            if (
                preparation.get("preparation_id") != preparation_id
                or clarification.get("clarification_id") != clarification_id
                or preparation.get("interpretation_sha256")
                != expected_interpretation_sha256
            ):
                raise self._record_error(
                    state,
                    scope="CLARIFICATION",
                    code="CONFIRM_STALE",
                    message="The clarification changed before the answer was recorded.",
                    current_state="CANNOT_FIX_SAFELY",
                    anything_fixed="NO",
                    user_action="Review the current Contract again.",
                    retryable=False,
                    operation_id=preparation_id,
                    idempotency_key=key,
                )
            try:
                delta = ConfirmationDeltaBuilder.build(clarification, answer)
                guided = self.guided_intake.confirm(
                    clarification["question"],
                    "Yes, use this" if answer == "CONFIRM" else "No, do not use this",
                    delta,
                )
            except (OrdinaryUserPathError, GuidedIntakeValidationError) as exc:
                code = getattr(exc, "code", "CONFIRM_DELTA_INVALID")
                raise self._record_error(
                    state,
                    scope="CLARIFICATION",
                    code=code,
                    message=str(exc),
                    current_state="CANNOT_FIX_SAFELY",
                    anything_fixed="NO",
                    user_action="Select the Contract again.",
                    retryable=False,
                    operation_id=preparation_id,
                    idempotency_key=key,
                )
            interpretation = guided.get("interpretation")
            preparation["interpretation_sha256"] = structured_sha256(interpretation)
            preparation["gate"] = interpretation.get("gate")
            preparation["clarification"] = None
            state["friction"]["clarification_count"] += 1
            state["state"] = (
                "REVIEW_READY"
                if preparation["gate"] == "CLEAR ENOUGH TO FREEZE"
                else "CANNOT_FIX_SAFELY"
            )
            if state["state"] == "REVIEW_READY":
                preparation["review_ready_ms"] = self._now_ms()
            state["action_error"] = None
            state["operation_revision"] += 1
            entry = state["idempotency"][sha256_bytes(key.encode("utf-8"))]
            entry["result_state"] = state["state"]
            entry["status"] = "COMPLETE"
            self.store.save_state(state)
            return self._projection(state)

    def _matching_freeze(
        self, freeze: Mapping[str, Any] | None, preparation: Mapping[str, Any]
    ) -> bool:
        return bool(
            isinstance(freeze, Mapping)
            and freeze.get("current") is True
            and freeze.get("repository_identity")
            == preparation.get("repository_identity")
            and freeze.get("request_id") == preparation.get("request_id")
            and freeze.get("draft_id") == preparation.get("draft_id")
            and freeze.get("interpretation_sha256")
            == preparation.get("interpretation_sha256")
        )

    def _friction_receipt(self, state: Mapping[str, Any], fixed_ms: int) -> dict[str, Any]:
        preparation = state["preparation"]
        fix = state["fix"]
        review = self._review(
            self.guided_intake.snapshot(),
            preparation.get("profile"),
        ) or {}
        visible_text = "\n".join(
            [
                "Contract fixed",
                _FIXED_MESSAGE,
                str(review.get("preserves", "")),
                str(review.get("completion", "")),
                *(str(value) for value in review.get("must_not_change", [])),
                *(str(value) for value in review.get("unresolved", [])),
                str(review.get("does_not_authorize", "")),
            ]
        )
        return {
            "schema": FRICTION_SCHEMA,
            "run_ordinal": 1,
            "visible_user_actions": [
                "SELECT_CONTRACT",
                "REVIEW_INTERPRETATION",
                "FIX_CONTRACT",
            ],
            "visible_user_action_count": 3,
            "repeated_click_count": state["friction"]["repeated_click_count"],
            "waiting_intervals_ms": {
                "selection_to_review_ready": max(
                    0,
                    int(preparation.get("review_ready_ms") or fix["started_ms"])
                    - int(preparation["started_ms"]),
                ),
                "fix_to_receipt": max(0, fixed_ms - int(fix["started_ms"])),
            },
            "clarification_count": state["friction"]["clarification_count"],
            "failed_automatic_recovery_count": state["friction"][
                "failed_automatic_recovery_count"
            ],
            "user_intervention_count": state["friction"]["user_intervention_count"],
            "internal_terms_exposed": [
                term for term in _ORDINARY_VISIBLE_DENYLIST if term in visible_text
            ],
        }

    def fix(
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
        key = self._uuid(idempotency_key)
        payload_digest = self._payload_digest(
            {
                "expected_draft_id": expected_draft_id,
                "expected_interpretation_sha256": expected_interpretation_sha256,
                "expected_repository_identity": expected_repository_identity,
                "expected_request_id": expected_request_id,
                "expected_source_sha256": expected_source_sha256,
                "preparation_id": preparation_id,
            }
        )
        with self.store.transaction():
            state = self.store.load_state()
            replay = self._idempotency(
                state,
                operation="FIX",
                key=key,
                payload_digest=payload_digest,
            )
            if replay is not None and replay.get("status") == "COMPLETE":
                self.store.save_state(state)
                return self._projection(state)
            preparation = state.get("preparation")
            if not isinstance(preparation, dict):
                raise self._record_error(
                    state,
                    scope="FIXATION",
                    code="FIX_NOT_READY",
                    message="No reviewed Contract is ready to fix.",
                    current_state="FIX_FAILED",
                    anything_fixed="NO",
                    user_action="Select and review a Contract first.",
                    retryable=False,
                    operation_id=None,
                    idempotency_key=key,
                )
            bindings = (
                ("preparation_id", preparation_id, "FIX_NOT_READY"),
                ("repository_identity", expected_repository_identity, "FIX_STALE_REPOSITORY"),
                ("request_id", expected_request_id, "FIX_STALE_REQUEST"),
                ("draft_id", expected_draft_id, "FIX_STALE_DRAFT"),
                (
                    "interpretation_sha256",
                    expected_interpretation_sha256,
                    "FIX_STALE_INTERPRETATION",
                ),
            )
            for field, expected, code in bindings:
                if preparation.get(field) != expected:
                    raise self._record_error(
                        state,
                        scope="FIXATION",
                        code=code,
                        message="The reviewed Contract changed before fixation.",
                        current_state="FIX_FAILED",
                        anything_fixed="NO",
                        user_action="Select the Contract again.",
                        retryable=False,
                        operation_id=preparation_id,
                        idempotency_key=key,
                    )
            if preparation.get("source_identity", {}).get("sha256") != expected_source_sha256:
                raise self._record_error(
                    state,
                    scope="FIXATION",
                    code="FIX_STALE_SOURCE",
                    message="The selected Contract changed before fixation.",
                    current_state="FIX_FAILED",
                    anything_fixed="NO",
                    user_action="Select the Contract again.",
                    retryable=False,
                    operation_id=preparation_id,
                    idempotency_key=key,
                )
            receipt = self.store.read_preparation_receipt(
                preparation.get("preparation_receipt_sha256")
            )
            if (
                receipt.get("source_identity") != preparation.get("source_identity")
                or receipt.get("wrapper_identity", {}).get("sha256")
                != preparation.get("wrapper_sha256")
                or receipt.get("draft_identity", {}).get("sha256")
                != preparation.get("draft_sha256")
                or receipt.get("repository_identity")
                != preparation.get("repository_identity")
                or receipt.get("request_id") != preparation.get("request_id")
                or receipt.get("draft_id") != preparation.get("draft_id")
                or receipt.get("interpretation_sha256")
                != preparation.get("interpretation_sha256")
            ):
                raise self._record_error(
                    state,
                    scope="FIXATION",
                    code="FIX_STALE_SOURCE",
                    message="The prepared Contract receipt no longer matches the review.",
                    current_state="FIX_FAILED",
                    anything_fixed="NO",
                    user_action="Select the Contract again.",
                    retryable=False,
                    operation_id=preparation_id,
                    idempotency_key=key,
                )
            guided = self.guided_intake.snapshot()
            interpretation = guided.get("interpretation")
            request = guided.get("request_identity")
            if _repository_head(self.repository) != expected_repository_identity:
                code = "FIX_STALE_REPOSITORY"
            elif not isinstance(request, dict) or request.get(
                "request_id"
            ) != expected_request_id:
                code = "FIX_STALE_REQUEST"
            else:
                with self.guided_intake.store.transaction(write=False):
                    active_draft_id = self.guided_intake.store.load_state().get(
                        "active_draft_id"
                    )
                if active_draft_id != expected_draft_id:
                    code = "FIX_STALE_DRAFT"
                elif (
                    not isinstance(interpretation, dict)
                    or structured_sha256(interpretation)
                    != expected_interpretation_sha256
                ):
                    code = "FIX_STALE_INTERPRETATION"
                elif guided.get("active_question") is not None:
                    code = "FIX_ACTIVE_CLARIFICATION"
                elif interpretation.get("gate") != "CLEAR ENOUGH TO FREEZE":
                    code = "FIX_GATE_MISMATCH"
                else:
                    code = None
            if code is not None:
                raise self._record_error(
                    state,
                    scope="FIXATION",
                    code=code,
                    message="The reviewed Contract changed before fixation.",
                    current_state="FIX_FAILED",
                    anything_fixed="NO",
                    user_action="Select the Contract again.",
                    retryable=False,
                    operation_id=preparation_id,
                    idempotency_key=key,
                )
            existing_freeze = self.guided_intake.verified_current_freeze()
            if self._matching_freeze(existing_freeze, preparation):
                fix_record = state.get("fix")
                if not isinstance(fix_record, dict) or fix_record.get("operation_id") is None:
                    raise self._record_error(
                        state,
                        scope="FIXATION",
                        code="FIX_ALREADY_FROZEN_OUTSIDE_OPERATION",
                        message="This interpretation was fixed outside the ordinary action.",
                        current_state="FIX_FAILED",
                        anything_fixed="YES",
                        user_action="Review the native receipt in Advanced / Audit Mode.",
                        retryable=False,
                        operation_id=preparation_id,
                        idempotency_key=key,
                    )
            else:
                existing_freeze = None
            if state.get("state") == "FIXED" and self._matching_freeze(
                existing_freeze, preparation
            ):
                entry = state["idempotency"][sha256_bytes(key.encode("utf-8"))]
                entry["result_state"] = "FIXED"
                entry["status"] = "COMPLETE"
                self.store.save_state(state)
                return self._projection(state)
            if not self._matching_freeze(existing_freeze, preparation):
                state["fix"] = {
                    "freeze": None,
                    "operation_id": self._new_id("OUP-FIX"),
                    "phase": "CALL_STARTED",
                    "started_ms": self._now_ms(),
                }
                state["state"] = "FIXING"
                state["operation_revision"] += 1
                self.store.save_state(state)
                try:
                    self.guided_intake.freeze()
                    state["fix"]["phase"] = "CALL_RETURNED"
                    self.store.save_state(state)
                except GuidedIntakeConflictError as exc:
                    raise self._record_error(
                        state,
                        scope="FIXATION",
                        code="FIX_NATIVE_REJECTED",
                        message=str(exc),
                        current_state="FIX_FAILED",
                        anything_fixed="NO",
                        user_action="Retry only after reviewing the current Contract.",
                        retryable=True,
                        operation_id=state["fix"]["operation_id"],
                        idempotency_key=key,
                    )
                except Exception as exc:
                    recovered = self.guided_intake.verified_current_freeze()
                    if not self._matching_freeze(recovered, preparation):
                        state["friction"]["failed_automatic_recovery_count"] += 1
                        raise self._record_error(
                            state,
                            scope="FIXATION",
                            code="FIX_CALL_OUTCOME_UNKNOWN",
                            message="The fixation result could not be read back safely.",
                            current_state="FIX_FAILED",
                            anything_fixed="UNKNOWN_READ_BACK_REQUIRED",
                            user_action="Do not click Fix again until receipt read-back succeeds.",
                            retryable=False,
                            operation_id=state["fix"]["operation_id"],
                            idempotency_key=key,
                        ) from exc
                    existing_freeze = recovered
            verified = existing_freeze or self.guided_intake.verified_current_freeze()
            if not self._matching_freeze(verified, preparation):
                raise self._record_error(
                    state,
                    scope="RECEIPT_PERSISTENCE",
                    code="RECEIPT_IDENTITY_MISMATCH",
                    message="The native fixation receipt did not match the reviewed Contract.",
                    current_state="FIX_FAILED",
                    anything_fixed="UNKNOWN_READ_BACK_REQUIRED",
                    user_action="Do not retry fixation until the receipt can be verified.",
                    retryable=False,
                    operation_id=state.get("fix", {}).get("operation_id"),
                    idempotency_key=key,
                )
            state["fix"]["freeze"] = deepcopy(verified)
            state["fix"]["phase"] = "RECEIPT_VERIFIED"
            try:
                fixed_ms = self._now_ms()
                self.store.store_friction_receipt(
                    self._friction_receipt(state, fixed_ms)
                )
            except Exception as exc:
                raise self._record_error(
                    state,
                    scope="RECEIPT_PERSISTENCE",
                    code="RECEIPT_PERSISTENCE_FAILED",
                    message="The fixation succeeded, but its local ordinary receipt could not be preserved.",
                    current_state="FIX_FAILED",
                    anything_fixed="YES",
                    user_action="Retry receipt preservation without fixing again.",
                    retryable=True,
                    operation_id=state["fix"]["operation_id"],
                    idempotency_key=key,
                ) from exc
            state["state"] = "FIXED"
            state["action_error"] = None
            state["operation_revision"] += 1
            entry = state["idempotency"][sha256_bytes(key.encode("utf-8"))]
            entry["result_state"] = "FIXED"
            entry["status"] = "COMPLETE"
            self.store.save_state(state)
            return self._projection(state)

    def dismiss_error(self, *, error_id: str, idempotency_key: str) -> dict[str, Any]:
        key = self._uuid(idempotency_key)
        if not isinstance(error_id, str) or not _SAFE_ID.fullmatch(error_id):
            raise OrdinaryUserPathError(
                "ORDINARY_STORE_CORRUPT",
                "The ordinary error identity is invalid.",
                http_status=400,
            )
        payload_digest = self._payload_digest({"error_id": error_id})
        with self.store.transaction():
            state = self.store.load_state()
            replay = self._idempotency(
                state,
                operation="DISMISS_ERROR",
                key=key,
                payload_digest=payload_digest,
            )
            if replay is not None and replay.get("status") == "COMPLETE":
                self.store.save_state(state)
                return self._projection(state)
            record = state["errors"].get(error_id)
            if not isinstance(record, dict) or state.get("action_error") != error_id:
                raise OrdinaryUserPathError(
                    "ORDINARY_IDEMPOTENCY_CONFLICT",
                    "That ordinary error is no longer current.",
                    http_status=409,
                )
            if record.get("dismissed_at") is None:
                record["dismissed_at"] = self._now()
                state["friction"]["user_intervention_count"] += 1
            state["action_error"] = None
            state["operation_revision"] += 1
            entry = state["idempotency"][sha256_bytes(key.encode("utf-8"))]
            entry["result_state"] = state["state"]
            entry["status"] = "COMPLETE"
            self.store.save_state(state)
            return self._projection(state)

    def record_external_error(self, *, code: str, message: str) -> str:
        """Persist one API-boundary failure in the ordinary action panel."""

        if not isinstance(code, str) or not code or not isinstance(message, str):
            raise OrdinaryUserPathError(
                "ORDINARY_STORE_CORRUPT",
                "The ordinary error record is invalid.",
                http_status=500,
            )
        if code.startswith("FIX_") or code.startswith("RECEIPT_"):
            scope = (
                "RECEIPT_PERSISTENCE"
                if code.startswith("RECEIPT_")
                else "FIXATION"
            )
            target_state = "FIX_FAILED"
            action = "Review the Contract and retry only when the panel allows it."
        elif code.startswith("CONFIRM_"):
            scope = "CLARIFICATION"
            target_state = "CANNOT_FIX_SAFELY"
            action = "Review the current clarification or select the Contract again."
        else:
            scope = "SELECTION_PREPARATION"
            target_state = "CANNOT_FIX_SAFELY"
            action = "Select a supported Contract again."
        with self.store.transaction():
            state = self.store.load_state()
            if state.get("state") in {"PREPARING", "FIXING"}:
                raise OrdinaryUserPathError(
                    "ORDINARY_BUSY",
                    "Another ordinary Contract action is still active.",
                    http_status=409,
                )
            recorded = self._record_error(
                state,
                scope=scope,
                code=code,
                message=message,
                current_state=target_state,
                anything_fixed="NO",
                user_action=action,
                retryable=False,
                operation_id=(
                    state.get("preparation", {}).get("preparation_id")
                    if isinstance(state.get("preparation"), dict)
                    else None
                ),
            )
            return str(recorded.error_id)
