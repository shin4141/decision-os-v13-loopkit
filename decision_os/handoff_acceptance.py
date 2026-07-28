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
import stat
import subprocess
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlsplit


SCHEMA_VERSION = "handoff-acceptance/v0.1"
MAX_INPUT_BYTES = 1024 * 1024

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
    "ACTION_BRANCH_MISMATCH",
    "OWNER_MISMATCH",
    "ROUTINE_WORK_RETURNED",
    "ACTION_RELATION_UNPROVEN",
    "GATE_ACTION_CONFLICT",
    "FIRST_ACTION_NONE_ACTIVE",
    "FIRST_ACTION_UNSAFE",
    "BOUNDARY_CONFLICT",
    "COMPLETION_CLOSURE_CONFLICT",
    "MISSING_CLOSURE_UNASSIGNED",
    "MISSING_CLOSURE_NO_ACTION",
    "CLOSED_STATE_INCOMPLETE",
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
    "what you own now": "receiving_ownership",
    "receiving ai owns": "receiving_ownership",
    "receiving ownership": "receiving_ownership",
    "first one action": "first_one_action",
    "first action": "first_one_action",
    "do not continue boundary": "do_not_continue_boundary",
    "stop boundary": "do_not_continue_boundary",
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

ROUTINE_WORK_KINDS = frozenset(
    (
        "INVESTIGATION",
        "IMPLEMENTATION",
        "VALIDATION",
        "TEST",
        "REVIEW",
        "GIT",
        "CLEANUP",
        "DOCUMENTATION",
    )
)
DECISION_WORK_KINDS = frozenset(("DECISION", "AUTHORITY"))
WORK_KINDS = ROUTINE_WORK_KINDS | DECISION_WORK_KINDS

ACTION_TOKENS = {
    "READ": "OBSERVE",
    "INSPECT": "OBSERVE",
    "VERIFY": "OBSERVE",
    "VALIDATE": "OBSERVE",
    "COMPARE": "OBSERVE",
    "CALCULATE": "OBSERVE",
    "REPORT": "REPORT",
    "RETURN": "REPORT",
    "IMPLEMENT": "LOCAL_CHANGE",
    "ADD": "LOCAL_CHANGE",
    "CREATE": "LOCAL_CHANGE",
    "EDIT": "LOCAL_CHANGE",
    "MODIFY": "LOCAL_CHANGE",
    "REMOVE": "LOCAL_CHANGE",
    "TEST": "TEST",
    "RUN": "TEST",
    "BRANCH": "GIT_LOCAL",
    "SWITCH": "GIT_LOCAL",
    "CHECKOUT": "GIT_LOCAL",
    "STAGE": "GIT_LOCAL",
    "COMMIT": "GIT_LOCAL",
    "FETCH": "EXTERNAL",
    "PULL": "EXTERNAL",
    "PUSH": "EXTERNAL",
    "OPEN_PR": "EXTERNAL",
    "SEND": "EXTERNAL",
    "DEPLOY": "EXTERNAL",
    "MERGE": "IRREVERSIBLE",
    "RELEASE": "IRREVERSIBLE",
    "PUBLISH": "IRREVERSIBLE",
    "DELETE": "IRREVERSIBLE",
    "RESET": "IRREVERSIBLE",
    "FORCE_PUSH": "IRREVERSIBLE",
    "STOP": "STOP",
    "WAIT": "STOP",
    "HOLD": "STOP",
}

ACTION_COMPATIBILITY = {
    "OBSERVE": frozenset(("INVESTIGATION", "VALIDATION", "REVIEW")),
    "REPORT": frozenset(("DOCUMENTATION", "REVIEW")),
    "LOCAL_CHANGE": frozenset(
        ("IMPLEMENTATION", "CLEANUP", "DOCUMENTATION")
    ),
    "TEST": frozenset(("TEST", "VALIDATION")),
    "GIT_LOCAL": frozenset(("GIT", "CLEANUP")),
    "STOP": WORK_KINDS,
}

ADVANCING_ACTION_CLASSES = frozenset(
    ("LOCAL_CHANGE", "TEST", "GIT_LOCAL", "EXTERNAL", "IRREVERSIBLE")
)
ALL_ACTION_CLASSES = frozenset(
    (
        "OBSERVE",
        "REPORT",
        "LOCAL_CHANGE",
        "TEST",
        "GIT_LOCAL",
        "EXTERNAL",
        "IRREVERSIBLE",
        "STOP",
    )
)

WITNESS_KINDS = frozenset(
    (
        "FILE",
        "GIT",
        "COMMAND",
        "TEST",
        "RESULT",
        "RECEIPT",
        "REVIEW",
        "CLEANUP",
        "DECISION",
    )
)

