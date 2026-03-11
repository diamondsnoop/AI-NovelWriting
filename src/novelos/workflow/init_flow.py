from pathlib import Path

from novelos.creation.init_builder import create_project_files
from novelos.memory.store import build_project_paths, ensure_project_layout, init_project_state


def run_init(project_root: Path, title: str) -> dict:
    paths = build_project_paths(project_root)
    ensure_project_layout(paths)
    create_project_files(paths, title)
    init_project_state(paths, title)
    return {"project_root": str(project_root), "title": title}
