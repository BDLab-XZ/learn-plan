from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_planning.plan_renderer import build_plan_report, render_plan, review_public_plan_markdown


class PlanMarkdownHygieneTest(unittest.TestCase):
    def test_render_plan_outputs_public_four_section_contract(self) -> None:
        sections = {
            "学习画像": """
- 学习主题：Python
- 当前 workflow mode：finalize
- 用户模型：
  - 画像：有一点 Python 基础，希望面向数据科学和大模型应用岗位。
  - 已知优势：能理解变量、列表和基础表达式。
  - 已知薄弱点：return / print / None 的边界不稳。
  - 已知薄弱点：{'id': 'q1', 'prompt': '请解释下面很长的诊断题干'}
  - 已掌握范围：变量与列表基础。
- planning state：
  - deepsearch 状态：complete
""",
            "能力指标与起点判断": """
- 核心分析：
  - 目标要求：能独立写出可测试的 Python 数据处理脚本。
  - 核心能力：函数抽象；返回值契约；文件读写；异常处理。
- 诊断摘要：
  - 推荐起步层级：Python 基础函数阶段。
""",
            "检索结论与取舍": """
- 当前 research questions：
  - 应该查哪些候选路径？
- 能力要求报告：
  - 岗位侧会看能否把脚本写成稳定函数，并用测试说明边界。
""",
            "阶段总览": """
### 阶段 1：函数与数据结构
- 阶段摘要：先把函数、返回值、列表/字典处理打牢。
""",
            "阶段路线图": """
### 阶段 1
- 阶段目标：能把重复逻辑封装成函数。
- 重点小节：
  - 参数
  - return
""",
            "每日推进表": """
### Day 1
- 当前阶段：阶段 1
- 今日主题：函数 return 与 None
- 新学习点：return；None；测试断言
- 练习重点：函数代码题
""",
            "学习记录": "- 下次复习重点：return 与 print 的区别。",
            "测试记录": "- 薄弱项：隐藏测试下返回 None。",
        }

        markdown = render_plan("Python", "进入数据科学/大模型应用岗位", "基础", "每天 30 分钟", "案例化", sections)

        for heading in ("## 学习目标", "## 用户画像", "## 学习路线", "## 学习安排"):
            self.assertIn(heading, markdown)
        for old_heading in ("## 学习画像", "## 规划假设与约束", "## 检索结论与取舍", "## 每日推进表"):
            self.assertNotIn(old_heading, markdown)
        forbidden = (
            "workflow mode",
            "planning state",
            "deepsearch 状态",
            "research questions",
            "quality_review",
            "generation_trace",
            "traceability",
            "missing_artifact",
            "{'id':",
        )
        for token in forbidden:
            self.assertNotIn(token, markdown)
        self.assertEqual(review_public_plan_markdown(markdown), [])

    def test_public_hygiene_reviewer_flags_internal_tokens_and_raw_repr(self) -> None:
        bad_markdown = """
# Learn Plan

## 学习目标
- 当前 workflow mode：finalize
- {'id': 'q1', 'title': 'raw dict'}

## 用户画像
- planning state：ready

## 学习路线
- generation_trace: {}

## 学习安排
- missing_artifact: planning_candidate
"""

        issues = review_public_plan_markdown(bad_markdown)

        self.assertIn("public-plan.internal-token", issues)
        self.assertIn("public-plan.raw-python-repr", issues)

    def test_plan_report_normalizes_string_fields_without_character_bullets(self) -> None:
        report = build_plan_report(
            {
                "mode": "finalize",
                "goal_model": {"mainline_goal": "写出稳定 Python 脚本"},
                "research_report": {
                    "must_master_core": "函数返回值契约",
                    "must_master_capabilities": "函数返回值契约",
                    "evidence_expectations": "能通过隐藏测试说明边界",
                },
            },
            {
                "stages": [
                    {
                        "name": "阶段 1",
                        "focus": "函数",
                        "goal": "掌握 return",
                        "reading": [],
                        "exercise_types": [],
                        "test_gate": "通过代码题",
                    }
                ]
            },
        )

        self.assertEqual(report["research_core_summary"]["must_master_core"], ["函数返回值契约"])
        self.assertEqual(report["must_master"], ["函数返回值契约"])
        self.assertEqual(report["research_core_summary"]["evidence_expectations"], ["能通过隐藏测试说明边界"])


if __name__ == "__main__":
    unittest.main()
