r"""
stats_analytics.py – generate Python-produced figures and LaTeX snippets for
the thesis, based on which texparts are actually \input{}-ed in the project.

HOW IT WORKS
------------
1.  ``registry.toml`` (same directory) maps a short key to the analysis script
    that produces it and the texpart / pic stem patterns it creates.  This is
    the only place you need to touch when adding a new analysis script.

2.  The script scans ``latex/main.tex`` recursively (following every
    ``\input{…}`` and ``\include{…}``) to collect every referenced
    Python-generated figure stem, including:
    - ``\input{texparts/python/STEM}``
    - ``\inputpgffigure{STEM}``

3.  A registry entry is *active* if at least one of its texpart patterns
    matches at least one referenced stem.  Inactive entries are never run,
    so removing an ``\input`` from the .tex is sufficient to stop generating
    the corresponding figures.

4.  An active entry is run when any of its expected output files are absent
    (or when ``--force`` is given).

USAGE
-----
    # normal use: called by latexmkrc / LaTeX Workshop before every build
    python stats_analytics.py

    # force-regenerate one group (key from REGISTRY)
    python stats_analytics.py --force arope

    # force-regenerate everything in REGISTRY that is referenced in the .tex
    python stats_analytics.py --force all

ADDING A NEW ANALYSIS SCRIPT
-----------------------------
1.  Create ``analyses/my_new_script.py`` that outputs into
    ``LATEX_PICS_DIR`` / ``LATEX_TEXPARTS_DIR`` (both from config.py).
2.  Add a section to ``registry.toml``.
3.  Reference the output stem in LaTeX using either:
    - ``\input{texparts/python/my_texpart}``, or
    - ``\inputpgffigure{my_texpart}``.
4.  Run ``python python_analytics.py`` once — it will detect the new missing
    output and run the script automatically.
"""

from __future__ import annotations

import ast
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from config import LATEX_PICS_DIR

PYTHON_DIR  = Path(__file__).parent.resolve()
DP_DIR      = PYTHON_DIR.parent
LATEX_DIR   = DP_DIR / "latex"
PICS_DIR    = Path(LATEX_PICS_DIR)
TEX_DIR     = LATEX_DIR / "texparts" / "python"
FIG_TEX_DIR = LATEX_DIR / "texparts" / "figures"
REVIEW_DIR  = DP_DIR / "review"
FIG_EXTS    = (".pgf", ".pdf", ".png", ".svg")

# ── Registry ──────────────────────────────────────────────────────────────────
# Loaded from registry.toml (same directory as this script).
# See that file for the schema and instructions for adding new analysis scripts.

with open(PYTHON_DIR / "analytics_registry.toml", "rb") as _f:
    REGISTRY: dict[str, dict] = tomllib.load(_f)

# ── LaTeX project scanner ─────────────────────────────────────────────────────

_INPUT_RE   = re.compile(r'\\(?:input|include)\{([^}]+)\}')
_PGF_RE     = re.compile(r'\\inputpgffigure\{([^}]+)\}')
_COMMENT_RE = re.compile(r'%.*')
_CAPTION_RE = re.compile(r'\\caption(?:\[[^\]]*\])?\{')
_DEF_CAPTION_RE = re.compile(r'\\def\\[A-Za-z0-9_]*Caption\{')
_DEF_STR_RE = re.compile(r'\\def\\str([A-Za-z0-9_]+)\{')
_YEAR_RE = re.compile(r'\b(?:19|20)\d{2}\b')
_AUX_FIG_LABEL_RE = re.compile(r'\\newlabel\{fig:([^}]+)\}\{\{([^}]+)\}')


def _latex_escape(text: str) -> str:
    """Escape plain text for safe placement into LaTeX table cells."""
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )

