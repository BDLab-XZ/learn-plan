from __future__ import annotations

import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
STORE_PATH = SKILL_DIR / "frontend" / "src" / "store" / "runtimeStore.ts"


class RuntimeFrontendSubmitHistoryTest(unittest.TestCase):
    def test_code_submit_persists_structured_submit_history(self) -> None:
        store_source = STORE_PATH.read_text(encoding="utf-8")

        self.assertIn("const submitResult =", store_source)
        self.assertIn("question_id", store_source)
        self.assertIn("passed_public_count", store_source)
        self.assertIn("passed_hidden_count", store_source)
        self.assertIn("failed_case_summaries", store_source)
        self.assertIn("failure_types", store_source)
        self.assertIn("stats.last_submit_result = submitResult", store_source)
        self.assertIn("stats.submit_history.push(submitResult)", store_source)


if __name__ == "__main__":
    unittest.main()
