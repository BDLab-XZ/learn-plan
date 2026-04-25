from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_runtime.plan_source import make_plan_source_from_markdown_fallback


class PlanSourcePublicHeadingsTest(unittest.TestCase):
    def test_public_headings_are_parsed_for_today_source(self) -> None:
        plan_text = """
# Learn Plan

## 学习目标

- 主线目标：用 Python 完成稳定的数据处理脚本。
- 支撑能力：函数返回值契约
- 支撑能力：文件读写与 JSON

## 用户画像

- 画像：有一点 Python 基础，正在补函数和数据处理。
- 已掌握范围：变量与列表基础
- 已知薄弱点：return / print / None 的边界不稳
- 学习风格：案例讲解
- 练习方式：练学练
- 交付偏好：课件 + 网页练习
- 推荐起步层级：Python 函数基础

## 学习路线

### 阶段 1：函数与数据结构
- 阶段目标：先把函数、返回值、列表/字典处理打牢。

## 学习安排

### Day 1：函数 return 与 None
- 当前阶段：阶段 1
- 今日主题：函数 return 与 None
- 复习点：变量；列表
- 新学习点：return；None；测试断言
- 练习重点：函数代码题；隐藏测试边界
- 推荐材料：Python 教程函数章节
- 难度目标：code easy

## 学习记录

- 下次复习重点：return 与 print 的区别。

## 测试记录

- 本次测试覆盖范围：变量；列表
- 薄弱项：隐藏测试下返回 None。
"""

        source = make_plan_source_from_markdown_fallback("Python", "today", None, plan_text, target_day="Day 1")

        self.assertEqual(source["current_stage"], "阶段 1")
        self.assertEqual(source["today_topic"], "函数 return 与 None")
        self.assertEqual(source["new_learning"], ["return", "None", "测试断言"])
        self.assertEqual(source["exercise_focus"], ["函数代码题", "隐藏测试边界"])
        self.assertEqual(source["goal_model"]["mainline_goal"], "用 Python 完成稳定的数据处理脚本。")
        self.assertIn("函数返回值契约", source["goal_model"]["supporting_capabilities"])
        self.assertIn("return / print / None 的边界不稳", source["user_model"]["weaknesses"])
        self.assertEqual(source["preference_state"]["teaching_pattern"], "practice-first")

    def test_old_headings_remain_compatible(self) -> None:
        plan_text = """
# Learn Plan

## 学习画像

- 用户模型：
  - 画像：旧版计划用户画像。
  - 已知薄弱点：函数参数
- 目标层级：
  - 主线目标：旧版主线目标
  - 支撑能力：函数参数
- 学习风格与练习方式：
  - 练习方式：先讲后练

## 每日推进表

### Day 1：函数参数
- 当前阶段：阶段 1
- 今日主题：函数参数
- 复习点：变量
- 新学习点：参数
- 练习重点：函数调用题
- 推荐材料：Python 教程
- 难度目标：concept easy
"""

        source = make_plan_source_from_markdown_fallback("Python", "today", None, plan_text, target_day="Day 1")

        self.assertEqual(source["today_topic"], "函数参数")
        self.assertEqual(source["goal_model"]["mainline_goal"], "旧版主线目标")
        self.assertIn("函数参数", source["user_model"]["weaknesses"])
        self.assertEqual(source["preference_state"]["teaching_pattern"], "lecture-first")


if __name__ == "__main__":
    unittest.main()
