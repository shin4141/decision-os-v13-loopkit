from __future__ import annotations

from contextlib import nullcontext
import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import tempfile
from threading import BrokenBarrierError
import time
import unittest

from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import (
    DecisionType,
    GENESIS_EVENT_HASH,
    ScopeError,
    derive_decision_identity,
    normalize_scope,
    repository_id,
)
from decision_os.acceleration.store import AccelerationStore, StateIntegrityError


def create_repository(parent: Path, name: str = "repo") -> Path:
    repository = parent / name
    repository.mkdir()
    subprocess.run(
        ("git", "init", "-q", str(repository)),
        check=True,
        capture_output=True,
    )
    return repository


def append_in_process(
    repository_raw: str,
    run_id: str,
    start_barrier: object | None = None,
    stale_read_barrier: object | None = None,
    bypass_event_lock: bool = False,
) -> None:
    """Append one deterministic event from an independent process."""

    repository = Path(repository_raw)
    store = AccelerationStore(
        repository,
        clock=lambda: "2026-08-20T00:00:00Z",
        event_id_factory=lambda: f"event-{run_id}",
    )
    identity = derive_decision_identity(
        repository,
        DecisionType.CREATE_FILE,
        "new.txt",
    )
    if bypass_event_lock:
        store.state_dir.mkdir(parents=True, exist_ok=True)
        store._locked_event_chain = nullcontext  # type: ignore[method-assign]
    if stale_read_barrier is not None:
        original_read_events = store.read_events

        def coordinated_stale_read() -> list[dict[str, object]]:
            events = original_read_events()
            try:
                stale_read_barrier.wait(timeout=3)  # type: ignore[attr-defined]
            except BrokenBarrierError:
                pass
            return events

        store.read_events = coordinated_stale_read  # type: ignore[method-assign]
    if start_barrier is not None:
        start_barrier.wait(timeout=10)  # type: ignore[attr-defined]
    store.append(
        "DECISION_CHECK",
        identity,
        run_id=run_id,
        iteration=1,
        adapter="test",
        adapter_version="1",
        status="CHECKED",
    )


def exit_while_holding_event_lock(
    repository_raw: str,
    acquired: object,
) -> None:
    store = AccelerationStore(Path(repository_raw))
    with store._locked_event_chain():
        acquired.set()  # type: ignore[attr-defined]
        os._exit(17)


