#!/usr/bin/env python3
"""Build a detailed PowerPoint walkthrough of notebooks/campusclaim_3b.ipynb."""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "CampusClaim_Notebook_Walkthrough.pptx"
SCREENSHOTS = ROOT / "screenshots"

# Campus / receipt-desk visual direction (avoid purple / cream-serif / broadsheet clichés)
NAVY = RGBColor(0x0F, 0x2C, 0x3C)
TEAL = RGBColor(0x1F, 0x7A, 0x6E)
INK = RGBColor(0x1A, 0x1F, 0x24)
MUTED = RGBColor(0x5A, 0x65, 0x6E)
LIGHT = RGBColor(0xF3, 0xF6, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0xC4, 0x5C, 0x26)
CARD = RGBColor(0xE7, 0xEE, 0xEC)


def _set_run(run, *, size=18, bold=False, color=INK, font="Calibri"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font


def _add_bg(slide, color=LIGHT):
    fill = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5)
    )
    fill.fill.solid()
    fill.fill.fore_color.rgb = color
    fill.line.fill.background()
    # send to back
    spTree = slide.shapes._spTree
    sp = fill._element
    spTree.remove(sp)
    spTree.insert(2, sp)


def _accent_bar(slide):
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.18), Inches(7.5)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = TEAL
    bar.line.fill.background()


def _title_block(slide, title: str, subtitle: str | None = None):
    box = slide.shapes.add_textbox(Inches(0.55), Inches(0.28), Inches(12.2), Inches(1.1))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = title
    _set_run(run, size=28, bold=True, color=NAVY, font="Georgia")
    if subtitle:
        p2 = tf.add_paragraph()
        p2.space_before = Pt(6)
        run2 = p2.add_run()
        run2.text = subtitle
        _set_run(run2, size=14, color=MUTED)


def _bullets(slide, lines: list[str], *, left=0.55, top=1.5, width=12.2, height=5.5, size=16):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = 0
        p.space_after = Pt(8)
        # support "  - child" as indent
        text = line
        level = 0
        while text.startswith("  "):
            level += 1
            text = text[2:]
        if text.startswith("- "):
            text = text[2:]
        p.level = min(level, 2)
        run = p.add_run()
        run.text = text
        _set_run(run, size=size - (2 if level else 0), color=INK if level == 0 else MUTED)


def _card(slide, left, top, width, height, title: str, body: str):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = WHITE
    shape.line.color.rgb = CARD
    shape.adjustments[0] = 0.08
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18)
    tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.14)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = title
    _set_run(run, size=14, bold=True, color=TEAL)
    for line in body.split("\n"):
        p2 = tf.add_paragraph()
        p2.space_before = Pt(4)
        run2 = p2.add_run()
        run2.text = line
        _set_run(run2, size=12, color=INK)


def _footer(slide, page: int, total: int):
    box = slide.shapes.add_textbox(Inches(0.55), Inches(7.05), Inches(10), Inches(0.35))
    tf = box.text_frame
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = f"CampusClaim · Theme 3B · notebooks/campusclaim_3b.ipynb"
    _set_run(run, size=10, color=MUTED)
    num = slide.shapes.add_textbox(Inches(11.5), Inches(7.05), Inches(1.4), Inches(0.35))
    tf2 = num.text_frame
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    run2 = p2.add_run()
    run2.text = f"{page} / {total}"
    _set_run(run2, size=10, color=MUTED)


