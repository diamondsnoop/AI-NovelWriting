from pathlib import Path
from uuid import uuid4

from novelos.foundation.io import ensure_dir, read_json, write_json


def entities_dir(project_root: Path) -> Path:
    return project_root / ".novelos" / "entities"


def save_entities(project_root: Path, chapter_no: int, entities: list[dict]) -> list[dict]:
    root = entities_dir(project_root)
    ensure_dir(root)
    stored = []
    for entity in entities:
        payload = {
            "entity_id": str(uuid4()),
            "chapter_no": chapter_no,
            **entity,
        }
        write_json(root / f"{payload['entity_id']}.json", payload)
        stored.append(payload)
    return stored


def list_entities(project_root: Path) -> list[dict]:
    root = entities_dir(project_root)
    if not root.exists():
        return []
    records = []
    for file in sorted(root.glob("*.json")):
        record = read_json(file, default={})
        if record:
            records.append(record)
    return records
