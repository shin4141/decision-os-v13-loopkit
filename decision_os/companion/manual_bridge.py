"""Exact, non-authoritative artifact bridge for the private Companion.

The Bridge writes only private repository-local state below the Git common
directory.  It never writes working-tree files, starts Codex, grants
authority, or changes the existing Acceleration store.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
from typing import Any
import uuid


SCHEMA = "decision-os-companion-manual-bridge-record-v0.1"
STORE_SCHEMA = "decision-os-companion-manual-bridge-store-v0.1"
REPLAY_BASELINE_SCHEMA = (
    "decision-os-companion-manual-bridge-replay-baseline-v0.1"
)
UNKNOWN = "UNKNOWN"
PRE_BRIDGE_UNKNOWN = "UNKNOWN — PRE-BRIDGE MANUAL EVENT NOT SYSTEM-OBSERVED"
GENESIS_EVENT_HASH = "0" * 64
MAX_ARTIFACT_BYTES = 1024 * 1024

ARTIFACT_ROLES = (
    "EVIDENCE_PACKET",
    "PRO_DESIGN",
    "EXECUTION_HANDOFF",
    "BUILD_RECEIPT",
    "PRO_AUDIT",
    "REUSABLE_DELTA_RECORD",
    "GOLDEN_MANIFEST",
    "REPLAY_RESULT",
    "BRIDGE_RECEIPT",
    "FORWARD_ONLY_DELTA",
)
IMPORTABLE_ROLES = frozenset(
    {
        "EVIDENCE_PACKET",
        "PRO_DESIGN",
        "BUILD_RECEIPT",
        "PRO_AUDIT",
        "REUSABLE_DELTA_RECORD",
    }
)
GENERATED_ROLES = frozenset(
    {
        "EXECUTION_HANDOFF",
        "GOLDEN_MANIFEST",
        "REPLAY_RESULT",
        "BRIDGE_RECEIPT",
    }
)
GOLDEN_ROLES = (
    "EVIDENCE_PACKET",
    "PRO_DESIGN",
    "EXECUTION_HANDOFF",
    "BUILD_RECEIPT",
    "PRO_AUDIT",
    "REUSABLE_DELTA_RECORD",
)
SESSION_STATES = (
    "BOUNDARY_INCOMPLETE",
    "COPY_READY",
    "DESIGN_IMPORTED",
    "HANDOFF_GENERATED",
    "HANDOFF_FROZEN",
    "BUILD_RECEIPT_IMPORTED",
    "AUDIT_IMPORTED",
    "DELTA_IMPORTED",
    "GOLDEN_INCOMPLETE",
    "GOLDEN_ELIGIBLE",
    "GOLDEN_FROZEN",
    "REPLAY_ELIGIBLE",
    "REPLAY_RECORDED",
    "BLOCKED_CORRUPT",
    "BLOCKED_AUTHORITY_INFLATION",
)
REPLAY_FIELDS = (
    "task_id",
    "objective",
    "completion_line",
    "do_not_touch",
    "current_gate",
    "authority_boundary",
    "as_of_identity",
    "model_identity",
    "role_identity",
    "time_anchor",
    "required_next_actor",
    "findings",
    "human_execution_cost",
    "reusable_delta",
    "unknowns",
)
REPLAY_STATUSES = (
    "PRESERVED",
    "ALTERED",
    "MISSING",
    "SUBSTITUTED",
    "AUTHORITY-INFLATED",
    "NOT APPLICABLE",
    "UNKNOWN",
)
MODEL_VERIFICATION_STATES = frozenset(
    {
        "VERIFIED_BY_RUNTIME",
        "USER_ATTESTED",
        "ARTIFACT_DECLARED",
        "SELF_DECLARED",
        "UNKNOWN",
        # The accepted Pro packet contains this historical value.  It is
        # preserved as declared evidence and never upgraded.
        "UNVERIFIED",
    }
)
IMPORT_MODES = frozenset({"BYTE_EXACT_FILE_IMPORT", "PASTE_CAPTURE"})
_OUTPUT_EVENT_KINDS = {
    "COPY_FOR_PRO": "COPY_FOR_PRO_GENERATED",
    "EXECUTION_HANDOFF": "EXECUTION_HANDOFF_GENERATED",
    "GOLDEN_MANIFEST": "GOLDEN_MANIFEST_GENERATED",
    "REPLAY_RESULT": "STRUCTURAL_REPLAY_EVALUATED",
    "BRIDGE_RECEIPT": "BRIDGE_RECEIPT_GENERATED",
}
HANDOFF_FIELDS = (
    "Target Layer",
    "Repo Root",
    "Current State",
    "Current Gate",
    "Active Branch",
    "Next Authorized Action",
    "Completion Line",
    "Missing Closure",
    "Next Owner",
    "What the Receiving AI Now Owns",
    "First One Action",
    "Do Not Continue Boundary",
    "What must not be returned to the Decision Owner",
)

EXPECTED_EVIDENCE_IDENTITY = {
    "commit": "970ae5e24e59dada54e1b829229360d9945a0910",
    "path": "validation/companion_manual_bridge_v0_1_shared_evidence_packet.md",
    "blob_sha": "92f9f69f18db052b421fa5fa7f233ce77f5a42b8",
    "sha256": (
        "847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab"
    ),
    "product_as_of_commit": (
        "63eb260a94595298e2b07b476f7f9d8572c9ef09"
    ),
}
_ROLE_AUTHORITIES = {
    "EVIDENCE_PACKET": {
        "EVIDENCE_ONLY",
        "EVIDENCE_INPUT_ONLY",
        UNKNOWN,
    },
    "PRO_DESIGN": {
        "DESIGN_ONLY_NO_EXECUTION_AUTHORITY",
        UNKNOWN,
    },
    "BUILD_RECEIPT": {
        "EXECUTION_EVIDENCE_ONLY",
        "BUILDER_EVIDENCE_ONLY",
        UNKNOWN,
    },
    "PRO_AUDIT": {
        "INDEPENDENT_JUDGMENT_ONLY",
        "AUDIT_ONLY_NO_EXECUTION_AUTHORITY",
        UNKNOWN,
    },
    "REUSABLE_DELTA_RECORD": {
        "FUTURE_USE_CANDIDATE_ONLY",
        UNKNOWN,
    },
}
_BOUNDARY_FIELDS = (
    "task_id",
    "protocol_run_id",
    "objective",
    "completion_line",
    "do_not_touch",
    "current_gate",
    "authority_boundary",
    "as_of_commit",
    "required_next_actor",
)
_BURDEN_FIELDS = (
    "shin_manual_transfer_count",
    "shin_copy_paste_count",
    "shin_re_explanation_count",
    "shin_boundary_correction_count",
    "shin_operational_intervention_count",
    "human_handling_time",
    "total_elapsed_time",
    "number_of_pro_calls",
    "number_of_builder_repairs",
    "number_of_reusable_deltas",
    "fields_lost_or_altered_during_transfer",
)
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,200}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_JSON_FENCE = re.compile(
    r"```json[ \t]*\r?\n(.*?)\r?\n```",
    flags=re.DOTALL | re.IGNORECASE,
)


class ManualBridgeError(RuntimeError):
    """Base error for bounded Manual Bridge operations."""


class ManualBridgeValidationError(ManualBridgeError):
    """Input did not satisfy a typed Bridge contract."""


class ManualBridgeConflictError(ManualBridgeError):
    """An operation conflicts with frozen state or role separation."""


class ManualBridgeBusyError(ManualBridgeConflictError):
    """Another process currently owns the bounded Bridge transaction."""


class ManualBridgeIntegrityError(ManualBridgeError):
    """The private Bridge event, blob, or output state is not trustworthy."""


def sha256_bytes(payload: bytes) -> str:
    """Return the SHA-256 of exact bytes without transforming them."""

    if not isinstance(payload, bytes):
        raise TypeError("Manual Bridge hashing requires bytes.")
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ManualBridgeValidationError(
            "Manual Bridge structured data is invalid."
        ) from exc
    return text.encode("utf-8")


def _json_document(value: Any) -> bytes:
    return _canonical_json(value) + b"\n"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime | str) -> str:
    if isinstance(value, str):
        if not value:
            raise ManualBridgeValidationError("Bridge time is invalid.")
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _clean_scalar(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return UNKNOWN


def _clean_single_line_scalar(value: Any, *, maximum: int = 2000) -> str:
    cleaned = _clean_scalar(value)
    if cleaned == UNKNOWN:
        return cleaned
    if (
        len(cleaned) > maximum
        or "\n" in cleaned
        or "\r" in cleaned
        or "\x00" in cleaned
    ):
        raise ManualBridgeValidationError(
            "Bridge identity and handoff fields must be bounded single-line text."
        )
    return cleaned


def _is_unknown(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip().upper().startswith("UNKNOWN")
    return False


def _git_common_directory(repository: Path) -> Path:
    try:
        completed = subprocess.run(
            (
                "git",
                "-C",
                str(repository),
                "rev-parse",
                "--git-common-dir",
            ),
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ManualBridgeValidationError(
            "Selected repository identity could not be resolved."
        ) from exc
    if completed.returncode != 0 or not completed.stdout.strip():
        raise ManualBridgeValidationError(
            "Select a valid local Git repository first."
        )
    candidate = Path(completed.stdout.strip())
    if not candidate.is_absolute():
        candidate = repository / candidate
    try:
        return candidate.resolve(strict=True)
    except OSError as exc:
        raise ManualBridgeValidationError(
            "Selected repository Git state is unavailable."
        ) from exc


class ManualBridgeStore:
    """Separate append-only Bridge store below the repository Git common dir."""

    _repo_locks_guard = threading.Lock()
    _repo_locks: dict[str, threading.RLock] = {}

    def __init__(self, repository: Path) -> None:
        self.repository = Path(repository).resolve()
        self.git_common_dir = _git_common_directory(self.repository)
        self.root = (
            self.git_common_dir / "decision-os" / "manual-bridge" / "v0.1"
        )
        self.events_path = self.root / "events.jsonl"
        lock_identity = str(self.git_common_dir)
        with self._repo_locks_guard:
            self._lock = self._repo_locks.setdefault(
                lock_identity,
                threading.RLock(),
            )
        self._transaction_local = threading.local()

    def _assert_safe_path(self, target: Path) -> None:
        try:
            relative = target.relative_to(self.git_common_dir)
        except ValueError as exc:
            raise ManualBridgeIntegrityError(
                "Manual Bridge state escaped the Git common directory."
            ) from exc
        current = self.git_common_dir
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise ManualBridgeIntegrityError(
                    "Manual Bridge state path contains a symlink."
                )
        nearest = target if target.exists() else target.parent
        try:
            if not nearest.resolve(strict=True).is_relative_to(
                self.git_common_dir
            ):
                raise ManualBridgeIntegrityError(
                    "Manual Bridge state escaped the Git common directory."
                )
        except FileNotFoundError:
            pass

    @contextmanager
    def transaction(
        self,
        *,
        write: bool = True,
        timeout_seconds: float = 0.25,
    ) -> Any:
        """Bound one repository operation across controllers and processes."""

        depth = getattr(self._transaction_local, "depth", 0)
        if depth:
            if write and not getattr(
                self._transaction_local,
                "write",
                False,
            ):
                raise ManualBridgeConflictError(
                    "A read-only Bridge transaction cannot be upgraded."
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
                self._assert_safe_path(self.root)
            lock_path = self.root / ".transaction.lock"
            if not write and not lock_path.exists():
                raise ManualBridgeIntegrityError(
                    "Manual Bridge transaction identity is missing."
                )
            self._assert_safe_path(lock_path)
            flags = os.O_RDWR | os.O_CREAT if write else os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                descriptor = os.open(lock_path, flags, 0o600)
                if write:
                    os.chmod(lock_path, 0o600)
            except OSError as exc:
                if descriptor is not None:
                    os.close(descriptor)
                raise ManualBridgeIntegrityError(
                    "Manual Bridge transaction lock is unavailable."
                ) from exc
        lock_mode = fcntl.LOCK_EX if write else fcntl.LOCK_SH
        deadline = time.monotonic() + timeout_seconds
        try:
            while True:
                try:
                    fcntl.flock(
                        descriptor,
                        lock_mode | fcntl.LOCK_NB,
                    )
                    break
                except BlockingIOError as exc:
                    if time.monotonic() >= deadline:
                        raise ManualBridgeBusyError(
                            "Manual Bridge is temporarily busy."
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

    def _ensure_directories(self) -> None:
        targets = (
            self.root,
            self.root / "artifacts" / "sha256",
            self.root / "imports",
            self.root / "sessions",
            self.root / "outputs",
        )
        for directory in targets:
            try:
                self._assert_safe_path(directory)
                relative = directory.relative_to(self.git_common_dir)
                current = self.git_common_dir
                for part in relative.parts:
                    current = current / part
                    if current.is_symlink():
                        raise ManualBridgeIntegrityError(
                            "Manual Bridge state path contains a symlink."
                        )
                    current.mkdir(mode=0o700, exist_ok=True)
                    if not current.resolve(strict=True).is_relative_to(
                        self.git_common_dir
                    ):
                        raise ManualBridgeIntegrityError(
                            "Manual Bridge state escaped the Git common directory."
                        )
                    os.chmod(current, 0o700)
            except ManualBridgeIntegrityError:
                raise
            except OSError as exc:
                raise ManualBridgeIntegrityError(
                    "Manual Bridge state permissions could not be secured."
                ) from exc

    def _atomic_write(
        self,
        target: Path,
        payload: bytes,
        *,
        immutable: bool = False,
    ) -> None:
        self._ensure_directories()
        self._assert_safe_path(target)
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._assert_safe_path(target.parent)
        if not target.parent.resolve(strict=True).is_relative_to(
            self.git_common_dir
        ):
            raise ManualBridgeIntegrityError(
                "Manual Bridge state path is unsafe."
            )
        os.chmod(target.parent, 0o700)
        if target.exists():
            try:
                current = target.read_bytes()
            except OSError as exc:
                raise ManualBridgeIntegrityError(
                    "Manual Bridge state could not be verified."
                ) from exc
            if immutable:
                if current != payload:
                    raise ManualBridgeIntegrityError(
                        "Content-addressed Bridge state is corrupted."
                    )
                return
        temporary = target.parent / f".bridge-{uuid.uuid4().hex}.tmp"
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            os.chmod(target, 0o600)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise ManualBridgeIntegrityError(
                "Manual Bridge state could not be written safely."
            ) from exc
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    @staticmethod
    def _wrapped(record: Mapping[str, Any]) -> dict[str, Any]:
        plain = dict(record)
        return {
            "record": plain,
            "record_hash": sha256_bytes(_canonical_json(plain)),
            "schema": STORE_SCHEMA,
        }

    def write_record(self, target: Path, record: Mapping[str, Any]) -> None:
        with self._lock:
            self._atomic_write(target, _json_document(self._wrapped(record)))

    def read_record(self, target: Path) -> dict[str, Any]:
        self._assert_safe_path(target)
        try:
            raw = target.read_bytes()
            value = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ManualBridgeIntegrityError(
                "Manual Bridge structured state is corrupted."
            ) from exc
        if (
            not isinstance(value, dict)
            or value.get("schema") != STORE_SCHEMA
            or not isinstance(value.get("record"), dict)
            or not isinstance(value.get("record_hash"), str)
            or value["record_hash"]
            != sha256_bytes(_canonical_json(value["record"]))
        ):
            raise ManualBridgeIntegrityError(
                "Manual Bridge structured state checksum is invalid."
            )
        return value["record"]

    def read_events(self) -> list[dict[str, Any]]:
        with self._lock:
            if not self.root.exists():
                return []
            self._assert_safe_path(self.root)
            if not self.events_path.exists():
                material = [
                    path
                    for path in self.root.rglob("*")
                    if not path.is_dir() and path.name != ".transaction.lock"
                ]
                if material:
                    raise ManualBridgeIntegrityError(
                        "Manual Bridge event history is missing."
                    )
                return []
            self._assert_safe_path(self.events_path)
            try:
                raw_events = self.events_path.read_bytes()
            except OSError as exc:
                raise ManualBridgeIntegrityError(
                    "Manual Bridge event history is unreadable."
                ) from exc
            if not raw_events:
                raise ManualBridgeIntegrityError(
                    "Manual Bridge event history is empty."
                )
            lines = raw_events.splitlines()
            events: list[dict[str, Any]] = []
            event_ids: set[str] = set()
            previous = GENESIS_EVENT_HASH
            for raw in lines:
                if not raw:
                    raise ManualBridgeIntegrityError(
                        "Manual Bridge event history contains an empty record."
                    )
                try:
                    event = json.loads(raw)
                except (UnicodeError, json.JSONDecodeError) as exc:
                    raise ManualBridgeIntegrityError(
                        "Manual Bridge event history is corrupted."
                    ) from exc
                if not isinstance(event, dict):
                    raise ManualBridgeIntegrityError(
                        "Manual Bridge event record is invalid."
                    )
                event_hash = event.get("event_hash")
                body = {
                    key: value
                    for key, value in event.items()
                    if key != "event_hash"
                }
                expected = sha256_bytes(_canonical_json(body))
                if (
                    event.get("schema") != STORE_SCHEMA
                    or event.get("previous_event_hash") != previous
                    or event_hash != expected
                    or not isinstance(event.get("event_id"), str)
                    or event["event_id"] in event_ids
                ):
                    raise ManualBridgeIntegrityError(
                        "Manual Bridge event chain verification failed."
                    )
                previous = event_hash
                event_ids.add(event["event_id"])
                events.append(event)
            return events

    def append_event(
        self,
        *,
        event_id: str,
        kind: str,
        recorded_at: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not _SAFE_ID.fullmatch(event_id):
            raise ManualBridgeValidationError("Bridge event identity is invalid.")
        with self._lock:
            events = self.read_events()
            body = {
                "event_id": event_id,
                "kind": kind,
                "payload": dict(payload),
                "previous_event_hash": (
                    events[-1]["event_hash"] if events else GENESIS_EVENT_HASH
                ),
                "recorded_at": recorded_at,
                "schema": STORE_SCHEMA,
            }
            event = {
                **body,
                "event_hash": sha256_bytes(_canonical_json(body)),
            }
            self._ensure_directories()
            try:
                self._assert_safe_path(self.events_path)
                flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                descriptor = os.open(
                    self.events_path,
                    flags,
                    0o600,
                )
                with os.fdopen(descriptor, "ab") as stream:
                    stream.write(_json_document(event))
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(self.events_path, 0o600)
            except OSError as exc:
                raise ManualBridgeIntegrityError(
                    "Manual Bridge event could not be appended."
                ) from exc
            return event

    def store_blob(self, payload: bytes) -> tuple[str, str]:
        digest = sha256_bytes(payload)
        target = self.root / "artifacts" / "sha256" / f"{digest}.bin"
        with self._lock:
            self._atomic_write(target, payload, immutable=True)
        return digest, f"artifacts/sha256/{digest}.bin"

    def read_blob(self, digest: str) -> bytes:
        if not _SHA256.fullmatch(digest):
            raise ManualBridgeIntegrityError(
                "Manual Bridge artifact identity is invalid."
            )
        target = self.root / "artifacts" / "sha256" / f"{digest}.bin"
        self._assert_safe_path(target)
        try:
            payload = target.read_bytes()
        except OSError as exc:
            raise ManualBridgeIntegrityError(
                "Manual Bridge artifact bytes are missing."
            ) from exc
        if sha256_bytes(payload) != digest:
            raise ManualBridgeIntegrityError(
                "Manual Bridge artifact bytes are corrupted."
            )
        return payload

    def session_path(self, session_id: str) -> Path:
        if not _SAFE_ID.fullmatch(session_id):
            raise ManualBridgeIntegrityError("Bridge session identity is invalid.")
        return self.root / "sessions" / session_id / "session.json"

    def save_session(self, session: Mapping[str, Any]) -> None:
        session_id = session.get("session_id")
        if not isinstance(session_id, str):
            raise ManualBridgeValidationError("Bridge session identity is missing.")
        self.write_record(self.session_path(session_id), session)

    def load_session(self, session_id: str) -> dict[str, Any]:
        return self.read_record(self.session_path(session_id))

    def set_active_session(self, session_id: str) -> None:
        if not _SAFE_ID.fullmatch(session_id):
            raise ManualBridgeValidationError("Bridge session identity is invalid.")
        self.write_record(
            self.root / "active_session.json",
            {"session_id": session_id},
        )

    def active_session(self) -> str | None:
        target = self.root / "active_session.json"
        if not target.exists():
            return None
        record = self.read_record(target)
        session_id = record.get("session_id")
        if not isinstance(session_id, str) or not _SAFE_ID.fullmatch(session_id):
            raise ManualBridgeIntegrityError(
                "Active Bridge session identity is corrupted."
            )
        return session_id

    def import_path(self, import_event_id: str) -> Path:
        if not _SAFE_ID.fullmatch(import_event_id):
            raise ManualBridgeIntegrityError("Bridge import identity is invalid.")
        return self.root / "imports" / f"{import_event_id}.json"

    def save_import(self, record: Mapping[str, Any]) -> None:
        event_id = record.get("import_event_id")
        if not isinstance(event_id, str):
            raise ManualBridgeValidationError("Bridge import identity is missing.")
        self.write_record(self.import_path(event_id), record)

    def load_import(self, import_event_id: str) -> dict[str, Any]:
        return self.read_record(self.import_path(import_event_id))

    def output_path(self, session_id: str, filename: str) -> Path:
        if not _SAFE_ID.fullmatch(session_id):
            raise ManualBridgeIntegrityError("Bridge session identity is invalid.")
        if not re.fullmatch(r"[a-z0-9_]+\.(?:md|json)", filename):
            raise ManualBridgeValidationError("Bridge output name is invalid.")
        return self.root / "outputs" / session_id / filename

    def write_output(
        self,
        session_id: str,
        filename: str,
        payload: bytes,
    ) -> str:
        target = self.output_path(session_id, filename)
        with self._lock:
            self._atomic_write(target, payload)
        return f"outputs/{session_id}/{filename}"

    def read_output(self, relative_path: str) -> bytes:
        parts = Path(relative_path).parts
        if (
            len(parts) != 3
            or parts[0] != "outputs"
            or not _SAFE_ID.fullmatch(parts[1])
            or not re.fullmatch(r"[a-z0-9_]+\.(?:md|json)", parts[2])
        ):
            raise ManualBridgeIntegrityError(
                "Manual Bridge output path is invalid."
            )
        target = self.root.joinpath(*parts)
        self._assert_safe_path(target)
        try:
            return target.read_bytes()
        except OSError as exc:
            raise ManualBridgeIntegrityError(
                "Manual Bridge generated output is missing."
            ) from exc


def _extract_envelope(payload: bytes) -> dict[str, Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return {}
    candidates: list[dict[str, Any]] = []
    for match in _JSON_FENCE.finditer(text):
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            candidates.append(value)
    normative = [
        candidate
        for candidate in candidates
        if candidate.get("schema") == SCHEMA
    ]
    if len(normative) > 1:
        raise ManualBridgeValidationError(
            "Artifact contains multiple normative Bridge envelopes."
        )
    if normative:
        return normative[0]
    return candidates[0] if len(candidates) == 1 else {}


def _merged_metadata(
    payload: bytes,
    explicit: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str]:
    embedded = _extract_envelope(payload)
    if explicit is None:
        return embedded, "EMBEDDED_TYPED_JSON" if embedded else "NONE"
    if not isinstance(explicit, Mapping):
        raise ManualBridgeValidationError(
            "Explicit Bridge metadata must be an object."
        )
    merged = dict(embedded)
    for key, value in explicit.items():
        if (
            key in {
                "artifact_role",
                "task_id",
                "protocol_run_id",
                "as_of_commit",
                "authority_state",
            }
            and key in embedded
            and not _is_unknown(embedded[key])
            and not _is_unknown(value)
            and embedded[key] != value
        ):
            raise ManualBridgeConflictError(
                "Explicit metadata conflicts with the artifact envelope."
            )
        merged[key] = value
    source = "EXPLICIT_UI_METADATA"
    if embedded:
        source = "EMBEDDED_TYPED_JSON_PLUS_EXPLICIT_UI_METADATA"
    return merged, source


def _default_result_records(
    id_factory: Callable[[], str],
) -> dict[str, dict[str, Any]]:
    return {
        "protocol": {
            "result_id": id_factory(),
            "question": "Did Pro Manual Protocol Run 002 execute correctly?",
            "result": "IN PROGRESS / NOT FINAL",
            "unknowns": [UNKNOWN],
        },
        "product": {
            "result_id": id_factory(),
            "question": (
                "Did Companion Manual Bridge v0.1 satisfy this bounded design?"
            ),
            "result": (
                "BUILDER EVIDENCE ONLY / INDEPENDENT AUDIT REQUIRED"
            ),
            "unknowns": ["Independent Pro Audit has not been imported."],
        },
        "replay": {
            "result_id": id_factory(),
            "question": "Did the Bridge preserve the Golden Run structure?",
            "result": "NOT YET PERFORMED",
            "unknowns": ["Golden Replay has not been performed."],
        },
    }


def _observation(
    *,
    recorded_at: str,
    unit: str,
    method: str,
    value: int | float | str = 0,
    basis: str = "SYSTEM_OBSERVED_LOWER_BOUND",
    confidence: str = "EXACT_FOR_POST_BRIDGE_EVENTS",
    notes: str = PRE_BRIDGE_UNKNOWN,
) -> dict[str, Any]:
    return {
        "basis": basis,
        "confidence": confidence,
        "method": method,
        "notes": notes,
        "recorded_at": recorded_at,
        "source_event_ids": [],
        "unit": unit,
        "value_or_unknown": value,
    }


def _default_burden(recorded_at: str) -> dict[str, dict[str, Any]]:
    burden: dict[str, dict[str, Any]] = {}
    count_fields = {
        "shin_manual_transfer_count",
        "shin_copy_paste_count",
        "shin_re_explanation_count",
        "shin_boundary_correction_count",
        "shin_operational_intervention_count",
        "number_of_pro_calls",
        "number_of_builder_repairs",
        "number_of_reusable_deltas",
        "fields_lost_or_altered_during_transfer",
    }
    for field in _BURDEN_FIELDS:
        if field in count_fields:
            burden[field] = _observation(
                recorded_at=recorded_at,
                unit="count",
                method="LOCAL_EVENT_COUNT",
            )
        else:
            burden[field] = _observation(
                recorded_at=recorded_at,
                unit="seconds",
                method="UNAVAILABLE_IN_V0_1",
                value=UNKNOWN,
                basis=PRE_BRIDGE_UNKNOWN,
                confidence="UNKNOWN",
            )
    return burden


class BridgeSessionController:
    """Own one bounded Bridge session for one selected repository."""

    def __init__(
        self,
        repository: Path,
        *,
        clock: Callable[[], datetime | str] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.repository = Path(repository).resolve()
        self.store = ManualBridgeStore(self.repository)
        self._clock = clock or _now_utc
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))
        self._lock = self.store._lock
        self._initial_integrity_failure = False
        # Active identity is resolved under the bounded transaction in _guard;
        # construction itself never lets Bridge I/O take down the Runner.
        self._session_id: str | None = None

    def _now(self) -> str:
        return _timestamp(self._clock())

    def _new_id(self) -> str:
        value = str(self._id_factory())
        if not _SAFE_ID.fullmatch(value):
            raise ManualBridgeValidationError(
                "Generated Bridge identity is invalid."
            )
        return value

    def _guard(self) -> dict[str, Any] | None:
        if self._initial_integrity_failure:
            raise ManualBridgeIntegrityError(
                "Manual Bridge state is corrupted."
            )
        events = self.store.read_events()
        events_by_id = {event["event_id"]: event for event in events}
        active_session_id = self.store.active_session()
        if active_session_id is None:
            if events:
                raise ManualBridgeIntegrityError(
                    "Manual Bridge event state has no active session."
                )
            self._session_id = None
            return None
        self._session_id = active_session_id
        session = self.store.load_session(self._session_id)
        if (
            session.get("schema") != SCHEMA
            or session.get("session_id") != self._session_id
            or not isinstance(session.get("imports"), list)
            or not isinstance(session.get("outputs"), dict)
            or session.get("event_count") != len(events)
            or session.get("event_chain_head")
            != (events[-1]["event_hash"] if events else GENESIS_EVENT_HASH)
        ):
            raise ManualBridgeIntegrityError(
                "Manual Bridge session state is corrupted."
            )
        created_event_id = session.get("created_event_id")
        created_event = events_by_id.get(created_event_id)
        if (
            not isinstance(created_event, dict)
            or created_event.get("kind") != "BRIDGE_SESSION_CREATED"
            or created_event.get("payload", {}).get("session_id")
            != self._session_id
            or created_event.get("payload", {}).get("boundary_hash")
            != sha256_bytes(_canonical_json(session.get("boundary")))
        ):
            raise ManualBridgeIntegrityError(
                "Manual Bridge session creation event is inconsistent."
            )
        import_ids = session["imports"]
        if len(import_ids) != len(set(import_ids)):
            raise ManualBridgeIntegrityError(
                "Manual Bridge import history is inconsistent."
            )
        for import_id in import_ids:
            record = self.store.load_import(import_id)
            digest = record.get("artifact_content_hash")
            if (
                record.get("session_id") != self._session_id
                or record.get("import_event_id") != import_id
                or not isinstance(digest, str)
                or import_id not in events_by_id
                or record.get("event_hash")
                != events_by_id[import_id].get("event_hash")
                or events_by_id[import_id].get("kind")
                not in {"ARTIFACT_IMPORTED", "ARTIFACT_IMPORT_DUPLICATE"}
                or events_by_id[import_id].get("payload", {}).get(
                    "artifact_sha256"
                )
                != digest
                or events_by_id[import_id].get("payload", {}).get(
                    "selected_role"
                )
                != record.get("selected_role")
                or events_by_id[import_id].get("payload", {}).get("session_id")
                != self._session_id
                or events_by_id[import_id].get("payload", {}).get(
                    "validation_state"
                )
                != record.get("validation_state")
            ):
                raise ManualBridgeIntegrityError(
                    "Manual Bridge import identity is corrupted."
                )
            self.store.read_blob(digest)
        for output_role, output in session["outputs"].items():
            if not isinstance(output, dict):
                raise ManualBridgeIntegrityError(
                    "Manual Bridge output identity is corrupted."
                )
            raw = self.store.read_output(output.get("path", ""))
            if sha256_bytes(raw) != output.get("sha256"):
                raise ManualBridgeIntegrityError(
                    "Frozen or generated Bridge output was altered."
                )
            generated_event_id = output.get("generated_event_id")
            generated_event = events_by_id.get(generated_event_id)
            if (
                not isinstance(generated_event, dict)
                or generated_event.get("kind")
                != _OUTPUT_EVENT_KINDS.get(output_role)
                or generated_event.get("payload", {}).get("session_id")
                != self._session_id
                or generated_event.get("payload", {}).get("artifact_role")
                != output_role
                or generated_event.get("payload", {}).get("output_sha256")
                != output.get("sha256")
            ):
                raise ManualBridgeIntegrityError(
                    "Manual Bridge output event identity is missing."
                )
            freeze_event_id = output.get("freeze_event_id")
            if (
                output.get("frozen")
                and (
                    freeze_event_id not in events_by_id
                    or events_by_id[freeze_event_id].get("kind")
                    != "GENERATED_ARTIFACT_FROZEN"
                    or events_by_id[freeze_event_id].get("payload", {}).get(
                        "artifact_sha256"
                    )
                    != output.get("sha256")
                    or events_by_id[freeze_event_id].get("payload", {}).get(
                        "artifact_role"
                    )
                    != output_role
                )
            ):
                raise ManualBridgeIntegrityError(
                    "Manual Bridge output freeze identity is missing."
                )
        return session

    @staticmethod
    def _evidence_matches(boundary: Mapping[str, Any]) -> bool:
        evidence = boundary.get("evidence_packet_identity")
        return isinstance(evidence, Mapping) and all(
            evidence.get(key) == expected
            for key, expected in EXPECTED_EVIDENCE_IDENTITY.items()
        )

    @staticmethod
    def _boundary_complete(boundary: Mapping[str, Any]) -> bool:
        if any(_is_unknown(boundary.get(key)) for key in _BOUNDARY_FIELDS):
            return False
        return BridgeSessionController._evidence_matches(boundary)

    def _save_session(self, session: Mapping[str, Any]) -> None:
        events = self.store.read_events()
        anchored = dict(session)
        anchored["event_count"] = len(events)
        anchored["event_chain_head"] = (
            events[-1]["event_hash"] if events else GENESIS_EVENT_HASH
        )
        if isinstance(session, dict):
            session.update(
                {
                    "event_count": anchored["event_count"],
                    "event_chain_head": anchored["event_chain_head"],
                }
            )
        self.store.save_session(anchored)

    def _append(
        self,
        kind: str,
        payload: Mapping[str, Any],
        *,
        event_id: str | None = None,
        recorded_at: str | None = None,
    ) -> dict[str, Any]:
        return self.store.append_event(
            event_id=event_id or self._new_id(),
            kind=kind,
            recorded_at=recorded_at or self._now(),
            payload=payload,
        )

    def create_session(self, boundary: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(boundary, dict):
            raise ManualBridgeValidationError(
                "Bridge session boundary must be an object."
            )
        with self.store.transaction():
            current = self._guard()
            if current is not None:
                raise ManualBridgeConflictError(
                    "One Manual Bridge session is already active."
                )
            normalized = dict(boundary)
            for key in _BOUNDARY_FIELDS:
                normalized[key] = _clean_single_line_scalar(boundary.get(key))
            evidence = boundary.get("evidence_packet_identity")
            normalized["evidence_packet_identity"] = (
                dict(evidence) if isinstance(evidence, Mapping) else {}
            )
            for field in (
                "framework_lens_used",
                "relevant_decision_os_layer",
                "reinterpretation_question",
                "framework_derived_finding",
            ):
                normalized[field] = _clean_single_line_scalar(
                    boundary.get(field)
                )
            for field in (
                "current_state",
                "active_branch",
                "missing_closure",
                "what_receiving_ai_owns",
                "first_one_action",
                "do_not_continue_boundary",
            ):
                normalized[field] = _clean_single_line_scalar(
                    boundary.get(field)
                )
            created_at = self._now()
            session_id = self._new_id()
            complete = self._boundary_complete(normalized)
            hold_reason = None
            if not self._evidence_matches(normalized):
                hold_reason = "HOLD — EVIDENCE IDENTITY MISMATCH"
            elif not complete:
                hold_reason = "HOLD — INCOMPLETE BOUNDARY"
            session = {
                "boundary": normalized,
                "boundary_complete": complete,
                "burden": _default_burden(created_at),
                "created_at": created_at,
                "effective_by_role": {},
                "golden_manifest": None,
                "hold_reason": hold_reason,
                "imports": [],
                "outputs": {},
                "results": _default_result_records(self._new_id),
                "schema": SCHEMA,
                "session_id": session_id,
                "state": "COPY_READY" if complete else "BOUNDARY_INCOMPLETE",
            }
            event = self._append(
                "BRIDGE_SESSION_CREATED",
                {
                    "boundary_hash": sha256_bytes(_canonical_json(normalized)),
                    "boundary_complete": complete,
                    "session_id": session_id,
                },
                recorded_at=created_at,
            )
            session["created_event_id"] = event["event_id"]
            self._save_session(session)
            self.store.set_active_session(session_id)
            self._session_id = session_id
            return self.snapshot()

    def _require_session(self) -> dict[str, Any]:
        session = self._guard()
        if session is None:
            raise ManualBridgeValidationError(
                "Start one Manual Bridge session first."
            )
        return session

    def _increment(
        self,
        session: dict[str, Any],
        field: str,
        event_id: str,
        *,
        amount: int = 1,
    ) -> None:
        record = session["burden"][field]
        current = record.get("value_or_unknown")
        if not isinstance(current, (int, float)) or isinstance(current, bool):
            current = 0
        record["value_or_unknown"] = current + amount
        record["recorded_at"] = self._now()
        record.setdefault("source_event_ids", []).append(event_id)

    def _set_output(
        self,
        session: dict[str, Any],
        role: str,
        filename: str,
        payload: bytes,
        event_kind: str,
    ) -> bool:
        existing = session["outputs"].get(role)
        digest = sha256_bytes(payload)
        if existing:
            if existing.get("sha256") == digest:
                # Deterministic regeneration is a no-op.  In particular, never
                # replace the record that carries a freeze identity.
                return False
            if existing.get("frozen"):
                raise ManualBridgeConflictError(
                    "Frozen Bridge output is immutable; use a Forward-only Delta."
                )
        relative = self.store.write_output(
            session["session_id"],
            filename,
            payload,
        )
        event = self._append(
            event_kind,
            {
                "artifact_role": role,
                "output_sha256": digest,
                "session_id": session["session_id"],
                "size_bytes": len(payload),
            },
        )
        session["outputs"][role] = {
            "frozen": bool(existing and existing.get("frozen")),
            "generated_event_id": event["event_id"],
            "path": relative,
            "sha256": digest,
            "size_bytes": len(payload),
        }
        self._save_session(session)
        return True

    def copy_for_pro(self) -> dict[str, Any]:
        with self.store.transaction():
            session = self._require_session()
            if not session["boundary_complete"]:
                raise ManualBridgeConflictError(
                    session.get("hold_reason") or "HOLD — INCOMPLETE BOUNDARY"
                )
            boundary = session["boundary"]
            evidence = boundary["evidence_packet_identity"]
            text = (
                "# Copy for Pro — Companion Manual Bridge v0.1\n\n"
                "## Fixed Task Boundary\n\n"
                f"Task ID: {boundary['task_id']}\n\n"
                f"Protocol Run ID: {boundary['protocol_run_id']}\n\n"
                f"Objective: {boundary['objective']}\n\n"
                f"Completion Line: {boundary['completion_line']}\n\n"
                f"Do Not Touch: {boundary['do_not_touch']}\n\n"
                f"Authority Boundary: {boundary['authority_boundary']}\n\n"
                "## Frozen Evidence Packet Identity\n\n"
                f"Commit: {evidence['commit']}\n\n"
                f"Path: {evidence['path']}\n\n"
                f"Blob SHA: {evidence['blob_sha']}\n\n"
                f"SHA-256: {evidence['sha256']}\n\n"
                f"Product As-of commit: {evidence['product_as_of_commit']}\n\n"
                "## Required Artifact Role\n\n"
                "PRO_DESIGN\n\n"
                "## Required Output\n\n"
                "Return a typed Bridge Artifact Envelope, exact implementation "
                "surface, required tests, Builder instructions, acceptance "
                "conditions, claim boundary, UNKNOWNs, and final seal.\n\n"
                "Artifact identity, role, model, time, or hash grants no execution, "
                "merge, publication, or release authority.\n\n"
                "Missing facts must remain UNKNOWN.\n\n"
                "## Final Seal\n\n"
                "DESIGN_READY_FOR_BUILD — DESIGN ONLY / NO EXECUTION AUTHORITY\n"
            )
            payload = text.encode("utf-8")
            self._set_output(
                session,
                "COPY_FOR_PRO",
                "copy_for_pro.md",
                payload,
                "COPY_FOR_PRO_GENERATED",
            )
            refreshed = self._require_session()
            transfer_event = self._append(
                "COPY_FOR_PRO_TRANSFERRED",
                {
                    "artifact_role": "COPY_FOR_PRO",
                    "output_sha256": refreshed["outputs"]["COPY_FOR_PRO"][
                        "sha256"
                    ],
                    "session_id": refreshed["session_id"],
                },
            )
            event_id = transfer_event["event_id"]
            self._increment(
                refreshed,
                "shin_manual_transfer_count",
                event_id,
            )
            self._increment(refreshed, "shin_copy_paste_count", event_id)
            self._save_session(refreshed)
            return self.snapshot()

    @staticmethod
    def _authority_inflated(role: str, authority: str) -> bool:
        if authority in _ROLE_AUTHORITIES.get(role, {UNKNOWN}):
            return False
        upper = authority.upper()
        inflation_tokens = (
            "GRANT",
            "MERGE",
            "PUBLISH",
            "RELEASE",
            "EXECUTION_AUTHORITY",
            "PRODUCT_PASS",
            "PROTOCOL_PASS",
            "REPLAY_PASS",
            "CERTIFIED",
        )
        return any(token in upper for token in inflation_tokens) or authority != UNKNOWN

    def _record_import_failure(
        self,
        *,
        session: dict[str, Any],
        failure: str,
        digest: str,
        selected_role: Any,
    ) -> None:
        event = self._append(
            "ARTIFACT_IMPORT_REJECTED",
            {
                "artifact_sha256": digest,
                "failure": failure,
                "selected_role": selected_role,
                "session_id": session["session_id"],
            },
        )
        self._increment(
            session,
            "shin_operational_intervention_count",
            event["event_id"],
        )
        session["hold_reason"] = failure
        self._save_session(session)

    def import_artifact(
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
        with self.store.transaction():
            session = self._require_session()
            if not isinstance(selected_role, str) or selected_role not in IMPORTABLE_ROLES:
                raise ManualBridgeValidationError(
                    "Select one supported import role before accepting bytes."
                )
            if not isinstance(payload, bytes) or not payload:
                raise ManualBridgeValidationError(
                    "Artifact import requires non-empty exact bytes."
                )
            if len(payload) > MAX_ARTIFACT_BYTES:
                raise ManualBridgeValidationError(
                    "Artifact exceeds the 1 MiB Manual Bridge limit."
                )
            if import_mode not in IMPORT_MODES:
                raise ManualBridgeValidationError(
                    "Bridge import mode is unsupported."
                )
            if (
                not isinstance(source_path_or_label, str)
                or not source_path_or_label
                or len(source_path_or_label) > 1000
                or "\n" in source_path_or_label
                or "\r" in source_path_or_label
                or "\x00" in source_path_or_label
            ):
                raise ManualBridgeValidationError(
                    "Artifact source label is invalid."
                )

            # Exact identity is fixed before decoding, parsing, extraction, or
            # display escaping.
            digest = sha256_bytes(payload)
            envelope, metadata_source = _merged_metadata(payload, metadata)
            embedded_hash = envelope.get("artifact_content_hash")
            effective_declared_hash = declared_sha256
            if (
                effective_declared_hash is None
                and isinstance(embedded_hash, str)
                and _SHA256.fullmatch(embedded_hash)
            ):
                effective_declared_hash = embedded_hash
            if (
                effective_declared_hash is not None
                and (
                    not isinstance(effective_declared_hash, str)
                    or effective_declared_hash.lower() != digest
                )
            ):
                self._record_import_failure(
                    session=session,
                    failure="DECLARED_HASH_MISMATCH",
                    digest=digest,
                    selected_role=selected_role,
                )
                raise ManualBridgeValidationError(
                    "Declared SHA-256 does not match exact payload bytes."
                )

            declared_role = _clean_single_line_scalar(
                envelope.get("artifact_role", envelope.get("declared_role"))
            )
            if declared_role != UNKNOWN and declared_role != selected_role:
                self._record_import_failure(
                    session=session,
                    failure="HOLD — ROLE MISMATCH",
                    digest=digest,
                    selected_role=selected_role,
                )
                raise ManualBridgeConflictError("HOLD — ROLE MISMATCH")

            previous_records = [
                self.store.load_import(import_id)
                for import_id in session["imports"]
            ]
            for previous in previous_records:
                if (
                    previous["artifact_content_hash"] == digest
                    and previous["selected_role"] != selected_role
                ):
                    self._record_import_failure(
                        session=session,
                        failure="HOLD — ROLE COLLISION",
                        digest=digest,
                        selected_role=selected_role,
                    )
                    raise ManualBridgeConflictError("HOLD — ROLE COLLISION")

            authority = _clean_single_line_scalar(
                envelope.get("authority_state")
            )
            if self._authority_inflated(selected_role, authority):
                self._record_import_failure(
                    session=session,
                    failure="BLOCKED_AUTHORITY_INFLATION",
                    digest=digest,
                    selected_role=selected_role,
                )
                session["state"] = "BLOCKED_AUTHORITY_INFLATION"
                self._save_session(session)
                raise ManualBridgeConflictError(
                    "BLOCKED_AUTHORITY_INFLATION"
                )
            if (
                selected_role == "PRO_AUDIT"
                and (
                    envelope.get("builder_generated") is True
                    or "BUILDER"
                    in _clean_single_line_scalar(
                        envelope.get("producer_role")
                    ).upper()
                )
            ):
                self._record_import_failure(
                    session=session,
                    failure="BUILDER_GENERATED_AUDIT_INELIGIBLE",
                    digest=digest,
                    selected_role=selected_role,
                )
                raise ManualBridgeConflictError(
                    "Builder-generated Pro Audit is ineligible."
                )

            duplicate_of = None
            for previous in previous_records:
                if (
                    previous["artifact_content_hash"] == digest
                    and previous["selected_role"] == selected_role
                ):
                    duplicate_of = previous["import_event_id"]
                    break

            current_effective_id = session["effective_by_role"].get(
                selected_role
            )
            if supersedes_import_event_id is not None:
                if (
                    current_effective_id != supersedes_import_event_id
                    or not isinstance(correction_reason, str)
                    or not correction_reason.strip()
                ):
                    raise ManualBridgeConflictError(
                        "Forward-only correction identity or reason is invalid."
                    )
            elif correction_reason is not None:
                raise ManualBridgeValidationError(
                    "Correction reason requires a superseded import."
                )

            artifact_hash, content_path = self.store.store_blob(payload)
            imported_at = self._now()
            event_id = self._new_id()
            model = envelope.get("model_identity")
            if not isinstance(model, Mapping):
                model = {}
            claimed_verification = _clean_single_line_scalar(
                model.get("verification_state")
            )
            verification = claimed_verification
            if verification not in MODEL_VERIFICATION_STATES:
                verification = "UNKNOWN"
            elif verification == "VERIFIED_BY_RUNTIME":
                # Imported bytes are declaration evidence, not a trusted
                # observation by this Companion runtime.
                verification = "ARTIFACT_DECLARED"
            claimed_as_of = _clean_single_line_scalar(
                envelope.get("as_of_commit")
            )
            as_of_commit = (
                claimed_as_of
                if _COMMIT.fullmatch(claimed_as_of)
                else UNKNOWN
            )
            task_id = _clean_single_line_scalar(envelope.get("task_id"))
            protocol_run_id = _clean_single_line_scalar(
                envelope.get("protocol_run_id")
            )
            imported_evidence = envelope.get("evidence_packet_identity")
            if not isinstance(imported_evidence, Mapping):
                imported_evidence = {}
            evidence_commit = _clean_scalar(
                envelope.get(
                    "evidence_packet_commit",
                    imported_evidence.get("commit"),
                )
            )
            evidence_blob_sha = _clean_scalar(
                envelope.get(
                    "evidence_packet_blob_sha",
                    imported_evidence.get("blob_sha"),
                )
            )
            evidence_sha256 = _clean_scalar(
                envelope.get(
                    "evidence_packet_sha256",
                    imported_evidence.get("sha256"),
                )
            )
            evidence_path = _clean_scalar(imported_evidence.get("path"))
            evidence_product_as_of = _clean_scalar(
                imported_evidence.get("product_as_of_commit")
            )
            boundary_evidence = session["boundary"][
                "evidence_packet_identity"
            ]
            evidence_identity_match = (
                evidence_commit == boundary_evidence["commit"]
                and evidence_blob_sha == boundary_evidence["blob_sha"]
                and evidence_sha256 == boundary_evidence["sha256"]
                and (
                    evidence_path == UNKNOWN
                    or evidence_path == boundary_evidence["path"]
                )
                and (
                    evidence_product_as_of == UNKNOWN
                    or evidence_product_as_of
                    == boundary_evidence["product_as_of_commit"]
                )
            )
            missing: list[str] = []
            required = {
                "task_id": task_id,
                "protocol_run_id": protocol_run_id,
                "declared_role": declared_role,
                "authority_state": authority,
                "as_of_commit": as_of_commit,
            }
            if selected_role == "PRO_DESIGN":
                required.update(
                    {
                        "role_identity": _clean_single_line_scalar(
                            envelope.get("role_identity")
                        ),
                        "required_next_actor": _clean_single_line_scalar(
                            envelope.get("required_next_actor")
                        ),
                    }
                )
            for name, value in required.items():
                if _is_unknown(value):
                    missing.append(name)
            role_required_keys = {
                "BUILD_RECEIPT": (
                    "builder_identity",
                    "builder_authority_source",
                    "base_commit",
                    "branch",
                    "implementation_commit",
                    "exact_changed_paths",
                    "test_commands",
                    "findings",
                    "deviations",
                    "repair_count",
                    "human_execution_cost",
                    "routine_cleanup_state",
                    "unknowns",
                    "builder_completion_boundary",
                ),
                "PRO_AUDIT": (
                    "audit_evidence_basis",
                    "repository_diff_inspected",
                    "artifact_identities_independently_checked",
                    "tests_independently_checked",
                    "product_result_recommendation",
                    "claim_boundary",
                    "repair_route",
                    "unknowns",
                ),
                "REUSABLE_DELTA_RECORD": (
                    "findings",
                    "reusable_delta",
                    "unknowns",
                    "claim_boundary",
                ),
            }
            for key in role_required_keys.get(selected_role, ()):
                if key not in envelope or envelope[key] in (None, "", UNKNOWN):
                    missing.append(key)
                elif key == "reusable_delta" and not envelope[key]:
                    missing.append(key)
            role_identity = _clean_single_line_scalar(
                envelope.get("role_identity")
            )
            if (
                selected_role == "PRO_DESIGN"
                and role_identity != "Independent Pro Designer"
            ):
                missing.append("independent_pro_designer_role_identity")
            if (
                selected_role == "PRO_AUDIT"
                and role_identity != "Independent Pro Auditor"
            ):
                missing.append("independent_pro_auditor_role_identity")
            if selected_role == "PRO_AUDIT":
                for key in (
                    "repository_diff_inspected",
                    "artifact_identities_independently_checked",
                    "tests_independently_checked",
                ):
                    if envelope.get(key) is not True:
                        missing.append(key)
            identity_match = (
                task_id == session["boundary"]["task_id"]
                and protocol_run_id == session["boundary"]["protocol_run_id"]
                and as_of_commit == session["boundary"]["as_of_commit"]
            )
            validation_state = "VALID"
            if (
                selected_role != "EVIDENCE_PACKET"
                and not evidence_identity_match
            ):
                validation_state = "HOLD_EVIDENCE_IDENTITY_MISMATCH"
            elif missing:
                validation_state = "HOLD_MISSING_REQUIRED_FIELDS"
            elif not identity_match:
                validation_state = "HOLD_IDENTITY_MISMATCH"
            golden_output = session["outputs"].get("GOLDEN_MANIFEST")
            current_effective = (
                self.store.load_import(current_effective_id)
                if current_effective_id is not None
                else None
            )
            duplicate_matches_effective = bool(
                isinstance(current_effective, Mapping)
                and current_effective.get("artifact_content_hash") == digest
            )
            if (
                validation_state == "VALID"
                and current_effective_id is not None
                and not duplicate_matches_effective
                and supersedes_import_event_id is None
            ):
                validation_state = "HOLD_SUPERSESSION_REQUIRED"
            elif (
                validation_state == "VALID"
                and supersedes_import_event_id is not None
                and isinstance(golden_output, Mapping)
                and golden_output.get("frozen") is True
            ):
                validation_state = (
                    "HOLD_FROZEN_GOLDEN_REQUIRES_FORWARD_ONLY_MANIFEST"
                )
            record = {
                "artifact_authored_at": _clean_single_line_scalar(
                    envelope.get("artifact_authored_at")
                ),
                "artifact_content_hash": artifact_hash,
                "artifact_size_bytes": len(payload),
                "as_of_commit": as_of_commit,
                "authority_state": authority,
                "claimed_as_of_commit": claimed_as_of,
                "content_addressed_path": content_path,
                "declared_role": declared_role,
                "duplicate_of_import_event_id": duplicate_of,
                "evidence_packet_commit": evidence_commit,
                "evidence_packet_blob_sha": evidence_blob_sha,
                "evidence_packet_sha256": evidence_sha256,
                "evidence_packet_path": evidence_path,
                "evidence_packet_product_as_of_commit": (
                    evidence_product_as_of
                ),
                "findings": envelope.get("findings", []),
                "framework_lens_used": _clean_scalar(
                    envelope.get("framework_lens_used")
                ),
                "human_execution_cost": envelope.get(
                    "human_execution_cost",
                    [],
                ),
                "import_event_id": event_id,
                "import_mode": import_mode,
                "imported_at": imported_at,
                "metadata_source": metadata_source,
                "missing_required_fields": missing,
                "model_identity": {
                    "basis": _clean_single_line_scalar(model.get("basis")),
                    "claimed_verification_state": claimed_verification,
                    "value": _clean_single_line_scalar(model.get("value")),
                    "verification_state": verification,
                },
                "objective": envelope.get("objective", UNKNOWN),
                "completion_line": envelope.get("completion_line", UNKNOWN),
                "do_not_touch": envelope.get("do_not_touch", UNKNOWN),
                "current_gate": envelope.get("current_gate", UNKNOWN),
                "authority_boundary": envelope.get(
                    "authority_boundary",
                    UNKNOWN,
                ),
                "protocol_run_id": protocol_run_id,
                "reusable_delta": envelope.get("reusable_delta", []),
                "required_next_actor": _clean_single_line_scalar(
                    envelope.get("required_next_actor")
                ),
                "role_identity": _clean_single_line_scalar(
                    envelope.get("role_identity")
                ),
                "schema": SCHEMA,
                "selected_role": selected_role,
                "session_id": session["session_id"],
                "source_path_or_label": source_path_or_label,
                "supersedes_import_event_id": (
                    supersedes_import_event_id or UNKNOWN
                ),
                "correction_reason": correction_reason or UNKNOWN,
                "forward_only_delta_linkage": (
                    self._new_id()
                    if supersedes_import_event_id is not None
                    else UNKNOWN
                ),
                "task_id": task_id,
                "unknowns": envelope.get("unknowns", [UNKNOWN]),
                "validation_state": validation_state,
            }
            event = self._append(
                (
                    "ARTIFACT_IMPORT_DUPLICATE"
                    if duplicate_of
                    else "ARTIFACT_IMPORTED"
                ),
                {
                    "artifact_sha256": artifact_hash,
                    "declared_role": declared_role,
                    "import_mode": import_mode,
                    "selected_role": selected_role,
                    "session_id": session["session_id"],
                    "source_path_or_label": source_path_or_label,
                    "supersedes_import_event_id": (
                        supersedes_import_event_id or UNKNOWN
                    ),
                    "validation_state": validation_state,
                },
                event_id=event_id,
                recorded_at=imported_at,
            )
            record["event_hash"] = event["event_hash"]
            self.store.save_import(record)
            session["imports"].append(event_id)
            exact_file_mode_upgrade = bool(
                validation_state == "VALID"
                and duplicate_matches_effective
                and isinstance(current_effective, Mapping)
                and current_effective.get("import_mode") == "PASTE_CAPTURE"
                and import_mode == "BYTE_EXACT_FILE_IMPORT"
            )
            effective_changed = validation_state == "VALID" and (
                current_effective_id is None
                or supersedes_import_event_id is not None
                or exact_file_mode_upgrade
            )
            if effective_changed:
                session["effective_by_role"][selected_role] = event_id
            if supersedes_import_event_id is not None:
                self._increment(
                    session,
                    "shin_boundary_correction_count",
                    event_id,
                )
            self._increment(
                session,
                "shin_manual_transfer_count",
                event_id,
            )
            if import_mode == "PASTE_CAPTURE":
                self._increment(
                    session,
                    "shin_copy_paste_count",
                    event_id,
                )
            state_by_role = {
                "PRO_DESIGN": "DESIGN_IMPORTED",
                "BUILD_RECEIPT": "BUILD_RECEIPT_IMPORTED",
                "PRO_AUDIT": "AUDIT_IMPORTED",
                "REUSABLE_DELTA_RECORD": "DELTA_IMPORTED",
            }
            if selected_role in state_by_role and effective_changed:
                session["state"] = state_by_role[selected_role]
                session["hold_reason"] = None
            elif validation_state != "VALID":
                session["hold_reason"] = (
                    validation_state
                )
            self._save_session(session)
            return self.snapshot()

    def _effective_import(
        self,
        session: Mapping[str, Any],
        role: str,
    ) -> dict[str, Any] | None:
        import_id = session["effective_by_role"].get(role)
        if import_id is None:
            return None
        record = self.store.load_import(import_id)
        if (
            record.get("validation_state") != "VALID"
            or record.get("selected_role") != role
            or record.get("declared_role") != role
        ):
            return None
        return record

    def generate_execution_handoff(self) -> dict[str, Any]:
        with self.store.transaction():
            session = self._require_session()
            boundary = session["boundary"]
            design = self._effective_import(session, "PRO_DESIGN")
            if not session["boundary_complete"]:
                raise ManualBridgeConflictError(
                    session.get("hold_reason") or "HOLD — INCOMPLETE BOUNDARY"
                )
            if design is None or design.get("validation_state") != "VALID":
                raise ManualBridgeConflictError(
                    "A valid frozen Pro Design import is required."
                )
            evidence = boundary["evidence_packet_identity"]
            if (
                design["selected_role"] != "PRO_DESIGN"
                or design["declared_role"] != "PRO_DESIGN"
                or design["authority_state"]
                != "DESIGN_ONLY_NO_EXECUTION_AUTHORITY"
                or design["task_id"] != boundary["task_id"]
                or design["protocol_run_id"] != boundary["protocol_run_id"]
                or design["as_of_commit"] != boundary["as_of_commit"]
                or design["evidence_packet_commit"] != evidence["commit"]
                or design["evidence_packet_blob_sha"] != evidence["blob_sha"]
                or design["evidence_packet_sha256"] != evidence["sha256"]
            ):
                raise ManualBridgeConflictError(
                    "Pro Design identity or authority does not match the session."
                )
            repo_root = str(self.repository)
            current_state = _clean_scalar(boundary.get("current_state"))
            if current_state == UNKNOWN:
                current_state = (
                    "Accepted Pro Design imported and locally frozen; "
                    "Builder authority remains a separate human Seat action."
                )
            active_branch = _clean_scalar(boundary.get("active_branch"))
            missing_closure = _clean_scalar(boundary.get("missing_closure"))
            if missing_closure == UNKNOWN:
                missing_closure = (
                    "Separate Builder authority, bounded implementation, Build "
                    "Receipt, independent Pro Audit, and later Replay remain open."
                )
            next_action = (
                "Shin may separately grant a fresh Builder the bounded "
                "implementation task defined by this handoff. Until that separate "
                "grant exists, no implementation action is authorized."
            )
            receiving_owns = _clean_scalar(
                boundary.get("what_receiving_ai_owns")
            )
            if receiving_owns == UNKNOWN:
                receiving_owns = (
                    f"Only the bounded implementation objective: "
                    f"{boundary['objective']}"
                )
            first_action = _clean_scalar(boundary.get("first_one_action"))
            if first_action == UNKNOWN:
                first_action = (
                    "Verify repository, Evidence Packet, and exact Pro Design "
                    "identities before any implementation action."
                )
            do_not_continue = _clean_scalar(
                boundary.get("do_not_continue_boundary")
            )
            if do_not_continue == UNKNOWN:
                do_not_continue = (
                    "Do not infer authority from this artifact; do not merge, "
                    "publish, release, audit your own build, or expand scope."
                )
            not_returned = (
                "Routine Git, tests, fixtures, hashing, app build, smoke, receipt, "
                "PR, and cleanup work that the authorized Builder can complete."
            )
            values = (
                ("Target Layer", "V13 — Compound Loop / Stage 2 Manual Bridge"),
                ("Repo Root", repo_root),
                ("Current State", current_state),
                ("Current Gate", "HOLD — SEPARATE BUILDER AUTHORITY REQUIRED"),
                ("Active Branch", active_branch),
                ("Next Authorized Action", next_action),
                ("Completion Line", boundary["completion_line"]),
                ("Missing Closure", missing_closure),
                ("Next Owner", boundary["required_next_actor"]),
                ("What the Receiving AI Now Owns", receiving_owns),
                ("First One Action", first_action),
                ("Do Not Continue Boundary", do_not_continue),
                (
                    "What must not be returned to the Decision Owner",
                    not_returned,
                ),
            )
            sections = [
                "# Companion Manual Bridge v0.1 — Execution Handoff",
                "",
            ]
            for label, value in values:
                sections.extend((f"## {label}", "", value, ""))
            evidence_identity = (
                f"commit={evidence['commit']}; path={evidence['path']}; "
                f"blob={evidence['blob_sha']}; sha256={evidence['sha256']}"
            )
            identity_values = (
                ("Task ID", boundary["task_id"]),
                ("Protocol Run ID", boundary["protocol_run_id"]),
                ("Evidence Packet identity", evidence_identity),
                (
                    "Pro Design artifact hash",
                    design["artifact_content_hash"],
                ),
                (
                    "Pro Design model identity",
                    (
                        f"{design['model_identity']['value']} "
                        f"({design['model_identity']['basis']} / "
                        f"{design['model_identity']['verification_state']})"
                    ),
                ),
                ("Pro Design role identity", design["role_identity"]),
                ("Pro Design time anchor", design["artifact_authored_at"]),
                ("Handoff hash", "EXTERNALLY_FIXED_ON_FREEZE"),
                ("Authority state", "INSTRUCTION_ARTIFACT_ONLY"),
            )
            sections.extend(("## Identity Block", ""))
            for label, value in identity_values:
                sections.extend((f"{label}:", str(value), ""))
            sections.extend(
                (
                    "Bootstrap status:",
                    "GENERATED AFTER BUILDER AUTHORITY FOR PRODUCT VALIDATION",
                    "",
                    "Authority:",
                    "INSTRUCTION_ARTIFACT_ONLY",
                    "",
                    "Historical implication:",
                    "DOES NOT RETROACTIVELY AUTHORIZE CODEX 13-25",
                    "",
                    "This generated handoff is an instruction artifact only. "
                    "Its hash, role, model identity, or existence grants no "
                    "execution, merge, publication, or release authority.",
                    "",
                )
            )
            payload = "\n".join(sections).encode("utf-8")
            rendered_handoff = payload.decode("utf-8")
            for field in HANDOFF_FIELDS:
                if rendered_handoff.count(f"## {field}\n") != 1:
                    raise ManualBridgeIntegrityError(
                        "Generated handoff has an invalid required-field structure."
                    )
            generated = self._set_output(
                session,
                "EXECUTION_HANDOFF",
                "execution_handoff.md",
                payload,
                "EXECUTION_HANDOFF_GENERATED",
            )
            if not generated:
                return self.snapshot()
            session = self._require_session()
            session["state"] = "HANDOFF_GENERATED"
            self._save_session(session)
            return self.snapshot()

    def freeze_output(self, role: str) -> dict[str, Any]:
        if role not in GENERATED_ROLES:
            raise ManualBridgeValidationError(
                "Only a generated Bridge artifact can be frozen."
            )
        with self.store.transaction():
            session = self._require_session()
            output = session["outputs"].get(role)
            if not isinstance(output, dict):
                raise ManualBridgeValidationError(
                    "Generate the Bridge artifact before freezing it."
                )
            raw = self.store.read_output(output["path"])
            if sha256_bytes(raw) != output["sha256"]:
                raise ManualBridgeIntegrityError(
                    "Generated Bridge output changed before freeze."
                )
            if role == "EXECUTION_HANDOFF":
                text = raw.decode("utf-8")
                missing = [
                    field
                    for field in HANDOFF_FIELDS
                    if text.count(f"## {field}\n") != 1
                ]
                if missing:
                    raise ManualBridgeConflictError(
                        "Execution Handoff required fields are missing."
                    )
            if (
                role == "GOLDEN_MANIFEST"
                and (session.get("golden_manifest") or {}).get("golden_status")
                != "GOLDEN_ELIGIBLE"
            ):
                raise ManualBridgeConflictError(
                    "An incomplete Golden manifest cannot be frozen."
                )
            if role == "GOLDEN_MANIFEST":
                manifest = session.get("golden_manifest")
                try:
                    output_manifest = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ManualBridgeIntegrityError(
                        "Golden manifest output is invalid."
                    ) from exc
                if (
                    not isinstance(manifest, Mapping)
                    or output_manifest != manifest
                    or not self._manifest_matches_current_effective(
                        session,
                        manifest,
                    )
                ):
                    raise ManualBridgeIntegrityError(
                        "Golden manifest is not bound to current fixed inputs."
                    )
            if output.get("frozen"):
                return self.snapshot()
            event = self._append(
                "GENERATED_ARTIFACT_FROZEN",
                {
                    "artifact_role": role,
                    "artifact_sha256": output["sha256"],
                    "session_id": session["session_id"],
                    "size_bytes": output["size_bytes"],
                },
            )
            output["freeze_event_id"] = event["event_id"]
            output["frozen"] = True
            if role == "EXECUTION_HANDOFF":
                session["state"] = "HANDOFF_FROZEN"
            elif role == "GOLDEN_MANIFEST":
                session["state"] = "GOLDEN_FROZEN"
            elif role == "REPLAY_RESULT":
                session["state"] = "REPLAY_RECORDED"
            self._save_session(session)
            return self.snapshot()

    def _receipt_payload(
        self,
        session: Mapping[str, Any],
    ) -> dict[str, Any]:
        imports = [
            self.store.load_import(import_id)
            for import_id in session["imports"]
        ]
        identities = [
            {
                "artifact_content_hash": record["artifact_content_hash"],
                "artifact_role": record["selected_role"],
                "authority_state": record["authority_state"],
                "import_event_id": record["import_event_id"],
                "source_path_or_label": record["source_path_or_label"],
            }
            for record in imports
        ]
        findings: list[Any] = []
        deltas: list[Any] = []
        unknowns: list[Any] = []
        for record in imports:
            value = record.get("findings")
            findings.extend(value if isinstance(value, list) else [value])
            value = record.get("reusable_delta")
            deltas.extend(value if isinstance(value, list) else [value])
            value = record.get("unknowns")
            unknowns.extend(value if isinstance(value, list) else [value])
        findings = [value for value in findings if value not in (None, "")]
        deltas = [value for value in deltas if value not in (None, "")]
        unknowns = [value for value in unknowns if value not in (None, "")]
        if not unknowns:
            unknowns = [UNKNOWN]
        event_ids = [record["import_event_id"] for record in imports]
        body = {
            "artifact_identities": identities,
            "claim_boundary": (
                "Local artifact-chain and observation record; not third-party "
                "certification, task correctness proof, model verification, "
                "merge approval, or burden-reduction proof."
            ),
            "cost_observations": session["burden"],
            "findings": findings or [UNKNOWN],
            "protocol_product_replay_results": session["results"],
            "receipt_type": "COMPANION_MANUAL_BRIDGE_V0_1",
            "referenced_import_event_ids": event_ids,
            "reusable_delta_records": deltas or [UNKNOWN],
            "schema": SCHEMA,
            "session_id": session["session_id"],
            "unknowns": unknowns,
        }
        body["receipt_id"] = sha256_bytes(_canonical_json(body))
        return body

    def generate_bridge_receipt(self) -> dict[str, Any]:
        with self.store.transaction():
            session = self._require_session()
            receipt = self._receipt_payload(session)
            pretty = json.dumps(
                receipt,
                allow_nan=False,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            text = (
                "# Companion Manual Bridge v0.1 — Finding / Cost / "
                "Reusable Delta Receipt\n\n"
                "```json\n"
                f"{pretty}\n"
                "```\n\n"
                "This receipt is separate from the existing Verified Save/Reuse "
                "Receipt. Configured estimates are not measured Golden burden.\n\n"
                "It grants no execution, audit, merge, publication, release, "
                "Protocol PASS, Product PASS, or Replay PASS authority.\n"
            )
            self._set_output(
                session,
                "BRIDGE_RECEIPT",
                "bridge_receipt.md",
                text.encode("utf-8"),
                "BRIDGE_RECEIPT_GENERATED",
            )
            return self.snapshot()

    @staticmethod
    def _missing_manifest_entry(role: str) -> dict[str, Any]:
        return {
            "artifact_authored_at": UNKNOWN,
            "artifact_hash": UNKNOWN,
            "artifact_role": role,
            "artifact_sha256": UNKNOWN,
            "as_of_commit": UNKNOWN,
            "authority_state": UNKNOWN,
            "fixation_commit_or_unknown": UNKNOWN,
            "git_blob_sha_or_unknown": UNKNOWN,
            "import_event_id": UNKNOWN,
            "imported_at": UNKNOWN,
            "model_identity": UNKNOWN,
            "model_identity_basis": UNKNOWN,
            "reason": "NOT_YET_PRODUCED",
            "repository_path_or_source_label": UNKNOWN,
            "role_identity": UNKNOWN,
            "result_boundary": (
                "Golden is a frozen comparison source only; not correctness, "
                "certification, authority, or PASS."
            ),
            "state": "MISSING",
            "supersedes": UNKNOWN,
            "unknowns": [UNKNOWN],
        }

    def _golden_replay_baseline(
        self,
        session: Mapping[str, Any],
        entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        by_role = {
            entry["artifact_role"]: entry
            for entry in entries
            if isinstance(entry, Mapping)
        }
        record_roles = (
            "PRO_DESIGN",
            "BUILD_RECEIPT",
            "PRO_AUDIT",
            "REUSABLE_DELTA_RECORD",
        )
        records: list[tuple[str, dict[str, Any]]] = []
        for role in record_roles:
            record = self._effective_import(session, role)
            entry = by_role.get(role)
            if (
                record is None
                or not isinstance(entry, Mapping)
                or entry.get("state") != "FROZEN"
                or entry.get("artifact_sha256")
                != record.get("artifact_content_hash")
            ):
                raise ManualBridgeIntegrityError(
                    "Golden Replay baseline source is not fixed."
                )
            records.append((role, record))

        prefixes = {
            "task_id": "TASK",
            "objective": "OBJ",
            "completion_line": "CL",
            "do_not_touch": "DNT",
            "current_gate": "GATE",
            "authority_boundary": "AUTH",
            "as_of_identity": "ASOF",
            "model_identity": "MODEL",
            "role_identity": "ROLE",
            "time_anchor": "TIME",
            "required_next_actor": "ACTOR",
            "findings": "FIND",
            "human_execution_cost": "COST",
            "reusable_delta": "DELTA",
            "unknowns": "UNK",
        }

        def usable(value: Any) -> bool:
            if value is None:
                return False
            if isinstance(value, str):
                return not _is_unknown(value)
            if isinstance(value, (list, tuple, Mapping)):
                return len(value) > 0
            return True

        def atom(
            field_id: str,
            role: str,
            record: Mapping[str, Any],
            location: str,
            value: Any,
            ordinal: int,
        ) -> dict[str, Any]:
            return {
                "atom_id": (
                    f"{prefixes[field_id]}-{role.replace('_', '-')}-{ordinal:03d}"
                ),
                "source_artifact_hash": record["artifact_content_hash"],
                "source_location": location,
                "value": value,
            }

        fields: dict[str, dict[str, Any]] = {}
        scalar_sources = {
            "task_id": ("task_id", "$.task_id"),
            "objective": ("objective", "$.objective"),
            "completion_line": ("completion_line", "$.completion_line"),
            "do_not_touch": ("do_not_touch", "$.do_not_touch"),
            "current_gate": ("current_gate", "$.current_gate"),
            "authority_boundary": (
                "authority_boundary",
                "$.authority_boundary",
            ),
            "as_of_identity": ("as_of_commit", "$.as_of_commit"),
            "model_identity": ("model_identity", "$.model_identity"),
            "role_identity": ("role_identity", "$.role_identity"),
            "time_anchor": (
                "artifact_authored_at",
                "$.artifact_authored_at",
            ),
            "required_next_actor": (
                "required_next_actor",
                "$.required_next_actor",
            ),
        }
        for field_id, (record_key, location) in scalar_sources.items():
            field_atoms = [
                atom(
                    field_id,
                    role,
                    record,
                    location,
                    record.get(record_key, UNKNOWN),
                    index,
                )
                for index, (role, record) in enumerate(records, start=1)
                if usable(record.get(record_key))
            ]
            if not field_atoms:
                role, record = records[0]
                field_atoms = [
                    atom(
                        field_id,
                        role,
                        record,
                        location,
                        UNKNOWN,
                        1,
                    )
                ]
            fields[field_id] = {"atoms": field_atoms}

        collection_sources = {
            "findings": ("findings", "$.findings"),
            "human_execution_cost": (
                "human_execution_cost",
                "$.human_execution_cost",
            ),
            "reusable_delta": ("reusable_delta", "$.reusable_delta"),
            "unknowns": ("unknowns", "$.unknowns"),
        }
        for field_id, (record_key, location) in collection_sources.items():
            field_atoms: list[dict[str, Any]] = []
            ordinal = 1
            for role, record in records:
                value = record.get(record_key)
                if not usable(value):
                    continue
                values = value if isinstance(value, list) else [value]
                for index, item in enumerate(values):
                    field_atoms.append(
                        atom(
                            field_id,
                            role,
                            record,
                            f"{location}[{index}]"
                            if isinstance(value, list)
                            else location,
                            item,
                            ordinal,
                        )
                    )
                    ordinal += 1
            if not field_atoms:
                role, record = records[0]
                field_atoms = [
                    atom(
                        field_id,
                        role,
                        record,
                        location,
                        UNKNOWN,
                        1,
                    )
                ]
            fields[field_id] = {"atoms": field_atoms}

        baseline = {
            "fields": fields,
            "protocol_run_id": session["boundary"]["protocol_run_id"],
            "schema": REPLAY_BASELINE_SCHEMA,
            "task_id": session["boundary"]["task_id"],
        }
        if set(fields) != set(REPLAY_FIELDS):
            raise ManualBridgeIntegrityError(
                "Golden Replay baseline field set is incomplete."
            )
        return baseline

    def generate_golden_manifest(self) -> dict[str, Any]:
        with self.store.transaction():
            session = self._require_session()
            boundary = session["boundary"]
            evidence = boundary["evidence_packet_identity"]
            entries: list[dict[str, Any]] = []
            for role in GOLDEN_ROLES:
                entry = self._missing_manifest_entry(role)
                if role == "EVIDENCE_PACKET" and self._evidence_matches(boundary):
                    entry.update(
                        {
                            "artifact_hash": evidence["sha256"],
                            "artifact_sha256": evidence["sha256"],
                            "artifact_role": role,
                            "as_of_commit": evidence["product_as_of_commit"],
                            "authority_state": "EVIDENCE_ONLY",
                            "git_blob_sha_or_unknown": evidence["blob_sha"],
                            "import_event_id": "FROZEN_EVIDENCE_INPUT",
                            "repository_path_or_source_label": evidence["path"],
                            "role_identity": "Scout Evidence Recorder",
                            "state": "FROZEN",
                            "unknowns": [UNKNOWN],
                        }
                    )
                    entry.pop("reason", None)
                elif role == "EXECUTION_HANDOFF":
                    output = session["outputs"].get(role)
                    if output and output.get("frozen"):
                        entry.update(
                            {
                                "artifact_hash": output["sha256"],
                                "artifact_sha256": output["sha256"],
                                "artifact_role": role,
                                "as_of_commit": boundary["as_of_commit"],
                                "authority_state": "INSTRUCTION_ARTIFACT_ONLY",
                                "import_event_id": output["freeze_event_id"],
                                "model_identity": "SYSTEM_GENERATED",
                                "model_identity_basis": (
                                    "DETERMINISTIC_GENERATOR"
                                ),
                                "repository_path_or_source_label": output["path"],
                                "role_identity": (
                                    "Companion Manual Bridge v0.1"
                                ),
                                "state": "FROZEN",
                            }
                        )
                        entry.pop("reason", None)
                else:
                    imported = self._effective_import(session, role)
                    if (
                        imported is not None
                        and imported.get("import_mode")
                        == "BYTE_EXACT_FILE_IMPORT"
                    ):
                        entry.update(
                            {
                                "artifact_authored_at": imported[
                                    "artifact_authored_at"
                                ],
                                "artifact_hash": imported[
                                    "artifact_content_hash"
                                ],
                                "artifact_sha256": imported[
                                    "artifact_content_hash"
                                ],
                                "artifact_role": role,
                                "as_of_commit": imported["as_of_commit"],
                                "authority_state": imported["authority_state"],
                                "import_event_id": imported["import_event_id"],
                                "imported_at": imported["imported_at"],
                                "model_identity": imported[
                                    "model_identity"
                                ]["value"],
                                "model_identity_basis": imported[
                                    "model_identity"
                                ]["basis"],
                                "repository_path_or_source_label": imported[
                                    "source_path_or_label"
                                ],
                                "role_identity": imported["role_identity"],
                                "state": "FROZEN",
                                "supersedes": imported[
                                    "supersedes_import_event_id"
                                ],
                                "unknowns": imported["unknowns"],
                            }
                        )
                        entry.pop("reason", None)
                    elif imported is not None:
                        entry["reason"] = (
                            "PASTE_CAPTURE_NOT_GOLDEN_ELIGIBLE"
                        )
                entries.append(entry)
            complete = (
                all(entry["state"] == "FROZEN" for entry in entries)
                and not session.get("hold_reason")
                and session.get("state") != "BLOCKED_AUTHORITY_INFLATION"
            )
            replay_baseline = (
                self._golden_replay_baseline(session, entries)
                if complete
                else None
            )
            manifest = {
                "artifact_order": list(GOLDEN_ROLES),
                "artifacts": entries,
                "golden_status": (
                    "GOLDEN_ELIGIBLE" if complete else "GOLDEN_INCOMPLETE"
                ),
                "golden_status_claim_boundary": (
                    "Golden means frozen comparison source only. It does not "
                    "mean correct, PASS, approved, certified, or authorized."
                ),
                "protocol_run_id": boundary["protocol_run_id"],
                "replay_baseline": replay_baseline,
                "replay_baseline_sha256": (
                    sha256_bytes(_canonical_json(replay_baseline))
                    if replay_baseline is not None
                    else UNKNOWN
                ),
                "schema": SCHEMA,
                "task_id": boundary["task_id"],
            }
            payload = _json_document(manifest)
            generated = self._set_output(
                session,
                "GOLDEN_MANIFEST",
                "golden_manifest.json",
                payload,
                "GOLDEN_MANIFEST_GENERATED",
            )
            if not generated:
                # Output bytes and their append-only event are persisted before
                # the materialized manifest projection.  Reconcile the latter
                # on retry so an interruption between those two writes cannot
                # strand an otherwise valid deterministic manifest.
                session = self._require_session()
                stored_manifest = session.get("golden_manifest")
                if stored_manifest is None:
                    session["golden_manifest"] = manifest
                    manifest_output = session["outputs"]["GOLDEN_MANIFEST"]
                    session["state"] = (
                        "GOLDEN_FROZEN"
                        if manifest_output.get("frozen") is True
                        else (
                            "GOLDEN_ELIGIBLE"
                            if complete
                            else "GOLDEN_INCOMPLETE"
                        )
                    )
                    self._save_session(session)
                elif stored_manifest != manifest:
                    raise ManualBridgeIntegrityError(
                        "Golden manifest projection conflicts with fixed output."
                    )
                return self.snapshot()
            session = self._require_session()
            session["golden_manifest"] = manifest
            session["state"] = (
                "GOLDEN_ELIGIBLE" if complete else "GOLDEN_INCOMPLETE"
            )
            self._save_session(session)
            return self.snapshot()

    def _manifest_matches_current_effective(
        self,
        session: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> bool:
        entries = manifest.get("artifacts")
        if (
            not isinstance(entries, list)
            or len(entries) != len(GOLDEN_ROLES)
            or not all(isinstance(entry, Mapping) for entry in entries)
            or [entry.get("artifact_role") for entry in entries]
            != list(GOLDEN_ROLES)
        ):
            return False
        by_role = {
            entry["artifact_role"]: entry
            for entry in entries
            if isinstance(entry, Mapping)
        }
        evidence = session.get("boundary", {}).get(
            "evidence_packet_identity",
            {},
        )
        evidence_entry = by_role.get("EVIDENCE_PACKET", {})
        if (
            evidence_entry.get("artifact_sha256") != evidence.get("sha256")
            or evidence_entry.get("repository_path_or_source_label")
            != evidence.get("path")
            or evidence_entry.get("import_event_id")
            != "FROZEN_EVIDENCE_INPUT"
        ):
            return False
        handoff = session.get("outputs", {}).get("EXECUTION_HANDOFF")
        handoff_entry = by_role.get("EXECUTION_HANDOFF", {})
        if (
            not isinstance(handoff, Mapping)
            or handoff.get("frozen") is not True
            or handoff_entry.get("artifact_sha256") != handoff.get("sha256")
            or handoff_entry.get("import_event_id")
            != handoff.get("freeze_event_id")
        ):
            return False
        for role in (
            "PRO_DESIGN",
            "BUILD_RECEIPT",
            "PRO_AUDIT",
            "REUSABLE_DELTA_RECORD",
        ):
            effective_id = session.get("effective_by_role", {}).get(role)
            entry = by_role.get(role, {})
            if (
                not isinstance(effective_id, str)
                or entry.get("import_event_id") != effective_id
            ):
                return False
            record = self.store.load_import(effective_id)
            if (
                record.get("validation_state") != "VALID"
                or record.get("import_mode") != "BYTE_EXACT_FILE_IMPORT"
                or entry.get("artifact_sha256")
                != record.get("artifact_content_hash")
                or entry.get("authority_state")
                != record.get("authority_state")
            ):
                return False
        if not all(
            by_role[role].get("state") == "FROZEN"
            for role in GOLDEN_ROLES
        ):
            return False
        try:
            expected_baseline = self._golden_replay_baseline(
                session,
                entries,
            )
        except ManualBridgeError:
            return False
        return (
            manifest.get("replay_baseline") == expected_baseline
            and manifest.get("replay_baseline_sha256")
            == sha256_bytes(_canonical_json(expected_baseline))
        )

    @staticmethod
    def _field_map(value: Mapping[str, Any]) -> Mapping[str, Any]:
        fields = value.get("fields")
        return fields if isinstance(fields, Mapping) else value

    @staticmethod
    def _atoms(field: Any) -> list[dict[str, Any]]:
        if not isinstance(field, Mapping):
            return []
        atoms = field.get("atoms")
        if not isinstance(atoms, list):
            return []
        required = {
            "atom_id",
            "value",
            "source_artifact_hash",
            "source_location",
        }
        return [
            dict(atom)
            for atom in atoms
            if isinstance(atom, Mapping)
            and required.issubset(atom)
            and isinstance(atom.get("atom_id"), str)
            and bool(atom["atom_id"])
            and isinstance(atom.get("source_artifact_hash"), str)
            and bool(atom["source_artifact_hash"])
            and isinstance(atom.get("source_location"), str)
            and bool(atom["source_location"])
        ]

    @staticmethod
    def _field_unknown(field: Any) -> bool:
        if not isinstance(field, Mapping):
            return False
        if str(field.get("state", "")).upper() == "UNKNOWN":
            return True
        atoms = BridgeSessionController._atoms(field)
        return bool(atoms) and all(_is_unknown(atom.get("value")) for atom in atoms)

    @staticmethod
    def _has_forward_only_delta(field: Any) -> bool:
        if not isinstance(field, Mapping):
            return False
        linkage = field.get("forward_only_delta")
        if not isinstance(linkage, Mapping):
            return False
        delta_id = linkage.get("delta_id")
        source_hash = linkage.get("source_artifact_hash")
        return bool(
            isinstance(delta_id, str)
            and delta_id.strip()
            and len(delta_id) <= 200
            and "\n" not in delta_id
            and "\r" not in delta_id
            and "\x00" not in delta_id
            and isinstance(source_hash, str)
            and _SHA256.fullmatch(source_hash)
        )

    @staticmethod
    def _candidate_authority_inflated(
        field_id: str,
        baseline: Any,
        candidate: Any,
    ) -> bool:
        if not isinstance(candidate, Mapping):
            return False
        if (
            candidate.get("authority_inflated") is True
            or candidate.get("status") == "AUTHORITY-INFLATED"
        ):
            return True
        if field_id not in {"authority_boundary", "current_gate"}:
            return False
        baseline_text = " ".join(
            str(atom.get("value", ""))
            for atom in BridgeSessionController._atoms(baseline)
        ).upper()
        candidate_text = " ".join(
            str(atom.get("value", ""))
            for atom in BridgeSessionController._atoms(candidate)
        ).upper()
        inflated_tokens = (
            "MERGE AUTHORITY",
            "PUBLICATION AUTHORITY",
            "RELEASE AUTHORITY",
            "EXECUTION AUTHORITY GRANTED",
            "PRODUCT PASS",
            "PROTOCOL PASS",
            "REPLAY PASS",
            "AUTO-MERGE",
        )
        if any(
            token in candidate_text and token not in baseline_text
            for token in inflated_tokens
        ):
            return True
        candidate_words = set(re.findall(r"[A-Z]+", candidate_text))
        baseline_words = set(re.findall(r"[A-Z]+", baseline_text))
        privileged = {
            "IMPLEMENTATION",
            "EXECUTION",
            "MERGE",
            "PUBLICATION",
            "PUBLISH",
            "RELEASE",
        }
        grant_words = {"AUTHORIZE", "AUTHORIZED", "AUTHORITY", "GRANT", "GO"}
        return bool(
            candidate_words & privileged
            and candidate_words & grant_words
            and (
                (candidate_words & privileged)
                - (baseline_words & privileged)
            )
        )

    @classmethod
    def compare_replay(
        cls,
        baseline: Mapping[str, Any],
        candidate: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(baseline, Mapping) or not isinstance(
            candidate,
            Mapping,
        ):
            raise ManualBridgeValidationError(
                "Replay baseline and candidate must be objects."
            )
        baseline_fields = cls._field_map(baseline)
        candidate_fields = cls._field_map(candidate)
        results: list[dict[str, Any]] = []
        for field_id in REPLAY_FIELDS:
            before = baseline_fields.get(field_id)
            after = candidate_fields.get(field_id)
            status: str
            reason: str
            if isinstance(before, Mapping) and str(
                before.get("state", "")
            ).upper().replace("_", " ") == "NOT APPLICABLE":
                if (
                    isinstance(after, Mapping)
                    and str(after.get("state", "")).upper().replace("_", " ")
                    == "NOT APPLICABLE"
                    and before.get("reason") == after.get("reason")
                    and before.get("reason")
                ):
                    status = "NOT APPLICABLE"
                    reason = "Explicit non-applicability reason was preserved."
                else:
                    status = "MISSING" if after is None else "ALTERED"
                    reason = "Non-applicability evidence was not preserved."
            elif cls._field_unknown(before):
                if cls._field_unknown(after):
                    status = "UNKNOWN"
                    reason = "The unresolved state remained explicitly UNKNOWN."
                elif cls._has_forward_only_delta(after):
                    status = "PRESERVED"
                    reason = "UNKNOWN was resolved by an explicit Forward-only Delta."
                else:
                    status = "ALTERED"
                    reason = "Baseline UNKNOWN was upgraded without a Delta."
            elif cls._candidate_authority_inflated(
                field_id,
                before,
                after,
            ):
                status = "AUTHORITY-INFLATED"
                reason = "Candidate authority exceeds the baseline boundary."
            else:
                before_atoms = cls._atoms(before)
                after_atoms = cls._atoms(after)
                before_raw_atoms = (
                    before.get("atoms")
                    if isinstance(before, Mapping)
                    else None
                )
                after_raw_atoms = (
                    after.get("atoms")
                    if isinstance(after, Mapping)
                    else None
                )
                before_ids = [
                    atom["atom_id"] for atom in before_atoms
                ]
                after_ids = [
                    atom["atom_id"] for atom in after_atoms
                ]
                if (
                    isinstance(before_raw_atoms, list)
                    and len(before_atoms) != len(before_raw_atoms)
                ):
                    status = "UNKNOWN"
                    reason = "Baseline contains an invalid structural atom."
                elif (
                    isinstance(after_raw_atoms, list)
                    and len(after_atoms) != len(after_raw_atoms)
                ):
                    status = "ALTERED"
                    reason = "Candidate contains an invalid structural atom."
                elif len(before_ids) != len(set(before_ids)):
                    status = "UNKNOWN"
                    reason = "Baseline atom identities are not unique."
                elif len(after_ids) != len(set(after_ids)):
                    status = "ALTERED"
                    reason = "Candidate atom identities are not unique."
                elif not before_atoms:
                    status = "UNKNOWN"
                    reason = "Baseline structural atoms are unavailable."
                elif not after_atoms:
                    status = "MISSING"
                    reason = "Candidate has no typed structural atoms."
                else:
                    before_by_id = {
                        atom.get("atom_id"): atom
                        for atom in before_atoms
                        if atom.get("atom_id")
                    }
                    after_by_id = {
                        atom.get("atom_id"): atom
                        for atom in after_atoms
                        if atom.get("atom_id")
                    }
                    missing_ids = set(before_by_id) - set(after_by_id)
                    additional_ids = set(after_by_id) - set(before_by_id)
                    explicit_forward_addition = bool(
                        field_id in {"findings", "reusable_delta"}
                        and cls._has_forward_only_delta(after)
                    )
                    if additional_ids and not explicit_forward_addition:
                        status = "ALTERED"
                        reason = (
                            "Candidate adds unlinked structural atoms outside "
                            "the fixed baseline."
                        )
                    elif missing_ids:
                        before_sources = {
                            atom.get("source_artifact_hash")
                            for atom in before_atoms
                        }
                        after_sources = {
                            atom.get("source_artifact_hash")
                            for atom in after_atoms
                        }
                        if after_sources and after_sources != before_sources:
                            status = "SUBSTITUTED"
                            reason = "Candidate uses a different source identity."
                        else:
                            status = "MISSING"
                            reason = "A required baseline atom is absent."
                    else:
                        changed = False
                        substituted = False
                        for atom_id, before_atom in before_by_id.items():
                            after_atom = after_by_id[atom_id]
                            if (
                                before_atom.get("source_artifact_hash")
                                != after_atom.get("source_artifact_hash")
                                or before_atom.get("source_location")
                                != after_atom.get("source_location")
                            ):
                                substituted = True
                            elif before_atom.get("value") != after_atom.get("value"):
                                changed = True
                        if substituted:
                            status = "SUBSTITUTED"
                            reason = "A source identity or location was substituted."
                        elif changed:
                            status = "ALTERED"
                            reason = "A baseline structural value was altered."
                        else:
                            status = "PRESERVED"
                            reason = "All required atoms and source identities remain."
            results.append(
                {
                    "field": field_id,
                    "reason": reason,
                    "status": status,
                }
            )
        overall = (
            "PASS"
            if all(
                result["status"] in {"PRESERVED", "NOT APPLICABLE"}
                for result in results
            )
            else "NOT PASS"
        )
        return {
            "field_results": results,
            "non_implication": {
                "product_result_does_not_imply_protocol_result": True,
                "product_result_does_not_imply_replay_result": True,
                "protocol_result_does_not_imply_product_result": True,
                "protocol_result_does_not_imply_replay_result": True,
                "replay_result_does_not_imply_product_result": True,
                "replay_result_does_not_imply_protocol_result": True,
            },
            "overall_replay_result": overall,
            "schema": SCHEMA,
            "unknowns": [
                result["field"]
                for result in results
                if result["status"] == "UNKNOWN"
            ],
        }

    @classmethod
    def _validate_live_replay_provenance(
        cls,
        baseline: Mapping[str, Any],
        candidate: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> None:
        task_id = manifest.get("task_id")
        protocol_run_id = manifest.get("protocol_run_id")
        for label, replay_input in (
            ("baseline", baseline),
            ("candidate", candidate),
        ):
            if (
                replay_input.get("task_id") != task_id
                or replay_input.get("protocol_run_id") != protocol_run_id
            ):
                raise ManualBridgeConflictError(
                    f"Replay {label} must match the frozen Golden task and "
                    "protocol identities."
                )

        entries = manifest.get("artifacts")
        allowed_hashes = {
            entry.get("artifact_sha256")
            for entry in entries
            if isinstance(entry, Mapping)
            and entry.get("state") == "FROZEN"
            and isinstance(entry.get("artifact_sha256"), str)
            and _SHA256.fullmatch(entry["artifact_sha256"])
        }
        if len(allowed_hashes) == 0:
            raise ManualBridgeConflictError(
                "Replay requires source identities from the frozen Golden set."
            )

        for label, replay_input in (
            ("baseline", baseline),
            ("candidate", candidate),
        ):
            fields = cls._field_map(replay_input)
            for field_id in REPLAY_FIELDS:
                field = fields.get(field_id)
                if not isinstance(field, Mapping):
                    continue
                if "forward_only_delta" in field:
                    linkage = field.get("forward_only_delta")
                    if (
                        not cls._has_forward_only_delta(field)
                        or linkage.get("source_artifact_hash")
                        not in allowed_hashes
                    ):
                        raise ManualBridgeConflictError(
                            f"Replay {label} field {field_id} has invalid "
                            "Forward-only Delta linkage."
                        )
                atoms = field.get("atoms")
                if atoms is None:
                    continue
                if not isinstance(atoms, list):
                    raise ManualBridgeConflictError(
                        f"Replay {label} field {field_id} has invalid atoms."
                    )
                atom_ids: set[str] = set()
                for atom in atoms:
                    if not isinstance(atom, Mapping):
                        raise ManualBridgeConflictError(
                            f"Replay {label} field {field_id} has an invalid atom."
                        )
                    atom_id = atom.get("atom_id")
                    if (
                        not {
                            "atom_id",
                            "value",
                            "source_artifact_hash",
                            "source_location",
                        }.issubset(atom)
                        or not isinstance(atom_id, str)
                        or not atom_id.strip()
                        or len(atom_id) > 200
                        or "\n" in atom_id
                        or "\r" in atom_id
                        or "\x00" in atom_id
                        or atom_id in atom_ids
                    ):
                        raise ManualBridgeConflictError(
                            f"Replay {label} field {field_id} has an invalid "
                            "or duplicate atom identity."
                        )
                    atom_ids.add(atom_id)
                    source_hash = atom.get("source_artifact_hash")
                    source_location = atom.get("source_location")
                    if source_hash not in allowed_hashes:
                        raise ManualBridgeConflictError(
                            f"Replay {label} field {field_id} cites a source "
                            "outside the frozen Golden set."
                        )
                    if (
                        not isinstance(source_location, str)
                        or not source_location.strip()
                        or len(source_location) > 500
                        or "\n" in source_location
                        or "\r" in source_location
                        or "\x00" in source_location
                    ):
                        raise ManualBridgeConflictError(
                            f"Replay {label} field {field_id} has an invalid "
                            "source location."
                        )

    def evaluate_replay(
        self,
        baseline: dict[str, Any],
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        with self.store.transaction():
            session = self._require_session()
            manifest = session.get("golden_manifest")
            manifest_output = session["outputs"].get("GOLDEN_MANIFEST")
            manifest_entries = (
                manifest.get("artifacts")
                if isinstance(manifest, Mapping)
                else None
            )
            frozen_roles = (
                {
                    entry.get("artifact_role")
                    for entry in manifest_entries
                    if isinstance(entry, Mapping)
                    and entry.get("state") == "FROZEN"
                }
                if isinstance(manifest_entries, list)
                else set()
            )
            if (
                not isinstance(manifest, Mapping)
                or manifest.get("golden_status") != "GOLDEN_ELIGIBLE"
                or not isinstance(manifest_output, Mapping)
                or manifest_output.get("frozen") is not True
                or frozen_roles != set(GOLDEN_ROLES)
                or not isinstance(manifest_entries, list)
                or len(manifest_entries) != len(GOLDEN_ROLES)
                or not self._manifest_matches_current_effective(
                    session,
                    manifest,
                )
                or session.get("hold_reason")
                or session.get("state") == "BLOCKED_AUTHORITY_INFLATION"
            ):
                raise ManualBridgeConflictError(
                    "Replay requires one frozen eligible six-role Golden manifest."
                )
            manifest_identity = manifest_output.get("sha256")
            if (
                baseline.get("manifest_identity") != manifest_identity
                or candidate.get("manifest_identity") != manifest_identity
                or _clean_single_line_scalar(
                    candidate.get("candidate_id"),
                    maximum=500,
                )
                == UNKNOWN
            ):
                raise ManualBridgeConflictError(
                    "Replay inputs must identify the exact frozen Golden manifest "
                    "and one fixed candidate."
                )
            fixed_baseline = manifest.get("replay_baseline")
            fixed_baseline_sha256 = manifest.get(
                "replay_baseline_sha256"
            )
            if (
                not isinstance(fixed_baseline, Mapping)
                or fixed_baseline_sha256
                != sha256_bytes(_canonical_json(fixed_baseline))
            ):
                raise ManualBridgeIntegrityError(
                    "Frozen Golden Replay baseline identity is invalid."
                )
            supplied_baseline_keys = set(baseline)
            expected_baseline_keys = set(fixed_baseline)
            if (
                supplied_baseline_keys
                != expected_baseline_keys | {"manifest_identity"}
                or {
                    key: baseline.get(key)
                    for key in expected_baseline_keys
                }
                != fixed_baseline
            ):
                raise ManualBridgeConflictError(
                    "Replay baseline must exactly match the baseline fixed "
                    "inside the frozen Golden manifest."
                )
            self._validate_live_replay_provenance(
                baseline,
                candidate,
                manifest,
            )
            result = self.compare_replay(baseline, candidate)
            result["baseline_manifest"] = manifest_identity
            result["candidate_manifest"] = manifest_identity
            result["candidate_id"] = candidate["candidate_id"]
            result["candidate_output_sha256"] = sha256_bytes(
                _canonical_json(candidate)
            )
            result["replay_result_id"] = sha256_bytes(
                _canonical_json(
                    {
                        "baseline": baseline,
                        "candidate": candidate,
                    }
                )
            )
            table = [
                "| Field | Status | Reason |",
                "| --- | --- | --- |",
            ]
            table.extend(
                f"| {item['field']} | {item['status']} | {item['reason']} |"
                for item in result["field_results"]
            )
            result["markdown_table"] = "\n".join(table)
            payload = _json_document(result)
            self._set_output(
                session,
                "REPLAY_RESULT",
                "replay_result.json",
                payload,
                "STRUCTURAL_REPLAY_EVALUATED",
            )
            session = self._require_session()
            session["results"]["replay"] = {
                "result_id": result["replay_result_id"],
                "result": result["overall_replay_result"],
                "unknowns": result["unknowns"],
            }
            session["state"] = "REPLAY_RECORDED"
            altered = sum(
                item["status"]
                in {
                    "ALTERED",
                    "MISSING",
                    "SUBSTITUTED",
                    "AUTHORITY-INFLATED",
                }
                for item in result["field_results"]
            )
            replay_event_id = session["outputs"]["REPLAY_RESULT"][
                "generated_event_id"
            ]
            record = session["burden"][
                "fields_lost_or_altered_during_transfer"
            ]
            record["value_or_unknown"] = altered
            record["source_event_ids"] = [replay_event_id]
            record["recorded_at"] = self._now()
            self._save_session(session)
            return self.snapshot()

    def record_observation(
        self,
        *,
        field: str,
        value: int | float | str,
        unit: str,
        method: str,
        notes: str = "",
    ) -> dict[str, Any]:
        with self.store.transaction():
            session = self._require_session()
            if field not in _BURDEN_FIELDS:
                raise ManualBridgeValidationError(
                    "Burden observation field is unsupported."
                )
            if (
                not isinstance(unit, str)
                or not unit
                or not isinstance(method, str)
                or not method
                or not isinstance(notes, str)
                or isinstance(value, bool)
                or not isinstance(value, (int, float, str))
            ):
                raise ManualBridgeValidationError(
                    "Burden observation value or method is invalid."
                )
            if isinstance(value, (int, float)) and value < 0:
                raise ManualBridgeValidationError(
                    "Burden observation cannot be negative."
                )
            event = self._append(
                "BURDEN_OBSERVATION_RECORDED",
                {
                    "field": field,
                    "method": method,
                    "session_id": session["session_id"],
                    "unit": unit,
                    "value": value,
                },
            )
            record = session["burden"][field]
            if method == "EXPLICIT_ONE_CLICK_INCREMENT":
                current = record.get("value_or_unknown")
                if not isinstance(current, (int, float)) or isinstance(
                    current,
                    bool,
                ):
                    current = 0
                record["value_or_unknown"] = current + float(value)
                if isinstance(value, int):
                    record["value_or_unknown"] = int(
                        record["value_or_unknown"]
                    )
            else:
                record["value_or_unknown"] = value
            record.update(
                {
                    "basis": "USER_ENTERED",
                    "confidence": "USER_ATTESTED",
                    "method": method,
                    "notes": notes or PRE_BRIDGE_UNKNOWN,
                    "recorded_at": event["recorded_at"],
                    "unit": unit,
                }
            )
            record.setdefault("source_event_ids", []).append(event["event_id"])
            self._save_session(session)
            return self.snapshot()

    def output_bytes(self, role: str) -> bytes:
        with self.store.transaction(
            write=False,
            timeout_seconds=0.05,
        ):
            session = self._require_session()
            output = session["outputs"].get(role)
            if not isinstance(output, dict):
                raise ManualBridgeValidationError(
                    "Requested Bridge output has not been generated."
                )
            return self.store.read_output(output["path"])

    def event_chain_head(self) -> str:
        with self.store.transaction(write=False, timeout_seconds=0.05):
            events = self.store.read_events()
            return events[-1]["event_hash"] if events else GENESIS_EVENT_HASH

    def snapshot(self) -> dict[str, Any]:
        with self.store.transaction(
            write=False,
            timeout_seconds=0.05,
        ):
            session = self._guard()
            if session is None:
                return {
                    "burden": {},
                    "error": None,
                    "event_chain_head": self.event_chain_head(),
                    "golden_manifest": None,
                    "imports": [],
                    "outputs": {},
                    "results": {
                        "product": (
                            "BUILDER EVIDENCE ONLY / INDEPENDENT AUDIT REQUIRED"
                        ),
                        "protocol": "IN PROGRESS / NOT FINAL",
                        "replay": "NOT YET PERFORMED",
                    },
                    "session": None,
                    "state": "BOUNDARY_INCOMPLETE",
                }
            imports: list[dict[str, Any]] = []
            effective = set(session["effective_by_role"].values())
            for import_id in session["imports"]:
                record = self.store.load_import(import_id)
                public = {
                    key: value
                    for key, value in record.items()
                    if key != "event_hash"
                }
                public["effective"] = import_id in effective
                imports.append(public)
            outputs: dict[str, dict[str, Any]] = {}
            for role, identity in session["outputs"].items():
                raw = self.store.read_output(identity["path"])
                try:
                    content = raw.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ManualBridgeIntegrityError(
                        "Generated Bridge output is not UTF-8."
                    ) from exc
                outputs[role] = {
                    **identity,
                    "content": content,
                }
            return {
                "burden": session["burden"],
                "error": None,
                "event_chain_head": self.event_chain_head(),
                "golden_manifest": session.get("golden_manifest"),
                "hold_reason": session.get("hold_reason"),
                "imports": imports,
                "outputs": outputs,
                "results": session["results"],
                "session": {
                    "boundary": session["boundary"],
                    "created_at": session["created_at"],
                    "session_id": session["session_id"],
                },
                "state": session["state"],
            }
