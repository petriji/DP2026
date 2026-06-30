r"""
Strike activity -- % working time lost to strikes, EU grey cloud + selected countries.

Data source: ILOSTAT STR_DAYS_ECO_RT_A; Statistics Denmark ABST1; Eurostat lfsa_ewhun2
Filter: přepočet dní stávek na procento odpracované doby pro ČR, Dánsko a porovnání s ostatními zeměmi (2000--2025)

Output
------
  pics/python/stav_stavky.pdf
  latex/texparts/python/stav_stavky.tex

Run
---
    python analyses/stav_stavky.py
"""

import sys
import logging
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.data_quality import warn_fallback, warn_non_target_year
from stattool.fetch import fetch_ilostat, fetch_eurostat, fetch
from stattool.dataset import Dataset
from stattool.style import apply_style_pgf, savefig_pgf, save_figure_tex_pgf, add_pgf_tooltips
from statout.timeline import timeline, EU27 as _EU27

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ── Parameters ────────────────────────────────────────────────────────────────

# Only countries with sufficiently continuous reporting are shown.
# CZ, SK: all-zero administrative underreporting (not real zero activity).
# AT, NL, EE, LT: coverage ends before 2010 or has a major outlier (LT 2008).
COUNTRIES  = ["DE", "ES", "FI", "FR", "HU", "LV", "PL", "SE", "DK"]
HIGHLIGHT  = ["FR", "DK"]
START_YEAR = 2000
MIN_POINTS = 3          # Countries with fewer data points are excluded from plot

# Average weeks in a Gregorian year: 365.2425 / 7 ≈ 52.1775, rounded to 52.18
WEEKS_PER_YEAR = 52.18

# ILO ISO3 → ISO2 mapping (partial; extended for EU27 + selected)
_ISO3_TO_ISO2: dict[str, str] = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY",
    "CZE": "CZ", "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR",
    "DEU": "DE", "GRC": "GR", "HUN": "HU", "IRL": "IE", "ITA": "IT",
    "LVA": "LV", "LTU": "LT", "LUX": "LU", "MLT": "MT", "NLD": "NL",
    "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK", "SVN": "SI",
    "ESP": "ES", "SWE": "SE",
    # Extra non-EU (kept for potential future use, filtered out below)
    "NOR": "NO", "CHE": "CH", "GBR": "GB", "USA": "US", "JPN": "JP",
    "AUS": "AU", "CAN": "CA", "NZL": "NZ", "KOR": "KR",
}

EU27_ISO3 = {
    "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
    "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
    "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE",
}

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ILOSTAT STR_DAYS_ECO_RT_A ────────────────────────────────────
print("Downloading ILOSTAT STR_DAYS_ECO_RT_A …")
path_ilo = fetch_ilostat(
    "STR_DAYS_ECO_RT_A",
    params={"classif1": "ECO_AGGREGATE_TOTAL", "sex": "SEX_T"},
)
df_ilo = pd.read_csv(path_ilo, low_memory=False)
print(f"  ILO raw: {len(df_ilo):,} rows, columns: {list(df_ilo.columns)}")

# Normalise column names (ILO API returns lower-case)
df_ilo.columns = [c.strip().lower() for c in df_ilo.columns]

# Keep only rows with usable obs_value
obs_col = "obs_value"
if obs_col not in df_ilo.columns:
    # Fallback: try 'value'
    obs_col = "value" if "value" in df_ilo.columns else df_ilo.columns[-1]
    log.warning("obs_value column not found; using '%s'", obs_col)
    warn_fallback(
        f"ILOSTAT strike dataset used fallback value column '{obs_col}' instead of 'obs_value'",
        source="ILOSTAT STR_DAYS_ECO_RT_A",
    )

df_ilo = df_ilo.dropna(subset=[obs_col])
df_ilo[obs_col] = pd.to_numeric(df_ilo[obs_col], errors="coerce")
df_ilo = df_ilo.dropna(subset=[obs_col])

# Map ref_area (ISO3) → ISO2
if "ref_area" not in df_ilo.columns:
    raise ValueError(f"Expected 'ref_area' column, got: {list(df_ilo.columns)}")

df_ilo["geo"] = df_ilo["ref_area"].str.strip().str.upper().map(_ISO3_TO_ISO2)
df_ilo = df_ilo.dropna(subset=["geo"])

# Keep only EU27 countries
df_ilo = df_ilo[df_ilo["ref_area"].str.strip().str.upper().isin(EU27_ISO3)].copy()

# Parse time column (annual: YYYY)
time_col = "time"
if time_col not in df_ilo.columns:
    # sometimes 'ref_period' or 'year'
    for alt in ("ref_period", "year"):
        if alt in df_ilo.columns:
            time_col = alt
            break
df_ilo["time"] = pd.to_numeric(df_ilo[time_col], errors="coerce")
df_ilo = df_ilo.dropna(subset=["time"])
df_ilo["time"] = df_ilo["time"].astype(int)
df_ilo = df_ilo[df_ilo["time"] >= START_YEAR]

