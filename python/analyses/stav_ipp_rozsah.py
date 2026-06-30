r"""
CA institutional breadth — IPP-derived timeline (2007–2025).

Shows two diverging trends in Czech collective agreements:

Figure A – ``ipp_ca_breadth``
    Three-line timeline (2007–2025) showing the share of surveyed CAs that
    include each of three institutional provisions:

    1. **Formal wage-tariff scale** (``mzda_tarify`` A1a, "Jsou v KS sjednány
       mzdové tarify") — sum of % with 12-grade monthly TS and % with other
       monthly TS.  Documents whether CAs establish a hierarchical wage
       structure, not just agree to a flat % increase.

     2. **Concretized union operating conditions**
         (``spoluprace_smluvnich_stran`` A19a,
         "Konkretizovány podmínky pro výkon činnosti odborové organizace")
         — share of CAs that explicitly define operating conditions for union
         activity. Indicator of procedural quality and enforceability.

    3. **Union release time** (``spoluprace_smluvnich_stran`` A19a,
       "Sjednán časový rozsah uvolnění pro výkon") — paid time off for union
       representatives specified in the CA.  Indicator of institutional
       empowerment of union reps.

    Argumentation:
    - Tariff scale coverage has fallen steadily (~58 % in 2009 → ~38 % in
      2025), signalling that CAs increasingly function as wage-increase
      instruments rather than comprehensive wage-governance frameworks.
        - Union operating-conditions and release-time provisions demonstrate
            stable or growing institutional
      entrenchment of unions within enterprises.
    - Together these trends suggest that Czech CAs retain their procedural
      union-rights architecture while losing their wage-setting infrastructure
      — consistent with the thesis argument that social dialogue in CZ is
      institutionally thin.

Data sources
------------
MPSV IPP ``mzda_tarify`` workbooks (kolektivnismlouvy.cz), sheet A1a.
MPSV IPP ``spoluprace_smluvnich_stran`` workbooks (kolektivnismlouvy.cz), sheet A19a.

Output
------
  pics/python/stav_ipp_rozsah.pdf
  latex/texparts/python/stav_ipp_rozsah.tex

Run
---
    python analyses/stav_ipp_rozsah.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

from config import FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.fetch import fetch_ipp
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

apply_style()

# ── Parameters ────────────────────────────────────────────────────────────────
START_YEAR = 2007
END_YEAR = 2025

# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_celkem_row(df: pd.DataFrame) -> int | None:
    """Return the 0-based row index where col 0 or col 1 equals 'Celkem'."""
    for ri in range(df.shape[0]):
        for lc in range(min(2, df.shape[1])):
            if str(df.iloc[ri, lc]).strip().lower() == "celkem":
                return ri
    return None


def _extract_tariff_coverage(path: Path, year: int) -> float | None:
    """Return total % of CAs with a formal monthly wage tariff scale.

    Sources sheet A1a from mzda_tarify.  Sums the '% KS' columns for
    12-grade monthly TS (col 12) and other monthly TS (col 14), which are
    consistent from 2009 onwards.  Returns None for earlier years where the
    tariff section is absent.
    """
    try:
        df = pd.read_excel(path, sheet_name="A1a", header=None)
    except Exception as exc:
        log.warning("mzda_tarify %d: cannot read A1a: %s", year, exc)
        return None

    celkem = _find_celkem_row(df)
    if celkem is None:
        log.warning("mzda_tarify %d: Celkem row not found", year)
        return None

    try:
        v_12grade = pd.to_numeric(df.iloc[celkem, 12], errors="coerce")
        v_other   = pd.to_numeric(df.iloc[celkem, 14], errors="coerce")
    except IndexError:
        # 2007–2008 A1a lacks the tariff columns (shorter layout)
        return None

    total = 0.0
    if pd.notna(v_12grade) and v_12grade >= 0:
        total += float(v_12grade)
    if pd.notna(v_other) and v_other >= 0:
        total += float(v_other)

    # Sanity check: percentage should be in 0–100
    if 0 < total <= 100:
        return total
    return None


def _extract_spoluprace(path: Path, year: int) -> tuple[float | None, float | None]:
    """Return (conditions_pct, release_time_pct) from spoluprace A19a.

    Column mapping (consistent 2007–2025):
        col 9  = % KS with concretized union operating conditions
                         ('Konkretizovány podmínky pro výkon činnosti odborové organizace')
        col 7  = % KS with agreed union release time ('Sjednán čas. rozsah uvolnění')
    """
    try:
        df = pd.read_excel(path, sheet_name="A19a", header=None)
    except Exception as exc:
        log.warning("spoluprace %d: cannot read A19a: %s", year, exc)
        return None, None

    celkem = _find_celkem_row(df)
    if celkem is None:
        log.warning("spoluprace %d: Celkem row not found", year)
        return None, None

    def safe(col: int) -> float | None:
        try:
            v = pd.to_numeric(df.iloc[celkem, col], errors="coerce")
            return float(v) if pd.notna(v) and 0 < float(v) <= 100 else None
        except IndexError:
            return None

    return safe(9), safe(7)


# ── 1. Download and parse mzda_tarify ─────────────────────────────────────────
print(f"Fetching mzda_tarify {START_YEAR}–{END_YEAR} …")
tariff: dict[int, float] = {}
for yr in range(START_YEAR, END_YEAR + 1):
    try:
        path_mt = fetch_ipp(yr, "mzda_tarify")
        val = _extract_tariff_coverage(path_mt, yr)
        if val is not None:
            tariff[yr] = val
            print(f"  mzda_tarify {yr}: {val:.1f} %")
        else:
            print(f"  mzda_tarify {yr}: tariff columns absent (pre-2009 layout)")
    except Exception as exc:
        print(f"  mzda_tarify {yr}: skipped ({exc})")

# ── 2. Download and parse spoluprace_smluvnich_stran ──────────────────────────
print(f"\nFetching spoluprace {START_YEAR}–{END_YEAR} …")
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
        c_str = f"{c:.1f}" if c is not None else "N/A"
        r_str = f"{r:.1f}" if r is not None else "N/A"
        print(f"  spoluprace {yr}: conditions={c_str} %  release={r_str} %")
    except Exception as exc:
        print(f"  spoluprace {yr}: skipped ({exc})")

if not (tariff or conditions or release):
    print("\nNo IPP breadth data available — exiting without figures.")
    sys.exit(0)

# ── 3. Build figure ────────────────────────────────────────────────────────────
all_years = sorted(
    set(tariff) | set(conditions) | set(release)
)

fig, ax = plt.subplots(figsize=cm2in(15, 8))

colors = [PALETTE[0], PALETTE[1], PALETTE[2]]

if tariff:
    ys = sorted(tariff)
    ax.plot(ys, [tariff[y] for y in ys], "o-",
            color=colors[0], linewidth=1.6, markersize=4,
            label="Formální mzdová tarifní soustava")

if conditions:
    ys = sorted(conditions)
    ax.plot(ys, [conditions[y] for y in ys], "s--",
            color=colors[1], linewidth=1.6, markersize=4,
            label="Konkretizované podmínky činnosti odborové organizace")

if release:
    ys = sorted(release)
    ax.plot(ys, [release[y] for y in ys], "^:",
            color=colors[2], linewidth=1.6, markersize=4,
            label="Sjednané uvolnění odborového zástupce")

# Annotations for key context
_EVENTS = {
    2008: ("Fin. krize", "bottom"),
    2020: ("COVID-19", "top"),
    2022: ("Inflační šok", "bottom"),
}
for yr, (label, va) in _EVENTS.items():
    if yr in all_years:
        ax.axvline(yr, color="grey", linewidth=0.6, linestyle="--", alpha=0.5)
        y_pos = ax.get_ylim()[0] + 2 if va == "bottom" else ax.get_ylim()[1] - 4
        ax.text(yr + 0.15, y_pos, label, fontsize=FONT_SIZE - 2,
                color="grey", va="bottom", rotation=0)

ax.set_xlabel("rok")
ax.set_ylabel("podíl KS [%]")
ax.set_xlim(START_YEAR, END_YEAR)
ax.set_ylim(0, 100)
ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))
ax.legend(loc="center left", fontsize=FONT_SIZE - 1, frameon=False)
ax.set_title(
    "Institucionální obsah kolektivních smluv (ČR)",
    fontsize=FONT_SIZE,
)

fig.tight_layout()

out_pdf = savefig(fig, "stav_ipp_rozsah", out_dir=LATEX_PICS_DIR)
out_tex = save_figure_tex(
    "stav_ipp_rozsah",
    caption=(
        r"Institucionální obsah kolektivních smluv, ČR, 2007--2025. "
        r"\emph{Mzdová stupnice} (plná čára) -- podíl KS "
        r"se sjednanou hierarchickou mzdovou stupnicí (12ti-stupňový nebo jiný "
        r"tarifní systém); zdroj: IPP Mzdový tarify A1a. "
        r"\emph{Konkretizované podmínky činnosti odborové organizace} "
        r"(přerušovaná čára) -- podíl KS s explicitně vymezenými pravidly "
        r"pro výkon odborové činnosti. "
        r"\emph{Uvolnění odborového zástupce} (tečkovaná čára) -- podíl KS "
        r"se sjednaným časovým rozsahem uvolnění pro odborovou práci; "
        r"zdroj: IPP Spolupráce smluvních stran A19a."
    ),
    cite_keys="mpsv_ipp",
    label="fig:stav_ipp_rozsah",
)
print(f"\nSaved: {out_pdf}")
print(f"Saved TeX: {out_tex}")
print("Done.")
