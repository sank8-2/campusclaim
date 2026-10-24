"""Pre-flight test: the notebook and the frozen data must stay in sync."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NotebookPreflightTests(unittest.TestCase):
    def test_notebook_preflight_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_notebook.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
