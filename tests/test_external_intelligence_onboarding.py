from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class RepoGroundedExternalIntelligenceOnboardingTests(unittest.TestCase):
    def test_00_readme_first_contact_order_centers_external_intelligence(self) -> None:
        readme = read("README.md")
        markers = (
            "### The problem",
            "### What External Intelligence changes",
            "### What this repository supports",
            "### Try it in English — no fork required",
            "### まず試してみる — Fork不要",
            "## Next, if you need completion and loop gates",
        )
        positions = [readme.index(marker) for marker in markers]

        self.assertEqual(positions, sorted(positions))
        self.assertIn(
            "selected past decisions, failure boundaries,\n"
            "reusable knowledge, and restart context outside one chat",
            readme,
        )
        self.assertIn("later AI retrieves\nonly the prior structure that matters", readme)
        self.assertLess(
            readme.index("### What External Intelligence changes"),
            readme.index("context compactor"),
        )
        prompt_path = "copy-paste/external-intelligence-first-contact.md"
        self.assertIn(f"]({prompt_path})", readme)
        self.assertTrue((ROOT / prompt_path).is_file())

    def test_01_english_prompt_is_repo_first_read_only_and_no_fork(self) -> None:
        prompt = read("copy-paste/external-intelligence-first-contact.md")
        tutorial = read("docs/codex_tutorial_guide.md")

        self.assertEqual(prompt.count("```text"), 1)
        self.assertIn(
            "https://github.com/shin4141/decision-os-v13-loopkit", prompt
        )
        for path in (
            "README.md",
            "AGENTS.md",
            "docs/external_intelligence_onboarding.md",
            "docs/ai_reading_order.md",
            "docs/field_note_lifecycle.md",
        ):
            self.assertIn(f"- {path}", prompt)
            self.assertTrue((ROOT / path).is_file())

        for instruction in (
            "Inspect the actual public repository",
            "files you actually inspected",
            "could access and which\n   you could not access",
            "Do not infer unseen code, private implementation",
            '"English first-contact — External Intelligence Quest Board"',
            "do not fork or clone the repository",
            "modify files",
            "Until I select a Quest",
        ):
            self.assertIn(instruction, prompt)

        self.assertIn(
            "`English\n   first-contact — External Intelligence Quest Board`",
            tutorial,
        )
        self.assertIn(
            "Do not replace it with the completion checker, Handoff, Compactor, or\n"
            "Gate system as the repository's primary interpretation.",
            tutorial,
        )

    def test_02_english_and_japanese_boards_preserve_the_same_quest_boundaries(
        self,
    ) -> None:
        onboarding = read("docs/external_intelligence_onboarding.md")
        english = onboarding.split(
            "## English first-contact — External Intelligence Quest Board", 1
        )[1].split("## 日本語first-contact — External Intelligence Quest Board", 1)[0]
        japanese = onboarding.split(
            "## 日本語first-contact — External Intelligence Quest Board", 1
        )[1]

        english_markers = (
            "### 🧠 MEMORY — Remember",
            "### 🌱 GROW — Develop reusable knowledge",
            "### 🪶 LIGHTEN — Retrieve selectively",
            "### 🔁 CONTINUE — Resume safely",
            "### 🛡️ PROTECT — Keep boundaries visible",
            "### 🔗 CONNECT — Reuse across AIs",
            "### 🎓 GRADUATE — Choose the tutorial's future",
            "## 🎮 Choose Your Quest",
        )
        japanese_markers = (
            "### 🧠 MEMORY — 覚える",
            "### 🌱 GROW — 育てる",
            "### 🪶 LIGHTEN — 軽くする",
            "### 🔁 CONTINUE — 続ける・再開する",
            "### 🛡️ PROTECT — 守る",
            "### 🔗 CONNECT — AIをつなぐ",
            "### 🎓 GRADUATE — Tutorialを卒業する",
            "## 🎮 Choose Your Quest",
        )

        for board, markers in (
            (english, english_markers),
            (japanese, japanese_markers),
        ):
            positions = [board.index(marker) for marker in markers]
            self.assertEqual(positions, sorted(positions))
            for boundary in ("Fork", "clone", "file", "Handoff", "Note", "Rule"):
                self.assertIn(boundary.lower(), board.lower())

        english_lighten = english.split(
            "### 🪶 LIGHTEN — Retrieve selectively", 1
        )[1].split("### 🔁 CONTINUE — Resume safely", 1)[0]
        self.assertIn("Little Compactor", english_lighten)
        self.assertIn("not the\n  core meaning", english_lighten)
        self.assertIn("not proof of complete public implementation", english)
        self.assertIn("完全なimplementation", japanese)

    def test_a_primary_prompt_requires_repo_read_disclosure_and_full_board(self) -> None:
        readme = read("README.md")
        primary = readme.split("### まず試してみる — Fork不要", 1)[1].split(
            "### 🔓 Full Experience — Forkして体感する", 1
        )[0]

        self.assertEqual(primary.count("```text"), 1)
        self.assertIn(
            "https://github.com/shin4141/decision-os-v13-loopkit", primary
        )
        for path in (
            "README.md",
            "AGENTS.md",
            "docs/external_intelligence_onboarding.md",
            "docs/ai_reading_order.md",
            "docs/field_note_lifecycle.md",
        ):
            self.assertIn(f"- {path}", primary)
            self.assertTrue((ROOT / path).is_file())

        for instruction in (
            "この公開repositoryを実際に読んでから",
            "repositoryで確認できた内容だけ",
            "実際に確認できた範囲",
            "確認できなかった範囲",
            "全文表示してください",
            "私がQuestを選ぶまでは",
            "必要な範囲だけ先に確認してから説明してください",
            "分かったふりをせず、その境界を明示してください",
        ):
            self.assertIn(instruction, primary)

        onboarding = read("docs/external_intelligence_onboarding.md")
        japanese_board = onboarding.split(
            "## 日本語first-contact — External Intelligence Quest Board", 1
        )[1]
        markers = (
            "# 🧠 External Intelligence",
            "### 🧠 MEMORY — 覚える",
            "### 🌱 GROW — 育てる",
            "### 🪶 LIGHTEN — 軽くする",
            "### 🔁 CONTINUE — 続ける・再開する",
            "### 🛡️ PROTECT — 守る",
            "### 🔗 CONNECT — AIをつなぐ",
            "### 🎓 GRADUATE — Tutorialを卒業する",
            "## 🎮 Choose Your Quest",
        )
        positions = [japanese_board.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("確認できたもの:", onboarding)
        self.assertIn("現在確認できないもの:", onboarding)
        self.assertIn("access boundaryを最大数行", onboarding)
        self.assertIn("全Field Notesを先読みしません", onboarding)

    def test_user_evidence_gate_precedes_deep_read_and_recommendation(
        self,
    ) -> None:
        onboarding = read("docs/external_intelligence_onboarding.md")
        reading_order = read("docs/ai_reading_order.md")

        for text in (onboarding, reading_order):
            self.assertIn("fixed SHA", text)
            self.assertIn("audit", text)
            self.assertIn("これはもうやっている", text)
            self.assertIn("自分なら何が合いそう？", text)

        self.assertIn("deep readより先に、その対象だけを一問", onboarding)
        self.assertIn("結果を変える最小質問を一つだけ", onboarding)
        self.assertIn("Do not deep-read a guessed Quest first.", reading_order)
        self.assertIn(
            "Do not prescribe `CONTINUE`, handoff,\n  or another Quest",
            reading_order,
        )

    def test_little_osi_route_disambiguates_the_separate_osi_surface(
        self,
    ) -> None:
        reading_order = read("docs/ai_reading_order.md")
        little_osi = reading_order.split("### Little OSI", 1)[1].split(
            "### Other Quests", 1
        )[0]

        self.assertIn("Follow the `CONTINUE` route", little_osi)
        self.assertIn("docs/osi_parallel_compounding_lane_v0_1.md", little_osi)
        self.assertTrue((ROOT / "docs/osi_parallel_compounding_lane_v0_1.md").is_file())
        self.assertIn("same as Output Surface Integrity", little_osi)
        self.assertIn("simplified", little_osi)
        self.assertIn("completely unrelated", little_osi)

    def test_v13_loop_is_explained_as_a_next_cycle_gate_not_automation(
        self,
    ) -> None:
        onboarding = read("docs/external_intelligence_onboarding.md")

        self.assertIn(
            "このrepositoryのV13 LoopKitは、AIとの仕事で生まれた記憶・再開点・再利用できる\n"
            "知識を外部に残し、現在の作業が終わった後に次の作業へ進むべきかを判断するための\n"
            "運用OSです。",
            onboarding,
        )
        self.assertIn(
            "V13 Loop Gateは、自動で作業を繰り返す機能ではありません。現在のtaskが\n"
            "    終わった後、次の作業cycleを開始する正当性を`GO / HOLD / CAP / BLOCK`で\n"
            "    判断する境界です。",
            onboarding,
        )
        self.assertIn(
            "今の作業が終わっていても、次のloopを自動開始しません。",
            onboarding,
        )

    def test_b_lighten_routes_to_public_evidence_without_compactor_overclaim(
        self,
    ) -> None:
        reading_order = read("docs/ai_reading_order.md")
        lighten = reading_order.split("### LIGHTEN", 1)[1].split(
            "### CONTINUE", 1
        )[0]

        for path in (
            "docs/field_notes_lite_v0_1_design.md",
            "field_notes/048_lane_memory_event_triggered_recall.md",
            "field_notes/051_lane_recall_mini_protocol.md",
            "decision_os/companion/field_notes_reconnect.py",
            "docs/research_candidates/agents_md_reconnectable_compactor.md",
        ):
            self.assertIn(path, lighten)
            self.assertTrue((ROOT / path).is_file())

        self.assertIn("research candidate", lighten)
        self.assertIn("not evidence", lighten)
        onboarding = read("docs/external_intelligence_onboarding.md")
        self.assertIn(
            "実装詳細はここからは確認できません。",
            onboarding,
        )

    def test_c_continue_routes_to_actual_v12_v13_and_handoff_rules(self) -> None:
        reading_order = read("docs/ai_reading_order.md")
        continuation = reading_order.split("### CONTINUE", 1)[1].split(
            "### Other Quests", 1
        )[0]

        for path in (
            "AGENTS.md",
            "docs/handoff_command.md",
            "docs/context_compression.md",
            "field_notes/022_v12_to_v13_mapping.md",
            "field_notes/099_handoff_responsibility_transfer.md",
        ):
            self.assertIn(path, continuation)
            self.assertTrue((ROOT / path).is_file())

        self.assertIn("PASS / DELAY / BLOCK / UNKNOWN", continuation)
        self.assertIn("GO / HOLD / CAP / BLOCK", continuation)
        agents = read("AGENTS.md")
        self.assertIn("`PASS` does not automatically mean `GO`.", agents)

    def test_d_fork_cta_is_post_interest_and_preserves_availability_boundary(
        self,
    ) -> None:
        readme = read("README.md")
        onboarding = read("docs/external_intelligence_onboarding.md")

        for text in (readme, onboarding):
            self.assertIn("🔓 Full Experience — Forkして体感する", text)
            self.assertIn("private repository", text)
            self.assertIn("separate unpublished", text)
            self.assertIn("private memory", text)
            self.assertIn("public `main`", text)

        self.assertIn("Questの選択だけでForkへ進めません", readme)
        self.assertIn("説明または小さなtrialを受けた後", onboarding)
        self.assertIn("Forkは理解するための前提ではなく", onboarding)
        self.assertIn("その人がそこから育てる新しい状態", onboarding)


if __name__ == "__main__":
    unittest.main()
