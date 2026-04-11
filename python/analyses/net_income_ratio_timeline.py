r"""
Ratio of hourly net personal income (PPS) to GDP per capita per avg hour – timeline.

Plots: (hourly net income in PPS) / (GDP PPS/cap / avg annual hours)
     = (annual net income in EUR / PLI) / GDP PPS/cap

Since average annual hours appear in both numerator and denominator they cancel,
yielding: net_income_PPS / GDP_PPS_per_capita (expressed as %).

This ratio shows how much of average GDP per capita a worker at 100 % of average
wage actually receives as disposable (net) income.

Data sources:
    Net annual earnings (PPS):      Eurostat ``earn_nt_net``
        (freq=A, currency=PPS, estruct=NET, ecase=P1_NCH_AW100)
  GDP per capita (PPS EU27=100):  Eurostat ``nama_10_pc``   (CP_PPS_EU27_2020_HAB.B1GQ)

Output
------
  pics/python/net_income_ratio_timeline.pdf
  latex/texparts/python/net_income_ratio_timeline.tex

Run
---
    python analyses/net_income_ratio_timeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from statout.timeline import EU27 as _EU27

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "SK", "PL", "AT", "DE", "DK"]
START_YEAR = 2004

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
print("Downloading Eurostat data …")

# Net annual earnings for single person, no children, 100% AW (PPS, all geo)
# earn_nt_net: freq.currency.estruct.ecase.geo
path_net = fetch_eurostat(
    "earn_nt_net",
    "A.PPS.NET.P1_NCH_AW100.",
    start_period=START_YEAR,
)

# GDP per capita in PPS (EU27_2020 = 100) – all geo
path_gdp = fetch_eurostat(
    "nama_10_pc",
    "A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.",
    start_period=START_YEAR,
)

print("Download complete.")

# ── 2. Parse ──────────────────────────────────────────────────────────────────
raw_net = pd.read_csv(path_net)
raw_net = raw_net[["geo", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
raw_net.columns = ["geo", "time", "net_pps"]
raw_net["time"] = raw_net["time"].astype(int)

raw_gdp = pd.read_csv(path_gdp)
raw_gdp = raw_gdp[["geo", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
raw_gdp.columns = ["geo", "time", "gdp_pps"]
raw_gdp["time"] = raw_gdp["time"].astype(int)

# ── 3. Compute ratio ──────────────────────────────────────────────────────────
df = raw_net.merge(raw_gdp, on=["geo", "time"], how="inner")

# ratio = net_income_PPS / GDP_PPS_per_capita   (expressed as %)
df["value"] = df["net_pps"] / df["gdp_pps"] * 100.0
df = df[["geo", "time", "value"]].dropna()

# ── 3b. Normalise to EU27=100 ─────────────────────────────────────────────────────────────────
# Use ARITHMETIC MEAN of EU27 member countries as the normalisation denominator
# (not the GDP-weighted EU27_2020 aggregate).  This ensures that the arithmetic
# mean of country-level normalised values equals 100 in every year, making the
# grey background cloud visually centred on the 100 % reference line.
# (Using the population-weighted aggregate would put the displayed mean at ~87 %
# because large, high-income countries like DE/FR dominate the aggregate.)
eu27_ratio = (
    df[df["geo"].isin(_EU27)]
    .groupby("time")["value"].mean()
)
df = df.merge(eu27_ratio.rename("eu27"), on="time", how="left")
df["value"] = df["value"] / df["eu27"] * 100.0
df = df.drop(columns=["eu27"]).dropna(subset=["value"])
# Remove EU27 aggregate row (no longer needed)
df = df[df["geo"] != "EU27_2020"]

# ── 4. Build Dataset ──────────────────────────────────────────────────────────
ds_ratio = Dataset(
    df,
    name="Čistý příjem/HDP na obyvatele",
    unit="EU27=100",
    source_url="Eurostat/earn_nt_net, nama_10_pc",
)

print(f"Ratio data: {len(ds_ratio.countries)} countries, "
      f"{ds_ratio.years[0] if ds_ratio.years else '?'}–{ds_ratio.years[-1] if ds_ratio.years else '?'}")

# ── 5. Plot ───────────────────────────────────────────────────────────────────
fig = timeline(
    ds_ratio,
    countries=COUNTRIES,
    title="Čistý příjem jako podíl HDP na obyvatele",
    ylabel="čistý příjem / HDP na ob. (EU27 = 100)",
    background_eu=True,
    annotate_last=True,
)

fig.axes[0].set_xlim(START_YEAR, ds_ratio.years[-1])

# ── 6. Save ───────────────────────────────────────────────────────────────────
savefig(fig, "net_income_ratio_timeline", out_dir=LATEX_PICS_DIR)

# ── 7. LaTeX snippet ──────────────────────────────────────────────────────────
last_year = ds_ratio.years[-1] if ds_ratio.years else "?"
save_figure_tex(
    "net_income_ratio_timeline",
    caption=(
        "Poměr ročního čistého příjmu pracovníka (100\\,\\% prům.~mzdy, "
        "svobodný bez dětí) v~PPS k~HDP na obyvatele v~PPS, normováno na "
        "průměr EU27\\,=\\,100 (Eurostat/\\texttt{earn\\_nt\\_net} + "
        "\\texttt{nama\\_10\\_pc}; obě řady v~PPS). "
        f"{START_YEAR}--{last_year}. "
        "Šedé linie = ostatní země EU27."
    ),
    label="fig:net_income_ratio_timeline",
    width=r"0.95\linewidth",
    cite_key="eurostat_earn_nt_net_PPS_AW100,eurostat_nama_10_pc_PPS_EU27eq100",
)

print("Done.")
