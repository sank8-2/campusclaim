"""Tests for the offline demo pipeline.

Run with:

    python3 -m unittest discover -s tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import demo_pipeline  # noqa: E402


class DemoPipelineTests(unittest.TestCase):
    def test_fixture_has_entities_and_no_image(self):
        fixture = demo_pipeline.load_fixture()
        self.assertEqual(
            set(fixture["entities"]), {"company", "date", "address", "total"}
        )
        self.assertNotIn("image", fixture)
        self.assertNotIn("image", fixture["entities"])

    def test_report_contains_the_full_demo_path(self):
        report = demo_pipeline.build_report()

        self.assertEqual(
            set(report),
            {
                "fixture_entities",
                "plain_json",
                "tuned_json",
                "fields",
                "claim_draft",
                "matches_fixture",
            },
        )
        self.assertEqual(
            report["fields"],
            {
                "company": "Campus Print Hub",
                "date": "2026-10-24",
                "address": "Block C, University Road",
                "total": "431.50",
            },
        )
        self.assertEqual(report["fields"], report["fixture_entities"])
        self.assertTrue(report["matches_fixture"])
        self.assertEqual(report["plain_json"]["date"], "")
        self.assertEqual(report["tuned_json"]["total"], "431.50")
        self.assertIn("Missing fields: none", report["claim_draft"])

    def test_report_marks_a_fixture_mismatch(self):
        fixture = {
            "entities": {
                "company": "Somewhere Else",
                "date": "2026-10-24",
                "address": "Block C, University Road",
                "total": "431.50",
            }
        }
        report = demo_pipeline.build_report(fixture=fixture)
        self.assertFalse(report["matches_fixture"])

    def test_write_report_creates_parent_and_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results" / "demo_report.json"
            written = demo_pipeline.write_report(demo_pipeline.build_report(), path)

            self.assertEqual(written, path)
            self.assertEqual(json.loads(path.read_text()), demo_pipeline.build_report())

    def test_summary_lists_the_four_fields(self):
        summary = demo_pipeline.format_summary(demo_pipeline.build_report())
        for text in ("company:", "date:", "address:", "total:", "Missing fields: none"):
            self.assertIn(text, summary)


if __name__ == "__main__":
    unittest.main()
