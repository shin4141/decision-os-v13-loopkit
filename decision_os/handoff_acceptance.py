"""Deterministic, read-only assessment of one local handoff artifact.

The public result intentionally contains only allowlisted computed facts.
Source paths, field values, Git values, and exception text remain private.
"""

from __future__ import annotations

from dataclasses import dataclass
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlsplit


SCHEMA_VERSION = "handoff-acceptance/v0.2"
MAX_INPUT_BYTES = 1024 * 1024
GIT_TIMEOUT_SECONDS = 5.0

RESULT_ACCEPTABLE = "ACCEPTABLE"
RESULT_NOT_ACCEPTABLE = "NOT_ACCEPTABLE"
RESULT_INVALID = "INVALID"

MODE_ACTIVE_TRANSFER = "ACTIVE_TRANSFER"
MODE_CLOSED_STATE = "CLOSED_STATE"

EXIT_ACCEPTABLE = 0
EXIT_USAGE_ERROR = 2
EXIT_REPOSITORY_CONTEXT_UNAVAILABLE = 3
EXIT_NOT_ACCEPTABLE = 4
EXIT_INVALID = 5
EXIT_INTERNAL_ERROR = 6
EXIT_UNSTABLE_SNAPSHOT = 7

USAGE_ERROR = "USAGE_ERROR"
REPOSITORY_CONTEXT_UNAVAILABLE = "REPOSITORY_CONTEXT_UNAVAILABLE"
INTERNAL_ERROR = "INTERNAL_ERROR"
UNSTABLE_SNAPSHOT = "UNSTABLE_SNAPSHOT"

PROCESS_ERROR_CODES = (
    USAGE_ERROR,
    REPOSITORY_CONTEXT_UNAVAILABLE,
    INTERNAL_ERROR,
    UNSTABLE_SNAPSHOT,
)

ISSUE_CODES = (
    "INPUT_MISSING",
    "INPUT_OUTSIDE_ROOT",
    "INPUT_SYMLINK",
    "INPUT_NOT_REGULAR",
    "INPUT_TOO_LARGE",
    "INPUT_UNREADABLE",
    "INPUT_INVALID_UTF8",
    "MALFORMED_REPRESENTATION",
    "UNSUPPORTED_VARIANT",
    "CURRENT_RECORD_AMBIGUOUS",
    "REQUIRED_FIELD_ABSENT",
    "FIELD_UNKNOWN",
    "FIELD_AMBIGUOUS",
    "FIELD_CONFLICT",
    "TARGET_LAYER_MISMATCH",
    "REPOSITORY_REFERENCE_UNRESOLVED",
    "REPOSITORY_MISMATCH",
    "STATE_GATE_CONFLICT",
    "ACTIVE_BRANCH_MISMATCH",
    "OWNER_MISMATCH",
    "ROUTINE_WORK_RETURNED",
    "ACTION_RELATION_UNPROVEN",
    "FIRST_ACTION_NONE_ACTIVE",
    "COMPLETION_CLOSURE_CONFLICT",
    "CLOSED_STATE_INCOMPLETE",
    "CANONICAL_BRANCH_UNKNOWN",
    "DETACHED_HEAD",
    "CLOSED_BRANCH_MISMATCH",
    "LOCAL_CHANGES_UNRESOLVED",
    "INDEX_DIRTY",
    "WORKTREE_DIRTY",
    "SEMANTIC_REVIEW_REQUIRED",
)

CANONICAL_FIELDS = (
    "target_layer",
    "repository_reference",
    "current_state",
    "current_gate",
    "active_branch",
    "next_authorized_action",
    "completion_line",
    "missing_closure",
    "next_owner",
    "receiving_ownership",
    "first_one_action",
    "do_not_continue_boundary",
    "ai_retained_work",
)

LABEL_ALIASES = {
    "target layer": "target_layer",
    "repository": "repository_reference",
    "repository identity": "repository_reference",
    "repo root": "repository_reference",
    "repository root": "repository_reference",
    "current state": "current_state",
    "current gate": "current_gate",
    "v13 gate": "current_gate",
    "active branch": "active_branch",
    "next authorized action": "next_authorized_action",
    "completion line": "completion_line",
    "missing closure": "missing_closure",
    "next owner": "next_owner",
    "what the receiving ai now owns": "receiving_ownership",
    "what you own now": "receiving_ownership",
    "receiving ai owns": "receiving_ownership",
    "receiving ownership": "receiving_ownership",
    "first one action": "first_one_action",
    "first action": "first_one_action",
    "do not continue boundary": "do_not_continue_boundary",
    "stop boundary": "do_not_continue_boundary",
    "what must not be returned to the decision owner": "ai_retained_work",
    "work not returned to decision owner": "ai_retained_work",
    "ai retained work": "ai_retained_work",
    "work retained by receiving ai": "ai_retained_work",
}

HISTORICAL_HEADINGS = (
    "REVERSE-CHRONOLOGICAL HISTORICAL LEDGER",
    "HISTORICAL MATERIAL",
    "HISTORICAL LEDGER",
    "ARCHIVED HANDOFFS",
    "PREVIOUS HANDOFFS",
    "PRIOR HANDOFFS",
    "HANDOFF HISTORY",
    "HISTORICAL",
    "HISTORY",
    "ARCHIVE",
)

OPERATIVE_HEADINGS = (
    "CURRENT CODEX HANDOFF",
    "RESPONSIBILITY TRANSFER",
    "CURRENT HANDOFF",
    "REPOSITORY HANDOFF",
    "HANDOFF ARTIFACT",
    "HANDOFF",
)

STATE_TOKENS = {
    "ACTIVE": "ACTIVE",
    "OPEN": "ACTIVE",
    "IN PROGRESS": "ACTIVE",
    "NOT STARTED": "ACTIVE",
    "READY": "ACTIVE",
    "RESTRICTED": "RESTRICTED",
    "HOLD": "RESTRICTED",
    "BLOCKED": "RESTRICTED",
    "CAPPED": "RESTRICTED",
    "AWAITING AUTHORIZATION": "RESTRICTED",
    "CLOSED": "CLOSED",
    "COMPLETE": "CLOSED",
    "COMPLETED": "CLOSED",
}

GATE_TOKENS = {
    "GO UNDER CAP": "GO_UNDER_CAP",
    "GO": "GO",
    "HOLD": "HOLD",
    "CAP": "CAP",
    "BLOCK": "BLOCK",
}

CLOSED_COMPLETION_VALUES = frozenset(
    ("complete", "completed", "closed", "pass", "satisfied")
)
CLOSED_BOUNDARY_VALUES = frozenset(
    (
        "do not continue without a new gate",
        "new work requires a new gate",
        "stop; new work requires a new gate",
    )
)
OPEN_COMPLETION_VALUES = frozenset(("open", "incomplete", "not complete"))
CLOSED_CONJUNCTION_NONE_FIELDS = (
    "active_branch",
    "next_authorized_action",
    "missing_closure",
    "first_one_action",
)
_HEADING_RE = re.compile(
    r"^[ ]{0,3}(?P<marks>#{1,6})(?:[ \t]+(?P<title>.*?))?[ \t]*$"
)
_FENCE_RE = re.compile(
    r"^[ ]{0,3}(?P<fence>`{3,}|~{3,})(?P<tail>.*)$"
)


@dataclass(frozen=True)
class HandoffAssessment:
    """One safe completed Artifact assessment."""

    result: str
    mode: str | None
    issue_codes: tuple[str, ...]


