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
    ) -> None:
        self._plain_extractor = plain_extractor
        self._tuned_extractor = tuned_extractor

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

        return cls(dummy_plain, dummy_tuned)


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

    return ReceiptExtractionService(plain_extractor, tuned_extractor)


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

    service = service or ReceiptExtractionService.from_dummy()

    css = """
    #app-shell {
        max-width: 1160px;
        margin: 0 auto;
    }
    .hero h1 {
        margin: 0;
        font-size: 2rem;
    }
    .hero p {
        margin: 0.5rem 0 0;
        opacity: 0.9;
    }
    .section-title {
        margin: 0.25rem 0 0.75rem;
        font-weight: 700;
    }
    """

    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
    )

    with gr.Blocks(
        title="CampusClaim — Receipt Extractor",
        theme=theme,
        css=css,
    ) as demo:
        with gr.Column(elem_id="app-shell"):
            gr.Markdown(
                """
                <div class="hero">
                  <h1>CampusClaim</h1>
                  <p>Upload a receipt, compare plain vs fine-tuned extraction, then finalize a claim draft.</p>
                </div>
                """
            )
            with gr.Row():
                with gr.Column(scale=5):
                    gr.Markdown('<div class="section-title">Receipt upload</div>')
                    receipt_image = gr.Image(
                        type="pil",
                        label="Receipt image",
                        height=360,
                    )
                with gr.Column(scale=3):
                    gr.Markdown('<div class="section-title">Actions</div>')
                    extract_button = gr.Button("Extract fields", variant="primary")
                    reset_button = gr.Button("Reset", variant="secondary")
                    gr.Markdown(
                        "Fine-tuned JSON pre-fills editable fields. Edit any value to refresh the draft instantly."
                    )

            with gr.Row():
                with gr.Column():
                    gr.Markdown('<div class="section-title">Plain model output</div>')
                    plain_box = gr.JSON(label="Plain model JSON")
                with gr.Column():
                    gr.Markdown('<div class="section-title">Fine-tuned model output</div>')
                    tuned_box = gr.JSON(label="Fine-tuned model JSON")

            gr.Markdown('<div class="section-title">Editable claim fields</div>')
            with gr.Row():
                company = gr.Textbox(label="Company", interactive=True, placeholder="Company name")
                date = gr.Textbox(label="Date", interactive=True, placeholder="YYYY-MM-DD")
            with gr.Row():
                address = gr.Textbox(label="Address", interactive=True, placeholder="Receipt address")
                total = gr.Textbox(label="Total", interactive=True, placeholder="Amount")

            claim_draft = gr.Textbox(
                label="Claim draft",
                lines=10,
                interactive=False,
                show_copy_button=True,
            )

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
    if args.use_dummy:
        return ReceiptExtractionService.from_dummy()

    if not args.base_model_id or not args.adapter_path:
        raise ValueError(
            "--no-dummy requires --base-model-id and --adapter-path "
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
    parser.add_argument("--use-dummy", action="store_true", default=True)
    parser.add_argument("--no-dummy", action="store_false", dest="use_dummy")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    service = _build_service_from_args(args)
    app = build_app(service)
    app.launch(server_name=args.host, server_port=args.port)


if __name__ == "__main__":
    main()
