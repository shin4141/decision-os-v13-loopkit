from __future__ import annotations

import inspect
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from decision_os.companion.guided_intake import (
    GuidedIntakeController,
    GuidedIntakeValidationError,
    _quoted_payload_boundary,
    structured_sha256,
)
from decision_os.companion.ordinary_user_path import (
    ORDINARY_PROFILE,
    PRODUCT_PROFILE,
    ContractFixationCompiler,
    ContractFixationInput,
    OrdinaryUserPathError,
)


FIXTURES = Path(__file__).parent / "fixtures"
ORDINARY_SOURCE = (
    FIXTURES
    / "ordinary_user_path_v0_1"
    / "Decision_OS_Ordinary_User_Path_Contract_v0.1_APPROVED_CANDIDATE.md"
)
ORACLE = (
    FIXTURES
    / "ordinary_user_path_v0_1"
    / "ordinary_user_path_semantic_oracle_v0.1.json"
)
PRODUCT_WRAPPER = (
    FIXTURES
    / "guided_intake_quoted_payload_v0_1"
    / "Decision_OS_Product_Contract_Fixation_Wrapper_v0.1.txt"
)
REPOSITORY_IDENTITY = "d" * 40


def product_source() -> bytes:
    wrapper = PRODUCT_WRAPPER.read_bytes()
    begin = b"BEGIN EXACT PRODUCT CONTRACT\n"
    end = b"END EXACT PRODUCT CONTRACT\n"
    return wrapper[wrapper.index(begin) + len(begin) : wrapper.index(end)]


def compile_source(
    source: bytes,
    filename: str = "Contract.md",
):
    return ContractFixationCompiler().compile(
        ContractFixationInput(
            source_bytes=source,
            filename=filename,
            repository_path="/private/test/repository",
            repository_identity=REPOSITORY_IDENTITY,
            active_prior_request_id="GI-REQ-prior",
        )
    )


