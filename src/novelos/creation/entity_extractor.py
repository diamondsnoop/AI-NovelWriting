import json

from novelos.foundation.agent_runtime import AgentRuntime, AgentTask
from novelos.foundation.logging import get_logger


class EntityExtractor:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime
        self.logger = get_logger("novelos.entities")

    def extract(self, project_title: str, chapter_no: int, chapter_text: str) -> list[dict]:
        task = AgentTask(
            role="entity_extractor",
            task_type="extract_entities",
            prompt=(
                "Extract named characters and locations from the chapter. "
                "Only output JSON, with no extra text. "
                'Use this schema exactly: {"characters": ["名字1"], "locations": ["地点1"]}.'
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
            self.logger.warning(
                "entity_extraction_parse_failed chapter=%s raw_output=%r",
                chapter_no,
                response.text[:2000],
            )
            return []

        entities = []
        for name in payload.get("characters", []):
            if isinstance(name, str) and name.strip():
                entities.append(
                    {
                        "entity_type": "character",
                        "name": name.strip(),
                        "source": "chapter_presence",
                        "character_profile_summary": None,
                    }
                )
        for name in payload.get("locations", []):
            if isinstance(name, str) and name.strip():
                entities.append(
                    {
                        "entity_type": "location",
                        "name": name.strip(),
                        "source": "chapter_presence",
                        "character_profile_summary": None,
                    }
                )
        return entities
