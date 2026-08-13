"""Authenticated live authority and durable mutation-capsule records for F-01.

This module deliberately provides only a repository/software boundary.  The
HMAC key must arrive from outside the protected repository and Broker journal;
protecting that key from an equivalent local process is a later OS deployment
gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import hmac
import time
from typing import Any

from decision_os.acceleration.model import canonical_json, hash_payload


MUTATION_CAPSULE_SCHEMA = "decision-os-broker-mutation-capsule-v0.1"
EXECUTION_ENVELOPE_SCHEMA = "decision-os-broker-execution-envelope-v0.1"
MAX_ENVELOPE_VALIDITY_SECONDS = 5 * 60
MAX_AUTHENTICATION_SECRET_BYTES = 4_096
MIN_AUTHENTICATION_SECRET_BYTES = 32
MAX_CAPSULE_BYTES = 32 * 1024
MAX_CAPSULES = 4_096
_MAX_IDENTITY_BYTES = 256
_MAX_RELATIVE_PATH_BYTES = 4_096
_MAX_TARGET_BYTES = 16 * 1024 * 1024
_MAX_KEY_VERSION = (1 << 31) - 1
_MAX_GENERATION_WITNESS = (1 << 64) - 1
_SHA256_LENGTH = 64

_CAPSULE_FIELDS = frozenset(
    {
        "schema",
        "authority_domain_id",
        "activation_sha256",
        "control_record_sha256",
        "repository_id",
        "protected_repository_identity",
        "write_principal_identity",
        "generation_witness",
        "operation",
        "relative_path",
        "expected_prior_sha256",
        "expected_post_sha256",
        "target_byte_count",
        "target_blob_sha256",
        "proposal_acquisition_sha256",
        "decision_sha256",
        "external_envelope_id",
        "external_envelope_nonce",
        "external_authorization_sha256",
        "capsule_sha256",
    }
)

_ENVELOPE_FIELDS = frozenset(
    {
        "schema",
        "envelope_id",
        "nonce",
        "authority_domain_id",
        "activation_sha256",
        "control_record_sha256",
        "repository_id",
        "protected_repository_identity",
        "write_principal_identity",
        "generation_witness",
        "decision_sha256",
        "capsule_sha256",
        "operation",
        "relative_path",
        "expected_prior_sha256",
        "expected_post_sha256",
        "target_byte_count",
        "proposal_acquisition_sha256",
        "issued_at_unix",
        "expires_at_unix",
        "bootstrap_activation_evidence_id",
        "bootstrap_activation_evidence_sha256",
        "human_seat_authorization_evidence_id",
        "human_seat_authorization_evidence_sha256",
        "authentication_key_id",
        "authentication_key_version",
        "authentication_hmac_sha256",
    }
)


class BrokerAuthorityError(RuntimeError):
    """Authenticated authority or capsule evidence failed closed."""


class EnvelopeAuthenticationError(BrokerAuthorityError):
    """An external execution envelope is absent, invalid, stale, or forged."""


class MutationCapsuleIntegrityError(BrokerAuthorityError):
    """A durable mutation capsule or its content blob is unprovable."""


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == _SHA256_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_sha256(value: Any, label: str) -> str:
    if not _is_sha256(value):
        raise ValueError(f"{label} must be one lowercase SHA-256 digest.")
    return value


def _bounded_identity(value: Any, label: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{label} must be one non-empty plain string.")
    try:
        encoded = value.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError(f"{label} must be valid UTF-8.") from exc
    if len(encoded) > _MAX_IDENTITY_BYTES:
        raise ValueError(f"{label} exceeds its bounded size limit.")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        raise ValueError(f"{label} cannot contain control characters.")
    return value


def _hex_nonce(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 32
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be 128 bits of lowercase hexadecimal.")
    return value


def _repository_identity(value: Any) -> str:
    result = _bounded_identity(value, "Repository identity")
    prefix = "repo:v1:"
    if not result.startswith(prefix) or not _is_sha256(result[len(prefix) :]):
        raise ValueError(
            "Repository identity must be a versioned lowercase SHA-256 identity."
        )
    return result


def _relative_path(value: Any) -> str:
    # MutationDecision owns the complete path grammar.  Capsule/envelope
    # parsing still bounds the scalar before reconstruction revalidates it.
    if type(value) is not str or not value or "\x00" in value:
        raise ValueError("Relative target path is invalid.")
    try:
        encoded = value.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError("Relative target path must be valid UTF-8.") from exc
    if len(encoded) > _MAX_RELATIVE_PATH_BYTES:
        raise ValueError("Relative target path exceeds its bounded size limit.")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        raise ValueError("Relative target path contains control characters.")
    return value


def _activation_dict(value: Any) -> dict[str, Any]:
    return {
        "authority_domain_id": value.authority_domain_id,
        "repository_id": value.repository_id,
        "protected_repository_identity": value.protected_repository_identity,
        "write_principal_identity": value.write_principal_identity,
        "generation_witness": value.generation_witness,
    }


def decision_sha256(decision: Any) -> str:
    """Return the canonical mutation-decision binding digest."""

    from decision_os.companion.broker_control import MutationDecision

    if type(decision) is not MutationDecision:
        raise MutationCapsuleIntegrityError(
            "A capsule requires one exact mutation decision."
        )
    try:
        return hash_payload(MutationDecision.binding_dict(decision))
    except (AttributeError, TypeError, ValueError) as exc:
        raise MutationCapsuleIntegrityError(
            "A capsule requires one exact mutation decision."
        ) from exc


def activation_sha256(activation: Any) -> str:
    """Return the canonical complete activation-tuple digest."""

    from decision_os.companion.broker_control import ActivationTuple

    if type(activation) is not ActivationTuple:
        raise MutationCapsuleIntegrityError(
            "A capsule requires one exact activation tuple."
        )
    try:
        ActivationTuple.__post_init__(activation)
        return hash_payload(_activation_dict(activation))
    except (AttributeError, TypeError, ValueError) as exc:
        raise MutationCapsuleIntegrityError(
            "A capsule requires one exact activation tuple."
        ) from exc


@dataclass(frozen=True)
class EnvelopeAuthenticationKey:
    """External HMAC trust material; never serialized into Broker evidence."""

    key_id: str
    key_version: int
    secret: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if type(self) is not EnvelopeAuthenticationKey:
            raise ValueError("Authentication-key subclasses are forbidden.")
        _bounded_identity(self.key_id, "Authentication key identity")
        if (
            type(self.key_version) is not int
            or not 1 <= self.key_version <= _MAX_KEY_VERSION
        ):
            raise ValueError("Authentication key version is invalid.")
        if type(self.secret) is not bytes or not (
            MIN_AUTHENTICATION_SECRET_BYTES
            <= len(self.secret)
            <= MAX_AUTHENTICATION_SECRET_BYTES
        ):
            raise ValueError(
                "Authentication secret must be bounded external bytes with at "
                "least 256 bits."
            )


@dataclass(frozen=True)
class AuthenticatedExecutionEnvelope:
    """One exact-scope, time-bounded, externally authenticated live authority."""

    schema: str
    envelope_id: str
    nonce: str
    authority_domain_id: str
    activation_sha256: str
    control_record_sha256: str
    repository_id: str
    protected_repository_identity: str
    write_principal_identity: str
    generation_witness: int
    decision_sha256: str
    capsule_sha256: str
    operation: str
    relative_path: str
    expected_prior_sha256: str | None
    expected_post_sha256: str
    target_byte_count: int
    proposal_acquisition_sha256: str
    issued_at_unix: int
    expires_at_unix: int
    bootstrap_activation_evidence_id: str
    bootstrap_activation_evidence_sha256: str
    human_seat_authorization_evidence_id: str
    human_seat_authorization_evidence_sha256: str
    authentication_key_id: str
    authentication_key_version: int
    authentication_hmac_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not AuthenticatedExecutionEnvelope:
            raise ValueError("Execution-envelope subclasses are forbidden.")
        self._validate_fields()

    def _validate_fields(self) -> None:
        if type(self.schema) is not str or self.schema != EXECUTION_ENVELOPE_SCHEMA:
            raise ValueError("Execution-envelope schema is invalid.")
        _hex_nonce(self.envelope_id, "Execution envelope identity")
        _hex_nonce(self.nonce, "Execution envelope nonce")
        if self.envelope_id == self.nonce:
            raise ValueError("Execution envelope identity and nonce must be distinct.")
        _bounded_identity(self.authority_domain_id, "Authority-domain identity")
        _require_sha256(self.activation_sha256, "Activation hash")
        _require_sha256(self.control_record_sha256, "Control-record hash")
        _repository_identity(self.repository_id)
        _bounded_identity(
            self.protected_repository_identity,
            "Protected-repository identity",
        )
        _bounded_identity(self.write_principal_identity, "Write-principal identity")
        if (
            type(self.generation_witness) is not int
            or not 0 <= self.generation_witness <= _MAX_GENERATION_WITNESS
        ):
            raise ValueError("Generation witness is invalid.")
        _require_sha256(self.decision_sha256, "Decision hash")
        _require_sha256(self.capsule_sha256, "Capsule hash")
        if type(self.operation) is not str or self.operation not in {
            "CREATE",
            "REPLACE",
        }:
            raise ValueError("Execution-envelope operation is invalid.")
        _relative_path(self.relative_path)
        if self.operation == "CREATE":
            if self.expected_prior_sha256 is not None:
                raise ValueError("CREATE envelope requires an absent prior image.")
        else:
            _require_sha256(self.expected_prior_sha256, "Prior-image hash")
        _require_sha256(self.expected_post_sha256, "Post-image hash")
        if (
            type(self.target_byte_count) is not int
            or not 0 <= self.target_byte_count <= _MAX_TARGET_BYTES
        ):
            raise ValueError("Execution-envelope target byte count is invalid.")
        _require_sha256(
            self.proposal_acquisition_sha256,
            "Proposal-acquisition hash",
        )
        if (
            type(self.issued_at_unix) is not int
            or type(self.expires_at_unix) is not int
            or self.issued_at_unix < 0
            or self.expires_at_unix <= self.issued_at_unix
            or self.expires_at_unix - self.issued_at_unix
            > MAX_ENVELOPE_VALIDITY_SECONDS
        ):
            raise ValueError("Execution-envelope validity interval is invalid.")
        _bounded_identity(
            self.bootstrap_activation_evidence_id,
            "Bootstrap activation evidence identity",
        )
        _require_sha256(
            self.bootstrap_activation_evidence_sha256,
            "Bootstrap activation evidence hash",
        )
        _bounded_identity(
            self.human_seat_authorization_evidence_id,
            "Human Seat authorization evidence identity",
        )
        _require_sha256(
            self.human_seat_authorization_evidence_sha256,
            "Human Seat authorization evidence hash",
        )
        _bounded_identity(self.authentication_key_id, "Authentication key identity")
        if (
            type(self.authentication_key_version) is not int
            or not 1 <= self.authentication_key_version <= _MAX_KEY_VERSION
        ):
            raise ValueError("Authentication key version is invalid.")
        _require_sha256(self.authentication_hmac_sha256, "Envelope HMAC")

    def payload_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "envelope_id": self.envelope_id,
            "nonce": self.nonce,
            "authority_domain_id": self.authority_domain_id,
            "activation_sha256": self.activation_sha256,
            "control_record_sha256": self.control_record_sha256,
            "repository_id": self.repository_id,
            "protected_repository_identity": self.protected_repository_identity,
            "write_principal_identity": self.write_principal_identity,
            "generation_witness": self.generation_witness,
            "decision_sha256": self.decision_sha256,
            "capsule_sha256": self.capsule_sha256,
            "operation": self.operation,
            "relative_path": self.relative_path,
            "expected_prior_sha256": self.expected_prior_sha256,
            "expected_post_sha256": self.expected_post_sha256,
            "target_byte_count": self.target_byte_count,
            "proposal_acquisition_sha256": self.proposal_acquisition_sha256,
            "issued_at_unix": self.issued_at_unix,
            "expires_at_unix": self.expires_at_unix,
            "bootstrap_activation_evidence_id": (
                self.bootstrap_activation_evidence_id
            ),
            "bootstrap_activation_evidence_sha256": (
                self.bootstrap_activation_evidence_sha256
            ),
            "human_seat_authorization_evidence_id": (
                self.human_seat_authorization_evidence_id
            ),
            "human_seat_authorization_evidence_sha256": (
                self.human_seat_authorization_evidence_sha256
            ),
            "authentication_key_id": self.authentication_key_id,
            "authentication_key_version": self.authentication_key_version,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.payload_dict(),
            "authentication_hmac_sha256": self.authentication_hmac_sha256,
        }

    def authorization_identity_dict(self) -> dict[str, Any]:
        """Return non-circular authority identity bound into the capsule."""

        payload = self.payload_dict()
        del payload["capsule_sha256"]
        return payload

    def authorization_identity_sha256(self) -> str:
        return hash_payload(self.authorization_identity_dict())

    @classmethod
    def from_dict(cls, value: Any) -> "AuthenticatedExecutionEnvelope":
        if type(value) is not dict or set(value) != _ENVELOPE_FIELDS:
            raise EnvelopeAuthenticationError(
                "Execution-envelope fields are invalid."
            )
        try:
            return cls(**value)
        except (KeyError, TypeError, ValueError) as exc:
            raise EnvelopeAuthenticationError(
                "Execution-envelope structure is invalid."
            ) from exc


@dataclass(frozen=True)
class MutationCapsule:
    """One immutable durable reconstruction of an accepted mutation decision."""

    schema: str
    authority_domain_id: str
    activation_sha256: str
    control_record_sha256: str
    repository_id: str
    protected_repository_identity: str
    write_principal_identity: str
    generation_witness: int
    operation: str
    relative_path: str
    expected_prior_sha256: str | None
    expected_post_sha256: str
    target_byte_count: int
    target_blob_sha256: str
    proposal_acquisition_sha256: str
    decision_sha256: str
    external_envelope_id: str
    external_envelope_nonce: str
    external_authorization_sha256: str
    capsule_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not MutationCapsule:
            raise ValueError("Mutation-capsule subclasses are forbidden.")
        self._validate_fields()

    def _validate_fields(self) -> None:
        if type(self.schema) is not str or self.schema != MUTATION_CAPSULE_SCHEMA:
            raise ValueError("Mutation-capsule schema is invalid.")
        _bounded_identity(self.authority_domain_id, "Authority-domain identity")
        _require_sha256(self.activation_sha256, "Activation hash")
        _require_sha256(self.control_record_sha256, "Control-record hash")
        _repository_identity(self.repository_id)
        _bounded_identity(
            self.protected_repository_identity,
            "Protected-repository identity",
        )
        _bounded_identity(self.write_principal_identity, "Write-principal identity")
        if (
            type(self.generation_witness) is not int
            or not 0 <= self.generation_witness <= _MAX_GENERATION_WITNESS
        ):
            raise ValueError("Generation witness is invalid.")
        if type(self.operation) is not str or self.operation not in {
            "CREATE",
            "REPLACE",
        }:
            raise ValueError("Mutation-capsule operation is invalid.")
        _relative_path(self.relative_path)
        if self.operation == "CREATE":
            if self.expected_prior_sha256 is not None:
                raise ValueError("CREATE capsule requires an absent prior image.")
        else:
            _require_sha256(self.expected_prior_sha256, "Prior-image hash")
        _require_sha256(self.expected_post_sha256, "Post-image hash")
        if (
            type(self.target_byte_count) is not int
            or not 0 <= self.target_byte_count <= _MAX_TARGET_BYTES
        ):
            raise ValueError("Mutation-capsule target byte count is invalid.")
        _require_sha256(self.target_blob_sha256, "Target-blob hash")
        if self.target_blob_sha256 != self.expected_post_sha256:
            raise ValueError("Target blob and post-image hashes mismatch.")
        _require_sha256(
            self.proposal_acquisition_sha256,
            "Proposal-acquisition hash",
        )
        _require_sha256(self.decision_sha256, "Decision hash")
        _hex_nonce(self.external_envelope_id, "External envelope identity")
        _hex_nonce(self.external_envelope_nonce, "External envelope nonce")
        if self.external_envelope_id == self.external_envelope_nonce:
            raise ValueError("External envelope identity and nonce must be distinct.")
        _require_sha256(
            self.external_authorization_sha256,
            "External authorization hash",
        )
        _require_sha256(self.capsule_sha256, "Capsule hash")

    def payload_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "authority_domain_id": self.authority_domain_id,
            "activation_sha256": self.activation_sha256,
            "control_record_sha256": self.control_record_sha256,
            "repository_id": self.repository_id,
            "protected_repository_identity": self.protected_repository_identity,
            "write_principal_identity": self.write_principal_identity,
            "generation_witness": self.generation_witness,
            "operation": self.operation,
            "relative_path": self.relative_path,
            "expected_prior_sha256": self.expected_prior_sha256,
            "expected_post_sha256": self.expected_post_sha256,
            "target_byte_count": self.target_byte_count,
            "target_blob_sha256": self.target_blob_sha256,
            "proposal_acquisition_sha256": self.proposal_acquisition_sha256,
            "decision_sha256": self.decision_sha256,
            "external_envelope_id": self.external_envelope_id,
            "external_envelope_nonce": self.external_envelope_nonce,
            "external_authorization_sha256": self.external_authorization_sha256,
        }

    def as_dict(self) -> dict[str, Any]:
        return {**self.payload_dict(), "capsule_sha256": self.capsule_sha256}

    @classmethod
    def from_dict(cls, value: Any) -> "MutationCapsule":
        if type(value) is not dict or set(value) != _CAPSULE_FIELDS:
            raise MutationCapsuleIntegrityError(
                "Persisted mutation-capsule fields are invalid."
            )
        try:
            capsule = cls(**value)
        except (KeyError, TypeError, ValueError) as exc:
            raise MutationCapsuleIntegrityError(
                "Persisted mutation-capsule structure is invalid."
            ) from exc
        if capsule.capsule_sha256 != hash_payload(capsule.payload_dict()):
            raise MutationCapsuleIntegrityError(
                "Persisted mutation-capsule hash mismatches."
            )
        return capsule

    def reconstruct_decision(self, target_bytes: bytes) -> Any:
        """Reconstruct and revalidate the exact accepted decision."""

        from decision_os.companion.broker_control import (
            ActivationTuple,
            MutationDecision,
            MutationOperation,
        )

        if type(target_bytes) is not bytes:
            raise MutationCapsuleIntegrityError(
                "Mutation-capsule target blob must contain exact bytes."
            )
        if (
            len(target_bytes) != self.target_byte_count
            or hashlib.sha256(target_bytes).hexdigest() != self.target_blob_sha256
        ):
            raise MutationCapsuleIntegrityError(
                "Mutation-capsule target blob size or hash mismatches."
            )
        try:
            activation = ActivationTuple(
                authority_domain_id=self.authority_domain_id,
                repository_id=self.repository_id,
                protected_repository_identity=self.protected_repository_identity,
                write_principal_identity=self.write_principal_identity,
                generation_witness=self.generation_witness,
            )
            decision = MutationDecision(
                activation=activation,
                operation=MutationOperation(self.operation),
                relative_path=self.relative_path,
                target_bytes=target_bytes,
                expected_prior_sha256=self.expected_prior_sha256,
                expected_post_sha256=self.expected_post_sha256,
                proposal_acquisition_sha256=self.proposal_acquisition_sha256,
            )
        except (TypeError, ValueError) as exc:
            raise MutationCapsuleIntegrityError(
                "Mutation capsule cannot reconstruct an exact decision."
            ) from exc
        if (
            activation_sha256(decision.activation) != self.activation_sha256
            or decision_sha256(decision) != self.decision_sha256
        ):
            raise MutationCapsuleIntegrityError(
                "Reconstructed mutation decision mismatches its capsule."
            )
        return decision


def canonical_capsule_bytes(capsule: MutationCapsule) -> bytes:
    if type(capsule) is not MutationCapsule:
        raise MutationCapsuleIntegrityError(
            "Mutation capsule must be one exact immutable record."
        )
    try:
        MutationCapsule.__post_init__(capsule)
    except ValueError as exc:
        raise MutationCapsuleIntegrityError(
            "Mutation-capsule runtime fields are invalid."
        ) from exc
    if capsule.capsule_sha256 != hash_payload(capsule.payload_dict()):
        raise MutationCapsuleIntegrityError(
            "Mutation-capsule runtime hash mismatches."
        )
    encoded = (canonical_json(capsule.as_dict()) + "\n").encode("utf-8")
    if len(encoded) > MAX_CAPSULE_BYTES:
        raise MutationCapsuleIntegrityError(
            "Mutation capsule exceeds its bounded size limit."
        )
    return encoded


def parse_capsule_bytes(raw: bytes) -> MutationCapsule:
    import json

    if type(raw) is not bytes or len(raw) > MAX_CAPSULE_BYTES:
        raise MutationCapsuleIntegrityError(
            "Persisted mutation capsule is oversized or unreadable."
        )
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise MutationCapsuleIntegrityError(
            "Persisted mutation capsule is unreadable."
        ) from exc
    capsule = MutationCapsule.from_dict(value)
    if raw != canonical_capsule_bytes(capsule):
        raise MutationCapsuleIntegrityError(
            "Persisted mutation capsule is not canonical."
        )
    return capsule


def _capsule_payload(
    decision: Any,
    control_record: Any,
    envelope: AuthenticatedExecutionEnvelope,
) -> dict[str, Any]:
    from decision_os.companion.broker_control import (
        ControlDomainRecord,
        MutationDecision,
    )

    if type(decision) is not MutationDecision or type(control_record) is not ControlDomainRecord:
        raise MutationCapsuleIntegrityError(
            "Capsule creation requires exact decision and control records."
        )
    if type(envelope) is not AuthenticatedExecutionEnvelope:
        raise MutationCapsuleIntegrityError(
            "Capsule creation requires one exact external envelope."
        )
    proposal_hash = decision.proposal_acquisition_sha256
    if not _is_sha256(proposal_hash):
        raise MutationCapsuleIntegrityError(
            "A live mutation capsule requires fd-acquisition provenance."
        )
    return {
        "schema": MUTATION_CAPSULE_SCHEMA,
        "authority_domain_id": decision.activation.authority_domain_id,
        "activation_sha256": activation_sha256(decision.activation),
        "control_record_sha256": control_record.record_sha256,
        "repository_id": decision.activation.repository_id,
        "protected_repository_identity": (
            decision.activation.protected_repository_identity
        ),
        "write_principal_identity": decision.activation.write_principal_identity,
        "generation_witness": decision.activation.generation_witness,
        "operation": decision.operation.value,
        "relative_path": decision.relative_path,
        "expected_prior_sha256": decision.expected_prior_sha256,
        "expected_post_sha256": decision.expected_post_sha256,
        "target_byte_count": len(decision.target_bytes),
        "target_blob_sha256": hashlib.sha256(decision.target_bytes).hexdigest(),
        "proposal_acquisition_sha256": proposal_hash,
        "decision_sha256": decision_sha256(decision),
        "external_envelope_id": envelope.envelope_id,
        "external_envelope_nonce": envelope.nonce,
        "external_authorization_sha256": (
            envelope.authorization_identity_sha256()
        ),
    }


def mutation_capsule_for(
    decision: Any,
    control_record: Any,
    envelope: AuthenticatedExecutionEnvelope,
) -> MutationCapsule:
    payload = _capsule_payload(decision, control_record, envelope)
    payload["capsule_sha256"] = hash_payload(payload)
    try:
        return MutationCapsule.from_dict(payload)
    except MutationCapsuleIntegrityError:
        raise
    except (TypeError, ValueError) as exc:
        raise MutationCapsuleIntegrityError(
            "Mutation capsule cannot be constructed safely."
        ) from exc


def _unsigned_envelope_payload(
    decision: Any,
    control_record: Any,
    *,
    envelope_id: str,
    nonce: str,
    issued_at_unix: int,
    expires_at_unix: int,
    bootstrap_activation_evidence_id: str,
    bootstrap_activation_evidence_sha256: str,
    human_seat_authorization_evidence_id: str,
    human_seat_authorization_evidence_sha256: str,
    authentication_key: EnvelopeAuthenticationKey,
) -> dict[str, Any]:
    from decision_os.companion.broker_control import (
        ControlDomainRecord,
        ControlDomainState,
        MutationDecision,
    )

    if type(decision) is not MutationDecision or type(control_record) is not ControlDomainRecord:
        raise EnvelopeAuthenticationError(
            "Envelope issuance requires exact decision and control records."
        )
    if type(authentication_key) is not EnvelopeAuthenticationKey:
        raise EnvelopeAuthenticationError(
            "Envelope issuance requires exact external authentication material."
        )
    if control_record.state is not ControlDomainState.ACTIVE:
        raise EnvelopeAuthenticationError(
            "An envelope can bind only the current ACTIVE control record."
        )
    if control_record.activation != decision.activation:
        raise EnvelopeAuthenticationError(
            "Envelope decision does not match the bound control record."
        )
    try:
        return {
            "schema": EXECUTION_ENVELOPE_SCHEMA,
            "envelope_id": _hex_nonce(envelope_id, "Execution envelope identity"),
            "nonce": _hex_nonce(nonce, "Execution envelope nonce"),
            "authority_domain_id": decision.activation.authority_domain_id,
            "activation_sha256": activation_sha256(decision.activation),
            "control_record_sha256": control_record.record_sha256,
            "repository_id": decision.activation.repository_id,
            "protected_repository_identity": (
                decision.activation.protected_repository_identity
            ),
            "write_principal_identity": (
                decision.activation.write_principal_identity
            ),
            "generation_witness": decision.activation.generation_witness,
            "decision_sha256": decision_sha256(decision),
            "operation": decision.operation.value,
            "relative_path": decision.relative_path,
            "expected_prior_sha256": decision.expected_prior_sha256,
            "expected_post_sha256": decision.expected_post_sha256,
            "target_byte_count": len(decision.target_bytes),
            "proposal_acquisition_sha256": (
                decision.proposal_acquisition_sha256
            ),
            "issued_at_unix": issued_at_unix,
            "expires_at_unix": expires_at_unix,
            "bootstrap_activation_evidence_id": (
                bootstrap_activation_evidence_id
            ),
            "bootstrap_activation_evidence_sha256": (
                bootstrap_activation_evidence_sha256
            ),
            "human_seat_authorization_evidence_id": (
                human_seat_authorization_evidence_id
            ),
            "human_seat_authorization_evidence_sha256": (
                human_seat_authorization_evidence_sha256
            ),
            "authentication_key_id": authentication_key.key_id,
            "authentication_key_version": authentication_key.key_version,
        }
    except (AttributeError, TypeError, ValueError) as exc:
        raise EnvelopeAuthenticationError(
            "Execution-envelope scope is invalid."
        ) from exc


def issue_execution_envelope(
    decision: Any,
    control_record: Any,
    *,
    authentication_key: EnvelopeAuthenticationKey,
    envelope_id: str,
    nonce: str,
    issued_at_unix: int,
    expires_at_unix: int,
    bootstrap_activation_evidence_id: str,
    bootstrap_activation_evidence_sha256: str,
    human_seat_authorization_evidence_id: str,
    human_seat_authorization_evidence_sha256: str,
) -> AuthenticatedExecutionEnvelope:
    """Sign one exact live scope with externally supplied HMAC key material."""

    base = _unsigned_envelope_payload(
        decision,
        control_record,
        envelope_id=envelope_id,
        nonce=nonce,
        issued_at_unix=issued_at_unix,
        expires_at_unix=expires_at_unix,
        bootstrap_activation_evidence_id=bootstrap_activation_evidence_id,
        bootstrap_activation_evidence_sha256=(
            bootstrap_activation_evidence_sha256
        ),
        human_seat_authorization_evidence_id=(
            human_seat_authorization_evidence_id
        ),
        human_seat_authorization_evidence_sha256=(
            human_seat_authorization_evidence_sha256
        ),
        authentication_key=authentication_key,
    )
    # Build the non-circular capsule identity from the envelope authority
    # fields, then bind that exact digest into the authenticated payload.
    placeholder = {
        **base,
        "capsule_sha256": "0" * _SHA256_LENGTH,
        "authentication_hmac_sha256": "0" * _SHA256_LENGTH,
    }
    try:
        provisional = AuthenticatedExecutionEnvelope(**placeholder)
    except ValueError as exc:
        raise EnvelopeAuthenticationError(
            "Execution-envelope fields are invalid."
        ) from exc
    capsule = mutation_capsule_for(decision, control_record, provisional)
    payload = {**base, "capsule_sha256": capsule.capsule_sha256}
    tag = hmac.new(
        authentication_key.secret,
        canonical_json(payload).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    try:
        return AuthenticatedExecutionEnvelope(
            **payload,
            authentication_hmac_sha256=tag,
        )
    except ValueError as exc:
        raise EnvelopeAuthenticationError(
            "Execution-envelope fields are invalid."
        ) from exc


def verify_envelope_authentication(
    envelope: Any,
    authentication_key: Any,
) -> AuthenticatedExecutionEnvelope:
    """Authenticate one exact envelope against external key material and time."""

    if type(envelope) is not AuthenticatedExecutionEnvelope:
        raise EnvelopeAuthenticationError(
            "Live apply requires one exact authenticated execution envelope."
        )
    if type(authentication_key) is not EnvelopeAuthenticationKey:
        raise EnvelopeAuthenticationError(
            "Live apply requires exact external authentication material."
        )
    try:
        snapshot = AuthenticatedExecutionEnvelope.from_dict(envelope.as_dict())
    except (AttributeError, TypeError, ValueError) as exc:
        raise EnvelopeAuthenticationError(
            "Execution envelope is invalid or was mutated."
        ) from exc
    if (
        snapshot.authentication_key_id != authentication_key.key_id
        or snapshot.authentication_key_version != authentication_key.key_version
    ):
        raise EnvelopeAuthenticationError(
            "Execution envelope names different authentication material."
        )
    expected = hmac.new(
        authentication_key.secret,
        canonical_json(snapshot.payload_dict()).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, snapshot.authentication_hmac_sha256):
        raise EnvelopeAuthenticationError(
            "Execution-envelope authentication failed."
        )
    now = int(time.time())
    if now < snapshot.issued_at_unix or now >= snapshot.expires_at_unix:
        raise EnvelopeAuthenticationError(
            "Execution envelope is not currently valid."
        )
    return snapshot


def verify_envelope_scope(
    envelope: AuthenticatedExecutionEnvelope,
    decision: Any,
    control_record: Any,
    capsule: MutationCapsule,
) -> None:
    """Enforce the authenticated scope as an exact, non-widenable ceiling."""

    from decision_os.companion.broker_control import (
        ControlDomainRecord,
        ControlDomainState,
        MutationDecision,
    )

    if (
        type(envelope) is not AuthenticatedExecutionEnvelope
        or type(decision) is not MutationDecision
        or type(control_record) is not ControlDomainRecord
        or type(capsule) is not MutationCapsule
        or control_record.state is not ControlDomainState.ACTIVE
    ):
        raise EnvelopeAuthenticationError(
            "Authenticated live scope requires exact ACTIVE Broker evidence."
        )
    expected = {
        "authority_domain_id": decision.activation.authority_domain_id,
        "activation_sha256": activation_sha256(decision.activation),
        "control_record_sha256": control_record.record_sha256,
        "repository_id": decision.activation.repository_id,
        "protected_repository_identity": (
            decision.activation.protected_repository_identity
        ),
        "write_principal_identity": decision.activation.write_principal_identity,
        "generation_witness": decision.activation.generation_witness,
        "decision_sha256": decision_sha256(decision),
        "capsule_sha256": capsule.capsule_sha256,
        "operation": decision.operation.value,
        "relative_path": decision.relative_path,
        "expected_prior_sha256": decision.expected_prior_sha256,
        "expected_post_sha256": decision.expected_post_sha256,
        "target_byte_count": len(decision.target_bytes),
        "proposal_acquisition_sha256": decision.proposal_acquisition_sha256,
    }
    observed = {key: getattr(envelope, key) for key in expected}
    if observed != expected:
        raise EnvelopeAuthenticationError(
            "Execution envelope does not exactly match the requested live scope."
        )
    if (
        capsule.external_envelope_id != envelope.envelope_id
        or capsule.external_envelope_nonce != envelope.nonce
        or capsule.external_authorization_sha256
        != envelope.authorization_identity_sha256()
    ):
        raise EnvelopeAuthenticationError(
            "Execution envelope does not exactly match its mutation capsule."
        )


PRODUCTION_AUTHENTICATION_TRUST_PRECONDITION = (
    "PRODUCTION PRECONDITION — NOT ENFORCED BY SLICE 3: deployed OS policy "
    "must keep the external authentication key outside the protected "
    "repository and Broker journal and inaccessible to untrusted or "
    "equivalently privileged processes. Slice 3 provides repository/software "
    "authentication and replay evidence only; it does not claim OS-level peer "
    "separation, root-owned secret protection, ACL enforcement, Broker "
    "sole-writer enforcement, LaunchDaemon/XPC isolation, or protection from "
    "another process holding equivalent filesystem authority."
)


__all__ = [
    "AuthenticatedExecutionEnvelope",
    "BrokerAuthorityError",
    "EnvelopeAuthenticationError",
    "EnvelopeAuthenticationKey",
    "EXECUTION_ENVELOPE_SCHEMA",
    "MAX_CAPSULES",
    "MAX_ENVELOPE_VALIDITY_SECONDS",
    "MUTATION_CAPSULE_SCHEMA",
    "MutationCapsule",
    "MutationCapsuleIntegrityError",
    "PRODUCTION_AUTHENTICATION_TRUST_PRECONDITION",
    "canonical_capsule_bytes",
    "issue_execution_envelope",
    "mutation_capsule_for",
    "parse_capsule_bytes",
    "verify_envelope_authentication",
    "verify_envelope_scope",
]
