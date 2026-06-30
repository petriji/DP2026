r"""
CB coverage timeline -- EU grey cloud + CZ, AT, DE, DK, PL, SK highlighted.

Data sources
------------
* ICTWSS v2 ``AdjCov`` column (OECD / AIAS, administrative-based adjusted
  coverage) for all EU-27 countries **except Germany**.
* OECD CBC API, ``MEASURE='ERB'`` (European Record of Bargaining survey-based
  measure) for **Germany only** --- ICTWSS AdjCov for DE is unavailable after 1990.

Note: AdjCov and ERB are methodologically distinct measures.  German values
(ERB ≈ 49 % in 2024) are not directly comparable to the AdjCov series
(CZ ≈ 31 % in 2023).  Both are shown in a single figure for structural
context; the difference for DE is acknowledged in the caption.

Output
------
  pics/python/eu_pokryti_kv_vyvoj.pdf
  pics/python/eu_pokryti_kv_vyvoj_2004.pdf
  latex/texparts/python/eu_pokryti_kv_vyvoj.tex
  latex/texparts/python/eu_pokryti_kv_vyvoj_2004.tex

Run
---
    python analyses/eu_pokryti_kv_vyvoj.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.style import apply_style_pgf, savefig_pgf, save_figure_tex_pgf, add_pgf_tooltips
from statout.timeline import timeline, EU27 as _EU27
from analyses._shared_data import load_cb_coverage

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "DK", "DE", "AT", "PL", "SK"]
HIGHLIGHT = ["CZ"]
START_YEAR = 1993   # grey cloud starts here; some EU27 countries go back to 1990

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Load CB coverage data ──────────────────────────────────────────────────
print("Loading CB coverage data …")
ds = load_cb_coverage(start_period=START_YEAR)
ds.name = "Pokrytí kolektivním vyjednáváním"
print(f"Merged: {ds.df['geo'].nunique()} countries, years {ds.years[0]}--{ds.years[-1]}")

# ── 4. Long-run figure (1993--latest, xlim up to 2025) ────────────────────────
STRINGS = {
    "title": r"Pokrytí \acs{KV}",
    "ylabel": r"pokrytí \acs{KV} [\%]",
}
fig = timeline(
    ds,
    countries=COUNTRIES,
    title=STRINGS["title"],
    ylabel=STRINGS["ylabel"],
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=False,
    background_eu=True,
)
fig.axes[0].set_xlim(START_YEAR - 2, 2025)
fig.axes[0].set_ylim(0, 105)

# ── PGF tooltips & geo labels ─────────────────────────────────────────────────
_ax1 = fig.axes[0]
_pivot_kv1 = (
    ds.df[ds.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax1, _pivot_kv1, fmt="{:.1f}")
_bg_kv = sorted(set(_EU27) - set(COUNTRIES))
_pivot_kv1_bg = (
    ds.df[ds.df["geo"].isin(_bg_kv)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax1, _pivot_kv1_bg, fmt="{:.1f}")
for _child in _ax1.get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

savefig_pgf(fig, "eu_pokryti_kv_vyvoj", strings=STRINGS)

latest_yr = ds.years[-1]
save_figure_tex_pgf(
    "eu_pokryti_kv_vyvoj",
    caption=(
        r"Vývoj pokrytí kolektivním vyjednáváním, "
        f"{START_YEAR}--{latest_yr}. "
        r"Šedé linie = ostatní země EU\,27. "
        r"CZ, DK, AT, PL: míra upraveného pokrytí \textit{AdjCov} "
        r"(OECD / AIAS ICTWSS); DE a SK: průzkumová míra ERB (Evropský přehled KV, "
        r"ERB \(\neq\) AdjCov). Chybějící hodnoty = mezery v datech."
    ),
    label="fig:eu_pokryti_kv_vyvoj",
    resizebox_width=r"\linewidth",
    cite_key="oecd_aias_ictwss_CBC_ERB_pct",
    strings=STRINGS,
)

# ── 5. Cropped figure (2004--latest, xlim up to 2025) ───────────────────────
YEAR_START2 = 2004

STRINGS_2004 = {
    "title": rf"Pokrytí \acs{{KV}} ({YEAR_START2}--{latest_yr})",
    "ylabel": r"pokrytí \acs{KV} [\%]",
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
fig2.axes[0].set_xlim(YEAR_START2 - 2, 2025)
fig2.axes[0].set_ylim(0, 105)

# ── PGF tooltips & geo labels ─────────────────────────────────────────────────
_ax2 = fig2.axes[0]
_pivot_kv2 = (
    ds.df[ds.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax2, _pivot_kv2, fmt="{:.1f}")
_pivot_kv2_bg = (
    ds.df[ds.df["geo"].isin(_bg_kv)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax2, _pivot_kv2_bg, fmt="{:.1f}")
for _child in _ax2.get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

savefig_pgf(fig2, "eu_pokryti_kv_vyvoj_2004", strings=STRINGS_2004)

save_figure_tex_pgf(
    "eu_pokryti_kv_vyvoj_2004",
    caption=(
        r"Vývoj pokrytí kolektivním vyjednáváním (podíl zaměstnanců "
        r"pokrytých kolektivní smlouvou, \%), "
        f"{YEAR_START2}--{latest_yr}. "
        r"Šedé linie = ostatní země EU\,27. "
        r"CZ, DK, AT, PL: míra \textit{AdjCov} "
        r"(OECD / AIAS ICTWSS); DE a SK: průzkumová míra ERB "
        r"(ERB \(\neq\) AdjCov, viz text). Chybějící hodnoty = mezery v datech."
    ),
    label="fig:eu_pokryti_kv_vyvoj_2004",
    resizebox_width=r"\linewidth",
    cite_key="oecd_aias_ictwss_CBC_ERB_pct",
    strings={},
)

print("Done.")
