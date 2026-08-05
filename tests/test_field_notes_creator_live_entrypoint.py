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
from urllib.parse import urlsplit

from decision_os.companion.field_notes_controller import (
    FieldNotesCompanionController,
)
from decision_os.companion.field_notes_creator_live_entrypoint import (
    CYCLE_AUTHORIZATION_OBSERVED_AT,
    EXPECTED_EXECUTION_AUTHORITY,
    EXPECTED_FREEZE_AUTHORITY,
    IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT,
    RUN_1_TASK,
    RUN_1_TASK_SHA256,
    RUN_2_TASK,
    RUN_2_TASK_SHA256,
    CreatorLiveCycle005Entrypoint,
    CreatorLiveCycle005Spec,
    CreatorLiveEntrypointError,
    CreatorLiveP0Result,
    compile_run_2_output_artifact,
)
from decision_os.companion.field_notes_reuse import FieldNoteIdentity
from decision_os.companion.field_notes_server import configure_field_notes_server
from decision_os.companion.server import CompanionServer
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
                "historical_boundary": "Historical attempts remain terminal.",
            },
            "identities": None,
            "receipt_sha256": None,
            "manifest_sha256": None,
            "failure_code": None,
            "one_attempt_no_retry": True,
            "replacement_permitted": False,
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
            "2026-08-05T08:47:00Z",
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
        self.entrypoint().start(_DIGEST)
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
        restarted = self.entrypoint()
        snapshot = restarted.snapshot(_Controller(self.repository).snapshot())
        self.assertEqual("FAILED", snapshot["state"])
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
        self.assertEqual(["A2"], projected["run"]["progress"])


if __name__ == "__main__":
    unittest.main()
