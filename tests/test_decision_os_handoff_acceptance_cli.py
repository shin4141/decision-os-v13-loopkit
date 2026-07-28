from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from decision_os.cli import (
    EXIT_INTERNAL,
    EXIT_REPOSITORY_CONTEXT_UNAVAILABLE,
    EXIT_UNSTABLE_SNAPSHOT,
    EXIT_USAGE,
    main,
)
from decision_os.handoff_acceptance import (
    MODE_CLOSED_STATE,
    RESULT_ACCEPTABLE,
    RESULT_INVALID,
    RESULT_NOT_ACCEPTABLE,
    HandoffAssessment,
    HandoffProcessError,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_ENTRY = REPO_ROOT / "bin" / "decision-os"
PROCESS_LINES = {
    "USAGE_ERROR": b"HANDOFF_ACCEPTANCE_ERROR: USAGE_ERROR\n",
    "REPOSITORY_CONTEXT_UNAVAILABLE": (
        b"HANDOFF_ACCEPTANCE_ERROR: REPOSITORY_CONTEXT_UNAVAILABLE\n"
    ),
    "INTERNAL_ERROR": b"HANDOFF_ACCEPTANCE_ERROR: INTERNAL_ERROR\n",
    "UNSTABLE_SNAPSHOT": (
        b"HANDOFF_ACCEPTANCE_ERROR: UNSTABLE_SNAPSHOT\n"
    ),
}


def cli_environment(
    extra_pythonpath: Path | None = None,
) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    python_paths = [str(REPO_ROOT)]
    if extra_pythonpath is not None:
        python_paths.append(str(extra_pythonpath))
    environment["PYTHONPATH"] = os.pathsep.join(python_paths)
    return environment


def run_module(
    cwd: Path,
    *arguments: str,
    extra_pythonpath: Path | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (sys.executable, "-B", "-m", "decision_os", *arguments),
        capture_output=True,
        check=False,
        cwd=cwd,
        env=cli_environment(extra_pythonpath),
    )


def run_bin(
    cwd: Path,
    *arguments: str,
    extra_pythonpath: Path | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (str(BIN_ENTRY), *arguments),
        capture_output=True,
        check=False,
        cwd=cwd,
        env=cli_environment(extra_pythonpath),
    )


def command_arguments(
    repository: str = "/safe/repository",
    handoff: str = "/safe/repository/handoff.md",
    receiver: str = "Codex",
    target_layer: str = "V13",
) -> list[str]:
    return [
        "handoff-accept",
        "--repo",
        repository,
        "--handoff",
        handoff,
        "--receiver",
        receiver,
        "--target-layer",
        target_layer,
    ]


def create_git_repository(parent: Path) -> Path:
    repository = parent / "guard-repository"
    repository.mkdir()
    commands = (
        ("git", "init", "-b", "guard-test"),
        ("git", "config", "user.name", "Decision OS Test"),
        ("git", "config", "user.email", "decision-os@example.invalid"),
        ("git", "config", "commit.gpgsign", "false"),
        (
            "git",
            "remote",
            "add",
            "origin",
            "https://github.com/example/guard-repository.git",
        ),
    )
    for command in commands:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            cwd=repository,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr.decode(errors="replace"))
    marker = repository / "tracked.txt"
    marker.write_text("guard repository\n", encoding="utf-8")
    for command in (
        ("git", "add", "tracked.txt"),
        ("git", "commit", "-m", "test fixture"),
    ):
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            cwd=repository,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr.decode(errors="replace"))
    return repository


def acceptable_closed_handoff(repository: Path) -> str:
    return (
        "# Handoff\n"
        "Target Layer: V13\n"
        f"Repository Root: {repository}\n"
        "Current State: COMPLETE\n"
        "V13 Gate: HOLD\n"
        "Active Branch: none\n"
        "Next Authorized Action: none\n"
        "Completion Line:\n"
        "MET:\n"
        "- [DONE-1] TEST; subject=handoff_guard; expected=passes\n"
        "Missing Closure: none\n"
        "Next Owner: none\n"
        "What You Own Now: none\n"
        "First One Action: none\n"
        "Do Not Continue Boundary: REQUIRE_NEW_GATE\n"
        "Work Not Returned to Decision Owner: none\n"
    )


