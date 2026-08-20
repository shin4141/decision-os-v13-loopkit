from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class RepositoryDefaultClaimBoundaryTest(unittest.TestCase):
    def test_operator_explanation_answers_the_four_boundary_questions(
        self,
    ) -> None:
        readme = read("README.md")
        section = readme.split(
            "## Optional Companion: your coding agent asks once. "
            "The next Run remembers.",
            1,
        )[1].split("## Turn one AI incident", 1)[0]
        explanation = " ".join(section.split())

        self.assertIn(
            "permission for this repository, action, and exact path",
            explanation,
        )
        self.assertIn("Future proposed content may differ", explanation)
        self.assertIn("without showing the same diff again", explanation)
        self.assertIn(
            "does not bind future reuse to the current diff or content",
            explanation,
        )

    def test_guide_names_what_the_default_does_not_persist(self) -> None:
        guide = read("docs/verified_save_claude_mvp_v0_1.md")
        boundary = guide.split(
            "## Repository Default Authority Boundary",
            1,
        )[1].split("## Human Choice", 1)[0]

        for excluded_identity in (
            "exact diff",
            "proposed content",
            "future preimage",
            "prompt",
            "task identity",
            "purpose",
            "tool-use identity",
        ):
            self.assertIn(excluded_identity, boundary)


if __name__ == "__main__":
    unittest.main()
