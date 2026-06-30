r"""
Employment share in foreign-controlled multinational enterprises -- EU choropleth.

Shows the percentage of employment in enterprises controlled by foreign parents
(inward FATS) as a share of total employment.  Used in the labour-market-context
section to document CZ's high attractiveness to multinational employers, which
coexists with below-average wage levels and reinforces the structural wage argument.

Data source: Eurostat ``egr_emp`` (Foreign Affiliates Statistics, inward)
  Enterprise group type: FOR_C (foreign-controlled)
  Scope: all NACE activities (TOTAL), all size classes (TOTAL)
  Unit: PC_EMP_TOT (% of total employment)

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
# egr_emp: Employment in enterprise groups (inward FATS)
# Download without dimension filter — the dimension names and values are
# printed below on first run so the filter dict can be verified/adjusted.
path = fetch_eurostat("egr_emp", start_period=2015)

# ── 2. Parse & filter ─────────────────────────────────────────────────────────
raw = pd.read_csv(path, na_values=["", ":", ": "])

# Debug: inspect available dimension values on first run.
# Adjust FILTERS below if column names differ from what is printed.
_meta_cols = {"DATAFLOW", "LAST UPDATE", "OBS_VALUE", "OBS_FLAG",
              "CONF_STATUS", "TIME_PERIOD"}
print("=== egr_emp: available columns ===")
for col in raw.columns:
    if col not in _meta_cols:
        uniq = sorted(raw[col].dropna().unique())[:12]
        print(f"  {col}: {uniq}")

# ── Filter for foreign-controlled enterprises, total NACE, total size class,
#    % of total employment.  Adjust these values if the debug output above
#    shows different codes (e.g. 'egr_grp' instead of 'ent_grp').
FILTERS = {
    "unit": "PC_EMP_TOT",   # % of total employment
    "nace_r2": "TOTAL",     # all NACE activities
    "sizecls": "TOTAL",     # all size classes
}
# The enterprise-group-type column selects foreign-controlled enterprises.
# Try common Eurostat names in order of likelihood:
_type_col = None
for _candidate in ("ent_grp", "egr_grp", "egr_ent", "entity", "ctrl_grp"):
    if _candidate in raw.columns:
        _type_col = _candidate
        break

if _type_col is None:
    raise RuntimeError(
        "Cannot find the enterprise-group-type column in egr_emp.\n"
        "Available columns: " + ", ".join(raw.columns.tolist()) + "\n"
        "Add the correct column name to the _candidate list above."
    )

print(f"\nUsing enterprise-type column: '{_type_col}'")
print(f"Available {_type_col} values: {sorted(raw[_type_col].dropna().unique())}")

# Foreign-controlled: try common value codes in order of likelihood:
_for_c_value = None
for _v in ("FOR_C", "FOR_CTRL", "FOREIGN", "INWARD", "FC"):
    if _v in raw[_type_col].values:
        _for_c_value = _v
        break

if _for_c_value is None:
    raise RuntimeError(
        f"Cannot find the foreign-controlled enterprise value in column '{_type_col}'.\n"
        f"Available values: {sorted(raw[_type_col].dropna().unique())}\n"
        "Add the correct value to the _for_c_value list above."
    )

print(f"Using enterprise-type value: '{_for_c_value}'")

# Apply filters
FILTERS[_type_col] = _for_c_value

df = raw.rename(columns={"TIME_PERIOD": "time", "OBS_VALUE": "value"})
df["geo"] = df["geo"].replace({"EL": "GR", "UK": "GB"})

for col, val in FILTERS.items():
    if col in df.columns:
        df = df[df[col] == val]

df = df[["geo", "time", "value"]].dropna(subset=["value"])

if df.empty:
    raise RuntimeError(
        "Filtered DataFrame is empty — check FILTERS dict above against the "
        "debug output and verify the dataset downloaded correctly."
    )

ds = Dataset(
    df,
    name="Podíl zaměstnanosti v zahraničních podnicích",
    unit="% z celkové zaměstnanosti",
    source_url="Eurostat/egr_emp",
)

print(f"\nCountries: {len(ds.countries)}  |  Years: {ds.years}")
print(f"Display year (latest): {ds.latest_year}")

# ── 3. Choropleth map ─────────────────────────────────────────────────────────
_values = (
    ds.df[ds.df["time"] <= ds.latest_year]
    .sort_values("time").groupby("geo")["value"].last().to_dict()
)
_vmax = max(_values.values())

NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]

STRINGS = {
    "title": f"Zaměstnanost v zahraničních podnicích ({ds.latest_year})",
    "colorbar_label": r"podíl zaměstnanosti [\%]",
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
        r"Podíl zaměstnanosti v~podnicích se zahraniční kontrolou na~celkové "
        r"zaměstnanosti, mapa Evropy, "
        f"{ds.latest_year}."
    ),
    label="fig:eu_mne_mapa",
    resizebox_width=r"\linewidth",
    cite_key=CITE_KEY,
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