def _tex_stems(tex_file: Path, visited: set[Path] | None = None) -> set[str]:
    """Recursively collect Python-generated figure stems from *tex_file*.

    Follows every ``\\input{…}`` / ``\\include{…}`` call, skipping files
    already visited (cycle guard) and files that don't exist.
    """
    if visited is None:
        visited = set()
    tex_file = tex_file.resolve()
    if tex_file in visited or not tex_file.exists():
        return set()
    visited.add(tex_file)

    stems: set[str] = set()
    base  = tex_file.parent

    for raw_line in tex_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = _COMMENT_RE.sub("", raw_line)           # strip TeX comments

        # Capture PGF figure macro usage directly from commentary/main files.
        for stem in _PGF_RE.findall(line):
            stems.add(stem.strip().removesuffix(".tex"))

        for arg in _INPUT_RE.findall(line):
            arg = arg.strip()
            # Capture python-generated texparts
            for prefix in ("texparts/python/", "texparts\\python\\"):
                if arg.startswith(prefix):
                    stem = arg[len(prefix):]
                    stem = stem.removesuffix(".tex")
                    stems.add(stem)
                    break
            else:
                # Recurse into other \input{} calls.
                # Try both file-relative and latex-root-relative resolution because
                # this project commonly uses \input{texparts/...} from nested files.
                arg_with_ext = arg if arg.endswith(".tex") else f"{arg}.tex"
                candidates = [base / arg_with_ext]
                if arg.startswith(("texparts/", "texparts\\")):
                    candidates.append(LATEX_DIR / arg_with_ext)

                for candidate in candidates:
                    stems |= _tex_stems(candidate, visited)

    return stems


# ── Output-existence checks ───────────────────────────────────────────────────

def _any_missing(entry: dict, referenced: set[str]) -> bool:
    """Return True if any output file that *should* exist is absent.

    Only checks outputs whose texpart pattern matched a referenced stem – so
    ``arope_map_*`` is only checked when e.g. ``arope_map_2025`` is referenced.
    """
    # Check texpart .tex files
    for pattern in entry["texparts"]:
        matching = [s for s in referenced if fnmatch.fnmatch(s, pattern)]
        for stem in matching:
            if not (TEX_DIR / f"{stem}.tex").exists():
                return True
        # Exact pattern that did not match any referenced stem → no output expected
        if not any(fnmatch.fnmatch(s, pattern) for s in referenced):
            # Pattern itself is exact (no wildcards) and referenced → check directly
            if "*" not in pattern and "?" not in pattern and pattern in referenced:
                if not (TEX_DIR / f"{pattern}.tex").exists():
                    return True

    # Check figure files in configured output dir.
    # Some analyses produce .pgf, others .pdf/.png/.svg.
    for pattern in entry.get("pics", []):
        matched_stems = [s for s in referenced if fnmatch.fnmatch(s, pattern)]
        for stem in matched_stems:
            if not any((PICS_DIR / f"{stem}{ext}").exists() for ext in FIG_EXTS):
                return True
        if not matched_stems and "*" not in pattern and pattern in referenced:
            if not any((PICS_DIR / f"{pattern}{ext}").exists() for ext in FIG_EXTS):
                return True

    return False


# ── Runner ────────────────────────────────────────────────────────────────────

def _run(key: str, entry: dict, *, target_year: int) -> None:
    script = entry["script"]
    print(f"[stats_analytics] running: {script}", flush=True)
    env = os.environ.copy()
    env["DP_TARGET_YEAR"] = str(target_year)
    result = subprocess.run([sys.executable, script], cwd=PYTHON_DIR, env=env)
    if result.returncode != 0:
        print(
            f"[stats_analytics] ERROR: {script} exited with code {result.returncode}",
            flush=True,
        )
        sys.exit(result.returncode)


def _covered_stems(referenced: set[str]) -> set[str]:
    """Return referenced stems covered by at least one registry texpart pattern."""
    covered: set[str] = set()
    for entry in REGISTRY.values():
        for pattern in entry["texparts"]:
            for stem in referenced:
                if fnmatch.fnmatch(stem, pattern):
                    covered.add(stem)
    return covered


