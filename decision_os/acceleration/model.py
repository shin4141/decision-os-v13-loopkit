"""Pure Verified Save protocol identities and path normalization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any
from urllib.parse import urlsplit, urlunsplit


PROTOCOL_VERSION = "decision-os.acceleration.v0.1"
GENESIS_EVENT_HASH = "0" * 64
EVENT_TYPES = frozenset(
    {
        "HUMAN_DEFAULT_CREATED",
        "DECISION_CHECK",
        "DEFAULT_MATCHED",
        "INTERRUPT_SKIPPED",
        "CHECKPOINT_PASSED",
        "CHECKPOINT_PENDING",
        "OVERRIDE",
        "VERIFIED_SAVE",
        "VERIFIED_REUSE",
        "REVOKED_SAVE",
        "DEFAULT_REVOKED_AFTER_USE",
        "DEFAULT_SUPERSEDED",
    }
)
EVENT_FIELDS = frozenset(
    {
        "event_id",
        "event_type",
        "timestamp",
        "run_id",
        "iteration",
        "repository_id",
        "decision_key",
        "decision_type",
        "normalized_scope",
        "default_created_run_id",
        "default_rule_hash",
        "matched_rule_hash",
        "adapter",
        "adapter_version",
        "protocol_version",
        "source_interrupt_id",
        "checkpoint_id",
        "interrupt_skipped",
        "status",
        "prev_event_hash",
        "event_hash",
    }
)
_GLOB_CHARACTERS = frozenset("*?[]{}")
_SCP_REMOTE = re.compile(
    r"^(?:(?P<user>[^@/:]+)@)?(?P<host>[^/:]+):(?P<path>.+)$"
)
_GIT_IDENTITY_TIMEOUT_SECONDS = 10


class AccelerationError(RuntimeError):
    """Base error for bounded acceleration operations."""


class RepositoryIdentityError(AccelerationError):
    """Repository identity cannot be established safely."""


class ScopeError(AccelerationError):
    """A requested scope is unsupported or escapes the repository."""


class UnsupportedDecisionError(AccelerationError):
    """A decision type is outside the fixed v0.1 protocol."""


class DecisionType(str, Enum):
    """Fixed protocol decision types."""

    ADD_TESTS = "ADD_TESTS"
    CREATE_FILE = "CREATE_FILE"
    MODIFY_FILE = "MODIFY_FILE"
    DELETE_OR_RENAME = "DELETE_OR_RENAME"
    ADD_DEPENDENCY = "ADD_DEPENDENCY"


@dataclass(frozen=True)
class DecisionIdentity:
    """Mechanically derived identity for one structured decision."""

    repository_id: str
    decision_type: DecisionType
    normalized_scope: str
    decision_key: str
    rule_hash: str


def canonical_json(value: Any) -> str:
    """Return stable UTF-8 JSON suitable for hashing."""

    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def sha256_text(value: str) -> str:
    """Hash one UTF-8 string."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_payload(payload: dict[str, Any]) -> str:
    """Hash one canonical JSON object."""

    return sha256_text(canonical_json(payload))


def _isolated_git_environment() -> dict[str, str]:
    """Build an environment with no ambient Git authority inputs."""

    # Identity reads operate only on the explicitly supplied local repository;
    # inherited Git context is unnecessary and can redirect that authority.
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
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
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
    )
    return environment


