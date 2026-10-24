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
        """Read the uploaded receipt locally with OCR (no adapter needed)."""
        try:
            from .ocr_extract import CachedOcr, parse_lines, parse_lines_naive
        except ImportError:  # `python app/gradio_app.py`
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


APP_CSS = """
:root {
    --ht-ink: #10201d;
    --ht-paper: #f7f7f2;
    --ht-cream: #f2f2eb;
    --ht-forest: #3d5f58;
    --ht-forest-deep: #2e4742;
    --ht-muted: #52635f;
    --ht-red: #e53927;
    --ht-salmon: #e97b77;
    --ht-pink: #f6c4c1;
    --ht-sky: #8bb2de;
    --ht-ochre: #f5b726;
    --ht-shadow: #671912;
    --ht-line: #e4e5da;
    --ht-mono: "Martian Mono", ui-monospace, "SFMono-Regular", "Cascadia Code",
        "Roboto Mono", Menlo, Consolas, monospace;
    --ht-display: "Barlow Semi Condensed", "Helvetica Neue", Helvetica, Arial, sans-serif;
}

body,
.gradio-container {
    background: var(--ht-cream) !important;
    color: var(--ht-ink);
}

/* paper grain, same recipe as hacktoberfest.com */
.gradio-container::after {
    content: "";
    position: fixed;
    inset: 0;
    z-index: 50;
    pointer-events: none;
    opacity: 0.05;
    mix-blend-mode: multiply;
    background-image:
        radial-gradient(circle, rgba(24, 37, 34, 0.6) 0 0.45px, transparent 0.65px),
        radial-gradient(circle, rgba(247, 247, 242, 0.6) 0 0.35px, transparent 0.55px);
    background-position: 0 0, 4px 5px;
    background-size: 7px 7px, 11px 11px;
}

#app-shell {
    max-width: 1160px;
    margin: 0 auto;
}

.hero {
    padding: clamp(28px, 4vw, 44px) clamp(20px, 4vw, 40px);
    border: 2px solid var(--ht-ink);
    background: var(--ht-forest);
    box-shadow: 7px 7px 0 var(--ht-shadow);
    text-align: center;
}

.hero .ht-eyebrow {
    margin: 0;
    color: var(--ht-pink);
    font-family: var(--ht-mono);
    font-size: 0.74rem;
    font-weight: 400;
    letter-spacing: 0.08em;
    line-height: 1.6;
    text-transform: uppercase;
}

.hero h1 {
    margin: 14px 0 0;
    color: var(--ht-paper) !important;
    font-family: var(--ht-display);
    font-size: clamp(2.6rem, 5.4vw, 3.9rem);
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 0.95;
    text-wrap: balance;
}

.hero h1 em {
    display: block;
    color: var(--ht-salmon);
    font-style: normal;
}

.hero .ht-hero-copy {
    margin: 16px auto 0;
    max-width: 52ch;
    color: rgba(247, 247, 242, 0.86);
    font-size: 0.98rem;
    line-height: 1.55;
    text-wrap: balance;
}

.section-title {
    display: flex;
    align-items: center;
    gap: 9px;
    margin: 0 0 12px;
    color: var(--ht-ink);
    font-family: var(--ht-mono);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
}

.section-title::before {
    content: "";
    display: block;
    width: 9px;
    height: 9px;
    flex: 0 0 auto;
    background: var(--ht-ochre);
    box-shadow: 2px 2px 0 var(--ht-ink);
}

.section-title.tone-sky::before {
    background: var(--ht-sky);
}

.section-title.tone-salmon::before {
    background: var(--ht-salmon);
}

.section-title.tone-red::before {
    background: var(--ht-red);
}

.gradio-container label > span {
    color: var(--ht-muted);
    font-family: var(--ht-mono);
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.gradio-container button {
    font-family: var(--ht-mono);
    font-weight: 600;
    letter-spacing: 0.02em;
}

.gradio-container input:focus-visible,
.gradio-container textarea:focus-visible {
    outline: 3px solid var(--ht-sky);
    outline-offset: 2px;
}

.ht-footer {
    margin-top: 22px;
    padding-top: 14px;
    border-top: 2px solid var(--ht-ink);
    color: var(--ht-muted);
    font-family: var(--ht-mono);
    font-size: 0.66rem;
    letter-spacing: 0.08em;
    text-align: center;
    text-transform: uppercase;
}

.ht-footer strong {
    color: var(--ht-ink);
    font-weight: 700;
}
"""


