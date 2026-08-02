from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from decision_os.acceleration.codex_adapter import (
    CodexReadEvidence,
    CodexRunResult,
)
from decision_os.companion.field_notes_adapter import FieldNoteCodexRunResult
from decision_os.companion.field_notes_controller import (
    FieldNotesCompanionController,
)
from decision_os.companion.field_notes_model import (
    FIELD_NOTE_SCHEMA_VERSION,
    FieldNoteProposalGate,
    compile_draft,
)


def proposal() -> dict[str, object]:
    return {
        "title": "Approval byte binding",
        "value_level": 3,
        "source_model_class": "stronger",
        "target_model_class": "lower-cost",
        "trigger_terms": ["bounded approval", "exact file create"],
        "scope": {
            "task_family": "governed-file-write",
            "path_prefixes": ["docs/"],
            "exclude_terms": ["bulk rewrite"],
        },
        "body": {
            "trigger": "Use when one exact new file is proposed.",
            "reusable_structure": (
                "Bind path, bytes, digest, and precondition."
            ),
            "scope": "One repository-relative Markdown file.",
            "do_not_apply_when": (
                "Do not use for updates or multiple files."
            ),
            "procedure": "Compile, approve once, create new, read back.",
            "acceptance": "The readback bytes and SHA-256 match.",
            "evidence": (
                "The source Run completed successfully; reuse is untested."
            ),
            "remaining_unknowns": (
                "External adoption and lower-model reuse remain unknown."
            ),
        },
    }


