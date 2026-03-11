from __future__ import annotations

from pathlib import Path

from novelos.presentation.status_report import build_status_report
from novelos.query.service import query_project


def build_dashboard_view(project_root: Path) -> dict:
    status_report = build_status_report(project_root)
    project = query_project(project_root=project_root, query_type="project").get("project", {})
    progress = query_project(project_root=project_root, query_type="progress").get("progress", {})
    entities = query_project(project_root=project_root, query_type="entities").get("entities", []) or []
    decisions = query_project(project_root=project_root, query_type="decisions").get("decisions", []) or []
    summaries = query_project(project_root=project_root, query_type="summaries").get("summaries", []) or []
    foreshadowing = query_project(project_root=project_root, query_type="foreshadowing").get("foreshadowing", []) or []

    return {
        "query_type": "dashboard",
        "mode": "read_only",
        "project_overview": {
            "title": project.get("title"),
            "status": project.get("status"),
            "active_volume": project.get("active_volume"),
            "active_chapter": project.get("active_chapter"),
            "completed_chapters": progress.get("completed_chapters", 0),
        },
        "chapter_overview": {
            "summary_coverage": {
                "summary_count": len(summaries),
                "completed_chapters": progress.get("completed_chapters", 0),
            },
            "foreshadowing_count": len(foreshadowing),
        },
        "entity_overview": _entity_overview(entities),
        "decision_overview": {
            "total_decisions": len(decisions),
            "latest_decision_type": None if not decisions else decisions[-1].get("decision_type"),
        },
        "risk_panel": {
            "risk_level": status_report.get("risk_level", "info"),
            "alerts": status_report.get("alerts", []),
        },
    }


def _entity_overview(entities: list[dict]) -> dict:
    type_counts: dict[str, int] = {}
    for entity in entities:
        entity_type = str(entity.get("entity_type", "unknown")).strip() or "unknown"
        type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
    return {
        "total_entities": len(entities),
        "type_counts": type_counts,
    }
