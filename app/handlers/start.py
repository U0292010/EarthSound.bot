from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main import main_menu_keyboard
from app.services.activity import (
    ActivityService,
    format_achievement_list,
    format_activity_history,
)


router = Router()


@router.message(CommandStart())
async def command_start(
    message: Message,
    state: FSMContext,
    activity_service: ActivityService,
) -> None:
    await state.clear()
    if message.from_user is not None:
        await activity_service.record_activity(message.from_user, "started")
    await message.answer(
        '🌍 Earth Jukebox\n\n"Explore Earth through sound."',
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("achievements"))
async def show_achievements(message: Message, activity_service: ActivityService) -> None:
    rows = await activity_service.get_achievements(message.from_user.id)
    await message.answer(format_achievement_list(rows))


@router.message(Command("history"))
async def show_activity_history(message: Message, activity_service: ActivityService) -> None:
    rows = await activity_service.get_recent_activity(message.from_user.id)
    await message.answer(format_activity_history(rows))