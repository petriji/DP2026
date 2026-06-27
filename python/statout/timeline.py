"""
Timeline (line chart) visualisation for comparing countries or groups over time.

Usage
-----
>>> from stattool.style import apply_style, savefig
>>> from statout.timeline import timeline
>>> apply_style()
>>> fig = timeline(ds, countries=["CZ", "DE", "PL", "SK"], title="Výsledky")
>>> savefig(fig, "gini_timeline")
"""

from __future__ import annotations

from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from config import COUNTRY_COLORS, EU_AVERAGE_CODE, FIGURE_HEIGHT_STANDARD_CM, FIGURE_TITLE_SIZE, FONT_SIZE, IS_POSTER_RUN, POSTER_FIGURE_COMPACT_LABEL_SIZE, POSTER_FIGURE_LABEL_SIZE
from stattool.dataset import Dataset
from stattool.style import cm2in


# Slightly shorter than the general standard so two timeline figures plus
# two-line captions fit on one thesis page more reliably.
TIMELINE_FIGURE_HEIGHT_CM = FIGURE_HEIGHT_STANDARD_CM - 0.8

# EU-27 country codes (ISO 3166-1 alpha-2, post geo-normalisation)
EU27: frozenset[str] = frozenset([
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK",
])


def _apply_year_ticks(ax: plt.Axes, years: pd.Index) -> None:
    """Set integer-only major ticks and yearly minor ticks on both axes."""
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=8))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x)}"))
    # Minor tick every year on x
    if len(years) > 1:
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
        ax.grid(which="minor", axis="x", linewidth=0.2, alpha=0.4,
                color="#DDDDDD", zorder=0)
    # Minor ticks on y (2 per major interval)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.grid(which="minor", axis="y", linewidth=0.2, alpha=0.4,
            color="#DDDDDD", zorder=0)


def _country_color(geo: str, prop_cycle_it) -> str:
    """Return fixed color for key countries; fall back to prop cycle."""
    if geo in COUNTRY_COLORS:
        return COUNTRY_COLORS[geo]
    return next(prop_cycle_it)["color"]


def _eu_avg(ds: Dataset) -> Optional[pd.Series]:
    """Return EU27 aggregate series if present, otherwise compute mean."""
    # Try direct aggregate code first
    agg_rows = ds.df[ds.df[ds.geo_col] == EU_AVERAGE_CODE]
    if not agg_rows.empty:
        return (
            agg_rows.groupby(ds.time_col)[ds.value_col]
            .mean()
            .dropna()
        )
    # Fall back to mean over EU27 members present in the dataset
    eu_rows = ds.df[ds.df[ds.geo_col].isin(EU27)]
    if eu_rows.empty:
        return None
    return eu_rows.groupby(ds.time_col)[ds.value_col].mean().dropna()


