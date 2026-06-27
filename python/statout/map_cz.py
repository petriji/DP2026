"""
CZ-centred NUTS choropleth map with coloured neighbouring regions.

Plots CZ NUTS2 (or NUTS3) regions coloured by data, with DE/AT/PL/SK NUTS2
neighbours also coloured when data is available.  National borders are drawn
as a black outline derived by dissolving the NUTS geometries per country.

Usage
-----
>>> import pandas as pd
>>> from stattool.style import apply_style
>>> from statout.map_cz import choropleth_cz
>>> apply_style()
>>> data = pd.Series({"CZ01": 4.2, "CZ02": 7.1, "DE2": 1.3})
>>> fig = choropleth_cz(data, nuts_level_cz=2, title="Cross-border commuting 2022")
>>> from stattool.style import savefig
>>> savefig(fig, "my_cz_map")
"""

from __future__ import annotations

from typing import Optional, Union
import textwrap
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as mpe
import numpy as np
import pandas as pd
from shapely.geometry import box as shapely_box

from config import (
    CMAP_SEQUENTIAL,
    CMAP_DIVERGING,
    CHOROPLETH_BLEND_WITH_WHITE,
    CHOROPLETH_WHITE_BLEND_PCT,
    FIGURE_LABEL_SIZE,
    FIGURE_TEXT_SIZE,
    FIGURE_TITLE_SIZE,
    MAP_COUNTRY_LABEL_SIZE,
    PGF_TARGET_WIDTH_CM,
)
from stattool.fetch import fetch
from stattool.style import cm2in
from statout.map_europe import CHOROPLETH_COLORBAR_HEIGHT_IN

# Default per-NUTS_ID nudges (EPSG:3035 metres).  Applied when *label_nudges*
# is not overridden by the caller.  Fixes label collisions where the
# geometric centroid of one region falls inside or on top of another:
#   - CZ010 (Prague) sits entirely inside CZ020 (Středočeský kraj); their
#     centroids are ~7 km apart and the default labels overlap.
_DEFAULT_CZ_LABEL_NUDGES: dict[str, tuple[float, float]] = {
    "CZ010": (-10_000, 7_000),    # Prague — nudge NW, out of Středočeský
    "CZ020": (30_000, -20_000),   # Středočeský — stronger SE shift to clear Prague label
}

# ── GISCO NUTS 2021 GeoJSON (20M resolution, already in EPSG:3035) ────────────
_GISCO_NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_20M_2021_3035.geojson"
)

# Neighbours always shown at NUTS2
_NEIGHBOURS = ["DE", "AT", "PL", "SK"]

# Default bounding box — tighter CZ-centred crop in EPSG:3035 metres.
# Western edge is additionally cropped by ~5% of current width for denser framing.
_CZ_XLIM_DEFAULT = (4_401_500, 5_000_000)
_CZ_YLIM_DEFAULT = (2_755_000, 3_195_000)

# Compute the natural figure height for CZ choropleth so the geographic map
# fills the column width correctly after PGF normalisation to PGF_TARGET_WIDTH_CM.
# Formula: axes_width_frac ≈ 0.826 (from column-fit with side_margin=0.03,
# cb_anchor=1.045, cb_width=0.08, 4pt gap); data_aspect = x_range / y_range.
_CZ_DATA_ASPECT = (
    (_CZ_XLIM_DEFAULT[1] - _CZ_XLIM_DEFAULT[0])
    / (_CZ_YLIM_DEFAULT[1] - _CZ_YLIM_DEFAULT[0])
)  # ≈ 1.360
_CZ_AXES_WIDTH_FRAC = 0.826  # column-fit fraction at 15 cm target width
_CZ_TOP_FRAC = 0.88           # layout_kwargs["top"] when a title is present
_CZ_BOT_FRAC = 0.01           # layout_kwargs["bottom"]
_CZ_DEFAULT_HEIGHT_CM = (
    (PGF_TARGET_WIDTH_CM * _CZ_AXES_WIDTH_FRAC / _CZ_DATA_ASPECT)
    / (_CZ_TOP_FRAC - _CZ_BOT_FRAC)
)  # ≈ 10.2 cm

# Module-level cache
_NUTS_ALL: "gpd.GeoDataFrame | None" = None


