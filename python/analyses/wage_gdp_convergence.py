r"""
GDP per capita vs Labour Cost convergence to EU27 – CZ, SK, PL, AT, DE, DK.

Shows that GDP per capita (PPS, EU27=100) is converging faster toward the
EU27 average than labour cost levels (EUR/hour, normalised to EU27=100),
supporting the thesis argument that Czech employees do not fully capture the
gains from economic convergence.

Data sources:
  GDP per capita (PPS, EU27=100): Eurostat ``nama_10_pc``
  Labour cost level (€/hour):     Eurostat ``lc_lcsts_r2``
    Both normalised to EU27=100 by dividing by the EU27_2020 aggregate value.

Output
------
  pics/wage_gdp_convergence.pdf
  latex/texparts/wage_gdp_convergence.tex  ← \input{} this in main.tex

Run
---
    python analyses/wage_gdp_convergence.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib.pyplot as plt

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "SK", "PL", "AT", "DE", "DK"]
GEO_6 = "+".join(COUNTRIES)
GEO_WITH_EU = GEO_6 + "+EU27_2020"
START_YEAR = 2004
HIGHLIGHT_COUNTRY = "CZ"

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
print("Downloading Eurostat data …")

# GDP per capita in PPS (absolute EUR PPS) – includes EU27_2020 for normalisation
path_gdp = fetch_eurostat(
    "nama_10_pc",
    f"A.CP_PPS_EU27_2020_HAB.B1GQ.{GEO_WITH_EU}",
    start_period=START_YEAR,
)

# Labour cost level (€/hour) – total economy, total labour cost component
# lc_lcsts_r2: freq · nace_r2 · indic_lc · unit · geo
# TOTAL = total economy; LCC = total labour cost per hour worked
path_lc = fetch_eurostat(
    "lc_lcsts_r2",
    f"A.B-S.LCC.EUR_HOUR.{GEO_6}",
    start_period=START_YEAR,
)

print("Download complete.")

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds_gdp = Dataset.from_sdmx_csv(
    path_gdp,
    name="HDP/obyvatele",
    unit="EUR PPS",
    source_url="Eurostat/nama_10_pc",
)

ds_lc = Dataset.from_sdmx_csv(
    path_lc,
    name="Mzdové náklady/h",
    unit="EUR/h",
    source_url="Eurostat/lc_lcsts_r2",
)


# ── 3. Normalise to EU27=100 ──────────────────────────────────────────────────

def _to_eu100(ds: Dataset, eu_geo: str = "EU27_2020") -> "Dataset":
    """Return a new Dataset with values normalised to EU average = 100.

    If *eu_geo* is absent, falls back to computing the mean over all
    available country rows for each year.
    """
    df = ds.df.copy()
    eu_rows = df[df[ds.geo_col] == eu_geo]

    if not eu_rows.empty:
        eu_series = (
            eu_rows.groupby(ds.time_col)[ds.value_col].mean().rename("_eu")
        )
    else:
        # Approximate EU27 average from available countries
        eu_series = (
            df.groupby(ds.time_col)[ds.value_col].mean().rename("_eu")
        )

    df = df.merge(eu_series, on=ds.time_col, how="left")
    df[ds.value_col] = df[ds.value_col] / df["_eu"] * 100
    df = df.drop(columns=["_eu"]).dropna(subset=[ds.value_col])
    return Dataset(
        df[df[ds.geo_col] != eu_geo],
        name=ds.name,
        unit="EU27=100",
        geo_col=ds.geo_col,
        time_col=ds.time_col,
        value_col=ds.value_col,
        source_url=ds.source_url,
    )


ds_gdp_idx = _to_eu100(ds_gdp)
ds_lc_idx = _to_eu100(ds_lc)

common_years = sorted(set(ds_gdp_idx.years) & set(ds_lc_idx.years))
print(
    f"GDP: {ds_gdp_idx.years[0]}–{ds_gdp_idx.years[-1]}  |  "
    f"LCC: {ds_lc_idx.years[0]}–{ds_lc_idx.years[-1]}  |  "
    f"Common: {common_years[0]}–{common_years[-1]}"
)

# ── 4. Extract CZ series ──────────────────────────────────────────────────────
gdp_cz = (
    ds_gdp_idx.for_country(HIGHLIGHT_COUNTRY)
    .set_index(ds_gdp_idx.time_col)[ds_gdp_idx.value_col]
    .reindex(common_years)
)
lc_cz = (
    ds_lc_idx.for_country(HIGHLIGHT_COUNTRY)
    .set_index(ds_lc_idx.time_col)[ds_lc_idx.value_col]
    .reindex(common_years)
)

# ── 5. Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=cm2in(15, 9))

color_gdp = COUNTRY_COLORS.get(HIGHLIGHT_COUNTRY, "#0072B2")
color_lc = "#D55E00"   # vermillion from PALETTE

ax.plot(
    common_years, gdp_cz.values,
    label="HDP/obyvatele (EU27\u00a0=\u00a0100)",
    color=color_gdp, linewidth=2.0,
)
ax.plot(
    common_years, lc_cz.values,
    label="Mzdové náklady/h (EU27\u00a0=\u00a0100)",
    color=color_lc, linewidth=2.0, linestyle="--",
)

# EU27=100 reference line
ax.axhline(100, color="gray", linewidth=0.8, linestyle=":", alpha=0.6, zorder=1)
ax.annotate(
    "EU27\u00a0=\u00a0100",
    xy=(common_years[-1], 100),
    xytext=(-65, 4),
    textcoords="offset points",
    fontsize=FONT_SIZE,
    color="gray",
    alpha=0.8,
)

ax.set_xlabel("rok")
ax.set_ylabel("Index (EU27\u00a0=\u00a0100)")
ax.set_title("ČR: konvergence HDP vs. mzdové náklady (EU27\u00a0=\u00a0100)")
ax.legend(frameon=False, fontsize=FONT_SIZE)
if common_years:
    ax.set_xlim(common_years[0], common_years[-1])

# ── 6. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "wage_gdp_convergence", out_dir=LATEX_PICS_DIR)

# ── 7. Write LaTeX snippet ────────────────────────────────────────────────────
last_year = common_years[-1] if common_years else ds_gdp_idx.years[-1]
save_figure_tex(
    "wage_gdp_convergence",
    caption=(
        "Konvergence ČR k průměru EU27: HDP na obyvatele v paritě kupní síly "
        "a mzdové náklady na odpracovanou hodinu – oba indexy normovány na "
        f"EU27\\,=\\,100, {START_YEAR}--{last_year}."
    ),
    label="fig:wage_gdp_convergence",
    width=r"0.95\linewidth",
    cite_key="eurostat_nama_10_pc",
)

print("Done.")
