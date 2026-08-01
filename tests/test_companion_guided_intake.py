from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from decision_os.companion.guided_intake import (
    AUTHORITY_CLAIM,
    AUTHORITY_STATE,
    DRAFT_SCHEMA,
    EVIDENCE_PACKET_IDENTITY,
    FREEZE_AUTHORITY_STATE,
    TRANSFER_AUTHORITY_STATE,
    GuidedIntakeConflictError,
    GuidedIntakeController,
    GuidedIntakeBusyError,
    GuidedIntakeIntegrityError,
    GuidedIntakeValidationError,
    MAX_ORIGINAL_REQUEST_BYTES,
    canonical_json,
    sha256_bytes,
    strict_json_object,
    structured_sha256,
)
from decision_os.companion.manual_bridge import BridgeSessionController


AMBIGUOUS_REQUEST = (
    "Add a Guided Intake box to the Companion so I can paste an unclear task\n"
    "and get it ready for the next agent. Don’t break the current Runner."
)


def _quote(value: str, occurrence: int = 1) -> dict[str, object]:
    return {
        "kind": "ORIGINAL_REQUEST_QUOTE",
        "quote": value,
        "occurrence": occurrence,
    }


def ambiguous_draft(request: str = AMBIGUOUS_REQUEST) -> dict[str, object]:
    digest = hashlib.sha256(request.encode("utf-8")).hexdigest()
    return {
        "schema_version": DRAFT_SCHEMA,
        "source_request_sha256": digest,
        "objective": {
            "text": (
                "Add a Guided Intake box to the Companion; "
                "paste an unclear task; "
                "get it ready for the next agent"
            ),
            "atoms": [
                {
                    "atom_id": "OBJ-1",
                    "text": "Add a Guided Intake box to the Companion",
                    "support": [
                        _quote("Add a Guided Intake box to the Companion")
                    ],
                },
                {
                    "atom_id": "OBJ-2",
                    "text": "paste an unclear task",
                    "support": [_quote("paste an unclear task")],
                },
                {
                    "atom_id": "OBJ-3",
                    "text": "get it ready for the next agent",
                    "support": [_quote("get it ready for the next agent")],
                },
            ],
        },
        "completion_line": {
            "text": (
                "UNKNOWN — ready for the next agent does not identify the "
                "observable completion state."
            ),
            "testability_status": "UNKNOWN",
            "checks": [],
        },
        "do_not_touch": [
            {
                "item_id": "DNT-1",
                "text": "Don’t break the current Runner.",
                "basis_kind": "USER_EXPLICIT",
                "support": _quote("Don’t break the current Runner."),
            }
        ],
        "unknown": [
            {
                "unknown_id": "UNK-1",
                "type": "MODEL_DETECTED_MISSING_FACT",
                "statement": (
                    "The observable state meant by ready for the next agent "
                    "is not stated."
                ),
                "basis": {
                    "kind": "MODEL_DETECTION",
                    "related_original_quotes": [
                        _quote("get it ready for the next agent")
                    ],
                },
                "affects": ["COMPLETION_LINE"],
                "materiality": "MATERIAL",
                "effect_on_execution": "HOLD_COMPLETION",
                "evidence_required": (
                    "An explicit user choice of the observable completion state."
                ),
                "current_state": "OPEN",
            },
            {
                "unknown_id": "UNK-2",
                "type": "UNVERIFIED_ASSUMPTION_CANDIDATE",
                "statement": (
                    "Readiness may mean frozen intake only or frozen intake "
                    "copied into Manual Bridge."
                ),
                "basis": {
                    "kind": "MODEL_DETECTION",
                    "related_original_quotes": [
                        _quote("get it ready for the next agent")
                    ],
                },
                "affects": ["COMPLETION_LINE"],
                "materiality": "MATERIAL",
                "effect_on_execution": "NEEDS_USER_CONFIRMATION",
                "evidence_required": (
                    "The user's explicit frozen-only or Bridge-transfer choice."
                ),
                "current_state": "OPEN",
            },
        ],
        "authority_claim": "NONE",
        "clarification_candidate": {
            "field": "COMPLETION_LINE",
            "question": (
                "Should ready for the next agent mean a frozen Guided Intake "
                "artifact, or one also copied into Manual Bridge?"
            ),
        },
    }


def clear_draft(request: str = AMBIGUOUS_REQUEST) -> dict[str, object]:
    value = ambiguous_draft(request)
    value["completion_line"] = {
        "text": (
            "Complete when one frozen Guided Intake exists for the captured "
            "request and its request and freeze hashes verify."
        ),
        "testability_status": "TESTABLE",
        "checks": [
            {
                "observable": "One frozen Guided Intake artifact",
                "pass_condition": (
                    "The artifact exists and its request and freeze hashes verify"
                ),
                "evidence_source": "Guided Intake freeze receipt",
            }
        ],
    }
    value["unknown"] = []
    value["clarification_candidate"] = None
    return value


def exact_clear_draft(
    request: str,
    objective_atoms: list[str],
) -> dict[str, object]:
    return {
        "schema_version": DRAFT_SCHEMA,
        "source_request_sha256": sha256_bytes(request.encode("utf-8")),
        "objective": {
            "text": "; ".join(objective_atoms),
            "atoms": [
                {
                    "atom_id": f"OBJ-{index}",
                    "text": atom,
                    "support": [_quote(atom)],
                }
                for index, atom in enumerate(objective_atoms, start=1)
            ],
        },
        "completion_line": {
            "text": "Complete when one bounded artifact exists.",
            "testability_status": "TESTABLE",
            "checks": [
                {
                    "observable": "One bounded artifact",
                    "pass_condition": "One bounded artifact exists",
                    "evidence_source": "Artifact receipt",
                }
            ],
        },
        "do_not_touch": [],
        "unknown": [],
        "authority_claim": "NONE",
        "clarification_candidate": None,
    }


def confirmation_delta() -> dict[str, object]:
    return {
        "completion_line": {
            "text": (
                "Complete when one frozen Guided Intake artifact exists for "
                "the captured request and its request and freeze hashes verify."
            ),
            "testability_status": "TESTABLE",
            "checks": [
                {
                    "observable": "One frozen Guided Intake artifact",
                    "pass_condition": (
                        "The artifact exists and both identity hashes verify"
                    ),
                    "evidence_source": "Guided Intake freeze receipt",
                }
            ],
        },
        "resolve_unknown_ids": ["UNK-1", "UNK-2"],
    }


class RecordingBridge:
    def __init__(self, *, alter: bool = False) -> None:
        self.calls: list[dict[str, object]] = []
        self.alter = alter

    def accept_guided_intake(
        self,
        transfer: dict[str, object],
    ) -> dict[str, object]:
        self.calls.append(deepcopy(transfer))
        hashes = dict(transfer["field_hashes"])
        if self.alter:
            hashes["objective"] = "0" * 64
        receipt_body = {
            "authority_state": TRANSFER_AUTHORITY_STATE,
            "bridge_session_id": "bridge-session-1",
            "field_hashes": hashes,
            "freeze_sha256": transfer["frozen_intake_sha256"],
            "post_transfer_field_hashes": hashes,
            "pre_transfer_field_hashes": dict(
                transfer["field_hashes"]
            ),
            "schema": "guided-intake-bridge-transfer-receipt-v0.1",
            "transfer_result": "TRANSFER_ACCEPTED",
            "transfer_sha256": sha256_bytes(canonical_json(transfer)),
        }
        return {
            "guided_intake_transfer": {
                **receipt_body,
                "receipt_sha256": sha256_bytes(
                    canonical_json(receipt_body)
                ),
            }
        }


class GuidedIntakeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = Path(self.temporary.name) / "repo"
        self.repository.mkdir()
        subprocess.run(
            ("git", "init", "-q"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "config", "user.email", "guided@example.test"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "config", "user.name", "Guided Intake Test"),
            cwd=self.repository,
            check=True,
        )
        (self.repository / "seed.txt").write_text("seed\n", encoding="utf-8")
        subprocess.run(
            ("git", "add", "seed.txt"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "commit", "-qm", "seed"),
            cwd=self.repository,
            check=True,
            env={
                **os.environ,
                "GIT_AUTHOR_DATE": "2026-07-29T00:00:00Z",
                "GIT_COMMITTER_DATE": "2026-07-29T00:00:00Z",
            },
        )
        self.identities = iter(f"id-{index}" for index in range(1, 500))
        self.controller = GuidedIntakeController(
            self.repository,
            clock=lambda: "2026-07-29T00:00:00Z",
            id_factory=lambda: next(self.identities),
        )

    def import_value(self, value: dict[str, object]) -> dict[str, object]:
        return self.controller.import_draft(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")),
            "MANUAL_PRO_DRAFT",
        )

    def capture_and_import_clear(self) -> dict[str, object]:
        self.controller.capture(AMBIGUOUS_REQUEST)
        return self.import_value(clear_draft())

    def confirm_ambiguous(self) -> dict[str, object]:
        captured = self.controller.capture(AMBIGUOUS_REQUEST)
        imported = self.import_value(ambiguous_draft())
        question = imported["active_question"]["question"]
        return self.controller.confirm(
            question,
            "A frozen Guided Intake artifact is sufficient.",
            confirmation_delta(),
        )

    def test_exact_request_identity_preserves_whitespace_and_line_endings(self) -> None:
        request = " \tA\r\nB\nC\r "
        snapshot = self.controller.capture(request)
        identity = snapshot["request_identity"]
        self.assertEqual(snapshot["original_request"], request)
        self.assertEqual(
            identity["sha256"],
            hashlib.sha256(request.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(identity["byte_size"], len(request.encode("utf-8")))
        self.assertEqual(identity["unicode_normalization"], "NONE")
        stored = (
            self.controller.store.root
            / "original-requests"
            / f"{identity['sha256']}.utf8"
        ).read_bytes()
        self.assertEqual(stored, request.encode("utf-8"))

    def test_unicode_is_not_normalized(self) -> None:
        composed = "é"
        decomposed = "e\u0301"
        first = self.controller.capture(composed)
        second = self.controller.capture(
            decomposed,
            first["request_identity"]["request_id"],
        )
        self.assertNotEqual(
            first["request_identity"]["sha256"],
            second["request_identity"]["sha256"],
        )
        self.assertEqual(second["original_request"], decomposed)

    def test_same_content_hashes_the_same_and_one_character_differs(self) -> None:
        first = self.controller.capture("same")
        second = self.controller.capture(
            "same",
            first["request_identity"]["request_id"],
        )
        third = self.controller.capture(
            "same!",
            second["request_identity"]["request_id"],
        )
        self.assertEqual(
            first["request_identity"]["sha256"],
            second["request_identity"]["sha256"],
        )
        self.assertNotEqual(
            second["request_identity"]["sha256"],
            third["request_identity"]["sha256"],
        )

    def test_forward_only_request_correction_requires_exact_supersession(self) -> None:
        first = self.controller.capture("first")
        with self.assertRaisesRegex(
            GuidedIntakeConflictError,
            "explicitly supersede",
        ):
            self.controller.capture("second")
        second = self.controller.capture(
            "second",
            first["request_identity"]["request_id"],
        )
        self.assertEqual(
            second["request_identity"]["supersedes_request_id"],
            first["request_identity"]["request_id"],
        )
        self.assertEqual(len(second["request_history"]), 2)
        first_path = (
            self.controller.store.root
            / "original-requests"
            / f"{first['request_identity']['sha256']}.utf8"
        )
        self.assertEqual(first_path.read_text(encoding="utf-8"), "first")

    def test_empty_oversized_and_invalid_surrogate_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "ORIGINAL REQUEST EMPTY",
        ):
            self.controller.capture(" \n\t")
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "ORIGINAL REQUEST TOO LARGE",
        ):
            self.controller.capture("a" * (MAX_ORIGINAL_REQUEST_BYTES + 1))
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "ORIGINAL REQUEST ENCODING",
        ):
            self.controller.capture("\ud800")

    def test_exact_size_limit_accepts_65536_utf8_bytes(self) -> None:
        snapshot = self.controller.capture("x" * MAX_ORIGINAL_REQUEST_BYTES)
        self.assertEqual(
            snapshot["request_identity"]["byte_size"],
            MAX_ORIGINAL_REQUEST_BYTES,
        )

    def test_copy_for_pro_binds_exact_request_and_grants_no_authority(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        snapshot = self.controller.copy_for_pro()
        prompt = snapshot["copy_for_pro_prompt"]
        self.assertIn(AMBIGUOUS_REQUEST, prompt)
        self.assertIn(snapshot["request_identity"]["sha256"], prompt)
        self.assertIn(AUTHORITY_CLAIM, prompt)
        self.assertNotIn("start_run(", prompt)

    def test_strict_json_rejects_duplicate_and_unsupported_original(self) -> None:
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "duplicate JSON key",
        ):
            strict_json_object('{"schema_version":"a","schema_version":"b"}')
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        value["original_request"] = "replacement"
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "top-level fields",
        ):
            self.import_value(value)

    def test_source_hash_mismatch_is_rejected(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        value["source_request_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "source request identity mismatch",
        ):
            self.import_value(value)

    def test_objective_quote_ranges_are_exact_utf8_offsets(self) -> None:
        request = "é Add box. Add box."
        self.controller.capture(request)
        value = {
            "schema_version": DRAFT_SCHEMA,
            "source_request_sha256": sha256_bytes(request.encode("utf-8")),
            "objective": {
                "text": "Add box.",
                "atoms": [
                    {
                        "atom_id": "OBJ-1",
                        "text": "Add box.",
                        "support": [_quote("Add box.", 2)],
                    }
                ],
            },
            "completion_line": {
                "text": "Complete when one box exists.",
                "testability_status": "TESTABLE",
                "checks": [
                    {
                        "observable": "one box",
                        "pass_condition": "one box exists",
                        "evidence_source": "box count",
                    }
                ],
            },
            "do_not_touch": [],
            "unknown": [],
            "authority_claim": "NONE",
            "clarification_candidate": None,
        }
        snapshot = self.import_value(value)
        support = snapshot["interpretation"]["objective"]["atoms"][0]["support"][0]
        self.assertEqual(
            request.encode("utf-8")[support["byte_start"] : support["byte_end"]],
            b"Add box.",
        )
        self.assertEqual(support["occurrence"], 2)

    def test_missing_or_wrong_quote_occurrence_fails_closed(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        for quote, occurrence in (("not present", 1), ("paste an unclear task", 2)):
            value = clear_draft()
            value["objective"]["atoms"][1]["support"] = [
                _quote(quote, occurrence)
            ]
            with self.assertRaisesRegex(
                GuidedIntakeValidationError,
                "FIELD PROVENANCE INCOMPLETE",
            ):
                self.import_value(value)

    def test_ambiguous_fixture_needs_one_confirmation_and_preserves_runner(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        snapshot = self.import_value(ambiguous_draft())
        interpretation = snapshot["interpretation"]
        self.assertEqual(interpretation["gate"], "NEEDS USER CONFIRMATION")
        self.assertEqual(
            interpretation["completion_line"]["testability_status"],
            "UNKNOWN",
        )
        self.assertEqual(snapshot["active_question"]["field"], "COMPLETION_LINE")
        self.assertIn(
            "Don’t break the current Runner.",
            [item["text"] for item in interpretation["do_not_touch"]],
        )
        self.assertIn(
            "No Guided Intake action may start the Runner.",
            [item["text"] for item in interpretation["do_not_touch"]],
        )
        self.assertEqual(snapshot["authority_claim"], AUTHORITY_CLAIM)

    def test_confirmation_is_forward_only_and_does_not_grant_authority(self) -> None:
        snapshot = self.confirm_ambiguous()
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "CLEAR ENOUGH TO FREEZE",
        )
        self.assertIsNone(snapshot["active_question"])
        for entry in snapshot["interpretation"]["unknown"]:
            self.assertEqual(entry["current_state"], "RESOLVED_FORWARD_ONLY")
            self.assertEqual(
                entry["resolution"]["evidence_kind"],
                "USER_CONFIRMATION",
            )
        self.assertEqual(snapshot["authority_claim"], AUTHORITY_CLAIM)
        draft = next(iter(self.controller.store.load_state()["drafts"].values()))
        self.assertEqual(draft["validation_result"], "NEEDS USER CONFIRMATION")
        state = self.controller.store.load_state()
        events = self.controller.store.read_events()
        confirmation_event = next(
            event
            for event in events
            if event["kind"] == "USER_CONFIRMATION_RECORDED"
        )
        receipt_sha = confirmation_event["payload"][
            "confirmation_sha256"
        ]
        receipt = self.controller.store.read_blob(
            "receipts",
            receipt_sha,
            suffix=".json",
        )
        self.assertEqual(
            receipt,
            canonical_json(state["confirmations"][0]),
        )

    def test_reimport_preserves_confirmation_and_unknown_history(self) -> None:
        confirmed = self.confirm_ambiguous()
        prior_history = deepcopy(confirmed["confirmation_history"])
        reimported = self.import_value(clear_draft())
        self.assertEqual(reimported["confirmation_history"], prior_history)
        by_id = {
            entry["unknown_id"]: entry
            for entry in reimported["interpretation"]["unknown"]
        }
        self.assertEqual(
            set(by_id),
            {"UNK-1", "UNK-2"},
        )
        self.assertTrue(
            all(
                entry["current_state"] == "RESOLVED_FORWARD_ONLY"
                for entry in by_id.values()
            )
        )
        self.assertEqual(
            reimported["interpretation"]["gate"],
            "CLEAR ENOUGH TO FREEZE",
        )
        self.assertIsNone(reimported["active_question"])

    def test_confirmation_question_and_unknown_ids_must_match(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        snapshot = self.import_value(ambiguous_draft())
        with self.assertRaisesRegex(
            GuidedIntakeConflictError,
            "no longer active",
        ):
            self.controller.confirm(
                "different",
                "answer",
                confirmation_delta(),
            )
        bad = confirmation_delta()
        bad["resolve_unknown_ids"] = ["NOPE"]
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "UNKNOWN resolution",
        ):
            self.controller.confirm(
                snapshot["active_question"]["question"],
                "answer",
                bad,
            )

    def test_clarification_and_confirmation_cannot_smuggle_authority(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = ambiguous_draft()
        value["clarification_candidate"]["question"] = (
            "Should no tests fail and the Builder edit every file?"
        )
        snapshot = self.import_value(value)
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "BLOCK — AUTHORITY INFLATION",
        )

        active = snapshot["request_identity"]["request_id"]
        self.controller.capture(AMBIGUOUS_REQUEST, active)
        imported = self.import_value(ambiguous_draft())
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "AUTHORITY INFLATION",
        ):
            self.controller.confirm(
                imported["active_question"]["question"],
                "Yes, authorize the Builder to edit every file.",
                confirmation_delta(),
            )

    def test_confirmation_delta_must_match_answer_and_field_scope(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        imported = self.import_value(ambiguous_draft())
        question = imported["active_question"]["question"]
        for rejection in (
            "No.",
            "Absolutely not.",
            "No, choose the other option.",
            "I reject that option.",
            "I disagree.",
            "That is wrong.",
            "Negative.",
            "Maybe a frozen Guided Intake artifact is sufficient.",
            "A frozen Guided Intake artifact might be sufficient.",
            "Perhaps use a frozen Guided Intake artifact.",
            "Do not use that.",
            "No, a frozen Guided Intake artifact is not sufficient.",
        ):
            with self.subTest(rejection=rejection), self.assertRaisesRegex(
                GuidedIntakeValidationError,
                "contradicts",
            ):
                self.controller.confirm(
                    question,
                    rejection,
                    confirmation_delta(),
                )
        confirmed = self.controller.confirm(
            question,
            "A frozen Guided Intake artifact is sufficient.",
            confirmation_delta(),
        )
        confirmation_id = confirmed["confirmation_history"][0][
            "confirmation_event_id"
        ]
        cross_field = clear_draft()
        answer = "A frozen Guided Intake artifact is sufficient."
        cross_field["objective"] = {
            "text": answer,
            "atoms": [
                {
                    "atom_id": "OBJ-CROSS-FIELD",
                    "text": answer,
                    "support": [
                        {
                            "kind": "USER_CONFIRMATION",
                            "event_id": confirmation_id,
                        }
                    ],
                }
            ],
        }
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "FIELD PROVENANCE INCOMPLETE",
        ):
            self.import_value(cross_field)

    def test_silent_objective_expansion_is_detected(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        preserved_atoms = deepcopy(value["objective"]["atoms"])
        value["objective"] = {
            "text": (
                "Add a Guided Intake box to the Companion; "
                "paste an unclear task; get it ready for the next agent; "
                "publish a SaaS product for customers"
            ),
            "atoms": [
                *preserved_atoms,
                {
                    "atom_id": "OBJ-ADDED",
                    "text": (
                        "Add a Guided Intake box to the Companion and "
                        "publish a SaaS product for customers"
                    ),
                    "support": [
                        _quote("Add a Guided Intake box to the Companion")
                    ],
                }
            ],
        }
        snapshot = self.import_value(value)
        self.assertEqual(
            snapshot["interpretation"]["objective"]["fidelity_status"],
            "EXPANDED",
        )
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "BLOCK — AUTHORITY INFLATION",
        )

    def test_substituted_objective_is_detected(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        value["objective"] = {
            "text": "Measure lunar temperatures.",
            "atoms": [
                {
                    "atom_id": "OBJ-1",
                    "text": "Measure lunar temperatures.",
                    "support": [
                        _quote("Add a Guided Intake box to the Companion")
                    ],
                }
            ],
        }
        snapshot = self.import_value(value)
        self.assertEqual(
            snapshot["interpretation"]["objective"]["fidelity_status"],
            "SUBSTITUTED",
        )

    def test_objective_addition_and_removal_both_fail_closed(self) -> None:
        request = "Create a red widget and create a blue dashboard."
        self.controller.capture(request)
        removed = exact_clear_draft(
            request,
            ["Create a red widget"],
        )
        snapshot = self.import_value(removed)
        self.assertEqual(
            snapshot["interpretation"]["objective"]["fidelity_status"],
            "SUBSTITUTED",
        )
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "HOLD — OBJECTIVE FIDELITY FAILURE",
        )

        active = snapshot["request_identity"]["request_id"]
        uncertain_request = (
            "Create a widget and maybe create a dashboard."
        )
        self.controller.capture(uncertain_request, active)
        uncertain = exact_clear_draft(
            uncertain_request,
            ["Create a widget"],
        )
        uncertain_snapshot = self.import_value(uncertain)
        self.assertEqual(
            uncertain_snapshot["interpretation"]["gate"],
            "HOLD — OBJECTIVE FIDELITY FAILURE",
        )
        represented_but_untyped = exact_clear_draft(
            uncertain_request,
            ["Create a widget", "maybe create a dashboard"],
        )
        untyped_snapshot = self.import_value(
            represented_but_untyped
        )
        self.assertEqual(
            untyped_snapshot["interpretation"]["objective"][
                "fidelity_status"
            ],
            "UNKNOWN",
        )
        self.assertEqual(
            untyped_snapshot["interpretation"]["gate"],
            "HOLD — OBJECTIVE UNKNOWN",
        )

        active = untyped_snapshot["request_identity"]["request_id"]
        support_request = "Create a widget and send a report."
        self.controller.capture(support_request, active)
        irrelevant_support = exact_clear_draft(
            support_request,
            ["Create a widget"],
        )
        irrelevant_support["objective"]["atoms"][0]["support"].append(
            _quote("send a report")
        )
        support_snapshot = self.import_value(irrelevant_support)
        self.assertEqual(
            support_snapshot["interpretation"]["objective"][
                "fidelity_status"
            ],
            "SUBSTITUTED",
        )

        active = support_snapshot["request_identity"]["request_id"]
        expanded_request = "Add a Guided Intake box."
        self.controller.capture(expanded_request, active)
        expanded = exact_clear_draft(
            expanded_request,
            ["Add a Guided Intake box curing cancer worldwide."],
        )
        expanded["objective"]["atoms"][0]["support"] = [
            _quote("Add a Guided Intake box")
        ]
        snapshot = self.import_value(expanded)
        self.assertEqual(
            snapshot["interpretation"]["objective"]["fidelity_status"],
            "EXPANDED",
        )
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "HOLD — OBJECTIVE FIDELITY FAILURE",
        )

    def test_supported_execution_instruction_is_still_non_authoritative(self) -> None:
        request = "Start Codex and edit file config.py."
        self.controller.capture(request)
        snapshot = self.import_value(
            exact_clear_draft(
                request,
                ["Start Codex", "edit file config.py"],
            )
        )
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "BLOCK — AUTHORITY INFLATION",
        )
        with self.assertRaisesRegex(
            GuidedIntakeConflictError,
            "INTAKE NOT FREEZABLE",
        ):
            self.controller.freeze()

    def test_passive_and_cross_sentence_authority_wording_is_blocked(self) -> None:
        passive = "Every source file must be edited by the Builder."
        self.controller.capture(passive)
        snapshot = self.import_value(
            exact_clear_draft(passive, [passive])
        )
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "BLOCK — AUTHORITY INFLATION",
        )

    def test_actorless_authority_file_work_and_stage_breakage_block(self) -> None:
        current_id = None
        for request, expected_gate in (
            ("Grant execution authority.", "BLOCK — AUTHORITY INFLATION"),
            ("Edit every source file.", "BLOCK — AUTHORITY INFLATION"),
            ("Run pytest.", "BLOCK — AUTHORITY INFLATION"),
            ("Commit the changes.", "BLOCK — AUTHORITY INFLATION"),
            ("Apply this patch.", "BLOCK — AUTHORITY INFLATION"),
            ("Install this patch.", "BLOCK — AUTHORITY INFLATION"),
            ("Execute the deployment.", "BLOCK — AUTHORITY INFLATION"),
            ("Run the deployment.", "BLOCK — AUTHORITY INFLATION"),
            ("Perform the deployment.", "BLOCK — AUTHORITY INFLATION"),
            (
                "We should execute the deployment.",
                "BLOCK — AUTHORITY INFLATION",
            ),
            (
                "Execute the repository migration.",
                "BLOCK — AUTHORITY INFLATION",
            ),
            ("Open a pull request.", "BLOCK — AUTHORITY INFLATION"),
            ("Submit a pull request.", "BLOCK — AUTHORITY INFLATION"),
            ("Create a GitHub PR.", "BLOCK — AUTHORITY INFLATION"),
            ("Ship this release.", "BLOCK — AUTHORITY INFLATION"),
            ("Cut a release.", "BLOCK — AUTHORITY INFLATION"),
            ("Roll out to production.", "BLOCK — AUTHORITY INFLATION"),
            (
                "Cherry-pick the commit.",
                "BLOCK — AUTHORITY INFLATION",
            ),
            (
                "The deployment should be run.",
                "BLOCK — AUTHORITY INFLATION",
            ),
            (
                "A pull request should be submitted.",
                "BLOCK — AUTHORITY INFLATION",
            ),
            (
                "The release should be cut.",
                "BLOCK — AUTHORITY INFLATION",
            ),
            (
                "The commit should be cherry-picked.",
                "BLOCK — AUTHORITY INFLATION",
            ),
            (
                "Prepare the repository for release.",
                "BLOCK — AUTHORITY INFLATION",
            ),
            (
                "Create the production release in the repository.",
                "BLOCK — AUTHORITY INFLATION",
            ),
            ("Break Stage 1 behavior.", "HOLD — DO NOT TOUCH UNKNOWN"),
        ):
            captured = self.controller.capture(request, current_id)
            current_id = captured["request_identity"]["request_id"]
            snapshot = self.import_value(
                exact_clear_draft(request, [request])
            )
            self.assertEqual(
                snapshot["interpretation"]["gate"],
                expected_gate,
            )

        for request in (
            "Create release notes.",
            "Summarize the deployment plan.",
            "Describe the repository boundary.",
        ):
            captured = self.controller.capture(request, current_id)
            current_id = captured["request_identity"]["request_id"]
            snapshot = self.import_value(
                exact_clear_draft(request, [request])
            )
            self.assertEqual(
                snapshot["interpretation"]["gate"],
                "CLEAR ENOUGH TO FREEZE",
            )

        active = snapshot["request_identity"]["request_id"]
        separated = (
            "Do not log diagnostics. Codex edits every file."
        )
        self.controller.capture(separated, active)
        value = exact_clear_draft(
            separated,
            ["Codex edits every file."],
        )
        value["do_not_touch"] = [
            {
                "item_id": "DNT-LOG",
                "text": "Do not log diagnostics.",
                "basis_kind": "USER_EXPLICIT",
                "support": _quote("Do not log diagnostics."),
            }
        ]
        snapshot = self.import_value(value)
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "BLOCK — AUTHORITY INFLATION",
        )

    def test_unsupported_authority_is_blocked(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        value["authority_claim"] = "BUILDER_AUTHORIZED"
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "AUTHORITY INFLATION",
        ):
            self.import_value(value)

    def test_all_completion_statuses_remain_distinct(self) -> None:
        current_id = None
        for index, status in enumerate(
            ["PARTIALLY TESTABLE", "SUBJECTIVE", "MISSING", "UNKNOWN"]
        ):
            with self.subTest(status=status):
                request = AMBIGUOUS_REQUEST
                captured = self.controller.capture(request, current_id)
                current_id = captured["request_identity"]["request_id"]
                value = clear_draft(request)
                value["completion_line"] = {
                    "text": "" if status == "MISSING" else status,
                    "testability_status": status,
                    "checks": [],
                }
                value["clarification_candidate"] = None
                imported = self.controller.import_draft(
                    json.dumps(value, ensure_ascii=False),
                    f"producer-{index}",
                )
                self.assertEqual(
                    imported["interpretation"]["completion_line"][
                        "testability_status"
                    ],
                    status,
                )
                self.assertEqual(
                    imported["interpretation"]["gate"],
                    "HOLD — COMPLETION LINE UNKNOWN",
                )

    def test_completion_requires_observable_predicate_and_evidence(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        for text, check in (
            (
                "Complete when everyone is happy.",
                {
                    "observable": "General sentiment",
                    "pass_condition": "Everyone is happy",
                    "evidence_source": "Team opinion",
                },
            ),
            (
                "Complete when the result feels good.",
                {
                    "observable": "Quality",
                    "pass_condition": "The result feels good",
                    "evidence_source": "Opinion",
                },
            ),
        ):
            with self.subTest(text=text):
                value = clear_draft()
                value["completion_line"] = {
                    "text": text,
                    "testability_status": "TESTABLE",
                    "checks": [check],
                }
                snapshot = self.import_value(value)
                self.assertEqual(
                    snapshot["interpretation"]["completion_line"][
                        "testability_status"
                    ],
                    "SUBJECTIVE",
                )
                self.assertEqual(
                    snapshot["interpretation"]["gate"],
                    "HOLD — COMPLETION LINE UNKNOWN",
                )

    def test_completion_cannot_assign_builder_or_codex_execution(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        for text in (
            "Complete when Codex starts and Builder deploys production.",
            "Complete when Builder changes every file.",
        ):
            value = clear_draft()
            value["completion_line"] = {
                "text": text,
                "testability_status": "TESTABLE",
                "checks": [
                    {
                        "observable": "One deployment event",
                        "pass_condition": "One event is recorded",
                        "evidence_source": "Event log",
                    }
                ],
            }
            with self.subTest(text=text), self.assertRaisesRegex(
                GuidedIntakeValidationError,
                "AUTHORITY INFLATION",
            ):
                self.import_value(value)

    def test_completion_line_must_bind_to_its_structural_check(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        for text, pass_condition, evidence_source in (
            (
                "Complete when stakeholders love the artifact.",
                "The artifact exists",
                "Artifact receipt",
            ),
            (
                "Complete when one artifact is delightful.",
                "One artifact is delightful",
                "Artifact review record",
            ),
            (
                "Complete when one artifact is magnificent.",
                "One artifact is magnificent",
                "Artifact review record",
            ),
            (
                "Complete when one artifact is excellent.",
                "One artifact is excellent",
                "Artifact review record",
            ),
            (
                "Complete when one artifact is beautiful.",
                "One artifact is beautiful",
                "Artifact review record",
            ),
            (
                "Complete when one artifact is polished.",
                "One artifact is polished",
                "Artifact review record",
            ),
            (
                "Complete when one artifact is professional.",
                "One artifact is professional",
                "Artifact review record",
            ),
            (
                "Complete when one artifact is intuitive.",
                "One artifact is intuitive",
                "Artifact review record",
            ),
            (
                "Complete when one artifact remains magnificent.",
                "One artifact remains magnificent",
                "Artifact review record",
            ),
            (
                "Complete when one artifact passes as excellent.",
                "One artifact passes as excellent",
                "Artifact review record",
            ),
            (
                "Complete when one artifact is present and beautiful.",
                "One artifact is present and beautiful",
                "Artifact review record",
            ),
            (
                "Complete when one polished artifact exists.",
                "One polished artifact exists",
                "Artifact review record",
            ),
            (
                "Complete when one artifact is present, beautiful.",
                "One artifact is present, beautiful",
                "Artifact state record",
            ),
            (
                "Complete when one artifact remains open but beautiful.",
                "One artifact remains open but beautiful",
                "Artifact state record",
            ),
            (
                "Complete when one artifact remains open despite being beautiful.",
                "One artifact remains open despite being beautiful",
                "Artifact state record",
            ),
        ):
            value = clear_draft()
            value["completion_line"] = {
                "text": text,
                "testability_status": "TESTABLE",
                "checks": [
                    {
                        "observable": "One bounded artifact",
                        "pass_condition": pass_condition,
                        "evidence_source": evidence_source,
                    }
                ],
            }
            snapshot = self.import_value(value)
            self.assertEqual(
                snapshot["interpretation"]["completion_line"][
                    "testability_status"
                ],
                "SUBJECTIVE",
            )
            self.assertEqual(
                snapshot["interpretation"]["gate"],
                "HOLD — COMPLETION LINE UNKNOWN",
            )

    def test_each_bounded_completion_condition_requires_check_coverage(
        self,
    ) -> None:
        request = "Create a widget."
        self.controller.capture(request)
        value = exact_clear_draft(request, ["Create a widget"])
        value["completion_line"] = {
            "text": (
                "Complete when one widget exists and zero tests fail."
            ),
            "testability_status": "TESTABLE",
            "checks": [
                {
                    "observable": "One widget artifact",
                    "pass_condition": "One widget exists",
                    "evidence_source": "Artifact receipt",
                }
            ],
        }
        snapshot = self.import_value(value)
        self.assertEqual(
            snapshot["interpretation"]["completion_line"][
                "testability_status"
            ],
            "PARTIALLY TESTABLE",
        )
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "HOLD — COMPLETION LINE UNKNOWN",
        )

    def test_negation_does_not_mask_later_builder_execution(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        value["completion_line"] = {
            "text": (
                "Complete when no tests fail while Builder edits every "
                "file and one artifact exists."
            ),
            "testability_status": "TESTABLE",
            "checks": [
                {
                    "observable": "One bounded artifact",
                    "pass_condition": (
                        "No tests fail while Builder edits every file "
                        "and one artifact exists"
                    ),
                    "evidence_source": "Artifact test record",
                }
            ],
        }
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "AUTHORITY INFLATION",
        ):
            self.import_value(value)

    def test_all_unknown_types_are_preserved_and_evidence_is_subordinate(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        entries = []
        for index, unknown_type in enumerate(
            [
                "USER_STATED_UNKNOWN",
                "MODEL_DETECTED_MISSING_FACT",
                "CONFLICTING_EVIDENCE",
                "UNVERIFIED_ASSUMPTION_CANDIDATE",
                "FUTURE_OBSERVATION",
            ],
            start=1,
        ):
            basis_kind = {
                "USER_STATED_UNKNOWN": "USER_STATEMENT",
                "MODEL_DETECTED_MISSING_FACT": "MODEL_DETECTION",
                "CONFLICTING_EVIDENCE": "EVIDENCE_CONFLICT",
                "UNVERIFIED_ASSUMPTION_CANDIDATE": (
                    "UNVERIFIED_ASSUMPTION"
                ),
                "FUTURE_OBSERVATION": "FUTURE_OBSERVATION",
            }[unknown_type]
            entries.append(
                {
                    "unknown_id": f"UNK-{index}",
                    "type": unknown_type,
                    "statement": (
                        "paste an unclear task"
                        if unknown_type == "USER_STATED_UNKNOWN"
                        else f"Unknown {index}"
                    ),
                    "basis": {
                        "kind": basis_kind,
                        "related_original_quotes": (
                            [_quote("paste an unclear task")]
                            if unknown_type == "USER_STATED_UNKNOWN"
                            else (
                                [
                                    _quote("paste an unclear task"),
                                    _quote(
                                        "get it ready for the next agent"
                                    ),
                                ]
                                if unknown_type
                                == "CONFLICTING_EVIDENCE"
                                else []
                            )
                        ),
                    },
                    "affects": ["COMPLETION_LINE"],
                    "materiality": (
                        "MATERIAL"
                        if unknown_type == "USER_STATED_UNKNOWN"
                        else "NON_MATERIAL"
                    ),
                    "effect_on_execution": (
                        "HOLD_COMPLETION"
                        if unknown_type == "USER_STATED_UNKNOWN"
                        else "NONE"
                    ),
                    "evidence_required": f"Evidence {index}",
                    "current_state": "OPEN",
                }
            )
        value["unknown"] = entries
        snapshot = self.import_value(value)
        self.assertEqual(
            [entry["type"] for entry in snapshot["interpretation"]["unknown"]],
            [entry["type"] for entry in entries],
        )
        self.assertNotIn("evidence_required", snapshot["interpretation"])
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "HOLD — MATERIAL UNKNOWN UNRESOLVED",
        )

    def test_nonmaterial_model_unknown_remains_visible_in_freeze(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        value["unknown"] = [
            {
                "unknown_id": "UNK-NON-MATERIAL",
                "type": "MODEL_DETECTED_MISSING_FACT",
                "statement": "An optional display label is not stated.",
                "basis": {
                    "kind": "MODEL_DETECTION",
                    "related_original_quotes": [],
                },
                "affects": ["COMPLETION_LINE"],
                "materiality": "NON_MATERIAL",
                "effect_on_execution": "NONE",
                "evidence_required": "Optional label evidence.",
                "current_state": "OPEN",
            }
        ]
        imported = self.import_value(value)
        self.assertEqual(
            imported["interpretation"]["gate"],
            "CLEAR ENOUGH TO FREEZE",
        )
        frozen = self.controller.freeze()
        self.assertEqual(
            frozen["interpretation"]["unknown"][0]["unknown_id"],
            "UNK-NON-MATERIAL",
        )

    def test_unknown_basis_materiality_and_boundary_effects_are_typed(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        invalid_entries = []
        wrong_basis = deepcopy(ambiguous_draft()["unknown"][0])
        wrong_basis["basis"]["kind"] = "USER_STATEMENT"
        invalid_entries.append(wrong_basis)
        material_none = deepcopy(ambiguous_draft()["unknown"][0])
        material_none["effect_on_execution"] = "NONE"
        invalid_entries.append(material_none)
        nonmaterial_boundary = deepcopy(ambiguous_draft()["unknown"][0])
        nonmaterial_boundary["affects"] = ["AUTHORITY"]
        nonmaterial_boundary["materiality"] = "NON_MATERIAL"
        nonmaterial_boundary["effect_on_execution"] = "NONE"
        invalid_entries.append(nonmaterial_boundary)
        user_without_quote = deepcopy(ambiguous_draft()["unknown"][0])
        user_without_quote["type"] = "USER_STATED_UNKNOWN"
        user_without_quote["basis"] = {
            "kind": "USER_STATEMENT",
            "related_original_quotes": [],
        }
        invalid_entries.append(user_without_quote)
        for entry in invalid_entries:
            value = clear_draft()
            value["unknown"] = [entry]
            with self.subTest(entry=entry), self.assertRaises(
                GuidedIntakeValidationError
            ):
                self.import_value(value)

        active = self.controller.snapshot()["request_identity"]["request_id"]
        stated_request = (
            "Create a widget. The required output is unknown."
        )
        self.controller.capture(stated_request, active)
        stated = exact_clear_draft(
            stated_request,
            [
                "Create a widget",
                "The required output is unknown",
            ],
        )
        stated["unknown"] = [
            {
                "unknown_id": "UNK-STATED",
                "type": "USER_STATED_UNKNOWN",
                "statement": "The required output is unknown.",
                "basis": {
                    "kind": "USER_STATEMENT",
                    "related_original_quotes": [
                        _quote("The required output is unknown.")
                    ],
                },
                "affects": ["COMPLETION_LINE"],
                "materiality": "NON_MATERIAL",
                "effect_on_execution": "NONE",
                "evidence_required": "The required output definition.",
                "current_state": "OPEN",
            }
        ]
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "must be material",
        ):
            self.import_value(stated)

        spoofed = exact_clear_draft(
            stated_request,
            [
                "Create a widget",
                "The required output is unknown",
            ],
        )
        spoofed["unknown"] = [
            {
                "unknown_id": "UNK-SPOOF",
                "type": "MODEL_DETECTED_MISSING_FACT",
                "statement": (
                    "Whether the future production deployment succeeds."
                ),
                "basis": {
                    "kind": "MODEL_DETECTION",
                    "related_original_quotes": [],
                },
                "affects": ["COMPLETION_LINE"],
                "materiality": "MATERIAL",
                "effect_on_execution": "HOLD_COMPLETION",
                "evidence_required": (
                    "The user's explicit confirmation of completion."
                ),
                "current_state": "OPEN",
            }
        ]
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "does not match its evidence",
        ):
            self.import_value(spoofed)

    def test_user_stated_uncertainty_cannot_be_omitted_or_retyped(
        self,
    ) -> None:
        current_id = None
        for request, atoms, unknown in (
            (
                "Create a widget and the platform is unknown.",
                ["Create a widget", "the platform is unknown"],
                [],
            ),
            (
                "Create a widget and maybe create a dashboard.",
                ["Create a widget", "maybe create a dashboard"],
                [
                    {
                        "unknown_id": "UNK-RETYPED",
                        "type": "MODEL_DETECTED_MISSING_FACT",
                        "statement": "Maybe create a dashboard.",
                        "basis": {
                            "kind": "MODEL_DETECTION",
                            "related_original_quotes": [
                                _quote("maybe create a dashboard")
                            ],
                        },
                        "affects": ["OBJECTIVE"],
                        "materiality": "NON_MATERIAL",
                        "effect_on_execution": "NONE",
                        "evidence_required": "Optional dashboard intent.",
                        "current_state": "OPEN",
                    }
                ],
            ),
            (
                "Create a widget and I don't know which platform.",
                ["Create a widget", "I don't know which platform"],
                [],
            ),
            (
                "Create a widget and the platform is TBD.",
                ["Create a widget", "the platform is TBD"],
                [],
            ),
            (
                "Create a widget and the platform remains undecided.",
                ["Create a widget", "the platform remains undecided"],
                [],
            ),
            (
                "Create a widget and the platform is unclear.",
                ["Create a widget", "the platform is unclear"],
                [],
            ),
            (
                "Create a widget and the platform is to be determined.",
                [
                    "Create a widget",
                    "the platform is to be determined",
                ],
                [],
            ),
            (
                "Create a widget and the platform is pending.",
                ["Create a widget", "the platform is pending"],
                [],
            ),
            (
                "Create a widget and the platform remains pending.",
                ["Create a widget", "the platform remains pending"],
                [],
            ),
        ):
            with self.subTest(request=request):
                captured = self.controller.capture(request, current_id)
                current_id = captured["request_identity"]["request_id"]
                value = exact_clear_draft(request, atoms)
                value["unknown"] = unknown
                snapshot = self.import_value(value)
                self.assertEqual(
                    snapshot["interpretation"]["objective"][
                        "fidelity_status"
                    ],
                    "UNKNOWN",
                )
                self.assertEqual(
                    snapshot["interpretation"]["gate"],
                    "HOLD — OBJECTIVE UNKNOWN",
                )
                with self.assertRaisesRegex(
                    GuidedIntakeConflictError,
                    "INTAKE NOT FREEZABLE",
                ):
                    self.controller.freeze()

        literal_request = "Render the label UNKNOWN."
        captured = self.controller.capture(literal_request, current_id)
        current_id = captured["request_identity"]["request_id"]
        literal = self.import_value(
            exact_clear_draft(literal_request, [literal_request])
        )
        self.assertEqual(
            literal["interpretation"]["gate"],
            "CLEAR ENOUGH TO FREEZE",
        )

    def test_material_unknown_without_bounded_question_holds(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        entry = ambiguous_draft()["unknown"][0]
        value["unknown"] = [entry]
        value["clarification_candidate"] = None
        snapshot = self.import_value(value)
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "HOLD — MATERIAL UNKNOWN UNRESOLVED",
        )
        with self.assertRaisesRegex(
            GuidedIntakeConflictError,
            "INTAKE NOT FREEZABLE",
        ):
            self.controller.freeze()

    def test_open_material_unknown_cannot_disappear_on_reimport(self) -> None:
        request = "Build a widget."
        self.controller.capture(request)
        first = exact_clear_draft(request, [request])
        first["unknown"] = [
            {
                "unknown_id": "UNK-M",
                "type": "MODEL_DETECTED_MISSING_FACT",
                "statement": "The required widget boundary is unavailable.",
                "basis": {
                    "kind": "MODEL_DETECTION",
                    "related_original_quotes": [_quote(request)],
                },
                "affects": ["OBJECTIVE"],
                "materiality": "MATERIAL",
                "effect_on_execution": "HOLD_OBJECTIVE",
                "evidence_required": "External boundary evidence.",
                "current_state": "OPEN",
            }
        ]
        held = self.import_value(first)
        self.assertEqual(
            held["interpretation"]["gate"],
            "HOLD — MATERIAL UNKNOWN UNRESOLVED",
        )
        second = self.import_value(
            exact_clear_draft(request, [request])
        )
        self.assertEqual(
            [item["unknown_id"] for item in second["interpretation"]["unknown"]],
            ["UNK-M"],
        )
        self.assertEqual(
            second["interpretation"]["gate"],
            "HOLD — MATERIAL UNKNOWN UNRESOLVED",
        )

    def test_external_or_future_unknown_cannot_be_resolved_by_intent(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        value["unknown"] = [
            {
                "unknown_id": "UNK-FUTURE",
                "type": "FUTURE_OBSERVATION",
                "statement": "The future test result is unavailable.",
                "basis": {
                    "kind": "FUTURE_OBSERVATION",
                    "related_original_quotes": [],
                },
                "affects": ["COMPLETION_LINE"],
                "materiality": "MATERIAL",
                "effect_on_execution": "HOLD_COMPLETION",
                "evidence_required": "A future test run.",
                "current_state": "OPEN",
            }
        ]
        value["clarification_candidate"] = {
            "field": "COMPLETION_LINE",
            "question": "Will the future tests pass?",
        }
        snapshot = self.import_value(value)
        self.assertIsNone(snapshot["active_question"])
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "HOLD — MATERIAL UNKNOWN UNRESOLVED",
        )

    def test_model_cannot_import_a_resolved_unknown(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        entry = ambiguous_draft()["unknown"][0]
        entry["current_state"] = "RESOLVED_FORWARD_ONLY"
        value["unknown"] = [entry]
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "UNKNOWN RESOLUTION EVIDENCE",
        ):
            self.import_value(value)

    def test_inferred_do_not_touch_candidate_requires_confirmation(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        value["do_not_touch"].append(
            {
                "item_id": "DNT-2",
                "text": "Preserve a possible adjacent surface.",
                "basis_kind": "INFERRED_SAFETY_CANDIDATE",
            }
        )
        value["clarification_candidate"] = {
            "field": "DO_NOT_TOUCH",
            "question": "Should the adjacent surface be protected?",
        }
        snapshot = self.import_value(value)
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "NEEDS USER CONFIRMATION",
        )
        self.assertEqual(snapshot["active_question"]["field"], "DO_NOT_TOUCH")

    def test_objective_unknown_can_only_narrow_with_explicit_confirmation(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        value["objective"] = {
            "text": "UNKNOWN — the owned objective surface is not bounded.",
            "atoms": [],
        }
        value["unknown"] = [
            {
                "unknown_id": "UNK-OBJ",
                "type": "MODEL_DETECTED_MISSING_FACT",
                "statement": "The owned objective surface is not bounded.",
                "basis": {
                    "kind": "MODEL_DETECTION",
                    "related_original_quotes": [],
                },
                "affects": ["OBJECTIVE"],
                "materiality": "MATERIAL",
                "effect_on_execution": "HOLD_OBJECTIVE",
                "evidence_required": "An explicit bounded objective.",
                "current_state": "OPEN",
            }
        ]
        value["clarification_candidate"] = {
            "field": "OBJECTIVE",
            "question": "Should the objective be limited to one Guided Intake surface?",
        }
        before = self.import_value(value)
        self.assertEqual(
            before["interpretation"]["objective"]["fidelity_status"],
            "UNKNOWN",
        )
        self.assertEqual(
            before["interpretation"]["gate"],
            "NEEDS USER CONFIRMATION",
        )
        after = self.controller.confirm(
            before["active_question"]["question"],
            "Limit the objective to one Guided Intake surface.",
            {
                "objective": {
                    "text": "Limit the objective to one Guided Intake surface.",
                    "atoms": [
                        {
                            "atom_id": "OBJ-CONF-1",
                            "text": (
                                "Limit the objective to one Guided Intake surface."
                            ),
                            "support": [
                                {
                                    "kind": "USER_CONFIRMATION",
                                    "event_id": "ACTIVE_CONFIRMATION",
                                }
                            ],
                        }
                    ],
                },
                "resolve_unknown_ids": ["UNK-OBJ"],
            },
        )
        self.assertEqual(
            after["interpretation"]["objective"]["fidelity_status"],
            "NARROWED WITH EXPLICIT USER APPROVAL",
        )
        self.assertEqual(
            after["interpretation"]["gate"],
            "CLEAR ENOUGH TO FREEZE",
        )

    def test_completion_can_observe_an_explicit_human_confirmation_event(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        value = clear_draft()
        value["completion_line"] = {
            "text": (
                "Complete when Shin records approval of the displayed boundary."
            ),
            "testability_status": "TESTABLE",
            "checks": [
                {
                    "observable": "A Shin approval event",
                    "pass_condition": (
                        "One event names Shin and the displayed boundary hash"
                    ),
                    "evidence_source": "Forward-only confirmation event log",
                }
            ],
        }
        snapshot = self.import_value(value)
        self.assertEqual(
            snapshot["interpretation"]["completion_line"][
                "testability_status"
            ],
            "TESTABLE",
        )

    def test_objective_conflict_with_explicit_do_not_touch_holds(self) -> None:
        request = (
            "Modify the current Runner behavior. "
            "Do not modify the current Runner behavior."
        )
        self.controller.capture(request)
        value = {
            "schema_version": DRAFT_SCHEMA,
            "source_request_sha256": sha256_bytes(request.encode("utf-8")),
            "objective": {
                "text": "Modify the current Runner behavior.",
                "atoms": [
                    {
                        "atom_id": "OBJ-1",
                        "text": "Modify the current Runner behavior.",
                        "support": [_quote("Modify the current Runner behavior.")],
                    }
                ],
            },
            "completion_line": {
                "text": "Complete when one bounded representation exists.",
                "testability_status": "TESTABLE",
                "checks": [
                    {
                        "observable": "one representation",
                        "pass_condition": "one representation exists",
                        "evidence_source": "artifact receipt",
                    }
                ],
            },
            "do_not_touch": [
                {
                    "item_id": "DNT-1",
                    "text": "Do not modify the current Runner behavior.",
                    "basis_kind": "USER_EXPLICIT",
                    "support": _quote(
                        "Do not modify the current Runner behavior."
                    ),
                }
            ],
            "unknown": [],
            "authority_claim": "NONE",
            "clarification_candidate": None,
        }
        snapshot = self.import_value(value)
        self.assertTrue(snapshot["interpretation"]["do_not_touch_conflict"])
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "HOLD — DO NOT TOUCH UNKNOWN",
        )

    def test_preservation_of_protected_object_is_not_a_conflict(self) -> None:
        objective = "Preserve the exact audit ledger identity."
        do_not_touch = "Do not modify the exact audit ledger."
        request = f"{objective} {do_not_touch}"
        self.controller.capture(request)
        value = exact_clear_draft(request, [objective])
        value["do_not_touch"] = [
            {
                "item_id": "DNT-AUDIT",
                "text": do_not_touch,
                "basis_kind": "USER_EXPLICIT",
                "support": _quote(do_not_touch),
            }
        ]

        snapshot = self.import_value(value)

        self.assertEqual(
            snapshot["interpretation"]["objective"]["fidelity_status"],
            "PRESERVED",
        )
        self.assertFalse(snapshot["interpretation"]["do_not_touch_conflict"])
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "CLEAR ENOUGH TO FREEZE",
        )

    def test_do_not_touch_requires_exact_provenance_and_any_scoped_action_conflicts(
        self,
    ) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        weakened = clear_draft()
        weakened["do_not_touch"][0]["text"] = (
            "Do not break the Moon Runner documentation."
        )
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            "FIELD PROVENANCE INCOMPLETE",
        ):
            self.import_value(weakened)

        active = self.controller.snapshot()["request_identity"]["request_id"]
        request = (
            "Delete the audit ledger. "
            "Do not modify the audit ledger."
        )
        self.controller.capture(request, active)
        value = exact_clear_draft(
            request,
            ["Delete the audit ledger."],
        )
        value["do_not_touch"] = [
            {
                "item_id": "DNT-AUDIT",
                "text": "Do not modify the audit ledger.",
                "basis_kind": "USER_EXPLICIT",
                "support": _quote("Do not modify the audit ledger."),
            }
        ]
        snapshot = self.import_value(value)
        self.assertTrue(snapshot["interpretation"]["do_not_touch_conflict"])
        self.assertEqual(
            snapshot["interpretation"]["gate"],
            "HOLD — DO NOT TOUCH UNKNOWN",
        )

        active = snapshot["request_identity"]["request_id"]
        omitted_request = (
            "Build a widget. Do not modify the audit ledger."
        )
        self.controller.capture(omitted_request, active)
        omitted = exact_clear_draft(
            omitted_request,
            ["Build a widget."],
        )
        omitted_snapshot = self.import_value(omitted)
        self.assertTrue(
            omitted_snapshot["interpretation"]["do_not_touch_conflict"]
        )
        self.assertEqual(
            omitted_snapshot["interpretation"]["gate"],
            "HOLD — DO NOT TOUCH UNKNOWN",
        )

        active = omitted_snapshot["request_identity"]["request_id"]
        synonym_request = (
            "Erase the audit ledger. Do not alter the audit ledger."
        )
        self.controller.capture(synonym_request, active)
        synonym = exact_clear_draft(
            synonym_request,
            ["Erase the audit ledger."],
        )
        synonym["do_not_touch"] = [
            {
                "item_id": "DNT-SYNONYM",
                "text": "Do not alter the audit ledger.",
                "basis_kind": "USER_EXPLICIT",
                "support": _quote("Do not alter the audit ledger."),
            }
        ]
        synonym_snapshot = self.import_value(synonym)
        self.assertTrue(
            synonym_snapshot["interpretation"]["do_not_touch_conflict"]
        )
        self.assertEqual(
            synonym_snapshot["interpretation"]["gate"],
            "HOLD — DO NOT TOUCH UNKNOWN",
        )

    def test_freeze_is_canonical_immutable_and_non_authoritative(self) -> None:
        self.capture_and_import_clear()
        frozen = self.controller.freeze()
        identity = frozen["freeze"]
        raw = (
            self.controller.store.root
            / "freezes"
            / f"{identity['sha256']}.json"
        ).read_bytes()
        artifact = json.loads(raw)
        self.assertEqual(raw, canonical_json(artifact))
        self.assertEqual(sha256_bytes(raw), identity["sha256"])
        self.assertEqual(
            artifact["authority"]["state"],
            FREEZE_AUTHORITY_STATE,
        )
        self.assertEqual(
            artifact["original_request_identity"]["sha256"],
            frozen["request_identity"]["sha256"],
        )
        receipt = identity["receipt"]
        self.assertEqual(
            receipt["receipt_sha256"],
            self.controller.store.load_state()["freezes"][
                identity["freeze_id"]
            ]["receipt_sha256"],
        )
        self.assertEqual(
            receipt["frozen_intake_sha256"],
            identity["sha256"],
        )
        self.assertEqual(
            receipt["latest_draft_sha256"],
            artifact["latest_draft_sha256"],
        )
        self.assertEqual(receipt["field_statuses"], artifact["field_statuses"])
        self.assertEqual(receipt["authority_state"], FREEZE_AUTHORITY_STATE)
        self.assertTrue(identity["current"])
        with self.assertRaisesRegex(
            GuidedIntakeConflictError,
            "immutable",
        ):
            self.controller.freeze()

    def test_forward_only_freeze_correction_supersedes_old_freeze(self) -> None:
        self.capture_and_import_clear()
        first = self.controller.freeze()
        corrected = clear_draft()
        corrected["completion_line"]["text"] += " Evidence is retained."
        self.import_value(corrected)
        stale = self.controller.snapshot()["freeze"]
        self.assertFalse(stale["current"])
        self.assertEqual(
            self.controller.snapshot()["state"],
            "FREEZABLE",
        )
        second = self.controller.freeze()
        self.assertNotEqual(first["freeze"]["sha256"], second["freeze"]["sha256"])
        state = self.controller.store.load_state()
        old = state["freezes"][first["freeze"]["freeze_id"]]
        self.assertEqual(
            old["superseded_by_freeze_id"],
            second["freeze"]["freeze_id"],
        )
        old_path = (
            self.controller.store.root
            / "freezes"
            / f"{first['freeze']['sha256']}.json"
        )
        self.assertTrue(old_path.is_file())

    def test_later_confirmation_invalidates_old_freeze_and_new_freeze_transfers(
        self,
    ) -> None:
        confirmed = self.confirm_ambiguous()
        first_confirmation = deepcopy(confirmed["confirmation_history"])
        first = self.controller.freeze()
        first_freeze_path = (
            self.controller.store.root
            / "freezes"
            / f"{first['freeze']['sha256']}.json"
        )
        first_receipt_path = (
            self.controller.store.root
            / "receipts"
            / f"{first['freeze']['receipt']['receipt_sha256']}.json"
        )
        first_freeze_bytes = first_freeze_path.read_bytes()
        first_receipt_bytes = first_receipt_path.read_bytes()

        later = clear_draft()
        later["objective"] = {
            "text": "UNKNOWN — the bounded objective requires confirmation.",
            "atoms": [],
        }
        later["unknown"] = [
            {
                "unknown_id": "UNK-LATER-OBJECTIVE",
                "type": "MODEL_DETECTED_MISSING_FACT",
                "statement": "The bounded objective requires confirmation.",
                "basis": {
                    "kind": "MODEL_DETECTION",
                    "related_original_quotes": [],
                },
                "affects": ["OBJECTIVE"],
                "materiality": "MATERIAL",
                "effect_on_execution": "HOLD_OBJECTIVE",
                "evidence_required": "A later explicit objective confirmation.",
                "current_state": "OPEN",
            }
        ]
        later["clarification_candidate"] = {
            "field": "OBJECTIVE",
            "question": "Should the objective remain limited to Guided Intake?",
        }
        imported = self.import_value(later)
        question = imported["active_question"]["question"]
        after_confirmation = self.controller.confirm(
            question,
            "Keep the objective limited to Guided Intake.",
            {
                "objective": {
                    "text": "Keep the objective limited to Guided Intake.",
                    "atoms": [
                        {
                            "atom_id": "OBJ-LATER-CONFIRMATION",
                            "text": (
                                "Keep the objective limited to Guided Intake."
                            ),
                            "support": [
                                {
                                    "kind": "USER_CONFIRMATION",
                                    "event_id": "ACTIVE_CONFIRMATION",
                                }
                            ],
                        }
                    ],
                },
                "resolve_unknown_ids": ["UNK-LATER-OBJECTIVE"],
            },
        )
        self.assertEqual(
            len(first_confirmation) + 1,
            len(after_confirmation["confirmation_history"]),
        )
        self.assertEqual(
            first_confirmation,
            after_confirmation["confirmation_history"][:-1],
        )

        stale_bridge = RecordingBridge()
        with self.assertRaisesRegex(
            GuidedIntakeConflictError,
            "HOLD — INTAKE AS-OF STALE",
        ):
            self.controller.transfer_to_bridge(stale_bridge)
        self.assertEqual([], stale_bridge.calls)

        second = self.controller.freeze()
        state = self.controller.store.load_state()
        old_record = state["freezes"][first["freeze"]["freeze_id"]]
        self.assertEqual(
            second["freeze"]["freeze_id"],
            old_record["superseded_by_freeze_id"],
        )
        self.assertEqual(
            first["freeze"]["freeze_id"],
            second["freeze"]["supersedes_freeze_id"],
        )
        self.assertEqual(first_freeze_bytes, first_freeze_path.read_bytes())
        self.assertEqual(first_receipt_bytes, first_receipt_path.read_bytes())
        self.assertEqual(
            2,
            sum(
                event["kind"] == "USER_CONFIRMATION_RECORDED"
                for event in self.controller.store.read_events()
            ),
        )

        latest_bridge = RecordingBridge()
        transferred = self.controller.transfer_to_bridge(latest_bridge)
        self.assertEqual(1, len(latest_bridge.calls))
        self.assertEqual(
            second["freeze"]["sha256"],
            transferred["transfer_receipt"]["freeze_sha256"],
        )

    def test_purge_requires_confirmation_and_exact_current_identity(self) -> None:
        captured = self.controller.capture("Purge this exact source.")
        identity = captured["request_identity"]
        source_path = (
            self.controller.store.root
            / "original-requests"
            / f"{identity['sha256']}.utf8"
        )

        with self.assertRaises(GuidedIntakeValidationError):
            self.controller.purge(
                identity["request_id"],
                identity["sha256"],
                False,
            )
        with self.assertRaises(GuidedIntakeConflictError):
            self.controller.purge(
                "GI-REQ-WRONG",
                identity["sha256"],
                True,
            )
        with self.assertRaises(GuidedIntakeConflictError):
            self.controller.purge(
                identity["request_id"],
                "0" * 64,
                True,
            )

        self.assertTrue(source_path.is_file())
        self.assertFalse(
            any(
                event["kind"] == "ORIGINAL_REQUEST_PURGED"
                for event in self.controller.store.read_events()
            )
        )
        self.assertEqual(
            "Purge this exact source.",
            self.controller.snapshot()["original_request"],
        )

    def test_purge_rejects_stale_superseded_and_duplicate_requests(self) -> None:
        first = self.controller.capture("First exact source.")
        second = self.controller.capture(
            "Second exact source.",
            first["request_identity"]["request_id"],
        )
        first_identity = first["request_identity"]
        second_identity = second["request_identity"]

        with self.assertRaises(GuidedIntakeConflictError):
            self.controller.purge(
                first_identity["request_id"],
                first_identity["sha256"],
                True,
            )

        purged = self.controller.purge(
            second_identity["request_id"],
            second_identity["sha256"],
            True,
        )
        self.assertEqual(
            second_identity["request_id"],
            purged["purge"]["request_id"],
        )
        with self.assertRaises(GuidedIntakeConflictError):
            self.controller.purge(
                second_identity["request_id"],
                second_identity["sha256"],
                True,
            )
        purge_events = [
            event
            for event in self.controller.store.read_events()
            if event["kind"] == "ORIGINAL_REQUEST_PURGED"
        ]
        self.assertEqual(1, len(purge_events))

    def test_failed_unique_blob_delete_can_resume_without_new_purge_event(
        self,
    ) -> None:
        captured = self.controller.capture("Retry one failed purge delete.")
        identity = captured["request_identity"]
        source_path = (
            self.controller.store.root
            / "original-requests"
            / f"{identity['sha256']}.utf8"
        )
        original_delete = self.controller.store.delete_blob

        def fail_delete(
            _collection: str,
            _digest: str,
            *,
            suffix: str,
        ) -> None:
            self.assertEqual(".utf8", suffix)
            raise GuidedIntakeIntegrityError(
                "HOLD — GUIDED INTAKE STATE CORRUPT"
            )

        self.controller.store.delete_blob = fail_delete  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(
                GuidedIntakeIntegrityError,
                "STATE CORRUPT",
            ):
                self.controller.purge(
                    identity["request_id"],
                    identity["sha256"],
                    True,
                )
        finally:
            self.controller.store.delete_blob = original_delete  # type: ignore[method-assign]

        self.assertTrue(source_path.is_file())
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()
        self.assertEqual(
            0,
            sum(
                event["kind"] == "ORIGINAL_REQUEST_PURGED"
                for event in self.controller.store.read_events()
            ),
        )
        self.assertEqual(
            1,
            sum(
                event["kind"] == "ORIGINAL_REQUEST_PURGE_REQUESTED"
                for event in self.controller.store.read_events()
            ),
        )

        recovered = self.controller.purge(
            identity["request_id"],
            identity["sha256"],
            True,
        )
        self.assertFalse(source_path.exists())
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            recovered["state"],
        )
        self.assertEqual(
            1,
            sum(
                event["kind"] == "ORIGINAL_REQUEST_PURGED"
                for event in self.controller.store.read_events()
            ),
        )
        with self.assertRaises(GuidedIntakeConflictError):
            self.controller.purge(
                identity["request_id"],
                identity["sha256"],
                True,
            )

    def test_duplicate_purge_does_not_delete_recreated_corrupt_blob(
        self,
    ) -> None:
        source = "Do not accept recreated bytes after completed purge."
        captured = self.controller.capture(source)
        identity = captured["request_identity"]
        source_path = (
            self.controller.store.root
            / "original-requests"
            / f"{identity['sha256']}.utf8"
        )
        self.controller.purge(
            identity["request_id"],
            identity["sha256"],
            True,
        )
        source_path.write_bytes(source.encode("utf-8"))
        os.chmod(source_path, 0o600)

        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.purge(
                identity["request_id"],
                identity["sha256"],
                True,
            )
        self.assertTrue(source_path.is_file())
        self.assertEqual(
            1,
            sum(
                event["kind"] == "ORIGINAL_REQUEST_PURGED"
                for event in self.controller.store.read_events()
            ),
        )

    def test_purge_resumes_after_delete_before_completion_event(
        self,
    ) -> None:
        captured = self.controller.capture(
            "Resume after deletion but before purge completion."
        )
        identity = captured["request_identity"]
        source_path = (
            self.controller.store.root
            / "original-requests"
            / f"{identity['sha256']}.utf8"
        )
        original_append = self.controller._append

        def fail_completion(
            state: dict[str, object],
            kind: str,
            payload: dict[str, object],
            *,
            event_id: str | None = None,
            recorded_at: str | None = None,
        ) -> dict[str, object]:
            if kind == "ORIGINAL_REQUEST_PURGED":
                raise GuidedIntakeIntegrityError(
                    "HOLD — GUIDED INTAKE STATE CORRUPT"
                )
            return original_append(
                state,
                kind,
                payload,
                event_id=event_id,
                recorded_at=recorded_at,
            )

        self.controller._append = fail_completion  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(
                GuidedIntakeIntegrityError,
                "STATE CORRUPT",
            ):
                self.controller.purge(
                    identity["request_id"],
                    identity["sha256"],
                    True,
                )
        finally:
            self.controller._append = original_append  # type: ignore[method-assign]

        self.assertFalse(source_path.exists())
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()
        recovered = self.controller.purge(
            identity["request_id"],
            identity["sha256"],
            True,
        )
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            recovered["state"],
        )
        self.assertEqual(
            [
                "ORIGINAL_REQUEST_PURGE_REQUESTED",
                "ORIGINAL_REQUEST_PURGED",
            ],
            [
                event["kind"]
                for event in self.controller.store.read_events()
                if event["kind"].startswith("ORIGINAL_REQUEST_PURGE")
            ],
        )

    def test_purge_recovers_request_event_after_state_save_failure(
        self,
    ) -> None:
        captured = self.controller.capture(
            "Recover a purge request event after state save failure."
        )
        identity = captured["request_identity"]
        source_path = (
            self.controller.store.root
            / "original-requests"
            / f"{identity['sha256']}.utf8"
        )
        original_save = self.controller.store.save_state

        def fail_save(_state: dict[str, object]) -> None:
            raise GuidedIntakeIntegrityError(
                "HOLD — GUIDED INTAKE STATE CORRUPT"
            )

        self.controller.store.save_state = fail_save  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(
                GuidedIntakeIntegrityError,
                "STATE CORRUPT",
            ):
                self.controller.purge(
                    identity["request_id"],
                    identity["sha256"],
                    True,
                )
        finally:
            self.controller.store.save_state = original_save  # type: ignore[method-assign]

        self.assertTrue(source_path.is_file())
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()
        recovered = self.controller.purge(
            identity["request_id"],
            identity["sha256"],
            True,
        )
        self.assertFalse(source_path.exists())
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            recovered["state"],
        )
        self.assertEqual(
            [
                "ORIGINAL_REQUEST_PURGE_REQUESTED",
                "ORIGINAL_REQUEST_PURGED",
            ],
            [
                event["kind"]
                for event in self.controller.store.read_events()
                if event["kind"].startswith("ORIGINAL_REQUEST_PURGE")
            ],
        )

    def test_purge_recovers_completion_event_after_state_save_failure(
        self,
    ) -> None:
        captured = self.controller.capture(
            "Recover a purge completion event after state save failure."
        )
        identity = captured["request_identity"]
        source_path = (
            self.controller.store.root
            / "original-requests"
            / f"{identity['sha256']}.utf8"
        )
        original_save = self.controller.store.save_state
        save_calls = 0

        def fail_second_save(state: dict[str, object]) -> None:
            nonlocal save_calls
            save_calls += 1
            if save_calls == 2:
                raise GuidedIntakeIntegrityError(
                    "HOLD — GUIDED INTAKE STATE CORRUPT"
                )
            original_save(state)

        self.controller.store.save_state = fail_second_save  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(
                GuidedIntakeIntegrityError,
                "STATE CORRUPT",
            ):
                self.controller.purge(
                    identity["request_id"],
                    identity["sha256"],
                    True,
                )
        finally:
            self.controller.store.save_state = original_save  # type: ignore[method-assign]

        self.assertFalse(source_path.exists())
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()
        recovered = self.controller.purge(
            identity["request_id"],
            identity["sha256"],
            True,
        )
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            recovered["state"],
        )
        self.assertEqual(
            1,
            sum(
                event["kind"] == "ORIGINAL_REQUEST_PURGED"
                for event in self.controller.store.read_events()
            ),
        )
        with self.assertRaises(GuidedIntakeConflictError):
            self.controller.purge(
                identity["request_id"],
                identity["sha256"],
                True,
            )

    def test_unique_source_purge_is_forward_only_and_preserves_history(
        self,
    ) -> None:
        self.capture_and_import_clear()
        frozen = self.controller.freeze()
        identity = frozen["request_identity"]
        source_path = (
            self.controller.store.root
            / "original-requests"
            / f"{identity['sha256']}.utf8"
        )
        freeze_path = (
            self.controller.store.root
            / "freezes"
            / f"{frozen['freeze']['sha256']}.json"
        )
        receipt_sha256 = frozen["freeze"]["receipt"]["receipt_sha256"]
        receipt_path = (
            self.controller.store.root
            / "receipts"
            / f"{receipt_sha256}.json"
        )
        freeze_bytes = freeze_path.read_bytes()
        receipt_bytes = receipt_path.read_bytes()
        events_before = deepcopy(self.controller.store.read_events())
        event_bytes_before = self.controller.store.events_path.read_bytes()

        purged = self.controller.purge(
            identity["request_id"],
            identity["sha256"],
            True,
        )
        purge = purged["purge"]
        self.assertEqual(identity["request_id"], purge["request_id"])
        self.assertEqual(identity["sha256"], purge["request_sha256"])
        self.assertEqual("2026-07-29T00:00:00Z", purge["purged_at"])
        self.assertEqual("EXPLICIT_USER_CONFIRMATION", purge["confirmation"])
        self.assertEqual(
            "DELETED_NO_NON_PURGED_REFERENCES",
            purge["raw_blob_disposition"],
        )
        self.assertEqual(0, purge["remaining_non_purged_references"])
        self.assertRegex(purge["event_id"], r"^GI-PURGE-")
        self.assertRegex(purge["event_hash"], r"^[0-9a-f]{64}$")

        self.assertFalse(source_path.exists())
        self.assertEqual(freeze_bytes, freeze_path.read_bytes())
        self.assertEqual(receipt_bytes, receipt_path.read_bytes())
        self.assertEqual(frozen["freeze"]["sha256"], purged["freeze"]["sha256"])
        self.assertEqual(
            receipt_sha256,
            purged["freeze"]["receipt"]["receipt_sha256"],
        )
        state = self.controller.store.load_state()
        self.assertTrue(
            state["freezes"][frozen["freeze"]["freeze_id"]]["purged"]
        )

        events_after = self.controller.store.read_events()
        self.assertEqual(events_before, events_after[:-2])
        self.assertEqual(
            "ORIGINAL_REQUEST_PURGE_REQUESTED",
            events_after[-2]["kind"],
        )
        self.assertEqual("ORIGINAL_REQUEST_PURGED", events_after[-1]["kind"])
        self.assertEqual(
            "2026-07-29T00:00:00Z",
            events_after[-1]["recorded_at"],
        )
        self.assertEqual(
            identity["request_id"],
            events_after[-1]["payload"]["request_id"],
        )
        self.assertEqual(
            identity["sha256"],
            events_after[-1]["payload"]["request_sha256"],
        )
        self.assertTrue(
            self.controller.store.events_path.read_bytes().startswith(
                event_bytes_before
            )
        )

        replayed = self.controller.snapshot()
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            replayed["state"],
        )
        self.assertIsNone(replayed["original_request"])
        self.assertIsNone(replayed["interpretation"])
        self.assertEqual("UNAVAILABLE", replayed["raw_source_availability"])
        self.assertEqual("BLOCKED", replayed["judgment_reuse"])
        self.assertEqual("BLOCKED", replayed["fidelity_evaluation"])
        self.assertEqual("PRESERVED", replayed["historical_identity"])
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            replayed["transfer_state"],
        )
        self.assertNotIn(AMBIGUOUS_REQUEST, json.dumps(replayed))

        for operation in (
            self.controller.copy_for_pro,
            lambda: self.import_value(clear_draft()),
            self.controller.freeze,
        ):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(
                    GuidedIntakeConflictError,
                    "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
                ):
                    operation()
        bridge = RecordingBridge()
        with self.assertRaisesRegex(
            GuidedIntakeConflictError,
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
        ):
            self.controller.transfer_to_bridge(bridge)
        self.assertEqual([], bridge.calls)

    def test_shared_hash_purge_retains_blob_for_non_purged_request(self) -> None:
        source = "One shared content-addressed source."
        first = self.controller.capture(source)
        second = self.controller.capture(
            source,
            first["request_identity"]["request_id"],
        )
        identity = second["request_identity"]
        source_path = (
            self.controller.store.root
            / "original-requests"
            / f"{identity['sha256']}.utf8"
        )

        purged = self.controller.purge(
            identity["request_id"],
            identity["sha256"],
            True,
        )
        self.assertEqual(
            "RETAINED_FOR_NON_PURGED_REFERENCE",
            purged["purge"]["raw_blob_disposition"],
        )
        self.assertEqual(
            1,
            purged["purge"]["remaining_non_purged_references"],
        )
        self.assertTrue(source_path.is_file())
        self.assertEqual(
            source.encode("utf-8"),
            self.controller.store.read_blob(
                "original-requests",
                identity["sha256"],
                suffix=".utf8",
            ),
        )
        self.assertIsNone(purged["original_request"])
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            purged["state"],
        )

    def test_shared_hash_blob_is_deleted_after_all_requests_are_purged(
        self,
    ) -> None:
        source = "Recreated shared source."
        first = self.controller.capture(source)
        first_identity = first["request_identity"]
        source_path = (
            self.controller.store.root
            / "original-requests"
            / f"{first_identity['sha256']}.utf8"
        )
        first_purge = self.controller.purge(
            first_identity["request_id"],
            first_identity["sha256"],
            True,
        )
        self.assertEqual(
            "DELETED_NO_NON_PURGED_REFERENCES",
            first_purge["purge"]["raw_blob_disposition"],
        )
        self.assertFalse(source_path.exists())

        second = self.controller.capture(
            source,
            first_identity["request_id"],
        )
        second_identity = second["request_identity"]
        self.assertTrue(source_path.is_file())
        self.assertEqual(source, second["original_request"])
        second_purge = self.controller.purge(
            second_identity["request_id"],
            second_identity["sha256"],
            True,
        )
        self.assertEqual(
            "DELETED_NO_NON_PURGED_REFERENCES",
            second_purge["purge"]["raw_blob_disposition"],
        )
        self.assertEqual(
            0,
            second_purge["purge"]["remaining_non_purged_references"],
        )
        self.assertFalse(source_path.exists())
        self.assertEqual(
            2,
            sum(
                event["kind"] == "ORIGINAL_REQUEST_PURGED"
                for event in self.controller.store.read_events()
            ),
        )

    def test_transfer_preserves_exact_fields_hashes_and_starts_nothing(self) -> None:
        self.capture_and_import_clear()
        frozen = self.controller.freeze()
        bridge = RecordingBridge()
        transferred = self.controller.transfer_to_bridge(bridge)
        self.assertEqual(len(bridge.calls), 1)
        transfer = bridge.calls[0]
        interpretation = frozen["interpretation"]
        self.assertEqual(transfer["objective"], interpretation["objective"]["text"])
        self.assertEqual(
            transfer["completion_line"],
            interpretation["completion_line"]["text"],
        )
        self.assertEqual(
            transfer["do_not_touch"],
            interpretation["do_not_touch"],
        )
        self.assertEqual(transfer["unknown"], interpretation["unknown"])
        self.assertEqual(
            transfer["field_hashes"]["objective"],
            structured_sha256(transfer["objective"]),
        )
        self.assertEqual(
            transferred["transfer_receipt"]["result"],
            "TRANSFERRED WITHOUT EXECUTION",
        )
        self.assertEqual(
            transferred["transfer_receipt"][
                "pre_transfer_field_hashes"
            ],
            transferred["transfer_receipt"][
                "post_transfer_field_hashes"
            ],
        )
        self.assertRegex(
            transferred["transfer_receipt"]["receipt_sha256"],
            r"^[0-9a-f]{64}$",
        )
        self.assertEqual(transfer["evidence_packet_identity"], EVIDENCE_PACKET_IDENTITY)
        self.assertFalse(hasattr(bridge, "start_run"))

    def test_current_transfer_receipt_must_replay_from_event_history(
        self,
    ) -> None:
        self.capture_and_import_clear()
        self.controller.freeze()
        self.controller.transfer_to_bridge(RecordingBridge())
        state = self.controller.store.load_state()
        state["transfer_receipt"] = None
        self.controller.store.save_state(state)
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()

    def test_historical_transfer_receipt_blob_remains_verifiable(
        self,
    ) -> None:
        self.capture_and_import_clear()
        self.controller.freeze()
        transferred = self.controller.transfer_to_bridge(
            RecordingBridge()
        )
        receipt_sha = transferred["transfer_receipt"][
            "receipt_sha256"
        ]
        active_request_id = transferred["request_identity"][
            "request_id"
        ]
        self.controller.capture(
            "Correct the captured request.",
            active_request_id,
        )
        receipt_path = (
            self.controller.store.root
            / "receipts"
            / f"{receipt_sha}.json"
        )
        receipt_path.unlink()
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()

    def test_transfer_field_alteration_fails_closed(self) -> None:
        self.capture_and_import_clear()
        self.controller.freeze()
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "TRANSFER ALTERED BOUNDARY",
        ):
            self.controller.transfer_to_bridge(RecordingBridge(alter=True))

    def test_actual_manual_bridge_receives_exact_frozen_boundary(self) -> None:
        self.capture_and_import_clear()
        frozen = self.controller.freeze()
        bridge = BridgeSessionController(
            self.repository,
            clock=lambda: "2026-07-29T00:00:01Z",
            id_factory=lambda: next(self.identities),
        )
        transferred = self.controller.transfer_to_bridge(bridge)
        bridge_snapshot = bridge.snapshot()
        exact = bridge_snapshot["session"]["boundary"][
            "guided_intake_boundary"
        ]
        self.assertEqual(
            exact["objective"],
            frozen["interpretation"]["objective"]["text"],
        )
        self.assertEqual(
            exact["completion_line"],
            frozen["interpretation"]["completion_line"]["text"],
        )
        self.assertEqual(
            exact["do_not_touch"],
            frozen["interpretation"]["do_not_touch"],
        )
        self.assertEqual(exact["unknown"], frozen["interpretation"]["unknown"])
        self.assertEqual(
            bridge_snapshot["guided_intake_transfer"]["field_hashes"],
            exact["field_hashes"],
        )
        self.assertEqual(
            transferred["transfer_receipt"]["bridge_session_id"],
            bridge_snapshot["guided_intake_transfer"]["bridge_session_id"],
        )
        copied = bridge.copy_for_pro()
        self.assertIn("COPY_FOR_PRO", copied["outputs"])

    def test_transfer_rejects_repository_freshness_change(self) -> None:
        self.capture_and_import_clear()
        self.controller.freeze()
        (self.repository / "later.txt").write_text("later\n", encoding="utf-8")
        subprocess.run(
            ("git", "add", "later.txt"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "commit", "-qm", "later"),
            cwd=self.repository,
            check=True,
        )
        stale = self.controller.snapshot()
        self.assertFalse(stale["freeze"]["current"])
        self.assertEqual(stale["state"], "FREEZABLE")
        with self.assertRaisesRegex(
            GuidedIntakeConflictError,
            "INTAKE AS-OF STALE",
        ):
            self.controller.transfer_to_bridge(RecordingBridge())

    def test_transfer_rejects_superseded_request_and_newer_draft(self) -> None:
        self.capture_and_import_clear()
        frozen = self.controller.freeze()
        self.import_value(clear_draft())
        with self.assertRaisesRegex(
            GuidedIntakeConflictError,
            "INTAKE AS-OF STALE",
        ):
            self.controller.transfer_to_bridge(RecordingBridge())
        active = self.controller.snapshot()["request_identity"]["request_id"]
        self.controller.capture("corrected request", active)
        self.assertTrue(
            (
                self.controller.store.root
                / "freezes"
                / f"{frozen['freeze']['sha256']}.json"
            ).is_file()
        )
        with self.assertRaises(
            (GuidedIntakeConflictError, GuidedIntakeIntegrityError)
        ):
            self.controller.transfer_to_bridge(RecordingBridge())

    def test_event_log_truncation_and_blob_hash_mismatch_fail_closed(self) -> None:
        snapshot = self.controller.capture(AMBIGUOUS_REQUEST)
        events = self.controller.store.events_path
        events.write_bytes(events.read_bytes()[:-1])
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()

        other = GuidedIntakeController(
            self.repository,
            id_factory=lambda: next(self.identities),
        )
        events.write_bytes(events.read_bytes() + b"\n")
        request_path = (
            self.controller.store.root
            / "original-requests"
            / f"{snapshot['request_identity']['sha256']}.utf8"
        )
        request_path.write_bytes(b"altered")
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            other.snapshot()

    def test_duplicate_keys_nested_state_and_draft_corruption_fail_closed(
        self,
    ) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        state_path = self.controller.store.state_path
        raw = state_path.read_bytes()
        state_path.write_bytes(
            raw.replace(
                b'"active_draft_id":null',
                b'"active_draft_id":null,"active_draft_id":null',
                1,
            )
        )
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()

        other = GuidedIntakeController(
            self.repository,
            id_factory=lambda: next(self.identities),
        )
        state_path.write_bytes(raw)
        self.import_value(clear_draft())
        draft = self.controller.store.load_state()["drafts"][
            self.controller.store.load_state()["active_draft_id"]
        ]
        draft_path = (
            self.controller.store.root
            / "drafts"
            / f"{draft['sha256']}.json"
        )
        draft_path.write_bytes(draft_path.read_bytes() + b" ")
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            other.snapshot()

    def test_state_gate_is_rederived_from_draft_and_events(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        self.import_value(ambiguous_draft())
        state = self.controller.store.load_state()
        state["current_interpretation"]["gate"] = (
            "CLEAR ENOUGH TO FREEZE"
        )
        self.controller.store.save_state(state)
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.freeze()
        self.assertEqual(
            self.controller.store.load_state()["freezes"],
            {},
        )

    def test_request_record_is_bijective_with_capture_event(self) -> None:
        first = self.controller.capture("Create alpha.")
        second = self.controller.capture(
            "Create bravo.",
            first["request_identity"]["request_id"],
        )
        state = self.controller.store.load_state()
        state["requests"][
            second["request_identity"]["request_id"]
        ]["sha256"] = first["request_identity"]["sha256"]
        self.controller.store.save_state(state)
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()

    def test_manual_raw_deletion_is_not_a_valid_purge(self) -> None:
        captured = self.controller.capture("Manual deletion is not purge.")
        identity = captured["request_identity"]
        source_path = (
            self.controller.store.root
            / "original-requests"
            / f"{identity['sha256']}.utf8"
        )
        source_path.unlink()
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()
        self.assertFalse(
            any(
                event["kind"] == "ORIGINAL_REQUEST_PURGED"
                for event in self.controller.store.read_events()
            )
        )

    def test_purge_projection_without_event_fails_closed(self) -> None:
        self.capture_and_import_clear()
        frozen = self.controller.freeze()
        state = self.controller.store.load_state()
        state["freezes"][frozen["freeze"]["freeze_id"]]["purged"] = True
        self.controller.store.save_state(state)
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()

    def test_corrupted_purge_event_fails_closed(self) -> None:
        captured = self.controller.capture("Corrupt the purge event.")
        identity = captured["request_identity"]
        self.controller.purge(
            identity["request_id"],
            identity["sha256"],
            True,
        )
        events_path = self.controller.store.events_path
        raw = events_path.read_bytes()
        corrupted = raw.replace(
            b'"ORIGINAL_REQUEST_PURGED"',
            b'"ORIGINAL_REQUEST_PURGEX"',
            1,
        )
        self.assertNotEqual(raw, corrupted)
        events_path.write_bytes(corrupted)
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()

    def test_missing_confirmation_receipt_blocks_snapshot_and_freeze(
        self,
    ) -> None:
        self.confirm_ambiguous()
        confirmation_event = next(
            event
            for event in self.controller.store.read_events()
            if event["kind"] == "USER_CONFIRMATION_RECORDED"
        )
        receipt_sha = confirmation_event["payload"][
            "confirmation_sha256"
        ]
        receipt_path = (
            self.controller.store.root
            / "receipts"
            / f"{receipt_sha}.json"
        )
        receipt_path.unlink()
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.freeze()

    def test_deep_state_references_and_permissions_fail_closed(self) -> None:
        captured = self.controller.capture(AMBIGUOUS_REQUEST)
        state = self.controller.store.load_state()
        state["active_request_id"] = "GI-REQ-ORPHAN"
        self.controller.store.save_state(state)
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()

        state["active_request_id"] = captured["request_identity"][
            "request_id"
        ]
        self.controller.store.save_state(state)
        request_path = (
            self.controller.store.root
            / "original-requests"
            / f"{captured['request_identity']['sha256']}.utf8"
        )
        os.chmod(request_path, 0o644)
        with self.assertRaisesRegex(
            GuidedIntakeIntegrityError,
            "STATE CORRUPT",
        ):
            self.controller.snapshot()

    def test_cross_process_lock_contention_is_busy_not_corrupt(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        lock_path = self.controller.store.root / ".transaction.lock"
        script = (
            "import fcntl,sys,time\n"
            "stream=open(sys.argv[1],'rb')\n"
            "fcntl.flock(stream.fileno(),fcntl.LOCK_EX)\n"
            "print('locked',flush=True)\n"
            "time.sleep(2)\n"
        )
        child = subprocess.Popen(
            (sys.executable, "-c", script, str(lock_path)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self.assertEqual(child.stdout.readline().strip(), "locked")
            with self.assertRaises(GuidedIntakeBusyError):
                self.controller.snapshot()
        finally:
            child.terminate()
            child.wait(timeout=5)
            child.stdout.close()
            child.stderr.close()

    def test_store_permissions_and_receipts_exclude_raw_request(self) -> None:
        self.controller.capture(AMBIGUOUS_REQUEST)
        root = self.controller.store.root
        self.assertEqual(os.stat(root).st_mode & 0o777, 0o700)
        self.assertEqual(
            os.stat(self.controller.store.state_path).st_mode & 0o777,
            0o600,
        )
        self.assertEqual(
            os.stat(self.controller.store.events_path).st_mode & 0o777,
            0o600,
        )
        self.assertNotIn(
            AMBIGUOUS_REQUEST.encode("utf-8"),
            self.controller.store.events_path.read_bytes(),
        )
        self.assertNotIn(
            AMBIGUOUS_REQUEST.encode("utf-8"),
            self.controller.store.state_path.read_bytes(),
        )

    def test_script_text_remains_inert_data(self) -> None:
        hostile = "<script>alert('x')</script>\nrequest"
        snapshot = self.controller.capture(hostile)
        self.assertEqual(snapshot["original_request"], hostile)
        self.assertEqual(
            snapshot["request_identity"]["sha256"],
            sha256_bytes(hostile.encode("utf-8")),
        )

    def test_module_has_no_runner_codex_or_acceleration_import(self) -> None:
        source = Path(
            "decision_os/companion/guided_intake.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("start_run(", source)
        self.assertNotIn("codex_adapter import", source)
        self.assertNotIn("acceleration.engine import", source)

    def test_repository_fixtures_prove_before_after_and_six_judgments(self) -> None:
        fixture_root = Path("validation/fixtures/guided_intake_v0_1")
        raw_request = (fixture_root / "ambiguous_request.txt").read_text(
            encoding="utf-8"
        )
        raw_bytes = (fixture_root / "ambiguous_request.txt").read_bytes()
        draft_text = (fixture_root / "pro_draft.json").read_text(
            encoding="utf-8"
        )
        confirmation = json.loads(
            (fixture_root / "user_confirmation.json").read_text(
                encoding="utf-8"
            )
        )
        captured = self.controller.capture(raw_request)
        self.assertEqual(
            captured["request_identity"]["sha256"],
            sha256_bytes(raw_bytes),
        )
        before = self.controller.import_draft(draft_text, "FIXTURE_PRO")
        self.assertEqual(
            before["interpretation"]["gate"],
            "NEEDS USER CONFIRMATION",
        )
        self.assertEqual(
            before["interpretation"]["completion_line"][
                "testability_status"
            ],
            "UNKNOWN",
        )
        after = self.controller.confirm(
            confirmation["question"],
            confirmation["answer"],
            confirmation["resulting_delta"],
        )
        self.assertEqual(
            after["interpretation"]["gate"],
            "CLEAR ENOUGH TO FREEZE",
        )
        frozen = self.controller.freeze()
        frozen_fixture = json.loads(
            (fixture_root / "frozen_intake.json").read_text(encoding="utf-8")
        )
        frozen_raw = self.controller.store.read_blob(
            "freezes",
            frozen["freeze"]["sha256"],
            suffix=".json",
        )
        self.assertEqual(frozen_raw, canonical_json(frozen_fixture))
        self.assertEqual(json.loads(frozen_raw), frozen_fixture)
        self.assertEqual(
            frozen["freeze"]["sha256"],
            "23a2a6523fa67f15efb86611a9a92f75202f08bce96ad6fb3d8ceeedc2d98a31",
        )
        self.assertEqual(
            frozen_fixture["original_request_identity"]["sha256"],
            sha256_bytes(raw_bytes),
        )
        self.assertEqual(
            frozen_fixture["authority"]["state"],
            FREEZE_AUTHORITY_STATE,
        )
        independent = json.loads(
            (fixture_root / "independent_evaluation.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            set(independent["six_independent_judgments"]),
            {
                "objective_fidelity",
                "objective_expansion",
                "completion_testability",
                "do_not_touch_preservation",
                "unknown_preservation",
                "authority_inflation",
            },
        )
        for name, judgment in independent[
            "six_independent_judgments"
        ].items():
            with self.subTest(judgment=name):
                fixture_status = judgment["fixture_status"]
                failure_status = judgment["failure_fixture_status"]
                self.assertIn(fixture_status, judgment["allowed_statuses"])
                self.assertIn(failure_status, judgment["allowed_statuses"])
                self.assertNotEqual(fixture_status, failure_status)
                self.assertTrue(judgment["evidence_unit"])
        self.assertEqual(
            independent["summary_gate"],
            "EVALUATION FIXTURE ONLY — NO PRODUCT OR PROTOCOL PASS",
        )


if __name__ == "__main__":
    unittest.main()
