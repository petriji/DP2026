r"""
Top 5 % wealth share timeline – CZ, AT, DE, DK, SK, FI.

Shows changes in the top 5 % net wealth share (% of total household net
wealth) from OECD HFCS survey waves.  The top 5 % captures the broadest
concentration trend, making it suitable for cross-country comparison.

Data source: OECD Wealth Distribution database (WEALTH dataset, SH_TOP5)

Output
------
  pics/python/eu_bohatstvi_top20.pdf
  latex/texparts/python/eu_bohatstvi_top20.tex

Run
---
    python analyses/eu_bohatstvi_top20.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR
from stattool.fetch import fetch_oecd
from stattool.dataset import Dataset
from stattool.style import cm2in, apply_style_pgf, savefig_pgf, save_figure_tex_pgf

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "SK", "FI"]
START_YEAR = 2008

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
# WEALTH dataset: SH_TOP5 = top 5 % net wealth share (% of total)
path = fetch_oecd("WEALTH", start_period=START_YEAR)

ds = Dataset.from_oecd_csv(
    path,
    name="Podíl top 5 % na čistém jmění",
    unit="%",
    source_url="OECD Wealth Distribution / WEALTH",
    filters={"MEASURE": "SH_TOP5"},
)

print(f"Loaded: {len(ds.countries)} countries, {ds.years[0]}–{ds.years[-1]}")

# ── 2. Separate all-countries data from highlighted subset ────────────────────
ds_all = ds   # keep all for grey cloud
ds_highlighted = Dataset(
    ds.df[ds.df[ds.geo_col].isin(COUNTRIES)].copy(),
    name=ds.name, unit=ds.unit,
    geo_col=ds.geo_col, time_col=ds.time_col, value_col=ds.value_col,
    source_url=ds.source_url,
)

# ── 3. Plot ───────────────────────────────────────────────────────────────────
# Survey data is sparse — plot as markers connected by dashed lines per country
fig, ax = plt.subplots(figsize=cm2in(15, 9))

# Grey cloud — all other countries in the dataset
for country in ds_all.countries:
    if country in COUNTRIES:
        continue
    sub = (
        ds_all.df[ds_all.df[ds_all.geo_col] == country]
        .sort_values(ds_all.time_col)
        .dropna(subset=[ds_all.value_col])
    )
    if sub.empty:
        continue
    ax.plot(
        sub[ds_all.time_col], sub[ds_all.value_col],
        marker=".", markersize=4,
        linestyle="--" if len(sub) > 1 else "none",
        color="#C8C8C8", linewidth=0.6, alpha=0.6, zorder=1,
    )

for country in COUNTRIES:
    sub = (
        ds_highlighted.df[ds_highlighted.df[ds_highlighted.geo_col] == country]
        .sort_values(ds_highlighted.time_col)
        .dropna(subset=[ds_highlighted.value_col])
    )
    if sub.empty:
        continue
    color = COUNTRY_COLORS.get(country, "#999999")
    ax.plot(
        sub[ds_highlighted.time_col], sub[ds_highlighted.value_col],
        marker="o", markersize=5.5,
        linestyle="--" if len(sub) > 1 else "none",
        color=color, linewidth=1.5, label=country,
    )
    # Label last point
    last = sub.iloc[-1]
    ax.annotate(
        f"{country}",
        xy=(last[ds_highlighted.time_col], last[ds_highlighted.value_col]),
        xytext=(4, 0), textcoords="offset points",
        fontsize=FONT_SIZE, color=color, va="center",
    )

ax.set_xlabel("rok (HFCS vlna)")
ax.set_ylabel("podíl top 5 % domácností na čistém jmění [%]")
ax.set_title("Podíl top 5 % domácností na čistém jmění")
ax.set_ylim(20, 60)
if ds_all.years:
    ax.set_xlim(ds_all.years[0] - 1, max(ds_all.years[-1], 2025))

# ── 4. Save ───────────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_bohatstvi_top20")

# ── 5. LaTeX snippet ──────────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_bohatstvi_top20",
    caption=(
        f"Podíl top 5\\,\\% na čistém jmění domácností, HFCS {START_YEAR}--{ds_all.years[-1] if ds_all.years else ''}. "
        "Přerušovaná spojnice propojuje průzkumné vlny (data nejsou roční). "
        "Šedé linie = ostatní země v~datové sadě."
    ),
    label="fig:eu_bohatstvi_top20",
    resizebox_width=r"0.95\linewidth",
    cite_key="oecd_hfcs_wealth_top5_PC",
    strings={},
)

print("Done.")
