from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest import mock

import decision_os.handoff_acceptance as guard
from decision_os.handoff_acceptance import (
    EXIT_ACCEPTABLE,
    EXIT_INVALID,
    EXIT_NOT_ACCEPTABLE,
    HandoffProcessError,
    MODE_CLOSED_STATE,
    RESULT_ACCEPTABLE,
    RESULT_INVALID,
    RESULT_NOT_ACCEPTABLE,
    SCHEMA_VERSION,
    assess_handoff,
    assessment_payload,
    exit_code_for_assessment,
    process_error_line,
    render_json,
    render_text,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "handoff_acceptance_v0_2"


def _run_git(
    root: Path,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    completed = subprocess.run(
        ("git", "-C", os.fspath(root), *arguments),
        check=False,
        capture_output=True,
        env=environment,
    )
    if check and completed.returncode != 0:
        raise AssertionError(
            f"git command failed: {arguments!r}; "
            f"stdout={completed.stdout!r}; stderr={completed.stderr!r}"
        )
    return completed


class HandoffAcceptanceV02Test(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.counter = 0

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _fixture(self, name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")

    def _repo(
        self,
        fixture: str = "closed_native.md",
        *,
        branch: str = "main",
        text: str | None = None,
        origin: str | None = None,
        extra_files: dict[str, str] | None = None,
    ) -> tuple[Path, Path]:
        self.counter += 1
        root = self.base / f"repo-{self.counter}"
        root.mkdir()
        _run_git(root, "init", "-b", branch)
        _run_git(root, "config", "user.name", "Handoff Test")
        _run_git(root, "config", "user.email", "handoff@example.invalid")
        if origin is not None:
            _run_git(root, "remote", "add", "origin", origin)
        handoff = root / "handoff.md"
        handoff.write_text(
            self._fixture(fixture) if text is None else text,
            encoding="utf-8",
        )
        (root / "tracked.txt").write_text("base\n", encoding="utf-8")
        for relative, content in (extra_files or {}).items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        _run_git(root, "add", ".")
        _run_git(root, "commit", "-m", "fixture")
        return root, handoff

    def _assess(
        self,
        root: Path,
        handoff: Path,
        *,
        receiver: str = "Codex",
        layer: str = "V13",
        canonical: str | None = None,
    ):
        return assess_handoff(
            repo_root=root,
            handoff_path=handoff,
            expected_receiver=receiver,
            expected_target_layer=layer,
            canonical_branch=canonical,
        )

    def _replace_field(self, text: str, label: str, value: str) -> str:
        prefix = f"{label}:"
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if line.startswith(prefix):
                lines[index] = f"{prefix} {value}"
                return "\n".join(lines) + "\n"
        self.fail(f"field not found: {label}")

    def _tree_snapshot(self, root: Path) -> tuple[object, ...]:
        files: list[tuple[str, int, str]] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            metadata = path.lstat()
            files.append(
                (
                    path.relative_to(root).as_posix(),
                    stat.S_IMODE(metadata.st_mode),
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )
            )
        return (
            tuple(files),
            _run_git(root, "rev-parse", "HEAD").stdout,
            _run_git(root, "symbolic-ref", "-q", "HEAD", check=False).stdout,
            _run_git(root, "show-ref").stdout,
            _run_git(
                root,
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
            ).stdout,
            _run_git(root, "diff", "--binary").stdout,
            _run_git(root, "diff", "--cached", "--binary").stdout,
        )

    def assertIssues(self, assessment, *codes: str) -> None:
        self.assertEqual(assessment.result, RESULT_NOT_ACCEPTABLE)
        self.assertEqual(assessment.mode, None)
        for code in codes:
            self.assertIn(code, assessment.issue_codes)

    def test_rc_01_native_active_routes_to_semantic_review(self) -> None:
        root, handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        assessment = self._assess(root, handoff)
        self.assertIssues(assessment, "SEMANTIC_REVIEW_REQUIRED")
        self.assertEqual(
            assessment.issue_codes, ("SEMANTIC_REVIEW_REQUIRED",)
        )

    def test_rc_01_native_label_layout_and_fence_variants(self) -> None:
        active_root, active_handoff = self._repo(
            "active_native_variant.md", branch="feature/or-fix"
        )
        active = self._assess(active_root, active_handoff)
        self.assertEqual(
            active.issue_codes, ("SEMANTIC_REVIEW_REQUIRED",)
        )

        closed_root, closed_handoff = self._repo(
            "closed_native_variant.md"
        )
        closed = self._assess(
            closed_root, closed_handoff, canonical="main"
        )
        self.assertEqual(
            closed,
            guard.HandoffAssessment(
                RESULT_ACCEPTABLE, MODE_CLOSED_STATE, ()
            ),
        )

    def test_rc_01_repository_identity_alias_is_native(self) -> None:
        text = self._fixture("active_native.md").replace(
            "Repo Root: .", "Repository Identity: owner/native"
        )
        root, handoff = self._repo(
            branch="feature/native",
            text=text,
            origin="https://github.com/owner/native.git",
        )
        assessment = self._assess(root, handoff)
        self.assertEqual(
            assessment.issue_codes, ("SEMANTIC_REVIEW_REQUIRED",)
        )

    def test_rc_02_conflicting_and_equivalent_duplicates(self) -> None:
        root, handoff = self._repo(
            "duplicate_conflict_native.md", branch="feature/native"
        )
        self.assertIssues(self._assess(root, handoff), "FIELD_CONFLICT")

        text = self._fixture("active_native.md").replace(
            "Target Layer: V13", "Target Layer: V13\nTarget-Layer:  v13."
        )
        root, handoff = self._repo(
            branch="feature/native", text=text
        )
        assessment = self._assess(root, handoff)
        self.assertEqual(
            assessment.issue_codes, ("SEMANTIC_REVIEW_REQUIRED",)
        )

    def test_rc_02_history_cannot_fill_current_record(self) -> None:
        root, handoff = self._repo("current_history_gap_native.md")
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "REQUIRED_FIELD_ABSENT")

    def test_rc_02_fenced_history_cannot_contaminate_current(self) -> None:
        text = (
            "```markdown\n"
            + self._fixture("current_history_gap_native.md")
            + "```\n"
        )
        root, handoff = self._repo(text=text)
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "REQUIRED_FIELD_ABSENT")

        unclosed = text.rsplit("```", 1)[0]
        root, handoff = self._repo(text=unclosed)
        assessment = self._assess(root, handoff, canonical="main")
        self.assertEqual(assessment.result, RESULT_INVALID)
        self.assertEqual(
            assessment.issue_codes, ("MALFORMED_REPRESENTATION",)
        )

    def test_rc_02_historical_formatting_after_boundary_is_ignored(
        self,
    ) -> None:
        text = (
            self._fixture("closed_native.md")
            + "\n# Historical Material\n"
            + "```text\nTarget Layer: UNKNOWN\n"
        )
        root, handoff = self._repo(text=text)
        assessment = self._assess(root, handoff, canonical="main")
        self.assertEqual(assessment.result, RESULT_ACCEPTABLE)

    def test_rc_02_explicit_current_heading_is_required(self) -> None:
        text = self._fixture("closed_native.md").split("\n", 2)[2]
        root, handoff = self._repo(text=text)
        assessment = self._assess(root, handoff, canonical="main")
        self.assertEqual(
            assessment.issue_codes, ("UNSUPPORTED_VARIANT",)
        )

    def test_rc_02_multiple_current_regions_are_ambiguous(self) -> None:
        text = (
            self._fixture("active_native.md")
            + "\n# Responsibility Transfer\n"
            + self._fixture("active_native.md").split("\n", 1)[1]
        )
        root, handoff = self._repo(
            branch="feature/native", text=text
        )
        assessment = self._assess(root, handoff)
        self.assertEqual(
            assessment.issue_codes, ("CURRENT_RECORD_AMBIGUOUS",)
        )

    def test_rc_02_qualified_controls_and_branch_case_conflict(
        self,
    ) -> None:
        base = self._fixture("active_native.md")
        cases = (
            base.replace(
                "Current Gate: GO UNDER CAP",
                "Current Gate: GO UNDER CAP — lane-a\n"
                "Current Gate: GO UNDER CAP — lane-b",
            ),
            base.replace(
                "Active Branch: feature/native",
                "Active Branch: feature/native\n"
                "Active Branch: Feature/Native",
            ),
        )
        for text in cases:
            with self.subTest(text=text):
                root, handoff = self._repo(
                    branch="feature/native", text=text
                )
                self.assertIssues(
                    self._assess(root, handoff), "FIELD_CONFLICT"
                )

    def test_rc_03_repository_and_target_binding(self) -> None:
        target_text = self._replace_field(
            self._fixture("active_native.md"), "Target Layer", "V12"
        )
        root, handoff = self._repo(
            branch="feature/native", text=target_text
        )
        self.assertIssues(
            self._assess(root, handoff), "TARGET_LAYER_MISMATCH"
        )

        repo_text = self._replace_field(
            self._fixture("active_native.md"),
            "Repo Root",
            "/definitely/not/this/repository",
        )
        root, handoff = self._repo(
            branch="feature/native", text=repo_text
        )
        self.assertIssues(
            self._assess(root, handoff), "REPOSITORY_MISMATCH"
        )

    def test_rc_03_active_branch_mismatch_has_priority_and_review(self) -> None:
        root, handoff = self._repo(
            "active_native.md", branch="feature/other"
        )
        assessment = self._assess(root, handoff)
        self.assertIssues(
            assessment,
            "ACTIVE_BRANCH_MISMATCH",
            "SEMANTIC_REVIEW_REQUIRED",
        )
        self.assertLess(
            assessment.issue_codes.index("ACTIVE_BRANCH_MISMATCH"),
            assessment.issue_codes.index("SEMANTIC_REVIEW_REQUIRED"),
        )

    def test_rc_03_feature_or_fix_is_not_an_alternative(self) -> None:
        root, handoff = self._repo(
            "active_native_variant.md", branch="feature/or-fix"
        )
        assessment = self._assess(root, handoff)
        self.assertNotIn("FIELD_AMBIGUOUS", assessment.issue_codes)
        self.assertEqual(
            assessment.issue_codes, ("SEMANTIC_REVIEW_REQUIRED",)
        )

    def test_rc_03_action_equality_is_only_a_mechanical_relation(self) -> None:
        text = self._replace_field(
            self._fixture("active_native.md"),
            "First One Action",
            "Inspect a different local record.",
        )
        root, handoff = self._repo(
            branch="feature/native", text=text
        )
        self.assertIssues(
            self._assess(root, handoff),
            "ACTION_RELATION_UNPROVEN",
            "SEMANTIC_REVIEW_REQUIRED",
        )

    def test_rc_03_owner_first_action_and_origin_contradictions(
        self,
    ) -> None:
        base = self._fixture("active_native.md")
        cases = (
            (
                self._replace_field(base, "Next Owner", "Another Agent"),
                "OWNER_MISMATCH",
            ),
            (
                self._replace_field(base, "First One Action", "none"),
                "FIRST_ACTION_NONE_ACTIVE",
            ),
            (
                base.replace(
                    "Repo Root: .",
                    "Repository Identity: owner/missing-origin",
                ),
                "REPOSITORY_REFERENCE_UNRESOLVED",
            ),
        )
        for text, issue in cases:
            with self.subTest(issue=issue):
                root, handoff = self._repo(
                    branch="feature/native", text=text
                )
                self.assertIssues(
                    self._assess(root, handoff),
                    issue,
                    "SEMANTIC_REVIEW_REQUIRED",
                )

    def test_rc_04_clean_canonical_closed_state_is_acceptable(self) -> None:
        root, handoff = self._repo()
        assessment = self._assess(root, handoff, canonical="main")
        self.assertEqual(assessment.result, RESULT_ACCEPTABLE)
        self.assertEqual(assessment.mode, MODE_CLOSED_STATE)
        self.assertEqual(assessment.issue_codes, ())
        self.assertEqual(exit_code_for_assessment(assessment), EXIT_ACCEPTABLE)

    def test_rc_04_stale_feature_branch_fails_closed(self) -> None:
        root, handoff = self._repo()
        _run_git(root, "switch", "-c", "feature/stale")
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "CLOSED_BRANCH_MISMATCH")

    def test_rc_04_dirty_worktree_fails_closed(self) -> None:
        root, handoff = self._repo()
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "WORKTREE_DIRTY")
        self.assertNotIn("INDEX_DIRTY", assessment.issue_codes)

    def test_rc_04_dirty_index_fails_closed(self) -> None:
        root, handoff = self._repo()
        (root / "tracked.txt").write_text("staged\n", encoding="utf-8")
        _run_git(root, "add", "tracked.txt")
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "INDEX_DIRTY")
        self.assertNotIn("WORKTREE_DIRTY", assessment.issue_codes)

    def test_rc_04_untracked_file_fails_closed(self) -> None:
        root, handoff = self._repo()
        (root / "untracked.txt").write_text("new\n", encoding="utf-8")
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "WORKTREE_DIRTY")

    def test_rc_04_unmerged_path_fails_closed(self) -> None:
        root, handoff = self._repo(
            extra_files={"conflict.txt": "base\n"}
        )
        _run_git(root, "switch", "-c", "other")
        (root / "conflict.txt").write_text("other\n", encoding="utf-8")
        _run_git(root, "add", "conflict.txt")
        _run_git(root, "commit", "-m", "other")
        _run_git(root, "switch", "main")
        (root / "conflict.txt").write_text("main\n", encoding="utf-8")
        _run_git(root, "add", "conflict.txt")
        _run_git(root, "commit", "-m", "main")
        merge = _run_git(root, "merge", "other", check=False)
        self.assertNotEqual(merge.returncode, 0)
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "LOCAL_CHANGES_UNRESOLVED")
        self.assertNotIn("INDEX_DIRTY", assessment.issue_codes)
        self.assertNotIn("WORKTREE_DIRTY", assessment.issue_codes)

    def test_rc_04_detached_head_fails_closed(self) -> None:
        root, handoff = self._repo()
        _run_git(root, "switch", "--detach")
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "DETACHED_HEAD")

    def test_rc_04_unknown_or_invalid_canonical_branch(self) -> None:
        candidates = (None, "missing", "refs/heads/main", "bad branch", "@{-1}")
        for candidate in candidates:
            with self.subTest(candidate=candidate):
                root, handoff = self._repo()
                assessment = self._assess(
                    root, handoff, canonical=candidate
                )
                self.assertIssues(
                    assessment, "CANONICAL_BRANCH_UNKNOWN"
                )

    def test_rc_05_unconditional_none_and_conditional_forms(self) -> None:
        base = self._fixture("closed_native.md")
        cases = (
            "none unless approved",
            "none if clean",
            "none / later",
            "none or validation",
        )
        for value in cases:
            with self.subTest(value=value):
                text = self._replace_field(
                    base, "Missing Closure", value
                )
                root, handoff = self._repo(text=text)
                assessment = self._assess(
                    root, handoff, canonical="main"
                )
                self.assertEqual(
                    assessment.result, RESULT_NOT_ACCEPTABLE
                )
                self.assertIn(
                    "FIELD_AMBIGUOUS"
                    if value in ("none / later", "none or validation")
                    else "FIELD_UNKNOWN",
                    assessment.issue_codes,
                )

    def test_rc_05_none_allows_case_space_and_trailing_period(self) -> None:
        text = self._fixture("closed_native.md").replace(
            ": none", ":   None."
        )
        root, handoff = self._repo(text=text)
        assessment = self._assess(root, handoff, canonical="main")
        self.assertEqual(assessment.result, RESULT_ACCEPTABLE)

    def test_rc_05_unknown_in_every_native_field_fails_closed(self) -> None:
        labels = (
            "Target Layer",
            "Repo Root",
            "Current State",
            "Current Gate",
            "Active Branch",
            "Next Authorized Action",
            "Completion Line",
            "Missing Closure",
            "Next Owner",
            "What the Receiving AI Now Owns",
            "First One Action",
            "Do Not Continue Boundary",
            "What must not be returned to the Decision Owner",
        )
        base = self._fixture("closed_native.md")
        for label in labels:
            with self.subTest(label=label):
                root, handoff = self._repo(
                    text=self._replace_field(base, label, "UNKNOWN")
                )
                assessment = self._assess(
                    root, handoff, canonical="main"
                )
                self.assertEqual(
                    assessment.result, RESULT_NOT_ACCEPTABLE
                )
                self.assertIn("FIELD_UNKNOWN", assessment.issue_codes)

    def test_rc_05_closed_owner_work_and_completion_must_close(self) -> None:
        cases = (
            ("Next Owner", "Codex", "CLOSED_STATE_INCOMPLETE"),
            (
                "What the Receiving AI Now Owns",
                "One more local test",
                "SEMANTIC_REVIEW_REQUIRED",
            ),
            (
                "Completion Line",
                "Open",
                "COMPLETION_CLOSURE_CONFLICT",
            ),
        )
        base = self._fixture("closed_native.md")
        for label, value, issue in cases:
            with self.subTest(label=label):
                root, handoff = self._repo(
                    text=self._replace_field(base, label, value)
                )
                self.assertIssues(
                    self._assess(root, handoff, canonical="main"),
                    issue,
                )

    def test_rc_05_state_gate_pairs_are_bounded(self) -> None:
        base = self._fixture("closed_native.md")
        for gate in ("GO", "CAP", "HOLD — qualified"):
            with self.subTest(gate=gate):
                root, handoff = self._repo(
                    text=self._replace_field(base, "Current Gate", gate)
                )
                self.assertIssues(
                    self._assess(root, handoff, canonical="main"),
                    "STATE_GATE_CONFLICT",
                )

    def test_rc_06_native_active_prose_never_auto_accepts(self) -> None:
        text = self._fixture("active_native.md")
        text = self._replace_field(
            text,
            "What the Receiving AI Now Owns",
            "A naturally worded responsibility with no formal grammar.",
        )
        text = self._replace_field(
            text,
            "Do Not Continue Boundary",
            "Pause at the documented local boundary.",
        )
        root, handoff = self._repo(
            branch="feature/native", text=text
        )
        assessment = self._assess(root, handoff)
        self.assertEqual(assessment.result, RESULT_NOT_ACCEPTABLE)
        self.assertIn(
            "SEMANTIC_REVIEW_REQUIRED", assessment.issue_codes
        )
        self.assertNotEqual(assessment.result, RESULT_INVALID)

    def test_rc_06_question_marks_are_not_substring_unknowns(self) -> None:
        text = self._fixture("active_native.md")
        for label in ("Next Authorized Action", "First One Action"):
            text = self._replace_field(
                text, label, "Inspect the README FAQ? heading."
            )
        root, handoff = self._repo(
            branch="feature/native", text=text
        )
        assessment = self._assess(root, handoff)
        self.assertNotIn("FIELD_UNKNOWN", assessment.issue_codes)
        self.assertEqual(
            assessment.issue_codes, ("SEMANTIC_REVIEW_REQUIRED",)
        )

    def test_rc_06_following_line_native_prose_is_not_a_false_label(
        self,
    ) -> None:
        text = self._fixture("active_native.md").replace(
            "Do Not Continue Boundary: "
            "Stop before push and merge; new work needs a gate.",
            "Do Not Continue Boundary:\n"
            "Current state remains unchanged; stop before push.",
        )
        root, handoff = self._repo(
            branch="feature/native", text=text
        )
        assessment = self._assess(root, handoff)
        self.assertNotEqual(assessment.result, RESULT_INVALID)
        self.assertEqual(
            assessment.issue_codes, ("SEMANTIC_REVIEW_REQUIRED",)
        )

    def test_rc_06_closed_none_paraphrase_routes_to_review(self) -> None:
        text = self._replace_field(
            self._fixture("closed_native.md"),
            "Next Owner",
            "There is no next owner",
        )
        root, handoff = self._repo(text=text)
        assessment = self._assess(root, handoff, canonical="main")
        self.assertEqual(
            assessment.issue_codes, ("SEMANTIC_REVIEW_REQUIRED",)
        )

    def test_rc_06_bounded_routine_work_contradiction(self) -> None:
        base = self._fixture("active_native.md")
        cases = (
            (
                "Return routine cleanup to the Decision Owner.",
                True,
            ),
            (
                "No routine cleanup is returned to the Decision Owner.",
                False,
            ),
            (
                "Return the approval decision to the Decision Owner.",
                False,
            ),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                text = self._replace_field(
                    base,
                    "What must not be returned to the Decision Owner",
                    value,
                )
                root, handoff = self._repo(
                    branch="feature/native", text=text
                )
                assessment = self._assess(root, handoff)
                self.assertEqual(
                    "ROUTINE_WORK_RETURNED" in assessment.issue_codes,
                    expected,
                )
                self.assertIn(
                    "SEMANTIC_REVIEW_REQUIRED",
                    assessment.issue_codes,
                )

    def test_rc_06_closed_native_paraphrase_routes_to_review(self) -> None:
        root, handoff = self._repo("semantic_paraphrase_native.md")
        assessment = self._assess(root, handoff, canonical="main")
        self.assertEqual(
            assessment.issue_codes, ("SEMANTIC_REVIEW_REQUIRED",)
        )

    def test_rc_06_label_presence_alone_is_not_acceptable(self) -> None:
        text = self._fixture("closed_native.md")
        text = self._replace_field(
            text, "Completion Line", "The work appears finished"
        )
        root, handoff = self._repo(text=text)
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "SEMANTIC_REVIEW_REQUIRED")
        self.assertNotEqual(assessment.result, RESULT_ACCEPTABLE)

    def test_rc_07_invalid_input_envelope(self) -> None:
        root, handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        outside = self.base / "outside.md"
        outside.write_text(self._fixture("active_native.md"), encoding="utf-8")
        cases: list[tuple[object, str]] = [
            (root / "missing.md", "INPUT_MISSING"),
            (outside, "INPUT_OUTSIDE_ROOT"),
            (root / ".." / "outside.md", "INPUT_OUTSIDE_ROOT"),
            (root, "INPUT_NOT_REGULAR"),
        ]
        directory = root / "directory"
        directory.mkdir()
        cases.append((directory, "INPUT_NOT_REGULAR"))
        for path, issue in cases:
            with self.subTest(issue=issue):
                assessment = self._assess(root, Path(path))
                self.assertEqual(assessment.result, RESULT_INVALID)
                self.assertIn(issue, assessment.issue_codes)

        symlink = root / "handoff-link.md"
        symlink.symlink_to(handoff)
        assessment = self._assess(root, symlink)
        self.assertEqual(assessment.result, RESULT_INVALID)
        self.assertEqual(assessment.issue_codes, ("INPUT_SYMLINK",))

    def test_rc_07_utf8_size_and_malformed_inputs(self) -> None:
        root, _ = self._repo(
            "active_native.md", branch="feature/native"
        )
        invalid_utf8 = root / "invalid.md"
        invalid_utf8.write_bytes(b"\xff")
        assessment = self._assess(root, invalid_utf8)
        self.assertEqual(assessment.result, RESULT_INVALID)
        self.assertEqual(
            assessment.issue_codes, ("INPUT_INVALID_UTF8",)
        )

        too_large = root / "large.md"
        too_large.write_bytes(b"x" * (guard.MAX_INPUT_BYTES + 1))
        assessment = self._assess(root, too_large)
        self.assertEqual(assessment.result, RESULT_INVALID)
        self.assertEqual(assessment.issue_codes, ("INPUT_TOO_LARGE",))

        malformed = root / "malformed.md"
        malformed.write_text(
            self._fixture("active_native.md").replace(
                "Target Layer:", "Target Layer::"
            ),
            encoding="utf-8",
        )
        assessment = self._assess(root, malformed)
        self.assertEqual(assessment.result, RESULT_INVALID)
        self.assertEqual(
            assessment.issue_codes, ("MALFORMED_REPRESENTATION",)
        )

    def test_rc_07_unreadable_input_is_invalid_and_non_echoing(self) -> None:
        root, handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        handoff.chmod(0)
        try:
            assessment = self._assess(root, handoff)
        finally:
            handoff.chmod(0o644)
        self.assertEqual(assessment.result, RESULT_INVALID)
        self.assertEqual(assessment.issue_codes, ("INPUT_UNREADABLE",))
        self.assertNotIn(os.fspath(handoff), render_text(assessment))

    def test_rc_07_non_echo_for_values_paths_git_and_exceptions(self) -> None:
        sentinel = "SECRET_HANDOFF_SENTINEL_9137"
        text = self._replace_field(
            self._fixture("active_native.md"),
            "Next Owner",
            sentinel,
        )
        root, handoff = self._repo(
            branch="feature/native",
            text=text,
            origin=f"https://example.invalid/{sentinel}/repo.git",
        )
        active = self._assess(root, handoff)
        closed_root, closed_handoff = self._repo()
        closed = self._assess(
            closed_root, closed_handoff, canonical="main"
        )
        invalid_path = root / f"{sentinel}.md"
        invalid = self._assess(root, invalid_path)
        for assessment in (active, closed, invalid):
            for rendered in (
                render_text(assessment),
                render_json(assessment),
            ):
                self.assertNotIn(sentinel, rendered)
                self.assertNotIn(os.fspath(root), rendered)
                self.assertNotIn(os.fspath(handoff), rendered)
                self.assertNotIn(os.fspath(closed_root), rendered)
                self.assertNotIn(os.fspath(closed_handoff), rendered)
                self.assertNotIn(os.fspath(invalid_path), rendered)

        with mock.patch.object(
            guard,
            "_select_record",
            side_effect=RuntimeError(sentinel),
        ):
            with self.assertRaises(HandoffProcessError) as raised:
                self._assess(root, handoff)
        self.assertEqual(raised.exception.code, "INTERNAL_ERROR")
        self.assertNotIn(sentinel, process_error_line(raised.exception))

        unavailable = self.base / f"{sentinel}-not-a-repository"
        with self.assertRaises(HandoffProcessError) as raised:
            self._assess(unavailable, unavailable / "handoff.md")
        error_line = process_error_line(raised.exception)
        self.assertNotIn(sentinel, error_line)
        self.assertNotIn(os.fspath(unavailable), error_line)

    def test_rc_07_guard_is_read_only_for_all_result_classes(self) -> None:
        active_root, active_handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        closed_root, closed_handoff = self._repo()
        invalid_root, _ = self._repo(
            "active_native.md", branch="feature/native"
        )
        invalid_path = invalid_root / "missing.md"
        cases = (
            (active_root, active_handoff, None),
            (closed_root, closed_handoff, "main"),
            (invalid_root, invalid_path, None),
        )
        for root, path, canonical in cases:
            with self.subTest(root=root.name):
                before = self._tree_snapshot(root)
                self._assess(
                    root, path, canonical=canonical
                )
                after = self._tree_snapshot(root)
                self.assertEqual(before, after)

    def test_rc_07_repository_fsmonitor_is_never_executed(self) -> None:
        root, handoff = self._repo()
        monitor = self.base / "hostile-fsmonitor"
        marker = Path(f"{monitor}.ran")
        monitor.write_text(
            "#!/bin/sh\n"
            "touch \"$0.ran\"\n"
            "exit 0\n",
            encoding="utf-8",
        )
        monitor.chmod(0o755)
        _run_git(root, "config", "core.fsmonitor", os.fspath(monitor))

        assessment = self._assess(root, handoff, canonical="main")

        self.assertEqual(assessment.result, RESULT_ACCEPTABLE)
        self.assertFalse(marker.exists())

    def test_rc_07_inherited_path_cannot_replace_git(self) -> None:
        root, handoff = self._repo()
        hostile_bin = self.base / "hostile-bin"
        hostile_bin.mkdir()
        fake_git = hostile_bin / "git"
        marker = hostile_bin / "ran"
        fake_git.write_text(
            "#!/bin/sh\n"
            f"touch {marker}\n"
            "exit 99\n",
            encoding="utf-8",
        )
        fake_git.chmod(0o755)
        with mock.patch.dict(
            os.environ, {"PATH": os.fspath(hostile_bin)}
        ):
            assessment = self._assess(
                root, handoff, canonical="main"
            )
        self.assertEqual(assessment.result, RESULT_ACCEPTABLE)
        self.assertFalse(marker.exists())

    def test_rc_07_repository_clean_filter_is_never_executed(self) -> None:
        for facet in ("clean", "process"):
            with self.subTest(facet=facet):
                root, handoff = self._repo(
                    extra_files={
                        ".gitattributes": "tracked.txt filter=evil\n"
                    }
                )
                filter_program = self.base / f"hostile-{facet}-filter"
                marker = Path(f"{filter_program}.ran")
                filter_program.write_text(
                    "#!/bin/sh\n"
                    "touch \"$0.ran\"\n"
                    "cat\n",
                    encoding="utf-8",
                )
                filter_program.chmod(0o755)
                _run_git(
                    root,
                    "config",
                    f"filter.evil.{facet}",
                    os.fspath(filter_program),
                )
                _run_git(
                    root, "config", "filter.evil.required", "true"
                )
                (root / "tracked.txt").write_text(
                    "edit\n", encoding="utf-8"
                )

                assessment = self._assess(
                    root, handoff, canonical="main"
                )

                self.assertIssues(assessment, "WORKTREE_DIRTY")
                self.assertFalse(marker.exists())

    def test_rc_07_hidden_index_flags_cannot_forge_clean_status(
        self,
    ) -> None:
        for option in ("--assume-unchanged", "--skip-worktree"):
            with self.subTest(option=option):
                root, handoff = self._repo()
                _run_git(root, "update-index", option, "tracked.txt")
                (root / "tracked.txt").write_text(
                    "hidden change\n", encoding="utf-8"
                )
                assessment = self._assess(
                    root, handoff, canonical="main"
                )
                self.assertIssues(assessment, "WORKTREE_DIRTY")

    def test_rc_07_local_filemode_config_cannot_forge_clean_status(
        self,
    ) -> None:
        root, handoff = self._repo()
        _run_git(root, "config", "core.filemode", "false")
        (root / "tracked.txt").chmod(0o755)
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "WORKTREE_DIRTY")

    def test_rc_07_in_progress_git_operation_is_unresolved(self) -> None:
        root, handoff = self._repo()
        _run_git(root, "switch", "-c", "topic")
        _run_git(root, "commit", "--allow-empty", "-m", "topic")
        _run_git(root, "switch", "main")
        merge = subprocess.run(
            (
                "git",
                "-C",
                os.fspath(root),
                "merge",
                "--no-ff",
                "--no-commit",
                "topic",
            ),
            check=False,
            capture_output=True,
        )
        self.assertEqual(merge.returncode, 0)
        self.assertTrue((root / ".git" / "MERGE_HEAD").exists())
        assessment = self._assess(root, handoff, canonical="main")
        self.assertIssues(assessment, "LOCAL_CHANGES_UNRESOLVED")

    def test_rc_07_submodule_filter_is_not_executed(self) -> None:
        root, handoff = self._repo()
        child = root / "sm"
        child.mkdir()
        _run_git(child, "init", "-b", "main")
        _run_git(child, "config", "user.name", "Child Test")
        _run_git(child, "config", "user.email", "child@example.invalid")
        (child / ".gitattributes").write_text(
            "tracked filter=subevil\n", encoding="utf-8"
        )
        (child / "tracked").write_text("base\n", encoding="utf-8")
        _run_git(child, "add", ".")
        _run_git(child, "commit", "-m", "child")
        child_head = _run_git(child, "rev-parse", "HEAD").stdout.decode().strip()
        _run_git(
            root,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{child_head},sm",
        )
        _run_git(root, "commit", "-m", "gitlink")

        filter_program = self.base / "submodule-clean-filter"
        marker = Path(f"{filter_program}.ran")
        filter_program.write_text(
            "#!/bin/sh\n"
            "touch \"$0.ran\"\n"
            "cat\n",
            encoding="utf-8",
        )
        filter_program.chmod(0o755)
        _run_git(
            child,
            "config",
            "filter.subevil.clean",
            os.fspath(filter_program),
        )
        (child / "tracked").write_text("edit\n", encoding="utf-8")

        assessment = self._assess(root, handoff, canonical="main")

        self.assertIssues(assessment, "WORKTREE_DIRTY")
        self.assertFalse(marker.exists())

    def test_rc_07_git_config_fifo_times_out_safely(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO unavailable")
        root, handoff = self._repo()
        fifo = self.base / "config-fifo"
        os.mkfifo(fifo)
        _run_git(root, "config", "--add", "include.path", os.fspath(fifo))
        with self.assertRaises(HandoffProcessError) as raised:
            self._assess(root, handoff, canonical="main")
        self.assertEqual(
            raised.exception.code, "REPOSITORY_CONTEXT_UNAVAILABLE"
        )

    def test_rc_07_physical_root_alias_is_supported(self) -> None:
        root, handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        alias = self.base / "repo-alias"
        alias.symlink_to(root, target_is_directory=True)
        assessment = assess_handoff(
            repo_root=alias,
            handoff_path=alias / handoff.name,
            expected_receiver="Codex",
            expected_target_layer="V13",
        )
        self.assertEqual(
            assessment.issue_codes, ("SEMANTIC_REVIEW_REQUIRED",)
        )

    def test_rc_07_root_alias_identity_is_part_of_snapshot(self) -> None:
        first, _ = self._repo()
        second, _ = self._repo()
        alias = self.base / "moving-alias"
        alias.symlink_to(first, target_is_directory=True)
        opening = guard._capture_repository_snapshot(alias, "main")
        alias.unlink()
        alias.symlink_to(second, target_is_directory=True)
        closing = guard._capture_repository_snapshot(alias, "main")
        self.assertFalse(
            guard._same_repository_snapshot(opening, closing)
        )


    def test_rc_08_deterministic_render_payload_and_exit_parity(self) -> None:
        root, handoff = self._repo()
        assessments = [
            self._assess(root, handoff, canonical="main")
            for _ in range(3)
        ]
        self.assertEqual(assessments[0], assessments[1])
        self.assertEqual(assessments[1], assessments[2])
        text_outputs = [render_text(item) for item in assessments]
        json_outputs = [render_json(item) for item in assessments]
        self.assertEqual(len(set(text_outputs)), 1)
        self.assertEqual(len(set(json_outputs)), 1)
        payload = json.loads(json_outputs[0])
        self.assertEqual(payload, assessment_payload(assessments[0]))
        self.assertEqual(payload["schema_version"], SCHEMA_VERSION)
        self.assertEqual(payload["writes_performed"], False)
        self.assertEqual(payload["remote_freshness"], "NOT_CHECKED")
        self.assertEqual(
            exit_code_for_assessment(assessments[0]), EXIT_ACCEPTABLE
        )

        active_root, active_handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        active = self._assess(active_root, active_handoff)
        self.assertEqual(
            exit_code_for_assessment(active), EXIT_NOT_ACCEPTABLE
        )

        invalid = self._assess(active_root, active_root / "missing.md")
        self.assertEqual(invalid.result, RESULT_INVALID)
        self.assertEqual(exit_code_for_assessment(invalid), EXIT_INVALID)

    def test_rc_08_input_mutation_is_unstable_snapshot(self) -> None:
        root, handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        with mock.patch.object(
            guard, "_reread_input", side_effect=guard._Unstable
        ):
            with self.assertRaises(HandoffProcessError) as raised:
                self._assess(root, handoff)
        self.assertEqual(raised.exception.code, "UNSTABLE_SNAPSHOT")

    def test_rc_08_git_head_mutation_is_unstable_snapshot(self) -> None:
        root, handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        original = guard._evaluate_record

        def mutate(*arguments, **keywords):
            result = original(*arguments, **keywords)
            _run_git(root, "commit", "--allow-empty", "-m", "moved")
            return result

        with mock.patch.object(guard, "_evaluate_record", side_effect=mutate):
            with self.assertRaises(HandoffProcessError) as raised:
                self._assess(root, handoff)
        self.assertEqual(raised.exception.code, "UNSTABLE_SNAPSHOT")

    def test_rc_08_git_status_mutation_is_unstable_snapshot(self) -> None:
        root, handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        original = guard._evaluate_record

        def mutate(*arguments, **keywords):
            result = original(*arguments, **keywords)
            (root / "appeared.txt").write_text("changed\n", encoding="utf-8")
            return result

        with mock.patch.object(guard, "_evaluate_record", side_effect=mutate):
            with self.assertRaises(HandoffProcessError) as raised:
                self._assess(root, handoff)
        self.assertEqual(raised.exception.code, "UNSTABLE_SNAPSHOT")

    def test_rc_08_repository_snapshot_comparison_covers_new_git_facts(
        self,
    ) -> None:
        root, _ = self._repo()
        snapshot = guard._capture_repository_snapshot(root, "main")
        for change in (
            {"canonical_tip": "0" * 40},
            {"status_digest": "0" * 64},
            {"index_dirty": True},
            {"worktree_dirty": True},
            {"untracked": True},
            {"unmerged": True},
        ):
            with self.subTest(change=change):
                self.assertFalse(
                    guard._same_repository_snapshot(
                        snapshot, replace(snapshot, **change)
                    )
                )

    def test_rc_08_trusted_scalar_and_process_errors_are_fixed(self) -> None:
        root, handoff = self._repo(
            "active_native.md", branch="feature/native"
        )
        for receiver in ("", "UNKNOWN", "Codex\nsecret", "A/B"):
            with self.subTest(receiver=receiver):
                with self.assertRaises(HandoffProcessError) as raised:
                    self._assess(root, handoff, receiver=receiver)
                self.assertEqual(raised.exception.code, "USAGE_ERROR")
                self.assertEqual(
                    process_error_line(raised.exception),
                    "HANDOFF_ACCEPTANCE_ERROR: USAGE_ERROR\n",
                )
        self.assertEqual(
            process_error_line("not-allowlisted"),
            "HANDOFF_ACCEPTANCE_ERROR: INTERNAL_ERROR\n",
        )


if __name__ == "__main__":
    unittest.main()
