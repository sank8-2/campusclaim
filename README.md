# campusclaim

Receipt-to-reimbursement assistant for campus events, built on Gemma 4 vision fine-tuning.

Hackathon submission: **Theme 3B — Receipt Information Extraction**. Policy retrieval is kept as the 3B *"combined approach"* bonus; the Theme 1 scorecard and the Laya layer are out of scope. See [the theme decision](docs/theme-selection.md) and [the team plan](docs/team-plan.md).

## Repository map

| Path | What it is |
|---|---|
| `notebooks/campusclaim_3b.ipynb` | The 3B working notebook. Upload it to Colab; the **shared Colab doc is the submission**. |
| `data/sroie_test_manifest.json` | The 361 test receipts' keys and labels (no images). |
| `data/eval_keys_seed0.json` | The frozen 100-receipt evaluation sample. |
| `scripts/freeze_eval_sample.py` | Regenerates the manifest and the frozen sample from the HF rows API. |
| `scripts/score.py` | Field-level scoring used by the notebook and the tests. |
| `tests/test_scoring.py` | 8 unit tests for the normalisers and scoring. |
| `docs/team-plan.md` | Roles, timeline, checkpoints, cut lines, rubric. |
| `docs/colab-handoff.md` | How to run the notebook and hand results to M2–M5. |
| `docs/results.md` | Settings, metrics and failure examples (filled during the run). |

## Quick checks

```bash
python3 scripts/freeze_eval_sample.py       # rebuild data/ (network, no images)
python3 -m unittest discover -s tests -v    # scoring tests
```

## Status

- [x] Theme 3B confirmed, single theme
- [x] Team roles assigned in the [Hack Day 3B milestone](https://github.com/sank8-2/campusclaim/milestone/1)
- [x] Frozen 100-receipt evaluation sample
- [ ] Baseline on the frozen sample
- [ ] LoRA fine-tune and comparison
- [ ] App and backup demo
- [ ] Policy RAG bonus (only after CP1)

## Gradio app (M3)

Run the baseline skeleton app:

```bash
pip install -r requirements.txt
python -m app.gradio_app
```

The default run mode uses dummy JSON so the upload → extract → edit → claim draft flow works immediately.

To use a saved adapter state (instead of a live training session), start with:

```bash
python -m app.gradio_app --no-dummy --base-model-id <base-model> --adapter-path <saved-adapter-dir>
```

Then pass your project inference callable when launching from Python so plain extraction uses `model.disable_adapter()` and tuned extraction uses the active adapter.

Screenshot checklist: `screenshots/README.md`  
Demo and backup clip checklist: `docs/demo-script.md`
