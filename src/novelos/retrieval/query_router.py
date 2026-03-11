from __future__ import annotations


def route_retrieval(
    intent: str,
    *,
    chapter_outline: str = "",
    previous_summary: str = "",
    user_query: str = "",
) -> dict:
    normalized_intent = (intent or "").strip().lower()
    if normalized_intent == "query":
        query_text = user_query.strip() or _join_non_empty([chapter_outline, previous_summary])
        return {
            "intent": "query",
            "query_text": query_text,
            "limit": 5,
            "max_chunk_chars": 260,
            "compress_chars": 200,
            "max_per_chapter": 2,
            "dedupe_threshold": 0.8,
            "source_weights": {
                "chapter_chunk": 1.0,
                "chapter_summary": 1.08,
            },
        }

    query_text = _join_non_empty([chapter_outline, previous_summary])
    has_outline = bool(chapter_outline.strip())
    has_summary = bool(previous_summary.strip())
    if has_outline and has_summary:
        limit = 4
    elif has_outline or has_summary:
        limit = 3
    else:
        limit = 2

    return {
        "intent": "write_context",
        "query_text": query_text,
        "limit": limit,
        "max_chunk_chars": 260,
        "compress_chars": 180,
        "max_per_chapter": 2,
        "dedupe_threshold": 0.82,
        "source_weights": {
            "chapter_chunk": 1.0,
            "chapter_summary": 1.12,
        },
    }


def _join_non_empty(parts: list[str]) -> str:
    return "\n\n".join(part.strip() for part in parts if part and part.strip())
