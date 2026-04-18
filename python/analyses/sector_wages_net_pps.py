r"""
Hourly wages by NACE sector in PPS – grouped bar chart, deviation from EU27,
and per-sector choropleth maps for all EU27 countries.

Compares gross hourly wages (adjusted for purchasing power parity) across
key economic sectors: C (manufacturing), G (wholesale/retail), J (ICT),
K (financial services).

Data sources:
  Labour costs per hour (EUR): Eurostat ``lc_lci_lev`` (D1_D4_MD5 total, fallback D1)
  Price Level Index (GDP):     Eurostat ``prc_ppp_ind`` (PLI_EU27_2020.GDP)

Output
------
  pics/python/sector_wages_bar.pdf
  pics/python/sector_wages_deviation.pdf
  pics/python/sector_wages_map_{C,G,J,K}.pdf
  latex/texparts/python/sector_wages_bar.tex
  latex/texparts/python/sector_wages_deviation.tex
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

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, cm2in, savefig, save_figure_tex
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
COUNTRIES_EU = COUNTRIES + ["EU27_2020"]
GEO_6 = "+".join(COUNTRIES)
GEO_WITH_EU = GEO_6 + "+EU27_2020"
SECTORS = {"C": "Výroba", "G": "Obchod", "J": "ICT", "K": "Finance"}
DISPLAY_YEAR = 2024   # latest available full year

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download sector wages (EUR/h) – 6 countries + EU27 ────────────────────
# lc_lci_lev: freq.unit.lcstruct.nace_r2.geo
# D1_D4_MD5 = total labour costs (wages + employer contributions − direct subsidies)
# D11 (wages only) is NOT used – D1_D4_MD5 is available for all sectors/countries.
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
for s in SECTORS:
    if pd.isna(lc_pps.loc[_EU27_GEO, s]) if s in lc_pps.columns else True:
        if s in lc_pps_all.columns:
            fallback_eu = lc_pps_all[s].dropna().mean()
            lc_pps.loc[_EU27_GEO, s] = fallback_eu
            print(f"  EU27 fallback mean used for sector {s}: {fallback_eu:.2f} PPS/h")

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

ax1.set_xticks(x)
ax1.set_xticklabels([f"{SECTORS[s]}\n({s})" for s in sector_codes])
ax1.set_ylabel("hodinové náklady práce [PPS/h]")
ax1.set_title(f"Náklady práce ve vybraných odvětvích a zemích EU27 ({ref_year})")
ax1.legend(frameon=False, fontsize=FONT_SIZE - 1, ncol=4)
ax1.set_ylim(0, None)
# y minor grid + remove x minor ticks
ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax1.grid(which="minor", axis="y", linewidth=0.2, alpha=0.4, color="#DDDDDD", zorder=0)
ax1.tick_params(axis="x", which="minor", bottom=False)

savefig(fig1, "sector_wages_bar", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "sector_wages_bar",
    caption=(
        f"Celkové hodinové náklady práce, klíčová odvětví, {ref_year}. [PPS/h] v~klíčových odvětvích NACE ({ref_year}). "
        f"EUR/h přepočteno na PPS/h pomocí \\texttt{{prc\\_ppp\\_ind}}. "
        f"Plná čára s~zarážkami = průměr EU27 pro dané odvětví."
    ),
    label="fig:sector_wages_bar",
    width=r"0.95\linewidth",
    cite_key="eurostat_lc_lci_lev_D1D4MD5_PPS_h",
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

    ax2.axvline(0, color="black", linewidth=0.9, zorder=2)
    ax2.set_yticks(y)
    ax2.set_yticklabels([f"{SECTORS[s]} ({s})" for s in sector_codes])
    ax2.set_xlabel("odchylka od průměru EU27 [PPS/h]")
    ax2.set_title(f"Srovnání nákladů práce ve vybraných odvětvích a zemích EU27 ({ref_year})")
    ax2.legend(frameon=False, fontsize=FONT_SIZE - 1, ncol=6)
    # x minor grid + remove y minor ticks
    ax2.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax2.grid(which="minor", axis="x", linewidth=0.2, alpha=0.4, color="#DDDDDD", zorder=0)
    ax2.tick_params(axis="y", which="minor", left=False)

    savefig(fig2, "sector_wages_deviation", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "sector_wages_deviation",
        caption=(
            f"Odchylka nákladů práce od průměru EU27, {ref_year}.. "
            f"EUR/h přepočteno na PPS/h pomocí \\texttt{{prc\\_ppp\\_ind}}. "
            f"Záporné hodnoty = nižší náklady práce než průměr EU27."
        ),
        label="fig:sector_wages_deviation",
        width=r"0.95\linewidth",
        cite_key="eurostat_lc_lci_lev_D1D4MD5_PPS_h",
    )
    print("Figure 2 saved.")

# ── 6. Figures 3–6: choropleth maps per sector ────────────────────────────────
SECTOR_TITLES = {
    "C": "Průmysl (C)",
    "G": "Obchod (G)",
    "J": "ICT (J)",
    "K": "Finance (K)",
}
for sec_code, sec_title in SECTOR_TITLES.items():
    if sec_code not in lc_pps_all.columns:
        print(f"  WARNING: sector {sec_code} not in all-EU data, skipping choropleth.")
        continue

    # Build Dataset for this sector map (single year, geo-value rows, absolute PPS/h)
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

    fig_map = choropleth(
        ds_map,
        year=int(ref_year),
        title=f"Hodinové náklady práce – {sec_title} ({ref_year})",
        colorbar_label="[PPS/h]",
        cmap="RdYlGn",
        vmin=None,
        vmax=None,
    )

    fig_name = f"sector_wages_map_{sec_code}"
    savefig(fig_map, fig_name, out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        fig_name,
        caption=(
            f"Hodinové náklady práce v~odvětví {sec_title}, EU27, {ref_year}. "
            f"EUR/h přepočteno na PPS/h pomocí \\texttt{{prc\\_ppp\\_ind}}; šedá~= data nedostupná."
        ),
        label=f"fig:{fig_name}",
        width=r"0.85\linewidth",
        cite_key="eurostat_lc_lci_lev_D1D4MD5_PPS_h",
    )
    print(f"Choropleth {sec_code} saved.")

print("Done.")
