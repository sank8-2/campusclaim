# CampusClaim — where the project stands

Snapshot: **24 October 2026**, branch `dev`. The code state described here is `9c7c351`; the only later commit is this document.
Everything below is checked against the repo, the CI run and the GitHub issues, not against the plan.

---

## 1. The one-paragraph version

CampusClaim turns a photo of a receipt into a reimbursement claim. The submission is **Theme 3B — Receipt Information Extraction**, and the deliverable is the **shared Colab notebook**, not this repo. The repo holds the notebook source, the frozen evaluation data, the scoring code, the app and the docs. The technique is a **LoRA fine-tune of Gemma 4 E2B** (vision + language layers, 4-bit, 120 steps) compared against the **same model without adapters** on the same frozen 100 SROIE receipts.

As of this snapshot the **engineering around the run is finished and green** — notebook, data, scoring, app, demo pipeline, RAG document shortlist, CI — but **the GPU run itself has not happened**. There is no `results/` folder, no adapter zip and no metrics anywhere in the repo. Every accuracy number the team will show is therefore still unwritten, and the deck cannot be assembled until the Colab run lands.

---

## 2. Two halves of the system

The split matters because it explains what can be verified here and what cannot.

| Half | Runs on | What it contains | Verified locally? |
|---|---|---|---|
| **GPU half** | Colab free T4 only | Install, model load, baseline inference, LoRA training, fine-tuned inference, the notebook's Gradio cell, adapter save | No — needs CUDA and ~16 GB VRAM |
| **CPU half** | Any laptop, stdlib only | Notebook validation, frozen-key checks, scoring, table generation, app in dummy mode, demo pipeline, RAG doc checks, tests, CI | Yes — 40 tests pass on `dev` |

Nothing in `scripts/` or `tests/` imports `torch`, `transformers` or `gradio` at module level, so CI on a plain Ubuntu runner exercises the whole CPU half. `app/inference.py` is deliberately import-safe: the heavy imports sit inside the functions that need them.

---

## 3. Repository and branch state

