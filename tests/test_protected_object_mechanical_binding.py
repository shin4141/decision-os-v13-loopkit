from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import (
    DecisionType,
    derive_decision_identity,
    hash_payload,
)
from decision_os.acceleration.store import AccelerationStore
from decision_os.companion.continuation import new_record
from decision_os.companion.controller import (
    CompanionController,
    ContinuationStateError,
)
from decision_os.companion.supervisor import ContractFact
from tests.test_companion_continuation import (
    RecordingFactory,
    stage_b_request,
)
from tests.test_companion_controller import create_repository, wait_for
from tests.test_companion_small_compound_loop import (
    EvidenceFactory,
    stage_c_request,
)


class ProtectedObjectMechanicalBindingTest(unittest.TestCase):
    @staticmethod
    def controller(
        root: Path,
        factory: RecordingFactory | EvidenceFactory,
    ) -> CompanionController:
        return CompanionController(
            state_path=root / "application-state" / "state.json",
            picker_runner=lambda _script: None,
            adapter_factory=factory,
        )

    def test_allowed_path_and_semantic_prose_preserve_existing_behavior(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            ordinary = AccelerationEngine(repository)
            ordinary.evaluate(
                run_id="semantic-prose-default",
                iteration=1,
                decision_type=DecisionType.MODIFY_FILE,
                requested_scope="target.txt",
                source_interrupt_id="semantic-prose-default",
                choice_provider=lambda _identity: "2",
            )
            factory = RecordingFactory("mutation")
            controller = self.controller(root, factory)
            controller.select_repository(repository)

            request = stage_b_request(
                goal_complete_after_run_1=ContractFact.SATISFIED,
                protected_objects=(
                    "target.txt must remain byte-for-byte unchanged",
                ),
                mechanically_protected_paths=(),
            )
            controller.start_one_automatic_continuation(request)
            stopped = wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "STOPPED"
                ),
            )

            run = stopped["compound_loop"]["runs"][0]
            self.assertIn(run["status"], {"VERIFIED_SAVE", "VERIFIED_REUSE"})
            self.assertEqual("approved", run["file_actions"][0]["status"])
            self.assertEqual([], request.as_dict()["mechanically_protected_paths"])

    def test_nonconflicting_mechanical_path_is_persisted_and_replayed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            factory = EvidenceFactory({"evidence": (1, 2, 3)})
            controller = self.controller(root, factory)
            controller.select_repository(repository)

            controller.start_small_compound_loop(
                stage_c_request(
                    allowed_mutation_paths=("other.txt",),
                    mechanically_protected_paths=("./target.txt",),
                )
            )
            terminal = wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "TERMINAL"
                ),
            )["compound_loop"]

            self.assertEqual("COMPLETE", terminal["outcome"])
            self.assertEqual(3, terminal["total_run_cap"])
            self.assertEqual(2, terminal["automatic_continuation_limit"])
            self.assertEqual(
                ["target.txt"],
                terminal["request"]["mechanically_protected_paths"],
            )
            self.assertEqual(
                ["other.txt"],
                terminal["request"]["allowed_mutation_paths"],
            )

            restarted_factory = EvidenceFactory()
            restarted = self.controller(root, restarted_factory)
            replayed = restarted.snapshot()["compound_loop"]
            self.assertEqual(terminal["record_sha256"], replayed["record_sha256"])
            self.assertEqual(
                ["target.txt"],
                replayed["request"]["mechanically_protected_paths"],
            )
            self.assertEqual([], restarted_factory.prompts)

    def test_same_machine_path_is_rejected_even_when_caller_says_satisfied(
        self,
    ) -> None:
        for label, build in (
            (
                "stage-b",
                lambda: stage_b_request(
                    mechanically_protected_paths=("target.txt",),
                    protected_object_and_ownership_unchanged=(
                        ContractFact.SATISFIED
                    ),
                ),
            ),
            (
                "stage-c",
                lambda: stage_c_request(
                    mechanically_protected_paths=("target.txt",),
                    protected_object_and_ownership_unchanged=(
                        ContractFact.SATISFIED
                    ),
                ),
            ),
        ):
            with self.subTest(stage=label):
                with self.assertRaisesRegex(
                    ValueError,
                    "conflict with mechanically protected path identities",
                ):
                    build()

    def test_normalized_conflict_fails_before_persistence_or_dispatch(
        self,
    ) -> None:
        cases = (
            (
                "stage-b",
                RecordingFactory(),
                lambda controller: controller.start_one_automatic_continuation(
                    stage_b_request(
                        allowed_mutation_paths=("./target.txt",),
                        mechanically_protected_paths=("target.txt",),
                    )
                ),
            ),
            (
                "stage-c",
                EvidenceFactory(),
                lambda controller: controller.start_small_compound_loop(
                    stage_c_request(
                        allowed_mutation_paths=("./target.txt",),
                        mechanically_protected_paths=("target.txt",),
                    )
                ),
            ),
        )
        for label, factory, start in cases:
            with (
                self.subTest(stage=label),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                repository = create_repository(root)
                controller = self.controller(root, factory)
                controller.select_repository(repository)

                with self.assertRaises(ContinuationStateError):
                    start(controller)

                self.assertEqual("idle", controller.snapshot()["run"]["state"])
                self.assertEqual([], factory.prompts)
                self.assertFalse(
                    (
                        root
                        / "application-state"
                        / "stage-b-continuation.json"
                    ).exists()
                )

    def test_unrelated_allowed_identity_remains_usable_in_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.controller(root, RecordingFactory())
            controller.select_repository(repository)
            request = stage_b_request(
                allowed_mutation_paths=("other.txt",),
                mechanically_protected_paths=("target.txt",),
            )
            chain_id = "a" * 32
            record = controller._continuation_store.save(
                new_record(
                    request,
                    chain_id=chain_id,
                    repository_id=AccelerationStore(repository).repository_id,
                )
            )
            controller._compound_loop = record
            controller._compound_active = True
            controller._compound_recovery_required = False
            controller._compound_allowed_mutation_paths = ("other.txt",)
            controller._run["state"] = "running"
            controller._run["task_mode"] = "contract"
            controller._run["continuation"] = {
                "schema": "decision-os-bounded-run-continuation-v0.1",
                "chain_id": chain_id,
                "run_number": 1,
                "automatic": False,
                "source_run_id": None,
                "source_evidence_sha256": None,
                "task_sha256": hashlib.sha256(
                    request.run_1_task.encode("utf-8")
                ).hexdigest(),
            }

            allowed = derive_decision_identity(
                repository,
                DecisionType.MODIFY_FILE,
                "other.txt",
            )
            protected = derive_decision_identity(
                repository,
                DecisionType.MODIFY_FILE,
                "target.txt",
            )
            self.assertTrue(controller._compound_mutation_preflight(allowed))
            self.assertFalse(controller._compound_mutation_preflight(protected))

    def test_replay_rejects_erased_mechanical_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = self.controller(
                root,
                EvidenceFactory({"evidence": (1, 2, 3)}),
            )
            controller.select_repository(repository)
            controller.start_small_compound_loop(
                stage_c_request(
                    allowed_mutation_paths=("other.txt",),
                    mechanically_protected_paths=("target.txt",),
                )
            )
            wait_for(
                controller,
                lambda state: (
                    state["compound_loop"] is not None
                    and state["compound_loop"].get("state") == "TERMINAL"
                ),
            )

            state_path = root / "application-state" / "stage-b-continuation.json"
            original = json.loads(state_path.read_text(encoding="utf-8"))
            for label, mutate in (
                (
                    "field-erased",
                    lambda record: record["request"].__delitem__(
                        "mechanically_protected_paths"
                    ),
                ),
                (
                    "conflict-injected",
                    lambda record: record["request"].__setitem__(
                        "allowed_mutation_paths",
                        ["target.txt"],
                    ),
                ),
            ):
                with self.subTest(tampering=label):
                    record = json.loads(json.dumps(original))
                    mutate(record)
                    record.pop("record_sha256")
                    record["record_sha256"] = hash_payload(record)
                    state_path.write_text(json.dumps(record), encoding="utf-8")

                    restarted_factory = EvidenceFactory()
                    restarted = self.controller(root, restarted_factory)
                    snapshot = restarted.snapshot()
                    self.assertEqual(
                        "BLOCKED_CORRUPT",
                        snapshot["compound_loop"]["state"],
                    )
                    self.assertEqual(
                        "BLOCK",
                        snapshot["compound_loop"]["outcome"],
                    )
                    self.assertEqual([], restarted_factory.prompts)


if __name__ == "__main__":
    unittest.main()
