r"""
Czech collective-agreement wage growth vs. actual wage growth -- CZ and peers.

Data sources
------------
Czech Republic (negotiated):
    MPSV IPP (Informace o pracovních podmínkách) -- annual Excel workbooks
    downloaded from ``https://www.kolektivnismlouvy.cz``.
    The ``odmenovani`` workbook sheet A15a "Mzdový vývoj" Celkem row col 11
    gives the average percentage increase among KS that used the
    "zvýšením v %" method.

All EU27 countries (actual):
    Eurostat Labour Cost Index -- nominal, annual (``lc_lci_r2_a``).
    ``B-S`` = total business economy; ``D1_D4_MD5`` = total labour costs;
    ``I20`` = 2020 = 100. Annual growth derived from index ratio.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from config import COUNTRY_COLORS, FONT_SIZE, PALETTE
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    add_pgf_tooltips,
    apply_style_pgf,
    cm2in,
    save_figure_tex_pgf,
    savefig_pgf,
)
from statout.timeline import EU27 as _EU27
from analyses._shared_data import extract_ipp_negotiated

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

# ── Parameters ────────────────────────────────────────────────────────────────
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
# Eurostat uses "EL" for Greece, not "GR" — translate when forming the request.
GEO_ALL = "+".join(sorted({("EL" if g == "GR" else g) for g in _EU27}))
START_YEAR = 2007
END_YEAR_IPP = 2025

NUDGE_LABELS = [(geo, rf"\acs{{geo-{geo}}}") for geo in COUNTRIES] + [
    ("Sjednany", r"sjednaný"),
]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. IPP negotiated wage increases ──────────────────────────────────────────
print(f"Loading IPP odmenovani for {START_YEAR}--{END_YEAR_IPP} …")
ipp_dict = extract_ipp_negotiated(START_YEAR, END_YEAR_IPP)
for yr, val in sorted(ipp_dict.items()):
    print(f"  IPP {yr}: {val:.1f} %")
ipp_series = pd.Series(ipp_dict).sort_index() if ipp_dict else pd.Series(dtype=float)

# ── 2. Eurostat LCI (all EU27) ────────────────────────────────────────────────
print("Downloading Eurostat labour cost index …")
path_lci = fetch_eurostat(
    "lc_lci_r2_a",
    f"A.I20.B-S.D1_D4_MD5.{GEO_ALL}",
    start_period=START_YEAR - 1,
)
ds_lci = Dataset.from_sdmx_csv(
    path_lci,
    name="Index nákladů práce",
    unit="2020=100",
    source_url="Eurostat/lc_lci_r2_a",
)
print(f"LCI countries: {len(ds_lci.countries)}  |  years: {ds_lci.years[0]}--{ds_lci.years[-1]}")
LAST_YEAR = max(2025, int(ds_lci.years[-1]),
                int(ipp_series.index.max()) if not ipp_series.empty else 0)


def _yoy(ds: Dataset, geo: str) -> pd.Series:
    s = ds.for_country(geo).set_index(ds.time_col)[ds.value_col].sort_index()
    return (s.pct_change() * 100).dropna()


growth: dict[str, pd.Series] = {}
for geo in sorted(_EU27):
    s = _yoy(ds_lci, geo)
    s = s[s.index >= START_YEAR]
    if not s.empty:
        growth[geo] = s

# ── 3. Build figure ───────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=cm2in(15, 9))

# EU27 grey cloud
for geo, s in growth.items():
    if geo in COUNTRIES:
        continue
    ax.plot(s.index, s.values, color="#C8C8C8", linewidth=0.5, alpha=0.55, zorder=1)

# Highlighted countries: solid (= actual)
for geo in COUNTRIES:
    if geo not in growth:
        continue
    s = growth[geo]
    color = COUNTRY_COLORS.get(geo, PALETTE[0])
    lw = 2.0 if geo == "CZ" else 1.4
    ax.plot(s.index, s.values, color=color, linewidth=lw, linestyle="-", zorder=3)
    ax.annotate(
        rf"\acs{{geo-{geo}}}",
        xy=(s.index[-1], s.iloc[-1]),
        xytext=(4, 0),
        textcoords="offset points",
        fontsize=FONT_SIZE,
        va="center",
        color=color,
    )

# CZ negotiated (IPP): dashed
if not ipp_series.empty:
    ax.plot(
        ipp_series.index, ipp_series.values,
        color=COUNTRY_COLORS["CZ"],
        linewidth=2.0,
        linestyle="--",
        zorder=4,
    )
    ax.annotate(
        r"sjednaný",
        xy=(ipp_series.index[-1], ipp_series.iloc[-1]),
        xytext=(4, 0),
        textcoords="offset points",
        fontsize=FONT_SIZE,
        va="center",
        color=COUNTRY_COLORS["CZ"],
    )

# Two-entry style legend
style_handles = [
    mlines.Line2D([], [], color="#444444", linewidth=1.4, linestyle="-",
                  label=r"skutečný (\acs{LCI})"),
    mlines.Line2D([], [], color="#444444", linewidth=1.4, linestyle="--",
                  label=r"sjednaný (\acs{IPP})"),
]
ax.legend(handles=style_handles, frameon=False, fontsize=FONT_SIZE,
          loc="upper left", borderaxespad=0.3)

ax.axhline(0, color="grey", linewidth=0.6, linestyle=":", alpha=0.6, zorder=2)
ax.set_xlabel("rok")
ax.set_ylabel(r"meziroční nárůst [\%]")
ax.set_xlim(START_YEAR, LAST_YEAR)
ax.set_ylim(0, 14)
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.yaxis.set_major_locator(ticker.MultipleLocator(2))
ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:.0f}\\,\\%"))
ax.set_axisbelow(True)
ax.grid(which="major", axis="y", linewidth=0.5, alpha=0.28)
ax.grid(which="minor", axis="y", linewidth=0.4, alpha=0.14)

STRINGS = {"title": r"Sjednaný vs.~skutečný mzdový nárůst v~\acs{geo-CZ}"}
ax.set_title(STRINGS["title"])

# ── 4. PGF tooltips (highlighted countries + IPP only — cloud lines stay clean) ──
_pivot_fg = (
    ds_lci.df[ds_lci.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
    .pct_change() * 100
)
add_pgf_tooltips(ax, _pivot_fg, fmt="{:.1f}")
if not ipp_series.empty:
    add_pgf_tooltips(ax, pd.DataFrame({"CZ": ipp_series}), fmt="{:.1f}")

# ── 5. Save ───────────────────────────────────────────────────────────────────
year_range = f"{START_YEAR}--{LAST_YEAR}"
savefig_pgf(fig, "stav_ipp_mzdy", strings=STRINGS, nudge_labels=NUDGE_LABELS)
save_figure_tex_pgf(
    "stav_ipp_mzdy",
    caption=f"Mzdový nárůst sjednaný v~\\acs{{KS}} a~skutečný, \\acs{{EU}} srovnání, {year_range}.",
    label="fig:stav_ipp_mzdy",
    resizebox_width=r"\linewidth",
    cite_keys=["mpsv_ipp", "eurostat_lci"],
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)
print("Done.")
