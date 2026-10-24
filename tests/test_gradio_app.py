import unittest

from app.gradio_app import build_claim_draft, extract_and_prefill, make_dual_model_extractors


class _ModelStub:
    def __init__(self):
        self.calls = []

    def disable_adapter(self):
        self.calls.append("disable")

    def enable_adapter(self):
        self.calls.append("enable")


class GradioAppLogicTests(unittest.TestCase):
    def test_claim_draft_reports_missing_fields(self):
        draft = build_claim_draft("Store", "", "Campus", "")
        self.assertIn("Missing fields: date, total", draft)

    def test_prefill_uses_tuned_json(self):
        class _Service:
            def extract(self, _image):
                return ({"company": "plain"}, {"company": "tuned", "date": "2026-10-24", "address": "A", "total": "10"})

        plain, tuned, company, date, address, total, draft = extract_and_prefill("image", _Service())
        self.assertEqual(plain["company"], "plain")
        self.assertEqual(tuned["company"], "tuned")
        self.assertEqual((company, date, address, total), ("tuned", "2026-10-24", "A", "10"))
        self.assertIn("Missing fields: none", draft)

    def test_plain_path_disables_then_enables_adapter(self):
        model = _ModelStub()

        def infer_json(_model, _image):
            return {"company": "ok"}

        service = make_dual_model_extractors(model, infer_json)
        plain, tuned = service.extract("image")

        self.assertEqual(plain["company"], "ok")
        self.assertEqual(tuned["company"], "ok")
        self.assertEqual(model.calls, ["disable", "enable"])


if __name__ == "__main__":
    unittest.main()
