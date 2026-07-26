from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from decision_os.audit_link import (
    CLAIMS_NOT_MADE,
    EXIT_LINKED,
    EXIT_NOT_LINKED,
    IDENTITY_FIELDS,
    RESULT_INVALID,
    RESULT_LINKED,
    RESULT_MISMATCH,
    RESULT_SCHEMA_VERSION,
    normalize_identity,
    validate_audit_link_files,
)
from decision_os.audit_delivery import MAX_INPUT_BYTES as AUDIT_MAX_INPUT_BYTES
from decision_os.intake import MAX_INPUT_BYTES as INTAKE_MAX_INPUT_BYTES
from tests.test_decision_os_checks import tree_digest


REPO_ROOT = Path(__file__).resolve().parents[1]
INTAKE_EXAMPLE = REPO_ROOT / "examples" / "workflow_incident_intake_v0_1.json"
AUDIT_EXAMPLE = (
    REPO_ROOT
    / "examples"
    / "ai_application_workflow_audit_delivery_v0_1.md"
)

AUDIT_LABELS = {
    "workflow": "Application or Workflow",
    "bounded_path": "Bounded Workflow Path",
    "trigger": "Trigger",
    "expected_state": "Expected State",
    "observed_state": "Observed State",
    "restart_or_fallback_path": "Current Restart or Fallback Path",
}


