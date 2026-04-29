"""复现课件质量 gap：真实生成的 lesson-html.json 违反三幕式约束。"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_runtime.lesson_html_validation import validate_lesson_html_json


class LessonHtmlQualityTest(unittest.TestCase):
    def _valid_three_part_json(self) -> dict:
        return {
            "title": "测试",
            "sections": [
                {
                    "type": "body",
                    "title": "Part 1 往期复习",
                    "content": "上一期完成了 clean_records，错题集中在 hashable 和 pytest 边界测试。本期从这些复习债继续推进。" * 8,
                },
                {
                    "type": "body",
                    "title": "Part 2 本期知识点讲解",
                    "content": "通过 `safe_int(value)` 和 `group_by_key(records, key)` 讲解函数契约、字典分组与边界测试。\n\n- 先观察失败输入\n- 再写契约\n- 最后用 pytest 固定边界" * 8,
                },
                {
                    "type": "body",
                    "title": "Part 3 本期内容回看",
                    "content": "参考资料：Python编程：从入门到实践（第3版）第 8 章 P.194，原文摘录：函数所做的任何修改都只影响副本；Python 官方文档 Tutorial: Data Structures section dictionaries；pytest 官方文档 Getting Started paragraph 2，key_quote：Use the assert statement。回看重点是函数返回值、dict key 和 assert。" * 4,
                },
            ],
        }

    def test_valid_three_part_json_passes(self):
        result = validate_lesson_html_json(self._valid_three_part_json())
        self.assertTrue(result["valid"], f"三段教学框架 JSON 应通过校验，issues={result['issues']}")

    def test_rejects_missing_review_part(self):
        data = self._valid_three_part_json()
        data["sections"] = data["sections"][:2]
        result = validate_lesson_html_json(data)
        self.assertFalse(result["valid"])
        self.assertTrue(any("本期内容回看" in issue for issue in result["issues"]))

    def test_rejects_missing_source_grounding(self):
        data = self._valid_three_part_json()
        data["sections"][2]["content"] = "Part 3 本期内容回看：回去看看相关内容。" * 20
        result = validate_lesson_html_json(data)
        self.assertFalse(result["valid"])
        self.assertTrue(any("来源 grounding" in issue for issue in result["issues"]))

    def test_allows_many_sections_and_lists(self):
        data = self._valid_three_part_json()
        data["sections"].extend([
            {"type": "body", "title": "补充案例", "content": "- 条件一\n- 条件二\n- 条件三"},
            {"type": "summary", "title": "检查", "items": [{"title": "掌握", "text": "能解释契约。"}]},
        ])
        result = validate_lesson_html_json(data)
        self.assertTrue(result["valid"], f"不应因 section 数量或列表失败，issues={result['issues']}")


if __name__ == "__main__":
    unittest.main()
