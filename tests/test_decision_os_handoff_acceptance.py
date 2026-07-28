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
from unittest.mock import patch

from decision_os.handoff_acceptance import (
    HandoffProcessError,
    ISSUE_CODES,
    assess_handoff,
    render_json,
    render_text,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "handoff_acceptance_v0_1"
EXPECTED_RECEIVER = "Codex Executor"
EXPECTED_TARGET_LAYER = "V13"
REPOSITORY_SLUG = "example/handoff-fixture"
ORIGIN_URL = f"https://github.com/{REPOSITORY_SLUG}.git"
MAX_INPUT_BYTES = 1024 * 1024


def run_git(repository: Path, *arguments: str) -> str:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        capture_output=True,
        check=False,
        env=environment,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return completed.stdout


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def replaced_once(content: str, old: str, new: str) -> str:
    if content.count(old) != 1:
        raise AssertionError(f"expected exactly one replacement for {old!r}")
    return content.replace(old, new, 1)


def create_repository(
    parent: Path,
    content: str,
    *,
    handoff_name: str = "handoff.md",
) -> tuple[Path, Path]:
    repository = parent / "target"
    repository.mkdir()
    run_git(repository, "init", "-b", "main")
    run_git(repository, "remote", "add", "origin", ORIGIN_URL)
    handoff_directory = repository / "handoff"
    handoff_directory.mkdir()
    handoff_path = handoff_directory / handoff_name
    rendered = content.replace("__REPO_ROOT__", str(repository.resolve()))
    handoff_path.write_text(rendered, encoding="utf-8")
    (repository / "README.md").write_text("fixture\n", encoding="utf-8")
    run_git(repository, "add", ".")
    run_git(
        repository,
        "-c",
        "user.name=Handoff Acceptance Test",
        "-c",
        "user.email=handoff-acceptance@example.invalid",
        "commit",
        "-m",
        "fixture",
    )
    return repository, handoff_path


def assess(repository: Path, handoff_path: Path):
    return assess_handoff(
        repo_root=repository,
        handoff_path=handoff_path,
        expected_receiver=EXPECTED_RECEIVER,
        expected_target_layer=EXPECTED_TARGET_LAYER,
    )


def artifact_snapshot(repository: Path, handoff_path: Path) -> tuple[object, ...]:
    status_output = run_git(repository, "status", "--porcelain=v1", "-z")
    head = run_git(repository, "rev-parse", "HEAD").strip()
    branch = run_git(repository, "branch", "--show-current").strip()
    metadata = handoff_path.lstat()
    digest = hashlib.sha256()
    for path in sorted(repository.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(repository).as_posix()
        observed = path.lstat()
        digest.update(relative.encode("utf-8"))
        digest.update(
            (
                observed.st_mode,
                observed.st_size,
                observed.st_mtime_ns,
            ).__repr__().encode("ascii")
        )
        if stat.S_ISLNK(observed.st_mode):
            digest.update(b"L")
            digest.update(os.readlink(path).encode("utf-8"))
        elif stat.S_ISREG(observed.st_mode):
            digest.update(b"F")
            digest.update(path.read_bytes())
        elif stat.S_ISDIR(observed.st_mode):
            digest.update(b"D")
    return (
        handoff_path.read_bytes(),
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
        digest.hexdigest(),
        status_output,
        head,
        branch,
    )


class HandoffAcceptanceSemanticTest(unittest.TestCase):
    def assert_assessment(
        self,
        assessment,
        *,
        result: str,
        mode: str | None,
        issues: tuple[str, ...] | None = None,
    ) -> None:
        self.assertEqual(result, assessment.result)
        self.assertEqual(mode, assessment.mode)
        if issues is not None:
            self.assertEqual(issues, tuple(assessment.issue_codes))
        rendered = json.loads(render_json(assessment))
        self.assertFalse(rendered["approval_performed"])
        self.assertFalse(rendered["authority_granted"])
        self.assertFalse(rendered["writes_performed"])
        self.assertEqual("NOT_CHECKED", rendered["remote_freshness"])

    def test_active_fenced_ordinary_cap_and_mixed_variants_are_acceptable(
        self,
    ) -> None:
        rendered_results: list[str] = []
        for fixture in (
            "active_fenced.md",
            "active_ordinary_cap.md",
            "active_mixed.md",
        ):
            with (
                self.subTest(fixture=fixture),
                tempfile.TemporaryDirectory() as directory,
            ):
                repository, handoff_path = create_repository(
                    Path(directory),
                    fixture_text(fixture),
                )

                assessment = assess(repository, handoff_path)

                self.assert_assessment(
                    assessment,
                    result="ACCEPTABLE",
                    mode="ACTIVE_TRANSFER",
                    issues=(),
                )
                rendered_results.append(render_json(assessment))

        self.assertEqual(1, len(set(rendered_results)))

    def test_two_closed_variants_are_acceptable_and_equivalent(self) -> None:
        rendered_results: list[str] = []
        for fixture in ("closed_ordinary.md", "closed_fenced.md"):
            with (
                self.subTest(fixture=fixture),
                tempfile.TemporaryDirectory() as directory,
            ):
                repository, handoff_path = create_repository(
                    Path(directory),
                    fixture_text(fixture),
                )

                assessment = assess(repository, handoff_path)

                self.assert_assessment(
                    assessment,
                    result="ACCEPTABLE",
                    mode="CLOSED_STATE",
                    issues=(),
                )
                rendered_results.append(render_json(assessment))

        self.assertEqual(1, len(set(rendered_results)))

    def test_label_presence_cannot_hide_semantic_tails_or_owner_substitution(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                fixture_text("label_only_false_ready.md"),
            )

            assessment = assess(repository, handoff_path)

        self.assert_assessment(
            assessment,
            result="NOT_ACCEPTABLE",
            mode=None,
        )
        self.assertIn("FIELD_UNKNOWN", assessment.issue_codes)
        self.assertNotEqual((), tuple(assessment.issue_codes))

    def test_control_and_action_tails_are_never_ignored(self) -> None:
        base = fixture_text("active_fenced.md")
        cases = (
            (
                "state_tail",
                "Current State: ACTIVE",
                "Current State: ACTIVE - READY",
                "FIELD_UNKNOWN",
            ),
            (
                "gate_tail",
                "Current Gate: GO",
                "Current Gate: GO — MERGE",
                "FIELD_UNKNOWN",
            ),
            (
                "action_tail",
                (
                    "Next Authorized Action: VALIDATE [VAL-1]; "
                    "closure=VAL-1; branch=main"
                ),
                (
                    "Next Authorized Action: VALIDATE [VAL-1]; "
                    "closure=VAL-1; branch=main then MERGE"
                ),
                "FIELD_UNKNOWN",
            ),
        )
        for name, old, new, issue in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    replaced_once(base, old, new),
                )

                assessment = assess(repository, handoff_path)

                self.assertEqual("NOT_ACCEPTABLE", assessment.result)
                self.assertIn(issue, assessment.issue_codes)

    def test_every_required_semantic_slot_fails_closed_when_unknown(
        self,
    ) -> None:
        base = fixture_text("active_fenced.md")
        cases = (
            ("target_layer", "Target Layer: V13", "Target Layer: UNKNOWN"),
            (
                "repository_reference",
                "Repo Root: __REPO_ROOT__",
                "Repo Root: UNKNOWN",
            ),
            ("current_state", "Current State: ACTIVE", "Current State: UNKNOWN"),
            ("current_gate", "Current Gate: GO", "Current Gate: UNKNOWN"),
            ("active_branch", "Active Branch: main", "Active Branch: UNKNOWN"),
            (
                "next_authorized_action",
                (
                    "Next Authorized Action: VALIDATE [VAL-1]; "
                    "closure=VAL-1; branch=main"
                ),
                "Next Authorized Action: UNKNOWN",
            ),
            (
                "completion_line",
                (
                    "Completion Line:\n"
                    "OPEN:\n"
                    "- [DONE-1] TEST; subject=handoff_guard; expected=passes"
                ),
                "Completion Line: UNKNOWN",
            ),
            (
                "missing_closure",
                (
                    "Missing Closure:\n"
                    "- [VAL-1] VALIDATION; owner=RECEIVER; "
                    "subject=handoff_guard"
                ),
                "Missing Closure: UNKNOWN",
            ),
            ("next_owner", "Next Owner: Codex Executor", "Next Owner: UNKNOWN"),
            (
                "receiving_ownership",
                (
                    "Receiving AI Owns:\n"
                    "- [VAL-1] VALIDATION; owner=RECEIVER; "
                    "subject=handoff_guard"
                ),
                "Receiving AI Owns: UNKNOWN",
            ),
            (
                "first_one_action",
                (
                    "First One Action: VALIDATE [VAL-1]; "
                    "closure=VAL-1; branch=main"
                ),
                "First One Action: UNKNOWN",
            ),
            (
                "do_not_continue_boundary",
                (
                    "Do Not Continue Boundary:\n"
                    "STOP_BEFORE: EXTERNAL, IRREVERSIBLE"
                ),
                "Do Not Continue Boundary: UNKNOWN",
            ),
            (
                "ai_retained_work",
                "Work Not Returned to Decision Owner: RETAIN: VAL-1",
                "Work Not Returned to Decision Owner: UNKNOWN",
            ),
        )
        for name, old, new in cases:
            with self.subTest(field=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    replaced_once(base, old, new),
                )

                assessment = assess(repository, handoff_path)

                self.assertEqual("NOT_ACCEPTABLE", assessment.result)
                self.assertIsNone(assessment.mode)
                self.assertIn("FIELD_UNKNOWN", assessment.issue_codes)

    def test_unresolved_alternatives_are_ambiguous_not_acceptable(self) -> None:
        base = fixture_text("active_fenced.md")
        cases = (
            (
                "target_layer",
                "Target Layer: V13",
                "Target Layer: V13 or V14",
                "FIELD_AMBIGUOUS",
            ),
            (
                "target_layer_punctuated_alternative",
                "Target Layer: V13",
                "Target Layer: V13 or,V14",
                "FIELD_AMBIGUOUS",
            ),
            (
                "branch",
                "Active Branch: main",
                "Active Branch: main or other",
                "FIELD_AMBIGUOUS",
            ),
            (
                "branch_punctuated_alternative",
                "Active Branch: main",
                "Active Branch: main or,other",
                "FIELD_AMBIGUOUS",
            ),
            (
                "owner",
                "Next Owner: Codex Executor",
                "Next Owner: Codex Executor or Other Executor",
                "FIELD_AMBIGUOUS",
            ),
            (
                "owner_punctuated_condition",
                "Next Owner: Codex Executor",
                "Next Owner: Codex Executor unless, approved",
                "FIELD_UNKNOWN",
            ),
            (
                "target_question_marker",
                "Target Layer: V13",
                "Target Layer: V13?",
                "FIELD_UNKNOWN",
            ),
        )
        for name, old, new, expected_issue in cases:
            with self.subTest(field=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    replaced_once(base, old, new),
                )

                assessment = assess(repository, handoff_path)

                self.assertEqual("NOT_ACCEPTABLE", assessment.result)
                self.assertIn(expected_issue, assessment.issue_codes)

    def test_ownership_requires_receiver_work_and_retention(self) -> None:
        base = fixture_text("active_fenced.md")
        receiving_block = (
            "Receiving AI Owns:\n"
            "- [VAL-1] VALIDATION; owner=RECEIVER; subject=handoff_guard\n"
        )
        cases = (
            (
                "owner_mismatch",
                replaced_once(
                    base,
                    "Next Owner: Codex Executor",
                    "Next Owner: Other Executor",
                ),
                ("OWNER_MISMATCH",),
            ),
            (
                "owner_only",
                base.replace(receiving_block, "", 1).replace(
                    "Work Not Returned to Decision Owner: RETAIN: VAL-1\n",
                    "",
                    1,
                ),
                ("REQUIRED_FIELD_ABSENT",),
            ),
            (
                "vague_ownership",
                replaced_once(
                    base,
                    (
                        "Receiving AI Owns:\n"
                        "- [VAL-1] VALIDATION; owner=RECEIVER; "
                        "subject=handoff_guard"
                    ),
                    "Receiving AI Owns: validate the handoff",
                ),
                ("FIELD_UNKNOWN",),
            ),
            (
                "routine_returned",
                base.replace(
                    "owner=RECEIVER",
                    "owner=DECISION_OWNER",
                ),
                ("OWNER_MISMATCH", "ROUTINE_WORK_RETURNED"),
            ),
        )
        for name, content, issues in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assertEqual("NOT_ACCEPTABLE", assessment.result)
                for issue in issues:
                    self.assertIn(issue, assessment.issue_codes)

    def test_work_identifier_references_are_closed_over_the_record(self) -> None:
        active = fixture_text("active_fenced.md")
        capped = fixture_text("active_ordinary_cap.md")
        cases = (
            (
                "undefined_retain",
                replaced_once(
                    active,
                    "RETAIN: VAL-1",
                    "RETAIN: OTHER",
                ),
            ),
            (
                "undefined_closure_reference",
                active.replace(
                    "closure=VAL-1",
                    "closure=OTHER",
                ),
            ),
            (
                "undefined_cap",
                replaced_once(
                    capped,
                    "CAP_TO: VAL-1",
                    "CAP_TO: OTHER",
                ),
            ),
            (
                "reused_id_with_different_subject",
                replaced_once(
                    active,
                    (
                        "Receiving AI Owns:\n"
                        "- [VAL-1] VALIDATION; owner=RECEIVER; "
                        "subject=handoff_guard"
                    ),
                    (
                        "Receiving AI Owns:\n"
                        "- [VAL-1] VALIDATION; owner=RECEIVER; "
                        "subject=handoff_guard\n"
                        "- [VAL-1] VALIDATION; owner=RECEIVER; "
                        "subject=other_subject"
                    ),
                ),
            ),
        )
        for name, content in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assertEqual("NOT_ACCEPTABLE", assessment.result)
                self.assertTrue(
                    {"FIELD_UNKNOWN", "FIELD_CONFLICT"}
                    .intersection(assessment.issue_codes)
                )

    def test_branch_and_action_relations_fail_closed(self) -> None:
        base = fixture_text("active_fenced.md")
        restricted_mutation = (
            base.replace("Current State: ACTIVE", "Current State: RESTRICTED")
            .replace("Current Gate: GO", "Current Gate: HOLD")
            .replace("VALIDATE [VAL-1]", "IMPLEMENT [VAL-1]")
            .replace("VALIDATION; owner=RECEIVER", "IMPLEMENTATION; owner=RECEIVER")
        )
        external_action = (
            base.replace("VALIDATE [VAL-1]", "PUSH [VAL-1]")
            .replace("VALIDATION; owner=RECEIVER", "GIT; owner=RECEIVER")
        )
        cases = (
            (
                "checkout_branch_mismatch",
                replaced_once(
                    base,
                    "Active Branch: main",
                    "Active Branch: other",
                ),
                "ACTIVE_BRANCH_MISMATCH",
            ),
            (
                "action_branch_mismatch",
                base.replace("branch=main", "branch=other"),
                "ACTION_BRANCH_MISMATCH",
            ),
            (
                "restricted_mutating_action",
                restricted_mutation,
                "GATE_ACTION_CONFLICT",
            ),
            (
                "authorized_and_first_disagree",
                replaced_once(
                    base,
                    (
                        "First One Action: VALIDATE [VAL-1]; "
                        "closure=VAL-1; branch=main"
                    ),
                    (
                        "First One Action: TEST [VAL-1]; "
                        "closure=VAL-1; branch=main"
                    ),
                ),
                "ACTION_RELATION_UNPROVEN",
            ),
            (
                "unsafe_external_first_action",
                external_action,
                "FIRST_ACTION_UNSAFE",
            ),
        )
        for name, content, issue in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assertEqual("NOT_ACCEPTABLE", assessment.result)
                self.assertIn(issue, assessment.issue_codes)

    def test_branch_grammar_allows_slash_and_detached_head_fails_closed(
        self,
    ) -> None:
        base = fixture_text("active_fenced.md")
        slash_branch = (
            base.replace("Active Branch: main", "Active Branch: feature/or")
            .replace("branch=main", "branch=feature/or")
        )
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                slash_branch,
            )
            run_git(repository, "branch", "-m", "feature/or")

            assessment = assess(repository, handoff_path)

            self.assert_assessment(
                assessment,
                result="ACCEPTABLE",
                mode="ACTIVE_TRANSFER",
                issues=(),
            )

        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                base,
            )
            run_git(repository, "checkout", "--detach")

            assessment = assess(repository, handoff_path)

            self.assert_assessment(
                assessment,
                result="NOT_ACCEPTABLE",
                mode=None,
                issues=("ACTIVE_BRANCH_MISMATCH",),
            )

    def test_or_tokens_remain_legal_in_grammar_defined_identifiers(
        self,
    ) -> None:
        work_id_or = fixture_text("active_ordinary_cap.md").replace(
            "VAL-1",
            "OR",
        )
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                work_id_or,
            )

            assessment = assess(repository, handoff_path)

            self.assert_assessment(
                assessment,
                result="ACCEPTABLE",
                mode="ACTIVE_TRANSFER",
                issues=(),
            )

        branch_or = fixture_text("active_fenced.md").replace("main", "or")
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                branch_or,
            )
            run_git(repository, "branch", "-m", "or")

            assessment = assess(repository, handoff_path)

            self.assert_assessment(
                assessment,
                result="ACCEPTABLE",
                mode="ACTIVE_TRANSFER",
                issues=(),
            )

        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "foo or bar"
            parent.mkdir()
            repository, handoff_path = create_repository(
                parent,
                fixture_text("active_fenced.md"),
            )

            assessment = assess(repository, handoff_path)

            self.assert_assessment(
                assessment,
                result="ACCEPTABLE",
                mode="ACTIVE_TRANSFER",
                issues=(),
            )

    def test_control_qualifiers_use_whole_atoms_and_state_gate_matrix(
        self,
    ) -> None:
        base = fixture_text("active_fenced.md")
        governance = (
            base.replace(
                "Current Gate: GO",
                (
                    "Current Gate: GO — GOVERNANCE\n"
                    "V13 Gate: GO - GOVERNANCE"
                ),
            )
            .replace(
                (
                    "- [VAL-1] VALIDATION; owner=RECEIVER; "
                    "subject=handoff_guard"
                ),
                (
                    "- [VAL-1] VALIDATION; owner=RECEIVER; "
                    "subject=handoff_guard; scope=GOVERNANCE"
                ),
            )
            .replace(
                "STOP_BEFORE: EXTERNAL, IRREVERSIBLE",
                (
                    "SCOPE: GOVERNANCE\n"
                    "STOP_BEFORE: EXTERNAL, IRREVERSIBLE"
                ),
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                governance,
            )

            assessment = assess(repository, handoff_path)

            self.assert_assessment(
                assessment,
                result="ACCEPTABLE",
                mode="ACTIVE_TRANSFER",
                issues=(),
            )

        conflicts = (
            (
                "restricted_go",
                base.replace("Current State: ACTIVE", "Current State: RESTRICTED"),
            ),
            (
                "restricted_go_under_cap",
                fixture_text("active_ordinary_cap.md").replace(
                    "ACTIVE",
                    "RESTRICTED",
                    1,
                ),
            ),
            (
                "closed_go",
                fixture_text("closed_ordinary.md").replace(
                    "Current Gate: HOLD",
                    "Current Gate: GO",
                ),
            ),
        )
        for name, content in conflicts:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assertEqual("NOT_ACCEPTABLE", assessment.result)
                self.assertIn("STATE_GATE_CONFLICT", assessment.issue_codes)

        capped = fixture_text("active_ordinary_cap.md")
        invalid_grammar = (
            (
                "action_class_qualifier",
                capped.replace("B DESIGN ONLY", "EXTERNAL").replace(
                    "B_DESIGN_ONLY",
                    "EXTERNAL",
                ),
            ),
            (
                "conditional_qualifier",
                capped.replace("B DESIGN ONLY", "WHEN STABLE").replace(
                    "B_DESIGN_ONLY",
                    "WHEN_STABLE",
                ),
            ),
            (
                "hyphenated_boundary_class",
                replaced_once(
                    base,
                    "STOP_BEFORE: EXTERNAL, IRREVERSIBLE",
                    "STOP_BEFORE: LOCAL-CHANGE, IRREVERSIBLE",
                ),
            ),
        )
        for name, content in invalid_grammar:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assert_assessment(
                    assessment,
                    result="NOT_ACCEPTABLE",
                    mode=None,
                    issues=("FIELD_UNKNOWN",),
                )

    def test_state_gate_matrix_is_exhaustive(self) -> None:
        active = fixture_text("active_fenced.md")
        capped = fixture_text("active_ordinary_cap.md")
        closed = fixture_text("closed_ordinary.md")
        cases: list[tuple[str, str, bool, str]] = []
        for state in ("ACTIVE", "RESTRICTED"):
            for gate in ("GO", "GO UNDER CAP", "HOLD", "CAP", "BLOCK"):
                if gate == "GO UNDER CAP":
                    content = capped.replace(
                        "Current State**: ACTIVE",
                        f"Current State**: {state}",
                    )
                else:
                    content = (
                        active.replace(
                            "Current State: ACTIVE",
                            f"Current State: {state}",
                        )
                        .replace("Current Gate: GO", f"Current Gate: {gate}")
                    )
                allowed = state == "ACTIVE" or gate in ("HOLD", "CAP", "BLOCK")
                cases.append((state, gate, allowed, content))
        for gate in ("GO", "GO UNDER CAP", "HOLD", "CAP", "BLOCK"):
            content = closed.replace("Current Gate: HOLD", f"Current Gate: {gate}")
            allowed = gate in ("HOLD", "CAP", "BLOCK")
            cases.append(("CLOSED", gate, allowed, content))

        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                active,
            )
            for state, gate, allowed, content in cases:
                with self.subTest(state=state, gate=gate):
                    handoff_path.write_text(
                        content.replace(
                            "__REPO_ROOT__",
                            str(repository.resolve()),
                        ),
                        encoding="utf-8",
                    )

                    assessment = assess(repository, handoff_path)

                    if allowed:
                        self.assert_assessment(
                            assessment,
                            result="ACCEPTABLE",
                            mode=(
                                "CLOSED_STATE"
                                if state == "CLOSED"
                                else "ACTIVE_TRANSFER"
                            ),
                            issues=(),
                        )
                    else:
                        self.assertEqual(
                            "NOT_ACCEPTABLE",
                            assessment.result,
                        )
                        self.assertIn(
                            "STATE_GATE_CONFLICT",
                            assessment.issue_codes,
                        )

    def test_issue_staging_is_exclusive_for_absent_and_unparseable_fields(
        self,
    ) -> None:
        base = fixture_text("active_fenced.md")
        receiving_block = (
            "Receiving AI Owns:\n"
            "- [VAL-1] VALIDATION; owner=RECEIVER; subject=handoff_guard\n"
        )
        cases = (
            (
                "absent_owner",
                base.replace("Next Owner: Codex Executor\n", "", 1),
                ("REQUIRED_FIELD_ABSENT",),
            ),
            (
                "unknown_next_action",
                replaced_once(
                    base,
                    (
                        "Next Authorized Action: VALIDATE [VAL-1]; "
                        "closure=VAL-1; branch=main"
                    ),
                    "Next Authorized Action: UNKNOWN",
                ),
                ("FIELD_UNKNOWN",),
            ),
            (
                "absent_receiving_ownership",
                base.replace(receiving_block, "", 1),
                ("REQUIRED_FIELD_ABSENT",),
            ),
            (
                "unknown_receiving_ownership",
                base.replace(
                    receiving_block,
                    "Receiving AI Owns: UNKNOWN\n",
                    1,
                ),
                ("FIELD_UNKNOWN",),
            ),
            (
                "invalid_repository_facet_skips_other_facet_relation",
                replaced_once(
                    base,
                    "Repo Root: __REPO_ROOT__",
                    (
                        "Repo Root: /definitely/not/the/repository\n"
                        "Repository Identity: UNKNOWN"
                    ),
                ),
                ("FIELD_UNKNOWN",),
            ),
            (
                "undefined_retained_reference",
                replaced_once(base, "RETAIN: VAL-1", "RETAIN: OTHER"),
                ("FIELD_UNKNOWN",),
            ),
            (
                "undefined_action_closure_reference",
                base.replace("closure=VAL-1", "closure=OTHER"),
                ("FIELD_UNKNOWN",),
            ),
            (
                "undefined_cap_reference",
                replaced_once(
                    fixture_text("active_ordinary_cap.md"),
                    "CAP_TO: VAL-1",
                    "CAP_TO: OTHER",
                ),
                ("FIELD_UNKNOWN",),
            ),
            (
                "repeated_retained_reference",
                replaced_once(
                    base,
                    "RETAIN: VAL-1",
                    "RETAIN: VAL-1, VAL-1",
                ),
                ("FIELD_UNKNOWN",),
            ),
            (
                "repeated_cap_reference",
                replaced_once(
                    fixture_text("active_ordinary_cap.md"),
                    "CAP_TO: VAL-1",
                    "CAP_TO: VAL-1, VAL-1",
                ),
                ("FIELD_UNKNOWN",),
            ),
        )
        for name, content, expected_issues in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assert_assessment(
                    assessment,
                    result="NOT_ACCEPTABLE",
                    mode=None,
                    issues=expected_issues,
                )

    def test_repository_target_and_multi_issue_relations_are_exactly_ordered(
        self,
    ) -> None:
        base = fixture_text("active_fenced.md")
        cases = (
            (
                "target_mismatch",
                replaced_once(base, "Target Layer: V13", "Target Layer: V14"),
                ("TARGET_LAYER_MISMATCH",),
            ),
            (
                "root_mismatch",
                replaced_once(
                    base,
                    "Repo Root: __REPO_ROOT__",
                    "Repo Root: /definitely/not/the/repository",
                ),
                ("REPOSITORY_MISMATCH",),
            ),
            (
                "slug_case_mismatch",
                replaced_once(
                    base,
                    "Repo Root: __REPO_ROOT__",
                    "Repository Identity: Example/handoff-fixture",
                ),
                ("REPOSITORY_MISMATCH",),
            ),
            (
                "repository_none",
                replaced_once(
                    base,
                    "Repo Root: __REPO_ROOT__",
                    "Repo Root: none",
                ),
                ("FIELD_UNKNOWN",),
            ),
        )
        for name, content, expected_issues in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assert_assessment(
                    assessment,
                    result="NOT_ACCEPTABLE",
                    mode=None,
                    issues=expected_issues,
                )

        identity_only = replaced_once(
            base,
            "Repo Root: __REPO_ROOT__",
            f"Repository Identity: {REPOSITORY_SLUG}",
        )
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                identity_only,
            )
            run_git(repository, "remote", "remove", "origin")

            assessment = assess(repository, handoff_path)

        self.assert_assessment(
            assessment,
            result="NOT_ACCEPTABLE",
            mode=None,
            issues=("REPOSITORY_REFERENCE_UNRESOLVED",),
        )

        multi_issue = (
            base.replace("Target Layer: V13", "Target Layer: V14")
            .replace("Active Branch: main", "Active Branch: other")
            .replace("Next Owner: Codex Executor", "Next Owner: Other Executor")
        )
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                multi_issue,
            )

            assessment = assess(repository, handoff_path)

        self.assertEqual("NOT_ACCEPTABLE", assessment.result)
        self.assertEqual(
            tuple(
                code
                for code in ISSUE_CODES
                if code in assessment.issue_codes
            ),
            assessment.issue_codes,
        )
        self.assertEqual(
            (
                "TARGET_LAYER_MISMATCH",
                "ACTIVE_BRANCH_MISMATCH",
                "ACTION_BRANCH_MISMATCH",
                "OWNER_MISMATCH",
            ),
            assessment.issue_codes,
        )

    def test_finite_grammar_consumes_inline_tails_and_facet_order(
        self,
    ) -> None:
        base = fixture_text("active_fenced.md")
        completion_block = (
            "Completion Line:\n"
            "OPEN:\n"
            "- [DONE-1] TEST; subject=handoff_guard; expected=passes"
        )
        inline_completion = replaced_once(
            base,
            completion_block,
            (
                "Completion Line: OPEN:\n"
                "- [DONE-1] TEST; subject=handoff_guard; expected=passes"
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                inline_completion,
            )

            assessment = assess(repository, handoff_path)

            self.assert_assessment(
                assessment,
                result="ACCEPTABLE",
                mode="ACTIVE_TRANSFER",
                issues=(),
            )

        invalid_cases = (
            (
                "ignored_second_action",
                replaced_once(
                    base,
                    (
                        "Next Authorized Action: VALIDATE [VAL-1]; "
                        "closure=VAL-1; branch=main"
                    ),
                    (
                        "Next Authorized Action: VALIDATE [VAL-1]; "
                        "closure=VAL-1; branch=main\n"
                        "MERGE [VAL-1]"
                    ),
                ),
            ),
            (
                "reversed_action_facets",
                base.replace(
                    "; closure=VAL-1; branch=main",
                    "; branch=main; closure=VAL-1",
                ),
            ),
            (
                "unbulleted_multiple_work_items",
                replaced_once(
                    base,
                    (
                        "Receiving AI Owns:\n"
                        "- [VAL-1] VALIDATION; owner=RECEIVER; "
                        "subject=handoff_guard"
                    ),
                    (
                        "Receiving AI Owns:\n"
                        "[VAL-1] VALIDATION; owner=RECEIVER; "
                        "subject=handoff_guard\n"
                        "[VAL-2] VALIDATION; owner=RECEIVER; "
                        "subject=other"
                    ),
                ),
            ),
            (
                "target_slash_alternative",
                replaced_once(
                    base,
                    "Target Layer: V13",
                    "Target Layer: V13/V14",
                ),
            ),
            (
                "owner_slash_alternative",
                replaced_once(
                    base,
                    "Next Owner: Codex Executor",
                    "Next Owner: Codex Executor/Other Executor",
                ),
            ),
        )
        for name, content in invalid_cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assertEqual("NOT_ACCEPTABLE", assessment.result)
                self.assertTrue(
                    {"FIELD_UNKNOWN", "FIELD_AMBIGUOUS"}
                    .intersection(assessment.issue_codes)
                )

        malformed = replaced_once(
            base,
            "Current Gate: GO",
            "Current Gate:: GO",
        )
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                malformed,
            )

            assessment = assess(repository, handoff_path)

        self.assert_assessment(
            assessment,
            result="INVALID",
            mode=None,
            issues=("MALFORMED_REPRESENTATION",),
        )

    def test_missing_closure_and_none_rules_are_conjunctive(self) -> None:
        base = fixture_text("active_fenced.md")
        closed = fixture_text("closed_ordinary.md")
        cases = (
            (
                "next_action_none_in_active_transfer",
                replaced_once(
                    base,
                    (
                        "Next Authorized Action: VALIDATE [VAL-1]; "
                        "closure=VAL-1; branch=main"
                    ),
                    "Next Authorized Action: none",
                ),
                "ACTION_RELATION_UNPROVEN",
            ),
            (
                "none_in_active_transfer",
                replaced_once(
                    base,
                    (
                        "First One Action: VALIDATE [VAL-1]; "
                        "closure=VAL-1; branch=main"
                    ),
                    "First One Action: none",
                ),
                "FIRST_ACTION_NONE_ACTIVE",
            ),
            (
                "action_omits_closure",
                base.replace("; closure=VAL-1", ""),
                "MISSING_CLOSURE_NO_ACTION",
            ),
            (
                "met_with_open_closure",
                replaced_once(base, "OPEN:", "MET:"),
                "COMPLETION_CLOSURE_CONFLICT",
            ),
            (
                "conditional_none_is_not_closed_none",
                replaced_once(
                    closed,
                    "Active Branch: none",
                    "Active Branch: none unless reopened",
                ),
                "FIELD_UNKNOWN",
            ),
            (
                "closed_with_remaining_closure",
                replaced_once(
                    closed,
                    "Missing Closure: none",
                    (
                        "Missing Closure:\n"
                        "- [VAL-1] VALIDATION; owner=RECEIVER; "
                        "subject=handoff_guard"
                    ),
                ),
                "CLOSED_STATE_INCOMPLETE",
            ),
        )
        for name, content, issue in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assertEqual("NOT_ACCEPTABLE", assessment.result)
                self.assertIn(issue, assessment.issue_codes)

    def test_history_cannot_complete_current_and_two_current_records_conflict(
        self,
    ) -> None:
        two_records = (
            fixture_text("active_fenced.md")
            + "\n"
            + fixture_text("active_fenced.md")
        )
        cases = (
            (
                "historical_tail_cannot_fill_gap",
                fixture_text("current_history_gap.md"),
                "REQUIRED_FIELD_ABSENT",
            ),
            (
                "two_operative_records",
                two_records,
                "CURRENT_RECORD_AMBIGUOUS",
            ),
        )
        for name, content, issue in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assertEqual("NOT_ACCEPTABLE", assessment.result)
                self.assertIn(issue, assessment.issue_codes)

    def test_malformed_and_unsafe_inputs_are_invalid(self) -> None:
        active = fixture_text("active_fenced.md")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenarios: list[tuple[str, Path, Path, str]] = []

            missing_parent = root / "missing_case"
            missing_parent.mkdir()
            repository, _ = create_repository(missing_parent, active)
            scenarios.append(
                (
                    "missing",
                    repository,
                    repository / "handoff" / "missing.md",
                    "INPUT_MISSING",
                )
            )

            outside_parent = root / "outside_case"
            outside_parent.mkdir()
            repository, _ = create_repository(outside_parent, active)
            outside = outside_parent / "SECRET_OUTSIDE_PATH.md"
            outside.write_text("SECRET_OUTSIDE_CONTENT\n", encoding="utf-8")
            scenarios.append(
                ("outside", repository, outside, "INPUT_OUTSIDE_ROOT")
            )

            traversal_parent = root / "traversal_case"
            traversal_parent.mkdir()
            repository, handoff_path = create_repository(
                traversal_parent,
                active,
            )
            traversal = (
                handoff_path.parent
                / ".."
                / handoff_path.parent.name
                / handoff_path.name
            )
            scenarios.append(
                (
                    "explicit_traversal",
                    repository,
                    traversal,
                    "INPUT_OUTSIDE_ROOT",
                )
            )

            symlink_parent = root / "symlink_case"
            symlink_parent.mkdir()
            repository, handoff_path = create_repository(
                symlink_parent,
                active,
            )
            target = symlink_parent / "SECRET_SYMLINK_TARGET.md"
            target.write_text(active, encoding="utf-8")
            handoff_path.unlink()
            try:
                handoff_path.symlink_to(target)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            scenarios.append(
                ("symlink", repository, handoff_path, "INPUT_SYMLINK")
            )

            directory_parent = root / "directory_case"
            directory_parent.mkdir()
            repository, handoff_path = create_repository(
                directory_parent,
                active,
            )
            scenarios.append(
                (
                    "directory",
                    repository,
                    handoff_path.parent,
                    "INPUT_NOT_REGULAR",
                )
            )

            oversize_parent = root / "oversize_case"
            oversize_parent.mkdir()
            repository, handoff_path = create_repository(
                oversize_parent,
                active,
            )
            handoff_path.write_bytes(b"x" * (MAX_INPUT_BYTES + 1))
            scenarios.append(
                ("oversize", repository, handoff_path, "INPUT_TOO_LARGE")
            )

            utf8_parent = root / "utf8_case"
            utf8_parent.mkdir()
            repository, handoff_path = create_repository(utf8_parent, active)
            handoff_path.write_bytes(b"\xffSECRET_INVALID_UTF8")
            scenarios.append(
                ("invalid_utf8", repository, handoff_path, "INPUT_INVALID_UTF8")
            )

            for name, repository, handoff_path, issue in scenarios:
                with self.subTest(name=name):
                    assessment = assess(repository, handoff_path)

                    self.assert_assessment(
                        assessment,
                        result="INVALID",
                        mode=None,
                    )
                    self.assertIn(issue, assessment.issue_codes)

    def test_malformed_candidate_fence_and_empty_field_are_invalid(self) -> None:
        active = fixture_text("active_fenced.md")
        cases = (
            (
                "unclosed_candidate_fence",
                active.rsplit("```", 1)[0],
            ),
            (
                "empty_recognized_field",
                replaced_once(
                    active,
                    "Current Gate: GO",
                    "Current Gate:",
                ),
            ),
        )
        for name, content in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )

                assessment = assess(repository, handoff_path)

                self.assert_assessment(
                    assessment,
                    result="INVALID",
                    mode=None,
                )
                self.assertIn(
                    "MALFORMED_REPRESENTATION",
                    assessment.issue_codes,
                )

    def test_well_formed_unsupported_document_is_not_malformed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                "# Notes\n\nNo handoff record is present.\n",
            )

            assessment = assess(repository, handoff_path)

        self.assert_assessment(
            assessment,
            result="NOT_ACCEPTABLE",
            mode=None,
            issues=("UNSUPPORTED_VARIANT",),
        )

    def test_results_render_safely_without_raw_values_paths_or_errors(
        self,
    ) -> None:
        sentinel_value = "SECRET_RAW_VALUE_SENTINEL"
        sentinel_path = "SECRET_PATH_SENTINEL.md"
        content = replaced_once(
            fixture_text("active_fenced.md"),
            "Current Gate: GO",
            f"Current Gate: {sentinel_value}",
        )
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                content,
                handoff_name=sentinel_path,
            )

            assessment = assess(repository, handoff_path)
            combined = (
                repr(assessment)
                + render_json(assessment)
                + render_text(assessment)
            )

        self.assertEqual("NOT_ACCEPTABLE", assessment.result)
        self.assertNotIn(sentinel_value, combined)
        self.assertNotIn(sentinel_path, combined)
        self.assertNotIn(str(repository), combined)

    def test_recognized_filesystem_errors_do_not_echo_exception_text(
        self,
    ) -> None:
        sentinel = "SECRET_OPERATING_SYSTEM_ERROR"
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                fixture_text("active_fenced.md"),
            )
            with patch(
                "decision_os.handoff_acceptance.os.open",
                side_effect=OSError(sentinel),
            ):
                assessment = assess(repository, handoff_path)

        combined = (
            repr(assessment)
            + render_json(assessment)
            + render_text(assessment)
        )
        self.assert_assessment(
            assessment,
            result="INVALID",
            mode=None,
        )
        self.assertIn("INPUT_UNREADABLE", assessment.issue_codes)
        self.assertNotIn(sentinel, combined)

    def test_assessment_is_read_only_for_all_artifact_result_classes(
        self,
    ) -> None:
        cases = (
            ("acceptable", fixture_text("active_fenced.md")),
            (
                "not_acceptable",
                replaced_once(
                    fixture_text("active_fenced.md"),
                    "Current Gate: GO",
                    "Current Gate: UNKNOWN",
                ),
            ),
            (
                "invalid",
                fixture_text("active_fenced.md").rsplit("```", 1)[0],
            ),
        )
        for name, content in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repository, handoff_path = create_repository(
                    Path(directory),
                    content,
                )
                before = artifact_snapshot(repository, handoff_path)

                assess(repository, handoff_path)

                self.assertEqual(
                    before,
                    artifact_snapshot(repository, handoff_path),
                )

    def test_repetition_json_and_text_are_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                fixture_text("active_fenced.md"),
            )

            first = assess(repository, handoff_path)
            second = assess(repository, handoff_path)
            first_json = render_json(first)
            second_json = render_json(second)
            first_text = render_text(first)
            second_text = render_text(second)

        self.assertEqual(first, second)
        self.assertEqual(first_json.encode("utf-8"), second_json.encode("utf-8"))
        self.assertEqual(first_text.encode("utf-8"), second_text.encode("utf-8"))
        self.assertTrue(first_json.endswith("\n"))
        self.assertTrue(first_text.endswith("\n"))
        self.assertEqual(
            [
                "schema_version",
                "result",
                "mode",
                "issue_codes",
                "approval_performed",
                "authority_granted",
                "writes_performed",
                "remote_freshness",
            ],
            list(json.loads(first_json)),
        )
        self.assertEqual(
            (
                "HANDOFF_ACCEPTANCE: ACCEPTABLE\n"
                "MODE: ACTIVE_TRANSFER\n"
                "ISSUES: NONE\n"
                "APPROVAL_PERFORMED: NO\n"
                "AUTHORITY_GRANTED: NO\n"
                "WRITES_PERFORMED: NO\n"
                "REMOTE_FRESHNESS: NOT_CHECKED\n"
            ),
            first_text,
        )

    def test_changed_snapshot_uses_process_error_not_mixed_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                fixture_text("active_fenced.md"),
            )
            from decision_os.handoff_acceptance import (
                _capture_repository_snapshot,
            )

            opening = _capture_repository_snapshot(repository)
            closing = replace(opening, head="0" * 40)
            with patch(
                "decision_os.handoff_acceptance._capture_repository_snapshot",
                side_effect=(opening, closing),
            ):
                with self.assertRaises(HandoffProcessError) as raised:
                    assess(repository, handoff_path)

        self.assertEqual("UNSTABLE_SNAPSHOT", raised.exception.code)
        self.assertNotIn(str(repository), repr(raised.exception))

    def test_actual_input_mutation_and_missing_input_appearance_are_unstable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                fixture_text("active_fenced.md"),
            )
            from decision_os.handoff_acceptance import _select_record

            def mutate_after_parse(text: str):
                selected = _select_record(text)
                handoff_path.write_text(text + "\n", encoding="utf-8")
                return selected

            with patch(
                "decision_os.handoff_acceptance._select_record",
                side_effect=mutate_after_parse,
            ):
                with self.assertRaises(HandoffProcessError) as raised:
                    assess(repository, handoff_path)

            self.assertEqual("UNSTABLE_SNAPSHOT", raised.exception.code)

        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository, original = create_repository(
                parent,
                fixture_text("active_fenced.md"),
            )
            missing = original.with_name("appears.md")
            from decision_os.handoff_acceptance import (
                _capture_repository_snapshot,
            )

            calls = 0

            def capture_and_create(root: Path):
                nonlocal calls
                calls += 1
                if calls == 2:
                    missing.write_text(
                        fixture_text("active_fenced.md").replace(
                            "__REPO_ROOT__",
                            str(repository.resolve()),
                        ),
                        encoding="utf-8",
                    )
                return _capture_repository_snapshot(root)

            with patch(
                "decision_os.handoff_acceptance._capture_repository_snapshot",
                side_effect=capture_and_create,
            ):
                with self.assertRaises(HandoffProcessError) as raised:
                    assess(repository, missing)

            self.assertEqual("UNSTABLE_SNAPSHOT", raised.exception.code)

        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                fixture_text("active_fenced.md"),
            )
            handoff_path.write_bytes(b"A" * (MAX_INPUT_BYTES + 1))
            from decision_os.handoff_acceptance import (
                _capture_repository_snapshot,
            )

            calls = 0

            def capture_and_rewrite_oversize(root: Path):
                nonlocal calls
                calls += 1
                if calls == 2:
                    handoff_path.write_bytes(
                        b"B" * (MAX_INPUT_BYTES + 2)
                    )
                return _capture_repository_snapshot(root)

            with patch(
                "decision_os.handoff_acceptance._capture_repository_snapshot",
                side_effect=capture_and_rewrite_oversize,
            ):
                with self.assertRaises(HandoffProcessError) as raised:
                    assess(repository, handoff_path)

            self.assertEqual("UNSTABLE_SNAPSHOT", raised.exception.code)

    def test_physical_repo_root_accepts_equivalent_lexical_handoff_path(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                fixture_text("active_fenced.md"),
            )

            assessment = assess_handoff(
                repo_root=repository.resolve(),
                handoff_path=handoff_path,
                expected_receiver=EXPECTED_RECEIVER,
                expected_target_layer=EXPECTED_TARGET_LAYER,
            )

        self.assert_assessment(
            assessment,
            result="ACCEPTABLE",
            mode="ACTIVE_TRANSFER",
            issues=(),
        )

    def test_repository_root_symlink_is_resolved_above_handoff_boundary(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository, handoff_path = create_repository(
                parent,
                fixture_text("active_fenced.md"),
            )
            repository_alias = parent / "repository-alias"
            try:
                repository_alias.symlink_to(
                    repository,
                    target_is_directory=True,
                )
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            for candidate in (
                handoff_path,
                repository_alias / "handoff" / handoff_path.name,
            ):
                with self.subTest(handoff_spelling=candidate.parent.name):
                    assessment = assess_handoff(
                        repo_root=repository_alias,
                        handoff_path=candidate,
                        expected_receiver=EXPECTED_RECEIVER,
                        expected_target_layer=EXPECTED_TARGET_LAYER,
                    )

                    self.assert_assessment(
                        assessment,
                        result="ACCEPTABLE",
                        mode="ACTIVE_TRANSFER",
                        issues=(),
                    )

    def test_unexpected_opening_failure_and_invalid_trusted_scalar_are_safe(
        self,
    ) -> None:
        sentinel = "SECRET_OPENING_FAILURE"
        with tempfile.TemporaryDirectory() as directory:
            repository, handoff_path = create_repository(
                Path(directory),
                fixture_text("active_fenced.md"),
            )
            before = artifact_snapshot(repository, handoff_path)
            with patch(
                "decision_os.handoff_acceptance._capture_repository_snapshot",
                side_effect=RuntimeError(sentinel),
            ):
                with self.assertRaises(HandoffProcessError) as raised:
                    assess(repository, handoff_path)
            after = artifact_snapshot(repository, handoff_path)

        self.assertEqual("INTERNAL_ERROR", raised.exception.code)
        self.assertNotIn(sentinel, repr(raised.exception))
        self.assertIsNone(raised.exception.__cause__)
        self.assertIsNone(raised.exception.__context__)
        self.assertEqual(before, after)

        for value in ("Codex\nExecutor", "Codex\u2028Executor", b"Codex"):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(HandoffProcessError) as raised:
                    assess_handoff(
                        repo_root="unused",
                        handoff_path="unused",
                        expected_receiver=value,
                        expected_target_layer=EXPECTED_TARGET_LAYER,
                    )
                self.assertEqual("USAGE_ERROR", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
