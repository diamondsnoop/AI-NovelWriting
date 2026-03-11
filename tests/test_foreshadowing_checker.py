import shutil
import sys
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = str(ROOT / "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from novelos.memory.foreshadowing import save_foreshadowing
from novelos.review.foreshadowing_checker import ForeshadowingChecker


class ForeshadowingCheckerTest(unittest.TestCase):
    def test_checker_warns_on_unclear_new_items(self) -> None:
        temp_root = ROOT / f".tmp_foreshadow_checker_{uuid4().hex}"
        project_root = temp_root / "demo"
        shutil.rmtree(temp_root, ignore_errors=True)
        project_root.mkdir(parents=True, exist_ok=True)
        try:
            checker = ForeshadowingChecker()
            result = checker.run(
                project_root=project_root,
                chapter_no=3,
                draft_text="主角收到一条模糊线索。",
                new_items=[
                    {
                        "setup": "出现神秘编号",
                        "hint": "",
                        "expected_payoff": "",
                    }
                ],
            )
            self.assertEqual(result["checker"], "foreshadowing")
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["severity"], "warning")
            self.assertTrue(result["issues"])
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)

    def test_checker_warns_on_possible_conflict_and_hanging(self) -> None:
        temp_root = ROOT / f".tmp_foreshadow_checker_{uuid4().hex}"
        project_root = temp_root / "demo"
        shutil.rmtree(temp_root, ignore_errors=True)
        project_root.mkdir(parents=True, exist_ok=True)
        try:
            save_foreshadowing(
                project_root=project_root,
                chapter_no=1,
                items=[
                    {
                        "setup": "赤铁钥匙首次出现",
                        "hint": "钥匙是矿场主线关键",
                        "expected_payoff": "后续揭示钥匙真正用途",
                        "source": "chapter_plant",
                    }
                ],
            )

            checker = ForeshadowingChecker(hanging_threshold_chapters=3)
            result = checker.run(
                project_root=project_root,
                chapter_no=5,
                draft_text="本章明确写到赤铁钥匙并非关键线索，主角转向其他目标。",
                new_items=[],
            )
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["severity"], "warning")
            issues_text = " ".join(result["issues"])
            self.assertIn("contradicted", issues_text)

            hanging_result = checker.run(
                project_root=project_root,
                chapter_no=5,
                draft_text="本章主角只处理支线任务，没有回看矿场线索。",
                new_items=[],
            )
            self.assertEqual(hanging_result["status"], "completed")
            self.assertEqual(hanging_result["severity"], "warning")
            hanging_text = " ".join(hanging_result["issues"])
            self.assertIn("hanging", hanging_text)
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
