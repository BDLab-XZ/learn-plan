from __future__ import annotations

from typing import Any


FORMAL_PLAN_WRITE_ALLOWED = "formal_plan_write_allowed"
FORMAL_PLAN_WRITE_BLOCKERS = "formal_plan_write_blockers"


def planning_artifact_source_blockers(workflow_state: dict[str, Any]) -> list[str]:
    planning_artifact = workflow_state.get("planning_artifact") if isinstance(workflow_state.get("planning_artifact"), dict) else {}
    if not planning_artifact:
        return []
    if planning_artifact.get("candidate_error"):
        return ["formal_plan.planning_candidate_error"]
    if not isinstance(planning_artifact.get("plan_candidate"), dict):
        return ["formal_plan.planning_candidate_missing"]
    generation_mode = str(planning_artifact.get("generation_mode") or "").strip()
    artifact_source = str(planning_artifact.get("artifact_source") or "").strip()
    generation_trace = planning_artifact.get("generation_trace") if isinstance(planning_artifact.get("generation_trace"), dict) else {}
    trace_source = str(generation_trace.get("artifact_source") or "").strip()
    allowed_generation_modes = {"harness-injected"}
    allowed_sources = {"harness-injected", "agent-subagent", "subagent", "user"}
    if generation_mode in allowed_generation_modes:
        return []
    if artifact_source in allowed_sources or trace_source in allowed_sources:
        return []
    return ["formal_plan.planning_candidate_source_invalid"]


def formal_plan_write_blockers(workflow_state: dict[str, Any], mode: str) -> list[str]:
    blockers: list[str] = []
    normalized_mode = str(mode or "").strip()
    blocking_stage = str(workflow_state.get("blocking_stage") or "")
    quality_issues = list(workflow_state.get("quality_issues") or [])
    missing_requirements = list(workflow_state.get("missing_requirements") or [])

    if normalized_mode != "finalize":
        blockers.append("formal_plan.mode_not_finalize")
    if blocking_stage != "ready":
        blockers.append(f"formal_plan.blocking_stage.{blocking_stage or 'unknown'}")
    if normalized_mode == "finalize" and blocking_stage != "ready":
        blockers.append("formal_plan.mode_finalize_with_blocker")
    blockers.extend(planning_artifact_source_blockers(workflow_state))
    if quality_issues:
        blockers.append("formal_plan.quality_issues")
    if missing_requirements:
        blockers.append("formal_plan.missing_requirements")
    return blockers


def can_write_formal_plan(workflow_state: dict[str, Any], mode: str) -> bool:
    return not formal_plan_write_blockers(workflow_state, mode)


def annotate_formal_plan_gate(workflow_state: dict[str, Any], mode: str) -> dict[str, Any]:
    annotated = dict(workflow_state)
    blockers = formal_plan_write_blockers(annotated, mode)
    annotated[FORMAL_PLAN_WRITE_ALLOWED] = not blockers
    annotated[FORMAL_PLAN_WRITE_BLOCKERS] = blockers
    return annotated
