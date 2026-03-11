from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from novelos.foundation.io import ensure_dir, read_json, write_json


def project_memory_dir(project_root: Path) -> Path:
    return project_root / ".novelos" / "project_memory"


def save_project_memory(
    project_root: Path,
    *,
    memory_type: str,
    content: str,
    source_refs: list[str] | None = None,
) -> dict:
    root = project_memory_dir(project_root)
    ensure_dir(root)

    record = {
        "memory_id": str(uuid4()),
        "memory_type": memory_type.strip() or "general",
        "content": content.strip(),
        "source_refs": [str(item).strip() for item in (source_refs or []) if str(item).strip()],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(root / f"{record['memory_id']}.json", record)
    return record


def list_project_memory(project_root: Path) -> list[dict]:
    root = project_memory_dir(project_root)
    if not root.exists():
        return []
    records = []
    for file in sorted(root.glob("*.json")):
        payload = read_json(file, default={})
        if payload:
            records.append(payload)
    return records
