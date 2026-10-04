from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def wildfire_location_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌍 Global", callback_data="wildfires:location:global"),
                InlineKeyboardButton(text="🇺🇸 California", callback_data="wildfires:location:california"),
            ],
            [
                InlineKeyboardButton(text="🌳 Amazon", callback_data="wildfires:location:amazon"),
                InlineKeyboardButton(text="🇦🇺 Australia", callback_data="wildfires:location:australia"),
            ],
        ]
    )


def wildfire_listen_keyboard(location_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎧 Listen",
                    callback_data=f"wildfires:listen:{location_key}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩ Choose another location",
                    callback_data="wildfires:locations",
                )
            ],
        ]
    )