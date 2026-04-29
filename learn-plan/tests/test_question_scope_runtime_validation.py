from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_runtime.question_validation import validate_questions_payload


class QuestionScopeRuntimeValidationTest(unittest.TestCase):
    def _scope(self) -> dict[str, object]:
        return {
            "schema_version": "learn-plan.question_scope.v1",
            "scope_id": "scope-stage",
            "source_profile": "history-stage-test",
            "session_type": "test",
            "session_intent": "assessment",
            "assessment_kind": "stage-test",
            "test_mode": "general",
            "topic": "Python 基础",
            "language_policy": {"user_facing_language": "zh-CN"},
            "scope_basis": [{"kind": "progress", "summary": "history progress learner_model"}],
            "target_capability_ids": ["python-assignment"],
            "target_concepts": [],
            "review_targets": ["赋值与比较"],
            "lesson_focus_points": [],
            "project_tasks": [],
            "project_blockers": [],
            "source_material_refs": [],
            "difficulty_target": {},
            "minimum_pass_shape": {"required_open_question_count": 0},
            "exclusions": [],
            "evidence": ["progress.json"],
            "generation_trace": {"status": "ok"},
        }

    def _plan(self) -> dict[str, object]:
        return {
            "schema_version": "learn-plan.question_plan.v1",
            "plan_id": "plan-stage",
            "scope_id": "scope-stage",
            "source_profile": "history-stage-test",
            "session_type": "test",
            "session_intent": "assessment",
            "assessment_kind": "stage-test",
            "test_mode": "general",
            "topic": "Python 基础",
            "question_count": 1,
            "question_mix": {"single_choice": 1},
            "difficulty_distribution": {"basic": 1},
            "planned_items": [],
            "coverage_matrix": [],
            "minimum_pass_shape": {"required_open_question_count": 0},
            "forbidden_question_types": ["open", "written", "short_answer", "free_text"],
            "generation_guidance": [],
            "review_checklist": [],
            "evidence": ["scope-stage"],
            "generation_trace": {"status": "ok"},
        }

    def _question(self) -> dict[str, object]:
        return {
            "id": "q1",
            "category": "concept",
            "type": "single_choice",
            "title": "Python 赋值符号判断",
            "prompt": "下面哪一个符号用于 **变量赋值**？\n\n- 请选择一个最准确的答案。",
            "question": "下面哪一个符号用于 **变量赋值**？\n\n- 请选择一个最准确的答案。",
            "options": ["=", "==", "!=", ":="],
            "answer": 0,
            "explanation": "`=` 用于赋值，`==` 用于比较相等。",
            "scoring_rubric": ["识别赋值符号", "区分赋值与比较"],
            "capability_tags": ["python-assignment"],
            "source_trace": {"question_source": "agent-injected", "target_capability_ids": ["python-assignment"]},
            "difficulty_level": "basic",
            "difficulty_label": "基础题",
            "difficulty_score": 1,
            "difficulty_reason": "只要求识别赋值符号。",
            "expected_failure_mode": "把赋值和相等比较混淆。",
        }

    def _payload(self) -> dict[str, object]:
        scope = self._scope()
        plan = self._plan()
        return {
            "date": "2026-04-29",
            "topic": "Python 基础",
            "mode": "test-general",
            "session_type": "test",
            "session_intent": "assessment",
            "assessment_kind": "stage-test",
            "test_mode": "general",
            "language_policy": {"user_facing_language": "zh-CN"},
            "plan_source": {
                "language_policy": {"user_facing_language": "zh-CN"},
                "question_scope": scope,
                "question_plan": plan,
                "lesson_grounding_context": {
                    "semantic_profile": "stage-test",
                    "session_intent": "assessment",
                    "assessment_kind": "stage-test",
                    "target_capability_ids": ["python-assignment"],
                    "question_scope": scope,
                    "question_plan": plan,
                    "minimum_pass_shape": {},
                },
                "question_generation_mode": "harness-injected",
                "strict_question_review": {"valid": True, "verdict": "ready", "issues": []},
                "deterministic_question_review": {"valid": True, "verdict": "ready", "issues": []},
            },
            "selection_context": {
                "language_policy": {"user_facing_language": "zh-CN"},
                "question_scope": scope,
                "question_plan": plan,
                "daily_lesson_plan": {
                    "semantic_profile": "stage-test",
                    "session_intent": "assessment",
                    "assessment_kind": "stage-test",
                    "target_capability_ids": ["python-assignment"],
                    "question_scope": scope,
                    "question_plan": plan,
                },
            },
            "materials": [],
            "questions": [self._question()],
        }

    def test_scope_plan_aligned_payload_passes(self) -> None:
        result = validate_questions_payload(self._payload())

        self.assertTrue(result.get("valid"), result.get("issues"))

    def test_scope_session_mismatch_fails(self) -> None:
        payload = self._payload()
        payload["plan_source"]["question_scope"]["session_type"] = "today"

        result = validate_questions_payload(payload)

        self.assertIn("question_scope.session_type_mismatch", result.get("issues", []))

    def test_question_mix_mismatch_fails(self) -> None:
        payload = self._payload()
        payload["plan_source"]["question_plan"]["question_mix"] = {"code": 1}
        payload["selection_context"]["question_plan"] = payload["plan_source"]["question_plan"]

        result = validate_questions_payload(payload)

        self.assertTrue(any("question_plan.question_mix_mismatch:code" in issue for issue in result.get("issues", [])))

    def test_difficulty_distribution_mismatch_fails(self) -> None:
        payload = self._payload()
        payload["plan_source"]["question_plan"]["difficulty_distribution"] = {"medium": 1}
        payload["selection_context"]["question_plan"] = payload["plan_source"]["question_plan"]

        result = validate_questions_payload(payload)

        self.assertIn("question_plan.difficulty_distribution_mismatch:medium:0/1", result.get("issues", []))

    def test_target_capability_uncovered_fails(self) -> None:
        payload = self._payload()
        payload["questions"][0]["capability_tags"] = ["other-capability"]
        payload["questions"][0]["source_trace"] = {"question_source": "agent-injected", "target_capability_ids": ["other-capability"]}

        result = validate_questions_payload(payload)

        self.assertIn("question_scope.target_capability_ids_uncovered:python-assignment", result.get("issues", []))


if __name__ == "__main__":
    unittest.main()
