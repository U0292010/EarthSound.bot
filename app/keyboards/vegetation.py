from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def vegetation_location_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌍 Global", callback_data="vegetation:location:global"),
                InlineKeyboardButton(text="🌳 Amazon", callback_data="vegetation:location:amazon"),
            ],
            [
                InlineKeyboardButton(text="🌲 Boreal Forest", callback_data="vegetation:location:boreal"),
                InlineKeyboardButton(text="🌾 Sahel", callback_data="vegetation:location:sahel"),
            ],
        ]
    )


def vegetation_listen_keyboard(location_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎧 Listen",
                    callback_data=f"vegetation:listen:{location_key}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩ Choose another location",
                    callback_data="vegetation:locations",
                )
            ],
        ]
    )