from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

from decision_os.intelligence_transplant import (
    AUDIT_COMPLETION_RECEIPT,
    AUDIT_INPUT_MANIFEST,
    AUTHORITY_PROVENANCE,
    CRYPTOGRAPHIC_PROVENANCE,
    DELTA_CANDIDATE,
    DELTA_IMPLEMENTED,
    DELTA_NONE,
    DELTA_REJECTED,
    DELTA_REUSED,
    DELTA_REVOKED,
    E1_DISCOVERY,
    E2_AUDIT,
    E3_ACCEPTED_DISCOVERY,
    E4_IMPLEMENTATION_BINDING,
    E5_REUSE,
    GENERALIZED_BOUNDARY,
    GENERALIZED_TRANSPLANT,
    GATE_BLOCK,
    GATE_CAP,
    GATE_GO,
    GATE_HOLD,
    IntelligenceTransplantError,
    LOWER_RUN_COMPLETION_RECEIPT,
    LOWER_RUN_TRIAL_MANIFEST,
    MANUAL_CONTROL_RECEIPT,
    OBJECT_FIELDS,
    OBJECT_TYPES,
    RUN_CHARTER,
    SCHEMA_VERSION,
    SEAT_ASSIGNMENT_RECEIPT,
    STRUCTURAL_FAIL,
    STRUCTURAL_PASS,
    ValidationAssessment,
    canonical_json,
    compute_content_hash,
    exact_ref,
    object_with_content_hash,
    reduce_evidence_graph,
    strict_json_object,
    validate_graph,
    validate_object,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXED_NOW = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)
RUN_ID = "stage5-run-001"
CHARTER_HEAD = "1" * 40
IMPLEMENTATION_BASE = "2" * 40
IMPLEMENTATION_HEAD = "3" * 40
ASSET_BLOB = "4" * 40
ASSET_HASH = "a" * 64
SOURCE_TASK_HASH = "b" * 64
NEW_TASK_HASH = "c" * 64
OWNER_ATTESTATION = "Shin manually attests this exact record and hash."


def timestamp(minute: int, second: int = 0) -> str:
    return f"2026-07-30T00:{minute:02d}:{second:02d}Z"


def signed(
    object_type: str,
    object_id: str,
    as_of: str,
    **fields: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "object_type": object_type,
        "object_id": object_id,
        "run_id": RUN_ID,
        "as_of": as_of,
        "supersedes": None,
        "content_hash": "",
        **fields,
    }
    special_ids = {
        RUN_CHARTER: "charter_id",
        SEAT_ASSIGNMENT_RECEIPT: "receipt_id",
        AUDIT_INPUT_MANIFEST: "manifest_id",
        E1_DISCOVERY: "e1_id",
        E2_AUDIT: "e2_id",
        AUDIT_COMPLETION_RECEIPT: "receipt_id",
        E3_ACCEPTED_DISCOVERY: "e3_id",
        E4_IMPLEMENTATION_BINDING: "e4_id",
        LOWER_RUN_TRIAL_MANIFEST: "manifest_id",
        LOWER_RUN_COMPLETION_RECEIPT: "receipt_id",
        E5_REUSE: "e5_id",
        MANUAL_CONTROL_RECEIPT: "receipt_id",
    }
    special_hashes = {
        RUN_CHARTER: "charter_hash",
        SEAT_ASSIGNMENT_RECEIPT: "receipt_hash",
        AUDIT_INPUT_MANIFEST: "manifest_hash",
        AUDIT_COMPLETION_RECEIPT: "receipt_hash",
        LOWER_RUN_TRIAL_MANIFEST: "manifest_hash",
        LOWER_RUN_COMPLETION_RECEIPT: "receipt_hash",
        MANUAL_CONTROL_RECEIPT: "receipt_hash",
    }
    value[special_ids[object_type]] = object_id
    if object_type in special_hashes:
        value[special_hashes[object_type]] = ""
    return object_with_content_hash(value)


def owner_fields(*, cryptographic: bool = False) -> dict[str, object]:
    value: dict[str, object] = {
        "authority_mode": "MANUAL_OWNER_ATTESTED",
        "decision_owner": "Shin",
        "decision_owner_attestation": OWNER_ATTESTATION,
    }
    if cryptographic:
        value["cryptographic_identity"] = "NOT_ESTABLISHED"
    return value


def seat(
    charter: dict[str, object],
    *,
    object_id: str,
    minute: int,
    seat_name: str,
    context: str,
    supersedes: dict[str, str] | None = None,
) -> dict[str, object]:
    value = signed(
        SEAT_ASSIGNMENT_RECEIPT,
        object_id,
        timestamp(minute),
        receipt_id=object_id,
        receipt_hash="",
        charter_ref=exact_ref(charter),
        seat=seat_name,
        assignee_context_identity=context,
        assignment_scope=f"Fixed {seat_name} work only.",
        allowed_inputs=["FIXED_MANIFEST_ONLY"],
        not_allowed_inputs=["UPPER_CONTEXT", "AUTOMATIC_INVOCATION"],
        effective_as_of=timestamp(minute),
        **owner_fields(cryptographic=True),
    )
    if supersedes is not None:
        value["supersedes"] = supersedes
        value = object_with_content_hash(value)
    return value


