from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SERVER_PATH = SKILL_DIR / "templates" / "server.py"


def load_server_module():
    spec = importlib.util.spec_from_file_location("learn_plan_runtime_server", SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load server module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HiddenTestsRuntimeTest(unittest.TestCase):
    def _payload(self) -> dict[str, object]:
        return {
            "questions": [
                {
                    "id": "code-hidden",
                    "type": "code",
                    "category": "code",
                    "title": "隐藏测试不应预泄露",
                    "problem_statement": "实现 identity(x)，返回 x。",
                    "input_spec": "x: int",
                    "output_spec": "int",
                    "constraints": ["x 为整数"],
                    "examples": [{"input": [1], "output": 1, "explanation": "返回输入本身。"}],
                    "public_tests": [{"input": [1], "expected": 1, "category": "public"}],
                    "hidden_tests": [
                        {
                            "input": [999001],
                            "expected": 999001,
                            "category": "hidden",
                            "capability_tags": ["identity-edge"],
                        }
                    ],
                    "test_cases": [{"input": [1], "expected": 1}],
                    "solution_code": "def identity(x):\n    return x\n",
                    "answer": "identity",
                    "answers": [0, 2],
                    "explanation": "直接返回 x。",
                    "reference_points": ["返回输入"],
                    "grading_hint": "必须通过隐藏边界。",
                }
            ]
        }

    def test_display_safe_questions_payload_strips_hidden_tests_and_answers(self) -> None:
        server = load_server_module()

        safe = server.build_display_safe_questions_payload(self._payload())
        question = safe["questions"][0]
        rendered = repr(safe)

        self.assertNotIn("hidden_tests", question)
        self.assertNotIn("solution_code", question)
        self.assertNotIn("answer", question)
        self.assertNotIn("answers", question)
        self.assertNotIn("reference_points", question)
        self.assertNotIn("grading_hint", question)
        self.assertNotIn("999001", rendered)
        self.assertIn("examples", question)
        self.assertIn("public_tests", question)

    def test_submit_function_reads_hidden_tests_from_backend_question(self) -> None:
        server = load_server_module()
        server.load_questions_data = self._payload

        class FakeHandler:
            def __init__(self) -> None:
                self.cases: list[dict[str, object]] = []

            def _run_function_case(self, code, function_name, case, timeout):
                self.cases.append(case)
                return {"passed": True, "expected_repr": repr(case.get("expected")), "actual_repr": repr(case.get("expected")), "error": ""}

        handler = FakeHandler()
        result = server.Handler._submit_function(
            handler,
            {
                "question_id": "code-hidden",
                "code": "def identity(x):\n    return x\n",
                "function_name": "identity",
                "test_cases": [{"input": [1], "expected": 1, "category": "public"}],
            },
        )

        self.assertEqual(result["total_count"], 2)
        self.assertEqual(result["passed_public_count"], 1)
        self.assertEqual(result["total_public_count"], 1)
        self.assertEqual(result["passed_hidden_count"], 1)
        self.assertEqual(result["total_hidden_count"], 1)
        self.assertEqual([case.get("category") for case in handler.cases], ["public", "hidden"])
        self.assertEqual(handler.cases[1].get("input"), [999001])
        self.assertEqual(result.get("results"), [])

    def test_submit_function_returns_capped_failed_case_summaries_only(self) -> None:
        server = load_server_module()
        payload = self._payload()
        question = payload["questions"][0]
        question["hidden_tests"] = [
            {"input": [999001 + index], "expected": 999001 + index, "category": "hidden", "capability_tags": ["edge"]}
            for index in range(5)
        ]
        server.load_questions_data = lambda: payload

        class FakeHandler:
            def _run_function_case(self, code, function_name, case, timeout):
                return {"passed": False, "expected_repr": repr(case.get("expected")), "actual_repr": "None", "error": "wrong_answer"}

        result = server.Handler._submit_function(
            FakeHandler(),
            {"question_id": "code-hidden", "code": "def identity(x):\n    return None\n", "function_name": "identity"},
        )

        self.assertFalse(result["all_passed"])
        self.assertEqual(result["total_count"], 6)
        self.assertEqual(result["passed_public_count"], 0)
        self.assertEqual(result["total_public_count"], 1)
        self.assertEqual(result["passed_hidden_count"], 0)
        self.assertEqual(result["total_hidden_count"], 5)
        self.assertEqual(len(result["failed_case_summaries"]), 3)
        self.assertEqual(result["results"], result["failed_case_summaries"])
        self.assertEqual({case["category"] for case in result["failed_case_summaries"]}, {"public", "hidden"})
        self.assertIn("wrong_answer", result["failure_types"])
        self.assertNotIn("999004", repr(result))


if __name__ == "__main__":
    unittest.main()
