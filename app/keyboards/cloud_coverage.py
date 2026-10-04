from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def cloud_coverage_location_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌍 Global", callback_data="cloud_coverage:location:global"),
                InlineKeyboardButton(text="🌴 Tropical Belt", callback_data="cloud_coverage:location:tropics"),
            ],
            [
                InlineKeyboardButton(text="🧊 Arctic", callback_data="cloud_coverage:location:arctic"),
                InlineKeyboardButton(text="🏜 Sahara", callback_data="cloud_coverage:location:sahara"),
            ],
        ]
    )


def cloud_coverage_listen_keyboard(location_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎧 Listen",
                    callback_data=f"cloud_coverage:listen:{location_key}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩ Choose another location",
                    callback_data="cloud_coverage:locations",
                )
            ],
        ]
    )