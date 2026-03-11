import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = str(ROOT / "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from novelos.review.report_builder import build_review_report


class ReviewScoreNormalizationTest(unittest.TestCase):
    def test_build_review_report_normalizes_percentage_scores(self) -> None:
        report = build_review_report(
            [
                {"checker": "continuity", "score": 95, "issues": []},
                {"checker": "consistency", "score": 0.92, "issues": []},
                {"checker": "character", "score": 12, "issues": []},
            ]
        )

        self.assertEqual(report["scores"]["continuity"], 0.95)
        self.assertEqual(report["scores"]["consistency"], 0.92)
        self.assertEqual(report["scores"]["character"], 0.12)
        self.assertTrue(all(0 <= score <= 1 for score in report["scores"].values()))


if __name__ == "__main__":
    unittest.main()
