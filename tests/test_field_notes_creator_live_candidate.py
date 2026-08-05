from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from decision_os.companion.field_notes_creator_live import (
    FieldNoteCreatorLiveA3CompilerAudit,
    FieldNoteCreatorLiveA3RejectionCounts,
    FieldNoteCreatorLiveRun2OutputIdentity,
)
from decision_os.companion.field_notes_creator_live_candidate import (
    A3_WITNESS_SCHEMA,
    BEFORE_BYTE_COUNT,
    BEFORE_SHA256,
    BEHAVIOR_RESULT_SCHEMA,
    BEHAVIOR_SUITE_SCHEMA,
    BOUNDARY_SCHEMA,
    BOUNDARY_SPECS,
    CANDIDATE_ID,
    CandidateFixationCoordinator,
    COMPRESSION_SCHEMA,
    CandidateFixationError,
    DIFF_SCHEMA,
    POST_A1_SCHEMA,
    PROJECTION_SCHEMA,
    PUBLIC_CLAIMS,
    PUBLIC_BUNDLE_ASSEMBLER,
    PUBLIC_BUNDLE_PATHS,
    PUBLIC_BUNDLE_SCHEMA,
    PUBLIC_NON_CLAIMS,
    PUBLIC_SCHEMA_IDENTITIES,
    RUN_1_PATH,
    RUN_1_SHA256,
    RUN_2_PATH,
    RUN_2_BYTE_COUNT,
    RUN_2_SHA256,
    SAFETY_SCHEMA,
    SOURCE_RECOVERY,
    WITNESS_LOCATOR,
    WITNESS_SCHEMA,
    artifact_behavior_not_run,
    assemble_public_bundle,
    bind_generated_witness,
    check_boundaries,
    compression_receipt,
    evaluate_behavior_fakes,
    issue_post_a1_gate,
    load_behavior_suite,
    persist_post_a1_readback,
    project_public_after,
    public_safety,
    read_post_a1_readback,
    require_candidate_gate_for_a2,
    require_witness_identity_for_a2,
    verify_a3_winner_witness,
    verify_fixed_before,
    verify_fixed_tasks,
)
from decision_os.companion import field_notes_creator_live_candidate as candidate_module
from decision_os.companion.field_notes_model import compile_draft
from decision_os.companion.field_notes_reuse import FieldNoteIdentity


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "validation/fixtures/creator_live_agents_before_after_v0_1/behavior"
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
    body = {
        "trigger": "Use for bounded agent operating instructions.",
        "reusable_structure": reusable,
        "scope": "Repository-local agent instructions only.",
        "do_not_apply_when": "Do not apply to unrelated policy documents.",
        "procedure": "Check the fixed source and preserve every boundary.",
        "acceptance": "All fixed gates pass with exact identities.",
        "evidence": "Use deterministic hashes and typed readback.",
        "remaining_unknowns": "Real behavior remains unqualified.",
    }
    return compile_draft(
        {
            "title": "Bounded Agent Operating Boundaries",
            "value_level": 2,
            "source_model_class": "stronger",
            "target_model_class": "lower-cost",
            "trigger_terms": ["agent instructions"],
            "scope": {
                "task_family": "agent governance",
                "path_prefixes": ["AGENTS.md"],
                "exclude_terms": ["live proof"],
            },
            "body": body,
        },
        source_run_id="run_fixture_origin",
        created_at="2026-08-05T16:29:00Z",
        field_note_id="fn_fixture_candidate",
    )


def _identity(draft=None):
    draft = draft or _draft()
    return FieldNoteIdentity(
        note_path=draft.relative_path,
        field_note_id=draft.field_note_id,
        note_sha256=draft.sha256,
        origin_run_id=draft.source_run_id,
    )


def _task_bytes():
    return (ROOT / RUN_1_PATH).read_bytes(), (ROOT / RUN_2_PATH).read_bytes()


def _core():
    before = (ROOT / "AGENTS.md").read_bytes()
    tasks = verify_fixed_tasks(ROOT)
    draft = _draft()
    projection = project_public_after(draft.markdown)
    safety = public_safety(projection.body)
    boundaries = check_boundaries(projection.body, safety)
    witness = bind_generated_witness(
        _identity(draft),
        draft.markdown,
        projection,
        (ROOT / RUN_1_PATH).read_bytes(),
        (ROOT / RUN_2_PATH).read_bytes(),
        safety,
    )
    compression = compression_receipt(before, projection.body)
    source = verify_fixed_before(ROOT)
    gate = issue_post_a1_gate(
        source,
        before,
        tasks,
        _task_bytes(),
        _identity(draft),
        draft.markdown,
        projection,
        compression,
        safety,
        boundaries,
        witness,
    )
    return before, draft, projection, safety, boundaries, witness, compression, gate


