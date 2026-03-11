from pathlib import Path

from novelos.memory.summaries import load_recent_structured_summaries


class PacingChecker:
    def __init__(self, window_size: int = 3) -> None:
        self.window_size = window_size

    def run(self, project_root, chapter_no: int) -> dict:
        recent = load_recent_structured_summaries(Path(project_root), chapter_no, self.window_size)
        if len(recent) < self.window_size - 1:
            return {
                "checker": "pacing",
                "status": "skipped",
                "score": None,
                "issues": [],
                "message": "Not enough recent chapter summaries to evaluate pacing.",
                "severity": "info",
            }

        advances = [bool(item.get("main_plot_advanced")) for item in recent]
        if not any(advances):
            return {
                "checker": "pacing",
                "status": "completed",
                "score": 0.4,
                "issues": ["Main plot advancement density is low across recent chapters."],
                "message": "No recent chapter in the current window appears to advance the main plot.",
                "severity": "warning",
            }

        return {
            "checker": "pacing",
            "status": "completed",
            "score": 0.75,
            "issues": [],
            "message": "Recent chapters include main plot advancement.",
            "severity": "info",
        }