def build_theme():
    import gradio as gr

    return gr.themes.Base(
        primary_hue=gr.themes.colors.red,
        secondary_hue=gr.themes.colors.green,
        neutral_hue=gr.themes.colors.stone,
        font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("Martian Mono"), "ui-monospace", "monospace"],
    ).set(
        body_background_fill="#f2f2eb",
        body_background_fill_dark="#f2f2eb",
        body_text_color="#10201d",
        body_text_color_dark="#10201d",
        body_text_color_subdued="#52635f",
        body_text_color_subdued_dark="#52635f",
        background_fill_primary="#f7f7f2",
        background_fill_primary_dark="#f7f7f2",
        background_fill_secondary="#e4e5da",
        background_fill_secondary_dark="#e4e5da",
        border_color_primary="#10201d",
        border_color_primary_dark="#10201d",
        border_color_accent="#e53927",
        border_color_accent_dark="#e53927",
        color_accent="#e53927",
        color_accent_soft="rgba(233, 123, 119, 0.28)",
        color_accent_soft_dark="rgba(233, 123, 119, 0.28)",
        link_text_color="#1f4e6b",
        link_text_color_dark="#1f4e6b",
        link_text_color_hover="#b8301f",
        link_text_color_hover_dark="#b8301f",
        block_background_fill="#f7f7f2",
        block_background_fill_dark="#f7f7f2",
        block_border_color="#10201d",
        block_border_color_dark="#10201d",
        block_border_width="2px",
        block_radius="0px",
        block_shadow="7px 7px 0 #671912",
        block_shadow_dark="7px 7px 0 #671912",
        block_label_background_fill="#f7f7f2",
        block_label_background_fill_dark="#f7f7f2",
        block_label_border_color="#10201d",
        block_label_border_color_dark="#10201d",
        block_label_text_color="#52635f",
        block_label_text_color_dark="#52635f",
        block_title_text_color="#10201d",
        block_title_text_color_dark="#10201d",
        panel_background_fill="#f2f2eb",
        panel_background_fill_dark="#f2f2eb",
        panel_border_color="#10201d",
        panel_border_color_dark="#10201d",
        input_background_fill="#ffffff",
        input_background_fill_dark="#ffffff",
        input_background_fill_focus="#ffffff",
        input_background_fill_focus_dark="#ffffff",
        input_background_fill_hover="#fbfbf7",
        input_background_fill_hover_dark="#fbfbf7",
        input_border_color="#10201d",
        input_border_color_dark="#10201d",
        input_border_color_focus="#10201d",
        input_border_color_focus_dark="#10201d",
        input_border_width="2px",
        input_border_width_dark="2px",
        input_placeholder_color="#52635f",
        input_placeholder_color_dark="#52635f",
        input_radius="0px",
        input_shadow="none",
        input_shadow_dark="none",
        button_primary_background_fill="#e97b77",
        button_primary_background_fill_dark="#e97b77",
        button_primary_background_fill_hover="#f6c4c1",
        button_primary_background_fill_hover_dark="#f6c4c1",
        button_primary_text_color="#10201d",
        button_primary_text_color_dark="#10201d",
        button_primary_border_color="#10201d",
        button_primary_border_color_dark="#10201d",
        button_primary_shadow="5px 5px 0 #671912",
        button_primary_shadow_dark="5px 5px 0 #671912",
        button_primary_shadow_hover="3px 3px 0 #671912",
        button_primary_shadow_hover_dark="3px 3px 0 #671912",
        button_secondary_background_fill="#f7f7f2",
        button_secondary_background_fill_dark="#f7f7f2",
        button_secondary_background_fill_hover="#e4e5da",
        button_secondary_background_fill_hover_dark="#e4e5da",
        button_secondary_text_color="#10201d",
        button_secondary_text_color_dark="#10201d",
        button_secondary_border_color="#10201d",
        button_secondary_border_color_dark="#10201d",
        button_secondary_shadow="5px 5px 0 #671912",
        button_secondary_shadow_dark="5px 5px 0 #671912",
        button_secondary_shadow_hover="3px 3px 0 #671912",
        button_secondary_shadow_hover_dark="3px 3px 0 #671912",
        button_transform_hover="translate(2px, 2px)",
        button_transform_active="translate(2px, 2px)",
        button_border_width="2px",
        button_border_width_dark="2px",
        button_large_radius="0px",
        button_medium_radius="0px",
        button_small_radius="0px",
        checkbox_background_color_selected="#e53927",
        checkbox_background_color_selected_dark="#e53927",
        slider_color="#e53927",
        slider_color_dark="#e53927",
        table_even_background_fill="#f7f7f2",
        table_even_background_fill_dark="#f7f7f2",
        table_odd_background_fill="#e4e5da",
        table_odd_background_fill_dark="#e4e5da",
        code_background_fill="#f7f7f2",
        code_background_fill_dark="#f7f7f2",
        container_radius="0px",
    )



