#!/usr/bin/env bash
# run.sh – run any python/analyses/* script using the project virtual environment.
#
# Looks for the venv in this order:
#   1. python/.venv        (created by setup_venv.sh, preferred)
#   2. <repo-root>/.venv   (VS Code / manual activation layout)
#   3. /tmp/dp_venv        (WSL2 fallback)
#   4. ~/.venvs/dp_thesis  (legacy location)
#
# Usage (call from anywhere):
#   bash run.sh analyses/gdp_ppp_timeline.py
#   bash run.sh analyses/arope_example.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Resolve venv: project-local first, then /tmp (WSL2), then legacy home location
if [[ -n "${VENV_DIR:-}" && -f "$VENV_DIR/bin/activate" ]]; then
    : # user-supplied override
elif [[ -f "$SCRIPT_DIR/.venv/bin/activate" ]]; then
    VENV_DIR="$SCRIPT_DIR/.venv"
elif [[ -f "$REPO_DIR/.venv/bin/activate" ]]; then
    VENV_DIR="$REPO_DIR/.venv"
elif [[ -f /tmp/dp_venv/bin/activate ]]; then
    VENV_DIR="/tmp/dp_venv"
elif [[ -f "$HOME/.venvs/dp_thesis/bin/activate" ]]; then
    VENV_DIR="$HOME/.venvs/dp_thesis"
else
    echo "No virtual environment found. Run: bash $SCRIPT_DIR/setup_venv.sh" >&2
    exit 1
fi

source "$VENV_DIR/bin/activate"

cd "$SCRIPT_DIR"
exec python "$@"
