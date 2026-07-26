from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from decision_os import audit_delivery as audit_contract
from decision_os import audit_gate as gate_contract
from decision_os import audit_link as link_contract
from decision_os import intake as intake_contract
from decision_os.audit_gate import (
    CHECK_CONTINUITY,
    CHECK_DELIVERY,
    CHECK_INTAKE,
    EXIT_NOT_READY,
    EXIT_READY,
    NEXT_STEP_CONTINUITY,
    NEXT_STEP_DELIVERY,
    NEXT_STEP_INTAKE,
    NEXT_STEP_INVALID,
    RESULT_INVALID,
    RESULT_NOT_READY,
    RESULT_NOT_RUN,
    RESULT_READY,
    RESULT_SCHEMA_VERSION,
    validate_audit_gate_files,
)
from tests.test_decision_os_audit_link import (
    example_audit,
    example_packet,
    replace_audit_field,
    write_audit,
    write_packet,
    write_pair,
)
from tests.test_decision_os_checks import tree_digest


def intake_payload(
    result: str,
    *,
    missing: tuple[str, ...] = (),
    invalid: tuple[str, ...] = (),
) -> dict[str, object]:
    next_steps = {
        intake_contract.RESULT_READY: intake_contract.NEXT_STEP_READY,
        intake_contract.RESULT_INCOMPLETE: intake_contract.NEXT_STEP_INCOMPLETE,
        intake_contract.RESULT_INVALID: intake_contract.NEXT_STEP_INVALID,
    }
    observed = (
        intake_contract.FIELD_ORDER
        if result == intake_contract.RESULT_READY
        else tuple(
            field
            for field in intake_contract.FIELD_ORDER
            if field not in set((*missing, *invalid))
        )
    )
    return intake_contract.result_payload(
        name="packet.json",
        result=result,
        observed_fields=observed,
        missing_required_fields=missing,
        invalid_fields=invalid,
        minimum_next_step=next_steps[result],
    )


def delivery_payload(
    result: str,
    *,
    missing_sections: tuple[str, ...] = (),
    invalid_sections: tuple[str, ...] = (),
    missing_fields: tuple[str, ...] = (),
    invalid_fields: tuple[str, ...] = (),
) -> dict[str, object]:
    next_steps = {
        audit_contract.RESULT_READY: audit_contract.NEXT_STEP_READY,
        audit_contract.RESULT_INCOMPLETE: audit_contract.NEXT_STEP_INCOMPLETE,
        audit_contract.RESULT_INVALID: audit_contract.NEXT_STEP_INVALID,
    }
    observed_sections = (
        audit_contract.REQUIRED_SECTIONS
        if result == audit_contract.RESULT_READY
        else tuple(
            section
            for section in audit_contract.REQUIRED_SECTIONS
            if section not in set((*missing_sections, *invalid_sections))
        )
    )
    observed_fields = (
        audit_contract.FIELD_ORDER
        if result == audit_contract.RESULT_READY
        else tuple(
            field
            for field in audit_contract.FIELD_ORDER
            if field not in set((*missing_fields, *invalid_fields))
        )
    )
    return audit_contract.result_payload(
        name="audit.md",
        profile=(
            audit_contract.SUPPORTED_PROFILE
            if result != audit_contract.RESULT_INVALID
            else "UNKNOWN"
        ),
        result=result,
        observed_sections=observed_sections,
        missing_required_sections=missing_sections,
        invalid_sections=invalid_sections,
        observed_fields=observed_fields,
        missing_required_fields=missing_fields,
        invalid_fields=invalid_fields,
        minimum_next_step=next_steps[result],
    )


