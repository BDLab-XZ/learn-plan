from __future__ import annotations

import unittest
from pathlib import Path


class LearnTodaySkillContractTest(unittest.TestCase):
    def test_skill_contract_describes_case_courseware_markdown(self) -> None:
        skill_path = Path.home() / ".claude/skills/learn-today/SKILL.md"
        text = skill_path.read_text(encoding="utf-8")

        for token in ("课前知识预告", "案例背景", "问题", "跟着案例学", "回看资料"):
            self.assertIn(token, text)
        self.assertIn("练习题由独立题目模块生成", text)
        self.assertIn("learn-today-YYYY-MM-DD.ipynb", text)
        self.assertIn("learn-today-YYYY-MM-DD.md", text)
        self.assertIn("case_courseware", text)
        self.assertNotIn("主人公遇到的问题", text)
        self.assertNotIn("今日练习安排", text)


if __name__ == "__main__":
    unittest.main()