def build_app(service: Optional[ReceiptExtractionService] = None):
    import gradio as gr

    service = service or ReceiptExtractionService.from_ocr()

    if service.source == "ocr":
        hero_copy = (
            "Upload a receipt and CampusClaim reads it with local OCR, "
            "then builds an editable claim draft."
        )
        plain_title = "OCR baseline"
        tuned_title = "OCR parsed"
        plain_label = "OCR baseline JSON"
        tuned_label = "OCR parsed JSON"
        hint = "Parsed OCR pre-fills the fields. Edit any value to refresh the draft instantly."
    elif service.source == "dummy":
        hero_copy = (
            "Upload a receipt, compare plain vs fine&#8209;tuned extraction, then finalize a claim draft."
        )
        plain_title = "Plain model output"
        tuned_title = "Fine-tuned model output"
        plain_label = "Plain model JSON"
        tuned_label = "Fine-tuned model JSON"
        hint = "Dummy mode: these values are placeholders, not read from the image."
    else:
        hero_copy = (
            "Upload a receipt, compare plain vs fine&#8209;tuned extraction, then finalize a claim draft."
        )
        plain_title = "Plain model output"
        tuned_title = "Fine-tuned model output"
        plain_label = "Plain model JSON"
        tuned_label = "Fine-tuned model JSON"
        hint = "Fine-tuned JSON pre-fills editable fields. Edit any value to refresh the draft instantly."

    with gr.Blocks(title="CampusClaim — Receipt Extractor") as demo:
        with gr.Column(elem_id="app-shell"):
            gr.Markdown(
                f"""
                <div class="hero">
                  <p class="ht-eyebrow">Team SnakeByte &middot; Hacktoberfest 2026 &middot; October 1&ndash;31</p>
                  <h1>CampusClaim <em>receipt extractor</em></h1>
                  <p class="ht-hero-copy">{hero_copy}</p>
                </div>
                """
            )
            with gr.Row():
                with gr.Column(scale=5):
                    gr.Markdown('<div class="section-title tone-sky">Receipt upload</div>')
                    receipt_image = gr.Image(
                        type="pil",
                        label="Receipt image",
                        height=360,
                        # Gradio mirrors webcams by default (selfie mode). Receipts
                        # must stay unflipped so text and OCR stay readable.
                        webcam_options=gr.WebcamOptions(mirror=False),
                    )
                with gr.Column(scale=3):
                    gr.Markdown('<div class="section-title">Actions</div>')
                    extract_button = gr.Button("Extract fields", variant="primary")
                    reset_button = gr.Button("Reset", variant="secondary")
                    gr.Markdown(hint)

            with gr.Row():
                with gr.Column():
                    gr.Markdown(f'<div class="section-title tone-salmon">{plain_title}</div>')
                    plain_box = gr.JSON(label=plain_label)
                with gr.Column():
                    gr.Markdown(f'<div class="section-title tone-sky">{tuned_title}</div>')
                    tuned_box = gr.JSON(label=tuned_label)

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
                buttons=["copy"],
            )

            gr.Markdown(
                '<div class="ht-footer">Team <strong>SnakeByte</strong> · Built for <strong>Hacktoberfest 2026</strong> · CampusClaim receipt extraction</div>'
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
    app.launch(
        server_name=args.host,
        server_port=args.port,
        theme=build_theme(),
        css=APP_CSS,
    )


if __name__ == "__main__":
    main()
