from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def location_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌍 Global", callback_data="temperature:location:global"),
                InlineKeyboardButton(text="🇺🇿 Uzbekistan", callback_data="temperature:location:uzbekistan"),
            ],
            [
                InlineKeyboardButton(text="🇺🇸 USA", callback_data="temperature:location:usa"),
                InlineKeyboardButton(text="🇯🇵 Japan", callback_data="temperature:location:japan"),
            ],
        ]
    )


def listen_keyboard(location_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎧 Listen",
                    callback_data=f"temperature:listen:{location_key}",
                )
            ],
            [InlineKeyboardButton(text="↩ Choose another location", callback_data="temperature:locations")],
        ]
    )