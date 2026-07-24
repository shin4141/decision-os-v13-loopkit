"""Command-line interface for the repository-local V13 Runner."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Sequence, TextIO

from .checks import evidence, inspect_repository, unknown_payload
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
