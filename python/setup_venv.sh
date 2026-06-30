#!/usr/bin/env bash
# setup_venv.sh — create and populate the Python virtual environment.
#
# WSL2 + Windows drive (9p/drvfs):  Python venv requires symlinks
# (lib64 → lib) which are not supported on 9p mounts.  When the project
# lives on /mnt/… the venv is created on a native Linux filesystem at
# /tmp/dp_venv instead.  A thin .venv/bin/activate shim is written so
# that `source .venv/bin/activate` and `run.sh` still work transparently.
# Note: /tmp/dp_venv does not survive a WSL restart — rerun this script.
#
# On native Linux filesystems the venv is created locally at python/.venv.
#
# Usage:
#   cd /path/to/DP/python
#   bash setup_venv.sh          # creates venv (auto-detects location)
#
# Activate manually:
#   source .venv/bin/activate
#
# Run a script without activating:
#   bash run.sh analyses/gdp_ppp_timeline.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Detect 9p / drvfs mount (Windows drive under WSL2) ───────────────────────
is_windows_mount() {
    local fstype
    fstype="$(stat -f -c '%T' "$SCRIPT_DIR" 2>/dev/null || echo unknown)"
    # 9p (WSL2 default) or drvfs (older WSL1); also match /mnt/[a-z] paths
    [[ "$fstype" == "9p" || "$fstype" == "drvfs" ]] && return 0
    [[ "$SCRIPT_DIR" =~ ^/mnt/[a-z]/ ]] && return 0
    return 1
}

if is_windows_mount; then
    VENV_DIR="/tmp/dp_venv"
    echo "Detected Windows drive mount — venv will be at $VENV_DIR"
else
    VENV_DIR="${VENV_DIR:-.venv}"
fi

# ── Create venv ───────────────────────────────────────────────────────────────
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment at $VENV_DIR …"
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# ── Activate ──────────────────────────────────────────────────────────────────
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── Install / upgrade deps ────────────────────────────────────────────────────
echo "Upgrading pip …"
pip install --upgrade pip --quiet

echo "Installing requirements …"
pip install -r "$SCRIPT_DIR/requirements.txt"

# ── Create .venv shim (Windows-mount case) ────────────────────────────────────
# Lets `source .venv/bin/activate` and run.sh work without knowing the real path.
if [[ "$VENV_DIR" != ".venv" && "$VENV_DIR" != "$SCRIPT_DIR/.venv" ]]; then
    mkdir -p "$SCRIPT_DIR/.venv/bin"
    cat > "$SCRIPT_DIR/.venv/bin/activate" <<EOF
# Auto-generated shim — redirects to the real venv at $VENV_DIR
# Recreate with: bash setup_venv.sh
source "$VENV_DIR/bin/activate"
EOF
    echo "Created .venv/bin/activate shim → $VENV_DIR"
fi

echo ""
echo "Done. Virtual environment is at $VENV_DIR"
echo "Activate with:  source .venv/bin/activate"
echo "Or run a script: bash run.sh analyses/gdp_ppp_timeline.py"
