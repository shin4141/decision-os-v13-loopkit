"""Deterministic structural checks for one local workflow incident packet."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
from typing import Any, Iterable
import unicodedata


EXIT_READY = 0
EXIT_INCOMPLETE = 4

INPUT_SCHEMA_VERSION = "decision-os.workflow-intake.v0.1"
RESULT_SCHEMA_VERSION = "decision-os.workflow-intake-result.v0.1"
MAX_INPUT_BYTES = 256 * 1024

RESULT_READY = "FIT_CHECK_READY"
RESULT_INCOMPLETE = "INCOMPLETE"
RESULT_INVALID = "INVALID"

REQUIRED_STRING_FIELDS = (
    "workflow",
    "bounded_path",
    "incident_as_of",
    "trigger",
    "expected_state",
    "observed_state",
    "restart_or_fallback_path",
)
REQUIRED_NONEMPTY_LIST_FIELDS = (
    "human_recovery_work",
    "materials_available",
)
REQUIRED_LIST_FIELDS = ("prohibited_materials",)
OPTIONAL_STRING_FIELDS = (
    "next_actor",
    "next_safe_action",
)
OPTIONAL_LIST_FIELDS = ("unknowns",)
FIELD_ORDER = (
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
)
REQUIRED_FIELD_ORDER = (
    "schema_version",
    *REQUIRED_STRING_FIELDS,
    *REQUIRED_NONEMPTY_LIST_FIELDS,
    *REQUIRED_LIST_FIELDS,
)
ACCEPTED_FIELDS = frozenset(FIELD_ORDER)

CLAIMS_NOT_MADE = (
    "workflow diagnosis",
    "vendor bug diagnosis",
    "task or product correctness",
    "security or safety",
    "recovery of lost state",
    "prevention of future incidents",
    "productivity, labor, cost, or revenue improvement",
    "paid Audit acceptance",
    "native resume as proof of trustworthy restart",
)

NEXT_STEP_READY = (
    "Discuss bounded fit using only the listed material classes; do not share "
    "prohibited material."
)
NEXT_STEP_INCOMPLETE = (
    "Add or correct only the listed intake fields, then rerun decision-os "
    "intake."
)
NEXT_STEP_INVALID = (
    "Provide one local regular UTF-8 JSON packet using the accepted schema, "
    "then rerun decision-os intake."
)


class _InputRejected(Exception):
    """One local input did not satisfy the bounded read contract."""


def _safe_basename(path: Path | str | os.PathLike[str] | None) -> str:
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


def _ordered(values: Iterable[str]) -> list[str]:
    selected = set(values)
    ordered = [field for field in FIELD_ORDER if field in selected]
    if "unsupported_fields" in selected:
        ordered.append("unsupported_fields")
    return ordered


def result_payload(
    *,
    name: str,
    result: str,
    observed_fields: Iterable[str] = (),
    missing_required_fields: Iterable[str] = (),
    invalid_fields: Iterable[str] = (),
    unknowns: Iterable[str] = (),
    minimum_next_step: str,
) -> dict[str, Any]:
    """Build one stable result without including packet field contents."""

    return {
        "claims_not_made": list(CLAIMS_NOT_MADE),
        "command": "intake",
        "input": {
            "content_echoed": False,
            "name": _safe_basename(name),
        },
        "invalid_fields": _ordered(invalid_fields),
        "minimum_next_step": minimum_next_step,
        "missing_required_fields": _ordered(missing_required_fields),
        "observed_fields": _ordered(observed_fields),
        "result": result,
        "schema_version": RESULT_SCHEMA_VERSION,
        "unknowns": list(unknowns),
    }


def invalid_payload(
    path: Path | str | os.PathLike[str] | None,
    *,
    minimum_next_step: str = NEXT_STEP_INVALID,
    unknowns: Iterable[str] = ("packet_structure",),
) -> dict[str, Any]:
    """Return the stable INVALID shape for bounded read or parse rejection."""

    return result_payload(
        name=_safe_basename(path),
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


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("duplicate JSON object key")
        output[key] = value
    return output


def _reject_json_constant(_: str) -> None:
    raise ValueError("non-finite JSON constant")


def _parse_packet(content: bytes) -> dict[str, Any]:
    try:
        text = content.decode("utf-8", errors="strict")
        packet = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ):
        raise _InputRejected
    if not isinstance(packet, dict):
        raise _InputRejected
    return packet


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, *, allow_empty: bool) -> bool:
    if not isinstance(value, list):
        return False
    if not allow_empty and not value:
        return False
    return all(_nonempty_string(item) for item in value)


def _inspect_packet(
    packet: dict[str, Any],
) -> tuple[list[str], list[str], list[str], list[str]]:
    missing = [
        field for field in REQUIRED_FIELD_ORDER if field not in packet
    ]
    invalid: list[str] = []
    observed: list[str] = []

    if "schema_version" in packet:
        if packet["schema_version"] != INPUT_SCHEMA_VERSION:
            invalid.append("schema_version")
        else:
            observed.append("schema_version")

    for field in REQUIRED_STRING_FIELDS:
        if field not in packet:
            continue
        if _nonempty_string(packet[field]):
            observed.append(field)
        else:
            invalid.append(field)

    for field in REQUIRED_NONEMPTY_LIST_FIELDS:
        if field not in packet:
            continue
        if _string_list(packet[field], allow_empty=False):
            observed.append(field)
        else:
            invalid.append(field)

    for field in REQUIRED_LIST_FIELDS:
        if field not in packet:
            continue
        if _string_list(packet[field], allow_empty=True):
            observed.append(field)
        else:
            invalid.append(field)

    for field in OPTIONAL_STRING_FIELDS:
        if field not in packet:
            continue
        if _nonempty_string(packet[field]):
            observed.append(field)
        else:
            invalid.append(field)

    for field in OPTIONAL_LIST_FIELDS:
        if field not in packet:
            continue
        if _string_list(packet[field], allow_empty=True):
            observed.append(field)
        else:
            invalid.append(field)

    if any(field not in ACCEPTED_FIELDS for field in packet):
        invalid.append("unsupported_fields")

    unknowns = (
        ["input_unknowns_present"]
        if (
            "unknowns" in packet
            and isinstance(packet["unknowns"], list)
            and bool(packet["unknowns"])
        )
        else []
    )
    return (
        _ordered(observed),
        _ordered(missing),
        _ordered(invalid),
        unknowns,
    )


def validate_intake_file(path: Path) -> tuple[dict[str, Any], int]:
    """Check one local packet without writing, diagnosing, or echoing content."""

    safe_name = _safe_basename(path)
    try:
        packet = _parse_packet(_read_local_regular_file(path))
    except _InputRejected:
        return invalid_payload(path), EXIT_INCOMPLETE

    observed, missing, invalid, unknowns = _inspect_packet(packet)
    if missing or invalid:
        return (
            result_payload(
                name=safe_name,
                result=RESULT_INCOMPLETE,
                observed_fields=observed,
                missing_required_fields=missing,
                invalid_fields=invalid,
                unknowns=unknowns,
                minimum_next_step=NEXT_STEP_INCOMPLETE,
            ),
            EXIT_INCOMPLETE,
        )

    return (
        result_payload(
            name=safe_name,
            result=RESULT_READY,
            observed_fields=observed,
            unknowns=unknowns,
            minimum_next_step=NEXT_STEP_READY,
        ),
        EXIT_READY,
    )
