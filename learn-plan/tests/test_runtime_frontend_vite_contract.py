from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = SKILL_DIR / "frontend"
SRC_DIR = FRONTEND_DIR / "src"


class RuntimeFrontendViteContractTest(unittest.TestCase):
    def test_vite_build_drives_production_bootstrap(self) -> None:
        vite_config = (FRONTEND_DIR / "vite.config.ts").read_text(encoding="utf-8")
        bootstrap_source = (SKILL_DIR / "session_bootstrap.py").read_text(encoding="utf-8")

        self.assertIn("../templates/runtime-dist", vite_config)
        self.assertIn("base: './'", vite_config)
        self.assertIn("RUNTIME_FRONTEND_DIST_DIR", bootstrap_source)
        self.assertIn("RUNTIME_FRONTEND_DIST_HTML", bootstrap_source)
        self.assertIn("RUNTIME_FRONTEND_ASSETS_DIR", bootstrap_source)
        self.assertIn("copy_file(RUNTIME_FRONTEND_DIST_HTML, session_dir / \"题集.html\"", bootstrap_source)
        self.assertIn("copy_tree(RUNTIME_FRONTEND_ASSETS_DIR, session_dir / \"assets\"", bootstrap_source)
        self.assertIn("session_dir / \"题集.html\", session_dir / \"questions.json\", session_dir / \"progress.json\", session_dir / \"server.py\"", bootstrap_source)

    def test_vue_runtime_keeps_expected_component_boundaries(self) -> None:
        expected = [
            SRC_DIR / "components" / "Sidebar.vue",
            SRC_DIR / "components" / "ProblemInfoTabs.vue",
            SRC_DIR / "components" / "AnswerWorkspace.vue",
            SRC_DIR / "components" / "StatusPanel.vue",
            SRC_DIR / "components" / "SubmitHistory.vue",
            SRC_DIR / "renderers" / "richText.ts",
            SRC_DIR / "store" / "runtimeStore.ts",
        ]
        for path in expected:
            self.assertTrue(path.exists(), path)

        app_source = (SRC_DIR / "App.vue").read_text(encoding="utf-8")
        self.assertIn("useRuntimeStore", app_source)
        self.assertNotIn("useDemoStore", app_source)
        for marker in ("<Sidebar", "<ProblemInfoTabs", "<AnswerWorkspace"):
            self.assertIn(marker, app_source)

    def test_runtime_store_uses_existing_relative_server_api(self) -> None:
        store_source = (SRC_DIR / "store" / "runtimeStore.ts").read_text(encoding="utf-8")
        for endpoint in ("./questions.json", "./progress", "./run", "./submit", "./finish", "./heartbeat"):
            self.assertIn(endpoint, store_source)
        self.assertIn("question_id", store_source)
        self.assertNotIn("hidden_tests", store_source)


if __name__ == "__main__":
    unittest.main()
