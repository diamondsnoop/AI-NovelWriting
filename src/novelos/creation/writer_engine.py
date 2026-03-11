from novelos.foundation.agent_runtime import AgentRuntime, AgentTask


class WriterEngine:
    def __init__(self, agent_runtime: AgentRuntime, max_chars: int = 1000) -> None:
        self.agent_runtime = agent_runtime
        self.max_chars = max_chars

    def draft(self, write_package: dict) -> dict:
        name_constraint = self._build_name_constraint(write_package.get("known_entities", []))
        task = AgentTask(
            role="writer",
            task_type="write_chapter",
            prompt=(
                "Write the next chapter draft from the provided package. "
                "Prioritize chapter outline, beat sheet, timeline, and volume plan when available. "
                f"Keep the draft concise and do not exceed {self.max_chars} Chinese characters. "
                f"{name_constraint}"
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

    def _build_name_constraint(self, known_entities: list[dict]) -> str:
        names = []
        for entity in known_entities:
            if entity.get("entity_type") != "character":
                continue
            name = str(entity.get("name", "")).strip()
            if not name or name in names:
                continue
            names.append(name)
        if not names:
            return ""
        limited = "、".join(names[:6])
        return f"本书已出现角色：{limited}（请严格使用这些名字，不要改变）"
