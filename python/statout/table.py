"""
LaTeX table generation from pandas DataFrames.

Produces ``booktabs``-style tables compatible with the CTUthesis class
(which loads ``booktabs``, ``tabularx``, ``multirow``, and ``siunitx``).

Typical usage
-------------
>>> from statout.table import save_table_tex
>>> save_table_tex(df, "flexicurity_table",
...               caption="Comparison of labour market indicators.",
...               label="tab:flexicurity",
...               note="Source: Eurostat, ETUI.")
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Union

import pandas as pd


def to_latex(
    df: pd.DataFrame,
    *,
    caption: str = "",
    label: str = "",
    note: str = "",
    cite_keys: Optional[list[str]] = None,
    col_headers: Optional[list[str]] = None,
    col_format: Optional[str] = None,
    fontsize: str = "small",
    position: str = "htbp",
    index_name: str = "",
    bold_header: bool = True,
    midrule_after: Optional[list[str]] = None,
    italic_rows: Optional[list[str]] = None,
    long_table: bool = False,
    arraystretch: Optional[float] = None,
    sans_serif: bool = False,
) -> str:
    r"""Generate a LaTeX ``table`` + ``tabular`` environment in *booktabs* style.

    Parameters
    ----------
    df:
        DataFrame where each row is an indicator and each column is a
        variable or country.  Cell values should already be formatted as
        strings for clean rendering (e.g. ``"€ 36 176"``).  NaN cells are
        rendered as ``--``.
    caption:
        Table caption (goes above the table as per CTU convention).
    label:
        ``\label{}`` reference key.
    note:
        Source / footnote text appended below ``\bottomrule``.
    cite_keys:
        biblatex cite keys appended to the caption as ``\cite{key}``.
    col_headers:
        Override the column header strings (default: ``list(df.columns)``).
    col_format:
        Full LaTeX column spec, e.g. ``"lrrrrrr"``.  Auto-generated as
        ``l`` for the first column and ``r`` for the rest when omitted.
    fontsize:
        LaTeX font size command (default ``small``).  Ignored when
        ``long_table=True`` (font size commands bleed out of longtable).
    position:
        Float placement, e.g. ``"htbp"`` or ``"H"``.
    index_name:
        Header label for the index column (default: empty).
    bold_header:
        Wrap column header cells in ``\\textbf{}``.
    midrule_after:
        List of row *index values* after which to insert a ``\midrule``.
    italic_rows:
        List of row *index values* whose entire row (label + all cells) should
        be wrapped in ``\textit{}``.  Use for sub-rows and derived indicators.
    long_table:
        When ``True``, emit an ``xltabular`` environment (longtable + tabularx
        combined) instead of the default ``table`` + ``tabularx`` pair.  This
        supports page breaks, repeating headers, and continuation captions.
        The ``position`` and ``fontsize`` parameters are ignored.
    """
    if cite_keys:
        caption = caption + " " + "".join(f"\\cite{{{k}}}" for k in cite_keys)

    cols = list(df.columns)
    n_cols = 1 + len(cols)  # index column + data columns

    # Column format
    if col_format is None:
        col_format = "l" + "r" * len(cols)

    # Column headers
    headers = col_headers if col_headers is not None else [str(c) for c in cols]
    if bold_header:
        headers = [f"\\textbf{{{h}}}" for h in headers]
        idx_header = f"\\textbf{{{index_name}}}" if index_name else ""
    else:
        idx_header = index_name

    # Build rows
    def _fmt(val) -> str:
        if pd.isna(val):
            return "--"
        return str(val)

    rows_str: list[str] = []
    for idx, row in df.iterrows():
        cells = [str(idx)] + [_fmt(v) for v in row]
        if italic_rows and idx in italic_rows:
            cells = [f"\\textit{{{c}}}" for c in cells]
        rows_str.append("  " + " & ".join(cells) + r" \\")
        if midrule_after and idx in midrule_after:
            rows_str.append(r"  \midrule")

    header_row = "  " + " & ".join([idx_header] + headers) + r" \\"

    # Note line
    note_block = ""
    if note:
        # Span all columns using \multicolumn
        escaped_note = re.sub(r"(?<!\\)%", r"\\%", note)
        note_block = (
            f"  \\multicolumn{{{n_cols}}}{{@{{}}p{{\\linewidth}}@{{}}}}{{"
            f"\\footnotesize {escaped_note}"
            f"}} \\\\\n"
        )

    if long_table:
        # ── xltabular (longtable + tabularx, multi-page) ─────────────────────
        # No \begin{table} wrapper; caption and label live inside the env.
        cap_line = f"  \\caption{{{caption}}}"
        if label:
            cap_line += f"\\label{{{label}}}"
        cap_line += r" \\"

        cont_cap_line = "  \\caption*{(pokra\u010dov\u00e1n\u00ed)} \\\\"
        foot_line = (
            f"  \\multicolumn{{{n_cols}}}{{r}}"
            "{\\footnotesize(pokra\u010duje na dal\u0161\u00ed str\u00e1nce)} \\\\"
        )

        lines = [f"\\begin{{xltabular}}{{\\linewidth}}{{{col_format}}}"]
        font_cmd = f"\\{fontsize}" + (r"\sffamily" if sans_serif else "")
        if arraystretch is not None:
            lines.insert(0, f"{{{font_cmd}\\renewcommand{{\\arraystretch}}{{{arraystretch}}}")
        else:
            lines.insert(0, f"{{{font_cmd}")
        if caption:
            lines.append(cap_line)
        lines += [
            "  \\toprule",
            header_row,
            "  \\midrule",
            "  \\endfirsthead",
            cont_cap_line,
            "  \\toprule",
            header_row,
            "  \\midrule",
            "  \\endhead",
            "  \\midrule",
            foot_line,
            "  \\endfoot",
            "  \\bottomrule",
        ]
        if note_block:
            lines.append(note_block.rstrip())
        lines.append("  \\endlastfoot")
        lines += rows_str
        lines.append("\\end{xltabular}")
        lines.append("}")  # close font-size / arraystretch group
    else:
        lines = [
            f"\\begin{{table}}[{position}]",
            "  \\centering",
            f"  \\{fontsize}",
        ]
        if caption:
            lines.append(f"  \\caption{{{caption}}}")
        if label:
            lines.append(f"  \\label{{{label}}}")

        # Use tabularx when column spec contains X-based columns (X, R, L, C, s)
        use_tabularx = bool(re.search(r'[XRLCs]', col_format))
        if use_tabularx:
            tabular_begin = f"  \\begin{{tabularx}}{{\\linewidth}}{{{col_format}}}"
            tabular_end   = "  \\end{tabularx}"
        else:
            tabular_begin = f"  \\begin{{tabular}}{{{col_format}}}"
            tabular_end   = "  \\end{tabular}"

        lines += [
            tabular_begin,
            "    \\toprule",
            "  " + header_row,
            "    \\midrule",
        ]
        lines += rows_str
        lines.append("    \\bottomrule")
        if note_block:
            lines.append(note_block.rstrip())
        lines += [
            tabular_end,
            "\\end{table}",
        ]
    return "\n".join(lines) + "\n"


def save_table_tex(
    df: pd.DataFrame,
    name: str,
    *,
    caption: str = "",
    label: str = "",
    note: str = "",
    cite_keys: Optional[list[str]] = None,
    out_dir: Optional[Union[str, Path]] = None,
    **kwargs,
) -> Path:
    """Write a LaTeX table to *out_dir/<name>.tex*.

    All ``**kwargs`` are forwarded to :func:`to_latex`.

    Parameters
    ----------
    name:
        Output filename stem (no ``.tex`` extension).
    cite_keys:
        biblatex cite keys appended to the caption (see :func:`to_latex`).
    out_dir:
        Directory to write into.  Defaults to ``LATEX_TEXPARTS_DIR`` from
        ``config``.
    """
    from config import LATEX_TEXPARTS_DIR

    directory = Path(out_dir) if out_dir else LATEX_TEXPARTS_DIR
    tex = to_latex(df, caption=caption, label=label, note=note,
                   cite_keys=cite_keys, **kwargs)
    out = directory / f"{name}.tex"
    out.write_text(tex, encoding="utf-8")
    print(f"Saved TeX: {out}")
    return out
