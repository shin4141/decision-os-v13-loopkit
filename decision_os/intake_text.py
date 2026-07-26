"""Deterministic text rendering for a workflow intake result payload."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


RESULT_LABELS = {
    "FIT_CHECK_READY": "FIT CHECK READY",
    "INCOMPLETE": "INCOMPLETE",
    "INVALID": "INVALID",
}
TEXT_FIELD_ORDER = (
    "workflow",
    "bounded_path",
    "trigger",
    "expected_state",
    "observed_state",
    "human_recovery_work",
    "restart_or_fallback_path",
    "materials_available",
    "prohibited_materials",
)
KNOWN_FIELDS = frozenset(
    (
        "schema_version",
        "incident_as_of",
        *TEXT_FIELD_ORDER,
        "next_actor",
        "next_safe_action",
        "unknowns",
        "unsupported_fields",
    )
)


def _field_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(
        value, (str, bytes, bytearray)
    ):
        return []
    selected = {
        item for item in value if isinstance(item, str) and item in KNOWN_FIELDS
    }
    return [field for field in TEXT_FIELD_ORDER if field in selected]


def _all_fields(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(
        value, (str, bytes, bytearray)
    ):
        return []
    selected = {
        item for item in value if isinstance(item, str) and item in KNOWN_FIELDS
    }
    ordered = [
        field
        for field in (
            "schema_version",
            "workflow",
            "bounded_path",
            "incident_as_of",
            "trigger",
            "expected_state",
            "observed_state",
            "human_recovery_work",
            "restart_or_fallback_path",
            "materials_available",
            "prohibited_materials",
            "next_actor",
            "next_safe_action",
            "unknowns",
            "unsupported_fields",
        )
        if field in selected
    ]
    return ordered


def _section(title: str, values: list[str]) -> list[str]:
    lines = [f"{title}:"]
    lines.extend(
        (f"- {value}" for value in values)
        if values
        else ("- none",)
    )
    return lines


def render_text(payload: Mapping[str, Any]) -> str:
    """Render one already-computed payload without reading the input again."""

    result = payload.get("result")
    label = RESULT_LABELS.get(result, "INVALID")
    lines = [
        f"Decision-OS Workflow Intake v0.1: {label}",
        "",
        *_section("Observed", _field_list(payload.get("observed_fields"))),
        "",
        *_section(
            "Missing",
            _all_fields(payload.get("missing_required_fields")),
        ),
    ]

    invalid = _all_fields(payload.get("invalid_fields"))
    if invalid:
        lines.extend(("", *_section("Invalid", invalid)))

    if result != "FIT_CHECK_READY":
        next_step = payload.get("minimum_next_step")
        if isinstance(next_step, str) and next_step:
            lines.extend(("", "Minimum next step:", next_step))

    lines.extend(
        (
            "",
            "This result confirms intake structure only.",
            "It does not diagnose the workflow or accept it for a paid Audit.",
        )
    )
    return "\n".join(lines) + "\n"
