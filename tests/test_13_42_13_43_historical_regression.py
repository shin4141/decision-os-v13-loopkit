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
        b"# Current Signal \xe2\x80\x94 V13 Compact Test Output Reference "
        b"Implementation\n"
    ),
    "handoff/current_codex_handoff.md": (
        b"# Current Codex Handoff \xe2\x80\x94 V13 Compact Test Output Reference "
        b"Implementation\n"
    ),
}
PRE_13_42_CLOSURE_SHA256 = {
    "docs/current_signal.md": (
        "fc24d6ad23c5dc6895b5b8ad214c1765a5cac9434edf320e84df15c828da6089"
    ),
    "handoff/current_codex_handoff.md": (
        "d3dfe6700bdf7d6cf9c083f674626ebe73b2ccb345f8504425e1cd5a5561e511"
    ),
}
RECONSTRUCTED_MAIN = "5be89c84d1816a2b185cc2f6e85869a9f1e73d11"


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


class Historical13_42And13_43RegressionTests(unittest.TestCase):
    def test_fresh_reader_recovers_the_repaired_frontier_from_first_blocks(self) -> None:
        signal_block, handoff_block = [current_block(path) for path in SURFACES]
        self.assertEqual(signal_block, handoff_block)

        fields = parse_fields(signal_block)
        required_fields = {
            "canonical_reconstruction_base",
            "current_canonical_main",
            "current_layer",
            "v12_state",
            "13_42_closure",
            "completed_work",
            "canonical_current_capability",
            "current_restart_point",
            "active_branch",
            "current_gate",
            "v13_self_repair_research",
            "article_publication",
            "value_port",
            "known_baseline_boundary",
            "what_13_43_now_owns",
            "what_remains_parked",
            "what_must_not_be_inferred",
            "first_one_action",
            "do_not_continue_boundary",
            "operational_cleanup",
            "handoff_responsibility_transfer",
            "completion_line",
            "missing_closure",
            "next_authorized_action",
            "next_actor",
            "not_authorized",
            "decision_owner",
            "admission_joint",
            "admission_evidence",
            "remote_read_back",
            "older_material_below",
        }
        self.assertEqual(set(), required_fields.difference(fields))
        self.assertEqual(
            RECONSTRUCTED_MAIN,
            fields["canonical_reconstruction_base"][0],
        )
        self.assertTrue(fields["current_gate"][0].startswith("HOLD"))
        self.assertIn("13-43", fields["next_authorized_action"][0])
        self.assertTrue(fields["value_port"][0].startswith("EXTERNAL OWNERSHIP"))
        self.assertEqual("Shin", fields["decision_owner"][0])
        self.assertIn("Handoff is not complete until the receiving AI knows what it now owns.", signal_block)
        self.assertIn("codex/13-42-closure-13-43-handoff", signal_block)
        self.assertIn("Value-Locked side", signal_block)

    def test_repository_check_reads_only_the_new_current_authority(self) -> None:
        payload, exit_code = inspect_repository(REPO_ROOT)
        self.assertEqual(EXIT_OK, exit_code)
        self.assertEqual("PASS", payload["v12_state"])
        self.assertEqual("HOLD", payload["v13_gate"])
        self.assertIn("13-43", payload["next_authorized_action"])

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
        self.assertIn("Merge pull request #150", title)

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
        self.assertIn("current_canonical_main", fields)
        self.assertEqual(
            RECONSTRUCTED_MAIN,
            fields["canonical_reconstruction_base"][0],
        )
        self.assertTrue(fields["current_gate"][0].startswith("HOLD"))
        self.assertTrue(
            fields["canonical_current_capability"][0].startswith(
                "the repaired V13 lineage"
            )
        )
        self.assertIn("fetched merge descendant", fields["current_canonical_main"][0])
        self.assertTrue(fields["missing_closure"][0].startswith("none"))
        self.assertIn("fetched origin/main: 13-43", fields["next_authorized_action"][0])
        self.assertTrue(fields["completion_line"][0].startswith("PASS when"))

    def test_pre_13_42_closure_surfaces_remain_byte_preserved_history(self) -> None:
        for relative_path in SURFACES:
            with self.subTest(relative_path=relative_path):
                contents = (REPO_ROOT / relative_path).read_bytes()
                boundary = (
                    b"<!-- current-state-history-boundary:"
                    b"v13-13-42-closure -->\n"
                )
                self.assertEqual(1, contents.count(boundary))
                history_offset = contents.index(HISTORY_HEADERS[relative_path])
                history = contents[history_offset:]
                self.assertEqual(
                    PRE_13_42_CLOSURE_SHA256[relative_path],
                    hashlib.sha256(history).hexdigest(),
                )
                disclaimer = contents[:history_offset]
                self.assertIn(
                    b"cannot be inherited as current authority",
                    disclaimer,
                )
                self.assertIn(b"Next Authorized Action:", history)

    def test_13_43_handoff_transfers_responsibility_without_starting_work(self) -> None:
        handoff = (REPO_ROOT / "handoff/current_codex_handoff.md").read_text(
            encoding="utf-8"
        )
        transfer = handoff.split("## 13-43 Responsibility Transfer", 1)[1].split(
            "<!-- current-state-history-boundary:v13-13-42-closure -->", 1
        )[0]
        for required in (
            "Target Layer:",
            "Repo Root:",
            "Current State:",
            "Current Gate:",
            "Completion Line:",
            "Missing Closure:",
            "Next Owner:",
            "What the Receiving AI Now Owns:",
            "First One Action:",
            "Do Not Continue Boundary:",
            "What must not be inferred:",
            "Value port:",
            "Article:",
            "Operational cleanup that must not be returned to Shin:",
        ):
            self.assertIn(required, transfer)
        self.assertIn(
            "Handoff is not complete until the receiving AI knows what it now owns.",
            transfer,
        )
        self.assertIn("HOLD", transfer)
        self.assertIn("Value-Locked side", transfer)
        self.assertIn("do not begin implementation", transfer)

if __name__ == "__main__":
    unittest.main()
