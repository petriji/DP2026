r"""
Czech sector-specific wage analysis using ISPV / RSCP data.

ISPV (*Informační systém o průměrném výdělku*) and RSCP (*Registr středních
cen práce*) are the Czech semi-annual wage surveys published by TREXIMA on
behalf of MPSV.  They provide median and percentile wages broken down by
NACE Rev. 2 sector, enabling sector-specific argumentation to complement the
economy-wide IPP collective-agreement analysis.

Three argumentation figures are produced:

Figure A -- ``rscp_sector_wages_cz``
    Horizontal bar chart: CZ sector median monthly wages relative to the
    economy-wide median (index 100 = economy median).  Sectors above 100
    are high-wage; below 100 are low-wage.

    Data: ISPV Excel workbook (podnikatelská sféra) if available (NACE
    sector detail).  Falls back to Eurostat ``earn_ses_pub2s`` cross-country
    comparison when ISPV is unavailable (network-restricted CI).

    Argumentation: Establishes the sector wage hierarchy and identifies
    where collective agreements face the greatest wage-floor pressure
    (low-wage sectors) vs. where they are least binding (high-wage sectors).

Figure B -- ``rscp_sector_lci_growth``
    Multi-line time series: CZ Labour Cost Index annual growth (%) by
    NACE sector, 2016--2025.

    Data: Eurostat ``lc_lci_r2_a`` with available NACE breakdowns for CZ.

    Argumentation: Illustrates sector heterogeneity in wage dynamics.
    Sectors with persistent above-average growth signal tight labour
    markets where market competition drives wages above KS-negotiated
    levels; below-average sectors depend more on collective agreements
    as a wage floor.

Figure C -- ``rscp_sector_dispersion``
    Grouped bar or dot plot: inter-country comparison of wage variation
    across sectors (coefficient of variation of sector median wages) for
    the 6 comparison countries.

    Data: Eurostat ``earn_ses_pub2s`` (Structure of Earnings Survey).

    Argumentation: Countries with stronger centralised bargaining
    (AT, DK) tend to show lower inter-sector wage dispersion; CZ's
    position illustrates the fragmented, enterprise-level bargaining
    legacy and its widening sector wage spread.

Data sources
------------
Czech sector wages:  MPSV/TREXIMA ISPV & RSCP Excel workbooks
                     (``https://www.ispv.cz``).
LCI by NACE:         Eurostat ``lc_lci_r2_a``.
Sector wage levels:  Eurostat ``earn_ses_pub2s``.

Output
------
  pics/python/problemy_sektor_mzdy_cz.pdf
  pics/python/problemy_sektor_lci.pdf
  pics/python/problemy_sektor_disperze.pdf
  latex/texparts/python/problemy_sektor_mzdy_cz.tex
  latex/texparts/python/problemy_sektor_lci.tex
  latex/texparts/python/problemy_sektor_disperze.tex

Run
---
    python analyses/rscp_sector_wages.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.fetch import fetch_ispv, fetch_eurostat
from stattool.style import cm2in, apply_style_pgf, savefig_pgf, save_figure_tex_pgf

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

apply_style_pgf()

# ── Parameters ────────────────────────────────────────────────────────────────
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2016
END_YEAR   = 2024   # SES and ISPV lag by one year vs IPP

# NACE sections in lc_lci_r2_a that Eurostat publishes for most countries.
# Keys = Eurostat NACE filter code; values = short Czech sector label.
LCI_NACE_CODES: dict[str, str] = {
    "B-E":  "Průmysl (B--E)",
    "C":     "Zpracovatelský průmysl (C)",
    "F":     "Stavebnictví (F)",
    "G-J":   "Obchod, doprava, IT (G--J)",
    "K-N":   "Finance, poradenství (K--N)",
}

# SES NACE codes available in earn_ses_pub2s (for inter-country comparison)
SES_NACE_CODES: dict[str, str] = {
    "B-E_X_D": "Průmysl",
    "C":        "Výroba",
    "F":        "Stavebnictví",
    "G":        "Obchod",
    "H":        "Doprava",
    "I":        "Ubytování/pohostinství",
    "J":        "Informace/komunikace",
    "K":        "Finance",
}

CZ_COLOR = COUNTRY_COLORS["CZ"]
GRAY     = "#555555"

# GUID-based URL for the 2025 ISPV national workbook (MZS sheets)
_ISPV_NAT_2025_URL = (
    "https://www.ispv.cz/getattachment/b568f503-6978-4af7-9f8a-d5aef8e46619"
    "/CR_254_MZS-xlsx.aspx?disposition=attachment"
)
# MZS-M6 (NACE section breakdown) is embedded in the MZS-M5_6 sheet.
# Rows 25--43 (0-based) in that sheet contain sections A--S; col 0=code, col 3=median.
_MZS_M6_START_ROW = 25
_MZS_M6_MEDIAN_COL = 3


# ════════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════════

def _read_ispv_nace_from_guid(url: str) -> pd.Series | None:
    """Download ISPV national workbook via GUID URL and extract NACE median wages.

    Reads MZS-M6 (NACE section breakdown) embedded in the ``MZS-M5_6`` sheet.
    Returns pd.Series indexed by short NACE label (e.g. "C -- Zpracovatelský průmysl").
    """
    from stattool.fetch import fetch as _fetch
    try:
        path = _fetch(url, suffix=".xlsx")
    except Exception as exc:
        log.warning("ISPV GUID download failed: %s", exc)
        return None
    try:
        df = pd.read_excel(path, sheet_name="MZS-M5_6", header=None)
    except Exception as exc:
        log.warning("ISPV: cannot read MZS-M5_6: %s", exc)
        return None
    # Find the MZS-M6 block by scanning for "sekce CZ-NACE" header row
    start = None
    for i in range(df.shape[0]):
        cell = str(df.iloc[i, 0]).strip().lower()
        if "sekce" in cell and "nace" in cell:
            # Data starts 3 rows after the header row
            start = i + 4
            break
    if start is None:
        # Fallback: use fixed row
        start = _MZS_M6_START_ROW
    records = {}
    for i in range(start, df.shape[0]):
        code = str(df.iloc[i, 0]).strip()
        label_raw = str(df.iloc[i, 1]).strip() if df.shape[1] > 1 else ""
        if len(code) != 1 or not code.isalpha():
            continue  # stop at Celkem / empty rows
        median = pd.to_numeric(df.iloc[i, _MZS_M6_MEDIAN_COL], errors="coerce")
        if pd.isna(median) or not (10_000 < median < 500_000):
            continue
        short = label_raw[:40] if label_raw and label_raw != "nan" else code
        records[f"{code} -- {short}"] = median
    if not records:
        return None
    return pd.Series(records, name="median_wage")


def _read_ispv_sector_wages(path: Path) -> pd.Series | None:
    """Parse the ISPV Excel workbook and return median monthly wages by sector.

    The ISPV workbook has a variable but consistent structure:
    - First sheet: data table with NACE sector rows and statistics columns.
    - First column contains sector names (Czech text).
    - A column labelled "Medián" or similar contains the median monthly wage.

    Returns a pd.Series (index = sector label, value = median wage in CZK)
    or None if parsing fails.
    """
    median_keywords = ["medián", "median", "střední hodnota"]
    for skiprows in range(0, 8):
        try:
            df = pd.read_excel(path, sheet_name=0, skiprows=skiprows, header=0)
            df = df.dropna(how="all").reset_index(drop=True)
            if df.shape[1] < 2 or df.shape[0] < 3:
                continue
            # Find median column
            med_col = None
            for col in df.columns[1:]:
                if any(kw in str(col).lower() for kw in median_keywords):
                    med_col = col
                    break
            if med_col is None:
                continue
            first_col = df.columns[0]
            # Filter rows that look like NACE sectors (non-empty label)
            mask = df[first_col].notna() & (df[first_col].astype(str).str.strip() != "")
            sub = df.loc[mask, [first_col, med_col]].copy()
            sub[med_col] = pd.to_numeric(sub[med_col], errors="coerce")
            sub = sub.dropna(subset=[med_col])
            if sub.empty:
                continue
            result = sub.set_index(first_col)[med_col].rename("median_wage")
            # Basic sanity: wages should be > 1000 CZK and < 500 000 CZK
            result = result[(result > 1_000) & (result < 500_000)]
            if len(result) >= 3:
                return result
        except Exception as exc:
            log.debug("ISPV parse skiprows=%d: %s", skiprows, exc)
    return None


def _fetch_lci_nace(nace_code: str, countries: list[str]) -> pd.DataFrame | None:
    """Fetch Eurostat LCI annual index for one NACE code, return growth rates."""
    geo = "+".join(countries)
    try:
        path = fetch_eurostat(
            "lc_lci_r2_a",
            f"A.I20.{nace_code}.D1_D4_MD5.{geo}",
            start_period=START_YEAR - 1,
        )
        from stattool.dataset import Dataset
        ds = Dataset.from_sdmx_csv(path, name=nace_code, unit="I20=100",
                                   source_url="Eurostat/lc_lci_r2_a")
        if ds.df.empty:
            return None
        pivot = (
            ds.df
            .assign(time=lambda d: d[ds.time_col].astype(int))
            .pivot_table(index="time", columns="geo", values=ds.value_col)
        )
        return pivot.pct_change() * 100  # → annual % growth
    except Exception as exc:
        log.warning("LCI fetch failed for NACE %s: %s", nace_code, exc)
        return None


# ════════════════════════════════════════════════════════════════════════════
# 1. Try to fetch ISPV data for latest available year
# ════════════════════════════════════════════════════════════════════════════
print("Fetching ISPV sector wage data …")
ispv_wages: pd.Series | None = None
ispv_year: int | None = None

# Try GUID-based URL (2025 national workbook) first
ispv_wages = _read_ispv_nace_from_guid(_ISPV_NAT_2025_URL)
if ispv_wages is not None and len(ispv_wages) >= 5:
    ispv_year = 2025
    print(f"  ISPV 2025 (GUID): {len(ispv_wages)} NACE sectors parsed")
else:
    # Fallback: try legacy fetch_ispv() URL pattern
    for yr in range(END_YEAR, START_YEAR - 1, -1):
        try:
            path_ispv = fetch_ispv(yr, half=2, sphere="podnikatelska")
            parsed = _read_ispv_sector_wages(path_ispv)
            if parsed is not None and len(parsed) >= 5:
                ispv_wages = parsed
                ispv_year = yr
                print(f"  ISPV {yr}H2: {len(parsed)} sectors parsed")
                break
        except Exception as exc:
            print(f"  ISPV {yr}H2: skipped ({type(exc).__name__}: {exc})")

if ispv_wages is None:
    print("  ISPV unavailable -- sector bar chart will be skipped or use Eurostat fallback.")

# ════════════════════════════════════════════════════════════════════════════
# 2. Fetch Eurostat LCI by NACE for CZ
# ════════════════════════════════════════════════════════════════════════════
print("Fetching Eurostat LCI by NACE for CZ …")
lci_by_nace: dict[str, pd.Series] = {}
for nace_code, label in LCI_NACE_CODES.items():
    df_nace = _fetch_lci_nace(nace_code, ["CZ"])
    if df_nace is not None and "CZ" in df_nace.columns:
        series = df_nace["CZ"].dropna()
        series = series[series.index >= START_YEAR]
        if len(series) >= 3:
            lci_by_nace[nace_code] = series
            print(f"  LCI {nace_code}: {len(series)} years")
        else:
            print(f"  LCI {nace_code}: insufficient data")
    else:
        print(f"  LCI {nace_code}: no data returned")

# Also fetch the aggregate B-S (total business economy) for reference
print("Fetching Eurostat LCI B-S (total) for 6 countries …")
lci_total: dict[str, pd.Series] = {}
try:
    df_total = _fetch_lci_nace("B-S", COUNTRIES)
    if df_total is not None:
        for country in COUNTRIES:
            if country in df_total.columns:
                s = df_total[country].dropna()
                s = s[s.index >= START_YEAR]
                if len(s) >= 3:
                    lci_total[country] = s
        print(f"  Total LCI: {sorted(lci_total.keys())}")
except Exception as exc:
    print(f"  Total LCI fetch failed: {exc}")


# ════════════════════════════════════════════════════════════════════════════
# Figure A -- ISPV sector wage bar chart (CZ)
# ════════════════════════════════════════════════════════════════════════════
if ispv_wages is not None:
    # Normalise to economy-wide median = 100
    economy_median = ispv_wages.median()
    wage_idx = (ispv_wages / economy_median * 100).sort_values()

    fig_a, ax_a = plt.subplots(figsize=cm2in(16, max(9, len(wage_idx) * 0.6)))

    bar_colors = [CZ_COLOR if v >= 100 else "#4393C3" for v in wage_idx]
    ax_a.barh(wage_idx.index, wage_idx.values, color=bar_colors, alpha=0.8, height=0.7)
    ax_a.axvline(100, color="gray", linewidth=1.2, linestyle="--", zorder=5)
    ax_a.xaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, _: f"{x:.0f}")
    )
    STRINGS_A = {
        "title": rf"\acs{{geo-CZ}}: mediánová mzda podle odvětví \acs{{NACE}} (\acs{{ISPV}} {ispv_year})",
        "xlabel": "index (medián ekonomiky = 100)",
    }
    ax_a.set_xlabel(STRINGS_A["xlabel"], fontsize=FONT_SIZE)
    ax_a.set_title(
        STRINGS_A["title"],
        fontsize=FONT_SIZE,
    )
    above = mpatches.Patch(color=CZ_COLOR, alpha=0.8, label="Nadprůměrné mzdy (≥ průměr ekonomiky)")
    below = mpatches.Patch(color="#4393C3", alpha=0.8, label="Podprůměrné mzdy (< průměr ekonomiky)")
    ax_a.legend(handles=[above, below], frameon=False, fontsize=FONT_SIZE - 1, loc="lower right")

    savefig_pgf(fig_a, "problemy_sektor_mzdy_cz", strings=STRINGS_A)
    save_figure_tex_pgf(
        "problemy_sektor_mzdy_cz",
        caption=(
            f"Mediánová hrubá mzda podle odvětví \\acs{{NACE}}, \\acs{{geo-CZ}}, {ispv_year}"),
        label="fig:problemy_sektor_mzdy_cz",
        resizebox_width=r"\linewidth",
        cite_key="mpsv_ispv",
        strings=STRINGS_A,
    )
else:
    print("Figure A (ISPV sector bars) skipped -- ISPV data unavailable.")

# ════════════════════════════════════════════════════════════════════════════
# Figures B & C (problemy_sektor_lci, problemy_sektor_disperze) commented
# out per user request — commentary merged into
# texparts/commentary/problemy_sektor_percentily.tex.
# ════════════════════════════════════════════════════════════════════════════
print("Figures B/C (sektor_lci, sektor_disperze) skipped — commented out.")
import sys as _sys
_sys.exit(0)

# ════════════════════════════════════════════════════════════════════════════
# Figure B -- Eurostat LCI growth by NACE sector (CZ)
# ════════════════════════════════════════════════════════════════════════════
if lci_by_nace:
    fig_b, ax_b = plt.subplots(figsize=cm2in(16, 9))

    # Also add total economy CZ for reference
    if "CZ" in lci_total:
        ax_b.plot(
            lci_total["CZ"].index, lci_total["CZ"].values,
            label="Celkem -- podnikat. sféra (B--N)",
            color="black", linewidth=2.5, linestyle="-",
        )

    for i, (nace_code, series) in enumerate(lci_by_nace.items()):
        label = LCI_NACE_CODES[nace_code]
        ax_b.plot(
            series.index, series.values,
            label=label, linewidth=1.6, linestyle="--",
            color=PALETTE[i % len(PALETTE)],
            marker="o", markersize=3,
        )

    ax_b.axhline(0, color="gray", linewidth=0.7, linestyle=":", alpha=0.5)
    ax_b.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda y, _: f"{y:.0f}\u00a0%")
    )
    ax_b.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
    STRINGS_B = {
        "title": r"\acs{geo-CZ}: růst indexu mzdových nákladů (\acs{LCI}) podle odvětví \acs{NACE}",
        "xlabel": "rok",
        "ylabel": r"meziroční nárůst \acs{LCI} [\%]",
    }
    ax_b.set_xlabel(STRINGS_B["xlabel"], fontsize=FONT_SIZE)
    ax_b.set_ylabel(STRINGS_B["ylabel"], fontsize=FONT_SIZE)
    ax_b.set_title(
        STRINGS_B["title"],
        fontsize=FONT_SIZE,
    )
    ax_b.legend(
        frameon=False, fontsize=FONT_SIZE - 1.5, loc="upper left",
        ncol=2, handlelength=1.5,
    )
    yr0 = min(s.index.min() for s in lci_by_nace.values())
    yr1 = max(s.index.max() for s in lci_by_nace.values())
    ax_b.set_xlim(yr0 - 0.4, yr1 + 0.4)

    savefig_pgf(fig_b, "problemy_sektor_lci", strings=STRINGS_B)
    save_figure_tex_pgf(
        "problemy_sektor_lci",
        caption=f"Meziroční nárůst \\acs{{LCI}} podle odvětví \\acs{{NACE}}, \\acs{{geo-CZ}}, {yr0}--{yr1}",
        label="fig:problemy_sektor_lci",
        resizebox_width=r"\linewidth",
        cite_keys="eurostat_lci",
        strings=STRINGS_B,
    )
else:
    print("Figure B (LCI by sector) skipped -- no Eurostat NACE data available.")

# ════════════════════════════════════════════════════════════════════════════
# Figure C -- Inter-sector wage dispersion across 6 countries
# (LCI coefficient of variation across NACE sectors, one bar per country)
# ════════════════════════════════════════════════════════════════════════════
print("Computing inter-sector wage dispersion (coefficient of variation) …")
# Fetch LCI for all NACE codes and all 6 countries, take most recent year
latest_yr = END_YEAR
nace_lci_latest: dict[str, dict[str, float]] = {}  # country → {nace: growth}

for nace_code in LCI_NACE_CODES:
    df_nace = _fetch_lci_nace(nace_code, COUNTRIES)
    if df_nace is None:
        continue
    for country in COUNTRIES:
        if country not in df_nace.columns:
            continue
        s = df_nace[country].dropna()
        # Use most recent available year
        for yr in range(latest_yr, START_YEAR - 1, -1):
            if yr in s.index:
                nace_lci_latest.setdefault(country, {})[nace_code] = float(s[yr])
                break

# Compute CV across sectors for each country
cv_by_country: dict[str, float] = {}
for country, sector_dict in nace_lci_latest.items():
    if len(sector_dict) < 3:
        continue
    vals = np.array(list(sector_dict.values()))
    if vals.mean() == 0:
        continue
    cv = vals.std() / abs(vals.mean()) * 100
    cv_by_country[country] = cv
    print(f"  {country}: CV = {cv:.1f}% across {len(sector_dict)} NACE codes")

if cv_by_country:
    # Sort by CV descending
    countries_sorted = sorted(cv_by_country, key=lambda c: cv_by_country[c], reverse=True)
    cv_vals = [cv_by_country[c] for c in countries_sorted]
    bar_colors_c = [COUNTRY_COLORS.get(c, PALETTE[0]) for c in countries_sorted]

    fig_c, ax_c = plt.subplots(figsize=cm2in(14, 8))
    bars = ax_c.bar(countries_sorted, cv_vals, color=bar_colors_c, alpha=0.8, width=0.6)

    for bar, val in zip(bars, cv_vals):
        ax_c.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.5,
            f"{val:.1f}",
            ha="center", va="bottom", fontsize=FONT_SIZE - 1.5,
        )

    STRINGS_C = {
        "title": rf"Variace nárůstu \acs{{LCI}} napříč odvětvími, vybrané země \acs{{geo-EU}} ({latest_yr})",
        "ylabel": r"variační koeficient nárůstu \acs{LCI} [\%]",
    }
    ax_c.set_ylabel(STRINGS_C["ylabel"], fontsize=FONT_SIZE)
    ax_c.set_title(
        STRINGS_C["title"],
        fontsize=FONT_SIZE,
    )
    ax_c.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda y, _: f"{y:.0f}\u00a0%")
    )

    savefig_pgf(fig_c, "problemy_sektor_disperze", strings=STRINGS_C)
    save_figure_tex_pgf(
        "problemy_sektor_disperze",
        caption=f"Variace nárůstu \\acs{{LCI}} napříč odvětvími \\acs{{NACE}}, vybrané země \\acs{{geo-EU}}, {latest_yr}",
        cite_keys="eurostat_lci",
        label="fig:problemy_sektor_disperze",
        resizebox_width=r"\linewidth",
        strings=STRINGS_C,
    )
else:
    print("Figure C (sector dispersion) skipped -- insufficient cross-country NACE data.")

print("Done.")
