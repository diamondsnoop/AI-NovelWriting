import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]


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


class SmokeTest(unittest.TestCase):
    def test_init_write_resume_smoke(self) -> None:
        temp_root = ROOT / f".tmp_test_{uuid4().hex}"
        project_root = temp_root / "demo"
        shutil.rmtree(temp_root, ignore_errors=True)
        temp_root.mkdir(parents=True, exist_ok=True)
        try:
            init_result = run_cli("init", "demo", "--root", str(project_root))
            self.assertEqual(init_result["title"], "demo")

            plan_result = run_cli("plan", "--project", str(project_root), "--chapter", "1")
            self.assertEqual(plan_result["chapter_no"], 1)

            write_result = run_cli("write", "--project", str(project_root), "--chapter", "1")
            self.assertEqual(write_result["review"]["gate_result"], "pass")

            outline_path = Path(plan_result["outline_path"])
            compact_outline_path = Path(plan_result["compact_outline_path"])
            outline_text = outline_path.read_text(encoding="utf-8")
            compact_outline_text = compact_outline_path.read_text(encoding="utf-8")
            self.assertIn("Chapter 1 Outline", outline_text)
            self.assertIn("Compact Outline", compact_outline_text)

            chapter_path = Path(write_result["chapter_path"])
            chapter_text = chapter_path.read_text(encoding="utf-8")
            self.assertIn("Chapter outline", chapter_text)
            self.assertIn("Compact Outline", chapter_text)

            resume_result = run_cli("resume", "--project", str(project_root))
            self.assertEqual(resume_result["status"], "ok")
            self.assertEqual(resume_result["task"]["task_status"], "completed")

            query_project = run_cli("query", "--project", str(project_root), "--type", "project")
            self.assertEqual(query_project["query_type"], "project")
            self.assertEqual(query_project["project"]["title"], "demo")

            query_progress = run_cli("query", "--project", str(project_root), "--type", "progress")
            self.assertEqual(query_progress["progress"]["current_chapter"], 1)
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)

    def test_write_conflict_abort_then_overwrite(self) -> None:
        temp_root = ROOT / f".tmp_test_conflict_{uuid4().hex}"
        project_root = temp_root / "demo"
        shutil.rmtree(temp_root, ignore_errors=True)
        temp_root.mkdir(parents=True, exist_ok=True)
        try:
            run_cli("init", "demo", "--root", str(project_root))
            first_write = run_cli("write", "--project", str(project_root), "--chapter", "1")
            self.assertEqual(first_write["review"]["gate_result"], "pass")

            abort_write = run_cli(
                "write",
                "--project",
                str(project_root),
                "--chapter",
                "1",
                "--on-conflict",
                "abort",
            )
            self.assertEqual(abort_write["status"], "aborted")
            self.assertEqual(abort_write["decision"]["selected_option"], "abort")

            overwrite_write = run_cli(
                "write",
                "--project",
                str(project_root),
                "--chapter",
                "1",
                "--on-conflict",
                "overwrite",
            )
            self.assertEqual(overwrite_write["review"]["gate_result"], "pass")

            query_decisions = run_cli("query", "--project", str(project_root), "--type", "decisions")
            self.assertGreaterEqual(len(query_decisions["decisions"]), 1)

            query_entities = run_cli("query", "--project", str(project_root), "--type", "entities")
            self.assertTrue(query_entities["entities"])
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
