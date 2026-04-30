from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_feedback.progress_summary import build_session_facts


class ProgressInteractionFactsTest(unittest.TestCase):
    def test_session_facts_include_agent_learning_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            (session_dir / "interaction_events.jsonl").write_text(
                json.dumps(
                    {
                        "timestamp": "2026-04-30T21:30:00+0800",
                        "session_type": "today",
                        "phase": "during_learning",
                        "source": "main_agent_interaction",
                        "knowledge_points": ["闭包"],
                        "user_event": {"type": "question", "summary": "用户追问闭包变量为什么还存在"},
                        "diagnostic_signal": {"confusion_type": "mental_model_gap", "severity": "medium"},
                        "follow_up_result": {"status": "partial", "prompting_level": "hinted"},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (session_dir / "reflection.json").write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "trigger": {"type": "user_completion_signal"},
                        "rounds": [{"round_index": 1, "question_type": "transfer_application", "result": "solid_after_intervention", "prompting_level": "hinted"}],
                        "mastery_judgement": {"status": "solid_after_intervention", "mastery_level": "explanation", "prompting_level": "hinted"},
                        "learning_path_evidence": ["agent_intervention_needed"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            progress = {
                "topic": "Python",
                "date": "2026-04-30",
                "session": {"type": "today", "status": "finished"},
                "summary": {"total": 1, "attempted": 1, "correct": 1},
                "pre_session_review": {
                    "status": "completed",
                    "passed": False,
                    "result": "needs_review",
                    "weak_points": ["变量生命周期"],
                    "user_decision": "继续新内容但下次复习",
                },
                "completion_signal": {
                    "status": "received",
                    "source": "main_agent",
                    "received_at": "2026-04-30T22:00:00+0800",
                    "user_message_summary": "用户说已经做完，可以更新",
                },
                "interaction_evidence": [],
                "user_feedback": {"difficulty": "偏难", "teaching_style": "希望更多代码例子", "comments": ["少一点抽象类比"]},
                "mastery_judgement": {
                    "status": "solid_after_intervention",
                    "confidence": 0.78,
                    "mastery_level": "explanation",
                    "prompting_level": "hinted",
                    "evidence": ["提示后能解释机制"],
                },
            }
            summary = {
                "topic": "Python",
                "date": "2026-04-30",
                "session_type": "today",
                "total": 1,
                "attempted": 1,
                "correct": 1,
                "mastery": {"reflection_done": True},
            }

            facts = build_session_facts(progress, summary, session_dir=session_dir, update_type="today")

            self.assertEqual(facts["pre_session_review_facts"]["result"], "needs_review")
            self.assertEqual(facts["completion_signal_facts"]["status"], "received")
            self.assertEqual(facts["interaction_event_facts"][0]["summary"], "用户追问闭包变量为什么还存在")
            self.assertEqual(facts["reflection_facts"]["mastery_judgement"]["status"], "solid_after_intervention")
            self.assertEqual(facts["user_feedback_facts"]["difficulty"], "偏难")
            self.assertEqual(facts["mastery_judgement_facts"]["prompting_level"], "hinted")
            evidence_text = "\n".join(facts.get("evidence", []))
            self.assertIn("课前复习", evidence_text)
            self.assertIn("完成信号", evidence_text)
            self.assertIn("学习交互", evidence_text)
            self.assertIn("复盘", evidence_text)
            self.assertIn("用户反馈", evidence_text)
            self.assertIn("掌握判断", evidence_text)


if __name__ == "__main__":
    unittest.main()