class AccelerationStoreTest(unittest.TestCase):
    process_context = multiprocessing.get_context("spawn")

    def assert_processes_complete(
        self,
        processes: list[multiprocessing.Process],
        *,
        timeout: float = 15,
    ) -> None:
        deadline = time.monotonic() + timeout
        for process in processes:
            process.join(max(0, deadline - time.monotonic()))
        stuck = [process for process in processes if process.is_alive()]
        for process in stuck:
            process.terminate()
            process.join()
        self.assertEqual([], stuck, "child process did not complete")
        self.assertEqual([0] * len(processes), [p.exitcode for p in processes])

    def test_unlocked_append_reproduces_sibling_event_race(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            stale_read_barrier = self.process_context.Barrier(2)
            processes = [
                self.process_context.Process(
                    target=append_in_process,
                    args=(
                        str(repository),
                        f"old-race-{index}",
                        None,
                        stale_read_barrier,
                        True,
                    ),
                )
                for index in range(2)
            ]

            for process in processes:
                process.start()
            self.assert_processes_complete(processes)

            store = AccelerationStore(repository)
            physical_events = [
                json.loads(line)
                for line in store.events_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(2, len(physical_events))
            self.assertEqual(
                {GENESIS_EVENT_HASH},
                {event["prev_event_hash"] for event in physical_events},
            )
            with self.assertRaises(StateIntegrityError):
                store.read_events()

    def test_two_process_appends_are_serialized_into_valid_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            start_barrier = self.process_context.Barrier(2)
            stale_read_barrier = self.process_context.Barrier(2)
            processes = [
                self.process_context.Process(
                    target=append_in_process,
                    args=(
                        str(repository),
                        f"repaired-race-{index}",
                        start_barrier,
                        stale_read_barrier,
                    ),
                )
                for index in range(2)
            ]

            for process in processes:
                process.start()
            self.assert_processes_complete(processes)

            events = AccelerationStore(repository).read_events()
            self.assertEqual(2, len(events))
            self.assertEqual(
                {"repaired-race-0", "repaired-race-1"},
                {event["run_id"] for event in events},
            )
            self.assertEqual(events[0]["event_hash"], events[1]["prev_event_hash"])

    def test_event_lock_is_repository_local(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            first_repository = create_repository(parent, "first")
            second_repository = create_repository(parent, "second")
            first_store = AccelerationStore(first_repository)

            with first_store._locked_event_chain():
                process = self.process_context.Process(
                    target=append_in_process,
                    args=(str(second_repository), "unrelated-repository"),
                )
                process.start()
                self.assert_processes_complete([process], timeout=5)

            events = AccelerationStore(second_repository).read_events()
            self.assertEqual(["unrelated-repository"], [e["run_id"] for e in events])

    def test_process_exit_releases_event_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            acquired = self.process_context.Event()
            process = self.process_context.Process(
                target=exit_while_holding_event_lock,
                args=(str(repository), acquired),
            )
            process.start()
            try:
                self.assertTrue(acquired.wait(timeout=10))
                process.join(timeout=10)
            finally:
                if process.is_alive():
                    process.terminate()
                    process.join()
            self.assertEqual(17, process.exitcode)

            append_in_process(str(repository), "after-crash")

            events = AccelerationStore(repository).read_events()
            self.assertEqual(["after-crash"], [event["run_id"] for event in events])

    def test_state_lives_under_git_common_dir_and_chain_is_reproducible(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            (repository / "target.txt").write_text("one\n", encoding="utf-8")
            ids = iter(("event-1", "event-2"))
            store = AccelerationStore(
                repository,
                clock=lambda: "2026-07-27T00:00:00Z",
                event_id_factory=lambda: next(ids),
            )
            identity = derive_decision_identity(
                repository,
                DecisionType.MODIFY_FILE,
                "./target.txt",
            )

            first = store.append(
                "DECISION_CHECK",
                identity,
                run_id="run-1",
                iteration=1,
                adapter="test",
                adapter_version="1",
                status="CHECKED",
            )
            second = store.append(
                "HUMAN_DEFAULT_CREATED",
                identity,
                run_id="run-1",
                iteration=1,
                adapter="test",
                adapter_version="1",
                status="ACTIVE",
                default_created_run_id="run-1",
                default_rule_hash=identity.rule_hash,
            )

            self.assertEqual(first["event_hash"], second["prev_event_hash"])
            self.assertEqual(second["event_hash"], store.chain_head())
            self.assertEqual(2, len(store.read_events()))
            self.assertTrue(
                store.events_path.is_relative_to(
                    (repository / ".git").resolve(strict=True)
                )
            )
            self.assertFalse((repository / "events.jsonl").exists())

    def test_corruption_blocks_reads_and_future_appends(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            store = AccelerationStore(repository)
            identity = derive_decision_identity(
                repository,
                DecisionType.CREATE_FILE,
                "new.txt",
            )
            store.append(
                "DECISION_CHECK",
                identity,
                run_id="run-1",
                iteration=1,
                adapter="test",
                adapter_version="1",
                status="CHECKED",
            )
            event = json.loads(store.events_path.read_text(encoding="utf-8"))
            event["status"] = "TAMPERED"
            store.events_path.write_text(
                f"{json.dumps(event, sort_keys=True)}\n",
                encoding="utf-8",
            )

            with self.assertRaises(StateIntegrityError):
                store.read_events()
            with self.assertRaises(StateIntegrityError):
                store.append(
                    "DECISION_CHECK",
                    identity,
                    run_id="run-2",
                    iteration=1,
                    adapter="test",
                    adapter_version="1",
                    status="CHECKED",
                )

    def test_scope_normalization_rejects_escape_glob_directory_and_symlink(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            repository = create_repository(parent)
            target = repository / "folder" / "target.txt"
            target.parent.mkdir()
            target.write_text("one\n", encoding="utf-8")
            outside = parent / "outside.txt"
            outside.write_text("secret\n", encoding="utf-8")
            (repository / "outside-link").symlink_to(outside)

            self.assertEqual(
                "folder/target.txt",
                normalize_scope(repository, "./folder//target.txt"),
            )
            self.assertEqual(
                "folder/new.txt",
                normalize_scope(repository, "folder/sub/../new.txt"),
            )
            first = derive_decision_identity(
                repository,
                DecisionType.MODIFY_FILE,
                "folder/target.txt",
            )
            second = derive_decision_identity(
                repository,
                DecisionType.MODIFY_FILE,
                "./folder/target.txt",
            )
            self.assertEqual(first.decision_key, second.decision_key)
            self.assertEqual(first.rule_hash, second.rule_hash)
            for invalid in (
                "../outside.txt",
                "*.txt",
                ".",
                "folder",
                "outside-link",
            ):
                with self.subTest(invalid=invalid):
                    with self.assertRaises(ScopeError):
                        normalize_scope(repository, invalid)

    def test_repository_id_hashes_credential_free_remote_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory), "private-name")
            remote = "https://secret-user:secret-token@github.com/acme/private.git"
            subprocess.run(
                ("git", "-C", str(repository), "remote", "add", "origin", remote),
                check=True,
                capture_output=True,
            )

            identity = repository_id(repository)

            self.assertTrue(identity.startswith("repo:v1:"))
            self.assertNotIn("secret", identity)
            self.assertNotIn("private", identity)
            self.assertNotIn("github", identity)

    def test_settings_are_validated_and_do_not_add_events(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            store = AccelerationStore(repository)

            updated = store.update_settings(
                minutes_per_reuse=8,
                hourly_value_jpy=6000,
                tokens_per_reuse=1000,
                set_tokens=True,
            )

            self.assertEqual(8, updated.minutes_per_reuse)
            self.assertEqual(6000, updated.hourly_value_jpy)
            self.assertEqual(1000, updated.tokens_per_reuse)
            self.assertEqual([], store.read_events())
            with self.assertRaises(StateIntegrityError):
                store.update_settings(minutes_per_reuse=0)

    def test_active_defaults_are_enumerated_and_revoked_without_key_changes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            (repository / "target.txt").write_text("one\n", encoding="utf-8")
            engine = AccelerationEngine(repository)
            run_id = engine.new_run_id()

            outcome = engine.evaluate(
                run_id=run_id,
                iteration=1,
                decision_type=DecisionType.MODIFY_FILE,
                requested_scope="./target.txt",
                source_interrupt_id="enumeration-test",
                choice_provider=lambda _identity: "2",
            )
            records = engine.store.active_defaults()

            self.assertEqual(1, len(records))
            record = records[0]
            self.assertEqual(outcome.identity.decision_key, record.decision_key)
            self.assertEqual(outcome.identity.rule_hash, record.rule_hash)
            self.assertEqual("MODIFY_FILE", record.decision_type)
            self.assertEqual("target.txt", record.normalized_scope)
            self.assertEqual(run_id, record.created_run_id)
            self.assertTrue(record.created_at.endswith("Z"))

            engine.revoke(
                run_id=engine.new_run_id(),
                decision_key=record.decision_key,
            )

            self.assertEqual((), engine.store.active_defaults())


if __name__ == "__main__":
    unittest.main()
