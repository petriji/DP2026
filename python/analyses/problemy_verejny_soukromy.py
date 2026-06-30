r"""
CZ public vs private sector wage comparison using ISPV 2025 data.

ISPV publishes two parallel wage surveys:

* **Mzdová sféra** (MZS, *podnikatelská sféra*): private / business sector
  employees paid a *mzda* (wage) -- ~3 million workers.
* **Platová sféra** (PLS, *nepodnikatelská sféra*): public / non-business sector
  employees paid a *plat* (salary) -- ~700 thousand workers.

The 2025 annual workbooks use a new URL scheme (GUID-based) rather than the
older ``/files/ISPV_25H2.xlsx`` pattern.  This script fetches them directly.

Figure A -- ``rscp_public_private_sector``
    Grouped horizontal bar chart: median monthly wage by CZ-NACE section for
    both spheres (2025).  Where a sphere has no employees in a sector (too few
    to publish or structurally absent), no bar is drawn.  IQR (P25--P75) shown
    as error markers.

    Argumentation: The public--private wage gap is NOT uniform across sectors.
    Public sector workers earn more in health (Q) and less in ICT (J) and
    public administration (O) vs their private-sector counterparts ---
    illustrating why blanket collective-agreement extension is more complex
    than a single economy-wide comparison suggests.

Figure B -- ``rscp_public_private_distribution``
    Dual box-and-whisker (P10/P25/P50/P75/P90) for the total MZS vs total PLS
    side-by-side, highlighting the overall wage distribution shape inequality.

Data sources
------------
MZS (2025): ISPV national workbook, mzdová sféra ČR, rok 2025
PLS (2025): ISPV national workbook, platová sféra ČR, rok 2025
Source: TREXIMA / MPSV, published 25. 3. 2026, https://www.ispv.cz

Output
------
  pics/python/problemy_verejny_soukromy.pdf
  pics/python/problemy_verejny_soukromy_dist.pdf
  latex/texparts/python/problemy_verejny_soukromy.tex
  latex/texparts/python/problemy_verejny_soukromy_dist.tex

Run
---
    python analyses/public_private_wages.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from config import LATEX_PICS_DIR, FIGURE_TEXT_SIZE, FIGURE_LABEL_SIZE, FIGURE_COMPACT_LABEL_SIZE
from stattool.fetch import fetch
from stattool.style import cm2in, apply_style_pgf, savefig_pgf, save_figure_tex_pgf

apply_style_pgf()

# ── Constants ────────────────────────────────────────────────────────────────
ISPV_YEAR = 2025

# 2025 national ISPV files --- GUID-based URLs (old /files/ scheme returns 2149-byte error page)
_URL_MZS = (
    "https://www.ispv.cz/getattachment/b568f503-6978-4af7-9f8a-d5aef8e46619/"
    "CR_254_MZS-xlsx.aspx?disposition=attachment"
)
_URL_PLS = (
    "https://www.ispv.cz/getattachment/64ad14f0-4b5b-4192-a2e2-3acceedff267/"
    "CR_254_PLS-xlsx.aspx?disposition=attachment"
)

_MZS_COLOR = "#E07B39"   # orange -- private/wage sphere
_PLS_COLOR = "#5B8DB8"   # blue   -- public/salary sphere

# NACE section short labels (Czech)
_NACE_LABEL: dict[str, str] = {
    "A": "Zemědělství",
    "B": "Těžba",
    "C": "Zprac. průmysl",
    "D": "Energie",
    "E": "Voda/odpady",
    "F": "Stavebnictví",
    "G": "Obchod",
    "H": "Doprava",
    "I": "Pohostinství",
    "J": "ICT",
    "K": "Finance",
    "L": "Nemovitosti",
    "M": "Prof. činnosti",
    "N": "Administ./podpora",
    "O": "Veřejná správa",
    "P": "Vzdělávání",
    "Q": "Zdravotnictví",
    "R": "Kultura/zábava",
    "S": "Ostatní",
}


# ════════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════════

def _download_ispv(url: str) -> Path:
    """Download an ISPV Excel workbook and verify it is a real xlsx file."""
    p = fetch(url, suffix=".xlsx")
    # Validate: xlsx is a zip, starts with PK magic bytes
    with open(p, "rb") as f:
        hdr = f.read(4)
    if hdr[:2] != b"PK":
        raise ValueError(
            f"Downloaded file is not a valid xlsx (size={p.stat().st_size}). "
            "Server may have returned an error HTML page."
        )
    return p


def _parse_nace_sheet(path: Path, sheet: str) -> pd.DataFrame:
    """Extract NACE sector wage rows from an ISPV M5_6 sheet.

    The sheet contains two tables:
    * M5 (rows 0-14): wages by employee citizenship
    * M6 (rows ~16+): wages by CZ-NACE section (A-S)

    Returns a DataFrame with columns:
        nace_code, sector_name, emp_tis, median, yoy_pct, p10, p25, p75, p90
    """
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl", header=None)

    rows = []
    nace_letters = set("ABCDEFGHIJKLMNOPQRS")
    for _, row in df.iterrows():
        code = str(row.iloc[0]).strip()
        # Single uppercase letter and appears in NACE codes
        if code not in nace_letters:
            continue
        # col1 = sector name, col2 = emp count, col3 = median, etc.
        name = str(row.iloc[1]).replace("\xa0", " ").strip()
        vals = [pd.to_numeric(row.iloc[i], errors="coerce") for i in range(2, 10)]
        emp, med, yoy, p10, p25 = vals[0], vals[1], vals[2], vals[3], vals[4]
        # P75 is the 6th value (index 5), P90 is 7th (index 6), if present
        p75 = vals[5] if len(vals) > 5 else np.nan
        p90 = vals[6] if len(vals) > 6 else np.nan
        rows.append(
            dict(
                nace_code=code,
                sector_name=name,
                emp_tis=emp,
                median=med,
                yoy_pct=yoy,
                p10=p10,
                p25=p25,
                p75=p75,
                p90=p90,
            )
        )
    return pd.DataFrame(rows)


def _parse_overall(path: Path, sheet: str) -> dict:
    """Extract headline percentile statistics from an ISPV M0 sheet.

    Returns a dict with keys: emp_tis, p10, p25, median, p75, p90, mean
    """
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl", header=None)
    result: dict[str, float] = {}
    for _, row in df.iterrows():
        for j in range(df.shape[1] - 1):
            cell = str(row.iloc[j]).lower()
            val = pd.to_numeric(row.iloc[j + 1], errors="coerce")
            if pd.isna(val):
                continue
            if "medián" in cell or "median" in cell:
                result.setdefault("median", val)
            elif "průměr" in cell or "prumer" in cell:
                result.setdefault("mean", val)
            elif "1. decil" in cell or "1.decil" in cell:
                result.setdefault("p10", val)
            elif "1. kvartil" in cell or "1.kvartil" in cell:
                result.setdefault("p25", val)
            elif "3. kvartil" in cell or "3.kvartil" in cell:
                result.setdefault("p75", val)
            elif "9. decil" in cell or "9.decil" in cell:
                result.setdefault("p90", val)
            elif "počet zaměst" in cell or "počet\nzaměst" in cell:
                result.setdefault("emp_tis", val)
    return result


# ════════════════════════════════════════════════════════════════════════════
# Data download
# ════════════════════════════════════════════════════════════════════════════
print("Fetching ISPV 2025 national workbooks …")
p_mzs = p_pls = None

try:
    p_mzs = _download_ispv(_URL_MZS)
    print(f"  MZS (private): {p_mzs.name}  ({p_mzs.stat().st_size:,} bytes)")
except Exception as exc:
    print(f"  MZS download failed: {exc}")

try:
    p_pls = _download_ispv(_URL_PLS)
    print(f"  PLS (public):  {p_pls.name}  ({p_pls.stat().st_size:,} bytes)")
except Exception as exc:
    print(f"  PLS download failed: {exc}")

if p_mzs is None and p_pls is None:
    print("Both workbooks unavailable -- skipping figures.")
    sys.exit(0)


# ════════════════════════════════════════════════════════════════════════════
# Parse data
# ════════════════════════════════════════════════════════════════════════════
df_mzs = df_pls = None

if p_mzs is not None:
    try:
        xl = pd.ExcelFile(p_mzs, engine="openpyxl")
        sheet_m56 = next((s for s in xl.sheet_names if "M5_6" in s or "M5" in s), None)
        sheet_m0  = next((s for s in xl.sheet_names if s.endswith("-M0")), None)
        if sheet_m56:
            df_mzs = _parse_nace_sheet(p_mzs, sheet_m56)
            print(f"  MZS sectors parsed: {len(df_mzs)}")
        overall_mzs = _parse_overall(p_mzs, sheet_m0) if sheet_m0 else {}
    except Exception as exc:
        print(f"  MZS parse error: {exc}")

if p_pls is not None:
    try:
        xl = pd.ExcelFile(p_pls, engine="openpyxl")
        sheet_m56 = next((s for s in xl.sheet_names if "M5_6" in s or "M5" in s), None)
        sheet_m0  = next((s for s in xl.sheet_names if s.endswith("-M0")), None)
        if sheet_m56:
            df_pls = _parse_nace_sheet(p_pls, sheet_m56)
            print(f"  PLS sectors parsed: {len(df_pls)}")
        overall_pls = _parse_overall(p_pls, sheet_m0) if sheet_m0 else {}
    except Exception as exc:
        print(f"  PLS parse error: {exc}")


# ════════════════════════════════════════════════════════════════════════════
# Figure A -- Sector comparison (grouped horizontal bars)
# ════════════════════════════════════════════════════════════════════════════
print("\nBuilding Figure A: sector wage comparison …")

# Merge on NACE code; keep all codes that appear in either sphere
all_codes = sorted(
    set(df_mzs["nace_code"].tolist() if df_mzs is not None else [])
    | set(df_pls["nace_code"].tolist() if df_pls is not None else [])
)

rows_plot = []
for code in all_codes:
    label = _NACE_LABEL.get(code, code)
    mrow = df_mzs[df_mzs["nace_code"] == code].iloc[0] if (
        df_mzs is not None and code in df_mzs["nace_code"].values
    ) else None
    prow = df_pls[df_pls["nace_code"] == code].iloc[0] if (
        df_pls is not None and code in df_pls["nace_code"].values
    ) else None
    m_med = float(mrow["median"])      if mrow is not None and pd.notna(mrow["median"])      else np.nan
    m_p25 = float(mrow["p25"])         if mrow is not None and pd.notna(mrow["p25"])         else np.nan
    m_p75 = float(mrow["p75"])         if mrow is not None and pd.notna(mrow["p75"])         else np.nan
    p_med = float(prow["median"])      if prow is not None and pd.notna(prow["median"])      else np.nan
    p_p25 = float(prow["p25"])         if prow is not None and pd.notna(prow["p25"])         else np.nan
    p_p75 = float(prow["p75"])         if prow is not None and pd.notna(prow["p75"])         else np.nan
    rows_plot.append(dict(
        code=code, label=label,
        m_med=m_med, m_p25=m_p25, m_p75=m_p75,
        p_med=p_med, p_p25=p_p25, p_p75=p_p75,
    ))

# Sort A-S (already alphabetical)
df_plot = pd.DataFrame(rows_plot)[::-1].reset_index(drop=True)  # top=A, bottom=S reversed for barh

n = len(df_plot)
bar_h = 0.35
y = np.arange(n)

fig_a, ax_a = plt.subplots(figsize=cm2in(18, max(12, n * 0.75)))

for i, row in df_plot.iterrows():
    # MZS bar
    if pd.notna(row["m_med"]):
        ax_a.barh(y[i] + bar_h / 2, row["m_med"], height=bar_h,
                  color=_MZS_COLOR, alpha=0.85, edgecolor="white", linewidth=0.4,
                  zorder=1)
        # IQR error bar
        if pd.notna(row["m_p25"]) and pd.notna(row["m_p75"]):
            ax_a.errorbar(
                row["m_med"], y[i] + bar_h / 2,
                xerr=[[row["m_med"] - row["m_p25"]], [row["m_p75"] - row["m_med"]]],
                fmt="none", color="#7B3B11", linewidth=1.2, capsize=2,
            )
    # PLS bar
    if pd.notna(row["p_med"]):
        ax_a.barh(y[i] - bar_h / 2, row["p_med"], height=bar_h,
                  color=_PLS_COLOR, alpha=0.85, edgecolor="white", linewidth=0.4,
                  zorder=1)
        if pd.notna(row["p_p25"]) and pd.notna(row["p_p75"]):
            ax_a.errorbar(
                row["p_med"], y[i] - bar_h / 2,
                xerr=[[row["p_med"] - row["p_p25"]], [row["p_p75"] - row["p_med"]]],
                fmt="none", color="#1B4F72", linewidth=1.2, capsize=2,
            )

ax_a.set_yticks(y)
ax_a.set_yticklabels(
    [f"{row['code']}  {row['label']}" for _, row in df_plot.iterrows()],
    fontsize=FIGURE_LABEL_SIZE,
)
ax_a.tick_params(axis="x", labelsize=FIGURE_LABEL_SIZE)
ax_a.xaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, _: f"{x / 1_000:.0f}")
)
ax_a.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
STRINGS_A = {
    "title": rf"\acs{{geo-CZ}}: mediánová mzda/plat podle odvětví \acs{{NACE}} ({ISPV_YEAR}); chybové úsečky P25--P75 (\acs{{IQR}})",
    "xlabel": r"hrubá měsíční mzda/plat [tis.\,\si{\czk}]",
}
ax_a.set_xlabel(STRINGS_A["xlabel"], fontsize=FIGURE_LABEL_SIZE)
fig_a.suptitle(STRINGS_A["title"], fontsize=FIGURE_TEXT_SIZE, y=0.995)

def _fmt_tis(v: float | None) -> str:
    if v is None:
        return "?"
    return f"{v:,.0f}".replace(",", "\N{NO-BREAK SPACE}")

# Employee counts: prefer M0 overall row; fall back to sum of NACE-sector rows
# (both come from the same ISPV workbook, so the sum is the natural source of
# truth when _parse_overall cannot locate the aggregate-row count column).
_emp_mzs_raw = overall_mzs.get("emp_tis")
if _emp_mzs_raw is None and df_mzs is not None:
    _emp_mzs_raw = df_mzs["emp_tis"].sum()
_emp_pls_raw = overall_pls.get("emp_tis")
if _emp_pls_raw is None and df_pls is not None:
    _emp_pls_raw = df_pls["emp_tis"].sum()

_emp_mzs: float | None = _emp_mzs_raw if (
    _emp_mzs_raw is not None and not np.isnan(float(_emp_mzs_raw))
) else None
_emp_pls: float | None = _emp_pls_raw if (
    _emp_pls_raw is not None and not np.isnan(float(_emp_pls_raw))
) else None

_mzs_label = f"Mzdová sféra ({_fmt_tis(_emp_mzs)}\N{NO-BREAK SPACE}tis.\N{NO-BREAK SPACE}osob)"
_pls_label = f"Platová sféra ({_fmt_tis(_emp_pls)}\N{NO-BREAK SPACE}tis.\N{NO-BREAK SPACE}osob)"
print(f"  Legend: {_mzs_label} | {_pls_label}")
patch_mzs = mpatches.Patch(color=_MZS_COLOR, alpha=0.85, label=_mzs_label)
patch_pls = mpatches.Patch(color=_PLS_COLOR, alpha=0.85, label=_pls_label)
ax_a.legend(handles=[patch_mzs, patch_pls], frameon=False,
            fontsize=FIGURE_LABEL_SIZE, loc="lower right", markerfirst=False)
ax_a.grid(which="major", axis="x", linestyle=":", linewidth=0.5, alpha=0.6)
ax_a.grid(which="minor", axis="x", linestyle=":", linewidth=0.3, alpha=0.4)
ax_a.tick_params(axis="y", which="minor", left=False)
ax_a.set_axisbelow(True)

fig_a.tight_layout()
savefig_pgf(fig_a, "problemy_verejny_soukromy", strings=STRINGS_A)
save_figure_tex_pgf(
    "problemy_verejny_soukromy",
    caption=f"Mediánová mzda a~plat podle sekce \\acs{{NACE}}, veřejný vs.\\ soukromý sektor, \\acs{{geo-CZ}}, {ISPV_YEAR}",
    cite_keys="mpsv_ispv",
    label="fig:problemy_verejny_soukromy",
    resizebox_width=r"\linewidth",
    cite_key="mpsv_ispv",
    strings=STRINGS_A,
)
print("  Figure A done.")


# ════════════════════════════════════════════════════════════════════════════
# Figure B -- Overall distribution comparison (P10/P25/P50/P75/P90)
# Commented out per user request — commentary merged into
# texparts/commentary/problemy_verejny_soukromy.tex.
# ════════════════════════════════════════════════════════════════════════════
print("\nDone.")

