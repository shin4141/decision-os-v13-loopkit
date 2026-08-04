from __future__ import annotations

from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from decision_os.acceleration.codex_adapter import (
    ADAPTER_NAME,
    CODEX_CLI_VERSION,
    CODEX_MODEL,
    CODEX_REASONING_EFFORT,
    CODEX_SERVICE_TIER,
    CodexAdapterFailure,
    CodexReadEvidence,
    CodexRunResult,
    CodexRuntimeIdentity,
)
from decision_os.acceleration.engine import AccelerationEngine
from decision_os.companion.field_notes_adapter import (
    FieldNoteA1ProposalDiagnostic,
    FieldNoteCreatorLiveA1CaptureConfig,
    FieldNoteCodexRunResult,
    FieldNotesCodexAdapter,
)
from decision_os.companion.field_notes_controller import (
    FieldNoteError,
    FieldNotesCompanionController,
)
from decision_os.companion.field_notes_model import (
    FIELD_NOTE_SCHEMA_VERSION,
    FIELD_NOTE_TOOL_NAME,
    FIELD_NOTE_TOOL_SPEC,
    FieldNoteProposalGate,
    compile_draft,
    field_note_tool_spec_for_trust,
    level_three_available,
)
from tests.test_acceleration_codex_adapter import (
    FakeTransportFactory,
    completed_agent_message,
    completed_turn,
    handshake_messages,
)


def proposal() -> dict[str, object]:
    return {
        "title": "Approval byte binding",
        "value_level": 3,
        "source_model_class": "stronger",
        "target_model_class": "lower-cost",
        "trigger_terms": ["bounded approval", "exact file create"],
        "scope": {
            "task_family": "governed-file-write",
            "path_prefixes": ["docs/"],
            "exclude_terms": ["bulk rewrite"],
        },
        "body": {
            "trigger": "Use when one exact new file is proposed.",
            "reusable_structure": (
                "Bind path, bytes, digest, and precondition."
            ),
            "scope": "One repository-relative Markdown file.",
            "do_not_apply_when": (
                "Do not use for updates or multiple files."
            ),
            "procedure": "Compile, approve once, create new, read back.",
            "acceptance": "The readback bytes and SHA-256 match.",
            "evidence": (
                "The source Run completed successfully; reuse is untested."
            ),
            "remaining_unknowns": (
                "External adoption and lower-model reuse remain unknown."
            ),
        },
    }


