r"""
Regional, gender and sectoral wage stratification using ISPV / RSCP data.

ISPV (*Informační systém o průměrném výdělku*) semi-annual Excel workbooks
publish wage breakdowns by NACE sector, Czech region (kraj / NUTS3), and sex,
with full percentile profiles (P10–P90).  This script extracts three
argumentation figures that together illustrate the multi-dimensional structure
of wage inequality in the Czech labour market.

Figure A – ``rscp_regional_wages``
    Horizontal bar chart: CZ median monthly wage by region (kraj), indexed
    to the national median (100 = ČR celkem).

    Data: ISPV Excel regional sheet (``sheet_name`` matching "kraj" or index 1)
    when available; falls back to Eurostat ``earn_rgnmhw`` (mean hourly wages,
    NUTS2) for AT, DE, DK, PL, SK cross-country context.

    Argumentation: Persistent regional wage gaps (Prague 140–150 vs. rural
    regions 80–90) illustrate why a single national wage floor / collective
    agreement can mean very different things across regions — and why regional
    extension mechanisms matter for equality.

Figure B – ``rscp_gender_gap``
    Dual panel:
      Left  – CZ unadjusted gender pay gap (%) by NACE sector (ISPV M/Ž
              median columns or Eurostat ``earn_gr_gpgr2``).
      Right – Cross-country unadjusted GPG trend 2010–2024 for 6 countries
              (Eurostat ``earn_gr_gpgr2``, economy-wide).

    Argumentation: The sectoral GPG panel shows that the gender wage gap is
    not uniform — it is smallest in sectors with strong collective agreements
    (industry, finance) and largest in mixed/service sectors.  The
    cross-country trend shows CZ consistently above the EU average, providing
    a reform motivation.

Figure C – ``rscp_sector_percentiles``
    Grouped horizontal bar (floating whisker) chart: P25 / P50 / P75 wage
    levels by NACE sector for CZ (ISPV percentile columns).  Bars run from
    P25 to P75; tick marks at P50.

    Argumentation: Sectors with narrow P25–P75 bands (low within-sector
    dispersion) are candidates for sector-wide collective agreements with
    tight wage grids; wide-band sectors have heterogeneous workforces where
    economy-wide KS floors are less effective.

Data sources
------------
Czech sector/regional wages: MPSV/TREXIMA ISPV & RSCP Excel workbooks.
Gender pay gap by NACE:      Eurostat ``earn_gr_gpgr2``.
Regional hourly wages:       Eurostat ``earn_rgnmhw``.

Output
------
  pics/python/rscp_regional_wages.pdf
  pics/python/rscp_gender_gap.pdf
  pics/python/rscp_sector_percentiles.pdf
  latex/texparts/python/rscp_regional_wages.tex
  latex/texparts/python/rscp_gender_gap.tex
  latex/texparts/python/rscp_sector_percentiles.tex

Run
---
    python analyses/rscp_stratification.py
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
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

apply_style()

# ── Parameters ────────────────────────────────────────────────────────────────
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2010   # gender pay gap trend starts here
END_YEAR   = 2024

CZ_COLOR = COUNTRY_COLORS["CZ"]

# Czech regions (kraje) — canonical order (Prague first, then Bohemia, Moravia)
CZ_REGIONS_ORDER = [
    "Hlavní město Praha",
    "Jihomoravský kraj",
    "Plzeňský kraj",
    "Středočeský kraj",
    "Liberecký kraj",
    "Královéhradecký kraj",
    "Pardubický kraj",
    "Kraj Vysočina",
    "Jihočeský kraj",
    "Olomoucký kraj",
    "Zlínský kraj",
    "Moravskoslezský kraj",
    "Ústecký kraj",
    "Karlovarský kraj",
]

# Short region labels for axis ticks
_REGION_SHORT: dict[str, str] = {
    "Hlavní město Praha":    "Praha",
    "Středočeský kraj":      "Středočeský",
    "Jihočeský kraj":        "Jihočeský",
    "Plzeňský kraj":         "Plzeňský",
    "Karlovarský kraj":      "Karlovarský",
    "Ústecký kraj":          "Ústecký",
    "Liberecký kraj":        "Liberecký",
    "Královéhradecký kraj":  "Královéhradecký",
    "Pardubický kraj":       "Pardubický",
    "Kraj Vysočina":         "Vysočina",
    "Jihomoravský kraj":     "Jihomoravský",
    "Olomoucký kraj":        "Olomoucký",
    "Zlínský kraj":          "Zlínský",
    "Moravskoslezský kraj":  "Moravskoslezský",
}


# ════════════════════════════════════════════════════════════════════════════
# ISPV Excel parsers
# ════════════════════════════════════════════════════════════════════════════

def _find_sheet(path: Path, keywords: list[str]) -> int | str | None:
    """Return the first sheet name/index that contains one of the keywords."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for i, name in enumerate(wb.sheetnames):
            if any(kw.lower() in name.lower() for kw in keywords):
                wb.close()
                return name
        wb.close()
        # Fallback: return second sheet if available (often regional data)
        return None
    except Exception as exc:
        log.debug("_find_sheet failed: %s", exc)
        return None


