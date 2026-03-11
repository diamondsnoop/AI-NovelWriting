def build_character_profiles(known_entities: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for entity in known_entities:
        if entity.get("entity_type") != "character":
            continue
        name = str(entity.get("name", "")).strip()
        summary = str(entity.get("character_profile_summary", "")).strip()
        if not name or not summary:
            continue

        chapter_no = int(entity.get("chapter_no", 0) or 0)
        bucket = grouped.setdefault(
            name,
            {
                "name": name,
                "chapter_summaries": {},
            },
        )
        chapter_summaries = bucket["chapter_summaries"]
        existing = chapter_summaries.get(chapter_no)
        if existing is None or len(summary) > len(existing):
            chapter_summaries[chapter_no] = summary

    profiles = []
    for name, bucket in grouped.items():
        chapter_summaries = bucket["chapter_summaries"]
        chapters = sorted(chapter_summaries)
        recent_chapters = chapters[-3:]
        profile_lines = [f"- 第{chapter_no}章：{chapter_summaries[chapter_no]}" for chapter_no in recent_chapters]
        profiles.append(
            {
                "name": name,
                "evidence_count": len(chapters),
                "chapters": chapters,
                "character_profile_summary": "\n".join(profile_lines),
            }
        )

    profiles.sort(key=lambda item: (-item["evidence_count"], item["name"]))
    return profiles
