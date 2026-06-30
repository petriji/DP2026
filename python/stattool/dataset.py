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

    @classmethod
    def from_oecd_csv(
        cls,
        path,
        *,
        name: str = "value",
        unit: str = "",
        source_url: str = "",
        filters: Optional[dict] = None,
    ) -> "Dataset":
        """Parse a CSV file downloaded from the OECD Stats SDMX API.

        The OECD Stats CSV format (``contentType=csv``) typically looks like::

            LOCATION,INDICATOR,SUBJECT,MEASURE,FREQUENCY,TIME,Value,Flag Codes
            CZE,TUD,,,A,1990,65.2,
            AUT,TUD,,,A,1990,55.3,

        Country codes are 3-letter ISO 3166-1 alpha-3 and are automatically
        converted to 2-letter codes used throughout this codebase.

        Parameters
        ----------
        path:
            Local path to the OECD CSV (returned by
            :func:`~stattool.fetch.fetch_oecd`).
        name:
            Human-readable variable name stored in :attr:`Dataset.name`.
        unit:
            Unit string (e.g. ``"%"`` or ``"USD PPP"``).
        source_url:
            The OECD URL used to obtain the file.
        filters:
            Optional dict of ``{column_name: value_or_list}`` to keep only
            matching rows after loading, e.g.::

                filters={"INDICATOR": "TUD"}
        """
        df = pd.read_csv(path, na_values=["", "..", "NA", ": "])

        # Detect column names — OECD CSV format varies across datasets
        cols_up = {c.upper(): c for c in df.columns}

        # Geo column: LOCATION (old) or REF_AREA / COU (newer exports)
        geo_col = next(
            (cols_up[k] for k in ("LOCATION", "COU", "REF_AREA", "COUNTRY", "GEO")
             if k in cols_up),
            None,
        )
        # Time column: TIME (old) or TIME_PERIOD / YEAR
        time_col = next(
            (cols_up[k] for k in ("TIME", "YEAR", "TIME_PERIOD", "PERIOD")
             if k in cols_up),
            None,
        )
        # Value column: Value (old) or OBS_VALUE
        value_col = next(
            (cols_up[k] for k in ("VALUE", "OBS_VALUE", "OBSVALUE")
             if k in cols_up),
            None,
        )

        if not all([geo_col, time_col, value_col]):
            raise ValueError(
                f"Could not identify geo/time/value columns. "
                f"Available columns: {list(df.columns)}"
            )

        df = df.rename(columns={geo_col: "geo", time_col: "time", value_col: "value"})

        # Normalise OECD 3-letter ISO codes to 2-letter
        df["geo"] = df["geo"].map(
            lambda x: _OECD_ISO3_TO_ISO2.get(str(x).upper(), str(x))
        )

        # Coerce time to int (years)
        try:
            df["time"] = df["time"].astype(int)
        except (ValueError, TypeError):
            pass

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
    def from_ipp_excel(
        cls,
        path,
        *,
        sheet_name: int | str = 0,
        skiprows: int = 3,
        year_col: str | None = None,
        value_col: str | None = None,
        year: int | None = None,
        name: str = "value",
        unit: str = "%",
        source_url: str = "",
    ) -> "Dataset":
        """Parse an IPP (Informace o pracovních podmínkách) Excel workbook.

        IPP workbooks are published annually by the Czech Ministry of Labour
        and Social Affairs (MPSV) at ``https://www.kolektivnismlouvy.cz``.
        Each workbook covers a single survey year and contains multiple sheets
        (záložky) for different aspects of collective agreements.

        The method returns a tidy long-format :class:`Dataset` with columns
        ``geo`` (fixed to ``"CZ"``), ``time`` (survey year), and ``value``
        (the extracted numeric metric).

        Parameters
        ----------
        path:
            Local path to the ``.xlsx`` file (returned by
            :func:`~stattool.fetch.fetch_ipp`).
        sheet_name:
            Sheet name or 0-based index to read.  Defaults to the first sheet.
        skiprows:
            Number of header rows to skip before the column labels.  Czech
            government workbooks typically have 2–4 title rows at the top.
        year_col:
            Name of the column containing the survey year (or a label/row
            that should be parsed as the year).  When ``None``, the method
            tries to auto-detect a column whose values look like 4-digit years.
        value_col:
            Name (or substring match) of the column containing the primary
            numeric metric.  When ``None``, the first numeric column that is
            not the year column is used.
        year:
            Override the survey year when the workbook does not contain an
            explicit year column (single-year files).  If provided, a ``time``
            column with this constant value is created.
        name:
            Human-readable variable name for :attr:`Dataset.name`.
        unit:
            Unit string (e.g. ``"%"`` or ``"CZK"``).
        source_url:
            Original URL of the workbook.

        Returns
        -------
        Dataset
            Tidy long-format Dataset with columns ``geo``, ``time``, ``value``.

        Examples
        --------
        >>> from stattool.fetch import fetch_ipp
        >>> from stattool.dataset import Dataset
        >>> path = fetch_ipp(2024, "odmenovani")
        >>> ds = Dataset.from_ipp_excel(
        ...     path,
        ...     sheet_name=0,
        ...     skiprows=3,
        ...     year=2024,
        ...     value_col="Sjednaný nárůst",
        ...     name="Sjednaný nárůst základní mzdy",
        ...     unit="%",
        ...     source_url="MPSV IPP 2024",
        ... )
        """
        df_raw = pd.read_excel(
            path,
            sheet_name=sheet_name,
            skiprows=skiprows,
            header=0,
        )
        # Drop fully-empty rows and columns
        df_raw = df_raw.dropna(how="all").reset_index(drop=True)
        df_raw = df_raw.loc[:, df_raw.notna().any(axis=0)]

        # ── Determine year column ─────────────────────────────────────────────
        if year is not None:
            # Single-year file: inject a constant year column
            df_raw["time"] = year
            time_col_used = "time"
        elif year_col is not None:
            # Exact column name provided
            if year_col not in df_raw.columns:
                raise ValueError(
                    f"year_col '{year_col}' not found. "
                    f"Available columns: {list(df_raw.columns)}"
                )
            df_raw = df_raw.rename(columns={year_col: "time"})
            time_col_used = "time"
        else:
            # Auto-detect: find first column whose values are 4-digit years
            time_col_used = _detect_year_column(df_raw)
            if time_col_used is None:
                raise ValueError(
                    "Cannot auto-detect a year column in the IPP workbook. "
                    "Pass year_col= or year= explicitly."
                )
            df_raw = df_raw.rename(columns={time_col_used: "time"})
            time_col_used = "time"

        # ── Determine value column ────────────────────────────────────────────
        if value_col is not None:
            # Exact name or substring match
            matched = [c for c in df_raw.columns if value_col in str(c)]
            if not matched:
                raise ValueError(
                    f"value_col substring '{value_col}' not found. "
                    f"Available columns: {list(df_raw.columns)}"
                )
            val_col = matched[0]
        else:
            # Auto-detect: first numeric column that is not the time column
            numeric_cols = [
                c for c in df_raw.columns
                if c != time_col_used
                and pd.api.types.is_numeric_dtype(df_raw[c])
            ]
            if not numeric_cols:
                raise ValueError(
                    "No numeric column found in the IPP workbook. "
                    "Pass value_col= explicitly."
                )
            val_col = numeric_cols[0]

        df = pd.DataFrame({
            "geo": "CZ",
            "time": pd.to_numeric(df_raw[time_col_used], errors="coerce"),
            "value": pd.to_numeric(df_raw[val_col], errors="coerce"),
        })
        df = df.dropna(subset=["time", "value"]).copy()
        df["time"] = df["time"].astype(int)

        return cls(df, name=name, unit=unit, source_url=source_url)


