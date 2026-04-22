r"""
Self-employment rate choropleth map of Europe.

Data source: Eurostat lfsa_egaps (Employed persons by professional status)
  Computes: self-employed (wstatus=SELF) / total employed (wstatus=EMP) × 100
  Sex: T (both), Age: Y15--74, Unit: THS_PER (thousands) → ratio computed here.

Output
------
  pics/python/eu_osvc_mapa.pdf
  latex/texparts/python/eu_osvc_mapa.tex

Run
---
    python analyses/eu_osvc_mapa.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import LATEX_PICS_DIR
from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
# Fetch both EMP (total employed) and SELF (self-employed) in thousands.
# Trailing dot in filter = all geo; EMP+SELF fetches both wstatus values.
path = fetch_eurostat(
    "lfsa_egaps",
    "A.THS_PER.T.Y15-74.EMP+SELF.",
    start_period=2015,
)

# ── 2. Parse & compute ratio ──────────────────────────────────────────────────
raw = pd.read_csv(path)

emp = (
    raw[raw["wstatus"] == "EMP"][["geo", "TIME_PERIOD", "OBS_VALUE"]]
    .rename(columns={"OBS_VALUE": "emp"})
)
self_emp = (
    raw[raw["wstatus"] == "SELF"][["geo", "TIME_PERIOD", "OBS_VALUE"]]
    .rename(columns={"OBS_VALUE": "self"})
)
merged = emp.merge(self_emp, on=["geo", "TIME_PERIOD"]).dropna()
merged["value"] = merged["self"] / merged["emp"] * 100
merged = merged.rename(columns={"TIME_PERIOD": "time"})
merged = merged[["geo", "time", "value"]]

ds = Dataset(
    merged,
    name="Podíl OSVČ",
    unit="%",
    source_url="Eurostat lfsa_egaps",
)

print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}--{ds.years[-1]}")
print(f"Display year: {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
_values = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmin = min(_values.values())
_vmax = max(_values.values())

STRINGS = {
    "title": f"Podíl \\acp{{OSVČ}} na zaměstnanosti ({ds.latest_year})",
    "colorbar_label": r"podíl \acp{OSVČ} [\%]",
}

fig = choropleth(
    ds,
    year=ds.latest_year,
    title=STRINGS["title"],
    colorbar_label=STRINGS["colorbar_label"],
    cmap="RdYlGn_r",
    vmin=_vmin,
    vmax=_vmax,
    label_countries=True,
    highlight_colorbar=["CZ", "DK", "AT", "DE", "PL", "SK"],
)

apply_geo_labels_pgf(fig.axes[0], halo=True, values=_values, tooltip_fmt="{:.1f}")

# ── 4. Save figure ───────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_osvc_mapa", strings=STRINGS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_osvc_mapa",
    caption=f"Podíl \\acs{{OSVČ}} na celkové zaměstnanosti, EU mapa, {ds.latest_year}.",
    label="fig:eu_osvc_mapa",
    resizebox_width=r"\linewidth",
    cite_keys="eurostat_lfsa_egaps",
    strings=STRINGS,
)

print("Done.")
