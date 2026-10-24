"""Tests for the receipt field scoring. Run with:

    python3 -m unittest discover -s tests -v
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from score import norm_date, norm_total, score, token_f1  # noqa: E402

ENTITIES = {
    "company": "BOOK TA .K (TAMAN DAYA) SDN BHD",
    "date": "25/12/2018",
    "address": "NO.53 55,57 & 59, JALAN SAGU 18, TAMAN DAYA, 81100 JOHOR BAHRU, JOHOR.",
    "total": "9.00",
}


class ScoreTests(unittest.TestCase):
    def test_perfect_json_scores_every_field(self):
        result = score(json.dumps(ENTITIES), ENTITIES)
        self.assertEqual(result["valid_json"], 1)
        for field in ("company", "date", "address", "total"):
            self.assertEqual(result[field], 1, field)
        self.assertEqual(result["address_f1"], 1.0)

    def test_case_currency_and_date_format_are_normalised(self):
        prediction = {
            "company": "book ta .k (taman daya) sdn bhd",
            "date": "25-12-18",
            "address": "no 53 55 57 59 jalan sagu 18 taman daya 81100 johor bahru johor",
            "total": "RM 9.00",
        }
        result = score(json.dumps(prediction), ENTITIES)
        for field in ("company", "date", "address", "total"):
            self.assertEqual(result[field], 1, field)

    def test_wrong_fields_score_zero(self):
        prediction = {
            "company": "WRONG",
            "date": "26/12/2018",
            "address": "elsewhere",
            "total": "9.50",
        }
        result = score(json.dumps(prediction), ENTITIES)
        self.assertEqual(result["valid_json"], 1)
        for field in ("company", "date", "address", "total"):
            self.assertEqual(result[field], 0, field)

    def test_prose_is_invalid_json(self):
        result = score("Sorry, I cannot read this receipt.", ENTITIES)
        self.assertEqual(result["valid_json"], 0)
        self.assertEqual(result["total"], 0)

    def test_markdown_fenced_json_is_parsed(self):
        result = score(f"```json\n{json.dumps(ENTITIES)}\n```", ENTITIES)
        self.assertEqual(result["valid_json"], 1)
        self.assertEqual(result["total"], 1)

    def test_date_formats(self):
        self.assertEqual(norm_date("25 MAR 2019"), "25/03/2019")
        self.assertEqual(norm_date("25-12-18"), "25/12/2018")
        self.assertEqual(norm_date("25/12/2018"), "25/12/2018")

    def test_total_formats(self):
        self.assertEqual(norm_total("RM 1,234.50"), 1234.5)
        self.assertEqual(norm_total("9.00"), 9.0)
        self.assertIsNone(norm_total(""))

    def test_token_f1_is_partial_for_missing_tokens(self):
        value = token_f1("jalan sagu 18 johor", "jalan sagu 18 taman daya johor")
        self.assertGreater(value, 0.0)
        self.assertLess(value, 1.0)


if __name__ == "__main__":
    unittest.main()
