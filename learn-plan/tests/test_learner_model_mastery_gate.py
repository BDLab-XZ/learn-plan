from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_feedback.learner_model import default_learner_model, update_learner_model_from_summary


class LearnerModelMasteryGateTest(unittest.TestCase):
    def _summary(self) -> dict[str, object]:
        return {
            "topic": "Python",
            "date": "2026-04-30",
            "overall": "表现不错",
            "covered_scope": ["闭包"],
            "solved_items": [{"title": "闭包变量题"}],
            "review_focus": [],
            "mastery": {"reflection_gate_completed": True},
        }

    def _facts(self, *, status: str | None = None, prompting_level: str = "unknown", completion: bool = True, reflection: bool = True) -> dict[str, object]:
        facts: dict[str, object] = {
            "date": "2026-04-30",
            "topic": "Python",
            "session_dir": "/tmp/session",
            "scores": {"attempted": 3},
            "evidence": ["fixture"],
        }
        if completion:
            facts["completion_signal_facts"] = {"status": "received"}
        if reflection:
            facts["reflection_facts"] = {"status": "completed"}
        if status:
            facts["mastery_judgement_facts"] = {
                "status": status,
                "mastery_level": "transfer",
                "prompting_level": prompting_level,
                "evidence": ["能迁移"],
                "next_session_reinforcement": ["下次轻量复习"],
            }
        return facts

    def test_covered_scope_without_reflection_does_not_become_mastered(self) -> None:
        model = update_learner_model_from_summary(default_learner_model(), self._summary(), session_facts=self._facts(status="mastered", reflection=False), update_type="today")

        self.assertNotIn("闭包", model.get("mastered_scope", []))
        self.assertIn("下次轻量复习", model.get("review_debt", []))

    def test_solid_after_intervention_records_prompted_scope_not_mastered_scope(self) -> None:
        model = update_learner_model_from_summary(default_learner_model(), self._summary(), session_facts=self._facts(status="solid_after_intervention", prompting_level="hinted"), update_type="today")

        self.assertNotIn("闭包", model.get("mastered_scope", []))
        self.assertIn("闭包", model.get("prompted_mastery_scope", []))
        self.assertIn("提示后能稳定掌握", model.get("learning_behaviors", []))

    def test_unprompted_mastered_scope_requires_completion_and_reflection(self) -> None:
        model = update_learner_model_from_summary(default_learner_model(), self._summary(), session_facts=self._facts(status="mastered", prompting_level="unprompted"), update_type="today")

        self.assertIn("闭包", model.get("mastered_scope", []))
        self.assertNotIn("闭包", model.get("prompted_mastery_scope", []))


if __name__ == "__main__":
    unittest.main()