_HEADING_RE = re.compile(
    r"^[ ]{0,3}(?P<marks>#{1,6})(?:[ \t]+(?P<title>.*?))?[ \t]*$"
)
_FENCE_RE = re.compile(
    r"^[ ]{0,3}(?P<fence>`{3,}|~{3,})(?P<tail>.*)$"
)
_ATOM_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_WORK_ID_RE = re.compile(r"^[A-Z][A-Z0-9_-]{0,31}$")
_WORK_ITEM_RE = re.compile(
    r"^(?:[-*+][ \t]+)?"
    r"\[(?P<id>[A-Za-z][A-Za-z0-9_-]{0,31})\][ \t]+"
    r"(?P<kind>[A-Za-z]+);[ \t]*"
    r"owner=(?P<owner>RECEIVER|DECISION_OWNER);[ \t]*"
    r"subject=(?P<subject>[A-Za-z0-9][A-Za-z0-9._-]{0,63})"
    r"(?:;[ \t]*scope=(?P<scope>[A-Za-z0-9][A-Za-z0-9._-]{0,63}))?$",
    re.IGNORECASE,
)
_PREDICATE_RE = re.compile(
    r"^(?:[-*+][ \t]+)?"
    r"\[(?P<id>[A-Za-z][A-Za-z0-9_-]{0,31})\][ \t]+"
    r"(?P<kind>[A-Za-z]+);[ \t]*"
    r"subject=(?P<subject>[A-Za-z0-9][A-Za-z0-9._-]{0,63});[ \t]*"
    r"expected=(?P<expected>[A-Za-z0-9][A-Za-z0-9._-]{0,63})$",
    re.IGNORECASE,
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
    resolved_root: Path
    root_identity: tuple[int, int, int]
    head: str
    branch: str | None
    origin: str | None
    origin_slug: str | None


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
    scope: str | None


@dataclass(frozen=True)
class _WorkItem:
    identifier: str
    kind: str
    owner: str
    subject: str
    scope: str | None


@dataclass(frozen=True)
class _Action:
    action_class: str
    token: str
    work_ids: tuple[str, ...]
    closure_ids: tuple[str, ...]
    branch: str | None

    @property
    def signature(
        self,
    ) -> tuple[str, str, tuple[str, ...], tuple[str, ...], str | None]:
        return (
            self.action_class,
            self.token,
            self.work_ids,
            self.closure_ids,
            self.branch,
        )


@dataclass(frozen=True)
class _Completion:
    status: str
    predicates: tuple[tuple[str, str, str, str], ...]


@dataclass(frozen=True)
class _Boundary:
    prohibit: frozenset[str]
    stop_before: frozenset[str]
    require_authority: frozenset[str]
    cap_to: tuple[str, ...]
    scope: str | None
    require_new_gate: bool

    @property
    def blocked_classes(self) -> frozenset[str]:
        return self.prohibit | self.stop_before | self.require_authority


@dataclass(frozen=True)
class _ParsedField:
    state: str
    value: object | None = None


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


class _SemanticFailure(Exception):
    def __init__(self, code: str, *, final: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.final = final


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
        if (
            assessment.mode not in (MODE_ACTIVE_TRANSFER, MODE_CLOSED_STATE)
            or assessment.issue_codes
        ):
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
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    environment.update(
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
    return environment


def _run_git(
    target: Path, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            ("git", "-C", os.fspath(target), *arguments),
            capture_output=True,
            check=False,
            env=_git_environment(),
            encoding="utf-8",
            errors="surrogateescape",
            input="",
        )
    except (OSError, ValueError) as exc:
        raise HandoffProcessError(
            REPOSITORY_CONTEXT_UNAVAILABLE
        ) from exc
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


def _capture_snapshot(repo_root: Path | str | os.PathLike[str]) -> _RepositorySnapshot:
    """Capture the local Git facts that define one assessment snapshot."""

    try:
        supplied = Path(os.path.abspath(os.fspath(repo_root)))
        if not supplied.is_dir():
            raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)
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
        # Retain the caller's lexical spelling after proving that it names the
        # exact worktree root.  On macOS, Git may report /private/var while the
        # caller and handoff path use the equivalent /var spelling.
        root = supplied
        resolved_root = Path(os.path.realpath(observed_root))
        root_metadata = resolved_root.stat()
        if not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError
    except (TypeError, ValueError, OSError) as exc:
        raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE) from exc

    head = _run_git(root, "rev-parse", "--verify", "HEAD").stdout.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40,64}", head):
        raise HandoffProcessError(REPOSITORY_CONTEXT_UNAVAILABLE)

    branch_result = _run_git(
        root,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
        check=False,
    )
    branch = (
        branch_result.stdout.strip()
        if branch_result.returncode == 0
        else None
    )
    if branch is not None and (
        not branch
        or "\n" in branch
        or "\r" in branch
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
    return _RepositorySnapshot(
        root,
        resolved_root,
        (
            root_metadata.st_dev,
            root_metadata.st_ino,
            root_metadata.st_mode,
        ),
        head.lower(),
        branch,
        origin,
        _origin_slug(origin),
    )


def _capture_repository_snapshot(
    repo_root: Path | str | os.PathLike[str],
) -> _RepositorySnapshot:
    """Patchable repository-snapshot seam used at both assessment boundaries."""

    return _capture_snapshot(repo_root)


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
) -> tuple[str, ...]:
    try:
        supplied = os.fspath(handoff_path)
        if not supplied or "\x00" in supplied:
            raise _ArtifactInputError("INPUT_MISSING")
        if ".." in Path(supplied).parts:
            raise _ArtifactInputError("INPUT_OUTSIDE_ROOT")
        absolute = Path(os.path.abspath(
            supplied if os.path.isabs(supplied) else root / supplied
        ))
        relative: Path | None = None
        for trusted_root in _trusted_root_spellings(root):
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
        directory_fd = os.open(
            Path(os.path.realpath(root)),
            _directory_flags(),
        )
    except OSError as exc:
        if initial:
            raise _ArtifactInputError("INPUT_UNREADABLE") from exc
        raise _Unstable from exc

    try:
        for component in parts[:-1]:
            try:
                metadata = os.stat(
                    component,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
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
                        "INPUT_SYMLINK",
                        _file_identity(metadata),
                    )
                raise _Unstable
            if not stat.S_ISDIR(metadata.st_mode):
                if initial:
                    raise _ArtifactInputError(
                        "INPUT_MISSING",
                        _file_identity(metadata),
                    )
                raise _Unstable
            try:
                next_fd = os.open(
                    component,
                    _directory_flags(),
                    dir_fd=directory_fd,
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
            before = os.stat(
                name,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
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
                    "INPUT_SYMLINK",
                    _file_identity(before),
                )
            raise _Unstable
        if not stat.S_ISREG(before.st_mode):
            if initial:
                raise _ArtifactInputError(
                    "INPUT_NOT_REGULAR",
                    _file_identity(before),
                )
            raise _Unstable
        if before.st_size > MAX_INPUT_BYTES:
            if initial:
                raise _ArtifactInputError(
                    "INPUT_TOO_LARGE",
                    _file_identity(before),
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
                    "INPUT_SYMLINK",
                    _file_identity(before),
                ) from exc
            if initial:
                raise _ArtifactInputError(
                    "INPUT_UNREADABLE",
                    _file_identity(before),
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
                        "INPUT_TOO_LARGE",
                        _file_identity(before),
                    )
                raise _Unstable
            after = os.fstat(descriptor)
            after_path = os.stat(
                name,
                dir_fd=directory_fd,
                follow_symlinks=False,
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
                    "INPUT_UNREADABLE",
                    _file_identity(before),
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
            ord(character) < 32 or ord(character) == 127
            for character in raw
        )
    ):
        raise HandoffProcessError(USAGE_ERROR)
    normalized = raw.strip()
    upper = normalized.upper()
    if (
        not normalized
        or upper in (
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
        if normalized.startswith(entry + ":") and normalized[len(entry) + 1 :].strip():
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
    return re.fullmatch(
        rf"[ ]{{0,3}}{re.escape(character)}{{{length},}}[ \t]*",
        line,
    ) is not None


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
            if tail and (
                tail[0] in "=:;"
                or tail.startswith("::")
                or tail[0].isspace()
            ):
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
    for index, line in enumerate(lines):
        if fence_character is not None:
            if _closing_fence(line, fence_character, fence_length):
                fence_character = None
                fence_length = 0
                fence_start = -1
            continue
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
        if _registry_heading(heading.title, HISTORICAL_HEADINGS) is not None:
            return index, tuple(headings)
        headings.append(heading)

    if (
        fence_character is not None
        and _contains_field_header(lines, fence_start + 1, len(lines))
    ):
        raise _MalformedRepresentation
    return len(lines), tuple(headings)


def _group_ranges(
    headings: Sequence[_Heading], cutoff: int
) -> tuple[tuple[int, int], ...]:
    if not headings:
        return ((0, cutoff),)
    minimum = min(heading.level for heading in headings)
    roots = [heading for heading in headings if heading.level == minimum]
    ranges: list[tuple[int, int]] = []
    if roots[0].line > 0:
        ranges.append((0, roots[0].line))
    for index, heading in enumerate(roots):
        end = roots[index + 1].line if index + 1 < len(roots) else cutoff
        ranges.append((heading.line, end))
    return tuple(ranges)


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
        occurrences.append(
            _Occurrence(field, label, "\n".join(value_lines))
        )
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
            if (
                heading.line > selected.line
                and heading.level <= selected.level
            ):
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

    bearing: list[tuple[_Occurrence, ...]] = []
    for start, end in _group_ranges(headings, cutoff):
        occurrences = _extract_occurrences(lines, start, end)
        if occurrences:
            bearing.append(occurrences)
    if not bearing:
        raise _ArtifactInputError("UNSUPPORTED_VARIANT")
    if len(bearing) > 1:
        raise _ArtifactInputError("CURRENT_RECORD_AMBIGUOUS")
    return bearing[0]


@dataclass(frozen=True)
class _CanonicalRecord:
    values: Mapping[str, str]
    repository_values: tuple[tuple[str, str], ...]
    conflict_fields: frozenset[str]
    v13_gate_alias: bool


def _normalized_lines(value: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line.strip()) for line in value.split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _repository_facet(label: str, value: str) -> str:
    if label in ("repo root", "repository root"):
        return "root"
    if label == "repository identity":
        return "identity"
    stripped = value.strip()
    return "root" if os.path.isabs(stripped) or stripped in (".", "./") else "identity"


def _comparison_value(field: str, value: str) -> object:
    if field == "next_owner":
        return value.strip().upper()
    normalized = _normalized_lines(value)
    if field in ("current_state", "current_gate"):
        try:
            registry = (
                STATE_TOKENS
                if field == "current_state"
                else GATE_TOKENS
            )
            return _control(value, registry)
        except _SemanticFailure:
            pass
    if field in ("active_branch", "repository_reference"):
        return (
            normalized[len("refs/heads/") :]
            if field == "active_branch"
            and normalized.startswith("refs/heads/")
            else normalized
        )
    if field in ("next_authorized_action", "first_one_action"):
        try:
            return _action(value).signature
        except _SemanticFailure:
            pass
        match = re.search(
            r"(?i)(;[ \t]*branch=)([^;\n]+)",
            normalized,
        )
        if match is not None:
            return (
                normalized[: match.start()].upper()
                + match.group(1).upper()
                + match.group(2).strip()
                + normalized[match.end() :].upper()
            )
    if field in ("missing_closure", "receiving_ownership"):
        try:
            return _work_items(value)
        except _SemanticFailure:
            pass
    if field == "ai_retained_work":
        try:
            return _retained_ids(value)
        except _SemanticFailure:
            pass
    if field == "completion_line":
        try:
            return _completion(value)
        except _SemanticFailure:
            pass
    if field == "do_not_continue_boundary":
        try:
            return _boundary(value)
        except _SemanticFailure:
            pass
    return normalized.upper()


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
            facets: dict[str, tuple[str, str]] = {}
            for occurrence in group:
                facet = _repository_facet(occurrence.label, occurrence.value)
                if facet == "root":
                    supplied = occurrence.value.strip()
                    try:
                        comparison = os.path.realpath(
                            supplied
                            if os.path.isabs(supplied)
                            else root / supplied
                        )
                    except (TypeError, ValueError, OSError):
                        comparison = supplied
                else:
                    comparison = occurrence.value.strip()
                    if comparison.endswith(".git"):
                        comparison = comparison[:-4]
                prior = facets.get(facet)
                if prior is not None and prior[0] != comparison:
                    conflicts.add(field)
                    continue
                facets[facet] = (comparison, occurrence.value)
            repository_values.extend(
                (facet, pair[1])
                for facet, pair in sorted(facets.items())
            )
            continue
        comparisons = {
            _comparison_value(field, occurrence.value)
            for occurrence in group
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


def _scalar(value: str) -> str:
    if "\n" in value:
        raise _SemanticFailure("FIELD_UNKNOWN")
    return re.sub(r"[ \t]+", " ", value.strip())


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
        or re.search(
            r"(?<![A-Z0-9_./-])(?:UNKNOWN|TBD|TODO|UNDECIDED)"
            r"(?![A-Z0-9_./-])",
            upper,
        )
        or re.search(
            r"(?:^|[ \t])(?:IF|UNLESS|PENDING)(?:[ \t]|$)",
            upper,
        )
        or upper.startswith("NONE ")
        or upper.startswith("NONE?")
    ):
        return "FIELD_UNKNOWN"
    if (
        "|" in normalized
        or re.search(
            r"(?:^|[ \t])(?:OR|AND/OR)(?:[ \t]|$)",
            upper,
        )
        or re.search(r"[ \t]/[ \t]", normalized)
    ):
        return "FIELD_AMBIGUOUS"
    return None


def _exact_unresolved_code(value: str) -> str | None:
    normalized = _normalized_lines(value)
    upper = normalized.upper()
    if (
        not normalized
        or upper in ("NONE", "UNKNOWN", "TBD", "?")
        or re.fullmatch(r"<[^<>\n]+>", normalized) is not None
        or "?" in normalized
    ):
        return "FIELD_UNKNOWN"
    return None


def _explicit_none(value: str) -> bool:
    return value.strip().casefold() == "none"


def _scalar_unresolved_code(value: str) -> str | None:
    unresolved = _unresolved_code(value)
    if unresolved is not None:
        return unresolved
    upper = _normalized_lines(value).upper()
    if "?" in value or re.search(
        r"(?<![A-Z0-9_./-])(?:IF|UNLESS|PENDING)"
        r"(?![A-Z0-9_./-])",
        upper,
    ):
        return "FIELD_UNKNOWN"
    if re.search(
        r"(?<![A-Z0-9_./-])(?:OR|AND/OR)"
        r"(?![A-Z0-9_./-])",
        upper,
    ):
        return "FIELD_AMBIGUOUS"
    return None


def _valid_atom(value: str) -> bool:
    return (
        _ATOM_RE.fullmatch(value) is not None
        and ".." not in value
        and "/" not in value
    )


def _control(
    value: str,
    registry: Mapping[str, str],
) -> _Control:
    unresolved = _unresolved_code(value)
    if unresolved is not None:
        raise _SemanticFailure(unresolved)
    scalar = _scalar(value)
    upper = scalar.upper()
    for surface in sorted(registry, key=len, reverse=True):
        if upper == surface:
            return _Control(registry[surface], None)
        if not upper.startswith(surface):
            continue
        tail = scalar[len(surface) :]
        match = re.fullmatch(
            r"(?:[ \t]*:[ \t]*|[ \t]+-[ \t]+|[ \t]*—[ \t]*)"
            r"(?P<qualifier>\S(?:.*\S)?)",
            tail,
        )
        if match is None:
            continue
        words = match.group("qualifier").split(" ")
        if not 1 <= len(words) <= 8 or any(
            not _valid_atom(word) for word in words
        ):
            raise _SemanticFailure("FIELD_UNKNOWN")
        qualifier = " ".join(words).upper()
        banned_words = {
            "ACTION",
            "OWNER",
            "RECEIVER",
            "DECISION",
            "DECISION_OWNER",
            "AUTHORITY",
            "BOUNDARY",
            "UNKNOWN",
            "TBD",
            "NONE",
            "NO",
            "NOT",
            "IF",
            "UNLESS",
            "WHEN",
            "PENDING",
            "DEPENDING",
            "CONDITIONAL",
            "MAYBE",
            "EITHER",
            "OR",
            "AND",
            "PROHIBIT",
            "STOP",
            "BEFORE",
            "REQUIRE",
            "CAP_TO",
            "SCOPE",
            "REQUIRE_NEW_GATE",
            "STOP_BEFORE",
            "REQUIRE_SEPARATE_AUTHORITY_BEFORE",
            *ALL_ACTION_CLASSES,
            *ACTION_TOKENS.keys(),
        }
        qualifier_words = tuple(word.upper() for word in words)
        normalized_qualifier_words = tuple(
            word.replace("-", "_")
            for word in qualifier_words
        )
        registered_controls = {
            token.replace(" ", "_")
            for token in (*STATE_TOKENS, *GATE_TOKENS)
        }

        def contains_phrase(phrase: str) -> bool:
            phrase_words = tuple(phrase.split(" "))
            return any(
                qualifier_words[index : index + len(phrase_words)]
                == phrase_words
                for index in range(
                    len(qualifier_words) - len(phrase_words) + 1
                )
            )

        if (
            any(
                word in banned_words or word in registered_controls
                for word in normalized_qualifier_words
            )
            or any(contains_phrase(token) for token in STATE_TOKENS)
            or any(contains_phrase(token) for token in GATE_TOKENS)
        ):
            raise _SemanticFailure("FIELD_UNKNOWN")
        return _Control(
            registry[surface],
            "_".join(word.upper() for word in words),
        )
    raise _SemanticFailure("FIELD_UNKNOWN")


def _identifier_list(value: str) -> tuple[str, ...]:
    parts = tuple(part.strip().upper() for part in value.split(","))
    if (
        not parts
        or any(_WORK_ID_RE.fullmatch(part) is None for part in parts)
    ):
        raise _SemanticFailure("FIELD_UNKNOWN")
    if len(parts) != len(set(parts)):
        raise _SemanticFailure("FIELD_UNKNOWN", final=True)
    return parts


def _parse_work_items(value: str) -> tuple[_WorkItem, ...]:
    lines = [line.strip() for line in value.split("\n")]
    if not lines or any(not line for line in lines):
        raise _SemanticFailure("FIELD_UNKNOWN")
    if len(lines) > 1 and any(
        re.match(r"^[-*+][ \t]+", line) is None for line in lines
    ):
        raise _SemanticFailure("FIELD_UNKNOWN")
    items: list[_WorkItem] = []
    for line in lines:
        match = _WORK_ITEM_RE.fullmatch(line)
        if match is None:
            raise _SemanticFailure("FIELD_UNKNOWN")
        identifier = match.group("id").upper()
        kind = match.group("kind").upper()
        owner = match.group("owner").upper()
        subject = match.group("subject")
        scope = match.group("scope")
        if (
            kind not in WORK_KINDS
            or not _valid_atom(subject)
            or (scope is not None and not _valid_atom(scope))
        ):
            raise _SemanticFailure("FIELD_UNKNOWN")
        items.append(
            _WorkItem(
                identifier,
                kind,
                owner,
                subject.upper(),
                scope.upper() if scope is not None else None,
            )
        )
    return tuple(items)


def _work_items(value: str) -> tuple[_WorkItem, ...]:
    try:
        items = _parse_work_items(value)
        if len(items) != len({item.identifier for item in items}):
            raise _SemanticFailure("FIELD_UNKNOWN", final=True)
        return items
    except _SemanticFailure as exc:
        if exc.final:
            raise
        unresolved = _unresolved_code(value)
        if unresolved is not None:
            raise _SemanticFailure(unresolved)
        raise


def _normalize_branch(value: str) -> str:
    scalar = value.strip()
    if scalar.startswith("refs/heads/"):
        scalar = scalar[len("refs/heads/") :]
    return scalar


def _action(value: str) -> _Action:
    scalar = _scalar(value)
    exact_unresolved = _exact_unresolved_code(scalar)
    if exact_unresolved is not None:
        raise _SemanticFailure(exact_unresolved)
    match = re.fullmatch(
        r"(?P<token>[A-Za-z][A-Za-z_-]*)[ \t]+"
        r"\[(?P<ids>[^\[\]]+)\](?P<facets>(?:[ \t]*;[ \t]*[^;]+)*)",
        scalar,
    )
    if match is None:
        unresolved = _unresolved_code(value)
        raise _SemanticFailure(unresolved or "FIELD_UNKNOWN")
    token = match.group("token").upper().replace("-", "_")
    action_class = ACTION_TOKENS.get(token)
    if action_class is None:
        raise _SemanticFailure("FIELD_UNKNOWN")
    work_ids = _identifier_list(match.group("ids"))
    closure_ids: tuple[str, ...] = ()
    branch: str | None = None
    seen: set[str] = set()
    facet_order: list[str] = []
    facets = match.group("facets").strip()
    if facets:
        for raw_facet in facets.split(";")[1:]:
            key, separator, raw_value = raw_facet.strip().partition("=")
            normalized_key = key.strip().casefold()
            if (
                separator != "="
                or normalized_key not in ("closure", "branch")
                or normalized_key in seen
                or not raw_value.strip()
            ):
                raise _SemanticFailure("FIELD_UNKNOWN")
            seen.add(normalized_key)
            facet_order.append(normalized_key)
            if normalized_key == "closure":
                closure_ids = _identifier_list(raw_value)
            else:
                branch = _normalize_branch(raw_value)
                branch_unresolved = _exact_unresolved_code(branch)
                if (
                    not branch
                    or "\n" in branch
                    or branch_unresolved is not None
                ):
                    raise _SemanticFailure(
                        branch_unresolved or "FIELD_UNKNOWN"
                    )
    if facet_order not in (
        [],
        ["closure"],
        ["branch"],
        ["closure", "branch"],
    ):
        raise _SemanticFailure("FIELD_UNKNOWN")
    return _Action(action_class, token, work_ids, closure_ids, branch)


def _completion(value: str) -> _Completion:
    unresolved = _unresolved_code(value)
    if unresolved is not None:
        raise _SemanticFailure(unresolved)
    lines = [line.strip() for line in value.split("\n")]
    if len(lines) < 2 or lines[0].upper() not in ("OPEN:", "MET:"):
        raise _SemanticFailure("FIELD_UNKNOWN")
    if any(not line for line in lines[1:]):
        raise _SemanticFailure("FIELD_UNKNOWN")
    predicates: list[tuple[str, str, str, str]] = []
    identifiers: set[str] = set()
    for line in lines[1:]:
        if re.match(r"^[-*+][ \t]+", line) is None:
            raise _SemanticFailure("FIELD_UNKNOWN")
        match = _PREDICATE_RE.fullmatch(line)
        if match is None:
            raise _SemanticFailure("FIELD_UNKNOWN")
        identifier = match.group("id").upper()
        kind = match.group("kind").upper()
        subject = match.group("subject")
        expected = match.group("expected")
        if (
            identifier in identifiers
            or kind not in WITNESS_KINDS
            or not _valid_atom(subject)
            or not _valid_atom(expected)
        ):
            raise _SemanticFailure("FIELD_UNKNOWN")
        identifiers.add(identifier)
        predicates.append(
            (identifier, kind, subject.upper(), expected.upper())
        )
    return _Completion(lines[0][:-1].upper(), tuple(predicates))


def _retained_ids(value: str) -> tuple[str, ...]:
    try:
        scalar = _scalar(value)
        match = re.fullmatch(
            r"RETAIN[ \t]*:[ \t]*(.+)",
            scalar,
            re.IGNORECASE,
        )
        if match is None:
            raise _SemanticFailure("FIELD_UNKNOWN")
        return _identifier_list(match.group(1))
    except _SemanticFailure as exc:
        if exc.final:
            raise
        unresolved = _unresolved_code(value)
        if unresolved is not None:
            raise _SemanticFailure(unresolved)
        raise


def _action_classes(value: str) -> frozenset[str]:
    values = tuple(
        part.strip().upper()
        for part in value.split(",")
    )
    if (
        not values
        or any(item not in ALL_ACTION_CLASSES for item in values)
        or len(values) != len(set(values))
    ):
        raise _SemanticFailure("FIELD_UNKNOWN")
    return frozenset(values)


def _parse_boundary(value: str) -> _Boundary:
    lines = [line.strip() for line in value.split("\n")]
    if not lines or any(not line for line in lines):
        raise _SemanticFailure("FIELD_UNKNOWN")
    prohibit: set[str] = set()
    stop_before: set[str] = set()
    require_authority: set[str] = set()
    cap_to: tuple[str, ...] = ()
    scope: str | None = None
    require_new_gate = False
    seen_singletons: set[str] = set()
    for line in lines:
        upper = line.upper()
        if upper == "REQUIRE_NEW_GATE":
            if "REQUIRE_NEW_GATE" in seen_singletons:
                raise _SemanticFailure("FIELD_UNKNOWN")
            seen_singletons.add("REQUIRE_NEW_GATE")
            require_new_gate = True
            continue
        key, separator, raw_value = line.partition(":")
        normalized_key = key.strip().upper()
        if separator != ":" or not raw_value.strip():
            raise _SemanticFailure("FIELD_UNKNOWN")
        if normalized_key == "PROHIBIT":
            prohibit.update(_action_classes(raw_value))
        elif normalized_key == "STOP_BEFORE":
            stop_before.update(_action_classes(raw_value))
        elif normalized_key == "REQUIRE_SEPARATE_AUTHORITY_BEFORE":
            require_authority.update(_action_classes(raw_value))
        elif normalized_key == "CAP_TO":
            if "CAP_TO" in seen_singletons:
                raise _SemanticFailure("FIELD_UNKNOWN")
            seen_singletons.add("CAP_TO")
            cap_to = _identifier_list(raw_value)
        elif normalized_key == "SCOPE":
            if "SCOPE" in seen_singletons:
                raise _SemanticFailure("FIELD_UNKNOWN")
            seen_singletons.add("SCOPE")
            candidate = raw_value.strip()
            if not _valid_atom(candidate):
                raise _SemanticFailure("FIELD_UNKNOWN")
            scope = candidate.upper()
        else:
            raise _SemanticFailure("FIELD_UNKNOWN")
    return _Boundary(
        frozenset(prohibit),
        frozenset(stop_before),
        frozenset(require_authority),
        cap_to,
        scope,
        require_new_gate,
    )


def _boundary(value: str) -> _Boundary:
    try:
        return _parse_boundary(value)
    except _SemanticFailure as exc:
        if exc.final:
            raise
        unresolved = _unresolved_code(value)
        if unresolved is not None:
            raise _SemanticFailure(unresolved)
        raise


def _known(parsed: Mapping[str, _ParsedField], field: str) -> object | None:
    item = parsed.get(field)
    return item.value if item is not None and item.state == "KNOWN" else None


def _is_none(parsed: Mapping[str, _ParsedField], field: str) -> bool:
    item = parsed.get(field)
    return item is not None and item.state == "EXPLICIT_NONE"


def _parse_present_fields(
    record: _CanonicalRecord,
    snapshot: _RepositorySnapshot,
    issues: set[str],
) -> dict[str, _ParsedField]:
    parsed: dict[str, _ParsedField] = {}

    def parse(
        field: str,
        parser: object,
    ) -> None:
        if field in record.conflict_fields or field not in record.values:
            return
        raw = record.values[field]
        try:
            if _explicit_none(raw):
                parsed[field] = _ParsedField("EXPLICIT_NONE")
                return
            value = parser(raw)  # type: ignore[operator]
            parsed[field] = _ParsedField("KNOWN", value)
        except _SemanticFailure as exc:
            issues.add(exc.code)

    def parse_target(raw: str) -> str:
        unresolved = _scalar_unresolved_code(raw)
        if unresolved is not None:
            raise _SemanticFailure(unresolved)
        if "/" in raw:
            raise _SemanticFailure("FIELD_AMBIGUOUS")
        return _scalar(raw)

    def parse_owner(raw: str) -> str:
        unresolved = _scalar_unresolved_code(raw)
        if unresolved is not None:
            raise _SemanticFailure(unresolved)
        if "/" in raw:
            raise _SemanticFailure("FIELD_AMBIGUOUS")
        if "\n" in raw or not raw.strip():
            raise _SemanticFailure("FIELD_UNKNOWN")
        return raw.strip()

    def parse_branch(raw: str) -> str:
        branch = _normalize_branch(_scalar(raw))
        exact_unresolved = _exact_unresolved_code(branch)
        if exact_unresolved is not None:
            raise _SemanticFailure(exact_unresolved)
        completed = _run_git(
            snapshot.root,
            "check-ref-format",
            "--branch",
            branch,
            check=False,
        )
        if completed.returncode != 0:
            unresolved = _scalar_unresolved_code(branch)
            raise _SemanticFailure(unresolved or "FIELD_UNKNOWN")
        return branch

    def parse_action(raw: str) -> _Action:
        value = _action(raw)
        if value.branch is not None:
            completed = _run_git(
                snapshot.root,
                "check-ref-format",
                "--branch",
                value.branch,
                check=False,
            )
            if completed.returncode != 0:
                unresolved = _scalar_unresolved_code(value.branch)
                raise _SemanticFailure(unresolved or "FIELD_UNKNOWN")
        return value

    parse("target_layer", parse_target)
    parse("current_state", lambda raw: _control(raw, STATE_TOKENS))
    parse("current_gate", lambda raw: _control(raw, GATE_TOKENS))
    parse("active_branch", parse_branch)
    parse("next_authorized_action", parse_action)
    parse("completion_line", _completion)
    parse("missing_closure", _work_items)
    parse("next_owner", parse_owner)
    parse("receiving_ownership", _work_items)
    parse("first_one_action", parse_action)
    parse("do_not_continue_boundary", _boundary)
    parse("ai_retained_work", _retained_ids)
    return parsed


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
        if _explicit_none(raw):
            field_issues.add("FIELD_UNKNOWN")
            continue
        if "\n" in raw or not raw.strip():
            field_issues.add("FIELD_UNKNOWN")
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
            if candidate != Path(os.path.realpath(snapshot.root)):
                unresolved = (
                    _exact_unresolved_code(raw)
                    or _unresolved_code(raw)
                )
                if unresolved is not None:
                    field_issues.add(unresolved)
                    continue
            validated.append((facet, candidate))
            continue

        slug = raw.strip()
        if slug.endswith(".git"):
            slug = slug[:-4]
        parts = slug.split("/")
        if (
            len(parts) != 2
            or any(not _valid_atom(part) for part in parts)
        ):
            unresolved = _unresolved_code(raw)
            field_issues.add(unresolved or "FIELD_UNKNOWN")
        else:
            validated.append((facet, slug))

    if field_issues:
        issues.update(field_issues)
        return

    for facet, value in validated:
        if facet == "root":
            if value != Path(os.path.realpath(snapshot.root)):
                issues.add("REPOSITORY_MISMATCH")
        elif snapshot.origin_slug is None:
            issues.add("REPOSITORY_REFERENCE_UNRESOLVED")
        elif value != snapshot.origin_slug:
            issues.add("REPOSITORY_MISMATCH")


def _id_counts(items: Sequence[_WorkItem]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item.identifier] = counts.get(item.identifier, 0) + 1
    return counts


def _work_relations(
    *,
    missing: Sequence[_WorkItem],
    ownership: Sequence[_WorkItem],
    retained: Sequence[str],
    issues: set[str],
) -> tuple[dict[str, _WorkItem], dict[str, _WorkItem]]:
    missing_counts = _id_counts(missing)
    ownership_counts = _id_counts(ownership)
    if any(count != 1 for count in missing_counts.values()) or any(
        count != 1 for count in ownership_counts.values()
    ):
        issues.add("FIELD_UNKNOWN")

    all_by_id: dict[str, list[_WorkItem]] = {}
    for item in (*missing, *ownership):
        all_by_id.setdefault(item.identifier, []).append(item)
        if item.kind in ROUTINE_WORK_KINDS and item.owner == "DECISION_OWNER":
            issues.add("ROUTINE_WORK_RETURNED")
        if item.kind in DECISION_WORK_KINDS and item.owner == "RECEIVER":
            issues.add("OWNER_MISMATCH")
    for items in all_by_id.values():
        if len(set(items)) > 1:
            issues.add("FIELD_CONFLICT")

    missing_map = {
        item.identifier: item
        for item in missing
        if missing_counts.get(item.identifier) == 1
    }
    ownership_map = {
        item.identifier: item
        for item in ownership
        if ownership_counts.get(item.identifier) == 1
    }

    retained_set = set(retained)
    retained_references_valid = len(retained) == len(retained_set)
    if not retained_references_valid:
        issues.add("FIELD_UNKNOWN")
    for identifier in retained:
        item = ownership_map.get(identifier)
        if item is None or item.kind not in ROUTINE_WORK_KINDS:
            issues.add("FIELD_UNKNOWN")
            retained_references_valid = False

    for item in ownership:
        if item.owner != "RECEIVER" or item.kind not in ROUTINE_WORK_KINDS:
            issues.add("OWNER_MISMATCH")
        if (
            retained_references_valid
            and item.kind in ROUTINE_WORK_KINDS
            and item.identifier not in retained_set
        ):
            issues.add("ROUTINE_WORK_RETURNED")

    for item in missing:
        if item.kind not in ROUTINE_WORK_KINDS:
            continue
        owned = ownership_map.get(item.identifier)
        if (
            owned is None
            or owned != item
            or (
                retained_references_valid
                and item.identifier not in retained_set
            )
        ):
            issues.add("MISSING_CLOSURE_UNASSIGNED")
        if (
            retained_references_valid
            and item.identifier not in retained_set
        ):
            issues.add("ROUTINE_WORK_RETURNED")
    return missing_map, ownership_map


def _evaluate_action_references(
    action: _Action,
    *,
    ownership: Mapping[str, _WorkItem],
    ownership_counts: Mapping[str, int],
    missing_counts: Mapping[str, int],
    ownership_ready: bool,
    missing_ready: bool,
    issues: set[str],
) -> tuple[bool | None, bool | None]:
    primary_valid: bool | None = True if ownership_ready else None
    closure_valid: bool | None = True if missing_ready else None
    if ownership_ready:
        for identifier in action.work_ids:
            if ownership_counts.get(identifier) != 1:
                issues.add("FIELD_UNKNOWN")
                primary_valid = False
    if missing_ready:
        for identifier in action.closure_ids:
            if missing_counts.get(identifier) != 1:
                issues.add("FIELD_UNKNOWN")
                closure_valid = False
    if primary_valid:
        compatible = ACTION_COMPATIBILITY.get(action.action_class)
        if compatible is None or any(
            ownership[identifier].kind not in compatible
            for identifier in action.work_ids
        ):
            issues.add("ACTION_RELATION_UNPROVEN")
    return primary_valid, closure_valid


def _evaluate_record(
    record: _CanonicalRecord,
    snapshot: _RepositorySnapshot,
    expected_receiver: str,
    expected_target_layer: str,
) -> HandoffAssessment:
    issues: set[str] = set()
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

    _evaluate_repository_reference(record, snapshot, issues)
    parsed = _parse_present_fields(record, snapshot, issues)

    target = _known(parsed, "target_layer")
    if target is not None:
        assert isinstance(target, str)
        if " ".join(target.split()).casefold() != " ".join(
            expected_target_layer.split()
        ).casefold():
            issues.add("TARGET_LAYER_MISMATCH")
    elif _is_none(parsed, "target_layer"):
        issues.add("FIELD_UNKNOWN")
    if record.v13_gate_alias and "target_layer" in parsed:
        if (
            expected_target_layer.casefold() != "v13"
            or not isinstance(target, str)
            or target.casefold() != "v13"
        ):
            issues.add("TARGET_LAYER_MISMATCH")

    state = _known(parsed, "current_state")
    gate = _known(parsed, "current_gate")
    if _is_none(parsed, "current_state") or _is_none(parsed, "current_gate"):
        issues.add("FIELD_UNKNOWN")
    mode: str | None = None
    if isinstance(state, _Control):
        mode = (
            MODE_CLOSED_STATE
            if state.token == "CLOSED"
            else MODE_ACTIVE_TRANSFER
        )
    if isinstance(state, _Control) and isinstance(gate, _Control):
        allowed_pair = (
            (state.token == "ACTIVE")
            or (
                state.token == "RESTRICTED"
                and gate.token in ("HOLD", "CAP", "BLOCK")
            )
            or (
                state.token == "CLOSED"
                and gate.token in ("HOLD", "CAP", "BLOCK")
            )
        )
        if not allowed_pair:
            issues.add("STATE_GATE_CONFLICT")

    branch = _known(parsed, "active_branch")
    next_owner = _known(parsed, "next_owner")
    completion = _known(parsed, "completion_line")
    next_action = _known(parsed, "next_authorized_action")
    first_action = _known(parsed, "first_one_action")
    boundary = _known(parsed, "do_not_continue_boundary")

    if _is_none(parsed, "completion_line") or _is_none(
        parsed, "do_not_continue_boundary"
    ):
        issues.add("FIELD_UNKNOWN")

    missing_value = _known(parsed, "missing_closure")
    ownership_value = _known(parsed, "receiving_ownership")
    retained_value = _known(parsed, "ai_retained_work")
    missing = (
        missing_value
        if isinstance(missing_value, tuple)
        else ()
    )
    ownership = (
        ownership_value
        if isinstance(ownership_value, tuple)
        else ()
    )
    retained = (
        retained_value
        if isinstance(retained_value, tuple)
        else ()
    )
    missing_counts = _id_counts(missing)
    ownership_counts = _id_counts(ownership)
    work_relations_ready = all(
        field in parsed
        for field in (
            "missing_closure",
            "receiving_ownership",
            "ai_retained_work",
        )
    )
    if work_relations_ready:
        missing_map, ownership_map = _work_relations(
            missing=missing,
            ownership=ownership,
            retained=retained,
            issues=issues,
        )
    else:
        missing_map = {
            item.identifier: item
            for item in missing
            if missing_counts.get(item.identifier) == 1
        }
        ownership_map = {
            item.identifier: item
            for item in ownership
            if ownership_counts.get(item.identifier) == 1
        }

    if isinstance(state, _Control) and isinstance(gate, _Control):
        scopes = tuple(
            control.scope
            for control in (state, gate)
            if control.scope is not None
        )
        required_scope = scopes[0] if scopes else None
        if len(set(scopes)) > 1:
            issues.add("FIELD_UNKNOWN")
        if isinstance(boundary, _Boundary):
            if required_scope is None and boundary.scope is not None:
                issues.add("FIELD_UNKNOWN")
            if required_scope is not None and boundary.scope != required_scope:
                issues.add("FIELD_UNKNOWN")
            if (
                required_scope is not None
                and "receiving_ownership" in parsed
                and any(
                item.scope != required_scope for item in ownership
                )
            ):
                issues.add("FIELD_UNKNOWN")

    if mode == MODE_ACTIVE_TRANSFER:
        if "active_branch" in parsed:
            if isinstance(branch, str):
                if snapshot.branch is None or branch != snapshot.branch:
                    issues.add("ACTIVE_BRANCH_MISMATCH")
            elif _is_none(parsed, "active_branch"):
                issues.add("ACTIVE_BRANCH_MISMATCH")

        if "next_owner" in parsed:
            if not isinstance(next_owner, str) or (
                next_owner.casefold() != expected_receiver.casefold()
            ):
                issues.add("OWNER_MISMATCH")
        if "receiving_ownership" in parsed:
            if _is_none(parsed, "receiving_ownership") or not ownership:
                issues.add("OWNER_MISMATCH")
        if (
            "ai_retained_work" in parsed
            and _is_none(parsed, "ai_retained_work")
        ):
            issues.add("ROUTINE_WORK_RETURNED")

        if (
            "first_one_action" in parsed
            and _is_none(parsed, "first_one_action")
        ):
            issues.add("FIRST_ACTION_NONE_ACTIVE")
        if (
            "next_authorized_action" in parsed
            and _is_none(parsed, "next_authorized_action")
        ):
            issues.add("ACTION_RELATION_UNPROVEN")
        if (
            isinstance(next_action, _Action)
            and isinstance(first_action, _Action)
        ):
            next_primary_valid, next_closure_valid = (
                _evaluate_action_references(
                    next_action,
                    ownership=ownership_map,
                    ownership_counts=ownership_counts,
                    missing_counts=missing_counts,
                    ownership_ready="receiving_ownership" in parsed,
                    missing_ready="missing_closure" in parsed,
                    issues=issues,
                )
            )
            first_primary_valid, first_closure_valid = (
                _evaluate_action_references(
                    first_action,
                    ownership=ownership_map,
                    ownership_counts=ownership_counts,
                    missing_counts=missing_counts,
                    ownership_ready="receiving_ownership" in parsed,
                    missing_ready="missing_closure" in parsed,
                    issues=issues,
                )
            )
            if next_action.signature != first_action.signature:
                issues.add("ACTION_RELATION_UNPROVEN")
            if (
                "active_branch" in parsed
                and isinstance(branch, str)
            ):
                for action in (next_action, first_action):
                    if action.branch is not None and action.branch != branch:
                        issues.add("ACTION_BRANCH_MISMATCH")
            if first_action.action_class in ("EXTERNAL", "IRREVERSIBLE"):
                issues.add("FIRST_ACTION_UNSAFE")
            if isinstance(gate, _Control):
                advancing_allowed = frozenset(
                    (
                        "OBSERVE",
                        "REPORT",
                        "LOCAL_CHANGE",
                        "TEST",
                        "GIT_LOCAL",
                    )
                )
                held_allowed = frozenset(("OBSERVE", "REPORT", "STOP"))
                allowed_actions = (
                    advancing_allowed
                    if gate.token in ("GO", "GO_UNDER_CAP")
                    else held_allowed
                )
                if first_action.action_class not in allowed_actions:
                    issues.add("GATE_ACTION_CONFLICT")
            if (
                (
                    next_primary_valid
                    and next_closure_valid
                    and first_primary_valid
                    and first_closure_valid
                )
                and any(
                    missing_map[identifier].kind in DECISION_WORK_KINDS
                    and first_action.action_class
                    not in ("OBSERVE", "REPORT", "STOP")
                    for identifier in first_action.closure_ids
                    if identifier in missing_map
                )
            ):
                issues.add("ACTION_RELATION_UNPROVEN")
        elif (
            "next_authorized_action" in parsed
            and "first_one_action" in parsed
            and not _is_none(parsed, "next_authorized_action")
            and not _is_none(parsed, "first_one_action")
        ):
            issues.add("ACTION_RELATION_UNPROVEN")

        if (
            "missing_closure" in parsed
            and "first_one_action" in parsed
            and missing
        ):
            if not isinstance(first_action, _Action):
                issues.add("MISSING_CLOSURE_NO_ACTION")
            else:
                closure_references_valid = all(
                    missing_counts.get(identifier) == 1
                    for identifier in first_action.closure_ids
                )
                if (
                    closure_references_valid
                    and not set(first_action.closure_ids).intersection(
                        item.identifier for item in missing
                    )
                ):
                    issues.add("MISSING_CLOSURE_NO_ACTION")
        if isinstance(completion, _Completion) and completion.status != "OPEN":
            issues.add("COMPLETION_CLOSURE_CONFLICT")

    elif mode == MODE_CLOSED_STATE:
        closed_none_fields = (
            "active_branch",
            "next_authorized_action",
            "missing_closure",
            "receiving_ownership",
            "first_one_action",
            "ai_retained_work",
        )
        if any(
            field in parsed and not _is_none(parsed, field)
            for field in closed_none_fields
        ):
            issues.add("CLOSED_STATE_INCOMPLETE")
        if "next_owner" in parsed:
            if not (
                _is_none(parsed, "next_owner")
                or (
                    isinstance(next_owner, str)
                    and next_owner.casefold() == expected_receiver.casefold()
                )
            ):
                issues.add("CLOSED_STATE_INCOMPLETE")
                if isinstance(next_owner, str):
                    issues.add("OWNER_MISMATCH")
        if (
            "completion_line" in parsed
            and (
                not isinstance(completion, _Completion)
                or completion.status != "MET"
            )
        ):
            issues.add("CLOSED_STATE_INCOMPLETE")
        if (
            "completion_line" in parsed
            and "missing_closure" in parsed
            and "receiving_ownership" in parsed
            and (missing or ownership)
        ):
            issues.add("COMPLETION_CLOSURE_CONFLICT")
    else:
        for common_field in (
            "active_branch",
            "next_authorized_action",
            "missing_closure",
            "next_owner",
            "receiving_ownership",
            "first_one_action",
            "ai_retained_work",
        ):
            if _is_none(parsed, common_field):
                # Legality depends on the unavailable mode; do not infer it.
                continue

    if isinstance(boundary, _Boundary):
        qualified = any(
            isinstance(control, _Control) and control.scope is not None
            for control in (state, gate)
        )
        controls_ready = (
            "current_state" in parsed and "current_gate" in parsed
        )
        if (
            controls_ready
            and boundary.scope is not None
            and not qualified
        ):
            issues.add("FIELD_UNKNOWN")
        if isinstance(gate, _Control):
            if boundary.cap_to and gate.token != "GO_UNDER_CAP":
                issues.add("FIELD_UNKNOWN")
            if gate.token == "GO_UNDER_CAP" and not boundary.cap_to:
                issues.add("FIELD_UNKNOWN")
        if (
            "current_state" in parsed
            and boundary.require_new_gate
            and mode != MODE_CLOSED_STATE
        ):
            issues.add("FIELD_UNKNOWN")
        operative = bool(
            boundary.prohibit
            or boundary.stop_before
            or boundary.require_authority
            or (
                isinstance(gate, _Control)
                and gate.token == "GO_UNDER_CAP"
                and boundary.cap_to
            )
            or boundary.require_new_gate
        )
        if not operative and (
            not boundary.cap_to or "current_gate" in parsed
        ):
            issues.add("FIELD_UNKNOWN")

        cap_references_valid = "receiving_ownership" in parsed
        if "receiving_ownership" in parsed:
            for identifier in boundary.cap_to:
                if ownership_counts.get(identifier) != 1:
                    issues.add("FIELD_UNKNOWN")
                    cap_references_valid = False
        if (
            "first_one_action" in parsed
            and isinstance(first_action, _Action)
        ):
            if first_action.action_class in boundary.blocked_classes:
                issues.add("BOUNDARY_CONFLICT")
            if (
                isinstance(gate, _Control)
                and gate.token == "GO_UNDER_CAP"
                and cap_references_valid
                and not set(first_action.work_ids).issubset(boundary.cap_to)
            ):
                issues.add("BOUNDARY_CONFLICT")
        if (
            "current_state" in parsed
            and mode == MODE_CLOSED_STATE
            and not (
                boundary.require_new_gate
                or ADVANCING_ACTION_CLASSES.issubset(boundary.prohibit)
            )
        ):
            issues.add("CLOSED_STATE_INCOMPLETE")

    if issues:
        return _assessment(RESULT_NOT_ACCEPTABLE, issues=issues)
    if mode is None:
        return _assessment(
            RESULT_NOT_ACCEPTABLE,
            issues=("FIELD_UNKNOWN",),
        )
    return _assessment(RESULT_ACCEPTABLE, mode=mode)


def _same_repository_snapshot(
    opening: _RepositorySnapshot,
    closing: _RepositorySnapshot,
) -> bool:
    return (
        opening.root == closing.root
        and opening.resolved_root == closing.resolved_root
        and opening.root_identity == closing.root_identity
        and opening.head == closing.head
        and opening.branch == closing.branch
        and opening.origin == closing.origin
        and opening.origin_slug == closing.origin_slug
    )


def assess_handoff(
    *,
    repo_root: Path | str | os.PathLike[str],
    handoff_path: Path | str | os.PathLike[str],
    expected_receiver: str,
    expected_target_layer: str,
) -> HandoffAssessment:
    """Assess one explicit handoff against one stable local Git snapshot."""

    try:
        receiver = _trusted_scalar(expected_receiver)
        target_layer = _trusted_scalar(expected_target_layer)
        opening_repository = _capture_repository_snapshot(repo_root)
        opening_input: _InputSnapshot | None = None
        opening_input_error: _ArtifactInputError | None = None
        assessment: HandoffAssessment

        try:
            parts = _input_parts(opening_repository.root, handoff_path)
            opening_input = _read_parts(
                opening_repository.root,
                parts,
                initial=True,
            )
            text = _decode_input(opening_input.content)
        except _ArtifactInputError as exc:
            opening_input_error = exc
            assessment = _assessment(RESULT_INVALID, issues=(exc.code,))
        else:
            try:
                occurrences = _select_record(text)
                record = _project_record(
                    occurrences,
                    opening_repository.root,
                )
            except _MalformedRepresentation:
                assessment = _assessment(
                    RESULT_INVALID,
                    issues=("MALFORMED_REPRESENTATION",),
                )
            except _ArtifactInputError as exc:
                assessment = _assessment(
                    RESULT_NOT_ACCEPTABLE,
                    issues=(exc.code,),
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
                opening_repository.root
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

    # Raise outside the handling clauses so the public error retains neither
    # a raw cause nor a raw exception context.
    raise HandoffProcessError(process_error)
