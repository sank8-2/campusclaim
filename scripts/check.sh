#!/usr/bin/env bash
# Local pre-flight checks. Run from anywhere:
#
#     scripts/check.sh
#
# This is the same sequence CI runs: compile/frozen-key validation for the
# notebook, then the standard-library unit tests.
set -euo pipefail

cd "$(dirname "$0")/.."

python3 scripts/validate_notebook.py
python3 -m unittest discover -s tests -v
