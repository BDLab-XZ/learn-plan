from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

HTML_PATH = SKILL_DIR / "templates" / "题集模板.html"
SERVER_PATH = SKILL_DIR / "templates" / "server.py"

from learn_runtime.question_generation import is_valid_runtime_question
from learn_runtime.schemas import normalize_question_type, validate_test_grade_question


def load_server_module():
    spec = importlib.util.spec_from_file_location("learn_plan_runtime_server_type_contract", SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load server module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RuntimeTypeContractTest(unittest.TestCase):
    def _objective_question(self, qtype: str = "single_choice") -> dict[str, object]:
        return {
            "id": f"concept-{qtype}",
            "type": qtype,
            "category": "concept",
            "title": "列表可变性",
            "prompt": "以下哪个操作会原地修改列表 xs？",
            "options": ["xs.append(1)", "xs + [1]", "tuple(xs)", "xs.copy()"],
            "answer": 0,
            "explanation": "append 会原地修改列表。",
            "scoring_rubric": ["识别原地修改"],
            "capability_tags": ["python-list"],
            "source_trace": {"question_source": "test-fixture"},
        }

    def test_legacy_objective_types_have_one_explicit_normalization_map(self) -> None:
        self.assertEqual(normalize_question_type("single"), "single_choice")
        self.assertEqual(normalize_question_type("multi"), "multiple_choice")
        self.assertEqual(normalize_question_type("judge"), "true_false")
        self.assertEqual(normalize_question_type("single_choice"), "single_choice")
        self.assertEqual(normalize_question_type("unknown"), "unknown")

    def test_raw_legacy_objective_question_is_not_valid_runtime_question(self) -> None:
        self.assertFalse(is_valid_runtime_question(self._objective_question("single")))
        self.assertFalse(is_valid_runtime_question(self._objective_question("multi")))
        self.assertFalse(is_valid_runtime_question(self._objective_question("judge")))

    def test_canonical_objective_question_is_valid_runtime_question(self) -> None:
        self.assertTrue(is_valid_runtime_question(self._objective_question("single_choice")))
        multi = self._objective_question("multiple_choice")
        multi["answers"] = [0, 1]
        multi.pop("answer", None)
        self.assertTrue(is_valid_runtime_question(multi))
        true_false = self._objective_question("true_false")
        true_false["options"] = ["正确", "错误"]
        true_false["answer"] = True
        self.assertTrue(is_valid_runtime_question(true_false))

    def test_validate_test_grade_question_rejects_unknown_and_raw_legacy_types(self) -> None:
        for qtype in ("single", "multi", "judge", "choice", "unknown"):
            with self.subTest(qtype=qtype):
                issues = validate_test_grade_question(self._objective_question(qtype))
                self.assertIn("question.test_grade_type_invalid", issues)

    def test_server_grades_only_canonical_objective_types(self) -> None:
        server = load_server_module()
        self.assertTrue(server.grade_concept_answer(self._objective_question("single_choice"), [0]))
        self.assertFalse(server.grade_concept_answer(self._objective_question("single_choice"), [1]))

        multiple = self._objective_question("multiple_choice")
        multiple["answers"] = [0, 2]
        multiple.pop("answer", None)
        self.assertTrue(server.grade_concept_answer(multiple, [2, 0]))
        self.assertFalse(server.grade_concept_answer(multiple, [0]))

        true_false = self._objective_question("true_false")
        true_false["options"] = ["正确", "错误"]
        true_false["answer"] = True
        self.assertTrue(server.grade_concept_answer(true_false, [0]))
        self.assertFalse(server.grade_concept_answer(true_false, [1]))

        unknown = self._objective_question("unknown")
        self.assertFalse(server.grade_concept_answer(unknown, [0]))

    def test_frontend_does_not_default_unknown_concept_type_to_judge(self) -> None:
        html = HTML_PATH.read_text(encoding="utf-8")
        label_block = re.search(r"function getQuestionTypeLabel\(question\) \{(?P<body>.*?)\n    \}", html, re.S)
        self.assertIsNotNone(label_block)
        self.assertIn("if (qtype === 'true_false') return '判断题';", label_block.group("body"))
        self.assertIn("return '题型契约错误';", label_block.group("body"))

        concept_block = re.search(r"function renderConceptPage\(question\) \{(?P<body>.*?)\n    function highlightCode", html, re.S)
        self.assertIsNotNone(concept_block)
        self.assertIn("isUnsupportedConceptType", concept_block.group("body"))
        self.assertIn("题型契约错误", concept_block.group("body"))
        self.assertNotIn("question.type === 'judge'", concept_block.group("body"))
        self.assertNotIn("question.type === 'single'", concept_block.group("body"))
        self.assertNotIn("question.type === 'multi'", concept_block.group("body"))


if __name__ == "__main__":
    unittest.main()
