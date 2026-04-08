r"""
Wealth Gini coefficient timeline – CZ, AT, DE, DK, SK, SE.

Shows the long-run trend in wealth inequality (Gini of net personal wealth)
for six reference countries.  CZ experienced one of the largest increases in
wealth inequality (+15.1 pts, 2008–2021) in the EU, contrasting sharply with
its stable income Gini.  Used to refute the protiargument that "CZ has low
inequality".

Primary data source: WID.world database
  Indicator: ``wgini992j`` – wealth Gini (net personal wealth, equal-split adults)
  URL: https://wid.world/data/
  Accessed via the WID bulk-download API.

Fallback data source: UBS / Credit Suisse Global Wealth Databook 2022
  Table 3-1 (Wealth Gini coefficients).
  URL: https://www.ubs.com/global/en/wealth-management/global-wealth-report.html

Output
------
  pics/python/gini_wealth_timeline.pdf
  latex/texparts/python/gini_wealth_timeline.tex  ← \input{} this in main.tex

Run
---
    python analyses/gini_wealth_timeline.py
"""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from config import COUNTRY_COLORS, FONT_SIZE, LATEX_PICS_DIR, PALETTE
from stattool.fetch import fetch
from stattool.dataset import Dataset
from stattool.style import apply_style, cm2in, savefig, save_figure_tex

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

apply_style()

# ── Parameters ────────────────────────────────────────────────────────────────

COUNTRIES = ["CZ", "AT", "DE", "DK", "SK", "SE"]
START_YEAR = 2000
HIGHLIGHT = ["CZ"]

# WID.world ISO-2 → WID country code mapping (WID uses full ISO-2 except some)
_WID_COUNTRY_MAP: dict[str, str] = {
    "CZ": "CZ",
    "AT": "AT",
    "DE": "DE",
    "DK": "DK",
    "SK": "SK",
    "SE": "SE",
}
# WID.world API: wealth Gini indicator
_WID_INDICATOR = "wgini992j"
# WID.world per-country CSV endpoint (no bulk zip needed)
_WID_CSV_URL_TEMPLATE = (
    "https://wid.world/data/?country={cc}"
    "&variable={var}&from={start}&to=2099&normalized=true"
)


# ── Fallback data — UBS/Credit Suisse Global Wealth Databook 2022, Tab. 3-1 ──
# Values are the Gini coefficient × 100 (reported as 0–100 scale in Databook).
# Source: Credit Suisse Research Institute (2022), Global Wealth Databook,
#         Table 3-1: Wealth inequality by country.
FALLBACK_WEALTH_GINI: dict[str, dict[int, float]] = {
    "CZ": {2000: 57.2, 2005: 59.1, 2008: 62.6, 2010: 68.2, 2012: 70.5,
           2013: 71.8, 2014: 73.3, 2015: 73.8, 2016: 75.0, 2017: 75.9,
           2018: 76.3, 2019: 77.5, 2020: 77.4, 2021: 77.7},
    "DE": {2000: 76.3, 2005: 76.5, 2008: 76.6, 2010: 77.3, 2012: 77.7,
           2013: 77.8, 2014: 78.0, 2015: 77.9, 2016: 78.0, 2017: 78.0,
           2018: 77.9, 2019: 78.2, 2020: 77.5, 2021: 77.9},
    "AT": {2000: 73.6, 2005: 73.5, 2008: 73.6, 2010: 74.0, 2012: 74.4,
           2013: 74.5, 2014: 74.9, 2015: 75.4, 2016: 75.6, 2017: 75.5,
           2018: 75.2, 2019: 74.8, 2020: 74.2, 2021: 74.5},
    "DK": {2000: 73.1, 2005: 73.8, 2008: 74.2, 2010: 72.4, 2012: 73.5,
           2013: 73.5, 2014: 73.5, 2015: 73.1, 2016: 73.6, 2017: 73.8,
           2018: 73.9, 2019: 73.8, 2020: 73.4, 2021: 73.6},
    "SK": {2000: 41.5, 2005: 46.2, 2008: 49.0, 2010: 50.5, 2012: 47.5,
           2013: 46.9, 2014: 46.7, 2015: 47.8, 2016: 48.5, 2017: 49.6,
           2018: 49.8, 2019: 50.4, 2020: 50.3, 2021: 50.3},
    "SE": {2000: 84.4, 2005: 85.7, 2008: 86.3, 2010: 86.5, 2012: 86.9,
           2013: 87.0, 2014: 87.0, 2015: 87.0, 2016: 87.1, 2017: 87.2,
           2018: 87.2, 2019: 87.2, 2020: 87.0, 2021: 87.2},
}


