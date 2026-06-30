r"""
Trade union density trend -- CZ, AT, DE, DK, PL, SK.

Data source: OECD AIAS ICTWSS (via OECD Stats API, dataset ``TUD``)
  Trade union density = share of wage and salary earners who are
  members of a trade union.

Output
------
  pics/stav_hustota_vyvoj.pdf
  latex/texparts/stav_hustota_vyvoj.tex  ← \input{} this in main.tex

Run
---
    python analyses/stav_hustota_vyvoj.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    add_pgf_tooltips,
)
from statout.timeline import timeline, EU27 as _EU27
from analyses._shared_data import load_union_density

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 1993   # post-transition baseline for all six countries
HIGHLIGHT = ["CZ"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Load data ──────────────────────────────────────────────────────────────
ds = load_union_density(start_period=START_YEAR)

print(f"Countries: {len(ds.countries)}  |  Years: {ds.years[0]}--{ds.years[-1]}")


def _add_tooltips_and_geo(ax, countries):
    """Attach tooltips on data points and \\acs{geo-XX} labels."""
    _pivot = (
        ds.df[ds.df["geo"].isin(countries)]
        .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
    )
    add_pgf_tooltips(ax, _pivot, fmt="{:.1f}")
    _bg = sorted(set(_EU27) - set(countries))
    _pivot_bg = (
        ds.df[ds.df["geo"].isin(_bg)]
        .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
    )
    add_pgf_tooltips(ax, _pivot_bg, fmt="{:.1f}")
    for child in ax.get_children():
        if hasattr(child, "get_text"):
            txt = child.get_text().strip()
            if txt in countries:
                child.set_text(f"\\acs{{geo-{txt}}}")


# ── 3. Timeline figure (full history, grey cloud) ─────────────────────────────
STRINGS_FULL = {
    "title": "Odborová organizovanost",
    "ylabel": r"odborová organizovanost [\% zaměstnanců]",
}

fig = timeline(
    ds,
    countries=COUNTRIES,
    title=STRINGS_FULL["title"],
    ylabel=STRINGS_FULL["ylabel"],
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=False,
    background_eu=True,
)
fig.axes[0].set_xlim(START_YEAR, 2025)
_add_tooltips_and_geo(fig.axes[0], COUNTRIES)

# ── 4. Save figure ────────────────────────────────────────────────────────────
NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]
savefig_pgf(fig, "stav_hustota_vyvoj", strings=STRINGS_FULL, nudge_labels=NUDGE_LABELS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "stav_hustota_vyvoj",
    caption=(
        f"Vývoj hustoty odborových organizací, vybrané země EU, "
        f"{START_YEAR}--{ds.years[-1]}."
    ),
    label="fig:stav_hustota_vyvoj",
    resizebox_width=r"\linewidth",
    cite_key="oecd_aias_ictwss_TUD_pct",
    strings=STRINGS_FULL,
    nudge_labels=NUDGE_LABELS,
)

# ── 6. Second variant: 2004--latest (cropped x-axis) ──────────────────────────
YEAR_2004 = 2004
STRINGS_2004 = {
    "title": f"Odborová organizovanost ({YEAR_2004}--{ds.years[-1]})",
    "ylabel": r"odborová organizovanost [\% zaměstnanců]",
}

fig2 = timeline(
    ds,
    countries=COUNTRIES,
    title=STRINGS_2004["title"],
    ylabel=STRINGS_2004["ylabel"],
    highlight=HIGHLIGHT,
    annotate_last=True,
    label_offsets={"PL": (4, -10)},
    show_eu_avg=False,
    background_eu=True,
)
fig2.axes[0].set_xlim(2004, 2025)
fig2.axes[0].set_ylim(0, 80)
_add_tooltips_and_geo(fig2.axes[0], COUNTRIES)

savefig_pgf(fig2, "stav_hustota_vyvoj_2004", strings=STRINGS_2004, nudge_labels=NUDGE_LABELS)
save_figure_tex_pgf(
    "stav_hustota_vyvoj_2004",
    caption=(
        f"Vývoj hustoty odborových organizací, vybrané země EU, "
        f"2004--{ds.years[-1]}."
    ),
    label="fig:stav_hustota_vyvoj_2004",
    resizebox_width=r"\linewidth",
    cite_key="oecd_aias_ictwss_TUD_pct",
    strings=STRINGS_2004,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
