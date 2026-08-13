from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import threading
import unittest
from unittest.mock import patch
from typing import Any

import decision_os.companion.broker_control as broker_control
from decision_os.acceleration.model import canonical_json, hash_payload
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

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=observed_fsync,
                ),
                patch(
                    "decision_os.companion.broker_control.os.replace",
                    side_effect=observed_replace,
                ),
            ):
                ControlDomainStore(path).activate_initial(activation())

            replace_indexes = [
                index
                for index, operation in enumerate(operations)
                if operation == "replace"
            ]
            self.assertEqual(2, len(replace_indexes))
            for index in replace_indexes:
                self.assertEqual("file-fsync", operations[index - 1])
                self.assertEqual("directory-fsync", operations[index + 1])
            self.assertEqual(
                [len(path.read_bytes()), len(path.read_bytes())],
                file_sizes_at_fsync,
            )

    def test_cas_fence_and_terminal_record_each_use_durable_publish(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "broker-control.json"
            store = ControlDomainStore(path)
            current = activation()
            store.activate_initial(current)
            operations: list[str] = []
            original_fsync = os.fsync
            original_replace = os.replace

            def observed_fsync(descriptor: int) -> None:
                mode = os.fstat(descriptor).st_mode
                original_fsync(descriptor)
                operations.append(
                    "directory-fsync" if stat.S_ISDIR(mode) else "file-fsync"
                )

            def observed_replace(source: Any, target: Any, **kwargs: Any) -> None:
                original_replace(source, target, **kwargs)
                operations.append("replace")

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=observed_fsync,
                ),
                patch(
                    "decision_os.companion.broker_control.os.replace",
                    side_effect=observed_replace,
                ),
            ):
                outcome = store.reconcile_cas(
                    replace_decision(current),
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                )

            self.assertEqual(ReconciliationOutcome.APPLIED, outcome)
            replace_indexes = [
                index
                for index, operation in enumerate(operations)
                if operation == "replace"
            ]
            self.assertEqual(6, len(replace_indexes))
            for index in replace_indexes:
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

    def test_control_file_fsync_failure_preserves_exact_prior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "broker-control.json"
            store = ControlDomainStore(path)
            initial = store.activate_initial(activation())
            prior_bytes = path.read_bytes()

            with patch(
                "decision_os.companion.broker_control.os.fsync",
                side_effect=OSError("injected file fsync failure"),
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

            def fail_file_then_observe_cleanup(descriptor: int) -> None:
                nonlocal cleanup_directory_fsyncs
                if stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise OSError("injected owned-temp failure")
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

            def fail_primary_and_cleanup_fsync(descriptor: int) -> None:
                if stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise OSError("primary durability failure")
                raise FileNotFoundError("cleanup directory fsync failure")

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
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
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
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
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
            directory_fsyncs = 0

            def fail_second_directory_fsync(descriptor: int) -> None:
                nonlocal directory_fsyncs
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    directory_fsyncs += 1
                    if directory_fsyncs == 2:
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
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            store.activate_initial(current)
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
                    with patch(
                        "decision_os.companion.broker_control.reconcile_mutation"
                    ) as reconcile:
                        with self.assertRaises(AuthorityRejectedError):
                            store.reconcile_cas(
                                replace_decision(mismatch),
                                TargetObservation(
                                    TargetKind.REGULAR,
                                    b"exact post\n",
                                ),
                            )
                        reconcile.assert_not_called()

            self.assertEqual(current, store.load_required().activation)
            self.assertFalse(store._fence_path.exists())

    def test_repository_identity_mismatch_fails_before_cas(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            store.activate_initial(current)
            mismatch = replace(
                current,
                repository_id=f"repo:v1:{'9' * 64}",
            )

            with self.assertRaises(AuthorityRejectedError):
                store.reconcile_cas(
                    replace_decision(mismatch),
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                )

            self.assertEqual(ControlDomainState.ACTIVE, store.load_required().state)

    def test_write_principal_identity_mismatch_fails_before_cas(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            store.activate_initial(current)
            mismatch = replace(
                current,
                write_principal_identity=f"principal:v1:{'8' * 64}",
            )

            with self.assertRaises(AuthorityRejectedError):
                store.reconcile_cas(
                    replace_decision(mismatch),
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                )

            self.assertEqual(ControlDomainState.ACTIVE, store.load_required().state)

    def test_abandoned_domain_cannot_authorize_or_reactivate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            old = activation()
            store.activate_initial(old)
            abandoned = store.transition(old, ControlDomainState.ABANDONED)

            self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)
            self.assertIn(
                old.authority_domain_id,
                abandoned.retired_authority_domain_ids,
            )
            with self.assertRaises(AuthorityRejectedError):
                store.require_active(old)
            with self.assertRaises(AuthorityRejectedError):
                store.reconcile_cas(
                    replace_decision(old),
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                )
            with self.assertRaises(ControlDomainTransitionError):
                store.transition(old, ControlDomainState.ACTIVE)

    def test_numeric_generation_reuse_does_not_restore_abandoned_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            first_process = ControlDomainStore(path)
            old = activation(generation_witness=41)
            first_process.activate_initial(old)
            first_process.transition(old, ControlDomainState.ABANDONED)
            successor = replace(
                old,
                authority_domain_id="authority-domain-successor",
                protected_repository_identity=f"protected:v1:{'7' * 64}",
                write_principal_identity=f"principal:v1:{'7' * 64}",
                generation_witness=41,
            )

            second_process = ControlDomainStore(path)
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
            with self.assertRaises(AuthorityRejectedError):
                first_process.reconcile_cas(
                    replace_decision(old),
                    TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                )

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
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            store.activate_initial(current)
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
                ControlDomainStore(store.path).require_active(current)
            with self.assertRaises(AuthorityRejectedError):
                ControlDomainStore(store.path).reconcile_cas(
                    replace_decision(current),
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                )

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
                path = Path(temporary) / "control.json"
                current = activation()
                decision = replace_decision(current)
                first_process = ControlDomainStore(path)
                first_process.activate_initial(current)

                with patch(
                    "decision_os.companion.broker_control.reconcile_mutation",
                    side_effect=RuntimeError("simulated crash after intent"),
                ):
                    with self.assertRaisesRegex(RuntimeError, "after intent"):
                        first_process.reconcile_cas(
                            decision,
                            TargetObservation(TargetKind.REGULAR, content),
                        )

                with self.assertRaises(AuthorityRejectedError):
                    ControlDomainStore(path).require_active(current)

                restarted = ControlDomainStore(path)
                outcome = restarted.reconcile_cas(
                    decision,
                    TargetObservation(TargetKind.REGULAR, content),
                )

                self.assertEqual(expected, outcome)
                self.assertEqual(terminal_state, restarted.load_required().state)
                self.assertEqual(
                    expected,
                    ControlDomainStore(path).reconcile_cas(
                        decision,
                        TargetObservation(TargetKind.REGULAR, b"changed later\n"),
                    ),
                )
                with self.assertRaises(AuthorityRejectedError):
                    restarted.require_active(current)

    def test_pending_intent_rejects_a_different_decision_before_reconciliation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            current = activation()
            original = replace_decision(current)
            store = ControlDomainStore(path)
            store.activate_initial(current)
            with patch(
                "decision_os.companion.broker_control.reconcile_mutation",
                side_effect=RuntimeError("simulated crash after intent"),
            ):
                with self.assertRaises(RuntimeError):
                    store.reconcile_cas(
                        original,
                        TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                    )

            different = replace_decision(
                current,
                post=b"different post\n",
            )
            with patch(
                "decision_os.companion.broker_control.reconcile_mutation"
            ) as reconcile:
                with self.assertRaisesRegex(
                    AuthorityRejectedError,
                    "different decision",
                ):
                    ControlDomainStore(path).reconcile_cas(
                        different,
                        TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                    )
                reconcile.assert_not_called()
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
                ControlDomainStore(path).reconcile_cas(
                    original,
                    TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                ),
            )

    def test_pending_intent_rejects_every_activation_mismatch_before_observation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            current = activation()
            decision = replace_decision(current)
            store = ControlDomainStore(path)
            store.activate_initial(current)
            with patch(
                "decision_os.companion.broker_control.reconcile_mutation",
                side_effect=RuntimeError("simulated crash after intent"),
            ):
                with self.assertRaises(RuntimeError):
                    store.reconcile_cas(
                        decision,
                        TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                    )

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
                with self.subTest(mismatch=mismatch), patch(
                    "decision_os.companion.broker_control.reconcile_mutation"
                ) as reconcile:
                    with self.assertRaises(AuthorityRejectedError):
                        ControlDomainStore(path).reconcile_cas(
                            replace_decision(mismatch),
                            TargetObservation(
                                TargetKind.REGULAR,
                                b"exact post\n",
                            ),
                        )
                    reconcile.assert_not_called()

            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                ControlDomainStore(path).reconcile_cas(
                    decision,
                    TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                ),
            )

    def test_lost_pending_intent_remains_uncertain_and_cannot_regain_authority(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            current = activation()
            decision = replace_decision(current)
            store = ControlDomainStore(path)
            store.activate_initial(current)
            with patch(
                "decision_os.companion.broker_control.reconcile_mutation",
                side_effect=RuntimeError("simulated crash after intent"),
            ):
                with self.assertRaises(RuntimeError):
                    store.reconcile_cas(
                        decision,
                        TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                    )
            for fence_path in store._fence_path.glob("*.json"):
                fence_path.unlink()
            store._fence_path.rmdir()

            restarted = ControlDomainStore(path)
            self.assertEqual(ControlDomainState.UNCERTAIN, restarted.load_required().state)
            with self.assertRaises(AuthorityRejectedError):
                restarted.require_active(current)
            self.assertEqual(
                ReconciliationOutcome.UNCERTAIN,
                restarted.reconcile_cas(
                    decision,
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                ),
            )
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
            path = Path(temporary) / "control.json"
            current = activation()
            store = ControlDomainStore(path)
            store.activate_initial(current)
            self.assertEqual(
                ReconciliationOutcome.APPLIED,
                store.reconcile_cas(
                    replace_decision(current),
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                ),
            )
            for fence in store._fence_path.iterdir():
                fence.unlink()
            store._fence_path.rmdir()

            restarted = ControlDomainStore(path)
            self.assertEqual(
                ControlDomainState.ABANDONED,
                restarted.load_required().state,
            )
            with self.assertRaises(AuthorityRejectedError):
                restarted.require_active(current)
            with self.assertRaises(AuthorityRejectedError):
                restarted.reconcile_cas(
                    replace_decision(current),
                    TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                )

    def test_completion_directory_fsync_failure_resumes_without_false_applied(
        self,
    ) -> None:
        for failure_ordinal in (4, 5, 6):
            with self.subTest(
                failure_ordinal=failure_ordinal,
            ), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "control.json"
                current = activation()
                decision = replace_decision(current)
                store = ControlDomainStore(path)
                store.activate_initial(current)
                store._fence_path.mkdir()
                original_fsync = os.fsync
                directory_fsyncs = 0

                def fail_selected_directory_fsync(descriptor: int) -> None:
                    nonlocal directory_fsyncs
                    if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                        directory_fsyncs += 1
                        if directory_fsyncs == failure_ordinal:
                            raise OSError("simulated terminal CAS directory fsync")
                    original_fsync(descriptor)

                with patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_selected_directory_fsync,
                ):
                    with self.assertRaisesRegex(OSError, "terminal CAS directory"):
                        store.reconcile_cas(
                            decision,
                            TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                        )

                restarted = ControlDomainStore(path)
                with self.assertRaises(BrokerControlError):
                    restarted.require_active(current)
                self.assertEqual(
                    ReconciliationOutcome.APPLIED,
                    restarted.reconcile_cas(
                        decision,
                        TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                    ),
                )
                self.assertEqual(
                    ControlDomainState.ABANDONED,
                    restarted.load_required().state,
                )

    def test_each_cas_consumes_old_domain_without_restoring_authority(self) -> None:
        for label, content, expected in (
            ("prior", b"exact prior\n", ReconciliationOutcome.NOT_APPLIED),
            ("post", b"exact post\n", ReconciliationOutcome.APPLIED),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                store = ControlDomainStore(Path(temporary) / "control.json")
                current = activation()
                initial = store.activate_initial(current)

                outcome = store.reconcile_cas(
                    replace_decision(current),
                    TargetObservation(TargetKind.REGULAR, content),
                )

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
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            initial = store.activate_initial(current)

            outcome = store.reconcile_cas(
                replace_decision(current),
                TargetObservation(TargetKind.REGULAR, b"neither\n"),
            )

            uncertain = store.load_required()
            self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
            self.assertEqual(ControlDomainState.UNCERTAIN, uncertain.state)
            self.assertEqual(initial.record_sha256, uncertain.predecessor_record_sha256)
            self.assertEqual(
                ReconciliationOutcome.UNCERTAIN,
                store.reconcile_cas(
                    replace_decision(current),
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                ),
            )
            self.assertEqual(ControlDomainState.UNCERTAIN, store.load_required().state)

    def test_uncertain_persistence_failure_never_reopens_active_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            store = ControlDomainStore(path)
            current = activation()
            store.activate_initial(current)
            original_fsync = os.fsync
            file_fsyncs = 0

            def fail_second_file_fsync(descriptor: int) -> None:
                nonlocal file_fsyncs
                if stat.S_ISREG(os.fstat(descriptor).st_mode):
                    file_fsyncs += 1
                    if file_fsyncs == 2:
                        raise OSError("injected uncertain record fsync failure")
                original_fsync(descriptor)

            with patch(
                "decision_os.companion.broker_control.os.fsync",
                side_effect=fail_second_file_fsync,
            ):
                with self.assertRaisesRegex(OSError, "uncertain record"):
                    store.reconcile_cas(
                        replace_decision(current),
                        TargetObservation(TargetKind.REGULAR, b"neither\n"),
                    )

            with self.assertRaises(ControlRecordIntegrityError):
                ControlDomainStore(path).require_active(current)
            abandoned = ControlDomainStore(path).transition(
                current,
                ControlDomainState.ABANDONED,
            )
            self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)

    def test_intent_failure_occurs_before_observation_is_consumed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            store = ControlDomainStore(path)
            current = activation()
            store.activate_initial(current)
            store._fence_path.mkdir()

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=OSError("injected intent fsync failure"),
                ),
                patch(
                    "decision_os.companion.broker_control.reconcile_mutation"
                ) as reconcile,
            ):
                with self.assertRaisesRegex(OSError, "intent fsync"):
                    store.reconcile_cas(
                        replace_decision(current),
                        TargetObservation(TargetKind.REGULAR, b"neither\n"),
                    )

            reconcile.assert_not_called()
            self.assertEqual(
                current,
                ControlDomainStore(path).require_active(current).activation,
            )

    def test_intent_directory_fsync_failure_is_restart_reconcilable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            current = activation()
            decision = replace_decision(current)
            store = ControlDomainStore(path)
            store.activate_initial(current)
            store._fence_path.mkdir()
            original_fsync = os.fsync
            directory_fsyncs = 0

            def fail_directory_fsync(descriptor: int) -> None:
                nonlocal directory_fsyncs
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    directory_fsyncs += 1
                    if directory_fsyncs == 3:
                        raise OSError("simulated intent directory fsync")
                original_fsync(descriptor)

            with (
                patch(
                    "decision_os.companion.broker_control.os.fsync",
                    side_effect=fail_directory_fsync,
                ),
                patch(
                    "decision_os.companion.broker_control.reconcile_mutation"
                ) as reconcile,
            ):
                with self.assertRaisesRegex(OSError, "intent directory"):
                    store.reconcile_cas(
                        decision,
                        TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                    )
                reconcile.assert_not_called()

            with self.assertRaises(AuthorityRejectedError):
                ControlDomainStore(path).require_active(current)
            self.assertEqual(
                ControlDomainState.UNCERTAIN,
                ControlDomainStore(path).load_required().state,
            )
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                ControlDomainStore(path).reconcile_cas(
                    decision,
                    TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                ),
            )

    def test_applied_evidence_cannot_restore_an_uncertain_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            decision = replace_decision(current)
            store.activate_initial(current)
            store.transition(current, ControlDomainState.UNCERTAIN)

            self.assertEqual(
                ReconciliationOutcome.APPLIED,
                reconcile_mutation(
                    decision,
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                ),
            )
            self.assertEqual(
                ReconciliationOutcome.UNCERTAIN,
                store.reconcile_cas(
                    decision,
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                ),
            )
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
            path = Path(temporary) / "control.json"
            current = activation()
            decision = replace_decision(current)
            first_process = ControlDomainStore(path)
            first_process.activate_initial(current)

            with patch(
                "decision_os.companion.broker_control.reconcile_mutation",
                side_effect=RuntimeError("simulated crash after intent"),
            ):
                with self.assertRaisesRegex(RuntimeError, "after intent"):
                    first_process.reconcile_cas(
                        decision,
                        TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                    )

            forged = replace_decision(current)
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
                ControlDomainStore(path).reconcile_cas(
                    forged,
                    TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                )
            self.assertEqual(
                ControlDomainState.UNCERTAIN,
                ControlDomainStore(path).load_required().state,
            )
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                ControlDomainStore(path).reconcile_cas(
                    decision,
                    TargetObservation(TargetKind.REGULAR, b"exact prior\n"),
                ),
            )

    def test_decision_subclass_cannot_alias_a_persisted_cas_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            store = ControlDomainStore(path)
            current = activation()
            legitimate = replace_decision(current)
            store.activate_initial(current)

            with patch(
                "decision_os.companion.broker_control.reconcile_mutation",
                side_effect=RuntimeError("simulated crash after intent"),
            ):
                with self.assertRaisesRegex(RuntimeError, "after intent"):
                    store.reconcile_cas(
                        legitimate,
                        TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                    )

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

            with patch(
                "decision_os.companion.broker_control.reconcile_mutation"
            ) as reconcile:
                with self.assertRaises(MutationDecisionError):
                    ControlDomainStore(path).reconcile_cas(
                        forged,
                        TargetObservation(
                            TargetKind.REGULAR,
                            b"different post\n",
                        ),
                    )
                reconcile.assert_not_called()

            self.assertEqual(
                ReconciliationOutcome.APPLIED,
                ControlDomainStore(path).reconcile_cas(
                    legitimate,
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                ),
            )

    def test_cas_uses_one_private_snapshot_if_caller_mutates_after_intent(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            decision = replace_decision(
                current,
                post=b"first post\n",
            )
            first_binding = MutationDecision.binding_dict(decision)
            store.activate_initial(current)
            reached_reconciliation = threading.Event()
            continue_reconciliation = threading.Event()
            original_reconcile = reconcile_mutation

            def pause_after_intent(
                snapshot: MutationDecision,
                observation: TargetObservation,
            ) -> ReconciliationOutcome:
                self.assertIsNot(snapshot, decision)
                reached_reconciliation.set()
                self.assertTrue(continue_reconciliation.wait(timeout=10))
                return original_reconcile(snapshot, observation)

            with patch(
                "decision_os.companion.broker_control.reconcile_mutation",
                side_effect=pause_after_intent,
            ), ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    store.reconcile_cas,
                    decision,
                    TargetObservation(
                        TargetKind.REGULAR,
                        b"second post\n",
                    ),
                )
                self.assertTrue(reached_reconciliation.wait(timeout=10))
                object.__setattr__(decision, "target_bytes", b"second post\n")
                object.__setattr__(
                    decision,
                    "expected_post_sha256",
                    sha256(b"second post\n"),
                )
                continue_reconciliation.set()
                outcome = future.result(timeout=10)

            self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
            intent = next(
                json.loads(path.read_bytes())
                for path in store._fence_path.glob("*.json")
                if json.loads(path.read_bytes())["kind"] == "INTENT"
            )
            self.assertEqual(
                hash_payload(first_binding),
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

    def test_observation_subclass_is_rejected_before_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            decision = replace_decision(current)
            store.activate_initial(current)
            forged = EqualitySpoofObservation(
                TargetKind.REGULAR,
                b"exact post\n",
            )

            with patch(
                "decision_os.companion.broker_control.reconcile_mutation"
            ) as reconcile:
                with self.assertRaises(MutationDecisionError):
                    store.reconcile_cas(decision, forged)
                reconcile.assert_not_called()

            self.assertEqual(
                ControlDomainState.ACTIVE,
                store.require_active(current).state,
            )
            self.assertFalse(store._fence_path.exists())

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
                    store.reconcile_cas(
                        replace_decision(activation()),
                        TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                    )

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
            path = Path(temporary) / "control.json"
            current = activation()
            decision = replace_decision(current)
            store = ControlDomainStore(path)
            store.activate_initial(current)
            with patch(
                "decision_os.companion.broker_control.reconcile_mutation",
                side_effect=RuntimeError("simulated crash"),
            ):
                with self.assertRaises(RuntimeError):
                    store.reconcile_cas(
                        decision,
                        TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                    )
            intent_path = next(store._fence_path.glob("*.json"))
            intent_path.write_bytes(b'{"torn":')

            restarted = ControlDomainStore(path)
            with self.assertRaises(ControlRecordIntegrityError):
                restarted.require_active(current)
            with self.assertRaises(ControlRecordIntegrityError):
                restarted.reconcile_cas(
                    decision,
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                )

    def test_orphan_cas_completion_never_becomes_applied(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "control.json"
            current = activation()
            store = ControlDomainStore(path)
            store.activate_initial(current)
            store.reconcile_cas(
                replace_decision(current),
                TargetObservation(TargetKind.REGULAR, b"exact post\n"),
            )
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

            restarted = ControlDomainStore(path)
            with self.assertRaises(ControlRecordIntegrityError):
                restarted.load_required()
            with self.assertRaises(ControlRecordIntegrityError):
                restarted.reconcile_cas(
                    replace_decision(current),
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                )

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
                    store.reconcile_cas(
                        replace_decision(activation()),
                        TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                    )


if __name__ == "__main__":
    unittest.main()
