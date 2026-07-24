"""Deterministic human rendering for an already-computed scan payload."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
import unicodedata


RECOMMENDATION_NONE = "NO ADOPTION RECOMMENDATION"
RECOMMENDATION_LITE = "LITE RESTART NOTE RECOMMENDED"
RECOMMENDATION_HANDOFF = "HANDOFF SURFACE RECOMMENDED"
RECOMMENDATION_FULLER = "FULLER V13 FIT CHECK MAY BE USEFUL"
RECOMMENDATION_INSUFFICIENT = "INSUFFICIENT EVIDENCE"

RECOMMENDATIONS = frozenset(
    (
        RECOMMENDATION_NONE,
        RECOMMENDATION_LITE,
        RECOMMENDATION_HANDOFF,
        RECOMMENDATION_FULLER,
        RECOMMENDATION_INSUFFICIENT,
    )
)

MODES = frozenset(
    (
        "UNMANAGED_REPOSITORY",
        "V13_MANAGED_REPOSITORY",
        "UNDETERMINED",
    )
)

UNKNOWN_MESSAGES = {
    "task_completion": (
        "The scan cannot establish whether the current task is complete."
    ),
    "instruction_quality": (
        "Instruction-surface presence does not establish instruction quality."
    ),
    "software_correctness": (
        "Local markers do not establish software correctness."
    ),
    "remote_freshness": (
        "Remote freshness was not checked by this local-only scan."
    ),
    "bounded_surface": (
        "At least one bounded surface could not be inspected safely."
    ),
    "scan_result": "The bounded local scan did not complete.",
}

MINIMUM_NEXT_STEPS = {
    RECOMMENDATION_NONE: (
        "No adoption step is recommended from this bounded evidence."
    ),
    RECOMMENDATION_LITE: (
        "Create or update one restart note with the current work and next "
        "action before the next agent session."
    ),
    RECOMMENDATION_HANDOFF: (
        "Create one stable handoff surface with current identity, evidence, "
        "boundaries, and the next action."
    ),
    RECOMMENDATION_FULLER: (
        "Review whether the observed instruction surfaces need one shared "
        "restart contract."
    ),
    RECOMMENDATION_INSUFFICIENT: (
        "Resolve the unavailable bounded evidence, then rerun the scan."
    ),
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return value
    return ()


def _safe_inline(value: Any, fallback: str = "unknown") -> str:
    if not isinstance(value, str):
        return fallback
    cleaned = "".join(
        (
            character
            if unicodedata.category(character) not in {"Cc", "Cf", "Cs"}
            else " "
        )
        for character in value
    )
    cleaned = " ".join(cleaned.split())
    return cleaned or fallback


def _safe_repository_name(value: Any) -> str:
    name = _safe_inline(value, "unknown")
    return name.replace("/", "_").replace("\\", "_")


def _integer(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _count(detail: Mapping[str, Any], key: str) -> int:
    return len(_sequence(detail.get(key)))


def _evidence_description(
    item: Mapping[str, Any],
    repository: Mapping[str, Any],
    mode: str,
) -> str:
    check = _safe_inline(item.get("check"), "unknown check")
    status = _safe_inline(item.get("status"), "UNKNOWN")
    detail = _mapping(item.get("detail"))

    if check == "git.repository":
        return (
            "Local Git repository identity was observed."
            if status == "OBSERVED"
            else "Local Git repository identity was not available."
        )
    if check == "git.head":
        head = _safe_inline(repository.get("head"), "unknown")
        return f"HEAD identity is {head[:12]}."
    if check == "git.branch":
        if repository.get("detached") is True:
            return "HEAD is detached."
        branch = _safe_inline(repository.get("branch"), "unknown")
        return f"Current branch is {branch}."
    if check == "git.worktree":
        state = _safe_inline(repository.get("worktree"), "UNKNOWN")
        count = _integer(repository.get("change_count"))
        suffix = "" if count is None else f" ({count} change entries)"
        return f"Worktree state is {state}{suffix}."
    if check == "git.default_branch":
        if status != "OBSERVED":
            return "The local default-branch relationship was not available."
        default_ref = _safe_inline(repository.get("default_ref"), "unknown")
        ahead = _integer(repository.get("ahead"))
        behind = _integer(repository.get("behind"))
        relation = (
            "unknown"
            if ahead is None or behind is None
            else f"ahead {ahead}, behind {behind}"
        )
        return f"Local default reference is {default_ref} ({relation})."
    if check == "git.origin":
        if status == "OBSERVED":
            return "A sanitized local origin identity was observed."
        if status == "ABSENT":
            return "No local origin was observed."
        return "The local origin identity could not be represented safely."
    if check == "instructions.surfaces":
        if status == "OBSERVED":
            count = _count(detail, "observed")
            return f"{count} allowlisted AI instruction surfaces were observed."
        if status == "ABSENT":
            return "No allowlisted AI instruction surface was observed."
        return "At least one allowlisted instruction surface was unavailable."
    if check == "restart.surfaces":
        if status == "OBSERVED":
            observed = _count(detail, "observed")
            bounded = _count(detail, "bounded_restart_evidence")
            return (
                f"{observed} bounded restart candidates were observed; "
                f"{bounded} contained structural restart evidence."
            )
        if status == "ABSENT":
            return "No bounded restart surface was observed."
        return "At least one bounded restart surface was unavailable."
    if check == "restart.markers":
        if status == "OBSERVED":
            return "One or more bounded restart marker classes were observed."
        if status == "ABSENT":
            return "No accepted restart marker class was observed."
        return "Restart-marker inspection had no readable candidate."
    if check == "v13.routing":
        if mode == "V13_MANAGED_REPOSITORY":
            return "Canonical V13 paths were observed; strict check is the route."
        if mode == "UNDETERMINED":
            return "V13 path state could not be classified completely."
        return "Strict V13 state validation is not applicable to this scan."
    if check == "scan.snapshot":
        if status == "OBSERVED":
            return "Opening and closing local evidence matched."
        return "The local repository changed during inspection."
    if check in ("cli.usage", "scan.cli.usage"):
        return "The scan invocation did not match the documented grammar."
    if check in ("runner.internal", "scan.internal"):
        return "The bounded scan encountered an internal failure."

    label = check.replace(".", " ")
    return f"{label}: {status}."


def _append_unique(target: list[str], value: str) -> None:
    if value not in target:
        target.append(value)


def _grouped_evidence(
    payload: Mapping[str, Any],
    repository: Mapping[str, Any],
    mode: str,
) -> dict[str, list[str]]:
    groups = {
        "Observed": [],
        "Absent": [],
        "Not applicable": [],
        "Unknown": [],
    }
    for raw_item in _sequence(payload.get("evidence")):
        item = _mapping(raw_item)
        status = item.get("status")
        description = _evidence_description(item, repository, mode)
        if status == "OBSERVED":
            group = "Observed"
        elif status == "ABSENT":
            group = "Absent"
        elif status == "NOT_APPLICABLE":
            group = "Not applicable"
        else:
            group = "Unknown"
        _append_unique(groups[group], description)

    for raw_unknown in _sequence(payload.get("unknowns")):
        unknown = _mapping(raw_unknown)
        code = unknown.get("code")
        if isinstance(code, str):
            description = UNKNOWN_MESSAGES.get(
                code,
                f"{_safe_inline(code).replace('_', ' ')} remains unknown.",
            )
            _append_unique(groups["Unknown"], description)
    return groups


def _summary_label(completion: str, recommendation: str) -> str:
    if completion == "FAILED":
        return "FAILED"
    if recommendation == RECOMMENDATION_INSUFFICIENT:
        return "INSUFFICIENT EVIDENCE"
    if recommendation == RECOMMENDATION_NONE:
        return "OBSERVATIONS AVAILABLE"
    return "REVIEW"


def render_text(payload: Mapping[str, Any]) -> str:
    """Render one scan payload without inspecting a repository or environment."""

    completion = _safe_inline(payload.get("scan_completion"), "FAILED")
    mode_value = payload.get("mode")
    mode = mode_value if mode_value in MODES else "UNDETERMINED"

    recommendation_object = _mapping(payload.get("recommendation"))
    recommendation_value = recommendation_object.get("code")
    recommendation = (
        recommendation_value
        if recommendation_value in RECOMMENDATIONS
        else RECOMMENDATION_INSUFFICIENT
    )

    repository = _mapping(payload.get("repository"))
    root_name = _safe_repository_name(repository.get("root_name"))
    head = _safe_inline(repository.get("head"), "unknown")[:12]
    if repository.get("detached") is True:
        branch = "DETACHED"
    else:
        branch = _safe_inline(repository.get("branch"), "unknown")

    if root_name == "unknown" and head == "unknown":
        repository_line = "Repository: unavailable"
    else:
        repository_line = f"Repository: {root_name} @ {head} ({branch})"

    lines = [
        f"Decision-OS Scan v0.2: {_summary_label(completion, recommendation)}",
        f"Mode: {mode}",
        repository_line,
        "",
    ]

    groups = _grouped_evidence(payload, repository, mode)
    for title in ("Observed", "Absent", "Not applicable", "Unknown"):
        lines.append(f"{title}:")
        entries = groups[title]
        if entries:
            lines.extend(f"- {entry}" for entry in entries)
        else:
            lines.append("- none")
        lines.append("")

    route = _mapping(payload.get("route"))
    minimum_next_step = (
        "Run decision-os check <repository>."
        if route.get("code") == "RUN_V13_CHECK"
        else MINIMUM_NEXT_STEPS[recommendation]
    )
    lines.extend(
        (
            "Recommendation:",
            recommendation,
            "",
            "Minimum next step:",
            minimum_next_step,
            "",
            "Limits:",
            (
                "This scan does not establish task completion, instruction "
                "quality, software correctness, repository safety, remote "
                "freshness, authority, or a V13 Gate."
            ),
        )
    )
    return "\n".join(lines) + "\n"


__all__ = ("render_text",)
