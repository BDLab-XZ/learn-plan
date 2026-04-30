from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

import learn_session_evidence_update


class AgentEvidenceUpdateTest(unittest.TestCase):
    def _event(self) -> dict[str, object]:
        return {
            "timestamp": "2026-04-30T21:30:00+0800",
            "session_type": "today",
            "phase": "during_learning",
            "source": "main_agent_interaction",
            "knowledge_points": ["闭包"],
            "user_event": {
                "type": "question",
                "summary": "用户追问为什么内层函数还能访问外层变量",
                "raw_excerpt": "为什么这个变量在外面函数结束后还存在？",
            },
            "diagnostic_signal": {
                "confusion_type": "mental_model_gap",
                "severity": "medium",
                "evidence": "用户混淆调用栈结束和对象生命周期",
            },
            "follow_up_result": {
                "status": "partial",
                "prompting_level": "hinted",
                "evidence": "用户能复述现象，但迁移还不稳",
            },
            "recommended_action": "下次用装饰器例子轻量复习闭包",
        }

    def _reflection(self) -> dict[str, object]:
        return {
            "status": "completed",
            "trigger": {
                "type": "user_completion_signal",
                "user_message_summary": "用户表示已经做完，可以开始复盘更新",
                "received_at": "2026-04-30T22:10:00+0800",
            },
            "session_type": "today",
            "rounds": [
                {
                    "round_index": 1,
                    "question_type": "transfer_application",
                    "knowledge_points": ["闭包"],
                    "question": "外层函数返回后，内层函数为什么还能访问外层变量？",
                    "user_answer_summary": "用户需要提示后能说明变量被函数对象引用",
                    "agent_feedback_summary": "纠正调用结束不等于对象消失",
                    "result": "solid_after_intervention",
                    "prompting_level": "hinted",
                }
            ],
            "mastery_judgement": {
                "status": "solid_after_intervention",
                "mastery_level": "explanation_and_near_transfer",
                "confidence": 0.78,
                "evidence": ["能用自己的话解释机制", "需要一次提示后能迁移"],
                "blocking_gaps": [],
                "next_session_reinforcement": ["用装饰器例子复习闭包"],
                "prompting_level": "hinted",
            },
            "learning_path_evidence": ["initial_misconception_observed", "agent_intervention_needed"],
            "review_debt": [],
            "user_feedback": {"teaching_style": "希望更多代码例子", "comments": ["例子越具体越好"]},
        }

    def test_agent_evidence_update_writes_event_reflection_and_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            progress_path = session_dir / "progress.json"
            progress_path.write_text(
                json.dumps(
                    {
                        "topic": "Python 基础",
                        "date": "2026-04-30",
                        "mastery_checks": {"reflection": []},
                        "update_history": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            payload_path = session_dir / "payload.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "events": [self._event()],
                        "completion_signal": {
                            "status": "received",
                            "source": "main_agent",
                            "received_at": "2026-04-30T22:00:00+0800",
                            "user_message_summary": "用户说已经做完题目，可以更新",
                        },
                        "reflection": self._reflection(),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                session_dir=str(session_dir),
                event_json=[],
                event_jsonl=[],
                reflection_json=None,
                completion_signal_json=None,
                payload_json=str(payload_path),
                stdin_json=False,
                stdout_json=True,
            )

            result = learn_session_evidence_update.run(args)

            self.assertEqual(result["event_count"], 1)
            event_lines = (session_dir / "interaction_events.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(event_lines), 1)
            self.assertEqual(json.loads(event_lines[0])["user_event"]["type"], "question")
            reflection = json.loads((session_dir / "reflection.json").read_text(encoding="utf-8"))
            self.assertEqual(reflection["status"], "completed")
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
            self.assertEqual(progress["completion_signal"]["status"], "received")
            self.assertEqual(progress["mastery_judgement"]["status"], "solid_after_intervention")
            self.assertEqual(progress["user_feedback"]["teaching_style"], "希望更多代码例子")
            self.assertEqual(progress["interaction_evidence"][0]["summary"], "用户追问为什么内层函数还能访问外层变量")
            self.assertTrue(progress["mastery_checks"]["reflection"])
            self.assertEqual(progress["update_history"][-1]["update_type"], "agent-evidence")

    def test_invalid_event_without_diagnostic_or_follow_up_is_rejected(self) -> None:
        event = self._event()
        event.pop("diagnostic_signal")
        event.pop("follow_up_result")

        with self.assertRaises(learn_session_evidence_update.EvidenceValidationError):
            learn_session_evidence_update.validate_event(event)


if __name__ == "__main__":
    unittest.main()