def _run_fallback_for_uncovered(referenced: set[str], *, target_year: int) -> None:
    """Run analyses/<stem>.py for referenced stems missing from registry.

    This makes "Clean + Analytics + Build all" robust for freshly-added
    analyses before registry.toml is updated.
    """
    uncovered = sorted(referenced - _covered_stems(referenced))
    if not uncovered:
        return

    for stem in uncovered:
        texpart = TEX_DIR / f"{stem}.tex"
        if texpart.exists():
            continue

        candidate = PYTHON_DIR / "analyses" / f"{stem}.py"
        if not candidate.exists():
            continue

        print(
            f"[stats_analytics] fallback: running unregistered analysis {candidate.name}",
            flush=True,
        )
        env = os.environ.copy()
        env["DP_TARGET_YEAR"] = str(target_year)
        result = subprocess.run([sys.executable, str(candidate)], cwd=PYTHON_DIR, env=env)
        if result.returncode != 0:
            print(
                f"[stats_analytics] ERROR: fallback {candidate.name} exited with code {result.returncode}",
                flush=True,
            )
            sys.exit(result.returncode)

    still_missing = [s for s in uncovered if not (TEX_DIR / f"{s}.tex").exists()]
    if still_missing:
        print(
            "[stats_analytics] ERROR: referenced python texparts are not covered by analytics_registry.toml "
            "and no fallback script produced them:",
            flush=True,
        )
        for stem in still_missing:
            print(f"  - {stem}", flush=True)
        print(
            "[stats_analytics] Add/update entries in python/analytics_registry.toml.",
            flush=True,
        )
        sys.exit(2)


def _extract_balanced_brace_payload(text: str, open_brace_index: int) -> str | None:
    """Return payload inside a balanced { ... } group starting at open_brace_index."""
    if open_brace_index < 0 or open_brace_index >= len(text) or text[open_brace_index] != "{":
        return None

    depth = 0
    for i in range(open_brace_index, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1 : i]
    return None


def _collect_caption_texts(stem: str) -> list[str]:
    """Collect caption-like texts associated with one generated stem."""
    texts: list[str] = []
    candidates = [
        TEX_DIR / f"{stem}.tex",
        FIG_TEX_DIR / f"{stem}.tex",
    ]
    for path in candidates:
        if not path.exists():
            continue
        body = path.read_text(encoding="utf-8", errors="replace")

        for m in _CAPTION_RE.finditer(body):
            payload = _extract_balanced_brace_payload(body, m.end() - 1)
            if payload and payload.strip():
                texts.append(payload.strip())

        for m in _DEF_CAPTION_RE.finditer(body):
            payload = _extract_balanced_brace_payload(body, m.end() - 1)
            if payload and payload.strip():
                texts.append(payload.strip())

    return texts


def _collect_wrapper_string_defs(stem: str) -> list[tuple[str, str]]:
    """Collect all wrapper string macro definitions from the editable figure tex."""
    path = FIG_TEX_DIR / f"{stem}.tex"
    if not path.exists():
        return []

    body = path.read_text(encoding="utf-8", errors="replace")
    out: list[tuple[str, str]] = []
    for m in _DEF_STR_RE.finditer(body):
        macro = m.group(1)
        payload = _extract_balanced_brace_payload(body, m.end() - 1)
        if payload and payload.strip():
            out.append((macro, payload.strip()))
    return out


def _extract_years(text: str) -> list[int]:
    return [int(y) for y in _YEAR_RE.findall(text)]


def _is_figure_stem(stem: str) -> bool:
    """Heuristic: stem is a figure when there is a rendered figure output."""
    if (FIG_TEX_DIR / f"{stem}.tex").exists():
        return True
    return any((PICS_DIR / f"{stem}{ext}").exists() for ext in FIG_EXTS)


def _stem_to_script(referenced: set[str]) -> dict[str, str]:
    """Resolve each referenced stem to the script declared in the registry."""
    mapping: dict[str, str] = {}
    for stem in sorted(referenced):
        for entry in REGISTRY.values():
            for pattern in entry["texparts"]:
                if fnmatch.fnmatch(stem, pattern):
                    mapping[stem] = entry["script"]
                    break
            if stem in mapping:
                break
    return mapping


