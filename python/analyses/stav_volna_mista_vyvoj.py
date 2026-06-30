r"""
Vacancy-rate timeline (jvs_a_r21), selected countries + EU27 background.

Purpose
-------
Provide a dedicated time-series view for B1 input used in the ternary model.
The model prefers the Eurostat 3-year vacancy average (unit AVG_3Y).

Output
------
  python/figures/stav_volna_mista_vyvoj.pgf
  latex/texparts/python/stav_volna_mista_vyvoj.tex

Run
---
    python analyses/stav_volna_mista_vyvoj.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from stattool.data_quality import warn_fallback, warn_non_target_year
from stattool.dataset import Dataset
from stattool.fetch import fetch_eurostat
from stattool.style import apply_style_pgf, add_pgf_tooltips, save_figure_tex_pgf, savefig_pgf
from statout.timeline import EU27 as _EU27
from statout.timeline import timeline

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
HIGHLIGHT = ["CZ", "DE"]
START_YEAR = 2010
NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]

apply_style_pgf()

path = fetch_eurostat("jvs_a_r21")
raw = pd.read_csv(path, na_values=["", ":", ": "])
raw = raw.rename(columns={"TIME_PERIOD": "time", "OBS_VALUE": "value"})
raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
raw = raw.dropna(subset=["value"])
raw = raw[raw["geo"].isin(_EU27)].copy()
raw["time"] = raw["time"].astype(str).str[:4].astype(int)

if "freq" in raw.columns:
    raw = raw[raw["freq"].isin(["A", "ANNUAL"])]

_raw_all = raw.copy()
# jvs_a_r21 publishes NACE under nace_r2_1.
_nace_col = "nace_r2" if "nace_r2" in raw.columns else (
    "nace_r2_1" if "nace_r2_1" in raw.columns else None
)
_chosen_nace = None
if _nace_col:
    for _nace in ["B-S_X_O", "TOTAL", "B-S", "B-O"]:
        _tmp = raw[raw[_nace_col] == _nace]
        if not _tmp.empty:
            raw = _tmp
            _chosen_nace = _nace
            break
if _chosen_nace and _chosen_nace != "B-S_X_O":
    warn_fallback(
        f"Vacancy-rate timeline used {_chosen_nace} aggregate instead of preferred B-S_X_O",
        source="Eurostat jvs_a_r21",
    )

_chosen_unit = None
if "unit" in raw.columns:
    for _u in ["AVG_3Y", "AVG_A"]:
        _tmp = raw[raw["unit"] == _u]
        if not _tmp.empty:
            raw = _tmp
            _chosen_unit = _u
            break
if _chosen_unit and _chosen_unit != "AVG_3Y":
    warn_fallback(
        f"Vacancy-rate timeline used {_chosen_unit} instead of preferred AVG_3Y",
        source="Eurostat jvs_a_r21",
    )

if "sizeclas" in raw.columns:
    for _sz in ["GE10", "TOTAL"]:
        _tmp = raw[raw["sizeclas"] == _sz]
        if not _tmp.empty:
            raw = _tmp
            break

_country_overrides: list[str] = []
if _nace_col and _chosen_nace:
    _base = raw.copy()
    _target_year = int(_base["time"].max()) if not _base.empty else START_YEAR
    _have = set(_base.loc[_base["time"] <= _target_year, "geo"].unique())
    _missing = [c for c in COUNTRIES if c not in _have]
    _alts = ["B-N", "B-O", "B-S", "TOTAL"]
    _parts = [_base]
    for _geo in _missing:
        if len(_country_overrides) >= 3:
            break
        for _alt in _alts:
            if _alt == _chosen_nace:
                continue
            _cand = _raw_all[_raw_all[_nace_col] == _alt]
            if _cand.empty:
                continue
            if _chosen_unit and "unit" in _cand.columns:
                _cand = _cand[_cand["unit"] == _chosen_unit]
            if "sizeclas" in raw.columns and "sizeclas" in _cand.columns:
                _cand = _cand[_cand["sizeclas"] == _base["sizeclas"].iloc[0]]
            _cand_geo = _cand[(_cand["geo"] == _geo) & (_cand["time"] <= _target_year)]
            if _cand_geo.empty:
                continue
            _parts.append(_cand[_cand["geo"] == _geo])
            _country_overrides.append(f"{_geo}:{_alt}")
            break
    raw = pd.concat(_parts, ignore_index=True)
if _country_overrides:
    warn_fallback(
        "Vacancy-rate timeline filled missing countries with alternate NACE aggregates: "
        + ", ".join(_country_overrides),
        source="Eurostat jvs_a_r21",
    )

raw = raw[raw["time"] >= START_YEAR]
warn_non_target_year(
    source="Eurostat jvs_a_r21",
    year=int(raw["time"].max()) if not raw.empty else None,
    context="Vacancy-rate timeline latest available year",
)

print(
    "jvs_a_r21 selection:",
    f"nace={_chosen_nace or 'n/a'}, unit={_chosen_unit or 'n/a'},",
    "country-overrides=" + (", ".join(_country_overrides) if _country_overrides else "none")
)

_ds_df = raw[["geo", "time", "value"]]

ds = Dataset(
    _ds_df,
    name="Míra volných pracovních míst",
    unit="%",
    source_url="Eurostat/jvs_a_r21",
)

STRINGS = {
    "title": r"Míra volných pracovních míst",
    "ylabel": r"volná pracovní místa [\%]",
}

fig = timeline(
    ds,
    countries=COUNTRIES,
    title=STRINGS["title"],
    ylabel=STRINGS["ylabel"],
    highlight=HIGHLIGHT,
    annotate_last=True,
    show_eu_avg=False,
    background_eu=True,
)

ax = fig.axes[0]
ax.set_xlim(START_YEAR, max(ds.years[-1], 2025))

# 5-year moving average for CZ (used in ternary B1 smoothing)
cz = _ds_df[_ds_df["geo"] == "CZ"].sort_values("time")[["time", "value"]]
if not cz.empty:
    cz_ma = cz.copy()
    cz_ma["ma5"] = cz_ma["value"].rolling(window=5, min_periods=3).mean()
    ax.plot(
        cz_ma["time"],
        cz_ma["ma5"],
        linestyle="--",
        linewidth=1.1,
        color="#B22222",
        alpha=0.9,
        label="CZ (5letý průměr)",
        zorder=4,
    )

_pivot_fg = (
    ds.df[ds.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(ax, _pivot_fg, fmt="{:.2f}")
_bg = sorted(set(_EU27) - set(COUNTRIES))
_pivot_bg = (
    ds.df[ds.df["geo"].isin(_bg)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(ax, _pivot_bg, fmt="{:.2f}")

for child in ax.get_children():
    if hasattr(child, "get_text"):
        txt = child.get_text().strip()
        if txt in COUNTRIES:
            child.set_text(f"\\acs{{geo-{txt}}}")

savefig_pgf(fig, "stav_volna_mista_vyvoj", strings=STRINGS, nudge_labels=NUDGE_LABELS)

save_figure_tex_pgf(
    "stav_volna_mista_vyvoj",
    caption=f"Vývoj míry volných pracovních míst, vybrané země \\acs{{EU}}, {START_YEAR}--{ds.latest_year}",
    label="fig:stav_volna_mista_vyvoj",
    resizebox_width=r"\linewidth",
    cite_keys=["eurostat_jvs_a_r21"],
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
