r"""
Equilateral ternary diagram — reusable template for three-party share plots.

Vertex layout (A at top, CCW from A):
    A = (0.5,  H)  — vertex_labels[0]  (increases toward apex)
    B = (0,    0)  — vertex_labels[1]  (bottom-left)
    C = (1,    0)  — vertex_labels[2]  (bottom-right)
where ``H = sqrt(3)/2``.

The RGB heatmap background is rasterised to a companion PNG when saved via
``savefig_pgf()``.  The PNG is deduplicated by content hash in the
``_shared/`` directory so the same image is never stored twice, keeping
the final PDF lightweight (typically 80–150 KB for a 500-pixel image).

Public API
----------
barycentric_to_cartesian(a, b, c) -> (x, y)
    Convert three normalised shares to 2-D Cartesian.

ternary_diagram(data, colors, vertex_labels, title, ...) -> plt.Figure
    Build a complete ternary diagram with RGB heatmap background, major/minor
    grid, rotated tick marks, axis arrows with 0/100 markers, optional corner labels,
    and labelled country scatter points.

Usage
-----
>>> from stattool.style import apply_style_pgf
>>> from statout.ternary import ternary_diagram
>>> apply_style_pgf()
>>> fig = ternary_diagram(
...     data={"CZ": (16, 47, 37), "DK": (33, 33, 34)},
...     colors={"CZ": "#D62728", "DK": "#FF7F0E"},
...     vertex_labels=("Zaměstnanci", "Zaměstnavatelé", "Vláda"),
...     title="Tripartitní rovnováha v EU",
... )
"""
from __future__ import annotations

import math

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np

from config import FONT_SIZE
from stattool.style import GEO_LONG_NAMES

# ── Constants ─────────────────────────────────────────────────────────────────

_H: float = math.sqrt(3.0) / 2.0    # height of a unit equilateral triangle
_GRID_COLOR: str = "#444444"         # dark-charcoal grid lines


# ── Geometry ──────────────────────────────────────────────────────────────────

def barycentric_to_cartesian(a: float, b: float, c: float) -> tuple[float, float]:
    """Convert ternary shares (a, b, c) to 2-D Cartesian (x, y).

    Vertex layout:
        A = (0.5, H)  — top           (a = 1 → pure A vertex)
        B = (0,   0)  — bottom-left   (b = 1 → pure B vertex)
        C = (1,   0)  — bottom-right  (c = 1 → pure C vertex)

    Shares need not sum to 100; they are normalised internally.
    """
    total = a + b + c
    a, b, c = a / total, b / total, c / total
    return 0.5 * a + c, _H * a


# ── Heatmap background ────────────────────────────────────────────────────────

def _build_background(resolution: int = 500, bg_alpha: float = 0.20) -> np.ndarray:
    """RGBA simplex heatmap: R = A-share, G = C-share, B = B-share.

    Pixels outside the triangle have alpha = 0; inside pixels have alpha =
    *bg_alpha*.  Higher *bg_alpha* produces a more vivid colour gradient.
    The array is rasterised to a PNG companion by matplotlib's PGF backend
    and deduplicated by content hash, so changing *bg_alpha* produces a new
    PNG only when the pixel values actually differ.
    """
    xs = np.linspace(0.0, 1.0, resolution)
    ys = np.linspace(0.0, _H, resolution)
    xg, yg = np.meshgrid(xs, ys)

    # Barycentric coordinates (A-at-top orientation)
    a = 2.0 * yg / math.sqrt(3.0)            # 1 at apex A, 0 at base BC
    b = 1.0 - xg - yg / math.sqrt(3.0)       # 1 at vertex B (bottom-left)
    c = xg - yg / math.sqrt(3.0)             # 1 at vertex C (bottom-right)

    inside = (a >= 0.0) & (b >= 0.0) & (c >= 0.0)
    alpha_ch = np.where(inside, bg_alpha, 0.0)

    return np.stack([
        np.clip(a, 0.0, 1.0),   # R = A-share (top vertex)
        np.clip(c, 0.0, 1.0),   # G = C-share (bottom-right)
        np.clip(b, 0.0, 1.0),   # B = B-share (bottom-left)
        alpha_ch,
    ], axis=-1)