def _read_ispv_table(
    path: Path,
    sheet: int | str = 0,
    stat_col_keywords: list[str] | None = None,
) -> pd.DataFrame | None:
    """Read an ISPV Excel sheet; return a DataFrame with sector rows.

    Tries up to 8 skiprows values until a table with >= 3 numeric rows and
    >= 2 columns is found.  Returns None when all attempts fail.

    Parameters
    ----------
    stat_col_keywords:
        Substrings used to locate value columns.  When None, all numeric
        columns are kept.
    """
    for skiprows in range(0, 8):
        try:
            df = pd.read_excel(path, sheet_name=sheet, skiprows=skiprows, header=0)
            df = df.dropna(how="all").reset_index(drop=True)
            if df.shape[1] < 2 or df.shape[0] < 3:
                continue
            first_col = df.columns[0]
            mask = df[first_col].notna() & (df[first_col].astype(str).str.strip() != "")
            sub = df.loc[mask].copy()
            if sub.shape[0] < 3:
                continue
            # Confirm there are at least some numeric values
            numeric_cols = [
                c for c in sub.columns[1:]
                if pd.to_numeric(sub[c], errors="coerce").notna().sum() >= 2
            ]
            if len(numeric_cols) < 1:
                continue
            if stat_col_keywords:
                matched = [
                    c for c in numeric_cols
                    if any(kw.lower() in str(c).lower() for kw in stat_col_keywords)
                ]
                if matched:
                    return sub[[first_col] + matched]
            return sub[[first_col] + numeric_cols]
        except Exception as exc:
            log.debug("_read_ispv_table sheet=%s skiprows=%d: %s", sheet, skiprows, exc)
    return None


def _parse_regional(path: Path) -> pd.Series | None:
    """Return median wage indexed by region label from the ISPV regional sheet."""
    sheet = _find_sheet(path, ["kraj", "region", "územ"])
    if sheet is None:
        sheet = 1  # 2nd sheet is often regional in ISPV workbooks
    df = _read_ispv_table(path, sheet=sheet,
                          stat_col_keywords=["medián", "median", "střední"])
    if df is None:
        return None
    first_col = df.columns[0]
    val_col = df.columns[1]
    s = pd.to_numeric(df[val_col], errors="coerce")
    df = df.copy()
    df[val_col] = s
    df = df.dropna(subset=[val_col])
    df = df[(df[val_col] > 1_000) & (df[val_col] < 500_000)]
    if df.empty:
        return None
    result = df.set_index(first_col)[val_col]
    return result


