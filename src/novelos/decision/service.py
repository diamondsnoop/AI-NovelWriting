from pathlib import Path

from novelos.decision.question_builder import build_overwrite_question
from novelos.decision.store import save_decision_record


class DecisionService:
    def resolve_overwrite(self, project_root: Path, task_id: str, chapter_path: str, policy: str | None) -> dict:
        question = build_overwrite_question(chapter_path)
        selected_option = policy or "abort"
        if selected_option not in {"overwrite", "abort"}:
            raise ValueError(f"Unsupported conflict policy: {selected_option}")

        record = save_decision_record(
            project_root=project_root,
            payload={
                "task_id": task_id,
                "decision_type": question["decision_type"],
                "question": question["question"],
                "options": question["options"],
                "selected_option": selected_option,
            },
        )
        return {
            "decision_required": True,
            "selected_option": selected_option,
            "record": record,
            "question": question,
        }