def _behaviors():
    _, scenarios, _ = load_behavior_suite(SUITE)
    observations = {
        scenario["scenario_id"]: scenario["required_tags"]
        for scenario in scenarios
    }
    return evaluate_behavior_fakes(SUITE, observations), artifact_behavior_not_run(SUITE)


def _manifest(projection, compression, safety, boundaries, harness, artifact):
    return {
        "schema": PUBLIC_BUNDLE_SCHEMA,
        "assembler": PUBLIC_BUNDLE_ASSEMBLER,
        "candidate_id": CANDIDATE_ID,
        "before": {
            "path": "AGENTS.md",
            "source_revision": "a80a06c067f7d558cfe16aa08566106aa4017a3d",
            "git_blob": "2deb6f610f8e3a4e67808a0182cb2439a7abc447",
            "utf8_byte_count": BEFORE_BYTE_COUNT,
            "line_count": 359,
            "sha256": BEFORE_SHA256,
        },
        "after": projection.identity_dict(),
        "compression": compression.as_dict(),
        "safety": safety.as_dict(),
        "behavior": {
            "suite_schema": BEHAVIOR_SUITE_SCHEMA,
            "suite_sha256": artifact.suite_sha256,
            "pass_threshold": "10/10",
            "harness_qualification": harness.result,
            "artifact_behavior_qualification": artifact.result,
            "real_qualification_receipt_sha256": None,
        },
        "boundary_ids": [item.boundary_id for item in boundaries],
        "receipt_hashes": {"a1_capture_sha256": "a" * 64, "a2_reconnect_sha256": "b" * 64},
        "output_artifact": {"artifact_id": "c" * 64, "media_type": "text/plain; charset=utf-8", "sha256": "e" * 64, "byte_count": 120},
        "a3": {
            "compiler_version": "decision-os.creator-live-a3-exact-output-artifact-compiler.v0.1",
            "compiler_branch": "EXACT_UTF8_NON_WHOLE_UNIQUE_SOURCE_UNIQUE_OUTPUT",
            "audit_sha256": "d" * 64,
            "exact_reuse": "PASS",
        },
        "schemas": list(PUBLIC_SCHEMA_IDENTITIES),
        "claims": list(PUBLIC_CLAIMS),
        "non_claims": list(PUBLIC_NON_CLAIMS),
        "source_recovery": SOURCE_RECOVERY,
        "files": list(PUBLIC_BUNDLE_PATHS),
    }


def _bundle_arguments():
    before, _, projection, safety, boundaries, _, compression, _ = _core()
    harness, artifact = _behaviors()
    return {
        "before": before,
        "projection": projection,
        "compression": compression,
        "safety": safety,
        "boundaries": boundaries,
        "harness_behavior": harness,
        "artifact_behavior": artifact,
        "public_manifest": _manifest(
            projection, compression, safety, boundaries, harness, artifact
        ),
        "witness": WITNESS.encode(),
        "witness_publication_approved": True,
    }


class FixedIdentityTests(unittest.TestCase):
    def test_01_before_exact_identity(self):
        identity = verify_fixed_before(ROOT)
        self.assertEqual(identity.sha256, BEFORE_SHA256)
        self.assertEqual(identity.byte_count, BEFORE_BYTE_COUNT)

    def test_02_before_line_count(self):
        self.assertEqual(verify_fixed_before(ROOT).line_count, 359)

    def test_03_tasks_exact_identities(self):
        first, second = verify_fixed_tasks(ROOT)
        self.assertEqual((first.sha256, second.sha256), (RUN_1_SHA256, RUN_2_SHA256))

    def test_04_tasks_final_lf(self):
        self.assertTrue((ROOT / RUN_1_PATH).read_bytes().endswith(b"\n"))
        self.assertTrue((ROOT / RUN_2_PATH).read_bytes().endswith(b"\n"))

    def test_05_tasks_do_not_contain_fixture_witness(self):
        witness = WITNESS.encode()
        self.assertNotIn(witness, (ROOT / RUN_1_PATH).read_bytes())
        self.assertNotIn(witness, (ROOT / RUN_2_PATH).read_bytes())

    def test_05a_source_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AGENTS.md"
            path.write_bytes(b"drift\n")
            with self.assertRaises(CandidateFixationError):
                candidate_module._fixed_file(Path(directory), "AGENTS.md", BEFORE_BYTE_COUNT, BEFORE_SHA256)

    def test_05b_run_1_forbids_historical_after(self):
        task = (ROOT / RUN_1_PATH).read_text(encoding="utf-8")
        self.assertIn("Do not consult, reconstruct, or imitate", task)
        self.assertIn("historical 20,705-byte AGENTS.md", task)


