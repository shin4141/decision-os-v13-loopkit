from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from decision_os.companion import field_notes_creator_live_candidate_v0_2 as v02
from decision_os.companion.field_notes_creator_live import (
    FieldNoteCreatorLiveA3CompilerAudit,
    FieldNoteCreatorLiveA3RejectionCounts,
    FieldNoteCreatorLiveProofRuntime,
    FieldNoteCreatorLiveValidationError,
)
from decision_os.companion.field_notes_creator_live_candidate import (
    CANDIDATE_ID as V01_CANDIDATE_ID,
    RUN_1_SHA256 as V01_RUN_1_SHA256,
    RUN_2_SHA256 as V01_RUN_2_SHA256,
    verify_fixed_before as verify_v01_before,
    verify_fixed_tasks as verify_v01_tasks,
)
from decision_os.companion.field_notes_model import canonical_json, compile_draft
from decision_os.companion.field_notes_reuse import FieldNoteIdentity


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "validation/fixtures/creator_live_agents_before_after_v0_2"
WITNESS = (
    "A3 Witness: The human Decision Owner retains the final seat for every "
    "bounded agent recommendation."
)
PUBLIC_AFTER_TEXT = "\n".join(
    (
        "B01 Human Seat: The human Decision Owner retains the final seat.",
        "B02 Authority Boundary: Authority scope does not create authority and no expansion is inferred.",
        "B03 Guard and Safety: Preserve protected artifacts and do not weaken safety guards.",
        "B04 Responsibility Transfer: A handoff closes when the receiver owns responsibility and the next action.",
        "B05 Stop Conditions: Stop and HOLD when a prerequisite is missing or unsafe.",
        "B06 Evidence and Provenance: Identity and provenance require verified readback evidence before continuation.",
        "B07 Handoff and Completion: Handoff restart state includes the Completion Line and next safe action.",
        "B08 Agent and Human Roles: Agents execute bounded work; human approval governs risk and value.",
        "B09 Routine Cleanup: The agent performs routine cleanup; do not return it to Shin.",
        "B10 Forward Change and Rollback: A Forward-only normal revert preserves protected artifacts during rollback.",
        WITNESS,
    )
)


def _draft(reusable: str = PUBLIC_AFTER_TEXT):
    return compile_draft(
        {
            "title": "Historical Before Bounded Agent Instructions",
            "value_level": 2,
            "source_model_class": "stronger",
            "target_model_class": "lower-cost",
            "trigger_terms": ["historical agent instructions"],
            "scope": {
                "task_family": "agent governance",
                "path_prefixes": ["before/AGENTS.md"],
                "exclude_terms": ["live proof"],
            },
            "body": {
                "trigger": "Use for the fixed historical Before candidate.",
                "reusable_structure": reusable,
                "scope": "Candidate v0.2 fixture scope only.",
                "do_not_apply_when": "Do not substitute another source.",
                "procedure": "Preserve every fixed boundary and generated Witness.",
                "acceptance": "Every fixed content-free Gate passes.",
                "evidence": "Use exact hashes and typed readback.",
                "remaining_unknowns": "Artifact behavior remains NOT_RUN.",
            },
        },
        source_run_id="run_fixture_v02_origin",
        created_at="2026-08-05T23:39:00Z",
        field_note_id="fn_fixture_candidate_v02",
    )


def _identity(draft=None):
    draft = draft or _draft()
    return FieldNoteIdentity(
        note_path=draft.relative_path,
        field_note_id=draft.field_note_id,
        note_sha256=draft.sha256,
        origin_run_id=draft.source_run_id,
    )


def _task_bytes() -> tuple[bytes, bytes]:
    return tuple((ROOT / value.path).read_bytes() for value in v02.FIXED_TASK_IDENTITIES)


