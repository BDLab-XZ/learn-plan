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
            "runtime_context": {"hidden_dataset": "orders_hidden_physical_table"},
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
                    "option_diagnostics": [
                        {
                            "index": 0,
                            "claim": "选项 0 对应正确概念。",
                            "diagnostic_role": "correct_concept",
                            "knowledge_point_ids": [{"id": "kp-hidden", "relevance": "primary", "confidence": 0.9}],
                            "prerequisite_ids": [],
                            "misconception_ids": [],
                            "evidence_span": "不应暴露给前端。",
                            "diagnostic_question": "为什么这个选项成立？",
                        }
                    ],
                    "explanation": "直接返回 x。",
                    "reference_points": ["返回输入"],
                    "grading_hint": "必须通过隐藏边界。",
                    "runtime_context": {"should_not": "leak"},
                    "dataset_refs": ["hidden-table-ref"],
                    "parameter_spec_ref": "hidden-param-ref",
                    "solution_sql": "SELECT * FROM hidden_table",
                    "reference_sql": "SELECT * FROM hidden_table",
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
        self.assertNotIn("dataset_refs", question)
        self.assertNotIn("parameter_spec_ref", question)
        self.assertNotIn("solution_sql", question)
        self.assertNotIn("reference_sql", question)
        self.assertNotIn("hidden-table-ref", rendered)
        self.assertNotIn("hidden-param-ref", rendered)
        self.assertNotIn("hidden_table", rendered)
        self.assertNotIn("orders_hidden_physical_table", rendered)
        self.assertNotIn("runtime_context", safe)
        self.assertNotIn("999001", rendered)
        self.assertNotIn("option_diagnostics", question)
        self.assertNotIn("kp-hidden", rendered)
        self.assertIn("examples", question)
        self.assertIn("public_tests", question)
        self.assertIn("example_displays", question)
        self.assertEqual(question["example_displays"][0]["input_parameters"][0]["name"], "x")
        self.assertEqual(question["example_displays"][0]["outputDisplay"]["repr"], "1")

    def test_objective_diagnostic_triggers_map_wrong_and_uncertain_options(self) -> None:
        server = load_server_module()
        question = {
            "id": "choice-q",
            "type": "single_choice",
            "options": ["正确项", "干扰项", "边界项"],
            "answer": 0,
            "capability_tags": ["python-list"],
            "option_diagnostics": [
                {
                    "index": 0,
                    "claim": "正确项验证列表原地修改概念。",
                    "diagnostic_role": "correct_concept",
                    "knowledge_point_ids": [{"id": "kp-list-mutability", "relevance": "primary", "confidence": 0.9}],
                    "prerequisite_ids": [],
                    "misconception_ids": [],
                    "evidence_span": "正确项。",
                    "diagnostic_question": "为什么 append 会原地修改？",
                    "confidence": 0.9,
                },
                {
                    "index": 1,
                    "claim": "干扰项暴露复制与修改混淆。",
                    "diagnostic_role": "distractor",
                    "knowledge_point_ids": [{"id": "kp-list-mutability", "relevance": "primary", "confidence": 0.8}],
                    "prerequisite_ids": [{"id": "kp-object-reference", "confidence": 0.7}],
                    "misconception_ids": [{"id": "mc-copy-vs-mutation", "confidence": 0.8}],
                    "evidence_span": "干扰项。",
                    "diagnostic_question": "复制和原地修改有什么区别？",
                },
                {
                    "index": 2,
                    "claim": "边界项检查是否过度泛化。",
                    "diagnostic_role": "edge_case",
                    "knowledge_point_ids": [{"id": "kp-list-mutability", "relevance": "primary", "confidence": 0.7}],
                    "prerequisite_ids": [],
                    "misconception_ids": [],
                    "evidence_span": "边界项。",
                    "diagnostic_question": "这个选项为什么不是普通原地修改？",
                },
            ],
        }

        self.assertFalse(server.grade_concept_answer(question, [1]))
        triggers = server.build_objective_diagnostic_triggers(question, [1], [0, 2])

        self.assertEqual([item["trigger_type"] for item in triggers], ["wrong_answer", "wrong_answer", "uncertain", "uncertain"])
        self.assertEqual(triggers[0]["option_index"], 1)
        self.assertTrue(triggers[0]["selected"])
        self.assertFalse(triggers[0]["is_correct_option"])
        self.assertEqual(triggers[0]["knowledge_point_ids"], ["kp-list-mutability"])
        self.assertEqual(triggers[0]["prerequisite_ids"], ["kp-object-reference"])
        self.assertEqual(triggers[0]["misconception_ids"], ["mc-copy-vs-mutation"])
        self.assertEqual(triggers[0]["diagnostic_mapping_status"], "mapped")
        self.assertEqual(triggers[1]["option_index"], 0)
        self.assertFalse(triggers[1]["selected"])
        self.assertTrue(triggers[1]["is_correct_option"])
        self.assertEqual(triggers[2]["trigger_type"], "uncertain")
        self.assertTrue(triggers[2]["is_correct_option"])
        self.assertEqual(triggers[3]["option_index"], 2)

    def test_objective_uncertain_does_not_change_correctness(self) -> None:
        server = load_server_module()
        question = {
            "id": "choice-correct-uncertain",
            "type": "single_choice",
            "options": ["=", "=="],
            "answer": 0,
            "option_diagnostics": [
                {
                    "index": 0,
                    "claim": "`=` 是赋值符号。",
                    "diagnostic_role": "correct_concept",
                    "knowledge_point_ids": [{"id": "kp-assignment", "relevance": "primary", "confidence": 0.9}],
                    "prerequisite_ids": [],
                    "misconception_ids": [],
                    "evidence_span": "正确项。",
                    "diagnostic_question": "为什么这里不是比较？",
                },
                {
                    "index": 1,
                    "claim": "`==` 是相等比较符号。",
                    "diagnostic_role": "distractor",
                    "knowledge_point_ids": [{"id": "kp-assignment", "relevance": "primary", "confidence": 0.9}],
                    "prerequisite_ids": [],
                    "misconception_ids": [{"id": "mc-assignment-vs-equality", "confidence": 0.8}],
                    "evidence_span": "干扰项。",
                    "diagnostic_question": "`=` 和 `==` 分别用于什么场景？",
                },
            ],
        }

        self.assertTrue(server.grade_concept_answer(question, [0]))
        triggers = server.build_objective_diagnostic_triggers(question, [0], [1])

        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]["trigger_type"], "uncertain")
        self.assertEqual(triggers[0]["option_index"], 1)
        self.assertFalse(triggers[0]["selected"])
        self.assertFalse(triggers[0]["is_correct_option"])

        result = server.attach_result_summary(
            {
                "ok": True,
                "is_correct": True,
                "question_id": question["id"],
                "question_type": question["type"],
                "selected": [0],
                "unsure": [1],
                "diagnostic_triggers": triggers,
            }
        )
        self.assertEqual(result["raw_score"], {"correct": 1, "attempted": 1, "total": 1, "ratio": 1.0})
        self.assertEqual(result["learning_score"]["level"], "medium")
        self.assertEqual(result["learning_score"]["uncertain_count"], 1)
        self.assertEqual(result["review_recommendation"]["recommended_action"], "mixed_review_then_new")

    def test_run_function_preview_reads_public_tests_from_backend_question(self) -> None:
        server = load_server_module()
        server.load_questions_data = self._payload

        class FakeHandler:
            def __init__(self) -> None:
                self.cases: list[dict[str, object]] = []

            def _run_function_case(self, code, function_name, case, timeout):
                self.cases.append(case)
                return {"passed": True, "expected_repr": repr(case.get("expected")), "actual_repr": repr(case.get("expected")), "stdout": "debug", "stderr": "", "error": ""}

        handler = FakeHandler()
        result = server.Handler._run_function_preview(
            handler,
            {"question_id": "code-hidden", "code": "def identity(x):\n    print('debug')\n    return x\n", "function_name": "identity"},
        )

        self.assertEqual(len(handler.cases), 1)
        self.assertEqual(handler.cases[0].get("category"), "public")
        self.assertEqual(result["run_cases"][0]["expected_repr"], "1")
        self.assertEqual(result["run_cases"][0]["actual_repr"], "1")
        self.assertEqual(result["run_cases"][0]["stdout"], "debug")
        self.assertNotIn("999001", repr(result))

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
        self.assertEqual(len(result["diagnostic_triggers"]), 1)
        trigger = result["diagnostic_triggers"][0]
        self.assertEqual(trigger["trigger_type"], "code_failure")
        self.assertEqual(trigger["question_id"], "code-hidden")
        self.assertEqual(trigger["question_type"], "code")
        self.assertEqual(trigger["failed_case_count"], 3)
        self.assertEqual(trigger["severity"], "high")
        self.assertTrue(trigger["requires_follow_up"])
        self.assertEqual(result["raw_score"]["correct"], 0)
        self.assertEqual(result["raw_score"]["total"], 6)
        self.assertEqual(result["learning_score"]["level"], "low")
        self.assertEqual(result["review_recommendation"]["recommended_action"], "review_first")
        self.assertNotIn("999004", repr(result))

    def test_sql_submit_result_gets_failure_diagnostic_trigger(self) -> None:
        server = load_server_module()
        server.load_runtime_context = lambda: {}
        server.find_question_by_id = lambda question_id: {"id": question_id, "type": "sql", "capability_tags": ["sql-join"]}

        def fake_submit_sql(question, sql, runtime_context):
            return {
                "all_passed": False,
                "passed_count": 0,
                "total_count": 1,
                "passed_public_count": 0,
                "total_public_count": 1,
                "passed_hidden_count": 0,
                "total_hidden_count": 0,
                "failed_case_summaries": [{"case": 1, "category": "public", "passed": False, "error": "wrong_answer"}],
                "failure_types": ["wrong_answer"],
                "results": [],
            }

        import learn_runtime.mysql_runtime as mysql_runtime

        original_submit_sql = mysql_runtime.submit_sql
        mysql_runtime.submit_sql = fake_submit_sql
        try:
            result = server.Handler._submit_sql_query(object(), {"question_id": "sql-q", "sql": "SELECT 1"})
        finally:
            mysql_runtime.submit_sql = original_submit_sql

        self.assertEqual(len(result["diagnostic_triggers"]), 1)
        trigger = result["diagnostic_triggers"][0]
        self.assertEqual(trigger["trigger_type"], "sql_failure")
        self.assertEqual(trigger["question_id"], "sql-q")
        self.assertEqual(trigger["question_type"], "sql")
        self.assertEqual(trigger["capability_tags"], ["sql-join"])
        self.assertEqual(trigger["severity"], "medium")
        self.assertEqual(result["raw_score"]["correct"], 0)
        self.assertEqual(result["learning_score"]["level"], "medium_low")
        self.assertEqual(result["review_recommendation"]["recommended_action"], "mixed_review_then_new")

    def test_display_safe_questions_payload_derives_public_dataset_description_only(self) -> None:
        server = load_server_module()
        payload = {
            "runtime_context": {
                "parameter_artifact": {
                    "cases": [
                        {
                            "question_id": "sql-multi",
                            "visibility": "public",
                            "parameters": {
                                "users": {"dataset_ref": "users-public"},
                                "orders": {"dataset_ref": "orders-public"},
                            },
                        },
                        {
                            "question_id": "sql-multi",
                            "visibility": "hidden",
                            "parameters": {"orders": {"dataset_ref": "orders-hidden"}},
                        },
                    ]
                },
                "dataset_artifact": {
                    "relationships": [
                        {
                            "left_table": "orders",
                            "left_key": "user_id",
                            "right_table": "users",
                            "right_key": "id",
                            "description": "orders.user_id joins users.id",
                            "physical_table": "learn_hidden_physical",
                        }
                    ],
                    "datasets": [
                        {
                            "dataset_id": "users-public",
                            "kind": "sql_table",
                            "visibility": "public",
                            "logical_name": "users",
                            "physical_table": "learn_demo__users_public",
                            "columns": [
                                {"name": "id", "dtype": "int", "mysql_type": "BIGINT", "nullable": False, "description": "用户 ID"},
                                {"name": "name", "dtype": "str", "mysql_type": "VARCHAR(32)", "nullable": False},
                            ],
                            "rows": [{"id": 1, "name": "Ada"}],
                        },
                        {
                            "dataset_id": "orders-public",
                            "kind": "sql_table",
                            "visibility": "public",
                            "logical_name": "orders",
                            "physical_table": "learn_demo__orders_public",
                            "columns": [
                                {"name": "user_id", "dtype": "int", "mysql_type": "BIGINT", "nullable": False},
                                {"name": "amount", "dtype": "float", "mysql_type": "DOUBLE", "nullable": False},
                            ],
                            "rows": [{"user_id": 1, "amount": 20.5}],
                        },
                        {
                            "dataset_id": "orders-hidden",
                            "kind": "sql_table",
                            "visibility": "hidden",
                            "logical_name": "orders_hidden",
                            "physical_table": "learn_demo__orders_hidden",
                            "columns": [{"name": "secret", "dtype": "int"}],
                            "rows": [{"secret": 999001}],
                        },
                    ],
                },
            },
            "questions": [
                {
                    "id": "sql-multi",
                    "type": "sql",
                    "category": "code",
                    "title": "多表 SQL",
                    "dataset_refs": ["users-public", "orders-public", "orders-hidden"],
                    "reference_sql": "SELECT * FROM learn_demo__orders_hidden",
                }
            ],
        }

        safe = server.build_display_safe_questions_payload(payload)
        rendered = repr(safe)
        question = safe["questions"][0]
        description = question["dataset_description"]

        self.assertEqual([table["name"] for table in description["tables"]], ["users", "orders"])
        self.assertEqual(description["relationships"][0]["left_table"], "orders")
        self.assertEqual(description["relationships"][0]["right_table"], "users")
        self.assertIn("用户 ID", rendered)
        self.assertIn("Ada", rendered)
        self.assertNotIn("runtime_context", rendered)
        self.assertNotIn("dataset_refs", rendered)
        self.assertNotIn("reference_sql", rendered)
        self.assertNotIn("learn_demo__users_public", rendered)
        self.assertNotIn("learn_demo__orders_hidden", rendered)
        self.assertNotIn("orders-hidden", rendered)
        self.assertNotIn("999001", rendered)


if __name__ == "__main__":
    unittest.main()