def create_repository(parent: Path) -> Path:
    repository = parent / "repo"
    repository.mkdir()
    completed = subprocess.run(
        ("git", "init", "-q", str(repository)),
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    (repository / "seed.txt").write_text("seed\n", encoding="utf-8")
    return repository


class FieldNotesModelTests(unittest.TestCase):
    def test_compile_is_byte_deterministic_and_canonical(self) -> None:
        draft = compile_draft(
            proposal(),
            source_run_id="run_001",
            created_at="2026-08-02T12:34:56Z",
            field_note_id="fn_fixed_identity",
        )
        repeated = compile_draft(
            proposal(),
            source_run_id="run_001",
            created_at="2026-08-02T12:34:56Z",
            field_note_id="fn_fixed_identity",
        )
        self.assertEqual(draft.markdown, repeated.markdown)
        self.assertEqual(
            draft.sha256,
            hashlib.sha256(draft.markdown).hexdigest(),
        )
        self.assertTrue(
            draft.relative_path.startswith(
                ".decision-os/field-notes/"
                "2026-08-02-approval-byte-binding-"
            )
        )
        first, metadata, end, *_ = draft.markdown.decode("utf-8").splitlines()
        self.assertEqual(
            first,
            "<!-- decision-os-field-note-metadata:v0.1",
        )
        self.assertEqual(end, "-->")
        parsed = json.loads(metadata)
        self.assertEqual(parsed["schema_version"], FIELD_NOTE_SCHEMA_VERSION)
        self.assertEqual(parsed["status"], "CANDIDATE")
        self.assertEqual(
            parsed["maturity_evidence"],
            {
                "different_task_reuse": None,
                "first_verified_reuse": None,
            },
        )

    def test_one_shot_accepts_at_most_one_candidate(self) -> None:
        gate = FieldNoteProposalGate("run_001")
        self.assertEqual(
            gate.propose(proposal()),
            (True, "proposal_accepted"),
        )
        original = gate.accepted
        self.assertEqual(
            gate.propose(proposal()),
            (False, "proposal_attempt_already_consumed"),
        )
        self.assertIs(gate.accepted, original)

    def test_invalid_first_attempt_consumes_gate(self) -> None:
        gate = FieldNoteProposalGate("run_001")
        invalid = proposal()
        invalid["value_level"] = 4
        self.assertEqual(
            gate.propose(invalid),
            (False, "proposal_schema_invalid"),
        )
        self.assertIsNone(gate.accepted)
        self.assertEqual(
            gate.propose(proposal()),
            (False, "proposal_attempt_already_consumed"),
        )

    def test_level_three_requires_stronger_to_lower_cost(self) -> None:
        invalid = proposal()
        invalid["target_model_class"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            compile_draft(
                invalid,
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )


class FieldNotesControllerTests(unittest.TestCase):
    def _controller(
        self,
        root: Path,
    ) -> tuple[FieldNotesCompanionController, Path]:
        repository = create_repository(root)
        controller = FieldNotesCompanionController(
            state_path=root / "state.json",
            picker_script=root / "picker.scpt",
        )
        controller.select_repository(repository)
        return controller, repository

    @staticmethod
    def _eligible_result(draft: object) -> FieldNoteCodexRunResult:
        return FieldNoteCodexRunResult(
            run_id="run_001",
            normal_terminal=True,
            status="NORMAL_TERMINAL",
            error_type=None,
            turn_status="completed",
            runtime_identity=None,
            checkpoint_outcomes=(),
            final_message="Completed.",
            file_actions=(),
            read_evidence=(
                CodexReadEvidence(
                    path="seed.txt",
                    byte_count=5,
                    sha256=hashlib.sha256(b"seed\n").hexdigest(),
                    repository_identity="head",
                    status="succeeded",
                ),
            ),
            field_note_proposal=draft,
        )

    def test_failed_or_evidence_free_run_does_not_expose_candidate(self) -> None:
        draft = compile_draft(
            proposal(),
            source_run_id="run_001",
            created_at="2026-08-02T12:34:56Z",
            field_note_id="fn_fixed_identity",
        )
        result = CodexRunResult(
            run_id="run_001",
            normal_terminal=True,
            status="NORMAL_TERMINAL",
            error_type=None,
            turn_status="completed",
            runtime_identity=None,
            checkpoint_outcomes=(),
            final_message="Completed.",
            file_actions=(),
            read_evidence=(),
        )
        self.assertIsNone(
            FieldNotesCompanionController._eligible_draft(result)
        )
        failed = self._eligible_result(draft)
        failed = FieldNoteCodexRunResult(
            **{
                **failed.__dict__,
                "normal_terminal": False,
                "status": "ABNORMAL_TERMINAL",
            }
        )
        self.assertIsNone(
            FieldNotesCompanionController._eligible_draft(failed)
        )

    def test_skip_changes_no_repository_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller, repository = self._controller(root)
            draft = compile_draft(
                proposal(),
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )
            before = sorted(
                path.relative_to(repository).as_posix()
                for path in repository.rglob("*")
                if ".git" not in path.parts
            )
            with controller._condition:
                controller._run["state"] = "completed"
                controller._field_note_draft = draft
                controller._run["field_note"] = draft.public_candidate()
            snapshot = controller.field_note_skip()
            after = sorted(
                path.relative_to(repository).as_posix()
                for path in repository.rglob("*")
                if ".git" not in path.parts
            )
            self.assertEqual(before, after)
            self.assertEqual(snapshot["run"]["field_note"], {"state": "skipped"})

    def test_save_requires_approval_then_creates_exact_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller, repository = self._controller(root)
            draft = compile_draft(
                proposal(),
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )
            with controller._condition:
                controller._run["state"] = "completed"
                controller._field_note_draft = draft
                controller._run["field_note"] = draft.public_candidate()
            approval = controller.field_note_save()
            target = repository / draft.relative_path
            self.assertFalse(target.exists())
            surface = approval["run"]["field_note"]["approval"]
            self.assertEqual(surface["action"], "CREATE")
            self.assertEqual(surface["precondition"], "MUST_NOT_EXIST")
            self.assertEqual(surface["content_sha256"], draft.sha256)
            saved = controller.field_note_approval("allow_once")
            self.assertEqual(target.read_bytes(), draft.markdown)
            self.assertEqual(
                hashlib.sha256(target.read_bytes()).hexdigest(),
                draft.sha256,
            )
            self.assertEqual(
                saved["run"]["field_note"],
                {"state": "saved", "path": draft.relative_path},
            )


if __name__ == "__main__":
    unittest.main()
