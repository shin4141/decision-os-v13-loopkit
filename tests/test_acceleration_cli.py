from __future__ import annotations

import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from decision_os.acceleration.claude_adapter import ClaudeAdapterUnavailable
from decision_os.acceleration.cli import (
    EXIT_DELAY,
    EXIT_OK,
    EXIT_USAGE,
    main,
)
from decision_os.acceleration.engine import AccelerationEngine, DeterministicAdapter
from decision_os.acceleration.model import DecisionType


def create_repository(parent: Path) -> Path:
    repository = parent / "repo"
    repository.mkdir()
    subprocess.run(
        ("git", "init", "-q", str(repository)),
        check=True,
        capture_output=True,
    )
    (repository / "target.txt").write_text("one\n", encoding="utf-8")
    return repository


class AccelerationCliTest(unittest.TestCase):
    def test_usage_is_nonzero_without_traceback(self) -> None:
        output = io.StringIO()
        errors = io.StringIO()

        exit_code = main([], stdout=output, stderr=errors)

        self.assertEqual(EXIT_USAGE, exit_code)
        self.assertNotIn("Traceback", errors.getvalue())

    def test_help_is_a_normal_zero_exit(self) -> None:
        output = io.StringIO()

        exit_code = main(
            ["--help"],
            stdout=output,
            stderr=io.StringIO(),
        )

        self.assertEqual(EXIT_OK, exit_code)

    def test_receipt_reads_verified_state_without_exposing_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = AccelerationEngine(repository)
            adapter = DeterministicAdapter(engine)
            adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice="2",
                run_id="run-1",
            )
            adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                run_id="run-2",
            )
            output = io.StringIO()

            exit_code = main(
                ["receipt", str(repository)],
                stdout=output,
                stderr=io.StringIO(),
            )

            self.assertEqual(EXIT_OK, exit_code)
            self.assertIn("1 Save", output.getvalue())
            self.assertIn("1 Verified Reuse", output.getvalue())
            self.assertNotIn("target.txt", output.getvalue())

    def test_revoke_preserves_verified_counts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = AccelerationEngine(repository)
            adapter = DeterministicAdapter(engine)
            adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice="2",
                run_id="run-1",
            )
            verified, _ = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                run_id="run-2",
            )
            output = io.StringIO()

            exit_code = main(
                [
                    "revoke",
                    "--decision-key",
                    verified.identity.decision_key,
                    str(repository),
                ],
                stdout=output,
                stderr=io.StringIO(),
            )

            self.assertEqual(EXIT_OK, exit_code)
            self.assertIn("DEFAULT_REVOKED_AFTER_USE", output.getvalue())
            self.assertEqual((1, 1), engine.store.counters())

    def test_missing_optional_extra_returns_bounded_delay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            prompt = Path(directory) / "prompt.txt"
            prompt.write_text("edit the target", encoding="utf-8")
            output = io.StringIO()
            with patch(
                "decision_os.acceleration.cli.ClaudeAdapter._load_sdk",
                side_effect=ClaudeAdapterUnavailable("optional extra missing"),
            ):
                exit_code = main(
                    [
                        "run",
                        "--adapter",
                        "claude",
                        "--prompt-file",
                        str(prompt),
                        str(repository),
                    ],
                    stdout=output,
                    stderr=io.StringIO(),
                )

            self.assertEqual(EXIT_DELAY, exit_code)
            self.assertIn("DELAY", output.getvalue())
            self.assertIn("optional extra missing", output.getvalue())
            self.assertNotIn("Traceback", output.getvalue())


if __name__ == "__main__":
    unittest.main()
