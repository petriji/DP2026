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
_CAPTION_RE = re.compile(r'\\caption(?:\[[^\]]*\])?\{(.+?)\}', re.DOTALL)
_DEF_CAPTION_RE = re.compile(r'\\def\\[A-Za-z0-9_]*Caption\{(.+?)\}\s*%?', re.DOTALL)
_YEAR_RE = re.compile(r'\b(?:19|20)\d{2}\b')

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
        texts.extend(_CAPTION_RE.findall(body))
        texts.extend(_DEF_CAPTION_RE.findall(body))
    return [t.strip() for t in texts if t.strip()]


def _extract_years(text: str) -> list[int]:
    return [int(y) for y in _YEAR_RE.findall(text)]


def _audit_target_year(referenced: set[str], *, target_year: int) -> None:
    """Warn for referenced outputs that don't clearly use target data year."""
    rows: list[dict] = []

    for stem in sorted(referenced):
        captions = _collect_caption_texts(stem)
        years: list[int] = []
        for cap in captions:
            years.extend(_extract_years(cap))
        years_sorted = sorted(set(years))

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

        rows.append(
            {
                "stem": stem,
                "status": status,
                "target_year": target_year,
                "years": years_sorted,
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

    _audit_target_year(referenced, target_year=args.target_year)


if __name__ == "__main__":
    main()
