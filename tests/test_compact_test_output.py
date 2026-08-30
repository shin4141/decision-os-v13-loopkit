from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "compact_test_output.py"


class CompactTestOutputTests(unittest.TestCase):
    def run_wrapped(
        self,
        directory: Path,
        source: str,
        *arguments: str,
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        log_path = directory / "full.log"
        completed = subprocess.run(
            (
                sys.executable,
                str(WRAPPER),
                "--log",
                str(log_path),
                "--",
                sys.executable,
                "-c",
                textwrap.dedent(source),
                *arguments,
            ),
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
        return completed, log_path

    def test_success_is_compact_and_complete_log_retains_both_streams(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed, log_path = self.run_wrapped(
                Path(temporary),
                """
                import sys
                print("suppressed successful stdout")
                sys.stdout.flush()
                print("retained stderr evidence", file=sys.stderr)
                print("...", file=sys.stderr)
                print("-" * 70, file=sys.stderr)
                print("Ran 3 tests in 0.125s", file=sys.stderr)
                print("", file=sys.stderr)
                print("OK", file=sys.stderr)
                """,
            )
            full_log = log_path.read_text(encoding="utf-8")

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(
            [
                "PASS: Ran 3 tests / OK / 0.125s",
                f"Full log: {log_path.resolve()}",
            ],
            completed.stdout.splitlines(),
        )
        self.assertIn("suppressed successful stdout", full_log)
        self.assertIn("retained stderr evidence", full_log)
        self.assertNotIn("suppressed successful stdout", completed.stdout)

    def test_failure_is_diagnostic_and_preserves_underlying_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed, log_path = self.run_wrapped(
                Path(temporary),
                """
                import sys
                print("unrelated successful output")
                print("=" * 70, file=sys.stderr)
                print("FAIL: test_false (example.ExampleTest.test_false)", file=sys.stderr)
                print("-" * 70, file=sys.stderr)
                print("Traceback (most recent call last):", file=sys.stderr)
                print('  File "example.py", line 7, in test_false', file=sys.stderr)
                print("AssertionError: expected true", file=sys.stderr)
                print("-" * 70, file=sys.stderr)
                print("Ran 2 tests in 0.250s", file=sys.stderr)
                print("", file=sys.stderr)
                print("FAILED (failures=1)", file=sys.stderr)
                raise SystemExit(7)
                """,
            )
            full_log = log_path.read_text(encoding="utf-8")

        self.assertEqual(7, completed.returncode)
        self.assertIn(
            "FAIL: test_false (example.ExampleTest.test_false)", completed.stdout
        )
        self.assertIn("Traceback (most recent call last):", completed.stdout)
        self.assertIn("AssertionError: expected true", completed.stdout)
        self.assertIn(
            "FAIL: Ran 2 tests / FAILED (failures=1) / 0.250s / exit 7",
            completed.stdout,
        )
        self.assertNotIn("additional identities", completed.stdout)
        self.assertNotIn("additional diagnostic sections", completed.stdout)
        self.assertIn(f"Full log: {log_path.resolve()}", completed.stdout)
        self.assertNotIn("unrelated successful output", completed.stdout)
        self.assertIn("unrelated successful output", full_log)

    def test_unknown_success_output_does_not_invent_test_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed, log_path = self.run_wrapped(
                Path(temporary),
                """
                print("custom runner completed")
                """,
            )
            full_log = log_path.read_text(encoding="utf-8")

        self.assertEqual(0, completed.returncode)
        self.assertIn("RESULT: exit 0 / unittest summary UNKNOWN", completed.stdout)
        self.assertNotIn("Ran ", completed.stdout)
        self.assertNotIn("PASS:", completed.stdout)
        self.assertEqual("custom runner completed\n", full_log)

    def test_command_and_arguments_are_executed_without_test_set_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            marker = temporary_path / "executed.json"
            expected_tests = ["test_alpha", "test_beta", "test_gamma"]
            completed, _ = self.run_wrapped(
                temporary_path,
                """
                import json
                from pathlib import Path
                import sys
                Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]), encoding="utf-8")
                print("." * len(sys.argv[2:]))
                print("-" * 70)
                print(f"Ran {len(sys.argv[2:])} tests in 0.001s")
                print("")
                print("OK")
                """,
                str(marker),
                *expected_tests,
            )

            executed = json.loads(marker.read_text(encoding="utf-8"))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(expected_tests, executed)
        self.assertIn("PASS: Ran 3 tests / OK / 0.001s", completed.stdout)


if __name__ == "__main__":
    unittest.main()
