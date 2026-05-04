from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from learn_core.io import read_json_if_exists, write_json
from learn_core.quality_review import apply_quality_envelope, build_traceability_entry
from learn_core.text_utils import normalize_string_list
from learn_workflow.contracts import CONTRACT_VERSION, default_workflow_paths
from learn_workflow.workflow_store import resolve_learning_root


PATCH_QUEUE_SCHEMA = "learn-plan.curriculum-patch-queue.v1"
PENDING_PATCH_STATUSES = {"proposed", "pending", "pending-evidence"}
APPROVED_PATCH_STATUSES = {"approved"}
CONSUMABLE_PATCH_STATUSES = PENDING_PATCH_STATUSES | APPROVED_PATCH_STATUSES
TERMINAL_PATCH_STATUSES = {"rejected", "applied"}
LOW_RISK_PATCH_TYPES = {"option_mapping_patch", "alias_patch", "tag_patch", "question_quality_issue"}
CONFIRMATION_REQUIRED_PATCH_TYPES = {"knowledge_node_patch", "prerequisite_edge_patch", "stage_order_patch", "target_scope_patch"}


def patch_risk_policy(patch_type: Any) -> dict[str, str]:
    normalized = str(patch_type or "").strip()
    if normalized in LOW_RISK_PATCH_TYPES:
        return {"risk_level": "low", "application_policy": "semi-automatic"}
    if normalized in CONFIRMATION_REQUIRED_PATCH_TYPES:
        return {"risk_level": "high", "application_policy": "pending-user-approval"}
    return {"risk_level": "medium", "application_policy": "pending-user-approval"}


def patch_status(value: Any) -> str:
    return str(value or "").strip()


def pending_patch_items(queue: dict[str, Any]) -> list[dict[str, Any]]:
    patches = [item for item in (queue.get("patches") or []) if isinstance(item, dict)]
    return [item for item in patches if patch_status(item.get("status")) in PENDING_PATCH_STATUSES]


def approved_patch_items(queue: dict[str, Any]) -> list[dict[str, Any]]:
    patches = [item for item in (queue.get("patches") or []) if isinstance(item, dict)]
    return [item for item in patches if patch_status(item.get("status")) in APPROVED_PATCH_STATUSES]


def apply_approval_patch_decisions(queue: dict[str, Any], approval_state: dict[str, Any] | None) -> tuple[dict[str, list[str]] | dict[str, Any], dict[str, list[str]]]:
    updated = deepcopy(queue) if isinstance(queue, dict) else default_patch_queue()
    normalized_approval = approval_state if isinstance(approval_state, dict) else {}
    approved_ids = set(normalize_string_list(normalized_approval.get("approved_patch_ids") or []))
    rejected_ids = set(normalize_string_list(normalized_approval.get("rejected_patch_ids") or []))
    patches = [item for item in (updated.get("patches") or []) if isinstance(item, dict)]
    if not approved_ids and not rejected_ids:
        legacy_approval_ready = (
            bool(normalized_approval.get("ready_for_execution"))
            and str(normalized_approval.get("approval_status") or normalized_approval.get("status") or "").strip().lower() == "approved"
            and not normalize_string_list(normalized_approval.get("pending_decisions") or [])
        )
        if legacy_approval_ready:
            approved_ids = {
                str(item.get("id") or "").strip()
                for item in patches
                if str(item.get("status") or "").strip() in PENDING_PATCH_STATUSES and str(item.get("id") or "").strip()
            }
        if not approved_ids:
            return _apply_patch_queue_envelope(updated), {"approved": [], "rejected": []}

    decisions = {"approved": [], "rejected": []}
    next_patches: list[dict[str, Any]] = []
    for item in patches:
        patch_id = str(item.get("id") or "").strip()
        status = patch_status(item.get("status"))
        next_status = status
        if patch_id and patch_id in approved_ids and status not in TERMINAL_PATCH_STATUSES:
            next_status = "approved"
        elif patch_id and patch_id in rejected_ids and status not in TERMINAL_PATCH_STATUSES:
            next_status = "rejected"
        if next_status == status:
            next_patches.append(item)
            continue

        evidence = normalize_string_list(list(item.get("evidence") or []) + [f"approval_patch_decision={patch_id}:{next_status}"])
        traceability = list(item.get("traceability") or [])
        traceability.append(
            build_traceability_entry(
                kind="approval",
                ref=patch_id or str(item.get("topic") or "patch"),
                title=item.get("topic") or "curriculum patch",
                detail=item.get("patch_type") or "feedback",
                stage="approval",
                status=next_status,
            )
        )
        decided_item = apply_quality_envelope(
            {
                **deepcopy(item),
                "status": next_status,
                "application_policy": "ready-to-apply" if next_status == "approved" else "rejected-by-approval",
            },
            stage="feedback",
            generator="approval-patch-decision",
            evidence=evidence,
            confidence=item.get("confidence"),
            quality_review=item.get("quality_review"),
            generation_trace={
                **(item.get("generation_trace") if isinstance(item.get("generation_trace"), dict) else {}),
                "stage": "approval",
                "generator": "approval-patch-decision",
                "status": next_status,
            },
            traceability=traceability,
        )
        next_patches.append(decided_item)
        decisions[next_status].append(patch_id)
    updated["patches"] = next_patches
    return _apply_patch_queue_envelope(updated), decisions


