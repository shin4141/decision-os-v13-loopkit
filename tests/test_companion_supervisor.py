from __future__ import annotations

import unittest
from dataclasses import replace
import hashlib
from pathlib import Path
import subprocess
from typing import Any

from decision_os.acceleration.codex_adapter import (
    CodexFileAction,
    CodexReadEvidence,
    CodexRunResult,
    CodexRuntimeIdentity,
)
from decision_os.acceleration.engine import CheckpointOutcome
from decision_os.companion.supervisor import (
    ContractFact,
    DecisionRoute,
    SupervisorContext,
    SupervisorGate,
    judge_continuation,
)


YES = ContractFact.SATISFIED
NO = ContractFact.NOT_SATISFIED
UNKNOWN = ContractFact.UNKNOWN
REPO_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_HEAD = "a04f1463fc1f4bf46196eeea1702c5b096fd36e2"
ACCEPTANCE_RECORD_SHA256 = (
    "c8f008dadce1d7a9684b5a658a3302f83bd50c17a48e2a916c71ed7f4971e336"
)


def completed_result(
    *,
    status: str = "VERIFIED_SAVE",
    normal_terminal: bool = True,
    turn_status: str | None = "completed",
) -> CodexRunResult:
    return CodexRunResult(
        run_id="real-bounded-run-001",
        normal_terminal=normal_terminal,
        status=status,
        error_type=None,
        turn_status=turn_status,
        runtime_identity=CodexRuntimeIdentity(
            model="gpt-5.6-sol",
            reasoning_effort="ultra",
            service_tier="priority",
            codex_cli_version="0.146.0-alpha.3.1",
            account_type="chatgpt",
        ),
        checkpoint_outcomes=(
            CheckpointOutcome(
                status="VERIFIED_SAVE",
                verified=True,
                event_hash="a" * 64,
            ),
        ),
        final_message="The first bounded repair completed.",
        file_actions=(
            CodexFileAction(
                action="Modify",
                normalized_scope="target.txt",
                access="reused",
                status="approved",
            ),
        ),
        read_evidence=(
            CodexReadEvidence(
                path="target.txt",
                byte_count=7,
                sha256="b" * 64,
                repository_identity="c" * 40,
                status="succeeded",
            ),
        ),
    )


def context(**overrides: Any) -> SupervisorContext:
    values: dict[str, Any] = {
        "goal": "Close one bounded repository repair and verify it.",
        "established_state": "The exact one-file repair is complete.",
        "remaining_gap": "Run the already-authorized focused verification.",
        "next_bounded_action": "Run the focused verification without mutation.",
        "evidence_recovery_action": (
            "Recover the missing evidence from the bounded Run and retry judgment."
        ),
        "irreducible_human_decision": None,
        "evidence_refs": ("validation/real-bounded-run-001.md",),
        "completed_runs": 1,
        "max_runs": 3,
        "goal_complete": NO,
        "continuation_proof_sufficient": YES,
        "goal_unchanged": YES,
        "authority_sufficient": YES,
        "blast_radius_bounded": YES,
        "action_reversible_or_authorized": YES,
        "evidence_sufficient": YES,
        "no_material_human_preference_required": YES,
        "no_external_or_irreversible_commitment": YES,
        "cost_boundary_intact": YES,
        "protected_object_and_ownership_unchanged": YES,
        "no_authoritative_conflict": YES,
        "no_truly_unanswered_human_question": YES,
    }
    values.update(overrides)
    return SupervisorContext(**values)


