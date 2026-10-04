import logging

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.keyboards.vegetation import vegetation_listen_keyboard, vegetation_location_keyboard
from app.handlers.telegram_utils import edit_message_if_changed
from app.services.activity import ActivityService, format_achievement_unlocks
from app.services.earth_data import resolve_yearly_data
from app.services.sonification import build_vegetation_audio, vegetation_instruments
from app.services.temperature_chart import build_yearly_line_chart
from app.services.vegetation import format_vegetation_report, get_vegetation_series


router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "🌱 Vegetation")
async def choose_vegetation_location(message: Message) -> None:
    await message.answer("Choose a location:", reply_markup=vegetation_location_keyboard())


@router.callback_query(F.data == "vegetation:locations")
async def show_vegetation_locations(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await edit_message_if_changed(
            callback.message,
            "Choose a location:",
            vegetation_location_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("vegetation:location:"))
async def show_vegetation_report(
    callback: CallbackQuery,
    activity_service: ActivityService,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    location_key = callback.data.removeprefix("vegetation:location:")
    series = get_vegetation_series(location_key)
    if series is None:
        await callback.answer("Unknown location.", show_alert=True)
        return

    location_name, fallback_values = series
    await callback.answer()
    data_result = await resolve_yearly_data("vegetation", location_key, fallback_values)
    yearly_values = data_result.values
    report = format_vegetation_report(location_name, yearly_values)
    report += f"\n\nSource: {data_result.source}"
    logger.info("Selected vegetation data:\n%s", report)
    logger.info("Vegetation instrument sequence: %s", vegetation_instruments(yearly_values))
    unlocked = await activity_service.record_selection(
        callback.from_user,
        "vegetation",
        location_key,
        data_result.source,
        yearly_values[0][0],
        yearly_values[-1][0],
    )
    await edit_message_if_changed(
        callback.message,
        report,
        vegetation_listen_keyboard(location_key),
    )

    chart = build_yearly_line_chart(
        "Vegetation Index",
        location_name,
        yearly_values,
        "index",
        "MID-YEAR NDVI x100 / ILLUSTRATIVE TEST INDEX",
        value_decimals=1,
    )
    await callback.bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=BufferedInputFile(chart, filename=f"{location_key}-vegetation.png"),
        caption=f"{location_name} · yearly vegetation index\nSource: {data_result.source}",
    )
    if unlocked:
        await callback.bot.send_message(callback.message.chat.id, format_achievement_unlocks(unlocked))


@router.callback_query(F.data.startswith("vegetation:listen:"))
async def listen_vegetation(
    callback: CallbackQuery,
    activity_service: ActivityService,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    location_key = callback.data.removeprefix("vegetation:listen:")
    series = get_vegetation_series(location_key)
    if series is None:
        await callback.answer("Unknown location.", show_alert=True)
        return

    location_name, fallback_values = series
    await callback.answer()
    data_result = await resolve_yearly_data("vegetation", location_key, fallback_values)
    yearly_values = data_result.values
    audio = build_vegetation_audio(yearly_values)
    instruments = ", ".join(dict.fromkeys(vegetation_instruments(yearly_values)))
    file_name = f"{location_key}-vegetation.mp3"
    await callback.bot.send_audio(
        chat_id=callback.message.chat.id,
        audio=BufferedInputFile(audio, filename=file_name),
        title=f"{location_name} Vegetation",
        performer="Earth Jukebox",
        caption=f"Values select timbre: {instruments}.\nSource: {data_result.source}",
    )
    unlocked = await activity_service.record_generated_audio(
        callback.from_user,
        "vegetation",
        location_key,
        file_name,
        audio,
        data_result.source,
        yearly_values[0][0],
        yearly_values[-1][0],
    )
    if unlocked:
        await callback.bot.send_message(callback.message.chat.id, format_achievement_unlocks(unlocked))