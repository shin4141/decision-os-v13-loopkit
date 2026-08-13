from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch
from typing import Any

import decision_os.companion.broker_control as broker_control
import decision_os.companion.broker_apply as broker_apply
from decision_os.acceleration.model import canonical_json, hash_payload
from decision_os.companion.broker_apply import (
    acquire_mutation_decision,
    apply_protected_mutation,
    protected_root_identity,
    recover_pending_protected_mutation,
)
from decision_os.companion.broker_authority import (
    EnvelopeAuthenticationKey,
    MutationCapsuleIntegrityError,
    issue_execution_envelope,
)
from decision_os.companion.broker_control import (
    ActivationTuple,
    AuthorityRejectedError,
    BrokerControlError,
    ControlDomainRecord,
    ControlDomainState,
    ControlDomainStore,
    ControlDomainTransitionError,
    ControlRecordIntegrityError,
    MutationDecision,
    MutationDecisionError,
    MutationOperation,
    ReconciliationOutcome,
    TargetKind,
    TargetObservation,
    reconcile_mutation,
)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class EqualitySpoofStr(str):
    def __eq__(self, _other: object) -> bool:
        return True

    def __ne__(self, _other: object) -> bool:
        return False

    __hash__ = str.__hash__


class EqualitySpoofInt(int):
    def __eq__(self, _other: object) -> bool:
        return True

    def __ne__(self, _other: object) -> bool:
        return False

    __hash__ = int.__hash__


class EqualitySpoofBytes(bytes):
    def __eq__(self, _other: object) -> bool:
        return True

    def __ne__(self, _other: object) -> bool:
        return False

    __hash__ = bytes.__hash__


class EqualitySpoofActivation(ActivationTuple):
    def __post_init__(self) -> None:
        pass

    def __eq__(self, _other: object) -> bool:
        return True

    def __ne__(self, _other: object) -> bool:
        return False


class EqualitySpoofRecord(ControlDomainRecord):
    def __eq__(self, _other: object) -> bool:
        return True

    def __ne__(self, _other: object) -> bool:
        return False


class EqualitySpoofDecision(MutationDecision):
    def __post_init__(self) -> None:
        pass

    def binding_dict(self) -> dict[str, Any]:
        return self.alias_binding


class EqualitySpoofObservation(TargetObservation):
    def __post_init__(self) -> None:
        pass


def forged_string_enum(
    enum_type: Any,
    underlying_value: str,
    advertised_value: str,
) -> Any:
    forged = str.__new__(enum_type, underlying_value)
    object.__setattr__(forged, "_name_", "FORGED")
    object.__setattr__(forged, "_value_", advertised_value)
    return forged


def activation(**overrides: Any) -> ActivationTuple:
    values: dict[str, Any] = {
        "authority_domain_id": "authority-domain-a",
        "repository_id": f"repo:v1:{'1' * 64}",
        "protected_repository_identity": f"protected:v1:{'2' * 64}",
        "write_principal_identity": f"principal:v1:{'3' * 64}",
        "generation_witness": 7,
    }
    values.update(overrides)
    return ActivationTuple(**values)


def replace_decision(
    domain: ActivationTuple,
    *,
    prior: bytes = b"exact prior\n",
    post: bytes = b"exact post\n",
    **overrides: Any,
) -> MutationDecision:
    values: dict[str, Any] = {
        "activation": domain,
        "operation": MutationOperation.REPLACE,
        "relative_path": "bounded/target.txt",
        "target_bytes": post,
        "expected_prior_sha256": sha256(prior),
        "expected_post_sha256": sha256(post),
    }
    values.update(overrides)
    return MutationDecision(**values)


def create_decision(
    domain: ActivationTuple,
    *,
    post: bytes = b"created bytes\n",
    **overrides: Any,
) -> MutationDecision:
    values: dict[str, Any] = {
        "activation": domain,
        "operation": MutationOperation.CREATE,
        "relative_path": "bounded/new.txt",
        "target_bytes": post,
        "expected_prior_sha256": None,
        "expected_post_sha256": sha256(post),
    }
    values.update(overrides)
    return MutationDecision(**values)


class CanonicalCASScenario:
    """One real authenticated apply/recovery route for control-plane tests."""

    def __init__(
        self,
        root: Path,
        *,
        prior: bytes = b"exact prior\n",
        post: bytes = b"exact post\n",
        operation: MutationOperation = MutationOperation.REPLACE,
        relative_path: str | None = None,
        activation_overrides: dict[str, Any] | None = None,
    ) -> None:
        self.root = root
        self.protected_root = root / "protected"
        self.proposals = root / "proposals"
        self.protected_root.mkdir()
        self.proposals.mkdir()
        current_values = dict(activation_overrides or {})
        current_values["protected_repository_identity"] = protected_root_identity(
            self.protected_root
        )
        self.current = activation(**current_values)
        self.authentication_key = EnvelopeAuthenticationKey(
            key_id="control-regression-key",
            key_version=1,
            secret=b"control regression external trust" * 2,
        )
        self.path = root / "state" / "control.json"
        self.store = ControlDomainStore(
            self.path,
            authentication_key=self.authentication_key,
        )
        self.initial = self.store.activate_initial(self.current)
        self.operation = operation
        self.relative_path = relative_path or (
            "bounded/new.txt"
            if operation is MutationOperation.CREATE
            else "bounded/target.txt"
        )
        self.target = self.protected_root / self.relative_path
        self.target.parent.mkdir(parents=True)
        if operation is MutationOperation.REPLACE:
            self.target.write_bytes(prior)
        proposal = self.proposals / "proposal.bin"
        proposal.write_bytes(post)
        acquired = acquire_mutation_decision(
            proposal,
            activation=self.current,
            operation=operation,
            relative_path=self.relative_path,
            expected_prior_sha256=(
                None if operation is MutationOperation.CREATE else sha256(prior)
            ),
        )
        self.proposal = proposal
        self.decision = acquired.decision
        now = int(time.time())
        self.envelope = issue_execution_envelope(
            self.decision,
            self.initial,
            authentication_key=self.authentication_key,
            envelope_id="1" * 32,
            nonce="2" * 32,
            issued_at_unix=now,
            expires_at_unix=now + 300,
            bootstrap_activation_evidence_id="control-bootstrap",
            bootstrap_activation_evidence_sha256="a" * 64,
            human_seat_authorization_evidence_id="control-human-seat",
            human_seat_authorization_evidence_sha256="b" * 64,
        )

    def apply(
        self,
        *,
        store: ControlDomainStore | None = None,
    ) -> ReconciliationOutcome:
        return apply_protected_mutation(
            self.store if store is None else store,
            self.protected_root,
            self.proposal,
            self.envelope,
        )

    def apply_as(
        self,
        requested_activation: ActivationTuple,
        *,
        store: ControlDomainStore | None = None,
    ) -> ReconciliationOutcome:
        """Submit a validly authenticated request for a non-current tuple."""

        acquired = acquire_mutation_decision(
            self.proposal,
            activation=requested_activation,
            operation=self.operation,
            relative_path=self.relative_path,
            expected_prior_sha256=self.decision.expected_prior_sha256,
        )
        synthetic_active = broker_control._new_record(
            requested_activation,
            state=ControlDomainState.ACTIVE,
            journal_position=0,
            predecessor_record_sha256=None,
            retired_authority_domain_ids=(),
        )
        now = int(time.time())
        envelope = issue_execution_envelope(
            acquired.decision,
            synthetic_active,
            authentication_key=self.authentication_key,
            envelope_id="3" * 32,
            nonce="4" * 32,
            issued_at_unix=now,
            expires_at_unix=now + 300,
            bootstrap_activation_evidence_id="control-bootstrap",
            bootstrap_activation_evidence_sha256="a" * 64,
            human_seat_authorization_evidence_id="control-human-seat",
            human_seat_authorization_evidence_sha256="b" * 64,
        )
        return apply_protected_mutation(
            self.store if store is None else store,
            self.protected_root,
            self.proposal,
            envelope,
        )

    def leave_pending(self) -> None:
        with patch.object(
            broker_apply,
            "_attempt_live",
            side_effect=RuntimeError("simulated live CAS crash"),
        ):
            try:
                self.apply()
            except RuntimeError as exc:
                if str(exc) != "simulated live CAS crash":
                    raise
            else:
                raise AssertionError("raising live CAS seam unexpectedly returned")

    def recover(
        self,
        *,
        store: ControlDomainStore | None = None,
    ) -> ReconciliationOutcome:
        return recover_pending_protected_mutation(
            self.store if store is None else store,
            self.protected_root,
        )

    def restarted_store(self, *, authenticated: bool = False) -> ControlDomainStore:
        return ControlDomainStore(
            self.path,
            authentication_key=(self.authentication_key if authenticated else None),
        )

    def set_target(self, content: bytes | None) -> None:
        if os.path.lexists(self.target):
            self.target.unlink()
        if content is not None:
            self.target.write_bytes(content)


