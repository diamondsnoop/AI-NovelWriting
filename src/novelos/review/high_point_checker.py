from __future__ import annotations

import re


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}")


class HighPointChecker:
    def run(
        self,
        *,
        draft_text: str,
        chapter_no: int,
        chapter_beats: str,
        chapter_timeline: str,
        structured_summary: dict | None,
    ) -> dict:
        if not draft_text.strip() or chapter_no < 1:
            return _skipped("Draft text is empty or chapter number is invalid.")

        structured_summary = structured_summary or {}
        markers = _normalize_markers(structured_summary.get("high_point_markers"))
        beat_count = _estimate_beat_count(chapter_beats)
        density = len(markers) / max(1, beat_count)
        aligned = _is_aligned(markers, chapter_beats=chapter_beats, chapter_timeline=chapter_timeline)

        codes: list[str] = []
        issues: list[str] = []
        score = 0.72
        severity = "info"

        if not markers:
            codes.append("high_point_missing")
            issues.append("No high-point marker is detected in current chapter summary.")
            score = 0.25
            severity = "critical"
        else:
            if density < 0.35:
                codes.append("high_point_density_low")
                issues.append("High-point density looks low against chapter beat count.")
                score = min(score, 0.55)
                severity = "warning"
            if not aligned:
                codes.append("high_point_not_aligned_with_beats")
                issues.append("High-point markers are weakly aligned with beats/timeline.")
                score = min(score, 0.52)
                severity = "warning"

        if not codes:
            codes = ["high_point_present"]
            issues = []
            score = 0.78
            severity = "info"

        return {
            "checker": "high_point",
            "status": "completed",
            "score": round(score, 3),
            "severity": severity,
            "issues": issues,
            "message": "High-point check completed." if not issues else "High-point risks detected.",
            "signals": {
                "codes": codes,
                "metrics": {
                    "marker_count": len(markers),
                    "beat_count": beat_count,
                    "density": round(density, 3),
                    "aligned": aligned,
                },
            },
        }


def _normalize_markers(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def _estimate_beat_count(chapter_beats: str) -> int:
    if not chapter_beats.strip():
        return 0
    count = 0
    for line in chapter_beats.splitlines():
        striped = line.strip()
        if not striped:
            continue
        if striped.startswith("- "):
            count += 1
            continue
        if re.match(r"^\d+[.)、\s]", striped):
            count += 1
    if count > 0:
        return count
    return max(1, len([line for line in chapter_beats.splitlines() if line.strip()]))


def _is_aligned(markers: list[str], *, chapter_beats: str, chapter_timeline: str) -> bool:
    if not markers:
        return False
    corpus = f"{chapter_beats}\n{chapter_timeline}".lower()
    if not corpus.strip():
        return False
    corpus_tokens = set(TOKEN_PATTERN.findall(corpus))
    if not corpus_tokens:
        return False

    for marker in markers:
        marker_tokens = set(TOKEN_PATTERN.findall(marker.lower()))
        if marker_tokens and len(marker_tokens & corpus_tokens) >= 1:
            return True
    return False


def _skipped(message: str) -> dict:
    return {
        "checker": "high_point",
        "status": "skipped",
        "score": None,
        "severity": "info",
        "issues": [],
        "message": message,
        "signals": {
            "codes": [],
            "metrics": {},
        },
    }
