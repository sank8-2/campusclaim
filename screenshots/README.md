# Screenshots checklist

The four required showcase screenshots are captured from the running app
(`scripts/capture_demo.py`):

1. `01-upload.png` — receipt uploaded
2. `02-extraction.png` — plain vs fine-tuned JSON and prefilled fields
3. `03-edited-field.png` — total edited to 430.00, claim draft refreshed
4. `04-claim-draft.png` — date cleared, draft lists `Missing fields: date`

`_demo_receipt.png` is the synthetic receipt used for the capture (regenerate with
`scripts/make_demo_receipt.py`).

Backup demo clips (`backup_baseline.webm`, `backup_final_both_models.webm`) are generated locally
by `scripts/capture_demo.py` and are ignored by git. Upload them to Drive and add the share links
to `docs/demo-script.md`; they are not committed here.
