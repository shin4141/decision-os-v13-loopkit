"""Deterministic text rendering for one Audit gate orchestration result."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import os
from typing import Any
import unicodedata

from . import audit_delivery as audit_contract
from . import audit_link as link_contract
from . import intake as intake_contract
from .audit_gate import (
    CHECK_CONTINUITY,
    CHECK_DELIVERY,
    CHECK_INTAKE,
    NEXT_STEP_CONTINUITY,
    NEXT_STEP_DELIVERY,
    NEXT_STEP_INTAKE,
    NEXT_STEP_INVALID,
    NEXT_STEP_READY,
    RESULT_INVALID,
    RESULT_NOT_READY,
    RESULT_NOT_RUN,
    RESULT_READY,
    UNKNOWN_ORDER,
)


RESULT_LABELS = {
    RESULT_READY: "HUMAN REVIEW READY",
    RESULT_NOT_READY: "NOT READY",
    RESULT_INVALID: "INVALID",
}
CHECK_LABELS = {
    intake_contract.RESULT_READY: "FIT CHECK READY",
    intake_contract.RESULT_INCOMPLETE: "INCOMPLETE",
    intake_contract.RESULT_INVALID: "INVALID",
    audit_contract.RESULT_READY: "DELIVERY READY",
    audit_contract.RESULT_INCOMPLETE: "INCOMPLETE",
    audit_contract.RESULT_INVALID: "INVALID",
    link_contract.RESULT_LINKED: "LINKED",
    link_contract.RESULT_MISMATCH: "MISMATCH",
    link_contract.RESULT_INVALID: "INVALID",
    RESULT_NOT_RUN: "NOT RUN",
}
AUDIT_GATE_USAGE = (
    "decision-os audit-gate <intake.json> <audit.md> | "
    "decision-os audit-gate --format json|text <intake.json> <audit.md>"
)
INTERNAL_FAILURE_NEXT_STEP = (
    "Retry the same two local files once; if the internal failure repeats, "
    "stop and report the command boundary."
)
ALLOWED_NEXT_STEPS = frozenset(
    (
        NEXT_STEP_READY,
        NEXT_STEP_INTAKE,
        NEXT_STEP_DELIVERY,
        NEXT_STEP_CONTINUITY,
        NEXT_STEP_INVALID,
        AUDIT_GATE_USAGE,
        INTERNAL_FAILURE_NEXT_STEP,
    )
)
_INTAKE_FIELD_ORDER = (*intake_contract.FIELD_ORDER, "unsupported_fields")
_DELIVERY_SECTION_ORDER = (
    "Title",
    *audit_contract.REQUIRED_SECTIONS,
    "Required heading order",
    "Fenced code block",
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _ordered(value: Any, order: Sequence[str]) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(
        value,
        (str, bytes, bytearray),
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
    inputs = _mapping(payload.get("inputs"))
    entry = _mapping(inputs.get(key))
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
    return name[:255]


def _checks(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(payload.get("checks"))


def _check(
    payload: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:
    return _mapping(_checks(payload).get(key))


def _check_result(
    payload: Mapping[str, Any],
    key: str,
    allowed: Sequence[str],
) -> str:
    result = _check(payload, key).get("result")
    if isinstance(result, str) and result in allowed:
        return result
    return RESULT_INVALID


def _blockers(payload: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    intake = _check(payload, CHECK_INTAKE)
    intake_result = _check_result(
        payload,
        CHECK_INTAKE,
        (
            intake_contract.RESULT_READY,
            intake_contract.RESULT_INCOMPLETE,
            intake_contract.RESULT_INVALID,
            RESULT_NOT_RUN,
        ),
    )
    if intake_result in (
        intake_contract.RESULT_INCOMPLETE,
        intake_contract.RESULT_INVALID,
    ):
        blockers.append(
            f"intake structure: {CHECK_LABELS[intake_result]}"
        )
    blockers.extend(
        f"intake missing field: {item}"
        for item in _ordered(
            intake.get("missing_fields"),
            _INTAKE_FIELD_ORDER,
        )
    )
    blockers.extend(
        f"intake invalid field: {item}"
        for item in _ordered(
            intake.get("invalid_fields"),
            _INTAKE_FIELD_ORDER,
        )
    )

    delivery = _check(payload, CHECK_DELIVERY)
    delivery_result = _check_result(
        payload,
        CHECK_DELIVERY,
        (
            audit_contract.RESULT_READY,
            audit_contract.RESULT_INCOMPLETE,
            audit_contract.RESULT_INVALID,
            RESULT_NOT_RUN,
        ),
    )
    if delivery_result in (
        audit_contract.RESULT_INCOMPLETE,
        audit_contract.RESULT_INVALID,
    ):
        blockers.append(
            f"delivery structure: {CHECK_LABELS[delivery_result]}"
        )
    blockers.extend(
        f"delivery missing section: {item}"
        for item in _ordered(
            delivery.get("missing_sections"),
            _DELIVERY_SECTION_ORDER,
        )
    )
    blockers.extend(
        f"delivery invalid section: {item}"
        for item in _ordered(
            delivery.get("invalid_sections"),
            _DELIVERY_SECTION_ORDER,
        )
    )
    blockers.extend(
        f"delivery missing field: {item}"
        for item in _ordered(
            delivery.get("missing_fields"),
            audit_contract.FIELD_ORDER,
        )
    )
    blockers.extend(
        f"delivery invalid field: {item}"
        for item in _ordered(
            delivery.get("invalid_fields"),
            audit_contract.FIELD_ORDER,
        )
    )

    continuity = _check(payload, CHECK_CONTINUITY)
    continuity_result = _check_result(
        payload,
        CHECK_CONTINUITY,
        (
            link_contract.RESULT_LINKED,
            link_contract.RESULT_MISMATCH,
            link_contract.RESULT_INVALID,
            RESULT_NOT_RUN,
        ),
    )
    if continuity_result in (
        link_contract.RESULT_MISMATCH,
        link_contract.RESULT_INVALID,
    ):
        blockers.append(
            f"incident continuity: {CHECK_LABELS[continuity_result]}"
        )
    blockers.extend(
        f"continuity mismatch: {item}"
        for item in _ordered(
            continuity.get("mismatched_fields"),
            link_contract.IDENTITY_FIELDS,
        )
    )
    blockers.extend(
        f"continuity missing field: {item}"
        for item in _ordered(
            continuity.get("missing_fields"),
            link_contract.IDENTITY_FIELDS,
        )
    )
    return blockers


def render_text(payload: Mapping[str, Any]) -> str:
    """Render one aggregate without reopening or echoing either input."""

    result = payload.get("result")
    label = RESULT_LABELS.get(result, "INVALID")
    intake_result = _check_result(
        payload,
        CHECK_INTAKE,
        (
            intake_contract.RESULT_READY,
            intake_contract.RESULT_INCOMPLETE,
            intake_contract.RESULT_INVALID,
            RESULT_NOT_RUN,
        ),
    )
    delivery_result = _check_result(
        payload,
        CHECK_DELIVERY,
        (
            audit_contract.RESULT_READY,
            audit_contract.RESULT_INCOMPLETE,
            audit_contract.RESULT_INVALID,
            RESULT_NOT_RUN,
        ),
    )
    continuity_result = _check_result(
        payload,
        CHECK_CONTINUITY,
        (
            link_contract.RESULT_LINKED,
            link_contract.RESULT_MISMATCH,
            link_contract.RESULT_INVALID,
            RESULT_NOT_RUN,
        ),
    )
    next_step = payload.get("minimum_next_step")
    if next_step not in ALLOWED_NEXT_STEPS:
        next_step = NEXT_STEP_INVALID

    lines = [
        f"Decision-OS Audit Gate v0.1: {label}",
        "",
        "Inputs:",
        f"- intake: {_input_name(payload, 'intake')}",
        f"- audit: {_input_name(payload, 'audit')}",
        "",
        "Checks:",
        f"- intake structure: {CHECK_LABELS[intake_result]}",
        f"- delivery structure: {CHECK_LABELS[delivery_result]}",
        f"- incident continuity: {CHECK_LABELS[continuity_result]}",
        "",
        *_section("Blockers", _blockers(payload)),
        "",
        *_section(
            "Unknowns",
            _ordered(payload.get("unknowns"), UNKNOWN_ORDER),
        ),
        "",
        "Minimum next step:",
        next_step,
        "",
        (
            "This result establishes structural eligibility for bounded human "
            "review only."
        ),
        (
            "It does not establish truth, diagnosis correctness, repair "
            "efficacy, client acceptance,"
        ),
        (
            "paid-delivery value, prevention, recovery, safety, productivity, "
            "or revenue."
        ),
    ]
    return "\n".join(lines) + "\n"
