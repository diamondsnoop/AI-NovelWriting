from novelos.foundation.io import read_text
from novelos.memory.entities import list_entities
from novelos.memory.store import ProjectPaths, compact_outline_file, outline_file, summary_file
from novelos.retrieval.search_engine import search_relevant_snippets
from novelos.workflow.character_profiles import build_character_profiles


def build_write_package(project_state: dict, chapter_no: int, paths: ProjectPaths) -> dict:
    project = project_state.get("project", {})
    state = project_state.get("project_state", {})
    chapter_outline = read_text(compact_outline_file(paths, chapter_no), default="")
    if not chapter_outline:
        chapter_outline = read_text(outline_file(paths, chapter_no), default="")
    known_entities = [
        entity for entity in list_entities(paths.root) if entity.get("chapter_no", 0) < chapter_no
    ]
    known_character_profiles = build_character_profiles(known_entities)
    previous_summary = ""
    if chapter_no > 1:
        previous_summary = read_text(summary_file(paths, chapter_no - 1), default="")
    retrieval_query = f"{chapter_outline}\n\n{previous_summary}".strip()
    retrieved_context = search_relevant_snippets(paths=paths, chapter_no=chapter_no, query_text=retrieval_query, limit=2)
    return {
        "project_root": str(paths.root),
        "project_title": project.get("title", "Untitled Project"),
        "chapter_no": chapter_no,
        "summary_hint": (
            f"Current progress: after chapter {state.get('progress', {}).get('current_chapter', 0)}. "
            "Generate the next chapter draft from the available outline and project state."
        ),
        "chapter_outline": chapter_outline,
        "known_entities": known_entities,
        "known_character_profiles": known_character_profiles,
        "previous_summary": previous_summary,
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
