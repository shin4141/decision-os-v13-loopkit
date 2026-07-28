from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import decision_os.cli as cli
from decision_os.handoff_acceptance import (
    HandoffAssessment,
    HandoffProcessError,
    MODE_ACTIVE_TRANSFER,
    MODE_CLOSED_STATE,
    RESULT_ACCEPTABLE,
    RESULT_NOT_ACCEPTABLE,
    assess_handoff,
    render_json,
    render_text,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "handoff_acceptance_v0_2"
BIN = REPO_ROOT / "bin" / "decision-os"


def _run_git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", "-C", os.fspath(root), *arguments),
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"git failed: {arguments!r}; {completed.stderr!r}"
        )
    return completed.stdout


class HandoffAcceptanceCliV02Test(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _repo(
        self,
        fixture: str = "closed_native.md",
        *,
        branch: str = "main",
    ) -> tuple[Path, Path]:
        root = self.base / fixture.replace(".md", "")
        root.mkdir()
        _run_git(root, "init", "-b", branch)
        _run_git(root, "config", "user.name", "CLI Test")
        _run_git(root, "config", "user.email", "cli@example.invalid")
        handoff = root / "handoff.md"
        handoff.write_bytes((FIXTURES / fixture).read_bytes())
        (root / "tracked.txt").write_text("base\n", encoding="utf-8")
        _run_git(root, "add", ".")
        _run_git(root, "commit", "-m", "fixture")
        return root, handoff

    def _arguments(
        self,
        root: Path,
        handoff: Path,
        *,
        output_format: str = "text",
        canonical: str | None = "main",
    ) -> list[str]:
        arguments = [
            "handoff-accept",
            "--repo",
            os.fspath(root),
            "--handoff",
            os.fspath(handoff),
            "--receiver",
            "Codex",
            "--target-layer",
            "V13",
        ]
        if canonical is not None:
            arguments.extend(("--canonical-branch", canonical))
        if output_format != "text":
            arguments.extend(("--format", output_format))
        return arguments

    def _main(self, arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = cli.main(arguments, stdout=stdout, stderr=stderr)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def _subprocess(
        self,
        prefix: list[str],
        arguments: list[str],
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            (*prefix, *arguments),
            cwd=REPO_ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_rc_08_callable_text_json_module_bin_exit_parity(self) -> None:
        root, handoff = self._repo()
        assessment = assess_handoff(
            repo_root=root,
            handoff_path=handoff,
            expected_receiver="Codex",
            expected_target_layer="V13",
            canonical_branch="main",
        )
        self.assertEqual(
            assessment,
            HandoffAssessment(RESULT_ACCEPTABLE, MODE_CLOSED_STATE, ()),
        )

        text_arguments = self._arguments(root, handoff)
        json_arguments = self._arguments(
            root, handoff, output_format="json"
        )
        main_text = self._main(text_arguments)
        main_json = self._main(json_arguments)
        module_text = self._subprocess(
            [sys.executable, "-B", "-m", "decision_os"],
            text_arguments,
        )
        module_json = self._subprocess(
            [sys.executable, "-B", "-m", "decision_os"],
            json_arguments,
        )
        bin_text = self._subprocess([os.fspath(BIN)], text_arguments)
        bin_json = self._subprocess([os.fspath(BIN)], json_arguments)

        self.assertEqual(main_text, (0, render_text(assessment), ""))
        self.assertEqual(main_json, (0, render_json(assessment), ""))
        for completed, expected in (
            (module_text, render_text(assessment)),
            (module_json, render_json(assessment)),
            (bin_text, render_text(assessment)),
            (bin_json, render_json(assessment)),
        ):
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(completed.stdout, expected)
            self.assertEqual(completed.stderr, "")
        self.assertEqual(
            json.loads(main_json[1])["schema_version"],
            "handoff-acceptance/v0.2",
        )

    def test_rc_04_cli_carries_trusted_canonical_branch(self) -> None:
        root, handoff = self._repo()
        expected = HandoffAssessment(
            RESULT_ACCEPTABLE, MODE_CLOSED_STATE, ()
        )
        with mock.patch.object(
            cli, "assess_handoff", return_value=expected
        ) as called:
            exit_code, stdout, stderr = self._main(
                self._arguments(root, handoff)
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, render_text(expected))
        self.assertEqual(stderr, "")
        called.assert_called_once_with(
            repo_root=root,
            handoff_path=handoff,
            expected_receiver="Codex",
            expected_target_layer="V13",
            canonical_branch="main",
        )

    def test_rc_04_missing_or_invalid_canonical_is_assessment_fact(
        self,
    ) -> None:
        root, handoff = self._repo()
        for canonical in (None, "missing", "bad branch"):
            with self.subTest(canonical=canonical):
                exit_code, stdout, stderr = self._main(
                    self._arguments(
                        root, handoff, canonical=canonical
                    )
                )
                self.assertEqual(exit_code, 4)
                self.assertEqual(stderr, "")
                self.assertIn(
                    "CANONICAL_BRANCH_UNKNOWN", stdout
                )

    def test_rc_06_active_cli_is_semantic_review_not_success(self) -> None:
        root, handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        arguments = self._arguments(
            root, handoff, canonical=None
        )
        exit_code, stdout, stderr = self._main(arguments)
        self.assertEqual(exit_code, 4)
        self.assertEqual(stderr, "")
        self.assertIn(
            "HANDOFF_ACCEPTANCE: NOT_ACCEPTABLE", stdout
        )
        self.assertIn("SEMANTIC_REVIEW_REQUIRED", stdout)
        self.assertNotIn("ACTIVE_TRANSFER", stdout)

    def test_rc_08_not_acceptable_invalid_and_process_exit_matrix(
        self,
    ) -> None:
        active_root, active_handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        cases = (
            (
                self._arguments(
                    active_root, active_handoff, canonical=None
                ),
                4,
                "HANDOFF_ACCEPTANCE: NOT_ACCEPTABLE\n",
                "",
            ),
            (
                self._arguments(
                    active_root,
                    active_handoff,
                    canonical=None,
                    output_format="json",
                ),
                4,
                '"result":"NOT_ACCEPTABLE"',
                "",
            ),
            (
                self._arguments(
                    active_root,
                    active_root / "missing.md",
                    canonical=None,
                ),
                5,
                "HANDOFF_ACCEPTANCE: INVALID\n",
                "",
            ),
            (
                self._arguments(
                    active_root,
                    active_root / "missing.md",
                    canonical=None,
                    output_format="json",
                ),
                5,
                '"result":"INVALID"',
                "",
            ),
            (
                ["handoff-accept"],
                2,
                "",
                "HANDOFF_ACCEPTANCE_ERROR: USAGE_ERROR\n",
            ),
            (
                self._arguments(
                    self.base / "not-a-repository",
                    self.base / "not-a-repository" / "handoff.md",
                    canonical=None,
                ),
                3,
                "",
                "HANDOFF_ACCEPTANCE_ERROR: "
                "REPOSITORY_CONTEXT_UNAVAILABLE\n",
            ),
        )
        for arguments, expected_exit, stdout_fragment, expected_stderr in cases:
            with self.subTest(expected_exit=expected_exit):
                exit_code, stdout, stderr = self._main(arguments)
                self.assertEqual(exit_code, expected_exit)
                self.assertIn(stdout_fragment, stdout)
                self.assertEqual(stderr, expected_stderr)
                for prefix in (
                    [sys.executable, "-B", "-m", "decision_os"],
                    [os.fspath(BIN)],
                ):
                    completed = self._subprocess(prefix, arguments)
                    self.assertEqual(completed.returncode, exit_code)
                    self.assertEqual(completed.stdout, stdout)
                    self.assertEqual(completed.stderr, stderr)

    def test_rc_08_option_order_duplicates_and_usage_are_bounded(self) -> None:
        root, handoff = self._repo()
        reordered = [
            "handoff-accept",
            "--format",
            "json",
            "--canonical-branch",
            "main",
            "--target-layer",
            "V13",
            "--handoff",
            os.fspath(handoff),
            "--receiver",
            "Codex",
            "--repo",
            os.fspath(root),
        ]
        exit_code, stdout, stderr = self._main(reordered)
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout)["result"], RESULT_ACCEPTABLE)

        invalid_cases = (
            self._arguments(root, handoff) + ["--repo", os.fspath(root)],
            self._arguments(root, handoff) + ["--unknown", "value"],
            self._arguments(root, handoff) + ["--format", "yaml"],
            self._arguments(root, handoff) + ["--canonical-branch"],
            [
                item
                for item in self._arguments(root, handoff)
                if item != "--receiver"
            ],
        )
        for arguments in invalid_cases:
            with self.subTest(arguments=arguments):
                exit_code, stdout, stderr = self._main(arguments)
                self.assertEqual(exit_code, 2)
                self.assertEqual(stdout, "")
                self.assertEqual(
                    stderr,
                    "HANDOFF_ACCEPTANCE_ERROR: USAGE_ERROR\n",
                )

    def test_rc_07_cli_non_echo_and_fixed_internal_error(self) -> None:
        sentinel = "CLI_SECRET_SENTINEL_5729"
        root, handoff = self._repo()
        arguments = self._arguments(root, handoff)
        with mock.patch.object(
            cli,
            "assess_handoff",
            side_effect=RuntimeError(sentinel),
        ):
            exit_code, stdout, stderr = self._main(arguments)
        self.assertEqual(exit_code, 6)
        self.assertEqual(stdout, "")
        self.assertEqual(
            stderr, "HANDOFF_ACCEPTANCE_ERROR: INTERNAL_ERROR\n"
        )
        self.assertNotIn(sentinel, stderr)
        self.assertNotIn(os.fspath(root), stderr)
        self.assertNotIn(os.fspath(handoff), stderr)

    def test_rc_08_unstable_snapshot_is_stderr_only(self) -> None:
        root, handoff = self._repo()
        with mock.patch.object(
            cli,
            "assess_handoff",
            side_effect=HandoffProcessError("UNSTABLE_SNAPSHOT"),
        ):
            exit_code, stdout, stderr = self._main(
                self._arguments(root, handoff)
            )
        self.assertEqual(exit_code, 7)
        self.assertEqual(stdout, "")
        self.assertEqual(
            stderr,
            "HANDOFF_ACCEPTANCE_ERROR: UNSTABLE_SNAPSHOT\n",
        )

    def test_rc_06_cli_rejects_forged_active_acceptance(self) -> None:
        root, handoff = self._repo()
        forged = HandoffAssessment(
            RESULT_ACCEPTABLE, MODE_ACTIVE_TRANSFER, ()
        )
        with mock.patch.object(
            cli, "assess_handoff", return_value=forged
        ):
            exit_code, stdout, stderr = self._main(
                self._arguments(root, handoff)
            )
        self.assertEqual(exit_code, 6)
        self.assertEqual(stdout, "")
        self.assertEqual(
            stderr, "HANDOFF_ACCEPTANCE_ERROR: INTERNAL_ERROR\n"
        )

    def test_rc_07_cli_is_read_only(self) -> None:
        root, handoff = self._repo()
        before = (
            _run_git(root, "rev-parse", "HEAD"),
            _run_git(root, "show-ref"),
            _run_git(
                root,
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
            ),
            handoff.read_bytes(),
        )
        exit_code, _, stderr = self._main(
            self._arguments(root, handoff)
        )
        after = (
            _run_git(root, "rev-parse", "HEAD"),
            _run_git(root, "show-ref"),
            _run_git(
                root,
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
            ),
            handoff.read_bytes(),
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