@dataclass(frozen=True)
class HandoffProcessError(Exception):
    """A process-only failure that must not expose source or exception text."""

    code: str

    def __post_init__(self) -> None:
        if self.code not in PROCESS_ERROR_CODES:
            object.__setattr__(self, "code", INTERNAL_ERROR)
        Exception.__init__(self, self.code)


@dataclass(frozen=True)
class _RepositorySnapshot:
    root: Path
    invocation_root: Path
    resolved_root: Path
    root_identity: tuple[int, int, int]
    invocation_identity: tuple[int, int, int]
    head: str
    branch: str | None
    origin: str | None
    origin_slug: str | None
    canonical_branch: str | None
    canonical_tip: str | None
    status_digest: str
    index_dirty: bool
    worktree_dirty: bool
    untracked: bool
    unmerged: bool


@dataclass(frozen=True)
class _InputSnapshot:
    parts: tuple[str, ...]
    identity: tuple[int, int, int, int, int]
    digest: str
    content: bytes


@dataclass(frozen=True)
class _Heading:
    line: int
    level: int
    title: str


@dataclass(frozen=True)
class _Occurrence:
    field: str
    label: str
    value: str


@dataclass(frozen=True)
class _Control:
    token: str
    exact: bool


@dataclass(frozen=True)
class _CanonicalRecord:
    values: Mapping[str, str]
    repository_values: tuple[tuple[str, str], ...]
    conflict_fields: frozenset[str]
    v13_gate_alias: bool


class _ArtifactInputError(Exception):
    def __init__(
        self,
        code: str,
        identity: tuple[int, int, int, int, int] | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.identity = identity


class _MalformedRepresentation(Exception):
    pass


class _Unstable(Exception):
    pass


def _validate_assessment(assessment: HandoffAssessment) -> None:
    if not isinstance(assessment, HandoffAssessment):
        raise HandoffProcessError(INTERNAL_ERROR)
    if assessment.result not in (
        RESULT_ACCEPTABLE,
        RESULT_NOT_ACCEPTABLE,
        RESULT_INVALID,
    ):
        raise HandoffProcessError(INTERNAL_ERROR)
    if assessment.result == RESULT_ACCEPTABLE:
        if assessment.mode != MODE_CLOSED_STATE or assessment.issue_codes:
            raise HandoffProcessError(INTERNAL_ERROR)
    elif assessment.mode is not None or not assessment.issue_codes:
        raise HandoffProcessError(INTERNAL_ERROR)
    if (
        not isinstance(assessment.issue_codes, tuple)
        or assessment.issue_codes != _ordered_issues(assessment.issue_codes)
    ):
        raise HandoffProcessError(INTERNAL_ERROR)


def _ordered_issues(issues: Iterable[str]) -> tuple[str, ...]:
    selected = set(issues)
    return tuple(code for code in ISSUE_CODES if code in selected)


def _assessment(
    result: str,
    *,
    mode: str | None = None,
    issues: Iterable[str] = (),
) -> HandoffAssessment:
    ordered = _ordered_issues(issues)
    if result != RESULT_ACCEPTABLE:
        mode = None
    return HandoffAssessment(result, mode, ordered)


def assessment_payload(assessment: HandoffAssessment) -> dict[str, object]:
    """Return the normative safe machine-readable shape."""

    _validate_assessment(assessment)
    return {
        "schema_version": SCHEMA_VERSION,
        "result": assessment.result,
        "mode": assessment.mode,
        "issue_codes": list(assessment.issue_codes),
        "approval_performed": False,
        "authority_granted": False,
        "writes_performed": False,
        "remote_freshness": "NOT_CHECKED",
    }


def render_json(assessment: HandoffAssessment) -> str:
    """Render stable compact JSON with one trailing newline."""

    return json.dumps(
        assessment_payload(assessment),
        ensure_ascii=True,
        separators=(",", ":"),
    ) + "\n"


def render_text(assessment: HandoffAssessment) -> str:
    """Render stable allowlisted text with one trailing newline."""

    _validate_assessment(assessment)
    mode = assessment.mode if assessment.mode is not None else "NONE"
    issues = (
        ",".join(assessment.issue_codes)
        if assessment.issue_codes
        else "NONE"
    )
    return "\n".join(
        (
            f"HANDOFF_ACCEPTANCE: {assessment.result}",
            f"MODE: {mode}",
            f"ISSUES: {issues}",
            "APPROVAL_PERFORMED: NO",
            "AUTHORITY_GRANTED: NO",
            "WRITES_PERFORMED: NO",
            "REMOTE_FRESHNESS: NOT_CHECKED",
            "",
        )
    )


def exit_code_for_assessment(assessment: HandoffAssessment) -> int:
    _validate_assessment(assessment)
    if assessment.result == RESULT_ACCEPTABLE:
        return EXIT_ACCEPTABLE
    if assessment.result == RESULT_NOT_ACCEPTABLE:
        return EXIT_NOT_ACCEPTABLE
    return EXIT_INVALID


def process_error_line(error: HandoffProcessError | str) -> str:
    code = error.code if isinstance(error, HandoffProcessError) else error
    if code not in PROCESS_ERROR_CODES:
        code = INTERNAL_ERROR
    return f"HANDOFF_ACCEPTANCE_ERROR: {code}\n"


def _git_environment() -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "PATH": os.defpath,
            "LC_ALL": "C",
            "LANG": "C",
            "TZ": "UTC",
        }
    )
    return environment


def _run_git(
    target: Path, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    command = (
        "git",
        "-c",
        f"core.hooksPath={os.devnull}",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.untrackedCache=false",
        "-c",
        "core.ignoreStat=false",
        "-c",
        "core.trustCtime=true",
        "-c",
        "core.checkStat=default",
        "-c",
        "core.fileMode=true",
        "-c",
        "maintenance.auto=false",
        "-C",
        os.fspath(target),
        *arguments,
    )
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_environment(),
            encoding="utf-8",
            errors="surrogateescape",
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(
                input="", timeout=GIT_TIMEOUT_SECONDS
            )
        except subprocess.TimeoutExpired as exc:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (AttributeError, OSError):
                process.kill()
            process.communicate()
            raise HandoffProcessError(
                REPOSITORY_CONTEXT_UNAVAILABLE
            ) from exc
        completed = subprocess.CompletedProcess(
            command,
            process.returncode,
            stdout,
            stderr,
        )
    except HandoffProcessError:
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE) from exc
    if check and completed.returncode != 0:
        raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)
    return completed


def _origin_slug(value: str | None) -> str | None:
    if value is None:
        return None
    candidate = value.strip()
    if not candidate or "\n" in candidate or "\r" in candidate:
        return None
    path: str | None = None
    if "://" in candidate:
        try:
            parsed = urlsplit(candidate)
        except ValueError:
            return None
        if (
            parsed.scheme.lower() not in ("https", "ssh")
            or parsed.hostname is None
            or parsed.query
            or parsed.fragment
        ):
            return None
        path = parsed.path
    else:
        match = re.fullmatch(
            r"(?:[^@/:\s]+@)?[^/:\s]+:(?P<path>[^?#\s]+)",
            candidate,
        )
        if match is None:
            return None
        path = match.group("path")
    normalized = path.strip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    parts = normalized.split("/")
    if (
        len(parts) != 2
        or any(
            not part
            or part in (".", "..")
            or any(ord(character) < 33 for character in part)
            for part in parts
        )
    ):
        return None
    return "/".join(parts)