# ── Grid and tick marks ───────────────────────────────────────────────────────

def _draw_grid_and_ticks(ax: plt.Axes) -> None:
    """Major (20 %) and minor (10 %) ternary grid lines with edge ticks.

    Tick *marks* (not numerals) are oriented to match the grid direction of
    each axis:
      - A-axis ticks:   0 °   (constant-a lines are horizontal)
      - B-axis ticks: -60 °   (constant-b lines are parallel to AC)
      - C-axis ticks: +60 °   (constant-c lines are parallel to AB)
    """
    major_levels = [0.2, 0.4, 0.6, 0.8]
    minor_levels = [0.1, 0.3, 0.5, 0.7, 0.9]

    for levels, lw, alpha, ls in [
        (major_levels, 0.55, 0.45, "-"),
        (minor_levels, 0.28, 0.25, ":"),
    ]:
        for k in levels:
            # Constant-a isolines (horizontal, parallel to base BC)
            ax.plot([k / 2, 1 - k / 2], [k * _H, k * _H],
                    color=_GRID_COLOR, ls=ls, lw=lw, alpha=alpha, zorder=2)
            # Constant-b isolines (parallel to right edge AC)
            ax.plot([1 - k, (1 - k) / 2], [0, (1 - k) * _H],
                    color=_GRID_COLOR, ls=ls, lw=lw, alpha=alpha, zorder=2)
            # Constant-c isolines (parallel to left edge AB)
            ax.plot([k, (1 + k) / 2], [0, (1 - k) * _H],
                    color=_GRID_COLOR, ls=ls, lw=lw, alpha=alpha, zorder=2)

    T = 0.036    # tick length (data units), 200% vs original 0.018
    _FS = FONT_SIZE
    v_a = np.array([1.0, 0.0])
    v_b = np.array([0.5, -_H])
    v_c = np.array([0.5, _H])
    n_a = np.array([-_H, 0.5])
    n_b = np.array([0.0, -1.0])
    n_c = np.array([_H, 0.5])
    # Tick numeral offset in pt — scale-independent, same visual distance in all variants
    _TN_AC = 14.0   # A- and C-axis tick numeral offset (pt)
    _TN_B  = 12.0   # B-axis tick numeral offset (pt)

    for k in major_levels:
        pct = int(round(k * 100))

        # ── A-axis: tick mark rotated to 0° (horizontal) ─────────────────
        p_a = np.array([k / 2, k * _H])
        a0 = p_a - 0.5 * T * v_a
        a1 = p_a + 0.5 * T * v_a
        ax.plot([a0[0], a1[0]], [a0[1], a1[1]],
                color="black", lw=0.8, zorder=4, solid_capstyle="butt")
        ax.annotate(f"{pct}", xy=tuple(p_a),
                xytext=(n_a[0] * _TN_AC, n_a[1] * _TN_AC),
                textcoords="offset points",
                ha="center", va="center", fontsize=_FS, color="#222222")

        # ── B-axis: tick mark rotated to -60° ─────────────────────────────
        p_b = np.array([1 - k, 0.0])
        b0 = p_b - 0.5 * T * v_b
        b1 = p_b + 0.5 * T * v_b
        ax.plot([b0[0], b1[0]], [b0[1], b1[1]],
                color="black", lw=0.8, zorder=4, solid_capstyle="butt")
        ax.annotate(f"{pct}", xy=tuple(p_b),
                xytext=(n_b[0] * _TN_B, n_b[1] * _TN_B),
                textcoords="offset points",
                ha="center", va="top", fontsize=_FS, color="#222222")

        # ── C-axis: tick mark rotated to +60° ─────────────────────────────
        p_c = np.array([(1 + k) / 2, (1 - k) * _H])
        c0 = p_c - 0.5 * T * v_c
        c1 = p_c + 0.5 * T * v_c
        ax.plot([c0[0], c1[0]], [c0[1], c1[1]],
                color="black", lw=0.8, zorder=4, solid_capstyle="butt")
        ax.annotate(f"{pct}", xy=tuple(p_c),
                xytext=(n_c[0] * _TN_AC, n_c[1] * _TN_AC),
                textcoords="offset points",
                ha="center", va="center", fontsize=_FS, color="#222222")


