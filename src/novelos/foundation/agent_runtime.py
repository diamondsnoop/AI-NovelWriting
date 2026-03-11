from dataclasses import dataclass

from novelos.foundation.llm_client import LLMClient, LLMRequest, LLMResponse


@dataclass(slots=True)
class AgentTask:
    role: str
    task_type: str
    prompt: str
    context: dict
    stream: bool = False


class AgentRuntime:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def run(self, task: AgentTask) -> LLMResponse:
        request = LLMRequest(
            task_type=task.task_type,
            prompt=task.prompt,
            context=task.context,
            stream=task.stream,
        )
        return self.llm_client.generate(request)
