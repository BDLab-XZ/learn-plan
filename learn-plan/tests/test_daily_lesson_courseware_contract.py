from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_runtime.lesson_builder import (
    build_daily_lesson_plan,
    build_daily_lesson_prompt,
    build_lesson_quality_artifact,
    build_lesson_review,
    render_daily_lesson_plan_markdown,
)


class DailyLessonCoursewareContractTest(unittest.TestCase):
    def _plan_source(self) -> dict[str, object]:
        return {
            "current_stage": "Python 基础",
            "day": "Day 1",
            "today_topic": "函数抽象",
            "mainline_goal": "用 Python 完成数据处理脚本",
            "new_learning": ["函数参数", "返回值"],
            "review": ["变量与列表"],
            "exercise_focus": ["函数改写题"],
            "preference_state": {"teaching_pattern": "lecture-first"},
        }

    def _segments(self) -> list[dict[str, object]]:
        return [
            {
                "segment_id": "seg-func",
                "label": "函数抽象",
                "material_title": "Python 教程",
                "material_source_name": "Python 教程",
                "material_kind": "tutorial",
                "source_status": "extracted",
                "source_summary": "函数用于封装重复逻辑；参数用于传入变化数据；返回值用于交付结果",
                "source_key_points": ["函数参数", "返回值"],
                "source_examples": ["老板要求小林把三段重复清洗逻辑改成一个函数"],
                "source_pitfalls": ["只打印结果而不返回值"],
                "locator": {"chapter": "函数", "sections": ["定义函数"]},
            }
        ]

    def test_daily_lesson_builds_case_courseware_sections(self) -> None:
        plan = build_daily_lesson_plan(
            "Python",
            self._plan_source(),
            self._segments(),
            {"reading_checklist": ["解释函数参数和返回值"]},
        )

        courseware = plan.get("case_courseware")
        self.assertIsInstance(courseware, dict)
        self.assertTrue(courseware.get("knowledge_preview_flashcards"))
        self.assertTrue(courseware.get("case_background"))
        self.assertTrue(courseware.get("guided_story_practice"))
        self.assertTrue(courseware.get("review_sources"))
        self.assertFalse(courseware.get("exercise_policy", {}).get("embedded_questions"))

    def test_lesson_quality_review_requires_courseware_not_embedded_questions(self) -> None:
        artifact = build_lesson_quality_artifact(
            {
                "materials_used": [{"material_title": "Python 教程", "locator": "函数"}],
                "today_focus": {"focus_points": [{"point": "函数参数", "mastery_check": "能解释参数"}]},
                "project_driven_explanation": {"tasks": [{"task_name": "改写清洗逻辑", "real_context": "小林收到清洗任务", "blocker": "重复逻辑", "knowledge_points": ["函数参数"]}]},
                "review_suggestions": {"today_review": ["复述函数参数"], "progress_review": ["变量与列表"]},
                "review_targets": ["函数参数"],
            }
        )
        issues = artifact.get("quality_review", {}).get("issues", [])
        self.assertNotIn("today-lesson.case-courseware-missing", issues)
        self.assertNotIn("today-lesson.embedded-practice-questions", issues)

    def test_markdown_renders_case_courseware_as_public_courseware(self) -> None:
        plan = build_daily_lesson_plan(
            "Python",
            self._plan_source(),
            self._segments(),
            {"reading_checklist": ["解释函数参数和返回值"]},
        )

        markdown = render_daily_lesson_plan_markdown(plan)

        for heading in ("## 课前知识预告", "## 案例背景", "## 问题", "## 跟着案例学", "## 回看资料"):
            self.assertIn(heading, markdown)
        self.assertNotIn("主人公遇到的问题", markdown)
        self.assertIn("练习题由独立题目模块生成", markdown)
        self.assertNotIn("## 今日练习安排", markdown)
        self.assertNotIn("## 项目驱动的知识点讲解和相关扩展", markdown)

    def test_lesson_review_rejects_hollow_case_courseware(self) -> None:
        review = build_lesson_review(
            {
                "materials_used": [{"material_title": "Python 教程", "locator": "函数", "match_reason": "return"}],
                "today_focus": {"focus_points": [{"point": "return", "mastery_check": "能解释 return"}]},
                "project_driven_explanation": {"tasks": [{"task_name": "修复 None", "real_context": "代码题返回 None", "blocker": "只 print", "knowledge_points": ["return"]}]},
                "review_suggestions": {"today_review": ["复述 return"], "progress_review": ["函数基础"]},
                "review_targets": ["return"],
                "case_courseware": {
                    "knowledge_preview_flashcards": [{"front": "return", "prompt": "今天学什么"}],
                    "case_background": {"situation": "", "problem_to_solve": ""},
                    "guided_story_practice": [{"scene": "修复 None", "challenge": "", "teaching_move": "", "resolution": ""}],
                    "review_sources": [{"material_title": "Python 教程"}],
                    "exercise_policy": {"embedded_questions": False},
                },
            }
        )

        self.assertIn("today-lesson.case-background-hollow", review["issues"])
        self.assertIn("today-lesson.guided-practice-hollow", review["issues"])
        self.assertIn("today-lesson.flashcard-mastery-check-missing", review["issues"])
        self.assertIn("today-lesson.review-source-incomplete", review["issues"])

    def test_prompt_demands_case_courseware_without_embedded_exercises(self) -> None:
        prompt = build_daily_lesson_prompt({}, {"title": "Day 1"})

        self.assertIn("case_courseware", prompt)
        self.assertIn("knowledge_preview_flashcards", prompt)
        self.assertIn("case_background", prompt)
        self.assertIn("guided_story_practice", prompt)
        self.assertIn("review_sources", prompt)
        self.assertIn("练习题由独立题目模块生成", prompt)


if __name__ == "__main__":
    unittest.main()
