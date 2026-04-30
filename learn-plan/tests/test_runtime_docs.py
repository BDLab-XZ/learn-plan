from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_DIR.parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))


class RuntimeDocsTest(unittest.TestCase):
    def test_session_orchestrator_examples_include_required_artifacts(self) -> None:
        today = (SKILL_DIR.parent / "learn-today" / "SKILL.md").read_text(encoding="utf-8")
        test = (SKILL_DIR.parent / "learn-test" / "SKILL.md").read_text(encoding="utf-8")
        guide = (SKILL_DIR / "docs" / "skill-operator-guide.md").read_text(encoding="utf-8")

        for text in (today, test, guide):
            self.assertIn("session_orchestrator.py", text)
            self.assertIn("--question-scope-json", text)
            self.assertIn("--question-plan-json", text)
            self.assertIn("--question-artifact-json", text)
            self.assertIn("--question-review-json", text)

        self.assertIn("--lesson-artifact-json", today)
        self.assertNotIn("--lesson-artifact-json", test)
        self.assertNotIn("--lesson-html-json", test)

    def test_deprecated_update_skill_manifests_are_not_registered(self) -> None:
        manifests = [
            SKILLS_ROOT / "learn-today-update" / "SKILL.md",
            SKILLS_ROOT / "learn-test-update" / "SKILL.md",
            SKILL_DIR.parent / "learn-today-update" / "SKILL.md",
            SKILL_DIR.parent / "learn-test-update" / "SKILL.md",
        ]
        for path in manifests:
            self.assertFalse(path.exists(), path)

    def test_main_entrypoints_own_feedback_writeback_steps(self) -> None:
        today = (SKILL_DIR.parent / "learn-today" / "SKILL.md").read_text(encoding="utf-8")
        test = (SKILL_DIR.parent / "learn-test" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Step 6", today)
        self.assertIn("复盘", today)
        self.assertIn("回写", today)
        self.assertIn("Step 7", test)
        self.assertIn("测试后复盘", test)
        self.assertIn("回写", test)

    def test_entrypoints_define_agent_evidence_workflow(self) -> None:
        docs = {
            "learn-today/SKILL.md": SKILL_DIR.parent / "learn-today" / "SKILL.md",
            "learn-test/SKILL.md": SKILL_DIR.parent / "learn-test" / "SKILL.md",
            "skill-operator-guide.md": SKILL_DIR / "docs" / "skill-operator-guide.md",
            "state-files.md": SKILL_DIR / "docs" / "state-files.md",
            "contracts.md": SKILL_DIR / "docs" / "contracts.md",
            "runtime-compatibility.md": SKILL_DIR / "docs" / "runtime-compatibility.md",
        }
        combined = "\n".join(path.read_text(encoding="utf-8") for path in docs.values())

        for token in (
            "pre_session_review",
            "interaction_events.jsonl",
            "reflection.json",
            "completion_signal",
            "mastery_judgement",
            "learn_session_evidence_update.py",
            "当前教学/练习微调",
            "pending-user-approval",
        ):
            self.assertIn(token, combined)

    def test_docs_define_selective_subagent_strategy(self) -> None:
        docs = {
            "learn-plan/SKILL.md": SKILL_DIR / "SKILL.md",
            "skill-operator-guide.md": SKILL_DIR / "docs" / "skill-operator-guide.md",
            "clarification-stage.md": SKILL_DIR / "docs" / "clarification-stage.md",
            "research-stage.md": SKILL_DIR / "docs" / "research-stage.md",
            "WORKFLOW_DESIGN.md": SKILL_DIR / "WORKFLOW_DESIGN.md",
            "learn-today/SKILL.md": SKILL_DIR.parent / "learn-today" / "SKILL.md",
            "learn-test/SKILL.md": SKILL_DIR.parent / "learn-test" / "SKILL.md",
            "question-schema.md": SKILL_DIR / "docs" / "question-schema.md",
            "lesson-schema.md": SKILL_DIR / "docs" / "lesson-schema.md",
        }
        combined = "\n".join(path.read_text(encoding="utf-8") for path in docs.values())

        self.assertNotIn("Agent-subagent-only", combined)
        self.assertNotIn("所有 workflow candidate 都必须 subagent 生成", combined)
        self.assertIn("selective subagent strategy", combined)
        self.assertIn("主 agent", combined)
        self.assertIn("subagent", combined)
        self.assertIn("澄清", combined)
        self.assertIn("编排", combined)
        self.assertIn("CLI 验证", combined)
        self.assertIn("检索", combined)
        self.assertIn("出题", combined)
        self.assertIn("严格审题", combined)
        self.assertIn("语义审查", combined)
        self.assertIn("缺 scope/plan/出题/审题 artifact", combined)
        self.assertIn("阻断", combined)
        self.assertIn("test-grade", combined)


if __name__ == "__main__":
    unittest.main()
