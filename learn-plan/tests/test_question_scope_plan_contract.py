from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_runtime.schemas import validate_question_plan_basic, validate_question_scope_basic


class QuestionScopePlanContractTest(unittest.TestCase):
    def _scope(self, source_profile: str = "today-lesson") -> dict[str, object]:
        assessment_kind = None if source_profile == "today-lesson" else "initial-test" if source_profile == "initial-diagnostic" else "stage-test"
        return {
            "schema_version": "learn-plan.question_scope.v1",
            "scope_id": f"scope-{source_profile}",
            "source_profile": source_profile,
            "session_type": "today" if source_profile == "today-lesson" else "test",
            "session_intent": "learning" if source_profile == "today-lesson" else "assessment",
            "assessment_kind": assessment_kind,
            "test_mode": None if source_profile == "today-lesson" else "general",
            "topic": "Python 基础",
            "language_policy": {"user_facing_language": "zh-CN"},
            "scope_basis": [{"kind": "learn-plan", "summary": "history progress learner_model"}],
            "target_capability_ids": ["python-basics"],
            "target_concepts": ["变量赋值"],
            "review_targets": ["变量与比较运算"],
            "lesson_focus_points": ["变量赋值"],
            "project_tasks": [],
            "project_blockers": [],
            "source_material_refs": [],
            "difficulty_target": {},
            "minimum_pass_shape": {"required_open_question_count": 0},
            "exclusions": [],
            "evidence": ["fixture"],
            "generation_trace": {"status": "ok"},
        }

    def _plan(self, source_profile: str = "today-lesson") -> dict[str, object]:
        assessment_kind = None if source_profile == "today-lesson" else "initial-test" if source_profile == "initial-diagnostic" else "stage-test"
        return {
            "schema_version": "learn-plan.question_plan.v1",
            "plan_id": f"plan-{source_profile}",
            "scope_id": f"scope-{source_profile}",
            "source_profile": source_profile,
            "session_type": "today" if source_profile == "today-lesson" else "test",
            "session_intent": "learning" if source_profile == "today-lesson" else "assessment",
            "assessment_kind": assessment_kind,
            "test_mode": None if source_profile == "today-lesson" else "general",
            "topic": "Python 基础",
            "question_count": 2,
            "question_mix": {"single_choice": 1, "true_false": 1},
            "difficulty_distribution": {"basic": 1, "medium": 1},
            "planned_items": [],
            "coverage_matrix": [],
            "minimum_pass_shape": {"required_open_question_count": 0},
            "forbidden_question_types": ["open", "written", "short_answer", "free_text"],
            "generation_guidance": [],
            "review_checklist": [],
            "evidence": ["fixture"],
            "generation_trace": {"status": "ok"},
        }

    def test_valid_scope_profiles_pass(self) -> None:
        for profile in ("today-lesson", "initial-diagnostic", "history-stage-test"):
            with self.subTest(profile=profile):
                self.assertEqual(validate_question_scope_basic(self._scope(profile)), [])

    def test_valid_question_plan_passes(self) -> None:
        self.assertEqual(validate_question_plan_basic(self._plan("initial-diagnostic")), [])

    def test_unknown_source_profile_fails(self) -> None:
        scope = self._scope()
        scope["source_profile"] = "unknown"

        self.assertIn("question_scope.source_profile_invalid", validate_question_scope_basic(scope))

    def test_test_scope_requires_capabilities(self) -> None:
        scope = self._scope("initial-diagnostic")
        scope["target_capability_ids"] = []

        self.assertIn("question_scope.initial.target_capability_ids_missing", validate_question_scope_basic(scope))

    def test_open_question_count_is_forbidden(self) -> None:
        plan = self._plan()
        plan["minimum_pass_shape"] = {"required_open_question_count": 1}

        self.assertIn("question_plan.minimum_pass_shape.open_not_allowed_by_test_grade", validate_question_plan_basic(plan))

    def test_forbidden_question_type_in_mix_fails(self) -> None:
        plan = self._plan()
        plan["question_mix"] = {"single_choice": 1, "open": 1}

        self.assertIn("question_plan.question_mix.forbidden_type", validate_question_plan_basic(plan))

    def test_question_count_and_mix_mismatch_fails(self) -> None:
        plan = self._plan()
        plan["question_count"] = 3

        self.assertIn("question_plan.question_mix.count_mismatch", validate_question_plan_basic(plan))


if __name__ == "__main__":
    unittest.main()
