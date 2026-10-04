from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌡 Temperature"), KeyboardButton(text="🌊 Sea Level")],
            [KeyboardButton(text="☁️ Cloud Coverage"), KeyboardButton(text="🔥 Wildfires")],
            [KeyboardButton(text="🌱 Vegetation")],
            [KeyboardButton(text="⏳ Time Machine")],
        ],
        resize_keyboard=True,
    )