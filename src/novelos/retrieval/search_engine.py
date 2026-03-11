from __future__ import annotations

import math
import re
from dataclasses import dataclass

from novelos.foundation.io import read_text
from novelos.memory.store import ProjectPaths, summary_file


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?；;])")


@dataclass(slots=True)
class RetrievalHit:
    chapter_no: int
    source: str
    source_type: str
    score: float
    snippet: str


def search_relevant_snippets(
    paths: ProjectPaths,
    chapter_no: int,
    query_text: str,
    limit: int = 2,
    *,
    strategy: dict | None = None,
) -> list[dict]:
    resolved_strategy = _resolve_strategy(limit=limit, strategy=strategy)
    effective_query = str(resolved_strategy.get("query_text") or query_text).strip()
    corpus = _build_corpus(paths, chapter_no, max_chunk_chars=resolved_strategy["max_chunk_chars"])
    if not corpus or not effective_query:
        return []

    query_terms = _tokenize(effective_query)
    if not query_terms:
        return []

    doc_freq: dict[str, int] = {}
    doc_terms: list[list[str]] = []
    for item in corpus:
        terms = _tokenize(item["text"])
        doc_terms.append(terms)
        for term in set(terms):
            doc_freq[term] = doc_freq.get(term, 0) + 1

    avgdl = sum(len(terms) for terms in doc_terms) / len(doc_terms)
    hits: list[RetrievalHit] = []
    for item, terms in zip(corpus, doc_terms):
        score = _bm25_score(query_terms, terms, doc_freq, len(doc_terms), avgdl)
        if score <= 0:
            continue
        score *= resolved_strategy["source_weights"].get(item["source_type"], 1.0)
        hits.append(
            RetrievalHit(
                chapter_no=item["chapter_no"],
                source=item["source"],
                source_type=item["source_type"],
                score=round(score, 4),
                snippet=_compress_snippet(
                    text=item["text"],
                    query_terms=query_terms,
                    max_chars=resolved_strategy["compress_chars"],
                ),
            )
        )

    hits.sort(key=lambda hit: hit.score, reverse=True)
    hits = _dedupe_hits(hits, threshold=resolved_strategy["dedupe_threshold"])
    hits = _limit_hits_per_chapter(hits, max_per_chapter=resolved_strategy["max_per_chapter"])
    return [
        {
            "chapter_no": hit.chapter_no,
            "source": hit.source,
            "score": hit.score,
            "snippet": hit.snippet,
        }
        for hit in hits[: resolved_strategy["limit"]]
    ]


def _resolve_strategy(limit: int, strategy: dict | None) -> dict:
    defaults = {
        "query_text": "",
        "limit": max(1, int(limit)),
        "max_chunk_chars": 260,
        "compress_chars": 180,
        "max_per_chapter": 2,
        "dedupe_threshold": 0.82,
        "source_weights": {
            "chapter_chunk": 1.0,
            "chapter_summary": 1.1,
        },
    }
    if not strategy:
        return defaults

    merged = dict(defaults)
    merged["query_text"] = str(strategy.get("query_text", defaults["query_text"])).strip()
    merged["limit"] = max(1, int(strategy.get("limit", defaults["limit"])))
    merged["max_chunk_chars"] = max(100, int(strategy.get("max_chunk_chars", defaults["max_chunk_chars"])))
    merged["compress_chars"] = max(80, int(strategy.get("compress_chars", defaults["compress_chars"])))
    merged["max_per_chapter"] = max(1, int(strategy.get("max_per_chapter", defaults["max_per_chapter"])))
    merged["dedupe_threshold"] = min(0.98, max(0.4, float(strategy.get("dedupe_threshold", defaults["dedupe_threshold"]))))

    source_weights = dict(defaults["source_weights"])
    for source_type, weight in dict(strategy.get("source_weights", {})).items():
        try:
            source_weights[str(source_type)] = max(0.5, min(2.0, float(weight)))
        except (TypeError, ValueError):
            continue
    merged["source_weights"] = source_weights
    return merged


