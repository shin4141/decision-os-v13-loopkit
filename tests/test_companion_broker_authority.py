from __future__ import annotations

from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import hashlib
import inspect
import json
import os
from pathlib import Path
import stat
import tempfile
import time
import unittest
from unittest.mock import patch
from typing import Any

import decision_os.companion.broker_authority as broker_authority
import decision_os.companion.broker_apply as broker_apply
import decision_os.companion.broker_control as broker_control
from decision_os.companion.broker_apply import (
    BrokerApplyError,
    PRODUCTION_AUTHENTICATION_TRUST_PRECONDITION,
    PRODUCTION_CANONICAL_STORE_PRECONDITION,
    acquire_mutation_decision,
    apply_protected_mutation,
    protected_root_identity,
    recover_pending_protected_mutation,
)
from decision_os.companion.broker_authority import (
    AuthenticatedExecutionEnvelope,
    EnvelopeAuthenticationKey,
    EnvelopeAuthenticationError,
    MutationCapsuleIntegrityError,
    issue_execution_envelope,
)
from decision_os.companion.broker_control import (
    ActivationTuple,
    AuthorityRejectedError,
    ControlDomainState,
    ControlDomainStore,
    ControlRecordIntegrityError,
    MutationDecision,
    MutationOperation,
    ReconciliationOutcome,
)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class Slice3Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.protected = self.root / "protected"
        self.proposals = self.root / "proposals"
        self.protected.mkdir()
        self.proposals.mkdir()
        self.activation = ActivationTuple(
            authority_domain_id="slice-3-authority-a",
            repository_id=f"repo:v1:{'1' * 64}",
            protected_repository_identity=protected_root_identity(self.protected),
            write_principal_identity=f"principal:v1:{'3' * 64}",
            generation_witness=31,
        )
        self.key = EnvelopeAuthenticationKey(
            key_id="external-test-key",
            key_version=3,
            secret=b"external test trust material only" * 2,
        )
        self.store = ControlDomainStore(
            self.root / "state" / "control.json",
            authentication_key=self.key,
        )
        self.store.activate_initial(self.activation)
        self.ordinal = 0
        self.proposal_paths: dict[int, Path] = {}

    def acquire(
        self,
        *,
        operation: MutationOperation,
        relative_path: str,
        target_bytes: bytes,
        expected_prior_sha256: str | None,
    ) -> Any:
        self.ordinal += 1
        proposal = self.proposals / f"proposal-{self.ordinal}.bin"
        proposal.write_bytes(target_bytes)
        acquired = acquire_mutation_decision(
            proposal,
            activation=self.activation,
            operation=operation,
            relative_path=relative_path,
            expected_prior_sha256=expected_prior_sha256,
        )
        self.proposal_paths[id(acquired)] = proposal
        return acquired

    def create(self, *, path: str = "bounded/new.bin", post: bytes = b"new\n") -> Any:
        return self.acquire(
            operation=MutationOperation.CREATE,
            relative_path=path,
            target_bytes=post,
            expected_prior_sha256=None,
        )

    def replace(
        self,
        *,
        path: str = "bounded/target.bin",
        prior: bytes = b"prior\n",
        post: bytes = b"post\r\n\x00tail",
    ) -> Any:
        return self.acquire(
            operation=MutationOperation.REPLACE,
            relative_path=path,
            target_bytes=post,
            expected_prior_sha256=sha256(prior),
        )

    def envelope(
        self,
        acquired: Any,
        *,
        envelope_id: str | None = None,
        nonce: str | None = None,
        key: EnvelopeAuthenticationKey | None = None,
        issued_at: int | None = None,
        expires_at: int | None = None,
    ) -> AuthenticatedExecutionEnvelope:
        now = int(time.time()) if issued_at is None else issued_at
        return issue_execution_envelope(
            acquired.decision,
            self.store.load_required(),
            authentication_key=self.key if key is None else key,
            envelope_id=envelope_id or f"{self.ordinal + 10:032x}",
            nonce=nonce or f"{self.ordinal + 100:032x}",
            issued_at_unix=now,
            expires_at_unix=now + 60 if expires_at is None else expires_at,
            bootstrap_activation_evidence_id="bootstrap-receipt-31",
            bootstrap_activation_evidence_sha256="a" * 64,
            human_seat_authorization_evidence_id="human-seat-receipt-31",
            human_seat_authorization_evidence_sha256="b" * 64,
        )

    def apply(self, acquired: Any, envelope: Any, **kwargs: Any) -> Any:
        return apply_protected_mutation(
            self.store,
            self.protected,
            self.proposal_paths[id(acquired)],
            envelope,
            **kwargs,
        )


