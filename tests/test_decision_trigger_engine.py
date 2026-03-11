import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = str(ROOT / "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

from novelos.decision.trigger_engine import collect_decision_triggers


class DecisionTriggerEngineTest(unittest.TestCase):
    def test_collects_review_severe_issue_trigger(self) -> None:
        triggers = collect_decision_triggers(
            write_package={},
            review_result={
                "checker_results": [
                    {
                        "checker": "continuity",
                        "status": "completed",
                        "severity": "critical",
                        "issues": ["Severe continuity break"],
                        "signals": {"codes": ["continuity_break"]},
                    }
                ]
            },
        )
        trigger_codes = [item["trigger_code"] for item in triggers]
        self.assertIn("review_severe_issue", trigger_codes)

    def test_collects_setting_conflict_trigger(self) -> None:
        triggers = collect_decision_triggers(
            write_package={},
            review_result={
                "checker_results": [
                    {
                        "checker": "consistency",
                        "status": "completed",
                        "score": 0.42,
                        "signals": {"codes": ["consistency_conflict"]},
                        "issues": ["Conflict with established setting."],
                    }
                ]
            },
        )
        trigger_codes = [item["trigger_code"] for item in triggers]
        self.assertIn("setting_conflict", trigger_codes)

    def test_collects_route_branch_trigger(self) -> None:
        triggers = collect_decision_triggers(
            write_package={
                "route_branch_candidates": [
                    "路线A：先潜入矿场。",
                    "路线B：先追踪内鬼。",
                ]
            },
            review_result={"checker_results": []},
        )
        trigger_codes = [item["trigger_code"] for item in triggers]
        self.assertIn("route_branch", trigger_codes)


if __name__ == "__main__":
    unittest.main()
