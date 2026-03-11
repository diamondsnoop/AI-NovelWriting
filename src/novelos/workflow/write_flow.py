from pathlib import Path

from novelos.creation.character_profiler import CharacterProfiler
from novelos.creation.entity_extractor import EntityExtractor
from novelos.creation.foreshadow_extractor import ForeshadowExtractor
from novelos.creation.summary_engine import SummaryEngine
from novelos.creation.structured_summary_engine import StructuredSummaryEngine
from novelos.creation.writer_engine import WriterEngine
from novelos.decision.service import DecisionService
from novelos.foundation.agent_runtime import AgentRuntime
from novelos.foundation.io import write_text
from novelos.foundation.llm_client import LLMClient
from novelos.memory.store import (
    build_project_paths,
    create_task_state,
    load_project_state,
    save_project_state,
    save_task_state,
    summary_file,
    write_snapshot,
)
from novelos.memory.entities import save_entities
from novelos.memory.foreshadowing import save_foreshadowing
from novelos.memory.summaries import save_structured_summary
from novelos.review.service_v2 import ReviewService
from novelos.workflow.context_package import build_write_package
from novelos.workflow.state_tracker import StateTracker


def run_write(
    project_root: Path,
    chapter_no: int,
    provider: str,
    model_name: str,
    base_url: str | None,
    api_mode: str,
    write_timeout_seconds: float,
    write_max_retries: int,
    review_timeout_seconds: float,
    summary_timeout_seconds: float,
    extraction_timeout_seconds: float,
    character_profile_timeout_seconds: float,
    write_target_chars: int,
    max_retries: int,
    on_conflict: str | None,
) -> dict:
    paths = build_project_paths(project_root)
    project_state = load_project_state(paths)
    project_title = project_state.get("project", {}).get("title", "Untitled Project")
    task_state = create_task_state(paths, "write")
    tracker = StateTracker(paths)
    chapter_path = paths.chapters_dir / f"chapter_{chapter_no:04d}.md"

    if chapter_path.exists():
        decision = DecisionService().resolve_overwrite(
            project_root=project_root,
            task_id=task_state["task_id"],
            chapter_path=str(chapter_path),
            policy=on_conflict,
        )
        tracker.mark_step(task_state, "overwrite_decided")
        if decision["selected_option"] == "abort":
            tracker.mark_done(task_state)
            return {
                "task_id": task_state["task_id"],
                "status": "aborted",
                "reason": "chapter_exists",
                "decision": decision["record"],
            }

    tracker.mark_step(task_state, "package_built")
    write_package = build_write_package(project_state, chapter_no, paths)
    snapshot_id = write_snapshot(paths, task_state["task_id"], "package_built", write_package)
    task_state["snapshot_ids"].append(snapshot_id)
    save_task_state(paths, task_state)

    writer_runtime = _build_runtime(
        provider=provider,
        model_name=model_name,
        base_url=base_url,
        api_mode=api_mode,
        timeout_seconds=write_timeout_seconds,
        max_retries=write_max_retries,
    )
    writer_engine = WriterEngine(agent_runtime=writer_runtime, max_chars=write_target_chars)
    draft = writer_engine.draft(write_package)

    tracker.mark_step(task_state, "draft_generated")
    write_text(chapter_path, draft["content"])
    snapshot_id = write_snapshot(paths, task_state["task_id"], "draft_generated", {"chapter_path": str(chapter_path)})
    task_state["snapshot_ids"].append(snapshot_id)
    save_task_state(paths, task_state)

    review_runtime = _build_runtime(
        provider=provider,
        model_name=model_name,
        base_url=base_url,
        api_mode=api_mode,
        timeout_seconds=review_timeout_seconds,
        max_retries=max_retries,
    )
    summary_runtime = _build_runtime(
        provider=provider,
        model_name=model_name,
        base_url=base_url,
        api_mode=api_mode,
        timeout_seconds=summary_timeout_seconds,
        max_retries=max_retries,
    )
    structured_summary = StructuredSummaryEngine(agent_runtime=summary_runtime).summarize(
        project_title=project_title,
        chapter_no=chapter_no,
        chapter_text=draft["content"],
    )
    extraction_runtime = _build_runtime(
        provider=provider,
        model_name=model_name,
        base_url=base_url,
        api_mode=api_mode,
        timeout_seconds=extraction_timeout_seconds,
        max_retries=max_retries,
    )
    foreshadowing_items = ForeshadowExtractor(agent_runtime=extraction_runtime).extract(
        project_title=project_title,
        chapter_no=chapter_no,
        chapter_text=draft["content"],
    )
    review_result = ReviewService(agent_runtime=review_runtime).review_draft(
        draft=draft,
        write_package=write_package,
        new_foreshadowing=foreshadowing_items,
        structured_summary=structured_summary["payload"],
    )
    tracker.mark_step(task_state, "reviewed")
    if review_result["gate_result"] == "blocked":
        tracker.mark_failed(task_state, "review_blocked")
        return {
            "task_id": task_state["task_id"],
            "chapter_path": str(chapter_path),
            "review": review_result,
            "generation": {
                "provider": draft["provider"],
                "model": draft["model"],
                "usage": draft["usage"],
                "latency_ms": draft["latency_ms"],
            },
            "structured_summary_generation": {
                "provider": structured_summary["provider"],
                "model": structured_summary["model"],
                "usage": structured_summary["usage"],
                "latency_ms": structured_summary["latency_ms"],
            },
        }

    state = project_state
    state.setdefault("project", {})
    state.setdefault("project_state", {})
    state["project"]["active_chapter"] = chapter_no
    state["project"]["status"] = "draft_available"
    progress = state["project_state"].setdefault("progress", {})
    progress["current_chapter"] = chapter_no
    progress["completed_chapters"] = max(progress.get("completed_chapters", 0), chapter_no)
    save_project_state(paths, state)

    summary = SummaryEngine(agent_runtime=summary_runtime).summarize_chapter(
        project_title=project_title,
        chapter_no=chapter_no,
        chapter_text=draft["content"],
    )
    write_text(summary_file(paths, chapter_no), summary["content"])
    save_structured_summary(project_root=project_root, chapter_no=chapter_no, payload=structured_summary["payload"])

    entities = EntityExtractor(agent_runtime=extraction_runtime).extract(
        project_title=project_title,
        chapter_no=chapter_no,
        chapter_text=draft["content"],
    )
    profile_runtime = _build_runtime(
        provider=provider,
        model_name=model_name,
        base_url=base_url,
        api_mode=api_mode,
        timeout_seconds=character_profile_timeout_seconds,
        max_retries=max_retries,
    )
    profiler = CharacterProfiler(agent_runtime=profile_runtime)
    for entity in entities:
        if entity.get("entity_type") == "character":
            entity["character_profile_summary"] = profiler.summarize(
                project_title=project_title,
                chapter_no=chapter_no,
                character_name=entity.get("name", "Unknown"),
                chapter_text=draft["content"],
            )
    stored_entities = save_entities(project_root=project_root, chapter_no=chapter_no, entities=entities)
    stored_foreshadowing = save_foreshadowing(
        project_root=project_root,
        chapter_no=chapter_no,
        items=foreshadowing_items,
    )

    tracker.mark_done(task_state)
    return {
        "task_id": task_state["task_id"],
        "chapter_path": str(chapter_path),
        "review": review_result,
        "generation": {
            "provider": draft["provider"],
            "model": draft["model"],
            "usage": draft["usage"],
            "latency_ms": draft["latency_ms"],
        },
        "summary_generation": {
            "provider": summary["provider"],
            "model": summary["model"],
            "usage": summary["usage"],
            "latency_ms": summary["latency_ms"],
        },
        "structured_summary_generation": {
            "provider": structured_summary["provider"],
            "model": structured_summary["model"],
            "usage": structured_summary["usage"],
            "latency_ms": structured_summary["latency_ms"],
        },
        "entities": stored_entities,
        "foreshadowing": stored_foreshadowing,
    }


def _build_runtime(
    provider: str,
    model_name: str,
    base_url: str | None,
    api_mode: str,
    timeout_seconds: float,
    max_retries: int,
) -> AgentRuntime:
    llm_client = LLMClient(
        provider=provider,
        model_name=model_name,
        base_url=base_url,
        api_mode=api_mode,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )
    return AgentRuntime(llm_client=llm_client)
