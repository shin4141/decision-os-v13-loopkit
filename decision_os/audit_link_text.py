"""Deterministic text rendering for one Audit case-link result."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import os
from typing import Any
import unicodedata

from .audit_link import (
    IDENTITY_FIELDS,
    NEXT_STEP_INVALID,
    NEXT_STEP_LINKED,
    NEXT_STEP_MISMATCH,
    UNKNOWN_ORDER,
)


RESULT_LABELS = {
    "LINKED": "LINKED",
    "MISMATCH": "MISMATCH",
    "INVALID": "INVALID",
}
AUDIT_LINK_USAGE = (
    "decision-os audit-link <intake.json> <audit.md> | "
    "decision-os audit-link --format json|text <intake.json> <audit.md>"
)
INTERNAL_FAILURE_NEXT_STEP = (
    "Retry the same two local files once; if the internal failure repeats, "
    "stop and report the command boundary."
)
ALLOWED_NEXT_STEPS = frozenset(
    (
        NEXT_STEP_LINKED,
        NEXT_STEP_MISMATCH,
        NEXT_STEP_INVALID,
        AUDIT_LINK_USAGE,
        INTERNAL_FAILURE_NEXT_STEP,
    )
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


def _input_name(payload: Mapping[str, Any], key: str) -> str:
    inputs = payload.get("inputs")
    if not isinstance(inputs, Mapping):
        return "unavailable"
    entry = inputs.get(key)
    if not isinstance(entry, Mapping):
        return "unavailable"
    name = entry.get("name")
    if (
        not isinstance(name, str)
        or not name
        or name in (".", "..")
        or os.path.basename(name) != name
        or any(
            unicodedata.category(character)
            in {"Cc", "Cf", "Cs", "Zl", "Zp"}
            for character in name
        )
    ):
        return "unavailable"
    return name


def render_text(payload: Mapping[str, Any]) -> str:
    """Render one computed result without reopening or echoing either input."""

    result = payload.get("result")
    label = RESULT_LABELS.get(result, "INVALID")
    unknowns = _ordered_list(payload.get("unknowns"), UNKNOWN_ORDER)
    next_step = payload.get("minimum_next_step")
    if next_step not in ALLOWED_NEXT_STEPS:
        next_step = NEXT_STEP_INVALID

    lines = [
        f"Decision-OS Audit Case Link v0.1: {label}",
        "",
        "Inputs:",
        f"- intake: {_input_name(payload, 'intake')}",
        f"- audit: {_input_name(payload, 'audit')}",
        "",
        *_section(
            "Matched",
            _ordered_list(payload.get("matched_fields"), IDENTITY_FIELDS),
        ),
        "",
        *_section(
            "Mismatched",
            _ordered_list(payload.get("mismatched_fields"), IDENTITY_FIELDS),
        ),
        "",
        *_section(
            "Missing",
            _ordered_list(payload.get("missing_fields"), IDENTITY_FIELDS),
        ),
        "",
        *_section("Unknowns", unknowns),
        "",
        "Minimum next step:",
        next_step,
        "",
        "This result checks bounded identity continuity only.",
        (
            "It does not establish factual correctness, diagnosis quality, "
            "repair efficacy, or client acceptance."
        ),
    ]
    return "\n".join(lines) + "\n"
