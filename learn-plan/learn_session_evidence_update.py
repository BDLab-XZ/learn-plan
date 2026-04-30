#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from learn_core.io import read_json_if_exists, write_json


INTERACTION_EVENTS_FILE = "interaction_events.jsonl"
REFLECTION_FILE = "reflection.json"
PROGRESS_FILE = "progress.json"


class EvidenceValidationError(ValueError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update a learn-plan session with agent-side learning evidence")
    parser.add_argument("--session-dir", required=True, help="session 目录，需包含或即将包含 progress.json")
    parser.add_argument("--event-json", action="append", default=[], help="单条 interaction event JSON 文件路径，可重复")
    parser.add_argument("--event-jsonl", action="append", default=[], help="interaction event JSONL 文件路径，可重复")
    parser.add_argument("--reflection-json", help="post-session reflection JSON 文件路径")
    parser.add_argument("--completion-signal-json", help="completion signal JSON 文件路径")
    parser.add_argument("--payload-json", help="包含 event/events/reflection/completion_signal/pre_session_review 等字段的 JSON 文件路径")
    parser.add_argument("--stdin-json", action="store_true", help="从 stdin 读取 payload JSON")
    parser.add_argument("--stdout-json", action="store_true", help="输出更新摘要 JSON")
    return parser.parse_args()


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def load_json_path(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise EvidenceValidationError(f"JSON payload must be an object: {path}")
    return payload


def load_jsonl_path(path: str | Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise EvidenceValidationError(f"JSONL line must be an object: {path}:{line_number}")
            events.append(payload)
    return events


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_event(event: dict[str, Any]) -> dict[str, Any]:
    user_event = event.get("user_event") if isinstance(event.get("user_event"), dict) else {}
    if not non_empty_text(event.get("source")):
        raise EvidenceValidationError("interaction event requires source")
    if not non_empty_text(event.get("phase")):
        raise EvidenceValidationError("interaction event requires phase")
    if not non_empty_text(user_event.get("summary")):
        raise EvidenceValidationError("interaction event requires user_event.summary")
    if not isinstance(event.get("diagnostic_signal"), dict) and not isinstance(event.get("follow_up_result"), dict):
        raise EvidenceValidationError("interaction event requires diagnostic_signal or follow_up_result")
    normalized = json.loads(json.dumps(event, ensure_ascii=False))
    normalized.setdefault("timestamp", now_iso())
    normalized.setdefault("source", "main_agent_interaction")
    return normalized


def validate_completion_signal(signal: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(signal, ensure_ascii=False))
    normalized.setdefault("status", "received")
    normalized.setdefault("source", "main_agent")
    normalized.setdefault("received_at", now_iso())
    if not non_empty_text(normalized.get("status")):
        raise EvidenceValidationError("completion_signal requires status")
    if normalized.get("status") in {"received", "completed"} and not non_empty_text(normalized.get("user_message_summary")):
        raise EvidenceValidationError("received completion_signal requires user_message_summary")
    return normalized


def validate_reflection(reflection: dict[str, Any]) -> dict[str, Any]:
    if not non_empty_text(reflection.get("status")):
        raise EvidenceValidationError("reflection requires status")
    if not isinstance(reflection.get("trigger"), dict):
        raise EvidenceValidationError("reflection requires trigger")
    if not isinstance(reflection.get("rounds"), list):
        raise EvidenceValidationError("reflection requires rounds")
    if not isinstance(reflection.get("mastery_judgement"), dict):
        raise EvidenceValidationError("reflection requires mastery_judgement")
    return json.loads(json.dumps(reflection, ensure_ascii=False))


def event_summary(event: dict[str, Any]) -> dict[str, Any]:
    user_event = event.get("user_event") if isinstance(event.get("user_event"), dict) else {}
    diagnostic = event.get("diagnostic_signal") if isinstance(event.get("diagnostic_signal"), dict) else {}
    follow_up = event.get("follow_up_result") if isinstance(event.get("follow_up_result"), dict) else {}
    related_material = event.get("related_material") if isinstance(event.get("related_material"), dict) else {}
    return {
        "timestamp": event.get("timestamp"),
        "phase": event.get("phase"),
        "type": user_event.get("type"),
        "summary": user_event.get("summary"),
        "knowledge_points": as_list(event.get("knowledge_points")),
        "confusion_type": diagnostic.get("confusion_type"),
        "severity": diagnostic.get("severity"),
        "follow_up_status": follow_up.get("status"),
        "prompting_level": follow_up.get("prompting_level"),
        "recommended_action": event.get("recommended_action"),
        "material_title": related_material.get("title"),
        "material_locator": related_material.get("locator"),
    }


def merge_unique_dicts(existing: Any, additions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in as_list(existing) + additions:
        if not isinstance(item, dict):
            continue
        key = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def merge_user_feedback(base: Any, addition: Any) -> dict[str, Any]:
    result = base if isinstance(base, dict) else {}
    result = json.loads(json.dumps(result, ensure_ascii=False))
    if not isinstance(addition, dict):
        return result
    for key in ("difficulty", "teaching_style", "pace", "question_design", "material_fit", "scope"):
        value = addition.get(key)
        if value not in (None, "", []):
            result[key] = value
    comments = []
    for value in as_list(result.get("comments")) + as_list(addition.get("comments")):
        if isinstance(value, str):
            text = value.strip()
            if text and text not in comments:
                comments.append(text)
        elif isinstance(value, dict) and value not in comments:
            comments.append(value)
    result["comments"] = comments
    result.setdefault("scope", "session")
    return result


def update_progress(
    progress: dict[str, Any],
    *,
    session_dir: Path,
    events: list[dict[str, Any]],
    reflection: dict[str, Any] | None,
    completion_signal: dict[str, Any] | None,
    pre_session_review: dict[str, Any] | None,
    user_feedback: dict[str, Any] | None,
    mastery_judgement: dict[str, Any] | None,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(progress if isinstance(progress, dict) else {}, ensure_ascii=False))
    if pre_session_review is not None:
        updated["pre_session_review"] = pre_session_review
    if events:
        summaries = [event_summary(event) for event in events]
        updated["interaction_evidence"] = merge_unique_dicts(updated.get("interaction_evidence"), summaries)
    if completion_signal is not None:
        updated["completion_signal"] = completion_signal
    if reflection is not None:
        reflection_summary = reflection.get("summary")
        if not reflection_summary:
            judgement = reflection.get("mastery_judgement") if isinstance(reflection.get("mastery_judgement"), dict) else {}
            evidence = judgement.get("evidence") if isinstance(judgement.get("evidence"), list) else []
            reflection_summary = "；".join(str(item).strip() for item in evidence if str(item).strip()) or reflection.get("status")
        updated["reflection"] = reflection_summary
        updated["mastery_judgement"] = reflection.get("mastery_judgement") or updated.get("mastery_judgement")
        mastery_checks = updated.get("mastery_checks") if isinstance(updated.get("mastery_checks"), dict) else {}
        reflection_checks = mastery_checks.get("reflection") if isinstance(mastery_checks.get("reflection"), list) else []
        if reflection_summary and reflection_summary not in reflection_checks:
            reflection_checks = reflection_checks + [reflection_summary]
        mastery_checks["reflection"] = reflection_checks
        updated["mastery_checks"] = mastery_checks
        if isinstance(reflection.get("user_feedback"), dict):
            updated["user_feedback"] = merge_user_feedback(updated.get("user_feedback"), reflection.get("user_feedback"))
    if mastery_judgement is not None:
        updated["mastery_judgement"] = mastery_judgement
    if user_feedback is not None:
        updated["user_feedback"] = merge_user_feedback(updated.get("user_feedback"), user_feedback)

    history = updated.get("update_history") if isinstance(updated.get("update_history"), list) else []
    history.append(
        {
            "update_type": "agent-evidence",
            "updated_at": now_iso(),
            "summary": {
                "event_count": len(events),
                "reflection_status": reflection.get("status") if isinstance(reflection, dict) else None,
                "completion_signal_status": completion_signal.get("status") if isinstance(completion_signal, dict) else None,
                "session_dir": str(session_dir),
            },
        }
    )
    updated["update_history"] = history[-20:]
    return updated


def append_events(session_dir: Path, events: list[dict[str, Any]]) -> None:
    if not events:
        return
    path = session_dir / INTERACTION_EVENTS_FILE
    session_dir.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def collect_payloads(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if args.payload_json:
        payload.update(load_json_path(args.payload_json))
    if args.stdin_json:
        stdin_text = sys.stdin.read().strip()
        if stdin_text:
            stdin_payload = json.loads(stdin_text)
            if not isinstance(stdin_payload, dict):
                raise EvidenceValidationError("stdin payload must be an object")
            payload.update(stdin_payload)
    events: list[dict[str, Any]] = []
    for path in args.event_json:
        events.append(load_json_path(path))
    for path in args.event_jsonl:
        events.extend(load_jsonl_path(path))
    events.extend(item for item in as_list(payload.get("event")) if isinstance(item, dict))
    events.extend(item for item in as_list(payload.get("events")) if isinstance(item, dict))
    reflection = load_json_path(args.reflection_json) if args.reflection_json else payload.get("reflection")
    completion_signal = load_json_path(args.completion_signal_json) if args.completion_signal_json else payload.get("completion_signal")
    return {
        "events": events,
        "reflection": reflection if isinstance(reflection, dict) else None,
        "completion_signal": completion_signal if isinstance(completion_signal, dict) else None,
        "pre_session_review": payload.get("pre_session_review") if isinstance(payload.get("pre_session_review"), dict) else None,
        "user_feedback": payload.get("user_feedback") if isinstance(payload.get("user_feedback"), dict) else None,
        "mastery_judgement": payload.get("mastery_judgement") if isinstance(payload.get("mastery_judgement"), dict) else None,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    session_dir = Path(args.session_dir).expanduser().resolve()
    payloads = collect_payloads(args)
    events = [validate_event(event) for event in payloads["events"]]
    reflection = validate_reflection(payloads["reflection"]) if payloads["reflection"] else None
    completion_signal = validate_completion_signal(payloads["completion_signal"]) if payloads["completion_signal"] else None

    append_events(session_dir, events)
    if reflection is not None:
        write_json(session_dir / REFLECTION_FILE, reflection)

    progress_path = session_dir / PROGRESS_FILE
    progress = read_json_if_exists(progress_path)
    updated_progress = update_progress(
        progress,
        session_dir=session_dir,
        events=events,
        reflection=reflection,
        completion_signal=completion_signal,
        pre_session_review=payloads["pre_session_review"],
        user_feedback=payloads["user_feedback"],
        mastery_judgement=payloads["mastery_judgement"],
    )
    write_json(progress_path, updated_progress)
    return {
        "session_dir": str(session_dir),
        "event_count": len(events),
        "wrote_reflection": reflection is not None,
        "completion_signal_status": completion_signal.get("status") if isinstance(completion_signal, dict) else None,
        "progress_path": str(progress_path),
        "interaction_events_path": str(session_dir / INTERACTION_EVENTS_FILE),
        "reflection_path": str(session_dir / REFLECTION_FILE) if reflection is not None else None,
    }


def main() -> int:
    args = parse_args()
    try:
        result = run(args)
    except (EvidenceValidationError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"agent evidence update failed: {exc}", file=sys.stderr)
        return 1
    if args.stdout_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"updated agent evidence: {result['session_dir']}")
        print(f"events: {result['event_count']}")
        if result["completion_signal_status"]:
            print(f"completion_signal: {result['completion_signal_status']}")
        if result["wrote_reflection"]:
            print(f"reflection: {result['reflection_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
