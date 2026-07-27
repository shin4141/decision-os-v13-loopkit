from __future__ import annotations

import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from decision_os.acceleration.claude_adapter import ClaudeAdapterUnavailable
from decision_os.acceleration.codex_adapter import (
    CODEX_CLI_VERSION,
    CODEX_MODEL,
    CODEX_REASONING_EFFORT,
    CODEX_SERVICE_TIER,
    CodexAdapterUnavailable,
    CodexRunResult,
    CodexRuntimeIdentity,
)
from decision_os.acceleration.cli import (
    CODEX_DEMO_RUN_1,
    CODEX_DEMO_RUN_2,
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

    def test_codex_run_dispatches_and_reports_machine_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            prompt = Path(directory) / "prompt.txt"
            prompt.write_text("edit the target", encoding="utf-8")
            result = CodexRunResult(
                run_id="run-1",
                normal_terminal=True,
                status="NORMAL_TERMINAL",
                error_type=None,
                turn_status="completed",
                runtime_identity=CodexRuntimeIdentity(
                    model=CODEX_MODEL,
                    reasoning_effort=CODEX_REASONING_EFFORT,
                    service_tier=CODEX_SERVICE_TIER,
                    codex_cli_version=CODEX_CLI_VERSION,
                    account_type="chatgpt",
                ),
                checkpoint_outcomes=(),
            )
            output = io.StringIO()
            run = AsyncMock(return_value=result)
            with patch(
                "decision_os.acceleration.cli.CodexAdapter.run",
                new=run,
            ):
                exit_code = main(
                    [
                        "run",
                        "--adapter",
                        "codex",
                        "--prompt-file",
                        str(prompt),
                        str(repository),
                    ],
                    stdout=output,
                    stderr=io.StringIO(),
                )

            self.assertEqual(EXIT_OK, exit_code)
            run.assert_awaited_once_with("edit the target")
            rendered = output.getvalue()
            self.assertIn("Run: NORMAL_TERMINAL", rendered)
            self.assertIn(f"model={CODEX_MODEL}", rendered)
            self.assertIn(
                f"reasoning_effort={CODEX_REASONING_EFFORT}",
                rendered,
            )
            self.assertIn(
                f"service_tier={CODEX_SERVICE_TIER}",
                rendered,
            )
            self.assertIn(
                f"cli_version={CODEX_CLI_VERSION}",
                rendered,
            )
            self.assertIn("account_type=chatgpt", rendered)

    def test_codex_unavailable_returns_bounded_delay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            prompt = Path(directory) / "prompt.txt"
            prompt.write_text("edit the target", encoding="utf-8")
            output = io.StringIO()
            with patch(
                "decision_os.acceleration.cli.CodexAdapter.run",
                new=AsyncMock(
                    side_effect=CodexAdapterUnavailable(
                        "bundled Codex unavailable"
                    )
                ),
            ):
                exit_code = main(
                    [
                        "run",
                        "--adapter",
                        "codex",
                        "--prompt-file",
                        str(prompt),
                        str(repository),
                    ],
                    stdout=output,
                    stderr=io.StringIO(),
                )

            self.assertEqual(EXIT_DELAY, exit_code)
            self.assertIn("DELAY", output.getvalue())
            self.assertIn("bundled Codex unavailable", output.getvalue())
            self.assertNotIn("Traceback", output.getvalue())

    def test_codex_pending_checkpoint_returns_delay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            prompt = Path(directory) / "prompt.txt"
            prompt.write_text("edit the target", encoding="utf-8")
            result = CodexRunResult(
                run_id="run-2",
                normal_terminal=False,
                status="PENDING",
                error_type=None,
                turn_status="failed",
                runtime_identity=CodexRuntimeIdentity(
                    model=CODEX_MODEL,
                    reasoning_effort=CODEX_REASONING_EFFORT,
                    service_tier=CODEX_SERVICE_TIER,
                    codex_cli_version=CODEX_CLI_VERSION,
                    account_type="chatgpt",
                ),
                checkpoint_outcomes=(),
            )
            with patch(
                "decision_os.acceleration.cli.CodexAdapter.run",
                new=AsyncMock(return_value=result),
            ):
                exit_code = main(
                    [
                        "run",
                        "--adapter",
                        "codex",
                        "--prompt-file",
                        str(prompt),
                        str(repository),
                    ],
                    stdout=io.StringIO(),
                    stderr=io.StringIO(),
                )

            self.assertEqual(EXIT_DELAY, exit_code)

    def test_codex_demo_choice_reaches_demo_dispatch(self) -> None:
        output = io.StringIO()
        choices = iter(("2",))
        observed_prompts: list[str] = []

        class DeterministicCodexDemoAdapter:
            def __init__(
                self,
                engine: AccelerationEngine,
                input_func,
            ) -> None:
                self.engine = engine
                self.input_func = input_func
                self.iteration = 0

            async def run(self, prompt: str) -> CodexRunResult:
                observed_prompts.append(prompt)
                self.iteration += 1
                run_id = self.engine.new_run_id()
                outcome = self.engine.evaluate(
                    run_id=run_id,
                    iteration=1,
                    decision_type=DecisionType.MODIFY_FILE,
                    requested_scope="demo_target.txt",
                    source_interrupt_id=f"item-{self.iteration}",
                    choice_provider=lambda _identity: self.input_func(),
                )
                checkpoint = self.engine.finish_checkpoint(
                    outcome,
                    normal_terminal=True,
                    checkpoint_id=f"checkpoint-{self.iteration}",
                )
                status = (
                    checkpoint.status
                    if outcome.pending_cross_run_checkpoint
                    else "NORMAL_TERMINAL"
                )
                return CodexRunResult(
                    run_id=run_id,
                    normal_terminal=True,
                    status=status,
                    error_type=None,
                    turn_status="completed",
                    runtime_identity=CodexRuntimeIdentity(
                        model=CODEX_MODEL,
                        reasoning_effort=CODEX_REASONING_EFFORT,
                        service_tier=CODEX_SERVICE_TIER,
                        codex_cli_version=CODEX_CLI_VERSION,
                        account_type="chatgpt",
                    ),
                    checkpoint_outcomes=(
                        (checkpoint,)
                        if outcome.pending_cross_run_checkpoint
                        else ()
                    ),
                )

        def configured(
            repository,
            adapter_name,
            *,
            stdout,
            input_func,
            store=None,
        ):
            del stdout
            self.assertEqual("codex", adapter_name)
            engine = AccelerationEngine(
                repository,
                store=store,
                adapter="codex-app-server",
                adapter_version=CODEX_CLI_VERSION,
            )
            return engine, DeterministicCodexDemoAdapter(
                engine,
                input_func,
            )

        with tempfile.TemporaryDirectory() as receipt_directory:
            with (
                patch(
                    "decision_os.acceleration.cli._configured_adapter",
                    side_effect=configured,
                ),
                patch(
                    "decision_os.acceleration.cli.tempfile.gettempdir",
                    return_value=receipt_directory,
                ),
            ):
                exit_code = main(
                    ["demo", "--adapter", "codex"],
                    stdout=output,
                    stderr=io.StringIO(),
                    input_func=lambda: next(choices),
                )
            receipts = list(Path(receipt_directory).glob("*.txt"))

        self.assertEqual(EXIT_OK, exit_code)
        self.assertEqual(
            [CODEX_DEMO_RUN_1, CODEX_DEMO_RUN_2],
            observed_prompts,
        )
        rendered = output.getvalue()
        self.assertIn("Live Run 1: status=NORMAL_TERMINAL", rendered)
        self.assertIn("Live Run 2: status=VERIFIED_SAVE", rendered)
        self.assertIn("1 Save", rendered)
        self.assertIn("1 Verified Reuse", rendered)
        self.assertEqual(1, len(receipts))


if __name__ == "__main__":
    unittest.main()
