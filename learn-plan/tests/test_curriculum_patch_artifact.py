from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from learn_feedback.curriculum_patch import pending_patch_items, update_patch_queue_file


class CurriculumPatchArtifactTest(unittest.TestCase):
    def _summary(self) -> dict:
        return {
            "topic": "Python 基础",
            "date": "2026-04-24",
            "overall": "条件判断需要回炉",
            "weaknesses": ["条件判断"],
            "next_actions": ["重做条件判断题"],
            "should_review": True,
            "can_advance": False,
        }

    def _session_facts(self) -> dict:
        return {
            "date": "2026-04-24",
            "topic": "Python 基础",
            "session_dir": "/tmp/session",
            "evidence": ["q2 wrong"],
            "outcome": {"confidence": 0.8},
            "traceability": [{"kind": "test", "ref": "session"}],
        }

    def _patch_candidate(self) -> dict:
        return {
            "id": "2026-04-24:test:Python 基础",
            "status": "proposed",
            "patch_type": "review-adjustment",
            "topic": "Python 基础",
            "created_at": "2026-04-24",
            "source_update_type": "test",
            "rationale": "subagent says review conditionals",
            "proposal": {"review_focus": ["条件判断"], "next_actions": ["重做条件判断题"], "should_review": True, "can_advance": False},
            "application_policy": "pending-user-approval",
            "evidence": ["q2 wrong"],
            "confidence": 0.8,
            "generation_trace": {"stage": "feedback", "generator": "subagent-fixture", "status": "proposed", "artifact_source": "agent-subagent"},
            "traceability": [{"kind": "test", "ref": "patch-candidate"}],
            "quality_review": {"reviewer": "test", "valid": True, "issues": [], "confidence": 0.8},
        }

    def test_missing_patch_candidate_does_not_generate_patch_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "learn-plan.md"
            plan_path.write_text("# Test Plan\n", encoding="utf-8")

            result = update_patch_queue_file(plan_path, self._summary(), self._session_facts(), update_type="test", patch_candidate=None)

            self.assertIsNone(result.get("patch"))
            self.assertEqual(pending_patch_items(result.get("queue", {})), [])

    def test_valid_patch_candidate_is_merged_into_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "learn-plan.md"
            plan_path.write_text("# Test Plan\n", encoding="utf-8")

            result = update_patch_queue_file(plan_path, self._summary(), self._session_facts(), update_type="test", patch_candidate=self._patch_candidate())

            pending = pending_patch_items(result.get("queue", {}))
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0].get("rationale"), "subagent says review conditionals")


if __name__ == "__main__":
    unittest.main()