def _is_year_col(col: str) -> bool:
    try:
        y = int(str(col).strip())
        return 1900 <= y <= 2100
    except ValueError:
        return False


def _detect_year_column(df: pd.DataFrame) -> Optional[str]:
    """Return the name of the first column whose non-null values are 4-digit years.

    Used by :meth:`Dataset.from_ipp_excel` to auto-detect the year column in
    Czech government Excel workbooks where the column header may vary by year.
    """
    for col in df.columns:
        sample = df[col].dropna().head(10)
        if sample.empty:
            continue
        try:
            years = pd.to_numeric(sample, errors="coerce").dropna()
            if len(years) > 0 and years.between(1900, 2100).all():
                return col
        except Exception:
            continue
    return None


# ── OECD ISO 3166-1 alpha-3 → alpha-2 mapping ────────────────────────────────
# OECD uses 3-letter codes; the rest of the codebase uses 2-letter codes.
_OECD_ISO3_TO_ISO2: dict[str, str] = {
    "AUT": "AT", "BEL": "BE", "BGR": "BG", "CYP": "CY", "CZE": "CZ",
    "DEU": "DE", "DNK": "DK", "ESP": "ES", "EST": "EE", "FIN": "FI",
    "FRA": "FR", "GBR": "GB", "GRC": "GR", "HRV": "HR", "HUN": "HU",
    "IRL": "IE", "ISL": "IS", "ITA": "IT", "LTU": "LT", "LUX": "LU",
    "LVA": "LV", "MLT": "MT", "NLD": "NL", "NOR": "NO", "POL": "PL",
    "PRT": "PT", "ROU": "RO", "SVK": "SK", "SVN": "SI", "SWE": "SE",
    "CHE": "CH", "TUR": "TR", "USA": "US", "JPN": "JP", "KOR": "KR",
    "AUS": "AU", "CAN": "CA", "MEX": "MX", "NZL": "NZ",
}
