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

import learn_today_update


class TodayUpdateSemanticTest(unittest.TestCase):
    def _progress(self) -> dict:
        return {
            "topic": "Python 基础",
            "date": "2026-04-24",
            "session": {"type": "today", "status": "active", "started_at": "2026-04-24T08:00:00"},
            "summary": {"total": 2, "attempted": 2, "correct": 1},
            "questions": {
                "q1": {"stats": {"attempts": 1, "correct_count": 1, "last_status": "correct"}},
                "q2": {"stats": {"attempts": 2, "correct_count": 0, "last_status": "wrong"}},
            },
            "mastery_checks": {
                "reading_checklist": ["变量"],
                "session_exercises": ["q1", "q2"],
                "reflection": ["复盘"],
            },
            "context": {
                "mastery_targets": {"reading_checklist": ["变量"], "session_exercises": ["基础题"], "reflection": ["复盘"]},
                "today_teaching_brief": {"new_learning_focus": ["函数"]},
                "lesson_focus_points": ["变量", "条件判断"],
            },
        }

    def _questions_map(self) -> dict:
        return {
            "q1": {"title": "变量赋值", "category": "concept", "tags": ["变量"]},
            "q2": {"title": "条件判断", "category": "concept", "tags": ["条件"]},
        }

    def test_missing_semantic_summary_does_not_generate_natural_language_advice(self) -> None:
        summary = learn_today_update.summarize_progress(self._progress(), self._questions_map())

        self.assertEqual(summary.get("semantic_status"), "missing_artifact")
        self.assertIsNone(summary.get("overall"))
        self.assertEqual(summary.get("review_focus"), [])
        self.assertEqual(summary.get("next_learning"), [])
        self.assertEqual(summary.get("high_freq_errors"), ["条件判断"])
        self.assertEqual(summary.get("semantic_missing_requirements"), ["semantic_summary"])

    def _semantic_summary(self) -> dict:
        return {
            "overall": "条件判断需要回炉",
            "review_focus": ["重做条件判断错题"],
            "next_learning": ["学习函数定义"],
            "should_review": True,
            "can_advance": False,
            "evidence": ["q2 错两次"],
            "confidence": 0.8,
            "generation_trace": {"stage": "today-update", "generator": "subagent-fixture", "status": "ok", "artifact_source": "agent-subagent"},
            "traceability": [{"kind": "test", "ref": "semantic-summary"}],
            "quality_review": {"reviewer": "test", "valid": True, "issues": [], "confidence": 0.8},
        }

    def test_valid_semantic_summary_populates_semantic_fields(self) -> None:
        summary = learn_today_update.summarize_progress(self._progress(), self._questions_map(), semantic_summary=self._semantic_summary())

        self.assertEqual(summary.get("semantic_status"), "ok")
        self.assertEqual(summary.get("overall"), "条件判断需要回炉")
        self.assertEqual(summary.get("review_focus"), ["重做条件判断错题"])
        self.assertEqual(summary.get("next_learning"), ["学习函数定义"])
        self.assertTrue(summary.get("should_review"))
        self.assertFalse(summary.get("can_advance"))

    def test_cli_semantic_summary_json_updates_learning_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            session_dir = root / "session"
            session_dir.mkdir()
            progress_path = session_dir / "progress.json"
            progress_path.write_text(json.dumps(self._progress(), ensure_ascii=False), encoding="utf-8")
            questions_path = session_dir / "questions.json"
            questions_path.write_text(json.dumps({"questions": [{"id": qid, **item} for qid, item in self._questions_map().items()]}, ensure_ascii=False), encoding="utf-8")
            semantic_path = root / "semantic.json"
            semantic_path.write_text(json.dumps(self._semantic_summary(), ensure_ascii=False), encoding="utf-8")
            plan_path = root / "learn-plan.md"
            plan_path.write_text("# Test Plan\n", encoding="utf-8")

            with patch.object(sys, "argv", [
                "learn_today_update.py",
                "--session-dir", str(session_dir),
                "--plan-path", str(plan_path),
                "--semantic-summary-json", str(semantic_path),
            ]), patch("learn_today_update.refresh_workflow_state", return_value={}), patch("sys.stdout", new_callable=io.StringIO):
                exit_code = learn_today_update.main()

            self.assertEqual(exit_code, 0)
            updated_progress = json.loads(progress_path.read_text(encoding="utf-8"))
            learning_state = updated_progress.get("learning_state", {})
            self.assertEqual(learning_state.get("overall"), "条件判断需要回炉")
            self.assertEqual(learning_state.get("review_focus"), ["重做条件判断错题"])
            self.assertEqual(learning_state.get("next_learning"), ["学习函数定义"])
            self.assertIn("semantic summary 状态：ok", plan_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
