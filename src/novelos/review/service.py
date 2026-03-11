class ReviewService:
    def review_draft(self, draft: dict) -> dict:
        content = draft.get("content", "")
        return {
            "gate_result": "pass" if content else "blocked",
            "scores": {
                "consistency": 0.7,
                "continuity": 0.7,
                "character": 0.7,
            },
            "issues": [] if content else ["Draft content is empty."],
            "fix_suggestions": [] if content else ["Regenerate draft."],
        }
