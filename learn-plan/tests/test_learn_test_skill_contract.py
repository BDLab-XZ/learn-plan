from __future__ import annotations

import unittest
from pathlib import Path


class LearnTestSkillContractTest(unittest.TestCase):
    def test_skill_contract_describes_scope_plan_question_review_flow(self) -> None:
        skill_path = Path.home() / ".claude/skills/learn-test/SKILL.md"
        text = skill_path.read_text(encoding="utf-8")

        for token in (
            "question-scope.json",
            "question-plan.json",
            "question-artifact.json",
            "question-review.json",
            "范围规划",
            "出题规划",
            "生成题目",
            "审题",
            "初始测试",
            "目的分析报告",
            "历史阶段测试",
            "learn-plan.md",
            "progress.json",
            "learner_model",
            "--question-scope-json",
            "--question-plan-json",
            "--question-artifact-json",
            "--question-review-json",
        ):
            self.assertIn(token, text)

        self.assertIn("test 不依赖 lesson artifact", text)
        self.assertNotIn("--lesson-html-json", text)
        self.assertNotIn("--lesson-artifact-json", text)


if __name__ == "__main__":
    unittest.main()