def _parse_gender_sector(path: Path) -> pd.DataFrame | None:
    """Return a DataFrame with columns [sector, male_median, female_median].

    Looks for a sheet with sex-disaggregated data (columns containing 'muž'
    or 'žen' / 'M' / 'Ž') alongside sector rows.
    """
    male_kws   = ["muž", "muže", "muži", "men", " m "]
    female_kws = ["žen", "ženy", "women", " ž "]
    # Try each sheet
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheets = wb.sheetnames
        wb.close()
    except Exception:
        sheets = [0]

    for sheet in sheets:
        df = _read_ispv_table(path, sheet=sheet)
        if df is None:
            continue
        first_col = df.columns[0]
        col_strs = [str(c).lower() for c in df.columns[1:]]
        male_cols   = [df.columns[1 + i] for i, cs in enumerate(col_strs)
                       if any(kw in cs for kw in male_kws)]
        female_cols = [df.columns[1 + i] for i, cs in enumerate(col_strs)
                       if any(kw in cs for kw in female_kws)]
        if not male_cols or not female_cols:
            continue
        m_col = male_cols[0]
        f_col = female_cols[0]
        out = pd.DataFrame({
            "sector":        df[first_col].values,
            "male_median":   pd.to_numeric(df[m_col], errors="coerce").values,
            "female_median": pd.to_numeric(df[f_col], errors="coerce").values,
        }).dropna()
        out = out[(out["male_median"] > 1_000) & (out["female_median"] > 1_000)]
        if len(out) >= 4:
            out["gpg_pct"] = ((out["male_median"] - out["female_median"])
                              / out["male_median"] * 100)
            return out
    return None


def _parse_percentiles(path: Path) -> pd.DataFrame | None:
    """Return sector-level P25/P50/P75 (and optionally P10/P90) from ISPV."""
    p_kws = ["p10", "p25", "p50", "p75", "p90", "medián", "median",
             "1. decil", "1. kvartil", "medián", "3. kvartil", "9. decil"]
    df = _read_ispv_table(path, sheet=0, stat_col_keywords=p_kws)
    if df is None:
        return None
    first_col = df.columns[0]
    # Identify P25, P50, P75 columns by heuristic name matching
    percentile_map: dict[str, str] = {}
    for col in df.columns[1:]:
        cs = str(col).lower()
        if "p25" in cs or "1. kvartil" in cs or "25" in cs:
            percentile_map.setdefault("p25", col)
        elif "p75" in cs or "3. kvartil" in cs or "75" in cs:
            percentile_map.setdefault("p75", col)
        elif "p50" in cs or "medián" in cs or "median" in cs or "50" in cs:
            percentile_map.setdefault("p50", col)
        elif "p10" in cs or "1. decil" in cs or "10" in cs:
            percentile_map.setdefault("p10", col)
        elif "p90" in cs or "9. decil" in cs or "90" in cs:
            percentile_map.setdefault("p90", col)
    if len(percentile_map) < 2:
        return None
    keep = [first_col] + list(percentile_map.values())
    sub = df[keep].copy()
    for c in keep[1:]:
        sub[c] = pd.to_numeric(sub[c], errors="coerce")
    sub = sub.dropna()
    sub = sub[(sub.iloc[:, 1] > 1_000)]
    if sub.empty:
        return None
    sub = sub.rename(columns={v: k for k, v in percentile_map.items()})
    sub = sub.rename(columns={first_col: "sector"})
    return sub


# ════════════════════════════════════════════════════════════════════════════
# Fetch ISPV for latest available year
# ════════════════════════════════════════════════════════════════════════════
print("Fetching ISPV data …")
ispv_path: Path | None = None
ispv_year: int | None = None

for yr in range(END_YEAR, 2014, -1):
    try:
        path_try = fetch_ispv(yr, half=2, sphere="podnikatelska")
        # Quick sanity: at least parseable as Excel
        pd.read_excel(path_try, sheet_name=0, nrows=5)
        ispv_path = path_try
        ispv_year = yr
        print(f"  ISPV {yr}/H2 fetched: {path_try.name}")
        break
    except Exception as exc:
        print(f"  ISPV {yr}/H2: skipped ({type(exc).__name__})")

