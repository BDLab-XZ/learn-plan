from __future__ import annotations

import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = SKILL_DIR / "frontend" / "src"


class RuntimeFrontendContractTest(unittest.TestCase):
    def test_code_submit_payload_includes_question_id_without_hidden_tests(self) -> None:
        store_source = (SRC_DIR / "store" / "runtimeStore.ts").read_text(encoding="utf-8")

        self.assertIn("fetch('./submit'", store_source)
        self.assertIn("question_id", store_source)
        self.assertIn("function_name", store_source)
        self.assertNotIn("hidden_tests", store_source)
        self.assertNotIn("test_cases: cases", store_source)

    def test_code_run_payload_includes_question_id(self) -> None:
        store_source = (SRC_DIR / "store" / "runtimeStore.ts").read_text(encoding="utf-8")

        self.assertIn("fetchJson<SubmitResult>('./run'", store_source)
        self.assertIn("question_id: question.id", store_source)

    def test_objective_questions_do_not_render_run_button(self) -> None:
        workspace_source = (SRC_DIR / "components" / "AnswerWorkspace.vue").read_text(encoding="utf-8")

        self.assertIn("canRunQuestion", workspace_source)
        self.assertIn("props.question.type === 'code' || props.question.type === 'sql'", workspace_source)
        self.assertIn("v-if=\"canRunQuestion\"", workspace_source)

    def test_code_page_renders_structured_leetcode_fields(self) -> None:
        store_source = (SRC_DIR / "store" / "runtimeStore.ts").read_text(encoding="utf-8")
        tabs_source = (SRC_DIR / "components" / "ProblemInfoTabs.vue").read_text(encoding="utf-8")

        for field in ("problem_statement", "input_spec", "output_spec", "calculation_spec", "constraints", "examples", "public_tests"):
            self.assertIn(field, store_source)
        self.assertIn("calculationSpec", store_source)
        self.assertIn("计算说明", tabs_source)
        self.assertNotIn("hidden_tests", tabs_source)
        self.assertNotIn("公开测试", tabs_source)
        self.assertNotIn("io-spec-grid", tabs_source)
        self.assertIn("ExampleDisplaySection", tabs_source)

    def test_example_parameter_display_uses_tag_single_column_layout(self) -> None:
        example_source = (SRC_DIR / "components" / "ExampleDisplaySection.vue").read_text(encoding="utf-8")
        style_source = (SRC_DIR / "style.css").read_text(encoding="utf-8")

        self.assertIn("example-parameter-row", example_source)
        self.assertIn("border-radius: 999px", style_source)
        self.assertIn("grid-template-columns: minmax(0, 1fr)", style_source)
        self.assertNotIn("grid-template-columns: minmax(92px, 0.35fr) minmax(0, 1fr)", style_source)

    def test_problem_layout_has_scroll_resize_and_long_text_guards(self) -> None:
        style_source = (SRC_DIR / "style.css").read_text(encoding="utf-8")
        app_source = (SRC_DIR / "App.vue").read_text(encoding="utf-8")

        for marker in ("overflow-wrap: anywhere", "word-break: break-word", "min-width: 0", "overflow: hidden", "overflow: auto"):
            self.assertIn(marker, style_source)
        rich_text_code_block = style_source.split(".rich-text-code-block", 1)[1].split("}", 1)[0]
        self.assertIn("overflow: auto", rich_text_code_block)
        self.assertNotIn("white-space: pre-wrap", rich_text_code_block)
        for marker in ("column-resizer", "startColumnResize", "--sidebar-width", "--problem-width"):
            self.assertIn(marker, app_source + style_source)

    def test_problem_title_tags_wrap_without_squeezing_difficulty_badge(self) -> None:
        tabs_source = (SRC_DIR / "components" / "ProblemInfoTabs.vue").read_text(encoding="utf-8")
        style_source = (SRC_DIR / "style.css").read_text(encoding="utf-8")

        self.assertIn("title-tags", tabs_source)
        self.assertIn("title-tag", tabs_source)
        self.assertIn("v-for=\"tag in props.question.tags\"", tabs_source)
        self.assertNotIn("tags.join(' / ')", tabs_source)
        self.assertIn(".title-tags", style_source)
        self.assertIn(".title-tag", style_source)
        self.assertIn("flex-wrap: wrap", style_source)
        self.assertIn("flex: 0 0 auto", style_source)
        self.assertIn("white-space: nowrap", style_source)

    def test_problem_body_uses_unified_rich_text_renderer(self) -> None:
        rich_text_source = (SRC_DIR / "renderers" / "richText.ts").read_text(encoding="utf-8")
        tabs_source = (SRC_DIR / "components" / "ProblemInfoTabs.vue").read_text(encoding="utf-8")

        for marker in ("renderRichText", "rich-text-paragraph", "rich-text-code-block", "rich-text-inline-code", "rich-text-list", "rich-text-ordered-list", "rich-text-heading", "rich-text-formula"):
            self.assertIn(marker, rich_text_source)
        self.assertIn("renderRichText", tabs_source)
        self.assertNotIn(".replace(/\\n/g, '<br>')", tabs_source)

    def test_status_panel_renders_failure_summary_input_expected_actual_error(self) -> None:
        status_source = (SRC_DIR / "components" / "StatusPanel.vue").read_text(encoding="utf-8")

        for field in ("testCase.input", "testCase.expected", "testCase.actual", "testCase.error", "testCase.stdout", "testCase.stderr", "testCase.traceback"):
            self.assertIn(field, status_source)
        self.assertIn("DisplayValueView", status_source)
        self.assertIn("testCase.actualDisplay", status_source)
        self.assertIn("!hasStructuredRunCases", status_source)

    def test_status_panel_renders_dual_score_summary_for_submit_results(self) -> None:
        status_source = (SRC_DIR / "components" / "StatusPanel.vue").read_text(encoding="utf-8")
        style_source = (SRC_DIR / "style.css").read_text(encoding="utf-8")

        for marker in ("score-summary", "rawScoreText", "rawScorePercentText", "learningLevelLabel", "recommendationLabel"):
            self.assertIn(marker, status_source)
        self.assertIn("latestRecord.action === 'submit' && latestRecord.raw_score", status_source)
        self.assertIn("latestRecord.learning_score?.rationale", status_source)
        self.assertIn("latestRecord.review_recommendation.message", status_source)
        for marker in (".score-summary", ".score-card", ".learning-score-card.medium_low", ".review-recommendation-card"):
            self.assertIn(marker, style_source)

    def test_dataset_description_and_display_value_contract_are_wired(self) -> None:
        types_source = (SRC_DIR / "types.ts").read_text(encoding="utf-8")
        store_source = (SRC_DIR / "store" / "runtimeStore.ts").read_text(encoding="utf-8")
        tabs_source = (SRC_DIR / "components" / "ProblemInfoTabs.vue").read_text(encoding="utf-8")
        dataset_component = SRC_DIR / "components" / "DatasetDescriptionSection.vue"
        display_component = SRC_DIR / "components" / "DisplayValueView.vue"

        self.assertTrue(dataset_component.exists())
        self.assertTrue(display_component.exists())
        for marker in ("DatasetDescription", "DatasetTableDescription", "DatasetRelationshipDescription", "dataset_description", "datasetDescription", "RuntimeExampleDisplay", "example_displays", "exampleDisplays"):
            self.assertIn(marker, types_source + store_source)
        self.assertIn("DatasetDescriptionSection", tabs_source)
        self.assertIn("ExampleDisplaySection", tabs_source)
        self.assertIn("displayFallback", store_source)
        self.assertIn("hasStructuredCases", store_source)
        self.assertNotIn("'kind' in value && 'repr' in value", store_source)

    def test_difficulty_badge_uses_four_level_contract(self) -> None:
        types_source = (SRC_DIR / "types.ts").read_text(encoding="utf-8")
        store_source = (SRC_DIR / "store" / "runtimeStore.ts").read_text(encoding="utf-8")
        sidebar_source = (SRC_DIR / "components" / "Sidebar.vue").read_text(encoding="utf-8")
        tabs_source = (SRC_DIR / "components" / "ProblemInfoTabs.vue").read_text(encoding="utf-8")
        style_source = (SRC_DIR / "style.css").read_text(encoding="utf-8")

        for marker in ("basic", "medium", "upper_medium", "hard"):
            self.assertIn(marker, types_source)
            self.assertIn(marker, store_source)
            self.assertIn(f".difficulty-badge.{marker}", style_source)
        self.assertIn("difficultyLevel", types_source)
        self.assertIn("difficulty_summary", store_source)
        self.assertIn("difficulty-badge", sidebar_source)
        self.assertIn("difficulty-badge", tabs_source)


if __name__ == "__main__":
    unittest.main()
