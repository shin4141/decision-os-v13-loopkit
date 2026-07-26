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

from decision_os.audit_link import (
    EXIT_NOT_LINKED,
    IDENTITY_FIELDS,
    RESULT_INVALID,
    RESULT_LINKED,
    RESULT_MISMATCH,
)
from decision_os.cli import (
    AUDIT_LINK_USAGE,
    EXIT_INTERNAL,
    EXIT_USAGE,
    main,
    serialize,
)
from decision_os.audit_link_text import render_text as render_audit_link_text
from tests.test_decision_os_checks import tree_digest


REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_ENTRY = REPO_ROOT / "bin" / "decision-os"
INTAKE_EXAMPLE = REPO_ROOT / "examples" / "workflow_incident_intake_v0_1.json"
AUDIT_EXAMPLE = (
    REPO_ROOT
    / "examples"
    / "ai_application_workflow_audit_delivery_v0_1.md"
)


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


def write_pair(
    directory: Path,
    *,
    shared_workflow: str = "SECRET SHARED WORKFLOW",
) -> tuple[Path, Path]:
    packet = json.loads(INTAKE_EXAMPLE.read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise AssertionError("expected object example")
    packet["workflow"] = shared_workflow
    intake = directory / "packet.json"
    intake.write_text(
        json.dumps(packet, ensure_ascii=False),
        encoding="utf-8",
    )

    audit_content = AUDIT_EXAMPLE.read_text(encoding="utf-8").replace(
        "Application or Workflow: Customer-support approval workflow",
        f"Application or Workflow: {shared_workflow}",
        1,
    )
    audit = directory / "audit.md"
    audit.write_text(audit_content, encoding="utf-8")
    return intake, audit


class AuditCaseLinkCliTest(unittest.TestCase):
    def test_json_default_explicit_repeated_and_bin_outputs_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            before = tree_digest(root)

            default = run_module(
                root,
                "audit-link",
                str(intake),
                str(audit),
            )
            repeated = run_module(
                root,
                "audit-link",
                str(intake),
                str(audit),
            )
            explicit = run_module(
                root,
                "audit-link",
                "--format",
                "json",
                str(intake),
                str(audit),
            )
            executable = run_bin(
                root,
                "audit-link",
                str(intake),
                str(audit),
            )

            results = (default, repeated, explicit, executable)
            self.assertTrue(all(item.returncode == 0 for item in results))
            self.assertTrue(all(item.stderr == b"" for item in results))
            self.assertTrue(
                all(item.stdout == default.stdout for item in results)
            )
            payload = decoded(default)
            self.assertEqual(RESULT_LINKED, payload["result"])
            self.assertEqual(
                (serialize(payload) + "\n").encode(),
                default.stdout,
            )
            self.assertNotIn(b"SECRET SHARED WORKFLOW", default.stdout)
            self.assertEqual(before, tree_digest(root))

    def test_text_output_is_exact_repeatable_and_bin_identical(self) -> None:
        expected = (
            "Decision-OS Audit Case Link v0.1: LINKED\n"
            "\n"
            "Inputs:\n"
            "- intake: packet.json\n"
            "- audit: audit.md\n"
            "\n"
            "Matched:\n"
            "- workflow\n"
            "- bounded_path\n"
            "- trigger\n"
            "- expected_state\n"
            "- observed_state\n"
            "- restart_or_fallback_path\n"
            "\n"
            "Mismatched:\n"
            "- none\n"
            "\n"
            "Missing:\n"
            "- none\n"
            "\n"
            "Unknowns:\n"
            "- none\n"
            "\n"
            "Minimum next step:\n"
            "Use LINKED only as bounded field-continuity evidence; continue "
            "with human review of factual correctness.\n"
            "\n"
            "This result checks bounded identity continuity only.\n"
            "It does not establish factual correctness, diagnosis quality, "
            "repair efficacy, or client acceptance.\n"
        ).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)

            first = run_module(
                root,
                "audit-link",
                "--format",
                "text",
                str(intake),
                str(audit),
            )
            second = run_module(
                root,
                "audit-link",
                "--format",
                "text",
                str(intake),
                str(audit),
            )
            executable = run_bin(
                root,
                "audit-link",
                "--format",
                "text",
                str(intake),
                str(audit),
            )

            self.assertEqual(0, first.returncode)
            self.assertEqual(expected, first.stdout)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(first.stdout, executable.stdout)
            self.assertEqual(b"", first.stderr)
            self.assertNotIn(b"SECRET SHARED WORKFLOW", first.stdout)
            self.assertFalse(first.stdout.endswith(b"\n\n"))

    def test_usage_errors_return_two_in_selected_safe_format(self) -> None:
        cases = (
            (("audit-link",), b"{"),
            (("audit-link", "packet.json"), b"{"),
            (("audit-link", "packet.json", "audit.md", "extra"), b"{"),
            (("audit-link", "--format"), b"{"),
            (
                ("audit-link", "--format", "yaml", "packet.json", "audit.md"),
                b"{",
            ),
            (
                ("audit-link", "--format", "text", "packet.json"),
                b"Decision-OS Audit Case Link v0.1: INVALID\n",
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
        exit_code = main(["audit-link"], stdout=output)
        self.assertEqual(EXIT_USAGE, exit_code)
        self.assertIn(AUDIT_LINK_USAGE, output.getvalue())

    def test_mismatch_and_invalid_return_four_without_content_echo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            mismatch_content = audit.read_text(encoding="utf-8").replace(
                "Application or Workflow: SECRET SHARED WORKFLOW",
                "Application or Workflow: SECRET DIFFERENT WORKFLOW",
                1,
            )
            audit.write_text(mismatch_content, encoding="utf-8")
            mismatch = run_module(
                root,
                "audit-link",
                str(intake),
                str(audit),
            )

            malformed = root / "malformed.json"
            malformed.write_text('{"SECRET INVALID":', encoding="utf-8")
            invalid = run_module(
                root,
                "audit-link",
                str(malformed),
                str(audit),
            )

            self.assertEqual(EXIT_NOT_LINKED, mismatch.returncode)
            self.assertEqual(RESULT_MISMATCH, decoded(mismatch)["result"])
            self.assertEqual(EXIT_NOT_LINKED, invalid.returncode)
            self.assertEqual(RESULT_INVALID, decoded(invalid)["result"])
            self.assertNotIn(b"SECRET", mismatch.stdout)
            self.assertNotIn(b"SECRET", invalid.stdout)

    def test_unexpected_failure_returns_six_without_exception_detail(
        self,
    ) -> None:
        output = io.StringIO()
        with patch(
            "decision_os.cli.validate_audit_link_files",
            side_effect=RuntimeError("SECRET INTERNAL DETAIL"),
        ):
            exit_code = main(
                ["audit-link", "safe-intake.json", "safe-audit.md"],
                stdout=output,
            )

        self.assertEqual(EXIT_INTERNAL, exit_code)
        self.assertNotIn("SECRET INTERNAL DETAIL", output.getvalue())
        payload = json.loads(output.getvalue())
        self.assertEqual(RESULT_INVALID, payload["result"])
        self.assertEqual(["internal_failure"], payload["unknowns"])
        self.assertEqual(
            "safe-intake.json",
            payload["inputs"]["intake"]["name"],
        )
        self.assertEqual(
            "safe-audit.md",
            payload["inputs"]["audit"]["name"],
        )

    def test_shipped_pair_and_audit_are_independently_valid(self) -> None:
        linked = run_module(
            REPO_ROOT,
            "audit-link",
            str(INTAKE_EXAMPLE),
            str(AUDIT_EXAMPLE),
        )
        delivery = run_module(
            REPO_ROOT,
            "audit-check",
            str(AUDIT_EXAMPLE),
        )

        self.assertEqual(0, linked.returncode)
        self.assertEqual(RESULT_LINKED, decoded(linked)["result"])
        self.assertEqual(0, delivery.returncode)
        self.assertEqual("DELIVERY_READY", decoded(delivery)["result"])

    def test_existing_commands_remain_available(self) -> None:
        cases = (
            ("check", str(REPO_ROOT)),
            ("scan", str(REPO_ROOT)),
            ("intake", str(INTAKE_EXAMPLE)),
            ("audit-check", str(AUDIT_EXAMPLE)),
        )
        for command, target in cases:
            with self.subTest(command=command):
                completed = run_module(REPO_ROOT.parent, command, target)

                self.assertEqual(0, completed.returncode)
                self.assertEqual(b"", completed.stderr)
                self.assertTrue(decoded(completed))

    def test_json_field_order_is_canonical_for_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            packet = json.loads(intake.read_text(encoding="utf-8"))
            for field in reversed(IDENTITY_FIELDS):
                packet[field] = f"{packet[field]} changed"
            intake.write_text(json.dumps(packet), encoding="utf-8")

            completed = run_module(
                root,
                "audit-link",
                str(intake),
                str(audit),
            )

            self.assertEqual(EXIT_NOT_LINKED, completed.returncode)
            payload = decoded(completed)
            self.assertEqual(list(IDENTITY_FIELDS), payload["mismatched_fields"])
            self.assertEqual(
                (serialize(payload) + "\n").encode(),
                completed.stdout,
            )

    def test_text_renderer_rejects_unsafe_supplied_input_names(self) -> None:
        payload = {
            "result": RESULT_INVALID,
            "matched_fields": [],
            "mismatched_fields": [],
            "missing_fields": [],
            "unknowns": ["internal_failure"],
            "minimum_next_step": (
                "Retry the same two local files once; if the internal failure "
                "repeats, stop and report the command boundary."
            ),
            "inputs": {
                "intake": {"name": "intake\u2028forged.json"},
                "audit": {"name": "../audit.md"},
            },
        }

        rendered = render_audit_link_text(payload)

        self.assertNotIn("\u2028", rendered)
        self.assertNotIn("forged", rendered)
        self.assertNotIn("../audit.md", rendered)
        self.assertIn("- intake: unavailable", rendered)
        self.assertIn("- audit: unavailable", rendered)


if __name__ == "__main__":
    unittest.main()
