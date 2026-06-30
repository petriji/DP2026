r"""
CB coverage timeline – EU grey cloud + CZ, AT, DE, DK, PL, SK highlighted.

Data sources
------------
* ICTWSS v2 ``AdjCov`` column (OECD / AIAS, administrative-based adjusted
  coverage) for all EU-27 countries **except Germany**.
* OECD CBC API, ``MEASURE='ERB'`` (European Record of Bargaining survey-based
  measure) for **Germany only** — ICTWSS AdjCov for DE is unavailable after 1990.

Note: AdjCov and ERB are methodologically distinct measures.  German values
(ERB ≈ 49 % in 2024) are not directly comparable to the AdjCov series
(CZ ≈ 31 % in 2023).  Both are shown in a single figure for structural
context; the difference for DE is acknowledged in the caption.

Output
------
  pics/python/cb_coverage_timeline.pdf
  pics/python/cb_coverage_timeline_2004.pdf
  latex/texparts/python/cb_coverage_timeline.tex
  latex/texparts/python/cb_coverage_timeline_2004.tex

Run
---
    python analyses/cb_coverage_timeline.py
"""

import sys
import csv
import urllib.request
from io import StringIO
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_oecd
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "DK", "DE", "AT", "PL", "SK"]
HIGHLIGHT = ["CZ"]
START_YEAR = 1993   # grey cloud starts here; some EU27 countries go back to 1990

ICTWSS_URL = "https://webfs.oecd.org/Els-com/ICTWSS-Database/ICTWSS_v2.csv"

# ISO3 → ISO2 for EU-27 countries
_ISO3_TO_ISO2: dict[str, str] = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY",
    "CZE": "CZ", "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR",
    "DEU": "DE", "GRC": "GR", "HUN": "HU", "IRL": "IE", "ITA": "IT",
    "LVA": "LV", "LTU": "LT", "LUX": "LU", "MLT": "MT", "NLD": "NL",
    "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK", "SVN": "SI",
    "ESP": "ES", "SWE": "SE",
}

EU27_ISO3 = set(_ISO3_TO_ISO2.keys())

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ICTWSS v2 CSV (AdjCov for all EU27 except DE) ────────────────
print("Downloading ICTWSS v2 CSV …")
with urllib.request.urlopen(ICTWSS_URL, timeout=60) as response:
    raw = response.read().decode("utf-8-sig")

reader = csv.DictReader(StringIO(raw))
ictwss_rows = list(reader)

# Extract AdjCov for EU27 (skip DEU and SVK — both replaced by CBC/ERB below)
adjcov_records = []
for row in ictwss_rows:
    iso3 = row.get("iso3", "").strip().upper()
    if iso3 not in EU27_ISO3 or iso3 in ("DEU", "SVK"):
        continue
    val = row.get("AdjCov", "").strip()
    if not val:
        continue
    year = row.get("year", "").strip()
    if not year:
        continue
    adjcov_records.append({
        "geo":   _ISO3_TO_ISO2[iso3],
        "time":  int(year),
        "value": float(val),
    })

df_adjcov = pd.DataFrame(adjcov_records)
print(f"  AdjCov: {df_adjcov['geo'].nunique()} EU27 countries (exc. DE, SK), "
      f"years {df_adjcov['time'].min()}–{df_adjcov['time'].max()}")

# ── 2. Download CBC API (ERB) – DE and SK ──────────────────────────────
print("Downloading OECD CBC API (ERB) for DE and SK …")
path_cbc = fetch_oecd("CBC", start_period=START_YEAR)
ds_cbc = Dataset.from_oecd_csv(
    path_cbc,
    name="Pokrytí KV",
    unit="%",
    source_url="OECD AIAS ICTWSS / CBC (ERB)",
    filters={"MEASURE": "ERB"},
)
df_erb = ds_cbc.df[ds_cbc.df["geo"].isin(["DE", "SK"])][["geo", "time", "value"]].copy()
print(f"  CBC ERB/DE+SK: years {df_erb['time'].min()}–{df_erb['time'].max()}, "
      f"{len(df_erb)} data points")

# ── 3. Merge ──────────────────────────────────────────────────────────────────
df_merged = pd.concat([df_adjcov, df_erb], ignore_index=True)
df_merged = df_merged[df_merged["time"] >= START_YEAR]

ds = Dataset(
    df_merged,
    name="Pokrytí kolektivním vyjednáváním",
    unit="%",
    source_url="ICTWSS AdjCov; OECD CBC ERB (DE, SK)",
)
print(f"Merged: {ds.df['geo'].nunique()} countries, years {ds.years[0]}–{ds.years[-1]}")

# ── 4. Long-run figure (1993–latest, xlim up to 2025) ────────────────────────
fig = timeline(
    ds,
    countries=COUNTRIES,
    title="Pokrytí kolektivním vyjednáváním – vývoj",
    ylabel="podíl zaměstnanců pokrytých KV [%]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=False,
    background_eu=True,
)
fig.axes[0].set_xlim(START_YEAR - 2, 2025)
fig.axes[0].set_ylim(0, 105)

savefig(fig, "cb_coverage_timeline", out_dir=LATEX_PICS_DIR)

latest_yr = ds.years[-1]
save_figure_tex(
    "cb_coverage_timeline",
    caption=(
        r"Vývoj pokrytí kolektivním vyjednáváním, "
        f"{START_YEAR}--{latest_yr}. "
        r"Šedé linie = ostatní země EU\,27. "
        r"CZ, DK, AT, PL: míra upraveného pokrytí \textit{AdjCov} "
        r"(OECD / AIAS ICTWSS); DE a SK: průzkumová míra ERB (Evropský přehled KV, "
        r"ERB \(\neq\) AdjCov). Chybějící hodnoty = mezery v datech."
    ),
    label="fig:cb_coverage_timeline",
    width=r"0.95\linewidth",
    cite_key="oecd_aias_ictwss_CBC_ERB_pct",
)

# ── 5. Cropped figure (2004–latest, xlim up to 2025) ─────────────────────────
YEAR_START2 = 2004

fig2 = timeline(
    ds,
    countries=COUNTRIES,
    title=f"Pokrytí kolektivním vyjednáváním ({YEAR_START2}–{latest_yr})",
    ylabel="podíl zaměstnanců pokrytých KV [%]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    label_offsets={"PL": (4, -10)},
    show_eu_avg=False,
    background_eu=True,
)
fig2.axes[0].set_xlim(YEAR_START2 - 2, 2025)
fig2.axes[0].set_ylim(0, 105)

savefig(fig2, "cb_coverage_timeline_2004", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "cb_coverage_timeline_2004",
    caption=(
        r"Vývoj pokrytí kolektivním vyjednáváním (podíl zaměstnanců "
        r"pokrytých kolektivní smlouvou, \%), "
        f"{YEAR_START2}--{latest_yr}. "
        r"Šedé linie = ostatní země EU\,27. "
        r"CZ, DK, AT, PL: míra \textit{AdjCov} "
        r"(OECD / AIAS ICTWSS); DE a SK: průzkumová míra ERB "
        r"(ERB \(\neq\) AdjCov, viz text). Chybějící hodnoty = mezery v datech."
    ),
    label="fig:cb_coverage_timeline_2004",
    width=r"0.95\linewidth",
    cite_key="oecd_aias_ictwss_CBC_ERB_pct",
)

print("Done.")
