import asyncio
import logging
import math
import time
from collections.abc import Sequence
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any

import aiohttp

from app.services.cloud_coverage import get_cloud_coverage_series
from app.services.sea_level import get_sea_level_series
from app.services.temperature import get_temperature_series
from app.services.vegetation import get_vegetation_series
from app.services.wildfires import get_wildfire_series


logger = logging.getLogger(__name__)

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
NOAA_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
MODIS_BASE_URL = "https://modis.ornl.gov/rst/api/v1/MOD13Q1"
REQUEST_TIMEOUT_SECONDS = 15
OVERALL_TIMEOUT_SECONDS = 25
CACHE_TTL_SECONDS = 600
FALLBACK_CACHE_TTL_SECONDS = 60

POWER_PARAMETERS = {
    "temperature": "T2M",
    "cloud_coverage": "CLOUD_AMT",
}

POWER_COORDINATES = {
    "temperature": {
        "global": (0.0, 0.0),
        "uzbekistan": (41.3, 69.2),
        "usa": (39.8, -98.6),
        "japan": (35.7, 139.7),
    },
    "cloud_coverage": {
        "global": (0.0, 0.0),
        "tropics": (0.0, -30.0),
        "arctic": (80.0, 0.0),
        "sahara": (23.0, 13.0),
    },
}

EONET_BBOXES = {
    "california": "-124,42,-114,32",
    "amazon": "-75,5,-45,-15",
    "australia": "112,-10,154,-44",
}

NOAA_STATIONS = {
    "global": ("9414290", "San Francisco gauge; proxy, not global mean"),
    "pacific": ("1612340", "Honolulu gauge"),
    "atlantic": ("8724580", "Key West gauge"),
}

MODIS_COORDINATES = {
    "global": (0.0, 20.0),
    "amazon": (-3.47, -62.21),
    "boreal": (60.0, 90.0),
    "sahel": (15.0, 0.0),
}


@dataclass(frozen=True)
class YearlyDataResult:
    values: tuple[tuple[int, float], ...]
    source: str
    used_fallback: bool


class EarthDataError(RuntimeError):
    pass


_cache: dict[tuple[str, str, tuple[int, ...]], tuple[float, YearlyDataResult]] = {}


async def _get_json(
    session: aiohttp.ClientSession,
    url: str,
    params: dict[str, str | int | float],
) -> dict[str, Any]:
    async with session.get(url, params=params) as response:
        if response.status >= 400:
            body = (await response.text())[:300]
            raise EarthDataError(f"{url} returned HTTP {response.status}: {body}")
        payload = await response.json(content_type=None)
        if not isinstance(payload, dict):
            raise EarthDataError(f"{url} returned a non-object response")
        return payload


def _require_complete_years(
    values: list[tuple[int, float]],
    years: tuple[int, ...],
) -> list[tuple[int, float]]:
    values_by_year = dict(values)
    missing_years = [year for year in years if year not in values_by_year]
    if missing_years:
        raise EarthDataError(f"Missing yearly values for {missing_years}")
    return [(year, values_by_year[year]) for year in years]


async def _fetch_power_series(
    session: aiohttp.ClientSession,
    metric_key: str,
    location_key: str,
    years: tuple[int, ...],
) -> tuple[list[tuple[int, float]], str]:
    parameter = POWER_PARAMETERS[metric_key]
    coordinates = POWER_COORDINATES[metric_key].get(location_key)
    if coordinates is None:
        raise EarthDataError("NASA POWER has no coordinate configured for this location")

    latitude, longitude = coordinates
    payload = await _get_json(
        session,
        POWER_URL,
        {
            "parameters": parameter,
            "community": "AG",
            "longitude": longitude,
            "latitude": latitude,
            "start": f"{years[0]}0101",
            "end": f"{years[-1]}1231",
            "format": "JSON",
            "time-standard": "UTC",
        },
    )

    daily_values = payload["properties"]["parameter"][parameter]
    yearly_totals: dict[int, list[float]] = defaultdict(list)
    for date_key, raw_value in daily_values.items():
        value = float(raw_value)
        if not math.isfinite(value) or value <= -999:
            continue
        year = int(date_key[:4])
        if year in years:
            yearly_totals[year].append(value)

    values = [
        (year, sum(yearly_totals[year]) / len(yearly_totals[year]))
        for year in years
        if yearly_totals[year]
    ]
    point_description = f"{latitude:.2f}°, {longitude:.2f}° representative point"
    source = f"NASA POWER daily {parameter} ({point_description})"
    return _require_complete_years(values, years), source


async def _fetch_eonet_wildfires(
    session: aiohttp.ClientSession,
    location_key: str,
    years: tuple[int, ...],
) -> tuple[list[tuple[int, float]], str]:
    semaphore = asyncio.Semaphore(5)

    async def fetch_year(year: int) -> tuple[int, float]:
        params: dict[str, str | int] = {
            "category": "wildfires",
            "status": "all",
            "start": f"{year}-01-01",
            "end": f"{year}-12-31",
            "limit": 1000,
        }
        bbox = EONET_BBOXES.get(location_key)
        if bbox is not None:
            params["bbox"] = bbox

        async with semaphore:
            payload = await _get_json(session, EONET_URL, params)
        events = payload.get("events")
        if not isinstance(events, list):
            raise EarthDataError("NASA EONET response did not include an events list")
        if len(events) >= int(params["limit"]):
            raise EarthDataError(f"NASA EONET result may be truncated for {year}")

        event_ids: set[str] = set()
        for event in events:
            event_id = str(event.get("id", ""))
            if event_id and any(
                date.fromisoformat(geometry["date"][:10]).year == year
                for geometry in event.get("geometry", [])
                if geometry.get("date")
            ):
                event_ids.add(event_id)
        return year, float(len(event_ids))

    values = await asyncio.gather(*(fetch_year(year) for year in years))
    return values, "NASA EONET curated wildfire events"