def _canonical_branch_candidate(value: object | None) -> str | None:
    if value is None:
        return None
    try:
        raw = os.fspath(value)
    except (TypeError, ValueError, OSError):
        return None
    if (
        not isinstance(raw, str)
        or raw != raw.strip()
        or not raw
        or raw.startswith("refs/")
        or raw.startswith("@{-")
        or "@{" in raw
        or len(raw) > 1024
        or len(raw.splitlines()) != 1
        or any(
            ord(character) < 32 or ord(character) == 127 for character in raw
        )
    ):
        return None
    return raw


def _status_flags(status: str) -> tuple[bool, bool, bool, bool]:
    index_dirty = False
    worktree_dirty = False
    untracked = False
    unmerged = False
    entries = status.split("\0")
    index = 0
    unmerged_codes = frozenset(("DD", "AU", "UD", "UA", "DU", "AA", "UU"))
    while index < len(entries):
        entry = entries[index]
        if not entry:
            index += 1
            continue
        if len(entry) < 3:
            raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)
        code = entry[:2]
        if code == "??":
            untracked = True
            worktree_dirty = True
        elif code == "!!":
            pass
        elif code in unmerged_codes or "U" in code:
            unmerged = True
        else:
            if code[0] not in (" ", "?"):
                index_dirty = True
            if code[1] not in (" ", "?"):
                worktree_dirty = True
        index += 2 if "R" in code or "C" in code else 1
    return index_dirty, worktree_dirty, untracked, unmerged


def _filter_overrides(root: Path) -> tuple[tuple[str, ...], str]:
    pattern = r"^filter\..*\.(clean|smudge|process|required)$"
    completed = _run_git(
        root,
        "config",
        "--includes",
        "--null",
        "--name-only",
        "--get-regexp",
        pattern,
        check=False,
    )
    if completed.returncode == 1:
        raw = ""
    elif completed.returncode == 0:
        raw = completed.stdout
    else:
        raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)

    prefixes: set[str] = set()
    for key in raw.split("\0"):
        if not key:
            continue
        match = re.fullmatch(
            r"(?P<prefix>filter\..+)\.(?:clean|smudge|process|required)",
            key,
            re.IGNORECASE,
        )
        if (
            match is None
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in key
            )
        ):
            raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)
        prefixes.add(match.group("prefix"))

    overrides: list[str] = []
    for prefix in sorted(prefixes):
        for facet, value in (
            ("process", ""),
            ("clean", ""),
            ("smudge", ""),
            ("required", "false"),
        ):
            overrides.extend(("-c", f"{prefix}.{facet}={value}"))
    return tuple(overrides), hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _index_visibility(root: Path) -> tuple[str, bool, bool]:
    output = _run_git(root, "ls-files", "-v", "-z").stdout
    hidden = False
    for entry in output.split("\0"):
        if not entry:
            continue
        if len(entry) < 3 or entry[1] != " ":
            raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)
        tag = entry[0]
        if tag.islower() or tag.upper() == "S":
            hidden = True
    stage_output = _run_git(root, "ls-files", "--stage", "-z").stdout
    gitlink = False
    for entry in stage_output.split("\0"):
        if not entry:
            continue
        metadata, separator, _ = entry.partition("\t")
        fields = metadata.split(" ")
        if (
            separator != "\t"
            or len(fields) != 3
            or not fields[0]
            or not fields[1]
            or not fields[2]
        ):
            raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)
        if fields[0] == "160000":
            gitlink = True
    return output + "\0" + stage_output, hidden, gitlink


def _operation_state(
    root: Path,
) -> tuple[tuple[str, tuple[int, int, int, int, int]], ...]:
    names = (
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "REBASE_HEAD",
        "AUTO_MERGE",
        "BISECT_LOG",
        "BISECT_START",
        "sequencer",
        "rebase-merge",
        "rebase-apply",
    )
    present: list[tuple[str, tuple[int, int, int, int, int]]] = []
    for name in names:
        result = _run_git(root, "rev-parse", "--git-path", name)
        supplied = result.stdout.rstrip("\n")
        if not supplied or "\n" in supplied or "\r" in supplied:
            raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)
        path = Path(supplied if os.path.isabs(supplied) else root / supplied)
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise HandoffProcessError(
                REPOSITORY_CONTEXT_UNAVAILABLE
            ) from exc
        present.append(
            (
                name,
                (
                    metadata.st_dev,
                    metadata.st_ino,
                    metadata.st_mode,
                    metadata.st_size,
                    metadata.st_mtime_ns,
                ),
            )
        )
    return tuple(present)


def _capture_snapshot(
    repo_root: Path | str | os.PathLike[str],
    canonical_branch: object | None = None,
) -> _RepositorySnapshot:
    """Capture only local Git facts needed for one assessment boundary."""

    try:
        supplied = Path(os.path.abspath(os.fspath(repo_root)))
        if not supplied.is_dir():
            raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)
        supplied_metadata = supplied.lstat()
    except HandoffProcessError:
        raise
    except (TypeError, ValueError, OSError) as exc:
        raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE) from exc

    root_result = _run_git(supplied, "rev-parse", "--show-toplevel")
    try:
        root_text = root_result.stdout.rstrip("\n")
        if not root_text or "\n" in root_text or "\r" in root_text:
            raise ValueError
        observed_root = Path(os.path.abspath(root_text))
        if (
            not observed_root.is_dir()
            or os.path.realpath(supplied) != os.path.realpath(observed_root)
        ):
            raise ValueError
        resolved_root = Path(os.path.realpath(observed_root))
        root_metadata = resolved_root.stat()
        if not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError
    except (TypeError, ValueError, OSError) as exc:
        raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE) from exc

    root = resolved_root
    head = _run_git(root, "rev-parse", "--verify", "HEAD").stdout.strip()
    if re.fullmatch(r"[0-9a-fA-F]{40,64}", head) is None:
        raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)

    branch_result = _run_git(
        root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    branch = (
        branch_result.stdout.strip() if branch_result.returncode == 0 else None
    )
    if branch is not None and (
        not branch or "\n" in branch or "\r" in branch
    ):
        raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)

    origin_result = _run_git(
        root,
        "config",
        "--local",
        "--get",
        "remote.origin.url",
        check=False,
    )
    origin = (
        origin_result.stdout.rstrip("\n")
        if origin_result.returncode == 0
        else None
    )
    if origin is not None and ("\n" in origin or "\r" in origin):
        origin = None

    canonical = _canonical_branch_candidate(canonical_branch)
    canonical_tip: str | None = None
    if canonical is not None:
        branch_check = _run_git(
            root,
            "check-ref-format",
            "--branch",
            canonical,
            check=False,
        )
        if branch_check.returncode == 0:
            canonical_result = _run_git(
                root,
                "show-ref",
                "--verify",
                "--hash",
                f"refs/heads/{canonical}",
                check=False,
            )
            candidate_tip = canonical_result.stdout.strip()
            if (
                canonical_result.returncode == 0
                and re.fullmatch(r"[0-9a-fA-F]{40,64}", candidate_tip)
                is not None
            ):
                canonical_tip = candidate_tip.lower()
            else:
                canonical = None
        else:
            canonical = None

    filter_overrides, filter_digest = _filter_overrides(root)
    status = _run_git(
        root,
        *filter_overrides,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignore-submodules=all",
    ).stdout
    _, closing_filter_digest = _filter_overrides(root)
    if closing_filter_digest != filter_digest:
        raise _Unstable
    index_dirty, worktree_dirty, untracked, unmerged = _status_flags(status)
    (
        index_visibility,
        hidden_index_entries,
        gitlink_present,
    ) = _index_visibility(root)
    operations = _operation_state(root)
    worktree_dirty = (
        worktree_dirty or hidden_index_entries or gitlink_present
    )
    unmerged = unmerged or bool(operations)
    status_digest = hashlib.sha256(
        (
            status
            + "\0"
            + index_visibility
            + "\0"
            + repr(operations)
            + "\0"
            + filter_digest
        ).encode("utf-8", errors="surrogateescape")
    ).hexdigest()
    return _RepositorySnapshot(
        root,
        supplied,
        resolved_root,
        (
            root_metadata.st_dev,
            root_metadata.st_ino,
            root_metadata.st_mode,
        ),
        (
            supplied_metadata.st_dev,
            supplied_metadata.st_ino,
            supplied_metadata.st_mode,
        ),
        head.lower(),
        branch,
        origin,
        _origin_slug(origin),
        canonical,
        canonical_tip,
        status_digest,
        index_dirty,
        worktree_dirty,
        untracked,
        unmerged,
    )


