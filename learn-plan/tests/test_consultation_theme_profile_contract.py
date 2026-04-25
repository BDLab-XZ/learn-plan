from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_workflow.stage_llm import build_stage_candidate_prompt
from learn_workflow.stage_review import review_stage_candidate


class ConsultationThemeProfileContractTest(unittest.TestCase):
    def _base_candidate(self) -> dict[str, object]:
        return {
            "contract_version": "learn-plan.workflow.v2",
            "stage": "clarification",
            "candidate_version": "test",
            "questionnaire": {
                "topic": "Python",
                "goal": "求职数据科学岗位",
                "success_criteria": ["能通过岗位面试"],
                "current_level_self_report": "有基础",
                "mastery_preferences": {"max_assessment_rounds_preference": 2, "questions_per_round_preference": 6},
            },
            "clarification_state": {"open_questions": []},
            "preference_state": {"pending_items": []},
            "consultation_state": {
                "current_topic_id": "learning_purpose",
                "topics": [
                    {"id": "learning_purpose", "required": True, "status": "in-progress", "exit_criteria": ["目标范围明确"]},
                    {"id": "current_level", "required": True, "status": "resolved", "exit_criteria": ["基础证据明确"]},
                    {"id": "assessment_scope", "required": True, "status": "resolved", "exit_criteria": ["测评预算明确"]},
                ],
            },
            "language_policy": {"user_facing_language": "zh-CN"},
            "evidence": ["用户回答"],
            "confidence": 0.8,
            "generation_trace": {"stage": "clarification", "generator": "test", "status": "ok"},
            "traceability": [{"kind": "test", "ref": "clarification"}],
        }

    def test_clarification_review_requires_theme_inventory_and_learner_profile(self) -> None:
        reviewed = review_stage_candidate("clarification", self._base_candidate())
        issues = reviewed.get("quality_review", {}).get("issues", [])

        self.assertIn("clarification.theme_inventory_missing", issues)
        self.assertIn("clarification.learner_profile_missing", issues)
        self.assertIn("clarification.learner_profile_confirmation_missing", issues)

    def test_clarification_review_accepts_theme_inventory_and_profile_confirmation(self) -> None:
        candidate = self._base_candidate()
        candidate["theme_inventory"] = ["学习目的", "目标范围", "当前基础", "测评范围"]
        candidate["learner_profile"] = {
            "summary": "有 Python 基础，目标是数据科学岗位",
            "background": ["学过基础语法"],
            "goal_context": ["求职"],
            "confirmation_status": "pending_user_confirmation",
            "confirmation_prompt": "请确认这个用户画像是否准确。",
        }

        reviewed = review_stage_candidate("clarification", candidate)
        issues = reviewed.get("quality_review", {}).get("issues", [])

        self.assertNotIn("clarification.theme_inventory_missing", issues)
        self.assertNotIn("clarification.learner_profile_missing", issues)
        self.assertNotIn("clarification.learner_profile_confirmation_missing", issues)

    def test_prompt_demands_theme_inventory_and_profile_confirmation(self) -> None:
        prompt = build_stage_candidate_prompt(
            "clarification",
            topic="Python",
            goal="求职",
            level="有基础",
            schedule="每天30分钟",
            preference="混合",
            context={},
        )

        self.assertIn("theme_inventory", prompt)
        self.assertIn("learner_profile", prompt)
        self.assertIn("用户画像", prompt)
        self.assertIn("确认", prompt)


if __name__ == "__main__":
    unittest.main()
