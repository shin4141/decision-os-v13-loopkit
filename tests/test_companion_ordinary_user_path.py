from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
import uuid
from unittest.mock import patch

from decision_os.companion.guided_intake import (
    GuidedIntakeController,
    sha256_bytes,
)
from decision_os.companion.ordinary_user_path import (
    OrdinaryUserPathCoordinator,
    OrdinaryUserPathError,
)


FIXTURES = Path(__file__).parent / "fixtures" / "ordinary_user_path_v0_1"
SOURCE_PATH = (
    FIXTURES / "Decision_OS_Ordinary_User_Path_Contract_v0.1_APPROVED_CANDIDATE.md"
)
PRODUCT_WRAPPER_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "guided_intake_quoted_payload_v0_1"
    / "Decision_OS_Product_Contract_Fixation_Wrapper_v0.1.txt"
)


def committed_repository(parent: Path) -> tuple[Path, str]:
    repository = parent / "repo"
    repository.mkdir()
    commands = (
        ("git", "init", "-q", str(repository)),
        ("git", "-C", str(repository), "config", "user.name", "Test User"),
        ("git", "-C", str(repository), "config", "user.email", "test@example.com"),
    )
    for command in commands:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode:
            raise AssertionError(completed.stderr)
    (repository / "tracked.txt").write_text("test\n", encoding="utf-8")
    for command in (
        ("git", "-C", str(repository), "add", "tracked.txt"),
        ("git", "-C", str(repository), "commit", "-qm", "initial"),
    ):
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode:
            raise AssertionError(completed.stderr)
    head = subprocess.run(
        ("git", "-C", str(repository), "rev-parse", "HEAD"),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return repository, head


class OrdinaryUserPathCoordinatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository, self.head = committed_repository(self.root)
        self.guided = GuidedIntakeController(self.repository)
        self.coordinator = OrdinaryUserPathCoordinator(
            self.repository,
            self.guided,
        )
        self.source = SOURCE_PATH.read_bytes()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def prepare(self, *, key: str | None = None, filename: str | None = None):
        return self.coordinator.prepare(
            filename=filename or SOURCE_PATH.name,
            source_bytes=self.source,
            source_byte_size=len(self.source),
            source_sha256=sha256_bytes(self.source),
            expected_repository_identity=self.head,
            expected_active_request_id=None,
            idempotency_key=key or str(uuid.uuid4()),
        )

    @staticmethod
    def fix_request(panel: dict[str, object], key: str | None = None) -> dict[str, str]:
        source = panel["source_identity"]
        technical = panel["technical_details"]
        return {
            "preparation_id": panel["preparation_id"],
            "expected_repository_identity": panel["repository_identity"],
            "expected_source_sha256": source["sha256"],
            "expected_request_id": technical["request_id"],
            "expected_draft_id": technical["draft_id"],
            "expected_interpretation_sha256": technical[
                "interpretation_sha256"
            ],
            "idempotency_key": key or str(uuid.uuid4()),
        }

    def test_prepare_maps_native_interpretation_to_five_field_review(self) -> None:
        panel = self.prepare()

        self.assertEqual("REVIEW_READY", panel["state"])
        self.assertEqual("Ready to fix", panel["status_label"])
        self.assertEqual(
            {
                "preserves",
                "completion",
                "must_not_change",
                "unresolved",
                "does_not_authorize",
            },
            set(panel["review"]),
        )
        self.assertEqual([], panel["review"]["unresolved"])
        rendered_review = json.dumps(panel["review"], ensure_ascii=False)
        for internal_term in (
            "PRESERVED",
            "TESTABLE",
            "authority_claim",
            "schema_version",
            "Request ID",
            "Draft ID",
            "Freeze ID",
            "SHA-256",
            "CLEAR ENOUGH TO FREEZE",
            "NEEDS USER CONFIRMATION",
            "HOLD —",
            "UNKNOWN_",
            "Producer label",
        ):
            self.assertNotIn(internal_term, rendered_review)
        self.assertEqual(
            "7503f4b01c7c05c9ec3aed8855c9fd538c66b9b3b38840f423ec41c2101f4dd7",
            panel["technical_details"]["interpretation_sha256"],
        )
        native = self.guided.snapshot()
        self.assertEqual(panel["technical_details"]["request_id"], native["request_identity"]["request_id"])
        self.assertIsNone(native["transfer_receipt"])

    def test_product_contract_family_reaches_ready_and_fixed(self) -> None:
        wrapper = PRODUCT_WRAPPER_PATH.read_bytes()
        begin = b"BEGIN EXACT PRODUCT CONTRACT\n"
        end = b"END EXACT PRODUCT CONTRACT\n"
        source = wrapper[wrapper.index(begin) + len(begin) : wrapper.index(end)]
        panel = self.coordinator.prepare(
            filename="Decision_OS_Product_Contract.md",
            source_bytes=source,
            source_byte_size=len(source),
            source_sha256=sha256_bytes(source),
            expected_repository_identity=self.head,
            expected_active_request_id=None,
            idempotency_key=str(uuid.uuid4()),
        )
        self.assertEqual("REVIEW_READY", panel["state"])
        self.assertEqual(
            "PRODUCT_CONTRACT_APPROVED_CANDIDATE_V0_1",
            panel["source_identity"]["profile"],
        )
        fixed = self.coordinator.fix(**self.fix_request(panel))
        self.assertEqual("FIXED", fixed["state"])
        self.assertEqual(3, json.loads(
            (
                self.repository
                / ".git"
                / "decision-os"
                / "ordinary-user-path-v0.1"
                / "friction"
                / "first-implementation-run.json"
            ).read_bytes()
        )["visible_user_action_count"])

    def test_prepare_same_key_and_payload_is_idempotent(self) -> None:
        key = str(uuid.uuid4())
        first = self.prepare(key=key)
        second = self.prepare(key=key)

        self.assertEqual(first["preparation_id"], second["preparation_id"])
        native = self.guided.snapshot()
        self.assertEqual(1, len(native["request_history"]))
        events = self.guided.store.read_events()
        self.assertEqual(
            ["ORIGINAL_REQUEST_CAPTURED", "PRO_DRAFT_IMPORTED"],
            [event["kind"] for event in events],
        )

    def test_fix_calls_native_freeze_once_and_replays_without_duplicate(self) -> None:
        panel = self.prepare()
        key = str(uuid.uuid4())
        first = self.coordinator.fix(**self.fix_request(panel, key))
        second = self.coordinator.fix(**self.fix_request(panel, key))
        third = self.coordinator.fix(**self.fix_request(panel))

        self.assertEqual("FIXED", first["state"])
        self.assertEqual(first["technical_details"]["freeze"], second["technical_details"]["freeze"])
        self.assertEqual(first["technical_details"]["freeze"], third["technical_details"]["freeze"])
        events = self.guided.store.read_events()
        self.assertEqual(1, sum(event["kind"] == "INTAKE_FROZEN" for event in events))
        self.assertIsNone(self.guided.snapshot()["transfer_receipt"])

    def test_friction_receipt_has_exact_privacy_allowlist(self) -> None:
        panel = self.prepare()
        self.coordinator.fix(**self.fix_request(panel))
        path = (
            self.repository
            / ".git"
            / "decision-os"
            / "ordinary-user-path-v0.1"
            / "friction"
            / "first-implementation-run.json"
        )
        receipt = json.loads(path.read_bytes())
        self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))
        self.assertEqual(
            {
                "schema",
                "run_ordinal",
                "visible_user_actions",
                "visible_user_action_count",
                "repeated_click_count",
                "waiting_intervals_ms",
                "clarification_count",
                "failed_automatic_recovery_count",
                "user_intervention_count",
                "internal_terms_exposed",
            },
            set(receipt),
        )
        self.assertEqual(3, receipt["visible_user_action_count"])
        self.assertEqual([], receipt["internal_terms_exposed"])
        self.assertEqual(
            {"selection_to_review_ready", "fix_to_receipt"},
            set(receipt["waiting_intervals_ms"]),
        )
        self.assertTrue(
            all(
                isinstance(value, int) and value >= 0
                for value in receipt["waiting_intervals_ms"].values()
            )
        )
        rendered = json.dumps(receipt)
        for secret in (
            SOURCE_PATH.name,
            str(self.repository),
            sha256_bytes(self.source),
            panel["preparation_id"],
            panel["review"]["preserves"],
        ):
            self.assertNotIn(secret, rendered)

    def test_compiler_failure_is_persistent_and_dismissal_is_non_mutating(self) -> None:
        key = str(uuid.uuid4())
        with self.assertRaises(OrdinaryUserPathError) as raised:
            self.prepare(key=key, filename="Contract.pdf")
        self.assertEqual("PREP_UNSUPPORTED_EXTENSION", raised.exception.code)
        first = self.coordinator.snapshot()
        second = self.coordinator.snapshot()
        self.assertEqual("CANNOT_FIX_SAFELY", first["state"])
        self.assertEqual(first["action_error"], second["action_error"])
        self.assertEqual([], self.guided.store.read_events())

        dismissed = self.coordinator.dismiss_error(
            error_id=first["action_error"]["error_id"],
            idempotency_key=str(uuid.uuid4()),
        )
        self.assertIsNone(dismissed["action_error"])
        self.assertEqual([], self.guided.store.read_events())

    def test_corrupt_sidecar_state_fails_closed(self) -> None:
        self.prepare()
        before = self.guided.store.read_events()
        self.coordinator.store.state_path.write_bytes(b"{}")

        with self.assertRaises(OrdinaryUserPathError) as raised:
            self.coordinator.snapshot()

        self.assertEqual("ORDINARY_STORE_CORRUPT", raised.exception.code)
        self.assertEqual(before, self.guided.store.read_events())

    def test_transport_and_stale_bindings_fail_before_native_mutation(self) -> None:
        with self.assertRaises(OrdinaryUserPathError) as mismatch:
            self.coordinator.prepare(
                filename=SOURCE_PATH.name,
                source_bytes=self.source,
                source_byte_size=len(self.source) + 1,
                source_sha256=sha256_bytes(self.source),
                expected_repository_identity=self.head,
                expected_active_request_id=None,
                idempotency_key=str(uuid.uuid4()),
            )
        self.assertEqual("PREP_SOURCE_TRANSPORT_MISMATCH", mismatch.exception.code)
        with self.assertRaises(OrdinaryUserPathError) as stale:
            self.coordinator.prepare(
                filename=SOURCE_PATH.name,
                source_bytes=self.source,
                source_byte_size=len(self.source),
                source_sha256=sha256_bytes(self.source),
                expected_repository_identity="0" * 40,
                expected_active_request_id=None,
                idempotency_key=str(uuid.uuid4()),
            )
        self.assertEqual("PREP_STALE_REPOSITORY", stale.exception.code)
        self.assertEqual([], self.guided.store.read_events())

    def test_forward_only_successor_preserves_prior_freeze_history(self) -> None:
        first = self.prepare()
        self.coordinator.fix(**self.fix_request(first))
        first_freeze = self.guided.snapshot()["freeze"]["freeze_id"]
        current_request = self.guided.snapshot()["request_identity"]["request_id"]
        successor = self.coordinator.prepare(
            filename=SOURCE_PATH.name,
            source_bytes=self.source,
            source_byte_size=len(self.source),
            source_sha256=sha256_bytes(self.source),
            expected_repository_identity=self.head,
            expected_active_request_id=current_request,
            idempotency_key=str(uuid.uuid4()),
        )
        self.assertEqual("REVIEW_READY", successor["state"])
        state = self.guided.store.load_state()
        self.assertIn(first_freeze, state["freezes"])
        self.assertEqual(2, len(state["requests"]))

    def test_restart_marks_unstaged_preparation_interruption_for_reselection(self) -> None:
        with patch.object(
            self.guided,
            "prepare_compiled_contract",
            side_effect=RuntimeError("simulated process loss"),
        ):
            with self.assertRaises(RuntimeError):
                self.prepare()
        self.assertEqual(
            "PREPARING",
            self.coordinator.store.load_state()["state"],
        )

        restarted_guided = GuidedIntakeController(self.repository)
        restarted = OrdinaryUserPathCoordinator(
            self.repository,
            restarted_guided,
        )
        restarted.recover_incomplete()
        panel = restarted.snapshot()
        self.assertEqual("CANNOT_FIX_SAFELY", panel["state"])
        self.assertEqual("PREP_INTERRUPTED", panel["action_error"]["code"])
        self.assertEqual([], restarted_guided.store.read_events())

    def test_restart_rolls_forward_native_events_after_state_save_loss(self) -> None:
        with patch.object(
            self.guided.store,
            "save_state",
            side_effect=OSError("simulated state-save loss"),
        ):
            with self.assertRaises(OSError):
                self.prepare()
        self.assertEqual(
            "PREPARING",
            self.coordinator.store.load_state()["state"],
        )
        self.assertEqual(
            ["ORIGINAL_REQUEST_CAPTURED", "PRO_DRAFT_IMPORTED"],
            [event["kind"] for event in self.guided.store.read_events()],
        )

        restarted_guided = GuidedIntakeController(self.repository)
        restarted = OrdinaryUserPathCoordinator(self.repository, restarted_guided)
        restarted.recover_incomplete()
        recovered_state = restarted.store.load_state()
        self.assertEqual("REVIEW_READY", recovered_state["state"], recovered_state)
        self.assertEqual("REVIEW_READY", restarted.snapshot()["state"])
        self.assertEqual(
            ["ORIGINAL_REQUEST_CAPTURED", "PRO_DRAFT_IMPORTED"],
            [event["kind"] for event in restarted_guided.store.read_events()],
        )

    def test_response_loss_after_native_freeze_recovers_without_second_freeze(self) -> None:
        panel = self.prepare()
        native_freeze = self.guided.freeze

        def freeze_then_disconnect():
            native_freeze()
            raise RuntimeError("response lost")

        with patch.object(self.guided, "freeze", side_effect=freeze_then_disconnect):
            fixed = self.coordinator.fix(**self.fix_request(panel))
        self.assertEqual("FIXED", fixed["state"])
        self.assertEqual(
            1,
            sum(
                event["kind"] == "INTAKE_FROZEN"
                for event in self.guided.store.read_events()
            ),
        )

    def test_restart_during_fixing_rolls_forward_verified_native_freeze(self) -> None:
        panel = self.prepare()
        native_freeze = self.guided.freeze

        def freeze_then_interrupt():
            native_freeze()
            raise KeyboardInterrupt("simulated process loss")

        with patch.object(self.guided, "freeze", side_effect=freeze_then_interrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.coordinator.fix(**self.fix_request(panel))
        self.assertEqual("FIXING", self.coordinator.snapshot()["state"])

        restarted_guided = GuidedIntakeController(self.repository)
        restarted = OrdinaryUserPathCoordinator(self.repository, restarted_guided)
        restarted.recover_incomplete()
        self.assertEqual("FIXED", restarted.snapshot()["state"])
        self.assertEqual(
            1,
            sum(
                event["kind"] == "INTAKE_FROZEN"
                for event in restarted_guided.store.read_events()
            ),
        )

    def test_fix_reports_repository_drift_exactly(self) -> None:
        panel = self.prepare()
        (self.repository / "drift.txt").write_text("drift\n", encoding="utf-8")
        subprocess.run(("git", "add", "drift.txt"), cwd=self.repository, check=True)
        subprocess.run(
            ("git", "commit", "-qm", "repository drift"),
            cwd=self.repository,
            check=True,
        )
        with self.assertRaises(OrdinaryUserPathError) as repository_error:
            self.coordinator.fix(**self.fix_request(panel))
        self.assertEqual("FIX_STALE_REPOSITORY", repository_error.exception.code)

    def test_fix_reports_stale_active_request_exactly(self) -> None:
        panel = self.prepare()
        self.guided.capture(
            "Forward-only manual successor",
            supersedes_request_id=panel["technical_details"]["request_id"],
        )
        with self.assertRaises(OrdinaryUserPathError) as raised:
            self.coordinator.fix(**self.fix_request(panel))
        self.assertEqual("FIX_STALE_REQUEST", raised.exception.code)

    def test_fix_reports_stale_active_draft_exactly(self) -> None:
        panel = self.prepare()
        ordinary_state = self.coordinator.store.load_state()
        draft_bytes = self.guided.store.read_blob(
            "drafts",
            ordinary_state["preparation"]["draft_sha256"],
            suffix=".json",
        )
        self.guided.import_draft(
            draft_bytes.decode("utf-8"),
            "MANUAL_REGRESSION_DRAFT",
        )
        with self.assertRaises(OrdinaryUserPathError) as raised:
            self.coordinator.fix(**self.fix_request(panel))
        self.assertEqual("FIX_STALE_DRAFT", raised.exception.code)

    def test_receipt_sidecar_failure_reports_native_success_without_refreeze(self) -> None:
        panel = self.prepare()
        with patch.object(
            self.coordinator.store,
            "store_friction_receipt",
            side_effect=OSError("disk full"),
        ):
            with self.assertRaises(OrdinaryUserPathError) as raised:
                self.coordinator.fix(**self.fix_request(panel))
        self.assertEqual("RECEIPT_PERSISTENCE_FAILED", raised.exception.code)
        failed = self.coordinator.snapshot()
        self.assertEqual("YES", failed["action_error"]["anything_fixed"])
        self.assertNotIn("SELECT_CONTRACT", failed["allowed_actions"])
        events_after_failure = self.guided.store.read_events()
        with self.assertRaises(OrdinaryUserPathError) as blocked_selection:
            self.coordinator.prepare(
                filename=SOURCE_PATH.name,
                source_bytes=self.source,
                source_byte_size=len(self.source),
                source_sha256=sha256_bytes(self.source),
                expected_repository_identity=self.head,
                expected_active_request_id=panel["technical_details"][
                    "request_id"
                ],
                idempotency_key=str(uuid.uuid4()),
            )
        self.assertEqual(
            "RECEIPT_PERSISTENCE_FAILED",
            blocked_selection.exception.code,
        )
        self.assertEqual(events_after_failure, self.guided.store.read_events())
        self.assertEqual(
            1,
            sum(
                event["kind"] == "INTAKE_FROZEN"
                for event in self.guided.store.read_events()
            ),
        )

    def test_native_receipt_identity_mismatch_fails_closed_after_one_freeze(self) -> None:
        panel = self.prepare()
        with patch.object(
            self.guided,
            "verified_current_freeze",
            side_effect=[None, {"current": True, "request_id": "wrong"}],
        ):
            with self.assertRaises(OrdinaryUserPathError) as raised:
                self.coordinator.fix(**self.fix_request(panel))
        self.assertEqual("RECEIPT_IDENTITY_MISMATCH", raised.exception.code)
        self.assertEqual(
            1,
            sum(
                event["kind"] == "INTAKE_FROZEN"
                for event in self.guided.store.read_events()
            ),
        )


if __name__ == "__main__":
    unittest.main()