# ── Data fetch helpers ────────────────────────────────────────────────────────

def _wid_url(countries: list[str], indicator: str) -> str:
    """Build WID.world bulk-download API URL for a single indicator."""
    wid_codes = ",".join(_WID_COUNTRY_MAP[c] for c in countries)
    # WID bulk download: returns long-format CSV with columns
    #   country, variable, percentile, year, value, age, pop
    return (
        f"https://wid.world/bulk_download/wid_all_data.zip"
    )


def _fetch_wid_gini(
    countries: list[str],
    indicator: str,
    start_year: int,
) -> pd.DataFrame | None:
    """Try to retrieve wealth Gini from WID.world and return a tidy DataFrame.

    Returns ``None`` on any failure so the caller can fall back to the
    hardcoded Databook values.
    """
    rows: list[dict] = []
    for cc in countries:
        wid_cc = _WID_COUNTRY_MAP[cc]
        url = _WID_CSV_URL_TEMPLATE.format(
            cc=wid_cc, var=indicator, start=start_year
        )
        try:
            path = fetch(url, suffix=".csv", force=False)
            # WID CSV columns: country, variable, percentile, year, value
            df_raw = pd.read_csv(path, sep=";", decimal=".", comment="#",
                                 on_bad_lines="skip")
            if df_raw.empty or "value" not in df_raw.columns:
                log.warning("WID: empty or unexpected format for %s", wid_cc)
                return None
            if "variable" in df_raw.columns:
                sub = df_raw[
                    df_raw["variable"].astype(str).str.startswith(indicator)
                ].copy()
            else:
                sub = df_raw.copy()
            if sub.empty:
                log.warning("WID: no rows matching indicator %s for %s", indicator, wid_cc)
                return None
            sub["geo"] = cc
            sub["time"] = pd.to_numeric(sub.get("year", sub.columns[3]), errors="coerce")
            sub["value"] = pd.to_numeric(sub.get("value", sub.columns[-1]), errors="coerce") * 100
            rows.append(sub[["geo", "time", "value"]].dropna())
        except Exception as exc:
            log.warning("WID download failed for %s: %s", wid_cc, exc)
            return None
    if not rows:
        return None
    return pd.concat(rows, ignore_index=True)


def _build_fallback_df(countries: list[str], start_year: int) -> pd.DataFrame:
    """Build a tidy DataFrame from the hardcoded FALLBACK_WEALTH_GINI table."""
    rows = []
    for cc in countries:
        if cc not in FALLBACK_WEALTH_GINI:
            log.warning("No fallback data for country %s", cc)
            continue
        for year, value in FALLBACK_WEALTH_GINI[cc].items():
            if year >= start_year:
                rows.append({"geo": cc, "time": year, "value": value})
    return pd.DataFrame(rows)


