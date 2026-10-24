# Adapters

`campusclaim_gemma4_lora/` is the LoRA adapter saved from the Theme 3B Colab run
(`unsloth/gemma-4-E2B-it`, rank 16, 120 steps). The large weight file
`adapter_model.safetensors` is stored with Git LFS.

Reload in the standalone app:

```bash
python -m app.gradio_app --no-dummy \
  --base-model-id unsloth/gemma-4-E2B-it \
  --adapter-path adapters/campusclaim_gemma4_lora
```

Training settings are in `results/settings.json`.
