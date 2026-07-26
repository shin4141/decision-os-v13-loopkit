"""Deterministic orchestration of intake, delivery, and continuity checks."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
import os
from pathlib import Path
import stat
from typing import Any
import unicodedata

from . import audit_delivery as audit_contract
from . import audit_link as link_contract
from . import intake as intake_contract


EXIT_READY = 0
EXIT_NOT_READY = 4

RESULT_SCHEMA_VERSION = "decision-os.audit-gate-result.v0.1"

RESULT_READY = "HUMAN_REVIEW_READY"
RESULT_NOT_READY = "NOT_READY"
RESULT_INVALID = "INVALID"
RESULT_NOT_RUN = "NOT_RUN"

CHECK_INTAKE = "intake_structure"
CHECK_DELIVERY = "delivery_structure"
CHECK_CONTINUITY = "incident_continuity"
CHECK_ORDER = (CHECK_INTAKE, CHECK_DELIVERY, CHECK_CONTINUITY)

CLAIMS_NOT_MADE = (
    "truth or completeness of either input",
    "factual correctness of the diagnosis",
    "efficacy or uniqueness of the repair",
    "client acceptance",
    "paid-delivery value or delivery authorization",
    "prevention or recovery",
    "software, workflow, security, or safety correctness",
    "productivity, labor, cost, or revenue improvement",
    "an atomic snapshot or one physical read of each input",
)

NEXT_STEP_READY = (
    "Begin bounded human review of factual correctness; do not treat structural "
    "eligibility as delivery acceptance."
)
NEXT_STEP_INTAKE = (
    "Add or correct only the listed intake structure, then rerun decision-os "
    "audit-gate."
)
NEXT_STEP_DELIVERY = (
    "Add or correct only the listed delivery structure, then rerun decision-os "
    "audit-gate."
)
NEXT_STEP_CONTINUITY = (
    "Copy the six accepted intake identity values into the corresponding Audit "
    "fields without paraphrasing, then rerun decision-os audit-gate."
)
NEXT_STEP_INVALID = (
    "Provide one local regular UTF-8 v0.1 intake JSON file and one local regular "
    "UTF-8 Audit Markdown file, then rerun decision-os audit-gate."
)

UNKNOWN_ORDER = (
    "input_identity_unavailable",
    "input_identity_changed",
    "cli_usage",
    "internal_failure",
)
_INTAKE_UNKNOWN_ORDER = (
    "input_unknowns_present",
    "packet_structure",
    "cli_usage",
    "internal_failure",
)
_AUDIT_SECTION_ORDER = (
    "Title",
    *audit_contract.REQUIRED_SECTIONS,
    "Required heading order",
    "Fenced code block",
)
_AUDIT_UNKNOWN_ORDER = (
    *audit_contract.DIAGNOSIS_DIMENSIONS,
    "Unknowns section",
    "cli_usage",
    "internal_failure",
)

_FileIdentity = tuple[int, ...] | None


def _safe_basename(path: Path | str | os.PathLike[str] | None) -> str:
    if path is None:
        return "unavailable"
    try:
        name = os.path.basename(os.path.abspath(os.fspath(path)))
    except (TypeError, ValueError, OSError):
        return "unavailable"
    if not name or name in (".", ".."):
        return "unavailable"
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in name
    ):
        return "unavailable"
    return name[:255]


def _sequence(value: Any) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return ()
    return value


def _ordered(value: Any, order: Sequence[str]) -> list[str]:
    selected = {
        item for item in _sequence(value) if isinstance(item, str) and item in order
    }
    return [item for item in order if item in selected]


def _contract_list(
    payload: Mapping[str, Any],
    key: str,
    order: Sequence[str],
) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise RuntimeError("component payload list shape is unavailable")
    projected = _ordered(value, order)
    if projected != value:
        raise RuntimeError("component payload list violated its public contract")
    return projected


def _require_component_base(
    payload: Mapping[str, Any],
    *,
    schema_version: str,
    command: str,
    claims_not_made: Sequence[str],
) -> None:
    if (
        payload.get("schema_version") != schema_version
        or payload.get("command") != command
        or payload.get("claims_not_made") != list(claims_not_made)
        or not isinstance(payload.get("minimum_next_step"), str)
    ):
        raise RuntimeError("component payload base contract is unavailable")


def _require_input_entry(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise RuntimeError("component input receipt is unavailable")
    if value.get("content_echoed") is not False or not isinstance(
        value.get("name"),
        str,
    ):
        raise RuntimeError("component input receipt violated its public contract")


def _not_run_intake() -> dict[str, Any]:
    return {
        "result": RESULT_NOT_RUN,
        "missing_fields": [],
        "invalid_fields": [],
        "unknowns": [],
    }


def _not_run_delivery() -> dict[str, Any]:
    return {
        "result": RESULT_NOT_RUN,
        "missing_sections": [],
        "invalid_sections": [],
        "missing_fields": [],
        "invalid_fields": [],
        "unknowns": [],
    }


def _not_run_continuity() -> dict[str, Any]:
    return {
        "result": RESULT_NOT_RUN,
        "matched_fields": [],
        "mismatched_fields": [],
        "missing_fields": [],
        "unknowns": [],
    }


def _validated_result(
    payload: Mapping[str, Any],
    exit_code: int,
    expected_exits: Mapping[str, int],
) -> str:
    if not isinstance(payload, Mapping):
        raise RuntimeError("component payload is not an object")
    result = payload.get("result")
    if (
        not isinstance(result, str)
        or result not in expected_exits
        or exit_code != expected_exits[result]
    ):
        raise RuntimeError("component result violated its public exit contract")
    return result


def _intake_summary(
    payload: Mapping[str, Any],
    exit_code: int,
) -> dict[str, Any]:
    _require_component_base(
        payload,
        schema_version=intake_contract.RESULT_SCHEMA_VERSION,
        command="intake",
        claims_not_made=intake_contract.CLAIMS_NOT_MADE,
    )
    _require_input_entry(payload.get("input"))
    result = _validated_result(
        payload,
        exit_code,
        {
            intake_contract.RESULT_READY: intake_contract.EXIT_READY,
            intake_contract.RESULT_INCOMPLETE: intake_contract.EXIT_INCOMPLETE,
            intake_contract.RESULT_INVALID: intake_contract.EXIT_INCOMPLETE,
        },
    )
    field_order = (*intake_contract.FIELD_ORDER, "unsupported_fields")
    observed = _contract_list(
        payload,
        "observed_fields",
        intake_contract.FIELD_ORDER,
    )
    missing = _contract_list(
        payload,
        "missing_required_fields",
        field_order,
    )
    invalid = _contract_list(payload, "invalid_fields", field_order)
    unknowns = _contract_list(
        payload,
        "unknowns",
        _INTAKE_UNKNOWN_ORDER,
    )
    expected_next_steps = {
        intake_contract.RESULT_READY: intake_contract.NEXT_STEP_READY,
        intake_contract.RESULT_INCOMPLETE: intake_contract.NEXT_STEP_INCOMPLETE,
        intake_contract.RESULT_INVALID: intake_contract.NEXT_STEP_INVALID,
    }
    if payload.get("minimum_next_step") != expected_next_steps[result]:
        raise RuntimeError("intake next-step contract is unavailable")
    if result == intake_contract.RESULT_READY and (
        missing
        or invalid
        or any(
            field not in observed
            for field in intake_contract.REQUIRED_FIELD_ORDER
        )
    ):
        raise RuntimeError("ready intake payload contains structural blockers")
    return {
        "result": result,
        "missing_fields": missing,
        "invalid_fields": invalid,
        "unknowns": unknowns,
    }


def _delivery_summary(
    payload: Mapping[str, Any],
    exit_code: int,
) -> dict[str, Any]:
    _require_component_base(
        payload,
        schema_version=audit_contract.RESULT_SCHEMA_VERSION,
        command="audit-check",
        claims_not_made=audit_contract.CLAIMS_NOT_MADE,
    )
    _require_input_entry(payload.get("input"))
    result = _validated_result(
        payload,
        exit_code,
        {
            audit_contract.RESULT_READY: audit_contract.EXIT_READY,
            audit_contract.RESULT_INCOMPLETE: audit_contract.EXIT_INCOMPLETE,
            audit_contract.RESULT_INVALID: audit_contract.EXIT_INCOMPLETE,
        },
    )
    observed_sections = _contract_list(
        payload,
        "observed_sections",
        audit_contract.REQUIRED_SECTIONS,
    )
    missing_sections = _contract_list(
        payload,
        "missing_required_sections",
        _AUDIT_SECTION_ORDER,
    )
    invalid_sections = _contract_list(
        payload,
        "invalid_sections",
        _AUDIT_SECTION_ORDER,
    )
    observed_fields = _contract_list(
        payload,
        "observed_fields",
        audit_contract.FIELD_ORDER,
    )
    missing_fields = _contract_list(
        payload,
        "missing_required_fields",
        audit_contract.FIELD_ORDER,
    )
    invalid_fields = _contract_list(
        payload,
        "invalid_fields",
        audit_contract.FIELD_ORDER,
    )
    unknowns = _contract_list(
        payload,
        "unknowns",
        _AUDIT_UNKNOWN_ORDER,
    )
    expected_next_steps = {
        audit_contract.RESULT_READY: audit_contract.NEXT_STEP_READY,
        audit_contract.RESULT_INCOMPLETE: audit_contract.NEXT_STEP_INCOMPLETE,
        audit_contract.RESULT_INVALID: audit_contract.NEXT_STEP_INVALID,
    }
    if payload.get("minimum_next_step") != expected_next_steps[result]:
        raise RuntimeError("delivery next-step contract is unavailable")
    if result == audit_contract.RESULT_READY and (
        payload.get("profile") != audit_contract.SUPPORTED_PROFILE
        or observed_sections != list(audit_contract.REQUIRED_SECTIONS)
        or observed_fields != list(audit_contract.FIELD_ORDER)
        or missing_sections
        or invalid_sections
        or missing_fields
        or invalid_fields
    ):
        raise RuntimeError("ready delivery payload contains structural blockers")
    return {
        "result": result,
        "missing_sections": missing_sections,
        "invalid_sections": invalid_sections,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "unknowns": unknowns,
    }


def _continuity_summary(
    payload: Mapping[str, Any],
    exit_code: int,
) -> dict[str, Any]:
    _require_component_base(
        payload,
        schema_version=link_contract.RESULT_SCHEMA_VERSION,
        command="audit-link",
        claims_not_made=link_contract.CLAIMS_NOT_MADE,
    )
    inputs = payload.get("inputs")
    if not isinstance(inputs, Mapping):
        raise RuntimeError("continuity input receipt is unavailable")
    _require_input_entry(inputs.get("intake"))
    _require_input_entry(inputs.get("audit"))
    result = _validated_result(
        payload,
        exit_code,
        {
            link_contract.RESULT_LINKED: link_contract.EXIT_LINKED,
            link_contract.RESULT_MISMATCH: link_contract.EXIT_NOT_LINKED,
            link_contract.RESULT_INVALID: link_contract.EXIT_NOT_LINKED,
        },
    )
    matched = _contract_list(
        payload,
        "matched_fields",
        link_contract.IDENTITY_FIELDS,
    )
    mismatched = _contract_list(
        payload,
        "mismatched_fields",
        link_contract.IDENTITY_FIELDS,
    )
    missing = _contract_list(
        payload,
        "missing_fields",
        link_contract.IDENTITY_FIELDS,
    )
    unknowns = _contract_list(
        payload,
        "unknowns",
        link_contract.UNKNOWN_ORDER,
    )
    expected_next_steps = {
        link_contract.RESULT_LINKED: link_contract.NEXT_STEP_LINKED,
        link_contract.RESULT_MISMATCH: link_contract.NEXT_STEP_MISMATCH,
        link_contract.RESULT_INVALID: link_contract.NEXT_STEP_INVALID,
    }
    if payload.get("minimum_next_step") != expected_next_steps[result]:
        raise RuntimeError("continuity next-step contract is unavailable")
    if result == link_contract.RESULT_LINKED and (
        matched != list(link_contract.IDENTITY_FIELDS)
        or mismatched
        or missing
        or unknowns
    ):
        raise RuntimeError("linked payload contains continuity blockers")
    if result == link_contract.RESULT_MISMATCH and (
        not mismatched
        or missing
        or unknowns
        or set(matched).intersection(mismatched)
        or set((*matched, *mismatched))
        != set(link_contract.IDENTITY_FIELDS)
    ):
        raise RuntimeError("mismatch payload violated its public contract")
    return {
        "result": result,
        "matched_fields": matched,
        "mismatched_fields": mismatched,
        "missing_fields": missing,
        "unknowns": unknowns,
    }


def _file_identity(path: Path) -> _FileIdentity:
    try:
        absolute = Path(os.path.abspath(os.fspath(path)))
        metadata = os.lstat(absolute)
    except (TypeError, ValueError, OSError):
        return None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        return None
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _input_identities(
    intake_path: Path,
    audit_path: Path,
) -> tuple[_FileIdentity, _FileIdentity]:
    return (_file_identity(intake_path), _file_identity(audit_path))


def _result_payload(
    *,
    intake_path: Path | str | None,
    audit_path: Path | str | None,
    result: str,
    intake_check: Mapping[str, Any] | None = None,
    delivery_check: Mapping[str, Any] | None = None,
    continuity_check: Mapping[str, Any] | None = None,
    unknowns: Iterable[str] = (),
    minimum_next_step: str,
) -> dict[str, Any]:
    """Build one stable aggregate without exposing supplied content or paths."""

    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "command": "audit-gate",
        "result": result,
        "checks": {
            CHECK_INTAKE: dict(intake_check or _not_run_intake()),
            CHECK_DELIVERY: dict(delivery_check or _not_run_delivery()),
            CHECK_CONTINUITY: dict(
                continuity_check or _not_run_continuity()
            ),
        },
        "unknowns": _ordered(tuple(unknowns), UNKNOWN_ORDER),
        "claims_not_made": list(CLAIMS_NOT_MADE),
        "minimum_next_step": minimum_next_step,
        "inputs": {
            "intake": {
                "name": _safe_basename(intake_path),
                "content_echoed": False,
            },
            "audit": {
                "name": _safe_basename(audit_path),
                "content_echoed": False,
            },
        },
    }


def invalid_payload(
    intake_path: Path | str | None,
    audit_path: Path | str | None,
    *,
    unknowns: Iterable[str] = (),
    minimum_next_step: str = NEXT_STEP_INVALID,
) -> dict[str, Any]:
    """Return the stable INVALID shape for command or orchestration rejection."""

    return _result_payload(
        intake_path=intake_path,
        audit_path=audit_path,
        result=RESULT_INVALID,
        unknowns=unknowns,
        minimum_next_step=minimum_next_step,
    )


def _require_aggregate_input(value: Any) -> None:
    _require_input_entry(value)
    if not isinstance(value, Mapping):
        raise RuntimeError("aggregate input receipt is unavailable")
    if set(value) != {"name", "content_echoed"}:
        raise RuntimeError("aggregate input receipt shape is unavailable")
    name = value.get("name")
    if name != _safe_basename(name):
        raise RuntimeError("aggregate input name is unsafe")


def validate_result_contract(
    payload: Mapping[str, Any],
    exit_code: int,
) -> None:
    """Reject malformed aggregate output before a CLI receipt is emitted."""

    if not isinstance(payload, Mapping):
        raise RuntimeError("aggregate payload is not an object")
    if set(payload) != {
        "schema_version",
        "command",
        "result",
        "checks",
        "unknowns",
        "claims_not_made",
        "minimum_next_step",
        "inputs",
    }:
        raise RuntimeError("aggregate payload shape is unavailable")
    if (
        payload.get("schema_version") != RESULT_SCHEMA_VERSION
        or payload.get("command") != "audit-gate"
        or payload.get("claims_not_made") != list(CLAIMS_NOT_MADE)
    ):
        raise RuntimeError("aggregate payload base contract is unavailable")

    result = payload.get("result")
    expected_exits = {
        RESULT_READY: EXIT_READY,
        RESULT_NOT_READY: EXIT_NOT_READY,
        RESULT_INVALID: EXIT_NOT_READY,
    }
    if (
        not isinstance(result, str)
        or result not in expected_exits
        or exit_code != expected_exits[result]
    ):
        raise RuntimeError("aggregate result violated its exit contract")

    checks = payload.get("checks")
    if not isinstance(checks, Mapping) or set(checks) != set(CHECK_ORDER):
        raise RuntimeError("aggregate check map is unavailable")
    intake_check = checks.get(CHECK_INTAKE)
    delivery_check = checks.get(CHECK_DELIVERY)
    continuity_check = checks.get(CHECK_CONTINUITY)
    if not all(
        isinstance(item, Mapping)
        for item in (intake_check, delivery_check, continuity_check)
    ):
        raise RuntimeError("aggregate component summary is unavailable")
    assert isinstance(intake_check, Mapping)
    assert isinstance(delivery_check, Mapping)
    assert isinstance(continuity_check, Mapping)

    if set(intake_check) != {
        "result",
        "missing_fields",
        "invalid_fields",
        "unknowns",
    }:
        raise RuntimeError("aggregate intake summary shape is unavailable")
    intake_result = intake_check.get("result")
    if intake_result not in (
        intake_contract.RESULT_READY,
        intake_contract.RESULT_INCOMPLETE,
        intake_contract.RESULT_INVALID,
        RESULT_NOT_RUN,
    ):
        raise RuntimeError("aggregate intake state is unavailable")
    intake_missing = _contract_list(
        intake_check,
        "missing_fields",
        (*intake_contract.FIELD_ORDER, "unsupported_fields"),
    )
    intake_invalid = _contract_list(
        intake_check,
        "invalid_fields",
        (*intake_contract.FIELD_ORDER, "unsupported_fields"),
    )
    _contract_list(intake_check, "unknowns", _INTAKE_UNKNOWN_ORDER)
    if intake_result in (intake_contract.RESULT_READY, RESULT_NOT_RUN) and (
        intake_missing or intake_invalid
    ):
        raise RuntimeError("aggregate intake summary is contradictory")

    if set(delivery_check) != {
        "result",
        "missing_sections",
        "invalid_sections",
        "missing_fields",
        "invalid_fields",
        "unknowns",
    }:
        raise RuntimeError("aggregate delivery summary shape is unavailable")
    delivery_result = delivery_check.get("result")
    if delivery_result not in (
        audit_contract.RESULT_READY,
        audit_contract.RESULT_INCOMPLETE,
        audit_contract.RESULT_INVALID,
        RESULT_NOT_RUN,
    ):
        raise RuntimeError("aggregate delivery state is unavailable")
    delivery_missing_sections = _contract_list(
        delivery_check,
        "missing_sections",
        _AUDIT_SECTION_ORDER,
    )
    delivery_invalid_sections = _contract_list(
        delivery_check,
        "invalid_sections",
        _AUDIT_SECTION_ORDER,
    )
    delivery_missing_fields = _contract_list(
        delivery_check,
        "missing_fields",
        audit_contract.FIELD_ORDER,
    )
    delivery_invalid_fields = _contract_list(
        delivery_check,
        "invalid_fields",
        audit_contract.FIELD_ORDER,
    )
    _contract_list(delivery_check, "unknowns", _AUDIT_UNKNOWN_ORDER)
    if delivery_result in (
        audit_contract.RESULT_READY,
        RESULT_NOT_RUN,
    ) and any(
        (
            delivery_missing_sections,
            delivery_invalid_sections,
            delivery_missing_fields,
            delivery_invalid_fields,
        )
    ):
        raise RuntimeError("aggregate delivery summary is contradictory")

    if set(continuity_check) != {
        "result",
        "matched_fields",
        "mismatched_fields",
        "missing_fields",
        "unknowns",
    }:
        raise RuntimeError("aggregate continuity summary shape is unavailable")
    continuity_result = continuity_check.get("result")
    if continuity_result not in (
        link_contract.RESULT_LINKED,
        link_contract.RESULT_MISMATCH,
        link_contract.RESULT_INVALID,
        RESULT_NOT_RUN,
    ):
        raise RuntimeError("aggregate continuity state is unavailable")
    continuity_matched = _contract_list(
        continuity_check,
        "matched_fields",
        link_contract.IDENTITY_FIELDS,
    )
    continuity_mismatched = _contract_list(
        continuity_check,
        "mismatched_fields",
        link_contract.IDENTITY_FIELDS,
    )
    continuity_missing = _contract_list(
        continuity_check,
        "missing_fields",
        link_contract.IDENTITY_FIELDS,
    )
    continuity_unknown_order = (
        *link_contract.UNKNOWN_ORDER,
        "input_identity_changed",
    )
    continuity_unknowns = _contract_list(
        continuity_check,
        "unknowns",
        continuity_unknown_order,
    )
    if continuity_result == RESULT_NOT_RUN and any(
        (
            continuity_matched,
            continuity_mismatched,
            continuity_missing,
            continuity_unknowns,
        )
    ):
        raise RuntimeError("not-run continuity summary is contradictory")
    if continuity_result == link_contract.RESULT_LINKED and (
        continuity_matched != list(link_contract.IDENTITY_FIELDS)
        or continuity_mismatched
        or continuity_missing
        or continuity_unknowns
    ):
        raise RuntimeError("linked aggregate summary is contradictory")
    if continuity_result == link_contract.RESULT_MISMATCH and (
        not continuity_mismatched
        or continuity_missing
        or continuity_unknowns
        or set(continuity_matched).intersection(continuity_mismatched)
        or set((*continuity_matched, *continuity_mismatched))
        != set(link_contract.IDENTITY_FIELDS)
    ):
        raise RuntimeError("mismatch aggregate summary is contradictory")

    unknowns = _contract_list(payload, "unknowns", UNKNOWN_ORDER)
    inputs = payload.get("inputs")
    if not isinstance(inputs, Mapping) or set(inputs) != {"intake", "audit"}:
        raise RuntimeError("aggregate input map is unavailable")
    _require_aggregate_input(inputs.get("intake"))
    _require_aggregate_input(inputs.get("audit"))

    if unknowns:
        expected_result = RESULT_INVALID
    elif (
        intake_result == intake_contract.RESULT_READY
        and delivery_result == audit_contract.RESULT_READY
    ):
        if continuity_result == link_contract.RESULT_LINKED:
            expected_result = RESULT_READY
        elif continuity_result == link_contract.RESULT_MISMATCH:
            expected_result = RESULT_NOT_READY
        elif continuity_result == link_contract.RESULT_INVALID:
            expected_result = RESULT_INVALID
        else:
            raise RuntimeError("ready structures have no continuity result")
    elif (
        intake_result == intake_contract.RESULT_INVALID
        or delivery_result == audit_contract.RESULT_INVALID
    ):
        if continuity_result != RESULT_NOT_RUN:
            raise RuntimeError("invalid structure produced continuity")
        expected_result = RESULT_INVALID
    elif (
        intake_result == intake_contract.RESULT_INCOMPLETE
        or delivery_result == audit_contract.RESULT_INCOMPLETE
    ):
        if continuity_result != RESULT_NOT_RUN:
            raise RuntimeError("incomplete structure produced continuity")
        expected_result = RESULT_NOT_READY
    else:
        raise RuntimeError("aggregate component state is incomplete")
    if result != expected_result:
        raise RuntimeError("aggregate result contradicts its components")

    if result == RESULT_READY:
        expected_next_step = NEXT_STEP_READY
    elif result == RESULT_INVALID:
        expected_next_step = NEXT_STEP_INVALID
    elif intake_result == intake_contract.RESULT_INCOMPLETE:
        expected_next_step = NEXT_STEP_INTAKE
    elif delivery_result == audit_contract.RESULT_INCOMPLETE:
        expected_next_step = NEXT_STEP_DELIVERY
    else:
        expected_next_step = NEXT_STEP_CONTINUITY
    if payload.get("minimum_next_step") != expected_next_step:
        raise RuntimeError("aggregate next-step contract is unavailable")


def _validated_output(
    payload: dict[str, Any],
    exit_code: int,
) -> tuple[dict[str, Any], int]:
    validate_result_contract(payload, exit_code)
    return payload, exit_code


def _identity_failure(
    intake_path: Path,
    audit_path: Path,
    *,
    intake_check: Mapping[str, Any],
    delivery_check: Mapping[str, Any] | None = None,
    continuity_check: Mapping[str, Any] | None = None,
    marker: str,
) -> tuple[dict[str, Any], int]:
    return _validated_output(
        _result_payload(
            intake_path=intake_path,
            audit_path=audit_path,
            result=RESULT_INVALID,
            intake_check=intake_check,
            delivery_check=delivery_check,
            continuity_check=continuity_check,
            unknowns=(marker,),
            minimum_next_step=NEXT_STEP_INVALID,
        ),
        EXIT_NOT_READY,
    )


def validate_audit_gate_files(
    intake_path: Path,
    audit_path: Path,
) -> tuple[dict[str, Any], int]:
    """Run the three public validators in order and return one bounded result."""

    opening_identities = _input_identities(intake_path, audit_path)

    intake_payload, intake_exit = intake_contract.validate_intake_file(
        intake_path
    )
    intake_check = _intake_summary(intake_payload, intake_exit)
    if _input_identities(intake_path, audit_path) != opening_identities:
        return _identity_failure(
            intake_path,
            audit_path,
            intake_check=intake_check,
            marker="input_identity_changed",
        )

    delivery_payload, delivery_exit = (
        audit_contract.validate_audit_delivery_file(audit_path)
    )
    delivery_check = _delivery_summary(delivery_payload, delivery_exit)
    if _input_identities(intake_path, audit_path) != opening_identities:
        return _identity_failure(
            intake_path,
            audit_path,
            intake_check=intake_check,
            delivery_check=delivery_check,
            marker="input_identity_changed",
        )

    if None in opening_identities:
        return _identity_failure(
            intake_path,
            audit_path,
            intake_check=intake_check,
            delivery_check=delivery_check,
            marker="input_identity_unavailable",
        )

    structure_results = (
        intake_check["result"],
        delivery_check["result"],
    )
    if (
        intake_contract.RESULT_READY not in structure_results
        or audit_contract.RESULT_READY not in structure_results
    ):
        invalid = (
            intake_contract.RESULT_INVALID in structure_results
            or audit_contract.RESULT_INVALID in structure_results
        )
        if invalid:
            result = RESULT_INVALID
            next_step = NEXT_STEP_INVALID
        elif intake_check["result"] != intake_contract.RESULT_READY:
            result = RESULT_NOT_READY
            next_step = NEXT_STEP_INTAKE
        else:
            result = RESULT_NOT_READY
            next_step = NEXT_STEP_DELIVERY
        return _validated_output(
            _result_payload(
                intake_path=intake_path,
                audit_path=audit_path,
                result=result,
                intake_check=intake_check,
                delivery_check=delivery_check,
                minimum_next_step=next_step,
            ),
            EXIT_NOT_READY,
        )

    continuity_payload, continuity_exit = (
        link_contract.validate_audit_link_files(intake_path, audit_path)
    )
    continuity_check = _continuity_summary(
        continuity_payload,
        continuity_exit,
    )
    if _input_identities(intake_path, audit_path) != opening_identities:
        return _identity_failure(
            intake_path,
            audit_path,
            intake_check=intake_check,
            delivery_check=delivery_check,
            continuity_check={
                **_not_run_continuity(),
                "result": RESULT_INVALID,
                "unknowns": ["input_identity_changed"],
            },
            marker="input_identity_changed",
        )

    continuity_result = continuity_check["result"]
    if continuity_result == link_contract.RESULT_LINKED:
        result = RESULT_READY
        exit_code = EXIT_READY
        next_step = NEXT_STEP_READY
    elif continuity_result == link_contract.RESULT_MISMATCH:
        result = RESULT_NOT_READY
        exit_code = EXIT_NOT_READY
        next_step = NEXT_STEP_CONTINUITY
    else:
        result = RESULT_INVALID
        exit_code = EXIT_NOT_READY
        next_step = NEXT_STEP_INVALID

    return _validated_output(
        _result_payload(
            intake_path=intake_path,
            audit_path=audit_path,
            result=result,
            intake_check=intake_check,
            delivery_check=delivery_check,
            continuity_check=continuity_check,
            minimum_next_step=next_step,
        ),
        exit_code,
    )
