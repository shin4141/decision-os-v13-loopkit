from __future__ import annotations

from collections import deque
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from typing import Any
from unittest.mock import Mock

from decision_os.acceleration.codex_adapter import (
    CODEX_CLI_VERSION,
    CODEX_MODEL,
    CODEX_REASONING_EFFORT,
    CODEX_SERVICE_TIER,
    CodexAdapterFailure,
    CodexApproval,
    CodexFileAction,
    CodexLifecycleEvent,
    CodexRunResult,
    CodexRuntimeIdentity,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import DecisionType
from decision_os.companion.controller import (
    ApprovalStateError,
    CompanionController,
    CompanionStateError,
    RepositorySelectionError,
    RunConflictError,
)
from decision_os.companion.guided_intake import (
    GuidedIntakeBusyError,
    GuidedIntakeIntegrityError,
)
from decision_os.companion.intelligence_transplant import (
    IntelligenceTransplantIntegrityError,
    IntelligenceTransplantValidationError,
)
from decision_os.companion.manual_bridge import ManualBridgeIntegrityError


EVIDENCE_COMMIT = "970ae5e24e59dada54e1b829229360d9945a0910"
EVIDENCE_BLOB_SHA = "92f9f69f18db052b421fa5fa7f233ce77f5a42b8"
EVIDENCE_SHA256 = (
    "847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab"
)
PRODUCT_AS_OF_COMMIT = "63eb260a94595298e2b07b476f7f9d8572c9ef09"


def intelligence_transplant_projection(
    **overrides: Any,
) -> dict[str, Any]:
    return {
        "run_id": "IT-RUN-001",
        "run_type": "intelligence_transplant",
        "execution_status": "NOT_ESTABLISHED",
        "delta_state": "NONE",
        "current_gate": "HOLD",
        "missing_evidence": ["E1_DISCOVERY"],
        "next_one_action": "Attach provenance-valid E1.",
        "not_allowed_next": ["MODEL_INVOCATION", "ROLE_ASSIGNMENT"],
        "evidence_objects": [],
        "lineage": [],
        "active_cap": None,
        "generalized_transplant": "NOT ESTABLISHED",
        "structural_validation": "PASS",
        "authority_provenance": "MANUAL OWNER ATTESTED",
        "cryptographic_provenance": "NOT ESTABLISHED",
        "error": None,
        **overrides,
    }


def bridge_boundary() -> dict[str, Any]:
    return {
        "task_id": "V13-CMB-001",
        "protocol_run_id": "V13-PMR-002",
        "objective": "Implement the bounded Companion Manual Bridge v0.1.",
        "completion_line": (
            "Bridge evidence is ready for separate independent audit."
        ),
        "do_not_touch": "AccelerationStore and Verified Save semantics.",
        "current_gate": "GO UNDER CAP — FRESH BUILDER IMPLEMENTATION ONLY",
        "authority_boundary": (
            "Artifact identity is evidence only and grants no execution authority."
        ),
        "as_of_commit": PRODUCT_AS_OF_COMMIT,
        "required_next_actor": "Fresh SOL / coding-agent Builder",
        "evidence_packet_identity": {
            "commit": EVIDENCE_COMMIT,
            "path": (
                "validation/"
                "companion_manual_bridge_v0_1_shared_evidence_packet.md"
            ),
            "blob_sha": EVIDENCE_BLOB_SHA,
            "sha256": EVIDENCE_SHA256,
            "product_as_of_commit": PRODUCT_AS_OF_COMMIT,
        },
    }


def pro_design_metadata() -> dict[str, Any]:
    return {
        "schema": "decision-os-companion-manual-bridge-record-v0.1",
        "task_id": "V13-CMB-001",
        "protocol_run_id": "V13-PMR-002",
        "artifact_role": "PRO_DESIGN",
        "model_identity": {
            "value": "GPT-5.6 Thinking",
            "basis": "SELF_DECLARED",
            "verification_state": "UNVERIFIED",
        },
        "role_identity": "Independent Pro Designer",
        "artifact_authored_at": "2026-07-28T22:00:00+09:00",
        "as_of_commit": PRODUCT_AS_OF_COMMIT,
        "evidence_packet_commit": EVIDENCE_COMMIT,
        "evidence_packet_blob_sha": EVIDENCE_BLOB_SHA,
        "evidence_packet_sha256": EVIDENCE_SHA256,
        "authority_state": "DESIGN_ONLY_NO_EXECUTION_AUTHORITY",
        "required_next_actor": "Fresh SOL / coding-agent Builder",
        "objective": "Implement the bounded Companion Manual Bridge v0.1.",
        "completion_line": (
            "Bridge evidence is ready for separate independent audit."
        ),
        "do_not_touch": "AccelerationStore and Verified Save semantics.",
        "current_gate": "HOLD — SEPARATE BUILDER AUTHORITY REQUIRED",
        "authority_boundary": "INSTRUCTION_ARTIFACT_ONLY",
        "unknowns": ["Independent Product Result remains UNKNOWN."],
    }


def create_repository(parent: Path, name: str = "repo") -> Path:
    repository = parent / name
    repository.mkdir()
    completed = subprocess.run(
        ("git", "init", "-q", str(repository)),
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    (repository / "target.txt").write_text("before\n", encoding="utf-8")
    return repository


def runtime_identity() -> CodexRuntimeIdentity:
    return CodexRuntimeIdentity(
        model=CODEX_MODEL,
        reasoning_effort=CODEX_REASONING_EFFORT,
        service_tier=CODEX_SERVICE_TIER,
        codex_cli_version=CODEX_CLI_VERSION,
        account_type="chatgpt",
    )


class ScriptedAdapter:
    def __init__(
        self,
        engine: AccelerationEngine,
        approval_provider: Any,
        lifecycle_sink: Any,
        mode: str,
    ) -> None:
        self.engine = engine
        self.approval_provider = approval_provider
        self.lifecycle_sink = lifecycle_sink
        self.mode = mode

    async def run(self, prompt: str) -> CodexRunResult:
        del prompt
        self.lifecycle_sink(
            CodexLifecycleEvent("runtime", "Starting the private Codex runtime.")
        )
        if self.mode == "malformed":
            self.lifecycle_sink({"kind": "raw", "message": "<script>"})
        if self.mode == "failure":
            raise CodexAdapterFailure("sensitive raw adapter failure")
        if self.mode == "read_only":
            return CodexRunResult(
                run_id=self.engine.new_run_id(),
                normal_terminal=True,
                status="NORMAL_TERMINAL",
                error_type=None,
                turn_status="completed",
                runtime_identity=runtime_identity(),
                checkpoint_outcomes=(),
                final_message="Read-only result.",
            )

        run_id = self.engine.new_run_id()
        outcome = self.engine.evaluate(
            run_id=run_id,
            iteration=1,
            decision_type=DecisionType.MODIFY_FILE,
            requested_scope="target.txt",
            source_interrupt_id="private-test-item",
            choice_provider=lambda identity: self.approval_provider(
                CodexApproval(
                    repository_name=self.engine.store.repository.name,
                    action="Modify",
                    normalized_scope=identity.normalized_scope,
                    diff=(
                        "--- a/target.txt\n"
                        "+++ b/target.txt\n"
                        "@@\n-before\n+after\n"
                    ),
                    reason="Apply the bounded update.",
                )
            ),
        )
        if not outcome.allowed:
            return CodexRunResult(
                run_id=run_id,
                normal_terminal=False,
                status="DENIED",
                error_type=None,
                turn_status="completed",
                runtime_identity=runtime_identity(),
                checkpoint_outcomes=(),
                final_message="The change was denied.",
                file_actions=(
                    CodexFileAction(
                        "Modify",
                        "target.txt",
                        "denied",
                        "denied",
                    ),
                ),
            )
        checkpoint = self.engine.finish_checkpoint(
            outcome,
            normal_terminal=True,
            checkpoint_id=f"companion-test:{run_id}",
        )
        access = {
            "ALLOW_ONCE": "one-time",
            "HUMAN_DEFAULT_CREATED": "newly-saved",
            "DEFAULT_MATCHED": "reused",
        }.get(outcome.status, "newly-saved")
        status = checkpoint.status if checkpoint.verified else "NORMAL_TERMINAL"
        return CodexRunResult(
            run_id=run_id,
            normal_terminal=True,
            status=status,
            error_type=None,
            turn_status="completed",
            runtime_identity=runtime_identity(),
            checkpoint_outcomes=(checkpoint,),
            final_message="Mutation result.",
            file_actions=(
                CodexFileAction(
                    "Modify",
                    "target.txt",
                    access,
                    "approved",
                ),
            ),
        )


class ScriptedFactory:
    def __init__(self, *modes: str) -> None:
        self.modes = deque(modes)

    def __call__(
        self,
        engine: AccelerationEngine,
        approval_provider: Any,
        lifecycle_sink: Any,
    ) -> ScriptedAdapter:
        return ScriptedAdapter(
            engine,
            approval_provider,
            lifecycle_sink,
            self.modes.popleft(),
        )


def wait_for(
    controller: CompanionController,
    predicate: Any,
    timeout: float = 4,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        snapshot = controller.snapshot()
        if predicate(snapshot):
            return snapshot
        time.sleep(0.01)
    raise AssertionError(f"Timed out waiting for companion state: {snapshot!r}")


class CompanionControllerTest(unittest.TestCase):
    def make_controller(
        self,
        directory: Path,
        factory: ScriptedFactory,
        *,
        picker_result: str | None = None,
    ) -> CompanionController:
        return CompanionController(
            state_path=directory / "application-state" / "state.json",
            picker_script=directory / "fixed-picker.applescript",
            picker_runner=lambda _script: picker_result,
            adapter_factory=factory,
        )

    def test_picker_validates_git_root_and_rejects_non_git(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory(),
                picker_result=str(repository),
            )

            snapshot = controller.pick_repository()

            self.assertEqual(
                str(repository.resolve()),
                snapshot["repository"]["path"],
            )
            non_git = root / "plain"
            non_git.mkdir()
            controller = self.make_controller(
                root / "other",
                ScriptedFactory(),
                picker_result=str(non_git),
            )
            with self.assertRaises(RepositorySelectionError):
                controller.pick_repository()

    def test_state_file_is_0600_and_contains_only_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(root, ScriptedFactory())

            controller.select_repository(repository)

            state_path = root / "application-state" / "state.json"
            self.assertEqual(
                {"repository": str(repository.resolve())},
                json.loads(state_path.read_text(encoding="utf-8")),
            )
            self.assertEqual(
                0o600,
                stat.S_IMODE(state_path.stat().st_mode),
            )
            invalid = root / "invalid-state.json"
            invalid.write_text(
                json.dumps(
                    {
                        "repository": str(repository),
                        "prompt": "must not persist",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(CompanionStateError):
                CompanionController(
                    state_path=invalid,
                    picker_runner=lambda _script: None,
                )

    def test_read_only_result_has_zero_verified_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            controller.select_repository(repository)

            controller.start_run("Read the target without changing it.")
            snapshot = wait_for(
                controller,
                lambda state: state["run"]["state"] == "completed",
            )

            self.assertEqual("Read-only result.", snapshot["run"]["result"])
            self.assertEqual(
                {
                    "estimated_minutes": 0.0,
                    "estimated_money_jpy": 0.0,
                    "estimated_tokens": None,
                    "verified_reuses": 0,
                    "verified_saves": 0,
                },
                snapshot["run"]["receipt_delta"],
            )
            self.assertEqual(0, snapshot["receipt"]["verified_saves"])

    def test_allow_once_deny_and_repository_default_choices(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)

            allow = self.make_controller(root / "allow", ScriptedFactory("mutation"))
            allow.select_repository(repository)
            allow.start_run("Modify target once.")
            wait_for(allow, lambda state: state["run"]["approval"] is not None)
            allow.submit_approval("allow_once")
            allowed = wait_for(
                allow,
                lambda state: state["run"]["state"] == "completed",
            )
            self.assertEqual("one-time", allowed["run"]["file_actions"][0]["access"])
            self.assertEqual([], allowed["defaults"])

            deny = self.make_controller(root / "deny", ScriptedFactory("mutation"))
            deny.select_repository(repository)
            deny.start_run("Attempt a denied modification.")
            wait_for(deny, lambda state: state["run"]["approval"] is not None)
            deny.submit_approval("deny")
            denied = wait_for(
                deny,
                lambda state: state["run"]["state"] == "denied",
            )
            self.assertEqual("denied", denied["run"]["file_actions"][0]["access"])

            saved = self.make_controller(root / "saved", ScriptedFactory("mutation"))
            saved.select_repository(repository)
            saved.start_run("Save exact access.")
            approval = wait_for(
                saved,
                lambda state: state["run"]["approval"] is not None,
            )["run"]["approval"]
            self.assertEqual(
                {
                    "action": "Modify",
                    "diff": (
                        "--- a/target.txt\n"
                        "+++ b/target.txt\n"
                        "@@\n-before\n+after\n"
                    ),
                    "path": "target.txt",
                    "reason": "Apply the bounded update.",
                    "repository": "repo",
                },
                approval,
            )
            saved.submit_approval("repository")
            persisted = wait_for(
                saved,
                lambda state: state["run"]["state"] == "completed",
            )
            self.assertEqual(
                "newly-saved",
                persisted["run"]["file_actions"][0]["access"],
            )
            self.assertEqual(1, len(persisted["defaults"]))

    def test_default_reuse_receipt_delta_enumeration_and_revoke(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("mutation", "mutation"),
            )
            controller.select_repository(repository)
            controller.start_run("Create exact saved access.")
            wait_for(controller, lambda state: state["run"]["approval"] is not None)
            controller.submit_approval("repository")
            first = wait_for(
                controller,
                lambda state: state["run"]["state"] == "completed",
            )
            self.assertEqual(0, first["receipt"]["verified_saves"])
            self.assertEqual(1, len(first["defaults"]))

            controller.new_run()
            controller.start_run("Reuse exact saved access.")
            second = wait_for(
                controller,
                lambda state: state["run"]["state"] == "completed",
            )

            self.assertEqual(1, second["run"]["receipt_delta"]["verified_saves"])
            self.assertEqual(1, second["run"]["receipt_delta"]["verified_reuses"])
            self.assertEqual(7.5, second["run"]["receipt_delta"]["estimated_minutes"])
            self.assertEqual(625.0, second["run"]["receipt_delta"]["estimated_money_jpy"])
            self.assertIsNone(second["run"]["receipt_delta"]["estimated_tokens"])
            self.assertEqual(1, second["receipt"]["verified_saves"])
            self.assertEqual(1, second["receipt"]["verified_reuses"])
            handle = second["defaults"][0]["handle"]

            revoked = controller.revoke_default(handle)

            self.assertEqual([], revoked["defaults"])
            self.assertEqual(1, revoked["receipt"]["verified_saves"])
            with self.assertRaises(ApprovalStateError):
                controller.submit_approval("allow_once")

    def test_one_active_run_and_browser_reconnect_to_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("mutation"),
            )
            controller.select_repository(repository)
            controller.start_run("Wait for approval.")
            first = wait_for(
                controller,
                lambda state: state["run"]["approval"] is not None,
            )

            second = controller.snapshot()

            self.assertEqual(first["run"]["approval"], second["run"]["approval"])
            with self.assertRaises(RunConflictError):
                controller.start_run("Overlapping Run.")
            with self.assertRaises(RunConflictError):
                controller.select_repository(repository)
            controller.submit_approval("deny")
            wait_for(
                controller,
                lambda state: state["run"]["state"] == "denied",
            )

    def test_manual_bridge_lifecycle_is_separate_from_run_and_receipt(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = ScriptedFactory("read_only")
            controller = self.make_controller(root, factory)
            selected = controller.select_repository(repository)
            receipt_before = selected["receipt"]
            run_before = selected["run"]

            started = controller.start_bridge_session(bridge_boundary())
            copied = controller.bridge_copy_for_pro()
            imported = controller.bridge_import_artifact(
                selected_role="PRO_DESIGN",
                payload=b"exact pro design bytes\r\n",
                source_path_or_label="accepted-pro-design.md",
                import_mode="BYTE_EXACT_FILE_IMPORT",
                metadata=pro_design_metadata(),
            )

            self.assertIsNotNone(started["manual_bridge"]["session"])
            self.assertIn(
                copied["manual_bridge"]["state"],
                {"COPY_READY", "DESIGN_IMPORTED"},
            )
            self.assertEqual(
                "PRO_DESIGN",
                imported["manual_bridge"]["imports"][0]["selected_role"],
            )
            self.assertEqual(receipt_before, imported["receipt"])
            self.assertEqual(run_before, imported["run"])
            self.assertEqual([], imported["defaults"])
            self.assertEqual(1, len(factory.modes))

    def test_guided_intake_lifecycle_is_separate_and_never_starts_runner(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = ScriptedFactory("read_only")
            controller = self.make_controller(root, factory)
            selected = controller.select_repository(repository)
            run_before = selected["run"]
            receipt_before = selected["receipt"]
            defaults_before = selected["defaults"]
            bridge_before = selected["manual_bridge"]
            bridge = controller._bridge
            self.assertIsNotNone(bridge)
            guided_intake = Mock()
            guided_intake.snapshot.return_value = {"state": "TEST_STATE"}
            controller._guided_intake = guided_intake
            delta = {"resolve_unknown_ids": []}

            snapshots = (
                controller.guided_intake_capture("  unclear task\r\n"),
                controller.guided_intake_copy_for_pro(),
                controller.guided_intake_import_draft(
                    '{"schema_version":"test"}',
                    "Independent Pro",
                ),
                controller.guided_intake_confirm(
                    "What is complete?",
                    "One frozen intake.",
                    delta,
                ),
                controller.guided_intake_freeze(),
                controller.guided_intake_transfer_to_bridge(),
            )

            guided_intake.capture.assert_called_once_with(
                "  unclear task\r\n",
                supersedes_request_id=None,
            )
            guided_intake.copy_for_pro.assert_called_once_with()
            guided_intake.import_draft.assert_called_once_with(
                '{"schema_version":"test"}',
                "Independent Pro",
            )
            guided_intake.confirm.assert_called_once_with(
                "What is complete?",
                "One frozen intake.",
                delta,
            )
            guided_intake.freeze.assert_called_once_with()
            guided_intake.transfer_to_bridge.assert_called_once_with(bridge)
            for snapshot in snapshots:
                self.assertEqual({"state": "TEST_STATE"}, snapshot["guided_intake"])
                self.assertEqual(run_before, snapshot["run"])
                self.assertEqual(receipt_before, snapshot["receipt"])
                self.assertEqual(defaults_before, snapshot["defaults"])
                self.assertEqual(bridge_before, snapshot["manual_bridge"])
            self.assertEqual(1, len(factory.modes))

    def test_intelligence_transplant_is_typed_and_never_starts_runner(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = ScriptedFactory("read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            projection = intelligence_transplant_projection()
            charter_source = {
                "completion_line": (
                    "Stage 5 structural state is restartable."
                ),
                "freeze_id": "GI-FREEZE-001",
                "frozen_intake_sha256": "a" * 64,
                "repository_head": "b" * 40,
            }
            charter = {
                "object_type": "RUN_CHARTER",
                "completion_line": charter_source["completion_line"],
                "repository_head": charter_source["repository_head"],
                "source_freeze_id": charter_source["freeze_id"],
                "source_freeze_sha256": (
                    charter_source["frozen_intake_sha256"]
                ),
            }
            guided_intake = Mock()
            guided_intake.charter_source.return_value = charter_source
            guided_intake.snapshot.return_value = {"state": "FROZEN"}
            guided_intake.store.transaction.return_value = nullcontext()
            intelligence_transplant = Mock()
            intelligence_transplant.freeze_charter.return_value = projection
            intelligence_transplant.snapshot.return_value = projection
            controller._guided_intake = guided_intake
            controller._intelligence_transplant = intelligence_transplant

            snapshot = controller.intelligence_transplant_freeze_charter(
                charter
            )

            intelligence_transplant.freeze_charter.assert_called_once_with(
                charter,
                charter_source=charter_source,
                repository_head=charter_source["repository_head"],
            )
            self.assertEqual(
                "intelligence_transplant",
                snapshot["run"]["run_type"],
            )
            self.assertEqual("active", snapshot["run"]["state"])
            self.assertEqual(
                "NOT_ESTABLISHED",
                snapshot["run"]["execution_status"],
            )
            self.assertIsNone(snapshot["run"]["approval"])
            self.assertIsNone(snapshot["run"]["runtime"])
            self.assertEqual(projection, snapshot["intelligence_transplant"])
            self.assertIsNone(controller._worker)
            self.assertEqual(1, len(factory.modes))

            with controller._guided_intake_transplant_operation():
                with self.assertRaises(GuidedIntakeBusyError):
                    controller.guided_intake_capture("concurrent mutation")

            with self.assertRaises(RunConflictError):
                controller.start_run("must not dispatch while Stage 5 is active")
            self.assertIsNone(controller._worker)
            self.assertEqual(1, len(factory.modes))

            with self.assertRaises(IntelligenceTransplantValidationError):
                controller.intelligence_transplant_freeze_charter(
                    {
                        **charter,
                        "source_freeze_sha256": "f" * 64,
                    }
                )
            self.assertEqual(
                1,
                intelligence_transplant.freeze_charter.call_count,
            )
            self.assertEqual(1, len(factory.modes))

            reset = controller.new_run()
            self.assertEqual("bounded_task", reset["run"]["run_type"])
            self.assertEqual("idle", reset["run"]["state"])
            self.assertEqual(projection, reset["intelligence_transplant"])
            self.assertEqual(1, len(factory.modes))

    def test_intelligence_transplant_transport_is_exact_and_route_typed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = ScriptedFactory("read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            projection = intelligence_transplant_projection(
                execution_status="ACTIVE",
            )
            intelligence_transplant = Mock()
            intelligence_transplant.attach_object.return_value = projection
            intelligence_transplant.snapshot.return_value = projection
            controller._intelligence_transplant = intelligence_transplant
            payload = (
                b'{"object_id":"E1-ONE","object_type":"E1_DISCOVERY"}'
            )
            payload_sha256 = hashlib.sha256(payload).hexdigest()

            snapshot = (
                controller.intelligence_transplant_attach_evidence(
                    payload=payload,
                    mode="BYTE_EXACT_FILE_IMPORT",
                    source_path_or_label="e1.json",
                    declared_sha256=payload_sha256,
                    context_evidence_ref=None,
                    as_of="2026-07-30T00:00:00Z",
                )
            )

            attached_record = (
                intelligence_transplant.attach_object.call_args.args[0]
            )
            transport = (
                intelligence_transplant.attach_object.call_args.kwargs[
                    "transport"
                ]
            )
            self.assertEqual("E1_DISCOVERY", attached_record["object_type"])
            self.assertEqual(payload, transport["payload"])
            self.assertEqual(
                "BYTE_EXACT_FILE_IMPORT",
                transport["transport_receipt"]["mode"],
            )
            self.assertEqual(
                "intelligence_transplant",
                snapshot["run"]["run_type"],
            )
            self.assertEqual(1, len(factory.modes))

            with self.assertRaises(IntelligenceTransplantValidationError):
                controller.intelligence_transplant_attach_receipt(
                    payload=payload,
                    mode="BYTE_EXACT_FILE_IMPORT",
                    source_path_or_label="wrong-route.json",
                    declared_sha256=payload_sha256,
                    context_evidence_ref=None,
                    as_of="2026-07-30T00:00:00Z",
                )
            self.assertEqual(
                1,
                intelligence_transplant.attach_object.call_count,
            )
            duplicate = (
                b'{"object_type":"E1_DISCOVERY",'
                b'"object_type":"E1_DISCOVERY"}'
            )
            with self.assertRaises(IntelligenceTransplantValidationError):
                controller.intelligence_transplant_attach_evidence(
                    payload=duplicate,
                    mode="BYTE_EXACT_FILE_IMPORT",
                    source_path_or_label="duplicate.json",
                    declared_sha256=hashlib.sha256(duplicate).hexdigest(),
                    context_evidence_ref=None,
                    as_of="2026-07-30T00:00:00Z",
                )
            self.assertEqual(
                1,
                intelligence_transplant.attach_object.call_count,
            )

    def test_intelligence_transplant_corruption_is_panel_local(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            selected = controller.select_repository(repository)
            intelligence_transplant = Mock()
            intelligence_transplant.snapshot.side_effect = (
                IntelligenceTransplantIntegrityError(
                    "sensitive Stage 5 path"
                )
            )
            controller._intelligence_transplant = intelligence_transplant

            snapshot = controller.snapshot()

            self.assertEqual(
                "BLOCKED_CORRUPT",
                snapshot["intelligence_transplant"]["store_state"],
            )
            self.assertEqual(
                "BLOCK",
                snapshot["intelligence_transplant"]["current_gate"],
            )
            self.assertNotIn("sensitive", json.dumps(snapshot))
            self.assertEqual(selected["run"], snapshot["run"])
            self.assertEqual(selected["receipt"], snapshot["receipt"])
            self.assertEqual(
                selected["defaults"],
                snapshot["defaults"],
            )
            self.assertEqual(
                selected["manual_bridge"],
                snapshot["manual_bridge"],
            )
            self.assertEqual(
                selected["guided_intake"],
                snapshot["guided_intake"],
            )

    def test_stage5_run_and_panel_share_fresh_revoked_projection(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            controller.select_repository(repository)
            implemented = intelligence_transplant_projection(
                execution_status="ACTIVE",
                delta_state="IMPLEMENTED",
                current_gate="GO",
                missing_evidence=[],
            )
            revoked = intelligence_transplant_projection(
                execution_status="ACTIVE",
                delta_state="REVOKED",
                current_gate="HOLD",
                missing_evidence=["FORWARD_ONLY_REPLACEMENT"],
            )
            intelligence_transplant = Mock()
            intelligence_transplant.attach_object.return_value = implemented
            intelligence_transplant.snapshot.return_value = revoked
            controller._intelligence_transplant = intelligence_transplant
            payload = (
                b'{"object_id":"E1-EXTERNAL-REVOKE",'
                b'"object_type":"E1_DISCOVERY"}'
            )

            snapshot = controller.intelligence_transplant_attach_evidence(
                payload=payload,
                mode="BYTE_EXACT_FILE_IMPORT",
                source_path_or_label="e1.json",
                declared_sha256=hashlib.sha256(payload).hexdigest(),
                context_evidence_ref=None,
                as_of="2026-07-30T00:00:00Z",
            )

            self.assertEqual(revoked, snapshot["intelligence_transplant"])
            self.assertEqual(
                snapshot["intelligence_transplant"]["execution_status"],
                snapshot["run"]["execution_status"],
            )
            self.assertEqual(
                snapshot["intelligence_transplant"]["delta_state"],
                snapshot["run"]["delta_state"],
            )
            self.assertEqual(
                snapshot["intelligence_transplant"]["current_gate"],
                snapshot["run"]["current_gate"],
            )
            self.assertEqual("ACTIVE", snapshot["run"]["execution_status"])
            self.assertEqual("REVOKED", snapshot["run"]["delta_state"])
            self.assertEqual("HOLD", snapshot["run"]["current_gate"])

    def test_stage5_corruption_replaces_cached_run_projection(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            controller.select_repository(repository)
            implemented = intelligence_transplant_projection(
                execution_status="ACTIVE",
                delta_state="IMPLEMENTED",
                current_gate="GO",
                missing_evidence=[],
            )
            intelligence_transplant = Mock()
            intelligence_transplant.attach_object.return_value = implemented
            intelligence_transplant.snapshot.side_effect = (
                IntelligenceTransplantIntegrityError(
                    "sensitive Stage 5 path"
                )
            )
            controller._intelligence_transplant = intelligence_transplant
            payload = (
                b'{"object_id":"E1-CORRUPT-AFTER-CACHE",'
                b'"object_type":"E1_DISCOVERY"}'
            )

            snapshot = controller.intelligence_transplant_attach_evidence(
                payload=payload,
                mode="BYTE_EXACT_FILE_IMPORT",
                source_path_or_label="e1.json",
                declared_sha256=hashlib.sha256(payload).hexdigest(),
                context_evidence_ref=None,
                as_of="2026-07-30T00:00:00Z",
            )

            panel = snapshot["intelligence_transplant"]
            self.assertEqual("BLOCKED_CORRUPT", panel["store_state"])
            self.assertEqual(
                panel["execution_status"],
                snapshot["run"]["execution_status"],
            )
            self.assertEqual(
                panel["delta_state"],
                snapshot["run"]["delta_state"],
            )
            self.assertEqual(
                panel["current_gate"],
                snapshot["run"]["current_gate"],
            )
            self.assertEqual(
                "NOT_ESTABLISHED",
                snapshot["run"]["execution_status"],
            )
            self.assertEqual("NONE", snapshot["run"]["delta_state"])
            self.assertEqual("BLOCK", snapshot["run"]["current_gate"])
            self.assertNotIn("sensitive", json.dumps(snapshot))

    def test_guided_intake_purge_wrapper_is_exact_and_never_starts_runner(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = ScriptedFactory("read_only")
            controller = self.make_controller(root, factory)
            selected = controller.select_repository(repository)
            run_before = selected["run"]
            receipt_before = selected["receipt"]
            defaults_before = selected["defaults"]
            bridge_before = selected["manual_bridge"]
            guided_intake = Mock()
            guided_intake.snapshot.return_value = {
                "state": "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            }
            controller._guided_intake = guided_intake
            request_id = "GI-REQ-EXACT"
            request_sha256 = "a" * 64

            snapshot = controller.guided_intake_purge(
                request_id,
                request_sha256,
                True,
            )

            guided_intake.purge.assert_called_once_with(
                request_id,
                request_sha256,
                True,
            )
            self.assertEqual(
                {"state": "BLOCK — ORIGINAL REQUEST UNAVAILABLE"},
                snapshot["guided_intake"],
            )
            self.assertEqual(run_before, snapshot["run"])
            self.assertEqual(receipt_before, snapshot["receipt"])
            self.assertEqual(defaults_before, snapshot["defaults"])
            self.assertEqual(bridge_before, snapshot["manual_bridge"])
            self.assertEqual(1, len(factory.modes))

    def test_guided_intake_corruption_and_busy_state_are_panel_local(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            selected = controller.select_repository(repository)
            guided_intake = Mock()
            controller._guided_intake = guided_intake

            guided_intake.snapshot.side_effect = GuidedIntakeIntegrityError(
                "sensitive corrupt path"
            )
            corrupted = controller.snapshot()
            self.assertEqual(
                "BLOCKED_CORRUPT",
                corrupted["guided_intake"]["state"],
            )
            self.assertEqual(
                (
                    "Guided Intake state is corrupted. "
                    "Guided Intake reads and writes are blocked."
                ),
                corrupted["guided_intake"]["error"],
            )
            self.assertNotIn("sensitive", json.dumps(corrupted))
            self.assertEqual(selected["run"], corrupted["run"])
            self.assertEqual(selected["receipt"], corrupted["receipt"])

            guided_intake.snapshot.side_effect = GuidedIntakeBusyError(
                "sensitive lock detail"
            )
            busy = controller.snapshot()
            self.assertEqual("BUSY", busy["guided_intake"]["state"])
            self.assertEqual(
                "Guided Intake is temporarily busy.",
                busy["guided_intake"]["error"],
            )
            self.assertNotIn("sensitive", json.dumps(busy))
            self.assertEqual(selected["manual_bridge"], busy["manual_bridge"])

    def test_guided_intake_transfer_blocks_repository_switch_and_binds_bridge(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository_a = create_repository(root, "repo-a")
            repository_b = create_repository(root, "repo-b")
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            controller.select_repository(repository_a)
            bridge_a = controller._bridge
            self.assertIsNotNone(bridge_a)
            entered = threading.Event()
            release = threading.Event()
            guided_intake = Mock()
            guided_intake.snapshot.return_value = {"state": "TRANSFERRED"}

            def bounded_transfer(_bridge: Any) -> None:
                entered.set()
                release.wait(timeout=5)

            guided_intake.transfer_to_bridge.side_effect = bounded_transfer
            controller._guided_intake = guided_intake
            results: list[dict[str, Any]] = []
            failures: list[BaseException] = []

            def transfer() -> None:
                try:
                    results.append(
                        controller.guided_intake_transfer_to_bridge()
                    )
                except BaseException as exc:
                    failures.append(exc)

            worker = threading.Thread(target=transfer)
            try:
                worker.start()
                self.assertTrue(entered.wait(timeout=5))
                with self.assertRaisesRegex(
                    RepositorySelectionError,
                    "(Manual Bridge|Guided Intake) action",
                ):
                    controller.select_repository(repository_b)
            finally:
                release.set()
                worker.join(timeout=5)

            self.assertFalse(worker.is_alive())
            self.assertEqual([], failures)
            self.assertEqual(1, len(results))
            guided_intake.transfer_to_bridge.assert_called_once_with(bridge_a)
            self.assertEqual(
                repository_a.resolve(),
                Path(results[0]["repository"]["path"]),
            )
            self.assertEqual(
                repository_a.resolve(),
                Path(controller.snapshot()["repository"]["path"]),
            )

    def test_manual_bridge_corruption_is_panel_local(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            selected = controller.select_repository(repository)
            receipt_before = selected["receipt"]
            bridge = controller._bridge
            self.assertIsNotNone(bridge)
            original_snapshot = bridge.snapshot

            def corrupted_bridge_snapshot() -> dict[str, Any]:
                raise ManualBridgeIntegrityError("sensitive bridge chain detail")

            bridge.snapshot = corrupted_bridge_snapshot  # type: ignore[method-assign]
            try:
                snapshot = controller.snapshot()
                self.assertEqual(
                    "BLOCKED_CORRUPT",
                    snapshot["manual_bridge"]["state"],
                )
                self.assertNotIn("sensitive", json.dumps(snapshot))
                self.assertEqual(receipt_before, snapshot["receipt"])
                self.assertEqual("idle", snapshot["run"]["state"])

                controller.start_run("Read target.txt without changing it.")
                completed = wait_for(
                    controller,
                    lambda state: state["run"]["state"] == "completed",
                )
                self.assertEqual("Read-only result.", completed["run"]["result"])
                self.assertEqual(receipt_before, completed["receipt"])
                self.assertEqual(
                    "BLOCKED_CORRUPT",
                    completed["manual_bridge"]["state"],
                )
            finally:
                bridge.snapshot = original_snapshot  # type: ignore[method-assign]

    def test_manual_bridge_lock_contention_is_bounded_and_panel_local(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            controller.select_repository(repository)
            controller.start_bridge_session(bridge_boundary())
            bridge = controller._bridge
            self.assertIsNotNone(bridge)
            lock_path = bridge.store.root / ".transaction.lock"

            holder = subprocess.Popen(
                (
                    sys.executable,
                    "-c",
                    (
                        "import fcntl,sys;"
                        "stream=open(sys.argv[1],'r+b',buffering=0);"
                        "fcntl.flock(stream.fileno(),fcntl.LOCK_EX);"
                        "print('LOCKED',flush=True);"
                        "sys.stdin.read(1)"
                    ),
                    str(lock_path),
                ),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual("LOCKED", holder.stdout.readline().strip())
            failures: list[BaseException] = []

            def blocked_bridge_action() -> None:
                try:
                    controller.bridge_copy_for_pro()
                except BaseException as exc:  # captured for deterministic join
                    failures.append(exc)

            worker = threading.Thread(target=blocked_bridge_action)
            try:
                worker.start()
                time.sleep(0.03)
                started = time.monotonic()
                snapshot = controller.snapshot()
                elapsed = time.monotonic() - started

                self.assertLess(elapsed, 0.2)
                self.assertEqual("idle", snapshot["run"]["state"])
                self.assertEqual(
                    "Manual Bridge is temporarily busy.",
                    snapshot["manual_bridge"]["error"],
                )
            finally:
                if holder.poll() is None:
                    holder.stdin.write("\n")
                    holder.stdin.flush()
                holder.wait(timeout=5)
                worker.join(timeout=5)
                holder.stdin.close()
                holder.stdout.close()
                holder.stderr.close()
            self.assertFalse(worker.is_alive())
            self.assertLessEqual(len(failures), 1)

    def test_repository_switch_is_rejected_during_bridge_operation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository_a = create_repository(root, "repo-a")
            repository_b = create_repository(root, "repo-b")
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            controller.select_repository(repository_a)
            controller.start_bridge_session(bridge_boundary())
            bridge_a = controller._bridge
            self.assertIsNotNone(bridge_a)
            events_before = bridge_a.store.events_path.read_bytes()
            entered = threading.Event()
            release = threading.Event()
            original_copy = bridge_a.copy_for_pro

            def bounded_pause() -> dict[str, Any]:
                entered.set()
                release.wait(timeout=5)
                return bridge_a.snapshot()

            bridge_a.copy_for_pro = bounded_pause  # type: ignore[method-assign]
            failures: list[BaseException] = []

            def run_bridge_action() -> None:
                try:
                    controller.bridge_copy_for_pro()
                except BaseException as exc:
                    failures.append(exc)

            worker = threading.Thread(target=run_bridge_action)
            try:
                worker.start()
                self.assertTrue(entered.wait(timeout=5))
                with self.assertRaisesRegex(
                    RepositorySelectionError,
                    "Bridge action",
                ):
                    controller.select_repository(repository_b)
            finally:
                release.set()
                worker.join(timeout=5)
                bridge_a.copy_for_pro = original_copy  # type: ignore[method-assign]

            self.assertFalse(worker.is_alive())
            self.assertEqual([], failures)
            self.assertEqual(
                repository_a.resolve(),
                Path(controller.snapshot()["repository"]["path"]),
            )
            self.assertEqual(events_before, bridge_a.store.events_path.read_bytes())
            self.assertFalse(
                repository_b
                .joinpath(".git", "decision-os", "manual-bridge", "v0.1")
                .exists()
            )

    def test_repository_switch_waits_for_bridge_response_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository_a = create_repository(root, "repo-a")
            repository_b = create_repository(root, "repo-b")
            controller = self.make_controller(
                root,
                ScriptedFactory("read_only"),
            )
            controller.select_repository(repository_a)
            controller.start_bridge_session(bridge_boundary())
            entered = threading.Event()
            release = threading.Event()
            original_snapshot = controller._snapshot_after_bridge

            def bounded_snapshot(bridge: Any) -> dict[str, Any]:
                entered.set()
                release.wait(timeout=5)
                return original_snapshot(bridge)

            controller._snapshot_after_bridge = bounded_snapshot  # type: ignore[method-assign]
            results: list[dict[str, Any]] = []
            failures: list[BaseException] = []

            def run_bridge_action() -> None:
                try:
                    results.append(controller.bridge_copy_for_pro())
                except BaseException as exc:
                    failures.append(exc)

            worker = threading.Thread(target=run_bridge_action)
            try:
                worker.start()
                self.assertTrue(entered.wait(timeout=5))
                with self.assertRaisesRegex(
                    RepositorySelectionError,
                    "Bridge action",
                ):
                    controller.select_repository(repository_b)
            finally:
                release.set()
                worker.join(timeout=5)
                controller._snapshot_after_bridge = original_snapshot  # type: ignore[method-assign]

            self.assertFalse(worker.is_alive())
            self.assertEqual([], failures)
            self.assertEqual(1, len(results))
            self.assertEqual(
                repository_a.resolve(),
                Path(results[0]["repository"]["path"]),
            )
            self.assertEqual(
                repository_a.resolve(),
                Path(controller.snapshot()["repository"]["path"]),
            )

    def test_malformed_lifecycle_and_app_server_failure_are_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root / "malformed",
                ScriptedFactory("malformed"),
            )
            controller.select_repository(repository)
            controller.start_run("Malformed lifecycle.")
            malformed = wait_for(
                controller,
                lambda state: state["run"]["state"] == "needs_attention",
            )
            self.assertEqual(
                "The companion received an invalid progress event.",
                malformed["run"]["error"],
            )
            self.assertNotIn("<script>", json.dumps(malformed))

            controller = self.make_controller(
                root / "failure",
                ScriptedFactory("failure"),
            )
            controller.select_repository(repository)
            controller.start_run("Adapter failure.")
            failed = wait_for(
                controller,
                lambda state: state["run"]["state"] == "needs_attention",
            )
            self.assertEqual(
                "The bounded Codex Run failed closed.",
                failed["run"]["error"],
            )
            self.assertNotIn("sensitive", json.dumps(failed))

    def test_corrupted_event_chain_blocks_repository_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            engine = AccelerationEngine(repository)
            outcome = engine.evaluate(
                run_id=engine.new_run_id(),
                iteration=1,
                decision_type=DecisionType.MODIFY_FILE,
                requested_scope="target.txt",
                source_interrupt_id="corruption-setup",
                choice_provider=lambda _identity: "2",
            )
            self.assertTrue(outcome.allowed)
            events_path = engine.store.events_path
            events_path.write_text("{}\n", encoding="utf-8")
            controller = self.make_controller(root, ScriptedFactory())

            with self.assertRaises(RepositorySelectionError):
                controller.select_repository(repository)
