"""Deterministic structural checks for one local Audit delivery packet."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
import os
from pathlib import Path
import re
import stat
from typing import Any
import unicodedata


EXIT_READY = 0
EXIT_INCOMPLETE = 4

RESULT_SCHEMA_VERSION = "decision-os.audit-delivery-result.v0.1"
SUPPORTED_PROFILE = "AI_APPLICATION_WORKFLOW"
MAX_INPUT_BYTES = 512 * 1024

RESULT_READY = "DELIVERY_READY"
RESULT_INCOMPLETE = "INCOMPLETE"
RESULT_INVALID = "INVALID"

REQUIRED_SECTIONS = (
    "Scope",
    "Source Materials",
    "Incident As-of State",
    "Friction Map",
    "Restartability Diagnosis",
    "Priority Fix",
    "Operational Asset",
    "Before / After Restart Check",
    "Unknowns",
    "Exclusions",
    "Claim Boundary",
    "Completion Line",
)

SCOPE_FIELDS = (
    "Audit Profile",
    "Application or Workflow",
    "Bounded Workflow Path",
    "Audit As-of",
)
SOURCE_FIELDS = (
    "Reviewed",
    "Not Reviewed",
    "Material Restrictions",
)
INCIDENT_FIELDS = (
    "Trigger",
    "Expected State",
    "Observed State",
    "Current Restart or Fallback Path",
    "Current Owner",
    "Next Safe Action",
)
DIAGNOSIS_DIMENSIONS = (
    "Trigger Clarity",
    "Accepted-State Clarity",
    "Evidence Continuity",
    "Completion Integrity",
    "Restartability",
    "Ownership / Next Actor",
    "Human Recovery Burden",
    "Safe Next Action",
)
DIAGNOSIS_FIELDS = (*DIAGNOSIS_DIMENSIONS, "Overall Diagnosis")
PRIORITY_FIELDS = ("Selected Fix", "Why Priority")
ASSET_FIELDS = ("Asset Type", "Asset Content")
RESTART_CHECK_FIELDS = ("Before", "After", "Still UNKNOWN")
CLAIM_BOUNDARIES = (
    ("Vendor Bug Fix", "NOT CLAIMED"),
    ("Future Prevention", "NOT CLAIMED"),
    ("Lost-State Recovery", "NOT CLAIMED"),
    ("Security or Safety", "NOT CLAIMED"),
    ("Productivity / Labor / Cost / Revenue", "NOT CLAIMED"),
    ("Unreviewed Systems", "NOT DIAGNOSED"),
    ("Native Resume", "NOT PROOF OF TRUSTWORTHY RESTART"),
)
CLAIM_FIELDS = tuple(field for field, _ in CLAIM_BOUNDARIES)

FRICTION_TABLE_FIELD = "Friction Map table"
UNKNOWNS_CONTENT_FIELD = "Unknowns content"
EXCLUSIONS_CONTENT_FIELD = "Exclusions content"
COMPLETION_CONTENT_FIELD = "Completion Line content"

FIELDS_BY_SECTION = {
    "Scope": SCOPE_FIELDS,
    "Source Materials": SOURCE_FIELDS,
    "Incident As-of State": INCIDENT_FIELDS,
    "Friction Map": (FRICTION_TABLE_FIELD,),
    "Restartability Diagnosis": DIAGNOSIS_FIELDS,
    "Priority Fix": PRIORITY_FIELDS,
    "Operational Asset": ASSET_FIELDS,
    "Before / After Restart Check": RESTART_CHECK_FIELDS,
    "Unknowns": (UNKNOWNS_CONTENT_FIELD,),
    "Exclusions": (EXCLUSIONS_CONTENT_FIELD,),
    "Claim Boundary": CLAIM_FIELDS,
    "Completion Line": (COMPLETION_CONTENT_FIELD,),
}
FIELD_ORDER = tuple(
    field
    for section in REQUIRED_SECTIONS
    for field in FIELDS_BY_SECTION[section]
)

CLAIMS_NOT_MADE = (
    "truth or completeness of source materials",
    "factual correctness of the diagnosis",
    "uniqueness of the selected Priority Fix",
    "efficacy of the Operational Asset",
    "absence of contradictory prose elsewhere in the document",
    "software, workflow, security, or product correctness",
    "prevention or recovery",
    "productivity, labor, cost, or revenue improvement",
    "client acceptance",
    "paid-delivery value",
    "testimonial or external delivery evidence",
)

NEXT_STEP_READY = (
    "Submit the structurally closed delivery for bounded human review; do not "
    "infer diagnosis truth, repair efficacy, or client acceptance."
)
NEXT_STEP_INCOMPLETE = (
    "Add or correct only the listed delivery structure, then rerun "
    "decision-os audit-check."
)
NEXT_STEP_INVALID = (
    "Provide one local regular UTF-8 Markdown file using the supported Audit "
    "profile, then rerun decision-os audit-check."
)

_HEADING_PATTERN = re.compile(
    r"^[ ]{0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$"
)
_OPEN_FENCE_PATTERN = re.compile(
    r"^[ ]{0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$"
)
_BULLET_PATTERN = re.compile(r"^[ ]{0,3}[-*+][ \t]+(.+?)\s*$")
_TABLE_DELIMITER_PATTERN = re.compile(r"^:?-{3,}:?$")
_RATING_PATTERN = re.compile(
    r"^(PASS|PARTIAL|FAIL|UNKNOWN)"
    r"(?:[ \t]+(?:(?:—|–|-|:)[ \t]+)?|(?:—|–|-|:)[ \t]*)"
    r"(\S.*)$"
)
_ANGLE_PLACEHOLDER_PATTERN = re.compile(r"^<[^<>]+>$", re.DOTALL)
_PLACEHOLDER_WORDS = frozenset(
    ("TBD", "TODO", "FIXME", "PLACEHOLDER")
)
_BOUNDED_EMPTY_DECLARATION = "none recorded within the accepted scope"

_SECTION_MARKER_ORDER = (
    "Title",
    *REQUIRED_SECTIONS,
    "Required heading order",
    "Fenced code block",
)
_UNKNOWN_MARKER_ORDER = (
    *DIAGNOSIS_DIMENSIONS,
    "Unknowns section",
    "cli_usage",
    "internal_failure",
)


class _InputRejected(Exception):
    """One local input did not satisfy the bounded read contract."""


def _safe_basename(
    path: Path | str | os.PathLike[str] | None,
) -> str:
    if path is None:
        return "unavailable"
    try:
        name = os.path.basename(os.path.abspath(os.fspath(path)))
    except (TypeError, ValueError, OSError):
        return "unavailable"
    if not name or name in (".", ".."):
        return "unavailable"
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs"}
        for character in name
    ):
        return "unavailable"
    return name[:255]


def _ordered(
    values: Iterable[str],
    order: Sequence[str],
) -> list[str]:
    selected = set(values)
    return [item for item in order if item in selected]


def result_payload(
    *,
    name: str,
    profile: str,
    result: str,
    observed_sections: Iterable[str] = (),
    missing_required_sections: Iterable[str] = (),
    invalid_sections: Iterable[str] = (),
    observed_fields: Iterable[str] = (),
    missing_required_fields: Iterable[str] = (),
    invalid_fields: Iterable[str] = (),
    unknowns: Iterable[str] = (),
    minimum_next_step: str,
) -> dict[str, Any]:
    """Build one stable result without including delivery content."""

    safe_profile = (
        SUPPORTED_PROFILE
        if profile == SUPPORTED_PROFILE
        else "UNKNOWN"
    )
    return {
        "claims_not_made": list(CLAIMS_NOT_MADE),
        "command": "audit-check",
        "input": {
            "content_echoed": False,
            "name": _safe_basename(name),
        },
        "invalid_fields": _ordered(invalid_fields, FIELD_ORDER),
        "invalid_sections": _ordered(
            invalid_sections,
            _SECTION_MARKER_ORDER,
        ),
        "minimum_next_step": minimum_next_step,
        "missing_required_fields": _ordered(
            missing_required_fields,
            FIELD_ORDER,
        ),
        "missing_required_sections": _ordered(
            missing_required_sections,
            _SECTION_MARKER_ORDER,
        ),
        "observed_fields": _ordered(observed_fields, FIELD_ORDER),
        "observed_sections": _ordered(
            observed_sections,
            REQUIRED_SECTIONS,
        ),
        "profile": safe_profile,
        "result": result,
        "schema_version": RESULT_SCHEMA_VERSION,
        "unknowns": _ordered(unknowns, _UNKNOWN_MARKER_ORDER),
    }


def invalid_payload(
    path: Path | str | os.PathLike[str] | None,
    *,
    minimum_next_step: str = NEXT_STEP_INVALID,
    unknowns: Iterable[str] = (),
) -> dict[str, Any]:
    """Return the stable INVALID shape for bounded read rejection."""

    return result_payload(
        name=_safe_basename(path),
        profile="UNKNOWN",
        result=RESULT_INVALID,
        minimum_next_step=minimum_next_step,
        unknowns=unknowns,
    )


def _regular_file_snapshot(path: Path) -> tuple[Path, os.stat_result]:
    try:
        absolute = Path(os.path.abspath(os.fspath(path)))
        metadata = os.lstat(absolute)
    except (TypeError, ValueError, OSError) as exc:
        raise _InputRejected from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise _InputRejected
    if metadata.st_size > MAX_INPUT_BYTES:
        raise _InputRejected
    return absolute, metadata


def _snapshot_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _read_local_regular_file(path: Path) -> bytes:
    absolute, before = _regular_file_snapshot(path)
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK

    try:
        descriptor = os.open(absolute, flags)
    except (OSError, ValueError) as exc:
        raise _InputRejected from exc

    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
        ):
            raise _InputRejected
        if opened.st_size > MAX_INPUT_BYTES:
            raise _InputRejected

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
            raise _InputRejected

        after_open = os.fstat(descriptor)
        after_path = os.lstat(absolute)
        identity = _snapshot_identity(before)
        if (
            identity != _snapshot_identity(opened)
            or identity != _snapshot_identity(after_open)
            or identity != _snapshot_identity(after_path)
        ):
            raise _InputRejected
        return b"".join(chunks)
    except OSError as exc:
        raise _InputRejected from exc
    finally:
        os.close(descriptor)


def _decode_markdown(content: bytes) -> str:
    try:
        return content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise _InputRejected from exc


def _visible_lines(
    lines: Sequence[str],
) -> tuple[list[bool], list[bool], bool]:
    visible: list[bool] = []
    content_visible: list[bool] = []
    fence_character: str | None = None
    fence_length = 0

    for line in lines:
        if fence_character is None:
            match = _OPEN_FENCE_PATTERN.match(line)
            if match is None:
                visible.append(True)
                content_visible.append(True)
                continue
            fence = match.group("fence")
            fence_character = fence[0]
            fence_length = len(fence)
            visible.append(False)
            content_visible.append(False)
            continue

        visible.append(False)
        closing = re.match(
            rf"^[ ]{{0,3}}{re.escape(fence_character)}"
            rf"{{{fence_length},}}[ \t]*$",
            line,
        )
        if closing is not None:
            content_visible.append(False)
            fence_character = None
            fence_length = 0
        else:
            content_visible.append(True)

    return visible, content_visible, fence_character is not None


def _heading(line: str) -> tuple[int, str] | None:
    match = _HEADING_PATTERN.match(line)
    if match is None:
        return None
    text = (match.group(2) or "").strip()
    if text and set(text) == {"#"}:
        text = ""
    else:
        text = re.sub(r"[ \t]+#+[ \t]*$", "", text).strip()
    return len(match.group(1)), text


def _headings(
    lines: Sequence[str],
    visible: Sequence[bool],
) -> list[tuple[int, int, str]]:
    output: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        if not visible[index]:
            continue
        heading = _heading(line)
        if heading is not None:
            level, text = heading
            output.append((index, level, text))
    return output


def _section_range(
    name: str,
    headings: Sequence[tuple[int, int, str]],
    line_count: int,
) -> tuple[int, int] | None:
    matches = [
        item
        for item in headings
        if item[1] == 2 and item[2] == name
    ]
    if len(matches) != 1:
        return None
    start = matches[0][0] + 1
    end = line_count
    for index, level, _ in headings:
        if index >= start and level <= 2:
            end = index
            break
    return start, end


def _field_pattern(labels: Sequence[str]) -> re.Pattern[str]:
    alternatives = "|".join(
        re.escape(label)
        for label in sorted(labels, key=len, reverse=True)
    )
    return re.compile(
        rf"^[ ]{{0,3}}(?P<label>{alternatives}):"
        r"[ \t]*(?P<value>.*)$"
    )


def _field_values(
    lines: Sequence[str],
    visible: Sequence[bool],
    content_visible: Sequence[bool],
    start: int,
    end: int,
    labels: Sequence[str],
) -> dict[str, list[str]]:
    values = {label: [] for label in labels}
    pattern = _field_pattern(labels)
    active_label: str | None = None
    active_lines: list[str] = []

    def finish() -> None:
        nonlocal active_label, active_lines
        if active_label is not None:
            values[active_label].append(_normalized_value(active_lines))
        active_label = None
        active_lines = []

    for index in range(start, end):
        match = pattern.match(lines[index]) if visible[index] else None
        if match is not None:
            finish()
            active_label = match.group("label")
            active_lines = [match.group("value")]
            if active_label != "Asset Content":
                finish()
        elif (
            active_label == "Asset Content"
            and content_visible[index]
        ):
            active_lines.append(lines[index])
    finish()
    return values


def _normalized_value(lines: Sequence[str]) -> str:
    meaningful = [line.strip() for line in lines if line.strip()]
    return "\n".join(meaningful).strip()


def _is_placeholder(value: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return True
    normalized = re.sub(
        r"^(?:(?:#{1,6}|[-*+])[ \t]+)+",
        "",
        normalized,
        count=1,
    ).strip()
    if normalized.upper() in _PLACEHOLDER_WORDS:
        return True
    return bool(_ANGLE_PLACEHOLDER_PATTERN.fullmatch(normalized))


def _starts_with_unknown(value: str) -> bool:
    return re.match(r"^UNKNOWN\b", value.strip(), re.IGNORECASE) is not None


def _inspect_plain_fields(
    values: dict[str, list[str]],
    *,
    disallow_unknown: Iterable[str] = (),
) -> tuple[list[str], list[str], list[str]]:
    unknown_forbidden = set(disallow_unknown)
    observed: list[str] = []
    missing: list[str] = []
    invalid: list[str] = []
    for label, occurrences in values.items():
        if not occurrences:
            missing.append(label)
        elif (
            len(occurrences) != 1
            or _is_placeholder(occurrences[0])
            or (
                label in unknown_forbidden
                and _starts_with_unknown(occurrences[0])
            )
        ):
            invalid.append(label)
        else:
            observed.append(label)
    return observed, missing, invalid


def _inspect_diagnosis_fields(
    values: dict[str, list[str]],
) -> tuple[list[str], list[str], list[str], list[str]]:
    observed: list[str] = []
    missing: list[str] = []
    invalid: list[str] = []
    unknowns: list[str] = []
    for label in DIAGNOSIS_FIELDS:
        occurrences = values[label]
        if not occurrences:
            missing.append(label)
            continue
        if len(occurrences) != 1 or _is_placeholder(occurrences[0]):
            invalid.append(label)
            continue
        value = occurrences[0]
        if label not in DIAGNOSIS_DIMENSIONS:
            observed.append(label)
            continue
        match = _RATING_PATTERN.match(value)
        if match is None or _is_placeholder(match.group(2)):
            invalid.append(label)
            continue
        observed.append(label)
        if match.group(1) == "UNKNOWN":
            unknowns.append(label)
    return observed, missing, invalid, unknowns


def _table_cells(line: str) -> list[str]:
    indentation = len(line) - len(line.lstrip(" "))
    if indentation > 3 or line.startswith("\t"):
        return []
    stripped = line.strip()
    if not stripped or "|" not in stripped:
        return []
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _valid_friction_table(
    lines: Sequence[str],
    visible: Sequence[bool],
    start: int,
    end: int,
) -> tuple[bool, bool]:
    expected = (
        "point",
        "expected carrier",
        "observed gap",
        "returned human work",
    )
    table_seen = False
    for index in range(start, end):
        if not visible[index]:
            continue
        header = _table_cells(lines[index])
        if not header:
            continue
        table_seen = True
        if tuple(cell.casefold() for cell in header) != expected:
            continue
        delimiter_index = index + 1
        if (
            delimiter_index >= end
            or not visible[delimiter_index]
        ):
            return True, False
        delimiter = _table_cells(lines[delimiter_index])
        if (
            len(delimiter) != len(expected)
            or any(
                _TABLE_DELIMITER_PATTERN.fullmatch(cell) is None
                for cell in delimiter
            )
        ):
            return True, False

        row_index = delimiter_index + 1
        while row_index < end:
            if not visible[row_index]:
                break
            if not lines[row_index].strip():
                break
            row = _table_cells(lines[row_index])
            if not row:
                break
            if (
                len(row) == len(expected)
                and all(not _is_placeholder(cell) for cell in row)
            ):
                return True, True
            row_index += 1
        return True, False
    return table_seen, False


def _bullet_values(
    lines: Sequence[str],
    visible: Sequence[bool],
    start: int,
    end: int,
) -> list[str]:
    values: list[str] = []
    for index in range(start, end):
        if not visible[index]:
            continue
        match = _BULLET_PATTERN.match(lines[index])
        if match is not None:
            values.append(match.group(1).strip())
    return values


def _section_content(
    lines: Sequence[str],
    visible: Sequence[bool],
    start: int,
    end: int,
) -> str:
    content = [
        lines[index]
        for index in range(start, end)
        if visible[index] and _heading(lines[index]) is None
    ]
    return _normalized_value(content)


def _inspect_markdown(
    text: str,
) -> tuple[dict[str, Any], int]:
    lines = text.splitlines()
    visible, content_visible, unclosed_fence = _visible_lines(lines)
    headings = _headings(lines, visible)

    observed_sections: list[str] = []
    missing_sections: list[str] = []
    invalid_sections: list[str] = []
    observed_fields: list[str] = []
    missing_fields: list[str] = []
    invalid_fields: list[str] = []
    unknowns: list[str] = []
    profile = "UNKNOWN"
    structurally_invalid = unclosed_fence

    all_level_one = [item for item in headings if item[1] == 1]
    titles = [
        item
        for item in all_level_one
        if bool(item[2]) and not _is_placeholder(item[2])
    ]
    if not titles:
        missing_sections.append("Title")
    if len(all_level_one) > 1:
        invalid_sections.append("Title")
        structurally_invalid = True

    positions: list[int] = []
    for section in REQUIRED_SECTIONS:
        matches = [
            item
            for item in headings
            if item[1] == 2 and item[2] == section
        ]
        if not matches:
            missing_sections.append(section)
            missing_fields.extend(FIELDS_BY_SECTION[section])
        elif len(matches) > 1:
            invalid_sections.append(section)
            structurally_invalid = True
        else:
            observed_sections.append(section)
            positions.append(matches[0][0])

    if positions != sorted(positions):
        invalid_sections.append("Required heading order")
        structurally_invalid = True
    if titles and positions and titles[0][0] > min(positions):
        invalid_sections.append("Required heading order")
        structurally_invalid = True
    if unclosed_fence:
        invalid_sections.append("Fenced code block")

    for section in REQUIRED_SECTIONS:
        bounds = _section_range(section, headings, len(lines))
        if bounds is None:
            continue
        start, end = bounds

        if section == "Friction Map":
            table_seen, table_valid = _valid_friction_table(
                lines,
                visible,
                start,
                end,
            )
            if table_valid:
                observed_fields.append(FRICTION_TABLE_FIELD)
            elif table_seen:
                invalid_fields.append(FRICTION_TABLE_FIELD)
            else:
                missing_fields.append(FRICTION_TABLE_FIELD)
            continue

        if section in ("Unknowns", "Exclusions"):
            marker = (
                UNKNOWNS_CONTENT_FIELD
                if section == "Unknowns"
                else EXCLUSIONS_CONTENT_FIELD
            )
            bullets = _bullet_values(lines, visible, start, end)
            valid_bullets = [
                value for value in bullets if not _is_placeholder(value)
            ]
            if valid_bullets:
                observed_fields.append(marker)
                if (
                    section == "Unknowns"
                    and any(
                        value.casefold()
                        != _BOUNDED_EMPTY_DECLARATION
                        for value in valid_bullets
                    )
                ):
                    unknowns.append("Unknowns section")
            else:
                invalid_fields.append(marker)
            continue

        if section == "Completion Line":
            content = _section_content(lines, visible, start, end)
            if (
                _is_placeholder(content)
                or _starts_with_unknown(content)
            ):
                invalid_fields.append(COMPLETION_CONTENT_FIELD)
            else:
                observed_fields.append(COMPLETION_CONTENT_FIELD)
            continue

        labels = FIELDS_BY_SECTION[section]
        values = _field_values(
            lines,
            visible,
            content_visible,
            start,
            end,
            labels,
        )
        if section == "Restartability Diagnosis":
            found, missing, invalid, declared_unknowns = (
                _inspect_diagnosis_fields(values)
            )
            unknowns.extend(declared_unknowns)
        elif section == "Claim Boundary":
            found = []
            missing = []
            invalid = []
            expected_values = dict(CLAIM_BOUNDARIES)
            for label in labels:
                occurrences = values[label]
                if not occurrences:
                    missing.append(label)
                elif (
                    len(occurrences) != 1
                    or occurrences[0] != expected_values[label]
                ):
                    invalid.append(label)
                else:
                    found.append(label)
        else:
            disallow_unknown: Iterable[str] = ()
            if section == "Priority Fix":
                disallow_unknown = PRIORITY_FIELDS
            elif section == "Operational Asset":
                disallow_unknown = ASSET_FIELDS
            found, missing, invalid = _inspect_plain_fields(
                values,
                disallow_unknown=disallow_unknown,
            )

        observed_fields.extend(found)
        missing_fields.extend(missing)
        invalid_fields.extend(invalid)

        if section == "Scope":
            occurrences = values["Audit Profile"]
            if (
                len(occurrences) == 1
                and occurrences[0] == SUPPORTED_PROFILE
            ):
                profile = SUPPORTED_PROFILE
            elif (
                len(occurrences) == 1
                and not _is_placeholder(occurrences[0])
            ):
                structurally_invalid = True
                if "Audit Profile" in observed_fields:
                    observed_fields.remove("Audit Profile")
                invalid_fields.append("Audit Profile")

    if structurally_invalid:
        result = RESULT_INVALID
        exit_code = EXIT_INCOMPLETE
        next_step = NEXT_STEP_INVALID
    elif missing_sections or missing_fields or invalid_fields:
        result = RESULT_INCOMPLETE
        exit_code = EXIT_INCOMPLETE
        next_step = NEXT_STEP_INCOMPLETE
    else:
        result = RESULT_READY
        exit_code = EXIT_READY
        next_step = NEXT_STEP_READY

    payload = result_payload(
        name="unavailable",
        profile=profile,
        result=result,
        observed_sections=observed_sections,
        missing_required_sections=missing_sections,
        invalid_sections=invalid_sections,
        observed_fields=observed_fields,
        missing_required_fields=missing_fields,
        invalid_fields=invalid_fields,
        unknowns=unknowns,
        minimum_next_step=next_step,
    )
    return payload, exit_code


def validate_audit_delivery_file(
    path: Path,
) -> tuple[dict[str, Any], int]:
    """Check one local delivery without writing, diagnosing, or echoing it."""

    safe_name = _safe_basename(path)
    try:
        text = _decode_markdown(_read_local_regular_file(path))
    except _InputRejected:
        return invalid_payload(path), EXIT_INCOMPLETE

    payload, exit_code = _inspect_markdown(text)
    payload["input"]["name"] = safe_name
    return payload, exit_code