def _pass_evidence(**overrides):
    tasks = _task_bytes()
    values = dict(
        contract_identity_sha256="a" * 64,
        run_1_task_sha256=v02.RUN_1_SHA256,
        developer_instructions_sha256=hashlib.sha256(
            v02.CANDIDATE_DEVELOPER_INSTRUCTIONS.encode()
        ).hexdigest(),
        dynamic_tool_manifest_sha256=v02.dynamic_tool_manifest_sha256(),
        runtime_identity_sha256="b" * 64,
        isolation_features_sha256=v02.isolation_features_sha256(),
        candidate_visible_input_set_sha256=v02.candidate_visible_input_set_sha256(
            tasks[0],
            v02.CANDIDATE_DEVELOPER_INSTRUCTIONS.encode(),
            v02.candidate_dynamic_tools(),
        ),
        event_log_sha256="c" * 64,
        source_identity_sha256=v02.fixed_source_identity_sha256(),
        source_call_count=1,
        semantic_disclosure_count=1,
        distinct_exposed_source_count=1,
        repository_read_count=0,
        current_after_access_count=0,
        git_access_count=0,
        prohibited_capability_event_count=0,
        proposal_call_count=1,
        proposal_after_source=True,
        normal_terminal=True,
        capability_surface_complete=True,
        native_or_implicit_reader_absent=True,
        manual_after_exposure_codes=(),
        event_reason_codes=(),
    )
    values.update(overrides)
    return v02.IsolationEvidence(**values)


def _core():
    before = v02.load_fixed_source()
    tasks = _task_bytes()
    draft = _draft()
    projection = v02.project_public_after(draft.markdown)
    safety = v02.public_safety(projection.body)
    boundaries = v02.check_boundaries_v0_2(projection.body, safety)
    witness = v02.bind_generated_witness_v0_2(
        _identity(draft), draft.markdown, projection, tasks[0], tasks[1], safety
    )
    compression = v02.compression_receipt(before, projection.body)
    isolation, independence = v02.qualify_independence(_pass_evidence())
    gate = v02.issue_post_a1_gate_v0_2(
        before=before,
        task_bytes=tasks,
        note_identity=_identity(draft),
        note_bytes=draft.markdown,
        source_isolation=isolation,
        independence=independence,
        projection=projection,
        compression=compression,
        safety=safety,
        boundaries=boundaries,
        witness_binding=witness,
    )
    return (
        before,
        tasks,
        draft,
        projection,
        safety,
        boundaries,
        witness,
        compression,
        isolation,
        independence,
        gate,
    )


class SourceAndTaskFixationTests(unittest.TestCase):
    def test_01_packaged_source_exact_identity(self):
        source = v02.load_fixed_source()
        self.assertEqual(len(source), 20_705)
        self.assertEqual(source.count(b"\n"), 517)
        self.assertEqual(hashlib.sha256(source).hexdigest(), v02.SOURCE_SHA256)
        self.assertTrue(source.endswith(b"\n"))

    def test_02_packaged_source_equals_historical_git_artifact(self):
        self.assertEqual(
            v02.verify_packaged_source_against_git(ROOT), v02.FIXED_SOURCE_IDENTITY
        )

    def test_03_source_rejects_drift_truncation_and_missing_lf(self):
        source = v02.load_fixed_source()
        for value in (source[:-1], source + b" ", source.replace(b"V13", b"V12", 1)):
            with self.subTest(size=len(value)), self.assertRaises(v02.CandidateV02Error):
                v02._fixed_bytes(value)

    def test_04_source_rejects_invalid_utf8(self):
        with self.assertRaises(v02.CandidateV02Error):
            v02._fixed_bytes(b"\xff\n")

    def test_05_tasks_exact_identities(self):
        first, second = v02.verify_fixed_tasks(ROOT)
        self.assertEqual((first.sha256, second.sha256), (v02.RUN_1_SHA256, v02.RUN_2_SHA256))
        self.assertEqual((first.byte_count, second.byte_count), (2713, 2703))
        self.assertEqual((first.line_count, second.line_count), (68, 56))

    def test_06_tasks_contain_no_fixture_witness(self):
        for task in _task_bytes():
            self.assertNotIn(WITNESS.encode(), task)

    def test_07_tasks_and_developer_text_have_no_manual_after_contamination(self):
        before_lines = set(v02.load_fixed_source().splitlines())
        manual = (ROOT / "AGENTS.md").read_bytes()
        after_only = {
            hashlib.sha256(line).hexdigest()
            for line in manual.splitlines()
            if len(line.strip()) >= 32 and line not in before_lines
        }
        material = (*_task_bytes(), v02.CANDIDATE_DEVELOPER_INSTRUCTIONS.encode())
        self.assertEqual(
            v02.manual_after_contamination_codes(
                material, after_only_line_sha256=after_only
            ),
            (),
        )

    def test_08_manual_after_identity_diff_and_text_are_rejected(self):
        after_line = next(
            line
            for line in (ROOT / "AGENTS.md").read_bytes().splitlines()
            if len(line.strip()) >= 32 and line not in set(v02.load_fixed_source().splitlines())
        )
        hashes = [hashlib.sha256(after_line).hexdigest()]
        material = [
            v02.MANUAL_AFTER_SHA256.encode(),
            b"--- before/AGENTS.md\n+++ after/AGENTS.md\n@@ -1,2 +1,2 @@\n",
            after_line,
        ]
        codes = v02.manual_after_contamination_codes(material, after_only_line_sha256=hashes)
        self.assertEqual(
            set(codes),
            {
                "MANUAL_AFTER_IDENTITY_EXPOSED",
                "MANUAL_AFTER_DIFF_EXPOSED",
                "MANUAL_AFTER_ONLY_TEXT_EXPOSED",
            },
        )


