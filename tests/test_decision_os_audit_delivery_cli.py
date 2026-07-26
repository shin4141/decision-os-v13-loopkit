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

from decision_os.audit_delivery import (
    EXIT_INCOMPLETE,
    REQUIRED_SECTIONS,
    RESULT_INVALID,
    RESULT_READY,
)
from decision_os.cli import (
    AUDIT_CHECK_USAGE,
    EXIT_INTERNAL,
    EXIT_USAGE,
    main,
)
from tests.test_decision_os_checks import tree_digest


REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_ENTRY = REPO_ROOT / "bin" / "decision-os"
SHIPPED_EXAMPLE = (
    REPO_ROOT
    / "examples"
    / "ai_application_workflow_audit_delivery_v0_1.md"
)
INTAKE_EXAMPLE = REPO_ROOT / "examples" / "workflow_incident_intake_v0_1.json"


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


def decoded(completed: subprocess.CompletedProcess[bytes]) -> dict[str, object]:
    if completed.stderr:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    if completed.stdout.count(b"\n") != 1 or not completed.stdout.endswith(b"\n"):
        raise AssertionError(f"expected one JSON line, got {completed.stdout!r}")
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise AssertionError("expected one JSON object")
    return payload


def write_example(directory: Path, *, secret: bool = False) -> Path:
    content = SHIPPED_EXAMPLE.read_text(encoding="utf-8")
    if secret:
        content = content.replace(
            "Synthetic editorial approval assistant",
            "SECRET DELIVERY CONTENT",
        )
    path = directory / "audit.md"
    path.write_text(content, encoding="utf-8")
    return path


class AuditDeliveryCliTest(unittest.TestCase):
    def test_shipped_example_is_delivery_ready(self) -> None:
        completed = run_module(
            REPO_ROOT,
            "audit-check",
            str(SHIPPED_EXAMPLE),
        )

        self.assertEqual(0, completed.returncode)
        payload = decoded(completed)
        self.assertEqual(RESULT_READY, payload["result"])
        self.assertEqual(
            list(REQUIRED_SECTIONS),
            payload["observed_sections"],
        )

    def test_json_default_explicit_repeated_and_bin_outputs_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_example(root, secret=True)
            before = tree_digest(root)

            default = run_module(root, "audit-check", str(path))
            repeated = run_module(root, "audit-check", str(path))
            explicit = run_module(
                root,
                "audit-check",
                "--format",
                "json",
                str(path),
            )
            executable = run_bin(root, "audit-check", str(path))

            results = (default, repeated, explicit, executable)
            self.assertTrue(all(item.returncode == 0 for item in results))
            self.assertTrue(all(item.stderr == b"" for item in results))
            self.assertTrue(
                all(item.stdout == default.stdout for item in results)
            )
            self.assertEqual(RESULT_READY, decoded(default)["result"])
            self.assertNotIn(b"SECRET DELIVERY CONTENT", default.stdout)
            self.assertEqual(before, tree_digest(root))

    def test_text_output_is_exact_repeatable_and_bin_identical(self) -> None:
        expected = (
            "Decision-OS Audit Delivery v0.1: DELIVERY READY\n"
            "\n"
            "Profile:\n"
            "- AI_APPLICATION_WORKFLOW\n"
            "\n"
            "Observed sections:\n"
            "- Scope\n"
            "- Source Materials\n"
            "- Incident As-of State\n"
            "- Friction Map\n"
            "- Restartability Diagnosis\n"
            "- Priority Fix\n"
            "- Operational Asset\n"
            "- Before / After Restart Check\n"
            "- Unknowns\n"
            "- Exclusions\n"
            "- Claim Boundary\n"
            "- Completion Line\n"
            "\n"
            "Missing:\n"
            "- none\n"
            "\n"
            "Invalid:\n"
            "- none\n"
            "\n"
            "This result confirms delivery structure only.\n"
            "It does not validate diagnosis truth, repair efficacy, "
            "or client acceptance.\n"
        ).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_example(root)

            first = run_module(
                root,
                "audit-check",
                "--format",
                "text",
                str(path),
            )
            second = run_module(
                root,
                "audit-check",
                "--format",
                "text",
                str(path),
            )
            executable = run_bin(
                root,
                "audit-check",
                "--format",
                "text",
                str(path),
            )

            self.assertEqual(0, first.returncode)
            self.assertEqual(expected, first.stdout)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(first.stdout, executable.stdout)
            self.assertEqual(b"", first.stderr)
            self.assertFalse(first.stdout.endswith(b"\n\n"))

    def test_usage_errors_return_two_in_selected_safe_format(self) -> None:
        cases = (
            (("audit-check",), b"{"),
            (("audit-check", "audit.md", "extra"), b"{"),
            (("audit-check", "--format"), b"{"),
            (("audit-check", "--format", "yaml", "audit.md"), b"{"),
            (
                ("audit-check", "--format", "text"),
                b"Decision-OS Audit Delivery v0.1: INVALID\n",
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
        exit_code = main(["audit-check"], stdout=output)
        self.assertEqual(EXIT_USAGE, exit_code)
        self.assertIn(AUDIT_CHECK_USAGE, output.getvalue())

    def test_incomplete_and_invalid_return_four_without_content_echo(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incomplete = write_example(root, secret=True)
            incomplete.write_text(
                incomplete.read_text(encoding="utf-8").replace(
                    "## Completion Line",
                    "## SECRET CLOSURE",
                    1,
                ),
                encoding="utf-8",
            )
            malformed = root / "malformed.md"
            malformed.write_text(
                "# SECRET TITLE\n\n```text\nSECRET VALUE\n",
                encoding="utf-8",
            )

            incomplete_run = run_module(
                root,
                "audit-check",
                str(incomplete),
            )
            invalid_run = run_module(
                root,
                "audit-check",
                str(malformed),
            )

            self.assertEqual(EXIT_INCOMPLETE, incomplete_run.returncode)
            self.assertEqual(EXIT_INCOMPLETE, invalid_run.returncode)
            self.assertNotIn(b"SECRET", incomplete_run.stdout)
            self.assertNotIn(b"SECRET", invalid_run.stdout)
            self.assertEqual(
                RESULT_INVALID,
                decoded(invalid_run)["result"],
            )

    def test_unexpected_failure_returns_six_without_exception_detail(
        self,
    ) -> None:
        output = io.StringIO()
        with patch(
            "decision_os.cli.validate_audit_delivery_file",
            side_effect=RuntimeError("SECRET INTERNAL DETAIL"),
        ):
            exit_code = main(
                ["audit-check", "safe-name.md"],
                stdout=output,
            )

        self.assertEqual(EXIT_INTERNAL, exit_code)
        self.assertNotIn("SECRET INTERNAL DETAIL", output.getvalue())
        payload = json.loads(output.getvalue())
        self.assertEqual(RESULT_INVALID, payload["result"])
        self.assertEqual(["internal_failure"], payload["unknowns"])
        self.assertEqual("safe-name.md", payload["input"]["name"])

    def test_existing_check_scan_and_intake_dispatch_remain_available(
        self,
    ) -> None:
        cases = (
            ("check", str(REPO_ROOT)),
            ("scan", str(REPO_ROOT)),
            ("intake", str(INTAKE_EXAMPLE)),
        )
        for command, target in cases:
            with self.subTest(command=command):
                completed = run_module(REPO_ROOT.parent, command, target)

                self.assertEqual(0, completed.returncode)
                self.assertEqual(b"", completed.stderr)
                self.assertTrue(decoded(completed))


if __name__ == "__main__":
    unittest.main()
