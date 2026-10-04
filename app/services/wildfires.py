from collections.abc import Sequence


WILDFIRE_TEST_DATA: dict[str, Sequence[tuple[int, float]]] = {
    "global": ((2020, 1050.0), (2021, 1150.0), (2022, 1250.0), (2023, 1380.0), (2024, 1500.0)),
    "california": ((2020, 4800.0), (2021, 5300.0), (2022, 6000.0), (2023, 6900.0), (2024, 7800.0)),
    "amazon": ((2020, 72000.0), (2021, 76000.0), (2022, 81000.0), (2023, 89000.0), (2024, 96000.0)),
    "australia": ((2020, 3200.0), (2021, 3500.0), (2022, 3900.0), (2023, 4500.0), (2024, 5200.0)),
}

WILDFIRE_LOCATIONS = {
    "global": "Global",
    "california": "California",
    "amazon": "Amazon",
    "australia": "Australia",
}


def get_wildfire_series(
    location_key: str,
) -> tuple[str, Sequence[tuple[int, float]]] | None:
    location_name = WILDFIRE_LOCATIONS.get(location_key)
    yearly_values = WILDFIRE_TEST_DATA.get(location_key)
    if location_name is None or yearly_values is None:
        return None

    return location_name, yearly_values


def format_wildfire_report(
    location_name: str,
    yearly_values: Sequence[tuple[int, float]],
) -> str:
    yearly_lines = "\n".join(f"{year}: {count:,.0f} fires" for year, count in yearly_values)
    return (
        f"🔥 {location_name}\n"
        "Annual wildfire count (illustrative test data):\n\n"
        f"{yearly_lines}"
    )