from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from novelos.foundation.io import ensure_dir, read_json, write_json


@dataclass(slots=True)
class ProjectPaths:
    root: Path
    meta_dir: Path
    state_file: Path
    tasks_dir: Path
    snapshots_dir: Path
    decisions_dir: Path
    chapters_dir: Path
    outlines_dir: Path
    summaries_dir: Path


def build_project_paths(project_root: Path) -> ProjectPaths:
    meta_dir = project_root / ".novelos"
    return ProjectPaths(
        root=project_root,
        meta_dir=meta_dir,
        state_file=meta_dir / "project_state.json",
        tasks_dir=meta_dir / "tasks",
        snapshots_dir=meta_dir / "snapshots",
        decisions_dir=meta_dir / "decisions",
        chapters_dir=project_root / "chapters",
        outlines_dir=project_root / "outlines",
        summaries_dir=project_root / "summaries",
    )


def ensure_project_layout(paths: ProjectPaths) -> None:
    for path in (
        paths.root,
        paths.meta_dir,
        paths.tasks_dir,
        paths.snapshots_dir,
        paths.decisions_dir,
        paths.chapters_dir,
        paths.outlines_dir,
        paths.summaries_dir,
    ):
        ensure_dir(path)


def init_project_state(paths: ProjectPaths, title: str) -> None:
    state = {
        "project": {
            "project_id": str(uuid4()),
            "title": title,
            "active_volume": 1,
            "active_chapter": 0,
            "status": "initialized",
        },
        "project_state": {
            "progress": {"current_volume": 1, "current_chapter": 0, "completed_chapters": 0},
            "protagonist_state": {},
            "world_state": {},
            "plot_threads": [],
            "foreshadowing_state": [],
            "relationship_state": [],
            "arc_state": {},
        },
    }
    write_json(paths.state_file, state)


def load_project_state(paths: ProjectPaths) -> dict[str, Any]:
    return read_json(paths.state_file, default={})


def save_project_state(paths: ProjectPaths, state: dict[str, Any]) -> None:
    write_json(paths.state_file, state)


def task_file(paths: ProjectPaths, task_id: str) -> Path:
    return paths.tasks_dir / f"{task_id}.json"


def create_task_state(paths: ProjectPaths, task_type: str) -> dict[str, Any]:
    task_id = str(uuid4())
    task_state = {
        "task_id": task_id,
        "task_type": task_type,
        "current_step": "created",
        "completed_steps": [],
        "failed_steps": [],
        "task_status": "running",
        "snapshot_ids": [],
        "resume_token": task_id,
    }
    write_json(task_file(paths, task_id), task_state)
    return task_state


def load_task_state(paths: ProjectPaths, task_id: str) -> dict[str, Any]:
    return read_json(task_file(paths, task_id), default={})


def save_task_state(paths: ProjectPaths, task_state: dict[str, Any]) -> None:
    write_json(task_file(paths, task_state["task_id"]), task_state)


def write_snapshot(paths: ProjectPaths, task_id: str, step_name: str, payload: dict[str, Any]) -> str:
    snapshot_id = str(uuid4())
    snapshot = {
        "snapshot_id": snapshot_id,
        "task_id": task_id,
        "step_name": step_name,
        "state_payload": payload,
    }
    write_json(paths.snapshots_dir / f"{snapshot_id}.json", snapshot)
    return snapshot_id


def outline_file(paths: ProjectPaths, chapter_no: int) -> Path:
    return paths.outlines_dir / f"chapter_{chapter_no:04d}_outline.md"


def compact_outline_file(paths: ProjectPaths, chapter_no: int) -> Path:
    return paths.outlines_dir / f"chapter_{chapter_no:04d}_outline_compact.md"


def volume_plan_file(paths: ProjectPaths, volume_no: int) -> Path:
    return paths.outlines_dir / f"volume_{volume_no:04d}_plan.md"


def beat_sheet_file(paths: ProjectPaths, chapter_no: int) -> Path:
    return paths.outlines_dir / f"chapter_{chapter_no:04d}_beats.md"


def timeline_file(paths: ProjectPaths, chapter_no: int) -> Path:
    return paths.outlines_dir / f"chapter_{chapter_no:04d}_timeline.md"


def summary_file(paths: ProjectPaths, chapter_no: int) -> Path:
    return paths.summaries_dir / f"chapter_{chapter_no:04d}_summary.md"