def valid_graph(
    *,
    verdict: str = "SURVIVE",
    causal_mode: str = "INTERCEPTION_TRACE",
) -> list[dict[str, object]]:
    charter = signed(
        RUN_CHARTER,
        "charter-001",
        timestamp(0),
        charter_id="charter-001",
        charter_hash="",
        run_type="intelligence_transplant",
        source_freeze_id="freeze-guided-001",
        source_freeze_sha256="d" * 64,
        source_task_id="source-task-001",
        source_task_hash=SOURCE_TASK_HASH,
        completion_line="A causal Stage 5 reuse is structurally demonstrated.",
        repository_head=CHARTER_HEAD,
        failure_family_id="failure-family-context-loss",
        failure_predicate="The agent acts without the fixed context guard.",
        charter_gate="GO",
        not_allowed_next=[
            "Do not merge or release.",
            "Do not invoke an external model.",
        ],
        **owner_fields(),
    )
    discovery_seat = seat(
        charter,
        object_id="seat-discovery-001",
        minute=1,
        seat_name="DISCOVERY",
        context="context-discovery-001",
    )
    e1 = signed(
        E1_DISCOVERY,
        "e1-001",
        timestamp(2),
        e1_id="e1-001",
        charter_ref=exact_ref(charter),
        discovery_assignment_ref=exact_ref(discovery_seat),
        discovery_context_identity="context-discovery-001",
        failure_family_id=charter["failure_family_id"],
        failure_predicate=charter["failure_predicate"],
        discovery_claim="A fixed context guard intercepts this failure family.",
        observed_failure="The unguarded path lost its fixed context.",
        mechanism="The path admitted action before context identity was checked.",
        strongest_falsifier="The same failure occurs with the guard active.",
        evidence_anchors=["artifact:incident-001", "trace:unguarded-001"],
        decision_owner_attestation=OWNER_ATTESTATION,
    )
    audit_seat = seat(
        charter,
        object_id="seat-audit-001",
        minute=3,
        seat_name="AUDIT",
        context="context-audit-001",
    )
    audit_manifest = signed(
        AUDIT_INPUT_MANIFEST,
        "audit-manifest-001",
        timestamp(4),
        manifest_id="audit-manifest-001",
        manifest_hash="",
        charter_ref=exact_ref(charter),
        target_e1_ref=exact_ref(e1),
        audit_assignment_ref=exact_ref(audit_seat),
        input_refs=[exact_ref(e1)],
        forbidden_input_classes=["DISCOVERY_CONVERSATION", "MUTABLE_TARGET"],
        frozen_as_of=timestamp(4),
        **owner_fields(),
    )
    required_deltas = (
        ["Bind the guard to the exact failure predicate."]
        if verdict == "REVISE"
        else []
    )
    e2 = signed(
        E2_AUDIT,
        "e2-001",
        timestamp(5),
        e2_id="e2-001",
        charter_ref=exact_ref(charter),
        target_e1_ref=exact_ref(e1),
        audit_manifest_ref=exact_ref(audit_manifest),
        audit_assignment_ref=exact_ref(audit_seat),
        auditor_context_identity="context-audit-001",
        verdict=verdict,
        strongest_counterexample="A model could succeed without the guard.",
        required_deltas=required_deltas,
        decision_owner_attestation=OWNER_ATTESTATION,
    )
    audit_receipt = signed(
        AUDIT_COMPLETION_RECEIPT,
        "audit-completion-001",
        timestamp(6),
        receipt_id="audit-completion-001",
        receipt_hash="",
        charter_ref=exact_ref(charter),
        target_e1_ref=exact_ref(e1),
        e2_ref=exact_ref(e2),
        audit_manifest_ref=exact_ref(audit_manifest),
        audit_assignment_ref=exact_ref(audit_seat),
        verdict=verdict,
        completed_as_of=timestamp(6),
        **owner_fields(cryptographic=True),
    )
    implementation_seat = seat(
        charter,
        object_id="seat-implementation-001",
        minute=7,
        seat_name="IMPLEMENTATION",
        context="context-implementation-001",
    )
    revisions = (
        [
            {
                "required_delta": required_deltas[0],
                "revision_applied": (
                    "The accepted claim now binds the guard to the exact "
                    "failure predicate."
                ),
            }
        ]
        if verdict == "REVISE"
        else []
    )
    e3 = signed(
        E3_ACCEPTED_DISCOVERY,
        "e3-001",
        timestamp(8),
        e3_id="e3-001",
        charter_ref=exact_ref(charter),
        e1_ref=exact_ref(e1),
        e2_ref=exact_ref(e2),
        audit_completion_receipt_ref=exact_ref(audit_receipt),
        accepted_claims=[e1["discovery_claim"]],
        revision_applied=revisions,
        excluded_claims=["The guard proves generalized model improvement."],
        implementation_requirements=["Implement an executable context guard."],
        implementation_scope=["decision_os/context_guard.py"],
        forbidden_overclaims=[GENERALIZED_BOUNDARY],
        claim_boundary=GENERALIZED_BOUNDARY,
        decision_owner_attestation=OWNER_ATTESTATION,
    )
    artifact = {
        "path": "decision_os/context_guard.py",
        "git_blob": ASSET_BLOB,
        "sha256": ASSET_HASH,
        "asset_identity": "context-guard",
        "asset_version": "v0.1",
        "asset_type": "guard",
    }
    e4 = signed(
        E4_IMPLEMENTATION_BINDING,
        "e4-001",
        timestamp(9),
        e4_id="e4-001",
        charter_ref=exact_ref(charter),
        e3_ref=exact_ref(e3),
        implementation_assignment_ref=exact_ref(implementation_seat),
        repository_base=IMPLEMENTATION_BASE,
        repository_head=IMPLEMENTATION_HEAD,
        repository_opening_head=IMPLEMENTATION_HEAD,
        repository_closing_head=IMPLEMENTATION_HEAD,
        repository_base_is_ancestor=True,
        changed_artifacts=[artifact],
        claim_bindings=[
            {
                "accepted_claim": e1["discovery_claim"],
                "required_control_behavior": (
                    "Stop action until context identity matches."
                ),
                "asset_identity": artifact["asset_identity"],
                "asset_version": artifact["asset_version"],
                "asset_hash": artifact["sha256"],
                "behavioral_verification": {
                    "mode": "ADVERSARIAL_BEHAVIOR_TEST",
                    "evidence_ref": "test:context-guard-adversarial-001",
                    "observed_behavior": (
                        "The guard stopped the action under the failure predicate."
                    ),
                },
                "activation_evidence": {
                    "mode": "ADVERSARIAL_TRIGGER_TRACE",
                    "trace_ref": "trace:guard-activation-001",
                    "activation_point": (
                        "Before the unbound action could be admitted."
                    ),
                },
            }
        ],
        focused_suite_status="PASS",
        regression_status="PASS",
        regression_reason=None,
        rollback_path="Revert the additive guard commit.",
        decision_owner_attestation=OWNER_ATTESTATION,
    )
    lower_seat = seat(
        charter,
        object_id="seat-lower-run-001",
        minute=10,
        seat_name="LOWER_RUN",
        context="context-lower-run-001",
    )
    allowed_manifest = [
        {
            "input_class": "NEW_TASK",
            "task_id": "new-task-001",
            "sha256": NEW_TASK_HASH,
        },
        {
            "input_class": "REPOSITORY_STATE",
            "repository_head": IMPLEMENTATION_HEAD,
        },
        {
            "input_class": "ACTIVE_ASSET",
            "asset_identity": "context-guard",
            "asset_version": "v0.1",
            "asset_hash": ASSET_HASH,
        },
        {
            "input_class": "MINIMUM_EXECUTION_BOUNDARY",
            "boundary": "Execute only the fixed new task.",
        },
    ]
    manifest = signed(
        LOWER_RUN_TRIAL_MANIFEST,
        "lower-manifest-001",
        timestamp(11),
        manifest_id="lower-manifest-001",
        manifest_hash="",
        charter_ref=exact_ref(charter),
        e4_ref=exact_ref(e4),
        lower_run_assignment_ref=exact_ref(lower_seat),
        trial_id="trial-001",
        new_task_id="new-task-001",
        new_task_hash=NEW_TASK_HASH,
        source_task_id=charter["source_task_id"],
        source_task_hash=charter["source_task_hash"],
        failure_family_id=charter["failure_family_id"],
        failure_predicate=charter["failure_predicate"],
        allowed_input_manifest=allowed_manifest,
        allowed_input_manifest_hash=hashlib.sha256(
            canonical_json(allowed_manifest)
        ).hexdigest(),
        forbidden_input_classes=[
            "UPPER_CONVERSATION",
            "UPPER_REASONING",
            "ACCEPTED_ANSWER",
            "SHIN_CORRECTION",
        ],
        input_separation_attestation="UPPER_INPUT_EXCLUDED",
        active_asset_identity=artifact["asset_identity"],
        active_asset_version=artifact["asset_version"],
        active_asset_hash=artifact["sha256"],
        repository_head=e4["repository_head"],
        lower_runtime_context_identity="context-lower-run-001",
        minimum_execution_boundary="Execute only the fixed new task.",
        effective_as_of=timestamp(11),
        **owner_fields(),
    )
    controlled_contrast: dict[str, object] | None
    if causal_mode == "CONTROLLED_CONTRAST":
        controlled_contrast = {
            "fixed_variables": [
                "new_task_bytes",
                "repository_head",
                "runtime_context",
                "input_manifest",
            ],
            "only_changed_condition": "ACTIVE_ASSET_ENABLED",
            "off_result": "FAILURE_OBSERVED",
            "on_result": "INTERCEPTED",
        }
    else:
        controlled_contrast = None
    completion = signed(
        LOWER_RUN_COMPLETION_RECEIPT,
        "lower-completion-001",
        timestamp(15),
        receipt_id="lower-completion-001",
        receipt_hash="",
        charter_ref=exact_ref(charter),
        trial_manifest_ref=exact_ref(manifest),
        e4_ref=exact_ref(e4),
        trial_id=manifest["trial_id"],
        actual_input_manifest_hash=manifest["allowed_input_manifest_hash"],
        active_asset_identity=manifest["active_asset_identity"],
        active_asset_version=manifest["active_asset_version"],
        active_asset_hash=manifest["active_asset_hash"],
        asset_activation_trace={
            "asset_identity": manifest["active_asset_identity"],
            "asset_version": manifest["active_asset_version"],
            "asset_hash": manifest["active_asset_hash"],
            "e4_ref": exact_ref(e4),
            "failure_predicate": charter["failure_predicate"],
            "interception_point": {
                "mode": "PRE_ACTION_CONTROL_INTERCEPTION",
                "event_ref": "event:pre-action-admission-001",
                "observed_effect": "INTERCEPTED",
            },
        },
        causal_proof_mode=causal_mode,
        controlled_contrast=controlled_contrast,
        detection_or_prevention_result="INTERCEPTED",
        human_rescue="NONE",
        no_rescue_attestation="NO_HUMAN_RESCUE",
        event_sequence=[
            "RUN_STARTED",
            "ASSET_ACTIVATED",
            "FAILURE_OBSERVED",
            "EVALUATED",
        ],
        lower_runtime_context_identity=manifest["lower_runtime_context_identity"],
        evaluator_context_identity="context-evaluator-001",
        evaluator_receipt="Evaluator confirms the fixed trace only.",
        started_as_of=timestamp(12),
        asset_activated_as_of=timestamp(13),
        failure_observed_as_of=timestamp(14),
        completed_as_of=timestamp(15),
        **owner_fields(cryptographic=True),
    )
    e5 = signed(
        E5_REUSE,
        "e5-001",
        timestamp(16),
        e5_id="e5-001",
        charter_ref=exact_ref(charter),
        e4_ref=exact_ref(e4),
        trial_manifest_ref=exact_ref(manifest),
        completion_receipt_ref=exact_ref(completion),
        source_task_id=manifest["source_task_id"],
        new_task_id=manifest["new_task_id"],
        failure_family_id=manifest["failure_family_id"],
        failure_predicate=manifest["failure_predicate"],
        causal_proof_mode=completion["causal_proof_mode"],
        detection_or_prevention_result=completion[
            "detection_or_prevention_result"
        ],
        decision_owner_attestation=OWNER_ATTESTATION,
    )
    return [
        charter,
        discovery_seat,
        e1,
        audit_seat,
        audit_manifest,
        e2,
        audit_receipt,
        implementation_seat,
        e3,
        e4,
        lower_seat,
        manifest,
        completion,
        e5,
    ]


