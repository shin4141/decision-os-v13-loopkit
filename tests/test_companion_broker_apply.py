from __future__ import annotations

import hashlib
import inspect
import os
from pathlib import Path
import stat
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch
from typing import Any

import decision_os.companion.broker_apply as broker_apply
from decision_os.companion.broker_apply import (
    AcquiredMutation,
    FileIdentity,
    PRODUCTION_EXCLUSIVE_WRITER_PRECONDITION,
    REPOSITORY_SLICE_ENFORCES_EXCLUSIVE_WRITER,
    acquire_mutation_decision,
    apply_protected_mutation,
    protected_root_identity,
    recover_protected_mutation,
)
from decision_os.companion.broker_control import (
    ActivationTuple,
    AuthorityRejectedError,
    BrokerControlError,
    ControlDomainState,
    ControlDomainStore,
    MutationDecision,
    MutationOperation,
    ReconciliationOutcome,
)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def activation(**overrides: Any) -> ActivationTuple:
    values: dict[str, Any] = {
        "authority_domain_id": "slice-2-authority-a",
        "repository_id": f"repo:v1:{'1' * 64}",
        "protected_repository_identity": f"protected:v1:{'2' * 64}",
        "write_principal_identity": f"principal:v1:{'3' * 64}",
        "generation_witness": 11,
    }
    values.update(overrides)
    return ActivationTuple(**values)


class BrokerApplyFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.proposals = self.root / "proposals"
        self.protected = self.root / "protected"
        self.proposals.mkdir()
        self.protected.mkdir()
        self.current = activation(
            protected_repository_identity=protected_root_identity(self.protected)
        )
        self.store = ControlDomainStore(self.root / "state" / "control.json")
        self.store.activate_initial(self.current)
        self.proposal_ordinal = 0

    def acquire(
        self,
        *,
        operation: MutationOperation,
        relative_path: str,
        proposal_bytes: bytes,
        expected_prior_sha256: str | None,
    ) -> Any:
        self.proposal_ordinal += 1
        proposal = self.proposals / f"proposal-{self.proposal_ordinal}.bin"
        proposal.write_bytes(proposal_bytes)
        return acquire_mutation_decision(
            proposal,
            activation=self.current,
            operation=operation,
            relative_path=relative_path,
            expected_prior_sha256=expected_prior_sha256,
        )

    def create_acquired(
        self,
        *,
        relative_path: str = "bounded/new.txt",
        post: bytes = b"created bytes\n",
    ) -> Any:
        return self.acquire(
            operation=MutationOperation.CREATE,
            relative_path=relative_path,
            proposal_bytes=post,
            expected_prior_sha256=None,
        )

    @staticmethod
    def leave_pending_intent() -> ReconciliationOutcome:
        raise RuntimeError("leave pending intent")

    def replace_acquired(
        self,
        *,
        relative_path: str = "bounded/target.txt",
        prior: bytes = b"exact prior\n",
        post: bytes = b"exact post\n",
        expected_prior_sha256: str | None = None,
    ) -> Any:
        return self.acquire(
            operation=MutationOperation.REPLACE,
            relative_path=relative_path,
            proposal_bytes=post,
            expected_prior_sha256=(
                sha256(prior)
                if expected_prior_sha256 is None
                else expected_prior_sha256
            ),
        )


