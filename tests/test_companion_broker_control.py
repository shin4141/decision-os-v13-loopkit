from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from typing import Any

import decision_os.companion.broker_control as broker_control
import decision_os.companion.continuation as continuation
from decision_os.acceleration.model import canonical_json, hash_payload
from decision_os.companion.broker_control import (
    ActivationTuple,
    AuthorityRejectedError,
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
from decision_os.companion.continuation import (
    ContinuationIntegrityError,
    StageBContinuationStore,
    new_record,
)
from decision_os.companion.small_compound_loop import new_stage_c_record
from tests.test_companion_continuation import stage_b_request
from tests.test_companion_small_compound_loop import stage_c_request


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def stage_b_record() -> dict[str, Any]:
    return new_record(
        stage_b_request(),
        chain_id="a" * 32,
        repository_id=f"repo:v1:{'b' * 64}",
    )


def stage_c_record() -> dict[str, Any]:
    return new_stage_c_record(
        stage_c_request(),
        chain_id="c" * 32,
        repository_id=f"repo:v1:{'d' * 64}",
    )


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

    def test_continuation_fsync_order_brackets_atomic_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "stage-b.json"
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
                    "decision_os.companion.continuation.os.fsync",
                    side_effect=observed_fsync,
                ),
                patch(
                    "decision_os.companion.continuation.os.replace",
                    side_effect=observed_replace,
                ),
            ):
                saved = StageBContinuationStore(path).save(stage_b_record())

            self.assertEqual(
                ["file-fsync", "replace", "directory-fsync"],
                operations,
            )
            self.assertEqual(saved, StageBContinuationStore(path).load_required())
            self.assertEqual(0o600, path.stat().st_mode & 0o777)

    def test_continuation_failure_prefixes_preserve_prior_or_exact_post(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "stage-b.json"
            store = StageBContinuationStore(path)
            first = store.save(stage_b_record())
            prior_bytes = path.read_bytes()
            second = stage_b_record()
            second["chain_id"] = "d" * 32

            with patch(
                "decision_os.companion.continuation.os.fsync",
                side_effect=OSError("injected file fsync failure"),
            ):
                with self.assertRaisesRegex(OSError, "file fsync"):
                    store.save(second)
            self.assertEqual(prior_bytes, path.read_bytes())
            self.assertEqual(first, store.load_required())

            with patch(
                "decision_os.companion.continuation.os.replace",
                side_effect=OSError("injected replace failure"),
            ):
                with self.assertRaisesRegex(OSError, "replace failure"):
                    store.save(second)
            self.assertEqual(prior_bytes, path.read_bytes())
            self.assertEqual(first, store.load_required())

            original_fsync = os.fsync

            def fail_directory_fsync(descriptor: int) -> None:
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    raise OSError("injected directory fsync failure")
                original_fsync(descriptor)

            with patch(
                "decision_os.companion.continuation.os.fsync",
                side_effect=fail_directory_fsync,
            ):
                with self.assertRaisesRegex(OSError, "directory fsync"):
                    store.save(second)
            published = store.load_required()
            self.assertEqual("d" * 32, published["chain_id"])
            self.assertEqual([], list(path.parent.glob(".stage-b-*.tmp")))

    def test_continuation_flushes_complete_bytes_before_file_fsync(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "stage-b.json"
            observed_file_sizes: list[int] = []
            original_fsync = os.fsync

            def observed_fsync(descriptor: int) -> None:
                status = os.fstat(descriptor)
                if stat.S_ISREG(status.st_mode):
                    observed_file_sizes.append(status.st_size)
                original_fsync(descriptor)

            with patch(
                "decision_os.companion.continuation.os.fsync",
                side_effect=observed_fsync,
            ):
                saved = StageBContinuationStore(path).save(stage_b_record())

            self.assertEqual(
                [len(f"{canonical_json(saved)}\n".encode("utf-8"))],
                observed_file_sizes,
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

    def test_journal_only_initial_domain_can_be_abandoned_but_not_used(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "control.json"
            store = ControlDomainStore(path)
            domain = activation()
            original_replace = os.replace

            def fail_head_replace(source: Any, target: Any) -> None:
                if Path(target) == path:
                    raise OSError("injected initial head replace failure")
                original_replace(source, target)

            with patch(
                "decision_os.companion.broker_control.os.replace",
                side_effect=fail_head_replace,
            ):
                with self.assertRaisesRegex(OSError, "initial head replace"):
                    store.activate_initial(domain)

            self.assertFalse(path.exists())
            with self.assertRaisesRegex(
                ControlRecordIntegrityError,
                "does not match its durable journal",
            ):
                ControlDomainStore(path).require_active(domain)

            recovered = ControlDomainStore(path)
            abandoned = recovered.transition(
                domain,
                ControlDomainState.ABANDONED,
            )
            self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)
            successor = replace(
                domain,
                authority_domain_id="authority-domain-after-initial-prefix",
            )
            self.assertEqual(
                successor,
                recovered.activate_successor(successor).activation,
            )
            self.assertEqual([], list(root.rglob(".broker-control-*.tmp")))

    def test_journal_ahead_abandonment_can_finish_after_head_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "control.json"
            store = ControlDomainStore(path)
            domain = activation()
            store.activate_initial(domain)
            original_replace = os.replace

            def fail_head_replace(source: Any, target: Any) -> None:
                if Path(target) == path:
                    raise OSError("injected abandonment head replace failure")
                original_replace(source, target)

            with patch(
                "decision_os.companion.broker_control.os.replace",
                side_effect=fail_head_replace,
            ):
                with self.assertRaisesRegex(OSError, "abandonment head replace"):
                    store.transition(domain, ControlDomainState.ABANDONED)

            with self.assertRaisesRegex(
                ControlRecordIntegrityError,
                "does not match its durable journal",
            ):
                ControlDomainStore(path).require_active(domain)

            recovered = ControlDomainStore(path)
            abandoned = recovered.transition(
                domain,
                ControlDomainState.ABANDONED,
            )
            self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)
            self.assertEqual(abandoned, recovered.load_required())
            with self.assertRaises(AuthorityRejectedError):
                recovered.require_active(domain)
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

    def test_continuation_file_fsync_failure_leaves_no_partial_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "stage-b.json"
            store = StageBContinuationStore(path)

            with patch(
                "decision_os.companion.continuation.os.fsync",
                side_effect=OSError("injected file fsync failure"),
            ):
                with self.assertRaisesRegex(OSError, "injected file fsync"):
                    store.save(stage_b_record())

            self.assertFalse(path.exists())
            self.assertEqual([], list(path.parent.glob(".stage-b-*.tmp")))

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
                if Path(target) == path:
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

    def test_real_corrupt_continuation_readback_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "stage-b.json"
            store = StageBContinuationStore(path)
            original_replace = os.replace

            def corrupt_after_replace(source: Any, target: Any, **kwargs: Any) -> None:
                original_replace(source, target, **kwargs)
                Path(target).write_bytes(b'{"torn":')

            with patch(
                "decision_os.companion.continuation.os.replace",
                side_effect=corrupt_after_replace,
            ):
                with self.assertRaises(ContinuationIntegrityError):
                    store.save(stage_b_record())

            with self.assertRaises(ContinuationIntegrityError):
                store.load_required()

    def test_continuation_readback_mismatch_never_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state" / "stage-b.json"
            store = StageBContinuationStore(path)
            different = stage_b_record()
            different["chain_id"] = "c" * 32
            different["record_sha256"] = hash_payload(
                {
                    key: value
                    for key, value in different.items()
                    if key != "record_sha256"
                }
            )

            with patch.object(store, "load_required", return_value=different):
                with self.assertRaisesRegex(
                    ContinuationIntegrityError,
                    "readback mismatches",
                ):
                    store.save(stage_b_record())


class BrokerControlAuthorityTest(unittest.TestCase):
    def test_fresh_domain_tuple_is_current_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            expected = activation()

            record = store.activate_initial(expected)

            self.assertEqual(expected, record.activation)
            self.assertEqual(record, store.require_active(expected))
            self.assertEqual((), record.retired_authority_domain_ids)

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

            self.assertEqual(current, store.load_required().activation)

    def test_equality_spoof_is_not_a_complete_activation_tuple(self) -> None:
        class EqualitySpoof:
            def __eq__(self, _other: Any) -> bool:
                return True

        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            store.activate_initial(current)
            spoof = EqualitySpoof()

            with self.assertRaises(AuthorityRejectedError):
                store.require_active(spoof)  # type: ignore[arg-type]
            with self.assertRaises(AuthorityRejectedError):
                store.transition(  # type: ignore[arg-type]
                    spoof,
                    ControlDomainState.UNCERTAIN,
                )
            self.assertEqual(current, store.require_active(current).activation)

    def test_activation_fields_reject_equality_spoofing_subclasses(self) -> None:
        class EqualityString(str):
            def __eq__(self, _other: Any) -> bool:
                return True

            __hash__ = str.__hash__

        class EqualityInteger(int):
            def __eq__(self, _other: Any) -> bool:
                return True

            __hash__ = int.__hash__

        current = activation()
        for field, spoof in (
            ("authority_domain_id", EqualityString("wrong-domain")),
            ("repository_id", EqualityString("wrong-repository")),
            (
                "protected_repository_identity",
                EqualityString("wrong-protected-repository"),
            ),
            (
                "write_principal_identity",
                EqualityString("wrong-principal"),
            ),
            ("generation_witness", EqualityInteger(999)),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                replace(current, **{field: spoof})

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
                store.authorize_cas(
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
                store.authorize_cas(
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
                store.authorize_cas(
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
                generation_witness=41,
            )

            second_process = ControlDomainStore(path)
            current = second_process.activate_successor(successor)

            self.assertEqual(41, current.activation.generation_witness)
            self.assertEqual(
                successor,
                second_process.require_active(successor).activation,
            )
            with self.assertRaises(AuthorityRejectedError):
                first_process.require_active(old)
            with self.assertRaises(AuthorityRejectedError):
                first_process.authorize_cas(
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
            second = replace(first, authority_domain_id="domain-second")
            store.activate_initial(first)
            store.transition(first, ControlDomainState.ABANDONED)
            store.activate_successor(second)
            store.transition(second, ControlDomainState.ABANDONED)

            with self.assertRaisesRegex(
                ControlDomainTransitionError,
                "retired",
            ):
                store.activate_successor(first)

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
            )
            activated = store.activate_successor(successor)
            self.assertEqual(ControlDomainState.ABANDONED, abandoned.state)
            self.assertEqual(ControlDomainState.ACTIVE, activated.state)

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
            successor = replace(current, authority_domain_id="capacity-successor")

            with patch(
                "decision_os.companion.broker_control._MAX_RETIRED_DOMAINS",
                1,
            ):
                with self.assertRaisesRegex(
                    ControlDomainTransitionError,
                    "capacity is exhausted",
                ):
                    store.activate_successor(successor)

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
                    store.activate_successor(successor)

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
                store.activate_successor(successor)

            self.assertEqual(current, store.require_active(current).activation)

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

    def test_each_cas_consumes_old_domain_without_restoring_authority(self) -> None:
        for label, content, expected in (
            ("prior", b"exact prior\n", ReconciliationOutcome.NOT_APPLIED),
            ("post", b"exact post\n", ReconciliationOutcome.APPLIED),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                store = ControlDomainStore(Path(temporary) / "control.json")
                current = activation()
                initial = store.activate_initial(current)

                outcome = store.authorize_cas(
                    replace_decision(current),
                    TargetObservation(TargetKind.REGULAR, content),
                )

                self.assertEqual(expected, outcome)
                with self.assertRaisesRegex(
                    ControlRecordIntegrityError,
                    "consumed CAS fence",
                ):
                    store.require_active(current)
                abandoned = store.transition(
                    current,
                    ControlDomainState.ABANDONED,
                )
                self.assertEqual(
                    initial.record_sha256,
                    abandoned.predecessor_record_sha256,
                )

    def test_unprovable_cas_durably_marks_domain_uncertain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            current = activation()
            initial = store.activate_initial(current)

            outcome = store.authorize_cas(
                replace_decision(current),
                TargetObservation(TargetKind.REGULAR, b"neither\n"),
            )

            uncertain = store.load_required()
            self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
            self.assertEqual(ControlDomainState.UNCERTAIN, uncertain.state)
            self.assertEqual(initial.record_sha256, uncertain.predecessor_record_sha256)
            with self.assertRaises(AuthorityRejectedError):
                store.authorize_cas(
                    replace_decision(current),
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                )

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
                    store.authorize_cas(
                        replace_decision(current),
                        TargetObservation(TargetKind.REGULAR, b"neither\n"),
                    )

            with self.assertRaisesRegex(
                ControlRecordIntegrityError,
                "consumed CAS fence",
            ):
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
                    store.authorize_cas(
                        replace_decision(current),
                        TargetObservation(TargetKind.REGULAR, b"neither\n"),
                    )

            reconcile.assert_not_called()
            self.assertEqual(
                current,
                ControlDomainStore(path).require_active(current).activation,
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
            with self.assertRaises(AuthorityRejectedError):
                store.authorize_cas(
                    decision,
                    TargetObservation(TargetKind.REGULAR, b"exact post\n"),
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

    def test_state_operation_and_observation_reject_equality_subclasses(self) -> None:
        class EqualityString(str):
            def __eq__(self, _other: Any) -> bool:
                return True

            __hash__ = str.__hash__

        current = activation()
        with self.assertRaises(MutationDecisionError):
            replace_decision(
                current,
                operation=EqualityString("DELETE"),
            )
        with self.assertRaises(MutationDecisionError):
            TargetObservation(
                EqualityString("REGULAR"),  # type: ignore[arg-type]
                b"untrusted",
            )
        with tempfile.TemporaryDirectory() as temporary:
            store = ControlDomainStore(Path(temporary) / "control.json")
            store.activate_initial(current)
            with self.assertRaises(ControlDomainTransitionError):
                store.transition(
                    current,
                    EqualityString("ABANDONED"),  # type: ignore[arg-type]
                )
            self.assertEqual(current, store.require_active(current).activation)


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
                    store.authorize_cas(
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
        for label, legacy_record in (
            ("stage-b", stage_b_record()),
            ("stage-c", stage_c_record()),
        ):
            with (
                self.subTest(label=label),
                tempfile.TemporaryDirectory() as temporary,
            ):
                path = Path(temporary) / "control.json"
                StageBContinuationStore(path).save(legacy_record)
                store = ControlDomainStore(path)

                with self.assertRaises(ControlRecordIntegrityError):
                    store.require_active(activation())
                with self.assertRaises(ControlRecordIntegrityError):
                    store.authorize_cas(
                        replace_decision(activation()),
                        TargetObservation(TargetKind.REGULAR, b"exact post\n"),
                    )


if __name__ == "__main__":
    unittest.main()
