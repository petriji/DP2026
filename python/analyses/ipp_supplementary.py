r"""
Supplementary figures for the IPP/collective-bargaining analysis.

Three additional figures that support argumentation about the
effectiveness and role of collective agreements in Czech wage setting:

Figure A – ``ipp_neg_vs_inflation``
    CZ negotiated basic-wage increase (IPP/KS) vs. CZ HICP inflation.
    Green shading = years where collective agreements outpaced inflation
    (real wage gain); red shading = years where inflation exceeded the
    negotiated increase (real wage erosion).

    Argumentation: Collective agreements provided consistent real-wage
    gains in 2016–2021; the 2022–2023 inflation shock exposed a lag in
    the negotiation cycle; 2024–2025 returned to a surplus.

Figure B – ``ipp_cumulative_real``
    Cumulative index (2016 = 100) tracking four series:
    nominal actual (Eurostat LCI), nominal negotiated (IPP),
    HICP price level, and real actual / real negotiated (deflated by HICP).

    Argumentation: Despite large nominal increases, CZ workers saw
    their real negotiated wage eroded during 2022–2023; both series
    converge again by 2025, illustrating the limits of annual bargaining
    rounds in fast-inflation environments.

Figure C – ``ipp_actual_vs_neg_gap``
    Bar chart: CZ actual LCI wage growth (Eurostat) minus the IPP
    negotiated increase, per year.

    Argumentation: A consistently positive gap (employers pay above what
    was agreed) indicates that collective agreements act as a floor, not a
    ceiling — labour-market competition drives wages above the negotiated
    minimum.  A negative gap would signal non-compliance or insufficient
    bargaining power.

Data sources
------------
CZ negotiated: MPSV IPP ``odmenovani`` workbooks (kolektivnismlouvy.cz).
CZ HICP:       Eurostat ``prc_hicp_aind`` (annual average rate of change).
Actual wages:  Eurostat ``lc_lci_r2`` (Labour Cost Index, B-S, I15=100).

Output
------
  pics/python/ipp_neg_vs_inflation.pdf
  pics/python/ipp_cumulative_real.pdf
  pics/python/ipp_actual_vs_neg_gap.pdf
  latex/texparts/python/ipp_neg_vs_inflation.tex
  latex/texparts/python/ipp_cumulative_real.tex
  latex/texparts/python/ipp_actual_vs_neg_gap.tex

Run
---
    python analyses/ipp_supplementary.py
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
from stattool.fetch import fetch_ipp, fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

apply_style()

# ── Parameters ────────────────────────────────────────────────────────────────
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2016
END_YEAR   = 2025

# ── Keyword list shared with ipp_wage_growth.py ───────────────────────────────
_KEYWORDS = [
    "sjednaný nárůst základní mzdy",
    "sjednaný nárůst mzdy",
    "sjednaný nárůst",
    "nárůst základní mzdy",
    "medián nárůstu",
    "medián sjednané mzdy",
    "sjednaná mzda",
]


def _extract_ipp_negotiated_increase(path: Path, year: int) -> float | None:
    """Return the median negotiated basic-wage increase (%) from one IPP file."""
    for skiprows in range(0, 7):
        try:
            df = pd.read_excel(path, sheet_name=0, skiprows=skiprows, header=0)
            df = df.dropna(how="all").reset_index(drop=True)
            if df.shape[1] < 2 or df.shape[0] < 1:
                continue
            first_col = df.columns[0]
            for _, row in df.iterrows():
                cell = str(row[first_col]).lower().strip()
                if any(kw in cell for kw in _KEYWORDS):
                    for col in df.columns[1:]:
                        val = pd.to_numeric(row[col], errors="coerce")
                        if pd.notna(val) and 0 < val < 200:
                            return float(val)
        except Exception as exc:
            log.debug("skiprows=%d failed: %s", skiprows, exc)
    log.warning("IPP %d: could not extract negotiated increase from %s", year, path.name)
    return None


# ── 1. Fetch IPP negotiated increases ─────────────────────────────────────────
print(f"Fetching IPP odmenovani {START_YEAR}–{END_YEAR} …")
ipp: dict[int, float] = {}
for yr in range(START_YEAR, END_YEAR + 1):
    try:
        path_ipp = fetch_ipp(yr, "odmenovani")
        val = _extract_ipp_negotiated_increase(path_ipp, yr)
        if val is not None:
            ipp[yr] = val
            print(f"  IPP {yr}: {val:.1f} %")
    except Exception as exc:
        print(f"  IPP {yr}: skipped ({exc})")

if not ipp:
    print(
        "\nNote: No IPP data available – network unavailable or files not yet published.\n"
        "Supplementary figures will be skipped (require both IPP and HICP/LCI).\n"
    )
    print("Done.")
    sys.exit(0)

# ── 2. Fetch Eurostat HICP (annual average % change) for CZ ──────────────────
print("Fetching Eurostat HICP for CZ …")
try:
    path_hicp = fetch_eurostat(
        "prc_hicp_aind",
        "A.RCH_A_AVG.HICP.CZ",
        start_period=START_YEAR,
    )
    ds_hicp_raw = Dataset.from_sdmx_csv(
        path_hicp, name="HICP CZ", unit="%", source_url="Eurostat/prc_hicp_aind"
    )
    hicp: dict[int, float] = {
        int(row[ds_hicp_raw.time_col]): float(row[ds_hicp_raw.value_col])
        for _, row in ds_hicp_raw.df.iterrows()
        if pd.notna(row[ds_hicp_raw.value_col])
    }
    print(f"  HICP years: {sorted(hicp)}")
except Exception as exc:
    print(f"  HICP fetch failed: {exc}")
    hicp = {}

# ── 3. Fetch Eurostat LCI for CZ ──────────────────────────────────────────────
print("Fetching Eurostat LCI for CZ …")
lci_growth: dict[int, float] = {}
try:
    path_lci = fetch_eurostat(
        "lc_lci_r2",
        f"A.B-S.LCI.TOTAL.I15.CZ",
        start_period=START_YEAR - 1,
    )
    ds_lci_raw = Dataset.from_sdmx_csv(
        path_lci, name="LCI CZ", unit="2015=100", source_url="Eurostat/lc_lci_r2"
    )
    sub = (
        ds_lci_raw.df
        .assign(time=lambda d: d[ds_lci_raw.time_col].astype(int))
        .set_index("time")[ds_lci_raw.value_col]
        .sort_index()
    )
    series = sub.pct_change() * 100
    lci_growth = {
        yr: float(val)
        for yr, val in series.items()
        if yr >= START_YEAR and pd.notna(val)
    }
    print(f"  LCI growth years: {sorted(lci_growth)}")
except Exception as exc:
    print(f"  LCI fetch failed: {exc}")

# ── Helpers ───────────────────────────────────────────────────────────────────
CZ_RED = COUNTRY_COLORS["CZ"]
GRAY   = "#555555"


def _common_years(*dicts: dict) -> list[int]:
    """Return sorted years present in all supplied dicts."""
    if not dicts:
        return []
    s = set(dicts[0])
    for d in dicts[1:]:
        s &= set(d)
    return sorted(s)


# ══════════════════════════════════════════════════════════════════════════════
# Figure A – Negotiated wage increase vs. HICP inflation
# ══════════════════════════════════════════════════════════════════════════════
years_ah = _common_years(ipp, hicp)
if years_ah:
    neg_vals  = [ipp[y]  for y in years_ah]
    inf_vals  = [hicp[y] for y in years_ah]

    fig_a, ax_a = plt.subplots(figsize=cm2in(15, 9))

    ax_a.plot(years_ah, neg_vals,
              label="Sjednaný nárůst základní mzdy (IPP/KS)",
              color=CZ_RED, linewidth=2.5, linestyle="-", marker="o", markersize=4, zorder=4)
    ax_a.plot(years_ah, inf_vals,
              label="Inflace HICP – průměr roku (Eurostat)",
              color=GRAY, linewidth=2.0, linestyle="--", marker="s", markersize=3.5, zorder=3)

    # Shading: green where negotiated > inflation, red otherwise
    ax_a.fill_between(
        years_ah, neg_vals, inf_vals,
        where=[n >= h for n, h in zip(neg_vals, inf_vals)],
        alpha=0.12, color="#2CA02C",
        label="Reálný nárůst mzdy (sjednaný > inflace)",
    )
    ax_a.fill_between(
        years_ah, neg_vals, inf_vals,
        where=[n < h for n, h in zip(neg_vals, inf_vals)],
        alpha=0.12, color="#D62728",
        label="Reálný pokles kupní síly (inflace > sjednaný nárůst)",
    )

    ax_a.axhline(0, color="gray", linewidth=0.7, linestyle=":", alpha=0.5)
    ax_a.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{y:.0f}\u00a0%"))
    ax_a.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
    ax_a.set_xlabel("rok", fontsize=FONT_SIZE)
    ax_a.set_ylabel("(%)", fontsize=FONT_SIZE)
    ax_a.set_title(
        "CZ: sjednaný nárůst základní mzdy v KS vs. inflace HICP",
        fontsize=FONT_SIZE,
    )
    ax_a.legend(frameon=False, fontsize=FONT_SIZE - 1, loc="upper left")
    ax_a.set_xlim(years_ah[0] - 0.4, years_ah[-1] + 0.4)

    savefig(fig_a, "ipp_neg_vs_inflation", out_dir=LATEX_PICS_DIR)
    year_range_ah = f"{years_ah[0]}–{years_ah[-1]}"
    save_figure_tex(
        "ipp_neg_vs_inflation",
        caption=(
            "ČR: medián sjednaného nárůstu základní mzdy v~kolektivních smlouvách "
            "(MPSV/IPP, plná čára) a~inflace HICP (Eurostat, přerušovaná čára), "
            f"{year_range_ah}. "
            "Zelené plochy označují roky s~reálným nárůstem kupní síly, "
            "červené plochy roky, kdy inflace převýšila sjednané zvýšení mezd."
        ),
        label="fig:ipp_neg_vs_inflation",
        width=r"0.95\linewidth",
        cite_key="mpsv_ipp",
    )
else:
    print("Figure A skipped – no overlapping IPP + HICP years.")

# ══════════════════════════════════════════════════════════════════════════════
# Figure B – Cumulative real/nominal wage index (CZ, 2016 = 100)
# ══════════════════════════════════════════════════════════════════════════════
years_bc = _common_years(ipp, hicp, lci_growth)
if years_bc:
    def _cumulative(growth_dict: dict, years: list[int]) -> list[float]:
        """Compound-growth index starting at 100 in the first year."""
        idx: list[float] = [100.0]
        for y in years[1:]:
            g = growth_dict.get(y, 0.0)
            idx.append(idx[-1] * (1 + g / 100))
        return idx

    nom_actual = _cumulative(lci_growth, years_bc)
    nom_negot  = _cumulative(ipp,        years_bc)
    price_lvl  = _cumulative(hicp,       years_bc)
    real_actual = [n / p * 100 for n, p in zip(nom_actual, price_lvl)]
    real_negot  = [n / p * 100 for n, p in zip(nom_negot,  price_lvl)]

    fig_b, ax_b = plt.subplots(figsize=cm2in(15, 9))

    ax_b.plot(years_bc, nom_actual,
              label="Nominální – skutečný nárůst (Eurostat LCI)",
              color=CZ_RED,       linewidth=1.8, linestyle="--")
    ax_b.plot(years_bc, nom_negot,
              label="Nominální – sjednáno v KS (IPP)",
              color=CZ_RED,       linewidth=2.2, linestyle="-",
              marker="o", markersize=3)
    ax_b.plot(years_bc, price_lvl,
              label="Cenová hladina HICP",
              color=GRAY,         linewidth=1.5, linestyle=":")
    ax_b.plot(years_bc, real_actual,
              label="Reálný – skutečný nárůst (LCI / HICP)",
              color="#009E73",    linewidth=1.8, linestyle="--")
    ax_b.plot(years_bc, real_negot,
              label="Reálný – sjednáno v KS (IPP / HICP)",
              color="#D55E00",    linewidth=2.2, linestyle="-",
              marker="o", markersize=3)

    ax_b.axhline(100, color="gray", linewidth=0.7, linestyle=":", alpha=0.5)
    ax_b.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda y, _: f"{y:.0f}")
    )
    ax_b.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
    ax_b.set_xlabel("rok", fontsize=FONT_SIZE)
    ax_b.set_ylabel(f"Index ({years_bc[0]} = 100)", fontsize=FONT_SIZE)
    ax_b.set_title(
        f"CZ: kumulativní nominální a reálný nárůst mezd od {years_bc[0]}",
        fontsize=FONT_SIZE,
    )
    ax_b.legend(frameon=False, fontsize=FONT_SIZE - 1.5, loc="upper left", ncol=2)
    ax_b.set_xlim(years_bc[0] - 0.4, years_bc[-1] + 0.4)

    savefig(fig_b, "ipp_cumulative_real", out_dir=LATEX_PICS_DIR)
    yr0, yr1 = years_bc[0], years_bc[-1]
    save_figure_tex(
        "ipp_cumulative_real",
        caption=(
            f"ČR: kumulativní index nominálních a~reálných mezd ({yr0}\u00a0=\u00a0100), "
            f"{yr0}\u2013{yr1}. "
            "Plné čáry\u00a0= sjednaný nárůst v~KS (IPP/MPSV); "
            "přerušované čáry\u00a0= skutečný nárůst mzdových nákladů (Eurostat LCI); "
            "tečkovaná čára\u00a0= cenová hladina HICP. "
            "Reálné řady jsou deflované indexem HICP."
        ),
        label="fig:ipp_cumulative_real",
        width=r"0.95\linewidth",
        cite_key="mpsv_ipp",
    )
else:
    print("Figure B skipped – insufficient overlapping data.")

# ══════════════════════════════════════════════════════════════════════════════
# Figure C – Gap: actual CZ LCI wage growth minus IPP negotiated increase
# ══════════════════════════════════════════════════════════════════════════════
years_c = _common_years(ipp, lci_growth)
if years_c:
    gap_vals = [lci_growth[y] - ipp[y] for y in years_c]
    bar_colors = ["#2CA02C" if g >= 0 else "#D62728" for g in gap_vals]

    fig_c, ax_c = plt.subplots(figsize=cm2in(15, 9))

    bars = ax_c.bar(
        years_c, gap_vals,
        color=bar_colors, alpha=0.75, width=0.65, zorder=3,
    )
    ax_c.axhline(0, color="gray", linewidth=1.0, linestyle="-", zorder=4)

    # Value annotations
    for bar, val in zip(bars, gap_vals):
        va     = "bottom" if val >= 0 else "top"
        offset = 0.12 if val >= 0 else -0.12
        ax_c.text(
            bar.get_x() + bar.get_width() / 2,
            val + offset,
            f"{val:+.1f}",
            ha="center", va=va, fontsize=FONT_SIZE - 1.5,
        )

    ax_c.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda y, _: f"{y:+.0f}\u00a0p.p.")
    )
    ax_c.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
    ax_c.set_xlabel("rok", fontsize=FONT_SIZE)
    ax_c.set_ylabel("Skutečný nárůst − sjednaný nárůst (p.p.)", fontsize=FONT_SIZE)
    ax_c.set_title(
        "CZ: rozdíl mezi skutečným nárůstem mzdových nákladů (Eurostat LCI)\n"
        "a sjednaným nárůstem v kolektivních smlouvách (IPP/MPSV)",
        fontsize=FONT_SIZE,
    )

    green_patch = mpatches.Patch(
        color="#2CA02C", alpha=0.75,
        label="Trh platí více, než bylo sjednáno v KS",
    )
    red_patch = mpatches.Patch(
        color="#D62728", alpha=0.75,
        label="Sjednáno více, než skutečný nárůst trhu",
    )
    ax_c.legend(handles=[green_patch, red_patch], frameon=False, fontsize=FONT_SIZE - 1)
    ax_c.set_xlim(years_c[0] - 0.5, years_c[-1] + 0.5)

    savefig(fig_c, "ipp_actual_vs_neg_gap", out_dir=LATEX_PICS_DIR)
    yr0, yr1 = years_c[0], years_c[-1]
    save_figure_tex(
        "ipp_actual_vs_neg_gap",
        caption=(
            "ČR: rozdíl mezi skutečným meziroční nárůstem mzdových nákladů "
            "(Eurostat LCI) a~mediánem sjednaného nárůstu základní mzdy v~KS "
            f"(MPSV/IPP), {yr0}\u2013{yr1}. "
            "Kladné hodnoty (zeleně) indikují, že zaměstnavatelé zvyšují mzdy "
            "nad rámec sjednaného minima; záporné hodnoty (červeně) by naznačovaly "
            "nedodržování sjednaných nárůstů."
        ),
        label="fig:ipp_actual_vs_neg_gap",
        width=r"0.95\linewidth",
        cite_key="mpsv_ipp",
    )
else:
    print("Figure C skipped – no overlapping IPP + LCI years.")

print("Done.")
