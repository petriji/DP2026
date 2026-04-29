r"""
sync_strings_from_tex.py
========================
Reads every latex/texparts/figures/<name>.tex and syncs the string
definitions back into the matching python/analyses/<name>.py.

Syncs:
  \def\strXxxCaption{...}     → caption= arg in save_figure_tex_pgf()
  \def\strXxxTitle{...}       → STRINGS["title"] (inline dict)
  \def\strXxxColorbarLabel{}  → STRINGS["colorbar_label"] (inline dict)
  + other common keys

Design rules:
  1. The tex \def caption = BARE_CAPTION. Zdroj dat: <cite>.
     We strip ". Zdroj dat: ..." to recover the bare caption.
  2. Backslash escaping:
     tex file has \acs{geo-CZ}   (single backslash, single braces)
     Python source must have \\acs{{geo-CZ}} inside an f-string literal,
     or \\acs{geo-CZ} inside a raw/plain string.
  3. Year expression preservation:
     If the Python source already uses a year variable (ds.latest_year etc.)
     where the tex has a literal year, treat them as equivalent → no change.
     Only replace a literal year in the Python source when the tex also has
     a literal year AND the text structure otherwise differs.
  4. The file is only written if a real change is needed.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_TEX_DIR = ROOT / "latex" / "texparts" / "figures"
ANALYSES_DIR = ROOT / "python" / "analyses"

YEAR_EXPR_PATTERNS = [
    r"\bds\.latest_year\b",
    r"\bds_all\.years\[-1\]\b",
    r"\blatest_year\b",
    r"\blast_year\b",
    r"\bYEAR\b",
    r"\bref_year\b",
    r"\bdisplay_year\b",
    r"\byear_range\b",   # covers things like "2007--2025"
    r"\bISPV_YEAR\b",
]
YEAR_EXPR_RE = "|".join(YEAR_EXPR_PATTERNS)


# ──────────────────────────────────────────────────────────────────────────────
# String normalization helpers
# ──────────────────────────────────────────────────────────────────────────────

def camel_to_snake(name: str) -> str:
    s1 = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    return s1.lower()


def parse_tex_defs(tex_text: str) -> dict[str, str]:
    """Return {MacroSuffix: value} for every \\def\\strXxx{...}% in tex_text."""
    results = {}
    for m in re.finditer(
        r"\\def\\str([A-Za-z]+)\{((?:[^{}]|\{[^{}]*\})*)\}%?", tex_text
    ):
        results[m.group(1)] = m.group(2)
    return results


def strip_zdroj_dat(caption_full: str) -> str:
    """Remove '. Zdroj dat: ...' suffix from the full caption string."""
    m = re.search(r"\.\s*Zdroj dat:.*$", caption_full, re.DOTALL)
    bare = caption_full[: m.start()] if m else caption_full
    return bare.rstrip(". \t\n")


def tex_to_py_source(tex_val: str, *, fstring: bool = True) -> str:
    """Convert a tex string value to the Python source literal content.

    tex_val has single backslashes and single braces.
    In a Python f-string literal:
      \\  → \\ (already one backslash in source → two chars \\ in file)
      {   → {{  (escape for f-string)
      }   → }}
    But if NOT an f-string (plain string):
      \\  → \\
      {   → {   (no escaping needed)
    """
    # Escape backslash first
    result = tex_val.replace("\\", "\\\\")
    if fstring:
        result = result.replace("{", "{{").replace("}", "}}")
    return result


def py_source_to_actual(py_src: str, *, fstring: bool = True) -> str:
    """Reverse of tex_to_py_source: unescape Python source → actual string value."""
    if fstring:
        # un-double braces (but not expression braces – approximate)
        result = py_src.replace("{{", "{").replace("}}", "}")
    else:
        result = py_src
    result = result.replace("\\\\", "\\")
    return result


def normalize_years(value: str) -> str:
    """Replace year literals and f-string year expressions with __Y__ for comparison.

    Treats all of these as equivalent:
      2024  {ds.latest_year}  {last_year}  {START_YEAR}  {year_range}  2004--2024
    """
    result = value
    # 1. Year expressions inside braces (f-string expressions containing "year"/"YEAR")
    #    Matches {anything_with_year_word} but NOT {\LaTeX_macro}
    result = re.sub(
        r"\{[^{}\\]*(?:[Yy][Ee][Aa][Rr][Ss]?)[^{}\\]*\}",
        "__Y__",
        result,
    )
    # 2. Literal year ranges:  YYYY--YYYY  (both 20xx and 19xx)
    result = re.sub(
        r"(?<![/_A-Za-z0-9])((?:20|19)\d{2})\s*--\s*(?:(?:20|19)\d{2}|__Y__)",
        "__Y__--__Y__",
        result,
    )
    # 3. Standalone literal years (20xx)
    result = re.sub(r"(?<![/_A-Za-z0-9])(20\d{2})(?![/_A-Za-z0-9])", "__Y__", result)
    # 4. Collapse __Y__--__Y__ to single placeholder for comparison
    result = re.sub(r"__Y__\s*--\s*__Y__", "__Y__", result)
    return result


def has_year_expr(py_src: str) -> bool:
    """True if the Python source string contains any f-string year expression.

    Matches any {braced_content} where content (no nested braces, no backslash)
    contains the word 'year' or 'YEAR'.  This is the same pattern used in
    normalize_years to collapse year expressions to __Y__.
    """
    return bool(re.search(r"\{[^{}\\]*(?:[Yy][Ee][Aa][Rr][Ss]?)[^{}\\]*\}", py_src))

def is_fstring_source(py_src: str) -> bool:
    """True if the Python source looks like an f-string literal.

    Either it has a year-variable expression {expr_with_year}, OR it has
    doubled-brace LaTeX-argument escaping {{...}} which is the f-string
    idiom for literal braces in a format string.
    """
    return has_year_expr(py_src) or bool(re.search(r"\{\{", py_src))


def detect_year_exprs_in_py(py_text: str) -> list[str]:
    """Return list of year variable expressions present in the Python file."""
    found = []
    for pat in YEAR_EXPR_PATTERNS:
        if re.search(pat, py_text):
            # Extract the expression name from pattern (strip boundary anchors)
            expr = pat.lstrip(r"\b").rstrip(r"\b").replace(r"\.", ".").replace(r"\[", "[").replace(r"\]", "]").replace(r"\-", "-")
            found.append(expr)
    return found


# ──────────────────────────────────────────────────────────────────────────────
# Caption comparison logic
# ──────────────────────────────────────────────────────────────────────────────

def captions_equivalent(py_cap_src: str, tex_bare: str, py_text: str) -> bool:
    """Return True if the Python caption source and tex bare caption are equivalent.

    Equivalent means:
      - Same content after normalizing backslash escaping
      - Year literals vs year variables in the same positions are treated equal
    """
    # Determine if the Python string is an f-string
    is_f = is_fstring_source(py_cap_src)
    # Get actual runtime value from Python source (approximate)
    py_actual = py_source_to_actual(py_cap_src, fstring=is_f)
    # Compare with year normalization
    return normalize_years(py_actual.strip(". \t\n")) == normalize_years(tex_bare.strip(". \t\n"))


def build_new_caption_src(tex_bare: str, py_text: str) -> tuple[str, bool]:
    """Build the new Python source string for caption= argument.

    Returns (new_source_content, is_fstring).
    Replaces year literals in tex_bare with year expressions found in py_text.
    """
    # Find year expressions used in the Python file
    year_exprs = detect_year_exprs_in_py(py_text)

    result = tex_bare
    is_f = False

    if year_exprs:
        # Replace year literals with the primary year expression
        # For end-year in ranges (--XXXX), use the primary year expr
        # For start-year in ranges, keep as literal
        primary_expr = year_exprs[0]
        # Find all year literals in the caption
        years_in_tex = re.findall(r"(?<![/_A-Za-z0-9])(20\d{2})(?![/_A-Za-z0-9])", tex_bare)
        if years_in_tex:
            last_year = sorted(set(years_in_tex))[-1]
            # Replace only the LAST/largest year with the expression
            result = re.sub(
                r"(?<![/_A-Za-z0-9])" + re.escape(last_year) + r"(?![/_A-Za-z0-9])",
                "{" + primary_expr + "}",
                result,
                count=1
            )
            # If the replacement left a range like "2004--{expr}", that's fine.

    # Check if result needs f-string (has {expr})
    is_f = bool(re.search(r"\{[a-z_A-Z]", result))

    # Convert to Python source escaping
    # Escape backslashes first
    src = result.replace("\\", "\\\\")
    if is_f:
        # Escape braces that are NOT part of a year expression
        # Strategy: escape ALL { and } then un-escape the {expr} ones
        # First escape all braces
        src_escaped = src.replace("{", "{{").replace("}", "}}")
        # Un-escape the year expression braces: {{expr}} → {expr}
        for year_expr in year_exprs:
            escaped_expr = year_expr.replace(".", r"\.").replace("[", r"\[").replace("]", r"\]")
            src_escaped = re.sub(
                r"\{\{" + escaped_expr + r"\}\}",
                "{" + year_expr + "}",
                src_escaped
            )
        src = src_escaped

    return src, is_f


# ──────────────────────────────────────────────────────────────────────────────
# STRINGS key comparison logic
# ──────────────────────────────────────────────────────────────────────────────

def extract_inline_string(py_text: str, key: str) -> tuple[str | None, str | None, bool]:
    """Find inline dict entry 'key': f"..." or 'key': "..." in py_text.

    Returns (full_match, string_content, is_fstring) or (None, None, False).
    The full_match includes 'key': "content".
    string_content is the raw source between the quotes.
    """
    pat = re.compile(
        r'(["\']' + re.escape(key) + r'["\']'
        r'\s*:\s*)'
        r'((?:f?)(?:"[^"]*"|\'[^\']*\'))',
    )
    m = pat.search(py_text)
    if not m:
        return None, None, False
    full = m.group(0)
    val_part = m.group(2)
    is_f = val_part.startswith("f")
    content_m = re.search(r'["\'](.+?)["\']', val_part)
    if not content_m:
        return None, None, False
    return full, content_m.group(1), is_f


def strings_equivalent(py_src: str, tex_val: str, py_text: str, is_fstring: bool) -> bool:
    """Check if STRINGS[key] source and tex value are equivalent."""
    py_actual = py_source_to_actual(py_src, fstring=is_fstring)
    return normalize_years(py_actual.strip()) == normalize_years(tex_val.strip())


def build_new_strings_src(tex_val: str, py_text: str) -> tuple[str, bool]:
    """Build new Python source string for a STRINGS dict value."""
    year_exprs = detect_year_exprs_in_py(py_text)
    result = tex_val
    is_f = False
    if year_exprs:
        years_in_tex = re.findall(r"(?<![/_A-Za-z0-9])(20\d{2})(?![/_A-Za-z0-9])", tex_val)
        if years_in_tex:
            primary_expr = year_exprs[0]
            last_year = sorted(set(years_in_tex))[-1]
            result = re.sub(
                r"(?<![/_A-Za-z0-9])" + re.escape(last_year) + r"(?![/_A-Za-z0-9])",
                "{" + primary_expr + "}",
                result, count=1
            )
    is_f = bool(re.search(r"\{[a-z_A-Z]", result))
    src = result.replace("\\", "\\\\")
    if is_f:
        src_e = src.replace("{", "{{").replace("}", "}}")
        for year_expr in year_exprs:
            escaped_expr = year_expr.replace(".", r"\.").replace("[", r"\[").replace("]", r"\]")
            src_e = re.sub(r"\{\{" + escaped_expr + r"\}\}", "{" + year_expr + "}", src_e)
        src = src_e
    return src, is_f


# ──────────────────────────────────────────────────────────────────────────────
# Per-script sync
# ──────────────────────────────────────────────────────────────────────────────

def sync_script(tex_file: Path, dry_run: bool = False) -> list[str]:
    stem = tex_file.stem
    py_file = ANALYSES_DIR / f"{stem}.py"
    if not py_file.exists():
        return [f"  SKIP {stem}: no matching Python script"]

    tex_text = tex_file.read_text(encoding="utf-8")
    py_text = py_file.read_text(encoding="utf-8")

    defs = parse_tex_defs(tex_text)
    if not defs:
        return [f"  SKIP {stem}: no \\def\\str macros found"]

    # Detect macro prefix (e.g. EuHustotaMapa from EuHustotaMapaCaption)
    KEY_SUFFIXES = ["Caption", "Title", "ColorbarLabel", "Ylabel", "Xlabel",
                    "Note", "Subtitle", "Label", "Name"]
    prefix = None
    for key in defs:
        for suf in KEY_SUFFIXES:
            if key.endswith(suf):
                prefix = key[: -len(suf)]
                break
        if prefix:
            break
    if prefix is None:
        first_key = next(iter(defs))
        m = re.match(r"(.+?)([A-Z][a-z]+)$", first_key)
        prefix = m.group(1) if m else first_key

    changes: list[str] = []
    new_py_text = py_text

    # ── Caption ──────────────────────────────────────────────────────────────
    caption_key = prefix + "Caption"
    if caption_key in defs:
        tex_caption_full = defs[caption_key]
        tex_bare = strip_zdroj_dat(tex_caption_full)

        # Find caption= in Python
        cap_pat = re.compile(
            r'(caption\s*=\s*)'
            r'(\('
            r'(?:\s*(?:f?)(?:"[^"]*"|\'[^\']*\'))+'   # one or more strings
            r'\s*\)'
            r'|'
            r'(?:f?)(?:"[^"]*"|\'[^\']*\')'
            r')',
            re.DOTALL,
        )
        m = cap_pat.search(new_py_text)
        if m:
            old_cap_arg = m.group(0)
            # Extract the string content(s) from the old arg
            old_strings = re.findall(r'(?:f?)(["\'])([^\1]*?)\1', old_cap_arg, re.DOTALL)
            # Combine multi-part string into one value (approximate)
            old_src = "".join(s[1] for s in old_strings) if old_strings else ""

            # Check equivalence
            if not captions_equivalent(old_src, tex_bare, py_text):
                new_src, is_f = build_new_caption_src(tex_bare, py_text)
                q = 'f"' if is_f else '"'
                new_cap_arg = f'caption={q}{new_src}"'
                new_py_text = new_py_text.replace(old_cap_arg, new_cap_arg, 1)
                # Show clean diff
                old_display = py_source_to_actual(old_src, fstring=has_year_expr(old_src))
                new_display = tex_bare
                changes.append(f"  caption:\n    was: {old_display!r}\n    now: {new_display!r}")

    # ── STRINGS inline dict keys ──────────────────────────────────────────────
    key_map = {
        prefix + "Title": "title",
        prefix + "ColorbarLabel": "colorbar_label",
        prefix + "Ylabel": "ylabel",
        prefix + "Xlabel": "xlabel",
        prefix + "Note": "note",
        prefix + "Subtitle": "subtitle",
    }
    for macro_key, strings_key in key_map.items():
        if macro_key not in defs:
            continue
        tex_val = defs[macro_key]
        full_match, old_src, is_f = extract_inline_string(new_py_text, strings_key)
        if full_match is None or old_src is None:
            continue
        if strings_equivalent(old_src, tex_val, py_text, is_fstring=is_f):
            continue
        new_src, new_is_f = build_new_strings_src(tex_val, py_text)
        q = 'f"' if new_is_f else '"'
        # Reconstruct the full match with new value
        key_part_m = re.search(
            r'(["\']' + re.escape(strings_key) + r'["\']' + r'\s*:\s*)',
            full_match
        )
        if key_part_m:
            new_full = key_part_m.group(1) + f'{q}{new_src}"'
            new_py_text = new_py_text.replace(full_match, new_full, 1)
            if new_full == full_match:
                continue  # no-op: skip reporting
            old_display = py_source_to_actual(old_src, fstring=is_f)
            new_display = py_source_to_actual(new_src, fstring=new_is_f)
            changes.append(f"  STRINGS[{strings_key!r}]:\n    was: {old_display!r}\n    now: {new_display!r}")

    if not changes:
        return [f"  OK   {stem}: no changes needed"]

    if not dry_run:
        py_file.write_text(new_py_text, encoding="utf-8")

    result = [f"  CHANGED {stem} ({len(changes)} update(s)):"]
    result.extend(changes)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv
    mode = "DRY RUN — no files will be written" if dry_run else "LIVE RUN — Python scripts will be updated"
    print(f"{mode}\n")

    tex_files = sorted(FIGURES_TEX_DIR.glob("*.tex"))
    print(f"Found {len(tex_files)} figure tex files\n")

    all_changed: list[str] = []
    all_ok: list[str] = []
    all_skip: list[str] = []

    for tex_file in tex_files:
        lines = sync_script(tex_file, dry_run=dry_run)
        is_changed = any("CHANGED" in l for l in lines)
        is_skip = any("SKIP" in l for l in lines)
        if is_changed:
            all_changed.append(tex_file.stem)
            for l in lines:
                print(l)
        elif is_skip:
            all_skip.append(tex_file.stem)
        else:
            all_ok.append(tex_file.stem)

    print(f"\n{'='*60}")
    print(f"Changed : {len(all_changed)}")
    print(f"OK (no change needed): {len(all_ok)}")
    print(f"Skipped (no py script): {len(all_skip)}")
    if all_changed:
        print("Changed files:", all_changed)


if __name__ == "__main__":
    main()
