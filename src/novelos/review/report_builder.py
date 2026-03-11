def build_review_report(results: list[dict]) -> dict:
    scores = {}
    issues: list[str] = []
    checker_results = []
    for result in results:
        checker_results.append(result)
        if result.get("score") is not None:
            scores[result["checker"]] = result["score"]
        issues.extend(result.get("issues", []))
    return {
        "checker_results": checker_results,
        "scores": scores,
        "issues": issues,
    }
