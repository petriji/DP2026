r"""
Correlation analyses -- CB coverage vs labour-market outcomes.

Produces a combined 2×2 scatter figure (latest available year) and a
correlation table (Pearson r and Spearman ρ).

Combined scatter (CB coverage on x, x_min=0, 8 countries highlighted):
  (a) CB coverage vs avg actual weekly hours worked
  (b) CB coverage vs gender pay gap (%)
  (c) CB coverage vs net hourly earnings (PPS/h)
  (d) CB coverage vs labour productivity per hour (PPS, EU27=100)

Correlation table (LaTeX):
  • Panel correlation: Pearson r + Spearman ρ on all geo×year observations
  • Cross-section: Pearson r for the latest available year only
  • 5th row: union density vs Gini (no figure, table only)

Data sources:
  CB coverage (%):            ICTWSS AdjCov + OECD CBC ERB (DE, SK)
  Avg actual weekly hours:    Eurostat lfsa_ewhan2
  Net annual earnings (PPS):  Eurostat earn_nt_net  (divided by hours×52.18
                              to get hourly rate)
  Gender pay gap (%):         Eurostat earn_gr_gpgr2
  Labour productivity (PPS/h): Eurostat nama_10_lp_ulc
  Income Gini:                Eurostat ilc_di12
  Union density (%):          OECD AIAS ICTWSS TUD

Output
------
  pics/python/korelace_scatter.pdf
  latex/texparts/python/korelace_scatter.tex
  latex/texparts/python/korelace_tabulka.tex

Run
---
    python analyses/correlation_analyses.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import pandas as pd

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR, LATEX_TEXPARTS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import cm2in, apply_style_pgf, savefig_pgf, save_figure_tex_pgf, add_pgf_tooltips_scatter
from statout.scatter import scatter_xy
from statout.timeline import EU27
from analyses._shared_data import load_cb_coverage, load_union_density

# ── Parameters ────────────────────────────────────────────────────────────────

HIGHLIGHT_COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK", "IT", "SE"]
START_YEAR = 2004

# Extend COUNTRY_COLORS at runtime for IT/SE (config.py not modified on disk)
COUNTRY_COLORS.update({"IT": "#17becf", "SE": "#e377c2"})  # teal, pink

# Ireland is excluded from all analyses: its GDP/cap (EU27=100 ≈ 237) is heavily
# distorted by large multinationals domiciled in IE for EU tax purposes (transfer
# pricing, IP relocation), making it a statistical outlier unrepresentative of
# actual living standards or labour-market conditions.
EXCLUDE_COUNTRIES = ["IE"]

# Footnote used in figure/table captions explaining excluded and missing countries.
# (Detailed rationale for IE exclusion and ICTWSS gaps lives in the commentary file.)
_EXCL_NOTE_FIG = (
    "Irsko (IE) vyřazeno (\\acs{HDP}/ob. silně zkresleno transfer pricing). "
    "Data pokrytí \\acs{KV} nedostupná: EE, LV, LU."
)
_EXCL_NOTE_TAB = (
    "Srovnáno dle kupní síly. Irsko (IE) vyřazeno. "
    "Data pokrytí \\acs{KV} nedostupná: EE, LV, LU."
)
# Backward-compat alias (still referenced in scatter footnote below).
_EXCL_NOTE = _EXCL_NOTE_FIG

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
print("Downloading data …")

# Avg actual weekly hours worked
path_hours = fetch_eurostat(
    "lfsa_ewhan2",
    "A.TOTAL.EMP.TOTAL.Y15-64.T.HR.",
    start_period=START_YEAR,
)

# Net annual earnings (PPS) -- single person, no children, 100% AW
path_net = fetch_eurostat(
    "earn_nt_net",
    "A.PPS.NET.P1_NCH_AW100.",
    start_period=START_YEAR,
)

# Gender pay gap (%) -- total economy B-S_X_O
path_gpg = fetch_eurostat(
    "earn_gr_gpgr2",
    "A.PC.B-S_X_O.",
    start_period=START_YEAR,
)

# Income Gini
path_gini = fetch_eurostat(
    "ilc_di12",
    "A.TOTAL.GINI_HND.",
    start_period=START_YEAR,
)

# Labour productivity per hour worked (PPS, EU27=100)
path_prod = fetch_eurostat(
    "nama_10_lp_ulc",
    "A.PC_EU27_2020_MPPS_CP.NLPR_HW.",
    start_period=START_YEAR,
)

print("Download complete.")

# ── 2. Parse ──────────────────────────────────────────────────────────────────

# CB coverage (shared helper: ICTWSS AdjCov + OECD CBC ERB for DE, SK)
print("Loading CB coverage …")
ds_cbc = load_cb_coverage(start_period=START_YEAR)

ds_hours = Dataset.from_sdmx_csv(
    path_hours,
    name="Průměrná skutečná týdenní pracovní doba",
    unit="h/týden",
    source_url="Eurostat/lfsa_ewhan2",
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

ds_tud = load_union_density(start_period=START_YEAR)

# Gender pay gap (%)
ds_gpg = Dataset.from_sdmx_csv(
    path_gpg,
    name="Gender pay gap",
    unit="%",
    source_url="Eurostat/earn_gr_gpgr2",
)

# Labour productivity per hour worked (PPS, EU27=100)
ds_prod = Dataset.from_sdmx_csv(
    path_prod,
    name="Produktivita práce (PPS/h)",
    unit="EU27=100",
    source_url="Eurostat/nama_10_lp_ulc",
)

# ── 3. Compute derived series ─────────────────────────────────────────────────

# Average weeks in a Gregorian year: 365.2425 / 7 ≈ 52.1775, rounded to 52.18
WEEKS_PER_YEAR = 52.18

# Hourly net income = annual PPS / (actual hours/week × weeks/year)
df_net = raw_net.copy()
df_hrs = ds_hours.df[[ds_hours.geo_col, ds_hours.time_col, ds_hours.value_col]].rename(
    columns={ds_hours.geo_col: "geo", ds_hours.time_col: "time", ds_hours.value_col: "hrs"}
)
df_hourly = df_net.merge(df_hrs, on=["geo", "time"])
df_hourly["value"] = df_hourly["net_pps"] / (df_hourly["hrs"] * WEEKS_PER_YEAR)
ds_netpps = Dataset(
    df_hourly[["geo", "time", "value"]],
    name="Čistý hodinový příjem (PPS/h)",
    unit="PPS/h",
    source_url="Eurostat/earn_nt_net + lfsa_ewhan2",
)

# ── 4. Combined 2×2 subplot figure ────────────────────────────────────────────

_SCATTER_SPECS = [
    # Left column: negative correlations
    {
        "name": "coverage_hours",
        "ds_x": ds_cbc,
        "ds_y": ds_hours,
        "xlabel": "pokrytí KV [%]",
        "ylabel": "průměrná skutečná týdenní\npracovní doba [h]",
    },
    # Right column: positive correlations
    {
        "name": "coverage_netincome",
        "ds_x": ds_cbc,
        "ds_y": ds_netpps,
        "xlabel": "pokrytí KV [%]",
        "ylabel": "čistý hodinový příjem [PPS/h]",
    },
    {
        "name": "coverage_gpg",
        "ds_x": ds_cbc,
        "ds_y": ds_gpg,
        "xlabel": "pokrytí KV [%]",
        "ylabel": "gender pay gap [%]",
    },
    {
        "name": "coverage_productivity",
        "ds_x": ds_cbc,
        "ds_y": ds_prod,
        "xlabel": "pokrytí KV [%]",
        "ylabel": "produktivita práce [PPS/h, EU27 = 100]",
    },
]

EU27_LIST = sorted(c for c in EU27 if c not in EXCLUDE_COUNTRIES)

print("Plotting combined scatter figure (2×2) …")

_SUBCAPTIONS = ["(a)", "(b)", "(c)", "(d)"]

STRINGS = {
    "title": r"Korelace pokrytí \acs{KV} s\,vybranými ukazateli trhu práce (2024)",
}
fig_all, axes = plt.subplots(2, 2, figsize=cm2in(16, 16), sharex=True)
fig_all.suptitle(
    STRINGS["title"],
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
        year_tolerance=9,
    )
    # ── PGF tooltips & geo labels (───────────────────────────────────────────
    add_pgf_tooltips_scatter(
        ax, fig_all._scatter_merged,
        fmt_x="{:.1f}", fmt_y="{:.1f}",
        label_x=spec["xlabel"].replace("\n", " "),
        label_y=spec["ylabel"].replace("\n", " "),
    )
    for _schild in ax.get_children():
        if hasattr(_schild, "get_text"):
            _stxt = _schild.get_text().strip()
            if _stxt in HIGHLIGHT_COUNTRIES:
                _schild.set_text(f"\\acs{{geo-{_stxt}}}")
    # Subcaption label
    ax.text(
        0.03, 0.97, _SUBCAPTIONS[idx],
        transform=ax.transAxes,
        fontsize=max(FONT_SIZE, 10), fontweight="bold",
        va="top", ha="left",
    )
    # Hide x-axis tick labels for top row
    if not row_bottom:
        ax.tick_params(labelbottom=False)
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
savefig_pgf(fig_all, "korelace_scatter", strings=STRINGS)
save_figure_tex_pgf(
    "korelace_scatter",
    caption=r"Korelace pokrytí \acs{KV} a~veličin trhu práce, \acs{EU}, 2024.",
    label="fig:korelace_scatter",
    resizebox_width=r"\linewidth",
    cite_keys=["oecd_aias_ictwss_CBC_ERB_pct", "eurostat_lfsa_ewhan2_HR_weekly",
               "eurostat_gpg", "eurostat_earn_nt_net_PPS_AW100",
               "eurostat_nama_10_lp_ulc_NLPR_HW_EU27eq100"],
    strings=STRINGS,
)
print("  saved scatter_combined")

# ── 5. Correlation table ──────────────────────────────────────────────────────
print("Computing correlation table …")

_PAIRS = [
    {
        "label": r"Skut. prac.~doba",
        "ds_x": ds_cbc,
        "ds_y": ds_hours,
        "y_name": "Prům. skut. hodin./týden",
    },
    {
        "label": r"Gender pay gap",
        "ds_x": ds_cbc,
        "ds_y": ds_gpg,
        "y_name": "GPG (%)",
    },
    {
        "label": r"Čistý hod. příjem",
        "ds_x": ds_cbc,
        "ds_y": ds_netpps,
        "y_name": "Čistý příjem (PPS/h)",
    },
    {
        "label": r"Produktivita",
        "ds_x": ds_cbc,
        "ds_y": ds_prod,
        "y_name": "Produktivita (EU27=100)",
    },
    {
        "label": r"Gini ($\acs{var-rho}_{\acs{idx-U}}$)",
        "ds_x": ds_tud,
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


def _corr_for_latest_year(ds_x: Dataset, ds_y: Dataset) -> tuple[float, int, int]:
    """Return (Pearson r, year, n_countries) for the latest common year."""
    df_x = ds_x.df[[ds_x.geo_col, ds_x.time_col, ds_x.value_col]].rename(
        columns={ds_x.geo_col: "geo", ds_x.time_col: "time", ds_x.value_col: "x"}
    )
    df_y = ds_y.df[[ds_y.geo_col, ds_y.time_col, ds_y.value_col]].rename(
        columns={ds_y.geo_col: "geo", ds_y.time_col: "time", ds_y.value_col: "y"}
    )
    common_years = sorted(set(df_x["time"]) & set(df_y["time"]))
    if not common_years:
        return float("nan"), 0, 0
    yr = int(max(common_years))
    merged = (
        df_x[df_x["time"] == yr]
        .merge(df_y[df_y["time"] == yr], on="geo")
        .dropna(subset=["x", "y"])
    )
    merged = merged[~merged["geo"].isin(EXCLUDE_COUNTRIES)]
    if len(merged) < 3:
        return float("nan"), yr, len(merged)
    return float(merged["x"].corr(merged["y"], method="pearson")), yr, len(merged)


rows = []
for pair in _PAIRS:
    merged = _merge_for_corr(pair["ds_x"], pair["ds_y"])
    n_panel = len(merged)
    n_geo = int(merged["geo"].nunique())
    if n_panel < 5:
        r_pearson, r_spearman = float("nan"), float("nan")
    else:
        r_pearson = merged["x"].corr(merged["y"], method="pearson")
        # Spearman = Pearson on ranked variables (no scipy dependency)
        rx = merged["x"].rank(method="average")
        ry = merged["y"].rank(method="average")
        r_spearman = rx.corr(ry, method="pearson")
    r_yr, yr, n_akt = _corr_for_latest_year(pair["ds_x"], pair["ds_y"])
    # Diagnostic: Pearson--Spearman divergence
    if not (pd.isna(r_pearson) or pd.isna(r_spearman)) and abs(r_pearson - r_spearman) > 0.12:
        print(f"  WARNING: |r − ρ| = {abs(r_pearson - r_spearman):.3f} for {pair['label']}")
    rows.append({
        "label": pair["label"],
        "y_name": pair["y_name"],
        "n_panel": n_panel,
        "n_geo": n_geo,
        "r_pearson": r_pearson,
        "r_spearman": r_spearman,
        "r_year": r_yr,
        "year": yr,
        "n_akt": n_akt,
    })

# Build LaTeX table
def _fmt_r(r: float) -> str:
    return "--" if pd.isna(r) else f"{r:.3f}"

# Determine the single "latest year" label for the header
_years = [row["year"] for row in rows if row["year"]]
from collections import Counter as _Counter
_year_label = max(_Counter(_years), key=lambda y: (_Counter(_years)[y], y)) if _years else "akt."

lines = [
    r"\begin{table}[htbp]",
    r"\centering",
    r"\caption{Korelace pokrytí \acs{KV} (hustoty odborů) s~vybranými veličinami "
    rf"pracovního trhu v~letech {START_YEAR}--{_year_label} a průřezovém roce "
    rf"{_year_label}. "
    r"Zdroj dat: Eurostat~\cite{eurostat_lfsa_ewhan2_HR_weekly}\cite{eurostat_gpg}"
    r"\cite{eurostat_earn_nt_net_PPS_AW100}\cite{eurostat_nama_10_lp_ulc_NLPR_HW_EU27eq100}"
    r"\cite{eurostat_ilc_di12}; \acs{OECD}~\acs{ICTWSS}~\cite{oecd_aias_ictwss_CBC_ERB_pct}"
    r"\cite{oecd_aias_ictwss_TUD_pct}; ETUI~\cite{etui_cba}.}",
    r"\label{tab:korelace_tabulka}",
    r"\begin{xltabular}{\linewidth}{@{}>{\raggedright\arraybackslash}p{4cm}"
    r"*{6}{>{\centering\arraybackslash}m{1.5cm}}@{}}",
    r"\toprule",
    rf"\bfseries Ukazatel & \bfseries $n_{{\text{{panel}}}}$ "
    rf"& \bfseries $n_{{\text{{geo}}}}$ & \bfseries $r$ & "
    rf"\bfseries $\rho$ & \bfseries $n_{{\text{{{_year_label}}}}}$ "
    rf"& \bfseries $r_{{\text{{{_year_label}}}}}$ \\",
    r"\midrule",
]
for row in rows:
    lines.append(
        f"{row['label']} & {row['n_panel']} & {row['n_geo']} & "
        f"{_fmt_r(row['r_pearson'])} & "
        f"{_fmt_r(row['r_spearman'])} & "
        f"{row['n_akt']} & {_fmt_r(row['r_year'])} \\\\"
    )
lines += [
    r"\bottomrule",
    r"\end{xltabular}",
    rf"\par\vspace{{2pt}}\footnotesize {_EXCL_NOTE_TAB}",
    r"\end{table}",
]

tex_dir = Path(LATEX_TEXPARTS_DIR)
tex_dir.mkdir(parents=True, exist_ok=True)
table_path = tex_dir / "korelace_tabulka.tex"
table_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Correlation table written to {table_path}")

# ── 6. Prediction table: CZ at 80 % coverage ──────────────────────────────────
print("Generating prediction table for CZ …")

TARGET_COVERAGE = 80.0

# Current CZ coverage (latest available year)
_cbc_cz = ds_cbc.df[ds_cbc.df[ds_cbc.geo_col] == "CZ"].dropna(subset=[ds_cbc.value_col])
_cz_cov_val = float(_cbc_cz.sort_values(ds_cbc.time_col)[ds_cbc.value_col].iloc[-1])
_cz_cov_year = int(_cbc_cz.sort_values(ds_cbc.time_col)[ds_cbc.time_col].iloc[-1])
_delta_x = TARGET_COVERAGE - _cz_cov_val


def _get_cz_latest(ds: "Dataset") -> tuple[float, int]:
    """Return (value, year) for CZ in the latest available year of dataset ds."""
    df_cz = ds.df[ds.df[ds.geo_col] == "CZ"].dropna(subset=[ds.value_col])
    if df_cz.empty:
        return float("nan"), 0
    row = df_cz.sort_values(ds.time_col).iloc[-1]
    return float(row[ds.value_col]), int(row[ds.time_col])


def _ols_beta(ds_x: "Dataset", ds_y: "Dataset") -> float:
    """OLS slope β̂ = Cov(x,y) / Var(x) on the full panel (excluding EXCLUDE_COUNTRIES)."""
    df_x = ds_x.df[[ds_x.geo_col, ds_x.time_col, ds_x.value_col]].rename(
        columns={ds_x.geo_col: "geo", ds_x.time_col: "time", ds_x.value_col: "x"}
    )
    df_y = ds_y.df[[ds_y.geo_col, ds_y.time_col, ds_y.value_col]].rename(
        columns={ds_y.geo_col: "geo", ds_y.time_col: "time", ds_y.value_col: "y"}
    )
    merged = (
        df_x.merge(df_y, on=["geo", "time"], how="inner")
        .dropna(subset=["x", "y"])
    )
    merged = merged[~merged["geo"].isin(EXCLUDE_COUNTRIES)]
    if len(merged) < 5:
        return float("nan")
    xm = merged["x"].mean()
    ym = merged["y"].mean()
    cov_xy = ((merged["x"] - xm) * (merged["y"] - ym)).sum()
    var_x = ((merged["x"] - xm) ** 2).sum()
    return float(cov_xy / var_x) if var_x > 0 else float("nan")


# Only coverage-vs-outcome pairs (first 4 in _PAIRS)
_PRED_SPECS = [
    {
        "label": r"Průměrná skut.~prac.~doba",
        "unit": r"\si{\hour\per\week}",
        "ds_y": ds_hours,
    },
    {
        "label": r"Gender pay gap",
        "unit": r"\si{\percent}",
        "ds_y": ds_gpg,
    },
    {
        "label": r"Čistý hod.~příjem",
        "unit": r"\si{\pps\per\hour}",
        "ds_y": ds_netpps,
    },
    {
        "label": r"Produktivita práce (EU27\,=\,100)",
        "unit": r"\si{\percent}",
        "ds_y": ds_prod,
    },
]

pred_rows = []
for spec in _PRED_SPECS:
    beta = _ols_beta(ds_cbc, spec["ds_y"])
    y0, y0_year = _get_cz_latest(spec["ds_y"])
    delta_y = beta * _delta_x if not (pd.isna(beta) or pd.isna(y0)) else float("nan")
    y1 = y0 + delta_y if not pd.isna(delta_y) else float("nan")
    pred_rows.append({
        "label": spec["label"],
        "unit": spec["unit"],
        "y0": y0,
        "y0_year": y0_year,
        "beta": beta,
        "delta_y": delta_y,
        "y1": y1,
    })


def _fmt_pred(v: float, sign: bool = False) -> str:
    if pd.isna(v):
        return "--"
    if sign and v > 0:
        return f"$+{v:.3g}$".replace(".", "{,}")
    return f"${v:.3g}$".replace(".", "{,}")


def _fmt_pred_beta(v: float) -> str:
    if pd.isna(v):
        return "--"
    sign = "+" if v >= 0 else ""
    return f"${sign}{v:.3f}$".replace(".", "{,}")


_cz_cov_str = f"{_cz_cov_val:.1f}".replace(".", "{,}")
_delta_x_str = f"{_delta_x:.1f}".replace(".", "{,}")
_target_str = f"{TARGET_COVERAGE:.0f}"
_max_year = max(r["y0_year"] for r in pred_rows)

pred_lines = [
    r"\begin{table}[htbp]",
    r"\centering",
    rf"\caption{{Lineární predikce: predikovaná změna ukazatelů trhu práce "
    rf"\aca{{geo-CZ}} při nárůstu pokrytí \ac{{KV}} ze "
    rf"\SI{{{_cz_cov_str}}}{{\percent}} na~\SI{{{_target_str}}}{{\percent}}.}}",
    r"\label{tab:model_cz}",
    r"\begin{xltabular}{\linewidth}{@{}>{\raggedright\arraybackslash}p{8cm}"
    r"*{4}{>{\centering\arraybackslash}m{1.65cm}}@{}}",
    r"\toprule",
    rf"\bfseries Ukazatel & \bfseries $y_{{{_max_year}}}$ "
    r"& \bfseries $\hat{\beta}$ (na \SI{}{\pp}) "
    r"& \bfseries $\Delta\hat{y}_{\acs{geo-CZ}}$ "
    r"& \bfseries $\hat{y}$ \\",
    r"\midrule",
]
for r in pred_rows:
    pred_lines.append(
        f"{r['label']} [{r['unit']}] & "
        f"{_fmt_pred(r['y0'])} & "
        f"{_fmt_pred_beta(r['beta'])} & "
        f"{_fmt_pred(r['delta_y'], sign=True)} & "
        f"\\bfseries {_fmt_pred(r['y1'])} \\\\"
    )
pred_lines += [
    r"\bottomrule",
    r"\end{xltabular}",
    r"\par\vspace{2pt}\footnotesize "
    r"Predikce je horním odhadem korelovatelné části efektu --- "
    r"nezachycuje zpětné vazby ani náklady přechodu.",
    r"\end{table}",
]

pred_path = tex_dir / "korelace_model_cz.tex"
pred_path.write_text("\n".join(pred_lines), encoding="utf-8")
print(f"Prediction table written to {pred_path}")

print("Done.")
