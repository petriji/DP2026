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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
    figsize: Optional[tuple[float, float]] = None,
    ax: Optional[plt.Axes] = None,
    color_col: Optional[str] = None,
    cmap: str = "tab10",
    alpha: float = 0.8,
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
        Annotate each point with its ISO-2 country code.
    trendline:
        Draw an OLS regression line with R² annotation.
    highlight:
        List of country codes to draw with a distinct marker.
    color_col:
        Column in ds_x for categorical group colouring.
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

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize or cm2in(12, 9))
    else:
        fig = ax.figure  # type: ignore[assignment]

    # --- Optional categorical colouring ---
    if color_col and color_col in merged.columns:
        groups = merged[color_col].unique()
        cmap_obj = plt.get_cmap(cmap, len(groups))
        color_map = {g: cmap_obj(i) for i, g in enumerate(groups)}
        colors = merged[color_col].map(color_map)
    else:
        colors = None

    normal = merged[~merged["geo"].isin(highlight or [])]
        
    sc = ax.scatter(
        normal["x"],
        normal["y"],
        c=colors.loc[normal.index] if colors is not None else None,
        alpha=alpha,
        zorder=3,
        s=40,
    )

    # Highlighted countries on top
    if highlight:
        hi = merged[merged["geo"].isin(highlight)]
        ax.scatter(
            hi["x"],
            hi["y"],
            marker="*",
            s=120,
            zorder=5,
            edgecolors="black",
            linewidth=0.5,
            c=colors.loc[hi.index] if colors is not None else None,
            label="Highlighted",
        )

    # --- Labels ---
    if label_points:
        for _, row in merged.iterrows():
            ax.annotate(
                row["geo"],
                xy=(row["x"], row["y"]),
                xytext=(4, 2),
                textcoords="offset points",
                fontsize=6,
                alpha=0.8,
            )

    # --- Trend line (OLS) ---
    if trendline and len(merged) >= 3:
        coeffs = np.polyfit(merged["x"], merged["y"], 1)
        x_line = np.linspace(merged["x"].min(), merged["x"].max(), 100)
        y_line = np.polyval(coeffs, x_line)
        corr = np.corrcoef(merged["x"], merged["y"])[0, 1]
        r2 = corr**2
        ax.plot(x_line, y_line, color="gray", linewidth=1, linestyle="--",
                label=f"OLS  $R^2={r2:.2f}$")
        ax.legend(frameon=False, fontsize=7)

    ax.set_xlabel(xlabel or (f"{ds_x.name} [{ds_x.unit}]" if ds_x.unit else ds_x.name))
    ax.set_ylabel(ylabel or (f"{ds_y.name} [{ds_y.unit}]" if ds_y.unit else ds_y.name))
    if title:
        ax.set_title(title)

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

    ax.set_xlabel(xlabel or (f"{ds_x.name} [{ds_x.unit}]" if ds_x.unit else ds_x.name))
    ax.set_ylabel(ylabel or (f"{ds_y.name} [{ds_y.unit}]" if ds_y.unit else ds_y.name))
    if title:
        ax.set_title(title)
    ax.legend(
        bbox_to_anchor=(1.01, 1), loc="upper left",
        borderaxespad=0, frameon=False, fontsize=7
    )
    return fig
