from __future__ import annotations

import json
from typing import Any


JSON_DECODER = json.JSONDecoder()


def _strip_code_fence(text: str) -> str:
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _decode_first_json_value(text: str) -> Any | None:
    for token in ("{", "["):
        start = text.find(token)
        while start != -1:
            try:
                value, _ = JSON_DECODER.raw_decode(text[start:])
                return value
            except json.JSONDecodeError:
                start = text.find(token, start + 1)
    return None


def parse_json_from_llm_output(raw_text: str) -> Any | None:
    text = _strip_code_fence(str(raw_text or "").strip())
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    first_value = _decode_first_json_value(text)
    if first_value is not None:
        return first_value
    object_start = text.find("{")
    object_end = text.rfind("}")
    if 0 <= object_start < object_end:
        try:
            return json.loads(text[object_start: object_end + 1])
        except json.JSONDecodeError:
            pass
    array_start = text.find("[")
    array_end = text.rfind("]")
    if 0 <= array_start < array_end:
        try:
            return json.loads(text[array_start: array_end + 1])
        except json.JSONDecodeError:
            return None
    return None
