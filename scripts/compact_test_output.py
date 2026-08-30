#!/usr/bin/env python3
"""Run one command, retain its complete output, and compact unittest results."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Sequence


RUN_RE = re.compile(
    r"^Ran (?P<count>\d+) tests? in (?P<seconds>\d+(?:\.\d+)?)s\s*$",
    re.MULTILINE,
)
STATUS_RE = re.compile(
    r"^(?P<status>OK|FAILED)(?: \((?P<details>[^\n]*)\))?\s*$",
    re.MULTILINE,
)
FAILURE_HEADER_RE = re.compile(r"^(?:FAIL|ERROR): .+")
MAX_IDENTITIES = 50
MAX_CONTEXT_SECTIONS = 3
MAX_CONTEXT_LINES = 30
UNKNOWN_TAIL_LINES = 30


@dataclass(frozen=True)
class UnittestSummary:
    tests_run: int
    seconds: str
    status: str
    details: str | None

    @property
    def rendered_status(self) -> str:
        if self.details:
            return f"{self.status} ({self.details})"
        return self.status


def parse_unittest_summary(output: str) -> UnittestSummary | None:
    """Return the runner's final summary, or ``None`` for unknown output."""

    runs = list(RUN_RE.finditer(output))
    if not runs:
        return None
    run = runs[-1]
    statuses = [match for match in STATUS_RE.finditer(output, run.end())]
    if not statuses:
        return None
    status = statuses[-1]
    return UnittestSummary(
        tests_run=int(run.group("count")),
        seconds=run.group("seconds"),
        status=status.group("status"),
        details=status.group("details"),
    )


def _is_rule(line: str, character: str) -> bool:
    stripped = line.strip()
    return len(stripped) >= 20 and set(stripped) == {character}


def failure_sections(output: str) -> list[list[str]]:
    """Extract unittest FAIL/ERROR sections without unrelated success noise."""

    lines = output.splitlines()
    sections: list[list[str]] = []
    index = 0
    while index + 1 < len(lines):
        if _is_rule(lines[index], "=") and FAILURE_HEADER_RE.match(
            lines[index + 1].strip()
        ):
            end = index + 2
            while end < len(lines):
                if _is_rule(lines[end], "=") or RUN_RE.match(lines[end].strip()):
                    break
                end += 1
            sections.append(lines[index + 1 : end])
            index = end
            continue
        index += 1
    return sections


def default_log_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(".test-logs") / f"test-run-{timestamp}-{os.getpid()}.log"


def shell_exit_result(returncode: int) -> tuple[int, str]:
    """Map a subprocess result to the observable wrapper exit result."""

    if returncode >= 0:
        return returncode, f"exit {returncode}"
    signal_number = -returncode
    exit_code = 128 + signal_number
    return exit_code, f"signal {signal_number} / exit {exit_code}"


def _print_failure_diagnostics(output: str) -> None:
    sections = failure_sections(output)
    if sections:
        identities = [section[0].strip() for section in sections]
        print(f"Failure identities ({len(identities)}):")
        for identity in identities[:MAX_IDENTITIES]:
            print(identity)
        omitted = max(0, len(identities) - MAX_IDENTITIES)
        if omitted:
            print(f"... {omitted} additional identities are in the full log")

        print("Diagnostic context:")
        for section in sections[:MAX_CONTEXT_SECTIONS]:
            selected = section[:MAX_CONTEXT_LINES]
            print("\n".join(selected))
            if len(section) > MAX_CONTEXT_LINES:
                print("... context clipped; complete section is in the full log")
        remaining = max(0, len(sections) - MAX_CONTEXT_SECTIONS)
        if remaining:
            print(f"... {remaining} additional diagnostic sections are in the full log")
        return

    nonempty = [line for line in output.splitlines() if line.strip()]
    if nonempty:
        print("Diagnostic tail:")
        for line in nonempty[-UNKNOWN_TAIL_LINES:]:
            print(line)


def render_result(output: str, returncode: int, log_path: Path) -> None:
    exit_code, exit_text = shell_exit_result(returncode)
    summary = parse_unittest_summary(output)

    if returncode == 0 and summary is not None and summary.status == "OK":
        print(
            f"PASS: Ran {summary.tests_run} tests / "
            f"{summary.rendered_status} / {summary.seconds}s"
        )
    elif returncode == 0:
        print(f"RESULT: {exit_text} / unittest summary UNKNOWN")
    else:
        _print_failure_diagnostics(output)
        if summary is None:
            print(f"FAIL: unittest summary UNKNOWN / {exit_text}")
        else:
            print(
                f"FAIL: Ran {summary.tests_run} tests / "
                f"{summary.rendered_status} / {summary.seconds}s / {exit_text}"
            )

    print(f"Full log: {log_path}")


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a command unchanged, retain complete combined stdout/stderr, "
            "and compact Python unittest output."
        )
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help="full-log path (default: .test-logs/test-run-<UTC>-<pid>.log)",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args(argv)
    if arguments.command and arguments.command[0] == "--":
        arguments.command = arguments.command[1:]
    if not arguments.command:
        parser.error("a command is required after --")
    return arguments


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    log_path = (arguments.log or default_log_path()).resolve()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("wb") as full_log:
            completed = subprocess.run(
                arguments.command,
                stdout=full_log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        output = log_path.read_bytes().decode("utf-8", errors="replace")
    except OSError as exc:
        print(f"WRAPPER ERROR: {exc}", file=sys.stderr)
        print(f"Full log: {log_path}", file=sys.stderr)
        return 127

    render_result(output, completed.returncode, log_path)
    return shell_exit_result(completed.returncode)[0]


if __name__ == "__main__":
    raise SystemExit(main())
