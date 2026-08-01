from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from decision_os.companion.guided_intake import (
    DRAFT_SCHEMA,
    GuidedIntakeController,
    GuidedIntakeValidationError,
    sha256_bytes,
)
from decision_os.companion.ordinary_user_path import (
    ContractFixationCompiler,
    ContractFixationInput,
)


FIXTURE_ROOT = (
    Path(__file__).parent
    / "fixtures"
    / "guided_intake_quoted_payload_v0_1"
)
WRAPPER_FIXTURE = (
    FIXTURE_ROOT
    / "Decision_OS_Product_Contract_Fixation_Wrapper_v0.1.txt"
)
DRAFT_FIXTURE = (
    FIXTURE_ROOT
    / "Decision_OS_Product_Contract_Fixation_Wrapper_guided_intake_draft_v0.1.json"
)
CONTRACT_SHA256 = (
    "20be140f9ce3a4d3559ce53e1c8799460ea7f0acbe76c62c0c05a92a77ef1499"
)
WRAPPER_SHA256 = (
    "90c5a778b1ed789042151c7aa28d45f3eab790b0df20ad9e4b10da5ce19cbfd5"
)
BOUNDARY_INVALID = "HOLD — QUOTED PAYLOAD BOUNDARY INVALID"
PROVENANCE_INVALID = "HOLD — QUOTED PAYLOAD PROVENANCE SCOPE INVALID"


def _quote(value: str, occurrence: int = 1) -> dict[str, object]:
    return {
        "kind": "ORIGINAL_REQUEST_QUOTE",
        "quote": value,
        "occurrence": occurrence,
    }


def _quoted_request(
    payload: str,
    *,
    before_boundary: str = "",
    after_boundary: str = "",
) -> str:
    if not payload.endswith("\n"):
        raise ValueError("Test payloads must retain their trailing newline.")
    payload_bytes = payload.encode("utf-8")
    return (
        "# Quoted Payload Boundary Test\n\n"
        "Target Contract SHA-256:\n"
        f"{sha256_bytes(payload_bytes)}\n\n"
        "Target Contract UTF-8 bytes:\n"
        f"{len(payload_bytes)}\n\n"
        "Target Contract role:\n"
        "APPROVED PRODUCT CONTRACT\n\n"
        "Objective:\n"
        "Preserve the wrapper boundary.\n\n"
        "Completion Line:\n"
        "Complete when one boundary record exists and its hash verifies.\n\n"
        "Do Not Touch:\n"
        "Do not merge outside the quoted payload.\n\n"
        f"{before_boundary}"
        "BEGIN EXACT PRODUCT CONTRACT\n"
        f"{payload}"
        "END EXACT PRODUCT CONTRACT\n"
        f"{after_boundary}"
    )


def _clear_draft(request: str) -> dict[str, object]:
    return {
        "schema_version": DRAFT_SCHEMA,
        "source_request_sha256": sha256_bytes(request.encode("utf-8")),
        "objective": {
            "text": "Preserve the wrapper boundary.",
            "atoms": [
                {
                    "atom_id": "OBJ-1",
                    "text": "Preserve the wrapper boundary.",
                    "support": [_quote("Preserve the wrapper boundary.")],
                }
            ],
        },
        "completion_line": {
            "text": (
                "Complete when one boundary record exists and its hash "
                "verifies."
            ),
            "testability_status": "TESTABLE",
            "checks": [
                {
                    "observable": "One boundary record and its hash",
                    "pass_condition": (
                        "The record exists and its hash verifies"
                    ),
                    "evidence_source": "Boundary record hash",
                }
            ],
        },
        "do_not_touch": [
            {
                "item_id": "DNT-1",
                "text": "Do not merge outside the quoted payload.",
                "basis_kind": "USER_EXPLICIT",
                "support": _quote(
                    "Do not merge outside the quoted payload."
                ),
            }
        ],
        "unknown": [],
        "authority_claim": "NONE",
        "clarification_candidate": None,
    }


class QuotedPayloadBoundaryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = Path(self.temporary.name) / "repo"
        self.repository.mkdir()
        subprocess.run(
            ("git", "init", "-q"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "config", "user.email", "quoted@example.test"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "config", "user.name", "Quoted Payload Test"),
            cwd=self.repository,
            check=True,
        )
        (self.repository / "seed.txt").write_text("seed\n", encoding="utf-8")
        subprocess.run(
            ("git", "add", "seed.txt"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "commit", "-qm", "seed"),
            cwd=self.repository,
            check=True,
            env={
                **os.environ,
                "GIT_AUTHOR_DATE": "2026-07-31T00:00:00Z",
                "GIT_COMMITTER_DATE": "2026-07-31T00:00:00Z",
            },
        )
        identities = iter(f"quoted-{index}" for index in range(1, 500))
        self.controller = GuidedIntakeController(
            self.repository,
            clock=lambda: "2026-07-31T00:00:00Z",
            id_factory=lambda: next(identities),
        )

    def import_value(self, value: dict[str, object]) -> dict[str, object]:
        return self.controller.import_draft(
            json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        )

    def test_legacy_request_identity_gate_and_copy_prompt_are_unchanged(
        self,
    ) -> None:
        request = "Create one artifact. Do not merge."
        draft = {
            **_clear_draft(request),
            "objective": {
                "text": "Create one artifact.",
                "atoms": [
                    {
                        "atom_id": "OBJ-1",
                        "text": "Create one artifact.",
                        "support": [_quote("Create one artifact.")],
                    }
                ],
            },
            "do_not_touch": [
                {
                    "item_id": "DNT-1",
                    "text": "Do not merge.",
                    "basis_kind": "USER_EXPLICIT",
                    "support": _quote("Do not merge."),
                }
            ],
        }
        captured = self.controller.capture(request)
        imported = self.import_value(draft)
        copied = self.controller.copy_for_pro()

        self.assertEqual(captured["original_request"], request)
        self.assertEqual(
            captured["request_identity"]["sha256"],
            sha256_bytes(request.encode("utf-8")),
        )
        self.assertEqual(
            imported["interpretation"]["gate"],
            "CLEAR ENOUGH TO FREEZE",
        )
        self.assertNotIn(
            "Quoted Payload Boundary: VERIFIED",
            copied["copy_for_pro_prompt"],
        )

    def test_compiler_generated_product_wrapper_is_fixture_exact(self) -> None:
        wrapper = WRAPPER_FIXTURE.read_bytes()
        begin = b"BEGIN EXACT PRODUCT CONTRACT\n"
        end = b"END EXACT PRODUCT CONTRACT\n"
        source = wrapper[wrapper.index(begin) + len(begin) : wrapper.index(end)]
        repository_identity = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=self.repository,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        compiled = ContractFixationCompiler().compile(
            ContractFixationInput(
                source_bytes=source,
                filename="Decision_OS_Product_Contract.md",
                repository_path=str(self.repository),
                repository_identity=repository_identity,
                active_prior_request_id=None,
            )
        )
        self.assertEqual(wrapper, compiled.wrapper_bytes)
        self.assertEqual(CONTRACT_SHA256, compiled.source_identity["sha256"])
        self.assertEqual(WRAPPER_SHA256, compiled.wrapper_identity["sha256"])

    def test_verified_payload_operations_are_inert_but_outer_operations_are_active(
        self,
    ) -> None:
        payload = (
            "Implement the files. Execute Codex. Invoke Builder. "
            "Merge, release, and publish with authority.\n"
        )
        request = _quoted_request(payload)
        self.controller.capture(request)
        imported = self.import_value(_clear_draft(request))
        interpretation = imported["interpretation"]
        self.assertEqual(
            interpretation["objective"]["fidelity_status"],
            "PRESERVED",
        )
        self.assertEqual(interpretation["authority_claim"], "NONE")
        self.assertEqual(interpretation["gate"], "CLEAR ENOUGH TO FREEZE")

        active_request = _quoted_request(
            payload,
            after_boundary="Implement repository files now.\n",
        )
        active_id = imported["request_identity"]["request_id"]
        self.controller.capture(active_request, active_id)
        active = self.import_value(_clear_draft(active_request))
        self.assertEqual(
            active["interpretation"]["objective"]["fidelity_status"],
            "SUBSTITUTED",
        )
        self.assertEqual(
            active["interpretation"]["gate"],
            "HOLD — OBJECTIVE FIDELITY FAILURE",
        )

    def test_output_constraint_before_begin_matches_legacy_fidelity(
        self,
    ) -> None:
        legacy_request = (
            "Preserve the wrapper boundary. Output format: JSON only. "
            "Do not merge outside the quoted payload."
        )
        legacy = self.controller.capture(legacy_request)
        legacy_imported = self.import_value(_clear_draft(legacy_request))

        request = _quoted_request(
            "Quoted policy evidence only.\n",
            before_boundary="Output format: JSON only.\n",
        )
        self.controller.capture(
            request,
            legacy["request_identity"]["request_id"],
        )
        imported = self.import_value(_clear_draft(request))

        self.assertEqual(
            legacy_imported["interpretation"]["objective"][
                "fidelity_status"
            ],
            "SUBSTITUTED",
        )
        self.assertEqual(
            imported["interpretation"]["objective"]["fidelity_status"],
            legacy_imported["interpretation"]["objective"][
                "fidelity_status"
            ],
        )

    def test_output_constraint_after_end_matches_legacy_fidelity(
        self,
    ) -> None:
        legacy_request = (
            "Preserve the wrapper boundary. Output format: JSON only. "
            "Do not merge outside the quoted payload."
        )
        legacy = self.controller.capture(legacy_request)
        legacy_imported = self.import_value(_clear_draft(legacy_request))

        request = _quoted_request(
            "Quoted policy evidence only.\n",
            after_boundary="Output format: JSON only.\n",
        )
        self.controller.capture(
            request,
            legacy["request_identity"]["request_id"],
        )
        imported = self.import_value(_clear_draft(request))

        self.assertEqual(
            legacy_imported["interpretation"]["objective"][
                "fidelity_status"
            ],
            "SUBSTITUTED",
        )
        self.assertEqual(
            imported["interpretation"]["objective"]["fidelity_status"],
            legacy_imported["interpretation"]["objective"][
                "fidelity_status"
            ],
        )

    def test_outer_no_network_prohibition_cannot_be_omitted(self) -> None:
        request = _quoted_request(
            "Quoted policy evidence only.\n",
            before_boundary="No network access.\n",
        )
        self.controller.capture(request)
        omitted_draft = _clear_draft(request)
        omitted_draft["objective"]["atoms"][0]["support"].append(
            _quote("No network access.")
        )
        omitted = self.import_value(omitted_draft)
        self.assertTrue(omitted["interpretation"]["do_not_touch_conflict"])
        self.assertEqual(
            omitted["interpretation"]["gate"],
            "HOLD — DO NOT TOUCH UNKNOWN",
        )

        supported_draft = deepcopy(_clear_draft(request))
        supported_draft["do_not_touch"].append(
            {
                "item_id": "DNT-NETWORK",
                "text": "No network access.",
                "basis_kind": "USER_EXPLICIT",
                "support": _quote("No network access."),
            }
        )
        supported = self.import_value(supported_draft)
        self.assertFalse(
            supported["interpretation"]["do_not_touch_conflict"]
        )
        self.assertEqual(
            supported["interpretation"]["gate"],
            "CLEAR ENOUGH TO FREEZE",
        )

    def test_nonoperational_constraints_inside_payload_remain_inert(
        self,
    ) -> None:
        request = _quoted_request(
            "Output format: JSON only.\n"
            "One repository only.\n"
            "No network access.\n"
        )
        self.controller.capture(request)
        imported = self.import_value(_clear_draft(request))
        interpretation = imported["interpretation"]
        self.assertEqual(
            interpretation["objective"]["fidelity_status"],
            "PRESERVED",
        )
        self.assertFalse(interpretation["do_not_touch_conflict"])
        self.assertEqual(interpretation["gate"], "CLEAR ENOUGH TO FREEZE")

    def test_text_before_begin_and_after_end_cannot_be_hidden(self) -> None:
        payload = "Quoted policy evidence only.\n"
        current_id = None
        for location, extras in (
            ("before", {"before_boundary": "Execute Codex now.\n"}),
            ("after", {"after_boundary": "Publish the release now.\n"}),
        ):
            with self.subTest(location=location):
                request = _quoted_request(payload, **extras)
                captured = self.controller.capture(request, current_id)
                current_id = captured["request_identity"]["request_id"]
                imported = self.import_value(_clear_draft(request))
                self.assertEqual(
                    imported["interpretation"]["objective"][
                        "fidelity_status"
                    ],
                    "SUBSTITUTED",
                )

    def test_exact_wrapper_and_draft_qualify_without_identity_change(self) -> None:
        wrapper_bytes = WRAPPER_FIXTURE.read_bytes()
        draft_text = DRAFT_FIXTURE.read_text(encoding="utf-8")
        wrapper = wrapper_bytes.decode("utf-8")
        begin = b"BEGIN EXACT PRODUCT CONTRACT\n"
        end = b"END EXACT PRODUCT CONTRACT"
        payload = wrapper_bytes.split(begin, 1)[1].split(end, 1)[0]

        self.assertEqual(len(payload), 11909)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), CONTRACT_SHA256)
        self.assertEqual(len(wrapper_bytes), 12827)
        self.assertEqual(
            hashlib.sha256(wrapper_bytes).hexdigest(),
            WRAPPER_SHA256,
        )

        with patch(
            "decision_os.companion.guided_intake.subprocess.run",
            side_effect=AssertionError("Guided Intake started an action"),
        ):
            captured = self.controller.capture(wrapper)
            imported = self.controller.import_draft(draft_text)
            copied = self.controller.copy_for_pro()

        interpretation = imported["interpretation"]
        self.assertEqual(captured["original_request"], wrapper)
        self.assertEqual(captured["request_identity"]["byte_size"], 12827)
        self.assertEqual(
            captured["request_identity"]["sha256"],
            WRAPPER_SHA256,
        )
        self.assertEqual(
            interpretation["objective"]["fidelity_status"],
            "PRESERVED",
        )
        self.assertEqual(
            interpretation["completion_line"]["testability_status"],
            "TESTABLE",
        )
        self.assertEqual(interpretation["authority_claim"], "NONE")
        self.assertEqual(
            sum(
                entry["materiality"] == "MATERIAL"
                and entry["current_state"] == "OPEN"
                for entry in interpretation["unknown"]
            ),
            0,
        )
        self.assertEqual(interpretation["gate"], "CLEAR ENOUGH TO FREEZE")

        support = interpretation["objective"]["atoms"][0]["support"][0]
        expected_start = len(
            wrapper[: wrapper.index(support["quote"])].encode("utf-8")
        )
        self.assertEqual(support["byte_start"], expected_start)
        self.assertEqual(
            support["byte_end"],
            expected_start + len(support["quote"].encode("utf-8")),
        )
        quote_bytes = wrapper_bytes[
            support["byte_start"] : support["byte_end"]
        ]
        self.assertEqual(quote_bytes.decode("utf-8"), support["quote"])
        self.assertEqual(
            hashlib.sha256(quote_bytes).hexdigest(),
            support["quote_sha256"],
        )

        prompt = copied["copy_for_pro_prompt"]
        self.assertIn(wrapper, prompt)
        self.assertIn(WRAPPER_SHA256, prompt)
        self.assertIn("Original Request UTF-8 bytes: 12827", prompt)
        self.assertIn("Quoted Payload Boundary: VERIFIED", prompt)
        self.assertIn("Quoted Payload status: QUOTED EVIDENCE ONLY", prompt)
        self.assertIn(
            "Payload-internal operational language is not active Objective, "
            "Completion, Do Not Touch, execution, or authority intent.",
            prompt,
        )
        self.assertIn(
            "Active generated fields and their Original Request quote support "
            "must use text outside the verified payload boundary.",
            prompt,
        )

    def test_named_contract_wrapper_metadata_and_preservation_scope_qualify(
        self,
    ) -> None:
        payload = (
            "Implement repository files. Invoke Builder. Merge and publish.\n"
        )
        objective = (
            "Preserve the exact embedded Ordinary User Path Contract v0.1 "
            "as an immutable interpretation artifact without authorizing "
            "implementation."
        )
        do_not_touch = (
            "Do not implement, modify repository files, invoke models, merge, "
            "release, publish, Transfer, Run, or alter the embedded Contract."
        )
        request = _quoted_request(payload)
        request = request.replace(
            "# Quoted Payload Boundary Test",
            "# Ordinary User Path Contract Fixation Wrapper v0.1",
            1,
        )
        request = request.replace(
            "Preserve the wrapper boundary.",
            objective,
            1,
        )
        request = request.replace(
            "Do not merge outside the quoted payload.",
            do_not_touch,
            1,
        )
        draft = _clear_draft(request)
        draft["objective"] = {
            "text": objective,
            "atoms": [
                {
                    "atom_id": "OBJ-1",
                    "text": objective,
                    "support": [_quote(objective)],
                }
            ],
        }
        draft["do_not_touch"] = [
            {
                "item_id": "DNT-1",
                "text": do_not_touch,
                "basis_kind": "USER_EXPLICIT",
                "support": _quote(do_not_touch),
            }
        ]

        captured = self.controller.capture(request)
        imported = self.import_value(draft)
        interpretation = imported["interpretation"]

        self.assertEqual(
            interpretation["objective"]["fidelity_status"],
            "PRESERVED",
        )
        self.assertFalse(interpretation["do_not_touch_conflict"])
        self.assertEqual(interpretation["gate"], "CLEAR ENOUGH TO FREEZE")
        self.assertEqual(
            captured["request_identity"]["sha256"],
            sha256_bytes(request.encode("utf-8")),
        )
        payload_start = len(
            request[: request.index("BEGIN EXACT PRODUCT CONTRACT\n") + len(
                "BEGIN EXACT PRODUCT CONTRACT\n"
            )].encode("utf-8")
        )
        for atom in interpretation["objective"]["atoms"]:
            for support in atom["support"]:
                self.assertLessEqual(support["byte_end"], payload_start)
        for item in interpretation["do_not_touch"]:
            support = item.get("support")
            if support is not None:
                self.assertLessEqual(support["byte_end"], payload_start)

    def test_payload_only_active_field_provenance_fails_closed(self) -> None:
        objective_payload = "Implement the release now.\n"
        request = _quoted_request(objective_payload)
        self.controller.capture(request)
        objective_draft = _clear_draft(request)
        objective_draft["objective"] = {
            "text": "Implement the release now.",
            "atoms": [
                {
                    "atom_id": "OBJ-PAYLOAD",
                    "text": "Implement the release now.",
                    "support": [_quote("Implement the release now.")],
                }
            ],
        }
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            PROVENANCE_INVALID,
        ):
            self.import_value(objective_draft)

        dnt_payload = "Do not merge the quoted release.\n"
        active_id = self.controller.snapshot()["request_identity"]["request_id"]
        dnt_request = _quoted_request(dnt_payload)
        self.controller.capture(dnt_request, active_id)
        dnt_draft = _clear_draft(dnt_request)
        dnt_draft["do_not_touch"].append(
            {
                "item_id": "DNT-PAYLOAD",
                "text": "Do not merge the quoted release.",
                "basis_kind": "USER_EXPLICIT",
                "support": _quote("Do not merge the quoted release."),
            }
        )
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            PROVENANCE_INVALID,
        ):
            self.import_value(dnt_draft)

        unknown_payload = "Maybe publish this release.\n"
        active_id = self.controller.snapshot()["request_identity"]["request_id"]
        unknown_request = _quoted_request(unknown_payload)
        self.controller.capture(unknown_request, active_id)
        unknown_draft = _clear_draft(unknown_request)
        unknown_draft["unknown"] = [
            {
                "unknown_id": "UNK-PAYLOAD",
                "type": "USER_STATED_UNKNOWN",
                "statement": "Maybe publish this release.",
                "basis": {
                    "kind": "USER_STATEMENT",
                    "related_original_quotes": [
                        _quote("Maybe publish this release.")
                    ],
                },
                "affects": ["OBJECTIVE"],
                "materiality": "MATERIAL",
                "effect_on_execution": "NEEDS_USER_CONFIRMATION",
                "evidence_required": "An explicit active objective choice.",
                "current_state": "OPEN",
            }
        ]
        unknown_draft["clarification_candidate"] = {
            "field": "OBJECTIVE",
            "question": "Should this release be published?",
        }
        with self.assertRaisesRegex(
            GuidedIntakeValidationError,
            PROVENANCE_INVALID,
        ):
            self.import_value(unknown_draft)

    def test_every_malformed_envelope_form_fails_with_one_gate(self) -> None:
        payload = "Implement the quoted policy.\n"
        valid = _quoted_request(payload)
        digest = sha256_bytes(payload.encode("utf-8"))
        size = str(len(payload.encode("utf-8")))
        reversed_markers = (
            valid.replace(
                "BEGIN EXACT PRODUCT CONTRACT",
                "TEMP PRODUCT CONTRACT MARKER",
            )
            .replace(
                "END EXACT PRODUCT CONTRACT",
                "BEGIN EXACT PRODUCT CONTRACT",
            )
            .replace(
                "TEMP PRODUCT CONTRACT MARKER",
                "END EXACT PRODUCT CONTRACT",
            )
        )
        malformed = {
            "missing begin": valid.replace(
                "BEGIN EXACT PRODUCT CONTRACT\n", ""
            ),
            "missing end": valid.replace(
                "END EXACT PRODUCT CONTRACT\n", ""
            ),
            "duplicate begin": valid.replace(
                "BEGIN EXACT PRODUCT CONTRACT\n",
                "BEGIN EXACT PRODUCT CONTRACT\n"
                "BEGIN EXACT PRODUCT CONTRACT\n",
            ),
            "duplicate end": valid.replace(
                "END EXACT PRODUCT CONTRACT\n",
                "END EXACT PRODUCT CONTRACT\n"
                "END EXACT PRODUCT CONTRACT\n",
            ),
            "nested begin": valid.replace(
                payload,
                "BEGIN EXACT PRODUCT CONTRACT\n" + payload,
            ),
            "reversed markers": reversed_markers,
            "missing declaration": valid.replace(
                "Target Contract role:\nAPPROVED PRODUCT CONTRACT\n\n",
                "",
            ),
            "duplicate declaration": (
                "Target Contract role:\nAPPROVED PRODUCT CONTRACT\n\n"
                + valid
            ),
            "unsupported role": valid.replace(
                "APPROVED PRODUCT CONTRACT", "UNSUPPORTED CONTRACT"
            ),
            "invalid sha format": valid.replace(digest, digest.upper()),
            "invalid byte count": valid.replace(
                f"Target Contract UTF-8 bytes:\n{size}",
                "Target Contract UTF-8 bytes:\n0",
            ),
            "byte count mismatch": valid.replace(
                f"Target Contract UTF-8 bytes:\n{size}",
                f"Target Contract UTF-8 bytes:\n{int(size) + 1}",
            ),
            "sha mismatch": valid.replace(digest, "0" * 64),
            "marker not on own line": valid.replace(
                "BEGIN EXACT PRODUCT CONTRACT",
                "prefix BEGIN EXACT PRODUCT CONTRACT",
            ),
            "ambiguous declaration": valid.replace(
                "Target Contract SHA-256:",
                "prefix Target Contract SHA-256:",
            ),
            "extra payload bytes": valid.replace(
                "END EXACT PRODUCT CONTRACT",
                "extra byte\nEND EXACT PRODUCT CONTRACT",
            ),
        }

        current_id = None
        for name, request in malformed.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    GuidedIntakeValidationError,
                    BOUNDARY_INVALID,
                ):
                    self.controller.capture(request, current_id)


if __name__ == "__main__":
    unittest.main()
