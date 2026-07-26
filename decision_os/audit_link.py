"""Deterministic identity-continuity checks for one intake and one Audit."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import re
from typing import Any
import unicodedata

from . import audit_delivery as audit_contract
from . import intake as intake_contract


EXIT_LINKED = 0
EXIT_NOT_LINKED = 4

RESULT_SCHEMA_VERSION = "decision-os.audit-link-result.v0.1"

RESULT_LINKED = "LINKED"
RESULT_MISMATCH = "MISMATCH"
RESULT_INVALID = "INVALID"

IDENTITY_FIELDS = (
    "workflow",
    "bounded_path",
    "trigger",
    "expected_state",
    "observed_state",
    "restart_or_fallback_path",
)

AUDIT_FIELD_MAPPINGS = {
    "workflow": ("Scope", "Application or Workflow"),
    "bounded_path": ("Scope", "Bounded Workflow Path"),
    "trigger": ("Incident As-of State", "Trigger"),
    "expected_state": ("Incident As-of State", "Expected State"),
    "observed_state": ("Incident As-of State", "Observed State"),
    "restart_or_fallback_path": (
        "Incident As-of State",
        "Current Restart or Fallback Path",
    ),
}

CLAIMS_NOT_MADE = (
    "truth of the intake packet",
    "correctness of the Audit diagnosis",
    "completeness of source materials",
    "efficacy or uniqueness of the Priority Fix",
    "client acceptance",
    "prevention, recovery, security, safety, productivity, cost, or revenue",
    "identity of systems not represented by the supplied files",
    "absence of contradictory prose elsewhere",
)

NEXT_STEP_LINKED = (
    "Use LINKED only as bounded field-continuity evidence; continue with "
    "human review of factual correctness."
)
NEXT_STEP_MISMATCH = (
    "Copy the six accepted intake identity values into the corresponding "
    "Audit fields without paraphrasing, then rerun decision-os audit-link."
)
NEXT_STEP_INVALID = (
    "Provide one local regular UTF-8 v0.1 intake JSON file and one local "
    "regular UTF-8 Audit Markdown file, then rerun decision-os audit-link."
)

UNKNOWN_ORDER = (
    "intake_structure",
    "audit_structure",
    "cli_usage",
    "internal_failure",
)


class _ContractInvalid(Exception):
    """One input did not satisfy its full accepted v0.1 contract."""

    def __init__(self, missing_fields: Iterable[str] = ()) -> None:
        super().__init__()
        self.missing_fields = tuple(missing_fields)


def _safe_output_name(
    value: Path | str | None,
    *,
    audit: bool,
) -> str:
    helper = (
        audit_contract._safe_basename
        if audit
        else intake_contract._safe_basename
    )
    name = helper(value)
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in name
    ):
        return "unavailable"
    return name


def _ordered_fields(values: Iterable[str]) -> list[str]:
    selected = set(values)
    return [field for field in IDENTITY_FIELDS if field in selected]


def _ordered_unknowns(values: Iterable[str]) -> list[str]:
    selected = set(values)
    return [marker for marker in UNKNOWN_ORDER if marker in selected]


def result_payload(
    *,
    intake_name: Path | str | None,
    audit_name: Path | str | None,
    result: str,
    matched_fields: Iterable[str] = (),
    mismatched_fields: Iterable[str] = (),
    missing_fields: Iterable[str] = (),
    unknowns: Iterable[str] = (),
    minimum_next_step: str,
) -> dict[str, Any]:
    """Build one stable result without exposing compared field contents."""

    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "command": "audit-link",
        "result": result,
        "matched_fields": _ordered_fields(matched_fields),
        "mismatched_fields": _ordered_fields(mismatched_fields),
        "missing_fields": _ordered_fields(missing_fields),
        "unknowns": _ordered_unknowns(unknowns),
        "claims_not_made": list(CLAIMS_NOT_MADE),
        "minimum_next_step": minimum_next_step,
        "inputs": {
            "intake": {
                "name": _safe_output_name(intake_name, audit=False),
                "content_echoed": False,
            },
            "audit": {
                "name": _safe_output_name(audit_name, audit=True),
                "content_echoed": False,
            },
        },
    }


def invalid_payload(
    intake_path: Path | str | None,
    audit_path: Path | str | None,
    *,
    missing_fields: Iterable[str] = (),
    unknowns: Iterable[str] = (),
    minimum_next_step: str = NEXT_STEP_INVALID,
) -> dict[str, Any]:
    """Return the stable INVALID shape for source or command rejection."""

    return result_payload(
        intake_name=intake_path,
        audit_name=audit_path,
        result=RESULT_INVALID,
        missing_fields=missing_fields,
        unknowns=unknowns,
        minimum_next_step=minimum_next_step,
    )


def normalize_identity(value: str) -> str:
    """Apply only the bounded whitespace normalization used for comparison."""

    normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    return re.sub(r"[ \t\n]+", " ", normalized)


def _load_intake_values(path: Path) -> dict[str, str]:
    try:
        content = intake_contract._read_local_regular_file(path)
        packet = intake_contract._parse_packet(content)
    except intake_contract._InputRejected as exc:
        raise _ContractInvalid from exc

    _, missing, invalid, _ = intake_contract._inspect_packet(packet)
    missing_identity = [
        field
        for field in IDENTITY_FIELDS
        if field in set((*missing, *invalid))
    ]
    if missing or invalid:
        raise _ContractInvalid(missing_identity)

    output: dict[str, str] = {}
    for field in IDENTITY_FIELDS:
        value = packet.get(field)
        if not isinstance(value, str):
            raise RuntimeError("validated intake identity field unavailable")
        output[field] = value
    return output


def _audit_missing_identity_fields(payload: dict[str, Any]) -> list[str]:
    unavailable = {
        item
        for key in ("missing_required_fields", "invalid_fields")
        for item in payload.get(key, ())
        if isinstance(item, str)
    }
    return [
        field
        for field in IDENTITY_FIELDS
        if AUDIT_FIELD_MAPPINGS[field][1] in unavailable
    ]


def _load_audit_values(path: Path) -> dict[str, str]:
    try:
        content = audit_contract._read_local_regular_file(path)
        text = audit_contract._decode_markdown(content)
    except audit_contract._InputRejected as exc:
        raise _ContractInvalid from exc

    payload, exit_code = audit_contract._inspect_markdown(text)
    if exit_code != audit_contract.EXIT_READY:
        raise _ContractInvalid(_audit_missing_identity_fields(payload))

    lines = text.splitlines()
    visible, content_visible, unclosed_fence = audit_contract._visible_lines(
        lines
    )
    if unclosed_fence:
        raise RuntimeError("validated Audit fence state unavailable")
    headings = audit_contract._headings(lines, visible)

    by_section: dict[str, dict[str, list[str]]] = {}
    for section in ("Scope", "Incident As-of State"):
        bounds = audit_contract._section_range(
            section,
            headings,
            len(lines),
        )
        if bounds is None:
            raise RuntimeError("validated Audit section unavailable")
        start, end = bounds
        labels = tuple(
            audit_label
            for mapped_section, audit_label in AUDIT_FIELD_MAPPINGS.values()
            if mapped_section == section
        )
        by_section[section] = audit_contract._field_values(
            lines,
            visible,
            content_visible,
            start,
            end,
            labels,
        )

    output: dict[str, str] = {}
    for field in IDENTITY_FIELDS:
        section, audit_label = AUDIT_FIELD_MAPPINGS[field]
        occurrences = by_section[section][audit_label]
        if len(occurrences) != 1:
            raise RuntimeError("validated Audit identity field unavailable")
        output[field] = occurrences[0]
    return output


def validate_audit_link_files(
    intake_path: Path,
    audit_path: Path,
) -> tuple[dict[str, Any], int]:
    """Compare accepted identity fields without writing or diagnosing."""

    values: dict[str, dict[str, str]] = {}
    missing_fields: list[str] = []
    unknowns: list[str] = []

    try:
        values["intake"] = _load_intake_values(intake_path)
    except _ContractInvalid as exc:
        missing_fields.extend(exc.missing_fields)
        unknowns.append("intake_structure")

    try:
        values["audit"] = _load_audit_values(audit_path)
    except _ContractInvalid as exc:
        missing_fields.extend(exc.missing_fields)
        unknowns.append("audit_structure")

    if unknowns:
        return (
            invalid_payload(
                intake_path,
                audit_path,
                missing_fields=missing_fields,
                unknowns=unknowns,
            ),
            EXIT_NOT_LINKED,
        )

    matched: list[str] = []
    mismatched: list[str] = []
    for field in IDENTITY_FIELDS:
        intake_value = normalize_identity(values["intake"][field])
        audit_value = normalize_identity(values["audit"][field])
        if intake_value == audit_value:
            matched.append(field)
        else:
            mismatched.append(field)

    if mismatched:
        return (
            result_payload(
                intake_name=str(intake_path),
                audit_name=str(audit_path),
                result=RESULT_MISMATCH,
                matched_fields=matched,
                mismatched_fields=mismatched,
                minimum_next_step=NEXT_STEP_MISMATCH,
            ),
            EXIT_NOT_LINKED,
        )

    return (
        result_payload(
            intake_name=str(intake_path),
            audit_name=str(audit_path),
            result=RESULT_LINKED,
            matched_fields=matched,
            minimum_next_step=NEXT_STEP_LINKED,
        ),
        EXIT_LINKED,
    )
