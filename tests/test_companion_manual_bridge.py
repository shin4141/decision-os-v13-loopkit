from __future__ import annotations

from collections.abc import Mapping
import copy
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from decision_os.companion.manual_bridge import (
    EXPECTED_EVIDENCE_IDENTITY,
    GOLDEN_ROLES,
    GUIDED_INTAKE_AUTHORITY,
    GUIDED_INTAKE_CURRENT_GATE,
    GUIDED_INTAKE_EVIDENCE_IDENTITY,
    GUIDED_INTAKE_HANDOFF_FIELD,
    GUIDED_INTAKE_PROFILE,
    GUIDED_INTAKE_PROTOCOL_RUN_ID,
    GUIDED_INTAKE_TASK_ID,
    GUIDED_INTAKE_TRANSFER_AUTHORITY,
    GUIDED_INTAKE_TRANSFER_SCHEMA,
    HANDOFF_FIELDS,
    PRE_BRIDGE_UNKNOWN,
    REPLAY_FIELDS,
    REPLAY_STATUSES,
    UNKNOWN,
    BridgeSessionController,
    ManualBridgeConflictError,
    ManualBridgeIntegrityError,
    ManualBridgeValidationError,
    sha256_bytes,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "companion_manual_bridge_v0_1"
FIXED_TIME = "2026-07-29T00:00:00Z"
PRODUCT_AS_OF = "63eb260a94595298e2b07b476f7f9d8572c9ef09"


class DeterministicIds:
    def __init__(self, prefix: str = "fixture-id") -> None:
        self._prefix = prefix
        self._values = itertools.count(1)

    def __call__(self) -> str:
        return f"{self._prefix}-{next(self._values):04d}"


def create_repository(parent: Path, name: str = "repo") -> Path:
    repository = parent / name
    repository.mkdir()
    subprocess.run(
        ("git", "init", "-q", str(repository)),
        check=True,
        capture_output=True,
    )
    (repository / "tracked.txt").write_text("unchanged\n", encoding="utf-8")
    return repository


def worktree_bytes(repository: Path) -> dict[str, bytes]:
    return {
        path.relative_to(repository).as_posix(): path.read_bytes()
        for path in repository.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(repository).parts
    }


def complete_boundary(**updates: object) -> dict[str, object]:
    boundary: dict[str, object] = {
        "task_id": "V13-CMB-001",
        "protocol_run_id": "V13-PMR-002",
        "objective": "Implement the bounded Companion Manual Bridge v0.1.",
        "completion_line": (
            "Produce one bounded implementation and Builder evidence for audit."
        ),
        "do_not_touch": (
            "AccelerationStore, Verified Save, merge, publication, and release."
        ),
        "current_gate": "GO UNDER CAP — FRESH BUILDER IMPLEMENTATION ONLY",
        "authority_boundary": (
            "Artifact identity grants no execution, merge, or publication authority."
        ),
        "as_of_commit": PRODUCT_AS_OF,
        "required_next_actor": "Fresh SOL / coding-agent Builder",
        "evidence_packet_identity": dict(EXPECTED_EVIDENCE_IDENTITY),
        "current_state": "Accepted Pro Design is ready for bounded transfer.",
        "active_branch": "codex/v13-cmb-001-build",
        "missing_closure": (
            "Build Receipt, independent Pro Audit, and Replay remain open."
        ),
        "what_receiving_ai_owns": "The bounded implementation only.",
        "first_one_action": "Verify the fixed identities.",
        "do_not_continue_boundary": "Do not merge, publish, release, or self-audit.",
        "framework_lens_used": "Artifact provenance",
        "relevant_decision_os_layer": "V13 / Stage 2",
        "reinterpretation_question": "Which identity survives transfer?",
        "framework_derived_finding": "Authority must remain independently visible.",
    }
    boundary.update(updates)
    return boundary


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def fixture_json(name: str) -> dict[str, object]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"Fixture is not an object: {name}")
    return value


def replay_fixture(name: str) -> dict[str, object]:
    value = fixture_json(name)
    fields = value.get("fields")
    if not isinstance(fields, dict):
        raise AssertionError(f"Replay fixture has no fields object: {name}")
    # Project the accepted packet's prose-friendly alias only if the landed
    # module exports the longer stable API ID.
    if (
        "as_of_identity" not in REPLAY_FIELDS
        and "as_of_commit_or_artifact_hash" in REPLAY_FIELDS
        and "as_of_identity" in fields
        and "as_of_commit_or_artifact_hash" not in fields
    ):
        fields["as_of_commit_or_artifact_hash"] = fields.pop("as_of_identity")
    return value


def typed_metadata(role: str, **updates: object) -> dict[str, object]:
    authorities = {
        "EVIDENCE_PACKET": "EVIDENCE_ONLY",
        "PRO_DESIGN": "DESIGN_ONLY_NO_EXECUTION_AUTHORITY",
        "BUILD_RECEIPT": "EXECUTION_EVIDENCE_ONLY",
        "PRO_AUDIT": "INDEPENDENT_JUDGMENT_ONLY",
        "REUSABLE_DELTA_RECORD": "FUTURE_USE_CANDIDATE_ONLY",
    }
    metadata: dict[str, object] = {
        "schema": "decision-os-companion-manual-bridge-record-v0.1",
        "task_id": "V13-CMB-001",
        "protocol_run_id": "V13-PMR-002",
        "artifact_role": role,
        "model_identity": {
            "value": "Synthetic Pro Model",
            "basis": "SELF_DECLARED",
            "verification_state": "UNVERIFIED",
        },
        "role_identity": (
            "Independent Pro Designer"
            if role == "PRO_DESIGN"
            else "Synthetic Fixture Role"
        ),
        "artifact_authored_at": "2026-07-28T22:00:00+09:00",
        "as_of_commit": PRODUCT_AS_OF,
        "evidence_packet_identity": dict(EXPECTED_EVIDENCE_IDENTITY),
        "authority_state": authorities[role],
        "objective": "Bounded fixture objective.",
        "completion_line": "Bounded fixture completion.",
        "do_not_touch": "No authority expansion.",
        "current_gate": "HOLD — SEPARATE AUTHORITY REQUIRED",
        "authority_boundary": "Identity is not authority.",
        "required_next_actor": "Fresh SOL / coding-agent Builder",
        "findings": [],
        "human_execution_cost": [],
        "reusable_delta": [],
        "unknowns": ["Independent Product Result"],
    }
    metadata.update(updates)
    return metadata


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def guided_intake_transfer(**updates: object) -> dict[str, object]:
    transfer: dict[str, object] = {
        "schema_version": GUIDED_INTAKE_TRANSFER_SCHEMA,
        "original_request_sha256": hashlib.sha256(
            b"  exact original request\r\nwith trailing space \n"
        ).hexdigest(),
        "frozen_intake_sha256": hashlib.sha256(
            b'{"frozen":"intake"}\n'
        ).hexdigest(),
        "objective": "  Preserve 日本語 without normalization.  ",
        "completion_line": (
            "A frozen intake is transferred with exact field identities."
        ),
        "do_not_touch": [
            {
                "basis_kind": "USER_EXPLICIT",
                "item_id": "DNT-1",
                "text": "Existing Runner",
            }
        ],
        "unknown": [
            {
                "current_state": "OPEN",
                "statement": "Whether the next actor needs another artifact",
                "unknown_id": "UNK-1",
            }
        ],
        "authority_boundary": GUIDED_INTAKE_AUTHORITY,
        "as_of_commit": GUIDED_INTAKE_EVIDENCE_IDENTITY["commit"],
        "evidence_packet_identity": dict(
            GUIDED_INTAKE_EVIDENCE_IDENTITY
        ),
    }
    transfer.update(updates)
    transfer["field_hashes"] = {
        field: hashlib.sha256(
            canonical_json_bytes(transfer[field])
        ).hexdigest()
        for field in (
            "objective",
            "completion_line",
            "do_not_touch",
            "unknown",
            "authority_boundary",
        )
    }
    return transfer


class CompanionManualBridgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = create_repository(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def controller(
        self,
        repository: Path | None = None,
    ) -> BridgeSessionController:
        return BridgeSessionController(
            repository or self.repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds(),
        )

    def session(
        self,
        controller: BridgeSessionController | None = None,
        **updates: object,
    ) -> BridgeSessionController:
        bridge = controller or self.controller()
        bridge.create_session(complete_boundary(**updates))
        return bridge

    def import_fixture(
        self,
        bridge: BridgeSessionController,
        filename: str,
        role: str,
        *,
        mode: str = "BYTE_EXACT_FILE_IMPORT",
    ) -> dict[str, object]:
        return bridge.import_artifact(
            selected_role=role,
            payload=fixture_bytes(filename),
            source_path_or_label=filename,
            import_mode=mode,
        )

    def frozen_golden_session(
        self,
        repository: Path | None = None,
    ) -> BridgeSessionController:
        bridge = self.session(
            self.controller(repository) if repository is not None else None
        )
        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()
        bridge.freeze_output("EXECUTION_HANDOFF")
        self.import_fixture(bridge, "build_receipt_valid.md", "BUILD_RECEIPT")
        self.import_fixture(bridge, "pro_audit_valid.md", "PRO_AUDIT")
        self.import_fixture(
            bridge,
            "reusable_delta_valid.md",
            "REUSABLE_DELTA_RECORD",
        )
        bridge.generate_golden_manifest()
        bridge.freeze_output("GOLDEN_MANIFEST")
        return bridge

    def bound_replay_pair(
        self,
        bridge: BridgeSessionController,
    ) -> tuple[dict[str, object], dict[str, object]]:
        snapshot = bridge.snapshot()
        manifest_identity = snapshot["outputs"]["GOLDEN_MANIFEST"]["sha256"]
        baseline = copy.deepcopy(
            snapshot["golden_manifest"]["replay_baseline"]
        )
        baseline["manifest_identity"] = manifest_identity
        candidate = copy.deepcopy(baseline)
        candidate["candidate_id"] = "fixture-replay-preserved-001"
        return baseline, candidate

    def test_exact_byte_hashing_line_endings_trailing_newline_and_paste(
        self,
    ) -> None:
        bridge = self.session()
        payloads = (
            (b"alpha\nbeta\n", "lf"),
            (b"alpha\r\nbeta\r\n", "crlf"),
            (b"alpha\nbeta", "no-trailing-newline"),
        )
        expected = {hashlib.sha256(value).hexdigest() for value, _ in payloads}

        for payload, label in payloads:
            bridge.import_artifact(
                selected_role="PRO_DESIGN",
                payload=payload,
                source_path_or_label=label,
                import_mode="BYTE_EXACT_FILE_IMPORT",
                metadata=typed_metadata("PRO_DESIGN"),
            )

        snapshot = bridge.snapshot()
        observed = {
            record["artifact_content_hash"] for record in snapshot["imports"]
        }
        self.assertEqual(expected, observed)
        self.assertEqual(3, len(observed))
        self.assertEqual(
            hashlib.sha256(b"alpha\nbeta\n").hexdigest(),
            sha256_bytes(b"alpha\nbeta\n"),
        )

        pasted = "日本語\ncaptured"
        bridge.import_artifact(
            selected_role="BUILD_RECEIPT",
            payload=pasted.encode("utf-8"),
            source_path_or_label="Manual paste capture",
            import_mode="PASTE_CAPTURE",
            metadata=typed_metadata("BUILD_RECEIPT"),
        )
        record = bridge.snapshot()["imports"][-1]
        self.assertEqual("PASTE_CAPTURE", record["import_mode"])
        self.assertEqual(
            hashlib.sha256(pasted.encode("utf-8")).hexdigest(),
            record["artifact_content_hash"],
        )
        self.assertNotEqual("BYTE_EXACT_FILE_IMPORT", record["import_mode"])
        self.assertEqual(
            1,
            bridge.snapshot()["burden"]["shin_copy_paste_count"][
                "value_or_unknown"
            ],
        )

    def test_declared_hash_mismatch_rejects_before_blob_acceptance(self) -> None:
        bridge = self.session()
        payload = b"exact bytes\n"
        with self.assertRaisesRegex(
            ManualBridgeValidationError,
            "Declared SHA-256",
        ):
            bridge.import_artifact(
                selected_role="PRO_DESIGN",
                payload=payload,
                source_path_or_label="mismatch.md",
                import_mode="BYTE_EXACT_FILE_IMPORT",
                metadata=typed_metadata("PRO_DESIGN"),
                declared_sha256="0" * 64,
            )

        snapshot = bridge.snapshot()
        self.assertEqual([], snapshot["imports"])
        self.assertEqual("DECLARED_HASH_MISMATCH", snapshot["hold_reason"])
        rejected = bridge.store.read_events()[-1]
        self.assertEqual("ARTIFACT_IMPORT_REJECTED", rejected["kind"])
        blob = (
            bridge.store.root
            / "artifacts"
            / "sha256"
            / f"{sha256_bytes(payload)}.bin"
        )
        self.assertFalse(blob.exists())

    def test_guided_intake_accepts_exact_transfer_hashes_and_unknowns(
        self,
    ) -> None:
        bridge = self.controller()
        transfer = guided_intake_transfer()

        accepted = bridge.accept_guided_intake(transfer)
        boundary = accepted["session"]["boundary"]
        nested = boundary["guided_intake_boundary"]
        receipt = boundary["guided_intake_transfer_receipt"]

        self.assertEqual(transfer, nested)
        self.assertEqual(GUIDED_INTAKE_PROFILE, boundary["bridge_profile"])
        self.assertEqual(GUIDED_INTAKE_TASK_ID, boundary["task_id"])
        self.assertEqual(
            GUIDED_INTAKE_PROTOCOL_RUN_ID,
            boundary["protocol_run_id"],
        )
        self.assertEqual(transfer["objective"], boundary["objective"])
        self.assertEqual(
            transfer["completion_line"],
            boundary["completion_line"],
        )
        self.assertEqual(
            canonical_json_bytes(transfer["do_not_touch"]).decode("utf-8"),
            boundary["do_not_touch"],
        )
        self.assertEqual(
            GUIDED_INTAKE_CURRENT_GATE,
            boundary["current_gate"],
        )
        self.assertEqual(transfer["unknown"], nested["unknown"])
        self.assertEqual(
            transfer["field_hashes"],
            receipt["pre_transfer_field_hashes"],
        )
        self.assertEqual(
            transfer["field_hashes"],
            receipt["post_transfer_field_hashes"],
        )
        self.assertEqual(
            transfer["field_hashes"],
            receipt["field_hashes"],
        )
        self.assertEqual(
            transfer["frozen_intake_sha256"],
            receipt["freeze_sha256"],
        )
        self.assertEqual(
            accepted["session"]["session_id"],
            receipt["bridge_session_id"],
        )
        self.assertEqual("TRANSFER_ACCEPTED", receipt["transfer_result"])
        self.assertEqual(
            GUIDED_INTAKE_TRANSFER_AUTHORITY,
            receipt["authority_state"],
        )
        self.assertEqual("COPY_READY", accepted["state"])
        self.assertIsNone(accepted["hold_reason"])
        self.assertEqual(receipt, accepted["guided_intake_transfer"])

    def test_guided_intake_rejects_altered_transfer_before_session(
        self,
    ) -> None:
        bridge = self.controller()
        altered = guided_intake_transfer()
        altered["objective"] = f"{altered['objective']} expanded"

        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "HOLD — TRANSFER ALTERED BOUNDARY",
        ):
            bridge.accept_guided_intake(altered)

        self.assertIsNone(bridge.snapshot()["session"])

    def test_guided_intake_rejects_authority_even_with_matching_hash(
        self,
    ) -> None:
        bridge = self.controller()
        inflated = guided_intake_transfer(
            authority_boundary="EXECUTION_AUTHORITY_GRANTED",
        )

        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "HOLD — TRANSFER ALTERED BOUNDARY",
        ):
            bridge.accept_guided_intake(inflated)

        self.assertIsNone(bridge.snapshot()["session"])

    def test_guided_intake_conflicts_with_existing_bridge_session(
        self,
    ) -> None:
        bridge = self.session()
        existing_id = bridge.snapshot()["session"]["session_id"]

        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "already active",
        ):
            bridge.accept_guided_intake(guided_intake_transfer())

        self.assertEqual(
            existing_id,
            bridge.snapshot()["session"]["session_id"],
        )

    def test_guided_intake_handoff_block_is_conditional_and_exact(
        self,
    ) -> None:
        guided_repository = create_repository(self.root, "guided-handoff")
        bridge = self.controller(guided_repository)
        transfer = guided_intake_transfer(
            objective=(
                "Keep exact text\nwithout allowing "
                "## Current Gate heading injection"
            ),
            completion_line="Transfer stays exact and testable.",
        )
        bridge.accept_guided_intake(transfer)
        bridge.import_artifact(
            selected_role="PRO_DESIGN",
            payload=b"guided intake independent pro design",
            source_path_or_label="guided-intake-pro-design",
            import_mode="BYTE_EXACT_FILE_IMPORT",
            metadata=typed_metadata(
                "PRO_DESIGN",
                task_id=GUIDED_INTAKE_TASK_ID,
                protocol_run_id=GUIDED_INTAKE_PROTOCOL_RUN_ID,
                as_of_commit=transfer["as_of_commit"],
                evidence_packet_identity=dict(
                    GUIDED_INTAKE_EVIDENCE_IDENTITY
                ),
                objective=transfer["objective"],
                completion_line=transfer["completion_line"],
                do_not_touch=transfer["do_not_touch"],
                authority_boundary=GUIDED_INTAKE_AUTHORITY,
            ),
        )
        generated = bridge.generate_execution_handoff()
        text = generated["outputs"]["EXECUTION_HANDOFF"]["content"]

        for field in HANDOFF_FIELDS:
            self.assertEqual(1, text.count(f"## {field}\n"))
        self.assertEqual(
            1,
            text.count(f"## {GUIDED_INTAKE_HANDOFF_FIELD}\n"),
        )
        for label, field in (
            ("Original Request SHA-256", "original_request_sha256"),
            ("Frozen Intake SHA-256", "frozen_intake_sha256"),
            ("Objective", "objective"),
            ("Completion Line", "completion_line"),
            ("Do Not Touch", "do_not_touch"),
            ("Open UNKNOWNs", "unknown"),
            ("Guided Intake Authority", "authority_boundary"),
        ):
            rendered = canonical_json_bytes(transfer[field]).decode("utf-8")
            self.assertIn(f"{label}:\n{rendered}\n", text)
        self.assertEqual(1, text.count("## Current Gate\n"))
        frozen = bridge.freeze_output("EXECUTION_HANDOFF")
        self.assertTrue(
            frozen["outputs"]["EXECUTION_HANDOFF"]["frozen"]
        )

        legacy = self.session(
            self.controller(create_repository(self.root, "legacy-handoff"))
        )
        self.import_fixture(legacy, "pro_design_valid.md", "PRO_DESIGN")
        legacy.generate_execution_handoff()
        legacy_text = legacy.output_bytes("EXECUTION_HANDOFF").decode(
            "utf-8"
        )
        self.assertNotIn(
            f"## {GUIDED_INTAKE_HANDOFF_FIELD}\n",
            legacy_text,
        )
        self.assertNotIn("guided_intake_transfer", legacy.snapshot())

    def test_identity_fields_remain_separate_and_unknown_is_preserved(self) -> None:
        bridge = self.session()
        payload = b"unstructured artifact bytes"
        bridge.import_artifact(
            selected_role="BUILD_RECEIPT",
            payload=payload,
            source_path_or_label="opaque-build-receipt",
            import_mode="BYTE_EXACT_FILE_IMPORT",
            metadata={
                "artifact_role": "BUILD_RECEIPT",
                "task_id": "V13-CMB-001",
                "protocol_run_id": "V13-PMR-002",
                "as_of_commit": PRODUCT_AS_OF,
                "authority_state": "EXECUTION_EVIDENCE_ONLY",
            },
        )
        record = bridge.snapshot()["imports"][0]

        self.assertEqual("V13-CMB-001", record["task_id"])
        self.assertEqual("V13-PMR-002", record["protocol_run_id"])
        self.assertEqual("BUILD_RECEIPT", record["selected_role"])
        self.assertEqual("BUILD_RECEIPT", record["declared_role"])
        self.assertEqual("UNKNOWN", record["model_identity"]["value"])
        self.assertEqual("UNKNOWN", record["artifact_authored_at"])
        self.assertEqual(FIXED_TIME, record["imported_at"])
        self.assertEqual(PRODUCT_AS_OF, record["as_of_commit"])
        self.assertEqual(sha256_bytes(payload), record["artifact_content_hash"])
        self.assertEqual("EXECUTION_EVIDENCE_ONLY", record["authority_state"])
        self.assertEqual(
            "BUILDER EVIDENCE ONLY / INDEPENDENT AUDIT REQUIRED",
            bridge.snapshot()["results"]["product"]["result"],
        )

    def test_pro_design_evidence_identity_mismatch_never_becomes_effective(
        self,
    ) -> None:
        bridge = self.session()
        metadata = typed_metadata("PRO_DESIGN")
        metadata["evidence_packet_identity"] = {
            "commit": "f" * 40,
            "path": EXPECTED_EVIDENCE_IDENTITY["path"],
            "blob_sha": "e" * 40,
            "sha256": "d" * 64,
            "product_as_of_commit": PRODUCT_AS_OF,
        }
        imported = bridge.import_artifact(
            selected_role="PRO_DESIGN",
            payload=b"synthetic design with a mismatched evidence identity",
            source_path_or_label="mismatched-evidence-design",
            import_mode="BYTE_EXACT_FILE_IMPORT",
            metadata=metadata,
        )
        record = imported["imports"][-1]
        self.assertEqual(
            "HOLD_EVIDENCE_IDENTITY_MISMATCH",
            record["validation_state"],
        )
        self.assertFalse(record["effective"])
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "valid frozen Pro Design",
        ):
            bridge.generate_execution_handoff()

    def test_role_mismatch_duplicate_collision_and_design_audit_separation(
        self,
    ) -> None:
        mismatch = self.session(
            self.controller(create_repository(self.root, "mismatch"))
        )
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "ROLE MISMATCH",
        ):
            self.import_fixture(
                mismatch,
                "artifact_role_mismatch.md",
                "PRO_DESIGN",
            )

        duplicate = self.session(
            self.controller(create_repository(self.root, "duplicate"))
        )
        self.import_fixture(duplicate, "pro_design_valid.md", "PRO_DESIGN")
        first_id = duplicate.snapshot()["imports"][0]["import_event_id"]
        self.import_fixture(duplicate, "pro_design_valid.md", "PRO_DESIGN")
        records = duplicate.snapshot()["imports"]
        self.assertEqual(2, len(records))
        self.assertEqual(first_id, records[1]["duplicate_of_import_event_id"])
        self.assertTrue(records[0]["effective"])
        self.assertFalse(records[1]["effective"])

        collision = self.session(
            self.controller(create_repository(self.root, "collision"))
        )
        shared = b"same untyped bytes"
        collision.import_artifact(
            selected_role="PRO_DESIGN",
            payload=shared,
            source_path_or_label="first",
            import_mode="BYTE_EXACT_FILE_IMPORT",
            metadata={"authority_state": "UNKNOWN"},
        )
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "ROLE COLLISION",
        ):
            collision.import_artifact(
                selected_role="BUILD_RECEIPT",
                payload=shared,
                source_path_or_label="second",
                import_mode="BYTE_EXACT_FILE_IMPORT",
                metadata={"authority_state": "UNKNOWN"},
            )

        separated = self.session(
            self.controller(create_repository(self.root, "separated"))
        )
        self.import_fixture(separated, "pro_design_valid.md", "PRO_DESIGN")
        self.import_fixture(separated, "pro_audit_valid.md", "PRO_AUDIT")
        role_records = separated.snapshot()["imports"]
        self.assertNotEqual(
            role_records[0]["import_event_id"],
            role_records[1]["import_event_id"],
        )
        self.assertEqual(
            {"PRO_DESIGN", "PRO_AUDIT"},
            {record["selected_role"] for record in role_records},
        )
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "ROLE MISMATCH",
        ):
            self.import_fixture(
                separated,
                "build_receipt_valid.md",
                "PRO_AUDIT",
            )

    def test_authority_inflation_and_builder_generated_audit_block(self) -> None:
        inflated = self.session()
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "BLOCKED_AUTHORITY_INFLATION",
        ):
            self.import_fixture(
                inflated,
                "artifact_authority_inflated.md",
                "PRO_DESIGN",
            )
        self.assertEqual(
            "BLOCKED_AUTHORITY_INFLATION",
            inflated.snapshot()["state"],
        )

        audit = self.session(self.controller(create_repository(self.root, "audit")))
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "Builder-generated Pro Audit",
        ):
            audit.import_artifact(
                selected_role="PRO_AUDIT",
                payload=b"synthetic audit",
                source_path_or_label="builder-audit",
                import_mode="BYTE_EXACT_FILE_IMPORT",
                metadata=typed_metadata(
                    "PRO_AUDIT",
                    builder_generated=True,
                ),
            )

    def test_copy_and_handoff_are_deterministic_complete_and_freezable(self) -> None:
        bridge = self.session()
        first_copy = bridge.copy_for_pro()["outputs"]["COPY_FOR_PRO"]["content"]
        second_copy = bridge.copy_for_pro()["outputs"]["COPY_FOR_PRO"]["content"]
        self.assertEqual(first_copy, second_copy)
        self.assertTrue(first_copy.endswith("\n"))
        self.assertNotIn("\r", first_copy)

        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()
        first_handoff = bridge.output_bytes("EXECUTION_HANDOFF")
        bridge.generate_execution_handoff()
        second_handoff = bridge.output_bytes("EXECUTION_HANDOFF")
        self.assertEqual(first_handoff, second_handoff)
        text = first_handoff.decode("utf-8")
        for field in HANDOFF_FIELDS:
            self.assertIn(f"## {field}\n", text)
        self.assertIn("INSTRUCTION_ARTIFACT_ONLY", text)
        self.assertIn(
            "DOES NOT RETROACTIVELY AUTHORIZE CODEX 13-25",
            text,
        )
        self.assertNotIn("\r", text)
        self.assertTrue(first_handoff.endswith(b"\n"))

        frozen = bridge.freeze_output("EXECUTION_HANDOFF")
        self.assertTrue(
            frozen["outputs"]["EXECUTION_HANDOFF"]["frozen"],
        )
        self.assertEqual("HANDOFF_FROZEN", frozen["state"])
        self.assertEqual(
            frozen["outputs"]["EXECUTION_HANDOFF"]["sha256"],
            sha256_bytes(first_handoff),
        )

    def test_private_store_is_lazy_git_common_dir_and_worktree_is_unchanged(
        self,
    ) -> None:
        before = worktree_bytes(self.repository)
        bridge = self.controller()
        self.assertEqual(
            (self.repository / ".git").resolve()
            / "decision-os"
            / "manual-bridge"
            / "v0.1",
            bridge.store.root,
        )
        self.assertFalse(bridge.store.root.exists())
        self.assertIsNone(bridge.snapshot()["session"])
        self.assertFalse(bridge.store.root.exists())

        self.session(bridge)
        created = bridge.snapshot()
        self.assertEqual("fixture-id-0001", created["session"]["session_id"])
        self.assertEqual(FIXED_TIME, created["session"]["created_at"])
        bridge.copy_for_pro()
        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()
        self.assertEqual(before, worktree_bytes(self.repository))
        self.assertTrue(bridge.store.events_path.is_file())
        self.assertFalse((self.repository / "events.jsonl").exists())

        source = create_repository(self.root, "common-source")
        subprocess.run(
            ("git", "-C", str(source), "config", "user.name", "Fixture"),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            (
                "git",
                "-C",
                str(source),
                "config",
                "user.email",
                "fixture@example.invalid",
            ),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ("git", "-C", str(source), "add", "tracked.txt"),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ("git", "-C", str(source), "commit", "-q", "-m", "fixture"),
            check=True,
            capture_output=True,
        )
        linked = self.root / "linked-worktree"
        subprocess.run(
            (
                "git",
                "-C",
                str(source),
                "worktree",
                "add",
                "-q",
                "--detach",
                str(linked),
            ),
            check=True,
            capture_output=True,
        )
        linked_before = worktree_bytes(linked)
        linked_bridge = self.controller(linked)
        self.assertEqual(
            (source / ".git").resolve()
            / "decision-os"
            / "manual-bridge"
            / "v0.1",
            linked_bridge.store.root,
        )
        self.assertFalse(linked_bridge.store.root.exists())
        self.assertIsNone(linked_bridge.snapshot()["session"])
        self.assertFalse(linked_bridge.store.root.exists())
        self.session(linked_bridge)
        linked_bridge.copy_for_pro()
        self.assertEqual(linked_before, worktree_bytes(linked))

    def test_manifest_always_has_six_roles_and_results_remain_separate(
        self,
    ) -> None:
        bridge = self.session()
        initial_results = bridge.snapshot()["results"]
        missing = bridge.generate_golden_manifest()["golden_manifest"]
        self.assertEqual(list(GOLDEN_ROLES), missing["artifact_order"])
        self.assertEqual(6, len(missing["artifacts"]))
        self.assertEqual(
            list(GOLDEN_ROLES),
            [entry["artifact_role"] for entry in missing["artifacts"]],
        )
        self.assertEqual("GOLDEN_INCOMPLETE", missing["golden_status"])
        self.assertEqual(
            5,
            sum(entry["state"] == "MISSING" for entry in missing["artifacts"]),
        )
        self.assertEqual(initial_results, bridge.snapshot()["results"])

        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()
        bridge.freeze_output("EXECUTION_HANDOFF")
        self.import_fixture(bridge, "build_receipt_valid.md", "BUILD_RECEIPT")
        self.import_fixture(bridge, "pro_audit_valid.md", "PRO_AUDIT")
        self.import_fixture(
            bridge,
            "reusable_delta_valid.md",
            "REUSABLE_DELTA_RECORD",
        )
        complete = bridge.generate_golden_manifest()["golden_manifest"]
        self.assertEqual("GOLDEN_ELIGIBLE", complete["golden_status"])
        self.assertTrue(
            all(entry["state"] == "FROZEN" for entry in complete["artifacts"])
        )
        self.assertEqual(initial_results, bridge.snapshot()["results"])
        final = bridge.freeze_output("GOLDEN_MANIFEST")
        self.assertEqual("GOLDEN_FROZEN", final["state"])
        self.assertEqual(initial_results, final["results"])

    def test_concurrent_controller_instances_recheck_active_session(
        self,
    ) -> None:
        first = BridgeSessionController(
            self.repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("first"),
        )
        second = BridgeSessionController(
            self.repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("second"),
        )

        created = first.create_session(complete_boundary())
        first_session_id = created["session"]["session_id"]
        with self.assertRaises(ManualBridgeConflictError):
            second.create_session(complete_boundary())

        self.assertEqual(first_session_id, first.store.active_session())
        self.assertEqual(
            1,
            sum(
                event["kind"] == "BRIDGE_SESSION_CREATED"
                for event in first.store.read_events()
            ),
        )

    def test_event_truncation_and_session_rollback_fail_closed(self) -> None:
        with self.subTest("event history truncation"):
            truncated_repository = create_repository(self.root, "truncated-events")
            truncated = self.session(self.controller(truncated_repository))
            truncated.store.events_path.write_bytes(b"")

            reopened = self.controller(truncated_repository)
            with self.assertRaises(ManualBridgeIntegrityError):
                reopened.snapshot()

        with self.subTest("materialized session rollback"):
            rollback_repository = create_repository(self.root, "session-rollback")
            rolled_back = self.session(self.controller(rollback_repository))
            session_id = rolled_back.snapshot()["session"]["session_id"]
            session_path = rolled_back.store.session_path(session_id)
            pre_import_session = session_path.read_bytes()

            self.import_fixture(
                rolled_back,
                "pro_design_valid.md",
                "PRO_DESIGN",
            )
            self.assertEqual(2, len(rolled_back.store.read_events()))
            session_path.write_bytes(pre_import_session)

            reopened = self.controller(rollback_repository)
            with self.assertRaises(ManualBridgeIntegrityError):
                reopened.snapshot()

    def test_invalid_imports_are_excluded_from_golden_eligibility(self) -> None:
        bridge = self.session()
        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()
        bridge.freeze_output("EXECUTION_HANDOFF")

        invalid_import_ids: set[str] = set()
        for index, role in enumerate(
            ("BUILD_RECEIPT", "PRO_AUDIT", "REUSABLE_DELTA_RECORD"),
            start=1,
        ):
            imported = bridge.import_artifact(
                selected_role=role,
                payload=f"invalid-{role}-{index}".encode("utf-8"),
                source_path_or_label=f"invalid-{role.lower()}",
                import_mode="BYTE_EXACT_FILE_IMPORT",
                metadata=typed_metadata(role),
            )
            record = imported["imports"][-1]
            self.assertEqual(
                "HOLD_MISSING_REQUIRED_FIELDS",
                record["validation_state"],
            )
            self.assertFalse(record["effective"])
            invalid_import_ids.add(record["import_event_id"])

        manifest = bridge.generate_golden_manifest()["golden_manifest"]
        self.assertEqual("GOLDEN_INCOMPLETE", manifest["golden_status"])
        by_role = {
            entry["artifact_role"]: entry for entry in manifest["artifacts"]
        }
        for role in (
            "BUILD_RECEIPT",
            "PRO_AUDIT",
            "REUSABLE_DELTA_RECORD",
        ):
            self.assertNotEqual("FROZEN", by_role[role]["state"])
            self.assertNotIn(
                by_role[role]["import_event_id"],
                invalid_import_ids,
            )

    def test_replay_requires_a_frozen_eligible_golden_manifest(self) -> None:
        bridge = self.session()
        baseline = replay_fixture("replay_candidate_preserved.json")

        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "Golden|frozen|Replay",
        ):
            bridge.evaluate_replay(
                baseline,
                copy.deepcopy(baseline),
            )

        snapshot = bridge.snapshot()
        self.assertIsNone(snapshot["golden_manifest"])
        self.assertEqual(
            "NOT YET PERFORMED",
            snapshot["results"]["replay"]["result"],
        )
        self.assertNotIn("REPLAY_RESULT", snapshot["outputs"])

    def test_incomplete_manifest_cannot_be_frozen_and_remains_completable(
        self,
    ) -> None:
        bridge = self.session()
        bridge.generate_golden_manifest()
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "incomplete Golden manifest",
        ):
            bridge.freeze_output("GOLDEN_MANIFEST")

        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()
        bridge.freeze_output("EXECUTION_HANDOFF")
        self.import_fixture(bridge, "build_receipt_valid.md", "BUILD_RECEIPT")
        self.import_fixture(bridge, "pro_audit_valid.md", "PRO_AUDIT")
        self.import_fixture(
            bridge,
            "reusable_delta_valid.md",
            "REUSABLE_DELTA_RECORD",
        )
        completed = bridge.generate_golden_manifest()
        self.assertEqual(
            "GOLDEN_ELIGIBLE",
            completed["golden_manifest"]["golden_status"],
        )
        self.assertEqual(
            "GOLDEN_FROZEN",
            bridge.freeze_output("GOLDEN_MANIFEST")["state"],
        )

    def test_paste_capture_is_not_golden_eligible(self) -> None:
        bridge = self.session()
        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()
        bridge.freeze_output("EXECUTION_HANDOFF")
        self.import_fixture(bridge, "build_receipt_valid.md", "BUILD_RECEIPT")
        self.import_fixture(bridge, "pro_audit_valid.md", "PRO_AUDIT")
        self.import_fixture(
            bridge,
            "reusable_delta_valid.md",
            "REUSABLE_DELTA_RECORD",
            mode="PASTE_CAPTURE",
        )
        manifest = bridge.generate_golden_manifest()["golden_manifest"]
        delta_entry = next(
            entry
            for entry in manifest["artifacts"]
            if entry["artifact_role"] == "REUSABLE_DELTA_RECORD"
        )
        self.assertEqual("GOLDEN_INCOMPLETE", manifest["golden_status"])
        self.assertEqual("MISSING", delta_entry["state"])
        self.assertEqual(
            "PASTE_CAPTURE_NOT_GOLDEN_ELIGIBLE",
            delta_entry["reason"],
        )
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "incomplete Golden manifest",
        ):
            bridge.freeze_output("GOLDEN_MANIFEST")

    def test_exact_file_reimport_promotes_same_bytes_over_paste(self) -> None:
        bridge = self.session()
        payload = fixture_bytes("pro_design_valid.md")
        pasted = bridge.import_artifact(
            selected_role="PRO_DESIGN",
            payload=payload,
            source_path_or_label="pasted-pro-design",
            import_mode="PASTE_CAPTURE",
        )["imports"][-1]
        self.assertTrue(pasted["effective"])

        file_imported = bridge.import_artifact(
            selected_role="PRO_DESIGN",
            payload=payload,
            source_path_or_label="pro_design_valid.md",
            import_mode="BYTE_EXACT_FILE_IMPORT",
        )
        records = file_imported["imports"]
        self.assertFalse(records[-2]["effective"])
        self.assertTrue(records[-1]["effective"])
        self.assertEqual(
            pasted["import_event_id"],
            records[-1]["duplicate_of_import_event_id"],
        )
        self.assertEqual(
            "BYTE_EXACT_FILE_IMPORT",
            records[-1]["import_mode"],
        )

        bridge.generate_execution_handoff()
        bridge.freeze_output("EXECUTION_HANDOFF")
        self.import_fixture(bridge, "build_receipt_valid.md", "BUILD_RECEIPT")
        self.import_fixture(bridge, "pro_audit_valid.md", "PRO_AUDIT")
        self.import_fixture(
            bridge,
            "reusable_delta_valid.md",
            "REUSABLE_DELTA_RECORD",
        )
        manifest = bridge.generate_golden_manifest()["golden_manifest"]
        self.assertEqual("GOLDEN_ELIGIBLE", manifest["golden_status"])

    def test_golden_manifest_retry_recovers_interrupted_projection(self) -> None:
        bridge = self.session()
        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()
        bridge.freeze_output("EXECUTION_HANDOFF")
        self.import_fixture(bridge, "build_receipt_valid.md", "BUILD_RECEIPT")
        self.import_fixture(bridge, "pro_audit_valid.md", "PRO_AUDIT")
        self.import_fixture(
            bridge,
            "reusable_delta_valid.md",
            "REUSABLE_DELTA_RECORD",
        )
        generated = bridge.generate_golden_manifest()
        fixed_identity = generated["outputs"]["GOLDEN_MANIFEST"]["sha256"]
        session_id = generated["session"]["session_id"]

        interrupted = bridge.store.load_session(session_id)
        interrupted["golden_manifest"] = None
        interrupted["state"] = "DELTA_IMPORTED"
        bridge.store.save_session(interrupted)

        recovered = bridge.generate_golden_manifest()
        self.assertEqual(
            fixed_identity,
            recovered["outputs"]["GOLDEN_MANIFEST"]["sha256"],
        )
        self.assertEqual(
            "GOLDEN_ELIGIBLE",
            recovered["golden_manifest"]["golden_status"],
        )
        self.assertEqual("GOLDEN_ELIGIBLE", recovered["state"])
        self.assertEqual(
            "GOLDEN_FROZEN",
            bridge.freeze_output("GOLDEN_MANIFEST")["state"],
        )

    def test_replacement_requires_forward_only_link_and_invalidates_replay(
        self,
    ) -> None:
        bridge = self.frozen_golden_session(
            create_repository(self.root, "frozen-replacement")
        )
        old_effective = next(
            record
            for record in bridge.snapshot()["imports"]
            if record["selected_role"] == "BUILD_RECEIPT"
            and record["effective"]
        )
        replacement = bridge.import_artifact(
            selected_role="BUILD_RECEIPT",
            payload=fixture_bytes("build_receipt_valid.md") + b"\n",
            source_path_or_label="unlinked-build-replacement.md",
            import_mode="BYTE_EXACT_FILE_IMPORT",
        )
        newest = replacement["imports"][-1]
        self.assertEqual(
            "HOLD_SUPERSESSION_REQUIRED",
            newest["validation_state"],
        )
        self.assertFalse(newest["effective"])
        self.assertTrue(
            next(
                record
                for record in replacement["imports"]
                if record["import_event_id"]
                == old_effective["import_event_id"]
            )["effective"]
        )

        baseline, candidate = self.bound_replay_pair(bridge)
        with self.assertRaises(ManualBridgeConflictError):
            bridge.evaluate_replay(baseline, candidate)

    def test_forward_only_correction_replaces_effective_before_golden(
        self,
    ) -> None:
        bridge = self.session()
        first = self.import_fixture(
            bridge,
            "build_receipt_valid.md",
            "BUILD_RECEIPT",
        )["imports"][-1]
        corrected = bridge.import_artifact(
            selected_role="BUILD_RECEIPT",
            payload=fixture_bytes("build_receipt_valid.md") + b"\n",
            source_path_or_label="corrected-build-receipt.md",
            import_mode="BYTE_EXACT_FILE_IMPORT",
            supersedes_import_event_id=first["import_event_id"],
            correction_reason="Fix one external fixation note.",
        )
        latest = corrected["imports"][-1]
        self.assertEqual("VALID", latest["validation_state"])
        self.assertTrue(latest["effective"])
        self.assertEqual(
            first["import_event_id"],
            latest["supersedes_import_event_id"],
        )
        self.assertNotEqual(
            first["artifact_content_hash"],
            latest["artifact_content_hash"],
        )
        self.assertNotEqual(
            "UNKNOWN",
            latest["forward_only_delta_linkage"],
        )

    def test_valid_same_byte_metadata_correction_promotes_without_effective(
        self,
    ) -> None:
        bridge = self.session()
        payload = b"one immutable design payload"
        first = bridge.import_artifact(
            selected_role="PRO_DESIGN",
            payload=payload,
            source_path_or_label="same-byte-design-first",
            import_mode="BYTE_EXACT_FILE_IMPORT",
            metadata=typed_metadata(
                "PRO_DESIGN",
                role_identity=UNKNOWN,
            ),
        )["imports"][-1]
        self.assertEqual(
            "HOLD_MISSING_REQUIRED_FIELDS",
            first["validation_state"],
        )
        self.assertFalse(first["effective"])

        corrected = bridge.import_artifact(
            selected_role="PRO_DESIGN",
            payload=payload,
            source_path_or_label="same-byte-design-corrected-metadata",
            import_mode="BYTE_EXACT_FILE_IMPORT",
            metadata=typed_metadata("PRO_DESIGN"),
        )
        second = corrected["imports"][-1]
        self.assertEqual("VALID", second["validation_state"])
        self.assertTrue(second["effective"])
        self.assertEqual(
            first["import_event_id"],
            second["duplicate_of_import_event_id"],
        )
        bridge.generate_execution_handoff()

    def test_live_replay_is_bound_to_exact_frozen_manifest_and_candidate(
        self,
    ) -> None:
        bridge = self.frozen_golden_session(
            create_repository(self.root, "bound-replay")
        )
        baseline = replay_fixture("replay_candidate_preserved.json")
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "exact frozen Golden manifest",
        ):
            bridge.evaluate_replay(baseline, copy.deepcopy(baseline))

        baseline, candidate = self.bound_replay_pair(bridge)
        candidate["manifest_identity"] = "0" * 64
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "exact frozen Golden manifest",
        ):
            bridge.evaluate_replay(baseline, candidate)

        baseline, candidate = self.bound_replay_pair(bridge)
        evaluated = bridge.evaluate_replay(baseline, candidate)
        replay = json.loads(
            bridge.output_bytes("REPLAY_RESULT").decode("utf-8")
        )
        expected_manifest = bridge.snapshot()["outputs"]["GOLDEN_MANIFEST"][
            "sha256"
        ]
        self.assertEqual(expected_manifest, replay["baseline_manifest"])
        self.assertEqual(expected_manifest, replay["candidate_manifest"])
        self.assertRegex(replay["candidate_output_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual("PASS", evaluated["results"]["replay"]["result"])

    def test_live_replay_rejects_sources_outside_frozen_golden(self) -> None:
        bridge = self.frozen_golden_session(
            create_repository(self.root, "forged-replay-source")
        )
        baseline, candidate = self.bound_replay_pair(bridge)
        candidate["fields"]["objective"]["atoms"][0][
            "source_artifact_hash"
        ] = "f" * 64

        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "outside the frozen Golden set",
        ):
            bridge.evaluate_replay(baseline, candidate)

    def test_live_replay_rejects_caller_substituted_golden_baseline(
        self,
    ) -> None:
        bridge = self.frozen_golden_session(
            create_repository(self.root, "forged-replay-baseline")
        )
        baseline, candidate = self.bound_replay_pair(bridge)
        allowed_hash = next(
            entry["artifact_sha256"]
            for entry in bridge.snapshot()["golden_manifest"]["artifacts"]
            if entry["artifact_role"] == "PRO_DESIGN"
        )
        for field in baseline["fields"].values():
            for atom in field["atoms"]:
                atom["value"] = "FORGED_VALUE_NOT_DERIVED_FROM_GOLDEN"
                atom["source_artifact_hash"] = allowed_hash
                atom["source_location"] = "$.forged"
        candidate = copy.deepcopy(baseline)
        candidate["candidate_id"] = "forged-baseline-candidate"

        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "exactly match the baseline fixed",
        ):
            bridge.evaluate_replay(baseline, candidate)

    def test_live_replay_rejects_extra_and_duplicate_candidate_atoms(
        self,
    ) -> None:
        bridge = self.frozen_golden_session(
            create_repository(self.root, "extra-replay-atoms")
        )
        baseline, candidate = self.bound_replay_pair(bridge)
        extra_atom = copy.deepcopy(
            candidate["fields"]["objective"]["atoms"][0]
        )
        extra_atom["atom_id"] = "OBJ-CONTRADICTORY-EXTRA"
        extra_atom["value"] = "CONTRADICTORY REPLACEMENT OBJECTIVE"
        candidate["fields"]["objective"]["atoms"].append(extra_atom)
        evaluated = bridge.evaluate_replay(baseline, candidate)
        objective = next(
            item
            for item in json.loads(
                bridge.output_bytes("REPLAY_RESULT").decode("utf-8")
            )["field_results"]
            if item["field"] == "objective"
        )
        self.assertEqual("ALTERED", objective["status"])
        self.assertEqual("NOT PASS", evaluated["results"]["replay"]["result"])

        baseline, candidate = self.bound_replay_pair(bridge)
        candidate["fields"]["objective"]["atoms"].append(
            copy.deepcopy(candidate["fields"]["objective"]["atoms"][0])
        )
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "duplicate atom identity",
        ):
            bridge.evaluate_replay(baseline, candidate)

        baseline, candidate = self.bound_replay_pair(bridge)
        candidate["fields"]["objective"]["atoms"].append(
            {
                "source_artifact_hash": candidate["fields"]["objective"][
                    "atoms"
                ][0]["source_artifact_hash"],
                "source_location": "$.objective",
                "value": "MALFORMED EXTRA WITHOUT AN ATOM ID",
            }
        )
        with self.assertRaisesRegex(
            ManualBridgeConflictError,
            "invalid or duplicate atom identity",
        ):
            bridge.evaluate_replay(baseline, candidate)

    def test_idempotent_generation_preserves_advanced_state_and_copy_events(
        self,
    ) -> None:
        bridge = self.session()
        bridge.copy_for_pro()
        bridge.copy_for_pro()
        transfer_events = [
            event
            for event in bridge.store.read_events()
            if event["kind"] == "COPY_FOR_PRO_TRANSFERRED"
        ]
        burden = bridge.snapshot()["burden"]
        self.assertEqual(2, len(transfer_events))
        self.assertEqual(
            2,
            burden["shin_copy_paste_count"]["value_or_unknown"],
        )
        self.assertEqual(
            2,
            len(
                set(
                    burden["shin_copy_paste_count"]["source_event_ids"]
                )
            ),
        )

        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()
        bridge.freeze_output("EXECUTION_HANDOFF")
        self.import_fixture(bridge, "build_receipt_valid.md", "BUILD_RECEIPT")
        advanced_state = bridge.snapshot()["state"]
        bridge.generate_execution_handoff()
        self.assertEqual(advanced_state, bridge.snapshot()["state"])

        self.import_fixture(bridge, "pro_audit_valid.md", "PRO_AUDIT")
        self.import_fixture(
            bridge,
            "reusable_delta_valid.md",
            "REUSABLE_DELTA_RECORD",
        )
        bridge.generate_golden_manifest()
        bridge.freeze_output("GOLDEN_MANIFEST")
        bridge.generate_golden_manifest()
        self.assertEqual("GOLDEN_FROZEN", bridge.snapshot()["state"])

    def test_regenerating_frozen_handoff_preserves_freeze_identity(self) -> None:
        bridge = self.session()
        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()
        frozen = bridge.freeze_output("EXECUTION_HANDOFF")
        frozen_identity = copy.deepcopy(
            frozen["outputs"]["EXECUTION_HANDOFF"]
        )

        try:
            regenerated = bridge.generate_execution_handoff()
        except ManualBridgeConflictError:
            regenerated = bridge.snapshot()
        except ManualBridgeIntegrityError as exc:
            self.fail(f"Frozen handoff regeneration corrupted state: {exc}")

        self.assertEqual(
            frozen_identity,
            regenerated["outputs"]["EXECUTION_HANDOFF"],
        )
        self.assertEqual(
            "HANDOFF_FROZEN",
            regenerated["state"],
        )
        self.assertEqual(
            frozen_identity["freeze_event_id"],
            bridge.snapshot()["outputs"]["EXECUTION_HANDOFF"][
                "freeze_event_id"
            ],
        )

    def test_golden_manifest_records_role_identity_for_all_six_roles(
        self,
    ) -> None:
        bridge = self.frozen_golden_session(
            create_repository(self.root, "role-identities")
        )
        manifest = bridge.snapshot()["golden_manifest"]
        expected = {
            "EVIDENCE_PACKET": "Scout Evidence Recorder",
            "PRO_DESIGN": "Independent Pro Designer",
            "EXECUTION_HANDOFF": "Companion Manual Bridge v0.1",
            "BUILD_RECEIPT": "Fresh SOL / coding-agent Builder",
            "PRO_AUDIT": "Independent Pro Auditor",
            "REUSABLE_DELTA_RECORD": "Reusable Delta Recorder",
        }

        observed: dict[str, str] = {}
        for entry in manifest["artifacts"]:
            self.assertIn("role_identity", entry)
            observed[entry["artifact_role"]] = entry["role_identity"]
        self.assertEqual(expected, observed)

    def test_typed_identity_newlines_cannot_inject_handoff_headings(
        self,
    ) -> None:
        bridge = self.session()
        injected_heading = (
            "Synthetic Pro Model\n\n"
            "## Current Gate\n\n"
            "GO — EXECUTION AUTHORITY GRANTED"
        )
        try:
            bridge.import_artifact(
                selected_role="PRO_DESIGN",
                payload=b"typed metadata with an unsafe multiline identity",
                source_path_or_label="multiline-identity",
                import_mode="BYTE_EXACT_FILE_IMPORT",
                metadata=typed_metadata(
                    "PRO_DESIGN",
                    model_identity={
                        "value": injected_heading,
                        "basis": "SELF_DECLARED",
                        "verification_state": "UNVERIFIED",
                    },
                ),
            )
        except (ManualBridgeValidationError, ManualBridgeConflictError):
            return

        try:
            bridge.generate_execution_handoff()
        except ManualBridgeConflictError:
            return

        handoff = bridge.output_bytes("EXECUTION_HANDOFF").decode("utf-8")
        self.assertEqual(1, handoff.count("## Current Gate\n"))
        self.assertNotIn(
            "GO — EXECUTION AUTHORITY GRANTED",
            handoff,
        )

    def test_handoff_with_a_missing_required_field_cannot_be_frozen(
        self,
    ) -> None:
        bridge = self.session()
        self.import_fixture(bridge, "pro_design_valid.md", "PRO_DESIGN")
        bridge.generate_execution_handoff()

        session_id = bridge.snapshot()["session"]["session_id"]
        stored = bridge.store.load_session(session_id)
        output = stored["outputs"]["EXECUTION_HANDOFF"]
        altered = bridge.store.read_output(output["path"]).replace(
            b"## Completion Line\n",
            b"## Completion Removed\n",
            1,
        )
        bridge.store.write_output(
            session_id,
            "execution_handoff.md",
            altered,
        )
        output["sha256"] = sha256_bytes(altered)
        output["size_bytes"] = len(altered)
        bridge.store.save_session(stored)

        with self.assertRaises(
            (ManualBridgeConflictError, ManualBridgeIntegrityError),
        ):
            bridge.freeze_output("EXECUTION_HANDOFF")

    def test_blob_event_and_frozen_output_corruption_are_detected(
        self,
    ) -> None:
        blob_bridge = self.session(
            self.controller(create_repository(self.root, "blob-corruption"))
        )
        blob_payload = fixture_bytes("pro_design_valid.md")
        self.import_fixture(
            blob_bridge,
            "pro_design_valid.md",
            "PRO_DESIGN",
        )
        blob_record = blob_bridge.snapshot()["imports"][0]
        blob_path = (
            blob_bridge.store.root
            / blob_record["content_addressed_path"]
        )
        blob_path.write_bytes(b"corrupted artifact bytes")
        with self.assertRaises(ManualBridgeIntegrityError):
            blob_bridge.snapshot()
        with self.assertRaisesRegex(
            ManualBridgeIntegrityError,
            "Content-addressed Bridge state is corrupted",
        ):
            blob_bridge.store.store_blob(blob_payload)

        event_bridge = self.session(
            self.controller(create_repository(self.root, "event-corruption"))
        )
        original_events = event_bridge.store.events_path.read_bytes()
        altered_events = original_events.replace(
            b"BRIDGE_SESSION_CREATED",
            b"BRIDGE_SESSION_TAMPERED",
            1,
        )
        self.assertNotEqual(original_events, altered_events)
        event_bridge.store.events_path.write_bytes(altered_events)
        with self.assertRaisesRegex(
            ManualBridgeIntegrityError,
            "event chain verification failed",
        ):
            event_bridge.snapshot()

        output_bridge = self.session(
            self.controller(create_repository(self.root, "output-corruption"))
        )
        self.import_fixture(
            output_bridge,
            "pro_design_valid.md",
            "PRO_DESIGN",
        )
        output_bridge.generate_execution_handoff()
        output_bridge.freeze_output("EXECUTION_HANDOFF")
        output_identity = output_bridge.snapshot()["outputs"][
            "EXECUTION_HANDOFF"
        ]
        output_path = output_bridge.store.root / output_identity["path"]
        output_path.write_bytes(b"tampered frozen output\n")
        with self.assertRaisesRegex(
            ManualBridgeIntegrityError,
            "output was altered",
        ):
            output_bridge.snapshot()

    def test_store_root_symlink_replacement_is_rejected(self) -> None:
        bridge = self.session(
            self.controller(create_repository(self.root, "root-symlink"))
        )
        original_root = bridge.store.root
        displaced_root = original_root.parent / "v0.1-displaced"
        original_root.rename(displaced_root)
        original_root.symlink_to(displaced_root, target_is_directory=True)

        with self.assertRaisesRegex(
            ManualBridgeIntegrityError,
            "symlink",
        ):
            bridge.snapshot()

    def test_structural_replay_covers_all_fields_statuses_and_no_prose_shortcut(
        self,
    ) -> None:
        baseline = replay_fixture("replay_candidate_preserved.json")
        baseline["fields"]["human_execution_cost"]["atoms"][0][
            "value"
        ] = "42 minutes / FIXTURE"

        preserved = BridgeSessionController.compare_replay(
            baseline,
            copy.deepcopy(baseline),
        )
        self.assertEqual(15, len(preserved["field_results"]))
        self.assertEqual(
            set(REPLAY_FIELDS),
            {item["field"] for item in preserved["field_results"]},
        )
        self.assertTrue(
            all(
                item["status"] == "PRESERVED"
                for item in preserved["field_results"]
            )
        )
        self.assertEqual("PASS", preserved["overall_replay_result"])
        self.assertTrue(all(preserved["non_implication"].values()))

        field_loss = replay_fixture("replay_candidate_field_loss.json")
        field_loss["fields"]["human_execution_cost"]["atoms"][0][
            "value"
        ] = "42 minutes / FIXTURE"
        field_loss_result = BridgeSessionController.compare_replay(
            baseline,
            field_loss,
        )

        authority_inflated = replay_fixture(
            "replay_candidate_authority_inflated.json"
        )
        authority_inflated["fields"]["human_execution_cost"]["atoms"][0][
            "value"
        ] = "42 minutes / FIXTURE"
        authority_result = BridgeSessionController.compare_replay(
            baseline,
            authority_inflated,
        )

        altered = copy.deepcopy(baseline)
        altered["fields"]["objective"]["atoms"][0]["value"] = (
            "A structurally different objective."
        )
        altered_result = BridgeSessionController.compare_replay(
            baseline,
            altered,
        )

        substituted = copy.deepcopy(baseline)
        substituted["fields"]["role_identity"]["atoms"][0][
            "source_artifact_hash"
        ] = "f" * 64
        substituted_result = BridgeSessionController.compare_replay(
            baseline,
            substituted,
        )

        not_applicable_baseline = copy.deepcopy(baseline)
        not_applicable_candidate = copy.deepcopy(baseline)
        not_applicable = {
            "atoms": [],
            "reason": "No reusable delta applies to this replay.",
            "state": "NOT APPLICABLE",
        }
        not_applicable_baseline["fields"]["reusable_delta"] = copy.deepcopy(
            not_applicable
        )
        not_applicable_candidate["fields"]["reusable_delta"] = copy.deepcopy(
            not_applicable
        )
        not_applicable_result = BridgeSessionController.compare_replay(
            not_applicable_baseline,
            not_applicable_candidate,
        )

        unknown_baseline = copy.deepcopy(baseline)
        unknown_candidate = copy.deepcopy(baseline)
        explicit_unknown = {
            "atoms": [
                {
                    "atom_id": "FIND-UNKNOWN",
                    "source_artifact_hash": "0" * 64,
                    "source_location": "$.findings",
                    "value": "UNKNOWN",
                }
            ],
            "state": "UNKNOWN",
        }
        unknown_baseline["fields"]["findings"] = copy.deepcopy(
            explicit_unknown
        )
        unknown_candidate["fields"]["findings"] = copy.deepcopy(
            explicit_unknown
        )
        unknown_result = BridgeSessionController.compare_replay(
            unknown_baseline,
            unknown_candidate,
        )

        prose_only = copy.deepcopy(baseline)
        prose_only["fields"]["objective"] = {
            "prose": baseline["fields"]["objective"]["atoms"][0]["value"]
        }
        prose_result = BridgeSessionController.compare_replay(
            baseline,
            prose_only,
        )

        result_sets = (
            preserved,
            field_loss_result,
            authority_result,
            altered_result,
            substituted_result,
            not_applicable_result,
            unknown_result,
            prose_result,
        )
        statuses = {
            item["status"]
            for result in result_sets
            for item in result["field_results"]
        }
        self.assertTrue(set(REPLAY_STATUSES).issubset(statuses))

        def status(result: Mapping[str, object], field: str) -> str:
            return next(
                item["status"]
                for item in result["field_results"]
                if item["field"] == field
            )

        self.assertEqual(
            "MISSING",
            status(field_loss_result, "completion_line"),
        )
        self.assertEqual(
            "AUTHORITY-INFLATED",
            status(authority_result, "authority_boundary"),
        )
        self.assertEqual("ALTERED", status(altered_result, "objective"))
        self.assertEqual(
            "SUBSTITUTED",
            status(substituted_result, "role_identity"),
        )
        self.assertEqual(
            "NOT APPLICABLE",
            status(not_applicable_result, "reusable_delta"),
        )
        self.assertEqual("UNKNOWN", status(unknown_result, "findings"))
        self.assertEqual("MISSING", status(prose_result, "objective"))

        bridge = self.frozen_golden_session(
            create_repository(self.root, "live-replay")
        )
        baseline, replay_candidate = self.bound_replay_pair(bridge)
        initial_results = copy.deepcopy(bridge.snapshot()["results"])
        evaluated = bridge.evaluate_replay(
            baseline,
            replay_candidate,
        )
        self.assertEqual(
            initial_results["protocol"],
            evaluated["results"]["protocol"],
        )
        self.assertEqual(
            initial_results["product"],
            evaluated["results"]["product"],
        )
        self.assertEqual("PASS", evaluated["results"]["replay"]["result"])
        self.assertEqual("REPLAY_RECORDED", evaluated["state"])
        self.assertIn("REPLAY_RESULT", evaluated["outputs"])
        self.assertEqual(
            0,
            evaluated["burden"][
                "fields_lost_or_altered_during_transfer"
            ]["value_or_unknown"],
        )

    def test_framework_and_burden_metadata_remain_explicit(
        self,
    ) -> None:
        bridge = self.session()
        initial = bridge.snapshot()
        boundary = initial["session"]["boundary"]
        self.assertEqual(
            {
                "framework_lens_used": "Artifact provenance",
                "relevant_decision_os_layer": "V13 / Stage 2",
                "reinterpretation_question": (
                    "Which identity survives transfer?"
                ),
                "framework_derived_finding": (
                    "Authority must remain independently visible."
                ),
            },
            {
                key: boundary[key]
                for key in (
                    "framework_lens_used",
                    "relevant_decision_os_layer",
                    "reinterpretation_question",
                    "framework_derived_finding",
                )
            },
        )
        count_observation = initial["burden"]["shin_re_explanation_count"]
        self.assertEqual(0, count_observation["value_or_unknown"])
        self.assertEqual(PRE_BRIDGE_UNKNOWN, count_observation["notes"])
        time_observation = initial["burden"]["human_handling_time"]
        self.assertEqual("UNKNOWN", time_observation["value_or_unknown"])
        self.assertEqual(PRE_BRIDGE_UNKNOWN, time_observation["basis"])
        self.assertEqual("UNKNOWN", time_observation["confidence"])

        results_before_import = copy.deepcopy(initial["results"])
        bridge.import_artifact(
            selected_role="PRO_DESIGN",
            payload=fixture_bytes("pro_design_valid.md"),
            source_path_or_label="pro_design_valid.md",
            import_mode="BYTE_EXACT_FILE_IMPORT",
            metadata={"framework_lens_used": "Artifact provenance"},
        )
        imported = bridge.snapshot()
        self.assertEqual(
            "Artifact provenance",
            imported["imports"][0]["framework_lens_used"],
        )
        self.assertEqual(results_before_import, imported["results"])

        incremented = bridge.record_observation(
            field="shin_re_explanation_count",
            value=1,
            unit="count",
            method="EXPLICIT_ONE_CLICK_INCREMENT",
            notes="One explicit re-explanation.",
        )
        re_explanation = incremented["burden"]["shin_re_explanation_count"]
        self.assertEqual(1, re_explanation["value_or_unknown"])
        self.assertEqual("USER_ENTERED", re_explanation["basis"])
        self.assertEqual("USER_ATTESTED", re_explanation["confidence"])
        self.assertEqual(
            "EXPLICIT_ONE_CLICK_INCREMENT",
            re_explanation["method"],
        )
        self.assertEqual(1, len(re_explanation["source_event_ids"]))

        timed = bridge.record_observation(
            field="human_handling_time",
            value=12.5,
            unit="seconds",
            method="MANUAL_TIMER",
            notes="Measured by the human operator.",
        )
        handling = timed["burden"]["human_handling_time"]
        self.assertEqual(12.5, handling["value_or_unknown"])
        self.assertEqual("MANUAL_TIMER", handling["method"])
        self.assertEqual("USER_ENTERED", handling["basis"])
        self.assertEqual("USER_ATTESTED", handling["confidence"])

        with self.assertRaisesRegex(
            ManualBridgeValidationError,
            "cannot be negative",
        ):
            bridge.record_observation(
                field="human_handling_time",
                value=-1,
                unit="seconds",
                method="MANUAL_TIMER",
            )
        with self.assertRaisesRegex(
            ManualBridgeValidationError,
            "unsupported",
        ):
            bridge.record_observation(
                field="unsupported_metric",
                value=1,
                unit="count",
                method="MANUAL",
            )


if __name__ == "__main__":
    unittest.main()