def create_repository(parent: Path) -> Path:
    repository = parent / "repo"
    repository.mkdir()
    completed = subprocess.run(
        ("git", "init", "-q", str(repository)),
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    (repository / "seed.txt").write_text("seed\n", encoding="utf-8")
    return repository


def started_proposal(
    *,
    thread_id: str,
    turn_id: str,
    call_id: str,
    arguments: dict[str, object],
) -> dict[str, object]:
    return {
        "method": "item/started",
        "params": {
            "item": {
                "arguments": arguments,
                "id": call_id,
                "status": "inProgress",
                "tool": FIELD_NOTE_TOOL_NAME,
                "type": "dynamicToolCall",
            },
            "startedAtMs": 1,
            "threadId": thread_id,
            "turnId": turn_id,
        },
    }


def proposal_request(
    *,
    thread_id: str,
    turn_id: str,
    call_id: str,
    request_id: str,
    arguments: dict[str, object],
) -> dict[str, object]:
    return {
        "id": request_id,
        "method": "item/tool/call",
        "params": {
            "arguments": arguments,
            "callId": call_id,
            "threadId": thread_id,
            "tool": FIELD_NOTE_TOOL_NAME,
            "turnId": turn_id,
        },
    }


def completed_proposal(
    *,
    thread_id: str,
    turn_id: str,
    call_id: str,
    arguments: dict[str, object],
) -> dict[str, object]:
    return {
        "method": "item/completed",
        "params": {
            "completedAtMs": 2,
            "item": {
                "arguments": arguments,
                "id": call_id,
                "status": "completed",
                "tool": FIELD_NOTE_TOOL_NAME,
                "type": "dynamicToolCall",
            },
            "threadId": thread_id,
            "turnId": turn_id,
        },
    }


class FieldNotesModelTests(unittest.TestCase):
    def test_derived_schema_hides_level_three_without_active_trust(self) -> None:
        self.assertFalse(level_three_available("UNKNOWN", "UNKNOWN"))
        tool_spec = field_note_tool_spec_for_trust("UNKNOWN", "UNKNOWN")
        input_schema = tool_spec["inputSchema"]
        self.assertEqual(
            [1, 2],
            input_schema["properties"]["value_level"]["enum"],
        )

    def test_derived_schema_hides_level_three_with_active_gate_trust(self) -> None:
        self.assertTrue(level_three_available("stronger", "lower-cost"))
        tool_spec = field_note_tool_spec_for_trust("stronger", "lower-cost")
        input_schema = tool_spec["inputSchema"]
        self.assertEqual(
            [1, 2],
            input_schema["properties"]["value_level"]["enum"],
        )

    def test_derived_schema_avoids_unsupported_root_keywords(self) -> None:
        prohibited = {"oneOf", "anyOf", "allOf", "enum", "const", "not"}
        for source_class, target_class in (
            ("UNKNOWN", "UNKNOWN"),
            ("stronger", "lower-cost"),
        ):
            with self.subTest(source=source_class, target=target_class):
                input_schema = field_note_tool_spec_for_trust(
                    source_class,
                    target_class,
                )["inputSchema"]
                self.assertEqual(set(), prohibited.intersection(input_schema))

    def test_derived_tool_specs_are_fresh_and_do_not_mutate_base(self) -> None:
        base_snapshot = json.loads(json.dumps(FIELD_NOTE_TOOL_SPEC))
        first = field_note_tool_spec_for_trust("UNKNOWN", "UNKNOWN")
        second = field_note_tool_spec_for_trust("UNKNOWN", "UNKNOWN")
        self.assertIsNot(first, second)
        self.assertIsNot(first["inputSchema"], second["inputSchema"])
        first["inputSchema"]["properties"]["value_level"]["enum"].append(3)
        self.assertEqual(
            [1, 2],
            second["inputSchema"]["properties"]["value_level"]["enum"],
        )
        self.assertEqual(base_snapshot, FIELD_NOTE_TOOL_SPEC)
        self.assertEqual(
            [1, 2, 3],
            FIELD_NOTE_TOOL_SPEC["inputSchema"]["properties"]["value_level"][
                "enum"
            ],
        )
        self.assertEqual(
            set(),
            {"oneOf", "anyOf", "allOf", "enum", "const", "not"}.intersection(
                FIELD_NOTE_TOOL_SPEC["inputSchema"]
            ),
        )

    def test_compile_is_byte_deterministic_and_canonical(self) -> None:
        draft = compile_draft(
            proposal(),
            source_run_id="run_001",
            created_at="2026-08-02T12:34:56Z",
            field_note_id="fn_fixed_identity",
        )
        repeated = compile_draft(
            proposal(),
            source_run_id="run_001",
            created_at="2026-08-02T12:34:56Z",
            field_note_id="fn_fixed_identity",
        )
        self.assertEqual(draft.markdown, repeated.markdown)
        self.assertEqual(
            draft.sha256,
            hashlib.sha256(draft.markdown).hexdigest(),
        )
        self.assertTrue(
            draft.relative_path.startswith(
                ".decision-os/field-notes/"
                "2026-08-02-approval-byte-binding-"
            )
        )
        first, metadata, end, *_ = draft.markdown.decode("utf-8").splitlines()
        self.assertEqual(
            first,
            "<!-- decision-os-field-note-metadata:v0.1",
        )
        self.assertEqual(end, "-->")
        parsed = json.loads(metadata)
        self.assertEqual(parsed["schema_version"], FIELD_NOTE_SCHEMA_VERSION)
        self.assertEqual(parsed["status"], "CANDIDATE")
        self.assertEqual(
            parsed["maturity_evidence"],
            {
                "different_task_reuse": None,
                "first_verified_reuse": None,
            },
        )

    def test_one_shot_accepts_at_most_one_candidate(self) -> None:
        gate = FieldNoteProposalGate(
            "run_001",
            trusted_source_model_class="stronger",
            trusted_target_model_class="lower-cost",
        )
        self.assertEqual(
            gate.propose(proposal()),
            (True, "proposal_accepted"),
        )
        original = gate.accepted
        self.assertEqual(
            gate.propose(proposal()),
            (False, "proposal_attempt_already_consumed"),
        )
        self.assertIs(gate.accepted, original)

    def test_invalid_first_attempt_consumes_gate(self) -> None:
        gate = FieldNoteProposalGate("run_001")
        invalid = proposal()
        invalid["value_level"] = 4
        self.assertEqual(
            gate.propose(invalid),
            (False, "proposal_schema_invalid"),
        )
        self.assertIsNone(gate.accepted)
        self.assertEqual(
            gate.propose(proposal()),
            (False, "proposal_attempt_already_consumed"),
        )

    def test_level_three_requires_stronger_to_lower_cost(self) -> None:
        invalid = proposal()
        invalid["target_model_class"] = "UNKNOWN"
        with self.assertRaises(ValueError):
            compile_draft(
                invalid,
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )

    def test_self_asserted_level_three_with_unknown_trust_is_rejected(
        self,
    ) -> None:
        gate = FieldNoteProposalGate("run_001")
        with patch(
            "decision_os.companion.field_notes_model.compile_draft"
        ) as compiler:
            self.assertEqual(
                gate.propose(proposal()),
                (False, "level_3_trust_not_configured"),
            )
        compiler.assert_not_called()
        self.assertIsNone(gate.accepted)
        self.assertEqual(
            (False, "proposal_attempt_already_consumed"),
            gate.propose(proposal()),
        )

    def test_level_three_proposal_and_trusted_classes_must_match(
        self,
    ) -> None:
        gate = FieldNoteProposalGate(
            "run_001",
            trusted_source_model_class="stronger",
            trusted_target_model_class="lower-cost",
        )
        mismatched = proposal()
        mismatched["source_model_class"] = "UNKNOWN"
        with patch(
            "decision_os.companion.field_notes_model.compile_draft"
        ) as compiler:
            self.assertEqual(
                gate.propose(mismatched),
                (False, "level_3_trust_class_mismatch"),
            )
        compiler.assert_not_called()
        self.assertIsNone(gate.accepted)
        self.assertEqual(
            (False, "proposal_attempt_already_consumed"),
            gate.propose(proposal()),
        )

    def test_trusted_stronger_to_lower_cost_level_three_is_accepted(
        self,
    ) -> None:
        gate = FieldNoteProposalGate(
            "run_001",
            trusted_source_model_class="stronger",
            trusted_target_model_class="lower-cost",
        )
        self.assertEqual(
            gate.propose(proposal()),
            (True, "proposal_accepted"),
        )
        assert gate.accepted is not None
        self.assertEqual(gate.accepted.source_model_class, "stronger")
        self.assertEqual(gate.accepted.target_model_class, "lower-cost")

    def test_levels_one_and_two_remain_available_with_unknown_trust(
        self,
    ) -> None:
        for value_level in (1, 2):
            with self.subTest(value_level=value_level):
                candidate = proposal()
                candidate["value_level"] = value_level
                gate = FieldNoteProposalGate("run_001")
                self.assertEqual(
                    gate.propose(candidate),
                    (True, "proposal_accepted"),
                )
                assert gate.accepted is not None
                self.assertEqual(
                    gate.accepted.source_model_class,
                    "UNKNOWN",
                )
                self.assertEqual(
                    gate.accepted.target_model_class,
                    "UNKNOWN",
                )

    def test_title_newline_and_h1_injection_are_rejected(self) -> None:
        for title in ("Safe title\nInjected", "# Injected H1"):
            with self.subTest(title=title):
                invalid = proposal()
                invalid["title"] = title
                with self.assertRaises(ValueError):
                    compile_draft(invalid, source_run_id="run_001")

    def test_body_heading_and_metadata_injections_are_rejected(self) -> None:
        injected_values = (
            "Safe prose\n## Evidence\nInjected fixed heading.",
            "Safe prose\n### Arbitrary heading\nInjected structure.",
            (
                "Safe prose\n"
                "<!-- decision-os-field-note-metadata:v0.1"
            ),
            "Safe prose\n<script>\nInjected HTML block.",
        )
        for injected in injected_values:
            with self.subTest(injected=injected):
                invalid = proposal()
                invalid["body"]["procedure"] = injected  # type: ignore[index]
                with self.assertRaises(ValueError):
                    compile_draft(invalid, source_run_id="run_001")

    def test_normal_multiline_prose_remains_valid(self) -> None:
        candidate = proposal()
        candidate["body"]["procedure"] = (  # type: ignore[index]
            "First preserve the exact path.\n"
            "Then verify the exact bytes.\n"
            "Finally record the digest."
        )
        draft = compile_draft(candidate, source_run_id="run_001")
        self.assertIn(
            b"First preserve the exact path.\nThen verify the exact bytes.",
            draft.markdown,
        )

    def test_whitespace_only_typed_text_is_schema_invalid(self) -> None:
        invalid = proposal()
        invalid["body"]["procedure"] = " \n\t "  # type: ignore[index]
        with self.assertRaises(ValueError):
            compile_draft(
                invalid,
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )


class FieldNotesAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def _creator_live_result(
        self,
        *,
        calls: tuple[tuple[str, dict[str, object]], ...] = (),
        final_message: str = "Completed.",
        include_completion: bool = True,
        observed_status: str | None = None,
        request_extra: dict[str, object] | None = None,
        omit_request_call_id: bool = False,
        request_id_override: str | int | bool | None = None,
        completion_thread_id: str | None = None,
        mismatched_completion_content: bool = False,
        trusted_source_model_class: str = "stronger",
        trusted_target_model_class: str = "lower-cost",
    ) -> FieldNoteCodexRunResult:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = create_repository(Path(temporary.name))
        thread_id = "thread-creator-live-a1"
        turn_id = "turn-creator-live-a1"
        messages = handshake_messages(
            repository,
            thread_id=thread_id,
            turn_id=turn_id,
        )
        for index, (call_id, arguments) in enumerate(calls):
            request = proposal_request(
                thread_id=thread_id,
                turn_id=turn_id,
                call_id=call_id,
                request_id=(
                    f"proposal-request-{index}"
                    if request_id_override is None
                    else request_id_override
                ),
                arguments=arguments,
            )
            if request_extra:
                request["params"].update(request_extra)  # type: ignore[union-attr]
            if omit_request_call_id:
                request["params"].pop("callId")  # type: ignore[union-attr]
            messages.extend(
                [
                    started_proposal(
                        thread_id=thread_id,
                        turn_id=turn_id,
                        call_id=call_id,
                        arguments=arguments,
                    ),
                    request,
                ]
            )
            if include_completion:
                completion = completed_proposal(
                    thread_id=completion_thread_id or thread_id,
                    turn_id=turn_id,
                    call_id=call_id,
                    arguments=arguments,
                )
                completion_item = completion["params"]["item"]  # type: ignore[index]
                completion_item["status"] = (  # type: ignore[index]
                    observed_status
                    if observed_status is not None
                    else "completed"
                    if index == 0 and arguments == proposal()
                    else "failed"
                )
                if mismatched_completion_content:
                    completion_item["contentItems"] = []  # type: ignore[index]
                messages.append(completion)
        messages.extend(
            [
                completed_agent_message(
                    thread_id=thread_id,
                    turn_id=turn_id,
                    text=final_message,
                ),
                completed_turn(thread_id=thread_id, turn_id=turn_id),
            ]
        )
        factory = FakeTransportFactory([messages])
        engine = AccelerationEngine(
            repository,
            adapter=ADAPTER_NAME,
            adapter_version=CODEX_CLI_VERSION,
        )
        adapter = FieldNotesCodexAdapter(
            engine,
            input_func=lambda: None,
            stdout=io.StringIO(),
            transport_factory=factory,
            trusted_source_model_class=trusted_source_model_class,
            trusted_target_model_class=trusted_target_model_class,
            creator_live_a1_capture_provider=lambda: (
                FieldNoteCreatorLiveA1CaptureConfig(
                    "run-live-a1",
                    CodexRuntimeIdentity(
                        model=CODEX_MODEL,
                        reasoning_effort=CODEX_REASONING_EFFORT,
                        service_tier=CODEX_SERVICE_TIER,
                        codex_cli_version=CODEX_CLI_VERSION,
                        account_type="chatgpt",
                    ),
                )
            ),
        )
        result = await adapter.run(
            "Reason, propose once, and make no mutation."
        )
        starts = [
            message
            for message in factory.transports[0].sent
            if message.get("method") == "thread/start"
        ]
        self.assertEqual(1, len(starts))
        dynamic_tools = starts[0]["params"]["dynamicTools"]
        field_note_tools = [
            tool
            for tool in dynamic_tools
            if tool.get("name") == FIELD_NOTE_TOOL_NAME
        ]
        self.assertEqual(1, len(field_note_tools))
        self._creator_live_repository = repository
        self._creator_live_adapter = adapter
        self._creator_live_tool_spec = field_note_tools[0]
        self._creator_live_developer_instructions = starts[0]["params"][
            "developerInstructions"
        ]
        return result

    async def test_thread_start_schema_uses_same_trust_as_gate(self) -> None:
        level_two = proposal()
        level_two["value_level"] = 2
        unknown_result = await self._creator_live_result(
            calls=(("proposal-call-unknown", level_two),),
            observed_status="completed",
            trusted_source_model_class="UNKNOWN",
            trusted_target_model_class="UNKNOWN",
        )
        self.assertTrue(unknown_result.normal_terminal)
        self.assertEqual(
            [1, 2],
            self._creator_live_tool_spec["inputSchema"]["properties"][
                "value_level"
            ]["enum"],
        )
        self.assertEqual(
            "UNKNOWN",
            self._creator_live_adapter._field_note_gate.trusted_source_model_class,
        )
        self.assertEqual(
            "UNKNOWN",
            self._creator_live_adapter._field_note_gate.trusted_target_model_class,
        )

        configured_result = await self._creator_live_result(
            calls=(("proposal-call-configured", proposal()),),
            trusted_source_model_class="stronger",
            trusted_target_model_class="lower-cost",
        )
        self.assertTrue(configured_result.normal_terminal)
        self.assertEqual(
            [1, 2],
            self._creator_live_tool_spec["inputSchema"]["properties"][
                "value_level"
            ]["enum"],
        )
        self.assertEqual(
            set(),
            {
                "oneOf",
                "anyOf",
                "allOf",
                "enum",
                "const",
                "not",
            }.intersection(self._creator_live_tool_spec["inputSchema"]),
        )
        self.assertEqual(
            "stronger",
            self._creator_live_adapter._field_note_gate.trusted_source_model_class,
        )
        self.assertEqual(
            "lower-cost",
            self._creator_live_adapter._field_note_gate.trusted_target_model_class,
        )

    async def test_creator_live_trust_codes_are_generic_gate_rejections(
        self,
    ) -> None:
        mismatched = proposal()
        mismatched["source_model_class"] = "UNKNOWN"
        cases = (
            (
                "not-configured",
                proposal(),
                "UNKNOWN",
                "UNKNOWN",
                "level_3_trust_not_configured",
                "failed",
            ),
            (
                "class-mismatch",
                mismatched,
                "stronger",
                "lower-cost",
                "level_3_trust_class_mismatch",
                None,
            ),
        )
        for label, arguments, source, target, code, observed_status in cases:
            with self.subTest(case=label):
                result = await self._creator_live_result(
                    calls=((f"proposal-call-{label}", arguments),),
                    observed_status=observed_status,
                    trusted_source_model_class=source,
                    trusted_target_model_class=target,
                )
                self.assertFalse(result.normal_terminal)
                self.assertEqual(
                    "A1_PROPOSAL_GATE_REJECTED",
                    result.creator_live_a1_failure_reason,
                )
                self.assertIsNone(result.field_note_proposal)
                diagnostic = result.creator_live_a1_proposal_diagnostic
                assert diagnostic is not None
                self.assertEqual(code, diagnostic.gate_response_code)
                self.assertFalse(diagnostic.gate_response_success)
                self.assertEqual(
                    "A1_PROPOSAL_GATE_REJECTED",
                    diagnostic.final_subcause,
                )
                self.assertFalse(
                    (
                        self._creator_live_repository
                        / ".decision-os"
                        / "field-notes"
                    ).exists()
                )

    async def test_creator_live_mode_requires_one_valid_proposal(self) -> None:
        result = await self._creator_live_result(
            calls=(("proposal-call", proposal()),)
        )
        self.assertTrue(result.normal_terminal)
        self.assertTrue(result.creator_live_a1_capture)
        self.assertEqual("run-live-a1", result.run_id)
        self.assertEqual(1, result.creator_live_a1_proposal_attempts)
        self.assertIsNone(result.creator_live_a1_failure_reason)
        self.assertIsNotNone(result.field_note_proposal)
        diagnostic = result.creator_live_a1_proposal_diagnostic
        self.assertIsInstance(diagnostic, FieldNoteA1ProposalDiagnostic)
        assert diagnostic is not None
        self.assertIsNone(diagnostic.final_subcause)
        self.assertTrue(diagnostic.all_proposals_completed)
        self.assertEqual("proposal_accepted", diagnostic.gate_response_code)
        self.assertEqual(
            diagnostic,
            FieldNoteA1ProposalDiagnostic.from_dict(diagnostic.as_dict()),
        )
        self.assertIn(
            "must call propose_field_note_candidate exactly once",
            self._creator_live_developer_instructions,
        )
        self.assertIn(
            "Do not create, update, modify, delete, patch",
            self._creator_live_developer_instructions,
        )
        self.assertNotIn(
            "Use the typed file-change tool for exactly one file mutation",
            self._creator_live_developer_instructions,
        )

    async def test_creator_live_transport_start_failure_has_no_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = create_repository(Path(temporary))
            engine = AccelerationEngine(
                repository,
                adapter=ADAPTER_NAME,
                adapter_version=CODEX_CLI_VERSION,
            )

            def fail_transport_start(_executable: str):
                raise CodexAdapterFailure(
                    "transport failed before proposal lifecycle"
                )

            adapter = FieldNotesCodexAdapter(
                engine,
                input_func=lambda: None,
                stdout=io.StringIO(),
                transport_factory=fail_transport_start,
                trusted_source_model_class="stronger",
                trusted_target_model_class="lower-cost",
                creator_live_a1_capture_provider=lambda: (
                    FieldNoteCreatorLiveA1CaptureConfig(
                        "run-live-a1-transport-failure",
                        CodexRuntimeIdentity(
                            model=CODEX_MODEL,
                            reasoning_effort=CODEX_REASONING_EFFORT,
                            service_tier=CODEX_SERVICE_TIER,
                            codex_cli_version=CODEX_CLI_VERSION,
                            account_type="chatgpt",
                        ),
                    )
                ),
            )

            with self.assertRaises(CodexAdapterFailure):
                await adapter.run("Fail before the proposal lifecycle.")

            self.assertEqual(set(), adapter._capture_proposal_call_ids)
            self.assertIsNone(adapter._field_note_gate.accepted)

    async def test_creator_live_mode_rejects_missing_raw_output(self) -> None:
        for raw in (
            "# Raw Field Note\n\nNot a typed proposal.",
            json.dumps(proposal(), sort_keys=True),
        ):
            with self.subTest(raw=raw[:1]):
                result = await self._creator_live_result(final_message=raw)
                self.assertFalse(result.normal_terminal)
                self.assertEqual(
                    "A1_PROPOSAL_MISSING",
                    result.creator_live_a1_failure_reason,
                )
                self.assertIsNone(result.field_note_proposal)
                diagnostic = result.creator_live_a1_proposal_diagnostic
                assert diagnostic is not None
                self.assertEqual(0, diagnostic.proposal_call_count)
                self.assertIsNone(diagnostic.request_shape_valid)
                self.assertFalse(diagnostic.malformed_observed)
                self.assertEqual(
                    "A1_PROPOSAL_MISSING",
                    diagnostic.final_subcause,
                )

    async def test_creator_live_zero_identity_malformed_request_is_shape_invalid(
        self,
    ) -> None:
        cases = (
            ("missing", None, True, None),
            ("empty", {"callId": ""}, False, None),
            ("non-string", {"callId": 7}, False, None),
            ("invalid-request-id", None, False, True),
        )
        for label, request_extra, omit_call_id, request_id in cases:
            with self.subTest(case=label):
                result = await self._creator_live_result(
                    calls=(("proposal-call", proposal()),),
                    request_extra=request_extra,
                    omit_request_call_id=omit_call_id,
                    request_id_override=request_id,
                )
                diagnostic = result.creator_live_a1_proposal_diagnostic
                assert diagnostic is not None
                self.assertFalse(result.normal_terminal)
                self.assertEqual(
                    "A1_PROPOSAL_REQUEST_SHAPE_INVALID",
                    result.creator_live_a1_failure_reason,
                )
                self.assertEqual(0, diagnostic.proposal_call_count)
                self.assertIsNone(diagnostic.call_identity_sha256)
                self.assertFalse(diagnostic.request_shape_valid)
                self.assertTrue(diagnostic.malformed_observed)
                self.assertTrue(diagnostic.protocol_identity_failure)
                self.assertEqual(
                    "dynamic_tool_call",
                    diagnostic.protocol_failure_phase,
                )
                self.assertEqual(
                    "A1_PROPOSAL_REQUEST_SHAPE_INVALID",
                    diagnostic.final_subcause,
                )
                self.assertIsNone(result.field_note_proposal)
                self.assertFalse(
                    (
                        self._creator_live_repository
                        / ".decision-os"
                        / "field-notes"
                    ).exists()
                )

    async def test_creator_live_mode_rejects_duplicate_proposal(self) -> None:
        result = await self._creator_live_result(
            calls=(
                ("proposal-call-1", proposal()),
                ("proposal-call-2", proposal()),
            )
        )
        self.assertFalse(result.normal_terminal)
        self.assertEqual(
            "A1_PROPOSAL_DUPLICATE",
            result.creator_live_a1_failure_reason,
        )
        diagnostic = result.creator_live_a1_proposal_diagnostic
        assert diagnostic is not None
        self.assertEqual(2, diagnostic.proposal_call_count)
        self.assertEqual(
            "A1_PROPOSAL_DUPLICATE",
            diagnostic.final_subcause,
        )
        self.assertIsNone(result.field_note_proposal)

    async def test_creator_live_mode_rejects_malformed_proposal(self) -> None:
        malformed = proposal()
        malformed["value_level"] = 99
        result = await self._creator_live_result(
            calls=(("proposal-call", malformed),)
        )
        self.assertFalse(result.normal_terminal)
        self.assertEqual(
            "A1_PROPOSAL_SCHEMA_REJECTED",
            result.creator_live_a1_failure_reason,
        )
        self.assertIsNone(result.field_note_proposal)

    async def test_creator_live_mode_rejects_inconsistent_replay(self) -> None:
        changed = proposal()
        changed["title"] = "Changed replay identity"
        result = await self._creator_live_result(
            calls=(
                ("proposal-call", proposal()),
                ("proposal-call", changed),
            )
        )
        self.assertFalse(result.normal_terminal)
        self.assertEqual(
            "A1_PROPOSAL_INCONSISTENT_REPLAY",
            result.creator_live_a1_failure_reason,
        )
        self.assertEqual(1, result.creator_live_a1_proposal_attempts)
        self.assertIsNone(result.field_note_proposal)

    async def test_creator_live_request_shape_failure_is_retained(self) -> None:
        result = await self._creator_live_result(
            calls=(("proposal-call", proposal()),),
            request_extra={"unexpected": "value"},
        )
        diagnostic = result.creator_live_a1_proposal_diagnostic
        assert diagnostic is not None
        self.assertEqual(
            "A1_PROPOSAL_REQUEST_SHAPE_INVALID",
            result.creator_live_a1_failure_reason,
        )
        self.assertFalse(diagnostic.request_shape_valid)
        self.assertTrue(diagnostic.malformed_observed)

    async def test_creator_live_gate_rejection_is_retained(self) -> None:
        with patch.object(
            FieldNoteProposalGate,
            "propose",
            return_value=(False, "proposal_policy_rejected"),
        ):
            result = await self._creator_live_result(
                calls=(("proposal-call", proposal()),),
                observed_status="failed",
            )
        diagnostic = result.creator_live_a1_proposal_diagnostic
        assert diagnostic is not None
        self.assertEqual(
            "A1_PROPOSAL_GATE_REJECTED",
            diagnostic.final_subcause,
        )
        self.assertEqual(
            "proposal_policy_rejected",
            diagnostic.gate_response_code,
        )

    async def test_creator_live_accepted_item_not_completed_is_retained(self) -> None:
        result = await self._creator_live_result(
            calls=(("proposal-call", proposal()),),
            include_completion=False,
        )
        diagnostic = result.creator_live_a1_proposal_diagnostic
        assert diagnostic is not None
        self.assertEqual(
            "A1_PROPOSAL_ITEM_NOT_COMPLETED",
            diagnostic.final_subcause,
        )
        self.assertFalse(diagnostic.item_completion_observed)
        self.assertFalse(diagnostic.all_proposals_completed)

    async def test_creator_live_item_status_mismatch_is_retained(self) -> None:
        result = await self._creator_live_result(
            calls=(("proposal-call", proposal()),),
            observed_status="failed",
        )
        diagnostic = result.creator_live_a1_proposal_diagnostic
        assert diagnostic is not None
        self.assertEqual(
            "A1_PROPOSAL_ITEM_STATUS_MISMATCH",
            diagnostic.final_subcause,
        )
        self.assertEqual("failed", diagnostic.item_observed_status)
        self.assertEqual("completed", diagnostic.item_expected_status)

    async def test_creator_live_response_identity_mismatch_is_retained(self) -> None:
        result = await self._creator_live_result(
            calls=(("proposal-call", proposal()),),
            mismatched_completion_content=True,
        )
        diagnostic = result.creator_live_a1_proposal_diagnostic
        assert diagnostic is not None
        self.assertEqual(
            "A1_PROPOSAL_RESPONSE_IDENTITY_MISMATCH",
            diagnostic.final_subcause,
        )
        self.assertTrue(diagnostic.response_identity_mismatch)

    async def test_creator_live_protocol_failure_retains_exact_phase(self) -> None:
        result = await self._creator_live_result(
            calls=(("proposal-call", proposal()),),
            completion_thread_id="different-thread",
        )
        diagnostic = result.creator_live_a1_proposal_diagnostic
        assert diagnostic is not None
        self.assertEqual(
            "A1_PROPOSAL_PROTOCOL_IDENTITY_FAILURE",
            diagnostic.final_subcause,
        )
        self.assertTrue(diagnostic.protocol_identity_failure)
        self.assertEqual("dynamic_tool_call", diagnostic.protocol_failure_phase)

    def test_proposal_diagnostic_digest_and_payload_non_retention(self) -> None:
        diagnostic = FieldNoteA1ProposalDiagnostic(
            proposal_call_count=1,
            call_identity_sha256="1" * 64,
            request_identity_sha256="2" * 64,
            arguments_identity_sha256="3" * 64,
            request_shape_valid=True,
            malformed_observed=False,
            gate_invoked=True,
            gate_response_code="proposal_schema_invalid",
            gate_response_success=False,
            accepted_proposal_present=False,
            item_start_observed=True,
            item_completion_observed=True,
            item_observed_status="failed",
            item_expected_status="failed",
            all_proposals_completed=True,
            request_identity_mismatch=False,
            response_identity_mismatch=False,
            inconsistent_replay=False,
            protocol_identity_failure=False,
            protocol_failure_phase=None,
            direct_write_identity=None,
            final_subcause="A1_PROPOSAL_SCHEMA_REJECTED",
        )
        changed = replace(diagnostic, malformed_observed=True)
        self.assertNotEqual(
            diagnostic.diagnostic_sha256,
            changed.diagnostic_sha256,
        )
        encoded = json.dumps(diagnostic.as_dict(), sort_keys=True)
        self.assertNotIn("Approval byte binding", encoded)
        self.assertNotIn("reusable_structure", encoded)
        self.assertNotIn("Completed.", encoded)
        self.assertNotIn("arguments", diagnostic.as_dict())

    async def test_exact_proposal_request_replay_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = create_repository(Path(temporary))
            thread_id = "thread-field-note"
            turn_id = "turn-field-note"
            call_id = "proposal-call"
            request_id = "proposal-request"
            arguments = proposal()
            request = proposal_request(
                thread_id=thread_id,
                turn_id=turn_id,
                call_id=call_id,
                request_id=request_id,
                arguments=arguments,
            )
            messages = handshake_messages(
                repository,
                thread_id=thread_id,
                turn_id=turn_id,
            )
            messages.extend(
                [
                    started_proposal(
                        thread_id=thread_id,
                        turn_id=turn_id,
                        call_id=call_id,
                        arguments=arguments,
                    ),
                    request,
                    request,
                    completed_proposal(
                        thread_id=thread_id,
                        turn_id=turn_id,
                        call_id=call_id,
                        arguments=arguments,
                    ),
                    completed_agent_message(
                        thread_id=thread_id,
                        turn_id=turn_id,
                        text="Completed.",
                    ),
                    completed_turn(
                        thread_id=thread_id,
                        turn_id=turn_id,
                    ),
                ]
            )
            factory = FakeTransportFactory([messages])
            engine = AccelerationEngine(
                repository,
                adapter=ADAPTER_NAME,
                adapter_version=CODEX_CLI_VERSION,
            )
            adapter = FieldNotesCodexAdapter(
                engine,
                input_func=lambda: None,
                stdout=io.StringIO(),
                transport_factory=factory,
                trusted_source_model_class="stronger",
                trusted_target_model_class="lower-cost",
            )

            result = await adapter.run("Read and report one bounded insight.")

            self.assertTrue(result.normal_terminal)
            self.assertIsNotNone(result.field_note_proposal)
            responses = [
                message
                for message in factory.transports[0].sent
                if message.get("id") == request_id
            ]
            self.assertEqual(2, len(responses))
            self.assertEqual(responses[0], responses[1])
            self.assertTrue(responses[0]["result"]["success"])


class FieldNotesControllerTests(unittest.TestCase):
    def _controller(
        self,
        root: Path,
    ) -> tuple[FieldNotesCompanionController, Path]:
        repository = create_repository(root)
        controller = FieldNotesCompanionController(
            state_path=root / "state.json",
            picker_script=root / "picker.scpt",
        )
        controller.select_repository(repository)
        return controller, repository

    @staticmethod
    def _arm_candidate(
        controller: FieldNotesCompanionController,
        draft: object,
    ) -> None:
        with controller._condition:
            controller._run["state"] = "completed"
            controller._field_note_draft = draft
            controller._run["field_note"] = draft.public_candidate()

    @staticmethod
    def _eligible_result(draft: object) -> FieldNoteCodexRunResult:
        return FieldNoteCodexRunResult(
            run_id="run_001",
            normal_terminal=True,
            status="NORMAL_TERMINAL",
            error_type=None,
            turn_status="completed",
            runtime_identity=None,
            checkpoint_outcomes=(),
            final_message="Completed.",
            file_actions=(),
            read_evidence=(
                CodexReadEvidence(
                    path="seed.txt",
                    byte_count=5,
                    sha256=hashlib.sha256(b"seed\n").hexdigest(),
                    repository_identity="head",
                    status="succeeded",
                ),
            ),
            field_note_proposal=draft,
        )

    def test_failed_or_evidence_free_run_does_not_expose_candidate(self) -> None:
        draft = compile_draft(
            proposal(),
            source_run_id="run_001",
            created_at="2026-08-02T12:34:56Z",
            field_note_id="fn_fixed_identity",
        )
        result = CodexRunResult(
            run_id="run_001",
            normal_terminal=True,
            status="NORMAL_TERMINAL",
            error_type=None,
            turn_status="completed",
            runtime_identity=None,
            checkpoint_outcomes=(),
            final_message="Completed.",
            file_actions=(),
            read_evidence=(),
        )
        self.assertIsNone(
            FieldNotesCompanionController._eligible_draft(result)
        )
        failed = self._eligible_result(draft)
        failed = FieldNoteCodexRunResult(
            **{
                **failed.__dict__,
                "normal_terminal": False,
                "status": "ABNORMAL_TERMINAL",
            }
        )
        self.assertIsNone(
            FieldNotesCompanionController._eligible_draft(failed)
        )

    def test_controller_factory_owns_trusted_model_classes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = create_repository(root)
            controller = FieldNotesCompanionController(
                state_path=root / "state.json",
                picker_script=root / "picker.scpt",
                trusted_source_model_class="stronger",
                trusted_target_model_class="lower-cost",
            )
            engine = AccelerationEngine(
                repository,
                adapter=ADAPTER_NAME,
                adapter_version=CODEX_CLI_VERSION,
            )
            adapter = controller.adapter_factory(
                engine,
                lambda _: None,
                lambda _: None,
            )
            self.assertIsInstance(adapter, FieldNotesCodexAdapter)
            self.assertEqual(
                adapter.trusted_source_model_class,
                "stronger",
            )
            self.assertEqual(
                adapter.trusted_target_model_class,
                "lower-cost",
            )

    def test_invalid_compiled_structure_is_rejected_before_approval(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller, repository = self._controller(root)
            draft = compile_draft(
                proposal(),
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )
            injected = draft.markdown.replace(
                b"\n## Evidence\n",
                b"\n## Injected\nambiguous\n\n## Evidence\n",
                1,
            )
            tampered = replace(
                draft,
                markdown=injected,
                sha256=hashlib.sha256(injected).hexdigest(),
            )
            self._arm_candidate(controller, tampered)
            with self.assertRaises(FieldNoteError):
                controller.field_note_save()
            self.assertIsNone(controller._field_note_pending)
            self.assertFalse((repository / draft.relative_path).exists())

    def test_skip_changes_no_repository_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller, repository = self._controller(root)
            draft = compile_draft(
                proposal(),
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )
            before = sorted(
                path.relative_to(repository).as_posix()
                for path in repository.rglob("*")
                if ".git" not in path.parts
            )
            self._arm_candidate(controller, draft)
            snapshot = controller.field_note_skip()
            after = sorted(
                path.relative_to(repository).as_posix()
                for path in repository.rglob("*")
                if ".git" not in path.parts
            )
            self.assertEqual(before, after)
            self.assertEqual(snapshot["run"]["field_note"], {"state": "skipped"})

    def test_save_requires_approval_then_creates_exact_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller, repository = self._controller(root)
            draft = compile_draft(
                proposal(),
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )
            self._arm_candidate(controller, draft)
            approval = controller.field_note_save()
            target = repository / draft.relative_path
            self.assertFalse(target.exists())
            surface = approval["run"]["field_note"]["approval"]
            self.assertEqual(surface["action"], "CREATE")
            self.assertEqual(surface["precondition"], "MUST_NOT_EXIST")
            self.assertEqual(
                surface["approval_scope"],
                "THIS ONE FILE ONLY",
            )
            self.assertEqual(surface["content_sha256"], draft.sha256)
            real_open = os.open
            open_calls: list[tuple[str, int, int | None]] = []

            def traced_open(
                path: object,
                flags: int,
                mode: int = 0o777,
                *,
                dir_fd: int | None = None,
            ) -> int:
                open_calls.append((os.fspath(path), flags, dir_fd))
                if dir_fd is None:
                    return real_open(path, flags, mode)
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with patch.object(
                controller,
                "_descriptor_containment_supported",
                return_value=None,
            ), patch(
                "decision_os.companion.field_notes_controller.os.open",
                side_effect=traced_open,
            ):
                saved = controller.field_note_approval("allow_once")
            self.assertEqual(target.read_bytes(), draft.markdown)
            self.assertEqual(
                hashlib.sha256(target.read_bytes()).hexdigest(),
                draft.sha256,
            )
            self.assertEqual(
                saved["run"]["field_note"],
                {"state": "saved", "path": draft.relative_path},
            )
            create_calls = [
                call for call in open_calls if call[1] & os.O_CREAT
            ]
            self.assertEqual(1, len(create_calls))
            self.assertEqual(target.name, create_calls[0][0])
            self.assertFalse(Path(create_calls[0][0]).is_absolute())
            self.assertIsNotNone(create_calls[0][2])

    def test_parent_symlink_before_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller, repository = self._controller(root)
            external = root / "external"
            external.mkdir()
            (repository / ".decision-os").symlink_to(
                external,
                target_is_directory=True,
            )
            draft = compile_draft(proposal(), source_run_id="run_001")
            self._arm_candidate(controller, draft)
            with self.assertRaises(FieldNoteError):
                controller.field_note_save()
            self.assertEqual([], list(external.iterdir()))

    def test_parent_swap_after_descriptor_open_writes_nothing_external(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller, repository = self._controller(root)
            external = root / "external"
            external.mkdir()
            draft = compile_draft(
                proposal(),
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )
            self._arm_candidate(controller, draft)
            controller.field_note_save()
            filename = Path(draft.relative_path).name
            real_open = os.open
            swapped = False

            def swap_before_create(
                path: object,
                flags: int,
                mode: int = 0o777,
                *,
                dir_fd: int | None = None,
            ) -> int:
                nonlocal swapped
                if (
                    not swapped
                    and os.fspath(path) == filename
                    and flags & os.O_CREAT
                ):
                    swapped = True
                    (repository / ".decision-os").rename(
                        repository / ".decision-os-original"
                    )
                    (repository / ".decision-os").symlink_to(
                        external,
                        target_is_directory=True,
                    )
                if dir_fd is None:
                    return real_open(path, flags, mode)
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with patch.object(
                controller,
                "_descriptor_containment_supported",
                return_value=None,
            ), patch(
                "decision_os.companion.field_notes_controller.os.open",
                side_effect=swap_before_create,
            ):
                with self.assertRaises(FieldNoteError):
                    controller.field_note_approval("allow_once")
            self.assertTrue(swapped)
            self.assertEqual([], list(external.iterdir()))
            self.assertFalse(
                (
                    repository
                    / ".decision-os-original"
                    / "field-notes"
                    / filename
                ).exists()
            )
            with self.assertRaises(FieldNoteError):
                controller.field_note_approval("allow_once")

    def test_casefold_sibling_race_fails_closed_and_consumes_approval(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller, repository = self._controller(root)
            draft = compile_draft(
                proposal(),
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )
            self._arm_candidate(controller, draft)
            controller.field_note_save()
            target = repository / draft.relative_path
            filename = target.name
            competing_name = filename.upper()
            competing_bytes = b"competing sibling remains unchanged\n"
            competitor = target.with_name("casefold-race-sentinel")
            real_open = os.open
            real_listdir = os.listdir
            inserted = False

            def raced_open(
                path: object,
                flags: int,
                mode: int = 0o777,
                *,
                dir_fd: int | None = None,
            ) -> int:
                nonlocal inserted
                if (
                    not inserted
                    and os.fspath(path) == filename
                    and flags & os.O_CREAT
                ):
                    inserted = True
                    competitor.write_bytes(competing_bytes)
                if dir_fd is None:
                    return real_open(path, flags, mode)
                return real_open(path, flags, mode, dir_fd=dir_fd)

            def raced_listdir(path: object) -> list[str]:
                entries = real_listdir(path)
                if inserted and competitor.name in entries:
                    return [
                        competing_name if name == competitor.name else name
                        for name in entries
                    ]
                return entries

            self.assertNotEqual(competing_name, filename)
            self.assertEqual(competing_name.casefold(), filename.casefold())
            with patch.object(
                controller,
                "_descriptor_containment_supported",
                return_value=None,
            ), patch(
                "decision_os.companion.field_notes_controller.os.open",
                side_effect=raced_open,
            ), patch(
                "decision_os.companion.field_notes_controller.os.listdir",
                side_effect=raced_listdir,
            ):
                with self.assertRaises(FieldNoteError):
                    controller.field_note_approval("allow_once")

            self.assertTrue(inserted)
            self.assertEqual(competitor.read_bytes(), competing_bytes)
            self.assertFalse(target.exists())
            state = controller.snapshot()["run"]["field_note"]
            self.assertEqual("candidate", state["state"])
            self.assertIn("new exact Approval", state["error"])
            with self.assertRaises(FieldNoteError):
                controller.field_note_approval("allow_once")
            renewed = controller.field_note_save()
            self.assertEqual(
                "approval",
                renewed["run"]["field_note"]["state"],
            )

    def test_failed_allow_once_requires_a_fresh_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller, repository = self._controller(root)
            draft = compile_draft(
                proposal(),
                source_run_id="run_001",
                created_at="2026-08-02T12:34:56Z",
                field_note_id="fn_fixed_identity",
            )
            target = repository / draft.relative_path
            target.parent.mkdir(parents=True)
            self._arm_candidate(controller, draft)
            controller.field_note_save()
            target.write_bytes(b"collision\n")
            with self.assertRaises(FieldNoteError):
                controller.field_note_approval("allow_once")
            self.assertEqual(b"collision\n", target.read_bytes())
            state = controller.snapshot()["run"]["field_note"]
            self.assertEqual("candidate", state["state"])
            self.assertIn("new exact Approval", state["error"])
            with self.assertRaises(FieldNoteError):
                controller.field_note_approval("allow_once")
            renewed = controller.field_note_save()
            self.assertEqual(
                "approval",
                renewed["run"]["field_note"]["state"],
            )
            self.assertNotEqual(
                draft.relative_path,
                renewed["run"]["field_note"]["approval"]["path"],
            )


class FieldNotesStaticUiTests(unittest.TestCase):
    def _run_action_harness(
        self,
        initial_state: dict[str, object],
        scenario: str,
    ) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for client behavior tests.")
        javascript = (
            Path(__file__).resolve().parents[1]
            / "decision_os"
            / "companion"
            / "static"
            / "field_notes.js"
        )
        harness = r'''
"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const javascriptPath = process.argv[2];
const source = fs.readFileSync(javascriptPath, "utf8");

class Element {
  constructor(tagName = "div") {
    this.tagName = tagName.toUpperCase();
    this.id = "";
    this.className = "";
    this.hidden = false;
    this.disabled = false;
    this.type = "";
    this.children = [];
    this.parentNode = null;
    this.listeners = new Map();
    this.attributes = new Map();
    this.ownText = "";
  }

  get firstChild() {
    return this.children[0] || null;
  }

  get textContent() {
    return this.ownText + this.children.map((child) => child.textContent).join("");
  }

  set textContent(value) {
    this.ownText = value == null ? "" : String(value);
    for (const child of this.children) child.parentNode = null;
    this.children = [];
  }

  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }

  removeChild(child) {
    const index = this.children.indexOf(child);
    assert.notStrictEqual(index, -1, "Cannot remove a missing child.");
    this.children.splice(index, 1);
    child.parentNode = null;
    return child;
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
  }

  getAttribute(name) {
    return this.attributes.has(name) ? this.attributes.get(name) : null;
  }

  removeAttribute(name) {
    this.attributes.delete(name);
  }

  addEventListener(name, callback) {
    const listeners = this.listeners.get(name) || [];
    listeners.push(callback);
    this.listeners.set(name, listeners);
  }

  dispatch(name) {
    for (const callback of this.listeners.get(name) || []) {
      callback({ target: this });
    }
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }

  querySelectorAll(selector) {
    const matches = [];
    for (const child of this.children) {
      if (selector === "button" && child.tagName === "BUTTON") {
        matches.push(child);
      } else if (
        selector.startsWith(".") &&
        child.className.split(/\s+/).includes(selector.slice(1))
      ) {
        matches.push(child);
      }
      matches.push(...child.querySelectorAll(selector));
    }
    return matches;
  }
}

const document = {
  body: new Element("body"),
  createElement(tagName) {
    return new Element(tagName);
  },
};
const fetchCalls = [];
const fetchQueue = [];
async function fetchMock(path, options = {}) {
  fetchCalls.push({ path, options });
  assert(fetchQueue.length > 0, `Unexpected fetch: ${path}`);
  return fetchQueue.shift()();
}
function response(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    async json() {
      return body;
    },
  };
}
function deferred() {
  let resolve;
  const promise = new Promise((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}
async function settle() {
  await new Promise((resolve) => setImmediate(resolve));
  await new Promise((resolve) => setImmediate(resolve));
}
function actionButton(root, label) {
  const found = root
    .querySelectorAll("button")
    .find((candidate) => candidate.textContent === label);
  assert(found, `Missing action button: ${label}`);
  return found;
}
function postCount(path) {
  return fetchCalls.filter(
    (call) => call.path === path && call.options.method === "POST",
  ).length;
}

async function main() {
  const initialState = __INITIAL_STATE__;
  fetchQueue.push(() => Promise.resolve(response(initialState)));
  const window = {
    setInterval() {
      return 1;
    },
  };
  const sandbox = {
    Error,
    JSON,
    Promise,
    String,
    console,
    document,
    fetch: fetchMock,
    window,
  };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox, { filename: javascriptPath });
  await settle();
  __SCENARIO__
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
'''.replace("__INITIAL_STATE__", json.dumps(initial_state)).replace(
            "__SCENARIO__", scenario
        )
        completed = subprocess.run(
            [node, "-", str(javascript)],
            input=harness,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(
            0,
            completed.returncode,
            msg=(
                "Node Field Notes action harness failed:\n"
                f"{completed.stdout}{completed.stderr}"
            ),
        )

    @staticmethod
    def _candidate_state() -> dict[str, object]:
        return {
            "csrf": "csrf-candidate",
            "run": {
                "field_note": {
                    "state": "candidate",
                    "title": "Approval byte binding",
                    "value_level": 3,
                    "reusable_structure": "Bind the exact bytes.",
                }
            },
        }

    @staticmethod
    def _approval_state() -> dict[str, object]:
        return {
            "csrf": "csrf-approval",
            "run": {
                "field_note": {
                    "state": "approval",
                    "approval": {
                        "action": "CREATE",
                        "path": ".decision-os/field-notes/approval-byte-binding.md",
                        "content_sha256": "a" * 64,
                        "precondition": "MUST_NOT_EXIST",
                        "approval_scope": "THIS ONE FILE ONLY",
                        "content": "# Approval byte binding\n",
                    },
                }
            },
        }

    def test_save_is_visible_single_flight_and_restores_or_renders(self) -> None:
        approval_state = json.dumps(self._approval_state())
        self._run_action_harness(
            self._candidate_state(),
            rf'''
  const root = document.body.children[0];
  const save = actionButton(root, "Save");
  const skip = actionButton(root, "Skip");
  const pending = deferred();
  fetchQueue.push(() => pending.promise);

  save.dispatch("click");
  assert.strictEqual(save.textContent, "Preparing approval…");
  assert.strictEqual(save.disabled, true);
  assert.strictEqual(skip.disabled, true);
  assert.strictEqual(root.getAttribute("aria-busy"), "true");
  save.dispatch("click");
  skip.dispatch("click");
  assert.strictEqual(postCount("/api/field-notes/save"), 1);
  assert.strictEqual(postCount("/api/field-notes/skip"), 0);

  pending.resolve(response({{ error: "Save failed visibly." }}, 500));
  await settle();
  assert.strictEqual(save.textContent, "Save");
  assert.strictEqual(skip.textContent, "Skip");
  assert.strictEqual(save.disabled, false);
  assert.strictEqual(skip.disabled, false);
  assert.strictEqual(root.getAttribute("aria-busy"), null);
  assert.strictEqual(
    root.querySelector(".field-note-error").textContent,
    "Save failed visibly.",
  );

  fetchQueue.push(() => Promise.resolve(response({approval_state})));
  save.dispatch("click");
  await settle();
  assert.strictEqual(postCount("/api/field-notes/save"), 2);
  assert.strictEqual(root.getAttribute("aria-busy"), null);
  assert(root.textContent.includes("CREATE .decision-os/field-notes/approval-byte-binding.md"));
  assert(actionButton(root, "Allow once"));
''',
        )

    def test_allow_once_is_visible_single_flight_and_restores_or_saves(
        self,
    ) -> None:
        saved_path = ".decision-os/field-notes/approval-byte-binding.md"
        saved_state = json.dumps(
            {
                "csrf": "csrf-saved",
                "run": {
                    "field_note": {
                        "state": "saved",
                        "path": saved_path,
                    }
                },
            }
        )
        self._run_action_harness(
            self._approval_state(),
            rf'''
  const root = document.body.children[0];
  const allowOnce = actionButton(root, "Allow once");
  const deny = actionButton(root, "Deny");
  const pending = deferred();
  fetchQueue.push(() => pending.promise);

  allowOnce.dispatch("click");
  assert.strictEqual(allowOnce.textContent, "Saving Field Note…");
  assert.strictEqual(allowOnce.disabled, true);
  assert.strictEqual(deny.disabled, true);
  assert.strictEqual(root.getAttribute("aria-busy"), "true");
  allowOnce.dispatch("click");
  deny.dispatch("click");
  assert.strictEqual(postCount("/api/field-notes/approval"), 1);

  pending.resolve(response({{ error: "Allow once failed visibly." }}, 500));
  await settle();
  assert.strictEqual(allowOnce.textContent, "Allow once");
  assert.strictEqual(deny.textContent, "Deny");
  assert.strictEqual(allowOnce.disabled, false);
  assert.strictEqual(deny.disabled, false);
  assert.strictEqual(root.getAttribute("aria-busy"), null);
  assert.strictEqual(
    root.querySelector(".field-note-error").textContent,
    "Allow once failed visibly.",
  );
  assert.strictEqual(root.querySelector(".field-note-saved-path"), null);
  assert(root.textContent.includes("THIS ONE FILE ONLY"));

  fetchQueue.push(() => Promise.resolve(response({saved_state})));
  allowOnce.dispatch("click");
  await settle();
  assert.strictEqual(postCount("/api/field-notes/approval"), 2);
  assert.strictEqual(root.getAttribute("aria-busy"), null);
  assert.strictEqual(root.children.length, 1);
  assert.strictEqual(root.children[0].tagName, "CODE");
  assert.strictEqual(root.children[0].className, "field-note-saved-path");
  assert.strictEqual(root.children[0].textContent, {json.dumps(saved_path)});
''',
        )

    def test_approval_renders_the_exact_one_file_scope(self) -> None:
        javascript = (
            Path(__file__).resolve().parents[1]
            / "decision_os"
            / "companion"
            / "static"
            / "field_notes.js"
        ).read_text(encoding="utf-8")
        self.assertIn("approval.approval_scope", javascript)


if __name__ == "__main__":
    unittest.main()
