import logging

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.keyboards.cloud_coverage import (
    cloud_coverage_listen_keyboard,
    cloud_coverage_location_keyboard,
)
from app.handlers.telegram_utils import edit_message_if_changed
from app.services.activity import ActivityService, format_achievement_unlocks
from app.services.earth_data import resolve_yearly_data
from app.services.cloud_coverage import format_cloud_coverage_report, get_cloud_coverage_series
from app.services.sonification import build_cloud_coverage_audio
from app.services.temperature_chart import build_yearly_line_chart


router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "☁️ Cloud Coverage")
async def choose_cloud_coverage_location(message: Message) -> None:
    await message.answer(
        "Choose a location:",
        reply_markup=cloud_coverage_location_keyboard(),
    )


@router.callback_query(F.data == "cloud_coverage:locations")
async def show_cloud_coverage_locations(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await edit_message_if_changed(
            callback.message,
            "Choose a location:",
            cloud_coverage_location_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("cloud_coverage:location:"))
async def show_cloud_coverage_report(
    callback: CallbackQuery,
    activity_service: ActivityService,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    location_key = callback.data.removeprefix("cloud_coverage:location:")
    series = get_cloud_coverage_series(location_key)
    if series is None:
        await callback.answer("Unknown location.", show_alert=True)
        return

    location_name, fallback_values = series
    await callback.answer()
    data_result = await resolve_yearly_data("cloud_coverage", location_key, fallback_values)
    yearly_values = data_result.values
    report = format_cloud_coverage_report(location_name, yearly_values)
    report += f"\n\nSource: {data_result.source}"
    logger.info("Selected cloud coverage data:\n%s", report)
    unlocked = await activity_service.record_selection(
        callback.from_user,
        "cloud_coverage",
        location_key,
        data_result.source,
        yearly_values[0][0],
        yearly_values[-1][0],
    )
    await edit_message_if_changed(
        callback.message,
        report,
        cloud_coverage_listen_keyboard(location_key),
    )

    chart = build_yearly_line_chart(
        "Cloud Coverage",
        location_name,
        yearly_values,
        "%",
        "ANNUAL MEAN / ILLUSTRATIVE TEST DATA",
    )
    await callback.bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=BufferedInputFile(chart, filename=f"{location_key}-cloud-coverage.png"),
        caption=f"{location_name} · yearly cloud coverage (%)\nSource: {data_result.source}",
    )
    if unlocked:
        await callback.bot.send_message(callback.message.chat.id, format_achievement_unlocks(unlocked))


@router.callback_query(F.data.startswith("cloud_coverage:listen:"))
async def listen_cloud_coverage(
    callback: CallbackQuery,
    activity_service: ActivityService,
) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    location_key = callback.data.removeprefix("cloud_coverage:listen:")
    series = get_cloud_coverage_series(location_key)
    if series is None:
        await callback.answer("Unknown location.", show_alert=True)
        return

    location_name, fallback_values = series
    await callback.answer()
    data_result = await resolve_yearly_data("cloud_coverage", location_key, fallback_values)
    yearly_values = data_result.values
    audio = build_cloud_coverage_audio(yearly_values)
    file_name = f"{location_key}-cloud-coverage.mp3"
    await callback.bot.send_audio(
        chat_id=callback.message.chat.id,
        audio=BufferedInputFile(audio, filename=file_name),
        title=f"{location_name} Cloud Coverage",
        performer="Earth Jukebox",
        caption=f"More cloud coverage creates longer, denser clusters of notes.\nSource: {data_result.source}",
    )
    unlocked = await activity_service.record_generated_audio(
        callback.from_user,
        "cloud_coverage",
        location_key,
        file_name,
        audio,
        data_result.source,
        yearly_values[0][0],
        yearly_values[-1][0],
    )
    if unlocked:
        await callback.bot.send_message(callback.message.chat.id, format_achievement_unlocks(unlocked))