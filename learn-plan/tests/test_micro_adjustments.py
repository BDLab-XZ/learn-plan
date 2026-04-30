from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_feedback.plan_update_renderer import append_micro_adjustments
from learn_runtime.plan_source import make_plan_source_from_markdown_fallback


class MicroAdjustmentsTest(unittest.TestCase):
    def test_append_micro_adjustments_writes_low_risk_feedback_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "learn-plan.md"
            plan_path.write_text("# Learn Plan\n", encoding="utf-8")

            wrote = append_micro_adjustments(
                plan_path,
                {
                    "date": "2026-04-30",
                    "topic": "Python",
                    "user_feedback": {
                        "difficulty": "降低题目跨度",
                        "teaching_style": "多给代码例子",
                        "comments": ["少一点抽象类比"],
                    },
                },
            )

            text = plan_path.read_text(encoding="utf-8")
            self.assertTrue(wrote)
            self.assertIn("## 当前教学/练习微调", text)
            self.assertIn("- 难度微调：降低题目跨度", text)
            self.assertIn("- 讲解方式微调：多给代码例子", text)
            self.assertIn("结构性路线变化仍走课程调整审批", text)

    def test_plan_source_consumes_current_micro_adjustments(self) -> None:
        plan_text = """
# Learn Plan

## 用户画像

- 画像：正在学习 Python。
- 学习风格：案例讲解

## 当前教学/练习微调

### 2026-04-30 / Python
- 难度微调：降低题目跨度
- 讲解方式微调：多给代码例子
- 本次反馈：少一点抽象类比
- 适用范围：后续 /learn-today 与 /learn-test 默认采用；结构性路线变化仍走课程调整审批。

## 学习安排

### Day 1：闭包
- 当前阶段：阶段 1
- 今日主题：闭包
- 复习点：函数作用域
- 新学习点：闭包
- 练习重点：概念题
- 推荐材料：Python 教程
- 难度目标：concept easy
"""

        source = make_plan_source_from_markdown_fallback("Python", "today", None, plan_text, target_day="Day 1")

        self.assertIn("多给代码例子", source["preference_state"]["learning_style"])
        self.assertIn("少一点抽象类比", source["preference_state"]["learning_style"])
        self.assertIn("降低题目跨度", source["preference_state"]["practice_style"])
        self.assertEqual(source["preference_state"]["current_micro_adjustments"]["practice_style"], ["降低题目跨度"])


if __name__ == "__main__":
    unittest.main()
