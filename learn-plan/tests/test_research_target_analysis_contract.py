from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_workflow.stage_llm import build_stage_candidate_prompt
from learn_workflow.stage_review import review_stage_candidate


class ResearchTargetAnalysisContractTest(unittest.TestCase):
    def _candidate(self) -> dict[str, object]:
        return {
            "contract_version": "learn-plan.workflow.v2",
            "stage": "research",
            "candidate_version": "test",
            "research_report": {
                "goal_target_band": "初级数据科学岗位",
                "required_level_definition": "能完成 Python 数据处理与建模任务",
                "user_facing_report": {"format": "html", "html": "<h1>目标分析</h1>", "summary": ["岗位要求"]},
                "must_master_core": ["Python 工程基础"],
                "evidence_expectations": ["项目代码"],
                "research_brief": "目标能力要求分析",
                "capability_metrics": [
                    {
                        "capability_id": "python-engineering",
                        "observable_behaviors": ["能拆分函数"],
                        "quantitative_indicators": ["正确率"],
                        "diagnostic_methods": ["代码题"],
                        "learning_evidence": ["项目提交"],
                        "source_evidence": ["岗位 JD"],
                    }
                ],
                "evidence_summary": ["岗位 JD"],
                "selection_rationale": ["目标匹配"],
                "diagnostic_scope": {
                    "target_capability_ids": ["python-engineering"],
                    "scoring_dimensions": ["正确性"],
                    "gap_judgement_basis": ["代码表现"],
                },
            },
            "deepsearch_status": "completed",
            "research_plan": {"queries": ["Python 数据科学 岗位 要求"]},
            "evidence": ["research fixture"],
            "confidence": 0.8,
            "generation_trace": {"stage": "research", "generator": "test", "status": "ok"},
            "traceability": [{"kind": "test", "ref": "research"}],
        }

    def test_research_review_requires_evaluator_roles_and_source_categories(self) -> None:
        reviewed = review_stage_candidate("research", self._candidate())
        issues = reviewed.get("quality_review", {}).get("issues", [])

        self.assertIn("research.evaluator_roles_missing", issues)
        self.assertIn("research.source_categories_missing", issues)
        self.assertIn("research.web_source_evidence_missing", issues)

    def test_research_review_accepts_role_and_source_grounded_target_analysis(self) -> None:
        candidate = self._candidate()
        report = candidate["research_report"]
        report["evaluator_roles"] = ["HR", "技术负责人", "一线实践者"]
        report["source_categories"] = ["岗位描述", "经验文档", "课程", "书籍", "练习题", "开源仓库"]
        report["web_source_evidence"] = [
            {"title": "岗位 JD", "url": "https://example.com/job", "claim": "要求 Python 工程能力"}
        ]

        reviewed = review_stage_candidate("research", candidate)
        issues = reviewed.get("quality_review", {}).get("issues", [])

        self.assertNotIn("research.evaluator_roles_missing", issues)
        self.assertNotIn("research.source_categories_missing", issues)
        self.assertNotIn("research.web_source_evidence_missing", issues)

    def test_prompt_demands_role_and_source_grounded_research(self) -> None:
        prompt = build_stage_candidate_prompt(
            "research",
            topic="Python",
            goal="求职",
            level="有基础",
            schedule="每天30分钟",
            preference="混合",
            context={},
        )

        self.assertIn("evaluator_roles", prompt)
        self.assertIn("source_categories", prompt)
        self.assertIn("web_source_evidence", prompt)
        self.assertIn("HR", prompt)
        self.assertIn("技术负责人", prompt)


if __name__ == "__main__":
    unittest.main()
