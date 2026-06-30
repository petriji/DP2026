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

from config import CMAP_SEQUENTIAL, CMAP_DIVERGING, COUNTRY_COLORS, FONT_SIZE
from stattool.dataset import Dataset
from stattool.fetch import fetch
from stattool.style import cm2in

# ── Natural Earth countries shapefile (50m) ───────────────────────────────────
# 50m keeps small EU states (e.g. Malta) that are missing in 110m.
_NE_URL = "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip"
_WORLD: "gpd.GeoDataFrame | None" = None

# ETRS89-LAEA Europe projection (Eurostat standard, equal-area → no skew)
_LAEA = "EPSG:3035"

# Default bounding box in EPSG:3035 metres — mainland Europe
# East and north cropped ~10 % to remove excess Russia/Scandinavia whitespace.
_EU_XLIM = (2_500_000, 6_640_000)
_EU_YLIM_DEFAULT = (1_400_000, 5_090_000)


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
    cbar = None
    if show_colorbar:
        cb_label = colorbar_label or (f"{ds.name} [{ds.unit}]" if ds.unit else ds.name)
        # Wrap colorbar label in \NoHyper so that hyperref boxes (from \acs{})
        # do not float horizontally next to a vertically-rotated label.
        if mpl.get_backend() == "pgf" and cb_label and "\\acs" in cb_label:
            cb_label = r"\NoHyper " + cb_label + r" \endNoHyper"
        # Fixed-size colourbar in inches (independent of axes aspect) so the
        # rasterised strip pixel dimensions are identical to map_cz output
        # and dedups to python/figures/_shared/ via content hash.
        # bbox_to_anchor x=1.10 leaves ~10pt extra gap between map and colorbar.
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        cax = inset_axes(
            ax, width=0.10, height=2.10,  # inches
            loc="center left",
            bbox_to_anchor=(1.10, 0.5),
            bbox_transform=ax.transAxes,
            borderpad=0,
        )
        cbar = fig.colorbar(sm, cax=cax, label=cb_label)

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
            lbl = geo if plain_highlight_labels else (rf"\acs{{geo-{geo}}}" if _pgf else geo)
            # Place label 3pt to the left of the marker using an offset transform.
            _label_trans = _mtx.offset_copy(trans, fig=fig, x=-3, y=0, units="points")
            cbar.ax.text(
                -0.12, val, lbl,
                color=color, fontsize=FONT_SIZE - 1,
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
                    fontsize=FONT_SIZE, va="center", ha="center",
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
                        fontsize=FONT_SIZE - 1, ha="center", va="center",
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
    # _subplots_adjust_kwargs is read by savefig() to re-apply this after
    # tight_layout() (which would otherwise clobber the top margin).
    if title:
        fig.subplots_adjust(top=0.85)
        fig._subplots_adjust_kwargs = {"top": 0.85}
        fig.suptitle(title, fontsize=plt.rcParams.get("axes.titlesize", 9),
                     y=0.95, ha="center")

    return fig