def graph_index(
    graph: list[dict[str, object]],
    object_type: str,
    *,
    seat_name: str | None = None,
) -> int:
    for index, record in enumerate(graph):
        if record["object_type"] != object_type:
            continue
        if seat_name is not None and record.get("seat") != seat_name:
            continue
        return index
    raise AssertionError(f"{object_type} not found")


def rehash_graph(graph: list[dict[str, object]]) -> list[dict[str, object]]:
    """Rebind exact references in chronological order after a test mutation."""

    updated: dict[str, dict[str, object]] = {}

    def rebind(value: object) -> object:
        if isinstance(value, dict):
            if set(value) == {"object_id", "content_hash"}:
                target = updated.get(str(value["object_id"]))
                return exact_ref(target) if target is not None else deepcopy(value)
            return {key: rebind(item) for key, item in value.items()}
        if isinstance(value, list):
            return [rebind(item) for item in value]
        return deepcopy(value)

    result: list[dict[str, object]] = []
    for source in graph:
        record = rebind(source)
        assert isinstance(record, dict)
        record = object_with_content_hash(record)
        updated[str(record["object_id"])] = record
        result.append(record)
    return result


def control(
    graph: list[dict[str, object]],
    *,
    action: str,
    target: dict[str, object],
    minute: int,
    object_id: str,
    capped_from: str | None = None,
    cap_expires_as_of: str | None = None,
    release_evidence_refs: list[dict[str, str]] | None = None,
    cap_release_condition: str | None = None,
) -> dict[str, object]:
    charter = graph[graph_index(graph, RUN_CHARTER)]
    is_cap = action == "CAP"
    is_release = action == "CAP_RELEASE"
    is_rollback = action == "ROLLBACK"
    return signed(
        MANUAL_CONTROL_RECEIPT,
        object_id,
        timestamp(minute),
        receipt_id=object_id,
        receipt_hash="",
        charter_ref=exact_ref(charter),
        control_action=action,
        target_object_id=target["object_id"],
        target_content_hash=target["content_hash"],
        reason=f"Manual owner control: {action}.",
        effective_as_of=timestamp(minute),
        capped_from=capped_from if is_cap else None,
        cap_axis="iteration_count" if is_cap else None,
        cap_limit="1 lower-run attempt" if is_cap else None,
        cap_release_condition=(
            cap_release_condition
            if (is_cap or is_release)
            else None
        ),
        cap_expires_as_of=cap_expires_as_of if is_cap else None,
        release_evidence_refs=release_evidence_refs or [],
        post_rollback_repository_head=("5" * 40 if is_rollback else None),
        rollback_changed_artifacts=(
            [
                {
                    "path": "decision_os/context_guard.py",
                    "post_rollback_state": "PRESENT",
                    "git_blob": "6" * 40,
                    "sha256": "e" * 64,
                }
            ]
            if is_rollback
            else []
        ),
        **owner_fields(cryptographic=True),
    )