def _stem_to_figure_number_from_main_aux() -> dict[str, str]:
    """Read figure numbering from latex/build/main.aux as stem -> figure number."""
    aux_path = LATEX_DIR / "build" / "main.aux"
    if not aux_path.exists():
        return {}

    text = aux_path.read_text(encoding="utf-8", errors="replace")
    mapping: dict[str, str] = {}
    for stem, fig_no in _AUX_FIG_LABEL_RE.findall(text):
        mapping[stem] = fig_no
    return mapping


def _node_as_text(node: ast.AST, source: str) -> str:
    """Best-effort conversion of an AST node to compact text."""
    if isinstance(node, ast.Constant):
        return str(node.value)
    seg = ast.get_source_segment(source, node)
    if not seg:
        return "?"
    return " ".join(seg.strip().split())


def _collect_script_quality_metadata(script_relpath: str) -> dict:
    """Extract dataset/filter/fallback metadata from one analysis script.

    Fallbacks are attributed per output stem: each warn_fallback() call is
    associated with the next savefig_pgf / save_figure_tex_pgf call that
    follows it in source order, so multi-output scripts don't bleed fallback
    remarks across unrelated figures.
    """
    import warnings

    script_path = PYTHON_DIR / script_relpath
    if not script_path.exists():
        return {"datasets": [], "filters": [], "fallbacks": [], "fallbacks_by_stem": {}}

    source = script_path.read_text(encoding="utf-8", errors="replace")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(source)
    except SyntaxError:
        return {"datasets": [], "filters": [], "fallbacks": [], "fallbacks_by_stem": {}}

    datasets: list[str] = []
    filters: list[str] = []
    # (lineno, message) pairs — populated below
    fallback_calls: list[tuple[int, str]] = []
    # (lineno, stem) pairs from savefig_pgf / save_figure_tex_pgf
    save_calls: list[tuple[int, str]] = []

    module_doc = ast.get_docstring(tree) or ""
    for raw_line in module_doc.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if lower.startswith("data source:") or lower.startswith("data sources:"):
            datasets.append(line.split(":", 1)[1].strip())
        if lower.startswith("filter:") or lower.startswith("filters:"):
            filters.append(line.split(":", 1)[1].strip())

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in {"fetch_eurostat", "fetch_oecd"}:
            source_label = "Eurostat" if func_name == "fetch_eurostat" else "OECD"
            dataset = _node_as_text(node.args[0], source) if node.args else "?"
            filter_expr = _node_as_text(node.args[1], source) if len(node.args) > 1 else ""

            options: list[str] = []
            for kw in node.keywords:
                if kw.arg in {"start_period", "end_period", "force"}:
                    options.append(f"{kw.arg}={_node_as_text(kw.value, source)}")

            datasets.append(f"{source_label} {dataset}")
            if filter_expr or options:
                payload = []
                if filter_expr:
                    payload.append(filter_expr)
                payload.extend(options)
                filters.append(f"{dataset}: " + ", ".join(payload))

        if func_name == "warn_fallback":
            msg = _node_as_text(node.args[0], source) if node.args else "fallback path used"
            lineno = getattr(node, "lineno", 0)
            fallback_calls.append((lineno, msg))

        if func_name == "savefig_pgf":
            # savefig_pgf(fig, stem, ...) — stem is the second argument
            stem_raw = _node_as_text(node.args[1], source) if len(node.args) > 1 else ""
            stem_clean = stem_raw.strip("'\"")
            if stem_clean:
                lineno = getattr(node, "lineno", 0)
                save_calls.append((lineno, stem_clean))

        if func_name == "save_figure_tex_pgf":
            # save_figure_tex_pgf(stem, ...) — stem is the first argument
            stem_raw = _node_as_text(node.args[0], source) if node.args else ""
            stem_clean = stem_raw.strip("'\"")
            if stem_clean:
                lineno = getattr(node, "lineno", 0)
                save_calls.append((lineno, stem_clean))

    # Sort both lists by source line number.
    fallback_calls.sort()
    save_calls.sort()

    # Attribute each fallback to the next save call that follows it.
    # If a fallback appears after all saves (e.g. post-loop clean-up), assign
    # it to the last save stem instead.
    fallbacks_by_stem: dict[str, list[str]] = {}
    for fb_line, fb_msg in fallback_calls:
        target_stem: str | None = None
        for save_line, save_stem in save_calls:
            if save_line > fb_line:
                target_stem = save_stem
                break
        if target_stem is None and save_calls:
            target_stem = save_calls[-1][1]
        if target_stem:
            fallbacks_by_stem.setdefault(target_stem, []).append(fb_msg)

    # Keep order stable while deduplicating.
    def _uniq(values: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for val in values:
            key = val.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(key)
        return out

    # Deduplicate per-stem fallbacks too.
    fallbacks_by_stem = {s: _uniq(msgs) for s, msgs in fallbacks_by_stem.items()}

    return {
        "datasets": _uniq(datasets),
        "filters": _uniq(filters),
        "fallbacks": _uniq([msg for _, msg in fallback_calls]),
        "fallbacks_by_stem": fallbacks_by_stem,
    }


def _write_pipeline_quality_table(
    referenced: set[str],
    audit_rows: list[dict],
    *,
    target_year: int,
) -> None:
    """Create a TeX table for pipeline attachment with dataset/filter metadata."""
    audit_by_stem = {row["stem"]: row for row in audit_rows}
    stem_script = _stem_to_script(referenced)
    stem_to_fig_no = _stem_to_figure_number_from_main_aux()

    script_meta_cache: dict[str, dict[str, list[str]]] = {}
    rows: list[dict[str, str]] = []

    for stem in sorted(s for s in referenced if _is_figure_stem(s)):
        script = stem_script.get(stem, "<unmapped>")
        if script not in script_meta_cache:
            script_meta_cache[script] = _collect_script_quality_metadata(script)
        meta = script_meta_cache[script]

        audit_row = audit_by_stem.get(stem, {})
        years = audit_row.get("years", [])
        fig_no = stem_to_fig_no.get(stem)
        figure_ref = f"Obr. {fig_no}" if fig_no else "Obr. ?"
        script_display = script.replace("analyses/", "")

        # Merge dataset + filter info into one column.
        # Format per dataset: "DatasetCode (filter_string)" when filter available.
        filter_map: dict[str, str] = {}
        for f in meta["filters"]:
            # filters have format "datasetcode: filter_expr, ..."
            if ": " in f:
                ds_key, rest = f.split(": ", 1)
                filter_map[ds_key.strip()] = rest.strip()

        dataset_parts: list[str] = []
        for ds in meta["datasets"]:
            # ds is "Eurostat datasetcode" or "OECD datasetcode"
            parts = ds.split(None, 1)
            ds_code = parts[1] if len(parts) == 2 else ds
            filt = filter_map.get(ds_code, "")
            if filt:
                dataset_parts.append(f"{ds} ({filt})")
            else:
                dataset_parts.append(ds)
        datasets_filters_txt = "; ".join(dataset_parts) if dataset_parts else "Neuvedeno (sdilene helpery nebo staticka data)"

        # Build remarks: year audit note + stem-specific fallback branches.
        remarks_parts: list[str] = []
        if years:
            remarks_parts.append("Roky v popisku: " + ", ".join(str(y) for y in years))
        else:
            remarks_parts.append("Rok v popisku: neuvedeno")
        if audit_row.get("status") == "warning" and audit_row.get("message"):
            msg = audit_row["message"]
            # shorten common message
            if "do not include target year" in msg:
                remarks_parts.append(f"Nesedi cilovy rok {target_year}")
            elif "no year token" in msg:
                remarks_parts.append("Rok v popisku nenalezen")
            elif "no caption text" in msg:
                remarks_parts.append("Popisek nenalezen")
            else:
                remarks_parts.append(msg)
        stem_fallbacks = meta.get("fallbacks_by_stem", {}).get(stem, [])
        if stem_fallbacks:
            remarks_parts.append("Fallback vetve: " + "; ".join(stem_fallbacks))
        remarks_txt = " | ".join(remarks_parts)

        rows.append(
            {
                "stem": figure_ref,
                "script": script_display,
                "datasets": datasets_filters_txt,
                "remarks": remarks_txt,
            }
        )

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REVIEW_DIR / "data_quality_pipeline_table.json"
    tex_path = REVIEW_DIR / "data_quality_pipeline_table.tex"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    # Column layout (4 columns, widths sum to ~0.97\linewidth after \tabcolsep):
    #   Obr.    0.08  — figure reference number
    #   Skript  0.20  — analysis script filename (no analyses/ prefix)
    #   Dataset 0.38  — dataset codes + filters merged
    #   Pozn.   0.29  — remarks: years, audit warnings, fallback branches
    col_spec = "p{0.08\\linewidth}p{0.20\\linewidth}p{0.38\\linewidth}p{0.29\\linewidth}"
    hdr = "Obr. & Skript & Dataset(y) a filtry & Pozn\\'{a}mky (roky, fallback)"

    lines = [
        "% Auto-generated by python/stats_analytics.py. Do not edit manually.",
        "\\begingroup",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\renewcommand{\\arraystretch}{1.12}",
        "\\begin{longtable}{" + col_spec + "}",
        "\\caption{Metadata datov\\'{e} kvality -- v\\v{s}echny obr\\'{a}zky z main.tex (c\\'{i}lov\\'{y} rok " + str(target_year) + ").}\\\\",
        "\\hline",
        hdr + " \\\\",
        "\\hline",
        "\\endfirsthead",
        "\\hline",
        hdr + " \\\\",
        "\\hline",
        "\\endhead",
    ]

    for row in rows:
        lines.append(
            " & ".join(
                [
                    _latex_escape(row["stem"]),
                    _latex_escape(row["script"]),
                    _latex_escape(row["datasets"]),
                    _latex_escape(row["remarks"]),
                ]
            )
            + r" \\"
        )

    lines.extend([
        "\\hline",
        "\\end{longtable}",
        "\\endgroup",
        "",
    ])

    tex_path.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"[data-quality] pipeline table written: {tex_path.relative_to(DP_DIR)} "
        f"({len(rows)} rows)",
        flush=True,
    )


