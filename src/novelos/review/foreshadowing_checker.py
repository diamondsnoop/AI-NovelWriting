from __future__ import annotations

import re
from pathlib import Path

from novelos.memory.foreshadowing import list_foreshadowing


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}")
NEGATION_PATTERN = re.compile(r"(不是|并非|无关|不存在|从未|不再|假的|伪造|误导)")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?；;])")


class ForeshadowingChecker:
    def __init__(self, hanging_threshold_chapters: int = 4) -> None:
        self.hanging_threshold_chapters = hanging_threshold_chapters

    def run(self, project_root: str | Path, chapter_no: int, draft_text: str, new_items: list[dict] | None = None) -> dict:
        new_items = new_items or []
        existing_items = [
            item
            for item in list_foreshadowing(Path(project_root))
            if int(item.get("chapter_no", 0) or 0) < chapter_no
        ]
        sentences = _split_sentences(draft_text)

        unclear_items = [item for item in new_items if not _is_clear_item(item)]
        conflict_items = [
            item for item in existing_items if _has_negation_conflict(item=item, sentences=sentences)
        ]
        hanging_items = [
            item
            for item in existing_items
            if _is_hanging(
                item=item,
                chapter_no=chapter_no,
                draft_text=draft_text,
                threshold=self.hanging_threshold_chapters,
            )
        ]

        issues: list[str] = []
        if unclear_items:
            issues.append(
                f"{len(unclear_items)} new foreshadowing item(s) are unclear (missing concrete setup/payoff)."
            )
        if conflict_items:
            issues.append(
                f"{len(conflict_items)} historical foreshadowing item(s) may be contradicted in current draft."
            )
        if hanging_items:
            issues.append(
                f"{len(hanging_items)} foreshadowing item(s) may be hanging too long without recent progression."
            )

        score = _compute_score(
            unclear_count=len(unclear_items),
            conflict_count=len(conflict_items),
            hanging_count=len(hanging_items),
        )
        severity = "warning" if issues else "info"

        if not new_items and not existing_items:
            return {
                "checker": "foreshadowing",
                "status": "skipped",
                "score": None,
                "issues": [],
                "message": "No foreshadowing data available yet.",
                "severity": "info",
            }

        return {
            "checker": "foreshadowing",
            "status": "completed",
            "score": score,
            "issues": issues,
            "message": (
                "Foreshadowing check completed."
                if not issues
                else "Foreshadowing risks detected; review suggested before publishing."
            ),
            "severity": severity,
            "signals": {
                "new_items": len(new_items),
                "unclear_new_items": len(unclear_items),
                "possible_conflicts": len(conflict_items),
                "possible_hanging_items": len(hanging_items),
            },
        }


def _is_clear_item(item: dict) -> bool:
    setup = str(item.get("setup", "")).strip()
    hint = str(item.get("hint", "")).strip()
    expected_payoff = str(item.get("expected_payoff", "")).strip()

    if not setup and not hint:
        return False
    if not expected_payoff:
        return False
    if len(expected_payoff) < 4:
        return False
    return True


def _has_negation_conflict(item: dict, sentences: list[str]) -> bool:
    keywords = _extract_keywords(item)
    if not keywords:
        return False
    for sentence in sentences:
        lowered = sentence.lower()
        if not any(keyword in lowered for keyword in keywords):
            continue
        if NEGATION_PATTERN.search(sentence):
            return True
    return False


def _is_hanging(item: dict, chapter_no: int, draft_text: str, threshold: int) -> bool:
    introduced = int(item.get("chapter_no", 0) or 0)
    if introduced <= 0:
        return False
    if chapter_no - introduced < threshold:
        return False
    keywords = _extract_keywords(item)
    if not keywords:
        return False
    lowered = draft_text.lower()
    return not any(keyword in lowered for keyword in keywords)


def _extract_keywords(item: dict) -> list[str]:
    text = " ".join(
        [
            str(item.get("setup", "")).strip(),
            str(item.get("hint", "")).strip(),
            str(item.get("expected_payoff", "")).strip(),
        ]
    ).lower()
    tokens = TOKEN_PATTERN.findall(text)
    keywords: list[str] = []
    for token in tokens:
        token = token.strip()
        if len(token) < 2:
            continue
        keywords.append(token)
        keywords.extend(_expand_keyword(token))

    deduped: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        if keyword in seen:
            continue
        seen.add(keyword)
        deduped.append(keyword)
    # Keep only first few tokens to avoid over-broad matching.
    return deduped[:12]


def _expand_keyword(token: str) -> list[str]:
    if not re.fullmatch(r"[\u4e00-\u9fff]+", token):
        return []
    length = len(token)
    if length <= 4:
        return []

    expansions = []
    # Keep prefix/suffix anchors and a few short n-grams to improve Chinese matching.
    expansions.append(token[:4])
    expansions.append(token[-4:])
    for size in (2, 3):
        for start in range(0, min(length - size + 1, 4)):
            expansions.append(token[start : start + size])
    return expansions


def _split_sentences(text: str) -> list[str]:
    chunks = [part.strip() for part in SENTENCE_SPLIT_PATTERN.split(text) if part and part.strip()]
    return chunks if chunks else [text.strip()]


def _compute_score(unclear_count: int, conflict_count: int, hanging_count: int) -> float:
    score = 1.0
    score -= min(0.45, unclear_count * 0.15)
    score -= min(0.5, conflict_count * 0.25)
    score -= min(0.3, hanging_count * 0.1)
    if score < 0:
        score = 0.0
    return round(score, 3)
