# Demo script and backup assets

## M3 app demo flow

1. Upload receipt image.
2. Click **Extract** to view plain model JSON and fine-tuned model JSON.
3. Confirm the four editable fields (company, date, address, total) are prefilled from fine-tuned JSON.
4. Edit one field and verify the claim draft updates and lists any missing fields.
5. Use **Reset** and repeat once end-to-end.

## Backup clips

Recorded with `scripts/capture_demo.py` (Playwright driving the installed Chrome) against the
dummy-mode app. Both clips run the full upload → extract → edit → claim draft flow twice.

- [x] Baseline clip, **2:00** — `screenshots/backup_baseline.webm`
- [x] Final clip, **2:00** (plain vs fine-tuned boxes) — `screenshots/backup_final_both_models.webm`

> **Caveat:** these were captured in dummy-JSON mode because no saved adapter/GPU was available
> locally. Re-record with the real adapter (`--no-dummy`) after CP1 for a true model-comparison clip.

Regenerate both clips:

```bash
python -m app.gradio_app --host 127.0.0.1 --port 7861
python scripts/make_demo_receipt.py
python scripts/capture_demo.py --url http://127.0.0.1:7861 --pause-ms 14000
```

## Rehearsal log

- [x] Live flow run end to end **4 times** (2 baseline + 2 final) during CP2 rehearsal.
  Every pass prefilled all four fields and the claim draft reported `Missing fields: date`
  after the date was cleared.
