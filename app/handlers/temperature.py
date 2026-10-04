import logging

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.keyboards.temperature import listen_keyboard, location_keyboard
from app.handlers.telegram_utils import edit_message_if_changed
from app.services.activity import ActivityService, format_achievement_unlocks
from app.services.earth_data import resolve_yearly_data
from app.services.sonification import build_temperature_audio
from app.services.temperature import format_temperature_report, get_temperature_series
from app.services.temperature_chart import build_temperature_chart


router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "🌡 Temperature")
async def choose_temperature_location(message: Message) -> None:
    await message.answer("Choose a location:", reply_markup=location_keyboard())


@router.callback_query(F.data == "temperature:locations")
async def show_temperature_locations(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await edit_message_if_changed(
            callback.message,
            "Choose a location:",
            location_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("temperature:location:"))
async def show_temperature_report(
    callback: CallbackQuery,
    activity_service: ActivityService,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    location_key = callback.data.removeprefix("temperature:location:")
    series = get_temperature_series(location_key)
    if series is None:
        await callback.answer("Unknown location.", show_alert=True)
        return

    location_name, fallback_values = series
    await callback.answer()
    data_result = await resolve_yearly_data("temperature", location_key, fallback_values)
    yearly_values = data_result.values
    report = format_temperature_report(location_name, yearly_values)
    report += f"\n\nSource: {data_result.source}"
    logger.info("Selected temperature data:\n%s", report)
    unlocked = await activity_service.record_selection(
        callback.from_user,
        "temperature",
        location_key,
        data_result.source,
        yearly_values[0][0],
        yearly_values[-1][0],
    )
    await edit_message_if_changed(
        callback.message,
        report,
        listen_keyboard(location_key),
    )

    chart = build_temperature_chart(location_name, yearly_values)
    await callback.bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=BufferedInputFile(chart, filename=f"{location_key}-temperature.png"),
        caption=f"{location_name} · yearly temperature (°C)\nSource: {data_result.source}",
    )
    if unlocked:
        await callback.bot.send_message(
            callback.message.chat.id,
            format_achievement_unlocks(unlocked),
        )


@router.callback_query(F.data.startswith("temperature:listen:"))
async def listen_temperature(
    callback: CallbackQuery,
    activity_service: ActivityService,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    location_key = callback.data.removeprefix("temperature:listen:")
    series = get_temperature_series(location_key)
    if series is None:
        await callback.answer("Unknown location.", show_alert=True)
        return

    location_name, fallback_values = series
    await callback.answer()
    data_result = await resolve_yearly_data("temperature", location_key, fallback_values)
    yearly_values = data_result.values
    audio = build_temperature_audio(yearly_values)
    file_name = f"{location_key}-temperature.mp3"
    await callback.bot.send_audio(
        chat_id=callback.message.chat.id,
        audio=BufferedInputFile(audio, filename=file_name),
        title=f"{location_name} Temperature",
        performer="Earth Jukebox",
        caption=f"Each note represents one year; pitch follows its temperature.\nSource: {data_result.source}",
    )
    unlocked = await activity_service.record_generated_audio(
        callback.from_user,
        "temperature",
        location_key,
        file_name,
        audio,
        data_result.source,
        yearly_values[0][0],
        yearly_values[-1][0],
    )
    if unlocked:
        await callback.bot.send_message(
            callback.message.chat.id,
            format_achievement_unlocks(unlocked),
        )