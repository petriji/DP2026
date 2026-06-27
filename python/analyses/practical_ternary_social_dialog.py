r"""
Practical ternary social-dialog comparison (AT, CZ, DK, DE, PL, SK) with EU27 cloud.

Shows the estimated power balance between Employees (A, top vertex),
Employers (B, bottom-left) and State (C, bottom-right) as a point on a
ternary simplex with an RGB heatmap background.  Six countries (AT, CZ,
DK, DE, PL, SK) are highlighted in the project palette; the remaining
EU27 are shown as a grey background cloud (toggle with SHOW_EU27_CLOUD).
Hover tooltips show A/B/C shares in PDF viewers that support pdfcomment
annotations (Adobe Acrobat, Foxit).

Data rows: (Employees %, Employers %, State %) — integers that sum to 100.
Coordinates are computed by ``_ternary_calc.calculate_eu27_axis_scores()`` from
Eurostat/OECD datasets.  Three weighted composite axes (A = Employees, B = Employers,
C = State) are normalised min-max over EU27 and then closed to a ternary simplex.
Filter: Highlights AT, CZ, DE, DK, PL, SK; EU27 background cloud.

Output
------
    python/figures/practical_ternary_social_dialog.pgf

Run
---
    python analyses/practical_ternary_social_dialog.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyses._ternary_calc import calculate_eu27_axis_scores
from config import COUNTRY_COLORS, FIGURES_DIR, IS_POSTER_RUN, poster_stem
from statout.map_europe import choropleth
from stattool.dataset import Dataset
from statout.ternary import ternary_diagram
from stattool.style import (
    cm2in,
    apply_geo_labels_pgf,
    apply_style_pgf,
    load_angle_nudges_from_figure_tex,
    savefig,
    savefig_pgf,
    save_figure_tex_pgf,
)

# ── Toggle ───────────────────────────────────────────────────────────────────
SHOW_EU27_CLOUD: bool = True   # set False to hide grey EU27 background dots
SHOW_COLOR_BACKGROUND: bool = True   # set False to disable ternary RGB heatmap
SHOW_EQUILIBRIUM_DISTANCE_GRID: bool = True  # set False to hide concentric equilibrium circles
# Set to False only for debugging. Hardcoded coordinates are kept below
# as comments for reference and are no longer used at runtime.
RECALCULATE_COORDS: bool = True
ENABLE_PDF_EXPORT: bool = False  # keep PDF capability, disabled in normal pipeline runs

# ── Featured countries (colour, foreground) ──────────────────────────────────
# (Employees %, Employers %, State %) — integers sum to 100.
# Vertex A (top) = Employees (Zaměstnanci)
# Vertex B (bottom-left) = Employers (Firmy)
# Vertex C (bottom-right) = State (Vláda)
#
# Reference coordinates from earlier manual calibration (ideal target values).
# These values are intentionally commented out and kept only for documentation.
_FEATURED_GEOS = ["CZ", "AT", "DE", "DK", "PL", "SK"]
# _REFERENCE_FEATURED: dict[str, tuple[int, int, int]] = {
#     "CZ": (16, 47, 37),
#     "DK": (33, 33, 34),
#     "DE": (41, 30, 29),
#     "SK": (11, 57, 32),
#     "PL": (16, 56, 28),
#     "AT": (35, 38, 27),
# }
# _REFERENCE_EU27_CLOUD: dict[str, tuple[int, int, int]] = {
#     "AT": (35, 38, 27),
#     "BE": (28, 32, 40),
#     "BG": (12, 60, 28),
#     "CY": (18, 48, 34),
#     "CZ": (16, 47, 37),
#     "DE": (41, 30, 29),
#     "DK": (33, 33, 34),
#     "EE": (20, 52, 28),
#     "ES": (22, 42, 36),
#     "FI": (36, 30, 34),
#     "FR": (20, 32, 48),
#     "GR": (15, 45, 40),
#     "HR": (14, 52, 34),
#     "HU": (10, 58, 32),
#     "IE": (28, 42, 30),
#     "IT": (26, 38, 36),
#     "LT": (16, 54, 30),
#     "LU": (30, 34, 36),
#     "LV": (14, 56, 30),
#     "MT": (20, 46, 34),
#     "NL": (32, 36, 32),
#     "PL": (16, 56, 28),
#     "PT": (22, 44, 34),
#     "RO": (10, 62, 28),
#     "SE": (32, 34, 34),
#     "SI": (24, 46, 30),
#     "SK": (11, 57, 32),
# }

# Module-level dicts — populated in main() from model-derived coordinates.
COUNTRY_SHARES: dict[str, tuple[int, int, int]] = {}
COUNTRY_POINT_COLORS: dict[str, str] = {k: COUNTRY_COLORS[k] for k in _FEATURED_GEOS}
EU27_CLOUD: dict[str, tuple[int, int, int]] = {}

PLOT_STEM = "practical_ternary_social_dialog"
STRENGTH_STEM = "practical_ternary_strength_map"

_VERTEX_LABELS = (r"Zam\v{e}stnanci", "Firmy", r"Vl\'ada")
_TOOLTIP_VERTEX_LABELS = ("Zaměstnanci", "Firmy", "Vláda")
_TITLE = "Tripartitní rovnováha v~EU"
_LABEL_ANGLE_NUDGES: dict[str, float] = {
    "CZ": 25.0,
    "DK": 40.0,
    "DE": 22.0,
    "SK": 0.0,
    "PL": 8.0,
    "AT": 160.0,
}
_LABEL_Y_NUDGES = [(geo, geo) for geo in _FEATURED_GEOS]

# Match CTUthesis text width (~15 cm) so wrapper resizebox{\linewidth}
# does not downscale typography (title should remain effectively 12 pt).
_TERNARY_FIGSIZE = cm2in(15.0, 14.1)


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    apply_style_pgf()

    # ── Coordinate calculation ────────────────────────────────────────────────
    global COUNTRY_SHARES, EU27_CLOUD  # noqa: PLW0603
    if RECALCULATE_COORDS:
        print("Computing EU27 ternary coordinates from Eurostat data…")
        raw = calculate_eu27_axis_scores()
        _all: dict[str, tuple[int, int, int]] = {}
        for geo, row in raw.iterrows():
            a = float(row["A_raw"])
            b = float(row["B_raw"])
            c = float(row["C_raw"])
            total = a + b + c
            a_pct = int(round(a / total * 100))
            b_pct = int(round(b / total * 100))
            c_pct = 100 - a_pct - b_pct
            _all[geo] = (a_pct, b_pct, c_pct)

        COUNTRY_SHARES = {geo: _all[geo] for geo in _FEATURED_GEOS if geo in _all}
        EU27_CLOUD = dict(_all)
        print("Coordinates computed.")
    else:
        raise RuntimeError(
            "RECALCULATE_COORDS=False is disabled: hardcoded coordinates are "
            "kept only as commented reference values in this file."
        )

    cloud = (
        {k: v for k, v in EU27_CLOUD.items() if k not in COUNTRY_SHARES}
        if SHOW_EU27_CLOUD
        else None
    )
    bg_alpha = 0.20 if SHOW_COLOR_BACKGROUND else 0.0

    strings_main = {
        "title": _TITLE,
        "vertex_a": r"Zam\v{e}stnanci",
        "vertex_b": "Firmy",
        "vertex_c": r"Vl\'ada",
        "caption": "Praktická tripartitní rovnováha v~\\acs{EU} na základě modelu preferencí aktérů sociálního dialogu (odpovídající zaměření na zaměstnance, firmy a stát).",
    }
    angle_nudges = load_angle_nudges_from_figure_tex(PLOT_STEM, _LABEL_ANGLE_NUDGES)

    # Primary thesis output: corners-on PGF for LaTeX.
    fig_pgf = ternary_diagram(
        data=COUNTRY_SHARES,
        colors=COUNTRY_POINT_COLORS,
        vertex_labels=_VERTEX_LABELS,
        tooltip_labels=_TOOLTIP_VERTEX_LABELS,
        title=_TITLE,
        show_corner_labels=True,
        label_angle_nudges=angle_nudges,
        figsize=_TERNARY_FIGSIZE,
        bg_alpha=bg_alpha,
        background_data=cloud,
        show_equilibrium_circles=SHOW_EQUILIBRIUM_DISTANCE_GRID,
    )
    pgf_path = savefig_pgf(
        fig_pgf,
        poster_stem(PLOT_STEM),
        out_dir=FIGURES_DIR,
        strings=strings_main,
        nudge_labels=_LABEL_Y_NUDGES,
    )

    if ENABLE_PDF_EXPORT:
        fig_pdf = ternary_diagram(
            data=COUNTRY_SHARES,
            colors=COUNTRY_POINT_COLORS,
            vertex_labels=_VERTEX_LABELS,
            tooltip_labels=_TOOLTIP_VERTEX_LABELS,
            title=_TITLE,
            show_corner_labels=True,
            label_angle_nudges=angle_nudges,
            figsize=_TERNARY_FIGSIZE,
            bg_alpha=bg_alpha,
            background_data=cloud,
            show_equilibrium_circles=SHOW_EQUILIBRIUM_DISTANCE_GRID,
        )
        savefig(fig_pdf, PLOT_STEM, fmt="pdf", out_dir=FIGURES_DIR)
    
    save_figure_tex_pgf(
        PLOT_STEM,
        caption=strings_main["caption"],
        cite_keys=[
            "eurostat_jvs_a_r21",
            "oecd_cts_cit",
            "eurostat_lc_lci_lev",
        ],
        label="fig:practical_ternary_social_dialog",
        resizebox_width=r"\linewidth",
        strings=strings_main,
        nudge_labels=_LABEL_Y_NUDGES,
        angle_labels=_LABEL_ANGLE_NUDGES,
    )
    print("Output files:")
    print(f"  - {pgf_path}")

    # Complementary visualisation: average strength (A+B+C)/3.
    strength_df = pd.DataFrame(
        {
            "geo": list(raw.index),
            "time": 2026,
            "value": raw["mean_raw"].tolist(),
        }
    )
    ds_strength = Dataset(
        strength_df,
        name=r"Souhrnné skóre sociálních partner\r{u}",
        unit="1",
        source_url="Modelový výpočet z os A/B/C",
    )

    values = ds_strength.for_year(ds_strength.latest_year).set_index("geo")["value"].to_dict()
    strings_strength = {
        "title": r"Souhrnné skóre sociálních partner\r{u}",
        "colorbar_label": "skóre [1]",
    }

    _vmin = min(values.values())
    _vmax = max(values.values())
    fig_strength = choropleth(
        ds_strength,
        year=ds_strength.latest_year,
        title=strings_strength["title"],
        colorbar_label=strings_strength["colorbar_label"],
        cmap="RdYlGn",
        vmin=_vmin,
        vmax=_vmax,
        label_countries=True,
        highlight_colorbar=_FEATURED_GEOS,
    )
    apply_geo_labels_pgf(fig_strength.axes[0], halo=True, values=values, tooltip_fmt="{:.1f}")
    strength_pgf = savefig_pgf(
        fig_strength,
        STRENGTH_STEM,
        out_dir=FIGURES_DIR,
        strings=strings_strength,
    )

    if ENABLE_PDF_EXPORT:
        fig_strength_pdf = choropleth(
            ds_strength,
            year=ds_strength.latest_year,
            title=strings_strength["title"],
            colorbar_label=strings_strength["colorbar_label"],
            cmap="RdYlGn",
            vmin=_vmin,
            vmax=_vmax,
            label_countries=True,
            highlight_colorbar=_FEATURED_GEOS,
        )
        apply_geo_labels_pgf(fig_strength_pdf.axes[0], halo=True, values=values, tooltip_fmt="{:.1f}")
        savefig(fig_strength_pdf, STRENGTH_STEM, fmt="pdf", out_dir=FIGURES_DIR)

    save_figure_tex_pgf(
        STRENGTH_STEM,
        caption=f"Průměr modelových os (A+B+C)/3 (souhrnné skóre sociálních partnerů), \\acs{{EU}}",
        cite_keys=[
            "eurostat_jvs_a_r21",
            "oecd_cts_cit",
            "eurostat_lc_lci_lev",
        ],
        label="fig:practical_ternary_strength_map",
        resizebox_width=r"\linewidth",
        strings=strings_strength,
    )

    print(f"  - {strength_pgf}")


if __name__ == "__main__":
    main()

