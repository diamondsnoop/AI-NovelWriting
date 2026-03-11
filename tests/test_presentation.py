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


class PresentationReadOnlyTest(unittest.TestCase):
    def test_status_report_and_dashboard_queries(self) -> None:
        temp_root = ROOT / f".tmp_presentation_{uuid4().hex}"
        project_root = temp_root / "demo"
        shutil.rmtree(temp_root, ignore_errors=True)
        temp_root.mkdir(parents=True, exist_ok=True)
        try:
            run_cli("init", "demo", "--root", str(project_root))
            run_cli("plan", "--project", str(project_root), "--chapter", "1")
            run_cli("write", "--project", str(project_root), "--chapter", "1")

            before_files = sorted(
                str(path.relative_to(project_root))
                for path in project_root.rglob("*")
                if path.is_file()
            )

            status_report = run_cli("query", "--project", str(project_root), "--type", "status_report")
            dashboard = run_cli("query", "--project", str(project_root), "--type", "dashboard")

            self.assertEqual(status_report["query_type"], "status_report")
            self.assertIn("risk_level", status_report)
            self.assertIn("alerts", status_report)

            self.assertEqual(dashboard["query_type"], "dashboard")
            self.assertEqual(dashboard["mode"], "read_only")
            self.assertIn("project_overview", dashboard)
            self.assertIn("risk_panel", dashboard)

            after_files = sorted(
                str(path.relative_to(project_root))
                for path in project_root.rglob("*")
                if path.is_file()
            )
            self.assertEqual(before_files, after_files)
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
