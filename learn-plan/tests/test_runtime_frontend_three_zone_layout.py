from __future__ import annotations

import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = SKILL_DIR / "frontend" / "src"


class RuntimeFrontendThreeZoneLayoutTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app_source = (SRC_DIR / "App.vue").read_text(encoding="utf-8")
        self.sidebar_source = (SRC_DIR / "components" / "Sidebar.vue").read_text(encoding="utf-8")
        self.tabs_source = (SRC_DIR / "components" / "ProblemInfoTabs.vue").read_text(encoding="utf-8")
        self.workspace_source = (SRC_DIR / "components" / "AnswerWorkspace.vue").read_text(encoding="utf-8")
        self.style_source = (SRC_DIR / "style.css").read_text(encoding="utf-8")

    def test_problem_page_has_collapsible_sidebar_control(self) -> None:
        self.assertIn("sidebarCollapsed", self.app_source + self.sidebar_source)
        self.assertIn("sidebar-collapsed", self.app_source + self.style_source)
        self.assertIn("toggleSidebar", self.app_source)
        self.assertIn("emit('toggle')", self.sidebar_source)

    def test_middle_area_has_problem_submissions_and_status_tabs(self) -> None:
        for marker in ("题目描述", "提交记录", "答题状态"):
            self.assertIn(marker, self.tabs_source)
        self.assertIn("panelMode", (SRC_DIR / "store" / "runtimeStore.ts").read_text(encoding="utf-8"))
        self.assertIn("state.panelMode = 'status'", (SRC_DIR / "store" / "runtimeStore.ts").read_text(encoding="utf-8"))

    def test_right_workspace_is_independent_scroll_answer_area(self) -> None:
        self.assertIn("workspace-card", self.workspace_source)
        self.assertIn("overflow: hidden", self.style_source)
        self.assertIn("answer-editor code", self.workspace_source)
        self.assertIn("choice-panel", self.workspace_source)

    def test_submit_switches_to_status_tab(self) -> None:
        store_source = (SRC_DIR / "store" / "runtimeStore.ts").read_text(encoding="utf-8")
        self.assertIn("state.panelMode = 'status'", store_source)

    def test_right_workspace_does_not_render_persistent_result_panel(self) -> None:
        for forbidden in ('<section class="workspace-bottom-panel">', 'id="codeResultPanel"', "控制台摘要", "运行 / 提交结果", "test-result-panel", "未通过测试"):
            self.assertNotIn(forbidden, self.workspace_source)

    def test_concept_and_written_workspace_do_not_embed_status_summary(self) -> None:
        for forbidden in ("concept-meta-grid", "concept-summary-grid compact", "concept-history-panel", "状态 ·"):
            self.assertNotIn(forbidden, self.workspace_source)


if __name__ == "__main__":
    unittest.main()
