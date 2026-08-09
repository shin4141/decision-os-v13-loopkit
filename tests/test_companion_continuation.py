from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from typing import Any

from decision_os.acceleration.model import hash_payload
from decision_os.acceleration.store import StateIntegrityError
from decision_os.companion.continuation import (
    ContinuationIntegrityError,
    StageBContinuationRequest,
)
from decision_os.companion.controller import (
    CompanionController,
    RunConflictError,
)
from decision_os.companion.supervisor import ContractFact
from tests.test_companion_controller import (
    ScriptedAdapter,
    create_repository,
    wait_for,
)


YES = ContractFact.SATISFIED
NO = ContractFact.NOT_SATISFIED
UNKNOWN = ContractFact.UNKNOWN
REPO_ROOT = Path(__file__).resolve().parents[1]


def stage_b_request(**overrides: Any) -> StageBContinuationRequest:
    values: dict[str, Any] = {
        "goal": (
            "Establish the exact target identity, then independently verify it "
            "without changing repository content."
        ),
        "run_1_task": (
            "Read target.txt and report its exact evidence without modifying it."
        ),
        "remaining_gap_after_run_1": (
            "Independently verify target.txt against the persisted Run 1 evidence."
        ),
        "next_bounded_action": (
            "Re-read target.txt and verify it matches the persisted Run 1 identity."
        ),
        "evidence_recovery_action": (
            "Recover the exact persisted Stage B causal record."
        ),
        "irreducible_human_decision": None,
        "authority_evidence_refs": (
            "docs/companion_product_roadmap_v0_3.md#stage-b",
        ),
        "allowed_mutation_paths": ("target.txt",),
        "protected_objects": ("all repository content remains read-only",),
        "completed_runs_before": 0,
        "max_runs": 3,
        "goal_complete_after_run_1": NO,
        "goal_unchanged": YES,
        "authority_sufficient": YES,
        "blast_radius_bounded": YES,
        "action_reversible_or_authorized": YES,
        "no_material_human_preference_required": YES,
        "no_external_or_irreversible_commitment": YES,
        "cost_boundary_intact": YES,
        "protected_object_and_ownership_unchanged": YES,
        "no_authoritative_conflict": YES,
        "no_truly_unanswered_human_question": YES,
    }
    values.update(overrides)
    return StageBContinuationRequest(**values)


class RecordingFactory:
    def __init__(self, *modes: str) -> None:
        self.modes = deque(modes)
        self.prompts: list[str] = []

    def __call__(
        self,
        engine: Any,
        approval_provider: Any,
        lifecycle_sink: Any,
    ) -> ScriptedAdapter:
        mode = self.modes.popleft()
        prompts = self.prompts

        class RecordingAdapter(ScriptedAdapter):
            async def run(self, prompt: str) -> Any:
                prompts.append(prompt)
                return await super().run(prompt)

        return RecordingAdapter(
            engine,
            approval_provider,
            lifecycle_sink,
            mode,
        )


