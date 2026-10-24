# Results

Status: **filled from the Colab run** (24 October 2026). Numbers come from `results/comparison.csv` and `results/settings.json`.

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
| Image max side | 1024 px |
| Training rows | 625 usable of 626 train receipts |
| Evaluation sample | 100 frozen test receipts, seed 0 (`data/eval_keys_seed0.json`) |
| GPU | Colab free T4 |
| Adapters | `adapters/campusclaim_gemma4_lora/` |

On a T4, Unsloth runs Gemma 4 in float32 because float16 produces NaN gradients. That is expected; the baseline and fine-tuned runs use the same setting, so the comparison is still like-for-like. It is also why the image side is 1024 px and the batch size is 1.

## Metrics

| Metric | Plain Gemma | Fine-tuned | Change |
|---|---|---|---|
| Valid JSON | 100.0% | 100.0% | +0.0 |
| Company exact | 79.0% | 85.0% | +6.0 |
| Date exact | 85.0% | 96.0% | +11.0 |
| Address exact | 60.0% | 79.0% | +19.0 |
| Total exact | 90.0% | 95.0% | +5.0 |
| Address token-F1 | 89.3% | 96.4% | +7.1 |

Copied from `results/comparison.csv`. Do not round differently from the notebook.

## Failure examples

33 of 100 receipts still had at least one wrong field after fine-tuning. Five examples:

| Receipt key | Expected | Predicted (fine-tuned) | Cause |
|---|---|---|---|
| `X51006008090` | total `30.50` | total `30.48` | Near-miss total (likely tax/rounding on the scan) |
| `X51006334927` | company `BIRU PETROLEUM`, date `11/11/16`, total `6.40` | `BIRU PETROLEUM CO.`, date `11/16`, total `6.04` | Truncated date + wrong total |
| `X51005361908` | company `TEO HENG…` | `TED HENG…` | OCR-style company typo (O→D) |
| `X51005587261` | company `CHOP YEW LIAN` | `COMPANY NO : 000200101-A` | Picked registration line instead of shop name |
| `X00016469670` | address `…B1750 MASAI…` | `…81750 MASAI…` | Exact address miss; token-F1 still high |

Wrong totals must block automatic approval even when the other fields look fine.

## Local campus receipts

Report 3–5 real campus receipts separately. Do **not** pool them with the SROIE numbers: the receipts are a different country, currency and layout.

| Receipt | Fields correct | Notes |
|---|---|---|
| — | — | — |

## Adapters

- Path: `adapters/campusclaim_gemma4_lora/` (weights via Git LFS: `adapter_model.safetensors`)
- Reload: `python -m app.gradio_app --no-dummy --base-model-id unsloth/gemma-4-E2B-it --adapter-path adapters/campusclaim_gemma4_lora`
