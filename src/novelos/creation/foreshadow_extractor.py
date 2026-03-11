import json

from novelos.foundation.agent_runtime import AgentRuntime, AgentTask
from novelos.foundation.logging import get_logger


class ForeshadowExtractor:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime
        self.logger = get_logger("novelos.foreshadowing")

    def extract(self, project_title: str, chapter_no: int, chapter_text: str) -> list[dict]:
        task = AgentTask(
            role="foreshadow_extractor",
            task_type="extract_foreshadowing",
            prompt=(
                "Extract newly planted foreshadowing items from the chapter. "
                "Only keep genuinely new foreshadowing that is first planted in this chapter. "
                "Do not split one event into multiple foreshadowing items. "
                "Do not repeat or restate existing foreshadowing. "
                "Return at most 5 foreshadowing items. "
                "Only output JSON with no extra text. "
                'Use this schema exactly: {"foreshadowing": [{"setup": "...", "hint": "...", "expected_payoff": "..."}]}.'
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
                "foreshadowing_parse_failed chapter=%s raw_output=%r",
                chapter_no,
                response.text[:2000],
            )
            return []

        items = []
        for item in payload.get("foreshadowing", []):
            if not isinstance(item, dict):
                continue
            setup = str(item.get("setup", "")).strip()
            hint = str(item.get("hint", "")).strip()
            expected_payoff = str(item.get("expected_payoff", "")).strip()
            if not setup and not hint:
                continue
            items.append(
                {
                    "setup": setup,
                    "hint": hint,
                    "expected_payoff": expected_payoff,
                    "source": "chapter_plant",
                }
            )
        return items
