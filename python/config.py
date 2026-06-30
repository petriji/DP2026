r"""
Central configuration for paths and figure output settings.

Adjust FIGURES_DIR to point at your LaTeX pics/ folder so figures are
immediately available to \includegraphics{} after running any script.
"""

from pathlib import Path

# ── Directories ──────────────────────────────────────────────────────────────

# Root of the python/ subtree (this file lives there)
PYTHON_DIR = Path(__file__).parent.resolve()

# Downloaded raw data – excluded from git (listed in .gitignore)
DATA_DIR = PYTHON_DIR / "data"

# Output figures consumed by the LaTeX project
# Change to an absolute path or override per-script if needed, e.g.:
#   FIGURES_DIR = PYTHON_DIR.parent / "latex" / "pics"
FIGURES_DIR = PYTHON_DIR / "figures"

# LaTeX integration
# Figures saved here are directly referenceable as '../python/figures/<name>' from latex/
LATEX_PICS_DIR = FIGURES_DIR
# Generated .tex snippets (figure/table environments) land here
LATEX_TEXPARTS_DIR = PYTHON_DIR.parent / "latex" / "texparts" / "python"
# Hand-editable PGF figure definitions (written once, never overwritten)
LATEX_FIGURES_TEX_DIR = PYTHON_DIR.parent / "latex" / "texparts" / "figures"
# Shared binary assets referenced by PGF files (deduplicated colorbars / rasters)
PGF_SHARED_ASSETS_DIR = FIGURES_DIR / "_shared"

# Create dirs on import so scripts never have to think about it
DATA_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)
# LATEX_PICS_DIR == FIGURES_DIR, no extra mkdir needed
LATEX_TEXPARTS_DIR.mkdir(parents=True, exist_ok=True)
LATEX_FIGURES_TEX_DIR.mkdir(parents=True, exist_ok=True)
PGF_SHARED_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ── Figure output format ─────────────────────────────────────────────────────
# "pdf"  – vector, best for pdflatex / lualatex  (\includegraphics{fig.pdf})
# "pgf"  – native LaTeX rendering (fonts match document), more fragile
# "svg"  – vector, needs \usepackage{svg} in LaTeX
# "png"  – raster fallback (set DPI below)
FIGURE_FORMAT: str = "pdf"
FIGURE_DPI: int = 300          # used only for raster formats

# ── PGF asset optimization ───────────────────────────────────────────────────
# PGF exports may emit companion rasters (typically <name>-img0.png colorbars).
# When many figures share identical rasters, deduplicating to a shared store
# substantially reduces repository size and LaTeX cache churn.
PGF_OPTIMIZE_ASSETS: bool = True
PGF_DEDUP_COMPANION_IMAGES: bool = True
# Reserved for future image recompression/transcoding pipeline.
PGF_RECOMPRESS_COMPANION_IMAGES: bool = False

# ── Matplotlib style defaults ────────────────────────────────────────────────
# CTUthesis textwidth: 210mm − 35mm (left) − 25mm (right) = 150mm
FIGURE_WIDTH_CM: float = 15.0
FIGURE_HEIGHT_CM: float = 9.0

# Standard height for single-axis figures (timeline, bar, scatter).
# Sized so two such figures + two 2-line captions fit on one A4 page.
# Derivation: textheight=247mm, 2×caption≈26mm, spacing≈15mm → 206mm/2 ≈ 103mm.
FIGURE_HEIGHT_STANDARD_CM: float = 10.5

# PGF export target width. Figures are normalized to this width at save time
# so LaTeX can include them without any resize/fitting step.
PGF_TARGET_WIDTH_CM: float = FIGURE_WIDTH_CM

# Typography source of truth from LaTeX (CTUthesis 12pt base):
#   \normalsize  = 12pt
#   \small       = 11pt
#   \footnotesize= 10pt
LATEX_NORMAL_SIZE_PT: int = 12
LATEX_SMALL_SIZE_PT: int = 11
LATEX_FOOTNOTE_SIZE_PT: int = 10

# Legacy compatibility constant used by older analysis scripts.
# Keep at 10 so existing hardcoded +1/+2 adjustments don't explode in size.
FONT_SIZE: int = LATEX_FOOTNOTE_SIZE_PT

