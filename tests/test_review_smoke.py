import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = str(ROOT / "src")
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)


def run_cli(*args: str) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["NOVEL_LLM_PROVIDER"] = "mock"
    env["NOVEL_LLM_MODEL"] = "skeleton-writer"
    env.pop("OPENAI_API_KEY", None)
    env.pop("OPENAI_BASE_URL", None)
    result = subprocess.run(
        [sys.executable, "-m", "novelos", *args],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class ReviewSmokeTest(unittest.TestCase):
    def test_plan_write_generates_summary(self) -> None:
        temp_root = ROOT / f".tmp_review_{uuid4().hex}"
        project_root = temp_root / "demo"
        shutil.rmtree(temp_root, ignore_errors=True)
        temp_root.mkdir(parents=True, exist_ok=True)
        try:
            run_cli("init", "demo", "--root", str(project_root))
            plan_result = run_cli("plan", "--project", str(project_root), "--chapter", "1")
            write_result = run_cli("write", "--project", str(project_root), "--chapter", "1")

            self.assertEqual(plan_result["chapter_no"], 1)
            self.assertIn("compact_outline_path", plan_result)
            self.assertEqual(write_result["review"]["gate_result"], "pass")
            summary_path = project_root / "summaries" / "chapter_0001_summary.md"
            self.assertTrue(summary_path.exists())
            structured_summary_path = project_root / ".novelos" / "summaries" / "chapter_0001_summary.json"
            self.assertTrue(structured_summary_path.exists())
            self.assertTrue(write_result["entities"])
            self.assertTrue(write_result["foreshadowing"])
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)

    def test_continuity_checker_uses_previous_summary(self) -> None:
        temp_root = ROOT / f".tmp_continuity_{uuid4().hex}"
        project_root = temp_root / "demo"
        shutil.rmtree(temp_root, ignore_errors=True)
        temp_root.mkdir(parents=True, exist_ok=True)
        try:
            run_cli("init", "demo", "--root", str(project_root))
            run_cli("plan", "--project", str(project_root), "--chapter", "1")
            run_cli("write", "--project", str(project_root), "--chapter", "1")
            run_cli("plan", "--project", str(project_root), "--chapter", "2")
            second_write = run_cli("write", "--project", str(project_root), "--chapter", "2")

            self.assertEqual(second_write["review"]["gate_result"], "pass")
            consistency = next(
                item for item in second_write["review"]["checker_results"] if item["checker"] == "consistency"
            )
            character = next(
                item for item in second_write["review"]["checker_results"] if item["checker"] == "character"
            )
            continuity = next(
                item for item in second_write["review"]["checker_results"] if item["checker"] == "continuity"
            )
            pacing = next(
                item for item in second_write["review"]["checker_results"] if item["checker"] == "pacing"
            )
            self.assertEqual(consistency["status"], "completed")
            self.assertGreaterEqual(consistency["score"], 0.5)
            self.assertEqual(character["status"], "completed")
            self.assertGreaterEqual(character["score"], 0.5)
            self.assertEqual(continuity["status"], "completed")
            self.assertGreaterEqual(continuity["score"], 0.5)
            self.assertIn(pacing["status"], {"completed", "skipped"})
            if pacing["status"] == "completed":
                self.assertIn(pacing["severity"], {"info", "warning"})
            self.assertTrue(second_write["review"]["inactive_checkers"])

            query_entities = run_cli("query", "--project", str(project_root), "--type", "entities")
            self.assertTrue(query_entities["entities"])
            entity_types = {item["entity_type"] for item in query_entities["entities"]}
            self.assertIn("character", entity_types)
            self.assertIn("location", entity_types)
            character_profiles = [
                item["character_profile_summary"]
                for item in query_entities["entities"]
                if item["entity_type"] == "character"
            ]
            self.assertTrue(all(character_profiles))

            query_summaries = run_cli("query", "--project", str(project_root), "--type", "summaries")
            self.assertTrue(query_summaries["summaries"])
            self.assertEqual(query_summaries["sync_issues"], [])
            self.assertTrue(all(item["in_sync"] for item in query_summaries["summaries"]))

            query_foreshadowing = run_cli("query", "--project", str(project_root), "--type", "foreshadowing")
            self.assertTrue(query_foreshadowing["foreshadowing"])

            from novelos.memory.store import build_project_paths, load_project_state
            from novelos.workflow.context_package import build_write_package

            paths = build_project_paths(project_root)
            project_state = load_project_state(paths)
            write_package = build_write_package(project_state, 2, paths)
            self.assertTrue(write_package["retrieved_context"])
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)
