"""Fail-closed Broker control-domain identities and CAS reconciliation.

This repository-only substrate detects present corruption and crash prefixes. It
does not claim resistance to coordinated rollback of every control artifact;
that requires a trusted monotonic anchor outside this rollback domain.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import stat
from typing import Any, Iterator

from decision_os.acceleration.model import canonical_json, hash_payload
from decision_os.companion.broker_authority import (
    AuthenticatedExecutionEnvelope,
    EnvelopeAuthenticationError,
    EnvelopeAuthenticationKey,
    MAX_CAPSULES,
    MutationCapsule,
    MutationCapsuleIntegrityError,
    canonical_capsule_bytes,
    mutation_capsule_for,
    parse_capsule_bytes,
    verify_envelope_scope,
    verify_envelope_authentication,
)


CONTROL_DOMAIN_SCHEMA = "decision-os-broker-control-domain-v0.1"
CAS_FENCE_SCHEMA = "decision-os-broker-cas-fence-v0.2"
GENESIS_CONTROL_RECORD_HASH: str | None = None
_MAX_CONTROL_RECORD_BYTES = 256 * 1024
_MAX_IDENTITY_BYTES = 256
_MAX_RETIRED_DOMAINS = 512
_MAX_JOURNAL_RECORDS = (_MAX_RETIRED_DOMAINS * 3) + 2
_MAX_CAS_FENCE_BYTES = 16 * 1024
_MAX_CAS_FENCES = 4_096
_MAX_TARGET_BYTES = 16 * 1024 * 1024
_MAX_RELATIVE_PATH_BYTES = 4_096
_MAX_GENERATION_WITNESS = (1 << 64) - 1
_SHA256_LENGTH = 64
_CONTROL_RECORD_FIELDS = frozenset(
    {
        "schema",
        "authority_domain_id",
        "repository_id",
        "protected_repository_identity",
        "write_principal_identity",
        "generation_witness",
        "state",
        "journal_position",
        "predecessor_record_sha256",
        "retired_authority_domain_ids",
        "record_sha256",
    }
)
_CAS_FENCE_FIELDS = frozenset(
    {
        "schema",
        "kind",
        "fence_id",
        "authority_domain_id",
        "activation_sha256",
        "control_record_sha256",
        "decision_sha256",
        "capsule_sha256",
        "intent_sha256",
        "outcome",
        "record_sha256",
    }
)


class BrokerControlError(RuntimeError):
    """The Broker control-domain operation cannot complete safely."""


class ControlRecordIntegrityError(BrokerControlError):
    """The durable Broker control record is absent, corrupt, or unprovable."""


class AuthorityRejectedError(BrokerControlError):
    """The supplied activation tuple is not the current mutation authority."""


class ControlDomainTransitionError(BrokerControlError):
    """A requested control-domain transition is forbidden."""


class MutationDecisionError(BrokerControlError, ValueError):
    """A mutation decision exceeds the fixed Slice 1 contract."""


class ControlDomainState(str, Enum):
    """Durable authority states; no state implies process-local authority."""

    ACTIVE = "ACTIVE"
    ABANDONED = "ABANDONED"
    UNCERTAIN = "UNCERTAIN"


class ReconciliationOutcome(str, Enum):
    """Exact pre/post-image outcomes for one bound mutation decision."""

    APPLIED = "APPLIED"
    NOT_APPLIED = "NOT_APPLIED"
    UNCERTAIN = "UNCERTAIN"


class MutationOperation(str, Enum):
    """The complete initial mutation operation set."""

    CREATE = "CREATE"
    REPLACE = "REPLACE"


class TargetKind(str, Enum):
    """Repository target observations relevant to fail-closed reconciliation."""

    ABSENT = "ABSENT"
    REGULAR = "REGULAR"
    SYMLINK = "SYMLINK"
    HARDLINK = "HARDLINK"
    DIRECTORY = "DIRECTORY"
    OTHER = "OTHER"


def _is_canonical_enum_member(value: Any, enum_type: type[Enum]) -> bool:
    return type(value) is enum_type and any(value is member for member in enum_type)


def _bounded_identity(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
    ):
        raise ValueError(f"{label} must be a non-empty string.")
    try:
        encoded = value.encode("utf-8")
    except UnicodeError as exc:
        raise ValueError(f"{label} must be valid UTF-8.") from exc
    if len(encoded) > _MAX_IDENTITY_BYTES:
        raise ValueError(f"{label} exceeds its bounded size limit.")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        raise ValueError(f"{label} cannot contain control characters.")
    return value


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == _SHA256_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _repository_identity(value: Any) -> str:
    normalized = _bounded_identity(value, "Repository identity")
    prefix = "repo:v1:"
    if not normalized.startswith(prefix) or not _is_sha256(normalized[len(prefix) :]):
        raise ValueError(
            "Repository identity must be a versioned lowercase SHA-256 identity."
        )
    return normalized


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class ActivationTuple:
    """The complete authority identity; generation is only one witness."""

    authority_domain_id: str
    repository_id: str
    protected_repository_identity: str
    write_principal_identity: str
    generation_witness: int

    def __post_init__(self) -> None:
        if type(self) is not ActivationTuple:
            raise ValueError("Activation tuple subclasses are forbidden.")
        for value, label in (
            (self.authority_domain_id, "Authority-domain identity"),
            (
                self.protected_repository_identity,
                "Protected-repository identity",
            ),
            (self.write_principal_identity, "Write-principal identity"),
        ):
            _bounded_identity(value, label)
        _repository_identity(self.repository_id)
        if (
            type(self.generation_witness) is not int
            or not 0 <= self.generation_witness <= _MAX_GENERATION_WITNESS
        ):
            raise ValueError(
                "Generation witness must be an unsigned 64-bit integer."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "authority_domain_id": self.authority_domain_id,
            "repository_id": self.repository_id,
            "protected_repository_identity": self.protected_repository_identity,
            "write_principal_identity": self.write_principal_identity,
            "generation_witness": self.generation_witness,
        }


@dataclass(frozen=True)
class ControlDomainRecord:
    """One strict, hash-bound durable Broker authority record."""

    schema: str
    activation: ActivationTuple
    state: ControlDomainState
    journal_position: int
    predecessor_record_sha256: str | None
    retired_authority_domain_ids: tuple[str, ...]
    record_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            **ActivationTuple.as_dict(self.activation),
            "state": self.state.value,
            "journal_position": self.journal_position,
            "predecessor_record_sha256": self.predecessor_record_sha256,
            "retired_authority_domain_ids": list(
                self.retired_authority_domain_ids
            ),
            "record_sha256": self.record_sha256,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "ControlDomainRecord":
        if type(value) is not dict or set(value) != _CONTROL_RECORD_FIELDS:
            raise ControlRecordIntegrityError(
                "Persisted Broker control-record fields are invalid."
            )
        if (
            type(value.get("schema")) is not str
            or value["schema"] != CONTROL_DOMAIN_SCHEMA
        ):
            raise ControlRecordIntegrityError(
                "Persisted Broker control-record schema is invalid."
            )
        try:
            activation = ActivationTuple(
                authority_domain_id=value["authority_domain_id"],
                repository_id=value["repository_id"],
                protected_repository_identity=value[
                    "protected_repository_identity"
                ],
                write_principal_identity=value["write_principal_identity"],
                generation_witness=value["generation_witness"],
            )
            raw_state = value["state"]
            if type(raw_state) is not str:
                raise ValueError("Persisted state must be a plain string.")
            state = ControlDomainState(raw_state)
        except (KeyError, TypeError, ValueError) as exc:
            raise ControlRecordIntegrityError(
                "Persisted Broker activation tuple or state is invalid."
            ) from exc
        position = value["journal_position"]
        if type(position) is not int or position < 0:
            raise ControlRecordIntegrityError(
                "Persisted Broker journal position is invalid."
            )
        predecessor = value["predecessor_record_sha256"]
        if (position == 0) != (predecessor is None):
            raise ControlRecordIntegrityError(
                "Persisted Broker predecessor position is invalid."
            )
        if predecessor is not None and not _is_sha256(predecessor):
            raise ControlRecordIntegrityError(
                "Persisted Broker predecessor hash is invalid."
            )
        retired_value = value["retired_authority_domain_ids"]
        if (
            type(retired_value) is not list
            or len(retired_value) > _MAX_RETIRED_DOMAINS
        ):
            raise ControlRecordIntegrityError(
                "Persisted retired authority-domain identities are invalid."
            )
        try:
            retired = tuple(
                _bounded_identity(item, "Retired authority-domain identity")
                for item in retired_value
            )
        except ValueError as exc:
            raise ControlRecordIntegrityError(
                "Persisted retired authority-domain identities are invalid."
            ) from exc
        if len(set(retired)) != len(retired):
            raise ControlRecordIntegrityError(
                "Persisted retired authority-domain identities are duplicated."
            )
        current_is_retired = activation.authority_domain_id in retired
        if current_is_retired != (state is ControlDomainState.ABANDONED):
            raise ControlRecordIntegrityError(
                "Persisted Broker retirement state is inconsistent."
            )
        if position == 0 and (
            state is not ControlDomainState.ACTIVE or retired
        ):
            raise ControlRecordIntegrityError(
                "The genesis Broker control record must be freshly ACTIVE."
            )
        if len(retired) > position:
            raise ControlRecordIntegrityError(
                "Persisted Broker retirement history exceeds its journal."
            )
        if (
            state is ControlDomainState.ABANDONED
            and retired[-1] != activation.authority_domain_id
        ):
            raise ControlRecordIntegrityError(
                "The abandoned Broker domain is not the latest retirement."
            )
        claimed_hash = value["record_sha256"]
        if not _is_sha256(claimed_hash):
            raise ControlRecordIntegrityError(
                "Persisted Broker control-record hash is invalid."
            )
        payload = {
            key: item for key, item in value.items() if key != "record_sha256"
        }
        if claimed_hash != hash_payload(payload):
            raise ControlRecordIntegrityError(
                "Persisted Broker control-record hash mismatches."
            )
        record = ControlDomainRecord(
            schema=CONTROL_DOMAIN_SCHEMA,
            activation=activation,
            state=state,
            journal_position=position,
            predecessor_record_sha256=predecessor,
            retired_authority_domain_ids=retired,
            record_sha256=claimed_hash,
        )
        if len(_canonical_record_bytes(record)) > _MAX_CONTROL_RECORD_BYTES:
            raise ControlRecordIntegrityError(
                "Persisted Broker control record is too large."
            )
        return record


@dataclass(frozen=True)
class MutationDecision:
    """One path/full-bytes CAS decision bound to complete Broker authority."""

    activation: ActivationTuple
    operation: MutationOperation
    relative_path: str
    target_bytes: bytes
    expected_prior_sha256: str | None
    expected_post_sha256: str
    proposal_acquisition_sha256: str | None = None

    def __post_init__(self) -> None:
        if type(self) is not MutationDecision:
            raise MutationDecisionError(
                "Mutation-decision subclasses are forbidden."
            )
        if type(self.activation) is not ActivationTuple:
            raise MutationDecisionError(
                "A complete activation tuple is required."
            )
        try:
            ActivationTuple.__post_init__(self.activation)
        except ValueError as exc:
            raise MutationDecisionError(
                "A complete activation tuple is required."
            ) from exc
        if not _is_canonical_enum_member(
            self.operation,
            MutationOperation,
        ):
            raise MutationDecisionError("Mutation operation is unsupported.")
        operation = self.operation
        normalized = _normalize_relative_path(self.relative_path)
        object.__setattr__(self, "relative_path", normalized)
        if type(self.target_bytes) is not bytes:
            raise MutationDecisionError("Full target bytes are required.")
        if len(self.target_bytes) > _MAX_TARGET_BYTES:
            raise MutationDecisionError("Target bytes exceed the bounded size limit.")
        if not _is_sha256(self.expected_post_sha256):
            raise MutationDecisionError("Expected post-image hash is invalid.")
        if _sha256_bytes(self.target_bytes) != self.expected_post_sha256:
            raise MutationDecisionError(
                "Expected post-image hash does not match the full target bytes."
            )
        if operation is MutationOperation.CREATE:
            if self.expected_prior_sha256 is not None:
                raise MutationDecisionError(
                    "CREATE requires an absent expected prior image."
                )
        else:
            if not _is_sha256(self.expected_prior_sha256):
                raise MutationDecisionError(
                    "REPLACE requires an exact expected prior-image hash."
                )
            if self.expected_prior_sha256 == self.expected_post_sha256:
                raise MutationDecisionError(
                    "REPLACE cannot use an identical prior and post image."
                )
        if (
            self.proposal_acquisition_sha256 is not None
            and not _is_sha256(self.proposal_acquisition_sha256)
        ):
            raise MutationDecisionError(
                "Proposal-acquisition binding hash is invalid."
            )

    def binding_dict(self) -> dict[str, Any]:
        """Return the exact bounded decision identity persisted by a CAS fence."""

        binding = {
            "activation": ActivationTuple.as_dict(self.activation),
            "operation": self.operation.value,
            "relative_path": self.relative_path,
            "target_byte_count": len(self.target_bytes),
            "target_bytes_sha256": _sha256_bytes(self.target_bytes),
            "expected_prior_sha256": self.expected_prior_sha256,
            "expected_post_sha256": self.expected_post_sha256,
        }
        # Preserve the accepted Slice 1 decision hash when no fd-acquisition
        # binding exists; Slice 2 live decisions extend, rather than rewrite,
        # that durable identity.
        if self.proposal_acquisition_sha256 is not None:
            binding["proposal_acquisition_sha256"] = (
                self.proposal_acquisition_sha256
            )
        return binding


@dataclass(frozen=True)
class TargetObservation:
    """A data-only target observation; production fd acquisition is later work."""

    kind: TargetKind
    content: bytes | None = None

    def __post_init__(self) -> None:
        if type(self) is not TargetObservation:
            raise MutationDecisionError(
                "Target-observation subclasses are forbidden."
            )
        if not _is_canonical_enum_member(self.kind, TargetKind):
            raise MutationDecisionError("Target observation kind is invalid.")
        kind = self.kind
        if kind is TargetKind.REGULAR:
            if type(self.content) is not bytes:
                raise MutationDecisionError(
                    "A regular target observation requires exact bytes."
                )
            if len(self.content) > _MAX_TARGET_BYTES:
                raise MutationDecisionError(
                    "Observed target bytes exceed the bounded size limit."
                )
        elif self.content is not None:
            raise MutationDecisionError(
                "Non-regular target observations cannot carry trusted bytes."
            )


def _snapshot_activation(value: Any) -> ActivationTuple:
    """Copy one exact activation into private, validated plain values."""

    if type(value) is not ActivationTuple:
        raise ValueError("Activation tuple subclasses are forbidden.")
    return ActivationTuple(
        authority_domain_id=value.authority_domain_id,
        repository_id=value.repository_id,
        protected_repository_identity=value.protected_repository_identity,
        write_principal_identity=value.write_principal_identity,
        generation_witness=value.generation_witness,
    )


def _snapshot_decision(value: Any) -> MutationDecision:
    """Copy one caller decision so later caller mutation cannot change binding."""

    if type(value) is not MutationDecision:
        raise MutationDecisionError(
            "Mutation-decision subclasses are forbidden."
        )
    return MutationDecision(
        activation=_snapshot_activation(value.activation),
        operation=value.operation,
        relative_path=value.relative_path,
        target_bytes=value.target_bytes,
        expected_prior_sha256=value.expected_prior_sha256,
        expected_post_sha256=value.expected_post_sha256,
        proposal_acquisition_sha256=value.proposal_acquisition_sha256,
    )


def _snapshot_observation(value: Any) -> TargetObservation:
    """Copy one caller observation into exact immutable fields."""

    if type(value) is not TargetObservation:
        raise MutationDecisionError(
            "Target-observation subclasses are forbidden."
        )
    return TargetObservation(kind=value.kind, content=value.content)


@dataclass(frozen=True)
class _CASFenceRecord:
    schema: str
    kind: str
    fence_id: str
    authority_domain_id: str
    activation_sha256: str
    control_record_sha256: str
    decision_sha256: str
    capsule_sha256: str | None
    intent_sha256: str | None
    outcome: str | None
    record_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "kind": self.kind,
            "fence_id": self.fence_id,
            "authority_domain_id": self.authority_domain_id,
            "activation_sha256": self.activation_sha256,
            "control_record_sha256": self.control_record_sha256,
            "decision_sha256": self.decision_sha256,
            "capsule_sha256": self.capsule_sha256,
            "intent_sha256": self.intent_sha256,
            "outcome": self.outcome,
            "record_sha256": self.record_sha256,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "_CASFenceRecord":
        if type(value) is not dict or set(value) != _CAS_FENCE_FIELDS:
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence fields are invalid."
            )
        if (
            type(value.get("schema")) is not str
            or value["schema"] != CAS_FENCE_SCHEMA
        ):
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence schema is invalid."
            )
        kind = value["kind"]
        if type(kind) is not str or kind not in {"INTENT", "COMPLETE"}:
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence kind is invalid."
            )
        fence_id = value["fence_id"]
        if (
            type(fence_id) is not str
            or len(fence_id) != 32
            or any(character not in "0123456789abcdef" for character in fence_id)
        ):
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence identity is invalid."
            )
        try:
            _bounded_identity(
                value["authority_domain_id"],
                "CAS-fence authority-domain identity",
            )
        except ValueError as exc:
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence authority identity is invalid."
            ) from exc
        for key in (
            "activation_sha256",
            "control_record_sha256",
            "decision_sha256",
            "record_sha256",
        ):
            if not _is_sha256(value[key]):
                raise ControlRecordIntegrityError(
                    "Persisted Broker CAS-fence hash is invalid."
                )
        capsule_sha256 = value["capsule_sha256"]
        if capsule_sha256 is not None and not _is_sha256(capsule_sha256):
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence capsule hash is invalid."
            )
        intent_sha256 = value["intent_sha256"]
        outcome = value["outcome"]
        if kind == "INTENT":
            if intent_sha256 is not None or outcome is not None:
                raise ControlRecordIntegrityError(
                    "Persisted Broker CAS intent is inconsistent."
                )
        elif (
            not _is_sha256(intent_sha256)
            or type(outcome) is not str
            or outcome
            not in {
                ReconciliationOutcome.APPLIED.value,
                ReconciliationOutcome.NOT_APPLIED.value,
                ReconciliationOutcome.UNCERTAIN.value,
            }
        ):
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS completion is inconsistent."
            )
        payload = {
            key: item for key, item in value.items() if key != "record_sha256"
        }
        if value["record_sha256"] != hash_payload(payload):
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence hash mismatches."
            )
        record = _CASFenceRecord(**value)
        if len(_canonical_fence_bytes(record)) > _MAX_CAS_FENCE_BYTES:
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS fence is too large."
            )
        return record


def _normalize_relative_path(value: Any) -> str:
    if type(value) is not str or not value or "\x00" in value:
        raise MutationDecisionError("Mutation path must be one non-empty path.")
    try:
        encoded = value.encode("utf-8")
    except UnicodeError as exc:
        raise MutationDecisionError("Mutation path must be valid UTF-8.") from exc
    if len(encoded) > _MAX_RELATIVE_PATH_BYTES:
        raise MutationDecisionError("Mutation path exceeds its bounded size limit.")
    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in value):
        raise MutationDecisionError("Mutation path cannot contain control characters.")
    if "\\" in value:
        raise MutationDecisionError("Mutation path must use portable separators.")
    path = PurePosixPath(value)
    if path.is_absolute() or value.endswith("/"):
        raise MutationDecisionError("Mutation path must name one relative file.")
    parts = path.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise MutationDecisionError("Mutation path is not normalized.")
    if any(part.casefold() == ".git" for part in parts):
        raise MutationDecisionError("Mutation under .git is forbidden.")
    normalized = path.as_posix()
    if normalized != value:
        raise MutationDecisionError("Mutation path is not canonical.")
    return normalized


def reconcile_mutation(
    decision: MutationDecision,
    observation: TargetObservation,
) -> ReconciliationOutcome:
    """Classify only exact pre/post evidence; never grant or restore authority."""

    decision = _snapshot_decision(decision)
    observation = _snapshot_observation(observation)

    if observation.kind is TargetKind.REGULAR:
        assert observation.content is not None
        observed_hash = _sha256_bytes(observation.content)
        if (
            observed_hash == decision.expected_post_sha256
            and observation.content == decision.target_bytes
        ):
            return ReconciliationOutcome.APPLIED
        if (
            decision.operation is MutationOperation.REPLACE
            and observed_hash == decision.expected_prior_sha256
        ):
            return ReconciliationOutcome.NOT_APPLIED
        return ReconciliationOutcome.UNCERTAIN
    if (
        observation.kind is TargetKind.ABSENT
        and decision.operation is MutationOperation.CREATE
    ):
        return ReconciliationOutcome.NOT_APPLIED
    return ReconciliationOutcome.UNCERTAIN


def _canonical_record_bytes(record: ControlDomainRecord) -> bytes:
    if (
        type(record) is not ControlDomainRecord
        or type(record.schema) is not str
        or record.schema != CONTROL_DOMAIN_SCHEMA
        or not _is_canonical_enum_member(record.state, ControlDomainState)
        or type(record.journal_position) is not int
        or record.journal_position < 0
        or (
            record.predecessor_record_sha256 is not None
            and not _is_sha256(record.predecessor_record_sha256)
        )
        or type(record.retired_authority_domain_ids) is not tuple
        or not _is_sha256(record.record_sha256)
    ):
        raise ControlRecordIntegrityError(
            "Broker control-record runtime types are invalid."
        )
    try:
        _snapshot_activation(record.activation)
        for retired in record.retired_authority_domain_ids:
            _bounded_identity(retired, "Retired authority-domain identity")
    except ValueError as exc:
        raise ControlRecordIntegrityError(
            "Broker control-record runtime types are invalid."
        ) from exc
    return (canonical_json(ControlDomainRecord.as_dict(record)) + "\n").encode(
        "utf-8"
    )


def _canonical_fence_bytes(record: _CASFenceRecord) -> bytes:
    return (canonical_json(_CASFenceRecord.as_dict(record)) + "\n").encode(
        "utf-8"
    )


def _activation_sha256(activation: ActivationTuple) -> str:
    snapshot = _snapshot_activation(activation)
    return hash_payload(ActivationTuple.as_dict(snapshot))


def _new_cas_intent(
    decision: MutationDecision,
    current: ControlDomainRecord,
    capsule_sha256: str | None = None,
) -> _CASFenceRecord:
    if capsule_sha256 is not None and not _is_sha256(capsule_sha256):
        raise ControlRecordIntegrityError(
            "A Broker CAS intent requires an exact capsule hash."
        )
    payload: dict[str, Any] = {
        "schema": CAS_FENCE_SCHEMA,
        "kind": "INTENT",
        "fence_id": secrets.token_hex(16),
        "authority_domain_id": decision.activation.authority_domain_id,
        "activation_sha256": _activation_sha256(decision.activation),
        "control_record_sha256": current.record_sha256,
        "decision_sha256": hash_payload(MutationDecision.binding_dict(decision)),
        "capsule_sha256": capsule_sha256,
        "intent_sha256": None,
        "outcome": None,
    }
    payload["record_sha256"] = hash_payload(payload)
    return _CASFenceRecord.from_dict(payload)


def _complete_cas_intent(
    intent: _CASFenceRecord,
    outcome: ReconciliationOutcome,
) -> _CASFenceRecord:
    if not _is_canonical_enum_member(outcome, ReconciliationOutcome):
        raise ControlRecordIntegrityError(
            "The CAS reconciliation outcome is invalid."
        )
    payload: dict[str, Any] = {
        "schema": CAS_FENCE_SCHEMA,
        "kind": "COMPLETE",
        "fence_id": intent.fence_id,
        "authority_domain_id": intent.authority_domain_id,
        "activation_sha256": intent.activation_sha256,
        "control_record_sha256": intent.control_record_sha256,
        "decision_sha256": intent.decision_sha256,
        "capsule_sha256": intent.capsule_sha256,
        "intent_sha256": intent.record_sha256,
        "outcome": outcome.value,
    }
    payload["record_sha256"] = hash_payload(payload)
    return _CASFenceRecord.from_dict(payload)


def _new_record(
    activation: ActivationTuple,
    *,
    state: ControlDomainState,
    journal_position: int,
    predecessor_record_sha256: str | None,
    retired_authority_domain_ids: tuple[str, ...],
) -> ControlDomainRecord:
    if type(activation) is not ActivationTuple:
        raise ControlRecordIntegrityError(
            "A Broker control record requires an exact activation tuple."
        )
    try:
        ActivationTuple.__post_init__(activation)
    except ValueError as exc:
        raise ControlRecordIntegrityError(
            "A Broker control record requires an exact activation tuple."
        ) from exc
    if not _is_canonical_enum_member(state, ControlDomainState):
        raise ControlRecordIntegrityError(
            "A Broker control record requires an exact state."
        )
    if type(journal_position) is not int or journal_position < 0:
        raise ControlRecordIntegrityError(
            "A Broker control record requires an exact journal position."
        )
    payload: dict[str, Any] = {
        "schema": CONTROL_DOMAIN_SCHEMA,
        **ActivationTuple.as_dict(activation),
        "state": state.value,
        "journal_position": journal_position,
        "predecessor_record_sha256": predecessor_record_sha256,
        "retired_authority_domain_ids": list(retired_authority_domain_ids),
    }
    payload["record_sha256"] = hash_payload(payload)
    return ControlDomainRecord.from_dict(payload)


class ControlDomainStore:
    """Durable Broker authority with an immutable control-record journal."""

    _IMMUTABLE_CONFIGURATION_FIELDS = frozenset(
        {
            "path",
            "_lock_path",
            "_journal_path",
            "_fence_path",
            "_capsule_path",
            "_blob_path",
            "_authenticator_path",
            "_authentication_key",
            "_IMMUTABLE_CONFIGURATION_FIELDS",
        }
    )

    def __setattr__(self, name: str, value: Any) -> None:
        protected = ControlDomainStore._IMMUTABLE_CONFIGURATION_FIELDS
        if (
            name in protected
            and (name == "_IMMUTABLE_CONFIGURATION_FIELDS" or name in self.__dict__)
        ):
            raise AttributeError(
                "Broker control-store configuration is immutable after construction."
            )
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if name in ControlDomainStore._IMMUTABLE_CONFIGURATION_FIELDS:
            raise AttributeError(
                "Broker control-store configuration cannot be removed."
            )
        object.__delattr__(self, name)

    def __init__(
        self,
        path: Path,
        *,
        authentication_key: EnvelopeAuthenticationKey | None = None,
    ) -> None:
        if not isinstance(path, Path):
            raise ValueError("Broker control path must be one pathlib.Path.")
        try:
            raw_path = os.fspath(path)
            if type(raw_path) not in {str, bytes}:
                raise TypeError("filesystem path is not plain text or bytes")
            decoded_path = os.fsdecode(raw_path)
            if any(
                component in {".", ".."}
                for component in decoded_path.split(os.sep)
            ):
                raise ValueError("control path is not lexically canonical")
            path = Path(decoded_path).absolute()
        except (OSError, TypeError, ValueError) as exc:
            raise ValueError("Broker control path is invalid or unavailable.") from exc
        if authentication_key is not None and type(
            authentication_key
        ) is not EnvelopeAuthenticationKey:
            raise ValueError(
                "Broker authentication material must be exact external key data."
            )
        self.path = path
        self._lock_path = path.with_name(f".{path.name}.lock")
        self._journal_path = path.with_name(f".{path.name}.journal")
        self._fence_path = path.with_name(f".{path.name}.cas-fences")
        self._capsule_path = path.with_name(f".{path.name}.mutation-capsules")
        self._blob_path = self._capsule_path / "blobs"
        self._authenticator_path = path.with_name(
            f".{path.name}.execution-authenticator.json"
        )
        self._authentication_key = (
            None
            if authentication_key is None
            else EnvelopeAuthenticationKey(
                key_id=authentication_key.key_id,
                key_version=authentication_key.key_version,
                secret=authentication_key.secret,
            )
        )

    def _require_coherent_routing(self) -> None:
        """Reject a store object whose snapshotted route fields were mutated."""

        path = self.path
        if (
            not isinstance(path, Path)
            or not path.is_absolute()
            or self._lock_path != path.with_name(f".{path.name}.lock")
            or self._journal_path != path.with_name(f".{path.name}.journal")
            or self._fence_path != path.with_name(f".{path.name}.cas-fences")
            or self._capsule_path
            != path.with_name(f".{path.name}.mutation-capsules")
            or self._blob_path != self._capsule_path / "blobs"
            or self._authenticator_path
            != path.with_name(f".{path.name}.execution-authenticator.json")
        ):
            raise ControlRecordIntegrityError(
                "Broker control-store routing identity is incoherent."
            )

    def _verify_execution_envelope(
        self,
        envelope: Any,
    ) -> AuthenticatedExecutionEnvelope:
        """Verify request authority against the store's external trust root."""

        if self._authentication_key is None:
            raise EnvelopeAuthenticationError(
                "Broker live execution has no configured external trust root."
            )
        return verify_envelope_authentication(
            envelope,
            self._authentication_key,
        )

    @staticmethod
    def _authenticator_payload(
        authentication_key: EnvelopeAuthenticationKey,
        *,
        control_path: Path,
    ) -> dict[str, Any]:
        return {
            "schema": "decision-os-broker-execution-authenticator-v0.1",
            "control_path_sha256": hashlib.sha256(
                os.fsencode(os.path.abspath(control_path))
            ).hexdigest(),
            "authentication_key_id": authentication_key.key_id,
            "authentication_key_version": authentication_key.key_version,
            "authentication_key_sha256": hashlib.sha256(
                authentication_key.secret
            ).hexdigest(),
        }

    def _authentication_key_commitment_unlocked(self) -> dict[str, Any] | None:
        if not os.path.lexists(self._authenticator_path):
            return None
        raw = self._recover_immutable_publication_unlocked(
            self._authenticator_path,
            maximum=4 * 1024,
            label="Persisted Broker execution authenticator",
        )
        try:
            value = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ControlRecordIntegrityError(
                "Persisted Broker execution authenticator is unreadable."
            ) from exc
        fields = {
            "schema",
            "authentication_key_id",
            "authentication_key_version",
            "authentication_key_sha256",
            "control_path_sha256",
        }
        if type(value) is not dict or set(value) != fields:
            raise ControlRecordIntegrityError(
                "Persisted Broker execution authenticator fields are invalid."
            )
        try:
            _bounded_identity(
                value["authentication_key_id"],
                "Authentication key identity",
            )
        except ValueError as exc:
            raise ControlRecordIntegrityError(
                "Persisted Broker execution authenticator identity is invalid."
            ) from exc
        if (
            value["schema"]
            != "decision-os-broker-execution-authenticator-v0.1"
            or type(value["authentication_key_version"]) is not int
            or not 1 <= value["authentication_key_version"] <= (1 << 31) - 1
            or not _is_sha256(value["control_path_sha256"])
            or not _is_sha256(value["authentication_key_sha256"])
        ):
            raise ControlRecordIntegrityError(
                "Persisted Broker execution authenticator is invalid."
            )
        expected = (canonical_json(value) + "\n").encode("utf-8")
        if raw != expected:
            raise ControlRecordIntegrityError(
                "Persisted Broker execution authenticator is not canonical."
            )
        return value

    def _require_authentication_key_commitment_unlocked(self) -> None:
        commitment = self._authentication_key_commitment_unlocked()
        if commitment is None:
            raise EnvelopeAuthenticationError(
                "Broker authority has no activation-bound execution authenticator."
            )
        if self._authentication_key is None:
            raise EnvelopeAuthenticationError(
                "Broker live execution has no configured external trust root."
            )
        expected = self._authenticator_payload(
            self._authentication_key,
            control_path=self.path,
        )
        if commitment != expected:
            raise EnvelopeAuthenticationError(
                "Configured external trust root does not match Broker activation."
            )

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        descriptor = os.open(
            directory,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @classmethod
    def _ensure_directory(cls, directory: Path) -> None:
        missing: list[Path] = []
        cursor = directory
        while not os.path.lexists(cursor):
            if cursor == cursor.parent:
                raise ControlRecordIntegrityError(
                    "Broker control-record directory cannot be established."
                )
            missing.append(cursor)
            cursor = cursor.parent
        try:
            ancestor_status = cursor.lstat()
        except OSError as exc:
            raise ControlRecordIntegrityError(
                "Broker control-record directory is unavailable."
            ) from exc
        if not stat.S_ISDIR(ancestor_status.st_mode):
            raise ControlRecordIntegrityError(
                "Broker control-record directory identity is unsafe."
            )
        if cursor != cursor.parent:
            # A prior process may have completed mkdir(cursor) but lost the
            # parent-directory fsync response.  Re-establish that name's
            # durability before using it as the parent of any authority
            # artifact, then prove that the same directory remained named.
            try:
                cls._fsync_directory(cursor.parent)
                refreshed_ancestor = cursor.lstat()
            except OSError as exc:
                raise ControlRecordIntegrityError(
                    "Broker control-record directory durability cannot be proven."
                ) from exc
            if (
                refreshed_ancestor.st_dev != ancestor_status.st_dev
                or refreshed_ancestor.st_ino != ancestor_status.st_ino
                or not stat.S_ISDIR(refreshed_ancestor.st_mode)
            ):
                raise ControlRecordIntegrityError(
                    "Broker control-record directory identity changed."
                )
        for candidate in reversed(missing):
            try:
                candidate.mkdir(mode=0o700)
            except OSError as exc:
                raise ControlRecordIntegrityError(
                    "Broker control-record directory cannot be created."
                ) from exc
            cls._fsync_directory(candidate.parent)
        try:
            final_status = directory.lstat()
        except OSError as exc:
            raise ControlRecordIntegrityError(
                "Broker control-record directory is unavailable."
            ) from exc
        if not stat.S_ISDIR(final_status.st_mode):
            raise ControlRecordIntegrityError(
                "Broker control-record directory identity is unsafe."
            )

    @contextmanager
    def _locked(self, *, exclusive: bool) -> Iterator[None]:
        self._require_coherent_routing()
        self._ensure_directory(self.path.parent)
        try:
            parent_before = self.path.parent.stat()
        except OSError as exc:
            raise ControlRecordIntegrityError(
                "Broker control-record directory is unavailable."
            ) from exc
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(self._lock_path, flags, 0o600)
        except OSError as exc:
            raise ControlRecordIntegrityError(
                "Broker control-record serializer is unavailable."
            ) from exc
        try:
            lock_status = os.fstat(descriptor)
            if not stat.S_ISREG(lock_status.st_mode) or lock_status.st_nlink != 1:
                raise ControlRecordIntegrityError(
                    "Broker control-record serializer identity is unsafe."
                )
            os.fchmod(descriptor, 0o600)
            fcntl.flock(
                descriptor,
                fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH,
            )
            try:
                named_lock = self._lock_path.lstat()
                parent_after = self.path.parent.stat()
            except OSError as exc:
                raise ControlRecordIntegrityError(
                    "Broker control-record serializer identity changed."
                ) from exc
            if (
                named_lock.st_dev != lock_status.st_dev
                or named_lock.st_ino != lock_status.st_ino
                or not stat.S_ISREG(named_lock.st_mode)
                or named_lock.st_nlink != 1
                or parent_after.st_dev != parent_before.st_dev
                or parent_after.st_ino != parent_before.st_ino
            ):
                raise ControlRecordIntegrityError(
                    "Broker control-record serializer identity changed."
                )
            yield
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

    @staticmethod
    def _read_private_bytes(path: Path, maximum: int, label: str) -> bytes:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            descriptor = os.open(path, flags)
        except OSError as exc:
            raise ControlRecordIntegrityError(f"{label} is unreadable.") from exc
        try:
            file_status = os.fstat(descriptor)
            if not stat.S_ISREG(file_status.st_mode) or file_status.st_nlink != 1:
                raise ControlRecordIntegrityError(f"{label} identity is unsafe.")
            chunks: list[bytes] = []
            remaining = maximum + 1
            while remaining:
                chunk = os.read(descriptor, min(65_536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
        except OSError as exc:
            raise ControlRecordIntegrityError(f"{label} is unreadable.") from exc
        finally:
            os.close(descriptor)
        if len(raw) > maximum:
            raise ControlRecordIntegrityError(f"{label} is too large.")
        return raw

    @staticmethod
    def _read_immutable_bytes(path: Path, maximum: int, label: str) -> bytes:
        """Read one stable, singly linked content-addressed inode."""

        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            descriptor = os.open(path, flags)
        except OSError as exc:
            raise MutationCapsuleIntegrityError(f"{label} is unreadable.") from exc
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise MutationCapsuleIntegrityError(f"{label} identity is unsafe.")
            chunks: list[bytes] = []
            remaining = maximum + 1
            while remaining:
                chunk = os.read(descriptor, min(65_536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
            after = os.fstat(descriptor)
            try:
                named = path.lstat()
            except OSError as exc:
                raise MutationCapsuleIntegrityError(
                    f"{label} pathname identity changed."
                ) from exc
            if (
                before.st_dev != after.st_dev
                or before.st_ino != after.st_ino
                or before.st_mode != after.st_mode
                or before.st_nlink != after.st_nlink
                or before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns
                or before.st_ctime_ns != after.st_ctime_ns
                or named.st_dev != after.st_dev
                or named.st_ino != after.st_ino
                or stat.S_IFMT(named.st_mode) != stat.S_IFMT(after.st_mode)
                or named.st_nlink != 1
                or named.st_size != after.st_size
                or named.st_mtime_ns != after.st_mtime_ns
                or named.st_ctime_ns != after.st_ctime_ns
            ):
                raise MutationCapsuleIntegrityError(f"{label} identity changed.")
        except MutationCapsuleIntegrityError:
            raise
        except OSError as exc:
            raise MutationCapsuleIntegrityError(f"{label} is unreadable.") from exc
        finally:
            os.close(descriptor)
        if len(raw) > maximum:
            raise MutationCapsuleIntegrityError(f"{label} is too large.")
        return raw

    @classmethod
    def _read_control_record(cls, path: Path) -> ControlDomainRecord:
        if path.parent.name.endswith(".journal"):
            try:
                raw = cls._recover_immutable_publication_unlocked(
                    path,
                    maximum=_MAX_CONTROL_RECORD_BYTES,
                    label="Persisted Broker control record",
                )
            except MutationCapsuleIntegrityError as exc:
                raise ControlRecordIntegrityError(
                    "Persisted Broker control record is unreadable."
                ) from exc
        else:
            raw = cls._read_private_bytes(
                path,
                _MAX_CONTROL_RECORD_BYTES,
                "Persisted Broker control record",
            )
        try:
            value = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ControlRecordIntegrityError(
                "Persisted Broker control record is unreadable."
            ) from exc
        try:
            record = ControlDomainRecord.from_dict(value)
        except ControlRecordIntegrityError:
            raise
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ControlRecordIntegrityError(
                "Persisted Broker control-record structure is invalid."
            ) from exc
        if raw != _canonical_record_bytes(record):
            raise ControlRecordIntegrityError(
                "Persisted Broker control record is not canonical."
            )
        return record

    @classmethod
    def _read_cas_fence(cls, path: Path) -> _CASFenceRecord:
        try:
            raw = cls._recover_immutable_publication_unlocked(
                path,
                maximum=_MAX_CAS_FENCE_BYTES,
                label="Persisted Broker CAS fence",
            )
        except MutationCapsuleIntegrityError as exc:
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS fence is unreadable."
            ) from exc
        try:
            value = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS fence is unreadable."
            ) from exc
        record = _CASFenceRecord.from_dict(value)
        if raw != _canonical_fence_bytes(record):
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS fence is not canonical."
            )
        return record

    @staticmethod
    def _record_filename(record: ControlDomainRecord) -> str:
        return (
            f"{record.journal_position:020d}-"
            f"{record.record_sha256}.json"
        )

    def _journal_records_unlocked(self) -> tuple[ControlDomainRecord, ...]:
        if not os.path.lexists(self._journal_path):
            return ()
        journal_status = self._journal_path.lstat()
        if not stat.S_ISDIR(journal_status.st_mode):
            raise ControlRecordIntegrityError(
                "Persisted Broker control journal identity is unsafe."
            )
        by_position: dict[int, ControlDomainRecord] = {}
        for path in self._journal_path.iterdir():
            if path.name.startswith(".broker-control-") and path.name.endswith(
                ".tmp"
            ):
                continue
            name = path.name
            if len(name) != 20 + 1 + 64 + 5 or name[20] != "-" or not name.endswith(
                ".json"
            ):
                raise ControlRecordIntegrityError(
                    "Persisted Broker control journal contains an invalid entry."
                )
            position_text = name[:20]
            digest = name[21:-5]
            if not position_text.isdigit() or not _is_sha256(digest):
                raise ControlRecordIntegrityError(
                    "Persisted Broker control journal entry name is invalid."
                )
            record = self._read_control_record(path)
            position = int(position_text)
            if (
                record.journal_position != position
                or record.record_sha256 != digest
                or position in by_position
            ):
                raise ControlRecordIntegrityError(
                    "Persisted Broker control journal identity mismatches."
                )
            by_position[position] = record
        if len(by_position) > _MAX_JOURNAL_RECORDS:
            raise ControlRecordIntegrityError(
                "Persisted Broker control journal is too large."
            )
        if not by_position:
            return ()
        expected_positions = list(range(len(by_position)))
        if sorted(by_position) != expected_positions:
            raise ControlRecordIntegrityError(
                "Persisted Broker control journal has a position gap."
            )
        records = tuple(by_position[position] for position in expected_positions)
        self._validate_journal(records)
        return records

    @staticmethod
    def _validate_journal(records: tuple[ControlDomainRecord, ...]) -> None:
        seen_domains: set[str] = set()
        seen_protected_identities: set[str] = set()
        seen_principal_identities: set[str] = set()
        for position, record in enumerate(records):
            if position == 0:
                if (
                    record.state is not ControlDomainState.ACTIVE
                    or record.predecessor_record_sha256 is not None
                    or record.retired_authority_domain_ids
                ):
                    raise ControlRecordIntegrityError(
                        "Persisted Broker control-journal genesis is invalid."
                    )
                seen_domains.add(record.activation.authority_domain_id)
                seen_protected_identities.add(
                    record.activation.protected_repository_identity
                )
                seen_principal_identities.add(
                    record.activation.write_principal_identity
                )
                continue
            prior = records[position - 1]
            if record.predecessor_record_sha256 != prior.record_sha256:
                raise ControlRecordIntegrityError(
                    "Persisted Broker control-journal predecessor mismatches."
                )
            same_domain = record.activation == prior.activation
            if same_domain:
                allowed = {
                    ControlDomainState.ACTIVE: {
                        ControlDomainState.ABANDONED,
                        ControlDomainState.UNCERTAIN,
                    },
                    ControlDomainState.UNCERTAIN: {
                        ControlDomainState.ABANDONED
                    },
                    ControlDomainState.ABANDONED: set(),
                }
                if record.state not in allowed[prior.state]:
                    raise ControlRecordIntegrityError(
                        "Persisted Broker control-journal transition is invalid."
                    )
                retired = prior.retired_authority_domain_ids
                if record.state is ControlDomainState.ABANDONED:
                    retired = (*retired, record.activation.authority_domain_id)
                if record.retired_authority_domain_ids != retired:
                    raise ControlRecordIntegrityError(
                        "Persisted Broker retirement history mismatches."
                    )
                continue
            if (
                prior.state is not ControlDomainState.ABANDONED
                or record.state is not ControlDomainState.ACTIVE
                or record.activation.repository_id
                != prior.activation.repository_id
                or record.activation.authority_domain_id in seen_domains
                or record.activation.protected_repository_identity
                in seen_protected_identities
                or record.activation.write_principal_identity
                in seen_principal_identities
                or record.retired_authority_domain_ids
                != prior.retired_authority_domain_ids
            ):
                raise ControlRecordIntegrityError(
                    "Persisted Broker successor activation is invalid."
                )
            seen_domains.add(record.activation.authority_domain_id)
            seen_protected_identities.add(
                record.activation.protected_repository_identity
            )
            seen_principal_identities.add(
                record.activation.write_principal_identity
            )

    def _cas_fences_unlocked(
        self,
        journal: tuple[ControlDomainRecord, ...],
    ) -> tuple[_CASFenceRecord, ...]:
        if not os.path.lexists(self._fence_path):
            return ()
        fence_status = self._fence_path.lstat()
        if not stat.S_ISDIR(fence_status.st_mode):
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence directory identity is unsafe."
            )
        fences: list[_CASFenceRecord] = []
        seen_hashes: set[str] = set()
        for path in self._fence_path.iterdir():
            if path.name.startswith(".broker-control-") and path.name.endswith(
                ".tmp"
            ):
                continue
            if len(path.name) != 64 + 5 or not path.name.endswith(".json"):
                raise ControlRecordIntegrityError(
                    "Persisted Broker CAS-fence entry name is invalid."
                )
            digest = path.name[:-5]
            if not _is_sha256(digest) or digest in seen_hashes:
                raise ControlRecordIntegrityError(
                    "Persisted Broker CAS-fence identity is invalid."
                )
            fence = self._read_cas_fence(path)
            if fence.record_sha256 != digest:
                raise ControlRecordIntegrityError(
                    "Persisted Broker CAS-fence name mismatches."
                )
            fences.append(fence)
            seen_hashes.add(digest)
        if len(fences) > _MAX_CAS_FENCES:
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence history is too large."
            )
        journal_by_hash = {record.record_sha256: record for record in journal}
        intents = {
            fence.record_sha256: fence
            for fence in fences
            if fence.kind == "INTENT"
        }
        intent_by_control: dict[str, _CASFenceRecord] = {}
        completed: set[str] = set()
        for fence in fences:
            control = journal_by_hash.get(fence.control_record_sha256)
            if (
                control is None
                or control.state is not ControlDomainState.ACTIVE
                or control.activation.authority_domain_id
                != fence.authority_domain_id
                or _activation_sha256(control.activation)
                != fence.activation_sha256
            ):
                raise ControlRecordIntegrityError(
                    "Persisted Broker CAS fence is not bound to its control record."
                )
            if fence.kind == "INTENT":
                if fence.control_record_sha256 in intent_by_control:
                    raise ControlRecordIntegrityError(
                        "Persisted Broker control authority has multiple CAS intents."
                    )
                intent_by_control[fence.control_record_sha256] = fence
                continue
            assert fence.intent_sha256 is not None
            intent = intents.get(fence.intent_sha256)
            if (
                intent is None
                or intent.fence_id != fence.fence_id
                or intent.authority_domain_id != fence.authority_domain_id
                or intent.activation_sha256 != fence.activation_sha256
                or intent.control_record_sha256
                != fence.control_record_sha256
                or intent.decision_sha256 != fence.decision_sha256
                or intent.capsule_sha256 != fence.capsule_sha256
                or intent.record_sha256 in completed
            ):
                raise ControlRecordIntegrityError(
                    "Persisted Broker CAS completion mismatches its intent."
                )
            completed.add(intent.record_sha256)
        return tuple(fences)

    def _cas_exchange_unlocked(
        self,
        journal: tuple[ControlDomainRecord, ...],
        activation: ActivationTuple,
        decision_sha256: str,
    ) -> tuple[_CASFenceRecord | None, _CASFenceRecord | None]:
        """Return one exact intent/completion without accepting a near match."""

        activation_hash = _activation_sha256(activation)
        fences = self._cas_fences_unlocked(journal)
        matching_intents = [
            fence
            for fence in fences
            if fence.kind == "INTENT"
            and fence.activation_sha256 == activation_hash
        ]
        if not matching_intents:
            return None, None
        if len(matching_intents) != 1:
            raise ControlRecordIntegrityError(
                "Broker activation has multiple persisted CAS intents."
            )
        intent = matching_intents[0]
        if intent.decision_sha256 != decision_sha256:
            raise AuthorityRejectedError(
                "A different decision already consumed this authority domain."
            )
        completions = [
            fence
            for fence in fences
            if fence.kind == "COMPLETE"
            and fence.intent_sha256 == intent.record_sha256
        ]
        if len(completions) > 1:
            raise ControlRecordIntegrityError(
                "Broker CAS intent has multiple persisted completions."
            )
        return intent, completions[0] if completions else None

    def _load_head_unlocked(self) -> ControlDomainRecord | None:
        if not os.path.lexists(self.path):
            return None
        return self._read_control_record(self.path)

    def _load_unlocked(
        self,
        *,
        allow_consumed_cas: bool = False,
        repair_incomplete_publication: bool = False,
    ) -> ControlDomainRecord | None:
        head = self._load_head_unlocked()
        journal = self._journal_records_unlocked()
        if head is None and not journal:
            if self._cas_fences_unlocked(journal):
                raise ControlRecordIntegrityError(
                    "Broker CAS fences exist without control authority."
                )
            return None
        if not journal:
            raise ControlRecordIntegrityError(
                "Broker control-record head does not match its durable journal."
            )
        if head != journal[-1]:
            if head is not None and head not in journal:
                raise ControlRecordIntegrityError(
                    "Broker control-record head is not a durable journal ancestor."
                )
            self._cas_fences_unlocked(journal)
            if not repair_incomplete_publication:
                raise ControlRecordIntegrityError(
                    "Broker control-record head does not match its durable journal."
                )
            recovered = journal[-1]
            if recovered.state is ControlDomainState.ACTIVE:
                recovered = self._prospective_record(
                    recovered,
                    ControlDomainState.UNCERTAIN,
                )
                self._append_control_record_unlocked(recovered)
                journal = (*journal, recovered)
            self._replace_head_unlocked(recovered)
            head = recovered
        fences = self._cas_fences_unlocked(journal)
        if (
            head.state is ControlDomainState.ACTIVE
            and not allow_consumed_cas
        ):
            for fence in fences:
                if (
                    fence.kind == "INTENT"
                    and fence.activation_sha256
                    == _activation_sha256(head.activation)
                ):
                    raise ControlRecordIntegrityError(
                        "Broker authority has a consumed CAS fence."
                    )
        return head

    def _load_required_unlocked(
        self,
        *,
        allow_consumed_cas: bool = False,
        repair_incomplete_publication: bool = False,
    ) -> ControlDomainRecord:
        record = self._load_unlocked(
            allow_consumed_cas=allow_consumed_cas,
            repair_incomplete_publication=repair_incomplete_publication,
        )
        if record is None:
            raise ControlRecordIntegrityError(
                "Persisted Broker control record is absent."
            )
        return record

    def load(self) -> ControlDomainRecord | None:
        with self._locked(exclusive=False):
            return self._load_unlocked()

    def load_required(self) -> ControlDomainRecord:
        with self._locked(exclusive=False):
            return self._load_required_unlocked()

    def recover_control_head_fail_closed(self) -> ControlDomainRecord:
        """Repair only a proven journal-prefix crash without granting authority."""

        with self._locked(exclusive=True):
            return deepcopy(
                self._load_required_unlocked(
                    allow_consumed_cas=True,
                    repair_incomplete_publication=True,
                )
            )

    def _durable_publish_unlocked(
        self,
        target: Path,
        encoded: bytes,
        *,
        replace_existing: bool,
    ) -> None:
        self._ensure_directory(target.parent)
        if not replace_existing and os.path.lexists(target):
            raise ControlRecordIntegrityError(
                "A supposedly fresh Broker security record already exists."
            )
        directory_descriptor = os.open(
            target.parent,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor: int | None = None
        temporary_identity: tuple[int, int] | None = None
        published = False
        try:
            temporary_name = f".broker-control-{secrets.token_hex(8)}.tmp"
            descriptor = os.open(
                temporary_name,
                flags,
                0o600,
                dir_fd=directory_descriptor,
            )
            metadata = os.fstat(descriptor)
            temporary_identity = (metadata.st_dev, metadata.st_ino)
            stream = os.fdopen(descriptor, "wb")
            descriptor = None
            with stream:
                stream.write(encoded)
                stream.flush()
                os.fchmod(stream.fileno(), 0o600)
                os.fsync(stream.fileno())
            os.replace(
                temporary_name,
                target.name,
                src_dir_fd=directory_descriptor,
                dst_dir_fd=directory_descriptor,
            )
            published = True
            os.fsync(directory_descriptor)
        except BaseException as primary_error:
            cleanup_errors: list[BaseException] = []
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except BaseException as cleanup_error:
                    cleanup_errors.append(cleanup_error)
                descriptor = None
            if not published and temporary_identity is not None:
                try:
                    observed = os.stat(
                        temporary_name,
                        dir_fd=directory_descriptor,
                        follow_symlinks=False,
                    )
                except FileNotFoundError:
                    pass
                except BaseException as cleanup_error:
                    cleanup_errors.append(cleanup_error)
                else:
                    if (observed.st_dev, observed.st_ino) == temporary_identity:
                        removed = False
                        try:
                            os.unlink(
                                temporary_name,
                                dir_fd=directory_descriptor,
                            )
                            removed = True
                        except FileNotFoundError:
                            pass
                        except BaseException as cleanup_error:
                            cleanup_errors.append(cleanup_error)
                        if removed:
                            try:
                                os.fsync(directory_descriptor)
                            except BaseException as cleanup_error:
                                cleanup_errors.append(cleanup_error)
            try:
                os.close(directory_descriptor)
            except BaseException as cleanup_error:
                cleanup_errors.append(cleanup_error)
            for cleanup_error in cleanup_errors:
                try:
                    primary_error.add_note(
                        "Broker temporary cleanup also failed: "
                        f"{cleanup_error!r}"
                    )
                except AttributeError:
                    pass
            raise
        else:
            os.close(directory_descriptor)
        if self._read_private_bytes(
            target,
            len(encoded),
            "Published Broker security record",
        ) != encoded:
            raise ControlRecordIntegrityError(
                "Published Broker security-record readback mismatches the write."
            )

    def _append_control_record_unlocked(
        self,
        record: ControlDomainRecord,
    ) -> None:
        target = self._journal_path / self._record_filename(record)
        self._durable_publish_immutable_unlocked(
            target,
            _canonical_record_bytes(record),
            label="Broker control-journal record",
        )
        if self._read_control_record(target) != record:
            raise ControlRecordIntegrityError(
                "Persisted Broker journal readback mismatches the write."
            )

    def _append_cas_fence_unlocked(self, fence: _CASFenceRecord) -> None:
        target = self._fence_path / f"{fence.record_sha256}.json"
        self._durable_publish_immutable_unlocked(
            target,
            _canonical_fence_bytes(fence),
            label="Broker CAS-fence record",
        )
        if self._read_cas_fence(target) != fence:
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence readback mismatches the write."
            )

    def _durable_publish_immutable_unlocked(
        self,
        target: Path,
        encoded: bytes,
        *,
        label: str,
    ) -> None:
        """Atomically publish one content address without ever clobbering it."""

        self._ensure_directory(target.parent)
        directory_descriptor = os.open(
            target.parent,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor: int | None = None
        temporary_identity: tuple[int, int] | None = None
        content_tag = hashlib.sha256(encoded).hexdigest()
        temporary_name = (
            f".broker-control-{content_tag}-{secrets.token_hex(8)}.tmp"
        )
        published = False
        temporary_removed = False
        try:
            descriptor = os.open(
                temporary_name,
                flags,
                0o600,
                dir_fd=directory_descriptor,
            )
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise MutationCapsuleIntegrityError(
                    f"{label} temporary identity is unsafe."
                )
            temporary_identity = (before.st_dev, before.st_ino)
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise MutationCapsuleIntegrityError(
                        f"{label} temporary write made no progress."
                    )
                view = view[written:]
            os.fchmod(descriptor, 0o600)
            os.fsync(descriptor)
            after = os.fstat(descriptor)
            if (
                not stat.S_ISREG(after.st_mode)
                or after.st_nlink != 1
                or (after.st_dev, after.st_ino) != temporary_identity
                or after.st_size != len(encoded)
            ):
                raise MutationCapsuleIntegrityError(
                    f"{label} temporary identity changed."
                )
            os.close(descriptor)
            descriptor = None

            # link(2) is the portable atomic no-clobber publication primitive
            # available to this repository-only slice.  A pre-existing final
            # name fails with EEXIST and is never overwritten.
            os.link(
                temporary_name,
                target.name,
                src_dir_fd=directory_descriptor,
                dst_dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
            published = True
            temporary = os.stat(
                temporary_name,
                dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
            final = os.stat(
                target.name,
                dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
            if (
                (temporary.st_dev, temporary.st_ino) != temporary_identity
                or (final.st_dev, final.st_ino) != temporary_identity
                or temporary.st_nlink != 2
                or final.st_nlink != 2
            ):
                raise MutationCapsuleIntegrityError(
                    f"{label} publication identity mismatches."
                )
            os.unlink(temporary_name, dir_fd=directory_descriptor)
            temporary_removed = True
            os.fsync(directory_descriptor)
        except BaseException as primary_error:
            cleanup_errors: list[BaseException] = []
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except BaseException as cleanup_error:
                    cleanup_errors.append(cleanup_error)
            if not temporary_removed and temporary_identity is not None:
                try:
                    observed = os.stat(
                        temporary_name,
                        dir_fd=directory_descriptor,
                        follow_symlinks=False,
                    )
                except FileNotFoundError:
                    pass
                except BaseException as cleanup_error:
                    cleanup_errors.append(cleanup_error)
                else:
                    if (observed.st_dev, observed.st_ino) == temporary_identity:
                        try:
                            os.unlink(temporary_name, dir_fd=directory_descriptor)
                            os.fsync(directory_descriptor)
                        except FileNotFoundError:
                            pass
                        except BaseException as cleanup_error:
                            cleanup_errors.append(cleanup_error)
            try:
                os.close(directory_descriptor)
            except BaseException as cleanup_error:
                cleanup_errors.append(cleanup_error)
            for cleanup_error in cleanup_errors:
                try:
                    primary_error.add_note(
                        f"{label} temporary cleanup also failed: "
                        f"{cleanup_error!r}"
                    )
                except AttributeError:
                    pass
            raise
        else:
            os.close(directory_descriptor)
        if not published or self._read_immutable_bytes(
            target,
            len(encoded),
            f"Published {label}",
        ) != encoded:
            raise MutationCapsuleIntegrityError(
                f"Published {label} readback mismatches the write."
            )

    @staticmethod
    def _recover_immutable_publication_unlocked(
        target: Path,
        *,
        maximum: int,
        label: str,
        expected: bytes | None = None,
        refresh_directory_durability: bool = False,
        allow_link_repair: bool = True,
    ) -> bytes:
        """Finish a proven link-before-unlink crash prefix, then read exactly.

        The immutable publisher creates one hard link from a uniquely named
        temporary inode to its content-addressed final name. A process crash in
        that small window can leave exactly those two names. Recovery removes
        only the uniquely identified sibling name after proving both names are
        the same regular inode and that no third hard link exists.
        """

        try:
            target_status = target.lstat()
        except OSError as exc:
            raise MutationCapsuleIntegrityError(f"{label} is unavailable.") from exc
        if not stat.S_ISREG(target_status.st_mode):
            raise MutationCapsuleIntegrityError(f"{label} identity is unsafe.")
        if target_status.st_nlink == 1:
            if refresh_directory_durability or allow_link_repair:
                # Re-establish final-name durability when reusing an artifact
                # whose original directory-fsync response may have been lost.
                # Link-repair callers always require this proof: a prior repair
                # may have unlinked its temporary name and then lost the fsync
                # response before returning.
                try:
                    ControlDomainStore._fsync_directory(target.parent)
                except OSError as exc:
                    raise MutationCapsuleIntegrityError(
                        f"{label} directory durability cannot be proven."
                    ) from exc
            # The exact readback must follow the directory durability proof so
            # a path rebound during that proof cannot return stale authority
            # bytes from the prior named inode.
            raw = ControlDomainStore._read_immutable_bytes(
                target,
                maximum,
                label,
            )
            if expected is not None and raw != expected:
                raise MutationCapsuleIntegrityError(
                    f"{label} bytes do not match their expected content."
                )
            return raw
        if target_status.st_nlink != 2:
            raise MutationCapsuleIntegrityError(f"{label} identity is unsafe.")
        if not allow_link_repair:
            raise MutationCapsuleIntegrityError(f"{label} identity is unsafe.")

        try:
            siblings = tuple(target.parent.iterdir())
        except OSError as exc:
            raise MutationCapsuleIntegrityError(
                f"{label} directory is unavailable."
            ) from exc
        candidates: list[Path] = []
        for sibling in siblings:
            prefix = ".broker-control-"
            if not sibling.name.startswith(prefix) or not sibling.name.endswith(".tmp"):
                continue
            try:
                sibling_status = sibling.lstat()
            except OSError as exc:
                raise MutationCapsuleIntegrityError(
                    f"{label} temporary identity is unavailable."
                ) from exc
            if (
                stat.S_ISREG(sibling_status.st_mode)
                and sibling_status.st_dev == target_status.st_dev
                and sibling_status.st_ino == target_status.st_ino
            ):
                candidates.append(sibling)
        if len(candidates) != 1:
            raise MutationCapsuleIntegrityError(
                f"{label} incomplete publication is ambiguous."
            )
        temporary = candidates[0]
        try:
            raw = ControlDomainStore._read_linked_immutable_bytes(
                target,
                maximum,
                label,
                expected_links=2,
            )
        except OSError as exc:
            raise MutationCapsuleIntegrityError(f"{label} is unreadable.") from exc
        if expected is not None and raw != expected:
            raise MutationCapsuleIntegrityError(
                f"{label} incomplete publication bytes mismatch."
            )
        content_tag = hashlib.sha256(raw).hexdigest()
        expected_prefix = f".broker-control-{content_tag}-"
        if (
            not temporary.name.startswith(expected_prefix)
            or len(temporary.name)
            != len(expected_prefix) + 16 + len(".tmp")
            or any(
                character not in "0123456789abcdef"
                for character in temporary.name[
                    len(expected_prefix) : -len(".tmp")
                ]
            )
        ):
            raise MutationCapsuleIntegrityError(
                f"{label} incomplete publication provenance is invalid."
            )
        try:
            current_target = target.lstat()
            current_temporary = temporary.lstat()
        except OSError as exc:
            raise MutationCapsuleIntegrityError(
                f"{label} incomplete publication changed."
            ) from exc
        identity = (target_status.st_dev, target_status.st_ino)
        if (
            (current_target.st_dev, current_target.st_ino) != identity
            or (current_temporary.st_dev, current_temporary.st_ino) != identity
            or current_target.st_nlink != 2
            or current_temporary.st_nlink != 2
            or not stat.S_ISREG(current_target.st_mode)
            or not stat.S_ISREG(current_temporary.st_mode)
        ):
            raise MutationCapsuleIntegrityError(
                f"{label} incomplete publication changed."
            )
        directory_descriptor: int | None = None
        try:
            directory_descriptor = os.open(
                target.parent,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
            )
            final_status = os.stat(
                target.name,
                dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
            temporary_status = os.stat(
                temporary.name,
                dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
            if (
                (final_status.st_dev, final_status.st_ino) != identity
                or (temporary_status.st_dev, temporary_status.st_ino) != identity
                or final_status.st_nlink != 2
                or temporary_status.st_nlink != 2
                or not stat.S_ISREG(final_status.st_mode)
                or not stat.S_ISREG(temporary_status.st_mode)
            ):
                raise MutationCapsuleIntegrityError(
                    f"{label} incomplete publication changed."
                )
            os.unlink(temporary.name, dir_fd=directory_descriptor)
            os.fsync(directory_descriptor)
        except MutationCapsuleIntegrityError:
            raise
        except OSError as exc:
            raise MutationCapsuleIntegrityError(
                f"{label} incomplete publication cannot be recovered."
            ) from exc
        finally:
            if directory_descriptor is not None:
                os.close(directory_descriptor)
        return ControlDomainStore._read_immutable_bytes(
            target,
            maximum,
            label,
        )

    @staticmethod
    def _read_linked_immutable_bytes(
        path: Path,
        maximum: int,
        label: str,
        *,
        expected_links: int,
    ) -> bytes:
        """Read a stable regular inode with an explicitly proven link count."""

        flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            descriptor = os.open(path, flags)
        except OSError as exc:
            raise MutationCapsuleIntegrityError(f"{label} is unreadable.") from exc
        try:
            before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != expected_links
            ):
                raise MutationCapsuleIntegrityError(f"{label} identity is unsafe.")
            chunks: list[bytes] = []
            remaining = maximum + 1
            while remaining:
                chunk = os.read(descriptor, min(65_536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
            after = os.fstat(descriptor)
            named = path.lstat()
            if (
                before.st_dev != after.st_dev
                or before.st_ino != after.st_ino
                or before.st_mode != after.st_mode
                or before.st_nlink != after.st_nlink
                or before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns
                or before.st_ctime_ns != after.st_ctime_ns
                or named.st_dev != after.st_dev
                or named.st_ino != after.st_ino
                or stat.S_IFMT(named.st_mode) != stat.S_IFMT(after.st_mode)
                or named.st_nlink != expected_links
                or named.st_size != after.st_size
                or named.st_mtime_ns != after.st_mtime_ns
                or named.st_ctime_ns != after.st_ctime_ns
            ):
                raise MutationCapsuleIntegrityError(f"{label} identity changed.")
        except MutationCapsuleIntegrityError:
            raise
        except OSError as exc:
            raise MutationCapsuleIntegrityError(f"{label} is unreadable.") from exc
        finally:
            os.close(descriptor)
        if len(raw) > maximum:
            raise MutationCapsuleIntegrityError(f"{label} is too large.")
        return raw

    @staticmethod
    def _content_filename(digest: str, suffix: str) -> str:
        if not _is_sha256(digest):
            raise MutationCapsuleIntegrityError(
                "Content-addressed Broker identity is invalid."
            )
        return f"{digest}{suffix}"

    def _immutable_entry_paths_unlocked(
        self,
        directory: Path,
        *,
        suffix: str,
        label: str,
    ) -> tuple[Path, ...]:
        if not os.path.lexists(directory):
            return ()
        try:
            directory_status = directory.lstat()
        except OSError as exc:
            raise MutationCapsuleIntegrityError(
                f"{label} directory is unavailable."
            ) from exc
        if not stat.S_ISDIR(directory_status.st_mode):
            raise MutationCapsuleIntegrityError(
                f"{label} directory identity is unsafe."
            )
        paths: list[Path] = []
        for path in directory.iterdir():
            if path.name == "blobs":
                try:
                    child_status = path.lstat()
                except OSError as exc:
                    raise MutationCapsuleIntegrityError(
                        f"{label} blob directory is unavailable."
                    ) from exc
                if not stat.S_ISDIR(child_status.st_mode):
                    raise MutationCapsuleIntegrityError(
                        f"{label} blob directory identity is unsafe."
                    )
                continue
            if path.name.startswith(".broker-control-") and path.name.endswith(
                ".tmp"
            ):
                continue
            if (
                len(path.name) != 64 + len(suffix)
                or not path.name.endswith(suffix)
                or not _is_sha256(path.name[:64])
            ):
                raise MutationCapsuleIntegrityError(
                    f"{label} directory contains an invalid entry."
                )
            paths.append(path)
        return tuple(paths)

    def _capsules_unlocked(self) -> tuple[MutationCapsule, ...]:
        paths = self._immutable_entry_paths_unlocked(
            self._capsule_path,
            suffix=".json",
            label="Broker mutation-capsule",
        )
        if len(paths) > MAX_CAPSULES:
            raise MutationCapsuleIntegrityError(
                "Broker mutation-capsule history is too large."
            )
        capsules: list[MutationCapsule] = []
        seen_envelope_ids: set[str] = set()
        seen_nonces: set[str] = set()
        seen_hashes: set[str] = set()
        for path in paths:
            raw = self._recover_immutable_publication_unlocked(
                path,
                maximum=32 * 1024,
                label="Persisted Broker mutation capsule",
                allow_link_repair=False,
            )
            capsule = parse_capsule_bytes(raw)
            digest = path.name[:-5]
            if capsule.capsule_sha256 != digest or digest in seen_hashes:
                raise MutationCapsuleIntegrityError(
                    "Persisted mutation-capsule identity mismatches."
                )
            if (
                capsule.external_envelope_id in seen_envelope_ids
                or capsule.external_envelope_nonce in seen_nonces
            ):
                raise MutationCapsuleIntegrityError(
                    "Persisted mutation-capsule authority replay is ambiguous."
                )
            seen_hashes.add(digest)
            seen_envelope_ids.add(capsule.external_envelope_id)
            seen_nonces.add(capsule.external_envelope_nonce)
            capsules.append(capsule)
        return tuple(capsules)

    def _load_capsule_unlocked(self, capsule_sha256: str) -> MutationCapsule:
        self._require_capsule_directories_unlocked(require_blob=False)
        target = self._capsule_path / self._content_filename(
            capsule_sha256,
            ".json",
        )
        raw = self._recover_immutable_publication_unlocked(
            target,
            maximum=32 * 1024,
            label="Persisted Broker mutation capsule",
            allow_link_repair=False,
        )
        capsule = parse_capsule_bytes(raw)
        if capsule.capsule_sha256 != capsule_sha256:
            raise MutationCapsuleIntegrityError(
                "Persisted mutation-capsule identity mismatches."
            )
        return capsule

    def _load_capsule_decision_unlocked(
        self,
        capsule_sha256: str,
    ) -> tuple[MutationCapsule, MutationDecision]:
        self._require_capsule_directories_unlocked(require_blob=True)
        capsule = self._load_capsule_unlocked(capsule_sha256)
        blob_target = self._blob_path / self._content_filename(
            capsule.target_blob_sha256,
            ".blob",
        )
        raw = self._recover_immutable_publication_unlocked(
            blob_target,
            maximum=_MAX_TARGET_BYTES,
            label="Persisted Broker mutation target blob",
            expected=None,
            allow_link_repair=False,
        )
        decision = capsule.reconstruct_decision(raw)
        return capsule, decision

    def _require_capsule_directories_unlocked(
        self,
        *,
        require_blob: bool,
    ) -> None:
        for directory, label, required in (
            (self._capsule_path, "Broker mutation-capsule", True),
            (self._blob_path, "Broker mutation-blob", require_blob),
        ):
            if not os.path.lexists(directory):
                if required:
                    raise MutationCapsuleIntegrityError(
                        f"{label} directory is absent."
                    )
                continue
            try:
                metadata = directory.lstat()
            except OSError as exc:
                raise MutationCapsuleIntegrityError(
                    f"{label} directory is unavailable."
                ) from exc
            if not stat.S_ISDIR(metadata.st_mode):
                raise MutationCapsuleIntegrityError(
                    f"{label} directory identity is unsafe."
                )

    def _publish_capsule_unlocked(
        self,
        decision: MutationDecision,
        current: ControlDomainRecord,
        envelope: Any,
    ) -> MutationCapsule:
        capsule = mutation_capsule_for(decision, current, envelope)
        existing = self._capsules_unlocked()
        if any(
            prior.external_envelope_id == capsule.external_envelope_id
            or prior.external_envelope_nonce == capsule.external_envelope_nonce
            for prior in existing
        ):
            raise AuthorityRejectedError(
                "Execution envelope identity or nonce was already consumed."
            )
        if len(existing) >= MAX_CAPSULES:
            raise ControlRecordIntegrityError(
                "Broker mutation-capsule capacity is exhausted."
            )
        verify_envelope_scope(envelope, decision, current, capsule)

        blob_target = self._blob_path / self._content_filename(
            capsule.target_blob_sha256,
            ".blob",
        )
        if os.path.lexists(blob_target):
            raw = self._recover_immutable_publication_unlocked(
                blob_target,
                maximum=_MAX_TARGET_BYTES,
                label="Persisted Broker mutation target blob",
                expected=decision.target_bytes,
                refresh_directory_durability=True,
                allow_link_repair=False,
            )
            if raw != decision.target_bytes:
                raise MutationCapsuleIntegrityError(
                    "Existing content-addressed target blob mismatches."
                )
        else:
            self._durable_publish_immutable_unlocked(
                blob_target,
                decision.target_bytes,
                label="Broker mutation target blob",
            )
        if self._read_immutable_bytes(
            blob_target,
            _MAX_TARGET_BYTES,
            "Published Broker mutation target blob",
        ) != decision.target_bytes:
            raise MutationCapsuleIntegrityError(
                "Published mutation target-blob readback mismatches."
            )

        capsule_target = self._capsule_path / self._content_filename(
            capsule.capsule_sha256,
            ".json",
        )
        self._durable_publish_immutable_unlocked(
            capsule_target,
            canonical_capsule_bytes(capsule),
            label="Broker mutation capsule",
        )
        published = self._load_capsule_unlocked(capsule.capsule_sha256)
        if published != capsule:
            raise MutationCapsuleIntegrityError(
                "Published mutation-capsule readback mismatches."
            )
        return published

    def _replace_head_unlocked(self, record: ControlDomainRecord) -> None:
        self._durable_publish_unlocked(
            self.path,
            _canonical_record_bytes(record),
            replace_existing=True,
        )
        if self._read_control_record(self.path) != record:
            raise ControlRecordIntegrityError(
                "Persisted Broker control-record head readback mismatches."
            )

    def _publish_unlocked(self, record: ControlDomainRecord) -> ControlDomainRecord:
        self._append_control_record_unlocked(record)
        self._replace_head_unlocked(record)
        published = self._load_required_unlocked()
        if published != record:
            raise ControlRecordIntegrityError(
                "Persisted Broker control-record readback mismatches the write."
            )
        return published

    @staticmethod
    def _prospective_record(
        current: ControlDomainRecord,
        state: ControlDomainState,
    ) -> ControlDomainRecord:
        retired = current.retired_authority_domain_ids
        if state is ControlDomainState.ABANDONED:
            retired = (*retired, current.activation.authority_domain_id)
        return _new_record(
            current.activation,
            state=state,
            journal_position=current.journal_position + 1,
            predecessor_record_sha256=current.record_sha256,
            retired_authority_domain_ids=retired,
        )

    @classmethod
    def _assert_future_abandonment_fits(
        cls,
        active: ControlDomainRecord,
    ) -> None:
        if len(active.retired_authority_domain_ids) >= _MAX_RETIRED_DOMAINS:
            raise ControlDomainTransitionError(
                "Broker authority-domain retirement capacity is exhausted."
            )
        try:
            cls._prospective_record(active, ControlDomainState.ABANDONED)
            uncertain = cls._prospective_record(
                active,
                ControlDomainState.UNCERTAIN,
            )
            cls._prospective_record(uncertain, ControlDomainState.ABANDONED)
        except ControlRecordIntegrityError as exc:
            raise ControlDomainTransitionError(
                "Broker authority cannot reserve durable abandonment capacity."
            ) from exc

    def activate_initial(self, activation: ActivationTuple) -> ControlDomainRecord:
        try:
            activation = _snapshot_activation(activation)
        except ValueError as exc:
            raise ControlDomainTransitionError(
                "Initial Broker authority requires a complete activation tuple."
            ) from exc
        with self._locked(exclusive=True):
            if self._load_unlocked(
                repair_incomplete_publication=True,
            ) is not None:
                raise ControlDomainTransitionError(
                    "Initial Broker authority already exists."
                )
            record = _new_record(
                activation,
                state=ControlDomainState.ACTIVE,
                journal_position=0,
                predecessor_record_sha256=GENESIS_CONTROL_RECORD_HASH,
                retired_authority_domain_ids=(),
            )
            self._assert_future_abandonment_fits(record)
            if self._authentication_key is not None:
                encoded_authenticator = (
                    canonical_json(
                        self._authenticator_payload(
                            self._authentication_key,
                            control_path=self.path,
                        )
                    )
                    + "\n"
                ).encode("utf-8")
                if os.path.lexists(self._authenticator_path):
                    observed_authenticator = (
                        self._recover_immutable_publication_unlocked(
                            self._authenticator_path,
                            maximum=4 * 1024,
                            label="Persisted Broker execution authenticator",
                            expected=encoded_authenticator,
                        )
                    )
                else:
                    self._durable_publish_immutable_unlocked(
                        self._authenticator_path,
                        encoded_authenticator,
                        label="Broker execution authenticator",
                    )
                    observed_authenticator = self._read_private_bytes(
                        self._authenticator_path,
                        4 * 1024,
                        "Persisted Broker execution authenticator",
                    )
                if observed_authenticator != encoded_authenticator:
                    raise ControlRecordIntegrityError(
                        "Persisted Broker execution authenticator readback mismatches."
                    )
            return self._publish_unlocked(record)

    def transition(
        self,
        expected_activation: ActivationTuple,
        target_state: ControlDomainState,
    ) -> ControlDomainRecord:
        if not _is_canonical_enum_member(
            target_state,
            ControlDomainState,
        ):
            raise ControlDomainTransitionError(
                "Requested Broker control-domain state is invalid."
            )
        target = target_state
        allowed = {
            ControlDomainState.ACTIVE: {
                ControlDomainState.ABANDONED,
                ControlDomainState.UNCERTAIN,
            },
            ControlDomainState.UNCERTAIN: {ControlDomainState.ABANDONED},
            ControlDomainState.ABANDONED: set(),
        }
        with self._locked(exclusive=True):
            current = self._load_required_unlocked(
                repair_incomplete_publication=True,
            )
            self._require_exact_activation(current, expected_activation)
            if target is ControlDomainState.ABANDONED:
                journal = self._journal_records_unlocked()
                fences = self._cas_fences_unlocked(journal)
                intents = {
                    fence.record_sha256
                    for fence in fences
                    if fence.kind == "INTENT"
                    and fence.activation_sha256
                    == _activation_sha256(current.activation)
                }
                completed = {
                    fence.intent_sha256
                    for fence in fences
                    if fence.kind == "COMPLETE"
                }
                if intents.difference(completed):
                    raise ControlDomainTransitionError(
                        "A pending CAS intent must be reconciled before abandonment."
                    )
            if target not in allowed[current.state]:
                raise ControlDomainTransitionError(
                    f"{current.state.value} -> {target.value} is forbidden."
                )
            return self._publish_unlocked(
                self._prospective_record(current, target)
            )

    def activate_successor(
        self,
        expected_predecessor: ControlDomainRecord,
        activation: ActivationTuple,
    ) -> ControlDomainRecord:
        if type(expected_predecessor) is not ControlDomainRecord:
            raise ControlDomainTransitionError(
                "Successor activation requires the exact abandoned predecessor."
            )
        try:
            activation = _snapshot_activation(activation)
        except ValueError as exc:
            raise ControlDomainTransitionError(
                "Successor Broker authority requires a complete activation tuple."
            ) from exc
        with self._locked(exclusive=True):
            current = self._load_required_unlocked(
                repair_incomplete_publication=True,
            )
            journal = self._journal_records_unlocked()
            try:
                predecessor_bytes = _canonical_record_bytes(expected_predecessor)
            except (
                AttributeError,
                ControlRecordIntegrityError,
                TypeError,
                ValueError,
            ) as exc:
                raise ControlDomainTransitionError(
                    "Successor activation requires the exact abandoned predecessor."
                ) from exc
            if _canonical_record_bytes(current) != predecessor_bytes:
                raise AuthorityRejectedError(
                    "Successor predecessor does not match the current control head."
                )
            if current.state is not ControlDomainState.ABANDONED:
                raise ControlDomainTransitionError(
                    "A successor requires an abandoned predecessor domain."
                )
            if activation.repository_id != current.activation.repository_id:
                raise ControlDomainTransitionError(
                    "A successor cannot change the logical repository identity."
                )
            if (
                activation.protected_repository_identity
                == current.activation.protected_repository_identity
            ):
                raise ControlDomainTransitionError(
                    "A successor requires a fresh protected-repository identity."
                )
            if (
                activation.write_principal_identity
                == current.activation.write_principal_identity
            ):
                raise ControlDomainTransitionError(
                    "A successor requires a fresh logical write-principal identity."
                )
            historical_domains = {
                record.activation.authority_domain_id for record in journal
            }
            if activation.authority_domain_id in historical_domains:
                raise ControlDomainTransitionError(
                    "A retired authority-domain identity cannot become current."
                )
            historical_protected_identities = {
                record.activation.protected_repository_identity
                for record in journal
            }
            if (
                activation.protected_repository_identity
                in historical_protected_identities
            ):
                raise ControlDomainTransitionError(
                    "A retired protected-repository identity cannot become current."
                )
            historical_principal_identities = {
                record.activation.write_principal_identity
                for record in journal
            }
            if (
                activation.write_principal_identity
                in historical_principal_identities
            ):
                raise ControlDomainTransitionError(
                    "A retired logical write-principal identity cannot become current."
                )
            record = _new_record(
                activation,
                state=ControlDomainState.ACTIVE,
                journal_position=current.journal_position + 1,
                predecessor_record_sha256=current.record_sha256,
                retired_authority_domain_ids=(
                    current.retired_authority_domain_ids
                ),
            )
            self._assert_future_abandonment_fits(record)
            return self._publish_unlocked(record)

    @staticmethod
    def _require_exact_activation(
        current: ControlDomainRecord,
        expected: ActivationTuple,
    ) -> None:
        try:
            expected_hash = _activation_sha256(_snapshot_activation(expected))
        except ValueError as exc:
            raise AuthorityRejectedError(
                "Activation tuple does not match current Broker authority."
            ) from exc
        if _activation_sha256(current.activation) != expected_hash:
            raise AuthorityRejectedError(
                "Activation tuple does not match current Broker authority."
            )

    def require_active(
        self,
        expected_activation: ActivationTuple,
    ) -> ControlDomainRecord:
        with self._locked(exclusive=False):
            current = self._load_required_unlocked()
            self._require_exact_activation(current, expected_activation)
            if current.state is not ControlDomainState.ACTIVE:
                raise AuthorityRejectedError(
                    "Current Broker control domain is not ACTIVE."
                )
            return deepcopy(current)

    @staticmethod
    def _snapshot_cas_decision(decision: MutationDecision) -> MutationDecision:
        """Validate one public CAS argument without exposing wrapper behavior."""

        try:
            return _snapshot_decision(decision)
        except MutationDecisionError:
            raise
        except (AttributeError, TypeError, ValueError) as exc:
            raise MutationDecisionError(
                "A CAS operation requires one exact bound mutation decision."
            ) from exc

    @staticmethod
    def _decision_sha256(decision: MutationDecision) -> str:
        return hash_payload(MutationDecision.binding_dict(decision))

    def _mark_pending_cas_uncertain_unlocked(
        self,
        current: ControlDomainRecord,
    ) -> ControlDomainRecord:
        """Consume an ACTIVE domain after its durable intent already exists."""

        if current.state is ControlDomainState.ACTIVE:
            return self._publish_unlocked(
                self._prospective_record(
                    current,
                    ControlDomainState.UNCERTAIN,
                )
            )
        if current.state is ControlDomainState.UNCERTAIN:
            return current
        raise ControlRecordIntegrityError(
            "An abandoned Broker domain has an incomplete CAS intent."
        )

    def _finish_cas_state_unlocked(
        self,
        current: ControlDomainRecord,
        outcome: ReconciliationOutcome,
    ) -> None:
        """Make an exact terminal result non-reusable before returning it."""

        if outcome is ReconciliationOutcome.UNCERTAIN:
            if current.state not in {
                ControlDomainState.UNCERTAIN,
                ControlDomainState.ABANDONED,
            }:
                raise ControlRecordIntegrityError(
                    "An uncertain CAS completion has an invalid control state."
                )
            return
        if current.state is ControlDomainState.UNCERTAIN:
            self._publish_unlocked(
                self._prospective_record(
                    current,
                    ControlDomainState.ABANDONED,
                )
            )
            return
        if current.state is not ControlDomainState.ABANDONED:
            raise ControlRecordIntegrityError(
                "An exact CAS completion has an invalid control state."
            )

    def _execute_authenticated_live_cas(
        self,
        envelope: AuthenticatedExecutionEnvelope,
        proposal_path: Path,
        protected_root: Path,
    ) -> ReconciliationOutcome:
        """Publish capsule then intent and perform one authenticated live CAS.

        Authentication is checked once before entering this method and again
        while the exclusive serializer is held.  The latter closes expiry and
        caller-mutation races before any capsule or intent can be published.
        """

        if type(envelope) is not AuthenticatedExecutionEnvelope:
            raise MutationDecisionError(
                "Authenticated live CAS requires one exact envelope snapshot."
            )
        if type(self) is not ControlDomainStore:
            raise AuthorityRejectedError(
                "Authenticated live CAS requires the exact Broker store type."
            )
        # Lazy import avoids making broker_control depend on the public apply
        # module at import time while keeping the mutation implementation fused
        # to this transaction rather than caller-supplied as a callback.
        from decision_os.companion import broker_apply

        protected_root = broker_apply._snapshot_filesystem_path(
            protected_root,
            "Protected root",
        )
        proposal_path = broker_apply._snapshot_filesystem_path(
            proposal_path,
            "Proposal path",
        )
        self._require_coherent_routing()
        expected_control_path = (
            protected_root.parent / broker_apply.CANONICAL_CONTROL_RELATIVE_PATH
        ).absolute()
        broker_apply._require_separate_control_directory(
            protected_root,
            expected_control_path,
        )
        if self.path != expected_control_path:
            raise AuthorityRejectedError(
                "Broker control store is not canonical for the protected root."
            )
        preverified = self._verify_execution_envelope(envelope)
        # The key commitment is part of authenticated authority, so prove it
        # before opening caller-selected proposal data. Expiry and the same
        # commitment are checked again under the live transaction lock.
        with self._locked(exclusive=True):
            self._require_authentication_key_commitment_unlocked()
        try:
            envelope_activation = ActivationTuple(
                authority_domain_id=preverified.authority_domain_id,
                repository_id=preverified.repository_id,
                protected_repository_identity=(
                    preverified.protected_repository_identity
                ),
                write_principal_identity=preverified.write_principal_identity,
                generation_witness=preverified.generation_witness,
            )
            envelope_operation = MutationOperation(preverified.operation)
        except (TypeError, ValueError) as exc:
            raise MutationDecisionError(
                "Authenticated envelope cannot form an exact mutation scope."
            ) from exc
        acquired = broker_apply.acquire_mutation_decision(
            proposal_path,
            activation=envelope_activation,
            operation=envelope_operation,
            relative_path=preverified.relative_path,
            expected_prior_sha256=preverified.expected_prior_sha256,
        )
        acquisition = broker_apply._snapshot_acquired(acquired)
        decision = self._snapshot_cas_decision(acquisition.decision)
        if (
            len(decision.target_bytes) != preverified.target_byte_count
            or decision.expected_post_sha256 != preverified.expected_post_sha256
            or decision.proposal_acquisition_sha256
            != preverified.proposal_acquisition_sha256
            or self._decision_sha256(decision) != preverified.decision_sha256
        ):
            raise AuthorityRejectedError(
                "Fd-acquired proposal does not match authenticated authority."
            )
        opened_root_fd = broker_apply._open_protected_root(protected_root)
        try:
            root_fd = broker_apply._duplicate_protected_root(opened_root_fd)
            try:
                broker_apply._require_bound_protected_root(
                    root_fd,
                    decision.activation,
                )
                with self._locked(exclusive=True):
                    self._require_authentication_key_commitment_unlocked()
                    current = self._load_required_unlocked(
                        allow_consumed_cas=True,
                        repair_incomplete_publication=True,
                    )
                    self._require_exact_activation(current, decision.activation)
                    journal = self._journal_records_unlocked()
                    intent, completion = self._cas_exchange_unlocked(
                        journal,
                        decision.activation,
                        self._decision_sha256(decision),
                    )
                    if intent is not None or completion is not None:
                        raise AuthorityRejectedError(
                            "Broker authority already has a consumed CAS intent; "
                            "live apply cannot resume it."
                        )
                    if current.state is not ControlDomainState.ACTIVE:
                        raise AuthorityRejectedError(
                            "A non-ACTIVE Broker domain cannot execute live CAS apply."
                        )
                    if len(self._cas_fences_unlocked(journal)) > _MAX_CAS_FENCES - 2:
                        raise ControlRecordIntegrityError(
                            "Broker CAS-fence capacity is exhausted."
                        )

                    verified_envelope = self._verify_execution_envelope(envelope)
                    if (
                        type(verified_envelope) is not AuthenticatedExecutionEnvelope
                        or verified_envelope != envelope
                    ):
                        raise AuthorityRejectedError(
                            "Execution envelope changed before durable authorization."
                        )
                    capsule = self._publish_capsule_unlocked(
                        decision,
                        current,
                        verified_envelope,
                    )

                    intent = _new_cas_intent(
                        decision,
                        current,
                        capsule_sha256=capsule.capsule_sha256,
                    )
                    self._append_cas_fence_unlocked(intent)
                    current = self._mark_pending_cas_uncertain_unlocked(current)

                    try:
                        with broker_apply._open_parent_from_root(
                            root_fd,
                            decision.relative_path,
                        ) as (parent_fd, name):
                            outcome = broker_apply._attempt_live(
                                parent_fd,
                                name,
                                decision,
                            )
                    except broker_apply.BrokerApplyError:
                        outcome = ReconciliationOutcome.UNCERTAIN
                    if not _is_canonical_enum_member(outcome, ReconciliationOutcome):
                        raise MutationDecisionError(
                            "Live CAS attempt outcome is invalid."
                        )
                    if outcome is ReconciliationOutcome.NOT_APPLIED:
                        raise MutationDecisionError(
                            "NOT_APPLIED is available only through CAS recovery."
                        )
                    completion = _complete_cas_intent(intent, outcome)
                    self._append_cas_fence_unlocked(completion)
                    self._finish_cas_state_unlocked(current, outcome)
                    return outcome
            finally:
                os.close(root_fd)
        finally:
            os.close(opened_root_fd)

    def _decision_for_capsule_intent_unlocked(
        self,
        intent: _CASFenceRecord,
        journal: tuple[ControlDomainRecord, ...],
    ) -> MutationDecision:
        if intent.kind != "INTENT" or intent.capsule_sha256 is None:
            raise MutationCapsuleIntegrityError(
                "Pending CAS intent has no bound mutation capsule."
            )
        capsule, decision = self._load_capsule_decision_unlocked(
            intent.capsule_sha256
        )
        control_by_hash = {record.record_sha256: record for record in journal}
        bound_control = control_by_hash.get(intent.control_record_sha256)
        if (
            bound_control is None
            or bound_control.state is not ControlDomainState.ACTIVE
            or capsule.control_record_sha256 != intent.control_record_sha256
            or capsule.authority_domain_id != intent.authority_domain_id
            or capsule.activation_sha256 != intent.activation_sha256
            or capsule.decision_sha256 != intent.decision_sha256
            or self._decision_sha256(decision) != intent.decision_sha256
            or _activation_sha256(decision.activation) != intent.activation_sha256
            or bound_control.activation != decision.activation
        ):
            raise MutationCapsuleIntegrityError(
                "Pending CAS intent and mutation capsule do not match."
            )
        return decision

    def _execute_pending_recovery_cas(
        self,
        protected_root: Path,
    ) -> ReconciliationOutcome:
        """Recover the only incomplete capsule-bound intent without caller data."""

        from decision_os.companion import broker_apply

        protected_root = broker_apply._snapshot_filesystem_path(
            protected_root,
            "Protected root",
        )
        self._require_coherent_routing()
        expected_control_path = (
            protected_root.parent / broker_apply.CANONICAL_CONTROL_RELATIVE_PATH
        ).absolute()
        broker_apply._require_separate_control_directory(
            protected_root,
            expected_control_path,
        )
        if self.path != expected_control_path:
            raise AuthorityRejectedError(
                "Broker control store is not canonical for the protected root."
            )
        opened_root_fd = broker_apply._open_protected_root(protected_root)
        try:
            root_fd = broker_apply._duplicate_protected_root(opened_root_fd)
            try:
                return self._execute_pending_recovery_cas_owned(
                    protected_root,
                    root_fd,
                )
            finally:
                os.close(root_fd)
        finally:
            os.close(opened_root_fd)

    def _execute_pending_recovery_cas_owned(
        self,
        protected_root: Path,
        root_fd: int,
    ) -> ReconciliationOutcome:
        """Recover while owning the protected-root descriptor for the transaction."""

        from decision_os.companion import broker_apply

        if type(self) is not ControlDomainStore:
            raise AuthorityRejectedError(
                "CAS recovery requires the exact Broker store type."
            )
        protected_root = broker_apply._snapshot_filesystem_path(
            protected_root,
            "Protected root",
        )
        self._require_coherent_routing()
        expected_control_path = (
            protected_root.parent / broker_apply.CANONICAL_CONTROL_RELATIVE_PATH
        ).absolute()
        broker_apply._require_separate_control_directory(
            protected_root,
            expected_control_path,
        )
        if self.path != expected_control_path:
            raise AuthorityRejectedError(
                "Broker control store is not canonical for the protected root."
            )
        if type(root_fd) is not int or root_fd < 0:
            raise MutationDecisionError(
                "CAS recovery requires one exact protected-root descriptor."
            )
        owned_root_fd = broker_apply._duplicate_protected_root(root_fd)
        try:
            comparison_fd = broker_apply._open_protected_root(protected_root)
            try:
                supplied_identity = os.fstat(owned_root_fd)
                expected_identity = os.fstat(comparison_fd)
            finally:
                os.close(comparison_fd)
            if (
                supplied_identity.st_dev,
                supplied_identity.st_ino,
            ) != (
                expected_identity.st_dev,
                expected_identity.st_ino,
            ):
                raise AuthorityRejectedError(
                    "CAS recovery descriptor is not the canonical protected root."
                )
            with self._locked(exclusive=True):
                current = self._load_required_unlocked(
                    allow_consumed_cas=True,
                    repair_incomplete_publication=True,
                )
                journal = self._journal_records_unlocked()
                fences = self._cas_fences_unlocked(journal)
                completed_intents = {
                    fence.intent_sha256
                    for fence in fences
                    if fence.kind == "COMPLETE"
                }
                intents_by_hash = {
                    fence.record_sha256: fence
                    for fence in fences
                    if fence.kind == "INTENT"
                }
                pending = [
                    fence
                    for fence in fences
                    if fence.kind == "INTENT"
                    and fence.record_sha256 not in completed_intents
                ]
                completion: _CASFenceRecord | None = None
                if len(pending) == 1:
                    intent = pending[0]
                elif not pending and current.state is ControlDomainState.UNCERTAIN:
                    unfinished_terminal = [
                        fence
                        for fence in fences
                        if fence.kind == "COMPLETE"
                        and fence.outcome
                        in {
                            ReconciliationOutcome.APPLIED.value,
                            ReconciliationOutcome.NOT_APPLIED.value,
                        }
                        and fence.authority_domain_id
                        == current.activation.authority_domain_id
                    ]
                    if len(unfinished_terminal) != 1:
                        raise AuthorityRejectedError(
                            "Recovery requires exactly one durable pending CAS intent."
                        )
                    completion = unfinished_terminal[0]
                    assert completion.intent_sha256 is not None
                    intent = intents_by_hash[completion.intent_sha256]
                else:
                    raise AuthorityRejectedError(
                        "Recovery requires exactly one durable pending CAS intent."
                    )
                decision = self._decision_for_capsule_intent_unlocked(intent, journal)
                # The ordinary lifecycle forbids successors while an intent is
                # incomplete. Requiring this exact domain prevents recovery from
                # perturbing an unrelated head if journal evidence is forged.
                if current.activation.authority_domain_id != intent.authority_domain_id:
                    raise MutationCapsuleIntegrityError(
                        "Pending CAS intent belongs to another authority domain."
                    )
                # Request routing must remain bound even when recovery only needs
                # to finish a completion that was durable before a process crash.
                broker_apply._require_bound_protected_root(
                    owned_root_fd,
                    decision.activation,
                )
                if completion is not None:
                    # The first process may have linked and read back the exact
                    # completion but lost the fence-directory fsync response.
                    # Re-establish name durability and rescan the complete
                    # fence graph before publishing an ABANDONED head that
                    # depends on this terminal evidence.
                    self._fsync_directory(self._fence_path)
                    refreshed_fences = self._cas_fences_unlocked(journal)
                    if completion not in refreshed_fences:
                        raise ControlRecordIntegrityError(
                            "Durable CAS completion changed before recovery."
                        )
                    assert completion.outcome is not None
                    outcome = ReconciliationOutcome(completion.outcome)
                    self._finish_cas_state_unlocked(current, outcome)
                    return outcome
                current = self._mark_pending_cas_uncertain_unlocked(current)
                observation = broker_apply._recovery_observation_from_root_fd(
                    owned_root_fd,
                    decision,
                )
                try:
                    observation = _snapshot_observation(observation)
                except MutationDecisionError:
                    raise
                except (AttributeError, TypeError, ValueError) as exc:
                    raise MutationDecisionError(
                        "CAS recovery requires one exact target observation."
                    ) from exc
                outcome = reconcile_mutation(decision, observation)
                completion = _complete_cas_intent(intent, outcome)
                self._append_cas_fence_unlocked(completion)
                self._finish_cas_state_unlocked(current, outcome)
                return outcome
        finally:
            os.close(owned_root_fd)

    def _reconstruct_pending_decision(self) -> MutationDecision:
        """Test/diagnostic seam returning only a proven pending capsule decision."""

        with self._locked(exclusive=False):
            self._load_required_unlocked(allow_consumed_cas=True)
            journal = self._journal_records_unlocked()
            fences = self._cas_fences_unlocked(journal)
            completed_intents = {
                fence.intent_sha256
                for fence in fences
                if fence.kind == "COMPLETE"
            }
            pending = [
                fence
                for fence in fences
                if fence.kind == "INTENT"
                and fence.record_sha256 not in completed_intents
            ]
            if len(pending) != 1 or pending[0].capsule_sha256 is None:
                raise AuthorityRejectedError(
                    "Exactly one capsule-bound pending intent is required."
                )
            return self._decision_for_capsule_intent_unlocked(
                pending[0],
                journal,
            )


__all__ = [
    "ActivationTuple",
    "AuthorityRejectedError",
    "BrokerControlError",
    "CONTROL_DOMAIN_SCHEMA",
    "ControlDomainRecord",
    "ControlDomainState",
    "ControlDomainStore",
    "ControlDomainTransitionError",
    "ControlRecordIntegrityError",
    "MutationDecision",
    "MutationDecisionError",
    "MutationOperation",
    "ReconciliationOutcome",
    "TargetKind",
    "TargetObservation",
    "reconcile_mutation",
]