# ════════════════════════════════════════════════════════════════════════════
# Figure A – Regional wage levels
# ════════════════════════════════════════════════════════════════════════════
regional_done = False

if ispv_path is not None:
    reg_wages = _parse_regional(ispv_path)
    if reg_wages is not None and len(reg_wages) >= 4:
        # Identify national average row (often "ČR celkem", "Česká republika")
        avg_kws = ["česká republika", "čr celkem", "celkem", "průměr", "total"]
        nat_row = None
        for idx in reg_wages.index:
            if any(kw in str(idx).lower() for kw in avg_kws):
                nat_row = idx
                break
        if nat_row is not None and reg_wages[nat_row] > 0:
            nat_med = reg_wages[nat_row]
            reg_idx = (reg_wages.drop(index=nat_row) / nat_med * 100).sort_values()
        else:
            nat_med = float(reg_wages.median())
            reg_idx = (reg_wages / nat_med * 100).sort_values()

        # Shorten labels where possible
        reg_idx.index = [_REGION_SHORT.get(str(k), str(k)) for k in reg_idx.index]

        fig_a, ax_a = plt.subplots(figsize=cm2in(16, max(9, len(reg_idx) * 0.65)))
        bar_colors = [CZ_COLOR if v >= 100 else "#4393C3" for v in reg_idx]
        ax_a.barh(reg_idx.index, reg_idx.values, color=bar_colors, alpha=0.82, height=0.7)
        ax_a.axvline(100, color="gray", linewidth=1.2, linestyle="--", zorder=5)
        ax_a.set_xlabel("Index (národní medián = 100)", fontsize=FONT_SIZE)
        ax_a.set_title(
            f"ČR: mediánová mzda podle kraje (ISPV {ispv_year}/H2)",
            fontsize=FONT_SIZE,
        )
        ax_a.xaxis.set_major_formatter(
            ticker.FuncFormatter(lambda x, _: f"{x:.0f}")
        )
        above = mpatches.Patch(color=CZ_COLOR, alpha=0.82, label="Nadnárodní medián")
        below = mpatches.Patch(color="#4393C3", alpha=0.82, label="Podnárodní medián")
        ax_a.legend(handles=[above, below], frameon=False, fontsize=FONT_SIZE - 1,
                    loc="lower right")
        savefig(fig_a, "rscp_regional_wages", out_dir=LATEX_PICS_DIR)
        save_figure_tex(
            "rscp_regional_wages",
            caption=(
                f"ČR: mediánová hrubá mzda podle kraje (ISPV {ispv_year}/H2, "
                "MPSV/TREXIMA), normovaná na národní medián\u00a0=\u00a0100. "
                "Červené sloupce = regiony s~nadprůměrnou mzdou; modré = "
                "podprůměrné kraje. Přetrvávající regionální mzdové nerovnosti "
                "dokládají, proč celostátní minimální mzda a KS různě ovlivňují "
                "reálnou kupní sílu zaměstnanců v~různých částech republiky."
            ),
            label="fig:rscp_regional_wages",
            width=r"0.95\linewidth",
            cite_key="mpsv_ispv",
        )
        regional_done = True

