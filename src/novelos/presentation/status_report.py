from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from novelos.query.service import query_project


def build_status_report(project_root: Path) -> dict:
    project_payload = query_project(project_root=project_root, query_type="project")
    progress_payload = query_project(project_root=project_root, query_type="progress")
    tasks_payload = query_project(project_root=project_root, query_type="tasks")
    summaries_payload = query_project(project_root=project_root, query_type="summaries")
    decisions_payload = query_project(project_root=project_root, query_type="decisions")
    foreshadowing_payload = query_project(project_root=project_root, query_type="foreshadowing")
    entities_payload = query_project(project_root=project_root, query_type="entities")

    project = project_payload.get("project", {})
    progress = progress_payload.get("progress", {})
    tasks = tasks_payload.get("tasks", []) or []
    summaries = summaries_payload.get("summaries", []) or []
    sync_issues = summaries_payload.get("sync_issues", []) or []
    decisions = decisions_payload.get("decisions", []) or []
    foreshadowing_items = foreshadowing_payload.get("foreshadowing", []) or []
    entities = entities_payload.get("entities", []) or []

    task_health = _task_health(tasks)
    summary_health = {
        "total_summaries": len(summaries),
        "sync_issue_count": len(sync_issues),
    }
    entity_health = {
        "total_entities": len(entities),
        "character_count": sum(1 for item in entities if item.get("entity_type") == "character"),
        "location_count": sum(1 for item in entities if item.get("entity_type") == "location"),
    }
    alerts = _build_alerts(
        progress=progress,
        task_health=task_health,
        summary_health=summary_health,
        foreshadowing_count=len(foreshadowing_items),
    )

    return {
        "query_type": "status_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "project_id": project.get("project_id"),
            "title": project.get("title"),
            "status": project.get("status"),
            "active_volume": project.get("active_volume"),
            "active_chapter": project.get("active_chapter"),
        },
        "progress": progress,
        "task_health": task_health,
        "summary_health": summary_health,
        "foreshadowing_health": {
            "total_items": len(foreshadowing_items),
        },
        "decision_health": {
            "total_decisions": len(decisions),
            "latest_decision_type": None if not decisions else decisions[-1].get("decision_type"),
        },
        "entity_health": entity_health,
        "alerts": alerts,
        "risk_level": _risk_level(alerts),
    }


def _task_health(tasks: list[dict]) -> dict:
    running = 0
    failed = 0
    completed = 0
    for task in tasks:
        status = str(task.get("task_status", "")).strip().lower()
        if status == "running":
            running += 1
        elif status == "failed":
            failed += 1
        elif status == "completed":
            completed += 1

    latest_task = tasks[0] if tasks else {}
    return {
        "total_tasks": len(tasks),
        "running_tasks": running,
        "failed_tasks": failed,
        "completed_tasks": completed,
        "latest_task": {
            "task_id": latest_task.get("task_id"),
            "task_type": latest_task.get("task_type"),
            "task_status": latest_task.get("task_status"),
            "current_step": latest_task.get("current_step"),
        }
        if latest_task
        else None,
    }


def _build_alerts(
    *,
    progress: dict,
    task_health: dict,
    summary_health: dict,
    foreshadowing_count: int,
) -> list[dict]:
    alerts: list[dict] = []
    completed_chapters = int(progress.get("completed_chapters", 0) or 0)

    if int(task_health.get("failed_tasks", 0)) > 0:
        alerts.append(
            {
                "level": "critical",
                "code": "task_failures_present",
                "message": "One or more tasks are marked as failed.",
            }
        )
    if int(summary_health.get("sync_issue_count", 0)) > 0:
        alerts.append(
            {
                "level": "warning",
                "code": "summary_sync_issues",
                "message": "Text summaries and structured summaries are out of sync.",
            }
        )
    if completed_chapters > 0 and int(summary_health.get("total_summaries", 0)) == 0:
        alerts.append(
            {
                "level": "warning",
                "code": "missing_summaries",
                "message": "Completed chapters exist but summaries are missing.",
            }
        )
    if completed_chapters >= 3 and foreshadowing_count == 0:
        alerts.append(
            {
                "level": "info",
                "code": "foreshadowing_sparse",
                "message": "Foreshadowing items are sparse compared with chapter progress.",
            }
        )
    return alerts


def _risk_level(alerts: list[dict]) -> str:
    levels = [str(item.get("level", "info")).strip().lower() for item in alerts]
    if "critical" in levels:
        return "critical"
    if "warning" in levels:
        return "warning"
    return "info"
