#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-/workspace/DP2026}"
VENV_PATH="$REPO_DIR/.venv"

cd "$REPO_DIR/python"

if [[ ! -f "$VENV_PATH/bin/activate" ]]; then
    python3 -m venv --copies "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"
python -m pip install --upgrade pip
pip install -r requirements.txt

RUN_PYTHON_ANALYTICS=1 bash run.sh stats_analytics.py

cd "$REPO_DIR/latex"
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex

printf '\nContainer verification finished successfully.\n'
