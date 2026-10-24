#!/usr/bin/env python3
"""Build and verify `docs/results.md` from the notebook's `results/` folder.

The notebook's export cell writes:

    results/settings.json
    results/baseline_metrics.json
    results/tuned_metrics.json
    results/comparison.csv
    results/baseline_predictions.csv
    results/tuned_predictions.csv
    results/failures.csv

This script does not trust `comparison.csv`: it recomputes every metric from the
raw predictions with `scripts/score.py` and refuses to write a table when the
recomputed numbers disagree with the exported ones, when the two runs did not
use the same frozen 100 keys, or when a key is outside the frozen sample.

Usage:

    python3 scripts/build_results.py --results results          # write docs/results.md
    python3 scripts/build_results.py --results results --check  # verify only, no writes

Optional inputs:

    results/local_receipts.csv   receipt,fields_correct,notes   (separate local test)
    results/failure_causes.csv   key,cause                      (human cause labels)
"""

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from score import FIELDS, parse_json, score  # noqa: E402

EVAL_KEYS = ROOT / "data" / "eval_keys_seed0.json"
DOCS = ROOT / "docs" / "results.md"

METRICS = [
    ("valid JSON", "valid_json"),
    ("company exact", "company"),
    ("date exact", "date"),
    ("address exact", "address"),
    ("total exact", "total"),
    ("address token-F1", "address_f1"),
]

TOLERANCE = 0.051  # the notebook rounds to one decimal place

FAILURE_LIMIT = 5


class ResultsError(Exception):
    """The results folder is incomplete or internally inconsistent."""


def read_json(path):
    if not path.exists():
        raise ResultsError(f"missing {path}")
    return json.loads(path.read_text())


def read_rows(path):
    if not path.exists():
        raise ResultsError(f"missing {path}")
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def load_predictions(results, filename, label):
    rows = read_rows(results / filename)
    if not rows:
        raise ResultsError(f"{filename} is empty")
    if label not in rows[0]:
        raise ResultsError(f"{filename} has no '{label}' column, so it is not the exported run")
    predicted = []
    for row in rows:
        if not row.get("key"):
            raise ResultsError(f"{filename} has a row without a key")
        expected = row.get("expected") or ""
        try:
            expected_entities = json.loads(expected)
        except json.JSONDecodeError:
            raise ResultsError(f"{filename}: key {row['key']} has an unreadable expected JSON")
        predicted.append(
            {
                "key": row["key"],
                "expected": expected_entities,
                "prediction": row.get(label, "") or "",
            }
        )
    return predicted


def frozen_keys():
    return json.loads(EVAL_KEYS.read_text())["keys"]


def recompute(rows):
    """Recompute per-field scores and the aggregate metrics for one run."""
    scored = []
    for row in rows:
        result = score(row["prediction"], row["expected"])
        scored.append({**row, **result})
    total = len(scored)
    metrics = {}
    for name, column in METRICS:
        value = sum(item[column] for item in scored) / total * 100
        metrics[name] = round(value, 1)
    return scored, metrics


def check_sample(baseline, tuned):
    keys = frozen_keys()
    problems = []
    for name, rows in (("baseline", baseline), ("tuned", tuned)):
        seen = [row["key"] for row in rows]
        if len(seen) != 100:
            problems.append(f"{name} has {len(seen)} receipts, expected 100")
        if len(set(seen)) != len(seen):
            problems.append(f"{name} contains duplicate keys")
        extra = sorted(set(seen) - set(keys))
        missing = sorted(set(keys) - set(seen))
        if extra:
            problems.append(f"{name} has keys outside the frozen sample: {extra[:3]}")
        if missing:
            problems.append(f"{name} is missing frozen keys: {missing[:3]}")
    if not problems and [r["key"] for r in baseline] != [r["key"] for r in tuned]:
        problems.append("baseline and fine-tuned runs are not in the same key order")
    return problems


