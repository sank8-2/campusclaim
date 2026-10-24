import unittest

from app.gradio_app import (
    ReceiptFields,
    build_claim_draft,
    extract_and_prefill,
    make_dual_model_extractors,
)


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

    def test_empty_image_returns_empty_fields(self):
        class _Service:
            def extract(self, _image):
                raise AssertionError("must not call the model for an empty upload")

        plain, tuned, company, date, address, total, draft = extract_and_prefill(None, _Service())
        self.assertEqual((plain, tuned), ({}, {}))
        self.assertEqual((company, date, address, total), ("", "", "", ""))
        self.assertIn("Missing fields: company, date, address, total", draft)

    def test_adapter_is_reenabled_when_inference_raises(self):
        model = _ModelStub()

        def infer_json(_model, _image):
            raise RuntimeError("boom")

        service = make_dual_model_extractors(model, infer_json)
        with self.assertRaises(RuntimeError):
            service.extract("image")
        self.assertEqual(model.calls, ["disable", "enable"])

    def test_from_json_handles_none_and_missing_fields(self):
        self.assertEqual(ReceiptFields.from_json(None).as_tuple(), ("", "", "", ""))
        self.assertEqual(
            ReceiptFields.from_json({"company": None, "total": 12.5}).as_tuple(),
            ("", "", "", "12.5"),
        )

    def test_claim_draft_lists_all_missing_fields(self):
        draft = build_claim_draft("", "", "", "")
        self.assertIn("[missing]", draft)
        self.assertIn("Missing fields: company, date, address, total", draft)


if __name__ == "__main__":
    unittest.main()