class StageBContinuationTest(unittest.TestCase):
    def make_controller(
        self,
        directory: Path,
        factory: RecordingFactory,
    ) -> CompanionController:
        return CompanionController(
            state_path=directory / "application-state" / "state.json",
            picker_runner=lambda _script: None,
            adapter_factory=factory,
        )

    def test_one_goal_creates_one_causal_automatic_run_and_never_run_three(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = RecordingFactory("read_only", "read_only", "read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)

            started = controller.start_one_automatic_continuation(
                stage_b_request()
            )
            self.assertEqual("running", started["run"]["state"])
            self.assertEqual(1, started["run"]["continuation"]["run_number"])

            completed = wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "COMPLETE"
                ),
            )
            chain = completed["compound_loop"]
            self.assertEqual(2, len(chain["runs"]))
            self.assertEqual(1, chain["automatic_continuations_started"])
            self.assertEqual(1, chain["automatic_continuation_limit"])
            self.assertEqual(2, len(factory.prompts))
            self.assertEqual(1, len(factory.modes))
            self.assertEqual(
                stage_b_request().run_1_task,
                factory.prompts[0],
            )

            run_1 = chain["runs"][0]
            task_2 = chain["automatic_task"]
            self.assertEqual(run_1["run_id"], task_2["source_run_id"])
            self.assertEqual(
                run_1["evidence_sha256"],
                task_2["source_evidence_sha256"],
            )
            self.assertEqual(task_2["task"], factory.prompts[1])
            self.assertIn(run_1["run_id"], factory.prompts[1])
            self.assertIn(run_1["evidence_sha256"], factory.prompts[1])
            self.assertIn(stage_b_request().goal, factory.prompts[1])
            self.assertIn(
                stage_b_request().next_bounded_action,
                factory.prompts[1],
            )
            self.assertTrue(
                completed["run"]["continuation"]["automatic"]
            )
            self.assertEqual(2, completed["run"]["continuation"]["run_number"])

            time.sleep(0.05)
            self.assertEqual(2, len(factory.prompts))
            self.assertEqual(1, len(factory.modes))

    def test_non_go_routes_never_start_run_two(self) -> None:
        cases = (
            (
                "goal-complete",
                {"goal_complete_after_run_1": YES},
                "HOLD",
                "STOP",
            ),
            (
                "authority-block",
                {"authority_sufficient": NO},
                "BLOCK",
                "HUMAN-SEAT",
            ),
            (
                "unknown-authority",
                {"authority_sufficient": UNKNOWN},
                "BLOCK",
                "EVIDENCE-RECOVERY",
            ),
            (
                "cap",
                {"completed_runs_before": 2},
                "CAP",
                "HUMAN-SEAT",
            ),
            (
                "protected-object",
                {"protected_object_and_ownership_unchanged": NO},
                "BLOCK",
                "HUMAN-SEAT",
            ),
        )
        for label, overrides, gate, route in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                repository = create_repository(root)
                factory = RecordingFactory("read_only", "read_only")
                controller = self.make_controller(root, factory)
                controller.select_repository(repository)

                controller.start_one_automatic_continuation(
                    stage_b_request(**overrides)
                )
                stopped = wait_for(
                    controller,
                    lambda state: (
                        state["compound_loop"] is not None
                        and state["compound_loop"].get("state") == "STOPPED"
                    ),
                )

                chain = stopped["compound_loop"]
                self.assertEqual(1, len(chain["runs"]))
                self.assertEqual(0, chain["automatic_continuations_started"])
                self.assertIsNone(chain["automatic_task"])
                self.assertEqual(gate, chain["supervisor"]["gate"])
                self.assertEqual(route, chain["supervisor"]["decision_route"])
                self.assertEqual(1, len(factory.prompts))
                self.assertEqual(1, len(factory.modes))

    def test_out_of_scope_mutation_is_denied_before_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = RecordingFactory("mutation", "read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)

            controller.start_one_automatic_continuation(
                stage_b_request(allowed_mutation_paths=("other.txt",))
            )
            stopped = wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "STOPPED"
                ),
            )

            chain = stopped["compound_loop"]
            self.assertEqual("DENIED", chain["runs"][0]["status"])
            self.assertEqual("BLOCK", chain["supervisor"]["gate"])
            self.assertEqual("STOP", chain["supervisor"]["decision_route"])
            self.assertEqual(0, chain["automatic_continuations_started"])
            self.assertEqual(1, len(factory.prompts))

    def test_insufficient_run_1_evidence_never_starts_run_two(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = RecordingFactory("typed_result_failure", "read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)

            controller.start_one_automatic_continuation(stage_b_request())
            stopped = wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "STOPPED"
                ),
            )

            chain = stopped["compound_loop"]
            self.assertEqual("HOLD", chain["supervisor"]["gate"])
            self.assertEqual(
                "EVIDENCE-RECOVERY",
                chain["supervisor"]["decision_route"],
            )
            self.assertEqual(0, chain["automatic_continuations_started"])
            self.assertEqual(1, len(factory.prompts))
            self.assertEqual(1, len(factory.modes))

    def test_automatic_run_2_cannot_expand_mutation_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = RecordingFactory("read_only", "mutation", "read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)

            controller.start_one_automatic_continuation(
                stage_b_request(allowed_mutation_paths=("other.txt",))
            )
            completed = wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "COMPLETE"
                ),
            )

            chain = completed["compound_loop"]
            self.assertEqual(2, len(chain["runs"]))
            self.assertEqual("DENIED", chain["runs"][1]["status"])
            self.assertEqual(1, chain["automatic_continuations_started"])
            self.assertEqual("HOLD", chain["governed_stop"]["gate"])
            self.assertEqual("STOP", chain["governed_stop"]["route"])
            self.assertEqual(2, len(factory.prompts))
            self.assertEqual(1, len(factory.modes))

    def test_run_1_persistence_failure_blocks_before_run_two(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = RecordingFactory("read_only", "read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            original_save = controller._continuation_store.save
            calls = 0

            def fail_second_save(payload: Any) -> dict[str, Any]:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise ContinuationIntegrityError(
                        "injected persisted Run 1 failure"
                    )
                return original_save(payload)

            controller._continuation_store.save = fail_second_save  # type: ignore[method-assign]
            controller.start_one_automatic_continuation(stage_b_request())
            blocked = wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "BLOCKED"
                ),
            )

            self.assertEqual(
                "EVIDENCE-RECOVERY",
                blocked["compound_loop"]["governed_stop"]["route"],
            )
            self.assertEqual(0, blocked["compound_loop"]["automatic_continuations_started"])
            self.assertEqual(1, len(factory.prompts))
            self.assertEqual(1, len(factory.modes))

    def test_run_1_receipt_failure_governs_stop_before_run_two(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = RecordingFactory("read_only", "read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            original_receipt = controller._safe_receipt
            calls = 0

            def fail_post_run_receipt(target: Path) -> dict[str, Any]:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise StateIntegrityError("injected Receipt failure")
                return original_receipt(target)

            controller._safe_receipt = fail_post_run_receipt  # type: ignore[method-assign]
            controller.start_one_automatic_continuation(stage_b_request())
            stopped = wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "STOPPED"
                ),
            )

            self.assertEqual(
                "EVIDENCE-RECOVERY",
                stopped["compound_loop"]["governed_stop"]["route"],
            )
            self.assertEqual([], stopped["compound_loop"]["runs"])
            self.assertEqual(
                0,
                stopped["compound_loop"]["automatic_continuations_started"],
            )
            self.assertEqual(1, len(factory.prompts))
            self.assertEqual(1, len(factory.modes))

    def test_run_2_execution_failure_is_restartable_and_never_recurses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = RecordingFactory("read_only", "failure", "read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)

            controller.start_one_automatic_continuation(stage_b_request())
            stopped = wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "STOPPED"
                    and state["compound_loop"].get("governed_stop") is not None
                ),
            )

            chain = stopped["compound_loop"]
            self.assertEqual(1, chain["automatic_continuations_started"])
            self.assertEqual("EVIDENCE-RECOVERY", chain["governed_stop"]["route"])
            self.assertEqual(2, len(factory.prompts))
            self.assertEqual(1, len(factory.modes))
            self.assertEqual("needs_attention", stopped["run"]["state"])

            reconnected = self.make_controller(root, RecordingFactory())
            snapshot = reconnected.snapshot()
            self.assertEqual("STOPPED", snapshot["compound_loop"]["state"])
            self.assertEqual(
                chain["record_sha256"],
                snapshot["compound_loop"]["record_sha256"],
            )

    def test_completed_chain_reconnects_without_dispatching_another_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = RecordingFactory("read_only", "read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            controller.start_one_automatic_continuation(stage_b_request())
            completed = wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "COMPLETE"
                ),
            )

            restarted_factory = RecordingFactory()
            restarted = self.make_controller(root, restarted_factory)
            snapshot = restarted.snapshot()
            self.assertEqual("COMPLETE", snapshot["compound_loop"]["state"])
            self.assertEqual(2, len(snapshot["compound_loop"]["runs"]))
            self.assertEqual(
                completed["compound_loop"]["record_sha256"],
                snapshot["compound_loop"]["record_sha256"],
            )
            self.assertEqual([], restarted_factory.prompts)
            state_path = (
                root / "application-state" / "stage-b-continuation.json"
            )
            self.assertEqual(0o600, state_path.stat().st_mode & 0o777)

    def test_corrupt_restart_state_blocks_without_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = RecordingFactory("read_only", "read_only")
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            controller.start_one_automatic_continuation(stage_b_request())
            wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "COMPLETE"
                ),
            )
            state_path = (
                root / "application-state" / "stage-b-continuation.json"
            )
            record = json.loads(state_path.read_text(encoding="utf-8"))
            record["automatic_continuations_started"] = 0
            state_path.write_text(json.dumps(record), encoding="utf-8")

            restarted_factory = RecordingFactory()
            restarted = self.make_controller(root, restarted_factory)
            snapshot = restarted.snapshot()

            self.assertEqual(
                "BLOCKED_CORRUPT",
                snapshot["compound_loop"]["state"],
            )
            self.assertEqual("BLOCK", snapshot["compound_loop"]["gate"])
            self.assertEqual([], restarted_factory.prompts)

    def test_rehashed_independent_task_two_is_rejected_as_corrupt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                RecordingFactory("read_only", "read_only"),
            )
            controller.select_repository(repository)
            controller.start_one_automatic_continuation(stage_b_request())
            wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "COMPLETE"
                ),
            )
            state_path = (
                root / "application-state" / "stage-b-continuation.json"
            )
            record = json.loads(state_path.read_text(encoding="utf-8"))
            injected = "independently supplied second task"
            record["automatic_task"]["task"] = injected
            record["automatic_task"]["task_sha256"] = hashlib.sha256(
                injected.encode("utf-8")
            ).hexdigest()
            record.pop("record_sha256")
            record["record_sha256"] = hash_payload(record)
            state_path.write_text(json.dumps(record), encoding="utf-8")

            restarted_factory = RecordingFactory()
            restarted = self.make_controller(root, restarted_factory)
            snapshot = restarted.snapshot()

            self.assertEqual(
                "BLOCKED_CORRUPT",
                snapshot["compound_loop"]["state"],
            )
            self.assertEqual([], restarted_factory.prompts)

    def test_interrupted_run_one_record_blocks_a_new_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.make_controller(
                root,
                RecordingFactory("read_only", "read_only"),
            )
            controller.select_repository(repository)
            controller.start_one_automatic_continuation(stage_b_request())
            wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "COMPLETE"
                ),
            )
            state_path = (
                root / "application-state" / "stage-b-continuation.json"
            )
            record = json.loads(state_path.read_text(encoding="utf-8"))
            record["state"] = "RUN_1_COMPLETE"
            record["runs"] = record["runs"][:1]
            record["automatic_task"] = None
            record["automatic_continuations_started"] = 0
            record["governed_stop"] = None
            record.pop("record_sha256")
            record["record_sha256"] = hash_payload(record)
            state_path.write_text(json.dumps(record), encoding="utf-8")

            restarted_factory = RecordingFactory()
            restarted = self.make_controller(root, restarted_factory)
            self.assertEqual(
                "RUN_1_COMPLETE",
                restarted.snapshot()["compound_loop"]["state"],
            )
            with self.assertRaises(RunConflictError):
                restarted.start_one_automatic_continuation(stage_b_request())
            self.assertEqual([], restarted_factory.prompts)

    def test_real_stage_b_record_is_bound_to_exact_stage_a_evidence(self) -> None:
        stage_a = (
            REPO_ROOT / "validation" / "stage_a_supervisor_judgment_001.md"
        )
        self.assertEqual(
            "a9b65437ea94b624ede85b2dfdb2f4f93d5a81a3bb17a5829d8f6c13a35ba77f",
            hashlib.sha256(stage_a.read_bytes()).hexdigest(),
        )
        record = (
            REPO_ROOT
            / "validation"
            / "stage_b_one_automatic_continuation_001.md"
        ).read_text(encoding="utf-8")
        for exact in (
            "abce9db4-d24f-479d-b33b-2cb7fa4cc206",
            "ae9b117f-d170-463c-95ad-3ea40c98efa4",
            "8ce582c8fc082aa2ca2adcfc82d17f813128cbc1c8f6a6fb6f9e950b07ebfd01",
            "277d323fd75ba60ac8f5f03757ff5dac6c29939b36be56a2458271cb5038a302",
            "fada414d4f667eefbc7f6e73f62c8fcc641221c623e9c73773ca2df7458e5c6d",
            "Stage B Completion Line:\nPASS",
        ):
            self.assertIn(exact, record)


if __name__ == "__main__":
    unittest.main()