| Item | Value |
|---|---|
| Branch | `dev` |
| HEAD | `2fbb781` — this snapshot, on top of `9c7c351` (merge of PR #8) |
| `main` vs `dev` | `dev` is 1 commit ahead (this document); code is identical |
| Tracked files | 43 |
| Tests on `dev` | 40 |
| CI | `.github/workflows/ci.yml` — Ubuntu, Python 3.11, `validate_notebook.py` + `unittest discover` |
| Milestone | *Hack Day 3B* — 5 open issues, 0 closed |

**Branch rule (from README):** `dev` is the integration branch; `main` holds the submitted baseline. Push to `dev`, never directly to `main`.

In practice every merge so far (#8, #9, #10) went straight into `main`, and `dev` was folded in once through #9. That is why the two branches are currently identical — by history, not by policy. Worth fixing before the submission, because the rule and the log disagree.

**Test breakdown on `dev`:**

| File | Tests | Covers |
|---|---|---|
| `tests/test_inference.py` | 14 | JSON parsing, processor/generation calls, import safety |
| `tests/test_gradio_app.py` | 12 | prefill, claim draft, adapter on/off, CLI wiring |
| `tests/test_scoring.py` | 8 | normalisers, token-F1, four scoring cases |
| `tests/test_demo_pipeline.py` | 5 | offline demo report |
| `tests/test_notebook.py` | 1 | notebook pre-flight |
| **total** | **40** | |

**Open PR:** [#11 `m2/eval-table`](https://github.com/sank8-2/campusclaim/pull/11) (draft, base `dev`, CI passing). It adds 13 more tests (53 total) and two tools described in §7.

---

## 4. How the pipeline actually works

```
receipt image
   │
   ├─ prepare_image(): RGB + thumbnail to 1600 px  →  same on train and inference
   │
   ├─ chat template "gemma-4" + INSTRUCTION
   │     "Extract the company, date, address and total from this receipt.
   │      Reply with JSON only."
   │
   ├─ greedy decode, max_new_tokens=128
   │
   ▼
{"company": …, "date": …, "address": …, "total": …}
   │
   ├─ parse_json() → first JSON object in the reply (None if prose)
   ├─ score() per field, after normalisation
   │
   └─ app: prefill four editable fields → claim draft → missing-field warning
                                          → "approval stays with the reviewer"
```

The **plain** run wraps generation in `model.disable_adapter()`; the **tuned** run leaves the adapter active. That is the entire difference between the two numbers in the comparison table — same images, same instruction, same decode, same 100 keys.

### The data

`jsdnrs/ICDAR2019-SROIE`, CC-BY-4.0, Malaysian receipts.

| Split | Rows | Usable | Used for |
|---|---|---|---|
| train | 626 | 625 (one row has an empty `total`) | 120 LoRA steps on image + entities |
| test | 361 | 361 | source pool for the frozen 100 |

`words` and `bboxes` are intentionally unused — they would build an OCR baseline, not a vision fine-tune.

### The frozen sample

`data/eval_keys_seed0.json` holds exactly 100 test keys drawn with `random.Random(0).sample(..., 100)`. The notebook embeds the same list and the validator asserts it still matches, so the plain and tuned runs cannot silently evaluate different receipts. This is the single most important anti-fraud control in the project: without it, a "fine-tuning helps" claim is unfalsifiable.

### What "correct" means

`scripts/score.py`, mirroring the notebook's scoring cell:

| Metric | Rule |
|---|---|
| valid JSON | the reply contains a parseable JSON **object**; prose scores 0 on every field |
| company exact | lowercase, non-alphanumerics collapsed to spaces, then exact match |
| date exact | normalised to `dd/mm/yyyy`; `25 Dec 2018`, `25-12-18` and `25/12/2018` all match |
| address exact | same text normalisation, exact match — deliberately strict |
| total exact | numeric after stripping `RM`/commas, compared within ±0.01 |
| address token-F1 | bag-of-tokens F1, so a missing comma is not reported as a total failure |

Reporting `valid_json` separately is the honest part: a model that answers in fluent prose looks fine in a demo and scores zero in the table.

---

## 5. Workstream status

Five roles, tracked in the milestone. The honest summary is that **four of five are blocked on the same GPU run**, and the fifth (M1) has not started it.

### M1 — notebook and fine-tune (#1) — *not started on GPU*

Written and committed: the 25-cell notebook (15 code cells), the frozen eval sample, the scoring, the export cell, the adapter-save cell. Validator passes: every code cell compiles, 100 keys match the manifest, all required cells present.

Not done: the Colab upload, the T4 run, the baseline, the 120 steps, the fine-tuned eval, the `results/` export, the adapter zip, the fresh-runtime reload test. Every task checkbox in #1 is still empty.

### M2 — evaluation (#2) — *tooling done, numbers blocked*

Done: the frozen sample, the reference scoring and its tests, and the four-case verification. `tests/test_notebook_scoring.py` on PR #11 now runs the four cases against **the notebook's own cell**, so the copy in `scripts/score.py` cannot drift from what Colab executes.

Blocked: the comparison table, five failure examples, the 3–5 local campus receipts. All three need outputs that do not exist yet.

### M3 — app and demo (#3) — *built, running on dummy JSON*

Done: Gradio app with upload → plain/tuned extraction → four editable fields → claim draft → reset; a real `--no-dummy` path through `app/inference.py`; an offline `scripts/demo_pipeline.py` that writes `results/demo_report.json`; four screenshots and a capture script.

Caveat worth stating plainly: the demo currently exercises **dummy extractors**. The app path is real and tested, but no receipt has been read by an actual model in it, because no model exists yet. The issue's checkboxes are all ticked — they should be read as "the code exists", not "the model ran".

### M4 — policy RAG bonus (#4) — *pre-CP1 only, correctly gated*

Done: two public, text-based policy PDFs shortlisted with checksums and a page map (`docs/rag-documents.md`), a 15-question test (10 covered, 5 refusal) in `docs/rag-eval.md` and `data/rag/questions.json`, plus `fetch_rag_docs.py` and a `pypdf` text-based check.

Not done: the RAG build. The plan gates it behind CP1, and CP1 needs M1's comparison. So this is deliberately parked, not behind schedule.

One thing the deck must say out loud: the documents are **proxy policies from two Indian universities**, not the team's own college. Every answer needs a document + page citation, and the deck needs a line admitting the substitution.

### M5 — slides and rehearsal (#5) — *skeleton only*

Done: the plan, the dataset description, the demo script, screenshots. Not done: the deck itself, the rubric checklist, the rehearsal. Its comparison and limitations slides consume M2's verified numbers, so it is blocked on the same run.

---

## 6. What is actually proven right now

Separating these three columns is the point of this document.

| Claim | Status | Evidence |
|---|---|---|
| The notebook is syntactically runnable and uses the frozen 100 keys | **Verified** | `scripts/validate_notebook.py` → OK |
| Scoring is correct on perfect / normalised / wrong / prose cases | **Verified** | `tests/test_scoring.py` + `tests/test_notebook_scoring.py` |
| The notebook's scoring cell matches the reference copy | **Verified** | `tests/test_notebook_scoring.py` |
| The app flow works end to end without a model | **Verified** | `tests/test_gradio_app.py`, `scripts/demo_pipeline.py` |
| The demo pipeline produces a claim draft with missing fields | **Verified** | `tests/test_demo_pipeline.py` |
| The two policy PDFs are text-based, not scans | **Verified** | `scripts/check_rag_docs.py` |
| Fine-tuning improves extraction on the frozen 100 | **Unproven — no run** | — |
| The app reads a real receipt with real adapters | **Unproven — no run** | — |
| The adapter reloads on a fresh runtime | **Unproven — no run** | — |
| The 15 RAG questions return cited answers / correct refusals | **Unproven — not built** | — |

No number in this repo currently describes model accuracy. That is the gap.

---

## 7. M2 tooling added on PR #11

Two additions, both verifiable today:

**`scripts/build_results.py`** — takes M1's `results/` export and writes `docs/results.md`, but recomputes every metric from `baseline_predictions.csv` and `tuned_predictions.csv` first. It refuses to write if:

- a recomputed metric disagrees with `*_metrics.json` beyond the 0.1 rounding,
- the two runs did not use the same 100 keys, or a key is outside the frozen sample,
- a predictions file is missing, empty, or missing its `plain_model` / `fine_tuned_model` column.

So the deck's numbers can only come from a run that passed arithmetic verification. It also builds the five-receipt failure table with expected → predicted fields and a cause, and keeps the local campus receipts in a separate section fed by `results/local_receipts.csv` so they can never be pooled into the SROIE numbers.

**`tests/test_notebook_scoring.py`** — extracts the notebook's own scoring cell, executes it without pandas or a GPU, and runs the four required cases against it plus every normaliser. Mutation-checked: changing one normaliser in `scripts/score.py` fails three tests.

Usage once the run exists:

```bash
python3 scripts/build_results.py --results results          # write docs/results.md
python3 scripts/build_results.py --results results --check  # verify only, in CI
```

---

## 8. Critical path

```
M1 Colab run  ──►  results/  ──►  build_results.py  ──►  docs/results.md
                                   (verified numbers)
                                        │
                                        ├──► M5 comparison + limitations slides
                                        ├──► M2 failure analysis + local receipts
                                        └──► CP1 gate ──► M4 RAG build
                                                          └──► CP2 demo dry run
```

Everything downstream is written and waiting. The chain is blocked at exactly one link: the T4 run. Cut lines already exist for the realistic failure modes (OOM, slow training, disconnect, quota, fine-tune losing) — see `docs/team-plan.md`, and none of them require new code.

---

## 9. Next actions, in order

1. **M1** — run the notebook on a T4, export `results/` and `campusclaim_gemma4_lora.zip`, commit the `results/` folder (only `results/demo_report.json` is gitignored, so the real exports will be tracked).
2. **M2** — `git pull`, `python3 scripts/build_results.py --results results`, review the diff, commit. Then pick the five failures and write the causes into `results/failure_causes.csv` before regenerating.
3. **M2** — 3–5 real campus receipts through the app with the real adapter, recorded in `results/local_receipts.csv`, labelled as a separate local test.
4. **M3** — re-record the backup clip with both models once the adapter exists; the current screenshots are dummy-mode.
5. **M5** — fill the deck from `docs/results.md` only; do not retype numbers from the notebook output.
6. **M4** — start only if CP1 is green; otherwise hide the tab.

---

## 10. Reproduce every check locally

```bash
bash scripts/check.sh                       # validator + all tests (what CI runs)
python3 scripts/validate_notebook.py        # notebook syntax + frozen keys
python3 -m unittest discover -s tests -v    # 40 tests on dev, 53 with PR #11
python3 scripts/demo_pipeline.py            # offline demo → results/demo_report.json
python3 scripts/freeze_eval_sample.py       # rebuild data/ (network, no images)
python3 scripts/build_results.py --results results --check   # verify M1's export
python3 scripts/check_rag_docs.py           # needs the downloaded PDFs + pypdf
```

Local environment caveat: this machine runs **Python 3.9.6** with no `torch`, no `pandas` and no `pypdf`; CI runs **3.11** with none of them either, by design. Anything that needs a model or a PDF must run in Colab or after installing `requirements.txt`.

---

## 11. Risks worth naming before the demo

| Risk | Why it matters | Mitigation already in place |
|---|---|---|
| No run happens | The whole 3B submission has zero numbers | Cut lines per failure mode; the notebook is ready to run top to bottom |
| Fine-tune loses to the baseline | Plausible at 120 steps / 625 receipts | Plan says report it honestly and show failures; the table has a signed Change column |
| SROIE ≠ campus receipts | Malaysian receipts, `RM`, `dd/mm/yyyy` | Local receipts are a separate, labelled section by design |
| Dummy-mode demo mistaken for real | Screenshots and the clip are dummy extractors | Re-record with the adapter after the run; say "dummy" until then |
| RAG on proxy documents | Not the team's own college policy | Every answer cites document + page; deck states the substitution |
| Numbers drift between notebook and deck | Two places to type them | `build_results.py` recomputes and refuses on mismatch |
| Branch rule vs. history | Every PR so far merged into `main`; `dev` is unused as a gate | Route new PRs into `dev` and sync before submission |
| Private repo, unauthenticated tooling | Plain `git clone` 404s on a private repo | Use `gh` (installed at `/opt/homebrew/bin/gh`, logged in); plain `git` has no credential helper |
