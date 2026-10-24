"""Run the notebook's own scoring cell against the four cases in issue #2.

`tests/test_scoring.py` covers the reference copy in `scripts/score.py`. This
file checks the copy that actually runs in Colab, so a normaliser edited in only
one place fails a test instead of quietly changing the reported numbers.
"""

import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "campusclaim_3b.ipynb"
sys.path.insert(0, str(ROOT / "scripts"))

import score as reference  # noqa: E402

EXPECTED = {
    "entities": {
        "company": "BOOK TA .K (TAMAN DAYA) SDN BHD",
        "date": "25/12/2018",
        "address": "NO.53 55,57 & 59, JALAN SAGU 18, TAMAN DAYA, 81100 JOHOR BAHRU, JOHOR.",
        "total": "9.00",
    }
}

CASES = {
    "perfect": json.dumps(EXPECTED["entities"]),
    "normalised": json.dumps(
        {
            "company": "book ta .k (taman daya) sdn bhd",
            "date": "25 Dec 2018",
            "address": "no.53 55,57 & 59, jalan sagu 18, taman daya, 81100 johor bahru, johor.",
            "total": "RM 9.00",
        }
    ),
    "wrong fields": json.dumps(
        {"company": "OTHER SHOP", "date": "01/01/2019", "address": "SOMEWHERE ELSE", "total": "10.00"}
    ),
    "prose": "The receipt shows a total of RM 9.00 at a bookshop in Johor Bahru.",
}


def load_cell():
    notebook = json.loads(NOTEBOOK.read_text())
    for cell in notebook["cells"]:
        source = "".join(cell["source"])
        if cell["cell_type"] == "code" and "def score(prediction, expected)" in source:
            return source
    raise AssertionError("the notebook no longer has a scoring cell")


def notebook_fields():
    """Read `FIELDS` from the Step 2 cell, where the notebook defines it."""
    notebook = json.loads(NOTEBOOK.read_text())
    for cell in notebook["cells"]:
        source = "".join(cell["source"])
        if cell["cell_type"] == "code" and "FIELDS = [" in source:
            import ast
            import re

            match = re.search(r"FIELDS = (\[[^\]]*\])", source)
            return ast.literal_eval(match.group(1))
    raise AssertionError("the notebook no longer defines FIELDS")


def namespace():
    """Execute the notebook scoring cell without pandas or a GPU."""
    stub = types.ModuleType("pandas")
    stub.DataFrame = object
    sys.modules.setdefault("pandas", stub)

    source = load_cell()
    space = {
        "torch": types.SimpleNamespace(),
        "processor": None,
        "model": None,
        "FIELDS": notebook_fields(),
    }
    # The cell also defines generation helpers; only the scoring part is run.
    head = source.split("def generate_from_image")[0]
    exec(compile(head, "notebook-scoring-cell", "exec"), space)
    return space


class NotebookScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = namespace()

    def nb(self, prediction):
        """The notebook cell scores a dataset sample, so it takes `entities`."""
        return self.ns["score"](prediction, EXPECTED)

    def ref(self, prediction):
        """scripts/score.py takes the flat entities dict."""
        return reference.score(prediction, EXPECTED["entities"])

    def test_frozen_fields_match_the_reference(self):
        self.assertEqual(self.ns["FIELDS"], reference.FIELDS)

    def test_only_a_dict_with_all_four_fields_is_valid_json(self):
        self.assertEqual(self.nb("The total is 9.00")["valid_json"], self.ref("The total is 9.00")["valid_json"])

    def test_four_issue_cases_agree_with_the_reference(self):
        for name, prediction in CASES.items():
            with self.subTest(case=name):
                notebook = self.nb(prediction)
                expected = self.ref(prediction)
                for field in ("valid_json", "company", "date", "address", "total"):
                    self.assertEqual(notebook[field], expected[field], f"{name}/{field}")
                self.assertAlmostEqual(notebook["address_f1"], expected["address_f1"], places=6)

    def test_case_expectations(self):
        self.assertEqual(self.nb(CASES["perfect"])["total"], 1)
        self.assertEqual(self.nb(CASES["normalised"])["date"], 1)
        self.assertEqual(self.nb(CASES["normalised"])["total"], 1)
        wrong = self.nb(CASES["wrong fields"])
        self.assertEqual([wrong[f] for f in ("company", "date", "address", "total")], [0, 0, 0, 0])
        prose = self.nb(CASES["prose"])
        self.assertEqual(prose["valid_json"], 0)
        self.assertEqual([prose[f] for f in ("company", "date", "address", "total")], [0, 0, 0, 0])

    def test_normalisers_agree_on_the_awkward_cases(self):
        pairs = [
            ("25 Dec 2018", "25/12/2018"),
            ("25-12-18", "25/12/2018"),
            ("2018-12-25", "25/12/2018"),
            ("9", "9.00"),
            ("RM 1,234.50", "1234.5"),
        ]
        for left, right in pairs:
            with self.subTest(value=left):
                self.assertEqual(self.ns["norm_date"](left), reference.norm_date(left))
                self.assertEqual(self.ns["norm_total"](left), reference.norm_total(left))
        self.assertEqual(
            self.ns["token_f1"]("NO.53 JALAN SAGU", EXPECTED["entities"]["address"]),
            reference.token_f1("NO.53 JALAN SAGU", EXPECTED["entities"]["address"]),
        )


if __name__ == "__main__":
    unittest.main()
