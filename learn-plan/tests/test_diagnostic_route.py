from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = SKILL_DIR / "templates"
if str(TEMPLATES_DIR) not in sys.path:
    sys.path.insert(0, str(TEMPLATES_DIR))

from server import build_diagnostic_next_route


class DiagnosticRouteTest(unittest.TestCase):
    def test_diagnostic_finish_reports_next_round_artifacts(self) -> None:
        progress = {
            "session": {
                "type": "test",
                "plan_execution_mode": "diagnostic",
                "round_index": 1,
                "max_rounds": 3,
                "follow_up_needed": True,
            }
        }

        route = build_diagnostic_next_route(progress)

        self.assertIsNotNone(route)
        self.assertTrue(route.get("next_diagnostic_round_required"))
        self.assertEqual(route.get("next_round_index"), 2)
        self.assertEqual(
            route.get("required_artifacts"),
            ["question-scope-json", "question-plan-json", "question-artifact-json", "question-review-json"],
        )
        self.assertEqual(route.get("next_action"), "prepare_next_diagnostic_round_artifacts")

    def test_diagnostic_finish_reports_semantic_update_when_no_next_round(self) -> None:
        progress = {
            "session": {
                "type": "test",
                "plan_execution_mode": "diagnostic",
                "round_index": 3,
                "max_rounds": 3,
                "follow_up_needed": False,
            }
        }

        route = build_diagnostic_next_route(progress)

        self.assertIsNotNone(route)
        self.assertFalse(route.get("next_diagnostic_round_required"))
        self.assertEqual(route.get("required_artifacts"), ["semantic-diagnostic-json"])
        self.assertEqual(route.get("next_action"), "run_semantic_diagnostic_update")

    def test_non_diagnostic_finish_has_no_diagnostic_route(self) -> None:
        progress = {"session": {"type": "today", "plan_execution_mode": None}}

        self.assertIsNone(build_diagnostic_next_route(progress))


if __name__ == "__main__":
    unittest.main()
