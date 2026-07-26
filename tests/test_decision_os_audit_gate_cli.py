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

from decision_os.audit_gate import (
    CHECK_CONTINUITY,
    EXIT_NOT_READY,
    RESULT_INVALID,
    RESULT_NOT_READY,
    RESULT_READY,
    validate_audit_gate_files,
)
from decision_os.audit_gate_text import render_text as render_audit_gate_text
from decision_os.cli import (
    AUDIT_GATE_USAGE,
    EXIT_INTERNAL,
    EXIT_USAGE,
    main,
    serialize,
)
from tests.test_decision_os_audit_link import (
    example_audit,
    example_packet,
    replace_audit_field,
    write_audit,
    write_packet,
    write_pair,
)
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


class AuditGateCliTest(unittest.TestCase):
    def test_json_default_explicit_repeated_and_bin_outputs_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = example_packet()
            packet["workflow"] = "SECRET SHARED WORKFLOW"
            intake = write_packet(root, packet)
            audit = write_audit(
                root,
                replace_audit_field(
                    example_audit(),
                    "workflow",
                    "SECRET SHARED WORKFLOW",
                ),
            )
            input_before = tree_digest(root)
            runner_before = tree_digest(REPO_ROOT)

            default = run_module(
                root,
                "audit-gate",
                str(intake),
                str(audit),
            )
            repeated = run_module(
                root,
                "audit-gate",
                str(intake),
                str(audit),
            )
            explicit = run_module(
                root,
                "audit-gate",
                "--format",
                "json",
                str(intake),
                str(audit),
            )
            executable = run_bin(
                root,
                "audit-gate",
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
            self.assertEqual(RESULT_READY, payload["result"])
            self.assertEqual(
                (serialize(payload) + "\n").encode(),
                default.stdout,
            )
            self.assertNotIn(b"SECRET SHARED WORKFLOW", default.stdout)
            self.assertEqual(input_before, tree_digest(root))
            self.assertEqual(runner_before, tree_digest(REPO_ROOT))

    def test_text_output_is_exact_repeatable_and_bin_identical(self) -> None:
        expected = (
            "Decision-OS Audit Gate v0.1: HUMAN REVIEW READY\n"
            "\n"
            "Inputs:\n"
            "- intake: accepted-intake.json\n"
            "- audit: delivery.md\n"
            "\n"
            "Checks:\n"
            "- intake structure: FIT CHECK READY\n"
            "- delivery structure: DELIVERY READY\n"
            "- incident continuity: LINKED\n"
            "\n"
            "Blockers:\n"
            "- none\n"
            "\n"
            "Unknowns:\n"
            "- none\n"
            "\n"
            "Minimum next step:\n"
            "Begin bounded human review of factual correctness; do not treat "
            "structural eligibility as delivery acceptance.\n"
            "\n"
            "This result establishes structural eligibility for bounded "
            "human review only.\n"
            "It does not establish truth, diagnosis correctness, repair "
            "efficacy, client acceptance,\n"
            "paid-delivery value, prevention, recovery, safety, productivity, "
            "or revenue.\n"
        ).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)

            first = run_module(
                root,
                "audit-gate",
                "--format",
                "text",
                str(intake),
                str(audit),
            )
            second = run_module(
                root,
                "audit-gate",
                "--format",
                "text",
                str(intake),
                str(audit),
            )
            executable = run_bin(
                root,
                "audit-gate",
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
            self.assertFalse(first.stdout.endswith(b"\n\n"))

    def test_usage_errors_return_two_in_selected_safe_format(self) -> None:
        cases = (
            (("audit-gate",), b"{"),
            (("audit-gate", "packet.json"), b"{"),
            (
                ("audit-gate", "packet.json", "audit.md", "extra"),
                b"{",
            ),
            (("audit-gate", "--format"), b"{"),
            (
                (
                    "audit-gate",
                    "--format",
                    "yaml",
                    "packet.json",
                    "audit.md",
                ),
                b"{",
            ),
            (
                ("audit-gate", "--format", "text", "packet.json"),
                b"Decision-OS Audit Gate v0.1: INVALID\n",
            ),
            (
                (
                    "audit-gate",
                    "packet.json",
                    "audit.md",
                    "--format",
                    "text",
                ),
                b"{",
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
        exit_code = main(["audit-gate"], stdout=output)
        self.assertEqual(EXIT_USAGE, exit_code)
        self.assertIn(AUDIT_GATE_USAGE, output.getvalue())

    def test_not_ready_and_invalid_return_four_without_content_echo(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake = write_packet(root, example_packet())
            audit = write_audit(
                root,
                replace_audit_field(
                    example_audit(),
                    "workflow",
                    "SECRET DIFFERENT WORKFLOW",
                ),
            )
            mismatch = run_module(
                root,
                "audit-gate",
                str(intake),
                str(audit),
            )

            malformed = root / "malformed.json"
            malformed.write_text('{"SECRET INVALID":', encoding="utf-8")
            invalid = run_module(
                root,
                "audit-gate",
                str(malformed),
                str(audit),
            )

            self.assertEqual(EXIT_NOT_READY, mismatch.returncode)
            mismatch_payload = decoded(mismatch)
            self.assertEqual(RESULT_NOT_READY, mismatch_payload["result"])
            self.assertEqual(
                "MISMATCH",
                mismatch_payload["checks"][CHECK_CONTINUITY]["result"],
            )
            self.assertEqual(EXIT_NOT_READY, invalid.returncode)
            self.assertEqual(RESULT_INVALID, decoded(invalid)["result"])
            self.assertNotIn(b"SECRET", mismatch.stdout)
            self.assertNotIn(b"SECRET", invalid.stdout)

    def test_unexpected_failure_returns_six_without_exception_detail(
        self,
    ) -> None:
        output = io.StringIO()
        with patch(
            "decision_os.cli.validate_audit_gate_files",
            side_effect=RuntimeError("SECRET INTERNAL DETAIL"),
        ):
            exit_code = main(
                [
                    "audit-gate",
                    "safe-intake.json",
                    "safe-audit.md",
                ],
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

    def test_malformed_aggregate_maps_to_six_in_each_output_format(
        self,
    ) -> None:
        cases = (
            (
                [
                    "audit-gate",
                    "safe-intake.json",
                    "safe-audit.md",
                ],
                "json",
            ),
            (
                [
                    "audit-gate",
                    "--format",
                    "text",
                    "safe-intake.json",
                    "safe-audit.md",
                ],
                "text",
            ),
        )
        for arguments, output_format in cases:
            with self.subTest(output_format=output_format):
                output = io.StringIO()
                with patch(
                    "decision_os.cli.validate_audit_gate_files",
                    return_value=({"result": []}, 0),
                ):
                    exit_code = main(arguments, stdout=output)

                self.assertEqual(EXIT_INTERNAL, exit_code)
                self.assertNotIn("Traceback", output.getvalue())
                if output_format == "json":
                    payload = json.loads(output.getvalue())
                    self.assertEqual(RESULT_INVALID, payload["result"])
                    self.assertEqual(
                        ["internal_failure"],
                        payload["unknowns"],
                    )
                else:
                    self.assertTrue(
                        output.getvalue().startswith(
                            "Decision-OS Audit Gate v0.1: INVALID\n"
                        )
                    )
                    self.assertIn(
                        "- internal_failure",
                        output.getvalue(),
                    )

    def test_aggregate_extra_nested_value_is_not_serialized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            payload, semantic_exit = validate_audit_gate_files(intake, audit)
            payload["inputs"]["intake"]["secret"] = "SECRET ECHO"
            output = io.StringIO()

            with patch(
                "decision_os.cli.validate_audit_gate_files",
                return_value=(payload, semantic_exit),
            ):
                exit_code = main(
                    [
                        "audit-gate",
                        str(intake),
                        str(audit),
                    ],
                    stdout=output,
                )

            self.assertEqual(EXIT_INTERNAL, exit_code)
            self.assertNotIn("SECRET ECHO", output.getvalue())
            fallback = json.loads(output.getvalue())
            self.assertEqual(RESULT_INVALID, fallback["result"])
            self.assertEqual(["internal_failure"], fallback["unknowns"])

    def test_existing_commands_remain_available(self) -> None:
        cases = (
            ("check", str(REPO_ROOT)),
            ("scan", str(REPO_ROOT)),
            ("intake", str(INTAKE_EXAMPLE)),
            ("audit-check", str(AUDIT_EXAMPLE)),
            (
                "audit-link",
                str(INTAKE_EXAMPLE),
                str(AUDIT_EXAMPLE),
            ),
        )
        for arguments in cases:
            with self.subTest(command=arguments[0]):
                completed = run_module(REPO_ROOT.parent, *arguments)

                self.assertEqual(0, completed.returncode)
                self.assertEqual(b"", completed.stderr)
                self.assertTrue(decoded(completed))

    def test_unsafe_basenames_and_renderer_values_are_not_emitted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            unsafe_intake = root / "intake\u2028forged.json"
            unsafe_audit = root / "audit\u2029forged.md"
            unsafe_intake.write_bytes(intake.read_bytes())
            unsafe_audit.write_bytes(audit.read_bytes())

            completed = run_module(
                root,
                "audit-gate",
                str(unsafe_intake),
                str(unsafe_audit),
            )

            self.assertEqual(0, completed.returncode)
            payload = decoded(completed)
            self.assertEqual(
                "unavailable",
                payload["inputs"]["intake"]["name"],
            )
            self.assertEqual(
                "unavailable",
                payload["inputs"]["audit"]["name"],
            )
            self.assertNotIn("\u2028", completed.stdout.decode())
            self.assertNotIn("\u2029", completed.stdout.decode())

        injected = {
            "result": RESULT_INVALID,
            "checks": {
                "intake_structure": {"result": "INVALID"},
                "delivery_structure": {"result": "NOT_RUN"},
                "incident_continuity": {"result": "NOT_RUN"},
            },
            "unknowns": ["internal_failure", "SECRET UNKNOWN"],
            "minimum_next_step": "SECRET NEXT STEP",
            "inputs": {
                "intake": {"name": "intake\u2028forged.json"},
                "audit": {"name": "../SECRET-audit.md"},
            },
        }

        rendered = render_audit_gate_text(injected)

        self.assertNotIn("\u2028", rendered)
        self.assertNotIn("forged", rendered)
        self.assertNotIn("../SECRET-audit.md", rendered)
        self.assertNotIn("SECRET UNKNOWN", rendered)
        self.assertNotIn("SECRET NEXT STEP", rendered)
        self.assertIn("- intake: unavailable", rendered)
        self.assertIn("- audit: unavailable", rendered)


if __name__ == "__main__":
    unittest.main()
