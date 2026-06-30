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

from config import CMAP_SEQUENTIAL, CMAP_DIVERGING, FONT_SIZE
from stattool.dataset import Dataset
from stattool.fetch import fetch
from stattool.style import cm2in

# ── Natural Earth countries shapefile (110m) ──────────────────────────────────
_NE_URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
_WORLD: "gpd.GeoDataFrame | None" = None

# ETRS89-LAEA Europe projection (Eurostat standard, equal-area → no skew)
_LAEA = "EPSG:3035"

# Default bounding box in EPSG:3035 metres — mainland Europe
_EU_XLIM = (2_500_000, 7_100_000)
_EU_YLIM_DEFAULT = (1_400_000, 5_500_000)


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
) -> plt.Figure:
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
    ylim_south:
        Lower y-limit in EPSG:3035 metres.  Raise to crop southern extent:
        1_700_000 roughly crops Turkey; default 1_400_000 keeps it.
    """
    year = year or ds.latest_year

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
        fig, ax = plt.subplots(figsize=figsize or cm2in(15, 11))
    else:
        fig = ax.figure  # type: ignore[assignment]

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
    cb_label = colorbar_label or (f"{ds.name} [{ds.unit}]" if ds.unit else ds.name)
    fig.colorbar(sm, ax=ax, shrink=0.6, label=cb_label)

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
                        fontsize=FONT_SIZE, ha="center", va="center",
                        color="black", fontweight="bold",
                        path_effects=[
                            __import__("matplotlib.patheffects", fromlist=["withStroke"])
                            .withStroke(linewidth=1.5, foreground="white")
                        ])

    ax.set_xlim(_EU_XLIM)
    ax.set_ylim(eu_ylim)
    ax.set_axis_off()

    # Title centred over the full figure (axes + colourbar)
    # top=0.85 leaves ~5 pt more space between map and title than default.
    if title:
        fig.subplots_adjust(top=0.85)
        fig.suptitle(title, fontsize=plt.rcParams.get("axes.titlesize", 9),
                     y=0.95, ha="center")

    return fig
