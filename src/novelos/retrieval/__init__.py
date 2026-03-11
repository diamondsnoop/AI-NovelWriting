"""Retrieval layer."""
from novelos.retrieval.query_router import route_retrieval
from novelos.retrieval.search_engine import search_relevant_snippets

__all__ = ["route_retrieval", "search_relevant_snippets"]
