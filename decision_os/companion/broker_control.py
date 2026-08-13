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


CONTROL_DOMAIN_SCHEMA = "decision-os-broker-control-domain-v0.1"
CAS_FENCE_SCHEMA = "decision-os-broker-cas-fence-v0.1"
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

    def binding_dict(self) -> dict[str, Any]:
        """Return the exact bounded decision identity persisted by a CAS fence."""

        return {
            "activation": ActivationTuple.as_dict(self.activation),
            "operation": self.operation.value,
            "relative_path": self.relative_path,
            "target_byte_count": len(self.target_bytes),
            "target_bytes_sha256": _sha256_bytes(self.target_bytes),
            "expected_prior_sha256": self.expected_prior_sha256,
            "expected_post_sha256": self.expected_post_sha256,
        }


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
) -> _CASFenceRecord:
    payload: dict[str, Any] = {
        "schema": CAS_FENCE_SCHEMA,
        "kind": "INTENT",
        "fence_id": secrets.token_hex(16),
        "authority_domain_id": decision.activation.authority_domain_id,
        "activation_sha256": _activation_sha256(decision.activation),
        "control_record_sha256": current.record_sha256,
        "decision_sha256": hash_payload(MutationDecision.binding_dict(decision)),
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

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock_path = path.with_name(f".{path.name}.lock")
        self._journal_path = path.with_name(f".{path.name}.journal")
        self._fence_path = path.with_name(f".{path.name}.cas-fences")

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
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
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

    @classmethod
    def _read_control_record(cls, path: Path) -> ControlDomainRecord:
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
        raw = cls._read_private_bytes(
            path,
            _MAX_CAS_FENCE_BYTES,
            "Persisted Broker CAS fence",
        )
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
        self._durable_publish_unlocked(
            target,
            _canonical_record_bytes(record),
            replace_existing=False,
        )
        if self._read_control_record(target) != record:
            raise ControlRecordIntegrityError(
                "Persisted Broker journal readback mismatches the write."
            )

    def _append_cas_fence_unlocked(self, fence: _CASFenceRecord) -> None:
        target = self._fence_path / f"{fence.record_sha256}.json"
        self._durable_publish_unlocked(
            target,
            _canonical_fence_bytes(fence),
            replace_existing=False,
        )
        if self._read_cas_fence(target) != fence:
            raise ControlRecordIntegrityError(
                "Persisted Broker CAS-fence readback mismatches the write."
            )

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

    def reconcile_cas(
        self,
        decision: MutationDecision,
        observation: TargetObservation,
    ) -> ReconciliationOutcome:
        """Fence and classify caller-supplied bytes; never mutate repository data.

        Repeating the exact decision reconciles a durable pre-crash intent.  A
        different decision cannot consume or supersede that intent.  Every
        terminal result moves the domain irreversibly out of ``ACTIVE`` before
        it is returned: exact evidence abandons it, while unprovable evidence
        marks it ``UNCERTAIN``.
        """

        try:
            decision = _snapshot_decision(decision)
            observation = _snapshot_observation(observation)
        except MutationDecisionError:
            raise
        except (AttributeError, TypeError, ValueError) as exc:
            raise MutationDecisionError(
                "CAS reconciliation requires one bound decision and observation."
            ) from exc
        with self._locked(exclusive=True):
            current = self._load_required_unlocked(
                allow_consumed_cas=True,
                repair_incomplete_publication=True,
            )
            self._require_exact_activation(current, decision.activation)
            journal = self._journal_records_unlocked()
            decision_sha256 = hash_payload(
                MutationDecision.binding_dict(decision)
            )
            intent, completion = self._cas_exchange_unlocked(
                journal,
                decision.activation,
                decision_sha256,
            )
            if intent is None:
                if current.state is ControlDomainState.UNCERTAIN:
                    return ReconciliationOutcome.UNCERTAIN
                if current.state is not ControlDomainState.ACTIVE:
                    raise AuthorityRejectedError(
                        "A non-ACTIVE Broker domain has no reconcilable CAS intent."
                    )
                if len(self._cas_fences_unlocked(journal)) > _MAX_CAS_FENCES - 2:
                    raise ControlRecordIntegrityError(
                        "Broker CAS-fence capacity is exhausted."
                    )
                intent = _new_cas_intent(decision, current)
                current = self._publish_unlocked(
                    self._prospective_record(
                        current,
                        ControlDomainState.UNCERTAIN,
                    )
                )
                self._append_cas_fence_unlocked(intent)
            if completion is None:
                if current.state is ControlDomainState.UNCERTAIN:
                    outcome = reconcile_mutation(decision, observation)
                elif current.state is not ControlDomainState.ABANDONED:
                    raise ControlRecordIntegrityError(
                        "A pending Broker CAS intent has an invalid control state."
                    )
                else:
                    raise ControlRecordIntegrityError(
                        "An abandoned Broker domain has an incomplete CAS fence."
                    )
                completion = _complete_cas_intent(intent, outcome)
                self._append_cas_fence_unlocked(completion)
            else:
                assert completion.outcome is not None
                outcome = ReconciliationOutcome(completion.outcome)
            if (
                current.state is ControlDomainState.UNCERTAIN
                and outcome is not ReconciliationOutcome.UNCERTAIN
            ):
                self._publish_unlocked(
                    self._prospective_record(
                        current,
                        ControlDomainState.ABANDONED,
                    )
                )
            return outcome


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
