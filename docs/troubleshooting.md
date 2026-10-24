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

## `CUDA out of memory`

Try these in order, restarting the runtime after each:

1. **Runtime → Restart runtime**, then run from the top.
2. Set `MAX_IMAGE_SIDE = 1024` (from 1600) in the dataset cell.
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