def _capture_repository_snapshot(
    repo_root: Path | str | os.PathLike[str],
    canonical_branch: object | None = None,
) -> _RepositorySnapshot:
    """Patchable repository-snapshot seam used at both boundaries."""

    return _capture_snapshot(repo_root, canonical_branch)


def _file_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _directory_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def _trusted_root_spellings(root: Path) -> tuple[Path, ...]:
    """Return equivalent spellings only for aliases above the worktree root."""

    candidates = [root, Path(os.path.realpath(root))]
    resolved_text = os.fspath(candidates[-1])
    for system_prefix in ("/private/var", "/private/tmp", "/private/etc"):
        if (
            resolved_text == system_prefix
            or resolved_text.startswith(system_prefix + os.sep)
        ):
            alias = Path(resolved_text[len("/private") :])
            if os.path.realpath(alias) == resolved_text:
                candidates.append(alias)
            break
    return tuple(dict.fromkeys(candidates))


def _input_parts(
    root: Path,
    handoff_path: Path | str | os.PathLike[str],
    invocation_root: Path | None = None,
) -> tuple[str, ...]:
    try:
        supplied = os.fspath(handoff_path)
        if not supplied or "\x00" in supplied:
            raise _ArtifactInputError("INPUT_MISSING")
        if ".." in Path(supplied).parts:
            raise _ArtifactInputError("INPUT_OUTSIDE_ROOT")
        absolute = Path(
            os.path.abspath(supplied if os.path.isabs(supplied) else root / supplied)
        )
        relative: Path | None = None
        trusted_roots = list(_trusted_root_spellings(root))
        if (
            invocation_root is not None
            and os.path.realpath(invocation_root) == os.path.realpath(root)
        ):
            trusted_roots.insert(0, invocation_root)
        for trusted_root in tuple(dict.fromkeys(trusted_roots)):
            try:
                relative = absolute.relative_to(trusted_root)
                break
            except ValueError:
                continue
        if relative is None:
            raise _ArtifactInputError("INPUT_OUTSIDE_ROOT")
        if not relative.parts:
            raise _ArtifactInputError("INPUT_NOT_REGULAR")
        if any(part in ("", ".", "..") for part in relative.parts):
            raise _ArtifactInputError("INPUT_OUTSIDE_ROOT")
        return tuple(relative.parts)
    except _ArtifactInputError:
        raise
    except (TypeError, ValueError, OSError) as exc:
        raise _ArtifactInputError("INPUT_MISSING") from exc


def _read_parts(
    root: Path,
    parts: Sequence[str],
    *,
    initial: bool,
) -> _InputSnapshot:
    try:
        directory_fd = os.open(Path(os.path.realpath(root)), _directory_flags())
    except OSError as exc:
        if initial:
            raise _ArtifactInputError("INPUT_UNREADABLE") from exc
        raise _Unstable from exc

    try:
        for component in parts[:-1]:
            try:
                metadata = os.stat(
                    component, dir_fd=directory_fd, follow_symlinks=False
                )
            except FileNotFoundError as exc:
                if initial:
                    raise _ArtifactInputError("INPUT_MISSING") from exc
                raise _Unstable from exc
            except OSError as exc:
                if initial:
                    raise _ArtifactInputError("INPUT_UNREADABLE") from exc
                raise _Unstable from exc
            if stat.S_ISLNK(metadata.st_mode):
                if initial:
                    raise _ArtifactInputError(
                        "INPUT_SYMLINK", _file_identity(metadata)
                    )
                raise _Unstable
            if not stat.S_ISDIR(metadata.st_mode):
                if initial:
                    raise _ArtifactInputError(
                        "INPUT_MISSING", _file_identity(metadata)
                    )
                raise _Unstable
            try:
                next_fd = os.open(
                    component, _directory_flags(), dir_fd=directory_fd
                )
            except OSError as exc:
                if initial and exc.errno == errno.ELOOP:
                    raise _ArtifactInputError("INPUT_SYMLINK") from exc
                if initial:
                    raise _ArtifactInputError("INPUT_UNREADABLE") from exc
                raise _Unstable from exc
            try:
                opened_metadata = os.fstat(next_fd)
            except OSError as exc:
                os.close(next_fd)
                if initial:
                    raise _ArtifactInputError("INPUT_UNREADABLE") from exc
                raise _Unstable from exc
            if (
                not stat.S_ISDIR(opened_metadata.st_mode)
                or opened_metadata.st_dev != metadata.st_dev
                or opened_metadata.st_ino != metadata.st_ino
            ):
                os.close(next_fd)
                raise _Unstable
            os.close(directory_fd)
            directory_fd = next_fd

        name = parts[-1]
        try:
            before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError as exc:
            if initial:
                raise _ArtifactInputError("INPUT_MISSING") from exc
            raise _Unstable from exc
        except OSError as exc:
            if initial:
                raise _ArtifactInputError("INPUT_UNREADABLE") from exc
            raise _Unstable from exc

        if stat.S_ISLNK(before.st_mode):
            if initial:
                raise _ArtifactInputError(
                    "INPUT_SYMLINK", _file_identity(before)
                )
            raise _Unstable
        if not stat.S_ISREG(before.st_mode):
            if initial:
                raise _ArtifactInputError(
                    "INPUT_NOT_REGULAR", _file_identity(before)
                )
            raise _Unstable
        if before.st_size > MAX_INPUT_BYTES:
            if initial:
                raise _ArtifactInputError(
                    "INPUT_TOO_LARGE", _file_identity(before)
                )
            raise _Unstable

        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NONBLOCK"):
            flags |= os.O_NONBLOCK
        try:
            descriptor = os.open(name, flags, dir_fd=directory_fd)
        except OSError as exc:
            if initial and exc.errno == errno.ELOOP:
                raise _ArtifactInputError(
                    "INPUT_SYMLINK", _file_identity(before)
                ) from exc
            if initial:
                raise _ArtifactInputError(
                    "INPUT_UNREADABLE", _file_identity(before)
                ) from exc
            raise _Unstable from exc

        try:
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_dev != before.st_dev
                or opened.st_ino != before.st_ino
            ):
                raise _Unstable
            chunks: list[bytes] = []
            total = 0
            while total <= MAX_INPUT_BYTES:
                chunk = os.read(
                    descriptor,
                    min(64 * 1024, MAX_INPUT_BYTES + 1 - total),
                )
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
            if total > MAX_INPUT_BYTES:
                if initial:
                    raise _ArtifactInputError(
                        "INPUT_TOO_LARGE", _file_identity(before)
                    )
                raise _Unstable
            after = os.fstat(descriptor)
            after_path = os.stat(
                name, dir_fd=directory_fd, follow_symlinks=False
            )
            identity = _file_identity(before)
            if (
                identity != _file_identity(opened)
                or identity != _file_identity(after)
                or identity != _file_identity(after_path)
            ):
                raise _Unstable
            content = b"".join(chunks)
            return _InputSnapshot(
                tuple(parts),
                identity,
                hashlib.sha256(content).hexdigest(),
                content,
            )
        except OSError as exc:
            if initial:
                raise _ArtifactInputError(
                    "INPUT_UNREADABLE", _file_identity(before)
                ) from exc
            raise _Unstable from exc
        finally:
            os.close(descriptor)
    finally:
        os.close(directory_fd)


