"""Field-level scoring for SROIE receipt extraction.

This is the local, dependency-free copy of the notebook's Step 3 scoring cell.
Keep the two in sync: if you change a normaliser here, change it in
`notebooks/campusclaim_3b.ipynb` as well.

Run the self-test with:

    python3 -m unittest discover -s tests -v
"""

import json
import re
from collections import Counter

FIELDS = ["company", "date", "address", "total"]
MONTHS = {
    month: index
    for index, month in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
        start=1,
    )
}


def parse_json(text):
    """Return the first JSON object in a model reply, or None."""
    match = re.search(r"\{.*?\}", text or "", re.DOTALL)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def norm_text(value):
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def norm_date(value):
    text = str(value or "").strip().lower()
    match = re.match(r"^(\d{1,2})[\s/-]+([a-z]{3})[a-z]*[\s/-]+(\d{2,4})$", text)
    if match:
        day, month, year = match.groups()
        year = ("20" + year) if len(year) == 2 else year
        return f"{int(day):02d}/{MONTHS[month]:02d}/{year}"
    digits = re.findall(r"\d+", text)
    if len(digits) == 3:
        day, month, year = digits
        year = ("20" + year) if len(year) == 2 else year
        return f"{int(day):02d}/{int(month):02d}/{year}"
    return "/".join(digits)


def norm_total(value):
    match = re.search(r"-?\d+(?:\.\d+)?", str(value or "").replace(",", ""))
    return float(match.group(0)) if match else None


def token_f1(prediction, expected):
    predicted = norm_text(prediction).split()
    gold = norm_text(expected).split()
    if not predicted and not gold:
        return 1.0
    if not predicted or not gold:
        return 0.0
    common = sum((Counter(predicted) & Counter(gold)).values())
    if common == 0:
        return 0.0
    precision, recall = common / len(predicted), common / len(gold)
    return 2 * precision * recall / (precision + recall)


def score(prediction, entities):
    """Score one model reply against one SROIE `entities` dict.

    Returns 0/1 for each field plus the address token-F1. A reply with no JSON
    is a total failure, which is the point of reporting `valid_json` separately.
    """
    predicted = parse_json(prediction)
    if predicted is None:
        return {
            "valid_json": 0,
            "company": 0,
            "date": 0,
            "address": 0,
            "total": 0,
            "address_f1": 0.0,
        }

    predicted_total = norm_total(predicted.get("total"))
    expected_total = norm_total(entities.get("total"))
    total_match = (
        predicted_total is not None
        and expected_total is not None
        and abs(predicted_total - expected_total) <= 0.01
    )

    return {
        "valid_json": 1,
        "company": int(norm_text(predicted.get("company")) == norm_text(entities.get("company"))),
        "date": int(norm_date(predicted.get("date")) == norm_date(entities.get("date"))),
        "address": int(norm_text(predicted.get("address")) == norm_text(entities.get("address"))),
        "total": int(total_match),
        "address_f1": token_f1(predicted.get("address"), entities.get("address")),
    }


if __name__ == "__main__":
    example = {
        "company": "BOOK TA .K (TAMAN DAYA) SDN BHD",
        "date": "25/12/2018",
        "address": "NO.53 55,57 & 59, JALAN SAGU 18, TAMAN DAYA, 81100 JOHOR BAHRU, JOHOR.",
        "total": "9.00",
    }
    print(json.dumps(score(json.dumps(example), example), indent=2))
