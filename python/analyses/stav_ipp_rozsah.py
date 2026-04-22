r"""
KS content breadth --- IPP-derived timeline (2007--2025).

Three indicators tracked from the MPSV IPP annual workbooks:

1. Formal wage-tariff scale (``mzda_tarify`` A1a) -- share of CAs
   establishing a hierarchical wage structure (12-grade or other monthly TS).
2. Concretised union operating conditions
   (``spoluprace_smluvnich_stran`` A19a, col 9).
3. Union release time (``spoluprace_smluvnich_stran`` A19a, col 7).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from config import FONT_SIZE, PALETTE
from stattool.fetch import fetch_ipp
from stattool.style import (
    add_pgf_tooltips,
    apply_style_pgf,
    cm2in,
    save_figure_tex_pgf,
    savefig_pgf,
)

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

apply_style_pgf()

# ── Parameters ────────────────────────────────────────────────────────────────
START_YEAR = 2007
END_YEAR = 2025

NUDGE_LABELS = [
    ("Tarif", r"mzdová stupnice"),
    ("Podminky", r"podmínky činnosti"),
    ("Uvolneni", r"uvolnění zástupce"),
    ("Krize", r"fin. krize"),
    ("Covid", r"COVID-19"),
    ("Inflace", r"inflační šok"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_celkem_row(df: pd.DataFrame) -> int | None:
    for ri in range(df.shape[0]):
        for lc in range(min(2, df.shape[1])):
            if str(df.iloc[ri, lc]).strip().lower() == "celkem":
                return ri
    return None


def _extract_tariff_coverage(path: Path, year: int) -> float | None:
    try:
        df = pd.read_excel(path, sheet_name="A1a", header=None)
    except Exception as exc:
        log.warning("mzda_tarify %d: cannot read A1a: %s", year, exc)
        return None
    celkem = _find_celkem_row(df)
    if celkem is None:
        return None
    try:
        v_12grade = pd.to_numeric(df.iloc[celkem, 12], errors="coerce")
        v_other = pd.to_numeric(df.iloc[celkem, 14], errors="coerce")
    except IndexError:
        return None
    total = 0.0
    if pd.notna(v_12grade) and v_12grade >= 0:
        total += float(v_12grade)
    if pd.notna(v_other) and v_other >= 0:
        total += float(v_other)
    return total if 0 < total <= 100 else None


def _extract_spoluprace(path: Path, year: int) -> tuple[float | None, float | None]:
    try:
        df = pd.read_excel(path, sheet_name="A19a", header=None)
    except Exception as exc:
        log.warning("spoluprace %d: cannot read A19a: %s", year, exc)
        return None, None
    celkem = _find_celkem_row(df)
    if celkem is None:
        return None, None

    def safe(col: int) -> float | None:
        try:
            v = pd.to_numeric(df.iloc[celkem, col], errors="coerce")
            return float(v) if pd.notna(v) and 0 < float(v) <= 100 else None
        except IndexError:
            return None

    return safe(9), safe(7)


# ── 1. Download and parse mzda_tarify ─────────────────────────────────────────
print(f"Fetching mzda_tarify {START_YEAR}--{END_YEAR} …")
tariff: dict[int, float] = {}
for yr in range(START_YEAR, END_YEAR + 1):
    try:
        path_mt = fetch_ipp(yr, "mzda_tarify")
        val = _extract_tariff_coverage(path_mt, yr)
        if val is not None:
            tariff[yr] = val
    except Exception as exc:
        print(f"  mzda_tarify {yr}: skipped ({exc})")

# ── 2. Download and parse spoluprace_smluvnich_stran ──────────────────────────
print(f"Fetching spoluprace {START_YEAR}--{END_YEAR} …")
conditions: dict[int, float] = {}
release: dict[int, float] = {}
for yr in range(START_YEAR, END_YEAR + 1):
    try:
        path_sp = fetch_ipp(yr, "spoluprace_smluvnich_stran")
        c, r = _extract_spoluprace(path_sp, yr)
        if c is not None:
            conditions[yr] = c
        if r is not None:
            release[yr] = r
    except Exception as exc:
        print(f"  spoluprace {yr}: skipped ({exc})")

if not (tariff or conditions or release):
    print("No IPP breadth data --- exiting.")
    sys.exit(0)

all_years = sorted(set(tariff) | set(conditions) | set(release))
LAST_YEAR = max(2025, max(all_years))

# ── 3. Build figure ───────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=cm2in(15, 9))

SERIES = [
    ("mzdová stupnice",     tariff,     PALETTE[0], "-"),
    ("podmínky činnosti",  conditions, PALETTE[1], "--"),
    ("uvolnění zástupce",  release,    PALETTE[2], "--"),
]

for label, data, color, ls in SERIES:
    if not data:
        continue
    ys = sorted(data)
    vals = [data[y] for y in ys]
    ax.plot(ys, vals, color=color, linewidth=1.8, linestyle=ls, zorder=3)
    last_y = ys[-1]
    last_v = data[last_y]
    ax.annotate(
        label,
        xy=(LAST_YEAR, last_v),
        xytext=(-2, 4),
        textcoords="offset points",
        fontsize=FONT_SIZE,
        ha="right",
        va="bottom",
        color=color,
    )

# Event annotations: vertical lines + label just above x-axis
_EVENTS = [
    (2008, "fin. krize"),
    (2020, "COVID-19"),
    (2022, "inflační šok"),
]
for yr, label in _EVENTS:
    if yr < START_YEAR or yr > LAST_YEAR:
        continue
    ax.axvline(yr, color="grey", linewidth=0.6, linestyle="--", alpha=0.5, zorder=1)
    ax.annotate(
        label,
        xy=(yr, 0),
        xytext=(2, 4),
        textcoords="offset points",
        fontsize=FONT_SIZE - 1,
        color="grey",
        ha="left",
        va="bottom",
    )

ax.set_xlabel("rok")
ax.set_ylabel(r"podíl \acs{KS} [\%]")
ax.set_xlim(START_YEAR, LAST_YEAR)
ax.set_ylim(0, 100)
ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))

STRINGS = {"title": r"Obsah \acs{KS} (\acs{geo-CZ})"}
ax.set_title(STRINGS["title"])

# ── 4. Tooltips ───────────────────────────────────────────────────────────────
_pivot = pd.DataFrame({
    "Tarif": pd.Series(tariff),
    "Podminky": pd.Series(conditions),
    "Uvolneni": pd.Series(release),
}).sort_index()
add_pgf_tooltips(ax, _pivot, fmt="{:.1f}")

# ── 5. Save ───────────────────────────────────────────────────────────────────
year_range = f"{START_YEAR}--{LAST_YEAR}"
savefig_pgf(fig, "stav_ipp_rozsah", strings=STRINGS, nudge_labels=NUDGE_LABELS)
save_figure_tex_pgf(
    "stav_ipp_rozsah",
    caption=rf"Obsah \acs{{KS}}, \acs{{geo-CZ}}, {year_range}.",
    cite_keys="mpsv_ipp",
    label="fig:stav_ipp_rozsah",
    resizebox_width=r"\linewidth",
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)
print("Done.")
