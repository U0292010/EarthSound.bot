import logging

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.keyboards.sea_level import sea_level_listen_keyboard, sea_level_location_keyboard
from app.handlers.telegram_utils import edit_message_if_changed
from app.services.activity import ActivityService, format_achievement_unlocks
from app.services.earth_data import resolve_yearly_data
from app.services.sea_level import format_sea_level_report, get_sea_level_series
from app.services.sonification import build_sea_level_audio
from app.services.temperature_chart import build_yearly_line_chart


router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "🌊 Sea Level")
async def choose_sea_level_location(message: Message) -> None:
    await message.answer("Choose an ocean region:", reply_markup=sea_level_location_keyboard())


@router.callback_query(F.data == "sea_level:locations")
async def show_sea_level_locations(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await edit_message_if_changed(
            callback.message,
            "Choose an ocean region:",
            sea_level_location_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("sea_level:location:"))
async def show_sea_level_report(
    callback: CallbackQuery,
    activity_service: ActivityService,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    location_key = callback.data.removeprefix("sea_level:location:")
    series = get_sea_level_series(location_key)
    if series is None:
        await callback.answer("Unknown ocean region.", show_alert=True)
        return

    location_name, fallback_values = series
    await callback.answer()
    data_result = await resolve_yearly_data("sea_level", location_key, fallback_values)
    yearly_values = data_result.values
    report = format_sea_level_report(location_name, yearly_values)
    report += f"\n\nSource: {data_result.source}"
    logger.info("Selected sea level data:\n%s", report)
    unlocked = await activity_service.record_selection(
        callback.from_user,
        "sea_level",
        location_key,
        data_result.source,
        yearly_values[0][0],
        yearly_values[-1][0],
    )
    await edit_message_if_changed(
        callback.message,
        report,
        sea_level_listen_keyboard(location_key),
    )

    chart = build_yearly_line_chart(
        "Sea Level",
        location_name,
        yearly_values,
        "mm",
        "YEARLY INDEX / ILLUSTRATIVE TEST DATA",
    )
    await callback.bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=BufferedInputFile(chart, filename=f"{location_key}-sea-level.png"),
        caption=f"{location_name} · yearly sea level (mm)\nSource: {data_result.source}",
    )
    if unlocked:
        await callback.bot.send_message(callback.message.chat.id, format_achievement_unlocks(unlocked))


@router.callback_query(F.data.startswith("sea_level:listen:"))
async def listen_sea_level(
    callback: CallbackQuery,
    activity_service: ActivityService,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    location_key = callback.data.removeprefix("sea_level:listen:")
    series = get_sea_level_series(location_key)
    if series is None:
        await callback.answer("Unknown ocean region.", show_alert=True)
        return

    location_name, fallback_values = series
    await callback.answer()
    data_result = await resolve_yearly_data("sea_level", location_key, fallback_values)
    yearly_values = data_result.values
    audio = build_sea_level_audio(yearly_values)
    file_name = f"{location_key}-sea-level.mp3"
    await callback.bot.send_audio(
        chat_id=callback.message.chat.id,
        audio=BufferedInputFile(audio, filename=file_name),
        title=f"{location_name} Sea Level Rhythm",
        performer="Earth Jukebox",
        caption=f"Each note is a year; rising sea level makes the rhythm faster.\nSource: {data_result.source}",
    )
    unlocked = await activity_service.record_generated_audio(
        callback.from_user,
        "sea_level",
        location_key,
        file_name,
        audio,
        data_result.source,
        yearly_values[0][0],
        yearly_values[-1][0],
    )
    if unlocked:
        await callback.bot.send_message(callback.message.chat.id, format_achievement_unlocks(unlocked))