r"""
B2 corporate tax indicator (ternary axis B) -- OECD map + timeline + fallback diagnostics.

Primary source (B2 in ternary): OECD ``CTS_CIT`` dataset,
indicator ``COMB_CIT_RATE`` (combined statutory corporate income tax rate, %).

Fallback in ternary:
1) same-source OECD alternatives from ``CTS_CIT`` (``CIT_RATE``,
   ``CIT_RATE_LESS_SUB_NAT``),
2) expert value for Cyprus (14.1 % for 2026).

Output
------
  pics/python/stav_korporatni_dan_mapa.pdf
  pics/python/stav_korporatni_dan_vyvoj.pdf
  latex/texparts/python/stav_korporatni_dan_mapa.tex
  latex/texparts/python/stav_korporatni_dan_vyvoj.tex

Run
---
    python analyses/stav_korporatni_dan.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from statout.map_europe import choropleth
from statout.timeline import EU27 as _EU27, timeline
from stattool.dataset import Dataset, _OECD_ISO3_TO_ISO2
from stattool.fetch import fetch_oecd
from stattool.style import (
    add_pgf_tooltips,
    apply_geo_labels_pgf,
    apply_style_pgf,
    save_figure_tex_pgf,
    savefig_pgf,
)

COUNTRIES = ["CZ", "AT", "DE", "DK", "PL", "SK"]
HIGHLIGHT = ["CZ"]
START_YEAR = 2000

_EU27_SORTED = sorted(_EU27)


def _snapshot_locf(df: pd.DataFrame, *, min_coverage: int = 18) -> tuple[pd.Series, int]:
    """Build EU27 country snapshot for latest year with sufficient coverage + LOCF."""
    d = df.copy()
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    d["time"] = pd.to_numeric(d["time"], errors="coerce")
    d = d[d["geo"].isin(_EU27_SORTED)].dropna(subset=["value", "time"])
    d["time"] = d["time"].astype(int)

    coverage = d.groupby("time")["geo"].nunique()
    valid = coverage[coverage >= min_coverage]
    if valid.empty:
        raise ValueError(
            f"No year with >= {min_coverage} EU27 observations "
            f"(max coverage {coverage.max()} in {coverage.idxmax()})."
        )
    latest_year = int(valid.index.max())

    out: dict[str, float] = {}
    for geo in _EU27_SORTED:
        hist = d[(d["geo"] == geo) & (d["time"] <= latest_year)].sort_values(
            "time", ascending=False
        )
        out[geo] = float(hist.iloc[0]["value"]) if not hist.empty else np.nan
    return pd.Series(out), latest_year


def _load_oecd_comb_rate() -> Dataset:
    path = fetch_oecd("CTS_CIT", start_period=START_YEAR)
    raw = pd.read_csv(path)
    raw = raw[raw["CORP_TAX"] == "COMB_CIT_RATE"].copy()
    if "UNIT_MEASURE" in raw.columns:
        raw = raw[raw["UNIT_MEASURE"] == "PC"]
    raw["geo"] = raw["COU"].map(lambda x: _OECD_ISO3_TO_ISO2.get(str(x).upper(), str(x)))
    raw = raw[raw["geo"].isin(_EU27_SORTED)].copy()
    raw = raw.rename(columns={"TIME_PERIOD": "time", "OBS_VALUE": "value"})
    raw["time"] = pd.to_numeric(raw["time"], errors="coerce")
    raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
    raw = raw.dropna(subset=["time", "value"])
    raw["time"] = raw["time"].astype(int)
    return Dataset(
        raw[["geo", "time", "value"]],
        name="Kombinovaná sazba DPPO",
        unit="%",
        source_url="OECD/CTS_CIT (COMB_CIT_RATE)",
    )


def main() -> None:
    apply_style_pgf()

    # ── 1) Primary OECD B2 indicator for dedicated visualisation ────────────
    ds = _load_oecd_comb_rate()
    print(
        "OECD metadata: dataset=CTS_CIT, indicator=COMB_CIT_RATE, "
        "unit=PC (percent), frequency=annual"
    )
    print(f"OECD data years available in EU27 subset: {ds.years[0]}--{ds.years[-1]}")

    snap_oecd, snap_year = _snapshot_locf(ds.df)
    missing_oecd = [geo for geo in _EU27_SORTED if pd.isna(snap_oecd.loc[geo])]
    print(
        f"Ternary primary B2 snapshot year (OECD coverage >=18): {snap_year}; "
        f"matched countries after LOCF: {snap_oecd.notna().sum()}"
    )
    if missing_oecd:
        print("OECD missing countries after LOCF:", ", ".join(missing_oecd))

    # ── 2) Choropleth map (OECD primary series, latest year) ───────────────
    values_map = ds.df[ds.df["time"] == ds.latest_year].set_index("geo")["value"].to_dict()
    vmax_map = max(values_map.values()) if values_map else 40.0

    strings_map = {
        "title": f"Kombinovaná sazba DPPO ({ds.latest_year})",
        "colorbar_label": r"sazba [\si{\percent}]",
    }
    fig_map = choropleth(
        ds,
        year=ds.latest_year,
        title=strings_map["title"],
        colorbar_label=strings_map["colorbar_label"],
        cmap="RdYlGn_r",
        vmin=0,
        vmax=vmax_map,
        label_countries=True,
        highlight_colorbar=COUNTRIES,
    )
    apply_geo_labels_pgf(fig_map.axes[0], halo=True, values=values_map, tooltip_fmt="{:.1f}")
    nudge_labels = [(c, rf"\acs{{geo-{c}}}") for c in COUNTRIES]
    savefig_pgf(fig_map, "stav_korporatni_dan_mapa", strings=strings_map, nudge_labels=nudge_labels)
    save_figure_tex_pgf(
        "stav_korporatni_dan_mapa",
        caption=(
            f"Kombinovaná statutární sazba daně z~příjmů právnických osob, "
            f"\\acs{{EU}}, {ds.latest_year}."
        ),
        label="fig:stav_korporatni_dan_mapa",
        resizebox_width=r"\linewidth",
        cite_key="oecd_cts_cit",
        strings=strings_map,
        nudge_labels=nudge_labels,
    )

    # ── 3) Timeline (OECD primary series) ───────────────────────────────────
    strings_tl = {
        "title": r"Vývoj kombinované sazby DPPO",
        "ylabel": r"sazba [\si{\percent}]",
    }
    fig_tl = timeline(
        ds,
        countries=COUNTRIES,
        title=strings_tl["title"],
        ylabel=strings_tl["ylabel"],
        highlight=HIGHLIGHT,
        annotate_last=True,
        show_eu_avg=False,
        background_eu=True,
    )
    fig_tl.axes[0].set_xlim(START_YEAR, max(2025, ds.years[-1]))
    fig_tl.axes[0].set_ylim(0, max(45, int(np.ceil(ds.df["value"].max())) + 2))

    pivot_fg = (
        ds.df[ds.df["geo"].isin(COUNTRIES)]
        .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
    )
    add_pgf_tooltips(fig_tl.axes[0], pivot_fg, fmt="{:.1f}")
    bg = sorted(set(_EU27_SORTED) - set(COUNTRIES))
    pivot_bg = (
        ds.df[ds.df["geo"].isin(bg)]
        .pivot_table(index="time", columns="geo", values="value", aggfunc="mean")
    )
    add_pgf_tooltips(fig_tl.axes[0], pivot_bg, fmt="{:.1f}")
    for child in fig_tl.axes[0].get_children():
        if hasattr(child, "get_text"):
            txt = child.get_text().strip()
            if txt in COUNTRIES:
                child.set_text(f"\\acs{{geo-{txt}}}")

    savefig_pgf(fig_tl, "stav_korporatni_dan_vyvoj", strings=strings_tl, nudge_labels=nudge_labels)
    save_figure_tex_pgf(
        "stav_korporatni_dan_vyvoj",
        caption=(
            f"Vývoj kombinované statutární sazby daně z~příjmů právnických osob, "
            f"vybrané země \\acs{{EU}}, {START_YEAR}--{ds.years[-1]}."
        ),
        label="fig:stav_korporatni_dan_vyvoj",
        resizebox_width=r"\linewidth",
        cite_key="oecd_cts_cit",
        strings=strings_tl,
        nudge_labels=nudge_labels,
    )

    # ── 4) Same-source fallback diagnostics + newest data years by country ──
    path_all = fetch_oecd("CTS_CIT", start_period=START_YEAR)
    all_raw = pd.read_csv(path_all)
    all_raw["geo"] = all_raw["COU"].map(
        lambda x: _OECD_ISO3_TO_ISO2.get(str(x).upper(), str(x))
    )
    all_raw = all_raw[all_raw["geo"].isin(_EU27_SORTED)].copy()
    if "UNIT_MEASURE" in all_raw.columns:
        all_raw = all_raw[all_raw["UNIT_MEASURE"] == "PC"]
    all_raw["TIME_PERIOD"] = pd.to_numeric(all_raw["TIME_PERIOD"], errors="coerce")
    all_raw["OBS_VALUE"] = pd.to_numeric(all_raw["OBS_VALUE"], errors="coerce")
    all_raw = all_raw.dropna(subset=["TIME_PERIOD", "OBS_VALUE"])
    all_raw["TIME_PERIOD"] = all_raw["TIME_PERIOD"].astype(int)

    newest: list[dict] = []
    for geo in _EU27_SORTED:
        g = all_raw[all_raw["geo"] == geo]
        if g.empty:
            newest.append({"geo": geo, "source": "expert", "measure": "EATR_model", "year": 2026})
            continue
        m = g[g["CORP_TAX"] == "COMB_CIT_RATE"]
        if not m.empty:
            newest.append(
                {
                    "geo": geo,
                    "source": "OECD",
                    "measure": "COMB_CIT_RATE",
                    "year": int(m["TIME_PERIOD"].max()),
                }
            )
            continue
        used = None
        used_year = None
        for alt in ["CIT_RATE", "CIT_RATE_LESS_SUB_NAT"]:
            a = g[g["CORP_TAX"] == alt]
            if not a.empty:
                used = alt
                used_year = int(a["TIME_PERIOD"].max())
                break
        if used is None:
            newest.append({"geo": geo, "source": "expert", "measure": "EATR_model", "year": 2026})
        else:
            newest.append({"geo": geo, "source": "OECD", "measure": used, "year": used_year})

    newest_df = pd.DataFrame(newest).sort_values("geo")
    print("Newest B2 year per country (ternary input source):")
    print(newest_df.to_string(index=False))

    fallback_used = newest_df[newest_df["measure"].isin(["CIT_RATE", "CIT_RATE_LESS_SUB_NAT"])]
    if fallback_used.empty:
        print("Same-source OECD fallback used: no")
    else:
        print("Same-source OECD fallback used: yes")
        print(fallback_used.to_string(index=False))

    # Difference between primary and same-source alternatives where both exist.
    for alt in ["CIT_RATE", "CIT_RATE_LESS_SUB_NAT"]:
        base = all_raw[all_raw["CORP_TAX"] == "COMB_CIT_RATE"][
            ["geo", "TIME_PERIOD", "OBS_VALUE"]
        ].rename(columns={"OBS_VALUE": "comb"})
        comp = all_raw[all_raw["CORP_TAX"] == alt][["geo", "TIME_PERIOD", "OBS_VALUE"]].rename(
            columns={"OBS_VALUE": "alt"}
        )
        inter = base.merge(comp, on=["geo", "TIME_PERIOD"], how="inner")
        if inter.empty:
            print(f"Difference diagnostics {alt} vs COMB_CIT_RATE: no overlap")
            continue
        inter["diff"] = inter["alt"] - inter["comb"]
        print(
            f"Difference diagnostics {alt} vs COMB_CIT_RATE: "
            f"n={len(inter)}, median={inter['diff'].median():.2f} p. b., "
            f"mean={inter['diff'].mean():.2f} p. b., "
            f"p95_abs={inter['diff'].abs().quantile(0.95):.2f} p. b."
        )

    print("Expert value used for CY: EATR_model=14.1 %, year=2026")
    print("Done.")


if __name__ == "__main__":
    main()
