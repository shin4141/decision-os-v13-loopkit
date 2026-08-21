from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import unittest

from decision_os.checks import EXIT_OK, inspect_repository
from decision_os.state import first_fenced_block, parse_fields


REPO_ROOT = Path(__file__).resolve().parents[1]
SURFACES = (
    "docs/current_signal.md",
    "handoff/current_codex_handoff.md",
)
HISTORY_HEADERS = {
    "docs/current_signal.md": (
        b"# Current Signal \xe2\x80\x94 Same-Run Completion Evidence Invalidation Integration\n"
    ),
    "handoff/current_codex_handoff.md": (
        b"# Current Codex Handoff \xe2\x80\x94 Same-Run Completion Evidence "
        b"Invalidation Integration\n"
    ),
}
PRE_13_198_SHA256 = {
    "docs/current_signal.md": (
        "8b4049f14d3d74f255ee0ebde522eac293d5a6bf241f79bf61bc8a3d83a47548"
    ),
    "handoff/current_codex_handoff.md": (
        "8a362d1261d13f4f43bfcf5b8f88047590062f1c7cc28f0ca4490adede78679d"
    ),
}
RECONSTRUCTED_MAIN = "fb89a07e31ebbf947f4f95d2bafdb1153dc08d29"


def current_block(relative_path: str) -> str:
    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    block = first_fenced_block(text)
    if block is None:
        raise AssertionError(f"{relative_path}: first fenced block is absent")
    return block


class CurrentStateAdmissionTests(unittest.TestCase):
    def test_fresh_reader_recovers_the_repaired_frontier_from_first_blocks(self) -> None:
        signal_block, handoff_block = [current_block(path) for path in SURFACES]
        self.assertEqual(signal_block, handoff_block)

        fields = parse_fields(signal_block)
        required_fields = {
            "current_canonical_main",
            "current_layer",
            "v12_state",
            "completed_canonical_frontier",
            "canonical_current_capability",
            "current_restart_point",
            "active_branch",
            "current_gate",
            "completion_line",
            "missing_closure",
            "next_authorized_action",
            "not_authorized",
            "decision_owner",
            "admission_joint",
            "expected_canonicalization_identity",
            "remote_read_back",
            "13_198_p3_status",
            "older_material_below",
        }
        self.assertEqual(set(), required_fields.difference(fields))
        self.assertTrue(fields["current_canonical_main"][0].startswith("origin/main at "))
        self.assertIn(RECONSTRUCTED_MAIN, fields["current_canonical_main"][0])
        self.assertTrue(fields["current_gate"][0].startswith("CAP"))
        self.assertEqual("Shin", fields["decision_owner"][0])
        self.assertIn("13-197", signal_block)
        self.assertIn("PR #146", signal_block)
        self.assertIn("13-198 Current-State Admission Repair", signal_block)
        self.assertNotIn("5d937fb3f1a123efc6a5d04727547d9c137c63e3", signal_block)
        self.assertNotIn("codex/13-126-same-run-invalidation-integration", signal_block)
        self.assertNotIn("HOLD \xe2\x80\x94 NO NEXT AUTHORITY", signal_block)

    def test_repository_check_reads_only_the_new_current_authority(self) -> None:
        payload, exit_code = inspect_repository(REPO_ROOT)
        self.assertEqual(EXIT_OK, exit_code)
        self.assertEqual("PASS", payload["v12_state"])
        self.assertEqual("CAP", payload["v13_gate"])
        self.assertIn("Review the Draft PR", payload["next_authorized_action"])

    def test_reconstructed_main_is_real_and_ancestral(self) -> None:
        completed = subprocess.run(
            ("git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", RECONSTRUCTED_MAIN, "HEAD"),
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        title = subprocess.run(
            ("git", "-C", str(REPO_ROOT), "show", "-s", "--format=%s", RECONSTRUCTED_MAIN),
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
        self.assertIn("13-197-git-authority-isolation-repair", title)

    def test_pre_13_198_surfaces_remain_byte_preserved_history(self) -> None:
        for relative_path in SURFACES:
            with self.subTest(relative_path=relative_path):
                contents = (REPO_ROOT / relative_path).read_bytes()
                boundary = b"<!-- current-state-history-boundary:13-198 -->\n"
                self.assertEqual(1, contents.count(boundary))
                history_offset = contents.index(HISTORY_HEADERS[relative_path])
                history = contents[history_offset:]
                self.assertEqual(
                    PRE_13_198_SHA256[relative_path],
                    hashlib.sha256(history).hexdigest(),
                )
                disclaimer = contents[:history_offset]
                self.assertIn(
                    b"cannot be\ninherited as current authority",
                    disclaimer,
                )
                self.assertIn(b"Next Authorized Action:", history)

    def test_agents_contract_blocks_complete_before_remote_admission(self) -> None:
        contract = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("### Current-State Admission Joint", contract)
        self.assertIn("not operationally `COMPLETE`", contract)
        self.assertIn("keep the two first fenced blocks byte-identical", contract)
        self.assertIn("after canonicalization, fetch `origin/main`", contract)
        self.assertIn("A pushed repair branch or Draft PR proves remote delivery", contract)
        self.assertIn("test_current_state_admission.py", contract)


if __name__ == "__main__":
    unittest.main()
