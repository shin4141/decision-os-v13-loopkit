"""Command-line interface for the repository-local V13 Runner."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Sequence, TextIO

from .checks import evidence, inspect_repository, unknown_payload


EXIT_USAGE = 2
EXIT_INTERNAL = 6
USAGE = "decision-os check <repository>"


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


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Run ``decision-os check <repository>`` and emit exactly one JSON object."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    output = sys.stdout if stdout is None else stdout

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
