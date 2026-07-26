from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from decision_os.audit_delivery import (
    CLAIMS_NOT_MADE,
    EXIT_INCOMPLETE,
    EXIT_READY,
    FIELD_ORDER,
    MAX_INPUT_BYTES,
    REQUIRED_SECTIONS,
    RESULT_INCOMPLETE,
    RESULT_INVALID,
    RESULT_READY,
    RESULT_SCHEMA_VERSION,
    SUPPORTED_PROFILE,
    validate_audit_delivery_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SHIPPED_EXAMPLE = (
    REPO_ROOT
    / "examples"
    / "ai_application_workflow_audit_delivery_v0_1.md"
)


def ready_document() -> str:
    return SHIPPED_EXAMPLE.read_text(encoding="utf-8")


def write_document(directory: Path, content: str) -> Path:
    path = directory / "audit.md"
    path.write_text(content, encoding="utf-8")
    return path


def validate_text(content: str) -> tuple[dict[str, object], int]:
    with tempfile.TemporaryDirectory() as directory:
        return validate_audit_delivery_file(
            write_document(Path(directory), content)
        )


class AuditDeliveryValidationTest(unittest.TestCase):
    def test_ready_example_is_deterministic_read_only_and_does_not_echo(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = ready_document().replace(
                "Synthetic editorial approval assistant",
                "SECRET APPLICATION VALUE",
            )
            path = write_document(root, content)
            before = path.read_bytes()

            first, first_exit = validate_audit_delivery_file(path)
            second, second_exit = validate_audit_delivery_file(path)

            self.assertEqual(EXIT_READY, first_exit)
            self.assertEqual(first_exit, second_exit)
            self.assertEqual(first, second)
            self.assertEqual(RESULT_READY, first["result"])
            self.assertEqual(RESULT_SCHEMA_VERSION, first["schema_version"])
            self.assertEqual(SUPPORTED_PROFILE, first["profile"])
            self.assertEqual(list(REQUIRED_SECTIONS), first["observed_sections"])
            self.assertEqual(list(FIELD_ORDER), first["observed_fields"])
            self.assertEqual([], first["missing_required_sections"])
            self.assertEqual([], first["missing_required_fields"])
            self.assertEqual([], first["invalid_sections"])
            self.assertEqual([], first["invalid_fields"])
            self.assertEqual(list(CLAIMS_NOT_MADE), first["claims_not_made"])
            self.assertFalse(first["input"]["content_echoed"])
            self.assertEqual("audit.md", first["input"]["name"])
            self.assertNotIn("SECRET APPLICATION VALUE", json.dumps(first))
            self.assertEqual(before, path.read_bytes())

    def test_missing_required_heading_is_incomplete(self) -> None:
        payload, exit_code = validate_text(
            ready_document().replace(
                "## Friction Map",
                "## Optional Map",
                1,
            )
        )

        self.assertEqual(EXIT_INCOMPLETE, exit_code)
        self.assertEqual(RESULT_INCOMPLETE, payload["result"])
        self.assertEqual(
            ["Friction Map"],
            payload["missing_required_sections"],
        )
        self.assertIn(
            "Friction Map table",
            payload["missing_required_fields"],
        )

    def test_duplicate_required_heading_is_invalid(self) -> None:
        payload, exit_code = validate_text(
            ready_document() + "\n## Scope\n"
        )

        self.assertEqual(EXIT_INCOMPLETE, exit_code)
        self.assertEqual(RESULT_INVALID, payload["result"])
        self.assertIn("Scope", payload["invalid_sections"])

    def test_required_headings_out_of_order_are_invalid(self) -> None:
        content = ready_document()
        content = content.replace("## Scope", "## TEMPORARY", 1)
        content = content.replace(
            "## Source Materials",
            "## Scope",
            1,
        )
        content = content.replace(
            "## TEMPORARY",
            "## Source Materials",
            1,
        )

        payload, exit_code = validate_text(content)

        self.assertEqual(EXIT_INCOMPLETE, exit_code)
        self.assertEqual(RESULT_INVALID, payload["result"])
        self.assertIn(
            "Required heading order",
            payload["invalid_sections"],
        )

    def test_title_must_be_nonplaceholder_and_before_required_sections(
        self,
    ) -> None:
        title, remainder = ready_document().split("\n", 1)
        cases = (
            (
                "placeholder",
                ready_document().replace(
                    title,
                    "# <fill this>",
                    1,
                ),
                RESULT_INCOMPLETE,
                "missing_required_sections",
                "Title",
            ),
            (
                "misplaced",
                remainder + "\n" + title + "\n",
                RESULT_INVALID,
                "invalid_sections",
                "Required heading order",
            ),
        )
        for name, content, result, output_key, marker in cases:
            with self.subTest(name=name):
                payload, exit_code = validate_text(content)

                self.assertEqual(EXIT_INCOMPLETE, exit_code)
                self.assertEqual(result, payload["result"])
                self.assertIn(marker, payload[output_key])

    def test_heading_and_field_inside_fence_are_ignored(self) -> None:
        content = ready_document().replace(
            "Fallback Approval Restart Record\n",
            (
                "## Scope\n"
                "Audit Profile: UNSUPPORTED_SECRET\n"
                "Fallback Approval Restart Record\n"
            ),
            1,
        )

        payload, exit_code = validate_text(content)

        self.assertEqual(EXIT_READY, exit_code)
        self.assertEqual(RESULT_READY, payload["result"])
        self.assertEqual(SUPPORTED_PROFILE, payload["profile"])
        self.assertNotIn("UNSUPPORTED_SECRET", json.dumps(payload))

    def test_unclosed_fenced_block_is_invalid(self) -> None:
        content = ready_document().replace(
            "Still UNKNOWN:\n```\n",
            "Still UNKNOWN:\n",
            1,
        )

        payload, exit_code = validate_text(content)

        self.assertEqual(EXIT_INCOMPLETE, exit_code)
        self.assertEqual(RESULT_INVALID, payload["result"])
        self.assertIn("Fenced code block", payload["invalid_sections"])

    def test_missing_empty_and_angle_placeholder_fields_are_incomplete(
        self,
    ) -> None:
        cases = (
            (
                "missing",
                (
                    "Current Owner: Human publication operator\n",
                    "",
                ),
                "Current Owner",
                "missing_required_fields",
            ),
            (
                "empty",
                (
                    "Application or Workflow: Synthetic editorial "
                    "approval assistant",
                    "Application or Workflow:",
                ),
                "Application or Workflow",
                "invalid_fields",
            ),
            (
                "placeholder",
                (
                    "Audit As-of: 2026-07-26",
                    "Audit As-of: <fill this>",
                ),
                "Audit As-of",
                "invalid_fields",
            ),
        )
        for name, replacement, field, output_key in cases:
            with self.subTest(name=name):
                payload, exit_code = validate_text(
                    ready_document().replace(*replacement, 1)
                )

                self.assertEqual(EXIT_INCOMPLETE, exit_code)
                self.assertEqual(RESULT_INCOMPLETE, payload["result"])
                self.assertIn(field, payload[output_key])

    def test_unknown_rating_with_rationale_is_accepted(self) -> None:
        content = ready_document().replace(
            (
                "Trigger Clarity: PASS — The interruption and attempted "
                "handoff are identified."
            ),
            "Trigger Clarity: UNKNOWN — The accepted evidence is silent.",
            1,
        )

        payload, exit_code = validate_text(content)

        self.assertEqual(EXIT_READY, exit_code)
        self.assertEqual(RESULT_READY, payload["result"])
        self.assertIn("Trigger Clarity", payload["unknowns"])

    def test_rating_rationale_accepts_optional_separator(self) -> None:
        original = (
            "Trigger Clarity: PASS — The interruption and attempted "
            "handoff are identified."
        )
        replacements = (
            "Trigger Clarity: PASS: The initiating event is identified.",
            "Trigger Clarity: PASS The initiating event is identified.",
        )
        for replacement in replacements:
            with self.subTest(replacement=replacement):
                payload, exit_code = validate_text(
                    ready_document().replace(original, replacement, 1)
                )

                self.assertEqual(EXIT_READY, exit_code)
                self.assertEqual(RESULT_READY, payload["result"])

    def test_unknown_is_rejected_as_the_whole_priority_fix(self) -> None:
        content = ready_document().replace(
            (
                "Selected Fix: Add a fallback approval restart record "
                "before publication handoff."
            ),
            "Selected Fix: UNKNOWN",
            1,
        )

        payload, exit_code = validate_text(content)

        self.assertEqual(EXIT_INCOMPLETE, exit_code)
        self.assertEqual(RESULT_INCOMPLETE, payload["result"])
        self.assertIn("Selected Fix", payload["invalid_fields"])

    def test_unknown_with_rationale_is_not_a_known_deliverable(self) -> None:
        cases = (
            (
                (
                    "Selected Fix: Add a fallback approval restart record "
                    "before publication handoff."
                ),
                "Selected Fix: UNKNOWN — No fix selected.",
                "Selected Fix",
            ),
            (
                "Asset Content: Copy and complete this record before "
                "resuming the bounded handoff.",
                "Asset Content: UNKNOWN — No asset delivered.",
                "Asset Content",
            ),
            (
                (
                    "Selected Fix: Add a fallback approval restart record "
                    "before publication handoff."
                ),
                "Selected Fix: UNKNOWN—No fix selected.",
                "Selected Fix",
            ),
            (
                "Asset Content: Copy and complete this record before "
                "resuming the bounded handoff.",
                "Asset Content: UNKNOWN:No asset delivered.",
                "Asset Content",
            ),
        )
        for old, new, field in cases:
            with self.subTest(field=field):
                payload, exit_code = validate_text(
                    ready_document().replace(old, new, 1)
                )

                self.assertEqual(EXIT_INCOMPLETE, exit_code)
                self.assertEqual(RESULT_INCOMPLETE, payload["result"])
                self.assertIn(field, payload["invalid_fields"])

    def test_missing_or_malformed_diagnosis_dimension_is_incomplete(
        self,
    ) -> None:
        cases = (
            (
                "missing",
                (
                    "Evidence Continuity: FAIL — The next operator lacks "
                    "a durable approval record.\n"
                ),
            ),
            (
                "invalid_rating",
                (
                    "Restartability: PARTIAL — A manual stop-and-revalidate "
                    "fallback remains available.",
                    (
                        "Restartability: MAYBE — A manual fallback remains "
                        "available."
                    ),
                ),
            ),
            (
                "missing_rationale",
                (
                    "Safe Next Action: PASS — Publication remains stopped "
                    "until identity is re-established.",
                    "Safe Next Action: PASS",
                ),
            ),
        )
        for name, replacement in cases:
            with self.subTest(name=name):
                if isinstance(replacement, tuple):
                    content = ready_document().replace(*replacement, 1)
                else:
                    content = ready_document().replace(replacement, "", 1)

                payload, exit_code = validate_text(content)

                self.assertEqual(EXIT_INCOMPLETE, exit_code)
                self.assertEqual(RESULT_INCOMPLETE, payload["result"])
                target = {
                    "missing": "Evidence Continuity",
                    "invalid_rating": "Restartability",
                    "missing_rationale": "Safe Next Action",
                }[name]
                output = (
                    payload["missing_required_fields"]
                    if name == "missing"
                    else payload["invalid_fields"]
                )
                self.assertIn(target, output)

    def test_friction_map_table_contract_fails_closed(self) -> None:
        table = (
            "| Point | Expected Carrier | Observed Gap | Returned Human Work |\n"
            "| --- | --- | --- | --- |\n"
            "| Approval handoff | Draft identity and accepted state | "
            "Approval binding absent | Revalidation and repeated handoff "
            "decision |\n"
        )
        cases = (
            ("missing", "", "missing_required_fields"),
            (
                "wrong_columns",
                table.replace("Expected Carrier", "Expected State"),
                "invalid_fields",
            ),
            (
                "no_rows",
                (
                    "| Point | Expected Carrier | Observed Gap | "
                    "Returned Human Work |\n"
                    "| --- | --- | --- | --- |\n"
                ),
                "invalid_fields",
            ),
            (
                "blank_before_delimiter",
                (
                    "| Point | Expected Carrier | Observed Gap | "
                    "Returned Human Work |\n"
                    "\n"
                    "| --- | --- | --- | --- |\n"
                    "| Approval handoff | Draft identity | Gap | Work |\n"
                ),
                "invalid_fields",
            ),
            (
                "fenced_gap_before_row",
                (
                    "| Point | Expected Carrier | Observed Gap | "
                    "Returned Human Work |\n"
                    "| --- | --- | --- | --- |\n"
                    "```text\n"
                    "not a table row\n"
                    "```\n"
                    "| Approval handoff | Draft identity | Gap | Work |\n"
                ),
                "invalid_fields",
            ),
            (
                "indented_code_block",
                (
                    "    | Point | Expected Carrier | Observed Gap | "
                    "Returned Human Work |\n"
                    "    | --- | --- | --- | --- |\n"
                    "    | Approval handoff | Draft identity | Gap | Work |\n"
                ),
                "missing_required_fields",
            ),
        )
        for name, replacement, output_key in cases:
            with self.subTest(name=name):
                payload, exit_code = validate_text(
                    ready_document().replace(table, replacement, 1)
                )

                self.assertEqual(EXIT_INCOMPLETE, exit_code)
                self.assertEqual(RESULT_INCOMPLETE, payload["result"])
                self.assertIn("Friction Map table", payload[output_key])

    def test_claim_boundary_must_be_complete_and_exact(self) -> None:
        cases = (
            (
                "missing",
                "Vendor Bug Fix: NOT CLAIMED\n",
                "",
                "missing_required_fields",
            ),
            (
                "contradictory",
                "Future Prevention: NOT CLAIMED",
                "Future Prevention: CLAIMED",
                "invalid_fields",
            ),
        )
        for name, old, new, output_key in cases:
            with self.subTest(name=name):
                payload, exit_code = validate_text(
                    ready_document().replace(old, new, 1)
                )

                self.assertEqual(EXIT_INCOMPLETE, exit_code)
                self.assertEqual(RESULT_INCOMPLETE, payload["result"])
                expected = (
                    "Vendor Bug Fix"
                    if name == "missing"
                    else "Future Prevention"
                )
                self.assertIn(expected, payload[output_key])

    def test_unknowns_and_exclusions_require_nonplaceholder_bullets(
        self,
    ) -> None:
        cases = (
            (
                "unknowns",
                (
                    "- Native session recoverability and vendor-internal "
                    "state remain unknown."
                ),
                "- TODO",
                "Unknowns content",
            ),
            (
                "exclusions",
                (
                    "- Vendor repair, live recovery, security review, and "
                    "production implementation are outside scope."
                ),
                "",
                "Exclusions content",
            ),
        )
        for name, old, new, field in cases:
            with self.subTest(name=name):
                payload, exit_code = validate_text(
                    ready_document().replace(old, new, 1)
                )

                self.assertEqual(EXIT_INCOMPLETE, exit_code)
                self.assertEqual(RESULT_INCOMPLETE, payload["result"])
                self.assertIn(field, payload["invalid_fields"])

    def test_explicit_bounded_no_unknown_declaration_is_accepted(self) -> None:
        content = ready_document().replace(
            (
                "- Native session recoverability and vendor-internal "
                "state remain unknown."
            ),
            "- none recorded within the accepted scope",
            1,
        )

        payload, exit_code = validate_text(content)

        self.assertEqual(EXIT_READY, exit_code)
        self.assertEqual(RESULT_READY, payload["result"])
        self.assertNotIn("Unknowns section", payload["unknowns"])

    def test_deep_markdown_decoration_is_bounded_and_incomplete(self) -> None:
        decorated_placeholder = "- " * 1200 + "TODO"
        content = ready_document().replace(
            (
                "- Native session recoverability and vendor-internal "
                "state remain unknown."
            ),
            f"- {decorated_placeholder}",
            1,
        )

        payload, exit_code = validate_text(content)

        self.assertEqual(EXIT_INCOMPLETE, exit_code)
        self.assertEqual(RESULT_INCOMPLETE, payload["result"])
        self.assertIn("Unknowns content", payload["invalid_fields"])

    def test_missing_completion_line_is_incomplete(self) -> None:
        payload, exit_code = validate_text(
            ready_document().replace(
                "## Completion Line",
                "## Closure",
                1,
            )
        )

        self.assertEqual(EXIT_INCOMPLETE, exit_code)
        self.assertEqual(RESULT_INCOMPLETE, payload["result"])
        self.assertIn(
            "Completion Line",
            payload["missing_required_sections"],
        )

    def test_completion_line_requires_visible_nonheading_content(self) -> None:
        original = (
            "The bounded synthetic incident, diagnosis, priority fix, "
            "operational asset,\n"
            "restart distinction, unknowns, exclusions, and claim boundaries "
            "are present for\n"
            "structural validation."
        )
        replacements = (
            "### TODO",
            "```text\n```\n",
            "UNKNOWN—No closure established.",
        )
        for replacement in replacements:
            with self.subTest(replacement=replacement):
                payload, exit_code = validate_text(
                    ready_document().replace(original, replacement, 1)
                )

                self.assertEqual(EXIT_INCOMPLETE, exit_code)
                self.assertEqual(RESULT_INCOMPLETE, payload["result"])
                self.assertIn(
                    "Completion Line content",
                    payload["invalid_fields"],
                )

    def test_only_asset_content_accepts_multiline_or_fenced_value(
        self,
    ) -> None:
        ordinary = ready_document().replace(
            (
                "Application or Workflow: Synthetic editorial approval "
                "assistant"
            ),
            (
                "Application or Workflow:\n"
                "```text\n"
                "Synthetic editorial approval assistant\n"
                "```"
            ),
            1,
        )
        ordinary_payload, ordinary_exit = validate_text(ordinary)

        self.assertEqual(EXIT_INCOMPLETE, ordinary_exit)
        self.assertEqual(RESULT_INCOMPLETE, ordinary_payload["result"])
        self.assertIn(
            "Application or Workflow",
            ordinary_payload["invalid_fields"],
        )

        asset = ready_document().replace(
            (
                "Asset Content: Copy and complete this record before "
                "resuming the bounded handoff."
            ),
            "Asset Content:",
            1,
        )
        asset_payload, asset_exit = validate_text(asset)

        self.assertEqual(EXIT_READY, asset_exit)
        self.assertEqual(RESULT_READY, asset_payload["result"])

        asset_block_start = asset.index("```text")
        asset_block_end = asset.index("```", asset_block_start + 3) + 3
        empty_asset = (
            asset[:asset_block_start]
            + "```text\n```"
            + asset[asset_block_end:]
        )
        empty_payload, empty_exit = validate_text(empty_asset)

        self.assertEqual(EXIT_INCOMPLETE, empty_exit)
        self.assertEqual(RESULT_INCOMPLETE, empty_payload["result"])
        self.assertIn("Asset Content", empty_payload["invalid_fields"])

    def test_tilde_fenced_asset_content_is_supported(self) -> None:
        content = ready_document().replace(
            "Asset Content: Copy and complete this record before "
            "resuming the bounded handoff.",
            "Asset Content:",
            1,
        )
        content = content.replace("```text", "~~~~text", 1)
        content = content.replace("```", "~~~~", 1)

        payload, exit_code = validate_text(content)

        self.assertEqual(EXIT_READY, exit_code)
        self.assertEqual(RESULT_READY, payload["result"])

    def test_unsupported_profile_is_invalid_without_echo(self) -> None:
        payload, exit_code = validate_text(
            ready_document().replace(
                SUPPORTED_PROFILE,
                "SECRET_UNSUPPORTED_PROFILE",
                1,
            )
        )

        self.assertEqual(EXIT_INCOMPLETE, exit_code)
        self.assertEqual(RESULT_INVALID, payload["result"])
        self.assertEqual("UNKNOWN", payload["profile"])
        self.assertIn("Audit Profile", payload["invalid_fields"])
        self.assertNotIn("Audit Profile", payload["observed_fields"])
        self.assertNotIn("SECRET_UNSUPPORTED_PROFILE", json.dumps(payload))

    def test_exact_size_limit_is_accepted(self) -> None:
        content = ready_document().encode("utf-8")
        self.assertLess(len(content), MAX_INPUT_BYTES)
        content += b" " * (MAX_INPUT_BYTES - len(content))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.md"
            path.write_bytes(content)

            payload, exit_code = validate_audit_delivery_file(path)

        self.assertEqual(EXIT_READY, exit_code)
        self.assertEqual(RESULT_READY, payload["result"])

    def test_fifo_is_rejected_before_open(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.fifo"
            os.mkfifo(path)

            with patch(
                "decision_os.audit_delivery.os.open",
                side_effect=AssertionError("non-regular input was opened"),
            ):
                payload, exit_code = validate_audit_delivery_file(path)

        self.assertEqual(EXIT_INCOMPLETE, exit_code)
        self.assertEqual(RESULT_INVALID, payload["result"])

    def test_symlink_directory_oversize_and_invalid_utf8_are_invalid(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = write_document(root, ready_document())
            link = root / "linked.md"
            try:
                link.symlink_to(target)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            oversized = root / "oversized.md"
            oversized.write_bytes(b"x" * (MAX_INPUT_BYTES + 1))
            invalid_utf8 = root / "invalid.md"
            invalid_utf8.write_bytes(b"\xff")

            for path in (link, root, oversized, invalid_utf8):
                with self.subTest(path=path.name):
                    payload, exit_code = validate_audit_delivery_file(path)

                    self.assertEqual(EXIT_INCOMPLETE, exit_code)
                    self.assertEqual(RESULT_INVALID, payload["result"])
                    self.assertFalse(payload["input"]["content_echoed"])
                    self.assertNotIn(str(root), json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
