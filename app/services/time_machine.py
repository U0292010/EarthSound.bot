from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.services.cloud_coverage import CLOUD_COVERAGE_LOCATIONS, CLOUD_COVERAGE_TEST_DATA
from app.services.sea_level import SEA_LEVEL_LOCATIONS, SEA_LEVEL_TEST_DATA
from app.services.sonification import (
    build_cloud_coverage_audio,
    build_sea_level_audio,
    build_temperature_audio,
    build_vegetation_audio,
    build_wildfire_audio,
)
from app.services.temperature import LOCATION_NAMES, TEMPERATURE_TEST_DATA
from app.services.vegetation import VEGETATION_LOCATIONS, VEGETATION_TEST_DATA
from app.services.wildfires import WILDFIRE_LOCATIONS, WILDFIRE_TEST_DATA


FIRST_YEAR = 2000
LAST_YEAR = 2026
YearlyValues = Sequence[tuple[int, float]]


@dataclass(frozen=True)
class TimeMachineMetric:
    label: str
    unit: str
    subtitle: str
    locations: Mapping[str, str]
    anchors: Mapping[str, YearlyValues]
    decimals: int = 1


TIME_MACHINE_METRICS = {
    "temperature": TimeMachineMetric(
        "Temperature",
        "°C",
        "ANNUAL MEAN / ILLUSTRATIVE TEST SERIES",
        LOCATION_NAMES,
        TEMPERATURE_TEST_DATA,
    ),
    "sea_level": TimeMachineMetric(
        "Sea Level",
        "mm",
        "YEARLY INDEX / ILLUSTRATIVE TEST SERIES",
        SEA_LEVEL_LOCATIONS,
        SEA_LEVEL_TEST_DATA,
    ),
    "cloud_coverage": TimeMachineMetric(
        "Cloud Coverage",
        "%",
        "ANNUAL MEAN / ILLUSTRATIVE TEST SERIES",
        CLOUD_COVERAGE_LOCATIONS,
        CLOUD_COVERAGE_TEST_DATA,
    ),
    "wildfires": TimeMachineMetric(
        "Wildfires",
        "fires",
        "ANNUAL EVENT COUNT / ILLUSTRATIVE TEST SERIES",
        WILDFIRE_LOCATIONS,
        WILDFIRE_TEST_DATA,
        decimals=0,
    ),
    "vegetation": TimeMachineMetric(
        "Vegetation Index",
        "index",
        "MID-YEAR NDVI x100 / ILLUSTRATIVE TEST SERIES",
        VEGETATION_LOCATIONS,
        VEGETATION_TEST_DATA,
        decimals=1,
    ),
}


def get_time_machine_metric(metric_key: str) -> TimeMachineMetric | None:
    return TIME_MACHINE_METRICS.get(metric_key)


def get_time_machine_locations(metric_key: str) -> Mapping[str, str] | None:
    metric = get_time_machine_metric(metric_key)
    return metric.locations if metric is not None else None


def _interpolate_anchor_value(year: int, anchors: YearlyValues) -> float:
    anchor_by_year = dict(anchors)
    if year in anchor_by_year:
        return anchor_by_year[year]

    if year < anchors[0][0]:
        left, right = anchors[0], anchors[1]
    elif year > anchors[-1][0]:
        left, right = anchors[-2], anchors[-1]
    else:
        left, right = next(
            (left, right)
            for left, right in zip(anchors, anchors[1:])
            if left[0] < year < right[0]
        )

    annual_change = (right[1] - left[1]) / (right[0] - left[0])
    return left[1] + annual_change * (year - left[0])


def build_time_machine_test_series(
    metric_key: str,
    location_key: str,
    start_year: int,
    end_year: int,
) -> list[tuple[int, float]] | None:
    metric = get_time_machine_metric(metric_key)
    if (
        metric is None
        or location_key not in metric.anchors
        or start_year < FIRST_YEAR
        or end_year > LAST_YEAR
        or start_year > end_year
    ):
        return None

    anchors = metric.anchors[location_key]
    values = []
    for year in range(start_year, end_year + 1):
        value = _interpolate_anchor_value(year, anchors)
        if metric.unit == "%" or metric_key == "vegetation":
            value = min(100.0, max(0.0, value))
        elif metric.unit in ("mm", "fires"):
            value = max(0.0, value)
        if metric_key == "wildfires":
            value = float(round(value))
        values.append((year, value))

    return values


def format_time_machine_report(
    metric_key: str,
    location_key: str,
    yearly_values: YearlyValues,
    source: str,
) -> str:
    metric = TIME_MACHINE_METRICS[metric_key]
    location_name = metric.locations[location_key]
    if metric.decimals == 0:
        lines = "\n".join(
            f"{year}: {value:,.0f} {metric.unit}" for year, value in yearly_values
        )
    else:
        lines = "\n".join(
            f"{year}: {value:.1f} {metric.unit}" for year, value in yearly_values
        )

    return (
        f"⏳ {metric.label} · {location_name}\n"
        f"{yearly_values[0][0]}-{yearly_values[-1][0]}:\n\n{lines}\n\n"
        f"Source: {source}"
    )


def build_time_machine_audio(metric_key: str, yearly_values: YearlyValues) -> bytes:
    builders = {
        "temperature": build_temperature_audio,
        "sea_level": build_sea_level_audio,
        "cloud_coverage": build_cloud_coverage_audio,
        "wildfires": build_wildfire_audio,
        "vegetation": build_vegetation_audio,
    }
    builder = builders.get(metric_key)
    if builder is None:
        raise ValueError(f"Unknown Time Machine metric: {metric_key}")
    return builder(yearly_values)