class FixedSourceToolAndIndependenceTests(unittest.TestCase):
    def test_09_source_tool_empty_schema_no_path(self):
        schema = v02.SOURCE_TOOL_SPEC["inputSchema"]
        self.assertEqual(schema, {"type": "object", "additionalProperties": False, "maxProperties": 0})
        self.assertNotIn("properties", schema)

    def test_10_dynamic_manifest_has_exact_two_tools(self):
        tools = v02.candidate_dynamic_tools()
        self.assertEqual(
            [value["name"] for value in tools],
            [v02.SOURCE_TOOL_NAME, "propose_field_note_candidate"],
        )
        self.assertNotIn("read_repository_text_file", canonical_json(tools))

    def test_11_first_call_discloses_once_and_replay_is_cached(self):
        session = v02.FixedSourceToolSession()
        first = session.call("source-1", {})
        replay = session.call("source-1", {})
        self.assertTrue(first.success)
        self.assertEqual(first, replay)
        self.assertEqual(session.source_call_count, 1)
        self.assertEqual(session.semantic_disclosure_count, 1)
        content = first.payload["content"].encode()
        self.assertEqual(hashlib.sha256(content).hexdigest(), v02.SOURCE_SHA256)

    def test_12_second_distinct_call_fails(self):
        session = v02.FixedSourceToolSession()
        session.call("source-1", {})
        second = session.call("source-2", {})
        self.assertFalse(second.success)
        self.assertEqual(second.code, "SOURCE_ALREADY_CONSUMED")

    def test_13_nonempty_arguments_and_inconsistent_replay_fail(self):
        session = v02.FixedSourceToolSession()
        bad = session.call("source-1", {"path": "AGENTS.md"})
        replay = session.call("source-1", {})
        self.assertEqual(bad.code, "SOURCE_ARGUMENTS_INVALID")
        self.assertEqual(replay.code, "SOURCE_REPLAY_INCONSISTENT")

    def test_14_isolation_fixture_result_vocabulary(self):
        fixture = json.loads((FIXTURES / "source_isolation_transcripts.json").read_bytes())
        for case in fixture["cases"]:
            overrides = dict(case["overrides"])
            for field in ("manual_after_exposure_codes", "event_reason_codes"):
                if field in overrides:
                    overrides[field] = tuple(overrides[field])
            isolation, independence = v02.qualify_independence(_pass_evidence(**overrides))
            with self.subTest(case=case["case_id"]):
                self.assertEqual(isolation.result, case["expected"])
                self.assertEqual(independence.result, case["expected"])

    def test_15_only_terminal_pass_admits_proposal(self):
        gate = v02.CandidateV02A1AdmissionGate()
        isolation, independence = v02.qualify_independence(_pass_evidence())
        self.assertEqual(
            gate.admit("proposal", isolation=isolation, independence=independence),
            "proposal",
        )
        failed_isolation, failed_independence = v02.qualify_independence(
            _pass_evidence(repository_read_count=1)
        )
        self.assertIsNone(
            gate.admit(
                "proposal",
                isolation=failed_isolation,
                independence=failed_independence,
            )
        )

    def test_16_latent_model_memory_is_explicit_nonclaim(self):
        isolation, independence = v02.qualify_independence(_pass_evidence())
        self.assertFalse(independence.latent_model_memory_excluded)
        with self.assertRaises(v02.CandidateV02Error):
            replace(independence, latent_model_memory_excluded=True)

    def test_16a_malformed_or_mismatched_identity_cannot_pass(self):
        for overrides, expected in (
            ({"contract_identity_sha256": "x"}, "NOT_ESTABLISHED"),
            ({"contract_identity_sha256": "x", "repository_read_count": 1}, "FAIL"),
            ({"developer_instructions_sha256": "d" * 64}, "FAIL"),
            ({"source_identity_sha256": "e" * 64}, "FAIL"),
            ({"candidate_visible_input_set_sha256": "f" * 64}, "FAIL"),
        ):
            with self.subTest(overrides=overrides):
                isolation, independence = v02.qualify_independence(
                    _pass_evidence(**overrides)
                )
                self.assertEqual((isolation.result, independence.result), (expected, expected))

    def test_16b_forged_pass_receipts_do_not_admit_a1(self):
        isolation, independence = v02.qualify_independence(_pass_evidence())
        forged_isolation = replace(
            isolation,
            repository_read_count=99,
            prohibited_capability_event_count=99,
        )
        forged_independence = replace(
            independence,
            source_isolation_receipt_sha256=forged_isolation.receipt_sha256,
        )
        self.assertIsNone(
            v02.CandidateV02A1AdmissionGate().admit(
                "proposal",
                isolation=forged_isolation,
                independence=forged_independence,
            )
        )


