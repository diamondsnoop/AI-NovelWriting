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


class LearnFlowTest(unittest.TestCase):
    def test_learn_saves_project_memory_and_can_query(self) -> None:
        temp_root = ROOT / f".tmp_learn_{uuid4().hex}"
        project_root = temp_root / "demo"
        shutil.rmtree(temp_root, ignore_errors=True)
        temp_root.mkdir(parents=True, exist_ok=True)
        try:
            run_cli("init", "demo", "--root", str(project_root))
            learn_result = run_cli(
                "learn",
                "--project",
                str(project_root),
                "--type",
                "hook_pattern",
                "--content",
                "章节尾段先给结果再抛反转疑问，追读动力更稳定。",
                "--source-ref",
                "chapter_0003",
                "--source-ref",
                "chapter_0004",
            )
            self.assertIn("task_id", learn_result)
            self.assertEqual(learn_result["memory_record"]["memory_type"], "hook_pattern")
            self.assertTrue(learn_result["memory_record"]["source_refs"])

            query_result = run_cli("query", "--project", str(project_root), "--type", "project_memory")
            self.assertEqual(query_result["query_type"], "project_memory")
            self.assertTrue(query_result["project_memory"])
            latest = query_result["project_memory"][-1]
            self.assertEqual(latest["memory_type"], "hook_pattern")
            self.assertIn("追读动力", latest["content"])
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