if not regional_done:
    # Eurostat NUTS2 fallback for CZ: earn_rgnmhw (mean hourly wages by NUTS2)
    print("  ISPV regional data unavailable; trying Eurostat earn_rgnmhw …")
    try:
        path_rg = fetch_eurostat(
            "earn_rgnmhw",
            "A.EUR.E.TOTAL.T.CZ",
            start_period=END_YEAR - 2,
        )
        from stattool.dataset import Dataset
        ds_rg = Dataset.from_sdmx_csv(path_rg, name="earn_rgnmhw", unit="EUR",
                                      source_url="Eurostat/earn_rgnmhw")
        if not ds_rg.df.empty:
            # ds_rg.df columns: geo, time, value
            yr_col = ds_rg.time_col
            most_recent = ds_rg.df[yr_col].max()
            snap = ds_rg.df[ds_rg.df[yr_col] == most_recent].copy()
            snap = snap[snap["geo"].str.startswith("CZ")]
            snap = snap.sort_values(ds_rg.value_col)
            nat_val = snap[ds_rg.value_col].median()
            snap["idx"] = snap[ds_rg.value_col] / nat_val * 100
            fig_a2, ax_a2 = plt.subplots(figsize=cm2in(14, max(8, len(snap) * 0.65)))
            bar_colors2 = [CZ_COLOR if v >= 100 else "#4393C3" for v in snap["idx"]]
            ax_a2.barh(snap["geo"].values, snap["idx"].values,
                       color=bar_colors2, alpha=0.82, height=0.7)
            ax_a2.axvline(100, color="gray", linewidth=1.2, linestyle="--")
            ax_a2.set_xlabel("Index (CZ medián NUTS2 = 100)", fontsize=FONT_SIZE)
            ax_a2.set_title(
                f"ČR NUTS2: průměrné hodinové mzdy (Eurostat, {most_recent})",
                fontsize=FONT_SIZE,
            )
            savefig(fig_a2, "rscp_regional_wages", out_dir=LATEX_PICS_DIR)
            save_figure_tex(
                "rscp_regional_wages",
                caption=(
                    f"ČR: průměrná hodinová mzda podle regionů NUTS2 "
                    f"(Eurostat earn_rgnmhw, {most_recent}), normovaná na medián "
                    "CZ regionů\u00a0=\u00a0100."
                ),
                label="fig:rscp_regional_wages",
                width=r"0.95\linewidth",
                cite_key="eurostat_rgnmhw",
            )
            regional_done = True
    except Exception as exc:
        print(f"  Eurostat regional fallback failed: {exc}")

if not regional_done:
    print("Figure A (regional wages) skipped – no data available.")


# ════════════════════════════════════════════════════════════════════════════
# Figure B – Gender pay gap (sector CZ + cross-country trend)
# ════════════════════════════════════════════════════════════════════════════
print("\nBuilding gender pay gap figures …")

# ── B1: CZ GPG by sector from ISPV ───────────────────────────────────────
ispv_gpg_sector: pd.DataFrame | None = None
if ispv_path is not None:
    ispv_gpg_sector = _parse_gender_sector(ispv_path)
    if ispv_gpg_sector is not None:
        print(f"  ISPV gender breakdown: {len(ispv_gpg_sector)} sectors")
    else:
        print("  ISPV gender columns not found in workbook")

# ── B2: Cross-country GPG trend (Eurostat earn_gr_gpgr2) ─────────────────
geo_6 = "+".join(COUNTRIES)
gpg_trend: dict[str, pd.Series] = {}
try:
    path_gpg = fetch_eurostat(
        "earn_gr_gpgr2",
        f"A.TOTAL.TOTAL.{geo_6}",
        start_period=START_YEAR,
    )
    from stattool.dataset import Dataset
    ds_gpg = Dataset.from_sdmx_csv(path_gpg, name="GPG", unit="%",
                                   source_url="Eurostat/earn_gr_gpgr2")
    if not ds_gpg.df.empty:
        for country in COUNTRIES:
            sub = ds_gpg.df[ds_gpg.df["geo"] == country].copy()
            sub["time"] = sub[ds_gpg.time_col].astype(int)
            sub = sub.sort_values("time")
            s = sub.set_index("time")[ds_gpg.value_col].dropna()
            if len(s) >= 3:
                gpg_trend[country] = s
        print(f"  GPG trend countries: {sorted(gpg_trend.keys())}")
    else:
        print("  earn_gr_gpgr2 returned no data")