def _audit_target_year(referenced: set[str], *, target_year: int) -> list[dict]:
    """Warn for referenced outputs that don't clearly use target data year."""
    rows: list[dict] = []

    for stem in sorted(referenced):
        captions = _collect_caption_texts(stem)
        wrapper_defs = _collect_wrapper_string_defs(stem)
        years: list[int] = []
        for cap in captions:
            years.extend(_extract_years(cap))
        years_sorted = sorted(set(years))

        wrapper_years: list[int] = []
        wrapper_macro_hits: list[str] = []
        for macro, value in wrapper_defs:
            vals = _extract_years(value)
            if not vals:
                continue
            wrapper_years.extend(vals)
            if target_year not in vals:
                wrapper_macro_hits.append(macro)

        status = "ok"
        msg = ""
        if not captions:
            status = "warning"
            msg = "no caption text found for year audit"
            print(
                f"[data-quality][WARNING][missing_caption] {stem}: {msg}",
                flush=True,
            )
        elif not years_sorted:
            status = "warning"
            msg = "caption found but no year token detected"
            print(
                f"[data-quality][WARNING][missing_year] {stem}: {msg}",
                flush=True,
            )
        elif target_year not in years_sorted:
            status = "warning"
            msg = f"caption years {years_sorted} do not include target year {target_year}"
            print(
                f"[data-quality][WARNING][year_mismatch] {stem}: {msg}",
                flush=True,
            )
        elif wrapper_macro_hits:
            status = "warning"
            msg = (
                f"wrapper string macros {wrapper_macro_hits} do not include target year {target_year}"
            )
            print(
                f"[data-quality][WARNING][year_mismatch] {stem}: {msg}",
                flush=True,
            )

        rows.append(
            {
                "stem": stem,
                "status": status,
                "target_year": target_year,
                "years": years_sorted,
                "wrapper_years": sorted(set(wrapper_years)),
                "message": msg,
            }
        )

    # Persist report for transparent citation in prose/review workflow.
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REVIEW_DIR / "data_quality_report.json"
    md_path = REVIEW_DIR / "data_quality_report.md"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    ok_count = sum(1 for r in rows if r["status"] == "ok")
    warn_count = len(rows) - ok_count
    lines = [
        "# Data Quality Report",
        "",
        f"Target year: {target_year}",
        f"Referenced stems audited: {len(rows)}",
        f"OK: {ok_count}",
        f"Warnings: {warn_count}",
        "",
        "| Stem | Status | Years | Message |",
        "|---|---|---|---|",
    ]
    for row in rows:
        years_txt = ", ".join(str(y) for y in row["years"]) if row["years"] else "-"
        msg = row["message"] or "-"
        lines.append(f"| {row['stem']} | {row['status']} | {years_txt} | {msg} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        f"[data-quality] target-year audit complete: {ok_count} ok, {warn_count} warning(s). "
        f"Report: {md_path.relative_to(DP_DIR)}",
        flush=True,
    )
    return rows


