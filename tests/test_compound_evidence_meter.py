from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from decision_os.checks import EXIT_OK, inspect_repository
from decision_os.compound_evidence_meter import (
    EVENT_TYPES,
    MeterValidationError,
    aggregate_records,
    load_ledger,
    render_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO_ROOT / "evidence" / "compound_evidence_meter_v0_1.jsonl"
SPEC_PATH = REPO_ROOT / "docs" / "compound_evidence_meter_v0_1.md"


def raw_records() -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    ]


def write_records(parent: Path, records: list[dict[str, object]]) -> Path:
    path = parent / "meter.jsonl"
    path.write_text(
        "\n".join(
            json.dumps(
                record,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            for record in records
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def loaded():
    return load_ledger(LEDGER_PATH, REPO_ROOT)


class CompoundEvidenceMeterBaselineTests(unittest.TestCase):
    def test_current_baseline_counts_are_derived_from_exact_sources(self) -> None:
        baseline, events = loaded()
        snapshot = aggregate_records(baseline, events)
        expected = {
            "BOUNDED_GOAL": 3,
            "WORKER_RUN": 8,
            "CAUSAL_CONTINUATION": 5,
            "STRUCTURE_EXTRACTED": 1,
            "VERIFIED_REUSE": 1,
            "CANON_PROMOTION": 1,
            "HUMAN_SEAT_RETURN": 0,
            "EFFICIENCY_COMPARISON": 0,
        }
        for event_type, count in expected.items():
            with self.subTest(event_type=event_type):
                self.assertEqual("BACKFILLED", snapshot["counters"][event_type]["baseline"])
                self.assertEqual(count, snapshot["counters"][event_type]["count"])

        self.assertEqual(
            {
                "validation/stage_b_one_automatic_continuation_001.md",
                "validation/stage_c_small_compound_loop_001.md",
                "validation/stage_d_leave_the_desk_dogfood_001.md",
                "field_notes/129_mutable_path_is_not_artifact_identity.md",
                "field_notes/125_execution_context_proof_selection.md",
                "field_notes/105_compound_loop_speed_as_os_evidence.md",
                "field_notes/132_autonomy_cost_and_intervention_ev.md",
            },
            {source["path"] for source in baseline["source_artifacts"]},
        )
        self.assertEqual(
            "084a1779792abd959c48a86f0ad183231c03526f",
            snapshot["canonical_commit"],
        )

    def test_aggregation_and_rendering_are_deterministic(self) -> None:
        baseline, events = loaded()
        first = aggregate_records(baseline, events)
        second = aggregate_records(deepcopy(baseline), deepcopy(events))
        self.assertEqual(first, second)
        self.assertEqual(render_snapshot(first), render_snapshot(second))

    def test_unknown_and_not_backfilled_never_become_zero(self) -> None:
        baseline, events = loaded()
        snapshot = aggregate_records(baseline, events)
        operational_assists = snapshot["counters"]["OPERATIONAL_ASSIST"]
        self.assertEqual("UNKNOWN", operational_assists["status"])
        self.assertEqual("NOT_BACKFILLED", operational_assists["baseline"])
        self.assertEqual(0, operational_assists["known_count"])
        self.assertNotIn("count", operational_assists)
        self.assertIn(
            "Bounded Operational Assists: UNKNOWN / NOT BACKFILLED",
            render_snapshot(snapshot),
        )

        for metric in snapshot["resource_deltas"].values():
            self.assertEqual("UNKNOWN", metric["status"])
            self.assertEqual([], metric["measured"])

    def test_checked_in_human_snapshot_is_exactly_derived(self) -> None:
        baseline, events = loaded()
        expected = render_snapshot(aggregate_records(baseline, events))
        specification = SPEC_PATH.read_text(encoding="utf-8")
        start_marker = "<!-- compound-evidence-meter-snapshot:start -->\n```text\n"
        end_marker = "```\n<!-- compound-evidence-meter-snapshot:end -->"
        self.assertIn(start_marker, specification)
        rendered = specification.split(start_marker, 1)[1].split(end_marker, 1)[0]
        self.assertEqual(expected, rendered)


class CompoundEvidenceMeterAdmissionTests(unittest.TestCase):
    def assert_invalid(self, records: list[dict[str, object]], message: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_records(Path(directory), records)
            with self.assertRaisesRegex(MeterValidationError, message):
                load_ledger(path, REPO_ROOT)

    def test_duplicate_event_identity_cannot_double_count(self) -> None:
        records = raw_records()
        records.append(deepcopy(records[1]))
        self.assert_invalid(records, "duplicate event identity")

    def test_malformed_or_untraceable_event_cannot_silently_count(self) -> None:
        records = raw_records()
        records[1]["source_identity"]["sha256"] = "0" * 64  # type: ignore[index]
        self.assert_invalid(records, "source identity is untraceable")

        records = raw_records()
        records[0]["source_artifacts"][0]["sha256"] = "0" * 64  # type: ignore[index]
        self.assert_invalid(records, "SHA-256 does not match the Git blob")

        records = raw_records()
        records[1]["evidence_pointer"] = (
            "validation/stage_b_one_automatic_continuation_001.md"
            "#section-that-does-not-exist"
        )
        self.assert_invalid(records, "section is absent from the exact source artifact")

    def test_verified_reuse_requires_a_prior_identified_structure(self) -> None:
        records = raw_records()
        reuse = next(
            record
            for record in records
            if record.get("event_type") == "VERIFIED_REUSE"
        )
        reuse["related_prior_event_id"] = None
        self.assert_invalid(records, "requires a prior identified structure")

    def test_causal_continuation_requires_causal_source_evidence(self) -> None:
        records = raw_records()
        continuation = next(
            record
            for record in records
            if record.get("event_type") == "CAUSAL_CONTINUATION"
        )
        del continuation["measured_values"]["source_evidence_sha256"]  # type: ignore[index]
        self.assert_invalid(records, "source_evidence_sha256 must be a non-empty string")

        records = raw_records()
        continuation = next(
            record
            for record in records
            if record.get("event_type") == "CAUSAL_CONTINUATION"
        )
        continuation["related_prior_event_id"] = None
        self.assert_invalid(records, "requires its causal Worker Run")

    def test_efficiency_comparison_requires_actual_measured_pair_evidence(self) -> None:
        records = raw_records()
        source = records[0]["source_artifacts"][6]  # type: ignore[index]
        metrics = {
            metric: {"status": "UNKNOWN", "reason": "not observed"}
            for metric in (
                "elapsed_time_seconds",
                "worker_run_count",
                "model_cost",
                "token_count",
                "human_intervention_burden",
                "reconstruction_burden",
            )
        }
        records.append(
            {
                "schema": "decision-os.compound-evidence-event.v0.1",
                "record_type": "EVENT",
                "event_id": "cem.invalid-comparison.001",
                "event_type": "EFFICIENCY_COMPARISON",
                "as_of": "2026-08-10T00:00:00+09:00",
                "source_artifact": source["path"],
                "source_identity": {
                    "repository_commit": source["repository_commit"],
                    "git_blob": source["git_blob"],
                    "sha256": source["sha256"],
                },
                "evidence_pointer": (
                    "field_notes/132_autonomy_cost_and_intervention_ev.md"
                    "#why-this-is-not-yet-a-rule"
                ),
                "goal_or_chain_id": "comparison-without-observation",
                "related_prior_event_id": None,
                "measured_values": {
                    "comparison_id": "comparison-without-observation",
                    "routes": ["AUTONOMOUS", "BOUNDED_OPERATIONAL_ASSIST"],
                    "pairing_basis": "claimed comparable",
                    "metrics": metrics,
                },
                "evidence_boundary": "No resource axis was observed.",
                "claim_status": "MEASURED",
            }
        )
        self.assert_invalid(records, "needs actual measured comparison evidence")

    def test_adding_one_valid_event_changes_only_its_counter(self) -> None:
        records = raw_records()
        source = records[0]["source_artifacts"][2]  # type: ignore[index]
        records.append(
            {
                "schema": "decision-os.compound-evidence-event.v0.1",
                "record_type": "EVENT",
                "event_id": "cem.future-goal.fixture.001",
                "event_type": "BOUNDED_GOAL",
                "as_of": "2026-08-10T00:00:00+09:00",
                "source_artifact": source["path"],
                "source_identity": {
                    "repository_commit": source["repository_commit"],
                    "git_blob": source["git_blob"],
                    "sha256": source["sha256"],
                },
                "evidence_pointer": (
                    "validation/stage_d_leave_the_desk_dogfood_001.md"
                    "#original-user-goal"
                ),
                "goal_or_chain_id": "future-valid-fixture-chain",
                "related_prior_event_id": None,
                "measured_values": {"completion_status": "PASS"},
                "evidence_boundary": "Synthetic validator fixture only.",
                "claim_status": "OBSERVED",
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            augmented_path = write_records(Path(directory), records)
            base, base_events = loaded()
            augmented, augmented_events = load_ledger(augmented_path, REPO_ROOT)

        before = aggregate_records(base, base_events)["counters"]
        after = aggregate_records(augmented, augmented_events)["counters"]
        for event_type in EVENT_TYPES:
            with self.subTest(event_type=event_type):
                if event_type == "BOUNDED_GOAL":
                    self.assertEqual(before[event_type]["count"] + 1, after[event_type]["count"])
                else:
                    self.assertEqual(before[event_type], after[event_type])


class CompoundEvidenceMeterCanonicalSurfaceTests(unittest.TestCase):
    def test_current_canonical_and_handoff_surfaces_are_consistent(self) -> None:
        payload, exit_code = inspect_repository(REPO_ROOT)
        self.assertEqual(EXIT_OK, exit_code)
        self.assertEqual("PASS", payload["v12_state"])
        self.assertEqual("HOLD", payload["v13_gate"])
        self.assertIn(
            "Preserve the exact compound-authority and acceleration boundary",
            payload["next_authorized_action"],
        )
        for relative_path in (
            "docs/current_signal.md",
            "handoff/current_codex_handoff.md",
        ):
            with self.subTest(relative_path=relative_path):
                current = (REPO_ROOT / relative_path).read_text(
                    encoding="utf-8"
                ).split(
                    "Everything below this boundary is preserved historical",
                    maxsplit=1,
                )[0]
                self.assertIn(
                    "V13 — Compound Loop / Authority Preflight Integration",
                    current,
                )
                self.assertIn(
                    "13-121 Blank-Slate Highest-EV Selection:\nPASS",
                    current,
                )
                self.assertIn(
                    "Selected capability:\nCompound authority preflight before "
                    "Repository Default reuse",
                    current,
                )
                self.assertIn(
                    "Classification:\nCONTROL",
                    current,
                )
                self.assertIn(
                    "Selection basis:\nhighest current realizable EV, not "
                    "category preference",
                    current,
                )
                self.assertIn(
                    "13-122 Compound Authority Preflight:\nINTEGRATED",
                    current,
                )
                self.assertIn(
                    "active Stage B/C Create/Modify authority is checked before "
                    "Repository Default\nreuse can authorize the action.",
                    current,
                )
                self.assertIn(
                    "valid in-envelope and ordinary non-compound Default reuse "
                    "remain intact.",
                    current,
                )
                self.assertIn(
                    "V13 now preflights active Stage B/C Create/Modify proposals "
                    "against the current\npersisted compound mutation envelope "
                    "before Repository Default reuse can\nauthorize them.",
                    current,
                )
                self.assertIn(
                    "This prevents an older reusable Default from widening the\n"
                    "current compound Run's file-mutation authority.",
                    current,
                )
                self.assertIn(
                    "This does not establish a generic permission hierarchy; "
                    "shell, network,\narbitrary-tool, publication, or release "
                    "authority; generalized capability\nalgebra; or a full "
                    "authority-system redesign.",
                    current,
                )
                self.assertIn(
                    "V11 Selective Reconnect:\nINTEGRATED",
                    current,
                )
                self.assertIn(
                    "V6 Safety Non-Dilution:\nINTEGRATED",
                    current,
                )
                self.assertIn(
                    "V8 Temporal Evidence Invalidation:\nINTEGRATED",
                    current,
                )
                self.assertIn(
                    "V10 Protective Rescale:\n"
                    "HOLD — Carrier observability missing",
                    current,
                )
                self.assertIn(
                    "Genesis Selection:\n"
                    "HOLD — typed present-Goal comparison missing",
                    current,
                )
                self.assertIn(
                    "13-108:\nNONCANONICAL",
                    current,
                )
                self.assertIn(
                    "Capability Commit:\n"
                    "8425b6e04a25f469687d8ca54b76258771a69027",
                    current,
                )
                self.assertIn(
                    "Canonical Starting Main:\n"
                    "b1131284854501a0364fb09984f1a4ea56eed531",
                    current,
                )
                self.assertIn(
                    "Field Note 132:\nVerification pending",
                    current,
                )
                self.assertIn(
                    "Compound Evidence Meter:\nunchanged",
                    current,
                )
                self.assertIn("HOLD — NO NEXT AUTHORITY", current)

    def test_historical_surface_tails_are_byte_for_byte_preserved(self) -> None:
        cases = (
            (
                REPO_ROOT / "docs" / "current_signal.md",
                b"# Current Signal\n\n",
                "2b65f7da9a5bba35a3116659e526e794e0623b9bb285277701082c8e937d8ecb",
            ),
            (
                REPO_ROOT / "handoff" / "current_codex_handoff.md",
                b"# Current Codex Handoff - V13 LoopKit\n\n",
                "f446d44147c02cd1bcf566ed936e04336ed6d4bc81c0d354cbb8cfc11db7f4c4",
            ),
        )
        for path, historical_start, expected_sha256 in cases:
            with self.subTest(path=path):
                contents = path.read_bytes()
                offset = contents.index(historical_start)
                historical_tail = contents[offset:]
                self.assertEqual(expected_sha256, hashlib.sha256(historical_tail).hexdigest())


if __name__ == "__main__":
    unittest.main()
