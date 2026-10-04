from collections.abc import Sequence


CLOUD_COVERAGE_TEST_DATA: dict[str, Sequence[tuple[int, float]]] = {
    "global": ((2020, 67.0), (2021, 66.0), (2022, 68.0), (2023, 67.0), (2024, 69.0)),
    "tropics": ((2020, 64.0), (2021, 65.0), (2022, 66.0), (2023, 68.0), (2024, 70.0)),
    "arctic": ((2020, 58.0), (2021, 59.0), (2022, 61.0), (2023, 62.0), (2024, 64.0)),
    "sahara": ((2020, 19.0), (2021, 20.0), (2022, 20.0), (2023, 21.0), (2024, 22.0)),
}

CLOUD_COVERAGE_LOCATIONS = {
    "global": "Global",
    "tropics": "Tropical Belt",
    "arctic": "Arctic",
    "sahara": "Sahara",
}


def get_cloud_coverage_series(
    location_key: str,
) -> tuple[str, Sequence[tuple[int, float]]] | None:
    location_name = CLOUD_COVERAGE_LOCATIONS.get(location_key)
    yearly_values = CLOUD_COVERAGE_TEST_DATA.get(location_key)
    if location_name is None or yearly_values is None:
        return None

    return location_name, yearly_values


def format_cloud_coverage_report(
    location_name: str,
    yearly_values: Sequence[tuple[int, float]],
) -> str:
    yearly_lines = "\n".join(f"{year}: {value:.1f}%" for year, value in yearly_values)
    return (
        f"☁️ {location_name}\n"
        "Annual cloud coverage (illustrative test data, %):\n\n"
        f"{yearly_lines}"
    )