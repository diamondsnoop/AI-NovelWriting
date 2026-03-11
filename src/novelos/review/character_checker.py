import json

from novelos.foundation.agent_runtime import AgentRuntime, AgentTask


class CharacterChecker:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime

    def run(self, draft_text: str, chapter_no: int, known_character_profiles: list[dict]) -> dict:
        if not known_character_profiles:
            return {
                "checker": "character",
                "status": "skipped",
                "score": None,
                "severity": "info",
                "issues": [],
                "message": "No historical character profiles available.",
                "signals": {"codes": [], "metrics": {"issue_count": 0}},
            }

        task = AgentTask(
            role="character_checker",
            task_type="review_character",
            prompt=(
                "Check whether character behavior in the draft clearly deviates from the known character profiles. "
                "Treat profiles with evidence_count=1 as weak signals and avoid hard deviation claims unless the conflict is obvious. "
                "Prefer stronger judgments only when repeated prior evidence exists. "
                "Return strict JSON with keys: score, issues, rationale. "
                "The score must be a decimal number between 0 and 1, where 1 means strongly in-character and 0 means severe out-of-character behavior. "
                "Do not use a percentage or a 0-100 scale."
            ),
            context={
                "chapter_no": chapter_no,
                "known_character_profiles": known_character_profiles,
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
            issues = ["Character checker returned non-JSON output."]
            rationale = response.text

        return {
            "checker": "character",
            "status": "completed",
            "score": score,
            "severity": _score_to_severity(score),
            "issues": issues,
            "message": rationale,
            "signals": {
                "codes": ["character_ooc"] if score < 0.5 else ["character_ok"],
                "metrics": {"issue_count": len(issues)},
            },
        }


def _score_to_severity(score: float) -> str:
    if score < 0.35:
        return "critical"
    if score < 0.6:
        return "warning"
    return "info"
