import unittest

from app.ocr_extract import (
    OcrLine,
    _find_date,
    _find_total,
    parse_lines,
    parse_lines_naive,
)


def line(text, x, y, width=200, height=24, confidence=0.9):
    return OcrLine(text=text, x=x, y=y, width=width, height=height, confidence=confidence)


def receipt_lines():
    return [
        line("CAMPUS PRINT HUB", 152, 46, 337, 26),
        line("Block C, University Road", 210, 85, 221, 24),
        line("Bengaluru 560001", 238, 113, 164, 23),
        line("Date", 46, 174, 50, 26),
        line("24/10/2026", 489, 176, 103, 21),
        line("Receipt #", 48, 209, 89, 25),
        line("CPH-00431", 486, 210, 106, 21),
        line("Cashier", 48, 243, 70, 24),
        line("R. Kumar", 501, 242, 80, 24),
        line("SUBTOTAL", 50, 441, 100, 26),
        line("431.50", 517, 440, 60, 24),
        line("TOTAL (RM)", 49, 484, 120, 26),
        line("431.50", 485, 484, 60, 24),
        line("GST Reg:29ABCDE1234F1Z5", 183, 841, 280, 20),
    ]


class OcrExtractTests(unittest.TestCase):
    def test_layout_aware_parse_reads_all_fields(self):
        fields = parse_lines(receipt_lines(), 900)
        self.assertEqual(fields["company"], "CAMPUS PRINT HUB")
        self.assertEqual(fields["date"], "24/10/2026")
        self.assertEqual(fields["address"], "Block C, University Road, Bengaluru 560001")
        self.assertEqual(fields["total"], "431.50")

    def test_naive_parse_uses_first_lines(self):
        fields = parse_lines_naive(receipt_lines())
        self.assertEqual(fields["company"], "CAMPUS PRINT HUB")
        self.assertEqual(fields["address"], "Block C, University Road")
        self.assertEqual(fields["total"], "431.50")

    def test_total_ignores_subtotal(self):
        lines = [
            line("SUBTOTAL", 50, 300, 90, 24),
            line("100.00", 400, 300, 60, 24),
            line("TOTAL", 50, 350, 60, 24),
            line("200.00", 400, 350, 60, 24),
        ]
        self.assertEqual(_find_total(lines), "200.00")

    def test_total_on_same_line(self):
        self.assertEqual(_find_total([line("Grand Total: 1,234.50", 50, 400, 250, 24)]), "1234.50")

    def test_date_formats(self):
        self.assertEqual(_find_date([line("Date 24/10/2026", 10, 10)]), "24/10/2026")
        self.assertEqual(_find_date([line("2026-10-24", 10, 10)]), "2026-10-24")
        self.assertEqual(_find_date([line("24 Oct 2026", 10, 10)]), "24 Oct 2026")

    def test_company_named_campus_is_not_treated_as_address(self):
        lines = [
            line("CAMPUS PRINT HUB", 100, 40, 300, 28),
            line("12 Main Road", 120, 80, 200, 22),
            line("Date", 40, 140, 50, 22),
        ]
        fields = parse_lines(lines, 600)
        self.assertEqual(fields["company"], "CAMPUS PRINT HUB")

    def test_company_falls_back_when_no_clear_title(self):
        lines = [line("Corner Store", 10, 10, 150, 20)]
        self.assertEqual(parse_lines(lines, 400)["company"], "Corner Store")


if __name__ == "__main__":
    unittest.main()
