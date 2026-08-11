from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from decision_os.acceleration.engine import AccelerationEngine, DeterministicAdapter
from decision_os.acceleration.model import DecisionType
from decision_os.acceleration.store import AccelerationStore


def create_repository(parent: Path, name: str = "private-repository") -> Path:
    repository = parent / name
    repository.mkdir()
    subprocess.run(
        ("git", "init", "-q", str(repository)),
        check=True,
        capture_output=True,
    )
    (repository / "target.txt").write_text("one\n", encoding="utf-8")
    return repository


class AccelerationEngineTest(unittest.TestCase):
    def make_engine(self, repository: Path) -> AccelerationEngine:
        return AccelerationEngine(
            repository,
            adapter="deterministic-test",
            adapter_version="v0.1",
        )

    def test_cross_run_first_save_then_reuse_counters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = self.make_engine(repository)
            adapter = DeterministicAdapter(engine)

            first, first_checkpoint = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice="2",
                run_id="run-1",
            )
            second, second_checkpoint = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                run_id="run-2",
            )
            third, third_checkpoint = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                run_id="run-3",
            )

            self.assertEqual("HUMAN_DEFAULT_CREATED", first.status)
            self.assertEqual("HUMAN_DEFAULT_CREATED", first_checkpoint.status)
            self.assertEqual("DEFAULT_MATCHED", second.status)
            self.assertEqual("VERIFIED_SAVE", second_checkpoint.status)
            self.assertEqual("VERIFIED_REUSE", third_checkpoint.status)
            self.assertTrue(third.allowed)
            self.assertEqual((1, 2), engine.store.counters())

    def test_mutation_authority_preflight_precedes_matching_default(self) -> None:
        cases = (
            (DecisionType.MODIFY_FILE, "target.txt"),
            (DecisionType.CREATE_FILE, "created.txt"),
        )
        for decision_type, path in cases:
            with self.subTest(decision_type=decision_type):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory))
                    ordinary = self.make_engine(repository)
                    created = ordinary.evaluate(
                        run_id="default-creation",
                        iteration=1,
                        decision_type=decision_type,
                        requested_scope=path,
                        source_interrupt_id="create-default",
                        choice_provider=lambda _identity: "2",
                    )
                    default_before = ordinary.store.active_default(
                        created.identity.decision_key
                    )
                    preflight_calls = []
                    human_calls = []
                    guarded = AccelerationEngine(
                        repository,
                        adapter="deterministic-test",
                        adapter_version="v0.1",
                        mutation_authority_preflight=lambda identity: (
                            preflight_calls.append(identity) or False
                        ),
                    )

                    with patch.object(
                        guarded.store,
                        "active_default",
                        wraps=guarded.store.active_default,
                    ) as default_lookup:
                        denied = guarded.evaluate(
                            run_id="compound-out-of-envelope",
                            iteration=1,
                            decision_type=decision_type,
                            requested_scope=path,
                            source_interrupt_id="compound-proposal",
                            choice_provider=lambda identity: (
                                human_calls.append(identity) or "1"
                            ),
                        )

                    self.assertEqual("DENIED", denied.status)
                    self.assertFalse(denied.allowed)
                    self.assertEqual([denied.identity], preflight_calls)
                    self.assertEqual([], human_calls)
                    default_lookup.assert_not_called()
                    self.assertEqual(
                        default_before,
                        guarded.store.active_default(
                            created.identity.decision_key
                        ),
                    )
                    event_types = [
                        event["event_type"]
                        for event in guarded.store.read_events()
                        if event["run_id"] == "compound-out-of-envelope"
                    ]
                    self.assertEqual(["DECISION_CHECK"], event_types)

    def test_in_envelope_and_ordinary_default_acceleration_survive(self) -> None:
        cases = (
            (DecisionType.MODIFY_FILE, "target.txt"),
            (DecisionType.CREATE_FILE, "created.txt"),
        )
        for decision_type, path in cases:
            with self.subTest(decision_type=decision_type):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory))
                    ordinary = self.make_engine(repository)
                    created = ordinary.evaluate(
                        run_id="default-creation",
                        iteration=1,
                        decision_type=decision_type,
                        requested_scope=path,
                        source_interrupt_id="create-default",
                        choice_provider=lambda _identity: "2",
                    )
                    preflight_calls = []
                    compound = AccelerationEngine(
                        repository,
                        adapter="deterministic-test",
                        adapter_version="v0.1",
                        mutation_authority_preflight=lambda identity: (
                            preflight_calls.append(identity) or True
                        ),
                    )

                    in_envelope = compound.evaluate(
                        run_id="compound-in-envelope",
                        iteration=1,
                        decision_type=decision_type,
                        requested_scope=path,
                        source_interrupt_id="compound-proposal",
                        choice_provider=lambda _identity: self.fail(
                            "matching Default must not ask the Human Seat"
                        ),
                    )
                    later_ordinary = ordinary.evaluate(
                        run_id="later-ordinary",
                        iteration=1,
                        decision_type=decision_type,
                        requested_scope=path,
                        source_interrupt_id="ordinary-proposal",
                        choice_provider=lambda _identity: self.fail(
                            "ordinary matching Default must not ask again"
                        ),
                    )

                    self.assertEqual("DEFAULT_MATCHED", in_envelope.status)
                    self.assertTrue(in_envelope.allowed)
                    self.assertEqual([in_envelope.identity], preflight_calls)
                    self.assertEqual("DEFAULT_MATCHED", later_ordinary.status)
                    self.assertTrue(later_ordinary.allowed)
                    self.assertEqual(
                        created.default_created_run_id,
                        later_ordinary.default_created_run_id,
                    )

    def test_mutation_authority_preflight_fails_closed_and_normalizes_once(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            observed = []
            engine = AccelerationEngine(
                repository,
                adapter="deterministic-test",
                adapter_version="v0.1",
                mutation_authority_preflight=lambda identity: (
                    observed.append(identity.normalized_scope) or False
                ),
            )

            first = engine.evaluate(
                run_id="normalized-1",
                iteration=1,
                decision_type=DecisionType.MODIFY_FILE,
                requested_scope="./target.txt",
                source_interrupt_id="normalized-1",
                choice_provider=lambda _identity: "1",
            )
            second = engine.evaluate(
                run_id="normalized-2",
                iteration=1,
                decision_type=DecisionType.MODIFY_FILE,
                requested_scope="nested/../target.txt",
                source_interrupt_id="normalized-2",
                choice_provider=lambda _identity: "1",
            )

            self.assertEqual("DENIED", first.status)
            self.assertEqual("DENIED", second.status)
            self.assertEqual(["target.txt", "target.txt"], observed)
            self.assertEqual(first.identity, second.identity)

            for result in (None, "allowed", 1):
                with self.subTest(result=result):
                    malformed = AccelerationEngine(
                        repository,
                        mutation_authority_preflight=lambda _identity: result,
                    ).evaluate(
                        run_id=f"malformed-{result!r}",
                        iteration=1,
                        decision_type=DecisionType.MODIFY_FILE,
                        requested_scope="target.txt",
                        source_interrupt_id="malformed",
                        choice_provider=lambda _identity: "1",
                    )
                    self.assertEqual("DENIED", malformed.status)

            raised = AccelerationEngine(
                repository,
                mutation_authority_preflight=lambda _identity: (_ for _ in ()).throw(
                    RuntimeError("malformed compound authority")
                ),
            ).evaluate(
                run_id="malformed-raised",
                iteration=1,
                decision_type=DecisionType.MODIFY_FILE,
                requested_scope="target.txt",
                source_interrupt_id="malformed",
                choice_provider=lambda _identity: "1",
            )
            self.assertEqual("DENIED", raised.status)

            callback_calls = []
            unrelated_surface = AccelerationEngine(
                repository,
                mutation_authority_preflight=lambda identity: (
                    callback_calls.append(identity) or False
                ),
            ).evaluate(
                run_id="unrelated-authority-surface",
                iteration=1,
                decision_type=DecisionType.ADD_TESTS,
                requested_scope="target.txt",
                source_interrupt_id="unrelated-authority-surface",
                choice_provider=lambda _identity: "1",
            )
            self.assertEqual("ALLOW_ONCE", unrelated_surface.status)
            self.assertEqual([], callback_calls)

    def test_allow_once_deny_timeout_and_same_run_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = self.make_engine(repository)
            adapter = DeterministicAdapter(engine)

            allowed, _ = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice="1",
                run_id="allow-once",
            )
            denied, _ = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice=None,
                run_id="timeout",
            )
            created, _ = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice="2",
                run_id="same-run",
                iteration=1,
            )
            same_run, same_checkpoint = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                run_id="same-run",
                iteration=2,
            )

            self.assertEqual("ALLOW_ONCE", allowed.status)
            self.assertEqual("DENIED", denied.status)
            self.assertEqual("HUMAN_DEFAULT_CREATED", created.status)
            self.assertEqual("SAME_RUN_DEFAULT", same_run.status)
            self.assertEqual("SAME_RUN_DEFAULT", same_checkpoint.status)
            self.assertEqual((0, 0), engine.store.counters())

    def test_abnormal_terminal_remains_pending(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = self.make_engine(repository)
            adapter = DeterministicAdapter(engine)
            adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice="2",
                run_id="run-1",
            )

            _, checkpoint = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                run_id="run-2",
                normal_terminal=False,
            )

            self.assertEqual("PENDING", checkpoint.status)
            self.assertEqual((0, 0), engine.store.counters())
            self.assertEqual(
                "CHECKPOINT_PENDING",
                engine.store.read_events()[-1]["event_type"],
            )

    def test_pre_checkpoint_override_rejects_save(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = self.make_engine(repository)
            adapter = DeterministicAdapter(engine)
            adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice="2",
                run_id="run-1",
            )

            _, checkpoint = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                run_id="run-2",
                override_before_checkpoint=True,
            )

            self.assertEqual("REVOKED_SAVE", checkpoint.status)
            self.assertEqual((0, 0), engine.store.counters())
            self.assertIsNone(
                engine.store.active_default(
                    engine.store.read_events()[0]["decision_key"]
                )
            )

    def test_post_checkpoint_revocation_preserves_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = self.make_engine(repository)
            adapter = DeterministicAdapter(engine)
            adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice="2",
                run_id="run-1",
            )
            verified, _ = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                run_id="run-2",
            )

            result = engine.revoke(
                run_id="revoke-run",
                decision_key=verified.identity.decision_key,
            )

            self.assertEqual("DEFAULT_REVOKED_AFTER_USE", result)
            self.assertEqual((1, 1), engine.store.counters())
            self.assertIsNone(
                engine.store.active_default(verified.identity.decision_key)
            )

    def test_receipt_separates_estimates_and_keeps_outward_privacy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "secret-project")
            engine = self.make_engine(repository)
            adapter = DeterministicAdapter(engine)
            adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice="2",
                run_id="run-1",
            )
            adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                run_id="run-2",
            )
            before_events = list(engine.store.read_events())
            engine.store.update_settings(
                minutes_per_reuse=7.5,
                hourly_value_jpy=5000,
                tokens_per_reuse=9467,
                set_tokens=True,
            )

            receipt = engine.receipt()
            rendered = engine.render_receipt()

            self.assertEqual(1, receipt["hard_metrics"]["verified_saves"])
            self.assertEqual(1, receipt["hard_metrics"]["verified_reuses"])
            self.assertEqual(7.5, receipt["estimated"]["minutes"])
            self.assertEqual(625, receipt["estimated"]["money_jpy"])
            self.assertEqual(9467, receipt["estimated"]["tokens"])
            self.assertEqual(before_events, engine.store.read_events())
            self.assertNotIn("secret-project", rendered)
            self.assertNotIn("target.txt", rendered)
            self.assertNotIn(str(repository), rendered)
            self.assertIn("not third-party certification", rendered)

    def test_default_tokens_are_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = self.make_engine(repository)

            self.assertIsNone(engine.receipt()["estimated"]["tokens"])
            self.assertIn("UNKNOWN tokens", engine.render_receipt())

    def test_supersede_preserves_verified_history_and_deactivates_default(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            engine = self.make_engine(repository)
            adapter = DeterministicAdapter(engine)
            adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                human_choice="2",
                run_id="run-1",
            )
            verified, _ = adapter.run(
                decision_type=DecisionType.MODIFY_FILE,
                scope="target.txt",
                run_id="run-2",
            )

            status = engine.supersede(
                run_id="supersede-run",
                decision_key=verified.identity.decision_key,
            )

            self.assertEqual("DEFAULT_SUPERSEDED", status)
            self.assertEqual((1, 1), engine.store.counters())
            self.assertIsNone(
                engine.store.active_default(verified.identity.decision_key)
            )
            self.assertEqual(
                "DEFAULT_SUPERSEDED",
                engine.store.read_events()[-1]["event_type"],
            )


if __name__ == "__main__":
    unittest.main()
