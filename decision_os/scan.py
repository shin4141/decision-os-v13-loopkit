"""Bounded, read-only inspection for ordinary local Git repositories."""

from __future__ import annotations

from dataclasses import dataclass
import errno
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any, Iterable, Sequence
from urllib.parse import urlsplit


EXIT_OK = 0
EXIT_NOT_GIT = 3
EXIT_UNSTABLE = 7

SCHEMA_VERSION = "decision-os.scan.v0.2"
MAX_RESTART_FILES = 64
MAX_FILE_BYTES = 256 * 1024
MAX_TOTAL_BYTES = 1024 * 1024
MAX_DIRECTORY_ENTRIES = 4096

INSTRUCTION_PATHS = (
    "AGENTS.md",
    "CLAUDE.md",
    ".github/copilot-instructions.md",
)
RESTART_PATHS = (
    "HANDOFF.md",
    "CURRENT_STATE.md",
    "docs/current_state.md",
)
V13_PATHS = (
    "docs/current_signal.md",
    "handoff/current_codex_handoff.md",
)

MARKER_LABELS = {
    "current_identity": frozenset(("current task", "active branch")),
    "verification": frozenset(
        ("verification", "validation", "test receipt", "tests")
    ),
    "rollback": frozenset(
        ("rollback", "rollback identity", "known-good commit")
    ),
    "unfinished_work": frozenset(
        ("known gaps", "unfinished work", "missing closure")
    ),
    "next_action": frozenset(("next action", "next authorized action")),
    "boundary": frozenset(("not authorized", "do not repeat", "boundary")),
}

CLAIMS_NOT_MADE = (
    "repository_safety",
    "task_completeness",
    "instruction_quality",
    "software_correctness",
    "remote_freshness",
    "workflow_specific_diagnosis",
    "authority_or_gate",
)

RECOMMENDATION_NONE = "NO ADOPTION RECOMMENDATION"
RECOMMENDATION_LITE = "LITE RESTART NOTE RECOMMENDED"
RECOMMENDATION_HANDOFF = "HANDOFF SURFACE RECOMMENDED"
RECOMMENDATION_FULLER = "FULLER V13 FIT CHECK MAY BE USEFUL"
RECOMMENDATION_INSUFFICIENT = "INSUFFICIENT EVIDENCE"


@dataclass(frozen=True)
class GitCommandError(Exception):
    args_used: tuple[str, ...]
    returncode: int
    stderr: str


@dataclass(frozen=True)
class _GitSnapshot:
    root: str
    head: str
    branch: str | None
    status: str


@dataclass(frozen=True)
class _FileObservation:
    path: str
    state: str
    reason: str | None = None
    content: str | None = None
    size: int = 0


class _UnstableSnapshot(Exception):
    def __init__(self, changed: Sequence[str]) -> None:
        super().__init__("inspection snapshot changed")
        self.changed = tuple(changed)


class GitReader:
    """Run only bounded local Git reads with optional locking disabled."""

    def __init__(self, target: Path) -> None:
        self.target = target
        self.environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        self.environment.update(
            {
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_NO_LAZY_FETCH": "1",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
                "LC_ALL": "C",
                "LANG": "C",
                "TZ": "UTC",
            }
        )

    def run(
        self, *arguments: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ("git", "-C", str(self.target), *arguments),
            capture_output=True,
            check=False,
            env=self.environment,
            encoding="utf-8",
            errors="surrogateescape",
            stdin=subprocess.DEVNULL,
        )
        if check and completed.returncode != 0:
            raise GitCommandError(
                tuple(arguments),
                completed.returncode,
                completed.stderr.strip(),
            )
        return completed


def _evidence(
    check: str, status: str, source: str, detail: Any
) -> dict[str, Any]:
    return {
        "check": check,
        "detail": detail,
        "source": source,
        "status": status,
    }


def _base_repository() -> dict[str, Any]:
    return {
        "ahead": None,
        "behind": None,
        "branch": None,
        "change_count": None,
        "default_ref": None,
        "detached": None,
        "head": None,
        "origin": {
            "identity": None,
            "present": None,
            "remote_freshness": "NOT_CHECKED",
        },
        "root_name": None,
        "worktree": "UNKNOWN",
    }


