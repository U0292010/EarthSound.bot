import logging

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.keyboards.wildfires import wildfire_listen_keyboard, wildfire_location_keyboard
from app.handlers.telegram_utils import edit_message_if_changed
from app.services.activity import ActivityService, format_achievement_unlocks
from app.services.earth_data import resolve_yearly_data
from app.services.sonification import build_wildfire_audio
from app.services.temperature_chart import build_yearly_line_chart
from app.services.wildfires import format_wildfire_report, get_wildfire_series


router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "🔥 Wildfires")
async def choose_wildfire_location(message: Message) -> None:
    await message.answer("Choose a location:", reply_markup=wildfire_location_keyboard())


@router.callback_query(F.data == "wildfires:locations")
async def show_wildfire_locations(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await edit_message_if_changed(
            callback.message,
            "Choose a location:",
            wildfire_location_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("wildfires:location:"))
async def show_wildfire_report(
    callback: CallbackQuery,
    activity_service: ActivityService,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    location_key = callback.data.removeprefix("wildfires:location:")
    series = get_wildfire_series(location_key)
    if series is None:
        await callback.answer("Unknown location.", show_alert=True)
        return

    location_name, fallback_values = series
    await callback.answer()
    data_result = await resolve_yearly_data("wildfires", location_key, fallback_values)
    yearly_values = data_result.values
    report = format_wildfire_report(location_name, yearly_values)
    report += f"\n\nSource: {data_result.source}"
    logger.info("Selected wildfire data:\n%s", report)
    unlocked = await activity_service.record_selection(
        callback.from_user,
        "wildfires",
        location_key,
        data_result.source,
        yearly_values[0][0],
        yearly_values[-1][0],
    )
    await edit_message_if_changed(
        callback.message,
        report,
        wildfire_listen_keyboard(location_key),
    )

    chart = build_yearly_line_chart(
        "Wildfire Count",
        location_name,
        yearly_values,
        "fires",
        "ANNUAL INCIDENT COUNT / ILLUSTRATIVE TEST DATA",
        value_decimals=0,
    )
    await callback.bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=BufferedInputFile(chart, filename=f"{location_key}-wildfires.png"),
        caption=f"{location_name} · annual wildfire count\nSource: {data_result.source}",
    )
    if unlocked:
        await callback.bot.send_message(callback.message.chat.id, format_achievement_unlocks(unlocked))


@router.callback_query(F.data.startswith("wildfires:listen:"))
async def listen_wildfires(
    callback: CallbackQuery,
    activity_service: ActivityService,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    location_key = callback.data.removeprefix("wildfires:listen:")
    series = get_wildfire_series(location_key)
    if series is None:
        await callback.answer("Unknown location.", show_alert=True)
        return

    location_name, fallback_values = series
    await callback.answer()
    data_result = await resolve_yearly_data("wildfires", location_key, fallback_values)
    yearly_values = data_result.values
    audio = build_wildfire_audio(yearly_values)
    file_name = f"{location_key}-wildfires.mp3"
    await callback.bot.send_audio(
        chat_id=callback.message.chat.id,
        audio=BufferedInputFile(audio, filename=file_name),
        title=f"{location_name} Wildfire Sonification",
        performer="Earth Jukebox",
        caption=f"More fires make the rhythm faster and the notes stronger.\nSource: {data_result.source}",
    )
    unlocked = await activity_service.record_generated_audio(
        callback.from_user,
        "wildfires",
        location_key,
        file_name,
        audio,
        data_result.source,
        yearly_values[0][0],
        yearly_values[-1][0],
    )
    if unlocked:
        await callback.bot.send_message(callback.message.chat.id, format_achievement_unlocks(unlocked))