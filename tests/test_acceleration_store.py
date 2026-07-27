from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from decision_os.acceleration.model import (
    DecisionType,
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


class AccelerationStoreTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
