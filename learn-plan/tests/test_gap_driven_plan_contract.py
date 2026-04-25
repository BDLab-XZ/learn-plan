from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_planning.plan_candidate import build_plan_candidate
from learn_workflow.stage_llm import build_stage_candidate_prompt
from learn_workflow.stage_review import review_stage_candidate


class GapDrivenPlanContractTest(unittest.TestCase):
    def _candidate(self) -> dict[str, object]:
        return {
            "contract_version": "learn-plan.workflow.v2",
            "stage": "planning",
            "candidate_version": "test",
            "plan_candidate": {
                "topic": "Python",
                "goal": "求职",
                "entry_level": "入门",
                "stage_goals": ["阶段一：补齐函数与数据结构"],
                "mastery_checks": ["代码题通过"],
                "stages": [
                    {
                        "id": "stage-1",
                        "name": "Python 基础",
                        "goal": "掌握函数与数据结构",
                    }
                ],
            },
            "evidence": ["planning fixture"],
            "confidence": 0.8,
            "generation_trace": {"stage": "planning", "generator": "test", "status": "ok"},
            "traceability": [{"kind": "test", "ref": "planning"}],
        }

    def test_planning_review_requires_gap_mapping_fields(self) -> None:
        reviewed = review_stage_candidate("planning", self._candidate())
        issues = reviewed.get("quality_review", {}).get("issues", [])

        self.assertIn("planning.problem_definition_missing", issues)
        self.assertIn("planning.stages.0.target_gap_missing", issues)
        self.assertIn("planning.stages.0.capability_metric_missing", issues)
        self.assertIn("planning.stages.0.evidence_requirement_missing", issues)
        self.assertIn("planning.stages.0.approx_time_range_missing", issues)

    def test_planning_review_accepts_gap_driven_stage_fields(self) -> None:
        candidate = self._candidate()
        plan = candidate["plan_candidate"]
        plan["problem_definition"] = ["目标岗位要求和当前基础之间存在函数抽象能力差距"]
        plan["stages"][0].update(
            {
                "target_gap": "函数抽象与基础数据结构不稳",
                "capability_metric": "能独立完成入门代码题",
                "evidence_requirement": "提交记录首次或少量重试通过",
                "approx_time_range": "1-2 周",
            }
        )

        reviewed = review_stage_candidate("planning", candidate)
        issues = reviewed.get("quality_review", {}).get("issues", [])

        self.assertNotIn("planning.problem_definition_missing", issues)
        self.assertNotIn("planning.stages.0.target_gap_missing", issues)
        self.assertNotIn("planning.stages.0.capability_metric_missing", issues)
        self.assertNotIn("planning.stages.0.evidence_requirement_missing", issues)
        self.assertNotIn("planning.stages.0.approx_time_range_missing", issues)

    def test_deterministic_plan_candidate_adds_gap_fields_from_curriculum(self) -> None:
        candidate = build_plan_candidate(
            {"topic": "Python", "goal": "求职", "level": "入门", "research_report": {"evidence_summary": ["岗位要求"]}},
            {
                "family": "python",
                "stages": [
                    {
                        "name": "Python 基础",
                        "goal": "掌握函数",
                        "focus": "函数",
                        "reading": ["教材"],
                        "exercise_types": ["代码题"],
                        "test_gate": "通过代码题",
                        "target_gap": "函数抽象不稳",
                        "capability_metric": "正确完成函数题",
                        "evidence_requirement": "提交历史显示通过",
                        "approx_time_range": "1-2 周",
                    }
                ],
            },
        )

        stage = candidate["plan_candidate"]["stages"][0]
        self.assertEqual(stage["target_gap"], "函数抽象不稳")
        self.assertEqual(stage["capability_metric"], "正确完成函数题")
        self.assertEqual(stage["evidence_requirement"], "提交历史显示通过")
        self.assertEqual(stage["approx_time_range"], "1-2 周")

    def test_prompt_demands_gap_driven_planning(self) -> None:
        prompt = build_stage_candidate_prompt(
            "planning",
            topic="Python",
            goal="求职",
            level="有基础",
            schedule="每天30分钟",
            preference="混合",
            context={},
        )

        self.assertIn("problem_definition", prompt)
        self.assertIn("target_gap", prompt)
        self.assertIn("capability_metric", prompt)
        self.assertIn("evidence_requirement", prompt)
        self.assertIn("approx_time_range", prompt)


if __name__ == "__main__":
    unittest.main()
