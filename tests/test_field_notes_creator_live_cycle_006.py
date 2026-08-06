from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import http.client
import io
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from decision_os.acceleration.codex_adapter import (
    ADAPTER_NAME,
    CODEX_CLI_VERSION,
    CodexAdapterFailure,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.companion import field_notes_adapter as adapter_module
from decision_os.companion import field_notes_creator_live_candidate_v0_2 as candidate_v02
from decision_os.companion import field_notes_creator_live_reconnect as exact_a2
from decision_os.companion.field_notes_adapter import (
    FieldNoteCreatorLiveA1CaptureConfig,
    FieldNoteCreatorLiveCandidateV02A1Config,
    FieldNoteCreatorLiveCandidateV02A2Config,
    FieldNotesCodexAdapter,
)
from decision_os.companion.field_notes_controller import (
    FieldNoteError,
    FieldNotesCompanionController,
)
from decision_os.companion.field_notes_creator_live_entrypoint import (
    CreatorLiveEntrypointError,
)
from decision_os.companion import field_notes_creator_live_cycle_006 as cycle006
from decision_os.companion.field_notes_creator_live_cycle_006 import (
    CYCLE_005_ANCHOR_SHA256,
    CYCLE_005_JOURNAL_SHA256,
    CYCLE_005_READBACK_SHA256,
    CYCLE_KEY,
    CYCLE_NUMBER,
    EXPECTED_RUNTIME,
    CreatorLiveCycle006Entrypoint,
    CreatorLiveCycle006Error,
    CreatorLiveCycle006P0Result,
    CreatorLiveCycle006Spec,
    future_proof_identity,
)
from decision_os.companion.field_notes_server import configure_field_notes_server
from decision_os.companion.field_notes_model import FIELD_NOTE_TOOL_NAME
from decision_os.companion.field_notes_reconnect import (
    FieldNoteReconnectPlan,
    FieldNoteReconnectReceipt,
)
from decision_os.companion.server import CompanionServer
from tests.test_acceleration_codex_adapter import (
    FakeTransportFactory,
    approval_request,
    change,
    completed_agent_message,
    completed_item,
    completed_turn,
    handshake_messages,
    resolved_request,
    started_item,
)
from tests.test_companion_controller import ScriptedFactory, create_repository


ROOT = Path(__file__).resolve().parents[1]
_DIGEST = "a4" * 32
_STALE = "7" * 64
_RUN_CANONICAL = (
    os.environ.get("DECISION_OS_RUN_CYCLE_006_CANONICAL_TESTS") == "1"
)


def _candidate_proposal() -> dict[str, object]:
    return {
        "title": "Bounded Candidate v0.2 fixture",
        "value_level": 1,
        "source_model_class": "UNKNOWN",
        "target_model_class": "UNKNOWN",
        "trigger_terms": ["candidate v0.2", "fixed source"],
        "scope": {
            "task_family": "candidate-v0.2",
            "path_prefixes": [],
            "exclude_terms": [],
        },
        "body": {
            "trigger": "Use only after the fixed historical source is disclosed.",
            "reusable_structure": "Keep source and proposal order exact.",
            "scope": "One bounded A1 fixture Run.",
            "do_not_apply_when": "The source has not been disclosed.",
            "procedure": "Read once, then propose once.",
            "acceptance": "The exact event lineage qualifies.",
            "evidence": "Fake app-server transcript only.",
            "remaining_unknowns": "No live claim is made.",
        },
    }


def _dynamic_event(
    method: str,
    *,
    thread: str,
    turn: str,
    call: str,
    tool: str,
    arguments: dict[str, object],
    status: str,
) -> dict[str, object]:
    return {
        "method": method,
        "params": {
            "item": {
                "arguments": arguments,
                "id": call,
                "status": status,
                "tool": tool,
                "type": "dynamicToolCall",
            },
            "threadId": thread,
            "turnId": turn,
        },
    }


def _tool_request(
    *,
    thread: str,
    turn: str,
    call: str,
    request: str,
    tool: str,
    arguments: dict[str, object],
) -> dict[str, object]:
    return {
        "id": request,
        "method": "item/tool/call",
        "params": {
            "arguments": arguments,
            "callId": call,
            "threadId": thread,
            "tool": tool,
            "turnId": turn,
        },
    }


def _passive_event(
    method: str,
    *,
    thread: str,
    turn: str,
    item: dict[str, object],
) -> dict[str, object]:
    return {
        "method": method,
        "params": {
            "item": item,
            "threadId": thread,
            "turnId": turn,
        },
    }


def _canonical_ordinary_contract_snapshot(
    common: Path,
) -> dict[str, object]:
    ordinary_store = json.loads(
        (
            common / "decision-os/ordinary-user-path-v0.1/state.json"
        ).read_text(encoding="utf-8")
    )
    guided_store = json.loads(
        (common / "decision-os/guided-intake-v0.1/state.json").read_text(
            encoding="utf-8"
        )
    )
    record = ordinary_store["record"]
    guided_record = guided_store["record"]
    preparation = record["preparation"]
    source = deepcopy(preparation["source_identity"])
    source["title"] = preparation["title"]
    source["profile"] = preparation["profile"]
    return {
        "state": record["state"],
        "preparation_id": preparation["preparation_id"],
        "repository_identity": preparation["repository_identity"],
        "source_identity": source,
        "execution_authority": cycle006.EXPECTED_EXECUTION_AUTHORITY,
        "technical_details": {
            "active_request_id": guided_record["active_request_id"],
            "wrapper_sha256": preparation["wrapper_sha256"],
            "request_id": preparation["request_id"],
            "draft_id": preparation["draft_id"],
            "interpretation_sha256": preparation["interpretation_sha256"],
            "preparation_repository_identity": preparation[
                "repository_identity"
            ],
            "gate": preparation["gate"],
            "producer_identity": (
                "DECISION_OS_CONTRACT_FIXATION_COMPILER_V0_1"
            ),
            "preparation_receipt_sha256": preparation[
                "preparation_receipt_sha256"
            ],
            "freeze": deepcopy(record["fix"]["freeze"]),
        },
    }


def _full_fixture_binding() -> dict[str, object]:
    return {
        "schema": "decision-os.creator-live-cycle-006-launch-binding.v0.1",
        "cycle": {
            "number": "006",
            "cycle_key": "cycle-006",
            "candidate_id": "CREATOR_LIVE_AGENTS_BEFORE_AFTER_V0_2",
            "implementation_authorization_observed_at": "2026-08-06T00:50:00Z",
            "live_start_authorization": "ABSENT",
        },
        "attempt_policy": {
            "attempt_count": 1,
            "one_attempt": True,
            "retry_count": 0,
            "replacement_count": 0,
            "resume_after_interruption": False,
            "proof_root": "/PRIVATE/PROOF/ROOT",
            "proof_identity_derivation": "PRIVATE_DERIVATION",
        },
        "repository": {
            "selected_path": "/PRIVATE/REPOSITORY",
            "selected_path_sha256": "1" * 64,
            "repository_id": "PRIVATE_REPOSITORY_ID",
            "head": "a" * 40,
            "local_main": "a" * 40,
            "origin_main": "a" * 40,
            "branch": "main",
            "ahead": 0,
            "behind": 0,
            "tracked_worktree_clean": True,
            "index_clean": True,
            "git_operation_active": False,
        },
        "product": {
            "source_tree_sha256": "2" * 64,
            "installed_tree_sha256": "2" * 64,
        },
        "contract": {
            "filename": cycle006.CONTRACT_FILENAME,
            "profile": cycle006.EXPECTED_CONTRACT_PROFILE,
            "title": cycle006.EXPECTED_CONTRACT_TITLE,
            "source_byte_count": cycle006.EXPECTED_CONTRACT_BYTES,
            "source_sha256": cycle006.EXPECTED_CONTRACT_SHA256,
            "wrapper_sha256": cycle006.EXPECTED_WRAPPER_SHA256,
            "interpretation_sha256": cycle006.EXPECTED_INTERPRETATION_SHA256,
            "ordinary_contract_execution_authority": "INTERPRETATION_ONLY",
            "guided_intake_freeze_authority": "IMMUTABLE_INTERPRETATION_ONLY",
            "gate": "CLEAR ENOUGH TO FREEZE",
            "preparation_id": "PRIVATE_PREPARATION",
        },
        "candidate": {
            "candidate_id": "CREATOR_LIVE_AGENTS_BEFORE_AFTER_V0_2",
            "common_before": {
                "utf8_byte_count": 20_705,
                "sha256": "e856160413a9d47622779dede6a2eeca9fd027284d815b155ab6e323a74863db",
            },
            "source_tool": {"name": "read_candidate_historical_before_v0_2"},
            "dynamic_tool_manifest": {
                "run_1_tool_names": [
                    "read_candidate_historical_before_v0_2",
                    "propose_field_note_candidate",
                ],
                "run_2_dynamic_tools": [],
            },
            "schema_identities": [],
            "gates": {"post_a1_readback": "EXACT_DURABLE_PASS_REQUIRED"},
            "a3_overlay": {
                "eligible_candidate_count": 1,
                "winning_candidate_count": 1,
            },
            "behavior": {"state_before_execution": "NOT_RUN"},
        },
        "tasks": {
            "run_1": {
                "lane": "A1_ONLY",
                "utf8_byte_count": 2713,
                "sha256": "2ed80098fb169313b13c36dddfd69a3ab487a4fe31d8474889cff7ba441b09e2",
            },
            "run_2": {
                "lane": "EXACT_A2_ONLY",
                "utf8_byte_count": 2703,
                "sha256": "1a67c3677ce8c73b4259317130e689dfefa1827fffe3abe377af861da8ec4bdb",
            },
        },
        "runtime": dict(EXPECTED_RUNTIME),
        "historical_boundary": {
            "cycle_005": {
                "cycle_key": "cycle-005",
                "state": "FAILED",
                "failure_boundary": "A3_REUSE",
                "failure_code": "A3_EXACT_STRUCTURE_MISSING",
            },
            "candidate_v0_1": {"immutable": True},
            "candidate_v0_2": {"immutable": True},
        },
        "comparison": {"result_before_execution": "NOT_ESTABLISHED"},
        "reduction_boundary": {"ranking": False},
        "pre_live_state": {
            "artifact_behavior": "NOT_RUN",
            "comparison_result": "NOT_ESTABLISHED",
            "proof_identity": None,
            "model_invocation_count": 0,
            "task_transmission_count": 0,
            "real_after": None,
            "publication_authorized": False,
        },
    }


class _Controller:
    def __init__(self, repository: Path) -> None:
        self.repository = repository

    def snapshot(self) -> dict[str, object]:
        return {"repository": {"path": str(self.repository)}}


class _ReadyEntrypoint(CreatorLiveCycle006Entrypoint):
    def _p0(self, _base_snapshot: object) -> CreatorLiveCycle006P0Result:
        return CreatorLiveCycle006P0Result(
            True,
            None,
            _full_fixture_binding(),
            _DIGEST,
        )

    def _require_runtime_binary_identity(self) -> None:
        return None


class Cycle006IdentityAndBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name) / "repository"
        self.repository.mkdir()
        self.spec = CreatorLiveCycle006Spec(repository=self.repository)
        self.entrypoint = _ReadyEntrypoint(
            _Controller(self.repository),
            spec=self.spec,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_exact_cycle_candidate_runtime_and_one_attempt_identity(self) -> None:
        self.assertEqual((CYCLE_NUMBER, CYCLE_KEY), ("006", "cycle-006"))
        self.assertEqual(
            cycle006.CANDIDATE_ID,
            "CREATOR_LIVE_AGENTS_BEFORE_AFTER_V0_2",
        )
        self.assertEqual(
            EXPECTED_RUNTIME,
            {
                "provider": "openai",
                "account": "ChatGPT",
                "model": "gpt-5.6-sol",
                "reasoning_effort": "ultra",
                "service_tier": "priority",
                "codex_cli_version": "0.146.0-alpha.3.1",
                "sandbox": "read-only",
                "model_sandbox_network": False,
                "provider_transport_required": True,
                "fresh_ephemeral_thread_per_run": True,
                "repository_cwd": "canonical-selected-repository",
            },
        )
        identity = future_proof_identity(_DIGEST)
        self.assertEqual(
            identity,
            "proof_a7_creator_live_cycle_006_" + _DIGEST,
        )
        self.assertEqual(len(identity.removeprefix("proof_a7_creator_live_cycle_006_")), 64)
        for invalid in ("", "A" * 64, "a" * 63, "a" * 65):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(
                ValueError, "LAUNCH_BINDING_INVALID"
            ):
                future_proof_identity(invalid)

    def test_snapshot_is_ready_but_start_disabled_and_private_values_redacted(self) -> None:
        snapshot = self.entrypoint.snapshot(_Controller(self.repository).snapshot())
        self.assertEqual((snapshot["state"], snapshot["stage"]), ("READY", "P0"))
        self.assertTrue(snapshot["p0"]["ready"])
        self.assertEqual(snapshot["live_start_authorization"], "ABSENT")
        self.assertFalse(snapshot["start_allowed"])
        self.assertFalse(snapshot["storage_occupied"])
        self.assertIsNone(snapshot["proof_identity"])
        self.assertEqual(snapshot["model_invocation_count"], 0)
        self.assertEqual(snapshot["task_transmission_count"], 0)
        self.assertEqual(snapshot["artifact_behavior"], "NOT_RUN")
        self.assertEqual(snapshot["comparison_result"], "NOT_ESTABLISHED")
        encoded = json.dumps(snapshot, sort_keys=True)
        for private in (
            "/PRIVATE/REPOSITORY",
            "/PRIVATE/PROOF/ROOT",
            "PRIVATE_REPOSITORY_ID",
            "PRIVATE_PREPARATION",
            "PRIVATE_DERIVATION",
            "proof_a7_creator_live_cycle_006_" + _DIGEST,
        ):
            self.assertNotIn(private, encoded)

    def test_stale_then_matching_start_fail_before_storage_or_activity(self) -> None:
        with self.assertRaisesRegex(
            CreatorLiveCycle006Error, "LAUNCH_BINDING_STALE"
        ):
            self.entrypoint.start(_STALE)
        self.assertFalse(self.spec.storage_root.exists())
        with self.assertRaisesRegex(
            CreatorLiveCycle006Error, "LIVE_START_AUTHORIZATION_ABSENT"
        ):
            self.entrypoint.start(_DIGEST)
        self.assertFalse(self.spec.storage_root.exists())
        self.assertEqual(future_proof_identity(_DIGEST), future_proof_identity(_DIGEST))

    def test_duplicate_and_concurrent_requests_map_to_one_unallocated_identity(self) -> None:
        errors: list[str] = []
        identities: list[str] = []
        lock = threading.Lock()

        def request() -> None:
            try:
                self.entrypoint.start(_DIGEST)
            except CreatorLiveCycle006Error as exc:
                with lock:
                    errors.append(exc.code)
                    identities.append(future_proof_identity(_DIGEST))

        workers = [threading.Thread(target=request) for _ in range(12)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=5)
        self.assertEqual(errors, ["LIVE_START_AUTHORIZATION_ABSENT"] * 12)
        self.assertEqual(len(set(identities)), 1)
        self.assertFalse(self.spec.storage_root.exists())

    def test_refresh_is_read_only_and_creates_no_identity_or_root(self) -> None:
        snapshots = [
            self.entrypoint.snapshot(_Controller(self.repository).snapshot())
            for _ in range(10)
        ]
        self.assertEqual({item["launch_binding_sha256"] for item in snapshots}, {_DIGEST})
        self.assertTrue(all(item["proof_identity"] is None for item in snapshots))
        self.assertFalse(self.spec.storage_root.exists())

    def test_absent_authority_never_opens_runtime_worker_or_fixed_task(self) -> None:
        calls: list[str] = []

        def runtime_opener(*_args: object, **_kwargs: object) -> object:
            calls.append("runtime")
            raise AssertionError("runtime must remain unopened")

        def worker_factory(*_args: object, **_kwargs: object) -> object:
            calls.append("worker")
            raise AssertionError("worker must remain unallocated")

        entrypoint = _ReadyEntrypoint(
            _Controller(self.repository),
            spec=self.spec,
            runtime_opener=runtime_opener,
            worker_factory=worker_factory,
        )
        with patch.object(
            entrypoint,
            "_load_fixed_task",
            side_effect=AssertionError("fixed task must remain unread"),
        ), self.assertRaisesRegex(
            CreatorLiveCycle006Error,
            "LIVE_START_AUTHORIZATION_ABSENT",
        ):
            entrypoint.start(_DIGEST)
        self.assertEqual(calls, [])
        self.assertFalse(entrypoint.mutation_blocked)
        self.assertFalse(os.path.lexists(self.spec.storage_root))

    def test_post_p0_head_change_fails_before_proof_open(self) -> None:
        calls: list[str] = []
        binding = deepcopy(_full_fixture_binding())
        binding["repository"]["repository_id"] = "repo:v1:" + "c" * 64

        class AuthorizedReady(_ReadyEntrypoint):
            def _p0(self, _base_snapshot: object) -> CreatorLiveCycle006P0Result:
                return CreatorLiveCycle006P0Result(True, None, binding, _DIGEST)

        entrypoint = AuthorizedReady(
            _Controller(self.repository),
            spec=CreatorLiveCycle006Spec(
                repository=self.repository,
                live_start_authorization_observed_at="2026-08-06T02:00:00Z",
            ),
            runtime_opener=lambda *_args, **_kwargs: calls.append("runtime"),
        )
        with (
            patch.object(
                cycle006,
                "repository_id",
                return_value="repo:v1:" + "c" * 64,
            ),
            patch.object(cycle006, "git_output", return_value="b" * 40),
            self.assertRaisesRegex(
                CreatorLiveCycle006Error,
                "P0_REPOSITORY_CHANGED_BEFORE_PROOF_OPEN",
            ),
        ):
            entrypoint.start(_DIGEST)
        self.assertEqual(calls, [])
        self.assertFalse(os.path.lexists(self.spec.storage_root))

    def test_final_full_p0_drift_fails_before_proof_open(self) -> None:
        calls: list[str] = []

        class DriftingP0(_ReadyEntrypoint):
            p0_calls = 0

            def _p0(self, _base_snapshot: object) -> CreatorLiveCycle006P0Result:
                self.p0_calls += 1
                if self.p0_calls < 3:
                    return CreatorLiveCycle006P0Result(
                        True,
                        None,
                        _full_fixture_binding(),
                        _DIGEST,
                    )
                return CreatorLiveCycle006P0Result(
                    False,
                    "P0_TRACKED_WORKTREE_DIRTY",
                    None,
                    None,
                )

        entrypoint = DriftingP0(
            _Controller(self.repository),
            spec=CreatorLiveCycle006Spec(
                repository=self.repository,
                live_start_authorization_observed_at="2026-08-06T02:00:00Z",
            ),
            runtime_opener=lambda *_args, **_kwargs: calls.append("runtime"),
        )
        with self.assertRaisesRegex(
            CreatorLiveCycle006Error,
            "P0_TRACKED_WORKTREE_DIRTY",
        ):
            entrypoint.start(_DIGEST)
        self.assertEqual(entrypoint.p0_calls, 3)
        self.assertEqual(calls, [])
        self.assertFalse(os.path.lexists(self.spec.storage_root))

    def test_future_authorized_concurrency_opens_one_exact_identity(self) -> None:
        binding = deepcopy(_full_fixture_binding())
        repository_identity = "repo:v1:" + "c" * 64
        head = "b" * 40
        binding["repository"]["repository_id"] = repository_identity
        binding["repository"]["head"] = head
        binding["repository"]["local_main"] = head
        binding["repository"]["origin_main"] = head

        class AuthorizedReady(_ReadyEntrypoint):
            def _p0(self, _base_snapshot: object) -> CreatorLiveCycle006P0Result:
                return CreatorLiveCycle006P0Result(
                    True,
                    None,
                    deepcopy(binding),
                    _DIGEST,
                )

        opener_entered = threading.Event()
        release_opener = threading.Event()
        competitors_done = threading.Event()
        lock = threading.Lock()
        opened_proof_ids: list[str] = []
        worker_starts: list[str] = []
        errors: list[str] = []

        def runtime_opener(*_args: object, **kwargs: object) -> object:
            attempt = kwargs["attempt"]
            with lock:
                opened_proof_ids.append(attempt.proof_attempt_id)
            opener_entered.set()
            if not release_opener.wait(timeout=5):
                raise AssertionError("concurrent requests did not settle")
            return SimpleNamespace()

        class FakeWorker:
            def start(self) -> None:
                worker_starts.append("started")

        entrypoint = AuthorizedReady(
            _Controller(self.repository),
            spec=CreatorLiveCycle006Spec(
                repository=self.repository,
                live_start_authorization_observed_at="2026-08-06T02:00:00Z",
            ),
            runtime_opener=runtime_opener,
            worker_factory=lambda **_kwargs: FakeWorker(),
        )

        def request() -> None:
            try:
                entrypoint.start(_DIGEST)
            except CreatorLiveCycle006Error as exc:
                with lock:
                    errors.append(exc.code)
                    if len(errors) == 11:
                        competitors_done.set()

        workers = [threading.Thread(target=request) for _ in range(12)]
        with (
            patch.object(cycle006, "repository_id", return_value=repository_identity),
            patch.object(cycle006, "git_output", return_value=head),
        ):
            for worker in workers:
                worker.start()
            self.assertTrue(opener_entered.wait(timeout=5))
            self.assertTrue(competitors_done.wait(timeout=5))
            release_opener.set()
            for worker in workers:
                worker.join(timeout=5)

        self.assertEqual(
            opened_proof_ids,
            [cycle006.future_proof_identity(_DIGEST)],
        )
        self.assertEqual(worker_starts, ["started"])
        self.assertEqual(errors, ["CYCLE_006_ATTEMPT_EXISTS"] * 11)
        self.assertFalse(os.path.lexists(self.spec.storage_root))

    def test_noncanonical_spec_and_symlinked_storage_parent_fail_p0(self) -> None:
        other_runtime = cycle006.CodexRuntimeIdentity(
            model="other-model",
            reasoning_effort="ultra",
            service_tier="priority",
            codex_cli_version="0.146.0-alpha.3.1",
            account_type="chatgpt",
        )
        result = CreatorLiveCycle006Entrypoint(
            _Controller(ROOT),
            spec=CreatorLiveCycle006Spec(repository=ROOT, runtime=other_runtime),
        )._p0(_Controller(ROOT).snapshot())
        self.assertFalse(result.ready)
        self.assertEqual(result.failure_code, "P0_FIXED_EXECUTION_IDENTITY_MISMATCH")

        target = self.repository.parent / "alternate-storage"
        target.mkdir()
        (self.repository / ".decision-os").symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(
            ValueError,
            "P0_CYCLE_006_STORAGE_PARENT_INVALID",
        ):
            self.entrypoint._require_storage_boundary(self.repository)

    def test_runtime_binary_mismatch_fails_before_proof_open(self) -> None:
        entrypoint = CreatorLiveCycle006Entrypoint(
            _Controller(self.repository),
            spec=CreatorLiveCycle006Spec(repository=self.repository),
            runtime_version_probe=lambda _path: "0.147.0-alpha.1.2",
        )
        with self.assertRaisesRegex(
            CreatorLiveCycle006Error,
            "P0_CODEX_CLI_VERSION_MISMATCH",
        ):
            entrypoint._require_runtime_binary_identity()
        self.assertFalse(os.path.lexists(self.spec.storage_root))


class Cycle006DurableActivityTests(unittest.TestCase):
    def test_allocated_runs_do_not_count_without_exact_turn_start_milestones(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "repository"
            root = repository / ".decision-os/field-notes/proofs/cycle-006"
            root.mkdir(parents=True)
            run_1 = SimpleNamespace(run_id="run-cycle-006-1")
            run_2 = SimpleNamespace(run_id="run-cycle-006-2")
            readback = SimpleNamespace(
                durable_readback_verified=True,
                proof_attempt_id=cycle006.future_proof_identity(_DIGEST),
                state="FAILED",
                failure_boundary="FAILED_BEFORE_TRANSPORT",
                failure_reason="FAILED_BEFORE_TRANSPORT",
                current_stage="A2_RECONNECT",
                run_1=run_1,
                run_2=run_2,
                journal_sha256="1" * 64,
                anchor_sha256="2" * 64,
                readback_sha256="3" * 64,
            )

            def projection() -> dict[str, object]:
                entrypoint = CreatorLiveCycle006Entrypoint(
                    object(),
                    spec=CreatorLiveCycle006Spec(repository=repository),
                )
                entrypoint._runtime = SimpleNamespace(read_back=lambda: readback)
                return entrypoint._durable_projection()

            def public_projection() -> dict[str, object]:
                entrypoint = CreatorLiveCycle006Entrypoint(
                    object(),
                    spec=CreatorLiveCycle006Spec(repository=repository),
                )
                entrypoint._runtime = SimpleNamespace(read_back=lambda: readback)
                return entrypoint.snapshot({})

            first = projection()
            self.assertEqual(
                (first["model_invocation_count"], first["task_transmission_count"]),
                (0, 0),
            )
            cycle006._persist_turn_start_intent(
                root,
                proof_attempt_id=readback.proof_attempt_id,
                launch_binding_sha256=_DIGEST,
                run_index=1,
                run_id=run_1.run_id,
            )
            with self.assertRaisesRegex(
                ValueError,
                "CYCLE_006_TURN_START_ACTIVITY_UNCERTAIN",
            ):
                projection()
            uncertain = public_projection()
            self.assertEqual(uncertain["state"], "INTEGRITY_FAILURE")
            self.assertIsNone(uncertain["model_invocation_count"])
            self.assertIsNone(uncertain["task_transmission_count"])
            cycle006._persist_turn_start(
                root,
                proof_attempt_id=readback.proof_attempt_id,
                launch_binding_sha256=_DIGEST,
                run_index=1,
                run_id=run_1.run_id,
            )
            second = projection()
            self.assertEqual(
                (second["model_invocation_count"], second["task_transmission_count"]),
                (1, 1),
            )
            cycle006._persist_turn_start_intent(
                root,
                proof_attempt_id=readback.proof_attempt_id,
                launch_binding_sha256=_DIGEST,
                run_index=2,
                run_id=run_2.run_id,
            )
            cycle006._persist_turn_start(
                root,
                proof_attempt_id=readback.proof_attempt_id,
                launch_binding_sha256=_DIGEST,
                run_index=2,
                run_id=run_2.run_id,
            )
            third = projection()
            self.assertEqual(
                (third["model_invocation_count"], third["task_transmission_count"]),
                (2, 2),
            )


class Cycle006CandidateAdapterIsolationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = create_repository(Path(self.temporary.name))

    def a1_adapter(
        self,
        messages: list[dict[str, object]],
        *,
        turn_start_intent_observer: Callable[[str], None] | None = None,
        turn_started_observer: Callable[[str], None] | None = None,
    ) -> tuple[FieldNotesCodexAdapter, FakeTransportFactory]:
        factory = FakeTransportFactory([messages])
        run_id = "run-cycle-006-a1-fixture"
        adapter = FieldNotesCodexAdapter(
            AccelerationEngine(
                self.repository,
                adapter=ADAPTER_NAME,
                adapter_version=CODEX_CLI_VERSION,
            ),
            input_func=lambda: self.fail("no public input permitted"),
            stdout=io.StringIO(),
            approval_provider=lambda _approval: self.fail(
                "no public approval permitted"
            ),
            transport_factory=factory,
            creator_live_a1_capture_provider=lambda: (
                FieldNoteCreatorLiveA1CaptureConfig(
                    run_id=run_id,
                    expected_runtime_identity=cycle006.EXPECTED_CODEX_RUNTIME,
                )
            ),
            candidate_v0_2_a1_provider=lambda: (
                FieldNoteCreatorLiveCandidateV02A1Config(
                    run_id=run_id,
                    expected_runtime_identity=cycle006.EXPECTED_CODEX_RUNTIME,
                    contract_identity_sha256="c" * 64,
                    turn_start_intent_observer=turn_start_intent_observer,
                    turn_started_observer=turn_started_observer,
                )
            ),
        )
        return adapter, factory

    async def run_a2_transcript(
        self,
        messages: list[dict[str, object]],
    ) -> tuple[object, FakeTransportFactory, list[object]]:
        factory = FakeTransportFactory([messages])
        target = exact_a2.FieldNoteCreatorLiveA2ReconnectTarget._issue(
            authority=exact_a2._A2_TARGET_AUTHORITY,
            proof_attempt_id="proof-a2",
            run_1_id="run-a1",
            run_2_id="run-a2",
            field_note_id="fn-a2",
            note_relative_path=".decision-os/field-notes/fn-a2.md",
            note_sha256="a" * 64,
            note_byte_count=1,
            source_repository_id="repo:v1:" + "b" * 64,
            source_commit="c" * 40,
            expected_runtime_identity=cycle006.EXPECTED_CODEX_RUNTIME,
        )
        receipt = FieldNoteReconnectReceipt(
            run_id="run-a2",
            state="NO_MATCH",
            failure_reason=None,
            metadata_entries_seen=0,
            metadata_candidate_files_seen=0,
            metadata_files_valid=0,
            metadata_bytes_read=0,
            selected_field_note_path=None,
            selected_field_note_id=None,
            selected_metadata_sha256=None,
            selected_full_note_sha256=None,
            full_note_bytes_read=0,
            full_notes_injected=0,
            ordinary_distinct_paths_consumed=0,
        )
        approvals: list[object] = []
        adapter = FieldNotesCodexAdapter(
            AccelerationEngine(
                self.repository,
                adapter=ADAPTER_NAME,
                adapter_version=CODEX_CLI_VERSION,
            ),
            input_func=lambda: self.fail("no public input permitted"),
            stdout=io.StringIO(),
            approval_provider=lambda approval: approvals.append(approval) or "deny",
            transport_factory=factory,
            creator_live_a2_reconnect_provider=lambda: target,
            candidate_v0_2_a2_provider=lambda: (
                FieldNoteCreatorLiveCandidateV02A2Config(
                    readback_path="unused",
                    readback_sha256="d" * 64,
                )
            ),
        )
        readback = SimpleNamespace(
            result="PASS",
            readback_sha256="d" * 64,
            source_isolation={"receipt_sha256": "e" * 64},
            independence={"receipt_sha256": "f" * 64},
            witness_binding={"witness_sha256": "1" * 64},
        )
        with (
            patch.object(
                adapter_module,
                "prepare_creator_live_a2_reconnect",
                return_value=SimpleNamespace(
                    plan=FieldNoteReconnectPlan(receipt)
                ),
            ),
            patch.object(
                candidate_v02,
                "read_post_a1_readback_v0_2",
                return_value=readback,
            ),
            patch.object(candidate_v02, "require_post_a1_gate_for_a2"),
        ):
            result = await adapter.run(
                (ROOT / cycle006.FIXED_TASK_IDENTITIES[1].path).read_text()
            )
        return result, factory, approvals

    def a1_transcript(
        self,
        *,
        proposal_before_source: bool = False,
        dangling_second_proposal: bool = False,
    ) -> list[dict[str, object]]:
        thread, turn = "thread-cycle-006-a1", "turn-cycle-006-a1"
        arguments = _candidate_proposal()
        messages = handshake_messages(
            self.repository,
            thread_id=thread,
            turn_id=turn,
        )
        proposal_start = _dynamic_event(
            "item/started",
            thread=thread,
            turn=turn,
            call="proposal-1",
            tool=FIELD_NOTE_TOOL_NAME,
            arguments=arguments,
            status="inProgress",
        )
        if proposal_before_source:
            messages.append(proposal_start)
        messages.extend(
            (
                _dynamic_event(
                    "item/started",
                    thread=thread,
                    turn=turn,
                    call="source-1",
                    tool=candidate_v02.SOURCE_TOOL_NAME,
                    arguments={},
                    status="inProgress",
                ),
                _tool_request(
                    thread=thread,
                    turn=turn,
                    call="source-1",
                    request="request-source-1",
                    tool=candidate_v02.SOURCE_TOOL_NAME,
                    arguments={},
                ),
                _dynamic_event(
                    "item/completed",
                    thread=thread,
                    turn=turn,
                    call="source-1",
                    tool=candidate_v02.SOURCE_TOOL_NAME,
                    arguments={},
                    status="completed",
                ),
            )
        )
        if not proposal_before_source:
            messages.append(proposal_start)
        messages.extend(
            (
                _tool_request(
                    thread=thread,
                    turn=turn,
                    call="proposal-1",
                    request="request-proposal-1",
                    tool=FIELD_NOTE_TOOL_NAME,
                    arguments=arguments,
                ),
                _dynamic_event(
                    "item/completed",
                    thread=thread,
                    turn=turn,
                    call="proposal-1",
                    tool=FIELD_NOTE_TOOL_NAME,
                    arguments=arguments,
                    status="completed",
                ),
            )
        )
        if dangling_second_proposal:
            messages.append(
                _dynamic_event(
                    "item/started",
                    thread=thread,
                    turn=turn,
                    call="proposal-2",
                    tool=FIELD_NOTE_TOOL_NAME,
                    arguments=arguments,
                    status="inProgress",
                )
            )
        messages.extend(
            (
                completed_agent_message(
                    thread_id=thread,
                    turn_id=turn,
                    text="done",
                ),
                completed_turn(thread_id=thread, turn_id=turn),
            )
        )
        return messages

    async def test_turn_start_response_loss_keeps_write_ahead_activity_visible(
        self,
    ) -> None:
        thread = "thread-cycle-006-response-loss"
        task = (ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path).read_text()
        messages = handshake_messages(
            self.repository,
            thread_id=thread,
            turn_id="turn-never-confirmed",
        )[:4]
        observer_calls: list[tuple[str, str]] = []
        adapter, factory = self.a1_adapter(
            messages,
            turn_start_intent_observer=lambda run_id: observer_calls.append(
                ("intent", run_id)
            ),
            turn_started_observer=lambda run_id: observer_calls.append(
                ("accepted", run_id)
            ),
        )

        with self.assertRaises(CodexAdapterFailure):
            await adapter.run(task)
        self.assertEqual(
            observer_calls,
            [("intent", "run-cycle-006-a1-fixture")],
        )
        turn_requests = [
            value
            for value in factory.transports[0].sent
            if value.get("method") == "turn/start"
        ]
        self.assertEqual(len(turn_requests), 1)
        self.assertEqual(
            turn_requests[0]["params"]["input"],
            [{"text": task, "type": "text"}],
        )

    async def test_a1_unadvertised_reader_returns_no_bytes_and_fails(self) -> None:
        thread, turn = "thread-cycle-006-a1", "turn-cycle-006-a1"
        messages = handshake_messages(
            self.repository,
            thread_id=thread,
            turn_id=turn,
        )
        messages.extend(
            (
                _dynamic_event(
                    "item/started",
                    thread=thread,
                    turn=turn,
                    call="read-1",
                    tool="read_repository_text_file",
                    arguments={"path": "target.txt"},
                    status="inProgress",
                ),
                _tool_request(
                    thread=thread,
                    turn=turn,
                    call="read-1",
                    request="request-read-1",
                    tool="read_repository_text_file",
                    arguments={"path": "target.txt"},
                ),
                completed_turn(thread_id=thread, turn_id=turn),
            )
        )
        adapter, factory = self.a1_adapter(messages)
        result = await adapter.run(
            (ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path).read_text()
        )
        self.assertFalse(result.normal_terminal)
        self.assertEqual(result.unsupported_reason, "unsupported_dynamic_tool")
        self.assertEqual(result.read_evidence, ())
        response = next(
            value
            for value in factory.transports[0].sent
            if value.get("id") == "request-read-1"
        )
        self.assertEqual(response["error"]["code"], -32601)
        self.assertNotIn("result", response)
        self.assertNotIn("bytes", str(response).lower())

    async def test_a1_proposal_start_before_source_disclosure_fails(self) -> None:
        adapter, _factory = self.a1_adapter(
            self.a1_transcript(proposal_before_source=True)
        )
        result = await adapter.run(
            (ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path).read_text()
        )
        self.assertFalse(result.normal_terminal)
        evidence = result.candidate_v0_2_isolation_evidence
        self.assertIsNotNone(evidence)
        self.assertFalse(evidence.proposal_after_source)
        self.assertEqual(
            result.creator_live_a1_failure_reason,
            "A1_CANDIDATE_INDEPENDENCE_NOT_PASS",
        )

    async def test_a1_dangling_second_proposal_start_fails(self) -> None:
        adapter, _factory = self.a1_adapter(
            self.a1_transcript(dangling_second_proposal=True)
        )
        result = await adapter.run(
            (ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path).read_text()
        )
        self.assertFalse(result.normal_terminal)
        evidence = result.candidate_v0_2_isolation_evidence
        self.assertIsNotNone(evidence)
        self.assertIn("PROPOSAL_ITEM_COUNT_INVALID", evidence.event_reason_codes)
        self.assertIn(
            "PROPOSAL_ITEM_LINEAGE_INCOMPLETE",
            evidence.event_reason_codes,
        )

    async def test_a1_source_request_is_exactly_once_and_never_replays_bytes(
        self,
    ) -> None:
        for request_id, call_id in (
            ("request-source-1", "source-1"),
            ("request-source-2", "source-1"),
            ("request-source-2", "source-2"),
        ):
            with self.subTest(request_id=request_id, call_id=call_id):
                transcript = self.a1_transcript()
                first_index = next(
                    index
                    for index, value in enumerate(transcript)
                    if value.get("id") == "request-source-1"
                )
                transcript.insert(
                    first_index + 1,
                    _tool_request(
                        thread="thread-cycle-006-a1",
                        turn="turn-cycle-006-a1",
                        call=call_id,
                        request=request_id,
                        tool=candidate_v02.SOURCE_TOOL_NAME,
                        arguments={},
                    ),
                )
                adapter, factory = self.a1_adapter(transcript)
                result = await adapter.run(
                    (ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path).read_text()
                )
                responses = [
                    value
                    for value in factory.transports[0].sent
                    if value.get("id") in {"request-source-1", request_id}
                ]
                disclosed = [value for value in responses if "result" in value]
                rejected = [value for value in responses if "error" in value]
                self.assertFalse(result.normal_terminal)
                self.assertEqual(len(disclosed), 1)
                self.assertEqual(len(rejected), 1)
                self.assertNotIn("result", rejected[0])
                self.assertNotIn("content", str(rejected[0]).lower())
                evidence = result.candidate_v0_2_isolation_evidence
                self.assertIsNotNone(evidence)
                self.assertEqual(evidence.semantic_disclosure_count, 1)
                self.assertIn(
                    "SOURCE_REQUEST_COUNT_INVALID",
                    evidence.event_reason_codes,
                )

    async def test_a1_source_item_start_and_completion_are_exactly_once(self) -> None:
        for method, call_id in (
            ("item/started", "source-1"),
            ("item/started", "source-2"),
            ("item/completed", "source-1"),
        ):
            with self.subTest(method=method, call_id=call_id):
                transcript = self.a1_transcript()
                target_index = next(
                    index
                    for index, value in enumerate(transcript)
                    if value.get("method") == method
                    and isinstance(value.get("params"), dict)
                    and value["params"]["item"].get("tool")
                    == candidate_v02.SOURCE_TOOL_NAME
                )
                transcript.insert(target_index + 1, deepcopy(transcript[target_index]))
                transcript[target_index + 1]["params"]["item"]["id"] = call_id
                adapter, _factory = self.a1_adapter(transcript)
                result = await adapter.run(
                    (ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path).read_text()
                )
                self.assertFalse(result.normal_terminal)
                evidence = result.candidate_v0_2_isolation_evidence
                self.assertIsNotNone(evidence)
                expected = (
                    "SOURCE_ITEM_COUNT_INVALID"
                    if method == "item/started"
                    else "SOURCE_ITEM_COMPLETION_DUPLICATE"
                )
                self.assertIn(expected, evidence.event_reason_codes)

    async def test_a1_proposal_request_item_and_completion_are_exactly_once(
        self,
    ) -> None:
        variants = (
            ("request", "request-proposal-1", "proposal-1"),
            ("request", "request-proposal-2", "proposal-1"),
            ("request", "request-proposal-2", "proposal-2"),
            ("item/started", None, "proposal-1"),
            ("item/started", None, "proposal-2"),
            ("item/completed", None, "proposal-1"),
        )
        for kind, request_id, call_id in variants:
            with self.subTest(kind=kind, request_id=request_id, call_id=call_id):
                transcript = self.a1_transcript()
                if kind == "request":
                    target_index = next(
                        index
                        for index, value in enumerate(transcript)
                        if value.get("id") == "request-proposal-1"
                    )
                    duplicate = _tool_request(
                        thread="thread-cycle-006-a1",
                        turn="turn-cycle-006-a1",
                        call=call_id,
                        request=request_id,
                        tool=FIELD_NOTE_TOOL_NAME,
                        arguments=_candidate_proposal(),
                    )
                else:
                    target_index = next(
                        index
                        for index, value in enumerate(transcript)
                        if value.get("method") == kind
                        and isinstance(value.get("params"), dict)
                        and value["params"]["item"].get("tool")
                        == FIELD_NOTE_TOOL_NAME
                    )
                    duplicate = deepcopy(transcript[target_index])
                    duplicate["params"]["item"]["id"] = call_id
                transcript.insert(target_index + 1, duplicate)
                adapter, factory = self.a1_adapter(transcript)
                result = await adapter.run(
                    (ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path).read_text()
                )
                self.assertFalse(result.normal_terminal)
                evidence = result.candidate_v0_2_isolation_evidence
                self.assertIsNotNone(evidence)
                if kind == "request":
                    rejected = [
                        value
                        for value in factory.transports[0].sent
                        if value.get("id") == request_id and "error" in value
                    ]
                    self.assertEqual(len(rejected), 1)
                    self.assertNotIn("result", rejected[0])
                    self.assertIn(
                        "PROPOSAL_REQUEST_COUNT_INVALID",
                        evidence.event_reason_codes,
                    )
                elif kind == "item/started":
                    self.assertIn(
                        "PROPOSAL_ITEM_COUNT_INVALID",
                        evidence.event_reason_codes,
                    )
                else:
                    self.assertIn(
                        "PROPOSAL_ITEM_COMPLETION_DUPLICATE",
                        evidence.event_reason_codes,
                    )

    async def test_candidate_dangling_file_change_start_is_non_mutating(self) -> None:
        thread, turn = "thread-cycle-006-a1", "turn-cycle-006-a1"
        changes = [
            change(
                path="candidate-output.md",
                kind="add",
                diff="@@ -0,0 +1 @@\n+forbidden\n",
            )
        ]
        a1_messages = self.a1_transcript()
        a1_messages.insert(
            -2,
            started_item(
                thread_id=thread,
                turn_id=turn,
                item_id="dangling-file-a1",
                changes=changes,
            ),
        )
        a1_adapter, _factory = self.a1_adapter(a1_messages)
        a1_result = await a1_adapter.run(
            (ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path).read_text()
        )
        self.assertFalse(a1_result.normal_terminal)
        self.assertEqual(a1_result.file_actions, ())
        self.assertEqual(a1_result.checkpoint_outcomes, ())

        a2_messages = handshake_messages(
            self.repository,
            thread_id="thread-cycle-006-a2",
            turn_id="turn-cycle-006-a2",
        )
        a2_messages.extend(
            (
                started_item(
                    thread_id="thread-cycle-006-a2",
                    turn_id="turn-cycle-006-a2",
                    item_id="dangling-file-a2",
                    changes=changes,
                ),
                completed_turn(
                    thread_id="thread-cycle-006-a2",
                    turn_id="turn-cycle-006-a2",
                ),
            )
        )
        a2_result, _factory, approvals = await self.run_a2_transcript(a2_messages)
        self.assertFalse(a2_result.normal_terminal)
        self.assertEqual(a2_result.file_actions, ())
        self.assertEqual(a2_result.checkpoint_outcomes, ())
        self.assertEqual(approvals, [])

    @staticmethod
    def _candidate_passive_items(task: str) -> list[dict[str, object]]:
        return [
            {"content": [{"text": task, "type": "text"}], "id": "user-1", "type": "userMessage"},
            {"content": ["bounded reasoning"], "id": "reasoning-1", "summary": [], "type": "reasoning"},
            {"id": "plan-1", "text": "One bounded step.", "type": "plan"},
        ]

    async def test_candidate_passive_allowlist_and_web_search_disable_are_exact(
        self,
    ) -> None:
        a1_task = (ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path).read_text()
        a1_messages = self.a1_transcript()
        insertion = next(
            index
            for index, value in enumerate(a1_messages)
            if value.get("method") == "item/started"
            and value["params"]["item"].get("tool")
            == candidate_v02.SOURCE_TOOL_NAME
        )
        passive_events: list[dict[str, object]] = []
        for item in self._candidate_passive_items(a1_task):
            passive_events.append(
                _passive_event(
                    "item/started",
                    thread="thread-cycle-006-a1",
                    turn="turn-cycle-006-a1",
                    item=deepcopy(item),
                )
            )
            if item["type"] != "userMessage":
                passive_events.append(
                    _passive_event(
                        "item/completed",
                        thread="thread-cycle-006-a1",
                        turn="turn-cycle-006-a1",
                        item=deepcopy(item),
                    )
                )
        a1_messages[insertion:insertion] = passive_events
        a1_adapter, a1_factory = self.a1_adapter(a1_messages)
        a1_result = await a1_adapter.run(a1_task)
        self.assertTrue(a1_result.normal_terminal)
        a1_start = next(
            value
            for value in a1_factory.transports[0].sent
            if value.get("method") == "thread/start"
        )
        self.assertEqual(a1_start["params"]["config"]["web_search"], "disabled")
        self.assertEqual(
            a1_start["params"]["config"]["project_doc_max_bytes"],
            0,
        )
        self.assertEqual(
            a1_start["params"]["config"]["project_doc_fallback_filenames"],
            [],
        )
        self.assertIs(
            a1_start["params"]["config"]["features"]["plugins"],
            False,
        )

        a2_task = (ROOT / cycle006.FIXED_TASK_IDENTITIES[1].path).read_text()
        a2_messages = handshake_messages(
            self.repository,
            thread_id="thread-cycle-006-a2",
            turn_id="turn-cycle-006-a2",
        )
        for item in self._candidate_passive_items(a2_task):
            a2_messages.append(
                _passive_event(
                    "item/started",
                    thread="thread-cycle-006-a2",
                    turn="turn-cycle-006-a2",
                    item=deepcopy(item),
                )
            )
            if item["type"] != "userMessage":
                a2_messages.append(
                    _passive_event(
                        "item/completed",
                        thread="thread-cycle-006-a2",
                        turn="turn-cycle-006-a2",
                        item=deepcopy(item),
                    )
                )
        a2_messages.extend(
            (
                completed_agent_message(
                    thread_id="thread-cycle-006-a2",
                    turn_id="turn-cycle-006-a2",
                    text="done",
                ),
                completed_turn(
                    thread_id="thread-cycle-006-a2",
                    turn_id="turn-cycle-006-a2",
                ),
            )
        )
        a2_result, a2_factory, _approvals = await self.run_a2_transcript(
            a2_messages
        )
        self.assertTrue(a2_result.normal_terminal)
        a2_start = next(
            value
            for value in a2_factory.transports[0].sent
            if value.get("method") == "thread/start"
        )
        self.assertEqual(a2_start["params"]["config"]["web_search"], "disabled")
        self.assertEqual(
            a2_start["params"]["config"]["project_doc_max_bytes"],
            0,
        )
        self.assertEqual(
            a2_start["params"]["config"]["project_doc_fallback_filenames"],
            [],
        )
        self.assertIs(
            a2_start["params"]["config"]["features"]["plugins"],
            False,
        )

    async def test_candidate_rejects_active_or_unknown_item_types_in_both_phases(
        self,
    ) -> None:
        prohibited_items = (
            {"id": "web-1", "query": "forbidden", "type": "webSearch"},
            {"id": "image-1", "path": "/forbidden", "type": "imageView"},
            {"id": "unknown-1", "type": "futureCapability"},
        )
        for method in ("item/started", "item/completed"):
            for prohibited in prohibited_items:
                with self.subTest(lane="A1", method=method, item=prohibited["type"]):
                    messages = self.a1_transcript()
                    messages.insert(
                        -2,
                        _passive_event(
                            method,
                            thread="thread-cycle-006-a1",
                            turn="turn-cycle-006-a1",
                            item=deepcopy(prohibited),
                        ),
                    )
                    adapter, _factory = self.a1_adapter(messages)
                    result = await adapter.run(
                        (ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path).read_text()
                    )
                    self.assertFalse(result.normal_terminal)
                    self.assertEqual(
                        result.unsupported_reason,
                        "unsupported_dynamic_tool",
                    )
                    evidence = result.candidate_v0_2_isolation_evidence
                    self.assertIsNotNone(evidence)
                    self.assertIn(
                        "CANDIDATE_ITEM_TYPE_NOT_ALLOWED",
                        evidence.event_reason_codes,
                    )

                with self.subTest(lane="A2", method=method, item=prohibited["type"]):
                    messages = handshake_messages(
                        self.repository,
                        thread_id="thread-cycle-006-a2",
                        turn_id="turn-cycle-006-a2",
                    )
                    messages.extend(
                        (
                            _passive_event(
                                method,
                                thread="thread-cycle-006-a2",
                                turn="turn-cycle-006-a2",
                                item=deepcopy(prohibited),
                            ),
                            completed_turn(
                                thread_id="thread-cycle-006-a2",
                                turn_id="turn-cycle-006-a2",
                            ),
                        )
                    )
                    result, _factory, approvals = await self.run_a2_transcript(
                        messages
                    )
                    self.assertFalse(result.normal_terminal)
                    self.assertEqual(
                        result.unsupported_reason,
                        "unsupported_dynamic_tool",
                    )
                    self.assertEqual(approvals, [])

    async def test_candidate_rejects_unapproved_notification_families(self) -> None:
        prohibited = (
            "item/commandExecution/outputDelta",
            "turn/diff/updated",
            "thread/compacted",
            "mcpServer/startupStatus/updated",
            "item/autoApprovalReview/started",
            "item/autoApprovalReview/completed",
            "guardianWarning",
            "future/capability/notification",
        )
        for lane in ("A1", "A2"):
            thread = f"thread-cycle-006-{lane.lower()}"
            turn = f"turn-cycle-006-{lane.lower()}"
            for method in prohibited:
                with self.subTest(lane=lane, method=method):
                    notification = {
                        "method": method,
                        "params": {
                            "delta": "forbidden",
                            "itemId": "hidden-capability",
                            "threadId": thread,
                            "turnId": turn,
                        },
                    }
                    if lane == "A1":
                        messages = self.a1_transcript()
                        messages.insert(-2, notification)
                        adapter, _factory = self.a1_adapter(messages)
                        result = await adapter.run(
                            (
                                ROOT / cycle006.FIXED_TASK_IDENTITIES[0].path
                            ).read_text()
                        )
                    else:
                        messages = handshake_messages(
                            self.repository,
                            thread_id=thread,
                            turn_id=turn,
                        )
                        messages.extend(
                            (
                                notification,
                                completed_turn(
                                    thread_id=thread,
                                    turn_id=turn,
                                ),
                            )
                        )
                        result, _factory, approvals = (
                            await self.run_a2_transcript(messages)
                        )
                        self.assertEqual(approvals, [])
                    self.assertFalse(result.normal_terminal)
                    self.assertEqual(
                        result.unsupported_reason,
                        "unsupported_request_method:other",
                    )
                    evidence = result.candidate_v0_2_isolation_evidence
                    if lane == "A1":
                        self.assertIsNotNone(evidence)
                        self.assertIn(
                            "CANDIDATE_NOTIFICATION_NOT_ALLOWED",
                            evidence.event_reason_codes,
                        )
                    else:
                        self.assertIsNone(evidence)

    async def test_candidate_accepts_only_validated_passive_notifications(
        self,
    ) -> None:
        thread, turn = "thread-cycle-006-a2", "turn-cycle-006-a2"
        messages = handshake_messages(
            self.repository,
            thread_id=thread,
            turn_id=turn,
        )
        for item in (
            {"id": "agent-passive", "text": "", "type": "agentMessage"},
            {"id": "plan-passive", "text": "", "type": "plan"},
            {
                "content": [],
                "id": "reasoning-passive",
                "summary": [],
                "type": "reasoning",
            },
        ):
            messages.append(
                _passive_event(
                    "item/started",
                    thread=thread,
                    turn=turn,
                    item=item,
                )
            )
        messages.extend(
            (
                {
                    "method": "item/agentMessage/delta",
                    "params": {
                        "delta": "bounded",
                        "itemId": "agent-passive",
                        "threadId": thread,
                        "turnId": turn,
                    },
                },
                {
                    "method": "item/plan/delta",
                    "params": {
                        "delta": "bounded",
                        "itemId": "plan-passive",
                        "threadId": thread,
                        "turnId": turn,
                    },
                },
                {
                    "method": "item/reasoning/summaryPartAdded",
                    "params": {
                        "itemId": "reasoning-passive",
                        "summaryIndex": 0,
                        "threadId": thread,
                        "turnId": turn,
                    },
                },
                {
                    "method": "item/reasoning/summaryTextDelta",
                    "params": {
                        "delta": "bounded",
                        "itemId": "reasoning-passive",
                        "summaryIndex": 0,
                        "threadId": thread,
                        "turnId": turn,
                    },
                },
                {
                    "method": "item/reasoning/textDelta",
                    "params": {
                        "contentIndex": 0,
                        "delta": "bounded",
                        "itemId": "reasoning-passive",
                        "threadId": thread,
                        "turnId": turn,
                    },
                },
                {
                    "method": "turn/plan/updated",
                    "params": {
                        "explanation": None,
                        "plan": [{"status": "pending", "step": "bounded"}],
                        "threadId": thread,
                        "turnId": turn,
                    },
                },
                {
                    "method": "thread/tokenUsage/updated",
                    "params": {
                        "threadId": thread,
                        "tokenUsage": {
                            "last": {
                                "cachedInputTokens": 0,
                                "inputTokens": 1,
                                "outputTokens": 1,
                                "reasoningOutputTokens": 0,
                                "totalTokens": 2,
                            },
                            "modelContextWindow": 100,
                            "total": {
                                "cachedInputTokens": 0,
                                "inputTokens": 1,
                                "outputTokens": 1,
                                "reasoningOutputTokens": 0,
                                "totalTokens": 2,
                            },
                        },
                        "turnId": turn,
                    },
                },
                {
                    "method": "thread/status/changed",
                    "params": {
                        "status": {"activeFlags": [], "type": "active"},
                        "threadId": thread,
                    },
                },
                {
                    "method": "turn/moderationMetadata",
                    "params": {
                        "metadata": {},
                        "threadId": thread,
                        "turnId": turn,
                    },
                },
                {
                    "method": "model/safetyBuffering/updated",
                    "params": {
                        "fasterModel": None,
                        "model": "gpt-5.6-sol",
                        "reasons": [],
                        "showBufferingUi": False,
                        "threadId": thread,
                        "turnId": turn,
                        "useCases": [],
                    },
                },
                {
                    "method": "warning",
                    "params": {"message": "bounded", "threadId": thread},
                },
                {
                    "method": "deprecationNotice",
                    "params": {"details": None, "summary": "bounded"},
                },
                completed_turn(thread_id=thread, turn_id=turn),
            )
        )
        result, _factory, approvals = await self.run_a2_transcript(messages)
        self.assertTrue(result.normal_terminal, result)
        self.assertEqual(approvals, [])

    async def test_candidate_rejects_malformed_passive_notification(self) -> None:
        thread, turn = "thread-cycle-006-a2", "turn-cycle-006-a2"
        messages = handshake_messages(
            self.repository,
            thread_id=thread,
            turn_id=turn,
        )
        messages.extend(
            (
                {
                    "method": "item/agentMessage/delta",
                    "params": {
                        "delta": "unbound",
                        "itemId": "missing-item",
                        "threadId": thread,
                        "turnId": turn,
                    },
                },
                completed_turn(thread_id=thread, turn_id=turn),
            )
        )
        result, _factory, approvals = await self.run_a2_transcript(messages)
        self.assertFalse(result.normal_terminal)
        self.assertIsNone(result.unsupported_reason)
        self.assertEqual(approvals, [])
        self.assertIsNone(result.candidate_v0_2_isolation_evidence)

    async def test_candidate_user_message_is_exact_fixed_task_and_one_item(self) -> None:
        for lane, task_index in (("A1", 0), ("A2", 1)):
            with self.subTest(lane=lane):
                task = (ROOT / cycle006.FIXED_TASK_IDENTITIES[task_index].path).read_text()
                first = {
                    "content": [{"text": task, "type": "text"}],
                    "id": "user-1",
                    "type": "userMessage",
                }
                second = deepcopy(first)
                second["id"] = "user-2"
                thread = f"thread-cycle-006-{lane.lower()}"
                turn = f"turn-cycle-006-{lane.lower()}"
                if lane == "A1":
                    messages = self.a1_transcript()
                    insertion = next(
                        index
                        for index, value in enumerate(messages)
                        if value.get("method") == "item/started"
                    )
                    messages[insertion:insertion] = [
                        _passive_event(
                            "item/started",
                            thread=thread,
                            turn=turn,
                            item=first,
                        ),
                        _passive_event(
                            "item/started",
                            thread=thread,
                            turn=turn,
                            item=second,
                        ),
                    ]
                    adapter, _factory = self.a1_adapter(messages)
                    result = await adapter.run(task)
                    evidence = result.candidate_v0_2_isolation_evidence
                    self.assertIsNotNone(evidence)
                    self.assertIn(
                        "CANDIDATE_USER_MESSAGE_COUNT_INVALID",
                        evidence.event_reason_codes,
                    )
                else:
                    messages = handshake_messages(
                        self.repository,
                        thread_id=thread,
                        turn_id=turn,
                    )
                    messages.extend(
                        (
                            _passive_event(
                                "item/started",
                                thread=thread,
                                turn=turn,
                                item=first,
                            ),
                            _passive_event(
                                "item/started",
                                thread=thread,
                                turn=turn,
                                item=second,
                            ),
                            completed_turn(thread_id=thread, turn_id=turn),
                        )
                    )
                    result, _factory, _approvals = await self.run_a2_transcript(
                        messages
                    )
                self.assertFalse(result.normal_terminal)

    async def test_candidate_user_message_rejects_nonfixed_task(self) -> None:
        for lane, task_index in (("A1", 0), ("A2", 1)):
            with self.subTest(lane=lane):
                task = (ROOT / cycle006.FIXED_TASK_IDENTITIES[task_index].path).read_text()
                bad_item = {
                    "content": [
                        {"text": task + "unexpected", "type": "text"}
                    ],
                    "id": "user-bad",
                    "type": "userMessage",
                }
                thread = f"thread-cycle-006-{lane.lower()}"
                turn = f"turn-cycle-006-{lane.lower()}"
                event = _passive_event(
                    "item/started",
                    thread=thread,
                    turn=turn,
                    item=bad_item,
                )
                if lane == "A1":
                    messages = self.a1_transcript()
                    messages.insert(
                        next(
                            index
                            for index, value in enumerate(messages)
                            if value.get("method") == "item/started"
                        ),
                        event,
                    )
                    adapter, _factory = self.a1_adapter(messages)
                    result = await adapter.run(task)
                    evidence = result.candidate_v0_2_isolation_evidence
                    self.assertIsNotNone(evidence)
                    self.assertIn(
                        "CANDIDATE_USER_MESSAGE_INVALID",
                        evidence.event_reason_codes,
                    )
                else:
                    messages = handshake_messages(
                        self.repository,
                        thread_id=thread,
                        turn_id=turn,
                    )
                    messages.extend(
                        (
                            event,
                            completed_turn(thread_id=thread, turn_id=turn),
                        )
                    )
                    result, _factory, _approvals = await self.run_a2_transcript(
                        messages
                    )
                self.assertFalse(result.normal_terminal)

    async def test_a2_file_change_is_declined_without_public_approval(self) -> None:
        thread, turn = "thread-cycle-006-a2", "turn-cycle-006-a2"
        changes = [
            change(
                path="candidate-output.md",
                kind="add",
                diff="@@ -0,0 +1 @@\n+forbidden\n",
            )
        ]
        messages = handshake_messages(
            self.repository,
            thread_id=thread,
            turn_id=turn,
        )
        messages.extend(
            (
                started_item(
                    thread_id=thread,
                    turn_id=turn,
                    item_id="file-1",
                    changes=changes,
                ),
                approval_request(
                    thread_id=thread,
                    turn_id=turn,
                    item_id="file-1",
                    request_id="approval-file-1",
                ),
                resolved_request(
                    thread_id=thread,
                    request_id="approval-file-1",
                ),
                completed_item(
                    thread_id=thread,
                    turn_id=turn,
                    item_id="file-1",
                    changes=changes,
                    status="declined",
                ),
                completed_turn(thread_id=thread, turn_id=turn),
            )
        )
        factory = FakeTransportFactory([messages])
        target = exact_a2.FieldNoteCreatorLiveA2ReconnectTarget._issue(
            authority=exact_a2._A2_TARGET_AUTHORITY,
            proof_attempt_id="proof-a2",
            run_1_id="run-a1",
            run_2_id="run-a2",
            field_note_id="fn-a2",
            note_relative_path=".decision-os/field-notes/fn-a2.md",
            note_sha256="a" * 64,
            note_byte_count=1,
            source_repository_id="repo:v1:" + "b" * 64,
            source_commit="c" * 40,
            expected_runtime_identity=cycle006.EXPECTED_CODEX_RUNTIME,
        )
        receipt = FieldNoteReconnectReceipt(
            run_id="run-a2",
            state="NO_MATCH",
            failure_reason=None,
            metadata_entries_seen=0,
            metadata_candidate_files_seen=0,
            metadata_files_valid=0,
            metadata_bytes_read=0,
            selected_field_note_path=None,
            selected_field_note_id=None,
            selected_metadata_sha256=None,
            selected_full_note_sha256=None,
            full_note_bytes_read=0,
            full_notes_injected=0,
            ordinary_distinct_paths_consumed=0,
        )
        approvals: list[object] = []
        adapter = FieldNotesCodexAdapter(
            AccelerationEngine(
                self.repository,
                adapter=ADAPTER_NAME,
                adapter_version=CODEX_CLI_VERSION,
            ),
            input_func=lambda: self.fail("no public input permitted"),
            stdout=io.StringIO(),
            approval_provider=lambda approval: approvals.append(approval) or "deny",
            transport_factory=factory,
            creator_live_a2_reconnect_provider=lambda: target,
            candidate_v0_2_a2_provider=lambda: (
                FieldNoteCreatorLiveCandidateV02A2Config(
                    readback_path="unused",
                    readback_sha256="d" * 64,
                )
            ),
        )
        readback = SimpleNamespace(
            result="PASS",
            readback_sha256="d" * 64,
            source_isolation={"receipt_sha256": "e" * 64},
            independence={"receipt_sha256": "f" * 64},
            witness_binding={"witness_sha256": "1" * 64},
        )
        with (
            patch.object(
                adapter_module,
                "prepare_creator_live_a2_reconnect",
                return_value=SimpleNamespace(
                    plan=FieldNoteReconnectPlan(receipt)
                ),
            ),
            patch.object(
                candidate_v02,
                "read_post_a1_readback_v0_2",
                return_value=readback,
            ),
            patch.object(candidate_v02, "require_post_a1_gate_for_a2"),
        ):
            result = await adapter.run(
                (ROOT / cycle006.FIXED_TASK_IDENTITIES[1].path).read_text()
            )
        decisions = [
            value["result"]["decision"]
            for value in factory.transports[0].sent
            if isinstance(value.get("result"), dict)
            and "decision" in value["result"]
        ]
        self.assertFalse(result.normal_terminal)
        self.assertEqual(approvals, [])
        self.assertEqual(decisions, ["decline"])
        events = factory.transports[0].events
        self.assertLess(
            events.index("approval_completed:decline"),
            events.index("received:serverRequest/resolved"),
        )

    async def test_a2_unadvertised_reader_returns_no_bytes_and_fails(self) -> None:
        thread, turn = "thread-cycle-006-a2", "turn-cycle-006-a2"
        messages = handshake_messages(
            self.repository,
            thread_id=thread,
            turn_id=turn,
        )
        messages.extend(
            (
                _dynamic_event(
                    "item/started",
                    thread=thread,
                    turn=turn,
                    call="read-a2",
                    tool="read_repository_text_file",
                    arguments={"path": "target.txt"},
                    status="inProgress",
                ),
                _tool_request(
                    thread=thread,
                    turn=turn,
                    call="read-a2",
                    request="request-read-a2",
                    tool="read_repository_text_file",
                    arguments={"path": "target.txt"},
                ),
                completed_turn(thread_id=thread, turn_id=turn),
            )
        )
        factory = FakeTransportFactory([messages])
        target = exact_a2.FieldNoteCreatorLiveA2ReconnectTarget._issue(
            authority=exact_a2._A2_TARGET_AUTHORITY,
            proof_attempt_id="proof-a2",
            run_1_id="run-a1",
            run_2_id="run-a2",
            field_note_id="fn-a2",
            note_relative_path=".decision-os/field-notes/fn-a2.md",
            note_sha256="a" * 64,
            note_byte_count=1,
            source_repository_id="repo:v1:" + "b" * 64,
            source_commit="c" * 40,
            expected_runtime_identity=cycle006.EXPECTED_CODEX_RUNTIME,
        )
        receipt = FieldNoteReconnectReceipt(
            run_id="run-a2",
            state="NO_MATCH",
            failure_reason=None,
            metadata_entries_seen=0,
            metadata_candidate_files_seen=0,
            metadata_files_valid=0,
            metadata_bytes_read=0,
            selected_field_note_path=None,
            selected_field_note_id=None,
            selected_metadata_sha256=None,
            selected_full_note_sha256=None,
            full_note_bytes_read=0,
            full_notes_injected=0,
            ordinary_distinct_paths_consumed=0,
        )
        adapter = FieldNotesCodexAdapter(
            AccelerationEngine(
                self.repository,
                adapter=ADAPTER_NAME,
                adapter_version=CODEX_CLI_VERSION,
            ),
            input_func=lambda: self.fail("no public input permitted"),
            stdout=io.StringIO(),
            approval_provider=lambda _approval: self.fail(
                "no public approval permitted"
            ),
            transport_factory=factory,
            creator_live_a2_reconnect_provider=lambda: target,
            candidate_v0_2_a2_provider=lambda: (
                FieldNoteCreatorLiveCandidateV02A2Config(
                    readback_path="unused",
                    readback_sha256="d" * 64,
                )
            ),
        )
        readback = SimpleNamespace(
            result="PASS",
            readback_sha256="d" * 64,
            source_isolation={"receipt_sha256": "e" * 64},
            independence={"receipt_sha256": "f" * 64},
            witness_binding={"witness_sha256": "1" * 64},
        )
        with (
            patch.object(
                adapter_module,
                "prepare_creator_live_a2_reconnect",
                return_value=SimpleNamespace(
                    plan=FieldNoteReconnectPlan(receipt)
                ),
            ),
            patch.object(
                candidate_v02,
                "read_post_a1_readback_v0_2",
                return_value=readback,
            ),
            patch.object(candidate_v02, "require_post_a1_gate_for_a2"),
        ):
            result = await adapter.run(
                (ROOT / cycle006.FIXED_TASK_IDENTITIES[1].path).read_text()
            )
        self.assertFalse(result.normal_terminal)
        self.assertEqual(result.unsupported_reason, "unsupported_dynamic_tool")
        self.assertEqual(result.read_evidence, ())
        response = next(
            value
            for value in factory.transports[0].sent
            if value.get("id") == "request-read-a2"
        )
        self.assertEqual(response["error"]["code"], -32601)
        self.assertNotIn("result", response)
        self.assertNotIn("bytes", str(response).lower())


class Cycle006ProtectedBindingTests(unittest.TestCase):
    @unittest.skipUnless(
        _RUN_CANONICAL,
        "requires canonical local Cycle 005 proof storage",
    )
    def test_candidate_v01_v02_and_cycle005_guards_match_canonical_repository(self) -> None:
        entrypoint = CreatorLiveCycle006Entrypoint(object())
        historical = entrypoint._historical_binding(ROOT)
        cycle_005 = historical["cycle_005"]
        self.assertEqual(
            (
                cycle_005["journal_sha256"],
                cycle_005["anchor_sha256"],
                cycle_005["typed_readback_sha256"],
            ),
            (
                CYCLE_005_JOURNAL_SHA256,
                CYCLE_005_ANCHOR_SHA256,
                CYCLE_005_READBACK_SHA256,
            ),
        )
        self.assertEqual(historical["candidate_v0_1"]["protected_file_count"], 18)
        self.assertEqual(historical["candidate_v0_2"]["protected_file_count"], 15)
        self.assertTrue(historical["candidate_v0_1"]["immutable"])
        self.assertTrue(historical["candidate_v0_2"]["immutable"])

    def test_common_before_tasks_schemas_source_isolation_and_a3_are_bound(self) -> None:
        candidate = CreatorLiveCycle006Entrypoint(object())._candidate_binding(ROOT)
        before = candidate["common_before"]
        self.assertEqual(
            (before["utf8_byte_count"], before["line_count"], before["sha256"]),
            (
                20_705,
                517,
                "e856160413a9d47622779dede6a2eeca9fd027284d815b155ab6e323a74863db",
            ),
        )
        self.assertEqual(
            candidate["dynamic_tool_manifest"]["run_1_tool_names"],
            [
                "read_candidate_historical_before_v0_2",
                "propose_field_note_candidate",
            ],
        )
        self.assertEqual(candidate["dynamic_tool_manifest"]["run_2_dynamic_tools"], [])
        self.assertEqual(len(candidate["schema_identities"]), 6)
        self.assertEqual(candidate["gates"]["run_2_open_before_all_pass"], False)
        self.assertEqual(candidate["a3_overlay"]["eligible_candidate_count"], 1)
        self.assertEqual(candidate["a3_overlay"]["winning_candidate_count"], 1)
        self.assertEqual(candidate["behavior"]["state_before_execution"], "NOT_RUN")

    def test_launch_binding_is_deterministic_content_free_and_non_ranking(self) -> None:
        entrypoint = CreatorLiveCycle006Entrypoint(
            object(),
            spec=CreatorLiveCycle006Spec(repository=ROOT, runtime_root=ROOT),
            runtime_version_probe=lambda _path: (
                cycle006.EXPECTED_CODEX_RUNTIME.codex_cli_version
            ),
        )
        head = "b" * 40

        def git_value(_repository: Path, *arguments: str) -> str:
            command = tuple(arguments)
            values = {
                ("rev-parse", "HEAD"): head,
                ("rev-parse", "main"): head,
                ("rev-parse", "origin/main"): head,
                ("branch", "--show-current"): "main",
                ("remote", "get-url", "origin"): cycle006.EXPECTED_REMOTE,
                ("rev-list", "--left-right", "--count", "main...origin/main"): "0\t0",
                ("status", "--porcelain", "--untracked-files=no"): "",
            }
            return values[command]

        candidate = CreatorLiveCycle006Entrypoint(object())._candidate_binding(ROOT)
        historical = deepcopy(_full_fixture_binding()["historical_boundary"])
        contract = {
            "filename": cycle006.CONTRACT_FILENAME,
            "source_byte_count": 11_039,
            "source_sha256": cycle006.EXPECTED_CONTRACT_SHA256,
            "ordinary_contract_execution_authority": "INTERPRETATION_ONLY",
            "guided_intake_freeze_authority": "IMMUTABLE_INTERPRETATION_ONLY",
        }
        base = {"repository": {"path": str(ROOT)}}
        with (
            patch.object(cycle006, "_run_git", side_effect=git_value),
            patch.object(cycle006, "_git_diff_clean", return_value=True),
            patch.object(cycle006, "repository_id", return_value="repository-id"),
            patch.object(cycle006, "product_tree_sha256", return_value="c" * 64),
            patch.object(entrypoint, "_git_common_dir", return_value=ROOT / ".git"),
            patch.object(entrypoint, "_contract_binding", return_value=contract),
            patch.object(entrypoint, "_historical_binding", return_value=historical),
            patch.object(entrypoint, "_candidate_binding", return_value=candidate),
        ):
            first = entrypoint._p0(base)
            second = entrypoint._p0(base)
        self.assertTrue(first.ready)
        self.assertEqual(first.launch_binding_sha256, second.launch_binding_sha256)
        self.assertRegex(first.launch_binding_sha256 or "", r"^[0-9a-f]{64}$")
        binding = first.binding or {}
        self.assertEqual(binding["cycle"]["live_start_authorization"], "ABSENT")
        self.assertEqual(binding["attempt_policy"]["retry_count"], 0)
        self.assertEqual(binding["attempt_policy"]["replacement_count"], 0)
        self.assertEqual(
            binding["runtime"],
            {
                **EXPECTED_RUNTIME,
                "run_1_dynamic_tools_exact": True,
                "run_2_exact_a2_reconnect_only": True,
                "candidate_feature_flags": {"plugins": False},
                "project_doc_fallback_filenames": [],
                "project_doc_max_bytes": 0,
                "disabled_capabilities": binding["runtime"][
                    "disabled_capabilities"
                ],
            },
        )
        self.assertIn(
            "project_document_injection",
            binding["runtime"]["disabled_capabilities"],
        )
        self.assertEqual(binding["comparison"]["result_before_execution"], "NOT_ESTABLISHED")
        self.assertFalse(binding["comparison"]["lane_b_human_ai_manual"]["candidate_visible"])
        self.assertEqual(binding["reduction_boundary"]["core_statement"], cycle006.REDUCTION_CORE_STATEMENT)
        self.assertFalse(binding["reduction_boundary"]["ranking"])
        self.assertEqual(binding["pre_live_state"]["artifact_behavior"], "NOT_RUN")
        encoded = json.dumps(binding, sort_keys=True)
        self.assertNotIn(cycle006.CANDIDATE_DEVELOPER_INSTRUCTIONS, encoded)
        self.assertNotIn("A3 Witness: ", encoded)


class Cycle006PortableLineageTests(unittest.TestCase):
    def test_each_exact_lineage_group_fails_closed_on_one_tampered_value(self) -> None:
        groups = {
            "repository_identity": ("head", "head", "head"),
            "preparation_id": ("preparation", "preparation"),
            "request_id": ("request", "request", "request"),
            "draft_id": ("draft", "draft", "draft"),
            "draft_sha256": ("draft-sha", "draft-sha"),
            "wrapper_sha256": ("wrapper-sha", "wrapper-sha"),
            "interpretation_sha256": (
                "interpretation-sha",
                "interpretation-sha",
            ),
            "gate": ("gate", "gate"),
            "freeze_id": ("freeze", "freeze"),
            "frozen_intake_sha256": ("frozen-sha", "frozen-sha"),
            "freeze_receipt_sha256": ("receipt-sha", "receipt-sha"),
            "predecessor_event_head": ("previous", "previous"),
            "current_event_head": ("current", "current"),
            "original_event_head": ("original", "original"),
        }
        cycle006._require_exact_lineage(groups)
        for label in groups:
            with self.subTest(label=label):
                tampered = deepcopy(groups)
                tampered[label] = (*tampered[label][:-1], "tampered")
                with self.assertRaisesRegex(
                    ValueError,
                    "P0_CONTRACT_LINEAGE_MISMATCH",
                ):
                    cycle006._require_exact_lineage(tampered)


class Cycle006FakeCoordinatorTests(unittest.TestCase):
    def test_exact_tasks_and_candidate_gate_overlay_order_without_provider(self) -> None:
        order: list[str] = []
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "repository"
            repository.mkdir()
            expected_tasks: list[bytes] = []
            for identity in cycle006.FIXED_TASK_IDENTITIES:
                raw = (ROOT / identity.path).read_bytes()
                target = repository / identity.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                expected_tasks.append(raw)

            note_bytes = b"# Exact fake note\nReusable structure.\n"
            note = cycle006.FieldNoteIdentity(
                note_path=".decision-os/field-notes/fake-cycle-006.md",
                field_note_id="FN-CYCLE-006-FAKE",
                note_sha256=cycle006._sha256(note_bytes),
                origin_run_id="run-1-cycle-006-fake",
            )
            completion = SimpleNamespace(
                task_byte_count=len(expected_tasks[1]),
                task_sha256=cycle006._sha256(expected_tasks[1]),
                actual_runtime_identity=cycle006.EXPECTED_CODEX_RUNTIME,
                reconnect_receipt=object(),
                final_output_bytes=b"fake exact A3 output\n",
                final_output_sha256=cycle006._sha256(
                    b"fake exact A3 output\n"
                ),
            )

            class FakeController:
                def start_creator_live_candidate_v0_2_a2(
                    self,
                    task: str,
                    **_kwargs: object,
                ) -> None:
                    self_task = task.encode("utf-8")
                    if self_task != expected_tasks[1]:
                        raise AssertionError("Run 2 task bytes changed")
                    order.append("run-2-start")

                @staticmethod
                def creator_live_a2_failure_reason(
                    **_kwargs: object,
                ) -> None:
                    return None

                @staticmethod
                def creator_live_a2_run_completion(
                    **_kwargs: object,
                ) -> object:
                    return completion

                @staticmethod
                def release_creator_live_a2_run_completion(
                    **_kwargs: object,
                ) -> None:
                    return None

            proof_attempt_id = "proof-cycle-006-fake"

            class FakeRuntime:
                @staticmethod
                def read_back() -> object:
                    return SimpleNamespace(
                        proof_attempt_id=proof_attempt_id,
                        run_2=SimpleNamespace(run_id="run-2-cycle-006-fake"),
                        attempt=object(),
                        run_1=object(),
                        events=(),
                    )

                @staticmethod
                def open_run_2(_identity: object) -> None:
                    order.append("run-2-open")

                @staticmethod
                def record_a2_reconnect(
                    *_args: object,
                    **_kwargs: object,
                ) -> None:
                    order.append("a2-recorded")

                @staticmethod
                def record_run_2_output_identity(_identity: object) -> None:
                    order.append("a2-output-identity")

                @staticmethod
                def record_a3_compiler_audit(audit: object) -> object:
                    return SimpleNamespace(a3_compiler_audit=audit)

                @staticmethod
                def record_a3_reuse(*_args: object, **_kwargs: object) -> None:
                    order.append("a3-recorded")

                @staticmethod
                def record_a4_durability(*_args: object, **_kwargs: object) -> None:
                    order.append("a4-recorded")

                @staticmethod
                def record_a5_confirmation(*_args: object, **_kwargs: object) -> None:
                    order.append("a5-recorded")

                @staticmethod
                def record_a6_review(*_args: object, **_kwargs: object) -> None:
                    order.append("a6-recorded")

            entrypoint = CreatorLiveCycle006Entrypoint(
                FakeController(),
                spec=CreatorLiveCycle006Spec(repository=repository),
                now=lambda: "2026-08-06T01:00:00Z",
            )
            post_a1 = SimpleNamespace(witness_binding={})
            post_sha = "8" * 64

            def capture_a1(**kwargs: object) -> tuple[object, object, bytes, object, str]:
                if kwargs["task_bytes"] != expected_tasks[0]:
                    raise AssertionError("Run 1 task bytes changed")
                if str(kwargs["task"]).encode("utf-8") != expected_tasks[0]:
                    raise AssertionError("Run 1 task text changed")
                order.append("run-1-capture")
                return object(), note, note_bytes, post_a1, post_sha

            def require_post(value: object) -> None:
                if value is not post_a1:
                    raise AssertionError("unexpected Post-A1 gate")
                order.append("post-a1-required")

            audit = SimpleNamespace(terminal_a3_code=None)

            def compiler(**_kwargs: object) -> tuple[object, object]:
                order.append("generic-a3-compiler")
                return object(), audit

            def candidate_witness(*_args: object) -> object:
                order.append("candidate-witness")
                return object()

            def overlay(*_args: object, **_kwargs: object) -> str:
                order.append("candidate-overlay")
                return "9" * 64

            def generic_reuse(*_args: object, **_kwargs: object) -> object:
                order.append("generic-reuse")
                return assessment

            assessment = SimpleNamespace(state="REUSED")
            durable_snapshot = object()
            commit = SimpleNamespace(
                durable_snapshot=durable_snapshot,
                assessment=assessment,
            )

            source = cycle006.FieldNoteSourceRepositoryIdentity(
                repository_id="repo:v1:" + "a" * 64,
                source_commit="b" * 40,
            )
            p0 = CreatorLiveCycle006P0Result(
                True,
                None,
                _full_fixture_binding(),
                _DIGEST,
            )
            with (
                patch.object(entrypoint, "_capture_a1", side_effect=capture_a1),
                patch.object(entrypoint, "_wait_for_controller_run"),
                patch.object(entrypoint, "_fail_open_runtime"),
                patch.object(
                    cycle006,
                    "require_post_a1_gate_for_a2",
                    side_effect=require_post,
                ),
                patch.object(
                    cycle006,
                    "creator_live_a2_target_from_readback",
                    return_value=object(),
                ),
                patch.object(
                    cycle006,
                    "prepare_creator_live_a2_reconnect",
                    return_value=SimpleNamespace(note_bytes=note_bytes),
                ),
                patch.object(
                    cycle006,
                    "compile_run_2_output_artifact_audited",
                    side_effect=compiler,
                ),
                patch.object(cycle006, "WitnessBindingV02", return_value=object()),
                patch.object(
                    cycle006,
                    "verify_a3_winner_witness_v0_2",
                    side_effect=candidate_witness,
                ),
                patch.object(cycle006, "_persist_a3_overlay", side_effect=overlay),
                patch.object(
                    cycle006,
                    "_claim_from_verified_a3_audit",
                    return_value=object(),
                ),
                patch.object(
                    cycle006,
                    "assess_field_note_reuse",
                    side_effect=generic_reuse,
                ),
                patch.object(cycle006, "FieldNoteMaturityLedger", return_value=object()),
                patch.object(
                    cycle006,
                    "FieldNoteMaturityCommitRequest",
                    return_value=object(),
                ),
                patch.object(
                    cycle006,
                    "commit_field_note_maturity",
                    return_value=commit,
                ),
                patch.object(
                    cycle006,
                    "review_field_note_maturity",
                    return_value=object(),
                ),
                patch.object(
                    cycle006,
                    "FieldNoteWholeFlowEvidenceBundle",
                    return_value=object(),
                ),
                patch.object(
                    cycle006,
                    "verify_field_note_whole_flow",
                    return_value=SimpleNamespace(
                        state="PASS",
                        failure_reason=None,
                        receipt_sha256="a" * 64,
                    ),
                ),
                patch.object(
                    cycle006,
                    "build_portable_candidate_warehouse_manifest",
                    return_value=SimpleNamespace(manifest_id="b" * 64),
                ),
            ):
                entrypoint._run_sequence(FakeRuntime(), source, p0)

            self.assertEqual(
                order,
                [
                    "run-1-capture",
                    "post-a1-required",
                    "run-2-open",
                    "run-2-start",
                    "a2-recorded",
                    "a2-output-identity",
                    "generic-a3-compiler",
                    "candidate-witness",
                    "candidate-overlay",
                    "generic-reuse",
                    "a3-recorded",
                    "a4-recorded",
                    "a5-recorded",
                    "a6-recorded",
                ],
            )
            self.assertEqual(entrypoint._terminal_state, "PASS")
            self.assertIsNone(entrypoint._terminal_failure_code)
            self.assertEqual(entrypoint._receipt_sha256, "a" * 64)
            self.assertEqual(entrypoint._manifest_sha256, "b" * 64)
            self.assertFalse(os.path.lexists(entrypoint.spec.storage_root))


@unittest.skipUnless(
    _RUN_CANONICAL,
    "requires canonical local Guided Intake and Ordinary User Path state",
)
class Cycle006ContractLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entrypoint = CreatorLiveCycle006Entrypoint(object())
        cls.common = cls.entrypoint._git_common_dir(ROOT)
        cls.head = cycle006._run_git(ROOT, "rev-parse", "HEAD")
        cls.ordinary = _canonical_ordinary_contract_snapshot(cls.common)

    def bind(self, ordinary: dict[str, object]) -> dict[str, object]:
        return self.entrypoint._contract_binding(
            repository=ROOT,
            common=self.common,
            head=self.head,
            base_snapshot={"ordinary_contract": ordinary},
        )

    @staticmethod
    def replace(
        value: dict[str, object],
        path: tuple[str, ...],
        replacement: object,
    ) -> None:
        target: dict[str, object] = value
        for key in path[:-1]:
            nested = target[key]
            assert isinstance(nested, dict)
            target = nested
        target[path[-1]] = replacement

    def test_exact_canonical_lineage_is_bound_across_all_projections(self) -> None:
        contract = self.bind(deepcopy(self.ordinary))
        self.assertEqual(contract["preparation_id"], self.ordinary["preparation_id"])
        self.assertEqual(contract["request_id"], self.ordinary["technical_details"]["request_id"])
        self.assertEqual(contract["draft_id"], self.ordinary["technical_details"]["draft_id"])
        self.assertEqual(contract["freeze_id"], self.ordinary["technical_details"]["freeze"]["freeze_id"])

    def test_projection_tampering_is_rejected_before_launch_binding(self) -> None:
        mutations = (
            ("preparation-id", ("preparation_id",), "OUP-PREP-TAMPERED"),
            (
                "active-request-id",
                ("technical_details", "active_request_id"),
                "GI-REQ-TAMPERED",
            ),
            (
                "request-id",
                ("technical_details", "request_id"),
                "GI-REQ-TAMPERED",
            ),
            (
                "draft-id",
                ("technical_details", "draft_id"),
                "GI-DRAFT-TAMPERED",
            ),
            (
                "preparation-repository",
                ("technical_details", "preparation_repository_identity"),
                "0" * 40,
            ),
            (
                "producer",
                ("technical_details", "producer_identity"),
                "TAMPERED_PRODUCER",
            ),
            (
                "freeze-repository",
                ("technical_details", "freeze", "repository_identity"),
                "0" * 40,
            ),
            (
                "freeze-request",
                ("technical_details", "freeze", "request_id"),
                "GI-REQ-TAMPERED",
            ),
            (
                "freeze-draft",
                ("technical_details", "freeze", "draft_id"),
                "GI-DRAFT-TAMPERED",
            ),
            (
                "freeze-interpretation",
                ("technical_details", "freeze", "interpretation_sha256"),
                "1" * 64,
            ),
            (
                "freeze-id",
                ("technical_details", "freeze", "freeze_id"),
                "GI-FREEZE-TAMPERED",
            ),
            (
                "frozen-intake",
                ("technical_details", "freeze", "frozen_intake_sha256"),
                "2" * 64,
            ),
            (
                "freeze-receipt",
                ("technical_details", "freeze", "receipt_sha256"),
                "3" * 64,
            ),
        )
        for label, path, replacement in mutations:
            with self.subTest(label=label):
                ordinary = deepcopy(self.ordinary)
                self.replace(ordinary, path, replacement)
                with self.assertRaisesRegex(
                    ValueError,
                    "P0_CONTRACT_LINEAGE_MISMATCH",
                ):
                    self.bind(ordinary)


class _FakeCycle005:
    def __init__(self, _controller: object) -> None:
        self.mutation_blocked = False
        self.started: list[str] = []

    def snapshot(self, _base: object) -> dict[str, object]:
        return {
            "cycle_key": "cycle-005",
            "state": "FAILED",
            "stage": "A3_REUSE",
            "p0": {"ready": False, "failure_code": "CYCLE_005_ATTEMPT_EXISTS"},
            "launch_binding_sha256": "5" * 64,
            "binding": None,
            "identities": {"failure_code": "A3_EXACT_STRUCTURE_MISSING"},
            "storage_occupied": True,
            "start_allowed": False,
        }

    def start(self, digest: str) -> None:
        self.started.append(digest)
        raise CreatorLiveEntrypointError("CYCLE_005_ATTEMPT_EXISTS")


class _FakeCycle006:
    def __init__(self, controller: object) -> None:
        self.controller = controller
        self.mutation_blocked = False
        self.started: list[str] = []
        self.controller_condition_owned: bool | None = None

    def snapshot(self, _base: object) -> dict[str, object]:
        return {
            "cycle_key": "cycle-006",
            "cycle_number": "006",
            "candidate_id": "CREATOR_LIVE_AGENTS_BEFORE_AFTER_V0_2",
            "state": "READY",
            "stage": "P0",
            "p0": {"ready": True, "failure_code": None},
            "launch_binding_sha256": _DIGEST,
            "binding": CreatorLiveCycle006Entrypoint._public_binding(
                _full_fixture_binding()
            ),
            "live_start_authorization": "ABSENT",
            "one_attempt": True,
            "retry_count": 0,
            "replacement_count": 0,
            "storage_occupied": False,
            "start_allowed": False,
            "proof_identity": None,
            "model_invocation_count": 0,
            "task_transmission_count": 0,
            "artifact_behavior": "NOT_RUN",
            "comparison_result": "NOT_ESTABLISHED",
        }

    def start(self, digest: str) -> None:
        condition = getattr(self.controller, "_condition", None)
        is_owned = getattr(condition, "_is_owned", None)
        self.controller_condition_owned = bool(
            callable(is_owned) and is_owned()
        )
        self.started.append(digest)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise CreatorLiveCycle006Error("LAUNCH_BINDING_INVALID", http_status=400)
        if digest != _DIGEST:
            raise CreatorLiveCycle006Error("LAUNCH_BINDING_STALE")
        raise CreatorLiveCycle006Error("LIVE_START_AUTHORIZATION_ABSENT")


class Cycle006ControllerConcurrencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = create_repository(self.root)
        self.controller = FieldNotesCompanionController(
            state_path=self.root / "state.json",
            picker_script=self.root / "picker.applescript",
            picker_runner=lambda _script: str(self.repository),
            adapter_factory=ScriptedFactory("read_only"),
            creator_live_entrypoint_factory=_FakeCycle005,
            creator_live_cycle_006_entrypoint_factory=_FakeCycle006,
        )
        self.controller.select_repository(self.repository)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_start_rejects_active_run_selection_and_other_operation(self) -> None:
        cycle = self.controller._creator_live_cycle_006
        states = (
            ("run", lambda: self.controller._run.__setitem__("state", "running")),
            (
                "selection",
                lambda: setattr(self.controller, "_repository_selection_active", True),
            ),
            (
                "guided",
                lambda: setattr(self.controller, "_active_guided_intake_operations", 1),
            ),
        )
        for label, activate in states:
            with self.subTest(label=label):
                with self.controller._condition:
                    self.controller._run["state"] = "idle"
                    self.controller._repository_selection_active = False
                    self.controller._active_guided_intake_operations = 0
                    activate()
                with self.assertRaisesRegex(
                    CreatorLiveCycle006Error,
                    "CYCLE_006_CONTROLLER_BUSY",
                ):
                    self.controller.creator_live_cycle_006_start(_DIGEST)
                self.assertEqual(cycle.started, [])

    def test_start_claim_and_mutation_guards_share_controller_condition(self) -> None:
        cycle = self.controller._creator_live_cycle_006
        with self.assertRaisesRegex(
            CreatorLiveCycle006Error,
            "LIVE_START_AUTHORIZATION_ABSENT",
        ):
            self.controller.creator_live_cycle_006_start(_DIGEST)
        self.assertTrue(cycle.controller_condition_owned)
        cycle.mutation_blocked = True
        with self.assertRaisesRegex(
            FieldNoteError,
            "CREATOR_LIVE_CYCLE_006_ACTIVE",
        ):
            self.controller.new_run()
        with self.assertRaisesRegex(
            FieldNoteError,
            "CREATOR_LIVE_CYCLE_006_ACTIVE",
        ):
            self.controller.select_repository(self.repository)

    def test_active_cycle_blocks_field_note_save_skip_and_approval_atomically(
        self,
    ) -> None:
        cycle = self.controller._creator_live_cycle_006
        draft_sentinel = object()
        pending_sentinel = object()
        with self.controller._condition:
            self.controller._run["state"] = "completed"
            self.controller._run["field_note"] = {"state": "approval"}
            self.controller._field_note_draft = draft_sentinel
            self.controller._field_note_pending = pending_sentinel
            cycle.mutation_blocked = True

        for operation in (
            self.controller.field_note_save,
            self.controller.field_note_skip,
            lambda: self.controller.field_note_approval("allow_once"),
        ):
            with self.subTest(operation=operation), self.assertRaisesRegex(
                FieldNoteError,
                "CREATOR_LIVE_CYCLE_006_ACTIVE",
            ):
                operation()

        with self.controller._condition:
            self.assertIs(self.controller._field_note_draft, draft_sentinel)
            self.assertIs(self.controller._field_note_pending, pending_sentinel)
            self.assertEqual(
                self.controller._run["field_note"],
                {"state": "approval"},
            )

    def test_only_active_cycle_entrypoint_can_use_internal_save_authority(
        self,
    ) -> None:
        cycle = self.controller._creator_live_cycle_006
        note_bytes = b"# Cycle 006 internal fixture\n"
        draft = SimpleNamespace(
            title="Cycle 006 internal fixture",
            relative_path=".decision-os/field-notes/fn-cycle-006-fixture.md",
            markdown=note_bytes,
            sha256=cycle006._sha256(note_bytes),
        )
        with self.controller._condition:
            self.controller._run["state"] = "completed"
            self.controller._run["field_note"] = {"state": "candidate"}
            self.controller._field_note_draft = draft
            cycle.mutation_blocked = True

        with self.assertRaisesRegex(
            FieldNoteError,
            "CREATOR_LIVE_CYCLE_006_INTERNAL_AUTHORITY_INVALID",
        ):
            self.controller.field_note_save(_cycle_006_authority=object())

        with (
            patch.object(
                self.controller,
                "_safe_candidate_path",
                return_value=draft,
            ),
            patch.object(
                self.controller,
                "_capture_parent_identities",
                return_value=((1, 1), (2, 2), (3, 3)),
            ),
            patch(
                "decision_os.companion.field_notes_controller."
                "validate_compiled_markdown"
            ),
        ):
            approval = self.controller.field_note_save(
                _cycle_006_authority=cycle
            )
        self.assertEqual(approval["run"]["field_note"]["state"], "approval")

        with patch.object(self.controller, "_write_pending") as write_pending:
            saved = self.controller.field_note_approval(
                "allow_once",
                _cycle_006_authority=cycle,
            )
        write_pending.assert_called_once()
        self.assertEqual(
            saved["run"]["field_note"],
            {"state": "saved", "path": draft.relative_path},
        )

        cycle.mutation_blocked = False
        with self.assertRaisesRegex(
            FieldNoteError,
            "CREATOR_LIVE_CYCLE_006_INTERNAL_AUTHORITY_INVALID",
        ):
            self.controller.field_note_approval(
                "allow_once",
                _cycle_006_authority=cycle,
            )


class Cycle006HTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        repository = create_repository(self.root)
        self.controller = FieldNotesCompanionController(
            state_path=self.root / "state.json",
            picker_script=self.root / "picker.applescript",
            picker_runner=lambda _script: str(repository),
            adapter_factory=ScriptedFactory("read_only"),
            creator_live_entrypoint_factory=_FakeCycle005,
            creator_live_cycle_006_entrypoint_factory=_FakeCycle006,
        )
        self.controller.select_repository(repository)
        self.server = CompanionServer(
            self.controller,
            static_root=ROOT / "decision_os/companion/static",
        )
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
        self.assertEqual(status, 303)
        cookie = headers["set-cookie"].split(";", 1)[0]
        status, _headers, raw = self.request(
            "GET", "/api/state", cookie=cookie, content_type=None
        )
        self.assertEqual(status, 200)
        return cookie, json.loads(raw)["csrf"]

    def post(
        self,
        raw: bytes,
        cookie: str,
        csrf: str,
        *,
        path: str = "/api/creator-live/cycles/006/start",
        **kwargs: object,
    ) -> tuple[int, bytes]:
        status, _headers, body = self.request(
            "POST",
            path,
            payload=raw,
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
            **kwargs,
        )
        return status, body

    def test_route_requires_session_loopback_host_origin_and_csrf(self) -> None:
        raw = json.dumps({"launch_binding_sha256": _DIGEST}).encode()
        self.assertEqual(self.post(raw, "", "")[0], 401)
        cookie, csrf = self.bootstrap()
        self.assertEqual(self.post(raw, cookie, csrf, host="attacker.invalid")[0], 403)
        status, _headers, _body = self.request(
            "POST",
            "/api/creator-live/cycles/006/start",
            payload=raw,
            cookie=cookie,
            csrf=csrf,
            origin="http://attacker.invalid",
        )
        self.assertEqual(status, 403)
        status, _headers, _body = self.request(
            "POST",
            "/api/creator-live/cycles/006/start",
            payload=raw,
            cookie=cookie,
            origin=self.server.origin,
        )
        self.assertEqual(status, 403)

    def test_strict_schema_duplicate_keys_content_type_stale_and_absent_authority(self) -> None:
        cookie, csrf = self.bootstrap()
        invalid = (
            b"{}",
            b'{"launch_binding_sha256":1}',
            b'{"launch_binding_sha256":"' + _DIGEST.encode() + b'","extra":1}',
            b'{"launch_binding_sha256":"' + _DIGEST.encode() + b'","launch_binding_sha256":"' + _DIGEST.encode() + b'"}',
            b'{"launch_binding_sha256":"' + _DIGEST.upper().encode() + b'"}',
            b'{"launch_binding_sha256":"short"}',
            b'{"launch_binding_sha256":"' + _DIGEST.encode() + b'","task":"PRIVATE"}',
            b'{"launch_binding_sha256":"' + _DIGEST.encode() + b'","runtime":{}}',
            b'{"launch_binding_sha256":"' + _DIGEST.encode() + b'","proof_identity":"PRIVATE"}',
            b'{"launch_binding_sha256":"' + _DIGEST.encode() + b'","lane":"A1_ONLY"}',
            b'{"launch_binding_sha256":"' + _DIGEST.encode() + b'","source":"alternate"}',
        )
        for raw in invalid:
            with self.subTest(raw=raw):
                self.assertEqual(self.post(raw, cookie, csrf)[0], 400)
        self.assertEqual(
            self.post(
                json.dumps({"launch_binding_sha256": _DIGEST}).encode(),
                cookie,
                csrf,
                content_type="text/plain",
            )[0],
            415,
        )
        status, body = self.post(
            json.dumps({"launch_binding_sha256": _STALE}).encode(), cookie, csrf
        )
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)["error"], "LAUNCH_BINDING_STALE")
        status, body = self.post(
            json.dumps({"launch_binding_sha256": _DIGEST}).encode(), cookie, csrf
        )
        self.assertEqual(status, 409)
        self.assertEqual(
            json.loads(body)["error"], "LIVE_START_AUTHORIZATION_ABSENT"
        )

    def test_refresh_cycle005_and_ordinary_routes_never_start_cycle006(self) -> None:
        cookie, csrf = self.bootstrap()
        for _ in range(8):
            status, _headers, raw = self.request(
                "GET", "/api/state", cookie=cookie, content_type=None
            )
            self.assertEqual(status, 200)
            cycle = json.loads(raw)["creator_live_cycle_006"]
            self.assertEqual((cycle["state"], cycle["stage"]), ("READY", "P0"))
            self.assertFalse(cycle["start_allowed"])
            self.assertIsNone(cycle["proof_identity"])
        self.assertEqual(self.controller._creator_live_cycle_006.started, [])
        self.post(
            json.dumps({"launch_binding_sha256": "5" * 64}).encode(),
            cookie,
            csrf,
            path="/api/creator-live/cycles/005/start",
        )
        self.assertEqual(self.controller._creator_live_cycle_006.started, [])
        self.post(
            json.dumps({"task": "ordinary fixture"}).encode(),
            cookie,
            csrf,
            path="/api/run",
        )
        self.assertEqual(self.controller._creator_live_cycle_006.started, [])

    def test_active_cycle006_blocks_other_posts_but_not_its_start_route(self) -> None:
        cookie, csrf = self.bootstrap()
        self.controller._creator_live_cycle_006.mutation_blocked = True
        status, body = self.post(
            json.dumps({"task": "ordinary fixture"}).encode(),
            cookie,
            csrf,
            path="/api/run",
        )
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)["error"], "CREATOR_LIVE_CYCLE_006_ACTIVE")
        status, body = self.post(
            json.dumps({"launch_binding_sha256": _DIGEST}).encode(),
            cookie,
            csrf,
        )
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(body)["error"], "LIVE_START_AUTHORIZATION_ABSENT")
        self.assertEqual(self.controller._creator_live_cycle_006.started, [_DIGEST])


