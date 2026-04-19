r"""
Correlation analyses – CB coverage vs labour-market outcomes.

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
from stattool.style import apply_style, cm2in, savefig, save_figure_tex
from statout.scatter import scatter_xy
from statout.timeline import EU27
from analyses._shared_data import load_cb_coverage, load_union_density

# ── Parameters ────────────────────────────────────────────────────────────────

HIGHLIGHT_COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK", "SI", "ES"]
START_YEAR = 2004

# Extend COUNTRY_COLORS at runtime for SI/ES (config.py not modified on disk)
COUNTRY_COLORS.update({"SI": "#17becf", "ES": "#e377c2"})  # teal, pink

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

# Avg actual weekly hours worked
path_hours = fetch_eurostat(
    "lfsa_ewhan2",
    "A.TOTAL.EMP.TOTAL.Y15-64.T.HR.",
    start_period=START_YEAR,
)

# Net annual earnings (PPS) – single person, no children, 100% AW
path_net = fetch_eurostat(
    "earn_nt_net",
    "A.PPS.NET.P1_NCH_AW100.",
    start_period=START_YEAR,
)

# Gender pay gap (%) – total economy B-S_X_O
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
        year_tolerance=9,
    )
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
savefig(fig_all, "korelace_scatter", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "korelace_scatter",
    caption="Korelace pokrytí KV a veličin trhu práce, EU27.",
    label="fig:korelace_scatter",
    width=r"0.98\linewidth",
    cite_keys=["oecd_aias_ictwss_CBC_ERB_pct", "eurostat_lfsa_ewhan2_HR_weekly",
               "eurostat_gpg", "eurostat_earn_nt_net_PPS_AW100",
               "eurostat_nama_10_lp_ulc_NLPR_HW_EU27eq100"],
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
        "y_name": "Prům. skut. hodin./týden",
    },
    {
        "label": r"Pokrytí KV vs. gender pay gap",
        "ds_x": ds_cbc,
        "ds_y": ds_gpg,
        "y_name": "GPG (%)",
    },
    {
        "label": r"Pokrytí KV vs. hod. příjem (PPS/h)",
        "ds_x": ds_cbc,
        "ds_y": ds_netpps,
        "y_name": "Čistý příjem (PPS/h)",
    },
    {
        "label": r"Pokrytí KV vs. produktivita (PPS/h)",
        "ds_x": ds_cbc,
        "ds_y": ds_prod,
        "y_name": "Produktivita (EU27=100)",
    },
    {
        "label": r"Hustota odborů vs. Gini",
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
    # Diagnostic: Pearson–Spearman divergence
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
    return "–" if pd.isna(r) else f"{r:.3f}"

# Determine the single "latest year" label for the header
_years = [row["year"] for row in rows if row["year"]]
from collections import Counter as _Counter
_year_label = max(_Counter(_years), key=lambda y: (_Counter(_years)[y], y)) if _years else "akt."

lines = [
    r"\begin{table}[htbp]",
    r"\centering",
    r"\caption{Korelace pokrytí KV a hustoty odborů s~vybranými veličinami pracovního trhu "
    r"(Pearsonovo $r$ a Spearmanovo $\rho$; panelový koeficient na všech dostupných "
    r"geo$\times$rok pozorováních, $r_{\text{akt.}}$ = průřezový Pearsonův $r$ pro rok "
    rf"{_year_label}).}}",
    r"\label{tab:korelace_tabulka}",
    r"\begin{tabular}{lrrrrrr}",
    r"\toprule",
    rf"Vztah & $n_{{\text{{panel}}}}$ & $n_{{\text{{geo}}}}$ & Pearson $r$ & "
    rf"Spearman $\rho$ & $r_{{\text{{akt.}}}}$ ({_year_label}) & $n_{{\text{{akt.}}}}$ \\",
    r"\midrule",
]
for row in rows:
    lines.append(
        f"{row['label']} & {row['n_panel']} & {row['n_geo']} & "
        f"{_fmt_r(row['r_pearson'])} & "
        f"{_fmt_r(row['r_spearman'])} & "
        f"{_fmt_r(row['r_year'])} & {row['n_akt']} \\\\"
    )
lines += [
    r"\bottomrule",
    r"\end{tabular}",
    rf"\par\vspace{{2pt}}\footnotesize {_EXCL_NOTE}",
    r"\end{table}",
]

tex_dir = Path(LATEX_TEXPARTS_DIR)
tex_dir.mkdir(parents=True, exist_ok=True)
table_path = tex_dir / "korelace_tabulka.tex"
table_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Correlation table written to {table_path}")

print("Done.")
