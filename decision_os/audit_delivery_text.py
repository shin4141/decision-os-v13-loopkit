"""Deterministic text rendering for an Audit delivery result payload."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .audit_delivery import (
    FIELD_ORDER,
    NEXT_STEP_INCOMPLETE,
    NEXT_STEP_INVALID,
    REQUIRED_SECTIONS,
    SUPPORTED_PROFILE,
)


RESULT_LABELS = {
    "DELIVERY_READY": "DELIVERY READY",
    "INCOMPLETE": "INCOMPLETE",
    "INVALID": "INVALID",
}
AUDIT_CHECK_USAGE = (
    "decision-os audit-check <audit.md> | "
    "decision-os audit-check --format json|text <audit.md>"
)
INTERNAL_FAILURE_NEXT_STEP = (
    "Retry the same local delivery once; if the internal failure repeats, "
    "stop and report the command boundary."
)
SECTION_MARKERS = (
    "Title",
    *REQUIRED_SECTIONS,
    "Required heading order",
    "Fenced code block",
)


def _ordered_list(value: Any, order: Sequence[str]) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(
        value, (str, bytes, bytearray)
    ):
        return []
    selected = {
        item for item in value if isinstance(item, str) and item in order
    }
    return [item for item in order if item in selected]


def _section(title: str, values: Sequence[str]) -> list[str]:
    lines = [f"{title}:"]
    lines.extend(
        (f"- {value}" for value in values)
        if values
        else ("- none",)
    )
    return lines


def render_text(payload: Mapping[str, Any]) -> str:
    """Render one already-computed payload without reopening the input."""

    result = payload.get("result")
    label = RESULT_LABELS.get(result, "INVALID")
    profile = (
        SUPPORTED_PROFILE
        if payload.get("profile") == SUPPORTED_PROFILE
        else "UNKNOWN"
    )
    observed_sections = _ordered_list(
        payload.get("observed_sections"),
        REQUIRED_SECTIONS,
    )
    missing = [
        *_ordered_list(
            payload.get("missing_required_sections"),
            SECTION_MARKERS,
        ),
        *_ordered_list(
            payload.get("missing_required_fields"),
            FIELD_ORDER,
        ),
    ]
    invalid = [
        *_ordered_list(
            payload.get("invalid_sections"),
            SECTION_MARKERS,
        ),
        *_ordered_list(payload.get("invalid_fields"), FIELD_ORDER),
    ]

    lines = [
        f"Decision-OS Audit Delivery v0.1: {label}",
        "",
        *_section("Profile", (profile,)),
        "",
        *_section("Observed sections", observed_sections),
        "",
        *_section("Missing", missing),
        "",
        *_section("Invalid", invalid),
    ]

    if result != "DELIVERY_READY":
        next_step = payload.get("minimum_next_step")
        if next_step in (
            NEXT_STEP_INCOMPLETE,
            NEXT_STEP_INVALID,
            AUDIT_CHECK_USAGE,
            INTERNAL_FAILURE_NEXT_STEP,
        ):
            lines.extend(("", "Minimum next step:", next_step))

    lines.extend(
        (
            "",
            "This result confirms delivery structure only.",
            (
                "It does not validate diagnosis truth, repair efficacy, "
                "or client acceptance."
            ),
        )
    )
    return "\n".join(lines) + "\n"