def _blend_cmap_with_white(cmap_name: str, n_colors: int = 256) -> mpl.colors.Colormap:
    """Return cmap optionally blended toward white for print-friendlier output."""
    base = plt.get_cmap(cmap_name)
    n = max(2, int(n_colors))
    rgba = base(np.linspace(0.0, 1.0, n))

    if CHOROPLETH_BLEND_WITH_WHITE:
        blend = float(CHOROPLETH_WHITE_BLEND_PCT) / 100.0
        blend = min(1.0, max(0.0, blend))
        rgba[:, :3] = rgba[:, :3] * (1.0 - blend) + blend

    return mpl.colors.LinearSegmentedColormap.from_list(
        f"{base.name}_wb{int(round(CHOROPLETH_WHITE_BLEND_PCT))}", rgba, N=n
    )


def _get_nuts_all() -> gpd.GeoDataFrame:
    """Lazy-load and cache the full GISCO NUTS GeoDataFrame."""
    global _NUTS_ALL
    if _NUTS_ALL is None:
        path = fetch(_GISCO_NUTS_URL, suffix=".geojson")
        gdf = gpd.read_file(path)
        gdf["CNTR_CODE"] = gdf["NUTS_ID"].str[:2]
        _NUTS_ALL = gdf
    return _NUTS_ALL


# ── Public API ────────────────────────────────────────────────────────────────