def continuity_payload(
    result: str,
    *,
    matched: tuple[str, ...] = (),
    mismatched: tuple[str, ...] = (),
    missing: tuple[str, ...] = (),
) -> dict[str, object]:
    if result == link_contract.RESULT_LINKED and not matched:
        matched = tuple(link_contract.IDENTITY_FIELDS)
    elif result == link_contract.RESULT_MISMATCH and not matched:
        matched = tuple(
            field
            for field in link_contract.IDENTITY_FIELDS
            if field not in set(mismatched)
        )
    next_steps = {
        link_contract.RESULT_LINKED: link_contract.NEXT_STEP_LINKED,
        link_contract.RESULT_MISMATCH: link_contract.NEXT_STEP_MISMATCH,
        link_contract.RESULT_INVALID: link_contract.NEXT_STEP_INVALID,
    }
    return link_contract.result_payload(
        intake_name="packet.json",
        audit_name="audit.md",
        result=result,
        matched_fields=matched,
        mismatched_fields=mismatched,
        missing_fields=missing,
        minimum_next_step=next_steps[result],
    )


class AuditGateValidationTest(unittest.TestCase):
    def test_example_pair_is_ready_deterministic_read_only_and_no_echo(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = example_packet()
            packet["workflow"] = "SECRET SHARED WORKFLOW"
            packet["unknowns"] = ["SECRET ACCEPTED UNKNOWN"]
            intake = write_packet(root, packet)
            audit = write_audit(
                root,
                replace_audit_field(
                    example_audit(),
                    "workflow",
                    "SECRET SHARED WORKFLOW",
                ),
            )
            before = tree_digest(root)

            first, first_exit = validate_audit_gate_files(intake, audit)
            second, second_exit = validate_audit_gate_files(intake, audit)

            self.assertEqual(EXIT_READY, first_exit)
            self.assertEqual(first_exit, second_exit)
            self.assertEqual(first, second)
            self.assertEqual(RESULT_READY, first["result"])
            self.assertEqual(RESULT_SCHEMA_VERSION, first["schema_version"])
            self.assertEqual("audit-gate", first["command"])
            self.assertEqual(
                intake_contract.RESULT_READY,
                first["checks"][CHECK_INTAKE]["result"],
            )
            self.assertEqual(
                audit_contract.RESULT_READY,
                first["checks"][CHECK_DELIVERY]["result"],
            )
            self.assertEqual(
                link_contract.RESULT_LINKED,
                first["checks"][CHECK_CONTINUITY]["result"],
            )
            self.assertEqual(
                ["input_unknowns_present"],
                first["checks"][CHECK_INTAKE]["unknowns"],
            )
            self.assertEqual(
                ["Unknowns section"],
                first["checks"][CHECK_DELIVERY]["unknowns"],
            )
            self.assertFalse(first["inputs"]["intake"]["content_echoed"])
            self.assertFalse(first["inputs"]["audit"]["content_echoed"])
            encoded = json.dumps(first, ensure_ascii=False)
            self.assertNotIn("SECRET SHARED WORKFLOW", encoded)
            self.assertNotIn("SECRET ACCEPTED UNKNOWN", encoded)
            self.assertEqual(before, tree_digest(root))

    def test_incomplete_intake_skips_continuity_and_preserves_blocker(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packet = example_packet()
            del packet["observed_state"]
            intake = write_packet(root, packet)
            audit = write_audit(root, example_audit())

            payload, exit_code = validate_audit_gate_files(intake, audit)

            self.assertEqual(EXIT_NOT_READY, exit_code)
            self.assertEqual(RESULT_NOT_READY, payload["result"])
            self.assertEqual(
                ["observed_state"],
                payload["checks"][CHECK_INTAKE]["missing_fields"],
            )
            self.assertEqual(
                audit_contract.RESULT_READY,
                payload["checks"][CHECK_DELIVERY]["result"],
            )
            self.assertEqual(
                RESULT_NOT_RUN,
                payload["checks"][CHECK_CONTINUITY]["result"],
            )
            self.assertEqual(
                NEXT_STEP_INTAKE,
                payload["minimum_next_step"],
            )

    def test_incomplete_delivery_skips_continuity_and_preserves_blocker(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake = write_packet(root, example_packet())
            audit = write_audit(
                root,
                example_audit().replace(
                    "## Completion Line",
                    "## Removed Completion",
                    1,
                ),
            )

            payload, exit_code = validate_audit_gate_files(intake, audit)

            self.assertEqual(EXIT_NOT_READY, exit_code)
            self.assertEqual(RESULT_NOT_READY, payload["result"])
            self.assertEqual(
                ["Completion Line"],
                payload["checks"][CHECK_DELIVERY]["missing_sections"],
            )
            self.assertEqual(
                RESULT_NOT_RUN,
                payload["checks"][CHECK_CONTINUITY]["result"],
            )
            self.assertEqual(
                NEXT_STEP_DELIVERY,
                payload["minimum_next_step"],
            )

    def test_valid_structure_with_mismatch_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake = write_packet(root, example_packet())
            audit = write_audit(
                root,
                replace_audit_field(
                    example_audit(),
                    "workflow",
                    "Different workflow",
                ),
            )

            payload, exit_code = validate_audit_gate_files(intake, audit)

            self.assertEqual(EXIT_NOT_READY, exit_code)
            self.assertEqual(RESULT_NOT_READY, payload["result"])
            self.assertEqual(
                link_contract.RESULT_MISMATCH,
                payload["checks"][CHECK_CONTINUITY]["result"],
            )
            self.assertEqual(
                ["workflow"],
                payload["checks"][CHECK_CONTINUITY]["mismatched_fields"],
            )
            self.assertEqual(
                NEXT_STEP_CONTINUITY,
                payload["minimum_next_step"],
            )

    def test_structure_matrix_has_invalid_precedence_and_fixed_order(
        self,
    ) -> None:
        intake_cases = {
            intake_contract.RESULT_READY: (
                intake_contract.EXIT_READY,
                intake_payload(intake_contract.RESULT_READY),
            ),
            intake_contract.RESULT_INCOMPLETE: (
                intake_contract.EXIT_INCOMPLETE,
                intake_payload(
                    intake_contract.RESULT_INCOMPLETE,
                    missing=("observed_state", "workflow"),
                ),
            ),
            intake_contract.RESULT_INVALID: (
                intake_contract.EXIT_INCOMPLETE,
                intake_payload(intake_contract.RESULT_INVALID),
            ),
        }
        delivery_cases = {
            audit_contract.RESULT_READY: (
                audit_contract.EXIT_READY,
                delivery_payload(audit_contract.RESULT_READY),
            ),
            audit_contract.RESULT_INCOMPLETE: (
                audit_contract.EXIT_INCOMPLETE,
                delivery_payload(
                    audit_contract.RESULT_INCOMPLETE,
                    missing_sections=("Completion Line", "Scope"),
                ),
            ),
            audit_contract.RESULT_INVALID: (
                audit_contract.EXIT_INCOMPLETE,
                delivery_payload(audit_contract.RESULT_INVALID),
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            for intake_result, (
                intake_exit,
                supplied_intake,
            ) in intake_cases.items():
                for delivery_result, (
                    delivery_exit,
                    supplied_delivery,
                ) in delivery_cases.items():
                    with self.subTest(
                        intake=intake_result,
                        delivery=delivery_result,
                    ):
                        linked = (
                            continuity_payload(
                                link_contract.RESULT_LINKED,
                                matched=tuple(link_contract.IDENTITY_FIELDS),
                            ),
                            link_contract.EXIT_LINKED,
                        )
                        with (
                            patch.object(
                                gate_contract.intake_contract,
                                "validate_intake_file",
                                return_value=(
                                    supplied_intake,
                                    intake_exit,
                                ),
                            ),
                            patch.object(
                                gate_contract.audit_contract,
                                "validate_audit_delivery_file",
                                return_value=(
                                    supplied_delivery,
                                    delivery_exit,
                                ),
                            ),
                            patch.object(
                                gate_contract.link_contract,
                                "validate_audit_link_files",
                                return_value=linked,
                            ) as link_mock,
                        ):
                            payload, exit_code = validate_audit_gate_files(
                                intake,
                                audit,
                            )

                        both_ready = (
                            intake_result == intake_contract.RESULT_READY
                            and delivery_result == audit_contract.RESULT_READY
                        )
                        if both_ready:
                            self.assertEqual(EXIT_READY, exit_code)
                            self.assertEqual(RESULT_READY, payload["result"])
                            link_mock.assert_called_once()
                        else:
                            self.assertEqual(EXIT_NOT_READY, exit_code)
                            expected = (
                                RESULT_INVALID
                                if intake_result
                                == intake_contract.RESULT_INVALID
                                or delivery_result
                                == audit_contract.RESULT_INVALID
                                else RESULT_NOT_READY
                            )
                            self.assertEqual(expected, payload["result"])
                            self.assertEqual(
                                RESULT_NOT_RUN,
                                payload["checks"][CHECK_CONTINUITY]["result"],
                            )
                            link_mock.assert_not_called()

                        if (
                            intake_result
                            == intake_contract.RESULT_INCOMPLETE
                        ):
                            self.assertEqual(
                                ["workflow", "observed_state"],
                                payload["checks"][CHECK_INTAKE][
                                    "missing_fields"
                                ],
                            )
                        if (
                            delivery_result
                            == audit_contract.RESULT_INCOMPLETE
                        ):
                            self.assertEqual(
                                ["Scope", "Completion Line"],
                                payload["checks"][CHECK_DELIVERY][
                                    "missing_sections"
                                ],
                            )

    def test_continuity_result_matrix_maps_to_top_level_contract(self) -> None:
        cases = (
            (
                link_contract.RESULT_LINKED,
                link_contract.EXIT_LINKED,
                RESULT_READY,
                EXIT_READY,
            ),
            (
                link_contract.RESULT_MISMATCH,
                link_contract.EXIT_NOT_LINKED,
                RESULT_NOT_READY,
                EXIT_NOT_READY,
            ),
            (
                link_contract.RESULT_INVALID,
                link_contract.EXIT_NOT_LINKED,
                RESULT_INVALID,
                EXIT_NOT_READY,
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            for link_result, link_exit, result, exit_code in cases:
                with self.subTest(link_result=link_result):
                    supplied = continuity_payload(
                        link_result,
                        mismatched=(
                            ("workflow",)
                            if link_result == link_contract.RESULT_MISMATCH
                            else ()
                        ),
                    )
                    with patch.object(
                        gate_contract.link_contract,
                        "validate_audit_link_files",
                        return_value=(supplied, link_exit),
                    ):
                        payload, actual_exit = validate_audit_gate_files(
                            intake,
                            audit,
                        )
                    self.assertEqual(exit_code, actual_exit)
                    self.assertEqual(result, payload["result"])

    def test_invalid_and_unavailable_inputs_fail_closed_without_echo(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            missing = root / "missing.json"
            intake_link = root / "intake-link.json"
            intake_link.symlink_to(intake)
            invalid_utf8 = root / "invalid.md"
            invalid_utf8.write_bytes(b"\xffSECRET")
            cases = (
                (missing, audit),
                (intake_link, audit),
                (intake, invalid_utf8),
                (root, audit),
            )
            for supplied_intake, supplied_audit in cases:
                with self.subTest(
                    intake=supplied_intake.name,
                    audit=supplied_audit.name,
                ):
                    payload, exit_code = validate_audit_gate_files(
                        supplied_intake,
                        supplied_audit,
                    )
                    self.assertEqual(EXIT_NOT_READY, exit_code)
                    self.assertEqual(RESULT_INVALID, payload["result"])
                    self.assertEqual(
                        RESULT_NOT_RUN,
                        payload["checks"][CHECK_CONTINUITY]["result"],
                    )
                    encoded = json.dumps(payload)
                    self.assertNotIn("SECRET", encoded)
                    self.assertNotIn(str(root), encoded)

    def test_identity_changes_between_component_checks_fail_closed(
        self,
    ) -> None:
        real_intake = intake_contract.validate_intake_file
        real_delivery = audit_contract.validate_audit_delivery_file
        real_link = link_contract.validate_audit_link_files

        for stage in ("after_intake", "after_delivery", "during_link"):
            with self.subTest(stage=stage):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    intake, audit = write_pair(root)

                    def intake_stage(path: Path):
                        result = real_intake(path)
                        if stage == "after_intake":
                            audit.write_text(
                                audit.read_text(encoding="utf-8") + "\n",
                                encoding="utf-8",
                            )
                        return result

                    def delivery_stage(path: Path):
                        result = real_delivery(path)
                        if stage == "after_delivery":
                            intake.write_text(
                                intake.read_text(encoding="utf-8") + "\n",
                                encoding="utf-8",
                            )
                        return result

                    def link_stage(first: Path, second: Path):
                        result = real_link(first, second)
                        if stage == "during_link":
                            audit.write_text(
                                audit.read_text(encoding="utf-8") + "\n",
                                encoding="utf-8",
                            )
                        return result

                    with (
                        patch.object(
                            gate_contract.intake_contract,
                            "validate_intake_file",
                            side_effect=intake_stage,
                        ),
                        patch.object(
                            gate_contract.audit_contract,
                            "validate_audit_delivery_file",
                            side_effect=delivery_stage,
                        ) as delivery_mock,
                        patch.object(
                            gate_contract.link_contract,
                            "validate_audit_link_files",
                            side_effect=link_stage,
                        ) as link_mock,
                    ):
                        payload, exit_code = validate_audit_gate_files(
                            intake,
                            audit,
                        )

                    self.assertEqual(EXIT_NOT_READY, exit_code)
                    self.assertEqual(RESULT_INVALID, payload["result"])
                    self.assertEqual(
                        ["input_identity_changed"],
                        payload["unknowns"],
                    )
                    self.assertEqual(
                        NEXT_STEP_INVALID,
                        payload["minimum_next_step"],
                    )
                    if stage == "after_intake":
                        delivery_mock.assert_not_called()
                        link_mock.assert_not_called()
                    elif stage == "after_delivery":
                        delivery_mock.assert_called_once()
                        link_mock.assert_not_called()
                    else:
                        delivery_mock.assert_called_once()
                        link_mock.assert_called_once()

    def test_component_exit_contract_mismatch_raises_internal_boundary(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)
            with patch.object(
                gate_contract.intake_contract,
                "validate_intake_file",
                return_value=(
                    intake_payload(intake_contract.RESULT_READY),
                    intake_contract.EXIT_INCOMPLETE,
                ),
            ):
                with self.assertRaises(RuntimeError):
                    validate_audit_gate_files(intake, audit)

    def test_contradictory_ready_component_payloads_fail_closed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake, audit = write_pair(root)

            bad_intake = intake_payload(intake_contract.RESULT_READY)
            bad_intake["missing_required_fields"] = ["workflow"]

            bad_delivery = delivery_payload(audit_contract.RESULT_READY)
            bad_delivery["missing_required_sections"] = ["Scope"]

            bad_link = continuity_payload(link_contract.RESULT_LINKED)
            bad_link["mismatched_fields"] = ["workflow"]

            cases = (
                (
                    "intake",
                    patch.object(
                        gate_contract.intake_contract,
                        "validate_intake_file",
                        return_value=(
                            bad_intake,
                            intake_contract.EXIT_READY,
                        ),
                    ),
                ),
                (
                    "delivery",
                    patch.object(
                        gate_contract.audit_contract,
                        "validate_audit_delivery_file",
                        return_value=(
                            bad_delivery,
                            audit_contract.EXIT_READY,
                        ),
                    ),
                ),
                (
                    "continuity",
                    patch.object(
                        gate_contract.link_contract,
                        "validate_audit_link_files",
                        return_value=(
                            bad_link,
                            link_contract.EXIT_LINKED,
                        ),
                    ),
                ),
            )
            for name, mocked_component in cases:
                with self.subTest(component=name):
                    with mocked_component:
                        with self.assertRaises(RuntimeError):
                            validate_audit_gate_files(intake, audit)


if __name__ == "__main__":
    unittest.main()
