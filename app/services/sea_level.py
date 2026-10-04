from collections.abc import Sequence


SEA_LEVEL_TEST_DATA: dict[str, Sequence[tuple[int, float]]] = {
    "global": ((2020, 87.0), (2021, 91.0), (2022, 96.0), (2023, 104.0), (2024, 113.0)),
    "pacific": ((2020, 90.0), (2021, 95.0), (2022, 101.0), (2023, 111.0), (2024, 122.0)),
    "atlantic": ((2020, 84.0), (2021, 88.0), (2022, 94.0), (2023, 102.0), (2024, 110.0)),
    "indian": ((2020, 88.0), (2021, 93.0), (2022, 99.0), (2023, 109.0), (2024, 119.0)),
}

SEA_LEVEL_LOCATIONS = {
    "global": "Global",
    "pacific": "Pacific Ocean",
    "atlantic": "Atlantic Ocean",
    "indian": "Indian Ocean",
}


def get_sea_level_series(
    location_key: str,
) -> tuple[str, Sequence[tuple[int, float]]] | None:
    location_name = SEA_LEVEL_LOCATIONS.get(location_key)
    yearly_values = SEA_LEVEL_TEST_DATA.get(location_key)
    if location_name is None or yearly_values is None:
        return None

    return location_name, yearly_values


def format_sea_level_report(
    location_name: str,
    yearly_values: Sequence[tuple[int, float]],
) -> str:
    yearly_lines = "\n".join(f"{year}: {value:.1f} mm" for year, value in yearly_values)
    return (
        f"🌊 {location_name}\n"
        "Annual sea level index (illustrative test data, mm):\n\n"
        f"{yearly_lines}"
    )