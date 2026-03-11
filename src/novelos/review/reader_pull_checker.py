from __future__ import annotations

import re


SOFT_LANDING_CUES = (
    "告一段落",
    "一切恢复平静",
    "暂时结束",
    "先到这里",
    "回去休息",
    "明天再说",
    "事情结束了",
)
HOOK_CUES = (
    "？",
    "然而",
    "但",
    "却",
    "未解",
    "下一章",
    "下一步",
    "忽然",
    "突然",
)


class ReaderPullChecker:
    def run(
        self,
        *,
        draft_text: str,
        chapter_no: int,
        chapter_outline: str,
        chapter_beats: str,
        structured_summary: dict | None,
    ) -> dict:
        if not draft_text.strip() or chapter_no < 1:
            return _skipped("Draft text is empty or chapter number is invalid.")

        tail = _extract_tail_window(draft_text)
        if not tail.strip():
            return _skipped("Tail window is empty.")

        structured_summary = structured_summary or {}
        marker = _normalize_reader_pull_marker(structured_summary.get("reader_pull_marker"))
        has_hook_cue = _contains_any(tail, HOOK_CUES)
        soft_landing = _contains_any(tail, SOFT_LANDING_CUES)
        beat_hook = _contains_any(f"{chapter_outline}\n{chapter_beats}", ("hook", "钩子", "悬念", "未解"))

        codes: list[str] = []
        issues: list[str] = []
        score = 0.74
        severity = "info"

        if not marker["has_pull"] and not has_hook_cue:
            codes.append("reader_pull_missing")
            issues.append("Ending lacks a visible pull signal for next chapter.")
            score = 0.25
            severity = "critical"
        else:
            if soft_landing and not marker["has_pull"]:
                codes.append("reader_pull_soft_landing")
                issues.append("Ending appears to soft-land and may reduce follow-up motivation.")
                score = min(score, 0.54)
                severity = "warning"
            if marker["has_pull"] and _is_weak_marker(marker) and not beat_hook:
                codes.append("reader_pull_weak_hook")
                issues.append("Reader-pull marker exists but evidence/hook style looks weak.")
                score = min(score, 0.58)
                severity = "warning"

        if not codes:
            codes = ["reader_pull_present"]
            score = 0.8
            severity = "info"

        return {
            "checker": "reader_pull",
            "status": "completed",
            "score": round(score, 3),
            "severity": severity,
            "issues": issues,
            "message": "Reader-pull check completed." if not issues else "Reader-pull risks detected.",
            "signals": {
                "codes": codes,
                "metrics": {
                    "tail_chars": len(tail),
                    "has_hook_cue": has_hook_cue,
                    "soft_landing": soft_landing,
                    "marker_has_pull": marker["has_pull"],
                    "marker_pull_type": marker["pull_type"],
                },
            },
        }


def _normalize_reader_pull_marker(raw: object) -> dict:
    if not isinstance(raw, dict):
        raw = {}
    return {
        "has_pull": bool(raw.get("has_pull", False)),
        "pull_type": str(raw.get("pull_type", "")).strip(),
        "evidence": str(raw.get("evidence", "")).strip(),
    }


def _extract_tail_window(text: str) -> str:
    content = text.strip()
    if not content:
        return ""
    total = len(content)
    length = int(total * 0.15)
    length = max(300, min(1200, length))
    if total <= length:
        return content
    return content[-length:]


def _contains_any(text: str, cues: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(cue.lower() in lowered for cue in cues)


def _is_weak_marker(marker: dict) -> bool:
    pull_type = marker.get("pull_type", "")
    evidence = marker.get("evidence", "")
    if not pull_type:
        return True
    if len(evidence) < 10:
        return True
    if re.fullmatch(r"(open_question|suspense|reveal|cliffhanger)", pull_type.lower()):
        return False
    return False


def _skipped(message: str) -> dict:
    return {
        "checker": "reader_pull",
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
