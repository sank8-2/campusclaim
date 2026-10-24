# Demo script and backup assets

## M3 app demo flow

1. Upload receipt image.
2. Click **Extract** to view plain model JSON and fine-tuned model JSON.
3. Confirm the four editable fields (company, date, address, total) are prefilled from fine-tuned JSON.
4. Edit one field and verify the claim draft updates and lists any missing fields.
5. Use **Reset** and repeat once end-to-end.

## Backup clips

`scripts/capture_demo.py` drives the running app in Playwright/Chrome and writes both clips
to `screenshots/` locally. The `.webm` files are **git-ignored**, so they are not in the repo:
upload them to Drive and put the two share links here before CP2.

- [ ] Baseline clip, **2:00** — local `screenshots/backup_baseline.webm`; _share link pending_
- [ ] Final clip, **2:00** (plain vs fine-tuned boxes) — local `screenshots/backup_final_both_models.webm`; _share link pending_

> **Caveat:** the local captures are dummy-JSON mode because no saved adapter/GPU was available.
> Re-record the final clip with the real adapter (`--no-dummy`) after CP1 for a true
> model-comparison clip.

Capture both clips:

```bash
python -m pip install playwright
python -m playwright install chrome
python -m app.gradio_app --host 127.0.0.1 --port 7861   # terminal 1; stop it afterwards
python scripts/make_demo_receipt.py
python scripts/capture_demo.py --url http://127.0.0.1:7861 --pause-ms 14000
```

The capture needs `pillow` for the synthetic receipt (already installed with `gradio`). Do not
leave the Gradio server running after the capture.

## Rehearsal log

- [x] Live flow run end to end **4 times** (2 baseline + 2 final) during CP2 rehearsal.
  Every pass prefilled all four fields and the claim draft reported `Missing fields: date`
  after the date was cleared.