def git_output(repository: Path, *arguments: str) -> str:
    """Run one read-only Git identity command."""

    try:
        completed = subprocess.run(
            (
                "git",
                "--no-replace-objects",
                "-c",
                "core.useReplaceRefs=false",
                "-C",
                str(repository),
                *arguments,
            ),
            capture_output=True,
            check=False,
            env=_isolated_git_environment(),
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=_GIT_IDENTITY_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RepositoryIdentityError(
            "Git repository identity is unavailable."
        ) from exc
    if completed.returncode != 0:
        raise RepositoryIdentityError(
            completed.stderr.strip() or "Git repository identity is unavailable."
        )
    return completed.stdout.strip()


def git_root(repository: Path) -> Path:
    """Resolve the canonical Git worktree root."""

    raw = git_output(repository, "rev-parse", "--show-toplevel")
    root = Path(raw).resolve(strict=True)
    if not root.is_dir():
        raise RepositoryIdentityError("Git root is not a directory.")
    return root


def _credential_free_remote(raw: str) -> str | None:
    remote = raw.strip()
    if not remote:
        return None

    scp_match = _SCP_REMOTE.match(remote)
    if "://" not in remote and scp_match:
        host = scp_match.group("host").lower()
        path = scp_match.group("path").strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return f"ssh://{host}/{path}" if host and path else None

    parsed = urlsplit(remote)
    if parsed.scheme not in {"http", "https", "ssh", "git"}:
        return None
    host = parsed.hostname
    if not host:
        return None
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not path:
        return None
    return urlunsplit(
        (
            parsed.scheme.lower(),
            f"{host.lower()}{port}",
            path,
            "",
            "",
        )
    )


def repository_id(repository: Path) -> str:
    """Derive a hashed repository identity without storing its raw name."""

    root = git_root(repository)
    try:
        remote = git_output(root, "remote", "get-url", "origin")
    except RepositoryIdentityError:
        normalized_remote = None
    else:
        normalized_remote = _credential_free_remote(remote)
    identity = normalized_remote or f"local:{root.as_posix()}"
    return f"repo:v1:{sha256_text(identity)}"


def normalize_scope(repository: Path, requested_scope: str) -> str:
    """Normalize one exact file scope and reject escapes or ambiguous syntax."""

    if not isinstance(requested_scope, str):
        raise ScopeError("Scope must be a string.")
    raw = requested_scope.strip()
    if not raw or "\x00" in raw:
        raise ScopeError("Scope must be a non-empty path.")
    if any(character in raw for character in _GLOB_CHARACTERS):
        raise ScopeError("Glob syntax is unsupported.")

    root = git_root(repository)
    portable = raw.replace("\\", "/")
    requested = Path(portable)
    candidate = requested if requested.is_absolute() else root / requested

    try:
        resolved = candidate.resolve(strict=False)
        relative = resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ScopeError("Scope escapes or cannot be resolved safely.") from exc

    if relative == Path("."):
        raise ScopeError("Repository root is not an exact file scope.")
    if resolved.exists() and resolved.is_dir():
        raise ScopeError("Directory scopes are unsupported.")

    ancestor = resolved.parent
    while not ancestor.exists() and ancestor != root:
        ancestor = ancestor.parent
    try:
        ancestor.resolve(strict=True).relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ScopeError("Parent identity is outside the repository.") from exc

    normalized = relative.as_posix()
    if normalized.startswith("../") or normalized in {"", "."}:
        raise ScopeError("Scope escapes the repository.")
    return normalized


def decision_key(
    repository_identity: str,
    decision_type: DecisionType,
    normalized_scope: str,
) -> str:
    """Build the exact v1 decision key."""

    try:
        fixed_type = DecisionType(decision_type)
    except ValueError as exc:
        raise UnsupportedDecisionError(str(decision_type)) from exc
    return (
        "dk:v1|"
        f"{repository_identity}|{fixed_type.value}|{normalized_scope}"
    )


def rule_hash(
    decision_type: DecisionType,
    normalized_scope: str,
) -> str:
    """Hash the stable allow rule without run-specific or display data."""

    try:
        fixed_type = DecisionType(decision_type)
    except ValueError as exc:
        raise UnsupportedDecisionError(str(decision_type)) from exc
    return hash_payload(
        {
            "decision": "allow",
            "decision_type": fixed_type.value,
            "normalized_scope": normalized_scope,
            "protocol_version": PROTOCOL_VERSION,
        }
    )


def derive_decision_identity(
    repository: Path,
    decision_type: DecisionType,
    requested_scope: str,
) -> DecisionIdentity:
    """Derive all mechanically stable fields for a decision check."""

    repo_id = repository_id(repository)
    normalized = normalize_scope(repository, requested_scope)
    fixed_type = DecisionType(decision_type)
    return DecisionIdentity(
        repository_id=repo_id,
        decision_type=fixed_type,
        normalized_scope=normalized,
        decision_key=decision_key(repo_id, fixed_type, normalized),
        rule_hash=rule_hash(fixed_type, normalized),
    )
