import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = str(ROOT / "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from novelos.review.gatekeeper import gate_review


class GatekeeperLevelTest(unittest.TestCase):
    def test_non_blocking_critical_becomes_pass_warning(self) -> None:
        gate = gate_review(
            {
                "scores": {},
                "checker_results": [
                    {
                        "checker": "high_point",
                        "status": "completed",
                        "score": 0.2,
                        "severity": "critical",
                        "signals": {"codes": ["high_point_missing"]},
                    }
                ],
            }
        )

        self.assertEqual(gate["gate_result"], "pass")
        self.assertEqual(gate["gate_level"], "warning")
        self.assertEqual(gate["blocking_reasons"], [])
        self.assertIn("high_point_missing", gate["warning_reasons"])

    def test_blocking_checker_critical_blocks(self) -> None:
        gate = gate_review(
            {
                "scores": {},
                "checker_results": [
                    {
                        "checker": "consistency",
                        "status": "completed",
                        "score": 0.3,
                        "severity": "critical",
                        "signals": {"codes": ["consistency_conflict"]},
                    }
                ],
            }
        )

        self.assertEqual(gate["gate_result"], "blocked")
        self.assertEqual(gate["gate_level"], "critical")
        self.assertIn("consistency_conflict", gate["blocking_reasons"])

    def test_core_threshold_still_blocks(self) -> None:
        gate = gate_review(
            {
                "scores": {"consistency": 0.49},
                "checker_results": [
                    {
                        "checker": "consistency",
                        "status": "completed",
                        "score": 0.49,
                        "signals": {"codes": []},
                    }
                ],
            }
        )

        self.assertEqual(gate["gate_result"], "blocked")
        self.assertIn("consistency_below_threshold", gate["blocking_reasons"])

    def test_info_only_passes_info(self) -> None:
        gate = gate_review(
            {
                "scores": {},
                "checker_results": [
                    {
                        "checker": "pacing",
                        "status": "completed",
                        "score": 0.75,
                        "severity": "info",
                        "signals": {"codes": ["pacing_ok"]},
                    }
                ],
            }
        )

        self.assertEqual(gate["gate_result"], "pass")
        self.assertEqual(gate["gate_level"], "info")
        self.assertEqual(gate["warning_reasons"], [])


if __name__ == "__main__":
    unittest.main()
