# campusclaim
Receipt-to-reimbursement assistant for campus events using Gemma vision fine-tuning, policy RAG, and open-model evaluation.

Primary hackathon theme: **3B — Receipt Information Extraction**, supported by **2A — Campus Regulations RAG** and **1 — Open Model Evaluation**.

See [the theme selection discussion](docs/theme-selection.md) for the alternatives considered, decision rationale, project scope, evaluation plan, and tradeoffs.

See [the Laya integration plan](docs/laya-integration.md) for the proposed decision layer inspired by Jev-style workflows: request routing, evidence checks, review handoffs, and evaluation.

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
