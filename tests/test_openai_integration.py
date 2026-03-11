import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY is required for this manual test.")
class OpenAIIntegrationTest(unittest.TestCase):
    def test_openai_write_flow_manual(self) -> None:
        project_root = ROOT / ".tmp_openai_test" / "demo"
        if project_root.parent.exists():
            import shutil

            shutil.rmtree(project_root.parent, ignore_errors=True)
        project_root.parent.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        env["NOVEL_LLM_PROVIDER"] = "openai"

        try:
            subprocess.run(
                [sys.executable, "-m", "novelos", "init", "demo", "--root", str(project_root)],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                [sys.executable, "-m", "novelos", "write", "--project", str(project_root), "--chapter", "1"],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["generation"]["provider"], "openai")
            self.assertTrue(payload["generation"]["latency_ms"] is None or payload["generation"]["latency_ms"] >= 0)
        finally:
            import shutil

            shutil.rmtree(project_root.parent, ignore_errors=True)
