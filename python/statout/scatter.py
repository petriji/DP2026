"""
XY scatter / correlation plots between two variables.

Usage
-----
>>> from stattool.style import apply_style, savefig
>>> from statout.scatter import scatter_xy
>>> apply_style()
>>> fig = scatter_xy(ds_x, ds_y, year=2022,
...                 title="Gini vs employment rate 2022")
>>> savefig(fig, "gini_vs_employment_2022")
"""

from __future__ import annotations

from typing import Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import COUNTRY_COLORS, FONT_SIZE, IS_POSTER_RUN, FIGURE_LABEL_SIZE, POSTER_FIGURE_COMPACT_LABEL_SIZE, POSTER_FIGURE_LABEL_SIZE
from stattool.dataset import Dataset
from stattool.style import cm2in


def scatter_xy(
    ds_x: Dataset,
    ds_y: Dataset,
    *,
    year: Optional[int] = None,
    title: str = "",
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    label_points: bool = True,
    trendline: bool = True,
    highlight: Optional[list[str]] = None,
    x_min: Optional[float] = None,
    countries: Optional[list[str]] = None,
    figsize: Optional[tuple[float, float]] = None,
    ax: Optional[plt.Axes] = None,
    color_col: Optional[str] = None,
    cmap: str = "tab10",
    alpha: float = 0.8,
    year_tolerance: int = 2,
) -> plt.Figure:
    """Scatter plot of *ds_x* vs *ds_y* for a single year.

    Both datasets must share the same geo column values.

    Parameters
    ----------
    ds_x, ds_y:
        X and Y variable datasets (long tidy format).
    year:
        Year to display.  Defaults to the latest common year.
    title:
        Chart title.
    xlabel / ylabel:
        Axis labels.  Auto-generated from dataset metadata when omitted.
    label_points:
        Annotate highlighted country codes on the plot (non-highlighted are
        never labelled to avoid clutter).
    trendline:
        Draw an OLS regression line with R² annotation.
    highlight:
        Country codes to emphasise: drawn with per-country colour (from
        COUNTRY_COLORS), star marker, and a country-code label.
        All other countries are rendered as small grey dots with no label.
    x_min:
        If given, sets the left limit of the x-axis (e.g. 0 for rates starting
        at zero).
    year_tolerance:
        For highlighted countries missing data at *year*, fall back to the most
        recent available year within this many years (default 2). Prints a
        notice when a fallback is used.
    color_col:
        Column in ds_x for categorical group colouring (applied to
        non-highlighted points only).
    """
    common_years = set(ds_x.years) & set(ds_y.years)
    year = year or max(common_years)

    px = ds_x.for_year(year)[[ds_x.geo_col, ds_x.value_col]].rename(
        columns={ds_x.geo_col: "geo", ds_x.value_col: "x"}
    )
    py = ds_y.for_year(year)[[ds_y.geo_col, ds_y.value_col]].rename(
        columns={ds_y.geo_col: "geo", ds_y.value_col: "y"}
    )
    merged = pd.merge(px, py, on="geo").dropna(subset=["x", "y"])

    # Optional geo filter (e.g. EU27 only)
    if countries:
        merged = merged[merged["geo"].isin(countries)]

    _highlight = set(highlight or [])

    # ── Year-tolerance fallback for missing countries ─────────────────────────
    # First, fill in missing highlighted countries (with log message).
    # Then, silently fill in any other countries from the `countries` filter.
    if year_tolerance > 0:
        all_candidates = set(_highlight) | (set(countries) if countries else set())
        for geo in all_candidates - set(merged["geo"]):
            for fallback_yr in range(year - 1, year - year_tolerance - 1, -1):
                px_geo = ds_x.df[ds_x.df[ds_x.geo_col] == geo]
                py_geo = ds_y.df[ds_y.df[ds_y.geo_col] == geo]
                px_val = px_geo[px_geo[ds_x.time_col] == fallback_yr][ds_x.value_col]
                py_val = py_geo[py_geo[ds_y.time_col] == fallback_yr][ds_y.value_col]
                if px_val.empty or py_val.empty:
                    continue
                fb = pd.DataFrame({"geo": [geo], "x": [px_val.iloc[0]], "y": [py_val.iloc[0]]})
                merged = pd.concat([merged, fb], ignore_index=True)
                if geo in _highlight:
                    print(f"  scatter_xy: {geo} missing at {year}, used fallback {fallback_yr}")
                break

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize or cm2in(12, 9))
    else:
        fig = ax.figure  # type: ignore[assignment]

    # ── Grey background points (all non-highlighted countries) ────────────────
    # --- Optional categorical colouring for grey points ---
    if color_col and color_col in merged.columns:
        groups = merged[color_col].unique()
        cmap_obj = plt.get_cmap(cmap, len(groups))
        color_map = {g: cmap_obj(i) for i, g in enumerate(groups)}
        bg_colors = merged[color_col].map(color_map)
    else:
        bg_colors = None

    normal = merged[~merged["geo"].isin(_highlight)]
    ax.scatter(
        normal["x"],
        normal["y"],
        c=(bg_colors.loc[normal.index].tolist() if bg_colors is not None
           else ["#AAAAAA"] * len(normal)),
        alpha=0.5,
        zorder=2,
        s=25,
        linewidths=0,
    )

    # ── Highlighted countries (colored circles, labelled) ────────────────────
    if _highlight:
        hi = merged[merged["geo"].isin(_highlight)]
        for _, row in hi.iterrows():
            color = COUNTRY_COLORS.get(row["geo"], "#333333")
            ax.scatter(
                row["x"],
                row["y"],
                marker="o",
                s=50,
                zorder=5,
                color=color,
                edgecolors="white",
                linewidth=0.5,
            )
            if label_points:
                ax.annotate(
                    row["geo"],
                    xy=(row["x"], row["y"]),
                    xytext=(5, 2),
                    textcoords="offset points",
                    fontsize=POSTER_FIGURE_COMPACT_LABEL_SIZE if IS_POSTER_RUN else FONT_SIZE - 1,
                    color=color,
                    fontweight="bold",
                    va="center",
                )

    # ── Minor grid ────────────────────────────────────────────────────────────
    ax.minorticks_on()
    ax.grid(which="major", linewidth=0.4, alpha=0.5, color="#AAAAAA", zorder=0)
    ax.grid(which="minor", linewidth=0.2, alpha=0.35, color="#DDDDDD", zorder=0)

    # ── Trend line (OLS) ─────────────────────────────────────────────────────
    if trendline and len(merged) >= 3:
        coeffs = np.polyfit(merged["x"], merged["y"], 1)
        x_line = np.linspace(merged["x"].min(), merged["x"].max(), 100)
        y_line = np.polyval(coeffs, x_line)
        corr = np.corrcoef(merged["x"], merged["y"])[0, 1]
        r2 = corr**2
        ax.plot(x_line, y_line, color="gray", linewidth=1, linestyle="--",
            label=f"$R^2={r2:.2f}$")
        if IS_POSTER_RUN:
            # Poster: render R^2 as right-anchored axes-fraction text instead of
            # a legend. Anchored at the bottom-right corner (empty in all four
            # korelace panels) with ha="right" so the LaTeX-inflated text grows
            # leftward and never overflows the right spine or collides with the
            # highlighted country points clustered in the upper corners.
            ax.text(0.97, 0.04, f"$R^2={r2:.2f}$",
                    transform=ax.transAxes, ha="right", va="bottom",
                    fontsize=POSTER_FIGURE_LABEL_SIZE, color="#555555")
        else:
            ax.legend(frameon=False, fontsize=FONT_SIZE - 1)

    ax.set_xlabel(xlabel if xlabel is not None
                  else (f"{ds_x.name} [{ds_x.unit}]" if ds_x.unit else ds_x.name))
    ax.set_ylabel(ylabel if ylabel is not None
                  else (f"{ds_y.name} [{ds_y.unit}]" if ds_y.unit else ds_y.name))
    if title:
        ax.set_title(f"{title} ({year})")

    if x_min is not None:
        ax.set_xlim(left=x_min)

    # Stash the merged (geo, x, y) data on the figure so callers (e.g. PGF
    # scripts) can attach hover tooltips with add_pgf_tooltips_scatter().
    fig._scatter_merged = merged.copy()  # type: ignore[attr-defined]

    if mpl.get_backend() == "pgf":
        from stattool.style import (
            add_pgf_tooltips_scatter as _ats,
            apply_geo_labels_pgf as _agl,
        )
        _x_lbl = (xlabel if xlabel
                  else (f"{ds_x.name} [{ds_x.unit}]" if ds_x.unit else ds_x.name))
        _y_lbl = (ylabel if ylabel
                  else (f"{ds_y.name} [{ds_y.unit}]" if ds_y.unit else ds_y.name))
        _ats(ax, merged, label_x=_x_lbl, label_y=_y_lbl)
        _agl(ax)

    return fig