def example_packet() -> dict[str, object]:
    packet = json.loads(INTAKE_EXAMPLE.read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise AssertionError("expected object example")
    return packet


def example_audit() -> str:
    return AUDIT_EXAMPLE.read_text(encoding="utf-8")


def write_packet(directory: Path, packet: dict[str, object]) -> Path:
    path = directory / "accepted-intake.json"
    path.write_text(
        json.dumps(packet, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def write_audit(directory: Path, content: str) -> Path:
    path = directory / "delivery.md"
    path.write_text(content, encoding="utf-8")
    return path


def write_pair(directory: Path) -> tuple[Path, Path]:
    return (
        write_packet(directory, example_packet()),
        write_audit(directory, example_audit()),
    )


def replace_audit_field(content: str, field: str, value: str) -> str:
    label = AUDIT_LABELS[field]
    prefix = f"{label}: "
    lines = content.splitlines()
    matches = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    if len(matches) != 1:
        raise AssertionError(f"expected one {label!r} field")
    lines[matches[0]] = f"{label}: {value}"
    return "\n".join(lines) + "\n"


class AuditCaseLinkValidationTest(unittest.TestCase):
    def test_example_pair_is_linked_deterministic_read_only_and_no_echo(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = example_packet()
            packet["workflow"] = "SECRET SHARED IDENTITY"
            intake = write_packet(root, packet)
            audit = write_audit(
                root,
                replace_audit_field(
                    example_audit(),
                    "workflow",
                    "SECRET SHARED IDENTITY",
                ),
            )
            before = tree_digest(root)

            first, first_exit = validate_audit_link_files(intake, audit)
            second, second_exit = validate_audit_link_files(intake, audit)

            self.assertEqual(EXIT_LINKED, first_exit)
            self.assertEqual(first_exit, second_exit)
            self.assertEqual(first, second)
            self.assertEqual(RESULT_LINKED, first["result"])
            self.assertEqual(RESULT_SCHEMA_VERSION, first["schema_version"])
            self.assertEqual("audit-link", first["command"])
            self.assertEqual(list(IDENTITY_FIELDS), first["matched_fields"])
            self.assertEqual([], first["mismatched_fields"])
            self.assertEqual([], first["missing_fields"])
            self.assertEqual([], first["unknowns"])
            self.assertEqual(list(CLAIMS_NOT_MADE), first["claims_not_made"])
            self.assertEqual(
                {
                    "intake": {
                        "name": "accepted-intake.json",
                        "content_echoed": False,
                    },
                    "audit": {
                        "name": "delivery.md",
                        "content_echoed": False,
                    },
                },
                first["inputs"],
            )
            self.assertNotIn("SECRET SHARED IDENTITY", json.dumps(first))
            self.assertEqual(before, tree_digest(root))

    def test_each_identity_field_mismatch_is_reported_in_fixed_order(
        self,
    ) -> None:
        for field in IDENTITY_FIELDS:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    packet = example_packet()
                    packet[field] = f"{packet[field]} changed"
                    intake = write_packet(root, packet)
                    audit = write_audit(root, example_audit())

                    payload, exit_code = validate_audit_link_files(
                        intake,
                        audit,
                    )

                    self.assertEqual(EXIT_NOT_LINKED, exit_code)
                    self.assertEqual(RESULT_MISMATCH, payload["result"])
                    self.assertEqual([field], payload["mismatched_fields"])
                    self.assertEqual(
                        [
                            candidate
                            for candidate in IDENTITY_FIELDS
                            if candidate != field
                        ],
                        payload["matched_fields"],
                    )

    def test_multiple_mismatches_remain_deterministically_ordered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = example_packet()
            changed = (
                "bounded_path",
                "observed_state",
                "restart_or_fallback_path",
            )
            for field in changed:
                packet[field] = f"{packet[field]} changed"

            payload, exit_code = validate_audit_link_files(
                write_packet(root, packet),
                write_audit(root, example_audit()),
            )

            self.assertEqual(EXIT_NOT_LINKED, exit_code)
            self.assertEqual(RESULT_MISMATCH, payload["result"])
            self.assertEqual(list(changed), payload["mismatched_fields"])

    def test_bounded_whitespace_normalization_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = example_packet()
            packet["workflow"] = (
                " \tCustomer-support\r\napproval\n\tworkflow \t"
            )
            packet["bounded_path"] = (
                "draft response  ->\thuman approval\r-> send decision"
            )
            audit_content = replace_audit_field(
                example_audit(),
                "workflow",
                "\tCustomer-support   approval workflow\t",
            )

            payload, exit_code = validate_audit_link_files(
                write_packet(root, packet),
                write_audit(root, audit_content),
            )

            self.assertEqual(EXIT_LINKED, exit_code)
            self.assertEqual(RESULT_LINKED, payload["result"])
            self.assertEqual(
                "one two three",
                normalize_identity(" \tone\r\ntwo\n  three\t "),
            )

    def test_case_and_punctuation_differences_remain_mismatches(self) -> None:
        cases = (
            ("workflow", "customer-support approval workflow"),
            (
                "trigger",
                "The workflow resumed after an interrupted approval step!",
            ),
        )
        for field, replacement in cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    packet = example_packet()
                    packet[field] = replacement
                    payload, exit_code = validate_audit_link_files(
                        write_packet(root, packet),
                        write_audit(root, example_audit()),
                    )

                    self.assertEqual(EXIT_NOT_LINKED, exit_code)
                    self.assertEqual(RESULT_MISMATCH, payload["result"])
                    self.assertEqual([field], payload["mismatched_fields"])

    def test_missing_intake_identity_field_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = example_packet()
            del packet["expected_state"]

            payload, exit_code = validate_audit_link_files(
                write_packet(root, packet),
                write_audit(root, example_audit()),
            )

            self.assertEqual(EXIT_NOT_LINKED, exit_code)
            self.assertEqual(RESULT_INVALID, payload["result"])
            self.assertEqual(["expected_state"], payload["missing_fields"])
            self.assertEqual(["intake_structure"], payload["unknowns"])
            self.assertEqual([], payload["matched_fields"])
            self.assertEqual([], payload["mismatched_fields"])

    def test_missing_audit_identity_field_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = example_audit().replace(
                "Expected State: The approved draft remained current and "
                "ready for the send decision.\n",
                "",
                1,
            )

            payload, exit_code = validate_audit_link_files(
                write_packet(root, example_packet()),
                write_audit(root, missing),
            )

            self.assertEqual(EXIT_NOT_LINKED, exit_code)
            self.assertEqual(RESULT_INVALID, payload["result"])
            self.assertEqual(["expected_state"], payload["missing_fields"])
            self.assertEqual(["audit_structure"], payload["unknowns"])

    def test_malformed_intake_and_invalid_audit_are_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            malformed = root / "malformed.json"
            malformed.write_text('{"workflow":', encoding="utf-8")
            invalid_audit = write_audit(
                root,
                example_audit() + "\n```text\nunclosed\n",
            )

            payload, exit_code = validate_audit_link_files(
                malformed,
                invalid_audit,
            )

            self.assertEqual(EXIT_NOT_LINKED, exit_code)
            self.assertEqual(RESULT_INVALID, payload["result"])
            self.assertEqual(
                ["intake_structure", "audit_structure"],
                payload["unknowns"],
            )
            self.assertEqual([], payload["matched_fields"])

    def test_field_like_text_inside_fences_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = example_audit().replace(
                "## Scope\n",
                (
                    "## Scope\n\n"
                    "```text\n"
                    "Application or Workflow: SECRET FENCED VALUE\n"
                    "Bounded Workflow Path: SECRET FENCED VALUE\n"
                    "```\n"
                ),
                1,
            )

            payload, exit_code = validate_audit_link_files(
                write_packet(root, example_packet()),
                write_audit(root, content),
            )

            self.assertEqual(EXIT_LINKED, exit_code)
            self.assertEqual(RESULT_LINKED, payload["result"])
            self.assertNotIn("SECRET FENCED VALUE", json.dumps(payload))

    def test_unicode_line_separators_are_not_emitted_in_basenames(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            unsafe_intake = root / "intake\u2028forged.json"
            unsafe_audit = root / "audit\u2029forged.md"
            unsafe_intake.write_bytes(intake.read_bytes())
            unsafe_audit.write_bytes(audit.read_bytes())

            intake_payload, intake_exit = validate_audit_link_files(
                unsafe_intake,
                audit,
            )
            audit_payload, audit_exit = validate_audit_link_files(
                intake,
                unsafe_audit,
            )

            self.assertEqual(EXIT_LINKED, intake_exit)
            self.assertEqual(EXIT_LINKED, audit_exit)
            self.assertEqual(
                "unavailable",
                intake_payload["inputs"]["intake"]["name"],
            )
            self.assertEqual(
                "unavailable",
                audit_payload["inputs"]["audit"]["name"],
            )
            serialized = json.dumps(
                (intake_payload, audit_payload),
                ensure_ascii=False,
            )
            self.assertNotIn("\u2028", serialized)
            self.assertNotIn("\u2029", serialized)

    def test_symlinks_are_rejected_for_each_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            intake_link = root / "intake-link.json"
            audit_link = root / "audit-link.md"
            intake_link.symlink_to(intake)
            audit_link.symlink_to(audit)

            cases = (
                (intake_link, audit, ["intake_structure"]),
                (intake, audit_link, ["audit_structure"]),
            )
            for supplied_intake, supplied_audit, unknowns in cases:
                with self.subTest(unknowns=unknowns):
                    payload, exit_code = validate_audit_link_files(
                        supplied_intake,
                        supplied_audit,
                    )
                    self.assertEqual(EXIT_NOT_LINKED, exit_code)
                    self.assertEqual(RESULT_INVALID, payload["result"])
                    self.assertEqual(unknowns, payload["unknowns"])

    def test_directories_are_rejected_for_each_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            cases = (
                (root, audit, ["intake_structure"]),
                (intake, root, ["audit_structure"]),
            )
            for supplied_intake, supplied_audit, unknowns in cases:
                with self.subTest(unknowns=unknowns):
                    payload, exit_code = validate_audit_link_files(
                        supplied_intake,
                        supplied_audit,
                    )
                    self.assertEqual(EXIT_NOT_LINKED, exit_code)
                    self.assertEqual(RESULT_INVALID, payload["result"])
                    self.assertEqual(unknowns, payload["unknowns"])

    def test_oversized_inputs_are_rejected_at_each_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            oversized_intake = root / "oversized.json"
            oversized_intake.write_bytes(b" " * (INTAKE_MAX_INPUT_BYTES + 1))
            oversized_audit = root / "oversized.md"
            oversized_audit.write_bytes(b" " * (AUDIT_MAX_INPUT_BYTES + 1))
            cases = (
                (oversized_intake, audit, ["intake_structure"]),
                (intake, oversized_audit, ["audit_structure"]),
            )
            for supplied_intake, supplied_audit, unknowns in cases:
                with self.subTest(unknowns=unknowns):
                    payload, exit_code = validate_audit_link_files(
                        supplied_intake,
                        supplied_audit,
                    )
                    self.assertEqual(EXIT_NOT_LINKED, exit_code)
                    self.assertEqual(unknowns, payload["unknowns"])

    def test_invalid_utf8_is_rejected_for_each_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            invalid_intake = root / "invalid.json"
            invalid_intake.write_bytes(b"\xff")
            invalid_audit = root / "invalid.md"
            invalid_audit.write_bytes(b"\xff")
            cases = (
                (invalid_intake, audit, ["intake_structure"]),
                (intake, invalid_audit, ["audit_structure"]),
            )
            for supplied_intake, supplied_audit, unknowns in cases:
                with self.subTest(unknowns=unknowns):
                    payload, exit_code = validate_audit_link_files(
                        supplied_intake,
                        supplied_audit,
                    )
                    self.assertEqual(EXIT_NOT_LINKED, exit_code)
                    self.assertEqual(RESULT_INVALID, payload["result"])
                    self.assertEqual(unknowns, payload["unknowns"])


if __name__ == "__main__":
    unittest.main()
