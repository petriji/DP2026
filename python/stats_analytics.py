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
import re
import subprocess
import sys
import tomllib
from pathlib import Path

PYTHON_DIR  = Path(__file__).parent.resolve()
DP_DIR      = PYTHON_DIR.parent
LATEX_DIR   = DP_DIR / "latex"
PICS_DIR    = DP_DIR / "pics" / "python"
TEX_DIR     = LATEX_DIR / "texparts" / "python"

# ── Registry ──────────────────────────────────────────────────────────────────
# Loaded from registry.toml (same directory as this script).
# See that file for the schema and instructions for adding new analysis scripts.

with open(PYTHON_DIR / "analytics_registry.toml", "rb") as _f:
    REGISTRY: dict[str, dict] = tomllib.load(_f)

# ── LaTeX project scanner ─────────────────────────────────────────────────────

_INPUT_RE   = re.compile(r'\\(?:input|include)\{([^}]+)\}')
_PGF_RE     = re.compile(r'\\inputpgffigure\{([^}]+)\}')
_COMMENT_RE = re.compile(r'%.*')

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
                # Recurse into other \input{} calls
                candidate = (base / arg).with_suffix(".tex") if not arg.endswith(".tex") \
                            else base / arg
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

    # Check pic PDF files
    for pattern in entry.get("pics", []):
        matching = [s for s in referenced
                    if fnmatch.fnmatch(s, pattern.replace("_map_*", "_map_*"))]
        # For pic patterns derived from texpart stems:
        # re-resolve against referenced stems
        matched_stems = [s for s in referenced if fnmatch.fnmatch(s, pattern)]
        for stem in matched_stems:
            if not (PICS_DIR / f"{stem}.pdf").exists():
                return True
        if not matched_stems and "*" not in pattern and pattern in referenced:
            if not (PICS_DIR / f"{pattern}.pdf").exists():
                return True

    return False


# ── Runner ────────────────────────────────────────────────────────────────────

def _run(key: str, entry: dict) -> None:
    script = entry["script"]
    print(f"[stats_analytics] running: {script}", flush=True)
    result = subprocess.run([sys.executable, script], cwd=PYTHON_DIR)
    if result.returncode != 0:
        print(
            f"[stats_analytics] ERROR: {script} exited with code {result.returncode}",
            flush=True,
        )
        sys.exit(result.returncode)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    valid_keys = list(REGISTRY.keys())

    parser = argparse.ArgumentParser(
        description="Generate Python-produced figures/texparts referenced in the LaTeX project.",
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
            _run(key, entry)
            ran_any = True

    if not ran_any:
        print("[stats_analytics] all outputs present — nothing to do.", flush=True)


if __name__ == "__main__":
    main()
