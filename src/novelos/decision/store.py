from pathlib import Path
from uuid import uuid4

from novelos.foundation.io import ensure_dir, read_json, write_json


def decisions_dir(project_root: Path) -> Path:
    return project_root / ".novelos" / "decisions"


def save_decision_record(project_root: Path, payload: dict) -> dict:
    ensure_dir(decisions_dir(project_root))
    record = {
        "decision_id": str(uuid4()),
        **payload,
    }
    write_json(decisions_dir(project_root) / f"{record['decision_id']}.json", record)
    return record


def list_decision_records(project_root: Path) -> list[dict]:
    root = decisions_dir(project_root)
    if not root.exists():
        return []
    records = []
    for file in sorted(root.glob("*.json")):
        record = read_json(file, default={})
        if record:
            records.append(record)
    return records
