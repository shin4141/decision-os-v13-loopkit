"""Private repository-local persistence for Intelligence Transplant v0.1.

The companion layer stores exact Stage 5 records and transport bytes below the
selected repository's Git common directory.  It performs no model invocation,
role assignment, working-tree write, or authority upgrade.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import stat
import subprocess
import threading
import time
from typing import Any
import uuid

from decision_os.intelligence_transplant import (
    AUDIT_INPUT_MANIFEST,
    E1_DISCOVERY,
    E2_AUDIT,
    E3_ACCEPTED_DISCOVERY,
    E4_IMPLEMENTATION_BINDING,
    E5_REUSE,
    LOWER_RUN_TRIAL_MANIFEST,
    MANUAL_CONTROL_RECEIPT,
    RUN_CHARTER,
    canonical_json,
    compute_content_hash,
    exact_ref,
    reduce_evidence_graph,
    strict_json_object,
    validate_graph,
    validate_object,
)


STORE_SCHEMA = "decision-os-intelligence-transplant-store-v0.1"
TRANSPORT_SCHEMA = "intelligence-transplant-transport-receipt-v0.1"
GENESIS_EVENT_HASH = "0" * 64
EVENT_KINDS = frozenset(
    {
        "CHARTER_FROZEN",
        "MANIFEST_FROZEN",
        "OBJECT_ATTACHED",
        "CONTROL_RECORDED",
    }
)
_BLOB_DIRECTORIES = {
    "charter": "charters",
    "evidence": "evidence",
    "manifest": "manifests",
}
_MANIFEST_TYPES = frozenset(
    {AUDIT_INPUT_MANIFEST, LOWER_RUN_TRIAL_MANIFEST}
)
_EVIDENCE_TYPES = frozenset(
    {
        "SEAT_ASSIGNMENT_RECEIPT",
        E1_DISCOVERY,
        E2_AUDIT,
        "AUDIT_COMPLETION_RECEIPT",
        E3_ACCEPTED_DISCOVERY,
        E4_IMPLEMENTATION_BINDING,
        "LOWER_RUN_COMPLETION_RECEIPT",
        E5_REUSE,
    }
)
_EVENT_FIELDS = {
    "event_hash",
    "event_id",
    "kind",
    "payload",
    "previous_event_hash",
    "recorded_at",
    "schema_version",
}
_EVENT_PAYLOAD_FIELDS = {
    "blob_kind",
    "content_hash",
    "object_id",
    "object_type",
    "repository_head",
    "transport_receipt",
    "transport_sha256",
}
_TRANSPORT_FIELDS = {
    "as_of",
    "context_evidence_ref",
    "declared_sha256",
    "exact_payload_sha256",
    "mode",
    "receipt_sha256",
    "schema_version",
    "source_path_or_label",
}
_HEAD_FIELDS = {
    "event_chain_head",
    "event_count",
    "head_sha256",
    "schema_version",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,200}$")
_UNSAFE_GIT_CONFIG = re.compile(
    r"^(?:"
    r"core\.(?:alternaterefscommand|alternaterefsprefixes|attributesfile|"
    r"usereplacerefs|worktree)"
    r"|diff\.external"
    r"|diff\..+\.(?:command|textconv)"
    r"|extensions\.(?:partialclone|worktreeconfig)"
    r"|filter\."
    r"|include(?:if)?\."
    r"|remote\..+\.promisor"
    r")"
)
_GIT_ENVIRONMENT_OVERRIDES = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_ATTR_NOSYSTEM",
        "GIT_CEILING_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG",
        "GIT_DIR",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_EXEC_PATH",
        "GIT_GRAFT_FILE",
        "GIT_INDEX_FILE",
        "GIT_NAMESPACE",
        "GIT_NO_LAZY_FETCH",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OBJECT_DIRECTORY",
        "GIT_OPTIONAL_LOCKS",
        "GIT_PREFIX",
        "GIT_REPLACE_REF_BASE",
        "GIT_SHALLOW_FILE",
        "GIT_WORK_TREE",
    }
)


class IntelligenceTransplantError(RuntimeError):
    """Base error for private Stage 5 companion operations."""


class IntelligenceTransplantValidationError(IntelligenceTransplantError):
    """Submitted Stage 5 input does not satisfy the fixed contract."""


class IntelligenceTransplantConflictError(IntelligenceTransplantError):
    """Submitted Stage 5 input conflicts with current immutable state."""


class IntelligenceTransplantIntegrityError(IntelligenceTransplantError):
    """The private Stage 5 event or blob state cannot be trusted."""


class IntelligenceTransplantBusyError(IntelligenceTransplantConflictError):
    """Another bounded Stage 5 operation owns the repository store."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _event_id_for_content_hash(content_hash: str) -> str:
    if _SHA256.fullmatch(content_hash) is None:
        raise IntelligenceTransplantValidationError(
            "Stage 5 event content identity is invalid."
        )
    return f"event-{content_hash}"


def _timestamp(value: datetime | str) -> str:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise IntelligenceTransplantValidationError(
                "Stage 5 timestamp must be timezone-aware."
            ) from exc
    else:
        raise IntelligenceTransplantValidationError(
            "Stage 5 timestamp must be timezone-aware."
        )
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise IntelligenceTransplantValidationError(
            "Stage 5 timestamp must be timezone-aware."
        )
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _raw_git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_ENVIRONMENT_OVERRIDES
        and not key.startswith("GIT_CONFIG_")
        and key != "GIT_CONFIG_PARAMETERS"
    }
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "LC_ALL": "C",
        }
    )
    return environment


