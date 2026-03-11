from pathlib import Path

from novelos.creation.outline_engine import OutlineEngine
from novelos.foundation.agent_runtime import AgentRuntime
from novelos.foundation.io import write_text
from novelos.foundation.llm_client import LLMClient
from novelos.memory.store import (
    beat_sheet_file,
    build_project_paths,
    compact_outline_file,
    load_project_state,
    outline_file,
    timeline_file,
    volume_plan_file,
)


def run_plan(
    project_root: Path,
    chapter_no: int,
    provider: str,
    model_name: str,
    base_url: str | None,
    api_mode: str,
    timeout_seconds: float,
    max_retries: int,
) -> dict:
    paths = build_project_paths(project_root)
    project_state = load_project_state(paths)
    project_title = project_state.get("project", {}).get("title", "Untitled Project")
    volume_no = _infer_volume_no(project_state=project_state, chapter_no=chapter_no)

    llm_client = LLMClient(
        provider=provider,
        model_name=model_name,
        base_url=base_url,
        api_mode=api_mode,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )
    agent_runtime = AgentRuntime(llm_client=llm_client)
    outline_engine = OutlineEngine(agent_runtime=agent_runtime)
    outline = outline_engine.build_chapter_outline(project_title=project_title, chapter_no=chapter_no)
    volume_plan = outline_engine.build_volume_plan(
        project_title=project_title,
        volume_no=volume_no,
        chapter_no=chapter_no,
    )
    beat_sheet = outline_engine.build_chapter_beats(project_title=project_title, chapter_no=chapter_no)
    timeline = outline_engine.build_chapter_timeline(project_title=project_title, chapter_no=chapter_no)

    path = outline_file(paths, chapter_no)
    compact_path = compact_outline_file(paths, chapter_no)
    volume_path = volume_plan_file(paths, volume_no)
    beats_path = beat_sheet_file(paths, chapter_no)
    timeline_path = timeline_file(paths, chapter_no)
    write_text(path, outline["content"])
    write_text(compact_path, outline["compact_content"])
    write_text(volume_path, volume_plan["content"])
    write_text(beats_path, beat_sheet["content"])
    write_text(timeline_path, timeline["content"])
    return {
        "chapter_no": chapter_no,
        "volume_no": volume_no,
        "outline_path": str(path),
        "compact_outline_path": str(compact_path),
        "volume_plan_path": str(volume_path),
        "beat_sheet_path": str(beats_path),
        "timeline_path": str(timeline_path),
        "generation": {
            "provider": outline["provider"],
            "model": outline["model"],
            "usage": outline["usage"],
            "latency_ms": outline["latency_ms"],
        },
        "compact_generation": outline["compact_generation"],
        "volume_plan_generation": volume_plan["generation"],
        "beat_sheet_generation": beat_sheet["generation"],
        "timeline_generation": timeline["generation"],
    }


def _infer_volume_no(project_state: dict, chapter_no: int) -> int:
    project = project_state.get("project", {})
    progress = project_state.get("project_state", {}).get("progress", {})
    active_volume = project.get("active_volume") or progress.get("current_volume")
    try:
        volume_no = int(active_volume)
        if volume_no > 0:
            return volume_no
    except (TypeError, ValueError):
        pass
    # Fallback when volume is unknown.
    return ((chapter_no - 1) // 100) + 1
