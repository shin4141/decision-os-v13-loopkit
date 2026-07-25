from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from decision_os.cli import EXIT_INTERNAL, EXIT_USAGE, main
from tests.test_decision_os_checks import create_repository, tree_digest


REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_ENTRY = REPO_ROOT / "bin" / "decision-os"
MINIMUM_FIELDS = {
    "authority_match",
    "evidence",
    "human_seat_required",
    "missing_closure",
    "next_authorized_action",
    "v12_state",
    "v13_gate",
}


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
    return json.loads(completed.stdout)


class DecisionOsCliTest(unittest.TestCase):
    def test_module_and_bin_match_from_outside_source_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_repository(parent, "complete")
            before = tree_digest(repository)

            module = run_module(parent, "check", str(repository))
            executable = run_bin(parent, "check", str(repository))

            self.assertEqual(0, module.returncode)
            self.assertEqual(module.returncode, executable.returncode)
            self.assertEqual(module.stdout, executable.stdout)
            self.assertEqual(b"", module.stderr)
            self.assertEqual(b"", executable.stderr)
            payload = decoded(module)
            self.assertTrue(MINIMUM_FIELDS.issubset(payload))
            self.assertEqual(before, tree_digest(repository))

    def test_output_is_byte_identical_across_repeated_runs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_repository(parent, "complete")

            first = run_module(parent, "check", str(repository))
            second = run_module(parent, "check", str(repository))

            self.assertEqual(0, first.returncode)
            self.assertEqual(first.stdout, second.stdout)
            self.assertTrue(first.stdout.startswith(b'{"authority_match":'))

    def test_usage_errors_return_two_and_json(self) -> None:
        cases = (
            (),
            ("inspect", "."),
            ("check",),
            ("check", ".", "extra"),
        )
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            for arguments in cases:
                with self.subTest(arguments=arguments):
                    completed = run_module(cwd, *arguments)

                    self.assertEqual(EXIT_USAGE, completed.returncode)
                    payload = decoded(completed)
                    self.assertEqual(
                        "cli.usage",
                        payload["evidence"][0]["check"],
                    )

    def test_semantic_exit_codes_are_exposed_by_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            complete_parent = parent / "complete_parent"
            missing_parent = parent / "missing_parent"
            contradictory_parent = parent / "contradictory_parent"
            for fixture_parent in (
                complete_parent,
                missing_parent,
                contradictory_parent,
            ):
                fixture_parent.mkdir()
            complete = create_repository(complete_parent, "complete")
            missing = create_repository(
                missing_parent,
                "missing_closure",
            )
            contradictory = create_repository(
                contradictory_parent,
                "contradictory",
            )
            non_git = parent / "non_git"
            non_git.mkdir()

            cases = (
                (complete, 0),
                (non_git, 3),
                (missing, 4),
                (contradictory, 5),
            )
            for repository, expected in cases:
                with self.subTest(repository=repository.name):
                    completed = run_module(parent, "check", str(repository))

                    self.assertEqual(expected, completed.returncode)
                    self.assertTrue(MINIMUM_FIELDS.issubset(decoded(completed)))

    def test_unexpected_failure_returns_six_and_json(self) -> None:
        output = io.StringIO()
        with patch(
            "decision_os.cli.inspect_repository",
            side_effect=RuntimeError("bounded test failure"),
        ):
            with redirect_stdout(output):
                exit_code = main(["check", "."])

        self.assertEqual(EXIT_INTERNAL, exit_code)
        payload = json.loads(output.getvalue())
        self.assertEqual("runner.internal", payload["evidence"][0]["check"])
        self.assertEqual("RuntimeError", payload["evidence"][0]["detail"]["type"])

    def test_current_canonical_state_is_explicit_and_read_only(
        self,
    ) -> None:
        before = tree_digest(REPO_ROOT)

        completed = run_module(REPO_ROOT.parent, "check", str(REPO_ROOT))

        self.assertEqual(0, completed.returncode)
        payload = decoded(completed)
        self.assertEqual("DELAY", payload["v12_state"])
        self.assertEqual("HOLD", payload["v13_gate"])
        required = next(
            item
            for item in payload["evidence"]
            if item["check"] == "state.required_fields"
        )
        self.assertEqual([], required["detail"]["missing"])
        self.assertEqual(before, tree_digest(REPO_ROOT))


if __name__ == "__main__":
    unittest.main()
