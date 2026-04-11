r"""
Labour Market Policy (LMP) expenditure as % of GDP – CZ, AT, DE, DK, PL, SK.

Key message for the thesis: DK spends ~2 % of GDP on active labour-market
policy; CZ spends ~0.3 %.  The "flexicurity" triangle only works with
adequate income-support and re-skilling investment.

Data source: Eurostat, ``lmp_expsumm``
  LMP summary expenditure by type of action.
  Dimensions: freq · exptype · unit · geo
  Filter used: freq=A, exptype=LMP_TOT (total LMP), unit=PC_GDP.

Output
------
  pics/lmp_expenditure.pdf
  latex/texparts/lmp_expenditure.tex  ← \input{} this in main.tex

Run
---
    python analyses/lmp_expenditure.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import FONT_SIZE, LATEX_PICS_DIR
from stattool.fetch import fetch_oecd
from stattool.dataset import Dataset
from stattool.style import apply_style, savefig, save_figure_tex
from statout.timeline import timeline

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
START_YEAR = 2004
HIGHLIGHT = ["CZ", "DK"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style()

# ── 1. Download ───────────────────────────────────────────────────────────────
# OECD LMPEXP: Labour Market Policy expenditure by programme and country.
# Programme _T = total LMP; UNIT_MEASURE PT_B1GQ = % of GDP.
# (Eurostat lmp_expsumm was discontinued; OECD covers same EU countries.)
path = fetch_oecd("LMPEXP", start_period=START_YEAR)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
import pandas as pd
raw = pd.read_csv(path)
# Keep total programme, expenditure measure, % of GDP
raw = raw[
    (raw["MEASURE"] == "EXP") &
    (raw["UNIT_MEASURE"] == "PT_B1GQ") &
    (raw["PROGRAMME"] == "_T")
].copy()
raw = raw.rename(columns={"REF_AREA": "geo", "TIME_PERIOD": "time", "OBS_VALUE": "value"})
from stattool.dataset import _OECD_ISO3_TO_ISO2  # reuse mapping
raw["geo"] = raw["geo"].map(lambda x: _OECD_ISO3_TO_ISO2.get(str(x).upper(), str(x)))
raw = raw[["geo", "time", "value"]].dropna(subset=["value"])
# Build ds_all (all countries) for grey cloud; ds_6 for highlighted lines
ds_all = Dataset(raw, name="Výdaje na APZ", unit="% HDP", source_url="OECD/LMPEXP")
# Filter OECD aggregate
ds_all.df = ds_all.df[ds_all.df["geo"] != "OECD"].copy()

print(f"All countries: {len(ds_all.countries)}  |  Years: {ds_all.years[0]}–{ds_all.years[-1]}")

# ── 3. Timeline figure ────────────────────────────────────────────────────────
fig = timeline(
    ds_all,
    countries=COUNTRIES,
    title="Výdaje na aktivní politiku zaměstnanosti",
    ylabel="výdaje na aktivní politiku zaměstnanosti [% HDP]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    label_offsets={"SK": (4, 5), "PL": (4, -5)},
    show_eu_avg=False,
    background_eu=True,
)
fig.axes[0].set_xlim(START_YEAR, ds_all.years[-1])
fig.axes[0].set_ylim(0, 7.5)

# COVID-19 annotation: 2020 spike was caused by emergency short-time work
# schemes (Kurzarbeit/furlough), extended unemployment benefits, and wage
# subsidies. DK 'Lønkompensation' covered 75% of wages — hence the highest spike.
_ax = fig.axes[0]
_ax.axvline(2020, color="#CC4444", linewidth=0.8, linestyle="--", alpha=0.7, zorder=2)
_ax.text(2020.2, 6.8, "COVID-19", fontsize=FONT_SIZE - 1,
         color="#CC4444", alpha=0.85, va="top")

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig(fig, "lmp_expenditure", out_dir=LATEX_PICS_DIR)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex(
    "lmp_expenditure",
    caption=(
        f"Výdaje na aktivní politiku zaměstnanosti jako podíl HDP (\\%), "
        f"bez korekce v~PPS (podíl HDP je bězrozměrný poměr), "
        f"{START_YEAR}--{ds_all.years[-1]}. Šedé linie = ostatní evropské země."
    ),
    label="fig:lmp_expenditure",
    width=r"0.95\linewidth",
    cite_key="oecd_lmpexp_PC_GDP",
)

# ── 6. Second variant: 2004–latest (cropped x-axis) ──────────────────────────
YEAR_2004 = 2004

fig2 = timeline(
    ds_all,
    countries=COUNTRIES,
    title=f"Výdaje na aktivní politiku zaměstnanosti ({YEAR_2004}–{ds_all.years[-1]})",
    ylabel="výdaje na aktivní politiku zaměstnanosti [% HDP]",
    highlight=HIGHLIGHT,
    annotate_last=True,
    label_offsets={"SK": (4, 5), "PL": (4, -5)},
    show_eu_avg=False,
    background_eu=True,
)
fig2.axes[0].set_xlim(YEAR_2004, ds_all.years[-1])
fig2.axes[0].set_ylim(0, 5.0)

_ax2 = fig2.axes[0]
_ax2.axvline(2020, color="#CC4444", linewidth=0.8, linestyle="--", alpha=0.7, zorder=2)
_ax2.text(2020.2, 4.7, "COVID-19", fontsize=FONT_SIZE - 1, color="#CC4444", alpha=0.85, va="top")

savefig(fig2, "lmp_expenditure_2004", out_dir=LATEX_PICS_DIR)
save_figure_tex(
    "lmp_expenditure_2004",
    caption=(
        f"Výdaje na aktivní politiku zaměstnanosti jako podíl HDP (\\%), "
        f"bez korekce v~PPS (podíl HDP je bězrozměrný poměr), "
        f"2004--{ds_all.years[-1]}. Šedé linie = ostatní evropské země."
    ),
    label="fig:lmp_expenditure_2004",
    width=r"0.95\linewidth",
    cite_key="oecd_lmpexp_PC_GDP",
)

print("Done.")