# Typography policy used across plotting helpers.
# - Figure titles: same as normal figure text.
# - Figure labels/ticks: one point smaller than normal figure text.
# - LaTeX tables: one point smaller via \small.
FIGURE_TEXT_SIZE: int = LATEX_NORMAL_SIZE_PT
FIGURE_TITLE_SIZE: int = FIGURE_TEXT_SIZE
FIGURE_LABEL_SIZE: int = LATEX_SMALL_SIZE_PT

# Dense combined plots can use a compact profile without going below 10pt.
FIGURE_COMPACT_TEXT_SIZE: int = LATEX_FOOTNOTE_SIZE_PT
FIGURE_COMPACT_LABEL_SIZE: int = LATEX_FOOTNOTE_SIZE_PT
# Country labels on Europe choropleth maps — compact but never below 10 pt floor.
MAP_COUNTRY_LABEL_SIZE: int = LATEX_FOOTNOTE_SIZE_PT
TABLE_FONT_SIZE_LATEX: str = "small"

# ── Poster mode ──────────────────────────────────────────────────────────────
# Analogous to \DPPosterFigureLabelSize / \DPPosterWorkBaseSize in poster.tex.
# Set DP_POSTER_RUN=1 when regenerating figures for the A1 poster so that
# scripts produce _poster.pgf variants with one-step-smaller labels.  The
# main thesis figures (*.pgf) are unaffected.
import os as _os
IS_POSTER_RUN: bool = _os.environ.get("DP_POSTER_RUN", "0") == "1"
# Poster-specific sizes — one step smaller than thesis equivalents.
POSTER_FIGURE_LABEL_SIZE: int = FIGURE_LABEL_SIZE - 1      # 10pt (footnotesize)
POSTER_FIGURE_COMPACT_LABEL_SIZE: int = FIGURE_COMPACT_LABEL_SIZE - 1  # 9pt


def poster_stem(stem: str) -> str:
    """Return ``{stem}_poster`` when DP_POSTER_RUN=1, otherwise *stem* unchanged.

    Usage in analysis scripts::

        savefig_pgf(fig, poster_stem("my_figure"), strings=STRINGS)
        if not IS_POSTER_RUN:
            save_figure_tex_pgf("my_figure", ...)  # thesis-only wrapper
    """
    return f"{stem}_poster" if IS_POSTER_RUN else stem

# Colour palette – qualitative, colour-blind safe (based on Wong 2011).
# Excluded: yellow (#F0E442, #E69F00) – near-invisible on white.
PALETTE = [
    "#0072B2",  # deep blue
    "#009E73",  # teal / green
    "#CC79A7",  # rose / pink
    "#56B4E9",  # sky blue
    "#D55E00",  # vermillion
    "#7B2D8B",  # purple
    "#000000",  # black
]

# Fixed high-visibility colours for the six key country codes.
# Order: CZ, DE, AT, DK, PL, SK
COUNTRY_COLORS: dict[str, str] = {
    "CZ": "#D62728",  # full red
    "DE": "#17376E",  # dark navy blue
    "AT": "#2CA02C",  # full green
    "DK": "#FF7F0E",  # orange
    "PL": "#4393C3",  # medium blue
    "SK": "#C71585",  # dark pink / magenta
}

# Eurostat aggregate codes used for EU-average computations
EU_AVERAGE_CODE: str = "EU27_2020"  # geo code for EU-27 aggregate in SDMX data

# Countries in the European geographic area that have NO regular data in
# Eurostat SDMX datasets (as of 2025).  They appear as missing-colour on maps.
# Source: manual verification against ilc_peps01n, earn_nt_taxwedge, nama_10_pc.
GEO_NOT_IN_EUROSTAT: frozenset[str] = frozenset([
    "UA",  # Ukraine – EU candidate; Eurostat does not publish regular SDMX data
    "BY",  # Belarus – not an EU member or candidate
    "RU",  # Russia  – not an EU member or candidate
    "MD",  # Moldova – EU candidate; limited Eurostat coverage
])

# Diverging colourmap for choropleth maps
CMAP_DIVERGING = "RdYlBu_r"
# Sequential colourmap for single-variable maps
CMAP_SEQUENTIAL = "RdYlGn_r"

# Choropleth print mode: optionally blend all map colormaps toward white.
# This is applied centrally in statout.map_europe / statout.map_cz and affects
# both default and explicitly-set cmap values used by analysis scripts.
CHOROPLETH_BLEND_WITH_WHITE: bool = False
# White blend in percent (0 = no change, 100 = fully white).
CHOROPLETH_WHITE_BLEND_PCT: float = 30.0
