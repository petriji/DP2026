r"""
Vývoj daňového klínu -- EU grey cloud + CZ a sousední/peer země.

Data source
-----------
* Eurostat ``earn_nt_taxwedge`` -- daňový klín na úrovni 67 \% průměrné
  mzdy, jednotlivec bez dětí, % celkových mzdových nákladů.

Output
------
  pics/python/eu_danovy_klin_vyvoj.pgf
  latex/texparts/figures/eu_danovy_klin_vyvoj.tex
  latex/texparts/python/eu_danovy_klin_vyvoj.tex

Run
---
    python analyses/eu_danovy_klin_vyvoj.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from stattool.fetch import fetch_eurostat
from stattool.dataset import Dataset
from stattool.style import (
    apply_style_pgf,
    savefig_pgf,
    save_figure_tex_pgf,
    add_pgf_tooltips,
)
from statout.timeline import timeline, EU27 as _EU27

# ── Parameters ────────────────────────────────────────────────────────────────
COUNTRIES = ["CZ", "AT", "DE", "SK", "PL", "HU"]
HIGHLIGHT = ["CZ"]
START_YEAR = 2000

# ── 0. Style ──────────────────────────────────────────────────────────────────
apply_style_pgf()

# ── 1. Download ───────────────────────────────────────────────────────────────
path = fetch_eurostat("earn_nt_taxwedge", start_period=START_YEAR)

# ── 2. Parse ──────────────────────────────────────────────────────────────────
ds = Dataset.from_sdmx_csv(
    path,
    name="Daňový klín",
    unit="%",
    source_url="https://ec.europa.eu/eurostat -- earn_nt_taxwedge",
)
print(f"Loaded: {len(ds.countries)} countries, years {ds.years[0]}--{ds.years[-1]}")

latest_yr = ds.years[-1]

# ── 3. Plot ───────────────────────────────────────────────────────────────────
STRINGS = {
    "title": r"Vývoj daňového klínu (67\,\% průměrné mzdy)",
    "ylabel": r"daňový klín [\% mzdových nákladů]",
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
fig.axes[0].set_xlim(START_YEAR - 1, latest_yr + 2)

# ── PGF tooltips & geo labels ─────────────────────────────────────────────────
_ax = fig.axes[0]
_pivot_fg = (
    ds.df[ds.df["geo"].isin(COUNTRIES)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax, _pivot_fg, fmt="{:.1f}")
_bg = sorted(set(_EU27) - set(COUNTRIES))
_pivot_bg = (
    ds.df[ds.df["geo"].isin(_bg)]
    .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
)
add_pgf_tooltips(_ax, _pivot_bg, fmt="{:.1f}")
for _child in _ax.get_children():
    if hasattr(_child, "get_text"):
        _txt = _child.get_text().strip()
        if _txt in COUNTRIES:
            _child.set_text(f"\\acs{{geo-{_txt}}}")

NUDGE_LABELS = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]
savefig_pgf(fig, "eu_danovy_klin_vyvoj", strings=STRINGS, nudge_labels=NUDGE_LABELS)

save_figure_tex_pgf(
    "eu_danovy_klin_vyvoj",
    caption=(
        r"Vývoj daňového klínu (\SI{67}{\percent} průměrné mzdy, "
        r"jednotlivec bez dětí, \% mzdových nákladů), "
        f"EU\\,27, {START_YEAR}--{latest_yr}. "
        r"Šedé linie = ostatní země EU\,27. "
        r"Zdroj dat: Eurostat~\cite{eurostat_earn_nt_taxwedge}."
    ),
    label="fig:eu_danovy_klin_vyvoj",
    resizebox_width=r"\linewidth",
    cite_key="eurostat_earn_nt_taxwedge",
    strings=STRINGS,
    nudge_labels=NUDGE_LABELS,
)

print("Done.")
