"""Read-only Git and V13 state checks."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable, Sequence

from .state import StateSurface, first_value, load_surface, normalize_field, values_for


EXIT_OK = 0
EXIT_NOT_GIT = 3
EXIT_INCOMPLETE = 4
EXIT_CONTRADICTION = 5

HANDOFF_PATH = "handoff/current_codex_handoff.md"
CURRENT_SIGNAL_PATH = "docs/current_signal.md"

V12_ALIASES = ("V12 State", "V12 Completion State")
V13_GATE_ALIASES = ("V13 Next Loop Gate", "Current Gate")
NEXT_ACTION_ALIASES = ("Next Authorized Action", "Codex Next Authorized Action")
ACTIVE_BRANCH_ALIASES = ("Active Branch",)
AUTHORITY_MATCH_ALIASES = ("Authority Match",)
HUMAN_SEAT_ALIASES = ("Human Seat Required",)
ACTIVATION_ALIASES = ("Activation", "Run Activation")
RUN_ALIASES = ("Run",)
IMPLEMENTATION_ALIASES = ("Implementation",)
LOOP_ALIASES = ("Loop",)
RUN_AUTHORITY_ALIASES = ("Run authority", "Run 003 authority")
AUTHORITY_WINDOW_ALIASES = ("BOAW-001", "Authority Window")
REMAINING_LOOPS_ALIASES = ("Remaining authorized loops",)
AUTHORITY_ENVELOPE_ALIASES = (
    "Authority Envelope",
    "Approved Authority Envelope",
    "Run Authority Envelope",
)
ROLLBACK_ALIASES = (
    "Rollback Identity",
    "Rollback Boundary",
    "Post-Exhaustion Closure rollback identity",
)
RECEIPT_ALIASES = ("Receipt", "Receipt Identity")
CLOSURE_TAIL_ALIASES = (
    "Closure-Only Tail",
    "Closure Tail",
    "Closure-Tail Authority",
)
AUTHORITY_MATCH_TEXT_WITNESSES = (
    ("required_authority", ("Required Authority",)),
    ("authority_held", ("Authority Held",)),
)
AUTHORITY_MATCH_BOOLEAN_WITNESSES = (
    (
        "operational_effect",
        ("Operational Effect Available By Loop End",),
    ),
    ("validation", ("Validation Closable",)),
    ("rollback", ("Rollback Closable",)),
    ("receipt", ("Receipt Closable",)),
    ("closure_tail", ("Closure-Tail Preserved", "Closure Tail Preserved")),
)


@dataclass(frozen=True)
class GitCommandError(Exception):
    args_used: tuple[str, ...]
    returncode: int
    stderr: str


class GitReader:
    """Run Git commands with optional locks disabled."""

    def __init__(self, target: Path) -> None:
        self.target = target
        self.environment = os.environ.copy()
        self.environment.update(
            {
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
                "LC_ALL": "C",
                "LANG": "C",
                "TZ": "UTC",
            }
        )

    def run(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        command = ("git", "-C", str(self.target), *arguments)
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            env=self.environment,
            stdin=subprocess.DEVNULL,
            text=True,
        )
        if check and completed.returncode != 0:
            raise GitCommandError(
                tuple(arguments),
                completed.returncode,
                completed.stderr.strip(),
            )
        return completed


def evidence(
    check: str, status: str, source: str, detail: Any
) -> dict[str, Any]:
    return {
        "check": check,
        "detail": detail,
        "source": source,
        "status": status,
    }


def unknown_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "authority_match": "UNKNOWN",
        "evidence": [item],
        "human_seat_required": None,
        "missing_closure": [],
        "next_authorized_action": "UNKNOWN",
        "v12_state": "UNKNOWN",
        "v13_gate": "UNKNOWN",
    }


def _parse_token(
    value: str | None, allowed: Sequence[str]
) -> tuple[str, bool]:
    if value is None:
        return "UNKNOWN", False
    match = re.match(r"^\s*([A-Z]+)\b", value)
    if match is None or match.group(1) not in allowed:
        return "UNKNOWN", False
    selected = match.group(1)
    alternatives = re.split(r"\s*(?:/|\bOR\b)\s*", value.upper())
    for alternative in alternatives[1:]:
        alternative_match = re.match(r"([A-Z]+)\b", alternative)
        if (
            alternative_match is not None
            and alternative_match.group(1) in allowed
            and alternative_match.group(1) != selected
        ):
            return "UNKNOWN", False
    return selected, True


def _token(value: str | None, allowed: Sequence[str]) -> str:
    return _parse_token(value, allowed)[0]


def _has_positive_integer(value: str | None) -> bool:
    if value is None:
        return False
    match = re.search(r"\b(\d+)\b", value)
    return bool(match and int(match.group(1)) > 0)


def _means_started(value: str | None) -> bool:
    if value is None:
        return False
    words = tuple(re.findall(r"[A-Z0-9]+", value.upper()))
    joined = " ".join(words)
    if (
        "NOT STARTED" in joined
        or "NOT ACTIVE" in joined
        or "INACTIVE" in words
        or words == ("NONE",)
        or "COMPLETE" in words
        or "CLOSED" in words
    ):
        return False
    return (
        "STARTED" in words
        or "ACTIVE" in words
        or "ACTIVATED" in words
        or "MAY START" in joined
        or ("ACTIVATION" in words and "RECEIVED" in words)
    )


def _means_not_started(value: str | None) -> bool:
    if value is None:
        return False
    words = tuple(re.findall(r"[A-Z0-9]+", value.upper()))
    joined = " ".join(words)
    return (
        "NOT STARTED" in joined
        or "NOT ACTIVE" in joined
        or "INACTIVE" in words
        or words == ("NONE",)
    )


def _means_closed(value: str | None) -> bool:
    if value is None:
        return False
    words = set(re.findall(r"[A-Z0-9]+", value.upper()))
    return bool(words.intersection({"COMPLETE", "CLOSED", "EXHAUSTED"}))


def _same_alias_conflicts(
    surfaces: Sequence[StateSurface], aliases: Iterable[str]
) -> tuple[str, ...]:
    values = values_for(surfaces, aliases)
    distinct = {value for _, value in values}
    if len(distinct) <= 1:
        return ()
    sources = ", ".join(f"{source}={value}" for source, value in values)
    return (sources,)


def _authority_is_held(value: str | None) -> bool:
    if not _is_resolved_evidence(value):
        return False
    assert value is not None
    words = tuple(re.findall(r"[A-Z0-9]+", value.upper()))
    joined = " ".join(words)
    return not (
        words == ("NO",)
        or "DENIED" in words
        or "REVOKED" in words
        or "NONE" in words
        or "MISSING" in words
        or "NO AUTHORITY" in joined
        or "NOT AUTHORIZED" in joined
        or "NOT GRANTED" in joined
        or "INSUFFICIENT" in words
        or "UNKNOWN" in words
        or "PENDING" in words
        or "TBD" in words
    )


def _is_resolved_evidence(value: str | None) -> bool:
    if value is None or not value.strip():
        return False
    stripped = value.strip()
    if re.search(r"<[^>]+>", stripped):
        return False
    words = tuple(re.findall(r"[A-Z0-9]+", stripped.upper()))
    joined = " ".join(words)
    return not (
        bool(
            set(words).intersection(
                {
                    "ABSENT",
                    "INSUFFICIENT",
                    "MISSING",
                    "NONE",
                    "PENDING",
                    "TBD",
                    "UNAVAILABLE",
                    "UNKNOWN",
                }
            )
        )
        or stripped.upper() in {"N/A", "NA"}
        or "NOT AUTHORIZED" in joined
        or "NOT AVAILABLE" in joined
        or "NOT YET" in joined
        or "ENVELOPE REQUIRED" in joined
    )


def _current_state(
    surfaces: Sequence[StateSurface],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str], list[str]]:
    state_evidence: list[dict[str, Any]] = []
    missing_required: list[str] = []
    contradictions: list[str] = []

    for surface in surfaces:
        if not surface.exists:
            state_evidence.append(
                evidence(
                    f"surface.{Path(surface.relative_path).stem}",
                    "MISSING",
                    surface.relative_path,
                    "required file is absent",
                )
            )
            continue
        if not surface.block_found:
            state_evidence.append(
                evidence(
                    f"surface.{Path(surface.relative_path).stem}",
                    "MISSING",
                    surface.relative_path,
                    "first current fenced block is absent",
                )
            )
            continue
        state_evidence.append(
            evidence(
                f"surface.{Path(surface.relative_path).stem}",
                "PASS",
                surface.relative_path,
                "first current fenced block parsed",
            )
        )
        for field in surface.conflicting_fields:
            contradictions.append(
                f"{surface.relative_path}: conflicting current values for {field}"
            )

    field_specs = (
        ("v12_state", V12_ALIASES),
        ("v13_gate", V13_GATE_ALIASES),
        ("active_branch", ACTIVE_BRANCH_ALIASES),
        ("next_authorized_action", NEXT_ACTION_ALIASES),
    )
    for output_name, aliases in field_specs:
        conflicts = _same_alias_conflicts(surfaces, aliases)
        contradictions.extend(f"{output_name}: {item}" for item in conflicts)
        value = first_value(surfaces, aliases)
        if value is None or not value.strip():
            missing_required.append(output_name)

    v12_value = first_value(surfaces, V12_ALIASES)
    v12_state, v12_valid = _parse_token(
        v12_value,
        ("PASS", "DELAY", "BLOCK", "UNKNOWN"),
    )
    if v12_value and not v12_valid:
        missing_required.append("v12_state:invalid")

    v13_gate_value = first_value(surfaces, V13_GATE_ALIASES)
    v13_gate, v13_gate_valid = _parse_token(
        v13_gate_value,
        ("GO", "HOLD", "CAP", "BLOCK"),
    )
    if v13_gate_value and not v13_gate_valid:
        contradictions.append(
            f"unsupported V13 Gate value: {v13_gate_value}"
        )

    next_action = first_value(surfaces, NEXT_ACTION_ALIASES) or "UNKNOWN"
    active_branch_value = first_value(surfaces, ACTIVE_BRANCH_ALIASES)

    for output_name, aliases in (
        ("authority_match", AUTHORITY_MATCH_ALIASES),
        ("human_seat_required", HUMAN_SEAT_ALIASES),
    ):
        conflicts = _same_alias_conflicts(surfaces, aliases)
        contradictions.extend(f"{output_name}: {item}" for item in conflicts)

    authority_match_value = first_value(surfaces, AUTHORITY_MATCH_ALIASES)
    explicit_authority_match, authority_match_valid = _parse_token(
        authority_match_value, ("YES", "NO", "UNKNOWN")
    )
    human_seat_value = first_value(surfaces, HUMAN_SEAT_ALIASES)
    explicit_human_seat, human_seat_valid = _parse_token(
        human_seat_value, ("YES", "NO")
    )
    human_seat_required: bool | None
    if explicit_human_seat == "YES":
        human_seat_required = True
    elif explicit_human_seat == "NO":
        human_seat_required = False
    else:
        human_seat_required = None

    if authority_match_value and not authority_match_valid:
        missing_required.append("authority_match:invalid")
    if human_seat_value and not human_seat_valid:
        missing_required.append("human_seat_required:invalid")

    envelope_value = first_value(surfaces, AUTHORITY_ENVELOPE_ALIASES)
    rollback_value = first_value(surfaces, ROLLBACK_ALIASES)
    receipt_value = first_value(surfaces, RECEIPT_ALIASES)
    closure_value = first_value(surfaces, CLOSURE_TAIL_ALIASES)
    activation_value = first_value(surfaces, ACTIVATION_ALIASES)
    run_value = first_value(surfaces, RUN_ALIASES)
    implementation_value = first_value(surfaces, IMPLEMENTATION_ALIASES)
    run_authority_value = first_value(surfaces, RUN_AUTHORITY_ALIASES)

    joint_specs = (
        ("authority_envelope", AUTHORITY_ENVELOPE_ALIASES),
        ("rollback_identity", ROLLBACK_ALIASES),
        ("receipt", RECEIPT_ALIASES),
        ("closure_tail", CLOSURE_TAIL_ALIASES),
        *AUTHORITY_MATCH_TEXT_WITNESSES,
        *AUTHORITY_MATCH_BOOLEAN_WITNESSES,
        ("activation", ACTIVATION_ALIASES),
        ("run", RUN_ALIASES),
        ("implementation", IMPLEMENTATION_ALIASES),
        ("loop", LOOP_ALIASES),
        ("run_authority", RUN_AUTHORITY_ALIASES),
        ("authority_window", AUTHORITY_WINDOW_ALIASES),
        ("remaining_authorized_loops", REMAINING_LOOPS_ALIASES),
    )
    for output_name, aliases in joint_specs:
        conflicts = _same_alias_conflicts(surfaces, aliases)
        contradictions.extend(f"{output_name}: {item}" for item in conflicts)

    run_active = any(
        _means_started(value)
        for value in (activation_value, run_value, implementation_value, envelope_value)
    )
    run_closed = _means_closed(run_value)
    loop_context = run_active or any(
        value is not None
        for value in (
            first_value(surfaces, LOOP_ALIASES),
            authority_match_value,
            human_seat_value,
            implementation_value,
        )
    )
    closure_context = loop_context or run_closed

    if loop_context:
        for output_name, value in (
            ("authority_match", authority_match_value),
            ("human_seat_required", human_seat_value),
        ):
            if value is None or not value.strip():
                missing_required.append(output_name)

    missing_closure: list[str] = []
    if closure_context and not _is_resolved_evidence(envelope_value):
        missing_required.append("authority_envelope")
    if closure_context:
        for name, value in (
            ("rollback_identity", rollback_value),
            ("receipt", receipt_value),
            ("closure_only_tail", closure_value),
        ):
            if not _is_resolved_evidence(value):
                missing_closure.append(name)

    if run_active and _means_not_started(activation_value):
        contradictions.append("run is active while activation is NOT STARTED")
    if run_active and run_authority_value and run_authority_value.upper() == "NONE":
        contradictions.append("run is active while run authority is NONE")
    if _means_not_started(run_value) and _means_started(implementation_value):
        contradictions.append("implementation may start while Run is NOT STARTED")
    if explicit_authority_match == "YES" and human_seat_required is True:
        contradictions.append(
            "Authority Match is YES while Human Seat Required is YES"
        )
    if (
        run_active
        and authority_match_value
        and explicit_authority_match == "UNKNOWN"
        and authority_match_valid
    ):
        contradictions.append(
            f"run is active while Authority Match is {explicit_authority_match}"
        )

    missing_match_witnesses: list[str] = []
    negative_match_witnesses: list[str] = []
    if explicit_authority_match == "YES":
        for name, aliases in AUTHORITY_MATCH_TEXT_WITNESSES:
            value = first_value(surfaces, aliases)
            if not _is_resolved_evidence(value):
                missing_match_witnesses.append(name)
            elif not _authority_is_held(value):
                negative_match_witnesses.append(name)
        for name, aliases in AUTHORITY_MATCH_BOOLEAN_WITNESSES:
            value = first_value(surfaces, aliases)
            token, valid = _parse_token(value, ("YES", "NO"))
            if value is None or not value.strip():
                missing_match_witnesses.append(name)
            elif not valid or token != "YES":
                negative_match_witnesses.append(name)
        if missing_match_witnesses or negative_match_witnesses:
            contradictions.append(
                "Authority Match is YES without affirmative witness(es): "
                + ", ".join(
                    sorted(missing_match_witnesses + negative_match_witnesses)
                )
            )

    if (
        explicit_authority_match == "NO"
        and _means_started(implementation_value)
    ):
        contradictions.append(
            "implementation may start while Authority Match is NO"
        )

    exhausted_value = first_value(surfaces, AUTHORITY_WINDOW_ALIASES)
    remaining_value = first_value(surfaces, REMAINING_LOOPS_ALIASES)
    if (
        exhausted_value
        and "EXHAUSTED" in exhausted_value.upper()
        and _has_positive_integer(remaining_value)
    ):
        contradictions.append("authority is EXHAUSTED with positive remaining loops")

    authority_match = explicit_authority_match

    if contradictions:
        human_seat_required = True
    elif human_seat_required is None and not loop_context:
        human_seat_required = False

    state_evidence.append(
        evidence(
            "state.required_fields",
            "PASS" if not missing_required else "MISSING",
            f"{HANDOFF_PATH} + {CURRENT_SIGNAL_PATH}",
            {"missing": sorted(missing_required)},
        )
    )
    state_evidence.append(
        evidence(
            "state.authority_match_witnesses",
            (
                "NOT_APPLICABLE"
                if explicit_authority_match != "YES"
                else "PASS"
                if not missing_match_witnesses and not negative_match_witnesses
                else "FAIL"
            ),
            f"{HANDOFF_PATH} + {CURRENT_SIGNAL_PATH}",
            {
                "missing": sorted(missing_match_witnesses),
                "negative_or_invalid": sorted(negative_match_witnesses),
            },
        )
    )

    conditional_items = (
        ("state.authority_envelope", envelope_value),
        ("state.rollback_identity", rollback_value),
        ("state.receipt", receipt_value),
        ("state.closure_tail", closure_value),
    )
    for check_name, value in conditional_items:
        if _is_resolved_evidence(value):
            status = "PASS"
            detail: Any = value
        elif closure_context and check_name == "state.authority_envelope":
            status = "MISSING"
            detail = "required for the declared run phase"
        elif closure_context and check_name in {
            "state.rollback_identity",
            "state.receipt",
            "state.closure_tail",
        }:
            status = "MISSING"
            detail = "required for the declared run phase"
        else:
            status = "NOT_APPLICABLE"
            detail = "no applicable run phase in the current state block"
        state_evidence.append(
            evidence(
                check_name,
                status,
                f"{HANDOFF_PATH} + {CURRENT_SIGNAL_PATH}",
                detail,
            )
        )

    state_evidence.append(
        evidence(
            "state.contradictions",
            "FAIL" if contradictions else "PASS",
            f"{HANDOFF_PATH} + {CURRENT_SIGNAL_PATH}",
            {"items": sorted(contradictions)},
        )
    )

    payload = {
        "authority_match": authority_match,
        "human_seat_required": human_seat_required,
        "missing_closure": sorted(missing_closure),
        "next_authorized_action": next_action,
        "v12_state": v12_state,
        "v13_gate": v13_gate,
    }
    return payload, state_evidence, missing_required, contradictions


def inspect_repository(target: str | Path) -> tuple[dict[str, Any], int]:
    """Inspect a repository without mutating it."""

    requested = Path(target).expanduser()
    git = GitReader(requested)
    root_result = git.run("rev-parse", "--show-toplevel", check=False)
    if root_result.returncode != 0:
        item = evidence(
            "git.repository",
            "FAIL",
            str(requested),
            "target is not an inspectable Git repository",
        )
        return unknown_payload(item), EXIT_NOT_GIT

    repo_root = Path(root_result.stdout.strip()).resolve()
    git = GitReader(repo_root)
    head_result = git.run("rev-parse", "--verify", "HEAD", check=False)
    if head_result.returncode != 0:
        item = evidence(
            "git.repository",
            "FAIL",
            "Git",
            "repository has no inspectable HEAD",
        )
        return unknown_payload(item), EXIT_NOT_GIT
    head = head_result.stdout.strip()
    origin_result = git.run("config", "--get", "remote.origin.url", check=False)
    origin = origin_result.stdout.strip() if origin_result.returncode == 0 else "UNKNOWN"

    all_evidence: list[dict[str, Any]] = [
        evidence(
            "git.repository",
            "PASS",
            "Git",
            {"head": head, "origin": origin, "root_name": repo_root.name},
        )
    ]

    branch_result = git.run("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    branch = (
        branch_result.stdout.strip()
        if branch_result.returncode == 0
        else "DETACHED"
    )
    all_evidence.append(
        evidence(
            "git.branch",
            "PASS" if branch != "DETACHED" else "UNKNOWN",
            ".git/HEAD",
            branch,
        )
    )

    try:
        status_result = git.run(
            "-c",
            "core.fsmonitor=false",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--no-renames",
        )
    except GitCommandError as exc:
        item = evidence(
            "git.worktree",
            "FAIL",
            "Git worktree",
            {
                "command": list(exc.args_used),
                "returncode": exc.returncode,
                "stderr": exc.stderr,
            },
        )
        return unknown_payload(item), EXIT_NOT_GIT
    status_lines = tuple(
        sorted(entry for entry in status_result.stdout.split("\0") if entry)
    )
    all_evidence.append(
        evidence(
            "git.worktree",
            "PASS" if not status_lines else "DIRTY",
            "Git worktree",
            {"entries": list(status_lines), "state": "CLEAN" if not status_lines else "DIRTY"},
        )
    )

    default_result = git.run(
        "symbolic-ref",
        "--quiet",
        "--short",
        "refs/remotes/origin/HEAD",
        check=False,
    )
    if default_result.returncode == 0:
        default_ref = default_result.stdout.strip()
        relation_result = git.run(
            "rev-list", "--left-right", "--count", f"HEAD...{default_ref}", check=False
        )
        if relation_result.returncode == 0:
            counts = relation_result.stdout.split()
            detail = {
                "ahead": int(counts[0]),
                "behind": int(counts[1]),
                "current_branch": branch,
                "default_ref": default_ref,
            }
            default_status = "PASS"
        else:
            detail = {
                "current_branch": branch,
                "default_ref": default_ref,
                "relationship": "UNKNOWN",
            }
            default_status = "UNKNOWN"
    else:
        detail = {
            "current_branch": branch,
            "default_ref": "UNKNOWN",
            "relationship": "UNKNOWN",
        }
        default_status = "UNKNOWN"
    all_evidence.append(
        evidence("git.default_branch", default_status, "local Git refs", detail)
    )

    try:
        surfaces = (
            load_surface(repo_root, HANDOFF_PATH),
            load_surface(repo_root, CURRENT_SIGNAL_PATH),
        )
    except (OSError, UnicodeError) as exc:
        item = evidence(
            "state.read",
            "FAIL",
            "canonical state surfaces",
            str(exc),
        )
        return unknown_payload(item), EXIT_INCOMPLETE
    payload, state_evidence, missing_required, contradictions = _current_state(surfaces)
    all_evidence.extend(state_evidence)
    payload["evidence"] = sorted(all_evidence, key=lambda item: item["check"])

    surface_missing = any(not surface.exists or not surface.block_found for surface in surfaces)
    if contradictions:
        return payload, EXIT_CONTRADICTION
    if surface_missing or missing_required or payload["missing_closure"]:
        return payload, EXIT_INCOMPLETE
    return payload, EXIT_OK
