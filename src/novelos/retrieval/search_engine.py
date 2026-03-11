from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from novelos.foundation.io import read_text
from novelos.memory.store import ProjectPaths, summary_file


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


@dataclass(slots=True)
class RetrievalHit:
    chapter_no: int
    source: str
    score: float
    snippet: str


def search_relevant_snippets(paths: ProjectPaths, chapter_no: int, query_text: str, limit: int = 2) -> list[dict]:
    corpus = _build_corpus(paths, chapter_no)
    if not corpus or not query_text.strip():
        return []

    query_terms = _tokenize(query_text)
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
        hits.append(
            RetrievalHit(
                chapter_no=item["chapter_no"],
                source=item["source"],
                score=round(score, 4),
                snippet=item["text"][:220].strip(),
            )
        )

    hits.sort(key=lambda hit: hit.score, reverse=True)
    return [
        {
            "chapter_no": hit.chapter_no,
            "source": hit.source,
            "score": hit.score,
            "snippet": hit.snippet,
        }
        for hit in hits[:limit]
    ]


def _build_corpus(paths: ProjectPaths, chapter_no: int) -> list[dict]:
    corpus: list[dict] = []
    for current in range(1, chapter_no):
        chapter_path = paths.chapters_dir / f"chapter_{current:04d}.md"
        chapter_text = read_text(chapter_path, default="")
        for idx, chunk in enumerate(_chunk_text(chapter_text)):
            corpus.append(
                {
                    "chapter_no": current,
                    "source": f"chapter_chunk_{idx + 1}",
                    "text": chunk,
                }
            )

        summary_text = read_text(summary_file(paths, current), default="")
        if summary_text:
            corpus.append(
                {
                    "chapter_no": current,
                    "source": "chapter_summary",
                    "text": summary_text,
                }
            )
    return corpus


def _chunk_text(text: str, max_chars: int = 260) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for part in paragraphs:
        candidate = f"{current}\n\n{part}".strip() if current else part
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(part) <= max_chars:
            current = part
        else:
            for start in range(0, len(part), max_chars):
                chunks.append(part[start : start + max_chars])
            current = ""
    if current:
        chunks.append(current)
    return chunks


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


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
