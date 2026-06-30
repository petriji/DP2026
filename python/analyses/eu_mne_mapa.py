r"""
Employment in enterprise groups -- EU choropleth map.

Shows the share of employment in multinational enterprises as a percentage
of total employment. A high share signals a labour market dominated by
large corporate structures.
Used in the labour-market-context section to document that CZ has a large
share of employment in corporate group structures, a situation associated
with stronger resistance to sector-level collective bargaining.

Data source: Eurostat ``egr_emp``
  Dimensions: freq · size_emp · unit · geo
  Filter: unit=PC_EMP (% of total employment), size_emp=TOTAL (all sizes)

Output
------
  python/figures/eu_mne_mapa.pgf
  latex/texparts/figures/eu_mne_mapa.tex   (hand-editable, git-tracked)
  latex/texparts/python/eu_mne_mapa.tex    (one-line wrapper)

Run
---
    python analyses/eu_mne_mapa.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    apply_geo_labels_pgf,
)
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────

CITE_KEY = "eurostat_egr_emp"
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
path = fetch_eurostat("egr_emp", start_period=2015)

# ── 2. Parse & filter ─────────────────────────────────────────────────────────
raw = pd.read_csv(path, na_values=["", ":", ": "])
raw = raw.rename(columns={"TIME_PERIOD": "time", "OBS_VALUE": "value"})
raw["geo"] = raw["geo"].replace({"EL": "GR", "UK": "GB"})

# Filter: % of total employment in enterprise groups (all sizes)
df = raw[(raw["unit"] == "PC_EMP") & (raw["size_emp"] == "TOTAL")].copy()
df = df[["geo", "time", "value"]].dropna(subset=["value"])

if df.empty:
    raise RuntimeError("Filtered DataFrame is empty — check egr_emp download.")

ds = Dataset(
    df,
    name="Podíl zaměstnanosti v podnikových skupinách",
    unit="% celkové zaměstnanosti",
    source_url="Eurostat/egr_emp",
)

print(f"Countries: {len(ds.countries)}  |  Years: {ds.years}")
print(f"Display year (latest): {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
_values = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmax = max(_values.values())

NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]

STRINGS = {
    "title": f"Zaměstnanost v podnikových skupinách ({ds.latest_year})",
    "colorbar_label": r"podíl zaměstnanosti v podnik. skupinách [\%]",
}

fig = choropleth(
    ds,
    year=ds.latest_year,
    title=STRINGS["title"],
    colorbar_label=STRINGS["colorbar_label"],
    cmap="RdYlGn",
    vmin=0,
    vmax=_vmax,
    label_countries=True,
    fill_latest=True,
    highlight_colorbar=COUNTRIES,
)

apply_geo_labels_pgf(fig.axes[0], halo=True, values=_values, tooltip_fmt="{:.1f}")

# ── 4. Save figure ────────────────────────────────────────────────────────────
savefig_pgf(fig, "eu_mne_mapa", strings=STRINGS, nudge_labels=NUDGE_LABELS)

# ── 5. Write LaTeX snippet ────────────────────────────────────────────────────
save_figure_tex_pgf(
    "eu_mne_mapa",
    caption=(
        r"Podíl zaměstnanosti v~nadnárodních korporacích na~celkové zaměstnanosti, "
        r"mapa Evropy, "
        f"{ds.latest_year}. Zdroj dat: Eurostat~\\cite{{{CITE_KEY}}}."
    ),
    label="fig:eu_mne_mapa",
    resizebox_width=r"\linewidth",
    cite_key=CITE_KEY,
    strings=STRINGS,
)

print("\nDone: eu_mne_mapa")