def _reread_input(root: Path, opening: _InputSnapshot) -> None:
    closing = _read_parts(root, opening.parts, initial=False)
    if (
        closing.identity != opening.identity
        or closing.digest != opening.digest
        or closing.content != opening.content
    ):
        raise _Unstable


def _decode_input(content: bytes) -> str:
    if content.startswith(b"\xef\xbb\xbf"):
        content = content[3:]
        if content.startswith(b"\xef\xbb\xbf"):
            raise _ArtifactInputError("INPUT_INVALID_UTF8")
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise _ArtifactInputError("INPUT_INVALID_UTF8") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _trusted_scalar(value: object) -> str:
    try:
        raw = os.fspath(value)
    except (TypeError, ValueError, OSError) as exc:
        raise HandoffProcessError(USAGE_ERROR) from exc
    if (
        not isinstance(raw, str)
        or len(raw.splitlines()) != 1
        or any(
            ord(character) < 32 or ord(character) == 127 for character in raw
        )
    ):
        raise HandoffProcessError(USAGE_ERROR)
    normalized = raw.strip()
    upper = normalized.upper()
    if (
        not normalized
        or upper
        in (
            "NONE",
            "UNKNOWN",
            "TBD",
            "?",
            "MAYBE",
            "EITHER",
            "CONDITIONAL",
            "PENDING",
        )
        or "?" in normalized
        or re.search(
            r"\b(?:OR|AND/OR|UNLESS|IF|WHEN|DEPENDING|"
            r"CONDITIONAL|PENDING|TBD|UNKNOWN|MAYBE|EITHER)\b",
            upper,
        )
        or "/" in normalized
        or "|" in normalized
    ):
        raise HandoffProcessError(USAGE_ERROR)
    return normalized


