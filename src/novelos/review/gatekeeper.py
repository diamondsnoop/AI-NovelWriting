BLOCKING_CHECKERS = {"consistency", "character", "continuity"}


def gate_review(report: dict) -> dict:
    checker_results = report.get("checker_results", []) or []
    blocking_reasons: list[str] = []
    warning_reasons: list[str] = []

    for result in checker_results:
        checker = str(result.get("checker", "unknown"))
        status = str(result.get("status", "completed"))
        if status == "skipped":
            continue

        severity = _resolve_severity(result)
        if severity is None:
            continue

        reason = _first_signal_code(result) or f"{checker}_{severity}"
        if severity == "critical":
            if checker in BLOCKING_CHECKERS:
                blocking_reasons.append(reason)
            else:
                warning_reasons.append(reason)
            continue
        if severity == "warning":
            warning_reasons.append(reason)

    # Keep compatibility with existing hard threshold on core consistency chain.
    scores = report.get("scores", {})
    consistency_score = scores.get("consistency")
    character_score = scores.get("character")
    continuity_score = scores.get("continuity")
    if consistency_score is not None and consistency_score < 0.5:
        blocking_reasons.append("consistency_below_threshold")
    if character_score is not None and character_score < 0.5:
        blocking_reasons.append("character_below_threshold")
    if continuity_score is not None and continuity_score < 0.5:
        blocking_reasons.append("continuity_below_threshold")

    if blocking_reasons:
        return {
            "gate_result": "blocked",
            "reason": blocking_reasons[0],
            "gate_level": "critical",
            "blocking_reasons": _dedupe(blocking_reasons),
            "warning_reasons": _dedupe(warning_reasons),
        }

    if warning_reasons:
        return {
            "gate_result": "pass",
            "reason": None,
            "gate_level": "warning",
            "blocking_reasons": [],
            "warning_reasons": _dedupe(warning_reasons),
        }

    return {
        "gate_result": "pass",
        "reason": None,
        "gate_level": "info",
        "blocking_reasons": [],
        "warning_reasons": [],
    }


def _resolve_severity(result: dict) -> str | None:
    severity = result.get("severity")
    if isinstance(severity, str) and severity in {"critical", "warning", "info"}:
        return severity

    score = result.get("score")
    if score is None:
        return None
    try:
        value = float(score)
    except (TypeError, ValueError):
        return None
    if value < 0.35:
        return "critical"
    if value < 0.6:
        return "warning"
    return "info"


def _first_signal_code(result: dict) -> str | None:
    signals = result.get("signals", {})
    if not isinstance(signals, dict):
        return None
    codes = signals.get("codes")
    if not isinstance(codes, list):
        return None
    for code in codes:
        code_value = str(code).strip()
        if code_value:
            return code_value
    return None


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered
