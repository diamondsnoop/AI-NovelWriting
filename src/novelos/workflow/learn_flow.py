from __future__ import annotations

from pathlib import Path

from novelos.memory.project_memory_store import save_project_memory
from novelos.memory.store import (
    build_project_paths,
    create_task_state,
    load_project_state,
    save_task_state,
    write_snapshot,
)
from novelos.workflow.state_tracker import StateTracker


def run_learn(
    project_root: Path,
    *,
    memory_type: str,
    content: str,
    source_refs: list[str] | None = None,
) -> dict:
    paths = build_project_paths(project_root)
    project_state = load_project_state(paths)
    if not project_state:
        raise ValueError("Project is not initialized. Run init first.")

    task_state = create_task_state(paths, "learn")
    tracker = StateTracker(paths)

    memory_record = save_project_memory(
        project_root=project_root,
        memory_type=memory_type,
        content=content,
        source_refs=source_refs,
    )
    tracker.mark_step(task_state, "memory_saved")
    snapshot_id = write_snapshot(
        paths,
        task_state["task_id"],
        "memory_saved",
        {
            "memory_id": memory_record["memory_id"],
            "memory_type": memory_record["memory_type"],
        },
    )
    task_state["snapshot_ids"].append(snapshot_id)
    save_task_state(paths, task_state)
    tracker.mark_done(task_state)

    return {
        "task_id": task_state["task_id"],
        "memory_record": memory_record,
    }
