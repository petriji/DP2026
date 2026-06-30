"""Data-quality helpers for analysis scripts and pipeline checks.

This module standardises warning messages for:
- fallback paths (secondary source, hardcoded defaults, expert imputations),
- target-year mismatches (default target year: 2025),
- machine-readable reporting for audit transparency.
"""

from __future__ import annotations

import json
import os
import inspect
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def target_year() -> int:
    """Return configured target data year (defaults to 2025)."""
    raw = os.environ.get("DP_TARGET_YEAR", "2025")
    try:
        return int(raw)
    except ValueError:
        return 2025


@dataclass
class QualityWarning:
    kind: str
    script: str
    message: str
    source: str | None = None
    year: int | None = None
    expected_year: int | None = None
    hardcoded: bool = False
    fallback: bool = False
    line: int | None = None
    timestamp_utc: str = ""


_WARNINGS: list[QualityWarning] = []


def _external_caller_line() -> int | None:
    """Return first callsite line outside this module (best effort)."""
    this_file = Path(__file__).resolve()
    frame = inspect.currentframe()
    if frame is None:
        return None
    try:
        f = frame.f_back
        while f is not None:
            code = f.f_code
            filename = Path(code.co_filename).resolve()
            if filename != this_file:
                return int(f.f_lineno)
            f = f.f_back
    finally:
        del frame
    return None


def _script_name() -> str:
    import sys

    if not sys.argv:
        return "<interactive>"
    try:
        return Path(sys.argv[0]).name
    except Exception:
        return str(sys.argv[0])


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def warn(kind: str, message: str, *, source: str | None = None, year: int | None = None,
         expected_year: int | None = None, hardcoded: bool = False, fallback: bool = False) -> None:
    """Emit a standard data-quality warning and keep it for summary output."""
    rec = QualityWarning(
        kind=kind,
        script=_script_name(),
        message=message,
        source=source,
        year=year,
        expected_year=expected_year,
        hardcoded=hardcoded,
        fallback=fallback,
        line=_external_caller_line(),
        timestamp_utc=_now_utc(),
    )
    _WARNINGS.append(rec)

    header = f"[data-quality][WARNING][{kind}]"
    if hardcoded:
        header = f"[ERROR-FLAG]{header}"
    parts = [header, message]
    if source:
        parts.append(f"source={source}")
    if year is not None:
        parts.append(f"year={year}")
    if expected_year is not None:
        parts.append(f"expected={expected_year}")
    if hardcoded:
        parts.append("hardcoded=yes")
    if fallback:
        parts.append("fallback=yes")
    if rec.line is not None:
        parts.append(f"line={rec.line}")
    print(" | ".join(parts), flush=True)


def warn_fallback(message: str, *, source: str | None = None, year: int | None = None,
                  hardcoded: bool = False) -> None:
    warn(
        "fallback",
        message,
        source=source,
        year=year,
        expected_year=target_year(),
        hardcoded=hardcoded,
        fallback=True,
    )


def warn_non_target_year(*, source: str, year: int | None, context: str) -> None:
    """Warn when a datum/year used for output is not the configured target year."""
    exp = target_year()
    if year is None:
        warn(
            "missing_year",
            f"{context}: could not determine data year",
            source=source,
            expected_year=exp,
        )
        return
    if int(year) != exp:
        warn(
            "year_mismatch",
            f"{context}: using year {year} instead of target year {exp}",
            source=source,
            year=int(year),
            expected_year=exp,
        )


def warn_years(source: str, years: Iterable[int], *, context: str) -> None:
    """Warn for every distinct non-target year in an iterable of years."""
    exp = target_year()
    seen = sorted({int(y) for y in years})
    if not seen:
        warn("missing_year", f"{context}: no years found", source=source, expected_year=exp)
        return
    for y in seen:
        if y != exp:
            warn(
                "year_mismatch",
                f"{context}: includes year {y} (target {exp})",
                source=source,
                year=y,
                expected_year=exp,
            )


def write_warning_report(path: Path) -> None:
    """Write collected warnings to JSON file (empty list if none)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(w) for w in _WARNINGS]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def warning_count() -> int:
    return len(_WARNINGS)
