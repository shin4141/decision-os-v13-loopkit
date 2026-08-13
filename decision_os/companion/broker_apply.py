"""Descriptor-bound acquisition and one-shot protected publication for F-01.

This module is a repository-only qualification surface.  It binds proposal and
protected-target observations to opened descriptors and makes CREATE/REPLACE
attempts fail closed, but it deliberately does not claim to exclude a process
with equivalent filesystem authority.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import os
from pathlib import Path
import secrets
import stat
from typing import Any, Iterator
from weakref import WeakKeyDictionary

from decision_os.acceleration.model import hash_payload

from decision_os.companion.broker_control import (
    ActivationTuple,
    BrokerControlError,
    ControlDomainStore,
    MutationDecision,
    MutationDecisionError,
    MutationOperation,
    ReconciliationOutcome,
    TargetKind,
    TargetObservation,
)
from decision_os.companion.broker_authority import (
    AuthenticatedExecutionEnvelope,
    EnvelopeAuthenticationError,
    PRODUCTION_AUTHENTICATION_TRUST_PRECONDITION,
)


MAX_PROPOSAL_BYTES = 16 * 1024 * 1024
CANONICAL_CONTROL_RELATIVE_PATH = Path("state") / "control.json"
PRODUCTION_CANONICAL_STORE_PRECONDITION = (
    "SLICE 3 TRUSTED ROUTING CONTRACT: the Broker control store for a protected "
    "root is the absolute sibling path protected_root.parent/state/control.json. "
    "The state directory must be a distinct filesystem directory outside the "
    "protected root. "
    "The deployed Broker must construct this store and its external trust key; "
    "request data may supply neither. Distinct protected repositories therefore "
    "require distinct parent deployment roots. OS protection of that routing "
    "and state directory remains a later deployment gate."
)
REPOSITORY_SLICE_ENFORCES_EXCLUSIVE_WRITER = False
PRODUCTION_EXCLUSIVE_WRITER_PRECONDITION = (
    "PRODUCTION PRECONDITION — NOT ENFORCED BY SLICE 2: deployed OS policy "
    "must make the Broker the sole non-root protected writer able to create, "
    "link, unlink, rename, or write protected entries and their ancestor "
    "directories. Repository-only Slice 2 does not close BA-10/TOCTOU against "
    "an arbitrary concurrent process with equivalent filesystem authority; "
    "the final REPLACE and identity-checked temporary unlink retain a "
    "check-to-syscall window until that sole-writer boundary is deployed."
)


class BrokerApplyError(BrokerControlError):
    """Descriptor acquisition or protected publication failed closed."""


def _snapshot_filesystem_path(value: Any, label: str) -> Path:
    """Seal one Path (including subclasses) into one concrete absolute value."""

    if not isinstance(value, Path):
        raise BrokerApplyError(f"{label} must be one pathlib.Path.")
    try:
        raw = os.fspath(value)
        if type(raw) not in {str, bytes}:
            raise TypeError("filesystem path is not plain text or bytes")
        decoded = os.fsdecode(raw)
        if any(component in {".", ".."} for component in decoded.split(os.sep)):
            raise ValueError("filesystem path is not lexically canonical")
        return Path(decoded).absolute()
    except (OSError, TypeError, ValueError) as exc:
        raise BrokerApplyError(f"{label} is invalid or unavailable.") from exc


def _require_separate_control_directory(
    protected_root: Path,
    control_path: Path,
) -> None:
    """Prove that positive-authority state is outside the protected repository."""

    control_directory = control_path.parent
    if (
        protected_root == control_directory
        or control_directory.is_relative_to(protected_root)
    ):
        raise BrokerApplyError(
            "Broker control state must be outside the protected root."
        )
    try:
        protected_status = protected_root.stat()
        control_status = control_directory.stat()
    except OSError as exc:
        raise BrokerApplyError(
            "Broker control-state separation cannot be proven."
        ) from exc
    if (
        not stat.S_ISDIR(protected_status.st_mode)
        or not stat.S_ISDIR(control_status.st_mode)
        or (protected_status.st_dev, protected_status.st_ino)
        == (control_status.st_dev, control_status.st_ino)
    ):
        raise BrokerApplyError(
            "Broker control state must be a distinct directory outside the "
            "protected root."
        )


@dataclass(frozen=True)
class FileIdentity:
    """The stable descriptor metadata used to bind an acquired file."""

    device: int
    inode: int
    mode: int
    link_count: int
    size: int
    mtime_ns: int
    ctime_ns: int

    @classmethod
    def from_stat(cls, value: os.stat_result) -> "FileIdentity":
        return cls(
            device=value.st_dev,
            inode=value.st_ino,
            mode=value.st_mode,
            link_count=value.st_nlink,
            size=value.st_size,
            mtime_ns=value.st_mtime_ns,
            ctime_ns=value.st_ctime_ns,
        )

    @property
    def inode_key(self) -> tuple[int, int]:
        return (self.device, self.inode)


@dataclass(frozen=True, init=False, eq=False)
class AcquiredMutation:
    """An opaque private proposal snapshot returned only by fd acquisition."""

    decision: MutationDecision
    proposal_bytes: bytes
    proposal_sha256: str
    proposal_identity: FileIdentity


@dataclass(frozen=True)
class _AcquisitionRecord:
    decision: MutationDecision
    proposal_bytes: bytes
    proposal_sha256: str
    proposal_identity: FileIdentity


_ACQUISITIONS: WeakKeyDictionary[AcquiredMutation, _AcquisitionRecord] = (
    WeakKeyDictionary()
)


@dataclass(frozen=True)
class _TargetSnapshot:
    observation: TargetObservation
    identity: FileIdentity | None


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _copy_decision(value: MutationDecision) -> MutationDecision:
    activation = ActivationTuple(
        authority_domain_id=value.activation.authority_domain_id,
        repository_id=value.activation.repository_id,
        protected_repository_identity=(
            value.activation.protected_repository_identity
        ),
        write_principal_identity=value.activation.write_principal_identity,
        generation_witness=value.activation.generation_witness,
    )
    return MutationDecision(
        activation=activation,
        operation=value.operation,
        relative_path=value.relative_path,
        target_bytes=value.target_bytes,
        expected_prior_sha256=value.expected_prior_sha256,
        expected_post_sha256=value.expected_post_sha256,
        proposal_acquisition_sha256=value.proposal_acquisition_sha256,
    )


def _proposal_acquisition_sha256(
    identity: FileIdentity,
    proposal_bytes: bytes,
) -> str:
    return hash_payload(
        {
            "schema": "decision-os-broker-proposal-acquisition-v0.1",
            "device": identity.device,
            "inode": identity.inode,
            "mode": identity.mode,
            "link_count": identity.link_count,
            "size": identity.size,
            "mtime_ns": identity.mtime_ns,
            "ctime_ns": identity.ctime_ns,
            "target_byte_count": len(proposal_bytes),
            "target_bytes_sha256": _sha256(proposal_bytes),
        }
    )


def _new_acquired(record: _AcquisitionRecord) -> AcquiredMutation:
    acquired = object.__new__(AcquiredMutation)
    object.__setattr__(acquired, "decision", _copy_decision(record.decision))
    object.__setattr__(acquired, "proposal_bytes", record.proposal_bytes)
    object.__setattr__(acquired, "proposal_sha256", record.proposal_sha256)
    object.__setattr__(acquired, "proposal_identity", record.proposal_identity)
    _ACQUISITIONS[acquired] = record
    return acquired


def _required_fd_features() -> int:
    missing = [
        name
        for name in ("O_NOFOLLOW", "O_DIRECTORY")
        if not hasattr(os, name)
    ]
    if missing:
        raise BrokerApplyError(
            "Required descriptor-safe filesystem features are unavailable: "
            + ", ".join(missing)
        )
    return getattr(os, "O_CLOEXEC", 0)


def _read_bounded(descriptor: int, maximum: int, label: str) -> bytes:
    chunks: list[bytes] = []
    remaining = maximum + 1
    try:
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
    except OSError as exc:
        raise BrokerApplyError(f"{label} bytes are unreadable.") from exc
    result = b"".join(chunks)
    if len(result) > maximum:
        raise BrokerApplyError(f"{label} exceeds the bounded size limit.")
    return result


def _stable_regular_identity(
    before: os.stat_result,
    after: os.stat_result,
    *,
    label: str,
) -> FileIdentity:
    first = FileIdentity.from_stat(before)
    second = FileIdentity.from_stat(after)
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or first != second
    ):
        raise BrokerApplyError(f"{label} identity is unsafe or changed.")
    return first


def acquire_mutation_decision(
    proposal_path: Path,
    *,
    activation: ActivationTuple,
    operation: MutationOperation,
    relative_path: str,
    expected_prior_sha256: str | None,
) -> AcquiredMutation:
    """Acquire proposal bytes once from a no-follow descriptor."""

    proposal_path = _snapshot_filesystem_path(proposal_path, "Proposal path")
    close_on_exec = _required_fd_features()
    flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_NONBLOCK", 0)
        | close_on_exec
    )
    try:
        descriptor = os.open(proposal_path, flags)
    except OSError as exc:
        raise BrokerApplyError(
            "Proposal cannot be opened without following links."
        ) from exc
    try:
        try:
            before = os.fstat(descriptor)
        except OSError as exc:
            raise BrokerApplyError(
                "Proposal descriptor identity is unavailable."
            ) from exc
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise BrokerApplyError("Proposal identity is not one private regular file.")
        proposal_bytes = _read_bounded(
            descriptor,
            MAX_PROPOSAL_BYTES,
            "Proposal",
        )
        try:
            after = os.fstat(descriptor)
        except OSError as exc:
            raise BrokerApplyError(
                "Proposal descriptor identity is unavailable."
            ) from exc
        identity = _stable_regular_identity(before, after, label="Proposal")
    finally:
        os.close(descriptor)

    proposal_sha256 = _sha256(proposal_bytes)
    acquisition_sha256 = _proposal_acquisition_sha256(
        identity,
        proposal_bytes,
    )
    try:
        decision = MutationDecision(
            activation=activation,
            operation=operation,
            relative_path=relative_path,
            target_bytes=proposal_bytes,
            expected_prior_sha256=expected_prior_sha256,
            expected_post_sha256=proposal_sha256,
            proposal_acquisition_sha256=acquisition_sha256,
        )
    except (MutationDecisionError, TypeError, ValueError) as exc:
        raise BrokerApplyError(
            "Proposal cannot form a valid mutation decision."
        ) from exc
    record = _AcquisitionRecord(
        decision=_copy_decision(decision),
        proposal_bytes=proposal_bytes,
        proposal_sha256=proposal_sha256,
        proposal_identity=identity,
    )
    return _new_acquired(record)


def _snapshot_acquired(value: Any) -> _AcquisitionRecord:
    if type(value) is not AcquiredMutation:
        raise BrokerApplyError("Live apply requires fd-acquired proposal bytes.")
    record = _ACQUISITIONS.get(value)
    if record is None:
        raise BrokerApplyError(
            "Live apply requires a registered fd-acquisition receipt."
        )
    try:
        current_binding = MutationDecision.binding_dict(value.decision)
        record_binding = MutationDecision.binding_dict(record.decision)
        exact = (
            type(value.decision) is MutationDecision
            and current_binding == record_binding
            and value.proposal_bytes == record.proposal_bytes
            and value.proposal_sha256 == record.proposal_sha256
            and value.proposal_identity == record.proposal_identity
            and value.decision.target_bytes == record.proposal_bytes
            and value.decision.proposal_acquisition_sha256
            == _proposal_acquisition_sha256(
                record.proposal_identity,
                record.proposal_bytes,
            )
        )
    except (AttributeError, MutationDecisionError, TypeError, ValueError) as exc:
        raise BrokerApplyError(
            "Fd-acquisition receipt was mutated after acquisition."
        ) from exc
    if not exact:
        raise BrokerApplyError(
            "Fd-acquisition receipt was forged or mutated after acquisition."
        )
    return _AcquisitionRecord(
        decision=_copy_decision(record.decision),
        proposal_bytes=record.proposal_bytes,
        proposal_sha256=record.proposal_sha256,
        proposal_identity=record.proposal_identity,
    )


def _open_protected_root(protected_root: Path) -> int:
    _required_fd_features()
    protected_root = _snapshot_filesystem_path(protected_root, "Protected root")
    flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor: int | None = None
    try:
        descriptor = os.open(protected_root, flags)
        metadata = os.fstat(descriptor)
    except OSError as exc:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise BrokerApplyError(
            "Protected root identity is unsafe or unavailable."
        ) from exc
    if not stat.S_ISDIR(metadata.st_mode):
        os.close(descriptor)
        raise BrokerApplyError("Protected root is not a directory.")
    return descriptor


def _protected_root_identity_from_fd(descriptor: int) -> str:
    try:
        metadata = os.fstat(descriptor)
    except OSError as exc:
        raise BrokerApplyError("Protected root identity is unavailable.") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise BrokerApplyError("Protected root is not a directory.")
    digest = hash_payload(
        {
            "schema": "decision-os-protected-root-identity-v0.1",
            "device": metadata.st_dev,
            "inode": metadata.st_ino,
        }
    )
    return f"protected:v1:{digest}"


def protected_root_identity(protected_root: Path) -> str:
    """Return the descriptor-derived identity required by Broker activation."""

    descriptor = _open_protected_root(protected_root)
    try:
        return _protected_root_identity_from_fd(descriptor)
    finally:
        os.close(descriptor)


def _require_bound_protected_root(
    root_fd: int,
    activation: ActivationTuple,
) -> None:
    if (
        _protected_root_identity_from_fd(root_fd)
        != activation.protected_repository_identity
    ):
        raise BrokerApplyError(
            "Opened protected root does not match Broker activation identity."
        )


def _duplicate_protected_root(root_fd: int) -> int:
    """Take descriptor ownership so caller-side close/dup2 cannot retarget it."""

    if type(root_fd) is not int or root_fd < 0:
        raise BrokerApplyError(
            "Protected root requires one exact open directory descriptor."
        )
    try:
        if hasattr(fcntl, "F_DUPFD_CLOEXEC"):
            owned = fcntl.fcntl(root_fd, fcntl.F_DUPFD_CLOEXEC, 0)
        else:
            owned = os.dup(root_fd)
            os.set_inheritable(owned, False)
        metadata = os.fstat(owned)
    except OSError as exc:
        try:
            os.close(owned)
        except (OSError, UnboundLocalError):
            pass
        raise BrokerApplyError(
            "Protected root descriptor cannot be owned safely."
        ) from exc
    if not stat.S_ISDIR(metadata.st_mode):
        os.close(owned)
        raise BrokerApplyError("Protected root descriptor is not a directory.")
    return owned


@contextmanager
def _open_parent_from_root(
    root_fd: int,
    relative_path: str,
) -> Iterator[tuple[int, str]]:
    """Walk the parent chain beneath one already-bound root descriptor."""

    parts = relative_path.split("/")
    flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptors: list[int] = []
    try:
        current = root_fd
        for component in parts[:-1]:
            try:
                current = os.open(component, flags, dir_fd=current)
            except OSError as exc:
                raise BrokerApplyError(
                    "Protected parent traversal is unsafe or unavailable."
                ) from exc
            descriptors.append(current)
            if not stat.S_ISDIR(os.fstat(current).st_mode):
                raise BrokerApplyError("Protected parent is not a directory.")
        yield current, parts[-1]
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


@contextmanager
def _open_parent(
    protected_root: Path,
    relative_path: str,
) -> Iterator[tuple[int, str]]:
    """Compatibility helper for one descriptor-bound parent walk."""

    root_fd = _open_protected_root(protected_root)
    try:
        with _open_parent_from_root(root_fd, relative_path) as opened:
            yield opened
    finally:
        os.close(root_fd)


def _kind_for_mode(mode: int, links: int) -> TargetKind:
    if stat.S_ISLNK(mode):
        return TargetKind.SYMLINK
    if stat.S_ISDIR(mode):
        return TargetKind.DIRECTORY
    if stat.S_ISREG(mode) and links != 1:
        return TargetKind.HARDLINK
    if stat.S_ISREG(mode):
        return TargetKind.REGULAR
    return TargetKind.OTHER


def _observe_target(parent_fd: int, name: str) -> _TargetSnapshot:
    """Observe the final entry from one no-follow descriptor and rebind check."""

    try:
        named_before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return _TargetSnapshot(TargetObservation(TargetKind.ABSENT), None)
    except OSError as exc:
        raise BrokerApplyError("Protected target observation failed.") from exc
    kind = _kind_for_mode(named_before.st_mode, named_before.st_nlink)
    if kind is not TargetKind.REGULAR:
        return _TargetSnapshot(TargetObservation(kind), None)
    flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise BrokerApplyError("Protected target cannot be opened safely.") from exc
    try:
        opened_before = os.fstat(descriptor)
        content = _read_bounded(descriptor, MAX_PROPOSAL_BYTES, "Protected target")
        opened_after = os.fstat(descriptor)
        identity = _stable_regular_identity(
            opened_before,
            opened_after,
            label="Protected target",
        )
        try:
            named_after = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError as exc:
            raise BrokerApplyError("Protected target identity changed.") from exc
        named_identity = FileIdentity.from_stat(named_after)
        if named_identity != identity:
            raise BrokerApplyError("Protected target identity changed.")
        if FileIdentity.from_stat(named_before) != identity:
            raise BrokerApplyError("Protected target identity changed.")
    finally:
        os.close(descriptor)
    return _TargetSnapshot(
        TargetObservation(TargetKind.REGULAR, content),
        identity,
    )


def _same_named_inode(parent_fd: int, name: str, identity: FileIdentity) -> bool:
    try:
        observed = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        return False
    return (observed.st_dev, observed.st_ino) == identity.inode_key


def _same_named_identity(
    parent_fd: int,
    name: str,
    identity: FileIdentity,
) -> bool:
    try:
        observed = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        return False
    return FileIdentity.from_stat(observed) == identity


def _fsync_parent(parent_fd: int) -> None:
    os.fsync(parent_fd)


def _cleanup_owned_temp(
    parent_fd: int,
    temporary_name: str,
    identity: FileIdentity | None,
) -> None:
    if identity is None or not _same_named_inode(parent_fd, temporary_name, identity):
        return
    try:
        os.unlink(temporary_name, dir_fd=parent_fd)
    except FileNotFoundError:
        return
    _fsync_parent(parent_fd)


def _write_temp(
    parent_fd: int,
    target_name: str,
    encoded: bytes,
) -> tuple[str, FileIdentity]:
    temporary_name = f".broker-apply-{target_name}-{secrets.token_hex(8)}.tmp"
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(temporary_name, flags, 0o600, dir_fd=parent_fd)
    except OSError as exc:
        raise BrokerApplyError(
            "Protected temporary file cannot be created safely."
        ) from exc
    identity: FileIdentity | None = None
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise BrokerApplyError("Protected temporary identity is unsafe.")
        identity = FileIdentity.from_stat(before)
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise BrokerApplyError("Protected temporary write made no progress.")
            view = view[written:]
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
        after = os.fstat(descriptor)
        if (
            not stat.S_ISREG(after.st_mode)
            or after.st_nlink != 1
            or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
            or stat.S_IFMT(before.st_mode) != stat.S_IFMT(after.st_mode)
        ):
            raise BrokerApplyError("Protected temporary identity changed.")
        identity = FileIdentity.from_stat(after)
        if after.st_size != len(encoded):
            raise BrokerApplyError("Protected temporary byte count mismatches.")
    except BaseException as primary:
        try:
            os.close(descriptor)
        finally:
            try:
                _cleanup_owned_temp(parent_fd, temporary_name, identity)
            except BaseException as cleanup:
                try:
                    primary.add_note(
                        "Protected temporary cleanup also failed: "
                        f"{cleanup!r}"
                    )
                except AttributeError:
                    pass
        raise
    os.close(descriptor)
    assert identity is not None
    return temporary_name, identity


def _publish_create(
    parent_fd: int,
    name: str,
    encoded: bytes,
) -> FileIdentity:
    temporary_name, identity = _write_temp(parent_fd, name, encoded)
    published = False
    try:
        os.link(
            temporary_name,
            name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
            follow_symlinks=False,
        )
        published = True
        _cleanup_owned_temp(parent_fd, temporary_name, identity)
        _fsync_parent(parent_fd)
        return identity
    except BaseException as primary:
        if not published:
            try:
                _cleanup_owned_temp(parent_fd, temporary_name, identity)
            except BaseException as cleanup:
                try:
                    primary.add_note(
                        "Protected temporary cleanup also failed: "
                        f"{cleanup!r}"
                    )
                except AttributeError:
                    pass
        raise


def _publish_replace(
    parent_fd: int,
    name: str,
    encoded: bytes,
    expected_identity: FileIdentity,
) -> FileIdentity:
    temporary_name, identity = _write_temp(parent_fd, name, encoded)
    published = False
    try:
        if not _same_named_identity(parent_fd, name, expected_identity):
            raise BrokerApplyError("Protected target identity changed before replace.")
        os.replace(
            temporary_name,
            name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        published = True
        _fsync_parent(parent_fd)
        return identity
    except BaseException as primary:
        if not published:
            try:
                _cleanup_owned_temp(parent_fd, temporary_name, identity)
            except BaseException as cleanup:
                try:
                    primary.add_note(
                        "Protected temporary cleanup also failed: "
                        f"{cleanup!r}"
                    )
                except AttributeError:
                    pass
        raise


def _readback_post(
    parent_fd: int,
    name: str,
    decision: MutationDecision,
    published_identity: FileIdentity,
) -> bool:
    snapshot = _observe_target(parent_fd, name)
    if snapshot.identity is None:
        return False
    if snapshot.identity.inode_key != published_identity.inode_key:
        return False
    if snapshot.observation.kind is not TargetKind.REGULAR:
        return False
    return (
        snapshot.observation.content == decision.target_bytes
        and _sha256(snapshot.observation.content or b"")
        == decision.expected_post_sha256
    )


def _observation_is_exact_post(
    decision: MutationDecision,
    observation: TargetObservation,
) -> bool:
    return (
        observation.kind is TargetKind.REGULAR
        and observation.content == decision.target_bytes
        and _sha256(observation.content or b"")
        == decision.expected_post_sha256
    )


def _attempt_live(
    parent_fd: int,
    name: str,
    decision: MutationDecision,
) -> ReconciliationOutcome:
    snapshot = _observe_target(parent_fd, name)
    if decision.operation is MutationOperation.CREATE:
        if snapshot.observation.kind is not TargetKind.ABSENT:
            return ReconciliationOutcome.UNCERTAIN
        try:
            identity = _publish_create(parent_fd, name, decision.target_bytes)
        except FileExistsError:
            return ReconciliationOutcome.UNCERTAIN
    else:
        if (
            snapshot.observation.kind is not TargetKind.REGULAR
            or snapshot.identity is None
            or snapshot.observation.content is None
            or _sha256(snapshot.observation.content)
            != decision.expected_prior_sha256
        ):
            return ReconciliationOutcome.UNCERTAIN
        identity = _publish_replace(
            parent_fd,
            name,
            decision.target_bytes,
            snapshot.identity,
        )
    exact = _readback_post(parent_fd, name, decision, identity)
    return (
        ReconciliationOutcome.APPLIED
        if exact
        else ReconciliationOutcome.UNCERTAIN
    )


def apply_protected_mutation(
    store: ControlDomainStore,
    protected_root: Path,
    proposal_path: Path,
    envelope: AuthenticatedExecutionEnvelope,
) -> ReconciliationOutcome:
    """Authenticate, fd-acquire, then perform one serialized live attempt."""

    if type(store) is not ControlDomainStore:
        raise BrokerApplyError("An exact Broker control store is required.")
    protected_root = _snapshot_filesystem_path(protected_root, "Protected root")
    proposal_path = _snapshot_filesystem_path(proposal_path, "Proposal path")
    expected_control_path = (
        protected_root.parent / CANONICAL_CONTROL_RELATIVE_PATH
    ).absolute()
    _require_separate_control_directory(protected_root, expected_control_path)
    try:
        store._require_coherent_routing()
    except BrokerControlError as exc:
        raise BrokerApplyError("Broker control-store routing is invalid.") from exc
    if store.path != expected_control_path:
        raise BrokerApplyError(
            "Broker control store is not the canonical store for this protected root."
        )
    try:
        verified_envelope = store._verify_execution_envelope(envelope)
    except EnvelopeAuthenticationError as exc:
        raise BrokerApplyError(
            "Live apply requires a valid external execution envelope."
        ) from exc
    try:
        with store._locked(exclusive=True):
            store._require_authentication_key_commitment_unlocked()
    except EnvelopeAuthenticationError as exc:
        raise BrokerApplyError(
            "Live apply requires the activation-bound external trust root."
        ) from exc
    return store._execute_authenticated_live_cas(
        verified_envelope,
        proposal_path,
        protected_root,
    )


def _recovery_observation_from_root_fd(
    root_fd: int,
    decision: MutationDecision,
) -> TargetObservation:
    # Root acquisition/identity is request routing, not target evidence.
    # Propagate any mismatch so it cannot consume the pending intent as an
    # UNCERTAIN observation.
    owned_root_fd = _duplicate_protected_root(root_fd)
    try:
        _require_bound_protected_root(owned_root_fd, decision.activation)
        with _open_parent_from_root(
            owned_root_fd,
            decision.relative_path,
        ) as (parent_fd, name):
            first = _observe_target(parent_fd, name)
            if not _observation_is_exact_post(
                decision,
                first.observation,
            ):
                return first.observation
            if first.identity is None:
                return TargetObservation(TargetKind.OTHER)

            # Exact bytes alone do not prove a publication survived the crash
            # window before its parent-directory fsync. Recovery may make that
            # already-observed entry durable, but never retries or rewrites it,
            # and must reopen it afterward.
            # A failed fsync is a transport/durability-proof failure, not
            # evidence that the target is neither pre nor post. Propagate it
            # so the pending intent remains retryable.
            _fsync_parent(parent_fd)
            second = _observe_target(parent_fd, name)
            if (
                second.identity != first.identity
                or not _observation_is_exact_post(
                    decision,
                    second.observation,
                )
            ):
                return TargetObservation(TargetKind.OTHER)
            return second.observation
    finally:
        os.close(owned_root_fd)


def _recovery_observation(
    protected_root: Path,
    decision: MutationDecision,
) -> TargetObservation:
    """Compatibility wrapper around fused descriptor-bound observation."""

    root_fd = _open_protected_root(protected_root)
    try:
        return _recovery_observation_from_root_fd(root_fd, decision)
    finally:
        os.close(root_fd)


def recover_pending_protected_mutation(
    store: ControlDomainStore,
    protected_root: Path,
) -> ReconciliationOutcome:
    """Reconstruct and observe the one pending durable mutation; never write."""

    if type(store) is not ControlDomainStore:
        raise BrokerApplyError("An exact Broker control store is required.")
    protected_root = _snapshot_filesystem_path(protected_root, "Protected root")
    expected_control_path = (
        protected_root.parent / CANONICAL_CONTROL_RELATIVE_PATH
    ).absolute()
    _require_separate_control_directory(protected_root, expected_control_path)
    try:
        store._require_coherent_routing()
    except BrokerControlError as exc:
        raise BrokerApplyError("Broker control-store routing is invalid.") from exc
    if store.path != expected_control_path:
        raise BrokerApplyError(
            "Broker control store is not the canonical store for this protected root."
        )
    return store._execute_pending_recovery_cas(protected_root)


__all__ = [
    "AcquiredMutation",
    "BrokerApplyError",
    "CANONICAL_CONTROL_RELATIVE_PATH",
    "FileIdentity",
    "MAX_PROPOSAL_BYTES",
    "PRODUCTION_AUTHENTICATION_TRUST_PRECONDITION",
    "PRODUCTION_CANONICAL_STORE_PRECONDITION",
    "PRODUCTION_EXCLUSIVE_WRITER_PRECONDITION",
    "REPOSITORY_SLICE_ENFORCES_EXCLUSIVE_WRITER",
    "acquire_mutation_decision",
    "apply_protected_mutation",
    "recover_pending_protected_mutation",
    "protected_root_identity",
]
