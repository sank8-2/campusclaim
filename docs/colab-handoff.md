# Colab handoff

The **shared Colab notebook is the submission**. `notebooks/campusclaim_3b.ipynb` in this repo is the versioned copy — do not treat the repo copy as the deliverable.

Before uploading, run `python3 scripts/validate_notebook.py`. If a cell fails in Colab, check [troubleshooting.md](troubleshooting.md) before changing the notebook.

## M1: first run

1. Open the [Theme 3 starter](https://colab.research.google.com/github/mithun-srinivas/HacktoberFest-HackDay/blob/main/templates/03_fine_tuning_starter_kit.ipynb), choose *File → Save a copy in Drive*, and rename it `CampusClaim 3B`.
2. Upload `notebooks/campusclaim_3b.ipynb` with *File → Upload notebook*, or paste its cells into the shared doc.
3. Set *Runtime → Change runtime type → T4 GPU*.
4. Run every cell top to bottom. The install cell takes 2–4 minutes.
5. At the end, download `results/` and `campusclaim_gemma4_lora.zip` from the Colab file browser, then commit the results to this repo (or hand them to M2).

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