def _sync_strings_from_tex(referenced: set[str]) -> None:
    """Sync editable figure-wrapper strings back into matching Python analyses."""
    from tools.sync_strings_from_tex import sync_script

    fig_stems = sorted(stem for stem in referenced if (FIG_TEX_DIR / f"{stem}.tex").exists())
    if not fig_stems:
        return

    changed: list[str] = []
    for stem in fig_stems:
        tex_file = FIG_TEX_DIR / f"{stem}.tex"
        lines = sync_script(tex_file, dry_run=False)
        if any(line.startswith("  CHANGED ") for line in lines):
            changed.append(stem)
        for line in lines:
            print(f"[tex-sync] {line}", flush=True)

    if changed:
        print(
            f"[tex-sync] synced {len(changed)} wrapper(s) back into Python: {', '.join(changed)}",
            flush=True,
        )
    else:
        print("[tex-sync] no Python source changes needed from editable figure wrappers.", flush=True)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    valid_keys = list(REGISTRY.keys())

    parser = argparse.ArgumentParser(
        description="Generate Python-produced figures/texparts referenced in the LaTeX project.",
    )
    parser.add_argument(
        "--target-year",
        type=int,
        default=int(os.environ.get("DP_TARGET_YEAR", "2025")),
        help="Target year for data-quality checks (default: 2025).",
    )
    parser.add_argument(
        "--force",
        metavar="KEY",
        help=(
            "Force regeneration of KEY even when all outputs exist.  "
            "KEY is one of: " + ", ".join(valid_keys) + ", all."
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print referenced texparts found in the LaTeX project and exit.",
    )
    args = parser.parse_args()

    # Discover which python texparts are referenced in the .tex project
    main_tex   = LATEX_DIR / "main.tex"
    referenced = _tex_stems(main_tex)

    _run_fallback_for_uncovered(referenced, target_year=args.target_year)

    if args.list:
        print("Referenced texparts/python/ stems:")
        for s in sorted(referenced):
            print(f"  {s}")
        return

    forced: set[str] = set()
    if args.force:
        if args.force == "all":
            forced = set(valid_keys)
        elif args.force in REGISTRY:
            forced = {args.force}
        else:
            parser.error(f"Unknown key '{args.force}'. Valid keys: {', '.join(valid_keys)}, all.")

    ran_any = False
    for key, entry in REGISTRY.items():
        # Is this entry referenced in the .tex project?
        active = any(
            fnmatch.fnmatch(stem, pattern)
            for pattern in entry["texparts"]
            for stem in referenced
        )
        if not active:
            continue

        if key in forced or _any_missing(entry, referenced):
            _run(key, entry, target_year=args.target_year)
            ran_any = True

    if not ran_any:
        print("[stats_analytics] all outputs present — nothing to do.", flush=True)

    _sync_strings_from_tex(referenced)
    audit_rows = _audit_target_year(referenced, target_year=args.target_year)
    _write_pipeline_quality_table(referenced, audit_rows, target_year=args.target_year)


if __name__ == "__main__":
    main()