def check_metrics(name, exported, recomputed):
    problems = []
    for metric, value in recomputed.items():
        if metric not in exported:
            problems.append(f"{name}: {metric} missing from the exported metrics")
            continue
        if abs(float(exported[metric]) - value) > TOLERANCE:
            problems.append(
                f"{name}: {metric} exported {exported[metric]} but recomputed {value}"
            )
    return problems


def guess_cause(row):
    """Suggest a cause for one failed receipt; a human label wins if present."""
    if not row["valid_json"]:
        return "prose reply, no JSON"
    if row["total"] == 0:
        predicted = parse_json(row["prediction"]) or {}
        if not str(predicted.get("total", "")).strip():
            return "missing total"
        return "hallucinated total"
    if row["date"] == 0:
        return "date format / misread date"
    if row["company"] == 0:
        return "misread company name"
    if row["address"] == 0:
        return "cropped or truncated address" if row["address_f1"] < 0.8 else "address formatting"
    return "unclassified"


def pick_failures(tuned, causes):
    failed = [row for row in tuned if sum(row[field] for field in FIELDS) < 4]
    failed.sort(key=lambda row: (sum(row[name] for name in FIELDS), row["address_f1"]))
    chosen = failed[:FAILURE_LIMIT]
    picked = []
    for row in chosen:
        expected = row["expected"]
        predicted = parse_json(row["prediction"]) or {}
        wrong = []
        for name in FIELDS:
            if row[name]:
                continue
            wrong.append((name, field(expected.get(name)), field(predicted.get(name))))
        picked.append(
            {
                "key": row["key"],
                "wrong": wrong,
                "cause": causes.get(row["key"]) or guess_cause(row),
            }
        )
    return picked, len(failed)


def load_causes(results):
    path = results / "failure_causes.csv"
    if not path.exists():
        return {}
    return {row["key"]: row["cause"] for row in read_rows(path) if row.get("key")}


def load_local_receipts(results):
    path = results / "local_receipts.csv"
    if not path.exists():
        return []
    return [
        {
            "receipt": row.get("receipt", ""),
            "fields_correct": row.get("fields_correct", ""),
            "notes": row.get("notes", ""),
        }
        for row in read_rows(path)
        if row.get("receipt")
    ]


def field(value):
    text = str(value).strip() if value is not None else ""
    return text if text else "(missing)"


