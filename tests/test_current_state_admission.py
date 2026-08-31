from __future__ import annotations

from pathlib import Path
import re
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
STABLE_ADMISSION_FIELDS = {
    "canonical_reconstruction_base",
    "current_canonical_main",
    "current_layer",
    "v12_state",
    "completed_work",
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
    "older_material_below",
}


def run_git(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", "-C", str(cwd), *arguments),
        capture_output=True,
        check=True,
        text=True,
    )


def validate_current_pair(blocks: tuple[str, str]) -> dict[str, tuple[str, ...]]:
    if blocks[0] != blocks[1]:
        raise AssertionError("the paired first current-state blocks differ")

    fields = parse_fields(blocks[0])
    missing = STABLE_ADMISSION_FIELDS.difference(fields)
    if missing:
        raise AssertionError(f"missing stable admission fields: {sorted(missing)}")

    for field in STABLE_ADMISSION_FIELDS:
        value = fields[field][0].strip()
        if value.upper().startswith("UNKNOWN"):
            reason = re.sub(r"^UNKNOWN(?:\s*[—–:\-]\s*)?", "", value, flags=re.I)
            if not reason.strip():
                raise AssertionError(f"{field}: UNKNOWN requires a concise reason")
    return fields


def first_blocks_from_worktree(repo_root: Path) -> tuple[str, str]:
    blocks = []
    for relative_path in SURFACES:
        text = (repo_root / relative_path).read_text(encoding="utf-8")
        block = first_fenced_block(text)
        if block is None:
            raise AssertionError(f"{relative_path}: first fenced block is absent")
        blocks.append(block)
    return blocks[0], blocks[1]


def admit_from_fetched_origin_main(
    repo_root: Path, expected_block: str
) -> dict[str, tuple[str, ...]]:
    remote_ref = "refs/remotes/origin/main"
    run_git(repo_root, "rev-parse", "--verify", remote_ref)
    blocks = []
    for relative_path in SURFACES:
        text = run_git(repo_root, "show", f"{remote_ref}:{relative_path}").stdout
        block = first_fenced_block(text)
        if block is None:
            raise AssertionError(
                f"{relative_path}: fetched origin/main has no current block"
            )
        blocks.append(block)

    fields = validate_current_pair((blocks[0], blocks[1]))
    if blocks[0] != expected_block:
        raise AssertionError("fetched origin/main does not contain the admitted block")

    reconstruction_base = fields["canonical_reconstruction_base"][0]
    relationship = subprocess.run(
        (
            "git",
            "-C",
            str(repo_root),
            "merge-base",
            "--is-ancestor",
            reconstruction_base,
            remote_ref,
        ),
        capture_output=True,
        check=False,
        text=True,
    )
    if relationship.returncode != 0:
        raise AssertionError(
            "Canonical Reconstruction Base is not an ancestor of fetched "
            f"origin/main: {relationship.stderr.strip()}"
        )
    return fields


def future_frontier_block(reconstruction_base: str) -> str:
    return f"""Canonical Reconstruction Base:
{reconstruction_base}

Current Canonical Main:
the fetched origin/main descendant containing this exact paired block

Current Layer:
V13 — synthetic future bounded task

V12 State:
PASS — the synthetic bounded task is complete

Completed Work:
one future bounded change

Canonical Current Capability:
the future bounded capability represented by this block

Current Restart Point:
this paired first block as read from fetched origin/main

Active Branch:
none after canonical admission

Current Gate:
HOLD — Human Seat selection remains required

Completion Line:
PASS after fetched origin/main read-back and ancestry verification

Missing Closure:
none after canonical admission

Next Authorized Action:
none

Not Authorized:
automatic next loop

Decision Owner:
Shin

Admission Joint:
exact paired block on fetched origin/main

Admission Evidence:
paired-surface read-back and ancestry verification

Remote Read-Back:
required before operational completion

Older Material Below:
HISTORICAL ONLY — preserved without rebaseline"""