df_ilo_clean = df_ilo[["geo", "time", obs_col]].copy()
df_ilo_clean = df_ilo_clean.rename(columns={obs_col: "D_S"})
print(f"  ILO clean: {df_ilo_clean['geo'].nunique()} EU27 countries, "
      f"years {df_ilo_clean['time'].min()}--{df_ilo_clean['time'].max()}")
warn_non_target_year(
    source="ILOSTAT STR_DAYS_ECO_RT_A",
    year=int(df_ilo_clean["time"].max()) if not df_ilo_clean.empty else None,
    context="Strike-activity timeline latest available ILO year",
)

# ── 1b. Statistics Denmark ABST1 -- lost working days + employment for DK ────────────────
# ABST1: unit 300 = "Number of lost working days", BRANCHE 000 = Total
# API: https://api.statbank.dk/v1/data/ABST1/CSV?lang=en
print("Downloading Statistics Denmark ABST1 (DK lost working days) …")
path_dk_days = fetch(
    "https://api.statbank.dk/v1/data/ABST1/CSV"
    "?lang=en&ENHED=300&BRANCHE=000&Tid=*",
    suffix=".csv",
)
df_dk_days = pd.read_csv(path_dk_days, sep=";", low_memory=False)
df_dk_days.columns = [c.strip().upper() for c in df_dk_days.columns]
# Expected columns: ENHED, BRANCHE, TID, INDHOLD
time_col_dk  = next((c for c in df_dk_days.columns if c in ("TID", "YEAR", "TIME")), None)
value_col_dk = next((c for c in df_dk_days.columns if c in ("INDHOLD", "VALUE", "OBS_VALUE")), None)
if not time_col_dk or not value_col_dk:
    raise ValueError(f"Unexpected ABST1 columns: {list(df_dk_days.columns)}")
df_dk_days = df_dk_days[[time_col_dk, value_col_dk]].copy()
df_dk_days.columns = ["time", "lost_days"]
df_dk_days["time"] = pd.to_numeric(df_dk_days["time"], errors="coerce")
df_dk_days["lost_days"] = pd.to_numeric(
    df_dk_days["lost_days"].astype(str).str.replace("\xa0", "").str.replace(" ", "").str.replace(",", "."),
    errors="coerce",
)
df_dk_days = df_dk_days.dropna().astype({"time": int})
df_dk_days = df_dk_days[df_dk_days["time"] >= START_YEAR]
print(f"  ABST1 raw: {len(df_dk_days)} years, {df_dk_days['time'].min()}--{df_dk_days['time'].max()}")

# Eurostat employment (total employed, thousands) for DK to compute rate per 1000
print("Downloading Eurostat lfsi_emp_a for DK employment …")
path_dk_emp = fetch_eurostat(
    "lfsi_emp_a",
    "A.EMP_LFS.T.Y20-64.THS_PER.DK",
    start_period=START_YEAR,
)
ds_dk_emp = Dataset.from_sdmx_csv(
    path_dk_emp,
    name="Zaměstnanost DK",
    unit="tis. osob",
    source_url="Eurostat/lfsi_emp_a",
)
df_dk_emp = ds_dk_emp.df[["time", "value"]].copy()
df_dk_emp = df_dk_emp.rename(columns={"value": "emp_thousands"})

# Merge and compute D_S_dk = lost_days / (emp_thousands * 1000) * 1000
#   = lost_days / emp_thousands  (per 1000 workers)
df_dk = df_dk_days.merge(df_dk_emp, on="time", how="inner")
df_dk["D_S"] = df_dk["lost_days"] / df_dk["emp_thousands"]
df_dk["geo"] = "DK"
df_dk = df_dk[["geo", "time", "D_S"]]
print(f"  DK computed: {len(df_dk)} years, D_S range "
      f"{df_dk['D_S'].min():.4f}--{df_dk['D_S'].max():.4f} days/1000")

# Merge DK into ILO frame (ILO doesn't report DK)
df_ilo_clean = pd.concat([df_ilo_clean, df_dk], ignore_index=True)
print(f"  After DK merge: {df_ilo_clean['geo'].nunique()} countries")

# ── 2. Download Eurostat lfsa_ewhun2 -- average weekly hours ──────────────────
# Dimension order: freq.unit.worktime.sex.age.geo
# We want: A (annual), TOTAL (worktime=total), T (sex), Y20-64 (age)
print("Downloading Eurostat lfsa_ewhun2 (average weekly hours) …")
path_hours = fetch_eurostat(
    "lfsa_ewhun2",
    "A.TOTAL.EMP.TOTAL.Y15-64.T.HR.",
    start_period=START_YEAR,
)
ds_hours = Dataset.from_sdmx_csv(
    path_hours,
    name="Průměrná týdenní pracovní doba",
    unit="h/týden",
    source_url="Eurostat/lfsa_ewhun2",
)
df_h = ds_hours.df[["geo", "time", "value"]].copy()
df_h = df_h.rename(columns={"value": "H_w"})
df_h["H_w"] = pd.to_numeric(df_h["H_w"], errors="coerce")
df_h = df_h.dropna(subset=["H_w"])
df_h = df_h[df_h["geo"].str.len() == 2]
print(f"  Eurostat H_w: {df_h['geo'].nunique()} countries, "
      f"years {df_h['time'].min()}--{df_h['time'].max()}")