class HandoffAcceptanceCliTest(unittest.TestCase):
    def assert_no_secret(self, *values: str | bytes) -> None:
        for value in values:
            leaked = (
                "SECRET" in value
                if isinstance(value, str)
                else b"SECRET" in value
            )
            if leaked:
                self.fail("untrusted sentinel leaked")

    def test_default_text_dispatches_exact_explicit_inputs(self) -> None:
        assessment = HandoffAssessment(
            RESULT_ACCEPTABLE,
            MODE_CLOSED_STATE,
            (),
        )
        output = io.StringIO()
        error = io.StringIO()
        arguments = command_arguments(
            receiver="  Codex  ",
            target_layer="  V13  ",
        )

        with (
            patch(
                "decision_os.cli.assess_handoff",
                return_value=assessment,
            ) as assess,
            patch(
                "decision_os.cli.exit_code_for_assessment",
                return_value=0,
            ),
            patch(
                "decision_os.cli.render_handoff_acceptance_text",
                return_value="HANDOFF_ACCEPTANCE: ACCEPTABLE\n",
            ) as render_text,
            patch(
                "decision_os.cli.render_handoff_acceptance_json",
            ) as render_json,
        ):
            exit_code = main(arguments, stdout=output, stderr=error)

        self.assertEqual(0, exit_code)
        self.assertEqual(
            "HANDOFF_ACCEPTANCE: ACCEPTABLE\n",
            output.getvalue(),
        )
        self.assertEqual("", error.getvalue())
        assess.assert_called_once_with(
            repo_root=Path("/safe/repository"),
            handoff_path=Path("/safe/repository/handoff.md"),
            expected_receiver="Codex",
            expected_target_layer="V13",
        )
        render_text.assert_called_once_with(assessment)
        render_json.assert_not_called()

    def test_json_selection_and_all_artifact_exits_remain_stdout_only(
        self,
    ) -> None:
        cases = (
            (
                HandoffAssessment(
                    RESULT_ACCEPTABLE,
                    MODE_CLOSED_STATE,
                    (),
                ),
                0,
            ),
            (
                HandoffAssessment(
                    RESULT_NOT_ACCEPTABLE,
                    None,
                    ("FIELD_UNKNOWN",),
                ),
                4,
            ),
            (
                HandoffAssessment(
                    RESULT_INVALID,
                    None,
                    ("INPUT_INVALID_UTF8",),
                ),
                5,
            ),
        )
        for assessment, semantic_exit in cases:
            with self.subTest(result=assessment.result):
                output = io.StringIO()
                error = io.StringIO()
                rendered = json.dumps({"result": assessment.result}) + "\n"
                arguments = [
                    *command_arguments(),
                    "--format",
                    "json",
                ]
                with (
                    patch(
                        "decision_os.cli.assess_handoff",
                        return_value=assessment,
                    ),
                    patch(
                        "decision_os.cli.exit_code_for_assessment",
                        return_value=semantic_exit,
                    ),
                    patch(
                        "decision_os.cli.render_handoff_acceptance_json",
                        return_value=rendered,
                    ),
                ):
                    exit_code = main(
                        arguments,
                        stdout=output,
                        stderr=error,
                    )

                self.assertEqual(semantic_exit, exit_code)
                self.assertEqual(rendered, output.getvalue())
                self.assertEqual("", error.getvalue())

    def test_usage_errors_are_fixed_stderr_only_and_never_echo_values(
        self,
    ) -> None:
        complete = command_arguments(
            repository="/SECRET_REPOSITORY",
            handoff="/SECRET_HANDOFF",
            receiver="SECRET_RECEIVER",
            target_layer="SECRET_LAYER",
        )
        cases = (
            ["handoff-accept"],
            complete[:-2],
            [*complete, "--repo", "/other"],
            [*complete, "--format"],
            [*complete, "--format", "yaml"],
            [*complete, "--unknown", "SECRET_UNKNOWN"],
            command_arguments(receiver=""),
            command_arguments(receiver="none"),
            command_arguments(receiver="UNKNOWN"),
            command_arguments(receiver="Codex\u2028forged"),
            command_arguments(receiver="Codex or Claude"),
            command_arguments(receiver="Codex / Claude"),
            command_arguments(receiver="none unless approved"),
            command_arguments(target_layer="TBD"),
            command_arguments(target_layer="V13 if approved"),
            command_arguments(target_layer="V13/V14"),
            command_arguments(target_layer="V13?"),
        )

        for case_index, arguments in enumerate(cases):
            with self.subTest(case_index=case_index):
                output = io.StringIO()
                error = io.StringIO()
                with patch("decision_os.cli.assess_handoff") as assess:
                    exit_code = main(
                        arguments,
                        stdout=output,
                        stderr=error,
                    )

                self.assert_no_secret(
                    output.getvalue(),
                    error.getvalue(),
                )
                self.assertEqual(EXIT_USAGE, exit_code)
                self.assertEqual("", output.getvalue())
                self.assertEqual(
                    PROCESS_LINES["USAGE_ERROR"].decode(),
                    error.getvalue(),
                )
                assess.assert_not_called()

    def test_typed_process_failures_use_only_fixed_codes(self) -> None:
        cases = (
            (
                "REPOSITORY_CONTEXT_UNAVAILABLE",
                EXIT_REPOSITORY_CONTEXT_UNAVAILABLE,
            ),
            ("UNSTABLE_SNAPSHOT", EXIT_UNSTABLE_SNAPSHOT),
        )
        for code, expected_exit in cases:
            with self.subTest(code=code):
                output = io.StringIO()
                error = io.StringIO()
                with patch(
                    "decision_os.cli.assess_handoff",
                    side_effect=HandoffProcessError(code),
                ):
                    exit_code = main(
                        command_arguments(),
                        stdout=output,
                        stderr=error,
                    )

                self.assertEqual(expected_exit, exit_code)
                self.assertEqual("", output.getvalue())
                self.assertEqual(
                    PROCESS_LINES[code].decode(),
                    error.getvalue(),
                )

    def test_unexpected_exception_is_internal_without_detail_echo(self) -> None:
        output = io.StringIO()
        error = io.StringIO()
        with patch(
            "decision_os.cli.assess_handoff",
            side_effect=RuntimeError("SECRET INTERNAL DETAIL"),
        ):
            exit_code = main(
                command_arguments(),
                stdout=output,
                stderr=error,
            )

        self.assertEqual(EXIT_INTERNAL, exit_code)
        self.assert_no_secret(output.getvalue(), error.getvalue())
        self.assertEqual("", output.getvalue())
        self.assertEqual(
            PROCESS_LINES["INTERNAL_ERROR"].decode(),
            error.getvalue(),
        )

    def test_invalid_renderer_contract_fails_before_stdout_write(self) -> None:
        output = io.StringIO()
        error = io.StringIO()
        with (
            patch(
                "decision_os.cli.assess_handoff",
                return_value=HandoffAssessment(
                    RESULT_ACCEPTABLE,
                    MODE_CLOSED_STATE,
                    (),
                ),
            ),
            patch(
                "decision_os.cli.exit_code_for_assessment",
                return_value=0,
            ),
            patch(
                "decision_os.cli.render_handoff_acceptance_text",
                return_value="SECRET PARTIAL WITHOUT NEWLINE",
            ),
        ):
            exit_code = main(
                command_arguments(),
                stdout=output,
                stderr=error,
            )

        self.assertEqual(EXIT_INTERNAL, exit_code)
        self.assert_no_secret(output.getvalue(), error.getvalue())
        self.assertEqual("", output.getvalue())
        self.assertEqual(
            PROCESS_LINES["INTERNAL_ERROR"].decode(),
            error.getvalue(),
        )

    def test_malformed_aggregate_is_internal_without_value_echo(self) -> None:
        cases = (
            HandoffAssessment(
                "SECRET_RESULT",
                None,
                ("FIELD_UNKNOWN",),
            ),
            HandoffAssessment(
                RESULT_NOT_ACCEPTABLE,
                None,
                ("SECRET_ISSUE",),
            ),
            HandoffAssessment(
                RESULT_ACCEPTABLE,
                MODE_CLOSED_STATE,
                ("FIELD_UNKNOWN",),
            ),
        )
        for case_index, assessment in enumerate(cases):
            with self.subTest(case_index=case_index):
                output = io.StringIO()
                error = io.StringIO()
                with (
                    patch(
                        "decision_os.cli.assess_handoff",
                        return_value=assessment,
                    ),
                    patch(
                        "decision_os.cli.render_handoff_acceptance_text",
                    ) as render,
                ):
                    exit_code = main(
                        command_arguments(),
                        stdout=output,
                        stderr=error,
                    )

                self.assertEqual(EXIT_INTERNAL, exit_code)
                self.assert_no_secret(
                    output.getvalue(),
                    error.getvalue(),
                )
                self.assertEqual("", output.getvalue())
                self.assertEqual(
                    PROCESS_LINES["INTERNAL_ERROR"].decode(),
                    error.getvalue(),
                )
                render.assert_not_called()

    def test_module_and_bin_usage_error_are_byte_identical(self) -> None:
        arguments = command_arguments(receiver="SECRET or UNKNOWN")
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            module = run_module(cwd, *arguments)
            executable = run_bin(cwd, *arguments)

        self.assertEqual(EXIT_USAGE, module.returncode)
        self.assertEqual(module.returncode, executable.returncode)
        self.assert_no_secret(
            module.stdout,
            module.stderr,
            executable.stdout,
            executable.stderr,
        )
        self.assertEqual(b"", module.stdout)
        self.assertEqual(module.stdout, executable.stdout)
        self.assertEqual(PROCESS_LINES["USAGE_ERROR"], module.stderr)
        self.assertEqual(module.stderr, executable.stderr)

    def test_module_and_bin_repository_error_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            arguments = command_arguments(
                repository=str(cwd),
                handoff=str(cwd / "SECRET_HANDOFF.md"),
            )
            module = run_module(cwd, *arguments)
            executable = run_bin(cwd, *arguments)

        self.assertEqual(
            EXIT_REPOSITORY_CONTEXT_UNAVAILABLE,
            module.returncode,
        )
        self.assertEqual(module.returncode, executable.returncode)
        self.assert_no_secret(
            module.stdout,
            module.stderr,
            executable.stdout,
            executable.stderr,
        )
        self.assertEqual(b"", module.stdout)
        self.assertEqual(module.stdout, executable.stdout)
        self.assertEqual(
            PROCESS_LINES["REPOSITORY_CONTEXT_UNAVAILABLE"],
            module.stderr,
        )
        self.assertEqual(module.stderr, executable.stderr)

    def test_module_and_bin_internal_error_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            injection = cwd / "injection"
            injection.mkdir()
            (injection / "sitecustomize.py").write_text(
                (
                    "import decision_os.cli\n"
                    "def fail_assessment(**kwargs):\n"
                    "    raise RuntimeError('SECRET_INTERNAL_SENTINEL')\n"
                    "decision_os.cli.assess_handoff = fail_assessment\n"
                ),
                encoding="utf-8",
            )
            arguments = command_arguments()
            module = run_module(
                cwd,
                *arguments,
                extra_pythonpath=injection,
            )
            executable = run_bin(
                cwd,
                *arguments,
                extra_pythonpath=injection,
            )

        self.assertEqual(EXIT_INTERNAL, module.returncode)
        self.assertEqual(module.returncode, executable.returncode)
        self.assert_no_secret(
            module.stdout,
            module.stderr,
            executable.stdout,
            executable.stderr,
        )
        self.assertEqual(b"", module.stdout)
        self.assertEqual(module.stdout, executable.stdout)
        self.assertEqual(PROCESS_LINES["INTERNAL_ERROR"], module.stderr)
        self.assertEqual(module.stderr, executable.stderr)

    def test_module_and_bin_unstable_error_are_byte_identical(self) -> None:
        real_git = shutil.which("git")
        if real_git is None:
            self.skipTest("git executable unavailable")
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_git_repository(parent)
            handoff = repository / "handoff.md"
            content = acceptable_closed_handoff(repository)
            wrapper_directory = parent / "wrapper"
            wrapper_directory.mkdir()
            wrapper = wrapper_directory / "git"
            wrapper.write_text(
                (
                    f"#!{sys.executable}\n"
                    "import os\n"
                    "from pathlib import Path\n"
                    "import sys\n"
                    "counter = Path(os.environ['HANDOFF_COUNTER'])\n"
                    "count = int(counter.read_text()) + 1\n"
                    "counter.write_text(str(count))\n"
                    "if count == 5:\n"
                    "    target = Path(os.environ['HANDOFF_MUTATE'])\n"
                    "    target.write_bytes(target.read_bytes() + b'\\n')\n"
                    "os.execv(\n"
                    "    os.environ['HANDOFF_REAL_GIT'],\n"
                    "    [os.environ['HANDOFF_REAL_GIT'], *sys.argv[1:]],\n"
                    ")\n"
                ),
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            counter = parent / "counter"
            arguments = command_arguments(
                repository=str(repository),
                handoff=str(handoff),
            )
            environment = {
                "HANDOFF_COUNTER": str(counter),
                "HANDOFF_MUTATE": str(handoff),
                "HANDOFF_REAL_GIT": real_git,
                "PATH": (
                    str(wrapper_directory)
                    + os.pathsep
                    + os.environ.get("PATH", "")
                ),
            }

            results = []
            for runner in (run_module, run_bin):
                handoff.write_text(content, encoding="utf-8")
                counter.write_text("0", encoding="ascii")
                with patch.dict(os.environ, environment):
                    results.append(runner(parent, *arguments))

        module, executable = results
        self.assertEqual(EXIT_UNSTABLE_SNAPSHOT, module.returncode)
        self.assertEqual(module.returncode, executable.returncode)
        self.assertEqual(b"", module.stdout)
        self.assertEqual(module.stdout, executable.stdout)
        self.assertEqual(
            PROCESS_LINES["UNSTABLE_SNAPSHOT"],
            module.stderr,
        )
        self.assertEqual(module.stderr, executable.stderr)

    def test_module_and_bin_cover_all_artifact_exits_in_both_formats(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_git_repository(parent)
            acceptable = repository / "acceptable.md"
            unacceptable = repository / "unacceptable.md"
            invalid = repository / "SECRET_INVALID.md"
            acceptable.write_text(
                acceptable_closed_handoff(repository),
                encoding="utf-8",
            )
            unacceptable.write_text(
                "# Handoff\nTarget Layer: V13\n",
                encoding="utf-8",
            )
            invalid.write_bytes(b"\xffSECRET INVALID BYTES")

            cases = (
                (
                    str(acceptable),
                    0,
                    "ACCEPTABLE",
                    (),
                ),
                (
                    "unacceptable.md",
                    4,
                    "NOT_ACCEPTABLE",
                    ("REQUIRED_FIELD_ABSENT",),
                ),
                (
                    str(invalid),
                    5,
                    "INVALID",
                    ("INPUT_INVALID_UTF8",),
                ),
            )
            for output_format in ("text", "json"):
                for (
                    handoff,
                    expected_exit,
                    expected_result,
                    expected_issues,
                ) in cases:
                    with self.subTest(
                        output_format=output_format,
                        expected_result=expected_result,
                    ):
                        arguments = command_arguments(
                            repository=str(repository),
                            handoff=handoff,
                        )
                        if output_format == "json":
                            arguments.extend(("--format", "json"))
                        module = run_module(parent, *arguments)
                        executable = run_bin(parent, *arguments)

                        self.assertEqual(expected_exit, module.returncode)
                        self.assert_no_secret(
                            module.stdout,
                            module.stderr,
                            executable.stdout,
                            executable.stderr,
                        )
                        self.assertEqual(
                            module.returncode,
                            executable.returncode,
                        )
                        self.assertEqual(b"", module.stderr)
                        self.assertEqual(
                            module.stderr,
                            executable.stderr,
                        )
                        self.assertEqual(
                            module.stdout,
                            executable.stdout,
                        )
                        if output_format == "json":
                            payload = json.loads(module.stdout)
                            self.assertEqual(
                                expected_result,
                                payload["result"],
                            )
                            self.assertEqual(
                                list(expected_issues),
                                payload["issue_codes"],
                            )
                        else:
                            self.assertTrue(
                                module.stdout.startswith(
                                    (
                                        "HANDOFF_ACCEPTANCE: "
                                        f"{expected_result}\n"
                                    ).encode()
                                )
                            )
                            rendered_issues = (
                                ",".join(expected_issues)
                                if expected_issues
                                else "NONE"
                            )
                            self.assertIn(
                                f"ISSUES: {rendered_issues}\n".encode(),
                                module.stdout,
                            )


if __name__ == "__main__":
    unittest.main()
