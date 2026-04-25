from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_feedback.progress_summary import build_coverage_ledger_facts, build_session_facts
from learn_runtime.lesson_builder import build_lesson_grounding_context


class LearningCoverageLedgerTest(unittest.TestCase):
    def test_coverage_ledger_records_learning_states(self) -> None:
        progress = {
            "questions": {
                "q1": {
                    "stats": {"attempted": True, "is_correct": True},
                    "capability_tags": ["function-params"],
                    "coverage": {"concept_id": "function-params", "introduced": True, "practiced": True, "tested": True},
                },
                "q2": {
                    "stats": {"attempted": True, "is_correct": False},
                    "tags": ["return-values"],
                    "coverage": {"concept_id": "return-values", "introduced": True, "practiced": True, "tested": True},
                },
            }
        }
        summary = {
            "lesson_focus_points": ["function-params", "return-values"],
            "covered_scope": ["function-params", "return-values"],
            "solved_items": [{"id": "q1", "title": "函数参数"}],
            "wrong_items": [{"id": "q2", "title": "返回值"}],
        }

        facts = build_coverage_ledger_facts(progress, summary)
        by_id = {item["concept_id"]: item for item in facts}

        self.assertTrue(by_id["function-params"]["introduced"])
        self.assertTrue(by_id["function-params"]["practiced"])
        self.assertTrue(by_id["function-params"]["tested"])
        self.assertTrue(by_id["function-params"]["mastered"])
        self.assertFalse(by_id["return-values"]["mastered"])
        self.assertIn("repeated_count", by_id["function-params"])

    def test_session_facts_include_coverage_ledger(self) -> None:
        progress = {
            "questions": {
                "q1": {
                    "stats": {"attempted": True, "is_correct": True},
                    "coverage": {"concept_id": "function-params", "introduced": True, "practiced": True, "tested": True},
                }
            }
        }
        summary = {"attempted": 1, "correct": 1, "covered_scope": ["function-params"]}

        with tempfile.TemporaryDirectory() as tmp:
            facts = build_session_facts(progress, summary, session_dir=Path(tmp), update_type="today")

        self.assertIn("coverage_ledger_facts", facts)
        self.assertEqual(facts["coverage_ledger_facts"][0]["concept_id"], "function-params")

    def test_lesson_grounding_context_carries_coverage_ledger_to_reduce_repetition(self) -> None:
        context = build_lesson_grounding_context(
            "Python",
            {
                "coverage_ledger": [
                    {"concept_id": "variables", "mastered": True, "repeated_count": 2},
                    {"concept_id": "function-params", "introduced": True, "mastered": False},
                ]
            },
            [],
            {},
        )

        self.assertIn("coverage_ledger", context)
        self.assertIn("avoid_repeating_mastered", context["coverage_policy"])
        self.assertEqual(context["coverage_ledger"][0]["concept_id"], "variables")


if __name__ == "__main__":
    unittest.main()
