from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from decision_os.companion.field_notes_controller import (
    FieldNotesCompanionController,
)
from decision_os.companion.field_notes_creator_live_entrypoint import (
    CYCLE_AUTHORIZATION_OBSERVED_AT,
    EXPECTED_EXECUTION_AUTHORITY,
    EXPECTED_FREEZE_AUTHORITY,
    IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT,
    NOT_DURABLY_PERSISTED,
    RUN_1_TASK,
    RUN_1_TASK_SHA256,
    RUN_2_TASK,
    RUN_2_TASK_SHA256,
    CreatorLiveCycle005Entrypoint,
    CreatorLiveCycle005Spec,
    CreatorLiveEntrypointError,
    CreatorLiveP0Result,
    compile_run_2_output_artifact,
    compile_run_2_output_artifact_audited,
)
from decision_os.companion.field_notes_creator_live import (
    FieldNoteCreatorLiveOutputArtifactIdentity,
    FieldNoteCreatorLiveRun2OutputIdentity,
    FieldNoteCreatorLiveValidationError,
)
from decision_os.companion.field_notes_model import canonical_json
from decision_os.companion.field_notes_reuse import FieldNoteIdentity
from decision_os.companion.field_notes_server import configure_field_notes_server
from decision_os.companion.server import CompanionServer
from decision_os.companion.field_notes_whole_flow import (
    FieldNoteSourceRepositoryIdentity,
)
from tests.test_companion_controller import ScriptedFactory, create_repository


_DIGEST = "a4" * 32


class _NoopWorker:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.started = False

    def start(self) -> None:
        self.started = True


class _FailingWorker(_NoopWorker):
    def start(self) -> None:
        raise RuntimeError("fixture interruption")


class _Controller:
    def __init__(self, repository: Path) -> None:
        self.repository = repository

    def snapshot(self) -> dict[str, object]:
        return {"repository": {"path": str(self.repository)}}


class _ReadyEntrypoint(CreatorLiveCycle005Entrypoint):
    def _p0(self, _base_snapshot: object) -> CreatorLiveP0Result:
        binding = {
            "schema": "test.creator-live-binding",
            "cycle_key": "cycle-005",
            "contract": {
                "profile": "ORDINARY_USER_PATH_CONTRACT_APPROVED_CANDIDATE_V0_1",
                "title": "Ordinary User Path Contract v0.1 — APPROVED CANDIDATE",
                "source_byte_count": 11_039,
                "source_sha256": "1" * 64,
                "wrapper_sha256": "2" * 64,
                "interpretation_sha256": "3" * 64,
                "ordinary_contract_execution_authority": (
                    EXPECTED_EXECUTION_AUTHORITY
                ),
                "guided_intake_freeze_authority_state": (
                    EXPECTED_FREEZE_AUTHORITY
                ),
            },
            "tasks": {
                "run_1": {
                    "byte_count": 832,
                    "sha256": RUN_1_TASK_SHA256,
                },
                "run_2": {
                    "byte_count": 856,
                    "sha256": RUN_2_TASK_SHA256,
                },
            },
            "authorizations": {
                "implementation_observed_at": (
                    IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT
                ),
            },
            "historical_boundary": {
                "cycle_key": "cycle-004",
                "state": "FAILED",
                "failure_boundary": "A1_CAPTURE",
                "failure_code": "A1_CAPTURE_CHRONOLOGY_INVALID",
            },
        }
        return CreatorLiveP0Result(True, None, binding, _DIGEST)


class _FakeHTTPEntrypoint:
    def __init__(self, _controller: object) -> None:
        self.started: list[str] = []
        self.mutation_blocked = False

    def snapshot(self, _base: object) -> dict[str, object]:
        return {
            "cycle_key": "cycle-005",
            "state": "READY",
            "stage": "P0",
            "p0": {"ready": True, "failure_code": None},
            "launch_binding_sha256": _DIGEST,
            "binding": {
                "repository": {"head": "a" * 40},
                "contract": {
                    "source_sha256": "b" * 64,
                    "source_byte_count": 11_039,
                    "profile": "ORDINARY_USER_PATH_CONTRACT_APPROVED_CANDIDATE_V0_1",
                    "title": "Ordinary User Path Contract v0.1 — APPROVED CANDIDATE",
                    "ordinary_contract_execution_authority": (
                        EXPECTED_EXECUTION_AUTHORITY
                    ),
                    "guided_intake_freeze_authority_state": (
                        EXPECTED_FREEZE_AUTHORITY
                    ),
                },
                "authorizations": {
                    "cycle_observed_at": CYCLE_AUTHORIZATION_OBSERVED_AT,
                    "implementation_observed_at": (
                        IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT
                    ),
                },
                "runtime": {
                    "provider": "openai",
                    "account_type": "chatgpt",
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "ultra",
                    "service_tier": "priority",
                    "codex_cli_version": "0.146.0-alpha.3.1",
                },
                "tasks": {
                    "run_1": {
                        "byte_count": 832,
                        "sha256": RUN_1_TASK_SHA256,
                        "lane": "A1_ONLY",
                    },
                    "run_2": {
                        "byte_count": 856,
                        "sha256": RUN_2_TASK_SHA256,
                        "lane": "EXACT_A2_ONLY",
                    },
                },
                "historical_boundary": {
                    "cycle_key": "cycle-004",
                    "state": "FAILED",
                    "failure_boundary": "A1_CAPTURE",
                    "failure_code": "A1_CAPTURE_CHRONOLOGY_INVALID",
                },
            },
            "identities": None,
            "receipt_sha256": None,
            "manifest_sha256": None,
            "failure_code": None,
            "one_attempt_no_retry": True,
            "replacement_permitted": False,
            "storage_occupied": False,
            "start_allowed": True,
        }

    def start(self, digest: str) -> dict[str, object]:
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise CreatorLiveEntrypointError(
                "LAUNCH_BINDING_INVALID",
                http_status=400,
            )
        if digest != _DIGEST:
            raise CreatorLiveEntrypointError("LAUNCH_BINDING_STALE")
        self.started.append(digest)
        return self.snapshot({})