def _draw_equilibrium_distance_circles(
    ax: plt.Axes,
    levels: tuple[float, ...] = (0.2, 0.4, 0.6, 0.8),
) -> None:
    """Draw concentric circles around the barycentric equilibrium point.

    The circles represent increasing Euclidean distance from equilibrium
    (A=B=C=1/3). Styling follows the minor ternary grid (dotted, subtle).
    """
    center_x = 0.5
    center_y = _H / 3.0
    max_radius = _H / 3.0  # inradius of the unit equilateral triangle

    for lvl in levels:
        if lvl <= 0.0:
            continue
        radius = max_radius * min(lvl, 1.0)
        circle = plt.Circle(
            (center_x, center_y),
            radius,
            fill=False,
            color=_GRID_COLOR,
            linestyle=":",
            linewidth=0.28,
            alpha=0.25,
            zorder=2,
        )
        ax.add_patch(circle)


# ── Axis arrows, corner labels, and 0/100 end-markers ─────────────────────────

def _draw_axis_arrows(
    ax: plt.Axes,
    vertex_labels: tuple[str, str, str],
    show_corner_labels: bool,
) -> None:
    """Outer directional arrows with 0/100 end-markers and bold axis-name labels.

    Axis-name labels are rotated parallel to their corresponding arrows.
    Corner labels are optional and positioned inward to avoid overlap with
    the 0/100 end markers.

    Geometry offsets (all in data units):
        off        — outward distance from edge to arrow shaft
        lbl_gap    — extra outward gap from arrow to bold axis-name text
        end_gap    — gap beyond arrowhead/tail for 0/100 markers
        corner_a_up — upward offset from apex A
        corner_x    — horizontal offset from base corners B/C
        corner_down — downward offset from base corners B/C
    """
    off       = 0.068   # edge → arrow shaft
    lbl_gap   = 0.0225  # arrow shaft → bold label (half of previous spacing)
    end_gap   = 0.024   # arrowhead/tail → 0 / 100 marker (A/C axes)
    end_gap_b = 0.036   # extra spacing for B-axis 0 % / 100 % markers
    end_gap_b_100_extra = 0.014  # ~4 pt extra for B-axis 100 % only

    Bv = np.array([0.0, 0.0])
    Av = np.array([0.5, _H])
    Cv = np.array([1.0, 0.0])

    _akw = dict(arrowstyle="->", color="black", lw=1.2, mutation_scale=14)
    _FS  = FONT_SIZE       # end-marker font size (same as tick labels)

    # ── A-axis: left edge B→A, vertex_labels[0] increases toward A ───────────
    d_a = Av - Bv                     # direction B→A (unit length since |BA|=1)
    n_a = np.array([-_H, 0.5])        # unit outward normal of edge AB
    s_a = Bv + n_a * off
    e_a = Av + n_a * off
    ax.annotate("", xy=e_a, xytext=s_a, arrowprops=_akw,
                xycoords="data", textcoords="data")
    ax.text(*(s_a - d_a * end_gap), "0 %",
            ha="center", va="center", fontsize=_FS, color="#333333", zorder=5)
    ax.text(*(e_a + d_a * end_gap), "100 %",
            ha="center", va="center", fontsize=_FS, color="#333333", zorder=5)
    mid_a = (s_a + e_a) / 2.0
    ax.text(*(mid_a + n_a * lbl_gap), vertex_labels[0],
            ha="center", va="center", fontsize=FONT_SIZE - 1, weight="bold",
            rotation=60, zorder=5)

    # ── B-axis: bottom edge C→B, vertex_labels[1] increases toward B ─────────
    d_b = Bv - Cv                     # direction C→B
    n_b = np.array([0.0, -1.0])       # unit outward normal of edge BC (downward)
    s_b = Cv + n_b * off
    e_b = Bv + n_b * off
    ax.annotate("", xy=e_b, xytext=s_b, arrowprops=_akw,
                xycoords="data", textcoords="data")
    ax.text(*(s_b - d_b * end_gap_b), "0 %",
            ha="center", va="center", fontsize=_FS, color="#333333", zorder=5)
    ax.text(*(e_b + d_b * (end_gap_b + end_gap_b_100_extra)), "100 %",
            ha="center", va="center", fontsize=_FS, color="#333333", zorder=5)
    mid_b = (s_b + e_b) / 2.0
    ax.text(*(mid_b + n_b * lbl_gap), vertex_labels[1],
            ha="center", va="top", fontsize=FONT_SIZE - 1, weight="bold", rotation=0, zorder=5)

    # ── C-axis: right edge A→C, vertex_labels[2] increases toward C ──────────
    d_c = Cv - Av                     # direction A→C
    n_c = np.array([_H, 0.5])         # unit outward normal of edge AC (rightward)
    s_c = Av + n_c * off
    e_c = Cv + n_c * off
    ax.annotate("", xy=e_c, xytext=s_c, arrowprops=_akw,
                xycoords="data", textcoords="data")
    ax.text(*(s_c - d_c * end_gap), "0 %",
            ha="center", va="center", fontsize=_FS, color="#333333", zorder=5)
    ax.text(*(e_c + d_c * end_gap), "100 %",
            ha="center", va="center", fontsize=_FS, color="#333333", zorder=5)
    mid_c = (s_c + e_c) / 2.0
    ax.text(*(mid_c + n_c * lbl_gap), vertex_labels[2],
            ha="center", va="center", fontsize=FONT_SIZE - 1, weight="bold",
            rotation=-60, zorder=5)

    if show_corner_labels:
        # Corner labels (non-italic), shifted outward from vertices.
        corner_a_up = 0.092
        corner_x = 0.050
        corner_down = 0.133
        corner_up_pts = 10
        ax.text(Av[0], Av[1] + corner_a_up, vertex_labels[0],
            ha="center", va="bottom", fontsize=FONT_SIZE - 1, weight="bold", zorder=5)
        ax.annotate(
            vertex_labels[1],
            (Bv[0] - corner_x, Bv[1] - corner_down),
            xytext=(0, corner_up_pts),
            textcoords="offset points",
            ha="right", va="top", fontsize=FONT_SIZE - 1, weight="bold", zorder=5,
            annotation_clip=False,
        )
        ax.annotate(
            vertex_labels[2],
            (Cv[0] + corner_x, Cv[1] - corner_down),
            xytext=(0, corner_up_pts),
            textcoords="offset points",
            ha="left", va="top", fontsize=FONT_SIZE - 1, weight="bold", zorder=5,
            annotation_clip=False,
        )


