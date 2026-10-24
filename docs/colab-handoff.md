# Colab handoff

The **shared Colab notebook is the submission**. `notebooks/campusclaim_3b.ipynb` in this repo is the versioned copy — do not treat the repo copy as the deliverable.

`dev` is the integration branch for this repo: local app changes, tests and CI land on `dev` first, and `main` holds the submitted baseline. Do not push to `main` directly.

GPU work stays in Colab. The install cell, model load, LoRA training, evaluation and the notebook's Gradio cell all need a T4 and are **not** runnable in this checkout. The local checks (`bash scripts/check.sh`) and the offline demo (`python3 scripts/demo_pipeline.py`) are CPU-only and must stay green before you upload the notebook.

Before uploading, run `python3 scripts/validate_notebook.py`. If a cell fails in Colab, check [troubleshooting.md](troubleshooting.md) before changing the notebook.

## M1: first run

The notebook is now split into a smoke test and the expensive run. Do not run the 100-receipt baseline or training until the smoke test prints JSON.

1. Open the [Theme 3 starter](https://colab.research.google.com/github/mithun-srinivas/HacktoberFest-HackDay/blob/main/templates/03_fine_tuning_starter_kit.ipynb), choose *File → Save a copy in Drive*, and rename it `CampusClaim 3B`.
2. Upload `notebooks/campusclaim_3b.ipynb` with *File → Upload notebook*, or paste its cells into the shared doc.
3. Set *Runtime → Change runtime type → T4 GPU*.
4. Run the install cell (2–4 minutes), then the GPU check and the model-load cell. The model-load cell prints `Unsloth: Using float16 precision for gemma4 won't work! Using float32.` — that is expected on a T4, not an error.
5. Run the dataset cell and the one-receipt smoke test only. The smoke test should print the receipt key, the expected fields, and a JSON prediction.
6. If the smoke test prints JSON, run the baseline, the LoRA cell, training, the fine-tuned evaluation, the failure table, and the export cell. If the runtime restarts instead, stop and use [troubleshooting.md](troubleshooting.md); do not re-run the model-load cell after a crash.
7. Download `results/` and `campusclaim_gemma4_lora.zip` from the Colab file browser, then commit the results to this repo (or hand them to M2).

The training cell builds a `datasets.Dataset` with `messages` and `images` columns. The image bytes stay encoded in Arrow and are decoded one batch at a time; do not replace this with a Python list or a `torch.utils.data.Dataset`.

## Handoffs

| Who | Needs | From |
|---|---|---|
| M2 | `results/baseline_predictions.csv`, `tuned_predictions.csv`, `comparison.csv`, `failures.csv`, `settings.json` | The export cell after Step 5 |
| M3 | The Gradio cell; the app runs in the live session | Step 6 |
| M4 | A **second** notebook for policy RAG; do not add it to the GPU notebook | Theme 2 starter |
| M5 | `settings.json` and `comparison.csv`; these are the only numbers for the deck | M2 after verification |

## If Colab disconnects

1. Reload the base model (`FastVisionModel.from_pretrained`).
2. Load the adapters from the zip in Drive.
3. Rerun only the evaluation and app cells.

Keep the adapter zip in Drive immediately after training; free Colab can disconnect without warning.

## Editing rules

- Only M1 edits the shared notebook.
- Everyone else puts proposed cells in a `SCRATCH` section at the bottom.
- The eval sample is frozen in `data/eval_keys_seed0.json`; do not resample it mid-run.