class CompanionSupervisorTest(unittest.TestCase):
    def test_canonical_real_acceptance_run_is_consumed_and_stops(self) -> None:
        record = (
            REPO_ROOT
            / "validation"
            / "decision_os_companion_acceptance_run_001.md"
        )
        self.assertEqual(
            ACCEPTANCE_RECORD_SHA256,
            hashlib.sha256(record.read_bytes()).hexdigest(),
        )
        adapter_source = subprocess.run(
            (
                "git",
                "show",
                f"{ACCEPTANCE_HEAD}:decision_os/acceleration/codex_adapter.py",
            ),
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertIn('CODEX_CLI_VERSION = "0.146.0-alpha.3.1"', adapter_source)

        real_result = replace(
            completed_result(),
            run_id="decision-os-companion-acceptance-run-001",
            final_message="The requested exact file change completed normally.",
            file_actions=(
                CodexFileAction(
                    action="Modify",
                    normalized_scope="companion_acceptance_trial.txt",
                    access="reused",
                    status="approved",
                ),
            ),
            read_evidence=(),
            checkpoint_outcomes=(
                CheckpointOutcome(
                    status="VERIFIED_SAVE",
                    verified=True,
                    event_hash=(
                        "840f263accae0a2093f9aa5baa60e4aaa5b75448825f97ad96"
                        "f63285ec45f491"
                    ),
                ),
            ),
        )
        judgment = judge_continuation(
            real_result,
            context(
                goal=(
                    "Complete the bounded fresh-process Companion acceptance "
                    "file change."
                ),
                established_state=(
                    "The exact requested file was modified, the turn completed "
                    "normally, and the cross-Run checkpoint produced VERIFIED_SAVE."
                ),
                remaining_gap="none",
                next_bounded_action=None,
                evidence_refs=(
                    "validation/decision_os_companion_acceptance_run_001.md"
                    f"#sha256={ACCEPTANCE_RECORD_SHA256}",
                ),
                goal_complete=YES,
            ),
        )

        self.assertEqual(SupervisorGate.HOLD, judgment.gate)
        self.assertEqual(DecisionRoute.STOP, judgment.decision_route)
        self.assertIsNone(judgment.human_seat_return)
        self.assertFalse(judgment.automatic_second_run_started)

    def test_clean_real_run_routes_routine_continuation_to_go(self) -> None:
        judgment = judge_continuation(completed_result(), context())

        self.assertEqual(SupervisorGate.GO, judgment.gate)
        self.assertEqual(DecisionRoute.AI_OWNED, judgment.decision_route)
        self.assertEqual(
            "Run the focused verification without mutation.",
            judgment.next_bounded_action,
        )
        self.assertIsNone(judgment.human_seat_return)
        self.assertFalse(judgment.automatic_second_run_started)
        self.assertEqual(
            {
                "run_id": "real-bounded-run-001",
                "status": "VERIFIED_SAVE",
            },
            judgment.as_dict()["consumed_run"],
        )

    def test_goal_change_returns_one_irreducible_human_decision(self) -> None:
        judgment = judge_continuation(
            completed_result(),
            context(
                goal_unchanged=NO,
                irreducible_human_decision=(
                    "Choose whether the Goal remains repository repair or changes "
                    "to release preparation."
                ),
            ),
        )

        self.assertEqual(SupervisorGate.HOLD, judgment.gate)
        self.assertEqual(DecisionRoute.HUMAN_SEAT, judgment.decision_route)
        self.assertIsNone(judgment.next_bounded_action)
        self.assertEqual(
            "Choose whether the Goal remains repository repair or changes to "
            "release preparation.",
            judgment.human_seat_return,
        )

    def test_known_authority_expansion_returns_to_human_seat(self) -> None:
        judgment = judge_continuation(
            completed_result(),
            context(authority_sufficient=NO),
        )

        self.assertEqual(SupervisorGate.BLOCK, judgment.gate)
        self.assertEqual(DecisionRoute.HUMAN_SEAT, judgment.decision_route)
        self.assertEqual(
            "Decide whether to authorize the proposed next bounded action.",
            judgment.human_seat_return,
        )

    def test_unknown_authority_routes_to_ai_owned_evidence_recovery(self) -> None:
        judgment = judge_continuation(
            completed_result(),
            context(authority_sufficient=UNKNOWN),
        )

        self.assertEqual(SupervisorGate.BLOCK, judgment.gate)
        self.assertEqual(
            DecisionRoute.EVIDENCE_RECOVERY,
            judgment.decision_route,
        )
        self.assertIsNone(judgment.human_seat_return)
        self.assertEqual(
            "Recover the missing evidence from the bounded Run and retry judgment.",
            judgment.next_bounded_action,
        )

    def test_insufficient_evidence_holds_without_human_question(self) -> None:
        judgment = judge_continuation(
            completed_result(),
            context(evidence_sufficient=NO),
        )

        self.assertEqual(SupervisorGate.HOLD, judgment.gate)
        self.assertEqual(
            DecisionRoute.EVIDENCE_RECOVERY,
            judgment.decision_route,
        )
        self.assertIsNone(judgment.human_seat_return)

    def test_abnormal_worker_result_fails_closed_before_contract_go(self) -> None:
        judgment = judge_continuation(
            completed_result(
                status="ABNORMAL_TERMINAL",
                normal_terminal=False,
                turn_status="failed",
            ),
            context(),
        )

        self.assertEqual(SupervisorGate.HOLD, judgment.gate)
        self.assertEqual(
            DecisionRoute.EVIDENCE_RECOVERY,
            judgment.decision_route,
        )
        self.assertIn("normal-terminal", judgment.reason)

    def test_verified_status_without_checkpoint_evidence_holds(self) -> None:
        judgment = judge_continuation(
            replace(completed_result(), checkpoint_outcomes=()),
            context(),
        )

        self.assertEqual(SupervisorGate.HOLD, judgment.gate)
        self.assertEqual(
            DecisionRoute.EVIDENCE_RECOVERY,
            judgment.decision_route,
        )
        self.assertIn("runtime or read evidence", judgment.reason)

    def test_first_live_cap_returns_exact_cap_decision(self) -> None:
        judgment = judge_continuation(
            completed_result(),
            context(completed_runs=3),
        )

        self.assertEqual(SupervisorGate.CAP, judgment.gate)
        self.assertEqual(DecisionRoute.HUMAN_SEAT, judgment.decision_route)
        self.assertEqual(
            "Decide whether to extend the 3-Run cap for the unchanged Goal.",
            judgment.human_seat_return,
        )

    def test_exceeded_run_cap_still_returns_structured_cap_decision(self) -> None:
        judgment = judge_continuation(
            completed_result(),
            context(completed_runs=4),
        )

        self.assertEqual(SupervisorGate.CAP, judgment.gate)
        self.assertEqual(DecisionRoute.HUMAN_SEAT, judgment.decision_route)
        self.assertIn("4/3 total Runs", judgment.reason)
        self.assertEqual(
            "Decide whether to extend the 3-Run cap for the unchanged Goal.",
            judgment.human_seat_return,
        )

    def test_completed_goal_stops_without_second_run_or_human_return(self) -> None:
        judgment = judge_continuation(
            completed_result(),
            context(
                goal_complete=YES,
                remaining_gap="none",
                next_bounded_action=None,
            ),
        )

        self.assertEqual(SupervisorGate.HOLD, judgment.gate)
        self.assertEqual(DecisionRoute.STOP, judgment.decision_route)
        self.assertEqual(
            "Preserve the completed Run evidence and close the Goal.",
            judgment.next_bounded_action,
        )
        self.assertFalse(judgment.automatic_second_run_started)

    def test_proved_authoritative_conflict_returns_to_human_seat(self) -> None:
        judgment = judge_continuation(
            completed_result(),
            context(no_authoritative_conflict=NO),
        )

        self.assertEqual(SupervisorGate.BLOCK, judgment.gate)
        self.assertEqual(DecisionRoute.HUMAN_SEAT, judgment.decision_route)
        self.assertEqual(
            "Resolve the identified authoritative conflict.",
            judgment.human_seat_return,
        )

    def test_missing_next_action_remains_routine_ai_owned_work(self) -> None:
        judgment = judge_continuation(
            completed_result(),
            context(next_bounded_action=None),
        )

        self.assertEqual(SupervisorGate.HOLD, judgment.gate)
        self.assertEqual(DecisionRoute.AI_OWNED, judgment.decision_route)
        self.assertIsNone(judgment.human_seat_return)
        self.assertIn("Derive one bounded next action", judgment.next_bounded_action)


if __name__ == "__main__":
    unittest.main()
