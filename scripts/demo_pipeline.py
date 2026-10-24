#!/usr/bin/env python3
"""Run the CampusClaim demo path end to end without a model.

This exercises the same code the Gradio app uses: extract the plain and tuned
JSON, prefill the four editable fields, and build the claim draft. It uses the
dummy extractors, so it needs no GPU, network, image or extra packages.

    python3 scripts/demo_pipeline.py

Writes ``results/demo_report.json`` (created if missing) and prints a summary.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.gradio_app import (  # noqa: E402
    ReceiptExtractionService,
    extract_and_prefill,
)

FIXTURE_PATH = ROOT / "data" / "demo_receipt.json"
REPORT_PATH = ROOT / "results" / "demo_report.json"


def load_fixture(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the receipt fixture. It carries labels only, never image data."""
    fixture_path = Path(path) if path is not None else FIXTURE_PATH
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def build_report(
    service: Optional[ReceiptExtractionService] = None,
    fixture: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the demo report dict without touching the filesystem."""
    service = service or ReceiptExtractionService.from_dummy()
    fixture = fixture if fixture is not None else load_fixture()
    entities = fixture.get("entities") or {}

    plain, tuned, company, date, address, total, draft = extract_and_prefill(
        "demo-receipt", service
    )
    fields = {
        "company": company,
        "date": date,
        "address": address,
        "total": total,
    }
    matches_fixture = all(
        str(entities.get(field, "")) == value for field, value in fields.items()
    )

    return {
        "fixture_entities": entities,
        "plain_json": plain,
        "tuned_json": tuned,
        "fields": fields,
        "claim_draft": draft,
        "matches_fixture": matches_fixture,
    }


def write_report(report: Dict[str, Any], path: Optional[Path] = None) -> Path:
    """Write the report as plain JSON, creating ``results/`` when needed."""
    report_path = Path(path) if path is not None else REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report_path


def format_summary(report: Dict[str, Any]) -> str:
    fields = report["fields"]
    lines = [
        "CampusClaim demo pipeline (dummy mode)",
        f"company: {fields['company']}",
        f"date: {fields['date']}",
        f"address: {fields['address']}",
        f"total: {fields['total']}",
        f"matches fixture: {'yes' if report['matches_fixture'] else 'no'}",
        "",
        report["claim_draft"],
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    print(format_summary(report))
    report_path = write_report(report)
    print(f"\nwrote {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