def _build_corpus(paths: ProjectPaths, chapter_no: int, max_chunk_chars: int) -> list[dict]:
    corpus: list[dict] = []
    for current in range(1, chapter_no):
        chapter_path = paths.chapters_dir / f"chapter_{current:04d}.md"
        chapter_text = read_text(chapter_path, default="")
        for idx, chunk in enumerate(_chunk_text(chapter_text, max_chars=max_chunk_chars)):
            corpus.append(
                {
                    "chapter_no": current,
                    "source": f"chapter_chunk_{idx + 1}",
                    "source_type": "chapter_chunk",
                    "text": chunk,
                }
            )

        summary_text = read_text(summary_file(paths, current), default="")
        if summary_text:
            corpus.append(
                {
                    "chapter_no": current,
                    "source": "chapter_summary",
                    "source_type": "chapter_summary",
                    "text": summary_text,
                }
            )
    return corpus


def _chunk_text(text: str, max_chars: int = 260) -> list[str]:
    paragraphs = [_normalize_whitespace(part) for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs and text.strip():
        paragraphs = [_normalize_whitespace(text)]
    chunks: list[str] = []
    for paragraph in paragraphs:
        chunks.extend(_chunk_paragraph(paragraph, max_chars=max_chars))
    return chunks


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _chunk_paragraph(paragraph: str, max_chars: int) -> list[str]:
    sentences = [part.strip() for part in SENTENCE_SPLIT_PATTERN.split(paragraph) if part and part.strip()]
    if not sentences:
        sentences = [paragraph]

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_slice_long_text(sentence, max_chars=max_chars))
            continue

        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)
    return chunks


def _slice_long_text(text: str, max_chars: int) -> list[str]:
    return [text[start : start + max_chars].strip() for start in range(0, len(text), max_chars) if text[start : start + max_chars].strip()]


def _compress_snippet(text: str, query_terms: list[str], max_chars: int) -> str:
    normalized = _normalize_whitespace(text)
    if len(normalized) <= max_chars:
        return normalized

    lowered = normalized.lower()
    pivot = -1
    for term in sorted({term for term in query_terms if len(term) >= 2}, key=len, reverse=True):
        idx = lowered.find(term)
        if idx >= 0:
            pivot = idx
            break

    if pivot < 0:
        return f"{normalized[:max_chars].rstrip()}..."

    left = max(0, pivot - max_chars // 3)
    right = min(len(normalized), left + max_chars)
    window = normalized[left:right].strip()
    if left > 0:
        window = f"...{window}"
    if right < len(normalized):
        window = f"{window}..."
    return window


def _dedupe_hits(hits: list[RetrievalHit], threshold: float) -> list[RetrievalHit]:
    kept: list[RetrievalHit] = []
    signatures: list[set[str]] = []
    for hit in hits:
        signature = set(_tokenize(hit.snippet))
        if signature and any(_jaccard(signature, other) >= threshold for other in signatures):
            continue
        kept.append(hit)
        if signature:
            signatures.append(signature)
    return kept


def _limit_hits_per_chapter(hits: list[RetrievalHit], max_per_chapter: int) -> list[RetrievalHit]:
    kept: list[RetrievalHit] = []
    chapter_counts: dict[int, int] = {}
    for hit in hits:
        if chapter_counts.get(hit.chapter_no, 0) >= max_per_chapter:
            continue
        kept.append(hit)
        chapter_counts[hit.chapter_no] = chapter_counts.get(hit.chapter_no, 0) + 1
    return kept


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _bm25_score(
    query_terms: list[str],
    doc_terms: list[str],
    doc_freq: dict[str, int],
    doc_count: int,
    avgdl: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not doc_terms or avgdl == 0:
        return 0.0
    score = 0.0
    doc_len = len(doc_terms)
    term_counts: dict[str, int] = {}
    for term in doc_terms:
        term_counts[term] = term_counts.get(term, 0) + 1

    for term in set(query_terms):
        freq = term_counts.get(term, 0)
        if freq == 0:
            continue
        df = doc_freq.get(term, 0)
        idf = math.log(1 + (doc_count - df + 0.5) / (df + 0.5))
        denom = freq + k1 * (1 - b + b * doc_len / avgdl)
        score += idf * (freq * (k1 + 1)) / denom
    return score
