"""Stage C hard-capped three-Run extension of the Stage B causal record."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping

from decision_os.acceleration.model import canonical_json, hash_payload
from decision_os.companion.continuation import (
    ContinuationIntegrityError,
    _bounded_strings,
    _bounded_text,
    _validate_run,
    _validate_supervisor,
)
from decision_os.companion.supervisor import (
    ContractFact,
    SupervisorContext,
)


STAGE_C_SCHEMA = "decision-os-stage-c-small-compound-loop-v0.1"
STAGE_C_TOTAL_RUN_CAP = 3
STAGE_C_AUTOMATIC_CONTINUATION_LIMIT = 2
STAGE_C_OUTCOMES = frozenset(
    {"COMPLETE", "HOLD", "CAP", "BLOCK", "HUMAN SEAT REQUIRED"}
)
_MAX_TASK_BYTES = 20_000
_STAGE_C_STATES = frozenset(
    {
        "RUN_1_ACTIVE",
        "RUN_1_COMPLETE",
        "RUN_2_ACTIVE",
        "RUN_2_COMPLETE",
        "RUN_3_ACTIVE",
        "RUN_3_COMPLETE",
        "TERMINAL",
    }
)
_REQUEST_FIELDS = frozenset(
    {
        "goal",
        "run_1_task",
        "completion_requirements",
        "evidence_recovery_action",
        "irreducible_human_decision",
        "authority_evidence_refs",
        "allowed_mutation_paths",
        "protected_objects",
        "max_runs",
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
_REQUIREMENT_FIELDS = frozenset(
    {"requirement_id", "description", "evidence_path", "expected_sha256"}
)
_RECORD_FIELDS = frozenset(
    {
        "schema",
        "chain_id",
        "repository_id",
        "state",
        "request",
        "runs",
        "residues",
        "supervisor_judgments",
        "automatic_tasks",
        "automatic_continuations_started",
        "automatic_continuation_limit",
        "total_run_cap",
        "outcome",
        "governed_stop",
        "record_sha256",
    }
)
_RESIDUE_FIELDS = frozenset(
    {
        "run_number",
        "source_run_id",
        "source_evidence_sha256",
        "established_requirement_ids",
        "new_requirement_ids",
        "remaining_requirement_ids",
        "residue_sha256",
    }
)
_TASK_FIELDS = frozenset(
    {
        "task_number",
        "source_run_number",
        "source_run_id",
        "source_evidence_sha256",
        "source_judgment_sha256",
        "goal_sha256",
        "selected_requirement_id",
        "selected_evidence_path",
        "selected_expected_sha256",
        "task",
        "task_sha256",
    }
)
_FACT_FIELDS = (
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


@dataclass(frozen=True)
class StageCCompletionRequirement:
    """One predeclared completion fact, not a prewritten Worker task."""

    requirement_id: str
    description: str
    evidence_path: str
    expected_sha256: str

    def __post_init__(self) -> None:
        _bounded_text(
            self.requirement_id,
            "Completion requirement ID",
            maximum=128,
        )
        _bounded_text(
            self.description,
            "Completion requirement description",
            maximum=2_000,
        )
        _bounded_text(
            self.evidence_path,
            "Completion evidence path",
            maximum=2_000,
        )
        if (
            not isinstance(self.expected_sha256, str)
            or len(self.expected_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.expected_sha256
            )
        ):
            raise ValueError(
                "Completion requirement SHA-256 must be lowercase hexadecimal."
            )

    def as_dict(self) -> dict[str, str]:
        return {
            "requirement_id": self.requirement_id.strip(),
            "description": self.description.strip(),
            "evidence_path": self.evidence_path.strip(),
            "expected_sha256": self.expected_sha256,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "StageCCompletionRequirement":
        if not isinstance(value, dict) or set(value) != _REQUIREMENT_FIELDS:
            raise ContinuationIntegrityError(
                "Persisted Stage C completion requirement is invalid."
            )
        try:
            return cls(**value)
        except (TypeError, ValueError) as exc:
            raise ContinuationIntegrityError(
                "Persisted Stage C completion requirement is invalid."
            ) from exc


@dataclass(frozen=True)
class StageCContinuationRequest:
    """One immutable Goal and authority envelope for a maximum of three Runs."""

    goal: str
    run_1_task: str
    completion_requirements: tuple[StageCCompletionRequirement, ...]
    evidence_recovery_action: str | None
    irreducible_human_decision: str | None
    authority_evidence_refs: tuple[str, ...]
    allowed_mutation_paths: tuple[str, ...]
    protected_objects: tuple[str, ...]
    max_runs: int
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
        _bounded_text(self.goal, "Goal", maximum=_MAX_TASK_BYTES)
        _bounded_text(self.run_1_task, "Run 1 task", maximum=_MAX_TASK_BYTES)
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
        if (
            not isinstance(self.completion_requirements, tuple)
            or not 1
            <= len(self.completion_requirements)
            <= STAGE_C_TOTAL_RUN_CAP
            or any(
                not isinstance(item, StageCCompletionRequirement)
                for item in self.completion_requirements
            )
        ):
            raise ValueError(
                "Stage C requires one to three completion requirements."
            )
        requirement_ids = tuple(
            item.requirement_id.strip() for item in self.completion_requirements
        )
        evidence_paths = tuple(
            item.evidence_path.strip() for item in self.completion_requirements
        )
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("Stage C completion requirement IDs must be unique.")
        if len(set(evidence_paths)) != len(evidence_paths):
            raise ValueError("Stage C completion evidence paths must be unique.")
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
            not isinstance(self.max_runs, int)
            or isinstance(self.max_runs, bool)
            or self.max_runs != STAGE_C_TOTAL_RUN_CAP
        ):
            raise ValueError("Stage C has one hard cap of three total Runs.")
        for name, fact in self.contract_facts():
            if not isinstance(fact, ContractFact):
                raise ValueError(f"{name} must be an explicit ContractFact.")

    def contract_facts(self) -> tuple[tuple[str, ContractFact], ...]:
        return tuple((name, getattr(self, name)) for name in _FACT_FIELDS)

    def as_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "goal": self.goal.strip(),
            "run_1_task": self.run_1_task.strip(),
            "completion_requirements": [
                item.as_dict() for item in self.completion_requirements
            ],
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
            "max_runs": self.max_runs,
        }
        value.update(
            {name: fact.value for name, fact in self.contract_facts()}
        )
        return value

    @classmethod
    def from_dict(cls, value: Any) -> "StageCContinuationRequest":
        if not isinstance(value, dict) or set(value) != _REQUEST_FIELDS:
            raise ContinuationIntegrityError(
                "Persisted Stage C authority fields are invalid."
            )
        for key in (
            "completion_requirements",
            "authority_evidence_refs",
            "allowed_mutation_paths",
            "protected_objects",
        ):
            if not isinstance(value[key], list):
                raise ContinuationIntegrityError(
                    "Persisted Stage C authority collections are invalid."
                )
        try:
            facts = {
                name: ContractFact(value[name]) for name in _FACT_FIELDS
            }
            return cls(
                goal=value["goal"],
                run_1_task=value["run_1_task"],
                completion_requirements=tuple(
                    StageCCompletionRequirement.from_dict(item)
                    for item in value["completion_requirements"]
                ),
                evidence_recovery_action=value["evidence_recovery_action"],
                irreducible_human_decision=value[
                    "irreducible_human_decision"
                ],
                authority_evidence_refs=tuple(
                    value["authority_evidence_refs"]
                ),
                allowed_mutation_paths=tuple(value["allowed_mutation_paths"]),
                protected_objects=tuple(value["protected_objects"]),
                max_runs=value["max_runs"],
                **facts,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ContinuationIntegrityError(
                "Persisted Stage C authority is invalid."
            ) from exc


def new_stage_c_record(
    request: StageCContinuationRequest,
    *,
    chain_id: str,
    repository_id: str,
) -> dict[str, Any]:
    return {
        "schema": STAGE_C_SCHEMA,
        "chain_id": chain_id,
        "repository_id": repository_id,
        "state": "RUN_1_ACTIVE",
        "request": request.as_dict(),
        "runs": [],
        "residues": [],
        "supervisor_judgments": [],
        "automatic_tasks": [],
        "automatic_continuations_started": 0,
        "automatic_continuation_limit": (
            STAGE_C_AUTOMATIC_CONTINUATION_LIMIT
        ),
        "total_run_cap": STAGE_C_TOTAL_RUN_CAP,
        "outcome": None,
        "governed_stop": None,
    }


def _requirements(record: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
    request = StageCContinuationRequest.from_dict(record.get("request"))
    return tuple(item.as_dict() for item in request.completion_requirements)


def satisfied_requirement_ids(
    record: Mapping[str, Any],
) -> tuple[str, ...]:
    requirements = _requirements(record)
    runs = record.get("runs")
    if not isinstance(runs, list):
        raise ContinuationIntegrityError("Stage C Run evidence is invalid.")
    satisfied: list[str] = []
    for requirement in requirements:
        matched = any(
            read.get("status") == "succeeded"
            and read.get("path") == requirement["evidence_path"]
            and read.get("sha256") == requirement["expected_sha256"]
            for run in runs
            if isinstance(run, dict)
            for read in run.get("read_evidence", [])
            if isinstance(read, dict)
        )
        if matched:
            satisfied.append(requirement["requirement_id"])
    return tuple(satisfied)


def remaining_requirements(
    record: Mapping[str, Any],
) -> tuple[dict[str, str], ...]:
    satisfied = set(satisfied_requirement_ids(record))
    return tuple(
        item
        for item in _requirements(record)
        if item["requirement_id"] not in satisfied
    )


def stage_c_residue(record: Mapping[str, Any]) -> dict[str, Any]:
    runs = record.get("runs")
    if not isinstance(runs, list) or not 1 <= len(runs) <= 3:
        raise ContinuationIntegrityError(
            "Stage C residue requires one to three persisted Runs."
        )
    established = satisfied_requirement_ids(record)
    previous_record = dict(record)
    previous_record["runs"] = runs[:-1]
    previous = set(satisfied_requirement_ids(previous_record))
    remaining = tuple(
        item["requirement_id"] for item in remaining_requirements(record)
    )
    payload: dict[str, Any] = {
        "run_number": len(runs),
        "source_run_id": runs[-1]["run_id"],
        "source_evidence_sha256": runs[-1]["evidence_sha256"],
        "established_requirement_ids": list(established),
        "new_requirement_ids": [
            item for item in established if item not in previous
        ],
        "remaining_requirement_ids": list(remaining),
    }
    payload["residue_sha256"] = hash_payload(payload)
    return payload


def _remaining_gap(record: Mapping[str, Any]) -> str:
    remaining = remaining_requirements(record)
    if not remaining:
        return "No completion requirement remains; the original Goal is complete."
    return "Unmet completion requirements: " + "; ".join(
        f"{item['requirement_id']} — {item['description']}"
        for item in remaining
    )


def _next_action(requirement: Mapping[str, str]) -> str:
    return (
        f"Establish completion requirement {requirement['requirement_id']} by "
        f"reading {requirement['evidence_path']} and verifying SHA-256 "
        f"{requirement['expected_sha256']}: {requirement['description']}"
    )


def stage_c_supervisor_context(
    record: Mapping[str, Any],
) -> SupervisorContext:
    request = StageCContinuationRequest.from_dict(record.get("request"))
    runs = record.get("runs")
    residues = record.get("residues")
    if (
        not isinstance(runs, list)
        or not 1 <= len(runs) <= STAGE_C_TOTAL_RUN_CAP
        or not isinstance(residues, list)
        or len(residues) != len(runs)
    ):
        raise ContinuationIntegrityError(
            "Stage C Supervisor requires the exact persisted current Run."
        )
    remaining = remaining_requirements(record)
    current = runs[-1]
    current_residue = residues[-1]
    made_progress = bool(current_residue["new_requirement_ids"])
    evidence_ref = (
        f"stage-c:{record['chain_id']}:run-{len(runs)}:"
        f"evidence-sha256={current['evidence_sha256']}"
    )
    return SupervisorContext(
        goal=request.goal,
        established_state=(
            f"Run {len(runs)} {current['run_id']} is persisted as "
            f"{current['status']} with evidence SHA-256 "
            f"{current['evidence_sha256']}. Cumulative residue: "
            f"{canonical_json(residues[-1])}"
        ),
        remaining_gap=_remaining_gap(record),
        next_bounded_action=(
            None if not remaining else _next_action(remaining[0])
        ),
        evidence_recovery_action=request.evidence_recovery_action,
        irreducible_human_decision=request.irreducible_human_decision,
        evidence_refs=(*request.authority_evidence_refs, evidence_ref),
        completed_runs=len(runs),
        max_runs=STAGE_C_TOTAL_RUN_CAP,
        goal_complete=(
            ContractFact.SATISFIED
            if not remaining
            else ContractFact.NOT_SATISFIED
        ),
        continuation_proof_sufficient=ContractFact.SATISFIED,
        evidence_sufficient=(
            ContractFact.SATISFIED
            if (
                made_progress
                or not remaining
                or len(runs) >= STAGE_C_TOTAL_RUN_CAP
            )
            else ContractFact.NOT_SATISFIED
        ),
        **{name: fact for name, fact in request.contract_facts()},
    )


def stage_c_automatic_task(record: Mapping[str, Any]) -> dict[str, Any]:
    request = StageCContinuationRequest.from_dict(record.get("request"))
    runs = record.get("runs")
    residues = record.get("residues")
    judgments = record.get("supervisor_judgments")
    if (
        record.get("state")
        not in {"RUN_1_COMPLETE", "RUN_2_COMPLETE"}
        or not isinstance(runs, list)
        or len(runs) not in {1, 2}
        or not isinstance(residues, list)
        or len(residues) != len(runs)
        or not isinstance(judgments, list)
        or len(judgments) != len(runs)
        or judgments[-1].get("gate") != "GO"
        or judgments[-1].get("decision_route") != "AI-OWNED"
    ):
        raise ContinuationIntegrityError(
            "The next Stage C Task lacks an exact persisted Supervisor GO chain."
        )
    remaining = remaining_requirements(record)
    if not remaining:
        raise ContinuationIntegrityError(
            "A completed Stage C Goal cannot construct another Task."
        )
    source = runs[-1]
    judgment = judgments[-1]
    selected = remaining[0]
    task_number = len(runs) + 1
    causal_evidence = {
        "run_id": source["run_id"],
        "status": source["status"],
        "evidence_sha256": source["evidence_sha256"],
        "read_evidence": source["read_evidence"],
        "receipt_delta": source["receipt_delta"],
        "residue": residues[-1],
        "supervisor_judgment": judgment,
    }
    task = "\n".join(
        (
            (
                f"STAGE C CAUSAL AUTOMATIC CONTINUATION — RUN {task_number} "
                f"OF HARD MAXIMUM {STAGE_C_TOTAL_RUN_CAP}"
            ),
            "",
            "Original user Goal:",
            request.goal,
            "",
            f"Persisted Run {len(runs)} causal evidence:",
            canonical_json(causal_evidence),
            "",
            "Current remaining gap derived after the preceding Run:",
            _remaining_gap(record),
            "",
            "Execute exactly this newly selected unmet completion requirement:",
            canonical_json(selected),
            "",
            "Derived bounded action:",
            _next_action(selected),
            "",
            "Allowed mutation path (no expansion):",
            request.allowed_mutation_paths[0],
            "",
            "Protected Objects / ownership boundaries (unchanged):",
            canonical_json(list(request.protected_objects)),
            "",
            (
                "Preserve the same Goal, authority, evidence continuity, blast "
                "radius, Human Seat contract, and three-Run total cap. Read only "
                "the selected evidence needed for this requirement. Do not "
                "publish, release, widen scope, or construct any later Task. "
                "Only the controller may supervise this result and decide "
                "whether another Run is admissible. Run 4 is forbidden."
            ),
        )
    )
    if len(task.encode("utf-8")) > _MAX_TASK_BYTES:
        raise ContinuationIntegrityError(
            "The causally constructed Stage C Task exceeds its bounded limit."
        )
    return {
        "task_number": task_number,
        "source_run_number": len(runs),
        "source_run_id": source["run_id"],
        "source_evidence_sha256": source["evidence_sha256"],
        "source_judgment_sha256": hash_payload(judgment),
        "goal_sha256": hashlib.sha256(
            request.goal.encode("utf-8")
        ).hexdigest(),
        "selected_requirement_id": selected["requirement_id"],
        "selected_evidence_path": selected["evidence_path"],
        "selected_expected_sha256": selected["expected_sha256"],
        "task": task,
        "task_sha256": hashlib.sha256(task.encode("utf-8")).hexdigest(),
    }


def stage_c_outcome(
    record: Mapping[str, Any],
    judgment: Mapping[str, Any],
) -> str:
    if not remaining_requirements(record):
        return "COMPLETE"
    if judgment.get("gate") == "CAP":
        return "CAP"
    if judgment.get("decision_route") == "HUMAN-SEAT":
        return "HUMAN SEAT REQUIRED"
    if judgment.get("gate") == "BLOCK":
        return "BLOCK"
    return "HOLD"


def _validate_residue(value: Any, expected: Mapping[str, Any]) -> None:
    if not isinstance(value, dict) or set(value) != _RESIDUE_FIELDS:
        raise ContinuationIntegrityError("Persisted Stage C residue is invalid.")
    if value != expected:
        raise ContinuationIntegrityError(
            "Persisted Stage C residue does not match accumulated Run evidence."
        )


def _validate_task(value: Any, expected: Mapping[str, Any]) -> None:
    if not isinstance(value, dict) or set(value) != _TASK_FIELDS:
        raise ContinuationIntegrityError(
            "Persisted Stage C automatic Task is invalid."
        )
    if value != expected:
        raise ContinuationIntegrityError(
            "Persisted Stage C Task is not the deterministic prior-Run derivation."
        )


def _validate_stop(value: Any) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"gate", "route", "reason", "next_action"}
        or any(not isinstance(item, str) or not item for item in value.values())
    ):
        raise ContinuationIntegrityError(
            "Persisted Stage C governed stop is invalid."
        )


def _validate_state_shape(value: Mapping[str, Any]) -> None:
    state = value["state"]
    runs = value["runs"]
    residues = value["residues"]
    judgments = value["supervisor_judgments"]
    tasks = value["automatic_tasks"]
    started = value["automatic_continuations_started"]
    outcome = value["outcome"]
    stop = value["governed_stop"]
    if state != "TERMINAL" and (outcome is not None or stop is not None):
        raise ContinuationIntegrityError(
            "Active Stage C state contains a terminal outcome."
        )
    active_shapes = {
        "RUN_1_ACTIVE": (0, 0, 0, 0),
        "RUN_2_ACTIVE": (1, 1, 1, 1),
        "RUN_3_ACTIVE": (2, 2, 2, 2),
    }
    if state in active_shapes:
        run_count, judgment_count, task_count, continuation_count = (
            active_shapes[state]
        )
        if (
            len(runs) != run_count
            or len(residues) != run_count
            or len(judgments) != judgment_count
            or len(tasks) != task_count
            or started != continuation_count
        ):
            raise ContinuationIntegrityError(
                "Active Stage C Run state is causally invalid."
            )
        if judgments and (
            judgments[-1]["gate"] != "GO"
            or judgments[-1]["decision_route"] != "AI-OWNED"
        ):
            raise ContinuationIntegrityError(
                "Active Stage C continuation lacks Supervisor GO."
            )
        return
    complete_shapes = {
        "RUN_1_COMPLETE": (1, 0),
        "RUN_2_COMPLETE": (2, 1),
        "RUN_3_COMPLETE": (3, 2),
    }
    if state in complete_shapes:
        run_count, task_count = complete_shapes[state]
        if (
            len(runs) != run_count
            or len(residues) != run_count
            or len(tasks) != task_count
            or started != task_count
            or len(judgments) not in {run_count - 1, run_count}
        ):
            raise ContinuationIntegrityError(
                "Completed Stage C Run state is causally invalid."
            )
        return
    if state != "TERMINAL":
        raise ContinuationIntegrityError("Persisted Stage C state is invalid.")
    if outcome not in STAGE_C_OUTCOMES:
        raise ContinuationIntegrityError(
            "Terminal Stage C outcome is invalid."
        )
    _validate_stop(stop)
    dispatched_runs = 1 + started
    if (
        len(tasks) != started
        or len(residues) != len(runs)
        or len(runs) not in {dispatched_runs - 1, dispatched_runs}
        or len(judgments) not in {max(0, len(runs) - 1), len(runs)}
    ):
        raise ContinuationIntegrityError(
            "Terminal Stage C causal counts are invalid."
        )
    remaining = remaining_requirements(value)
    if outcome == "COMPLETE" and (
        remaining
        or len(runs) != dispatched_runs
        or len(judgments) != len(runs)
    ):
        raise ContinuationIntegrityError(
            "Completed Stage C outcome lacks complete evidence."
        )
    if outcome == "CAP" and (
        not remaining
        or len(judgments) != len(runs)
        or judgments[-1]["gate"] != "CAP"
        or stop["gate"] != "CAP"
    ):
        raise ContinuationIntegrityError("Stage C cap outcome is invalid.")
    if outcome == "HUMAN SEAT REQUIRED" and (
        not judgments
        or judgments[-1]["decision_route"] != "HUMAN-SEAT"
        or stop["route"] != "HUMAN-SEAT"
    ):
        raise ContinuationIntegrityError(
            "Stage C Human Seat outcome is invalid."
        )
    if outcome == "HUMAN SEAT REQUIRED" and judgments[-1]["gate"] == "CAP":
        raise ContinuationIntegrityError(
            "A Stage C CAP judgment cannot be relabeled as Human Seat required."
        )
    if outcome == "BLOCK" and (
        stop["gate"] != "BLOCK" or stop["route"] == "HUMAN-SEAT"
    ):
        raise ContinuationIntegrityError(
            "Stage C BLOCK outcome lacks its exact governed gate."
        )
    if outcome == "HOLD" and stop["gate"] != "HOLD":
        raise ContinuationIntegrityError(
            "Stage C HOLD outcome lacks its exact governed gate."
        )
    if outcome == "COMPLETE" and stop["route"] != "STOP":
        raise ContinuationIntegrityError(
            "Stage C completion lacks its exact governed stop."
        )


def validate_stage_c_record(value: Any, *, maximum_bytes: int) -> None:
    """Validate one complete or reconnectable Stage C causal record."""

    if not isinstance(value, dict) or set(value) != _RECORD_FIELDS:
        raise ContinuationIntegrityError("Persisted Stage C fields are invalid.")
    if value["schema"] != STAGE_C_SCHEMA or value["state"] not in _STAGE_C_STATES:
        raise ContinuationIntegrityError(
            "Persisted Stage C schema or state is invalid."
        )
    if (
        not isinstance(value["chain_id"], str)
        or len(value["chain_id"]) != 32
        or any(
            character not in "0123456789abcdef"
            for character in value["chain_id"]
        )
        or not isinstance(value["repository_id"], str)
        or not value["repository_id"].startswith("repo:v1:")
    ):
        raise ContinuationIntegrityError("Persisted Stage C identity is invalid.")
    StageCContinuationRequest.from_dict(value["request"])
    runs = value["runs"]
    residues = value["residues"]
    judgments = value["supervisor_judgments"]
    tasks = value["automatic_tasks"]
    if (
        not isinstance(runs, list)
        or len(runs) > STAGE_C_TOTAL_RUN_CAP
        or not isinstance(residues, list)
        or len(residues) > len(runs)
        or not isinstance(judgments, list)
        or len(judgments) > len(runs)
        or not isinstance(tasks, list)
        or len(tasks) > STAGE_C_AUTOMATIC_CONTINUATION_LIMIT
    ):
        raise ContinuationIntegrityError(
            "Persisted Stage C causal collections are invalid."
        )
    for index, run in enumerate(runs, start=1):
        _validate_run(run, index)
    for index, residue in enumerate(residues, start=1):
        prefix = dict(value)
        prefix["runs"] = runs[:index]
        _validate_residue(residue, stage_c_residue(prefix))
    for index, judgment in enumerate(judgments):
        _validate_supervisor(judgment, runs[index])
        evidence_ref = (
            f"stage-c:{value['chain_id']}:run-{index + 1}:"
            f"evidence-sha256={runs[index]['evidence_sha256']}"
        )
        if evidence_ref not in judgment["evidence_refs"]:
            raise ContinuationIntegrityError(
                "Stage C Supervisor judgment lacks current Run provenance."
            )
    started = value["automatic_continuations_started"]
    if (
        not isinstance(started, int)
        or isinstance(started, bool)
        or started not in {0, 1, 2}
        or value["automatic_continuation_limit"]
        != STAGE_C_AUTOMATIC_CONTINUATION_LIMIT
        or value["total_run_cap"] != STAGE_C_TOTAL_RUN_CAP
        or started != len(tasks)
    ):
        raise ContinuationIntegrityError(
            "Persisted Stage C Run cap or continuation count is invalid."
        )
    for index, task in enumerate(tasks, start=1):
        prefix = dict(value)
        prefix["runs"] = runs[:index]
        prefix["residues"] = residues[:index]
        prefix["supervisor_judgments"] = judgments[:index]
        prefix["state"] = f"RUN_{index}_COMPLETE"
        _validate_task(task, stage_c_automatic_task(prefix))
    _validate_state_shape(value)
    claimed_hash = value["record_sha256"]
    if not isinstance(claimed_hash, str) or len(claimed_hash) != 64:
        raise ContinuationIntegrityError(
            "Persisted Stage C record hash is invalid."
        )
    payload = {
        key: item for key, item in value.items() if key != "record_sha256"
    }
    if claimed_hash != hash_payload(payload):
        raise ContinuationIntegrityError(
            "Persisted Stage C record hash mismatches."
        )
    if len(canonical_json(value).encode("utf-8")) > maximum_bytes:
        raise ContinuationIntegrityError("Persisted Stage C record is too large.")


__all__ = [
    "STAGE_C_AUTOMATIC_CONTINUATION_LIMIT",
    "STAGE_C_OUTCOMES",
    "STAGE_C_SCHEMA",
    "STAGE_C_TOTAL_RUN_CAP",
    "StageCCompletionRequirement",
    "StageCContinuationRequest",
    "new_stage_c_record",
    "remaining_requirements",
    "satisfied_requirement_ids",
    "stage_c_automatic_task",
    "stage_c_outcome",
    "stage_c_residue",
    "stage_c_supervisor_context",
    "validate_stage_c_record",
]
