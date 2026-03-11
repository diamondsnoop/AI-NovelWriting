from pathlib import Path
import re
from uuid import uuid4

from novelos.foundation.io import ensure_dir, read_json, write_json
from novelos.foundation.logging import get_logger


logger = get_logger("novelos.foreshadowing")


def foreshadowing_dir(project_root: Path) -> Path:
    return project_root / ".novelos" / "foreshadowing"


def save_foreshadowing(project_root: Path, chapter_no: int, items: list[dict]) -> list[dict]:
    root = foreshadowing_dir(project_root)
    ensure_dir(root)
    existing = list_foreshadowing(project_root)
    filtered = _dedupe_items(existing, items)
    if len(filtered) > 5:
        logger.warning(
            "foreshadowing_truncated chapter=%s original_count=%s kept_count=%s",
            chapter_no,
            len(filtered),
            5,
        )
        filtered = filtered[:5]
    stored = []
    for item in filtered:
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


def _dedupe_items(existing_items: list[dict], new_items: list[dict]) -> list[dict]:
    kept: list[dict] = []
    existing_signatures = [_signature(item) for item in existing_items]
    seen_new_signatures: list[set[str]] = []
    for item in new_items:
        signature = _signature(item)
        if not signature:
            continue
        if any(_jaccard(signature, other) >= 0.6 for other in existing_signatures):
            continue
        if any(_jaccard(signature, other) >= 0.75 for other in seen_new_signatures):
            continue
        kept.append(item)
        seen_new_signatures.append(signature)
    return kept


def _signature(item: dict) -> set[str]:
    text = " ".join(
        [
            str(item.get("setup", "")).strip(),
            str(item.get("hint", "")).strip(),
            str(item.get("expected_payoff", "")).strip(),
        ]
    ).lower()
    return set(re.findall(r"[\u4e00-\u9fff]|[a-z0-9_]+", text))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
