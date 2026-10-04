import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import load_config
from app.handlers.cloud_coverage import router as cloud_coverage_router
from app.handlers.sea_level import router as sea_level_router
from app.handlers.start import router as start_router
from app.handlers.temperature import router as temperature_router
from app.handlers.time_machine import router as time_machine_router
from app.handlers.vegetation import router as vegetation_router
from app.handlers.wildfires import router as wildfires_router
from app.repositories.sqlite import SQLiteRepository
from app.services.activity import ActivityService


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    activity_service = ActivityService(SQLiteRepository(config.database_path))
    await activity_service.initialize()
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher["activity_service"] = activity_service
    dispatcher.include_router(start_router)
    dispatcher.include_router(temperature_router)
    dispatcher.include_router(sea_level_router)
    dispatcher.include_router(cloud_coverage_router)
    dispatcher.include_router(wildfires_router)
    dispatcher.include_router(vegetation_router)
    dispatcher.include_router(time_machine_router)

    async with Bot(token=config.bot_token) as bot:
        await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())