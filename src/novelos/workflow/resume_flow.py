from pathlib import Path

from novelos.foundation.io import read_json
from novelos.memory.store import build_project_paths


def run_resume(project_root: Path) -> dict:
    paths = build_project_paths(project_root)
    task_files = sorted(paths.tasks_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not task_files:
        return {"status": "no_tasks"}

    latest_task = read_json(task_files[0], default={})
    snapshots = []
    for snapshot_id in latest_task.get("snapshot_ids", []):
        snapshot = read_json(paths.snapshots_dir / f"{snapshot_id}.json", default={})
        if snapshot:
            snapshots.append(snapshot)

    return {
        "status": "ok",
        "task": latest_task,
        "snapshots": snapshots,
    }
