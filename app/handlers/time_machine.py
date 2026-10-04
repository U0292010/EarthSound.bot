import logging
import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardMarkup, Message

from app.handlers.telegram_utils import edit_message_if_changed
from app.keyboards.main import main_menu_keyboard
from app.keyboards.time_machine import (
    time_machine_location_keyboard,
    time_machine_metric_keyboard,
)
from app.services.activity import ActivityService, format_achievement_unlocks
from app.services.earth_data import resolve_yearly_data
from app.services.temperature_chart import build_yearly_line_chart
from app.services.time_machine import (
    FIRST_YEAR,
    LAST_YEAR,
    TIME_MACHINE_METRICS,
    build_time_machine_audio,
    build_time_machine_test_series,
    format_time_machine_report,
    get_time_machine_locations,
    get_time_machine_metric,
)


router = Router()
logger = logging.getLogger(__name__)


class TimeMachineStates(StatesGroup):
    waiting_for_year_range = State()


@router.message(F.text == "⏳ Time Machine")
async def start_time_machine(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Choose an Earth data layer:", reply_markup=time_machine_metric_keyboard())


@router.callback_query(F.data.startswith("time_machine:metric:"))
async def choose_time_machine_metric(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    metric_key = callback.data.removeprefix("time_machine:metric:")
    metric = get_time_machine_metric(metric_key)
    locations = get_time_machine_locations(metric_key)
    if metric is None or locations is None:
        await callback.answer("Unknown data layer.", show_alert=True)
        return

    await state.clear()
    await state.update_data(metric_key=metric_key)
    await callback.answer()
    await edit_message_if_changed(
        callback.message,
        f"{metric.label}: choose a location:",
        time_machine_location_keyboard(metric_key, locations),
    )


@router.callback_query(F.data.startswith("time_machine:location:"))
async def choose_time_machine_location(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None or callback.data is None:
        await callback.answer()
        return

    _, _, metric_key, location_key = callback.data.split(":", maxsplit=3)
    metric = get_time_machine_metric(metric_key)
    locations = get_time_machine_locations(metric_key)
    if metric is None or locations is None or location_key not in locations:
        await callback.answer("Unknown location.", show_alert=True)
        return

    await state.update_data(metric_key=metric_key, location_key=location_key)
    await state.set_state(TimeMachineStates.waiting_for_year_range)
    await callback.answer()
    await edit_message_if_changed(
        callback.message,
        f"{locations[location_key]} selected. Enter a year range from "
        f"{FIRST_YEAR} to {LAST_YEAR}, for example 2000-2026:",
        InlineKeyboardMarkup(inline_keyboard=[]),
    )


@router.message(Command("cancel"), TimeMachineStates.waiting_for_year_range)
async def cancel_time_machine(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Time Machine cancelled.", reply_markup=main_menu_keyboard())


@router.message(TimeMachineStates.waiting_for_year_range)
async def show_time_machine_range(
    message: Message,
    state: FSMContext,
    activity_service: ActivityService,
) -> None:
    match = re.fullmatch(r"\s*(\d{4})\s*[-–]\s*(\d{4})\s*", message.text or "")
    if match is None:
        await message.answer(f"Enter the range as YYYY-YYYY, between {FIRST_YEAR} and {LAST_YEAR}.")
        return

    start_year, end_year = (int(part) for part in match.groups())
    if start_year < FIRST_YEAR or end_year > LAST_YEAR or start_year > end_year:
        await message.answer(f"Choose an inclusive range from {FIRST_YEAR} to {LAST_YEAR}.")
        return

    state_data = await state.get_data()
    metric_key = state_data.get("metric_key")
    location_key = state_data.get("location_key")
    metric = get_time_machine_metric(metric_key or "")
    if metric is None or location_key not in metric.locations:
        await state.clear()
        await message.answer("Time Machine selection expired. Start again from the menu.")
        return

    fallback_values = build_time_machine_test_series(
        metric_key,
        location_key,
        start_year,
        end_year,
    )
    if fallback_values is None:
        await message.answer("Could not prepare data for that range.")
        return

    data_result = await resolve_yearly_data(metric_key, location_key, fallback_values)
    location_name = metric.locations[location_key]
    unlocked = await activity_service.record_selection(
        message.from_user,
        metric_key,
        location_key,
        data_result.source,
        start_year,
        end_year,
    )
    report = format_time_machine_report(
        metric_key,
        location_key,
        data_result.values,
        data_result.source,
    )
    await message.answer(report)

    chart = build_yearly_line_chart(
        metric.label,
        location_name,
        data_result.values,
        metric.unit,
        metric.subtitle,
        value_decimals=metric.decimals,
    )
    await message.answer_photo(
        BufferedInputFile(
            chart,
            filename=f"{metric_key}-{location_key}-{start_year}-{end_year}.png",
        ),
        caption=f"{metric.label} · {location_name} · {start_year}-{end_year}\nSource: {data_result.source}",
    )

    audio = build_time_machine_audio(metric_key, data_result.values)
    file_name = f"{metric_key}-{location_key}-{start_year}-{end_year}.mp3"
    await message.answer_audio(
        BufferedInputFile(
            audio,
            filename=file_name,
        ),
        title=f"{metric.label} · {location_name} · {start_year}-{end_year}",
        performer="Earth Jukebox",
        caption=f"Audio uses the same yearly series. Source: {data_result.source}",
    )
    unlocked.extend(
        await activity_service.record_generated_audio(
            message.from_user,
            metric_key,
            location_key,
            file_name,
            audio,
            data_result.source,
            start_year,
            end_year,
        )
    )
    if unlocked:
        await message.answer(format_achievement_unlocks(unlocked))
    logger.info(
        "Time Machine sent %s/%s for %s-%s from %s",
        metric_key,
        location_key,
        start_year,
        end_year,
        data_result.source,
    )
    await state.clear()