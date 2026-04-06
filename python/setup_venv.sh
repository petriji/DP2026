#!/usr/bin/env bash
# setup_venv.sh — create and populate the Python virtual environment.
#
# The virtual environment is placed inside the project at python/.venv so that
# it is self-contained and the path is predictable regardless of who clones the
# repository.
#
# The --copies flag is required when the project lives on a Windows NTFS
# filesystem mounted via WSL2 (/mnt/…), because Python's default venv creates
# a lib64 → lib symlink that NTFS does not allow.  --copies replaces every
# symlink with a real file copy (~30 MB extra, otherwise identical).
#
# Usage:
#   cd /path/to/DP/python
#   bash setup_venv.sh          # creates python/.venv
#
# Activate manually:
#   source .venv/bin/activate
#
# Run a script without activating:
#   bash run.sh analyses/gdp_ppp_timeline.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="${VENV_DIR:-.venv}"

# ── Create venv ───────────────────────────────────────────────────────────────
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment in $SCRIPT_DIR/$VENV_DIR …"
    # --copies avoids symlinks: required on NTFS (WSL2 /mnt/… mounts)
    python3 -m venv --copies "$VENV_DIR"
else
    echo "Virtual environment already exists at $SCRIPT_DIR/$VENV_DIR"
fi

# ── Activate ──────────────────────────────────────────────────────────────────
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── Install / upgrade deps ────────────────────────────────────────────────────
echo "Upgrading pip …"
pip install --upgrade pip --quiet

echo "Installing requirements …"
pip install -r requirements.txt

echo ""
echo "Done. Virtual environment is at $SCRIPT_DIR/$VENV_DIR"
echo "Activate with:  source $VENV_DIR/bin/activate"
echo "Or run a script: bash run.sh analyses/gdp_ppp_timeline.py"
