from novelos.memory.store import ProjectPaths, save_task_state


class StateTracker:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths

    def mark_step(self, task_state: dict, step_name: str) -> dict:
        task_state["current_step"] = step_name
        if step_name not in task_state["completed_steps"]:
            task_state["completed_steps"].append(step_name)
        save_task_state(self.paths, task_state)
        return task_state

    def mark_failed(self, task_state: dict, step_name: str) -> dict:
        task_state["current_step"] = step_name
        if step_name not in task_state["failed_steps"]:
            task_state["failed_steps"].append(step_name)
        task_state["task_status"] = "failed"
        save_task_state(self.paths, task_state)
        return task_state

    def mark_done(self, task_state: dict) -> dict:
        task_state["task_status"] = "completed"
        save_task_state(self.paths, task_state)
        return task_state
