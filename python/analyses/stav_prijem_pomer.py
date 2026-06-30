r"""
Ratio of hourly net personal income (PPS) to GDP per capita per avg hour -- timeline.

Plots: (hourly net income in PPS) / (GDP PPS/cap / avg annual hours)
     = (annual net income in EUR / PLI) / GDP PPS/cap

Since average annual hours appear in both numerator and denominator they cancel,
yielding: net_income_PPS / GDP_PPS_per_capita (expressed as %).

This ratio shows how much of average GDP per capita a worker at 100 % of average
wage actually receives as disposable (net) income.

Data sources:
    Net annual earnings (PPS):      Eurostat ``earn_nt_net``
        (freq=A, currency=PPS, estruct=NET, ecase=P1_NCH_AW100)
  GDP per capita (PPS abs.):       Eurostat ``nama_10_pc``   (CP_PPS_EU27_2020_HAB.B1GQ)

Output
------
  pics/python/stav_prijem_pomer.pdf
  latex/texparts/python/stav_prijem_pomer.tex

Run
---
    python analyses/stav_prijem_pomer.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from statout.timeline import EU27 as _EU27

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style_pgf, savefig_pgf, save_figure_tex_pgf, add_pgf_tooltips
from statout.timeline import timeline

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "SK", "PL", "AT", "DE", "DK"]
START_YEAR = 2004

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
print("Downloading Eurostat data …")

# Net annual earnings for single person, no children, 100% AW (PPS, all geo)
# earn_nt_net: freq.currency.estruct.ecase.geo
path_net = fetch_eurostat(
    "earn_nt_net",
    "A.PPS.NET.P1_NCH_AW100.",
    start_period=START_YEAR,
)

# GDP per capita in PPS (absolute, current prices) -- all geo
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
      f"{ds_ratio.years[0] if ds_ratio.years else '?'}--{ds_ratio.years[-1] if ds_ratio.years else '?'}")

# ── 5. Plot ───────────────────────────────────────────────────────────────────
STRINGS = {
    "title": r"Čistý příjem jako podíl \acs{HDP} na obyvatele",
    "ylabel": r"čistý příjem / \acs{HDP} na obyvatele [\acs{geo-EU}27 = 100]",
}
fig = timeline(
    ds_ratio,
    countries=COUNTRIES,
    title=STRINGS["title"],
    ylabel=STRINGS["ylabel"],
    background_eu=True,
    annotate_last=True,
)

fig.axes[0].set_xlim(START_YEAR, max(2025, ds_ratio.years[-1]))
# ── PGF tooltips & geo labels ───────────────────────────────────────────
_pivot_pp = (
    ds_ratio.df[ds_ratio.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(fig.axes[0], _pivot_pp, fmt="{:.2f}")
_bg_pp = sorted(set(_EU27) - set(COUNTRIES))
_pivot_pp_bg = (
    ds_ratio.df[ds_ratio.df["geo"].isin(_bg_pp)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(fig.axes[0], _pivot_pp_bg, fmt="{:.2f}")
for _child in fig.axes[0].get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")
# ── 6. Save ───────────────────────────────────────────────────────────────────
savefig_pgf(fig, "stav_prijem_pomer", strings=STRINGS)

# ── 7. LaTeX snippet ──────────────────────────────────────────────────────────
last_year = ds_ratio.years[-1] if ds_ratio.years else "?"
save_figure_tex_pgf(
    "stav_prijem_pomer",
    caption=f"Poměr čistého příjmu k~\\acs{{HDP}} na obyvatele (\\acs{{EU}}27\\,=\\,100), vybrané země EU, {START_YEAR}--{last_year}.",
    label="fig:stav_prijem_pomer",
    resizebox_width=r"\linewidth",
    cite_keys=["eurostat_earn_nt_net_PPS_AW100", "eurostat_nama_10_pc_PPS_EU27eq100"],
    strings=STRINGS,
)

print("Done.")
