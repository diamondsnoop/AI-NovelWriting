import shutil
import sys
import unittest
from collections import Counter
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = str(ROOT / "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from novelos.foundation.io import write_text
from novelos.memory.store import build_project_paths, ensure_project_layout
from novelos.retrieval.query_router import route_retrieval
from novelos.retrieval.search_engine import search_relevant_snippets


class RetrievalRoutingTest(unittest.TestCase):
    def test_route_retrieval_for_write_context(self) -> None:
        route = route_retrieval(
            "write_context",
            chapter_outline="主角必须在本章找回赤铁钥匙。",
            previous_summary="上一章主角发现钥匙线索来自旧矿场。",
        )

        self.assertEqual(route["intent"], "write_context")
        self.assertEqual(route["limit"], 4)
        self.assertIn("赤铁钥匙", route["query_text"])
        self.assertIn("旧矿场", route["query_text"])
        self.assertGreater(route["source_weights"]["chapter_summary"], route["source_weights"]["chapter_chunk"])


class RetrievalSearchTest(unittest.TestCase):
    def test_search_relevant_snippets_dedupes_limits_and_compresses(self) -> None:
        temp_root = ROOT / f".tmp_retrieval_{uuid4().hex}"
        project_root = temp_root / "demo"
        shutil.rmtree(temp_root, ignore_errors=True)
        try:
            paths = build_project_paths(project_root)
            ensure_project_layout(paths)

            write_text(
                paths.chapters_dir / "chapter_0001.md",
                (
                    "林澈在旧矿场追查赤铁钥匙的来源。他确认钥匙和矿场废墟有关。\n\n"
                    "林澈在旧矿场追查赤铁钥匙的来源。他确认钥匙和矿场废墟有关。"
                ),
            )
            write_text(
                paths.chapters_dir / "chapter_0002.md",
                "苏晚在档案库找到赤铁钥匙的登记记录，但记录指向错误仓库。",
            )
            write_text(
                paths.summaries_dir / "chapter_0001_summary.md",
                "第1章：林澈在旧矿场追查赤铁钥匙来源，确认线索有效。",
            )
            write_text(
                paths.summaries_dir / "chapter_0002_summary.md",
                "第2章：苏晚确认赤铁钥匙登记记录存在异常，线索转向仓库。",
            )

            query_text = "赤铁钥匙 旧矿场 登记记录"
            strategy = {
                "query_text": query_text,
                "limit": 6,
                "compress_chars": 70,
                "max_per_chapter": 1,
                "dedupe_threshold": 0.75,
                "source_weights": {
                    "chapter_chunk": 1.0,
                    "chapter_summary": 1.12,
                },
            }
            hits = search_relevant_snippets(
                paths=paths,
                chapter_no=3,
                query_text=query_text,
                limit=6,
                strategy=strategy,
            )

            self.assertTrue(hits)
            chapter_counter = Counter(hit["chapter_no"] for hit in hits)
            self.assertTrue(all(count <= 1 for count in chapter_counter.values()))
            self.assertLessEqual(max(len(hit["snippet"]) for hit in hits), 73)
            self.assertEqual(len(hits), len({hit["snippet"] for hit in hits}))
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
