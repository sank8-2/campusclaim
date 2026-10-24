# Results

Status: **pending**. M1 records the run settings; M2 fills the metrics and failures from the notebook's `results/` folder.

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

Copy the numbers from `results/comparison.csv`. Do not round differently from the notebook.

## Failure examples

| Receipt key | Expected | Predicted | Cause |
|---|---|---|---|
| — | — | — | — |

Pick five from `results/failures.csv` and name the cause (blur, crop, currency, date format, hallucinated total, missing line item).

## Local campus receipts

Report 3–5 real campus receipts separately. Do **not** pool them with the SROIE numbers: the receipts are a different country, currency and layout.

| Receipt | Fields correct | Notes |
|---|---|---|
| — | — | — |

## Adapters

- `campusclaim_gemma4_lora.zip` — Drive link: _pending_
- Reload tested on a fresh runtime: _pending_
