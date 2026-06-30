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
import random
import time
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

import requests
from tqdm import tqdm

from config import DATA_DIR

log = logging.getLogger(__name__)

# Timeout for HTTP requests (connect, read) in seconds
_TIMEOUT = (10, 120)
_MAX_DOWNLOAD_ATTEMPTS = 5
_BACKOFF_BASE_SECONDS = 1.5
_BACKOFF_MAX_SECONDS = 20.0


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


def _download_with_progress(
    url: str,
    dest: Path,
    *,
    chunk_size: int = 1 << 20,
) -> Path:
    """Stream *url* into *dest* with the standard progress bar style."""
    tmp_dest = dest.with_suffix(dest.suffix + ".part")
    last_exc: Exception | None = None

    for attempt in range(1, _MAX_DOWNLOAD_ATTEMPTS + 1):
        try:
            response = requests.get(url, stream=True, timeout=_TIMEOUT)
            response.raise_for_status()

            total = int(response.headers.get("content-length", 0)) or None
            with tmp_dest.open("wb") as fh, tqdm(
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

            tmp_dest.replace(dest)
            log.info("Saved %s (%.1f kB)", dest, dest.stat().st_size / 1024)
            return dest

        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            # Retry transient server/rate-limit failures; fail fast on client errors.
            if status not in {429, 500, 502, 503, 504}:
                raise
            last_exc = exc
        except requests.exceptions.RequestException as exc:
            last_exc = exc

        if tmp_dest.exists():
            tmp_dest.unlink()

        if attempt >= _MAX_DOWNLOAD_ATTEMPTS:
            break

        backoff = min(_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)), _BACKOFF_MAX_SECONDS)
        # Small jitter helps avoid synchronized retries when remote endpoint is flaky.
        backoff += random.uniform(0.0, 0.5)
        log.warning(
            "Download attempt %d/%d failed for %s (%s). Retrying in %.1fs",
            attempt,
            _MAX_DOWNLOAD_ATTEMPTS,
            url,
            type(last_exc).__name__ if last_exc is not None else "unknown error",
            backoff,
        )
        time.sleep(backoff)

    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"Download failed for {url}")


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
    return _download_with_progress(url, dest, chunk_size=chunk_size)


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
        Survey / reference year (e.g., ``2025``).
    topic:
        File topic code.  Use the *canonical* name; year-specific filename
        variants are resolved automatically (see table below).

        Available in all years (2007–present):

        - ``"odmenovani"``                      – remuneration: negotiated wage
          increases, forms of pay, tariff vs. non-tariff systems.
        - ``"mzda_tarify"``                     – wage tariff levels agreed in CAs.

        Available 2009–present:

        - ``"zamestnanost_rozvoj_BOZP_dohody"`` – employment, personnel
          development, health & safety, and other agreements.
        - ``"spoluprace_smluvnich_stran"``      – cooperation of contracting
          parties (unions and employers).

        Available 2019–present:

        - ``"priplatky_dalsi_slozky_mzdy"``     – supplements and other wage
          components (overtime, night shifts, holiday pay, …).

        New from 2025:

        - ``"pracovni_zivotni_vyroci"``         – work and life anniversaries
          (jubilee benefits, service-length bonuses).
        - ``"prac_doba_zmeny_prac_pomeru"``      – working hours, leave, and
          changes to the employment relationship.
        - ``"prac_podminky_benefity"``           – working conditions and
          employee benefits (meal vouchers, transport, home-office, …).

        Historical-only (2007–2008):

        - ``"doba_zmeny_pomeru"``               – working time and changes to
          employment relationships.

    force:
        Re-download even when a cached copy already exists.

    Returns
    -------
    Path
        Local path to the cached ``.xls`` / ``.xlsx`` file.  Load it with
        :func:`pandas.read_excel`.
    """
    # Some topic filenames changed between the ISPP (2007–2008) era and later.
    # Map canonical topic names to their historical filename variants.
    _TOPIC_ALIASES: dict[str, dict[range, str]] = {
        "spoluprace_smluvnich_stran": {
            # 2007–2008 used a shorter name
            range(2007, 2009): "spoluprace_sml_stran",
        },
    }
    resolved_topic = topic
    for year_range, alias in _TOPIC_ALIASES.get(topic, {}).items():
        if year in year_range:
            resolved_topic = alias
            break

    yy = str(year)[2:]  # last two digits: 2024 → "24"
    if year >= 2019:
        prefix, ext = "IPP", ".xlsx"
    elif year >= 2015:
        prefix, ext = "IPP", ".xls"
    else:  # 2007–2014: published as ISPP (double-P) .xls
        prefix, ext = "ISPP", ".xls"
    filename = f"{prefix}_{yy}_{resolved_topic}{ext}"
    url = f"https://www.kolektivnismlouvy.cz/download/{year}/{filename}"
    return fetch(url, suffix=ext, force=force)


def fetch_ispv(
    year: int,
    half: int = 2,
    *,
    sphere: str = "podnikatelska",
    force: bool = False,
) -> Path:
    """Download an ISPV / RSCP Excel workbook from the TREXIMA portal.

    ISPV (*Informační systém o průměrném výdělku*) is the Czech wage-statistics
    system covering the **business / private sector** (podnikatelská sféra).
    RSCP (*Registr středních cen práce*) covers the **public / non-business
    sector** (nepodnikatelská sféra – e.g. government, education, health).
    Both surveys are published semi-annually by TREXIMA on behalf of the
    Ministry of Labour and Social Affairs (MPSV) at ``https://www.ispv.cz``.

    URL pattern::

        https://www.ispv.cz/files/{PREFIX}_{yy}H{half}.xlsx

    where ``PREFIX`` is ``"ISPV"`` for the private sector and ``"RSCP"`` for
    the public sector.

    The Excel workbooks contain sector-specific (NACE Rev. 2) breakdowns
    of median and mean wages, wage percentiles (P10, P25, P75, P90), and
    employee counts for the reference half-year period.

    Parameters
    ----------
    year:
        Reference year (e.g., ``2024``).
    half:
        Half-year: ``1`` = January–June, ``2`` = July–December.
        The H2 edition is typically the main annual publication.
    sphere:
        Which employment sphere to download:

        - ``"podnikatelska"``   – private / business sector (ISPV).
        - ``"nepodnikatelska"`` – public / non-business sector (RSCP).
    force:
        Re-download even when a cached copy already exists.

    Returns
    -------
    Path
        Local path to the cached ``.xlsx`` file.  Parse it with
        :func:`pandas.read_excel`; the sector labels are in Czech and
        correspond to NACE Rev. 2 section-level codes (A–S).

    Notes
    -----
    The TREXIMA portal occasionally reorganises its URL structure between
    annual editions.  If this function raises an HTTP 404, check the current
    download links at ``https://www.ispv.cz/cz/Vysledky/`` and pass an
    explicit URL via the generic :func:`fetch` helper instead.
    """
    yy = str(year)[2:]  # last two digits: 2024 → "24"
    prefix = "ISPV" if sphere == "podnikatelska" else "RSCP"
    filename = f"{prefix}_{yy}H{half}.xlsx"
    url = f"https://www.ispv.cz/files/{filename}"
    path = fetch(url, suffix=".xlsx", force=force)
    # Validate: a valid XLSX/ZIP file starts with the PK magic bytes (50 4B).
    # The ISPV portal returns a 2149-byte HTML error page with status 200 when
    # the old /files/ URL pattern is used.  Detect and reject that here.
    with open(path, "rb") as _fh:
        _magic = _fh.read(2)
    if _magic != b"PK":
        raise ValueError(
            f"Downloaded file is not a valid XLSX (magic={_magic!r}). "
            "The ISPV portal has likely changed its URL structure. "
            "Use stattool.fetch.fetch() with the current GUID-based URL from "
            "https://www.ispv.cz/cz/Vysledky-setreni/Aktualni.aspx"
        )
    return path


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


def fetch_ilostat(
    indicator: str,
    params: Optional[dict] = None,
    *,
    force: bool = False,
) -> Path:
    """Download a dataset from the ILOSTAT REST API as CSV.

    Uses the ``rplumber.ilo.org`` endpoint.  The indicator code uniquely
    identifies the dataset (e.g. ``"STR_DAYS_ECO_RT_A"`` for strike days
    per 1000 workers).

    API reference::

        https://rplumber.ilo.org/data/indicator/?id={indicator}&type=both&format=.csv

    Optional query parameters (passed via *params*):

    - ``ref_area``  – comma-separated ISO3 country codes, e.g. ``"CZE,DEU"``
    - ``classif1``  – first classification filter, e.g. ``"ECO_AGGREGATE_TOTAL"``
    - ``sex``       – e.g. ``"SEX_T"`` (total), ``"SEX_M"``, ``"SEX_F"``
    - ``timefrom``  – start year as string, e.g. ``"2000"``
    - ``timeto``    – end year as string

    CSV columns returned:

        ref_area, source, indicator, sex, classif1, classif2, time,
        obs_value, obs_status, note_*

    Parameters
    ----------
    indicator:
        ILOSTAT indicator code, e.g. ``"STR_DAYS_ECO_RT_A"``.
    params:
        Optional dict of additional query parameters (see above).
    force:
        Re-download even when a cached copy already exists.

    Returns the local :class:`Path` to the cached CSV.
    """
    from urllib.parse import urlencode as _urlencode

    base = "https://rplumber.ilo.org/data/indicator/"
    qp: dict = {"id": indicator, "type": "both", "format": ".csv"}
    if params:
        qp.update(params)

    # Build a stable cache key from indicator + sorted params (excluding format)
    cache_params = {k: v for k, v in sorted(qp.items()) if k != "format"}
    cache_key_str = indicator + "_" + "_".join(f"{k}-{v}" for k, v in cache_params.items() if k != "id")
    url_hash = hashlib.sha1(cache_key_str.encode()).hexdigest()[:8]
    dest = DATA_DIR / f"{indicator}_{url_hash}.csv"

    if dest.exists() and not force:
        log.info("Cache hit: %s", dest)
        return dest

    url = base + "?" + _urlencode(qp)
    log.info("Downloading ILOSTAT %s → %s", indicator, dest)
    return _download_with_progress(url, dest)