class AuthenticatedLiveEnvelopeTest(Slice3Fixture):
    def test_valid_exact_envelope_performs_one_live_mutation(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create(post=b"authenticated exact bytes\n")
        envelope = self.envelope(acquired)

        self.assertEqual(
            ReconciliationOutcome.APPLIED,
            self.apply(acquired, envelope),
        )
        self.assertEqual(
            b"authenticated exact bytes\n",
            (self.protected / "bounded" / "new.bin").read_bytes(),
        )
        self.assertEqual(ControlDomainState.ABANDONED, self.store.load_required().state)
        with self.assertRaises(AuthorityRejectedError):
            self.apply(acquired, envelope)

    def test_authentication_precedes_fd_acquisition_and_durable_cas_order(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create(post=b"ordered bytes\n")
        envelope = self.envelope(acquired)
        events: list[str] = []
        original_verify = self.store._verify_execution_envelope
        original_acquire = broker_apply.acquire_mutation_decision
        original_capsule = self.store._publish_capsule_unlocked
        original_append = self.store._append_cas_fence_unlocked
        original_consume = self.store._mark_pending_cas_uncertain_unlocked
        original_attempt = broker_apply._attempt_live
        original_readback = broker_apply._readback_post

        def verify(*args: Any, **kwargs: Any) -> Any:
            result = original_verify(*args, **kwargs)
            events.append("authenticate")
            return result

        def acquire(*args: Any, **kwargs: Any) -> Any:
            result = original_acquire(*args, **kwargs)
            events.append("acquire")
            return result

        def capsule(*args: Any, **kwargs: Any) -> Any:
            result = original_capsule(*args, **kwargs)
            events.append("capsule")
            return result

        def append(fence: Any) -> None:
            original_append(fence)
            events.append(fence.kind.casefold())

        def consume(*args: Any, **kwargs: Any) -> Any:
            result = original_consume(*args, **kwargs)
            events.append("consume")
            return result

        def attempt(*args: Any, **kwargs: Any) -> Any:
            events.append("mutation")
            return original_attempt(*args, **kwargs)

        def readback(*args: Any, **kwargs: Any) -> Any:
            result = original_readback(*args, **kwargs)
            events.append("post-verify")
            return result

        with (
            patch.object(self.store, "_verify_execution_envelope", side_effect=verify),
            patch(
                "decision_os.companion.broker_apply.acquire_mutation_decision",
                side_effect=acquire,
            ),
            patch.object(self.store, "_publish_capsule_unlocked", side_effect=capsule),
            patch.object(self.store, "_append_cas_fence_unlocked", side_effect=append),
            patch.object(
                self.store,
                "_mark_pending_cas_uncertain_unlocked",
                side_effect=consume,
            ),
            patch("decision_os.companion.broker_apply._attempt_live", side_effect=attempt),
            patch("decision_os.companion.broker_apply._readback_post", side_effect=readback),
        ):
            self.assertEqual(ReconciliationOutcome.APPLIED, self.apply(acquired, envelope))

        expected = (
            "authenticate",
            "authenticate",
            "acquire",
            "authenticate",
            "capsule",
            "intent",
            "consume",
            "mutation",
            "post-verify",
            "complete",
        )
        self.assertEqual(expected, tuple(events))

    def test_untrusted_store_rejects_before_fd_acquisition(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create()
        proposal, envelope = (
            self.proposal_paths[id(acquired)],
            self.envelope(acquired),
        )
        untrusted = ControlDomainStore(self.store.path)

        with (
            patch("decision_os.companion.broker_apply.acquire_mutation_decision") as acquire,
            self.assertRaises(BrokerApplyError),
        ):
            apply_protected_mutation(
                untrusted,
                self.protected,
                proposal,
                envelope,
            )
        acquire.assert_not_called()

    def test_authenticated_transaction_has_no_caller_decision_or_callback(self) -> None:
        parameters = inspect.signature(
            self.store._execute_authenticated_live_cas
        ).parameters
        self.assertEqual(
            {"envelope", "proposal_path", "protected_root"},
            set(parameters),
        )
        self.assertNotIn("attempt", parameters)
        self.assertNotIn("decision", parameters)
        self.assertNotIn("outcome", parameters)

    def test_same_bytes_from_a_substituted_proposal_inode_are_rejected(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create(post=b"same bytes\n")
        envelope = self.envelope(acquired)
        substituted = self.proposals / "substituted.bin"
        substituted.write_bytes(b"same bytes\n")

        with self.assertRaises(AuthorityRejectedError):
            apply_protected_mutation(
                self.store,
                self.protected,
                substituted,
                envelope,
            )
        self.assertFalse(self.store._fence_path.exists())
        self.assertFalse((self.protected / "bounded" / "new.bin").exists())

    def test_missing_wrong_or_modified_envelope_rejects_before_intent(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create()
        envelope = self.envelope(acquired)
        wrong_key = EnvelopeAuthenticationKey(
            key_id=self.key.key_id,
            key_version=self.key.key_version,
            secret=b"z" * 32,
        )

        with self.assertRaises(BrokerApplyError):
            apply_protected_mutation(
                self.store,
                self.protected,
                self.proposal_paths[id(acquired)],
                None,  # type: ignore[arg-type]
            )
        with self.assertRaises(BrokerApplyError):
            apply_protected_mutation(
                ControlDomainStore(
                    self.store.path,
                    authentication_key=wrong_key,
                ),
                self.protected,
                self.proposal_paths[id(acquired)],
                envelope,
            )
        modified = replace(envelope, relative_path="bounded/sibling.bin")
        with self.assertRaises(BrokerApplyError):
            self.apply(acquired, modified)

        self.assertEqual(self.activation, self.store.require_active(self.activation).activation)
        self.assertFalse(self.store._fence_path.exists())
        self.assertFalse((self.protected / "bounded" / "new.bin").exists())

    def test_self_consistent_caller_selected_key_or_store_rejects_before_acquisition(
        self,
    ) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create()
        attacker_key = EnvelopeAuthenticationKey(
            key_id="caller-selected-key",
            key_version=99,
            secret=b"caller selected untrusted material" * 2,
        )
        attacker_store = ControlDomainStore(
            self.store.path,
            authentication_key=attacker_key,
        )
        now = int(time.time())
        forged = issue_execution_envelope(
            acquired.decision,
            attacker_store.load_required(),
            authentication_key=attacker_key,
            envelope_id="9" * 32,
            nonce="a" * 32,
            issued_at_unix=now,
            expires_at_unix=now + 60,
            bootstrap_activation_evidence_id="forged-bootstrap",
            bootstrap_activation_evidence_sha256="b" * 64,
            human_seat_authorization_evidence_id="forged-seat",
            human_seat_authorization_evidence_sha256="c" * 64,
        )

        with (
            patch(
                "decision_os.companion.broker_apply.acquire_mutation_decision"
            ) as acquire,
            self.assertRaises(BrokerApplyError),
        ):
            apply_protected_mutation(
                attacker_store,
                self.protected,
                self.proposal_paths[id(acquired)],
                forged,
            )
        acquire.assert_not_called()
        self.assertFalse(self.store._fence_path.exists())
        self.assertFalse((self.protected / "bounded" / "new.bin").exists())

        parallel_store = ControlDomainStore(
            self.root / "attacker-deployment" / "state" / "control.json",
            authentication_key=attacker_key,
        )
        parallel_store.activate_initial(self.activation)
        parallel_envelope = issue_execution_envelope(
            acquired.decision,
            parallel_store.load_required(),
            authentication_key=attacker_key,
            envelope_id="d" * 32,
            nonce="e" * 32,
            issued_at_unix=now,
            expires_at_unix=now + 60,
            bootstrap_activation_evidence_id="forged-bootstrap",
            bootstrap_activation_evidence_sha256="f" * 64,
            human_seat_authorization_evidence_id="forged-seat",
            human_seat_authorization_evidence_sha256="0" * 64,
        )
        with (
            patch(
                "decision_os.companion.broker_apply.acquire_mutation_decision"
            ) as acquire,
            self.assertRaises(BrokerApplyError),
        ):
            apply_protected_mutation(
                parallel_store,
                self.protected,
                self.proposal_paths[id(acquired)],
                parallel_envelope,
            )
        acquire.assert_not_called()
        self.assertFalse((self.protected / "bounded" / "new.bin").exists())

        attacker_parent = self.root / "attacker-deployment"
        split_path_type = type(
            "SplitProtectedRootPath",
            (type(Path()),),
            {"parent": property(lambda _value: attacker_parent)},
        )
        split_root = split_path_type(self.protected)
        with (
            patch(
                "decision_os.companion.broker_apply.acquire_mutation_decision"
            ) as acquire,
            self.assertRaises(BrokerApplyError),
        ):
            apply_protected_mutation(
                parallel_store,
                split_root,
                self.proposal_paths[id(acquired)],
                parallel_envelope,
            )
        acquire.assert_not_called()
        with self.assertRaises(BrokerApplyError):
            recover_pending_protected_mutation(parallel_store, split_root)
        self.assertFalse((self.protected / "bounded" / "new.bin").exists())

        split_control_path = split_path_type(self.store.path)
        snapshotted_store = ControlDomainStore(split_control_path)
        self.assertEqual(self.store.path, snapshotted_store.path)
        self.assertEqual(
            self.store._journal_path,
            snapshotted_store._journal_path,
        )

        spliced_store = ControlDomainStore(
            parallel_store.path,
            authentication_key=attacker_key,
        )
        with self.assertRaises(AttributeError):
            spliced_store.path = self.store.path
        with self.assertRaises(AttributeError):
            self.store._authentication_key = attacker_key
        with self.assertRaises(AttributeError):
            self.store._authenticator_path = parallel_store._authenticator_path
        with self.assertRaises(AttributeError):
            spliced_store._IMMUTABLE_CONFIGURATION_FIELDS = frozenset()
        with self.assertRaises(AttributeError):
            spliced_store.path = self.store.path
        with self.assertRaises(AttributeError):
            del spliced_store.path
        with self.assertRaises(AttributeError):
            del self.store._authentication_key
        self.assertEqual(parallel_store.path, spliced_store.path)
        self.assertEqual(self.key, self.store._authentication_key)
        self.assertFalse((self.protected / "bounded" / "new.bin").exists())

    def test_deep_live_seam_cannot_bypass_canonical_store_routing(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create(post=b"deep route must reject\n")
        attacker_key = EnvelopeAuthenticationKey(
            key_id="deep-route-attacker",
            key_version=1,
            secret=b"deep route attacker material" * 2,
        )
        parallel_store = ControlDomainStore(
            self.root / "parallel-deployment" / "state" / "control.json",
            authentication_key=attacker_key,
        )
        parallel_record = parallel_store.activate_initial(self.activation)
        now = int(time.time())
        parallel_envelope = issue_execution_envelope(
            acquired.decision,
            parallel_record,
            authentication_key=attacker_key,
            envelope_id="1" * 32,
            nonce="2" * 32,
            issued_at_unix=now,
            expires_at_unix=now + 60,
            bootstrap_activation_evidence_id="attacker-bootstrap",
            bootstrap_activation_evidence_sha256="3" * 64,
            human_seat_authorization_evidence_id="attacker-seat",
            human_seat_authorization_evidence_sha256="4" * 64,
        )
        root_fd = broker_apply._open_protected_root(self.protected)
        try:
            direct = parallel_store._execute_authenticated_live_cas
            parameters = inspect.signature(direct).parameters
            arguments: dict[str, Any] = {
                "envelope": parallel_envelope,
                "proposal_path": self.proposal_paths[id(acquired)],
            }
            if "protected_root" in parameters:
                arguments["protected_root"] = self.protected
            if "root_fd" in parameters:
                arguments["root_fd"] = root_fd
            self.assertTrue(
                {"protected_root", "root_fd"}.intersection(parameters),
                "Deep live seam has no protected-root binding input.",
            )
            with self.assertRaises((BrokerApplyError, AuthorityRejectedError)):
                direct(**arguments)
        finally:
            os.close(root_fd)

        self.assertFalse(parallel_store._capsule_path.exists())
        self.assertFalse(parallel_store._fence_path.exists())
        self.assertFalse((self.protected / "bounded" / "new.bin").exists())

    def test_control_state_cannot_be_the_protected_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            protected = root / "state"
            proposals = root / "proposals"
            protected.mkdir()
            proposals.mkdir()
            key = EnvelopeAuthenticationKey(
                key_id="separation-key",
                key_version=1,
                secret=b"separation external trust material" * 2,
            )
            current = replace(
                self.activation,
                authority_domain_id="separation-domain",
                protected_repository_identity=protected_root_identity(protected),
            )
            store = ControlDomainStore(
                protected / "control.json",
                authentication_key=key,
            )
            record = store.activate_initial(current)
            proposal = proposals / "proposal.bin"
            proposal.write_bytes(b"must not overwrite authority state\n")
            acquired = acquire_mutation_decision(
                proposal,
                activation=current,
                operation=MutationOperation.CREATE,
                relative_path="bounded/new.bin",
                expected_prior_sha256=None,
            )
            now = int(time.time())
            envelope = issue_execution_envelope(
                acquired.decision,
                record,
                authentication_key=key,
                envelope_id="7" * 32,
                nonce="8" * 32,
                issued_at_unix=now,
                expires_at_unix=now + 60,
                bootstrap_activation_evidence_id="bootstrap",
                bootstrap_activation_evidence_sha256="9" * 64,
                human_seat_authorization_evidence_id="seat",
                human_seat_authorization_evidence_sha256="a" * 64,
            )

            with self.assertRaises(BrokerApplyError):
                apply_protected_mutation(store, protected, proposal, envelope)
            with self.assertRaises(BrokerApplyError):
                store._execute_authenticated_live_cas(
                    envelope,
                    proposal,
                    protected,
                )
            with self.assertRaises(BrokerApplyError):
                recover_pending_protected_mutation(store, protected)
            root_fd = broker_apply._open_protected_root(protected)
            try:
                with self.assertRaises(BrokerApplyError):
                    store._execute_pending_recovery_cas_owned(
                        protected,
                        root_fd,
                    )
            finally:
                os.close(root_fd)

            self.assertFalse((protected / "bounded" / "new.bin").exists())
            self.assertEqual(record, store.load_required())

    def test_control_state_cannot_be_beneath_the_protected_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            protected = Path(temporary) / "protected"
            control = protected / "state" / "control.json"
            protected.mkdir()
            control.parent.mkdir()

            with self.assertRaisesRegex(BrokerApplyError, "outside"):
                broker_apply._require_separate_control_directory(
                    protected,
                    control,
                )

    def test_lexical_parent_alias_cannot_select_a_different_control_store(
        self,
    ) -> None:
        (self.protected / "bounded").mkdir()
        alias_child = self.protected / "repository-artifact"
        alias_child.mkdir()
        aliased_root = Path(f"{alias_child}{os.sep}..")
        attacker_key = EnvelopeAuthenticationKey(
            key_id="lexical-route-attacker",
            key_version=1,
            secret=b"lexical route attacker material" * 2,
        )
        attacker_store = ControlDomainStore(
            alias_child / "state" / "control.json",
            authentication_key=attacker_key,
        )
        attacker_store.activate_initial(self.activation)
        acquired = self.create(post=b"lexical alias must reject\n")
        now = int(time.time())
        forged = issue_execution_envelope(
            acquired.decision,
            attacker_store.load_required(),
            authentication_key=attacker_key,
            envelope_id="5" * 32,
            nonce="6" * 32,
            issued_at_unix=now,
            expires_at_unix=now + 60,
            bootstrap_activation_evidence_id="attacker-bootstrap",
            bootstrap_activation_evidence_sha256="7" * 64,
            human_seat_authorization_evidence_id="attacker-seat",
            human_seat_authorization_evidence_sha256="8" * 64,
        )

        with self.assertRaises(BrokerApplyError):
            apply_protected_mutation(
                attacker_store,
                aliased_root,
                self.proposal_paths[id(acquired)],
                forged,
            )
        with self.assertRaises(BrokerApplyError):
            attacker_store._execute_authenticated_live_cas(
                forged,
                self.proposal_paths[id(acquired)],
                aliased_root,
            )
        self.assertFalse((self.protected / "bounded" / "new.bin").exists())

    def test_expired_and_future_envelopes_reject(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create()
        now = int(time.time())
        expired = self.envelope(
            acquired,
            issued_at=now - 60,
            expires_at=now - 1,
        )
        future = self.envelope(
            acquired,
            envelope_id="e" * 32,
            nonce="f" * 32,
            issued_at=now + 20,
            expires_at=now + 40,
        )

        for envelope in (expired, future):
            with self.subTest(envelope_id=envelope.envelope_id), self.assertRaises(
                BrokerApplyError
            ):
                self.apply(acquired, envelope)
        self.assertEqual(self.activation, self.store.require_active(self.activation).activation)

    def test_existing_blob_is_directory_fsynced_before_fresh_capsule(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create(post=b"retry exact blob bytes\n")
        first = self.envelope(acquired)
        original_fsync = ControlDomainStore._fsync_directory
        original_os_fsync = broker_control.os.fsync
        regular_fsyncs = 0

        def fail_first_publisher_directory_fsync(descriptor: int) -> None:
            nonlocal regular_fsyncs
            mode = os.fstat(descriptor).st_mode
            if stat.S_ISREG(mode):
                regular_fsyncs += 1
            if stat.S_ISDIR(mode) and regular_fsyncs == 1:
                raise OSError("injected blob directory fsync failure")
            original_os_fsync(descriptor)

        with (
            patch(
                "decision_os.companion.broker_control.os.fsync",
                side_effect=fail_first_publisher_directory_fsync,
            ),
            self.assertRaisesRegex(OSError, "blob directory fsync failure"),
        ):
            self.apply(acquired, first)

        self.assertEqual(1, len(tuple(self.store._blob_path.glob("*.blob"))))
        self.assertFalse(self.store._capsule_path.joinpath(
            f"{first.capsule_sha256}.json"
        ).exists())
        self.assertFalse(self.store._fence_path.exists())
        self.assertFalse((self.protected / "bounded" / "new.bin").exists())

        fresh = self.envelope(
            acquired,
            envelope_id="c" * 32,
            nonce="d" * 32,
        )
        fsynced: list[Path] = []

        def record_fsync(directory: Path) -> None:
            fsynced.append(directory)
            original_fsync(directory)

        with patch.object(
            ControlDomainStore,
            "_fsync_directory",
            side_effect=record_fsync,
        ):
            self.assertEqual(ReconciliationOutcome.APPLIED, self.apply(acquired, fresh))
        self.assertIn(self.store._blob_path, fsynced)

    def test_envelope_identity_and_nonce_each_have_global_one_use(self) -> None:
        for field in ("envelope_id", "nonce"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                protected = root / "protected"
                proposals = root / "proposals"
                protected.mkdir()
                proposals.mkdir()
                current = replace(
                    self.activation,
                    authority_domain_id=f"replay-{field}",
                    protected_repository_identity=protected_root_identity(protected),
                )
                store = ControlDomainStore(
                    root / "state" / "control.json",
                    authentication_key=self.key,
                )
                store.activate_initial(current)
                (protected / "bounded").mkdir()
                proposal = proposals / "proposal.bin"
                proposal.write_bytes(b"one-use bytes\n")
                acquired = acquire_mutation_decision(
                    proposal,
                    activation=current,
                    operation=MutationOperation.CREATE,
                    relative_path="bounded/new.bin",
                    expected_prior_sha256=None,
                )
                now = int(time.time())

                def signed(envelope_id: str, nonce: str) -> Any:
                    return issue_execution_envelope(
                        acquired.decision,
                        store.load_required(),
                        authentication_key=self.key,
                        envelope_id=envelope_id,
                        nonce=nonce,
                        issued_at_unix=now,
                        expires_at_unix=now + 60,
                        bootstrap_activation_evidence_id="bootstrap",
                        bootstrap_activation_evidence_sha256="1" * 64,
                        human_seat_authorization_evidence_id="seat",
                        human_seat_authorization_evidence_sha256="2" * 64,
                    )

                first = signed("3" * 32, "4" * 32)
                with (
                    patch.object(
                        broker_control,
                        "_new_cas_intent",
                        side_effect=RuntimeError("crash after capsule"),
                    ),
                    self.assertRaisesRegex(RuntimeError, "after capsule"),
                ):
                    apply_protected_mutation(store, protected, proposal, first)
                second = signed(
                    first.envelope_id if field == "envelope_id" else "5" * 32,
                    first.nonce if field == "nonce" else "6" * 32,
                )
                with self.assertRaises(AuthorityRejectedError):
                    apply_protected_mutation(store, protected, proposal, second)
                self.assertFalse(store._fence_path.exists())
                self.assertFalse((protected / "bounded" / "new.bin").exists())

    def test_concurrent_authenticated_requests_have_one_mutation_winner(self) -> None:
        (self.protected / "bounded").mkdir()
        first = self.create(path="bounded/first.bin", post=b"first\n")
        first_envelope = self.envelope(first)
        second = self.create(path="bounded/second.bin", post=b"second\n")
        second_envelope = self.envelope(
            second,
            envelope_id="7" * 32,
            nonce="8" * 32,
        )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = (
                executor.submit(self.apply, first, first_envelope),
                executor.submit(self.apply, second, second_envelope),
            )
            results: list[ReconciliationOutcome] = []
            failures: list[BaseException] = []
            for future in futures:
                try:
                    results.append(future.result(timeout=5))
                except BaseException as exc:
                    failures.append(exc)

        self.assertEqual([ReconciliationOutcome.APPLIED], results)
        self.assertEqual(1, len(failures))
        self.assertIsInstance(failures[0], AuthorityRejectedError)
        self.assertEqual(
            1,
            sum(
                path.exists()
                for path in (
                    self.protected / "bounded" / "first.bin",
                    self.protected / "bounded" / "second.bin",
                )
            ),
        )
        self.assertEqual(1, len(tuple(self.store._capsule_path.glob("*.json"))))

    def test_live_uses_owned_root_descriptor_if_caller_fd_is_rebound(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create(post=b"owned live descriptor\n")
        envelope = self.envelope(acquired)
        wrong_root = self.root / "wrong-live-root"
        (wrong_root / "bounded").mkdir(parents=True)
        original_verify = self.store._verify_execution_envelope
        calls = 0

        def rebind_caller_fd(value: Any) -> Any:
            nonlocal calls
            result = original_verify(value)
            calls += 1
            if calls == 3:
                wrong_fd = os.open(
                    wrong_root,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
                )
                try:
                    caller_fds = [
                        descriptor
                        for descriptor in range(3, 256)
                        if descriptor != wrong_fd
                        and self._fd_matches_path(descriptor, self.protected)
                    ]
                    self.assertTrue(caller_fds)
                    os.dup2(wrong_fd, min(caller_fds))
                finally:
                    os.close(wrong_fd)
            return result

        with patch.object(
            self.store,
            "_verify_execution_envelope",
            side_effect=rebind_caller_fd,
        ):
            self.assertEqual(ReconciliationOutcome.APPLIED, self.apply(acquired, envelope))
        self.assertEqual(
            b"owned live descriptor\n",
            (self.protected / "bounded" / "new.bin").read_bytes(),
        )
        self.assertFalse((wrong_root / "bounded" / "new.bin").exists())

    @staticmethod
    def _fd_matches_path(descriptor: int, path: Path) -> bool:
        try:
            observed = os.fstat(descriptor)
            expected = path.stat()
        except OSError:
            return False
        return (observed.st_dev, observed.st_ino) == (
            expected.st_dev,
            expected.st_ino,
        )

    def test_envelope_expiring_before_locked_start_leaves_no_capsule_or_intent(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create()
        now = int(time.time())
        envelope = self.envelope(
            acquired,
            issued_at=now,
            expires_at=now + 2,
        )

        with (
            patch(
                "decision_os.companion.broker_authority.time.time",
                side_effect=[now, now, now + 2],
            ),
            self.assertRaises(EnvelopeAuthenticationError) as raised,
        ):
            self.apply(acquired, envelope)
        self.assertIn("valid", str(raised.exception.__cause__ or raised.exception).casefold())
        self.assertFalse(self.store._fence_path.exists())
        self.assertFalse(self.store._capsule_path.exists())
        self.assertEqual(self.activation, self.store.require_active(self.activation).activation)

    def test_every_authority_ceiling_substitution_is_rejected(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create()
        envelope = self.envelope(acquired)
        substitutions = {
            "authority_domain_id": "other-domain",
            "control_record_sha256": "c" * 64,
            "repository_id": f"repo:v1:{'d' * 64}",
            "protected_repository_identity": f"protected:v1:{'e' * 64}",
            "write_principal_identity": f"principal:v1:{'f' * 64}",
            "operation": "REPLACE",
            "relative_path": "bounded/sibling.bin",
            "decision_sha256": "1" * 64,
            "capsule_sha256": "2" * 64,
            "bootstrap_activation_evidence_sha256": "3" * 64,
            "human_seat_authorization_evidence_sha256": "4" * 64,
        }

        for field, value in substitutions.items():
            with self.subTest(field=field):
                try:
                    forged = replace(envelope, **{field: value})
                except ValueError:
                    continue
                with self.assertRaises(BrokerApplyError):
                    self.apply(acquired, forged)
        self.assertEqual(self.activation, self.store.require_active(self.activation).activation)
        self.assertFalse(self.store._fence_path.exists())

    def test_capsule_without_intent_is_inert_and_envelope_replay_rejects(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create()
        envelope = self.envelope(acquired)

        original_new_intent = broker_control._new_cas_intent

        def crash_after_capsule(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("crash after capsule")

        with (
            patch.object(
                broker_control,
                "_new_cas_intent",
                side_effect=crash_after_capsule,
            ),
            self.assertRaisesRegex(RuntimeError, "after capsule"),
        ):
            self.apply(acquired, envelope)

        self.assertFalse((self.protected / "bounded" / "new.bin").exists())
        self.assertFalse(self.store._fence_path.exists())
        self.assertEqual(self.activation, self.store.require_active(self.activation).activation)
        with self.assertRaises(AuthorityRejectedError):
            self.apply(acquired, envelope)
        with self.assertRaises(AuthorityRejectedError):
            recover_pending_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
            )
        fresh = self.envelope(
            acquired,
            envelope_id="d" * 32,
            nonce="e" * 32,
        )
        self.assertIsNotNone(original_new_intent)
        self.assertEqual(ReconciliationOutcome.APPLIED, self.apply(acquired, fresh))

    def test_capsule_binds_exact_decision_and_external_evidence_without_secret(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create(post=b"capsule bytes\r\n\x00")
        envelope = self.envelope(acquired)

        self.assertEqual(ReconciliationOutcome.APPLIED, self.apply(acquired, envelope))
        capsule_path = next(self.store._capsule_path.glob("*.json"))
        capsule = json.loads(capsule_path.read_bytes())
        self.assertEqual(self.activation.authority_domain_id, capsule["authority_domain_id"])
        self.assertEqual(self.store._journal_records_unlocked()[0].record_sha256, capsule["control_record_sha256"])
        self.assertEqual(acquired.decision.relative_path, capsule["relative_path"])
        self.assertEqual(len(acquired.decision.target_bytes), capsule["target_byte_count"])
        self.assertEqual(acquired.decision.expected_post_sha256, capsule["target_blob_sha256"])
        self.assertEqual(envelope.envelope_id, capsule["external_envelope_id"])
        self.assertEqual(envelope.nonce, capsule["external_envelope_nonce"])
        evidence = b"".join(
            path.read_bytes()
            for path in self.store.path.parent.rglob("*")
            if path.is_file()
        )
        self.assertNotIn(self.key.secret, evidence)
        self.assertEqual(0o600, capsule_path.stat().st_mode & 0o777)

    def test_live_and_recovery_paths_do_not_invoke_subprocess(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create()
        with patch(
            "decision_os.acceleration.model.subprocess.run",
            side_effect=AssertionError("Broker must not execute subprocesses"),
        ):
            self.assertEqual(
                ReconciliationOutcome.APPLIED,
                self.apply(acquired, self.envelope(acquired)),
            )

    def test_repository_file_or_governance_artifact_cannot_mint_authority(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create()
        envelope = self.envelope(acquired)
        repository_envelope = self.protected / "approved-envelope.json"
        repository_envelope.write_text(json.dumps(envelope.as_dict()), encoding="utf-8")
        (self.protected / "ROLE_CONTRACT.md").write_text(
            "approved by repository governance\n",
            encoding="utf-8",
        )

        with self.assertRaises(BrokerApplyError):
            apply_protected_mutation(
                self.store,
                self.protected,
                self.proposal_paths[id(acquired)],
                repository_envelope,  # type: ignore[arg-type]
            )
        self.assertEqual(self.activation, self.store.require_active(self.activation).activation)


class DurableCapsuleRecoveryTest(Slice3Fixture):
    def leave_pending_case(
        self,
        temporary: str,
        authority_domain_id: str,
    ) -> tuple[ControlDomainStore, Path]:
        root = Path(temporary)
        protected = root / "protected"
        proposals = root / "proposals"
        protected.mkdir()
        proposals.mkdir()
        current = replace(
            self.activation,
            authority_domain_id=authority_domain_id,
            protected_repository_identity=protected_root_identity(protected),
        )
        store = ControlDomainStore(
            root / "state" / "control.json",
            authentication_key=self.key,
        )
        store.activate_initial(current)
        (protected / "bounded").mkdir()
        (protected / "bounded" / "target.bin").write_bytes(b"prior\n")
        proposal = proposals / "post.bin"
        proposal.write_bytes(b"post\n")
        acquired = acquire_mutation_decision(
            proposal,
            activation=current,
            operation=MutationOperation.REPLACE,
            relative_path="bounded/target.bin",
            expected_prior_sha256=sha256(b"prior\n"),
        )
        now = int(time.time())
        envelope = issue_execution_envelope(
            acquired.decision,
            store.load_required(),
            authentication_key=self.key,
            envelope_id="9" * 32,
            nonce="a" * 32,
            issued_at_unix=now,
            expires_at_unix=now + 60,
            bootstrap_activation_evidence_id="bootstrap",
            bootstrap_activation_evidence_sha256="b" * 64,
            human_seat_authorization_evidence_id="seat",
            human_seat_authorization_evidence_sha256="c" * 64,
        )
        with patch(
            "decision_os.companion.broker_apply._observe_target",
            side_effect=RuntimeError("crash"),
        ), self.assertRaises(RuntimeError):
            apply_protected_mutation(store, protected, proposal, envelope)
        return store, protected

    def leave_pending_replace(self, target_bytes: bytes) -> Any:
        parent = self.protected / "bounded"
        parent.mkdir(exist_ok=True)
        (parent / "target.bin").write_bytes(target_bytes)
        acquired = self.replace()
        envelope = self.envelope(acquired)
        with patch(
            "decision_os.companion.broker_apply._observe_target",
            side_effect=RuntimeError("crash after intent"),
        ), self.assertRaisesRegex(RuntimeError, "after intent"):
            self.apply(acquired, envelope)
        return acquired

    def test_restart_reconstructs_exact_decision_and_callerless_recovery(self) -> None:
        acquired = self.leave_pending_replace(b"prior\n")
        restarted = ControlDomainStore(self.store.path)
        reconstructed = restarted._reconstruct_pending_decision()

        self.assertIsNot(reconstructed, acquired.decision)
        self.assertEqual(acquired.decision.binding_dict(), reconstructed.binding_dict())
        self.assertEqual(b"post\r\n\x00tail", reconstructed.target_bytes)
        with (
            patch("decision_os.companion.broker_apply._attempt_live") as attempt,
            patch("decision_os.companion.broker_apply._publish_create") as create,
            patch("decision_os.companion.broker_apply._publish_replace") as replace,
        ):
            outcome = recover_pending_protected_mutation(restarted, self.protected)
        self.assertEqual(ReconciliationOutcome.NOT_APPLIED, outcome)
        attempt.assert_not_called()
        create.assert_not_called()
        replace.assert_not_called()
        self.assertEqual(ControlDomainState.ABANDONED, restarted.load_required().state)

    def test_wrong_root_recovery_rejects_without_terminal_consumption(self) -> None:
        self.leave_pending_replace(b"prior\n")
        wrong_root = self.root / "wrong-protected"
        (wrong_root / "bounded").mkdir(parents=True)
        before = tuple(self.store._fence_path.glob("*.json"))

        with self.assertRaises(BrokerApplyError):
            recover_pending_protected_mutation(
                ControlDomainStore(self.store.path),
                wrong_root,
            )
        self.assertEqual(before, tuple(self.store._fence_path.glob("*.json")))
        self.assertEqual(
            ReconciliationOutcome.NOT_APPLIED,
            recover_pending_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
            ),
        )

    def test_deep_recovery_seam_cannot_terminalize_a_relocated_store(self) -> None:
        self.leave_pending_replace(b"prior\n")
        relocated_parent = self.root / "relocated-deployment"
        relocated_parent.mkdir()
        relocated_state = relocated_parent / "state"
        self.store.path.parent.rename(relocated_state)
        relocated_store = ControlDomainStore(relocated_state / "control.json")
        before_fences = {
            path.name for path in relocated_store._fence_path.glob("*.json")
        }
        self.assertEqual(
            ControlDomainState.UNCERTAIN,
            relocated_store.load_required().state,
        )

        root_fd = broker_apply._open_protected_root(self.protected)
        try:
            direct = relocated_store._execute_pending_recovery_cas_owned
            parameters = inspect.signature(direct).parameters
            arguments: dict[str, Any] = {}
            if "protected_root" in parameters:
                arguments["protected_root"] = self.protected
            if "root_fd" in parameters:
                arguments["root_fd"] = root_fd
            self.assertTrue(
                {"protected_root", "root_fd"}.intersection(parameters),
                "Deep recovery seam has no protected-root binding input.",
            )
            with self.assertRaises((BrokerApplyError, AuthorityRejectedError)):
                direct(**arguments)
        finally:
            os.close(root_fd)

        self.assertEqual(
            before_fences,
            {path.name for path in relocated_store._fence_path.glob("*.json")},
        )
        self.assertEqual(
            ControlDomainState.UNCERTAIN,
            relocated_store.load_required().state,
        )
        self.assertEqual(
            b"prior\n",
            (self.protected / "bounded" / "target.bin").read_bytes(),
        )

    def test_lexical_parent_alias_cannot_terminalize_recovery(self) -> None:
        self.leave_pending_replace(b"prior\n")
        alias_child = self.protected / "repository-artifact"
        alias_child.mkdir()
        relocated_state = alias_child / "state"
        self.store.path.parent.rename(relocated_state)
        relocated_store = ControlDomainStore(relocated_state / "control.json")
        aliased_root = Path(f"{alias_child}{os.sep}..")
        before = {
            path.name for path in relocated_store._fence_path.glob("*.json")
        }

        with self.assertRaises(BrokerApplyError):
            recover_pending_protected_mutation(relocated_store, aliased_root)
        root_fd = broker_apply._open_protected_root(self.protected)
        try:
            with self.assertRaises(BrokerApplyError):
                relocated_store._execute_pending_recovery_cas_owned(
                    aliased_root,
                    root_fd,
                )
        finally:
            os.close(root_fd)
        self.assertEqual(
            before,
            {path.name for path in relocated_store._fence_path.glob("*.json")},
        )
        self.assertEqual(
            ControlDomainState.UNCERTAIN,
            relocated_store.load_required().state,
        )

    def test_transient_recovery_access_failure_preserves_pending_intent(self) -> None:
        self.leave_pending_replace(b"prior\n")
        before = tuple(self.store._fence_path.glob("*.json"))

        with (
            patch(
                "decision_os.companion.broker_apply._open_parent_from_root",
                side_effect=BrokerApplyError("transient traversal failure"),
            ),
            self.assertRaisesRegex(BrokerApplyError, "transient traversal"),
        ):
            recover_pending_protected_mutation(self.store, self.protected)
        self.assertEqual(before, tuple(self.store._fence_path.glob("*.json")))
        self.assertEqual(
            ReconciliationOutcome.NOT_APPLIED,
            recover_pending_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
            ),
        )

    def test_recovery_uses_owned_root_descriptor_if_caller_fd_is_rebound(self) -> None:
        self.leave_pending_replace(b"prior\n")
        wrong_root = self.root / "wrong-recovery-root"
        (wrong_root / "bounded").mkdir(parents=True)
        (wrong_root / "bounded" / "target.bin").write_bytes(b"post\r\n\x00tail")
        original_owned = self.store._execute_pending_recovery_cas_owned

        def rebind_caller_fd(
            protected_root: Path,
            owned_root_fd: int,
        ) -> ReconciliationOutcome:
            wrong_fd = os.open(
                wrong_root,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
            )
            try:
                caller_fds = [
                    descriptor
                    for descriptor in range(3, 256)
                    if descriptor not in {wrong_fd, owned_root_fd}
                    and self._fd_matches_path(descriptor, self.protected)
                ]
                self.assertTrue(caller_fds)
                os.dup2(wrong_fd, min(caller_fds))
            finally:
                os.close(wrong_fd)
            return original_owned(protected_root, owned_root_fd)

        with patch.object(
            self.store,
            "_execute_pending_recovery_cas_owned",
            side_effect=rebind_caller_fd,
        ):
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                recover_pending_protected_mutation(self.store, self.protected),
            )
        self.assertEqual(
            b"prior\n",
            (self.protected / "bounded" / "target.bin").read_bytes(),
        )
        self.assertEqual(
            b"post\r\n\x00tail",
            (wrong_root / "bounded" / "target.bin").read_bytes(),
        )

    @staticmethod
    def _fd_matches_path(descriptor: int, path: Path) -> bool:
        try:
            observed = os.fstat(descriptor)
            expected = path.stat()
        except OSError:
            return False
        return (observed.st_dev, observed.st_ino) == (
            expected.st_dev,
            expected.st_ino,
        )

    def test_durable_completion_crash_finishes_without_observing_again(self) -> None:
        self.leave_pending_replace(b"prior\n")
        original_finish = self.store._finish_cas_state_unlocked
        with (
            patch.object(
                self.store,
                "_finish_cas_state_unlocked",
                side_effect=RuntimeError("crash after completion"),
            ),
            self.assertRaisesRegex(RuntimeError, "after completion"),
        ):
            recover_pending_protected_mutation(self.store, self.protected)
        self.assertEqual(ControlDomainState.UNCERTAIN, self.store.load_required().state)
        self.assertIsNotNone(original_finish)

        with patch(
            "decision_os.companion.broker_apply._recovery_observation_from_root_fd",
            side_effect=AssertionError("completed recovery must not observe again"),
        ) as observe:
            self.assertEqual(
                ReconciliationOutcome.NOT_APPLIED,
                recover_pending_protected_mutation(
                    ControlDomainStore(self.store.path),
                    self.protected,
                ),
            )
        observe.assert_not_called()
        self.assertEqual(ControlDomainState.ABANDONED, self.store.load_required().state)

    def test_durable_completion_still_rejects_wrong_root_and_remains_retryable(
        self,
    ) -> None:
        self.leave_pending_replace(b"prior\n")
        with (
            patch.object(
                self.store,
                "_finish_cas_state_unlocked",
                side_effect=RuntimeError("crash after completion"),
            ),
            self.assertRaisesRegex(RuntimeError, "after completion"),
        ):
            recover_pending_protected_mutation(self.store, self.protected)
        wrong_root = self.root / "wrong-completed-root"
        wrong_root.mkdir()
        before = tuple(self.store._fence_path.glob("*.json"))

        with self.assertRaises(BrokerApplyError):
            recover_pending_protected_mutation(
                ControlDomainStore(self.store.path),
                wrong_root,
            )
        self.assertEqual(before, tuple(self.store._fence_path.glob("*.json")))
        self.assertEqual(ControlDomainState.UNCERTAIN, self.store.load_required().state)
        self.assertEqual(
            ReconciliationOutcome.NOT_APPLIED,
            recover_pending_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
            ),
        )

    def test_recovery_classifies_exact_post_and_neither(self) -> None:
        for label, observed, expected in (
            ("post", b"post\r\n\x00tail", ReconciliationOutcome.APPLIED),
            ("neither", b"neither\n", ReconciliationOutcome.UNCERTAIN),
        ):
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temporary:
                    # Re-run a complete fixture manually because each case needs
                    # an independent one-shot authority domain.
                    protected = Path(temporary) / "protected"
                    proposals = Path(temporary) / "proposals"
                    protected.mkdir()
                    proposals.mkdir()
                    current = replace(
                        self.activation,
                        authority_domain_id=f"case-{label}",
                        protected_repository_identity=protected_root_identity(protected),
                    )
                    store = ControlDomainStore(
                        Path(temporary) / "state" / "control.json",
                        authentication_key=self.key,
                    )
                    store.activate_initial(current)
                    (protected / "bounded").mkdir()
                    target = protected / "bounded" / "target.bin"
                    target.write_bytes(observed)
                    proposal = proposals / "post.bin"
                    proposal.write_bytes(b"post\r\n\x00tail")
                    acquired = acquire_mutation_decision(
                        proposal,
                        activation=current,
                        operation=MutationOperation.REPLACE,
                        relative_path="bounded/target.bin",
                        expected_prior_sha256=sha256(b"prior\n"),
                    )
                    now = int(time.time())
                    envelope = issue_execution_envelope(
                        acquired.decision,
                        store.load_required(),
                        authentication_key=self.key,
                        envelope_id="5" * 32,
                        nonce="6" * 32,
                        issued_at_unix=now,
                        expires_at_unix=now + 60,
                        bootstrap_activation_evidence_id="bootstrap",
                        bootstrap_activation_evidence_sha256="7" * 64,
                        human_seat_authorization_evidence_id="human-seat",
                        human_seat_authorization_evidence_sha256="8" * 64,
                    )
                    with patch(
                        "decision_os.companion.broker_apply._observe_target",
                        side_effect=RuntimeError("crash after intent"),
                    ), self.assertRaises(RuntimeError):
                        apply_protected_mutation(
                            store,
                            protected,
                            proposal,
                            envelope,
                        )
                    self.assertEqual(
                        expected,
                        recover_pending_protected_mutation(
                            ControlDomainStore(store.path),
                            protected,
                        ),
                    )

    def test_missing_capsule_or_wrong_bound_capsule_fails_before_observation(self) -> None:
        self.leave_pending_replace(b"prior\n")
        intent_path = next(
            path
            for path in self.store._fence_path.glob("*.json")
            if json.loads(path.read_bytes())["kind"] == "INTENT"
        )
        intent = json.loads(intent_path.read_bytes())
        capsule_path = self.store._capsule_path / f"{intent['capsule_sha256']}.json"
        capsule_path.rename(capsule_path.with_suffix(".missing"))

        with patch(
            "decision_os.companion.broker_apply._recovery_observation_from_root_fd"
        ) as observe:
            with self.assertRaises(MutationCapsuleIntegrityError):
                recover_pending_protected_mutation(
                    ControlDomainStore(self.store.path),
                    self.protected,
                )
            observe.assert_not_called()

    def test_intent_bound_to_wrong_capsule_hash_fails_before_observation(self) -> None:
        self.leave_pending_replace(b"prior\n")
        intent_path = next(
            path
            for path in self.store._fence_path.glob("*.json")
            if json.loads(path.read_bytes())["kind"] == "INTENT"
        )
        value = json.loads(intent_path.read_bytes())
        value["capsule_sha256"] = "d" * 64
        value["record_sha256"] = broker_authority.hash_payload(
            {key: item for key, item in value.items() if key != "record_sha256"}
        )
        replacement = intent_path.with_name(f"{value['record_sha256']}.json")
        replacement.write_bytes(
            (broker_authority.canonical_json(value) + "\n").encode("utf-8")
        )
        intent_path.unlink()

        with patch(
            "decision_os.companion.broker_apply._recovery_observation_from_root_fd"
        ) as observe:
            with self.assertRaises(MutationCapsuleIntegrityError):
                recover_pending_protected_mutation(
                    ControlDomainStore(self.store.path),
                    self.protected,
                )
            observe.assert_not_called()

    def test_ambiguous_pending_intents_fail_before_observation(self) -> None:
        acquired = self.leave_pending_replace(b"prior\n")
        journal = self.store._journal_records_unlocked()
        pending = next(
            fence
            for fence in self.store._cas_fences_unlocked(journal)
            if fence.kind == "INTENT"
        )
        second_decision = MutationDecision(
            activation=self.activation,
            operation=MutationOperation.REPLACE,
            relative_path="bounded/other.bin",
            target_bytes=b"other post\n",
            expected_prior_sha256=sha256(b"other prior\n"),
            expected_post_sha256=sha256(b"other post\n"),
            proposal_acquisition_sha256=(
                acquired.decision.proposal_acquisition_sha256
            ),
        )
        second = broker_control._new_cas_intent(
            second_decision,
            journal[0],
            capsule_sha256=pending.capsule_sha256,
        )
        self.store._append_cas_fence_unlocked(second)

        with patch(
            "decision_os.companion.broker_apply._recovery_observation_from_root_fd"
        ) as observe:
            with self.assertRaises(ControlRecordIntegrityError):
                recover_pending_protected_mutation(
                    ControlDomainStore(self.store.path),
                    self.protected,
                )
            observe.assert_not_called()

    def test_missing_corrupt_symlinked_or_hardlinked_blob_fails_closed(self) -> None:
        cases = ("missing", "corrupt", "oversize", "symlink", "hardlink")
        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as temporary:
                    store, protected = self.leave_pending_case(
                        temporary,
                        f"blob-{case}",
                    )
                    blob = next(store._blob_path.glob("*.blob"))
                    if case == "missing":
                        blob.rename(blob.with_suffix(".missing"))
                    elif case == "corrupt":
                        blob.write_bytes(b"wrong\n")
                    elif case == "oversize":
                        blob.write_bytes(b"x" * (broker_authority._MAX_TARGET_BYTES + 1))
                    elif case == "symlink":
                        held = blob.with_suffix(".held")
                        blob.rename(held)
                        blob.symlink_to(held.name)
                    else:
                        alias = blob.with_name(
                            f".broker-control-{sha256(blob.read_bytes())}-"
                            "deadbeefdeadbeef.tmp"
                        )
                        os.link(blob, alias)
                    with patch(
                        "decision_os.companion.broker_apply."
                        "_recovery_observation_from_root_fd"
                    ) as observe:
                        with self.assertRaises(MutationCapsuleIntegrityError):
                            recover_pending_protected_mutation(
                                ControlDomainStore(store.path),
                                protected,
                            )
                        observe.assert_not_called()

    def test_corrupt_oversize_symlinked_or_hardlinked_capsule_fails_closed(
        self,
    ) -> None:
        for case in ("corrupt", "oversize", "symlink", "hardlink"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                store, protected = self.leave_pending_case(
                    temporary,
                    f"capsule-{case}",
                )
                capsule = next(store._capsule_path.glob("*.json"))
                if case == "corrupt":
                    capsule.write_bytes(b"{}\n")
                elif case == "oversize":
                    capsule.write_bytes(
                        b"x" * (broker_authority.MAX_CAPSULE_BYTES + 1)
                    )
                elif case == "symlink":
                    held = Path(temporary) / "held-capsule.json"
                    capsule.rename(held)
                    capsule.symlink_to(held)
                else:
                    os.link(capsule, Path(temporary) / "capsule-alias.json")

                with patch(
                    "decision_os.companion.broker_apply."
                    "_recovery_observation_from_root_fd"
                ) as observe:
                    with self.assertRaises(MutationCapsuleIntegrityError):
                        recover_pending_protected_mutation(
                            ControlDomainStore(store.path),
                            protected,
                        )
                    observe.assert_not_called()

    def test_symlinked_capsule_parent_directory_fails_closed(self) -> None:
        self.leave_pending_replace(b"prior\n")
        held = self.store._capsule_path.parent / "held-capsules"
        self.store._capsule_path.rename(held)
        self.store._capsule_path.symlink_to(held.name)

        with patch(
            "decision_os.companion.broker_apply._recovery_observation_from_root_fd"
        ) as observe:
            with self.assertRaises(MutationCapsuleIntegrityError):
                recover_pending_protected_mutation(
                    ControlDomainStore(self.store.path),
                    self.protected,
                )
            observe.assert_not_called()

    def test_symlinked_blob_parent_directory_fails_closed(self) -> None:
        self.leave_pending_replace(b"prior\n")
        held = self.store._capsule_path / "held-blobs"
        self.store._blob_path.rename(held)
        self.store._blob_path.symlink_to(held.name)

        with patch(
            "decision_os.companion.broker_apply._recovery_observation_from_root_fd"
        ) as observe:
            with self.assertRaises(MutationCapsuleIntegrityError):
                recover_pending_protected_mutation(
                    ControlDomainStore(self.store.path),
                    self.protected,
                )
            observe.assert_not_called()

    def test_capsule_from_another_domain_is_rejected(self) -> None:
        self.leave_pending_replace(b"prior\n")
        capsule_path = next(self.store._capsule_path.glob("*.json"))
        value = json.loads(capsule_path.read_bytes())
        value["authority_domain_id"] = "another-domain"
        value["capsule_sha256"] = broker_authority.hash_payload(
            {key: item for key, item in value.items() if key != "capsule_sha256"}
        )
        replacement_capsule = capsule_path.with_name(
            f"{value['capsule_sha256']}.json"
        )
        replacement_capsule.write_bytes(
            (broker_authority.canonical_json(value) + "\n").encode("utf-8")
        )
        capsule_path.unlink()
        intent_path = next(
            path
            for path in self.store._fence_path.glob("*.json")
            if json.loads(path.read_bytes())["kind"] == "INTENT"
        )
        intent = json.loads(intent_path.read_bytes())
        intent["capsule_sha256"] = value["capsule_sha256"]
        intent["record_sha256"] = broker_authority.hash_payload(
            {key: item for key, item in intent.items() if key != "record_sha256"}
        )
        replacement_intent = intent_path.with_name(
            f"{intent['record_sha256']}.json"
        )
        replacement_intent.write_bytes(
            (broker_authority.canonical_json(intent) + "\n").encode("utf-8")
        )
        intent_path.unlink()

        with self.assertRaises(MutationCapsuleIntegrityError):
            recover_pending_protected_mutation(
                ControlDomainStore(self.store.path),
                self.protected,
            )

    def test_completed_authority_has_no_pending_public_recovery(self) -> None:
        (self.protected / "bounded").mkdir()
        acquired = self.create()
        self.apply(acquired, self.envelope(acquired))

        with self.assertRaises(AuthorityRejectedError):
            recover_pending_protected_mutation(self.store, self.protected)


class Slice3ClaimBoundaryTest(unittest.TestCase):
    def test_public_recovery_takes_no_decision_details(self) -> None:
        parameters = inspect.signature(recover_pending_protected_mutation).parameters
        self.assertEqual({"store", "protected_root"}, set(parameters))
        self.assertFalse(hasattr(
            __import__(
                "decision_os.companion.broker_apply",
                fromlist=["recover_protected_mutation"],
            ),
            "recover_protected_mutation",
        ))
        live_parameters = inspect.signature(apply_protected_mutation).parameters
        self.assertNotIn("authentication_key", live_parameters)
        self.assertNotIn("operation", live_parameters)
        self.assertNotIn("relative_path", live_parameters)
        self.assertNotIn("expected_prior_sha256", live_parameters)

    def test_trust_root_and_os_claim_boundaries_are_explicit(self) -> None:
        normalized = PRODUCTION_AUTHENTICATION_TRUST_PRECONDITION.casefold()
        for phrase in (
            "not enforced by slice 3",
            "external authentication key",
            "outside the protected repository",
            "os-level peer separation",
            "root-owned secret protection",
            "acl enforcement",
            "broker sole-writer enforcement",
            "launchdaemon/xpc isolation",
            "equivalent filesystem authority",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, normalized)
        routing = PRODUCTION_CANONICAL_STORE_PRECONDITION.casefold()
        for phrase in (
            "protected_root.parent/state/control.json",
            "request data may supply neither",
            "distinct parent deployment roots",
            "later deployment gate",
        ):
            with self.subTest(routing_phrase=phrase):
                self.assertIn(phrase, routing)

    def test_secret_is_not_serialized_into_broker_evidence(self) -> None:
        key = EnvelopeAuthenticationKey(
            key_id="hidden",
            key_version=1,
            secret=b"never-persist-this-external-secret" * 2,
        )
        self.assertNotIn(key.secret.decode(), repr(key))


if __name__ == "__main__":
    unittest.main()
