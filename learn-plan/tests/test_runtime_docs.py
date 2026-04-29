from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))


class RuntimeDocsTest(unittest.TestCase):
    def test_session_orchestrator_examples_include_required_artifacts(self) -> None:
        docs = [
            SKILL_DIR.parent / "learn-today" / "SKILL.md",
            SKILL_DIR.parent / "learn-test" / "SKILL.md",
            SKILL_DIR / "docs" / "skill-operator-guide.md",
        ]
        for path in docs:
            text = path.read_text(encoding="utf-8")
            self.assertIn("session_orchestrator.py", text, path)
            self.assertIn("--lesson-artifact-json", text, path)
            self.assertIn("--question-artifact-json", text, path)
            self.assertIn("--question-review-json", text, path)

    def test_learn_today_update_docs_do_not_claim_project_path(self) -> None:
        path = SKILL_DIR.parent / "learn-today-update" / "SKILL.md"
        text = path.read_text(encoding="utf-8")

        self.assertNotIn("--project-path", text)
        # 已废弃：功能合并到 /learn-today Step 6，不再保留 CLI 参数引用
        self.assertIn("已废弃", text)

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
            "learn-today-update/SKILL.md": SKILL_DIR.parent / "learn-today-update" / "SKILL.md",
            "learn-test-update/SKILL.md": SKILL_DIR.parent / "learn-test-update" / "SKILL.md",
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
        self.assertIn("缺出题/审题 artifact", combined)
        self.assertIn("阻断", combined)
        self.assertIn("test-grade", combined)
        # learn-test-update 已废弃：语义审查合并到 /learn-test Step 4
        self.assertIn("已废弃", (SKILL_DIR.parent / "learn-test-update" / "SKILL.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
