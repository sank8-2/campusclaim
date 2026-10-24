"""Tests for the dependency-free inference adapter.

Run with:

    python3 -m unittest discover -s tests -v
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.inference import (  # noqa: E402
    INSTRUCTION,
    build_infer_fn,
    parse_receipt_json,
)


class _FakeTensor:
    """Just enough of a tensor for slicing and ``.shape``."""

    def __init__(self, values, shape=None):
        self.values = list(values)
        self.shape = shape or (1, len(self.values))

    def __getitem__(self, index):
        if isinstance(index, slice):
            return _FakeTensor(self.values[index])
        return self.values[index]


class _FakeOutput:
    """A batch of generated token tensors."""

    def __init__(self, rows):
        self.rows = rows

    def __getitem__(self, index):
        return self.rows[index]


class _FakeBatch(dict):
    def __init__(self, payload, device="cpu"):
        super().__init__(payload)
        self.device = device

    def to(self, device):
        self.device = device
        return self


class _FakeProcessor:
    def __init__(self, reply):
        self.reply = reply
        self.chat_calls = []
        self.batches = []
        self.call_kwargs = None
        self.image = None
        self.text = None
        self.decoded = None

    def apply_chat_template(self, messages, add_generation_prompt=False):
        self.chat_calls.append((messages, add_generation_prompt))
        return "PROMPT"

    def __call__(self, image, text, **kwargs):
        self.image = image
        self.text = text
        self.call_kwargs = kwargs
        batch = _FakeBatch(
            {
                "input_ids": _FakeTensor([101, 102, 103]),
                "attention_mask": _FakeTensor([1, 1, 1]),
            }
        )
        self.batches.append(batch)
        return batch

    def decode(self, token_ids, skip_special_tokens=True):
        self.decoded = list(token_ids.values)
        return self.reply


class _FakeModel:
    def __init__(self, device="cpu"):
        self.device = device
        self.generate_kwargs = None

    def generate(self, **kwargs):
        self.generate_kwargs = kwargs
        return _FakeOutput([_FakeTensor([101, 102, 103, 201, 202])])


class ParseReceiptJsonTests(unittest.TestCase):
    def test_plain_json_object(self):
        self.assertEqual(
            parse_receipt_json('{"company": "Campus Print Hub", "total": "431.50"}'),
            {"company": "Campus Print Hub", "total": "431.50"},
        )

    def test_fenced_json(self):
        text = '```json\n{"company": "Fenced", "total": "1.00"}\n```'
        self.assertEqual(parse_receipt_json(text), {"company": "Fenced", "total": "1.00"})

    def test_json_inside_prose(self):
        text = 'Here is the extraction:\n{"company": "Prose", "date": "2026-10-24"}\nHope that helps.'
        self.assertEqual(
            parse_receipt_json(text),
            {"company": "Prose", "date": "2026-10-24"},
        )

    def test_nested_object_is_kept_whole(self):
        text = '{"company": "Nested", "extra": {"line": 1}}'
        self.assertEqual(parse_receipt_json(text), {"company": "Nested", "extra": {"line": 1}})

    def test_first_object_wins(self):
        self.assertEqual(parse_receipt_json('{"a": 1} {"b": 2}'), {"a": 1})

    def test_non_object_json_before_object_is_skipped(self):
        self.assertEqual(parse_receipt_json('[1, 2] then {"a": 1}'), {"a": 1})

    def test_invalid_or_missing_json_returns_empty_dict(self):
        for text in ("", None, "I could not read the receipt.", "{company: Campus}", "{broken"):
            with self.subTest(text=text):
                self.assertEqual(parse_receipt_json(text), {})

    def test_instruction_matches_the_notebook(self):
        notebook = json.loads((ROOT / "notebooks" / "campusclaim_3b.ipynb").read_text())
        text = "\n".join(
            "".join(cell["source"])
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
        )
        self.assertIn(INSTRUCTION, text)


class BuildInferFnTests(unittest.TestCase):
    def test_returns_parsed_dict_and_mirrors_the_notebook_calls(self):
        processor = _FakeProcessor('{"company": "Campus Print Hub", "total": "431.50"}')
        model = _FakeModel()
        infer_json = build_infer_fn(model, processor, max_new_tokens=42)

        result = infer_json(model, "receipt-image")

        self.assertEqual(result, {"company": "Campus Print Hub", "total": "431.50"})
        self.assertEqual(len(processor.chat_calls), 1)
        messages, add_generation_prompt = processor.chat_calls[0]
        self.assertTrue(add_generation_prompt)
        self.assertEqual(messages[0]["content"][0], {"type": "image"})
        self.assertEqual(messages[0]["content"][1], {"type": "text", "text": INSTRUCTION})

        self.assertEqual(processor.image, "receipt-image")
        self.assertEqual(processor.text, "PROMPT")
        self.assertIs(processor.call_kwargs["tokenize"], True)
        self.assertIs(processor.call_kwargs["return_dict"], True)
        self.assertEqual(processor.call_kwargs["return_tensors"], "pt")
        self.assertIs(processor.call_kwargs["add_special_tokens"], False)

        self.assertEqual(model.generate_kwargs["max_new_tokens"], 42)
        self.assertIs(model.generate_kwargs["do_sample"], False)
        self.assertIs(model.generate_kwargs["use_cache"], True)

    def test_decodes_only_the_new_tokens(self):
        processor = _FakeProcessor('{"company": "Only new"}')
        infer_json = build_infer_fn(_FakeModel(), processor)

        infer_json(_FakeModel(), "receipt-image")

        self.assertEqual(processor.decoded, [201, 202])

    def test_inputs_move_to_the_model_device(self):
        processor = _FakeProcessor('{"company": "Moved"}')
        model = _FakeModel(device="cuda:0")

        infer_json = build_infer_fn(model, processor)
        infer_json(model, "receipt-image")

        self.assertEqual(processor.batches[-1].device, "cuda:0")

    def test_bad_model_output_returns_empty_dict(self):
        processor = _FakeProcessor("I cannot read this receipt.")
        infer_json = build_infer_fn(_FakeModel(), processor)

        self.assertEqual(infer_json(_FakeModel(), "receipt-image"), {})

    def test_uses_the_model_argument_passed_to_the_callable(self):
        processor = _FakeProcessor('{"company": "Called"}')
        builder_model = _FakeModel(device="cpu")
        call_model = _FakeModel(device="cpu")

        infer_json = build_infer_fn(builder_model, processor)
        infer_json(call_model, "receipt-image")

        self.assertIsNotNone(call_model.generate_kwargs)
        self.assertIsNone(builder_model.generate_kwargs)


class ImportSafetyTests(unittest.TestCase):
    def test_importing_app_inference_does_not_import_torch(self):
        code = "import sys, app.inference; print('torch' in sys.modules)"
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False")


if __name__ == "__main__":
    unittest.main()