# ── Hover tooltips ────────────────────────────────────────────────────────────

def _add_ternary_tooltips(
    ax: plt.Axes,
    data: dict[str, tuple[float, float, float]],
    vertex_labels: tuple[str, str, str],
) -> None:
    r"""Invisible \pdftooltip anchors at each data point (PGF backend only).

    Tooltip text format: "Country: A_label A% / B_label B% / C_label C%".
    No-op when the active backend is not ``pgf``.
    """
    if mpl.get_backend() != "pgf":
        return
    a_lbl, b_lbl, c_lbl = vertex_labels
    for country, (a, b, c) in data.items():
        px, py = barycentric_to_cartesian(a, b, c)
        country_label = GEO_LONG_NAMES.get(country, country)
        tip = (
            f"{country_label}: "
            f"{a_lbl} {int(round(a))}\\% / "
            f"{b_lbl} {int(round(b))}\\% / "
            f"{c_lbl} {int(round(c))}\\%"
        )
        ax.text(
            px, py,
            r"\pdftooltip{\phantom{\rule{4pt}{4pt}}}{" + tip + r"}",
            fontsize=FONT_SIZE,
            ha="center", va="center",
            transform=ax.transData,
            clip_on=True,
            zorder=10,
        )


# ── Country scatter points ────────────────────────────────────────────────────

