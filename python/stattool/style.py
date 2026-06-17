"""
Matplotlib style helpers tuned for LaTeX PDF output.

Typical usage
-------------
>>> from stattool.style import apply_style, savefig, cm2in
>>> apply_style()
>>> fig, ax = plt.subplots(figsize=cm2in(14, 9))
>>> # … plot …
>>> savefig(fig, "my_figure")   # writes FIGURES_DIR/my_figure.pdf
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

import matplotlib as mpl

if TYPE_CHECKING:
    import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from config import (
    CMAP_DIVERGING,
    CMAP_SEQUENTIAL,
    FIGURE_DPI,
    FIGURE_FORMAT,
    FIGURE_HEIGHT_CM,
    FIGURE_LABEL_SIZE,
    FIGURE_TEXT_SIZE,
    FIGURE_TITLE_SIZE,
    FIGURE_WIDTH_CM,
    FIGURES_DIR,
    FONT_SIZE,
    PALETTE,
    PGF_DEDUP_COMPANION_IMAGES,
    PGF_OPTIMIZE_ASSETS,
    PGF_RECOMPRESS_COMPANION_IMAGES,
    PGF_SHARED_ASSETS_DIR,
)

# ── Unit conversion ───────────────────────────────────────────────────────────

def cm2in(width_cm: float, height_cm: float) -> tuple[float, float]:
    """Convert centimetres to inches (matplotlib figsize unit)."""
    return width_cm / 2.54, height_cm / 2.54


def default_figsize() -> tuple[float, float]:
    return cm2in(FIGURE_WIDTH_CM, FIGURE_HEIGHT_CM)


# ── Style application ─────────────────────────────────────────────────────────

def apply_style() -> None:
    """Apply global rcParams so all figures look consistent.

    Call once at the top of each script.  The settings are designed to
    produce publication-quality PDF figures that integrate well into a
    LaTeX document (matching font size, thin spines, no chartjunk).
    """
    mpl.rcParams.update(
        {
            # --- Typography ---
            "font.size": FIGURE_TEXT_SIZE,
            "axes.titlesize": FIGURE_TITLE_SIZE,
            "axes.labelsize": FIGURE_LABEL_SIZE,
            "xtick.labelsize": FIGURE_LABEL_SIZE,
            "ytick.labelsize": FIGURE_LABEL_SIZE,
            "legend.fontsize": FIGURE_LABEL_SIZE,
            "figure.titlesize": FIGURE_TITLE_SIZE,
            # Latin Modern Sans matches the CMU sans-serif font used in
            # the CTUthesis LaTeX document. Falls back to DejaVu Sans.
            "font.family": "sans-serif",
            "font.sans-serif": ["Latin Modern Sans", "CMU Sans Serif", "DejaVu Sans"],
            "axes.titlepad": 6,
            # --- Lines & ticks ---
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.minor.width": 0.4,
            "ytick.minor.width": 0.4,
            "lines.linewidth": 1.5,
            "lines.markersize": 4,
            # --- Grid ---
            "axes.grid": True,
            "axes.grid.which": "major",
            "grid.linewidth": 0.5,
            "grid.alpha": 0.45,
            "grid.color": "#CCCCCC",
            "xtick.minor.visible": True,
            "ytick.minor.visible": True,
            # --- Spines ---
            "axes.spines.top": False,
            "axes.spines.right": False,
            # --- colours ---
            "axes.prop_cycle": mpl.cycler("color", PALETTE),
            "image.cmap": CMAP_SEQUENTIAL,
            # --- Figure ---
            "figure.dpi": 150,           # screen preview (not saved DPI)
            "savefig.dpi": FIGURE_DPI,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            # --- PDF / vector ---
            "pdf.fonttype": 42,          # embed TrueType fonts → editable in Illustrator
            "ps.fonttype": 42,
            "svg.fonttype": "none",      # keep text as text in SVG
        }
    )
    # Register the discrete colour cycle as a named cyclic colourmap helper
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler("color", PALETTE)


# ── PGF backend support ──────────────────────────────────────────────────────

# Minimal preamble for the PGF backend.  When the .pgf file is \input{} into
# main.tex the *document's* preamble supplies all packages (acro, hyperref,
# siunitx with custom units, …).  This preamble is only used when matplotlib
# itself invokes pdflatex for font metrics / text sizing.
PGF_PREAMBLE = r"""
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{siunitx}
\DeclareSIUnit\pps{PPS}
\DeclareSIUnit\eur{€}
\DeclareSIUnit\czk{Kč}
\DeclareSIUnit\rok{rok}
\DeclareSIUnit\person{os.}
\DeclareSIUnit\pp{p.\,b.}
\DeclareSIUnit\week{týd.}
\DeclareSIUnit\month{měs.}
\sisetup{output-decimal-marker={,}, per-mode=symbol}
\usepackage[pdftex]{contour}
\contourlength{0.6pt}
% Stub \contour for the metrics pass (real one comes from CTUthesis.cls).
\providecommand{\contour}[2]{#2}
\usepackage{pdfcomment}
% Stub \pdftooltip for the PGF metrics pass (real one from CTUthesis.cls).
% Falls back to showing the displayed text only, so figures degrade gracefully.
\providecommand{\pdftooltip}[2]{#1}
% Stub \CTUtooltiplink for the PGF metrics pass.
% CTUthesis.cls defines \CTUtooltiplink as the public alias for \CTU@tooltiplink.
% Using the public (no-@) name avoids catcode issues when the text is typeset
% after the preamble (where @  has catcode 12, not 11).
\providecommand{\CTUtooltiplink}[3]{#2}
% Stub acro commands so PGF text-metric pass can measure them.
% The real acro package resolves them when \input{} into main.tex.
\providecommand{\ac}[1]{#1}
\providecommand{\acs}[1]{#1}
\providecommand{\acp}[1]{#1}
\providecommand{\acl}[1]{#1}
\providecommand{\acgen}[1]{#1}
\providecommand{\acdat}[1]{#1}
\providecommand{\acacc}[1]{#1}
\providecommand{\acloc}[1]{#1}
\providecommand{\acins}[1]{#1}
"""

# ── Geo-label helpers ─────────────────────────────────────────────────────────

# Czech long-form names matching the `long=` property of each \DeclareAcronym{geo-XX}
# entry in latex/texparts/references/acro.tex.  Used in PDF hover tooltips so
# Acrobat displays "Česko: 1.36" instead of "CZ: 1.36".
GEO_LONG_NAMES: dict[str, str] = {
    "AT": "Rakousko",
    "BE": "Belgie",
    "BG": "Bulharsko",
    "CH": "Švýcarsko",
    "CY": "Kypr",
    "CZ": "Česko",
    "DE": "Německo",
    "DK": "Dánsko",
    "EE": "Estonsko",
    "EL": "Řecko",
    "ES": "Španělsko",
    "FI": "Finsko",
    "FR": "Francie",
    "GR": "Řecko",
    "HR": "Chorvatsko",
    "HU": "Maďarsko",
    "IE": "Irsko",
    "IS": "Island",
    "IT": "Itálie",
    "LT": "Litva",
    "LU": "Lucembursko",
    "LV": "Lotyšsko",
    "MT": "Malta",
    "NL": "Nizozemsko",
    "NO": "Norsko",
    "PL": "Polsko",
    "PT": "Portugalsko",
    "RO": "Rumunsko",
    "SE": "Švédsko",
    "SI": "Slovinsko",
    "SK": "Slovensko",
    "UK": "Spojené království",
    "GB": "Velká Británie",
    "UA": "Ukrajina",
    "RS": "Srbsko",
    "TR": "Turecko",
    "GE": "Gruzie",
    "AM": "Arménie",
    "AL": "Albánie",
    "MD": "Moldavsko"
}

# All ISO 3166-1 alpha-2 codes with a \DeclareAcronym{geo-XX} entry in acro.tex.
# EU-27 + GR alias + EEA/non-EU countries that appear in Eurostat data.
GEO_ACRO: frozenset[str] = frozenset({
    # EU-27
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES",
    "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV",
    "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
    # Non-EU European countries declared in acro.tex
    "IS", "NO", "CH", "UK",
})


def apply_geo_labels_pgf(
    ax: "plt.Axes",
    *,
    halo: bool = True,
    geo_set: "frozenset[str] | None" = None,
    values: "dict[str, float] | None" = None,
    tooltip_fmt: str = "{:.1f}",
) -> None:
    r"""Replace bare ISO-2 country codes on a PGF axes with ``\acs{geo-XX}``.

    For codes in *geo_set* (default: :data:`GEO_ACRO`):

    * Replaces the text with ``\acs{geo-XX}`` so acro resolves it in LaTeX.
    * Clears matplotlib ``path_effects`` (mandatory: PGF renders stroked text
      as outlines, which strips embedded LaTeX commands).
    * If *halo* is ``True`` (default), wraps in ``\contour{white}{...}`` for
      readability on coloured map backgrounds.  Requires the ``contour``
      package in ``CTUthesis.cls``.
    * If *values* is given (``{"CZ": 38.2, "DE": 52.1, …}``), each label is
      wrapped with ``\pdftooltip{label}{XX: N.N}`` so hover-capable PDF
      viewers (Adobe Acrobat, Foxit) display the value on mouse-over.
      Formatted using *tooltip_fmt*.

    Call this function *after* all plotting is done, *before* ``savefig_pgf()``.
    """
    if geo_set is not None:
        codes = geo_set
    elif values is not None:
        codes = frozenset(values.keys())
    else:
        codes = GEO_ACRO
    for child in ax.get_children():
        if not hasattr(child, "get_text"):
            continue
        txt = child.get_text().strip()
        if txt not in codes:
            continue
        if values is not None and txt in values:
            # Keep map labels as pure tooltips (no GoTo destination links).
            # This avoids unresolved name{geo-XX} warnings when geo acronyms
            # are configured with hyper=false.
            display = rf"\contour{{white}}{{{txt}}}" if halo else txt
            val_str = tooltip_fmt.format(values[txt])
            long = GEO_LONG_NAMES.get(txt, txt)
            label = rf"\pdftooltip{{{display}}}{{{long}: {val_str}}}"
        else:
            label = rf"\acs{{geo-{txt}}}"
            if halo:
                label = rf"\contour{{white}}{{{label}}}"
        child.set_text(label)
        child.set_path_effects([])


def add_pgf_tooltips(
    ax: "plt.Axes",
    pivot: "pd.DataFrame",
    *,
    fmt: str = "{:.1f}",
) -> None:
    r"""Overlay invisible ``\pdftooltip`` annotations at every data point.

    Each annotation is a zero-width phantom node that hover-capable PDF
    viewers (Adobe Acrobat, Foxit) render as a tooltip showing the country
    code, year, and numeric value.  In other viewers the annotation is
    completely invisible.

    This function is a **no-op** when the active matplotlib backend is not
    ``pgf``; it can therefore be called unconditionally in scripts that
    support both PGF and raster output.

    Parameters
    ----------
    ax:
        Axes containing the plotted data.
    pivot:
        DataFrame with time/year values as the index and ISO-2 country codes
        as columns, matching the internal pivot used by :func:`timeline`.
    fmt:
        Python format string for the numeric value (e.g. ``"{:.1f}"`` or
        ``"{:.2f}"``).  Default ``"{:.1f}"``.
    """
    import pandas as pd  # noqa: F401 --- guard if not yet imported at module top
    if mpl.get_backend() != "pgf":
        return
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    for geo in pivot.columns:
        series = pivot[geo].dropna()
        for year, val in series.items():
            if not (x_min <= float(year) <= x_max):
                continue
            if not (y_min <= float(val) <= y_max):
                continue
            long = GEO_LONG_NAMES.get(str(geo), str(geo))
            tooltip_text = f"{long} {int(year)}: {fmt.format(val)}"
            ax.text(
                float(year),
                float(val),
                # \phantom{\rule{3pt}{3pt}} gives a 3×3pt invisible hit area
                # matching the data-point marker size (markersize=3).
                # \phantom{0.00} was too large and visually offset the line.
                r"\pdftooltip{\phantom{\rule{3pt}{3pt}}}{" + tooltip_text + r"}",
                fontsize=FONT_SIZE,
                ha="center",
                va="center",
                transform=ax.transData,
                clip_on=True,
                zorder=10,
            )


def add_pgf_tooltips_scatter(
    ax: "plt.Axes",
    merged: "pd.DataFrame",
    *,
    fmt_x: str = "{:.1f}",
    fmt_y: str = "{:.1f}",
    label_x: str = "x",
    label_y: str = "y",
) -> None:
    r"""Overlay invisible ``\pdftooltip`` annotations at every scatter point.

    Each annotation is a zero-width phantom node that hover-capable PDF
    viewers (Adobe Acrobat, Foxit) render as a tooltip showing the country
    name and the x/y values.  In other viewers the annotation is completely
    invisible.

    This function is a **no-op** when the active matplotlib backend is not
    ``pgf``; it can therefore be called unconditionally in scripts that
    support both PGF and raster output.

    Parameters
    ----------
    ax:
        Axes containing the plotted scatter data.
    merged:
        DataFrame with at minimum columns ``geo``, ``x``, ``y`` as produced
        by :func:`statout.scatter.scatter_xy` and stored on
        ``fig._scatter_merged``.
    fmt_x:
        Python format string for the x value (default ``"{:.1f}"``).
    fmt_y:
        Python format string for the y value (default ``"{:.1f}"``).
    label_x:
        Short label for the x axis used in the tooltip text.
    label_y:
        Short label for the y axis used in the tooltip text.
    """
    if mpl.get_backend() != "pgf":
        return
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    for _, row in merged.iterrows():
        if not (x_min <= float(row["x"]) <= x_max):
            continue
        if not (y_min <= float(row["y"]) <= y_max):
            continue
        geo = str(row["geo"])
        long = GEO_LONG_NAMES.get(geo, geo)
        # Keep tooltip short to prevent matplotlib PGF backend from splitting
        # the text across multiple pgftext nodes (which breaks brace matching).
        # Format: "Country: xval / yval"
        tooltip_text = (
            f"{long}: {fmt_x.format(row['x'])} / {fmt_y.format(row['y'])}"
        )
        ax.text(
            float(row["x"]),
            float(row["y"]),
            r"\pdftooltip{\phantom{\rule{3pt}{3pt}}}{" + tooltip_text + r"}",
            fontsize=FONT_SIZE,
            ha="center",
            va="center",
            transform=ax.transData,
            clip_on=True,
            zorder=10,
        )


def apply_style_pgf() -> None:
    """Switch to the PGF backend and apply consistent style.

    Must be called **before** any ``plt.subplots()`` call.  Produces ``.pgf``
    files that are compiled inside the host LaTeX document, so all document
    macros (``\\ac{}``, ``\\SI{}{}``, ``\\cite{}``) are available in axis
    labels, titles, and annotations.
    """
    mpl.use("pgf")

    mpl.rcParams.update(
        {
            # --- PGF-specific ---
            "pgf.rcfonts": False,           # don't override document fonts
            "pgf.preamble": PGF_PREAMBLE,
            # --- Typography (must match document) ---
            "font.family": "sans-serif",
            "font.sans-serif": ["Latin Modern Sans", "CMU Sans Serif", "DejaVu Sans"],
            "font.size": FIGURE_TEXT_SIZE,
            "axes.titlesize": FIGURE_TITLE_SIZE,
            "axes.labelsize": FIGURE_LABEL_SIZE,
            "xtick.labelsize": FIGURE_LABEL_SIZE,
            "ytick.labelsize": FIGURE_LABEL_SIZE,
            "legend.fontsize": FIGURE_LABEL_SIZE,
            "figure.titlesize": FIGURE_TITLE_SIZE,
            "axes.titlepad": 6,
            # --- Lines & ticks ---
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.minor.width": 0.4,
            "ytick.minor.width": 0.4,
            "lines.linewidth": 1.5,
            "lines.markersize": 4,
            # --- Grid ---
            "axes.grid": True,
            "axes.grid.which": "major",
            "grid.linewidth": 0.5,
            "grid.alpha": 0.45,
            "grid.color": "#CCCCCC",
            "xtick.minor.visible": True,
            "ytick.minor.visible": True,
            # --- Spines ---
            "axes.spines.top": False,
            "axes.spines.right": False,
            # --- Colours ---
            "axes.prop_cycle": mpl.cycler("color", PALETTE),
            "image.cmap": CMAP_SEQUENTIAL,
            # --- Figure ---
            "figure.dpi": 150,
            "savefig.dpi": FIGURE_DPI,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
        }
    )


# ── Centering helper ──────────────────────────────────────────────────────────

def _recenter_on_visual(fig: plt.Figure) -> None:
    """Shift suptitle & figure legends so they appear centred after tight crop.

    ``bbox_inches='tight'`` crops the figure canvas asymmetrically when the
    axes have unequal left/right margins (e.g. ylabel on the left and inline
    labels on the right).  This function computes the visual centre of the
    tight bounding box and repositions the suptitle and any figure-level
    legends to that centre so they look centred in the saved image.

    It also snugs the suptitle down so it sits just above the topmost
    axes content (vline annotations, etc.) instead of leaving a large gap.
    """
    has_suptitle = getattr(fig, '_suptitle', None) is not None
    has_legends = bool(fig.legends)
    if not has_suptitle and not has_legends:
        return

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    # ── snug suptitle down to just above axes content ──────────────────────
    if has_suptitle:
        st = fig._suptitle
        was_visible = st.get_visible()
        # Temporarily hide suptitle so it doesn't inflate the bbox
        st.set_visible(False)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        # Get top of all remaining content (axes, annotations, legends…)
        bb_content = fig.get_tightbbox(renderer)
        st.set_visible(was_visible)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        if bb_content is not None:
            fig_h = fig.get_figheight()
            gap_pt = getattr(fig, '_suptitle_gap_pt', 6)
            content_top_frac = bb_content.y1 / fig_h
            st_bb = st.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())
            anchor_offset = st.get_position()[1] - st_bb.y0
            new_y = content_top_frac + gap_pt / 72 / fig_h + anchor_offset
            st.set_position((st.get_position()[0], new_y))

    # ── horizontal centring on the visual crop ─────────────────────────────
    bb = fig.get_tightbbox(renderer)
    if bb is None:
        return

    # x_center in figure-fraction coordinates
    # get_tightbbox returns inches, so divide by figure width in inches
    fig_w = fig.get_figwidth()
    x_c = (bb.x0 + bb.x1) / 2 / fig_w

    if has_suptitle:
        st = fig._suptitle
        _, y = st.get_position()
        st.set_position((x_c, y))

    for leg in fig.legends:
        ba = leg.get_bbox_to_anchor()
        inv_tf = fig.transFigure.inverted()
        ba_fig = inv_tf.transform_bbox(ba)
        y_val = (ba_fig.y0 + ba_fig.y1) / 2
        leg.set_bbox_to_anchor((x_c, y_val), fig.transFigure)


# ── Save helper ───────────────────────────────────────────────────────────────

def _safe_tight_layout(fig: plt.Figure, kwargs: dict) -> None:
    """Apply tight_layout while ignoring the known incompatible-axes warning."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "error",
            message=(
                r"This figure includes Axes that are not compatible with "
                r"tight_layout.*"
            ),
            category=UserWarning,
        )
        try:
            fig.tight_layout(**kwargs)
        except UserWarning:
            # Some artists (e.g. colorbar/axes-grid constructs) are not
            # tight_layout-compatible; keep export flow stable.
            return

def savefig(
    fig: plt.Figure,
    name: str,
    *,
    fmt: Optional[str] = None,
    out_dir: Optional[Union[str, Path]] = None,
    tight: bool = True,
) -> Path:
    """Save *fig* to *FIGURES_DIR/<name>.<fmt>* and close it.

    Parameters
    ----------
    fig:
        The matplotlib Figure to save.
    name:
        Output filename *without* extension.
    fmt:
        Override ``FIGURE_FORMAT`` just for this call (e.g. ``"png"``).
    out_dir:
        Override the output directory (defaults to ``FIGURES_DIR``).
    tight:
        If True, call ``fig.tight_layout()`` before saving.
    """
    if tight:
        _tl_kwargs = getattr(fig, '_tight_layout_kwargs', {})
        _safe_tight_layout(fig, _tl_kwargs)
        # Re-apply any subplots_adjust overrides (tight_layout may clobber hspace etc.)
        _spa = getattr(fig, '_subplots_adjust_kwargs', None)
        if _spa:
            fig.subplots_adjust(**_spa)
        _recenter_on_visual(fig)

    fmt = fmt or FIGURE_FORMAT
    directory = Path(out_dir) if out_dir else FIGURES_DIR
    directory.mkdir(parents=True, exist_ok=True)
    out = directory / f"{name}.{fmt}"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved: {out}")
    return out


def _macro_prefix(name: str) -> str:
    r"""Convert ``'vyhled_porodnost_vyvoj'`` → ``'VyhledPorodnostVyvoj'``.

    Digits are mapped to letters (``0→O``, ``1→I``, ``2→Z``, ``3→T``, ``4→F``,
    ``5→V``, ``6→S``, ``7→N``, ``8→E``, ``9→X``) so the result is a valid
    TeX control-sequence body (letters only).  Without this, a stem like
    ``eu_apz_vydaje_2004`` would produce ``\NudgeEuApzVydaje2004Cz`` which
    TeX parses as ``\NudgeEuApzVydaje`` followed by stray ``2004Cz`` tokens.
    """
    camel = "".join(part.capitalize() for part in name.split("_"))
    return camel.translate(_DIGIT_TO_LETTER)


_DIGIT_TO_LETTER = str.maketrans("0123456789", "OIZTFVSNEX")


def _macro_name(prefix: str, key: str) -> str:
    r"""Build a LaTeX macro name like ``\strVyhledPorodnostVyvojTitle``."""
    suffix = "".join(part.capitalize() for part in key.split("_"))
    return rf"\str{prefix}{suffix}"


def _replace_pgf_strings(
    pgf_path: Path,
    name: str,
    strings: dict[str, str],
) -> int:
    r"""Replace literal string values in a ``.pgf`` file with ``\strXxx`` macros.

    Replacements are constrained to occurrences inside text payloads of
    ``\pgftext[...]{...PAYLOAD...}`` to avoid corrupting PGF drawing
    primitives (e.g. ``"rok"`` matching inside ``stroke``).

    Returns the total number of replacements made.
    """
    import re as _re
    prefix = _macro_prefix(name)
    content = pgf_path.read_text(encoding="utf-8")
    total = 0

    # Match the body of every \pgftext[...]{BODY} (non-greedy, balanced one level).
    # The actual visible payload is the innermost {...} that follows the inner
    # \selectfont and catcode resets — just operate on the line as a whole and
    # only replace values that appear inside lines containing \pgftext.
    new_lines: list[str] = []
    repl_items = sorted(strings.items(), key=lambda kv: -len(kv[1]))
    for line in content.splitlines(keepends=True):
        if "\\pgftext" in line:
            for key, value in repl_items:
                if not value:
                    continue
                if value in line:
                    macro = _macro_name(prefix, key)
                    n = line.count(value)
                    line = line.replace(value, macro)
                    total += n
        new_lines.append(line)

    if total:
        pgf_path.write_text("".join(new_lines), encoding="utf-8")
    return total


# ── Per-label y-nudge interface ──────────────────────────────────────────────

def _nudge_macro_name(prefix: str, label_id: str) -> str:
    r"""Build a LaTeX macro name like ``\NudgeStavHdpVyvojCZ``.

    *label_id* is sanitised: non-letter chars dropped, ``_`` → CamelCase.
    """
    parts = [p for p in label_id.replace("-", "_").split("_") if p]
    suffix = "".join(p.capitalize() for p in parts)
    # Strip remaining non-letter chars (e.g. digits, '=') --- LaTeX macros
    # may only contain letters when defined via \providecommand without \csname.
    suffix = "".join(c for c in suffix if c.isalpha())
    macro = rf"\Nudge{prefix}{suffix}"
    import re as _re
    assert _re.fullmatch(r"\\[A-Za-z]+", macro), (
        f"Invalid TeX cs name: {macro!r} (prefix={prefix!r}, label_id={label_id!r})"
    )
    return macro


def _extract_figure_tex_macro_value(content: str, macro: str) -> str | None:
    r"""Return the value of a ``\def\str...{...}%`` macro from a figure wrapper."""
    import re as _re

    macro_name = macro[1:] if macro.startswith("\\") else macro
    pattern = _re.compile(rf"^\\def{_re.escape(macro_name)}\{{(.*)\}}%?\s*$", _re.MULTILINE)
    match = pattern.search(content)
    return match.group(1) if match else None


def _apply_label_nudges_pgf(
    pgf_path: Path,
    name: str,
    nudge_labels: list,
) -> dict[str, str]:
    r"""Rewrite y-coords of matching ``\pgftext`` lines with nudge macros.

    *nudge_labels* is a list of items, each one of:

    * ``"\\acs{geo-CZ}"`` --- bare match string; macro name auto-derived as
      ``\NudgeStavHdpVyvojGeoCZ``.
    * ``("CZ", "\\acs{geo-CZ}")`` --- explicit (label_id, match_string) pair;
      macro becomes ``\NudgeStavHdpVyvojCZ``.

    For every ``\pgftext[x=…,y=Yin,…]{…match_string…}`` line found, the
    ``y=Yin`` portion is rewritten as
    ``y={\dimexpr Yin+\Nudge…\relax}``.  All other content of the line
    (including hyperlinks, tooltips, contour/halo wrappers) is preserved.

    Returns ``{macro_name: match_string}`` mapping for use by
    :func:`save_figure_tex_pgf` to emit ``\providecommand{\Nudge…}{0pt}``.
    """
    import re

    prefix = _macro_prefix(name)
    items: list[tuple[str, str]] = []
    for entry in nudge_labels:
        if isinstance(entry, str):
            # Auto-derive ID by stripping LaTeX/punctuation
            label_id = re.sub(r"[\\{}]", "", entry)
            label_id = re.sub(r"[^A-Za-z0-9]+", "_", label_id).strip("_")
        else:
            label_id, entry = entry
        macro = _nudge_macro_name(prefix, label_id)
        items.append((macro, entry))

    content = pgf_path.read_text(encoding="utf-8")
    macros_used: dict[str, str] = {}

    # Match only the y= coordinate inside a \pgftext[...] bracket.
    # The text body is searched separately on the whole line because
    # it can contain arbitrarily nested braces (\acs{geo-CZ}, \color{...} ...).
    y_re = re.compile(r"(\\pgftext\[x=[^,\]]+,y=)([^,\]]+)")

    new_lines: list[str] = []
    for line in content.splitlines(keepends=True):
        if "\\pgftext" not in line:
            new_lines.append(line)
            continue
        # Needle must be the actual text payload of the \pgftext, i.e.
        # immediately followed by "}}" (closing \selectfont and \color groups).
        # This avoids false positives where the needle appears inside another
        # element (e.g. y-axis title containing "EU27 = 100").
        chosen: tuple[str, str] | None = None
        for macro, needle in sorted(items, key=lambda kv: -len(kv[1])):
            if needle + "}}" in line:
                chosen = (macro, needle)
                break
        if chosen is None:
            new_lines.append(line)
            continue
        m = y_re.search(line)
        if not m:
            new_lines.append(line)
            continue
        macro, needle = chosen
        y_val = m.group(2)
        new_y = f"{{\\dimexpr {y_val}+{macro}\\relax}}"
        new_line = line[: m.start(2)] + new_y + line[m.end(2) :]
        new_lines.append(new_line)
        macros_used[macro] = needle

    if macros_used:
        pgf_path.write_text("".join(new_lines), encoding="utf-8")
    return macros_used


def _sha256_file(path: Path) -> str:
    """Return sha256 hex digest for *path* (streaming, memory-safe)."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _dedup_pgf_companion_images(
    pgf_path: Path,
    *,
    shared_dir: Path,
) -> int:
    r"""Deduplicate PGF companion rasters to ``shared_dir`` and rewrite references.

    Matplotlib PGF export can produce files like ``<name>-img0.png``
    (typically colourbar/image tiles).  This helper:

    1. Finds references to local ``.png`` companions in *pgf_path*.
    2. Moves image payloads into ``shared_dir`` under content-hash names.
    3. Rewrites PGF references to ``_shared/<hash>.png``.
    4. Removes redundant local companion files.

    Returns number of PGF reference rewrites performed.
    """
    content = pgf_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    rewritten = 0

    # Match arguments of \pgfimage[...]...{...png} including nested dirs.
    import re
    png_re = re.compile(r"\{([^{}]+\.png)\}")

    companion_map: dict[str, str] = {}
    for line in lines:
        for m in png_re.finditer(line):
            ref = m.group(1)
            # Absolute paths are left untouched; we only manage local companions.
            if ref.startswith("/") or ref.startswith("../") or ref.startswith("./"):
                continue
            companion_map[ref] = ref

    if not companion_map:
        return 0

    shared_dir.mkdir(parents=True, exist_ok=True)
    base_dir = pgf_path.parent

    replace_map: dict[str, str] = {}
    for ref in companion_map:
        src = base_dir / ref
        if not src.exists() or not src.is_file():
            continue
        digest = _sha256_file(src)
        target_name = f"img-{digest[:20]}.png"
        target = shared_dir / target_name
        if not target.exists():
            src.replace(target)
        else:
            # Duplicate payload already stored.
            src.unlink(missing_ok=True)
        replace_map[ref] = f"_shared/{target_name}"

    if not replace_map:
        return 0

    # Replace longer keys first to avoid accidental partial substitutions.
    for old, new in sorted(replace_map.items(), key=lambda kv: -len(kv[0])):
        count = content.count("{" + old + "}")
        if count:
            content = content.replace("{" + old + "}", "{" + new + "}")
            rewritten += count

    if rewritten:
        pgf_path.write_text(content, encoding="utf-8")
    return rewritten


def _suppress_hyperref_in_rotated_pgftext(pgf_path: Path) -> int:
    r"""Wrap rotated ``\pgftext`` payloads with ``\NoHyper ... \endNoHyper``.

    hyperref produces axis-aligned PDF link annotations; when the surrounding
    text is rotated (e.g. y-axis labels at 90°, vertical colorbar labels),
    the link box stays horizontal and floats away from the visible text.
    Suppressing hyperref inside rotated labels removes the stray boxes.

    Operates line by line on ``\pgftext[...rotate=...]{...}`` lines.  The
    visible payload sits between ``\def%{\%}`` and the closing ``}}`` at the
    end of the line — wrap it.

    Returns the number of payloads modified.
    """
    import re as _re
    lines = pgf_path.read_text(encoding="utf-8").splitlines(keepends=True)
    marker = r"\def%{\%}"
    pgftext_rot = _re.compile(r"\\pgftext\[[^\]]*rotate=")
    n = 0
    for i, line in enumerate(lines):
        if not pgftext_rot.search(line):
            continue
        if r"\NoHyper\sffamily" in line:
            continue
        # Upgrade older wraps that lack the explicit \sffamily re-assertion.
        if r"\NoHyper " in line and r"\endNoHyper" in line:
            lines[i] = line.replace(r"\NoHyper ", r"\NoHyper\sffamily ", 1)
            n += 1
            continue
        idx = line.find(marker)
        if idx < 0:
            continue
        payload_start = idx + len(marker)
        # Find the closing "}}" that terminates \color{textcolor}{...}.
        # The line typically ends with "}}%\n" or "}}\n".
        stripped = line.rstrip("\n")
        if stripped.endswith("}}%"):
            payload_end = len(stripped) - 3
            tail = "}}%\n" if line.endswith("\n") else "}}%"
        elif stripped.endswith("}}"):
            payload_end = len(stripped) - 2
            tail = "}}\n" if line.endswith("\n") else "}}"
        else:
            continue
        payload = line[payload_start:payload_end]
        new_line = (
            line[:payload_start]
            + r"\NoHyper\sffamily " + payload + r" \endNoHyper"
            + tail
        )
        lines[i] = new_line
        n += 1
    if n:
        pgf_path.write_text("".join(lines), encoding="utf-8")
    return n


def _optimize_pgf_assets(pgf_path: Path) -> list[str]:
    """Run enabled PGF post-export optimizations and return status messages."""
    notes: list[str] = []
    if not PGF_OPTIMIZE_ASSETS:
        return notes

    if PGF_DEDUP_COMPANION_IMAGES:
        n = _dedup_pgf_companion_images(pgf_path, shared_dir=PGF_SHARED_ASSETS_DIR)
        if n:
            notes.append(f"{n} companion image reference(s) deduplicated to _shared/")

    if PGF_RECOMPRESS_COMPANION_IMAGES:
        # Placeholder switch: kept for future pngquant/zopfli pipeline.
        notes.append("recompression switch enabled (no-op placeholder)")

    n = _suppress_hyperref_in_rotated_pgftext(pgf_path)
    if n:
        notes.append(f"{n} rotated label(s) wrapped with \\NoHyper")

    return notes


def savefig_pgf(
    fig: plt.Figure,
    name: str,
    *,
    out_dir: Optional[Union[str, Path]] = None,
    tight: bool = True,
    strings: Optional[dict[str, str]] = None,
    nudge_labels: Optional[list] = None,
) -> Path:
    r"""Save *fig* as a ``.pgf`` file for inclusion via ``\input{}`` in LaTeX.

    The PGF backend must be active (call ``apply_style_pgf()`` first).
    Unlike ``savefig()``, this does **not** produce a standalone PDF ---
    the ``.pgf`` file is compiled inside the host document.

    If *strings* is given (``{key: literal_value}``), the saved ``.pgf`` is
    post-processed: every *literal_value* is replaced with a ``\strXxx``
    macro reference.  The matching ``\def`` lines are emitted by
    ``save_figure_tex_pgf(strings=...)``.
    """
    if tight:
        _tl_kwargs = getattr(fig, '_tight_layout_kwargs', {})
        _safe_tight_layout(fig, _tl_kwargs)
        _spa = getattr(fig, '_subplots_adjust_kwargs', None)
        if _spa:
            fig.subplots_adjust(**_spa)
        _recenter_on_visual(fig)

    directory = Path(out_dir) if out_dir else FIGURES_DIR
    directory.mkdir(parents=True, exist_ok=True)
    out = directory / f"{name}.pgf"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved PGF: {out}")

    for note in _optimize_pgf_assets(out):
        print(f"  ↳ {note}")

    if strings:
        n = _replace_pgf_strings(out, name, strings)
        print(f"  ↳ {n} string→macro replacement(s) in PGF")

    if nudge_labels:
        used = _apply_label_nudges_pgf(out, name, nudge_labels)
        print(f"  ↳ {len(used)} label nudge macro(s) wired in PGF")

    return out


# ── Citation helpers for save_figure_tex ─────────────────────────────────────

_CITE_PROVIDERS: list[tuple[str, str]] = [
    ("oecd_aias_ictwss", "\\acs{OECD}~\\acs{ICTWSS}"),
    ("oecd_hfcs",        "\\acs{OECD}~\\acs{HFCS}"),
    ("oecd_lmp",         "\\acs{OECD}~\\acs{LMP}"),
    ("eurostat_ses",     "Eurostat~\\acs{SES}"),
    ("eurostat",         "Eurostat"),
    ("oecd",             "\\acs{OECD}"),
    ("mpsv_ipp",         "\\acs{MPSV}~\\acs{IPP}"),
    ("mpsv_ispv",        "\\acs{MPSV}~\\acs{ISPV}"),
    ("cssz",             "\\acs{ČSSZ}"),
    ("zakon_",           "Model podle legislativy \\aca{geo-CZ}"),
    ("nv_",              "Model podle legislativy \\aca{geo-CZ}"),
    ("sdeleni_",         "Model podle legislativy \\aca{geo-CZ}"),
]


def _cite_provider(key: str) -> str:
    """Return human-readable provider label for a biblatex cite key."""
    for prefix, label in _CITE_PROVIDERS:
        if key.startswith(prefix):
            return label
    return ""


def _build_cite_source(keys: list) -> str:
    """Return grouped 'Provider~\\cite{k1}~\\cite{k2}, …' string."""
    from collections import OrderedDict
    groups: "OrderedDict[str, list]" = OrderedDict()
    for k in keys:
        lbl = _cite_provider(k)
        if lbl not in groups:
            groups[lbl] = []
        groups[lbl].append(k)
    parts = []
    for lbl, ks in groups.items():
        cites = "~".join(f"\\cite{{{k}}}" for k in ks)
        parts.append(f"{lbl}.~{cites}" if lbl else cites)
    return ", ".join(parts)


def save_figure_tex(
    name: str,
    caption: str,
    label: str,
    *,
    out_dir: Optional[Union[str, Path]] = None,
    include_path: Optional[str] = None,
    width: str = r"\columnwidth",
    cite_keys: Optional[Union[str, list]] = None,
    cite_key: Optional[str] = None,
    footnote: Optional[str] = None,
) -> Path:
    r"""Write a LaTeX ``\begin{figure}`` environment that includes *name*.pdf.

    Parameters
    ----------
    name:
        Figure filename *without* extension.
    caption:
        Short title (≤10 words, Czech OK).  A ``Zdroj dat:`` sentence is
        appended automatically when *cite_keys* are provided.
    label:
        ``\label{}`` key, e.g. ``"fig:gdp_timeline"``.
    out_dir:
        Directory for the .tex file.  Defaults to ``LATEX_TEXPARTS_DIR``.
    include_path:
        Path for ``\includegraphics``.  Defaults to ``"../pics/<name>"``.
    width:
        LaTeX width expression (default ``\columnwidth``).
    cite_keys:
        List of biblatex cite keys, or a comma-separated string.
        Provider labels (Eurostat, OECD, MPSV/IPP, MPSV/ISPV) are inferred
        from key prefixes and prepended before the ``\cite{}`` commands.
    cite_key:
        Deprecated alias for *cite_keys* (kept for backward compatibility).
    """
    import re
    from config import LATEX_TEXPARTS_DIR

    directory = Path(out_dir) if out_dir else LATEX_TEXPARTS_DIR
    include_path = include_path or f"../python/figures/{name}"

    # Resolve cite keys --- cite_keys takes priority over deprecated cite_key
    raw = cite_keys if cite_keys is not None else cite_key
    keys: list = []
    if raw is not None:
        if isinstance(raw, str):
            keys = [k.strip() for k in raw.split(",") if k.strip()]
        else:
            keys = [k.strip() for k in raw if k.strip()]

    # Escape special LaTeX characters in caption (but not already-escaped ones)
    title = caption.rstrip(". \t\n")
    # Escape % that are not already escaped
    title = re.sub(r"(?<!\\)%", r"\%", title)
    if keys:
        source = _build_cite_source(keys)
        caption_full = f"{title}. Zdroj dat: {source}"
    else:
        caption_full = title

    if footnote:
        caption_str = f"{caption_full}\\protect\\footnotemark"
        footnote_line = f"\\footnotetext{{{footnote}}}\n"
    else:
        caption_str = caption_full
        footnote_line = ""

    tex = (
        f"\\begin{{figure}}[htbp]\n"
        f"  \\centering\n"
        f"  \\includegraphics[width={width}]{{{include_path}}}\n"
        f"  \\caption{{{caption_str}}}\n"
        f"  \\label{{{label}}}\n"
        f"\\end{{figure}}\n"
        f"{footnote_line}"
    )
    out = directory / f"{name}.tex"
    out.write_text(tex, encoding="utf-8")
    print(f"Saved TeX: {out}")
    return out


def save_figure_tex_pgf(
    name: str,
    caption: str,
    label: str,
    *,
    out_dir: Optional[Union[str, Path]] = None,
    include_path: Optional[str] = None,
    cite_keys: Optional[Union[str, list]] = None,
    cite_key: Optional[str] = None,
    footnote: Optional[str] = None,
    resizebox_width: str = r"\linewidth",
    strings: Optional[dict[str, str]] = None,
    nudge_labels: Optional[list] = None,
) -> Path:
    r"""Write a LaTeX ``figure`` environment that ``\input``s a PGF file.

    Unlike ``save_figure_tex()`` which uses ``\includegraphics``, this uses::

        \resizebox{<width>}{!}{\input{<path>.pgf}}

    The PGF file is compiled *inside* the host document, so all document
    macros (\ac{}, \SI{}{}, \cite{}, hyperref links) are available.
    """
    import re
    from config import LATEX_TEXPARTS_DIR

    directory = Path(out_dir) if out_dir else LATEX_TEXPARTS_DIR
    include_path = include_path or f"../python/figures/{name}.pgf"

    raw = cite_keys if cite_keys is not None else cite_key
    keys: list = []
    if raw is not None:
        if isinstance(raw, str):
            keys = [k.strip() for k in raw.split(",") if k.strip()]
        else:
            keys = [k.strip() for k in raw if k.strip()]

    title = caption.rstrip(". \t\n")
    title = re.sub(r"(?<!\\)%", r"\%", title)
    if keys:
        source = _build_cite_source(keys)
        caption_full = f"{title}. Zdroj dat: {source}"
    else:
        caption_full = title

    if footnote:
        caption_str = f"{caption_full}\\protect\\footnotemark"
        footnote_line = f"\\footnotetext{{{footnote}}}\n"
    else:
        caption_str = caption_full
        footnote_line = ""

    # ── Editable figure tex file (written once, never overwritten) ────────
    if strings is not None or nudge_labels:
        from config import LATEX_FIGURES_TEX_DIR
        prefix = _macro_prefix(name)
        caption_macro = _macro_name(prefix, "caption")
        strings_file = LATEX_FIGURES_TEX_DIR / f"{name}.tex"
        strings_input_path = f"texparts/figures/{name}"
        # Build list of nudge macros (auto-derived names).
        nudge_macros: list[str] = []
        if nudge_labels:
            import re as _re
            for entry in nudge_labels:
                if isinstance(entry, str):
                    label_id = _re.sub(r"[\\{}]", "", entry)
                    label_id = _re.sub(r"[^A-Za-z0-9]+", "_", label_id).strip("_")
                else:
                    label_id, _ = entry
                nudge_macros.append(_nudge_macro_name(prefix, label_id))
        if not strings_file.exists():
            lines = [
                f"% Editable figure definition for {name}",
                f"% Edit freely --- Python will NOT overwrite this file.",
                f"% To regenerate defaults, delete this file and re-run the script.",
            ]
            for key, value in (strings or {}).items():
                macro = _macro_name(prefix, key)
                # Escape unescaped % so they don't comment out the closing brace
                value_esc = re.sub(r"(?<!\\)%", r"\\%", str(value))
                lines.append(f"\\def{macro}{{{value_esc}}}%")
            if nudge_macros:
                lines.append("% --- Per-label y-nudge knobs (override with \\renewcommand)")
                lines.append("% Example: \\renewcommand" + nudge_macros[0] + "{-3pt}  % shift label up by 3pt")
                for m in nudge_macros:
                    lines.append(f"\\providecommand{m}{{0pt}}%")
            lines.append(f"\\def{caption_macro}{{{caption_str}}}%")
            lines.append(f"%")
            lines.append(f"\\begin{{figure}}[htbp]")
            lines.append(f"  \\centering")
            lines.append(
                f"  \\resizebox{{{resizebox_width}}}{{!}}"
                f"{{\\input{{{include_path}}}}}"
            )
            lines.append(f"  \\caption{{{caption_macro}}}")
            lines.append(f"  \\label{{{label}}}")
            lines.append(f"\\end{{figure}}")
            if footnote_line:
                lines.append(footnote_line.rstrip("\n"))
            strings_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"  Created figure tex: {strings_file}")
        else:
            # File exists: do NOT overwrite the wrapper. Keep user-authored
            # string macros intact and only warn if Python defaults drift.
            # Nudge defaults may still be added because they are additive.
            existing = strings_file.read_text(encoding="utf-8")
            stale_macros: list[str] = []
            expected_macros = {caption_macro: caption_str}
            for key, value in (strings or {}).items():
                expected_macros[_macro_name(prefix, key)] = str(value)
            for macro, expected in expected_macros.items():
                actual = _extract_figure_tex_macro_value(existing, macro)
                expected_esc = re.sub(r"(?<!\\)%", r"\\%", expected)
                if actual is None:
                    stale_macros.append(f"{macro}=missing")
                    continue
                if actual != expected_esc:
                    stale_macros.append(macro)
            missing_nudges: list[str] = []
            if nudge_macros:
                missing_nudges = [m for m in nudge_macros if m not in existing]
                if missing_nudges:
                    add_blocks = [
                        "",
                        "% --- Auto-added nudge knobs (override with \\renewcommand)",
                        *(f"\\providecommand{m}{{0pt}}%" for m in missing_nudges),
                    ]
                # Insert before the \begin{figure} line so defaults are in
                # scope when \input{...pgf} expands.
                marker = "\\begin{figure}"
                if marker in existing:
                    existing = existing.replace(
                        marker, "\n".join(add_blocks) + "\n" + marker, 1
                    )
                else:
                    existing = existing + "\n".join(add_blocks) + "\n"
                strings_file.write_text(existing, encoding="utf-8")
                print(f"  Added {len(missing_nudges)} nudge default(s) to: {strings_file}")
            if stale_macros:
                preview = ", ".join(stale_macros[:4])
                extra = "" if len(stale_macros) <= 4 else f" (+{len(stale_macros) - 4} more)"
                print(
                    "  WARNING: figure tex macros differ from current Python defaults; "
                    f"kept custom wrapper as-is: {strings_file} [{preview}{extra}]"
                )
            print(f"  Figure tex exists (kept): {strings_file}")

        # Wrapper is a one-line macro call --- always regenerated, no user content.
        # Commentary files that haven't migrated to \inputpgffigure{} yet
        # can still use \input{texparts/python/name}.
        tex = f"\\inputpgffigure{{{name}}}\n"
    else:
        tex = (
            f"\\begin{{figure}}[htbp]\n"
            f"  \\centering\n"
            f"  \\resizebox{{{resizebox_width}}}{{!}}{{\\input{{{include_path}}}}}\n"
            f"  \\caption{{{caption_str}}}\n"
            f"  \\label{{{label}}}\n"
            f"\\end{{figure}}\n"
            f"{footnote_line}"
        )

    out = directory / f"{name}.tex"
    out.write_text(tex, encoding="utf-8")
    print(f"Saved TeX (PGF): {out}")
    return out


# ── CZ figure annotation helpers ─────────────────────────────────────────────

def _fmt_czk(amount: int) -> str:
    """Formátuje celé číslo jako CZK s LaTeX thin-space oddělovači tisíců."""
    return f"{amount:,}".replace(",", "\\,") + "\\,Kč"


def _add_vertical_ref(ax: plt.Axes, x_kczk: float, label: str,
                      color: str, alpha: float = 0.7,
                      linestyle: tuple = (0, (3, 4))) -> None:
    """Přidá svislou referenční čáru s anotací do grafu ax.

    Anotace je umístěna nad osou (axes fraction pro y = 1) aby byla
    jasně viditelná a nepřekrývala data.
    """
    ax.axvline(x_kczk, color=color, linewidth=0.8, linestyle=linestyle,
               alpha=alpha, zorder=1)
    ann = ax.annotate(
        label,
        xy=(x_kczk, 1),
        xycoords=("data", "axes fraction"),
        xytext=(0, 8), textcoords="offset points",
        fontsize=FONT_SIZE - 2, color=color, va="bottom", ha="center",
    )
    ann.set_clip_on(False)


def _apply_figure_layout(ax: plt.Axes, *,
                         hspace: float | None = None) -> None:
    """Nastav layout figury: right=0.78 (místo pro inline popisky) + pad=1.5.

    Přesune také titulek os (ax.set_title) do fig.suptitle, aby byl zarovnán
    na střed celé figury, nikoli zúžené oblasti os.
    Volejte na konci každé funkce vracející fig, místo _add_linestyle_key.
    """
    fig = ax.get_figure()
    fig._tight_layout_kwargs = {"pad": 1.5}
    spa: dict = {"right": 0.78}
    if hspace is not None:
        spa["hspace"] = hspace
    fig._subplots_adjust_kwargs = spa
    # Per-axes grid: major more visible than minor.
    for _ax in fig.axes:
        _ax.grid(True, which="major", alpha=0.45, linewidth=0.5, color="#CCCCCC")
        _ax.grid(True, which="minor", alpha=0.18, linewidth=0.3, color="#CCCCCC")
    # Re-centre the axes title on the full figure width.
    ax_top = fig.axes[0]
    title_text = ax_top.get_title()
    if title_text:
        ax_top.set_title("")
        fig.suptitle(title_text, y=1.0, fontsize=FIGURE_TITLE_SIZE, va="bottom")


def _add_linestyle_key(ax: plt.Axes, *, hspace: float | None = None,
                       title_pad: float = 33,
                       svarc_linestyle: tuple = (0, (6, 1))) -> None:
    """Přidá legendu typů čar pod osu x (zarovnanou na střed obrázku).

    Barva (typ OSVČ / zaměstnanec) je vysvětlena inline popisky přímo u křivek;
    legenda vysvětluje, co zobrazuje každý linestyle.
    """
    fig = ax.get_figure()
    key = [
        Line2D([0], [0], color="#444444", linewidth=1.5, linestyle="--",
               label="výdaje\u00a0dle\u00a0paušálu"),
        Line2D([0], [0], color="#444444", linewidth=1.5, linestyle="-.", alpha=0.6,
               label="výdajový\u00a0paušál"),
        Line2D([0], [0], color="#444444", linewidth=2.0, linestyle=":",
               label="paušální\u00a0daň"),
        Line2D([0], [0], color="#888888", linewidth=1.0, linestyle=(0, (3, 1.5)), alpha=0.7,
               label="bez\u00a0výdajů"),
        Line2D([0], [0], color="#888888", linewidth=1.2, linestyle=svarc_linestyle, alpha=0.85,
               label="16\\,\\%~výdaje~(PAQ)"),
    ]
    fig._tight_layout_kwargs = {"pad": 1.5}
    spa = {"right": 0.78}
    if hspace is not None:
        spa["hspace"] = hspace
    fig._subplots_adjust_kwargs = spa
    # Place at figure bottom, horizontally centred on the figure (not axes).
    fig_h = fig.get_figheight()            # inches
    gap_in = (7 + FONT_SIZE) / 72          # ~xlabel height + small gap
    y_frac = gap_in / fig_h                # fraction of figure height
    fig.legend(handles=key, frameon=False, fontsize=FONT_SIZE - 2,
               loc="upper center", bbox_to_anchor=(0.5, y_frac),
               ncols=5, handlelength=1.2, handletextpad=0.4, columnspacing=0.8)
    # Move the axes title → fig.suptitle so it is centred on the figure
    # (not on the axes, which are shifted left by right=0.78).
    ax_top = fig.axes[0]
    title_text = ax_top.get_title()
    if title_text:
        ax_top.set_title("")               # remove the axes-level title
        fig.suptitle(title_text, y=1.0, fontsize=FIGURE_TITLE_SIZE,
                     va="bottom")


def _bottom_legend(fig: plt.Figure, c_emp: str,
                   osvc_types: list[tuple[float, str, str]],
                   ax: plt.Axes | None = None) -> None:
    """Přidá sdílenou legendu barev dole mimo osy.

    Pokud je předána `ax`, přidá také interní linestyle key (typ čáry).
    """
    fig.subplots_adjust(bottom=0.20)
    legend_handles = [
        Line2D([0], [0], color=c_emp, linewidth=2.0,
               label="Zaměstnanec (celk.\u00a0nákl.)"),
    ]
    for _er, lbl, col in osvc_types:
        legend_handles.append(
            Line2D([0], [0], color=col, linewidth=1.5, linestyle="--", label=lbl))
    fig.legend(handles=legend_handles, frameon=False, fontsize=FONT_SIZE - 2,
               loc="lower center", bbox_to_anchor=(0.5, -0.01), ncols=2)
    if ax is not None:
        _add_linestyle_key(ax)
