"""lesson-html.json 内容校验。

校验 Agent 产出的 long-output-html JSON 是否覆盖 /learn-today 的三段教学框架。
"""

from __future__ import annotations

import re
from typing import Any


REQUIRED_FRAMEWORK_TITLES = ["往期复习", "本期知识点讲解", "本期内容回看"]
MIN_TOTAL_CONTENT_CHARS = 600
SOURCE_REFERENCE_PATTERN = re.compile(
    r"(材料|资料|来源|引用|参考|locator|segment|章节|章|节|页|page|paragraph|段落|section|key_quote|原文|摘录|文档|教程|官方)",
    re.IGNORECASE,
)
PRECISE_REFERENCE_PATTERN = re.compile(
    r"(PDF\s*第\s*\d+\s*页|第\s*\d+\s*[章节页段]|P\.?\s*\d+|p\.?\s*\d+|page\s*\d+|paragraph\s*\d+|段落\s*\d+|section\s*[\w.\-]+|locator|segment)",
    re.IGNORECASE,
)
EXCERPT_PATTERN = re.compile(r"(原文摘录|key_quote|摘录|读到|原文)", re.IGNORECASE)


def _section_text(section: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("title", "lead", "intro", "content"):
        value = section.get(key)
        if value:
            parts.append(str(value))
    for key in ("items", "notes"):
        value = section.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    parts.extend(str(v) for v in item.values() if v)
                elif item:
                    parts.append(str(item))
    return "\n".join(parts)


def _all_text(data: dict[str, Any], sections: list[dict[str, Any]]) -> str:
    parts = [str(data.get("title") or ""), str(data.get("subtitle") or "")]
    summary = data.get("summary")
    if isinstance(summary, list):
        parts.extend(str(item) for item in summary if item)
    parts.extend(_section_text(section) for section in sections)
    appendix = data.get("appendix")
    if isinstance(appendix, list):
        parts.extend(str(item) for item in appendix if item)
    return "\n".join(parts)


def _has_required_part(text: str, title: str) -> bool:
    return title in text or title.replace("本期", "今日") in text


def validate_lesson_html_json(data: dict[str, Any]) -> dict[str, Any]:
    """校验 lesson-html.json 的结构和内容质量。

    Returns: {"valid": bool, "issues": [...], "warnings": [...]}
    """
    issues: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return {"valid": False, "issues": ["lesson-html.json 不是 JSON object"], "warnings": []}

    sections_raw = data.get("sections")
    if not isinstance(sections_raw, list) or not sections_raw:
        return {"valid": False, "issues": ["lesson-html.json 缺少 sections 数组"], "warnings": warnings}

    sections = [section for section in sections_raw if isinstance(section, dict)]
    if not sections:
        return {"valid": False, "issues": ["lesson-html.json sections 中没有有效 section object"], "warnings": warnings}

    full_text = _all_text(data, sections)
    compact_text = re.sub(r"\s+", "", full_text)
    if len(compact_text) < MIN_TOTAL_CONTENT_CHARS:
        warnings.append(f"lesson-html.json 总内容偏短（{len(compact_text)} 字），请确认课件不是空壳。")

    for title in REQUIRED_FRAMEWORK_TITLES:
        if not _has_required_part(full_text, title):
            issues.append(f"缺少三段教学框架：{title}")

    review_sections = [section for section in sections if "回看" in _section_text(section) or "参考" in _section_text(section)]
    reference_text = "\n".join(_section_text(section) for section in review_sections) or full_text
    if not SOURCE_REFERENCE_PATTERN.search(reference_text):
        issues.append("缺少来源 grounding：本期内容回看必须包含材料、资料、章节、页码、段落或 locator 等引用信息。")
    if not PRECISE_REFERENCE_PATTERN.search(reference_text):
        issues.append("来源引用不够精确：本期内容回看必须细化到 PDF 页码、章节、段落、section 或 locator；不能只写材料索引里的粗范围。")
    if not EXCERPT_PATTERN.search(reference_text):
        issues.append("缺少原文短摘录：本期内容回看必须包含 key_quote / 原文摘录 / 摘录，以证明实际读取过材料。")

    valid = len(issues) == 0
    return {"valid": valid, "issues": issues, "warnings": warnings}


__all__ = ["validate_lesson_html_json", "REQUIRED_FRAMEWORK_TITLES", "MIN_TOTAL_CONTENT_CHARS", "PRECISE_REFERENCE_PATTERN", "EXCERPT_PATTERN"]
