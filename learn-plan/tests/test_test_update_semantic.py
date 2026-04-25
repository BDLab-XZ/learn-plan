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


class TestUpdateSemanticTest(unittest.TestCase):
    def _progress(self) -> dict:
        return {
            "topic": "Python 基础",
            "date": "2026-04-24",
            "session": {"type": "test", "status": "active", "started_at": "2026-04-24T08:00:00", "test_mode": "stage"},
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
        }

    def _questions_data(self) -> dict:
        return {
            "questions": [
                {"id": "q1", "title": "变量赋值", "category": "concept", "tags": ["变量"]},
                {"id": "q2", "title": "条件判断", "category": "concept", "tags": ["条件"]},
            ],
            "plan_source": {"covered": ["变量"], "weakness_focus": ["条件判断"]},
        }

    def _semantic_review(self) -> dict:
        return {
            "overall": "阶段测试显示条件判断仍需巩固",
            "weaknesses": ["条件判断分支推理"],
            "next_actions": ["重做条件判断阶段题"],
            "should_review": True,
            "can_advance": False,
            "review_decision": "先回退复习条件判断",
            "advance_decision": "暂不进入下一阶段",
            "evidence": ["q2 连续错误"],
            "confidence": 0.8,
            "generation_trace": {"stage": "test-update", "generator": "subagent-fixture", "status": "ok", "artifact_source": "agent-subagent"},
            "traceability": [{"kind": "test", "ref": "semantic-review"}],
            "quality_review": {"reviewer": "test", "valid": True, "issues": [], "confidence": 0.8},
        }

    def test_missing_semantic_review_does_not_generate_natural_language_advice(self) -> None:
        summary = learn_test_update.summarize_test_progress(self._progress(), self._questions_data())

        self.assertEqual(summary.get("semantic_status"), "missing_artifact")
        self.assertIsNone(summary.get("overall"))
        self.assertEqual(summary.get("weaknesses"), [])
        self.assertEqual(summary.get("next_actions"), [])
        self.assertFalse(summary.get("can_advance"))
        self.assertEqual(summary.get("semantic_missing_requirements"), ["semantic_review"])
        self.assertEqual([item["title"] for item in summary.get("wrong_items", [])], ["条件判断"])

    def test_valid_semantic_review_populates_semantic_fields(self) -> None:
        summary = learn_test_update.summarize_test_progress(self._progress(), self._questions_data(), semantic_review=self._semantic_review())

        self.assertEqual(summary.get("semantic_status"), "ok")
        self.assertEqual(summary.get("overall"), "阶段测试显示条件判断仍需巩固")
        self.assertEqual(summary.get("weaknesses"), ["条件判断分支推理"])
        self.assertEqual(summary.get("next_actions"), ["重做条件判断阶段题"])
        self.assertTrue(summary.get("should_review"))
        self.assertFalse(summary.get("can_advance"))
        self.assertEqual(summary.get("review_decision"), "先回退复习条件判断")
        self.assertEqual(summary.get("advance_decision"), "暂不进入下一阶段")

    def test_cli_semantic_review_json_updates_learning_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            session_dir = root / "session"
            session_dir.mkdir()
            progress_path = session_dir / "progress.json"
            progress_path.write_text(json.dumps(self._progress(), ensure_ascii=False), encoding="utf-8")
            questions_path = session_dir / "questions.json"
            questions_path.write_text(json.dumps(self._questions_data(), ensure_ascii=False), encoding="utf-8")
            semantic_path = root / "semantic-review.json"
            semantic_path.write_text(json.dumps(self._semantic_review(), ensure_ascii=False), encoding="utf-8")
            plan_path = root / "learn-plan.md"
            plan_path.write_text("# Test Plan\n", encoding="utf-8")

            with patch.object(sys, "argv", [
                "learn_test_update.py",
                "--session-dir", str(session_dir),
                "--plan-path", str(plan_path),
                "--semantic-review-json", str(semantic_path),
            ]), patch("learn_test_update.refresh_workflow_state", return_value={}), patch("sys.stdout", new_callable=io.StringIO):
                exit_code = learn_test_update.main()

            self.assertEqual(exit_code, 0)
            updated_progress = json.loads(progress_path.read_text(encoding="utf-8"))
            learning_state = updated_progress.get("learning_state", {})
            self.assertEqual(learning_state.get("overall"), "阶段测试显示条件判断仍需巩固")
            self.assertEqual(learning_state.get("weaknesses"), ["条件判断分支推理"])
            self.assertEqual(learning_state.get("next_actions"), ["重做条件判断阶段题"])
            self.assertIn("semantic review 状态：ok", plan_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
