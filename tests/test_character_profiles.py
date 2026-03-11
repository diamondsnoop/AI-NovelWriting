import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = str(ROOT / "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from novelos.workflow.character_profiles import build_character_profiles


class CharacterProfileAggregationTest(unittest.TestCase):
    def test_build_character_profiles_deduplicates_same_chapter_and_keeps_recent_three(self) -> None:
        profiles = build_character_profiles(
            [
                {"entity_type": "character", "name": "林澈", "chapter_no": 1, "character_profile_summary": "第一章短摘要"},
                {"entity_type": "character", "name": "林澈", "chapter_no": 1, "character_profile_summary": "第一章更长的画像摘要"},
                {"entity_type": "character", "name": "林澈", "chapter_no": 2, "character_profile_summary": "第二章摘要"},
                {"entity_type": "character", "name": "林澈", "chapter_no": 3, "character_profile_summary": "第三章摘要"},
                {"entity_type": "character", "name": "林澈", "chapter_no": 4, "character_profile_summary": "第四章摘要"},
            ]
        )

        self.assertEqual(len(profiles), 1)
        profile = profiles[0]
        self.assertEqual(profile["name"], "林澈")
        self.assertEqual(profile["evidence_count"], 4)
        self.assertEqual(profile["chapters"], [1, 2, 3, 4])
        self.assertNotIn("第一章短摘要", profile["character_profile_summary"])
        self.assertNotIn("第1章", profile["character_profile_summary"])
        self.assertIn("第2章：第二章摘要", profile["character_profile_summary"])
        self.assertIn("第3章：第三章摘要", profile["character_profile_summary"])
        self.assertIn("第4章：第四章摘要", profile["character_profile_summary"])


if __name__ == "__main__":
    unittest.main()
