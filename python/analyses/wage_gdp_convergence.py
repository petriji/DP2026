r"""
Labour productivity (GDP/hour worked) vs net disposable income convergence to EU27.

Solid lines   = real labour productivity per hour worked (PPS, EU27=100)
Dashed lines  = annual net disposable income (PPS, EU27=100) for single worker at 100 % AW

LU and IE are excluded: both are extreme outliers driven by multinational HQ accounting
effects and cross-border worker mechanics, not genuine living-standard convergence.

Data sources:
  Labour productivity/h (PPS EU27=100):  Eurostat ``nama_10_lp_ulc``
    unit = PC_EU27_2020_MPPS_CP, na_item = NLPR_HW (nominal LP per hour, % of EU27)
  Net disposable income (PPS, annual):    Eurostat ``earn_nt_net``
    currency = PPS, estruct = NET, ecase = P1_NCH_AW100 (single, no children, 100 % AW)
  Both normalised to EU27=100 per year.

Output
------
  pics/python/wage_gdp_convergence.pdf
  latex/texparts/python/wage_gdp_convergence.tex

Run
---
    python analyses/wage_gdp_convergence.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, cm2in, savefig, save_figure_tex
from statout.timeline import EU27

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "SK", "PL", "AT", "DE", "DK"]
EXCLUDE_OUTLIERS = {"LU", "IE"}   # extreme outliers: ~270 and ~175 EU27=100
START_YEAR = 2004

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
print("Downloading Eurostat data …")

# Labour productivity per hour worked as % of EU27 (PPS, current prices)
# nama_10_lp_ulc: freq . unit . na_item . geo
# unit = PC_EU27_2020_MPPS_CP, na_item = NLPR_HW → value already = EU27=100
path_lp = fetch_eurostat(
    "nama_10_lp_ulc",
    "A.PC_EU27_2020_MPPS_CP.NLPR_HW.",
    start_period=START_YEAR,
)

# Net annual earnings in PPS (single person, no children, 100 % AW) – all countries
path_net = fetch_eurostat(
    "earn_nt_net",
    "A.PPS.NET.P1_NCH_AW100.",
    start_period=START_YEAR,
)

print("Download complete.")

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds_lp_raw = Dataset.from_sdmx_csv(
    path_lp,
    name="Produktivita práce/h",
    unit="PPS EU27=100",
    source_url="Eurostat/nama_10_lp_ulc",
)

raw_net = pd.read_csv(path_net)
raw_net = raw_net[["geo", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
raw_net.columns = ["geo", "time", "value"]
raw_net["time"] = raw_net["time"].astype(int)
ds_net_raw = Dataset(
    raw_net,
    name="Čistý příjem (PPS)",
    unit="EUR PPS/rok",
    source_url="Eurostat/earn_nt_net",
)

# ── 3. Normalise both series to EU27=100 per year ────────────────────────────

def _to_eu100(ds: Dataset, eu_geo: str = "EU27_2020") -> Dataset:
    """Normalise every country–year observation to EU27 aggregate = 100."""
    df = ds.df.copy()
    eu_rows = df[df[ds.geo_col] == eu_geo]
    if not eu_rows.empty:
        eu_series = eu_rows.groupby(ds.time_col)[ds.value_col].mean().rename("_eu")
    else:
        # Compute EU mean from EU27 members present in the dataset
        eu_members = EU27 & set(df[ds.geo_col].unique())
        eu_series = (
            df[df[ds.geo_col].isin(eu_members)]
            .groupby(ds.time_col)[ds.value_col]
            .mean()
            .rename("_eu")
        )
    df = df.merge(eu_series, on=ds.time_col, how="left")
    df[ds.value_col] = df[ds.value_col] / df["_eu"] * 100
    df = df.drop(columns=["_eu"]).dropna(subset=[ds.value_col])
    df = df[df[ds.geo_col] != eu_geo]
    return Dataset(
        df,
        name=ds.name, unit="EU27=100",
        geo_col=ds.geo_col, time_col=ds.time_col, value_col=ds.value_col,
        source_url=ds.source_url,
    )


ds_lp_idx = _to_eu100(ds_lp_raw)
ds_net_idx = _to_eu100(ds_net_raw)

# Remove outliers
ds_lp_idx.df = ds_lp_idx.df[~ds_lp_idx.df[ds_lp_idx.geo_col].isin(EXCLUDE_OUTLIERS)].copy()
ds_net_idx.df = ds_net_idx.df[~ds_net_idx.df[ds_net_idx.geo_col].isin(EXCLUDE_OUTLIERS)].copy()

lp_years = sorted(ds_lp_idx.years)
net_years = sorted(ds_net_idx.years)
print(
    f"LP: {lp_years[0]}–{lp_years[-1]}  |  "
    f"Net income: {net_years[0] if net_years else 'n/a'}–"
    f"{net_years[-1] if net_years else 'n/a'}"
)

# ── 4. Build pivot tables ─────────────────────────────────────────────────────
lp_pivot = ds_lp_idx.df.pivot_table(
    index=ds_lp_idx.time_col, columns=ds_lp_idx.geo_col,
    values=ds_lp_idx.value_col, aggfunc="mean"
)
net_pivot = ds_net_idx.df.pivot_table(
    index=ds_net_idx.time_col, columns=ds_net_idx.geo_col,
    values=ds_net_idx.value_col, aggfunc="mean"
)

# ── 5. Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=cm2in(15, 9))

# --- EU grey cloud (LP/h only, for all EU27 except our 6 + outliers) ---
eu_bg = EU27 - set(COUNTRIES) - EXCLUDE_OUTLIERS
for geo in eu_bg:
    if geo in lp_pivot.columns:
        s = lp_pivot[geo].dropna()
        ax.plot(s.index, s.values, color="#C8C8C8", linewidth=0.5, alpha=0.5, zorder=1)

# --- 6 countries: solid = LP/h, dashed = net income ---
for geo in COUNTRIES:
    color = COUNTRY_COLORS.get(geo, "#999999")
    if geo in lp_pivot.columns:
        s_lp = lp_pivot[geo].dropna()
        ax.plot(s_lp.index, s_lp.values,
                color=color, linewidth=2.0, linestyle="-", zorder=3)
        if not s_lp.empty:
            ax.annotate(geo, xy=(s_lp.index[-1], s_lp.iloc[-1]),
                        xytext=(4, 5) if geo == "SK" else (4, 0),
                        textcoords="offset points",
                        fontsize=FONT_SIZE, color=color, va="center")
    if geo in net_pivot.columns:
        s_net = net_pivot[geo].dropna()
        ax.plot(s_net.index, s_net.values,
                color=color, linewidth=1.5, linestyle="--", zorder=3)

# EU27=100 reference line
ax.axhline(100, color="#555555", linewidth=0.8, linestyle=":", alpha=0.7, zorder=2)
ax.text(START_YEAR + 0.3, 101.5, "EU27\u00a0=\u00a0100",
        fontsize=FONT_SIZE - 1, color="#555555", alpha=0.8, va="bottom")

# ── 6. Axes styling ───────────────────────────────────────────────────────────
ax.set_xlabel("rok")
ax.set_ylabel("index (EU27 = 100) [%]")
ax.set_title(
    "Konvergence produktivity práce a čistého disponibilního příjmu (obě v PPS)"
)
ax.set_xlim(START_YEAR, lp_years[-1])

# Integer major ticks + minor grid
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x)}"))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax.grid(which="major", linewidth=0.4, alpha=0.5, color="#AAAAAA", zorder=0)
ax.grid(which="minor", linewidth=0.2, alpha=0.35, color="#DDDDDD", zorder=0)

# ── 7. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "wage_gdp_convergence", out_dir=LATEX_PICS_DIR)

# ── 8. Write LaTeX snippet ────────────────────────────────────────────────────
last_year = lp_years[-1]
save_figure_tex(
    "wage_gdp_convergence",
    caption=(
        "Konvergence k~průměru EU27: reálná produktivita práce na odpracovanou hodinu "
        "(plná čára, Eurostat/\\texttt{nama\\_10\\_lp\\_ulc}, kód \\texttt{NLPR\\_HW}) "
        "a roční čistý disponibilní příjem pracovníka při 100\\,\\% prům.~mzdy "
        "(přerušovaná, Eurostat/\\texttt{earn\\_nt\\_net}), "
        "obě řady v~PPS na srovnatelné ceny, normováno na EU27\\,=\\,100. "
        f"Šedé linie = ostatní země EU27 (pouze produktivita). "
        f"{START_YEAR}--{last_year}."
    ),
    label="fig:wage_gdp_convergence",
    width=r"0.95\linewidth",
    cite_key="eurostat_nama_10_lp_ulc_NLPR_HW_EU27eq100,eurostat_earn_nt_net_PPS_AW100",
)

print("Done.")
