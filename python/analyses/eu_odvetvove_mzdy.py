r"""
Hourly wages by NACE sector in PPS -- grouped bar chart, deviation from EU27,
and per-sector choropleth maps for all EU27 countries.

Compares gross hourly wages (adjusted for purchasing power parity) across
key economic sectors: C (manufacturing), G (wholesale/retail), J (ICT),
K (financial services).

Data sources:
  Labour costs per hour (EUR): Eurostat ``lc_lci_lev`` (D1_D4_MD5 total, fallback D1)
  Price Level Index (GDP):     Eurostat ``prc_ppp_ind`` (PLI_EU27_2020.GDP)

Output
------
  pics/python/eu_odvetvove_mzdy_bar.pdf
  pics/python/eu_odvetvove_mzdy_odchylka.pdf
  pics/python/sector_wages_map_{C,G,J,K}.pdf
  latex/texparts/python/eu_odvetvove_mzdy_bar.tex
  latex/texparts/python/eu_odvetvove_mzdy_odchylka.tex
  latex/texparts/python/sector_wages_map_{C,G,J,K}.tex

Run
---
    python analyses/sector_wages_net_pps.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from config import (
    CHOROPLETH_BLEND_WITH_WHITE,
    CHOROPLETH_WHITE_BLEND_PCT,
    COUNTRY_COLORS,
    FIGURE_COMPACT_LABEL_SIZE,
    FIGURE_COMPACT_TEXT_SIZE,
    FIGURE_LABEL_SIZE,
    MAP_COUNTRY_LABEL_SIZE,
    LATEX_PICS_DIR,
)
from stattool.fetch import fetch_eurostat
from stattool.data_quality import warn_fallback, warn_non_target_year
from stattool.dataset import Dataset
from stattool.style import (
    cm2in,
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
COUNTRIES_EU = COUNTRIES + ["EU27_2020"]
GEO_6 = "+".join(COUNTRIES)
GEO_WITH_EU = GEO_6 + "+EU27_2020"
SECTORS = {"C": "Výroba", "G": "Obchod", "J": "ICT", "K": "Finance"}
DISPLAY_YEAR = 2024   # latest available full year

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download sector wages (EUR/h) -- 6 countries + EU27 ────────────────────
# lc_lci_lev: freq.unit.lcstruct.nace_r2.geo
# D1_D4_MD5 = total labour costs (wages + employer contributions − direct subsidies)
# D11 (wages only) is NOT used -- D1_D4_MD5 is available for all sectors/countries.
sector_filter = "+".join(SECTORS.keys())

path_lc = fetch_eurostat(
    "lc_lci_lev",
    f"A.EUR.D1_D4_MD5.{sector_filter}.{GEO_WITH_EU}",
    start_period=DISPLAY_YEAR,
)
path_lc_all = fetch_eurostat(
    "lc_lci_lev",
    f"A.EUR.D1_D4_MD5.{sector_filter}.",   # trailing dot = all geo
    start_period=DISPLAY_YEAR,
)

raw_lc = pd.read_csv(path_lc)
raw_lc = raw_lc[["geo", "nace_r2", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
ref_year = raw_lc["TIME_PERIOD"].max()
lc = raw_lc[raw_lc["TIME_PERIOD"] == ref_year].pivot_table(
    index="geo", columns="nace_r2", values="OBS_VALUE", aggfunc="first"
)
print(f"Sector wages year: {ref_year}  [D1_D4_MD5]")
warn_non_target_year(source="Eurostat lc_lci_lev", year=int(ref_year), context="Sector wages snapshot")

raw_lc_all = pd.read_csv(path_lc_all)
raw_lc_all = raw_lc_all[["geo", "nace_r2", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
lc_all = raw_lc_all[raw_lc_all["TIME_PERIOD"] == ref_year].pivot_table(
    index="geo", columns="nace_r2", values="OBS_VALUE", aggfunc="first"
)

# ── 2. Download PLI for PPS conversion ────────────────────────────────────────
# prc_ppp_ind: freq.na_item.ppp_cat.geo
# PLI_EU27_2020.GDP = price level index (EU27=100)
# EU27_2020 has PLI=100 by definition (not in the dataset)
path_pli = fetch_eurostat(
    "prc_ppp_ind",
    "A.PLI_EU27_2020.GDP.",   # trailing dot = all geo (needed for choropleth)
    start_period=DISPLAY_YEAR,
)

raw_pli = pd.read_csv(path_pli)
raw_pli = raw_pli[["geo", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
pli_year = raw_pli["TIME_PERIOD"].max()
pli = raw_pli[raw_pli["TIME_PERIOD"] == pli_year].set_index("geo")["OBS_VALUE"]
pli["EU27_2020"] = 100.0   # EU27 PLI = 100 by definition
print(f"PLI year: {pli_year}")
print("PLI:", pli[COUNTRIES_EU].to_dict())
warn_non_target_year(source="Eurostat prc_ppp_ind", year=int(pli_year), context="PLI snapshot for PPS conversion")

# ── 3. Convert EUR/h → PPS/h ──────────────────────────────────────────────────
# PPS_wage = EUR_wage / (PLI / 100)
def _to_pps(df_eur: pd.DataFrame) -> pd.DataFrame:
    """Convert EUR/h wage table to PPS/h using PLI."""
    df = df_eur.copy()
    for country in df.index:
        if country in pli.index:
            df.loc[country] = df_eur.loc[country] / (pli[country] / 100)
    return df

lc_pps = _to_pps(lc)
lc_pps_all = _to_pps(lc_all)

# Filter to our 6 countries (EU27_2020 kept in lc_pps for reference)
lc_6 = lc_pps.loc[[c for c in COUNTRIES if c in lc_pps.index]]

# EU27 fallback: if EU27_2020 row is missing or has NaN for J/K,
# compute cross-country mean from lc_pps_all as the EU27 benchmark
_EU27_GEO = "EU27_2020"
if _EU27_GEO not in lc_pps.index:
    lc_pps.loc[_EU27_GEO] = float("nan")
_fallback_sectors: list[str] = []
for s in SECTORS:
    if pd.isna(lc_pps.loc[_EU27_GEO, s]) if s in lc_pps.columns else True:
        if s in lc_pps_all.columns:
            fallback_eu = lc_pps_all[s].dropna().mean()
            lc_pps.loc[_EU27_GEO, s] = fallback_eu
            _fallback_sectors.append(s)
            print(f"  EU27 fallback mean used for sector {s}: {fallback_eu:.2f} PPS/h")
if _fallback_sectors:
    warn_fallback(
        f"EU27 sector benchmark missing for {', '.join(_fallback_sectors)}; cross-country mean used",
        source="Eurostat lc_lci_lev + prc_ppp_ind",
        year=int(ref_year),
    )

# ── 3b. EU27=100 index (needed for deviation chart only) ────────────────────────
_eu27_sector = lc_pps.loc["EU27_2020", list(SECTORS.keys())]
lc_idx_6 = lc_6.div(_eu27_sector) * 100   # 6 countries, EU27=100 per sector
print("EU27 reference values (PPS/h):", _eu27_sector.to_dict())

# ── 4. Figure 1: Grouped bar chart by sector ──────────────────────────────────
sector_codes = list(SECTORS.keys())
sector_labels = [SECTORS[s] for s in sector_codes]
x = np.arange(len(sector_codes))
n = len(COUNTRIES)
bar_w = 0.12
offsets = np.linspace(-(n - 1) / 2, (n - 1) / 2, n) * bar_w

fig1, ax1 = plt.subplots(figsize=cm2in(16, 10))

for i, country in enumerate(COUNTRIES):
    if country not in lc_6.index:
        continue
    vals = [lc_6.loc[country, s] for s in sector_codes]
    ax1.bar(x + offsets[i], vals, bar_w * 0.9,
            color=COUNTRY_COLORS.get(country, "#999999"),
            label=country, zorder=3)

# EU27 reference: solid line spanning exactly from left edge of first bar
# to right edge of last bar in each sector cluster, with end caps (|)
eu27_pps = [_eu27_sector[s] for s in sector_codes]
half_group = bar_w * 0.9 / 2          # half-width of a single bar
left_edge  = offsets[0]  - half_group  # leftmost bar left edge (relative to x)
right_edge = offsets[-1] + half_group  # rightmost bar right edge (relative to x)

for xi, eu_val in zip(x, eu27_pps):
    ax1.hlines(eu_val, xi + left_edge, xi + right_edge,
               colors="#222222", linewidth=1.8, linestyle="-", zorder=6,
               label="_nolegend_")
    # Vertical end-caps
    cap_h = eu_val * 0.018
    for xe in (xi + left_edge, xi + right_edge):
        ax1.vlines(xe, eu_val - cap_h, eu_val + cap_h,
                   colors="#222222", linewidth=1.8, zorder=6)
ax1.hlines([], [], [], colors="#222222", linewidth=1.8, linestyle="-", label="EU27")

STRINGS_BAR = {
    "title": rf"Hodinové náklady práce dle odvětví ({ref_year})",
    "ylabel": r"hodinové náklady práce [\si{\pps\per\hour}]",
}
ax1.set_xticks(x)
ax1.set_xticklabels([f"{SECTORS[s]}\n({s})" for s in sector_codes])
ax1.set_ylabel(STRINGS_BAR["ylabel"])
ax1.set_title(STRINGS_BAR["title"])
ax1.legend(frameon=False, fontsize=FIGURE_LABEL_SIZE, ncol=4)
ax1.set_ylim(0, None)
# y minor grid + remove x minor ticks
ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax1.grid(which="minor", axis="y", linewidth=0.2, alpha=0.4, color="#DDDDDD", zorder=0)
ax1.tick_params(axis="x", which="minor", bottom=False)

savefig_pgf(fig1, "eu_odvetvove_mzdy_bar", strings=STRINGS_BAR)
save_figure_tex_pgf(
    "eu_odvetvove_mzdy_bar",
    caption=f"Hodinové náklady práce (\\si{{\\pps\\per\\hour}}) v~odvětvích Průmysl~(C), Obchod~(G), \\acs{{ICT}}~(J) a~Finance~(K), \\acs{{geo-EU27}}, {ref_year}",
    label="fig:eu_odvetvove_mzdy_bar",
    resizebox_width=r"\linewidth",
    cite_key="eurostat_lc_lci_lev_D1D4MD5_PPS_h",
    strings=STRINGS_BAR,
)
print("Figure 1 saved.")

# ── 5. Figure 2: deviation from EU27 average ─────────────────────────────────
if "EU27_2020" in lc_pps.index:
    y = np.arange(len(sector_labels))
    n2 = len(COUNTRIES)
    bw2 = 0.12
    offs2 = np.linspace(-(n2 - 1) / 2, (n2 - 1) / 2, n2) * bw2

    fig2, ax2 = plt.subplots(figsize=cm2in(14, 9))

    for i, country in enumerate(COUNTRIES):
        if country not in lc_idx_6.index:
            continue
        pct_vals = [(lc_idx_6.loc[country, s] - 100)
                    for s in sector_codes]
        ax2.barh(y + offs2[i], pct_vals, bw2 * 0.9,
                 color=COUNTRY_COLORS.get(country, "#999999"),
                 label=country, zorder=3)

    STRINGS_ODCH = {
        "title": rf"Odchylka nákladů práce od průměru \acs{{geo-EU}}27 ({ref_year})",
        "xlabel": r"odchylka od průměru \acs{geo-EU}27 [\si{\pp}]",
    }
    ax2.axvline(0, color="black", linewidth=0.9, zorder=2)
    ax2.set_yticks(y)
    ax2.set_yticklabels([f"{SECTORS[s]} ({s})" for s in sector_codes])
    ax2.set_xlabel(STRINGS_ODCH["xlabel"])
    ax2.set_title(STRINGS_ODCH["title"])
    ax2.legend(frameon=False, fontsize=FIGURE_LABEL_SIZE, ncol=6)
    # x minor grid + remove y minor ticks
    ax2.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax2.grid(which="minor", axis="x", linewidth=0.2, alpha=0.4, color="#DDDDDD", zorder=0)
    ax2.tick_params(axis="y", which="minor", left=False)

    savefig_pgf(fig2, "eu_odvetvove_mzdy_odchylka", strings=STRINGS_ODCH)
    save_figure_tex_pgf(
        "eu_odvetvove_mzdy_odchylka",
        caption=(
            f"Odchylka odvětvových nákladů práce od průměru EU27, vybrané země EU, {ref_year}."),
        label="fig:eu_odvetvove_mzdy_odchylka",
        resizebox_width=r"\linewidth",
        cite_key="eurostat_lc_lci_lev_D1D4MD5_PPS_h",
        strings=STRINGS_ODCH,
    )
    print("Figure 2 saved.")

# ── 6. Combined 2×2 choropleth map ────────────────────────────────────────────
SECTOR_TITLES = {
    "C": "Průmysl (C)",
    "G": "Obchod (G)",
    "J": "ICT (J)",
    "K": "Finance (K)",
}

# Global vmin/vmax across all four sectors for a shared colour scale
all_vals = pd.concat(
    [lc_pps_all[s].dropna() for s in SECTOR_TITLES if s in lc_pps_all.columns]
)
vmin_global = all_vals.min()
vmax_global = all_vals.max()

# Keep canvas close to final LaTeX width to avoid aggressive downscaling
# by \resizebox{\linewidth}{!}{...}, which would shrink text too much.
fig_maps, axes = plt.subplots(2, 2, figsize=cm2in(15, 12))
panel_labels = iter("abcd")

STRINGS_MAP = {
    "title": f"Hodinové náklady práce dle odvětví, \\acs{{geo-EU27}} ({ref_year})",
    "colorbar_label": r"[\si{\pps\per\hour}]",
}

for ax_i, (sec_code, sec_title) in zip(axes.flat, SECTOR_TITLES.items()):
    if sec_code not in lc_pps_all.columns:
        print(f"  WARNING: sector {sec_code} not in all-EU data, skipping.")
        ax_i.set_visible(False)
        continue

    sector_series = lc_pps_all[sec_code].dropna()
    df_map = pd.DataFrame({
        "geo": sector_series.index,
        "time": int(ref_year),
        "value": sector_series.values,
    })
    ds_map = Dataset(
        df_map,
        name=f"Hodinové náklady práce {sec_code}",
        unit="PPS/h",
        source_url="Eurostat/lc_lci_lev",
    )

    choropleth(
        ds_map,
        year=int(ref_year),
        title="",
        colorbar_label=r"[\si{\pps\per\hour}]",
        cmap="RdYlGn",
        vmin=vmin_global,
        vmax=vmax_global,
        ax=ax_i,
        label_countries=True,
        country_label_size=MAP_COUNTRY_LABEL_SIZE,
        show_colorbar=False,  # shared colorbar added centrally below
    )
    apply_geo_labels_pgf(
        ax_i,
        halo=True,
        values=sector_series.to_dict(),
        tooltip_fmt="{:.1f}",
    )
    lbl = next(panel_labels)
    ax_i.set_title(
        f"({lbl}) {sec_title}",
        fontsize=FIGURE_COMPACT_TEXT_SIZE,
        pad=4,
    )

fig_maps.suptitle(
    STRINGS_MAP["title"],
    fontsize=FIGURE_COMPACT_TEXT_SIZE,
    y=0.98,
)

# Shared central colorbar — uses the EXACT same inset_axes(width=0.10, height=2.10)
# code path as the standard choropleth helper, so the raster strip is byte-identical
# and deduplicates to the same _shared/ PNG as all other RdYlGn choropleths.
# bbox_transform=transFigure lets bbox_to_anchor=(0.5, 0.5) mean "figure centre".
import matplotlib as mpl_lib
from mpl_toolkits.axes_grid1.inset_locator import inset_axes as _inset_axes
norm_shared = mpl_lib.colors.Normalize(vmin=vmin_global, vmax=vmax_global)
_base_cmap = mpl_lib.cm.get_cmap("RdYlGn")
_rgba = _base_cmap(np.linspace(0.0, 1.0, 256))
if CHOROPLETH_BLEND_WITH_WHITE:
    _blend = min(1.0, max(0.0, float(CHOROPLETH_WHITE_BLEND_PCT) / 100.0))
    _rgba[:, :3] = _rgba[:, :3] * (1.0 - _blend) + _blend
_shared_cmap = mpl_lib.colors.LinearSegmentedColormap.from_list(
    f"{_base_cmap.name}_wb{int(round(CHOROPLETH_WHITE_BLEND_PCT))}", _rgba, N=256
)
sm_shared = mpl_lib.cm.ScalarMappable(cmap=_shared_cmap, norm=norm_shared)
sm_shared.set_array([])
cax_center = _inset_axes(
    axes[0, 0],                        # parent axes (positional anchor only)
    width=0.10, height=2.10,           # identical to choropleth helper → same PNG
    loc="center",
    bbox_to_anchor=(0.5, 0.5),         # figure centre
    bbox_transform=fig_maps.transFigure,
    borderpad=0,
)
cb_center = fig_maps.colorbar(sm_shared, cax=cax_center,
                               label=STRINGS_MAP["colorbar_label"])
cb_center.ax.tick_params(labelsize=FIGURE_COMPACT_LABEL_SIZE)
cb_center.set_label(
    STRINGS_MAP["colorbar_label"],
    fontsize=FIGURE_COMPACT_LABEL_SIZE,
)

# Subplot spacing — no large central gap needed; colorbar is an inset overlay.
fig_maps.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.04,
                         wspace=0.14, hspace=0.10)
# Prevent savefig's tight_layout from clobbering the manual layout.
fig_maps._tight_layout_kwargs = {"pad": 0.4}
fig_maps._subplots_adjust_kwargs = {"left": 0.02, "right": 0.98,
                                    "top": 0.92, "bottom": 0.04,
                                    "wspace": 0.14, "hspace": 0.10}

savefig_pgf(fig_maps, "eu_odvetvove_mzdy_mapa", strings=STRINGS_MAP)
save_figure_tex_pgf(
    "eu_odvetvove_mzdy_mapa",
    caption=(
        f"Hodinové náklady práce (\\si{{\\pps\\per\\hour}}) v~odvětvích Průmysl~(C), Obchod~(G), \\acs{{ICT}}~(J) a~Finance~(K), EU27, {ref_year}."
    ),
    label="fig:eu_odvetvove_mzdy_mapa",
    resizebox_width=r"\linewidth",
    cite_key="eurostat_lc_lci_lev_D1D4MD5_PPS_h",
    strings=STRINGS_MAP,
)
print("Combined choropleth (2×2) saved.")

print("Done.")
