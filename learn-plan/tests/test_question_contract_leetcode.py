from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_runtime.question_generation import build_question_reviewer_prompt, build_runtime_question_prompt
from learn_runtime.question_validation import validate_questions_payload
from learn_runtime.schemas import (
    MAX_FAILED_CASE_SUMMARIES,
    validate_code_question_contract,
    validate_objective_question_contract,
    validate_submit_result_contract,
    validate_test_grade_question,
)


class LeetCodeQuestionContractTest(unittest.TestCase):
    def _code_question(self) -> dict[str, object]:
        return {
            "id": "code-two-sum",
            "type": "code",
            "category": "code",
            "title": "两数之和：返回满足目标和的下标",
            "problem_statement": "实现 `two_sum(nums, target)`。\n\n**目标**：返回两个不同元素的下标，使它们的和等于 `target`。\n\n要求：\n- 不能重复使用同一个元素\n- 返回任意一个满足条件的下标组合",
            "input_spec": "`nums: list[int]`，长度 2 到 10^4；`target: int`。",
            "output_spec": "返回 `list[int]`，包含两个不同下标，顺序不限。",
            "constraints": ["每个输入恰好存在一个答案", "不能重复使用同一个元素"],
            "examples": [
                {
                    "input": {"nums": [2, 7, 11, 15], "target": 9},
                    "output": [0, 1],
                    "explanation": "nums[0] + nums[1] = 9。",
                }
            ],
            "public_tests": [
                {"kwargs": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1], "category": "public"}
            ],
            "hidden_tests": [
                {"kwargs": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2], "category": "hidden"}
            ],
            "starter_code": "def two_sum(nums, target):\n    pass\n",
            "function_signature": "two_sum(nums: list[int], target: int) -> list[int]",
            "function_name": "two_sum",
            "scoring_rubric": ["正确返回两个不同下标", "覆盖重复值和边界输入"],
            "capability_tags": ["array", "hash-map"],
            "source_trace": {"question_source": "test-fixture"},
            "explanation": "可用哈希表记录已访问数字。",
        }

    def _objective_question(self) -> dict[str, object]:
        return {
            "id": "choice-mutability",
            "type": "single_choice",
            "category": "concept",
            "title": "Python 列表可变性判断",
            "prompt": "以下哪个操作会原地修改列表 xs？",
            "options": ["xs.append(1)", "xs + [1]", "tuple(xs)", "xs.copy()"],
            "answer": 0,
            "explanation": "append 会原地修改列表，其他选项会创建新对象或转换对象。",
            "scoring_rubric": ["识别列表原地修改 API", "区分新对象创建与原地变更"],
            "capability_tags": ["python-list", "mutability"],
            "source_trace": {"question_source": "test-fixture"},
        }

    def _submit_result(self) -> dict[str, object]:
        return {
            "question_id": "code-two-sum",
            "question_type": "code",
            "status": "failed",
            "passed_public_count": 1,
            "total_public_count": 1,
            "passed_hidden_count": 0,
            "total_hidden_count": 1,
            "failed_case_summaries": [
                {
                    "category": "hidden",
                    "input": {"nums": [3, 2, 4], "target": 6},
                    "expected": [1, 2],
                    "actual": [0, 1],
                    "error": "wrong_answer",
                    "capability_tags": ["array", "hash-map"],
                }
            ],
            "failure_types": ["wrong_answer"],
            "capability_tags": ["array", "hash-map"],
            "submitted_at": "2026-04-25T02:00:00Z",
        }

    def test_canonical_code_question_contract_passes(self) -> None:
        self.assertEqual(validate_code_question_contract(self._code_question()), [])
        self.assertEqual(validate_test_grade_question(self._code_question()), [])

    def test_canonical_objective_question_contract_passes(self) -> None:
        self.assertEqual(validate_objective_question_contract(self._objective_question()), [])
        self.assertEqual(validate_test_grade_question(self._objective_question()), [])

    def test_open_written_questions_are_not_test_grade_by_default(self) -> None:
        question = {
            "id": "open-1",
            "type": "written",
            "category": "open",
            "question": "解释 Python GIL。",
            "prompt": "解释 Python GIL。",
            "reference_points": ["线程", "解释器锁"],
        }

        issues = validate_test_grade_question(question)
        self.assertIn("question.open_not_allowed_by_default", issues)

    def test_code_question_missing_required_leetcode_fields_fails(self) -> None:
        required_fields = (
            "problem_statement",
            "input_spec",
            "output_spec",
            "constraints",
            "examples",
            "hidden_tests",
            "scoring_rubric",
            "capability_tags",
        )
        for field in required_fields:
            with self.subTest(field=field):
                question = self._code_question()
                question.pop(field, None)
                issues = validate_code_question_contract(question)
                self.assertIn(f"question.code.{field}_missing", issues)

    def test_submit_result_contract_passes_and_caps_failed_case_summaries(self) -> None:
        self.assertEqual(validate_submit_result_contract(self._submit_result()), [])
        result = self._submit_result()
        result["failed_case_summaries"] = list(result["failed_case_summaries"]) * (MAX_FAILED_CASE_SUMMARIES + 1)

        issues = validate_submit_result_contract(result)
        self.assertIn("submit_result.failed_case_summaries_too_many", issues)

    def _questions_payload(self, question: dict[str, object]) -> dict[str, object]:
        return {
            "date": "2026-04-25",
            "topic": "Python",
            "mode": "test",
            "session_type": "test",
            "session_intent": "assessment",
            "assessment_kind": "stage-test",
            "test_mode": "general",
            "language_policy": {"user_facing_language": "zh-CN"},
            "plan_source": {
                "language_policy": {"user_facing_language": "zh-CN"},
                "lesson_grounding_context": {
                    "semantic_profile": "today",
                    "minimum_pass_shape": {},
                },
                "question_generation_mode": "agent-subagent",
                "strict_question_review": {"valid": True, "verdict": "pass", "issues": []},
                "deterministic_question_review": {"valid": True, "verdict": "pass", "issues": []},
            },
            "selection_context": {"language_policy": {"user_facing_language": "zh-CN"}},
            "materials": [],
            "questions": [question],
        }

    def test_validate_questions_payload_rejects_code_question_missing_test_grade_contract(self) -> None:
        question = self._code_question()
        question.pop("input_spec", None)

        review = validate_questions_payload(self._questions_payload(question))

        self.assertFalse(review.get("valid"))
        self.assertIn("code-two-sum: question.code.input_spec_missing", review.get("issues", []))

    def test_validate_questions_payload_rejects_one_paragraph_code_statement(self) -> None:
        question = self._code_question()
        question["problem_statement"] = "实现 two_sum 函数，接收 nums 和 target，返回两个不同元素下标，使它们的和等于 target，不能重复使用同一个元素，每个输入恰好存在一个答案。"

        review = validate_questions_payload(self._questions_payload(question))

        self.assertFalse(review.get("valid"))
        self.assertTrue(any("problem_statement 为纯文本一段到底" in issue for issue in review.get("issues", [])))

    def test_validate_questions_payload_rejects_semicolon_packed_constraints(self) -> None:
        question = self._code_question()
        question["constraints"] = "每个输入恰好存在一个答案；不能重复使用同一个元素；返回顺序不限"

        review = validate_questions_payload(self._questions_payload(question))

        self.assertFalse(review.get("valid"))
        self.assertTrue(any("constraints 必须用数组" in issue for issue in review.get("issues", [])))

    def test_validate_questions_payload_rejects_open_question_by_default(self) -> None:
        question = {
            "id": "open-1",
            "type": "written",
            "category": "open",
            "question": "解释 Python GIL。",
            "prompt": "解释 Python GIL。",
            "reference_points": ["线程", "解释器锁"],
            "source_trace": {"question_source": "test-fixture"},
        }

        review = validate_questions_payload(self._questions_payload(question))

        self.assertFalse(review.get("valid"))
        self.assertIn("open-1: question.open_not_allowed_by_default", review.get("issues", []))

    def test_runtime_question_prompt_requires_test_grade_questions(self) -> None:
        prompt = build_runtime_question_prompt(
            "Python",
            {"semantic_profile": "stage-test", "session_intent": "assessment", "assessment_kind": "stage-test"},
            {"plan_execution_mode": "assessment", "language_policy": {"user_facing_language": "zh-CN"}},
            limit=3,
            question_mix={"code": 2, "single_choice": 1, "open": 1},
            seed_constraints={"required_open_question_count": 1, "required_code_question_count": 1},
        )

        self.assertIn("test-grade", prompt)
        self.assertIn("single_choice", prompt)
        self.assertIn("multiple_choice", prompt)
        self.assertIn("true_false", prompt)
        self.assertIn("problem_statement", prompt)
        self.assertIn("input_spec", prompt)
        self.assertIn("output_spec", prompt)
        self.assertIn("constraints", prompt)
        self.assertIn("examples", prompt)
        self.assertIn("public_tests", prompt)
        self.assertIn("hidden_tests", prompt)
        self.assertIn("scoring_rubric", prompt)
        self.assertIn("capability_tags", prompt)
        self.assertIn("Markdown 可读文本", prompt)
        self.assertIn("每条独立成行", prompt)
        self.assertIn("禁止用分号堆成一行", prompt)
        self.assertIn("禁止生成 open / written / short_answer / free_text", prompt)
        self.assertNotIn("允许生成 concept / code / open", prompt)
        self.assertNotIn("open 题 type 必须是 written", prompt)
        self.assertNotIn("required_open_question_count", prompt)

    def test_strict_question_reviewer_prompt_blocks_non_test_grade_questions(self) -> None:
        prompt = build_question_reviewer_prompt(
            "Python",
            {"semantic_profile": "stage-test", "session_intent": "assessment", "assessment_kind": "stage-test"},
            {"plan_execution_mode": "assessment", "language_policy": {"user_facing_language": "zh-CN"}},
            [self._code_question()],
            {"valid": False, "issues": ["code-two-sum: question.code.input_spec_missing"], "warnings": []},
        )

        for required in (
            "LeetCode-like",
            "problem_statement",
            "input_spec",
            "output_spec",
            "constraints",
            "示例解释",
            "hidden_tests",
            "题干和测试用例不一致",
            "禁止 open / written / short_answer / free_text",
            "泄露 hidden tests",
            "Markdown 可读文本",
            "分号堆成一行",
        ):
            self.assertIn(required, prompt)
        self.assertNotIn("code/open/concept", prompt)


if __name__ == "__main__":
    unittest.main()
