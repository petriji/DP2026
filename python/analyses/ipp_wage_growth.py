r"""
Czech collective-agreement wage growth vs. actual wage growth – CZ and peers.

Data sources
------------
Czech Republic (negotiated):
    MPSV IPP (Informace o pracovních podmínkách) – annual Excel workbooks
    downloaded from ``https://www.kolektivnismlouvy.cz``.
    The ``odmenovani`` workbook for each year contains the median negotiated
    basic-wage increase (%) agreed in collective contracts surveyed that year.

    Sheet / row mapping used here (adjust ``_IPP_SHEET_CFG`` if MPSV change
    the workbook layout in a future edition):
      - ``sheet_name``  – 0-based sheet index or name of the sheet
      - ``skiprows``    – header rows to skip before the data table
      - ``value_col``   – column header substring matching the median-increase
                          column (Czech: "Sjednaný nárůst …" / "Medián …")
      - ``year``        – override for single-year files (no year column)

All 6 countries (actual):
    Eurostat Labour Cost Index – nominal, total economy (``lc_lci_r2``).
    ``B-S`` = total business economy; ``LCI`` = labour cost index;
    ``TOTAL`` = total; ``I15`` = 2015 = 100 base year.
    Annual growth rate derived by dividing consecutive index values.

Output
------
  pics/python/ipp_wage_growth.pdf
  latex/texparts/python/ipp_wage_growth.tex  ← \\input{} this in main.tex

Run
---
    python analyses/ipp_wage_growth.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.fetch import fetch_ipp, fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
GEO_6 = "+".join(COUNTRIES)
START_YEAR = 2016   # first year with consistent IPP odmenovani time-series data
END_YEAR = 2024     # most recent complete survey year

# IPP odmenovani workbook structure (adjust if MPSV updates the layout)
# Each entry: year → dict with read_excel kwargs + metric column info.
# When MPSV publish a new year, add an entry; if the structure changed,
# adjust ``sheet_name``, ``skiprows``, and ``value_col`` accordingly.
_IPP_SHEET_CFG: dict[int, dict] = {
    # Default config applied to years without a specific override
    # Typical IPP odmenovani layout (verified for 2018–2024 editions):
    #   Row 0-2: title / blank rows (skipped)
    #   Row 3:   column headers – "Ukazatel" | numeric columns
    #   Rows 4+: data rows where the first column contains the metric label
    #            and subsequent columns contain values.
    # The row containing the median negotiated-increase figure is identified
    # by the keyword search in _extract_ipp_negotiated_increase() below.
}

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download IPP odmenovani for each survey year ───────────────────────────

def _extract_ipp_negotiated_increase(path: Path, year: int) -> float | None:
    """Extract the median negotiated basic-wage increase (%) from one IPP file.

    The odmenovani Excel workbook has a transposed layout:
    - rows  = indicators (Czech text)
    - columns = values for the survey year / different groups

    The function:
    1. Reads the first sheet with up to 6 leading rows skipped sequentially
       until it finds a parseable table.
    2. Searches for the row whose first column contains keywords associated
       with the negotiated basic-wage increase (sjednaný nárůst základní mzdy).
    3. Returns the first numeric value from that row, interpreted as a %.

    If no matching row is found, returns ``None`` and logs a warning.
    """
    import openpyxl  # lightweight read for structure inspection

    keywords = [
        "sjednaný nárůst základní mzdy",
        "sjednaný nárůst mzdy",
        "sjednaný nárůst",
        "nárůst základní mzdy",
        "medián nárůstu",
        "medián sjednané mzdy",
        "sjednaná mzda",
    ]

    for skiprows in range(0, 7):
        try:
            df = pd.read_excel(path, sheet_name=0, skiprows=skiprows, header=0)
            df = df.dropna(how="all").reset_index(drop=True)
            if df.shape[1] < 2 or df.shape[0] < 1:
                continue

            first_col = df.columns[0]
            for _, row in df.iterrows():
                cell = str(row[first_col]).lower().strip()
                if any(kw in cell for kw in keywords):
                    # Found the row – extract first numeric value
                    for col in df.columns[1:]:
                        val = pd.to_numeric(row[col], errors="coerce")
                        if pd.notna(val) and 0 < val < 200:
                            return float(val)
        except Exception as exc:
            log.debug("skiprows=%d failed: %s", skiprows, exc)
            continue

    log.warning("IPP %d: could not extract negotiated increase from %s", year, path.name)
    return None


print(f"Downloading IPP odmenovani for {START_YEAR}–{END_YEAR} …")

ipp_records: list[dict] = []
ipp_years_ok: list[int] = []

for yr in range(START_YEAR, END_YEAR + 1):
    try:
        path_ipp = fetch_ipp(yr, "odmenovani")
        val = _extract_ipp_negotiated_increase(path_ipp, yr)
        if val is not None:
            ipp_records.append({"time": yr, "value": val})
            ipp_years_ok.append(yr)
            print(f"  IPP {yr}: {val:.1f} %")
        else:
            print(f"  IPP {yr}: extraction failed (structure unrecognised – see log)")
    except Exception as exc:
        print(f"  IPP {yr}: skipped ({exc})")

if not ipp_records:
    print(
        "\nNote: No IPP data could be downloaded (network unavailable or files "
        "not yet published for these years).\n"
        "The figure will show Eurostat labour-cost data only.\n"
        "Download the odmenovani Excel files manually from "
        "https://www.kolektivnismlouvy.cz and re-run to include CZ CA data."
    )

# ── 2. Download Eurostat labour cost index (nominal, all countries) ───────────
# lc_lci_r2: Labour cost index – nominal, total economy
# Dimensions: freq · nace_r2 · lcstruct · unit · geo
# Filter: A (annual) · B-S (business economy) · LCI (index) · TOTAL · I15 (2015=100)
print("Downloading Eurostat labour cost index …")
path_lci = fetch_eurostat(
    "lc_lci_r2",
    f"A.B-S.LCI.TOTAL.I15.{GEO_6}",
    start_period=START_YEAR - 1,  # one extra year to compute first difference
)

ds_lci = Dataset.from_sdmx_csv(
    path_lci,
    name="Index mzdových nákladů",
    unit="2015=100",
    source_url="Eurostat/lc_lci_r2",
)

print(f"LCI countries: {ds_lci.countries}  |  years: {ds_lci.years[0]}–{ds_lci.years[-1]}")

# ── 3. Compute year-on-year wage growth from LCI index ────────────────────────

def _lci_yoy_growth(ds: Dataset, geo: str) -> pd.Series:
    """Return annual % wage growth for *geo* derived from LCI index."""
    sub = ds.for_country(geo).set_index(ds.time_col)[ds.value_col].sort_index()
    return sub.pct_change() * 100


wage_growth: dict[str, pd.Series] = {}
for country in COUNTRIES:
    series = _lci_yoy_growth(ds_lci, country)
    series = series[series.index >= START_YEAR].dropna()
    if not series.empty:
        wage_growth[country] = series

# ── 4. Build figure ───────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=cm2in(15, 10))

prop_cycle = iter(plt.rcParams["axes.prop_cycle"])

# Plot Eurostat actual wage growth (dashed, lighter) for comparison countries
for geo in COUNTRIES:
    if geo not in wage_growth:
        continue
    series = wage_growth[geo]
    color = COUNTRY_COLORS.get(geo, next(prop_cycle)["color"])
    lw = 2.0 if geo == "CZ" else 1.2
    alpha = 1.0 if geo == "CZ" else 0.65
    ax.plot(
        series.index,
        series.values,
        label=f"{geo} (skutečná)",
        color=color,
        linewidth=lw,
        linestyle="--",
        alpha=alpha,
    )

# Plot IPP negotiated increases for CZ (solid, prominent)
if ipp_records:
    df_ipp = pd.DataFrame(ipp_records).set_index("time")["value"]
    ax.plot(
        df_ipp.index,
        df_ipp.values,
        label="CZ (KS – sjednaný nárůst)",
        color=COUNTRY_COLORS["CZ"],
        linewidth=2.5,
        linestyle="-",
        marker="o",
        markersize=4,
        zorder=5,
    )

# Reference line at 0 %
ax.axhline(0, color="gray", linewidth=0.7, linestyle=":", alpha=0.5)

# Axis formatting
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:.0f}\u00a0%"))
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
ax.set_xlabel("rok", fontsize=FONT_SIZE)
ax.set_ylabel("Meziroční nárůst (%)", fontsize=FONT_SIZE)
ax.set_title(
    "Sjednaný nárůst mzdy v KS (CZ) a skutečný nárůst mzdových nákladů",
    fontsize=FONT_SIZE,
)

# Legend: place outside plot area if many entries
ax.legend(
    frameon=False,
    fontsize=FONT_SIZE - 1,
    ncol=2,
    loc="upper left",
)

all_years = sorted(
    {y for s in wage_growth.values() for y in s.index}
    | {r["time"] for r in ipp_records}
)
if all_years:
    ax.set_xlim(all_years[0] - 0.3, all_years[-1] + 0.3)

# ── 5. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "ipp_wage_growth", out_dir=LATEX_PICS_DIR)

# ── 6. Write LaTeX snippet ────────────────────────────────────────────────────
year_range = f"{START_YEAR}–{END_YEAR}"
save_figure_tex(
    "ipp_wage_growth",
    caption=(
        "Sjednaný nárůst základní mzdy v kolektivních smlouvách v~ČR "
        "(MPSV/IPP, plná čára) a~skutečný meziroční nárůst mzdových nákladů "
        f"(Eurostat LCI, přerušovaná čára) pro vybrané země, {year_range}."
    ),
    label="fig:ipp_wage_growth",
    width=r"0.95\linewidth",
    cite_key="mpsv_ipp",
)

print("Done.")