def _raw_git_command(
    repository: Path,
    *arguments: str,
    text: bool = False,
    timeout: float = 20,
) -> subprocess.CompletedProcess[Any]:
    try:
        return subprocess.run(
            (
                "git",
                "--no-replace-objects",
                "-c",
                "core.attributesFile=/dev/null",
                "-c",
                "core.useReplaceRefs=false",
                "-c",
                "diff.external=",
                "-c",
                "diff.renames=false",
                "-C",
                str(repository),
                *arguments,
            ),
            capture_output=True,
            check=False,
            env=_raw_git_environment(),
            text=text,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IntelligenceTransplantConflictError(
            "HOLD — STAGE 5 GIT EVIDENCE UNAVAILABLE"
        ) from exc


def _git_common_directory(repository: Path) -> Path:
    try:
        completed = _raw_git_command(
            repository,
            "rev-parse",
            "--git-common-dir",
            text=True,
            timeout=10,
        )
    except IntelligenceTransplantConflictError as exc:
        raise IntelligenceTransplantValidationError(
            "Selected repository identity could not be resolved."
        ) from exc
    if completed.returncode != 0 or not completed.stdout.strip():
        raise IntelligenceTransplantValidationError(
            "Select a valid local Git repository first."
        )
    candidate = Path(completed.stdout.strip())
    if not candidate.is_absolute():
        candidate = repository / candidate
    try:
        return candidate.resolve(strict=True)
    except OSError as exc:
        raise IntelligenceTransplantValidationError(
            "Selected repository Git state is unavailable."
        ) from exc


def _assert_raw_git_evidence_mode(repository: Path) -> None:
    layout = _raw_git_command(
        repository,
        "rev-parse",
        "--git-common-dir",
        "--git-dir",
        "--show-object-format",
        text=True,
    )
    layout_lines = layout.stdout.splitlines()
    if (
        layout.returncode != 0
        or len(layout_lines) != 3
        or layout_lines[2].strip() != "sha1"
    ):
        raise IntelligenceTransplantConflictError(
            "HOLD — STAGE 5 GIT INTERPRETATION UNSAFE"
        )
    resolved_directories: list[Path] = []
    for value in layout_lines[:2]:
        candidate = Path(value.strip())
        if not candidate.is_absolute():
            candidate = repository / candidate
        try:
            resolved_directories.append(candidate.resolve(strict=True))
        except OSError as exc:
            raise IntelligenceTransplantConflictError(
                "HOLD — STAGE 5 GIT INTERPRETATION UNSAFE"
            ) from exc
    common_directory, git_directory = resolved_directories
    grafts_paths = {
        common_directory / "info" / "grafts",
        git_directory / "info" / "grafts",
    }
    alternates_path = common_directory / "objects" / "info" / "alternates"
    if (
        any(os.path.lexists(path) for path in grafts_paths)
        or os.path.lexists(alternates_path)
    ):
        raise IntelligenceTransplantConflictError(
            "HOLD — STAGE 5 GIT INTERPRETATION UNSAFE"
        )

    replacement_refs = _raw_git_command(
        repository,
        "for-each-ref",
        "--format=%(refname)",
        "refs/replace/",
        text=True,
    )
    if replacement_refs.returncode != 0 or replacement_refs.stdout.strip():
        raise IntelligenceTransplantConflictError(
            "HOLD — STAGE 5 GIT INTERPRETATION UNSAFE"
        )

    local_config = _raw_git_command(
        repository,
        "config",
        "--no-includes",
        "--show-scope",
        "--name-only",
        "--get-regexp",
        ".*",
        text=True,
    )
    if local_config.returncode not in {0, 1}:
        raise IntelligenceTransplantConflictError(
            "HOLD — STAGE 5 GIT INTERPRETATION UNSAFE"
        )
    config_keys: set[str] = set()
    for line in local_config.stdout.splitlines():
        try:
            scope, key = line.split("\t", 1)
        except ValueError as exc:
            raise IntelligenceTransplantConflictError(
                "HOLD — STAGE 5 GIT INTERPRETATION UNSAFE"
            ) from exc
        if scope in {"local", "worktree"}:
            config_keys.add(key.strip().lower())
    if any(_UNSAFE_GIT_CONFIG.match(key) for key in config_keys):
        raise IntelligenceTransplantConflictError(
            "HOLD — STAGE 5 GIT INTERPRETATION UNSAFE"
        )


def _repository_head(repository: Path) -> str:
    try:
        _assert_raw_git_evidence_mode(repository)
        completed = _raw_git_command(
            repository,
            "rev-parse",
            "--verify",
            "HEAD^{commit}",
            text=True,
            timeout=10,
        )
    except (
        IntelligenceTransplantConflictError,
        IntelligenceTransplantValidationError,
    ) as exc:
        if (
            isinstance(exc, IntelligenceTransplantConflictError)
            and "GIT INTERPRETATION UNSAFE" in str(exc)
        ):
            raise
        raise IntelligenceTransplantConflictError(
            "HOLD — STAGE 5 REPOSITORY AS-OF STALE"
        ) from exc
    head = completed.stdout.strip()
    if completed.returncode != 0 or _COMMIT.fullmatch(head) is None:
        raise IntelligenceTransplantConflictError(
            "HOLD — STAGE 5 REPOSITORY AS-OF STALE"
        )
    return head


def _git_command(
    repository: Path,
    *arguments: str,
    text: bool = False,
) -> subprocess.CompletedProcess[Any]:
    return _raw_git_command(repository, *arguments, text=text)


def _safe_git_path(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\x00" in value
        or "\n" in value
        or "\r" in value
        or "\\" in value
    ):
        raise IntelligenceTransplantValidationError(
            "Stage 5 artifact path is unsafe."
        )
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise IntelligenceTransplantValidationError(
            "Stage 5 artifact path is unsafe."
        )
    return path.as_posix()


def _git_blob_at(repository: Path, head: str, path: str) -> tuple[str, bytes]:
    resolved = _git_command(
        repository,
        "rev-parse",
        "--verify",
        f"{head}:{path}",
        text=True,
    )
    blob_id = resolved.stdout.strip()
    if (
        resolved.returncode != 0
        or re.fullmatch(r"[0-9a-f]{40}", blob_id) is None
    ):
        raise IntelligenceTransplantValidationError(
            "Stage 5 artifact is not present at the bound repository HEAD."
        )
    object_type = _git_command(
        repository,
        "cat-file",
        "-t",
        blob_id,
        text=True,
    )
    if object_type.returncode != 0 or object_type.stdout.strip() != "blob":
        raise IntelligenceTransplantValidationError(
            "Stage 5 artifact identity is not a Git blob."
        )
    content = _git_command(repository, "cat-file", "blob", blob_id)
    if content.returncode != 0:
        raise IntelligenceTransplantValidationError(
            "Stage 5 artifact bytes are unavailable."
        )
    return blob_id, bytes(content.stdout)


def _verify_e4_git_binding(
    repository: Path,
    record: Mapping[str, Any],
    current_head: str,
) -> None:
    base = record.get("repository_base")
    head = record.get("repository_head")
    if not (
        isinstance(base, str)
        and isinstance(head, str)
        and record.get("repository_opening_head") == current_head
        and head == current_head
        and record.get("repository_closing_head") == current_head
        and record.get("repository_base_is_ancestor") is True
        and base != head
    ):
        raise IntelligenceTransplantConflictError(
            "HOLD — E4 REPOSITORY BINDING IS STALE"
        )
    base_exists = _git_command(
        repository,
        "cat-file",
        "-e",
        f"{base}^{{commit}}",
    )
    head_exists = _git_command(
        repository,
        "cat-file",
        "-e",
        f"{head}^{{commit}}",
    )
    ancestor = _git_command(
        repository,
        "merge-base",
        "--is-ancestor",
        base,
        head,
    )
    if (
        base_exists.returncode != 0
        or head_exists.returncode != 0
        or ancestor.returncode != 0
    ):
        raise IntelligenceTransplantValidationError(
            "Stage 5 E4 base/head ancestry is not established."
        )
    changed = _git_command(
        repository,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--no-renames",
        "--name-only",
        "-z",
        base,
        head,
        "--",
    )
    if changed.returncode != 0:
        raise IntelligenceTransplantValidationError(
            "Stage 5 E4 changed paths are unavailable."
        )
    try:
        changed_paths = {
            item.decode("utf-8", errors="strict")
            for item in bytes(changed.stdout).split(b"\x00")
            if item
        }
    except UnicodeDecodeError as exc:
        raise IntelligenceTransplantValidationError(
            "Stage 5 E4 changed path is not UTF-8."
        ) from exc
    observed_paths: set[str] = set()
    for artifact in record.get("changed_artifacts", ()):
        path = _safe_git_path(artifact.get("path"))
        if path in observed_paths or path not in changed_paths:
            raise IntelligenceTransplantValidationError(
                "Stage 5 E4 artifact is not an exact changed path."
            )
        blob_id, blob_bytes = _git_blob_at(repository, head, path)
        if (
            artifact.get("git_blob") != blob_id
            or artifact.get("sha256") != _sha256(blob_bytes)
        ):
            raise IntelligenceTransplantValidationError(
                "Stage 5 E4 artifact Git identity is invalid."
            )
        observed_paths.add(path)
    if observed_paths != changed_paths:
        raise IntelligenceTransplantValidationError(
            "Stage 5 E4 changed paths are not completely bound."
        )


def _verify_rollback_git_binding(
    repository: Path,
    record: Mapping[str, Any],
    current_head: str,
    current_records: Sequence[Mapping[str, Any]],
) -> None:
    if record.get("post_rollback_repository_head") != current_head:
        raise IntelligenceTransplantConflictError(
            "HOLD — ROLLBACK REPOSITORY BINDING IS STALE"
        )
    target_ref = {
        "object_id": record.get("target_object_id"),
        "content_hash": record.get("target_content_hash"),
    }
    target_e4 = next(
        (
            item
            for item in current_records
            if item.get("object_type") == E4_IMPLEMENTATION_BINDING
            and exact_ref(item) == target_ref
        ),
        None,
    )
    if target_e4 is None:
        raise IntelligenceTransplantValidationError(
            "Stage 5 rollback target E4 is unavailable."
        )
    target_head = target_e4.get("repository_head")
    if not isinstance(target_head, str):
        raise IntelligenceTransplantValidationError(
            "Stage 5 rollback target repository identity is invalid."
        )
    target_exists = _git_command(
        repository,
        "cat-file",
        "-e",
        f"{target_head}^{{commit}}",
    )
    post_exists = _git_command(
        repository,
        "cat-file",
        "-e",
        f"{current_head}^{{commit}}",
    )
    forward = _git_command(
        repository,
        "merge-base",
        "--is-ancestor",
        target_head,
        current_head,
    )
    changed = _git_command(
        repository,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--name-only",
        "--no-renames",
        "-z",
        target_head,
        current_head,
        "--",
    )
    if (
        target_exists.returncode != 0
        or post_exists.returncode != 0
        or forward.returncode != 0
        or changed.returncode != 0
    ):
        raise IntelligenceTransplantValidationError(
            "Stage 5 rollback is not a forward Git transition."
        )
    try:
        changed_paths = {
            item.decode("utf-8", errors="strict")
            for item in bytes(changed.stdout).split(b"\x00")
            if item
        }
    except UnicodeDecodeError as exc:
        raise IntelligenceTransplantValidationError(
            "Stage 5 rollback changed path is not UTF-8."
        ) from exc
    observed: set[str] = set()
    for artifact in record.get("rollback_changed_artifacts", ()):
        path = _safe_git_path(artifact.get("path"))
        if path in observed or path not in changed_paths:
            raise IntelligenceTransplantValidationError(
                "Stage 5 rollback artifact is not an exact changed path."
            )
        state = artifact.get("post_rollback_state")
        if state == "PRESENT":
            blob_id, blob_bytes = _git_blob_at(
                repository,
                current_head,
                path,
            )
            if (
                artifact.get("git_blob") != blob_id
                or artifact.get("sha256") != _sha256(blob_bytes)
            ):
                raise IntelligenceTransplantValidationError(
                    "Stage 5 rollback artifact Git identity is invalid."
                )
        elif state == "DELETED":
            deleted = _git_command(
                repository,
                "cat-file",
                "-e",
                f"{current_head}:{path}",
            )
            if (
                deleted.returncode == 0
                or artifact.get("git_blob") is not None
                or artifact.get("sha256") is not None
            ):
                raise IntelligenceTransplantValidationError(
                    "Stage 5 rollback deletion identity is invalid."
                )
        else:
            raise IntelligenceTransplantValidationError(
                "Stage 5 rollback artifact state is invalid."
            )
        observed.add(path)
    target_paths = {
        _safe_git_path(artifact.get("path"))
        for artifact in target_e4.get("changed_artifacts", ())
    }
    if observed != changed_paths or not target_paths.issubset(observed):
        raise IntelligenceTransplantValidationError(
            "Stage 5 rollback changed paths are not completely bound."
        )


def _verify_repository_record_binding(
    repository: Path,
    record: Mapping[str, Any],
    current_head: str,
    current_records: Sequence[Mapping[str, Any]],
) -> None:
    object_type = record.get("object_type")
    if object_type == RUN_CHARTER:
        if record.get("repository_head") != current_head:
            raise IntelligenceTransplantConflictError(
                "HOLD — RUN CHARTER REPOSITORY AS-OF STALE"
            )
    elif object_type == E4_IMPLEMENTATION_BINDING:
        _verify_e4_git_binding(repository, record, current_head)
    elif object_type == LOWER_RUN_TRIAL_MANIFEST:
        if record.get("repository_head") != current_head:
            raise IntelligenceTransplantConflictError(
                "HOLD — LOWER-RUN MANIFEST REPOSITORY AS-OF STALE"
            )
    elif (
        object_type == MANUAL_CONTROL_RECEIPT
        and record.get("control_action") == "ROLLBACK"
    ):
        _verify_rollback_git_binding(
            repository,
            record,
            current_head,
            current_records,
        )


def _transport_receipt(
    transport: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    if not isinstance(transport, Mapping) or set(transport) != {
        "payload",
        "transport_receipt",
    }:
        raise IntelligenceTransplantValidationError(
            "Stage 5 transport envelope is invalid."
        )
    payload = transport.get("payload")
    receipt = transport.get("transport_receipt")
    if not isinstance(payload, bytes) or not payload or not isinstance(receipt, Mapping):
        raise IntelligenceTransplantValidationError(
            "Stage 5 transport envelope is invalid."
        )
    value = deepcopy(dict(receipt))
    if not _transport_receipt_value_valid(value):
        raise IntelligenceTransplantValidationError(
            "Stage 5 transport receipt identity is invalid."
        )
    digest = _sha256(payload)
    if (
        value.get("exact_payload_sha256") != digest
        or value.get("declared_sha256") != digest
    ):
        raise IntelligenceTransplantValidationError(
            "Stage 5 transport receipt identity is invalid."
        )
    return payload, value


def _transport_receipt_value_valid(value: Any) -> bool:
    if not isinstance(value, Mapping) or set(value) != _TRANSPORT_FIELDS:
        return False
    try:
        normalized_as_of = _timestamp(value.get("as_of"))
    except IntelligenceTransplantValidationError:
        return False
    context_ref = value.get("context_evidence_ref")
    if context_ref is not None and (
        not isinstance(context_ref, Mapping)
        or set(context_ref) != {"content_hash", "object_id"}
        or not isinstance(context_ref.get("object_id"), str)
        or _SAFE_ID.fullmatch(context_ref["object_id"]) is None
        or not isinstance(context_ref.get("content_hash"), str)
        or _SHA256.fullmatch(context_ref["content_hash"]) is None
    ):
        return False
    body = {
        key: item
        for key, item in value.items()
        if key != "receipt_sha256"
    }
    return bool(
        value.get("schema_version") == TRANSPORT_SCHEMA
        and value.get("mode")
        in {"BYTE_EXACT_FILE_IMPORT", "PASTE_CAPTURE"}
        and isinstance(value.get("source_path_or_label"), str)
        and bool(value["source_path_or_label"])
        and "\n" not in value["source_path_or_label"]
        and "\r" not in value["source_path_or_label"]
        and "\x00" not in value["source_path_or_label"]
        and len(value["source_path_or_label"]) <= 1000
        and isinstance(value.get("exact_payload_sha256"), str)
        and _SHA256.fullmatch(value["exact_payload_sha256"]) is not None
        and isinstance(value.get("declared_sha256"), str)
        and value["declared_sha256"] == value["exact_payload_sha256"]
        and value.get("as_of") == normalized_as_of
        and isinstance(value.get("receipt_sha256"), str)
        and value["receipt_sha256"] == _sha256(canonical_json(body))
    )


class IntelligenceTransplantStore:
    """Private hash-chained Stage 5 state below one Git common directory."""

    _locks_guard = threading.Lock()
    _locks: dict[str, threading.RLock] = {}

    def __init__(self, repository: Path) -> None:
        self.repository = Path(repository).resolve()
        self.git_common_dir = _git_common_directory(self.repository)
        self.root = (
            self.git_common_dir
            / "decision-os"
            / "intelligence-transplant"
            / "v0.1"
        )
        self.events_path = self.root / "events.ndjson"
        self.event_head_path = self.root / "event-head.json"
        self.publication_state_path = self.root / "publication-state.json"
        with self._locks_guard:
            self._lock = self._locks.setdefault(
                str(self.root),
                threading.RLock(),
            )
        self._transaction_local = threading.local()

    @property
    def chain_head(self) -> str:
        events = self.read_events()
        return events[-1]["event_hash"] if events else GENESIS_EVENT_HASH

    def _directories(self) -> tuple[Path, ...]:
        return (
            self.git_common_dir / "decision-os",
            self.git_common_dir / "decision-os" / "intelligence-transplant",
            self.root,
            self.root / "charters",
            self.root / "charters" / "sha256",
            self.root / "evidence",
            self.root / "evidence" / "sha256",
            self.root / "manifests",
            self.root / "manifests" / "sha256",
            self.root / "transport",
            self.root / "transport" / "sha256",
        )

    def _assert_safe_path(self, target: Path) -> None:
        try:
            relative = target.relative_to(self.git_common_dir)
        except ValueError as exc:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            ) from exc
        current = self.git_common_dir
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
        nearest = target
        while not nearest.exists() and nearest != self.git_common_dir:
            nearest = nearest.parent
        try:
            nearest.resolve(strict=True).relative_to(self.git_common_dir)
        except (OSError, ValueError) as exc:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            ) from exc

    @staticmethod
    def _assert_open_private_file(descriptor: int) -> os.stat_result:
        try:
            metadata = os.fstat(descriptor)
        except OSError as exc:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            ) from exc
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            )
        return metadata

    @contextmanager
    def _directory_descriptor(self, directory: Path) -> Any:
        """Open a store directory without following intermediate symlinks."""

        self._assert_safe_path(directory)
        try:
            relative = directory.relative_to(self.git_common_dir)
        except ValueError as exc:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            ) from exc
        flags = os.O_RDONLY
        flags |= getattr(os, "O_DIRECTORY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor: int | None = None
        try:
            descriptor = os.open(self.git_common_dir, flags)
            common_metadata = os.fstat(descriptor)
            if (
                not stat.S_ISDIR(common_metadata.st_mode)
                or common_metadata.st_uid != os.getuid()
            ):
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
            for part in relative.parts:
                child = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
                metadata = os.fstat(descriptor)
                if (
                    not stat.S_ISDIR(metadata.st_mode)
                    or metadata.st_uid != os.getuid()
                    or stat.S_IMODE(metadata.st_mode) != 0o700
                ):
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
            yield descriptor
        except IntelligenceTransplantIntegrityError:
            raise
        except OSError as exc:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            ) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def _ensure_private_directory(self, directory: Path) -> None:
        self._assert_safe_path(directory)
        try:
            relative = directory.relative_to(self.git_common_dir)
        except ValueError as exc:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            ) from exc
        flags = os.O_RDONLY
        flags |= getattr(os, "O_DIRECTORY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor: int | None = None
        try:
            descriptor = os.open(self.git_common_dir, flags)
            for part in relative.parts:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                child = os.open(part, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
                os.fchmod(descriptor, 0o700)
                metadata = os.fstat(descriptor)
                if (
                    not stat.S_ISDIR(metadata.st_mode)
                    or metadata.st_uid != os.getuid()
                    or stat.S_IMODE(metadata.st_mode) != 0o700
                ):
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
        except IntelligenceTransplantIntegrityError:
            raise
        except OSError as exc:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            ) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def _read_private_bytes(self, target: Path) -> bytes:
        self._assert_safe_path(target)
        descriptor: int | None = None
        try:
            with self._directory_descriptor(target.parent) as parent:
                flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                descriptor = os.open(target.name, flags, dir_fd=parent)
                before = self._assert_open_private_file(descriptor)
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                after = self._assert_open_private_file(descriptor)
                if (
                    before.st_dev,
                    before.st_ino,
                    before.st_size,
                    before.st_mtime_ns,
                ) != (
                    after.st_dev,
                    after.st_ino,
                    after.st_size,
                    after.st_mtime_ns,
                ):
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
                return b"".join(chunks)
        except IntelligenceTransplantIntegrityError:
            raise
        except OSError as exc:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            ) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def _ensure_directories(self) -> None:
        for directory in self._directories():
            self._ensure_private_directory(directory)

    def _verify_directories(self) -> None:
        self._assert_safe_path(self.root)
        for directory in self._directories():
            self._assert_safe_path(directory)
            with self._directory_descriptor(directory):
                pass

    @contextmanager
    def transaction(
        self,
        *,
        write: bool = True,
        timeout_seconds: float = 5.0,
    ) -> Any:
        depth = getattr(self._transaction_local, "depth", 0)
        if depth:
            if write and not getattr(self._transaction_local, "write", False):
                raise IntelligenceTransplantConflictError(
                    "A read-only Stage 5 transaction cannot be upgraded."
                )
            self._transaction_local.depth = depth + 1
            try:
                yield
            finally:
                self._transaction_local.depth -= 1
            return
        descriptor: int | None = None
        with self._lock:
            if write:
                self._ensure_directories()
            elif not self.root.exists():
                yield
                return
            else:
                self._verify_directories()
            lock_path = self.root / ".transaction.lock"
            if not write and not lock_path.exists():
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
            self._assert_safe_path(lock_path)
            flags = os.O_RDWR | os.O_CREAT if write else os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                with self._directory_descriptor(self.root) as parent:
                    descriptor = os.open(
                        lock_path.name,
                        flags,
                        0o600,
                        dir_fd=parent,
                    )
                if write:
                    os.fchmod(descriptor, 0o600)
                self._assert_open_private_file(descriptor)
            except IntelligenceTransplantIntegrityError:
                if descriptor is not None:
                    os.close(descriptor)
                raise
            except OSError as exc:
                if descriptor is not None:
                    os.close(descriptor)
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                ) from exc
        lock_mode = fcntl.LOCK_EX if write else fcntl.LOCK_SH
        deadline = time.monotonic() + timeout_seconds
        try:
            while True:
                try:
                    fcntl.flock(descriptor, lock_mode | fcntl.LOCK_NB)
                    break
                except BlockingIOError as exc:
                    if time.monotonic() >= deadline:
                        raise IntelligenceTransplantBusyError(
                            "Intelligence Transplant is temporarily busy."
                        ) from exc
                    time.sleep(0.01)
            with self._lock:
                self._transaction_local.depth = 1
                self._transaction_local.write = write
                try:
                    yield
                finally:
                    self._transaction_local.depth = 0
                    self._transaction_local.write = False
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

    def _atomic_write(
        self,
        target: Path,
        payload: bytes,
        *,
        immutable: bool = True,
    ) -> None:
        self._ensure_directories()
        self._assert_safe_path(target)
        if target.exists():
            current = self._read_private_bytes(target)
            if immutable and current != payload:
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
            if immutable:
                return
        temporary = target.parent / f".stage5-{uuid.uuid4().hex}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            with self._directory_descriptor(target.parent) as parent:
                descriptor = os.open(
                    temporary.name,
                    flags,
                    0o600,
                    dir_fd=parent,
                )
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                descriptor = None
                os.replace(
                    temporary.name,
                    target.name,
                    src_dir_fd=parent,
                    dst_dir_fd=parent,
                )
                os.fsync(parent)
                verified = os.open(
                    target.name,
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=parent,
                )
                try:
                    os.fchmod(verified, 0o600)
                    self._assert_open_private_file(verified)
                finally:
                    os.close(verified)
        except Exception:
            try:
                with self._directory_descriptor(target.parent) as parent:
                    os.unlink(temporary.name, dir_fd=parent)
            except (FileNotFoundError, IntelligenceTransplantIntegrityError):
                pass
            raise

    def _record_path(self, blob_kind: str, digest: str) -> Path:
        directory = _BLOB_DIRECTORIES.get(blob_kind)
        if directory is None or _SHA256.fullmatch(digest) is None:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            )
        return self.root / directory / "sha256" / f"{digest}.json"

    def _transport_path(self, digest: str) -> Path:
        if _SHA256.fullmatch(digest) is None:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            )
        return self.root / "transport" / "sha256" / f"{digest}.bin"

    def _transport_receipt_path(self, digest: str) -> Path:
        if _SHA256.fullmatch(digest) is None:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            )
        return (
            self.root
            / "transport"
            / "sha256"
            / f"{digest}.receipt.json"
        )

    def store_record(
        self,
        blob_kind: str,
        record: Mapping[str, Any],
    ) -> str:
        with self.transaction():
            value = deepcopy(dict(record))
            digest = value.get("content_hash")
            if (
                not isinstance(digest, str)
                or _SHA256.fullmatch(digest) is None
                or compute_content_hash(value) != digest
            ):
                raise IntelligenceTransplantValidationError(
                    "Stage 5 object content hash is invalid."
                )
            self._atomic_write(
                self._record_path(blob_kind, digest),
                canonical_json(value),
            )
            return digest

    def read_record(self, blob_kind: str, digest: str) -> dict[str, Any]:
        with self.transaction(write=False):
            target = self._record_path(blob_kind, digest)
            self._assert_safe_path(target)
            try:
                raw = self._read_private_bytes(target)
                record = strict_json_object(raw)
            except Exception as exc:
                if isinstance(exc, IntelligenceTransplantIntegrityError):
                    raise
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                ) from exc
            try:
                actual = compute_content_hash(record)
            except Exception as exc:
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                ) from exc
            if (
                canonical_json(record) != raw
                or record.get("content_hash") != digest
                or actual != digest
            ):
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
            return record

    def store_transport(self, payload: bytes, digest: str) -> None:
        with self.transaction():
            if _sha256(payload) != digest:
                raise IntelligenceTransplantValidationError(
                    "Stage 5 transport hash is invalid."
                )
            self._atomic_write(self._transport_path(digest), payload)

    def read_transport(self, digest: str) -> bytes:
        with self.transaction(write=False):
            target = self._transport_path(digest)
            self._assert_safe_path(target)
            try:
                payload = self._read_private_bytes(target)
            except OSError as exc:
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                ) from exc
            if _sha256(payload) != digest:
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
            return payload

    def store_transport_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> str:
        with self.transaction():
            value = deepcopy(dict(receipt))
            if not _transport_receipt_value_valid(value):
                raise IntelligenceTransplantValidationError(
                    "Stage 5 transport receipt identity is invalid."
                )
            digest = value["receipt_sha256"]
            self._atomic_write(
                self._transport_receipt_path(digest),
                canonical_json(value),
            )
            return digest

    def read_transport_receipt(self, digest: str) -> dict[str, Any]:
        with self.transaction(write=False):
            target = self._transport_receipt_path(digest)
            try:
                raw = self._read_private_bytes(target)
                value = strict_json_object(raw)
            except Exception as exc:
                if isinstance(exc, IntelligenceTransplantIntegrityError):
                    raise
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                ) from exc
            if (
                canonical_json(value) != raw
                or value.get("receipt_sha256") != digest
                or not _transport_receipt_value_valid(value)
            ):
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
            return value

    def _write_event_head(self, *, event_count: int, event_chain_head: str) -> None:
        body = {
            "event_chain_head": event_chain_head,
            "event_count": event_count,
            "schema_version": STORE_SCHEMA,
        }
        anchor = {
            **body,
            "head_sha256": _sha256(canonical_json(body)),
        }
        self._atomic_write(
            self.event_head_path,
            canonical_json(anchor),
            immutable=False,
        )

    @staticmethod
    def _publication_state(
        *,
        event_count: int,
        event_chain_head: str,
        expected_repository_head: str,
        observed_repository_head: str | None,
        status: str,
    ) -> dict[str, Any]:
        body = {
            "event_chain_head": event_chain_head,
            "event_count": event_count,
            "expected_repository_head": expected_repository_head,
            "observed_repository_head": observed_repository_head,
            "publication_status": status,
            "schema_version": STORE_SCHEMA,
        }
        return {
            **body,
            "state_sha256": _sha256(canonical_json(body)),
        }

    def _write_publication_state(
        self,
        *,
        event_count: int,
        event_chain_head: str,
        expected_repository_head: str,
        observed_repository_head: str | None,
        status: str,
    ) -> None:
        state = self._publication_state(
            event_count=event_count,
            event_chain_head=event_chain_head,
            expected_repository_head=expected_repository_head,
            observed_repository_head=observed_repository_head,
            status=status,
        )
        self._atomic_write(
            self.publication_state_path,
            canonical_json(state),
            immutable=False,
        )

    def _clear_publication_state(self) -> None:
        self._assert_safe_path(self.publication_state_path)
        try:
            with self._directory_descriptor(self.root) as parent:
                descriptor = os.open(
                    self.publication_state_path.name,
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=parent,
                )
                try:
                    self._assert_open_private_file(descriptor)
                finally:
                    os.close(descriptor)
                os.unlink(self.publication_state_path.name, dir_fd=parent)
                os.fsync(parent)
        except IntelligenceTransplantIntegrityError:
            raise
        except OSError as exc:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 PUBLICATION INVALID"
            ) from exc

    def _invalidate_publication(
        self,
        *,
        event_count: int,
        event_chain_head: str,
        expected_repository_head: str,
        observed_repository_head: str | None,
    ) -> None:
        state = self._publication_state(
            event_count=event_count,
            event_chain_head=event_chain_head,
            expected_repository_head=expected_repository_head,
            observed_repository_head=observed_repository_head,
            status="INVALID",
        )
        try:
            self._atomic_write(
                self.publication_state_path,
                canonical_json(state),
                immutable=False,
            )
        finally:
            self._atomic_write(
                self.event_head_path,
                canonical_json(state),
                immutable=False,
            )

    def _assert_publication_ready(self) -> None:
        if os.path.lexists(self.publication_state_path):
            self._assert_safe_path(self.publication_state_path)
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 PUBLICATION INVALID"
            )

    def _read_event_head(self) -> dict[str, Any]:
        self._assert_safe_path(self.event_head_path)
        try:
            raw = self._read_private_bytes(self.event_head_path)
            anchor = strict_json_object(raw)
        except Exception as exc:
            if isinstance(exc, IntelligenceTransplantIntegrityError):
                raise
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            ) from exc
        if anchor.get("publication_status") in {"IN_PROGRESS", "INVALID"}:
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 PUBLICATION INVALID"
            )
        body = {
            key: value
            for key, value in anchor.items()
            if key != "head_sha256"
        }
        if (
            set(anchor) != _HEAD_FIELDS
            or canonical_json(anchor) != raw
            or anchor.get("schema_version") != STORE_SCHEMA
            or not isinstance(anchor.get("event_count"), int)
            or isinstance(anchor.get("event_count"), bool)
            or anchor["event_count"] < 1
            or not isinstance(anchor.get("event_chain_head"), str)
            or _SHA256.fullmatch(anchor["event_chain_head"]) is None
            or anchor.get("head_sha256") != _sha256(canonical_json(body))
        ):
            raise IntelligenceTransplantIntegrityError(
                "HOLD — STAGE 5 STORE CORRUPT"
            )
        return anchor

    @staticmethod
    def _event_shape_valid(event: Any) -> bool:
        if not isinstance(event, dict) or set(event) != _EVENT_FIELDS:
            return False
        payload = event.get("payload")
        return bool(
            event.get("schema_version") == STORE_SCHEMA
            and isinstance(event.get("event_id"), str)
            and _SAFE_ID.fullmatch(event["event_id"]) is not None
            and event.get("kind") in EVENT_KINDS
            and isinstance(event.get("recorded_at"), str)
            and isinstance(event.get("event_hash"), str)
            and _SHA256.fullmatch(event["event_hash"]) is not None
            and isinstance(event.get("previous_event_hash"), str)
            and _SHA256.fullmatch(event["previous_event_hash"]) is not None
            and isinstance(payload, dict)
            and set(payload) == _EVENT_PAYLOAD_FIELDS
            and isinstance(payload.get("object_id"), str)
            and _SAFE_ID.fullmatch(payload["object_id"]) is not None
            and isinstance(payload.get("object_type"), str)
            and isinstance(payload.get("content_hash"), str)
            and _SHA256.fullmatch(payload["content_hash"]) is not None
            and payload.get("blob_kind") in _BLOB_DIRECTORIES
            and isinstance(payload.get("repository_head"), str)
            and _COMMIT.fullmatch(payload["repository_head"]) is not None
        )

    @staticmethod
    def _event_category_valid(event: Mapping[str, Any]) -> bool:
        kind = event["kind"]
        payload = event["payload"]
        object_type = payload["object_type"]
        blob_kind = payload["blob_kind"]
        receipt = payload["transport_receipt"]
        transport_sha = payload["transport_sha256"]
        if kind == "CHARTER_FROZEN":
            return bool(
                object_type == RUN_CHARTER
                and blob_kind == "charter"
                and receipt is None
                and transport_sha is None
            )
        if (
            receipt is None
            or not isinstance(transport_sha, str)
            or _SHA256.fullmatch(transport_sha) is None
        ):
            return False
        if kind == "MANIFEST_FROZEN":
            return object_type in _MANIFEST_TYPES and blob_kind == "manifest"
        if kind == "CONTROL_RECORDED":
            return object_type == MANUAL_CONTROL_RECEIPT and blob_kind == "evidence"
        return (
            kind == "OBJECT_ATTACHED"
            and object_type in _EVIDENCE_TYPES
            and blob_kind == "evidence"
        )

    def read_events(
        self,
        *,
        staged_payload: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Read and verify the complete event, record, and transport chain."""

        with self.transaction(write=False):
            if not self.root.exists():
                return []
            self._assert_publication_ready()
            try:
                _assert_raw_git_evidence_mode(self.repository)
            except (
                IntelligenceTransplantConflictError,
                IntelligenceTransplantValidationError,
            ) as exc:
                raise IntelligenceTransplantIntegrityError(str(exc)) from exc
            if not self.events_path.exists():
                if self.event_head_path.exists():
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
                blob_directories = (
                    self.root / "charters" / "sha256",
                    self.root / "evidence" / "sha256",
                    self.root / "manifests" / "sha256",
                    self.root / "transport" / "sha256",
                )
                observed_blobs = {
                    target
                    for directory in blob_directories
                    for target in directory.iterdir()
                }
                permitted_blobs: set[Path] = set()
                if staged_payload is not None:
                    try:
                        permitted_blobs.add(
                            self._record_path(
                                str(staged_payload["blob_kind"]),
                                str(staged_payload["content_hash"]),
                            )
                        )
                        transport_sha = staged_payload.get(
                            "transport_sha256"
                        )
                        if isinstance(transport_sha, str):
                            permitted_blobs.add(
                                self._transport_path(transport_sha)
                            )
                        transport_receipt = staged_payload.get(
                            "transport_receipt"
                        )
                        if isinstance(transport_receipt, Mapping):
                            permitted_blobs.add(
                                self._transport_receipt_path(
                                    str(
                                        transport_receipt.get(
                                            "receipt_sha256"
                                        )
                                    )
                                )
                            )
                    except (KeyError, TypeError) as exc:
                        raise IntelligenceTransplantIntegrityError(
                            "HOLD — STAGE 5 STORE CORRUPT"
                        ) from exc
                if observed_blobs != permitted_blobs:
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
                return []
            if not self.event_head_path.exists():
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
            self._verify_directories()
            self._assert_safe_path(self.events_path)
            try:
                raw = self._read_private_bytes(self.events_path)
            except OSError as exc:
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                ) from exc
            if not raw or not raw.endswith(b"\n"):
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
            events: list[dict[str, Any]] = []
            event_ids: set[str] = set()
            previous = GENESIS_EVENT_HASH
            known_refs: set[tuple[str, str]] = set()
            verified_records: list[dict[str, Any]] = []
            for raw_line in raw.splitlines():
                if not raw_line:
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
                try:
                    event = strict_json_object(raw_line)
                except Exception as exc:
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    ) from exc
                if (
                    not self._event_shape_valid(event)
                    or not self._event_category_valid(event)
                    or event["event_id"] in event_ids
                    or canonical_json(event) != raw_line
                ):
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
                try:
                    recorded_at = _timestamp(event["recorded_at"])
                except IntelligenceTransplantValidationError as exc:
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    ) from exc
                body = {
                    key: value
                    for key, value in event.items()
                    if key != "event_hash"
                }
                if (
                    recorded_at != event["recorded_at"]
                    or event["previous_event_hash"] != previous
                    or event["event_hash"] != _sha256(canonical_json(body))
                ):
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
                payload = event["payload"]
                record = self.read_record(
                    payload["blob_kind"],
                    payload["content_hash"],
                )
                if (
                    record.get("object_id") != payload["object_id"]
                    or record.get("object_type") != payload["object_type"]
                ):
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
                try:
                    expected_event_id = _event_id_for_content_hash(
                        record["content_hash"]
                    )
                    record_as_of = _timestamp(record.get("as_of"))
                except (
                    KeyError,
                    IntelligenceTransplantValidationError,
                ) as exc:
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    ) from exc
                if (
                    event["event_id"] != expected_event_id
                    or event["recorded_at"] != record_as_of
                ):
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
                try:
                    bound_commit = _git_command(
                        self.repository,
                        "cat-file",
                        "-e",
                        f"{payload['repository_head']}^{{commit}}",
                    )
                except IntelligenceTransplantConflictError as exc:
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    ) from exc
                if bound_commit.returncode != 0:
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
                record_repository_head = None
                if record.get("object_type") in {
                    RUN_CHARTER,
                    E4_IMPLEMENTATION_BINDING,
                    LOWER_RUN_TRIAL_MANIFEST,
                }:
                    record_repository_head = record.get("repository_head")
                elif (
                    record.get("object_type") == MANUAL_CONTROL_RECEIPT
                    and record.get("control_action") == "ROLLBACK"
                ):
                    record_repository_head = record.get(
                        "post_rollback_repository_head"
                    )
                if (
                    record_repository_head is not None
                    and record_repository_head != payload["repository_head"]
                ):
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
                receipt = payload["transport_receipt"]
                if receipt is not None:
                    stored_receipt = self.read_transport_receipt(
                        receipt["receipt_sha256"]
                    )
                    transport_bytes = self.read_transport(
                        payload["transport_sha256"]
                    )
                    try:
                        verified_payload, verified_receipt = _transport_receipt(
                            {
                                "payload": transport_bytes,
                                "transport_receipt": receipt,
                            }
                        )
                        transported_record = strict_json_object(verified_payload)
                    except Exception as exc:
                        raise IntelligenceTransplantIntegrityError(
                            "HOLD — STAGE 5 STORE CORRUPT"
                        ) from exc
                    if (
                        stored_receipt != receipt
                        or verified_receipt != receipt
                        or transported_record != record
                    ):
                        raise IntelligenceTransplantIntegrityError(
                            "HOLD — STAGE 5 STORE CORRUPT"
                        )
                    context_ref = receipt["context_evidence_ref"]
                    if context_ref is not None and (
                        context_ref["object_id"],
                        context_ref["content_hash"],
                    ) not in known_refs:
                        raise IntelligenceTransplantIntegrityError(
                            "HOLD — STAGE 5 STORE CORRUPT"
                        )
                    if (
                        context_ref is None
                        and record.get("object_type")
                        != "SEAT_ASSIGNMENT_RECEIPT"
                    ):
                        raise IntelligenceTransplantIntegrityError(
                            "HOLD — STAGE 5 STORE CORRUPT"
                        )
                try:
                    if record.get("object_type") == E4_IMPLEMENTATION_BINDING:
                        _verify_e4_git_binding(
                            self.repository,
                            record,
                            str(record.get("repository_head")),
                        )
                    elif (
                        record.get("object_type") == MANUAL_CONTROL_RECEIPT
                        and record.get("control_action") == "ROLLBACK"
                    ):
                        _verify_rollback_git_binding(
                            self.repository,
                            record,
                            str(
                                record.get(
                                    "post_rollback_repository_head"
                                )
                            ),
                            verified_records,
                        )
                except (
                    IntelligenceTransplantConflictError,
                    IntelligenceTransplantValidationError,
                ) as exc:
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 GIT EVIDENCE INVALID"
                    ) from exc
                previous = event["event_hash"]
                event_ids.add(event["event_id"])
                known_refs.add(
                    (record["object_id"], record["content_hash"])
                )
                verified_records.append(record)
                events.append(event)
            anchor = self._read_event_head()
            if (
                anchor["event_count"] != len(events)
                or anchor["event_chain_head"] != events[-1]["event_hash"]
            ):
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
            try:
                _assert_raw_git_evidence_mode(self.repository)
            except (
                IntelligenceTransplantConflictError,
                IntelligenceTransplantValidationError,
            ) as exc:
                raise IntelligenceTransplantIntegrityError(str(exc)) from exc
            return events

    def read_records(self) -> list[dict[str, Any]]:
        with self.transaction(write=False):
            return [
                self.read_record(
                    event["payload"]["blob_kind"],
                    event["payload"]["content_hash"],
                )
                for event in self.read_events()
            ]

    def append_event(
        self,
        *,
        event_id: str,
        kind: str,
        recorded_at: str,
        payload: Mapping[str, Any],
        expected_previous_event_hash: str,
        expected_repository_head: str,
    ) -> dict[str, Any]:
        with self.transaction():
            if (
                not isinstance(event_id, str)
                or _SAFE_ID.fullmatch(event_id) is None
                or kind not in EVENT_KINDS
                or not isinstance(payload, Mapping)
                or set(payload) != _EVENT_PAYLOAD_FIELDS
                or not isinstance(expected_repository_head, str)
                or _COMMIT.fullmatch(expected_repository_head) is None
            ):
                raise IntelligenceTransplantValidationError(
                    "Stage 5 event is invalid."
                )
            events = self.read_events(staged_payload=payload)
            previous = (
                events[-1]["event_hash"] if events else GENESIS_EVENT_HASH
            )
            if previous != expected_previous_event_hash:
                raise IntelligenceTransplantConflictError(
                    "HOLD — STAGE 5 EVENT HEAD CHANGED"
                )
            if any(event["event_id"] == event_id for event in events):
                raise IntelligenceTransplantConflictError(
                    "HOLD — STAGE 5 EVENT ID ALREADY EXISTS"
                )
            body = {
                "event_id": event_id,
                "kind": kind,
                "payload": deepcopy(dict(payload)),
                "previous_event_hash": previous,
                "recorded_at": _timestamp(recorded_at),
                "schema_version": STORE_SCHEMA,
            }
            event = {
                **body,
                "event_hash": _sha256(canonical_json(body)),
            }
            if (
                not self._event_shape_valid(event)
                or not self._event_category_valid(event)
            ):
                raise IntelligenceTransplantValidationError(
                    "Stage 5 event category is invalid."
                )
            candidate_record = self.read_record(
                event["payload"]["blob_kind"],
                event["payload"]["content_hash"],
            )
            if (
                candidate_record.get("object_id")
                != event["payload"]["object_id"]
                or candidate_record.get("object_type")
                != event["payload"]["object_type"]
            ):
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 STORE CORRUPT"
                )
            candidate_receipt = event["payload"]["transport_receipt"]
            if candidate_receipt is not None:
                stored_candidate_receipt = self.read_transport_receipt(
                    candidate_receipt["receipt_sha256"]
                )
                candidate_transport = self.read_transport(
                    event["payload"]["transport_sha256"]
                )
                try:
                    verified_payload, verified_receipt = _transport_receipt(
                        {
                            "payload": candidate_transport,
                            "transport_receipt": candidate_receipt,
                        }
                    )
                    transported_record = strict_json_object(verified_payload)
                except Exception as exc:
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    ) from exc
                if (
                    stored_candidate_receipt != candidate_receipt
                    or
                    verified_receipt != candidate_receipt
                    or transported_record != candidate_record
                ):
                    raise IntelligenceTransplantIntegrityError(
                        "HOLD — STAGE 5 STORE CORRUPT"
                    )
            if _repository_head(self.repository) != expected_repository_head:
                raise IntelligenceTransplantConflictError(
                    "HOLD — STAGE 5 APPEND INPUT CHANGED"
                )
            event_count = len(events) + 1
            self._write_publication_state(
                event_count=event_count,
                event_chain_head=event["event_hash"],
                expected_repository_head=expected_repository_head,
                observed_repository_head=None,
                status="IN_PROGRESS",
            )
            self._ensure_directories()
            self._assert_safe_path(self.events_path)
            flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            event_appended = False
            try:
                with self._directory_descriptor(self.root) as parent:
                    descriptor = os.open(
                        self.events_path.name,
                        flags,
                        0o600,
                        dir_fd=parent,
                    )
                    os.fchmod(descriptor, 0o600)
                    self._assert_open_private_file(descriptor)
                    with os.fdopen(descriptor, "ab") as stream:
                        stream.write(canonical_json(event) + b"\n")
                        stream.flush()
                        os.fsync(stream.fileno())
                    descriptor = None
                event_appended = True
                self._write_event_head(
                    event_count=event_count,
                    event_chain_head=event["event_hash"],
                )
            except Exception as exc:
                if event_appended:
                    try:
                        self._invalidate_publication(
                            event_count=event_count,
                            event_chain_head=event["event_hash"],
                            expected_repository_head=(
                                expected_repository_head
                            ),
                            observed_repository_head=None,
                        )
                    except Exception:
                        pass
                if isinstance(exc, IntelligenceTransplantError):
                    raise
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 EVENT APPEND FAILED"
                ) from exc
            try:
                observed_repository_head = _repository_head(
                    self.repository
                )
            except IntelligenceTransplantError as exc:
                try:
                    self._invalidate_publication(
                        event_count=event_count,
                        event_chain_head=event["event_hash"],
                        expected_repository_head=expected_repository_head,
                        observed_repository_head=None,
                    )
                except Exception:
                    pass
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 PUBLICATION INVALID"
                ) from exc
            if observed_repository_head != expected_repository_head:
                try:
                    self._invalidate_publication(
                        event_count=event_count,
                        event_chain_head=event["event_hash"],
                        expected_repository_head=expected_repository_head,
                        observed_repository_head=observed_repository_head,
                    )
                except Exception:
                    pass
                raise IntelligenceTransplantIntegrityError(
                    "HOLD — STAGE 5 PUBLICATION INVALID"
                )
            try:
                self._clear_publication_state()
            except IntelligenceTransplantError:
                try:
                    self._invalidate_publication(
                        event_count=event_count,
                        event_chain_head=event["event_hash"],
                        expected_repository_head=expected_repository_head,
                        observed_repository_head=observed_repository_head,
                    )
                except Exception:
                    pass
                raise
            return event


def _lineage(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    lineage: list[dict[str, Any]] = []
    for record in records:
        refs: list[dict[str, str]] = []
        for key, value in record.items():
            if key.endswith("_ref") and isinstance(value, Mapping):
                if set(value) == {"content_hash", "object_id"}:
                    refs.append(dict(value))
            elif key in {"input_refs", "release_evidence_refs"} and isinstance(
                value,
                list,
            ):
                refs.extend(
                    dict(item)
                    for item in value
                    if isinstance(item, Mapping)
                    and set(item) == {"content_hash", "object_id"}
                )
        trace = record.get("asset_activation_trace")
        if isinstance(trace, Mapping):
            nested = trace.get("e4_ref")
            if (
                isinstance(nested, Mapping)
                and set(nested) == {"content_hash", "object_id"}
            ):
                refs.append(dict(nested))
        if record.get("object_type") == MANUAL_CONTROL_RECEIPT:
            target_id = record.get("target_object_id")
            target_hash = record.get("target_content_hash")
            if isinstance(target_id, str) and isinstance(target_hash, str):
                refs.append(
                    {"object_id": target_id, "content_hash": target_hash}
                )
        unique: list[dict[str, str]] = []
        for reference in refs:
            if reference not in unique:
                unique.append(reference)
        lineage.append(
            {
                "object_ref": exact_ref(record),
                "object_type": record["object_type"],
                "source_refs": unique,
                "supersedes": deepcopy(record.get("supersedes")),
            }
        )
    return lineage


class IntelligenceTransplantController:
    """Validate, persist, and project one repository-local Stage 5 graph."""

    def __init__(
        self,
        repository: Path,
        *,
        clock: Callable[[], datetime | str] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.repository = Path(repository).resolve()
        self.store = IntelligenceTransplantStore(self.repository)
        self._clock = clock or _now_utc
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))

    def _now(self) -> str:
        return _timestamp(self._clock())

    @staticmethod
    def _new_event_id(record: Mapping[str, Any]) -> str:
        return _event_id_for_content_hash(str(record.get("content_hash")))

    @staticmethod
    def _raise_invalid(
        assessment: Any,
        *,
        existing: bool = False,
    ) -> None:
        error_type = (
            IntelligenceTransplantIntegrityError
            if existing
            else IntelligenceTransplantValidationError
        )
        issues = ", ".join(assessment.issue_codes) or "UNKNOWN"
        raise error_type(f"Stage 5 structural validation failed: {issues}")

    def _current_records_for_write(self) -> list[dict[str, Any]]:
        records = self.store.read_records()
        if records:
            assessment = validate_graph(records, now=self._now())
            if not assessment.valid:
                self._raise_invalid(assessment, existing=True)
        return records

    @staticmethod
    def _validate_candidate(
        record: Mapping[str, Any],
        current: Sequence[Mapping[str, Any]],
        *,
        now: str,
    ) -> dict[str, Any]:
        value = deepcopy(dict(record))
        local = validate_object(value, now=now)
        if not local.valid:
            IntelligenceTransplantController._raise_invalid(local)
        proposed = [*current, value]
        graph = validate_graph(proposed, now=now)
        if not graph.valid:
            IntelligenceTransplantController._raise_invalid(graph)
        return value

    @staticmethod
    def _validate_context_ref(
        record: Mapping[str, Any],
        receipt: Mapping[str, Any],
        current: Sequence[Mapping[str, Any]],
        *,
        now: str,
    ) -> None:
        try:
            record_as_of = datetime.fromisoformat(
                _timestamp(record.get("as_of")).replace("Z", "+00:00")
            )
            receipt_as_of = datetime.fromisoformat(
                _timestamp(receipt.get("as_of")).replace("Z", "+00:00")
            )
            event_as_of = datetime.fromisoformat(
                _timestamp(now).replace("Z", "+00:00")
            )
        except IntelligenceTransplantValidationError:
            raise
        if not (record_as_of <= receipt_as_of <= event_as_of):
            raise IntelligenceTransplantValidationError(
                "Stage 5 transport as_of is outside the record/event window."
            )
        reference = receipt.get("context_evidence_ref")
        if reference is None:
            if record.get("object_type") != "SEAT_ASSIGNMENT_RECEIPT":
                raise IntelligenceTransplantValidationError(
                    "Stage 5 context evidence reference is required."
                )
            return
        referenced = next(
            (item for item in current if exact_ref(item) == reference),
            None,
        )
        superseded_refs = {
            (
                item["supersedes"]["object_id"],
                item["supersedes"]["content_hash"],
            )
            for item in current
            if isinstance(item.get("supersedes"), Mapping)
            and set(item["supersedes"]) == {"content_hash", "object_id"}
        }
        revoked_refs = {
            (
                item.get("target_object_id"),
                item.get("target_content_hash"),
            )
            for item in current
            if item.get("object_type") == MANUAL_CONTROL_RECEIPT
            and item.get("control_action") in {"REVOKE", "ROLLBACK"}
        }
        reference_key = (
            reference.get("object_id"),
            reference.get("content_hash"),
        )
        if (
            referenced is None
            or reference_key in superseded_refs
            or reference_key in revoked_refs
        ):
            raise IntelligenceTransplantValidationError(
                "Stage 5 context evidence reference is not current."
            )

    def _attach(
        self,
        record: Mapping[str, Any],
        *,
        event_kind: str,
        blob_kind: str,
        transport: Mapping[str, Any] | None,
        repository_head: str | None,
    ) -> dict[str, Any]:
        with self.store.transaction():
            now = self._now()
            opening_head = _repository_head(self.repository)
            if (
                repository_head is not None
                and repository_head != opening_head
            ):
                raise IntelligenceTransplantConflictError(
                    "HOLD — STAGE 5 REPOSITORY AS-OF STALE"
                )
            current = self._current_records_for_write()
            value = self._validate_candidate(record, current, now=now)
            _verify_repository_record_binding(
                self.repository,
                value,
                opening_head,
                current,
            )
            payload_bytes: bytes | None = None
            receipt: dict[str, Any] | None = None
            transport_sha256: str | None = None
            if transport is not None:
                payload_bytes, receipt = _transport_receipt(transport)
                try:
                    transported = strict_json_object(payload_bytes)
                except Exception as exc:
                    raise IntelligenceTransplantValidationError(
                        "Stage 5 transport must contain one strict JSON object."
                    ) from exc
                if transported != value:
                    raise IntelligenceTransplantValidationError(
                        "Stage 5 transport bytes do not match the submitted object."
                    )
                self._validate_context_ref(
                    value,
                    receipt,
                    current,
                    now=now,
                )
                transport_sha256 = receipt["exact_payload_sha256"]
            elif event_kind != "CHARTER_FROZEN":
                raise IntelligenceTransplantValidationError(
                    "Stage 5 manual transport receipt is required."
                )
            event_head = self.store.chain_head
            self.store.store_record(blob_kind, value)
            if payload_bytes is not None and transport_sha256 is not None:
                self.store.store_transport(payload_bytes, transport_sha256)
                assert receipt is not None
                self.store.store_transport_receipt(receipt)
            self.store.append_event(
                event_id=self._new_event_id(value),
                kind=event_kind,
                recorded_at=str(value["as_of"]),
                payload={
                    "blob_kind": blob_kind,
                    "content_hash": value["content_hash"],
                    "object_id": value["object_id"],
                    "object_type": value["object_type"],
                    "repository_head": opening_head,
                    "transport_receipt": receipt,
                    "transport_sha256": transport_sha256,
                },
                expected_previous_event_hash=event_head,
                expected_repository_head=opening_head,
            )
            return self.snapshot()

    def freeze_charter(
        self,
        record: Mapping[str, Any],
        *,
        charter_source: Mapping[str, Any],
        repository_head: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(charter_source, Mapping) or set(charter_source) != {
            "completion_line",
            "freeze_id",
            "frozen_intake_sha256",
            "repository_head",
        }:
            raise IntelligenceTransplantValidationError(
                "Guided Intake Charter source is invalid."
            )
        expected = {
            "completion_line": charter_source["completion_line"],
            "repository_head": charter_source["repository_head"],
            "source_freeze_id": charter_source["freeze_id"],
            "source_freeze_sha256": charter_source[
                "frozen_intake_sha256"
            ],
        }
        if any(record.get(key) != value for key, value in expected.items()):
            raise IntelligenceTransplantValidationError(
                "Run Charter does not match the current Guided Intake freeze."
            )
        return self._attach(
            record,
            event_kind="CHARTER_FROZEN",
            blob_kind="charter",
            transport=None,
            repository_head=repository_head,
        )

    def freeze_manifest(
        self,
        record: Mapping[str, Any],
        *,
        transport: Mapping[str, Any],
        repository_head: str | None = None,
    ) -> dict[str, Any]:
        if record.get("object_type") not in _MANIFEST_TYPES:
            raise IntelligenceTransplantValidationError(
                "Stage 5 manifest route received the wrong object type."
            )
        return self._attach(
            record,
            event_kind="MANIFEST_FROZEN",
            blob_kind="manifest",
            transport=transport,
            repository_head=repository_head,
        )

    def attach_object(
        self,
        record: Mapping[str, Any],
        *,
        transport: Mapping[str, Any],
        repository_head: str | None = None,
    ) -> dict[str, Any]:
        if record.get("object_type") not in _EVIDENCE_TYPES:
            raise IntelligenceTransplantValidationError(
                "Stage 5 object route received the wrong object type."
            )
        return self._attach(
            record,
            event_kind="OBJECT_ATTACHED",
            blob_kind="evidence",
            transport=transport,
            repository_head=repository_head,
        )

    def record_control(
        self,
        record: Mapping[str, Any],
        *,
        transport: Mapping[str, Any],
        repository_head: str | None = None,
    ) -> dict[str, Any]:
        if record.get("object_type") != MANUAL_CONTROL_RECEIPT:
            raise IntelligenceTransplantValidationError(
                "Stage 5 control route received the wrong object type."
            )
        return self._attach(
            record,
            event_kind="CONTROL_RECORDED",
            blob_kind="evidence",
            transport=transport,
            repository_head=repository_head,
        )

    def snapshot(self) -> dict[str, Any]:
        with self.store.transaction(
            write=False,
            timeout_seconds=0.05,
        ):
            records = self.store.read_records()
            projection = reduce_evidence_graph(
                records,
                now=self._now(),
            ).as_dict()
            projection.update(
                {
                    "error": None,
                    "event_chain_head": self.store.chain_head,
                    "lineage": _lineage(records),
                    "store_state": "READY" if records else "EMPTY",
                }
            )
            return projection

    def projection_run(self, run_id: str | None = None) -> dict[str, Any]:
        projection = self.snapshot()
        if (
            run_id is not None
            and projection["run_id"] not in {run_id, "UNKNOWN"}
        ):
            raise IntelligenceTransplantConflictError(
                "Requested Stage 5 run is not current."
            )
        return projection