def timeline(
    ds: Dataset,
    *,
    countries: Optional[list[str]] = None,
    title: str = "",
    ylabel: Optional[str] = None,
    xlabel: str = "rok",
    figsize: Optional[tuple[float, float]] = None,
    ax: Optional[plt.Axes] = None,
    markers: bool = False,
    highlight: Optional[list[str]] = None,
    annotate_last: bool = True,
    show_legend: bool = True,
    label_offsets: Optional[dict[str, tuple[float, float]]] = None,
    background_eu: bool = False,
    eu_norm: bool = False,
    show_eu_avg: Optional[bool] = None,
) -> plt.Figure:
    """Line chart of *ds.value_col* over time for selected countries.

    Parameters
    ----------
    countries:
        ISO-2 codes to plot as coloured lines (all ds.countries if omitted).
    highlight:
        Subset to draw with the thickest line.  Other explicitly listed
        countries remain fully opaque but slightly thinner – never faded.
    background_eu:
        Thin gray EU-27 context lines behind the coloured selection.
    eu_norm:
        Scale every series to EU27=100 (the EU average becomes a flat 100 line).
        Requires ``EU27_2020`` aggregate or computable EU mean in the dataset.
    show_eu_avg:
        Add dashed EU-average line.  Defaults to True when *eu_norm* is False
        and a usable EU aggregate exists, False when *eu_norm* is True.
    """
    geos = countries or ds.countries

    # ── EU average ────────────────────────────────────────────────────────────
    eu_series = _eu_avg(ds)

    # Normalise to EU=100 if requested
    if eu_norm and eu_series is not None and not eu_series.empty:
        norm_df = ds.df.copy()
        # Align EU series to country-year index
        norm_df["_eu"] = norm_df[ds.time_col].map(eu_series)
        norm_df[ds.value_col] = norm_df[ds.value_col] / norm_df["_eu"] * 100
        norm_df = norm_df.drop(columns=["_eu"])
        ds_plot = Dataset(norm_df, name=ds.name, unit="EU27=100",
                          geo_col=ds.geo_col, time_col=ds.time_col,
                          value_col=ds.value_col)
        ylabel_default = f"{ds.name} (EU27\u00a0=\u00a0100)"
    else:
        ds_plot = ds
        ylabel_default = f"{ds.name} [{ds.unit}]" if ds.unit else ds.name

    # default: show EU avg line only when not normalised
    if show_eu_avg is None:
        show_eu_avg = (not eu_norm) and (eu_series is not None)

    subset = ds_plot.for_countries(geos) if countries else ds_plot.df.copy()
    pivot = subset.pivot_table(
        index=ds_plot.time_col, columns=ds_plot.geo_col,
        values=ds_plot.value_col, aggfunc="mean"
    )
    ordered_cols = [g for g in geos if g in pivot.columns]
    pivot = pivot[ordered_cols]

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize or cm2in(15, TIMELINE_FIGURE_HEIGHT_CM))
    else:
        fig = ax.figure  # type: ignore[assignment]
    fig._tight_layout_kwargs = {"pad": 0.15}

    # Property cycle iterator for fallback colors
    prop_it = iter(plt.rcParams["axes.prop_cycle"])

    # ── Optional EU-27 gray background ────────────────────────────────────────
    if background_eu:
        eu_bg = EU27 - set(geos) - {EU_AVERAGE_CODE}
        bg_subset = ds_plot.for_countries(list(eu_bg))
        if not bg_subset.empty:
            bg_pivot = bg_subset.pivot_table(
                index=ds_plot.time_col, columns=ds_plot.geo_col,
                values=ds_plot.value_col, aggfunc="mean"
            )
            for _, series in bg_pivot.items():
                ax.plot(series.index, series.values,
                        color="#C8C8C8", linewidth=0.5, alpha=0.5, zorder=1)

    # ── Coloured foreground lines ─────────────────────────────────────────────
    for geo, series in pivot.items():
        color = _country_color(geo, prop_it)
        is_highlighted = highlight and geo in highlight
        # highlighted → thickest line; others → normal but still fully visible
        lw = 2.5 if is_highlighted else 1.5
        line, = ax.plot(
            series.index, series.values,
            label=geo,
            color=color,
            marker="o" if markers else None,
            markersize=3,
            linewidth=lw,
            alpha=1.0,
            zorder=3,
        )
        if annotate_last:
            valid = series.dropna()
            if not valid.empty:
                _ofs = (label_offsets or {}).get(geo, (4, 0))
                ax.annotate(
                    geo,
                    xy=(valid.index[-1], valid.iloc[-1]),
                    xytext=_ofs,
                    textcoords="offset points",
                    fontsize=POSTER_FIGURE_COMPACT_LABEL_SIZE if IS_POSTER_RUN else FONT_SIZE - 1,
                    va="center",
                    color=color,
                )

    # ── EU average dashed line ────────────────────────────────────────────────
    if show_eu_avg and eu_series is not None and not eu_series.empty:
        if eu_norm:
            # After normalisation the EU average is identically 100
            eu_vals = pd.Series(100.0, index=eu_series.index)
        else:
            eu_vals = eu_series
        ax.plot(
            eu_vals.index, eu_vals.values,
            color="#555555", linewidth=1.0, linestyle="--", alpha=0.7, zorder=2,
        )
        ax.annotate(
            "EU27",
            xy=(eu_vals.index[-1], eu_vals.iloc[-1]),
            xytext=(4, 0),
            textcoords="offset points",
            fontsize=POSTER_FIGURE_COMPACT_LABEL_SIZE if IS_POSTER_RUN else FONT_SIZE - 1,
            va="center",
            color="#555555",
            alpha=0.8,
        )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel or ylabel_default)
    if title:
        fig._suptitle_gap_pt = 5
        fig.suptitle(title, y=1.0, fontsize=FIGURE_TITLE_SIZE, va="bottom")
        if IS_POSTER_RUN:
            # Reserve top headroom so the LaTeX-inflated title is not clipped at
            # the canvas top (matplotlib measures the title shorter than LaTeX
            # renders it). Main thesis export keeps the default tight top.
            fig._subplots_adjust_kwargs = {"top": 0.90}

    # Tight x-axis + integer year ticks + minor grid
    if not pivot.empty:
        ax.set_xlim(pivot.index.min(), pivot.index.max())
        _apply_year_ticks(ax, pivot.index)

    if (not annotate_last) and show_legend:
        ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left",
                  borderaxespad=0, frameon=False,
                  fontsize=POSTER_FIGURE_LABEL_SIZE if IS_POSTER_RUN else FONT_SIZE - 1)

    # Stash the pivots so savefig_pgf() can attach \pdftooltip nodes after
    # the script has finalised xlim/ylim, and so apply_geo_labels_pgf() can
    # replace bare ISO-2 country code annotations with \acs{geo-XX}.
    fig._timeline_pivot = pivot
    if background_eu and 'bg_pivot' in locals():
        fig._timeline_pivot_bg = bg_pivot

    return fig


