"""
Lightweight wrapper around a :class:`pandas.DataFrame` that keeps metadata
(source URL, variable name, unit) together with the data and provides
convenience accessors used by the visualisation modules.

Typical usage
-------------
>>> from stattool.fetch import fetch
>>> from stattool.dataset import Dataset
>>> import pandas as pd
>>>
>>> path = fetch("https://example.com/data.csv")
>>> df = pd.read_csv(path)
>>> ds = Dataset(df, name="Gini coefficient", unit="%", source_url="https://...")
>>> ds.for_year(2022)          # → filtered DataFrame
>>> ds.countries               # → list[str] of ISO-3166-alpha2 codes
>>> ds.years                   # → sorted list[int]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class Dataset:
    """Container pairing a tidy DataFrame with metadata.

    Expected DataFrame shape (long / tidy format)::

        geo   | time | value | [unit] | [other columns…]
        ------+------+-------+--------+-----------------
        CZ    | 2020 | 26.3  | …
        DE    | 2020 | 31.7  | …

    - ``geo``  column: ISO 3166-1 alpha-2 country code (upper-case, e.g. ``"CZ"``).
    - ``time`` column: integer year or pandas Period/datetime.
    - ``value`` column: the primary numeric variable.

    Column names can be overridden via constructor arguments.
    """

    df: pd.DataFrame
    name: str = "value"
    unit: str = ""
    source_url: str = ""
    geo_col: str = "geo"
    time_col: str = "time"
    value_col: str = "value"
    # Extra metadata key-value pairs (e.g. {"database": "Eurostat"})
    meta: dict = field(default_factory=dict)

    # ── Validation ────────────────────────────────────────────────────────────

    def __post_init__(self) -> None:
        missing = [
            c
            for c in (self.geo_col, self.time_col, self.value_col)
            if c not in self.df.columns
        ]
        if missing:
            raise ValueError(
                f"DataFrame is missing expected columns: {missing}. "
                f"Available: {list(self.df.columns)}"
            )
        # Coerce time column to int where possible (years)
        try:
            self.df = self.df.copy()
            self.df[self.time_col] = self.df[self.time_col].astype(int)
        except (ValueError, TypeError):
            pass  # non-integer time axis is fine

    # ── Derived properties ────────────────────────────────────────────────────

    @property
    def countries(self) -> list[str]:
        """Sorted list of unique country codes present in the data."""
        return sorted(self.df[self.geo_col].dropna().unique().tolist())

    @property
    def years(self) -> list[int]:
        """Sorted list of unique integer years present in the data."""
        return sorted(self.df[self.time_col].dropna().unique().tolist())

    @property
    def latest_year(self) -> int:
        return self.years[-1]

    # ── Filtering helpers ─────────────────────────────────────────────────────

    def for_year(self, year: int) -> pd.DataFrame:
        """Return rows for a single year."""
        return self.df[self.df[self.time_col] == year].copy()

    def for_country(self, geo: str) -> pd.DataFrame:
        """Return rows for a single country code (case-insensitive)."""
        return self.df[self.df[self.geo_col].str.upper() == geo.upper()].copy()

    def for_countries(self, geos: list[str]) -> pd.DataFrame:
        """Return rows for a list of country codes."""
        upper = [g.upper() for g in geos]
        return self.df[self.df[self.geo_col].str.upper().isin(upper)].copy()

    def pivot(
        self,
        index: Optional[str] = None,
        columns: Optional[str] = None,
    ) -> pd.DataFrame:
        """Pivot to wide format.

        Defaults: index=time_col, columns=geo_col, values=value_col.
        """
        return self.df.pivot_table(
            index=index or self.time_col,
            columns=columns or self.geo_col,
            values=self.value_col,
            aggfunc="mean",
        )

    # ── I/O helpers ───────────────────────────────────────────────────────────

    @classmethod
    def from_eurostat_csv(
        cls,
        path,
        *,
        name: str = "value",
        unit: str = "",
        source_url: str = "",
        **kwargs,
    ) -> "Dataset":
        """Load a Eurostat bulk-download CSV (semicolon-separated, wide format).

        Eurostat CSVs look like::

            freq,unit,geo\\TIME_PERIOD,2022,2021,2020,...
            A,PC,AT,26.3,26.1,...

        This method melts the wide format into the tidy long format expected
        by :class:`Dataset`.
        """
        df = pd.read_csv(path, sep=",", na_values=[":", ": "])

        # Identify year columns (numeric headers)
        id_cols = [c for c in df.columns if not _is_year_col(c)]
        year_cols = [c for c in df.columns if _is_year_col(c)]

        df = df.melt(id_vars=id_cols, value_vars=year_cols, var_name="time", value_name="value")
        df["time"] = df["time"].astype(int)

        # Normalise geo column name
        geo_candidates = [c for c in id_cols if c.lower() in ("geo", "geo\\time_period", "country")]
        geo_col = geo_candidates[0] if geo_candidates else id_cols[-1]
        if geo_col != "geo":
            df = df.rename(columns={geo_col: "geo"})

        return cls(df, name=name, unit=unit, source_url=source_url, **kwargs)

    @classmethod
    def from_sdmx_csv(
        cls,
        path,
        *,
        name: str = "value",
        unit: str = "",
        source_url: str = "",
        filters: Optional[dict] = None,
    ) -> "Dataset":
        """Parse an SDMX-CSV file as returned by :func:`~core.fetch.fetch_eurostat`.

        The Eurostat SDMX-CSV format looks like::

            DATAFLOW,LAST UPDATE,freq,unit,na_item,geo,TIME_PERIOD,OBS_VALUE,...
            ESTAT:NAMA_10_PC(1.0),...,A,CP_PPS,...,AT,2022,48350.0,...

        The method renames ``TIME_PERIOD`` → ``time`` and ``OBS_VALUE`` →
        ``value``, drops metadata columns, and returns a :class:`Dataset`.

        Parameters
        ----------
        path:
            Local path to the SDMX-CSV file (returned by
            :func:`~core.fetch.fetch_eurostat`).
        name:
            Human-readable variable name stored in :attr:`Dataset.name`.
        unit:
            Unit string (e.g. ``"%"`` or ``"EUR PPS"``).
        source_url:
            The Eurostat URL used to obtain the file.
        filters:
            Optional dict of ``{column_name: value_or_list}`` to keep only
            matching rows after loading.  Useful when a single download
            contains multiple breakdowns, e.g.::

                filters={"sex": "T", "age": "Y20-64"}
        """
        df = pd.read_csv(path, na_values=["", ":", ": "])
        # Rename standard SDMX columns
        df = df.rename(columns={"TIME_PERIOD": "time", "OBS_VALUE": "value"})
        # Drop Eurostat metadata columns that are not analytical
        drop_cols = {"DATAFLOW", "LAST UPDATE", "OBS_FLAG", "CONF_STATUS"}
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])
        # Normalise Eurostat-specific geo codes to ISO 3166-1 alpha-2 so that
        # they match Natural Earth / standard reference data:
        #   EL → GR  (Greece), UK → GB  (United Kingdom)
        if "geo" in df.columns:
            df["geo"] = df["geo"].replace({"EL": "GR", "UK": "GB"})
        # Apply optional row filters
        if filters:
            for col, val in filters.items():
                if col not in df.columns:
                    continue
                if isinstance(val, (list, tuple, set)):
                    df = df[df[col].isin(val)]
                else:
                    df = df[df[col] == val]
        df = df.dropna(subset=["value"])
        return cls(df, name=name, unit=unit, source_url=source_url)

    @classmethod
    def from_wide(
        cls,
        path,
        *,
        geo_col: str = "geo",
        name: str = "value",
        unit: str = "",
        source_url: str = "",
        read_kwargs: Optional[dict] = None,
    ) -> "Dataset":
        """Load an Excel/CSV where columns are years and rows are countries."""
        _read_kwargs = read_kwargs or {}
        suffix = str(path).lower()
        if suffix.endswith(".csv"):
            df = pd.read_csv(path, **_read_kwargs)
        else:
            df = pd.read_excel(path, **_read_kwargs)

        id_cols = [c for c in df.columns if not _is_year_col(c)]
        year_cols = [c for c in df.columns if _is_year_col(c)]
        df = df.melt(id_vars=id_cols, value_vars=year_cols, var_name="time", value_name="value")
        df["time"] = df["time"].astype(int)
        return cls(df, name=name, unit=unit, source_url=source_url, geo_col=geo_col)


def _is_year_col(col: str) -> bool:
    try:
        y = int(str(col).strip())
        return 1900 <= y <= 2100
    except ValueError:
        return False