def _draw_country_points(
    ax: plt.Axes,
    data: dict[str, tuple[float, float, float]],
    colors: dict[str, str],
    label_angle_nudges: dict[str, float] | None = None,
    label_radius_pts: float = 9.0,
) -> None:
    """Scatter plot of country data points with labelled annotations.

    ``label_angle_nudges`` rotates each label around its point in degrees
    (0° = right, 90° = up), while keeping the text itself horizontal.
    """
    _nudges = label_angle_nudges or {}
    for country, (a, b, c) in data.items():
        px, py = barycentric_to_cartesian(a, b, c)
        color = colors.get(country, "#777777")
        ax.scatter(
            [px], [py],
            s=90, c=[color],
            edgecolors="white", linewidths=0.9,
            zorder=6,
        )
        angle = _nudges.get(country, 35.0)
        _cos = math.cos(math.radians(angle))
        _sin = math.sin(math.radians(angle))
        if abs(_cos) >= abs(_sin):          # label predominantly left/right
            _ha = "left" if _cos >= 0 else "right"
            _va = "center"
        else:                               # label predominantly up/down
            _ha = "center"
            _va = "bottom" if _sin >= 0 else "top"
        ann = ax.annotate(
            country,
            (px, py),
            xytext=(
                label_radius_pts * _cos,
                label_radius_pts * _sin,
            ),
            textcoords="offset points",
            fontsize=FONT_SIZE - 1, ha=_ha, va=_va,
            color=color, weight="bold",
            zorder=7,
        )
        ann.set_path_effects([
            pe.withStroke(linewidth=2.0, foreground="white", alpha=0.95),
        ])


# ── Main public function ───────────────────────────────────────────────────────

