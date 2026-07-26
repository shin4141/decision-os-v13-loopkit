"""Command-line interface for the repository-local V13 Runner."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Sequence, TextIO

from .audit_link import invalid_payload as audit_link_invalid_payload
from .audit_link import validate_audit_link_files
from .audit_link_text import render_text as render_audit_link_text
from .audit_delivery import invalid_payload as audit_invalid_payload
from .audit_delivery import validate_audit_delivery_file
from .audit_delivery_text import render_text as render_audit_text
from .checks import evidence, inspect_repository, unknown_payload
from .intake import invalid_payload as intake_invalid_payload
from .intake import validate_intake_file
from .intake_text import render_text as render_intake_text
from .scan import failure_payload as scan_failure_payload
from .scan import scan_repository
from .scan_text import render_text


EXIT_USAGE = 2
EXIT_INTERNAL = 6
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


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Run one repository-local Decision-OS inspection command."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    output = sys.stdout if stdout is None else stdout

    if arguments and arguments[0] == "scan":
        return _run_scan(arguments, output)

    if arguments and arguments[0] == "intake":
        return _run_intake(arguments, output)

    if arguments and arguments[0] == "audit-check":
        return _run_audit_check(arguments, output)

    if arguments and arguments[0] == "audit-link":
        return _run_audit_link(arguments, output)

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