class ProjectionGateAndA3Tests(unittest.TestCase):
    def test_17_projection_compression_safety_boundaries_witness_pass(self):
        values = _core()
        projection, safety, boundaries, witness, compression = (
            values[3], values[4], values[5], values[6], values[7]
        )
        self.assertLess(projection.utf8_byte_count, 20_705)
        self.assertEqual(compression.before_byte_count, 20_705)
        self.assertEqual(compression.result, "PASS")
        self.assertEqual(safety.result, "PASS")
        self.assertEqual([value.status for value in boundaries], ["PRESENT"] * 10)
        self.assertEqual(witness.policy_result, "PASS")

    def test_18_compression_fraction_uses_20705(self):
        values = _core()
        compression = values[7]
        expected = v02.Decimal(compression.reduction_byte_count) / v02.Decimal(20_705)
        self.assertEqual(
            compression.reduction_fraction,
            format(expected.quantize(v02.Decimal("0.000001"), rounding=v02.ROUND_HALF_UP), ".6f"),
        )

    def test_19_boundaries_preserve_order_matchers_and_historical_rationale(self):
        self.assertEqual(
            [value.boundary_id for value in v02.BOUNDARY_SPECS],
            [
                "B01_HUMAN_SEAT", "B02_AUTHORITY", "B03_GUARD_SAFETY",
                "B04_RESPONSIBILITY_TRANSFER", "B05_STOP_CONDITIONS",
                "B06_EVIDENCE_PROVENANCE", "B07_HANDOFF_COMPLETION",
                "B08_AGENT_HUMAN_ROLES", "B09_ROUTINE_CLEANUP",
                "B10_FORWARD_ROLLBACK",
            ],
        )
        self.assertTrue(all("Historical Before lines" in value.rationale for value in v02.BOUNDARY_SPECS))
        self.assertTrue(all(value.matcher_id.endswith(".v0.1") for value in v02.BOUNDARY_SPECS))

    def test_20_missing_or_duplicate_boundary_fails(self):
        draft = _draft(PUBLIC_AFTER_TEXT.replace("B01 Human Seat:", "B01 Missing:"))
        projection = v02.project_public_after(draft.markdown)
        results = v02.check_boundaries_v0_2(projection.body, v02.public_safety(projection.body))
        self.assertEqual(results[0].status, "MISSING")
        duplicated = _draft(PUBLIC_AFTER_TEXT + "\n" + PUBLIC_AFTER_TEXT.splitlines()[0])
        projection = v02.project_public_after(duplicated.markdown)
        results = v02.check_boundaries_v0_2(projection.body, v02.public_safety(projection.body))
        self.assertEqual(results[0].status, "AMBIGUOUS")

    def test_21_witness_task_presence_and_meaning_fail_closed(self):
        values = _core()
        draft, projection, safety = values[2], values[3], values[4]
        with self.assertRaises(v02.CandidateV02Error):
            v02.bind_generated_witness_v0_2(
                _identity(draft), draft.markdown, projection, WITNESS.encode(), b"other", safety
            )
        short = _draft(PUBLIC_AFTER_TEXT.replace(WITNESS, "A3 Witness: abc"))
        projection = v02.project_public_after(short.markdown)
        with self.assertRaises(v02.CandidateV02Error):
            v02.bind_generated_witness_v0_2(
                _identity(short), short.markdown, projection, *_task_bytes(), v02.public_safety(projection.body)
            )

    def test_22_post_a1_gate_pass_and_persists_canonically(self):
        gate = _core()[-1]
        v02.require_post_a1_gate_for_a2(gate)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / v02.POST_A1_READBACK_FILENAME
            digest = v02.persist_post_a1_readback_v0_2(path, gate)
            self.assertEqual(v02.read_post_a1_readback_v0_2(path, digest), gate)

    def test_23_post_a1_gate_rejects_nonpass_receipts(self):
        values = _core()
        failed_isolation, failed_independence = v02.qualify_independence(
            _pass_evidence(git_access_count=1)
        )
        with self.assertRaises(v02.CandidateV02Error):
            v02.issue_post_a1_gate_v0_2(
                before=values[0], task_bytes=values[1], note_identity=_identity(values[2]),
                note_bytes=values[2].markdown, source_isolation=failed_isolation,
                independence=failed_independence, projection=values[3],
                compression=values[7], safety=values[4], boundaries=values[5],
                witness_binding=values[6],
            )

    def test_23a_shallow_or_tampered_post_a1_readback_cannot_open_a2(self):
        gate = _core()[-1]
        for forged in (
            replace(gate, projection={}),
            replace(gate, source_isolation={"result": "PASS", "receipt_sha256": "a" * 64}),
            replace(gate, boundaries=tuple({"status": "PRESENT"} for _ in range(10))),
        ):
            with self.subTest(fields=forged.as_dict().keys()), self.assertRaises(
                v02.CandidateV02Error
            ):
                v02.require_post_a1_gate_for_a2(forged)

    def test_23b_post_a1_persistence_does_not_create_parent_or_arbitrary_name(self):
        gate = _core()[-1]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(v02.CandidateV02Error):
                v02.persist_post_a1_readback_v0_2(root / "other.json", gate)
            with self.assertRaises(v02.CandidateV02Error):
                v02.persist_post_a1_readback_v0_2(
                    root / "missing" / v02.POST_A1_READBACK_FILENAME,
                    gate,
                )
            self.assertFalse((root / "missing").exists())

    def test_23c_private_proof_fields_fail_v02_public_safety(self):
        for marker in (
            b"journal_sha256",
            b"anchor_sha256",
            b"readback_sha256",
            b"journal SHA-256: " + b"a" * 64,
            b"anchor-sha256=" + b"b" * 64,
            b"typed readback SHA256: " + b"c" * 64,
        ):
            with self.subTest(marker=marker):
                receipt = v02.public_safety(b"public line " + marker + b"\n")
                self.assertEqual(receipt.result, "FAIL")

    def _audit(self, output: bytes, draft, binding, **changes):
        output_start = output.index(WITNESS.encode())
        values = dict(
            proof_attempt_id="proof_fixture_v02",
            run_id="run_fixture_v02_reuse",
            output_artifact_id="d" * 64,
            source_note_byte_count=len(draft.markdown),
            source_note_sha256=draft.sha256,
            output_byte_count=len(output),
            output_sha256=hashlib.sha256(output).hexdigest(),
            eligible_candidate_count=1,
            rejection_counts=FieldNoteCreatorLiveA3RejectionCounts(0, 0, 0, 0, 0),
            longest_candidate_byte_count=len(WITNESS.encode()),
            winning_candidate_count=1,
            selected_source_start_byte=binding.source_start_byte,
            selected_source_end_byte=binding.source_end_byte,
            selected_output_start_byte=output_start,
            selected_output_end_byte=output_start + len(WITNESS.encode()),
            terminal_a3_code=None,
        )
        values.update(changes)
        return FieldNoteCreatorLiveA3CompilerAudit.issue(**values)

    def test_24_exact_designated_witness_wins(self):
        values = _core()
        draft, binding = values[2], values[6]
        output = ("Result\n" + WITNESS + "\nDone\n").encode()
        result = v02.verify_a3_winner_witness_v0_2(
            self._audit(output, draft, binding), binding, draft.markdown, output
        )
        self.assertEqual(result.result, "PASS")

    def test_25_alternate_offset_multiple_winner_or_output_occurrence_rejected(self):
        values = _core()
        draft, binding = values[2], values[6]
        output = (WITNESS + "\n").encode()
        with self.assertRaises(v02.CandidateV02Error):
            v02.verify_a3_winner_witness_v0_2(
                self._audit(
                    output,
                    draft,
                    binding,
                    selected_source_start_byte=binding.source_start_byte - 1,
                    selected_source_end_byte=binding.source_end_byte - 1,
                ),
                binding, draft.markdown, output,
            )
        with self.assertRaises(v02.CandidateV02Error):
            v02.verify_a3_winner_witness_v0_2(
                self._audit(output, draft, binding, eligible_candidate_count=2),
                binding, draft.markdown, output,
            )
        with self.assertRaises(FieldNoteCreatorLiveValidationError):
            self._audit(
                output,
                draft,
                binding,
                eligible_candidate_count=2,
                winning_candidate_count=2,
            )
        repeated = (WITNESS + "\n" + WITNESS + "\n").encode()
        with self.assertRaises(v02.CandidateV02Error):
            v02.verify_a3_winner_witness_v0_2(
                self._audit(repeated, draft, binding), binding, draft.markdown, repeated
            )


