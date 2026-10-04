from typing import Any

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup


async def edit_message_if_changed(
    message: Any,
    text: str,
    reply_markup: InlineKeyboardMarkup,
) -> bool:
    edit_text = getattr(message, "edit_text", None)
    if edit_text is None:
        return False

    try:
        await edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as error:
        if "message is not modified" in str(error).casefold():
            return False
        raise

    return True