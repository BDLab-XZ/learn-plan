from __future__ import annotations

from pathlib import Path
from typing import Any

from learn_core.io import read_text_if_exists, write_text
from learn_core.markdown_sections import upsert_markdown_section
from learn_core.text_utils import normalize_string_list


LOW_RISK_FEEDBACK_LABELS = {
    "difficulty": "难度微调",
    "teaching_style": "讲解方式微调",
    "pace": "节奏微调",
    "question_design": "题型微调",
    "material_fit": "材料贴合微调",
}


def append_plan_record(plan_path: Path, heading: str, block: str) -> None:
    original = read_text_if_exists(plan_path)
    updated = upsert_markdown_section(original, heading, block)
    write_text(plan_path, updated)


def build_micro_adjustment_lines(summary: dict[str, Any]) -> list[str]:
    feedback = summary.get("user_feedback") if isinstance(summary.get("user_feedback"), dict) else {}
    lines: list[str] = []
    for key, label in LOW_RISK_FEEDBACK_LABELS.items():
        value = str(feedback.get(key) or "").strip()
        if value:
            lines.append(f"- {label}：{value}")
    for comment in normalize_string_list(feedback.get("comments")):
        lines.append(f"- 本次反馈：{comment}")
    if not lines:
        return []
    return [
        f"### {summary.get('date') or 'unknown-date'} / {summary.get('topic') or '未命名主题'}",
        *lines,
        "- 适用范围：后续 /learn-today 与 /learn-test 默认采用；结构性路线变化仍走课程调整审批。",
    ]


def append_micro_adjustments(plan_path: Path, summary: dict[str, Any]) -> bool:
    lines = build_micro_adjustment_lines(summary)
    if not lines:
        return False
    append_plan_record(plan_path, "当前教学/练习微调", "\n".join(lines))
    return True


def render_feedback_output_lines(*, learner_model_result: dict[str, Any], patch_result: dict[str, Any]) -> list[str]:
    lines = [f"learner model：{learner_model_result.get('path')}"]
    patch = patch_result.get("patch")
    if patch:
        lines.append(f"curriculum patch：{patch_result.get('path')}（{patch.get('status')} / {patch.get('patch_type')}）")
    else:
        lines.append(f"curriculum patch：{patch_result.get('path')}（本次无需新增 patch）")
    return lines


__all__ = [
    "append_micro_adjustments",
    "append_plan_record",
    "build_micro_adjustment_lines",
    "render_feedback_output_lines",
]
