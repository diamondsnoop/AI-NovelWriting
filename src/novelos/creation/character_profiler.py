from novelos.foundation.agent_runtime import AgentRuntime, AgentTask


class CharacterProfiler:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime

    def summarize(self, project_title: str, chapter_no: int, character_name: str, chapter_text: str) -> str:
        task = AgentTask(
            role="character_profiler",
            task_type="summarize_character_profile",
            prompt="Summarize the character's apparent behavior style and core impression in one short sentence.",
            context={
                "project_title": project_title,
                "chapter_no": chapter_no,
                "character_name": character_name,
                "chapter_text": chapter_text,
            },
            stream=False,
        )
        response = self.agent_runtime.run(task)
        return response.text.strip()
