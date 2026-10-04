from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def sea_level_location_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌍 Global", callback_data="sea_level:location:global"),
                InlineKeyboardButton(text="🌊 Pacific Ocean", callback_data="sea_level:location:pacific"),
            ],
            [
                InlineKeyboardButton(text="🌊 Atlantic Ocean", callback_data="sea_level:location:atlantic"),
                InlineKeyboardButton(text="🌊 Indian Ocean", callback_data="sea_level:location:indian"),
            ],
        ]
    )


def sea_level_listen_keyboard(location_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎧 Listen",
                    callback_data=f"sea_level:listen:{location_key}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩ Choose another location",
                    callback_data="sea_level:locations",
                )
            ],
        ]
    )