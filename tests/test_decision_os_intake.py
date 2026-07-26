from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from decision_os.intake import (
    EXIT_INCOMPLETE,
    EXIT_READY,
    INPUT_SCHEMA_VERSION,
    MAX_INPUT_BYTES,
    RESULT_INCOMPLETE,
    RESULT_INVALID,
    RESULT_READY,
    validate_intake_file,
)


def ready_packet() -> dict[str, object]:
    return {
        "schema_version": INPUT_SCHEMA_VERSION,
        "workflow": "Approval workflow",
        "bounded_path": "draft -> approval -> send decision",
        "incident_as_of": "2026-07-26",
        "trigger": "Resume after an interrupted approval.",
        "expected_state": "The approved draft remains current.",
        "observed_state": "The resumed run cannot identify the draft.",
        "human_recovery_work": ["Revalidated the draft."],
        "restart_or_fallback_path": "Stop before send and re-establish identity.",
        "materials_available": ["Sanitized event timeline."],
        "prohibited_materials": [],
    }


def write_packet(directory: Path, packet: object) -> Path:
    path = directory / "packet.json"
    path.write_text(
        json.dumps(packet, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


class WorkflowIntakeValidationTest(unittest.TestCase):
    def test_ready_packet_is_deterministic_and_does_not_echo_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = ready_packet()
            packet["workflow"] = "SECRET WORKFLOW VALUE"
            path = write_packet(root, packet)
            before = path.read_bytes()

            first, first_exit = validate_intake_file(path)
            second, second_exit = validate_intake_file(path)

            self.assertEqual(EXIT_READY, first_exit)
            self.assertEqual(first_exit, second_exit)
            self.assertEqual(first, second)
            self.assertEqual(RESULT_READY, first["result"])
            self.assertEqual([], first["missing_required_fields"])
            self.assertEqual([], first["invalid_fields"])
            self.assertFalse(first["input"]["content_echoed"])
            self.assertEqual("packet.json", first["input"]["name"])
            self.assertNotIn("SECRET WORKFLOW VALUE", json.dumps(first))
            self.assertEqual(before, path.read_bytes())

    def test_missing_required_field_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = ready_packet()
            del packet["observed_state"]
            path = write_packet(root, packet)

            payload, exit_code = validate_intake_file(path)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)
            self.assertEqual(RESULT_INCOMPLETE, payload["result"])
            self.assertEqual(
                ["observed_state"],
                payload["missing_required_fields"],
            )
            self.assertEqual([], payload["invalid_fields"])

    def test_empty_required_lists_are_invalid_but_empty_prohibited_is_valid(
        self,
    ) -> None:
        for field in ("human_recovery_work", "materials_available"):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    packet = ready_packet()
                    packet[field] = []
                    path = write_packet(root, packet)

                    payload, exit_code = validate_intake_file(path)

                    self.assertEqual(EXIT_INCOMPLETE, exit_code)
                    self.assertEqual(RESULT_INCOMPLETE, payload["result"])
                    self.assertEqual([field], payload["invalid_fields"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload, exit_code = validate_intake_file(
                write_packet(root, ready_packet())
            )
            self.assertEqual(EXIT_READY, exit_code)
            self.assertIn(
                "prohibited_materials",
                payload["observed_fields"],
            )

    def test_optional_fields_and_unknowns_are_structural_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = ready_packet()
            packet.update(
                {
                    "next_actor": "PRIVATE PERSON",
                    "next_safe_action": "PRIVATE ACTION",
                    "unknowns": ["PRIVATE UNKNOWN"],
                }
            )
            path = write_packet(root, packet)

            payload, exit_code = validate_intake_file(path)
            encoded = json.dumps(payload)

            self.assertEqual(EXIT_READY, exit_code)
            self.assertEqual(["input_unknowns_present"], payload["unknowns"])
            self.assertIn("next_actor", payload["observed_fields"])
            self.assertIn("next_safe_action", payload["observed_fields"])
            self.assertIn("unknowns", payload["observed_fields"])
            self.assertNotIn("PRIVATE PERSON", encoded)
            self.assertNotIn("PRIVATE ACTION", encoded)
            self.assertNotIn("PRIVATE UNKNOWN", encoded)

    def test_malformed_unsupported_and_non_object_json_are_rejected(self) -> None:
        cases = (
            b'{"schema_version":',
            b'{"value":NaN}',
            b'{"value":1,"value":2}',
            b"[]",
        )
        for content in cases:
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "packet.json"
                    path.write_bytes(content)

                    payload, exit_code = validate_intake_file(path)

                    self.assertEqual(EXIT_INCOMPLETE, exit_code)
                    self.assertEqual(RESULT_INVALID, payload["result"])
                    self.assertEqual([], payload["observed_fields"])

    def test_unsupported_schema_and_extra_field_are_incomplete(self) -> None:
        cases = (
            ("schema_version", "unsupported"),
            ("private_extra_field", "SECRET"),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    packet = ready_packet()
                    packet[field] = value
                    path = write_packet(root, packet)

                    payload, exit_code = validate_intake_file(path)

                    self.assertEqual(EXIT_INCOMPLETE, exit_code)
                    self.assertEqual(RESULT_INCOMPLETE, payload["result"])
                    expected = (
                        ["schema_version"]
                        if field == "schema_version"
                        else ["unsupported_fields"]
                    )
                    self.assertEqual(expected, payload["invalid_fields"])
                    self.assertNotIn("SECRET", json.dumps(payload))

    def test_oversized_invalid_utf8_directory_and_missing_file_are_invalid(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            oversized = root / "oversized.json"
            oversized.write_bytes(b"x" * (MAX_INPUT_BYTES + 1))
            invalid_utf8 = root / "invalid.json"
            invalid_utf8.write_bytes(b"\xff")
            missing = root / "missing.json"

            for path in (oversized, invalid_utf8, root, missing):
                with self.subTest(path=path.name):
                    payload, exit_code = validate_intake_file(path)
                    self.assertEqual(EXIT_INCOMPLETE, exit_code)
                    self.assertEqual(RESULT_INVALID, payload["result"])
                    self.assertFalse(payload["input"]["content_echoed"])
                    self.assertNotIn(str(root), json.dumps(payload))

    def test_exact_size_limit_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = ready_packet()
            packet["workflow"] = "x"
            content = json.dumps(packet, ensure_ascii=False).encode("utf-8")
            packet["workflow"] = "x" * (1 + MAX_INPUT_BYTES - len(content))
            content = json.dumps(packet, ensure_ascii=False).encode("utf-8")
            self.assertEqual(MAX_INPUT_BYTES, len(content))
            path = root / "packet.json"
            path.write_bytes(content)

            payload, exit_code = validate_intake_file(path)

            self.assertEqual(EXIT_READY, exit_code)
            self.assertEqual(RESULT_READY, payload["result"])

    def test_fifo_is_rejected_before_open(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.fifo"
            os.mkfifo(path)

            with patch(
                "decision_os.intake.os.open",
                side_effect=AssertionError("non-regular input was opened"),
            ):
                payload, exit_code = validate_intake_file(path)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)
            self.assertEqual(RESULT_INVALID, payload["result"])

    def test_parser_depth_exhaustion_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.json"
            path.write_bytes(b"{}")

            with patch(
                "decision_os.intake.json.loads",
                side_effect=RecursionError,
            ):
                payload, exit_code = validate_intake_file(path)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)
            self.assertEqual(RESULT_INVALID, payload["result"])

    def test_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real_directory = root / "real"
            real_directory.mkdir()
            target = write_packet(real_directory, ready_packet())
            link = root / "linked.json"
            try:
                link.symlink_to(target)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")

            payload, exit_code = validate_intake_file(link)

            self.assertEqual(EXIT_INCOMPLETE, exit_code)
            self.assertEqual(RESULT_INVALID, payload["result"])


if __name__ == "__main__":
    unittest.main()