def _new(prs, *, title=None, subtitle=None, bullets=None, blank=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    _add_bg(slide)
    _accent_bar(slide)
    if not blank:
        if title:
            _title_block(slide, title, subtitle)
        if bullets:
            _bullets(slide, bullets)
    return slide


def build() -> Path:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slides_meta: list[tuple] = []  # filled after we know count via two-pass; instead append then footer

    built = []

    # 1 Title
    s = _new(prs, blank=True)
    hero = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    hero.fill.solid()
    hero.fill.fore_color.rgb = NAVY
    hero.line.fill.background()
    accent = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(6.85), Inches(13.333), Inches(0.65))
    accent.fill.solid()
    accent.fill.fore_color.rgb = TEAL
    accent.line.fill.background()
    t = s.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(11.5), Inches(3))
    tf = t.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "CampusClaim"
    _set_run(r, size=48, bold=True, color=WHITE, font="Georgia")
    p2 = tf.add_paragraph()
    p2.space_before = Pt(12)
    r2 = p2.add_run()
    r2.text = "Receipt Information Extraction with Gemma 4 Vision"
    _set_run(r2, size=22, color=RGBColor(0xB8, 0xD4, 0xCE))
    p3 = tf.add_paragraph()
    p3.space_before = Pt(18)
    r3 = p3.add_run()
    r3.text = "A detailed walkthrough of notebooks/campusclaim_3b.ipynb\nHacktoberfest Hack Day · Theme 3B · Unsloth LoRA on Colab T4"
    _set_run(r3, size=14, color=RGBColor(0x9A, 0xB0, 0xAA))
    built.append(s)

    # 2 Agenda
    s = _new(
        prs,
        title="Agenda",
        subtitle="What this deck covers from the working notebook",
        bullets=[
            "Problem & Theme 3B scope — why CampusClaim exists",
            "Notebook architecture — seven steps from install to adapter zip",
            "Dataset — ICDAR 2019 SROIE, frozen eval sample, domain shift",
            "Memory-safe Colab design — why the first runs crashed",
            "Baseline → LoRA fine-tune → comparison on the same 100 receipts",
            "Scoring, exports, Gradio demo, and optional policy RAG bonus",
            "Honest limits, cut lines, and what to say in the live showcase",
        ],
    )
    built.append(s)

    # 3 Problem
    s = _new(
        prs,
        title="The problem",
        subtitle="Student clubs retype receipts and hunt for reimbursement rules",
    )
    _card(s, 0.55, 1.55, 3.9, 4.6, "Today", "Photograph a receipt\nRetype merchant, date,\naddress, and total\nSearch finance PDFs\nDraft a claim by hand\nWait on human approval")
    _card(s, 4.7, 1.55, 3.9, 4.6, "CampusClaim", "Upload the image\nExtract four fields as JSON\nEdit mistakes in the form\nDraft a claim summary\nOptional: cited policy Q&A")
    _card(s, 8.85, 1.55, 3.9, 4.6, "Still human", "Approval stays with the\ncollege reviewer\nThe model prepares the\nclaim — it does not\nsanction the expense")
    built.append(s)

    # 4 Theme
    s = _new(
        prs,
        title="Theme selection — 3B only",
        subtitle="Confirmed 24 October 2026 · one theme per team",
        bullets=[
            "Primary: Theme 3B — Receipt Information Extraction (required)",
            "Bonus only: Theme 2A-style policy RAG as the 3B “combined approach”",
            "Out of scope for hack day: Theme 1 four-model scorecard · Laya decision layer",
            "Model: unsloth/gemma-4-E2B-it (4-bit) with Unsloth FastVisionModel",
            "Hardware: free Colab T4 · GPU cells are not runnable in the local checkout",
            "Source of truth for the run: shared Colab notebook; repo holds the versioned copy",
        ],
    )
    built.append(s)

    # 5 Notebook map
    s = _new(
        prs,
        title="Notebook map — seven steps",
        subtitle="campusclaim_3b.ipynb run order (T4 GPU required)",
    )
    steps = [
        ("1", "Load model", "FastVisionModel\n4-bit · chat template"),
        ("2", "Load data", "SROIE train/test\nlazy indices"),
        ("3", "Baseline", "Smoke → 100\nplain Gemma"),
        ("4", "LoRA", "Vision + language\n120 steps"),
        ("5", "Evaluate", "Same 100 keys\ncomparison table"),
        ("6", "App", "Gradio upload\nedit · claim draft"),
        ("7", "Save", "Adapter zip\nbefore disconnect"),
    ]
    for i, (n, title, body) in enumerate(steps):
        left = 0.45 + i * 1.82
        badge = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(left + 0.55), Inches(1.7), Inches(0.45), Inches(0.45))
        badge.fill.solid()
        badge.fill.fore_color.rgb = TEAL
        badge.line.fill.background()
        btf = badge.text_frame
        btf.paragraphs[0].alignment = PP_ALIGN.CENTER
        br = btf.paragraphs[0].add_run()
        br.text = n
        _set_run(br, size=14, bold=True, color=WHITE)
        _card(s, left, 2.4, 1.7, 3.5, title, body)
    built.append(s)

    # 6 Budget
    s = _new(
        prs,
        title="Runtime budget on a free T4",
        subtitle="Plan the showcase around these ranges from the notebook header",
        bullets=[
            "Install Unsloth + deps — about 2–4 minutes",
            "Model download (gemma-4-E2B-it) — about 5 minutes first time",
            "SROIE download — about 2 minutes",
            "Baseline on 100 receipts — about 3–5 minutes",
            "120 LoRA steps — about 20–30 minutes",
            "Fine-tuned eval on the same 100 — about 3–5 minutes",
            "Critical: stop after the one-receipt smoke test before spending GPU on the full baseline",
            "Gemma 4 is forced to float32 on T4 (float16 → NaN gradients) — expected; image side capped at 1024 px",
        ],
    )
    built.append(s)

    # 7 Dataset
    s = _new(
        prs,
        title="Dataset — ICDAR 2019 SROIE",
        subtitle="jsdnrs/ICDAR2019-SROIE · CC-BY-4.0 · Malaysian receipts",
        bullets=[
            "987 rows: 626 train · 361 test",
            "Entities used: company, date, address, total",
            "words / bboxes unused — those would be an OCR baseline, not vision fine-tuning",
            "One train row has empty total → 625 usable train receipts",
            "All 361 test rows usable; evaluation uses a frozen 100-key sample (seed 0)",
            "Frozen keys live in data/eval_keys_seed0.json and are embedded in the notebook",
            "Never resample mid-run — baseline and fine-tuned must share the exact same receipts",
            "Domain shift: SROIE score ≠ campus-receipt score; local receipts are a separate, labelled test",
        ],
    )
    built.append(s)

    # 8 Memory
    s = _new(
        prs,
        title="Colab memory design (the hard part)",
        subtitle="“Session crashed after using all available RAM” — system RAM, not GPU",
        bullets=[
            "Free Colab ≈ 12.7 GB system RAM · T4 ≈ 15 GB VRAM",
            "First crash cause: iterating the image column and decoding ~1,000 PILs into Python lists",
            "Fix 1 — filter on key/entities only via select_columns (metadata views)",
            "Fix 2 — LazyRows for evaluation (decode one receipt per access)",
            "Fix 3 — training Dataset of row indices + with_transform (messages + images)",
            "TRL SFTTrainer accepts datasets.Dataset / IterableDataset — not torch.utils.data.Dataset",
            "Do not Dataset.from_list(all conversations) — that reintroduces the RAM spike",
            "MAX_IMAGE_SIDE = 1024 · dataloader_num_workers = 0 · gc + empty_cache around heavy cells",
        ],
    )
    built.append(s)

    # 9 Model load
    s = _new(
        prs,
        title="Step 1 — Load the vision model",
        subtitle="FastVisionModel.from_pretrained + Gemma 4 chat template",
        bullets=[
            "MODEL_NAME = unsloth/gemma-4-E2B-it (E4B is stronger but tighter on a T4)",
            "load_in_4bit=True — fits inside free T4 VRAM",
            "use_gradient_checkpointing = \"unsloth\"",
            "Returns a processor, not a tokenizer — use get_chat_template(processor, \"gemma-4\")",
            "INSTRUCTION: Extract company, date, address, total · reply with JSON only",
            "Print device + allocated/reserved GPU memory after load",
            "Common pitfall: calling processor.tokenizer → TypeError on Gemma 4",
        ],
    )
    built.append(s)

    # 10 Conversations
    s = _new(
        prs,
        title="Step 2 — Conversation format",
        subtitle="What each training example looks like for UnslothVisionDataCollator",
        bullets=[
            "messages[user]: text instruction + {\"type\": \"image\"} placeholder",
            "messages[assistant]: JSON string of the four gold entities",
            "images: [prepared PIL] — separate column matching generate_from_image",
            "prepare_image: RGB convert + thumbnail to MAX_IMAGE_SIDE",
            "INSTRUCTION is redefined in the conversation cell so partial re-runs after a restart do not NameError",
            "Preview prints the assistant JSON for row 0 to confirm the pipeline before training",
        ],
    )
    built.append(s)

    # 11 Scoring
    s = _new(
        prs,
        title="Step 3 — Generation & scoring",
        subtitle="Same instruction for baseline and fine-tuned · normalised field match",
        bullets=[
            "generate_from_image: chat template → processor(images=…) → greedy decode new tokens only",
            "parse_json: first JSON object in the reply (handles fences / prose wrappers)",
            "Normalisers: case/punctuation for text · date formats · currency/comma totals",
            "Metrics: valid JSON · exact company/date/address/total · address token-F1",
            "Formatting differences are not counted as wrong extractions after normalisation",
            "Report valid JSON separately — a prose reply scores 0 on every field",
        ],
    )
    built.append(s)

    # 12 Smoke
    s = _new(
        prs,
        title="Smoke test — gate before the long run",
        subtitle="One frozen receipt · if this fails, do not start the 100-receipt baseline",
        bullets=[
            "smoke = eval_rows[0]",
            "Print key, expected entities, and prediction JSON",
            "Success criterion: valid JSON with the four fields (accuracy can still be wrong)",
            "Failure: fix generation / processor / OOM before spending 30+ minutes of GPU",
            "This is the checkpoint the Colab handoff asks M1 to paste back to the team",
        ],
    )
    built.append(s)

    # 13 Baseline
    s = _new(
        prs,
        title="Baseline — plain Gemma on 100 receipts",
        subtitle="evaluate_vision(eval_rows, \"plain_model\")",
        bullets=[
            "Runs the frozen 100 keys with adapters off (or before LoRA is attached)",
            "Produces baseline_df + baseline_metrics",
            "This is the control group every fine-tuned result must beat",
            "Export later: baseline_predictions.csv · baseline_metrics.json",
            "Do not change EVAL_KEYS between baseline and fine-tuned runs",
        ],
    )
    built.append(s)

    # 14 LoRA
    s = _new(
        prs,
        title="Step 4 — LoRA fine-tuning",
        subtitle="Vision layers are trained because the task is reading the receipt",
        bullets=[
            "FastVisionModel.get_peft_model · r = alpha = 16 · dropout 0 · all-linear targets",
            "finetune_vision_layers = True (and language / attention / MLP)",
            "SFTTrainer + UnslothVisionDataCollator · processing_class = processor",
            "120 steps ≈ 0.75 epoch over 625 usable train receipts",
            "LR 2e-4 · batch 1 · grad accum 4 · max_length 2048 · adamw_8bit · cosine schedule",
            "skip_prepare_dataset=True · remove_unused_columns=False",
            "OOM fallbacks: LORA_RANK=8 · finetune_vision_layers=False · MAX_IMAGE_SIDE=800",
        ],
    )
    built.append(s)

    # 15 Eval compare
    s = _new(
        prs,
        title="Step 5 — Fine-tuned eval & comparison",
        subtitle="Same receipts · same instruction · same scorers",
        bullets=[
            "tuned_records = evaluate_vision(eval_rows, \"fine_tuned_model\")",
            "comparison table: Plain % · Fine-tuned % · Change (points)",
            "Failure table: receipts with any wrong field among company/date/address/total",
            "Show where fine-tuning helped and where it did not — no invented wins",
            "Exact address is strict; always show token-F1 beside it",
        ],
    )
    built.append(s)

    # 16 Metrics placeholder
    s = _new(
        prs,
        title="Metrics slide (fill from results/)",
        subtitle="Numbers come only from comparison.csv after the Colab run — never invent them",
    )
    headers = ["Metric", "Plain Gemma", "Fine-tuned", "Change"]
    rows = [
        ["Valid JSON", "—", "—", "—"],
        ["Company exact", "—", "—", "—"],
        ["Date exact", "—", "—", "—"],
        ["Address exact", "—", "—", "—"],
        ["Total exact", "—", "—", "—"],
        ["Address token-F1", "—", "—", "—"],
    ]
    table = s.shapes.add_table(len(rows) + 1, 4, Inches(1.2), Inches(1.7), Inches(10.8), Inches(4.2)).table
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        for p in cell.text_frame.paragraphs:
            for run in p.runs:
                _set_run(run, size=13, bold=True, color=WHITE)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cell = table.cell(r, c)
            cell.text = val
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    _set_run(run, size=13, color=INK)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if r % 2 else CARD
    note = s.shapes.add_textbox(Inches(1.2), Inches(6.1), Inches(10.8), Inches(0.6))
    np = note.text_frame.paragraphs[0]
    nr = np.add_run()
    nr.text = "After export: copy from results/comparison.csv. M2 owns verification before the deck goes final."
    _set_run(nr, size=12, color=ACCENT)
    built.append(s)

    # 17 Exports
    s = _new(
        prs,
        title="Exports for M2 / M5",
        subtitle="results/ folder written by the notebook export cell",
        bullets=[
            "baseline_metrics.json · tuned_metrics.json",
            "comparison.csv · failures.csv",
            "baseline_predictions.csv · tuned_predictions.csv",
            "settings.json — model, instruction, eval size/seed, image side, LoRA, steps, LR, batch",
            "Download the whole results/ folder from the Colab file browser",
            "Also download campusclaim_gemma4_lora.zip immediately after training",
        ],
    )
    built.append(s)

    # 18 Gradio
    s = _new(
        prs,
        title="Step 6 — Gradio application",
        subtitle="Upload → extract (plain vs tuned) → edit → claim draft",
    )
    _card(
        s, 0.55, 1.55, 6.0, 4.8, "In-notebook demo (primary)",
        "extract_both: disable_adapter for plain,\nthen tuned with adapters on\n\nEditable fields: company, date,\naddress, total + purpose\n\nbuild_summary marks missing fields\nand reminds that approval is human\n\nStandalone app/gradio_app.py is the\nCPU fallback (dummy or --no-dummy)",
    )
    # screenshots collage
    shots = [
        SCREENSHOTS / "01-upload.png",
        SCREENSHOTS / "02-extraction.png",
        SCREENSHOTS / "03-edited-field.png",
        SCREENSHOTS / "04-claim-draft.png",
    ]
    labels = ["Upload", "Extract", "Edit", "Claim"]
    for i, (path, label) in enumerate(zip(shots, labels)):
        left = 6.9
        top = 1.55 + i * 1.2
        if path.exists():
            s.shapes.add_picture(str(path), Inches(left), Inches(top), height=Inches(1.05))
        tag = s.shapes.add_textbox(Inches(11.0), Inches(top + 0.3), Inches(1.8), Inches(0.4))
        tr = tag.text_frame.paragraphs[0].add_run()
        tr.text = label
        _set_run(tr, size=12, bold=True, color=TEAL)
    built.append(s)

    # 19 Demo flow
    s = _new(
        prs,
        title="5-minute demo script",
        subtitle="From docs/demo-script.md / team plan",
        bullets=[
            "0:30 — Problem: clubs retype receipts and hunt rules",
            "1:30 — Extraction: upload held-out receipt · plain vs fine-tuned side by side · fix one field",
            "1:00 — Claim draft from corrected fields · show missing information",
            "1:00 — Evidence: metrics table + two failures (include a wrong total)",
            "1:00 — Policy (if CP1 green): covered question with citation · uncovered refusal",
            "0:30 — Limits: SROIE is Malaysian · local receipts separate · approval stays human",
        ],
    )
    built.append(s)

    # 20 Save adapters
    s = _new(
        prs,
        title="Step 7 — Save adapters before disconnect",
        subtitle="Free Colab can die without warning",
        bullets=[
            "model.save_pretrained(\"campusclaim_gemma4_lora\")",
            "processor.save_pretrained(...)",
            "zip the folder → campusclaim_gemma4_lora.zip",
            "Copy to Google Drive immediately after training",
            "On reconnect: reload base model → load adapters → re-run eval/app only",
            "Optional: push_to_hub with a Hugging Face token",
        ],
    )
    built.append(s)

    # 21 RAG bonus
    s = _new(
        prs,
        title="Optional bonus — policy RAG",
        subtitle="Only after Checkpoint 1 (baseline + fine-tune + app green)",
        bullets=[
            "Separate notebook — do not mix RAG into the GPU extraction notebook",
            "Proxy docs shortlisted: SNU student reimbursement policy · IIIT Una SAC policy",
            "15-question test: 10 covered · 5 must refuse",
            "Every answer cites document + page; never invent policy",
            "If RAG is not green by CP2 — hide the tab; do not demo a broken feature",
            "Deck must say policy docs are institutional proxies unless college PDFs arrive",
        ],
    )
    built.append(s)

    # 22 Honest reporting
    s = _new(
        prs,
        title="Honest reporting notes",
        subtitle="From the notebook’s closing markdown — judges reward clarity over hype",
        bullets=[
            "SROIE is Malaysian (RM, dd/mm/yyyy) — campus receipts are a domain shift",
            "Report valid JSON separately from field accuracy",
            "Exact address match is strict — always pair with token-F1",
            "State eval subset size and seed (100 · seed 0)",
            "Never compare a 100-receipt baseline with a 361-receipt fine-tuned run",
            "If fine-tuning loses on a field — show it; the problem statement asks for that analysis",
        ],
    )
    built.append(s)

    # 23 Cut lines
    s = _new(
        prs,
        title="Cut lines & fallbacks",
        subtitle="From docs/team-plan.md — decide early, record what you did",
        bullets=[
            "CUDA OOM → keep 4-bit · freeze vision layers · lower image side / max_length",
            "Training > 30 min → stop, save, evaluate actual step count",
            "Colab disconnect → reload base + adapters from Drive · eval/app only",
            "GPU quota gone → switch Google account (notebook is account-agnostic)",
            "Fine-tuned worse → report honestly · use prompted baseline as comparison",
            "RAG scanned PDFs → replace or drop bonus",
        ],
    )
    built.append(s)

    # 24 Repo vs Colab
    s = _new(
        prs,
        title="Repo companion pieces",
        subtitle="What lives outside the notebook but supports the same story",
        bullets=[
            "app/inference.py — mirrors generate_from_image for the standalone Gradio app",
            "app/gradio_app.py — dummy by default · --no-dummy with adapter path",
            "scripts/score.py · validate_notebook.py · demo_pipeline.py · freeze_eval_sample.py",
            "tests/ — 40 standard-library tests · bash scripts/check.sh = CI",
            "dev = integration branch · main = submitted baseline",
            "GPU work stays in Colab; local checks stay CPU-only",
        ],
    )
    built.append(s)

    # 25 Team
    s = _new(
        prs,
        title="Team ownership (Hack Day 3B)",
        subtitle="Only M1 edits the shared notebook; others use SCRATCH",
    )
    roles = [
        ("M1", "Notebook + fine-tune", "Colab run, adapters, smoke gate"),
        ("M2", "Eval + metrics", "Frozen keys, comparison, failures"),
        ("M3", "App + demo", "Gradio, screenshots, backup clip"),
        ("M4", "Policy RAG", "PDFs + 15Q after CP1"),
        ("M5", "Deck + rehearsal", "Slides, rubric checklist"),
    ]
    for i, (who, role, detail) in enumerate(roles):
        _card(s, 0.55 + i * 2.5, 1.7, 2.35, 4.2, who, f"{role}\n\n{detail}")
    built.append(s)

    # 26 Rubric
    s = _new(
        prs,
        title="Definition of done (rubric checklist)",
        subtitle="Tick these before the final rehearsal",
        bullets=[
            "Fine-tuned model with settings documented (steps, LR, rank, image size, subset)",
            "Dataset description: source, 626/361, fields, filtering, frozen eval sample",
            "Comparative analysis on the same receipts (JSON + four fields + address F1)",
            "Working app demonstrated live (upload → extract → edit → claim draft)",
            "Discussion of where fine-tuning helped / did not / why",
            "Backup video + screenshots if live demo fails",
            "Bonus only if green: policy RAG with citations, refusal, 15-question test",
        ],
    )
    built.append(s)

    # 27 Next steps
    s = _new(
        prs,
        title="Immediate next steps for M1",
        subtitle="Where the notebook run stands operationally",
        bullets=[
            "Disconnect and delete the Colab runtime after any RAM crash",
            "Upload the patched notebooks/campusclaim_3b.ipynb",
            "Run install → GPU check → model → data → conversations → smoke test",
            "Paste smoke output before starting the 100-receipt baseline",
            "After training: save zip to Drive · run fine-tuned eval · export results/",
            "Hand results/ to M2 · fill metrics slide · rehearse the 5-minute script",
        ],
    )
    built.append(s)

    # 28 Close
    s = _new(prs, blank=True)
    hero = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    hero.fill.solid()
    hero.fill.fore_color.rgb = NAVY
    hero.line.fill.background()
    t = s.shapes.add_textbox(Inches(0.8), Inches(2.3), Inches(11.5), Inches(3))
    tf = t.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "Questions"
    _set_run(r, size=44, bold=True, color=WHITE, font="Georgia")
    p2 = tf.add_paragraph()
    p2.space_before = Pt(16)
    r2 = p2.add_run()
    r2.text = "CampusClaim · Theme 3B · Gemma 4 E2B + LoRA on SROIE\nNotebook: notebooks/campusclaim_3b.ipynb · Repo: sank8-2/campusclaim"
    _set_run(r2, size=16, color=RGBColor(0xB8, 0xD4, 0xCE))
    built.append(s)

    total = len(built)
    # footers on content slides (skip title + closing)
    for i, slide in enumerate(built, start=1):
        if i == 1 or i == total:
            continue
        _footer(slide, i, total)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path} ({path.stat().st_size} bytes)")