async def _fetch_noaa_sea_level(
    session: aiohttp.ClientSession,
    location_key: str,
    years: tuple[int, ...],
) -> tuple[list[tuple[int, float]], str]:
    station = NOAA_STATIONS.get(location_key)
    if station is None:
        raise EarthDataError("No NOAA CO-OPS gauge is mapped for this ocean region")

    station_id, station_name = station
    payload = await _get_json(
        session,
        NOAA_URL,
        {
            "begin_date": f"{years[0]}0101",
            "end_date": f"{years[-1]}1231",
            "station": station_id,
            "product": "monthly_mean",
            "datum": "MSL",
            "time_zone": "gmt",
            "units": "metric",
            "application": "EarthJukebox",
            "format": "json",
        },
    )

    rows = payload.get("data")
    if not isinstance(rows, list):
        raise EarthDataError(f"NOAA response had no monthly data for station {station_id}")

    monthly_values: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        if str(row.get("inferred", "0")) not in ("0", ""):
            continue
        value = row.get("MSL")
        if value in (None, ""):
            continue
        year = int(row["year"])
        if year in years:
            monthly_values[year].append(float(value) * 1000.0)

    current_year = date.today().year
    values = []
    for year in years:
        minimum_months = 6 if year == current_year else 9
        if len(monthly_values[year]) >= minimum_months:
            values.append((year, sum(monthly_values[year]) / len(monthly_values[year])))
    source = f"NOAA CO-OPS station {station_id} ({station_name}; monthly mean, mm)"
    return _require_complete_years(values, years), source


async def _fetch_modis_ndvi(
    session: aiohttp.ClientSession,
    location_key: str,
    years: tuple[int, ...],
) -> tuple[list[tuple[int, float]], str]:
    coordinates = MODIS_COORDINATES.get(location_key)
    if coordinates is None:
        raise EarthDataError("No MODIS representative point is configured for this location")

    latitude, longitude = coordinates
    selected_dates = {year: f"A{year}193" for year in years}

    semaphore = asyncio.Semaphore(5)

    async def fetch_one(year: int, composite_date: str) -> tuple[int, float]:
        async with semaphore:
            payload = await _get_json(
                session,
                f"{MODIS_BASE_URL}/subset",
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    "startDate": composite_date,
                    "endDate": composite_date,
                    "kmAboveBelow": 0,
                    "kmLeftRight": 0,
                    "band": "250m_16_days_NDVI",
                },
            )
        ndvi_entry = next(
            (
                item
                for item in payload.get("subset", [])
                if item.get("band") == "250m_16_days_NDVI"
            ),
            None,
        )
        if ndvi_entry is None or not ndvi_entry.get("data"):
            raise EarthDataError(f"MODIS NDVI value missing for {year}")
        raw_value = float(ndvi_entry["data"][0])
        if raw_value <= -2000 or raw_value > 10000:
            raise EarthDataError(f"MODIS NDVI is fill or out of range for {year}")
        return year, raw_value / 100.0

    values = await asyncio.gather(
        *(fetch_one(year, composite_date) for year, composite_date in selected_dates.items())
    )
    source = (
        "ORNL DAAC NASA MODIS MOD13Q1 mid-year NDVI composite, scaled x100 "
        f"({latitude:.2f}°, {longitude:.2f}° point)"
    )
    return _require_complete_years(list(values), years), source


async def _fetch_live_series(
    session: aiohttp.ClientSession,
    metric_key: str,
    location_key: str,
    years: tuple[int, ...],
) -> tuple[list[tuple[int, float]], str]:
    if metric_key in POWER_PARAMETERS:
        return await _fetch_power_series(session, metric_key, location_key, years)
    if metric_key == "wildfires":
        return await _fetch_eonet_wildfires(session, location_key, years)
    if metric_key == "sea_level":
        return await _fetch_noaa_sea_level(session, location_key, years)
    if metric_key == "vegetation":
        return await _fetch_modis_ndvi(session, location_key, years)
    raise EarthDataError(f"No Earth data provider configured for {metric_key}")


async def resolve_yearly_data(
    metric_key: str,
    location_key: str,
    fallback_values: Sequence[tuple[int, float]],
) -> YearlyDataResult:
    if not fallback_values:
        raise ValueError("Fallback yearly data must not be empty")

    years = tuple(year for year, _ in fallback_values)
    cache_key = (metric_key, location_key, years)
    now = time.monotonic()
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_at, cached_result = cached
        ttl = FALLBACK_CACHE_TTL_SECONDS if cached_result.used_fallback else CACHE_TTL_SECONDS
        if now - cached_at < ttl:
            return cached_result
        _cache.pop(cache_key, None)

    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS, connect=5, sock_read=10)
    try:
        async with aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": "EarthJukebox/1.0"},
        ) as session:
            async with asyncio.timeout(OVERALL_TIMEOUT_SECONDS):
                values, source = await _fetch_live_series(
                    session,
                    metric_key,
                    location_key,
                    years,
                )
        result = YearlyDataResult(tuple(values), source, False)
    except (
        aiohttp.ClientError,
        asyncio.TimeoutError,
        EarthDataError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        logger.warning(
            "Earth data request failed for %s/%s; using test data: %s",
            metric_key,
            location_key,
            error,
        )
        result = YearlyDataResult(
            tuple((int(year), float(value)) for year, value in fallback_values),
            "Illustrative test data fallback (Earth API unavailable)",
            True,
        )

    _cache[cache_key] = (
        time.monotonic(),
        result,
    )
    return result