import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = str(ROOT / "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from novelos.creation.structured_summary_engine import StructuredSummaryEngine


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text
        self.provider = "fake"
        self.model = "fake-model"
        self.usage = {}
        self.latency_ms = 0


class _FakeRuntime:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.calls = 0

    def run(self, task):  # noqa: ANN001
        output = self.outputs[min(self.calls, len(self.outputs) - 1)]
        self.calls += 1
        return _FakeResponse(output)


class StructuredSummaryEngineTest(unittest.TestCase):
    def test_retries_when_key_events_empty(self) -> None:
        runtime = _FakeRuntime(
            [
                json.dumps({"key_events": [], "main_plot_advanced": False}, ensure_ascii=False),
                json.dumps(
                    {"key_events": ["主线推进事件"], "main_plot_advanced": True},
                    ensure_ascii=False,
                ),
            ]
        )
        engine = StructuredSummaryEngine(runtime)

        result = engine.summarize("demo", 3, "chapter text")

        self.assertEqual(runtime.calls, 2)
        self.assertEqual(result["payload"]["key_events"], ["主线推进事件"])
        self.assertTrue(result["payload"]["main_plot_advanced"])

    def test_persists_empty_payload_after_retry(self) -> None:
        runtime = _FakeRuntime(
            [
                json.dumps({"key_events": [], "main_plot_advanced": False}, ensure_ascii=False),
                "not json",
            ]
        )
        engine = StructuredSummaryEngine(runtime)

        result = engine.summarize("demo", 4, "chapter text")

        self.assertEqual(runtime.calls, 2)
        self.assertEqual(result["payload"]["key_events"], [])
        self.assertFalse(result["payload"]["main_plot_advanced"])


if __name__ == "__main__":
    unittest.main()
