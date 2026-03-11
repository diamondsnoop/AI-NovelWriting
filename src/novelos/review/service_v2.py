from novelos.foundation.agent_runtime import AgentRuntime
from novelos.review.consistency_checker import ConsistencyChecker
from novelos.review.character_checker import CharacterChecker
from novelos.review.continuity_checker import ContinuityChecker
from novelos.review.foreshadowing_checker import ForeshadowingChecker
from novelos.review.gatekeeper import gate_review
from novelos.review.high_point_checker import HighPointChecker
from novelos.review.pacing_checker import PacingChecker
from novelos.review.reader_pull_checker import ReaderPullChecker
from novelos.review.report_builder import build_review_report


class ReviewService:
    def __init__(self, agent_runtime: AgentRuntime) -> None:
        self.agent_runtime = agent_runtime

    def review_draft(
        self,
        draft: dict,
        write_package: dict,
        new_foreshadowing: list[dict] | None = None,
        structured_summary: dict | None = None,
    ) -> dict:
        content = draft.get("content", "")
        if not content:
            return {
                "checker_results": [],
                "scores": {},
                "issues": ["Draft content is empty."],
                "gate_result": "blocked",
                "reason": "empty_draft",
                "inactive_checkers": self._inactive_checkers(),
                "fix_suggestions": ["Regenerate draft."],
            }

        results = [
            ConsistencyChecker(self.agent_runtime).run(
                draft_text=content,
                chapter_no=write_package.get("chapter_no", 0),
                known_entities=write_package.get("known_entities", []),
            ),
            CharacterChecker(self.agent_runtime).run(
                draft_text=content,
                chapter_no=write_package.get("chapter_no", 0),
                known_character_profiles=write_package.get("known_character_profiles", []),
            ),
            ContinuityChecker(self.agent_runtime).run(
                draft_text=content,
                chapter_no=write_package.get("chapter_no", 0),
                previous_summary=write_package.get("previous_summary", ""),
                chapter_outline=write_package.get("chapter_outline", ""),
            ),
            PacingChecker(window_size=3).run(
                project_root=write_package.get("project_root"),
                chapter_no=write_package.get("chapter_no", 0),
            ),
            ForeshadowingChecker().run(
                project_root=write_package.get("project_root"),
                chapter_no=write_package.get("chapter_no", 0),
                draft_text=content,
                new_items=new_foreshadowing,
            ),
            HighPointChecker().run(
                draft_text=content,
                chapter_no=write_package.get("chapter_no", 0),
                chapter_beats=write_package.get("chapter_beats", ""),
                chapter_timeline=write_package.get("chapter_timeline", ""),
                structured_summary=structured_summary,
            ),
            ReaderPullChecker().run(
                draft_text=content,
                chapter_no=write_package.get("chapter_no", 0),
                chapter_outline=write_package.get("chapter_outline", ""),
                chapter_beats=write_package.get("chapter_beats", ""),
                structured_summary=structured_summary,
            ),
        ]
        report = build_review_report(results)
        gate = gate_review(report)
        return {
            **report,
            **gate,
            "inactive_checkers": self._inactive_checkers(),
            "fix_suggestions": [] if gate["gate_result"] == "pass" else ["Revise continuity before saving."],
        }

    def _inactive_checkers(self) -> list[dict]:
        return []
