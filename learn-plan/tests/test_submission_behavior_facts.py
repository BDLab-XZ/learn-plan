from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_feedback.progress_summary import aggregate_diagnostic_targets, build_diagnostic_trigger_facts, build_result_summary, build_session_facts, build_submission_behavior_facts


class SubmissionBehaviorFactsTest(unittest.TestCase):
    def _submit_result(self, qid: str, *, passed: bool, failure_types: list[str] | None = None, submitted_at: str = "2026-04-25T03:00:00Z") -> dict[str, object]:
        return {
            "question_id": qid,
            "question_type": "code",
            "status": "passed" if passed else "failed",
            "passed_public_count": 1 if passed else 0,
            "total_public_count": 1,
            "passed_hidden_count": 1 if passed else 0,
            "total_hidden_count": 1,
            "failed_case_summaries": [] if passed else [{"category": "hidden", "input": {"x": 1}, "expected": 2, "actual_repr": "1", "error": (failure_types or ["wrong_answer"])[0]}],
            "failure_types": failure_types or ([] if passed else ["wrong_answer"]),
            "capability_tags": ["function-arguments"],
            "submitted_at": submitted_at,
        }

    def _progress(self) -> dict[str, object]:
        return {
            "topic": "Python",
            "date": "2026-04-25",
            "session": {"type": "test", "status": "completed"},
            "summary": {"total": 3, "attempted": 3, "correct": 2},
            "questions": {
                "first-pass": {
                    "stats": {
                        "attempts": 1,
                        "pass_count": 1,
                        "last_status": "passed",
                        "last_submit_result": self._submit_result("first-pass", passed=True),
                    },
                    "history": [
                        {"type": "submit", "submitted_at": "2026-04-25T03:00:00Z", "result": self._submit_result("first-pass", passed=True)}
                    ],
                },
                "retry-success": {
                    "stats": {
                        "attempts": 3,
                        "pass_count": 1,
                        "last_status": "passed",
                        "submit_history": [
                            self._submit_result("retry-success", passed=False, failure_types=["argument_error"], submitted_at="2026-04-25T03:01:00Z"),
                            self._submit_result("retry-success", passed=False, failure_types=["runtime_error"], submitted_at="2026-04-25T03:02:00Z"),
                            self._submit_result("retry-success", passed=True, submitted_at="2026-04-25T03:03:00Z"),
                        ],
                    }
                },
                "persistent-failure": {
                    "stats": {
                        "attempts": 2,
                        "pass_count": 0,
                        "last_status": "wrong",
                        "last_submit_result": self._submit_result("persistent-failure", passed=False, failure_types=["hidden_wrong_answer"], submitted_at="2026-04-25T03:05:00Z"),
                    },
                    "history": [
                        {"type": "submit", "submitted_at": "2026-04-25T03:05:00Z", "result": self._submit_result("persistent-failure", passed=False, failure_types=["hidden_wrong_answer"], submitted_at="2026-04-25T03:05:00Z")},
                        {"type": "submit", "submitted_at": "2026-04-25T03:04:00Z", "result": self._submit_result("persistent-failure", passed=False, failure_types=["wrong_answer"], submitted_at="2026-04-25T03:04:00Z")},
                    ],
                },
            },
        }

    def test_submission_behavior_facts_classify_attempt_patterns(self) -> None:
        facts = build_submission_behavior_facts(self._progress())
        by_id = {item["question_id"]: item for item in facts}

        self.assertTrue(by_id["first-pass"]["first_pass"])
        self.assertFalse(by_id["first-pass"]["retry_success"])
        self.assertEqual(by_id["first-pass"]["attempts"], 1)

        self.assertFalse(by_id["retry-success"]["first_pass"])
        self.assertTrue(by_id["retry-success"]["retry_success"])
        self.assertEqual(by_id["retry-success"]["failure_sequence"], ["argument_error", "runtime_error"])
        self.assertIn("argument_error", by_id["retry-success"]["failure_types"])

        self.assertTrue(by_id["persistent-failure"]["persistent_failure"])
        self.assertFalse(by_id["persistent-failure"]["ever_passed"])
        self.assertEqual(by_id["persistent-failure"]["last_failure_types"], ["hidden_wrong_answer"])

    def _diagnostic_progress(self) -> dict[str, object]:
        trigger_wrong = {
            "trigger_type": "wrong_answer",
            "question_id": "choice-assignment",
            "question_type": "single_choice",
            "option_index": 1,
            "selected": True,
            "is_correct_option": False,
            "knowledge_point_ids": ["kp-assignment"],
            "prerequisite_ids": ["kp-expression"],
            "misconception_ids": ["mc-assignment-vs-equality"],
            "capability_tags": ["python-assignment"],
            "evidence": ["user selected option 1"],
            "severity": "medium",
            "requires_follow_up": True,
            "diagnostic_mapping_status": "mapped",
            "diagnostic_role": "distractor",
            "mapping_confidence": 0.82,
        }
        trigger_uncertain = {
            "trigger_type": "uncertain",
            "question_id": "choice-assignment",
            "question_type": "single_choice",
            "option_index": 0,
            "selected": False,
            "is_correct_option": True,
            "knowledge_point_ids": ["kp-assignment"],
            "prerequisite_ids": [],
            "misconception_ids": [],
            "capability_tags": ["python-assignment"],
            "evidence": ["user marked option 0 uncertain"],
            "severity": "low",
            "requires_follow_up": True,
            "diagnostic_mapping_status": "mapped",
            "mapping_confidence": 0.9,
        }
        return {
            "topic": "Python",
            "date": "2026-04-25",
            "session": {"type": "today", "status": "completed"},
            "summary": {"total": 1, "attempted": 1, "correct": 0},
            "questions": {
                "choice-assignment": {
                    "stats": {
                        "attempts": 1,
                        "correct_count": 0,
                        "last_status": "failed",
                        "submit_history": [
                            {
                                "question_id": "choice-assignment",
                                "question_type": "single_choice",
                                "is_correct": False,
                                "selected": [1],
                                "unsure": [0],
                                "diagnostic_triggers": [trigger_wrong, trigger_uncertain],
                                "submitted_at": "2026-04-25T03:06:00Z",
                            },
                            {
                                "question_id": "choice-assignment",
                                "question_type": "single_choice",
                                "is_correct": False,
                                "selected": [1],
                                "unsure": [0],
                                "diagnostic_triggers": [trigger_wrong],
                                "submitted_at": "2026-04-25T03:07:00Z",
                            },
                        ],
                    }
                }
            },
        }

    def test_diagnostic_triggers_deduplicate_and_aggregate_by_knowledge_point(self) -> None:
        triggers = build_diagnostic_trigger_facts(self._diagnostic_progress())

        self.assertEqual(len(triggers), 2)
        targets = aggregate_diagnostic_targets(triggers)
        self.assertEqual(len(targets), 1)
        target = targets[0]
        self.assertEqual(target["knowledge_point_id"], "kp-assignment")
        self.assertEqual(target["trigger_count"], 2)
        self.assertEqual(target["trigger_types"], ["wrong_answer", "uncertain"])
        self.assertEqual(target["source_questions"], ["choice-assignment"])
        self.assertEqual(target["misconception_ids"], ["mc-assignment-vs-equality"])
        self.assertTrue(target["requires_user_follow_up"])
        self.assertIn("fragile_or_uncertain_understanding", target["candidate_diagnoses"])

    def test_result_summary_separates_raw_score_from_uncertain_learning_signal(self) -> None:
        trigger = {
            "trigger_type": "uncertain",
            "knowledge_point_ids": ["kp-assignment"],
            "severity": "low",
        }

        summary = build_result_summary(total=1, attempted=1, correct=1, diagnostic_triggers=[trigger])

        self.assertEqual(summary["raw_score"], {"correct": 1, "attempted": 1, "total": 1, "ratio": 1.0})
        self.assertEqual(summary["learning_score"]["level"], "medium")
        self.assertEqual(summary["learning_score"]["uncertain_count"], 1)
        self.assertEqual(summary["review_recommendation"]["recommended_action"], "mixed_review_then_new")
        self.assertEqual(summary["review_recommendation"]["targets"], [])

    def test_session_facts_include_diagnostic_targets(self) -> None:
        summary = {
            "topic": "Python",
            "date": "2026-04-25",
            "session_type": "today",
            "total": 1,
            "attempted": 1,
            "correct": 0,
            "wrong_items": [],
            "solved_items": [],
            "mastery": {},
        }

        facts = build_session_facts(self._diagnostic_progress(), summary, session_dir=Path("/tmp/session"), update_type="today")

        self.assertEqual(len(facts["diagnostic_triggers"]), 2)
        self.assertEqual(facts["diagnostic_targets"][0]["knowledge_point_id"], "kp-assignment")
        self.assertTrue(any("诊断目标：kp-assignment" in item for item in facts.get("evidence", [])))

    def test_session_facts_include_submission_behavior_without_advice(self) -> None:
        summary = {
            "topic": "Python",
            "date": "2026-04-25",
            "session_type": "test",
            "total": 3,
            "attempted": 3,
            "correct": 2,
            "wrong_items": [],
            "solved_items": [],
            "mastery": {},
        }

        facts = build_session_facts(self._progress(), summary, session_dir=Path("/tmp/session"), update_type="test")

        self.assertIn("submission_behavior_facts", facts)
        behavior = facts["submission_behavior_facts"]
        self.assertEqual(len(behavior), 3)
        rendered = repr(behavior).lower()
        self.assertNotIn("建议", rendered)
        self.assertNotIn("should", rendered)
        self.assertTrue(any("多次失败后通过" in item for item in facts.get("evidence", [])))


if __name__ == "__main__":
    unittest.main()