def timeline_groups(
    ds: Dataset,
    groups: dict[str, list[str]],
    *,
    title: str = "",
    ylabel: Optional[str] = None,
    xlabel: str = "rok",
    figsize: Optional[tuple[float, float]] = None,
    markers: bool = False,
    annotate_last: bool = True,
    eu_norm: bool = False,
    show_eu_avg: Optional[bool] = None,
) -> plt.Figure:
    """Line chart with one line per named group (average over member countries).

    Parameters
    ----------
    groups:
        Mapping of display label → list of ISO-2 codes.  Example::

            {"V4": ["CZ", "SK", "PL", "HU"], "S-EU": ["SE", "FI", "DK"]}

    eu_norm:
        Scale to EU27=100 before computing group averages.
    show_eu_avg:
        Add dashed EU-average line.  Defaults to True when *eu_norm* is False.
    """
    # EU normalisation
    eu_series = _eu_avg(ds)
    if eu_norm and eu_series is not None and not eu_series.empty:
        norm_df = ds.df.copy()
        norm_df["_eu"] = norm_df[ds.time_col].map(eu_series)
        norm_df[ds.value_col] = norm_df[ds.value_col] / norm_df["_eu"] * 100
        norm_df = norm_df.drop(columns=["_eu"])
        ds_plot = Dataset(norm_df, name=ds.name, unit="EU27=100",
                          geo_col=ds.geo_col, time_col=ds.time_col,
                          value_col=ds.value_col)
        ylabel_default = f"{ds.name} (EU27\u00a0=\u00a0100)"
    else:
        ds_plot = ds
        ylabel_default = f"{ds.name} [{ds.unit}]" if ds.unit else ds.name

    if show_eu_avg is None:
        show_eu_avg = (not eu_norm) and (eu_series is not None)

    fig, ax = plt.subplots(figsize=figsize or cm2in(15, TIMELINE_FIGURE_HEIGHT_CM))
    fig._tight_layout_kwargs = {"pad": 0.15}
    prop_it = iter(plt.rcParams["axes.prop_cycle"])

    x_min, x_max = None, None
    for label, geos in groups.items():
        subset = ds_plot.for_countries(geos)
        avg = subset.groupby(ds_plot.time_col)[ds_plot.value_col].mean().dropna()
        if avg.empty:
            continue
        # Use fixed color if group is a single country code, otherwise cycle
        color = COUNTRY_COLORS.get(label, next(prop_it)["color"])
        line, = ax.plot(
            avg.index, avg.values,
            label=label,
            color=color,
            marker="o" if markers else None,
            markersize=3,
            linewidth=1.8,
        )
        if annotate_last:
            ax.annotate(
                label,
                xy=(avg.index[-1], avg.iloc[-1]),
                xytext=(4, 0),
                textcoords="offset points",
                fontsize=FONT_SIZE,
                va="center",
                color=color,
            )
        x_min = avg.index.min() if x_min is None else min(x_min, avg.index.min())
        x_max = avg.index.max() if x_max is None else max(x_max, avg.index.max())

    # EU average dashed reference
    if show_eu_avg and eu_series is not None and not eu_series.empty:
        eu_vals = eu_series if not eu_norm else pd.Series(100.0, index=eu_series.index)
        ax.plot(eu_vals.index, eu_vals.values,
                color="#555555", linewidth=1.0, linestyle="--", alpha=0.7, zorder=2)
        ax.annotate("EU27",
                    xy=(eu_vals.index[-1], eu_vals.iloc[-1]),
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=FONT_SIZE, va="center", color="#555555", alpha=0.8)
        if x_min is not None:
            x_min = min(x_min, eu_vals.index.min())
            x_max = max(x_max, eu_vals.index.max())

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel or ylabel_default)
    if title:
        fig._suptitle_gap_pt = 5
        fig.suptitle(title, y=1.0, fontsize=FIGURE_TITLE_SIZE, va="bottom")

    if x_min is not None:
        ax.set_xlim(x_min, x_max)
        idx = pd.RangeIndex(int(x_min), int(x_max) + 1)
        _apply_year_ticks(ax, idx)

    if not annotate_last:
        ax.legend(frameon=False, fontsize=FONT_SIZE)

    return fig
