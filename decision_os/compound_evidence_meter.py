"""Evidence-strict aggregation for the Compound Evidence Meter v0.1."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any, Sequence
import unicodedata


BASELINE_SCHEMA = "decision-os.compound-evidence-baseline.v0.1"
EVENT_SCHEMA = "decision-os.compound-evidence-event.v0.1"
SNAPSHOT_SCHEMA = "decision-os.compound-evidence-snapshot.v0.1"

EVENT_TYPES = (
    "STRUCTURE_EXTRACTED",
    "VERIFIED_REUSE",
    "BOUNDED_GOAL",
    "WORKER_RUN",
    "CAUSAL_CONTINUATION",
    "CANON_PROMOTION",
    "HUMAN_SEAT_RETURN",
    "OPERATIONAL_ASSIST",
    "EFFICIENCY_COMPARISON",
)

EVENT_LABELS = {
    "BOUNDED_GOAL": "Measured bounded Goals",
    "WORKER_RUN": "Worker Runs",
    "CAUSAL_CONTINUATION": "Causal AI continuations",
    "STRUCTURE_EXTRACTED": "Verified structures extracted",
    "VERIFIED_REUSE": "Verified reuse events",
    "CANON_PROMOTION": "Canon promotions",
    "HUMAN_SEAT_RETURN": "Human Seat returns",
    "OPERATIONAL_ASSIST": "Bounded Operational Assists",
    "EFFICIENCY_COMPARISON": "Paired efficiency comparisons",
}

SNAPSHOT_ORDER = tuple(EVENT_LABELS)
COVERAGE_STATUSES = {"BACKFILLED", "NOT_BACKFILLED"}
CLAIM_STATUSES = {"OBSERVED", "MEASURED"}
RESOURCE_METRICS = (
    "elapsed_time_seconds",
    "worker_run_count",
    "model_cost",
    "token_count",
    "human_intervention_burden",
    "reconstruction_burden",
)
RESOURCE_LABELS = {
    "elapsed_time_seconds": "Elapsed-time delta",
    "worker_run_count": "Worker Run-count delta",
    "model_cost": "Model-cost delta",
    "token_count": "Token-count delta",
    "human_intervention_burden": "Human-intervention-burden delta",
    "reconstruction_burden": "Reconstruction-burden delta",
}

_HEX_40 = re.compile(r"[0-9a-f]{40}")
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_SAFE_EVENT_ID = re.compile(r"[a-z0-9][a-z0-9._:-]{2,127}")
_ISO_AS_OF = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})"
)


class MeterValidationError(ValueError):
    """The ledger cannot be admitted into a derived meter."""


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MeterValidationError(f"{label} must be a non-empty string")
    return value


def _require_exact_keys(
    value: dict[str, Any],
    expected: set[str],
    label: str,
) -> None:
    if set(value) != expected:
        raise MeterValidationError(
            f"{label} keys differ: expected {sorted(expected)!r}, "
            f"received {sorted(value)!r}"
        )


def _safe_relative_path(value: Any, label: str) -> str:
    text = _require_string(value, label)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or text != path.as_posix():
        raise MeterValidationError(f"{label} must be a normalized relative path")
    return text


def _git(repository: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=False,
        capture_output=True,
        stdin=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        raise MeterValidationError(
            "repository evidence is unavailable: "
            + completed.stderr.decode("utf-8", errors="replace").strip()
        )
    return completed.stdout


def _validate_source_identity(
    repository: Path,
    source: Any,
    *,
    label: str,
) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise MeterValidationError(f"{label} must be an object")
    _require_exact_keys(
        source,
        {"path", "repository_commit", "git_blob", "sha256"},
        label,
    )
    path = _safe_relative_path(source["path"], f"{label}.path")
    commit = _require_string(source["repository_commit"], f"{label}.repository_commit")
    blob = _require_string(source["git_blob"], f"{label}.git_blob")
    sha256 = _require_string(source["sha256"], f"{label}.sha256")
    if not _HEX_40.fullmatch(commit) or not _HEX_40.fullmatch(blob):
        raise MeterValidationError(f"{label} Git identities must be lowercase SHA-1")
    if not _HEX_64.fullmatch(sha256):
        raise MeterValidationError(f"{label}.sha256 must be lowercase SHA-256")

    resolved_blob = _git(repository, "rev-parse", f"{commit}:{path}").decode().strip()
    if resolved_blob != blob:
        raise MeterValidationError(f"{label} does not match the named commit and path")
    blob_bytes = _git(repository, "cat-file", "blob", blob)
    if hashlib.sha256(blob_bytes).hexdigest() != sha256:
        raise MeterValidationError(f"{label} SHA-256 does not match the Git blob")
    try:
        source_text = blob_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise MeterValidationError(f"{label} is not UTF-8 evidence text") from exc
    fragments = tuple(
        _normalize_fragment(match.group(1))
        for line in source_text.splitlines()
        if (match := re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line))
    )
    return {
        "path": path,
        "repository_commit": commit,
        "git_blob": blob,
        "sha256": sha256,
        "_fragments": fragments,
    }


def _normalize_fragment(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")


def _validate_pointer(
    pointer: Any,
    sources: dict[str, dict[str, Any]],
    label: str,
) -> str:
    text = _require_string(pointer, label)
    if "#" not in text:
        raise MeterValidationError(f"{label} must include a section fragment")
    path, fragment = text.split("#", 1)
    if path not in sources or not fragment.strip():
        raise MeterValidationError(f"{label} does not identify a registered source section")
    if _normalize_fragment(fragment) not in sources[path]["_fragments"]:
        raise MeterValidationError(f"{label} section is absent from the exact source artifact")
    return text


def _validate_baseline(
    repository: Path,
    record: Any,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    if not isinstance(record, dict):
        raise MeterValidationError("the baseline record must be an object")
    _require_exact_keys(
        record,
        {
            "schema",
            "record_type",
            "as_of",
            "repository",
            "canonical_commit",
            "baseline_boundary",
            "source_artifacts",
            "event_type_coverage",
        },
        "baseline record",
    )
    if record["schema"] != BASELINE_SCHEMA or record["record_type"] != "BASELINE_BOUNDARY":
        raise MeterValidationError("the first record must be the v0.1 baseline boundary")
    as_of = _require_string(record["as_of"], "baseline.as_of")
    if not _ISO_AS_OF.fullmatch(as_of):
        raise MeterValidationError("baseline.as_of must be an RFC 3339 timestamp")
    _require_string(record["repository"], "baseline.repository")
    canonical_commit = _require_string(record["canonical_commit"], "baseline.canonical_commit")
    if not _HEX_40.fullmatch(canonical_commit):
        raise MeterValidationError("baseline.canonical_commit must be a lowercase Git SHA-1")
    _git(repository, "cat-file", "-e", f"{canonical_commit}^{{commit}}")
    _require_string(record["baseline_boundary"], "baseline.baseline_boundary")

    raw_sources = record["source_artifacts"]
    if not isinstance(raw_sources, list) or not raw_sources:
        raise MeterValidationError("baseline.source_artifacts must be a non-empty list")
    sources: dict[str, dict[str, Any]] = {}
    for index, raw_source in enumerate(raw_sources):
        source = _validate_source_identity(
            repository,
            raw_source,
            label=f"baseline.source_artifacts[{index}]",
        )
        if source["repository_commit"] != canonical_commit:
            raise MeterValidationError("all baseline sources must bind the canonical commit")
        if source["path"] in sources:
            raise MeterValidationError("baseline source paths must be unique")
        sources[source["path"]] = source

    coverage = record["event_type_coverage"]
    if not isinstance(coverage, dict) or set(coverage) != set(EVENT_TYPES):
        raise MeterValidationError("baseline coverage must name exactly the v0.1 event classes")
    for event_type, entry in coverage.items():
        if not isinstance(entry, dict):
            raise MeterValidationError(f"coverage for {event_type} must be an object")
        _require_exact_keys(
            entry,
            {"status", "evidence_pointers", "evidence_boundary"},
            f"coverage.{event_type}",
        )
        if entry["status"] not in COVERAGE_STATUSES:
            raise MeterValidationError(f"coverage for {event_type} has an invalid status")
        pointers = entry["evidence_pointers"]
        if not isinstance(pointers, list) or not pointers:
            raise MeterValidationError(f"coverage for {event_type} needs evidence pointers")
        for index, pointer in enumerate(pointers):
            _validate_pointer(
                pointer,
                sources,
                f"coverage.{event_type}.evidence_pointers[{index}]",
            )
        _require_string(entry["evidence_boundary"], f"coverage.{event_type}.evidence_boundary")
    return record, sources


def _validate_metric(metric: Any, label: str) -> None:
    if not isinstance(metric, dict) or "status" not in metric:
        raise MeterValidationError(f"{label} must be a status-bearing object")
    status = metric["status"]
    if status == "UNKNOWN":
        _require_exact_keys(metric, {"status", "reason"}, label)
        _require_string(metric["reason"], f"{label}.reason")
        return
    if status != "MEASURED":
        raise MeterValidationError(f"{label}.status must be MEASURED or UNKNOWN")
    _require_exact_keys(
        metric,
        {"status", "route_a", "route_b", "delta", "unit"},
        label,
    )
    route_a = metric["route_a"]
    route_b = metric["route_b"]
    delta = metric["delta"]
    if (
        isinstance(route_a, bool)
        or isinstance(route_b, bool)
        or isinstance(delta, bool)
        or not isinstance(route_a, (int, float))
        or not isinstance(route_b, (int, float))
        or not isinstance(delta, (int, float))
    ):
        raise MeterValidationError(f"{label} measured values must be numeric")
    if abs((route_b - route_a) - delta) > 1e-9:
        raise MeterValidationError(f"{label}.delta must equal route_b minus route_a")
    _require_string(metric["unit"], f"{label}.unit")


def _validate_event(
    raw_event: Any,
    *,
    repository: Path,
    sources: dict[str, dict[str, Any]],
    prior_events: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(raw_event, dict):
        raise MeterValidationError("each event record must be an object")
    _require_exact_keys(
        raw_event,
        {
            "schema",
            "record_type",
            "event_id",
            "event_type",
            "as_of",
            "source_artifact",
            "source_identity",
            "evidence_pointer",
            "goal_or_chain_id",
            "related_prior_event_id",
            "measured_values",
            "evidence_boundary",
            "claim_status",
        },
        "event",
    )
    if raw_event["schema"] != EVENT_SCHEMA or raw_event["record_type"] != "EVENT":
        raise MeterValidationError("ledger event schema or record type is invalid")
    event_id = _require_string(raw_event["event_id"], "event.event_id")
    if not _SAFE_EVENT_ID.fullmatch(event_id):
        raise MeterValidationError("event.event_id is not a safe stable identity")
    if event_id in prior_events:
        raise MeterValidationError(f"duplicate event identity: {event_id}")
    event_type = raw_event["event_type"]
    if event_type not in EVENT_TYPES:
        raise MeterValidationError(f"unsupported v0.1 event type: {event_type!r}")
    as_of = _require_string(raw_event["as_of"], f"event {event_id}.as_of")
    if not _ISO_AS_OF.fullmatch(as_of):
        raise MeterValidationError(f"event {event_id}.as_of must be RFC 3339")
    source_path = _safe_relative_path(raw_event["source_artifact"], "event.source_artifact")
    if source_path not in sources:
        raise MeterValidationError(f"event {event_id} source is outside the baseline register")
    identity = raw_event["source_identity"]
    if not isinstance(identity, dict):
        raise MeterValidationError(f"event {event_id} source_identity must be an object")
    expected_identity = {
        key: sources[source_path][key]
        for key in ("repository_commit", "git_blob", "sha256")
    }
    if identity != expected_identity:
        raise MeterValidationError(f"event {event_id} source identity is untraceable")
    _validate_pointer(
        raw_event["evidence_pointer"],
        {source_path: sources[source_path]},
        f"event {event_id}.evidence_pointer",
    )
    _require_string(raw_event["evidence_boundary"], f"event {event_id}.evidence_boundary")
    if raw_event["claim_status"] not in CLAIM_STATUSES:
        raise MeterValidationError(f"event {event_id} claim status is invalid")
    if event_type == "EFFICIENCY_COMPARISON":
        if raw_event["claim_status"] != "MEASURED":
            raise MeterValidationError("efficiency comparisons must be MEASURED")
    elif raw_event["claim_status"] != "OBSERVED":
        raise MeterValidationError(f"{event_type} must use OBSERVED in v0.1")

    values = raw_event["measured_values"]
    if not isinstance(values, dict):
        raise MeterValidationError(f"event {event_id}.measured_values must be an object")
    chain_id = raw_event["goal_or_chain_id"]
    if chain_id is not None:
        _require_string(chain_id, f"event {event_id}.goal_or_chain_id")
    related_id = raw_event["related_prior_event_id"]
    related: dict[str, Any] | None = None
    if related_id is not None:
        _require_string(related_id, f"event {event_id}.related_prior_event_id")
        related = prior_events.get(related_id)
        if related is None:
            raise MeterValidationError(f"event {event_id} does not identify a prior event")

    if event_type == "STRUCTURE_EXTRACTED":
        _require_string(values.get("structure_id"), f"event {event_id}.structure_id")
        origin_blob = _require_string(
            values.get("origin_git_blob"),
            f"event {event_id}.origin_git_blob",
        )
        origin_sha256 = _require_string(
            values.get("origin_sha256"),
            f"event {event_id}.origin_sha256",
        )
        if not _HEX_40.fullmatch(origin_blob) or not _HEX_64.fullmatch(origin_sha256):
            raise MeterValidationError("STRUCTURE_EXTRACTED origin identity is invalid")
        if hashlib.sha256(_git(repository, "cat-file", "blob", origin_blob)).hexdigest() != origin_sha256:
            raise MeterValidationError("STRUCTURE_EXTRACTED origin identity is untraceable")
        if related_id is not None:
            raise MeterValidationError("a structure extraction cannot depend on a later reuse")
    elif event_type == "VERIFIED_REUSE":
        if related is None or related["event_type"] != "STRUCTURE_EXTRACTED":
            raise MeterValidationError("VERIFIED_REUSE requires a prior identified structure")
        structure_id = _require_string(values.get("structure_id"), f"event {event_id}.structure_id")
        if structure_id != related["measured_values"].get("structure_id"):
            raise MeterValidationError("VERIFIED_REUSE structure identity does not match")
        _require_string(values.get("reusing_run_id"), f"event {event_id}.reusing_run_id")
    elif event_type == "BOUNDED_GOAL":
        _require_string(chain_id, f"event {event_id}.goal_or_chain_id")
        _require_string(values.get("completion_status"), f"event {event_id}.completion_status")
    elif event_type == "WORKER_RUN":
        _require_string(chain_id, f"event {event_id}.goal_or_chain_id")
        _require_string(values.get("run_id"), f"event {event_id}.run_id")
        ordinal = values.get("run_ordinal")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
            raise MeterValidationError(f"event {event_id}.run_ordinal must be positive")
        if not any(
            prior["event_type"] == "BOUNDED_GOAL"
            and prior["goal_or_chain_id"] == chain_id
            for prior in prior_events.values()
        ):
            raise MeterValidationError("WORKER_RUN requires its prior bounded Goal")
    elif event_type == "CAUSAL_CONTINUATION":
        if related is None or related["event_type"] != "WORKER_RUN":
            raise MeterValidationError("CAUSAL_CONTINUATION requires its causal Worker Run")
        if not chain_id or chain_id != related["goal_or_chain_id"]:
            raise MeterValidationError("CAUSAL_CONTINUATION must preserve the source chain")
        if values.get("source_run_id") != related["measured_values"].get("run_id"):
            raise MeterValidationError("CAUSAL_CONTINUATION source Run identity differs")
        for key in ("source_evidence_sha256", "constructed_task_sha256"):
            value = _require_string(values.get(key), f"event {event_id}.{key}")
            if not _HEX_64.fullmatch(value):
                raise MeterValidationError(f"event {event_id}.{key} must be SHA-256")
    elif event_type == "CANON_PROMOTION":
        _require_string(values.get("promoted_structure_id"), f"event {event_id}.promoted_structure_id")
        if related is None or related["event_type"] != "VERIFIED_REUSE":
            raise MeterValidationError("CANON_PROMOTION requires the admitted reuse it promoted")
    elif event_type == "HUMAN_SEAT_RETURN":
        _require_string(values.get("return_contract_trigger"), f"event {event_id}.return_contract_trigger")
    elif event_type == "OPERATIONAL_ASSIST":
        _require_string(values.get("assist_scope"), f"event {event_id}.assist_scope")
        if values.get("changed_human_seat") is not False:
            raise MeterValidationError("OPERATIONAL_ASSIST must preserve Human Seat")
    elif event_type == "EFFICIENCY_COMPARISON":
        _require_string(values.get("comparison_id"), f"event {event_id}.comparison_id")
        routes = values.get("routes")
        if (
            not isinstance(routes, list)
            or len(routes) != 2
            or any(not isinstance(route, str) or not route.strip() for route in routes)
            or routes[0] == routes[1]
        ):
            raise MeterValidationError("EFFICIENCY_COMPARISON requires two distinct routes")
        _require_string(values.get("pairing_basis"), f"event {event_id}.pairing_basis")
        metrics = values.get("metrics")
        if not isinstance(metrics, dict) or set(metrics) != set(RESOURCE_METRICS):
            raise MeterValidationError("EFFICIENCY_COMPARISON must preserve every v0.1 metric state")
        measured = 0
        for metric_name in RESOURCE_METRICS:
            _validate_metric(metrics[metric_name], f"event {event_id}.metrics.{metric_name}")
            measured += metrics[metric_name]["status"] == "MEASURED"
        if measured == 0:
            raise MeterValidationError("EFFICIENCY_COMPARISON needs actual measured comparison evidence")
    return raw_event


def load_ledger(
    ledger_path: Path,
    repository: Path,
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    """Load and fail-closed validate one append-only JSONL evidence ledger."""

    try:
        raw_lines = ledger_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise MeterValidationError(f"ledger cannot be read: {exc}") from exc
    if not raw_lines or any(not line.strip() for line in raw_lines):
        raise MeterValidationError("ledger must contain non-blank JSONL records")
    records: list[Any] = []
    for line_number, line in enumerate(raw_lines, 1):
        try:
            records.append(json.loads(line))
        except (json.JSONDecodeError, ValueError) as exc:
            raise MeterValidationError(f"ledger line {line_number} is malformed JSON") from exc

    repository = repository.resolve()
    baseline, sources = _validate_baseline(repository, records[0])
    prior_events: dict[str, dict[str, Any]] = {}
    events: list[dict[str, Any]] = []
    for raw_event in records[1:]:
        event = _validate_event(
            raw_event,
            repository=repository,
            sources=sources,
            prior_events=prior_events,
        )
        prior_events[event["event_id"]] = event
        events.append(event)
    return baseline, tuple(events)


def aggregate_records(
    baseline: dict[str, Any],
    events: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Derive counters and observed deltas without independent headline input."""

    counts = Counter(event["event_type"] for event in events)
    counters: dict[str, dict[str, Any]] = {}
    coverage = baseline["event_type_coverage"]
    for event_type in EVENT_TYPES:
        known_count = counts[event_type]
        coverage_status = coverage[event_type]["status"]
        if coverage_status == "NOT_BACKFILLED":
            counters[event_type] = {
                "status": "UNKNOWN",
                "known_count": known_count,
                "baseline": "NOT_BACKFILLED",
            }
        else:
            status = (
                "MEASURED"
                if event_type == "EFFICIENCY_COMPARISON" and known_count > 0
                else "OBSERVED"
            )
            counters[event_type] = {
                "status": status,
                "count": known_count,
                "baseline": "BACKFILLED",
            }

    comparisons = [
        event for event in events if event["event_type"] == "EFFICIENCY_COMPARISON"
    ]
    resource_deltas: dict[str, dict[str, Any]] = {}
    for metric_name in RESOURCE_METRICS:
        admitted = []
        unknown_comparisons = []
        for event in comparisons:
            metric = event["measured_values"]["metrics"][metric_name]
            comparison_id = event["measured_values"]["comparison_id"]
            if metric["status"] == "MEASURED":
                admitted.append(
                    {
                        "comparison_id": comparison_id,
                        "delta": metric["delta"],
                        "unit": metric["unit"],
                    }
                )
            else:
                unknown_comparisons.append(comparison_id)
        resource_deltas[metric_name] = {
            "status": "MEASURED" if admitted else "UNKNOWN",
            "measured": admitted,
            "unknown_comparison_ids": unknown_comparisons,
        }

    return {
        "schema": SNAPSHOT_SCHEMA,
        "as_of": baseline["as_of"],
        "repository": baseline["repository"],
        "canonical_commit": baseline["canonical_commit"],
        "baseline_boundary": baseline["baseline_boundary"],
        "counters": counters,
        "resource_deltas": resource_deltas,
    }


