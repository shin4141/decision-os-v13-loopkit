"""Stage A authority judgment over one completed bounded Worker Run.

The Supervisor is deliberately separate from execution.  It consumes the
existing immutable ``CodexRunResult`` plus an explicit authority context,
returns one structured judgment, and has no adapter or Run-start capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from decision_os.acceleration.codex_adapter import CodexRunResult


FIRST_LIVE_MAX_RUNS = 3
_COMPLETED_RUN_STATUSES = frozenset(
    {"NORMAL_TERMINAL", "VERIFIED_SAVE", "VERIFIED_REUSE"}
)


class ContractFact(str, Enum):
    """Evidence state for one Human Seat return-contract invariant."""

    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    UNKNOWN = "UNKNOWN"


class SupervisorGate(str, Enum):
    """Existing V13 gates available to the Stage A Supervisor."""

    GO = "GO"
    HOLD = "HOLD"
    CAP = "CAP"
    BLOCK = "BLOCK"


class DecisionRoute(str, Enum):
    """Who owns the consequence of the Supervisor judgment."""

    AI_OWNED = "AI-OWNED"
    EVIDENCE_RECOVERY = "EVIDENCE-RECOVERY"
    HUMAN_SEAT = "HUMAN-SEAT"
    STOP = "STOP"


@dataclass(frozen=True)
class SupervisorContext:
    """Authority and evidence facts fixed before judging one Worker result."""

    goal: str
    established_state: str
    remaining_gap: str
    next_bounded_action: str | None
    evidence_recovery_action: str | None
    irreducible_human_decision: str | None
    evidence_refs: tuple[str, ...]
    completed_runs: int
    max_runs: int
    goal_complete: ContractFact
    continuation_proof_sufficient: ContractFact
    goal_unchanged: ContractFact
    authority_sufficient: ContractFact
    blast_radius_bounded: ContractFact
    action_reversible_or_authorized: ContractFact
    evidence_sufficient: ContractFact
    no_material_human_preference_required: ContractFact
    no_external_or_irreversible_commitment: ContractFact
    cost_boundary_intact: ContractFact
    protected_object_and_ownership_unchanged: ContractFact
    no_authoritative_conflict: ContractFact
    no_truly_unanswered_human_question: ContractFact

    def __post_init__(self) -> None:
        for label, value, maximum in (
            ("Goal", self.goal, 20_000),
            ("Established state", self.established_state, 8_000),
            ("Remaining gap", self.remaining_gap, 8_000),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} must be a non-empty string.")
            if len(value) > maximum:
                raise ValueError(f"{label} exceeds the bounded size limit.")
        for label, value in (
            ("Next bounded action", self.next_bounded_action),
            ("Evidence recovery action", self.evidence_recovery_action),
            ("Irreducible Human Seat decision", self.irreducible_human_decision),
        ):
            if value is not None and (
                not isinstance(value, str)
                or not value.strip()
                or len(value) > 8_000
            ):
                raise ValueError(
                    f"{label} must be absent or one bounded non-empty string."
                )
        if (
            not isinstance(self.completed_runs, int)
            or isinstance(self.completed_runs, bool)
            or self.completed_runs < 1
        ):
            raise ValueError("Completed Runs must be a positive integer.")
        if (
            not isinstance(self.max_runs, int)
            or isinstance(self.max_runs, bool)
            or not 1 <= self.max_runs <= FIRST_LIVE_MAX_RUNS
        ):
            raise ValueError("The first live Run cap must be between 1 and 3.")
        if (
            not isinstance(self.evidence_refs, tuple)
            or any(
                not isinstance(item, str)
                or not item.strip()
                or len(item) > 2_000
                for item in self.evidence_refs
            )
        ):
            raise ValueError("Evidence references must be bounded strings.")
        for name, fact in self.contract_facts():
            if not isinstance(fact, ContractFact):
                raise ValueError(f"{name} must be an explicit ContractFact.")

    def contract_facts(self) -> tuple[tuple[str, ContractFact], ...]:
        return (
            ("goal_complete", self.goal_complete),
            (
                "continuation_proof_sufficient",
                self.continuation_proof_sufficient,
            ),
            ("goal_unchanged", self.goal_unchanged),
            ("authority_sufficient", self.authority_sufficient),
            ("blast_radius_bounded", self.blast_radius_bounded),
            (
                "action_reversible_or_authorized",
                self.action_reversible_or_authorized,
            ),
            ("evidence_sufficient", self.evidence_sufficient),
            (
                "no_material_human_preference_required",
                self.no_material_human_preference_required,
            ),
            (
                "no_external_or_irreversible_commitment",
                self.no_external_or_irreversible_commitment,
            ),
            ("cost_boundary_intact", self.cost_boundary_intact),
            (
                "protected_object_and_ownership_unchanged",
                self.protected_object_and_ownership_unchanged,
            ),
            ("no_authoritative_conflict", self.no_authoritative_conflict),
            (
                "no_truly_unanswered_human_question",
                self.no_truly_unanswered_human_question,
            ),
        )


@dataclass(frozen=True)
class SupervisorJudgment:
    """One complete Stage A result; it never carries execution authority."""

    consumed_run_id: str
    consumed_run_status: str
    gate: SupervisorGate
    reason: str
    established_state: str
    remaining_gap: str
    decision_route: DecisionRoute
    next_bounded_action: str | None
    human_seat_return: str | None
    evidence_refs: tuple[str, ...]
    automatic_second_run_started: bool = False

    def __post_init__(self) -> None:
        if self.automatic_second_run_started:
            raise ValueError("Stage A cannot start a second Run.")
        if (self.next_bounded_action is None) == (
            self.human_seat_return is None
        ):
            raise ValueError(
                "A judgment requires exactly one next action or Human Seat return."
            )
        if (
            self.decision_route == DecisionRoute.HUMAN_SEAT
        ) != (self.human_seat_return is not None):
            raise ValueError("Human Seat route and return must agree.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "decision-os-supervisor-judgment-v0.1",
            "role": "SUPERVISOR",
            "consumed_run": {
                "run_id": self.consumed_run_id,
                "status": self.consumed_run_status,
            },
            "gate": self.gate.value,
            "reason": self.reason,
            "established_state": self.established_state,
            "remaining_gap": self.remaining_gap,
            "decision_route": self.decision_route.value,
            "next_bounded_action": self.next_bounded_action,
            "human_seat_return": self.human_seat_return,
            "evidence_refs": list(self.evidence_refs),
            "automatic_second_run_started": False,
        }


def _established(result: CodexRunResult, context: SupervisorContext) -> str:
    return (
        f"Worker Run {result.run_id} ended {result.status}. "
        f"{context.established_state.strip()}"
    )


def _judgment(
    result: CodexRunResult,
    context: SupervisorContext,
    *,
    gate: SupervisorGate,
    reason: str,
    route: DecisionRoute,
    next_action: str | None = None,
    human_return: str | None = None,
) -> SupervisorJudgment:
    return SupervisorJudgment(
        consumed_run_id=result.run_id,
        consumed_run_status=result.status,
        gate=gate,
        reason=reason,
        established_state=_established(result, context),
        remaining_gap=context.remaining_gap.strip(),
        decision_route=route,
        next_bounded_action=next_action,
        human_seat_return=human_return,
        evidence_refs=context.evidence_refs,
    )


def _recovery_action(context: SupervisorContext, missing: str) -> str:
    if context.evidence_recovery_action is not None:
        return context.evidence_recovery_action.strip()
    return f"Recover sufficient evidence for {missing} under current authority."


def _human_return(context: SupervisorContext, fallback: str) -> str:
    if context.irreducible_human_decision is not None:
        return context.irreducible_human_decision.strip()
    return fallback


def _runtime_and_read_evidence_sufficient(result: CodexRunResult) -> bool:
    identity = result.runtime_identity
    if identity is None or any(
        not isinstance(value, str) or not value.strip()
        for value in (
            identity.model,
            identity.reasoning_effort,
            identity.service_tier,
            identity.codex_cli_version,
            identity.account_type,
        )
    ):
        return False
    for evidence in result.read_evidence:
        if (
            evidence.status != "succeeded"
            or not isinstance(evidence.path, str)
            or not evidence.path
            or not isinstance(evidence.byte_count, int)
            or isinstance(evidence.byte_count, bool)
            or evidence.byte_count < 0
            or not isinstance(evidence.sha256, str)
            or len(evidence.sha256) != 64
            or not isinstance(evidence.repository_identity, str)
            or not evidence.repository_identity
        ):
            return False
    if result.status in {"VERIFIED_SAVE", "VERIFIED_REUSE"}:
        if not result.checkpoint_outcomes:
            return False
        terminal = result.checkpoint_outcomes[-1]
        if not terminal.verified or terminal.status != result.status:
            return False
    return True


def judge_continuation(
    result: CodexRunResult,
    context: SupervisorContext,
) -> SupervisorJudgment:
    """Judge whether another bounded loop is allowed; execute nothing."""

    if not isinstance(result, CodexRunResult):
        raise TypeError("Stage A requires one CodexRunResult.")
    if not isinstance(context, SupervisorContext):
        raise TypeError("Stage A requires one SupervisorContext.")

    if not isinstance(result.run_id, str) or not result.run_id.strip():
        return _judgment(
            result,
            context,
            gate=SupervisorGate.BLOCK,
            reason="The Worker Run identity is not established.",
            route=DecisionRoute.EVIDENCE_RECOVERY,
            next_action=_recovery_action(context, "the Worker Run identity"),
        )
    if result.status == "DENIED":
        return _judgment(
            result,
            context,
            gate=SupervisorGate.BLOCK,
            reason="The recorded file decision denied this bounded action.",
            route=DecisionRoute.STOP,
            next_action="Preserve the denial and stop this continuation path.",
        )
    if result.status == "UNSUPPORTED_MUTATION":
        return _judgment(
            result,
            context,
            gate=SupervisorGate.HOLD,
            reason="The Worker result did not verify the requested mutation path.",
            route=DecisionRoute.EVIDENCE_RECOVERY,
            next_action=_recovery_action(context, "the unsupported Run path"),
        )
    if (
        result.status not in _COMPLETED_RUN_STATUSES
        or not result.normal_terminal
        or result.turn_status != "completed"
        or result.error_type is not None
        or result.failure_diagnostic is not None
    ):
        return _judgment(
            result,
            context,
            gate=SupervisorGate.HOLD,
            reason="The Worker Run lacks a clean normal-terminal result.",
            route=DecisionRoute.EVIDENCE_RECOVERY,
            next_action=_recovery_action(context, "normal-terminal Run evidence"),
        )
    if not _runtime_and_read_evidence_sufficient(result):
        return _judgment(
            result,
            context,
            gate=SupervisorGate.HOLD,
            reason="The Worker Run lacks sufficient runtime or read evidence.",
            route=DecisionRoute.EVIDENCE_RECOVERY,
            next_action=_recovery_action(context, "runtime and read evidence"),
        )
    if not context.evidence_refs:
        return _judgment(
            result,
            context,
            gate=SupervisorGate.HOLD,
            reason="The Worker result is not bound to persisted evidence.",
            route=DecisionRoute.EVIDENCE_RECOVERY,
            next_action=_recovery_action(context, "persisted Run provenance"),
        )

    unknown = [
        name
        for name, fact in context.contract_facts()
        if fact == ContractFact.UNKNOWN
    ]
    if unknown:
        gate = (
            SupervisorGate.BLOCK
            if "continuation_proof_sufficient" in unknown
            or "authority_sufficient" in unknown
            else SupervisorGate.HOLD
        )
        return _judgment(
            result,
            context,
            gate=gate,
            reason=(
                "The Human Seat contract cannot be evaluated from established "
                f"evidence: {', '.join(unknown)}."
            ),
            route=DecisionRoute.EVIDENCE_RECOVERY,
            next_action=_recovery_action(
                context,
                ", ".join(unknown),
            ),
        )

    if context.continuation_proof_sufficient == ContractFact.NOT_SATISFIED:
        return _judgment(
            result,
            context,
            gate=SupervisorGate.BLOCK,
            reason="Sufficient continuation proof is unavailable.",
            route=DecisionRoute.EVIDENCE_RECOVERY,
            next_action=_recovery_action(context, "continuation proof"),
        )
    if context.evidence_sufficient == ContractFact.NOT_SATISFIED:
        return _judgment(
            result,
            context,
            gate=SupervisorGate.HOLD,
            reason="The next loop is not justified by sufficient evidence.",
            route=DecisionRoute.EVIDENCE_RECOVERY,
            next_action=_recovery_action(context, "the remaining evidence gap"),
        )
    if context.goal_complete == ContractFact.SATISFIED:
        return _judgment(
            result,
            context,
            gate=SupervisorGate.HOLD,
            reason="The declared Goal is complete; another Worker Run is unnecessary.",
            route=DecisionRoute.STOP,
            next_action="Preserve the completed Run evidence and close the Goal.",
        )
    if context.completed_runs >= context.max_runs:
        return _judgment(
            result,
            context,
            gate=SupervisorGate.CAP,
            reason=(
                "The authorized loop-count cap is exhausted "
                f"({context.completed_runs}/{context.max_runs} total Runs)."
            ),
            route=DecisionRoute.HUMAN_SEAT,
            human_return=(
                _human_return(
                    context,
                    f"Decide whether to extend the {context.max_runs}-Run cap "
                    "for the unchanged Goal.",
                )
            ),
        )

    human_conditions = (
        (
            "goal_unchanged",
            context.goal_unchanged,
            SupervisorGate.HOLD,
            "Continuing requires changing the declared Goal or Aspire direction.",
            "Decide whether to change the declared Goal or Aspire direction.",
        ),
        (
            "authority_sufficient",
            context.authority_sufficient,
            SupervisorGate.BLOCK,
            "The next bounded action exceeds current authority.",
            "Decide whether to authorize the proposed next bounded action.",
        ),
        (
            "blast_radius_bounded",
            context.blast_radius_bounded,
            SupervisorGate.BLOCK,
            "The next action exceeds the bounded blast radius.",
            "Decide whether to expand the authorized blast radius.",
        ),
        (
            "action_reversible_or_authorized",
            context.action_reversible_or_authorized,
            SupervisorGate.BLOCK,
            "The next action is neither reversible nor explicitly authorized.",
            "Decide whether to authorize the irreversible action.",
        ),
        (
            "no_material_human_preference_required",
            context.no_material_human_preference_required,
            SupervisorGate.HOLD,
            "Continuation requires a material human value preference.",
            "Choose the value direction that should govern the unchanged Goal.",
        ),
        (
            "no_external_or_irreversible_commitment",
            context.no_external_or_irreversible_commitment,
            SupervisorGate.BLOCK,
            "Continuation introduces an external or irreversible commitment.",
            (
                "Decide whether to make the identified external or "
                "irreversible commitment."
            ),
        ),
        (
            "cost_boundary_intact",
            context.cost_boundary_intact,
            SupervisorGate.CAP,
            "The authorized cost boundary is exhausted.",
            "Decide whether to expand the authorized cost boundary.",
        ),
        (
            "protected_object_and_ownership_unchanged",
            context.protected_object_and_ownership_unchanged,
            SupervisorGate.BLOCK,
            "Continuation changes a Protected Object or ownership boundary.",
            "Decide whether to change the Protected Object or ownership boundary.",
        ),
        (
            "no_authoritative_conflict",
            context.no_authoritative_conflict,
            SupervisorGate.BLOCK,
            "A genuine authoritative conflict remains after evidence recovery.",
            "Resolve the identified authoritative conflict.",
        ),
        (
            "no_truly_unanswered_human_question",
            context.no_truly_unanswered_human_question,
            SupervisorGate.HOLD,
            "A material Human Seat question is proved truly unanswered.",
            "Answer the single proved Human Seat question recorded in the evidence.",
        ),
    )
    failed_human_conditions = tuple(
        condition
        for condition in human_conditions
        if condition[1] == ContractFact.NOT_SATISFIED
    )
    if failed_human_conditions:
        failed_blocks = tuple(
            condition
            for condition in failed_human_conditions
            if condition[2] == SupervisorGate.BLOCK
        )
        primary = (
            failed_blocks[0]
            if failed_blocks
            else failed_human_conditions[0]
        )
        _name, _fact, gate, reason, human_return = primary
        if len(failed_human_conditions) > 1:
            failed_names = ", ".join(
                condition[0] for condition in failed_human_conditions
            )
            reason = (
                f"{reason} Simultaneous failed Human Seat conditions: "
                f"{failed_names}."
            )
        return _judgment(
            result,
            context,
            gate=gate,
            reason=reason,
            route=DecisionRoute.HUMAN_SEAT,
            human_return=(
                human_return
                if failed_blocks and len(failed_human_conditions) > 1
                else _human_return(context, human_return)
            ),
        )

    if context.next_bounded_action is None:
        return _judgment(
            result,
            context,
            gate=SupervisorGate.HOLD,
            reason=(
                "The remaining gap is established, but one bounded next action "
                "has not yet been derived."
            ),
            route=DecisionRoute.AI_OWNED,
            next_action=(
                "Derive one bounded next action from the unchanged Goal and "
                "established remaining gap."
            ),
        )

    return _judgment(
        result,
        context,
        gate=SupervisorGate.GO,
        reason=(
            "The Worker result is complete and every Human Seat return-contract "
            "invariant remains satisfied."
        ),
        route=DecisionRoute.AI_OWNED,
        next_action=context.next_bounded_action.strip(),
    )


__all__ = [
    "ContractFact",
    "DecisionRoute",
    "FIRST_LIVE_MAX_RUNS",
    "SupervisorContext",
    "SupervisorGate",
    "SupervisorJudgment",
    "judge_continuation",
]
