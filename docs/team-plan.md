# CampusClaim team plan — 5 members

Status: confirmed 24 October 2026. Submit **Theme 3B only** (receipt information extraction). The policy assistant is the 3B *"combined approach"* bonus, not a second theme. The Theme 1 four-model scorecard and the Laya decision layer are out of scope for the hack day.

Source: [HacktoberFest-HackDay problem statements](https://github.com/mithun-srinivas/HacktoberFest-HackDay/blob/main/PROBLEM_STATEMENTS.md) — one theme per team, one problem statement within the theme.

## Roles

| Member | Role | Owns | First task | Deliverable |
|---|---|---|---|---|
| **M1** (sank8-2) | Lead + notebook driver | The shared Colab notebook, training runs, adapter saves | Open the Theme 3 starter, save a copy to Drive, select T4, run install + GPU check | A notebook that runs top to bottom and a saved adapter zip |
| **M2** | Data + evaluation | Fixed eval sample, scoring, metrics, failure analysis | Generate the 100-receipt eval keys (seed 0) and the metrics sheet | Comparison table + 5 worked failure examples + local-receipt note |
| **M3** | App + demo | Gradio app, backup video, screenshots | Build the app skeleton with the four fields and claim draft | Live demo + 2-minute backup video |
| **M4** | Policy RAG (starts at Checkpoint 1) | Two official documents, citations, refusal test | Shortlist two text-based official finance/activity PDFs | RAG tab or second notebook + 15-question test |
| **M5** | Docs + presentation + second GPU | Slides, README, rubric checklist, demo script | Slide skeleton + this plan in the repo | 5-minute deck, rubric checklist, rehearsal |

If the team has different strengths, swap names but keep the ownership boundaries. **Only M1 edits the shared notebook**; everyone else puts proposed cells in a `SCRATCH` section at the bottom to avoid edit conflicts.

## Ground rules

- One theme, one problem statement: 3B. Do not spend GPU time on Theme 1 or Laya.
- The shared Colab notebook is the source of truth. The GitHub repo holds docs, screenshots and links only.
- The evaluation sample is fixed once (seed 0, 100 test receipts) and reused for baseline and fine-tuned runs. Never compare different samples.
- Save the LoRA adapters to Drive **before** any long run and immediately after training.
- No invented numbers. If fine-tuning loses on a field, show it.
- SROIE is Malaysian; any campus receipt from your college is a separate, clearly labelled local test.

## Timeline (T+0 = kickoff)

| Time | M1 notebook | M2 evaluation | M3 app | M4 RAG | M5 docs |
|---|---|---|---|---|---|
| **0:00–0:20** | Open starter, save copy, T4, run install | Build eval keys (seed 0, 100) | App skeleton, no model | Shortlist 2 official PDFs | Slide skeleton, commit this plan |
| **0:20–0:50** | Load vision model, smoke-test one receipt | Write scoring + metrics sheet | Wire skeleton to a dummy JSON | Check PDFs are text-based | Dataset description + pipeline diagram |
| **0:50–1:30** | Baseline on 100, then start 120-step LoRA | Verify baseline metrics, failure table | Record baseline backup clip | Draft 15 RAG questions | Baseline slide |
| **1:30–2:30** | Fine-tuned eval on the same 100 | Fill comparison table, categorise errors | Both models + claim draft | RAG notebook (only after CP1) | Comparison + limitations slides |
| **2:30–3:30** | Adapter reload test on a fresh runtime | Final metrics + local receipt note | Polish + record final backup | Integrate RAG tab, test refusals | Assemble deck, rubric checklist |
| **3:30–4:30** | Buffer / second experiment (160 steps or E4B) | Verify every number in the deck | Demo dry run | Fix citations or hide tab | Rehearse |

Compressed variant: if the showcase is under 4 hours away, run 0:00–2:30 only, freeze features at 2:30, and go straight to rehearsal.

## Checkpoints (go / no-go)

- **CP1 at 2:30 — core green?** Baseline + fine-tuned comparison + app working. If yes, M4 builds the RAG tab. If no, cut RAG; M4 moves to app testing and M5 gets help with the deck.
- **CP2 at 3:30 — demo dry run.** The demo must run end to end twice, including the adapter reload. Freeze features after this.
- **CP3 at 4:15 — final rehearsal.** No code changes after this except demo-blocking fixes.

## Cut lines

| Symptom | Action |
|---|---|
| CUDA out of memory | Keep `load_in_4bit=True`, set `finetune_vision_layers=False`, lower `MAX_IMAGE_SIDE` to 1200 and `max_length` to 1536 |
| Training slower than 30 min | Stop at the current step, save, evaluate what you have, record the actual step count |
| Colab disconnects | Reload base + adapters from Drive, rerun only eval and app cells |
| GPU quota exhausted | Switch to another member's account; the notebook is account-agnostic |
| Fine-tuned model is worse | Report it honestly, show failures, and use the prompted baseline as the comparison |
| RAG documents are scanned images | Replace them with text-based PDFs or drop RAG (bonus only) |
| RAG not green by CP2 | Hide the tab; do not show a broken feature in the demo |

## Definition of done (rubric)

- [ ] Fine-tuned model with training settings documented (steps, LR, LoRA rank, image size, subset)
- [ ] Dataset description: source, 626/361 split, fields, filtering, fixed eval sample
- [ ] Comparative analysis on the same receipts: valid JSON, company, date, address, total, address token-F1
- [ ] Working application demonstrated live (upload → extract → edit → claim draft)
- [ ] Discussion of where fine-tuning helped, where it did not, and why
- [ ] Backup video and screenshots in case the live demo fails
- [ ] Bonus only if green: policy RAG with document + page citations, refusal, 15-question test

## GitHub tracking

Work is tracked in the [Hack Day 3B milestone](https://github.com/sank8-2/campusclaim/milestone/1):

| Issue | Role | Assignee |
|---|---|---|
| [#1](https://github.com/sank8-2/campusclaim/issues/1) | M1 — notebook and fine-tuning | sank8-2 |
| [#2](https://github.com/sank8-2/campusclaim/issues/2) | M2 — evaluation and metrics | preetamggoudar |
| [#3](https://github.com/sank8-2/campusclaim/issues/3) | M3 — app and demo | itz-dark007 |
| [#4](https://github.com/sank8-2/campusclaim/issues/4) | M4 — policy RAG bonus | unassigned |
| [#5](https://github.com/sank8-2/campusclaim/issues/5) | M5 — slides and rehearsal | unassigned |

Issues #4 and #5 need the remaining team members' GitHub handles. Until then, anyone can self-assign by commenting on the issue.

## Shared artifacts

- Colab sections: `Setup`, `Data`, `Baseline`, `Fine-tune`, `Evaluation`, `App`, `RAG (optional)`, `SCRATCH`.
- Repo: `docs/team-plan.md` (this file), `docs/results.md` (numbers + failures), `docs/demo-script.md`, `screenshots/`.
- Adapters: `campusclaim_gemma4_lora.zip` in Drive, shared with the team.

## GPU plan

- Account A (M1): the main run — baseline, training, evaluation.
- Account B (M5): second experiment only after the main baseline is recorded.
- Account C (M4): AI Studio API for RAG, no GPU needed.
- Every member should have a Google account ready; free T4 time is per account.

## Immediate next 30 minutes

1. **M1** — open the [Theme 3 starter](https://colab.research.google.com/github/mithun-srinivas/HacktoberFest-HackDay/blob/main/templates/03_fine_tuning_starter_kit.ipynb), *File → Save a copy in Drive*, rename it `CampusClaim 3B`, set T4, run the install and GPU cells.
2. **M2** — create the fixed eval list: `random.Random(0).sample(test_rows, 100)` over usable test receipts; paste the 100 `key` values into the notebook and the metrics sheet.
3. **M3** — build the Gradio skeleton with image upload, plain/tuned boxes, four editable fields, claim draft, and a reset button; it can run on dummy JSON.
4. **M4** — shortlist two official campus finance/activity documents with public URLs; confirm they are text-based PDFs, not scans. Do not start the RAG build before CP1.
5. **M5** — create the slide skeleton (problem, pipeline, dataset, baseline vs fine-tuned, failures, demo, limitations) and commit this plan.

## 5-minute demo script

1. **Problem** (30 s): student clubs retype receipts and hunt for reimbursement rules.
2. **Extraction** (90 s): upload a held-out receipt, show plain vs fine-tuned side by side, correct one field.
3. **Claim draft** (60 s): build the draft from the corrected fields, show missing information.
4. **Evidence** (60 s): metrics table + two failure examples, including one wrong total.
5. **Policy** (60 s, if green): ask a covered question (cited) and an uncovered one (refused).
6. **Limits** (30 s): SROIE is Malaysian; local receipts are a separate small test; approval stays human.