def render_snapshot(snapshot: dict[str, Any]) -> str:
    """Render the compact human meter from a derived snapshot."""

    lines = [
        "Compound Evidence Meter v0.1",
        "",
        f"As-of canonical commit: {snapshot['canonical_commit']}",
        f"Baseline boundary: {snapshot['baseline_boundary']}",
        "",
    ]
    counters = snapshot["counters"]
    for event_type in SNAPSHOT_ORDER:
        counter = counters[event_type]
        label = EVENT_LABELS[event_type]
        if counter["status"] == "UNKNOWN":
            suffix = "UNKNOWN / NOT BACKFILLED"
            if counter["known_count"]:
                suffix += f" ({counter['known_count']} later observed event(s), not a total)"
        elif counter["status"] == "MEASURED":
            suffix = f"{counter['count']} (MEASURED)"
        elif event_type == "EFFICIENCY_COMPARISON":
            suffix = f"{counter['count']} (OBSERVED; measured admission required)"
        else:
            suffix = f"{counter['count']} (OBSERVED)"
        lines.append(f"{label}: {suffix}")

    lines.extend(("", "Observed resource deltas"))
    for metric_name in RESOURCE_METRICS:
        metric = snapshot["resource_deltas"][metric_name]
        if metric["status"] == "UNKNOWN":
            rendered = "UNKNOWN"
        else:
            rendered = "; ".join(
                f"{item['comparison_id']}={item['delta']:+g} {item['unit']}"
                for item in metric["measured"]
            )
            if metric["unknown_comparison_ids"]:
                rendered += "; UNKNOWN for " + ", ".join(metric["unknown_comparison_ids"])
        lines.append(f"{RESOURCE_LABELS[metric_name]}: {rendered}")
    return "\n".join(lines) + "\n"


def derive_meter(repository: Path, ledger_path: Path) -> dict[str, Any]:
    baseline, events = load_ledger(ledger_path, repository)
    return aggregate_records(baseline, events)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) not in (1, 2):
        sys.stderr.write(
            "usage: python -m decision_os.compound_evidence_meter "
            "<repository> [ledger.jsonl]\n"
        )
        return 2
    repository = Path(arguments[0]).resolve()
    ledger = (
        Path(arguments[1]).resolve()
        if len(arguments) == 2
        else repository / "evidence" / "compound_evidence_meter_v0_1.jsonl"
    )
    try:
        snapshot = derive_meter(repository, ledger)
    except MeterValidationError as exc:
        sys.stderr.write(f"Compound Evidence Meter invalid: {exc}\n")
        return 4
    sys.stdout.write(render_snapshot(snapshot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
