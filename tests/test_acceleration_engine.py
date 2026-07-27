from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

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
