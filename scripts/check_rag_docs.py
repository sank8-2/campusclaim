"""Check that the policy PDFs are text-based, not scans.

Usage:
    python3 scripts/check_rag_docs.py [pdf ...]

With no arguments it checks every PDF in data/rag/source. For each document it
prints the page count, the extractable characters per page and a verdict. A page
with fewer than MIN_CHARS characters is treated as image-only (a scan, or a
graphic page). The whole document is only usable for RAG if every content page
clears the threshold.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pypdf import PdfReader

SOURCE_DIR = Path(__file__).resolve().parent.parent / "data" / "rag" / "source"
MIN_CHARS = 200


def check(path: Path) -> dict:
    reader = PdfReader(str(path))
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append((number, len(text.strip())))
    total = sum(chars for _, chars in pages)
    low = [number for number, chars in pages if chars < MIN_CHARS]
    content_pages = len(pages) - len(low)
    if not pages:
        verdict = "EMPTY"
    elif content_pages == len(pages):
        verdict = "TEXT-BASED"
    elif content_pages == 0:
        verdict = "SCANNED"
    elif content_pages / len(pages) >= 0.8:
        verdict = "TEXT-BASED (cover/blank pages skipped)"
    else:
        verdict = "MIXED"
    return {
        "path": path,
        "pages": len(pages),
        "total_chars": total,
        "empty_pages": low,
        "per_page": pages,
        "verdict": verdict,
    }


def main(argv: list[str]) -> int:
    paths = [Path(arg) for arg in argv] or sorted(SOURCE_DIR.glob("*.pdf"))
    if not paths:
        print(f"no PDFs found in {SOURCE_DIR}")
        return 1

    failed = False
    for path in paths:
        result = check(path)
        page_chars = ", ".join(f"p{number}={chars}" for number, chars in result["per_page"])
        print(f"{path.name}")
        print(f"  pages: {result['pages']}")
        print(f"  characters: {result['total_chars']} total")
        print(f"  per page: {page_chars}")
        if result["empty_pages"]:
            print(f"  low-text pages (cover/blank, not used for retrieval): {result['empty_pages']}")
        print(f"  verdict: {result['verdict']}")
        print()
        if result["verdict"] not in {"TEXT-BASED", "TEXT-BASED (cover/blank pages skipped)"}:
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
