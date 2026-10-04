from collections.abc import Sequence


VEGETATION_TEST_DATA: dict[str, Sequence[tuple[int, float]]] = {
    "global": ((2020, 21.0), (2021, 24.0), (2022, 27.0), (2023, 31.0), (2024, 35.0)),
    "amazon": ((2020, 78.0), (2021, 77.0), (2022, 76.0), (2023, 74.0), (2024, 72.0)),
    "boreal": ((2020, 56.0), (2021, 58.0), (2022, 60.0), (2023, 62.0), (2024, 64.0)),
    "sahel": ((2020, 18.0), (2021, 20.0), (2022, 23.0), (2023, 26.0), (2024, 29.0)),
}

VEGETATION_LOCATIONS = {
    "global": "Global",
    "amazon": "Amazon",
    "boreal": "Boreal Forest",
    "sahel": "Sahel",
}


def get_vegetation_series(
    location_key: str,
) -> tuple[str, Sequence[tuple[int, float]]] | None:
    location_name = VEGETATION_LOCATIONS.get(location_key)
    yearly_values = VEGETATION_TEST_DATA.get(location_key)
    if location_name is None or yearly_values is None:
        return None

    return location_name, yearly_values


def format_vegetation_report(
    location_name: str,
    yearly_values: Sequence[tuple[int, float]],
) -> str:
    yearly_lines = "\n".join(f"{year}: {value:.1f}" for year, value in yearly_values)
    return (
        f"🌱 {location_name}\n"
        "Annual vegetation index (NDVI scaled x100 / 0-100 test scale):\n\n"
        f"{yearly_lines}"
    )