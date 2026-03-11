from novelos.foundation.agent_runtime import AgentRuntime, AgentTask


class OutlineEngine:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime

    def build_chapter_outline(self, project_title: str, chapter_no: int) -> dict:
        full_task = AgentTask(
            role="planner",
            task_type="plan_chapter",
            prompt="Create a complete chapter outline for the specified chapter. Include purpose, scene beats, and ending hook.",
            context={
                "project_title": project_title,
                "chapter_no": chapter_no,
            },
            stream=False,
        )
        compact_task = AgentTask(
            role="planner",
            task_type="plan_chapter_compact",
            prompt=(
                "Create a compact writing outline for the specified chapter. "
                "Only include: chapter goal, 3-5 key beats, and ending hook. "
                "Keep the result within 500 Chinese characters."
            ),
            context={
                "project_title": project_title,
                "chapter_no": chapter_no,
            },
            stream=False,
        )
        full_response = self.agent_runtime.run(full_task)
        compact_response = self.agent_runtime.run(compact_task)
        return {
            "chapter_no": chapter_no,
            "content": full_response.text,
            "compact_content": compact_response.text,
            "provider": full_response.provider,
            "model": full_response.model,
            "usage": full_response.usage,
            "latency_ms": full_response.latency_ms,
            "compact_generation": {
                "provider": compact_response.provider,
                "model": compact_response.model,
                "usage": compact_response.usage,
                "latency_ms": compact_response.latency_ms,
            },
        }
