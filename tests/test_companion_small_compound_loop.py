from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from typing import Any

from decision_os.acceleration.codex_adapter import (
    CodexFileAction,
    CodexReadEvidence,
    CodexRunResult,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import DecisionType, hash_payload
from decision_os.companion.controller import (
    CompanionController,
    RunConflictError,
)
from decision_os.companion.small_compound_loop import (
    StageCCompletionRequirement,
    StageCContinuationRequest,
    remaining_requirements,
    satisfied_requirement_ids,
    stage_c_outcome,
)
from decision_os.companion.supervisor import ContractFact
from tests.test_companion_controller import (
    ScriptedAdapter,
    create_repository,
    runtime_identity,
    wait_for,
)


YES = ContractFact.SATISFIED
NO = ContractFact.NOT_SATISFIED
REPO_ROOT = Path(__file__).resolve().parents[1]


def requirement(number: int) -> StageCCompletionRequirement:
    return StageCCompletionRequirement(
        requirement_id=f"REQ-{number}",
        description=f"Establish independent completion fact {number}.",
        evidence_path=f"evidence-{number}.md",
        expected_sha256=str(number) * 64,
    )


def stage_c_request(**overrides: Any) -> StageCContinuationRequest:
    values: dict[str, Any] = {
        "goal": (
            "Establish three distinct evidence facts through one causally "
            "supervised compound loop without changing repository content."
        ),
        "run_1_task": (
            "Read evidence-1.md and establish only completion fact REQ-1."
        ),
        "completion_requirements": (
            requirement(1),
            requirement(2),
            requirement(3),
        ),
        "evidence_recovery_action": (
            "Recover the exact persisted Stage C causal record."
        ),
        "irreducible_human_decision": None,
        "authority_evidence_refs": (
            "docs/companion_product_roadmap_v0_3.md#stage-c",
        ),
        "allowed_mutation_paths": ("target.txt",),
        "protected_objects": ("all repository content remains read-only",),
        "max_runs": 3,
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
    return StageCContinuationRequest(**values)


def temporal_support_record(*plans: dict[str, Any]) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for plan in plans:
        reads = [
            {
                "path": f"evidence-{number}.md",
                "bytes": number,
                "sha256": str(number) * 64,
                "repository_identity": "b" * 40,
                "status": "succeeded",
                "reason": None,
            }
            for number in plan.get("evidence", ())
        ]
        reads.extend(
            {
                "path": f"evidence-{number}.md",
                "bytes": number,
                "sha256": "f" * 64,
                "repository_identity": "b" * 40,
                "status": "succeeded",
                "reason": None,
            }
            for number in plan.get("nonmatching_evidence", ())
        )
        runs.append(
            {
                "read_evidence": reads,
                "file_actions": [
                    {
                        "action": "Modify",
                        "path": path,
                        "access": "one-time",
                        "status": "approved",
                    }
                    for path in plan.get("modifies", ())
                ],
            }
        )
    return {
        "request": stage_c_request(
            allowed_mutation_paths=("evidence-1.md",),
        ).as_dict(),
        "runs": runs,
    }


class EvidenceFactory:
    """Return one predetermined Worker result per actual dispatch."""

    def __init__(self, *plans: Any) -> None:
        self.plans = deque(plans)
        self.prompts: list[str] = []

    def __call__(
        self,
        engine: Any,
        approval_provider: Any,
        lifecycle_sink: Any,
    ) -> Any:
        plan = self.plans.popleft()
        prompts = self.prompts

        if plan == "mutation":
            class RecordingMutationAdapter(ScriptedAdapter):
                async def run(self, prompt: str) -> CodexRunResult:
                    prompts.append(prompt)
                    return await super().run(prompt)

            return RecordingMutationAdapter(
                engine,
                approval_provider,
                lifecycle_sink,
                "mutation",
            )

        class EvidenceAdapter:
            async def run(self, prompt: str) -> CodexRunResult:
                prompts.append(prompt)
                if plan == "failure":
                    raise RuntimeError("injected bounded execution failure")
                evidence_ids = tuple(plan.get("evidence", ()))
                nonmatching_evidence_ids = tuple(
                    plan.get("nonmatching_evidence", ())
                )
                modified_paths = tuple(plan.get("modifies", ()))
                status = plan.get("status", "NORMAL_TERMINAL")
                normal = status == "NORMAL_TERMINAL"
                return CodexRunResult(
                    run_id=engine.new_run_id(),
                    normal_terminal=normal,
                    status=status,
                    error_type=None,
                    turn_status="completed",
                    runtime_identity=runtime_identity(),
                    checkpoint_outcomes=(),
                    final_message=f"Established {evidence_ids!r}.",
                    file_actions=tuple(
                        CodexFileAction(
                            action="Modify",
                            normalized_scope=path,
                            access="one-time",
                            status="approved",
                        )
                        for path in modified_paths
                    ),
                    read_evidence=(
                        tuple(
                            CodexReadEvidence(
                                path=f"evidence-{number}.md",
                                byte_count=number,
                                sha256=str(number) * 64,
                                repository_identity="b" * 40,
                                status="succeeded",
                            )
                            for number in evidence_ids
                        )
                        + tuple(
                            CodexReadEvidence(
                                path=f"evidence-{number}.md",
                                byte_count=number,
                                sha256="f" * 64,
                                repository_identity="b" * 40,
                                status="succeeded",
                            )
                            for number in nonmatching_evidence_ids
                        )
                    ),
                )

        return EvidenceAdapter()


class StageCSmallCompoundLoopTest(unittest.TestCase):
    def make_controller(
        self,
        directory: Path,
        factory: EvidenceFactory,
    ) -> CompanionController:
        return CompanionController(
            state_path=directory / "application-state" / "state.json",
            picker_runner=lambda _script: None,
            adapter_factory=factory,
        )

    @staticmethod
    def terminal(controller: CompanionController) -> dict[str, Any]:
        return wait_for(
            controller,
            lambda state: (
                state["compound_loop"] is not None
                and state["compound_loop"].get("state") == "TERMINAL"
            ),
        )

    def run_complete_chain(
        self,
        root: Path,
    ) -> tuple[CompanionController, EvidenceFactory, dict[str, Any]]:
        repository = create_repository(root)
        factory = EvidenceFactory(
            {"evidence": (1,)},
            {"evidence": (2,)},
            {"evidence": (3,)},
            {"evidence": ()},
        )
        controller = self.make_controller(root, factory)
        controller.select_repository(repository)
        controller.start_small_compound_loop(stage_c_request())
        return controller, factory, self.terminal(controller)

    def test_three_distinct_runs_are_causal_and_run_four_is_impossible(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            controller, factory, completed = self.run_complete_chain(
                Path(temporary)
            )
            chain = completed["compound_loop"]

            self.assertEqual("COMPLETE", chain["outcome"])
            self.assertEqual(3, len(chain["runs"]))
            self.assertEqual(3, len(chain["residues"]))
            self.assertEqual(3, len(chain["supervisor_judgments"]))
            self.assertEqual(2, len(chain["automatic_tasks"]))
            self.assertEqual(2, chain["automatic_continuations_started"])
            self.assertEqual(2, chain["automatic_continuation_limit"])
            self.assertEqual(3, chain["total_run_cap"])
            self.assertEqual(3, len(factory.prompts))
            self.assertEqual(1, len(factory.plans))

            self.assertEqual(
                ["REQ-1"],
                chain["residues"][0]["established_requirement_ids"],
            )
            self.assertEqual(
                ["REQ-1", "REQ-2"],
                chain["residues"][1]["established_requirement_ids"],
            )
            self.assertEqual(
                ["REQ-1", "REQ-2", "REQ-3"],
                chain["residues"][2]["established_requirement_ids"],
            )
            task_2, task_3 = chain["automatic_tasks"]
            self.assertEqual("REQ-2", task_2["selected_requirement_id"])
            self.assertEqual("REQ-3", task_3["selected_requirement_id"])
            self.assertNotEqual(task_2["task"], task_3["task"])
            self.assertEqual(
                chain["runs"][0]["run_id"],
                task_2["source_run_id"],
            )
            self.assertEqual(
                chain["runs"][1]["run_id"],
                task_3["source_run_id"],
            )
            self.assertEqual(
                chain["runs"][1]["evidence_sha256"],
                task_3["source_evidence_sha256"],
            )
            self.assertNotEqual(
                chain["runs"][0]["run_id"],
                task_3["source_run_id"],
            )
            for index, judgment in enumerate(
                chain["supervisor_judgments"],
                start=1,
            ):
                self.assertEqual(
                    chain["runs"][index - 1]["run_id"],
                    judgment["consumed_run"]["run_id"],
                )

            time.sleep(0.05)
            self.assertEqual(3, len(factory.prompts))
            self.assertEqual(1, len(factory.plans))
            self.assertEqual(
                "TERMINAL",
                controller.snapshot()["compound_loop"]["state"],
            )

    def test_same_run_approved_modify_invalidates_current_read_support(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = EvidenceFactory(
                {
                    "evidence": (1, 2, 3),
                    "modifies": ("evidence-1.md",),
                },
                {"evidence": (1,)},
            )
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            controller.start_small_compound_loop(
                stage_c_request(
                    allowed_mutation_paths=("evidence-1.md",),
                )
            )
            chain = self.terminal(controller)["compound_loop"]

            self.assertEqual("HOLD", chain["outcome"])
            self.assertEqual(1, len(chain["runs"]))
            self.assertEqual(
                ["REQ-2", "REQ-3"],
                chain["residues"][0]["established_requirement_ids"],
            )
            self.assertEqual(
                ["REQ-1"],
                chain["residues"][0]["remaining_requirement_ids"],
            )
            self.assertEqual(
                "EVIDENCE-RECOVERY",
                chain["supervisor_judgments"][0]["decision_route"],
            )
            self.assertEqual("HOLD", chain["governed_stop"]["gate"])
            self.assertEqual(
                "EVIDENCE-RECOVERY",
                chain["governed_stop"]["route"],
            )
            self.assertEqual([], chain["automatic_tasks"])
            self.assertEqual(0, chain["automatic_continuations_started"])
            self.assertEqual(1, len(factory.prompts))
            self.assertEqual(1, len(factory.plans))

            matching_read = chain["runs"][0]["read_evidence"][0]
            self.assertEqual(
                {
                    "path": "evidence-1.md",
                    "bytes": 1,
                    "sha256": "1" * 64,
                    "repository_identity": "b" * 40,
                    "status": "succeeded",
                    "reason": None,
                },
                matching_read,
            )
            self.assertEqual(
                {
                    "action": "Modify",
                    "path": "evidence-1.md",
                    "access": "one-time",
                    "status": "approved",
                },
                chain["runs"][0]["file_actions"][0],
            )

            restarted_factory = EvidenceFactory()
            restarted = self.make_controller(root, restarted_factory)
            replayed = restarted.snapshot()["compound_loop"]
            self.assertEqual("HOLD", replayed["outcome"])
            self.assertEqual(
                chain["record_sha256"],
                replayed["record_sha256"],
            )
            self.assertEqual(
                chain["runs"][0]["read_evidence"],
                replayed["runs"][0]["read_evidence"],
            )
            self.assertEqual(
                ["REQ-1"],
                replayed["residues"][0]["remaining_requirement_ids"],
            )
            self.assertEqual([], restarted_factory.prompts)

    def test_same_run_collision_is_conservative_and_modify_specific(
        self,
    ) -> None:
        collision = temporal_support_record(
            {
                "evidence": (1, 1, 2, 3),
                "modifies": ("evidence-1.md",),
            }
        )
        self.assertEqual(
            ("REQ-2", "REQ-3"),
            satisfied_requirement_ids(collision),
        )
        self.assertEqual(
            ("REQ-1",),
            tuple(
                item["requirement_id"]
                for item in remaining_requirements(collision)
            ),
        )
        self.assertEqual(
            2,
            sum(
                read["path"] == "evidence-1.md"
                for read in collision["runs"][0]["read_evidence"]
            ),
        )

        read_only = temporal_support_record({"evidence": (1, 2, 3)})
        self.assertEqual(
            ("REQ-1", "REQ-2", "REQ-3"),
            satisfied_requirement_ids(read_only),
        )

        denied = temporal_support_record(
            {
                "evidence": (1, 2, 3),
                "modifies": ("evidence-1.md",),
            }
        )
        denied_action = denied["runs"][0]["file_actions"][0]
        denied_action["access"] = "denied"
        denied_action["status"] = "denied"
        self.assertEqual(
            ("REQ-1", "REQ-2", "REQ-3"),
            satisfied_requirement_ids(denied),
        )

        created = temporal_support_record(
            {
                "evidence": (1, 2, 3),
                "modifies": ("evidence-1.md",),
            }
        )
        created["runs"][0]["file_actions"][0]["action"] = "Create"
        self.assertEqual(
            ("REQ-1", "REQ-2", "REQ-3"),
            satisfied_requirement_ids(created),
        )

        different_path = temporal_support_record(
            {
                "evidence": (1, 2, 3),
                "modifies": ("evidence-1.md",),
            }
        )
        different_path["request"] = stage_c_request(
            allowed_mutation_paths=("other.txt",),
        ).as_dict()
        different_path["runs"][0]["file_actions"][0]["path"] = "other.txt"
        self.assertEqual(
            ("REQ-1", "REQ-2", "REQ-3"),
            satisfied_requirement_ids(different_path),
        )

    def test_later_authorized_modify_invalidates_historical_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = EvidenceFactory(
                {"evidence": (1,)},
                {"evidence": (2,), "modifies": ("evidence-1.md",)},
                {"evidence": (3,)},
                {"evidence": (1,)},
            )
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            controller.start_small_compound_loop(
                stage_c_request(
                    allowed_mutation_paths=("evidence-1.md",),
                )
            )
            chain = self.terminal(controller)["compound_loop"]

            self.assertEqual("HOLD", chain["outcome"])
            self.assertNotEqual("COMPLETE", chain["outcome"])
            self.assertEqual(
                "EVIDENCE-RECOVERY",
                chain["supervisor_judgments"][-1]["decision_route"],
            )
            self.assertEqual(
                ["REQ-1", "REQ-3"],
                chain["residues"][-1]["remaining_requirement_ids"],
            )
            self.assertEqual(
                ["REQ-1"],
                chain["residues"][0]["established_requirement_ids"],
            )
            self.assertEqual(
                ["REQ-2"],
                chain["residues"][1]["established_requirement_ids"],
            )
            self.assertEqual(
                ["REQ-1", "REQ-3"],
                chain["residues"][1]["remaining_requirement_ids"],
            )
            self.assertEqual(1, len(chain["automatic_tasks"]))
            self.assertEqual(
                "REQ-2",
                chain["automatic_tasks"][0]["selected_requirement_id"],
            )
            self.assertIn(
                "reading evidence-1.md",
                chain["governed_stop"]["next_action"],
            )
            self.assertEqual(2, len(factory.prompts))
            self.assertEqual(2, len(factory.plans))

            three_run_record = temporal_support_record(
                {"evidence": (1,)},
                {"evidence": (2,), "modifies": ("evidence-1.md",)},
                {"evidence": (3,)},
            )
            self.assertEqual(
                ("REQ-2", "REQ-3"),
                satisfied_requirement_ids(three_run_record),
            )
            self.assertEqual(
                ("REQ-1",),
                tuple(
                    item["requirement_id"]
                    for item in remaining_requirements(three_run_record)
                ),
            )
            self.assertEqual(
                "HOLD",
                stage_c_outcome(three_run_record, {"gate": "HOLD"}),
            )

    def test_post_mutation_matching_reread_reestablishes_requirement(
        self,
    ) -> None:
        record = temporal_support_record(
            {"evidence": (1,)},
            {"evidence": (2,), "modifies": ("evidence-1.md",)},
            {"evidence": (1, 3)},
        )

        self.assertEqual(
            ("REQ-1", "REQ-2", "REQ-3"),
            satisfied_requirement_ids(record),
        )
        self.assertEqual((), remaining_requirements(record))

    def test_modify_of_different_path_does_not_invalidate_requirement(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = EvidenceFactory(
                {"evidence": (1,)},
                {"evidence": (2,), "modifies": ("other.txt",)},
                {"evidence": (3,)},
            )
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            controller.start_small_compound_loop(
                stage_c_request(allowed_mutation_paths=("other.txt",))
            )
            chain = self.terminal(controller)["compound_loop"]

            self.assertEqual("COMPLETE", chain["outcome"])
            self.assertEqual(
                ["REQ-1", "REQ-2", "REQ-3"],
                chain["residues"][-1]["established_requirement_ids"],
            )

    def test_post_mutation_nonmatching_read_does_not_reestablish(
        self,
    ) -> None:
        record = temporal_support_record(
            {"evidence": (1,)},
            {"evidence": (2,), "modifies": ("evidence-1.md",)},
            {"evidence": (3,), "nonmatching_evidence": (1,)},
        )

        self.assertEqual(
            ("REQ-2", "REQ-3"),
            satisfied_requirement_ids(record),
        )
        self.assertEqual(
            ("REQ-1",),
            tuple(
                item["requirement_id"]
                for item in remaining_requirements(record)
            ),
        )

    def test_stale_zero_progress_holds_without_dispatching_run_three(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = EvidenceFactory(
                {"evidence": (1,)},
                {"evidence": (), "modifies": ("evidence-1.md",)},
                {"evidence": (1, 2, 3)},
            )
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            controller.start_small_compound_loop(
                stage_c_request(
                    allowed_mutation_paths=("evidence-1.md",),
                )
            )
            chain = self.terminal(controller)["compound_loop"]

            self.assertEqual("HOLD", chain["outcome"])
            self.assertEqual(2, len(chain["runs"]))
            self.assertEqual(1, chain["automatic_continuations_started"])
            self.assertEqual(2, len(factory.prompts))
            self.assertEqual(1, len(factory.plans))
            self.assertEqual(
                "EVIDENCE-RECOVERY",
                chain["supervisor_judgments"][-1]["decision_route"],
            )

    def test_stale_terminal_replay_is_identical_and_dispatch_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = EvidenceFactory(
                {"evidence": (1,)},
                {"evidence": (2,), "modifies": ("evidence-1.md",)},
                {"evidence": (3,)},
            )
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            controller.start_small_compound_loop(
                stage_c_request(
                    allowed_mutation_paths=("evidence-1.md",),
                )
            )
            terminal = self.terminal(controller)["compound_loop"]

            restarted_factory = EvidenceFactory()
            restarted = self.make_controller(root, restarted_factory)
            replayed = restarted.snapshot()["compound_loop"]
            self.assertEqual("HOLD", replayed["outcome"])
            self.assertEqual(
                terminal["record_sha256"],
                replayed["record_sha256"],
            )
            self.assertEqual([], restarted_factory.prompts)

    def test_early_completion_after_run_one_or_two_preserves_unused_budget(
        self,
    ) -> None:
        cases = (
            ("run-one", ({"evidence": (1, 2, 3)},), 1, 0),
            (
                "run-two",
                ({"evidence": (1,)}, {"evidence": (2, 3)}),
                2,
                1,
            ),
        )
        for label, plans, runs, continuations in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                repository = create_repository(root)
                factory = EvidenceFactory(*plans, {"evidence": ()})
                controller = self.make_controller(root, factory)
                controller.select_repository(repository)
                controller.start_small_compound_loop(stage_c_request())
                chain = self.terminal(controller)["compound_loop"]

                self.assertEqual("COMPLETE", chain["outcome"])
                self.assertEqual(runs, len(chain["runs"]))
                self.assertEqual(runs, len(factory.prompts))
                self.assertEqual(
                    continuations,
                    chain["automatic_continuations_started"],
                )
                self.assertGreater(len(factory.plans), 0)

    def test_normal_terminal_without_new_evidence_stops_before_retry(self) -> None:
        cases = (
            ("run-one", ({"evidence": ()},), 1, 0),
            (
                "run-two",
                ({"evidence": (1,)}, {"evidence": (1,)}),
                2,
                1,
            ),
        )
        for label, plans, run_count, continuation_count in cases:
            with (
                self.subTest(label=label),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                repository = create_repository(root)
                factory = EvidenceFactory(*plans, {"evidence": (2,)})
                controller = self.make_controller(root, factory)
                controller.select_repository(repository)
                controller.start_small_compound_loop(stage_c_request())
                chain = self.terminal(controller)["compound_loop"]

                self.assertEqual("HOLD", chain["outcome"])
                self.assertEqual(run_count, len(chain["runs"]))
                self.assertEqual(
                    run_count,
                    len(chain["supervisor_judgments"]),
                )
                self.assertEqual(
                    continuation_count,
                    chain["automatic_continuations_started"],
                )
                self.assertEqual(
                    continuation_count,
                    len(chain["automatic_tasks"]),
                )
                self.assertEqual(run_count, len(factory.prompts))
                self.assertEqual(1, len(factory.plans))
                self.assertEqual(
                    "EVIDENCE-RECOVERY",
                    chain["supervisor_judgments"][-1]["decision_route"],
                )
                self.assertIn(
                    "not justified by sufficient evidence",
                    chain["supervisor_judgments"][-1]["reason"],
                )

    def test_non_go_human_seat_and_cap_all_stop_without_run_four(self) -> None:
        cases = (
            (
                "abnormal-run-two",
                stage_c_request(),
                (
                    {"evidence": (1,)},
                    {
                        "evidence": (2,),
                        "status": "ABNORMAL_TERMINAL",
                    },
                ),
                "HOLD",
                2,
            ),
            (
                "human-seat-run-one",
                stage_c_request(authority_sufficient=NO),
                ({"evidence": (1,)},),
                "HUMAN SEAT REQUIRED",
                1,
            ),
            (
                "hard-cap-run-three",
                stage_c_request(),
                ({"evidence": (1,)}, {"evidence": (2,)}, {"evidence": (2,)}),
                "CAP",
                3,
            ),
        )
        for label, request, plans, outcome, runs in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                repository = create_repository(root)
                factory = EvidenceFactory(*plans, {"evidence": ()})
                controller = self.make_controller(root, factory)
                controller.select_repository(repository)
                controller.start_small_compound_loop(request)
                chain = self.terminal(controller)["compound_loop"]

                self.assertEqual(outcome, chain["outcome"])
                self.assertEqual(runs, len(chain["runs"]))
                self.assertEqual(runs, len(chain["supervisor_judgments"]))
                self.assertEqual(runs, len(factory.prompts))
                self.assertGreater(len(factory.plans), 0)
                if label == "hard-cap-run-three":
                    with self.assertRaisesRegex(
                        RunConflictError,
                        "cannot be reset or renewed",
                    ):
                        controller.start_small_compound_loop(request)
                    self.assertEqual(3, len(factory.prompts))

    def test_run_three_execution_failure_stops_without_run_four(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = EvidenceFactory(
                {"evidence": (1,)},
                {"evidence": (2,)},
                "failure",
                {"evidence": (3,)},
            )
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            controller.start_small_compound_loop(stage_c_request())
            chain = self.terminal(controller)["compound_loop"]

            self.assertEqual("HOLD", chain["outcome"])
            self.assertEqual(2, len(chain["runs"]))
            self.assertEqual(2, chain["automatic_continuations_started"])
            self.assertEqual(3, len(factory.prompts))
            self.assertEqual(1, len(factory.plans))

    def test_run_three_cannot_widen_the_authorized_mutation_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = EvidenceFactory(
                {"evidence": (1,)},
                {"evidence": (2,)},
                "mutation",
                {"evidence": (3,)},
            )
            controller = self.make_controller(root, factory)
            controller.select_repository(repository)
            controller.start_small_compound_loop(
                stage_c_request(allowed_mutation_paths=("other.txt",))
            )
            chain = self.terminal(controller)["compound_loop"]

            self.assertEqual("BLOCK", chain["outcome"])
            self.assertEqual("DENIED", chain["runs"][2]["status"])
            self.assertEqual(
                "BLOCK",
                chain["supervisor_judgments"][2]["gate"],
            )
            self.assertEqual(3, len(factory.prompts))
            self.assertEqual(1, len(factory.plans))

    def test_stage_c_default_reuse_is_bounded_by_the_active_envelope(self) -> None:
        cases = (
            ("allowed.txt", "DENIED", "BLOCK", False),
            ("target.txt", "VERIFIED_SAVE", "HOLD", True),
        )
        for allowed_path, run_status, outcome, approved in cases:
            with self.subTest(allowed_path=allowed_path):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    repository = create_repository(root)
                    ordinary = AccelerationEngine(repository)
                    created = ordinary.evaluate(
                        run_id="ordinary-default-creation",
                        iteration=1,
                        decision_type=DecisionType.MODIFY_FILE,
                        requested_scope="target.txt",
                        source_interrupt_id="ordinary-default-creation",
                        choice_provider=lambda _identity: "2",
                    )
                    default_before = ordinary.store.active_default(
                        created.identity.decision_key
                    )
                    factory = EvidenceFactory("mutation")
                    controller = self.make_controller(root, factory)
                    controller.select_repository(repository)

                    controller.start_small_compound_loop(
                        stage_c_request(
                            allowed_mutation_paths=(allowed_path,),
                        )
                    )
                    chain = self.terminal(controller)["compound_loop"]

                    self.assertEqual(run_status, chain["runs"][0]["status"])
                    self.assertEqual(outcome, chain["outcome"])
                    approved_actions = [
                        action
                        for action in chain["runs"][0]["file_actions"]
                        if action["status"] == "approved"
                    ]
                    self.assertEqual(approved, bool(approved_actions))
                    if approved:
                        self.assertEqual("reused", approved_actions[0]["access"])
                    else:
                        self.assertFalse(
                            any(
                                action["access"] == "reused"
                                for action in chain["runs"][0]["file_actions"]
                            )
                        )
                    self.assertEqual(
                        default_before,
                        ordinary.store.active_default(
                            created.identity.decision_key
                        ),
                    )

    def test_rehashed_task_and_provenance_tampering_blocks_reconnect(self) -> None:
        def change_task_2(record: dict[str, Any]) -> None:
            injected = "independently supplied Task 2"
            record["automatic_tasks"][0]["task"] = injected
            record["automatic_tasks"][0]["task_sha256"] = hashlib.sha256(
                injected.encode("utf-8")
            ).hexdigest()

        def change_task_3(record: dict[str, Any]) -> None:
            injected = "repeated Task 2 label instead of causal Task 3"
            record["automatic_tasks"][1]["task"] = injected
            record["automatic_tasks"][1]["task_sha256"] = hashlib.sha256(
                injected.encode("utf-8")
            ).hexdigest()

        cases = (
            ("task-two", change_task_2),
            ("task-three", change_task_3),
            (
                "wrong-source-run",
                lambda record: record["automatic_tasks"][1].__setitem__(
                    "source_run_id",
                    record["runs"][0]["run_id"],
                ),
            ),
            (
                "wrong-source-evidence",
                lambda record: record["automatic_tasks"][1].__setitem__(
                    "source_evidence_sha256",
                    record["runs"][0]["evidence_sha256"],
                ),
            ),
        )
        for label, mutate in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self.run_complete_chain(root)
                state_path = (
                    root / "application-state" / "stage-b-continuation.json"
                )
                record = json.loads(state_path.read_text(encoding="utf-8"))
                mutate(record)
                record.pop("record_sha256")
                record["record_sha256"] = hash_payload(record)
                state_path.write_text(json.dumps(record), encoding="utf-8")

                restarted_factory = EvidenceFactory()
                restarted = self.make_controller(root, restarted_factory)
                snapshot = restarted.snapshot()
                self.assertEqual(
                    "BLOCKED_CORRUPT",
                    snapshot["compound_loop"]["state"],
                )
                self.assertEqual([], restarted_factory.prompts)

    def test_tampered_run_order_or_mutation_evidence_blocks_replay(
        self,
    ) -> None:
        def wrong_run_order(record: dict[str, Any]) -> None:
            record["runs"][1]["run_number"] = 1

        def malformed_mutation(record: dict[str, Any]) -> None:
            record["runs"][1]["file_actions"][0]["status"] = "authorized"

        for label, mutate in (
            ("run-order", wrong_run_order),
            ("mutation-evidence", malformed_mutation),
        ):
            with (
                self.subTest(label=label),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                repository = create_repository(root)
                controller = self.make_controller(
                    root,
                    EvidenceFactory(
                        {"evidence": (1,)},
                        {
                            "evidence": (2,),
                            "modifies": ("evidence-1.md",),
                        },
                        {"evidence": (3,)},
                    ),
                )
                controller.select_repository(repository)
                controller.start_small_compound_loop(
                    stage_c_request(
                        allowed_mutation_paths=("evidence-1.md",),
                    )
                )
                self.terminal(controller)

                state_path = (
                    root / "application-state" / "stage-b-continuation.json"
                )
                record = json.loads(state_path.read_text(encoding="utf-8"))
                mutate(record)
                for run in record["runs"]:
                    run_payload = {
                        key: value
                        for key, value in run.items()
                        if key != "evidence_sha256"
                    }
                    run["evidence_sha256"] = hash_payload(run_payload)
                record.pop("record_sha256")
                record["record_sha256"] = hash_payload(record)
                state_path.write_text(json.dumps(record), encoding="utf-8")

                restarted_factory = EvidenceFactory()
                restarted = self.make_controller(root, restarted_factory)
                self.assertEqual(
                    "BLOCKED_CORRUPT",
                    restarted.snapshot()["compound_loop"]["state"],
                )
                self.assertEqual([], restarted_factory.prompts)

    def test_stale_active_replay_never_dispatches_and_blocks_new_chain(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.run_complete_chain(root)
            state_path = (
                root / "application-state" / "stage-b-continuation.json"
            )
            record = json.loads(state_path.read_text(encoding="utf-8"))
            record["state"] = "RUN_3_ACTIVE"
            record["runs"] = record["runs"][:2]
            record["residues"] = record["residues"][:2]
            record["supervisor_judgments"] = record[
                "supervisor_judgments"
            ][:2]
            record["outcome"] = None
            record["governed_stop"] = None
            record.pop("record_sha256")
            record["record_sha256"] = hash_payload(record)
            state_path.write_text(json.dumps(record), encoding="utf-8")

            restarted_factory = EvidenceFactory({"evidence": (3,)})
            restarted = self.make_controller(root, restarted_factory)
            snapshot = restarted.snapshot()
            self.assertEqual(
                "RUN_3_ACTIVE",
                snapshot["compound_loop"]["state"],
            )
            self.assertEqual([], restarted_factory.prompts)
            with self.assertRaises(RunConflictError):
                restarted.start_small_compound_loop(stage_c_request())
            self.assertEqual([], restarted_factory.prompts)

    def test_terminal_reconnect_is_hash_identical_and_dispatch_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _controller, _factory, completed = self.run_complete_chain(root)
            restarted_factory = EvidenceFactory()
            restarted = self.make_controller(root, restarted_factory)
            snapshot = restarted.snapshot()

            self.assertEqual("TERMINAL", snapshot["compound_loop"]["state"])
            self.assertEqual(
                completed["compound_loop"]["record_sha256"],
                snapshot["compound_loop"]["record_sha256"],
            )
            self.assertEqual([], restarted_factory.prompts)
            state_path = (
                root / "application-state" / "stage-b-continuation.json"
            )
            self.assertEqual(0o600, state_path.stat().st_mode & 0o777)

    def test_governed_stop_and_cap_reconnect_without_dispatch(self) -> None:
        cases = (
            (
                "human-seat",
                stage_c_request(authority_sufficient=NO),
                ({"evidence": (1,)},),
                "HUMAN SEAT REQUIRED",
            ),
            (
                "cap",
                stage_c_request(),
                (
                    {"evidence": (1,)},
                    {"evidence": (2,)},
                    {"evidence": (2,)},
                ),
                "CAP",
            ),
        )
        for label, request, plans, outcome in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                repository = create_repository(root)
                controller = self.make_controller(
                    root,
                    EvidenceFactory(*plans),
                )
                controller.select_repository(repository)
                controller.start_small_compound_loop(request)
                terminal = self.terminal(controller)["compound_loop"]

                restarted_factory = EvidenceFactory()
                restarted = self.make_controller(root, restarted_factory)
                snapshot = restarted.snapshot()["compound_loop"]
                self.assertEqual(outcome, snapshot["outcome"])
                self.assertEqual(
                    terminal["record_sha256"],
                    snapshot["record_sha256"],
                )
                self.assertEqual([], restarted_factory.prompts)

    def test_real_stage_c_proof_binds_all_three_distinct_sources(self) -> None:
        sources = (
            (
                "validation/stage_a_supervisor_judgment_001.md",
                "a9b65437ea94b624ede85b2dfdb2f4f93d5a81a3bb17a5829d8f6c13a35ba77f",
            ),
            (
                "validation/stage_b_one_automatic_continuation_001.md",
                "35e3a28b4d6488e210f065646e43a4f0d2c99ece5e5bbf17186ea359f22f6fb8",
            ),
            (
                "docs/companion_product_roadmap_v0_3.md",
                "c3283a70e12d509419b0b314cf026fa59676564332913fa5c1c38abeacf73f3d",
            ),
        )
        for source, expected in sources:
            self.assertEqual(
                expected,
                hashlib.sha256(
                    REPO_ROOT.joinpath(source).read_bytes()
                ).hexdigest(),
            )
        proof = REPO_ROOT.joinpath(
            "validation/stage_c_small_compound_loop_001.md"
        ).read_text(encoding="utf-8")
        for exact in (
            "74e7ae5174ac73e2f295e3a4e2866cb3",
            "57b1bfdc-10dd-4b42-b4e8-41f4027feee9",
            "5ace2dfe-d7ca-46fe-aa43-12fffd2f0412",
            "b2120b10-ba90-4fbb-80b9-f1aeadbc4b1f",
            "0f804cbe44e24862de3ea97b059cd38f74eae07f8937cce0d6b7d8ff9e789d8b",
            "36bcecf09c87ba8853c1ccf849fb28f32b84b700d4a85f44ef15fb44f1be0b6e",
            "58b926ae5b75317466df53329cafa2cf700137b5a7b0638f03e6f79662d9cafa",
            "Stage C Completion Line:\nPASS",
            "Run 4:\nSTRUCTURALLY ABSENT",
        ):
            self.assertIn(exact, proof)


if __name__ == "__main__":
    unittest.main()
