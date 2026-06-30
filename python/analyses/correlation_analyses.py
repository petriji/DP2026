r"""
Correlation analyses – CB coverage vs labour-market outcomes.

Produces four scatter plots (latest available year) and a correlation table
(Pearson r and Spearman ρ, using all available historical data).

Scatter figures (CB coverage on x, x_min=0, 6 countries highlighted):
  1. coverage_hours_scatter       – avg weekly hours worked
  2. coverage_netincome_scatter   – net personal income in PPS
  3. coverage_gini_scatter        – income Gini coefficient
  4. coverage_ratio_scatter       – (net income PPS) / (GDP PPS/cap)  [%]

Correlation table (LaTeX):
  • Each pair: Pearson r + Spearman ρ, using all geo×year obs where complete
  • Citation key written into each table caption

Data sources:
  CB coverage (%):            OECD CBC (ERB measure)
  Avg weekly hours (HR):      Eurostat lfsa_ewhun2
    Net income (PPS):           Eurostat earn_nt_net
  GDP PPS/cap:                Eurostat nama_10_pc
  Income Gini:                Eurostat ilc_di12

Output
------
  pics/python/coverage_hours_scatter.pdf
  pics/python/coverage_netincome_scatter.pdf
  pics/python/coverage_gini_scatter.pdf
  pics/python/coverage_ratio_scatter.pdf
  latex/texparts/python/coverage_hours_scatter.tex
  latex/texparts/python/coverage_netincome_scatter.tex
  latex/texparts/python/coverage_gini_scatter.tex
  latex/texparts/python/coverage_ratio_scatter.tex
  latex/texparts/python/coverage_correlation_table.tex

Run
---
    python analyses/correlation_analyses.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import FONT_SIZE, LATEX_PICS_DIR, LATEX_TEXPARTS_DIR
from stattool.fetch import fetch_oecd, fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, cm2in, savefig, save_figure_tex
from statout.scatter import scatter_xy
from statout.timeline import EU27

# ── Parameters ────────────────────────────────────────────────────────────────

HIGHLIGHT_COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2004

# Ireland is excluded from all analyses: its GDP/cap (EU27=100 ≈ 237) is heavily
# distorted by large multinationals domiciled in IE for EU tax purposes (transfer
# pricing, IP relocation), making it a statistical outlier unrepresentative of
# actual living standards or labour-market conditions.
EXCLUDE_COUNTRIES = ["IE"]

# Footnote used in all figure/table captions explaining excluded and missing countries.
_EXCL_NOTE = (
    "Irsko (IE) vyřazeno: HDP/ob.~v~PPS $\\approx 237$ (EU27\\,=\\,100) "
    "je zkresleno přesunem zisků nadnárodních korporací se sídlem v~Irsku "
    "(transfer pricing, relokace~IP) --- nereprezentuje skutečnou životní "
    "úroveň ani podmínky trhu práce. "
    "Data nedostupná: EE, LV --- chybějící hodnoty v~ICTWSS~\\textit{AdjCov}; "
    "LU --- data dostupná pouze před rokem 2004."
)

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
print("Downloading data …")

# CB coverage – all OECD countries
path_cbc = fetch_oecd("CBC", start_period=START_YEAR)

# Avg weekly hours worked
path_hours = fetch_eurostat(
    "lfsa_ewhun2",
    "A.TOTAL.EMP.TOTAL.Y15-64.T.HR.",
    start_period=START_YEAR,
)

# Net annual earnings (PPS) – single person, no children, 100% AW
path_net = fetch_eurostat(
    "earn_nt_net",
    "A.PPS.NET.P1_NCH_AW100.",
    start_period=START_YEAR,
)

# GDP per capita in PPS (EU27_2020 index)
path_gdp = fetch_eurostat(
    "nama_10_pc",
    "A.PC_EU27_2020_HAB_MPPS_CP.B1GQ.",
    start_period=START_YEAR,
)

# Income Gini
path_gini = fetch_eurostat(
    "ilc_di12",
    "A.TOTAL.GINI_HND.",
    start_period=START_YEAR,
)

# Union density – all OECD countries (for union_gini scatter + correlation table)
path_tud = fetch_oecd("TUD", start_period=START_YEAR)

print("Download complete.")

# ── 2. Parse ──────────────────────────────────────────────────────────────────

# CB coverage: AdjCov from ICTWSS CSV (all EU27 exc. DE and SK)
#              + ERB from OECD CBC (DE and SK — AdjCov stalls before 2015/1990)
import csv as _csv, urllib.request as _urllib_req
from io import StringIO as _StringIO
_ICTWSS_URL = "https://webfs.oecd.org/Els-com/ICTWSS-Database/ICTWSS_v2.csv"
_ISO3_TO_ISO2_COR: dict[str, str] = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY",
    "CZE": "CZ", "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR",
    "DEU": "DE", "GRC": "GR", "HUN": "HU", "IRL": "IE", "ITA": "IT",
    "LVA": "LV", "LTU": "LT", "LUX": "LU", "MLT": "MT", "NLD": "NL",
    "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK", "SVN": "SI",
    "ESP": "ES", "SWE": "SE",
}
_EU27_ISO3_COR = set(_ISO3_TO_ISO2_COR.keys())

print("Downloading ICTWSS v2 CSV (AdjCov) …")
_adjcov_rows: list[dict] = []
try:
    with _urllib_req.urlopen(_ICTWSS_URL, timeout=60) as _resp:
        _reader = _csv.DictReader(_StringIO(_resp.read().decode("utf-8-sig")))
        for _r in _reader:
            _iso3 = _r.get("iso3", "").strip().upper()
            _iso2 = _ISO3_TO_ISO2_COR.get(_iso3)
            if not _iso2 or _iso2 in ("DE", "SK"):
                continue
            _val = _r.get("AdjCov", "").strip()
            _yr  = _r.get("year", "").strip()
            if _val and _yr:
                _adjcov_rows.append({"geo": _iso2, "time": int(_yr), "value": float(_val)})
except Exception as _e:
    print(f"  WARNING: ICTWSS AdjCov unavailable ({_e}) — CBC ERB used for all countries")

_df_adjcov = pd.DataFrame(_adjcov_rows) if _adjcov_rows else pd.DataFrame(columns=["geo","time","value"])
if not _df_adjcov.empty:
    _df_adjcov = _df_adjcov[_df_adjcov["time"] >= START_YEAR]
print(f"  AdjCov: {_df_adjcov['geo'].nunique()} EU27 countries (exc. DE, SK), "
      f"years {_df_adjcov['time'].min() if not _df_adjcov.empty else '?'}–"
      f"{_df_adjcov['time'].max() if not _df_adjcov.empty else '?'}")

# ERB from OECD CBC for DE and SK
ds_cbc_erb = Dataset.from_oecd_csv(
    path_cbc,
    name="Pokrytí KV (ERB)",
    unit="%",
    source_url="OECD AIAS ICTWSS / CBC",
    filters={"MEASURE": "ERB"},
)
_df_erb = ds_cbc_erb.df[ds_cbc_erb.df["geo"].isin(["DE", "SK"])][["geo", "time", "value"]].copy()
print(f"  CBC ERB/DE+SK: years {_df_erb['time'].min() if not _df_erb.empty else '?'}–"
      f"{_df_erb['time'].max() if not _df_erb.empty else '?'}")

ds_cbc = Dataset(
    pd.concat([_df_adjcov, _df_erb], ignore_index=True),
    name="Pokrytí KV",
    unit="%",
    source_url="ICTWSS AdjCov + OECD CBC ERB (DE, SK)",
)

ds_hours = Dataset.from_sdmx_csv(
    path_hours,
    name="Průměrný týdenní pracovní úvazek",
    unit="h/týden",
    source_url="Eurostat/lfsa_ewhun2",
)

ds_gini = Dataset.from_sdmx_csv(
    path_gini,
    name="Giniho koeficient",
    unit="",
    source_url="Eurostat/ilc_di12",
)

raw_net = pd.read_csv(path_net)[["geo", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
raw_net.columns = ["geo", "time", "net_pps"]
raw_net["time"] = raw_net["time"].astype(int)

raw_gdp = pd.read_csv(path_gdp)[["geo", "TIME_PERIOD", "OBS_VALUE"]].dropna(subset=["OBS_VALUE"])
raw_gdp.columns = ["geo", "time", "gdp_pps"]
raw_gdp["time"] = raw_gdp["time"].astype(int)

ds_tud = Dataset.from_oecd_csv(
    path_tud,
    name="Hustota odborů",
    unit="%",
    source_url="OECD AIAS ICTWSS / TUD",
    filters={"INDICATOR": "TUD"},
)

# GDP per capita index (EU27=100) as a standalone dataset for scatter
ds_gdp_idx = Dataset.from_sdmx_csv(
    path_gdp,
    name="HDP na obyvatele (EU27=100)",
    unit="EU27=100",
    source_url="Eurostat/nama_10_pc",
)

# ── 3. Compute derived series ─────────────────────────────────────────────────

# net income is already in PPS
df_net = raw_net.copy()
ds_netpps = Dataset(
    df_net[["geo", "time", "net_pps"]].rename(columns={"net_pps": "value"}),
    name="Čistý příjem (PPS)",
    unit="EUR PPS/rok",
    source_url="Eurostat/earn_nt_net",
)

# ratio = net income PPS / GDP PPS per capita (%)
df_ratio = df_net.merge(raw_gdp, on=["geo", "time"], how="inner")
df_ratio["value"] = df_ratio["net_pps"] / df_ratio["gdp_pps"] * 100.0
ds_ratio = Dataset(
    df_ratio[["geo", "time", "value"]].dropna(),
    name="Čistý příjem / HDP na ob.",
    unit="% HDP/ob.",
    source_url="Eurostat/earn_nt_net, nama_10_pc",
)

# ── 4. Scatter plots ──────────────────────────────────────────────────────────

_SCATTER_SPECS = [
    {
        "name": "coverage_hours_scatter",
        "ds_x": ds_cbc,
        "ds_y": ds_hours,
        "title": "Korelace: pokrytí KV a průměrná pracovní doba",
        "xlabel": "pokrytí kolektivního vyjednávání [%]",
        "ylabel": "průměrná týdenní pracovní doba [h]",
        "caption": "Pokrytí KV a~průměrná pracovní doba, EU27.",
        "label": "fig:coverage_hours_scatter",
        "cite": "oecd_aias_ictwss_CBC_ERB_pct,eurostat_lfsa_ewhun2_HR_weekly",
    },
    {
        "name": "coverage_income_scatter",
        "ds_x": ds_cbc,
        "ds_y": ds_gdp_idx,
        "title": "Korelace: pokrytí KV a HDP na obyvatele v PPS",
        "xlabel": "pokrytí kolektivního vyjednávání [%]",
        "ylabel": "HDP na obyvatele v PPS (EU27 = 100)",
        "caption": "Pokrytí KV a~HDP na obyvatele v~PPS, EU27.",
        "label": "fig:coverage_income_scatter",
        "cite": "oecd_aias_ictwss_CBC_ERB_pct,eurostat_nama_10_pc_PPS_EU27eq100",
    },
    {
        "name": "coverage_gini_scatter",
        "ds_x": ds_cbc,
        "ds_y": ds_gini,
        "title": "Korelace: pokrytí KV a Giniho koeficient",
        "xlabel": "pokrytí kolektivního vyjednávání [%]",
        "ylabel": "Giniho koeficient (disponibilní příjem, 0–100)",
        "caption": "Pokrytí KV a~Giniho koeficient, EU27.",
        "label": "fig:coverage_gini_scatter",
        "cite": "oecd_aias_ictwss_CBC_ERB_pct,eurostat_ilc_di12_Gini",
    },
    {
        "name": "coverage_ratio_scatter",
        "ds_x": ds_cbc,
        "ds_y": ds_ratio,
        "title": "Korelace: pokrytí KV a disponibilní příjem / produktivita (po zdanění a odvod.)",
        "xlabel": "pokrytí kolektivního vyjednávání [%]",
        "ylabel": "disponibilní příjem / produktivita [%]",
        "caption": "Pokrytí KV a~podíl čistého příjmu na HDP, EU27.",
        "label": "fig:coverage_ratio_scatter",
        "cite": "oecd_aias_ictwss_CBC_ERB_pct,eurostat_earn_nt_net_PPS_AW100,eurostat_nama_10_pc_PPS_EU27eq100",
    },
]

EU27_LIST = sorted(c for c in EU27 if c not in EXCLUDE_COUNTRIES)

for spec in _SCATTER_SPECS:
    print(f"Plotting {spec['name']} …")
    fig = scatter_xy(
        spec["ds_x"],
        spec["ds_y"],
        title=spec["title"],
        xlabel=spec["xlabel"],
        ylabel=spec["ylabel"],
        trendline=True,
        label_points=True,
        highlight=HIGHLIGHT_COUNTRIES,
        x_min=0,
        countries=EU27_LIST,
        year_tolerance=8,
    )
    savefig(fig, spec["name"], out_dir=LATEX_PICS_DIR)
    common_years = sorted(set(spec["ds_x"].years) & set(spec["ds_y"].years))
    display_year = common_years[-1] if common_years else "?"
    save_figure_tex(
        spec["name"],
        caption=f"{spec['caption']}\n{display_year}.",
        label=spec["label"],
        width=r"0.85\linewidth",
        cite_key=spec["cite"],
        footnote=_EXCL_NOTE,
    )
    print(f"  saved {spec['name']} ({display_year})")

# ── 4b. Combined 2×2 subplot figure (CB coverage plots only) ─────────────────
print("Plotting combined scatter figure (2×2) …")

_SUBCAPTIONS = ["(a)", "(b)", "(c)", "(d)"]

fig_all, axes = plt.subplots(2, 2, figsize=cm2in(16, 16), sharex=True)
fig_all.suptitle(
    "Korelace pokrytí KV s vybranými ukazateli trhu práce (2024)",
    fontsize=max(FONT_SIZE, 10),
)
for idx, (spec, ax) in enumerate(zip(_SCATTER_SPECS, axes.flat)):
    row_bottom = idx >= 2
    scatter_xy(
        spec["ds_x"],
        spec["ds_y"],
        title="",
        xlabel=spec["xlabel"] if row_bottom else "",
        ylabel=spec["ylabel"],
        trendline=True,
        label_points=True,
        highlight=HIGHLIGHT_COUNTRIES,
        x_min=0,
        ax=ax,
        countries=EU27_LIST,
        year_tolerance=8,
    )
    # Subcaption label in caption style
    ax.text(
        0.03, 0.97, _SUBCAPTIONS[idx],
        transform=ax.transAxes,
        fontsize=max(FONT_SIZE, 10), fontweight="bold",
        va="top", ha="left",
    )
    # Apply "tis." (thousands) formatter where y-values reach 1000+
    import matplotlib.ticker as _ticker
    ax.yaxis.set_major_formatter(
        _ticker.FuncFormatter(
            lambda val, _: f"{val/1000:.0f}\u202ftis." if abs(val) >= 1000 else f"{val:.4g}"
        )
    )
    for item in ax.get_xticklabels() + ax.get_yticklabels():
        item.set_fontsize(max(item.get_fontsize(), 10))
fig_all.tight_layout(pad=1.5, rect=[0, 0, 1, 0.96])
savefig(fig_all, "scatter_combined", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "scatter_combined",
    caption="Korelace pokrytí KV a veličin trhu práce, EU27.",
    label="fig:scatter_combined",
    width=r"0.98\linewidth",
    cite_keys=["oecd_aias_ictwss_CBC_ERB_pct", "eurostat_lfsa_ewhun2_HR_weekly",
               "eurostat_nama_10_pc_PPS_EU27eq100", "eurostat_ilc_di12_Gini",
               "eurostat_earn_nt_net_PPS_AW100"],
    footnote=_EXCL_NOTE,
)
print("  saved scatter_combined")

# ── 5. Correlation table ──────────────────────────────────────────────────────
print("Computing correlation table …")

_PAIRS = [
    {
        "label": r"Pokrytí KV vs. prac.~doba",
        "ds_x": ds_cbc,
        "ds_y": ds_hours,
        "y_name": "Prům. hodin./týden",
    },
    {
        "label": r"Pokrytí KV vs. HDP/ob. (PPS)",
        "ds_x": ds_cbc,
        "ds_y": ds_gdp_idx,
        "y_name": "HDP/ob. (EU27=100)",
    },
    {
        "label": r"Pokrytí KV vs. Gini",
        "ds_x": ds_cbc,
        "ds_y": ds_gini,
        "y_name": "Gini",
    },
    {
        "label": r"Pokrytí KV vs. příjem/HDP",
        "ds_x": ds_cbc,
        "ds_y": ds_ratio,
        "y_name": "Příjem/HDP (\\%)",
    },
    {
        "label": r"Hustota odborů vs. Gini",
        "ds_x": None,   # handled separately (uses TUD from OECD)
        "ds_y": ds_gini,
        "y_name": "Gini",
    },
]


def _merge_for_corr(ds_x: Dataset, ds_y: Dataset) -> pd.DataFrame:
    """Return long DataFrame with columns x, y for all matched geo×year pairs."""
    df_x = ds_x.df[[ds_x.geo_col, ds_x.time_col, ds_x.value_col]].rename(
        columns={ds_x.geo_col: "geo", ds_x.time_col: "time", ds_x.value_col: "x"}
    )
    df_y = ds_y.df[[ds_y.geo_col, ds_y.time_col, ds_y.value_col]].rename(
        columns={ds_y.geo_col: "geo", ds_y.time_col: "time", ds_y.value_col: "y"}
    )
    merged = df_x.merge(df_y, on=["geo", "time"], how="inner").dropna(subset=["x", "y"])
    merged = merged[~merged["geo"].isin(EXCLUDE_COUNTRIES)]
    return merged


def _corr_for_latest_year(ds_x: Dataset, ds_y: Dataset) -> tuple[float, int]:
    """Return (Pearson r, year) for the latest common year between ds_x and ds_y."""
    df_x = ds_x.df[[ds_x.geo_col, ds_x.time_col, ds_x.value_col]].rename(
        columns={ds_x.geo_col: "geo", ds_x.time_col: "time", ds_x.value_col: "x"}
    )
    df_y = ds_y.df[[ds_y.geo_col, ds_y.time_col, ds_y.value_col]].rename(
        columns={ds_y.geo_col: "geo", ds_y.time_col: "time", ds_y.value_col: "y"}
    )
    common_years = sorted(set(df_x["time"]) & set(df_y["time"]))
    if not common_years:
        return float("nan"), 0
    yr = int(max(common_years))
    merged = (
        df_x[df_x["time"] == yr]
        .merge(df_y[df_y["time"] == yr], on="geo")
        .dropna(subset=["x", "y"])
    )
    merged = merged[~merged["geo"].isin(EXCLUDE_COUNTRIES)]
    if len(merged) < 3:
        return float("nan"), yr
    return float(merged["x"].corr(merged["y"], method="pearson")), yr


# ds_tud already fetched and parsed above (used for union_gini_scatter)
_PAIRS[4]["ds_x"] = ds_tud

rows = []
for pair in _PAIRS:
    if pair["ds_x"] is None:
        continue
    merged = _merge_for_corr(pair["ds_x"], pair["ds_y"])
    n = len(merged)
    if n < 5:
        r_pearson, p_pearson, r_spearman = float("nan"), float("nan"), float("nan")
    else:
        r_pearson = merged["x"].corr(merged["y"], method="pearson")
        # Spearman = Pearson on ranked variables (no scipy dependency)
        rx = merged["x"].rank(method="average")
        ry = merged["y"].rank(method="average")
        r_spearman = rx.corr(ry, method="pearson")
        p_pearson = float("nan")
    r_yr, yr = _corr_for_latest_year(pair["ds_x"], pair["ds_y"])
    rows.append({
        "label": pair["label"],
        "y_name": pair["y_name"],
        "n": n,
        "r_pearson": r_pearson,
        "p_pearson": p_pearson,
        "r_spearman": r_spearman,
        "r_year": r_yr,
        "year": yr,
    })

# Build LaTeX table
def _fmt_r(r: float) -> str:
    return "–" if pd.isna(r) else f"{r:.3f}"

def _sig(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""

# Determine the single "latest year" label for the header (use most common year,
# falling back to max year if tied).
_years = [row["year"] for row in rows if row["year"]]
from collections import Counter as _Counter
_year_label = max(_Counter(_years), key=lambda y: (_Counter(_years)[y], y)) if _years else "akt."

lines = [
    r"\begin{table}[htbp]",
    r"\centering",
    r"\caption{Korelace pokrytí KV a hustoty odborů s~vybranými veličinami pracovního trhu "
    r"(Pearsonovo $r$ a Spearmanovo $\rho$, všechna dostupná geo$\times$rok; "
    rf"$r_{{\text{{akt.}}}}$ = Pearsonovo $r$ pro rok {_year_label}).\\footnote{{{_EXCL_NOTE}}}" + "}",
    r"\label{tab:coverage_correlation_table}",
    r"\begin{tabular}{lrrrrr}",
    r"\toprule",
    rf"Vztah & $n$ & Pearson $r$ & $p$ & Spearman $\rho$ & $r_{{\text{{akt.}}}}$ ({_year_label}) \\",
    r"\midrule",
]
for row in rows:
    p_text = "--" if np.isnan(row["p_pearson"]) else f"\\num{{{row['p_pearson']:.3f}}}"
    lines.append(
        f"{row['label']} & {row['n']} & "
        f"{_fmt_r(row['r_pearson'])}{_sig(row['p_pearson'])} & "
        f"{p_text} & "
        f"{_fmt_r(row['r_spearman'])} & "
        f"{_fmt_r(row['r_year'])} \\\\"
    )
lines += [
    r"\bottomrule",
    r"\end{tabular}",
    r"\end{table}",
]

tex_dir = Path(LATEX_TEXPARTS_DIR)
tex_dir.mkdir(parents=True, exist_ok=True)
table_path = tex_dir / "coverage_correlation_table.tex"
table_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Correlation table written to {table_path}")

print("Done.")