except Exception as exc:
    print(f"  earn_gr_gpgr2 fetch failed: {exc}")

# ── Build Figure B ────────────────────────────────────────────────────────
has_sector_gpg = ispv_gpg_sector is not None
has_trend_gpg  = bool(gpg_trend)

if has_sector_gpg or has_trend_gpg:
    n_panels = (1 if has_sector_gpg else 0) + (1 if has_trend_gpg else 0)
    fig_b, axes_b = plt.subplots(
        1, n_panels, figsize=cm2in(16 * n_panels / 2 + 4, 10),
        squeeze=False,
    )
    axes_b = axes_b.flatten()
    panel = 0

    if has_sector_gpg:
        ax = axes_b[panel]; panel += 1
        gpg_s = ispv_gpg_sector.sort_values("gpg_pct")
        bar_clrs = [CZ_COLOR if v >= 0 else "#2CA02C" for v in gpg_s["gpg_pct"]]
        ax.barh(gpg_s["sector"].values, gpg_s["gpg_pct"].values,
                color=bar_clrs, alpha=0.82, height=0.7)
        ax.axvline(0, color="gray", linewidth=0.8, linestyle="-")
        ax.set_xlabel("Gender pay gap, muži − ženy (%)", fontsize=FONT_SIZE)
        ax.set_title(
            f"ČR: gender pay gap podle odvětví\n(ISPV {ispv_year}/H2)",
            fontsize=FONT_SIZE,
        )
        ax.xaxis.set_major_formatter(
            ticker.FuncFormatter(lambda x, _: f"{x:.0f}\u00a0pp")
        )

    if has_trend_gpg:
        ax = axes_b[panel]; panel += 1
        for i, country in enumerate(COUNTRIES):
            if country not in gpg_trend:
                continue
            s = gpg_trend[country]
            lw  = 2.5 if country == "CZ" else 1.4
            ls  = "-" if country == "CZ" else "--"
            ax.plot(
                s.index, s.values,
                label=country, color=COUNTRY_COLORS.get(country, PALETTE[i]),
                linewidth=lw, linestyle=ls,
                marker="o" if country == "CZ" else None,
                markersize=3.5,
            )
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda y, _: f"{y:.0f}\u00a0%")
        )
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=7))
        ax.set_xlabel("rok", fontsize=FONT_SIZE)
        ax.set_ylabel("Neupr. gender pay gap (%)", fontsize=FONT_SIZE)
        ax.set_title(
            "Nekorigovaný gender pay gap: 6 zemí",
            fontsize=FONT_SIZE,
        )
        ax.legend(frameon=False, fontsize=FONT_SIZE - 1.5, ncol=2)

    fig_b.tight_layout(pad=1.5)
    savefig(fig_b, "rscp_gender_gap", out_dir=LATEX_PICS_DIR, tight=False)
    caption_gpg = (
        "Gender pay gap (GPG, rozdíl mediánových hrubých mezd mužů a žen v~\\%) "
    )
    if has_sector_gpg:
        caption_gpg += (
            f"podle odvětví NACE v~ČR (ISPV {ispv_year}/H2, levý panel) a "
        )
    caption_gpg += (
        "vývoj nekorigovaného GPG v~6 srovnávaných zemích "
        f"{START_YEAR}\u2013{END_YEAR} (Eurostat earn_gr_gpgr2, pravý panel). "
        "ČR se dlouhodobě nachází nad průměrem EU a odvětvový profil GPG "
        "ukazuje, že odvětví se silnějším kolektivním vyjednáváním vykazují "
        "nižší mzdové nerovnosti mezi pohlavími."
    )
    save_figure_tex(
        "rscp_gender_gap",
        caption=caption_gpg,
        label="fig:rscp_gender_gap",
        width=r"0.98\linewidth",
        cite_key="eurostat_gpg",
    )
else:
    print("Figure B (gender pay gap) skipped – no data available.")


