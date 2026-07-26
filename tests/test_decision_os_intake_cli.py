from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from decision_os.cli import EXIT_INTERNAL, EXIT_USAGE, INTAKE_USAGE, main
from decision_os.intake import (
    EXIT_INCOMPLETE,
    INPUT_SCHEMA_VERSION,
    RESULT_INVALID,
    RESULT_READY,
)
from tests.test_decision_os_checks import tree_digest


REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_ENTRY = REPO_ROOT / "bin" / "decision-os"
SHIPPED_EXAMPLE = REPO_ROOT / "examples" / "workflow_incident_intake_v0_1.json"


def cli_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(REPO_ROOT)
    return environment


def run_module(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (sys.executable, "-B", "-m", "decision_os", *arguments),
        capture_output=True,
        check=False,
        cwd=cwd,
        env=cli_environment(),
    )


def run_bin(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (str(BIN_ENTRY), *arguments),
        capture_output=True,
        check=False,
        cwd=cwd,
        env=cli_environment(),
    )


def packet() -> dict[str, object]:
    return {
        "schema_version": INPUT_SCHEMA_VERSION,
        "workflow": "Approval workflow",
        "bounded_path": "draft -> approval -> send decision",
        "incident_as_of": "2026-07-26",
        "trigger": "Resume after interruption.",
        "expected_state": "Approved draft remains current.",
        "observed_state": "Draft identity is unavailable.",
        "human_recovery_work": ["Revalidated the draft."],
        "restart_or_fallback_path": "Stop before send.",
        "materials_available": ["Sanitized event timeline."],
        "prohibited_materials": [],
    }


def write_packet(directory: Path) -> Path:
    path = directory / "packet.json"
    path.write_text(json.dumps(packet()), encoding="utf-8")
    return path


def decoded(completed: subprocess.CompletedProcess[bytes]) -> dict[str, object]:
    if completed.stderr:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    if completed.stdout.count(b"\n") != 1 or not completed.stdout.endswith(b"\n"):
        raise AssertionError(f"expected one JSON line, got {completed.stdout!r}")
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise AssertionError("expected one JSON object")
    return payload


class WorkflowIntakeCliTest(unittest.TestCase):
    def test_shipped_example_is_fit_check_ready(self) -> None:
        completed = run_module(
            REPO_ROOT,
            "intake",
            str(SHIPPED_EXAMPLE),
        )

        self.assertEqual(0, completed.returncode)
        self.assertEqual(RESULT_READY, decoded(completed)["result"])

    def test_json_default_explicit_repeated_and_bin_outputs_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_packet(root)
            before = tree_digest(root)

            default = run_module(root, "intake", str(path))
            repeated = run_module(root, "intake", str(path))
            explicit = run_module(
                root, "intake", "--format", "json", str(path)
            )
            executable = run_bin(root, "intake", str(path))

            results = (default, repeated, explicit, executable)
            self.assertTrue(all(item.returncode == 0 for item in results))
            self.assertTrue(all(item.stderr == b"" for item in results))
            self.assertTrue(
                all(item.stdout == default.stdout for item in results)
            )
            self.assertEqual(RESULT_READY, decoded(default)["result"])
            self.assertEqual(before, tree_digest(root))

    def test_text_output_is_exact_repeatable_and_bin_identical(self) -> None:
        expected = (
            "Decision-OS Workflow Intake v0.1: FIT CHECK READY\n"
            "\n"
            "Observed:\n"
            "- workflow\n"
            "- bounded_path\n"
            "- trigger\n"
            "- expected_state\n"
            "- observed_state\n"
            "- human_recovery_work\n"
            "- restart_or_fallback_path\n"
            "- materials_available\n"
            "- prohibited_materials\n"
            "\n"
            "Missing:\n"
            "- none\n"
            "\n"
            "This result confirms intake structure only.\n"
            "It does not diagnose the workflow or accept it for a paid Audit.\n"
        ).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_packet(root)

            first = run_module(
                root, "intake", "--format", "text", str(path)
            )
            second = run_module(
                root, "intake", "--format", "text", str(path)
            )
            executable = run_bin(
                root, "intake", "--format", "text", str(path)
            )

            self.assertEqual(0, first.returncode)
            self.assertEqual(expected, first.stdout)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(first.stdout, executable.stdout)
            self.assertEqual(b"", first.stderr)
            self.assertFalse(first.stdout.endswith(b"\n\n"))

    def test_usage_errors_return_two_in_selected_safe_format(self) -> None:
        cases = (
            (("intake",), b"{"),
            (("intake", "packet.json", "extra"), b"{"),
            (("intake", "--format"), b"{"),
            (("intake", "--format", "yaml", "packet.json"), b"{"),
            (
                ("intake", "--format", "text"),
                b"Decision-OS Workflow Intake v0.1: INVALID\n",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for arguments, prefix in cases:
                with self.subTest(arguments=arguments):
                    completed = run_module(root, *arguments)
                    self.assertEqual(EXIT_USAGE, completed.returncode)
                    self.assertEqual(b"", completed.stderr)
                    self.assertTrue(completed.stdout.startswith(prefix))
                    self.assertNotIn(str(root).encode(), completed.stdout)

        output = io.StringIO()
        exit_code = main(["intake"], stdout=output)
        self.assertEqual(EXIT_USAGE, exit_code)
        self.assertIn(INTAKE_USAGE, output.getvalue())

    def test_incomplete_and_invalid_return_four_without_content_echo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incomplete_packet = packet()
            incomplete_packet["workflow"] = "SECRET VALUE"
            incomplete_packet["materials_available"] = []
            incomplete = root / "incomplete.json"
            incomplete.write_text(
                json.dumps(incomplete_packet),
                encoding="utf-8",
            )
            malformed = root / "malformed.json"
            malformed.write_text('{"SECRET VALUE":', encoding="utf-8")

            incomplete_run = run_module(root, "intake", str(incomplete))
            invalid_run = run_module(root, "intake", str(malformed))

            self.assertEqual(EXIT_INCOMPLETE, incomplete_run.returncode)
            self.assertEqual(EXIT_INCOMPLETE, invalid_run.returncode)
            self.assertNotIn(b"SECRET VALUE", incomplete_run.stdout)
            self.assertNotIn(b"SECRET VALUE", invalid_run.stdout)
            self.assertEqual(
                ["materials_available"],
                decoded(incomplete_run)["invalid_fields"],
            )
            self.assertEqual(RESULT_INVALID, decoded(invalid_run)["result"])

    def test_unexpected_failure_returns_six_without_exception_detail(self) -> None:
        output = io.StringIO()
        with patch(
            "decision_os.cli.validate_intake_file",
            side_effect=RuntimeError("SECRET INTERNAL DETAIL"),
        ):
            exit_code = main(
                ["intake", "safe-name.json"],
                stdout=output,
            )

        self.assertEqual(EXIT_INTERNAL, exit_code)
        self.assertNotIn("SECRET INTERNAL DETAIL", output.getvalue())
        payload = json.loads(output.getvalue())
        self.assertEqual(RESULT_INVALID, payload["result"])
        self.assertEqual(["internal_failure"], payload["unknowns"])
        self.assertEqual("safe-name.json", payload["input"]["name"])


if __name__ == "__main__":
    unittest.main()
