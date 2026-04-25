from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_workflow.stage_review import review_stage_candidate
from learn_workflow.state_machine import normalize_clarification_artifact, resolve_assessment_budget_preference


class ClarificationArtifactContractTest(unittest.TestCase):
    def _candidate(self) -> dict[str, object]:
        return {
            "contract_version": "learn-plan.workflow.v2",
            "stage": "clarification",
            "candidate_version": "test",
            "questionnaire": {
                "topic": "Python",
                "goal": "一线城市数据科学或大模型应用岗位面试水平",
                "success_criteria": ["能通过 Python 高频面试题", "能完成数据处理脚本"],
                "current_level_self_report": "有 Python 基础，学过 pandas、numpy",
                "time_constraints": {"session_length": "30 分钟内", "frequency": "灵活"},
            },
            "clarification_state": {"open_questions": [], "resolved_items": []},
            "preference_state": {"status": "confirmed", "pending_items": []},
            "consultation_state": {
                "status": "complete",
                "current_topic_id": "assessment_scope",
                "topic_order": ["learning_purpose", "exam_or_job_target", "success_criteria", "current_level", "constraints", "assessment_scope"],
                "topics": [
                    {
                        "id": "learning_purpose",
                        "required": True,
                        "status": "resolved",
                        "exit_criteria": ["目标场景已明确"],
                        "confirmed_values": {"goal": "一线城市数据科学或大模型应用岗位面试水平"},
                        "open_questions": [],
                        "assumptions": [],
                        "ambiguities": [],
                        "evidence": ["用户目标"],
                    },
                    {
                        "id": "exam_or_job_target",
                        "required": True,
                        "status": "resolved",
                        "exit_criteria": ["目标岗位范围已明确"],
                        "confirmed_values": {"target": "一线城市数据科学或大模型应用岗位"},
                        "open_questions": [],
                        "assumptions": [],
                        "ambiguities": [],
                        "evidence": ["用户目标"],
                    },
                    {
                        "id": "success_criteria",
                        "required": True,
                        "status": "resolved",
                        "exit_criteria": ["用户认可的达标证据已明确"],
                        "confirmed_values": {"success_criteria": ["能通过 Python 高频面试题"]},
                        "open_questions": [],
                        "assumptions": [],
                        "ambiguities": [],
                        "evidence": ["用户目标"],
                    },
                    {
                        "id": "current_level",
                        "required": True,
                        "status": "resolved",
                        "exit_criteria": ["当前水平有具体证据"],
                        "confirmed_values": {"current_level_self_report": "有 Python 基础，学过 pandas、numpy"},
                        "open_questions": [],
                        "assumptions": [],
                        "ambiguities": [],
                        "evidence": ["用户自报"],
                    },
                    {
                        "id": "constraints",
                        "required": True,
                        "status": "resolved",
                        "exit_criteria": ["频率、单次时长、截止日期或作息约束至少明确一类"],
                        "confirmed_values": {"session_length": "30 分钟内", "frequency": "灵活"},
                        "open_questions": [],
                        "assumptions": [],
                        "ambiguities": [],
                        "evidence": ["用户约束"],
                    },
                    {
                        "id": "assessment_scope",
                        "required": True,
                        "status": "resolved",
                        "exit_criteria": ["最多测评轮数已确认", "每轮题量已确认"],
                        "confirmed_values": {"max_rounds": 3, "questions_per_round": 8},
                        "open_questions": [],
                        "assumptions": [],
                        "ambiguities": [],
                        "evidence": ["用户接受 deep 起点评测"],
                    },
                ],
                "thread": [],
                "open_questions": [],
                "assumptions": [],
            },
            "language_policy": {"user_facing_language": "zh-CN"},
            "theme_inventory": ["学习目的", "目标岗位范围", "达标标准", "当前基础", "时间约束", "测评范围"],
            "learner_profile": {
                "summary": "有 Python 基础，目标是一线城市数据科学或大模型应用岗位面试水平",
                "background": ["学过 pandas、numpy"],
                "goal_context": ["求职面试"],
                "constraints": ["30 分钟内，频率灵活"],
                "learning_preferences": ["混合"],
                "confirmation_status": "pending_user_confirmation",
                "confirmation_prompt": "请确认这个用户画像是否准确。",
            },
            "generation_trace": {"prompt_version": "test", "generator": "subagent", "status": "ok"},
            "evidence": ["用户回答"],
            "confidence": 0.8,
            "traceability": [{"kind": "conversation", "ref": "user"}],
            "quality_review": {"valid": True, "issues": []},
        }

    def test_assessment_budget_aliases_project_to_mastery_preferences(self) -> None:
        normalized = normalize_clarification_artifact(self._candidate())

        budget = resolve_assessment_budget_preference(normalized)
        self.assertEqual(budget.get("max_assessment_rounds_preference"), 3)
        self.assertEqual(budget.get("questions_per_round_preference"), 8)
        mastery = normalized.get("questionnaire", {}).get("mastery_preferences", {})
        self.assertEqual(mastery.get("max_assessment_rounds_preference"), 3)
        self.assertEqual(mastery.get("questions_per_round_preference"), 8)

    def test_clarification_candidate_with_budget_aliases_passes_stage_review(self) -> None:
        reviewed = review_stage_candidate("clarification", self._candidate())
        issues = reviewed.get("quality_review", {}).get("issues", [])

        self.assertNotIn("clarification.max_assessment_rounds_preference_missing", issues)
        self.assertNotIn("clarification.questions_per_round_preference_missing", issues)

    def test_cli_injected_clarification_candidate_with_budget_aliases_does_not_report_missing_budget(self) -> None:
        with tempfile.TemporaryDirectory(prefix="learn-plan-clarification-cli.") as tmp:
            root = Path(tmp)
            candidate_path = root / "clarification_candidate.json"
            candidate_path.write_text(json.dumps(self._candidate(), ensure_ascii=False), encoding="utf-8")

            result = subprocess.run(
                [
                    "python3",
                    str(SKILL_DIR / "learn_plan.py"),
                    "--topic",
                    "Python",
                    "--goal",
                    "一线城市数据科学或大模型应用岗位面试水平",
                    "--level",
                    "有 Python 基础，学过 pandas、numpy",
                    "--schedule",
                    "30 分钟内，频率灵活",
                    "--preference",
                    "混合",
                    "--plan-path",
                    str(root / "learn-plan.md"),
                    "--materials-dir",
                    str(root / "materials"),
                    "--mode",
                    "draft",
                    "--stdout-json",
                    "--stage-candidate-json",
                    str(candidate_path),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertIn(result.returncode, {0, 2}, result.stderr)
            combined_output = f"{result.stdout}\n{result.stderr}"
            self.assertNotIn("clarification.max_assessment_rounds_preference_missing", combined_output)
            self.assertNotIn("clarification.questions_per_round_preference_missing", combined_output)
            persisted = json.loads((root / ".learn-workflow" / "clarification.json").read_text(encoding="utf-8"))
            mastery = persisted.get("questionnaire", {}).get("mastery_preferences", {})
            self.assertEqual(mastery.get("max_assessment_rounds_preference"), 3)
            self.assertEqual(mastery.get("questions_per_round_preference"), 8)
            workflow_state = json.loads((root / ".learn-workflow" / "workflow_state.json").read_text(encoding="utf-8"))
            self.assertEqual(workflow_state.get("blocking_stage"), "research")
            self.assertEqual(workflow_state.get("recommended_mode"), "research-report")


if __name__ == "__main__":
    unittest.main()
