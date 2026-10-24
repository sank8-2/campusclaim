# Results

Status: **pending**. M1 records the run settings; M2 fills the metrics and failures from the notebook's `results/` folder.

M2 does not type these numbers by hand. Once `results/` is in the repo root:

```bash
python3 scripts/build_results.py --results results          # rewrites this file
python3 scripts/build_results.py --results results --check  # verify only
```

The script recomputes every metric from `baseline_predictions.csv` and `tuned_predictions.csv` with `scripts/score.py`, and refuses to write when the recomputed numbers disagree with `comparison.csv`/`*_metrics.json`, when the two runs did not use the same frozen 100 keys, or when a key is outside `data/eval_keys_seed0.json`.

## Run settings

| Setting | Value |
|---|---|
| Model | `unsloth/gemma-4-E2B-it` |
| Quantisation | 4-bit |
| LoRA rank / alpha | 16 / 16 |
| Vision layers | trained |
| Training steps | 120 |
| Batch / gradient accumulation | 1 / 4 |
| Learning rate | 2e-4 |
| Max sequence length | 2048 |
| Image max side | 1600 px |
| Evaluation sample | 100 frozen test receipts, seed 0 (`data/eval_keys_seed0.json`) |
| GPU | Colab free T4 |

## Metrics

| Metric | Plain Gemma | Fine-tuned | Change |
|---|---|---|---|
| Valid JSON | — | — | — |
| Company exact | — | — | — |
| Date exact | — | — | — |
| Address exact | — | — | — |
| Total exact | — | — | — |
| Address token-F1 | — | — | — |

Filled by `scripts/build_results.py` from the raw predictions. Do not round differently from the notebook.

## Scoring verification

The scoring cell was checked on the four cases the issue asks for:

| Case | Expected result | Test |
|---|---|---|
| Perfect JSON | all fields 1 | `test_perfect_json_scores_every_field` |
| Normalised (case / `RM` / date format) | all fields 1 | `test_case_currency_and_date_format_are_normalised` |
| Wrong fields | all fields 0 | `test_wrong_fields_score_zero` |
| Prose, no JSON | `valid_json` 0 and all fields 0 | `test_prose_is_invalid_json` |

`tests/test_notebook_scoring.py` runs the same four cases against the notebook's own scoring cell, so the copy in `scripts/score.py` cannot drift from what Colab executes.

## Failure examples

| Receipt key | Wrong fields (expected → predicted) | Cause |
|---|---|---|
| — | — | — |

Built from the same predictions: five receipts with at least one wrong field, and a cause (blur, crop, currency, date format, hallucinated total, missing line item).

## Local campus receipts

Report 3–5 real campus receipts separately. Do **not** pool them with the SROIE numbers: the receipts are a different country, currency and layout.

| Receipt | Fields correct | Notes |
|---|---|---|
| — | — | — |

## Adapters

- `campusclaim_gemma4_lora.zip` — Drive link: _pending_
- Reload tested on a fresh runtime: _pending_