# ════════════════════════════════════════════════════════════════════════════
# Figure C – Sector wage distribution (P25 / P50 / P75) from ISPV
# ════════════════════════════════════════════════════════════════════════════
print("\nBuilding sector percentile figure …")
pct_df: pd.DataFrame | None = None
if ispv_path is not None:
    pct_df = _parse_percentiles(ispv_path)
    if pct_df is not None:
        print(f"  Percentile table: {len(pct_df)} sectors, cols={list(pct_df.columns)}")
    else:
        print("  No percentile columns found in ISPV workbook")

if pct_df is not None and "p50" in pct_df.columns:
    # Sort by median descending
    pct_df = pct_df.sort_values("p50", ascending=True).reset_index(drop=True)
    n = len(pct_df)

    fig_c, ax_c = plt.subplots(figsize=cm2in(16, max(9, n * 0.65)))

    y_pos = np.arange(n)
    labels = [str(s) for s in pct_df["sector"]]

    # Draw IQR bar (P25–P75) if available
    if "p25" in pct_df.columns and "p75" in pct_df.columns:
        widths = pct_df["p75"].values - pct_df["p25"].values
        ax_c.barh(
            y_pos, widths, left=pct_df["p25"].values,
            color="#4393C3", alpha=0.55, height=0.6, label="P25–P75 (IQR)",
        )

    # P50 tick mark
    ax_c.scatter(
        pct_df["p50"].values, y_pos,
        color=CZ_COLOR, zorder=5, s=40, label="Medián (P50)",
    )

    # P10 / P90 whiskers if available
    if "p10" in pct_df.columns:
        for i, (p10, p25) in enumerate(zip(pct_df["p10"].values,
                                           pct_df.get("p25", pct_df["p50"]).values)):
            ax_c.plot([p10, p25], [i, i], color="gray", linewidth=1.0, alpha=0.7)
    if "p90" in pct_df.columns:
        p75_vals = pct_df.get("p75", pct_df["p50"]).values
        for i, (p75, p90) in enumerate(zip(p75_vals, pct_df["p90"].values)):
            ax_c.plot([p75, p90], [i, i], color="gray", linewidth=1.0, alpha=0.7)

    ax_c.set_yticks(y_pos)
    ax_c.set_yticklabels(labels, fontsize=FONT_SIZE - 1)
    ax_c.xaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, _: f"{x/1_000:.0f}\u00a0tis. Kč")
    )
    ax_c.set_xlabel("Hrubá měsíční mzda (Kč)", fontsize=FONT_SIZE)
    ax_c.set_title(
        f"ČR: rozložení mezd podle odvětví NACE (ISPV {ispv_year}/H2)\n"
        "mezikvartilový rozsah P25–P75 a medián",
        fontsize=FONT_SIZE,
    )
    ax_c.legend(frameon=False, fontsize=FONT_SIZE - 1, loc="lower right")

    savefig(fig_c, "rscp_sector_percentiles", out_dir=LATEX_PICS_DIR)
    save_figure_tex(
        "rscp_sector_percentiles",
        caption=(
            f"ČR: vnitroodnvětvové rozložení hrubé měsíční mzdy podle odvětví NACE "
            f"(ISPV {ispv_year}/H2, MPSV/TREXIMA). "
            "Modrý pruh = mezikvartilový rozsah P25–P75; červená tečka = medián (P50); "
            "šedé vousy = P10 a P90 (pokud jsou k~dispozici). "
            "Odvětví s~úzkým IQR jsou kandidáty pro kolektivní smlouvy "
            "s~pevnou tarifní strukturou; odvětví s~širokým IQR vyžadují "
            "flexibilnější přístupy nebo individuální sjednávání mzdy."
        ),
        label="fig:rscp_sector_percentiles",
        width=r"0.95\linewidth",
        cite_key="mpsv_ispv",
    )
else:
    print("Figure C (sector percentiles) skipped – no percentile data available.")

print("\nDone.")
