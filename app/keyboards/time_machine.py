from collections.abc import Mapping

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def time_machine_metric_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌡 Temperature", callback_data="time_machine:metric:temperature"),
                InlineKeyboardButton(text="🌊 Sea Level", callback_data="time_machine:metric:sea_level"),
            ],
            [
                InlineKeyboardButton(text="☁️ Cloud Coverage", callback_data="time_machine:metric:cloud_coverage"),
                InlineKeyboardButton(text="🔥 Wildfires", callback_data="time_machine:metric:wildfires"),
            ],
            [InlineKeyboardButton(text="🌱 Vegetation", callback_data="time_machine:metric:vegetation")],
        ]
    )


def time_machine_location_keyboard(
    metric_key: str,
    locations: Mapping[str, str],
) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=location_name,
            callback_data=f"time_machine:location:{metric_key}:{location_key}",
        )
        for location_key, location_name in locations.items()
    ]
    rows = [buttons[index : index + 2] for index in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)