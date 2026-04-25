from __future__ import annotations

from typing import Any

from .lesson_builder import normalize_lesson_case_courseware, render_daily_lesson_plan_markdown
from learn_core.text_utils import normalize_string_list


def _source_lines(text: str) -> list[str]:
    lines = str(text or "").splitlines()
    return [f"{line}\n" for line in lines] if lines else []


def _markdown_cell(source: str) -> dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": _source_lines(source),
    }


def _code_cell(source: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _source_lines(source),
    }


def _collect_code_examples(plan: dict[str, Any]) -> list[str]:
    case_courseware = normalize_lesson_case_courseware(plan.get("case_courseware"), plan)
    examples: list[str] = []
    for step in case_courseware.get("guided_story_practice") or []:
        if not isinstance(step, dict):
            continue
        for key in ("code_example", "example_code", "demo_code"):
            value = str(step.get(key) or "").strip()
            if value and value not in examples:
                examples.append(value)
    if not examples:
        focus_terms = " ".join(normalize_string_list(plan.get("lesson_focus_points") or []))
        if any(token in focus_terms.lower() for token in ("return", "none", "print")):
            examples.append("def add(a, b):\n    return a + b\n\nassert add(1, 2) == 3")
    return examples[:4]


def render_daily_lesson_notebook(plan: dict[str, Any]) -> dict[str, Any]:
    markdown = render_daily_lesson_plan_markdown(plan)
    cells: list[dict[str, Any]] = []
    current_heading = ""
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_heading, current_lines
        if current_lines:
            cells.append(_markdown_cell("\n".join(current_lines).strip()))
        current_heading = ""
        current_lines = []

    for raw_line in markdown.splitlines():
        if raw_line.startswith("## "):
            flush()
            current_heading = raw_line
            current_lines = [raw_line]
        elif raw_line.startswith("# "):
            flush()
            current_heading = raw_line
            current_lines = [raw_line]
        else:
            if not current_lines:
                current_lines = [current_heading] if current_heading else []
            current_lines.append(raw_line)
    flush()

    code_examples = _collect_code_examples(plan)
    if code_examples:
        cells.append(_markdown_cell("## 代码示例\n\n下面的代码只用于讲解今天的关键概念，不是正式练习题答案。"))
        for example in code_examples:
            cells.append(_code_cell(example))

    if not cells:
        cells.append(_markdown_cell("# 当日学习课件\n\n暂无可生成的教学内容。"))

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "pygments_lexer": "ipython3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
