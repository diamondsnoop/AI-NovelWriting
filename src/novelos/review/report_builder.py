from novelos.foundation.logging import get_logger


logger = get_logger("novelos.review")


def _normalize_score(score: object, checker: str) -> float | None:
    if score is None:
        return None
    try:
        value = float(score)
    except (TypeError, ValueError):
        logger.warning("review_score_invalid checker=%s raw_score=%r", checker, score)
        return None

    if value > 1:
        normalized = value / 100.0
        logger.warning(
            "review_score_normalized checker=%s raw_score=%s normalized_score=%s",
            checker,
            value,
            normalized,
        )
        value = normalized

    if value < 0:
        logger.warning("review_score_clamped_low checker=%s raw_score=%s", checker, value)
        value = 0.0
    elif value > 1:
        logger.warning("review_score_clamped_high checker=%s raw_score=%s", checker, value)
        value = 1.0

    return value


def build_review_report(results: list[dict]) -> dict:
    scores = {}
    issues: list[str] = []
    checker_results = []
    for result in results:
        checker = str(result.get("checker", "unknown"))
        normalized_result = dict(result)
        normalized_score = _normalize_score(result.get("score"), checker)
        normalized_result["score"] = normalized_score
        checker_results.append(normalized_result)
        if normalized_score is not None:
            scores[checker] = normalized_score
        issues.extend(normalized_result.get("issues", []))
    return {
        "checker_results": checker_results,
        "scores": scores,
        "issues": issues,
    }
