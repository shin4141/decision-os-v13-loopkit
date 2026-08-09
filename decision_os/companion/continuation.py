"""Stage B persisted, exactly-once automatic continuation contract."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import secrets
from typing import Any, Mapping

from decision_os.acceleration.codex_adapter import CodexRunResult
from decision_os.acceleration.model import canonical_json, hash_payload
from decision_os.companion.supervisor import (
    ContractFact,
    FIRST_LIVE_MAX_RUNS,
    SupervisorContext,
)


STAGE_B_SCHEMA = "decision-os-stage-b-continuation-v0.1"
STAGE_B_AUTOMATIC_CONTINUATION_LIMIT = 1
_MAX_RECORD_BYTES = 256 * 1024
_MAX_TASK_BYTES = 20_000
_RECORD_STATES = frozenset(
    {
        "RUN_1_ACTIVE",
        "RUN_1_COMPLETE",
        "RUN_2_ACTIVE",
        "COMPLETE",
        "STOPPED",
        "BLOCKED",
    }
)
_REQUEST_FIELDS = frozenset(
    {
        "goal",
        "run_1_task",
        "remaining_gap_after_run_1",
        "next_bounded_action",
        "evidence_recovery_action",
        "irreducible_human_decision",
        "authority_evidence_refs",
        "allowed_mutation_paths",
        "protected_objects",
        "completed_runs_before",
        "max_runs",
        "goal_complete_after_run_1",
        "goal_unchanged",
        "authority_sufficient",
        "blast_radius_bounded",
        "action_reversible_or_authorized",
        "no_material_human_preference_required",
        "no_external_or_irreversible_commitment",
        "cost_boundary_intact",
        "protected_object_and_ownership_unchanged",
        "no_authoritative_conflict",
        "no_truly_unanswered_human_question",
    }
)
_RECORD_FIELDS = frozenset(
    {
        "schema",
        "chain_id",
        "repository_id",
        "state",
        "request",
        "runs",
        "supervisor",
        "automatic_task",
        "automatic_continuations_started",
        "automatic_continuation_limit",
        "governed_stop",
        "record_sha256",
    }
)
_RUN_FIELDS = frozenset(
    {
        "run_number",
        "run_id",
        "status",
        "normal_terminal",
        "turn_status",
        "error_type",
        "unsupported_reason",
        "runtime_identity",
        "checkpoint_outcomes",
        "file_actions",
        "read_evidence",
        "receipt_delta",
        "final_message_bytes",
        "final_message_sha256",
        "evidence_sha256",
    }
)
_SUPERVISOR_FIELDS = frozenset(
    {
        "schema",
        "role",
        "consumed_run",
        "gate",
        "reason",
        "established_state",
        "remaining_gap",
        "decision_route",
        "next_bounded_action",
        "human_seat_return",
        "evidence_refs",
        "automatic_second_run_started",
    }
)


class ContinuationError(RuntimeError):
    """A Stage B request or transition cannot be executed safely."""


class ContinuationIntegrityError(ContinuationError):
    """Persisted Stage B state is missing, corrupt, or causally mismatched."""


def _bounded_text(
    value: Any,
    label: str,
    *,
    maximum: int,
    optional: bool = False,
) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a bounded non-empty string.")
    if len(value.encode("utf-8")) > maximum:
        raise ValueError(f"{label} exceeds its bounded size limit.")
    return value.strip()


def _bounded_strings(
    values: Any,
    label: str,
    *,
    minimum: int = 1,
    maximum: int = 16,
) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not minimum <= len(values) <= maximum:
        raise ValueError(f"{label} must contain {minimum} to {maximum} entries.")
    normalized: list[str] = []
    for value in values:
        item = _bounded_text(value, label, maximum=2_000)
        assert item is not None
        normalized.append(item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} cannot contain duplicate entries.")
    return tuple(normalized)


@dataclass(frozen=True)
class StageBContinuationRequest:
    """One pre-Run authority envelope for exactly one possible continuation."""

    goal: str
    run_1_task: str
    remaining_gap_after_run_1: str
    next_bounded_action: str
    evidence_recovery_action: str | None
    irreducible_human_decision: str | None
    authority_evidence_refs: tuple[str, ...]
    allowed_mutation_paths: tuple[str, ...]
    protected_objects: tuple[str, ...]
    completed_runs_before: int
    max_runs: int
    goal_complete_after_run_1: ContractFact
    goal_unchanged: ContractFact
    authority_sufficient: ContractFact
    blast_radius_bounded: ContractFact
    action_reversible_or_authorized: ContractFact
    no_material_human_preference_required: ContractFact
    no_external_or_irreversible_commitment: ContractFact
    cost_boundary_intact: ContractFact
    protected_object_and_ownership_unchanged: ContractFact
    no_authoritative_conflict: ContractFact
    no_truly_unanswered_human_question: ContractFact

    def __post_init__(self) -> None:
        for label, value, maximum in (
            ("Goal", self.goal, _MAX_TASK_BYTES),
            ("Run 1 task", self.run_1_task, _MAX_TASK_BYTES),
            ("Remaining gap", self.remaining_gap_after_run_1, 8_000),
            ("Next bounded action", self.next_bounded_action, 8_000),
        ):
            _bounded_text(value, label, maximum=maximum)
        _bounded_text(
            self.evidence_recovery_action,
            "Evidence recovery action",
            maximum=8_000,
            optional=True,
        )
        _bounded_text(
            self.irreducible_human_decision,
            "Irreducible Human Seat decision",
            maximum=8_000,
            optional=True,
        )
        _bounded_strings(
            self.authority_evidence_refs,
            "Authority evidence references",
        )
        _bounded_strings(
            self.allowed_mutation_paths,
            "Allowed mutation paths",
            maximum=1,
        )
        _bounded_strings(
            self.protected_objects,
            "Protected Objects",
            maximum=8,
        )
        if (
            not isinstance(self.completed_runs_before, int)
            or isinstance(self.completed_runs_before, bool)
            or self.completed_runs_before < 0
        ):
            raise ValueError("Completed Runs before Stage B must be non-negative.")
        if (
            not isinstance(self.max_runs, int)
            or isinstance(self.max_runs, bool)
            or not 1 <= self.max_runs <= FIRST_LIVE_MAX_RUNS
        ):
            raise ValueError("The authorized total Run cap must be between 1 and 3.")
        if self.completed_runs_before >= self.max_runs:
            raise ValueError("The Run cap leaves no authority for Worker Run 1.")
        for name, fact in self.contract_facts():
            if not isinstance(fact, ContractFact):
                raise ValueError(f"{name} must be an explicit ContractFact.")

    def contract_facts(self) -> tuple[tuple[str, ContractFact], ...]:
        return (
            ("goal_complete_after_run_1", self.goal_complete_after_run_1),
            ("goal_unchanged", self.goal_unchanged),
            ("authority_sufficient", self.authority_sufficient),
            ("blast_radius_bounded", self.blast_radius_bounded),
            (
                "action_reversible_or_authorized",
                self.action_reversible_or_authorized,
            ),
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

    def as_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "goal": self.goal.strip(),
            "run_1_task": self.run_1_task.strip(),
            "remaining_gap_after_run_1": self.remaining_gap_after_run_1.strip(),
            "next_bounded_action": self.next_bounded_action.strip(),
            "evidence_recovery_action": (
                None
                if self.evidence_recovery_action is None
                else self.evidence_recovery_action.strip()
            ),
            "irreducible_human_decision": (
                None
                if self.irreducible_human_decision is None
                else self.irreducible_human_decision.strip()
            ),
            "authority_evidence_refs": list(self.authority_evidence_refs),
            "allowed_mutation_paths": list(self.allowed_mutation_paths),
            "protected_objects": list(self.protected_objects),
            "completed_runs_before": self.completed_runs_before,
            "max_runs": self.max_runs,
        }
        value.update(
            {name: fact.value for name, fact in self.contract_facts()}
        )
        return value

    @classmethod
    def from_dict(cls, value: Any) -> "StageBContinuationRequest":
        if not isinstance(value, dict) or set(value) != _REQUEST_FIELDS:
            raise ContinuationIntegrityError(
                "Persisted Stage B authority fields are invalid."
            )
        if any(
            not isinstance(value[key], list)
            for key in (
                "authority_evidence_refs",
                "allowed_mutation_paths",
                "protected_objects",
            )
        ):
            raise ContinuationIntegrityError(
                "Persisted Stage B authority collections are invalid."
            )
        try:
            facts = {
                name: ContractFact(value[name])
                for name in (
                    "goal_complete_after_run_1",
                    "goal_unchanged",
                    "authority_sufficient",
                    "blast_radius_bounded",
                    "action_reversible_or_authorized",
                    "no_material_human_preference_required",
                    "no_external_or_irreversible_commitment",
                    "cost_boundary_intact",
                    "protected_object_and_ownership_unchanged",
                    "no_authoritative_conflict",
                    "no_truly_unanswered_human_question",
                )
            }
            return cls(
                goal=value["goal"],
                run_1_task=value["run_1_task"],
                remaining_gap_after_run_1=value[
                    "remaining_gap_after_run_1"
                ],
                next_bounded_action=value["next_bounded_action"],
                evidence_recovery_action=value["evidence_recovery_action"],
                irreducible_human_decision=value[
                    "irreducible_human_decision"
                ],
                authority_evidence_refs=tuple(
                    value["authority_evidence_refs"]
                ),
                allowed_mutation_paths=tuple(value["allowed_mutation_paths"]),
                protected_objects=tuple(value["protected_objects"]),
                completed_runs_before=value["completed_runs_before"],
                max_runs=value["max_runs"],
                **facts,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ContinuationIntegrityError(
                "Persisted Stage B authority is invalid."
            ) from exc


def result_evidence(
    result: CodexRunResult,
    *,
    run_number: int,
    receipt_delta: Mapping[str, Any],
) -> dict[str, Any]:
    identity = result.runtime_identity
    payload: dict[str, Any] = {
        "run_number": run_number,
        "run_id": result.run_id,
        "status": result.status,
        "normal_terminal": result.normal_terminal,
        "turn_status": result.turn_status,
        "error_type": result.error_type,
        "unsupported_reason": result.unsupported_reason,
        "runtime_identity": (
            None
            if identity is None
            else {
                "model": identity.model,
                "reasoning_effort": identity.reasoning_effort,
                "service_tier": identity.service_tier,
                "codex_cli_version": identity.codex_cli_version,
                "account_type": identity.account_type,
            }
        ),
        "checkpoint_outcomes": [
            {
                "status": item.status,
                "verified": item.verified,
                "event_hash": item.event_hash,
            }
            for item in result.checkpoint_outcomes
        ],
        "file_actions": [
            {
                "action": item.action,
                "path": item.normalized_scope,
                "access": item.access,
                "status": item.status,
            }
            for item in result.file_actions
        ],
        "read_evidence": [
            {
                "path": item.path,
                "bytes": item.byte_count,
                "sha256": item.sha256,
                "repository_identity": item.repository_identity,
                "status": item.status,
                "reason": item.reason,
            }
            for item in result.read_evidence
        ],
        "receipt_delta": dict(receipt_delta),
        "final_message_bytes": len(result.final_message.encode("utf-8")),
        "final_message_sha256": hashlib.sha256(
            result.final_message.encode("utf-8")
        ).hexdigest(),
    }
    payload["evidence_sha256"] = hash_payload(payload)
    return payload


def supervisor_context_from_persisted_run(
    record: Mapping[str, Any],
) -> SupervisorContext:
    request = StageBContinuationRequest.from_dict(record["request"])
    runs = record.get("runs")
    if not isinstance(runs, list) or len(runs) != 1:
        raise ContinuationIntegrityError(
            "Stage B requires exactly one persisted Run 1 result before judgment."
        )
    run = runs[0]
    evidence_ref = (
        f"stage-b:{record['chain_id']}:run-1:"
        f"evidence-sha256={run['evidence_sha256']}"
    )
    return SupervisorContext(
        goal=request.goal,
        established_state=(
            f"Run 1 {run['run_id']} is persisted as {run['status']} with "
            f"evidence SHA-256 {run['evidence_sha256']}."
        ),
        remaining_gap=request.remaining_gap_after_run_1,
        next_bounded_action=request.next_bounded_action,
        evidence_recovery_action=request.evidence_recovery_action,
        irreducible_human_decision=request.irreducible_human_decision,
        evidence_refs=(*request.authority_evidence_refs, evidence_ref),
        completed_runs=request.completed_runs_before + 1,
        max_runs=request.max_runs,
        goal_complete=request.goal_complete_after_run_1,
        continuation_proof_sufficient=ContractFact.SATISFIED,
        goal_unchanged=request.goal_unchanged,
        authority_sufficient=request.authority_sufficient,
        blast_radius_bounded=request.blast_radius_bounded,
        action_reversible_or_authorized=(
            request.action_reversible_or_authorized
        ),
        evidence_sufficient=ContractFact.SATISFIED,
        no_material_human_preference_required=(
            request.no_material_human_preference_required
        ),
        no_external_or_irreversible_commitment=(
            request.no_external_or_irreversible_commitment
        ),
        cost_boundary_intact=request.cost_boundary_intact,
        protected_object_and_ownership_unchanged=(
            request.protected_object_and_ownership_unchanged
        ),
        no_authoritative_conflict=request.no_authoritative_conflict,
        no_truly_unanswered_human_question=(
            request.no_truly_unanswered_human_question
        ),
    )


def automatic_task_from_persisted_run(record: Mapping[str, Any]) -> dict[str, str]:
    request = StageBContinuationRequest.from_dict(record.get("request"))
    runs = record.get("runs")
    supervisor = record.get("supervisor")
    consumed_run = (
        supervisor.get("consumed_run")
        if isinstance(supervisor, dict)
        else None
    )
    if (
        record.get("state") != "RUN_1_COMPLETE"
        or not isinstance(runs, list)
        or len(runs) != 1
        or not isinstance(supervisor, dict)
        or not isinstance(consumed_run, dict)
        or supervisor.get("gate") != "GO"
        or supervisor.get("decision_route") != "AI-OWNED"
        or consumed_run.get("run_id") != runs[0].get("run_id")
    ):
        raise ContinuationIntegrityError(
            "Task 2 cannot be derived without an exact persisted Run 1 GO chain."
        )
    causal_evidence = {
        "run_id": runs[0]["run_id"],
        "status": runs[0]["status"],
        "evidence_sha256": runs[0]["evidence_sha256"],
        "checkpoint_outcomes": runs[0]["checkpoint_outcomes"],
        "file_actions": runs[0]["file_actions"],
        "read_evidence": runs[0]["read_evidence"],
        "receipt_delta": runs[0]["receipt_delta"],
    }
    task = "\n".join(
        (
            "STAGE B AUTOMATIC CONTINUATION — RUN 2 OF 2 FOR THIS INVOCATION",
            "",
            "Original user Goal:",
            request.goal,
            "",
            "Persisted Run 1 causal evidence:",
            canonical_json(causal_evidence),
            "",
            "Established remaining gap:",
            request.remaining_gap_after_run_1,
            "",
            "Execute exactly this authorized next bounded action:",
            request.next_bounded_action,
            "",
            "Allowed mutation path (no expansion):",
            request.allowed_mutation_paths[0],
            "",
            "Protected Objects / ownership boundaries (unchanged):",
            canonical_json(list(request.protected_objects)),
            "",
            (
                "Preserve the same Goal, authority, evidence continuity, blast "
                "radius, and total Run cap. Do not publish, release, modify a "
                "Protected Object, request a new user task, or start/propose Run 3."
            ),
        )
    )
    if len(task.encode("utf-8")) > _MAX_TASK_BYTES:
        raise ContinuationIntegrityError(
            "The causally constructed Task 2 exceeds the bounded task limit."
        )
    return {
        "source_run_id": runs[0]["run_id"],
        "source_evidence_sha256": runs[0]["evidence_sha256"],
        "goal_sha256": hashlib.sha256(
            request.goal.encode("utf-8")
        ).hexdigest(),
        "task": task,
        "task_sha256": hashlib.sha256(task.encode("utf-8")).hexdigest(),
    }


def new_record(
    request: StageBContinuationRequest,
    *,
    chain_id: str,
    repository_id: str,
) -> dict[str, Any]:
    return {
        "schema": STAGE_B_SCHEMA,
        "chain_id": chain_id,
        "repository_id": repository_id,
        "state": "RUN_1_ACTIVE",
        "request": request.as_dict(),
        "runs": [],
        "supervisor": None,
        "automatic_task": None,
        "automatic_continuations_started": 0,
        "automatic_continuation_limit": STAGE_B_AUTOMATIC_CONTINUATION_LIMIT,
        "governed_stop": None,
    }


def governed_stop(
    *,
    gate: str,
    route: str,
    reason: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "gate": gate,
        "route": route,
        "reason": reason,
        "next_action": next_action,
    }


def _validate_run(value: Any, expected_number: int) -> None:
    if not isinstance(value, dict) or set(value) != _RUN_FIELDS:
        raise ContinuationIntegrityError("Persisted Worker Run evidence is invalid.")
    if value["run_number"] != expected_number:
        raise ContinuationIntegrityError("Persisted Worker Run order is invalid.")
    for key in ("run_id", "status", "final_message_sha256", "evidence_sha256"):
        if not isinstance(value[key], str) or not value[key]:
            raise ContinuationIntegrityError("Persisted Worker identity is invalid.")
    if len(value["final_message_sha256"]) != 64 or len(
        value["evidence_sha256"]
    ) != 64:
        raise ContinuationIntegrityError("Persisted Worker hashes are invalid.")
    if not isinstance(value["normal_terminal"], bool):
        raise ContinuationIntegrityError("Persisted terminal state is invalid.")
    if value["turn_status"] is not None and not isinstance(
        value["turn_status"],
        str,
    ):
        raise ContinuationIntegrityError("Persisted turn status is invalid.")
    for key in ("error_type", "unsupported_reason"):
        if value[key] is not None and not isinstance(value[key], str):
            raise ContinuationIntegrityError("Persisted Run error state is invalid.")
    if value["runtime_identity"] is not None and not isinstance(
        value["runtime_identity"],
        dict,
    ):
        raise ContinuationIntegrityError("Persisted runtime identity is invalid.")
    if any(
        not isinstance(value[key], list)
        for key in ("checkpoint_outcomes", "file_actions", "read_evidence")
    ) or not isinstance(value["receipt_delta"], dict):
        raise ContinuationIntegrityError("Persisted Run evidence shape is invalid.")
    if (
        not isinstance(value["final_message_bytes"], int)
        or isinstance(value["final_message_bytes"], bool)
        or value["final_message_bytes"] < 0
    ):
        raise ContinuationIntegrityError("Persisted message size is invalid.")
    payload = {key: item for key, item in value.items() if key != "evidence_sha256"}
    if value["evidence_sha256"] != hash_payload(payload):
        raise ContinuationIntegrityError("Persisted Worker evidence hash mismatches.")


def _validate_supervisor(value: Any, run_1: Mapping[str, Any]) -> None:
    if not isinstance(value, dict) or set(value) != _SUPERVISOR_FIELDS:
        raise ContinuationIntegrityError("Persisted Supervisor fields are invalid.")
    consumed = value["consumed_run"]
    if (
        value["schema"] != "decision-os-supervisor-judgment-v0.1"
        or value["role"] != "SUPERVISOR"
        or not isinstance(consumed, dict)
        or set(consumed) != {"run_id", "status"}
        or consumed["run_id"] != run_1["run_id"]
        or consumed["status"] != run_1["status"]
        or value["gate"] not in {"GO", "HOLD", "CAP", "BLOCK"}
        or value["decision_route"]
        not in {"AI-OWNED", "EVIDENCE-RECOVERY", "HUMAN-SEAT", "STOP"}
        or value["automatic_second_run_started"] is not False
    ):
        raise ContinuationIntegrityError("Persisted Supervisor identity is invalid.")
    for key in ("reason", "established_state", "remaining_gap"):
        if not isinstance(value[key], str) or not value[key]:
            raise ContinuationIntegrityError(
                "Persisted Supervisor narrative is invalid."
            )
    evidence_refs = value["evidence_refs"]
    if (
        not isinstance(evidence_refs, list)
        or not evidence_refs
        or any(not isinstance(item, str) or not item for item in evidence_refs)
    ):
        raise ContinuationIntegrityError("Persisted Supervisor evidence is invalid.")
    next_action = value["next_bounded_action"]
    human_return = value["human_seat_return"]
    if (next_action is None) == (human_return is None):
        raise ContinuationIntegrityError("Persisted Supervisor route is invalid.")
    if next_action is not None and (
        not isinstance(next_action, str) or not next_action
    ):
        raise ContinuationIntegrityError("Persisted Supervisor action is invalid.")
    if human_return is not None and (
        not isinstance(human_return, str) or not human_return
    ):
        raise ContinuationIntegrityError("Persisted Human Seat return is invalid.")
    if (value["decision_route"] == "HUMAN-SEAT") != (
        human_return is not None
    ):
        raise ContinuationIntegrityError(
            "Persisted Supervisor Human Seat route is invalid."
        )


def _validate_stage_b_record(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != _RECORD_FIELDS:
        raise ContinuationIntegrityError("Persisted Stage B fields are invalid.")
    if value["schema"] != STAGE_B_SCHEMA or value["state"] not in _RECORD_STATES:
        raise ContinuationIntegrityError("Persisted Stage B schema or state is invalid.")
    if (
        not isinstance(value["chain_id"], str)
        or len(value["chain_id"]) != 32
        or any(character not in "0123456789abcdef" for character in value["chain_id"])
        or not isinstance(value["repository_id"], str)
        or not value["repository_id"].startswith("repo:v1:")
    ):
        raise ContinuationIntegrityError("Persisted Stage B identity is invalid.")
    StageBContinuationRequest.from_dict(value["request"])
    runs = value["runs"]
    if not isinstance(runs, list) or len(runs) > 2:
        raise ContinuationIntegrityError("Stage B can persist at most two Runs.")
    for index, run in enumerate(runs, start=1):
        _validate_run(run, index)
    started = value["automatic_continuations_started"]
    if (
        not isinstance(started, int)
        or isinstance(started, bool)
        or started not in {0, 1}
        or value["automatic_continuation_limit"]
        != STAGE_B_AUTOMATIC_CONTINUATION_LIMIT
    ):
        raise ContinuationIntegrityError("Stage B continuation count is invalid.")
    task = value["automatic_task"]
    if task is not None:
        if not isinstance(task, dict) or set(task) != {
            "source_run_id",
            "source_evidence_sha256",
            "goal_sha256",
            "task",
            "task_sha256",
        }:
            raise ContinuationIntegrityError("Persisted automatic Task 2 is invalid.")
        if not runs or task["source_run_id"] != runs[0]["run_id"]:
            raise ContinuationIntegrityError("Task 2 source Run mismatches.")
        if any(
            not isinstance(task[key], str) or not task[key]
            for key in (
                "source_run_id",
                "source_evidence_sha256",
                "goal_sha256",
                "task",
                "task_sha256",
            )
        ):
            raise ContinuationIntegrityError("Persisted Task 2 values are invalid.")
        if task["source_evidence_sha256"] != runs[0]["evidence_sha256"]:
            raise ContinuationIntegrityError("Task 2 evidence source mismatches.")
        request = StageBContinuationRequest.from_dict(value["request"])
        if task["goal_sha256"] != hashlib.sha256(
            request.goal.encode("utf-8")
        ).hexdigest():
            raise ContinuationIntegrityError("Task 2 Goal identity mismatches.")
        if task["task_sha256"] != hashlib.sha256(
            task["task"].encode("utf-8")
        ).hexdigest():
            raise ContinuationIntegrityError("Task 2 content hash mismatches.")
    if started == 1 and task is None:
        raise ContinuationIntegrityError("Started Task 2 has no causal task record.")
    if len(runs) == 2 and started != 1:
        raise ContinuationIntegrityError("Run 2 lacks one continuation start.")
    if value["state"] in {"RUN_2_ACTIVE", "COMPLETE"} and started != 1:
        raise ContinuationIntegrityError("Stage B terminal state lacks Run 2 authority.")
    supervisor = value["supervisor"]
    if supervisor is not None:
        if not runs:
            raise ContinuationIntegrityError(
                "Persisted Supervisor has no consumed Run."
            )
        _validate_supervisor(supervisor, runs[0])
    stop = value["governed_stop"]
    if stop is not None and (
        not isinstance(stop, dict)
        or set(stop) != {"gate", "route", "reason", "next_action"}
        or any(not isinstance(item, str) or not item for item in stop.values())
    ):
        raise ContinuationIntegrityError("Persisted governed stop is invalid.")
    state = value["state"]
    if state == "RUN_1_ACTIVE" and (
        runs
        or supervisor is not None
        or task is not None
        or started
        or stop is not None
    ):
        raise ContinuationIntegrityError("Active Run 1 state is causally invalid.")
    if state == "RUN_1_COMPLETE" and (
        len(runs) != 1 or task is not None or started or stop is not None
    ):
        raise ContinuationIntegrityError("Completed Run 1 state is causally invalid.")
    if state == "RUN_2_ACTIVE" and (
        len(runs) != 1
        or supervisor is None
        or supervisor.get("gate") != "GO"
        or task is None
        or stop is not None
    ):
        raise ContinuationIntegrityError("Active Run 2 state is causally invalid.")
    if state == "COMPLETE" and (
        len(runs) != 2
        or supervisor is None
        or supervisor.get("gate") != "GO"
        or task is None
    ):
        raise ContinuationIntegrityError("Completed Stage B state is causally invalid.")
    if state in {"STOPPED", "BLOCKED"} and stop is None:
        raise ContinuationIntegrityError("Governed terminal state lacks its stop.")
    if task is not None:
        derivation_record = {
            "state": "RUN_1_COMPLETE",
            "chain_id": value["chain_id"],
            "request": value["request"],
            "runs": runs[:1],
            "supervisor": supervisor,
        }
        if task != automatic_task_from_persisted_run(derivation_record):
            raise ContinuationIntegrityError(
                "Persisted Task 2 is not the deterministic Run 1 derivation."
            )
    claimed_hash = value["record_sha256"]
    if not isinstance(claimed_hash, str) or len(claimed_hash) != 64:
        raise ContinuationIntegrityError("Persisted Stage B record hash is invalid.")
    payload = {key: item for key, item in value.items() if key != "record_sha256"}
    if claimed_hash != hash_payload(payload):
        raise ContinuationIntegrityError("Persisted Stage B record hash mismatches.")
    if len(canonical_json(value).encode("utf-8")) > _MAX_RECORD_BYTES:
        raise ContinuationIntegrityError("Persisted Stage B record is too large.")


def _validate_record(value: Any) -> None:
    if (
        isinstance(value, dict)
        and value.get("schema")
        == "decision-os-stage-c-small-compound-loop-v0.1"
    ):
        from decision_os.companion.small_compound_loop import (
            validate_stage_c_record,
        )

        validate_stage_c_record(value, maximum_bytes=_MAX_RECORD_BYTES)
        return
    _validate_stage_b_record(value)


class StageBContinuationStore:
    """One strict, atomic, hash-bound reconnectable continuation record."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        value = deepcopy(dict(payload))
        value.pop("record_sha256", None)
        value["record_sha256"] = hash_payload(value)
        _validate_record(value)
        encoded = (canonical_json(value) + "\n").encode("utf-8")
        directory = self.path.parent
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(directory, 0o700)
        temporary = directory / f".stage-b-{secrets.token_hex(8)}.tmp"
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(encoded)
            os.replace(temporary, self.path)
            os.chmod(self.path, 0o600)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return self.load_required()

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            raw = self.path.read_bytes()
            if len(raw) > _MAX_RECORD_BYTES:
                raise ContinuationIntegrityError(
                    "Persisted Stage B record is too large."
                )
            value = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ContinuationIntegrityError(
                "Persisted Stage B record is unreadable."
            ) from exc
        try:
            _validate_record(value)
        except ContinuationIntegrityError:
            raise
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ContinuationIntegrityError(
                "Persisted Stage B record structure is invalid."
            ) from exc
        return deepcopy(value)

    def load_required(self) -> dict[str, Any]:
        value = self.load()
        if value is None:
            raise ContinuationIntegrityError("Persisted Stage B record is absent.")
        return value

    def schema_hint(self) -> str | None:
        """Return only a bounded display hint; never grant authority from it."""

        try:
            raw = self.path.read_bytes()
            if len(raw) > _MAX_RECORD_BYTES:
                return None
            value = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        if not isinstance(value, dict):
            return None
        schema = value.get("schema")
        if schema in {
            STAGE_B_SCHEMA,
            "decision-os-stage-c-small-compound-loop-v0.1",
        }:
            return schema
        return None


__all__ = [
    "ContinuationError",
    "ContinuationIntegrityError",
    "STAGE_B_AUTOMATIC_CONTINUATION_LIMIT",
    "STAGE_B_SCHEMA",
    "StageBContinuationRequest",
    "StageBContinuationStore",
    "automatic_task_from_persisted_run",
    "governed_stop",
    "new_record",
    "result_evidence",
    "supervisor_context_from_persisted_run",
]