class Cycle006UIStaticTests(unittest.TestCase):
    def test_ui_shows_required_content_free_fields_and_keeps_start_disabled(self) -> None:
        html = (ROOT / "decision_os/companion/static/index.html").read_text()
        script = (ROOT / "decision_os/companion/static/app.js").read_text()
        for marker in (
            'id="creator-live-cycle-006-card"',
            'id="creator-live-cycle-006-candidate"',
            'id="creator-live-cycle-006-revision"',
            'id="creator-live-cycle-006-before"',
            'id="creator-live-cycle-006-run-1"',
            'id="creator-live-cycle-006-run-2"',
            'id="creator-live-cycle-006-runtime"',
            'id="creator-live-cycle-006-history"',
            'id="creator-live-cycle-006-behavior"',
            'id="creator-live-cycle-006-comparison"',
            'id="creator-live-cycle-006-p0"',
            'id="creator-live-cycle-006-binding-sha256"',
            'id="creator-live-cycle-006-start"',
            "Start Cycle 006",
            "disabled",
        ):
            self.assertIn(marker, html)
        self.assertIn('cycle?.live_start_authorization === "PRESENT"', script)
        self.assertIn('cycle?.live_start_authorization !== "PRESENT"', script)
        self.assertIn('postJSON("/api/creator-live/cycles/006/start"', script)
        self.assertIn("cycle?.start_allowed !== true", script)
        for runtime_field in (
            "runtime.provider",
            "runtime.account",
            "runtime.model",
            "runtime.reasoning_effort",
            "runtime.service_tier",
            "runtime.codex_cli_version",
            "runtime.sandbox",
            "runtime.model_sandbox_network",
            "runtime.provider_transport_required",
            "runtime.fresh_ephemeral_thread_per_run",
            "runtime.repository_cwd",
        ):
            self.assertIn(runtime_field, script)
        for private in (
            cycle006.CANDIDATE_DEVELOPER_INSTRUCTIONS,
            "A3 Witness: ",
            "proof_a7_creator_live_cycle_006_" + _DIGEST,
        ):
            self.assertNotIn(private, html)
            self.assertNotIn(private, script)


