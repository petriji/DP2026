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
from typing import Optional, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from config import (
    CMAP_DIVERGING,
    CMAP_SEQUENTIAL,
    FIGURE_DPI,
    FIGURE_FORMAT,
    FIGURE_HEIGHT_CM,
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
            "font.size": FONT_SIZE,
            "axes.titlesize": FONT_SIZE,
            "axes.labelsize": FONT_SIZE,
            "xtick.labelsize": FONT_SIZE,
            "ytick.labelsize": FONT_SIZE,
            "legend.fontsize": FONT_SIZE,
            "figure.titlesize": FONT_SIZE + 1,
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
\sisetup{output-decimal-marker={,}, per-mode=symbol}
\usepackage[pdftex]{contour}
\contourlength{0.6pt}
% Stub \contour for the metrics pass (real one comes from CTUthesis.cls).
\providecommand{\contour}[2]{#2}
\usepackage{pdfcomment}
% Stub \pdftooltip for the PGF metrics pass (real one from CTUthesis.cls).
% Falls back to showing the displayed text only, so figures degrade gracefully.
\providecommand{\pdftooltip}[2]{#1}
% Stub \CTUtooltiplink (user-level alias used in PGF annotations) for the
% metrics pass.  Falls back to showing the visible text only (arg #2).
% \CTU@tooltiplink (the internal @-command) is NOT used directly in PGF
% annotations because \makeatletter inside a tokenised group has no effect.
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
    codes = geo_set if geo_set is not None else GEO_ACRO
    for child in ax.get_children():
        if not hasattr(child, "get_text"):
            continue
        txt = child.get_text().strip()
        if txt not in codes:
            continue
        if values is not None and txt in values:
            # Country code labels never become hyperlinks: their acro entries
            # use tag=geo which is excluded from the printed acronym list, so
            # no \hypertarget{geo-XX} exists.  A GoTo link to a missing
            # destination falls back to page 1 in Acrobat.  Use \pdftooltip
            # (annotation only, no link) so hover shows the long Czech name.
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
    import pandas as pd  # noqa: F401 — guard if not yet imported at module top
    if mpl.get_backend() != "pgf":
        return
    for geo in pivot.columns:
        series = pivot[geo].dropna()
        for year, val in series.items():
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
    points: "pd.DataFrame",
    *,
    geo_col: str = "geo",
    x_col: str = "x",
    y_col: str = "y",
    fmt_x: str = "{:.1f}",
    fmt_y: str = "{:.1f}",
    label_x: str = "x",
    label_y: str = "y",
) -> None:
    r"""Overlay invisible ``\pdftooltip`` annotations at every scatter point.

    Each row of *points* yields one tooltip showing
    ``"<long-name> | <label_x>: N | <label_y>: N"`` on hover (Acrobat/Foxit).
    No-op when the active matplotlib backend is not ``pgf``.
    """
    if mpl.get_backend() != "pgf":
        return
    for _, row in points.iterrows():
        geo = str(row[geo_col])
        long = GEO_LONG_NAMES.get(geo, geo)
        x_str = fmt_x.format(float(row[x_col]))
        y_str = fmt_y.format(float(row[y_col]))
        tooltip_text = f"{long} | {label_x}: {x_str} | {label_y}: {y_str}"
        ax.text(
            float(row[x_col]),
            float(row[y_col]),
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
            "font.size": FONT_SIZE,
            "axes.titlesize": FONT_SIZE + 2,
            "axes.labelsize": FONT_SIZE,
            "xtick.labelsize": FONT_SIZE,
            "ytick.labelsize": FONT_SIZE,
            "legend.fontsize": FONT_SIZE,
            "figure.titlesize": FONT_SIZE + 2,
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
        try:
            fig.tight_layout(**_tl_kwargs)
        except Exception:
            pass  # some constrained-layout figures raise here — safe to ignore
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
    """Convert ``'vyhled_porodnost_vyvoj'`` → ``'VyhledPorodnostVyvoj'``."""
    return "".join(part.capitalize() for part in name.split("_"))


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

    Returns the total number of replacements made.
    """
    prefix = _macro_prefix(name)
    content = pgf_path.read_text(encoding="utf-8")
    total = 0
    # Replace longest strings first to avoid partial matches.
    for key, value in sorted(strings.items(), key=lambda kv: -len(kv[1])):
        macro = _macro_name(prefix, key)
        count = content.count(value)
        if count:
            content = content.replace(value, macro)
            total += count
    if total:
        pgf_path.write_text(content, encoding="utf-8")
    return total


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

    return notes


def savefig_pgf(
    fig: plt.Figure,
    name: str,
    *,
    out_dir: Optional[Union[str, Path]] = None,
    tight: bool = True,
    strings: Optional[dict[str, str]] = None,
) -> Path:
    r"""Save *fig* as a ``.pgf`` file for inclusion via ``\input{}`` in LaTeX.

    The PGF backend must be active (call ``apply_style_pgf()`` first).
    Unlike ``savefig()``, this does **not** produce a standalone PDF —
    the ``.pgf`` file is compiled inside the host document.

    If *strings* is given (``{key: literal_value}``), the saved ``.pgf`` is
    post-processed: every *literal_value* is replaced with a ``\strXxx``
    macro reference.  The matching ``\def`` lines are emitted by
    ``save_figure_tex_pgf(strings=...)``.
    """
    if tight:
        _tl_kwargs = getattr(fig, '_tight_layout_kwargs', {})
        try:
            fig.tight_layout(**_tl_kwargs)
        except Exception:
            pass
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

    return out


# ── Citation helpers for save_figure_tex ─────────────────────────────────────

_CITE_PROVIDERS: list[tuple[str, str]] = [
    ("eurostat",         "Eurostat"),
    ("oecd_aias_ictwss", "OECD\\,ICTWSS"),
    ("oecd",             "OECD"),
    ("mpsv_ipp",         "MPSV/IPP"),
    ("mpsv_ispv",        "MPSV/ISPV"),
    ("zakon_",           "zákon\\,ČR"),
    ("nv_",              "zákon\\,ČR"),
    ("sdeleni_",         "zákon\\,ČR"),
]


def _cite_provider(key: str) -> str:
    """Return human-readable provider label for a biblatex cite key."""
    for prefix, label in _CITE_PROVIDERS:
        if key.startswith(prefix):
            return label
    return ""


def _build_cite_source(keys: list) -> str:
    """Return grouped 'Provider~\\cite{k1}\\cite{k2}, …' string."""
    from collections import OrderedDict
    groups: "OrderedDict[str, list]" = OrderedDict()
    for k in keys:
        lbl = _cite_provider(k)
        if lbl not in groups:
            groups[lbl] = []
        groups[lbl].append(k)
    parts = []
    for lbl, ks in groups.items():
        cites = "".join(f"\\cite{{{k}}}" for k in ks)
        parts.append(f"{lbl}~{cites}" if lbl else cites)
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

    # Resolve cite keys — cite_keys takes priority over deprecated cite_key
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
        caption_full = f"{title}. Zdroj dat: {source}."
    else:
        caption_full = title

    if footnote:
        caption_str = f"\\centering {caption_full}\\protect\\footnotemark"
        footnote_line = f"\\footnotetext{{{footnote}}}\n"
    else:
        caption_str = f"\\centering {caption_full}"
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
        caption_full = f"{title}. Zdroj dat: {source}."
    else:
        caption_full = title

    if footnote:
        caption_str = f"\\centering {caption_full}\\protect\\footnotemark"
        footnote_line = f"\\footnotetext{{{footnote}}}\n"
    else:
        caption_str = f"\\centering {caption_full}"
        footnote_line = ""

    # ── Editable figure tex file (written once, never overwritten) ────────
    if strings:
        from config import LATEX_FIGURES_TEX_DIR
        prefix = _macro_prefix(name)
        strings_file = LATEX_FIGURES_TEX_DIR / f"{name}.tex"
        strings_input_path = f"texparts/figures/{name}"
        if not strings_file.exists():
            caption_macro = _macro_name(prefix, "caption")
            lines = [
                f"% Editable figure definition for {name}",
                f"% Edit freely — Python will NOT overwrite this file.",
                f"% To regenerate defaults, delete this file and re-run the script.",
            ]
            for key, value in strings.items():
                macro = _macro_name(prefix, key)
                lines.append(f"\\def{macro}{{{value}}}%")
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
            print(f"  Figure tex exists (kept): {strings_file}")

        # Wrapper is a one-line macro call — always regenerated, no user content.
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
    """Formátuje celé číslo jako CZK s úzkými mezerami jako oddělovači tisíců."""
    return f"{amount:,}".replace(",", "\u202f") + "\u202fKč"


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
        fig.suptitle(title_text, y=1.0, fontsize=FONT_SIZE, va="bottom")


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
               label="16\u202f%\u00a0výdaje\u00a0(PAQ)"),
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
        fig.suptitle(title_text, y=1.0, fontsize=FONT_SIZE,
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