class ProjectionTests(unittest.TestCase):
    def test_06_projection_exact_bytes(self):
        projection = project_public_after(_draft().markdown)
        self.assertEqual(projection.body, (PUBLIC_AFTER_TEXT + "\n").encode())

    def test_07_projection_identity(self):
        projection = project_public_after(_draft().markdown)
        self.assertEqual(projection.schema, PROJECTION_SCHEMA)
        self.assertEqual(projection.sha256, hashlib.sha256(projection.body).hexdigest())

    def test_08_projection_final_lf(self):
        self.assertTrue(project_public_after(_draft().markdown).body.endswith(b"\n"))

    def test_09_projection_rejects_non_bytes(self):
        with self.assertRaises(CandidateFixationError):
            project_public_after("not bytes")  # type: ignore[arg-type]

    def test_10_projection_rejects_nul(self):
        broken = _draft().markdown.replace(b"human Decision", b"human\x00Decision", 1)
        with self.assertRaises(CandidateFixationError):
            project_public_after(broken)

    def test_11_projection_rejects_cr(self):
        broken = _draft().markdown.replace(b"human Decision", b"human\rDecision", 1)
        with self.assertRaises(CandidateFixationError):
            project_public_after(broken)

    def test_12_projection_rejects_duplicate_marker(self):
        broken = _draft().markdown.replace(b"## Scope\n", b"## Reusable Structure\nextra\n\n## Scope\n")
        with self.assertRaises(CandidateFixationError):
            project_public_after(broken)

    def test_12a_projection_is_repeatable(self):
        first = project_public_after(_draft().markdown)
        second = project_public_after(_draft().markdown)
        self.assertEqual((first.body, first.sha256), (second.body, second.sha256))

    def test_12b_projection_rejects_non_lf_line_separators(self):
        for separator in ("\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
            broken = _draft().markdown.replace(
                b"human Decision",
                ("human" + separator + "Decision").encode("utf-8"),
                1,
            )
            with self.subTest(separator=repr(separator)):
                with self.assertRaises(CandidateFixationError):
                    project_public_after(broken)


class CompressionTests(unittest.TestCase):
    def test_13_compression_passes(self):
        before, _, projection, _, _, _, receipt, _ = _core()
        self.assertLess(len(projection.body), len(before))
        self.assertEqual(receipt.result, "PASS")

    def test_14_compression_schema(self):
        receipt = _core()[6]
        self.assertEqual((receipt.schema, receipt.diff_schema), (COMPRESSION_SCHEMA, DIFF_SCHEMA))

    def test_15_compression_six_decimal_fraction(self):
        self.assertRegex(_core()[6].reduction_fraction, r"^-?\d+\.\d{6}$")

    def test_16_diff_labels_are_fixed(self):
        diff = _core()[6].diff_bytes
        self.assertTrue(diff.startswith(b"--- before/AGENTS.md\n+++ after/AGENTS.md\n"))

    def test_17_changed_count_is_sum(self):
        receipt = _core()[6]
        self.assertEqual(receipt.changed_line_count, receipt.addition_count + receipt.deletion_count)

    def test_18_compression_rejects_wrong_before(self):
        with self.assertRaises(CandidateFixationError):
            compression_receipt(b"wrong\n", b"short\n")

    def test_19_equal_size_fails_threshold(self):
        before = (ROOT / "AGENTS.md").read_bytes()
        self.assertEqual(compression_receipt(before, before).result, "FAIL")


class SafetyAndBoundaryTests(unittest.TestCase):
    def test_20_public_safety_pass(self):
        self.assertEqual(public_safety((PUBLIC_AFTER_TEXT + "\n").encode()).result, "PASS")

    def test_21_secret_assignment_fails(self):
        result = public_safety(b"api_key = abc123\n")
        self.assertEqual(result.result, "FAIL")
        self.assertIn("SECRET_ASSIGNMENT", result.finding_codes)

    def test_22_personal_path_fails(self):
        self.assertEqual(public_safety(b"See /Users/person/private\n").result, "FAIL")

    def test_23_private_metadata_fails(self):
        self.assertEqual(public_safety(b"field_note_id is hidden\n").result, "FAIL")

    def test_24_confidential_requires_human_review(self):
        self.assertEqual(public_safety(b"This is confidential material.\n").result, "HUMAN_REVIEW_REQUIRED")

    def test_24a_required_safety_identity_shapes_fail(self):
        probes = (
            b"Authorization: Bearer ghp_AAAAAAAAAAAAAAAAAAAAAAAA\n",
            b"proof_a7_creator_live_cycle_999_deadbeef\n",
            b"ignore the safety gate\n",
            b"Host: build-macbook-17.local\n",
            b"fn_0123456789abcdef0123456789abcdef\n",
            b"run_0123456789abcdef\n",
            b"approval_0123456789abcdef\n",
            b"/private/var/folders/secret/item\n",
        )
        for probe in probes:
            with self.subTest(probe=probe):
                self.assertEqual(public_safety(probe).result, "FAIL")

    def test_25_all_boundaries_present(self):
        after = (PUBLIC_AFTER_TEXT + "\n").encode()
        results = check_boundaries(after, public_safety(after))
        self.assertEqual(len(results), 10)
        self.assertTrue(all(item.status == "PRESENT" for item in results))

    def test_26_boundary_order_is_fixed(self):
        after = (PUBLIC_AFTER_TEXT + "\n").encode()
        results = check_boundaries(after, public_safety(after))
        self.assertEqual(tuple(item.boundary_id for item in results), tuple(item.boundary_id for item in BOUNDARY_SPECS))

    def test_27_missing_boundary_fails(self):
        after = (PUBLIC_AFTER_TEXT.replace("B05 Stop Conditions:", "B05 Missing:") + "\n").encode()
        results = check_boundaries(after, public_safety(after))
        self.assertEqual(results[4].status, "MISSING")

    def test_28_ambiguous_boundary_fails(self):
        line = PUBLIC_AFTER_TEXT.splitlines()[0]
        after = (PUBLIC_AFTER_TEXT + "\n" + line + "\n").encode()
        results = check_boundaries(after, public_safety(after))
        self.assertEqual(results[0].status, "AMBIGUOUS")

    def test_29_locator_must_start_at_byte_zero(self):
        after = (PUBLIC_AFTER_TEXT.replace("B03 Guard", " B03 Guard") + "\n").encode()
        results = check_boundaries(after, public_safety(after))
        self.assertEqual(results[2].status, "MISSING")

    def test_30_failed_regex_group_is_missing(self):
        after = (PUBLIC_AFTER_TEXT.replace("protected artifacts", "ordinary material", 1) + "\n").encode()
        results = check_boundaries(after, public_safety(after))
        self.assertEqual(results[2].status, "MISSING")

    def test_31_spans_exposed_only_after_safety_pass(self):
        after = (PUBLIC_AFTER_TEXT + "\n").encode()
        good = check_boundaries(after, public_safety(after))
        bad = check_boundaries(after, public_safety(b"api_key=x\n"))
        self.assertIsNotNone(good[0].start_byte)
        self.assertIsNone(bad[0].start_byte)


class WitnessAndGateTests(unittest.TestCase):
    def test_32_witness_binding_pass(self):
        binding = _core()[5]
        self.assertEqual((binding.schema, binding.policy_result), (WITNESS_SCHEMA, "PASS"))

    def test_33_witness_binding_has_no_raw_identity(self):
        binding = _core()[5].as_dict()
        self.assertFalse({"note_path", "field_note_id", "origin_run_id"}.intersection(binding))

    def test_34_witness_binding_has_no_text(self):
        self.assertNotIn(WITNESS, json.dumps(_core()[5].as_dict()))

    def test_35_witness_identity_digest_changes_with_identity(self):
        _, draft, projection, safety, _, binding, _, _ = _core()
        changed = FieldNoteIdentity(draft.relative_path, "fn_other", draft.sha256, draft.source_run_id)
        other = bind_generated_witness(changed, draft.markdown, projection, (ROOT / RUN_1_PATH).read_bytes(), (ROOT / RUN_2_PATH).read_bytes(), safety)
        self.assertNotEqual(binding.note_identity_sha256, other.note_identity_sha256)

    def test_36_witness_rejects_task_prepopulation(self):
        _, draft, projection, safety, _, _, _, _ = _core()
        with self.assertRaises(CandidateFixationError):
            bind_generated_witness(_identity(draft), draft.markdown, projection, WITNESS.encode(), b"other", safety)

    def test_37_witness_rejects_short_meaningless_value(self):
        draft = _draft("A3 Witness: abc123")
        projection = project_public_after(draft.markdown)
        with self.assertRaises(CandidateFixationError):
            bind_generated_witness(_identity(draft), draft.markdown, projection, b"one", b"two", public_safety(projection.body))

    def test_37a_witness_rejects_long_nonce_only_value(self):
        draft = _draft("A3 Witness: " + "a1b2c3d4" * 8)
        projection = project_public_after(draft.markdown)
        with self.assertRaises(CandidateFixationError):
            bind_generated_witness(_identity(draft), draft.markdown, projection, b"one", b"two", public_safety(projection.body))

    def test_37b_witness_occurrence_counts_are_exact(self):
        binding = _core()[5]
        self.assertEqual((binding.source_occurrence_count, binding.projection_occurrence_count), (1, 1))

    def test_37c_witness_rejects_keyword_salad(self):
        for text in (
            "A3 Witness: Authority banana banana banana banana banana banana.",
            "A3 Witness: Authority and safety must banana banana orange purple.",
        ):
            draft = _draft(text)
            projection = project_public_after(draft.markdown)
            with self.subTest(text=text):
                with self.assertRaises(CandidateFixationError):
                    bind_generated_witness(
                        _identity(draft),
                        draft.markdown,
                        projection,
                        b"one",
                        b"two",
                        public_safety(projection.body),
                    )

    def test_38_post_a1_gate_pass(self):
        gate = _core()[7]
        self.assertEqual((gate.schema, gate.result), (POST_A1_SCHEMA, "PASS"))

    def test_39_post_a1_gate_rejects_boundary_reorder(self):
        before, draft, projection, safety, boundaries, witness, compression, _ = _core()
        gate = issue_post_a1_gate(
            verify_fixed_before(ROOT), before, verify_fixed_tasks(ROOT),
            _task_bytes(), _identity(draft), draft.markdown, projection,
            compression, safety, tuple(reversed(boundaries)), witness,
        )
        self.assertEqual(gate.result, "FAIL")

    def test_39a_post_a1_rejects_mixed_projection_receipts(self):
        before, _, projection, safety, boundaries, witness, compression, _ = _core()
        changed_draft = _draft(PUBLIC_AFTER_TEXT.replace("governs risk", "governs current risk"))
        changed_projection = project_public_after(changed_draft.markdown)
        changed_safety = public_safety(changed_projection.body)
        changed_boundaries = check_boundaries(changed_projection.body, changed_safety)
        changed_witness = bind_generated_witness(
            _identity(changed_draft),
            changed_draft.markdown,
            changed_projection,
            (ROOT / RUN_1_PATH).read_bytes(),
            (ROOT / RUN_2_PATH).read_bytes(),
            changed_safety,
        )
        gate = issue_post_a1_gate(
            verify_fixed_before(ROOT),
            before,
            verify_fixed_tasks(ROOT),
            _task_bytes(),
            _identity(changed_draft),
            changed_draft.markdown,
            changed_projection,
            compression,
            safety,
            boundaries,
            changed_witness,
        )
        self.assertEqual(gate.result, "FAIL")

    def test_39b_post_a1_rejects_forged_projection_identity(self):
        before, _, projection, safety, boundaries, witness, compression, _ = _core()
        forged = replace(projection, sha256="f" * 64)
        forged_witness = replace(witness, projection_sha256="f" * 64)
        gate = issue_post_a1_gate(
            verify_fixed_before(ROOT), before, verify_fixed_tasks(ROOT),
            _task_bytes(), _identity(), _draft().markdown, forged,
            compression, safety, boundaries, forged_witness,
        )
        self.assertEqual(gate.result, "FAIL")

    def test_39c_post_a1_rejects_source_path_drift(self):
        before, _, projection, safety, boundaries, witness, compression, _ = _core()
        source = replace(verify_fixed_before(ROOT), path="OTHER.md")
        gate = issue_post_a1_gate(
            source, before, verify_fixed_tasks(ROOT), _task_bytes(),
            _identity(), _draft().markdown, projection,
            compression, safety, boundaries, witness,
        )
        self.assertEqual(gate.result, "FAIL")

    def test_39d_post_a1_rejects_forged_witness_source_receipt(self):
        before, draft, projection, safety, boundaries, witness, compression, _ = _core()
        forged = replace(witness, source_occurrence_count=2)
        gate = issue_post_a1_gate(
            verify_fixed_before(ROOT), before, verify_fixed_tasks(ROOT),
            _task_bytes(), _identity(draft), draft.markdown, projection,
            compression, safety, boundaries, forged,
        )
        self.assertEqual(gate.result, "FAIL")

    def test_40_a2_requires_pass(self):
        require_candidate_gate_for_a2(_core()[7])

    def test_41_a2_rejects_fail(self):
        gate = replace(_core()[7], result="FAIL")
        with self.assertRaises(CandidateFixationError):
            require_candidate_gate_for_a2(gate)

    def test_41a_a2_requires_exact_note_identity(self):
        _, draft, _, _, _, binding, _, _ = _core()
        require_witness_identity_for_a2(binding, _identity(draft))

    def test_41b_a2_rejects_content_identical_different_identity(self):
        _, draft, _, _, _, binding, _, _ = _core()
        changed = FieldNoteIdentity(draft.relative_path, "fn_changed", draft.sha256, draft.source_run_id)
        with self.assertRaises(CandidateFixationError):
            require_witness_identity_for_a2(binding, changed)

    def test_42_readback_write_once_and_exact(self):
        gate = _core()[7]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gate.json"
            digest = persist_post_a1_readback(path, gate)
            self.assertEqual(read_post_a1_readback(path, digest), gate)
            with self.assertRaises(CandidateFixationError):
                persist_post_a1_readback(path, gate)

    def test_43_readback_tamper_fails(self):
        gate = _core()[7]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gate.json"
            digest = persist_post_a1_readback(path, gate)
            path.write_bytes(path.read_bytes().replace(b'"PASS"', b'"FAIL"', 1))
            with self.assertRaises(CandidateFixationError):
                read_post_a1_readback(path, digest)


class A3WitnessTests(unittest.TestCase):
    def _audit(
        self,
        output: bytes,
        draft,
        binding,
        *,
        source_start=None,
        output_artifact_id="e" * 64,
        proof_attempt_id="proof_fixture",
        run_id="run_fixture_reuse",
    ):
        output_start = output.index(WITNESS.encode())
        source_start = binding.source_start_byte if source_start is None else source_start
        return FieldNoteCreatorLiveA3CompilerAudit.issue(
            proof_attempt_id=proof_attempt_id,
            run_id=run_id,
            output_artifact_id=output_artifact_id,
            source_note_byte_count=len(draft.markdown),
            source_note_sha256=draft.sha256,
            output_byte_count=len(output),
            output_sha256=hashlib.sha256(output).hexdigest(),
            eligible_candidate_count=1,
            rejection_counts=FieldNoteCreatorLiveA3RejectionCounts(0, 0, 0, 0, 0),
            longest_candidate_byte_count=len(WITNESS.encode()),
            winning_candidate_count=1,
            selected_source_start_byte=source_start,
            selected_source_end_byte=source_start + len(WITNESS.encode()),
            selected_output_start_byte=output_start,
            selected_output_end_byte=output_start + len(WITNESS.encode()),
            terminal_a3_code=None,
        )

    def test_44_exact_a3_witness_pass(self):
        _, draft, _, _, _, binding, _, _ = _core()
        output = ("Result\n" + WITNESS + "\nDone\n").encode()
        result = verify_a3_winner_witness(self._audit(output, draft, binding), binding, draft.markdown, output)
        self.assertEqual((result.schema, result.result), (A3_WITNESS_SCHEMA, "PASS"))

    def test_45_a3_wrong_source_offsets_fail(self):
        _, draft, _, _, _, binding, _, _ = _core()
        output = (WITNESS + "\n").encode()
        with self.assertRaises(CandidateFixationError):
            verify_a3_winner_witness(self._audit(output, draft, binding, source_start=binding.source_start_byte + 1), binding, draft.markdown, output)

    def test_46_a3_wrong_output_bytes_fail(self):
        _, draft, _, _, _, binding, _, _ = _core()
        output = (WITNESS + "\n").encode()
        audit = self._audit(output, draft, binding)
        with self.assertRaises(CandidateFixationError):
            verify_a3_winner_witness(audit, binding, draft.markdown, output.replace(b"bounded", b"changed"))

    def test_46a_a3_eligible_count_must_equal_one(self):
        _, draft, _, _, _, binding, _, _ = _core()
        output = (WITNESS + "\n").encode()
        audit = self._audit(output, draft, binding)
        widened = FieldNoteCreatorLiveA3CompilerAudit.issue(
            proof_attempt_id=audit.proof_attempt_id,
            run_id=audit.run_id,
            output_artifact_id=audit.output_artifact_id,
            source_note_byte_count=audit.source_note_byte_count,
            source_note_sha256=audit.source_note_sha256,
            output_byte_count=audit.output_byte_count,
            output_sha256=audit.output_sha256,
            eligible_candidate_count=2,
            rejection_counts=audit.rejection_counts,
            longest_candidate_byte_count=audit.longest_candidate_byte_count,
            winning_candidate_count=1,
            selected_source_start_byte=audit.selected_source_start_byte,
            selected_source_end_byte=audit.selected_source_end_byte,
            selected_output_start_byte=audit.selected_output_start_byte,
            selected_output_end_byte=audit.selected_output_end_byte,
            terminal_a3_code=None,
        )
        with self.assertRaises(CandidateFixationError):
            verify_a3_winner_witness(widened, binding, draft.markdown, output)

    def _coordinator_fixture(self, directory: str):
        _, draft, _, _, _, binding, _, gate = _core()
        path = Path(directory) / "gate.json"
        digest = persist_post_a1_readback(path, gate)
        coordinator = CandidateFixationCoordinator(
            readback_path=path,
            readback_sha256=digest,
            witness_binding=binding,
        )
        output = ("Result\n" + WITNESS + "\nDone\n").encode()
        run_2 = FieldNoteCreatorLiveRun2OutputIdentity.create(
            proof_attempt_id="proof_fixture",
            run_id="run_fixture_reuse",
            task_byte_count=RUN_2_BYTE_COUNT,
            task_sha256=RUN_2_SHA256,
            final_output_byte_count=len(output),
            final_output_sha256=hashlib.sha256(output).hexdigest(),
        )
        audit = self._audit(
            output,
            draft,
            binding,
            output_artifact_id=run_2.output_artifact.artifact_id,
        )
        return coordinator, draft, binding, output, run_2, audit

    def test_46b_coordinator_orders_durable_a2_and_candidate_a3(self):
        with tempfile.TemporaryDirectory() as directory:
            coordinator, draft, _, output, run_2, audit = self._coordinator_fixture(directory)
            self.assertIs(coordinator.transport_a2(a2_note_identity=_identity(draft), transport=lambda: run_2), run_2)
            verification = coordinator.checkpoint_a3(
                audit=audit,
                source_note_bytes=draft.markdown,
                output_bytes=output,
                checkpoint=lambda value: value,
            )
            self.assertEqual(verification.result, "PASS")

    def test_46c_coordinator_blocks_a3_reentry_during_a2(self):
        with tempfile.TemporaryDirectory() as directory:
            coordinator, draft, _, output, run_2, audit = self._coordinator_fixture(directory)
            observed = []

            def transport():
                with self.assertRaises(CandidateFixationError):
                    coordinator.checkpoint_a3(
                        audit=audit,
                        source_note_bytes=draft.markdown,
                        output_bytes=output,
                        checkpoint=lambda value: value,
                    )
                observed.append("blocked")
                return run_2

            coordinator.transport_a2(a2_note_identity=_identity(draft), transport=transport)
            self.assertEqual(observed, ["blocked"])

    def test_46d_failed_a2_transport_never_admits_a3(self):
        with tempfile.TemporaryDirectory() as directory:
            coordinator, draft, _, output, _, audit = self._coordinator_fixture(directory)

            def fail_transport():
                raise RuntimeError("fixture transport failed")

            with self.assertRaises(RuntimeError):
                coordinator.transport_a2(a2_note_identity=_identity(draft), transport=fail_transport)
            with self.assertRaises(CandidateFixationError):
                coordinator.checkpoint_a3(
                    audit=audit,
                    source_note_bytes=draft.markdown,
                    output_bytes=output,
                    checkpoint=lambda value: value,
                )


class BehaviorAndBundleTests(unittest.TestCase):
    def test_47_behavior_suite_exact_coverage(self):
        _, scenarios, digest = load_behavior_suite(SUITE)
        self.assertEqual(len(scenarios), 10)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_48_artifact_behavior_is_not_run(self):
        result = artifact_behavior_not_run(SUITE)
        self.assertEqual((result.schema, result.suite_schema, result.result), (BEHAVIOR_RESULT_SCHEMA, BEHAVIOR_SUITE_SCHEMA, "NOT_RUN"))

    def test_49_fake_behavior_pass(self):
        _, scenarios, _ = load_behavior_suite(SUITE)
        observations = {scenario["scenario_id"]: scenario["required_tags"] for scenario in scenarios}
        result = evaluate_behavior_fakes(SUITE, observations)
        self.assertEqual((result.result, result.passed), ("PASS", 10))

    def test_50_fake_behavior_failure(self):
        _, scenarios, _ = load_behavior_suite(SUITE)
        observations = {scenario["scenario_id"]: scenario["required_tags"] for scenario in scenarios}
        observations[scenarios[0]["scenario_id"]] = scenarios[0]["forbidden_tags"]
        self.assertEqual(evaluate_behavior_fakes(SUITE, observations).result, "FAIL")

    def test_51_fake_behavior_incomplete_is_invalid(self):
        self.assertEqual(evaluate_behavior_fakes(SUITE, {}).result, "INVALID")

    def test_51a_forged_harness_result_is_rejected(self):
        with self.assertRaises(CandidateFixationError):
            candidate_module.BehaviorResult(
                BEHAVIOR_RESULT_SCHEMA,
                "evil-suite",
                "PASS",
                10,
                10,
                (),
                "f" * 64,
            )

    def test_51b_fail_result_cannot_hide_not_run_scenario(self):
        states = tuple(
            (scenario_id, "FAIL" if index == 0 else "NOT_RUN")
            for index, scenario_id in enumerate(candidate_module.BEHAVIOR_SCENARIO_IDS)
        )
        with self.assertRaises(CandidateFixationError):
            candidate_module.BehaviorResult(
                BEHAVIOR_RESULT_SCHEMA,
                BEHAVIOR_SUITE_SCHEMA,
                "FAIL",
                0,
                10,
                states,
                candidate_module.BEHAVIOR_SUITE_SHA256,
            )

    def test_52_bundle_exact_paths(self):
        bundle = assemble_public_bundle(**_bundle_arguments())
        self.assertEqual(tuple(bundle), PUBLIC_BUNDLE_PATHS)

    def test_53_bundle_requires_manifest_allowlist(self):
        arguments = _bundle_arguments()
        arguments["public_manifest"]["extra"] = "forbidden"
        with self.assertRaises(CandidateFixationError):
            assemble_public_bundle(**arguments)

    def test_54_bundle_rejects_private_identity(self):
        arguments = _bundle_arguments()
        arguments["public_manifest"]["output_artifact"]["run_id"] = "private"
        with self.assertRaises(CandidateFixationError):
            assemble_public_bundle(**arguments)

    def test_55_bundle_rejects_unapproved_witness(self):
        arguments = _bundle_arguments()
        arguments["witness_publication_approved"] = False
        with self.assertRaises(CandidateFixationError):
            assemble_public_bundle(**arguments)

    def test_56_bundle_claim_boundary_present(self):
        bundle = assemble_public_bundle(**_bundle_arguments())
        self.assertIn(b"No claim of general usefulness", bundle["README.md"])

    def test_56a_bundle_rejects_mixed_boundary_receipt(self):
        arguments = _bundle_arguments()
        arguments["boundaries"] = tuple(reversed(arguments["boundaries"]))
        arguments["public_manifest"]["boundary_ids"] = [
            item.boundary_id for item in arguments["boundaries"]
        ]
        with self.assertRaises(CandidateFixationError):
            assemble_public_bundle(**arguments)

    def test_56b_fake_harness_pass_cannot_be_artifact_pass(self):
        arguments = _bundle_arguments()
        harness = arguments["harness_behavior"]
        arguments["artifact_behavior"] = harness
        arguments["public_manifest"]["behavior"][
            "artifact_behavior_qualification"
        ] = "PASS"
        with self.assertRaises(CandidateFixationError):
            assemble_public_bundle(**arguments)

    def test_56c_proof_summary_contains_allowlisted_identities(self):
        bundle = assemble_public_bundle(**_bundle_arguments())
        summary = json.loads(bundle["proof-summary.json"])
        self.assertEqual(
            set(summary)
            & {"receipt_hashes", "output_artifact", "a3", "behavior"},
            {"receipt_hashes", "output_artifact", "a3", "behavior"},
        )

    def test_56d_bundle_rejects_self_consistent_oversized_projection(self):
        before = (ROOT / "AGENTS.md").read_bytes()
        draft = _draft(PUBLIC_AFTER_TEXT + "\n" + ("ordinary filler text " * 700))
        projection = project_public_after(draft.markdown)
        safety = public_safety(projection.body)
        boundaries = check_boundaries(projection.body, safety)
        compression = compression_receipt(before, projection.body)
        self.assertEqual(compression.result, "FAIL")
        harness, artifact = _behaviors()
        with self.assertRaises(CandidateFixationError):
            assemble_public_bundle(
                before=before,
                projection=projection,
                compression=compression,
                safety=safety,
                boundaries=boundaries,
                harness_behavior=harness,
                artifact_behavior=artifact,
                public_manifest=_manifest(
                    projection, compression, safety, boundaries, harness, artifact
                ),
                witness=WITNESS.encode(),
                witness_publication_approved=True,
            )

    def test_57_bundle_is_deterministic(self):
        arguments = _bundle_arguments()
        self.assertEqual(assemble_public_bundle(**arguments), assemble_public_bundle(**arguments))

    def test_58_no_cycle_or_proof_root_created(self):
        self.assertFalse((ROOT / ".decision-os").exists())
        self.assertNotIn("cycle-", (ROOT / "decision_os/companion/field_notes_creator_live_candidate.py").read_text(encoding="utf-8").casefold())


if __name__ == "__main__":
    unittest.main()
