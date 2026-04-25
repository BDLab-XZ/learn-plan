from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_runtime.plan_source import make_plan_source
from learn_runtime.session_history import resolve_structured_state_lookup


class HistoryAggregationTest(unittest.TestCase):
    def _write_progress(
        self,
        sessions_dir: Path,
        name: str,
        *,
        topic: str = "Python 基础",
        status: str = "finished",
        assessment_kind: str = "stage",
        plan_execution_mode: str = "normal",
        current_stage: str = "阶段 1",
        topic_cluster: str = "变量",
        mastered: list[str] | None = None,
        weaknesses: list[str] | None = None,
        review_debt: list[str] | None = None,
    ) -> Path:
        session_dir = sessions_dir / name
        session_dir.mkdir(parents=True)
        progress = {
            "topic": topic,
            "date": "2026-04-24",
            "session": {"type": "today", "status": status, "assessment_kind": assessment_kind},
            "context": {
                "current_stage": current_stage,
                "topic_cluster": topic_cluster,
                "plan_execution_mode": plan_execution_mode,
                "plan_source_snapshot": {"current_stage": current_stage, "today_topic": topic_cluster},
            },
            "learning_state": {
                "weaknesses": weaknesses or [],
                "review_focus": weaknesses or [],
            },
            "progression": {
                "mastered_clusters": mastered or [],
                "review_debt": review_debt or [],
            },
        }
        path = session_dir / "progress.json"
        path.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")
        return path

    def test_structured_state_lookup_returns_aggregated_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            plan_path = root / "learn-plan.md"
            plan_path.write_text("# Python 基础\n", encoding="utf-8")
            sessions_dir = root / "sessions"
            self._write_progress(sessions_dir, "day1", topic_cluster="变量", mastered=["变量"], weaknesses=["条件判断"])
            self._write_progress(sessions_dir, "day2", topic_cluster="循环", mastered=["循环"], weaknesses=["函数参数"])
            self._write_progress(sessions_dir, "day3", topic_cluster="列表", mastered=["列表"], review_debt=["字典遍历"])

            lookup = resolve_structured_state_lookup(plan_path, "Python 基础")

            self.assertEqual(lookup.get("status"), "found")
            self.assertEqual(len(lookup.get("progress_states", [])), 3)
            aggregates = lookup.get("aggregates", {})
            self.assertEqual(aggregates.get("history_count"), 3)
            self.assertEqual(aggregates.get("covered"), ["变量", "阶段 1", "循环", "列表"])
            self.assertEqual(aggregates.get("weakness_focus"), ["条件判断", "函数参数", "字典遍历"])

    def test_stage_test_plan_source_uses_aggregated_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            plan_path = root / "learn-plan.md"
            plan_path.write_text("# Python 基础\n\n## 学习计划\n- 当前主题：Python 基础\n", encoding="utf-8")
            sessions_dir = root / "sessions"
            self._write_progress(sessions_dir, "day1", topic_cluster="变量", mastered=["变量"], weaknesses=["条件判断"])
            self._write_progress(sessions_dir, "day2", topic_cluster="循环", mastered=["循环"], weaknesses=["函数参数"])

            source = make_plan_source("Python 基础", "test", "mixed", plan_path.read_text(encoding="utf-8"), plan_path=plan_path)

            self.assertEqual(source.get("basis"), "progress-state")
            self.assertEqual(source.get("history_count"), 2)
            self.assertEqual(source.get("covered"), ["变量", "阶段 1", "循环"])
            self.assertEqual(source.get("weakness_focus"), ["条件判断", "函数参数"])
            self.assertEqual(source.get("history_state", {}).get("normalized_status"), "ok")

    def test_initial_diagnostic_progress_is_not_reused_as_stage_test_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            plan_path = root / "learn-plan.md"
            plan_path.write_text("# Python 基础\n\n## 学习计划\n- 当前主题：Python 基础\n", encoding="utf-8")
            sessions_dir = root / "sessions"
            self._write_progress(
                sessions_dir,
                "initial",
                assessment_kind="initial-test",
                plan_execution_mode="diagnostic",
                topic_cluster="诊断题",
                mastered=["诊断题"],
                weaknesses=["条件判断"],
            )

            source = make_plan_source("Python 基础", "test", "mixed", plan_path.read_text(encoding="utf-8"), plan_path=plan_path)

            self.assertNotEqual(source.get("basis"), "progress-state")
            self.assertEqual(source.get("progress_state_anchor"), str(sessions_dir / "initial" / "progress.json"))


if __name__ == "__main__":
    unittest.main()
