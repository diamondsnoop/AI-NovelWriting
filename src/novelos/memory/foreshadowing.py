from pathlib import Path
from uuid import uuid4

from novelos.foundation.io import ensure_dir, read_json, write_json


def foreshadowing_dir(project_root: Path) -> Path:
    return project_root / ".novelos" / "foreshadowing"


def save_foreshadowing(project_root: Path, chapter_no: int, items: list[dict]) -> list[dict]:
    root = foreshadowing_dir(project_root)
    ensure_dir(root)
    stored = []
    for item in items:
        payload = {
            "foreshadowing_id": str(uuid4()),
            "chapter_no": chapter_no,
            **item,
        }
        write_json(root / f"{payload['foreshadowing_id']}.json", payload)
        stored.append(payload)
    return stored


def list_foreshadowing(project_root: Path) -> list[dict]:
    root = foreshadowing_dir(project_root)
    if not root.exists():
        return []
    records = []
    for file in sorted(root.glob("*.json")):
        record = read_json(file, default={})
        if record:
            records.append(record)
    return records
