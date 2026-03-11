import json

from novelos.foundation.agent_runtime import AgentRuntime, AgentTask


class ConsistencyChecker:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime

    def run(self, draft_text: str, chapter_no: int, known_entities: list[dict]) -> dict:
        if not known_entities:
            return {
                "checker": "consistency",
                "status": "skipped",
                "score": None,
                "severity": "info",
                "issues": [],
                "message": "No historical entity data available.",
                "signals": {"codes": [], "metrics": {"issue_count": 0}},
            }

        task = AgentTask(
            role="consistency_checker",
            task_type="review_consistency",
            prompt=(
                "Check whether the draft contradicts the known historical entity records. "
                "Return strict JSON with keys: score, issues, rationale. "
                "The score must be a decimal number between 0 and 1, where 1 means fully consistent and 0 means severe contradiction. "
                "Do not use a percentage or a 0-100 scale."
            ),
            context={
                "chapter_no": chapter_no,
                "known_entities": known_entities,
                "draft_text": draft_text,
            },
            stream=False,
        )
        response = self.agent_runtime.run(task)
        try:
            payload = json.loads(response.text)
            score = float(payload.get("score", 0.0))
            issues = payload.get("issues", [])
            rationale = payload.get("rationale", "")
        except Exception:
            score = 0.5
            issues = ["Consistency checker returned non-JSON output."]
            rationale = response.text

        if not isinstance(issues, list):
            issues = [str(issues)]
        issues = [str(item).strip() for item in issues if str(item).strip()]
        severity = _score_to_severity(score)
        issue_text = " ".join(issues).lower()
        codes = []
        if score < 0.5 or "conflict" in issue_text or "冲突" in issue_text or "矛盾" in issue_text:
            codes.append("consistency_conflict")
        else:
            codes.append("consistency_ok")

        return {
            "checker": "consistency",
            "status": "completed",
            "score": score,
            "severity": severity,
            "issues": issues,
            "message": rationale,
            "signals": {
                "codes": codes,
                "metrics": {"issue_count": len(issues)},
            },
        }


def _score_to_severity(score: float) -> str:
    if score < 0.35:
        return "critical"
    if score < 0.6:
        return "warning"
    return "info"
