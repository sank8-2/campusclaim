# Colab troubleshooting

Run the local pre-flight first:

```bash
python3 scripts/validate_notebook.py
python3 -m unittest discover -s tests -v
```

If a cell fails in Colab, match the error below before changing the notebook.

## `ImportError: cannot import name 'FastVisionModel'`

- The install cell did not finish, or the runtime restarted.
- Re-run the install cell, then **Runtime → Restart runtime**, then start at the model-load cell.
- Do not `pip install unsloth` separately; use the starter's install cell.

## `TypeError: 'processor' object has no attribute 'tokenizer'`

- Gemma 4 returns a processor, not a tokenizer.
- Use `get_chat_template(processor, "gemma-4")` and `UnslothVisionDataCollator(model, processor)` as the notebook does.
- Do not call `processor.tokenizer`.

## `NameError: name 'INSTRUCTION' is not defined`

- The conversation cell needs the extraction prompt. Re-run that cell from the patched notebook (it defines `INSTRUCTION` locally), or re-run the model-load cell first so the name exists in the kernel.

## `Your session crashed after using all available RAM` (system RAM, not GPU)

Colab's free runtime has ~12.7 GB of **system** RAM. Kernel restarts at the dataset or training cell with debugger/`frozen modules` noise in the runtime logs are almost always this, not a Python exception.

Cause: decoding every SROIE image into a Python list before training. The notebook must keep images lazy:

- Filter on `key` / `entities` only (`select_columns`), never iterate the image column to build lists.
- Eval uses `LazyRows` (one decode per access).
- Training uses a HF `Dataset` of row indices plus `with_transform` that yields `messages` (image placeholder) and `images` (one PIL per row) only when the collator asks. Do **not** use `torch.utils.data.Dataset` (TRL 1.x rejects it) and do **not** `Dataset.from_list([to_conversation(...) for ...])` — that decodes all 625 receipts before Arrow can help.
- `MAX_IMAGE_SIDE = 1024` and `dataloader_num_workers = 0`.
- The conversation cell defines `INSTRUCTION` itself so a partial re-run after a restart does not raise `NameError`.

If the restart happens while building the training set, confirm the cell uses `with_transform` (not a full `from_list` of conversations). If it still restarts, lower `MAX_IMAGE_SIDE` to 800 and rerun from the dataset cell.

After a crash: **Runtime → Disconnect and delete runtime**, upload the patched notebook, then run from the install cell again. The HF Hub "unauthenticated requests" warning is unrelated; a token only helps rate limits.

## `Unsloth: Using float16 precision for gemma4 won't work! Using float32.`

This warning is expected on a T4, not a bug. Unsloth forces float32 for Gemma 4 because float16 produces NaN gradients. Do not set `dtype=torch.float16` or `torch_dtype=torch.float16` to silence it; the run will diverge.

Consequences on a free T4 (16 GB VRAM, ~12.7 GB system RAM):

- Keep `MAX_IMAGE_SIDE = 1024`, `BATCH_SIZE = 1`, `GRAD_ACCUM = 4`.
- If it still runs out of GPU memory, set `LORA_RANK = 8` and/or `finetune_vision_layers = False`.
- A bf16 GPU (A100/L4) or a Kaggle 2×T4 runtime with 30 GB system RAM is the robust alternative. If you switch, record it in `results/settings.json` and `docs/results.md`.

## `CUDA out of memory`

Try these in order, restarting the runtime after each:

1. **Runtime → Restart runtime**, then run from the top.
2. Confirm `MAX_IMAGE_SIDE = 1024` in the dataset cell (not 1600).
3. Set `LORA_RANK = 8` (from 16) in the LoRA cell.
4. Keep `BATCH_SIZE = 1` and `GRAD_ACCUM = 4`.
5. If it still runs out, set `finetune_vision_layers = False` and keep the language layers trainable.

Record which fallback you used. The language-only run is still a valid result, but say so in the comparison: the vision encoder is frozen, so layout adaptation is weaker. Do **not** reduce the evaluation sample; 100 is fixed.

## `RuntimeError: element 0 of tensors does not require grad`

- The LoRA target modules did not attach. Check that `FastVisionModel.get_peft_model` ran and printed trainable parameters.
- Restart and re-run the LoRA cell; do not skip it.

## Generation returns an empty string

- Ensure `model.eval()` (the evaluation function already calls it).
- Decode only the new tokens: `outputs[0][inputs["input_ids"].shape[1]:]`.
- `max_new_tokens=160` is enough for four fields; do not go below 96.

## The `datasets` download stalls

- Re-run the dataset cell; the Hugging Face hub resumes.
- Check **Runtime → Manage sessions** for disk pressure, then restart.
- Do not switch datasets mid-run; the frozen keys belong to `jsdnrs/ICDAR2019-SROIE`.

## Colab disconnected

1. Reload the base model.
2. Load the adapter zip from Drive.
3. Re-run only the evaluation and app cells.
4. The evaluation keys are embedded in the notebook; do not resample.

## `results/` is empty

- The export cell runs after the failure table. Run it after the fine-tuned evaluation.
- Refresh the file browser, then download the whole `results` folder (Colab zips it).

## `disable_adapter` is missing

- The baseline path expects a PEFT model. If `model` is the raw Unsloth model, `disable_adapter` does not exist; load the adapter with `PeftModel.from_pretrained` first.
- As a fallback, run the baseline in a second session **before** loading the adapter.

## The app cell cannot find the adapter

- The app cell uses the in-memory model, so run it after the fine-tuned evaluation in the same session.
- In a fresh runtime, load the base model and the adapter zip first, then run the app cell.

## The adapter zip is missing after a disconnect

- `model.save_pretrained("campusclaim_gemma4_lora")` runs in the save cell; run it **immediately after training**.
- Copy the folder to Drive before running the evaluation. Free Colab can disconnect without warning.
