from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Dict, Optional

try:  # `python -m app.gradio_app` and the tests import the package
    from .inference import INSTRUCTION, build_infer_fn
except ImportError:  # `python app/gradio_app.py`
    from inference import INSTRUCTION, build_infer_fn

REQUIRED_FIELDS = ("company", "date", "address", "total")


@dataclass
class ReceiptFields:
    company: str = ""
    date: str = ""
    address: str = ""
    total: str = ""

    @classmethod
    def from_json(cls, payload: Optional[Dict[str, Any]]) -> "ReceiptFields":
        payload = payload or {}
        return cls(
            company=str(payload.get("company", "") or ""),
            date=str(payload.get("date", "") or ""),
            address=str(payload.get("address", "") or ""),
            total=str(payload.get("total", "") or ""),
        )

    def as_tuple(self) -> tuple[str, str, str, str]:
        return (self.company, self.date, self.address, self.total)


class ReceiptExtractionService:
    def __init__(
        self,
        plain_extractor: Callable[[Any], Dict[str, Any]],
        tuned_extractor: Callable[[Any], Dict[str, Any]],
        *,
        source: str = "model",
    ) -> None:
        self._plain_extractor = plain_extractor
        self._tuned_extractor = tuned_extractor
        self.source = source

    def extract(self, image: Any) -> tuple[Dict[str, Any], Dict[str, Any]]:
        plain_payload = self._plain_extractor(image)
        tuned_payload = self._tuned_extractor(image)
        return plain_payload, tuned_payload

    @classmethod
    def from_dummy(cls) -> "ReceiptExtractionService":
        def dummy_plain(_: Any) -> Dict[str, Any]:
            return {
                "company": "Campus Print Hub",
                "date": "",
                "address": "Block C, University Road",
                "total": "",
            }

        def dummy_tuned(_: Any) -> Dict[str, Any]:
            return {
                "company": "Campus Print Hub",
                "date": "2026-10-24",
                "address": "Block C, University Road",
                "total": "431.50",
            }

        return cls(dummy_plain, dummy_tuned, source="dummy")

    @classmethod
    def from_ocr(cls) -> "ReceiptExtractionService":
        """Read the receipt locally with OCR (no model adapter required)."""
        try:
            from .ocr_extract import CachedOcr, parse_lines, parse_lines_naive
        except ImportError:
            from ocr_extract import CachedOcr, parse_lines, parse_lines_naive

        cache = CachedOcr()

        def plain_extractor(image: Any) -> Dict[str, Any]:
            lines, _ = cache.lines(image)
            return parse_lines_naive(lines)

        def tuned_extractor(image: Any) -> Dict[str, Any]:
            lines, height = cache.lines(image)
            return parse_lines(lines, height)

        return cls(plain_extractor, tuned_extractor, source="ocr")


def make_dual_model_extractors(
    model: Any,
    infer_json: Callable[[Any, Any], Dict[str, Any]],
) -> ReceiptExtractionService:
    def plain_extractor(image: Any) -> Dict[str, Any]:
        disable_adapter = getattr(model, "disable_adapter", None)
        enable_adapter = getattr(model, "enable_adapter", None)
        if callable(disable_adapter):
            disable_adapter()
        try:
            return infer_json(model, image)
        finally:
            if callable(enable_adapter):
                enable_adapter()

    def tuned_extractor(image: Any) -> Dict[str, Any]:
        return infer_json(model, image)

    return ReceiptExtractionService(plain_extractor, tuned_extractor, source="model")


def load_model_from_saved_adapter(
    base_model_id: str,
    adapter_path: str,
    *,
    device_map: str = "auto",
):
    from peft import PeftModel
    from transformers import AutoModelForImageTextToText

    base_model = AutoModelForImageTextToText.from_pretrained(
        base_model_id,
        device_map=device_map,
    )
    return PeftModel.from_pretrained(base_model, adapter_path)


def load_processor(base_model_id: str):
    from transformers import AutoProcessor

    return AutoProcessor.from_pretrained(base_model_id)


def load_inference_factory(
    spec: str,
) -> Callable[[Any, Any], Callable[[Any, Any], Dict[str, Any]]]:
    """Resolve ``module:function`` into a factory called with ``(model, processor)``."""
    module_name, separator, attribute = spec.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError(
            f"--inference-module must look like 'module:function', got {spec!r}"
        )

    module = import_module(module_name)
    factory = getattr(module, attribute, None)
    if not callable(factory):
        raise ValueError(f"{spec!r} does not resolve to a callable factory")
    return factory


def build_claim_draft(company: str, date: str, address: str, total: str) -> str:
    values = {
        "company": (company or "").strip(),
        "date": (date or "").strip(),
        "address": (address or "").strip(),
        "total": (total or "").strip(),
    }
    missing = [field for field in REQUIRED_FIELDS if not values[field]]

    lines = ["Claim draft", ""]
    lines.append(f"Company: {values['company'] or '[missing]'}")
    lines.append(f"Date: {values['date'] or '[missing]'}")
    lines.append(f"Address: {values['address'] or '[missing]'}")
    lines.append(f"Total: {values['total'] or '[missing]'}")

    if missing:
        lines.extend(["", f"Missing fields: {', '.join(missing)}"])
    else:
        lines.extend(["", "Missing fields: none"])

    return "\n".join(lines)