def _commit_repository(root: Path) -> Path:
    repository = root / "repository"
    repository.mkdir()
    commands = (
        ("git", "init", "-q", "-b", "main"),
        ("git", "config", "user.email", "tests@example.invalid"),
        ("git", "config", "user.name", "Decision OS Tests"),
    )
    for command in commands:
        subprocess.run(command, cwd=repository, check=True, capture_output=True)
    (repository / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(("git", "add", "README.md"), cwd=repository, check=True)
    subprocess.run(
        ("git", "commit", "-q", "-m", "fixture"),
        cwd=repository,
        check=True,
    )
    return repository


class CreatorLiveTaskAndEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.note_bytes = (
            b"# Execution identity\n"
            b"Bind the product-code baseline and execution repository HEAD as separate exact identities.\n"
            b"A later repository commit requires bounded requalification or a Charter delta.\n"
        )
        self.note = FieldNoteIdentity(
            note_path=(
                ".decision-os/field-notes/"
                "2026-08-05-bind-execution-identities-fixture.md"
            ),
            field_note_id="FN-FIXTURE-005",
            note_sha256=hashlib.sha256(self.note_bytes).hexdigest(),
            origin_run_id="run-1-fixture",
        )
        self.run_2_id = "run-2-fixture"
        self.structure = self.note_bytes.splitlines()[1]

    def output(self, structure: bytes | None = None) -> bytes:
        exact = self.structure if structure is None else structure
        return b"\n".join(
            (
                f"note_path={self.note.note_path}".encode(),
                f"note_id={self.note.field_note_id}".encode(),
                f"note_sha256={self.note.note_sha256}".encode(),
                f"run_2_id={self.run_2_id}".encode(),
                b"exact_structure=" + exact,
            )
        )

    def compile(self, output: bytes):
        return compile_run_2_output_artifact(
            note=self.note,
            note_bytes=self.note_bytes,
            run_2_id=self.run_2_id,
            final_output_bytes=output,
            final_output_sha256=hashlib.sha256(output).hexdigest(),
            observed_at="2026-08-05T09:00:00Z",
        )

    def output_identity(
        self,
        output: bytes,
        *,
        run_2_id: str | None = None,
    ) -> FieldNoteCreatorLiveRun2OutputIdentity:
        return FieldNoteCreatorLiveRun2OutputIdentity.create(
            proof_attempt_id="proof-fixture-005",
            run_id=run_2_id or self.run_2_id,
            task_byte_count=len(RUN_2_TASK.encode("utf-8")),
            task_sha256=RUN_2_TASK_SHA256,
            final_output_byte_count=len(output),
            final_output_sha256=hashlib.sha256(output).hexdigest(),
        )

    def test_canonical_task_bytes_hashes_lanes_and_authorizations_are_exact(
        self,
    ) -> None:
        self.assertEqual(832, len(RUN_1_TASK.encode("utf-8")))
        self.assertEqual(
            RUN_1_TASK_SHA256,
            hashlib.sha256(RUN_1_TASK.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(856, len(RUN_2_TASK.encode("utf-8")))
        self.assertEqual(
            RUN_2_TASK_SHA256,
            hashlib.sha256(RUN_2_TASK.encode("utf-8")).hexdigest(),
        )
        self.assertEqual("2026-08-05T06:22:00Z", CYCLE_AUTHORIZATION_OBSERVED_AT)
        self.assertEqual(
            "2026-08-05T12:28:00Z",
            IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT,
        )
        self.assertIn("Propose exactly one new Field Note", RUN_1_TASK)
        self.assertNotIn("Propose another Field Note", RUN_2_TASK)

    def test_a3_compiles_one_unique_exact_non_whole_utf8_range(self) -> None:
        output = self.output()
        claim = self.compile(output)
        evidence = claim.use_evidence
        self.assertIsNotNone(evidence)
        assert evidence is not None
        self.assertEqual("OUTPUT_ARTIFACT", evidence.evidence_class)
        self.assertEqual("IMMEDIATE_COMPLETION_RECORD", evidence.evidence_origin)
        self.assertTrue(evidence.structure_binding.verifies(self.note, self.note_bytes))
        self.assertEqual(hashlib.sha256(output).hexdigest(), evidence.evidence_sha256)
        self.assertEqual("UNKNOWN", claim.outcome_evaluation.outcome)
        self.assertEqual("HOLD", claim.disposition.action)

    def test_a3_rejects_fuzzy_semantic_normalized_and_whole_note_claims(self) -> None:
        variants = (
            self.output(self.structure.replace(b"exact", b"similar")),
            self.output(self.structure.lower()),
            self.output(self.structure.replace(b" ", b"  ")),
            self.output() + b"\n" + self.note_bytes,
        )
        for output in variants:
            with self.subTest(output=output[-80:]):
                with self.assertRaises(ValueError):
                    self.compile(output)

    def test_a3_rejects_missing_lineage_wrong_output_hash_and_ambiguity(self) -> None:
        missing = self.output().replace(self.note.note_sha256.encode(), b"0" * 64)
        with self.assertRaisesRegex(ValueError, "A3_OUTPUT_ARTIFACT_LINEAGE_MISSING"):
            self.compile(missing)
        output = self.output()
        with self.assertRaisesRegex(ValueError, "A3_OUTPUT_ARTIFACT_IDENTITY_INVALID"):
            compile_run_2_output_artifact(
                note=self.note,
                note_bytes=self.note_bytes,
                run_2_id=self.run_2_id,
                final_output_bytes=output,
                final_output_sha256="0" * 64,
                observed_at="2026-08-05T09:00:00Z",
            )

    def test_audited_a3_persists_exact_winner_offsets_and_counts(self) -> None:
        output = self.output()
        winner, audit = compile_run_2_output_artifact_audited(
            note=self.note,
            note_bytes=self.note_bytes,
            run_2_id=self.run_2_id,
            final_output_bytes=output,
            output_identity=self.output_identity(output),
        )
        self.assertIsNotNone(winner)
        self.assertEqual(1, audit.eligible_candidate_count)
        self.assertEqual(1, audit.winning_candidate_count)
        self.assertIsNone(audit.terminal_a3_code)
        source_start = self.note_bytes.index(self.structure)
        output_start = output.index(self.structure)
        self.assertEqual(source_start, audit.selected_source_start_byte)
        self.assertEqual(source_start + len(self.structure), audit.selected_source_end_byte)
        self.assertEqual(output_start, audit.selected_output_start_byte)
        self.assertEqual(output_start + len(self.structure), audit.selected_output_end_byte)
        self.assertEqual(
            hashlib.sha256(
                canonical_json(audit._body()).encode("utf-8")
            ).hexdigest(),
            audit.audit_sha256,
        )

    def test_audited_a3_zero_candidate_has_counts_and_null_offsets(self) -> None:
        output = self.output(
            b"A semantic paraphrase that is intentionally not an exact Note range."
        )
        winner, audit = compile_run_2_output_artifact_audited(
            note=self.note,
            note_bytes=self.note_bytes,
            run_2_id=self.run_2_id,
            final_output_bytes=output,
            output_identity=self.output_identity(output),
        )
        self.assertIsNone(winner)
        self.assertEqual(0, audit.eligible_candidate_count)
        self.assertEqual(0, audit.winning_candidate_count)
        self.assertEqual("A3_EXACT_STRUCTURE_MISSING", audit.terminal_a3_code)
        self.assertGreater(audit.rejection_counts.absent_output_occurrence, 0)
        self.assertEqual(
            (None, None, None, None),
            (
                audit.selected_source_start_byte,
                audit.selected_source_end_byte,
                audit.selected_output_start_byte,
                audit.selected_output_end_byte,
            ),
        )

    def test_audited_a3_multiple_candidate_ambiguity(self) -> None:
        tied_note_bytes = b"# Fixture\n" + b"A" * 48 + b"\n" + b"B" * 48 + b"\n"
        tied_note = FieldNoteIdentity(
            note_path=self.note.note_path,
            field_note_id=self.note.field_note_id,
            note_sha256=hashlib.sha256(tied_note_bytes).hexdigest(),
            origin_run_id=self.note.origin_run_id,
        )
        output = b"\n".join(
            (
                tied_note.note_path.encode(),
                tied_note.field_note_id.encode(),
                tied_note.note_sha256.encode(),
                self.run_2_id.encode(),
                b"A" * 48,
                b"B" * 48,
            )
        )
        winner, audit = compile_run_2_output_artifact_audited(
            note=tied_note,
            note_bytes=tied_note_bytes,
            run_2_id=self.run_2_id,
            final_output_bytes=output,
            output_identity=self.output_identity(output),
        )
        self.assertIsNone(winner)
        self.assertEqual(2, audit.eligible_candidate_count)
        self.assertEqual(2, audit.winning_candidate_count)
        self.assertEqual("A3_EXACT_STRUCTURE_AMBIGUOUS", audit.terminal_a3_code)
        self.assertIsNone(audit.selected_source_start_byte)

    def test_audited_a3_counts_multiple_output_occurrences(self) -> None:
        output = self.output() + b"\nrepeated=" + self.structure
        winner, audit = compile_run_2_output_artifact_audited(
            note=self.note,
            note_bytes=self.note_bytes,
            run_2_id=self.run_2_id,
            final_output_bytes=output,
            output_identity=self.output_identity(output),
        )
        self.assertIsNone(winner)
        self.assertEqual(0, audit.eligible_candidate_count)
        self.assertEqual(
            1,
            audit.rejection_counts.multiple_output_occurrences,
        )
        self.assertEqual("A3_EXACT_STRUCTURE_MISSING", audit.terminal_a3_code)

    def test_output_artifact_id_is_canonical_and_mismatch_is_rejected(self) -> None:
        output = self.output()
        artifact = self.output_identity(output).output_artifact
        body = {
            key: value
            for key, value in artifact.as_dict().items()
            if key != "artifact_id"
        }
        self.assertEqual(
            hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest(),
            artifact.artifact_id,
        )
        invalid = artifact.as_dict()
        invalid["artifact_id"] = "0" * 64
        with self.assertRaises(FieldNoteCreatorLiveValidationError):
            FieldNoteCreatorLiveOutputArtifactIdentity.from_dict(invalid)
        tied_note_bytes = b"# Fixture\n" + b"A" * 48 + b"\n" + b"B" * 48 + b"\n"
        tied_note = FieldNoteIdentity(
            note_path=self.note.note_path,
            field_note_id=self.note.field_note_id,
            note_sha256=hashlib.sha256(tied_note_bytes).hexdigest(),
            origin_run_id=self.note.origin_run_id,
        )
        tied_output = b"\n".join(
            (
                tied_note.note_path.encode(),
                tied_note.field_note_id.encode(),
                tied_note.note_sha256.encode(),
                self.run_2_id.encode(),
                b"A" * 48,
                b"B" * 48,
            )
        )
        with self.assertRaisesRegex(ValueError, "A3_EXACT_STRUCTURE_AMBIGUOUS"):
            compile_run_2_output_artifact(
                note=tied_note,
                note_bytes=tied_note_bytes,
                run_2_id=self.run_2_id,
                final_output_bytes=tied_output,
                final_output_sha256=hashlib.sha256(tied_output).hexdigest(),
                observed_at="2026-08-05T09:00:00Z",
            )


class CreatorLiveAttemptIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = _commit_repository(self.root)
        self.spec = CreatorLiveCycle005Spec(
            repository=self.repository,
            remote="fixture",
            protected_history=(),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def entrypoint(self) -> _ReadyEntrypoint:
        return _ReadyEntrypoint(
            _Controller(self.repository),
            spec=self.spec,
            worker_factory=_NoopWorker,
        )

    def test_preopen_mismatch_is_unconsumed_and_invokes_no_worker(self) -> None:
        entrypoint = self.entrypoint()
        with self.assertRaisesRegex(CreatorLiveEntrypointError, "LAUNCH_BINDING_STALE"):
            entrypoint.start("5" * 64)
        self.assertFalse(self.spec.storage_root.exists())
        self.assertIsNone(entrypoint._worker)

    def test_open_is_durable_deterministic_and_duplicate_has_no_replacement(self) -> None:
        entrypoint = self.entrypoint()
        snapshot = entrypoint.start(_DIGEST)
        expected = "proof_a7_creator_live_cycle_005_" + _DIGEST
        self.assertEqual(expected, snapshot["identities"]["proof_attempt_id"])
        self.assertTrue(entrypoint._worker.started)
        self.assertTrue(entrypoint._runtime.journal_path.is_file())
        self.assertTrue(entrypoint._runtime.anchor_path.is_file())
        with self.assertRaisesRegex(CreatorLiveEntrypointError, "ATTEMPT_EXISTS"):
            entrypoint.start(_DIGEST)
        with self.assertRaisesRegex(CreatorLiveEntrypointError, "ATTEMPT_EXISTS"):
            entrypoint.start("6" * 64)
        self.assertEqual(
            {entrypoint._runtime.journal_path.name, entrypoint._runtime.anchor_path.name},
            {path.name for path in self.spec.storage_root.iterdir()},
        )

    def test_restart_exposes_open_unresumable_and_cannot_create_replacement(self) -> None:
        opened = self.entrypoint()
        opened.start(_DIGEST)
        opened._active = False
        opened._terminal_state = "FAILED"
        in_process = opened.snapshot(_Controller(self.repository).snapshot())
        self.assertEqual("OPEN_UNRESUMABLE", in_process["state"])
        restarted = self.entrypoint()
        snapshot = restarted.snapshot(_Controller(self.repository).snapshot())
        self.assertEqual("OPEN_UNRESUMABLE", snapshot["state"])
        self.assertEqual(
            "proof_a7_creator_live_cycle_005_" + _DIGEST,
            snapshot["identities"]["proof_attempt_id"],
        )
        with self.assertRaisesRegex(CreatorLiveEntrypointError, "ATTEMPT_EXISTS"):
            restarted.start(_DIGEST)

    def test_postopen_coordinator_failure_consumes_one_terminal_attempt(self) -> None:
        entrypoint = _ReadyEntrypoint(
            _Controller(self.repository),
            spec=self.spec,
            worker_factory=_FailingWorker,
        )
        with self.assertRaisesRegex(
            CreatorLiveEntrypointError,
            "CYCLE_005_COORDINATOR_START_FAILED",
        ):
            entrypoint.start(_DIGEST)
        self.assertEqual("FAILED", entrypoint._runtime.read_back().state)
        entrypoint._terminal_state = "PASS"
        self.assertEqual(
            "FAILED",
            entrypoint.snapshot(_Controller(self.repository).snapshot())["state"],
        )
        restarted = self.entrypoint()
        snapshot = restarted.snapshot(_Controller(self.repository).snapshot())
        self.assertEqual("FAILED", snapshot["state"])
        self.assertIsNone(snapshot["binding"])
        identities = snapshot["identities"]
        self.assertEqual(
            "ORDINARY_USER_PATH_CONTRACT_APPROVED_CANDIDATE_V0_1",
            identities["contract_identity"]["profile"],
        )
        self.assertEqual(832, identities["run_1_task"]["byte_count"])
        self.assertEqual(856, identities["run_2_task"]["byte_count"])
        self.assertEqual(
            IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT,
            identities["implementation_authorization_observed_at"],
        )
        self.assertEqual(0, identities["retry_count"])
        self.assertEqual(0, identities["replacement_count"])
        self.assertNotIn(str(self.repository), json.dumps(snapshot))
        with self.assertRaisesRegex(CreatorLiveEntrypointError, "ATTEMPT_EXISTS"):
            restarted.start(_DIGEST)

    def test_concurrent_clicks_resolve_to_one_open_attempt(self) -> None:
        entrypoint = self.entrypoint()
        outcomes: list[str] = []
        gate = threading.Barrier(3)

        def start() -> None:
            gate.wait()
            try:
                entrypoint.start(_DIGEST)
                outcomes.append("accepted")
            except CreatorLiveEntrypointError as exc:
                outcomes.append(exc.code)

        workers = [threading.Thread(target=start) for _ in range(2)]
        for worker in workers:
            worker.start()
        gate.wait()
        for worker in workers:
            worker.join(timeout=5)
        self.assertCountEqual(
            ["accepted", "CYCLE_005_ATTEMPT_EXISTS"],
            outcomes,
        )
        self.assertEqual(2, len(tuple(self.spec.storage_root.iterdir())))

    def test_partial_storage_is_integrity_failure_and_permanently_occupied(self) -> None:
        self.spec.storage_root.mkdir(parents=True)
        (self.spec.storage_root / "creator-live-proof-v0.2.jsonl").write_bytes(b"{")
        entrypoint = self.entrypoint()
        snapshot = entrypoint.snapshot(_Controller(self.repository).snapshot())
        self.assertEqual("INTEGRITY_FAILURE", snapshot["state"])
        with self.assertRaisesRegex(CreatorLiveEntrypointError, "ATTEMPT_EXISTS"):
            entrypoint.start(_DIGEST)

    def test_post_completion_readback_failure_releases_transient_output(self) -> None:
        run_2_id = "run_a7_creator_live_cycle_005_2_" + _DIGEST

        class Controller:
            def __init__(self) -> None:
                self._creator_live_a2_run_completion = object()

            def creator_live_a1_completed_draft(
                self, *, expected_run_id: str
            ) -> object:
                self.a1_run_id = expected_run_id
                return object()

            def creator_live_a2_run_completion(
                self, *, expected_run_id: str
            ) -> object:
                self.asserted_run_id = expected_run_id
                return self._creator_live_a2_run_completion

            def release_creator_live_a2_run_completion(
                self, *, expected_run_id: str
            ) -> None:
                self.released_run_id = expected_run_id
                self._creator_live_a2_run_completion = None

        note = object()

        class Runtime:
            def __init__(self) -> None:
                self.read_count = 0

            def read_back(self) -> object:
                self.read_count += 1
                if self.read_count == 1:
                    return type(
                        "AfterA1",
                        (),
                        {
                            "proof_attempt_id": "proof-fixture",
                            "run_1": type("Run1", (), {"run_id": "run-1"})(),
                            "captured_note": note,
                        },
                    )()
                if self.read_count == 2:
                    return object()
                if self.read_count == 3:
                    raise ValueError("POST_COMPLETION_READBACK_FAILED")
                return type("Failed", (), {"state": "FAILED"})()

            def open_run_2(self, _identity: object) -> None:
                return None

        class Bridge:
            def __init__(self, **_kwargs: object) -> None:
                pass

            def capture(self, _task: str) -> None:
                return None

            def reconnect(self, _task: str) -> None:
                return None

        controller = Controller()
        entrypoint = CreatorLiveCycle005Entrypoint(
            controller,
            spec=self.spec,
        )
        source = FieldNoteSourceRepositoryIdentity(
            repository_id="repo:v1:" + "a" * 64,
            source_commit="a" * 40,
        )
        runtime = Runtime()
        prepared = type("Prepared", (), {"note_bytes": b"fixture\n"})()
        with (
            patch(
                "decision_os.companion.field_notes_creator_live_entrypoint."
                "FieldNoteCreatorLiveA1CaptureBridge",
                Bridge,
            ),
            patch(
                "decision_os.companion.field_notes_creator_live_entrypoint."
                "FieldNoteCreatorLiveA2ReconnectBridge",
                Bridge,
            ),
            patch(
                "decision_os.companion.field_notes_creator_live_entrypoint."
                "creator_live_a2_target_from_readback",
                return_value=object(),
            ),
            patch(
                "decision_os.companion.field_notes_creator_live_entrypoint."
                "prepare_creator_live_a2_reconnect",
                return_value=prepared,
            ),
        ):
            entrypoint._run_sequence(runtime, source, _DIGEST)

        self.assertIsNone(
            controller._creator_live_a2_run_completion,
            entrypoint._terminal_failure_code,
        )
        self.assertEqual(run_2_id, controller.released_run_id)
        self.assertEqual("FAILED", entrypoint._terminal_state)


class CreatorLiveCycle005BackwardProjectionTests(unittest.TestCase):
    def test_cycle_005_projects_only_exact_v2_durable_values(self) -> None:
        entrypoint = CreatorLiveCycle005Entrypoint(object())
        snapshot = entrypoint.snapshot({})
        identities = snapshot["identities"]
        self.assertEqual("FAILED", snapshot["state"])
        self.assertEqual("A3_REUSE", snapshot["stage"])
        self.assertFalse(snapshot["start_allowed"])
        self.assertTrue(snapshot["storage_occupied"])
        self.assertIsNone(snapshot["binding"])
        self.assertEqual(
            "bbfa49ba48254758a8b6429b2eb88d141954eac8",
            identities["revision"],
        )
        self.assertEqual(NOT_DURABLY_PERSISTED, identities["contract_identity"])
        self.assertEqual(
            NOT_DURABLY_PERSISTED,
            identities["run_1_task"]["byte_count"],
        )
        self.assertEqual(RUN_1_TASK_SHA256, identities["run_1_task"]["sha256"])
        self.assertEqual(
            NOT_DURABLY_PERSISTED,
            identities["run_2_task"]["byte_count"],
        )
        self.assertEqual(
            "2026-08-05T11:24:40.255812Z",
            identities["proof_as_of"],
        )
        self.assertEqual(
            "1de2e998804f5fb694707846b7deb0dc9d8b5f9cfc6027ad0210ddc270029322",
            identities["journal_sha256"],
        )
        self.assertEqual(
            "e246757a7ba98849a6b4a694ababf473dc1a98baf1fc1ce0ea7daa3a6e7e8610",
            identities["anchor_sha256"],
        )
        self.assertEqual(
            "481be90dc8751bda3d7b00714f5a0c650230dffa8974a1332881ce42c127710f",
            identities["readback_sha256"],
        )
        self.assertEqual("A3_EXACT_STRUCTURE_MISSING", identities["failure_code"])

    def test_cycle_005_never_reconstructs_from_contemporary_constants(self) -> None:
        spec = CreatorLiveCycle005Spec(
            run_1_task="CONTEMPORARY_PRIVATE_RUN_1_TASK",
            run_2_task="CONTEMPORARY_PRIVATE_RUN_2_TASK",
            implementation_authorization_observed_at=(
                "2099-01-01T00:00:00Z"
            ),
        )
        snapshot = CreatorLiveCycle005Entrypoint(
            object(),
            spec=spec,
        ).snapshot({})
        raw = json.dumps(snapshot, sort_keys=True)
        self.assertNotIn("CONTEMPORARY_PRIVATE", raw)
        self.assertNotIn("2099-01-01", raw)
        self.assertEqual(
            NOT_DURABLY_PERSISTED,
            snapshot["identities"]["implementation_authorization_observed_at"],
        )


class CreatorLiveHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        repository = create_repository(self.root)
        self.controller = FieldNotesCompanionController(
            state_path=self.root / "state.json",
            picker_script=self.root / "picker.applescript",
            picker_runner=lambda _script: str(repository),
            adapter_factory=ScriptedFactory("read_only"),
            creator_live_entrypoint_factory=_FakeHTTPEntrypoint,
        )
        self.controller.select_repository(repository)
        static_root = (
            Path(__file__).resolve().parents[1]
            / "decision_os"
            / "companion"
            / "static"
        )
        self.server = CompanionServer(self.controller, static_root=static_root)
        configure_field_notes_server(self.server)
        self.server.start_background()

    def tearDown(self) -> None:
        self.server.close()
        self.temporary.cleanup()

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: bytes | None = None,
        content_type: str | None = "application/json",
        cookie: str | None = None,
        csrf: str | None = None,
        origin: str | None = None,
        host: str | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection("127.0.0.1", self.server.port)
        headers: dict[str, str] = {}
        if payload is not None and content_type is not None:
            headers["Content-Type"] = content_type
        if cookie is not None:
            headers["Cookie"] = cookie
        if csrf is not None:
            headers["X-Decision-OS-CSRF"] = csrf
        if origin is not None:
            headers["Origin"] = origin
        if host is not None:
            headers["Host"] = host
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        response_headers = {key.lower(): value for key, value in response.getheaders()}
        status = response.status
        connection.close()
        return status, response_headers, raw

    def bootstrap(self) -> tuple[str, str]:
        path = urlsplit(self.server.bootstrap_url).path
        status, headers, _raw = self.request("GET", path, content_type=None)
        self.assertEqual(303, status)
        cookie = headers["set-cookie"].split(";", 1)[0]
        status, _headers, raw = self.request(
            "GET", "/api/state", cookie=cookie, content_type=None
        )
        self.assertEqual(200, status)
        return cookie, json.loads(raw)["csrf"]

    def post(self, raw: bytes, cookie: str, csrf: str, **kwargs: object) -> int:
        status, _headers, _body = self.request(
            "POST",
            "/api/creator-live/cycles/005/start",
            payload=raw,
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
            **kwargs,
        )
        return status

    def test_route_requires_private_session_loopback_origin_and_csrf(self) -> None:
        raw = json.dumps({"launch_binding_sha256": _DIGEST}).encode()
        self.assertEqual(401, self.post(raw, "", ""))
        cookie, csrf = self.bootstrap()
        self.assertEqual(403, self.post(raw, cookie, csrf, host="attacker.invalid"))
        status, _headers, _body = self.request(
            "POST",
            "/api/creator-live/cycles/005/start",
            payload=raw,
            cookie=cookie,
            csrf=csrf,
            origin="http://attacker.invalid",
        )
        self.assertEqual(403, status)
        status, _headers, _body = self.request(
            "POST",
            "/api/creator-live/cycles/005/start",
            payload=raw,
            cookie=cookie,
            origin=self.server.origin,
        )
        self.assertEqual(403, status)

    def test_route_is_strict_and_caller_controls_only_lowercase_digest(self) -> None:
        cookie, csrf = self.bootstrap()
        invalid = (
            b"{}",
            b'{"launch_binding_sha256":"' + _DIGEST.encode() + b'","extra":1}',
            b'{"launch_binding_sha256":"' + _DIGEST.encode() + b'","launch_binding_sha256":"' + _DIGEST.encode() + b'"}',
            b'{"launch_binding_sha256":"' + _DIGEST.upper().encode() + b'"}',
            b'{"launch_binding_sha256":"short"}',
        )
        for raw in invalid:
            with self.subTest(raw=raw):
                self.assertEqual(400, self.post(raw, cookie, csrf))
        self.assertEqual(
            415,
            self.post(
                json.dumps({"launch_binding_sha256": _DIGEST}).encode(),
                cookie,
                csrf,
                content_type="text/plain",
            ),
        )
        stale = json.dumps({"launch_binding_sha256": "7" * 64}).encode()
        self.assertEqual(409, self.post(stale, cookie, csrf))

    def test_exact_route_returns_202_and_ordinary_run_is_not_reused(self) -> None:
        cookie, csrf = self.bootstrap()
        raw = json.dumps({"launch_binding_sha256": _DIGEST}).encode()
        status, _headers, body = self.request(
            "POST",
            "/api/creator-live/cycles/005/start",
            payload=raw,
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(202, status)
        self.assertEqual(_DIGEST, json.loads(body)["creator_live_cycle_005"]["launch_binding_sha256"])
        self.assertEqual([_DIGEST], self.controller._creator_live_cycle_005.started)
        ordinary = json.dumps({"task": ""}).encode()
        status, _headers, _body = self.request(
            "POST",
            "/api/run",
            payload=ordinary,
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertNotEqual(202, status)
        self.assertEqual([_DIGEST], self.controller._creator_live_cycle_005.started)

    def test_http_projection_removes_private_run_content(self) -> None:
        snapshot = {
            "creator_live_cycle_005": {
                "state": "RUNNING",
                "stage": "A2",
                "failure_code": None,
            },
            "run": {
                "task": RUN_2_TASK,
                "result": "PRIVATE MODEL OUTPUT",
                "field_note": {"markdown": "PRIVATE NOTE"},
                "approval": {"hidden": "PRIVATE"},
            },
        }
        projected = self.controller.creator_live_cycle_005_public_projection(snapshot)
        encoded = json.dumps(projected)
        self.assertNotIn(RUN_2_TASK, encoded)
        self.assertNotIn("PRIVATE MODEL OUTPUT", encoded)
        self.assertNotIn("PRIVATE NOTE", encoded)
        self.assertNotIn("PRIVATE", encoded)
        self.assertEqual("creator_live_cycle_005", projected["run"]["run_type"])
        self.assertEqual("running", projected["run"]["state"])
        self.assertEqual(["A2"], projected["run"]["progress"])
        self.assertEqual("", projected["run"]["result"])
        self.assertEqual([], projected["run"]["file_actions"])
        self.assertEqual([], projected["run"]["read_evidence"])
        self.assertIsNone(projected["run"]["runtime"])
        self.assertIsNone(projected["run"]["approval"])

    def test_terminal_projection_preserves_evidence_and_restores_safe_idle(
        self,
    ) -> None:
        for terminal_state in (
            "FAILED",
            "TRACE_COMPLETE",
            "PASS",
            "OPEN_UNRESUMABLE",
            "INTEGRITY_FAILURE",
        ):
            with self.subTest(terminal_state=terminal_state):
                cycle = {
                    "cycle_key": "cycle-005",
                    "state": terminal_state,
                    "stage": "A3",
                    "failure_code": "HISTORICAL_FAILURE",
                    "identities": {
                        "proof_attempt_id": "cycle-005-attempt-001",
                        "journal_sha256": "1" * 64,
                        "anchor_sha256": "2" * 64,
                    },
                }
                cycle_before = json.loads(json.dumps(cycle, sort_keys=True))
                snapshot = {
                    "creator_live_cycle_005": cycle,
                    "run": {
                        "run_type": "bounded_task",
                        "state": "completed",
                        "task": RUN_2_TASK,
                        "result": "PRIVATE MODEL OUTPUT",
                        "field_note": {"markdown": "PRIVATE NOTE"},
                        "runtime": {"model": "PRIVATE MODEL"},
                        "approval": {"hidden": "PRIVATE APPROVAL"},
                    },
                }

                projected = self.controller.creator_live_cycle_005_public_projection(
                    snapshot
                )

                self.assertEqual(cycle_before, projected["creator_live_cycle_005"])
                self.assertEqual(
                    {
                        "run_type": "bounded_task",
                        "task_mode": None,
                        "state": "idle",
                        "progress": [],
                        "result": "",
                        "file_actions": [],
                        "read_evidence": [],
                        "outcomes": {
                            "execution": {
                                "state": "not_started",
                                "label": "Not started",
                            },
                            "file_change": {
                                "state": "none",
                                "label": "No file was modified",
                            },
                            "verification": {
                                "state": "not_started",
                                "label": "Not started",
                                "reason": None,
                            },
                        },
                        "runtime": None,
                        "receipt_delta": None,
                        "approval": None,
                        "error": None,
                        "failure": None,
                    },
                    projected["run"],
                )
                encoded_run = json.dumps(projected["run"], sort_keys=True)
                for private in (
                    RUN_2_TASK,
                    "PRIVATE MODEL OUTPUT",
                    "PRIVATE NOTE",
                    "PRIVATE MODEL",
                    "PRIVATE APPROVAL",
                ):
                    self.assertNotIn(private, encoded_run)

    def test_terminal_http_state_is_allowlisted_and_duplicate_start_is_409(
        self,
    ) -> None:
        cookie, csrf = self.bootstrap()
        self.controller._creator_live_cycle_005 = CreatorLiveCycle005Entrypoint(
            self.controller
        )
        status, _headers, raw = self.request(
            "GET",
            "/api/state",
            cookie=cookie,
            content_type=None,
        )
        self.assertEqual(200, status)
        state = json.loads(raw)
        cycle = state["creator_live_cycle_005"]
        run = state["run"]
        encoded = json.dumps(cycle, sort_keys=True)
        self.assertEqual("FAILED", cycle["state"])
        self.assertIsNone(cycle["binding"])
        self.assertFalse(cycle["start_allowed"])
        self.assertEqual("bounded_task", run["run_type"])
        self.assertEqual("idle", run["state"])
        self.assertIsNone(run["task_mode"])
        self.assertEqual("", run["result"])
        self.assertEqual([], run["file_actions"])
        self.assertEqual([], run["read_evidence"])
        self.assertIsNone(run["runtime"])
        self.assertIsNone(run["approval"])
        for private in (
            RUN_1_TASK,
            RUN_2_TASK,
            "note_path",
            "note_id",
            "PRIVATE MODEL OUTPUT",
            "protected_history",
            "/Users/sn/Documents/v13/decision-os-v13-loopkit",
        ):
            self.assertNotIn(private, encoded)
        terminal_evidence = json.loads(json.dumps(cycle, sort_keys=True))
        status, _headers, raw = self.request(
            "POST",
            "/api/new-run",
            payload=b"{}",
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status)
        refreshed = json.loads(raw)
        self.assertEqual(terminal_evidence, refreshed["creator_live_cycle_005"])
        self.assertEqual("bounded_task", refreshed["run"]["run_type"])
        self.assertEqual("idle", refreshed["run"]["state"])
        status, _headers, body = self.request(
            "POST",
            "/api/creator-live/cycles/005/start",
            payload=json.dumps(
                {"launch_binding_sha256": cycle["launch_binding_sha256"]}
            ).encode("utf-8"),
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(409, status)
        self.assertEqual("CYCLE_005_ATTEMPT_EXISTS", json.loads(body)["error"])


if __name__ == "__main__":
    unittest.main()
