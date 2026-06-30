r"""
Czech citizen emigration timeline (migr_emi1ctz).

Shows the number of Czech citizens emigrating annually, disaggregated by
broad age group (youth 15--34 vs. mid-career 35--49) to illustrate the
age profile of brain-drain-relevant emigration.

Data source: Eurostat, ``migr_emi1ctz``
  Emigration by age group, sex and citizenship.
  Dimensions: freq · agedef · age · sex · citizen · geo
  Filter: citizen=CZ, sex=T, geo=CZ

Note: migr_emi1ctz counts emigrants *leaving* a given country (geo) who hold
a given citizenship (citizen).  Filtering geo=CZ & citizen=CZ gives Czech
citizens emigrating from CZ.  NOT a destination breakdown -- total outflows.

Output
------
  pics/python/problemy_emigrace_vyvoj.pdf
  latex/texparts/python/problemy_emigrace_vyvoj.tex

Run
---
    cd python && python analyses/emigration_cz.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.data_quality import warn_non_target_year
from stattool.fetch import fetch_eurostat
from stattool.style import cm2in, apply_style_pgf, savefig_pgf, save_figure_tex_pgf

# ── Parameters ────────────────────────────────────────────────────────────────
START_YEAR = 2008
CZ_COLOR   = COUNTRY_COLORS["CZ"]

apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
print("Downloading migr_emi1ctz …")
# Dimensions: freq · citizen · agedef · age · unit · sex · geo
# Filter: freq=A, citizen=CZ, agedef=all, age=all, unit=NR, sex=T, geo=CZ
path = fetch_eurostat(
    "migr_emi1ctz",
    "A.CZ...NR.T.CZ",
    start_period=START_YEAR,
)

# ── 2. Parse and filter ───────────────────────────────────────────────────────
raw = pd.read_csv(path, comment="#")
raw.columns = [c.strip().upper() for c in raw.columns]
print("Columns:", list(raw.columns))

geo_col     = next((c for c in raw.columns if c in ("GEO", "REF_AREA")), None)
time_col    = next((c for c in raw.columns if c in ("TIME_PERIOD", "TIME")), None)
val_col     = next((c for c in raw.columns if c in ("OBS_VALUE", "VALUE")), None)
citizen_col = next((c for c in raw.columns if "CITIZEN" in c), None)
sex_col     = next((c for c in raw.columns if "SEX" in c), None)
# Prefer exact "AGE" over "AGEDEF"
age_col     = next((c for c in raw.columns if c == "AGE"), None) or \
              next((c for c in raw.columns if "AGE" in c and "DEF" not in c), None)

print(f"  citizen col: {citizen_col}, sex col: {sex_col}, age col: {age_col}")
if citizen_col:
    print("  citizen values (sample):", raw[citizen_col].unique()[:10])
if sex_col:
    print("  sex values:", raw[sex_col].unique())
if age_col:
    print("  age values (sample):", raw[age_col].unique()[:15])

# Filter citizen=CZ, sex=T, geo=CZ
mask = pd.Series([True] * len(raw), index=raw.index)
if citizen_col:
    mask &= raw[citizen_col].astype(str).str.upper() == "CZ"
if sex_col:
    sex_total = next(
        (v for v in raw[sex_col].unique() if str(v).upper() in ("T", "TOTAL")), None
    )
    if sex_total:
        mask &= raw[sex_col].astype(str).str.upper() == str(sex_total).upper()
if geo_col:
    mask &= raw[geo_col].astype(str).str.upper() == "CZ"

df = raw[mask].copy()
print(f"  Rows after country/sex filter: {len(df)}")
if age_col:
    print("  age values after filter:", df[age_col].unique())

df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
df = df.dropna(subset=[val_col])
df["time"] = df[time_col].astype(str).str[:4].astype(int)

# ── Bucket age groups ─────────────────────────────────────────────────────────
# Identify individual year/group codes that fall into youth (15-34) and mid-career (35-49)
# Typical codes: Y15-19, Y20-24, Y25-29, Y30-34, Y35-39, Y40-44, Y45-49, TOTAL, etc.
def _age_bucket(code: str) -> str | None:
    code = str(code).upper().replace("Y", "").replace("_", "").strip()
    # Try to parse start of range
    start_str = code.split("-")[0].split("T")[0]
    try:
        start = int(start_str)
    except ValueError:
        return None
    if 15 <= start <= 34:
        return "Y15-34"
    if 35 <= start <= 49:
        return "Y35-49"
    return None

if age_col:
    df["age_bucket"] = df[age_col].map(_age_bucket)
    df_youth  = df[df["age_bucket"] == "Y15-34"].groupby("time")[val_col].sum().reset_index()
    df_mid    = df[df["age_bucket"] == "Y35-49"].groupby("time")[val_col].sum().reset_index()
    df_total  = df[df[age_col].astype(str).str.upper().isin(["TOTAL", "Y"])].groupby(
        "time")[val_col].sum().reset_index()
    have_buckets = len(df_youth) >= 3 and len(df_mid) >= 3
else:
    have_buckets = False
    df_total = df.groupby("time")[val_col].sum().reset_index()

print(f"  Youth rows: {len(df_youth) if have_buckets else 'n/a'}, "
      f"Mid rows: {len(df_mid) if have_buckets else 'n/a'}, "
      f"Total rows: {len(df_total)}")

# ── 3. Figure ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=cm2in(15, 9))

if have_buckets and not df_youth.empty and not df_mid.empty:
    ax.plot(
        df_youth["time"], df_youth[val_col] / 1_000,
        color=PALETTE[0], linewidth=2.2, marker="o", markersize=3.5,
        label="15--34 let (mládež)",
    )
    ax.plot(
        df_mid["time"], df_mid[val_col] / 1_000,
        color=PALETTE[1], linewidth=2.2, marker="s", markersize=3.5,
        label="35--49 let (střední kariéra)",
    )
    if not df_total.empty:
        ax.plot(
            df_total["time"], df_total[val_col] / 1_000,
            color="gray", linewidth=1.4, linestyle="--",
            label="Celkem (evidované věkové skupiny)",
        )
elif not df_total.empty:
    ax.plot(
        df_total["time"], df_total[val_col] / 1_000,
        color=CZ_COLOR, linewidth=2.4, marker="o", markersize=4,
        label="Celkem",
    )

ax.yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda y, _: f"{y:.0f}\u00a0tis.")
)
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
STRINGS = {
    "title": r"Emigrace občanů \acs{geo-CZ} podle věkové skupiny",
    "xlabel": "rok",
    "ylabel": "počet emigrantů [tis.]",
}
ax.set_xlabel(STRINGS["xlabel"], fontsize=FONT_SIZE)
ax.set_ylabel(STRINGS["ylabel"], fontsize=FONT_SIZE)
ax.set_title(
    STRINGS["title"],
    fontsize=FONT_SIZE,
)
ax.legend(frameon=False, fontsize=FONT_SIZE - 1)

# ── 4. Save ───────────────────────────────────────────────────────────────────
savefig_pgf(fig, "problemy_emigrace_vyvoj", strings=STRINGS)

yr_min = int(df["time"].min()) if not df.empty else START_YEAR
yr_max = int(df["time"].max()) if not df.empty else 2023
warn_non_target_year(source="Eurostat migr_emi1ctz", year=yr_max, context="Emigration age-profile timeline latest available year")
save_figure_tex_pgf(
    "problemy_emigrace_vyvoj",
    caption=(
        f"Emigrace z~\\acs{{geo-CZ}} podle věkové skupiny, {yr_min}--{yr_max}."),
    cite_keys="eurostat_migr_emi1ctz",
    label="fig:problemy_emigrace_vyvoj",
    resizebox_width=r"\linewidth",
    strings=STRINGS,
)

print("Done.")
