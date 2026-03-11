from pathlib import Path

from novelos.decision.store import list_decision_records
from novelos.foundation.io import read_json
from novelos.memory.entities import list_entities
from novelos.memory.summaries import load_structured_summary
from novelos.memory.store import build_project_paths, load_project_state


SUPPORTED_QUERY_TYPES = {
    "project",
    "progress",
    "tasks",
    "snapshots",
    "decisions",
    "entities",
    "relationships",
    "foreshadowing",
    "summaries",
}


def _load_tasks(paths) -> list[dict]:
    tasks = []
    if not paths.tasks_dir.exists():
        return tasks
    for file in sorted(paths.tasks_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = read_json(file, default={})
        if payload:
            tasks.append(payload)
    return tasks


def _load_snapshots(paths, limit: int = 5) -> list[dict]:
    snapshots = []
    if not paths.snapshots_dir.exists():
        return snapshots
    files = sorted(paths.snapshots_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for file in files[:limit]:
        payload = read_json(file, default={})
        if payload:
            snapshots.append(payload)
    return snapshots


def _load_summaries(paths) -> dict:
    text_summaries = {}
    if paths.summaries_dir.exists():
        for file in sorted(paths.summaries_dir.glob("chapter_*_summary.md")):
            chapter_key = file.stem.replace("_summary", "")
            text_summaries[chapter_key] = file.read_text(encoding="utf-8")

    structured_summaries = {}
    structured_root = paths.meta_dir / "summaries"
    if structured_root.exists():
        for file in sorted(structured_root.glob("chapter_*_summary.json")):
            chapter_key = file.stem.replace("_summary", "")
            structured_summaries[chapter_key] = read_json(file, default={})

    all_keys = sorted(set(text_summaries) | set(structured_summaries))
    summaries = []
    sync_issues = []
    for chapter_key in all_keys:
        text_exists = chapter_key in text_summaries
        structured_exists = chapter_key in structured_summaries
        if text_exists != structured_exists:
            sync_issues.append(
                {
                    "chapter": chapter_key,
                    "text_exists": text_exists,
                    "structured_exists": structured_exists,
                }
            )
        summaries.append(
            {
                "chapter": chapter_key,
                "text_summary": text_summaries.get(chapter_key),
                "structured_summary": structured_summaries.get(chapter_key),
                "in_sync": text_exists and structured_exists,
            }
        )
    return {
        "summaries": summaries,
        "sync_issues": sync_issues,
    }


def query_project(project_root: Path, query_type: str) -> dict:
    if query_type not in SUPPORTED_QUERY_TYPES:
        raise ValueError(f"Unsupported query type: {query_type}")

    paths = build_project_paths(project_root)
    project_state = load_project_state(paths)
    tasks = _load_tasks(paths)

    if query_type == "project":
        return {
            "query_type": "project",
            "project": project_state.get("project", {}),
        }

    if query_type == "progress":
        return {
            "query_type": "progress",
            "progress": project_state.get("project_state", {}).get("progress", {}),
        }

    if query_type == "tasks":
        return {
            "query_type": "tasks",
            "tasks": tasks,
        }

    if query_type == "snapshots":
        return {
            "query_type": "snapshots",
            "snapshots": _load_snapshots(paths),
        }

    if query_type == "decisions":
        return {
            "query_type": "decisions",
            "decisions": list_decision_records(project_root),
        }

    if query_type == "entities":
        return {
            "query_type": "entities",
            "entities": list_entities(project_root),
        }

    if query_type == "summaries":
        payload = _load_summaries(paths)
        return {
            "query_type": "summaries",
            "summaries": payload["summaries"],
            "sync_issues": payload["sync_issues"],
        }

    return {
        "query_type": query_type,
        "status": "not_ready",
        "message": "Data object is defined in design docs but the write path is not implemented yet.",
    }
