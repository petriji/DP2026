"""MCP tools for the DP thesis data layer.

The server is intentionally a thin wrapper around ``stattool``. It gives
agents read-oriented access to cached provider data without making the normal
LaTeX/Python build depend on MCP.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

import pandas as pd
from mcp.server.fastmcp import FastMCP

from config import DATA_DIR, PYTHON_DIR
from stattool.dataset import Dataset
from stattool.fetch import fetch_eurostat, fetch_ilostat, fetch_oecd

DP_DIR = PYTHON_DIR.parent
REVIEW_DIR = DP_DIR / "review"
REGISTRY_PATH = PYTHON_DIR / "analytics_registry.toml"

mcp = FastMCP("dp-data")


def _resolve_project_path(path: str | Path) -> Path:
    raw = Path(path)
    candidates = [raw] if raw.is_absolute() else [DP_DIR / raw, PYTHON_DIR / raw]

    resolved = next((candidate.resolve() for candidate in candidates if candidate.exists()), candidates[0].resolve())
    try:
        resolved.relative_to(DP_DIR)
    except ValueError as exc:
        raise ValueError(f"Path must stay inside the DP workspace: {resolved}") from exc
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def _provider_name(provider: str) -> str:
    normalized = provider.strip().lower().replace("-", "_")
    aliases = {
        "sdmx": "eurostat",
        "eurostat_sdmx": "eurostat",
        "oecd_csv": "oecd",
        "plain_csv": "csv",
    }
    return aliases.get(normalized, normalized)


def _apply_filters(df: pd.DataFrame, filters: dict[str, Any] | None) -> pd.DataFrame:
    if not filters:
        return df

    out = df
    for column, value in filters.items():
        if column not in out.columns:
            continue
        if isinstance(value, list):
            out = out[out[column].isin(value)]
        else:
            out = out[out[column] == value]
    return out


def _load_dataframe(
    path: Path,
    provider: str,
    filters: dict[str, Any] | None = None,
) -> pd.DataFrame:
    provider = _provider_name(provider)
    if provider == "eurostat":
        return Dataset.from_sdmx_csv(path, filters=filters).df
    if provider == "oecd":
        return Dataset.from_oecd_csv(path, filters=filters).df
    if provider == "ilostat":
        df = pd.read_csv(path, na_values=["", "..", "NA", ": "])
        df = df.rename(columns={"ref_area": "geo", "obs_value": "value"})
        return _apply_filters(df, filters)
    if provider == "csv":
        return _apply_filters(pd.read_csv(path), filters)
    raise ValueError("provider must be one of: eurostat, oecd, ilostat, csv")


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    clean = df.astype(object).where(pd.notna(df), None)
    return [
        {str(column): _json_value(value) for column, value in row.items()}
        for row in clean.to_dict(orient="records")
    ]


def _first_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    lower = {column.lower(): column for column in df.columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return None


def _coverage(path: Path, provider: str, df: pd.DataFrame, target_year: int | None) -> dict[str, Any]:
    geo_col = _first_column(df, ("geo", "location", "ref_area", "country", "cou"))
    time_col = _first_column(df, ("time", "time_period", "year", "period", "TIME"))
    value_col = _first_column(df, ("value", "obs_value", "Value", "OBS_VALUE"))

    countries: list[Any] = []
    if geo_col:
        countries = sorted(_json_value(value) for value in df[geo_col].dropna().unique())

    years: list[Any] = []
    numeric_years: list[int] = []
    if time_col:
        for value in df[time_col].dropna().unique():
            json_value = _json_value(value)
            years.append(json_value)
            try:
                numeric_years.append(int(json_value))
            except (TypeError, ValueError):
                pass
        years = sorted(years)

    latest_year = max(numeric_years) if numeric_years else None
    return {
        "path": str(path),
        "provider": _provider_name(provider),
        "rows": int(len(df)),
        "columns": [str(column) for column in df.columns],
        "geo_column": geo_col,
        "time_column": time_col,
        "value_column": value_col,
        "countries": countries,
        "years": years,
        "latest_year": latest_year,
        "target_year": target_year,
        "target_year_present": None if target_year is None else target_year in numeric_years,
    }


@mcp.tool()
def eurostat_fetch(
    dataset: str,
    filter_expr: str = "",
    start_period: int | str | None = None,
    end_period: int | str | None = None,
    force: bool = False,
    target_year: int | None = 2025,
) -> dict[str, Any]:
    """Fetch a Eurostat SDMX-CSV dataset into the project cache and report coverage."""
    path = fetch_eurostat(
        dataset,
        filter_expr,
        start_period=start_period,
        end_period=end_period,
        force=force,
    )
    df = _load_dataframe(path, "eurostat")
    return _coverage(path, "eurostat", df, target_year)


@mcp.tool()
def oecd_fetch(
    dataset: str,
    filter_expr: str = "all",
    start_period: int | str | None = None,
    end_period: int | str | None = None,
    force: bool = False,
    target_year: int | None = 2025,
) -> dict[str, Any]:
    """Fetch an OECD Stats CSV dataset into the project cache and report coverage."""
    path = fetch_oecd(
        dataset,
        filter_expr,
        start_period=start_period,
        end_period=end_period,
        force=force,
    )
    df = _load_dataframe(path, "oecd")
    return _coverage(path, "oecd", df, target_year)


@mcp.tool()
def ilostat_fetch(
    indicator: str,
    params: dict[str, Any] | None = None,
    force: bool = False,
    target_year: int | None = 2025,
) -> dict[str, Any]:
    """Fetch an ILOSTAT indicator CSV into the project cache and report coverage."""
    path = fetch_ilostat(indicator, params=params, force=force)
    df = _load_dataframe(path, "ilostat")
    return _coverage(path, "ilostat", df, target_year)


@mcp.tool()
def dataset_coverage(
    path: str,
    provider: str,
    filters: dict[str, Any] | None = None,
    target_year: int | None = 2025,
) -> dict[str, Any]:
    """Read a cached dataset and return rows, columns, countries, and years."""
    resolved = _resolve_project_path(path)
    df = _load_dataframe(resolved, provider, filters=filters)
    return _coverage(resolved, provider, df, target_year)


@mcp.tool()
def dataset_preview(
    path: str,
    provider: str,
    filters: dict[str, Any] | None = None,
    columns: list[str] | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Read a cached dataset and return a small JSON-safe table preview."""
    resolved = _resolve_project_path(path)
    df = _load_dataframe(resolved, provider, filters=filters)
    if columns:
        existing = [column for column in columns if column in df.columns]
        df = df[existing]
    limit = max(1, min(int(limit), 200))
    preview = df.head(limit)
    return {
        "path": str(resolved),
        "provider": _provider_name(provider),
        "rows_total": int(len(df)),
        "rows_returned": int(len(preview)),
        "columns": [str(column) for column in preview.columns],
        "records": _records(preview),
    }