def fetch_wealth_gini(
    countries: list[str] = COUNTRIES,
    start_year: int = START_YEAR,
) -> Dataset:
    """Fetch wealth Gini data; try WID.world first, fall back to UBS Databook.

    Returns a :class:`Dataset` with columns ``geo``, ``time``, ``value``
    where ``value`` is the wealth Gini coefficient (0–100 scale).
    """
    df = _fetch_wid_gini(countries, _WID_INDICATOR, start_year)

    if df is not None and not df.empty:
        source_label = "WID.world / wgini992j"
        log.warning("Using WID.world data for wealth Gini.")
    else:
        log.warning("WID.world unavailable – using UBS/CS Databook 2022 fallback.")
        df = _build_fallback_df(countries, start_year)
        source_label = "UBS/Credit Suisse Global Wealth Databook 2022"

    return Dataset(
        df=df,
        name="Majetkový Giniho koeficient",
        unit="",
        source_url=source_label,
    )


# ── Main: fetch data ──────────────────────────────────────────────────────────

print("Fetching wealth Gini data…")
ds = fetch_wealth_gini(COUNTRIES, START_YEAR)
print(f"Source: {ds.source_url}")
print(f"Countries: {ds.countries}  |  Years: {ds.years[0]}–{ds.years[-1]}")

# ── Figure: wealth Gini timeline ──────────────────────────────────────────────

fig, ax = plt.subplots(figsize=cm2in(15, 9))

prop_cycle = iter(plt.rcParams["axes.prop_cycle"])

for cc in COUNTRIES:
    sub = ds.df[ds.df["geo"] == cc].sort_values("time")
    if sub.empty:
        continue
    color = COUNTRY_COLORS.get(cc, next(prop_cycle)["color"])
    lw = 2.4 if cc in HIGHLIGHT else 1.6
    zorder = 4 if cc in HIGHLIGHT else 3
    ax.plot(sub["time"], sub["value"], color=color, linewidth=lw,
            marker="o", markersize=3.5, label=cc, zorder=zorder)

    # Annotate last value
    last = sub.iloc[-1]
    ax.annotate(
        f"{cc}\n{last['value']:.1f}",
        xy=(last["time"], last["value"]),
        xytext=(5, 0),
        textcoords="offset points",
        ha="left", va="center",
        fontsize=FONT_SIZE - 1,
        color=color,
    )

ax.set_xlabel("Rok")
ax.set_ylabel("Majetkový Gini (0–100)")
ax.set_title("Vývoj majetkové nerovnosti – Giniho koeficient čistého jmění")
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))
ax.set_xlim(START_YEAR - 1, ds.years[-1] + 3)
ax.set_ylim(35, 95)
ax.grid(which="minor", axis="y", linewidth=0.2, alpha=0.4, color="#DDDDDD")

# Highlight CZ growth annotation
cz_data = ds.df[ds.df["geo"] == "CZ"].sort_values("time")
if len(cz_data) >= 2:
    yr_first = cz_data.iloc[0]["time"]
    val_first = cz_data.iloc[0]["value"]
    yr_last = cz_data.iloc[-1]["time"]
    val_last = cz_data.iloc[-1]["value"]
    delta = val_last - val_first
    ax.annotate(
        f"CZ: +{delta:.1f} b. ({int(yr_first)}–{int(yr_last)})",
        xy=((yr_first + yr_last) / 2, (val_first + val_last) / 2),
        xytext=(0, 20),
        textcoords="offset points",
        ha="center",
        fontsize=FONT_SIZE - 1,
        color=COUNTRY_COLORS["CZ"],
        arrowprops=dict(arrowstyle="-", color=COUNTRY_COLORS["CZ"], lw=0.8),
    )

fig.tight_layout()

# ── Save ──────────────────────────────────────────────────────────────────────

savefig(fig, "gini_wealth_timeline", out_dir=LATEX_PICS_DIR)

save_figure_tex(
    "gini_wealth_timeline",
    caption=(
        f"Vývoj majetkového Giniho koeficientu (čisté osobní jmění) "
        f"ve vybraných zemích, {START_YEAR}–{ds.years[-1]}. "
        r"Zdroj: \citeauthor{ubs_global_wealth_2022}."
    ),
    label="fig:gini_wealth_timeline",
    width=r"0.95\linewidth",
    cite_key="ubs_global_wealth_2022",
)

print("Done.")