@unittest.skipUnless(
    os.environ.get("DECISION_OS_CYCLE_006_EXACT_P0") == "1",
    "Exact-final-merge installed P0 is explicitly enabled after canonical install.",
)
class Cycle006ExactFinalP0Tests(unittest.TestCase):
    def test_installed_exact_final_merge_p0_is_unopened_and_truthful(self) -> None:
        runtime_root = Path(
            "/Users/sn/Library/Application Support/Decision OS Companion/runtime"
        ).resolve()
        installed_modules = (
            Path(cycle006.__file__).resolve(),
            Path(__import__(
                FieldNotesCompanionController.__module__,
                fromlist=["__file__"],
            ).__file__).resolve(),
        )
        for module_path in installed_modules:
            self.assertTrue(
                module_path == runtime_root or runtime_root in module_path.parents,
                f"expected installed module provenance under {runtime_root}, got {module_path}",
            )

        root = ROOT / ".decision-os/field-notes/proofs/cycle-006"
        self.assertFalse(os.path.lexists(root))
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            controller = FieldNotesCompanionController(
                state_path=temporary_root / "state.json",
                picker_script=temporary_root / "picker.applescript",
                picker_runner=lambda _script: str(ROOT),
                creator_live_cycle_006_entrypoint_factory=lambda owner: (
                    CreatorLiveCycle006Entrypoint(
                        owner,
                        spec=CreatorLiveCycle006Spec(
                            repository=ROOT,
                            runtime_root=runtime_root,
                        ),
                    )
                ),
            )
            state = controller.select_repository(ROOT)
            snapshot = state["creator_live_cycle_006"]
        observed_cli = cycle006._bundled_codex_cli_version(
            cycle006.BUNDLED_CODEX_PATH
        )
        exact_cli = cycle006.EXPECTED_CODEX_RUNTIME.codex_cli_version
        if observed_cli == exact_cli:
            self.assertEqual(
                (snapshot["state"], snapshot["stage"]),
                ("READY", "P0"),
            )
            self.assertTrue(snapshot["p0"]["ready"])
            self.assertIsNone(snapshot["p0"]["failure_code"])
        else:
            self.assertEqual(
                (snapshot["state"], snapshot["stage"]),
                ("NOT_READY", "P0"),
            )
            self.assertFalse(snapshot["p0"]["ready"])
            self.assertEqual(
                snapshot["p0"]["failure_code"],
                "P0_CODEX_CLI_VERSION_MISMATCH",
            )
        self.assertIsInstance(snapshot["binding"], dict)
        self.assertRegex(snapshot["launch_binding_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(snapshot["live_start_authorization"], "ABSENT")
        self.assertFalse(snapshot["start_allowed"])
        self.assertFalse(snapshot["storage_occupied"])
        self.assertIsNone(snapshot["proof_identity"])
        self.assertEqual(snapshot["model_invocation_count"], 0)
        self.assertEqual(snapshot["task_transmission_count"], 0)
        self.assertEqual(snapshot["artifact_behavior"], "NOT_RUN")
        self.assertEqual(snapshot["comparison_result"], "NOT_ESTABLISHED")
        self.assertFalse(snapshot["publication_authorized"])
        self.assertFalse(os.path.lexists(root))


if __name__ == "__main__":
    unittest.main()