def choropleth_cz(
    data: Union[pd.Series, dict],
    *,
    nuts_level_cz: int = 2,
    title: str = "",
    cmap: Optional[str] = None,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    diverging: bool = False,
    missing_color: str = "#DDDDDD",
    figsize: Optional[tuple] = None,
    ax: Optional[plt.Axes] = None,
    label_cz: bool = True,
    label_nbr: bool = False,
    label_fmt: str = "{:.1f}",
    label_fontsize: Optional[float] = None,
    label_nudges: Optional[dict] = None,
    label_names: Optional[dict] = None,
    label_tooltip_fmt: Optional[str] = None,
    colorbar_label: Optional[str] = None,
    border_color: str = "black",
    border_linewidth: float = 0.8,
    region_linewidth: float = 0.3,
    region_edgecolor: str = "white",
    xlim: Optional[tuple] = None,
    ylim: Optional[tuple] = None,
) -> plt.Figure:
    """Draw a CZ-centred NUTS choropleth with coloured neighbouring regions.

    Parameters
    ----------
    data:
        Mapping of NUTS_ID -> numeric value.  Pass ``pd.Series`` or ``dict``.
        NUTS_IDs not present in *data* are rendered in *missing_color*.
    nuts_level_cz:
        NUTS level for Czech regions (2 = NUTS2, 3 = NUTS3).
    title:
        Figure title (suptitle, centred over axes + colourbar).
    cmap:
        Matplotlib colourmap name.  Defaults to ``CMAP_SEQUENTIAL`` (or
        ``CMAP_DIVERGING`` if *diverging* is True).
    vmin, vmax:
        Colour scale limits.  Derived from all displayed regions when not set.
    diverging:
        Centre the colourmap symmetrically around the midpoint.
    missing_color:
        Fill colour for regions with no data.
    figsize:
        Figure size in inches.  Defaults to ``cm2in(15, 9)`` (matches
        ``statout.map_europe.choropleth`` so colourbar rasters dedup).
    ax:
        Existing Axes to draw into.  A new figure is created when None.
    label_cz:
        Annotate CZ regions with their value (default True).
    label_nbr:
        Annotate neighbour regions with their value (default False).
    label_fmt:
        Python format string applied to each value, e.g. ``"{:.1f}"``.
    label_fontsize:
        Label font size in points.  Defaults to ``FONT_SIZE - 1``.
    label_nudges:
        Per-NUTS_ID ``(dx, dy)`` offsets (EPSG:3035 metres) added to the
        centroid before placing the label.  Useful to separate overlapping
        centroids (Prague vs. Středočeský).  Merged over sensible defaults
        for CZ010/CZ020; pass an explicit empty dict to disable.
    label_names:
        Mapping NUTS_ID → long region name, used for PGF tooltips.  When set
        together with *label_tooltip_fmt* and the PGF backend is active, the
        visible value is wrapped in ``\pdftooltip{value}{name: formatted-value}``
        so hover-capable PDF viewers show the full region name.
    label_tooltip_fmt:
        Format string for the tooltip's numeric value; defaults to *label_fmt*.
        Only used when the PGF backend is active.
    colorbar_label:
        Colourbar axis label.
    border_color:
        Colour of the national border outline (default black).
    border_linewidth:
        Line width of national borders.
    region_linewidth:
        Line width of NUTS region boundaries.
    region_edgecolor:
        Edge colour of individual NUTS region polygons.
    xlim, ylim:
        EPSG:3035 axis limits in metres.  Defaults to ``_CZ_XLIM_DEFAULT`` /
        ``_CZ_YLIM_DEFAULT``.

    Returns
    -------
    plt.Figure
    """
    if isinstance(data, dict):
        data = pd.Series(data, dtype=float)
    data = data.astype(float)

    nuts_all = _get_nuts_all()

    # ── Select geometry layers ────────────────────────────────────────────────
    cz_gdf = nuts_all[
        (nuts_all["LEVL_CODE"] == nuts_level_cz) & (nuts_all["CNTR_CODE"] == "CZ")
    ].copy()
    nbr_gdf = nuts_all[
        (nuts_all["LEVL_CODE"] == 2) & (nuts_all["CNTR_CODE"].isin(_NEIGHBOURS))
    ].copy()

    # ── Merge data ────────────────────────────────────────────────────────────
    cz_gdf["value"] = cz_gdf["NUTS_ID"].map(data)
    nbr_gdf["value"] = nbr_gdf["NUTS_ID"].map(data)

    x_lim = xlim or _CZ_XLIM_DEFAULT
    y_lim = ylim or _CZ_YLIM_DEFAULT

    # Default scale should reflect actually visible regions in the viewport.
    viewport = shapely_box(x_lim[0], y_lim[0], x_lim[1], y_lim[1])
    cz_visible = cz_gdf[cz_gdf.geometry.intersects(viewport)]
    nbr_visible = nbr_gdf[nbr_gdf.geometry.intersects(viewport)]

    # ── Unified colour scale across all displayed regions ─────────────────────
    all_values = pd.concat([cz_visible["value"], nbr_visible["value"]]).dropna()
    if all_values.empty:
        all_values = pd.concat([cz_gdf["value"], nbr_gdf["value"]]).dropna()
    vmin_ = vmin if vmin is not None else (
        float(all_values.min()) if not all_values.empty else 0.0
    )
    vmax_ = vmax if vmax is not None else (
        float(all_values.max()) if not all_values.empty else 1.0
    )

    if diverging:
        mid = (vmin_ + vmax_) / 2
        half = max(abs(vmax_ - mid), abs(vmin_ - mid))
        vmin_, vmax_ = mid - half, mid + half

    chosen_cmap = cmap or (CMAP_DIVERGING if diverging else CMAP_SEQUENTIAL)
    chosen_cmap = _blend_cmap_with_white(chosen_cmap, 256)
    norm = mpl.colors.Normalize(vmin=vmin_, vmax=vmax_)
    cmap_obj = chosen_cmap

    # ── Create figure ─────────────────────────────────────────────────────────
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize or cm2in(PGF_TARGET_WIDTH_CM, _CZ_DEFAULT_HEIGHT_CM))
    else:
        fig = ax.figure  # type: ignore[assignment]

    _is_pgf = mpl.get_backend() == "pgf"
    _font = float(label_fontsize) if label_fontsize is not None else MAP_COUNTRY_LABEL_SIZE
    _nudges: dict = dict(_DEFAULT_CZ_LABEL_NUDGES)
    if label_nudges is not None:
        _nudges.update(label_nudges)
    _names: dict = label_names or {}
    _tip_fmt = label_tooltip_fmt or label_fmt

    def _plot_layer(gdf: gpd.GeoDataFrame, do_label: bool) -> None:
        for _, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            val = row["value"]
            color = cmap_obj(norm(val)) if pd.notna(val) else missing_color
            gpd.GeoSeries([geom]).plot(
                ax=ax, color=color,
                edgecolor=region_edgecolor, linewidth=region_linewidth,
            )
            if do_label and pd.notna(val):
                nuts_id = row.get("NUTS_ID", "")
                cx, cy = geom.centroid.x, geom.centroid.y
                dx, dy = _nudges.get(nuts_id, (0.0, 0.0))
                cx, cy = cx + dx, cy + dy
                if not (x_lim[0] <= cx <= x_lim[1] and y_lim[0] <= cy <= y_lim[1]):
                    continue
                disp = label_fmt.format(val)
                if _is_pgf:
                    # Contour halo (white outline) for readability, without
                    # path_effects — which PGF renders as outlined glyph paths
                    # and therefore strips the text content entirely.
                    text = rf"\contour{{white}}{{{disp}}}"
                    if _names.get(nuts_id):
                        tip = f"{_names[nuts_id]}: {_tip_fmt.format(val)}"
                        text = rf"\pdftooltip{{{text}}}{{{tip}}}"
                    ax.text(
                        cx, cy, text,
                        ha="center", va="center",
                        fontsize=_font, color="black",
                    )
                else:
                    ax.text(
                        cx, cy, disp,
                        ha="center", va="center",
                        fontsize=_font, color="black",
                        path_effects=[
                            mpe.withStroke(linewidth=1.5, foreground="white")
                        ],
                    )

    # Draw neighbours first so CZ regions render on top
    _plot_layer(nbr_gdf, label_nbr)
    _plot_layer(cz_gdf, label_cz)

    # ── National borders — dissolved per country ──────────────────────────────
    borders = (
        pd.concat([
            cz_gdf[["CNTR_CODE", "geometry"]],
            nbr_gdf[["CNTR_CODE", "geometry"]],
        ])
        .pipe(gpd.GeoDataFrame, geometry="geometry", crs=nuts_all.crs)
        .dissolve(by="CNTR_CODE")
    )
    borders.plot(
        ax=ax, facecolor="none",
        edgecolor=border_color, linewidth=border_linewidth,
    )

    # ── Colourbar ─────────────────────────────────────────────────────────────
    sm = mpl.cm.ScalarMappable(cmap=chosen_cmap, norm=norm)
    sm.set_array([])
    # Fixed-size colourbar in inches (independent of axes aspect) so the
    # rasterised strip pixel dimensions are identical to map_europe output
    # and dedups to python/figures/_shared/ via content hash.
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    cb_width_ax = 0.08
    gap_4pt_ax = (4.0 / 72.0) / (fig.get_figwidth() * ax.get_position().width)
    cb_anchor_ax = 1.045 + gap_4pt_ax
    cax = inset_axes(
        ax, width=cb_width_ax, height=CHOROPLETH_COLORBAR_HEIGHT_IN,
        loc="center left",
        bbox_to_anchor=(cb_anchor_ax, 0.5),
        bbox_transform=ax.transAxes,
        borderpad=0,
    )
    cb = fig.colorbar(sm, cax=cax, label=colorbar_label)
    if colorbar_label:
        cb.set_label(colorbar_label, fontsize=FIGURE_LABEL_SIZE)
    cb.ax.tick_params(labelsize=FIGURE_LABEL_SIZE)

    # ── Axes formatting ───────────────────────────────────────────────────────
    ax.set_xlim(x_lim)
    ax.set_ylim(y_lim)
    ax.set_axis_off()

    # Reserve explicit right margin for colorbar ticks/label so they do not
    # protrude past the figure bbox when included at exact \linewidth width.
    # Fit (map + colorbar) into full column width with symmetric side margins.
    side_margin = 0.03
    block_factor = cb_anchor_ax + cb_width_ax
    axes_width = (1.0 - 2.0 * side_margin) / block_factor
    axes_left = side_margin
    axes_right = axes_left + axes_width
    layout_kwargs = {"left": axes_left, "right": axes_right, "bottom": 0.01}

    if title:
        # Aligned with statout.map_europe.choropleth so axes/colourbar layout
        # matches and the rasterised colourbar dedups via _shared/.
        layout_kwargs["top"] = 0.88
        fig.subplots_adjust(**layout_kwargs)
        fig._subplots_adjust_kwargs = layout_kwargs
        fig._tight_layout_kwargs = {"pad": 0.15}
        fig._suptitle_gap_pt = 4
        wrapped_title = (
            textwrap.fill(title, width=56)
            if ("\n" not in title and len(title) > 44)
            else title
        )
        fig.suptitle(
            wrapped_title,
            fontsize=FIGURE_TITLE_SIZE,
            y=0.92, ha="center",
        )
    else:
        fig.subplots_adjust(**layout_kwargs)
        fig._subplots_adjust_kwargs = layout_kwargs
        fig._tight_layout_kwargs = {"pad": 0.15}

    return fig