def consume_approved_patches(queue: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    updated = deepcopy(queue) if isinstance(queue, dict) else default_patch_queue()
    patches = [item for item in (updated.get("patches") or []) if isinstance(item, dict)]
    consumed: list[dict[str, Any]] = []
    next_patches: list[dict[str, Any]] = []
    for item in patches:
        status = patch_status(item.get("status"))
        if status in APPROVED_PATCH_STATUSES:
            applied = deepcopy(item)
            applied["status"] = "applied"
            consumed.append(applied)
            next_patches.append(applied)
        else:
            next_patches.append(item)
    updated["patches"] = next_patches
    return _apply_patch_queue_envelope(updated), consumed


def _sorted_patch_items(queue: dict[str, Any]) -> list[dict[str, Any]]:
    patches = [item for item in (queue.get("patches") or []) if isinstance(item, dict)]
    return sorted(
        patches,
        key=lambda item: (
            str(item.get("created_at") or ""),
            str(item.get("source_update_type") or ""),
            str(item.get("id") or ""),
        ),
    )


def _build_patch_queue_root_evidence(queue: dict[str, Any]) -> list[str]:
    patches = _sorted_patch_items(queue)
    latest_patch = patches[-1] if patches else {}
    evidence: list[str] = []
    latest_parts = [
        str(latest_patch.get("created_at") or "").strip(),
        str(latest_patch.get("topic") or "").strip(),
        str(latest_patch.get("patch_type") or "").strip(),
    ]
    latest_text = " / ".join(part for part in latest_parts if part)
    if latest_text:
        evidence.append(f"最近 patch：{latest_text}")
    status_counts: dict[str, int] = {}
    for item in patches:
        status = str(item.get("status") or "unknown").strip() or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
    if status_counts:
        summary = "；".join(f"{status}={count}" for status, count in sorted(status_counts.items()))
        evidence.append(f"patch 状态分布：{summary}")
    return normalize_string_list(evidence)[:6]


def _build_patch_queue_root_traceability(queue: dict[str, Any]) -> list[dict[str, Any]]:
    patches = _sorted_patch_items(queue)
    traceability: list[dict[str, Any]] = []
    for item in reversed(patches):
        item_traceability = item.get("traceability") if isinstance(item.get("traceability"), list) else []
        traceability.extend(item_traceability)
        if len(traceability) >= 12:
            break
    if not traceability and patches:
        latest_patch = patches[-1]
        traceability.append(
            build_traceability_entry(
                kind="patch",
                ref=str(latest_patch.get("id") or "").strip(),
                title=latest_patch.get("topic") or "curriculum-patch-queue",
                detail=latest_patch.get("patch_type") or "feedback",
                stage="feedback",
                status=latest_patch.get("status") or "recorded",
            )
        )
    return traceability[:12]


def _apply_patch_queue_envelope(queue: dict[str, Any] | None) -> dict[str, Any]:
    updated = dict(queue) if isinstance(queue, dict) else {}
    updated.setdefault("schema", PATCH_QUEUE_SCHEMA)
    updated.setdefault("contract_version", CONTRACT_VERSION)
    patches = updated.get("patches") if isinstance(updated.get("patches"), list) else []
    updated["patches"] = patches
    evidence = _build_patch_queue_root_evidence(updated)
    latest_patch = patches[-1] if patches else {}
    queue_confidence = 0.0
    if patches:
        queue_confidence = max(float(item.get("confidence") or 0.0) for item in patches if isinstance(item, dict))
    generation_trace = {
        "stage": "feedback",
        "generator": "curriculum-patch-queue",
        "status": "updated" if patches else "initialized",
    }
    if latest_patch.get("source_update_type"):
        generation_trace["update_type"] = latest_patch.get("source_update_type")
    if latest_patch.get("created_at"):
        generation_trace["updated_at"] = latest_patch.get("created_at")
    return apply_quality_envelope(
        updated,
        stage="feedback",
        generator="curriculum-patch-queue",
        evidence=evidence,
        confidence=queue_confidence,
        quality_review={
            "reviewer": "patch-queue-root-gate",
            "valid": True,
            "issues": [],
            "warnings": [],
            "confidence": queue_confidence,
            "evidence_adequacy": "sufficient" if patches else "partial",
            "verdict": "ready",
        },
        generation_trace=generation_trace,
        traceability=_build_patch_queue_root_traceability(updated),
    )


def patch_queue_path_for_plan(plan_path: Path) -> Path:
    plan = plan_path.expanduser().resolve()
    paths = default_workflow_paths(resolve_learning_root(plan), plan, plan.parent / "materials" / "index.json")
    return paths["curriculum_patch_queue_json"]


def default_patch_queue() -> dict[str, Any]:
    return _apply_patch_queue_envelope(
        {
            "schema": PATCH_QUEUE_SCHEMA,
            "contract_version": CONTRACT_VERSION,
            "patches": [],
        }
    )


def load_patch_queue(path: Path) -> dict[str, Any]:
    existing = read_json_if_exists(path)
    queue = default_patch_queue()
    if isinstance(existing, dict):
        queue.update(existing)
    if not isinstance(queue.get("patches"), list):
        queue["patches"] = []
    queue.setdefault("schema", PATCH_QUEUE_SCHEMA)
    queue.setdefault("contract_version", CONTRACT_VERSION)
    return _apply_patch_queue_envelope(queue)


def should_propose_patch(summary: dict[str, Any], update_type: str) -> bool:
    if update_type == "diagnostic":
        return bool(summary.get("recommended_entry_level"))
    if summary.get("can_advance"):
        return True
    if summary.get("should_review"):
        return True
    if normalize_string_list(summary.get("high_freq_errors") or summary.get("weaknesses")):
        return True
    mastery = summary.get("mastery") if isinstance(summary.get("mastery"), dict) else {}
    return bool(mastery and (not mastery.get("reading_done") or not mastery.get("reflection_done")))


def validate_patch_proposal(patch: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    quality_review = patch.get("quality_review") if isinstance(patch.get("quality_review"), dict) else {}
    generation_trace = patch.get("generation_trace") if isinstance(patch.get("generation_trace"), dict) else {}
    if not quality_review.get("valid"):
        issues.append("patch.quality_review_invalid")
    if not generation_trace:
        issues.append("patch.generation_trace_missing")
    if not normalize_string_list(patch.get("traceability") or []):
        issues.append("patch.traceability_missing")
    if not patch.get("evidence") and patch_status(patch.get("status")) != "pending-evidence":
        issues.append("patch.evidence_missing")
    policy = patch_risk_policy(patch.get("patch_type"))
    if patch.get("application_policy") != policy["application_policy"]:
        issues.append("patch.application_policy_mismatch")
    confidence = patch.get("confidence")
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        confidence_value = 0.0
    if confidence_value <= 0:
        issues.append("patch.confidence_missing")
    return issues



def build_patch_proposal(summary: dict[str, Any], session_facts: dict[str, Any], *, update_type: str) -> dict[str, Any] | None:
    if not should_propose_patch(summary, update_type):
        return None
    date = session_facts.get("date") or summary.get("date") or "unknown-date"
    topic = session_facts.get("topic") or summary.get("topic") or "未命名主题"
    weaknesses = normalize_string_list(summary.get("high_freq_errors") or summary.get("weaknesses"))
    review_focus = normalize_string_list(summary.get("review_focus") or weaknesses)
    next_actions = normalize_string_list(summary.get("next_learning") or summary.get("next_actions"))
    evidence = normalize_string_list(session_facts.get("evidence"))
    status = "proposed" if evidence else "pending-evidence"
    patch_type = "review-adjustment"
    rationale = "根据本次 session 证据补充复习债。"
    if update_type == "diagnostic":
        patch_type = "entry-level-adjustment"
        rationale = "根据前置诊断建议调整起步层级。"
    elif summary.get("can_advance"):
        patch_type = "advance-proposal"
        rationale = "本次 session 达到推进条件，建议进入下一阶段或下一批内容。"
    elif summary.get("should_review") or weaknesses:
        patch_type = "review-adjustment"
        rationale = "本次 session 暴露薄弱点，建议先补强再推进。"

    policy = patch_risk_policy(patch_type)
    patch = {
        "id": f"{date}:{update_type}:{topic}",
        "status": status,
        "patch_type": patch_type,
        "risk_level": policy["risk_level"],
        "topic": topic,
        "created_at": date,
        "source_update_type": update_type,
        "rationale": rationale,
        "evidence": evidence,
        "confidence": session_facts.get("outcome", {}).get("confidence") or (0.65 if evidence else 0.35),
        "proposal": {
            "recommended_entry_level": summary.get("recommended_entry_level"),
            "review_focus": review_focus,
            "next_actions": next_actions,
            "blocking_weaknesses": normalize_string_list(summary.get("blocking_weaknesses") or weaknesses),
            "deferred_enhancement": normalize_string_list(summary.get("deferred_enhancement") or summary.get("defer_enhancement")),
            "can_advance": bool(summary.get("can_advance")),
            "should_review": bool(summary.get("should_review")),
        },
        "application_policy": policy["application_policy"],
    }
    traceability = list(session_facts.get("traceability") or [])
    traceability.append(
        build_traceability_entry(
            kind="session",
            ref=str(session_facts.get("session_dir") or ""),
            title=topic,
            detail=patch_type,
            stage="feedback",
            status=patch["status"],
        )
    )
    patch["traceability"] = traceability
    patch["generation_trace"] = {
        "stage": "feedback",
        "generator": "curriculum-patch",
        "status": patch["status"],
        "update_type": update_type,
    }
    patch["quality_review"] = {
        "reviewer": "deterministic-feedback-gate",
        "valid": True,
        "issues": [],
        "warnings": [],
        "confidence": patch.get("confidence"),
        "evidence_adequacy": "sufficient" if evidence else "partial",
        "verdict": "ready",
    }
    quality_issues = validate_patch_proposal(patch)
    if quality_issues and patch["status"] == "proposed":
        patch["status"] = "pending-evidence"
        patch["generation_trace"]["status"] = patch["status"]
    patch["quality_review"] = {
        "reviewer": "deterministic-feedback-gate",
        "valid": not quality_issues,
        "issues": quality_issues,
        "warnings": [],
        "confidence": patch.get("confidence"),
        "evidence_adequacy": "sufficient" if evidence else "partial",
        "verdict": "ready" if not quality_issues else "needs-revision",
    }
    return apply_quality_envelope(
        patch,
        stage="feedback",
        generator="curriculum-patch",
        evidence=evidence,
        confidence=patch.get("confidence"),
        quality_review=patch["quality_review"],
        generation_trace={
            "stage": "feedback",
            "generator": "curriculum-patch",
            "status": patch["status"],
            "update_type": update_type,
        },
        traceability=traceability,
    )



def merge_patch(queue: dict[str, Any], patch: dict[str, Any] | None) -> dict[str, Any]:
    updated = deepcopy(queue) if isinstance(queue, dict) else default_patch_queue()
    updated.setdefault("schema", PATCH_QUEUE_SCHEMA)
    updated.setdefault("contract_version", CONTRACT_VERSION)
    patches = updated.get("patches") if isinstance(updated.get("patches"), list) else []
    if not patch:
        updated["patches"] = patches
        return updated
    patch_id = patch.get("id")
    replaced = False
    next_patches: list[dict[str, Any]] = []
    for item in patches:
        if isinstance(item, dict) and item.get("id") == patch_id and item.get("status") in PENDING_PATCH_STATUSES:
            next_patches.append(patch)
            replaced = True
        else:
            next_patches.append(item)
    if not replaced:
        next_patches.append(patch)
    updated["patches"] = next_patches[-100:]
    return _apply_patch_queue_envelope(updated)


def write_patch_queue(path: Path, queue: dict[str, Any]) -> None:
    write_json(path, queue)


def update_patch_queue_file(
    plan_path: Path,
    summary: dict[str, Any],
    session_facts: dict[str, Any],
    *,
    update_type: str,
    patch_candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = patch_queue_path_for_plan(plan_path)
    queue = load_patch_queue(path)
    if patch_candidate is None:
        write_patch_queue(path, queue)
        return {"path": str(path), "patch": None, "queue": queue}
    patch = deepcopy(patch_candidate)
    policy = patch_risk_policy(patch.get("patch_type"))
    patch.setdefault("risk_level", policy["risk_level"])
    patch.setdefault("application_policy", policy["application_policy"])
    quality_issues = validate_patch_proposal(patch)
    if quality_issues:
        patch = apply_quality_envelope(
            patch,
            stage="feedback",
            generator="curriculum-patch-candidate-gate",
            evidence=normalize_string_list(patch.get("evidence") or []),
            confidence=patch.get("confidence"),
            quality_review={
                "reviewer": "curriculum-patch-candidate-gate",
                "valid": False,
                "issues": quality_issues,
                "warnings": [],
                "confidence": patch.get("confidence"),
                "evidence_adequacy": "sufficient" if patch.get("evidence") else "partial",
                "verdict": "needs-revision",
            },
            generation_trace={
                **(patch.get("generation_trace") if isinstance(patch.get("generation_trace"), dict) else {}),
                "stage": "feedback",
                "generator": "curriculum-patch-candidate-gate",
                "status": "rejected",
            },
            traceability=list(patch.get("traceability") or []),
        )
        write_patch_queue(path, queue)
        return {"path": str(path), "patch": patch, "queue": queue, "quality_issues": quality_issues}
    updated = merge_patch(queue, patch)
    write_patch_queue(path, updated)
    return {"path": str(path), "patch": patch, "queue": updated, "quality_issues": []}


__all__ = [
    "PATCH_QUEUE_SCHEMA",
    "apply_approval_patch_decisions",
    "build_patch_proposal",
    "default_patch_queue",
    "load_patch_queue",
    "merge_patch",
    "patch_queue_path_for_plan",
    "patch_risk_policy",
    "should_propose_patch",
    "update_patch_queue_file",
    "write_patch_queue",
]
