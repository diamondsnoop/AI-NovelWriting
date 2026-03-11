import json

from novelos.foundation.agent_runtime import AgentRuntime, AgentTask
from novelos.foundation.logging import get_logger


class StructuredSummaryEngine:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime
        self.logger = get_logger("novelos.structured_summary")

    def summarize(self, project_title: str, chapter_no: int, chapter_text: str) -> dict:
        response = None
        payload = None
        for attempt in (1, 2):
            task = AgentTask(
                role="structured_summarizer",
                task_type="summarize_structured_chapter",
                prompt=(
                    "Summarize the chapter into strict JSON with keys: "
                    "key_events, main_plot_advanced, high_point_markers, reader_pull_marker. "
                    "key_events must be an array of concise event strings, not empty when the chapter contains visible plot movement. "
                    "main_plot_advanced must be true or false. "
                    "high_point_markers must be an array of short strings that mark strong plot/high-point moments (can be empty). "
                    "reader_pull_marker must be an object with keys: has_pull (bool), pull_type (string), evidence (string). "
                    "Only output valid JSON with no extra text."
                ),
                context={
                    "project_title": project_title,
                    "chapter_no": chapter_no,
                    "chapter_text": chapter_text,
                },
                stream=False,
            )
            response = self.agent_runtime.run(task)
            payload = self._parse_payload(response.text)
            if payload.get("key_events"):
                break
            if attempt == 1:
                self.logger.warning(
                    "structured_summary_empty_key_events_retry chapter=%s raw_output=%r",
                    chapter_no,
                    response.text[:2000],
                )

        if payload is None:
            payload = self._default_payload()
        if not payload.get("key_events"):
            self.logger.warning(
                "structured_summary_empty_key_events_persisted chapter=%s raw_output=%r",
                chapter_no,
                "" if response is None else response.text[:2000],
            )

        return {
            "payload": payload,
            "provider": None if response is None else response.provider,
            "model": None if response is None else response.model,
            "usage": {} if response is None else response.usage,
            "latency_ms": 0 if response is None else response.latency_ms,
        }

    def _parse_payload(self, raw_text: str) -> dict:
        try:
            payload = json.loads(raw_text)
        except Exception:
            return self._default_payload()

        key_events = payload.get("key_events")
        if not isinstance(key_events, list):
            key_events = []
        key_events = [str(item).strip() for item in key_events if str(item).strip()]
        high_point_markers = payload.get("high_point_markers")
        if not isinstance(high_point_markers, list):
            high_point_markers = []
        high_point_markers = [str(item).strip() for item in high_point_markers if str(item).strip()]
        reader_pull_marker = payload.get("reader_pull_marker")
        if not isinstance(reader_pull_marker, dict):
            reader_pull_marker = {}

        return {
            "key_events": key_events,
            "main_plot_advanced": bool(payload.get("main_plot_advanced", False)),
            "high_point_markers": high_point_markers,
            "reader_pull_marker": {
                "has_pull": bool(reader_pull_marker.get("has_pull", False)),
                "pull_type": str(reader_pull_marker.get("pull_type", "")).strip(),
                "evidence": str(reader_pull_marker.get("evidence", "")).strip(),
            },
        }

    def _default_payload(self) -> dict:
        return {
            "key_events": [],
            "main_plot_advanced": False,
            "high_point_markers": [],
            "reader_pull_marker": {
                "has_pull": False,
                "pull_type": "",
                "evidence": "",
            },
        }
