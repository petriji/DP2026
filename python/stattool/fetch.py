"""
Fetch and cache remote data files (CSV, Excel, JSON).

Usage
-----
>>> from stattool.fetch import fetch
>>> path = fetch("https://ec.europa.eu/.../data.xlsx")
>>> import pandas as pd
>>> df = pd.read_excel(path)

The file is downloaded only once; subsequent calls return the cached path.
Pass force=True to re-download.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

import requests
from tqdm import tqdm

from config import DATA_DIR

log = logging.getLogger(__name__)

# Timeout for HTTP requests (connect, read) in seconds
_TIMEOUT = (10, 120)


def _cache_path(url: str, suffix: Optional[str] = None) -> Path:
    """Derive a stable cache filename from the URL."""
    parsed = urlparse(url)
    # Prefer the original filename from the URL path
    original_name = Path(parsed.path).name or "data"
    # Append a short hash to avoid collisions across different URLs with same filename
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
    stem = Path(original_name).stem
    ext = suffix or Path(original_name).suffix or ".bin"
    return DATA_DIR / f"{stem}_{url_hash}{ext}"


def fetch(
    url: str,
    *,
    suffix: Optional[str] = None,
    force: bool = False,
    chunk_size: int = 1 << 20,
) -> Path:
    """Download *url* to the data cache and return the local :class:`Path`.

    Parameters
    ----------
    url:
        Full URL to the resource (HTTP/HTTPS).
    suffix:
        Override file extension, e.g. ``".xlsx"``.  Detected from URL by default.
    force:
        Re-download even if a cached copy already exists.
    chunk_size:
        Streaming chunk size in bytes (default 1 MiB).
    """
    dest = _cache_path(url, suffix)

    if dest.exists() and not force:
        log.info("Cache hit: %s", dest)
        return dest

    log.info("Downloading %s → %s", url, dest)
    response = requests.get(url, stream=True, timeout=_TIMEOUT)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0)) or None
    with dest.open("wb") as fh, tqdm(
        total=total,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc=dest.name,
        leave=False,
    ) as bar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            fh.write(chunk)
            bar.update(len(chunk))

    log.info("Saved %s (%.1f kB)", dest, dest.stat().st_size / 1024)
    return dest


def fetch_oecd(
    dataset: str,
    filter_expr: str = "all",
    *,
    start_period: Optional[Union[int, str]] = None,
    end_period: Optional[Union[int, str]] = None,
    force: bool = False,
) -> Path:
    """Download a dataset from the OECD Stats SDMX REST API as CSV.

    Uses the ``stats.oecd.org`` endpoint which accepts plain dataset codes
    and returns comma-separated values via ``contentType=csv``.

    Parameters
    ----------
    dataset:
        OECD dataset code, e.g. ``"TUD"`` (Trade Union Density) or
        ``"AV_AN_WAGE"`` (Average Annual Wages).
    filter_expr:
        Dot-separated SDMX key filter, e.g.
        ``"CZE+AUT+DEU+DNK+POL+SVK.../all"``.
        Use ``"all"`` (default) to download the full dataset.
    start_period / end_period:
        Integer years or strings, e.g. ``1990`` or ``"2023"``.
    force:
        Re-download even when a cached copy already exists.

    Returns the local :class:`Path` to the cached CSV.  Load it with
    :meth:`~stattool.dataset.Dataset.from_oecd_csv`.
    """
    from urllib.parse import urlencode as _urlencode

    base = "https://stats.oecd.org/SDMX-JSON/data"
    endpoint = f"{base}/{dataset}/{filter_expr}/all"

    qp: dict = {"contentType": "csv"}
    if start_period is not None:
        qp["startTime"] = str(start_period)
    if end_period is not None:
        qp["endTime"] = str(end_period)

    url = endpoint + "?" + _urlencode(qp)
    return fetch(url, suffix=".csv", force=force)


def fetch_ipp(
    year: int,
    topic: str = "odmenovani",
    *,
    force: bool = False,
) -> Path:
    """Download an IPP (Informace o pracovních podmínkách) Excel workbook from MPSV.

    IPP is the annual Czech survey of collective agreements conducted by the Ministry
    of Labour and Social Affairs (MPSV) in cooperation with trade unions and employer
    associations.  Results are published at ``https://www.kolektivnismlouvy.cz``.

    URL pattern::

        https://www.kolektivnismlouvy.cz/download/{year}/IPP_{yy}_{topic}.xlsx

    Parameters
    ----------
    year:
        Survey / reference year (e.g., ``2024``).
    topic:
        File topic code.  Known codes and the data they contain:

        - ``"odmenovani"``                    – remuneration: negotiated wage
          increases, forms of pay, tariff vs. non-tariff systems.
        - ``"mzda_tarify"``                   – wage tariff levels agreed in CAs.
        - ``"priplatky_dalsi_slozky_mzdy"``   – supplements and other wage
          components (overtime, night shifts, holiday pay, …).
        - ``"zamestnanost_rozvoj_BOZP_dohody"`` – employment, personnel
          development, health & safety, and other agreements.
        - ``"spoluprace_smluvnich_stran"``    – cooperation of contracting
          parties (unions and employers).
    force:
        Re-download even when a cached copy already exists.

    Returns
    -------
    Path
        Local path to the cached ``.xlsx`` file.  Load it with
        :func:`pandas.read_excel` or :meth:`~stattool.dataset.Dataset.from_ipp_excel`.
    """
    yy = str(year)[2:]  # last two digits: 2024 → "24"
    filename = f"IPP_{yy}_{topic}.xlsx"
    url = f"https://www.kolektivnismlouvy.cz/download/{year}/{filename}"
    return fetch(url, suffix=".xlsx", force=force)


def fetch_eurostat(
    dataset: str,
    filter_expr: str = "",
    *,
    start_period: Optional[Union[int, str]] = None,
    end_period: Optional[Union[int, str]] = None,
    force: bool = False,
) -> Path:
    """Download a dataset from the Eurostat SDMX 2.1 REST API as SDMX-CSV.

    Uses the path-based filter format which reliably respects geo/dimension
    restrictions (query-param filtering is inconsistent across datasets).

    Parameters
    ----------
    dataset:
        Eurostat dataset code, e.g. ``"nama_10_pc"``.
    filter_expr:
        Dimension filter expression matching the dataset's SDMX dimension
        order, separated by dots.  Use ``+`` for multiple values within one
        dimension and leave a dimension blank to select all::

            "A.CP_PPS_EU27_2020_HAB.B1GQ.AT+CZ+DE+DK+PL+SK"
            "A.TOTAL.GINI_HND.AT+CZ"      # ilc_di12
            "A.AT+CZ+DK"                  # earn_nt_taxwedge (2-dim)

        Omit *filter_expr* entirely to download the full dataset.
    start_period / end_period:
        Integer years or ISO period strings, e.g. ``2010`` or ``"2010-Q1"``.
    force:
        Re-download even when a cached copy already exists.

    Returns the local :class:`Path` to the cached CSV.  Load it with
    :meth:`~core.dataset.Dataset.from_sdmx_csv`.
    """
    from urllib.parse import urlencode as _urlencode

    base = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data"
    endpoint = f"{base}/{dataset}"
    if filter_expr:
        endpoint += f"/{filter_expr}"

    qp: dict = {"format": "SDMX-CSV", "compressed": "false"}
    if start_period is not None:
        qp["startPeriod"] = str(start_period)
    if end_period is not None:
        qp["endPeriod"] = str(end_period)

    url = endpoint + "?" + _urlencode(qp)
    return fetch(url, suffix=".csv", force=force)

