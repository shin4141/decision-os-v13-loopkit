from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile
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


def run_git(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", "-C", str(cwd), *arguments),
        capture_output=True,
        check=True,
        text=True,
    )


class CurrentStateAdmissionTests(unittest.TestCase):
    def test_fresh_reader_recovers_the_repaired_frontier_from_first_blocks(self) -> None:
        signal_block, handoff_block = [current_block(path) for path in SURFACES]
        self.assertEqual(signal_block, handoff_block)

        fields = parse_fields(signal_block)
        required_fields = {
            "canonical_reconstruction_base",
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
            "admission_evidence",
            "remote_read_back",
            "13_198_p3_status",
            "older_material_below",
        }
        self.assertEqual(set(), required_fields.difference(fields))
        self.assertNotIn("current_canonical_main", fields)
        self.assertEqual(
            RECONSTRUCTED_MAIN,
            fields["canonical_reconstruction_base"][0],
        )
        self.assertTrue(fields["current_gate"][0].startswith("HOLD"))
        self.assertTrue(fields["next_authorized_action"][0].startswith("None. Stop."))
        self.assertTrue(fields["13_198_p3_status"][0].startswith("CLOSED"))
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
        self.assertEqual("HOLD", payload["v13_gate"])
        self.assertIn("None. Stop.", payload["next_authorized_action"])

    def test_reconstruction_base_is_real_and_ancestral(self) -> None:
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

    def test_post_merge_reader_on_origin_main_recovers_steady_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            source = parent / "source"
            remote = parent / "remote.git"
            reader = parent / "reader"

            run_git(parent, "init", "-b", "main", str(source))
            run_git(source, "config", "user.name", "Current State Test")
            run_git(source, "config", "user.email", "current-state@example.invalid")
            for relative_path in SURFACES:
                target = source / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((REPO_ROOT / relative_path).read_bytes())
            run_git(source, "add", "--", *SURFACES)
            run_git(source, "commit", "-m", "admit current state")

            run_git(parent, "init", "--bare", str(remote))
            run_git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
            run_git(source, "remote", "add", "origin", str(remote))
            run_git(source, "push", "-u", "origin", "main")
            run_git(parent, "clone", str(remote), str(reader))
            run_git(reader, "fetch", "origin", "main")

            observed_head = run_git(reader, "rev-parse", "origin/main").stdout.strip()
            observed_blocks = []
            for relative_path in SURFACES:
                text = run_git(
                    reader,
                    "show",
                    f"origin/main:{relative_path}",
                ).stdout
                block = first_fenced_block(text)
                self.assertIsNotNone(block)
                observed_blocks.append(block)

        self.assertEqual(observed_blocks[0], observed_blocks[1])
        self.assertNotEqual(RECONSTRUCTED_MAIN, observed_head)
        fields = parse_fields(observed_blocks[0] or "")
        self.assertNotIn("current_canonical_main", fields)
        self.assertEqual(
            RECONSTRUCTED_MAIN,
            fields["canonical_reconstruction_base"][0],
        )
        self.assertTrue(fields["current_gate"][0].startswith("HOLD"))
        self.assertTrue(fields["13_198_current_state_admission_repair"][0].startswith("COMPLETE"))
        self.assertTrue(fields["13_198_p3_status"][0].startswith("CLOSED"))
        self.assertNotIn("pending", fields["13_198_p3_status"][0].casefold())
        self.assertTrue(fields["missing_closure"][0].startswith("none"))
        self.assertNotIn("merge", fields["missing_closure"][0].casefold())
        self.assertNotIn("read-back", fields["missing_closure"][0].casefold())
        self.assertNotIn("Draft PR", fields["next_authorized_action"][0])
        self.assertNotIn("merge", fields["next_authorized_action"][0].casefold())
        self.assertNotIn("read-back", fields["next_authorized_action"][0].casefold())

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
