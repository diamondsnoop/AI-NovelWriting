from novelos.foundation.agent_runtime import AgentRuntime, AgentTask


class SummaryEngine:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime

    def summarize_chapter(self, project_title: str, chapter_no: int, chapter_text: str) -> dict:
        task = AgentTask(
            role="summarizer",
            task_type="summarize_chapter",
            prompt="Summarize the chapter into a concise continuity-focused summary.",
            context={
                "project_title": project_title,
                "chapter_no": chapter_no,
                "chapter_text": chapter_text,
            },
            stream=False,
        )
        response = self.agent_runtime.run(task)
        return {
            "content": response.text,
            "provider": response.provider,
            "model": response.model,
            "usage": response.usage,
            "latency_ms": response.latency_ms,
        }
