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
                "issues": [],
                "message": "No historical character profiles available.",
            }

        task = AgentTask(
            role="character_checker",
            task_type="review_character",
            prompt=(
                "Check whether character behavior in the draft clearly deviates from the known character profiles. "
                "Return strict JSON with keys: score, issues, rationale."
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
            "issues": issues,
            "message": rationale,
        }
