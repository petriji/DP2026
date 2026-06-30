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
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as mpe
import pandas as pd

from config import CMAP_SEQUENTIAL, CMAP_DIVERGING, FONT_SIZE
from stattool.fetch import fetch
from stattool.style import cm2in

# ── GISCO NUTS 2021 GeoJSON (20M resolution, already in EPSG:3035) ────────────
_GISCO_NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_20M_2021_3035.geojson"
)

# Neighbours always shown at NUTS2
_NEIGHBOURS = ["DE", "AT", "PL", "SK"]

# Default bounding box — tighter CZ-centred crop in EPSG:3035 metres (~1.5x zoom vs old)
_CZ_XLIM_DEFAULT = (4_300_000, 5_000_000)
_CZ_YLIM_DEFAULT = (2_700_000, 3_250_000)

# Module-level cache
_NUTS_ALL: "gpd.GeoDataFrame | None" = None


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
        Figure size in inches.  Defaults to ``cm2in(15, 10)``.
    ax:
        Existing Axes to draw into.  A new figure is created when None.
    label_cz:
        Annotate CZ regions with their value (default True).
    label_nbr:
        Annotate neighbour regions with their value (default False).
    label_fmt:
        Python format string applied to each value, e.g. ``"{:.1f}"``.
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

    # ── Unified colour scale across all displayed regions ─────────────────────
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
    norm = mpl.colors.Normalize(vmin=vmin_, vmax=vmax_)
    cmap_obj = plt.get_cmap(chosen_cmap)

    # ── Create figure ─────────────────────────────────────────────────────────
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize or cm2in(15, 10))
    else:
        fig = ax.figure  # type: ignore[assignment]

    x_lim = xlim or _CZ_XLIM_DEFAULT
    y_lim = ylim or _CZ_YLIM_DEFAULT

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
                cx, cy = geom.centroid.x, geom.centroid.y
                if x_lim[0] <= cx <= x_lim[1] and y_lim[0] <= cy <= y_lim[1]:
                    ax.text(
                        cx, cy, label_fmt.format(val),
                        ha="center", va="center",
                        fontsize=FONT_SIZE - 1, color="black",
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
    cb = fig.colorbar(sm, ax=ax, shrink=0.7, pad=0.02)
    if colorbar_label:
        cb.set_label(colorbar_label, fontsize=FONT_SIZE)
    cb.ax.tick_params(labelsize=FONT_SIZE - 1)

    # ── Axes formatting ───────────────────────────────────────────────────────
    ax.set_xlim(x_lim)
    ax.set_ylim(y_lim)
    ax.set_axis_off()

    if title:
        fig.subplots_adjust(top=0.88)
        fig.suptitle(
            title,
            fontsize=plt.rcParams.get("axes.titlesize", 9),
            y=0.97, ha="center",
        )

    return fig
