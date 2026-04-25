from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_workflow.stage_llm import build_stage_candidate_prompt


class ClarificationProtocolTest(unittest.TestCase):
    def test_operator_docs_ban_userquestions_for_clarification(self) -> None:
        paths = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "docs" / "clarification-stage.md",
            SKILL_DIR / "docs" / "skill-operator-guide.md",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("AskUserQuestion", text, path)
            self.assertIn("UserQuestions", text, path)
            self.assertRegex(text, r"禁止|不使用")
            self.assertIn("自然语言", text, path)

    def test_clarification_candidate_prompt_forbids_userquestions_schema(self) -> None:
        prompt = build_stage_candidate_prompt(
            "clarification",
            topic="Python",
            goal="面试",
            level="基础",
            schedule="每天 30 分钟",
            preference="混合",
            context={},
        )

        self.assertIn("不要输出 AskUserQuestion/UserQuestions schema", prompt)
        self.assertIn("结构化 candidate patch", prompt)
        self.assertIn("questionnaire.mastery_preferences", prompt)


if __name__ == "__main__":
    unittest.main()
