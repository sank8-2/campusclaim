"""Drive the CampusClaim Gradio app in Chrome to capture screenshots and backup clips.

Usage:
    python scripts/capture_demo.py --url http://127.0.0.1:7861

Requires the app to already be running (dummy mode is fine).
Writes the four showcase screenshots and two .webm backup clips into screenshots/.

The canonical screenshots (01-04) are captured on the first baseline pass. The
baseline and final clips each run the full flow end to end, with configurable
dwell time so the backup clip is long enough to follow without narration.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "screenshots"
RECEIPT = SHOTS / "_demo_receipt.png"

CANONICAL = {
    "upload": "01-upload.png",
    "extraction": "02-extraction.png",
    "edited": "03-edited-field.png",
    "draft": "04-claim-draft.png",
}


def _wait_draft(page, text: str, timeout: int = 20000):
    page.wait_for_function(
        "t => Array.from(document.querySelectorAll('textarea')).some(x => x.value.includes(t))",
        arg=text,
        timeout=timeout,
    )


def run_flow(page, *, pause_ms: int = 2500, capture: bool = False, tag: str = "") -> dict:
    """Run upload -> extract -> edit -> claim draft once. Returns observed state."""
    def shot(kind: str):
        if not capture:
            return
        name = CANONICAL[kind] if not tag else CANONICAL[kind].replace(".png", f"{tag}.png")
        page.screenshot(path=str(SHOTS / name), full_page=True)

    # 1. Upload
    page.locator('input[type="file"]').first.set_input_files(str(RECEIPT))
    page.wait_for_timeout(pause_ms)
    shot("upload")

    # 2. Extract
    page.get_by_role("button", name="Extract").click()
    page.wait_for_function(
        "() => Array.from(document.querySelectorAll('textarea')).filter(t => t.value.trim()).length >= 4",
        timeout=25000,
    )
    page.wait_for_timeout(pause_ms)
    shot("extraction")

    areas = page.locator("textarea")
    company = areas.nth(0).input_value()
    date = areas.nth(1).input_value()
    address = areas.nth(2).input_value()
    total = areas.nth(3).input_value()

    # 3. Edit one field (total) and let the claim draft refresh.
    areas.nth(3).fill("430.00")
    areas.nth(3).press("Tab")
    _wait_draft(page, "430.00")
    page.wait_for_timeout(pause_ms)
    shot("edited")

    # 4. Clear a field to prove the draft lists missing information.
    areas.nth(1).fill("")
    areas.nth(1).press("Tab")
    _wait_draft(page, "Missing fields: date")
    page.wait_for_timeout(pause_ms)
    shot("draft")

    draft = areas.nth(4).input_value()

    # Reset for the next run.
    page.get_by_role("button", name="Reset").click()
    page.wait_for_timeout(1200)

    return {
        "company": company,
        "date": date,
        "address": address,
        "total": total,
        "draft_lists_missing_date": "Missing fields: date" in draft,
    }


def _record(browser, url, *, runs, pause_ms, video_dir, tag_prefix, capture_first):
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 900},
        record_video_dir=str(video_dir),
        record_video_size={"width": 1280, "height": 900},
    )
    page = ctx.new_page()
    page.goto(url, wait_until="load")
    page.wait_for_timeout(2500)
    results = []
    for i in range(runs):
        capture = capture_first and i == 0
        tag = "" if capture else f"{tag_prefix}{i + 1}"
        results.append(run_flow(page, pause_ms=pause_ms, capture=capture, tag=tag))
    page.wait_for_timeout(2000)
    page.close()
    ctx.close()
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:7861")
    parser.add_argument("--pause-ms", type=int, default=2500)
    parser.add_argument("--baseline-runs", type=int, default=2)
    parser.add_argument("--final-runs", type=int, default=2)
    args = parser.parse_args()

    SHOTS.mkdir(exist_ok=True)
    if not RECEIPT.exists():
        raise SystemExit(f"missing receipt image: {RECEIPT} (run scripts/make_demo_receipt.py)")

    raw_dir = SHOTS / "_video_raw"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True)

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)

        results += _record(
            browser, args.url,
            runs=args.baseline_runs, pause_ms=args.pause_ms,
            video_dir=raw_dir / "baseline", tag_prefix="b",
            capture_first=True,
        )
        results += _record(
            browser, args.url,
            runs=args.final_runs, pause_ms=args.pause_ms,
            video_dir=raw_dir / "final", tag_prefix="final",
            capture_first=False,
        )
        browser.close()

    for label, dest in (
        ("baseline", "backup_baseline.webm"),
        ("final", "backup_final_both_models.webm"),
    ):
        vids = list((raw_dir / label).glob("*.webm"))
        if vids:
            shutil.move(str(vids[0]), str(SHOTS / dest))
            print(f"video: {SHOTS / dest}")
    shutil.rmtree(raw_dir, ignore_errors=True)

    # Keep only the four canonical screenshots; drop per-run duplicates.
    for suffix in ("-b1", "-b2", "-final1", "-final2", "-run1", "-run2"):
        for png in SHOTS.glob(f"*{suffix}.png"):
            png.unlink()

    print("runs:")
    for i, r in enumerate(results, 1):
        print(f"  run {i}: {r}")


if __name__ == "__main__":
    main()