def _normalize_label(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[-_]+", " ", value)
    return " ".join(value.casefold().split())


def _strip_heading_tail(value: str) -> str:
    return re.sub(r"[ \t]+#+[ \t]*$", "", value.strip())


def _heading_at(line: str, index: int) -> _Heading | None:
    match = _HEADING_RE.fullmatch(line)
    if match is None or not match.group("title"):
        return None
    return _Heading(
        index,
        len(match.group("marks")),
        _strip_heading_tail(match.group("title")),
    )


def _registry_heading(title: str, registry: Sequence[str]) -> str | None:
    normalized = " ".join(title.upper().split())
    for entry in sorted(registry, key=len, reverse=True):
        if normalized == entry:
            return entry
        if (
            normalized.startswith(entry + ":")
            and normalized[len(entry) + 1 :].strip()
        ):
            return entry
        if (
            normalized.startswith(entry + " - ")
            and normalized[len(entry) + 3 :].strip()
        ):
            return entry
        if normalized.startswith(entry):
            tail = normalized[len(entry) :]
            if tail.lstrip().startswith("—") and tail.lstrip()[1:].strip():
                return entry
    return None


def _closing_fence(line: str, character: str, length: int) -> bool:
    return (
        re.fullmatch(
            rf"[ ]{{0,3}}{re.escape(character)}{{{length},}}[ \t]*", line
        )
        is not None
    )


def _strip_bullet(value: str) -> str:
    match = re.match(r"^[ ]{0,3}[-*+][ \t]+(.*)$", value)
    return match.group(1) if match is not None else value.lstrip(" ")


def _decorated_label(value: str) -> tuple[str, str, bool] | None:
    """Return label candidate, remainder, and whether colon was present."""

    candidate = _strip_bullet(value).rstrip()
    for wrapper in ("**", "__", "*", "_", "`"):
        if not candidate.startswith(wrapper):
            continue
        closing = candidate.find(wrapper, len(wrapper))
        if closing < 0:
            return None
        inner = candidate[len(wrapper) : closing]
        remainder = candidate[closing + len(wrapper) :]
        colon = False
        if inner.endswith(":"):
            inner = inner[:-1]
            colon = True
        horizontal_trimmed = remainder.lstrip(" \t")
        if horizontal_trimmed.startswith(":"):
            remainder = horizontal_trimmed[1:]
            colon = True
        return inner, remainder, colon
    if ":" in candidate:
        label, remainder = candidate.split(":", 1)
        return label, remainder, True
    return candidate, "", False


def _malformed_known_prefix(line: str) -> bool:
    candidate = _strip_bullet(line).strip()
    undecorated = candidate
    for wrapper in ("**", "__", "*", "_", "`"):
        if undecorated.startswith(wrapper):
            undecorated = undecorated[len(wrapper) :]
            break
    lowered = undecorated.casefold()
    for alias in LABEL_ALIASES:
        if lowered == alias:
            return False
        if lowered.startswith(alias):
            tail = lowered[len(alias) :]
            if tail and tail.lstrip().startswith(("=", ":", ";")):
                return True
    return False


def _field_header(line: str) -> tuple[str, str, str | None] | None:
    """Parse one finite field header; inline value is None for block form."""

    parsed = _decorated_label(line)
    if parsed is None:
        if _malformed_known_prefix(line):
            raise _MalformedRepresentation
        return None
    label_text, remainder, colon = parsed
    normalized_label = _normalize_label(label_text)
    field = LABEL_ALIASES.get(normalized_label)
    if field is None:
        if _malformed_known_prefix(line):
            raise _MalformedRepresentation
        return None
    if colon and remainder.lstrip().startswith(":"):
        raise _MalformedRepresentation
    if not colon:
        if remainder.strip():
            raise _MalformedRepresentation
        return field, normalized_label, None
    inline = remainder.strip()
    return field, normalized_label, inline or None


def _contains_field_header(lines: Sequence[str], start: int, end: int) -> bool:
    for line in lines[start:end]:
        if _field_header(line) is not None:
            return True
    return False


def _prehistory_structure(
    lines: Sequence[str],
) -> tuple[int, tuple[_Heading, ...]]:
    """Find the first historical heading while respecting finite fences."""

    headings: list[_Heading] = []
    fence_character: str | None = None
    fence_length = 0
    fence_start = -1
    cutoff = len(lines)
    for index, line in enumerate(lines):
        if cutoff != len(lines):
            if (
                fence_character is not None
                and _closing_fence(line, fence_character, fence_length)
            ):
                return cutoff, tuple(headings)
            continue
        if fence_character is not None:
            if _closing_fence(line, fence_character, fence_length):
                fence_character = None
                fence_length = 0
                fence_start = -1
                continue
        else:
            fence_match = _FENCE_RE.fullmatch(line)
            if fence_match is not None:
                fence = fence_match.group("fence")
                fence_character = fence[0]
                fence_length = len(fence)
                fence_start = index
                continue
        heading = _heading_at(line, index)
        if heading is None:
            continue
        if (
            _registry_heading(heading.title, HISTORICAL_HEADINGS) is not None
        ):
            cutoff = index
            if fence_character is None:
                return cutoff, tuple(headings)
        else:
            headings.append(heading)
    if cutoff != len(lines):
        raise _MalformedRepresentation
    if (
        fence_character is not None
        and _contains_field_header(lines, fence_start + 1, len(lines))
    ):
        raise _MalformedRepresentation
    return cutoff, tuple(headings)


def _extract_occurrences(
    lines: Sequence[str], start: int, end: int
) -> tuple[_Occurrence, ...]:
    occurrences: list[_Occurrence] = []
    index = start
    fence_character: str | None = None
    fence_length = 0
    while index < end:
        line = lines[index]
        if fence_character is not None and _closing_fence(
            line, fence_character, fence_length
        ):
            fence_character = None
            fence_length = 0
            index += 1
            continue
        fence_match = _FENCE_RE.fullmatch(line)
        if fence_character is None and fence_match is not None:
            fence = fence_match.group("fence")
            fence_character = fence[0]
            fence_length = len(fence)
            index += 1
            continue
        header = _field_header(line)
        if header is None:
            index += 1
            continue
        field, label, inline = header
        value_lines: list[str] = [inline] if inline is not None else []
        cursor = index + 1
        while cursor < end:
            candidate = lines[cursor]
            if fence_character is not None and _closing_fence(
                candidate, fence_character, fence_length
            ):
                break
            if _FENCE_RE.fullmatch(candidate) is not None:
                break
            if _heading_at(candidate, cursor) is not None:
                break
            if _field_header(candidate) is not None:
                break
            value_lines.append(candidate)
            cursor += 1
        while value_lines and not value_lines[0].strip():
            value_lines.pop(0)
        while value_lines and not value_lines[-1].strip():
            value_lines.pop()
        if not value_lines or not any(line.strip() for line in value_lines):
            raise _MalformedRepresentation
        occurrences.append(_Occurrence(field, label, "\n".join(value_lines)))
        index = cursor
    return tuple(occurrences)


def _select_record(text: str) -> tuple[_Occurrence, ...]:
    lines = text.split("\n")
    cutoff, headings = _prehistory_structure(lines)
    operative = tuple(
        heading
        for heading in headings
        if _registry_heading(heading.title, OPERATIVE_HEADINGS) is not None
    )
    if len(operative) > 1:
        raise _ArtifactInputError("CURRENT_RECORD_AMBIGUOUS")
    if operative:
        selected = operative[0]
        end = cutoff
        for heading in headings:
            if heading.line > selected.line and heading.level <= selected.level:
                end = heading.line
                break
        inside = _extract_occurrences(lines, selected.line, end)
        outside = (
            _extract_occurrences(lines, 0, selected.line)
            + _extract_occurrences(lines, end, cutoff)
        )
        if outside:
            raise _ArtifactInputError("CURRENT_RECORD_AMBIGUOUS")
        if not inside:
            raise _ArtifactInputError("UNSUPPORTED_VARIANT")
        return inside

    raise _ArtifactInputError("UNSUPPORTED_VARIANT")


def _normalized_lines(value: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line.strip()) for line in value.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _native_scalar(value: str, *, trailing_period: bool = True) -> str:
    normalized = " ".join(_normalized_lines(value).split()).casefold()
    if trailing_period and normalized.endswith("."):
        normalized = normalized[:-1].rstrip()
    return normalized


def _normalize_branch(value: str) -> str:
    scalar = value.strip()
    if scalar.startswith("refs/heads/"):
        scalar = scalar[len("refs/heads/") :]
    return scalar


def _repository_facet(label: str, value: str) -> str:
    if label in ("repo root", "repository root"):
        return "root"
    if label == "repository identity":
        return "identity"
    stripped = value.strip()
    return "root" if os.path.isabs(stripped) or stripped in (".", "./") else "identity"


def _control(value: str, registry: Mapping[str, str]) -> _Control | None:
    if "\n" in value or _unresolved_code(value) is not None:
        return None
    scalar = re.sub(r"[ \t]+", " ", value.strip())
    upper = scalar.upper()
    for surface in sorted(registry, key=len, reverse=True):
        if upper == surface:
            return _Control(registry[surface], True)
        if not upper.startswith(surface):
            continue
        tail = scalar[len(surface) :]
        if re.fullmatch(
            r"(?:[ \t]*:[ \t]*|[ \t]+-[ \t]+|[ \t]*—[ \t]*)\S(?:.*\S)?",
            tail,
        ):
            return _Control(registry[surface], False)
    return None


def _comparison_value(field: str, value: str) -> object:
    if field == "active_branch":
        return _normalize_branch(_normalized_lines(value))
    if field == "current_state":
        control = _control(value, STATE_TOKENS)
        if control is not None:
            return (
                ("CONTROL", control.token)
                if control.exact
                else ("QUALIFIED_CONTROL", control.token, _native_scalar(value))
            )
        return _native_scalar(value)
    if field == "current_gate":
        control = _control(value, GATE_TOKENS)
        if control is not None:
            return (
                ("CONTROL", control.token)
                if control.exact
                else ("QUALIFIED_CONTROL", control.token, _native_scalar(value))
            )
        return _native_scalar(value)
    return _native_scalar(value)


def _project_record(
    occurrences: Sequence[_Occurrence],
    root: Path,
) -> _CanonicalRecord:
    grouped: dict[str, list[_Occurrence]] = {
        field: [] for field in CANONICAL_FIELDS
    }
    for occurrence in occurrences:
        grouped[occurrence.field].append(occurrence)

    values: dict[str, str] = {}
    repository_values: list[tuple[str, str]] = []
    conflicts: set[str] = set()
    for field in CANONICAL_FIELDS:
        group = grouped[field]
        if not group:
            continue
        if field == "repository_reference":
            facets: dict[str, tuple[object, str]] = {}
            for occurrence in group:
                facet = _repository_facet(occurrence.label, occurrence.value)
                if facet == "root":
                    supplied = occurrence.value.strip()
                    try:
                        comparison: object = os.path.realpath(
                            supplied if os.path.isabs(supplied) else root / supplied
                        )
                    except (TypeError, ValueError, OSError):
                        comparison = _native_scalar(occurrence.value)
                else:
                    comparison = _native_scalar(
                        occurrence.value, trailing_period=False
                    )
                    if isinstance(comparison, str) and comparison.endswith(".git"):
                        comparison = comparison[:-4]
                prior = facets.get(facet)
                if prior is not None and prior[0] != comparison:
                    conflicts.add(field)
                    continue
                facets[facet] = (comparison, occurrence.value)
            repository_values.extend(
                (facet, pair[1]) for facet, pair in sorted(facets.items())
            )
            continue
        comparisons = {
            _comparison_value(field, occurrence.value) for occurrence in group
        }
        if len(comparisons) > 1:
            conflicts.add(field)
            continue
        values[field] = group[0].value
    return _CanonicalRecord(
        values,
        tuple(repository_values),
        frozenset(conflicts),
        any(
            occurrence.label == "v13 gate"
            for occurrence in grouped["current_gate"]
        ),
    )


def _explicit_none(value: str) -> bool:
    return _native_scalar(value) == "none"


def _unresolved_code(value: str) -> str | None:
    normalized = _normalized_lines(value)
    upper = normalized.upper()
    if not normalized:
        return "FIELD_UNKNOWN"
    if upper == "NONE":
        return None
    if (
        upper in ("UNKNOWN", "TBD", "?")
        or re.fullmatch(r"<[^<>\n]+>", normalized) is not None
        or re.search(r"(?:^|\s)\?(?:$|\s)", normalized) is not None
        or re.search(
            r"(?<![A-Z0-9_./-])(?:UNKNOWN|TBD|TODO|UNDECIDED)"
            r"(?![A-Z0-9_./-])",
            upper,
        )
        or re.search(
            r"(?<![A-Z0-9_./-])(?:IF|UNLESS|WHEN|PENDING|DEPENDING|"
            r"CONDITIONAL|MAYBE|EITHER)(?![A-Z0-9_./-])",
            upper,
        )
    ):
        return "FIELD_UNKNOWN"
    if (
        "|" in normalized
        or re.search(
            r"(?<![A-Z0-9_./-])(?:OR|AND/OR)(?![A-Z0-9_./-])", upper
        )
        or re.search(r"[ \t]/[ \t]", normalized)
    ):
        return "FIELD_AMBIGUOUS"
    return None


def _document_branch(
    value: str,
    snapshot: _RepositorySnapshot,
) -> str | None:
    if "\n" in value:
        return None
    branch = _normalize_branch(value.strip())
    if not branch or _unresolved_code(branch) is not None:
        return None
    completed = _run_git(
        snapshot.root,
        "check-ref-format",
        "--branch",
        branch,
        check=False,
    )
    return branch if completed.returncode == 0 else None


def _evaluate_repository_reference(
    record: _CanonicalRecord,
    snapshot: _RepositorySnapshot,
    issues: set[str],
) -> None:
    if "repository_reference" in record.conflict_fields:
        return
    validated: list[tuple[str, Path | str]] = []
    field_issues: set[str] = set()
    for facet, raw in record.repository_values:
        unresolved = _unresolved_code(raw)
        if _explicit_none(raw) or unresolved is not None or "\n" in raw:
            field_issues.add(unresolved or "FIELD_UNKNOWN")
            continue
        if facet == "root":
            try:
                supplied = raw.strip()
                candidate = Path(
                    os.path.realpath(
                        supplied
                        if os.path.isabs(supplied)
                        else snapshot.root / supplied
                    )
                )
            except (TypeError, ValueError, OSError):
                field_issues.add("FIELD_UNKNOWN")
                continue
            validated.append((facet, candidate))
            continue
        slug = raw.strip()
        if slug.endswith(".git"):
            slug = slug[:-4]
        parts = slug.split("/")
        if (
            len(parts) != 2
            or any(
                not part
                or part in (".", "..")
                or any(ord(character) < 33 for character in part)
                for part in parts
            )
        ):
            field_issues.add("FIELD_UNKNOWN")
        else:
            validated.append((facet, slug))
    if field_issues:
        issues.update(field_issues)
        return
    for facet, value in validated:
        if facet == "root":
            if value != snapshot.resolved_root:
                issues.add("REPOSITORY_MISMATCH")
        elif snapshot.origin_slug is None:
            issues.add("REPOSITORY_REFERENCE_UNRESOLVED")
        elif value != snapshot.origin_slug:
            issues.add("REPOSITORY_MISMATCH")


def _routine_work_returned(value: str) -> bool:
    normalized = _native_scalar(value)
    return (
        re.fullmatch(
            r"(?:return|assign|give|send) (?:the )?"
            r"(?:routine work|routine cleanup) to (?:the )?decision owner",
            normalized,
        )
        is not None
        or re.fullmatch(
            r"(?:routine work|routine cleanup) "
            r"(?:is|must be|will be) "
            r"(?:returned|assigned|given|sent) to (?:the )?decision owner",
            normalized,
        )
        is not None
        or re.fullmatch(
            r"(?:the )?decision owner "
            r"(?:owns|handles|performs|must do|will do) "
            r"(?:the )?(?:routine work|routine cleanup)",
            normalized,
        )
        is not None
    )


def _required_fields(record: _CanonicalRecord, issues: set[str]) -> None:
    if record.conflict_fields:
        issues.add("FIELD_CONFLICT")
    for field in CANONICAL_FIELDS:
        present = (
            bool(record.repository_values)
            if field == "repository_reference"
            else field in record.values
        )
        if not present and field not in record.conflict_fields:
            issues.add("REQUIRED_FIELD_ABSENT")


def _field_unresolved_issues(
    record: _CanonicalRecord,
    issues: set[str],
) -> None:
    for field, value in record.values.items():
        if field in record.conflict_fields:
            continue
        unresolved = _unresolved_code(value)
        if unresolved is not None:
            issues.add(unresolved)
    for _, value in record.repository_values:
        unresolved = _unresolved_code(value)
        if unresolved is not None:
            issues.add(unresolved)


def _evaluate_closed_git(
    snapshot: _RepositorySnapshot,
    issues: set[str],
) -> None:
    if snapshot.canonical_branch is None or snapshot.canonical_tip is None:
        issues.add("CANONICAL_BRANCH_UNKNOWN")
    if snapshot.branch is None:
        issues.add("DETACHED_HEAD")
    elif (
        snapshot.canonical_branch is not None
        and snapshot.canonical_tip is not None
        and (
            snapshot.branch != snapshot.canonical_branch
            or snapshot.head != snapshot.canonical_tip
        )
    ):
        issues.add("CLOSED_BRANCH_MISMATCH")
    if snapshot.unmerged:
        issues.add("LOCAL_CHANGES_UNRESOLVED")
    else:
        if snapshot.index_dirty:
            issues.add("INDEX_DIRTY")
        if snapshot.worktree_dirty or snapshot.untracked:
            issues.add("WORKTREE_DIRTY")


def _evaluate_record(
    record: _CanonicalRecord,
    snapshot: _RepositorySnapshot,
    expected_receiver: str,
    expected_target_layer: str,
) -> HandoffAssessment:
    issues: set[str] = set()
    _required_fields(record, issues)
    _field_unresolved_issues(record, issues)
    _evaluate_repository_reference(record, snapshot, issues)

    target_raw = record.values.get("target_layer")
    if target_raw is not None and _unresolved_code(target_raw) is None:
        if _native_scalar(target_raw) != _native_scalar(expected_target_layer):
            issues.add("TARGET_LAYER_MISMATCH")
    if record.v13_gate_alias and (
        _native_scalar(expected_target_layer) != "v13"
        or target_raw is None
        or _native_scalar(target_raw) != "v13"
    ):
        issues.add("TARGET_LAYER_MISMATCH")

    state_raw = record.values.get("current_state")
    gate_raw = record.values.get("current_gate")
    state = _control(state_raw, STATE_TOKENS) if state_raw is not None else None
    gate = _control(gate_raw, GATE_TOKENS) if gate_raw is not None else None
    if (
        state_raw is not None
        and _unresolved_code(state_raw) is None
        and state is None
    ):
        issues.add("FIELD_UNKNOWN")
    if gate_raw is not None and _unresolved_code(gate_raw) is None and gate is None:
        issues.add("FIELD_UNKNOWN")

    mode: str | None = None
    if state is not None:
        mode = MODE_CLOSED_STATE if state.token == "CLOSED" else MODE_ACTIVE_TRANSFER
    if state is not None and gate is not None:
        allowed_pair = (
            state.token == "ACTIVE"
            or (
                state.token == "RESTRICTED"
                and gate.token in ("HOLD", "CAP", "BLOCK")
            )
            or (
                state.token == "CLOSED"
                and state.exact
                and gate.token in ("HOLD", "BLOCK")
                and gate.exact
            )
        )
        if not allowed_pair:
            issues.add("STATE_GATE_CONFLICT")

    branch_raw = record.values.get("active_branch")
    branch: str | None = None
    if (
        branch_raw is not None
        and not _explicit_none(branch_raw)
        and _unresolved_code(branch_raw) is None
    ):
        branch = _document_branch(branch_raw, snapshot)
        if branch is None:
            issues.add("FIELD_UNKNOWN")

    next_owner_raw = record.values.get("next_owner")
    next_action_raw = record.values.get("next_authorized_action")
    first_action_raw = record.values.get("first_one_action")
    completion_raw = record.values.get("completion_line")
    boundary_raw = record.values.get("do_not_continue_boundary")
    receiving_raw = record.values.get("receiving_ownership")
    retained_raw = record.values.get("ai_retained_work")

    if retained_raw is not None and _routine_work_returned(retained_raw):
        issues.add("ROUTINE_WORK_RETURNED")

    if mode == MODE_ACTIVE_TRANSFER:
        if branch_raw is not None:
            if (
                _explicit_none(branch_raw)
                or branch is None
                or snapshot.branch is None
                or branch != snapshot.branch
            ):
                issues.add("ACTIVE_BRANCH_MISMATCH")

        if next_owner_raw is not None and (
            _explicit_none(next_owner_raw)
            or _unresolved_code(next_owner_raw) is not None
            or _native_scalar(next_owner_raw) != _native_scalar(expected_receiver)
        ):
            issues.add("OWNER_MISMATCH")
        if receiving_raw is not None and _explicit_none(receiving_raw):
            issues.add("OWNER_MISMATCH")
        if retained_raw is not None and _explicit_none(retained_raw):
            issues.add("ROUTINE_WORK_RETURNED")

        if first_action_raw is not None and _explicit_none(first_action_raw):
            issues.add("FIRST_ACTION_NONE_ACTIVE")
        if next_action_raw is not None and _explicit_none(next_action_raw):
            issues.add("ACTION_RELATION_UNPROVEN")
        if (
            next_action_raw is not None
            and first_action_raw is not None
            and not _explicit_none(next_action_raw)
            and not _explicit_none(first_action_raw)
            and _native_scalar(next_action_raw) != _native_scalar(first_action_raw)
        ):
            issues.add("ACTION_RELATION_UNPROVEN")
        if (
            completion_raw is not None
            and _native_scalar(completion_raw) in CLOSED_COMPLETION_VALUES
        ):
            issues.add("COMPLETION_CLOSURE_CONFLICT")

        structural_blockers = {
            "REQUIRED_FIELD_ABSENT",
            "FIELD_UNKNOWN",
            "FIELD_AMBIGUOUS",
            "FIELD_CONFLICT",
        }
        if not structural_blockers.intersection(issues):
            issues.add("SEMANTIC_REVIEW_REQUIRED")

    elif mode == MODE_CLOSED_STATE:
        for field in CLOSED_CONJUNCTION_NONE_FIELDS:
            value = record.values.get(field)
            if (
                value is not None
                and not _explicit_none(value)
                and _unresolved_code(value) is None
            ):
                issues.add("CLOSED_STATE_INCOMPLETE")
        if (
            next_owner_raw is not None
            and not _explicit_none(next_owner_raw)
            and _unresolved_code(next_owner_raw) is None
        ):
            if _native_scalar(next_owner_raw) == _native_scalar(
                expected_receiver
            ):
                issues.add("CLOSED_STATE_INCOMPLETE")
            else:
                issues.add("SEMANTIC_REVIEW_REQUIRED")
        for field in ("receiving_ownership", "ai_retained_work"):
            value = record.values.get(field)
            if (
                value is not None
                and not _explicit_none(value)
                and _unresolved_code(value) is None
            ):
                issues.add("SEMANTIC_REVIEW_REQUIRED")

        completion = (
            _native_scalar(completion_raw)
            if completion_raw is not None
            else None
        )
        if completion in OPEN_COMPLETION_VALUES:
            issues.add("COMPLETION_CLOSURE_CONFLICT")
        elif (
            completion_raw is not None
            and _unresolved_code(completion_raw) is None
            and completion not in CLOSED_COMPLETION_VALUES
        ):
            issues.add("SEMANTIC_REVIEW_REQUIRED")

        boundary = (
            _native_scalar(boundary_raw) if boundary_raw is not None else None
        )
        if (
            boundary_raw is not None
            and _unresolved_code(boundary_raw) is None
            and boundary not in CLOSED_BOUNDARY_VALUES
        ):
            issues.add("SEMANTIC_REVIEW_REQUIRED")

        _evaluate_closed_git(snapshot, issues)
    elif mode is None and state_raw is not None:
        issues.add("FIELD_UNKNOWN")

    if issues:
        return _assessment(RESULT_NOT_ACCEPTABLE, issues=issues)
    if mode != MODE_CLOSED_STATE:
        return _assessment(
            RESULT_NOT_ACCEPTABLE, issues=("SEMANTIC_REVIEW_REQUIRED",)
        )
    return _assessment(RESULT_ACCEPTABLE, mode=MODE_CLOSED_STATE)


def _same_repository_snapshot(
    opening: _RepositorySnapshot,
    closing: _RepositorySnapshot,
) -> bool:
    return opening == closing


def assess_handoff(
    *,
    repo_root: Path | str | os.PathLike[str],
    handoff_path: Path | str | os.PathLike[str],
    expected_receiver: str,
    expected_target_layer: str,
    canonical_branch: Path | str | os.PathLike[str] | None = None,
) -> HandoffAssessment:
    """Assess one explicit handoff against one stable local Git snapshot."""

    try:
        receiver = _trusted_scalar(expected_receiver)
        target_layer = _trusted_scalar(expected_target_layer)
        opening_repository = _capture_repository_snapshot(
            repo_root, canonical_branch
        )
        opening_input: _InputSnapshot | None = None
        opening_input_error: _ArtifactInputError | None = None
        assessment: HandoffAssessment

        try:
            parts = _input_parts(
                opening_repository.root,
                handoff_path,
                opening_repository.invocation_root,
            )
            opening_input = _read_parts(
                opening_repository.root, parts, initial=True
            )
            text = _decode_input(opening_input.content)
        except _ArtifactInputError as exc:
            opening_input_error = exc
            assessment = _assessment(RESULT_INVALID, issues=(exc.code,))
        else:
            try:
                occurrences = _select_record(text)
                record = _project_record(occurrences, opening_repository.root)
            except _MalformedRepresentation:
                assessment = _assessment(
                    RESULT_INVALID, issues=("MALFORMED_REPRESENTATION",)
                )
            except _ArtifactInputError as exc:
                assessment = _assessment(
                    RESULT_NOT_ACCEPTABLE, issues=(exc.code,)
                )
            else:
                assessment = _evaluate_record(
                    record,
                    opening_repository,
                    receiver,
                    target_layer,
                )

        try:
            closing_repository = _capture_repository_snapshot(
                opening_repository.invocation_root, canonical_branch
            )
        except HandoffProcessError as exc:
            raise _Unstable from exc
        if not _same_repository_snapshot(
            opening_repository, closing_repository
        ):
            raise _Unstable
        if opening_input is not None:
            _reread_input(opening_repository.root, opening_input)
        elif opening_input_error is not None:
            try:
                closing_parts = _input_parts(
                    opening_repository.root,
                    handoff_path,
                    opening_repository.invocation_root,
                )
                _read_parts(
                    opening_repository.root,
                    closing_parts,
                    initial=True,
                )
            except _ArtifactInputError as exc:
                if (
                    exc.code != opening_input_error.code
                    or exc.identity != opening_input_error.identity
                ):
                    raise _Unstable from exc
            else:
                raise _Unstable
        _validate_assessment(assessment)
        return assessment
    except _Unstable:
        process_error = UNSTABLE_SNAPSHOT
    except HandoffProcessError as exc:
        process_error = exc.code
    except Exception:
        process_error = INTERNAL_ERROR

    raise HandoffProcessError(process_error)
