from novelos.foundation.agent_runtime import AgentRuntime, AgentTask


class EntityExtractor:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime

    def extract(self, project_title: str, chapter_no: int, chapter_text: str) -> list[dict]:
        # First-pass extractor: keep the output deterministic and minimal.
        task = AgentTask(
            role="entity_extractor",
            task_type="extract_entities",
            prompt="Extract named characters and locations from the chapter.",
            context={
                "project_title": project_title,
                "chapter_no": chapter_no,
                "chapter_text": chapter_text,
            },
            stream=False,
        )
        response = self.agent_runtime.run(task)
        entities = []
        for line in response.text.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            entity_type, name = line.split(":", 1)
            entity_type = entity_type.strip().lower()
            name = name.strip()
            if entity_type in {"character", "location"} and name:
                entities.append(
                    {
                        "entity_type": entity_type,
                        "name": name,
                        "source": "chapter_presence",
                        "character_profile_summary": None,
                    }
                )
        return entities
