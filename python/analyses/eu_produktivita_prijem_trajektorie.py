r"""
Trajectory analysis: labour productivity per hour vs net hourly income.

The figure follows the variables used in ``korelace_analyza.py``:

* x-axis: nominal labour productivity per hour worked (PPS, EU27=100),
  Eurostat ``nama_10_lp_ulc``;
* y-axis: net annual earnings for a single worker at 100 % AW, in PPS,
  divided by actual annual hours worked, Eurostat ``earn_nt_net`` and
  ``lfsa_ewhan2``.

Ireland and Luxembourg are excluded because productivity per hour is strongly
distorted by multinational accounting and cross-border-worker effects.

Output
------
  python/figures/eu_produktivita_prijem_trajektorie.pgf
  latex/texparts/python/eu_produktivita_prijem_trajektorie.tex
  latex/texparts/figures/eu_produktivita_prijem_trajektorie.tex

Run
---
    python analyses/eu_produktivita_prijem_trajektorie.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from config import COUNTRY_COLORS, FIGURE_TEXT_SIZE, FIGURE_LABEL_SIZE, FIGURE_COMPACT_LABEL_SIZE
from statout.timeline import EU27
from stattool.dataset import Dataset
from stattool.fetch import fetch_eurostat
from stattool.style import apply_style_pgf, cm2in, save_figure_tex_pgf, savefig_pgf

# -- Parameters ----------------------------------------------------------------

STEM = "eu_produktivita_prijem_trajektorie"
COUNTRIES = ["CZ", "SK", "PL", "AT", "DE", "DK"]
EXCLUDE_OUTLIERS = {"IE", "LU"}
START_YEAR = 2004
WEEKS_PER_YEAR = 52.18

LABEL_OFFSETS: dict[str, tuple[float, float]] = {
    "CZ": (6, -2),
    "SK": (6, -7),
    "PL": (6, 5),
    "AT": (6, 3),
    "DE": (6, -2),
    "DK": (6, 3),
}

# -- 0. Style ------------------------------------------------------------------

apply_style_pgf()

# -- 1. Download ---------------------------------------------------------------

print("Downloading Eurostat data ...")

path_prod = fetch_eurostat(
    "nama_10_lp_ulc",
    "A.PC_EU27_2020_MPPS_CP.NLPR_HW.",
    start_period=START_YEAR,
)

path_net = fetch_eurostat(
    "earn_nt_net",
    "A.PPS.NET.P1_NCH_AW100.",
    start_period=START_YEAR,
)

path_hours = fetch_eurostat(
    "lfsa_ewhan2",
    "A.TOTAL.EMP.TOTAL.Y15-64.T.HR.",
    start_period=START_YEAR,
)

print("Download complete.")

# -- 2. Parse and derive hourly net income ------------------------------------

ds_prod = Dataset.from_sdmx_csv(
    path_prod,
    name="Produktivita práce/h",
    unit="EU27=100",
    source_url="Eurostat/nama_10_lp_ulc",
)
prod = ds_prod.df[[ds_prod.geo_col, ds_prod.time_col, ds_prod.value_col]].rename(
    columns={ds_prod.geo_col: "geo", ds_prod.time_col: "time", ds_prod.value_col: "prod"}
)
prod["time"] = prod["time"].astype(int)

raw_net = pd.read_csv(path_net)[["geo", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
raw_net.columns = ["geo", "time", "net_pps"]
raw_net["time"] = raw_net["time"].astype(int)

ds_hours = Dataset.from_sdmx_csv(
    path_hours,
    name="Skutečná týdenní pracovní doba",
    unit="h/týden",
    source_url="Eurostat/lfsa_ewhan2",
)
hours = ds_hours.df[[ds_hours.geo_col, ds_hours.time_col, ds_hours.value_col]].rename(
    columns={ds_hours.geo_col: "geo", ds_hours.time_col: "time", ds_hours.value_col: "hours"}
)
hours["time"] = hours["time"].astype(int)

hourly = raw_net.merge(hours, on=["geo", "time"], how="inner")
hourly = hourly[hourly["hours"] > 0].copy()
hourly["income_pps_hour"] = hourly["net_pps"] / (hourly["hours"] * WEEKS_PER_YEAR)

panel = prod.merge(hourly[["geo", "time", "income_pps_hour"]], on=["geo", "time"], how="inner")
panel = panel[~panel["geo"].isin(EXCLUDE_OUTLIERS)].dropna(subset=["prod", "income_pps_hour"])

country_panel = panel[panel["geo"] != "EU27_2020"].copy()
eu_traj = panel[panel["geo"] == "EU27_2020"].sort_values("time")

years = sorted(country_panel["time"].unique())
last_year = int(years[-1])
print(f"Loaded panel: {len(country_panel['geo'].unique())} countries, {years[0]}--{last_year}")

# -- 3. Plot -------------------------------------------------------------------

STRINGS = {
    "title": r"Produktivita práce a čistý hodinový příjem",
    "xlabel": r"produktivita práce [\acs{geo-EU}27 = 100]",
    "ylabel": r"čistý hodinový příjem [\si{\pps\per\hour}]",
}

fig, ax = plt.subplots(figsize=cm2in(15, 10))

background_geos = sorted((EU27 & set(country_panel["geo"])) - set(COUNTRIES) - EXCLUDE_OUTLIERS)
for geo in background_geos:
    traj = country_panel[country_panel["geo"] == geo].sort_values("time")
    if len(traj) < 2:
        continue
    ax.plot(
        traj["prod"],
        traj["income_pps_hour"],
        color="#C6C6C6",
        linewidth=0.65,
        alpha=0.45,
        zorder=1,
    )

if not eu_traj.empty:
    ax.plot(
        eu_traj["prod"],
        eu_traj["income_pps_hour"],
        color="#444444",
        linewidth=1.2,
        linestyle=":",
        marker="o",
        markersize=2.5,
        zorder=2,
    )
    eu_last = eu_traj.iloc[-1]
    ax.annotate(
        r"\acs{geo-EU}27",
        xy=(eu_last["prod"], eu_last["income_pps_hour"]),
        xytext=(5, 4),
        textcoords="offset points",
        fontsize=FIGURE_LABEL_SIZE,
        color="#444444",
        va="center",
    )

for geo in COUNTRIES:
    traj = country_panel[country_panel["geo"] == geo].sort_values("time")
    if len(traj) < 2:
        print(f"  skipped {geo}: insufficient paired observations")
        continue
    color = COUNTRY_COLORS.get(geo, "#333333")
    ax.plot(
        traj["prod"],
        traj["income_pps_hour"],
        color=color,
        linewidth=2.0,
        marker="o",
        markersize=3.0,
        markeredgecolor="white",
        markeredgewidth=0.35,
        zorder=4,
    )
    first = traj.iloc[0]
    last = traj.iloc[-1]
    offset = LABEL_OFFSETS.get(geo, (6, 0))
    ax.annotate(
        rf"\acs{{geo-{geo}}}",
        xy=(last["prod"], last["income_pps_hour"]),
        xytext=offset,
        textcoords="offset points",
        fontsize=FIGURE_LABEL_SIZE,
        color=color,
        fontweight="bold",
        va="center",
    )
    ax.scatter(
        [first["prod"], last["prod"]],
        [first["income_pps_hour"], last["income_pps_hour"]],
        s=[22, 35],
        color=color,
        edgecolors="white",
        linewidth=0.5,
        zorder=5,
    )
    print(
        f"  {geo}: {int(first['time'])} -> {int(last['time'])} | "
        f"prod {first['prod']:.1f} -> {last['prod']:.1f}; "
        f"net {first['income_pps_hour']:.1f} -> {last['income_pps_hour']:.1f} PPS/h"
    )

ax.axvline(100, color="#555555", linewidth=0.8, linestyle="--", alpha=0.7, zorder=2)
ax.text(
    100,
    ax.get_ylim()[1],
    r"\acs{geo-EU}27 = 100",
    fontsize=FIGURE_COMPACT_LABEL_SIZE,
    color="#555555",
    ha="right",
    va="top",
    rotation=90,
)

ax.set_xlabel(STRINGS["xlabel"])
ax.set_ylabel(STRINGS["ylabel"])
ax.set_title(STRINGS["title"])
ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=7))
ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=7))
ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax.grid(which="major", linewidth=0.4, alpha=0.5, color="#AAAAAA", zorder=0)
ax.grid(which="minor", linewidth=0.2, alpha=0.35, color="#DDDDDD", zorder=0)

x_min = max(40, country_panel["prod"].min() - 5)
x_max = min(175, country_panel["prod"].max() + 8)
y_min = max(0, country_panel["income_pps_hour"].min() - 1.5)
y_max = country_panel["income_pps_hour"].max() + 2.0
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

# Re-apply reference label after limits are fixed.
for child in ax.get_children():
    if hasattr(child, "get_text") and child.get_text() == r"\acs{geo-EU}27 = 100":
        child.set_position((100, y_max))

fig._tight_layout_kwargs = {"pad": 1.2}

# -- 4. Save -------------------------------------------------------------------

savefig_pgf(fig, STEM, strings=STRINGS)

save_figure_tex_pgf(
    STEM,
    caption=(
        f"Trajektorie produktivity práce a~čistého hodinového příjmu, "
        f"státy \\acs{{EU}}, {years[0]}--{last_year}."
    ),
    cite_keys=[
        "eurostat_nama_10_lp_ulc_NLPR_HW_EU27eq100",
        "eurostat_earn_nt_net_PPS_AW100",
        "eurostat_lfsa_ewhan2_HR_weekly",
    ],
    label=f"fig:{STEM}",
    resizebox_width=r"\linewidth",
    strings=STRINGS,
)

print("Done.")
