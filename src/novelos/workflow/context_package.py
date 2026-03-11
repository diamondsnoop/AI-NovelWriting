from novelos.foundation.io import read_text
from novelos.memory.entities import list_entities
from novelos.memory.store import ProjectPaths, compact_outline_file, outline_file, summary_file


def build_write_package(project_state: dict, chapter_no: int, paths: ProjectPaths) -> dict:
    project = project_state.get("project", {})
    state = project_state.get("project_state", {})
    chapter_outline = read_text(compact_outline_file(paths, chapter_no), default="")
    if not chapter_outline:
        chapter_outline = read_text(outline_file(paths, chapter_no), default="")
    known_entities = [
        entity for entity in list_entities(paths.root) if entity.get("chapter_no", 0) < chapter_no
    ]
    known_character_profiles = [
        {
            "name": entity.get("name"),
            "character_profile_summary": entity.get("character_profile_summary"),
        }
        for entity in known_entities
        if entity.get("entity_type") == "character" and entity.get("character_profile_summary")
    ]
    previous_summary = ""
    if chapter_no > 1:
        previous_summary = read_text(summary_file(paths, chapter_no - 1), default="")
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
        "project_state": state,
    }
