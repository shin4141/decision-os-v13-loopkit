"""Evidence-bound authorization for Owner-attested public claim surfaces.

The guard is deliberately mechanical.  It validates a frozen native
``PUBLIC_CLAIM_MANIFEST``, reconstructs its byte-complete surface, resolves the
current Stage 5 graph on every evaluation, and compares declared predicates
and evidence contracts without deriving claims from prose.

Persistence remains exclusively owned by
``IntelligenceTransplantController.freeze_manifest``.  This module never
writes store files or appends events directly.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any, Callable, Mapping, Sequence

from decision_os.companion.intelligence_transplant import (
    IntelligenceTransplantBusyError,
    IntelligenceTransplantConflictError,
    IntelligenceTransplantController,
    IntelligenceTransplantIntegrityError,
    IntelligenceTransplantValidationError,
    _repository_head,
    _transport_receipt,
)
from decision_os.intelligence_transplant import (
    E3_ACCEPTED_DISCOVERY,
    MANUAL_CONTROL_RECEIPT,
    OBJECT_TYPES,
    PUBLIC_CLAIM_MANIFEST,
    RUN_CHARTER,
    SCHEMA_VERSION,
    SEAT_ASSIGNMENT_RECEIPT,
    canonical_json,
    compute_content_hash,
    exact_ref,
    reduce_evidence_graph,
    strict_json_object,
    validate_graph,
    validate_object,
    _all_refs,
    _current_records,
    _select_chain,
)


ASSET_IDENTITY = "decision-os.public-claim-evidence-guard"
ASSET_TYPE = "guard"
ASSET_VERSION = "v0.1"

MANIFEST_SCHEMA_VERSION = "decision-os.public-claim-manifest.v0.1"
EVALUATION_SCHEMA_VERSION = "decision-os.public-claim-evaluation.v0.1"
RESULT_SCHEMA_VERSION = "decision-os.public-claim-evaluation-result.v0.1"
AUTHORIZATION_RECEIPT_SCHEMA_VERSION = (
    "decision-os.public-claim-authorization-receipt.v0.1"
)

ALLOW = "ALLOW"
REVISE_REQUIRED = "REVISE_REQUIRED"
HOLD = "HOLD"
BLOCK = "BLOCK"
DISPOSITIONS = (ALLOW, REVISE_REQUIRED, HOLD, BLOCK)

MANIFEST_TRUST_EVIDENCE_INCOMPLETE = "MANIFEST_TRUST_EVIDENCE_INCOMPLETE"
MANIFEST_TRUST_BINDING_MISMATCH = "MANIFEST_TRUST_BINDING_MISMATCH"
MANIFEST_TRANSPORT_AUTHORITY_MISMATCH = (
    "MANIFEST_TRANSPORT_AUTHORITY_MISMATCH"
)
MANIFEST_TRANSPORT_BINDING_MISMATCH = "MANIFEST_TRANSPORT_BINDING_MISMATCH"
MANIFEST_TRANSPORT_TIME_ORDER_INVALID = (
    "MANIFEST_TRANSPORT_TIME_ORDER_INVALID"
)
NATIVE_GRAPH_EVIDENCE_UNAVAILABLE = "NATIVE_GRAPH_EVIDENCE_UNAVAILABLE"
NATIVE_GRAPH_CONTRADICTION = "NATIVE_GRAPH_CONTRADICTION"
EVIDENCE_APPLICABILITY_MISMATCH = "EVIDENCE_APPLICABILITY_MISMATCH"
MATCHING_EVIDENCE_REQUIRED = "MATCHING_EVIDENCE_REQUIRED"
VISIBLE_SPAN_FORBIDDEN_DECLARATION = (
    "VISIBLE_SPAN_FORBIDDEN_DECLARATION"
)
QUALIFIER_REQUIRED = "QUALIFIER_REQUIRED"
RUNTIME_OVERRIDE_ATTEMPT = "RUNTIME_OVERRIDE_ATTEMPT"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,200}$")

_EVALUATION_FIELDS = {
    "content_hash",
    "evaluation_id",
    "event_chain_head",
    "evidence",
    "manifest_hash",
    "manifest_id",
    "owner_execution_authorization",
    "repository_head",
    "schema_version",
    "surface_base64",
}
_EVIDENCE_FIELDS = {
    "boundary_id",
    "claim_id",
    "evidence_id",
    "evidence_type",
    "event_chain_head",
    "observed_behavior",
    "payload_base64",
    "payload_sha256",
    "repository_head",
    "verification_mode",
}

_PROHIBITED_STATE_STRINGS = (
    "delta_state=implemented",
    "delta_state = implemented",
    '"delta_state":"implemented"',
    "delta_state=reused",
    "delta_state = reused",
    '"delta_state":"reused"',
    "formal_run_maturity=implemented",
    "formal_run_maturity = implemented",
    "formal_run_maturity=reused",
    "formal_run_maturity = reused",
    "generalized_transplant_established",
)
_GENERALIZED_SUBJECTS = (
    "generalized transplant",
    "generalized reuse",
    "model-independent transplant",
    "cross-model reuse",
    "multiple-model transplant",
    "external reproduction",
)
_GENERALIZED_OUTCOMES = ("established", "proven", "successful")
_PROHIBITED_GENERALIZED_DECLARATIONS = tuple(
    f"{subject} {outcome}"
    for subject in _GENERALIZED_SUBJECTS
    for outcome in _GENERALIZED_OUTCOMES
)
_STRUCTURAL_BYTES = frozenset(
    bytes.fromhex(
        "09 0a 0d 20 21 23 28 29 2a 2b 2d 2e 3a 3d 3e 5b 5d 5f 60 7b 7d"
    )
)
_SEVERITY = {ALLOW: 0, REVISE_REQUIRED: 1, HOLD: 2, BLOCK: 3}
_MATURITY = {"NONE": 0, "CANDIDATE": 1, "IMPLEMENTED": 2, "REUSED": 3}


class PublicClaimGuardError(ValueError):
    """One bounded public-claim operation could not safely continue."""

    def __init__(
        self,
        disposition: str,
        issue_code: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.disposition = disposition
        self.issue_code = issue_code


@dataclass(frozen=True)
class TrustedManifestReadback:
    """Freshly verified native state used by exactly one evaluation."""

    record: dict[str, Any]
    records: tuple[dict[str, Any], ...]
    events: tuple[dict[str, Any], ...]
    current_inventory: tuple[dict[str, Any], ...]
    current_e3: dict[str, Any]
    projection: dict[str, Any]
    repository_head: str
    event_chain_head: str
    manifest_event: dict[str, Any]
    transport_payload: bytes
    transport_receipt: dict[str, Any]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _fail(disposition: str, issue_code: str, message: str) -> None:
    raise PublicClaimGuardError(disposition, issue_code, message)


def _strict_base64(value: Any) -> bytes:
    if not isinstance(value, str) or not value:
        _fail(BLOCK, RUNTIME_OVERRIDE_ATTEMPT, "Exact base64 bytes are required.")
    try:
        payload = base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise PublicClaimGuardError(
            BLOCK,
            RUNTIME_OVERRIDE_ATTEMPT,
            "Exact base64 bytes are invalid.",
        ) from exc
    if base64.b64encode(payload).decode("ascii") != value:
        _fail(BLOCK, RUNTIME_OVERRIDE_ATTEMPT, "Base64 is not canonical.")
    return payload


def _visible_forbidden(text: str) -> bool:
    folded = "".join(
        character.lower() if "A" <= character <= "Z" else character
        for character in text
    )
    return any(item in folded for item in _PROHIBITED_STATE_STRINGS) or any(
        item in folded for item in _PROHIBITED_GENERALIZED_DECLARATIONS
    )


def _record_key(record: Mapping[str, Any]) -> tuple[str, str]:
    return (str(record.get("object_id")), str(record.get("content_hash")))


def _replaced_keys(
    records: Sequence[Mapping[str, Any]],
) -> set[tuple[str, str]]:
    return {
        (
            str(record["supersedes"]["object_id"]),
            str(record["supersedes"]["content_hash"]),
        )
        for record in records
        if isinstance(record.get("supersedes"), Mapping)
        and set(record["supersedes"]) == {"content_hash", "object_id"}
    }


def _revoked_keys(
    records: Sequence[Mapping[str, Any]],
) -> set[tuple[str, str]]:
    return {
        (
            str(record.get("target_object_id")),
            str(record.get("target_content_hash")),
        )
        for record in records
        if record.get("object_type") == MANUAL_CONTROL_RECEIPT
        and record.get("control_action") in {"REVOKE", "ROLLBACK"}
    }


def current_object_inventory(
    records: Sequence[Mapping[str, Any]],
    *,
    run_id: str,
) -> tuple[dict[str, Any], ...]:
    """Return exact current, valid, same-run, non-revoked native records."""

    replaced = _replaced_keys(records)
    revoked = _revoked_keys(records)
    candidates = [
        deepcopy(dict(record))
        for record in records
        if record.get("run_id") == run_id
        and _record_key(record) not in replaced
        and _record_key(record) not in revoked
        and validate_object(record).valid
    ]
    registry = {_record_key(record): record for record in candidates}
    current: list[dict[str, Any]] = []
    for record in candidates:
        if record.get("object_type") == MANUAL_CONTROL_RECEIPT:
            current.append(record)
            continue
        dependencies_current = True
        for reference in _all_refs(record):
            if reference == record.get("supersedes"):
                continue
            reference_key = (
                str(reference.get("object_id")),
                str(reference.get("content_hash")),
            )
            if (
                reference_key in replaced
                or reference_key in revoked
                or reference_key not in registry
            ):
                dependencies_current = False
                break
        if dependencies_current:
            current.append(record)

    sidecar_keys: set[tuple[str, str]] = set()
    for record in current:
        if record.get("object_type") != PUBLIC_CLAIM_MANIFEST:
            continue
        lineage = (str(record.get("run_id")), str(record.get("surface_id")))
        if lineage in sidecar_keys:
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "More than one current public-claim sidecar occupies a lineage.",
            )
        sidecar_keys.add(lineage)
    return tuple(current)


def reconstruct_surface(record: Mapping[str, Any]) -> bytes:
    """Reconstruct and verify one byte-complete fixed public surface."""

    assessment = validate_object(record)
    if not assessment.valid or record.get("object_type") != PUBLIC_CLAIM_MANIFEST:
        _fail(
            BLOCK,
            MANIFEST_TRUST_BINDING_MISMATCH,
            "The public-claim Manifest is not a valid native object.",
        )
    surface = b"".join(
        str(span["exact_text"]).encode("utf-8") for span in record["spans"]
    )
    if (
        len(surface) != record.get("surface_utf8_bytes")
        or _sha256(surface) != record.get("surface_sha256")
    ):
        _fail(
            BLOCK,
            MANIFEST_TRUST_BINDING_MISMATCH,
            "The public surface does not reconstruct exactly.",
        )
    for span in record["spans"]:
        if span.get("span_type") == "STRUCTURAL_BYTES":
            exact = str(span["exact_text"]).encode("utf-8")
            if any(byte not in _STRUCTURAL_BYTES for byte in exact):
                _fail(
                    BLOCK,
                    MANIFEST_TRUST_BINDING_MISMATCH,
                    "A structural span contains a visible assertion byte.",
                )
    return surface


def _find_exact(
    records: Sequence[Mapping[str, Any]],
    reference: Mapping[str, Any],
) -> dict[str, Any] | None:
    for record in records:
        if exact_ref(record) == reference:
            return deepcopy(dict(record))
    return None


def _exact_e3_allowed_input(e3: Mapping[str, Any]) -> str:
    return (
        "E3_ACCEPTED_DISCOVERY:"
        f"{e3['object_id']}@{e3['content_hash']}"
    )


def _validate_current_authority(
    record: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    inventory: Sequence[Mapping[str, Any]],
    *,
    missing_disposition: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    e3 = _find_exact(records, record["e3_ref"])
    if e3 is None:
        _fail(
            missing_disposition,
            NATIVE_GRAPH_EVIDENCE_UNAVAILABLE,
            "The exact current E3 is unavailable.",
        )
    if e3.get("object_type") != E3_ACCEPTED_DISCOVERY:
        _fail(
            BLOCK,
            NATIVE_GRAPH_CONTRADICTION,
            "The E3 reference resolves to the wrong native object type.",
        )
    seat = _find_exact(records, record["implementation_assignment_ref"])
    if seat is None:
        _fail(
            missing_disposition,
            MANIFEST_TRUST_EVIDENCE_INCOMPLETE,
            "The exact Implementation Seat is unavailable.",
        )
    inventory_keys = {_record_key(item) for item in inventory}
    if _record_key(e3) not in inventory_keys:
        _fail(
            BLOCK,
            NATIVE_GRAPH_CONTRADICTION,
            "The referenced E3 is not current.",
        )
    if _record_key(seat) not in inventory_keys:
        _fail(
            BLOCK,
            MANIFEST_TRANSPORT_AUTHORITY_MISMATCH,
            "The referenced Implementation Seat is not current.",
        )
    if (
        seat.get("object_type") != SEAT_ASSIGNMENT_RECEIPT
        or seat.get("seat") != "IMPLEMENTATION"
        or seat.get("run_id") != record.get("run_id")
        or seat.get("charter_ref") != record.get("charter_ref")
        or _exact_e3_allowed_input(e3) not in seat.get("allowed_inputs", ())
    ):
        _fail(
            BLOCK,
            MANIFEST_TRANSPORT_AUTHORITY_MISMATCH,
            "The transport Seat does not carry the exact implementation authority.",
        )
    if record.get("generalized_boundary") != e3.get("claim_boundary"):
        _fail(
            BLOCK,
            NATIVE_GRAPH_CONTRADICTION,
            "The Manifest boundary contradicts current E3 truth.",
        )
    return e3, seat


def _core_projection(projection: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        projection.get("execution_status"),
        projection.get("delta_state"),
        projection.get("current_gate"),
        tuple(projection.get("missing_evidence", ())),
    )


def _sidecar_neutral_projection(
    records: Sequence[Mapping[str, Any]],
    projection: Mapping[str, Any],
) -> bool:
    sidecar_refs = {
        _record_key(record)
        for record in records
        if record.get("object_type") == PUBLIC_CLAIM_MANIFEST
    }
    without_sidecars = [
        record
        for record in records
        if record.get("object_type") != PUBLIC_CLAIM_MANIFEST
        and not (
            record.get("object_type") == MANUAL_CONTROL_RECEIPT
            and (
                str(record.get("target_object_id")),
                str(record.get("target_content_hash")),
            )
            in sidecar_refs
        )
    ]
    if not without_sidecars:
        return False
    baseline = reduce_evidence_graph(without_sidecars).as_dict()
    return _core_projection(baseline) == _core_projection(projection)


def _normalize_evidence(
    value: Any,
    *,
    repository_head: str,
    event_chain_head: str,
) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        _fail(BLOCK, RUNTIME_OVERRIDE_ATTEMPT, "Evidence must be an exact array.")
    result: list[dict[str, Any]] = []
    identities: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping) or set(item) != _EVIDENCE_FIELDS:
            _fail(
                BLOCK,
                RUNTIME_OVERRIDE_ATTEMPT,
                "Runtime evidence contains an unapproved field.",
            )
        evidence = deepcopy(dict(item))
        if (
            not isinstance(evidence.get("evidence_id"), str)
            or _SAFE_ID.fullmatch(evidence["evidence_id"]) is None
            or evidence["evidence_id"] in identities
            or not isinstance(evidence.get("claim_id"), str)
            or _SAFE_ID.fullmatch(evidence["claim_id"]) is None
            or evidence.get("repository_head") != repository_head
            or evidence.get("event_chain_head") != event_chain_head
            or not isinstance(evidence.get("payload_sha256"), str)
            or _SHA256.fullmatch(evidence["payload_sha256"]) is None
            or (
                evidence.get("observed_behavior") is not None
                and (
                    not isinstance(evidence.get("observed_behavior"), str)
                    or not evidence["observed_behavior"]
                )
            )
        ):
            _fail(
                BLOCK,
                EVIDENCE_APPLICABILITY_MISMATCH,
                "Runtime evidence identity or graph binding is invalid.",
            )
        payload = _strict_base64(evidence.get("payload_base64"))
        if _sha256(payload) != evidence.get("payload_sha256"):
            _fail(
                BLOCK,
                EVIDENCE_APPLICABILITY_MISMATCH,
                "Runtime evidence payload hash does not match.",
            )
        evidence["_payload"] = payload
        identities.add(evidence["evidence_id"])
        result.append(evidence)
    return tuple(result)


def _predicate_disposition(
    predicate: Mapping[str, Any],
    *,
    readback: TrustedManifestReadback,
) -> tuple[str, str | None]:
    projection = readback.projection
    scalar_fields = (
        ("execution_status_equals", "execution_status"),
        ("delta_state_equals", "delta_state"),
        ("current_gate_equals", "current_gate"),
    )
    for declared, observed in scalar_fields:
        expected = predicate.get(declared)
        if expected is not None and projection.get(observed) != expected:
            return BLOCK, NATIVE_GRAPH_CONTRADICTION
    expected_missing = predicate.get("missing_evidence_exact")
    if (
        expected_missing is not None
        and projection.get("missing_evidence") != expected_missing
    ):
        return BLOCK, NATIVE_GRAPH_CONTRADICTION
    inventory_types = {
        str(record.get("object_type")) for record in readback.current_inventory
    }
    for requirement in predicate.get("object_type_requirements", ()):
        present = requirement["object_type"] in inventory_types
        if (requirement["presence"] == "PRESENT") != present:
            return BLOCK, NATIVE_GRAPH_CONTRADICTION
    expected_boundary = predicate.get("generalized_boundary_equals")
    if (
        expected_boundary is not None
        and readback.current_e3.get("claim_boundary") != expected_boundary
    ):
        return BLOCK, NATIVE_GRAPH_CONTRADICTION
    return ALLOW, None


def _matching_evidence(
    span: Mapping[str, Any],
    evidence: Sequence[Mapping[str, Any]],
) -> tuple[str, str | None]:
    contract = span["evidence_contract"]
    candidates = [
        item for item in evidence if item.get("claim_id") == span.get("claim_id")
    ]
    if not candidates:
        return HOLD, MATCHING_EVIDENCE_REQUIRED
    applicable_type = [
        item
        for item in candidates
        if item.get("evidence_type")
        in contract["permitted_evidence_types"]
    ]
    if not applicable_type:
        if (
            span.get("claim_id")
            == "V13-S5-FR-001-README-DRAFT-000-CLAIM-012"
        ):
            return HOLD, MATCHING_EVIDENCE_REQUIRED
        return BLOCK, EVIDENCE_APPLICABILITY_MISMATCH
    for item in applicable_type:
        if (
            item.get("evidence_type")
            not in contract["permitted_evidence_types"]
            or item.get("verification_mode")
            != contract["required_verification_mode"]
            or item.get("boundary_id") != contract["required_boundary_id"]
            or item.get("observed_behavior")
            != contract["required_observed_behavior"]
        ):
            continue
        mode = contract["required_verification_mode"]
        if mode in {"DOCUMENTARY_BLOB_MATCH", "SOURCE_BLOB_MATCH"}:
            if item.get("_payload") != str(span["exact_text"]).encode("utf-8"):
                continue
        elif mode in {
            "ADVERSARIAL_BEHAVIOR_TEST",
            "RUNTIME_INTERCEPTION_TRACE",
        }:
            if not item.get("_payload"):
                continue
        return ALLOW, None
    return BLOCK, EVIDENCE_APPLICABILITY_MISMATCH


def _span_result(
    span: Mapping[str, Any],
    *,
    evidence: Sequence[Mapping[str, Any]],
    readback: TrustedManifestReadback,
) -> dict[str, Any]:
    identity = span.get("claim_id", span.get("span_id"))
    span_type = span["span_type"]
    result = {
        "disposition": ALLOW,
        "issue_code": None,
        "span_id": identity,
        "span_type": span_type,
    }
    if span_type in {"CLAIM", "OWNER_ATTESTED_NON_CLAIM"} and _visible_forbidden(
        str(span["exact_text"])
    ):
        result.update(
            {
                "disposition": BLOCK,
                "issue_code": VISIBLE_SPAN_FORBIDDEN_DECLARATION,
            }
        )
        return result
    if span_type != "CLAIM":
        return result

    predicate = span.get("native_graph_predicate")
    if predicate is not None:
        disposition, issue = _predicate_disposition(
            predicate,
            readback=readback,
        )
    else:
        disposition, issue = _matching_evidence(span, evidence)

    required_maturity = str(span.get("required_formal_run_maturity"))
    observed_maturity = str(readback.projection.get("delta_state"))
    observed_rank = _MATURITY.get(observed_maturity, -1)
    if (
        disposition == ALLOW
        and _MATURITY.get(required_maturity, 99) > observed_rank
    ):
        disposition, issue = HOLD, MATCHING_EVIDENCE_REQUIRED
    if disposition == ALLOW and span.get("qualifier_requirement") is not None:
        disposition, issue = REVISE_REQUIRED, QUALIFIER_REQUIRED
    result.update({"disposition": disposition, "issue_code": issue})
    return result


def _authorization_receipt(
    *,
    packet: Mapping[str, Any],
    readback: TrustedManifestReadback,
    decision_hash: str,
) -> dict[str, Any]:
    body = {
        "asset_identity": ASSET_IDENTITY,
        "asset_version": ASSET_VERSION,
        "authorized_surface_sha256": readback.record["surface_sha256"],
        "content_hash": readback.record["content_hash"],
        "decision_hash": decision_hash,
        "event_chain_head": readback.event_chain_head,
        "evaluation_id": packet["evaluation_id"],
        "manifest_hash": readback.record["manifest_hash"],
        "manifest_id": readback.record["manifest_id"],
        "owner_execution_authorization": packet[
            "owner_execution_authorization"
        ],
        "repository_head": readback.repository_head,
        "schema_version": AUTHORIZATION_RECEIPT_SCHEMA_VERSION,
    }
    return {**body, "receipt_sha256": _sha256(canonical_json(body))}


class PublicClaimManifestController:
    """Validate, delegate, read back, and evaluate native public sidecars."""

    def __init__(
        self,
        repository: Path,
        *,
        controller_factory: Callable[
            [Path], IntelligenceTransplantController
        ] = IntelligenceTransplantController,
    ) -> None:
        self.repository = Path(repository).resolve()
        self._controller_factory = controller_factory

    def _controller(self) -> IntelligenceTransplantController:
        return self._controller_factory(self.repository)

    def _read_native_state(
        self,
    ) -> tuple[
        IntelligenceTransplantController,
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        controller = self._controller()
        try:
            events = controller.store.read_events()
            records = [
                controller.store.read_record(
                    event["payload"]["blob_kind"],
                    event["payload"]["content_hash"],
                )
                for event in events
            ]
        except (IntelligenceTransplantBusyError, IntelligenceTransplantConflictError) as exc:
            raise PublicClaimGuardError(
                HOLD,
                MANIFEST_TRUST_EVIDENCE_INCOMPLETE,
                "The current native store is temporarily unavailable.",
            ) from exc
        except IntelligenceTransplantIntegrityError as exc:
            raise PublicClaimGuardError(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The current native store failed integrity verification.",
            ) from exc
        return controller, records, events

    def _trusted_readback(
        self,
        *,
        manifest_id: str,
        content_hash: str,
        manifest_hash: str,
        repository_head: str,
        event_chain_head: str | None,
    ) -> TrustedManifestReadback:
        controller, records, events = self._read_native_state()
        if not records:
            _fail(
                HOLD,
                MANIFEST_TRUST_EVIDENCE_INCOMPLETE,
                "No native records are available.",
            )
        graph = validate_graph(records)
        if not graph.valid:
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The current native graph is structurally invalid.",
            )
        observed_head = _repository_head(self.repository)
        if repository_head != observed_head:
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The requested repository HEAD is not current.",
            )
        actual_chain_head = (
            events[-1]["event_hash"] if events else "0" * 64
        )
        if (
            event_chain_head is not None
            and event_chain_head != actual_chain_head
        ):
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The requested event-chain head is not current.",
            )

        matching_hash = [
            record
            for record in records
            if record.get("content_hash") == content_hash
        ]
        if not matching_hash:
            _fail(
                HOLD,
                MANIFEST_TRUST_EVIDENCE_INCOMPLETE,
                "The requested Manifest payload is unavailable.",
            )
        if len(matching_hash) != 1:
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The requested Manifest hash is ambiguous.",
            )
        record = deepcopy(dict(matching_hash[0]))
        if (
            record.get("object_type") != PUBLIC_CLAIM_MANIFEST
            or record.get("object_id") != manifest_id
            or record.get("manifest_id") != manifest_id
            or record.get("content_hash") != content_hash
            or record.get("manifest_hash") != manifest_hash
            or content_hash != manifest_hash
            or compute_content_hash(record) != content_hash
        ):
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The requested Manifest triple or self-hash does not bind.",
            )
        canonical_record = canonical_json(record)
        reconstruct_surface(record)

        manifest_events = [
            event
            for event in events
            if event["kind"] == "MANIFEST_FROZEN"
            and event["payload"]["object_id"] == manifest_id
            and event["payload"]["content_hash"] == content_hash
        ]
        if len(manifest_events) != 1:
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "Exactly one Manifest freeze event was not found.",
            )
        manifest_event = deepcopy(manifest_events[0])
        event_payload = manifest_event["payload"]
        receipt = event_payload.get("transport_receipt")
        if not isinstance(receipt, Mapping):
            _fail(
                BLOCK,
                MANIFEST_TRANSPORT_BINDING_MISMATCH,
                "The Manifest transport receipt is absent.",
            )
        transport_payload = controller.store.read_transport(
            str(event_payload.get("transport_sha256"))
        )
        stored_receipt = controller.store.read_transport_receipt(
            str(receipt.get("receipt_sha256"))
        )
        if (
            event_payload.get("repository_head") != observed_head
            or record.get("repository_head") != observed_head
            or transport_payload != canonical_record
            or strict_json_object(transport_payload) != record
            or stored_receipt != receipt
            or event_payload.get("transport_sha256")
            != receipt.get("exact_payload_sha256")
            or receipt.get("declared_sha256")
            != receipt.get("exact_payload_sha256")
            or receipt.get("context_evidence_ref")
            != record.get("implementation_assignment_ref")
            or receipt.get("as_of") != record.get("as_of")
            or manifest_event.get("recorded_at") != record.get("as_of")
        ):
            _fail(
                BLOCK,
                MANIFEST_TRANSPORT_BINDING_MISMATCH,
                "Manifest event, payload, receipt, and record linkage differs.",
            )

        inventory = current_object_inventory(
            records,
            run_id=str(record.get("run_id")),
        )
        if _record_key(record) not in {_record_key(item) for item in inventory}:
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The requested Manifest is not current and non-revoked.",
            )
        e3, _ = _validate_current_authority(
            record,
            records,
            inventory,
            missing_disposition=HOLD,
        )
        selected_e3 = _select_chain(_current_records(records)).get("e3")
        if selected_e3 is None:
            _fail(
                HOLD,
                NATIVE_GRAPH_EVIDENCE_UNAVAILABLE,
                "The active native E3 cannot be resolved.",
            )
        if exact_ref(selected_e3) != exact_ref(e3):
            _fail(
                BLOCK,
                NATIVE_GRAPH_CONTRADICTION,
                "The Manifest does not bind the current exact E3.",
            )
        projection = reduce_evidence_graph(records).as_dict()
        if (
            projection.get("structural_validation") != "PASS"
            or not _sidecar_neutral_projection(records, projection)
        ):
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The sidecar changed native maturity projection.",
            )
        return TrustedManifestReadback(
            record=record,
            records=tuple(deepcopy(records)),
            events=tuple(deepcopy(events)),
            current_inventory=tuple(deepcopy(inventory)),
            current_e3=deepcopy(e3),
            projection=projection,
            repository_head=observed_head,
            event_chain_head=actual_chain_head,
            manifest_event=manifest_event,
            transport_payload=transport_payload,
            transport_receipt=deepcopy(dict(receipt)),
        )

    def _prewrite_validate(
        self,
        record: Mapping[str, Any],
        transport: Mapping[str, Any],
        repository_head: str,
    ) -> None:
        value = deepcopy(dict(record))
        local = validate_object(value)
        if (
            not local.valid
            or value.get("object_type") != PUBLIC_CLAIM_MANIFEST
            or value.get("manifest_schema_version") != MANIFEST_SCHEMA_VERSION
        ):
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The candidate Manifest failed strict native/public validation.",
            )
        reconstruct_surface(value)
        observed_head = _repository_head(self.repository)
        if (
            repository_head != observed_head
            or value.get("repository_head") != observed_head
        ):
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The candidate repository HEAD is not exact.",
            )
        _, records, _ = self._read_native_state()
        if not records:
            _fail(
                HOLD,
                MANIFEST_TRUST_EVIDENCE_INCOMPLETE,
                "The prerequisite native graph is unavailable.",
            )
        current_graph = validate_graph(records)
        if not current_graph.valid:
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The prerequisite native graph is invalid.",
            )
        inventory = current_object_inventory(
            records,
            run_id=str(value.get("run_id")),
        )
        _validate_current_authority(
            value,
            records,
            inventory,
            missing_disposition=HOLD,
        )
        proposed = validate_graph([*records, value])
        if not proposed.valid:
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The candidate native graph or forward lineage is invalid.",
            )
        try:
            payload, receipt = _transport_receipt(transport)
        except IntelligenceTransplantValidationError as exc:
            raise PublicClaimGuardError(
                BLOCK,
                MANIFEST_TRANSPORT_BINDING_MISMATCH,
                "The exact native transport receipt is invalid.",
            ) from exc
        if payload != canonical_json(value) or strict_json_object(payload) != value:
            _fail(
                BLOCK,
                MANIFEST_TRANSPORT_BINDING_MISMATCH,
                "The transport payload is not the canonical complete Manifest.",
            )
        if receipt.get("context_evidence_ref") != value.get(
            "implementation_assignment_ref"
        ):
            _fail(
                BLOCK,
                MANIFEST_TRANSPORT_AUTHORITY_MISMATCH,
                "The transport context is not the exact Implementation Seat.",
            )
        if receipt.get("as_of") != value.get("as_of"):
            _fail(
                BLOCK,
                MANIFEST_TRANSPORT_TIME_ORDER_INVALID,
                "The transport receipt time does not equal Manifest time.",
            )

    def freeze_manifest(
        self,
        record: Mapping[str, Any],
        *,
        transport: Mapping[str, Any],
        repository_head: str,
    ) -> dict[str, Any]:
        """Delegate one fully prevalidated freeze to the sole native writer."""

        self._prewrite_validate(record, transport, repository_head)
        controller = self._controller()
        try:
            controller.freeze_manifest(
                record,
                transport=transport,
                repository_head=repository_head,
            )
        except IntelligenceTransplantValidationError as exc:
            raise PublicClaimGuardError(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The native freeze route rejected the candidate.",
            ) from exc
        except (IntelligenceTransplantBusyError, IntelligenceTransplantConflictError) as exc:
            raise PublicClaimGuardError(
                HOLD,
                MANIFEST_TRUST_EVIDENCE_INCOMPLETE,
                "The native freeze transaction could not establish stable state.",
            ) from exc
        value = dict(record)
        readback = self._trusted_readback(
            manifest_id=str(value.get("manifest_id")),
            content_hash=str(value.get("content_hash")),
            manifest_hash=str(value.get("manifest_hash")),
            repository_head=repository_head,
            event_chain_head=None,
        )
        return {
            "event_chain_head": readback.event_chain_head,
            "manifest": deepcopy(readback.record),
            "projection": deepcopy(readback.projection),
            "repository_head": readback.repository_head,
            "transport_receipt": deepcopy(readback.transport_receipt),
        }

    def evaluate(self, packet: Mapping[str, Any]) -> dict[str, Any]:
        """Evaluate one strict runtime packet after a fresh trusted readback."""

        if not isinstance(packet, Mapping) or set(packet) != _EVALUATION_FIELDS:
            _fail(
                BLOCK,
                RUNTIME_OVERRIDE_ATTEMPT,
                "The runtime packet contains missing or unapproved fields.",
            )
        value = deepcopy(dict(packet))
        if (
            value.get("schema_version") != EVALUATION_SCHEMA_VERSION
            or not isinstance(value.get("evaluation_id"), str)
            or _SAFE_ID.fullmatch(value["evaluation_id"]) is None
            or not isinstance(value.get("manifest_id"), str)
            or _SAFE_ID.fullmatch(value["manifest_id"]) is None
            or not isinstance(value.get("content_hash"), str)
            or _SHA256.fullmatch(value["content_hash"]) is None
            or not isinstance(value.get("manifest_hash"), str)
            or _SHA256.fullmatch(value["manifest_hash"]) is None
            or not isinstance(value.get("repository_head"), str)
            or _COMMIT.fullmatch(value["repository_head"]) is None
            or not isinstance(value.get("event_chain_head"), str)
            or _SHA256.fullmatch(value["event_chain_head"]) is None
            or not isinstance(value.get("owner_execution_authorization"), str)
            or not value["owner_execution_authorization"].strip()
        ):
            _fail(
                BLOCK,
                RUNTIME_OVERRIDE_ATTEMPT,
                "The runtime packet identity is invalid.",
            )
        readback = self._trusted_readback(
            manifest_id=value["manifest_id"],
            content_hash=value["content_hash"],
            manifest_hash=value["manifest_hash"],
            repository_head=value["repository_head"],
            event_chain_head=value["event_chain_head"],
        )
        supplied_surface = _strict_base64(value.get("surface_base64"))
        if supplied_surface != reconstruct_surface(readback.record):
            _fail(
                BLOCK,
                MANIFEST_TRUST_BINDING_MISMATCH,
                "The supplied surface differs from the frozen Manifest.",
            )
        evidence = _normalize_evidence(
            value.get("evidence"),
            repository_head=readback.repository_head,
            event_chain_head=readback.event_chain_head,
        )
        known_claims = {
            str(span.get("claim_id"))
            for span in readback.record["spans"]
            if span.get("span_type") == "CLAIM"
        }
        if any(item["claim_id"] not in known_claims for item in evidence):
            _fail(
                BLOCK,
                EVIDENCE_APPLICABILITY_MISMATCH,
                "Evidence targets a claim outside the frozen Manifest.",
            )
        span_results = [
            _span_result(span, evidence=evidence, readback=readback)
            for span in readback.record["spans"]
        ]
        aggregate = max(
            (item["disposition"] for item in span_results),
            key=lambda item: _SEVERITY[item],
        )
        issues: list[str] = []
        for item in span_results:
            issue = item["issue_code"]
            if isinstance(issue, str) and issue not in issues:
                issues.append(issue)
        result_body = {
            "aggregate_disposition": aggregate,
            "authorization_status": (
                "AUTHORIZED" if aggregate == ALLOW else "NOT_AUTHORIZED"
            ),
            "content_hash": readback.record["content_hash"],
            "evaluation_id": value["evaluation_id"],
            "event_chain_head": readback.event_chain_head,
            "issue_codes": issues,
            "manifest_hash": readback.record["manifest_hash"],
            "manifest_id": readback.record["manifest_id"],
            "projection": {
                key: deepcopy(readback.projection[key])
                for key in (
                    "current_gate",
                    "delta_state",
                    "execution_status",
                    "missing_evidence",
                )
            },
            "repository_head": readback.repository_head,
            "schema_version": RESULT_SCHEMA_VERSION,
            "span_results": span_results,
            "surface_id": readback.record["surface_id"],
            "surface_sha256": readback.record["surface_sha256"],
        }
        decision_hash = _sha256(canonical_json(result_body))
        receipt = (
            _authorization_receipt(
                packet=value,
                readback=readback,
                decision_hash=decision_hash,
            )
            if aggregate == ALLOW
            else None
        )
        return {
            **result_body,
            "authorization_receipt": receipt,
            "decision_hash": decision_hash,
        }


def evaluation_exit_code(result: Mapping[str, Any]) -> int:
    """Map one verified aggregate disposition to the stable CLI contract."""

    disposition = result.get("aggregate_disposition")
    if disposition == ALLOW:
        return 0
    if disposition in {REVISE_REQUIRED, HOLD}:
        return 4
    if disposition == BLOCK:
        return 5
    return 6


def parse_evaluation_packet(raw: bytes | str) -> dict[str, Any]:
    """Parse exactly one strict runtime JSON object."""

    return strict_json_object(raw)


__all__ = [
    "ALLOW",
    "ASSET_IDENTITY",
    "ASSET_TYPE",
    "ASSET_VERSION",
    "BLOCK",
    "EVALUATION_SCHEMA_VERSION",
    "HOLD",
    "PublicClaimGuardError",
    "PublicClaimManifestController",
    "REVISE_REQUIRED",
    "current_object_inventory",
    "evaluation_exit_code",
    "parse_evaluation_packet",
    "reconstruct_surface",
]
