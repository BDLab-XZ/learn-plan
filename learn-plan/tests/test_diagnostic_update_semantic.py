from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

import learn_test_update
from learn_feedback.diagnostic_update import summarize_diagnostic_progress


class DiagnosticUpdateSemanticTest(unittest.TestCase):
    def _progress(self) -> dict:
        return {
            "topic": "Python 基础",
            "date": "2026-04-24",
            "session": {
                "type": "test",
                "status": "active",
                "started_at": "2026-04-24T08:00:00",
                "assessment_kind": "initial-test",
                "intent": "assessment",
                "plan_execution_mode": "diagnostic",
                "round_index": 1,
                "max_rounds": 2,
                "questions_per_round": 2,
            },
            "questions": {
                "q1": {"stats": {"attempts": 1, "correct_count": 1, "last_status": "correct"}},
                "q2": {"stats": {"attempts": 1, "correct_count": 0, "last_status": "wrong"}},
            },
            "context": {"current_stage": "阶段 1"},
        }

    def _questions_map(self) -> dict:
        return {
            "q1": {"id": "q1", "title": "变量赋值", "category": "concept", "tags": ["变量"]},
            "q2": {"id": "q2", "title": "条件判断", "category": "concept", "tags": ["条件"]},
        }

    def _questions_data(self) -> dict:
        return {"questions": list(self._questions_map().values()), "plan_source": {"topic": "Python 基础"}}

    def _semantic_diagnostic(self) -> dict:
        return {
            "overall": "起点诊断显示条件判断需要补强",
            "recommended_entry_level": "阶段 1：条件判断补强",
            "follow_up_needed": True,
            "stop_reason": "needs-follow-up",
            "diagnostic_profile": {
                "status": "in-progress",
                "follow_up_needed": True,
                "stop_reason": "needs-follow-up",
                "recommended_entry_level": "阶段 1：条件判断补强",
            },
            "evidence": ["q2 wrong"],
            "confidence": 0.8,
            "generation_trace": {"stage": "diagnostic-update", "generator": "subagent-fixture", "status": "ok", "artifact_source": "agent-subagent"},
            "traceability": [{"kind": "test", "ref": "semantic-diagnostic"}],
            "quality_review": {"reviewer": "test", "valid": True, "issues": [], "confidence": 0.8},
        }

    def test_missing_semantic_diagnostic_does_not_generate_diagnostic_conclusion(self) -> None:
        summary = summarize_diagnostic_progress(self._progress(), self._questions_map())

        self.assertEqual(summary.get("semantic_status"), "missing_artifact")
        self.assertIsNone(summary.get("overall"))
        self.assertIsNone(summary.get("recommended_entry_level"))
        self.assertEqual(summary.get("semantic_missing_requirements"), ["semantic_diagnostic"])
        diagnostic_profile = summary.get("diagnostic_profile", {})
        self.assertEqual(diagnostic_profile.get("status"), "missing_artifact")
        self.assertEqual(diagnostic_profile.get("observed_strengths"), ["变量赋值"])
        self.assertEqual(diagnostic_profile.get("observed_weaknesses"), ["条件判断"])

    def test_valid_semantic_diagnostic_populates_semantic_fields(self) -> None:
        summary = summarize_diagnostic_progress(self._progress(), self._questions_map(), semantic_diagnostic=self._semantic_diagnostic())

        self.assertEqual(summary.get("semantic_status"), "ok")
        self.assertEqual(summary.get("overall"), "起点诊断显示条件判断需要补强")
        self.assertEqual(summary.get("recommended_entry_level"), "阶段 1：条件判断补强")
        diagnostic_profile = summary.get("diagnostic_profile", {})
        self.assertTrue(diagnostic_profile.get("follow_up_needed"))
        self.assertEqual(diagnostic_profile.get("stop_reason"), "needs-follow-up")

    def test_cli_semantic_diagnostic_json_updates_learning_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            session_dir = root / "session"
            session_dir.mkdir()
            progress_path = session_dir / "progress.json"
            progress_path.write_text(json.dumps(self._progress(), ensure_ascii=False), encoding="utf-8")
            questions_path = session_dir / "questions.json"
            questions_path.write_text(json.dumps(self._questions_data(), ensure_ascii=False), encoding="utf-8")
            semantic_path = root / "semantic-diagnostic.json"
            semantic_path.write_text(json.dumps(self._semantic_diagnostic(), ensure_ascii=False), encoding="utf-8")
            plan_path = root / "learn-plan.md"
            plan_path.write_text("# Test Plan\n", encoding="utf-8")

            with patch.object(sys, "argv", [
                "learn_test_update.py",
                "--session-dir", str(session_dir),
                "--plan-path", str(plan_path),
                "--semantic-diagnostic-json", str(semantic_path),
            ]), patch("learn_test_update.refresh_workflow_state", return_value={}), patch("sys.stdout", new_callable=io.StringIO):
                exit_code = learn_test_update.main()

            self.assertEqual(exit_code, 0)
            updated_progress = json.loads(progress_path.read_text(encoding="utf-8"))
            result_summary = updated_progress.get("result_summary", {})
            self.assertEqual(result_summary.get("overall"), "起点诊断显示条件判断需要补强")
            self.assertEqual(result_summary.get("recommended_entry_level"), "阶段 1：条件判断补强")
            self.assertIn("semantic diagnostic 状态：ok", plan_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
