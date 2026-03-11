from __future__ import annotations


def collect_decision_triggers(*, write_package: dict, review_result: dict) -> list[dict]:
    triggers: list[dict] = []
    checker_results = review_result.get("checker_results", []) or []

    # 1) Review severe issues.
    for checker_result in checker_results:
        severity = _resolve_severity(checker_result)
        if severity != "critical":
            continue
        checker = str(checker_result.get("checker", "unknown"))
        triggers.append(
            {
                "trigger_code": "review_severe_issue",
                "source_module": "review.service_v2",
                "source_field": f"checker_results[{checker}].severity",
                "severity": "critical",
                "summary": f"Critical review issue detected in checker `{checker}`.",
                "payload": {
                    "checker": checker,
                    "issues": checker_result.get("issues", []),
                    "signals": checker_result.get("signals", {}),
                },
            }
        )

    # 2) Setting conflict from consistency checker.
    consistency_result = next(
        (item for item in checker_results if str(item.get("checker")) == "consistency"),
        None,
    )
    if consistency_result and _is_setting_conflict(consistency_result):
        triggers.append(
            {
                "trigger_code": "setting_conflict",
                "source_module": "review.consistency_checker",
                "source_field": "checker_results[consistency].signals.codes/score",
                "severity": "critical" if _resolve_severity(consistency_result) == "critical" else "warning",
                "summary": "Possible setting conflict detected by consistency checker.",
                "payload": {
                    "score": consistency_result.get("score"),
                    "issues": consistency_result.get("issues", []),
                    "signals": consistency_result.get("signals", {}),
                },
            }
        )

    # 3) Route branch from write package candidates.
    route_branch_candidates = write_package.get("route_branch_candidates", []) or []
    if isinstance(route_branch_candidates, list):
        clean_candidates = [str(item).strip() for item in route_branch_candidates if str(item).strip()]
    else:
        clean_candidates = []
    if len(clean_candidates) >= 2:
        triggers.append(
            {
                "trigger_code": "route_branch",
                "source_module": "workflow.context_package",
                "source_field": "write_package.route_branch_candidates",
                "severity": "warning",
                "summary": "Possible route branching detected from planning context.",
                "payload": {
                    "candidates": clean_candidates[:4],
                    "candidate_count": len(clean_candidates),
                },
            }
        )

    return _dedupe_triggers(triggers)


def _resolve_severity(checker_result: dict) -> str:
    severity = checker_result.get("severity")
    if isinstance(severity, str) and severity in {"critical", "warning", "info"}:
        return severity

    score = checker_result.get("score")
    try:
        value = float(score)
    except (TypeError, ValueError):
        return "info"
    if value < 0.35:
        return "critical"
    if value < 0.6:
        return "warning"
    return "info"


def _is_setting_conflict(consistency_result: dict) -> bool:
    signals = consistency_result.get("signals", {})
    codes = []
    if isinstance(signals, dict) and isinstance(signals.get("codes"), list):
        codes = [str(code).strip() for code in signals["codes"] if str(code).strip()]
    if "consistency_conflict" in codes:
        return True

    score = consistency_result.get("score")
    try:
        return float(score) < 0.5
    except (TypeError, ValueError):
        return False


def _dedupe_triggers(triggers: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()
    for trigger in triggers:
        key = f"{trigger.get('trigger_code')}::{trigger.get('source_field')}::{trigger.get('summary')}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(trigger)
    return deduped
