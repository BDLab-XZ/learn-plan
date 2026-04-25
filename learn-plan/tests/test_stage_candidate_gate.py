from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

import learn_plan


class StageCandidateGateTest(unittest.TestCase):
    def _clarification(self) -> dict:
        return {
            "questionnaire": {
                "topic": "Python",
                "goal": "通过期末考试",
                "success_criteria": ["完成基础语法题"],
                "current_level_self_report": "零基础",
                "time_constraints": {"frequency": "每天", "session_length": "30分钟"},
                "mastery_preferences": {"max_assessment_rounds_preference": 1, "questions_per_round_preference": 5},
            },
            "clarification_state": {"open_questions": []},
            "preference_state": {"pending_items": []},
            "evidence": ["clarification fixture"],
            "confidence": 0.8,
            "generation_trace": {"stage": "clarification", "generator": "test-fixture", "status": "ok"},
            "traceability": [{"kind": "test", "ref": "clarification"}],
            "quality_review": {"reviewer": "test", "valid": True, "issues": [], "confidence": 0.8},
        }

    def _base_kwargs(self) -> dict:
        return {
            "topic": "Python",
            "goal": "通过期末考试",
            "level": "零基础",
            "schedule": "每天30分钟",
            "preference": "混合",
            "clarification": self._clarification(),
            "research": {},
            "diagnostic": {},
            "approval": {},
            "learner_model": {},
            "curriculum_patch_queue": {},
            "workflow_state": {},
            "artifacts": {},
            "injected_candidate": None,
        }

    def test_missing_research_candidate_does_not_build_deterministic_fallback(self) -> None:
        with patch("learn_plan.build_research_fallback_candidate", side_effect=AssertionError("research fallback should not run")):
            artifact, metadata = learn_plan.maybe_generate_stage_candidate("research", **self._base_kwargs())

        self.assertEqual(metadata.get("status"), "missing-external-artifact")
        self.assertEqual(artifact.get("stage"), "research")
        self.assertEqual(artifact.get("candidate_error", {}).get("message"), "external_candidate_required")
        self.assertNotIn("research_report", artifact)
        self.assertFalse(artifact.get("quality_review", {}).get("valid"))
        self.assertIn("research.external_candidate_required", artifact.get("quality_review", {}).get("issues", []))

    def test_missing_diagnostic_candidate_does_not_build_deterministic_fallback(self) -> None:
        kwargs = self._base_kwargs()
        kwargs["research"] = {
            "research_report": {
                "goal_target_band": "期末高分",
                "required_level_definition": "掌握基础语法",
                "diagnostic_scope": {"target_capability_ids": ["syntax"], "scoring_dimensions": ["正确率"], "gap_judgement_basis": ["错题"]},
            }
        }
        with patch("learn_plan.build_diagnostic_fallback_candidate", side_effect=AssertionError("diagnostic fallback should not run")):
            artifact, metadata = learn_plan.maybe_generate_stage_candidate("diagnostic", **kwargs)

        self.assertEqual(metadata.get("status"), "missing-external-artifact")
        self.assertEqual(artifact.get("stage"), "diagnostic")
        self.assertEqual(artifact.get("candidate_error", {}).get("message"), "external_candidate_required")
        self.assertNotIn("diagnostic_plan", artifact)
        self.assertFalse(artifact.get("quality_review", {}).get("valid"))
        self.assertIn("diagnostic.external_candidate_required", artifact.get("quality_review", {}).get("issues", []))


if __name__ == "__main__":
    unittest.main()