class ProposalAcquisitionTest(BrokerApplyFixture):
    def test_mutation_path_contract_rejects_absolute_parent_git_and_dot_forms(
        self,
    ) -> None:
        proposal = self.proposals / "path-contract.bin"
        proposal.write_bytes(b"bounded bytes\n")

        for relative_path in (
            "/absolute.txt",
            "../outside.txt",
            "bounded/../outside.txt",
            "bounded/./target.txt",
            ".git/config",
            "bounded//target.txt",
        ):
            with self.subTest(relative_path=relative_path), self.assertRaises(
                BrokerControlError
            ):
                acquire_mutation_decision(
                    proposal,
                    activation=self.current,
                    operation=MutationOperation.CREATE,
                    relative_path=relative_path,
                    expected_prior_sha256=None,
                )

    def test_regular_proposal_binds_exact_descriptor_bytes_hash_and_identity(
        self,
    ) -> None:
        proposal = self.proposals / "exact.bin"
        expected = b"line one\r\nline two\n\x00tail"
        proposal.write_bytes(expected)
        metadata = proposal.stat()

        acquired = acquire_mutation_decision(
            proposal,
            activation=self.current,
            operation=MutationOperation.CREATE,
            relative_path="bounded/exact.bin",
            expected_prior_sha256=None,
        )

        self.assertEqual(expected, acquired.proposal_bytes)
        self.assertEqual(sha256(expected), acquired.proposal_sha256)
        self.assertEqual(expected, acquired.decision.target_bytes)
        self.assertEqual(sha256(expected), acquired.decision.expected_post_sha256)
        self.assertEqual(
            sha256(expected),
            acquired.decision.binding_dict()["target_bytes_sha256"],
        )
        self.assertEqual(
            acquired.decision.proposal_acquisition_sha256,
            acquired.decision.binding_dict()["proposal_acquisition_sha256"],
        )
        self.assertIsNotNone(acquired.proposal_identity)
        identity_text = repr(acquired.proposal_identity)
        self.assertIn(str(metadata.st_ino), identity_text)

    def test_caller_activation_mutation_cannot_rebind_acquired_decision(
        self,
    ) -> None:
        (self.protected / "bounded").mkdir()
        caller_activation = activation(
            protected_repository_identity=protected_root_identity(self.protected)
        )
        proposal = self.proposals / "activation-snapshot.bin"
        proposal.write_bytes(b"activation-bound bytes\n")
        acquired = acquire_mutation_decision(
            proposal,
            activation=caller_activation,
            operation=MutationOperation.CREATE,
            relative_path="bounded/activation-bound.txt",
            expected_prior_sha256=None,
        )

        object.__setattr__(
            caller_activation,
            "authority_domain_id",
            "slice-2-authority-mutated",
        )

        self.assertIsNot(caller_activation, acquired.decision.activation)
        self.assertEqual(self.current, acquired.decision.activation)
        self.assertEqual(
            ReconciliationOutcome.APPLIED,
            apply_protected_mutation(self.store, self.protected, acquired),
        )

    def test_proposal_path_swap_after_open_cannot_change_acquired_bytes(
        self,
    ) -> None:
        proposal = self.proposals / "swapped.bin"
        held = self.proposals / "opened-inode.bin"
        original = b"bytes from opened descriptor\n"
        replacement = b"later pathname replacement\n"
        proposal.write_bytes(original)
        original_open = os.open
        opened = False

        def open_then_swap(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
            nonlocal opened
            descriptor = original_open(path, flags, *args, **kwargs)
            if not opened and Path(path) == proposal:
                opened = True
                proposal.rename(held)
                proposal.write_bytes(replacement)
            return descriptor

        with patch(
            "decision_os.companion.broker_apply.os.open",
            side_effect=open_then_swap,
        ):
            acquired = acquire_mutation_decision(
                proposal,
                activation=self.current,
                operation=MutationOperation.CREATE,
                relative_path="bounded/snapshot.bin",
                expected_prior_sha256=None,
            )

        self.assertTrue(opened)
        self.assertEqual(replacement, proposal.read_bytes())
        self.assertEqual(original, held.read_bytes())
        self.assertEqual(original, acquired.proposal_bytes)
        self.assertEqual(original, acquired.decision.target_bytes)
        self.assertEqual(sha256(original), acquired.proposal_sha256)

    def test_proposal_symlink_is_rejected_without_following_it(self) -> None:
        target = self.proposals / "target.bin"
        target.write_bytes(b"untrusted target\n")
        proposal = self.proposals / "proposal-link.bin"
        proposal.symlink_to(target.name)

        with self.assertRaises(BrokerControlError):
            acquire_mutation_decision(
                proposal,
                activation=self.current,
                operation=MutationOperation.CREATE,
                relative_path="bounded/new.bin",
                expected_prior_sha256=None,
            )

    def test_proposal_directory_is_rejected(self) -> None:
        proposal = self.proposals / "directory"
        proposal.mkdir()

        with self.assertRaises(BrokerControlError):
            acquire_mutation_decision(
                proposal,
                activation=self.current,
                operation=MutationOperation.CREATE,
                relative_path="bounded/new.bin",
                expected_prior_sha256=None,
            )

    def test_proposal_hardlink_is_rejected_as_unsafe_identity(self) -> None:
        original = self.proposals / "original.bin"
        proposal = self.proposals / "hardlink.bin"
        original.write_bytes(b"multiply linked\n")
        os.link(original, proposal)
        self.assertGreater(proposal.stat().st_nlink, 1)

        with self.assertRaises(BrokerControlError):
            acquire_mutation_decision(
                proposal,
                activation=self.current,
                operation=MutationOperation.CREATE,
                relative_path="bounded/new.bin",
                expected_prior_sha256=None,
            )

    def test_oversize_proposal_is_rejected_before_a_decision_is_returned(
        self,
    ) -> None:
        proposal = self.proposals / "oversize.bin"
        proposal.write_bytes(b"x" * (broker_apply.MAX_PROPOSAL_BYTES + 1))

        with self.assertRaises(BrokerControlError):
            acquire_mutation_decision(
                proposal,
                activation=self.current,
                operation=MutationOperation.CREATE,
                relative_path="bounded/new.bin",
                expected_prior_sha256=None,
            )

    def test_live_apply_rejects_a_raw_unacquired_mutation_decision(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create_acquired()

        with self.assertRaises(BrokerControlError):
            apply_protected_mutation(
                self.store,
                self.protected,
                acquired.decision,
            )

        self.assertFalse((self.protected / "bounded" / "new.txt").exists())
        self.assertEqual(ControlDomainState.ACTIVE, self.store.load_required().state)

    def test_caller_forged_acquisition_bytes_are_revalidated_before_intent(
        self,
    ) -> None:
        (self.protected / "bounded").mkdir()
        target = self.protected / "bounded" / "new.txt"
        acquired = self.create_acquired()
        object.__setattr__(acquired, "proposal_bytes", b"forged after acquisition\n")

        with self.assertRaises(BrokerControlError):
            apply_protected_mutation(self.store, self.protected, acquired)

        self.assertFalse(target.exists())
        self.assertEqual(self.current, self.store.require_active(self.current).activation)

    def test_manually_constructed_acquisition_receipt_cannot_bypass_fd_open(
        self,
    ) -> None:
        (self.protected / "bounded").mkdir()
        target = self.protected / "bounded" / "new.txt"
        decision = MutationDecision(
            activation=self.current,
            operation=MutationOperation.CREATE,
            relative_path="bounded/new.txt",
            target_bytes=b"forged bytes\n",
            expected_prior_sha256=None,
            expected_post_sha256=sha256(b"forged bytes\n"),
            proposal_acquisition_sha256="4" * 64,
        )
        forged = object.__new__(AcquiredMutation)
        object.__setattr__(forged, "decision", decision)
        object.__setattr__(forged, "proposal_bytes", b"forged bytes\n")
        object.__setattr__(forged, "proposal_sha256", sha256(b"forged bytes\n"))
        object.__setattr__(
            forged,
            "proposal_identity",
            FileIdentity(999, 999, stat.S_IFREG | 0o600, 1, 13, 1, 1),
        )

        with self.assertRaises(BrokerControlError):
            apply_protected_mutation(self.store, self.protected, forged)

        self.assertFalse(target.exists())
        self.assertEqual(self.current, self.store.require_active(self.current).activation)


class ProtectedLiveApplyTest(BrokerApplyFixture):
    def test_arbitrary_protected_root_cannot_use_another_roots_activation(
        self,
    ) -> None:
        wrong_root = self.root / "wrong-protected"
        (wrong_root / "bounded").mkdir(parents=True)
        acquired = self.create_acquired()

        with self.assertRaises(BrokerControlError):
            apply_protected_mutation(self.store, wrong_root, acquired)

        self.assertFalse((wrong_root / "bounded" / "new.txt").exists())
        self.assertEqual(self.current, self.store.require_active(self.current).activation)

    def test_real_create_is_atomic_and_requires_exact_durable_post_readback(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        acquired = self.create_acquired(post=b"created exact bytes\n")

        outcome = apply_protected_mutation(self.store, self.protected, acquired)

        target = parent / "new.txt"
        self.assertEqual(ReconciliationOutcome.APPLIED, outcome)
        self.assertEqual(b"created exact bytes\n", target.read_bytes())
        self.assertTrue(stat.S_ISREG(target.stat().st_mode))
        self.assertEqual(1, target.stat().st_nlink)
        self.assertEqual(ControlDomainState.ABANDONED, self.store.load_required().state)

    def test_real_replace_uses_exact_prior_for_the_one_live_attempt(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        prior = b"exact prior bytes\n"
        post = b"exact intended post\n"
        target.write_bytes(prior)
        acquired = self.replace_acquired(prior=prior, post=post)

        outcome = apply_protected_mutation(self.store, self.protected, acquired)

        self.assertEqual(ReconciliationOutcome.APPLIED, outcome)
        self.assertEqual(post, target.read_bytes())
        self.assertEqual(ControlDomainState.ABANDONED, self.store.load_required().state)

    def test_wrong_prior_hash_never_mutates_and_live_never_returns_not_applied(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        observed = b"actual prior\n"
        target.write_bytes(observed)
        acquired = self.replace_acquired(
            post=b"unwritten post\n",
            expected_prior_sha256=sha256(b"different expected prior\n"),
        )

        outcome = apply_protected_mutation(self.store, self.protected, acquired)

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertNotEqual(ReconciliationOutcome.NOT_APPLIED, outcome)
        self.assertEqual(observed, target.read_bytes())
        self.assertEqual(ControlDomainState.UNCERTAIN, self.store.load_required().state)

    def test_target_symlink_fails_closed_without_mutating_referent(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        referent = parent / "referent.txt"
        referent.write_bytes(b"referent prior\n")
        target = parent / "target.txt"
        target.symlink_to(referent.name)
        acquired = self.replace_acquired(prior=b"referent prior\n")

        outcome = apply_protected_mutation(self.store, self.protected, acquired)

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertTrue(target.is_symlink())
        self.assertEqual(b"referent prior\n", referent.read_bytes())

    def test_parent_symlink_traversal_fails_closed(self) -> None:
        real_parent = self.protected / "real-parent"
        real_parent.mkdir()
        (real_parent / "target.txt").write_bytes(b"exact prior\n")
        (self.protected / "bounded").symlink_to(real_parent.name)
        acquired = self.replace_acquired()

        outcome = apply_protected_mutation(
            self.store,
            self.protected,
            acquired,
        )

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertEqual(
            b"exact prior\n",
            (real_parent / "target.txt").read_bytes(),
        )
        self.assertEqual(
            ControlDomainState.UNCERTAIN,
            self.store.load_required().state,
        )

    def test_protected_root_path_swap_after_open_stays_bound_to_opened_root(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        (parent / "target.txt").write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()
        opened_root = self.root / "protected-opened"
        replacement_sentinel = b"replacement root sentinel\n"
        original_open = os.open
        swapped = False

        def open_then_swap_root(
            path: Any,
            flags: int,
            *args: Any,
            **kwargs: Any,
        ) -> int:
            nonlocal swapped
            descriptor = original_open(path, flags, *args, **kwargs)
            if (
                not swapped
                and Path(os.fspath(path)) == self.protected
                and flags & os.O_DIRECTORY
            ):
                swapped = True
                self.protected.rename(opened_root)
                replacement_parent = self.protected / "bounded"
                replacement_parent.mkdir(parents=True)
                (replacement_parent / "target.txt").write_bytes(
                    replacement_sentinel
                )
            return descriptor

        with patch(
            "decision_os.companion.broker_apply.os.open",
            side_effect=open_then_swap_root,
        ):
            outcome = apply_protected_mutation(
                self.store,
                self.protected,
                acquired,
            )

        self.assertTrue(swapped)
        self.assertEqual(ReconciliationOutcome.APPLIED, outcome)
        self.assertEqual(
            b"exact post\n",
            (opened_root / "bounded" / "target.txt").read_bytes(),
        )
        self.assertEqual(
            replacement_sentinel,
            (self.protected / "bounded" / "target.txt").read_bytes(),
        )

    def test_target_hardlink_fails_closed_without_breaking_either_link(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        alias = parent / "alias.txt"
        target.write_bytes(b"exact prior\n")
        os.link(target, alias)
        acquired = self.replace_acquired()

        outcome = apply_protected_mutation(self.store, self.protected, acquired)

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertEqual(b"exact prior\n", target.read_bytes())
        self.assertEqual(b"exact prior\n", alias.read_bytes())
        self.assertEqual(2, target.stat().st_nlink)

    def test_target_directory_is_ambiguous_and_never_replaced(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.mkdir()
        (target / "sentinel").write_bytes(b"directory sentinel\n")
        acquired = self.replace_acquired()

        outcome = apply_protected_mutation(self.store, self.protected, acquired)

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertTrue(target.is_dir())
        self.assertEqual(
            b"directory sentinel\n",
            (target / "sentinel").read_bytes(),
        )

    def test_target_inode_rebound_after_open_is_detected_before_publication(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()
        original_open = os.open
        original_unlink = os.unlink
        rebound = False
        sentinel = b"replacement inode sentinel\n"

        def open_then_rebind(
            path: Any,
            flags: int,
            *args: Any,
            **kwargs: Any,
        ) -> int:
            nonlocal rebound
            descriptor = original_open(path, flags, *args, **kwargs)
            if not rebound and Path(os.fspath(path)).name == target.name:
                rebound = True
                directory_fd = kwargs.get("dir_fd")
                if directory_fd is None:
                    original_unlink(target)
                    replacement_fd = original_open(
                        target,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                        0o600,
                    )
                else:
                    original_unlink(path, dir_fd=directory_fd)
                    replacement_fd = original_open(
                        path,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                        0o600,
                        dir_fd=directory_fd,
                    )
                try:
                    os.write(replacement_fd, sentinel)
                finally:
                    os.close(replacement_fd)
            return descriptor

        with patch(
            "decision_os.companion.broker_apply.os.open",
            side_effect=open_then_rebind,
        ):
            outcome = apply_protected_mutation(
                self.store,
                self.protected,
                acquired,
            )

        self.assertTrue(rebound)
        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertEqual(sentinel, target.read_bytes())
        self.assertEqual(
            ControlDomainState.UNCERTAIN,
            self.store.load_required().state,
        )

    def test_failure_before_intent_durability_leaves_target_and_authority_free(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()

        with (
            patch.object(
                self.store,
                "_execute_live_cas",
                side_effect=OSError("injected pre-intent failure"),
            ),
            patch("decision_os.companion.broker_apply._observe_target") as observe,
            self.assertRaisesRegex(OSError, "pre-intent"),
        ):
            apply_protected_mutation(self.store, self.protected, acquired)

        observe.assert_not_called()
        self.assertEqual(b"exact prior\n", target.read_bytes())
        self.assertEqual(self.current, self.store.require_active(self.current).activation)

    def test_failure_after_intent_before_mutation_recovers_exact_prior_only(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()

        with (
            patch(
                "decision_os.companion.broker_apply._observe_target",
                side_effect=OSError("injected after-intent failure"),
            ),
            self.assertRaisesRegex(OSError, "after-intent"),
        ):
            apply_protected_mutation(self.store, self.protected, acquired)

        self.assertEqual(b"exact prior\n", target.read_bytes())
        with self.assertRaises(AuthorityRejectedError):
            self.store.require_active(self.current)
        self.assertEqual(
            ReconciliationOutcome.NOT_APPLIED,
            recover_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
                acquired.decision,
            ),
        )

    def test_replace_execute_then_raise_is_never_retried_and_recovers_post(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()
        original_replace = os.replace
        original_observe = broker_apply._observe_target
        original_fsync_parent = broker_apply._fsync_parent
        replace_calls = 0
        recovery_proof: list[str] = []

        def execute_then_raise(source: Any, destination: Any, **kwargs: Any) -> None:
            nonlocal replace_calls
            original_replace(source, destination, **kwargs)
            # Patching the module-level ``os`` object also observes the control
            # store's durable record publications.  Inject only at the one
            # protected target publication, never at an earlier fence write.
            destination_text = os.fspath(destination)
            if destination_text in {target.name, os.fspath(target)}:
                replace_calls += 1
                raise OSError("simulated response loss after replace")

        def record_recovery_observation(*args: Any, **kwargs: Any) -> Any:
            recovery_proof.append("observe")
            return original_observe(*args, **kwargs)

        def record_recovery_fsync(parent_fd: int) -> None:
            recovery_proof.append("parent-fsync")
            original_fsync_parent(parent_fd)

        with (
            patch(
                "decision_os.companion.broker_apply.os.replace",
                side_effect=execute_then_raise,
            ),
            self.assertRaisesRegex(OSError, "response loss"),
        ):
            apply_protected_mutation(self.store, self.protected, acquired)

        self.assertEqual(1, replace_calls)
        self.assertEqual(b"exact post\n", target.read_bytes())
        with self.assertRaises(AuthorityRejectedError):
            apply_protected_mutation(self.store, self.protected, acquired)
        self.assertEqual(1, replace_calls)
        with (
            patch(
                "decision_os.companion.broker_apply._observe_target",
                side_effect=record_recovery_observation,
            ),
            patch(
                "decision_os.companion.broker_apply._fsync_parent",
                side_effect=record_recovery_fsync,
            ),
            patch("decision_os.companion.broker_apply._publish_create") as create,
            patch("decision_os.companion.broker_apply._publish_replace") as replace,
        ):
            recovered = recover_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
                acquired.decision,
            )

        self.assertEqual(
            ["observe", "parent-fsync", "observe"],
            recovery_proof,
        )
        self.assertEqual(ReconciliationOutcome.APPLIED, recovered)
        create.assert_not_called()
        replace.assert_not_called()

    def test_create_execute_then_raise_is_never_retried_and_recovers_post(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "new.txt"
        acquired = self.create_acquired()
        original_link = os.link
        link_calls = 0

        def execute_then_raise(source: Any, destination: Any, **kwargs: Any) -> None:
            nonlocal link_calls
            original_link(source, destination, **kwargs)
            link_calls += 1
            raise OSError("simulated response loss after link")

        with (
            patch(
                "decision_os.companion.broker_apply.os.link",
                side_effect=execute_then_raise,
            ),
            self.assertRaisesRegex(OSError, "response loss"),
        ):
            apply_protected_mutation(self.store, self.protected, acquired)

        self.assertEqual(1, link_calls)
        self.assertEqual(b"created bytes\n", target.read_bytes())
        with self.assertRaises(AuthorityRejectedError):
            apply_protected_mutation(self.store, self.protected, acquired)
        self.assertEqual(1, link_calls)
        self.assertEqual(
            ReconciliationOutcome.APPLIED,
            recover_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
                acquired.decision,
            ),
        )

    def test_publication_before_post_verification_recovers_exact_post(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()

        with (
            patch(
                "decision_os.companion.broker_apply._readback_post",
                side_effect=OSError("injected post-verification failure"),
            ),
            self.assertRaisesRegex(OSError, "post-verification"),
        ):
            apply_protected_mutation(self.store, self.protected, acquired)

        self.assertEqual(b"exact post\n", target.read_bytes())
        self.assertEqual(
            ReconciliationOutcome.APPLIED,
            recover_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
                acquired.decision,
            ),
        )

    def test_post_write_corruption_readback_mismatch_is_uncertain(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()
        original_readback = broker_apply._readback_post

        def corrupt_then_readback(*args: Any, **kwargs: Any) -> Any:
            target.write_bytes(b"corrupt post image\n")
            return original_readback(*args, **kwargs)

        with patch(
            "decision_os.companion.broker_apply._readback_post",
            side_effect=corrupt_then_readback,
        ):
            outcome = apply_protected_mutation(
                self.store,
                self.protected,
                acquired,
            )

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertEqual(b"corrupt post image\n", target.read_bytes())
        self.assertEqual(ControlDomainState.UNCERTAIN, self.store.load_required().state)

    def test_same_post_bytes_on_a_different_inode_are_not_applied(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()
        original_readback = broker_apply._readback_post

        def replace_inode_then_readback(*args: Any, **kwargs: Any) -> Any:
            target.unlink()
            target.write_bytes(b"exact post\n")
            return original_readback(*args, **kwargs)

        with patch(
            "decision_os.companion.broker_apply._readback_post",
            side_effect=replace_inode_then_readback,
        ):
            outcome = apply_protected_mutation(
                self.store,
                self.protected,
                acquired,
            )

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertEqual(b"exact post\n", target.read_bytes())
        self.assertEqual(ControlDomainState.UNCERTAIN, self.store.load_required().state)

    def test_parent_fsync_failure_in_live_and_recovery_persists_uncertain(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()

        with (
            patch(
                "decision_os.companion.broker_apply._fsync_parent",
                side_effect=OSError("injected post-publication parent fsync failure"),
            ),
            self.assertRaisesRegex(OSError, "parent fsync failure"),
        ):
            apply_protected_mutation(self.store, self.protected, acquired)

        self.assertEqual(b"exact post\n", target.read_bytes())
        with self.assertRaises(AuthorityRejectedError):
            apply_protected_mutation(self.store, self.protected, acquired)
        with (
            patch(
                "decision_os.companion.broker_apply._fsync_parent",
                side_effect=OSError("injected recovery parent fsync failure"),
            ) as recovery_fsync,
            patch("decision_os.companion.broker_apply._publish_create") as create,
            patch("decision_os.companion.broker_apply._publish_replace") as replace,
        ):
            outcome = recover_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
                acquired.decision,
            )

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertEqual(1, recovery_fsync.call_count)
        create.assert_not_called()
        replace.assert_not_called()
        self.assertEqual(ControlDomainState.UNCERTAIN, self.store.load_required().state)

    def test_same_authority_cannot_make_a_second_live_mutation(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        first = self.create_acquired(relative_path="bounded/first.txt")
        second = self.create_acquired(relative_path="bounded/second.txt")

        self.assertEqual(
            ReconciliationOutcome.APPLIED,
            apply_protected_mutation(self.store, self.protected, first),
        )
        with self.assertRaises(AuthorityRejectedError):
            apply_protected_mutation(self.store, self.protected, second)

        self.assertTrue((parent / "first.txt").is_file())
        self.assertFalse((parent / "second.txt").exists())


class ProtectedRecoveryTest(BrokerApplyFixture):
    def begin_pending_replace(
        self,
        *,
        target_bytes: bytes,
        expected_prior: bytes = b"exact prior\n",
        post: bytes = b"exact post\n",
    ) -> Any:
        parent = self.protected / "bounded"
        parent.mkdir(exist_ok=True)
        target = parent / "target.txt"
        target.write_bytes(target_bytes)
        acquired = self.replace_acquired(prior=expected_prior, post=post)
        with self.assertRaisesRegex(RuntimeError, "leave pending intent"):
            self.store._execute_live_cas(
                acquired.decision,
                self.leave_pending_intent,
            )
        return acquired

    def test_recovery_exact_prior_is_not_applied_and_never_replays(self) -> None:
        acquired = self.begin_pending_replace(target_bytes=b"exact prior\n")
        target = self.protected / "bounded" / "target.txt"

        with (
            patch("decision_os.companion.broker_apply._publish_create") as create,
            patch("decision_os.companion.broker_apply._publish_replace") as replace,
        ):
            outcome = recover_protected_mutation(
                self.store,
                self.protected,
                acquired.decision,
            )

        self.assertEqual(ReconciliationOutcome.NOT_APPLIED, outcome)
        create.assert_not_called()
        replace.assert_not_called()
        self.assertEqual(b"exact prior\n", target.read_bytes())
        self.assertEqual(ControlDomainState.ABANDONED, self.store.load_required().state)
        with self.assertRaises(AuthorityRejectedError):
            self.store.require_active(self.current)

    def test_recovery_exact_post_is_applied_without_publication(self) -> None:
        acquired = self.begin_pending_replace(target_bytes=b"exact post\n")

        with (
            patch("decision_os.companion.broker_apply._publish_create") as create,
            patch("decision_os.companion.broker_apply._publish_replace") as replace,
        ):
            outcome = recover_protected_mutation(
                self.store,
                self.protected,
                acquired.decision,
            )

        self.assertEqual(ReconciliationOutcome.APPLIED, outcome)
        create.assert_not_called()
        replace.assert_not_called()
        self.assertEqual(ControlDomainState.ABANDONED, self.store.load_required().state)

    def test_recovery_exact_post_inode_swap_after_parent_fsync_is_uncertain(
        self,
    ) -> None:
        acquired = self.begin_pending_replace(target_bytes=b"exact post\n")
        target = self.protected / "bounded" / "target.txt"
        original_inode = target.stat().st_ino
        replacement = target.with_name("recovery-replacement.tmp")
        original_fsync_parent = broker_apply._fsync_parent
        fsync_calls = 0

        def fsync_then_swap_exact_post_inode(parent_fd: int) -> None:
            nonlocal fsync_calls
            original_fsync_parent(parent_fd)
            fsync_calls += 1
            replacement.write_bytes(b"exact post\n")
            os.replace(replacement, target)

        with (
            patch(
                "decision_os.companion.broker_apply._fsync_parent",
                side_effect=fsync_then_swap_exact_post_inode,
            ),
            patch("decision_os.companion.broker_apply._publish_create") as create,
            patch("decision_os.companion.broker_apply._publish_replace") as replace,
        ):
            outcome = recover_protected_mutation(
                self.store,
                self.protected,
                acquired.decision,
            )

        self.assertEqual(1, fsync_calls)
        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        create.assert_not_called()
        replace.assert_not_called()
        self.assertEqual(b"exact post\n", target.read_bytes())
        self.assertNotEqual(original_inode, target.stat().st_ino)
        self.assertEqual(ControlDomainState.UNCERTAIN, self.store.load_required().state)

    def test_recovery_observes_private_decision_snapshot_not_mutated_caller(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        prior = b"exact prior\n"
        post = b"exact post\n"
        path_a = "bounded/path-a.txt"
        path_b = "bounded/path-b.txt"
        target_a = self.protected / path_a
        target_b = self.protected / path_b
        target_a.write_bytes(prior)
        target_b.write_bytes(post)
        acquired = self.replace_acquired(
            relative_path=path_a,
            prior=prior,
            post=post,
        )
        with self.assertRaisesRegex(RuntimeError, "leave pending intent"):
            self.store._execute_live_cas(
                acquired.decision,
                self.leave_pending_intent,
            )

        observation_entered = threading.Event()
        allow_observation = threading.Event()
        observed_paths: list[str] = []
        original_observation = broker_apply._recovery_observation

        def observe_after_caller_mutation(
            protected_root: Path,
            decision: MutationDecision,
        ) -> Any:
            # The store invokes this only after snapshotting and matching the
            # decision to the durable intent under its exclusive lock.
            observed_paths.append(decision.relative_path)
            observation_entered.set()
            self.assertTrue(allow_observation.wait(timeout=10))
            return original_observation(protected_root, decision)

        with (
            patch(
                "decision_os.companion.broker_apply._recovery_observation",
                side_effect=observe_after_caller_mutation,
            ),
            ThreadPoolExecutor(max_workers=1) as executor,
        ):
            recovery = executor.submit(
                recover_protected_mutation,
                ControlDomainStore(self.store.path),
                self.protected,
                acquired.decision,
            )
            try:
                self.assertTrue(observation_entered.wait(timeout=10))
                object.__setattr__(
                    acquired.decision,
                    "relative_path",
                    path_b,
                )
            finally:
                allow_observation.set()
            outcome = recovery.result(timeout=10)

        self.assertEqual(path_b, acquired.decision.relative_path)
        self.assertEqual([path_a], observed_paths)
        self.assertEqual(ReconciliationOutcome.NOT_APPLIED, outcome)
        self.assertEqual(prior, target_a.read_bytes())
        self.assertEqual(post, target_b.read_bytes())
        self.assertEqual(ControlDomainState.ABANDONED, self.store.load_required().state)

    def test_recovery_neither_image_is_uncertain_and_never_unlocked(self) -> None:
        acquired = self.begin_pending_replace(target_bytes=b"neither image\n")

        outcome = recover_protected_mutation(
            self.store,
            self.protected,
            acquired.decision,
        )

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertEqual(ControlDomainState.UNCERTAIN, self.store.load_required().state)
        with self.assertRaises(AuthorityRejectedError):
            self.store.require_active(self.current)
        self.assertEqual(
            ReconciliationOutcome.UNCERTAIN,
            recover_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
                acquired.decision,
            ),
        )

    def test_recovery_create_absence_is_not_applied(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        acquired = self.create_acquired()
        with self.assertRaisesRegex(RuntimeError, "leave pending intent"):
            self.store._execute_live_cas(
                acquired.decision,
                self.leave_pending_intent,
            )

        outcome = recover_protected_mutation(
            self.store,
            self.protected,
            acquired.decision,
        )

        self.assertEqual(ReconciliationOutcome.NOT_APPLIED, outcome)
        self.assertFalse((parent / "new.txt").exists())
        self.assertEqual(ControlDomainState.ABANDONED, self.store.load_required().state)

    def test_recovery_without_a_durable_intent_is_rejected(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create_acquired()

        with self.assertRaises(AuthorityRejectedError):
            recover_protected_mutation(
                self.store,
                self.protected,
                acquired.decision,
            )

        self.assertEqual(self.current, self.store.require_active(self.current).activation)

    def test_recovery_requires_the_exact_persisted_decision_binding(self) -> None:
        acquired = self.begin_pending_replace(target_bytes=b"exact prior\n")
        different = MutationDecision(
            activation=self.current,
            operation=MutationOperation.REPLACE,
            relative_path="bounded/target.txt",
            target_bytes=b"different post\n",
            expected_prior_sha256=sha256(b"exact prior\n"),
            expected_post_sha256=sha256(b"different post\n"),
        )

        with self.assertRaises(AuthorityRejectedError):
            recover_protected_mutation(
                self.store,
                self.protected,
                different,
            )

        self.assertEqual(
            ReconciliationOutcome.NOT_APPLIED,
            recover_protected_mutation(
                self.store,
                self.protected,
                acquired.decision,
            ),
        )

    def test_recovery_target_symlink_is_uncertain_without_following(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        referent = parent / "referent.txt"
        referent.write_bytes(b"exact prior\n")
        target = parent / "target.txt"
        target.symlink_to(referent.name)
        acquired = self.replace_acquired()
        with self.assertRaisesRegex(RuntimeError, "leave pending intent"):
            self.store._execute_live_cas(
                acquired.decision,
                self.leave_pending_intent,
            )

        outcome = recover_protected_mutation(
            self.store,
            self.protected,
            acquired.decision,
        )

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertTrue(target.is_symlink())
        self.assertEqual(b"exact prior\n", referent.read_bytes())

    def test_recovery_waits_until_the_one_live_attempt_leaves_control_lock(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()
        attempt_entered = threading.Event()
        allow_attempt_to_finish = threading.Event()
        recovery_returned = threading.Event()

        def held_attempt() -> ReconciliationOutcome:
            attempt_entered.set()
            self.assertTrue(allow_attempt_to_finish.wait(timeout=10))
            return ReconciliationOutcome.UNCERTAIN

        def recover() -> ReconciliationOutcome:
            try:
                return recover_protected_mutation(
                    ControlDomainStore(self.store.path),
                    self.protected,
                    acquired.decision,
                )
            finally:
                recovery_returned.set()

        with ThreadPoolExecutor(max_workers=2) as executor:
            live = executor.submit(
                self.store._execute_live_cas,
                acquired.decision,
                held_attempt,
            )
            self.assertTrue(attempt_entered.wait(timeout=10))
            recovery = executor.submit(recover)
            self.assertFalse(recovery_returned.wait(timeout=0.2))
            allow_attempt_to_finish.set()
            self.assertEqual(ReconciliationOutcome.UNCERTAIN, live.result(timeout=10))
            self.assertEqual(
                ReconciliationOutcome.UNCERTAIN,
                recovery.result(timeout=10),
            )

    def test_recovery_observes_post_only_after_response_lost_replace_unlocks(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "target.txt"
        target.write_bytes(b"exact prior\n")
        acquired = self.replace_acquired()
        replace_entered = threading.Event()
        allow_replace = threading.Event()
        recovery_observed = threading.Event()
        original_replace = os.replace
        original_recovery_observation = broker_apply._recovery_observation

        def pause_replace_then_lose_response(
            source: Any,
            destination: Any,
            **kwargs: Any,
        ) -> None:
            destination_text = os.fspath(destination)
            if destination_text not in {target.name, os.fspath(target)}:
                original_replace(source, destination, **kwargs)
                return
            replace_entered.set()
            self.assertTrue(allow_replace.wait(timeout=10))
            original_replace(source, destination, **kwargs)
            raise OSError("simulated response loss after protected replace")

        def record_recovery_observation(*args: Any, **kwargs: Any) -> Any:
            recovery_observed.set()
            return original_recovery_observation(*args, **kwargs)

        with (
            patch(
                "decision_os.companion.broker_apply.os.replace",
                side_effect=pause_replace_then_lose_response,
            ),
            patch(
                "decision_os.companion.broker_apply._recovery_observation",
                side_effect=record_recovery_observation,
            ),
            ThreadPoolExecutor(max_workers=2) as executor,
        ):
            live = executor.submit(
                apply_protected_mutation,
                self.store,
                self.protected,
                acquired,
            )
            self.assertTrue(replace_entered.wait(timeout=10))
            self.assertEqual(b"exact prior\n", target.read_bytes())
            recovery = executor.submit(
                recover_protected_mutation,
                ControlDomainStore(self.store.path),
                self.protected,
                acquired.decision,
            )
            observed_before_unlock = recovery_observed.wait(timeout=0.2)
            allow_replace.set()
            with self.assertRaisesRegex(OSError, "response loss"):
                live.result(timeout=10)
            recovered = recovery.result(timeout=10)

        self.assertFalse(observed_before_unlock)
        self.assertTrue(recovery_observed.is_set())
        self.assertEqual(b"exact post\n", target.read_bytes())
        self.assertEqual(ReconciliationOutcome.APPLIED, recovered)


class ProtectedPublicationDurabilityTest(BrokerApplyFixture):
    def test_create_publication_is_file_fsync_then_no_clobber_then_directory_fsync(
        self,
    ) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        acquired = self.create_acquired()
        original_fsync = os.fsync
        original_link = os.link
        operations: list[str] = []

        def observed_fsync(descriptor: int) -> None:
            mode = os.fstat(descriptor).st_mode
            original_fsync(descriptor)
            operations.append(
                "directory-fsync" if stat.S_ISDIR(mode) else "file-fsync"
            )

        def observed_link(source: Any, target: Any, **kwargs: Any) -> None:
            original_link(source, target, **kwargs)
            operations.append("create-publish")

        with (
            patch(
                "decision_os.companion.broker_apply.os.fsync",
                side_effect=observed_fsync,
            ),
            patch(
                "decision_os.companion.broker_apply.os.link",
                side_effect=observed_link,
            ),
        ):
            outcome = apply_protected_mutation(
                self.store,
                self.protected,
                acquired,
            )

        self.assertEqual(ReconciliationOutcome.APPLIED, outcome)
        publication = operations.index("create-publish")
        self.assertEqual("file-fsync", operations[publication - 1])
        self.assertIn("directory-fsync", operations[publication + 1 :])

    def test_create_never_clobbers_a_target_appearing_at_publication(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        target = parent / "new.txt"
        acquired = self.create_acquired()
        original_link = os.link

        def race_target_into_place(source: Any, destination: Any, **kwargs: Any) -> None:
            target.write_bytes(b"concurrent sentinel\n")
            original_link(source, destination, **kwargs)

        with patch(
            "decision_os.companion.broker_apply.os.link",
            side_effect=race_target_into_place,
        ):
            outcome = apply_protected_mutation(
                self.store,
                self.protected,
                acquired,
            )

        self.assertEqual(ReconciliationOutcome.UNCERTAIN, outcome)
        self.assertEqual(b"concurrent sentinel\n", target.read_bytes())

    def test_cleanup_pathname_rebound_preserves_foreign_regular_file(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        acquired = self.create_acquired()
        original_link = os.link
        original_unlink = os.unlink
        original_open = os.open
        rebound_name: str | None = None
        sentinel = b"foreign rebound temp\n"

        def rebind_temp_after_link(
            source: Any,
            destination: Any,
            **kwargs: Any,
        ) -> None:
            nonlocal rebound_name
            original_link(source, destination, **kwargs)
            rebound_name = os.fspath(source)
            directory_fd = kwargs["src_dir_fd"]
            original_unlink(source, dir_fd=directory_fd)
            descriptor = original_open(
                source,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=directory_fd,
            )
            try:
                os.write(descriptor, sentinel)
            finally:
                os.close(descriptor)

        with patch(
            "decision_os.companion.broker_apply.os.link",
            side_effect=rebind_temp_after_link,
        ):
            outcome = apply_protected_mutation(
                self.store,
                self.protected,
                acquired,
            )

        self.assertEqual(ReconciliationOutcome.APPLIED, outcome)
        self.assertIsNotNone(rebound_name)
        assert rebound_name is not None
        self.assertEqual(sentinel, (parent / rebound_name).read_bytes())
        self.assertEqual(b"created bytes\n", (parent / "new.txt").read_bytes())

    def test_cleanup_pathname_rebound_preserves_foreign_symlink(self) -> None:
        parent = self.protected / "bounded"
        parent.mkdir()
        acquired = self.create_acquired()
        original_link = os.link
        original_unlink = os.unlink
        original_symlink = os.symlink
        rebound_name: str | None = None

        def rebind_temp_after_link(
            source: Any,
            destination: Any,
            **kwargs: Any,
        ) -> None:
            nonlocal rebound_name
            original_link(source, destination, **kwargs)
            rebound_name = os.fspath(source)
            directory_fd = kwargs["src_dir_fd"]
            original_unlink(source, dir_fd=directory_fd)
            original_symlink(
                "foreign-sentinel",
                source,
                dir_fd=directory_fd,
            )

        with patch(
            "decision_os.companion.broker_apply.os.link",
            side_effect=rebind_temp_after_link,
        ):
            outcome = apply_protected_mutation(
                self.store,
                self.protected,
                acquired,
            )

        self.assertEqual(ReconciliationOutcome.APPLIED, outcome)
        self.assertIsNotNone(rebound_name)
        assert rebound_name is not None
        rebound = parent / rebound_name
        self.assertTrue(rebound.is_symlink())
        self.assertEqual("foreign-sentinel", os.readlink(rebound))


class ProductionClaimBoundaryTest(unittest.TestCase):
    def test_raw_cas_callbacks_are_not_a_public_result_minting_api(self) -> None:
        public_methods = {
            name: member
            for name, member in inspect.getmembers(
                ControlDomainStore,
                predicate=inspect.isfunction,
            )
            if not name.startswith("_")
        }
        for forbidden in (
            "execute_live_cas",
            "execute_recovery_cas",
            "recover_cas",
            "reconcile_cas",
            "complete_live_cas",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, public_methods)

        callback_like = {
            "attempt",
            "callback",
            "observe",
            "observation",
            "outcome",
            "result",
        }
        for name, method in public_methods.items():
            with self.subTest(public_method=name):
                self.assertTrue(
                    callback_like.isdisjoint(inspect.signature(method).parameters),
                    f"public {name} accepts raw callback/evidence authority",
                )

    def test_repository_slice_explicitly_exposes_sole_writer_dependency(self) -> None:
        self.assertIs(False, REPOSITORY_SLICE_ENFORCES_EXCLUSIVE_WRITER)
        self.assertIs(type(PRODUCTION_EXCLUSIVE_WRITER_PRECONDITION), str)
        normalized = PRODUCTION_EXCLUSIVE_WRITER_PRECONDITION.casefold()
        for required in (
            "production precondition",
            "not enforced by slice 2",
            "sole non-root",
            "ba-10",
            "toctou",
            "equivalent filesystem authority",
            "temporary unlink",
            "check-to-syscall window",
        ):
            with self.subTest(required=required):
                self.assertIn(required, normalized)


if __name__ == "__main__":
    unittest.main()