class IntelligenceTransplantPureTest(unittest.TestCase):
    maxDiff = None

    def assertIssue(
        self,
        graph: list[dict[str, object]],
        issue: str,
    ) -> None:
        assessment = validate_graph(graph, now=FIXED_NOW)
        self.assertEqual(STRUCTURAL_FAIL, assessment.structural_validation)
        self.assertIn(issue, assessment.issue_codes)

    def test_schema_is_exact_and_owns_every_record_type(self) -> None:
        schema = json.loads(
            (
                REPO_ROOT / "schema" / "v13_intelligence_transplant.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            "https://json-schema.org/draft/2020-12/schema",
            schema["$schema"],
        )
        variants = {
            entry["$ref"].rsplit("/", 1)[-1] for entry in schema["oneOf"]
        }
        self.assertEqual(12, len(variants))
        self.assertEqual(
            set(OBJECT_TYPES),
            set(
                schema["$defs"]["baseRecord"]["properties"]["object_type"][
                    "enum"
                ]
            ),
        )
        for name in variants:
            self.assertFalse(schema["$defs"][name]["unevaluatedProperties"])
        self.assertEqual(12, len(OBJECT_FIELDS))

    def test_committed_charter_fixtures_preserve_version_behavior(self) -> None:
        fixture_root = (
            REPO_ROOT / "tests" / "fixtures" / "intelligence_transplant_v0_1"
        )
        valid = strict_json_object(
            (fixture_root / "valid_charter.json").read_bytes()
        )
        future = strict_json_object(
            (fixture_root / "unknown_future_charter.json").read_bytes()
        )
        self.assertTrue(validate_graph([valid], now=FIXED_NOW).valid)
        self.assertEqual(
            GATE_HOLD,
            reduce_evidence_graph([future], now=FIXED_NOW).current_gate,
        )

    def test_canonical_hash_strict_parse_and_exact_reference(self) -> None:
        graph = valid_graph()
        charter = graph[0]
        self.assertEqual(charter["content_hash"], compute_content_hash(charter))
        self.assertEqual(charter["content_hash"], charter["charter_hash"])
        self.assertEqual(
            {"object_id": charter["object_id"], "content_hash": charter["content_hash"]},
            exact_ref(charter),
        )
        first = canonical_json({"é": 1, "a": [2]})
        second = canonical_json({"a": [2], "é": 1})
        self.assertEqual(first, second)
        self.assertEqual({"a": 1}, strict_json_object(b'{"a":1}'))
        for raw in (
            '{"a":1,"a":2}',
            '{"outer":{"a":1,"a":2}}',
            '{"value":NaN}',
            "[]",
            b"\xff",
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(IntelligenceTransplantError):
                    strict_json_object(raw)

    def test_valid_graph_is_deterministic_reused_and_never_overclaims(self) -> None:
        graph = valid_graph()
        original = deepcopy(graph)

        first = validate_graph(graph, now=FIXED_NOW)
        second = validate_graph(graph, now=FIXED_NOW)
        projection = reduce_evidence_graph(graph, now=FIXED_NOW)

        self.assertEqual(ValidationAssessment(STRUCTURAL_PASS, ()), first)
        self.assertEqual(first, second)
        self.assertEqual(DELTA_REUSED, projection.delta_state)
        self.assertEqual(GATE_HOLD, projection.current_gate)
        self.assertEqual(AUTHORITY_PROVENANCE, projection.authority_provenance)
        self.assertEqual(
            CRYPTOGRAPHIC_PROVENANCE,
            projection.cryptographic_provenance,
        )
        self.assertEqual(
            GENERALIZED_TRANSPLANT,
            projection.generalized_transplant,
        )
        self.assertEqual("MANUAL OWNER ATTESTED", projection.as_dict()["authority_provenance"])
        self.assertEqual("NOT ESTABLISHED", projection.as_dict()["cryptographic_provenance"])
        self.assertEqual(graph, original)

    def test_pure_layer_never_calls_process_or_filesystem(self) -> None:
        graph = valid_graph()
        with mock.patch(
            "subprocess.run",
            side_effect=AssertionError("pure validator invoked subprocess"),
        ), mock.patch(
            "os.system",
            side_effect=AssertionError("pure validator invoked a shell"),
        ), mock.patch(
            "pathlib.Path.open",
            side_effect=AssertionError("pure validator opened a file"),
        ):
            self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
            self.assertEqual(
                DELTA_REUSED,
                reduce_evidence_graph(graph, now=FIXED_NOW).delta_state,
            )

    def test_charter_freeze_is_not_execution_and_e1_is_not_candidate(self) -> None:
        graph = valid_graph()
        charter_only = graph[:1]
        projection = reduce_evidence_graph(charter_only, now=FIXED_NOW)
        self.assertEqual("NOT_ESTABLISHED", projection.execution_status)
        self.assertEqual(DELTA_NONE, projection.delta_state)

        e1_only = graph[:3]
        self.assertTrue(validate_graph(e1_only, now=FIXED_NOW).valid)
        projection = reduce_evidence_graph(e1_only, now=FIXED_NOW)
        self.assertEqual("ACTIVE", projection.execution_status)
        self.assertEqual(DELTA_NONE, projection.delta_state)
        self.assertEqual(GATE_HOLD, projection.current_gate)

    def test_incomplete_e2_graph_is_persistable_and_holds(self) -> None:
        graph = valid_graph()[:6]
        assessment = validate_graph(graph, now=FIXED_NOW)
        projection = reduce_evidence_graph(graph, now=FIXED_NOW)
        self.assertTrue(assessment.valid)
        self.assertEqual(DELTA_NONE, projection.delta_state)
        self.assertEqual(GATE_HOLD, projection.current_gate)
        self.assertIn("AUDIT_COMPLETION_RECEIPT", projection.missing_evidence)

    def test_e3_is_candidate_and_e4_is_implemented(self) -> None:
        graph = valid_graph()
        e3_end = graph_index(graph, E3_ACCEPTED_DISCOVERY) + 1
        candidate = reduce_evidence_graph(graph[:e3_end], now=FIXED_NOW)
        self.assertEqual(DELTA_CANDIDATE, candidate.delta_state)
        self.assertEqual(GATE_GO, candidate.current_gate)

        e4_end = graph_index(graph, E4_IMPLEMENTATION_BINDING) + 1
        implemented = reduce_evidence_graph(graph[:e4_end], now=FIXED_NOW)
        self.assertEqual(DELTA_IMPLEMENTED, implemented.delta_state)
        self.assertEqual(GATE_HOLD, implemented.current_gate)

    def test_same_seat_and_same_context_self_audit_are_invalid(self) -> None:
        graph = valid_graph()
        e1 = graph[graph_index(graph, E1_DISCOVERY)]
        discovery = graph[
            graph_index(graph, SEAT_ASSIGNMENT_RECEIPT, seat_name="DISCOVERY")
        ]
        e2_index = graph_index(graph, E2_AUDIT)
        graph[e2_index]["audit_assignment_ref"] = exact_ref(discovery)
        graph[e2_index]["auditor_context_identity"] = e1[
            "discovery_context_identity"
        ]
        graph = rehash_graph(graph)
        assessment = validate_graph(graph, now=FIXED_NOW)
        self.assertIn("SAME_SEAT_SELF_AUDIT", assessment.issue_codes)
        self.assertIn(
            "CONTEXT_INDEPENDENCE_VIOLATION",
            assessment.issue_codes,
        )

    def test_immutable_target_hash_substitution_is_invalid(self) -> None:
        graph = valid_graph()
        e2_index = graph_index(graph, E2_AUDIT)
        graph[e2_index]["target_e1_ref"]["content_hash"] = "0" * 64
        graph[e2_index] = object_with_content_hash(graph[e2_index])
        self.assertIssue(graph, "REFERENCE_HASH_MISMATCH")

    def test_reject_cannot_progress_to_e3_and_cap_cannot_rescue_it(self) -> None:
        graph = valid_graph(verdict="REJECT")
        self.assertIssue(graph, "REJECTED_LINEAGE_CANNOT_PROGRESS")
        e3 = graph[graph_index(graph, E3_ACCEPTED_DISCOVERY)]
        cap = control(
            graph,
            action="CAP",
            target=e3,
            minute=17,
            object_id="cap-invalid-001",
            capped_from=DELTA_NONE,
            cap_release_condition="New independent evidence is attached.",
        )
        graph.append(cap)
        projection = reduce_evidence_graph(graph, now=FIXED_NOW)
        self.assertEqual(STRUCTURAL_FAIL, projection.structural_validation)
        self.assertEqual(GATE_BLOCK, projection.current_gate)

    def test_reject_cannot_be_reaudited_into_survive_on_same_e1(self) -> None:
        graph = valid_graph()
        original_e2_index = graph_index(graph, E2_AUDIT)
        original_e2 = graph[original_e2_index]
        rejected_e2 = deepcopy(original_e2)
        rejected_e2["object_id"] = "e2-rejected-first"
        rejected_e2["e2_id"] = "e2-rejected-first"
        rejected_e2["as_of"] = timestamp(4, 30)
        rejected_e2["verdict"] = "REJECT"
        rejected_e2["required_deltas"] = []
        rejected_e2["supersedes"] = None
        rejected_e2 = object_with_content_hash(rejected_e2)

        original_receipt = graph[
            graph_index(graph, AUDIT_COMPLETION_RECEIPT)
        ]
        rejected_receipt = deepcopy(original_receipt)
        rejected_receipt["object_id"] = "audit-rejected-first"
        rejected_receipt["receipt_id"] = "audit-rejected-first"
        rejected_receipt["as_of"] = timestamp(4, 40)
        rejected_receipt["completed_as_of"] = timestamp(4, 40)
        rejected_receipt["e2_ref"] = exact_ref(rejected_e2)
        rejected_receipt["verdict"] = "REJECT"
        rejected_receipt["supersedes"] = None
        rejected_receipt = object_with_content_hash(rejected_receipt)

        graph[original_e2_index:original_e2_index] = [
            rejected_e2,
            rejected_receipt,
        ]
        graph = rehash_graph(graph)
        self.assertIssue(graph, "REJECTED_LINEAGE_CANNOT_PROGRESS")

    def test_cap_cannot_hide_reject_completion_transported_after_cap(self) -> None:
        full = valid_graph(verdict="REJECT")
        e2_end = graph_index(full, E2_AUDIT) + 1
        graph = full[:e2_end]
        graph.append(
            control(
                graph,
                action="CAP",
                target=graph[-1],
                minute=5,
                object_id="cap-before-reject-completion",
                capped_from=DELTA_NONE,
                cap_release_condition="A materially new lineage is attached.",
            )
        )
        graph.append(full[graph_index(full, AUDIT_COMPLETION_RECEIPT)])
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
        projection = reduce_evidence_graph(graph, now=FIXED_NOW)
        self.assertEqual(DELTA_REJECTED, projection.delta_state)
        self.assertEqual(GATE_BLOCK, projection.current_gate)

    def test_revise_requires_one_to_one_delta_binding(self) -> None:
        graph = valid_graph(verdict="REVISE")
        e3_index = graph_index(graph, E3_ACCEPTED_DISCOVERY)
        graph[e3_index]["revision_applied"] = []
        graph = rehash_graph(graph)
        self.assertIssue(graph, "REVISION_BINDING_INCOMPLETE")

    def test_false_implemented_requires_all_claim_and_activation_bindings(self) -> None:
        graph = valid_graph()
        e4_index = graph_index(graph, E4_IMPLEMENTATION_BINDING)
        graph[e4_index]["claim_bindings"] = []
        graph = rehash_graph(graph)
        assessment = validate_graph(graph, now=FIXED_NOW)
        self.assertIn("CLAIM_BINDING_INCOMPLETE", assessment.issue_codes)
        self.assertEqual(
            GATE_BLOCK,
            reduce_evidence_graph(graph, now=FIXED_NOW).current_gate,
        )

        graph = valid_graph()
        e4_index = graph_index(graph, E4_IMPLEMENTATION_BINDING)
        graph[e4_index]["claim_bindings"][0]["activation_evidence"] = ""
        graph = rehash_graph(graph)
        assessment = validate_graph(graph, now=FIXED_NOW)
        self.assertIn("BEHAVIORAL_ACTIVATION_MISSING", assessment.issue_codes)

    def test_repository_head_drift_is_invalid(self) -> None:
        graph = valid_graph()
        e4_index = graph_index(graph, E4_IMPLEMENTATION_BINDING)
        graph[e4_index]["repository_closing_head"] = "6" * 40
        graph = rehash_graph(graph)
        self.assertIssue(graph, "REPOSITORY_BINDING_INVALID")

    def test_forward_replacement_regresses_e3_and_e4_dependents(self) -> None:
        graph = valid_graph()
        old_e3 = graph[graph_index(graph, E3_ACCEPTED_DISCOVERY)]
        replacement = deepcopy(old_e3)
        replacement["object_id"] = "e3-002"
        replacement["e3_id"] = "e3-002"
        replacement["as_of"] = timestamp(17)
        replacement["supersedes"] = exact_ref(old_e3)
        replacement = object_with_content_hash(replacement)
        graph.append(replacement)
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
        projection = reduce_evidence_graph(graph, now=FIXED_NOW)
        self.assertEqual(DELTA_CANDIDATE, projection.delta_state)

        graph = valid_graph()
        old_e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        replacement = deepcopy(old_e4)
        replacement["object_id"] = "e4-002"
        replacement["e4_id"] = "e4-002"
        replacement["as_of"] = timestamp(17)
        replacement["supersedes"] = exact_ref(old_e4)
        replacement = object_with_content_hash(replacement)
        graph.append(replacement)
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
        projection = reduce_evidence_graph(graph, now=FIXED_NOW)
        self.assertEqual(DELTA_IMPLEMENTED, projection.delta_state)

    def test_detached_same_lineage_e3_and_e4_are_not_replacements(self) -> None:
        for object_type, identity_field in (
            (E3_ACCEPTED_DISCOVERY, "e3_id"),
            (E4_IMPLEMENTATION_BINDING, "e4_id"),
        ):
            with self.subTest(object_type=object_type):
                graph = valid_graph()
                detached = deepcopy(graph[graph_index(graph, object_type)])
                detached["object_id"] = f"{object_type.lower()}-detached"
                detached[identity_field] = detached["object_id"]
                detached["as_of"] = timestamp(17)
                detached["supersedes"] = None
                detached = object_with_content_hash(detached)
                graph.append(detached)
                self.assertIssue(graph, "FORWARD_REPLACEMENT_REQUIRED")

        graph = valid_graph()
        receipt = deepcopy(
            graph[graph_index(graph, AUDIT_COMPLETION_RECEIPT)]
        )
        receipt["object_id"] = "audit-completion-detached"
        receipt["receipt_id"] = "audit-completion-detached"
        receipt["as_of"] = timestamp(17)
        receipt["completed_as_of"] = timestamp(17)
        receipt["supersedes"] = None
        receipt = object_with_content_hash(receipt)
        graph.append(receipt)
        self.assertIssue(graph, "FORWARD_REPLACEMENT_REQUIRED")

    def test_revoke_e4_recovery_requires_exact_forward_successor(self) -> None:
        graph = valid_graph()
        old_e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        graph.append(
            control(
                graph,
                action="REVOKE",
                target=old_e4,
                minute=17,
                object_id="revoke-before-detached",
            )
        )
        detached = deepcopy(old_e4)
        detached["object_id"] = "e4-after-revoke-detached"
        detached["e4_id"] = "e4-after-revoke-detached"
        detached["as_of"] = timestamp(18)
        detached["supersedes"] = None
        detached = object_with_content_hash(detached)
        graph.append(detached)
        self.assertIssue(graph, "FORWARD_REPLACEMENT_REQUIRED")

        graph = valid_graph()
        old_e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        graph.append(
            control(
                graph,
                action="REVOKE",
                target=old_e4,
                minute=17,
                object_id="revoke-before-successor",
            )
        )
        successor = deepcopy(old_e4)
        successor["object_id"] = "e4-after-revoke-forward"
        successor["e4_id"] = "e4-after-revoke-forward"
        successor["as_of"] = timestamp(18)
        successor["supersedes"] = exact_ref(old_e4)
        successor = object_with_content_hash(successor)
        graph.append(successor)
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
        self.assertEqual(
            DELTA_IMPLEMENTED,
            reduce_evidence_graph(graph, now=FIXED_NOW).delta_state,
        )

    def test_pending_parallel_trial_does_not_demote_verified_reuse(self) -> None:
        graph = valid_graph()
        pending = deepcopy(
            graph[graph_index(graph, LOWER_RUN_TRIAL_MANIFEST)]
        )
        pending["object_id"] = "lower-manifest-pending"
        pending["manifest_id"] = "lower-manifest-pending"
        pending["as_of"] = timestamp(17)
        pending["effective_as_of"] = timestamp(17)
        pending["trial_id"] = "trial-pending"
        pending["new_task_id"] = "new-task-pending"
        pending["new_task_hash"] = "7" * 64
        pending["allowed_input_manifest"][0] = {
            "input_class": "NEW_TASK",
            "task_id": pending["new_task_id"],
            "sha256": pending["new_task_hash"],
        }
        pending["allowed_input_manifest_hash"] = hashlib.sha256(
            canonical_json(pending["allowed_input_manifest"])
        ).hexdigest()
        pending["supersedes"] = None
        pending = object_with_content_hash(pending)
        graph.append(pending)
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
        self.assertEqual(
            DELTA_REUSED,
            reduce_evidence_graph(graph, now=FIXED_NOW).delta_state,
        )

    def test_stale_dependency_created_after_replacement_is_rejected(self) -> None:
        graph = valid_graph()
        old_e3 = graph[graph_index(graph, E3_ACCEPTED_DISCOVERY)]
        replacement = deepcopy(old_e3)
        replacement["object_id"] = "e3-002"
        replacement["e3_id"] = "e3-002"
        replacement["as_of"] = timestamp(17)
        replacement["supersedes"] = exact_ref(old_e3)
        replacement = object_with_content_hash(replacement)
        graph.append(replacement)
        stale_e4 = deepcopy(graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)])
        stale_e4["object_id"] = "e4-stale"
        stale_e4["e4_id"] = "e4-stale"
        stale_e4["as_of"] = timestamp(18)
        stale_e4["supersedes"] = None
        stale_e4 = object_with_content_hash(stale_e4)
        graph.append(stale_e4)
        self.assertIssue(graph, "STALE_DEPENDENCY_REFERENCE")

    def test_same_task_failure_family_and_predicate_mismatch_are_invalid(self) -> None:
        mutations = (
            ("new_task_id", "source-task-001", "SAME_TASK_REUSE"),
            ("failure_family_id", "different-family", "FAILURE_FAMILY_MISMATCH"),
            ("failure_predicate", "different predicate", "FAILURE_PREDICATE_MISMATCH"),
        )
        for field, value, issue in mutations:
            with self.subTest(field=field):
                graph = valid_graph()
                manifest_index = graph_index(graph, LOWER_RUN_TRIAL_MANIFEST)
                graph[manifest_index][field] = value
                if field == "new_task_id":
                    graph[manifest_index]["new_task_hash"] = SOURCE_TASK_HASH
                graph = rehash_graph(graph)
                self.assertIssue(graph, issue)

    def test_manifest_created_after_run_start_is_invalid(self) -> None:
        graph = valid_graph()
        manifest_index = graph_index(graph, LOWER_RUN_TRIAL_MANIFEST)
        graph[manifest_index]["as_of"] = timestamp(12, 30)
        graph[manifest_index]["effective_as_of"] = timestamp(12, 30)
        graph = rehash_graph(graph)
        self.assertIssue(graph, "LOWER_RUN_MANIFEST_NOT_PREFROZEN")

    def test_upper_context_and_shin_answer_leakage_are_invalid(self) -> None:
        for injected in ("UPPER_CONVERSATION:secret", "SHIN_CORRECTION:answer"):
            with self.subTest(injected=injected):
                graph = valid_graph()
                manifest_index = graph_index(graph, LOWER_RUN_TRIAL_MANIFEST)
                manifest = graph[manifest_index]
                manifest["allowed_input_manifest"].append(injected)
                manifest["allowed_input_manifest_hash"] = hashlib.sha256(
                    canonical_json(manifest["allowed_input_manifest"])
                ).hexdigest()
                graph = rehash_graph(graph)
                self.assertIssue(graph, "LOWER_RUN_INPUT_LEAKAGE")

    def test_asset_must_activate_before_failure_and_trace_exact_e4(self) -> None:
        graph = valid_graph()
        completion_index = graph_index(graph, LOWER_RUN_COMPLETION_RECEIPT)
        graph[completion_index]["asset_activated_as_of"] = timestamp(14, 30)
        graph = rehash_graph(graph)
        self.assertIssue(graph, "ASSET_NOT_ACTIVATED")

        graph = valid_graph()
        completion_index = graph_index(graph, LOWER_RUN_COMPLETION_RECEIPT)
        graph[completion_index]["asset_activation_trace"]["asset_hash"] = "f" * 64
        graph = rehash_graph(graph)
        self.assertIssue(graph, "CAUSAL_TRACE_MISMATCH")

    def test_controlled_contrast_must_hold_all_other_variables_fixed(self) -> None:
        graph = valid_graph(causal_mode="CONTROLLED_CONTRAST")
        completion_index = graph_index(graph, LOWER_RUN_COMPLETION_RECEIPT)
        graph[completion_index]["controlled_contrast"][
            "only_changed_condition"
        ] = False
        graph = rehash_graph(graph)
        self.assertIssue(graph, "UNCONTROLLED_CONTRAST")

    def test_human_rescue_and_no_rescue_sequence_conflict_are_invalid(self) -> None:
        graph = valid_graph()
        completion_index = graph_index(graph, LOWER_RUN_COMPLETION_RECEIPT)
        graph[completion_index]["human_rescue"] = "PRESENT"
        graph = rehash_graph(graph)
        self.assertIssue(graph, "HUMAN_RESCUE_PRESENT")

        graph = valid_graph()
        completion_index = graph_index(graph, LOWER_RUN_COMPLETION_RECEIPT)
        graph[completion_index]["event_sequence"].append("HUMAN_RESCUE")
        graph = rehash_graph(graph)
        self.assertIssue(graph, "NO_RESCUE_SEQUENCE_MISMATCH")

    def test_manual_attestation_and_crypto_boundary_are_exact(self) -> None:
        graph = valid_graph()
        seat_index = graph_index(
            graph,
            SEAT_ASSIGNMENT_RECEIPT,
            seat_name="AUDIT",
        )
        del graph[seat_index]["decision_owner_attestation"]
        graph[seat_index] = object_with_content_hash(graph[seat_index])
        assessment = validate_graph(graph, now=FIXED_NOW)
        self.assertIn("DECISION_OWNER_ATTESTATION_REQUIRED", assessment.issue_codes)

        graph = valid_graph()
        seat_index = graph_index(
            graph,
            SEAT_ASSIGNMENT_RECEIPT,
            seat_name="AUDIT",
        )
        graph[seat_index]["cryptographic_identity"] = "CRYPTOGRAPHIC_VERIFIED"
        graph = rehash_graph(graph)
        self.assertIssue(graph, "CRYPTOGRAPHIC_IDENTITY_OVERCLAIM")

    def test_cap_freezes_promotion_expiry_holds_and_release_is_explicit(self) -> None:
        full = valid_graph()
        e3_end = graph_index(full, E3_ACCEPTED_DISCOVERY) + 1
        graph = full[:e3_end]
        e3 = graph[-1]
        cap = control(
            graph,
            action="CAP",
            target=e3,
            minute=8,
            object_id="cap-001",
            capped_from=DELTA_CANDIDATE,
            cap_expires_as_of=timestamp(18),
            cap_release_condition="Fresh bounded release evidence is attached.",
        )
        graph.append(cap)
        graph.extend(full[e3_end : graph_index(full, E4_IMPLEMENTATION_BINDING) + 1])
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)

        active = reduce_evidence_graph(
            graph,
            now=datetime(2026, 7, 30, 0, 17, tzinfo=timezone.utc),
        )
        self.assertEqual(DELTA_CANDIDATE, active.delta_state)
        self.assertEqual(GATE_CAP, active.current_gate)

        expired = reduce_evidence_graph(
            graph,
            now=datetime(2026, 7, 30, 0, 19, tzinfo=timezone.utc),
        )
        self.assertEqual(DELTA_CANDIDATE, expired.delta_state)
        self.assertEqual(GATE_HOLD, expired.current_gate)
        self.assertEqual("EXPIRED_HOLD", expired.active_cap["status"])

        release_evidence = seat(
            graph[0],
            object_id="seat-release-evidence-001",
            minute=19,
            seat_name="IMPLEMENTATION",
            context="context-release-evidence-001",
        )
        graph.append(release_evidence)
        release = control(
            graph,
            action="CAP_RELEASE",
            target=cap,
            minute=20,
            object_id="cap-release-001",
            release_evidence_refs=[exact_ref(release_evidence)],
            cap_release_condition="Fresh bounded release evidence is attached.",
        )
        graph.append(release)
        released = reduce_evidence_graph(
            graph,
            now=datetime(2026, 7, 30, 0, 21, tzinfo=timezone.utc),
        )
        self.assertEqual(DELTA_IMPLEMENTED, released.delta_state)
        self.assertIsNone(released.active_cap)

    def test_cap_release_without_authority_evidence_is_invalid(self) -> None:
        graph = valid_graph()
        e5 = graph[-1]
        cap = control(
            graph,
            action="CAP",
            target=e5,
            minute=17,
            object_id="cap-001",
            capped_from=DELTA_REUSED,
            cap_release_condition="Fresh release evidence.",
        )
        graph.append(cap)
        release = control(
            graph,
            action="CAP_RELEASE",
            target=cap,
            minute=18,
            object_id="cap-release-001",
            release_evidence_refs=[],
            cap_release_condition="Fresh release evidence.",
        )
        graph.append(release)
        self.assertIssue(graph, "CAP_RELEASE_AUTHORITY_MISSING")

    def test_cap_release_rejects_revoked_or_superseded_evidence(self) -> None:
        for invalidation in ("REVOKE", "SUPERSEDE"):
            with self.subTest(invalidation=invalidation):
                full = valid_graph()
                e3_end = graph_index(full, E3_ACCEPTED_DISCOVERY) + 1
                graph = full[:e3_end]
                cap = control(
                    graph,
                    action="CAP",
                    target=graph[-1],
                    minute=8,
                    object_id=f"cap-{invalidation.lower()}",
                    capped_from=DELTA_CANDIDATE,
                    cap_release_condition="Fresh bounded release evidence.",
                )
                graph.append(cap)
                evidence = seat(
                    graph[0],
                    object_id=f"seat-release-{invalidation.lower()}",
                    minute=9,
                    seat_name="IMPLEMENTATION",
                    context=f"context-release-{invalidation.lower()}",
                )
                graph.append(evidence)
                if invalidation == "REVOKE":
                    graph.append(
                        control(
                            graph,
                            action="REVOKE",
                            target=evidence,
                            minute=10,
                            object_id="revoke-release-evidence",
                        )
                    )
                else:
                    graph.append(
                        seat(
                            graph[0],
                            object_id="seat-release-successor",
                            minute=10,
                            seat_name="IMPLEMENTATION",
                            context="context-release-successor",
                            supersedes=exact_ref(evidence),
                        )
                    )
                release = control(
                    graph,
                    action="CAP_RELEASE",
                    target=cap,
                    minute=11,
                    object_id=f"release-{invalidation.lower()}",
                    release_evidence_refs=[exact_ref(evidence)],
                    cap_release_condition="Fresh bounded release evidence.",
                )
                graph.append(release)
                self.assertIssue(graph, "CAP_RELEASE_AUTHORITY_MISSING")

    def test_revoke_sets_revoked_and_missing_authority_is_invalid(self) -> None:
        graph = valid_graph()
        e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        revoke = control(
            graph,
            action="REVOKE",
            target=e4,
            minute=17,
            object_id="revoke-001",
        )
        graph.append(revoke)
        projection = reduce_evidence_graph(graph, now=FIXED_NOW)
        self.assertEqual(DELTA_REVOKED, projection.delta_state)
        self.assertEqual(GATE_HOLD, projection.current_gate)

        graph = valid_graph()
        e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        revoke = control(
            graph,
            action="REVOKE",
            target=e4,
            minute=17,
            object_id="revoke-001",
        )
        revoke["decision_owner_attestation"] = ""
        revoke = object_with_content_hash(revoke)
        graph.append(revoke)
        self.assertIssue(graph, "DECISION_OWNER_ATTESTATION_REQUIRED")

    def test_control_target_hash_swap_and_revoked_replay_are_invalid(self) -> None:
        graph = valid_graph()
        e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        revoke = control(
            graph,
            action="REVOKE",
            target=e4,
            minute=17,
            object_id="revoke-001",
        )
        revoke["target_content_hash"] = "0" * 64
        revoke = object_with_content_hash(revoke)
        graph.append(revoke)
        self.assertIssue(graph, "REFERENCE_HASH_MISMATCH")

        graph = valid_graph()
        e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        revoke = control(
            graph,
            action="REVOKE",
            target=e4,
            minute=17,
            object_id="revoke-001",
        )
        graph.append(revoke)
        replay = deepcopy(graph[graph_index(graph, E5_REUSE)])
        replay["object_id"] = "e5-replay"
        replay["e5_id"] = "e5-replay"
        replay["as_of"] = timestamp(18)
        replay["supersedes"] = None
        replay = object_with_content_hash(replay)
        graph.append(replay)
        self.assertIssue(graph, "STALE_DEPENDENCY_REFERENCE")

    def test_rollback_must_target_current_effective_e4(self) -> None:
        graph = valid_graph()
        old_e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        replacement = deepcopy(old_e4)
        replacement["object_id"] = "e4-002"
        replacement["e4_id"] = "e4-002"
        replacement["as_of"] = timestamp(17)
        replacement["supersedes"] = exact_ref(old_e4)
        replacement = object_with_content_hash(replacement)
        graph.append(replacement)
        rollback = control(
            graph,
            action="ROLLBACK",
            target=old_e4,
            minute=18,
            object_id="rollback-001",
        )
        graph.append(rollback)
        self.assertIssue(graph, "ROLLBACK_TARGET_MISMATCH")

    def test_audit_manifest_is_strictly_prefrozen_and_seat_bound(self) -> None:
        graph = valid_graph()
        manifest_index = graph_index(graph, AUDIT_INPUT_MANIFEST)
        e2 = graph[graph_index(graph, E2_AUDIT)]
        graph[manifest_index]["as_of"] = e2["as_of"]
        graph[manifest_index]["frozen_as_of"] = e2["as_of"]
        graph = rehash_graph(graph)
        self.assertIssue(graph, "AUDIT_MANIFEST_NOT_PREFROZEN")

        graph = valid_graph()
        manifest_index = graph_index(graph, AUDIT_INPUT_MANIFEST)
        second_audit_seat = seat(
            graph[0],
            object_id="seat-audit-002",
            minute=3,
            seat_name="AUDIT",
            context="context-audit-002",
        )
        graph.insert(manifest_index, second_audit_seat)
        e2_index = graph_index(graph, E2_AUDIT)
        receipt_index = graph_index(graph, AUDIT_COMPLETION_RECEIPT)
        graph[e2_index]["audit_assignment_ref"] = exact_ref(second_audit_seat)
        graph[e2_index]["auditor_context_identity"] = "context-audit-002"
        graph[receipt_index]["audit_assignment_ref"] = exact_ref(
            second_audit_seat
        )
        graph = rehash_graph(graph)
        self.assertIssue(graph, "IMMUTABLE_TARGET_MISMATCH")

    def test_e5_requires_one_exact_manifest_completion_e4_chain(self) -> None:
        graph = valid_graph()
        original_manifest = graph[
            graph_index(graph, LOWER_RUN_TRIAL_MANIFEST)
        ]
        alternate_manifest = deepcopy(original_manifest)
        alternate_manifest["object_id"] = "lower-manifest-002"
        alternate_manifest["manifest_id"] = "lower-manifest-002"
        alternate_manifest["as_of"] = timestamp(17)
        alternate_manifest["effective_as_of"] = timestamp(17)
        alternate_manifest["supersedes"] = None
        alternate_manifest = object_with_content_hash(alternate_manifest)
        graph.append(alternate_manifest)

        spliced_e5 = deepcopy(graph[graph_index(graph, E5_REUSE)])
        spliced_e5["object_id"] = "e5-splice"
        spliced_e5["e5_id"] = "e5-splice"
        spliced_e5["as_of"] = timestamp(18)
        spliced_e5["trial_manifest_ref"] = exact_ref(alternate_manifest)
        spliced_e5["supersedes"] = None
        spliced_e5 = object_with_content_hash(spliced_e5)
        graph.append(spliced_e5)
        self.assertIssue(graph, "E5_CHAIN_SPLICE")

    def test_indirect_dependency_revoke_and_replacement_regress_reuse(self) -> None:
        for object_type, seat_name in (
            (AUDIT_INPUT_MANIFEST, None),
            (SEAT_ASSIGNMENT_RECEIPT, "AUDIT"),
        ):
            with self.subTest(revoked=object_type):
                graph = valid_graph()
                target = graph[
                    graph_index(graph, object_type, seat_name=seat_name)
                ]
                graph.append(
                    control(
                        graph,
                        action="REVOKE",
                        target=target,
                        minute=17,
                        object_id=f"revoke-indirect-{object_type.lower()}",
                    )
                )
                projection = reduce_evidence_graph(graph, now=FIXED_NOW)
                self.assertEqual(DELTA_REVOKED, projection.delta_state)
                self.assertEqual(GATE_HOLD, projection.current_gate)

        graph = valid_graph()
        old_manifest = graph[graph_index(graph, AUDIT_INPUT_MANIFEST)]
        replacement_manifest = deepcopy(old_manifest)
        replacement_manifest["object_id"] = "audit-manifest-002"
        replacement_manifest["manifest_id"] = "audit-manifest-002"
        replacement_manifest["as_of"] = timestamp(17)
        replacement_manifest["frozen_as_of"] = timestamp(17)
        replacement_manifest["supersedes"] = exact_ref(old_manifest)
        replacement_manifest = object_with_content_hash(replacement_manifest)
        graph.append(replacement_manifest)
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
        self.assertEqual(
            DELTA_NONE,
            reduce_evidence_graph(graph, now=FIXED_NOW).delta_state,
        )

        graph = valid_graph()
        old_seat = graph[
            graph_index(graph, SEAT_ASSIGNMENT_RECEIPT, seat_name="AUDIT")
        ]
        replacement_seat = seat(
            graph[0],
            object_id="seat-audit-002",
            minute=17,
            seat_name="AUDIT",
            context="context-audit-002",
            supersedes=exact_ref(old_seat),
        )
        graph.append(replacement_seat)
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
        self.assertNotEqual(
            DELTA_REUSED,
            reduce_evidence_graph(graph, now=FIXED_NOW).delta_state,
        )

    def test_cap_binds_actual_prefix_maturity_target_and_safety_controls(self) -> None:
        graph = valid_graph()
        cap = control(
            graph,
            action="CAP",
            target=graph[-1],
            minute=17,
            object_id="cap-wrong-maturity",
            capped_from=DELTA_CANDIDATE,
            cap_release_condition="Exact release evidence.",
        )
        graph.append(cap)
        self.assertIssue(graph, "CAP_MATURITY_MISMATCH")

        graph = valid_graph()
        unrelated_seat = seat(
            graph[0],
            object_id="seat-unrelated-001",
            minute=17,
            seat_name="IMPLEMENTATION",
            context="context-unrelated-001",
        )
        graph.append(unrelated_seat)
        graph.append(
            control(
                graph,
                action="CAP",
                target=unrelated_seat,
                minute=18,
                object_id="cap-unrelated",
                capped_from=DELTA_REUSED,
                cap_release_condition="Exact release evidence.",
            )
        )
        self.assertIssue(graph, "CAP_TARGET_NOT_CURRENT")

        full = valid_graph()
        receipt_end = graph_index(full, AUDIT_COMPLETION_RECEIPT) + 1
        rejected = valid_graph(verdict="REJECT")[:receipt_end]
        rejected.append(
            control(
                rejected,
                action="CAP",
                target=rejected[-1],
                minute=7,
                object_id="cap-reject",
                capped_from=DELTA_REJECTED,
                cap_release_condition="A new lineage is attached.",
            )
        )
        self.assertIssue(rejected, "CONTROL_CANNOT_RESCUE_INVALID_GRAPH")
        self.assertEqual(
            GATE_BLOCK,
            reduce_evidence_graph(rejected, now=FIXED_NOW).current_gate,
        )

        graph = valid_graph()
        cap = control(
            graph,
            action="CAP",
            target=graph[-1],
            minute=17,
            object_id="cap-before-revoke",
            capped_from=DELTA_REUSED,
            cap_release_condition="Exact release evidence.",
        )
        graph.append(cap)
        audit_manifest = graph[graph_index(graph, AUDIT_INPUT_MANIFEST)]
        graph.append(
            control(
                graph,
                action="REVOKE",
                target=audit_manifest,
                minute=18,
                object_id="revoke-after-cap",
            )
        )
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
        projection = reduce_evidence_graph(graph, now=FIXED_NOW)
        self.assertEqual(DELTA_REVOKED, projection.delta_state)
        self.assertEqual(GATE_HOLD, projection.current_gate)

    def test_cap_prefix_uses_sequence_for_equal_timestamps(self) -> None:
        full = valid_graph()
        e3_end = graph_index(full, E3_ACCEPTED_DISCOVERY) + 1
        graph = full[:e3_end]
        graph.append(
            control(
                graph,
                action="CAP",
                target=graph[-1],
                minute=8,
                object_id="cap-equal-time",
                capped_from=DELTA_CANDIDATE,
                cap_release_condition="Exact release evidence.",
            )
        )
        later_e4 = deepcopy(full[graph_index(full, E4_IMPLEMENTATION_BINDING)])
        later_e4["as_of"] = timestamp(8)
        later_e4 = object_with_content_hash(later_e4)
        graph.append(later_e4)
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
        projection = reduce_evidence_graph(graph, now=FIXED_NOW)
        self.assertEqual(DELTA_CANDIDATE, projection.delta_state)
        self.assertEqual(GATE_CAP, projection.current_gate)

    def test_behavioral_evidence_cannot_be_opaque_pass_only_text(self) -> None:
        graph = valid_graph()
        e4_index = graph_index(graph, E4_IMPLEMENTATION_BINDING)
        binding = graph[e4_index]["claim_bindings"][0]
        binding["behavioral_verification"] = "test suite PASS only"
        binding["activation_evidence"] = "file exists at commit only"
        graph = rehash_graph(graph)
        self.assertIssue(graph, "BEHAVIORAL_ACTIVATION_MISSING")
        self.assertEqual(
            GATE_BLOCK,
            reduce_evidence_graph(graph, now=FIXED_NOW).current_gate,
        )

    def test_lower_run_manifest_and_event_sequence_reject_unknown_inputs(self) -> None:
        graph = valid_graph()
        manifest_index = graph_index(graph, LOWER_RUN_TRIAL_MANIFEST)
        graph[manifest_index]["allowed_input_manifest"].append(
            {
                "input_class": "SHIN_HINT",
                "hint": "rescue",
            }
        )
        graph[manifest_index]["allowed_input_manifest_hash"] = hashlib.sha256(
            canonical_json(graph[manifest_index]["allowed_input_manifest"])
        ).hexdigest()
        graph = rehash_graph(graph)
        self.assertIssue(graph, "LOWER_RUN_INPUT_LEAKAGE")

        graph = valid_graph()
        completion_index = graph_index(graph, LOWER_RUN_COMPLETION_RECEIPT)
        graph[completion_index]["event_sequence"].insert(
            2, "SHIN_HINT_INJECTED"
        )
        graph = rehash_graph(graph)
        self.assertIssue(graph, "NO_RESCUE_SEQUENCE_MISMATCH")

    def test_controlled_contrast_binds_active_asset_and_exact_result(self) -> None:
        graph = valid_graph(causal_mode="CONTROLLED_CONTRAST")
        completion_index = graph_index(graph, LOWER_RUN_COMPLETION_RECEIPT)
        graph[completion_index]["controlled_contrast"][
            "only_changed_condition"
        ] = "MODEL_VARIANT"
        graph = rehash_graph(graph)
        self.assertIssue(graph, "UNCONTROLLED_CONTRAST")

        graph = valid_graph(causal_mode="CONTROLLED_CONTRAST")
        completion_index = graph_index(graph, LOWER_RUN_COMPLETION_RECEIPT)
        graph[completion_index]["controlled_contrast"][
            "on_result"
        ] = "PREVENTED"
        graph = rehash_graph(graph)
        self.assertIssue(graph, "CAUSAL_TRACE_MISMATCH")

    def test_e3_cannot_add_unaudited_or_excluded_accepted_claims(self) -> None:
        graph = valid_graph()
        e3_index = graph_index(graph, E3_ACCEPTED_DISCOVERY)
        graph[e3_index]["accepted_claims"].append(
            "An unaudited generalized claim."
        )
        graph = rehash_graph(graph)
        self.assertIssue(graph, "ACCEPTED_CLAIM_MISMATCH")

        graph = valid_graph()
        e3_index = graph_index(graph, E3_ACCEPTED_DISCOVERY)
        graph[e3_index]["excluded_claims"].append(
            graph[e3_index]["accepted_claims"][0]
        )
        graph = rehash_graph(graph)
        self.assertIssue(graph, "ACCEPTED_CLAIM_MISMATCH")

    def test_asset_loaded_only_is_not_activation_or_causal_proof(self) -> None:
        graph = valid_graph()
        completion_index = graph_index(graph, LOWER_RUN_COMPLETION_RECEIPT)
        graph[completion_index]["asset_activation_trace"][
            "interception_point"
        ] = "asset loaded"
        graph = rehash_graph(graph)
        self.assertIssue(graph, "CAUSAL_TRACE_MISMATCH")

    def test_rollback_requires_forward_successor_and_supports_deletion(self) -> None:
        graph = valid_graph()
        old_e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        rollback = control(
            graph,
            action="ROLLBACK",
            target=old_e4,
            minute=17,
            object_id="rollback-detached",
        )
        graph.append(rollback)
        detached = deepcopy(old_e4)
        detached["object_id"] = "e4-detached"
        detached["e4_id"] = "e4-detached"
        detached["as_of"] = timestamp(18)
        detached["supersedes"] = None
        detached = object_with_content_hash(detached)
        graph.append(detached)
        self.assertIssue(graph, "ROLLBACK_FORWARD_REPLACEMENT_REQUIRED")

        graph = valid_graph()
        old_e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        rollback = control(
            graph,
            action="ROLLBACK",
            target=old_e4,
            minute=17,
            object_id="rollback-forward",
        )
        graph.append(rollback)
        successor = deepcopy(old_e4)
        successor["object_id"] = "e4-forward"
        successor["e4_id"] = "e4-forward"
        successor["as_of"] = timestamp(18)
        successor["supersedes"] = exact_ref(old_e4)
        successor = object_with_content_hash(successor)
        graph.append(successor)
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)
        self.assertEqual(
            DELTA_IMPLEMENTED,
            reduce_evidence_graph(graph, now=FIXED_NOW).delta_state,
        )

        graph = valid_graph()
        old_e4 = graph[graph_index(graph, E4_IMPLEMENTATION_BINDING)]
        deletion_rollback = control(
            graph,
            action="ROLLBACK",
            target=old_e4,
            minute=17,
            object_id="rollback-deletion",
        )
        deletion_rollback["rollback_changed_artifacts"] = [
            {
                "path": "decision_os/context_guard.py",
                "post_rollback_state": "DELETED",
                "git_blob": None,
                "sha256": None,
            }
        ]
        deletion_rollback = object_with_content_hash(deletion_rollback)
        graph.append(deletion_rollback)
        self.assertTrue(validate_graph(graph, now=FIXED_NOW).valid)

    def test_dependency_list_order_is_authoritative_for_equal_timestamps(self) -> None:
        graph = valid_graph()
        e3_index = graph_index(graph, E3_ACCEPTED_DISCOVERY)
        e4_index = graph_index(graph, E4_IMPLEMENTATION_BINDING)
        graph[e4_index]["as_of"] = graph[e3_index]["as_of"]
        graph = rehash_graph(graph)
        graph[e3_index], graph[e4_index] = graph[e4_index], graph[e3_index]
        self.assertIssue(graph, "DEPENDENCY_SEQUENCE_ORDER_INVALID")

    def test_unknown_future_version_is_read_only_hold(self) -> None:
        for future_version in (
            "decision-os.intelligence-transplant.v9",
            "v13-intelligence-transplant-v9.0",
        ):
            with self.subTest(future_version=future_version):
                graph = valid_graph()[:1]
                graph[0]["schema_version"] = future_version
                graph[0]["future_extension"] = {
                    "new_semantics": "unknown to this reader"
                }
                graph[0] = object_with_content_hash(graph[0])
                assessment = validate_graph(graph, now=FIXED_NOW)
                projection = reduce_evidence_graph(graph, now=FIXED_NOW)
                self.assertEqual(
                    STRUCTURAL_FAIL, assessment.structural_validation
                )
                self.assertEqual(
                    ("UNSUPPORTED_SCHEMA_VERSION",),
                    assessment.issue_codes,
                )
                self.assertEqual(GATE_HOLD, projection.current_gate)

        charter = valid_graph()[0]
        tampered = {
            key: deepcopy(value)
            for key, value in charter.items()
            if key
            in {
                "schema_version",
                "object_type",
                "object_id",
                "run_id",
                "as_of",
                "supersedes",
                "content_hash",
                "charter_id",
                "charter_hash",
            }
        }
        tampered["schema_version"] = "tamper-bypass"
        tampered = object_with_content_hash(tampered)
        projection = reduce_evidence_graph([tampered], now=FIXED_NOW)
        self.assertEqual(GATE_BLOCK, projection.current_gate)
        self.assertIn("INVALID_OBJECT_STRUCTURE", projection.issue_codes)

        arbitrary = valid_graph()[0]
        arbitrary["schema_version"] = "tamper-bypass"
        arbitrary = object_with_content_hash(arbitrary)
        projection = reduce_evidence_graph([arbitrary], now=FIXED_NOW)
        self.assertEqual(GATE_BLOCK, projection.current_gate)
        self.assertIn("INVALID_OBJECT_STRUCTURE", projection.issue_codes)

    def test_validate_object_checks_local_shape_without_forcing_completion(self) -> None:
        graph = valid_graph()
        e2 = graph[graph_index(graph, E2_AUDIT)]
        self.assertTrue(validate_object(e2, now=FIXED_NOW).valid)
        partial = graph[: graph_index(graph, E2_AUDIT) + 1]
        self.assertTrue(
            validate_object(e2, objects=partial, now=FIXED_NOW).valid
        )


if __name__ == "__main__":
    unittest.main()
