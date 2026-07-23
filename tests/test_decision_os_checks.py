from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from decision_os.checks import (
    EXIT_CONTRADICTION,
    EXIT_INCOMPLETE,
    EXIT_NOT_GIT,
    EXIT_OK,
    inspect_repository,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "v13_runner_v0_1"


def run_git(target: Path, *arguments: str) -> None:
    completed = subprocess.run(
        ("git", "-C", str(target), *arguments),
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)


def create_repository(parent: Path, fixture_name: str) -> Path:
    repository = parent / "target"
    remote = parent / "remote.git"
    repository.mkdir()
    run_git(repository, "init", "-b", "main")
    shutil.copytree(FIXTURES / fixture_name / "docs", repository / "docs")
    shutil.copytree(FIXTURES / fixture_name / "handoff", repository / "handoff")
    (repository / "README.md").write_text("fixture\n", encoding="utf-8")
    run_git(repository, "add", ".")
    run_git(
        repository,
        "-c",
        "user.name=V13 Runner Test",
        "-c",
        "user.email=runner@example.invalid",
        "commit",
        "-m",
        "fixture",
    )
    run_git(parent, "init", "--bare", str(remote))
    run_git(repository, "remote", "add", "origin", str(remote))
    run_git(repository, "push", "-u", "origin", "main")
    run_git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    run_git(repository, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    return repository


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        if path.is_symlink():
            digest.update(b"L")
            digest.update(path.readlink().as_posix().encode("utf-8"))
        elif path.is_file():
            digest.update(b"F")
            digest.update(path.stat().st_mode.to_bytes(8, "big"))
            digest.update(path.read_bytes())
        elif path.is_dir():
            digest.update(b"D")
    return digest.hexdigest()


def replace_in_state_surfaces(repository: Path, old: str, new: str) -> None:
    for relative in (
        Path("docs/current_signal.md"),
        Path("handoff/current_codex_handoff.md"),
    ):
        path = repository / relative
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise AssertionError(f"{old!r} is absent from {relative}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_in_current_signal(repository: Path, old: str, new: str) -> None:
    path = repository / "docs" / "current_signal.md"
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"{old!r} is absent from docs/current_signal.md")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


class RepositoryChecksTest(unittest.TestCase):
    def test_complete_fixture_is_consistent_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            before = tree_digest(repository)

            payload, exit_code = inspect_repository(repository)
            repeated_payload, repeated_exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual(exit_code, repeated_exit_code)
            self.assertEqual(payload, repeated_payload)
            self.assertEqual("PASS", payload["v12_state"])
            self.assertEqual("GO", payload["v13_gate"])
            self.assertEqual("YES", payload["authority_match"])
            self.assertEqual([], payload["missing_closure"])
            self.assertFalse(payload["human_seat_required"])
            default_branch = next(
                item
                for item in payload["evidence"]
                if item["check"] == "git.default_branch"
            )
            self.assertEqual("PASS", default_branch["status"])
            self.assertEqual(0, default_branch["detail"]["ahead"])
            self.assertEqual(0, default_branch["detail"]["behind"])
            self.assertEqual(before, tree_digest(repository))

    def test_missing_closure_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "missing_closure")

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)
            self.assertEqual(
                ["closure_only_tail", "receipt", "rollback_identity"],
                payload["missing_closure"],
            )

    def test_no_run_phase_does_not_require_run_only_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            current = """# Current State

```text
V12 State:
PASS

Current Gate:
HOLD

Active Branch:
none

Codex Next Authorized Action:
none
```
"""
            for relative in (
                Path("docs/current_signal.md"),
                Path("handoff/current_codex_handoff.md"),
            ):
                (repository / relative).write_text(current, encoding="utf-8")

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("UNKNOWN", payload["authority_match"])
            self.assertFalse(payload["human_seat_required"])
            self.assertEqual([], payload["missing_closure"])
            envelope = next(
                item
                for item in payload["evidence"]
                if item["check"] == "state.authority_envelope"
            )
            self.assertEqual("NOT_APPLICABLE", envelope["status"])

    def test_contradiction_has_precedence_over_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "contradictory")
            replace_in_state_surfaces(
                repository,
                "Receipt:\ntests / passing\n\n",
                "",
            )

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_CONTRADICTION, exit_code)
            self.assertTrue(payload["human_seat_required"])
            self.assertIn("receipt", payload["missing_closure"])
            contradiction = next(
                item
                for item in payload["evidence"]
                if item["check"] == "state.contradictions"
            )
            self.assertEqual("FAIL", contradiction["status"])

    def test_dirty_worktree_is_evidence_not_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            (repository / "README.md").write_text("dirty\n", encoding="utf-8")

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            worktree = next(
                item for item in payload["evidence"] if item["check"] == "git.worktree"
            )
            self.assertEqual("DIRTY", worktree["status"])

    def test_missing_handoff_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            (repository / "handoff" / "current_codex_handoff.md").unlink()

            _, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)

    def test_historical_block_does_not_backfill_current_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            current_signal = repository / "docs" / "current_signal.md"
            current_signal.write_text(
                """# Current Signal

```text
Current Gate:
GO

Codex Next Authorized Action:
none
```

## Historical As-of

```text
V12 State:
PASS
```
""",
                encoding="utf-8",
            )
            handoff = repository / "handoff" / "current_codex_handoff.md"
            handoff.write_text(current_signal.read_text(encoding="utf-8"), encoding="utf-8")

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)
            self.assertEqual("UNKNOWN", payload["v12_state"])

    def test_non_git_target_uses_exit_three(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload, exit_code = inspect_repository(directory)

            self.assertEqual(EXIT_NOT_GIT, exit_code)
            self.assertEqual("UNKNOWN", payload["v13_gate"])

    def test_unborn_repository_uses_exit_three(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            run_git(repository, "init", "-b", "main")

            _, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_NOT_GIT, exit_code)

    def test_uninspectable_git_worktree_uses_exit_three(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            (repository / ".git" / "index").write_bytes(b"invalid")

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_NOT_GIT, exit_code)
            self.assertEqual("git.worktree", payload["evidence"][0]["check"])

    def test_invalid_utf8_surface_uses_exit_four(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            (repository / "docs" / "current_signal.md").write_bytes(b"\xff")

            _, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)

    def test_symlinked_surface_uses_exit_four(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_repository(parent, "complete")
            outside = parent / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            current_signal = repository / "docs" / "current_signal.md"
            current_signal.unlink()
            current_signal.symlink_to(outside)

            _, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)

    def test_conflicting_duplicate_in_current_block_uses_exit_five(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            current_signal = repository / "docs" / "current_signal.md"
            text = current_signal.read_text(encoding="utf-8")
            text = text.replace(
                "Current Gate:\nGO",
                "Current Gate:\nGO\n\nCurrent Gate:\nBLOCK",
                1,
            )
            current_signal.write_text(text, encoding="utf-8")

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_CONTRADICTION, exit_code)
            self.assertTrue(payload["human_seat_required"])

    def test_cross_surface_authority_and_closure_conflicts_use_exit_five(self) -> None:
        cases = (
            (
                "Validation Closable:\nYES",
                "Validation Closable:\nNO",
            ),
            (
                "Rollback Identity:\nrunner-test-base",
                "Rollback Identity:\ndifferent-base",
            ),
            (
                "Authority Envelope:\nRUNNER-TEST / ACTIVE",
                "Authority Envelope:\nDIFFERENT-RUNNER / ACTIVE",
            ),
            (
                "Receipt:\ntests / passing",
                "Receipt:\ndifferent receipt",
            ),
            (
                "Activation:\nSTARTED",
                "Activation:\nNOT STARTED",
            ),
        )
        for old, new in cases:
            with self.subTest(field=old.split(":")[0]):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory), "complete")
                    replace_in_current_signal(repository, old, new)

                    payload, exit_code = inspect_repository(repository)

                    self.assertEqual(EXIT_CONTRADICTION, exit_code)
                    self.assertTrue(payload["human_seat_required"])

    def test_preface_fence_is_not_skipped_to_find_later_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            for relative in (
                Path("docs/current_signal.md"),
                Path("handoff/current_codex_handoff.md"),
            ):
                path = repository / relative
                original = path.read_text(encoding="utf-8")
                path.write_text(
                    "# Preface\n\n```text\nNote:\nnot current state\n```\n\n" + original,
                    encoding="utf-8",
                )

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)
            self.assertEqual("UNKNOWN", payload["v12_state"])

    def test_authority_match_yes_requires_all_components(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            for relative in (
                Path("docs/current_signal.md"),
                Path("handoff/current_codex_handoff.md"),
            ):
                path = repository / relative
                text = path.read_text(encoding="utf-8")
                text = text.replace(
                    "Required Authority:\nREPOSITORY-LOCAL TEST\n\n",
                    "",
                    1,
                )
                path.write_text(text, encoding="utf-8")

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_CONTRADICTION, exit_code)
            self.assertTrue(payload["human_seat_required"])

    def test_negative_match_witness_is_a_contradiction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            replace_in_state_surfaces(
                repository,
                "Validation Closable:\nYES",
                "Validation Closable:\nNO",
            )

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_CONTRADICTION, exit_code)
            self.assertTrue(payload["human_seat_required"])

    def test_authority_match_yes_conflicts_with_human_seat_yes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            replace_in_state_surfaces(
                repository,
                "Human Seat Required:\nNO",
                "Human Seat Required:\nYES",
            )

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_CONTRADICTION, exit_code)
            self.assertTrue(payload["human_seat_required"])

    def test_authority_match_no_conflicts_with_implementation_may_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            replace_in_state_surfaces(
                repository,
                "Authority Match:\nYES",
                "Authority Match:\nNO",
            )
            replace_in_state_surfaces(
                repository,
                "Run:\nACTIVE",
                "Run:\nNOT STARTED\n\nImplementation:\nMAY START",
            )

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_CONTRADICTION, exit_code)
            self.assertTrue(payload["human_seat_required"])

    def test_active_authority_mismatch_can_stop_before_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            replace_in_state_surfaces(
                repository,
                "Authority Match:\nYES",
                "Authority Match:\nNO",
            )
            replace_in_state_surfaces(
                repository,
                "Run:\nACTIVE",
                "Run:\nACTIVE\n\nImplementation:\nNOT STARTED",
            )

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("NO", payload["authority_match"])
            self.assertFalse(payload["human_seat_required"])

    def test_invalid_v12_value_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            replace_in_state_surfaces(
                repository,
                "V12 State:\nPASS",
                "V12 State:\nBANANA",
            )

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)
            self.assertEqual("UNKNOWN", payload["v12_state"])

    def test_illegal_fifth_gate_is_a_contradiction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            replace_in_state_surfaces(
                repository,
                "Current Gate:\nGO",
                "Current Gate:\nMAYBE",
            )

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_CONTRADICTION, exit_code)
            self.assertTrue(payload["human_seat_required"])

    def test_blank_next_action_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            replace_in_state_surfaces(
                repository,
                "Codex Next Authorized Action:\nnone",
                "Codex Next Authorized Action:\n\n",
            )

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)
            self.assertEqual("UNKNOWN", payload["next_authorized_action"])

    def test_invalid_authority_and_human_values_are_incomplete(self) -> None:
        replacements = (
            ("Authority Match:\nYES", "Authority Match:\nMAYBE"),
            ("Human Seat Required:\nNO", "Human Seat Required:\nMAYBE"),
        )
        for old, new in replacements:
            with self.subTest(field=old.split(":")[0]):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory), "complete")
                    replace_in_state_surfaces(repository, old, new)

                    _, exit_code = inspect_repository(repository)

                    self.assertEqual(EXIT_INCOMPLETE, exit_code)

    def test_unresolved_enum_alternatives_do_not_pass(self) -> None:
        cases = (
            ("V12 State:\nPASS", "V12 State:\nPASS / BLOCK", EXIT_INCOMPLETE),
            (
                "V12 State:\nPASS",
                "V12 State:\nUNKNOWN / PASS",
                EXIT_INCOMPLETE,
            ),
            ("V12 State:\nPASS", "V12 State:\nUNKNOWNISH", EXIT_INCOMPLETE),
            ("Current Gate:\nGO", "Current Gate:\nGO / HOLD", EXIT_CONTRADICTION),
            (
                "Authority Match:\nYES",
                "Authority Match:\nYES / NO",
                EXIT_INCOMPLETE,
            ),
            (
                "Validation Closable:\nYES",
                "Validation Closable:\nYES / NO",
                EXIT_CONTRADICTION,
            ),
        )
        for old, new, expected in cases:
            with self.subTest(field=old.split(":")[0]):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory), "complete")
                    replace_in_state_surfaces(repository, old, new)

                    _, exit_code = inspect_repository(repository)

                    self.assertEqual(expected, exit_code)

    def test_unresolved_authority_and_closure_placeholders_do_not_pass(self) -> None:
        cases = (
            (
                "Authority Envelope:\nRUNNER-TEST / ACTIVE",
                "Authority Envelope:\n<approved authority envelope>",
                EXIT_INCOMPLETE,
            ),
            (
                "Required Authority:\nREPOSITORY-LOCAL TEST",
                "Required Authority:\n<list>",
                EXIT_CONTRADICTION,
            ),
            (
                "Rollback Identity:\nrunner-test-base",
                "Rollback Identity:\n<commit>",
                EXIT_INCOMPLETE,
            ),
            (
                "Receipt:\ntests / passing",
                "Receipt:\nPENDING VALIDATION",
                EXIT_INCOMPLETE,
            ),
            (
                "Receipt:\ntests / passing",
                "Receipt:\nMISSING",
                EXIT_INCOMPLETE,
            ),
            (
                "Rollback Identity:\nrunner-test-base",
                "Rollback Identity:\nNOT AVAILABLE",
                EXIT_INCOMPLETE,
            ),
            (
                "Closure-Only Tail:\ndocs/current_signal.md + handoff/current_codex_handoff.md",
                "Closure-Only Tail:\nNONE / RESERVED",
                EXIT_INCOMPLETE,
            ),
        )
        for old, new, expected in cases:
            with self.subTest(field=old.split(":")[0]):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory), "complete")
                    replace_in_state_surfaces(repository, old, new)

                    _, exit_code = inspect_repository(repository)

                    self.assertEqual(expected, exit_code)

    def test_not_active_phrase_does_not_activate_a_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            replace_in_state_surfaces(
                repository,
                "Authority Envelope:\nRUNNER-TEST / ACTIVE",
                "Authority Envelope:\nRUNNER-TEST / NOT ACTIVE",
            )
            replace_in_state_surfaces(
                repository,
                "Authority Match:\nYES",
                "Authority Match:\nNO",
            )
            replace_in_state_surfaces(
                repository,
                "Activation:\nSTARTED",
                "Activation:\nNOT STARTED",
            )
            replace_in_state_surfaces(
                repository,
                "Run:\nACTIVE",
                "Run:\nNOT ACTIVE",
            )

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("NO", payload["authority_match"])

    def test_operational_branch_does_not_have_to_equal_checkout_branch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "complete")
            run_git(repository, "switch", "-c", "inspection-branch")

            payload, exit_code = inspect_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            branch = next(
                item for item in payload["evidence"] if item["check"] == "git.branch"
            )
            self.assertEqual("inspection-branch", branch["detail"])


if __name__ == "__main__":
    unittest.main()
