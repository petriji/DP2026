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

import fnmatch
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_TEX_DIR = ROOT / "latex" / "texparts" / "figures"
ANALYSES_DIR = ROOT / "python" / "analyses"
REGISTRY_PATH = ROOT / "python" / "analytics_registry.toml"

with REGISTRY_PATH.open("rb") as f:
    REGISTRY: dict[str, dict[str, object]] = tomllib.load(f)

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


def _normalize_compare(value: str) -> str:
    """Normalization for safe equivalence checks.

    Besides year masking, collapse cosmetic wrappers around years
    (e.g. '(2024)' vs '2024') to avoid noisy sync churn.
    """
    result = normalize_years(value)
    result = re.sub(r"\(\s*__Y__\s*\)", "__Y__", result)
    result = re.sub(r"\s+", " ", result)
    return result.strip(" .\t\n")


def _has_literal_year(value: str) -> bool:
    return bool(re.search(r"(?<![/_A-Za-z0-9])(20\d{2})(?![/_A-Za-z0-9])", value))


def has_year_expr(py_src: str) -> bool:
    """True if the Python source string contains any f-string year expression.

    Matches any {braced_content} where content (no nested braces, no backslash)
    contains the word 'year' or 'YEAR'.  This is the same pattern used in
    normalize_years to collapse year expressions to __Y__.
    """
    return bool(re.search(r"\{[^{}\\]*(?:[Yy][Ee][Aa][Rr][Ss]?)[^{}\\]*\}", py_src))


def has_programmatic_expr(py_src: str) -> bool:
    """True if source contains a non-escaped f-string expression like {expr}."""
    return bool(re.search(r"(?<!\{)\{[A-Za-z_][^{}]*\}(?!\})", py_src))

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
    return _normalize_compare(py_actual) == _normalize_compare(tex_bare)


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
    return _normalize_compare(py_actual) == _normalize_compare(tex_val)


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


def _find_call_bounds(py_text: str, func_name: str) -> list[tuple[int, int]]:
    """Return [(start, end), ...] spans for function calls with balanced parens."""
    bounds: list[tuple[int, int]] = []
    token = f"{func_name}("
    pos = 0
    while True:
        start = py_text.find(token, pos)
        if start == -1:
            break
        i = start + len(token)
        depth = 1
        in_str: str | None = None
        escaped = False
        while i < len(py_text):
            ch = py_text[i]
            if in_str is not None:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == in_str:
                    in_str = None
            else:
                if ch in ('"', "'"):
                    in_str = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        bounds.append((start, i + 1))
                        break
            i += 1
        pos = start + len(token)
    return bounds


