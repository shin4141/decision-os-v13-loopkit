from __future__ import annotations

from copy import deepcopy
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from decision_os.cli import EXIT_INTERNAL, EXIT_USAGE, main
from decision_os.scan import (
    EXIT_NOT_GIT,
    EXIT_UNSTABLE,
    failure_payload as scan_failure_payload,
    scan_repository,
)
from decision_os.scan_text import render_text
from tests.test_decision_os_checks import (
    create_repository as create_v13_repository,
    tree_digest,
)
from tests.test_decision_os_scan import create_unmanaged_repository


REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_ENTRY = REPO_ROOT / "bin" / "decision-os"
CANONICAL_AS_OF = "57dc2d1f557aabf40b18c09313fabcb5b6dc96f8"

CHECK_FIELDS = {
    "authority_match",
    "evidence",
    "human_seat_required",
    "missing_closure",
    "next_authorized_action",
    "v12_state",
    "v13_gate",
}

PROTECTED_BLOBS = {
    "bin/decision-os": ("100755", "07b5cd88453ec679afcc7c0b84cfc7fd50694c79"),
    "decision_os/__init__.py": (
        "100644",
        "b6efd44beec1bbbf2bad47fb225081ad861c08d9",
    ),
    "decision_os/__main__.py": (
        "100644",
        "704bce80052b7adb0975c22b4424a60f7fece5fb",
    ),
    "decision_os/checks.py": (
        "100644",
        "fa304eb1361e09c0ee7213aa3a6899ec867507a6",
    ),
    "decision_os/state.py": (
        "100644",
        "e072baf3bc0a21c507ae9c5def795c939ad68591",
    ),
    "docs/v13_runner_v0_1.md": (
        "100644",
        "45deb95d32a832d9a8059951f04d895db906201e",
    ),
    "tests/fixtures/v13_runner_v0_1/complete/docs/current_signal.md": (
        "100644",
        "50e127f53b4eda56cb6730f6a99f12badd03fd4b",
    ),
    (
        "tests/fixtures/v13_runner_v0_1/complete/"
        "handoff/current_codex_handoff.md"
    ): (
        "100644",
        "070f5630efa57595f87e8007155435b9b5539d09",
    ),
    "tests/fixtures/v13_runner_v0_1/contradictory/docs/current_signal.md": (
        "100644",
        "73f3883372b7202249816bc70a5627de864948f2",
    ),
    (
        "tests/fixtures/v13_runner_v0_1/contradictory/"
        "handoff/current_codex_handoff.md"
    ): (
        "100644",
        "c034705317cbe5b20760571d3f08ab28ec7a6749",
    ),
    "tests/fixtures/v13_runner_v0_1/missing_closure/docs/current_signal.md": (
        "100644",
        "1c585ebadc8ef48820ddb26f5f8ce1abcf253d75",
    ),
    (
        "tests/fixtures/v13_runner_v0_1/missing_closure/"
        "handoff/current_codex_handoff.md"
    ): (
        "100644",
        "0151506a999d19e5bdc2a535771ab9345d9d3872",
    ),
    "tests/test_decision_os_checks.py": (
        "100644",
        "e04f8e85fd2297e6c8a9d2b4711f13c97b6c67b2",
    ),
    "tests/test_decision_os_cli.py": (
        "100644",
        "bafbb8d484995fcf0d4ba3af6968e6c0efb49633",
    ),
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


def decoded_json(
    completed: subprocess.CompletedProcess[bytes],
) -> dict[str, object]:
    if completed.stderr:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    if completed.stdout.count(b"\n") != 1 or not completed.stdout.endswith(b"\n"):
        raise AssertionError(
            f"expected exactly one JSON line, got {completed.stdout!r}"
        )
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise AssertionError("JSON output is not an object")
    return payload


def direct_scan(
    arguments: list[str],
) -> tuple[int, str]:
    output = io.StringIO()
    exit_code = main(arguments, stdout=output)
    return exit_code, output.getvalue()


class ScanTextRendererTest(unittest.TestCase):
    def test_renderer_is_payload_only_terminal_safe_and_has_no_url(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(
                Path(directory), "multiple_instructions"
            )
            payload, _ = scan_repository(repository)
            adversarial = deepcopy(payload)
            adversarial["repository"]["root_name"] = (
                "/private/tmp/secret\x1b[31m\udcff"
            )
            adversarial["recommendation"]["minimum_next_step"] = (
                "Click https://example.invalid/private"
            )
            adversarial["unknowns"][0]["reason"] = (
                "Open https://example.invalid/private"
            )
            adversarial["evidence"][0]["source"] = "/private/tmp/source"

            with patch(
                "decision_os.scan.scan_repository",
                side_effect=AssertionError("renderer performed a second scan"),
            ):
                first = render_text(adversarial)
                second = render_text(adversarial)

            self.assertEqual(first, second)
            first.encode("utf-8", errors="strict")
            self.assertTrue(first.endswith("\n"))
            self.assertFalse(first.endswith("\n\n"))
            self.assertNotIn("\x1b", first)
            self.assertNotIn("\udcff", first)
            self.assertNotIn("/private/tmp", first)
            self.assertNotIn("http://", first)
            self.assertNotIn("https://", first)
            self.assertNotIn("Click ", first)


class DecisionOsScanCliTest(unittest.TestCase):
    def test_default_and_explicit_json_are_byte_identical_with_module_bin_parity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_unmanaged_repository(
                parent, "one_instruction"
            )
            target = str(repository)

            module_first = run_module(parent, "scan", target)
            module_second = run_module(parent, "scan", target)
            module_explicit = run_module(
                parent, "scan", "--format", "json", target
            )
            bin_default = run_bin(parent, "scan", target)
            bin_explicit = run_bin(
                parent, "scan", "--format", "json", target
            )

            results = (
                module_first,
                module_second,
                module_explicit,
                bin_default,
                bin_explicit,
            )
            self.assertTrue(all(result.returncode == 0 for result in results))
            self.assertTrue(all(result.stderr == b"" for result in results))
            self.assertTrue(
                all(result.stdout == module_first.stdout for result in results)
            )
            payload = decoded_json(module_first)
            self.assertEqual("decision-os.scan.v0.2", payload["schema_version"])
            self.assertEqual("scan", payload["command"])

    def test_explicit_text_is_repeatable_with_module_bin_parity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_unmanaged_repository(
                parent, "multiple_instructions"
            )
            target = str(repository)

            module_first = run_module(
                parent, "scan", "--format", "text", target
            )
            module_second = run_module(
                parent, "scan", "--format", "text", target
            )
            executable = run_bin(
                parent, "scan", "--format", "text", target
            )

            self.assertEqual(0, module_first.returncode)
            self.assertEqual(module_first.returncode, module_second.returncode)
            self.assertEqual(module_first.returncode, executable.returncode)
            self.assertEqual(module_first.stdout, module_second.stdout)
            self.assertEqual(module_first.stdout, executable.stdout)
            self.assertEqual(b"", module_first.stderr)
            self.assertEqual(b"", executable.stderr)
            self.assertTrue(
                module_first.stdout.startswith(b"Decision-OS Scan v0.2: ")
            )
            self.assertTrue(module_first.stdout.endswith(b"\n"))
            self.assertFalse(module_first.stdout.endswith(b"\n\n"))
            self.assertNotIn(str(parent).encode("utf-8"), module_first.stdout)
            self.assertNotIn(b"\x1b", module_first.stdout)
            self.assertNotIn(b"http://", module_first.stdout)
            self.assertNotIn(b"https://", module_first.stdout)

    def test_scan_usage_errors_return_two_and_never_check_codes(self) -> None:
        cases = (
            ("scan",),
            ("scan", ".", "extra"),
            ("scan", "--format"),
            ("scan", "--format", "text"),
            ("scan", "--format", "yaml", "."),
            ("scan", ".", "--format", "text"),
        )
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            observed_codes: list[int] = []
            for arguments in cases:
                with self.subTest(arguments=arguments):
                    completed = run_module(cwd, *arguments)
                    observed_codes.append(completed.returncode)
                    self.assertEqual(EXIT_USAGE, completed.returncode)
                    self.assertEqual(b"", completed.stderr)
                    if arguments != ("scan", "--format", "text"):
                        payload = decoded_json(completed)
                        self.assertEqual("FAILED", payload["scan_completion"])
            self.assertNotIn(4, observed_codes)
            self.assertNotIn(5, observed_codes)

    def test_scan_non_git_is_three_and_never_check_codes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            completed = run_module(Path(directory), "scan", directory)

            self.assertEqual(EXIT_NOT_GIT, completed.returncode)
            self.assertNotIn(completed.returncode, (4, 5))
            payload = decoded_json(completed)
            self.assertEqual("FAILED", payload["scan_completion"])
            self.assertEqual("UNDETERMINED", payload["mode"])

    def test_scan_internal_and_unstable_exits_are_serialized(self) -> None:
        with patch(
            "decision_os.cli.scan_repository",
            side_effect=RuntimeError("bounded fixture failure"),
        ):
            internal_code, internal_output = direct_scan(["scan", "."])

        self.assertEqual(EXIT_INTERNAL, internal_code)
        self.assertNotIn(internal_code, (4, 5))
        internal_payload = json.loads(internal_output)
        self.assertEqual("FAILED", internal_payload["scan_completion"])
        self.assertEqual(
            "scan.internal", internal_payload["evidence"][0]["check"]
        )
        self.assertNotIn("bounded fixture failure", internal_output)

        unstable = scan_failure_payload(
            "scan.snapshot",
            {"changed": ["head"]},
            status="CONTRADICTORY",
        )
        with patch(
            "decision_os.cli.scan_repository",
            return_value=(unstable, EXIT_UNSTABLE),
        ):
            unstable_code, unstable_output = direct_scan(["scan", "."])

        self.assertEqual(EXIT_UNSTABLE, unstable_code)
        self.assertNotIn(unstable_code, (4, 5))
        unstable_payload = json.loads(unstable_output)
        self.assertEqual(
            "CONTRADICTORY", unstable_payload["evidence"][0]["status"]
        )

    def test_scan_text_failure_preserves_selected_format(self) -> None:
        unstable = scan_failure_payload(
            "scan.snapshot",
            {"changed": ["worktree"]},
            status="CONTRADICTORY",
        )
        with patch(
            "decision_os.cli.scan_repository",
            return_value=(unstable, EXIT_UNSTABLE),
        ):
            exit_code, output = direct_scan(
                ["scan", "--format", "text", "."]
            )

        self.assertEqual(EXIT_UNSTABLE, exit_code)
        self.assertTrue(output.startswith("Decision-OS Scan v0.2: FAILED\n"))
        self.assertTrue(output.endswith("\n"))
        self.assertFalse(output.endswith("\n\n"))

    def test_existing_check_contract_and_exit_codes_are_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            complete_parent = parent / "complete"
            missing_parent = parent / "missing"
            contradictory_parent = parent / "contradictory"
            for fixture_parent in (
                complete_parent,
                missing_parent,
                contradictory_parent,
            ):
                fixture_parent.mkdir()
            complete = create_v13_repository(complete_parent, "complete")
            missing = create_v13_repository(
                missing_parent, "missing_closure"
            )
            contradictory = create_v13_repository(
                contradictory_parent, "contradictory"
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
                with self.subTest(expected=expected):
                    module = run_module(
                        parent, "check", str(repository)
                    )
                    executable = run_bin(
                        parent, "check", str(repository)
                    )
                    self.assertEqual(expected, module.returncode)
                    self.assertEqual(module.returncode, executable.returncode)
                    self.assertEqual(module.stdout, executable.stdout)
                    payload = decoded_json(module)
                    self.assertEqual(CHECK_FIELDS, set(payload))
                    for item in payload["evidence"]:
                        self.assertEqual(
                            {"check", "detail", "source", "status"},
                            set(item),
                        )

    def test_existing_check_usage_payload_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            completed = run_module(Path(directory), "check")

        self.assertEqual(EXIT_USAGE, completed.returncode)
        payload = decoded_json(completed)
        self.assertEqual(CHECK_FIELDS, set(payload))
        self.assertEqual(
            {
                "arguments": ["check"],
                "usage": "decision-os check <repository>",
            },
            payload["evidence"][0]["detail"],
        )
        self.assertEqual("cli.usage", payload["evidence"][0]["check"])
        self.assertEqual("decision-os", payload["evidence"][0]["source"])
        self.assertEqual("FAIL", payload["evidence"][0]["status"])

    def test_protected_v01_blobs_and_modes_are_unchanged(self) -> None:
        for relative, (expected_mode, expected_blob) in PROTECTED_BLOBS.items():
            with self.subTest(relative=relative):
                path = REPO_ROOT / relative
                completed = subprocess.run(
                    ("git", "hash-object", str(path)),
                    capture_output=True,
                    check=False,
                    cwd=REPO_ROOT,
                    text=True,
                )
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertEqual(expected_blob, completed.stdout.strip())
                executable = bool(path.stat().st_mode & stat.S_IXUSR)
                actual_mode = "100755" if executable else "100644"
                self.assertEqual(expected_mode, actual_mode)

        canonical = subprocess.run(
            ("git", "cat-file", "-e", f"{CANONICAL_AS_OF}^{{commit}}"),
            capture_output=True,
            check=False,
            cwd=REPO_ROOT,
        )
        self.assertEqual(0, canonical.returncode)

    def test_scan_module_and_bin_do_not_write_target_or_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_unmanaged_repository(
                parent, "multiple_instructions"
            )
            target_before = tree_digest(repository)
            runner_before = tree_digest(REPO_ROOT)
            target = str(repository)

            results = (
                run_module(parent, "scan", target),
                run_module(parent, "scan", "--format", "json", target),
                run_module(parent, "scan", "--format", "text", target),
                run_bin(parent, "scan", target),
                run_bin(parent, "scan", "--format", "json", target),
                run_bin(parent, "scan", "--format", "text", target),
            )

            self.assertTrue(all(result.returncode == 0 for result in results))
            self.assertTrue(all(result.stderr == b"" for result in results))
            self.assertEqual(target_before, tree_digest(repository))
            self.assertEqual(runner_before, tree_digest(REPO_ROOT))


if __name__ == "__main__":
    unittest.main()