@mcp.tool()
def data_cache_list(limit: int = 100) -> dict[str, Any]:
    """List cached data files under python/data without reading their contents."""
    limit = max(1, min(int(limit), 500))
    files = sorted(
        (
            {
                "path": str(path),
                "name": path.name,
                "size_bytes": path.stat().st_size,
            }
            for path in DATA_DIR.glob("**/*")
            if path.is_file()
        ),
        key=lambda row: row["name"],
    )
    return {"data_dir": str(DATA_DIR), "count_total": len(files), "files": files[:limit]}


@mcp.tool()
def analytics_registry_list() -> dict[str, Any]:
    """Return the analysis registry entries that map scripts to generated stems."""
    with REGISTRY_PATH.open("rb") as handle:
        registry = tomllib.load(handle)
    return {
        "path": str(REGISTRY_PATH),
        "entries": [
            {
                "key": key,
                "script": value.get("script"),
                "texparts": value.get("texparts", []),
                "pics": value.get("pics", []),
            }
            for key, value in sorted(registry.items())
        ],
    }


@mcp.tool()
def data_quality_report() -> dict[str, Any]:
    """Return the latest stats_analytics data-quality report, if present."""
    path = REVIEW_DIR / "data_quality_report.json"
    if not path.exists():
        return {"path": str(path), "exists": False, "report": None}
    return {"path": str(path), "exists": True, "report": json.loads(path.read_text(encoding="utf-8"))}


if __name__ == "__main__":
    mcp.run()
