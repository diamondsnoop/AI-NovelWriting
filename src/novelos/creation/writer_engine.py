from novelos.foundation.agent_runtime import AgentRuntime, AgentTask


class WriterEngine:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime

    def draft(self, write_package: dict) -> dict:
        task = AgentTask(
            role="writer",
            task_type="write_chapter",
            prompt=(
                "Write the next chapter draft from the provided package. "
                "Keep the draft concise and do not exceed 1000 Chinese characters."
            ),
            context=write_package,
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