def extract_and_prefill(image: Any, service: ReceiptExtractionService):
    if image is None:
        empty = ReceiptFields()
        return {}, {}, *empty.as_tuple(), build_claim_draft(*empty.as_tuple())

    plain_payload, tuned_payload = service.extract(image)
    fields = ReceiptFields.from_json(tuned_payload)
    draft = build_claim_draft(*fields.as_tuple())

    return (
        plain_payload,
        tuned_payload,
        fields.company,
        fields.date,
        fields.address,
        fields.total,
        draft,
    )


def build_app(service: Optional[ReceiptExtractionService] = None):
    import gradio as gr

    service = service or ReceiptExtractionService.from_ocr()

    if service.source == "ocr":
        header = (
            "## CampusClaim receipt extraction demo\n"
            "Text is read from the uploaded receipt with local OCR. "
            "Edit any field and the claim draft updates."
        )
        plain_label, tuned_label = "OCR baseline JSON", "OCR parsed JSON"
    elif service.source == "dummy":
        header = (
            "## CampusClaim receipt extraction demo\n"
            "Dummy mode: these values are placeholders, not read from the image."
        )
        plain_label, tuned_label = "Plain model JSON", "Fine-tuned model JSON"
    else:
        header = "## CampusClaim receipt extraction demo"
        plain_label, tuned_label = "Plain model JSON", "Fine-tuned model JSON"

    with gr.Blocks(title="CampusClaim — Receipt Extractor") as demo:
        gr.Markdown(header)

        with gr.Row():
            receipt_image = gr.Image(type="pil", label="Upload receipt image")
            with gr.Column():
                extract_button = gr.Button("Extract")
                reset_button = gr.Button("Reset")

        with gr.Row():
            plain_box = gr.JSON(label=plain_label)
            tuned_box = gr.JSON(label=tuned_label)

        company = gr.Textbox(label="Company", interactive=True)
        date = gr.Textbox(label="Date", interactive=True)
        address = gr.Textbox(label="Address", interactive=True)
        total = gr.Textbox(label="Total", interactive=True)

        claim_draft = gr.Textbox(label="Claim draft", lines=8, interactive=False)

        extract_button.click(
            fn=lambda image: extract_and_prefill(image, service),
            inputs=[receipt_image],
            outputs=[plain_box, tuned_box, company, date, address, total, claim_draft],
        )

        for field in (company, date, address, total):
            field.change(
                fn=build_claim_draft,
                inputs=[company, date, address, total],
                outputs=[claim_draft],
            )

        reset_button.click(
            fn=lambda: ({}, {}, "", "", "", "", build_claim_draft("", "", "", ""), None),
            inputs=[],
            outputs=[plain_box, tuned_box, company, date, address, total, claim_draft, receipt_image],
        )

    return demo


def _build_service_from_args(args: argparse.Namespace) -> ReceiptExtractionService:
    extractor = getattr(args, "extractor", "ocr")
    if extractor == "dummy":
        return ReceiptExtractionService.from_dummy()
    if extractor == "ocr":
        return ReceiptExtractionService.from_ocr()

    if not args.base_model_id or not args.adapter_path:
        raise ValueError(
            "--extractor model requires --base-model-id and --adapter-path "
            "(the adapter directory saved by the notebook's final cell)"
        )

    model = load_model_from_saved_adapter(args.base_model_id, args.adapter_path)
    processor = load_processor(args.base_model_id)

    inference_module = getattr(args, "inference_module", None)
    if inference_module:
        factory = load_inference_factory(inference_module)
        infer_json = factory(model, processor)
        if not callable(infer_json):
            raise ValueError(
                f"--inference-module {inference_module!r} did not return a callable"
            )
    else:
        infer_json = build_infer_fn(model, processor, INSTRUCTION)

    return make_dual_model_extractors(model, infer_json)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CampusClaim Gradio app")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--base-model-id", default=None)
    parser.add_argument("--adapter-path", default=None)
    parser.add_argument(
        "--inference-module",
        default=None,
        metavar="MODULE:FUNCTION",
        help=(
            "Factory called with (model, processor) that returns a "
            "callable (model, image) -> dict. Defaults to the built-in adapter."
        ),
    )
    parser.add_argument(
        "--extractor",
        choices=["ocr", "dummy", "model"],
        default="ocr",
        help=(
            "ocr reads the receipt locally (default); dummy shows placeholders; "
            "model uses the saved adapter"
        ),
    )
    parser.add_argument(
        "--use-dummy",
        dest="extractor",
        action="store_const",
        const="dummy",
        help="alias for --extractor dummy",
    )
    parser.add_argument(
        "--no-dummy",
        dest="extractor",
        action="store_const",
        const="model",
        help="alias for --extractor model (requires --base-model-id and --adapter-path)",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    service = _build_service_from_args(args)
    app = build_app(service)
    app.launch(server_name=args.host, server_port=args.port)


if __name__ == "__main__":
    main()
