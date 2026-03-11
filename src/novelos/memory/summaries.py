from pathlib import Path

from novelos.foundation.io import ensure_dir, read_json, write_json


def summaries_dir(project_root: Path) -> Path:
    return project_root / ".novelos" / "summaries"


def save_structured_summary(project_root: Path, chapter_no: int, payload: dict) -> None:
    root = summaries_dir(project_root)
    ensure_dir(root)
    write_json(root / f"chapter_{chapter_no:04d}_summary.json", payload)


def load_structured_summary(project_root: Path, chapter_no: int) -> dict:
    return read_json(summaries_dir(project_root) / f"chapter_{chapter_no:04d}_summary.json", default={})


def load_recent_structured_summaries(project_root: Path, chapter_no: int, limit: int) -> list[dict]:
    start = max(1, chapter_no - limit)
    return [
        load_structured_summary(project_root, current)
        for current in range(start, chapter_no)
        if load_structured_summary(project_root, current)
    ]