class BrokerControlDurabilityTest(unittest.TestCase):
    def test_normal_durable_save_reloads_exact_canonical_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "broker-control.json"
            store = ControlDomainStore(path)

            saved = store.activate_initial(activation())

            self.assertEqual(saved, store.load_required())
            self.assertEqual(ControlDomainState.ACTIVE, saved.state)
            self.assertEqual(0, saved.journal_position)
            self.assertIsNone(saved.predecessor_record_sha256)
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            self.assertEqual(0o700, path.parent.stat().st_mode & 0o777)
            self.assertEqual(
                f"{canonical_json(saved.as_dict())}\n".encode("utf-8"),
                path.read_bytes(),
            )

    def test_control_record_fsync_order_brackets_atomic_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "broker-control.json"
            operations: list[str] = []
            file_sizes_at_fsync: list[int] = []
            original_fsync = os.fsync
            original_replace = os.replace
            original_link = os.link

            def observed_fsync(descriptor: int) -> None:
                mode = os.fstat(descriptor).st_mode
                original_fsync(descriptor)
                if stat.S_ISREG(mode):
                    file_sizes_at_fsync.append(os.fstat(descriptor).st_size)
                operations.append(
                    "directory-fsync" if stat.S_ISDIR(mode) else "file-fsync"
                )

            def observed_replace(source: Any, target: Any, **kwargs: Any) -> None:
                original_replace(source, target, **kwargs)
                operations.append("replace")

            def observed_link(source: Any, target: Any, **kwargs: Any) -> None:
                original_link(source, target, **kwargs)
                operations.append("link")

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=observed_fsync,
                ),
                patch(
                    "decision_os.companion.broker_control.os.replace",
                    side_effect=observed_replace,
                ),
                patch(
                    "decision_os.companion.broker_control.os.link",
                    side_effect=observed_link,
                ),
            ):
                ControlDomainStore(path).activate_initial(activation())

            replace_indexes = [
                index
                for index, operation in enumerate(operations)
                if operation == "replace"
            ]
            self.assertEqual(1, len(replace_indexes))
            for index in replace_indexes:
                self.assertEqual("file-fsync", operations[index - 1])
                self.assertEqual("directory-fsync", operations[index + 1])
            link_indexes = [
                index
                for index, operation in enumerate(operations)
                if operation == "link"
            ]
            self.assertEqual(1, len(link_indexes))
            for index in link_indexes:
                self.assertEqual("file-fsync", operations[index - 1])
                self.assertEqual("directory-fsync", operations[index + 1])
            self.assertEqual(2, len(file_sizes_at_fsync))
            self.assertTrue(all(size == len(path.read_bytes()) for size in file_sizes_at_fsync))

    def test_cas_fence_and_terminal_record_each_use_durable_publish(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            path = scenario.path
            store = scenario.store
            operations: list[str] = []
            original_fsync = os.fsync
            original_replace = os.replace
            original_link = os.link

            def observed_fsync(descriptor: int) -> None:
                mode = os.fstat(descriptor).st_mode
                original_fsync(descriptor)
                operations.append(
                    "directory-fsync" if stat.S_ISDIR(mode) else "file-fsync"
                )

            def observed_replace(source: Any, target: Any, **kwargs: Any) -> None:
                original_replace(source, target, **kwargs)
                operations.append(
                    "protected-replace"
                    if os.fspath(target) == scenario.target.name
                    and kwargs.get("dst_dir_fd") is not None
                    else "replace"
                )

            def observed_link(source: Any, target: Any, **kwargs: Any) -> None:
                original_link(source, target, **kwargs)
                operations.append("link")

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=observed_fsync,
                ),
                patch(
                    "decision_os.companion.broker_control.os.replace",
                    side_effect=observed_replace,
                ),
                patch(
                    "decision_os.companion.broker_control.os.link",
                    side_effect=observed_link,
                ),
            ):
                outcome = scenario.apply()

            self.assertEqual(ReconciliationOutcome.APPLIED, outcome)
            replace_indexes = [
                index
                for index, operation in enumerate(operations)
                if operation == "replace"
            ]
            self.assertEqual(2, len(replace_indexes))
            for index in replace_indexes:
                self.assertEqual("file-fsync", operations[index - 1])
                self.assertEqual("directory-fsync", operations[index + 1])
            link_indexes = [
                index
                for index, operation in enumerate(operations)
                if operation == "link"
            ]
            # Blob + capsule + INTENT + UNCERTAIN journal + COMPLETE +
            # ABANDONED journal are each immutable no-clobber publications.
            self.assertEqual(6, len(link_indexes))
            for index in link_indexes:
                self.assertEqual("file-fsync", operations[index - 1])
                self.assertEqual("directory-fsync", operations[index + 1])
            security_files = (
                [path]
                + list(store._journal_path.glob("*.json"))
                + list(store._fence_path.glob("*.json"))
            )
            self.assertTrue(security_files)
            self.assertTrue(
                all(item.stat().st_mode & 0o777 == 0o600 for item in security_files)
            )

    def test_immutable_publish_is_full_fsync_no_clobber_and_exact_readback(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "immutable" / "record.bin"
            store = ControlDomainStore(Path(temporary) / "state" / "control.json")
            encoded = b"immutable exact bytes\x00\n"
            operations: list[str] = []
            original_fsync = os.fsync
            original_link = os.link

            def observed_fsync(descriptor: int) -> None:
                mode = os.fstat(descriptor).st_mode
                original_fsync(descriptor)
                operations.append(
                    "directory-fsync" if stat.S_ISDIR(mode) else "file-fsync"
                )

            def observed_link(source: Any, destination: Any, **kwargs: Any) -> None:
                original_link(source, destination, **kwargs)
                operations.append("link")

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=observed_fsync,
                ),
                patch(
                    "decision_os.companion.broker_control.os.link",
                    side_effect=observed_link,
                ),
            ):
                store._durable_publish_immutable_unlocked(
                    target,
                    encoded,
                    label="test immutable record",
                )
            self.assertEqual(encoded, target.read_bytes())
            link_index = operations.index("link")
            self.assertEqual("file-fsync", operations[link_index - 1])
            self.assertEqual("directory-fsync", operations[link_index + 1])
            self.assertEqual([], list(target.parent.glob(".broker-control-*.tmp")))

            with self.assertRaises(FileExistsError):
                store._durable_publish_immutable_unlocked(
                    target,
                    b"must not clobber",
                    label="test immutable collision",
                )
            self.assertEqual(encoded, target.read_bytes())

    def test_immutable_link_before_unlink_crash_prefix_is_recovered_exactly(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "immutable"
            directory.mkdir()
            target = directory / "record.bin"
            encoded = b"crash-prefix exact bytes\n"
            temporary_path = directory / (
                f".broker-control-{sha256(encoded)}-a1b2c3d4e5f60718.tmp"
            )
            temporary_path.write_bytes(encoded)
            os.link(temporary_path, target)
            self.assertEqual(2, target.stat().st_nlink)

            recovered = ControlDomainStore._recover_immutable_publication_unlocked(
                target,
                maximum=len(encoded),
                label="test immutable crash prefix",
                expected=encoded,
            )

            self.assertEqual(encoded, recovered)
            self.assertFalse(temporary_path.exists())
            self.assertEqual(1, target.stat().st_nlink)

    def test_immutable_link_repair_rejects_a_rebound_temporary_before_unlink(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "immutable"
            directory.mkdir()
            target = directory / "record.bin"
            encoded = b"crash-prefix exact bytes\n"
            temporary_path = directory / (
                f".broker-control-{sha256(encoded)}-a1b2c3d4e5f60718.tmp"
            )
            foreign = directory / "foreign.bin"
            sentinel = b"foreign temporary replacement\n"
            temporary_path.write_bytes(encoded)
            foreign.write_bytes(sentinel)
            os.link(temporary_path, target)
            original_stat = os.stat
            rebound = False

            def rebind_before_final_stat(
                path: Any,
                *args: Any,
                **kwargs: Any,
            ) -> os.stat_result:
                nonlocal rebound
                directory_descriptor = kwargs.get("dir_fd")
                if (
                    not rebound
                    and path == temporary_path.name
                    and directory_descriptor is not None
                ):
                    rebound = True
                    os.unlink(temporary_path.name, dir_fd=directory_descriptor)
                    os.rename(
                        foreign.name,
                        temporary_path.name,
                        src_dir_fd=directory_descriptor,
                        dst_dir_fd=directory_descriptor,
                    )
                return original_stat(path, *args, **kwargs)

            with (
                patch(
                    "decision_os.companion.broker_control.os.stat",
                    side_effect=rebind_before_final_stat,
                ),
                self.assertRaises(MutationCapsuleIntegrityError),
            ):
                ControlDomainStore._recover_immutable_publication_unlocked(
                    target,
                    maximum=len(encoded),
                    label="test rebound immutable crash prefix",
                    expected=encoded,
                )

            self.assertTrue(rebound)
            self.assertEqual(encoded, target.read_bytes())
            self.assertEqual(sentinel, temporary_path.read_bytes())

    def test_immutable_link_repair_retry_reestablishes_directory_durability(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "immutable"
            directory.mkdir()
            target = directory / "record.bin"
            encoded = b"repair durability exact bytes\n"
            temporary_path = directory / (
                f".broker-control-{sha256(encoded)}-a1b2c3d4e5f60718.tmp"
            )
            temporary_path.write_bytes(encoded)
            os.link(temporary_path, target)
            original_fsync = os.fsync

            def fail_repair_directory_fsync(descriptor: int) -> None:
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    raise OSError("injected repair directory fsync failure")
                original_fsync(descriptor)

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_repair_directory_fsync,
                ),
                self.assertRaisesRegex(
                    MutationCapsuleIntegrityError,
                    "cannot be recovered",
                ),
            ):
                ControlDomainStore._recover_immutable_publication_unlocked(
                    target,
                    maximum=len(encoded),
                    label="test immutable repair durability",
                    expected=encoded,
                )

            self.assertFalse(temporary_path.exists())
            self.assertEqual(1, target.stat().st_nlink)
            retry_directory_fsyncs = 0

            def observe_retry_fsync(descriptor: int) -> None:
                nonlocal retry_directory_fsyncs
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    retry_directory_fsyncs += 1
                original_fsync(descriptor)

            with patch(
                "decision_os.companion.broker_control.os.fsync",
                side_effect=observe_retry_fsync,
            ):
                recovered = (
                    ControlDomainStore._recover_immutable_publication_unlocked(
                        target,
                        maximum=len(encoded),
                        label="test immutable repair durability",
                        expected=encoded,
                    )
                )

            self.assertEqual(encoded, recovered)
            self.assertGreaterEqual(retry_directory_fsyncs, 1)

    def test_immutable_reuse_reads_back_after_directory_durability_refresh(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "immutable"
            directory.mkdir()
            target = directory / "record.bin"
            replacement = directory / "replacement.bin"
            expected = b"expected immutable bytes\n"
            substituted = b"substituted immutable bytes\n"
            target.write_bytes(expected)
            replacement.write_bytes(substituted)
            original_refresh = ControlDomainStore._fsync_directory
            rebound = False

            def rebind_during_refresh(parent: Path) -> None:
                nonlocal rebound
                original_refresh(parent)
                if not rebound:
                    rebound = True
                    os.replace(replacement, target)

            with (
                patch.object(
                    ControlDomainStore,
                    "_fsync_directory",
                    side_effect=rebind_during_refresh,
                ),
                self.assertRaisesRegex(
                    MutationCapsuleIntegrityError,
                    "expected content",
                ),
            ):
                ControlDomainStore._recover_immutable_publication_unlocked(
                    target,
                    maximum=len(substituted),
                    label="test immutable reuse",
                    expected=expected,
                )

            self.assertTrue(rebound)
            self.assertEqual(substituted, target.read_bytes())

    def test_existing_directory_is_refsynced_after_mkdir_fsync_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "state"
            path = state / "control.json"
            store = ControlDomainStore(path)
            original_fsync = os.fsync
            root_identity = root.stat()
            failed = False

            def fail_state_name_fsync(descriptor: int) -> None:
                nonlocal failed
                observed = os.fstat(descriptor)
                if (
                    not failed
                    and state.exists()
                    and stat.S_ISDIR(observed.st_mode)
                    and (observed.st_dev, observed.st_ino)
                    == (root_identity.st_dev, root_identity.st_ino)
                ):
                    failed = True
                    raise OSError("injected state-name directory fsync failure")
                original_fsync(descriptor)

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_state_name_fsync,
                ),
                self.assertRaisesRegex(
                    OSError,
                    "state-name directory fsync",
                ),
            ):
                store.activate_initial(activation())

            self.assertTrue(failed)
            self.assertTrue(state.is_dir())
            self.assertFalse(path.exists())

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=OSError("injected retry directory fsync failure"),
                ),
                self.assertRaisesRegex(
                    ControlRecordIntegrityError,
                    "directory durability",
                ),
            ):
                store.activate_initial(activation())
            self.assertFalse(path.exists())

            root_refreshes = 0

            def observe_retry_fsync(descriptor: int) -> None:
                nonlocal root_refreshes
                observed = os.fstat(descriptor)
                if (
                    stat.S_ISDIR(observed.st_mode)
                    and (observed.st_dev, observed.st_ino)
                    == (root_identity.st_dev, root_identity.st_ino)
                ):
                    root_refreshes += 1
                original_fsync(descriptor)

            with patch(
                "decision_os.companion.broker_control.os.fsync",
                side_effect=observe_retry_fsync,
            ):
                activated = store.activate_initial(activation())

            self.assertGreaterEqual(root_refreshes, 1)
            self.assertEqual(ControlDomainState.ACTIVE, activated.state)
            self.assertEqual(activated, store.load_required())

    def test_authenticator_orphan_is_exactly_retryable_before_active_head(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "control.json"
            key = broker_control.EnvelopeAuthenticationKey(
                key_id="activation-retry-key",
                key_version=1,
                secret=b"activation retry external secret" * 2,
            )
            store = ControlDomainStore(path, authentication_key=key)
            original_publish = store._publish_unlocked

            with (
                patch.object(
                    store,
                    "_publish_unlocked",
                    side_effect=RuntimeError("crash after authenticator"),
                ),
                self.assertRaisesRegex(RuntimeError, "after authenticator"),
            ):
                store.activate_initial(activation())
            self.assertFalse(path.exists())
            self.assertTrue(store._authenticator_path.exists())

            with patch.object(
                store,
                "_publish_unlocked",
                side_effect=original_publish,
            ):
                activated = store.activate_initial(activation())
            self.assertEqual(ControlDomainState.ACTIVE, activated.state)
            self.assertEqual(activated, store.load_required())

    def test_immutable_stable_read_rejects_same_inode_mutation_at_final_check(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "record.bin"
            target.write_bytes(b"good!")
            original_lstat = Path.lstat
            mutated = False

            def mutate_then_lstat(path: Path) -> os.stat_result:
                nonlocal mutated
                if path == target and not mutated:
                    mutated = True
                    path.write_bytes(b"evil!")
                return original_lstat(path)

            with (
                patch.object(Path, "lstat", autospec=True, side_effect=mutate_then_lstat),
                self.assertRaises(MutationCapsuleIntegrityError),
            ):
                ControlDomainStore._read_immutable_bytes(
                    target,
                    5,
                    "test immutable record",
                )

    def test_control_file_fsync_failure_preserves_exact_prior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "broker-control.json"
            store = ControlDomainStore(path)
            initial = store.activate_initial(activation())
            prior_bytes = path.read_bytes()
            original_fsync = os.fsync
            regular_fsyncs = 0

            def fail_head_file_fsync(descriptor: int) -> None:
                nonlocal regular_fsyncs
                if stat.S_ISREG(os.fstat(descriptor).st_mode):
                    regular_fsyncs += 1
                    if regular_fsyncs == 1:
                        raise OSError("injected file fsync failure")
                original_fsync(descriptor)

            with patch(
                "decision_os.companion.broker_control.os.fsync",
                side_effect=fail_head_file_fsync,
            ):
                with self.assertRaisesRegex(OSError, "injected file fsync"):
                    store.transition(
                        initial.activation,
                        ControlDomainState.ABANDONED,
                    )

            self.assertEqual(prior_bytes, path.read_bytes())
            self.assertEqual(initial, store.load_required())
            self.assertEqual(
                [],
                list(path.parent.rglob(".broker-control-*.tmp")),
            )

    def test_temp_name_collision_never_unlinks_foreign_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "control.json"
            foreign = root / ".broker-control-collision.tmp"
            sentinel = b"foreign collision sentinel"
            foreign.write_bytes(sentinel)
            foreign_identity = (foreign.stat().st_dev, foreign.stat().st_ino)
            store = ControlDomainStore(target)

            with (
                patch(
                    "decision_os.companion.broker_control.secrets.token_hex",
                    return_value="collision",
                ),
                self.assertRaises(FileExistsError),
            ):
                store._durable_publish_unlocked(
                    target,
                    b"owned bytes",
                    replace_existing=False,
                )

            self.assertEqual(sentinel, foreign.read_bytes())
            self.assertEqual(
                foreign_identity,
                (foreign.stat().st_dev, foreign.stat().st_ino),
            )
            self.assertFalse(target.exists())

    def test_temp_without_captured_inode_is_preserved_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "control.json"
            unverified = root / ".broker-control-unverified.tmp"
            store = ControlDomainStore(target)

            with (
                patch(
                    "decision_os.companion.broker_control.secrets.token_hex",
                    return_value="unverified",
                ),
                patch(
                    "decision_os.companion.broker_control.os.fstat",
                    side_effect=OSError("injected fstat failure"),
                ),
                self.assertRaisesRegex(OSError, "injected fstat failure"),
            ):
                store._durable_publish_unlocked(
                    target,
                    b"owned bytes",
                    replace_existing=False,
                )

            self.assertTrue(unverified.exists())
            self.assertEqual(b"", unverified.read_bytes())
            self.assertFalse(target.exists())

    def test_proven_owned_temp_cleanup_is_directory_fsynced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "control.json"
            temporary_path = root / ".broker-control-cleanup.tmp"
            store = ControlDomainStore(target)
            original_fsync = os.fsync
            cleanup_directory_fsyncs = 0
            primary_failed = False

            def fail_file_then_observe_cleanup(descriptor: int) -> None:
                nonlocal cleanup_directory_fsyncs, primary_failed
                if stat.S_ISREG(os.fstat(descriptor).st_mode):
                    primary_failed = True
                    raise OSError("injected owned-temp failure")
                if primary_failed:
                    cleanup_directory_fsyncs += 1
                original_fsync(descriptor)

            with (
                patch(
                    "decision_os.companion.broker_control.secrets.token_hex",
                    return_value="cleanup",
                ),
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_file_then_observe_cleanup,
                ),
                self.assertRaisesRegex(OSError, "owned-temp failure"),
            ):
                store._durable_publish_unlocked(
                    target,
                    b"owned bytes",
                    replace_existing=False,
                )

            self.assertFalse(temporary_path.exists())
            self.assertEqual(1, cleanup_directory_fsyncs)
            self.assertFalse(target.exists())

    def test_cleanup_fsync_failure_preserves_the_primary_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "control.json"
            temporary_path = root / ".broker-control-cleanup-note.tmp"
            store = ControlDomainStore(target)
            original_fsync = os.fsync
            primary_failed = False

            def fail_primary_and_cleanup_fsync(descriptor: int) -> None:
                nonlocal primary_failed
                if stat.S_ISREG(os.fstat(descriptor).st_mode):
                    primary_failed = True
                    raise OSError("primary durability failure")
                if primary_failed:
                    raise FileNotFoundError("cleanup directory fsync failure")
                original_fsync(descriptor)

            with (
                patch(
                    "decision_os.companion.broker_control.secrets.token_hex",
                    return_value="cleanup-note",
                ),
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_primary_and_cleanup_fsync,
                ),
                self.assertRaisesRegex(
                    OSError,
                    "primary durability failure",
                ) as caught,
            ):
                store._durable_publish_unlocked(
                    target,
                    b"owned bytes",
                    replace_existing=False,
                )

            self.assertFalse(temporary_path.exists())
            self.assertTrue(
                any(
                    "cleanup directory fsync failure" in note
                    for note in getattr(caught.exception, "__notes__", ())
                )
            )
            self.assertFalse(target.exists())

    def test_temp_cleanup_preserves_rebound_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "control.json"
            temporary_path = root / ".broker-control-rebound.tmp"
            sentinel = b"foreign rebound sentinel"
            store = ControlDomainStore(target)
            original_fsync = os.fsync
            owned_identity: tuple[int, int] | None = None

            def rebind_then_fail(descriptor: int) -> None:
                nonlocal owned_identity
                metadata = os.fstat(descriptor)
                if stat.S_ISREG(metadata.st_mode):
                    owned_identity = (metadata.st_dev, metadata.st_ino)
                    temporary_path.unlink()
                    temporary_path.write_bytes(sentinel)
                    raise OSError("injected rebound file failure")
                original_fsync(descriptor)

            with (
                patch(
                    "decision_os.companion.broker_control.secrets.token_hex",
                    return_value="rebound",
                ),
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=rebind_then_fail,
                ),
                self.assertRaisesRegex(OSError, "rebound file failure"),
            ):
                store._durable_publish_unlocked(
                    target,
                    b"owned bytes",
                    replace_existing=False,
                )

            self.assertIsNotNone(owned_identity)
            self.assertNotEqual(
                owned_identity,
                (temporary_path.stat().st_dev, temporary_path.stat().st_ino),
            )
            self.assertEqual(sentinel, temporary_path.read_bytes())
            self.assertFalse(target.exists())

    def test_temp_cleanup_preserves_rebound_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "control.json"
            temporary_path = root / ".broker-control-rebound-link.tmp"
            sentinel_path = root / "foreign-sentinel"
            sentinel_path.write_bytes(b"foreign symlink sentinel")
            store = ControlDomainStore(target)
            original_fsync = os.fsync

            def rebind_then_fail(descriptor: int) -> None:
                if stat.S_ISREG(os.fstat(descriptor).st_mode):
                    temporary_path.unlink()
                    temporary_path.symlink_to(sentinel_path)
                    raise OSError("injected rebound symlink failure")
                original_fsync(descriptor)

            with (
                patch(
                    "decision_os.companion.broker_control.secrets.token_hex",
                    return_value="rebound-link",
                ),
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=rebind_then_fail,
                ),
                self.assertRaisesRegex(OSError, "rebound symlink failure"),
            ):
                store._durable_publish_unlocked(
                    target,
                    b"owned bytes",
                    replace_existing=False,
                )

            self.assertTrue(temporary_path.is_symlink())
            self.assertEqual(b"foreign symlink sentinel", sentinel_path.read_bytes())
            self.assertFalse(target.exists())

    def test_temp_cleanup_stays_bound_to_the_open_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent = root / "state"
            parent.mkdir()
            moved_parent = root / "owned-state"
            target = parent / "control.json"
            temporary_name = ".broker-control-parent-race.tmp"
            foreign = parent / temporary_name
            sentinel = b"foreign parent replacement sentinel"
            store = ControlDomainStore(target)
            original_fsync = os.fsync
            substituted = False

            def substitute_parent_then_fail(descriptor: int) -> None:
                nonlocal substituted
                if stat.S_ISREG(os.fstat(descriptor).st_mode) and not substituted:
                    substituted = True
                    parent.rename(moved_parent)
                    parent.mkdir()
                    foreign.write_bytes(sentinel)
                    raise OSError("injected parent substitution failure")
                original_fsync(descriptor)

            with (
                patch(
                    "decision_os.companion.broker_control.secrets.token_hex",
                    return_value="parent-race",
                ),
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=substitute_parent_then_fail,
                ),
                self.assertRaisesRegex(OSError, "parent substitution failure"),
            ):
                store._durable_publish_unlocked(
                    target,
                    b"owned bytes",
                    replace_existing=False,
                )

            self.assertTrue(substituted)
            self.assertEqual(sentinel, foreign.read_bytes())
            self.assertFalse((moved_parent / temporary_name).exists())
            self.assertFalse(target.exists())

    def test_post_replace_temp_reuse_survives_directory_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "control.json"
            temporary_path = root / ".broker-control-published.tmp"
            encoded = b"durably published bytes"
            sentinel = b"post-publication foreign sentinel"
            store = ControlDomainStore(target)
            original_fsync = os.fsync

            def reuse_then_fail(descriptor: int) -> None:
                if (
                    target.exists()
                    and stat.S_ISDIR(os.fstat(descriptor).st_mode)
                ):
                    temporary_path.write_bytes(sentinel)
                    raise OSError("injected published directory failure")
                original_fsync(descriptor)

            with (
                patch(
                    "decision_os.companion.broker_control.secrets.token_hex",
                    return_value="published",
                ),
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=reuse_then_fail,
                ),
                self.assertRaisesRegex(OSError, "published directory failure"),
            ):
                store._durable_publish_unlocked(
                    target,
                    encoded,
                    replace_existing=False,
                )

            self.assertEqual(encoded, target.read_bytes())
            self.assertEqual(sentinel, temporary_path.read_bytes())

    def test_journal_fsync_failure_cannot_mint_initial_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "control.json"
            store = ControlDomainStore(path)
            store._journal_path.mkdir()
            original_fsync = os.fsync
            directory_fsyncs = 0

            def fail_first_directory_fsync(descriptor: int) -> None:
                nonlocal directory_fsyncs
                if (
                    any(store._journal_path.glob("*.json"))
                    and stat.S_ISDIR(os.fstat(descriptor).st_mode)
                ):
                    directory_fsyncs += 1
                    if directory_fsyncs == 1:
                        raise OSError("injected journal directory fsync failure")
                original_fsync(descriptor)

            with patch(
                "decision_os.companion.broker_control.os.fsync",
                side_effect=fail_first_directory_fsync,
            ):
                with self.assertRaisesRegex(OSError, "journal directory"):
                    store.activate_initial(activation())

            self.assertFalse(path.exists())
            with self.assertRaises(ControlRecordIntegrityError):
                ControlDomainStore(path).require_active(activation())
            self.assertEqual([], list(root.rglob(".broker-control-*.tmp")))

    def test_head_directory_fsync_failure_is_complete_or_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "control.json"
            store = ControlDomainStore(path)
            store._journal_path.mkdir()
            original_fsync = os.fsync
            failed = False

            def fail_second_directory_fsync(descriptor: int) -> None:
                nonlocal failed
                metadata = os.fstat(descriptor)
                parent = path.parent.stat()
                if (
                    not failed
                    and stat.S_ISDIR(metadata.st_mode)
                    and (metadata.st_dev, metadata.st_ino)
                    == (parent.st_dev, parent.st_ino)
                    and path.exists()
                ):
                    failed = True
                    raise OSError("injected head directory fsync failure")
                original_fsync(descriptor)

            with patch(
                "decision_os.companion.broker_control.os.fsync",
                side_effect=fail_second_directory_fsync,
            ):
                with self.assertRaisesRegex(OSError, "head directory"):
                    store.activate_initial(activation())

            reloaded = ControlDomainStore(path).require_active(activation())
            self.assertEqual(ControlDomainState.ACTIVE, reloaded.state)
            self.assertEqual([], list(root.rglob(".broker-control-*.tmp")))

    def test_control_readback_mismatch_never_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            foreign_store = ControlDomainStore(root / "foreign" / "control.json")
            foreign = foreign_store.activate_initial(
                activation(authority_domain_id="foreign-domain")
            )
            path = root / "subject" / "control.json"
            store = ControlDomainStore(path)

            with patch.object(
                store,
                "_load_required_unlocked",
                return_value=foreign,
            ):
                with self.assertRaisesRegex(
                    ControlRecordIntegrityError,
                    "readback mismatches",
                ):
                    store.activate_initial(activation())

            self.assertEqual(
                [],
                list(path.parent.rglob(".broker-control-*.tmp")),
            )

    def test_real_corrupt_postpublication_readback_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            store = ControlDomainStore(path)
            original_replace = os.replace

            def corrupt_head_after_replace(
                source: Any,
                target: Any,
                **kwargs: Any,
            ) -> None:
                original_replace(source, target, **kwargs)
                if Path(target).name == path.name:
                    path.write_bytes(b'{"torn":')

            with patch(
                "decision_os.companion.broker_control.os.replace",
                side_effect=corrupt_head_after_replace,
            ):
                with self.assertRaisesRegex(
                    ControlRecordIntegrityError,
                    "readback mismatches",
                ):
                    store.activate_initial(activation())

            with self.assertRaises(ControlRecordIntegrityError):
                ControlDomainStore(path).require_active(activation())

    def test_safe_journal_tail_repairs_a_stale_head_before_successor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            old = activation()
            store = ControlDomainStore(path)
            store.activate_initial(old)
            original_replace = os.replace

            def fail_head_replace(source: Any, target: Any, **kwargs: Any) -> None:
                if Path(target).name == path.name:
                    raise OSError("simulated stale head")
                original_replace(source, target, **kwargs)

            with patch(
                "decision_os.companion.broker_control.os.replace",
                side_effect=fail_head_replace,
            ):
                with self.assertRaisesRegex(OSError, "stale head"):
                    store.transition(old, ControlDomainState.ABANDONED)

            with self.assertRaisesRegex(
                ControlRecordIntegrityError,
                "does not match its durable journal",
            ):
                ControlDomainStore(path).require_active(old)

            successor = replace(
                old,
                authority_domain_id="safe-tail-successor",
                protected_repository_identity=f"protected:v1:{'8' * 64}",
                write_principal_identity=f"principal:v1:{'8' * 64}",
            )
            recovered_store = ControlDomainStore(path)
            predecessor = recovered_store.recover_control_head_fail_closed()
            recovered = recovered_store.activate_successor(
                predecessor,
                successor,
            )
            self.assertEqual(ControlDomainState.ACTIVE, recovered.state)
            with self.assertRaises(AuthorityRejectedError):
                ControlDomainStore(path).require_active(old)

    def test_unpublished_active_tail_recovers_as_uncertain_then_abandoned(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            first = activation()
            second = replace(
                first,
                authority_domain_id="incomplete-successor",
                protected_repository_identity=f"protected:v1:{'9' * 64}",
                write_principal_identity=f"principal:v1:{'9' * 64}",
            )
            store = ControlDomainStore(path)
            store.activate_initial(first)
            store.transition(first, ControlDomainState.ABANDONED)
            original_replace = os.replace

            def fail_head_replace(source: Any, target: Any, **kwargs: Any) -> None:
                if Path(target).name == path.name:
                    raise OSError("simulated unpublished active head")
                original_replace(source, target, **kwargs)

            with patch(
                "decision_os.companion.broker_control.os.replace",
                side_effect=fail_head_replace,
            ):
                with self.assertRaisesRegex(OSError, "unpublished active"):
                    store.activate_successor(store.load_required(), second)

            with self.assertRaises(ControlRecordIntegrityError):
                ControlDomainStore(path).require_active(second)
            abandoned = ControlDomainStore(path).transition(
                second,
                ControlDomainState.ABANDONED,
            )
            self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)
            with self.assertRaises(AuthorityRejectedError):
                ControlDomainStore(path).require_active(second)