def scatter_time_series(
    ds_x: Dataset,
    ds_y: Dataset,
    *,
    countries: Optional[list[str]] = None,
    title: str = "",
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Optional[tuple[float, float]] = None,
    annotate_years: bool = True,
) -> plt.Figure:
    """Trajectory plot: each country draws a path through (x, y) space over time.

    Useful for showing co-evolution of two variables (e.g. employment & poverty).
    """
    geos = countries or list(set(ds_x.countries) & set(ds_y.countries))
    fig, ax = plt.subplots(figsize=figsize or cm2in(13, 9))

    for geo in geos:
        rx = ds_x.for_country(geo)[[ds_x.time_col, ds_x.value_col]].rename(
            columns={ds_x.time_col: "year", ds_x.value_col: "x"}
        )
        ry = ds_y.for_country(geo)[[ds_y.time_col, ds_y.value_col]].rename(
            columns={ds_y.time_col: "year", ds_y.value_col: "y"}
        )
        traj = pd.merge(rx, ry, on="year").dropna().sort_values("year")
        if traj.empty:
            continue
        line, = ax.plot(traj["x"], traj["y"], marker="o", markersize=3,
                        linewidth=1.2, label=geo)
        # Annotate first and last year
        if annotate_years and len(traj) > 0:
            for idx in [0, -1]:
                ax.annotate(
                    str(traj["year"].iloc[idx]),
                    xy=(traj["x"].iloc[idx], traj["y"].iloc[idx]),
                    xytext=(3, 3),
                    textcoords="offset points",
                    fontsize=5,
                    color=line.get_color(),
                )

    ax.set_xlabel(xlabel if xlabel is not None
                  else (f"{ds_x.name} [{ds_x.unit}]" if ds_x.unit else ds_x.name))
    ax.set_ylabel(ylabel if ylabel is not None
                  else (f"{ds_y.name} [{ds_y.unit}]" if ds_y.unit else ds_y.name))
    if title:
        ax.set_title(title)
    ax.legend(
        bbox_to_anchor=(1.01, 1), loc="upper left",
        borderaxespad=0, frameon=False, fontsize=7
    )
    return fig