class BehaviorComparisonMapAndBundleTests(unittest.TestCase):
    def test_26_behavior_suite_reused_and_artifact_not_run(self):
        harness, artifact = v02.qualify_behavior_harness(ROOT)
        self.assertEqual((harness.result, harness.passed), ("PASS", 10))
        self.assertEqual((artifact.result, artifact.passed), ("NOT_RUN", 0))
        self.assertEqual(harness.suite_sha256, v02.BEHAVIOR_SUITE_SHA256)

    def test_27_comparison_is_deterministic_and_matches_fixture(self):
        first = v02.build_common_before_comparison()
        second = v02.build_common_before_comparison()
        self.assertEqual(first, second)
        expected = (FIXTURES / "comparison_manifest_expected.json").read_text().strip()
        self.assertEqual(canonical_json(first), expected)
        self.assertEqual(first["comparison_result"], "NOT_ESTABLISHED")

    def test_28_comparison_keeps_lane_a_and_c_unknown_and_lane_b_exact(self):
        comparison = v02.build_common_before_comparison()
        lane_a, lane_b, lane_c = comparison["lanes"]
        self.assertEqual(lane_a["tool_identity"]["result"], "NOT_ESTABLISHED")
        self.assertEqual(lane_b["reduction"]["fraction"], "0.461628")
        self.assertEqual(lane_b["qualification"]["behavior"], "NOT_ESTABLISHED")
        self.assertEqual(lane_c["retry_replacement"], "NOT_AUTHORIZED")

    def test_29_comparison_has_no_raw_cross_lane_output(self):
        raw = canonical_json(v02.build_common_before_comparison())
        self.assertNotIn("--- before/AGENTS.md", raw)
        self.assertNotIn("+++ after/AGENTS.md", raw)
        self.assertNotIn((ROOT / "AGENTS.md").read_text(), raw)

    def test_29a_comparison_rejects_lane_c_or_cross_lane_mutation(self):
        value = v02.build_common_before_comparison()
        value["lanes"][2]["after_identity"] = {
            "result": "PASS",
            "raw_note": "/Users/private/Note.md",
        }
        with self.assertRaises(v02.CandidateV02Error):
            v02.validate_common_before_comparison(value)
        value = v02.build_common_before_comparison()
        value["cross_lane_isolation"]["run_1_input_lanes"] = ["LANE_B"]
        with self.assertRaises(v02.CandidateV02Error):
            v02.validate_common_before_comparison(value)

    def test_30_reduction_map_exact_and_deterministic(self):
        value = v02.build_reduction_boundary_map()
        expected = (FIXTURES / "reduction_boundary_map_expected.json").read_text().strip()
        self.assertEqual(canonical_json(value), expected)
        self.assertEqual(value["core_statement"], v02.REDUCTION_CORE_STATEMENT)
        self.assertEqual(len(value["entries"]), 5)

    def test_31_external_map_entries_require_later_verification(self):
        entries = v02.build_reduction_boundary_map()["entries"]
        self.assertTrue(
            all(value["verification_status"] == "LATER_WEB_VERIFICATION_REQUIRED" for value in entries[:4])
        )
        self.assertEqual(entries[4]["verification_status"], "INTERNAL_POSITIONING_STATEMENT")

    def test_32_reduction_map_rejects_superiority_and_performance(self):
        value = v02.build_reduction_boundary_map()
        value["rules"].append("RTK is superior to every system.")
        with self.assertRaises(v02.CandidateV02Error):
            v02.validate_reduction_boundary_map(value)

    def test_32a_reduction_map_rejects_extra_fields_and_entry_claims(self):
        value = v02.build_reduction_boundary_map()
        value["entries"][0]["raw_source"] = "private"
        with self.assertRaises(v02.CandidateV02Error):
            v02.validate_reduction_boundary_map(value)
        for claim in ("RTK is better than V13.", "Measured result is 99 percent."):
            value = v02.build_reduction_boundary_map()
            value["entries"][0]["combination_position"] = claim
            with self.subTest(claim=claim), self.assertRaises(v02.CandidateV02Error):
                v02.validate_reduction_boundary_map(value)
        value = v02.build_reduction_boundary_map()
        value["rules"].append("External result is 99%.")
        with self.assertRaises(v02.CandidateV02Error):
            v02.validate_reduction_boundary_map(value)

    def _bundle_arguments(self):
        values = _core()
        harness, artifact = v02.qualify_behavior_harness(ROOT)
        comparison = v02.build_common_before_comparison()
        reduction_map = v02.build_reduction_boundary_map()
        manifest = v02.build_public_manifest_v0_2(
            projection=values[3], compression=values[7], safety=values[4],
            boundaries=values[5], source_isolation=values[8], independence=values[9],
            harness_behavior=harness, artifact_behavior=artifact,
            comparison=comparison, reduction_map=reduction_map,
            receipt_hashes={"a1_capture_sha256": "a" * 64, "a2_reconnect_sha256": "b" * 64},
            output_artifact={"artifact_id": "c" * 64, "media_type": "text/plain; charset=utf-8", "byte_count": 120, "sha256": "d" * 64},
            a3={"compiler_version": v02.A3_COMPILER_VERSION, "compiler_branch": v02.A3_COMPILER_BRANCH, "audit_sha256": "e" * 64, "exact_reuse": "PASS"},
        )
        return dict(
            before=values[0], projection=values[3], compression=values[7], safety=values[4],
            boundaries=values[5], source_isolation=values[8], independence=values[9],
            harness_behavior=harness, artifact_behavior=artifact,
            comparison=comparison, reduction_map=reduction_map, public_manifest=manifest,
            witness=WITNESS.encode(), fixture_witness_publication_approved=True,
        )

    def test_33_bundle_exact_paths_determinism_and_privacy(self):
        arguments = self._bundle_arguments()
        first = v02.assemble_public_bundle_v0_2(**arguments)
        second = v02.assemble_public_bundle_v0_2(**arguments)
        self.assertEqual(first, second)
        self.assertEqual(tuple(first), v02.PUBLIC_BUNDLE_PATHS)
        public_control = b"".join(
            value
            for path, value in first.items()
            if path not in {"before/AGENTS.md", "diff.patch"}
        )
        for marker in (
            b"proof_attempt_id", b"run_id", b"field_note_id", b"task_body",
            b"journal_sha256", b"anchor_sha256", b"readback_sha256",
        ):
            self.assertNotIn(marker, public_control)

    def test_34_bundle_requires_fixture_witness_approval(self):
        arguments = self._bundle_arguments()
        arguments["fixture_witness_publication_approved"] = False
        with self.assertRaises(v02.CandidateV02Error):
            v02.assemble_public_bundle_v0_2(**arguments)

    def test_35_bundle_rejects_private_manifest_key(self):
        arguments = self._bundle_arguments()
        arguments["public_manifest"] = dict(arguments["public_manifest"])
        arguments["public_manifest"]["task_body"] = "private"
        with self.assertRaises(v02.CandidateV02Error):
            v02.assemble_public_bundle_v0_2(**arguments)

    def test_36_claim_and_nonclaim_boundaries_are_present(self):
        bundle = v02.assemble_public_bundle_v0_2(**self._bundle_arguments())
        readme = bundle["README.md"].decode()
        self.assertIn("textual and structural presence only", readme)
        self.assertIn("latent model memory", readme)
        self.assertIn("V13 is not only a compressor", readme)
        self.assertIn("requires separate user or human evidence", readme)

    def test_36a_public_receipt_files_are_allowlisted_projections(self):
        bundle = v02.assemble_public_bundle_v0_2(**self._bundle_arguments())
        source_projection = json.loads(bundle["source-isolation.json"])
        independence_projection = json.loads(bundle["independence-qualification.json"])
        self.assertEqual(
            source_projection["schema"],
            v02.SOURCE_ISOLATION_PUBLIC_PROJECTION_SCHEMA,
        )
        self.assertEqual(
            independence_projection["schema"],
            v02.INDEPENDENCE_PUBLIC_PROJECTION_SCHEMA,
        )
        public_receipts = (
            bundle["source-isolation.json"]
            + bundle["independence-qualification.json"]
        )
        for marker in (
            b"runtime_identity_sha256",
            b"contract_identity_sha256",
            b"event_log_sha256",
            b"developer_instructions_sha256",
        ):
            self.assertNotIn(marker, public_receipts)