class ContractFixationCompilerTest(unittest.TestCase):
    def assert_code(self, code: str, source: bytes, filename: str = "Contract.md") -> None:
        with self.assertRaises(OrdinaryUserPathError) as raised:
            compile_source(source, filename)
        self.assertEqual(code, raised.exception.code)

    def test_ordinary_golden_is_deterministic_and_matches_frozen_oracle(self) -> None:
        source = ORDINARY_SOURCE.read_bytes()
        first = compile_source(source, ORDINARY_SOURCE.name)
        second = compile_source(source, ORDINARY_SOURCE.name)
        oracle = json.loads(ORACLE.read_text(encoding="utf-8"))

        self.assertEqual(ORDINARY_PROFILE, first.contract_profile)
        self.assertEqual(first, second)
        self.assertEqual(11_039, first.source_identity["byte_size"])
        self.assertEqual(oracle["source_sha256"], first.source_identity["sha256"])
        self.assertEqual(
            "c3de6236a450666d8a8ef59a8f8db303bf4654cc9cb20d6ab816f3066177b11e",
            first.wrapper_identity["sha256"],
        )
        draft = json.loads(first.draft_bytes)
        interpretation, question = GuidedIntakeController._validate_draft(
            draft,
            original=first.wrapper_bytes.decode("utf-8"),
            request_sha256=first.wrapper_identity["sha256"],
            confirmations=[],
        )
        self.assertIsNone(question)
        self.assertEqual(oracle["interpretation_sha256"], structured_sha256(interpretation))
        self.assertEqual(oracle["objective"], interpretation["objective"]["text"])
        self.assertEqual(oracle["completion"], interpretation["completion_line"]["text"])
        self.assertEqual("CLEAR ENOUGH TO FREEZE", interpretation["gate"])

    def test_product_golden_preserves_exact_historical_wrapper_and_meaning(self) -> None:
        source = product_source()
        result = compile_source(source, "Decision_OS_Product_Contract.md")

        self.assertEqual(PRODUCT_PROFILE, result.contract_profile)
        self.assertEqual(PRODUCT_WRAPPER.read_bytes(), result.wrapper_bytes)
        self.assertEqual(
            "90c5a778b1ed789042151c7aa28d45f3eab790b0df20ad9e4b10da5ce19cbfd5",
            result.wrapper_identity["sha256"],
        )
        draft = json.loads(result.draft_bytes)
        interpretation, question = GuidedIntakeController._validate_draft(
            draft,
            original=result.wrapper_bytes.decode("utf-8"),
            request_sha256=result.wrapper_identity["sha256"],
            confirmations=[],
        )
        self.assertIsNone(question)
        self.assertEqual("PRESERVED", interpretation["objective"]["fidelity_status"])
        self.assertEqual("TESTABLE", interpretation["completion_line"]["testability_status"])
        self.assertEqual("NONE", interpretation["authority_claim"])

    def test_payload_is_exact_and_all_generated_support_is_outside_it(self) -> None:
        source = ORDINARY_SOURCE.read_bytes()
        result = compile_source(source)
        wrapper = result.wrapper_bytes.decode("utf-8")
        boundary = _quoted_payload_boundary(wrapper)
        self.assertIsNotNone(boundary)
        self.assertEqual(
            source,
            result.wrapper_bytes[
                boundary.payload_byte_start : boundary.payload_byte_end
            ],
        )
        draft = json.loads(result.draft_bytes)
        quotes = [
            draft["objective"]["atoms"][0]["support"][0]["quote"],
            draft["do_not_touch"][0]["support"]["quote"],
        ]
        for quote in quotes:
            self.assertLess(wrapper.index(quote), boundary.payload_char_start)

    def test_crlf_source_is_preserved_without_normalization(self) -> None:
        source = ORDINARY_SOURCE.read_bytes().replace(b"\n", b"\r\n")
        result = compile_source(source, "Contract.TXT")
        boundary = _quoted_payload_boundary(result.wrapper_bytes.decode("utf-8"))
        self.assertEqual(
            source,
            result.wrapper_bytes[
                boundary.payload_byte_start : boundary.payload_byte_end
            ],
        )

    def test_fail_closed_input_boundaries(self) -> None:
        source = ORDINARY_SOURCE.read_bytes()
        self.assert_code("PREP_UNSUPPORTED_EXTENSION", source, "Contract.pdf")
        self.assert_code("PREP_INVALID_UTF8", b"\xff\n")
        self.assert_code("PREP_EMPTY_SOURCE", b" \n")
        self.assert_code("PREP_SOURCE_TOO_LARGE", b"x" * 61_441 + b"\n")
        self.assert_code("PREP_SOURCE_BOUNDARY_UNREPRESENTABLE", source.rstrip(b"\n"))

    def test_fail_closed_profile_and_metadata_boundaries(self) -> None:
        source = ORDINARY_SOURCE.read_bytes()
        ambiguous = source.replace(
            b"\n---\n",
            b"\n# Initial Product Contract v0.1 \xe2\x80\x94 APPROVED CANDIDATE\n\n---\n",
            1,
        )
        self.assert_code("PREP_TITLE_INVALID", ambiguous)
        malformed = source.replace(b"Primary Layer:\nV9", b"Primary Layer:\nV8", 1)
        self.assert_code("PREP_METADATA_MALFORMED", malformed)
        duplicate = source.replace(
            b"Primary Layer:\nV9 \xe2\x80\x94 Product Adoption\n",
            b"Primary Layer:\nV9 \xe2\x80\x94 Product Adoption\nPrimary Layer:\nV9\n",
            1,
        )
        self.assert_code("PREP_METADATA_MALFORMED", duplicate)
        unsupported = source.replace(
            b"# Ordinary User Path Contract v0.1 \xe2\x80\x94 APPROVED CANDIDATE",
            b"# New Contract Family v0.1 \xe2\x80\x94 APPROVED CANDIDATE",
            1,
        )
        self.assert_code("PREP_UNSUPPORTED_CONTRACT_ROLE", unsupported)

    def test_unsupported_top_level_contract_cannot_borrow_later_evidence(self) -> None:
        source = ORDINARY_SOURCE.read_bytes().replace(
            b"# Ordinary User Path Contract v0.1 \xe2\x80\x94 APPROVED CANDIDATE",
            b"# Unsupported Contract v9.9 \xe2\x80\x94 APPROVED CANDIDATE",
            1,
        )
        embedded = source + (
            b"\n## Appendix: supported example\n\n"
            b"# Ordinary User Path Contract v0.1 \xe2\x80\x94 APPROVED CANDIDATE\n\n"
            b"Primary Layer:\nV9 \xe2\x80\x94 Product Adoption\n\n"
            b"Supporting Layer:\nV13 \xe2\x80\x94 Internal Governance\n\n"
            b"Implementation Authority:\nNONE\n\n"
            b"This Contract does not authorize repository changes, implementation, merge,\n"
            b"release, publication, model invocation, or rollout.\n"
        )

        self.assert_code("PREP_UNSUPPORTED_CONTRACT_ROLE", embedded)

    def test_supported_title_inside_fenced_code_is_not_profile_evidence(self) -> None:
        source = (
            b"# Decision-OS V9\n\n```markdown\n"
            b"# Ordinary User Path Contract v0.1 \xe2\x80\x94 APPROVED CANDIDATE\n\n"
            b"Primary Layer:\nV9 \xe2\x80\x94 Product Adoption\n\n"
            b"Supporting Layer:\nV13 \xe2\x80\x94 Internal Governance\n\n"
            b"Implementation Authority:\nNONE\n"
            b"```\n\n---\n"
        )

        self.assert_code("PREP_TITLE_INVALID", source)

    def test_quoted_appendix_is_not_profile_or_metadata_evidence(self) -> None:
        source = (
            b"# Decision-OS V9\n\n## Appendix\n\n"
            b"> # Ordinary User Path Contract v0.1 \xe2\x80\x94 APPROVED CANDIDATE\n>\n"
            b"> Primary Layer:\n> V9 \xe2\x80\x94 Product Adoption\n>\n"
            b"> Supporting Layer:\n> V13 \xe2\x80\x94 Internal Governance\n>\n"
            b"> Implementation Authority:\n> NONE\n>\n"
            b"> This Contract does not authorize repository changes, implementation, merge,\n"
            b"> release, publication, model invocation, or rollout.\n"
        )

        self.assert_code("PREP_TITLE_INVALID", source)

    def test_wrapper_and_draft_self_checks_have_exact_fail_closed_codes(self) -> None:
        source = ORDINARY_SOURCE.read_bytes()
        with patch(
            "decision_os.companion.ordinary_user_path._quoted_payload_boundary",
            return_value=None,
        ):
            self.assert_code("PREP_WRAPPER_IDENTITY_MISMATCH", source)

        cases = (
            ("invalid schema", "PREP_DRAFT_SCHEMA_INVALID"),
            ("HOLD — QUOTED PAYLOAD PROVENANCE SCOPE INVALID", "PREP_PROVENANCE_OVERLAP"),
            ("HOLD — OBJECTIVE FIDELITY FAILURE", "PREP_OBJECTIVE_FIDELITY_FAILED"),
            ("HOLD — COMPLETION LINE UNKNOWN", "PREP_COMPLETION_UNTESTABLE"),
            ("HOLD — MATERIAL UNKNOWN UNRESOLVED", "PREP_MATERIAL_UNKNOWN"),
            ("BLOCK — AUTHORITY INFLATION", "PREP_AUTHORITY_INFLATION"),
            ("HOLD — DO NOT TOUCH UNKNOWN", "PREP_DNT_CONFLICT"),
        )
        for message, code in cases:
            with self.subTest(code=code), patch.object(
                GuidedIntakeController,
                "_validate_draft",
                side_effect=GuidedIntakeValidationError(message),
            ):
                self.assert_code(code, source)

    def test_source_marker_injection_is_rejected_as_malformed_boundary(self) -> None:
        source = ORDINARY_SOURCE.read_bytes() + b"BEGIN EXACT PRODUCT CONTRACT\n"
        self.assert_code("PREP_WRAPPER_IDENTITY_MISMATCH", source)

    def test_compiler_has_no_model_network_runner_or_bridge_dependency(self) -> None:
        module_source = inspect.getsource(
            __import__(
                "decision_os.companion.ordinary_user_path",
                fromlist=["ContractFixationCompiler"],
            )
        )
        compiler_source = module_source[
            module_source.index("class ContractFixationCompiler") :
            module_source.index("def _empty_state")
        ]
        for forbidden in (
            "codex_adapter",
            "AccelerationEngine",
            "ManualBridge",
            "urllib",
            "requests",
            "socket",
        ):
            self.assertNotIn(forbidden, compiler_source)


if __name__ == "__main__":
    unittest.main()
