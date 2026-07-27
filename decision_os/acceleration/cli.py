"""Separate ``decision-os-accelerate`` command surface."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Callable, Sequence
from contextlib import redirect_stderr
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import TextIO

from .claude_adapter import (
    ADAPTER_NAME as CLAUDE_ADAPTER_NAME,
    CLAUDE_AGENT_SDK_VERSION,
    ClaudeAdapter,
    ClaudeAdapterFailure,
    ClaudeAdapterUnavailable,
    ClaudeRunResult,
)
from .codex_adapter import (
    ADAPTER_NAME as CODEX_ADAPTER_NAME,
    CODEX_CLI_VERSION,
    CodexAdapter,
    CodexAdapterFailure,
    CodexAdapterUnavailable,
    CodexRunResult,
)
from .engine import AccelerationEngine
from .store import AccelerationStore, StateIntegrityError


EXIT_OK = 0
EXIT_USAGE = 2
EXIT_STATE = 3
EXIT_DELAY = 4
EXIT_DENIED = 5

DEMO_RUN_1 = (
    "Read demo_target.txt. Use Edit exactly once to replace the line "
    "'stage: initial' with 'stage: run-1'. Do not touch any other file."
)
DEMO_RUN_2 = (
    "Read demo_target.txt. Use Edit exactly once to replace the line "
    "'stage: run-1' with 'stage: run-2'. Do not touch any other file."
)
CODEX_DEMO_RUN_1 = (
    "In demo_target.txt, the current line is 'stage: initial'. "
    "Use the typed file-change tool exactly once to replace it with "
    "'stage: run-1'. Do not use a shell command or touch any other file."
)
CODEX_DEMO_RUN_2 = (
    "In demo_target.txt, the current line is 'stage: run-1'. "
    "Use the typed file-change tool exactly once to replace it with "
    "'stage: run-2'. Do not use a shell command or touch any other file."
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="decision-os-accelerate")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run = subcommands.add_parser("run")
    run.add_argument("--adapter", choices=("claude", "codex"), required=True)
    run.add_argument("--prompt-file", type=Path, required=True)
    run.add_argument("--minutes-per-reuse", type=float, default=7.5)
    run.add_argument("--hourly-value-jpy", type=float, default=5000)
    run.add_argument("--tokens-per-reuse", type=int)
    run.add_argument("repository", type=Path)

    receipt = subcommands.add_parser("receipt")
    receipt.add_argument("repository", type=Path)

    revoke = subcommands.add_parser("revoke")
    revoke.add_argument("--decision-key", required=True)
    revoke.add_argument("repository", type=Path)

    demo = subcommands.add_parser("demo")
    demo.add_argument(
        "--adapter",
        choices=("claude", "codex"),
        required=True,
    )
    demo.add_argument("--tokens-per-reuse", type=int)
    return parser


def _settings(
    store: AccelerationStore,
    *,
    minutes_per_reuse: float,
    hourly_value_jpy: float,
    tokens_per_reuse: int | None,
) -> None:
    store.update_settings(
        minutes_per_reuse=minutes_per_reuse,
        hourly_value_jpy=hourly_value_jpy,
        tokens_per_reuse=tokens_per_reuse,
        set_tokens=tokens_per_reuse is not None,
    )


def _configured_adapter(
    repository: Path,
    adapter_name: str,
    *,
    stdout: TextIO,
    input_func: Callable[[], str],
    store: AccelerationStore | None = None,
) -> tuple[AccelerationEngine, ClaudeAdapter | CodexAdapter]:
    if adapter_name == "claude":
        engine = AccelerationEngine(
            repository,
            store=store,
            adapter=CLAUDE_ADAPTER_NAME,
            adapter_version=CLAUDE_AGENT_SDK_VERSION,
        )
        return engine, ClaudeAdapter(
            engine,
            input_func=input_func,
            stdout=stdout,
        )
    if adapter_name == "codex":
        engine = AccelerationEngine(
            repository,
            store=store,
            adapter=CODEX_ADAPTER_NAME,
            adapter_version=CODEX_CLI_VERSION,
        )
        return engine, CodexAdapter(
            engine,
            input_func=input_func,
            stdout=stdout,
        )
    raise ValueError(f"Unsupported acceleration adapter: {adapter_name}")


def _write_codex_identity(
    result: CodexRunResult,
    *,
    stdout: TextIO,
) -> None:
    identity = result.runtime_identity
    if identity is None:
        stdout.write("Codex runtime identity: UNAVAILABLE\n")
        return
    stdout.write(
        "Codex runtime identity: "
        f"model={identity.model}; "
        f"reasoning_effort={identity.reasoning_effort}; "
        f"service_tier={identity.service_tier}; "
        f"cli_version={identity.codex_cli_version}; "
        f"account_type={identity.account_type}\n"
    )


def _run_command(
    arguments: argparse.Namespace,
    *,
    stdout: TextIO,
    input_func: Callable[[], str],
) -> int:
    try:
        prompt = arguments.prompt_file.read_text(encoding="utf-8")
        store = AccelerationStore(arguments.repository)
        _settings(
            store,
            minutes_per_reuse=arguments.minutes_per_reuse,
            hourly_value_jpy=arguments.hourly_value_jpy,
            tokens_per_reuse=arguments.tokens_per_reuse,
        )
        engine, adapter = _configured_adapter(
            arguments.repository,
            arguments.adapter,
            input_func=input_func,
            stdout=stdout,
            store=store,
        )
        result = asyncio.run(adapter.run(prompt))
    except (OSError, UnicodeError, StateIntegrityError) as exc:
        stdout.write(f"BLOCK: {type(exc).__name__}\n")
        return EXIT_STATE
    except (
        ClaudeAdapterUnavailable,
        ClaudeAdapterFailure,
        CodexAdapterUnavailable,
        CodexAdapterFailure,
    ) as exc:
        stdout.write(f"DELAY: {exc}\n")
        return EXIT_DELAY

    stdout.write(
        f"Run: {result.status} / "
        f"{'normal' if result.normal_terminal else 'abnormal'} checkpoint\n"
    )
    if result.error_type:
        stdout.write(f"Adapter error type: {result.error_type}\n")
    if isinstance(result, CodexRunResult):
        _write_codex_identity(result, stdout=stdout)
    stdout.write(engine.render_receipt())
    if result.status in {"VERIFIED_SAVE", "VERIFIED_REUSE", "NORMAL_TERMINAL"}:
        return EXIT_OK
    if result.status in {"ABNORMAL_TERMINAL", "PENDING"}:
        return EXIT_DELAY
    return EXIT_DENIED


def _receipt_command(arguments: argparse.Namespace, *, stdout: TextIO) -> int:
    try:
        engine = AccelerationEngine(arguments.repository)
        stdout.write(engine.render_receipt())
    except StateIntegrityError as exc:
        stdout.write(f"BLOCK: {type(exc).__name__}\n")
        return EXIT_STATE
    return EXIT_OK


def _revoke_command(arguments: argparse.Namespace, *, stdout: TextIO) -> int:
    try:
        engine = AccelerationEngine(arguments.repository)
        status = engine.revoke(
            run_id=engine.new_run_id(),
            decision_key=arguments.decision_key,
        )
    except StateIntegrityError as exc:
        stdout.write(f"BLOCK: {type(exc).__name__}\n")
        return EXIT_STATE
    except ValueError as exc:
        stdout.write(f"DENIED: {exc}\n")
        return EXIT_DENIED
    stdout.write(f"{status}\n")
    return EXIT_OK


def _write_live_result(
    label: str,
    result: ClaudeRunResult | CodexRunResult,
    *,
    stdout: TextIO,
) -> None:
    if isinstance(result, CodexRunResult):
        identity = result.runtime_identity
        stdout.write(
            f"{label}: "
            f"status={result.status}; "
            f"turn_status={result.turn_status or 'NONE'}; "
            f"model={identity.model if identity else 'NONE'}; "
            "reasoning_effort="
            f"{identity.reasoning_effort if identity else 'NONE'}; "
            "service_tier="
            f"{identity.service_tier if identity else 'NONE'}; "
            "codex_cli_version="
            f"{identity.codex_cli_version if identity else 'NONE'}; "
            f"error_type={result.error_type or 'NONE'}\n"
        )
        return
    stdout.write(
        f"{label}: "
        f"status={result.status}; "
        f"result_subtype={result.result_subtype or 'NONE'}; "
        f"api_error_status={result.api_error_status or 'NONE'}; "
        f"stop_reason={result.stop_reason or 'NONE'}; "
        f"error_type={result.error_type or 'NONE'}\n"
    )


def _demo_command(
    arguments: argparse.Namespace,
    *,
    stdout: TextIO,
    input_func: Callable[[], str],
) -> int:
    directory = Path(tempfile.mkdtemp(prefix="decision-os-verified-save-"))
    try:
        completed = subprocess.run(
            ("git", "init", "-q", str(directory)),
            capture_output=True,
            check=False,
            text=True,
        )
        if completed.returncode != 0:
            stdout.write("BLOCK: disposable Git repository creation failed.\n")
            return EXIT_STATE
        (directory / "demo_target.txt").write_text(
            "stage: initial\n",
            encoding="utf-8",
        )
        store = AccelerationStore(directory)
        _settings(
            store,
            minutes_per_reuse=7.5,
            hourly_value_jpy=5000,
            tokens_per_reuse=arguments.tokens_per_reuse,
        )
        engine, adapter = _configured_adapter(
            directory,
            store=store,
            adapter_name=arguments.adapter,
            input_func=input_func,
            stdout=stdout,
        )
        if isinstance(adapter, ClaudeAdapter):
            first = asyncio.run(adapter.run(DEMO_RUN_1, demo=True))
        else:
            first = asyncio.run(adapter.run(CODEX_DEMO_RUN_1))
        _write_live_result("Live Run 1", first, stdout=stdout)
        default_created = any(
            event["event_type"] == "HUMAN_DEFAULT_CREATED"
            and event["run_id"] == first.run_id
            for event in store.read_events()
        )
        if not first.normal_terminal or not default_created:
            stdout.write(
                "DELAY: Run 1 did not end normally with an explicit "
                "Repository Default.\n"
            )
            return EXIT_DELAY

        if isinstance(adapter, ClaudeAdapter):
            second = asyncio.run(adapter.run(DEMO_RUN_2, demo=True))
        else:
            second = asyncio.run(adapter.run(CODEX_DEMO_RUN_2))
        _write_live_result("Live Run 2", second, stdout=stdout)
        receipt = engine.render_receipt()
        stdout.write(receipt)
        verified_saves, verified_reuses = store.counters()
        if (
            not second.normal_terminal
            or second.status != "VERIFIED_SAVE"
            or (verified_saves, verified_reuses) != (1, 1)
        ):
            stdout.write("DELAY: live two-Run proof did not verify.\n")
            return EXIT_DELAY

        receipt_path = (
            Path(tempfile.gettempdir())
            / (
                "decision-os-verified-save-receipt-"
                f"{store.chain_head()[:12]}.txt"
            )
        )
        receipt_path.write_text(receipt, encoding="utf-8")
        stdout.write(f"Sanitized receipt: {receipt_path}\n")
        return EXIT_OK
    except (
        ClaudeAdapterUnavailable,
        ClaudeAdapterFailure,
        CodexAdapterUnavailable,
        CodexAdapterFailure,
    ) as exc:
        stdout.write(f"DELAY: {exc}\n")
        return EXIT_DELAY
    except (OSError, StateIntegrityError) as exc:
        stdout.write(f"BLOCK: {type(exc).__name__}\n")
        return EXIT_STATE
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    input_func: Callable[[], str] = input,
) -> int:
    """Run the bounded acceleration CLI without disturbing ``decision-os``."""

    output = sys.stdout if stdout is None else stdout
    errors = sys.stderr if stderr is None else stderr
    try:
        with redirect_stderr(errors):
            arguments = _parser().parse_args(
                list(sys.argv[1:] if argv is None else argv)
            )
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_USAGE

    if arguments.command == "run":
        return _run_command(
            arguments,
            stdout=output,
            input_func=input_func,
        )
    if arguments.command == "receipt":
        return _receipt_command(arguments, stdout=output)
    if arguments.command == "revoke":
        return _revoke_command(arguments, stdout=output)
    if arguments.command == "demo":
        return _demo_command(
            arguments,
            stdout=output,
            input_func=input_func,
        )
    output.write("Unknown command.\n")
    return EXIT_USAGE
