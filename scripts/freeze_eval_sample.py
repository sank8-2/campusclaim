#!/usr/bin/env python3
"""Freeze the SROIE test manifest and the 100-receipt evaluation sample.

Uses the Hugging Face datasets-server rows API, so it never downloads the
510 MB image archive. Run from the repo root:

    python3 scripts/freeze_eval_sample.py

The output is deterministic: same dataset, same filter, same seed -> same keys.
"""

import json
import random
import urllib.request
from pathlib import Path

DATASET = "jsdnrs/ICDAR2019-SROIE"
SPLIT_SIZES = {"train": 626, "test": 361}
FIELDS = ["company", "date", "address", "total"]
SEED = 0
N_EVAL = 100
ROWS_URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=jsdnrs%2FICDAR2019-SROIE&config=default&split={split}"
    "&offset={offset}&length=100"
)


def fetch_rows(split: str, total: int) -> list[dict]:
    rows: list[dict] = []
    for offset in range(0, total, 100):
        url = ROWS_URL.format(split=split, offset=offset)
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = json.load(response)
        rows.extend(item["row"] for item in payload["rows"])
    if len(rows) != total:
        raise RuntimeError(f"{split}: expected {total} rows, got {len(rows)}")
    return rows


def usable(row: dict) -> bool:
    entities = row.get("entities") or {}
    return all(str(entities.get(field, "")).strip() for field in FIELDS)


def to_manifest(rows: list[dict]) -> list[dict]:
    return [
        {"key": row["key"], "entities": {field: row["entities"][field] for field in FIELDS}}
        for row in rows
        if usable(row)
    ]


def main() -> None:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    test_rows = to_manifest(fetch_rows("test", SPLIT_SIZES["test"]))
    train_rows = to_manifest(fetch_rows("train", SPLIT_SIZES["train"]))

    eval_keys = [row["key"] for row in random.Random(SEED).sample(test_rows, N_EVAL)]

    (data_dir / "sroie_test_manifest.json").write_text(
        json.dumps(
            {
                "dataset": DATASET,
                "split": "test",
                "fields": FIELDS,
                "total_rows": SPLIT_SIZES["test"],
                "usable_rows": len(test_rows),
                "rows": test_rows,
            },
            indent=2,
        )
        + "\n"
    )
    (data_dir / "eval_keys_seed0.json").write_text(
        json.dumps(
            {
                "dataset": DATASET,
                "split": "test",
                "seed": SEED,
                "count": N_EVAL,
                "note": "Frozen for both the plain and the fine-tuned run. Do not resample.",
                "keys": eval_keys,
            },
            indent=2,
        )
        + "\n"
    )

    print(f"train usable: {len(train_rows)}/{SPLIT_SIZES['train']}")
    print(f"test usable:  {len(test_rows)}/{SPLIT_SIZES['test']}")
    print(f"eval sample:  {len(eval_keys)} keys (seed {SEED})")
    print("wrote data/sroie_test_manifest.json and data/eval_keys_seed0.json")


if __name__ == "__main__":
    main()
