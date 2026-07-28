"""Command-line interface for the repository-local V13 Runner."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence, TextIO

from .audit_gate import invalid_payload as audit_gate_invalid_payload
from .audit_gate import validate_audit_gate_files
from .audit_gate import validate_result_contract as validate_audit_gate_result
from .audit_gate_text import render_text as render_audit_gate_text
from .audit_link import invalid_payload as audit_link_invalid_payload
from .audit_link import validate_audit_link_files
from .audit_link_text import render_text as render_audit_link_text
from .audit_delivery import invalid_payload as audit_invalid_payload
from .audit_delivery import validate_audit_delivery_file
from .audit_delivery_text import render_text as render_audit_text
from .checks import evidence, inspect_repository, unknown_payload
from .handoff_acceptance import (
    ISSUE_CODES as HANDOFF_ACCEPTANCE_ISSUE_CODES,
    MODE_ACTIVE_TRANSFER,
    MODE_CLOSED_STATE,
    RESULT_ACCEPTABLE,
    RESULT_INVALID,
    RESULT_NOT_ACCEPTABLE,
    HandoffAssessment,
    HandoffProcessError,
    assess_handoff,
    exit_code_for_assessment,
    render_json as render_handoff_acceptance_json,
    render_text as render_handoff_acceptance_text,
)
from .intake import invalid_payload as intake_invalid_payload
from .intake import validate_intake_file
from .intake_text import render_text as render_intake_text
from .scan import failure_payload as scan_failure_payload
from .scan import scan_repository
from .scan_text import render_text


EXIT_USAGE = 2
EXIT_REPOSITORY_CONTEXT_UNAVAILABLE = 3
EXIT_INTERNAL = 6
EXIT_UNSTABLE_SNAPSHOT = 7
USAGE = "decision-os check <repository>"
SCAN_USAGE = (
    "decision-os scan <repository> | "
    "decision-os scan --format json|text <repository>"
)
INTAKE_USAGE = (
    "decision-os intake <packet.json> | "
    "decision-os intake --format json|text <packet.json>"
)
AUDIT_CHECK_USAGE = (
    "decision-os audit-check <audit.md> | "
    "decision-os audit-check --format json|text <audit.md>"
)
AUDIT_LINK_USAGE = (
    "decision-os audit-link <intake.json> <audit.md> | "
    "decision-os audit-link --format json|text <intake.json> <audit.md>"
)
AUDIT_GATE_USAGE = (
    "decision-os audit-gate <intake.json> <audit.md> | "
    "decision-os audit-gate --format json|text <intake.json> <audit.md>"
)
HANDOFF_ACCEPTANCE_PROCESS_EXITS = {
    "USAGE_ERROR": EXIT_USAGE,
    "REPOSITORY_CONTEXT_UNAVAILABLE": EXIT_REPOSITORY_CONTEXT_UNAVAILABLE,
    "INTERNAL_ERROR": EXIT_INTERNAL,
    "UNSTABLE_SNAPSHOT": EXIT_UNSTABLE_SNAPSHOT,
}
_HANDOFF_ACCEPTANCE_OPTIONS = (
    "--repo",
    "--handoff",
    "--receiver",
    "--target-layer",
    "--format",
)
_TRUSTED_SCALAR_MARKER = re.compile(
    (
        r"\b(?:NONE|UNKNOWN|TBD|MAYBE|EITHER|IF|UNLESS|WHEN|OR|"
        r"DEPENDING|CONDITIONAL|PENDING)\b"
    ),
    re.IGNORECASE,
)


def serialize(payload: dict[str, Any]) -> str:
    """Serialize one payload with stable keys and no environment-dependent data."""

    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _write(payload: dict[str, Any], stream: TextIO) -> None:
    stream.write(serialize(payload))
    stream.write("\n")


def _failure_payload(
    check: str,
    detail: Any,
) -> dict[str, Any]:
    return unknown_payload(
        evidence(
            check,
            "FAIL",
            "decision-os",
            detail,
        )
    )


def _scan_format(arguments: Sequence[str]) -> str:
    if (
        len(arguments) >= 3
        and arguments[0] == "scan"
        and arguments[1] == "--format"
        and arguments[2] == "text"
    ):
        return "text"
    return "json"


def _write_scan(
    payload: dict[str, Any],
    output_format: str,
    stream: TextIO,
) -> None:
    if output_format == "text":
        stream.write(render_text(payload))
        return
    _write(payload, stream)


def _run_scan(arguments: Sequence[str], output: TextIO) -> int:
    output_format = _scan_format(arguments)
    repository: str | None = None
    if (
        len(arguments) == 2
        and arguments[0] == "scan"
        and arguments[1]
        and not arguments[1].startswith("-")
    ):
        repository = arguments[1]
        output_format = "json"
    elif (
        len(arguments) == 4
        and arguments[0] == "scan"
        and arguments[1] == "--format"
        and arguments[2] in ("json", "text")
        and arguments[3]
    ):
        output_format = arguments[2]
        repository = arguments[3]

    if repository is None:
        payload = scan_failure_payload(
            "scan.cli.usage",
            {
                "argument_count": len(arguments),
                "usage": SCAN_USAGE,
            },
        )
        _write_scan(payload, output_format, output)
        return EXIT_USAGE

    try:
        payload, exit_code = scan_repository(Path(repository))
    except Exception as exc:
        payload = scan_failure_payload(
            "scan.internal",
            {
                "message": "unexpected bounded scan failure",
                "type": type(exc).__name__,
            },
        )
        exit_code = EXIT_INTERNAL

    _write_scan(payload, output_format, output)
    return exit_code


def _intake_format(arguments: Sequence[str]) -> str:
    if (
        len(arguments) >= 3
        and arguments[0] == "intake"
        and arguments[1] == "--format"
        and arguments[2] == "text"
    ):
        return "text"
    return "json"


def _write_intake(
    payload: dict[str, Any],
    output_format: str,
    stream: TextIO,
) -> None:
    if output_format == "text":
        stream.write(render_intake_text(payload))
        return
    _write(payload, stream)


def _run_intake(arguments: Sequence[str], output: TextIO) -> int:
    output_format = _intake_format(arguments)
    packet: str | None = None
    if (
        len(arguments) == 2
        and arguments[0] == "intake"
        and arguments[1]
        and not arguments[1].startswith("-")
    ):
        packet = arguments[1]
        output_format = "json"
    elif (
        len(arguments) == 4
        and arguments[0] == "intake"
        and arguments[1] == "--format"
        and arguments[2] in ("json", "text")
        and arguments[3]
    ):
        output_format = arguments[2]
        packet = arguments[3]

    if packet is None:
        payload = intake_invalid_payload(
            None,
            minimum_next_step=INTAKE_USAGE,
            unknowns=("cli_usage",),
        )
        _write_intake(payload, output_format, output)
        return EXIT_USAGE

    try:
        payload, exit_code = validate_intake_file(Path(packet))
    except Exception:
        payload = intake_invalid_payload(
            Path(packet),
            minimum_next_step=(
                "Retry the same local packet once; if the internal failure "
                "repeats, stop and report the command boundary."
            ),
            unknowns=("internal_failure",),
        )
        exit_code = EXIT_INTERNAL

    _write_intake(payload, output_format, output)
    return exit_code


def _audit_check_format(arguments: Sequence[str]) -> str:
    if (
        len(arguments) >= 3
        and arguments[0] == "audit-check"
        and arguments[1] == "--format"
        and arguments[2] == "text"
    ):
        return "text"
    return "json"


def _write_audit_check(
    payload: dict[str, Any],
    output_format: str,
    stream: TextIO,
) -> None:
    if output_format == "text":
        stream.write(render_audit_text(payload))
        return
    _write(payload, stream)


def _run_audit_check(arguments: Sequence[str], output: TextIO) -> int:
    output_format = _audit_check_format(arguments)
    delivery: str | None = None
    if (
        len(arguments) == 2
        and arguments[0] == "audit-check"
        and arguments[1]
        and not arguments[1].startswith("-")
    ):
        delivery = arguments[1]
        output_format = "json"
    elif (
        len(arguments) == 4
        and arguments[0] == "audit-check"
        and arguments[1] == "--format"
        and arguments[2] in ("json", "text")
        and arguments[3]
    ):
        output_format = arguments[2]
        delivery = arguments[3]

    if delivery is None:
        payload = audit_invalid_payload(
            None,
            minimum_next_step=AUDIT_CHECK_USAGE,
            unknowns=("cli_usage",),
        )
        _write_audit_check(payload, output_format, output)
        return EXIT_USAGE

    try:
        payload, exit_code = validate_audit_delivery_file(Path(delivery))
    except Exception:
        payload = audit_invalid_payload(
            Path(delivery),
            minimum_next_step=(
                "Retry the same local delivery once; if the internal failure "
                "repeats, stop and report the command boundary."
            ),
            unknowns=("internal_failure",),
        )
        exit_code = EXIT_INTERNAL

    _write_audit_check(payload, output_format, output)
    return exit_code


def _audit_link_format(arguments: Sequence[str]) -> str:
    if (
        len(arguments) >= 3
        and arguments[0] == "audit-link"
        and arguments[1] == "--format"
        and arguments[2] == "text"
    ):
        return "text"
    return "json"


def _write_audit_link(
    payload: dict[str, Any],
    output_format: str,
    stream: TextIO,
) -> None:
    if output_format == "text":
        stream.write(render_audit_link_text(payload))
        return
    _write(payload, stream)


def _run_audit_link(arguments: Sequence[str], output: TextIO) -> int:
    output_format = _audit_link_format(arguments)
    intake_path: str | None = None
    audit_path: str | None = None
    if (
        len(arguments) == 3
        and arguments[0] == "audit-link"
        and arguments[1]
        and arguments[2]
        and not arguments[1].startswith("-")
        and not arguments[2].startswith("-")
    ):
        intake_path = arguments[1]
        audit_path = arguments[2]
        output_format = "json"
    elif (
        len(arguments) == 5
        and arguments[0] == "audit-link"
        and arguments[1] == "--format"
        and arguments[2] in ("json", "text")
        and arguments[3]
        and arguments[4]
        and not arguments[3].startswith("-")
        and not arguments[4].startswith("-")
    ):
        output_format = arguments[2]
        intake_path = arguments[3]
        audit_path = arguments[4]

    if intake_path is None or audit_path is None:
        payload = audit_link_invalid_payload(
            None,
            None,
            minimum_next_step=AUDIT_LINK_USAGE,
            unknowns=("cli_usage",),
        )
        _write_audit_link(payload, output_format, output)
        return EXIT_USAGE

    try:
        payload, exit_code = validate_audit_link_files(
            Path(intake_path),
            Path(audit_path),
        )
    except Exception:
        payload = audit_link_invalid_payload(
            Path(intake_path),
            Path(audit_path),
            minimum_next_step=(
                "Retry the same two local files once; if the internal failure "
                "repeats, stop and report the command boundary."
            ),
            unknowns=("internal_failure",),
        )
        exit_code = EXIT_INTERNAL

    _write_audit_link(payload, output_format, output)
    return exit_code


def _audit_gate_format(arguments: Sequence[str]) -> str:
    if (
        len(arguments) >= 3
        and arguments[0] == "audit-gate"
        and arguments[1] == "--format"
        and arguments[2] == "text"
    ):
        return "text"
    return "json"


def _write_audit_gate(
    payload: dict[str, Any],
    output_format: str,
    stream: TextIO,
) -> None:
    if output_format == "text":
        stream.write(render_audit_gate_text(payload))
        return
    _write(payload, stream)


def _run_audit_gate(arguments: Sequence[str], output: TextIO) -> int:
    output_format = _audit_gate_format(arguments)
    intake_path: str | None = None
    audit_path: str | None = None
    if (
        len(arguments) == 3
        and arguments[0] == "audit-gate"
        and arguments[1]
        and arguments[2]
        and not arguments[1].startswith("-")
        and not arguments[2].startswith("-")
    ):
        intake_path = arguments[1]
        audit_path = arguments[2]
        output_format = "json"
    elif (
        len(arguments) == 5
        and arguments[0] == "audit-gate"
        and arguments[1] == "--format"
        and arguments[2] in ("json", "text")
        and arguments[3]
        and arguments[4]
        and not arguments[3].startswith("-")
        and not arguments[4].startswith("-")
    ):
        output_format = arguments[2]
        intake_path = arguments[3]
        audit_path = arguments[4]

    if intake_path is None or audit_path is None:
        payload = audit_gate_invalid_payload(
            None,
            None,
            minimum_next_step=AUDIT_GATE_USAGE,
            unknowns=("cli_usage",),
        )
        _write_audit_gate(payload, output_format, output)
        return EXIT_USAGE

    try:
        payload, exit_code = validate_audit_gate_files(
            Path(intake_path),
            Path(audit_path),
        )
        validate_audit_gate_result(payload, exit_code)
        _write_audit_gate(payload, output_format, output)
        return exit_code
    except Exception:
        payload = audit_gate_invalid_payload(
            Path(intake_path),
            Path(audit_path),
            minimum_next_step=(
                "Retry the same two local files once; if the internal failure "
                "repeats, stop and report the command boundary."
            ),
            unknowns=("internal_failure",),
        )
        _write_audit_gate(payload, output_format, output)
        return EXIT_INTERNAL


def _trusted_handoff_scalar(value: str) -> str | None:
    normalized = value.strip()
    if not normalized:
        return None
    if len(value.splitlines()) != 1:
        return None
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return None
    if "?" in normalized or "|" in normalized or "/" in normalized:
        return None
    if _TRUSTED_SCALAR_MARKER.search(normalized):
        return None
    return normalized


def _parse_handoff_acceptance_options(
    arguments: Sequence[str],
) -> dict[str, str] | None:
    if not arguments or arguments[0] != "handoff-accept":
        return None

    values: dict[str, str] = {}
    index = 1
    while index < len(arguments):
        option = arguments[index]
        if option not in _HANDOFF_ACCEPTANCE_OPTIONS or option in values:
            return None
        if index + 1 >= len(arguments):
            return None
        value = arguments[index + 1]
        if not value or value in _HANDOFF_ACCEPTANCE_OPTIONS:
            return None
        values[option] = value
        index += 2

    if set(values) - {"--format"} != {
        "--repo",
        "--handoff",
        "--receiver",
        "--target-layer",
    }:
        return None

    output_format = values.get("--format", "text")
    if output_format not in ("text", "json"):
        return None

    receiver = _trusted_handoff_scalar(values["--receiver"])
    target_layer = _trusted_handoff_scalar(values["--target-layer"])
    if receiver is None or target_layer is None:
        return None

    values["--receiver"] = receiver
    values["--target-layer"] = target_layer
    values["--format"] = output_format
    return values


def _write_handoff_acceptance_process_error(
    code: str,
    error: TextIO,
) -> int:
    safe_code = (
        code
        if isinstance(code, str) and code in HANDOFF_ACCEPTANCE_PROCESS_EXITS
        else "INTERNAL_ERROR"
    )
    error.write(f"HANDOFF_ACCEPTANCE_ERROR: {safe_code}\n")
    return HANDOFF_ACCEPTANCE_PROCESS_EXITS[safe_code]


def _valid_handoff_assessment(assessment: object) -> bool:
    if not isinstance(assessment, HandoffAssessment):
        return False
    if not isinstance(assessment.issue_codes, tuple):
        return False
    if any(
        not isinstance(code, str)
        or code not in HANDOFF_ACCEPTANCE_ISSUE_CODES
        for code in assessment.issue_codes
    ):
        return False
    expected_issue_order = tuple(
        code
        for code in HANDOFF_ACCEPTANCE_ISSUE_CODES
        if code in assessment.issue_codes
    )
    if assessment.issue_codes != expected_issue_order:
        return False
    if assessment.result == RESULT_ACCEPTABLE:
        return (
            assessment.mode in (MODE_ACTIVE_TRANSFER, MODE_CLOSED_STATE)
            and not assessment.issue_codes
        )
    if assessment.result in (RESULT_NOT_ACCEPTABLE, RESULT_INVALID):
        return assessment.mode is None and bool(assessment.issue_codes)
    return False


def _run_handoff_acceptance(
    arguments: Sequence[str],
    output: TextIO,
    error: TextIO,
) -> int:
    options = _parse_handoff_acceptance_options(arguments)
    if options is None:
        return _write_handoff_acceptance_process_error("USAGE_ERROR", error)

    try:
        assessment = assess_handoff(
            repo_root=Path(options["--repo"]),
            handoff_path=Path(options["--handoff"]),
            expected_receiver=options["--receiver"],
            expected_target_layer=options["--target-layer"],
        )
        if not _valid_handoff_assessment(assessment):
            raise ValueError("invalid Artifact assessment")
        exit_code = exit_code_for_assessment(assessment)
        if exit_code not in (0, 4, 5):
            raise ValueError("invalid Artifact assessment exit")
        if options["--format"] == "json":
            rendered = render_handoff_acceptance_json(assessment)
        else:
            rendered = render_handoff_acceptance_text(assessment)
        if not isinstance(rendered, str) or not rendered.endswith("\n"):
            raise ValueError("invalid Artifact assessment rendering")
    except HandoffProcessError as exc:
        return _write_handoff_acceptance_process_error(exc.code, error)
    except Exception:
        return _write_handoff_acceptance_process_error("INTERNAL_ERROR", error)

    output.write(rendered)
    return exit_code


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run one repository-local Decision-OS inspection command."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    output = sys.stdout if stdout is None else stdout
    error = sys.stderr if stderr is None else stderr

    if arguments and arguments[0] == "handoff-accept":
        return _run_handoff_acceptance(arguments, output, error)

    if arguments and arguments[0] == "scan":
        return _run_scan(arguments, output)

    if arguments and arguments[0] == "intake":
        return _run_intake(arguments, output)

    if arguments and arguments[0] == "audit-check":
        return _run_audit_check(arguments, output)

    if arguments and arguments[0] == "audit-link":
        return _run_audit_link(arguments, output)

    if arguments and arguments[0] == "audit-gate":
        return _run_audit_gate(arguments, output)

    if (
        len(arguments) != 2
        or arguments[0] != "check"
        or not arguments[1]
    ):
        _write(
            _failure_payload(
                "cli.usage",
                {
                    "arguments": arguments,
                    "usage": USAGE,
                },
            ),
            output,
        )
        return EXIT_USAGE

    try:
        payload, exit_code = inspect_repository(Path(arguments[1]))
    except Exception as exc:
        payload = _failure_payload(
            "runner.internal",
            {
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )
        exit_code = EXIT_INTERNAL

    _write(payload, output)
    return exit_code
