"""
Europe choropleth map.

Usage
-----
>>> from stattool.style import apply_style
>>> from statout.map_europe import choropleth
>>> apply_style()
>>> fig = choropleth(ds, title="Tax wedge 2023")
>>> from stattool.style import savefig
>>> savefig(fig, "tax_wedge_2023")
"""

from __future__ import annotations

from typing import Optional
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import box as shapely_box
from shapely.ops import unary_union

from config import (
    CMAP_SEQUENTIAL,
    CMAP_DIVERGING,
    COUNTRY_COLORS,
    FIGURE_LABEL_SIZE,
    FIGURE_TEXT_SIZE,
    FIGURE_TITLE_SIZE,
    IS_POSTER_RUN,
    MAP_COUNTRY_LABEL_SIZE,
    POSTER_FIGURE_COMPACT_LABEL_SIZE,
    POSTER_FIGURE_LABEL_SIZE,
    PGF_TARGET_WIDTH_CM,
)
from stattool.dataset import Dataset
from stattool.fetch import fetch
from stattool.style import cm2in

# ── Natural Earth countries shapefile (110m) ──────────────────────────────────
# 110m keeps thesis-wide PGF output compact. Malta is added via a fallback
# marker when needed, so we do not have to load heavier 50m polygons globally.
_NE_URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
_WORLD: "gpd.GeoDataFrame | None" = None

# ETRS89-LAEA Europe projection (Eurostat standard, equal-area → no skew)
_LAEA = "EPSG:3035"

# Default bounding box in EPSG:3035 metres — mainland Europe
# East and north cropped ~10 % to remove excess Russia/Scandinavia whitespace.
_EU_XLIM = (2_500_000, 6_640_000)
_EU_YLIM_DEFAULT = (1_400_000, 5_090_000)

# Compute the natural figure height for EU choropleth so the geographic map
# fills the column width correctly after PGF normalisation to PGF_TARGET_WIDTH_CM.
# Formula: axes_width_frac ≈ 0.808 (column-fit with side_margin=0.03,
# cb_anchor=1.075, cb_width=0.08, 4pt gap); data_aspect = x_range / y_range.
_EU_DATA_ASPECT = (
    (_EU_XLIM[1] - _EU_XLIM[0])
    / (_EU_YLIM_DEFAULT[1] - _EU_YLIM_DEFAULT[0])
)  # ≈ 1.122
_EU_AXES_WIDTH_FRAC = 0.808  # column-fit fraction at 15 cm target width
_EU_TOP_FRAC = 0.88           # layout_kwargs["top"] when a title is present
_EU_BOT_FRAC = 0.01           # layout_kwargs["bottom"]
_EU_DEFAULT_HEIGHT_CM = (
    (PGF_TARGET_WIDTH_CM * _EU_AXES_WIDTH_FRAC / _EU_DATA_ASPECT)
    / (_EU_TOP_FRAC - _EU_BOT_FRAC)
)  # ≈ 12.4 cm

# Shared colorbar height used by all choropleth backends (map_europe, map_cz,
# composite panels) so the rasterised colorbar strip deduplicates to the same
# _shared/ PNG via content hash regardless of the enclosing figure height.
CHOROPLETH_COLORBAR_HEIGHT_IN: float = _EU_DEFAULT_HEIGHT_CM / 2.54 * 0.68

# Malta centroid in EPSG:3035; used when 110m Natural Earth omits MT geometry.
_MT_FALLBACK_XY = (4_719_360, 1_442_124)
_MT_LABEL_DX = 70_000


def _get_world() -> gpd.GeoDataFrame:
    global _WORLD
    if _WORLD is None:
        path = fetch(_NE_URL, suffix=".zip")
        world = gpd.read_file(path)
        if "ISO_A2_EH" in world.columns:
            world["iso_a2"] = world["ISO_A2_EH"]
        else:
            world["iso_a2"] = world["ISO_A2"]
        world.loc[world["iso_a2"] == "-99", "iso_a2"] = None
        # Reassign Crimea from Russia to Ukraine — all Natural Earth resolutions
        # incorrectly assign Crimea to RU; fix at WGS84 level before reprojection.
        crimea_box = shapely_box(32.0, 44.3, 36.8, 46.5)
        ru_mask = world["iso_a2"] == "RU"
        ua_mask = world["iso_a2"] == "UA"
        if ru_mask.any() and ua_mask.any():
            ru_geom = world.loc[ru_mask, "geometry"].iloc[0]
            ua_geom = world.loc[ua_mask, "geometry"].iloc[0]
            crimea = ru_geom.intersection(crimea_box)
            if not crimea.is_empty:
                world.loc[ru_mask, "geometry"] = ru_geom.difference(crimea_box)
                world.loc[ua_mask, "geometry"] = unary_union([ua_geom, crimea])
        _WORLD = world.to_crs(_LAEA)
    return _WORLD


