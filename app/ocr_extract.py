"""Local OCR receipt extraction for the standalone Gradio fallback app.

The primary demo uses Gemma 4 in the notebook. This module lets the fallback app
read the uploaded receipt instead of showing dummy placeholders:

* ``extract_fields``       - layout-aware parse (company, date, address, total)
* ``extract_fields_naive`` - deliberately simple baseline parse

Both share a single OCR pass per image.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

REQUIRED_FIELDS = ("company", "date", "address", "total")

_DATE_RES = (
    re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b"),
    re.compile(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b"),
    re.compile(r"\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{2,4}\b", re.I),
    re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{2,4}\b", re.I),
)

_AMOUNT_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)(?![\d])")

_LABEL_RE = re.compile(
    r"^(date|receipt(?:\s*#| no)?|invoice(?:\s*#| no)?|bill(?:\s*no)?|cashier|time|order(?:\s*#)?|"
    r"table|gst|tin|tax|phone|tel|mobile|served by|server|waiter|customer|voucher)\b",
    re.I,
)

_ADDRESS_WORDS = re.compile(
    r"\b(road|rd\.?|street|st\.?|avenue|ave\.?|lane|block|sector|nagar|colony|floor|building|"
    r"suite|plot|opposite|near|bengaluru|bangalore|mumbai|delhi|pune|chennai|hyderabad|"
    r"kolkata|jaipur)\b",
    re.I,
)

_TOTAL_WORDS = ("grand total", "total due", "amount due", "balance due", "total")
_TOTAL_EXCLUDE = ("subtotal", "sub total", "sub-total", "sub-tot")


@dataclass
class OcrLine:
    text: str
    x: float
    y: float
    width: float
    height: float
    confidence: float

    @property
    def right(self) -> float:
        return self.x + self.width


_ENGINE = None


def _get_engine():
    global _ENGINE
    if _ENGINE is None:
        from rapidocr_onnxruntime import RapidOCR

        _ENGINE = RapidOCR()
    return _ENGINE


def _as_input(image: Any):
    """RapidOCR accepts a path, bytes or a numpy array; convert PIL images."""
    if isinstance(image, (str, bytes)):
        return image
    try:
        from PIL import Image
        import numpy as np

        if isinstance(image, Image.Image):
            rgb = image.convert("RGB")
            # RapidOCR/OpenCV expect BGR.
            return np.asarray(rgb)[:, :, ::-1]
    except Exception:  # pragma: no cover - optional dependency path
        pass
    return image


def image_to_lines(image: Any) -> tuple[list[OcrLine], int]:
    """Run OCR once and return y-sorted lines plus the image height."""
    height = 0
    try:
        from PIL import Image

        if isinstance(image, Image.Image):
            height = image.height
    except Exception:  # pragma: no cover
        pass

    result, _ = _get_engine()(_as_input(image))
    lines: list[OcrLine] = []
    for box, text, score in result or []:
        xs = [float(p[0]) for p in box]
        ys = [float(p[1]) for p in box]
        lines.append(
            OcrLine(
                text=str(text).strip(),
                x=min(xs),
                y=min(ys),
                width=max(xs) - min(xs),
                height=max(ys) - min(ys),
                confidence=float(score),
            )
        )
    lines.sort(key=lambda line: (round(line.y / 8), line.x))
    if not height and lines:
        height = int(max(line.y + line.height for line in lines))
    return lines, height


# ---------------------------------------------------------------------------
# Field helpers
# ---------------------------------------------------------------------------

def _find_date(lines: list[OcrLine]) -> str:
    for line in lines:
        if re.search(r"\bdate\b", line.text, re.I):
            for pattern in _DATE_RES:
                match = pattern.search(line.text)
                if match:
                    return match.group(0)
    for line in lines:
        for pattern in _DATE_RES:
            match = pattern.search(line.text)
            if match:
                return match.group(0)
    return ""


def _amounts(text: str) -> list[str]:
    cleaned = re.sub(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", " ", text)
    cleaned = re.sub(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b", " ", cleaned)
    return [m.group(1) for m in _AMOUNT_RE.finditer(cleaned)]


def _clean_amount(token: str) -> str:
    return token.replace(",", "").strip()


def _find_total(lines: list[OcrLine]) -> str:
    for index, line in enumerate(lines):
        low = line.text.lower()
        if any(word in low for word in _TOTAL_WORDS) and not any(
            word in low for word in _TOTAL_EXCLUDE
        ):
            same_line = _amounts(line.text)
            if same_line:
                return _clean_amount(same_line[-1])
            row = [
                other
                for j, other in enumerate(lines)
                if j != index
                and abs(other.y - line.y) <= max(line.height, 10) * 1.4
                and other.x > line.x
            ]
            row.sort(key=lambda other: other.x)
            for other in row:
                found = _amounts(other.text)
                if found:
                    return _clean_amount(found[-1])
            below = [
                other
                for j, other in enumerate(lines)
                if j != index
                and line.y < other.y <= line.y + max(line.height, 10) * 3
                and other.x >= line.x - 5
            ]
            below.sort(key=lambda other: (other.y, other.x))
            for other in below:
                found = _amounts(other.text)
                if found:
                    return _clean_amount(found[-1])

    fallback = [amount for line in lines for amount in _amounts(line.text)]
    if fallback:
        def as_float(value: str) -> float:
            try:
                return float(value.replace(",", ""))
            except ValueError:
                return -1.0

        return _clean_amount(max(fallback, key=as_float))
    return ""


def _is_noise(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if _LABEL_RE.match(stripped):
        return True
    if re.fullmatch(r"[\d\s.,/:-]+", stripped):
        return True
    if not re.search(r"[A-Za-z]{2,}", stripped):
        return True
    if re.search(r"\b(gst|tin|tax|reg)\b", stripped, re.I) and re.search(r"\d", stripped):
        return True
    return False


def _find_company(lines: list[OcrLine], height: int) -> str:
    if not lines:
        return ""
    top = [line for line in lines if line.y <= max(height * 0.35, 120)] or lines[:3]
    pool = [line for line in top if not _is_noise(line.text) and not _ADDRESS_WORDS.search(line.text)]
    if not pool:
        pool = [line for line in top if not _is_noise(line.text)] or top

    def score(line: OcrLine) -> tuple[float, int, float]:
        letters = sum(char.isalpha() for char in line.text)
        upper_bonus = 1.25 if line.text.isupper() else 1.0
        return (line.height * upper_bonus, letters, line.confidence)

    return max(pool, key=score).text.strip()


def _find_address(lines: list[OcrLine], company: str, height: int) -> str:
    if not lines:
        return ""
    company_index = next(
        (i for i, line in enumerate(lines) if line.text.strip() == company.strip()), 0
    )
    collected: list[str] = []
    for line in lines[company_index + 1:]:
        if line.y > max(height * 0.45, 160):
            break
        text = line.text.strip()
        if _LABEL_RE.match(text):
            break
        if _is_noise(text) or re.search(r"\b(phone|tel|mobile)\b", text, re.I):
            continue
        collected.append(text)

    if not collected:
        for line in lines:
            if line.y > max(height * 0.5, 180):
                break
            if _ADDRESS_WORDS.search(line.text):
                collected.append(line.text.strip())

    unique: list[str] = []
    for text in collected:
        if text and text not in unique:
            unique.append(text)
    return ", ".join(unique)


def parse_lines(lines: list[OcrLine], height: int) -> dict[str, str]:
    company = _find_company(lines, height)
    return {
        "company": company,
        "date": _find_date(lines),
        "address": _find_address(lines, company, height),
        "total": _find_total(lines),
    }


def parse_lines_naive(lines: list[OcrLine]) -> dict[str, str]:
    """Simple baseline: first line, first date, second line, located total."""
    texts = [line.text.strip() for line in lines if line.text.strip()]
    return {
        "company": texts[0] if texts else "",
        "date": _find_date(lines),
        "address": texts[1] if len(texts) > 1 else "",
        "total": _find_total(lines),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_fields(image: Any) -> dict[str, str]:
    """Layout-aware extraction of the four claim fields."""
    lines, height = image_to_lines(image)
    return parse_lines(lines, height)


def extract_fields_naive(image: Any) -> dict[str, str]:
    """Simple baseline: first line, first date, second line, located total."""
    lines, _ = image_to_lines(image)
    return parse_lines_naive(lines)


# ---------------------------------------------------------------------------
# Shared single OCR pass for the dual (plain/tuned) app boxes
# ---------------------------------------------------------------------------

class CachedOcr:
    """OCR an image once and reuse the lines for both parse strategies."""

    def __init__(self) -> None:
        self._image = None
        self._lines: Optional[list[OcrLine]] = None
        self._height = 0

    def lines(self, image: Any) -> tuple[list[OcrLine], int]:
        if self._image is not image:
            self._lines, self._height = image_to_lines(image)
            self._image = image
        return self._lines or [], self._height
