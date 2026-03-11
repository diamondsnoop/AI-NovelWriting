from novelos.foundation.io import read_text
from novelos.memory.entities import list_entities
from novelos.memory.store import (
    ProjectPaths,
    beat_sheet_file,
    compact_outline_file,
    outline_file,
    summary_file,
    timeline_file,
    volume_plan_file,
)
from novelos.retrieval.query_router import route_retrieval
from novelos.retrieval.search_engine import search_relevant_snippets
from novelos.workflow.character_profiles import build_character_profiles


def build_write_package(project_state: dict, chapter_no: int, paths: ProjectPaths) -> dict:
    project = project_state.get("project", {})
    state = project_state.get("project_state", {})
    volume_no = _infer_volume_no(project_state=project_state, chapter_no=chapter_no)
    chapter_outline = read_text(compact_outline_file(paths, chapter_no), default="")
    if not chapter_outline:
        chapter_outline = read_text(outline_file(paths, chapter_no), default="")
    chapter_beats = read_text(beat_sheet_file(paths, chapter_no), default="")
    chapter_timeline = read_text(timeline_file(paths, chapter_no), default="")
    volume_plan = read_text(volume_plan_file(paths, volume_no), default="")
    known_entities = [
        entity for entity in list_entities(paths.root) if entity.get("chapter_no", 0) < chapter_no
    ]
    known_character_profiles = build_character_profiles(known_entities)
    previous_summary = ""
    if chapter_no > 1:
        previous_summary = read_text(summary_file(paths, chapter_no - 1), default="")
    retrieval_route = route_retrieval(
        intent="write_context",
        chapter_outline="\n\n".join(part for part in [chapter_outline, chapter_beats, chapter_timeline] if part.strip()),
        previous_summary=previous_summary,
    )
    route_branch_candidates = _extract_route_branch_candidates(
        chapter_outline=chapter_outline,
        chapter_beats=chapter_beats,
        chapter_timeline=chapter_timeline,
    )
    retrieved_context = search_relevant_snippets(
        paths=paths,
        chapter_no=chapter_no,
        query_text=retrieval_route["query_text"],
        limit=retrieval_route["limit"],
        strategy=retrieval_route,
    )
    return {
        "project_root": str(paths.root),
        "project_title": project.get("title", "Untitled Project"),
        "chapter_no": chapter_no,
        "volume_no": volume_no,
        "summary_hint": (
            f"Current progress: after chapter {state.get('progress', {}).get('current_chapter', 0)}. "
            "Generate the next chapter draft from the available outline and project state."
        ),
        "chapter_outline": chapter_outline,
        "chapter_beats": chapter_beats,
        "chapter_timeline": chapter_timeline,
        "volume_plan": volume_plan,
        "route_branch_candidates": route_branch_candidates,
        "known_entities": known_entities,
        "known_character_profiles": known_character_profiles,
        "previous_summary": previous_summary,
        "retrieval_route": retrieval_route,
        "retrieved_context": retrieved_context,
        "project_state": state,
    }


def _build_character_profiles(known_entities: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for entity in known_entities:
        if entity.get("entity_type") != "character":
            continue
        name = str(entity.get("name", "")).strip()
        summary = str(entity.get("character_profile_summary", "")).strip()
        if not name or not summary:
            continue
        bucket = grouped.setdefault(
            name,
            {
                "name": name,
                "evidence_count": 0,
                "chapters": [],
                "character_profile_summary": "",
            },
        )
        bucket["evidence_count"] += 1
        bucket["chapters"].append(entity.get("chapter_no"))
        if bucket["character_profile_summary"]:
            bucket["character_profile_summary"] += "\n"
        bucket["character_profile_summary"] += f"- 第{entity.get('chapter_no')}章：{summary}"

    profiles = list(grouped.values())
    profiles.sort(key=lambda item: (-item["evidence_count"], item["name"]))
    return profiles


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
    return ((chapter_no - 1) // 100) + 1


def _extract_route_branch_candidates(chapter_outline: str, chapter_beats: str, chapter_timeline: str) -> list[str]:
    keywords = [
        "路线",
        "分支",
        "二选一",
        "抉择",
        "方案a",
        "方案b",
        "a/b",
        "route",
        "branch",
        "option",
    ]
    text = "\n".join([chapter_outline, chapter_beats, chapter_timeline]).strip()
    if not text:
        return []

    candidates: list[str] = []
    for line in text.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        lowered = normalized.lower()
        if any(keyword in lowered for keyword in keywords):
            candidates.append(normalized)

    # Deduplicate while preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        deduped.append(candidate)
    return deduped