class CompatibilitySchemaAndProtectedStateTests(unittest.TestCase):
    def test_37_all_new_schemas_parse_and_fix_ids(self):
        expected = {
            "creator_live_agents_source_isolation_v0_1.schema.json": v02.SOURCE_ISOLATION_SCHEMA,
            "creator_live_agents_independence_v0_1.schema.json": v02.INDEPENDENCE_SCHEMA,
            "creator_live_agents_post_a1_gate_v0_2.schema.json": v02.POST_A1_SCHEMA,
            "creator_live_agents_before_after_public_bundle_v0_2.schema.json": v02.PUBLIC_BUNDLE_SCHEMA,
            "creator_live_agents_common_before_comparison_v0_1.schema.json": v02.COMPARISON_SCHEMA,
            "creator_live_agents_reduction_boundary_map_v0_1.schema.json": v02.REDUCTION_MAP_SCHEMA,
        }
        for filename, schema_id in expected.items():
            with self.subTest(filename=filename):
                value = json.loads((ROOT / "schema" / filename).read_bytes())
                self.assertEqual(value["$id"], schema_id)

    def test_38_candidate_v01_fixed_identities_unchanged(self):
        self.assertEqual(V01_CANDIDATE_ID, "CREATOR_LIVE_AGENTS_BEFORE_AFTER_V0_1")
        self.assertEqual(verify_v01_before(ROOT).sha256, v02.MANUAL_AFTER_SHA256)
        first, second = verify_v01_tasks(ROOT)
        self.assertEqual((first.sha256, second.sha256), (V01_RUN_1_SHA256, V01_RUN_2_SHA256))

    def test_39_cycle_005_fixed_identity_guard(self):
        protected = os.environ.get("DECISION_OS_PROTECTED_REPOSITORY")
        if protected is None:
            self.skipTest("Protected repository was not supplied to this non-live fixture run.")
        root = Path(protected) / ".decision-os/field-notes/proofs/cycle-005"
        readback = FieldNoteCreatorLiveProofRuntime.load_attempt(root).read_back()
        self.assertEqual(readback.journal_sha256, "1de2e998804f5fb694707846b7deb0dc9d8b5f9cfc6027ad0210ddc270029322")
        self.assertEqual(readback.anchor_sha256, "e246757a7ba98849a6b4a694ababf473dc1a98baf1fc1ce0ea7daa3a6e7e8610")
        self.assertEqual(readback.readback_sha256, "481be90dc8751bda3d7b00714f5a0c650230dffa8974a1332881ce42c127710f")
        self.assertEqual((readback.state, readback.failure_boundary, readback.failure_reason), ("FAILED", "A3_REUSE", "A3_EXACT_STRUCTURE_MISSING"))

    def test_40_module_owns_no_live_launch_or_proof_root(self):
        source = (ROOT / "decision_os/companion/field_notes_creator_live_candidate_v0_2.py").read_text()
        self.assertNotIn("open_attempt(", source)
        self.assertNotIn("transport.start(", source)
        self.assertNotIn("cycle-006", source.casefold())


if __name__ == "__main__":
    unittest.main()
