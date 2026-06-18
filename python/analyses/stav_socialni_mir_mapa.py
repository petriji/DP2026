r"""
Social-peace benchmark choropleths (B4): score map + strike-days map.

Purpose
-------
Provide a transparent visual basis for the expert B4 variable used in the
ternary model:
    1) categorical social-peace score (0/25/50/75/100)
  2) benchmark strike-days per 1,000 employees used for that categorisation.

The benchmark combines ILOSTAT/ETUI evidence and conservative country-level
fallbacks for data-lacuna cases documented in thesis commentary.

Output
------
  python/figures/stav_socialni_mir_skore_mapa.pgf
  python/figures/stav_socialni_mir_dny_mapa.pgf
  latex/texparts/python/stav_socialni_mir_skore_mapa.tex
  latex/texparts/python/stav_socialni_mir_dny_mapa.tex

Run
---
    python analyses/stav_socialni_mir_mapa.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyses.stav_socialni_mir_data import (
    build_b4_scores,
    get_b4_benchmark_year,
    get_b4_strike_days_per_1000,
)
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    apply_geo_labels_pgf,
    save_figure_tex_pgf,
    savefig_pgf,
)
from statout.map_europe import choropleth

# ── Parameters ────────────────────────────────────────────────────────────────
YEAR = get_b4_benchmark_year()
COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Build benchmark datasets ───────────────────────────────────────────────
rows: list[dict[str, float | int | str]] = []
_score_series = build_b4_scores()
_strike_days = get_b4_strike_days_per_1000()
for geo in sorted(_score_series.index):
    days = _strike_days.get(geo)
    rows.append(
        {
            "geo": geo,
            "time": YEAR,
            "days_per_1000": float(days) if days is not None else np.nan,
            "score": float(_score_series.get(geo, 50.0)),
        }
    )

_df = pd.DataFrame(rows)

# B4 score map dataset
_ds_score = Dataset(
    _df[["geo", "time", "score"]].rename(columns={"score": "value"}),
    name="Skóre sociálního míru",
    unit="body",
    source_url="ETUI/ILOSTAT + národní kontext (CMKOS)",
)

# Strike-days map dataset
_ds_days = Dataset(
    _df[["geo", "time", "days_per_1000"]].rename(columns={"days_per_1000": "value"}),
    name="Dny ztracené stávkami na 1 000 zaměstnanců",
    unit="dny / 1000 zaměstnanců",
    source_url="ETUI/ILOSTAT + národní fallbacky",
)

# ── 2. Score choropleth ───────────────────────────────────────────────────────
STRINGS_SCORE = {
    "title": f"Sociální smír, kvalitativní skóre ({YEAR})",
    "colorbar_label": r"skóre sociálního míru [0/25/50/75/100]",
}

fig_score = choropleth(
    _ds_score,
    year=YEAR,
    title=STRINGS_SCORE["title"],
    colorbar_label=STRINGS_SCORE["colorbar_label"],
    cmap="RdYlGn",
    vmin=0,
    vmax=100,
    label_countries=True,
    highlight_colorbar=COUNTRIES,
)

_values_score = {row["geo"]: float(row["score"]) for _, row in _df.iterrows()}
apply_geo_labels_pgf(fig_score.axes[0], halo=True, values=_values_score, tooltip_fmt="{:.0f}")

savefig_pgf(
    fig_score,
    "stav_socialni_mir_skore_mapa",
    strings=STRINGS_SCORE,
    nudge_labels=NUDGE_LABELS,
)

save_figure_tex_pgf(
    "stav_socialni_mir_skore_mapa",
    caption=f"Expertní skóre sociálního smíru, \\acs{{geo-EU27}}, {YEAR}",
    label="fig:stav_socialni_mir_skore_mapa",
    resizebox_width=r"\linewidth",
    cite_keys=["ilostat_STR_DAYS_ECO_RT_A", "etui_cba", "CMKOS_ZpravaKV2025"],
    strings=STRINGS_SCORE,
    nudge_labels=NUDGE_LABELS,
)

# ── 3. Strike-days choropleth ─────────────────────────────────────────────────
STRINGS_DAYS = {
    "title": f"Benchmark stávkové aktivity: ztracené dny práce ({YEAR})",
    "colorbar_label": r"ztracené dny práce [na 1 000 zaměstnanců]",
}

fig_days = choropleth(
    _ds_days,
    year=YEAR,
    title=STRINGS_DAYS["title"],
    colorbar_label=STRINGS_DAYS["colorbar_label"],
    cmap="RdYlGn_r",
    vmin=0,
    vmax=max(1.0, float(_df["days_per_1000"].dropna().max())),
    label_countries=True,
    highlight_colorbar=COUNTRIES,
)

_values_days = {
    row["geo"]: float(row["days_per_1000"])
    for _, row in _df.iterrows()
    if pd.notna(row["days_per_1000"])
}
apply_geo_labels_pgf(fig_days.axes[0], halo=True, values=_values_days, tooltip_fmt="{:.1f}")

savefig_pgf(
    fig_days,
    "stav_socialni_mir_dny_mapa",
    strings=STRINGS_DAYS,
    nudge_labels=NUDGE_LABELS,
)

save_figure_tex_pgf(
    "stav_socialni_mir_dny_mapa",
    caption=(
        f"Benchmark stávkové aktivity (dny neodpracované kvůli průmyslovým sporům "
        f"na 1 000 zaměstnanců), \\acs{{geo-EU27}}, {YEAR}."
    ),
    label="fig:stav_socialni_mir_dny_mapa",
    resizebox_width=r"\linewidth",
    cite_keys=["ilostat_STR_DAYS_ECO_RT_A", "etui_cba", "CMKOS_ZpravaKV2025"],
    strings=STRINGS_DAYS,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
