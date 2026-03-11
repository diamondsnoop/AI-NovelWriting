def gate_review(report: dict) -> dict:
    consistency_score = report.get("scores", {}).get("consistency")
    character_score = report.get("scores", {}).get("character")
    continuity_score = report.get("scores", {}).get("continuity")
    if consistency_score is not None and consistency_score < 0.5:
        return {
            "gate_result": "blocked",
            "reason": "consistency_below_threshold",
        }
    if character_score is not None and character_score < 0.5:
        return {
            "gate_result": "blocked",
            "reason": "character_below_threshold",
        }
    if continuity_score is not None and continuity_score < 0.5:
        return {
            "gate_result": "blocked",
            "reason": "continuity_below_threshold",
        }
    return {
        "gate_result": "pass",
        "reason": None,
    }
