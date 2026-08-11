from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from decision_os.acceleration.model import git_output, repository_id
from decision_os.companion import field_notes_reconnect as broad_reconnect
from decision_os.companion import field_notes_selective_reconnect as selective
from decision_os.companion.field_notes_adapter import FieldNotesCodexAdapter
from decision_os.companion.field_notes_controller import FieldNotesCompanionController
from decision_os.companion.field_notes_model import canonical_json, compile_draft
from decision_os.companion.field_notes_reconnect import (
    MAX_DIRECTORY_ENTRIES,
    prepare_field_note_reconnect,
)
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteServingPolicyBoundary,
    bind_field_note_structure,
    project_field_note_a3_status,
    summarize_field_note_maturity,
)
from decision_os.companion.field_notes_selective_reconnect import (
    SELECTIVE_RECONNECT_EDGE_PATH,
    SELECTIVE_RECONNECT_SCHEMA,
    SelectiveReconnectApplicability,
    SelectiveReconnectCurrentBinding,
    SelectiveReconnectEdge,
    SelectiveReconnectIdentity,
    SelectiveReconnectSourceAnchor,
    SelectiveReconnectTargetBinding,
    persist_selective_reconnect_edge,
    resolve_selective_reconnect,
)


AS_OF = "2026-08-11T10:00:00+09:00"
SOURCE_COMMIT = "07f20eb5bbea1e49d0b5f60fc4962c45ddcd3704"
SOURCE_PATH = "notes/v11/Decision_OS_V11___Forget_for_Future.pdf"
SOURCE_BLOB = "7939df5c03cad37c92cbbaab9418f7bf0ce0db7e"
SOURCE_SHA256 = "58f089213c85553fe0451ce574a172a43c6cd5243ad716c784acf6a269268356"
STRUCTURE_TEXT = "Preserve the exact causal guard and keep its route HOLD."


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def identity(value: str) -> SelectiveReconnectIdentity:
    return SelectiveReconnectIdentity(
        identity=value,
        sha256=digest_bytes(value.encode("utf-8")),
    )


def proposal(
    *,
    title: str,
    reusable_structure: str = STRUCTURE_TEXT,
    trigger_terms: list[str] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "value_level": 1,
        "source_model_class": "UNKNOWN",
        "target_model_class": "UNKNOWN",
        "trigger_terms": trigger_terms or ["selective reconnect", "scale edge"],
        "scope": {
            "task_family": "selective-reconnect-edge-1-01",
            "path_prefixes": ["decision_os/companion"],
            "exclude_terms": [],
        },
        "body": {
            "trigger": "Use only for the exact bound Goal and remaining gap.",
            "reusable_structure": reusable_structure,
            "scope": "One current Goal/gap and one exact historical structure.",
            "do_not_apply_when": "Do not apply after any identity becomes stale.",
            "procedure": "Reopen the exact byte range, then check applicability.",
            "acceptance": "Recall remains separate from serving and selection.",
            "evidence": "One exact source anchor and one exact Note binding.",
            "remaining_unknowns": "Current usefulness remains independently gated.",
        },
    }


def write_note(
    repository: Path,
    *,
    title: str,
    field_note_id: str,
    source_run_id: str,
    reusable_structure: str = STRUCTURE_TEXT,
    trigger_terms: list[str] | None = None,
):
    draft = compile_draft(
        proposal(
            title=title,
            reusable_structure=reusable_structure,
            trigger_terms=trigger_terms,
        ),
        source_run_id=source_run_id,
        created_at="2026-08-10T12:00:00Z",
        field_note_id=field_note_id,
    )
    path = repository / draft.relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(draft.markdown)
    return draft


def rehash_record(record: dict[str, object]) -> dict[str, object]:
    payload = {key: value for key, value in record.items() if key != "edge_sha256"}
    record["edge_sha256"] = digest_bytes(
        canonical_json(payload).encode("utf-8")
    )
    return record


class SelectiveReconnectFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = Path(self.temporary.name) / "repo"
        self.repository.mkdir()
        (self.repository / "seed.txt").write_text("seed\n", encoding="utf-8")
        commands = (
            ("git", "init", "-q", str(self.repository)),
            ("git", "-C", str(self.repository), "add", "seed.txt"),
            (
                "git",
                "-C",
                str(self.repository),
                "-c",
                "user.name=Selective Reconnect Test",
                "-c",
                "user.email=selective-reconnect@example.invalid",
                "commit",
                "-qm",
                "seed",
            ),
        )
        for command in commands:
            completed = subprocess.run(command, capture_output=True, text=True)
            if completed.returncode != 0:
                raise AssertionError(completed.stderr)
        self.repository_id = repository_id(self.repository)
        self.as_of_commit = git_output(self.repository, "rev-parse", "HEAD")
        self.draft = write_note(
            self.repository,
            title="Selective reconnect scale target",
            field_note_id="fn_selective_reconnect_scale_target",
            source_run_id="run_historical_target",
        )
        self.note_path = self.repository / self.draft.relative_path
        self.note = FieldNoteIdentity(
            note_path=self.draft.relative_path,
            field_note_id=self.draft.field_note_id,
            note_sha256=self.draft.sha256,
            origin_run_id=self.draft.source_run_id,
        )
        structure_bytes = STRUCTURE_TEXT.encode("utf-8")
        start = self.draft.markdown.index(structure_bytes)
        self.structure = bind_field_note_structure(
            self.note,
            self.draft.markdown,
            structure_id="v11-selective-reconnect-causal-guard",
            start_byte=start,
            end_byte=start + len(structure_bytes),
        )
        self.current = SelectiveReconnectCurrentBinding(
            goal=identity("goal:13-119-selective-reconnect"),
            remaining_gap=identity("gap:scale-addressable-exact-reconnect"),
            current_gate="GO",
            protected_object=identity("protected:human-seat-and-current-gate"),
            authority_boundary=identity("authority:shin-decision-owner"),
            repository_id=self.repository_id,
            as_of_commit=self.as_of_commit,
            as_of=AS_OF,
        )
        evidence_path = "evidence/selective-reconnect-source-anchor.txt"
        evidence = self.repository / evidence_path
        evidence.parent.mkdir(parents=True)
        evidence_bytes = selective.selective_reconnect_source_evidence_bytes(
            repository_id="shin4141/decision-os-paper",
            source_commit=SOURCE_COMMIT,
            source_path=SOURCE_PATH,
            source_blob=SOURCE_BLOB,
            source_sha256=SOURCE_SHA256,
            evidence_path=evidence_path,
            as_of=AS_OF,
        )
        evidence.write_bytes(evidence_bytes)
        self.source = SelectiveReconnectSourceAnchor(
            repository_id="shin4141/decision-os-paper",
            source_commit=SOURCE_COMMIT,
            source_path=SOURCE_PATH,
            source_blob=SOURCE_BLOB,
            source_sha256=SOURCE_SHA256,
            evidence_path=evidence_path,
            evidence_sha256=digest_bytes(evidence_bytes),
            as_of=AS_OF,
        )
        scope_payload = {
            "task_family": self.draft.task_family,
            "path_prefixes": list(self.draft.path_prefixes),
            "exclude_terms": list(self.draft.exclude_terms),
            "repository": "current",
        }
        self.scope = SelectiveReconnectIdentity(
            identity=self.draft.task_family,
            sha256=digest_bytes(canonical_json(scope_payload).encode("utf-8")),
        )
        self.target = SelectiveReconnectTargetBinding(
            structure=self.structure,
            source=self.source,
            scope=self.scope,
            stop_conditions=("Stop if any exact target identity changes.",),
            recheck_conditions=("Recheck source evidence and current Gate.",),
            unresolved_delta="Current applicability and usefulness remain separate.",
            reentry_path=self.note.note_path,
        )
        self.serving_policy = FieldNoteServingPolicyBoundary(note=self.note)
        self.applicability = SelectiveReconnectApplicability(
            current=self.current,
            target_binding_sha256=self.target.binding_sha256,
            source=self.source,
            scope=self.scope,
            target_current_gate="HOLD",
            target_status_as_of=AS_OF,
            evidence_stale=False,
            serving_policy=self.serving_policy,
        )
        self.edge = SelectiveReconnectEdge(
            current=self.current,
            target=self.target,
            applicability=self.applicability,
        )

    @property
    def edge_path(self) -> Path:
        return self.repository / SELECTIVE_RECONNECT_EDGE_PATH

    def persist(self, edge: SelectiveReconnectEdge | None = None) -> Path:
        return persist_selective_reconnect_edge(
            self.repository,
            edge or self.edge,
        )

    def resolve(
        self,
        *,
        current: SelectiveReconnectCurrentBinding | None = None,
    ):
        return resolve_selective_reconnect(
            self.repository,
            current=current or self.current,
        )

    def replace_persisted_edge(self, edge: SelectiveReconnectEdge) -> Path:
        if self.edge_path.exists() or self.edge_path.is_symlink():
            self.edge_path.unlink()
        return self.persist(edge)

    def write_edge_records(
        self,
        *edges: SelectiveReconnectEdge,
    ) -> Path:
        if self.edge_path.exists() or self.edge_path.is_symlink():
            self.edge_path.unlink()
        self.edge_path.parent.mkdir(parents=True, exist_ok=True)
        self.edge_path.write_bytes(
            b"".join(
                canonical_json(edge.as_dict()).encode("utf-8") + b"\n"
                for edge in edges
            )
        )
        return self.edge_path

    def test_257_valid_notes_fail_broad_reconnect_but_edge_recalls_exact_target(
        self,
    ) -> None:
        for index in range(MAX_DIRECTORY_ENTRIES):
            write_note(
                self.repository,
                title=f"Historical unrelated note {index:03d}",
                field_note_id=f"fn_unrelated_{index:03d}",
                source_run_id=f"run_unrelated_{index:03d}",
                reusable_structure=f"Unrelated structure sentinel {index:03d}.",
                trigger_terms=[f"unrelated {index:03d}", "historical only"],
            )
        store = self.repository / ".decision-os" / "field-notes"
        self.assertEqual(MAX_DIRECTORY_ENTRIES + 1, len(list(store.iterdir())))
        self.persist()
        ordinary = prepare_field_note_reconnect(
            self.repository,
            "selective reconnect scale edge",
            "run_scale_baseline",
        )
        self.assertEqual("NO_MATCH", ordinary.receipt.state)
        self.assertEqual("directory_entry_limit", ordinary.receipt.failure_reason)
        self.assertEqual(MAX_DIRECTORY_ENTRIES + 1, ordinary.receipt.metadata_entries_seen)
        self.assertEqual(0, ordinary.receipt.metadata_bytes_read)
        self.assertEqual(0, ordinary.receipt.full_note_bytes_read)
        self.assertIsNone(ordinary.envelope)

        opened: list[str] = []
        exact_repository_files: list[str] = []
        exact_read = selective.read_exact_field_note
        exact_file_read = selective._read_exact_repository_file

        def observe_exact_read(repository: Path, relative_path: str):
            opened.append(relative_path)
            return exact_read(repository, relative_path)

        def observe_exact_file(repository: Path, relative_path: str, **kwargs):
            exact_repository_files.append(relative_path)
            return exact_file_read(repository, relative_path, **kwargs)

        with (
            patch.object(
                broad_reconnect,
                "_score",
                side_effect=AssertionError("broad relevance score used"),
            ),
            patch.object(
                broad_reconnect.os,
                "scandir",
                side_effect=AssertionError("broad Field Note scan used"),
            ),
            patch.object(
                selective,
                "read_exact_field_note",
                side_effect=observe_exact_read,
            ),
            patch.object(
                selective,
                "_read_exact_repository_file",
                side_effect=observe_exact_file,
            ),
            patch.object(
                os,
                "listdir",
                side_effect=AssertionError("directory list used"),
            ),
            patch.object(
                Path,
                "iterdir",
                side_effect=AssertionError("directory iteration used"),
            ),
            patch.object(
                Path,
                "glob",
                side_effect=AssertionError("glob used"),
            ),
            patch.object(
                Path,
                "rglob",
                side_effect=AssertionError("recursive glob used"),
            ),
        ):
            recalled = self.resolve()

        self.assertEqual("RECALLED", recalled.receipt.state)
        self.assertEqual("HOLD", recalled.receipt.applicability_gate)
        self.assertEqual(STRUCTURE_TEXT.encode("utf-8"), recalled.structure_bytes)
        self.assertEqual(self.structure.binding_sha256, recalled.receipt.structure_binding_sha256)
        self.assertEqual(self.edge.edge_sha256, recalled.receipt.edge_sha256)
        self.assertEqual([self.note.note_path, self.note.note_path], opened)
        self.assertEqual(
            [
                SELECTIVE_RECONNECT_EDGE_PATH,
                self.source.evidence_path,
                SELECTIVE_RECONNECT_EDGE_PATH,
                self.source.evidence_path,
            ],
            exact_repository_files,
        )
        self.assertEqual(0, recalled.receipt.field_note_directory_entries_seen)
        self.assertEqual(0, recalled.receipt.unrelated_field_note_files_opened)
        self.assertFalse(recalled.receipt.broad_scan_performed)
        self.assertNotIn("Unrelated structure sentinel", recalled.envelope or "")
        self.assertNotIn("# Selective reconnect scale target", recalled.envelope or "")
        self.assertNotIn("One current Goal/gap and one exact", recalled.envelope or "")
        self.assertIn("Current Goal Gate: GO", recalled.envelope or "")
        self.assertIn("Target current-use Gate: HOLD", recalled.envelope or "")

    def test_target_and_edge_identity_are_deterministic(self) -> None:
        self.persist()
        first = self.resolve()
        second = self.resolve()
        self.assertEqual(first.receipt.as_dict(), second.receipt.as_dict())
        self.assertEqual(first.structure_bytes, second.structure_bytes)
        self.assertEqual(self.edge.edge_sha256, first.receipt.edge_sha256)
        self.assertEqual(self.target.binding_sha256, first.receipt.target_binding_sha256)
        self.assertEqual(self.structure.binding_sha256, first.receipt.structure_binding_sha256)
        self.assertEqual(self.note.note_path, first.receipt.target_note_path)
        self.assertEqual(self.note.field_note_id, first.receipt.target_field_note_id)
        self.assertEqual(self.note.note_sha256, first.receipt.target_note_sha256)

    def test_zero_matching_edge_holds_without_opening_a_target(self) -> None:
        with patch.object(
            selective,
            "read_exact_field_note",
            side_effect=AssertionError("target opened"),
        ):
            result = self.resolve()
        self.assertEqual("DELAY_HOLD", result.receipt.state)
        self.assertEqual("ZERO_TARGETS", result.receipt.failure_reason)
        self.assertEqual("HOLD", result.receipt.applicability_gate)
        self.assertIsNone(result.structure_bytes)
        self.assertEqual(0, result.receipt.target_note_read_attempts)

    def test_multiple_matching_edges_hold_without_ranking_or_target_read(self) -> None:
        self.persist()
        alternate_bytes = b"Recall remains separate from serving and selection."
        alternate_start = self.draft.markdown.index(alternate_bytes)
        alternate_structure = bind_field_note_structure(
            self.note,
            self.draft.markdown,
            structure_id="alternate-current-gap-target",
            start_byte=alternate_start,
            end_byte=alternate_start + len(alternate_bytes),
        )
        alternate_target = replace(
            self.target,
            structure=alternate_structure,
        )
        alternate_applicability = replace(
            self.applicability,
            target_binding_sha256=alternate_target.binding_sha256,
            serving_policy=FieldNoteServingPolicyBoundary(
                note=alternate_target.structure.note
            ),
        )
        alternate_edge = SelectiveReconnectEdge(
            current=self.current,
            target=alternate_target,
            applicability=alternate_applicability,
        )
        self.assertNotEqual(self.edge.target.binding_sha256, alternate_target.binding_sha256)
        lines = (
            canonical_json(self.edge.as_dict()).encode("utf-8")
            + b"\n"
            + canonical_json(alternate_edge.as_dict()).encode("utf-8")
            + b"\n"
        )
        self.edge_path.write_bytes(lines)
        with (
            patch.object(
                broad_reconnect,
                "_score",
                side_effect=AssertionError("ranker used"),
            ),
            patch.object(
                selective,
                "read_exact_field_note",
                side_effect=AssertionError("target opened"),
            ),
        ):
            result = self.resolve()
        self.assertEqual("DELAY_HOLD", result.receipt.state)
        self.assertEqual("MULTIPLE_TARGETS", result.receipt.failure_reason)
        self.assertEqual(2, result.receipt.edge_records_seen)
        self.assertIsNone(result.structure_bytes)

    def test_stale_target_and_stale_evidence_hold(self) -> None:
        self.persist()
        self.note_path.write_bytes(self.note_path.read_bytes() + b"\n")
        stale_target = self.resolve()
        self.assertEqual("DELAY_HOLD", stale_target.receipt.state)
        self.assertEqual("STALE_TARGET", stale_target.receipt.failure_reason)
        self.assertIsNone(stale_target.structure_bytes)

        self.note_path.write_bytes(self.draft.markdown)
        stale_applicability = replace(self.applicability, evidence_stale=True)
        self.write_edge_records(
            replace(self.edge, applicability=stale_applicability)
        )
        stale_evidence = self.resolve()
        self.assertEqual("DELAY_HOLD", stale_evidence.receipt.state)
        self.assertEqual("STALE_EVIDENCE", stale_evidence.receipt.failure_reason)
        self.assertIsNone(stale_evidence.structure_bytes)

    def test_source_identity_and_evidence_failure_hold(self) -> None:
        self.persist()
        evidence_path = self.repository / self.source.evidence_path
        source_cases = {
            "repository": replace(self.source, repository_id="different/source"),
            "commit": replace(self.source, source_commit="0" * 40),
            "source_path": replace(self.source, source_path="notes/v11/different.pdf"),
            "source_blob": replace(self.source, source_blob="0" * 40),
            "source_sha256": replace(self.source, source_sha256="0" * 64),
        }
        for label, wrong_source in source_cases.items():
            with self.subTest(label=label):
                self.write_edge_records(
                    replace(
                        self.edge,
                        applicability=replace(
                            self.applicability,
                            source=wrong_source,
                        ),
                    )
                )
                mismatched = self.resolve()
                self.assertEqual("DELAY_HOLD", mismatched.receipt.state)
                self.assertEqual(
                    "SOURCE_IDENTITY_MISMATCH",
                    mismatched.receipt.failure_reason,
                )
                self.assertEqual(1, mismatched.receipt.target_note_read_attempts)

        evidence_cases = {
            "path": replace(self.source, evidence_path="evidence/different.txt"),
            "digest": replace(self.source, evidence_sha256="0" * 64),
        }
        for label, wrong_source in evidence_cases.items():
            with self.subTest(label=label):
                self.write_edge_records(
                    replace(
                        self.edge,
                        applicability=replace(
                            self.applicability,
                            source=wrong_source,
                        ),
                    )
                )
                mismatched = self.resolve()
                self.assertEqual(
                    "SOURCE_EVIDENCE_FAILURE",
                    mismatched.receipt.failure_reason,
                )

        wrong_as_of = replace(
            self.source,
            as_of="2026-08-11T10:01:00+09:00",
        )
        self.write_edge_records(
            replace(
                self.edge,
                applicability=replace(self.applicability, source=wrong_as_of),
            )
        )
        as_of_result = self.resolve()
        self.assertEqual("AS_OF_MISMATCH", as_of_result.receipt.failure_reason)

        self.replace_persisted_edge(self.edge)
        original = evidence_path.read_bytes()
        outside = self.repository.parent / "outside-evidence.txt"
        outside.write_bytes(original)
        for case in ("changed", "missing", "symlink"):
            with self.subTest(evidence_file=case):
                if evidence_path.exists() or evidence_path.is_symlink():
                    evidence_path.unlink()
                evidence_path.write_bytes(original)
                if case == "changed":
                    evidence_path.write_bytes(b"changed source evidence\n")
                elif case == "missing":
                    evidence_path.unlink()
                else:
                    evidence_path.unlink()
                    evidence_path.symlink_to(outside)
                failed = self.resolve()
                self.assertEqual("DELAY_HOLD", failed.receipt.state)
                self.assertEqual(
                    "SOURCE_EVIDENCE_FAILURE",
                    failed.receipt.failure_reason,
                )
                self.assertIsNone(failed.structure_bytes)

    def test_current_side_identity_mismatch_matrix_holds_before_target_read(self) -> None:
        cases = {
            "goal": (
                replace(self.current, goal=identity("goal:different")),
                "GOAL_IDENTITY_MISMATCH",
            ),
            "gap": (
                replace(self.current, remaining_gap=identity("gap:different")),
                "GAP_IDENTITY_MISMATCH",
            ),
            "gate": (
                replace(self.current, current_gate="HOLD"),
                "CURRENT_GATE_MISMATCH",
            ),
            "protected_object": (
                replace(
                    self.current,
                    protected_object=identity("protected:different"),
                ),
                "PROTECTED_OBJECT_MISMATCH",
            ),
            "authority": (
                replace(
                    self.current,
                    authority_boundary=identity("authority:different"),
                ),
                "AUTHORITY_BOUNDARY_MISMATCH",
            ),
            "as_of": (
                replace(self.current, as_of="2026-08-11T10:01:00+09:00"),
                "AS_OF_MISMATCH",
            ),
        }
        for label, (edge_current, reason) in cases.items():
            with self.subTest(label=label):
                self.write_edge_records(
                    replace(self.edge, current=edge_current)
                )
                with patch.object(
                    selective,
                    "read_exact_field_note",
                    side_effect=AssertionError("target opened"),
                ):
                    result = self.resolve()
                self.assertEqual("DELAY_HOLD", result.receipt.state)
                self.assertEqual(reason, result.receipt.failure_reason)
                self.assertEqual(0, result.receipt.target_note_read_attempts)

    def test_current_repository_as_of_and_changed_during_read_hold(self) -> None:
        self.persist()
        wrong_repository = self.resolve(
            current=replace(
                self.current,
                repository_id="repo:v1:" + "0" * 64,
            )
        )
        self.assertEqual(
            "CURRENT_REPOSITORY_MISMATCH",
            wrong_repository.receipt.failure_reason,
        )
        self.assertEqual(0, wrong_repository.receipt.edge_read_attempts)

        wrong_commit = self.resolve(
            current=replace(self.current, as_of_commit="0" * 40)
        )
        self.assertEqual("AS_OF_MISMATCH", wrong_commit.receipt.failure_reason)
        self.assertEqual(0, wrong_commit.receipt.edge_read_attempts)

        with patch.object(
            selective,
            "_repository_identity",
            side_effect=(
                (self.repository_id, self.as_of_commit),
                (self.repository_id, "0" * 40),
            ),
        ):
            changed = self.resolve()
        self.assertEqual("DELAY_HOLD", changed.receipt.state)
        self.assertEqual("AS_OF_MISMATCH", changed.receipt.failure_reason)
        self.assertEqual(2, changed.receipt.target_note_read_attempts)
        self.assertEqual(2, changed.receipt.source_evidence_read_attempts)

    def test_cross_read_swap_fails_closed_without_partial_payload(self) -> None:
        self.persist()
        evidence_path = self.repository / self.source.evidence_path
        valid_evidence = evidence_path.read_bytes()
        evidence_path.write_bytes(b"invalid before target read\n")
        exact_read = selective.read_exact_field_note
        calls = 0

        def swap_after_first_target(repository: Path, relative_path: str):
            nonlocal calls
            exact = exact_read(repository, relative_path)
            calls += 1
            if calls == 1:
                self.note_path.write_bytes(self.draft.markdown + b"\n")
                evidence_path.write_bytes(valid_evidence)
            return exact

        with patch.object(
            selective,
            "read_exact_field_note",
            side_effect=swap_after_first_target,
        ):
            result = self.resolve()
        self.assertEqual("DELAY_HOLD", result.receipt.state)
        self.assertEqual(
            "UNSTABLE_RECOVERY_WINDOW",
            result.receipt.failure_reason,
        )
        self.assertEqual(2, result.receipt.target_note_read_attempts)
        self.assertIsNone(result.target)
        self.assertIsNone(result.structure_bytes)
        self.assertIsNone(result.envelope)
        with self.assertRaises(ValueError):
            selective.SelectiveReconnectResult(
                receipt=result.receipt,
                structure_bytes=b"partial payload must be rejected",
            )

    def test_alternating_note_and_evidence_versions_fail_closed(self) -> None:
        self.persist()
        evidence_path = self.repository / self.source.evidence_path
        valid_evidence = evidence_path.read_bytes()
        invalid_evidence = b"invalid alternating evidence\n"
        evidence_path.write_bytes(invalid_evidence)
        exact_note_read = selective.read_exact_field_note
        exact_file_read = selective._read_exact_repository_file
        edge_reads = 0

        def flip_after_note(repository: Path, relative_path: str):
            exact = exact_note_read(repository, relative_path)
            self.note_path.write_bytes(self.draft.markdown + b"\n")
            evidence_path.write_bytes(valid_evidence)
            return exact

        def flip_after_second_edge(
            repository: Path,
            relative_path: str,
            **kwargs,
        ):
            nonlocal edge_reads
            exact = exact_file_read(repository, relative_path, **kwargs)
            if relative_path == SELECTIVE_RECONNECT_EDGE_PATH:
                edge_reads += 1
                if edge_reads == 2:
                    self.note_path.write_bytes(self.draft.markdown)
                    evidence_path.write_bytes(invalid_evidence)
            return exact

        with (
            patch.object(
                selective,
                "read_exact_field_note",
                side_effect=flip_after_note,
            ),
            patch.object(
                selective,
                "_read_exact_repository_file",
                side_effect=flip_after_second_edge,
            ),
        ):
            result = self.resolve()
        self.assertEqual("DELAY_HOLD", result.receipt.state)
        self.assertEqual(
            "UNSTABLE_RECOVERY_WINDOW",
            result.receipt.failure_reason,
        )
        self.assertIsNone(result.structure_bytes)

    def test_source_evidence_record_binds_the_declared_source_tuple(self) -> None:
        false_source = replace(self.source, source_commit="0" * 40)
        false_target = replace(self.target, source=false_source)
        false_applicability = replace(
            self.applicability,
            target_binding_sha256=false_target.binding_sha256,
            source=false_source,
        )
        self.write_edge_records(
            SelectiveReconnectEdge(
                current=self.current,
                target=false_target,
                applicability=false_applicability,
            )
        )
        result = self.resolve()
        self.assertEqual("DELAY_HOLD", result.receipt.state)
        self.assertEqual(
            "SOURCE_EVIDENCE_FAILURE",
            result.receipt.failure_reason,
        )
        self.assertIsNone(result.structure_bytes)

    def test_applicability_scope_and_binding_mismatch_hold_after_recovery(self) -> None:
        self.persist()
        other_note = replace(
            self.note,
            field_note_id="fn_other_serving_identity",
        )
        cases = {
            "scope": (
                replace(self.applicability, scope=identity("scope:different")),
                "SCOPE_MISMATCH",
            ),
            "target_binding": (
                replace(self.applicability, target_binding_sha256="0" * 64),
                "TARGET_IDENTITY_MISMATCH",
            ),
            "applicability_goal": (
                replace(
                    self.applicability,
                    current=replace(
                        self.current,
                        goal=identity("goal:stale-applicability"),
                    ),
                ),
                "GOAL_IDENTITY_MISMATCH",
            ),
            "applicability_gap": (
                replace(
                    self.applicability,
                    current=replace(
                        self.current,
                        remaining_gap=identity("gap:stale-applicability"),
                    ),
                ),
                "GAP_IDENTITY_MISMATCH",
            ),
            "applicability_gate": (
                replace(
                    self.applicability,
                    current=replace(self.current, current_gate="HOLD"),
                ),
                "CURRENT_GATE_MISMATCH",
            ),
            "applicability_protected_object": (
                replace(
                    self.applicability,
                    current=replace(
                        self.current,
                        protected_object=identity("protected:stale-applicability"),
                    ),
                ),
                "PROTECTED_OBJECT_MISMATCH",
            ),
            "applicability_authority": (
                replace(
                    self.applicability,
                    current=replace(
                        self.current,
                        authority_boundary=identity("authority:stale-applicability"),
                    ),
                ),
                "AUTHORITY_BOUNDARY_MISMATCH",
            ),
            "applicability_repository": (
                replace(
                    self.applicability,
                    current=replace(self.current, repository_id="repo:v1:" + "0" * 64),
                ),
                "CURRENT_REPOSITORY_MISMATCH",
            ),
            "applicability_commit": (
                replace(
                    self.applicability,
                    current=replace(self.current, as_of_commit="0" * 40),
                ),
                "AS_OF_MISMATCH",
            ),
            "applicability_as_of": (
                replace(
                    self.applicability,
                    current=replace(
                        self.current,
                        as_of="2026-08-11T10:01:00+09:00",
                    ),
                ),
                "AS_OF_MISMATCH",
            ),
            "target_status_as_of": (
                replace(
                    self.applicability,
                    target_status_as_of="2026-08-11T10:01:00+09:00",
                ),
                "AS_OF_MISMATCH",
            ),
            "serving_policy_note": (
                replace(
                    self.applicability,
                    serving_policy=FieldNoteServingPolicyBoundary(note=other_note),
                ),
                "TARGET_IDENTITY_MISMATCH",
            ),
        }
        for label, (applicability, reason) in cases.items():
            with self.subTest(label=label):
                self.write_edge_records(
                    replace(self.edge, applicability=applicability)
                )
                result = self.resolve()
                self.assertEqual("DELAY_HOLD", result.receipt.state)
                self.assertEqual(reason, result.receipt.failure_reason)
                self.assertEqual(1, result.receipt.target_note_read_attempts)
                self.assertIsNone(result.structure_bytes)

    def test_recalled_hold_target_preserves_all_non_activation_boundaries(self) -> None:
        self.persist()
        serving_before = self.serving_policy.as_dict()
        maturity_before = project_field_note_a3_status(
            summarize_field_note_maturity(self.note, (), ())
        ).as_dict()

        def repository_snapshot() -> dict[str, str]:
            return {
                path.relative_to(self.repository).as_posix(): digest_bytes(
                    path.read_bytes()
                )
                for path in self.repository.rglob("*")
                if path.is_file()
            }

        files_before = repository_snapshot()
        with (
            patch.object(
                FieldNotesCompanionController,
                "start_run",
                side_effect=AssertionError("Worker dispatched"),
            ),
            patch.object(
                FieldNotesCodexAdapter,
                "run",
                side_effect=AssertionError("adapter dispatched"),
            ),
        ):
            result = self.resolve()
        self.assertEqual("RECALLED", result.receipt.state)
        self.assertNotEqual("SELECTED", result.receipt.state)
        self.assertEqual("HOLD", result.receipt.applicability_gate)
        self.assertEqual("HOLD", self.applicability.target_current_gate)
        self.assertEqual(self.target, result.target)
        self.assertEqual(serving_before, self.serving_policy.as_dict())
        self.assertEqual(
            maturity_before,
            project_field_note_a3_status(
                summarize_field_note_maturity(self.note, (), ())
            ).as_dict(),
        )
        self.assertEqual(files_before, repository_snapshot())
        self.assertEqual("DELAY", result.receipt.serving_policy_derivation)
        self.assertIsNone(result.receipt.automatic_injection)
        self.assertFalse(result.receipt.serving_created)
        self.assertFalse(result.receipt.selection_created)
        self.assertFalse(result.receipt.promotion_created)
        self.assertFalse(result.receipt.canon_created)
        self.assertFalse(result.receipt.authority_granted)
        self.assertEqual(0, result.receipt.worker_runs_dispatched)
        self.assertEqual("UNSET", result.receipt.promotion_policy_status)
        self.assertEqual(
            ("TOPMOST_CANONICAL", "ADVISORY_FIELD_NOTE"),
            result.receipt.authority_precedence,
        )
        with self.assertRaises(TypeError):
            resolve_selective_reconnect(
                self.repository,
                current=self.current,
                applicability=replace(
                    self.applicability,
                    target_current_gate="GO",
                ),
            )
        self.write_edge_records(
            replace(
                self.edge,
                applicability=replace(
                    self.applicability,
                    target_current_gate="GO",
                ),
            )
        )
        unsupported_route = self.resolve()
        self.assertEqual("DELAY_HOLD", unsupported_route.receipt.state)
        self.assertEqual(
            "UNSUPPORTED_APPLICABILITY_ROUTE",
            unsupported_route.receipt.failure_reason,
        )

    def test_restart_replay_recovers_same_target_and_same_or_safer_route(self) -> None:
        self.persist()
        first = self.resolve()
        payload = {
            "repository": str(self.repository),
            "current": self.current.as_dict(),
        }
        replay_script = r'''
import hashlib
import json
from pathlib import Path
import sys
from decision_os.companion.field_notes_selective_reconnect import (
    SelectiveReconnectCurrentBinding,
    SelectiveReconnectIdentity,
    resolve_selective_reconnect,
)

data = json.loads(sys.stdin.read())
def exact(value):
    return SelectiveReconnectIdentity(value["identity"], value["sha256"])
current_data = data["current"]
current = SelectiveReconnectCurrentBinding(
    goal=exact(current_data["goal"]),
    remaining_gap=exact(current_data["remaining_gap"]),
    current_gate=current_data["current_gate"],
    protected_object=exact(current_data["protected_object"]),
    authority_boundary=exact(current_data["authority_boundary"]),
    repository_id=current_data["repository_id"],
    as_of_commit=current_data["as_of_commit"],
    as_of=current_data["as_of"],
)
result = resolve_selective_reconnect(
    Path(data["repository"]),
    current=current,
)
print(json.dumps({
    "receipt": result.receipt.as_dict(),
    "target": result.target.as_dict() if result.target else None,
    "structure_sha256": hashlib.sha256(result.structure_bytes or b"").hexdigest(),
}, sort_keys=True, separators=(",", ":")))
'''
        completed = subprocess.run(
            (sys.executable, "-c", replay_script),
            input=canonical_json(payload),
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        replay = json.loads(completed.stdout)
        self.assertEqual(first.receipt.as_dict(), replay["receipt"])
        self.assertEqual(self.target.as_dict(), replay["target"])
        self.assertEqual(
            digest_bytes(first.structure_bytes or b""),
            replay["structure_sha256"],
        )
        self.assertEqual("HOLD", replay["receipt"]["applicability_gate"])

        self.note_path.write_bytes(self.note_path.read_bytes() + b"\n")
        safer = self.resolve()
        self.assertEqual("DELAY_HOLD", safer.receipt.state)
        self.assertEqual("HOLD", safer.receipt.applicability_gate)

    def test_corrupted_edge_variants_fail_safely_without_target_read(self) -> None:
        self.persist()
        valid = self.edge.as_dict()
        bad_digest = dict(valid)
        bad_digest["edge_sha256"] = "0" * 64
        unknown = dict(valid)
        unknown["unexpected"] = True
        rehash_record(unknown)
        bad_binding = json.loads(canonical_json(valid))
        bad_binding["target"]["structure"]["binding_sha256"] = "0" * 64
        rehash_record(bad_binding)
        traversal = json.loads(canonical_json(valid))
        traversal["target"]["source"]["evidence_path"] = "../outside"
        rehash_record(traversal)
        duplicate = canonical_json(valid)[:-1] + ',"schema":"duplicate"}'
        valid_line = canonical_json(valid).encode("utf-8") + b"\n"
        variants = {
            "malformed": b"{\n",
            "noncanonical": (json.dumps(valid) + "\n").encode("utf-8"),
            "bad_edge_digest": canonical_json(bad_digest).encode("utf-8") + b"\n",
            "unknown_key": canonical_json(unknown).encode("utf-8") + b"\n",
            "bad_binding": canonical_json(bad_binding).encode("utf-8") + b"\n",
            "traversal": canonical_json(traversal).encode("utf-8") + b"\n",
            "duplicate_key": duplicate.encode("utf-8") + b"\n",
            "mixed_valid_and_corrupt": valid_line + b"{\n",
            "oversized": b"x" * (selective.MAX_EDGE_FILE_BYTES + 1),
        }
        for label, data in variants.items():
            with self.subTest(label=label):
                self.edge_path.write_bytes(data)
                with patch.object(
                    selective,
                    "read_exact_field_note",
                    side_effect=AssertionError("target opened"),
                ):
                    result = self.resolve()
                self.assertEqual("DELAY_HOLD", result.receipt.state)
                self.assertEqual("CORRUPTED_EDGE", result.receipt.failure_reason)
                self.assertIsNone(result.structure_bytes)

        outside = self.repository.parent / "outside-edge.jsonl"
        outside.write_bytes(valid_line)
        self.edge_path.unlink()
        self.edge_path.symlink_to(outside)
        with patch.object(
            selective,
            "read_exact_field_note",
            side_effect=AssertionError("target opened"),
        ):
            symlinked = self.resolve()
        self.assertEqual("DELAY_HOLD", symlinked.receipt.state)
        self.assertEqual("CORRUPTED_EDGE", symlinked.receipt.failure_reason)

    def test_persist_failure_does_not_wedge_the_single_edge_slot(self) -> None:
        inconsistent = replace(
            self.edge,
            applicability=replace(
                self.applicability,
                target_binding_sha256="0" * 64,
            ),
        )
        with self.assertRaises(ValueError):
            self.persist(inconsistent)
        self.assertFalse(self.edge_path.exists())

        write = selective.os.write
        writes = 0

        def fail_after_one_byte(descriptor: int, data) -> int:
            nonlocal writes
            writes += 1
            if writes == 1:
                return write(descriptor, data[:1])
            raise OSError("simulated partial edge write")

        with (
            patch.object(selective.os, "write", side_effect=fail_after_one_byte),
            self.assertRaises(ValueError),
        ):
            self.persist()
        self.assertFalse(self.edge_path.exists())
        reconnect_directory = self.edge_path.parent
        self.assertEqual(
            [],
            [
                path.name
                for path in reconnect_directory.iterdir()
                if path.name.startswith(".edge-v1-")
            ],
        )

        self.persist()
        recalled = self.resolve()
        self.assertEqual("RECALLED", recalled.receipt.state)

    def test_persisted_schema_round_trip_contains_only_the_bounded_edge(self) -> None:
        with self.assertRaises(ValueError):
            replace(self.current, as_of="20260811T100000+09:00")
        first_path = self.persist()
        second_path = self.persist()
        self.assertEqual(first_path, second_path)
        raw = self.edge_path.read_bytes()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(1, len(raw.splitlines()))
        record = json.loads(raw)
        self.assertEqual(SELECTIVE_RECONNECT_SCHEMA, record["schema"])
        self.assertEqual(self.current.as_dict(), record["current"])
        self.assertEqual(self.target.as_dict(), record["target"])
        self.assertEqual(self.applicability.as_dict(), record["applicability"])
        self.assertEqual(self.edge.edge_sha256, record["edge_sha256"])
        self.assertEqual(canonical_json(record).encode("utf-8") + b"\n", raw)
        recalled = self.resolve()
        self.assertEqual(self.target, recalled.target)
        self.assertEqual(
            ("Stop if any exact target identity changes.",),
            recalled.target.stop_conditions if recalled.target else (),
        )
        self.assertEqual(
            ("Recheck source evidence and current Gate.",),
            recalled.target.recheck_conditions if recalled.target else (),
        )
        self.assertEqual(
            "Current applicability and usefulness remain separate.",
            recalled.target.unresolved_delta if recalled.target else None,
        )
        self.assertEqual(
            self.note.note_path,
            recalled.target.reentry_path if recalled.target else None,
        )


if __name__ == "__main__":
    unittest.main()