def _extract_name_string_assignments(py_text: str) -> tuple[dict[str, str], dict[str, str]]:
    """Extract simple NAME='literal' and NAME=f'template{...}' assignments."""
    literals: dict[str, str] = {}
    templates: dict[str, str] = {}
    pat = re.compile(
        r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(f?)([\"\'])(.*?)\3\s*$",
        re.MULTILINE,
    )
    for m in pat.finditer(py_text):
        name, is_f, _, val = m.groups()
        if is_f:
            templates[name] = val
        else:
            literals[name] = val
    return literals, templates


def _template_matches_stem(template: str, stem: str) -> bool:
    """Check if a simple f-string template can match a concrete stem."""
    # Replace each {expr} with a wildcard.
    regex = re.escape(template)
    regex = re.sub(r"\\\{[^{}]+\\\}", r".+", regex)
    return bool(re.fullmatch(regex, stem))


def _resolve_name_matches_stem(name: str, stem: str, literals: dict[str, str], templates: dict[str, str]) -> bool:
    if name in literals:
        return literals[name] == stem
    if name in templates:
        return _template_matches_stem(templates[name], stem)
    return False


def _call_matches_stem(call_src: str, func_name: str, stem: str, literals: dict[str, str], templates: dict[str, str]) -> bool:
    """Check if a function call source resolves to the requested stem."""
    if func_name == "save_figure_tex_pgf":
        m_pos_lit = re.search(r"save_figure_tex_pgf\(\s*([\"\'])([^\"\']+)\1", call_src)
        if m_pos_lit and m_pos_lit.group(2) == stem:
            return True

        m_pos_name = re.search(r"save_figure_tex_pgf\(\s*([A-Za-z_][A-Za-z0-9_]*)", call_src)
        if m_pos_name and _resolve_name_matches_stem(m_pos_name.group(1), stem, literals, templates):
            return True

    m_kw_lit = re.search(r"\bstem\s*=\s*([\"\'])([^\"\']+)\1", call_src)
    if m_kw_lit and m_kw_lit.group(2) == stem:
        return True

    m_kw_name = re.search(r"\bstem\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", call_src)
    if m_kw_name and _resolve_name_matches_stem(m_kw_name.group(1), stem, literals, templates):
        return True

    return False


def _find_target_call_for_stem(py_text: str, stem: str) -> tuple[int, int, str] | None:
    """Find a call block tied to *stem* and return (start, end, call_kind)."""
    literals, templates = _extract_name_string_assignments(py_text)
    for func_name in ["save_figure_tex_pgf", "_make_choropleth"]:
        for start, end in _find_call_bounds(py_text, func_name):
            call_src = py_text[start:end]
            if _call_matches_stem(call_src, func_name, stem, literals, templates):
                return start, end, func_name
    return None


def _extract_kw_string(call_src: str, kw_name: str) -> tuple[str | None, str | None, bool]:
    """Extract a keyword string argument from a call source.

    Returns (full_match, source_content, is_fstring).
    """
    pat = re.compile(
        r'(' + re.escape(kw_name) + r'\s*=\s*)'
        r'(\('
        r'(?:\s*(?:f?)(?:"[^"]*"|\'[^\']*\'))+'
        r'\s*\)'
        r'|'
        r'(?:f?)(?:"[^"]*"|\'[^\']*\')'
        r')',
        re.DOTALL,
    )
    m = pat.search(call_src)
    if not m:
        return None, None, False
    full = m.group(0)
    val = m.group(2)
    is_f = val.startswith("f") or val.startswith("(f")
    parts = re.findall(r'(?:f?)(["\'])([^\1]*?)\1', val, re.DOTALL)
    src = "".join(p[1] for p in parts) if parts else None
    return full, src, is_f


def _find_dict_assignment_bounds(py_text: str, var_name: str, before_pos: int) -> tuple[int, int] | None:
    """Find nearest preceding `var_name = {...}` block and return its bounds."""
    pat = re.compile(r"\b" + re.escape(var_name) + r"\s*=\s*\{")
    match = None
    for m in pat.finditer(py_text):
        if m.start() < before_pos:
            match = m
        else:
            break
    if match is None:
        return None

    open_brace = py_text.find("{", match.start())
    if open_brace == -1:
        return None

    i = open_brace + 1
    depth = 1
    in_str: str | None = None
    escaped = False
    while i < len(py_text):
        ch = py_text[i]
        if in_str is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_str:
                in_str = None
        else:
            if ch in ('"', "'"):
                in_str = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return match.start(), i + 1
        i += 1
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Per-script sync
# ──────────────────────────────────────────────────────────────────────────────

def sync_script(tex_file: Path, dry_run: bool = False) -> list[str]:
    stem = tex_file.stem
    py_file = ANALYSES_DIR / f"{stem}.py"
    if not py_file.exists():
        registry_scripts = {
            Path(str(entry["script"])).name
            for entry in REGISTRY.values()
            if any(fnmatch.fnmatch(stem, pattern) for pattern in entry.get("texparts", []))
        }
        if len(registry_scripts) == 1:
            py_file = ANALYSES_DIR / next(iter(registry_scripts))
        elif len(registry_scripts) > 1:
            return [
                f"  SKIP {stem}: multiple registry scripts match ({', '.join(sorted(registry_scripts))})"
            ]
        else:
            return [f"  SKIP {stem}: no matching Python script (likely unregistered output)"]

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
    notes: list[str] = []
    new_py_text = py_text

    # Scope all updates to the specific save_figure_tex_pgf("<stem>", ...) call.
    target_call_bounds = _find_target_call_for_stem(new_py_text, stem)
    if target_call_bounds is None:
        return [f"  SKIP {stem}: no save_figure_tex_pgf call for this stem"]
    call_start, call_end, call_kind = target_call_bounds
    target_call_src = new_py_text[call_start:call_end]

    # ── Caption ──────────────────────────────────────────────────────────────
    caption_key = prefix + "Caption"
    if caption_key in defs:
        tex_caption_full = defs[caption_key]
        tex_bare = strip_zdroj_dat(tex_caption_full)

        # Find caption= only in the target figure call.
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
        m = cap_pat.search(target_call_src)
        if m:
            old_cap_arg = m.group(0)
            # Extract the string content(s) from the old arg
            old_strings = re.findall(r'(?:f?)(["\'])([^\1]*?)\1', old_cap_arg, re.DOTALL)
            # Combine multi-part string into one value (approximate)
            old_src = "".join(s[1] for s in old_strings) if old_strings else ""

            # Check equivalence
            if not captions_equivalent(old_src, tex_bare, py_text):
                # Do not overwrite programmatic expressions with literal-year text.
                if has_programmatic_expr(old_src) and _has_literal_year(tex_bare):
                    notes.append("  caption: skipped (programmatic expression in Python source)")
                else:
                    new_src, is_f = build_new_caption_src(tex_bare, py_text)
                    q = 'f"' if is_f else '"'
                    new_cap_arg = f'caption={q}{new_src}"'
                    target_call_src = target_call_src.replace(old_cap_arg, new_cap_arg, 1)
                    new_py_text = new_py_text[:call_start] + target_call_src + new_py_text[call_end:]
                    call_end = call_start + len(target_call_src)
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
    strings_var_m = re.search(r"\bstrings\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", target_call_src)
    strings_var = strings_var_m.group(1) if strings_var_m else None

    for macro_key, strings_key in key_map.items():
        if macro_key not in defs:
            continue
        tex_val = defs[macro_key]
        if strings_var:
            dict_bounds = _find_dict_assignment_bounds(new_py_text, strings_var, call_start)
            if dict_bounds is None:
                continue
            dict_start, dict_end = dict_bounds
            dict_src = new_py_text[dict_start:dict_end]

            if len(re.findall(r'["\']' + re.escape(strings_key) + r'["\']\s*:', dict_src)) != 1:
                continue

            full_match, old_src, is_f = extract_inline_string(dict_src, strings_key)
            if full_match is None or old_src is None:
                continue
            if strings_equivalent(old_src, tex_val, py_text, is_fstring=is_f):
                continue
            if has_programmatic_expr(old_src) and _has_literal_year(tex_val):
                notes.append(f"  STRINGS[{strings_key!r}]: skipped (programmatic expression in Python source)")
                continue
            new_src, new_is_f = build_new_strings_src(tex_val, py_text)
            q = 'f"' if new_is_f else '"'
            key_part_m = re.search(
                r'(["\']' + re.escape(strings_key) + r'["\']' + r'\s*:\s*)',
                full_match
            )
            if key_part_m:
                new_full = key_part_m.group(1) + f'{q}{new_src}"'
                new_dict_src = dict_src.replace(full_match, new_full, 1)
                new_py_text = new_py_text[:dict_start] + new_dict_src + new_py_text[dict_end:]
                delta = len(new_dict_src) - len(dict_src)
                if dict_start < call_start:
                    call_start += delta
                    call_end += delta
                target_call_src = new_py_text[call_start:call_end]
                if new_full == full_match:
                    continue
                old_display = py_source_to_actual(old_src, fstring=is_f)
                new_display = py_source_to_actual(new_src, fstring=new_is_f)
                changes.append(f"  STRINGS[{strings_key!r}]:\n    was: {old_display!r}\n    now: {new_display!r}")
        elif call_kind == "_make_choropleth":
            helper_kw_map = {
                "title": "title",
                "colorbar_label": "cbar_label",
            }
            helper_kw = helper_kw_map.get(strings_key)
            if not helper_kw:
                continue
            full_match, old_src, is_f = _extract_kw_string(target_call_src, helper_kw)
            if full_match is None or old_src is None:
                continue
            if strings_equivalent(old_src, tex_val, py_text, is_fstring=is_f):
                continue
            if has_programmatic_expr(old_src) and _has_literal_year(tex_val):
                notes.append(f"  {helper_kw}: skipped (programmatic expression in Python source)")
                continue
            new_src, new_is_f = build_new_strings_src(tex_val, py_text)
            q = 'f"' if new_is_f else '"'
            key_part_m = re.search(r'(' + re.escape(helper_kw) + r'\s*=\s*)', full_match)
            if not key_part_m:
                continue
            new_full = key_part_m.group(1) + f'{q}{new_src}"'
            target_call_src = target_call_src.replace(full_match, new_full, 1)
            new_py_text = new_py_text[:call_start] + target_call_src + new_py_text[call_end:]
            call_end = call_start + len(target_call_src)
            old_display = py_source_to_actual(old_src, fstring=is_f)
            new_display = py_source_to_actual(new_src, fstring=new_is_f)
            changes.append(f"  {helper_kw}:\n    was: {old_display!r}\n    now: {new_display!r}")

    if not changes:
        result = [f"  OK   {stem}: no changes needed"]
        result.extend(notes)
        return result

    if not dry_run:
        py_file.write_text(new_py_text, encoding="utf-8")

    result = [f"  CHANGED {stem} ({len(changes)} update(s)):"]
    result.extend(changes)
    result.extend(notes)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    apply_mode = "--apply" in args
    dry_run = not apply_mode
    targets = [a for a in args if not a.startswith("--")]

    mode = "DRY RUN — no files will be written" if dry_run else "LIVE RUN — Python scripts will be updated"
    print(f"{mode}\n")

    tex_files = sorted(FIGURES_TEX_DIR.glob("*.tex"))
    if targets:
        target_set = set(targets)
        tex_files = [
            p for p in tex_files
            if p.stem in target_set or p.name in target_set or str(p.relative_to(ROOT)) in target_set
        ]
    print(f"Found {len(tex_files)} figure tex files\n")

    all_changed: list[str] = []
    all_ok: list[str] = []
    all_skip_no_script: list[str] = []
    all_skip_no_stem: list[str] = []
    all_skip_other: list[str] = []

    for tex_file in tex_files:
        lines = sync_script(tex_file, dry_run=dry_run)
        is_changed = any("CHANGED" in l for l in lines)
        is_skip = any("SKIP" in l for l in lines)
        if is_changed:
            all_changed.append(tex_file.stem)
            for l in lines:
                print(l)
        elif is_skip:
            head = lines[0] if lines else ""
            if "no matching Python script" in head:
                all_skip_no_script.append(tex_file.stem)
            elif "no save_figure_tex_pgf call for this stem" in head:
                all_skip_no_stem.append(tex_file.stem)
            else:
                all_skip_other.append(tex_file.stem)
        else:
            all_ok.append(tex_file.stem)

    print(f"\n{'='*60}")
    print(f"Changed : {len(all_changed)}")
    print(f"OK (no change needed): {len(all_ok)}")
    print(f"Skipped (no matching script / unregistered): {len(all_skip_no_script)}")
    print(f"Skipped (no matched stem call): {len(all_skip_no_stem)}")
    print(f"Skipped (other): {len(all_skip_other)}")
    if all_changed:
        print("Changed files:", all_changed)


if __name__ == "__main__":
    main()
