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
        LaTeX font size command (default ``small``).
    position:
        Float placement, e.g. ``"htbp"`` or ``"H"``.
    index_name:
        Header label for the index column (default: empty).
    bold_header:
        Wrap column header cells in ``\\textbf{}``.
    midrule_after:
        List of row *index values* after which to insert a ``\midrule``.
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
        rows_str.append("  " + " & ".join(cells) + r" \\")
        if midrule_after and idx in midrule_after:
            rows_str.append(r"  \midrule")

    header_row = "  " + " & ".join([idx_header] + headers) + r" \\"

    # Note line
    note_block = ""
    if note:
        # Span all columns using \multicolumn
        escaped_note = note.replace("%", r"\%")
        note_block = (
            f"  \\multicolumn{{{n_cols}}}{{l}}{{"
            f"\\footnotesize {escaped_note}"
            f"}} \\\\\n"
        )

    lines = [
        f"\\begin{{table}}[{position}]",
        "  \\centering",
        f"  \\{fontsize}",
    ]
    if caption:
        lines.append(f"  \\caption{{{caption}}}")
    if label:
        lines.append(f"  \\label{{{label}}}")

    # Use tabularx when column spec contains X columns (requires \linewidth arg)
    use_tabularx = "X" in col_format
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
