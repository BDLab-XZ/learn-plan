"""
Question bank stubs.

Hardcoded question banks have been removed. All questions must be generated
by LLM sub-agents (one to author, one to review) and injected via
--question-artifact-json and --question-review-json.

The utility helpers (make_code_question, make_python_metadata, etc.) remain
as dict constructors for use by the artifact normalization pipeline.
"""

from __future__ import annotations

from typing import Any

from learn_core.text_utils import normalize_string_list


# ---------------------------------------------------------------------------
# Dict constructors (utilities kept for artifact normalization)
# ---------------------------------------------------------------------------

def make_python_metadata(
    qid: str,
    difficulty: str,
    title: str,
    func_name: str,
    args: list[str],
    *,
    constraints: dict[str, Any] | None = None,
    hidden_tests: list[dict[str, Any]] | None = None,
    preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": qid,
        "difficulty": difficulty,
        "title": title,
        "func_name": func_name,
        "args": args,
        "constraints": constraints or {},
        "hidden_tests": hidden_tests or [],
        "preflight": preflight or {},
    }


def make_code_question(
    qid: str,
    difficulty: str,
    title: str,
    func_name: str,
    args: list[str],
    *,
    constraints: dict[str, Any] | None = None,
    hidden_tests: list[dict[str, Any]] | None = None,
    preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": qid,
        "category": "code",
        "type": "code",
        "question": title,
        "difficulty": difficulty,
        "language": "python",
        "metadata": make_python_metadata(qid, difficulty, title, func_name, args, constraints=constraints, hidden_tests=hidden_tests, preflight=preflight),
    }


def make_written_question(
    qid: str,
    difficulty: str,
    title: str,
    *,
    reference_material: str = "",
    rubric_hints: list[str] | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": qid,
        "category": "written",
        "type": "written",
        "question": title,
        "difficulty": difficulty,
    }
    if reference_material:
        item["reference_material"] = reference_material
    if rubric_hints:
        item["rubric_hints"] = list(rubric_hints)
    return item


# ---------------------------------------------------------------------------
# Stub bank builders (return empty — no hardcoded questions)
# ---------------------------------------------------------------------------

def _empty_bank() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return [], []


def build_algorithm_bank() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _empty_bank()


def build_math_bank() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _empty_bank()


def build_english_bank() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _empty_bank()


def build_linux_bank() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _empty_bank()


def build_llm_app_bank() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _empty_bank()


def build_general_cs_bank() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _empty_bank()


def build_python_bank() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _empty_bank()


def build_git_bank() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _empty_bank()


def build_question_bank(domain: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _empty_bank()


def domain_supports_code_questions(domain: str) -> bool:
    return domain in {"python", "algorithm", "math", "linux", "git"}


# ---------------------------------------------------------------------------
# Stub selection / seed functions (return empty)
# ---------------------------------------------------------------------------

def collect_focus_terms(plan_source: dict[str, Any]) -> list[str]:
    return []


def extract_difficulty_targets(plan_source: dict[str, Any], category: str) -> list[str]:
    return []


def resolve_target_stages(plan_source: dict[str, Any]) -> list[str]:
    return []


def resolve_target_clusters(plan_source: dict[str, Any]) -> list[str]:
    return []


def score_question(item: dict[str, Any], focus_terms: list[str]) -> int:
    return 0


def filter_python_questions_by_constraints(
    items: list[dict[str, Any]], plan_source: dict[str, Any]
) -> list[dict[str, Any]]:
    return []


def combine_priority_pools(*pools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for pool in pools:
        result.extend(pool)
    return result


def build_python_priority_pool(
    concept: list[dict[str, Any]], code: list[dict[str, Any]], plan_source: dict[str, Any]
) -> dict[str, Any]:
    return {"priority_items": [], "python_selection_context": {}, "fallback_items": []}


def allocate_python_question_mix(
    priority_pool: dict[str, Any], plan_source: dict[str, Any]
) -> dict[str, Any]:
    return {"concept": 0, "code": 0, "open": 0}


def resolve_preference_quota(plan_source: dict[str, Any], *, category: str) -> list[tuple[str, int]]:
    return []


def build_python_question_generation_seed(
    bank_concept: list[dict[str, Any]], bank_code: list[dict[str, Any]], plan_source: dict[str, Any]
) -> dict[str, Any]:
    return {
        "seed_questions": [],
        "question_mix": {"concept": 0, "code": 0, "open": 0},
        "seed_constraints": {},
        "selection_context": {"selection_policy": "external-artifact-required"},
    }


def select_python_questions(
    concept: list[dict[str, Any]], code: list[dict[str, Any]], plan_source: dict[str, Any]
) -> list[dict[str, Any]]:
    return []


def is_initial_diagnostic_plan_source(plan_source: dict[str, Any]) -> bool:
    return False


def diagnostic_repair_actions(repair_plan: dict[str, Any] | None) -> list[dict[str, Any]]:
    return []


def diagnostic_required_primary_categories(plan_source: dict[str, Any], repair_plan: dict[str, Any] | None) -> list[str]:
    return []


def enrich_diagnostic_anchor(
    anchor: dict[str, Any] | None, plan_source: dict[str, Any]
) -> dict[str, Any] | None:
    return anchor


def choose_diagnostic_bank_candidates(
    concept: list[dict[str, Any]], code: list[dict[str, Any]], plan_source: dict[str, Any]
) -> list[dict[str, Any]]:
    return []


def build_python_diagnostic_written_anchor(
    plan_source: dict[str, Any]
) -> dict[str, Any] | None:
    return None


def select_python_diagnostic_questions(
    concept: list[dict[str, Any]], code: list[dict[str, Any]], plan_source: dict[str, Any]
) -> list[dict[str, Any]]:
    return []