class BrokerControlAuthorityTest(unittest.TestCase):
    def test_fresh_domain_tuple_is_current_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            expected = activation()

            record = store.activate_initial(expected)

            self.assertEqual(expected, record.activation)
            self.assertEqual(record, store.require_active(expected))
            self.assertEqual((), record.retired_authority_domain_ids)

    def test_concurrent_initial_activation_has_exactly_one_winner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"

            def attempt(index: int) -> str:
                try:
                    ControlDomainStore(path).activate_initial(
                        activation(authority_domain_id=f"domain-{index}")
                    )
                except ControlDomainTransitionError:
                    return "REJECTED"
                return "ACTIVE"

            with ThreadPoolExecutor(max_workers=16) as executor:
                outcomes = tuple(executor.map(attempt, range(16)))

            self.assertEqual(1, outcomes.count("ACTIVE"))
            self.assertEqual(15, outcomes.count("REJECTED"))
            self.assertEqual(
                ControlDomainState.ACTIVE,
                ControlDomainStore(path).load_required().state,
            )

    def test_activation_identities_and_generation_are_bounded(self) -> None:
        cases = (
            {"authority_domain_id": " leading-space"},
            {"authority_domain_id": "control\ncharacter"},
            {"protected_repository_identity": "x" * 257},
            {"write_principal_identity": ""},
            {"repository_id": "repository-without-versioned-digest"},
            {"repository_id": f"repo:v1:{'A' * 64}"},
            {"generation_witness": -1},
            {"generation_witness": 1 << 64},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    activation(**overrides)

    def test_activation_scalar_subclasses_are_rejected_exactly(self) -> None:
        cases = {
            "authority_domain_id": EqualitySpoofStr("authority-domain-other"),
            "repository_id": EqualitySpoofStr(f"repo:v1:{'4' * 64}"),
            "protected_repository_identity": EqualitySpoofStr(
                f"protected:v1:{'5' * 64}"
            ),
            "write_principal_identity": EqualitySpoofStr(
                f"principal:v1:{'6' * 64}"
            ),
            "generation_witness": EqualitySpoofInt(8),
        }

        for field, spoof in cases.items():
            with self.subTest(field=field), self.assertRaises(ValueError):
                activation(**{field: spoof})

    def test_spoof_fields_cannot_match_or_transition_current_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            store.activate_initial(current)
            cases: dict[str, tuple[Any, Any]] = {
                "authority_domain_id": (
                    "authority-domain-other",
                    EqualitySpoofStr("authority-domain-other"),
                ),
                "repository_id": (
                    f"repo:v1:{'4' * 64}",
                    EqualitySpoofStr(f"repo:v1:{'4' * 64}"),
                ),
                "protected_repository_identity": (
                    f"protected:v1:{'5' * 64}",
                    EqualitySpoofStr(f"protected:v1:{'5' * 64}"),
                ),
                "write_principal_identity": (
                    f"principal:v1:{'6' * 64}",
                    EqualitySpoofStr(f"principal:v1:{'6' * 64}"),
                ),
                "generation_witness": (8, EqualitySpoofInt(8)),
            }

            for field, (plain_mismatch, spoof) in cases.items():
                with self.subTest(field=field):
                    candidate = activation(**{field: plain_mismatch})
                    object.__setattr__(candidate, field, spoof)
                    with self.assertRaises(AuthorityRejectedError):
                        store.require_active(candidate)
                    with self.assertRaises(AuthorityRejectedError):
                        store.transition(
                            candidate,
                            ControlDomainState.UNCERTAIN,
                        )

            self.assertEqual(
                current,
                store.require_active(current).activation,
            )

    def test_activation_subclass_cannot_acquire_or_match_authority(self) -> None:
        current = activation()
        spoof = EqualitySpoofActivation(
            authority_domain_id="spoof-domain",
            repository_id=f"repo:v1:{'4' * 64}",
            protected_repository_identity=f"protected:v1:{'5' * 64}",
            write_principal_identity=f"principal:v1:{'6' * 64}",
            generation_witness=99,
        )
        self.assertTrue(spoof == current)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = ControlDomainStore(root / "control.json")
            store.activate_initial(current)

            with self.assertRaises(AuthorityRejectedError):
                store.require_active(spoof)
            with self.assertRaises(AuthorityRejectedError):
                store.transition(spoof, ControlDomainState.UNCERTAIN)
            with self.assertRaises(MutationDecisionError):
                replace_decision(spoof)

            abandoned = store.transition(
                current,
                ControlDomainState.ABANDONED,
            )
            with self.assertRaises(ControlDomainTransitionError):
                store.activate_successor(abandoned, spoof)
            self.assertEqual(abandoned, store.load_required())

            with self.assertRaises(ControlDomainTransitionError):
                ControlDomainStore(root / "other.json").activate_initial(spoof)

    def test_every_activation_tuple_component_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            current = scenario.current
            mismatches = {
                "authority-domain": replace(
                    current,
                    authority_domain_id="authority-domain-other",
                ),
                "repository": replace(
                    current,
                    repository_id=f"repo:v1:{'4' * 64}",
                ),
                "protected-repository": replace(
                    current,
                    protected_repository_identity=f"protected:v1:{'5' * 64}",
                ),
                "write-principal": replace(
                    current,
                    write_principal_identity=f"principal:v1:{'6' * 64}",
                ),
                "generation-witness": replace(current, generation_witness=8),
            }

            for label, mismatch in mismatches.items():
                with self.subTest(label=label):
                    with self.assertRaises(AuthorityRejectedError):
                        store.require_active(mismatch)
                    attempt = Mock()
                    with (
                        patch.object(broker_apply, "_attempt_live", attempt),
                        self.assertRaises(BrokerControlError),
                    ):
                        scenario.apply_as(mismatch)
                    attempt.assert_not_called()

            self.assertEqual(current, store.load_required().activation)
            self.assertFalse(store._fence_path.exists())

    def test_repository_identity_mismatch_fails_before_cas(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            current = scenario.current
            mismatch = replace(
                current,
                repository_id=f"repo:v1:{'9' * 64}",
            )

            attempt = Mock()
            with (
                patch.object(broker_apply, "_attempt_live", attempt),
                self.assertRaises(AuthorityRejectedError),
            ):
                scenario.apply_as(mismatch)
            attempt.assert_not_called()

            self.assertEqual(ControlDomainState.ACTIVE, store.load_required().state)

    def test_write_principal_identity_mismatch_fails_before_cas(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            current = scenario.current
            mismatch = replace(
                current,
                write_principal_identity=f"principal:v1:{'8' * 64}",
            )

            attempt = Mock()
            with (
                patch.object(broker_apply, "_attempt_live", attempt),
                self.assertRaises(AuthorityRejectedError),
            ):
                scenario.apply_as(mismatch)
            attempt.assert_not_called()

            self.assertEqual(ControlDomainState.ACTIVE, store.load_required().state)

    def test_abandoned_domain_cannot_authorize_or_reactivate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            old = scenario.current
            abandoned = store.transition(old, ControlDomainState.ABANDONED)

            self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)
            self.assertIn(
                old.authority_domain_id,
                abandoned.retired_authority_domain_ids,
            )
            with self.assertRaises(AuthorityRejectedError):
                store.require_active(old)
            attempt = Mock()
            with (
                patch.object(broker_apply, "_attempt_live", attempt),
                self.assertRaises(AuthorityRejectedError),
            ):
                scenario.apply()
            attempt.assert_not_called()
            with self.assertRaises(ControlDomainTransitionError):
                store.transition(old, ControlDomainState.ACTIVE)

    def test_numeric_generation_reuse_does_not_restore_abandoned_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(
                Path(temporary),
                activation_overrides={"generation_witness": 41},
            )
            first_process = scenario.store
            old = scenario.current
            first_process.transition(old, ControlDomainState.ABANDONED)
            successor = replace(
                old,
                authority_domain_id="authority-domain-successor",
                protected_repository_identity=f"protected:v1:{'7' * 64}",
                write_principal_identity=f"principal:v1:{'7' * 64}",
                generation_witness=41,
            )

            second_process = scenario.restarted_store(authenticated=True)
            current = second_process.activate_successor(
                second_process.load_required(),
                successor,
            )

            self.assertEqual(41, current.activation.generation_witness)
            self.assertEqual(
                successor,
                second_process.require_active(successor).activation,
            )
            with self.assertRaises(AuthorityRejectedError):
                first_process.require_active(old)
            attempt = Mock()
            with (
                patch.object(broker_apply, "_attempt_live", attempt),
                self.assertRaises(AuthorityRejectedError),
            ):
                scenario.apply(store=second_process)
            attempt.assert_not_called()

    def test_exact_stale_active_head_replay_cannot_erase_abandonment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            store = ControlDomainStore(path)
            old = activation()
            store.activate_initial(old)
            stale_active_bytes = path.read_bytes()
            store.transition(old, ControlDomainState.ABANDONED)

            path.write_bytes(stale_active_bytes)

            with self.assertRaisesRegex(
                ControlRecordIntegrityError,
                "does not match its durable journal",
            ):
                ControlDomainStore(path).require_active(old)

    def test_retired_domain_id_can_never_be_selected_as_a_later_successor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            first = activation(authority_domain_id="domain-first")
            second = replace(
                first,
                authority_domain_id="domain-second",
                protected_repository_identity=f"protected:v1:{'d' * 64}",
                write_principal_identity=f"principal:v1:{'d' * 64}",
            )
            store.activate_initial(first)
            store.transition(first, ControlDomainState.ABANDONED)
            store.activate_successor(store.load_required(), second)
            store.transition(second, ControlDomainState.ABANDONED)

            with self.assertRaisesRegex(
                ControlDomainTransitionError,
                "retired",
            ):
                store.activate_successor(store.load_required(), first)

            self.assertEqual(
                ControlDomainState.ABANDONED,
                store.load_required().state,
            )

    def test_uncertain_domain_is_abandoned_not_repaired_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            current = scenario.current
            uncertain = store.transition(current, ControlDomainState.UNCERTAIN)

            self.assertEqual(ControlDomainState.UNCERTAIN, uncertain.state)
            with self.assertRaises(AuthorityRejectedError):
                store.require_active(current)
            with self.assertRaises(ControlDomainTransitionError):
                store.transition(current, ControlDomainState.ACTIVE)

            abandoned = store.transition(current, ControlDomainState.ABANDONED)
            successor = replace(
                current,
                authority_domain_id="fresh-after-uncertainty",
                protected_repository_identity=f"protected:v1:{'a' * 64}",
                write_principal_identity=f"principal:v1:{'a' * 64}",
                generation_witness=current.generation_witness,
            )
            activated = store.activate_successor(abandoned, successor)
            self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)
            self.assertEqual(ControlDomainState.ACTIVE, activated.state)
            with self.assertRaises(AuthorityRejectedError):
                scenario.restarted_store().require_active(current)
            attempt = Mock()
            with (
                patch.object(broker_apply, "_attempt_live", attempt),
                self.assertRaises(AuthorityRejectedError),
            ):
                scenario.apply(store=scenario.restarted_store(authenticated=True))
            attempt.assert_not_called()

    def test_no_force_unlock_or_generic_record_overwrite_path_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")

            self.assertFalse(hasattr(store, "force_unlock"))
            self.assertFalse(hasattr(store, "unlock"))
            self.assertFalse(hasattr(store, "save"))

    def test_retirement_capacity_fails_before_stranding_an_active_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            store.activate_initial(current)
            store.transition(current, ControlDomainState.ABANDONED)
            successor = replace(
                current,
                authority_domain_id="capacity-successor",
                protected_repository_identity=f"protected:v1:{'e' * 64}",
                write_principal_identity=f"principal:v1:{'e' * 64}",
            )

            with patch(
                "decision_os.companion.broker_control._MAX_RETIRED_DOMAINS",
                1,
            ):
                with self.assertRaisesRegex(
                    ControlDomainTransitionError,
                    "capacity is exhausted",
                ):
                    store.activate_successor(store.load_required(), successor)

            self.assertEqual(
                ControlDomainState.ABANDONED,
                store.load_required().state,
            )

    def test_serialized_capacity_is_reserved_before_successor_activation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            first = activation(authority_domain_id="first-domain")
            store.activate_initial(first)
            abandoned = store.transition(first, ControlDomainState.ABANDONED)
            successor = replace(
                first,
                authority_domain_id="s" * 240,
                protected_repository_identity=f"protected:v1:{'f' * 64}",
                write_principal_identity=f"principal:v1:{'f' * 64}",
            )
            active_candidate = broker_control._new_record(
                successor,
                state=ControlDomainState.ACTIVE,
                journal_position=abandoned.journal_position + 1,
                predecessor_record_sha256=abandoned.record_sha256,
                retired_authority_domain_ids=(
                    abandoned.retired_authority_domain_ids
                ),
            )
            abandoned_candidate = store._prospective_record(
                active_candidate,
                ControlDomainState.ABANDONED,
            )
            active_size = len(
                broker_control._canonical_record_bytes(active_candidate)
            )
            abandoned_size = len(
                broker_control._canonical_record_bytes(abandoned_candidate)
            )
            self.assertLess(active_size, abandoned_size)
            limit = (active_size + abandoned_size) // 2

            with patch(
                "decision_os.companion.broker_control._MAX_CONTROL_RECORD_BYTES",
                limit,
            ):
                with self.assertRaisesRegex(
                    ControlDomainTransitionError,
                    "reserve durable abandonment capacity",
                ):
                    store.activate_successor(store.load_required(), successor)

            self.assertEqual(abandoned, store.load_required())

    def test_store_does_not_change_existing_parent_directory_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary) / "existing-state"
            parent.mkdir(mode=0o750)
            os.chmod(parent, 0o750)
            store = ControlDomainStore(parent / "control.json")

            store.activate_initial(activation())

            self.assertEqual(0o750, parent.stat().st_mode & 0o777)

    def test_successor_requires_an_explicit_abandonment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            successor = replace(
                current,
                authority_domain_id="premature-successor",
            )
            store.activate_initial(current)

            with self.assertRaises(ControlDomainTransitionError):
                store.activate_successor(store.load_required(), successor)

            self.assertEqual(current, store.require_active(current).activation)

    def test_stale_abandoned_predecessor_cannot_activate_a_later_successor(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            first = activation(authority_domain_id="domain-a")
            first_abandoned = store.activate_initial(first)
            first_abandoned = store.transition(
                first,
                ControlDomainState.ABANDONED,
            )
            second = replace(
                first,
                authority_domain_id="domain-b",
                protected_repository_identity=f"protected:v1:{'b' * 64}",
                write_principal_identity=f"principal:v1:{'c' * 64}",
                generation_witness=8,
            )
            store.activate_successor(first_abandoned, second)
            second_abandoned = store.transition(
                second,
                ControlDomainState.ABANDONED,
            )
            stale_successor = replace(
                first,
                authority_domain_id="domain-c",
            )

            with self.assertRaisesRegex(
                AuthorityRejectedError,
                "predecessor",
            ):
                store.activate_successor(first_abandoned, stale_successor)

            self.assertEqual(second_abandoned, store.load_required())

    def test_record_subclass_cannot_alias_successor_predecessor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            initial = store.activate_initial(current)
            abandoned = store.transition(
                current,
                ControlDomainState.ABANDONED,
            )
            fake = EqualitySpoofRecord(
                schema=initial.schema,
                activation=initial.activation,
                state=initial.state,
                journal_position=initial.journal_position,
                predecessor_record_sha256=initial.predecessor_record_sha256,
                retired_authority_domain_ids=("unrelated-retired-domain",),
                record_sha256="0" * 64,
            )
            successor = replace(
                current,
                authority_domain_id="record-spoof-successor",
                protected_repository_identity=f"protected:v1:{'8' * 64}",
                write_principal_identity=f"principal:v1:{'8' * 64}",
            )
            self.assertTrue(fake == abandoned)

            with self.assertRaises(ControlDomainTransitionError):
                store.activate_successor(fake, successor)

            self.assertEqual(abandoned, store.load_required())

    def test_successor_requires_fresh_protected_and_principal_identities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            store.activate_initial(current)
            abandoned = store.transition(current, ControlDomainState.ABANDONED)
            cases = (
                replace(
                    current,
                    authority_domain_id="same-protected",
                    write_principal_identity=f"principal:v1:{'4' * 64}",
                ),
                replace(
                    current,
                    authority_domain_id="same-principal",
                    protected_repository_identity=f"protected:v1:{'5' * 64}",
                ),
            )
            for successor in cases:
                with self.subTest(successor=successor.authority_domain_id):
                    with self.assertRaises(ControlDomainTransitionError):
                        store.activate_successor(abandoned, successor)

            self.assertEqual(abandoned, store.load_required())

    def test_successor_cannot_reuse_any_historical_protected_or_principal_identity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            first = activation(authority_domain_id="historical-a")
            first_abandoned = store.activate_initial(first)
            first_abandoned = store.transition(
                first,
                ControlDomainState.ABANDONED,
            )
            second = replace(
                first,
                authority_domain_id="historical-b",
                protected_repository_identity=f"protected:v1:{'6' * 64}",
                write_principal_identity=f"principal:v1:{'6' * 64}",
            )
            store.activate_successor(first_abandoned, second)
            second_abandoned = store.transition(
                second,
                ControlDomainState.ABANDONED,
            )
            reuse_first = replace(
                first,
                authority_domain_id="historical-c",
            )

            with self.assertRaises(ControlDomainTransitionError):
                store.activate_successor(second_abandoned, reuse_first)

            self.assertEqual(second_abandoned, store.load_required())

    def test_transition_journal_binds_the_exact_predecessor_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            initial = store.activate_initial(current)
            uncertain = store.transition(current, ControlDomainState.UNCERTAIN)
            abandoned = store.transition(current, ControlDomainState.ABANDONED)

            self.assertEqual(0, initial.journal_position)
            self.assertEqual(1, uncertain.journal_position)
            self.assertEqual(initial.record_sha256, uncertain.predecessor_record_sha256)
            self.assertEqual(2, abandoned.journal_position)
            self.assertEqual(
                uncertain.record_sha256,
                abandoned.predecessor_record_sha256,
            )


class BrokerControlCASTest(unittest.TestCase):
    def test_unacquired_decision_binding_preserves_slice_one_hash_shape(
        self,
    ) -> None:
        decision = replace_decision(activation())

        self.assertIsNone(decision.proposal_acquisition_sha256)
        self.assertNotIn(
            "proposal_acquisition_sha256",
            MutationDecision.binding_dict(decision),
        )

    def test_exact_prior_post_and_neither_reconcile_to_fixed_outcomes(self) -> None:
        decision = replace_decision(activation())

        self.assertEqual(
            ReconciliationOutcome.NOT_APPLIED,
            reconcile_mutation(
                decision,
                TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
            ),
        )
        self.assertEqual(
            ReconciliationOutcome.APPLIED,
            reconcile_mutation(
                decision,
                TargetObservation(TargetKind.REGULAR, b"exact post\n"),
            ),
        )
        self.assertEqual(
            ReconciliationOutcome.UNCERTAIN,
            reconcile_mutation(
                decision,
                TargetObservation(TargetKind.REGULAR, b"neither\n"),
            ),
        )

    def test_create_distinguishes_absence_from_an_empty_regular_file(self) -> None:
        decision = create_decision(activation())

        self.assertEqual(
            ReconciliationOutcome.NOT_APPLIED,
            reconcile_mutation(decision, TargetObservation(TargetKind.ABSENT)),
        )
        self.assertEqual(
            ReconciliationOutcome.APPLIED,
            reconcile_mutation(
                decision,
                TargetObservation(TargetKind.REGULAR, b"created bytes\n"),
            ),
        )
        self.assertEqual(
            ReconciliationOutcome.UNCERTAIN,
            reconcile_mutation(
                decision,
                TargetObservation(TargetKind.REGULAR, b""),
            ),
        )

    def test_unsupported_target_identities_are_always_uncertain(self) -> None:
        decision = replace_decision(activation())

        for kind in (
            TargetKind.ABSENT,
            TargetKind.SYMLINK,
            TargetKind.HARDLINK,
            TargetKind.DIRECTORY,
            TargetKind.OTHER,
        ):
            with self.subTest(kind=kind.value):
                self.assertEqual(
                    ReconciliationOutcome.UNCERTAIN,
                    reconcile_mutation(decision, TargetObservation(kind)),
                )

    def test_recovery_without_durable_intent_is_rejected_without_consumption(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            observe = Mock()

            with (
                patch(
                    "decision_os.companion.broker_control.reconcile_mutation"
                ) as reconcile,
                patch(
                    "decision_os.companion.broker_apply._recovery_observation_from_root_fd",
                    observe,
                ),
                patch.object(store, "_append_cas_fence_unlocked") as append,
                self.assertRaisesRegex(
                    AuthorityRejectedError,
                    "requires exactly one durable pending CAS intent",
                ),
            ):
                scenario.recover()

            observe.assert_not_called()
            reconcile.assert_not_called()
            append.assert_not_called()
            self.assertEqual(
                scenario.initial,
                store.require_active(scenario.current),
            )
            self.assertFalse(store._fence_path.exists())

    def test_raw_cas_assertion_callbacks_are_not_public(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            decision = replace_decision(current)
            initial = store.activate_initial(current)
            mint_applied = Mock(return_value=ReconciliationOutcome.APPLIED)
            mint_not_applied = Mock(
                return_value=TargetObservation(
                    TargetKind.REGULAR,
                    b"exact prior\n",
                )
            )

            self.assertFalse(hasattr(store, "execute_live_cas"))
            self.assertFalse(hasattr(store, "execute_recovery_cas"))
            self.assertFalse(hasattr(store, "recover_cas"))
            self.assertFalse(hasattr(store, "reconcile_cas"))
            with self.assertRaises(AttributeError):
                store.execute_live_cas(  # type: ignore[attr-defined]
                    decision,
                    mint_applied,
                )
            with self.assertRaises(AttributeError):
                store.execute_recovery_cas(  # type: ignore[attr-defined]
                    decision,
                    mint_not_applied,
                )

            mint_applied.assert_not_called()
            mint_not_applied.assert_not_called()
            self.assertEqual(initial, store.require_active(current))
            self.assertFalse(store._fence_path.exists())

            public_methods = {
                name
                for name in dir(store)
                if not name.startswith("_") and callable(getattr(store, name))
            }
            self.assertTrue(
                {
                    "activate_initial",
                    "activate_successor",
                    "load",
                    "load_required",
                    "require_active",
                    "transition",
                }.issubset(public_methods)
            )
            self.assertFalse(
                any("cas" in name or "reconcil" in name for name in public_methods)
            )

    def test_second_live_execute_is_rejected_even_for_the_exact_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            scenario.leave_pending()
            original_fences = tuple(store._fence_path.iterdir())
            second_attempt = Mock()

            with (
                patch.object(store, "_append_cas_fence_unlocked") as append,
                patch.object(
                    broker_apply,
                    "_attempt_live",
                    second_attempt,
                ),
                self.assertRaisesRegex(
                    AuthorityRejectedError,
                    "live apply cannot resume",
                ),
            ):
                scenario.apply()

            append.assert_not_called()
            second_attempt.assert_not_called()
            self.assertEqual(original_fences, tuple(store._fence_path.iterdir()))
            self.assertEqual(ControlDomainState.UNCERTAIN, store.load_required().state)

    def test_live_not_applied_is_rejected_and_only_recovery_can_prove_it(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            attempt = Mock(return_value=ReconciliationOutcome.NOT_APPLIED)

            with (
                patch.object(broker_apply, "_attempt_live", attempt),
                self.assertRaisesRegex(
                    MutationDecisionError,
                    "only through CAS recovery",
                ),
            ):
                scenario.apply()

            self.assertEqual(1, attempt.call_count)
            journal = store._journal_records_unlocked()
            fences = store._cas_fences_unlocked(journal)
            self.assertEqual(1, len(fences))
            self.assertEqual("INTENT", fences[0].kind)
            self.assertEqual(ControlDomainState.UNCERTAIN, store.load_required().state)
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                scenario.recover(),
            )
            self.assertEqual(ControlDomainState.ABANDONED, store.load_required().state)

    def test_active_head_with_durable_intent_is_recovery_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            path = scenario.path
            store = scenario.store
            current = scenario.current
            initial = scenario.initial
            attempt = Mock()

            with (
                patch.object(
                    store,
                    "_mark_pending_cas_uncertain_unlocked",
                    side_effect=RuntimeError("simulated crash after durable intent"),
                ),
                self.assertRaisesRegex(RuntimeError, "after durable intent"),
            ):
                scenario.apply()

            attempt.assert_not_called()

            journal = store._journal_records_unlocked()
            fences = store._cas_fences_unlocked(journal)
            self.assertEqual((initial,), journal)
            self.assertEqual(1, len(fences))
            self.assertEqual("INTENT", fences[0].kind)
            with self.assertRaisesRegex(
                ControlRecordIntegrityError,
                "consumed CAS fence",
            ):
                ControlDomainStore(path).require_active(current)
            with self.assertRaisesRegex(
                AuthorityRejectedError,
                "live apply cannot resume",
            ), patch.object(broker_apply, "_attempt_live", attempt):
                scenario.apply(store=scenario.restarted_store(authenticated=True))
            attempt.assert_not_called()

            restarted = scenario.restarted_store()
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                scenario.recover(store=restarted),
            )
            recovered_journal = restarted._journal_records_unlocked()
            self.assertEqual(
                (
                    ControlDomainState.ACTIVE,
                    ControlDomainState.UNCERTAIN,
                    ControlDomainState.ABANDONED,
                ),
                tuple(record.state for record in recovered_journal),
            )
            self.assertEqual(
                2,
                len(restarted._cas_fences_unlocked(recovered_journal)),
            )

    def test_recovery_observes_after_failed_live_callback_releases_lock(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            target_path = scenario.target
            attempt_entered = threading.Event()
            finish_attempt = threading.Event()
            recovery_started = threading.Event()
            observer_called = threading.Event()
            attempt = Mock()
            observed_bytes: list[bytes] = []

            def blocked_live_attempt(
                _parent_fd: int,
                _name: str,
                _decision: MutationDecision,
            ) -> ReconciliationOutcome:
                attempt()
                attempt_entered.set()
                self.assertTrue(finish_attempt.wait(timeout=10))
                target_path.write_bytes(b"exact post\n")
                raise RuntimeError("simulated failure after live mutation")

            original_observation = broker_apply._recovery_observation_from_root_fd

            def observe_target(*args: Any, **kwargs: Any) -> TargetObservation:
                observed = target_path.read_bytes()
                observed_bytes.append(observed)
                observer_called.set()
                return original_observation(*args, **kwargs)

            def recover_target() -> ReconciliationOutcome:
                recovery_started.set()
                return scenario.recover(
                    store=scenario.restarted_store(),
                )

            reconcile = Mock(wraps=reconcile_mutation)
            with (
                patch(
                    "decision_os.companion.broker_control.reconcile_mutation",
                    reconcile,
                ),
                patch.object(
                    broker_apply,
                    "_attempt_live",
                    side_effect=blocked_live_attempt,
                ),
                patch.object(
                    broker_apply,
                    "_recovery_observation_from_root_fd",
                    side_effect=observe_target,
                ),
                ThreadPoolExecutor(max_workers=2) as executor,
            ):
                live_future = executor.submit(scenario.apply)
                try:
                    self.assertTrue(attempt_entered.wait(timeout=10))
                    self.assertEqual(b"exact prior\n", target_path.read_bytes())
                    recovery_future = executor.submit(recover_target)
                    self.assertTrue(recovery_started.wait(timeout=10))
                    with self.assertRaises(FutureTimeoutError):
                        recovery_future.result(timeout=0.1)
                    self.assertFalse(observer_called.is_set())
                    reconcile.assert_not_called()
                finally:
                    finish_attempt.set()

                with self.assertRaisesRegex(RuntimeError, "after live mutation"):
                    live_future.result(timeout=10)
                self.assertEqual(
                    ReconciliationOutcome.APPLIED,
                    recovery_future.result(timeout=10),
                )

            attempt.assert_called_once_with()
            self.assertEqual([b"exact post\n"], observed_bytes)
            self.assertTrue(observer_called.is_set())
            reconcile.assert_called_once()
            self.assertEqual(
                ControlDomainState.ABANDONED,
                store.load_required().state,
            )

    def test_durable_intent_reconciles_exactly_after_process_restart(self) -> None:
        cases = (
            (
                "prior",
                b"exact prior\n",
                ReconciliationOutcome.NOT_APPLIED,
                ControlDomainState.ABANDONED,
            ),
            (
                "post",
                b"exact post\n",
                ReconciliationOutcome.APPLIED,
                ControlDomainState.ABANDONED,
            ),
            (
                "neither",
                b"neither\n",
                ReconciliationOutcome.UNCERTAIN,
                ControlDomainState.UNCERTAIN,
            ),
        )
        for label, content, expected, terminal_state in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                scenario = CanonicalCASScenario(Path(temporary))
                path = scenario.path
                current = scenario.current
                scenario.leave_pending()
                scenario.set_target(content)

                with self.assertRaises(AuthorityRejectedError):
                    scenario.restarted_store().require_active(current)

                restarted = scenario.restarted_store()
                outcome = scenario.recover(store=restarted)

                self.assertEqual(expected, outcome)
                self.assertEqual(terminal_state, restarted.load_required().state)
                observe_after_completion = Mock(
                    side_effect=AssertionError(
                        "completed recovery must not sample the target"
                    )
                )
                if terminal_state is ControlDomainState.ABANDONED:
                    with patch.object(
                        broker_apply,
                        "_recovery_observation_from_root_fd",
                        observe_after_completion,
                    ):
                        with self.assertRaises(AuthorityRejectedError):
                            scenario.recover(store=scenario.restarted_store())
                else:
                    with self.assertRaises(AuthorityRejectedError):
                        scenario.recover(store=scenario.restarted_store())
                observe_after_completion.assert_not_called()
                with self.assertRaises(AuthorityRejectedError):
                    restarted.require_active(current)

    def test_pending_intent_rejects_a_different_decision_before_reconciliation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            path = scenario.path
            current = scenario.current
            store = scenario.store
            scenario.leave_pending()

            different = replace_decision(
                current,
                post=b"different post\n",
            )
            reconstructed = store._reconstruct_pending_decision()
            self.assertEqual(scenario.decision, reconstructed)
            self.assertNotEqual(different, reconstructed)
            with self.assertRaisesRegex(
                ControlDomainTransitionError,
                "pending CAS intent",
            ):
                ControlDomainStore(path).transition(
                    current,
                    ControlDomainState.ABANDONED,
                )
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                scenario.recover(store=scenario.restarted_store()),
            )

    def test_pending_intent_rejects_every_activation_mismatch_before_observation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            current = scenario.current
            scenario.leave_pending()

            mismatches = (
                replace(current, authority_domain_id="other-domain"),
                replace(current, repository_id=f"repo:v1:{'4' * 64}"),
                replace(
                    current,
                    protected_repository_identity=f"protected:v1:{'5' * 64}",
                ),
                replace(
                    current,
                    write_principal_identity=f"principal:v1:{'6' * 64}",
                ),
                replace(current, generation_witness=8),
            )
            for mismatch in mismatches:
                with self.subTest(mismatch=mismatch):
                    self.assertNotEqual(
                        replace_decision(mismatch),
                        scenario.store._reconstruct_pending_decision(),
                    )

            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                scenario.recover(store=scenario.restarted_store()),
            )

    def test_lost_pending_intent_remains_uncertain_and_cannot_regain_authority(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            current = scenario.current
            store = scenario.store
            scenario.leave_pending()
            for fence_path in store._fence_path.glob("*.json"):
                fence_path.unlink()
            store._fence_path.rmdir()

            restarted = scenario.restarted_store()
            self.assertEqual(ControlDomainState.UNCERTAIN, restarted.load_required().state)
            with self.assertRaises(AuthorityRejectedError):
                restarted.require_active(current)
            with self.assertRaises(AuthorityRejectedError):
                scenario.recover(store=restarted)
            abandoned = restarted.transition(
                current,
                ControlDomainState.ABANDONED,
            )
            self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)
            with self.assertRaises(AuthorityRejectedError):
                restarted.require_active(current)

    def test_exact_completion_is_control_journal_bound_if_fences_are_lost(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            current = scenario.current
            store = scenario.store
            self.assertEqual(
                ReconciliationOutcome.APPLIED,
                scenario.apply(),
            )
            for fence in store._fence_path.iterdir():
                fence.unlink()
            store._fence_path.rmdir()

            restarted = scenario.restarted_store()
            self.assertEqual(
                ControlDomainState.ABANDONED,
                restarted.load_required().state,
            )
            with self.assertRaises(AuthorityRejectedError):
                restarted.require_active(current)
            with self.assertRaises(AuthorityRejectedError):
                scenario.recover(store=restarted)

    def test_completion_directory_fsync_failure_resumes_without_false_applied(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            current = scenario.current
            store = scenario.store
            original_fsync = os.fsync
            fail_completion_directory = False
            completion_path: Path | None = None

            def fail_exact_completion_directory_fsync(descriptor: int) -> None:
                nonlocal fail_completion_directory
                if (
                    fail_completion_directory
                    and completion_path is not None
                    and completion_path.exists()
                    and stat.S_ISDIR(os.fstat(descriptor).st_mode)
                ):
                    fail_completion_directory = False
                    raise OSError("simulated terminal CAS directory fsync")
                original_fsync(descriptor)

            original_complete = broker_control._complete_cas_intent

            def mark_completion(*args: Any, **kwargs: Any) -> Any:
                nonlocal completion_path, fail_completion_directory
                completion = original_complete(*args, **kwargs)
                completion_path = (
                    store._fence_path / f"{completion.record_sha256}.json"
                )
                fail_completion_directory = True
                return completion

            with (
                patch(
                    "decision_os.companion.broker_control._complete_cas_intent",
                    side_effect=mark_completion,
                ),
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_exact_completion_directory_fsync,
                ),
            ):
                with self.assertRaisesRegex(OSError, "terminal CAS directory"):
                    scenario.apply()

            restarted = scenario.restarted_store()
            with self.assertRaises(BrokerControlError):
                restarted.require_active(current)
            recovery_directory_fsyncs = 0

            def observe_recovery_fsync(descriptor: int) -> None:
                nonlocal recovery_directory_fsyncs
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    recovery_directory_fsyncs += 1
                original_fsync(descriptor)

            with patch(
                "decision_os.companion.broker_control.os.fsync",
                side_effect=observe_recovery_fsync,
            ):
                self.assertEqual(
                    ReconciliationOutcome.APPLIED,
                    scenario.recover(store=restarted),
                )
            self.assertGreaterEqual(recovery_directory_fsyncs, 1)
            self.assertEqual(
                ControlDomainState.ABANDONED,
                restarted.load_required().state,
            )

    def test_terminal_transition_refreshes_visible_completion_durability(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            current = scenario.current
            store = scenario.store
            original_fsync = os.fsync
            fail_completion_directory = False
            completion_path: Path | None = None

            def fail_exact_completion_directory_fsync(descriptor: int) -> None:
                nonlocal fail_completion_directory
                if (
                    fail_completion_directory
                    and completion_path is not None
                    and completion_path.exists()
                    and stat.S_ISDIR(os.fstat(descriptor).st_mode)
                ):
                    fail_completion_directory = False
                    raise OSError("simulated terminal CAS directory fsync")
                original_fsync(descriptor)

            original_complete = broker_control._complete_cas_intent

            def mark_completion(*args: Any, **kwargs: Any) -> Any:
                nonlocal completion_path, fail_completion_directory
                completion = original_complete(*args, **kwargs)
                completion_path = (
                    store._fence_path / f"{completion.record_sha256}.json"
                )
                fail_completion_directory = True
                return completion

            with (
                patch(
                    "decision_os.companion.broker_control._complete_cas_intent",
                    side_effect=mark_completion,
                ),
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_exact_completion_directory_fsync,
                ),
                self.assertRaisesRegex(OSError, "terminal CAS directory"),
            ):
                scenario.apply()

            restarted = scenario.restarted_store()
            refreshed_directories: list[Path] = []
            original_refresh = ControlDomainStore._fsync_directory

            def observe_refresh(directory: Path) -> None:
                refreshed_directories.append(directory)
                original_refresh(directory)

            with patch.object(
                ControlDomainStore,
                "_fsync_directory",
                side_effect=observe_refresh,
            ):
                abandoned = restarted.transition(
                    current,
                    ControlDomainState.ABANDONED,
                )

            self.assertIn(restarted._fence_path, refreshed_directories)
            self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)
            self.assertEqual(abandoned, restarted.load_required())

    def test_each_cas_consumes_old_domain_without_restoring_authority(self) -> None:
        for label, content, expected in (
            ("prior", b"exact prior\n", ReconciliationOutcome.NOT_APPLIED),
            ("post", b"exact post\n", ReconciliationOutcome.APPLIED),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                scenario = CanonicalCASScenario(Path(temporary))
                store = scenario.store
                current = scenario.current
                initial = scenario.initial

                if expected is ReconciliationOutcome.APPLIED:
                    outcome = scenario.apply()
                else:
                    scenario.leave_pending()
                    scenario.set_target(content)
                    outcome = scenario.recover()

                self.assertEqual(expected, outcome)
                with self.assertRaises(AuthorityRejectedError):
                    store.require_active(current)
                abandoned = store.load_required()
                self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)
                journal = store._journal_records_unlocked()
                self.assertEqual(3, len(journal))
                self.assertEqual(initial, journal[0])
                self.assertEqual(ControlDomainState.UNCERTAIN, journal[1].state)
                self.assertEqual(
                    journal[1].record_sha256,
                    abandoned.predecessor_record_sha256,
                )

    def test_unprovable_cas_durably_marks_domain_uncertain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            initial = scenario.initial

            scenario.set_target(b"neither\n")
            outcome = scenario.apply()

            uncertain = store.load_required()
            self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
            self.assertEqual(ControlDomainState.UNCERTAIN, uncertain.state)
            self.assertEqual(initial.record_sha256, uncertain.predecessor_record_sha256)
            with self.assertRaises(AuthorityRejectedError):
                scenario.recover()
            self.assertEqual(ControlDomainState.UNCERTAIN, store.load_required().state)

    def test_uncertain_persistence_failure_never_reopens_active_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            current = scenario.current
            attempt = Mock()
            original_mark = store._mark_pending_cas_uncertain_unlocked

            def lose_uncertain_response(current_record: Any) -> None:
                original_mark(current_record)
                raise OSError("injected uncertain record fsync failure")

            with (
                patch.object(
                    store,
                    "_mark_pending_cas_uncertain_unlocked",
                    side_effect=lose_uncertain_response,
                ),
                patch.object(broker_apply, "_attempt_live", attempt),
            ):
                with self.assertRaisesRegex(OSError, "uncertain record"):
                    scenario.apply()

            attempt.assert_not_called()

            with self.assertRaises(AuthorityRejectedError):
                scenario.restarted_store().require_active(current)
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                scenario.recover(store=scenario.restarted_store()),
            )
            self.assertEqual(
                ControlDomainState.ABANDONED,
                scenario.restarted_store().load_required().state,
            )

    def test_journal_ahead_repair_refreshes_directory_before_head_promotion(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            original_append = store._append_control_record_unlocked
            original_fsync = os.fsync
            attempt = Mock()
            failed = False

            def append_with_uncertain_directory_failure(
                record: ControlDomainRecord,
            ) -> None:
                nonlocal failed
                if record.state is not ControlDomainState.UNCERTAIN:
                    original_append(record)
                    return
                record_path = store._journal_path / store._record_filename(record)

                def fail_directory_fsync(descriptor: int) -> None:
                    nonlocal failed
                    if (
                        not failed
                        and record_path.exists()
                        and stat.S_ISDIR(os.fstat(descriptor).st_mode)
                    ):
                        failed = True
                        raise OSError("simulated uncertain journal directory fsync")
                    original_fsync(descriptor)

                with patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_directory_fsync,
                ):
                    original_append(record)

            with (
                patch.object(
                    store,
                    "_append_control_record_unlocked",
                    side_effect=append_with_uncertain_directory_failure,
                ),
                patch.object(broker_apply, "_attempt_live", attempt),
                self.assertRaisesRegex(OSError, "uncertain journal directory"),
            ):
                scenario.apply()

            self.assertTrue(failed)
            attempt.assert_not_called()
            restarted = scenario.restarted_store()
            original_refresh = ControlDomainStore._fsync_directory
            original_replace = restarted._replace_head_unlocked
            recovery_events: list[str] = []

            def observe_refresh(directory: Path) -> None:
                if directory == restarted._journal_path:
                    recovery_events.append("journal-directory-fsync")
                original_refresh(directory)

            def crash_after_head_repair(record: ControlDomainRecord) -> None:
                recovery_events.append("head-promotion")
                original_replace(record)
                raise RuntimeError("simulated crash after head promotion")

            with (
                patch.object(
                    ControlDomainStore,
                    "_fsync_directory",
                    side_effect=observe_refresh,
                ),
                patch.object(
                    restarted,
                    "_replace_head_unlocked",
                    side_effect=crash_after_head_repair,
                ),
                self.assertRaisesRegex(RuntimeError, "after head promotion"),
            ):
                scenario.recover(store=restarted)

            self.assertIn("journal-directory-fsync", recovery_events)
            self.assertLess(
                recovery_events.index("journal-directory-fsync"),
                recovery_events.index("head-promotion"),
            )
            self.assertEqual(
                ControlDomainState.UNCERTAIN,
                restarted.load_required().state,
            )
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                scenario.recover(store=scenario.restarted_store()),
            )

    def test_intent_failure_occurs_before_observation_is_consumed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            current = scenario.current
            store._fence_path.mkdir()
            attempt = Mock()
            original_fsync = os.fsync
            original_new_intent = broker_control._new_cas_intent
            publishing_intent = False

            def mark_intent(*args: Any, **kwargs: Any) -> Any:
                nonlocal publishing_intent
                intent = original_new_intent(*args, **kwargs)
                publishing_intent = True
                return intent

            def fail_intent_file_fsync(descriptor: int) -> None:
                if publishing_intent and stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise OSError("injected intent fsync failure")
                original_fsync(descriptor)

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_intent_file_fsync,
                ),
                patch(
                    "decision_os.companion.broker_control._new_cas_intent",
                    side_effect=mark_intent,
                ),
                patch.object(broker_apply, "_attempt_live", attempt),
            ):
                with self.assertRaisesRegex(OSError, "intent fsync"):
                    scenario.apply()

            attempt.assert_not_called()
            self.assertEqual(
                current,
                scenario.restarted_store().require_active(current).activation,
            )

    def test_intent_directory_fsync_failure_is_restart_reconcilable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            current = scenario.current
            store = scenario.store
            store._fence_path.mkdir()
            attempt = Mock()
            original_fsync = os.fsync
            original_append = store._append_cas_fence_unlocked
            failed = False
            intent_path: Path | None = None

            def fail_directory_fsync(descriptor: int) -> None:
                nonlocal failed
                if (
                    not failed
                    and intent_path is not None
                    and intent_path.exists()
                    and stat.S_ISDIR(os.fstat(descriptor).st_mode)
                ):
                    failed = True
                    raise OSError("simulated intent directory fsync")
                original_fsync(descriptor)

            def append_with_intent_fsync_failure(fence: Any) -> None:
                nonlocal intent_path
                if fence.kind != "INTENT":
                    original_append(fence)
                    return
                intent_path = store._fence_path / f"{fence.record_sha256}.json"
                with patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_directory_fsync,
                ):
                    original_append(fence)

            with (
                patch.object(
                    store,
                    "_append_cas_fence_unlocked",
                    side_effect=append_with_intent_fsync_failure,
                ),
                patch.object(broker_apply, "_attempt_live", attempt),
            ):
                with self.assertRaisesRegex(OSError, "intent directory"):
                    scenario.apply()

            attempt.assert_not_called()

            with self.assertRaises(ControlRecordIntegrityError):
                scenario.restarted_store().require_active(current)
            restarted = scenario.restarted_store()
            original_refresh = ControlDomainStore._fsync_directory
            original_mark = restarted._mark_pending_cas_uncertain_unlocked
            recovery_events: list[str] = []

            def observe_refresh(directory: Path) -> None:
                if directory == restarted._fence_path:
                    recovery_events.append("fence-directory-fsync")
                original_refresh(directory)

            def crash_after_uncertain_mark(
                current_record: ControlDomainRecord,
            ) -> ControlDomainRecord:
                recovery_events.append("uncertain-mark")
                original_mark(current_record)
                raise RuntimeError("simulated crash after uncertain mark")

            with (
                patch.object(
                    ControlDomainStore,
                    "_fsync_directory",
                    side_effect=observe_refresh,
                ),
                patch.object(
                    restarted,
                    "_mark_pending_cas_uncertain_unlocked",
                    side_effect=crash_after_uncertain_mark,
                ),
                self.assertRaisesRegex(RuntimeError, "after uncertain mark"),
            ):
                scenario.recover(store=restarted)
            self.assertIn("fence-directory-fsync", recovery_events)
            self.assertLess(
                recovery_events.index("fence-directory-fsync"),
                recovery_events.index("uncertain-mark"),
            )
            self.assertEqual(
                ControlDomainState.UNCERTAIN,
                restarted.load_required().state,
            )
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                scenario.recover(store=scenario.restarted_store()),
            )
            self.assertEqual(
                ControlDomainState.ABANDONED,
                scenario.restarted_store().load_required().state,
            )

    def test_applied_evidence_cannot_restore_an_uncertain_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            current = scenario.current
            decision = scenario.decision
            store.transition(current, ControlDomainState.UNCERTAIN)

            self.assertEqual(
                ReconciliationOutcome.APPLIED,
                reconcile_mutation(
                    decision,
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                ),
            )
            with self.assertRaises(AuthorityRejectedError):
                scenario.recover()
            self.assertEqual(ControlDomainState.UNCERTAIN, store.load_required().state)

    def test_mutation_contract_rejects_forbidden_operations_and_paths(self) -> None:
        current = activation()
        cases = (
            {"operation": "DELETE"},
            {"relative_path": ".git/config"},
            {"relative_path": "../outside.txt"},
            {"relative_path": "/absolute.txt"},
            {"relative_path": "two//segments.txt"},
            {"relative_path": "directory/"},
            {"relative_path": "ambiguous\nname.txt"},
            {"relative_path": "windows\\separator.txt"},
            {"relative_path": f"{'x' * 4097}.txt"},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(MutationDecisionError):
                    replace_decision(current, **overrides)

    def test_mutation_contract_requires_full_bytes_and_matching_post_hash(self) -> None:
        current = activation()
        with self.assertRaises(MutationDecisionError):
            replace_decision(
                current,
                target_bytes="not bytes",
            )
        with self.assertRaises(MutationDecisionError):
            replace_decision(
                current,
                expected_post_sha256=sha256(b"different"),
            )
        with self.assertRaises(MutationDecisionError):
            create_decision(
                current,
                expected_prior_sha256=sha256(b"unexpected prior"),
            )
        with self.assertRaises(MutationDecisionError):
            replace_decision(
                current,
                prior=b"same",
                post=b"same",
            )

    def test_mutation_and_observation_scalars_require_exact_types(self) -> None:
        current = activation()
        cases = (
            {"operation": EqualitySpoofStr("REPLACE")},
            {"operation": EqualitySpoofStr("DELETE")},
            {"relative_path": EqualitySpoofStr("bounded/target.txt")},
            {"target_bytes": EqualitySpoofBytes(b"exact post\n")},
            {
                "expected_prior_sha256": EqualitySpoofStr(
                    sha256(b"exact prior\n")
                )
            },
            {
                "expected_post_sha256": EqualitySpoofStr(
                    sha256(b"exact post\n")
                )
            },
        )
        for overrides in cases:
            with self.subTest(overrides=tuple(overrides)), self.assertRaises(
                MutationDecisionError
            ):
                replace_decision(current, **overrides)

        with self.assertRaises(MutationDecisionError):
            TargetObservation(
                EqualitySpoofStr("REGULAR"),
                b"exact post\n",
            )
        with self.assertRaises(MutationDecisionError):
            TargetObservation(
                TargetKind.REGULAR,
                EqualitySpoofBytes(b"exact post\n"),
            )

    def test_state_equality_spoof_cannot_request_a_transition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            store.activate_initial(current)

            with self.assertRaises(ControlDomainTransitionError):
                store.transition(
                    current,
                    EqualitySpoofStr("UNCERTAIN"),
                )

            self.assertEqual(
                ControlDomainState.ACTIVE,
                store.require_active(current).state,
            )

    def test_unregistered_exact_enum_objects_are_rejected(self) -> None:
        forged_operation = forged_string_enum(
            MutationOperation,
            MutationOperation.REPLACE.value,
            MutationOperation.REPLACE.value,
        )
        forged_kind = forged_string_enum(
            TargetKind,
            TargetKind.ABSENT.value,
            TargetKind.ABSENT.value,
        )
        forged_state = forged_string_enum(
            ControlDomainState,
            ControlDomainState.UNCERTAIN.value,
            ControlDomainState.ACTIVE.value,
        )
        self.assertIs(type(forged_operation), MutationOperation)
        self.assertEqual(MutationOperation.REPLACE, forged_operation)
        self.assertIsNot(MutationOperation.REPLACE, forged_operation)
        self.assertIs(type(forged_kind), TargetKind)
        self.assertEqual(TargetKind.ABSENT, forged_kind)
        self.assertIsNot(TargetKind.ABSENT, forged_kind)
        self.assertIs(type(forged_state), ControlDomainState)
        self.assertEqual(ControlDomainState.UNCERTAIN, forged_state)
        self.assertIsNot(ControlDomainState.UNCERTAIN, forged_state)

        with self.assertRaises(MutationDecisionError):
            replace_decision(activation(), operation=forged_operation)
        with self.assertRaises(MutationDecisionError):
            TargetObservation(forged_kind)

        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            initial = store.activate_initial(current)
            with self.assertRaises(ControlDomainTransitionError):
                store.transition(current, forged_state)
            self.assertEqual(initial, store.load_required())
            self.assertEqual((initial,), store._journal_records_unlocked())

    def test_unregistered_operation_cannot_resume_an_equal_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            decision = scenario.decision
            scenario.leave_pending()

            forged = replace_decision(
                scenario.current,
                proposal_acquisition_sha256=(
                    decision.proposal_acquisition_sha256
                ),
            )
            object.__setattr__(
                forged,
                "operation",
                forged_string_enum(
                    MutationOperation,
                    MutationOperation.REPLACE.value,
                    MutationOperation.REPLACE.value,
                ),
            )
            self.assertEqual(
                MutationDecision.binding_dict(decision),
                MutationDecision.binding_dict(forged),
            )

            with self.assertRaises(MutationDecisionError):
                scenario.store._snapshot_cas_decision(forged)
            self.assertEqual(
                ControlDomainState.UNCERTAIN,
                scenario.restarted_store().load_required().state,
            )
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                scenario.recover(store=scenario.restarted_store()),
            )

    def test_decision_subclass_cannot_alias_a_persisted_cas_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            current = scenario.current
            legitimate = scenario.decision
            scenario.leave_pending()

            forged = EqualitySpoofDecision(
                activation=current,
                operation=MutationOperation.REPLACE,
                relative_path="different/target.txt",
                target_bytes=b"different post\n",
                expected_prior_sha256=sha256(b"different prior\n"),
                expected_post_sha256=sha256(b"different post\n"),
            )
            object.__setattr__(
                forged,
                "alias_binding",
                MutationDecision.binding_dict(legitimate),
            )

            with self.assertRaises(MutationDecisionError):
                store._snapshot_cas_decision(forged)

            self.assertEqual(
                legitimate,
                store._reconstruct_pending_decision(),
            )
            scenario.set_target(b"exact post\n")
            self.assertEqual(
                ReconciliationOutcome.APPLIED,
                scenario.recover(store=scenario.restarted_store()),
            )

    def test_cas_uses_one_private_snapshot_if_caller_mutates_after_intent(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(
                Path(temporary),
                post=b"first post\n",
            )
            store = scenario.store
            current = scenario.current
            decision = scenario.decision
            first_binding = MutationDecision.binding_dict(decision)
            first_decision_sha256 = hash_payload(first_binding)
            attempt_entered = threading.Event()
            release_attempt = threading.Event()

            def paused_attempt(
                _parent_fd: int,
                _name: str,
                _decision: MutationDecision,
            ) -> ReconciliationOutcome:
                attempt_entered.set()
                self.assertTrue(release_attempt.wait(timeout=10))
                return ReconciliationOutcome.UNCERTAIN

            with (
                patch.object(
                    broker_apply,
                    "_attempt_live",
                    side_effect=paused_attempt,
                ),
                ThreadPoolExecutor(max_workers=1) as executor,
            ):
                future = executor.submit(scenario.apply)
                try:
                    self.assertTrue(attempt_entered.wait(timeout=10))
                    pending_journal = store._journal_records_unlocked()
                    pending_fences = store._cas_fences_unlocked(pending_journal)
                    self.assertEqual(
                        (
                            ControlDomainState.ACTIVE,
                            ControlDomainState.UNCERTAIN,
                        ),
                        tuple(record.state for record in pending_journal),
                    )
                    self.assertEqual(
                        ControlDomainState.UNCERTAIN,
                        store._read_control_record(store.path).state,
                    )
                    self.assertEqual(1, len(pending_fences))
                    self.assertEqual("INTENT", pending_fences[0].kind)
                    self.assertEqual(
                        first_decision_sha256,
                        pending_fences[0].decision_sha256,
                    )

                    object.__setattr__(decision, "target_bytes", b"second post\n")
                    object.__setattr__(
                        decision,
                        "expected_post_sha256",
                        sha256(b"second post\n"),
                    )
                finally:
                    release_attempt.set()
                self.assertEqual(
                    ReconciliationOutcome.UNCERTAIN,
                    future.result(timeout=10),
                )

            intent = next(
                json.loads(path.read_bytes())
                for path in store._fence_path.glob("*.json")
                if json.loads(path.read_bytes())["kind"] == "INTENT"
            )
            self.assertEqual(
                first_decision_sha256,
                intent["decision_sha256"],
            )
            self.assertNotEqual(
                hash_payload(MutationDecision.binding_dict(decision)),
                intent["decision_sha256"],
            )
            self.assertEqual(
                ControlDomainState.UNCERTAIN,
                store.load_required().state,
            )
            completion = next(
                json.loads(path.read_bytes())
                for path in store._fence_path.glob("*.json")
                if json.loads(path.read_bytes())["kind"] == "COMPLETE"
            )
            self.assertEqual(first_decision_sha256, completion["decision_sha256"])
            self.assertEqual(intent["record_sha256"], completion["intent_sha256"])
            self.assertEqual(
                ReconciliationOutcome.UNCERTAIN.value,
                completion["outcome"],
            )
            self.assertEqual(
                ControlDomainState.UNCERTAIN,
                store.load_required().state,
            )
            with self.assertRaises(AuthorityRejectedError):
                scenario.recover()

    def test_observation_subclass_is_rejected_before_reconciliation(self) -> None:
        decision = replace_decision(activation())
        forged = EqualitySpoofObservation(
            TargetKind.REGULAR,
            b"exact post\n",
        )

        with self.assertRaises(MutationDecisionError):
            reconcile_mutation(decision, forged)

    def test_standalone_reconciliation_rejects_wrapper_subclasses(self) -> None:
        current = activation()
        decision = replace_decision(current)
        forged_decision = EqualitySpoofDecision(
            activation=current,
            operation=MutationOperation.REPLACE,
            relative_path="bounded/target.txt",
            target_bytes=b"exact post\n",
            expected_prior_sha256=sha256(b"exact prior\n"),
            expected_post_sha256=sha256(b"exact post\n"),
        )
        object.__setattr__(
            forged_decision,
            "alias_binding",
            MutationDecision.binding_dict(decision),
        )
        forged_observation = EqualitySpoofObservation(
            TargetKind.REGULAR,
            b"exact post\n",
        )

        with self.assertRaises(MutationDecisionError):
            reconcile_mutation(
                forged_decision,
                TargetObservation(TargetKind.REGULAR, b"exact post\n"),
            )
        with self.assertRaises(MutationDecisionError):
            reconcile_mutation(decision, forged_observation)


class BrokerControlIntegrityTest(unittest.TestCase):
    def test_torn_or_hash_invalid_record_never_authorizes_or_applies(self) -> None:
        valid = broker_control._new_record(
            activation(),
            state=ControlDomainState.ACTIVE,
            journal_position=0,
            predecessor_record_sha256=None,
            retired_authority_domain_ids=(),
        ).as_dict()
        valid["record_sha256"] = "0" * 64
        for label, raw in (
            ("torn", b'{"schema":'),
            ("non-object", b"[]\n"),
            ("hash-invalid", f"{canonical_json(valid)}\n".encode("utf-8")),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "control.json"
                path.write_bytes(raw)
                store = ControlDomainStore(path)

                with self.assertRaises(ControlRecordIntegrityError):
                    store.load_required()

    def test_rehashed_impossible_state_is_still_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            store = ControlDomainStore(path)
            store.activate_initial(activation())
            value = json.loads(path.read_bytes())
            value["state"] = "ABANDONED"
            value["record_sha256"] = hash_payload(
                {
                    key: item
                    for key, item in value.items()
                    if key != "record_sha256"
                }
            )
            path.write_bytes(
                f"{canonical_json(value)}\n".encode("utf-8")
            )

            with self.assertRaises(ControlRecordIntegrityError):
                store.load_required()

    def test_rehashed_successor_cannot_reuse_retired_binding_identities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            store = ControlDomainStore(path)
            first = activation(authority_domain_id="forged-a")
            store.activate_initial(first)
            abandoned = store.transition(first, ControlDomainState.ABANDONED)
            forged_activation = replace(
                first,
                authority_domain_id="forged-b",
            )
            forged = broker_control._new_record(
                forged_activation,
                state=ControlDomainState.ACTIVE,
                journal_position=abandoned.journal_position + 1,
                predecessor_record_sha256=abandoned.record_sha256,
                retired_authority_domain_ids=(
                    abandoned.retired_authority_domain_ids
                ),
            )
            forged_path = store._journal_path / store._record_filename(forged)
            forged_path.write_bytes(
                broker_control._canonical_record_bytes(forged)
            )
            path.write_bytes(broker_control._canonical_record_bytes(forged))

            with self.assertRaises(ControlRecordIntegrityError):
                ControlDomainStore(path).load_required()
            with self.assertRaises(ControlRecordIntegrityError):
                ControlDomainStore(path).require_active(forged_activation)

    def test_torn_cas_intent_never_reconciles_or_restores_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            current = scenario.current
            store = scenario.store
            scenario.leave_pending()
            intent_path = next(store._fence_path.glob("*.json"))
            intent_path.write_bytes(b'{"torn":')

            restarted = scenario.restarted_store()
            with self.assertRaises(ControlRecordIntegrityError):
                restarted.require_active(current)
            with self.assertRaises(ControlRecordIntegrityError):
                scenario.recover(store=restarted)

    def test_orphan_cas_completion_never_becomes_applied(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            scenario = CanonicalCASScenario(Path(temporary))
            store = scenario.store
            scenario.apply()
            fence_values = {
                fence_path: json.loads(fence_path.read_bytes())
                for fence_path in store._fence_path.glob("*.json")
            }
            intent_path = next(
                fence_path
                for fence_path, value in fence_values.items()
                if value["kind"] == "INTENT"
            )
            intent_path.unlink()

            restarted = scenario.restarted_store()
            with self.assertRaises(ControlRecordIntegrityError):
                restarted.load_required()
            with self.assertRaises(ControlRecordIntegrityError):
                scenario.recover(store=restarted)

    def test_noncanonical_or_unsafe_record_identity_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "control.json"
            store = ControlDomainStore(path)
            record = store.activate_initial(activation())
            path.write_text(json.dumps(record.as_dict(), indent=2), encoding="utf-8")

            with self.assertRaises(ControlRecordIntegrityError):
                store.require_active(record.activation)

            path.unlink()
            target = root / "target.json"
            target.write_bytes(
                f"{canonical_json(record.as_dict())}\n".encode("utf-8")
            )
            path.symlink_to(target)
            with self.assertRaises(ControlRecordIntegrityError):
                store.load_required()

    def test_legacy_unfenced_active_records_are_not_broker_authority(self) -> None:
        cases = (
            ("decision-os-stage-b-continuation-v0.1", "RUN_1_ACTIVE"),
            ("decision-os-stage-b-continuation-v0.1", "RUN_1_COMPLETE"),
            ("decision-os-stage-b-continuation-v0.1", "RUN_2_ACTIVE"),
            ("decision-os-stage-b-continuation-v0.1", "COMPLETE"),
            ("decision-os-stage-c-small-compound-loop-v0.1", "RUN_1_COMPLETE"),
            ("decision-os-stage-c-small-compound-loop-v0.1", "RUN_2_ACTIVE"),
            ("decision-os-stage-c-small-compound-loop-v0.1", "RUN_2_COMPLETE"),
        )
        for legacy_schema, legacy_state in cases:
            with self.subTest(
                schema=legacy_schema,
                state=legacy_state,
            ), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "control.json"
                path.write_bytes(
                    (
                        canonical_json(
                            {
                                "schema": legacy_schema,
                                "state": legacy_state,
                                "repository_id": activation().repository_id,
                            }
                        )
                        + "\n"
                    ).encode("utf-8")
                )
                store = ControlDomainStore(path)

                with self.assertRaises(ControlRecordIntegrityError):
                    store.require_active(activation())
                with self.assertRaises(ControlRecordIntegrityError):
                    store.load_required()


if __name__ == "__main__":
    unittest.main()
