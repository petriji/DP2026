r"""
Labour Market Policy (LMP) expenditure as % of GDP -- CZ, AT, DE, DK, PL, SK.

Key message for the thesis: DK spends ~2 % of GDP on active labour-market
policy; CZ spends ~0.3 %.  The "flexicurity" triangle only works with
adequate income-support and re-skilling investment.

Data source: Eurostat, ``lmp_expsumm``
  LMP summary expenditure by type of action.
  Dimensions: freq · exptype · unit · geo
  Filter used: freq=A, programme=LMP_20T70 (active, cat. 2--7), unit=PC_GDP.

Output
------
  pics/eu_apz_vydaje.pdf
  latex/texparts/eu_apz_vydaje.tex  ← \input{} this in main.tex

Run
---
    python analyses/eu_apz_vydaje.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR, FIGURE_TEXT_SIZE, FIGURE_LABEL_SIZE, FIGURE_COMPACT_LABEL_SIZE
from stattool.style import apply_style_pgf, savefig_pgf, save_figure_tex_pgf, add_pgf_tooltips
from statout.timeline import timeline, EU27 as _EU27
from analyses._shared_data import load_lmp_active

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2004
HIGHLIGHT = ["CZ", "DK"]

# ── TUNING KNOBS (edit + re-run script to apply) ─────────────────────────────
# Axis limits: set to None for matplotlib auto-fit.
XLIM:  tuple[float, float] | None = None  # auto-extends to max(years[-1], 2025)
YLIM:  tuple[float, float] | None = (0, 2.0)
# Second variant (cropped to 2004--latest, narrower y-range)
XLIM2: tuple[float, float] | None = None
YLIM2: tuple[float, float] | None = (0, 2.0)

# Per-label nudges (matplotlib offset_points). End-of-line country labels.
# Final tweaks can also be done LaTeX-side via
#   \renewcommand\NudgeEuApzVydajeCZ{-3pt}
# in latex/texparts/figures/eu_apz_vydaje.tex (no Python re-run needed).
LABEL_OFFSETS: dict[str, tuple[float, float]] = {"SK": (4, 5), "PL": (4, -5)}

# Per-label y-nudge knobs exposed to LaTeX — auto-derived from COUNTRIES.
# Each entry creates a \NudgeEuApzVydaje<ID> macro overridable via \renewcommand.
NUDGE_LABELS = [
    (geo, rf"\acs{{geo-{geo}}}") for geo in COUNTRIES
] + [("COVID", "COVID-19")]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Load data ──────────────────────────────────────────────────────────────
ds_all = load_lmp_active(start_period=START_YEAR)

print(f"All countries: {len(ds_all.countries)}  |  Years: {ds_all.years[0]}--{ds_all.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
STRINGS = {
    "title": r"Výdaje na \acs{APZ}",
    "ylabel": r"výdaje na \acs{APZ} [\% \acs{HDP}]",
}
fig = timeline(
    ds_all,
    countries=COUNTRIES,
    title=STRINGS["title"],
    ylabel=STRINGS["ylabel"],
    highlight=HIGHLIGHT,
    annotate_last=True,
    label_offsets=LABEL_OFFSETS,
    show_eu_avg=False,
    background_eu=True,
)
if XLIM is not None:
    fig.axes[0].set_xlim(*XLIM)
else:
    fig.axes[0].set_xlim(START_YEAR, max(ds_all.years[-1], 2025))
if YLIM is not None:
    fig.axes[0].set_ylim(*YLIM)

# COVID-19 annotation: 2020 spike was caused by emergency short-time work
# schemes (Kurzarbeit/furlough), extended unemployment benefits, and wage
# subsidies. DK 'Lønkompensation' covered 75% of wages --- hence the highest spike.
_ax = fig.axes[0]
_ax.axvline(2020, color="#CC4444", linewidth=0.8, linestyle="--", alpha=0.7, zorder=2)
_ax.text(2020.2, 1.9, "COVID-19", fontsize=FIGURE_COMPACT_LABEL_SIZE,
         color="#CC4444", alpha=0.85, va="top")

# ── PGF tooltips & geo labels ─────────────────────────────────────────────────
_pivot_fg = (
    ds_all.df[ds_all.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax, _pivot_fg, fmt="{:.1f}")
_bg = sorted(set(_EU27) - set(COUNTRIES))
_pivot_fg_bg = (
    ds_all.df[ds_all.df["geo"].isin(_bg)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax, _pivot_fg_bg, fmt="{:.1f}")
for _child in _ax.get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_apz_vydaje", strings=STRINGS, nudge_labels=NUDGE_LABELS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_apz_vydaje",
    caption=f"Výdaje na \\acacc{{APZ}} (\\% \\acs{{HDP}}), vybrané země \\acs{{EU}}, 2004--2023",
    label="fig:eu_apz_vydaje",
    resizebox_width=r"\linewidth",
    cite_key="oecd_lmpexp_PC_GDP",
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)

# ── 6. Second variant: 2004--latest (cropped x-axis) ──────────────────────────
YEAR_2004 = 2004
STRINGS_2004 = {
    "title": rf"Výdaje na \acs{{APZ}} ({YEAR_2004}--{ds_all.years[-1]})",
    "ylabel": r"výdaje na \acs{APZ} [\% \acs{HDP}]",
}

fig2 = timeline(
    ds_all,
    countries=COUNTRIES,
    title=STRINGS_2004["title"],
    ylabel=STRINGS_2004["ylabel"],
    highlight=HIGHLIGHT,
    annotate_last=True,
    label_offsets=LABEL_OFFSETS,
    show_eu_avg=False,
    background_eu=True,
)
if XLIM2 is not None:
    fig2.axes[0].set_xlim(*XLIM2)
else:
    fig2.axes[0].set_xlim(YEAR_2004, max(ds_all.years[-1], 2025))
if YLIM2 is not None:
    fig2.axes[0].set_ylim(*YLIM2)

_ax2 = fig2.axes[0]
_ax2.axvline(2020, color="#CC4444", linewidth=0.8, linestyle="--", alpha=0.7, zorder=2)
_ax2.text(2020.2, 1.7, "COVID-19", fontsize=FIGURE_COMPACT_LABEL_SIZE, color="#CC4444", alpha=0.85, va="top")

# ── PGF tooltips & geo labels ─────────────────────────────────────────────────
_pivot_fg2 = (
    ds_all.df[ds_all.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax2, _pivot_fg2, fmt="{:.1f}")
_pivot_fg2_bg = (
    ds_all.df[ds_all.df["geo"].isin(_bg)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax2, _pivot_fg2_bg, fmt="{:.1f}")
for _child in _ax2.get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

savefig_pgf(fig2, "eu_apz_vydaje_2004", strings=STRINGS_2004, nudge_labels=NUDGE_LABELS)
save_figure_tex_pgf(
    "eu_apz_vydaje_2004",
    caption=(
        f"Výdaje na \\acs{{APZ}} (\\% \\acs{{HDP}}), vybrané země EU, "
        f"2004--{ds_all.years[-1]}."
    ),
    label="fig:eu_apz_vydaje_2004",
    resizebox_width=r"\linewidth",
    cite_key="oecd_lmpexp_PC_GDP",
    strings=STRINGS_2004,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
