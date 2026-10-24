"""Download the two shortlisted policy PDFs into data/rag/source/.

The PDFs are git-ignored for licence and size reasons, so fetch them before
running scripts/check_rag_docs.py or the RAG build.

Usage:
    python3 scripts/fetch_rag_docs.py [--force]

Checksums are the copies verified in docs/rag-documents.md. A download that
does not match its checksum is deleted and treated as a failure.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent.parent / "data" / "rag" / "source"

DOCUMENTS = {
    "snu_student_event_reimbursement_policy.pdf": {
        "url": "https://snu.edu.in/site/assets/files/16669/reimburesement_policy_for_students.pdf",
        "sha256": "4cb39f569273603de5d09b6ae86c74e30fb51323fe2e7311349838a8b84f2b19",
    },
    "iiituna_student_activity_council_policy.pdf": {
        "url": "https://iiitu.ac.in/assets/IIITUna-Student-Activity-Council-Policy-URsaLXRv.pdf",
        "sha256": "66e8dd7db83cb876f798eb3c25553002f2c9cde5573bc47c95e94ac8a0acdca0",
    },
}

USER_AGENT = "Mozilla/5.0 (compatible; campusclaim-rag/1.0)"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    partial = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    partial.replace(dest)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="re-download even if a copy exists")
    args = parser.parse_args(argv)

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    failed = False

    for name, meta in DOCUMENTS.items():
        dest = SOURCE_DIR / name
        if dest.exists() and not args.force:
            actual = sha256(dest)
            if actual == meta["sha256"]:
                print(f"{name}: already present (checksum OK)")
                continue
            print(f"{name}: checksum mismatch, re-downloading")

        print(f"{name}: downloading {meta['url']}")
        try:
            download(meta["url"], dest)
        except Exception as exc:  # noqa: BLE001 - report and continue with the other document
            print(f"{name}: download failed: {exc}")
            failed = True
            continue

        actual = sha256(dest)
        if actual != meta["sha256"]:
            print(f"{name}: checksum mismatch (expected {meta['sha256']}, got {actual})")
            dest.unlink(missing_ok=True)
            failed = True
        else:
            print(f"{name}: checksum OK")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
