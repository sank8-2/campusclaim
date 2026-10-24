"""Inference adapter for the CampusClaim receipt extractor.

This mirrors ``generate_from_image`` in ``notebooks/campusclaim_3b.ipynb`` so the
standalone app and the notebook call the processor and chat template the same
way. Keep the two in sync if the notebook changes.

The module is import-safe: ``torch``, ``transformers``, ``gradio`` and ``unsloth``
are only imported inside the functions that need them, so the tests and the
dummy-mode app run on the standard library alone.
"""

from __future__ import annotations

import json
from contextlib import nullcontext
from typing import Any, Callable, Dict

INSTRUCTION = (
    "Extract the company, date, address and total from this receipt. "
    "Reply with JSON only."
)

MAX_IMAGE_SIDE = 1600


def parse_receipt_json(text: str) -> Dict[str, Any]:
    """Return the first JSON object in ``text``, or ``{}`` when there is none.

    The model is asked for JSON only, but a reply can still be wrapped in a
    markdown fence or a sentence. Scan for the first ``{`` that starts a valid
    JSON object and return it. Invalid or non-object JSON yields ``{}``.
    """
    if not text:
        return {}

    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return {}


def _prepare_image(image: Any, max_side: int = MAX_IMAGE_SIDE) -> Any:
    """Downscale a PIL image exactly like the notebook's ``prepare_image``.

    Anything that is not a PIL-like image (for example the string sentinel used
    by the demo pipeline and tests) is passed through untouched.
    """
    if not (hasattr(image, "convert") and hasattr(image, "thumbnail")):
        return image
    prepared = image.convert("RGB")
    prepared.thumbnail((max_side, max_side))
    return prepared


def _model_device(model: Any) -> Any:
    """Best-effort device lookup so inputs land where the weights are."""
    device = getattr(model, "device", None)
    if device is not None:
        return device
    try:
        return next(model.parameters()).device
    except (AttributeError, StopIteration, TypeError):
        return "cpu"


def _inference_context():
    """Use ``torch.inference_mode`` when torch is available.

    Falling back to a no-op context keeps the fake-model tests dependency-free;
    the real model always has torch installed.
    """
    try:
        import torch
    except ImportError:
        return nullcontext()
    return torch.inference_mode()


def build_infer_fn(
    model: Any,
    processor: Any,
    instruction: str = INSTRUCTION,
    max_new_tokens: int = 160,
) -> Callable[[Any, Any], Dict[str, Any]]:
    """Build the ``infer_json(model, image) -> dict`` callable the app expects.

    The processor/chat-template calls mirror the notebook's
    ``generate_from_image``: one user message with an image placeholder and the
    instruction, an applied chat template with ``add_generation_prompt=True``,
    tokenised inputs moved to the model's device, and a greedy generation whose
    new tokens are decoded and parsed as JSON.
    """

    def infer_json(loaded_model: Any, image: Any) -> Dict[str, Any]:
        active_model = loaded_model if loaded_model is not None else model

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": instruction},
                ],
            }
        ]
        prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = processor(
            _prepare_image(image),
            prompt,
            add_special_tokens=False,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )

        device = _model_device(active_model)
        if hasattr(inputs, "to"):
            inputs = inputs.to(device)

        prompt_tokens = inputs["input_ids"].shape[1]
        with _inference_context():
            outputs = active_model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                use_cache=True,
                do_sample=False,
            )

        new_tokens = outputs[0][prompt_tokens:]
        reply = processor.decode(new_tokens, skip_special_tokens=True).strip()
        return parse_receipt_json(reply)

    return infer_json
