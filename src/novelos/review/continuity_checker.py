import json

from novelos.foundation.agent_runtime import AgentRuntime, AgentTask


class ContinuityChecker:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime

    def run(self, draft_text: str, chapter_no: int, previous_summary: str, chapter_outline: str) -> dict:
        if chapter_no <= 1 or not previous_summary.strip():
            return {
                "checker": "continuity",
                "status": "skipped",
                "score": None,
                "issues": [],
                "message": "No previous chapter summary available.",
            }

        task = AgentTask(
            role="continuity_checker",
            task_type="review_continuity",
            prompt=(
                "Evaluate whether the draft continues naturally from the previous chapter summary. "
                "Return strict JSON with keys: score, issues, rationale. "
                "The score must be a decimal number between 0 and 1, where 1 means excellent continuity and 0 means severe continuity break. "
                "Do not use a percentage or a 0-100 scale."
            ),
            context={
                "chapter_no": chapter_no,
                "previous_summary": previous_summary,
                "chapter_outline": chapter_outline,
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
            issues = ["Continuity checker returned non-JSON output."]
            rationale = response.text

        return {
            "checker": "continuity",
            "status": "completed",
            "score": score,
            "issues": issues,
            "message": rationale,
        }
