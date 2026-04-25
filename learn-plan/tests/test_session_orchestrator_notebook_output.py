from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from session_orchestrator import write_daily_lesson_plan


class SessionOrchestratorNotebookOutputTest(unittest.TestCase):
    def test_write_daily_lesson_plan_defaults_to_notebook_and_keeps_markdown_companion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / "learn-plan.md"
            plan_path.write_text("# Learn Plan\n", encoding="utf-8")
            session_dir = root / "sessions" / "2026-04-25"
            session_dir.mkdir(parents=True)
            payload = {
                "date": "2026-04-25",
                "plan_source": {
                    "daily_lesson_plan": {
                        "title": "Day 1：return 与 None",
                        "current_stage": "阶段 1",
                        "today_focus": {"summary": "修复返回 None", "focus_points": [{"point": "return", "mastery_check": "能返回结果"}]},
                        "case_courseware": {
                            "knowledge_preview_flashcards": [{"front": "return", "prompt": "如何返回结果？", "mastery_check": "能写 return"}],
                            "case_background": {"protagonist": "学习者", "situation": "代码题打印正确但测试失败。", "problem_to_solve": "函数返回 None。"},
                            "guided_story_practice": [{"scene": "复现失败", "challenge": "只 print", "teaching_move": "引入 return", "resolution": "return 计算结果", "knowledge_points": ["return", "None"]}],
                            "review_sources": [{"material_title": "Python 教程", "locator": "函数", "review_focus": "return"}],
                            "exercise_policy": {"embedded_questions": False, "question_module": "练习题由独立题目模块生成"},
                        },
                    }
                },
            }

            artifact_path = write_daily_lesson_plan(plan_path, payload, session_dir)

            self.assertEqual(artifact_path.name, "learn-today-2026-04-25.ipynb")
            self.assertTrue(artifact_path.exists())
            self.assertTrue((root / "learn-today-2026-04-25.md").exists())
            self.assertEqual(payload["plan_source"]["daily_plan_artifact_path"], str(artifact_path))
            self.assertEqual(payload["plan_source"]["lesson_path"], str(artifact_path))
            self.assertEqual(payload["plan_source"]["lesson_markdown_path"], str(root / "learn-today-2026-04-25.md"))


if __name__ == "__main__":
    unittest.main()
