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


class ForeshadowingStoreTest(unittest.TestCase):
    def test_save_foreshadowing_dedupes_and_limits_count(self) -> None:
        temp_root = ROOT / f".tmp_foreshadow_{uuid4().hex}"
        project_root = temp_root / "demo"
        shutil.rmtree(temp_root, ignore_errors=True)
        project_root.mkdir(parents=True, exist_ok=True)
        try:
            save_foreshadowing(
                project_root,
                5,
                [
                    {
                        "setup": "S-07 首次出现于残影提示",
                        "hint": "S-07 是关键编号",
                        "expected_payoff": "后续揭示 S-07 含义",
                        "source": "chapter_plant",
                    }
                ],
            )
            stored = save_foreshadowing(
                project_root,
                6,
                [
                    {
                        "setup": "S-07 再次出现于残影提示",
                        "hint": "S-07 是关键编号",
                        "expected_payoff": "后续揭示 S-07 含义",
                        "source": "chapter_plant",
                    },
                    {
                        "setup": "地下机房在 23:41 出现维护窗口",
                        "hint": "存在关键时间点",
                        "expected_payoff": "主角将进入地下机房",
                        "source": "chapter_plant",
                    },
                    {
                        "setup": "地下机房 23:41 有维护窗口",
                        "hint": "关键时间点短暂开放",
                        "expected_payoff": "主角会利用窗口潜入",
                        "source": "chapter_plant",
                    },
                    {
                        "setup": "完整版证据包被投放到落脚点",
                        "hint": "有人在引导叙事",
                        "expected_payoff": "后续揭示投放者",
                        "source": "chapter_plant",
                    },
                    {
                        "setup": "录音笔原件可能是唯一真相锚点",
                        "hint": "原件不能轻易交出",
                        "expected_payoff": "后续用于真伪校验",
                        "source": "chapter_plant",
                    },
                    {
                        "setup": "实时观看提示说明林澈被监控",
                        "hint": "终端被渗透",
                        "expected_payoff": "后续追查监控者",
                        "source": "chapter_plant",
                    },
                    {
                        "setup": "许澄的话术像模板",
                        "hint": "许澄可能被对齐",
                        "expected_payoff": "后续揭露许澄状态",
                        "source": "chapter_plant",
                    },
                ],
            )

            self.assertLessEqual(len(stored), 5)
            setups = [item["setup"] for item in stored]
            self.assertEqual(len(setups), len(set(setups)))
            self.assertTrue(any("地下机房" in setup for setup in setups))
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
