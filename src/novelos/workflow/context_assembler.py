from pathlib import Path

from novelos.foundation.io import read_text
from novelos.memory.store import ProjectPaths, outline_file


def build_write_package(project_state: dict, chapter_no: int, paths: ProjectPaths) -> dict:
    project = project_state.get("project", {})
    state = project_state.get("project_state", {})
    chapter_outline = read_text(outline_file(paths, chapter_no), default="")
    return {
        "project_title": project.get("title", "Untitled Project"),
        "chapter_no": chapter_no,
        "summary_hint": (
            f"当前进度：第{state.get('progress', {}).get('current_chapter', 0)}章后。"
            "请生成下一章的骨架草稿。"
        ),
        "chapter_outline": chapter_outline,
        "project_state": state,
    }
