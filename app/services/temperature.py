from collections.abc import Sequence


TEMPERATURE_TEST_DATA: dict[str, Sequence[tuple[int, float]]] = {
    "global": ((2020, 14.9), (2021, 15.0), (2022, 15.0), (2023, 15.1), (2024, 15.2)),
    "uzbekistan": ((2020, 14.2), (2021, 14.5), (2022, 14.3), (2023, 14.8), (2024, 15.0)),
    "usa": ((2020, 12.5), (2021, 12.7), (2022, 12.6), (2023, 12.9), (2024, 13.1)),
    "japan": ((2020, 15.3), (2021, 15.5), (2022, 15.4), (2023, 15.7), (2024, 15.9)),
}

LOCATION_NAMES = {
    "global": "Global",
    "uzbekistan": "Uzbekistan",
    "usa": "USA",
    "japan": "Japan",
}


def get_temperature_series(
    location_key: str,
) -> tuple[str, Sequence[tuple[int, float]]] | None:
    location_name = LOCATION_NAMES.get(location_key)
    yearly_values = TEMPERATURE_TEST_DATA.get(location_key)
    if location_name is None or yearly_values is None:
        return None

    return location_name, yearly_values


def format_temperature_report(
    location_name: str,
    yearly_values: Sequence[tuple[int, float]],
) -> str:
    yearly_lines = "\n".join(f"{year}: {value:.1f} °C" for year, value in yearly_values)
    return (
        f"🌡 {location_name}\n"
        "Annual temperature (illustrative test data, °C):\n\n"
        f"{yearly_lines}"
    )