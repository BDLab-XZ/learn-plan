from __future__ import annotations

from typing import Any

INDEX_SCHEMA_VERSION = "learn-plan.materials.v1"

CACHE_FIELDS = frozenset(
    {
        "cache_status",
        "cached_at",
        "last_attempt",
        "local_path",
    }
)

PLANNING_FIELDS = frozenset(
    {
        "availability",
        "capability_alignment",
        "coverage",
        "discovery_notes",
        "goal_alignment",
        "mastery_checks",
        "reading_segments",
        "role_in_plan",
        "selection_status",
        "usage_modes",
    }
)


def get_index_entries(index_data: dict[str, Any]) -> list[dict[str, Any]]:
    entries = index_data.get("entries") or index_data.get("items") or index_data.get("materials") or []
    if not isinstance(entries, list):
        return []
    return [item for item in entries if isinstance(item, dict)]


def normalize_materials_index(index_data: dict[str, Any] | None, *, entries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    normalized = dict(index_data or {})
    normalized_entries = entries if entries is not None else get_index_entries(normalized)
    cleaned_entries: list[dict[str, Any]] = []
    for item in normalized_entries:
        if not isinstance(item, dict):
            continue
        cleaned = dict(item)
        for legacy_field in ("cache_note", "exists_locally", "local_artifact", "downloaded_at"):
            cleaned.pop(legacy_field, None)
        cleaned_entries.append(cleaned)
    normalized["material_schema_version"] = normalized.get("material_schema_version") or INDEX_SCHEMA_VERSION
    normalized["entries"] = cleaned_entries
    normalized["items"] = cleaned_entries
    normalized["materials"] = cleaned_entries
    return normalized
