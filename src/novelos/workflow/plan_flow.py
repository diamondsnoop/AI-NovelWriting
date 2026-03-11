from pathlib import Path

from novelos.creation.outline_engine import OutlineEngine
from novelos.foundation.agent_runtime import AgentRuntime
from novelos.foundation.io import write_text
from novelos.foundation.llm_client import LLMClient
from novelos.memory.store import build_project_paths, compact_outline_file, load_project_state, outline_file


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

    path = outline_file(paths, chapter_no)
    compact_path = compact_outline_file(paths, chapter_no)
    write_text(path, outline["content"])
    write_text(compact_path, outline["compact_content"])
    return {
        "chapter_no": chapter_no,
        "outline_path": str(path),
        "compact_outline_path": str(compact_path),
        "generation": {
            "provider": outline["provider"],
            "model": outline["model"],
            "usage": outline["usage"],
            "latency_ms": outline["latency_ms"],
        },
        "compact_generation": outline["compact_generation"],
    }