def failure_payload(
    check: str,
    detail: Any,
    *,
    status: str = "UNKNOWN",
    repository: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the stable scan failure schema used for bounded transport errors."""

    return {
        "claims_not_made": list(CLAIMS_NOT_MADE),
        "command": "scan",
        "evidence": [_evidence(check, status, "decision-os scan", detail)],
        "mode": "UNDETERMINED",
        "recommendation": {
            "basis": [check],
            "code": RECOMMENDATION_INSUFFICIENT,
            "minimum_next_step": (
                "Establish one stable local repository snapshot before "
                "interpreting scan evidence."
            ),
        },
        "repository": _base_repository() if repository is None else repository,
        "route": {
            "basis": [],
            "code": "NONE",
            "command": None,
        },
        "scan_completion": "FAILED",
        "schema_version": SCHEMA_VERSION,
        "unknowns": [
            {
                "basis": [check],
                "code": "scan_result",
                "reason": "The bounded local scan did not complete.",
            }
        ],
    }


def _snapshot(reader: GitReader) -> _GitSnapshot:
    root = reader.run("rev-parse", "--show-toplevel").stdout.strip()
    head = reader.run("rev-parse", "--verify", "HEAD").stdout.strip()
    branch_result = reader.run(
        "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    branch = (
        branch_result.stdout.strip()
        if branch_result.returncode == 0
        else None
    )
    status_output = reader.run(
        "-c",
        "core.fsmonitor=false",
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--no-renames",
    ).stdout
    return _GitSnapshot(root, head, branch, status_output)


def _changed_snapshot_fields(
    opening: _GitSnapshot, closing: _GitSnapshot
) -> tuple[str, ...]:
    changed: list[str] = []
    if opening.root != closing.root:
        changed.append("repository_identity")
    if opening.head != closing.head:
        changed.append("head")
    if opening.branch != closing.branch:
        changed.append("branch")
    if opening.status != closing.status:
        changed.append("worktree")
    return tuple(changed)


def _sanitize_origin(raw: str | None) -> dict[str, Any]:
    if raw is None or not raw.strip():
        return {
            "identity": None,
            "present": False,
            "remote_freshness": "NOT_CHECKED",
        }

    value = raw.strip()
    identity = "LOCAL_PATH"
    if "://" in value:
        try:
            parsed = urlsplit(value)
            hostname = parsed.hostname
        except ValueError:
            hostname = None
            parsed = None
        if parsed is None:
            identity = None
        elif parsed.scheme not in ("file", "") and hostname:
            path = parsed.path.lstrip("/")
            identity = hostname
            if path:
                identity = f"{identity}/{path}"
    else:
        bounded_value = value.split("#", 1)[0].split("?", 1)[0]
        scp_match = re.match(
            r"^(?:[^@/\s]+@)?([^:/\s]+):(.+)$", bounded_value
        )
        if scp_match:
            identity = f"{scp_match.group(1)}/{scp_match.group(2).lstrip('/')}"

    return {
        "identity": _safe_output_text(identity),
        "present": True,
        "remote_freshness": "NOT_CHECKED",
    }


def _safe_output_text(value: str | None) -> str | None:
    if value is None:
        return None
    if any(
        ord(character) < 32
        or ord(character) == 127
        or 0xD800 <= ord(character) <= 0xDFFF
        for character in value
    ):
        return None
    return value


def _safe_parts(relative: str) -> tuple[str, ...]:
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts:
        raise ValueError("path is not a bounded relative path")
    if any(part in ("", ".", "..") or "\x00" in part for part in path.parts):
        raise ValueError("path contains an unsafe component")
    return tuple(path.parts)


def _directory_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def _entry_match(directory_fd: int, expected: str) -> tuple[str, str | None]:
    """Find one exact entry name without allowing an unbounded directory read."""

    case_mismatch = False
    try:
        with os.scandir(directory_fd) as entries:
            for index, entry in enumerate(entries):
                if index >= MAX_DIRECTORY_ENTRIES:
                    return "UNKNOWN", "directory_entry_limit"
                if entry.name == expected:
                    return "OBSERVED", None
                if entry.name.casefold() == expected.casefold():
                    case_mismatch = True
    except OSError as exc:
        return "UNKNOWN", f"unreadable:{type(exc).__name__}"
    if case_mismatch:
        return "UNKNOWN", "case_mismatch"
    return "ABSENT", None


def _open_parent_directory(
    root: Path, parts: Sequence[str]
) -> tuple[int | None, str, str | None]:
    """Open a verified parent via descriptor-relative, no-follow traversal."""

    try:
        directory_fd = os.open(root, _directory_flags())
    except OSError as exc:
        return None, "UNKNOWN", f"unreadable:{type(exc).__name__}"

    for component in parts[:-1]:
        state, reason = _entry_match(directory_fd, component)
        if state != "OBSERVED":
            os.close(directory_fd)
            return None, state, reason
        try:
            observed = os.stat(
                component, dir_fd=directory_fd, follow_symlinks=False
            )
            if stat.S_ISLNK(observed.st_mode):
                os.close(directory_fd)
                return None, "UNKNOWN", "symlink_rejected"
            child_fd = os.open(
                component,
                _directory_flags(),
                dir_fd=directory_fd,
            )
        except FileNotFoundError:
            os.close(directory_fd)
            return None, "ABSENT", None
        except OSError as exc:
            os.close(directory_fd)
            reason = (
                "symlink_rejected"
                if exc.errno in (errno.ELOOP, errno.ENOTDIR)
                else f"unreadable:{type(exc).__name__}"
            )
            return None, "UNKNOWN", reason
        os.close(directory_fd)
        directory_fd = child_fd
    return directory_fd, "OBSERVED", None


def _observe_path(
    root: Path,
    relative: str,
    *,
    read_content: bool,
    remaining_bytes: int = MAX_TOTAL_BYTES,
) -> _FileObservation:
    try:
        parts = _safe_parts(relative)
    except ValueError:
        return _FileObservation(relative, "UNKNOWN", "unsafe_path")

    parent_fd, parent_state, parent_reason = _open_parent_directory(root, parts)
    if parent_fd is None:
        return _FileObservation(relative, parent_state, parent_reason)
    final_name = parts[-1]
    try:
        final_state, final_reason = _entry_match(parent_fd, final_name)
        if final_state != "OBSERVED":
            os.close(parent_fd)
            return _FileObservation(relative, final_state, final_reason)
        before = os.stat(final_name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        os.close(parent_fd)
        return _FileObservation(relative, "ABSENT")
    except OSError as exc:
        os.close(parent_fd)
        return _FileObservation(
            relative, "UNKNOWN", f"unreadable:{type(exc).__name__}"
        )
    if stat.S_ISLNK(before.st_mode):
        os.close(parent_fd)
        return _FileObservation(relative, "UNKNOWN", "symlink_rejected")
    if not stat.S_ISREG(before.st_mode):
        os.close(parent_fd)
        return _FileObservation(relative, "UNKNOWN", "not_regular_file")
    if not read_content:
        os.close(parent_fd)
        return _FileObservation(relative, "OBSERVED", size=before.st_size)
    if before.st_size > MAX_FILE_BYTES or before.st_size > remaining_bytes:
        os.close(parent_fd)
        return _FileObservation(relative, "UNKNOWN", "size_limit")

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    descriptor: int | None = None
    try:
        descriptor = os.open(final_name, flags, dir_fd=parent_fd)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
        ):
            raise _UnstableSnapshot((f"surface:{relative}",))
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65536, MAX_FILE_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_FILE_BYTES or total > remaining_bytes:
                return _FileObservation(relative, "UNKNOWN", "size_limit")
        after_open = os.fstat(descriptor)
        after_path = os.stat(
            final_name, dir_fd=parent_fd, follow_symlinks=False
        )
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_open = (
            after_open.st_dev,
            after_open.st_ino,
            after_open.st_mode,
            after_open.st_size,
            after_open.st_mtime_ns,
        )
        identity_path = (
            after_path.st_dev,
            after_path.st_ino,
            after_path.st_mode,
            after_path.st_size,
            after_path.st_mtime_ns,
        )
        if identity_before != identity_open or identity_before != identity_path:
            raise _UnstableSnapshot((f"surface:{relative}",))
        data = b"".join(chunks)
    except _UnstableSnapshot:
        raise
    except OSError as exc:
        return _FileObservation(
            relative, "UNKNOWN", f"unreadable:{type(exc).__name__}"
        )
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_fd)

    try:
        content = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _FileObservation(relative, "UNKNOWN", "invalid_utf8")
    return _FileObservation(
        relative, "OBSERVED", content=content, size=len(data)
    )


def _handoff_candidates(root: Path) -> tuple[tuple[str, ...], str | None]:
    try:
        parts = _safe_parts("handoff")
    except ValueError:
        return (), "unsafe_path"
    parent_fd, parent_state, parent_reason = _open_parent_directory(root, parts)
    if parent_fd is None:
        if parent_state == "ABSENT":
            return (), None
        return (), parent_reason
    state, reason = _entry_match(parent_fd, parts[-1])
    if state != "OBSERVED":
        os.close(parent_fd)
        if state == "ABSENT":
            return (), None
        return (), reason
    try:
        directory_fd = os.open(
            parts[-1],
            _directory_flags(),
            dir_fd=parent_fd,
        )
    except OSError as exc:
        reason = (
            "symlink_rejected"
            if exc.errno in (errno.ELOOP, errno.ENOTDIR)
            else f"unreadable:{type(exc).__name__}"
        )
        return (), reason
    finally:
        os.close(parent_fd)
    names: list[str] = []
    try:
        with os.scandir(directory_fd) as entries:
            for index, entry in enumerate(entries):
                if index >= MAX_DIRECTORY_ENTRIES:
                    return (), "directory_entry_limit"
                name = entry.name
                if not name.endswith(".md"):
                    continue
                if any(
                    ord(character) < 32 or ord(character) == 127
                    for character in name
                ):
                    return (), "unsafe_filename"
                if any(0xD800 <= ord(character) <= 0xDFFF for character in name):
                    return (), "unsafe_filename"
                names.append(name)
                if len(names) > MAX_RESTART_FILES:
                    return (), "candidate_limit"
    except OSError as exc:
        return (), f"unreadable:{type(exc).__name__}"
    finally:
        os.close(directory_fd)
    names.sort(key=lambda item: item.encode("utf-8"))
    return tuple(f"handoff/{name}" for name in names), None


def _marker_classes(content: str) -> tuple[str, ...]:
    labels: set[str] = set()
    for line in content.splitlines():
        match = re.match(
            r"^\s*(?:[-*]\s+)?([A-Za-z][A-Za-z -]*?)\s*:",
            line,
        )
        if match is None:
            continue
        label = " ".join(match.group(1).lower().split())
        for marker_class, accepted in MARKER_LABELS.items():
            if label in accepted:
                labels.add(marker_class)
    return tuple(name for name in MARKER_LABELS if name in labels)


def _unknown_entry(code: str, reason: str, basis: Iterable[str]) -> dict[str, Any]:
    return {
        "basis": list(basis),
        "code": code,
        "reason": reason,
    }


def _recommendation(
    *,
    mode: str,
    unsafe_surface: bool,
    instruction_count: int,
    has_restart: bool,
    dirty: bool,
    detached: bool,
    non_default_ahead: bool,
) -> tuple[str, list[str], str]:
    if mode != "UNMANAGED_REPOSITORY":
        return (
            RECOMMENDATION_NONE,
            ["v13.surface"],
            "Run decision-os check <repository>.",
        )
    if unsafe_surface:
        return (
            RECOMMENDATION_INSUFFICIENT,
            ["surface.unknown"],
            (
                "Review the unreadable or unsafe bounded evidence before "
                "drawing an adoption conclusion."
            ),
        )
    if instruction_count >= 2 and not has_restart and (
        dirty or non_default_ahead
    ):
        return (
            RECOMMENDATION_FULLER,
            ["instructions.multiple", "active_work", "restart.absent"],
            (
                "Use a fit check only if repository-specific interpretation "
                "of these bounded findings is valuable."
            ),
        )
    if not has_restart and (
        instruction_count >= 2 or non_default_ahead
    ):
        basis = (
            ["instructions.multiple", "restart.absent"]
            if instruction_count >= 2
            else ["branch.non_default_ahead", "restart.absent"]
        )
        return (
            RECOMMENDATION_HANDOFF,
            basis,
            (
                "Create one stable handoff surface with current identity, "
                "evidence, boundaries, and the next action."
            ),
        )
    if not has_restart and (
        dirty or detached or instruction_count == 1
    ):
        basis: list[str] = []
        if dirty:
            basis.append("worktree.dirty")
        if detached:
            basis.append("head.detached")
        if instruction_count == 1:
            basis.append("instructions.one")
        basis.append("restart.absent")
        return (
            RECOMMENDATION_LITE,
            basis,
            (
                "Create or update one restart note with the current work and "
                "next action before the next agent session."
            ),
        )
    return (
        RECOMMENDATION_NONE,
        [],
        "No adoption step is recommended from this bounded evidence.",
    )


def scan_repository(target: Path) -> tuple[dict[str, Any], int]:
    """Inspect one local Git repository without writing to it."""

    reader = GitReader(target)
    try:
        opening = _snapshot(reader)
    except GitCommandError as exc:
        return (
            failure_payload(
                "git.repository",
                {
                    "arguments": list(exc.args_used),
                    "message": "required local Git read failed",
                    "returncode": exc.returncode,
                },
            ),
            EXIT_NOT_GIT,
        )

    root = Path(opening.root)
    root_name = _safe_output_text(root.name)
    branch = _safe_output_text(opening.branch)
    status_lines = tuple(
        sorted(entry for entry in opening.status.split("\0") if entry)
    )
    origin_result = reader.run(
        "config", "--get", "remote.origin.url", check=False
    )
    origin_raw = (
        origin_result.stdout.strip()
        if origin_result.returncode == 0
        else None
    )
    origin = _sanitize_origin(origin_raw)

    default_result = reader.run(
        "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD", check=False
    )
    default_ref: str | None = None
    ahead: int | None = None
    behind: int | None = None
    if default_result.returncode == 0:
        full_default_ref = default_result.stdout.strip()
        prefix = "refs/remotes/"
        default_ref = (
            full_default_ref[len(prefix) :]
            if full_default_ref.startswith(prefix)
            else full_default_ref
        )
        default_ref = _safe_output_text(default_ref)
        count_result = reader.run(
            "rev-list",
            "--left-right",
            "--count",
            f"HEAD...{full_default_ref}",
            check=False,
        )
        if count_result.returncode == 0:
            counts = count_result.stdout.split()
            if len(counts) == 2 and all(item.isdigit() for item in counts):
                ahead, behind = (int(counts[0]), int(counts[1]))

    repository = {
        "ahead": ahead,
        "behind": behind,
        "branch": branch,
        "change_count": len(status_lines),
        "default_ref": default_ref,
        "detached": opening.branch is None,
        "head": opening.head,
        "origin": origin,
        "root_name": root_name,
        "worktree": "DIRTY" if status_lines else "CLEAN",
    }

    evidence: list[dict[str, Any]] = [
        _evidence(
            "git.repository",
            "OBSERVED" if root_name is not None else "UNKNOWN",
            "local Git",
            {"root_name": root_name},
        ),
        _evidence(
            "git.head",
            "OBSERVED",
            "local Git",
            {
                "detached": opening.branch is None,
                "head": opening.head,
            },
        ),
        _evidence(
            "git.branch",
            "OBSERVED" if opening.branch is None or branch is not None else "UNKNOWN",
            "local Git",
            {
                "branch": branch,
                "detached": opening.branch is None,
            },
        ),
        _evidence(
            "git.worktree",
            "OBSERVED",
            "local Git",
            {
                "change_count": len(status_lines),
                "state": "DIRTY" if status_lines else "CLEAN",
            },
        ),
        _evidence(
            "git.default_branch",
            "OBSERVED" if default_ref is not None else "UNKNOWN",
            "local Git",
            {
                "ahead": ahead,
                "behind": behind,
                "default_ref": default_ref,
                "remote_freshness": "NOT_CHECKED",
            },
        ),
        _evidence(
            "git.origin",
            (
                "UNKNOWN"
                if origin["present"] and origin["identity"] is None
                else "OBSERVED"
                if origin["present"]
                else "ABSENT"
            ),
            "local Git config",
            origin,
        ),
    ]

    instruction_observations = tuple(
        _observe_path(root, relative, read_content=False)
        for relative in INSTRUCTION_PATHS
    )
    instruction_present = tuple(
        item.path for item in instruction_observations if item.state == "OBSERVED"
    )
    instruction_unknown = tuple(
        {"path": item.path, "reason": item.reason}
        for item in instruction_observations
        if item.state == "UNKNOWN"
    )
    evidence.append(
        _evidence(
            "instructions.surfaces",
            (
                "UNKNOWN"
                if instruction_unknown
                else "OBSERVED"
                if instruction_present
                else "ABSENT"
            ),
            "bounded path allowlist",
            {
                "absent": [
                    item.path
                    for item in instruction_observations
                    if item.state == "ABSENT"
                ],
                "observed": list(instruction_present),
                "unknown": list(instruction_unknown),
            },
        )
    )

    handoff_paths, handoff_directory_issue = _handoff_candidates(root)
    restart_candidates = tuple(dict.fromkeys((*RESTART_PATHS, *handoff_paths)))
    restart_observations: list[_FileObservation] = []
    remaining_bytes = MAX_TOTAL_BYTES
    for relative in restart_candidates:
        try:
            observation = _observe_path(
                root,
                relative,
                read_content=True,
                remaining_bytes=remaining_bytes,
            )
        except _UnstableSnapshot as exc:
            return (
                failure_payload(
                    "scan.snapshot",
                    {"changed": list(exc.changed)},
                    status="CONTRADICTORY",
                    repository=repository,
                ),
                EXIT_UNSTABLE,
            )
        restart_observations.append(observation)
        if observation.state == "OBSERVED":
            remaining_bytes -= observation.size

    restart_present = tuple(
        item.path for item in restart_observations if item.state == "OBSERVED"
    )
    restart_unknown: list[dict[str, Any]] = [
        {"path": item.path, "reason": item.reason}
        for item in restart_observations
        if item.state == "UNKNOWN"
    ]
    if handoff_directory_issue is not None:
        restart_unknown.append(
            {"path": "handoff/*.md", "reason": handoff_directory_issue}
        )
    markers = {
        item.path: list(_marker_classes(item.content or ""))
        for item in restart_observations
        if item.state == "OBSERVED"
    }
    bounded_restart = tuple(
        path
        for path, marker_classes in markers.items()
        if "current_identity" in marker_classes
        and "next_action" in marker_classes
    )
    evidence.extend(
        (
            _evidence(
                "restart.surfaces",
                (
                    "UNKNOWN"
                    if restart_unknown
                    else "OBSERVED"
                    if restart_present
                    else "ABSENT"
                ),
                "bounded restart paths",
                {
                    "absent": [
                        item.path
                        for item in restart_observations
                        if item.state == "ABSENT"
                    ],
                    "bounded_restart_evidence": list(bounded_restart),
                    "observed": list(restart_present),
                    "unknown": restart_unknown,
                },
            ),
            _evidence(
                "restart.markers",
                (
                    "OBSERVED"
                    if any(markers.values())
                    else "ABSENT"
                    if markers
                    else "NOT_APPLICABLE"
                ),
                "exact normalized field labels",
                {
                    "markers": markers,
                    "semantic_quality_proven": False,
                },
            ),
        )
    )

    v13_observations = tuple(
        _observe_path(root, relative, read_content=False)
        for relative in V13_PATHS
    )
    v13_present = tuple(
        item.path for item in v13_observations if item.state == "OBSERVED"
    )
    v13_unknown = tuple(
        {"path": item.path, "reason": item.reason}
        for item in v13_observations
        if item.state == "UNKNOWN"
    )
    if len(v13_present) == len(V13_PATHS) and not v13_unknown:
        mode = "V13_MANAGED_REPOSITORY"
    elif not v13_present and not v13_unknown:
        mode = "UNMANAGED_REPOSITORY"
    else:
        mode = "UNDETERMINED"
    route = {
        "basis": list(v13_present)
        + [item["path"] for item in v13_unknown],
        "code": "RUN_V13_CHECK" if mode != "UNMANAGED_REPOSITORY" else "NONE",
        "command": (
            "decision-os check <repository>"
            if mode != "UNMANAGED_REPOSITORY"
            else None
        ),
    }
    evidence.append(
        _evidence(
            "v13.routing",
            (
                "UNKNOWN"
                if v13_unknown
                else "OBSERVED"
                if v13_present
                else "NOT_APPLICABLE"
            ),
            "canonical V13 path allowlist",
            {
                "mode": mode,
                "observed": list(v13_present),
                "unknown": list(v13_unknown),
            },
        )
    )

    try:
        closing = _snapshot(reader)
    except GitCommandError as exc:
        return (
            failure_payload(
                "git.snapshot",
                {
                    "arguments": list(exc.args_used),
                    "message": "required local Git read failed",
                    "returncode": exc.returncode,
                },
                repository=repository,
            ),
            EXIT_NOT_GIT,
        )
    changed = _changed_snapshot_fields(opening, closing)
    if changed:
        return (
            failure_payload(
                "scan.snapshot",
                {"changed": list(changed)},
                status="CONTRADICTORY",
                repository=repository,
            ),
            EXIT_UNSTABLE,
        )
    evidence.append(
        _evidence(
            "scan.snapshot",
            "OBSERVED",
            "opening and closing local reads",
            {"stable": True},
        )
    )

    unsafe_surface = bool(
        instruction_unknown or restart_unknown or v13_unknown
    )
    default_name = default_ref.rsplit("/", 1)[-1] if default_ref else None
    non_default_ahead = bool(
        branch is not None
        and default_name is not None
        and branch != default_name
        and ahead is not None
        and ahead > 0
    )
    recommendation_code, basis, minimum_next_step = _recommendation(
        mode=mode,
        unsafe_surface=unsafe_surface,
        instruction_count=len(instruction_present),
        has_restart=bool(bounded_restart),
        dirty=bool(status_lines),
        detached=opening.branch is None,
        non_default_ahead=non_default_ahead,
    )

    unknowns = [
        _unknown_entry(
            "task_completion",
            "A clean worktree or a handoff marker cannot prove task completion.",
            ["git.worktree", "restart.markers"],
        ),
        _unknown_entry(
            "instruction_quality",
            "Instruction-surface presence does not prove instruction quality.",
            ["instructions.surfaces"],
        ),
        _unknown_entry(
            "software_correctness",
            "Local test or verification markers do not prove software correctness.",
            ["restart.markers"],
        ),
        _unknown_entry(
            "remote_freshness",
            "The local-only scan does not contact a remote.",
            ["git.default_branch", "git.origin"],
        ),
    ]
    if unsafe_surface:
        unknowns.append(
            _unknown_entry(
                "bounded_surface",
                "At least one bounded surface could not be inspected safely.",
                ["surface.unknown"],
            )
        )

    return (
        {
            "claims_not_made": list(CLAIMS_NOT_MADE),
            "command": "scan",
            "evidence": evidence,
            "mode": mode,
            "recommendation": {
                "basis": basis,
                "code": recommendation_code,
                "minimum_next_step": minimum_next_step,
            },
            "repository": repository,
            "route": route,
            "scan_completion": "PARTIAL" if unsafe_surface else "COMPLETE",
            "schema_version": SCHEMA_VERSION,
            "unknowns": unknowns,
        },
        EXIT_OK,
    )


__all__ = (
    "CLAIMS_NOT_MADE",
    "EXIT_NOT_GIT",
    "EXIT_OK",
    "EXIT_UNSTABLE",
    "GitCommandError",
    "GitReader",
    "SCHEMA_VERSION",
    "failure_payload",
    "scan_repository",
)
