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
            "grid.linewidth": 0.4,
            "grid.alpha": 0.5,
            "grid.color": "#CCCCCC",
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

    renderer = fig.canvas.get_renderer()

    # ── snug suptitle down to just above axes content ──────────────────────
    if has_suptitle:
        st = fig._suptitle
        # Temporarily hide suptitle so it doesn't inflate the bbox
        st.set_visible(False)
        # Get top of all remaining content (axes, annotations, legends…)
        bb_content = fig.get_tightbbox(renderer)
        st.set_visible(True)
        if bb_content is not None:
            fig_h = fig.get_figheight()
            gap_pt = 6                                    # points above content
            content_top_frac = bb_content.y1 / fig_h
            new_y = content_top_frac + gap_pt / 72 / fig_h
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


def save_figure_tex(
    name: str,
    caption: str,
    label: str,
    *,
    out_dir: Optional[Union[str, Path]] = None,
    include_path: Optional[str] = None,
    width: str = r"\columnwidth",
    cite_key: Optional[str] = None,
) -> Path:
    r"""Write a LaTeX ``\begin{figure}`` environment that includes *name*.pdf.

    Parameters
    ----------
    name:
        Figure filename *without* extension.
    caption:
        Caption text (Czech OK).
    label:
        ``\label{}`` key, e.g. ``"fig:gdp_timeline"``.
    out_dir:
        Directory for the .tex file.  Defaults to ``LATEX_TEXPARTS_DIR``.
    include_path:
        Path for ``\includegraphics``.  Defaults to ``"../pics/<name>"``.
    width:
        LaTeX width expression (default ``\columnwidth``).
    cite_key:
        biblatex cite key for the data source.  When provided, ``\cite{key}``
        is appended to the caption so the bibliography entry is referenced.
    """
    from config import LATEX_TEXPARTS_DIR

    directory = Path(out_dir) if out_dir else LATEX_TEXPARTS_DIR
    include_path = include_path or f"../pics/python/{name}"

    caption_full = caption
    if cite_key:
        caption_full += f" \\cite{{{cite_key}}}"

    tex = (
        f"\\begin{{figure}}[htbp]\n"
        f"  \\centering\n"
        f"  \\includegraphics[width={width}]{{{include_path}}}\n"
        f"  \\caption{{\\centering {caption_full}}}\n"
        f"  \\label{{{label}}}\n"
        f"\\end{{figure}}\n"
    )
    out = directory / f"{name}.tex"
    out.write_text(tex, encoding="utf-8")
    print(f"Saved TeX: {out}")
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
