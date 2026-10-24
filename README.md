# campusclaim

Receipt-to-reimbursement assistant for campus events, built on Gemma 4 vision fine-tuning.

Hackathon submission: **Theme 3B — Receipt Information Extraction**. Policy retrieval is kept as the 3B *"combined approach"* bonus; the Theme 1 scorecard and the Laya layer are out of scope. See [the theme decision](docs/theme-selection.md) and [the team plan](docs/team-plan.md).

## Dataset

[`jsdnrs/ICDAR2019-SROIE`](https://huggingface.co/datasets/jsdnrs/ICDAR2019-SROIE) — ICDAR 2019 SROIE receipts, **CC-BY-4.0**.

- 987 rows: **626 train**, **361 test**.
- Fields: `image`, `key`, `image_size`, `entities` (`company`, `date`, `address`, `total`), `words`, `bboxes`.
- Training uses `image` + `entities`; `words` and `bboxes` are unused (they would make an OCR baseline, not vision fine-tuning).
- One train row has an empty `total`, so **625 of 626** are usable; all **361 test** rows are usable.
- The receipts are Malaysian, so the SROIE score is not a campus-receipt score. Real campus receipts are reported separately in [results.md](docs/results.md).

## Branches

`dev` is the integration branch: local work, the app, the demo pipeline and CI land there first. `main` holds the submitted baseline. Push to `dev`; never push directly to `main`.

The GPU cells (install, model load, LoRA training, evaluation, the notebook's Gradio cell) run only in Colab on a T4. Everything in `scripts/` and `tests/` runs locally on the standard library.

## Repository map

| Path | What it is |
|---|---|
| `notebooks/campusclaim_3b.ipynb` | The 3B working notebook. Upload it to Colab; the **shared Colab doc is the submission**. |
| `data/sroie_test_manifest.json` | The 361 test receipts' keys and labels (no images). |
| `data/eval_keys_seed0.json` | The frozen 100-receipt evaluation sample. |
| `data/demo_receipt.json` | Label-only receipt fixture for the offline demo (no image data). |
| `scripts/freeze_eval_sample.py` | Regenerates the manifest and the frozen sample from the HF rows API. |
| `scripts/score.py` | Field-level scoring used by the notebook and the tests. |
| `scripts/validate_notebook.py` | Pre-flight: compiles the notebook and checks the frozen keys and required cells. |
| `scripts/demo_pipeline.py` | Offline dummy run: extract → prefill → claim draft → `results/demo_report.json`. |
| `scripts/check.sh` | Runs the validator and the test suite from the repo root (same as CI). |
| `app/inference.py` | Notebook-mirroring inference adapter: `build_infer_fn` and `parse_receipt_json`. |
| `app/gradio_app.py` | Standalone app. Dummy mode by default; real adapters via `--no-dummy`. |
| `tests/test_scoring.py` | 8 unit tests for the normalisers and scoring. |
| `tests/test_gradio_app.py` | 12 unit tests for prefill, claim draft, adapter handling and CLI wiring. |
| `tests/test_inference.py` | 14 unit tests for JSON parsing, the processor/generation calls and import safety. |
| `tests/test_demo_pipeline.py` | 5 unit tests for the demo report. |
| `.github/workflows/ci.yml` | CI on pushes and pull requests to `dev` and `main`. |
| `scripts/fetch_rag_docs.py` | Downloads the two policy PDFs into the git-ignored `data/rag/source/` and verifies checksums. |
| `scripts/check_rag_docs.py` | Checks that the policy PDFs are text-based, not scans. |
| `docs/rag-documents.md` | The two shortlisted policy documents, their URLs and page map (pre-CP1). |
| `docs/rag-eval.md` | The 15-question policy test (10 covered, 5 refusals). |
| `data/rag/questions.json` | Machine-readable copy of the 15-question test. |
| `docs/team-plan.md` | Roles, timeline, checkpoints, cut lines, rubric. |
| `docs/colab-handoff.md` | How to run the notebook and hand results to M2–M5. |
| `docs/results.md` | Settings, metrics and failure examples (filled during the run). |
| `docs/troubleshooting.md` | Common Colab failures and the OOM fallback. |

## Quick checks

```bash
bash scripts/check.sh                       # validator + tests (the same commands CI runs)
python3 scripts/validate_notebook.py        # notebook syntax + frozen keys
python3 -m unittest discover -s tests -v    # 40 tests, standard library only
python3 scripts/demo_pipeline.py            # offline demo; writes results/demo_report.json
python3 scripts/freeze_eval_sample.py       # rebuild data/ (network, no images)
```

## Status

- [x] Theme 3B confirmed, single theme
- [x] Team roles assigned in the [Hack Day 3B milestone](https://github.com/sank8-2/campusclaim/milestone/1)
- [x] Frozen 100-receipt evaluation sample
- [x] App real-inference path and offline demo pipeline (dummy mode verified locally)
- [ ] Baseline on the frozen sample (Colab GPU)
- [ ] LoRA fine-tune and comparison (Colab GPU)
- [x] App screenshots and capture script (backup clips pending share links; re-record with the real adapter after CP1)
- [ ] Policy RAG bonus (only after CP1)

## Gradio app (M3)

Run the app in dummy mode (no model, no GPU, no network):

```bash
pip install -r requirements.txt
python -m app.gradio_app
```

The default uses dummy JSON so the upload → extract → edit → claim draft flow works immediately.

To use a saved adapter state instead of a live training session:

```bash
python -m app.gradio_app --no-dummy \
  --base-model-id unsloth/gemma-4-E2B-it \
  --adapter-path campusclaim_gemma4_lora
```

`--no-dummy` loads the base model with `PeftModel`, loads the processor with `AutoProcessor`, and uses `app.inference.build_infer_fn`, which mirrors the notebook's `generate_from_image` (same instruction, chat template, image downscale and greedy decode). Plain extraction runs with `model.disable_adapter()`; tuned extraction runs with the adapter active.

To plug in a project-specific inference callable, pass a factory as `module:function`. It is called with `(model, processor)` and must return a callable `(model, image) -> dict`:

```bash
python -m app.gradio_app --no-dummy \
  --base-model-id unsloth/gemma-4-E2B-it \
  --adapter-path campusclaim_gemma4_lora \
  --inference-module my_project.inference:build_infer
```

`--no-dummy` without `--base-model-id` and `--adapter-path` fails before launch with a clear `ValueError`.

This standalone app is a **fallback** for the demo; the primary demo is the Gradio cell in the notebook. The GPU cells still run in Colab — this repo's checks and the demo pipeline stay CPU-only.

## Offline demo

```bash
python3 scripts/demo_pipeline.py
```

Runs the same service → extract → prefill → claim draft path as the app using the dummy extractors and `data/demo_receipt.json`, prints a summary, and writes `results/demo_report.json`. It is the dry run to do before recording the backup clip.

Screenshot checklist: `screenshots/README.md`  
Demo and backup clip checklist: `docs/demo-script.md`
