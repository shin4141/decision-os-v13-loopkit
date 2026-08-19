from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class RepoGroundedExternalIntelligenceOnboardingTests(unittest.TestCase):
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
        positions = [onboarding.index(marker) for marker in markers]
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
