from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_runtime.question_validation import validate_questions_payload
from learn_runtime.schemas import preflight_code_question_tests


class CodeTestPreflightTest(unittest.TestCase):
    def _question(self, *, expected: int = 6, solution_code: str | None = None) -> dict[str, object]:
        return {
            "id": "code-combine",
            "type": "code",
            "category": "code",
            "title": "多参数求和",
            "problem_statement": "实现 `combine(a, b, c)`。\n\n**目标**：返回三个整数之和。\n\n要求：\n- 使用三个独立参数\n- 不修改输入值",
            "input_spec": "`a: int`、`b: int`、`c: int`，三个参数均为整数。",
            "output_spec": "返回 `int`，表示三个整数之和。",
            "calculation_spec": "计算规则为 `a + b + c`，不做类型转换或舍入。",
            "constraints": ["参数均为整数"],
            "examples": [{"input": {"a": 1, "b": 2, "c": 3}, "output": 6, "explanation": "1 + 2 + 3 = 6。"}],
            "public_tests": [{"kwargs": {"a": 1, "b": 2, "c": 3}, "expected": expected, "category": "public"}],
            "hidden_tests": [{"args": [2, 3, 4], "expected": 9, "category": "hidden"}],
            "starter_code": "def combine(a, b, c):\n    pass\n",
            "solution_code": solution_code or "def combine(a, b, c):\n    return a + b + c\n",
            "function_signature": "combine(a: int, b: int, c: int) -> int",
            "function_name": "combine",
            "scoring_rubric": ["正确处理多个形参"],
            "capability_tags": ["function-arguments"],
            "source_trace": {"question_source": "test-fixture"},
            "question_role": "code",
        }

    def _payload(self, question: dict[str, object]) -> dict[str, object]:
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
                "lesson_grounding_context": {"semantic_profile": "today", "minimum_pass_shape": {}},
                "question_generation_mode": "agent-subagent",
                "strict_question_review": {"valid": True, "verdict": "pass", "issues": []},
                "deterministic_question_review": {"valid": True, "verdict": "pass", "issues": []},
            },
            "selection_context": {"language_policy": {"user_facing_language": "zh-CN"}},
            "materials": [],
            "runtime_context": {
                "parameter_spec": {
                    "schema_version": "learn-plan.parameter_spec.v1",
                    "questions": [
                        {
                            "question_id": "code-combine",
                            "supported_runtimes": ["python"],
                            "default_runtime": "python",
                            "parameters": [
                                {"name": "a", "type": "json", "schema": {"kind": "int"}},
                                {"name": "b", "type": "json", "schema": {"kind": "int"}},
                                {"name": "c", "type": "json", "schema": {"kind": "int"}},
                            ],
                            "output_schema": {"kind": "int"},
                        }
                    ],
                }
            },
            "questions": [question],
        }

    def test_reference_solution_passes_public_and_hidden_tests(self) -> None:
        issues = preflight_code_question_tests(self._question())

        self.assertEqual(issues, [])

    def test_reference_solution_failure_blocks_preflight(self) -> None:
        issues = preflight_code_question_tests(self._question(expected=7))

        self.assertIn("question.code.preflight.public.0.wrong_answer", issues)

    def test_runtime_error_blocks_preflight(self) -> None:
        issues = preflight_code_question_tests(self._question(solution_code="def combine(a, b, c):\n    raise RuntimeError('boom')\n"))

        self.assertIn("question.code.preflight.public.0.runtime_error", issues)

    def test_validate_questions_payload_includes_preflight_issues(self) -> None:
        review = validate_questions_payload(self._payload(self._question(expected=7)))

        self.assertFalse(review.get("valid"))
        self.assertIn("code-combine: question.code.preflight.public.0.wrong_answer", review.get("issues", []))


if __name__ == "__main__":
    unittest.main()
