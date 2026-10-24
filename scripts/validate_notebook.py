#!/usr/bin/env python3
"""Pre-flight checks for the 3B notebook.

Run before uploading the notebook to Colab:

    python3 scripts/validate_notebook.py

It checks that every code cell compiles, that the frozen evaluation sample in
the notebook matches ``data/eval_keys_seed0.json`` and the test manifest, and
that the cells the run depends on are still present.
"""

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "campusclaim_3b.ipynb"
EVAL_KEYS = ROOT / "data" / "eval_keys_seed0.json"
MANIFEST = ROOT / "data" / "sroie_test_manifest.json"

REQUIRED_MARKERS = {
    "smoke test": "smoke = eval_rows[0]",
    "baseline": "baseline_records = evaluate_vision",
    "fine-tuned eval": "tuned_records = evaluate_vision",
    "results export": "baseline_metrics.to_json",
    "gradio app": "import gradio as gr",
    "adapter save": "save_pretrained",
}


def code_cells(notebook):
    return [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]


def check_syntax(cells):
    problems = []
    for index, cell in enumerate(cells):
        source = "".join(cell["source"])
        # The install cell is shell/magic, not Python.
        if "%%" in source or re.search(r"^\s*!", source, re.MULTILINE):
            continue
        try:
            compile(source, f"cell-{index}", "exec")
        except SyntaxError as error:
            problems.append(f"cell {index}: line {error.lineno}: {error.msg}")
    return problems


def check_keys(cells):
    source = next(
        ("".join(cell["source"]) for cell in cells if "EVAL_KEYS = [" in "".join(cell["source"])),
        None,
    )
    if source is None:
        return ["no EVAL_KEYS literal found"]

    match = re.search(r"EVAL_KEYS = (\[.*?\])", source, re.DOTALL)
    if not match:
        return ["could not parse the EVAL_KEYS list"]
    try:
        embedded = ast.literal_eval(match.group(1))
    except (ValueError, SyntaxError) as error:
        return [f"EVAL_KEYS is not a plain list: {error}"]

    frozen = json.loads(EVAL_KEYS.read_text())["keys"]
    manifest = {row["key"] for row in json.loads(MANIFEST.read_text())["rows"]}

    problems = []
    if len(embedded) != 100:
        problems.append(f"notebook has {len(embedded)} keys, expected 100")
    if len(set(embedded)) != len(embedded):
        problems.append("notebook keys contain duplicates")
    if embedded != frozen:
        problems.append("notebook keys differ from data/eval_keys_seed0.json")
    missing = sorted(set(embedded) - manifest)
    if missing:
        problems.append(f"{len(missing)} notebook keys are missing from the manifest: {missing[:3]}")
    return problems


def check_markers(cells):
    text = "\n".join("".join(cell["source"]) for cell in cells)
    return [f"missing {name}" for name, marker in REQUIRED_MARKERS.items() if marker not in text]


def main():
    if not NOTEBOOK.exists():
        print(f"FAIL: missing {NOTEBOOK}")
        return 1

    notebook = json.loads(NOTEBOOK.read_text())
    cells = code_cells(notebook)

    problems = []
    problems += check_syntax(cells)
    problems += check_keys(cells)
    problems += check_markers(cells)

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1

    print(f"OK: {len(cells)} code cells, 100 frozen keys, all required cells present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
