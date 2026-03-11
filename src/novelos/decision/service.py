from pathlib import Path

from novelos.decision.policy import normalize_decision_mode, select_option
from novelos.decision.question_builder import build_semantic_question
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

    def resolve_semantic_triggers(
        self,
        *,
        project_root: Path,
        task_id: str,
        triggers: list[dict],
        mode: str | None = None,
    ) -> dict:
        if not triggers:
            return {
                "decision_required": False,
                "records": [],
                "triggers": [],
                "mode": normalize_decision_mode(mode),
            }

        resolved_mode = normalize_decision_mode(mode)
        records = []
        for trigger in triggers:
            question = build_semantic_question(trigger)
            selected_option = select_option(question, resolved_mode)
            record = save_decision_record(
                project_root=project_root,
                payload={
                    "task_id": task_id,
                    "decision_type": question["decision_type"],
                    "question": question["question"],
                    "options": question["options"],
                    "selected_option": selected_option,
                    "trigger_code": trigger.get("trigger_code"),
                    "source_module": trigger.get("source_module"),
                    "source_field": trigger.get("source_field"),
                    "trigger_payload": trigger.get("payload", {}),
                },
            )
            records.append(record)

        return {
            "decision_required": True,
            "records": records,
            "triggers": triggers,
            "mode": resolved_mode,
        }