def _eu_centroid(geom, bbox_poly):
    """Return centroid of *geom* after clipping to *bbox_poly*.

    Fixes cases like France (which includes French Guiana) where the raw
    centroid falls outside mainland Europe.
    """
    try:
        clipped = geom.intersection(bbox_poly)
        if clipped.is_empty:
            return geom.centroid
        return clipped.centroid
    except Exception:
        return geom.centroid


# ── Public API ────────────────────────────────────────────────────────────────

def choropleth(
    ds: Dataset,
    *,
    year: Optional[int] = None,
    title: str = "",
    cmap: Optional[str] = None,
    n_colors: int = 256,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    diverging: bool = False,
    missing_color: str = "#DDDDDD",
    figsize: Optional[tuple[float, float]] = None,
    ax: Optional[plt.Axes] = None,
    label_countries: bool = True,
    colorbar_label: Optional[str] = None,
    fill_latest: bool = True,
    ylim_south: Optional[float] = None,
    highlight_colorbar: Optional[list[str]] = None,
    plain_highlight_labels: bool = False,
    show_colorbar: bool = True,
    malta_fallback_marker: bool = True,
    country_label_size: Optional[float] = None,
    colorbar_labelpad_pt: Optional[float] = None,
) -> plt.Figure:
    # Default markers on every choropleth colorbar (key reference economies).
    if highlight_colorbar is None:
        highlight_colorbar = ["CZ", "DK", "AT", "DE", "PL", "SK"]
    """Draw a choropleth map of Europe coloured by *ds* values.

    Parameters
    ----------
    ds:
        Dataset in long tidy format.
    year:
        Year to display; defaults to latest year in dataset.
    fill_latest:
        Use latest available value for countries missing data in *year*.
    title:
        Figure title — centred over the full figure including colourbar.
    label_countries:
        Annotate each filled country with its ISO-2 code (default True).
        Centroid is computed after clipping to the EU bounding box to avoid
        overseas-territory displacement (e.g. France).
    malta_fallback_marker:
        Draw Malta as a compact point marker when MT has data but 110m source
        geometry omits it. Keeps PDF size low while preserving MT visibility.
    country_label_size:
        Font size for ISO country labels drawn on the map. If None, uses
        ``FIGURE_LABEL_SIZE``.
    ylim_south:
        Lower y-limit in EPSG:3035 metres.  Raise to crop southern extent:
        1_700_000 roughly crops Turkey; default 1_400_000 keeps it.
    """
    year = year or ds.latest_year
    label_fs = (
        POSTER_FIGURE_COMPACT_LABEL_SIZE if IS_POSTER_RUN and country_label_size is None
        else (MAP_COUNTRY_LABEL_SIZE if country_label_size is None
              else float(country_label_size))
    )

    if fill_latest:
        exact = ds.for_year(year).set_index(ds.geo_col)[ds.value_col]
        latest = (
            ds.df[ds.df[ds.time_col] <= year]
            .sort_values(ds.time_col)
            .groupby(ds.geo_col)[ds.value_col]
            .last()
        )
        values = latest.copy()
        values.update(exact.dropna())
        row = values.reset_index()
        row.columns = [ds.geo_col, ds.value_col]
    else:
        row = ds.for_year(year)

    ys_min = ylim_south if ylim_south is not None else _EU_YLIM_DEFAULT[0]
    eu_ylim = (ys_min, _EU_YLIM_DEFAULT[1])
    bbox_poly = shapely_box(_EU_XLIM[0], eu_ylim[0], _EU_XLIM[1], eu_ylim[1])

    world = _get_world()
    merged = world.merge(
        row[[ds.geo_col, ds.value_col]].rename(
            columns={ds.geo_col: "iso_a2", ds.value_col: "value"}
        ),
        on="iso_a2",
        how="left",
    )

    europe = merged.cx[_EU_XLIM[0]:_EU_XLIM[1], eu_ylim[0]:eu_ylim[1]]

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize or cm2in(PGF_TARGET_WIDTH_CM, _EU_DEFAULT_HEIGHT_CM))
    else:
        fig = ax.figure  # type: ignore[assignment]

    # Keep EU choropleths on a unified label-placement baseline.
    # Timeline and line/scatter figures may still use nudge macros,
    # but map labels should stay at map_europe centroid positions.
    fig._apply_label_nudges = False
    # When analyses pass country-code nudge labels ("CZ", "DK", ...),
    # constrain matching to colorbar-side geo labels only.
    fig._nudge_geo_colorbar_only = True

    chosen_cmap = cmap or (CMAP_DIVERGING if diverging else CMAP_SEQUENTIAL)
    # Resample to n_colors levels when requested (improves visual gradation)
    if n_colors != 256:
        base = plt.get_cmap(chosen_cmap)
        chosen_cmap = mpl.colors.LinearSegmentedColormap.from_list(
            f"{chosen_cmap}_{n_colors}", base(np.linspace(0, 1, n_colors)), N=n_colors
        )

    europe[europe["value"].isna()].plot(
        ax=ax, color=missing_color, linewidth=0.3, edgecolor="white"
    )

    vmin_ = vmin if vmin is not None else europe["value"].min()
    vmax_ = vmax if vmax is not None else europe["value"].max()

    if diverging:
        mid = (vmin_ + vmax_) / 2
        abs_range = max(abs(vmax_ - mid), abs(vmin_ - mid))
        vmin_, vmax_ = mid - abs_range, mid + abs_range

    norm = mpl.colors.Normalize(vmin=vmin_, vmax=vmax_)
    filled = europe.dropna(subset=["value"])
    filled.plot(
        column="value",
        ax=ax,
        cmap=chosen_cmap,
        norm=norm,
        linewidth=0.3,
        edgecolor="white",
    )

    sm = mpl.cm.ScalarMappable(cmap=chosen_cmap, norm=norm)
    sm.set_array([])
    cbar = None
    cbar_extra_right_ax = 0.0
    title_center_x = 0.5
    if show_colorbar:
        cb_label = colorbar_label or (f"{ds.name} [{ds.unit}]" if ds.unit else ds.name)
        # Wrap colorbar label in \NoHyper so that hyperref boxes (from \acs{})
        # do not float horizontally next to a vertically-rotated label.
        if mpl.get_backend() == "pgf" and cb_label and "\\acs" in cb_label:
            cb_label = r"\NoHyper " + cb_label + r"\endNoHyper"
        # Fixed-size colourbar in inches (independent of axes aspect) so the
        # rasterised strip pixel dimensions are identical to map_cz output
        # and dedups to python/figures/_shared/ via content hash.
        # Keep the colorbar close enough to the map that the label still fits
        # inside the column width once the figure is normalized to PGF width.
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        cb_width_ax = 0.08
        gap_4pt_ax = (4.0 / 72.0) / (fig.get_figwidth() * ax.get_position().width)
        gap_2pt_ax = (2.0 / 72.0) / (fig.get_figwidth() * ax.get_position().width)
        # Keep the existing 8pt separation and add another 2pt as requested.
        cb_anchor_ax = 1.020 + gap_4pt_ax + gap_4pt_ax + gap_2pt_ax
        cax = inset_axes(
            ax, width=cb_width_ax, height=CHOROPLETH_COLORBAR_HEIGHT_IN,
            loc="center left",
            bbox_to_anchor=(cb_anchor_ax, 0.5),
            bbox_transform=ax.transAxes,
            borderpad=0,
        )
        cbar = fig.colorbar(sm, cax=cax, label=cb_label)
        if IS_POSTER_RUN:
            # Poster: colorbar ticks and labels match poster country label size.
            # extra labelpad so Czech descenders (p, y, j, g) are not clipped.
            _cbar_fs = POSTER_FIGURE_LABEL_SIZE
            cbar.ax.tick_params(labelsize=_cbar_fs)
            cbar.ax.yaxis.label.set_fontsize(_cbar_fs)
            cbar.ax.yaxis.label.set_rotation(90)
            cbar.ax.yaxis.labelpad = 10 if colorbar_labelpad_pt is None else float(colorbar_labelpad_pt)

        # Estimate right-side content width purely from typographic metrics.
        # Agg pixel measurements in PGF mode overestimate LaTeX/CM glyph widths
        # by ~2×, producing an over-wide block_factor and empty right space.
        # Strategy: char_count × 0.50 em (CM tabular digit) + labelpad + 1 em label.
        fig.canvas.draw()  # populate tick label text
        _tick_strs = [
            t.get_text() for t in cbar.ax.get_yticklabels() if t.get_text().strip()
        ]
        _max_chars = max((len(s) for s in _tick_strs), default=2)
        _fs = float(IS_POSTER_RUN and POSTER_FIGURE_LABEL_SIZE or FIGURE_LABEL_SIZE)
        # right-side content in pt: compact estimate tuned to LaTeX output
        # (digits in CM are narrower than Agg reports for PGF previews).
        _right_content_pt = _max_chars * _fs * 0.38 + 2.0 + (_fs * 0.45)
        # Convert to figure fraction (pt → inches → fraction)
        _right_content_frac = _right_content_pt / 72.0 / fig.get_figwidth()

    if highlight_colorbar and cbar is not None:
        import matplotlib.transforms as _mtx
        _pgf = mpl.get_backend() == "pgf"
        _val_lookup: dict[str, float] = {
            geo: float(v)
            for geo, v in zip(row[ds.geo_col], row[ds.value_col])
            if v == v  # drop NaN
        }
        for geo in highlight_colorbar:
            if geo not in COUNTRY_COLORS or geo not in _val_lookup:
                continue
            val = _val_lookup[geo]
            if not (norm.vmin <= val <= norm.vmax):
                continue
            color = COUNTRY_COLORS[geo]
            trans = _mtx.blended_transform_factory(
                cbar.ax.transAxes, cbar.ax.transData
            )
            cbar.ax.axhline(y=val, color=color, linewidth=1.5, alpha=0.85, zorder=5)
            # Marker on the LEFT side of colorbar (negative axes x-coord)
            # marker=">" points rightward toward the colorbar strip.
            cbar.ax.plot(
                [-0.12], [val], marker=">", markersize=4,
                color=color, clip_on=False, zorder=6, transform=trans,
            )
            # In PGF/main.tex context, acro labels render as \acs{geo-XX}.
            # For standalone PDF exports, callers can force plain ISO labels.
            lbl = geo if plain_highlight_labels else (rf"\acs{{geo-{geo}}}\relax" if _pgf else geo)
            # Place label 3pt to the left of the marker using an offset transform.
            _label_trans = _mtx.offset_copy(trans, fig=fig, x=-3, y=0, units="points")
            cbar.ax.text(
                -0.12, val, lbl,
                color=color,
                fontsize=(POSTER_FIGURE_COMPACT_LABEL_SIZE if IS_POSTER_RUN else FIGURE_LABEL_SIZE),
                va="center", ha="right",
                transform=_label_trans, clip_on=False,
            )
            # Invisible phantom tooltip on the marker (PGF only).
            # The visible label is already printed; tooltip shows just the value.
            if _pgf:
                val_str = f"{val:.2f}"
                cbar.ax.text(
                    -0.12, val,
                    r"\pdftooltip{\phantom{\rule{3pt}{3pt}}}{" + val_str + r"}",
                    fontsize=(POSTER_FIGURE_COMPACT_LABEL_SIZE if IS_POSTER_RUN else FIGURE_LABEL_SIZE),
                    va="center", ha="center",
                    transform=trans, clip_on=False, zorder=7,
                )

    if label_countries:
        for _, row_ in filled.iterrows():
            code = row_["iso_a2"]
            if not code:
                continue
            pt = _eu_centroid(row_.geometry, bbox_poly)
            # Only label if centroid is within the displayed extent
            if (_EU_XLIM[0] <= pt.x <= _EU_XLIM[1] and
                    eu_ylim[0] <= pt.y <= eu_ylim[1]):
                ax.text(pt.x, pt.y, code,
                    fontsize=label_fs, ha="center", va="center",
                        color="black", fontweight="bold",
                        path_effects=[
                            __import__("matplotlib.patheffects", fromlist=["withStroke"])
                            .withStroke(linewidth=1.5, foreground="white")
                        ])

    # Malta fallback for lightweight 110m source: if MT has data but no geometry,
    # draw a colored point and label so maps still show Malta without 50m bloat.
    if malta_fallback_marker:
        has_mt_geom = bool((europe["iso_a2"] == "MT").any())
        mt_vals = row.loc[row[ds.geo_col] == "MT", ds.value_col].dropna()
        if (not has_mt_geom) and (not mt_vals.empty):
            mt_val = float(mt_vals.iloc[-1])
            mx, my = _MT_FALLBACK_XY
            if (_EU_XLIM[0] <= mx <= _EU_XLIM[1]) and (eu_ylim[0] <= my <= eu_ylim[1]):
                mt_color = sm.cmap(norm(mt_val))
                ax.scatter(
                    [mx], [my],
                    s=28,
                    marker="o",
                    c=[mt_color],
                    edgecolors="white",
                    linewidths=0.5,
                    zorder=8,
                )
                import matplotlib.transforms as _mtx
                _mt_label_trans = _mtx.offset_copy(
                    ax.transData, fig=fig, x=0, y=3, units="points"
                )
                ax.text(
                    mx + _MT_LABEL_DX,
                    my,
                    "MT",
                    fontsize=label_fs,
                    ha="left",
                    va="center",
                    color="black",
                    fontweight="bold",
                    transform=_mt_label_trans,
                    path_effects=[
                        __import__("matplotlib.patheffects", fromlist=["withStroke"])
                        .withStroke(linewidth=1.5, foreground="white")
                    ],
                    zorder=9,
                )
                if mpl.get_backend() == "pgf":
                    tip = f"MT: {mt_val:.2f}"
                    ax.text(
                        mx,
                        my,
                        r"\pdftooltip{\phantom{\rule{3pt}{3pt}}}{" + tip + r"}",
                        fontsize=FIGURE_LABEL_SIZE,
                        ha="center",
                        va="center",
                        zorder=10,
                    )

    ax.set_xlim(_EU_XLIM)
    ax.set_ylim(eu_ylim)
    ax.set_axis_off()

    # Title centred over the full figure (axes + colourbar) with compact padding.
    # _subplots_adjust_kwargs is read by savefig() to re-apply this after
    # tight_layout() (which would otherwise clobber the margins).
    auto_figsize = figsize is None and ax is None

    if show_colorbar:
        # Fit the whole block (map + colorbar + right label content), then center it
        # and nudge slightly right so optical alignment matches surrounding text.
        side_margin = 0.01
        axes_width = (
            (1.0 - (2.0 * side_margin) - _right_content_frac)
            / (cb_anchor_ax + cb_width_ax)
        )
        block_width = axes_width * (cb_anchor_ax + cb_width_ax) + _right_content_frac
        # Previous +4pt shift was still visually left; add +20pt more.
        center_shift_right = (24.0 / 72.0) / fig.get_figwidth()
        axes_left = ((1.0 - block_width) / 2.0) + center_shift_right
        max_left = 1.0 - block_width
        axes_left = min(max_left, max(0.0, axes_left))
        title_center_x = axes_left + (block_width / 2.0)
        axes_right = axes_left + axes_width
        layout_kwargs = {"left": axes_left, "right": axes_right, "bottom": _EU_BOT_FRAC}
    else:
        layout_kwargs = {"left": 0.03, "right": 0.97, "bottom": _EU_BOT_FRAC}
    if title:
        layout_kwargs["top"] = _EU_TOP_FRAC
        fig.subplots_adjust(**layout_kwargs)
        fig._subplots_adjust_kwargs = layout_kwargs
        fig._tight_layout_kwargs = {"pad": 0.1}
        # Keep exactly the intended gap to map content; savefig_pgf trims the
        # vertical canvas while preserving column width.
        fig._suptitle_gap_pt = 4
        fig._pgf_trim_vertical = True
        fig.suptitle(
            title,
            fontsize=FIGURE_TITLE_SIZE,
            y=0.940,
            x=title_center_x,
            ha="center",
        )
    else:
        fig.subplots_adjust(**layout_kwargs)
        fig._subplots_adjust_kwargs = layout_kwargs
        fig._tight_layout_kwargs = {"pad": 0.15}

    if auto_figsize:
        top_frac = float(layout_kwargs.get("top", 0.88))
        bottom_frac = float(layout_kwargs.get("bottom", 0.01))
        axes_width_frac = float(layout_kwargs["right"] - layout_kwargs["left"])
        y_span = eu_ylim[1] - eu_ylim[0]
        if y_span > 0 and top_frac > bottom_frac:
            data_aspect = (_EU_XLIM[1] - _EU_XLIM[0]) / y_span
            target_h_in = (
                (fig.get_figwidth() * axes_width_frac / data_aspect)
                / (top_frac - bottom_frac)
            )
            if target_h_in > 0 and abs(target_h_in - fig.get_figheight()) > 0.02:
                fig.set_size_inches(fig.get_figwidth(), target_h_in, forward=True)
                fig.subplots_adjust(**layout_kwargs)
                fig._subplots_adjust_kwargs = layout_kwargs

    return fig
