from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from decision_os.scan import (
    EXIT_NOT_GIT,
    EXIT_OK,
    EXIT_UNSTABLE,
    GitReader,
    RECOMMENDATION_FULLER,
    RECOMMENDATION_HANDOFF,
    RECOMMENDATION_INSUFFICIENT,
    RECOMMENDATION_LITE,
    RECOMMENDATION_NONE,
    _snapshot,
    scan_repository,
)
from decision_os import scan as scan_module
from tests.test_decision_os_checks import (
    create_repository as create_v13_repository,
    run_git,
    tree_digest,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "v13_runner_v0_2"


def apply_overlay(repository: Path, name: str) -> None:
    shutil.copytree(FIXTURES / name, repository, dirs_exist_ok=True)


def create_unmanaged_repository(
    parent: Path, *overlays: str, push: bool = True
) -> Path:
    repository = parent / "target"
    remote = parent / "remote.git"
    repository.mkdir()
    run_git(repository, "init", "-b", "main")
    apply_overlay(repository, "base")
    for overlay in overlays:
        apply_overlay(repository, overlay)
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
    if push:
        run_git(parent, "init", "--bare", str(remote))
        run_git(repository, "remote", "add", "origin", str(remote))
        run_git(repository, "push", "-u", "origin", "main")
        run_git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
        run_git(
            repository,
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            "refs/remotes/origin/main",
        )
    return repository


def recommendation(payload: dict[str, object]) -> str:
    value = payload["recommendation"]
    if not isinstance(value, dict):
        raise AssertionError("recommendation is not an object")
    code = value["code"]
    if not isinstance(code, str):
        raise AssertionError("recommendation code is not text")
    return code


def evidence_item(
    payload: dict[str, object], check: str
) -> dict[str, object]:
    items = payload["evidence"]
    if not isinstance(items, list):
        raise AssertionError("evidence is not an array")
    return next(item for item in items if item["check"] == check)


class UnmanagedRepositoryScanTest(unittest.TestCase):
    def test_clean_repository_has_no_adoption_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("decision-os.scan.v0.2", payload["schema_version"])
            self.assertEqual("COMPLETE", payload["scan_completion"])
            self.assertEqual("UNMANAGED_REPOSITORY", payload["mode"])
            self.assertEqual(RECOMMENDATION_NONE, recommendation(payload))
            self.assertEqual("NONE", payload["route"]["code"])
            self.assertEqual("CLEAN", payload["repository"]["worktree"])
            self.assertEqual(0, payload["repository"]["change_count"])
            self.assertNotIn(str(repository), repr(payload))

    def test_one_instruction_recommends_lite_restart_note(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(
                Path(directory), "one_instruction"
            )

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual(RECOMMENDATION_LITE, recommendation(payload))
            instruction = evidence_item(payload, "instructions.surfaces")
            self.assertEqual("OBSERVED", instruction["status"])
            self.assertEqual(
                ["AGENTS.md"], instruction["detail"]["observed"]
            )

    def test_multiple_instructions_recommend_handoff_surface(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(
                Path(directory), "multiple_instructions"
            )

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual(RECOMMENDATION_HANDOFF, recommendation(payload))

    def test_multiple_instructions_and_active_work_use_fuller_fit_route(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(
                Path(directory), "multiple_instructions"
            )
            (repository / "work.txt").write_text("uncommitted\n", encoding="utf-8")

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual(RECOMMENDATION_FULLER, recommendation(payload))

    def test_structural_restart_evidence_suppresses_adoption_recommendation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(
                Path(directory), "one_instruction", "restart_markers"
            )

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual(RECOMMENDATION_NONE, recommendation(payload))
            restart = evidence_item(payload, "restart.surfaces")
            self.assertEqual(
                ["HANDOFF.md"],
                restart["detail"]["bounded_restart_evidence"],
            )
            marker = evidence_item(payload, "restart.markers")
            self.assertIn(
                "current_identity", marker["detail"]["markers"]["HANDOFF.md"]
            )
            self.assertIn(
                "next_action", marker["detail"]["markers"]["HANDOFF.md"]
            )
            self.assertFalse(marker["detail"]["semantic_quality_proven"])

    def test_filename_only_restart_surface_does_not_prove_restartability(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(
                Path(directory), "one_instruction", "restart_surface"
            )

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual(RECOMMENDATION_LITE, recommendation(payload))
            restart = evidence_item(payload, "restart.surfaces")
            self.assertEqual(
                [], restart["detail"]["bounded_restart_evidence"]
            )
            marker = evidence_item(payload, "restart.markers")
            self.assertEqual("ABSENT", marker["status"])

    def test_dirty_and_detached_states_are_evidence_not_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))
            (repository / "dirty.txt").write_text("dirty\n", encoding="utf-8")

            dirty_payload, dirty_exit = scan_repository(repository)

            self.assertEqual(EXIT_OK, dirty_exit)
            self.assertEqual(RECOMMENDATION_LITE, recommendation(dirty_payload))
            run_git(repository, "add", "dirty.txt")
            run_git(
                repository,
                "-c",
                "user.name=V13 Runner Test",
                "-c",
                "user.email=runner@example.invalid",
                "commit",
                "-m",
                "detach fixture",
            )
            run_git(repository, "checkout", "--detach", "HEAD")

            detached_payload, detached_exit = scan_repository(repository)

            self.assertEqual(EXIT_OK, detached_exit)
            self.assertEqual(
                RECOMMENDATION_LITE, recommendation(detached_payload)
            )
            self.assertTrue(detached_payload["repository"]["detached"])

    def test_non_default_ahead_work_recommends_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))
            run_git(repository, "switch", "-c", "feature/local")
            (repository / "feature.txt").write_text("feature\n", encoding="utf-8")
            run_git(repository, "add", "feature.txt")
            run_git(
                repository,
                "-c",
                "user.name=V13 Runner Test",
                "-c",
                "user.email=runner@example.invalid",
                "commit",
                "-m",
                "local feature",
            )

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual(RECOMMENDATION_HANDOFF, recommendation(payload))
            self.assertEqual(1, payload["repository"]["ahead"])
            self.assertEqual(0, payload["repository"]["behind"])

    def test_invalid_utf8_is_partial_unknown_not_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(
                Path(directory), "restart_surface"
            )
            (repository / "HANDOFF.md").write_bytes(b"\xff\xfe")

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("PARTIAL", payload["scan_completion"])
            self.assertEqual(
                RECOMMENDATION_INSUFFICIENT, recommendation(payload)
            )
            restart = evidence_item(payload, "restart.surfaces")
            self.assertEqual("UNKNOWN", restart["status"])
            self.assertEqual(
                "invalid_utf8", restart["detail"]["unknown"][0]["reason"]
            )

    def test_symlinked_surface_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_unmanaged_repository(parent)
            sentinel = parent / "outside.md"
            sentinel.write_text(
                "Active Branch:\noutside\n\nNext Action:\nnever read\n",
                encoding="utf-8",
            )
            handoff = repository / "HANDOFF.md"
            handoff.symlink_to(sentinel)
            before = sentinel.read_bytes()

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("PARTIAL", payload["scan_completion"])
            self.assertEqual(
                RECOMMENDATION_INSUFFICIENT, recommendation(payload)
            )
            self.assertEqual(before, sentinel.read_bytes())
            restart = evidence_item(payload, "restart.surfaces")
            self.assertEqual(
                "symlink_rejected", restart["detail"]["unknown"][0]["reason"]
            )

    def test_symlinked_handoff_directory_is_not_traversed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_unmanaged_repository(parent)
            outside = parent / "outside"
            outside.mkdir()
            (outside / "state.md").write_text(
                "Active Branch:\noutside\n\nNext Action:\nnever read\n",
                encoding="utf-8",
            )
            (repository / "handoff").symlink_to(outside, target_is_directory=True)

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("PARTIAL", payload["scan_completion"])
            self.assertEqual(
                RECOMMENDATION_NONE, recommendation(payload)
            )
            self.assertEqual("UNDETERMINED", payload["mode"])
            self.assertEqual("RUN_V13_CHECK", payload["route"]["code"])
            restart = evidence_item(payload, "restart.surfaces")
            reasons = {
                item["reason"] for item in restart["detail"]["unknown"]
            }
            self.assertIn("symlink_rejected", reasons)

    def test_v13_repository_routes_to_check_without_weak_scan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_v13_repository(
                Path(directory), "complete"
            )

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("V13_MANAGED_REPOSITORY", payload["mode"])
            self.assertEqual(RECOMMENDATION_NONE, recommendation(payload))
            self.assertEqual("RUN_V13_CHECK", payload["route"]["code"])
            self.assertEqual(
                "decision-os check <repository>",
                payload["route"]["command"],
            )

    def test_partial_v13_surface_is_undetermined_and_routes_to_check(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))
            current_signal = repository / "docs" / "current_signal.md"
            current_signal.parent.mkdir()
            current_signal.write_text("# current\n", encoding="utf-8")

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("UNDETERMINED", payload["mode"])
            self.assertEqual("RUN_V13_CHECK", payload["route"]["code"])
            self.assertEqual(RECOMMENDATION_NONE, recommendation(payload))

    def test_origin_identity_does_not_emit_credentials_or_local_path(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))
            run_git(
                repository,
                "remote",
                "set-url",
                "origin",
                "https://user:secret@example.test/owner/repo.git?token=x#frag",
            )

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            identity = payload["repository"]["origin"]["identity"]
            self.assertEqual("example.test/owner/repo.git", identity)
            self.assertNotIn("secret", repr(payload))
            self.assertNotIn("token", repr(payload))

            run_git(
                repository,
                "remote",
                "set-url",
                "origin",
                "git@example.test:owner/repo.git?token=x#frag",
            )
            scp_payload, scp_exit = scan_repository(repository)

            self.assertEqual(EXIT_OK, scp_exit)
            self.assertEqual(
                "example.test/owner/repo.git",
                scp_payload["repository"]["origin"]["identity"],
            )
            self.assertNotIn("token", repr(scp_payload))

    def test_malformed_origin_is_bounded_unknown_not_internal_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))
            run_git(
                repository,
                "remote",
                "set-url",
                "origin",
                "https://[malformed/repo",
            )

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertIsNone(payload["repository"]["origin"]["identity"])
            origin = evidence_item(payload, "git.origin")
            self.assertEqual("UNKNOWN", origin["status"])

    def test_exact_allowlist_does_not_accept_case_variant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))
            (repository / "agents.md").write_text(
                "# lower-case only\n", encoding="utf-8"
            )
            run_git(repository, "add", "agents.md")
            run_git(
                repository,
                "-c",
                "user.name=V13 Runner Test",
                "-c",
                "user.email=runner@example.invalid",
                "commit",
                "-m",
                "case fixture",
            )

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            instruction = evidence_item(payload, "instructions.surfaces")
            self.assertNotIn("AGENTS.md", instruction["detail"]["observed"])

    def test_handoff_candidate_enumeration_stops_at_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))
            handoff = repository / "handoff"
            handoff.mkdir()
            for index in range(65):
                (handoff / f"{index:02d}.md").write_text(
                    "Active Branch:\nfixture\n\nNext Action:\nfixture\n",
                    encoding="utf-8",
                )

            payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("PARTIAL", payload["scan_completion"])
            restart = evidence_item(payload, "restart.surfaces")
            self.assertEqual([], restart["detail"]["observed"])
            self.assertIn(
                {
                    "path": "handoff/*.md",
                    "reason": "candidate_limit",
                },
                restart["detail"]["unknown"],
            )

    def test_intermediate_directory_swap_cannot_escape_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_unmanaged_repository(parent)
            docs = repository / "docs"
            docs.mkdir()
            (docs / "current_state.md").write_text(
                "Active Branch:\ninside\n\nNext Action:\ninside\n",
                encoding="utf-8",
            )
            run_git(repository, "add", "docs/current_state.md")
            run_git(
                repository,
                "-c",
                "user.name=V13 Runner Test",
                "-c",
                "user.email=runner@example.invalid",
                "commit",
                "-m",
                "safe state",
            )
            outside = parent / "outside"
            outside.mkdir()
            sentinel = outside / "current_state.md"
            sentinel.write_text(
                "Active Branch:\nsecret\n\nNext Action:\nsecret\n",
                encoding="utf-8",
            )
            real_match = scan_module._entry_match
            swapped = False

            def swap_after_match(
                directory_fd: int, expected: str
            ) -> tuple[str, str | None]:
                nonlocal swapped
                result = real_match(directory_fd, expected)
                if expected == "docs" and result[0] == "OBSERVED" and not swapped:
                    docs.rename(repository / "docs-original")
                    (repository / "docs").symlink_to(
                        outside, target_is_directory=True
                    )
                    swapped = True
                return result

            with patch(
                "decision_os.scan._entry_match",
                side_effect=swap_after_match,
            ):
                payload, exit_code = scan_repository(repository)

            self.assertTrue(swapped)
            self.assertEqual(EXIT_UNSTABLE, exit_code)
            self.assertNotIn("secret", repr(payload))
            self.assertEqual(
                b"Active Branch:\nsecret\n\nNext Action:\nsecret\n",
                sentinel.read_bytes(),
            )

    def test_non_git_target_returns_three_with_stable_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload, exit_code = scan_repository(Path(directory))

            self.assertEqual(EXIT_NOT_GIT, exit_code)
            self.assertEqual("FAILED", payload["scan_completion"])
            self.assertEqual("UNDETERMINED", payload["mode"])
            self.assertEqual(
                RECOMMENDATION_INSUFFICIENT, recommendation(payload)
            )
            self.assertNotIn(str(Path(directory)), repr(payload))

    def test_ambient_git_environment_cannot_redirect_or_trace_scan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            target_parent = parent / "target-parent"
            other_parent = parent / "other-parent"
            target_parent.mkdir()
            other_parent.mkdir()
            repository = create_unmanaged_repository(target_parent)
            other = create_unmanaged_repository(other_parent)
            (other / "other.txt").write_text("other\n", encoding="utf-8")
            run_git(other, "add", "other.txt")
            run_git(
                other,
                "-c",
                "user.name=V13 Runner Test",
                "-c",
                "user.email=runner@example.invalid",
                "commit",
                "-m",
                "different repository",
            )
            target_head = GitReader(repository).run(
                "rev-parse", "--verify", "HEAD"
            ).stdout.strip()
            trace = parent / "git-trace.log"

            with patch.dict(
                os.environ,
                {
                    "GIT_DIR": str(other / ".git"),
                    "GIT_WORK_TREE": str(other),
                    "GIT_INDEX_FILE": str(other / ".git" / "index"),
                    "GIT_TRACE": str(trace),
                },
            ):
                payload, exit_code = scan_repository(repository)
                reader = GitReader(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual(target_head, payload["repository"]["head"])
            self.assertFalse(trace.exists())
            self.assertNotIn("GIT_DIR", reader.environment)
            self.assertNotIn("GIT_TRACE", reader.environment)
            self.assertEqual("1", reader.environment["GIT_NO_LAZY_FETCH"])

    def test_non_utf8_worktree_filename_is_counted_but_never_emitted(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))
            stable = _snapshot(GitReader(repository))
            raw_filename_snapshot = replace(
                stable, status="?? invalid-\udcff.txt\0"
            )

            with patch(
                "decision_os.scan._snapshot",
                side_effect=(raw_filename_snapshot, raw_filename_snapshot),
            ):
                payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_OK, exit_code)
            self.assertEqual("DIRTY", payload["repository"]["worktree"])
            self.assertEqual(1, payload["repository"]["change_count"])
            self.assertNotIn("invalid-", repr(payload))

    def test_opening_and_closing_snapshot_mismatch_returns_seven(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))
            reader_snapshot = _snapshot(GitReader(repository))
            closing = replace(reader_snapshot, head="0" * 40)

            with patch(
                "decision_os.scan._snapshot",
                side_effect=(reader_snapshot, closing),
            ):
                payload, exit_code = scan_repository(repository)

            self.assertEqual(EXIT_UNSTABLE, exit_code)
            self.assertEqual("FAILED", payload["scan_completion"])
            self.assertEqual(
                "CONTRADICTORY", payload["evidence"][0]["status"]
            )
            self.assertEqual(
                ["head"], payload["evidence"][0]["detail"]["changed"]
            )

    def test_status_read_disables_fsmonitor_and_uses_nul_no_renames(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(Path(directory))
            reader = GitReader(repository)

            with patch.object(reader, "run", wraps=reader.run) as run:
                _snapshot(reader)

            calls = tuple(call.args for call in run.call_args_list)
            self.assertIn(
                (
                    "-c",
                    "core.fsmonitor=false",
                    "status",
                    "--porcelain=v1",
                    "-z",
                    "--untracked-files=all",
                    "--no-renames",
                ),
                calls,
            )

    def test_direct_scan_is_repeatable_and_does_not_write_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_unmanaged_repository(
                Path(directory), "multiple_instructions"
            )
            before = tree_digest(repository)

            first_payload, first_exit = scan_repository(repository)
            second_payload, second_exit = scan_repository(repository)

            self.assertEqual(EXIT_OK, first_exit)
            self.assertEqual(first_exit, second_exit)
            self.assertEqual(first_payload, second_payload)
            self.assertEqual(before, tree_digest(repository))


if __name__ == "__main__":
    unittest.main()
