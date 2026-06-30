#!/usr/bin/env bash
# run_poster_figures.sh — regenerate all PGF figures for the A1 poster.
#
# Sets DP_POSTER_RUN=1 so that analysis scripts:
#   • use poster-optimised font sizes (one step smaller than thesis)
#   • save to {stem}_poster.pgf instead of overwriting the thesis figures
#
# After running this script, build the poster with:
#   cd latex && latexmk -pdf -interaction=nonstopmode poster.tex
#
# The thesis figures (*.pgf without _poster suffix) are unaffected.

set -euo pipefail
cd "$(dirname "$0")"

export DP_POSTER_RUN=1

# Activate venv if present
if [[ -f ../.venv/bin/activate ]]; then
    # shellcheck disable=SC1091
    source ../.venv/bin/activate
fi

echo "=== Generating poster figures (DP_POSTER_RUN=1) ==="

python analyses/eu_pokryti_kv_mapa.py
python analyses/eu_hustota_mapa.py
python analyses/eu_apz_vydaje.py
python analyses/problemy_cz_model.py
python analyses/korelace_analyza.py
python analyses/practical_ternary_social_dialog.py

echo ""
echo "=== Done.  Poster PGF files written to python/figures/*_poster.pgf ==="
echo "    Build poster: cd latex && latexmk -pdf -interaction=nonstopmode poster.tex"