# ── 3. Merge and compute P_S ──────────────────────────────────────────────────
df = df_ilo_clean.merge(df_h[["geo", "time", "H_w"]], on=["geo", "time"], how="left")

# Fill missing H_w using country median (across all available years)
median_hw = df.groupby("geo")["H_w"].median()
df["H_w"] = df.apply(
    lambda r: median_hw.get(r["geo"], 38.0) if pd.isna(r["H_w"]) else r["H_w"],
    axis=1,
)

# Annual working days per worker: H_w × 52.18 weeks / 8 hours per day
df["A"] = df["H_w"] * WEEKS_PER_YEAR / 8.0

# % working time lost to strikes
df["value"] = df["D_S"] / (1000.0 * df["A"]) * 100.0

# Drop countries with too few data points
counts = df.groupby("geo")["value"].count()
excluded = counts[counts < MIN_POINTS].index.tolist()
if excluded:
    log.warning(
        "Excluding countries with < %d data points (2000--): %s",
        MIN_POINTS, excluded,
    )
df = df[~df["geo"].isin(excluded)].copy()

ds = Dataset(
    df[["geo", "time", "value"]],
    name="Podíl ztracené pracovní doby vlivem pracovních konfliktů",
    unit="%",
    source_url="ILOSTAT STR_DAYS_ECO_RT_A; DST ABST1 (DK); Eurostat lfsa_ewhun2",
)
print(f"Final: {ds.df['geo'].nunique()} countries, "
      f"years {ds.years[0]}--{ds.years[-1]}")

# Clamp requested COUNTRIES to those actually present
countries_present = [c for c in COUNTRIES if c in ds.countries]
highlight_present = [c for c in HIGHLIGHT if c in countries_present]
missing = set(COUNTRIES) - set(countries_present)
if missing:
    log.warning("Countries not in data: %s", missing)

# ── 4. Plot ───────────────────────────────────────────────────────────────────
latest_yr = ds.years[-1]

STRINGS = {
    "title": "Ztracená pracovní doba vlivem pracovních konfliktů",
    "ylabel": r"ztracená pracovní doba [\%]",
}
fig = timeline(
    ds,
    countries=countries_present,
    title=STRINGS["title"],
    ylabel=STRINGS["ylabel"],
    highlight=highlight_present,
    annotate_last=True,
    background_eu=True,
    show_eu_avg=False,
)
fig.axes[0].set_xlim(START_YEAR - 1, 2025)
fig.axes[0].set_ylim(0, 0.4)   # cap at 0.4 %; LT 2008 outlier (~10 %) is clipped

# ── PGF tooltips & geo labels ───────────────────────────────────────────
_pivot_str = (
    ds.df[ds.df["geo"].isin(countries_present)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(fig.axes[0], _pivot_str, fmt="{:.3f}")
_bg_str = sorted(set(_EU27) - set(countries_present))
_pivot_str_bg = (
    ds.df[ds.df["geo"].isin(_bg_str)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(fig.axes[0], _pivot_str_bg, fmt="{:.3f}")
for _child in fig.axes[0].get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in countries_present:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in countries_present]
savefig_pgf(fig, "stav_stavky", strings=STRINGS, nudge_labels=NUDGE_LABELS)

save_figure_tex_pgf(
    "stav_stavky",
    caption=(
        r"Podíl ztracené pracovní doby vlivem pracovních konfliktů (stávky a~výluky), "
        f"{START_YEAR}--{latest_yr}. "
        r"Zobrazeno 9 zemí s~dostatečně kontinuálním reportováním dat "
        r"(CZ, SK a~další země s~chybějícím pokrytím nejsou zobrazeny --- "
        r"nulové hodnoty v~datové sadě \ac{ILO} neodpovídají nulové aktivitě). "
        r"DK: vlastní výpočet z~národní statistiky (Statistics Denmark, ABST1). "
        r"Šedé linie = ostatní reportující země EU\,27; osa $y$ je zkrácena na \SI{0.4}{\percent} "
        r"(LT 2008 dosahuje cca \SI{10}{\percent} --- jednorázový spor ve veřejném sektoru)."
    ),
    label="fig:stav_stavky",
    resizebox_width=r"\linewidth",
    cite_keys=["ilostat_STR_DAYS_ECO_RT_A", "dst_abst1", "eurostat_lfsa_ewhun2"],
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