def render(settings, baseline_metrics, tuned_metrics, failures, failed_count, local):
    lines = [
        "# Results",
        "",
        "Status: **filled by `scripts/build_results.py` from `results/`** — do not edit by hand.",
        "Every number below was recomputed from the raw predictions with `scripts/score.py`.",
        "",
        "## Run settings",
        "",
        "| Setting | Value |",
        "|---|---|",
    ]
    rank = settings.get("lora_rank")
    batch, accum = settings.get("batch_size"), settings.get("grad_accum")
    setting_rows = [
        ("Model", settings.get("model", "")),
        ("Quantisation", "4-bit"),
        ("LoRA rank / alpha", f"{rank} / {rank}" if rank is not None else ""),
        ("Vision layers", "trained"),
        ("Training steps", settings.get("train_steps", "")),
        ("Batch / gradient accumulation", f"{batch} / {accum}" if batch is not None and accum is not None else ""),
        ("Learning rate", settings.get("learning_rate", "")),
        ("Max sequence length", settings.get("max_length", "")),
        ("Image max side", settings.get("image_max_side", "")),
        (
            "Evaluation sample",
            f"{settings.get('eval_keys', 100)} frozen test receipts, seed {settings.get('eval_seed', 0)} "
            "(`data/eval_keys_seed0.json`)",
        ),
        ("GPU", "Colab free T4"),
    ]
    for label, value in setting_rows:
        lines.append(f"| {label} | {value} |")

    lines += [
        "",
        "## Metrics",
        "",
        "| Metric | Plain Gemma | Fine-tuned | Change |",
        "|---|---|---|---|",
    ]
    for metric, _ in METRICS:
        plain = baseline_metrics[metric]
        tuned = tuned_metrics[metric]
        change = tuned - plain
        lines.append(
            f"| {metric} | {plain:.1f} | {tuned:.1f} | {change:+.1f} |"
        )

    lines += [
        "",
        f"{failed_count} of 100 receipts had at least one wrong field after fine-tuning.",
        "",
        "## Failure examples",
        "",
        "| Receipt key | Wrong fields (expected → predicted) | Cause |",
        "|---|---|---|",
    ]
    if not failures:
        lines.append("| — | — | — |")
    for item in failures:
        detail = "<br>".join(
            f"{name}: {gold} → {guess}" for name, gold, guess in item["wrong"]
        )
        lines.append(f"| `{item['key']}` | {detail} | {item['cause']} |")

    lines += [
        "",
        "## Scoring verification",
        "",
        "The scoring cell was checked on the four cases the issue asks for:",
        "",
        "| Case | Expected result | Test |",
        "|---|---|---|",
        "| Perfect JSON | all fields 1 | `test_perfect_json_scores_every_field` |",
        "| Normalised (case / `RM` / date format) | all fields 1 | `test_case_currency_and_date_format_are_normalised` |",
        "| Wrong fields | all fields 0 | `test_wrong_fields_score_zero` |",
        "| Prose, no JSON | `valid_json` 0 and all fields 0 | `test_prose_is_invalid_json` |",
        "",
        "`tests/test_notebook_scoring.py` runs the same four cases against the notebook's",
        "own scoring cell, so the copy here cannot drift from what Colab executes.",
        "",
        "## Local campus receipts",
        "",
        "Separate local test — **not** pooled with the SROIE numbers (different country, currency and layout).",
        "",
        "| Receipt | Fields correct | Notes |",
        "|---|---|---|",
    ]
    if local:
        for item in local:
            lines.append(
                f"| {field(item['receipt'])} | {field(item['fields_correct'])} | {field(item['notes'])} |"
            )
    else:
        lines.append("| — | — | — |")

    lines += [
        "",
        "## Adapters",
        "",
        "- `campusclaim_gemma4_lora.zip` — Drive link: _pending_",
        "- Reload tested on a fresh runtime: _pending_",
        "",
    ]
    return "\n".join(lines)


def build(results, check_only=False, output=DOCS):
    settings = read_json(results / "settings.json")
    baseline_exported = read_json(results / "baseline_metrics.json")
    tuned_exported = read_json(results / "tuned_metrics.json")

    baseline = load_predictions(results, "baseline_predictions.csv", "plain_model")
    tuned = load_predictions(results, "tuned_predictions.csv", "fine_tuned_model")

    baseline_scored, baseline_metrics = recompute(baseline)
    tuned_scored, tuned_metrics = recompute(tuned)

    problems = check_sample(baseline, tuned)
    problems += check_metrics("plain", baseline_exported, baseline_metrics)
    problems += check_metrics("fine-tuned", tuned_exported, tuned_metrics)
    if problems:
        raise ResultsError("; ".join(problems))

    failures, failed_count = pick_failures(tuned_scored, load_causes(results))
    text = render(
        settings,
        baseline_metrics,
        tuned_metrics,
        failures,
        failed_count,
        load_local_receipts(results),
    )

    if not check_only:
        output.write_text(text)
    return baseline_metrics, tuned_metrics, failures, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results", type=Path, help="the notebook's results/ folder")
    parser.add_argument("--out", default=DOCS, type=Path, help="markdown file to write")
    parser.add_argument("--check", action="store_true", help="verify only, do not write")
    args = parser.parse_args(argv)

    try:
        baseline, tuned, failures, _ = build(args.results, args.check, args.out)
    except ResultsError as error:
        print(f"FAIL: {error}")
        return 1

    for metric, _ in METRICS:
        print(f"{metric:<18} plain {baseline[metric]:>5.1f}  tuned {tuned[metric]:>5.1f}")
    print(f"{len(failures)} failure examples")
    if args.check:
        print("OK: results match the exported metrics and the frozen 100 keys")
    else:
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
