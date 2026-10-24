"""Tests for scripts/build_results.py.

They run on a fake `results/` folder so the table builder can be checked without
the Colab run. The fake folder has the exact shape the notebook's export cell
produces.
"""

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_results  # noqa: E402

EXPECTED = {
    "company": "BOOK TA .K (TAMAN DAYA) SDN BHD",
    "date": "25/12/2018",
    "address": "NO.53 55,57 & 59, JALAN SAGU 18, TAMAN DAYA, 81100 JOHOR BAHRU, JOHOR.",
    "total": "9.00",
}


def keys():
    return json.loads((ROOT / "data" / "eval_keys_seed0.json").read_text())["keys"]


def write_csv(path, rows, columns):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def score_run(predictions):
    """Build one prediction CSV and its metrics JSON exactly like the notebook."""
    from score import score

    keys_list = keys()
    rows = []
    totals = {name: 0.0 for name in ["valid JSON", "company exact", "date exact", "address exact", "total exact", "address token-F1"]}
    for key, prediction in zip(keys_list, predictions):
        result = score(prediction, EXPECTED)
        rows.append(
            {
                "key": key,
                "expected": json.dumps(EXPECTED),
                "plain_model": prediction,
                **{k: v for k, v in result.items()},
            }
        )
        totals["valid JSON"] += result["valid_json"]
        totals["company exact"] += result["company"]
        totals["date exact"] += result["date"]
        totals["address exact"] += result["address"]
        totals["total exact"] += result["total"]
        totals["address token-F1"] += result["address_f1"]
    metrics = {name: round(value / len(keys_list) * 100, 1) for name, value in totals.items()}
    return rows, metrics


class BuildResultsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.results = Path(self.tmp.name)
        good = json.dumps(EXPECTED)
        # 98 perfect receipts, one prose reply, one wrong total.
        predictions = [good] * 98 + ["I cannot read this receipt."] + [json.dumps({**EXPECTED, "total": "19.00"})]

        baseline_rows, self.baseline_metrics = score_run(predictions)
        tuned_rows, self.tuned_metrics = score_run(predictions)
        for row in tuned_rows:
            row["fine_tuned_model"] = row.pop("plain_model")

        write_csv(self.results / "baseline_predictions.csv", baseline_rows, list(baseline_rows[0]))
        write_csv(self.results / "tuned_predictions.csv", tuned_rows, list(tuned_rows[0]))
        (self.results / "baseline_metrics.json").write_text(json.dumps(self.baseline_metrics))
        (self.results / "tuned_metrics.json").write_text(json.dumps(self.tuned_metrics))
        (self.results / "settings.json").write_text(
            json.dumps(
                {
                    "model": "unsloth/gemma-4-E2B-it",
                    "eval_keys": 100,
                    "eval_seed": 0,
                    "image_max_side": 1600,
                    "lora_rank": 16,
                    "train_steps": 120,
                    "learning_rate": 0.0002,
                    "batch_size": 1,
                    "grad_accum": 4,
                    "max_length": 2048,
                }
            )
        )
        self.out = self.results / "results.md"

    def tearDown(self):
        self.tmp.cleanup()

    def test_metrics_are_recomputed_and_written(self):
        build_results.build(self.results, check_only=False, output=self.out)
        text = self.out.read_text()
        self.assertIn("| Valid JSON | 99.0 | 99.0 | +0.0 |".replace("Valid", "valid"), text)
        self.assertIn("| total exact | 98.0 | 98.0 | +0.0 |", text)
        self.assertIn("2 of 100 receipts had at least one wrong field", text)
        self.assertIn("test_prose_is_invalid_json", text)

    def test_two_failures_are_listed_with_causes(self):
        _, _, failures, _ = build_results.build(self.results, check_only=False, output=self.out)
        self.assertEqual(len(failures), 2)
        causes = {item["cause"] for item in failures}
        self.assertIn("prose reply, no JSON", causes)

    def test_a_drifted_metric_is_rejected(self):
        self.tuned_metrics["total exact"] = 100.0
        (self.results / "tuned_metrics.json").write_text(json.dumps(self.tuned_metrics))
        with self.assertRaises(build_results.ResultsError):
            build_results.build(self.results, check_only=True)

    def test_a_different_sample_is_rejected(self):
        with (self.results / "tuned_predictions.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        rows[0]["key"] = "SOMETHING_ELSE"
        write_csv(self.results / "tuned_predictions.csv", rows, list(rows[0]))
        with self.assertRaises(build_results.ResultsError):
            build_results.build(self.results, check_only=True)

    def test_check_mode_does_not_write(self):
        build_results.build(self.results, check_only=True, output=self.out)
        self.assertFalse(self.out.exists())

    def test_local_receipts_stay_separate(self):
        write_csv(
            self.results / "local_receipts.csv",
            [{"receipt": "canteen_01.jpg", "fields_correct": "3/4", "notes": "date smudged"}],
            ["receipt", "fields_correct", "notes"],
        )
        build_results.build(self.results, check_only=False, output=self.out)
        text = self.out.read_text()
        self.assertIn("canteen_01.jpg", text)
        self.assertIn("not** pooled with the SROIE numbers", text)

    def test_all_metrics_green_lists_no_failures(self):
        perfect = [json.dumps(EXPECTED)] * 100
        rows, metrics = score_run(perfect)
        tuned_rows = [dict(row) for row in rows]
        for row in tuned_rows:
            row["fine_tuned_model"] = row.pop("plain_model")
        write_csv(self.results / "tuned_predictions.csv", tuned_rows, list(tuned_rows[0]))
        write_csv(self.results / "baseline_predictions.csv", rows, list(rows[0]))
        (self.results / "baseline_metrics.json").write_text(json.dumps(metrics))
        (self.results / "tuned_metrics.json").write_text(json.dumps(metrics))
        _, _, failures, _ = build_results.build(self.results, check_only=False, output=self.out)
        self.assertEqual(failures, [])
        self.assertIn("0 of 100 receipts", self.out.read_text())

    def test_a_missing_label_column_is_rejected(self):
        with (self.results / "tuned_predictions.csv").open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            row["some_other_model"] = row.pop("fine_tuned_model")
        write_csv(self.results / "tuned_predictions.csv", rows, list(rows[0]))
        with self.assertRaises(build_results.ResultsError):
            build_results.build(self.results, check_only=True)


if __name__ == "__main__":
    unittest.main()