class CurrentStateAdmissionTests(unittest.TestCase):
    def test_repository_frontier_satisfies_stable_generic_contract(self) -> None:
        fields = validate_current_pair(first_blocks_from_worktree(REPO_ROOT))
        self.assertEqual("Shin", fields["decision_owner"][0])
        self.assertTrue(fields["current_gate"][0].startswith("HOLD"))

        payload, exit_code = inspect_repository(REPO_ROOT)
        self.assertEqual(EXIT_OK, exit_code)
        self.assertEqual("PASS", payload["v12_state"])
        self.assertEqual("HOLD", payload["v13_gate"])

    def test_future_frontier_is_not_forced_to_use_13_42_fields(self) -> None:
        block = future_frontier_block("a" * 40)
        fields = validate_current_pair((block, block))
        self.assertEqual(STABLE_ADMISSION_FIELDS, set(fields))
        for historical_field in (
            "13_42_closure",
            "what_13_43_now_owns",
            "v13_self_repair_research",
            "value_port",
        ):
            self.assertNotIn(historical_field, fields)

    def test_candidate_branch_does_not_admit_until_origin_main_contains_it(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            source = parent / "source"
            remote = parent / "remote.git"
            reader = parent / "reader"

            run_git(parent, "init", "-b", "main", str(source))
            run_git(source, "config", "user.name", "Admission Contract Test")
            run_git(
                source,
                "config",
                "user.email",
                "admission-contract@example.invalid",
            )
            (source / "README.md").write_text("base\n", encoding="utf-8")
            run_git(source, "add", "README.md")
            run_git(source, "commit", "-m", "canonical reconstruction base")
            base = run_git(source, "rev-parse", "HEAD").stdout.strip()

            run_git(parent, "init", "--bare", str(remote))
            run_git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
            run_git(source, "remote", "add", "origin", str(remote))
            run_git(source, "push", "-u", "origin", "main")

            run_git(source, "switch", "-c", "candidate")
            block = future_frontier_block(base)
            for relative_path in SURFACES:
                target = source / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"# Current\n\n```text\n{block}\n```\n", encoding="utf-8")
            run_git(source, "add", "--", *SURFACES)
            run_git(source, "commit", "-m", "future admission candidate")
            run_git(source, "push", "-u", "origin", "candidate")

            run_git(parent, "clone", str(remote), str(reader))
            run_git(reader, "fetch", "origin")
            self.assertIn(
                block,
                run_git(reader, "show", "origin/candidate:docs/current_signal.md").stdout,
            )
            with self.assertRaises(subprocess.CalledProcessError):
                admit_from_fetched_origin_main(reader, block)

            run_git(source, "switch", "main")
            run_git(source, "merge", "--ff-only", "candidate")
            run_git(source, "push", "origin", "main")
            run_git(reader, "fetch", "origin", "main")
            admitted = admit_from_fetched_origin_main(reader, block)
            self.assertEqual(base, admitted["canonical_reconstruction_base"][0])

            non_ancestral_block = future_frontier_block("f" * 40)
            for relative_path in SURFACES:
                target = source / relative_path
                target.write_text(
                    f"# Current\n\n```text\n{non_ancestral_block}\n```\n",
                    encoding="utf-8",
                )
            run_git(source, "add", "--", *SURFACES)
            run_git(source, "commit", "-m", "declare non-ancestral base")
            run_git(source, "push", "origin", "main")
            run_git(reader, "fetch", "origin", "main")
            with self.assertRaisesRegex(AssertionError, "not an ancestor"):
                admit_from_fetched_origin_main(reader, non_ancestral_block)

    def test_unknown_requires_a_reason_but_remains_representable(self) -> None:
        unexplained = future_frontier_block("a" * 40).replace(
            "Current Restart Point:\nthis paired first block as read from fetched origin/main",
            "Current Restart Point:\nUNKNOWN",
        )
        with self.assertRaisesRegex(AssertionError, "UNKNOWN requires"):
            validate_current_pair((unexplained, unexplained))

        explained = unexplained.replace(
            "Current Restart Point:\nUNKNOWN",
            "Current Restart Point:\nUNKNOWN — source evidence is unavailable",
        )
        fields = validate_current_pair((explained, explained))
        self.assertTrue(fields["current_restart_point"][0].startswith("UNKNOWN"))

    def test_agents_defines_generic_admission_and_exact_remote_relationship(
        self,
    ) -> None:
        contract = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("### Current-State Admission Joint", contract)
        self.assertIn("stable\n   admission fields", contract)
        self.assertIn("Task-specific fields may be added", contract)
        self.assertIn("preserves every\nolder block", contract)
        self.assertIn("separately named historical", contract)
        self.assertIn("declared Canonical\n   Reconstruction Base is an ancestor", contract)
        self.assertIn("exact admitted change on fetched `origin/main`", contract)
        self.assertIn("branch, commit, pushed artifact, or PR", contract)

    def test_agents_has_deterministic_routed_document_precedence(self) -> None:
        contract = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        handoff = (REPO_ROOT / "docs/handoff_command.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("controlling repository instruction surface", contract)
        self.assertIn("binding only within the scope delegated", contract)
        self.assertIn("does not override `AGENTS.md`", contract)
        self.assertIn("shorter summary here does not waive", contract)
        self.assertIn("## Required Output Fields", handoff)
        self.assertIn("What must not be returned to the Decision Owner", handoff)

    def test_fn060_and_fn100_are_folded_evidence_not_canon_authority(self) -> None:
        contract = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        fn060 = (
            REPO_ROOT / "field_notes/060_v13_active_and_parked_lines_status_review.md"
        ).read_text(encoding="utf-8")
        fn100 = (REPO_ROOT / "field_notes/100_session_size_context_risk.md").read_text(
            encoding="utf-8"
        )
        for note in (fn060, fn100):
            self.assertIn("Status: Folded", note)
            self.assertIn("origin and trajectory evidence", note)
            self.assertIn("no independent\nexecution or Gate authority", note)
            self.assertNotIn("Status: Canon-promoted", note)
        self.assertNotIn("| Separate active signals from parked horizons |", contract)
        self.assertNotIn("| Judge context-health risk |", contract)
        self.assertIn("Neither label creates execution authority or\nselects a Gate", contract)
        self.assertIn("cannot independently require, forbid, or block", contract)

    def test_operational_terms_are_defined_without_changing_gate_outcomes(self) -> None:
        contract = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("0.99 risk", contract)
        self.assertIn("material regression\n  risk", contract)
        self.assertIn("`UNKNOWN` remains valid", contract)
        self.assertIn("concise reason why it\nis unknown", contract)
        self.assertIn("GO / HOLD / CAP / BLOCK", contract)


if __name__ == "__main__":
    unittest.main()
