from __future__ import annotations

from pathlib import Path
from typing import Any

from learn_core.io import read_json_if_exists
from learn_core.text_utils import normalize_string_list


def _append_unique(target: list[str], values: Any) -> None:
    for value in normalize_string_list(values):
        if value not in target:
            target.append(value)


def build_progress_history_aggregates(states: list[dict[str, Any]]) -> dict[str, Any]:
    covered: list[str] = []
    weakness_focus: list[str] = []
    review_debt: list[str] = []
    deferred_enhancement: list[str] = []
    selected_segments: list[Any] = []
    aggregated_from: list[str] = []
    latest_anchor = ""
    for state in states:
        progress_path = str(state.get("progress_path") or "")
        if progress_path:
            aggregated_from.append(progress_path)
            latest_anchor = latest_anchor or progress_path
        context = state.get("context") if isinstance(state.get("context"), dict) else {}
        snapshot = context.get("plan_source_snapshot") if isinstance(context.get("plan_source_snapshot"), dict) else {}
        learning_state = state.get("learning_state") if isinstance(state.get("learning_state"), dict) else {}
        progression = state.get("progression") if isinstance(state.get("progression"), dict) else {}
        _append_unique(covered, progression.get("mastered_clusters"))
        _append_unique(covered, context.get("covered") or snapshot.get("covered"))
        _append_unique(covered, context.get("topic_cluster") or snapshot.get("today_topic"))
        _append_unique(covered, context.get("current_stage") or snapshot.get("current_stage"))
        _append_unique(weakness_focus, learning_state.get("weaknesses"))
        _append_unique(weakness_focus, learning_state.get("high_freq_errors"))
        _append_unique(weakness_focus, learning_state.get("review_focus"))
        _append_unique(weakness_focus, progression.get("review_debt"))
        _append_unique(review_debt, progression.get("review_debt"))
        _append_unique(review_debt, context.get("review_targets") or snapshot.get("review_targets"))
        _append_unique(deferred_enhancement, progression.get("deferred_clusters"))
        for item in context.get("selected_segments") or snapshot.get("selected_segments") or []:
            if item not in selected_segments:
                selected_segments.append(item)
    return {
        "history_count": len(states),
        "aggregated_from": aggregated_from,
        "latest_anchor": latest_anchor,
        "covered": covered,
        "weakness_focus": weakness_focus or review_debt,
        "review_debt": review_debt,
        "deferred_enhancement": deferred_enhancement,
        "selected_segments": selected_segments,
    }


def resolve_structured_state_lookup(plan_path: Path, topic: str) -> dict[str, Any]:
    sessions_dir = plan_path.parent / "sessions"
    if not sessions_dir.exists() or not sessions_dir.is_dir():
        return {
            "status": "no_sessions_dir",
            "reason": "path-missing-or-uninitialized",
            "sessions_dir": str(sessions_dir),
            "topic": topic,
            "progress_state": None,
        }

    candidates: list[tuple[float, int, dict[str, Any]]] = []
    session_count = 0
    topic_match_count = 0
    structured_progress_count = 0
    eligible_count = 0
    for progress_path in sessions_dir.glob("*/progress.json"):
        session_count += 1
        progress = read_json_if_exists(progress_path)
        if not progress:
            continue
        if str(progress.get("topic") or "").strip() != topic:
            continue
        topic_match_count += 1
        session = progress.get("session") or {}
        context = progress.get("context") if isinstance(progress.get("context"), dict) else {}
        learning_state = progress.get("learning_state") if isinstance(progress.get("learning_state"), dict) else {}
        progression = progress.get("progression") if isinstance(progress.get("progression"), dict) else {}
        if not context and not learning_state and not progression:
            continue
        structured_progress_count += 1
        status = str(session.get("status") or "")
        if status not in {"finished", "active"}:
            continue
        if status == "active" and not (learning_state or progression):
            continue
        eligible_count += 1
        current_stage = str(context.get("current_stage") or "").strip()
        current_day = str(context.get("current_day") or "").strip()
        topic_cluster = str(context.get("topic_cluster") or "").strip()
        anchor_score = 1 if (current_stage and (current_day or topic_cluster)) else 0
        status_score = 2 if status == "active" else 1
        try:
            sort_ts = progress_path.stat().st_mtime
        except OSError:
            continue
        candidates.append(
            (
                sort_ts,
                anchor_score * 10 + status_score,
                {
                    "progress_path": str(progress_path),
                    "session": session,
                    "context": context,
                    "learning_state": learning_state,
                    "progression": progression,
                    "material_alignment": progress.get("material_alignment") if isinstance(progress.get("material_alignment"), dict) else {},
                },
            )
        )

    if candidates:
        candidates.sort(key=lambda item: (item[1], item[0]), reverse=True)
        latest_progress_state = candidates[0][2]
        chronological_states = [item[2] for item in sorted(candidates, key=lambda item: item[0])]
        return {
            "status": "found",
            "reason": "ok",
            "sessions_dir": str(sessions_dir),
            "topic": topic,
            "progress_state": latest_progress_state,
            "progress_states": chronological_states,
            "aggregates": build_progress_history_aggregates(chronological_states),
            "session_count": session_count,
            "topic_match_count": topic_match_count,
            "structured_progress_count": structured_progress_count,
            "eligible_count": eligible_count,
        }
    if topic_match_count == 0:
        status = "no_topic_match"
        reason = "topic-mismatch-or-wrong-path"
    elif structured_progress_count == 0:
        status = "no_structured_progress"
        reason = "no-learning-history"
    else:
        status = "no_eligible_session"
        reason = "history-not-ready-for-test"
    return {
        "status": status,
        "reason": reason,
        "sessions_dir": str(sessions_dir),
        "topic": topic,
        "progress_state": None,
        "session_count": session_count,
        "topic_match_count": topic_match_count,
        "structured_progress_count": structured_progress_count,
        "eligible_count": eligible_count,
    }


def load_latest_structured_state(plan_path: Path, topic: str) -> dict[str, Any] | None:
    lookup = resolve_structured_state_lookup(plan_path, topic)
    progress_state = lookup.get("progress_state") if isinstance(lookup, dict) else None
    return progress_state if isinstance(progress_state, dict) else None
