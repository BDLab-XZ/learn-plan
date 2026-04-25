from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_workflow.stage_llm import build_stage_candidate_prompt
from learn_workflow.stage_review import review_stage_candidate


class StaircaseDiagnosticContractTest(unittest.TestCase):
    def _candidate(self) -> dict[str, object]:
        return {
            "contract_version": "learn-plan.workflow.v2",
            "stage": "diagnostic",
            "candidate_version": "test",
            "diagnostic_plan": {
                "delivery": "web-session",
                "assessment_kind": "initial-test",
                "session_intent": "assessment",
                "plan_execution_mode": "diagnostic",
                "target_capability_ids": ["python-basics"],
                "scoring_rubric": ["正确性"],
                "round_index": 1,
                "max_rounds": 3,
                "questions_per_round": 5,
                "follow_up_needed": True,
                "stop_reason": "needs_next_round",
            },
            "diagnostic_items": [{"id": "q1", "capability_id": "python-basics", "expected_signals": ["能写函数"]}],
            "diagnostic_result": {"status": "pending", "follow_up_needed": True, "stop_reason": "needs_next_round"},
            "diagnostic_profile": {"status": "pending", "follow_up_needed": True, "stop_reason": "needs_next_round"},
            "evidence": ["diagnostic fixture"],
            "confidence": 0.8,
            "generation_trace": {"stage": "diagnostic", "generator": "test", "status": "ok"},
            "traceability": [{"kind": "test", "ref": "diagnostic"}],
        }

    def test_diagnostic_review_requires_staircase_difficulty_metadata(self) -> None:
        reviewed = review_stage_candidate("diagnostic", self._candidate())
        issues = reviewed.get("quality_review", {}).get("issues", [])

        self.assertIn("diagnostic.start_difficulty_missing", issues)
        self.assertIn("diagnostic.difficulty_ladder_missing", issues)
        self.assertIn("diagnostic.difficulty_adjustment_policy_missing", issues)

    def test_diagnostic_review_accepts_staircase_difficulty_metadata(self) -> None:
        candidate = self._candidate()
        plan = candidate["diagnostic_plan"]
        plan["start_difficulty"] = "medium"
        plan["difficulty_ladder"] = ["easy", "medium", "hard"]
        plan["difficulty_adjustment_policy"] = {
            "too_hard": "lower_difficulty_next_round",
            "too_easy": "raise_difficulty_next_round",
        }

        reviewed = review_stage_candidate("diagnostic", candidate)
        issues = reviewed.get("quality_review", {}).get("issues", [])

        self.assertNotIn("diagnostic.start_difficulty_missing", issues)
        self.assertNotIn("diagnostic.difficulty_ladder_missing", issues)
        self.assertNotIn("diagnostic.difficulty_adjustment_policy_missing", issues)

    def test_prompt_demands_staircase_diagnostic(self) -> None:
        prompt = build_stage_candidate_prompt(
            "diagnostic",
            topic="Python",
            goal="求职",
            level="有基础",
            schedule="每天30分钟",
            preference="混合",
            context={},
        )

        self.assertIn("start_difficulty", prompt)
        self.assertIn("difficulty_ladder", prompt)
        self.assertIn("difficulty_adjustment_policy", prompt)
        self.assertIn("过难", prompt)
        self.assertIn("过易", prompt)


if __name__ == "__main__":
    unittest.main()
