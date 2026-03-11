def build_overwrite_question(chapter_path: str) -> dict:
    return {
        "decision_type": "overwrite_write",
        "question": f"Chapter file already exists: {chapter_path}",
        "options": [
            {
                "label": "overwrite",
                "description": "Replace the existing chapter file with the new draft.",
            },
            {
                "label": "abort",
                "description": "Stop the write flow and keep the existing chapter file.",
            },
        ],
    }
