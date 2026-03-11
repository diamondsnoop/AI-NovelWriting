import json

from novelos.foundation.agent_runtime import AgentRuntime, AgentTask


class StructuredSummaryEngine:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime

    def summarize(self, project_title: str, chapter_no: int, chapter_text: str) -> dict:
        task = AgentTask(
            role="structured_summarizer",
            task_type="summarize_structured_chapter",
            prompt=(
                "Summarize the chapter into strict JSON with keys: key_events, main_plot_advanced. "
                "main_plot_advanced must be true or false."
            ),
            context={
                "project_title": project_title,
                "chapter_no": chapter_no,
                "chapter_text": chapter_text,
            },
            stream=False,
        )
        response = self.agent_runtime.run(task)
        try:
            payload = json.loads(response.text)
        except Exception:
            payload = {
                "key_events": [],
                "main_plot_advanced": False,
            }
        return {
            "payload": payload,
            "provider": response.provider,
            "model": response.model,
            "usage": response.usage,
            "latency_ms": response.latency_ms,
        }
