from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from learn_core.io import read_json_if_exists, write_json, write_text
from learn_core.text_utils import normalize_int, normalize_string_list

KNOWLEDGE_STATE_FILENAME = "knowledge-state.json"
KNOWLEDGE_MAP_FILENAME = "knowledge-map.md"
CONTRACT_VERSION = "learn-plan.knowledge-state.v1"
SCHEMA_VERSION = "1.0"
MAX_MASTERY_DELTA = 20
DEFAULT_EVIDENCE_TYPES = {
    "recognition",
    "explanation",
    "calculation",
    "implementation",
    "transfer",
    "retention",
    "debugging",
}


class KnowledgeStateError(ValueError):
    pass


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def resolve_knowledge_paths(plan_path: Path) -> dict[str, Path]:
    root = plan_path.expanduser().resolve().parent
    return {
        "knowledge_state": root / KNOWLEDGE_STATE_FILENAME,
        "knowledge_map": root / KNOWLEDGE_MAP_FILENAME,
    }


def _slug(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower()
    chars = []
    for char in text:
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    slug = "".join(chars).strip("-")
    return slug or fallback


def derive_status_label(mastery: Any) -> str:
    try:
        score = int(float(mastery))
    except (TypeError, ValueError):
        score = 0
    if score >= 100:
        return "已熟练掌握"
    if score >= 80:
        return "已熟悉"
    if score >= 60:
        return "已了解"
    if score > 0:
        return "不熟悉"
    return "未学习"


def _node_title(node: dict[str, Any]) -> str:
    return str(node.get("title") or node.get("id") or "未命名知识点").strip()


def _unique(items: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, dict) else str(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _extract_candidate_stages(planning: dict[str, Any] | None) -> list[dict[str, Any]]:
    planning = planning if isinstance(planning, dict) else {}
    candidates: list[Any] = []
    for key in ("stage_plan", "stages", "daily_roadmap"):
        value = planning.get(key)
        if isinstance(value, list) and value:
            candidates = value
            break
    return [item for item in candidates if isinstance(item, dict)]


def _extract_research_capabilities(research: dict[str, Any] | None) -> list[str]:
    research = research if isinstance(research, dict) else {}
    report = research.get("research_report") if isinstance(research.get("research_report"), dict) else research
    values: list[str] = []
    for key in ("must_master_core", "must_master_capabilities", "mainline_capabilities", "supporting_capabilities"):
        values.extend(normalize_string_list(report.get(key)))
    metrics = report.get("capability_metrics") if isinstance(report.get("capability_metrics"), list) else []
    for metric in metrics:
        if isinstance(metric, dict):
            values.append(str(metric.get("name") or metric.get("title") or metric.get("capability") or "").strip())
    return [item for item in _unique([item for item in values if item])]


def _default_required_evidence(title: str, goal: str) -> list[str]:
    text = f"{title} {goal}".lower()
    evidence = ["explanation"]
    if any(token in text for token in ("代码", "编程", "python", "pandas", "api", "实现", "项目", "脚本")):
        evidence.append("implementation")
    if any(token in text for token in ("计算", "公式", "数学", "统计", "窗口", "聚合")):
        evidence.append("calculation")
    if any(token in text for token in ("debug", "调试", "错误", "异常", "排障")):
        evidence.append("debugging")
    if any(token in text for token in ("迁移", "综合", "项目", "应用", "真实")):
        evidence.append("transfer")
    return [item for item in _unique(evidence) if item in DEFAULT_EVIDENCE_TYPES]


def build_default_knowledge_state(
    *,
    topic: str,
    goal: str,
    level: str,
    schedule: str,
    preference: str,
    planning: dict[str, Any] | None = None,
    research: dict[str, Any] | None = None,
    diagnostic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stages = _extract_candidate_stages(planning)
    capabilities = _extract_research_capabilities(research)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    domain_id = f"domain-{_slug(topic, 'main')}"
    nodes.append(
        {
            "id": domain_id,
            "title": topic or "学习主线",
            "level": "domain",
            "parent_id": None,
            "description": goal,
            "source": "learn-plan:goal",
            "relevance": 1.0,
            "derived_mastery": 0,
            "child_ids": [],
            "notes": ["顶层节点只展示 derived_mastery，不维护真实 mastery。"],
            "expandable_subpoints": [],
        }
    )

    if not stages:
        stages = [
            {"name": "核心主线", "focus": item, "goal": item}
            for item in (capabilities[:4] or [goal or topic or "核心能力"])
        ]

    previous_topic_id: str | None = None
    for stage_index, stage in enumerate(stages[:8], start=1):
        title = str(stage.get("name") or stage.get("title") or stage.get("focus") or f"主题 {stage_index}").strip()
        topic_id = f"topic-{stage_index:02d}-{_slug(title, 'topic')}"
        focus_values = normalize_string_list(stage.get("focus")) or normalize_string_list(stage.get("stage_goal")) or normalize_string_list(stage.get("goal")) or [title]
        nodes.append(
            {
                "id": topic_id,
                "title": title,
                "level": "topic",
                "parent_id": domain_id,
                "description": str(stage.get("goal") or stage.get("stage_goal") or stage.get("focus") or title),
                "source": "learn-plan:stage",
                "relevance": 1.0 if stage_index <= 3 else 0.7,
                "derived_mastery": 0,
                "child_ids": [],
                "notes": [],
                "expandable_subpoints": normalize_string_list(stage.get("expandable_subpoints")),
            }
        )
        nodes[0]["child_ids"].append(topic_id)
        if previous_topic_id:
            edges.append(
                {
                    "from": previous_topic_id,
                    "to": topic_id,
                    "type": "recommended",
                    "reason": "阶段路线推荐顺序",
                    "source": "learn-plan:stage_order",
                    "confidence": "medium",
                }
            )
        previous_topic_id = topic_id

        leaf_candidates = focus_values[:3]
        if len(leaf_candidates) == 1 and title not in leaf_candidates:
            leaf_candidates.append(title)
        for leaf_index, leaf_title in enumerate(leaf_candidates[:4], start=1):
            point_title = str(leaf_title or title).strip()
            point_id = f"kp-{stage_index:02d}-{leaf_index:02d}-{_slug(point_title, 'point')}"
            nodes.append(
                {
                    "id": point_id,
                    "title": point_title,
                    "level": "knowledge_point",
                    "parent_id": topic_id,
                    "description": f"能围绕“{point_title}”完成解释、练习和应用验证。",
                    "source": "learn-plan:core_leaf",
                    "relevance": 1.0 if stage_index <= 3 else 0.7,
                    "mastery": 0,
                    "confidence": "low",
                    "target_mastery": 80 if stage_index <= 3 else 70,
                    "required_evidence_types": _default_required_evidence(point_title, goal),
                    "status_label": "未学习",
                    "last_studied": None,
                    "last_tested": None,
                    "evidence_refs": [],
                    "next_action": "learn",
                    "notes": [],
                    "expandable_subpoints": [],
                }
            )
            topic_node = next(item for item in nodes if item["id"] == topic_id)
            topic_node["child_ids"].append(point_id)
            edges.append(
                {
                    "from": topic_id,
                    "to": point_id,
                    "type": "recommended",
                    "reason": "主题包含该核心叶子知识点",
                    "source": "learn-plan:core_leaf",
                    "confidence": "medium",
                }
            )

    state = {
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "goal": {
            "topic": topic,
            "goal": goal,
            "level": level,
            "schedule": schedule,
            "preference": preference,
        },
        "status": "draft",
        "nodes": nodes,
        "edges": edges,
        "coverage_report": {},
        "dag_validation": {},
        "diagnostic_blueprint": {
            "owner": "/learn-test",
            "default_mode": "standard",
            "requires_user_confirmation": True,
            "budget": {
                "rounds": (diagnostic or {}).get("max_rounds") or 2,
                "questions_per_round": (diagnostic or {}).get("questions_per_round") or 5,
            },
        },
        "evidence_log": [],
        "history": [
            {
                "event": "created",
                "timestamp": now_iso(),
                "source": "/learn-plan",
                "summary": "生成初始核心叶子知识图谱。",
            }
        ],
    }
    validate_knowledge_state(state)
    return recalculate_state(state)


def _leaf_nodes(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [node for node in state.get("nodes", []) if isinstance(node, dict) and node.get("level") == "knowledge_point"]


def _node_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(node.get("id")): node
        for node in state.get("nodes", [])
        if isinstance(node, dict) and str(node.get("id") or "").strip()
    }


def _child_ids(state: dict[str, Any], parent_id: str) -> list[str]:
    return [str(node.get("id")) for node in state.get("nodes", []) if isinstance(node, dict) and node.get("parent_id") == parent_id]


def _descendant_leaf_ids(state: dict[str, Any], node_id: str) -> list[str]:
    mapping = _node_map(state)
    result: list[str] = []
    stack = _child_ids(state, node_id)
    while stack:
        current_id = stack.pop()
        current = mapping.get(current_id)
        if not current:
            continue
        if current.get("level") == "knowledge_point":
            result.append(current_id)
        else:
            stack.extend(_child_ids(state, current_id))
    return result


def _detect_cycle(edges: list[dict[str, Any]], node_ids: set[str]) -> bool:
    graph: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        source = str(edge.get("from") or "")
        target = str(edge.get("to") or "")
        if source in graph and target in node_ids:
            graph[source].append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> bool:
        if node_id in visiting:
            return True
        if node_id in visited:
            return False
        visiting.add(node_id)
        for target in graph.get(node_id, []):
            if visit(target):
                return True
        visiting.remove(node_id)
        visited.add(node_id)
        return False

    return any(visit(node_id) for node_id in node_ids)


def validate_knowledge_state(state: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if state.get("contract_version") != CONTRACT_VERSION:
        issues.append("knowledge.contract_version.unsupported")
    if state.get("schema_version") != SCHEMA_VERSION:
        issues.append("knowledge.schema_version.unsupported")
    nodes = state.get("nodes") if isinstance(state.get("nodes"), list) else []
    edges = state.get("edges") if isinstance(state.get("edges"), list) else []
    ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict):
            issues.append("knowledge.node.invalid")
            continue
        node_id = str(node.get("id") or "").strip()
        level = str(node.get("level") or "").strip()
        if not node_id:
            issues.append("knowledge.node.id_missing")
        ids.append(node_id)
        if level not in {"domain", "topic", "knowledge_point"}:
            issues.append(f"knowledge.node.level_invalid:{node_id}")
        if level != "domain" and node.get("parent_id") not in ids and not any(isinstance(item, dict) and item.get("id") == node.get("parent_id") for item in nodes):
            issues.append(f"knowledge.node.parent_missing:{node_id}")
        if level != "knowledge_point" and "mastery" in node:
            issues.append(f"knowledge.node.upper_mastery_forbidden:{node_id}")
        if level == "knowledge_point":
            if not isinstance(node.get("required_evidence_types"), list) or not node.get("required_evidence_types"):
                issues.append(f"knowledge.node.required_evidence_missing:{node_id}")
            unknown = [item for item in node.get("required_evidence_types") or [] if item not in DEFAULT_EVIDENCE_TYPES]
            if unknown:
                issues.append(f"knowledge.node.required_evidence_unknown:{node_id}")
            try:
                mastery = int(float(node.get("mastery", 0)))
                target = int(float(node.get("target_mastery", 0)))
            except (TypeError, ValueError):
                issues.append(f"knowledge.node.mastery_invalid:{node_id}")
                mastery = target = 0
            if not 0 <= mastery <= 100:
                issues.append(f"knowledge.node.mastery_range:{node_id}")
            if not 0 <= target <= 100:
                issues.append(f"knowledge.node.target_mastery_range:{node_id}")
    if len(ids) != len(set(ids)):
        issues.append("knowledge.node.duplicate_id")
    node_ids = set(ids)
    for edge in edges:
        if not isinstance(edge, dict):
            issues.append("knowledge.edge.invalid")
            continue
        if edge.get("from") not in node_ids:
            issues.append(f"knowledge.edge.from_missing:{edge.get('from')}")
        if edge.get("to") not in node_ids:
            issues.append(f"knowledge.edge.to_missing:{edge.get('to')}")
        if edge.get("type") not in {"hard", "soft", "recommended", "diagnostic"}:
            issues.append(f"knowledge.edge.type_invalid:{edge.get('from')}->{edge.get('to')}")
    if _detect_cycle(edges, node_ids):
        issues.append("knowledge.dag.cycle")
    if issues:
        raise KnowledgeStateError("; ".join(issues))
    return {"valid": True, "issues": [], "checked_at": now_iso()}


def recalculate_state(state: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(state, ensure_ascii=False))
    mapping = _node_map(updated)
    for node in updated.get("nodes", []):
        if not isinstance(node, dict):
            continue
        if node.get("level") == "knowledge_point":
            node["status_label"] = derive_status_label(node.get("mastery", 0))
            continue
        leaf_ids = _descendant_leaf_ids(updated, str(node.get("id")))
        leaves = [mapping[leaf_id] for leaf_id in leaf_ids if leaf_id in mapping]
        total_weight = 0.0
        weighted = 0.0
        for leaf in leaves:
            try:
                weight = float(leaf.get("relevance", 1.0) or 1.0)
                mastery = float(leaf.get("mastery", 0) or 0)
            except (TypeError, ValueError):
                continue
            total_weight += weight
            weighted += mastery * weight
        node["derived_mastery"] = round(weighted / total_weight, 1) if total_weight else 0
        node["child_ids"] = _child_ids(updated, str(node.get("id")))
    leaf_count = len(_leaf_nodes(updated))
    source_counts: dict[str, int] = {}
    for node in updated.get("nodes", []):
        source = str((node or {}).get("source") or "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
    low_confidence_edges = [edge for edge in updated.get("edges", []) if edge.get("confidence") == "low"]
    updated["coverage_report"] = {
        "leaf_count": leaf_count,
        "source_counts": source_counts,
        "low_confidence_edge_count": len(low_confidence_edges),
        "core_leaf_policy": "初始图谱采用核心叶子粒度；边缘细节先保留为 expandable_subpoints / notes。",
        "updated_at": now_iso(),
    }
    updated["dag_validation"] = {"valid": True, "issues": [], "checked_at": now_iso()}
    return updated


def load_knowledge_state(plan_path: Path) -> dict[str, Any] | None:
    path = resolve_knowledge_paths(plan_path)["knowledge_state"]
    data = read_json_if_exists(path)
    if not data:
        return None
    validate_knowledge_state(data)
    return recalculate_state(data)


def save_knowledge_state(plan_path: Path, state: dict[str, Any], *, write_map: bool = True) -> dict[str, Path]:
    paths = resolve_knowledge_paths(plan_path)
    updated = recalculate_state(state)
    validate_knowledge_state(updated)
    write_json(paths["knowledge_state"], updated)
    if write_map:
        write_text(paths["knowledge_map"], render_knowledge_map(updated))
    return paths


def render_knowledge_map(state: dict[str, Any]) -> str:
    updated = recalculate_state(state)
    mapping = _node_map(updated)
    lines = [
        "# Knowledge Map",
        "",
        "## 状态摘要",
        "",
        f"- contract_version：{updated.get('contract_version')}",
        f"- schema_version：{updated.get('schema_version')}",
        f"- 图谱状态：{updated.get('status')}",
        f"- 底层知识点数量：{updated.get('coverage_report', {}).get('leaf_count', 0)}",
        "- 粒度策略：初始采用核心叶子；边缘 API 参数、罕见选项和细碎题型先保留为 expandable_subpoints / notes。",
        "",
        "## 层级知识图谱",
        "",
    ]
    roots = [node for node in updated.get("nodes", []) if isinstance(node, dict) and node.get("level") == "domain"]

    def emit(node_id: str, depth: int) -> None:
        node = mapping[node_id]
        indent = "  " * depth
        if node.get("level") == "knowledge_point":
            lines.append(
                f"{indent}- {node.get('title')}（{node.get('mastery', 0)}%，{node.get('status_label')}，confidence={node.get('confidence')}，target={node.get('target_mastery')}）"
            )
            evidence = ", ".join(node.get("required_evidence_types") or [])
            if evidence:
                lines.append(f"{indent}  - required evidence：{evidence}")
            if node.get("expandable_subpoints"):
                lines.append(f"{indent}  - 可展开子项：{'；'.join(normalize_string_list(node.get('expandable_subpoints')))}")
            return
        lines.append(f"{indent}- {node.get('title')}（derived_mastery={node.get('derived_mastery', 0)}）")
        for child_id in node.get("child_ids") or _child_ids(updated, node_id):
            if child_id in mapping:
                emit(child_id, depth + 1)

    for root in roots:
        emit(str(root.get("id")), 0)
    lines.extend(["", "## 关键依赖", ""])
    for edge in updated.get("edges", [])[:80]:
        source = mapping.get(str(edge.get("from")))
        target = mapping.get(str(edge.get("to")))
        if not source or not target:
            continue
        lines.append(f"- {source.get('title')} → {target.get('title')}（{edge.get('type')}）：{edge.get('reason')}")
    lines.extend(["", "## Coverage Report", ""])
    report = updated.get("coverage_report") or {}
    lines.append(f"- 底层知识点数量：{report.get('leaf_count', 0)}")
    lines.append(f"- 低置信依赖数量：{report.get('low_confidence_edge_count', 0)}")
    lines.append(f"- 来源分布：{json.dumps(report.get('source_counts') or {}, ensure_ascii=False, sort_keys=True)}")
    lines.extend(["", "## DAG 校验", ""])
    validation = updated.get("dag_validation") or {}
    lines.append(f"- valid：{validation.get('valid')}")
    lines.append(f"- checked_at：{validation.get('checked_at')}")
    lines.extend(["", "## Diagnostic Blueprint", ""])
    blueprint = updated.get("diagnostic_blueprint") or {}
    lines.append("- 初始测试题生成由 /learn-test 负责。")
    lines.append(f"- 默认模式：{blueprint.get('default_mode', 'standard')}")
    lines.append(f"- 需要用户确认图谱：{blueprint.get('requires_user_confirmation', True)}")
    return "\n".join(lines).rstrip() + "\n"


def _hard_prerequisite_ids(state: dict[str, Any], point_id: str) -> list[str]:
    return [
        str(edge.get("from"))
        for edge in state.get("edges", [])
        if edge.get("to") == point_id and edge.get("type") == "hard"
    ]


def readiness_for_points(state: dict[str, Any], point_ids: list[str], *, min_mastery: int = 60) -> dict[str, Any]:
    mapping = _node_map(state)
    blocked: list[dict[str, Any]] = []
    ready: list[str] = []
    for point_id in point_ids:
        prerequisites = _hard_prerequisite_ids(state, point_id)
        missing = []
        for prereq_id in prerequisites:
            prereq = mapping.get(prereq_id)
            if not prereq:
                missing.append({"id": prereq_id, "reason": "missing"})
                continue
            mastery = int(float(prereq.get("mastery", 0) or 0))
            confidence = str(prereq.get("confidence") or "low")
            if mastery < min_mastery or confidence == "low":
                missing.append({"id": prereq_id, "title": prereq.get("title"), "mastery": mastery, "confidence": confidence})
        if missing:
            blocked.append({"id": point_id, "title": (mapping.get(point_id) or {}).get("title"), "missing_prerequisites": missing})
        else:
            ready.append(point_id)
    return {"ready_point_ids": ready, "blocked_points": blocked, "ready": not blocked}


def _topic_leaf_ids(state: dict[str, Any], topic_hint: str | None) -> list[str]:
    hint = str(topic_hint or "").strip().lower()
    mapping = _node_map(state)
    selected: list[str] = []
    for node in state.get("nodes", []):
        if not isinstance(node, dict) or node.get("level") != "topic":
            continue
        title = str(node.get("title") or "").lower()
        description = str(node.get("description") or "").lower()
        if not hint or hint in title or hint in description or title in hint:
            selected.extend(_descendant_leaf_ids(state, str(node.get("id"))))
    if not selected:
        selected = [str(node.get("id")) for node in _leaf_nodes(state)]
    return [item for item in _unique(selected) if item in mapping]


def build_lesson_target_slice(state: dict[str, Any], *, stage: str | None = None, topic: str | None = None, time_budget: str | None = None) -> dict[str, Any]:
    updated = recalculate_state(state)
    mapping = _node_map(updated)
    candidates = _topic_leaf_ids(updated, topic)
    leaves = [mapping[item] for item in candidates if item in mapping]
    leaves.sort(key=lambda node: (float(node.get("mastery", 0) or 0) - float(node.get("target_mastery", 80) or 80), -float(node.get("relevance", 1) or 1)))
    primary = [str(node.get("id")) for node in leaves[:3]]
    prerequisite_ids = _unique([prereq for point_id in primary for prereq in _hard_prerequisite_ids(updated, point_id)])
    review = [
        str(node.get("id"))
        for node in _leaf_nodes(updated)
        if str(node.get("confidence") or "") == "low" or int(float(node.get("mastery", 0) or 0)) < 60
    ][:3]
    readiness = readiness_for_points(updated, primary)
    return {
        "session_goal": f"推进 {topic or stage or '当前主题'} 的核心知识点",
        "plan_pointer": {"stage": stage, "topic": topic, "time_budget": time_budget},
        "primary_points": primary,
        "prerequisite_points": prerequisite_ids,
        "review_points": review,
        "bridge_points": prerequisite_ids[:2] if not readiness.get("ready") else [],
        "blocked_points": readiness.get("blocked_points", []),
        "evidence_targets": _unique([e for point_id in primary for e in (mapping.get(point_id, {}).get("required_evidence_types") or [])]),
        "material_segments": [],
        "readiness": readiness,
    }


def build_test_coverage_slice(state: dict[str, Any], *, test_goal: str = "阶段测试", rounds: int = 2, questions_per_round: int = 5) -> dict[str, Any]:
    updated = recalculate_state(state)
    leaves = _leaf_nodes(updated)
    leaves.sort(key=lambda node: (str(node.get("confidence") or "low") != "low", float(node.get("mastery", 0) or 0), -float(node.get("relevance", 1) or 1)))
    budget = max(1, rounds) * max(1, questions_per_round)
    selected = [str(node.get("id")) for node in leaves[: max(3, min(len(leaves), budget * 2))]]
    excluded = [str(node.get("id")) for node in leaves if str(node.get("id")) not in selected]
    return {
        "test_goal": test_goal,
        "coverage_budget": {"rounds": rounds, "questions_per_round": questions_per_round},
        "selected_points": selected,
        "excluded_points": excluded,
        "question_mapping": [],
        "evidence_types": _unique([e for node in leaves if str(node.get("id")) in selected for e in (node.get("required_evidence_types") or [])]),
        "expected_confidence_update": {
            "covered_leaf_count": len(selected),
            "total_leaf_count": len(leaves),
            "coverage_ratio": round(len(selected) / len(leaves), 3) if leaves else 0,
        },
    }


def _clamp_delta(delta: Any, limit: int = MAX_MASTERY_DELTA) -> int:
    try:
        value = int(float(delta))
    except (TypeError, ValueError):
        return 0
    return max(-limit, min(limit, value))


def _question_knowledge_point_ids(question: dict[str, Any]) -> list[str]:
    source_trace = question.get("source_trace") if isinstance(question.get("source_trace"), dict) else {}
    rubric = question.get("rubric_by_knowledge_point") if isinstance(question.get("rubric_by_knowledge_point"), dict) else {}
    return normalize_string_list(
        question.get("knowledge_point_ids")
        or question.get("knowledge_points")
        or source_trace.get("knowledge_point_ids")
        or source_trace.get("knowledge_points")
        or list(rubric.keys())
    )


def _question_evidence_types(question: dict[str, Any]) -> list[str]:
    source_trace = question.get("source_trace") if isinstance(question.get("source_trace"), dict) else {}
    values = normalize_string_list(question.get("evidence_types") or source_trace.get("evidence_types"))
    return [item for item in values if item in DEFAULT_EVIDENCE_TYPES]


def build_session_knowledge_evidence_items(
    progress: dict[str, Any],
    questions_map: dict[str, dict[str, Any]],
    *,
    session_type: str,
    gate: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if gate is not None and not (gate.get("completion_received") and gate.get("reflection_completed")):
        return []
    question_progress = progress.get("questions") if isinstance(progress.get("questions"), dict) else {}
    evidence_items: list[dict[str, Any]] = []
    for qid, item in question_progress.items():
        item = item if isinstance(item, dict) else {}
        stats = item.get("stats") if isinstance(item.get("stats"), dict) else {}
        attempts = normalize_int(stats.get("attempts"))
        if attempts <= 0:
            continue
        question = questions_map.get(qid) or questions_map.get(str(qid)) or {}
        if not isinstance(question, dict) or question.get("category") == "open":
            continue
        point_ids = _question_knowledge_point_ids(question)
        if not point_ids:
            continue
        category = str(question.get("category") or "unknown").strip().lower()
        success_count = normalize_int(stats.get("pass_count")) if category == "code" else normalize_int(stats.get("correct_count"))
        if not success_count:
            last_status = str(stats.get("last_status") or "").strip().lower()
            success_count = 1 if last_status in {"passed", "correct"} else 0
        success = success_count > 0
        evidence_types = _question_evidence_types(question)
        if not evidence_types:
            continue
        delta = 8 if success else -4
        if session_type == "test" and success:
            delta = 10
        confidence_after = "medium" if success else "low"
        title = str(question.get("title") or question.get("question") or qid).strip()
        evidence_items.append(
            {
                "knowledge_point_ids": point_ids,
                "evidence_types": evidence_types,
                "mastery_delta": delta,
                "confidence_after": confidence_after,
                "summary": f"{title}: {'答对/通过' if success else '未通过'}，尝试 {attempts} 次",
                "source": f"/learn-{session_type}:question:{qid}",
            }
        )
    return evidence_items


def count_applicable_session_evidence(state: dict[str, Any], evidence_items: list[dict[str, Any]]) -> int:
    mapping = _node_map(state)
    count = 0
    for item in evidence_items:
        if not isinstance(item, dict):
            continue
        evidence_types = [e for e in normalize_string_list(item.get("evidence_types") or item.get("evidence_type")) if e in DEFAULT_EVIDENCE_TYPES]
        if not evidence_types:
            continue
        point_ids = normalize_string_list(item.get("knowledge_point_ids") or item.get("knowledge_points") or item.get("point_id"))
        for point_id in point_ids:
            node = mapping.get(point_id)
            if node and node.get("level") == "knowledge_point":
                count += 1
    return count


def update_state_from_session_evidence(
    state: dict[str, Any],
    *,
    session_dir: Path,
    session_type: str,
    evidence_items: list[dict[str, Any]],
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(state, ensure_ascii=False))
    mapping = _node_map(updated)
    log = updated.get("evidence_log") if isinstance(updated.get("evidence_log"), list) else []
    timestamp = now_iso()
    applied_count = 0
    for item in evidence_items:
        if not isinstance(item, dict):
            continue
        point_ids = normalize_string_list(item.get("knowledge_point_ids") or item.get("knowledge_points") or item.get("point_id"))
        evidence_types = [e for e in normalize_string_list(item.get("evidence_types") or item.get("evidence_type")) if e in DEFAULT_EVIDENCE_TYPES]
        if not evidence_types:
            continue
        delta = _clamp_delta(item.get("mastery_delta", 0))
        confidence = item.get("confidence_after") or item.get("confidence")
        for point_id in point_ids:
            node = mapping.get(point_id)
            if not node or node.get("level") != "knowledge_point":
                continue
            mastery = int(float(node.get("mastery", 0) or 0))
            node["mastery"] = max(0, min(100, mastery + delta))
            if confidence in {"low", "medium", "high"}:
                node["confidence"] = confidence
            if session_type == "test":
                node["last_tested"] = timestamp
            else:
                node["last_studied"] = timestamp
            evidence_id = f"ev-{len(log) + 1:05d}"
            node.setdefault("evidence_refs", [])
            if evidence_id not in node["evidence_refs"]:
                node["evidence_refs"].append(evidence_id)
            log.append(
                {
                    "id": evidence_id,
                    "timestamp": timestamp,
                    "session_dir": str(session_dir),
                    "session_type": session_type,
                    "knowledge_point_ids": [point_id],
                    "evidence_types": evidence_types,
                    "mastery_delta": delta,
                    "summary": item.get("summary") or item.get("rationale") or (summary or {}).get("overall"),
                    "source": item.get("source") or f"/learn-{session_type}",
                }
            )
            applied_count += 1
    if not applied_count:
        return recalculate_state(updated)
    updated["evidence_log"] = log[-500:]
    history = updated.get("history") if isinstance(updated.get("history"), list) else []
    history.append(
        {
            "event": "session_evidence_update",
            "timestamp": timestamp,
            "source": f"/learn-{session_type}",
            "session_dir": str(session_dir),
            "summary": (summary or {}).get("overall") or f"{session_type} session 更新知识状态",
            "applied_evidence_count": applied_count,
        }
    )
    updated["history"] = history[-100:]
    return recalculate_state(updated)