def ternary_diagram(
    data: dict[str, tuple[float, float, float]],
    colors: dict[str, str],
    vertex_labels: tuple[str, str, str] = ("A", "B", "C"),
    title: str = "",
    bg_alpha: float = 0.20,
    figsize: tuple[float, float] = (6.4, 5.4),
    resolution: int = 500,
    enable_tooltips: bool = True,
    show_corner_labels: bool = False,
    label_angle_nudges: dict[str, float] | None = None,
    label_radius_pts: float = 9.0,
    background_data: dict[str, tuple[float, float, float]] | None = None,
    show_equilibrium_circles: bool = False,
) -> plt.Figure:
    """Build and return a ternary diagram figure.

    Parameters
    ----------
    data:
        Mapping from country/entity code to ``(A%, B%, C%)`` shares.
        Values need not sum to 100; they are normalised internally.
    colors:
        Per-entity hex colour strings.  Missing keys fall back to ``"#777777"``.
    vertex_labels:
        Axis names for vertices A (top), B (bottom-left), C (bottom-right).
        May contain LaTeX markup (e.g. ``r"\\acs{KEY}"``).  Native UTF-8
        characters (e.g. Czech diacritics) are supported with modern pdflatex.
    title:
        Figure title.  May contain LaTeX markup.
    bg_alpha:
        Opacity of the RGB heatmap background (0 = transparent, 1 = opaque).
        The default 0.20 keeps the gradient subtle.
        The heatmap is rasterised once to a companion PNG (~80–150 KB) and
        deduplicated by content hash in the PGF ``_shared/`` directory, so
        the output PDF remains lightweight regardless of resolution.
    figsize:
        Matplotlib figure size in inches.  The default (6.4, 5.4) is sized
        for the typical content extent (≈ 1.52 × 1.29 data units) so that
        ``tight_layout(pad=0.15)`` leaves only minimal whitespace.
        LaTeX's ``\\resizebox{\\linewidth}`` in the figure wrapper will scale
        the result to the exact column width.
    resolution:
        Pixel resolution of the background heatmap (width = height).
        500 is a good default; 700 gives a smoother gradient at +50 % PNG size.
    enable_tooltips:
        Embed invisible ``\\pdftooltip`` anchors (PGF backend only).
    show_corner_labels:
        If True, draw extra corner labels (A/B/C names) positioned outward from
        vertices. Disabled by default to keep margins minimal.
    label_angle_nudges:
        Optional per-country angle (degrees) for point-label placement around
        each marker. Text remains horizontal; only anchor position rotates.
        0° = right, 90° = up, 180° = left, 270° = down.
    label_radius_pts:
        Radius of the point-label offset in points.
    background_data:
        Optional mapping of background entities (e.g. EU27) to ``(A%, B%, C%)``
        shares.  Drawn as grey dots behind the main ``data`` points.
        Pass ``None`` (default) to disable.
    show_equilibrium_circles:
        If True, draw 4 concentric dotted circles around equilibrium
        (A=B=C=1/3), matching minor-grid visual styling.

    Returns
    -------
    plt.Figure
        Call ``savefig_pgf(fig, stem)`` to save for PGF/LaTeX inclusion.
    """
    fig, ax = plt.subplots(figsize=figsize)
    # Tight-layout kwargs are consumed by savefig_pgf's internal call.
    fig._tight_layout_kwargs = {"pad": 0.03}

    # ── RGB heatmap background ────────────────────────────────────────────
    ax.imshow(
        _build_background(resolution=resolution, bg_alpha=bg_alpha),
        origin="lower",
        extent=[0.0, 1.0, 0.0, _H],
        interpolation="bilinear",
        zorder=1,
    )

    # ── Grid + tick marks ─────────────────────────────────────────────────
    _draw_grid_and_ticks(ax)

    if show_equilibrium_circles:
        _draw_equilibrium_distance_circles(ax)

    # ── Triangle boundary ─────────────────────────────────────────────────
    ax.plot([0.0, 1.0, 0.5, 0.0], [0.0, 0.0, _H, 0.0],
            color="black", lw=1.4, zorder=4)

    # ── Background cloud (e.g. EU27) ──────────────────────────────────────
    if background_data:
        _bcoords = [
            barycentric_to_cartesian(a, b, c)
            for a, b, c in background_data.values()
        ]
        _bxs, _bys = zip(*_bcoords)
        ax.scatter(
            _bxs, _bys,
            s=90, c="#a8a8a8", alpha=0.78,
            edgecolors="none", zorder=5,
        )

    # ── Country scatter + annotations ─────────────────────────────────────
    _draw_country_points(
        ax,
        data,
        colors,
        label_angle_nudges=label_angle_nudges,
        label_radius_pts=label_radius_pts,
    )

    # ── PGF hover tooltips ────────────────────────────────────────────────
    if enable_tooltips:
        if background_data:
            _add_ternary_tooltips(ax, background_data, vertex_labels)
        _add_ternary_tooltips(ax, data, vertex_labels)

    # ── Axis arrows + optional corner labels ──────────────────────────────
    _draw_axis_arrows(ax, vertex_labels, show_corner_labels=show_corner_labels)

    # ── Layout ────────────────────────────────────────────────────────────
    if title:
        # Extra title pad for corners-on so title clears the A corner label that overflows above axes.
        ax.set_title(title, fontsize=FONT_SIZE, pad=20 if show_corner_labels else 2)
    # Identical limits for both variants → identical data/inch scale → identical visual appearance.
    # Corner labels that fall outside this range render via clip_on=False / annotation_clip=False.
    ax.set_xlim(-0.15, 1.15)
    ax.set_ylim(-0.120, _H + 0.09)
    ax.set_aspect("equal")
    ax.axis("off")

    return fig
